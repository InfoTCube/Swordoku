from sqlalchemy.orm import Session

from backend.models.match import MatchParticipant
from backend.models.puzzle import Puzzle


def validate_move(solution: list[int], cell_index: int, value: int) -> bool:
    """Pure function: True if value matches the solution at cell_index."""
    return solution[cell_index] == value


def process_move(
    db: Session,
    puzzle: Puzzle,
    participant: MatchParticipant,
    cell_index: int,
    value: int,
) -> tuple[bool | None, str | None]:
    """
    Apply a player move to their board state and update participant stats.

    Returns (is_correct, rejection_reason).
    rejection_reason is None when the move is accepted; is_correct is None when rejected.
    """
    if puzzle.givens[cell_index] != 0:
        return None, "given_cell"

    board = list(participant.board_state)
    if board[cell_index] != 0:
        return None, "already_filled"

    correct = validate_move(puzzle.solution, cell_index, value)

    if correct:
        participant.cells_correct += 1
        board[cell_index] = value
        participant.board_state = board
    else:
        participant.mistakes += 1

    db.commit()
    db.refresh(participant)
    return correct, None
