# Phase 2.4: Implementation Plan — Sprint Breakdown

## Timeline: 16 tuần (8 sprints × 2 tuần)

```
Week  1  2  3  4  5  6  7  8  9  10  11  12  13  14  15  16
      ├──────┤├──────┤├──────┤├──────┤├──────┤├───────┤├──────┤├──────┤
      Sprint1 Sprint2 Sprint3 Sprint4 Sprint5  Sprint6  Sprint7 Sprint8
      ─────── ─────── ─────── ─────── ───────  ───────  ─────── ───────
      Infra   Batch   Batch   Self-   Stream   Stream   Govern  Optimize
      Setup   Ingest  Transform Service Ingest  Serve    ance    Harden
                                                                        
      ════════════════════════════════╗  ════════════════════════════════
                  MVP (Week 8)        ║       Full Platform (Week 16)
                                      ╚════════════════════════════════
```

---

## Sprint 1 (Week 1-2): Infrastructure Foundation

**Goal**: K8s cluster running, core services deployed, team can develop locally

| Task | Owner | Deliverable |
|------|-------|-------------|
| K8s cluster setup (RKE2, 20 nodes) | Platform Eng | Cluster ready, kubectl access for all |
| MinIO deployment (4 nodes, distributed) | Platform Eng | Buckets created (raw/staging/curated/analytics) |
| Kafka deployment (Strimzi, 3 brokers) | Platform Eng | Topics created, producer/consumer test pass |
| Hive Metastore + PostgreSQL | Platform Eng | Metastore accessible from Spark/Trino |
| Dagster deployment | Data Eng | Web UI accessible, can define assets |
| Docker-compose local dev | Data Eng | Team can develop locally without K8s |
| Monitoring (Prometheus + Grafana) | Platform Eng | Basic K8s dashboards |
| ArgoCD setup | Platform Eng | GitOps: push to main → deploy |
| CI pipeline (lint + test) | Senior Eng | PR checks running |

**Exit criteria**: `make up` works locally. Dagster UI shows empty assets. MinIO console accessible.

---

## Sprint 2 (Week 3-4): Batch Ingestion Pipeline

**Goal**: POS + Payment data flows from source → raw → staging automatically

| Task | Owner | Deliverable |
|------|-------|-------------|
| POS ingestion job (120 stores CSV) | Data Eng 1 | Raw POS data in MinIO, partitioned by store+date |
| Payment ingestion (VNPay, Momo, Card) | Data Eng 2 | 3 sources → raw/payments/{gateway}/{date}/ |
| Staging: stg_pos__transactions | Data Eng 1 | Dedup, date normalize, Iceberg table |
| Staging: stg_payments__* (3 gateways) | Data Eng 2 | Normalized amounts, unified schema |
| Soda quality checks (staging) | Data Analyst | Quality gates active: dedup, null, range |
| Dagster sensors (detect new POS files) | Senior Eng | Auto-trigger on new data arrival |
| Datagen: realistic POS + payment data | Data Eng 1 | Test data matching real volume/patterns |

**Exit criteria**: Daily pipeline runs automatically. Soda checks pass. Dagster lineage shows raw→staging.

---

## Sprint 3 (Week 5-6): Batch Transform + Analytics

**Goal**: curated + analytics layers producing business-ready data

| Task | Owner | Deliverable |
|------|-------|-------------|
| E-commerce CDC setup (Debezium → Kafka → MinIO) | Senior Eng | Orders + customers flowing to raw |
| Staging: stg_ecommerce__orders, stg_ecommerce__customers | Data Eng 1 | Clean e-commerce data |
| Curated: identity resolution (dim_customers_unified) | Senior Eng | Unified customer matching phone/email |
| Curated: fct_pos_transactions, fct_ecom_orders | Data Eng 2 | Orders joined with customer + product dims |
| Analytics: mart_revenue_daily | Data Eng 1 | dbt model, tested, documented |
| Analytics: mart_reconciliation | Data Eng 2 | POS vs Payment vs E-commerce comparison |
| Reconciliation alert job | Data Analyst | Alert if discrepancy > 1% |
| dbt tests + documentation | Data Analyst | All models tested, descriptions written |

**Exit criteria**: `dbt run` produces all marts. Reconciliation runs daily. Revenue numbers match across sources.

---

## Sprint 4 (Week 7-8): Self-Service + MVP Go-Live ✅

**Goal**: Business users can query and see dashboards. **MVP complete.**

| Task | Owner | Deliverable |
|------|-------|-------------|
| Trino deployment (3 workers) | Platform Eng | SQL queries < 30s on analytics tables |
| Superset deployment + Trino connection | Platform Eng | Superset UI accessible |
| Dashboard: CEO daily revenue | Data Analyst | Auto-refresh, store/region/category drill-down |
| Dashboard: CFO reconciliation | Data Analyst | 3-way comparison, alert status |
| Dashboard: Regional manager scorecard | Data Analyst | Per-store daily performance |
| Customer RFM model (mart_customer_rfm) | Data Eng 1 | dbt model, daily refresh |
| User access control (Trino + Superset) | Senior Eng | Each department sees their data only |
| Self-service training (2h workshop) | Data Analyst | Business users can use SQL Lab |
| Load testing | Platform Eng | 30 concurrent users, queries < 30s |

