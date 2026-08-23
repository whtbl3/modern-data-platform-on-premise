-- VietMart real-time analytics tables (ClickHouse)
-- Fed by Flink streaming jobs from Kafka topics

-- =============================================================================
-- REAL-TIME REVENUE (orders from e-commerce + POS via Kafka)
-- =============================================================================

CREATE TABLE IF NOT EXISTS default.revenue_realtime
(
    window_start DateTime,
    window_end DateTime,
    store_id String,
    channel LowCardinality(String),  -- 'pos' | 'ecommerce'
    order_count UInt64,
    gross_revenue Decimal(18, 2),
    net_revenue Decimal(18, 2),
    avg_order_value Decimal(10, 2)
)
ENGINE = SummingMergeTree()
ORDER BY (window_start, store_id, channel)
TTL window_start + INTERVAL 90 DAY;


CREATE TABLE IF NOT EXISTS default.orders_raw
(
    order_id String,
    customer_id Nullable(String),
    store_id String,
    channel LowCardinality(String),
    amount Decimal(18, 2),
    discount Decimal(10, 2) DEFAULT 0,
    payment_method LowCardinality(String),
    status LowCardinality(String),
    event_time DateTime
)
ENGINE = MergeTree()
ORDER BY (event_time, store_id, order_id)
TTL event_time + INTERVAL 30 DAY;


-- =============================================================================
-- CLICKSTREAM SESSIONS (aggregated from 5M events/day)
-- =============================================================================

CREATE TABLE IF NOT EXISTS default.sessions_realtime
(
    session_id String,
    user_id Nullable(String),
    session_start DateTime,
    session_end DateTime,
    page_views UInt32,
    clicks UInt32,
    add_to_carts UInt32,
    purchases UInt32,
    device_type LowCardinality(String),
    utm_source Nullable(String),
    utm_campaign Nullable(String),
    city LowCardinality(String)
)
ENGINE = ReplacingMergeTree(session_end)
ORDER BY (session_start, session_id)
TTL session_start + INTERVAL 30 DAY;


-- =============================================================================
-- FLASH SALE LIVE DASHBOARD (1-minute tumbling windows)
-- =============================================================================

CREATE TABLE IF NOT EXISTS default.flash_sale_live
(
    window_start DateTime,
    window_end DateTime,
    event_type LowCardinality(String),
    event_count UInt64,
    unique_sessions UInt64,
    unique_users UInt64,
    revenue Decimal(18, 2)
)
ENGINE = SummingMergeTree()
ORDER BY (window_start, event_type)
TTL window_start + INTERVAL 7 DAY;


-- =============================================================================
-- PAYMENT GATEWAY MONITORING (near real-time success rates)
-- =============================================================================

CREATE TABLE IF NOT EXISTS default.payment_gateway_stats
(
    window_start DateTime,
    gateway LowCardinality(String),  -- 'vnpay' | 'momo' | 'card'
    total_attempts UInt64,
    successful UInt64,
    failed UInt64,
    total_amount Decimal(18, 2),
    avg_latency_ms UInt32
)
ENGINE = SummingMergeTree()
ORDER BY (window_start, gateway)
TTL window_start + INTERVAL 30 DAY;


-- =============================================================================
-- INVENTORY ALERTS (low stock detection from streaming SAP events)
-- =============================================================================

CREATE TABLE IF NOT EXISTS default.inventory_alerts_live
(
    detected_at DateTime,
    store_id String,
    sku String,
    product_id String,
    qty_available Int32,
    safety_stock Int32,
    alert_type LowCardinality(String)  -- 'OUT_OF_STOCK' | 'LOW_STOCK' | 'REORDER'
)
ENGINE = MergeTree()
ORDER BY (detected_at, store_id, sku)
TTL detected_at + INTERVAL 7 DAY;
