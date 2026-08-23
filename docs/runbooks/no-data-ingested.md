# Runbook: No Data Ingested

**Alert:** `NoDataIngested`  
**Severity:** Warning  
**Impact:** Downstream models will use stale data. Reports for affected sources are outdated.

## Triage

```bash
# Check which raw asset hasn't materialized
# Dagster UI → Assets → filter by "raw_" → check last materialization time

# Check if files exist in MinIO
kubectl exec -n lakehouse-prod minio-0 -- mc ls local/prod-raw/pos/$(date +%Y-%m-%d)/
kubectl exec -n lakehouse-prod minio-0 -- mc ls local/prod-raw/ecommerce/orders/$(date +%Y-%m-%d)/
```

## Common Causes by Source

| Source | Why It Stops | Check |
|--------|-------------|-------|
| POS (CSV) | Store file server down, network issue | Ping store gateway, check NAS mount |
| E-commerce (CDC) | Debezium connector crashed | Check Kafka Connect status |
| Payments (API) | Gateway API rate limit / maintenance | Check gateway status page |
| Inventory (SAP) | SAP batch job didn't run | Contact SAP admin |
| Loyalty (CDC) | MySQL binlog position lost | Check Debezium connector logs |
| Clickstream | Tracking script broken, CDN issue | Check website JS console |

## Resolution Steps

### POS CSV files missing
```bash
# Check the file transfer service
ssh file-gateway "ls -la /export/pos/$(date +%Y-%m-%d)/"

# If files exist but weren't copied to MinIO:
# Manually trigger the file sync
ssh file-gateway "rsync /export/pos/ s3://prod-raw/pos/ --endpoint http://minio:9000"
```

### E-commerce / Loyalty CDC stopped
```bash
# Check Kafka Connect connectors
curl -s http://kafka-connect:8083/connectors | jq .
curl -s http://kafka-connect:8083/connectors/ecommerce-cdc/status | jq .

# Restart failed connector
curl -X POST http://kafka-connect:8083/connectors/ecommerce-cdc/restart
```

### Dagster sensor not triggering
```bash
# Check sensor status in Dagster UI → Sensors
# Or via CLI:
uv run dagster sensor list

# If sensor is stopped, start it:
uv run dagster sensor start minio_file_sensor
```

### Manual backfill after source recovers
```bash
# Once files arrive, trigger backfill for missed dates
uv run dagster job backfill --job __ASSET_JOB \
  --partition-set daily_partitions \
  --from 2026-08-21 --to 2026-08-23
```

## Escalation

- If POS data missing for >4 hours during business hours: contact store IT
- If e-commerce data missing: contact platform team (revenue impact)
- If all sources missing simultaneously: likely network/infra issue — escalate to infra team
