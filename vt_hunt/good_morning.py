import os
import requests
import json
import logging
from typing import Dict, List, Any


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def load_config(config_path: str = 'config.json') -> Dict[str, Any]:
    """Load config with validation."""
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        if 'sources' not in config:
            raise ValueError("Missing 'sources' in config")
        return config
    except Exception as e:
        logger.error(f"Config load failed: {e}")
        raise


def get_ioc_hashes(token: str, source: str, limit: int, base_url: str) -> List[Dict]:
    """Fetch file hashes from VT IoC stream by YARA notification_tag."""
    headers = {'x-apikey': token}
    params = {'limit': limit, 'filter': f'notification_tag:"{source}" entity_type:file'}
    resp = requests.get(base_url, headers=headers, params=params, timeout=30)
    resp.raise_for_status()
    iocs = resp.json().get('data', [])
    logger.info(f"Got {len(iocs)} hashes for source '{source}'")
    return iocs


def get_itw_domains(token: str, file_hash: str, base_url: str) -> List[str]:
    """Get contacted domains for file hash."""
    url = base_url.format(file_hash)
    headers = {'x-apikey': token}
    resp = requests.get(url, headers=headers, timeout=30)
    if resp.status_code == 404:
        logger.debug(f"No ITW domains for {file_hash}")
        return []
    resp.raise_for_status()
    domains = [item['id'] for item in resp.json().get('data', [])]
    logger.debug(f"{file_hash}: {len(domains)} domains")
    return domains


def build_csv_content(ioc_data: Dict[str, Dict[str, List[str]]]) -> str:
    """CSV: malware,type,parent_hash,ioc_domain."""
    csv_lines = ["malware,type,parent,ioc"]
    for malware, hash_dict in ioc_data.items():
        for parent_hash, domains in hash_dict.items():
            for domain in domains:
                csv_lines.append(f'"{malware}","domain","{parent_hash}","{domain}"')
    return '\n'.join(csv_lines)


def update_gist(gist_id: str, token: str, filename: str, csv_content: str, base_url: str) -> Dict:
    """Update Gist with CSV content."""
    url = base_url.format(gist_id)
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    data = {'files': {filename: {'content': csv_content}}}
    resp = requests.patch(url, headers=headers, json=data, timeout=30)
    resp.raise_for_status()
    logger.info(f"Gist {gist_id} updated")
    return resp.json()


def main():
    required_env = ['VT_TOKEN', 'GIST_ID', 'GIST_TOKEN', 'VT_IOC_STREAM_URL', 'VT_FILE_ITW_DOMAINS_URL', 'GIST_UPDATE_URL']
    for var in required_env:
        if not os.environ.get(var):
            raise ValueError(f"Missing env var: {var}")

    vt_token = os.environ['VT_TOKEN']
    gist_id = os.environ['GIST_ID']
    gist_token = os.environ['GIST_TOKEN']
    vt_stream_url = os.environ['VT_IOC_STREAM_URL']
    vt_domains_url = os.environ['VT_FILE_ITW_DOMAINS_URL']
    gist_url = os.environ['GIST_UPDATE_URL']

    config = load_config()
    limit = config.get('limit', 20)

    ioc_data = {}

    for src in config['sources']:
        source_name = src if isinstance(src, str) else src.get('name', 'unknown')
        hashes = get_ioc_hashes(vt_token, source_name, limit, vt_stream_url)

        for ioc in hashes:
            hash_id = ioc['id']
            domains = get_itw_domains(vt_token, hash_id, vt_domains_url)
            if domains:
                ioc_data.setdefault(source_name, {}).setdefault(hash_id, set()).update(domains)

    csv_content = build_csv_content(ioc_data)
    update_gist(gist_id, gist_token, 'iocs.csv', csv_content, gist_url)


if __name__ == "__main__":
    main()
