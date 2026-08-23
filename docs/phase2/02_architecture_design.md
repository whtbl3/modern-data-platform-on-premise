# Phase 2.2: Architecture Design

## Target Architecture (TO-BE)

```
┌──────────────────────────────────────────────────────────────────────────────────────┐
│                        VIETMART DATA PLATFORM — ON-PREMISE                           │
├──────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  DATA SOURCES             INGESTION              STORAGE (MinIO + Iceberg)           │
│  ────────────            ──────────              ───────────────────────             │
│                                                                                      │
│  ┌──────────┐                                    ┌─────────────────────────┐         │
│  │ POS      │──CSV(15min)──→ Spark Job ─────────→│ s3://raw/pos/           │         │
│  │ 120 store│                                    │                         │         │
│  └──────────┘                                    │                         │         │
│                                                  │ s3://raw/ecommerce/     │         │
│  ┌──────────┐                                    │                         │         │
│  │E-commerce│──CDC(Debezium)──→ Kafka ──────────→│ s3://raw/clickstream/   │         │
│  │PostgreSQL│                     │              │                         │         │
│  └──────────┘                     │              │ s3://raw/payments/      │         │
│                                   │              │                         │         │
│  ┌──────────┐                     │              │ s3://raw/inventory/     │         │
│  │Clickstrm │──SDK──→ Kafka ──────┤              │                         │         │
│  │Web+Mobile│                     │              └──────────┬──────────────┘         │
│  └──────────┘                     │                         │                        │
│                                   │                         │ Dagster                │
│  ┌──────────┐                     │                         │ orchestrates           │
│  │ Payment  │──SFTP/API──→ Spark Job ──→         ┌──────────▼──────────────┐         │
│  │ Gateways │                                    │ s3://staging/           │         │
│  └──────────┘                                    │   Clean, dedup, typed   │         │
│                                   │              │   Iceberg tables        │         │
│  ┌──────────┐                     │              └──────────┬──────────────┘         │
│  │ SAP      │──CSV(30min)──→ Spark Job ──→                  │                        │
│  │Inventory │                                    ┌──────────▼──────────────┐         │
│  └──────────┘                                    │ s3://curated/           │         │
│                                                  │   Business logic        │         │
│  ┌──────────┐                                    │   Unified customer      │         │
│  │ Loyalty  │──CDC──→ Kafka ──→ Spark ──→        │   Enriched orders       │         │
│  │ MySQL    │                                    └──────────┬──────────────┘         │
│  └──────────┘                                               │                        │
│                                                  ┌──────────▼──────────────┐         │
│                                                  │ s3://analytics/         │         │
│                                                  │   Aggregated metrics    │         │
│                                                  │   Mart tables           │         │
│                                                  └──────────┬──────────────┘         │
│                                                             │                        │
│  STREAMING PATH                    SERVING LAYER            │                        │
│  ──────────────                   ──────────────            │                        │
│                                                             │                        │
│  Kafka ──→ Flink ──→ ClickHouse   Trino ←───────────────────┘                        │
│  (clickstream,       (real-time    (batch SQL, self-service)                         │
│   flash sale         aggregation)        │                                           │
│   events)                  │             │                                           │
│                            │             ▼                                           │
│                            └─────→ Superset (dashboards)                             │
│                                                                                      │
│  GOVERNANCE & OPS          ORCHESTRATION          INFRASTRUCTURE                     │
│  ────────────────         ──────────────          ──────────────                     │
│                                                                                      │
│  OpenMetadata              Dagster                 Kubernetes (RKE2)                 │
│  Hive Metastore            • Sensors (MinIO)       Helm + ArgoCD                     │
│  Schema Registry           • Software-defined      Prometheus + Grafana              │
│                              assets                KEDA (autoscaling)                │
│                            • Schedules                                               │
│                            • Quality gates                                           │
│                                                                                      │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Requirement → Architecture Mapping

| Requirement | Architectural Decision | Component |
|-------------|------------------------|-----------|
| FR-1: Auto ingest from POS, e-commerce, payment | Spark batch jobs (POS/payment CSV) + Debezium CDC (e-commerce/loyalty) | Spark, Kafka Connect, Dagster sensors |
| FR-2: Unified customer view | Identity resolution in curated layer (match by phone/email) | Spark job in curated, dbt model |
| FR-3: Daily revenue aggregation | dbt models: staging → curated → analytics mart | dbt (fct_revenue_daily) |
| FR-4: Revenue reconciliation | Dedicated reconciliation job comparing 3 sources | reconciliation.py, Dagster scheduled |
| FR-5: Self-service SQL | Trino cluster exposed to business via Superset | Trino + Superset |
| FR-6: Customer segmentation (RFM) | dbt model computing RFM scores daily | dbt (dim_customers) |
| FR-7: Real-time flash sale dashboard | Kafka → Flink (windowed agg) → ClickHouse → Superset | Streaming path |
| FR-8: Clickstream analysis | Kafka → Flink (session windows) → ClickHouse | Streaming path |
| FR-9: Inventory monitoring | Spark ingests SAP exports → alert on low stock | Spark + Dagster + Soda |
| NFR-1: Batch < 2h | Spark Dynamic Allocation, parallel jobs | KEDA, Dagster parallelism |
| NFR-2: Streaming < 60s | Flink with 5s watermark | Flink autoscaler |
| NFR-10: 10x spike handling | Flink autoscaler + Kafka partition increase | Pre-scale before flash sale |
| NFR-11: PII encryption | MinIO server-side encryption, TLS everywhere | MinIO SSE, K8s network policies |
| NFR-12: Column-level access | OpenMetadata policies + Trino access control | OpenMetadata + Trino |

---

## Data Flow: Batch Path (Primary)

```
Schedule: Dagster runs every hour (POS) and daily (reconciliation)

