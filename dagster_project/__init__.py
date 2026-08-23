from dagster import Definitions

from .assets import analytics_assets, curated_assets, raw_assets, staging_assets
from .resources import minio_resource, spark_resource, trino_resource
from .sensors import minio_file_sensor

defs = Definitions(
    assets=[*raw_assets, *staging_assets, *curated_assets, *analytics_assets],
    sensors=[minio_file_sensor],
    resources={
        "spark": spark_resource,
        "minio": minio_resource,
        "trino": trino_resource,
    },
)
