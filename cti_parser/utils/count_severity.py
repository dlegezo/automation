#!/usr/bin/env python3
"""Compute per-report severity from tags Jaccard distance.

Severity is stored as an integer percentage in report.metadata.severity:
severity = round(jaccard_distance(report_tags, tags_of_interest) * 100)
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable, Set

from utils import jaccard_distance, normalize_tag


def parse_args() -> argparse.Namespace:
    base_dir = Path(__file__).resolve().parent
    default_inbound = base_dir.parent / "inbound" / "inbound.json"
    default_outbound = base_dir.parent / "outbound"

    parser = argparse.ArgumentParser(description="Count severity for outbound report files")
    parser.add_argument("--inbound", default=str(default_inbound), help="Path to inbound JSON")
    parser.add_argument("--outbound-dir", default=str(default_outbound), help="Path to outbound directory")
    parser.add_argument("--dry-run", action="store_true", help="Print values without writing files")
    return parser.parse_args()


def flatten_tag_values(node: Any) -> Iterable[str]:
    if isinstance(node, str):
        yield node
    elif isinstance(node, list):
        for item in node:
            yield from flatten_tag_values(item)
    elif isinstance(node, dict):
        for value in node.values():
            yield from flatten_tag_values(value)


def load_tags_of_interest(inbound_path: Path) -> Set[str]:
    with inbound_path.open("r", encoding="utf-8-sig") as f:
        inbound_doc = json.load(f)

    toi = inbound_doc.get("tags_of_interest", {})
    tags = {normalize_tag(tag) for tag in flatten_tag_values(toi) if isinstance(tag, str) and tag.strip()}
    if not tags:
        raise ValueError("No tags_of_interest found in inbound file")
    return tags


def load_report_tags(report_doc: dict) -> Set[str]:
    metadata = report_doc.get("report", {}).get("metadata", {})
    raw_tags = metadata.get("tags", [])
    if not isinstance(raw_tags, list):
        return set()
    return {normalize_tag(tag) for tag in raw_tags if isinstance(tag, str) and tag.strip()}


def iter_report_files(outbound_dir: Path) -> Iterable[Path]:
    for path in sorted(outbound_dir.glob("*.json")):
        if path.name.lower() == "outbound.json":
            continue
        yield path


def main() -> None:
    args = parse_args()
    inbound_path = Path(args.inbound).resolve()
    outbound_dir = Path(args.outbound_dir).resolve()

    tags_of_interest = load_tags_of_interest(inbound_path)

    updated_count = 0
    for report_path in iter_report_files(outbound_dir):
        with report_path.open("r", encoding="utf-8-sig") as f:
            report_doc = json.load(f)

        report_tags = load_report_tags(report_doc)
        severity = int(round(jaccard_distance(report_tags, tags_of_interest) * 100))

        report_doc.setdefault("report", {}).setdefault("metadata", {})["severity"] = severity

        if not args.dry_run:
            with report_path.open("w", encoding="utf-8") as f:
                json.dump(report_doc, f, ensure_ascii=False, indent=4)
                f.write("\n")

        print(f"{report_path.name}: severity={severity}")
        updated_count += 1

    print(f"Updated {updated_count} report files")


if __name__ == "__main__":
    main()
