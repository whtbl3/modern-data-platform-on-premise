"""Sink: write data as JSON/Parquet files to MinIO (S3-compatible)."""
import io
import json
from dataclasses import dataclass
from datetime import UTC, datetime

import boto3

from .base import BaseSink


@dataclass
class MinIOConfig:
    endpoint: str = "http://localhost:9000"
    access_key: str = "minioadmin"
    secret_key: str = "minioadmin"
    bucket: str = "dev-raw"


class MinIOSink(BaseSink):
    def __init__(self, config: MinIOConfig | None = None):
        self.config = config or MinIOConfig()
        self._client = None

    def connect(self) -> None:
        self._client = boto3.client(
            "s3",
            endpoint_url=self.config.endpoint,
            aws_access_key_id=self.config.access_key,
            aws_secret_access_key=self.config.secret_key,
        )
        self._ensure_bucket()

    def _ensure_bucket(self):
        try:
            self._client.head_bucket(Bucket=self.config.bucket)
        except self._client.exceptions.ClientError:
            self._client.create_bucket(Bucket=self.config.bucket)

    def write(self, records: list[dict], target: str) -> int:
        if not records:
            return 0

        now = datetime.now(UTC)
        partition = now.strftime("%Y-%m-%d")
        timestamp = now.strftime("%H%M%S")

        key = f"{target}/{partition}/{timestamp}_{len(records)}.json"

        body = "\n".join(json.dumps(r, default=str) for r in records)

        self._client.put_object(
            Bucket=self.config.bucket,
            Key=key,
            Body=body.encode("utf-8"),
            ContentType="application/x-ndjson",
        )

        return len(records)

    def write_parquet(self, records: list[dict], target: str) -> int:
        """Write as Parquet using pyarrow."""
        import pyarrow as pa
        import pyarrow.parquet as pq

        if not records:
            return 0

        table = pa.Table.from_pylist(records)
        buffer = io.BytesIO()
        pq.write_table(table, buffer)
        buffer.seek(0)

        now = datetime.now(UTC)
        partition = now.strftime("%Y-%m-%d")
        timestamp = now.strftime("%H%M%S")
        key = f"{target}/{partition}/{timestamp}_{len(records)}.parquet"

        self._client.put_object(
            Bucket=self.config.bucket,
            Key=key,
            Body=buffer.getvalue(),
            ContentType="application/octet-stream",
        )

        return len(records)

    def close(self) -> None:
        self._client = None
