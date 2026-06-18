import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.core.database import Base


class Lobby(Base):
    __tablename__ = "lobbies"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    code: Mapped[str] = mapped_column(String(8), unique=True, nullable=False)
    creator_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False)
    mode: Mapped[str] = mapped_column(
        Enum("casual", "ranked", name="lobby_mode_enum"),
        nullable=False,
    )
    difficulty: Mapped[str] = mapped_column(
        Enum("easy", "medium", "hard", name="lobby_difficulty_enum"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        Enum("waiting", "active", name="lobby_status_enum"),
        default="waiting",
        nullable=False,
    )
    match_id: Mapped[str | None] = mapped_column(String, ForeignKey("matches.id"), nullable=True)
    time_limit_min: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    mistake_limit: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class LobbyMember(Base):
    __tablename__ = "lobby_members"

    lobby_id: Mapped[str] = mapped_column(String, ForeignKey("lobbies.id"), primary_key=True)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), primary_key=True)
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
