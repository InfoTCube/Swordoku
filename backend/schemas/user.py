from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    username: Annotated[str, Field(min_length=1, max_length=32)]
    email: EmailStr
    password: Annotated[str, Field(min_length=8, max_length=72)]


class UserOut(BaseModel):
    id: str
    username: str
    email: str
    elo_rating: int
    wins: int
    losses: int
    created_at: datetime

    model_config = {"from_attributes": True}


class UserProfile(BaseModel):
    username: str
    elo_rating: int
    wins: int
    losses: int

    model_config = {"from_attributes": True}


class MatchHistoryEntry(BaseModel):
    match_id: str
    ended_at: datetime | None
    mode: Literal["casual", "ranked"]
    difficulty: str
    result: Literal["win", "loss", "draw"]
    opponents: list[str]
    elo_delta: int | None
    cells_correct: int
    mistakes: int


class LeaderboardEntry(BaseModel):
    rank: int
    username: str
    elo_rating: int
    wins: int
    losses: int

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
