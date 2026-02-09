from typing import Optional
from sqlmodel import SQLModel, Field


class Discipline(SQLModel, table=True):
    __tablename__ = "disciplines"

    id: int = Field(primary_key=True)
    name: str = Field(index=True)


class Program(SQLModel, table=True):
    __tablename__ = "programs"

    id: str = Field(primary_key=True)
    program_stream_id: int = Field(index=True)
    discipline_id: int = Field(index=True)
    discipline_name: str = Field(index=True)
    school_id: int = Field(index=True)
    school_name: str = Field(index=True)
    program_stream_name: str
    program_site: str
    program_stream: str
    program_name: str = Field(index=True)
    program_url: str


class ProgramDoc(SQLModel, table=True):
    __tablename__ = "program_docs"

    id: str = Field(primary_key=True)
    source: str = Field(index=True)
    page_content: str
    match_iteration_id: Optional[int] = Field(default=None, index=True)
    program_description_id: Optional[int] = Field(default=None, index=True)
