import boto3
from dagster import ConfigurableResource, EnvVar
from pyspark.sql import SparkSession


class SparkResource(ConfigurableResource):
    master: str = "k8s://https://kubernetes.default.svc"
    app_name: str = "lakehouse"
    metastore_uri: str = "thrift://hive-metastore:9083"

    def get_session(self) -> SparkSession:
        return (
            SparkSession.builder
            .master(self.master)
            .appName(self.app_name)
            .config("spark.sql.catalog.lakehouse", "org.apache.iceberg.spark.SparkCatalog")
            .config("spark.sql.catalog.lakehouse.type", "hive")
            .config("spark.sql.catalog.lakehouse.uri", self.metastore_uri)
            .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions")
            .config("spark.dynamicAllocation.enabled", "true")
            .config("spark.dynamicAllocation.minExecutors", "1")
            .config("spark.dynamicAllocation.maxExecutors", "10")
            .getOrCreate()
        )


class MinIOResource(ConfigurableResource):
    endpoint: str
    access_key: str
    secret_key: str

    def get_client(self):
        return boto3.client(
            "s3",
            endpoint_url=self.endpoint,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
        )


class TrinoResource(ConfigurableResource):
    host: str = "trino"
    port: int = 8080
    catalog: str = "iceberg"

    def get_connection(self):
        from trino.dbapi import connect
        return connect(host=self.host, port=self.port, catalog=self.catalog)


spark_resource = SparkResource(
    master=EnvVar("SPARK_MASTER"),
    metastore_uri=EnvVar("HIVE_METASTORE_URI"),
)

minio_resource = MinIOResource(
    endpoint=EnvVar("MINIO_ENDPOINT"),
    access_key=EnvVar("MINIO_ACCESS_KEY"),
    secret_key=EnvVar("MINIO_SECRET_KEY"),
)

trino_resource = TrinoResource(
    host=EnvVar("TRINO_HOST"),
)
