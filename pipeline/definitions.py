from dagster import Definitions

from pipeline.assets import extract_raw, transform_clean, load_postgres


defs = Definitions(assets=[extract_raw, transform_clean, load_postgres])
