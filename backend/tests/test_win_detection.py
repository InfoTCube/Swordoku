import pytest

from backend.models.match import Match, MatchParticipant
from backend.models.puzzle import Puzzle
from backend.models.user import User
from backend.services.win_detection import (
    WIN_THRESHOLD,
    determine_winner,
    finalize_match,
    has_won,
    rank_participants,
)


def _participant(cells_correct=0, mistakes=0, user_id="u1", match_id="m1"):
    """Transient (no DB) MatchParticipant for pure-function tests."""
    return MatchParticipant(
        match_id=match_id,
        user_id=user_id,
        cells_correct=cells_correct,
        mistakes=mistakes,
        board_state=[0] * 81,
    )


def _seed_db(db, p1_cells=81, p2_cells=50, p1_mistakes=0, p2_mistakes=3, mode="ranked"):
    """Create two users, a puzzle, a match, and two participants in the DB."""
    u1 = User(username="p1", email="p1@test.com", password_hash="x", elo_rating=1200)
    u2 = User(username="p2", email="p2@test.com", password_hash="x", elo_rating=1200)
    db.add(u1)
    db.add(u2)
    db.flush()

    puzzle = Puzzle(difficulty="easy", givens=[0] * 81, solution=[1] * 81)
    db.add(puzzle)
    db.flush()

    match = Match(puzzle_id=puzzle.id, mode=mode, status="active")
    db.add(match)
    db.flush()

    mp1 = MatchParticipant(
        match_id=match.id, user_id=u1.id,
        cells_correct=p1_cells, mistakes=p1_mistakes, board_state=[0] * 81,
    )
    mp2 = MatchParticipant(
        match_id=match.id, user_id=u2.id,
        cells_correct=p2_cells, mistakes=p2_mistakes, board_state=[0] * 81,
    )
    db.add(mp1)
    db.add(mp2)
    db.commit()
    for obj in (u1, u2, match, mp1, mp2):
        db.refresh(obj)
    return u1, u2, match, mp1, mp2


# --- has_won ---

def test_has_won_at_threshold():
    assert has_won(_participant(cells_correct=WIN_THRESHOLD)) is True


def test_has_won_above_threshold():
    assert has_won(_participant(cells_correct=WIN_THRESHOLD + 1)) is True


def test_has_won_one_below_threshold():
    assert has_won(_participant(cells_correct=WIN_THRESHOLD - 1)) is False


def test_has_won_at_zero():
    assert has_won(_participant(cells_correct=0)) is False


def test_win_threshold_is_81():
    assert WIN_THRESHOLD == 81


# --- rank_participants ---

def test_rank_by_cells_desc():
    p1 = _participant(cells_correct=40, user_id="a")
    p2 = _participant(cells_correct=70, user_id="b")
    ranked = rank_participants([p1, p2])
    assert ranked[0].user_id == "b"
    assert ranked[1].user_id == "a"


def test_rank_tiebreaker_mistakes_asc():
    p1 = _participant(cells_correct=50, mistakes=5, user_id="a")
    p2 = _participant(cells_correct=50, mistakes=2, user_id="b")
    ranked = rank_participants([p1, p2])
    assert ranked[0].user_id == "b"


def test_rank_three_players():
    p1 = _participant(cells_correct=80, mistakes=1, user_id="a")
    p2 = _participant(cells_correct=81, mistakes=0, user_id="b")
    p3 = _participant(cells_correct=80, mistakes=0, user_id="c")
    ranked = rank_participants([p1, p2, p3])
    assert ranked[0].user_id == "b"
    assert ranked[1].user_id == "c"
    assert ranked[2].user_id == "a"


# --- determine_winner ---

def test_determine_winner_clear_winner():
    p1 = _participant(cells_correct=70, user_id="a")
    p2 = _participant(cells_correct=40, user_id="b")
    assert determine_winner([p1, p2]).user_id == "a"


def test_determine_winner_none_on_exact_draw():
    p1 = _participant(cells_correct=50, mistakes=3, user_id="a")
    p2 = _participant(cells_correct=50, mistakes=3, user_id="b")
    assert determine_winner([p1, p2]) is None


def test_determine_winner_tiebreaker_by_mistakes():
    p1 = _participant(cells_correct=50, mistakes=5, user_id="a")
    p2 = _participant(cells_correct=50, mistakes=1, user_id="b")
    assert determine_winner([p1, p2]).user_id == "b"


# --- finalize_match ---

def test_finalize_match_sets_status_finished(db):
    _, _, match, mp1, mp2, = _seed_db(db)
    finalize_match(db, match, [mp1, mp2], "completed")
    assert match.status == "finished"


def test_finalize_match_sets_winner_id(db):
    u1, _, match, mp1, mp2 = _seed_db(db)
    finalize_match(db, match, [mp1, mp2], "completed")
    assert match.winner_id == u1.id


def test_finalize_match_sets_ended_at(db):
    _, _, match, mp1, mp2 = _seed_db(db)
    finalize_match(db, match, [mp1, mp2], "completed")
    assert match.ended_at is not None


def test_finalize_match_updates_win_loss_record(db):
    u1, u2, match, mp1, mp2 = _seed_db(db, mode="casual")
    finalize_match(db, match, [mp1, mp2], "completed")
    db.refresh(u1)
    db.refresh(u2)
    assert u1.wins == 1
    assert u1.losses == 0
    assert u2.wins == 0
    assert u2.losses == 1


def test_finalize_match_ranked_updates_elo(db):
    u1, u2, match, mp1, mp2 = _seed_db(db, mode="ranked")
    finalize_match(db, match, [mp1, mp2], "completed")
    db.refresh(u1)
    db.refresh(u2)
    assert u1.elo_rating > 1200
    assert u2.elo_rating < 1200


def test_finalize_match_casual_no_elo_change(db):
    u1, u2, match, mp1, mp2 = _seed_db(db, mode="casual")
    finalize_match(db, match, [mp1, mp2], "completed")
    db.refresh(u1)
    db.refresh(u2)
    assert u1.elo_rating == 1200
    assert u2.elo_rating == 1200


def test_finalize_match_draw_no_winner_id(db):
    u1, u2, match, mp1, mp2 = _seed_db(db, p1_cells=50, p2_cells=50, p1_mistakes=3, p2_mistakes=3)
    winner = finalize_match(db, match, [mp1, mp2], "time_limit")
    assert winner is None
    assert match.winner_id is None


def test_finalize_match_time_limit_winner_by_cells(db):
    u1, u2, match, mp1, mp2 = _seed_db(db, p1_cells=60, p2_cells=40, mode="casual")
    winner = finalize_match(db, match, [mp1, mp2], "time_limit")
    assert winner is not None
    assert winner.user_id == u1.id


def test_finalize_match_time_limit_winner_by_mistakes_tiebreaker(db):
    u1, u2, match, mp1, mp2 = _seed_db(
        db, p1_cells=50, p2_cells=50, p1_mistakes=1, p2_mistakes=5, mode="casual"
    )
    winner = finalize_match(db, match, [mp1, mp2], "time_limit")
    assert winner is not None
    assert winner.user_id == u1.id
