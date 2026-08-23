# src/shared_logic/

Business rules dùng chung giữa batch (dbt) và streaming (Flink).

**Mục đích:** Đảm bảo logic xử lý giống nhau giữa 2 paths, tránh drift.

## Cấu trúc

```
shared_logic/
├── __init__.py
├── rules.py           # Business constants và validation rules
└── sql_templates.py   # SQL fragment generators từ rules
```

## Files

| File | Vai trò |
|------|---------|
| `rules.py` | Định nghĩa: ORDER_VALIDATIONS, COMPLETED_STATUSES, REVENUE_DAILY aggregation, INVENTORY_ALERT_RULES, RFM_SEGMENTS, PHONE_NORMALIZE_RULES |
| `sql_templates.py` | Sinh SQL fragments: `order_filter_sql()`, `is_completed_sql()`, `inventory_alert_case_sql()`, `phone_normalize_sql()`, `reconciliation_alert_sql()` |

## Pattern: Single Source of Truth

```
rules.py (Python constants)
    │
    ├──→ sql_templates.py ──→ Flink streaming jobs (orders_stream.py)
    │
    └──→ macros/shared_rules.sql ──→ dbt models (staging, marts)
```

- `rules.py` là source of truth
- `sql_templates.py` sinh SQL cho Flink
- `macros/shared_rules.sql` (trong dbt) mirror cùng logic cho batch
- Tests (`test_shared_logic.py`) verify consistency

## Ví dụ

```python
from src.shared_logic.sql_templates import order_filter_sql
print(order_filter_sql())
# → "order_id IS NOT NULL AND customer_id IS NOT NULL AND amount > 0"
```

Logic này xuất hiện ở cả:
- dbt: `{{ order_filter() }}` macro
- Flink: `WHERE {order_filter_sql()}` trong streaming job
