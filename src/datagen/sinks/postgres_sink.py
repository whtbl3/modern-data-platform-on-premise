"""Sink: write to PostgreSQL (simulates operational/transactional source DB)."""
import json
from dataclasses import dataclass

import psycopg2
from psycopg2.extras import execute_values

from .base import BaseSink


@dataclass
class PostgresConfig:
    host: str = "localhost"
    port: int = 5432
    database: str = "operational"
    user: str = "postgres"
    password: str = "postgres"


class PostgresSink(BaseSink):
    def __init__(self, config: PostgresConfig | None = None):
        self.config = config or PostgresConfig()
        self._conn = None

    def connect(self) -> None:
        self._conn = psycopg2.connect(
            host=self.config.host,
            port=self.config.port,
            database=self.config.database,
            user=self.config.user,
            password=self.config.password,
        )
        self._conn.autocommit = False

    def write(self, records: list[dict], target: str) -> int:
        """Write records to a table. Target = table name. Auto-creates table if not exists."""
        if not records:
            return 0

        columns = list(records[0].keys())
        self._ensure_table(target, records[0])

        col_str = ", ".join(columns)
        template = f"({', '.join(['%s'] * len(columns))})"

        values = []
        for record in records:
            row = []
            for col in columns:
                val = record.get(col)
                if isinstance(val, (dict, list)):
                    val = json.dumps(val, default=str)
                row.append(val)
            values.append(tuple(row))

        with self._conn.cursor() as cur:
            query = f"INSERT INTO {target} ({col_str}) VALUES %s ON CONFLICT DO NOTHING"
            execute_values(cur, query, values, template=template)

        self._conn.commit()
        return len(records)

    def _ensure_table(self, table: str, sample_record: dict):
        """Create table if not exists based on sample record structure."""
        columns_def = []
        for key, value in sample_record.items():
            pg_type = self._infer_pg_type(value)
            columns_def.append(f"{key} {pg_type}")

        create_sql = f"""
            CREATE TABLE IF NOT EXISTS {table} (
                {', '.join(columns_def)}
            )
        """

        with self._conn.cursor() as cur:
            cur.execute(create_sql)
        self._conn.commit()

    def _infer_pg_type(self, value) -> str:
        if isinstance(value, bool):
            return "BOOLEAN"
        if isinstance(value, int):
            return "BIGINT"
        if isinstance(value, float):
            return "DOUBLE PRECISION"
        if isinstance(value, (dict, list)):
            return "JSONB"
        return "TEXT"

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None
