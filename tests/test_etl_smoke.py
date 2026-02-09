from dagster import build_asset_context

from pipeline.assets import extract_raw, transform_clean


def test_extract_transform_counts():
    context = build_asset_context()
    raw = extract_raw(context)
    cleaned = transform_clean(raw)

    assert len(cleaned["disciplines"]) >= 30
    assert len(cleaned["programs"]) == 815
    assert len(cleaned["docs"]) == 815
