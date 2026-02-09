from contextlib import contextmanager

from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

import app.api as api_module
from app.models import Program, ProgramDoc


def test_rank_endpoint_returns_results():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        session.add(
            Program(
                id="1503|1",
                program_stream_id=1,
                discipline_id=13,
                discipline_name="Anesthesiology",
                school_id=100,
                school_name="Sample University",
                program_stream_name="CMG Stream",
                program_site="Halifax",
                program_stream="CMG",
                program_name="Sample University / Anesthesiology / Halifax",
                program_url="https://example.org/program/1",
            )
        )
        session.add(
            ProgramDoc(
                id="1503|1",
                source="https://example.org/program/1",
                page_content="Strong research in anesthesia and perioperative medicine.",
                match_iteration_id=1503,
                program_description_id=1,
            )
        )
        session.commit()

    @contextmanager
    def _test_session():
        with Session(engine) as session:
            yield session

    api_module.get_session = _test_session

    client = TestClient(api_module.app)
    resp = client.post("/rank", json={"query": "research anesthesia", "top_k": 5})
    assert resp.status_code == 200

    body = resp.json()
    assert body["results"]
    assert body["results"][0]["program_id"] == "1503|1"
    assert "description_snippet" in body["results"][0]


def test_rank_endpoint_no_matches_message():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    @contextmanager
    def _test_session():
        with Session(engine) as session:
            yield session

    api_module.get_session = _test_session
    client = TestClient(api_module.app)

    resp = client.post(
        "/rank",
        json={"query": "zzzzzzzzzz", "discipline": "NonexistentDiscipline", "top_k": 5},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["results"] == []
    assert body["message"] == "No matches found"
