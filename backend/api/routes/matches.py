from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.models.user import User
from backend.schemas.match import MatchCreate, MatchOut
from backend.services.auth_service import get_current_user
from backend.services.match_service import create_match, get_match
from backend.models.puzzle import Puzzle

router = APIRouter(prefix="/matches", tags=["matches"])

@router.post("", response_model=MatchOut, status_code=status.HTTP_201_CREATED)
def create_match_endpoint(
    payload: MatchCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MatchOut:
    puzzle = db.get(Puzzle, payload.puzzle_id)
    if puzzle is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Puzzle not found")
    
    match = create_match(db, payload.puzzle_id, payload.mode, current_user.id)
    return MatchOut.model_validate(match)