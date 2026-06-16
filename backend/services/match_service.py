from datetime import datetime, timezone

from sqlalchemy.orm import Session

from backend.models.match import Match, MatchParticipant

def create_match(db: Session, puzzle_id: str, mode: str, creator_user_id: str) -> Match:
    match = Match(
        puzzle_id=puzzle_id, 
        mode=mode, 
        status="active",
        started_at=datetime.now(timezone.utc),
    )
    db.add(match)
    db.flush() # get match.id before creating participant

    participant = MatchParticipant(match_id=match.id, user_id=creator_user_id)
    db.add(participant)
    db.commit()
    db.refresh(match)
    return match

def get_match(db: Session, match_id: str) -> Match | None:
    return db.get(Match, match_id)

def get_participant(db: Session, match_id: str, user_id: str) -> MatchParticipant | None:
    return db.get(MatchParticipant, {"match_id": match_id, "user_id": user_id})

def get_participants(db: Session, match_id: str) -> list[MatchParticipant]:
    return db.query(MatchParticipant).filter(MatchParticipant.match_id == match_id).all()

def upsert_participant(db: Session, match_id: str, user_id: str) -> MatchParticipant:
    participant = get_participant(db, match_id, user_id)
    if participant is None:
        participant = MatchParticipant(match_id=match_id, user_id=user_id)
        db.add(participant)
        db.commit()
        db.refresh(participant)
    return participant