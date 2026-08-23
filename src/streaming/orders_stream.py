"""
Flink streaming job: Kafka order_events → ClickHouse revenue_realtime

Uses shared business rules from src.shared_logic to ensure
batch (dbt) and streaming (Flink) logic stays in sync.
"""
import os
import sys

from pyflink.datastream import StreamExecutionEnvironment
from pyflink.table import EnvironmentSettings, StreamTableEnvironment

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))
from src.shared_logic.sql_templates import order_filter_sql


def create_orders_streaming_job():
    env = StreamExecutionEnvironment.get_execution_environment()
    env.enable_checkpointing(60000)

    settings = EnvironmentSettings.in_streaming_mode()
    t_env = StreamTableEnvironment.create(env, environment_settings=settings)

    kafka_brokers = os.getenv("KAFKA_BROKERS", "kafka:9092")
    clickhouse_url = os.getenv("CLICKHOUSE_URL", "clickhouse:8123")

    # Source: e-commerce + POS order events from Kafka
    t_env.execute_sql(f"""
        CREATE TABLE kafka_order_events (
            order_id STRING,
            customer_id STRING,
            store_id STRING,
            channel STRING,
            amount DECIMAL(18, 2),
            discount DECIMAL(10, 2),
            payment_method STRING,
            status STRING,
            event_time TIMESTAMP(3),
            WATERMARK FOR event_time AS event_time - INTERVAL '5' SECOND
        ) WITH (
            'connector' = 'kafka',
            'topic' = 'order_events',
            'properties.bootstrap.servers' = '{kafka_brokers}',
            'properties.group.id' = 'flink-orders-consumer',
            'scan.startup.mode' = 'latest-offset',
            'format' = 'json'
        )
    """)

    # Sink: ClickHouse revenue_realtime
    t_env.execute_sql(f"""
        CREATE TABLE clickhouse_revenue_realtime (
            window_start TIMESTAMP(3),
            window_end TIMESTAMP(3),
            store_id STRING,
            channel STRING,
            order_count BIGINT,
            gross_revenue DECIMAL(18, 2),
            net_revenue DECIMAL(18, 2),
            avg_order_value DECIMAL(10, 2)
        ) WITH (
            'connector' = 'jdbc',
            'url' = 'jdbc:clickhouse://{clickhouse_url}/default',
            'table-name' = 'revenue_realtime',
            'driver' = 'com.clickhouse.jdbc.ClickHouseDriver'
        )
    """)

    # Sink: ClickHouse orders_raw (for reconciliation with batch)
    t_env.execute_sql(f"""
        CREATE TABLE clickhouse_orders_raw (
            order_id STRING,
            customer_id STRING,
            store_id STRING,
            channel STRING,
            amount DECIMAL(18, 2),
            discount DECIMAL(10, 2),
            payment_method STRING,
            status STRING,
            event_time TIMESTAMP(3)
        ) WITH (
            'connector' = 'jdbc',
            'url' = 'jdbc:clickhouse://{clickhouse_url}/default',
            'table-name' = 'orders_raw',
            'driver' = 'com.clickhouse.jdbc.ClickHouseDriver'
        )
    """)

    # Shared filter — same logic as dbt stg_pos__transactions / stg_ecommerce__orders
    filter_clause = order_filter_sql()

    t_env.execute_sql(f"""
        CREATE VIEW valid_orders AS
        SELECT * FROM kafka_order_events
        WHERE {filter_clause}
    """)

    # Write raw orders for reconciliation
    t_env.execute_sql("""
        INSERT INTO clickhouse_orders_raw
        SELECT order_id, customer_id, store_id, channel,
               amount, discount, payment_method, status, event_time
        FROM valid_orders
    """)

    # 1-minute tumbling window aggregation → revenue_realtime
    t_env.execute_sql("""
        INSERT INTO clickhouse_revenue_realtime
        SELECT
            window_start,
            window_end,
            store_id,
            channel,
            COUNT(*) AS order_count,
            SUM(amount) AS gross_revenue,
            SUM(amount - discount) AS net_revenue,
            AVG(amount) AS avg_order_value
        FROM TABLE(
            TUMBLE(TABLE valid_orders, DESCRIPTOR(event_time), INTERVAL '1' MINUTE)
        )
        GROUP BY window_start, window_end, store_id, channel
    """)


if __name__ == "__main__":
    create_orders_streaming_job()
