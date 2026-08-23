"""
Batch ingestion job: pull from source systems → write raw to MinIO.
Triggered by Dagster on schedule or sensor.
"""
import argparse

from pyspark.sql import SparkSession


def ingest_raw(spark: SparkSession, source_table: str, partition_date: str, env: str):
    bucket = f"{env}-raw"

    df = spark.read.format("jdbc").options(
        url="jdbc:postgresql://source-db:5432/operational",
        dbtable=source_table,
        driver="org.postgresql.Driver",
    ).load()

    filtered = df.filter(f"updated_at >= '{partition_date}' AND updated_at < date_add('{partition_date}', 1)")

    (
        filtered.write
        .mode("overwrite")
        .partitionBy("updated_at")
        .parquet(f"s3a://{bucket}/{source_table}/{partition_date}/")
    )

    return filtered.count()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-table", required=True)
    parser.add_argument("--partition-date", required=True)
    parser.add_argument("--env", default="dev")
    args = parser.parse_args()

    spark = SparkSession.builder.appName(f"raw-ingestion-{args.source_table}").getOrCreate()

    count = ingest_raw(spark, args.source_table, args.partition_date, args.env)
    print(f"Ingested {count} rows for {args.source_table} on {args.partition_date}")

    spark.stop()


if __name__ == "__main__":
    main()
