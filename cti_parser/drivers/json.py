"""Minimal JSON file driver with the same interface as ClickHouseDriver."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


class JsonDriver:
    def __init__(self, path: Union[str, Path]) -> None:
        self._path = Path(path)

    def read(self, query: Optional[str] = None, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Load JSON from file and return as a list of dicts.

        *query* and *parameters* are accepted for interface parity but ignored.
        """
        if not self._path.exists():
            return []
        data = json.loads(self._path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return data
        return [data]

    def write(self, table: Optional[str] = None, rows: Optional[List[Dict[str, Any]]] = None) -> None:
        """Serialise *rows* to the JSON file, replacing existing content.

        *table* is accepted for interface parity but ignored.
        """
        if rows is None:
            rows = []
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")

    def execute(self, query: Optional[str] = None, parameters: Optional[Dict[str, Any]] = None) -> None:
        """No-op — kept for interface parity with ClickHouseDriver."""

    def close(self) -> None:
        """No-op — no persistent connection to close."""

    def __enter__(self) -> "JsonDriver":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()
