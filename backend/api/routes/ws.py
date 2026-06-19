import asyncio
import json
from collections import defaultdict
from datetime import datetime, timezone

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status, Depends
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.core.security import decode_access_token
from backend.models.match import Match
from backend.models.puzzle import Puzzle
from backend.models.user import User
from backend.schemas.match import (
    MatchEndBroadcast,
    MoveMessage,
    MoveResultMessage,
    PlayerEliminatedBroadcast,
    ProgressBroadcast,
)
from backend.services.connection_manager import manager
from backend.services.match_service import get_match, get_participant, get_participants
from backend.services.move_validator import process_move
from backend.services.win_detection import finalize_match, has_won

router = APIRouter()

# match_id → set of eliminated user_ids (in-memory; single-process server)
_match_eliminated: dict[str, set[str]] = defaultdict(set)
# per-match lock prevents double-finalization when multiple clients race to end the match
_match_locks: dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)


async def _finalize_and_broadcast(
    db: Session,
    match: Match,
    match_id: str,
    reason: str,
) -> None:
    lock = _match_locks[match_id]
    winner = None
    elo_deltas: dict[str, int] | None = None

    async with lock:
        # Re-fetch match status under the lock so concurrent callers see the
        # committed state from whichever handler wins the race.
        db.refresh(match)
        if match.status == "finished":
            return
        eliminated = _match_eliminated.pop(match_id, set())
        _match_locks.pop(match_id, None)
        participants = get_participants(db, match_id)
        winner = finalize_match(db, match, participants, reason=reason,
                                eliminated_user_ids=eliminated or None)
        if match.mode == "ranked":
            elo_deltas = {
                p.user_id: (p.elo_after - p.elo_before)
                for p in participants
                if p.elo_before is not None and p.elo_after is not None
            }

    await manager.broadcast_to_match(match_id, MatchEndBroadcast(
        winner_id=winner.user_id if winner is not None else None,
        reason=reason,
        elo_deltas=elo_deltas,
    ).model_dump())


@router.websocket("/ws/match/{match_id}")
async def match_ws(
    match_id: str,
    websocket: WebSocket,
    db: Session = Depends(get_db),
) -> None:
    # Accept first so we can send a 1008 close frame on auth failures (pre-accept
    # raises a 1006 abnormal closure the browser can't distinguish from a network error).
    await websocket.accept()

    # Auth via first message payload — avoids token appearing in server access logs,
    # browser history, and Referer headers (query-string token leakage).
    try:
        raw_auth = await asyncio.wait_for(websocket.receive_text(), timeout=10.0)
        auth_data = json.loads(raw_auth)
        token = auth_data.get("token") if isinstance(auth_data, dict) else None
    except Exception:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    if not isinstance(token, str) or not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    user_id = decode_access_token(token)
    if user_id is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    user = db.get(User, user_id)
    if user is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    match = get_match(db, match_id)
    if match is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    participant = get_participant(db, match_id, user_id)
    if participant is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    if match.status == "finished":
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    manager.add_connection(match_id, websocket)

    puzzle = db.get(Puzzle, match.puzzle_id)
    blank_count = sum(1 for g in puzzle.givens if g == 0)
    eliminated = _match_eliminated.get(match_id, set())
    started_at_ts: float | None = None
    if match.started_at is not None:
        t = match.started_at
        if t.tzinfo is None:
            t = t.replace(tzinfo=timezone.utc)
        started_at_ts = t.timestamp()

    other_participants = [p for p in get_participants(db, match_id) if p.user_id != user_id]
    participants_state = []
    for p in other_participants:
        u = db.get(User, p.user_id)
        if u:
            participants_state.append({
                "user_id": p.user_id,
                "username": u.username,
                "cells_correct": p.cells_correct,
                "mistakes": p.mistakes,
            })

    await websocket.send_json({
        "type": "board_state",
        "givens": puzzle.givens,
        "blank_count": blank_count,
        "board_state": participant.board_state,
        "mistakes": participant.mistakes,
        "eliminated_user_ids": list(eliminated),
        "started_at": started_at_ts,
        "time_limit_s": match.time_limit_s,
        "mistake_limit": match.mistake_limit,
        "participants_state": participants_state,
    })

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
            except Exception:
                await websocket.send_json({"type": "error", "detail": "Invalid message format"})
                continue

            if data.get("type") == "time_up":
                if match.status != "finished":
                    db.refresh(match)
                    if match.started_at is not None:
                        started = match.started_at
                        if started.tzinfo is None:
                            started = started.replace(tzinfo=timezone.utc)
                        elapsed_s = (datetime.now(timezone.utc) - started).total_seconds()
                        # 10-second grace window absorbs clock skew and network latency
                        if elapsed_s >= match.time_limit_s - 10:
                            await _finalize_and_broadcast(db, match, match_id, reason="time_up")
                continue

            try:
                move = MoveMessage.model_validate(data)
            except Exception:
                await websocket.send_json({"type": "error", "detail": "Invalid move format"})
                continue

            if user_id in _match_eliminated.get(match_id, set()):
                await websocket.send_json({"type": "error", "detail": "eliminated"})
                continue

            is_correct, rejection_reason = process_move(
                db, puzzle, participant, move.cell, move.value
            )

            if rejection_reason is not None:
                await websocket.send_json({"type": "error", "detail": rejection_reason})
                continue

            await websocket.send_json(
                MoveResultMessage(cell=move.cell, correct=is_correct).model_dump()
            )

            await manager.broadcast_to_match(match_id, ProgressBroadcast(
                user_id=user_id,
                username=user.username,
                cells_correct=participant.cells_correct,
                mistakes=participant.mistakes,
            ).model_dump())

            db.refresh(match)
            if match.status != "finished":
                if has_won(participant, blank_count):
                    await _finalize_and_broadcast(db, match, match_id, reason="completed")

                elif not is_correct and participant.mistakes > match.mistake_limit:
                    _match_eliminated[match_id].add(user_id)
                    await manager.broadcast_to_match(match_id, PlayerEliminatedBroadcast(
                        user_id=user_id,
                        username=user.username,
                    ).model_dump())

                    all_participants = get_participants(db, match_id)
                    active = [p for p in all_participants
                              if p.user_id not in _match_eliminated[match_id]]

                    if len(active) <= 1:
                        await _finalize_and_broadcast(db, match, match_id,
                                                      reason="mistake_limit")

    except WebSocketDisconnect:
        manager.disconnect(match_id, websocket)
