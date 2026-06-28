from datetime import datetime

from pydantic import BaseModel


class PuzzleOut(BaseModel):
    id: str
    difficulty: str
    givens: list[int]
    created_at: datetime

    model_config = {"from_attributes": True}


class PracticeOut(BaseModel):
    id: str
    difficulty: str
    givens: list[int]
    solution: list[int]
    created_at: datetime

    model_config = {"from_attributes": True}
