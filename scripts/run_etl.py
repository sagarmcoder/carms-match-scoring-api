from dagster import materialize

from pipeline.assets import extract_raw, transform_clean, load_postgres


if __name__ == "__main__":
    result = materialize([extract_raw, transform_clean, load_postgres])
    if not result.success:
        raise SystemExit(1)
    print("ETL completed")
