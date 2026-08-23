"""
Batch job: raw → staging layer.
Clean, deduplicate, validate, write as Iceberg table.
"""
import argparse

from pyspark.sql import SparkSession
from pyspark.sql import functions as F


def transform_to_staging(spark: SparkSession, table: str, partition_date: str, env: str):
    raw_path = f"s3a://{env}-raw/{table}/{partition_date}/"

    df = spark.read.parquet(raw_path)

    cleaned = (
        df
        .dropDuplicates([f"{table[:-1]}_id"])
        .filter(F.col(f"{table[:-1]}_id").isNotNull())
        .withColumn("_ingested_at", F.current_timestamp())
        .withColumn("_partition_date", F.lit(partition_date))
    )

    (
        cleaned.writeTo(f"lakehouse.staging.{table}")
        .partitionedBy("_partition_date")
        .createOrReplace()
    )

    return cleaned.count()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--table", required=True)
    parser.add_argument("--partition-date", required=True)
    parser.add_argument("--env", default="dev")
    args = parser.parse_args()

    spark = SparkSession.builder.appName(f"staging-{args.table}").getOrCreate()

    count = transform_to_staging(spark, args.table, args.partition_date, args.env)
    print(f"Staged {count} rows for {args.table}")

    spark.stop()


if __name__ == "__main__":
    main()
