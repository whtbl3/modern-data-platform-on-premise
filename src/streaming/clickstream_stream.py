"""
Flink streaming job: Kafka clickstream → ClickHouse sessions_realtime + flash_sale_live

Sessionizes clickstream events (5M/day, peak 600/sec during flash sale)
and feeds real-time dashboards in Superset.
"""
import os
import sys

from pyflink.datastream import StreamExecutionEnvironment
from pyflink.table import EnvironmentSettings, StreamTableEnvironment

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))


def create_clickstream_streaming_job():
    env = StreamExecutionEnvironment.get_execution_environment()
    env.enable_checkpointing(30000)

    settings = EnvironmentSettings.in_streaming_mode()
    t_env = StreamTableEnvironment.create(env, environment_settings=settings)

    kafka_brokers = os.getenv("KAFKA_BROKERS", "kafka:9092")
    clickhouse_url = os.getenv("CLICKHOUSE_URL", "clickhouse:8123")

    # Source: clickstream events from Kafka
    t_env.execute_sql(f"""
        CREATE TABLE kafka_clickstream (
            event_id STRING,
            session_id STRING,
            user_id STRING,
            event_type STRING,
            page_url STRING,
            utm_source STRING,
            utm_campaign STRING,
            device_type STRING,
            city STRING,
            duration_ms INT,
            event_time TIMESTAMP(3),
            WATERMARK FOR event_time AS event_time - INTERVAL '10' SECOND
        ) WITH (
            'connector' = 'kafka',
            'topic' = 'clickstream',
            'properties.bootstrap.servers' = '{kafka_brokers}',
            'properties.group.id' = 'flink-clickstream-consumer',
            'scan.startup.mode' = 'latest-offset',
            'format' = 'json'
        )
    """)

    # Sink: session aggregates
    t_env.execute_sql(f"""
        CREATE TABLE clickhouse_sessions (
            session_id STRING,
            user_id STRING,
            session_start TIMESTAMP(3),
            session_end TIMESTAMP(3),
            page_views INT,
            clicks INT,
            add_to_carts INT,
            purchases INT,
            device_type STRING,
            utm_source STRING,
            utm_campaign STRING,
            city STRING
        ) WITH (
            'connector' = 'jdbc',
            'url' = 'jdbc:clickhouse://{clickhouse_url}/default',
            'table-name' = 'sessions_realtime',
            'driver' = 'com.clickhouse.jdbc.ClickHouseDriver'
        )
    """)

    # Sink: flash sale live metrics (1-minute windows)
    t_env.execute_sql(f"""
        CREATE TABLE clickhouse_flash_sale (
            window_start TIMESTAMP(3),
            window_end TIMESTAMP(3),
            event_type STRING,
            event_count BIGINT,
            unique_sessions BIGINT,
            unique_users BIGINT,
            revenue DECIMAL(18, 2)
        ) WITH (
            'connector' = 'jdbc',
            'url' = 'jdbc:clickhouse://{clickhouse_url}/default',
            'table-name' = 'flash_sale_live',
            'driver' = 'com.clickhouse.jdbc.ClickHouseDriver'
        )
    """)

    # Session aggregation using session window (30-min gap)
    t_env.execute_sql("""
        INSERT INTO clickhouse_sessions
        SELECT
            session_id,
            LAST_VALUE(user_id) AS user_id,
            MIN(event_time) AS session_start,
            MAX(event_time) AS session_end,
            CAST(SUM(CASE WHEN event_type = 'page_view' THEN 1 ELSE 0 END) AS INT) AS page_views,
            CAST(SUM(CASE WHEN event_type = 'click' THEN 1 ELSE 0 END) AS INT) AS clicks,
            CAST(SUM(CASE WHEN event_type = 'add_to_cart' THEN 1 ELSE 0 END) AS INT) AS add_to_carts,
            CAST(SUM(CASE WHEN event_type = 'purchase' THEN 1 ELSE 0 END) AS INT) AS purchases,
            LAST_VALUE(device_type) AS device_type,
            LAST_VALUE(utm_source) AS utm_source,
            LAST_VALUE(utm_campaign) AS utm_campaign,
            LAST_VALUE(city) AS city
        FROM TABLE(
            SESSION(TABLE kafka_clickstream PARTITION BY session_id, DESCRIPTOR(event_time), INTERVAL '30' MINUTE)
        )
        GROUP BY session_id, window_start, window_end
    """)

    # Flash sale live: filter on /flash-sale page, 1-min tumbling windows
    t_env.execute_sql("""
        INSERT INTO clickhouse_flash_sale
        SELECT
            window_start,
            window_end,
            event_type,
            COUNT(*) AS event_count,
            COUNT(DISTINCT session_id) AS unique_sessions,
            COUNT(DISTINCT user_id) AS unique_users,
            CAST(0 AS DECIMAL(18, 2)) AS revenue
        FROM TABLE(
            TUMBLE(TABLE kafka_clickstream, DESCRIPTOR(event_time), INTERVAL '1' MINUTE)
        )
        WHERE page_url LIKE '%flash-sale%'
        GROUP BY window_start, window_end, event_type
    """)


if __name__ == "__main__":
    create_clickstream_streaming_job()
