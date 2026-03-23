from typing import Set, Dict, Any, Optional, List
from datetime import datetime
import csv
from io import StringIO


def build_csv_content(ioc_store: Dict[str, Dict[str, Set[str]]]) -> str:
    lines = ["source,type,parent,ioc,created"]
    for source_name, hash_map in ioc_store.items():
        for hash_id, domains in hash_map.items():
            for domain, created in domains.items():
                created_formated = datetime.fromtimestamp(created)
                lines.append(f'"{source_name}","domain","{hash_id}","{domain}","{created_formated}"')
    return '\n'.join(lines)


def build_csv_content2(
    ioc_store: Dict[str, List[Dict[str, Any]]],  # {"source_name": [ioc1, ioc2, ...]}
    fields: Optional[List[str]] = None,           # Explicit fields or auto-detect
    include_source: bool = True,                  # Add 'source' column
    include_timestamp: bool = True                # Add 'enriched_at' column
) -> str:
    """
    Build CSV content from dynamic IOC store.

    Args:
        ioc_store: Dict of sources → list of IOC dicts
        fields: Specific fields to include (None = all keys from first IOC)
        include_source: Add source column
        include_timestamp: Add enrichment timestamp

    Returns:
        CSV string ready for Gist upload
    """
    if not ioc_store:
        return ""

    # Auto-detect fields if not specified
    sample_ioc = next(iter(ioc_store.values()))[0] if ioc_store else {}
    all_keys = set(sample_ioc.keys())
    for iocs in ioc_store.values():
        for ioc in iocs:
            all_keys.update(ioc.keys())

    if fields:
        csv_fields = list(fields)
    else:
        csv_fields = sorted(all_keys)

    if include_source:
        csv_fields = ['source'] + csv_fields
    if include_timestamp:
        csv_fields.append('enriched_at')

    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=csv_fields)
    writer.writeheader()

    now = datetime.now().isoformat()
    for source_name, iocs in ioc_store.items():
        for ioc in iocs:
            row = dict(ioc)
            if include_source:
                row['source'] = source_name
            if include_timestamp:
                row['enriched_at'] = now
            writer.writerow(row)

    return output.getvalue()