1. INGEST (Dagster sensor detects new files)
   POS CSV → Spark → MinIO raw/pos/{store_id}/{date}/{file}.csv
   Payment SFTP → Spark → MinIO raw/payments/{gateway}/{date}/
   Inventory SAP → Spark → MinIO raw/inventory/{date}/

2. STAGE (Dagster asset: staging_*)
   raw/ → Spark (validate, dedup, type cast, normalize) → Iceberg staging tables

3. CURATE (Dagster asset: curated_*)
   staging tables → Spark/dbt (joins, business logic, identity resolution) → Iceberg curated tables

4. ANALYTICS (Dagster asset: analytics_*)
   curated tables → dbt (aggregate, window functions) → Iceberg analytics tables

5. SERVE
   analytics tables → Trino → Superset dashboards auto-refresh
```

## Data Flow: Streaming Path (Flash Sale & Clickstream)

```
Always-on: Flink jobs running continuously

1. INGEST
   Web/Mobile SDK → Kafka topic: clickstream (Avro, Schema Registry)
   E-commerce events → Kafka topic: order_events (via Debezium CDC)

2. PROCESS (Flink)
   clickstream → session windowing → ClickHouse (sessions_realtime)
   order_events → tumbling window 1min → ClickHouse (revenue_realtime)
   order_events → filter flash_sale_id → ClickHouse (flash_sale_live)

3. SERVE
   ClickHouse → Superset real-time dashboard (auto-refresh 10s)

4. RECONCILE (Daily, Dagster)
   Compare: ClickHouse revenue_realtime vs Iceberg fct_revenue_daily
   Alert if drift > 2%
```

---

## Deployment Architecture (K8s)

```
┌─────────────────────────────────────────────────────────────────┐
│ Kubernetes Cluster (RKE2)                                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ Namespace: platform                                             │
│   MinIO (4 nodes, distributed)                                  │
│   Kafka (Strimzi, 3 brokers)                                    │
│   Hive Metastore (2 replicas)                                   │
│   Schema Registry (2 replicas)                                  │
│   OpenMetadata                                                  │
│                                                                 │
│ Namespace: compute                                              │
│   Spark Operator                                                │
│   Flink Operator + TaskManagers                                 │
│   ClickHouse Operator (2 shards × 2 replicas)                   │
│   Trino (1 coordinator + 3 workers)                             │
│                                                                 │
│ Namespace: orchestration                                        │
│   Dagster (webserver + daemon)                                  │
│                                                                 │
│ Namespace: serving                                              │
│   Superset (2 replicas)                                         │
│                                                                 │
│ Namespace: monitoring                                           │
│   Prometheus + Grafana                                          │
│   KEDA                                                          │
│   Alertmanager → Slack                                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Trade-off Decision Log

| Decision | Option A | Option B | Chosen | Reasoning |
|----------|----------|----------|--------|-----------|
| CDC tool | Debezium | Custom Kafka producer | Debezium | Battle-tested, schema evolution, exactly-once |
| Streaming engine | Flink | Spark Structured Streaming | Flink | True streaming (not micro-batch), better state mgmt, exactly-once |
| Real-time OLAP | ClickHouse | Druid | ClickHouse | Simpler ops, better SQL support, smaller team can manage |
| Query engine | Trino | Spark SQL | Trino | Lower latency for ad-hoc, concurrent users, always-on |
| Orchestration | Dagster | Airflow | Dagster | Asset-based (matches our 4-layer model), better observability, modern |
| Table format | Iceberg | Delta Lake | Iceberg | Better multi-engine support (Spark+Trino+Flink all read), vendor-neutral |
| Identity resolution | Spark (custom) | External tool (Zingg) | Spark (custom) | Simple matching (phone/email), Zingg overkill for our case |
| Dashboard | Superset | Metabase | Superset | Better SQL Lab for power users, Trino connector mature |
| K8s distro | RKE2 | K3s | RKE2 | Production-grade, CIS hardened, better for 20-node cluster |
| Schema enforcement | Schema Registry (Avro) | JSON Schema (application) | Schema Registry | Centralized, versioned, breaking change detection |
