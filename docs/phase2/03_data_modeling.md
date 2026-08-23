# Phase 2.3: Data Modeling

## Modeling Approach

Dựa trên requirements & stakeholder needs:

```
Business question                        Model decision
──────────────────                      ────────────────

"Doanh thu hôm qua theo cửa hàng"  →   fct_revenue_daily (pre-aggregated)
"Khách hàng nào sắp churn?"        →   dim_customers (RFM scoring)
"Reconcile POS vs Payment"          →   fct_reconciliation (3-way compare)
"Flash sale đang bán bao nhiêu"     →   ClickHouse: revenue_realtime (streaming)
"Inventory nào sắp hết?"           →   fct_inventory_status (daily snapshot)
"Campaign nào hiệu quả?"           →   fct_campaign_attribution (funnel)
"Unified customer: online + offline" →  dim_customers_unified (identity resolution)
```

---

## Entity Relationship (Curated Layer)

```
                        ┌───────────────────────┐
                        │ dim_customers_unified │
                        │───────────────────────│
                        │ customer_uid (PK)     │
                        │ pos_customer_id (FK)  │
                        │ ecom_customer_id (FK) │
                        │ loyalty_member_id(FK) │
                        │ name                  │
                        │ phone_normalized      │
                        │ email_normalized      │
                        │ segment               │
                        │ loyalty_tier          │
                        │ region                │
                        │ first_seen_date       │
                        │ is_omnichannel        │
                        └───────────┬───────────┘
                                    │
            ┌───────────────────────┼──────────────────────┐
            │                       │                      │
┌───────────▼──────────┐ ┌──────────▼─────────┐ ┌──────────▼──────────┐
│ fct_pos_transactions │ │ fct_ecom_orders    │ │ fct_payments        │
│──────────────────────│ │────────────────────│ │─────────────────────│
│ txn_id (PK)          │ │ order_id (PK)      │ │ payment_id (PK)     │
│ store_id (FK)        │ │ customer_uid (FK)  │ │ order_ref (FK)      │
│ customer_uid (FK)    │ │ status             │ │ gateway (vnpay/momo)│
│ items[]              │ │ items[]            │ │ amount_vnd          │
│ total_amount_vnd     │ │ total_amount_vnd   │ │ fee_vnd             │
│ payment_method       │ │ shipping_address   │ │ status              │
│ txn_timestamp        │ │ order_date         │ │ settled_at          │
└───────────┬──────────┘ └─────────┬──────────┘ └─────────────────────┘
            │                      │
            │    ┌─────────────────┘
            │    │
┌───────────▼────▼─────┐          ┌──────────────────────┐
│ dim_products         │          │ dim_stores           │
│──────────────────────│          │──────────────────────│
│ product_id (PK)      │          │ store_id (PK)        │
│ sku                  │          │ store_name           │
│ name                 │          │ region (B/T/N)       │
│ category_l1          │          │ city                 │
│ category_l2          │          │ district             │
│ price_vnd            │          │ format (mall/street) │
│ cost_vnd             │          │ opened_date          │
│ supplier_id          │          │ sqm                  │
│ is_active            │          │ staff_count          │
└──────────────────────┘          └──────────────────────┘
```

---

## Layer-by-Layer Data Model

### Raw Layer (s3://raw/)
Lưu đúng original format, không transform.

| Table/Path | Source | Format | Partitioned by |
|------------|--------|--------|----------------|
| raw/pos/{store_id}/{date}/ | POS CSV export | CSV | store_id + date |
| raw/ecommerce/orders/{date}/ | PostgreSQL CDC | JSON (Debezium) | date |
| raw/ecommerce/clickstream/{date}/{hour}/ | Event SDK | JSON | date + hour |
| raw/payments/{gateway}/{date}/ | SFTP/webhook | CSV/JSON | gateway + date |
| raw/inventory/{date}/ | SAP export | CSV | date |
| raw/loyalty/{date}/ | MySQL CDC | JSON (Debezium) | date |

### Staging Layer (Iceberg tables in s3://staging/)
Clean, deduplicate, normalize, type cast. 1:1 mapping from raw.

