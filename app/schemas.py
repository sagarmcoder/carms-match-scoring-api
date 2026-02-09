from typing import Optional
from pydantic import BaseModel, Field


class RankRequest(BaseModel):
    query: str = Field(min_length=3)
    discipline: Optional[str] = None
    top_k: int = Field(default=10, ge=1, le=50)


class RankResult(BaseModel):
    program_id: str
    program_name: str
    school_name: str
    discipline_name: str
    score: float


class RankResponse(BaseModel):
    query: str
    total_candidates: int
    results: list[RankResult]
