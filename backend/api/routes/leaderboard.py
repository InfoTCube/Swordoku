from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.models.user import User
from backend.schemas.user import LeaderboardEntry

router = APIRouter(prefix="/leaderboard", tags=["leaderboard"])


@router.get("", response_model=list[LeaderboardEntry])
def get_leaderboard(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[LeaderboardEntry]:
    users = (
        db.query(User)
        .order_by(User.elo_rating.desc(), User.username.asc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return [
        LeaderboardEntry(
            rank=offset + i + 1,
            username=u.username,
            elo_rating=u.elo_rating,
            wins=u.wins,
            losses=u.losses,
        )
        for i, u in enumerate(users)
    ]
