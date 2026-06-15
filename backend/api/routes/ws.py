import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, WebSocketException, status, Depends
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.core.security import decode_access_token
from backend.models.puzzle import Puzzle
from backend.models.user import User
from backend.schemas.match import MoveMessage, ProgressBroadcast
from backend.services.connection_manager import manager
from backend.services.match_service import get_match, upsert_participant
from backend.services.move_validator import process_move

router = APIRouter()

@router.websocket("/ws/match/{match_id}")
async def match_ws(
    match_id: str, 
    websocket: WebSocket,
    token: str,
    db: Session = Depends(get_db),
) -> None:
    user_id = decode_access_token(token)
    if user_id is None:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")

    user = db.get(User, user_id)
    if user is None:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="User not found")

    match = get_match(db, match_id)
    if match is None:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="Match not found")
    
    participant = upsert_participant(db, match_id, user_id)
    await manager.connect(match_id, websocket)

    puzzle = db.get(Puzzle, match.puzzle_id)
    await websocket.send_json({"type": "board_state", "givens": puzzle.givens})

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                move = MoveMessage.model_validate(json.loads(raw))
            except Exception:
                await websocket.send_json({"type": "error", "detail": "Invalid move format"})
                continue

            is_correct, rejection_reason = process_move(
                db, puzzle, participant, move.cell, move.value
            )

            if rejection_reason is not None:
                await websocket.send_json({"type": "error", "detail": rejection_reason})
                continue

            broadcast = ProgressBroadcast(
                user_id=user_id,
                cells_correct=participant.cells_correct,
                mistakes=participant.mistakes,
            )
            await manager.broadcast_to_match(match_id, broadcast.model_dump())

    except WebSocketDisconnect:
        manager.disconnect(match_id, websocket)