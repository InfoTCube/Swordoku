import pytest
from pydantic import ValidationError

from backend.models.match import Match, MatchParticipant
from backend.models.puzzle import Puzzle
from backend.models.user import User
from backend.schemas.match import MoveMessage
from backend.services.move_validator import process_move, validate_move


def _setup(db):
    """Seed DB with a user, puzzle, match, and participant.

    Cell 0 is a given (value=5). All other cells are empty with solution=5.
    """
    user = User(username="tester", email="tester@test.com", password_hash="x")
    db.add(user)
    db.flush()

    solution = [5] * 81
    givens = [0] * 81
    givens[0] = 5  # cell 0 is pre-filled

    puzzle = Puzzle(difficulty="easy", givens=givens, solution=solution)
    db.add(puzzle)
    db.flush()

    match = Match(puzzle_id=puzzle.id, mode="casual", status="active")
    db.add(match)
    db.flush()

    participant = MatchParticipant(
        match_id=match.id,
        user_id=user.id,
        board_state=[0] * 81,
    )
    db.add(participant)
    db.commit()
    db.refresh(puzzle)
    db.refresh(participant)
    return puzzle, participant


# --- validate_move (pure function) ---

def test_validate_move_correct_value():
    solution = [3] + [0] * 80
    assert validate_move(solution, 0, 3) is True


def test_validate_move_wrong_value():
    solution = [3] + [0] * 80
    assert validate_move(solution, 0, 9) is False


def test_validate_move_uses_correct_index():
    solution = [1, 2, 3] + [0] * 78
    assert validate_move(solution, 1, 2) is True
    assert validate_move(solution, 2, 3) is True
    assert validate_move(solution, 0, 2) is False


# --- MoveMessage schema (out-of-range rejected at schema boundary) ---

def test_move_message_rejects_cell_above_80():
    with pytest.raises(ValidationError):
        MoveMessage(cell=81, value=5)


def test_move_message_rejects_cell_below_0():
    with pytest.raises(ValidationError):
        MoveMessage(cell=-1, value=5)


def test_move_message_rejects_value_above_9():
    with pytest.raises(ValidationError):
        MoveMessage(cell=0, value=10)


def test_move_message_rejects_value_below_1():
    with pytest.raises(ValidationError):
        MoveMessage(cell=0, value=0)


def test_move_message_accepts_valid():
    msg = MoveMessage(cell=40, value=5)
    assert msg.cell == 40
    assert msg.value == 5


# --- process_move (needs DB) ---

def test_process_move_correct_accepted(db):
    puzzle, participant = _setup(db)
    is_correct, reason = process_move(db, puzzle, participant, 1, 5)
    assert is_correct is True
    assert reason is None


def test_process_move_correct_increments_cells_correct(db):
    puzzle, participant = _setup(db)
    process_move(db, puzzle, participant, 1, 5)
    assert participant.cells_correct == 1
    assert participant.mistakes == 0


def test_process_move_correct_updates_board_state(db):
    puzzle, participant = _setup(db)
    process_move(db, puzzle, participant, 1, 5)
    assert participant.board_state[1] == 5


def test_process_move_wrong_value_increments_mistakes(db):
    puzzle, participant = _setup(db)
    is_correct, reason = process_move(db, puzzle, participant, 1, 3)
    assert is_correct is False
    assert reason is None
    assert participant.mistakes == 1
    assert participant.cells_correct == 0


def test_process_move_wrong_value_does_not_update_board(db):
    puzzle, participant = _setup(db)
    process_move(db, puzzle, participant, 1, 3)
    assert participant.board_state[1] == 0


def test_process_move_given_cell_rejected(db):
    puzzle, participant = _setup(db)
    is_correct, reason = process_move(db, puzzle, participant, 0, 5)
    assert is_correct is None
    assert reason == "given_cell"


def test_process_move_given_cell_no_stat_change(db):
    puzzle, participant = _setup(db)
    process_move(db, puzzle, participant, 0, 5)
    assert participant.cells_correct == 0
    assert participant.mistakes == 0


def test_process_move_already_filled_rejected(db):
    puzzle, participant = _setup(db)
    # Pre-fill cell 2 as if a correct move already landed
    board = list(participant.board_state)
    board[2] = 5
    participant.board_state = board
    db.commit()
    db.refresh(participant)

    is_correct, reason = process_move(db, puzzle, participant, 2, 5)
    assert is_correct is None
    assert reason == "already_filled"


def test_process_move_already_filled_no_stat_change(db):
    puzzle, participant = _setup(db)
    board = list(participant.board_state)
    board[2] = 5
    participant.board_state = board
    db.commit()
    db.refresh(participant)

    original_correct = participant.cells_correct
    original_mistakes = participant.mistakes
    process_move(db, puzzle, participant, 2, 5)
    assert participant.cells_correct == original_correct
    assert participant.mistakes == original_mistakes
