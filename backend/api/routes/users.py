from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.models.match import Match, MatchParticipant
from backend.models.puzzle import Puzzle
from backend.models.user import User
from backend.schemas.user import MatchHistoryEntry, UserProfile
from backend.services.auth_service import get_current_user

router = APIRouter(prefix="/users", tags=["users"])


def _get_user_or_404(username: str, db: Session) -> User:
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.get("/{username}", response_model=UserProfile)
def get_user_profile(
    username: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> UserProfile:
    return _get_user_or_404(username, db)


@router.get("/{username}/matches", response_model=list[MatchHistoryEntry])
def get_user_matches(
    username: str,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[MatchHistoryEntry]:
    user = _get_user_or_404(username, db)

    participations = (
        db.query(MatchParticipant, Match, Puzzle)
        .join(Match, Match.id == MatchParticipant.match_id)
        .join(Puzzle, Puzzle.id == Match.puzzle_id)
        .filter(
            MatchParticipant.user_id == user.id,
            Match.status == "finished",
        )
        .order_by(Match.ended_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    entries: list[MatchHistoryEntry] = []
    for p, match, puzzle in participations:
        others = (
            db.query(MatchParticipant)
            .filter(
                MatchParticipant.match_id == match.id,
                MatchParticipant.user_id != user.id,
            )
            .all()
        )
        opponent_names: list[str] = []
        for op in others:
            ou = db.get(User, op.user_id)
            if ou:
                opponent_names.append(ou.username)

        if match.winner_id is None:
            result = "draw"
        elif match.winner_id == user.id:
            result = "win"
        else:
            result = "loss"

        elo_delta: int | None = None
        if p.elo_before is not None and p.elo_after is not None:
            elo_delta = p.elo_after - p.elo_before

        entries.append(
            MatchHistoryEntry(
                match_id=match.id,
                ended_at=match.ended_at,
                mode=match.mode,
                difficulty=puzzle.difficulty,
                result=result,
                opponents=opponent_names,
                elo_delta=elo_delta,
                cells_correct=p.cells_correct,
                mistakes=p.mistakes,
            )
        )

    return entries
