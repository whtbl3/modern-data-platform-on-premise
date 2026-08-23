"""Unit tests for staging transform logic."""
import pytest
from pyspark.sql import SparkSession


@pytest.fixture(scope="session")
def spark():
    session = (
        SparkSession.builder
        .master("local[1]")
        .appName("test")
        .config("spark.sql.shuffle.partitions", "1")
        .getOrCreate()
    )
    yield session
    session.stop()


def test_deduplication(spark):
    data = [
        ("ord_1", "cust_1", 100.0, "completed"),
        ("ord_1", "cust_1", 100.0, "completed"),
        ("ord_2", "cust_2", 200.0, "pending"),
    ]
    df = spark.createDataFrame(data, ["order_id", "customer_id", "amount", "status"])

    deduped = df.dropDuplicates(["order_id"])

    assert deduped.count() == 2


def test_null_filter(spark):
    data = [
        ("ord_1", "cust_1", 100.0),
        (None, "cust_2", 200.0),
        ("ord_3", "cust_3", None),
    ]
    df = spark.createDataFrame(data, ["order_id", "customer_id", "amount"])

    filtered = df.filter("order_id IS NOT NULL AND amount IS NOT NULL")

    assert filtered.count() == 1
    assert filtered.first()["order_id"] == "ord_1"


def test_amount_positive_filter(spark):
    data = [
        ("ord_1", 100.0),
        ("ord_2", -50.0),
        ("ord_3", 0.0),
    ]
    df = spark.createDataFrame(data, ["order_id", "amount"])

    valid = df.filter("amount > 0")

    assert valid.count() == 1
