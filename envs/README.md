# envs/

Environment-specific configuration (secrets, connection strings).

## Cấu trúc

```
envs/
├── dev/
│   └── .env              # Dev environment variables (local docker-compose)
└── prod/
    └── .env.example      # Template cho production (actual .env in vault)
```

## Files

| File | Vai trò |
|------|---------|
| `dev/.env` | Connection strings cho local dev: MinIO (localhost:9000), Kafka (localhost:9092), ClickHouse, Trino, PostgreSQL |
| `prod/.env.example` | Template cho production. Actual secrets managed by HashiCorp Vault hoặc K8s Secrets |

## Variables

| Variable | Mô tả |
|----------|--------|
| `MINIO_ENDPOINT` | MinIO S3-compatible endpoint |
| `MINIO_ACCESS_KEY` / `MINIO_SECRET_KEY` | MinIO credentials |
| `KAFKA_BROKERS` | Kafka bootstrap servers |
| `HIVE_METASTORE_URI` | Thrift URI cho Hive Metastore |
| `TRINO_HOST` | Trino coordinator host |
| `SPARK_MASTER` | Spark master URL (`k8s://...` in prod, `local[*]` in dev) |
| `CLICKHOUSE_URL` | ClickHouse HTTP interface |
| `GRAFANA_ADMIN_PASSWORD` | Grafana admin password |

## Security

- `.env` files KHÔNG được commit vào git (đã có trong `.gitignore`)
- Production secrets: HashiCorp Vault → K8s ExternalSecrets → Pod env vars
- Dev secrets: plaintext `.env` (local only, non-sensitive defaults)
