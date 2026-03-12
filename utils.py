from typing import Set
from datetime import datetime


def build_csv_content(ioc_store: Dict[str, Dict[str, Set[str]]]) -> str:
    lines = ["source,type,parent,ioc,created"]
    for source_name, hash_map in ioc_store.items():
        for hash_id, domains in hash_map.items():
            for domain, created in domains.items():
                created_formated = datetime.fromtimestamp(created)
                lines.append(f'"{source_name}","domain","{hash_id}","{domain}","{created_formated}"')
    return '\n'.join(lines)