| Table | Source | Key transforms |
|-------|--------|----------------|
| stg_pos__transactions | raw/pos/ | Dedup by txn_id+timestamp, normalize date to ISO, validate amounts |
| stg_ecommerce__orders | raw/ecommerce/orders/ | Dedup by order_id, extract from CDC envelope |
| stg_ecommerce__clickstream | raw/ecommerce/clickstream/ | Filter malformed JSON, filter bots, normalize timestamps |
| stg_payments__vnpay | raw/payments/vnpay/ | Normalize amount to VND integer, dedup webhook retries |
| stg_payments__momo | raw/payments/momo/ | Same normalization, different source format |
| stg_payments__card | raw/payments/card/ | Remove fee from amount, convert DD/MM/YYYY |
| stg_inventory__stock_levels | raw/inventory/ | Validate SKU exists, cast quantities |
| stg_loyalty__members | raw/loyalty/ | Normalize phone (+84→0xx), lowercase email |

### Curated Layer (Iceberg tables in s3://curated/)
Business logic, joins, identity resolution.

| Table | Logic | Feeds |
|-------|-------|-------|
| dim_customers_unified | Identity resolution: match by phone OR email across POS/ecom/loyalty | All customer-facing analytics |
| dim_products | Product master enriched with category hierarchy | Revenue, inventory |
| dim_stores | Store master with region, format metadata | Revenue by store |
| fct_pos_transactions | POS txn joined with dim_customers_unified + dim_products | Revenue, customer |
| fct_ecom_orders | E-commerce orders joined with unified customer | Revenue, marketing |
| fct_payments_consolidated | All 3 gateways unioned, normalized, with order reference | Reconciliation |
| fct_inventory_daily | Daily snapshot: stock per SKU per store | Operations |
| fct_clickstream_sessions | Session-stitched clickstream with user mapping | Marketing |

### Analytics Layer (Iceberg tables in s3://analytics/) — Marts

**Finance mart**:
| Table | Grain | Purpose |
|-------|-------|---------|
| mart_revenue_daily | date × store × channel × category | CEO/CFO daily report |
| mart_revenue_monthly | month × region | Monthly P&L |
| mart_reconciliation | date × source (pos/ecom/payment) | CFO: 3-way reconcile |

**Marketing mart**:
| Table | Grain | Purpose |
|-------|-------|---------|
| mart_customer_rfm | customer_uid | RFM segmentation (updated daily) |
| mart_customer_ltv | customer_uid | Lifetime value + churn risk |
| mart_campaign_attribution | campaign × channel | CMO: campaign ROI |
| mart_funnel_conversion | date × referrer × device | Conversion funnel |

**Operations mart**:
| Table | Grain | Purpose |
|-------|-------|---------|
| mart_store_performance | date × store | Regional manager: daily scorecard |
| mart_inventory_alerts | date × store × sku | COO: stockout prediction |
| mart_delivery_sla | date × partner | COO: delivery partner comparison |

---

## Streaming Models (ClickHouse)

| Table | Source | Window | Purpose |
|-------|--------|--------|---------|
| revenue_realtime | Flink (order events) | Tumbling 1 min | Flash sale live revenue |
| sessions_realtime | Flink (clickstream) | Session window 30 min | Live user sessions |
| flash_sale_live | Flink (filtered orders) | Tumbling 10 sec | Flash sale dashboard |
| inventory_alerts_rt | Flink (stock events) | Sliding 5 min | Near-real-time stockout |

---

## Identity Resolution Strategy (dim_customers_unified)

```
┌─────────┐     ┌───────────┐     ┌──────────┐
│ POS     │     │ E-commerce│     │ Loyalty  │
│ customer│     │ customer  │     │ member   │
└────┬────┘     └─────┬─────┘     └────┬─────┘
     │                │                │
     │    normalize phone, email       │
     │                │                │
     └────────────────┼────────────────┘
                      │
              ┌───────▼────────┐
              │ Match rules:   │
              │ 1. phone exact │
              │ 2. email exact │
              │ 3. phone+name  │
              │    fuzzy (>90%)│
              └───────┬────────┘
                      │
              ┌───────▼────────┐
              │ customer_uid   │
              │ (generated)    │
              │                │
              │ is_omnichannel:│
              │ TRUE if matched│
              │ across 2+ src  │
              └────────────────┘

Expected match rate: 70-80% (phone), +10% (email), +5% (fuzzy)
```
