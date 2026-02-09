from fastapi import FastAPI, Query
from sqlmodel import select

from app.config import TOP_K_DEFAULT
from app.db import create_db_and_tables, get_session
from app.models import Program
from app.schemas import RankRequest, RankResponse
from app.services.ranker import ProgramRanker


app = FastAPI(title="CaRMS Match Scoring API", version="0.1.0")


@app.on_event("startup")
def startup() -> None:
    create_db_and_tables()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/programs")
def list_programs(
    discipline: str | None = Query(default=None),
    school: str | None = Query(default=None),
    limit: int = Query(default=25, ge=1, le=200),
) -> list[dict]:
    with get_session() as session:
        stmt = select(Program)
        if discipline:
            stmt = stmt.where(Program.discipline_name.ilike(f"%{discipline}%"))
        if school:
            stmt = stmt.where(Program.school_name.ilike(f"%{school}%"))

        rows = session.exec(stmt.limit(limit)).all()
        return [row.model_dump() for row in rows]


@app.post("/rank", response_model=RankResponse)
def rank_programs(payload: RankRequest) -> RankResponse:
    with get_session() as session:
        ranker = ProgramRanker(session)
        top_k = payload.top_k or TOP_K_DEFAULT
        results = ranker.rank(payload.query, top_k=top_k, discipline=payload.discipline)

    return RankResponse(
        query=payload.query,
        total_candidates=len(results),
        results=results,
    )
