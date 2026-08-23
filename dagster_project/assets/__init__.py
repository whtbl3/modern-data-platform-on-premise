from dagster import DailyPartitionsDefinition, asset

from ..resources import MinIOResource, SparkResource, TrinoResource

DAILY = DailyPartitionsDefinition(start_date="2024-01-01")

RAW_BUCKET = "dev-raw"
WAREHOUSE = "lakehouse"


# =============================================================================
# RAW LAYER — Ingest from MinIO landing zone into raw Iceberg tables
# =============================================================================

@asset(partitions_def=DAILY, group_name="raw")
def raw_pos_transactions(context, spark: SparkResource, minio: MinIOResource):
    """Ingest POS CSV files → raw Iceberg (800K txn/day from 120 stores)."""
    date = context.partition_key
    session = spark.get_session()
    df = session.read.csv(
        f"s3a://{RAW_BUCKET}/pos/{date}/*.csv",
        header=True, inferSchema=True,
    )
    df.writeTo(f"{WAREHOUSE}.raw.pos_transactions").partitionedBy("transaction_date").append()
    context.log.info(f"[raw_pos] {date}: {df.count()} records")


@asset(partitions_def=DAILY, group_name="raw")
def raw_ecommerce_orders(context, spark: SparkResource, minio: MinIOResource):
    """Ingest e-commerce orders from CDC → raw Iceberg."""
    date = context.partition_key
    session = spark.get_session()
    df = session.read.json(f"s3a://{RAW_BUCKET}/ecommerce/orders/{date}/*.json")
    df.writeTo(f"{WAREHOUSE}.raw.ecommerce_orders").append()
    context.log.info(f"[raw_ecom_orders] {date}: {df.count()} records")


@asset(partitions_def=DAILY, group_name="raw")
def raw_ecommerce_customers(context, spark: SparkResource, minio: MinIOResource):
    """Ingest e-commerce customer CDC → raw Iceberg."""
    date = context.partition_key
    session = spark.get_session()
    df = session.read.json(f"s3a://{RAW_BUCKET}/ecommerce/customers/{date}/*.json")
    df.writeTo(f"{WAREHOUSE}.raw.ecommerce_customers").append()
    context.log.info(f"[raw_ecom_customers] {date}: {df.count()} records")


@asset(partitions_def=DAILY, group_name="raw")
def raw_payments(context, spark: SparkResource, minio: MinIOResource):
    """Ingest 3 payment gateways (VNPay, Momo, Card) → raw Iceberg."""
    date = context.partition_key
    session = spark.get_session()

    for gateway in ["vnpay", "momo", "card"]:
        path = f"s3a://{RAW_BUCKET}/payments/{gateway}/{date}/*.json"
        df = session.read.json(path)
        df.writeTo(f"{WAREHOUSE}.raw.payments_{gateway}").append()
        context.log.info(f"[raw_payments_{gateway}] {date}: {df.count()} records")


@asset(partitions_def=DAILY, group_name="raw")
def raw_inventory(context, spark: SparkResource, minio: MinIOResource):
    """Ingest SAP inventory snapshots → raw Iceberg (50K SKUs × 120 stores)."""
    date = context.partition_key
    session = spark.get_session()
    df = session.read.json(f"s3a://{RAW_BUCKET}/inventory/{date}/*.json")
    df.writeTo(f"{WAREHOUSE}.raw.inventory").append()
    context.log.info(f"[raw_inventory] {date}: {df.count()} records")


@asset(partitions_def=DAILY, group_name="raw")
def raw_loyalty_members(context, spark: SparkResource, minio: MinIOResource):
    """Ingest loyalty member CDC → raw Iceberg (1.5M members)."""
    date = context.partition_key
    session = spark.get_session()
    df = session.read.json(f"s3a://{RAW_BUCKET}/loyalty/{date}/*.json")
    df.writeTo(f"{WAREHOUSE}.raw.loyalty_members").append()
    context.log.info(f"[raw_loyalty] {date}: {df.count()} records")


@asset(partitions_def=DAILY, group_name="raw")
def raw_clickstream(context, spark: SparkResource, minio: MinIOResource):
    """Ingest clickstream events → raw Iceberg (5M events/day)."""
    date = context.partition_key
    session = spark.get_session()
    df = session.read.json(f"s3a://{RAW_BUCKET}/ecommerce/clickstream/{date}/*.json")
    df.writeTo(f"{WAREHOUSE}.raw.clickstream").append()
    context.log.info(f"[raw_clickstream] {date}: {df.count()} records")


