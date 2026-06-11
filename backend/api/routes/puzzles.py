from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.models.puzzle import Puzzle
from backend.models.user import User
from backend.schemas.puzzle import PuzzleOut
from backend.services.auth_service import get_current_user
from backend.services.difficulty_classifier import Difficulty, classify_difficulty
from backend.services.puzzle_generator import generate_solved_grid, make_puzzle

router = APIRouter(prefix="/puzzles", tags=["puzzles"])


@router.post("", response_model=PuzzleOut, status_code=status.HTTP_201_CREATED)
def create_puzzle(
    difficulty: Difficulty = Query(Difficulty.medium),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> PuzzleOut:
    solved = generate_solved_grid()
    givens, solution = make_puzzle(solved, difficulty.value)
    actual_difficulty = classify_difficulty(givens)

    puzzle = Puzzle(
        difficulty=actual_difficulty.value,
        givens=givens,
        solution=solution,
    )
    db.add(puzzle)
    db.commit()
    db.refresh(puzzle)
    return PuzzleOut.model_validate(puzzle)


@router.get("/{puzzle_id}", response_model=PuzzleOut)
def get_puzzle(
    puzzle_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> PuzzleOut:
    puzzle = db.get(Puzzle, puzzle_id)
    if puzzle is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Puzzle not found")
    return PuzzleOut.model_validate(puzzle)
