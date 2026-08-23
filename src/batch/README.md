# src/batch/

Spark batch jobs cho raw ingestion và staging transform.

## Cấu trúc

```
batch/
├── Dockerfile                   # Spark container image (uv + dependencies)
└── jobs/
    ├── raw_ingestion.py         # JDBC/file source → MinIO raw layer (Iceberg)
    └── staging_transform.py     # Raw → staging: dedup, null filter, type cast
```

## Files

| File | Vai trò |
|------|---------|
| `jobs/raw_ingestion.py` | Đọc từ JDBC sources (PostgreSQL, MySQL) hoặc file (CSV), ghi vào MinIO raw bucket dưới dạng Iceberg tables |
| `jobs/staging_transform.py` | Đọc raw Iceberg, áp dụng dedup + validation (shared_logic), ghi vào staging Iceberg |
| `Dockerfile` | Base: spark:3.5, cài uv, copy pyproject.toml + source code |

## Lưu ý

Trong production flow, Dagster orchestrate các jobs này:
1. Dagster raw assets gọi Spark để ingest
2. Dagster dbt assets thay thế staging_transform (dbt chạy qua Trino)

File `staging_transform.py` là Spark-native alternative nếu cần xử lý heavy (>10M records) mà Trino không handle tốt.

## Scaling

- Spark dynamic allocation: min 1, max 10 executors
- KEDA ScaledObject trigger dựa trên MinIO file count (see `infra/keda/spark-scaledobject.yaml`)
