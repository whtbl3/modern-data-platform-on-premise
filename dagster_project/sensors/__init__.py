from dagster import DefaultSensorStatus, RunRequest, SensorEvaluationContext, sensor

from ..resources import MinIOResource

WATCHED_PREFIXES = [
    "pos/",
    "ecommerce/orders/",
    "ecommerce/customers/",
    "payments/vnpay/",
    "payments/momo/",
    "payments/card/",
    "inventory/",
    "loyalty/",
    "ecommerce/clickstream/",
]


@sensor(
    job_name="__ASSET_JOB",
    minimum_interval_seconds=60,
    default_status=DefaultSensorStatus.RUNNING,
    description="Detect new files in MinIO raw bucket across all VietMart sources",
)
def minio_file_sensor(context: SensorEvaluationContext, minio: MinIOResource):
    client = minio.get_client()
    cursor = context.cursor or ""
    bucket = "dev-raw"

    latest_key = cursor
    for prefix in WATCHED_PREFIXES:
        response = client.list_objects_v2(
            Bucket=bucket,
            Prefix=prefix,
            StartAfter=cursor,
        )

        for obj in response.get("Contents", []):
            key = obj["Key"]
            parts = key.split("/")
            date_part = next((p for p in parts if len(p) == 10 and p[4] == "-"), None)
            if date_part:
                yield RunRequest(run_key=key, partition_key=date_part)
            latest_key = max(latest_key, key)

    if latest_key != cursor:
        context.update_cursor(latest_key)
