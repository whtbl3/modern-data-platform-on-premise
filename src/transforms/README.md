# src/transforms/

dbt project — Kimball star schema modeling cho VietMart Lakehouse.

## Cấu trúc

```
transforms/
├── dbt_project.yml          # dbt config: materialization per layer
├── profiles.yml             # Trino connection (dev/prod targets)
├── packages.yml             # dbt_utils dependency
├── macros/
│   ├── shared_rules.sql     # Business rules mirroring shared_logic/rules.py
│   └── dedup.sql            # Reusable dedup macro
├── models/
│   ├── staging/             # Layer 1: Clean, dedup, normalize (views)
│   ├── intermediate/        # Layer 2: Join, union, resolve identity (tables)
│   └── marts/               # Layer 3: Fact + Dimension tables (Kimball)
│       ├── dimensions/      # dim_customers, dim_stores, dim_products, dim_date
│       ├── finance/         # fct_revenue_daily, fct_revenue_monthly, fct_reconciliation
│       ├── marketing/       # fct_campaign_performance, fct_funnel_daily
│       └── operations/      # fct_store_performance, fct_inventory_alerts
├── seeds/
│   ├── seed_stores.csv      # 120 stores reference data
│   └── seed_products.csv    # Product catalog sample
└── tests/                   # Custom dbt tests
```

## Model Layers

### Staging (`models/staging/`)
- Materialized as **views** (lightweight, no storage cost)
- 6 domains: pos, ecommerce, payments, inventory, loyalty, clickstream
- Logic: dedup by primary key, type cast, phone normalization, null filter

| Domain | Models |
|--------|--------|
| pos | `stg_pos__transactions` |
| ecommerce | `stg_ecommerce__orders`, `stg_ecommerce__customers` |
| payments | `stg_payments__vnpay`, `stg_payments__momo`, `stg_payments__card`, `stg_payments__consolidated` |
| inventory | `stg_inventory__stock_levels` |
| loyalty | `stg_loyalty__members` |
| clickstream | `stg_clickstream__events` |

### Intermediate (`models/intermediate/`)
- Materialized as **tables**
- Cross-domain logic: identity resolution, channel union, metrics aggregation

| Model | Vai trò |
|-------|---------|
| `int_customers_unified` | Merge customers từ POS/e-com/loyalty bằng phone/email matching |
| `int_orders_all_channels` | Union POS + e-commerce orders với unified customer_uid |
| `int_customer_metrics` | Lifetime metrics: total_orders, total_spend, recency (cho RFM) |
| `int_sessions` | Session aggregation từ clickstream events |

### Marts (`models/marts/`)
- Materialized as **tables** (Kimball star schema)
- Consumed by Superset dashboards và ad-hoc Trino queries

## Macros

| Macro | Vai trò |
|-------|---------|
| `order_filter()` | WHERE clause cho valid orders (mirrors shared_logic) |
| `is_completed()` | Status filter cho completed orders |
| `inventory_alert()` | CASE expression cho OUT_OF_STOCK/LOW_STOCK/REORDER |
| `phone_normalize()` | Chuẩn hóa phone VN về format 0xxxxxxxxx |
| `reconciliation_alert()` | CASE cho reconciliation alert levels |
| `dedup()` | Generic dedup bằng ROW_NUMBER() OVER() |

## Chạy

```bash
# Dev
make dbt-run
make dbt-test

# Specific model
cd src/transforms && uv run dbt run --select marts.finance
cd src/transforms && uv run dbt test --select marts.finance

# Generate docs
make dbt-docs
```
