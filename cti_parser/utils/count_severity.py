#!/usr/bin/env python3
"""Compute per-report severity from tags overlap.

Severity is stored as a float in [0.0, 1.0] in report.metadata.severity:
severity = jaccard_similarity(report_tags, tags_of_interest)
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Set

from utils import extract_report_tags, flatten_tag_values, iter_report_files, jaccard_similarity, normalize_tag


def parse_args() -> argparse.Namespace:
    base_dir = Path(__file__).resolve().parent
    default_inbound = base_dir.parent / "inbound" / "inbound.json"
    default_outbound = base_dir.parent / "outbound"

    parser = argparse.ArgumentParser(description="Count severity for outbound report files")
    parser.add_argument("--inbound", default=str(default_inbound), help="Path to inbound JSON")
    parser.add_argument("--outbound-dir", default=str(default_outbound), help="Path to outbound directory")
    parser.add_argument("--dry-run", action="store_true", help="Print values without writing files")
    return parser.parse_args()


def load_tags_of_interest(inbound_path: Path) -> Set[str]:
    with inbound_path.open("r", encoding="utf-8-sig") as f:
        inbound_doc = json.load(f)

    toi = inbound_doc.get("tags_of_interest", {})
    tags = {normalize_tag(tag) for tag in flatten_tag_values(toi) if isinstance(tag, str) and tag.strip()}
    if not tags:
        raise ValueError("No tags_of_interest found in inbound file")
    return tags


def main() -> None:
    args = parse_args()
    inbound_path = Path(args.inbound).resolve()
    outbound_dir = Path(args.outbound_dir).resolve()

    tags_of_interest = load_tags_of_interest(inbound_path)

    updated_count = 0
    for report_path in iter_report_files(outbound_dir):
        with report_path.open("r", encoding="utf-8-sig") as f:
            report_doc = json.load(f)

        report = report_doc.get("report", {})
        report_tags = extract_report_tags(report if isinstance(report, dict) else {})
        severity = round(jaccard_similarity(report_tags, tags_of_interest), 4)

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
