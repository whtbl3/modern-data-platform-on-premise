# Phase 2 — Design (Kimball Applied)

## Áp dụng Kimball 4-Step cho VietMart

### Step 1: Chọn Business Process

Hỏi: "Công ty đo lường cái gì?" → đó là process.

| Business Process | Ai quan tâm | Tại sao ưu tiên |
|-----------------|-------------|-----------------|
| **Bán hàng** (POS + e-com) | CEO, CFO, Regional | Revenue = #1 metric |
| **Thanh toán** | CFO | Reconciliation pain |
| **Tồn kho** | COO | Stockout = mất doanh thu |
| **Marketing/Clickstream** | CMO, E-com Head | Campaign ROI, flash sale |
| **Khách hàng** | CMO | RFM, churn, unified view |

→ **MVP: Bán hàng + Thanh toán trước** (vì pain lớn nhất = revenue chênh lệch 3-8%)

---

### Step 2: Khai báo Grain

**Quan trọng nhất.** Grain = 1 dòng trong fact table đại diện cho cái gì?

| Fact Table | Grain (1 row = ?) | Tại sao chọn grain này |
|-----------|-------------------|----------------------|
| `fct_revenue_daily` | 1 ngày × 1 store × 1 channel | Đủ chi tiết để drill-down theo store, nhưng không quá nặng |
| `fct_reconciliation` | 1 ngày × 1 store × 1 channel | So sánh 3 nguồn ở cùng grain |
| `fct_store_performance` | 1 ngày × 1 store | Scorecard per store |
| `fct_inventory_alerts` | 1 event (khi stock thấp) | Event-driven, không periodic |
| `fct_funnel_daily` | 1 ngày × 1 funnel step | Conversion tracking |
| `fct_campaign_performance` | 1 ngày × 1 campaign | UTM attribution |

**Nguyên tắc:** Grain càng chi tiết → càng linh hoạt. Nhưng không chi tiết hơn mức cần thiết (POS từng line item thì quá nặng cho dashboard, để ở staging).

---

### Step 3: Xác định Dimensions

Grain đã rõ → dimension tự hiện ra (ai, cái gì, ở đâu, khi nào).

| Dimension | Mô tả | Conformed? |
|-----------|--------|-----------|
| `dim_date` | Calendar spine (ngày, tuần, tháng, quý, năm, is_weekend, is_holiday) | ✅ Dùng chung mọi fact |
| `dim_stores` | 120 stores (name, region, city, size, format) | ✅ Dùng chung revenue + inventory |
| `dim_customers` | Unified customer (RFM segment, tier, city) | ✅ Dùng chung revenue + marketing |
| `dim_products` | SKU catalog (category, brand, margin) | ✅ Dùng chung revenue + inventory |

**Conformed = dimension dùng chung** giữa nhiều fact → không tạo silo.

---

### Step 4: Xác định Facts (Measures)

| Fact Table | Measures | Loại |
|-----------|----------|------|
| `fct_revenue_daily` | gross_revenue, net_revenue, order_count, avg_order_value | **Transaction** (aggregate of transactions) |
| `fct_reconciliation` | pos_amount, ecom_amount, payment_amount, discrepancy_pct | **Periodic Snapshot** (daily compare) |
| `fct_inventory_alerts` | qty_available, safety_stock, alert_type | **Transaction** (event khi stock thấp) |
| `fct_store_performance` | revenue, txn_count, avg_basket, rank | **Periodic Snapshot** (daily scorecard) |

---

---

## Load Strategy: Full / Incremental / Passthrough

### Dimension tables

| Dimension | Strategy | Tại sao |
|-----------|----------|---------|
| `dim_date` | **Full load (1 lần)** | Calendar spine sinh sẵn 2022-2030, không đổi. Chạy seed 1 lần duy nhất |
| `dim_stores` | **Full load (hiếm khi chạy)** | 120 stores thay đổi rất ít (mở store mới ~2-3 lần/năm). Reload khi có store mới |
| `dim_products` | **Incremental (daily)** | Catalog thay đổi: thêm SKU mới, update giá, ngưng bán. Merge on `product_id` |
| `dim_customers` | **Incremental (daily)** | Thêm customer mới + refresh RFM score hàng ngày. Merge on `customer_uid` |

### Fact tables

| Fact | Strategy | Tại sao |
|------|----------|---------|
| `fct_revenue_daily` | **Incremental (append partition)** | Mỗi ngày append 1 partition mới. Không touch data cũ |
| `fct_revenue_monthly` | **Incremental (overwrite current month)** | Cuối ngày tính lại tháng hiện tại (MoM cần cả tháng) |
| `fct_reconciliation` | **Incremental (append)** | Mỗi ngày 1 dòng per store/channel. Append only |
| `fct_store_performance` | **Incremental (append)** | Daily scorecard, append |
| `fct_inventory_alerts` | **Passthrough (event-driven)** | Không aggregate — ghi thẳng khi alert trigger. Không có schedule cố định |
| `fct_funnel_daily` | **Incremental (append)** | Daily funnel metrics, append |
| `fct_campaign_performance` | **Incremental (append)** | Daily per campaign, append |

