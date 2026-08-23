# On-Call Quick Reference — VietMart Lakehouse

## Key URLs

| Service | URL | Credentials |
|---------|-----|-------------|
| Dagster UI | http://dagster:3000 | SSO |
| Grafana | http://grafana:3000 | admin / vault |
| MinIO Console | http://minio:9001 | vault |
| Trino UI | http://trino:8080 | N/A |
| Flink Dashboard | http://flink-jm:8081 | N/A |
| ArgoCD | http://argocd:8080 | admin / vault |
| Kafka UI | http://kafka-ui:8080 | N/A |

## Quick Health Check

```bash
# All pods running?
kubectl get pods -n lakehouse-prod | grep -v Running

# Any alerts firing?
curl -s http://alertmanager:9093/api/v2/alerts | jq '.[].labels.alertname'

# Kafka consumer lag
kubectl exec -n lakehouse-prod kafka-0 -- kafka-consumer-groups.sh \
  --bootstrap-server localhost:9092 --list

# MinIO healthy?
kubectl exec -n lakehouse-prod minio-0 -- mc admin info local

# Latest Dagster run status
curl -s http://dagster:3000/graphql -H 'Content-Type: application/json' \
  -d '{"query": "{ runsOrError { __typename ... on Runs { results(limit: 5) { status runId } } } }"}'
```

## Decision Tree

```
Alert fires
├── Is it a pipeline failure? (DagsterRunFailed, DbtTestFailure)
│   └── → docs/runbooks/dagster-run-failed.md
├── Is it streaming? (KafkaConsumerLag, FlinkJobNotRunning)
│   └── → docs/runbooks/kafka-consumer-lag.md or flink-job-down.md
├── Is it storage? (MinIODiskUsage, MinIONodeDown)
│   └── → docs/runbooks/minio-disk-full.md
├── Is it data quality? (RevenueReconciliationDrift)
│   └── → docs/runbooks/reconciliation-drift.md
└── Is it infrastructure? (NodeDiskPressure, PodCrashLooping)
    └── Escalate to infra team
```

## SLAs

| Metric | Target | Measurement |
|--------|--------|-------------|
| Batch data freshness | < 2 hours from source | Time from raw file arrival to mart availability |
| Real-time latency | < 60 seconds | Kafka produce → ClickHouse queryable |
| Revenue reconciliation | < 1% drift | Batch vs stream daily totals |
| Dashboard availability | 99.5% | Superset + ClickHouse uptime |
| Alert response time | < 15 min (critical) | Time from alert to first action |

## Escalation Path

1. **L1 — On-call engineer:** Investigate, apply runbook fix
2. **L2 — Senior data engineer:** Complex root cause, architecture decisions
3. **L3 — CTO / Infra lead:** Hardware failures, capacity planning, budget decisions

## Slack Channels

- `#data-alerts` — All warnings
- `#data-alerts-critical` — Critical alerts only
- `#finance-data` — Revenue-impacting alerts
- `#data-engineering` — Team discussion
