# Phase 2.1: 5V Analysis → Technology Selection

## Volume — Bao nhiêu data?

| Source | Daily | Monthly | Yearly (compressed) |
|--------|-------|---------|---------------------|
| POS Transactions | 400 MB | 12 GB | 50 GB |
| E-commerce Orders | 100 MB | 3 GB | 12 GB |
| Clickstream Events | 4 GB | 120 GB | 500 GB |
| Payment Gateways | 20 MB | 600 MB | 2.5 GB |
| Inventory Snapshots | 1.2 GB | 36 GB | 150 GB |
| Delivery Tracking | 20 MB | 600 MB | 2.5 GB |
| **TOTAL RAW** | **~5.8 GB** | **~175 GB** | **~720 GB** |

**After compression (Iceberg/Parquet, ~5x)**: ~150 GB/year stored

**3 năm retention**: ~500 GB hot data
**128 TB available**: hơn đủ cho 10+ năm

**→ Decision**: Volume moderate. Spark cần cho POS (800K rows/batch) + clickstream joins.
DuckDB viable cho ad-hoc trên aggregated data.

---

## Velocity — Tốc độ data đến?

| Source | Frequency | Latency requirement |
|--------|-----------|---------------------|
| POS (batch) | Every 15 min | T+1 trước 6 AM (batch) |
| E-commerce (CDC) | Real-time | < 60s cho flash sale |
| Clickstream | 60 events/sec (peak 600/sec) | < 60s cho real-time dashboard |
| Payment | Hourly/daily file drop | T+1 (reconciliation) |
| Inventory | Every 30 min | Near real-time (alert stockout) |

**→ Decision**:
- **Batch path** (POS, payment, inventory): Spark + Dagster, chạy mỗi giờ hoặc daily
- **Streaming path** (clickstream, e-commerce events, flash sale): Kafka + Flink
- Flash sale = 600 events/sec × 4h = ~8.6M events. Flink handles easily.
- **KHÔNG cần streaming cho TẤT CẢ** — chỉ clickstream + order events khi flash sale

---

## Variety — Bao nhiêu loại data, format khác nhau?

| Format | Sources | Challenge |
|--------|---------|-----------|
| CSV (various encodings, date formats) | POS, Payment, Inventory, HR | Schema drift, delimiter issues |
| JSON (nested, semi-structured) | Clickstream, Delivery API, Momo webhook | Nested fields, schema evolution |
| PostgreSQL tables (structured) | E-commerce, Loyalty | Clean but need CDC setup |
| SAP IDoc (proprietary) | Inventory | Need connector/export middleware |

**→ Decision**:
- Ingest raw **as-is** vào MinIO (preserve original)
- **Spark handles variety**: CSV reader (schema inference), JSON reader (nested), JDBC reader
- Iceberg cho **unified format** từ staging trở đi
- Schema Registry (Kafka) cho streaming events — enforce schema ở ingestion

---

## Veracity — Data có đáng tin không?

| Issue | Source | Impact | Solution |
|-------|--------|--------|----------|
| 1.5% duplicates | POS (network retry) | Revenue inflate $3M/year (1.5% × $200M) | Dedup by txn_id + timestamp |
| 3% malformed JSON | Clickstream (old SDK) | Events dropped, analytics incomplete | Dead letter queue, fix SDK, backfill |
| Phone format inconsistent | Loyalty, E-commerce | Cannot unify customers (miss 20% matches) | Normalize: strip spaces, +84 → 0xx |
| Amount format differs | Payment gateways | Reconciliation fails | Standardize to VND integer at staging |
| Date format chaos | POS (per store) | Parse errors, wrong aggregation | Force ISO 8601 at ingestion |
| Bot traffic 15% | Clickstream | Inflate page views, conversion drop | Filter by pattern + rate limit |
| Settlement timing | Card payments | T+1 mismatch with POS | Join on merchant_ref, allow T+1 window |

**→ Decision**:
- **Layer strategy**: raw (as-is) → staging (clean, dedup, normalize) → curated (business logic) → analytics (aggregated)
- **Quality gates**: Soda checks BETWEEN each layer. Block promotion if fail.
- **Reconciliation job**: daily compare POS revenue vs payment sum vs e-commerce sum
- **Dead letter queue**: malformed events → Kafka DLQ → alert → manual review

---

## Value — Business value từ data?

| Use case | Stakeholder | Current state | Target state | Business value |
|----------|-------------|---------------|--------------|----------------|
| Daily revenue report | CEO, CFO | 3-5 days, 5% error | T+1 6AM, < 0.1% error | Faster decisions, trust in numbers |
| Customer segmentation | CMO | 6-month-old Excel | Daily refresh RFM | Better targeting → +15% campaign ROI |
| Flash sale real-time | E-commerce | Blind during sale | 60s latency dashboard | Optimize in real-time → +20% conversion |
| Revenue reconciliation | Finance | 2 people × 5 days/month | Automated, 2h alert | Save 80 man-hours/month, catch fraud |
| Inventory optimization | Operations | React to stockout | Predict stockout 3 days ahead | Reduce stockout days 3 → 0.5 |
| Self-service analytics | All | Engineer bottleneck | Business self-query | Free 70% engineer time for platform |

**→ Decision**: ROI clear. Highest value = revenue accuracy + self-service (unlocks ALL other use cases).

---

## Summary: 5V → Stack Mapping

```
┌──────────────┬─────────────────────────────────────────────────────────┐
│ 5V Finding   │ Technology Decision                                      │
├──────────────┼─────────────────────────────────────────────────────────┤
│ VOLUME       │ MinIO (128TB, erasure coding) + Iceberg (compression)   │
│ ~6 GB/day    │ Spark for batch, DuckDB for lightweight                 │
│              │ 12 worker nodes sufficient for 2+ years                  │
├──────────────┼─────────────────────────────────────────────────────────┤
│ VELOCITY     │ Batch: Spark + Dagster (hourly/daily schedules)         │
│ mixed        │ Stream: Kafka + Flink (clickstream, flash sale only)    │
│              │ NOT everything streaming — only where latency matters   │
├──────────────┼─────────────────────────────────────────────────────────┤
│ VARIETY      │ Raw layer preserves original format                      │
│ CSV+JSON+DB  │ Spark handles all (csv/json/jdbc readers)               │
│              │ Iceberg unifies from staging onward                      │
│              │ Schema Registry for Kafka events                         │
├──────────────┼─────────────────────────────────────────────────────────┤
│ VERACITY     │ 4-layer architecture (raw→staging→curated→analytics)    │
│ multiple     │ Soda quality gates between layers                       │
│ issues       │ Reconciliation job (daily)                              │
│              │ Dead letter queue for bad events                         │
├──────────────┼─────────────────────────────────────────────────────────┤
│ VALUE        │ Trino (self-service SQL, ad-hoc)                        │
│ self-service │ Superset (dashboards for all stakeholders)              │
│ + real-time  │ ClickHouse (real-time OLAP for flash sale)              │
│              │ OpenMetadata (discovery, governance)                     │
└──────────────┴─────────────────────────────────────────────────────────┘
```
