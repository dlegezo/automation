#!/usr/bin/env python3
"""Build a Mermaid IOC-chain diagram from outbound JSON.

Default behavior:
- Input:  cti_parser/outbound/outbound.json
- Output: cti_parser/diagrams/iocs_chain.mmd

Only IOC-to-IOC edges are rendered, based on report xrefs where:
- type is "creates" or "uses"
- both endpoints are IOC IDs present in report.iocs

Usage:
    python diagrams/build_iocs_chain_mmd.py
    python diagrams/build_iocs_chain_mmd.py --input outbound/outbound.json --output diagrams/iocs_chain.mmd
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List, Set, Tuple


def parse_args() -> argparse.Namespace:
    script_dir = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description="Generate Mermaid IOC chain .mmd from outbound JSON")
    parser.add_argument(
        "--input",
        default=str(script_dir.parent / "outbound" / "outbound.json"),
        help="Path to outbound JSON file",
    )
    parser.add_argument(
        "--output",
        default=str(script_dir / "iocs_chain.mmd"),
        help="Path for generated Mermaid .mmd file",
    )
    return parser.parse_args()


def esc(text: str) -> str:
    return text.replace('"', "'").replace("\n", " ").strip()


def node_key(report_index: int, ioc_id: str) -> str:
    cleaned = []
    for ch in ioc_id:
        cleaned.append(ch if ch.isalnum() else "_")
    return f"r{report_index}_{''.join(cleaned)}"


def short_value(value: str, limit: int = 48) -> str:
    if len(value) <= limit:
        return value
    return value[: limit - 3] + "..."


def ioc_label(ioc: Dict) -> str:
    ioc_id = ioc.get("id", "")
    ioc_type = ioc.get("type", "")
    value = short_value(str(ioc.get("value", "")))
    return f"{ioc_id} | {ioc_type} | {value}"


def collect_ioc_edges(report: Dict) -> Tuple[List[Tuple[str, str, str]], Set[str], Dict[str, Dict]]:
    """Return unique (src_ioc, dst_ioc, rel_type) edges, used IOC IDs, and IOC lookup."""
    ioc_lookup: Dict[str, Dict] = {item.get("id", ""): item for item in report.get("iocs", []) if item.get("id")}
    ioc_ids = set(ioc_lookup.keys())

    edges: List[Tuple[str, str, str]] = []
    seen: Set[Tuple[str, str, str]] = set()
    used_iocs: Set[str] = set()

    for xref in report.get("xrefs", []):
        rel = xref.get("type", "")
        if rel not in {"creates", "uses"}:
            continue

        for src in xref.get("from", []):
            for dst in xref.get("to", []):
                if src in ioc_ids and dst in ioc_ids:
                    edge = (src, dst, rel)
                    if edge not in seen:
                        seen.add(edge)
                        edges.append(edge)
                    used_iocs.add(src)
                    used_iocs.add(dst)

    return edges, used_iocs, ioc_lookup


def build_mermaid(doc: Dict) -> str:
    lines: List[str] = []
    lines.append("flowchart LR")
    lines.append("    %% Auto-generated from outbound/outbound.json")
    lines.append("    %% IOC chains only (derived from xrefs creates/uses)")

    class_nodes: List[str] = []

    for idx, report in enumerate(doc.get("reports", []), start=1):
        meta = report.get("metadata", {})
        report_url = meta.get("url", f"report-{idx}")
        edges, used_iocs, ioc_lookup = collect_ioc_edges(report)

        lines.append("")
        lines.append(f"    subgraph report_{idx}[\"Report {idx}: {esc(report_url)}\"]")

        if not edges:
            placeholder = f"r{idx}_no_ioc_chain"
            lines.append(f"    {placeholder}[\"No IOC chain found in xrefs\"]")
            lines.append("    end")
            continue

        for ioc_id in sorted(used_iocs):
            node = node_key(idx, ioc_id)
            label = ioc_label(ioc_lookup[ioc_id])
            lines.append(f"    {node}[\"{esc(label)}\"]")
            class_nodes.append(node)

        for src, dst, rel in edges:
            src_node = node_key(idx, src)
            dst_node = node_key(idx, dst)
            lines.append(f"    {src_node} -->|{esc(rel)}| {dst_node}")

        lines.append("    end")

    lines.append("")
    lines.append("    classDef ioc fill:#eefaf1,stroke:#2c7a4b,stroke-width:1px")
    for node in class_nodes:
        lines.append(f"    class {node} ioc")

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
    print("IOC chain Mermaid generation complete.")


if __name__ == "__main__":
    main()
