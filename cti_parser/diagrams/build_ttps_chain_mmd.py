#!/usr/bin/env python3
"""Build a Mermaid TTP-chain diagram from outbound JSON.

Default behavior:
- Input:  cti_parser/outbound/outbound.json
- Output: cti_parser/diagrams/ttps_chain.mmd

Only TTP-to-TTP edges are rendered, based on report xrefs where both endpoints
are ATT&CK technique IDs present in report.ttps.

Usage:
    python diagrams/build_ttps_chain_mmd.py
    python diagrams/build_ttps_chain_mmd.py --input outbound/outbound.json --output diagrams/ttps_chain.mmd
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List, Set, Tuple


def parse_args() -> argparse.Namespace:
    script_dir = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description="Generate Mermaid TTP chain .mmd from outbound JSON")
    parser.add_argument(
        "--input",
        default=str(script_dir.parent / "outbound" / "outbound.json"),
        help="Path to outbound JSON file",
    )
    parser.add_argument(
        "--output",
        default=str(script_dir / "ttps_chain.mmd"),
        help="Path for generated Mermaid .mmd file",
    )
    return parser.parse_args()


def esc(text: str) -> str:
    return text.replace('"', "'").replace("\n", " ").strip()


def node_key(report_index: int, ttp_id: str) -> str:
    cleaned = []
    for ch in ttp_id:
        cleaned.append(ch if ch.isalnum() else "_")
    return f"r{report_index}_{''.join(cleaned)}"


def collect_ttp_edges(report: Dict) -> Tuple[List[Tuple[str, str, str]], Set[str]]:
    """Return unique (src_ttp, dst_ttp, rel_type) edges and participating TTP IDs."""
    ttp_ids = {item["id"] for item in report.get("ttps", [])}
    edges: List[Tuple[str, str, str]] = []
    seen: Set[Tuple[str, str, str]] = set()
    used_ttps: Set[str] = set()

    for xref in report.get("xrefs", []):
        rel = xref.get("type", "uses")
        for src in xref.get("from", []):
            for dst in xref.get("to", []):
                if src in ttp_ids and dst in ttp_ids:
                    edge = (src, dst, rel)
                    if edge not in seen:
                        seen.add(edge)
                        edges.append(edge)
                    used_ttps.add(src)
                    used_ttps.add(dst)

    return edges, used_ttps


def build_mermaid(doc: Dict) -> str:
    lines: List[str] = []
    lines.append("flowchart LR")
    lines.append("    %% Auto-generated from outbound/outbound.json")
    lines.append("    %% TTP chains only (derived from xrefs)")

    class_nodes: List[str] = []

    for idx, report in enumerate(doc.get("reports", []), start=1):
        meta = report.get("metadata", {})
        report_url = meta.get("url", f"report-{idx}")
        edges, used_ttps = collect_ttp_edges(report)

        lines.append("")
        lines.append(f"    subgraph report_{idx}[\"Report {idx}: {esc(report_url)}\"]")

        if not edges:
            placeholder = f"r{idx}_no_ttp_chain"
            lines.append(f"    {placeholder}[\"No TTP chain found in xrefs\"]")
            lines.append("    end")
            continue

        for ttp_id in sorted(used_ttps):
            node = node_key(idx, ttp_id)
            lines.append(f"    {node}[\"{ttp_id}\"]")
            class_nodes.append(node)

        for src, dst, rel in edges:
            src_node = node_key(idx, src)
            dst_node = node_key(idx, dst)
            lines.append(f"    {src_node} -->|{esc(rel)}| {dst_node}")

        lines.append("    end")

    lines.append("")
    lines.append("    classDef ttp fill:#e6f2ff,stroke:#0066cc,stroke-width:1px")
    for node in class_nodes:
        lines.append(f"    class {node} ttp")

    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()

    input_path = Path(args.input).resolve()
    output_path = Path(args.output).resolve()

    with input_path.open("r", encoding="utf-8-sig") as fh:
        doc = json.load(fh)

    mermaid = build_mermaid(doc)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(mermaid, encoding="utf-8")

    print(f"Input : {input_path}")
    print(f"Output: {output_path}")
    print("TTP chain Mermaid generation complete.")


if __name__ == "__main__":
    main()
