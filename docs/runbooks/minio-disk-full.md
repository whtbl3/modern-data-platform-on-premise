# Runbook: MinIO Disk Usage High

**Alert:** `MinIODiskUsageHigh` / `MinIODiskUsageCritical`  
**Severity:** Warning / Critical  
**Impact:** At 95%+, MinIO stops accepting writes. All ingestion fails.

## Triage

```bash
# Check disk usage per bucket
kubectl exec -n lakehouse-prod minio-0 -- mc admin info local

# Check which buckets are largest
kubectl exec -n lakehouse-prod minio-0 -- mc du local/ --depth 2
```

## Expected Growth

| Bucket | Daily Growth | 30-day Projection |
|--------|-------------|-------------------|
| dev-raw | ~6 GB/day | ~180 GB |
| prod-raw | ~6 GB/day | ~180 GB |
| prod-staging | ~3 GB/day (compacted) | ~90 GB |
| prod-curated | ~1.5 GB/day | ~45 GB |
| flink checkpoints | ~500 MB/day | ~15 GB |

## Resolution Steps

### Immediate (>90% usage)

```bash
# 1. Delete old Flink checkpoints (older than 7 days)
kubectl exec -n lakehouse-prod minio-0 -- \
  mc rm --recursive --older-than 7d local/prod-raw/flink/checkpoints/

# 2. Run Iceberg compaction to reclaim space
cd src/transforms
uv run dbt run-operation compact_tables

# 3. Delete expired snapshots (Iceberg table maintenance)
# Run via Trino:
# CALL lakehouse.system.expire_snapshots('raw', 'pos_transactions', TIMESTAMP '2026-08-01 00:00:00');
```

### Medium-term (>85% usage)

```bash
# 1. Set lifecycle policy: auto-delete raw data older than 90 days
kubectl exec -n lakehouse-prod minio-0 -- \
  mc ilm set --expiry-days 90 local/prod-raw

# 2. Enable Iceberg snapshot expiration (keep last 5 snapshots)
# Add to dbt post-hook or Dagster maintenance job
```

### Long-term (capacity planning)

1. Add storage nodes per `docs/phase1/04_constraints.md` hardware inventory
2. Expand MinIO server pool: edit `infra/helm/minio/values-prod.yaml`
3. Consider tiered storage: hot (NVMe) / warm (HDD) with MinIO tiering

## Prevention

- Set up weekly disk usage report
- Alert at 75% for planning, 85% for warning, 95% for critical
- Budget: ~200 GB/month growth → plan 6-month capacity expansions
