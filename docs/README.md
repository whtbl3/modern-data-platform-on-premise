# docs/

Tài liệu dự án VietMart Lakehouse theo methodology Discovery → Design → Build → Operate.

## Cấu trúc

```
docs/
├── phase1/          # Discovery — Tìm hiểu bài toán
├── phase2/          # Design — Thiết kế giải pháp
└── runbooks/        # Operate — Hướng dẫn xử lý sự cố
```

## Phase 1 — Discovery

| File | Mô tả |
|------|--------|
| `00_business_context.md` | Bối cảnh VietMart Group: 120 stores, $200M revenue, why on-prem |
| `01_stakeholder_interviews.md` | Phỏng vấn 7 stakeholders (CEO, CFO, CMO, COO, CTO, Head E-com, Regional Manager) |
| `02_requirements.md` | 12 Functional Requirements + 13 Non-Functional Requirements + MVP scope |
| `03_data_audit.md` | 10 nguồn dữ liệu, volume analysis (5.8GB/day), data quality issues |
| `04_constraints.md` | Hardware inventory (20 servers), team (5 người), budget ($0 license), risks |

## Phase 2 — Design

| File | Mô tả |
|------|--------|
| `01_5v_analysis.md` | Phân tích 5V (Volume/Velocity/Variety/Veracity/Value) → chọn technology |
| `02_architecture_design.md` | Target architecture, component mapping, trade-off decision log |
| `03_data_modeling.md` | ER diagram, 4-layer model, identity resolution, streaming models |
| `04_implementation_plan.md` | 8 sprints (16 weeks), tasks per sprint, exit criteria |

## Runbooks

| File | Mô tả |
|------|--------|
| `on-call-quickref.md` | Quick reference cho on-call: URLs, health check, decision tree, SLAs |
| `dagster-run-failed.md` | Xử lý khi pipeline Dagster fail |
| `dbt-test-failure.md` | Xử lý khi dbt tests phát hiện data quality issue |
| `kafka-consumer-lag.md` | Xử lý Kafka consumer lag (streaming bị chậm) |
| `flink-job-down.md` | Xử lý khi Flink streaming job ngừng chạy |
| `flink-checkpoint-failure.md` | Xử lý khi Flink checkpoint fail liên tục |
| `minio-disk-full.md` | Xử lý khi MinIO hết dung lượng |
| `reconciliation-drift.md` | Xử lý khi batch vs streaming revenue chênh lệch >1% |
| `spark-oom.md` | Xử lý khi Spark executor bị OOM |
| `no-data-ingested.md` | Xử lý khi không có dữ liệu mới trong 2+ giờ |