# =============================================================================
# STAGING + CURATED + ANALYTICS — dbt orchestration
# =============================================================================

@asset(
    partitions_def=DAILY,
    group_name="staging",
    deps=[
        raw_pos_transactions,
        raw_ecommerce_orders,
        raw_ecommerce_customers,
        raw_payments,
        raw_inventory,
        raw_loyalty_members,
        raw_clickstream,
    ],
)
def dbt_staging(context, trino: TrinoResource):
    """Run dbt staging models (stg_*) — dedup, type cast, normalize."""
    import subprocess
    date = context.partition_key
    result = subprocess.run(
        ["uv", "run", "dbt", "run", "--select", "staging", "--vars", f'{{"run_date": "{date}"}}'],
        cwd="src/transforms",
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise Exception(f"dbt staging failed:\n{result.stderr}")
    context.log.info(f"[dbt_staging] {date} completed")


@asset(
    partitions_def=DAILY,
    group_name="curated",
    deps=[dbt_staging],
)
def dbt_intermediate(context, trino: TrinoResource):
    """Run dbt intermediate models — identity resolution, channel union, metrics."""
    import subprocess
    date = context.partition_key
    result = subprocess.run(
        ["uv", "run", "dbt", "run", "--select", "intermediate", "--vars", f'{{"run_date": "{date}"}}'],
        cwd="src/transforms",
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise Exception(f"dbt intermediate failed:\n{result.stderr}")
    context.log.info(f"[dbt_intermediate] {date} completed")


@asset(
    partitions_def=DAILY,
    group_name="analytics",
    deps=[dbt_intermediate],
)
def dbt_marts(context, trino: TrinoResource):
    """Run dbt mart models — fact/dim tables (Kimball star schema)."""
    import subprocess
    date = context.partition_key
    result = subprocess.run(
        ["uv", "run", "dbt", "run", "--select", "marts", "--vars", f'{{"run_date": "{date}"}}'],
        cwd="src/transforms",
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise Exception(f"dbt marts failed:\n{result.stderr}")
    context.log.info(f"[dbt_marts] {date} completed")


@asset(
    partitions_def=DAILY,
    group_name="analytics",
    deps=[dbt_marts],
)
def dbt_tests(context, trino: TrinoResource):
    """Run dbt tests after marts complete — data quality gate."""
    import subprocess
    date = context.partition_key
    result = subprocess.run(
        ["uv", "run", "dbt", "test", "--vars", f'{{"run_date": "{date}"}}'],
        cwd="src/transforms",
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        context.log.warning(f"[dbt_tests] FAILURES:\n{result.stdout}")
        raise Exception(f"dbt tests failed — data quality issue on {date}")
    context.log.info(f"[dbt_tests] {date} all passed")


# =============================================================================
# QUALITY — Reconciliation between batch and streaming paths
# =============================================================================

@asset(
    partitions_def=DAILY,
    group_name="quality",
    deps=[dbt_marts],
)
def reconciliation_check(context, trino: TrinoResource):
    """Compare batch (Trino/Iceberg) vs streaming (ClickHouse) revenue totals."""
    from src.quality.reconciliation import BatchStreamReconciler

    date = context.partition_key
    reconciler = BatchStreamReconciler(trino_resource=trino)
    result = reconciler.compare_daily_revenue(date)

    if result["discrepancy_pct"] > 1.0:
        context.log.warning(
            f"[reconciliation] {date}: {result['discrepancy_pct']:.2f}% discrepancy "
            f"(batch={result['batch_total']:,.0f} vs stream={result['stream_total']:,.0f})"
        )
    else:
        context.log.info(f"[reconciliation] {date}: OK ({result['discrepancy_pct']:.4f}%)")


# =============================================================================
# Export asset lists
# =============================================================================

raw_assets = [
    raw_pos_transactions,
    raw_ecommerce_orders,
    raw_ecommerce_customers,
    raw_payments,
    raw_inventory,
    raw_loyalty_members,
    raw_clickstream,
]

staging_assets = [dbt_staging]
curated_assets = [dbt_intermediate]
analytics_assets = [dbt_marts, dbt_tests, reconciliation_check]
