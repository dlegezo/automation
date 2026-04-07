#!/usr/bin/env python3
"""Shared utility helpers for CTI parser scripts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Set


def normalize_tag(value: str) -> str:
    return value.strip().lower()


def jaccard_distance(left: Set[str], right: Set[str]) -> float:
    """Return Jaccard distance in [0.0, 1.0]."""
    union = left | right
    if not union:
        return 0.0
    similarity = len(left & right) / len(union)
    return 1.0 - similarity


def flatten_tag_values(node: Any) -> Iterable[str]:
    if isinstance(node, str):
        yield node
    elif isinstance(node, list):
        for item in node:
            yield from flatten_tag_values(item)
    elif isinstance(node, dict):
        for value in node.values():
            yield from flatten_tag_values(value)


def extract_report_tags(report: Dict[str, Any]) -> Set[str]:
    metadata = report.get("metadata", {})
    raw_tags = metadata.get("tags", [])
    if not isinstance(raw_tags, list):
        return set()
    return {normalize_tag(tag) for tag in raw_tags if isinstance(tag, str) and tag.strip()}


def iter_report_files(outbound_dir: Path) -> Iterable[Path]:
    for path in sorted(outbound_dir.glob("*.json")):
        if path.name.lower() == "outbound.json":
            continue
        yield path


def load_report_objects(outbound_dir: Path) -> List[Dict[str, Any]]:
    reports: List[Dict[str, Any]] = []
    for report_file in iter_report_files(outbound_dir):
        with report_file.open("r", encoding="utf-8-sig") as f:
            doc = json.load(f)
        report = doc.get("report", {})
        if isinstance(report, dict) and report:
            reports.append(report)
    return reports


def esc_mermaid(text: str) -> str:
    return text.replace('"', "'").replace("\n", " ").strip()


def sanitize_node_key(text: str) -> str:
    cleaned = []
    for ch in text:
        cleaned.append(ch if ch.isalnum() else "_")
    return "".join(cleaned)


def shorten_text(value: str, limit: int = 48) -> str:
    if len(value) <= limit:
        return value
    return value[: limit - 3] + "..."
