"""Test Dagster asset definitions load correctly."""
from dagster_project.assets import analytics_assets, curated_assets, raw_assets, staging_assets


def test_raw_assets_count():
    assert len(raw_assets) == 7  # pos, ecom_orders, ecom_customers, payments, inventory, loyalty, clickstream


def test_staging_assets_count():
    assert len(staging_assets) == 1  # dbt_staging


def test_curated_assets_count():
    assert len(curated_assets) == 1  # dbt_intermediate


def test_analytics_assets_count():
    assert len(analytics_assets) == 3  # dbt_marts, dbt_tests, reconciliation_check


def test_asset_group_names():
    for asset_def in raw_assets:
        groups = list(asset_def.group_names_by_key.values())
        assert all(g == "raw" for g in groups)

    for asset_def in staging_assets:
        groups = list(asset_def.group_names_by_key.values())
        assert all(g == "staging" for g in groups)

    for asset_def in curated_assets:
        groups = list(asset_def.group_names_by_key.values())
        assert all(g == "curated" for g in groups)


def test_all_assets_have_partitions():
    all_assets = raw_assets + staging_assets + curated_assets + analytics_assets
    for asset_def in all_assets:
        assert asset_def.partitions_def is not None


def test_definitions_load():
    from dagster_project import defs
    assert defs is not None
    assert defs.resources is not None
