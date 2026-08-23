# src/

Source code chính của VietMart Lakehouse platform.

## Cấu trúc

```
src/
├── batch/           # Spark batch jobs (raw ingestion, staging transform)
├── datagen/         # Data generators giả lập 6 nguồn dữ liệu VietMart
├── ingestion/       # Kafka producer examples
├── quality/         # Data quality checks (Soda) + batch/stream reconciliation
├── shared_logic/    # Business rules dùng chung giữa batch và streaming
├── streaming/       # Flink streaming jobs + ClickHouse DDL
└── transforms/      # dbt project (Kimball star schema models)
```

## Luồng dữ liệu

```
Sources → datagen (simulate) → MinIO/Kafka
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
              batch/jobs      streaming/        (real-time)
              (Spark)         (Flink)
                    │               │
                    ▼               ▼
              transforms/     ClickHouse
              (dbt models)
                    │
                    ▼
              quality/
              (reconciliation)
```
