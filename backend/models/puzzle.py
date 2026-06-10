import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.core.database import Base


class Puzzle(Base):
    __tablename__ = "puzzles"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    difficulty: Mapped[str] = mapped_column(
        Enum("easy", "medium", "hard", name="difficulty_enum"),
        nullable=False,
    )
    givens: Mapped[list] = mapped_column(JSON, nullable=False)
    solution: Mapped[list] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
