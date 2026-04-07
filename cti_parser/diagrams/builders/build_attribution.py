#!/usr/bin/env python3
"""Build attribution markdown from outbound per-report JSON files.

Tables generated:
1) Pairwise attribution distances between reports
2) Popularity of TTP follows-pairs across reports (count > 1)

Output is written to diagrams/attribution/attribution.md.
"""

from __future__ import annotations

import argparse
import importlib.util
import itertools
import re
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List, Set, Tuple
from urllib.parse import urlparse


def _load_utils_module():
    utils_path = Path(__file__).resolve().parents[2] / "utils" / "utils.py"
    spec = importlib.util.spec_from_file_location("cti_shared_utils", utils_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load shared utils from {utils_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_utils = _load_utils_module()
extract_report_tags = _utils.extract_report_tags
jaccard_distance = _utils.jaccard_distance
load_report_objects = _utils.load_report_objects

TTP_RE = re.compile(r"^T[0-9]{4}(\.[0-9]{3})?$")


def parse_args() -> argparse.Namespace:
    base_dir = Path(__file__).resolve().parent
    default_input_dir = base_dir.parent.parent / "outbound"
    default_output = base_dir.parent / "attribution" / "attribution.md"

    parser = argparse.ArgumentParser(description="Build attribution markdown between reports")
    parser.add_argument("--input-dir", default=str(default_input_dir), help="Path to outbound report JSON directory")
    parser.add_argument("--output", default=str(default_output), help="Path to markdown output")
    return parser.parse_args()


def is_ttp(value: str) -> bool:
    return bool(TTP_RE.match(value))


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


def extract_follows_edges(report: Dict, ttps: Set[str]) -> Set[str]:
    edges: Set[str] = set()
    for xref in report.get("xrefs", []):
        if xref.get("type") != "follows":
            continue
        sources = [x for x in xref.get("from", []) if x in ttps and is_ttp(x)]
        targets = [x for x in xref.get("to", []) if x in ttps and is_ttp(x)]
        for src, dst in itertools.product(sources, targets):
            edges.add(f"{src}->{dst}")
    return edges


def build_distance_table(rows: Iterable[Tuple[str, str, float, float, float]]) -> List[str]:
    lines: List[str] = []
    lines.append("# Attribution Distances Between Reports")
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
    return lines


def build_popularity_table(counter: Counter[str]) -> List[str]:
    lines: List[str] = []
    lines.append("## TTP Follows-Pairs Popularity Across Reports")
    lines.append("")
    lines.append("Only pairs seen in more than one report are listed.")
    lines.append("")
    lines.append("| TTP follows pair | Popularity (reports) |")
    lines.append("| --- | ---: |")

    popular_pairs = [(pair, count) for pair, count in counter.items() if count > 1]
    popular_pairs.sort(key=lambda item: (-item[1], item[0]))

    for pair, count in popular_pairs:
        lines.append(f"| {pair} | {count} |")

    if not popular_pairs:
        lines.append("| _No pairs with popularity > 1_ | 0 |")

    lines.append("")
    return lines


def main() -> None:
    args = parse_args()
    input_dir = Path(args.input_dir).resolve()
    output_path = Path(args.output).resolve()

    reports = load_report_objects(input_dir)
    if len(reports) < 2:
        raise ValueError("Need at least two reports to compute pairwise distances")

    extracted = []
    follows_popularity: Counter[str] = Counter()

    for idx, report in enumerate(reports, start=1):
        label = report_label(report, idx)
        ttps = extract_ttps(report)
        ttp_chains = extract_follows_edges(report, ttps)
        tags = extract_report_tags(report)
        extracted.append((label, ttps, ttp_chains, tags))

        # Count each follows pair once per report.
        for pair in ttp_chains:
            follows_popularity[pair] += 1

    rows: List[Tuple[str, str, float, float, float]] = []
    for i in range(len(extracted)):
        for j in range(i + 1, len(extracted)):
            label_a, ttps_a, ttp_chains_a, tags_a = extracted[i]
            label_b, ttps_b, ttp_chains_b, tags_b = extracted[j]
            ttp_dist = jaccard_distance(ttps_a, ttps_b)
            ttp_chain_dist = jaccard_distance(ttp_chains_a, ttp_chains_b)
            tags_dist = jaccard_distance(tags_a, tags_b)
            rows.append((label_a, label_b, ttp_dist, ttp_chain_dist, tags_dist))

    lines = []
    lines.extend(build_distance_table(rows))
    lines.extend(build_popularity_table(follows_popularity))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")

    print(f"Input dir: {input_dir}")
    print(f"Output   : {output_path}")
    print(f"Pairs    : {len(rows)}")


if __name__ == "__main__":
    main()
