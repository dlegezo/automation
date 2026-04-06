#!/usr/bin/env python3
"""Compute pairwise Jaccard distances between CTI reports.

For each report pair in outbound JSON, the script computes:
1) TTP Jaccard distance on report.ttps IDs
2) TTP-chain Jaccard distance on report.xrefs edges where type == "follows"
3) Tags Jaccard distance on report.metadata.tags

Output is written to attribution/count_jaccard.md as a compact markdown table.
"""

from __future__ import annotations

import argparse
import itertools
import json
import re
from pathlib import Path
from typing import Dict, Iterable, List, Set, Tuple
from urllib.parse import urlparse


TTP_RE = re.compile(r"^T[0-9]{4}(\.[0-9]{3})?$")


def parse_args() -> argparse.Namespace:
    base_dir = Path(__file__).resolve().parent
    default_input = base_dir.parent / "outbound" / "outbound.json"
    default_output = base_dir / "count_jaccard.md"

    parser = argparse.ArgumentParser(description="Count Jaccard distances between reports")
    parser.add_argument("--input", default=str(default_input), help="Path to outbound JSON")
    parser.add_argument("--output", default=str(default_output), help="Path to markdown output")
    return parser.parse_args()


def is_ttp(value: str) -> bool:
    return bool(TTP_RE.match(value))


def jaccard_distance(left: Set, right: Set) -> float:
    union = left | right
    if not union:
        return 0.0
    intersection = left & right
    similarity = len(intersection) / len(union)
    return 1.0 - similarity


def report_label(report: Dict, index: int) -> str:
    url = report.get("metadata", {}).get("url", "")
    if not url:
        return f"R{index}"
    parsed = urlparse(url)
    host = parsed.netloc or "unknown"
    path = parsed.path.strip("/")
    if len(path) > 36:
        path = path[:33] + "..."
    tail = f"/{path}" if path else ""
    return f"R{index} {host}{tail}"


def extract_ttps(report: Dict) -> Set[str]:
    result: Set[str] = set()
    for item in report.get("ttps", []):
        ttp_id = item.get("id", "")
        if is_ttp(ttp_id):
            result.add(ttp_id)
    return result


def extract_follows_edges(report: Dict, ttps: Set[str]) -> Set[Tuple[str, str]]:
    edges: Set[Tuple[str, str]] = set()
    for xref in report.get("xrefs", []):
        if xref.get("type") != "follows":
            continue
        sources = [x for x in xref.get("from", []) if x in ttps and is_ttp(x)]
        targets = [x for x in xref.get("to", []) if x in ttps and is_ttp(x)]
        for src, dst in itertools.product(sources, targets):
            edges.add((src, dst))
    return edges


def extract_tags(report: Dict) -> Set[str]:
    """Extract tags from report metadata."""
    tags: Set[str] = set()
    metadata = report.get("metadata", {})
    tag_list = metadata.get("tags", [])
    if isinstance(tag_list, list):
        for tag in tag_list:
            if isinstance(tag, str):
                tags.add(tag.strip().lower())
    return tags


def build_table(rows: Iterable[Tuple[str, str, float, float, float]]) -> str:
    lines: List[str] = []
    lines.append("# Jaccard Distances Between Reports")
    lines.append("")
    lines.append("Jaccard distance formula: 1 - (intersection/union).")
    lines.append("Lower is closer. 0 means identical, 1 means no overlap.")
    lines.append("")
    lines.append("| Report A | Report B | TTP distance | TTP follows-chain distance | Tags distance |")
    lines.append("| --- | --- | ---: | ---: | ---: |")
    for rep_a, rep_b, ttp_dist, chain_dist, tags_dist in rows:
        lines.append(
            f"| {rep_a} | {rep_b} | {ttp_dist:.4f} | {chain_dist:.4f} | {tags_dist:.4f} |"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    input_path = Path(args.input).resolve()
    output_path = Path(args.output).resolve()

    with input_path.open("r", encoding="utf-8-sig") as f:
        doc = json.load(f)

    reports = doc.get("reports", [])
    if len(reports) < 2:
        raise ValueError("Need at least two reports to compute pairwise distances")

    extracted = []
    for idx, report in enumerate(reports, start=1):
        label = report_label(report, idx)
        ttps = extract_ttps(report)
        ttp_chains = extract_follows_edges(report, ttps)
        tags = extract_tags(report)
        extracted.append((label, ttps, ttp_chains, tags))

    rows: List[Tuple[str, str, float, float, float]] = []
    for i in range(len(extracted)):
        for j in range(i + 1, len(extracted)):
            label_a, ttps_a, ttp_chains_a, tags_a = extracted[i]
            label_b, ttps_b, ttp_chains_b, tags_b = extracted[j]
            ttp_dist = jaccard_distance(ttps_a, ttps_b)
            ttp_chain_dist = jaccard_distance(ttp_chains_a, ttp_chains_b)
            tags_dist = jaccard_distance(tags_a, tags_b)
            rows.append((label_a, label_b, ttp_dist, ttp_chain_dist, tags_dist))

    markdown = build_table(rows)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(markdown, encoding="utf-8")

    print(f"Input : {input_path}")
    print(f"Output: {output_path}")
    print(f"Pairs : {len(rows)}")


if __name__ == "__main__":
    main()
