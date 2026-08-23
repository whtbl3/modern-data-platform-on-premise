# src/datagen/

Data generator giả lập 6 nguồn dữ liệu VietMart theo đúng volume và format từ Data Audit.

## Cấu trúc

```
datagen/
├── __main__.py          # CLI entry point — chạy batch/stream/flash-sale mode
├── pipeline.py          # Orchestrator kết nối generators với sinks
├── generators/          # OOP generators cho từng nguồn dữ liệu
│   ├── base.py          # BaseGenerator — abstract class, helpers (_store_id, _customer_phone, etc.)
│   ├── pos.py           # POS transactions (800K txn/day, 120 stores, CSV format)
│   ├── ecommerce.py     # E-commerce orders + customers (PostgreSQL CDC)
│   ├── payments.py      # 3 payment gateways: VNPay, Momo, Card (different formats)
│   ├── inventory.py     # SAP stock level snapshots (50K SKUs × 120 stores)
│   ├── loyalty.py       # Loyalty members (1.5M, intentionally inconsistent phone formats)
│   └── clickstream.py   # Web/mobile events (5M/day, flash_sale_burst method)
└── sinks/               # Output destinations
    ├── base.py          # BaseSink abstract class (connect/write/close protocol)
    ├── minio_sink.py    # Write JSON/CSV to MinIO (batch path)
    ├── kafka_sink.py    # Produce to Kafka topics (streaming path)
    └── postgres_sink.py # Write to PostgreSQL (for CDC simulation)
```

## Sử dụng

```bash
# Batch: tạo 1 ngày dữ liệu đầy đủ → MinIO
make datagen-batch

# Stream: continuous clickstream + orders → Kafka
make datagen-stream

# Flash sale: burst 600 events/sec × 60s
make datagen-flash-sale

# Chỉ 1 source
uv run python -m src.datagen --mode batch --source pos --pos-txns 10000
```

## Design decisions

- Mỗi generator kế thừa `BaseGenerator` → deterministic (seed), generate_one/generate_batch
- `GeneratorConfig` chứa: seed, num_stores (120), num_customers (50K), num_products (5K)
- Phone formats intentionally inconsistent (loyalty) để test identity resolution
- Payment gateways có format khác nhau (VNPay: vnp_*, Momo: trans_id, Card: transaction_id)
