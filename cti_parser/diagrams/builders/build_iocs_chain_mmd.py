#!/usr/bin/env python3
"""Build a Mermaid IOC-chain diagram from outbound per-report JSON files.

Default behavior:
- Input dir: cti_parser/outbound/*.json
- Output:    cti_parser/diagrams/iocs_chain.mmd

Only IOC-to-IOC edges are rendered, based on report xrefs where:
- type is "creates" or "uses"
- both endpoints are IOC IDs present in report.iocs
"""

from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path
from typing import Dict, List, Set, Tuple


def _load_utils_module():
    utils_path = Path(__file__).resolve().parents[2] / "utils" / "utils.py"
    spec = importlib.util.spec_from_file_location("cti_shared_utils", utils_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load shared utils from {utils_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_utils = _load_utils_module()
esc_mermaid = _utils.esc_mermaid
load_report_objects = _utils.load_report_objects
sanitize_node_key = _utils.sanitize_node_key
shorten_text = _utils.shorten_text


def parse_args() -> argparse.Namespace:
    script_dir = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description="Generate Mermaid IOC chain .mmd from outbound report JSON files")
    parser.add_argument(
        "--input-dir",
        default=str(script_dir.parent.parent / "outbound"),
        help="Path to outbound report JSON directory",
    )
    parser.add_argument(
        "--output",
        default=str(script_dir.parent / "iocs_chain.mmd"),
        help="Path for generated Mermaid .mmd file",
    )
    return parser.parse_args()


def node_key(report_index: int, ioc_id: str) -> str:
    return f"r{report_index}_{sanitize_node_key(ioc_id)}"


def ioc_label(ioc: Dict) -> str:
    ioc_id = ioc.get("id", "")
    ioc_type = ioc.get("type", "")
    value = shorten_text(str(ioc.get("value", "")))
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


def build_mermaid(reports: List[Dict]) -> str:
    lines: List[str] = []
    lines.append("flowchart LR")
    lines.append("    %% Auto-generated from outbound/*.json")
    lines.append("    %% IOC chains only (derived from xrefs creates/uses)")

    class_nodes: List[str] = []

    for idx, report in enumerate(reports, start=1):
        meta = report.get("metadata", {})
        report_url = meta.get("url", f"report-{idx}")
        edges, used_iocs, ioc_lookup = collect_ioc_edges(report)

        lines.append("")
        lines.append(f"    subgraph report_{idx}[\"Report {idx}: {esc_mermaid(report_url)}\"]")

        if not edges:
            placeholder = f"r{idx}_no_ioc_chain"
            lines.append(f"    {placeholder}[\"No IOC chain found in xrefs\"]")
            lines.append("    end")
            continue

        for ioc_id in sorted(used_iocs):
            node = node_key(idx, ioc_id)
            label = ioc_label(ioc_lookup[ioc_id])
            lines.append(f"    {node}[\"{esc_mermaid(label)}\"]")
            class_nodes.append(node)

        for src, dst, rel in edges:
            src_node = node_key(idx, src)
            dst_node = node_key(idx, dst)
            lines.append(f"    {src_node} -->|{esc_mermaid(rel)}| {dst_node}")

        lines.append("    end")

    lines.append("")
    lines.append("    classDef ioc fill:#eefaf1,stroke:#2c7a4b,stroke-width:1px")
    for node in class_nodes:
        lines.append(f"    class {node} ioc")

    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()

    input_dir = Path(args.input_dir).resolve()
    output_path = Path(args.output).resolve()

    reports = load_report_objects(input_dir)

    mermaid = build_mermaid(reports)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(mermaid, encoding="utf-8")

    print(f"Input dir: {input_dir}")
    print(f"Output: {output_path}")
    print("IOC chain Mermaid generation complete.")


if __name__ == "__main__":
    main()
