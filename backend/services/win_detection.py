from datetime import datetime, timezone
from itertools import combinations

from sqlalchemy.orm import Session

from backend.models.match import Match, MatchParticipant
from backend.models.user import User
from backend.services.elo_service import calculate_elo

WIN_THRESHOLD = 81


def has_won(participant: MatchParticipant) -> bool:
    return participant.cells_correct >= WIN_THRESHOLD


def rank_participants(participants: list[MatchParticipant]) -> list[MatchParticipant]:
    """Rank by cells_correct desc, then mistakes asc."""
    return sorted(participants, key=lambda p: (-p.cells_correct, p.mistakes))


def determine_winner(participants: list[MatchParticipant]) -> MatchParticipant | None:
    """Top-ranked participant, or None if the top two are tied (draw)."""
    ranked = rank_participants(participants)
    top = ranked[0]
    if len(ranked) > 1:
        runner_up = ranked[1]
        if runner_up.cells_correct == top.cells_correct and runner_up.mistakes == top.mistakes:
            return None
    return top


def _pairwise_result(a: MatchParticipant, b: MatchParticipant) -> float:
    """Outcome for `a` against `b`: 1.0 win, 0.5 draw, 0.0 loss."""
    if a.cells_correct != b.cells_correct:
        return 1.0 if a.cells_correct > b.cells_correct else 0.0
    if a.mistakes != b.mistakes:
        return 1.0 if a.mistakes < b.mistakes else 0.0
    return 0.5


def _apply_elo(db: Session, participants: list[MatchParticipant]) -> None:
    """
    Apply ELO updates for a ranked match. For matches with more than two
    participants, ratings are updated via round-robin pairwise comparisons
    and the resulting deltas are averaged per player.
    """
    users = {p.user_id: db.get(User, p.user_id) for p in participants}
    for p in participants:
        p.elo_before = users[p.user_id].elo_rating

    deltas: dict[str, list[int]] = {p.user_id: [] for p in participants}
    for a, b in combinations(participants, 2):
        result_a = _pairwise_result(a, b)
        new_a, new_b = calculate_elo(users[a.user_id].elo_rating, users[b.user_id].elo_rating, result_a)
        deltas[a.user_id].append(new_a - users[a.user_id].elo_rating)
        deltas[b.user_id].append(new_b - users[b.user_id].elo_rating)

    for p in participants:
        delta = round(sum(deltas[p.user_id]) / len(deltas[p.user_id]))
        users[p.user_id].elo_rating += delta
        p.elo_after = users[p.user_id].elo_rating


def finalize_match(
    db: Session,
    match: Match,
    participants: list[MatchParticipant],
    reason: str,
) -> MatchParticipant | None:
    """
    Resolve a finished match: rank participants, apply ELO for ranked
    matches, update win/loss records, and persist everything in a single
    transaction.

    Returns the winning participant, or None on a draw.
    """
    winner = determine_winner(participants)

    if match.mode == "ranked":
        _apply_elo(db, participants)

    if winner is not None:
        for participant in participants:
            user = db.get(User, participant.user_id)
            if participant.user_id == winner.user_id:
                user.wins += 1
            else:
                user.losses += 1

    match.status = "finished"
    match.ended_at = datetime.now(timezone.utc)
    match.winner_id = winner.user_id if winner is not None else None

    db.commit()
    db.refresh(match)
    for participant in participants:
        db.refresh(participant)

    return winner
