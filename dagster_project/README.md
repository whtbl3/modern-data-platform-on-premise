# dagster_project/

Dagster orchestration — điều phối toàn bộ pipeline VietMart Lakehouse.

## Cấu trúc

```
dagster_project/
├── __init__.py              # Definitions: đăng ký assets, sensors, resources
├── assets/
│   └── __init__.py          # Asset definitions: raw → staging → curated → analytics → quality
├── resources/
│   └── __init__.py          # ConfigurableResource: Spark, MinIO, Trino connections
└── sensors/
    └── __init__.py          # MinIO file sensor: detect new files → trigger runs
```

## Files

| File | Vai trò |
|------|---------|
| `__init__.py` | `Definitions` object — Dagster entry point. Registers tất cả assets, sensors, resources |
| `assets/__init__.py` | 12 assets across 5 groups: **raw** (7 sources), **staging** (dbt), **curated** (dbt intermediate), **analytics** (dbt marts + tests), **quality** (reconciliation) |
| `resources/__init__.py` | 3 resources: `SparkResource` (Iceberg catalog), `MinIOResource` (S3 client), `TrinoResource` (SQL connection) |
| `sensors/__init__.py` | `minio_file_sensor`: poll 9 MinIO prefixes mỗi 60s, trigger partition runs khi có file mới |

## Asset DAG

```
raw_pos_transactions ─────────┐
raw_ecommerce_orders ─────────┤
raw_ecommerce_customers ──────┤
raw_payments ─────────────────┼──→ dbt_staging ──→ dbt_intermediate ──→ dbt_marts ──→ dbt_tests
raw_inventory ────────────────┤                                              │
raw_loyalty_members ──────────┤                                              ▼
raw_clickstream ──────────────┘                                    reconciliation_check
```

## Partitioning

Tất cả assets sử dụng `DailyPartitionsDefinition(start_date="2024-01-01")`.
Mỗi ngày là 1 partition — cho phép backfill và incremental processing.

## Chạy

```bash
# Local dev (UI tại http://localhost:3000)
make dagster

# Launch specific partition
uv run dagster job launch --job __ASSET_JOB --partition 2026-08-23

# Backfill range
uv run dagster job backfill --job __ASSET_JOB --from 2026-08-01 --to 2026-08-23
```
