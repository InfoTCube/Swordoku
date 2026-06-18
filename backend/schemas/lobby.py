from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class LobbyCreate(BaseModel):
    mode: Literal["casual", "ranked"]
    difficulty: Literal["easy", "medium", "hard"]
    time_limit_min: int = Field(default=10, ge=5, le=25)
    mistake_limit: int = Field(default=3, ge=0, le=10)


class LobbyMemberOut(BaseModel):
    user_id: str
    username: str
    joined_at: datetime


class LobbyOut(BaseModel):
    id: str
    code: str
    creator_id: str
    invite_url: str
    mode: Literal["casual", "ranked"]
    difficulty: Literal["easy", "medium", "hard"]
    status: Literal["waiting", "active"]
    players: list[LobbyMemberOut]
    match_id: str | None
    time_limit_min: int
    mistake_limit: int


class LobbyStartOut(BaseModel):
    match_id: str
