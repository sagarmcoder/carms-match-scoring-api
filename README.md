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
- `docs/samples/`: saved sample API responses

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
docker compose run --rm -e PYTHONPATH=/app api python scripts/run_etl.py
docker compose up --build -d api
docker compose up --build -d dagster
```

## Local (without Docker)
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export DATABASE_URL='postgresql+psycopg2://msagar@localhost:5432/carms'
export DATA_DIR='/Users/msagar/Documents/New project/Junior-Data-Scientist'
PYTHONPATH=. python scripts/run_etl.py

uvicorn app.api:app --reload
```

## API Endpoints
- `GET /health`
- `GET /programs?discipline=Anesthesiology&school=University&limit=25`
- `POST /rank`

## Example Queries (Pretty Output with jq)

Pediatrics query:
```bash
curl -s -X POST http://127.0.0.1:8000/rank \
  -H "Content-Type: application/json" \
  -d '{"query":"pediatrics interview process","discipline":"Pediatrics","top_k":5}' | jq .
```

No-match query:
```bash
curl -s -X POST http://127.0.0.1:8000/rank \
  -H "Content-Type: application/json" \
  -d '{"query":"zzzzzzzzzz","discipline":"NonexistentDiscipline","top_k":5}' | jq .
```

Saved outputs:
- `docs/samples/rank_pediatrics.json`
- `docs/samples/rank_no_matches.json`

## Verified ETL Counts
```text
disciplines: 37
programs: 815
program_docs: 815
```

## Tests
```bash
pytest -q
```

## Notes
- Ranking uses a deterministic LangChain embedding class for offline demo reliability.
- Scores are rounded to 4 decimals and include a short `description_snippet`.
- If no results are found, the API returns `message: "No matches found"`.
- For higher semantic quality, swap `HashEmbeddings` with sentence-transformers or hosted embeddings.

## Future Plans
- Upgrade LangChain ranking from `HashEmbeddings` to `sentence-transformers` (`all-MiniLM-L6-v2`) for stronger semantic relevance.
- Deploy API + Dagster + PostgreSQL on AWS (ECS/EC2 + RDS) with environment-based configuration.
- Add scheduled Dagster runs and data quality checks for automated refresh and monitoring.
