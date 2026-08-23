# infra/

Infrastructure as Code — K8s deployments cho VietMart Lakehouse.

## Cấu trúc

```
infra/
├── helm/                    # Helm values cho từng component (dev + prod)
│   ├── minio/               # Object storage (4 nodes, erasure coding)
│   ├── kafka/               # Event streaming (Strimzi operator)
│   ├── flink/               # Stream processing (Flink Kubernetes Operator)
│   ├── spark/               # Batch processing (Spark on K8s)
│   ├── clickhouse/          # Real-time OLAP (ClickHouse Operator)
│   ├── trino/               # SQL query engine (federated queries)
│   ├── hive-metastore/      # Iceberg catalog (Hive Metastore)
│   ├── dagster/             # Orchestrator
│   ├── superset/            # BI dashboards
│   ├── openmetadata/        # Data governance & catalog
│   └── monitoring/          # kube-prometheus-stack (Prometheus + Grafana + Alertmanager)
├── argocd/                  # GitOps deployment
│   ├── dev/applications.yaml    # ArgoCD ApplicationSet cho dev namespace
│   └── prod/applications.yaml   # ArgoCD ApplicationSet cho prod namespace
├── keda/                    # Auto-scaling
│   ├── spark-scaledobject.yaml          # Scale Spark dựa trên MinIO file count
│   └── kafka-consumer-scaledobject.yaml # Scale consumers dựa trên Kafka lag
├── monitoring/              # Observability
│   ├── prometheus-rules/
│   │   └── lakehouse-alerts.yaml    # 15 PrometheusRule alerts (5 categories)
│   ├── grafana-dashboards/
│   │   ├── pipeline-overview.json   # Pipeline health, dbt timing, reconciliation
│   │   ├── streaming-realtime.json  # Kafka lag, Flink throughput, flash sale
│   │   └── infrastructure.json      # MinIO disk, K8s nodes, CPU/memory
│   └── grafana-configmap.yaml       # K8s ConfigMap to mount dashboards
└── docker/
    └── trino/catalog/
        ├── iceberg.properties       # Trino ↔ Iceberg (Hive Metastore)
        └── clickhouse.properties    # Trino ↔ ClickHouse (federated queries)
```

## Environments

| Environment | Namespace | Mô tả |
|------------|-----------|--------|
| dev | `lakehouse-dev` | Local dev (docker-compose) hoặc K8s dev namespace |
| prod | `lakehouse-prod` | Production on-premise cluster (20 servers) |

## Deployment flow

```
Git push → ArgoCD detect change → Helm upgrade → K8s rolling update
```

## Key decisions

- **2 environments only** (dev + prod) — K8s namespace separation
- **ArgoCD ApplicationSet** — 1 file per env, auto-sync enabled
- **KEDA** — event-driven autoscaling (không dùng HPA vì cần custom metrics)
- **No Nessie** — Hive Metastore namespaces (`dev.*` / `prod.*`) đủ cho catalog isolation