### Giải thích 3 strategy

```
Full Load        = DROP + reload toàn bộ. Dùng khi data nhỏ, ít đổi
                   VD: dim_date (4 năm = 1,461 rows), dim_stores (120 rows)

Incremental      = Chỉ xử lý data mới/thay đổi. Dùng khi data lớn, thêm liên tục
                   VD: fct_revenue_daily — chỉ tính ngày hôm qua, không chạy lại 3 năm
                   Cách detect: partition date, updated_at > last_run, CDC

Passthrough      = Không transform, ghi thẳng event khi xảy ra. Dùng khi:
                   - Event-driven (không có schedule)
                   - Data đã clean ở upstream
                   - Cần latency thấp (streaming → ClickHouse trực tiếp)
                   VD: inventory_alerts, flash_sale_live
```

### Trong dbt cài đặt như thế nào?

```sql
-- Full load (default dbt behavior)
{{ config(materialized='table') }}

-- Incremental (chỉ process rows mới)
{{ config(
    materialized='incremental',
    unique_key='surrogate_key',
    incremental_strategy='merge'
) }}
-- Thêm filter:
{% if is_incremental() %}
WHERE updated_at > (SELECT max(updated_at) FROM {{ this }})
{% endif %}

-- Passthrough (streaming ghi thẳng vào ClickHouse, dbt không quản lý)
-- Không có dbt model — Flink ghi trực tiếp
```

### Decision tree khi chọn strategy

```
Data thay đổi không?
├── Không (hoặc rất hiếm) → Full Load
│   VD: dim_date, dim_stores
│
└── Có
    ├── Có schedule (daily/hourly)? 
    │   ├── Data lớn (>100K rows/day) → Incremental
    │   │   VD: fct_revenue_daily, dim_customers
    │   └── Data nhỏ (<10K rows) → Full Load cũng được
    │       VD: dim_products (5K SKUs, reload nhanh)
    │
    └── Không schedule (event-driven)?  → Passthrough
        VD: inventory_alerts, flash_sale_live (Flink → ClickHouse)
```

---

## Streaming thì Kimball như thế nào?

Streaming **không thay thế** Kimball — nó **feed vào** cùng model nhưng ở tốc độ khác.

```
                    Batch (dbt)                  Streaming (Flink)
                    ──────────                   ─────────────────
Grain:              1 day × store × channel      1 minute × store × channel
Output:             fct_revenue_daily (Iceberg)  revenue_realtime (ClickHouse)
Schema:             GIỐNG NHAU (cùng columns)    GIỐNG NHAU
Logic filter:       shared_logic/rules.py        shared_logic/rules.py
Khi nào dùng:      Báo cáo chính thức (T+1)     Dashboard real-time (live)
```

**Key insight:** Streaming table là **preview** của batch table. Cùng grain nhỏ hơn (1 phút thay vì 1 ngày), cùng measures, cùng filter logic. Cuối ngày, batch "chốt sổ" và reconciliation kiểm tra 2 bên khớp nhau.

### Ví dụ cụ thể: Flash Sale 11.11 (11h sáng)

**11:00 AM — Flash sale bắt đầu**

Đơn hàng đổ vào Kafka topic `order_events`:
```json
{"order_id": "ECOM-00012345", "store_id": "STR-001", "channel": "ecommerce", "amount": 1500000, "event_time": "2026-11-11T11:00:05"}
{"order_id": "ECOM-00012346", "store_id": "STR-042", "channel": "ecommerce", "amount": 890000, "event_time": "2026-11-11T11:00:07"}
... 600 events/giây ...
```

**11:01 AM — Flink tổng hợp window 1 phút, ghi vào ClickHouse:**
```sql
-- revenue_realtime (ClickHouse) — có data sau 1 phút
SELECT * FROM revenue_realtime WHERE window_start = '2026-11-11 11:00:00';

| window_start        | store_id | channel   | order_count | gross_revenue |
|---------------------|----------|-----------|-------------|---------------|
| 2026-11-11 11:00:00 | STR-001  | ecommerce | 45          | 67,500,000    |
| 2026-11-11 11:00:00 | STR-042  | ecommerce | 38          | 33,820,000    |
| ...                 | ...      | ...       | ...         | ...           |
```

→ CMO mở Superset dashboard, thấy **real-time**: "11:00-11:01 đã bán 2.3 tỷ VNĐ, 1,200 đơn"

**11:02 AM — Vẫn flash sale**

Flink tiếp tục ghi window tiếp theo. Dashboard cập nhật mỗi phút.
CMO thấy: "Revenue đang tăng 40% so với flash sale tháng trước → campaign đang hiệu quả"

**6:00 AM hôm sau — Batch "chốt sổ"**

Dagster chạy pipeline:
```
raw_ecommerce_orders (MinIO)
  → dbt staging: dedup, validate (cùng shared_logic filter)
  → dbt intermediate: join customer, union POS + e-com
  → dbt marts: fct_revenue_daily
```

