import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.core.database import Base


class Match(Base):
    __tablename__ = "matches"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    puzzle_id: Mapped[str] = mapped_column(String, ForeignKey("puzzles.id"), nullable=False)
    mode: Mapped[str] = mapped_column(
        Enum("casual", "ranked", name="match_mode_enum"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        Enum("waiting", "active", "finished", name="match_status_enum"),
        default="waiting",
        nullable=False,
    )
    time_limit_s: Mapped[int] = mapped_column(Integer, default=600, nullable=False)
    mistake_limit: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    winner_id: Mapped[str | None] = mapped_column(String, ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class MatchParticipant(Base):
    __tablename__ = "match_participants"

    match_id: Mapped[str] = mapped_column(String, ForeignKey("matches.id"), primary_key=True)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), primary_key=True)
    cells_correct: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    mistakes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    solve_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    elo_before: Mapped[int | None] = mapped_column(Integer, nullable=True)
    elo_after: Mapped[int | None] = mapped_column(Integer, nullable=True)
    board_state: Mapped[list] = mapped_column(JSON, nullable=False, default=lambda: [0] * 81)
