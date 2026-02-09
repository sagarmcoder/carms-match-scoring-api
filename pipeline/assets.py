import json
import zipfile
from pathlib import Path

import pandas as pd
from dagster import AssetExecutionContext, asset
from sqlmodel import delete

from app.config import DATA_DIR
from app.db import create_db_and_tables, get_session
from app.models import Discipline, Program, ProgramDoc


def _load_markdown_v2(data_dir: Path) -> list[dict]:
    zip_path = data_dir / "1503_markdown_program_descriptions_v2.zip"
    with zipfile.ZipFile(zip_path) as zf:
        raw = zf.read("1503_markdown_program_descriptions_v2.json")
    return json.loads(raw)


@asset
def extract_raw(context: AssetExecutionContext) -> dict:
    if not DATA_DIR.exists():
        raise FileNotFoundError(f"DATA_DIR not found: {DATA_DIR}")

    discipline_df = pd.read_excel(DATA_DIR / "1503_discipline.xlsx")
    program_df = pd.read_excel(DATA_DIR / "1503_program_master.xlsx")
    docs = _load_markdown_v2(DATA_DIR)

    context.log.info(
        "Extracted rows: disciplines=%s programs=%s docs=%s",
        len(discipline_df),
        len(program_df),
        len(docs),
    )

    return {
        "disciplines": discipline_df.to_dict(orient="records"),
        "programs": program_df.to_dict(orient="records"),
        "docs": docs,
    }


@asset
def transform_clean(extract_raw: dict) -> dict:
    disciplines = []
    for row in extract_raw["disciplines"]:
        disciplines.append(
            {
                "id": int(row["discipline_id"]),
                "name": str(row["discipline"]),
            }
        )

    programs = []
    for row in extract_raw["programs"]:
        stream_id = int(row["program_stream_id"])
        programs.append(
            {
                "id": f"1503|{stream_id}",
                "program_stream_id": stream_id,
                "discipline_id": int(row["discipline_id"]),
                "discipline_name": str(row["discipline_name"]),
                "school_id": int(row["school_id"]),
                "school_name": str(row["school_name"]),
                "program_stream_name": str(row["program_stream_name"]),
                "program_site": str(row["program_site"]),
                "program_stream": str(row["program_stream"]),
                "program_name": str(row["program_name"]),
                "program_url": str(row["program_url"]),
            }
        )

    docs = []
    for row in extract_raw["docs"]:
        doc_id = row["id"]
        right = doc_id.split("|")[-1]
        content = str(row["page_content"])  # markdown text
        docs.append(
            {
                "id": doc_id,
                "source": str(row["metadata"]["source"]),
                "page_content": content,
                "match_iteration_id": 1503,
                "program_description_id": int(right),
            }
        )

    return {"disciplines": disciplines, "programs": programs, "docs": docs}


@asset(deps=[transform_clean])
def load_postgres(context: AssetExecutionContext, transform_clean: dict) -> dict:
    create_db_and_tables()
    with get_session() as session:
        session.exec(delete(ProgramDoc))
        session.exec(delete(Program))
        session.exec(delete(Discipline))

        session.add_all(Discipline(**d) for d in transform_clean["disciplines"])
        session.add_all(Program(**p) for p in transform_clean["programs"])
        session.add_all(ProgramDoc(**d) for d in transform_clean["docs"])
        session.commit()

    counts = {
        "disciplines": len(transform_clean["disciplines"]),
        "programs": len(transform_clean["programs"]),
        "docs": len(transform_clean["docs"]),
    }
    context.log.info("Loaded to postgres: %s", counts)
    return counts
