# VietMart Lakehouse — Modern Data Platform (On-Premise)

VietMart Group: top-10 Vietnamese retail chain, 120 stores, $200M/year revenue.  
Platform giải quyết: data fragmentation, 3-8% revenue discrepancy, 3-5 day report latency.

## Architecture

```
Sources ──→ Kafka ──→ Flink ──→ ClickHouse ──→ Superset (real-time)
                │
                └──→ MinIO (raw)
                          │
                Dagster orchestrates:
                          │
                Spark (raw → Iceberg) → dbt (staging → intermediate → marts)
                          │
                     Trino ──→ Superset (batch)
                          │
                OpenMetadata (governance)
```

## Stack

| Layer | Tool |
|-------|------|
| Storage | MinIO + Apache Iceberg (4-layer: raw → staging → curated → analytics) |
| Catalog | Hive Metastore |
| Governance | OpenMetadata |
| Batch | Spark (PySpark) on K8s |
| Streaming | Kafka + Flink → ClickHouse |
| Real-time OLAP | ClickHouse |
| Transform | dbt-trino (Kimball star schema) |
| Query | Trino (federated: Iceberg + ClickHouse) |
| BI | Apache Superset |
| Orchestration | Dagster |
| Infra | K8s (RKE2) + Helm + ArgoCD |
| Monitoring | Prometheus + Grafana + Alertmanager + KEDA |

## Project Structure

```
├── docs/                   # Phase 1 (Discovery) + Phase 2 (Design) + Runbooks
├── src/
│   ├── datagen/            # Data generators: 6 VietMart sources (POS, e-com, payments, etc.)
│   ├── batch/              # Spark batch jobs (raw ingestion)
│   ├── streaming/          # Flink streaming jobs (orders + clickstream → ClickHouse)
│   ├── transforms/         # dbt project (Kimball: staging → intermediate → marts)
│   ├── shared_logic/       # Business rules dùng chung batch/streaming
│   └── quality/            # Soda checks + batch/stream reconciliation
├── dagster_project/        # Dagster: assets, sensors, resources (orchestration)
├── infra/
│   ├── helm/               # Helm values per component (dev + prod)
│   ├── argocd/             # GitOps deployments
│   ├── keda/               # Auto-scaling (Spark + Kafka consumer)
│   └── monitoring/         # PrometheusRules + Grafana dashboards
├── tests/                  # Unit tests (43 tests)
├── ci/                     # GitLab CI pipeline
└── envs/                   # Environment configs (dev/prod)
```

Mỗi thư mục có `README.md` giải thích vai trò từng file.

## Quick Start

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Setup
uv sync

# Start infra (MinIO, Kafka, ClickHouse, Trino, PostgreSQL)
make up

# Generate sample data (10K POS, 1K orders, 5K clickstream)
make datagen-batch

# Run Dagster UI (http://localhost:3000)
make dagster

# Run dbt models
make dbt-run

# Run tests
make test

# Lint
uv run ruff check src/ dagster_project/
```

## Data Sources (VietMart)

| Source | Volume | Format | Path |
|--------|--------|--------|------|
| POS (Oracle) | 800K txn/day | CSV | Batch → MinIO |
| E-commerce (PostgreSQL) | 50K orders/day | CDC/JSON | Batch + Stream |
| Clickstream | 5M events/day | JSON | Stream (Kafka) |
| Payments (VNPay/Momo/Card) | 65K/day | JSON (3 formats) | Batch → MinIO |
| Inventory (SAP) | 50K SKUs × 120 stores | JSON | Batch → MinIO |
| Loyalty (MySQL) | 1.5M members | CDC/JSON | Batch → MinIO |

## Environments

| Env | K8s Namespace | Mô tả |
|-----|--------------|--------|
| dev | `lakehouse-dev` | docker-compose local, sample data |
| prod | `lakehouse-prod` | 20-server on-prem cluster, full data, HA |

## Auto-Scaling

| Component | Mechanism | Trigger |
|-----------|-----------|---------|
| Spark executors | Dynamic Allocation | Job queue depth |
| Spark jobs | KEDA ScaledObject | MinIO file count |
| Flink | Native Autoscaler | Backpressure / utilization |
| Kafka | Strimzi + Cruise Control | Partition load |
| ClickHouse | ClickHouse Operator | CPU/memory utilization |

## Monitoring & Alerting

- **3 Grafana dashboards:** Pipeline Overview, Streaming Real-time, Infrastructure
- **15 PrometheusRule alerts** across: pipeline health, streaming, storage, ClickHouse, data quality
- **Alertmanager routing:** Slack channels by severity (#data-alerts, #data-alerts-critical, #finance-data)
- **8 runbooks** covering every critical alert scenario
- **On-call quick reference:** decision tree, SLAs, escalation path
