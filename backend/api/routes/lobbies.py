from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.models.user import User
from backend.schemas.lobby import LobbyCreate, LobbyMemberOut, LobbyOut, LobbyStartOut
from backend.services.auth_service import get_current_user
from backend.services.lobby_service import (
    create_lobby,
    get_lobby_by_code,
    get_lobby_members,
    join_lobby,
    start_lobby,
)

router = APIRouter(prefix="/lobbies", tags=["lobbies"])


def _build_lobby_out(lobby, members, db: Session, request: Request) -> LobbyOut:
    players = []
    for m in members:
        user = db.get(User, m.user_id)
        players.append(
            LobbyMemberOut(
                user_id=m.user_id,
                username=user.username if user else "unknown",
                joined_at=m.joined_at,
            )
        )

    base = str(request.base_url).rstrip("/")
    invite_url = f"{base}/lobby/{lobby.code}"

    return LobbyOut(
        id=lobby.id,
        code=lobby.code,
        invite_url=invite_url,
        mode=lobby.mode,
        difficulty=lobby.difficulty,
        status=lobby.status,
        players=players,
        match_id=lobby.match_id,
    )


@router.post("", response_model=LobbyOut, status_code=status.HTTP_201_CREATED)
def create_lobby_endpoint(
    payload: LobbyCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LobbyOut:
    lobby = create_lobby(db, current_user.id, payload.mode, payload.difficulty)
    members = get_lobby_members(db, lobby.id)
    return _build_lobby_out(lobby, members, db, request)


@router.get("/{code}", response_model=LobbyOut)
def get_lobby_endpoint(
    code: str,
    request: Request,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> LobbyOut:
    lobby = get_lobby_by_code(db, code)
    if lobby is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lobby not found")
    members = get_lobby_members(db, lobby.id)
    return _build_lobby_out(lobby, members, db, request)


@router.post("/{code}/join", response_model=LobbyOut)
def join_lobby_endpoint(
    code: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LobbyOut:
    lobby = get_lobby_by_code(db, code)
    if lobby is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lobby not found")
    join_lobby(db, lobby, current_user.id)
    members = get_lobby_members(db, lobby.id)
    return _build_lobby_out(lobby, members, db, request)


@router.post("/{code}/start", response_model=LobbyStartOut)
def start_lobby_endpoint(
    code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LobbyStartOut:
    lobby = get_lobby_by_code(db, code)
    if lobby is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lobby not found")
    match_id = start_lobby(db, lobby, current_user.id)
    return LobbyStartOut(match_id=match_id)
