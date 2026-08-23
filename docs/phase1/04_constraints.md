# Phase 1.4: Constraints & Assumptions

## Constraints

| Loại | Nội dung | Impact on Design |
|------|----------|------------------|
| **Infrastructure** | 20 bare-metal servers (đã mua), on-premise DC tại HCM | Phải dùng on-prem stack, không cloud-native services |
| **Compliance** | PII (tên, SĐT, email khách hàng) phải lưu trong VN | Không dùng cloud storage cho PII data |
| **Team** | 3 data engineers + 1 platform engineer + 1 data analyst | Cần automation cao, self-service để scale impact |
| **Budget** | Hardware đã có. Budget cho software: $0 (open-source only) | Toàn bộ stack phải open-source hoặc community edition |
| **Timeline** | MVP 8 tuần, full platform 16 tuần | Phải chia sprint rõ, prioritize ruthlessly |
| **Skills** | Team biết Python, SQL, Docker. Đang học K8s. Không biết Java/Scala | PySpark, PyFlink — không dùng Scala. K8s cần training 2 tuần đầu |
| **Network** | Internal network 10Gbps giữa servers. Internet 1Gbps | Data transfer giữa services nhanh, external API calls limited |
| **Maintenance window** | Chủ nhật 2:00-6:00 AM cho planned maintenance | Pipeline phải handle 4h downtime/tuần gracefully |

---

## Hardware Inventory

```
┌──────────────────────────────────────────────────────────────────────┐
│ ON-PREMISE DATA CENTER — HCM                                          │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│ Master nodes (K8s control plane): 3 servers                          │
│   • CPU: 16 cores (Xeon Gold 5218)                                   │
│   • RAM: 64 GB                                                        │
│   • Storage: 500 GB SSD                                               │
│                                                                       │
│ Worker nodes (compute): 12 servers                                    │
│   • CPU: 32 cores (Xeon Gold 6248)                                   │
│   • RAM: 128 GB                                                       │
│   • Storage: 2 TB NVMe SSD                                           │
│                                                                       │
│ Storage nodes (MinIO): 4 servers                                      │
│   • CPU: 16 cores                                                     │
│   • RAM: 64 GB                                                        │
│   • Storage: 8 × 4 TB HDD (JBOD) = 32 TB per node = 128 TB total    │
│                                                                       │
│ GPU node (future ML): 1 server                                        │
│   • CPU: 32 cores                                                     │
│   • RAM: 256 GB                                                       │
│   • GPU: 2 × NVIDIA A30                                              │
│   • Storage: 2 TB NVMe                                                │
│                                                                       │
│ TOTAL: 20 servers                                                     │
│ TOTAL RAM: ~1.7 TB                                                    │
│ TOTAL CPU: ~480 cores                                                 │
│ TOTAL STORAGE: 128 TB (object) + 30 TB (SSD compute)                │
│                                                                       │
│ Network: 10 Gbps internal, redundant switches                         │
│ UPS: 4h battery backup                                                │
│ Generator: diesel, auto-start                                         │
│                                                                       │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Assumptions

| # | Assumption | Risk if wrong | Mitigation |
|---|-----------|---------------|------------|
| 1 | POS system can export CSV every 15 min (not just daily) | Batch latency increases to T+1 | Negotiate with POS vendor for API/CDC |
| 2 | E-commerce PostgreSQL supports CDC (logical replication) | Cannot do real-time ingest | Use pg_dump hourly as fallback |
| 3 | 128 TB storage lasts 2+ years with compression | Need to buy more hardware | Iceberg compaction + lifecycle policies |
| 4 | 12 worker nodes enough for current workload + 2x growth | Performance degradation | K8s autoscaling within available nodes |
| 5 | Team can learn K8s + Spark + Flink in 4 weeks (with training) | Timeline slips | Start with simple batch, add streaming Sprint 5+ |
| 6 | Flash sale 10x spike lasts < 4 hours | Need more streaming capacity | Pre-scale Flink + Kafka before events |
| 7 | SAP can export inventory every 30 min reliably | Inventory data stale | Build alerting on data freshness |
| 8 | Business users can write basic SQL (with training) | Self-service fails, back to ad-hoc | Superset pre-built dashboards as fallback |

---

## Team Structure & Responsibilities

```
┌─────────────────────────────────────────────────────────┐
│ DATA PLATFORM TEAM (5 people)                            │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ Platform Engineer (1) — Anh Nam                         │
│   • K8s cluster setup & maintenance                     │
│   • Helm charts, ArgoCD, monitoring                     │
│   • MinIO, Kafka, ClickHouse operations                 │
│                                                          │
│ Senior Data Engineer (1) — Chị Hoa                      │
│   • Architecture decisions                              │
│   • Streaming pipeline (Flink)                          │
│   • Shared logic, data quality framework                │
│   • Code review & mentoring                             │
│                                                          │
│ Data Engineer (2) — Anh Tuấn, Chị Linh                 │
│   • Batch pipelines (Spark, Dagster)                    │
│   • dbt models                                          │
│   • Source connectors & ingestion                       │
│   • Testing                                             │
│                                                          │
│ Data Analyst (1) — Anh Bình                             │
│   • Superset dashboards                                 │
│   • Business requirements → data model mapping          │
│   • Self-service training for business users            │
│   • Data quality rules (domain knowledge)               │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## Risk Register

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| K8s complexity → timeline slip | High | High | Start simple (1 namespace), expand later |
| POS vendor không hỗ trợ high-frequency export | Medium | High | Fallback to daily batch, negotiate API later |
| Flash sale traffic overwhelms Flink | Medium | High | Pre-scale 2h trước, KEDA + Flink autoscaler |
| Team burnout (5 people, ambitious scope) | Medium | Medium | Strict MVP scope, defer nice-to-have |
| Hardware failure (no cloud failover) | Low | Critical | RAID on storage, K8s pod rescheduling, MinIO erasure coding |
| Data quality issues block go-live | High | Medium | Quality gates per layer, don't block on perfection |
