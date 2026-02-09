# CaRMS Match Scoring API

Backend MVP for CaRMS residency program exploration and ranking using:
- PostgreSQL
- SQLAlchemy/SQLModel
- Dagster
- LangChain
- FastAPI

## What it does
- Ingests CaRMS source files from `Junior-Data-Scientist/`
- Loads normalized tables into PostgreSQL
- Exposes API endpoints for program filtering and semantic ranking
- Provides a Dagster ETL flow (`extract_raw -> transform_clean -> load_postgres`)

## Project Structure
- `app/models.py`: SQLModel tables
- `app/db.py`: DB engine/session
- `app/api.py`: FastAPI endpoints
- `app/services/ranker.py`: LangChain-based ranking
- `pipeline/assets.py`: Dagster assets
- `pipeline/definitions.py`: Dagster Definitions
- `scripts/run_etl.py`: CLI ETL runner
- `tests/`: smoke tests

## Data Source
Expected local path (mounted in Docker):
- `./Junior-Data-Scientist`

Required files used:
- `1503_discipline.xlsx`
- `1503_program_master.xlsx`
- `1503_markdown_program_descriptions_v2.zip`

## Quick Start (Docker)
```bash
docker compose up --build -d postgres
```

Run ETL once:
```bash
docker compose run --rm api python scripts/run_etl.py
```

Start API:
```bash
docker compose up --build -d api
```

Start Dagster UI:
```bash
docker compose up --build -d dagster
```

## API Endpoints
- `GET /health`
- `GET /programs?discipline=Anesthesiology&school=University&limit=25`
- `POST /rank`

Example:
```bash
curl -X POST http://localhost:8000/rank \
  -H "Content-Type: application/json" \
  -d '{"query":"research heavy anesthesia program", "discipline":"Anesthesiology", "top_k":5}'
```

## Local (without Docker)
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL='postgresql+psycopg2://postgres:postgres@localhost:5432/carms'
export DATA_DIR='/Users/msagar/Documents/New project/Junior-Data-Scientist'
python scripts/run_etl.py
uvicorn app.api:app --reload
```

## Tests
```bash
pytest -q
```

## Notes
- Ranking uses a deterministic LangChain embedding class for offline demo reliability.
- For production, swap `HashEmbeddings` with an API-backed embedding model.
