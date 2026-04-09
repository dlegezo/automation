"""Minimal ClickHouse driver using clickhouse-connect."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

import clickhouse_connect
from clickhouse_connect.driver.client import Client


class ClickHouseDriver:
    def __init__(
        self,
        host: str = "localhost",
        port: int = 8123,
        username: str = "default",
        password: str = "",
        database: str = "default",
    ) -> None:
        self._client: Client = clickhouse_connect.get_client(
            host=host,
            port=port,
            username=username,
            password=password,
            database=database,
        )

    def read(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute a SELECT query and return rows as a list of dicts."""
        result = self._client.query(query, parameters=parameters or {})
        columns = result.column_names
        return [dict(zip(columns, row)) for row in result.result_rows]

    def write(self, table: str, rows: List[Dict[str, Any]]) -> None:
        """Insert a list of dicts into *table*."""
        if not rows:
            return
        column_names = list(rows[0].keys())
        data = [[row[col] for col in column_names] for row in rows]
        self._client.insert(table, data, column_names=column_names)

    def execute(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> None:
        """Execute a non-SELECT statement (CREATE TABLE, DROP, etc.)."""
        self._client.command(query, parameters=parameters or {})

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "ClickHouseDriver":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()
