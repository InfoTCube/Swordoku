from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class LobbyCreate(BaseModel):
    mode: Literal["casual", "ranked"]
    difficulty: Literal["easy", "medium", "hard"]


class LobbyMemberOut(BaseModel):
    user_id: str
    username: str
    joined_at: datetime


class LobbyOut(BaseModel):
    id: str
    code: str
    invite_url: str
    mode: Literal["casual", "ranked"]
    difficulty: Literal["easy", "medium", "hard"]
    status: Literal["waiting", "active"]
    players: list[LobbyMemberOut]
    match_id: str | None


class LobbyStartOut(BaseModel):
    match_id: str
