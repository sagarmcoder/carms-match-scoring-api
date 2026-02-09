from contextlib import contextmanager
from sqlmodel import Session, SQLModel, create_engine

from app.config import DATABASE_URL


engine = create_engine(DATABASE_URL, echo=False)


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)


@contextmanager
def get_session() -> Session:
    with Session(engine) as session:
        yield session
