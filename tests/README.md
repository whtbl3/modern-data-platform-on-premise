# tests/

Unit tests cho VietMart Lakehouse platform.

## Cấu trúc

```
tests/
├── __init__.py
├── test_datagen.py          # 21 tests — tất cả 7 VietMart generators
├── test_shared_logic.py     # 15 tests — business rules + SQL templates
├── test_dagster_assets.py   # 7 tests — asset definitions, groups, partitions
└── test_batch_staging.py    # 3 tests — Spark dedup/filter logic (cần PySpark)
```

## Files

| File | Vai trò | Dependencies |
|------|---------|-------------|
| `test_datagen.py` | Test generators: POS, e-commerce, payments, inventory, loyalty, clickstream. Verify: field names, formats, deterministic output, distributions | None (pure Python) |
| `test_shared_logic.py` | Test shared rules: order filter SQL, revenue aggregation, inventory alerts, phone normalization, RFM segments | None (pure Python) |
| `test_dagster_assets.py` | Test Dagster definitions load: asset counts, group names, partitions, resource config | dagster |
| `test_batch_staging.py` | Test Spark transforms: dedup, null filter, amount validation | pyspark, chispa |

## Chạy

```bash
# Tất cả tests (trừ Spark — cần Java)
make test

# Chỉ datagen + shared logic (nhanh, không cần external deps)
uv run pytest tests/test_datagen.py tests/test_shared_logic.py -v

# Chỉ Dagster
uv run pytest tests/test_dagster_assets.py -v

# Với coverage
uv run pytest --cov=src --cov=dagster_project tests/
```

## Test strategy

- **Unit tests** (this dir): logic thuần, không cần infra
- **Integration tests**: chạy trong CI với docker-compose (MinIO, Trino, Kafka)
- **dbt tests**: `make dbt-test` — data quality assertions trên actual data
- **Soda checks**: `make quality` — quality rules trên staging/marts tables
