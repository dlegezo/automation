from typing import Set


def build_csv_content(ioc_store: Dict[str, Dict[str, Set[str]]]) -> str:
    lines = ["source,type,parent,ioc"]
    for source_name, hash_map in ioc_store.items():
        for hash_id, domains in hash_map.items():
            for domain in domains:
                lines.append(f'"{source_name}","domain","{hash_id}","{domain}"')
    return '\n'.join(lines)
