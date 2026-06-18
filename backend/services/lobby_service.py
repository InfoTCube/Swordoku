import random
import string
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.models.lobby import Lobby, LobbyMember
from backend.models.match import Match, MatchParticipant
from backend.models.puzzle import Puzzle
from backend.services.difficulty_classifier import classify_difficulty
from backend.services.puzzle_generator import generate_solved_grid, make_puzzle

MAX_LOBBY_SIZE = 4


def _generate_code() -> str:
    chars = string.ascii_uppercase + string.digits
    return "".join(random.choices(chars, k=6))


def create_lobby(db: Session, creator_id: str, mode: str, difficulty: str, time_limit_min: int = 10, mistake_limit: int = 3) -> Lobby:
    for _ in range(10):
        code = _generate_code()
        if not db.query(Lobby).filter(Lobby.code == code).first():
            break
    else:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not generate a unique lobby code; please try again",
        )

    lobby = Lobby(code=code, creator_id=creator_id, mode=mode, difficulty=difficulty, time_limit_min=time_limit_min, mistake_limit=mistake_limit)
    db.add(lobby)
    db.flush()

    member = LobbyMember(lobby_id=lobby.id, user_id=creator_id)
    db.add(member)
    db.commit()
    db.refresh(lobby)
    return lobby


def get_lobby_by_code(db: Session, code: str) -> Lobby | None:
    return db.query(Lobby).filter(Lobby.code == code).first()


def get_lobby_members(db: Session, lobby_id: str) -> list[LobbyMember]:
    return db.query(LobbyMember).filter(LobbyMember.lobby_id == lobby_id).all()


def join_lobby(db: Session, lobby: Lobby, user_id: str) -> LobbyMember:
    if lobby.status != "waiting":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Lobby already started")

    members = get_lobby_members(db, lobby.id)

    existing = next((m for m in members if m.user_id == user_id), None)
    if existing is not None:
        return existing

    if len(members) >= MAX_LOBBY_SIZE:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Lobby is full")

    member = LobbyMember(lobby_id=lobby.id, user_id=user_id)
    db.add(member)
    db.commit()
    db.refresh(member)
    return member


def start_lobby(db: Session, lobby: Lobby, requesting_user_id: str) -> str:
    if lobby.creator_id != requesting_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the lobby creator can start the match",
        )

    if lobby.status != "waiting":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Lobby already started")

    members = get_lobby_members(db, lobby.id)
    if len(members) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least 2 players required to start",
        )

    solved = generate_solved_grid()
    givens, solution = make_puzzle(solved, lobby.difficulty)
    actual_difficulty = classify_difficulty(givens)

    puzzle = Puzzle(
        difficulty=actual_difficulty.value,
        givens=givens,
        solution=solution,
    )
    db.add(puzzle)
    db.flush()

    match = Match(
        puzzle_id=puzzle.id,
        mode=lobby.mode,
        status="active",
        time_limit_s=lobby.time_limit_min * 60,
        mistake_limit=lobby.mistake_limit,
        started_at=datetime.now(timezone.utc),
    )
    db.add(match)
    db.flush()

    for member in members:
        db.add(MatchParticipant(match_id=match.id, user_id=member.user_id))

    lobby.status = "active"
    lobby.match_id = match.id

    db.commit()
    db.refresh(match)
    return match.id