**Exit criteria (MVP)**:
- ✅ CEO sees yesterday's revenue by 8 AM
- ✅ CFO reconciliation automated (alert on drift)
- ✅ 3 regional managers self-serve daily scorecard
- ✅ CMO sees customer RFM segments
- ✅ Revenue discrepancy < 0.1%
- ✅ Pipeline runs reliably for 1 week without manual intervention

---

## Sprint 5 (Week 9-10): Streaming Pipeline

**Goal**: Real-time path operational for flash sale + clickstream

| Task | Owner | Deliverable |
|------|-------|-------------|
| Flink deployment (Flink Operator) | Platform Eng | Flink cluster running on K8s |
| ClickHouse deployment (2 shards) | Platform Eng | ClickHouse queryable from Superset |
| Schema Registry setup | Senior Eng | Avro schemas for clickstream events |
| Clickstream → Kafka (SDK integration) | Data Eng 1 | Web+Mobile events flowing to Kafka |
| Flink job: clickstream → sessions_realtime | Senior Eng | Session windowing, 60s latency |
| Flink job: orders → revenue_realtime | Senior Eng | Tumbling window 1min aggregation |
| ClickHouse DDL + materialized views | Data Eng 2 | Tables optimized for dashboard queries |
| Flink autoscaler configuration | Platform Eng | Scale on backpressure |

**Exit criteria**: Clickstream events visible in ClickHouse within 60s. Flash sale simulation handles 600 events/sec.

---

## Sprint 6 (Week 11-12): Streaming Serving + Inventory

**Goal**: Real-time dashboards live. Inventory monitoring started.

| Task | Owner | Deliverable |
|------|-------|-------------|
| Dashboard: Flash sale real-time | Data Analyst | Live revenue, conversion, cart value |
| Dashboard: Clickstream funnel | Data Analyst | User journey, drop-off visualization |
| Reconciliation: batch vs stream | Senior Eng | Daily job comparing Iceberg vs ClickHouse |
| Inventory ingestion (SAP → MinIO) | Data Eng 1 | Stock levels every 30 min |
| Inventory model (fct_inventory_daily) | Data Eng 2 | Stock vs safety threshold |
| Inventory alert (stockout prediction) | Data Eng 2 | Alert 3 days before predicted stockout |
| KEDA scaling for Kafka consumer lag | Platform Eng | Auto-scale Flink on spike |

**Exit criteria**: Flash sale simulation: dashboard updates in < 60s. Inventory alerts triggering correctly.

---

## Sprint 7 (Week 13-14): Governance & Quality

**Goal**: Data is discoverable, governed, and quality is enforced

| Task | Owner | Deliverable |
|------|-------|-------------|
| OpenMetadata deployment | Platform Eng | UI accessible, auto-discovery configured |
| Auto-discovery: Iceberg tables + ClickHouse | Senior Eng | All tables visible in catalog |
| Ownership assignment (per department) | Data Analyst | Each table has owner + description |
| Column-level access policies | Senior Eng | Marketing cannot see payment details |
| Soda checks expansion (all layers) | Data Eng 1 | Comprehensive quality rules |
| Data freshness monitoring | Data Eng 2 | Alert if data stale > SLA |
| Dagster alerts → Slack integration | Platform Eng | Pipeline failures → team Slack channel |
| Runbook documentation | All | How to handle common failures |

**Exit criteria**: New analyst can find, understand, and query any table within 1 hour. Access control enforced.

---

## Sprint 8 (Week 15-16): Optimize & Harden

**Goal**: Production-ready, performant, resilient

| Task | Owner | Deliverable |
|------|-------|-------------|
| Iceberg compaction jobs (scheduled) | Data Eng 1 | Small files merged, query performance up |
| Partition optimization (time-based) | Data Eng 2 | Queries scan less data |
| MinIO lifecycle policies (hot/cold) | Platform Eng | Old data moves to slower storage |
| Disaster recovery test | Platform Eng | Full restore from backup < 4h |
| Load test: 2x current volume | All | Pipeline handles growth projection |
| Flash sale pre-scale procedure | Platform Eng | Runbook: scale 2h before event |
| Security audit | Senior Eng | TLS, encryption, access review |
| Performance tuning (Trino, ClickHouse) | Platform Eng | Query p95 < 30s confirmed |
| Handover documentation | All | Architecture, operations, troubleshooting |

**Exit criteria (Full Platform)**:
- ✅ All original requirements (FR-1 through FR-9) delivered
- ✅ Platform handles 2x current volume
- ✅ Recovery tested: RPO < 24h, RTO < 4h
- ✅ Self-service adopted by 3+ departments
- ✅ Engineer ad-hoc time reduced from 70% to < 10%

---

## Post-Platform Backlog

| Item | Priority | Sprint estimate |
|------|----------|-----------------|
| FR-10: Delivery SLA tracking | High | 1 sprint |
| FR-12: Churn prediction (ML) | Medium | 2 sprints |
| FR-11: Data catalog self-service onboard | Medium | 1 sprint |
| Hybrid cloud (replicate to cloud for DR) | Low | 3 sprints |
| ML feature store on curated layer | Low | 2 sprints |
| Multi-tenant (separate business units) | Low | 2 sprints |
