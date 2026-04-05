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
import re
from pathlib import Path
from urllib.error import URLError, HTTPError
from urllib.request import Request, urlopen
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
    parser.add_argument(
        "--name-cache",
        default=str(script_dir / "mitre_technique_names.json"),
        help="Path for MITRE ATT&CK technique-name cache JSON",
    )
    return parser.parse_args()


def esc(text: str) -> str:
    return text.replace('"', "'").replace("\n", " ").strip()


def node_key(report_index: int, ttp_id: str) -> str:
    cleaned = []
    for ch in ttp_id:
        cleaned.append(ch if ch.isalnum() else "_")
    return f"r{report_index}_{''.join(cleaned)}"


def technique_web_path(ttp_id: str) -> str:
    if "." in ttp_id:
        major, sub = ttp_id.split(".", 1)
        return f"{major}/{sub}/"
    return f"{ttp_id}/"


def parse_title_to_name(title: str, ttp_id: str) -> str:
    # Example title: "Command and Scripting Interpreter: PowerShell, Technique T1059.001 - Enterprise | MITRE ATT&CK®"
    id_marker = f", Technique {ttp_id}"
    if id_marker in title:
        return title.split(id_marker, 1)[0].strip()
    # Fallback parser if title format changes.
    m = re.search(r"^(.*?)\s*-\s*Enterprise\s*\|\s*MITRE ATT&CK", title)
    if m:
        name = m.group(1).strip()
        # Strip any remaining ATT&CK title suffix for cleaner short labels.
        name = re.sub(r",\s*(Sub-technique|Technique)\s+T[0-9]{4}(\.[0-9]{3})?$", "", name)
        return name.strip()
    return ""


def fetch_mitre_name(ttp_id: str) -> str:
    url = f"https://attack.mitre.org/techniques/{technique_web_path(ttp_id)}"
    req = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; ttp-chain-builder/1.0)",
            "Accept": "text/html",
        },
    )
    try:
        with urlopen(req, timeout=10) as resp:
            html = resp.read().decode("utf-8", errors="replace")
    except (URLError, HTTPError, TimeoutError):
        return ""

    m = re.search(r"<title>(.*?)</title>", html, flags=re.IGNORECASE | re.DOTALL)
    if not m:
        return ""
    title = re.sub(r"\s+", " ", m.group(1)).strip()
    return parse_title_to_name(title, ttp_id)


def load_name_cache(cache_path: Path) -> Dict[str, str]:
    if not cache_path.exists():
        return {}
    try:
        return json.loads(cache_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def save_name_cache(cache_path: Path, cache: Dict[str, str]) -> None:
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(cache, indent=2, sort_keys=True), encoding="utf-8")


def resolve_names(ttp_ids: Set[str], cache: Dict[str, str]) -> Dict[str, str]:
    resolved: Dict[str, str] = {}
    for ttp_id in sorted(ttp_ids):
        name = cache.get(ttp_id, "")
        if not name:
            name = fetch_mitre_name(ttp_id)
            if name:
                cache[ttp_id] = name
        resolved[ttp_id] = name
    return resolved


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


def build_mermaid(doc: Dict, name_map: Dict[str, str]) -> str:
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
            ttp_name = name_map.get(ttp_id, "")
            ttp_name = re.sub(r",\s*(Sub-technique|Technique)\s+T[0-9]{4}(\.[0-9]{3})?$", "", ttp_name).strip()
            label = f"{ttp_id} - {ttp_name}" if ttp_name else ttp_id
            lines.append(f"    {node}[\"{esc(label)}\"]")
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
    cache_path = Path(args.name_cache).resolve()

    with input_path.open("r", encoding="utf-8-sig") as fh:
        doc = json.load(fh)

    all_ttps: Set[str] = set()
    for report in doc.get("reports", []):
        for ttp in report.get("ttps", []):
            ttp_id = ttp.get("id", "")
            if ttp_id.startswith("T"):
                all_ttps.add(ttp_id)

    cache = load_name_cache(cache_path)
    name_map = resolve_names(all_ttps, cache)
    save_name_cache(cache_path, cache)

    mermaid = build_mermaid(doc, name_map)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(mermaid, encoding="utf-8")

    print(f"Input : {input_path}")
    print(f"Output: {output_path}")
    print(f"Name cache: {cache_path}")
    print("TTP chain Mermaid generation complete.")


if __name__ == "__main__":
    main()