```sql
-- fct_revenue_daily (Iceberg/Trino) — data chính thức
SELECT * FROM fct_revenue_daily WHERE revenue_date = '2026-11-11';

| revenue_date | store_id | channel   | order_count | gross_revenue  |
|--------------|----------|-----------|-------------|----------------|
| 2026-11-11   | STR-001  | ecommerce | 5,420       | 8,130,000,000  |
| 2026-11-11   | STR-001  | pos       | 3,100       | 4,650,000,000  |
| 2026-11-11   | STR-042  | ecommerce | 4,890       | 4,357,100,000  |
| ...          | ...      | ...       | ...         | ...            |
```

→ CFO mở báo cáo sáng: "11/11 tổng revenue 45.2 tỷ, tăng 180% YoY"

**6:15 AM — Reconciliation kiểm tra**

```sql
-- So sánh: batch (chính thức) vs streaming (real-time hôm qua)
-- Stream: SUM tất cả 1-minute windows trong ngày 11/11
SELECT sum(gross_revenue) FROM revenue_realtime 
WHERE toDate(window_start) = '2026-11-11';
-- → 44.8 tỷ

-- Batch: từ fct_revenue_daily
SELECT sum(gross_revenue) FROM fct_revenue_daily 
WHERE revenue_date = '2026-11-11';
-- → 45.2 tỷ

-- Drift = |45.2 - 44.8| / 45.2 = 0.88% → OK (< 1% threshold)
```

### Tại sao 2 con số hơi khác nhau?

| Nguyên nhân | Giải thích |
|-------------|-----------|
| Late-arriving events | Đơn tạo lúc 23:59, payment confirm lúc 00:02 → streaming miss, batch catch |
| POS offline sync | Store mất mạng 2h, sync CSV lúc 2AM → batch có, stream không có |
| Dedup khác nhau | Streaming dedup by window, batch dedup toàn ngày (chính xác hơn) |

**< 1% drift = bình thường, chấp nhận được.** > 1% = có vấn đề → alert.

### Tóm lại vai trò mỗi bên

```
Streaming (Flink → ClickHouse)          Batch (Dagster → dbt → Iceberg)
─────────────────────────────           ────────────────────────────────
Tốc độ: 1 phút                         Tốc độ: T+1 (6AM hôm sau)
Mục đích: Monitoring, quyết định nhanh  Mục đích: Báo cáo chính thức, audit
Ai dùng: CMO (flash sale), COO (ops)   Ai dùng: CFO (tài chính), CEO (board)
Có thể sai 1-2%: OK                    Phải chính xác: YES
Grain: 1 phút                          Grain: 1 ngày
Retention: 30-90 ngày                   Retention: 3-7 năm
```

**Một câu:** Streaming cho "đang xảy ra gì?", Batch cho "hôm qua/tháng này thực sự là bao nhiêu?"

---

## Mapping vào dbt layers

```
Kimball concept        →  dbt layer         →  Ví dụ VietMart
─────────────────────────────────────────────────────────────
Source systems         →  sources (yml)     →  raw.pos_transactions
Staging (clean/dedup)  →  staging (views)   →  stg_pos__transactions
Integration/conform    →  intermediate      →  int_customers_unified, int_orders_all_channels
Dimension tables       →  marts/dimensions  →  dim_customers, dim_stores
Fact tables            →  marts/facts       →  fct_revenue_daily, fct_reconciliation
```

---

## Sai lầm đã tránh trong project này

| Sai lầm Kimball cảnh báo | Cách VietMart tránh |
|--------------------------|---------------------|
| Chỉ lưu data tổng hợp | Giữ raw + staging ở mức atomic (từng transaction) |
| Không track thay đổi dimension | dim_customers có RFM refresh daily (SCD Type 1 cho segment) |
| Tách hierarchy thành nhiều dim | dim_stores gộp: store → region → city (1 bảng) |
| Thiết kế theo report cụ thể | Design theo business process (bán hàng), không theo "báo cáo CEO muốn" |
| Không conformed dimension | dim_date, dim_stores dùng chung 4 fact tables |
| Nhồi text vào fact | alert_type, channel là FK hoặc low-cardinality enum, không free text |

---

## Tóm lại khi phỏng vấn

Nếu được hỏi "Anh/chị design data model như thế nào?":

> 1. Chọn business process quan trọng nhất (revenue)
> 2. Declare grain rõ ràng (1 row = 1 ngày × 1 store × 1 channel)  
> 3. Dimensions tự hiện (date, store, customer, product)
> 4. Facts = measures mà business cần (revenue, order_count, discrepancy)
> 5. Conform dimensions dùng chung → không tạo silo
> 6. Streaming dùng cùng schema, grain nhỏ hơn, reconcile cuối ngày

Không cần nói 34 ETL subsystems hay SCD Type 6. Focus vào **grain + conform** là đủ thể hiện hiểu Kimball.
