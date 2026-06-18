from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, Field

class MatchCreate(BaseModel):
    puzzle_id: str
    mode: Literal["casual", "ranked"]

class MatchOut(BaseModel):
    id: str
    puzzle_id: str
    mode: Literal["casual", "ranked"]
    status: str
    started_at: datetime | None

    model_config = { "from_attributes": True }

class MoveMessage(BaseModel):
    cell: Annotated[int, Field(ge=0, le=80)]
    value: Annotated[int, Field(ge=1, le=9)]

class ProgressBroadcast(BaseModel):
    type: Literal["progress"] = "progress"
    user_id: str
    username: str
    cells_correct: int
    mistakes: int

class MatchEndBroadcast(BaseModel):
    type: Literal["match_end"] = "match_end"
    winner_id: str | None
    reason: str