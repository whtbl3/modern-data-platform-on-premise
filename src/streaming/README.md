# src/streaming/

Flink streaming jobs: Kafka → process → ClickHouse (real-time path).

## Cấu trúc

```
streaming/
├── orders_stream.py         # Flink job: order_events → revenue_realtime + orders_raw
├── clickstream_stream.py    # Flink job: clickstream → sessions_realtime + flash_sale_live
├── clickhouse_init.sql      # DDL cho 5 ClickHouse tables
├── flink-deployment.yaml    # 2 FlinkDeployment CRDs (K8s Operator)
└── Dockerfile               # Container image cho Flink jobs
```

## Files

| File | Vai trò |
|------|---------|
| `orders_stream.py` | Consume `order_events` topic, filter bằng shared_logic, ghi raw orders + 1-min aggregated revenue vào ClickHouse |
| `clickstream_stream.py` | Consume `clickstream` topic, sessionize (30-min gap), detect flash sale traffic, ghi sessions + live metrics |
| `clickhouse_init.sql` | DDL: `revenue_realtime`, `orders_raw`, `sessions_realtime`, `flash_sale_live`, `payment_gateway_stats`, `inventory_alerts_live` |
| `flink-deployment.yaml` | 2 FlinkDeployment CRDs: orders (parallelism 4) + clickstream (parallelism 6, autoscaler target 70%) |
| `Dockerfile` | Build image: Flink 1.18 + uv + shared_logic + cả 2 job files |

## Architecture

```
Kafka Topics              Flink Jobs                    ClickHouse Tables
─────────────           ──────────────                ───────────────────
order_events  ────→  orders_stream.py  ────→  revenue_realtime (SummingMergeTree)
                                        └──→  orders_raw (MergeTree, for reconciliation)

clickstream   ────→  clickstream_stream.py ─→  sessions_realtime (ReplacingMergeTree)
                                          └──→  flash_sale_live (SummingMergeTree)
```

## Shared logic

Cả 2 jobs đều import `src.shared_logic.sql_templates.order_filter_sql()` để đảm bảo filter logic giống với dbt staging models.

## Auto-scaling

- Flink native autoscaler: `kubernetes.operator.job.autoscaler.enabled: true`
- Target utilization: 70% cho clickstream (flash sale burst 600 events/sec)
- KEDA ScaledObject cho Kafka consumer lag (see `infra/keda/`)
