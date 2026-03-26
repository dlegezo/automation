import requests
import os
from typing import Dict, List, Set


class Vt_Ioc_Stream:
    def __init__(self, config: Dict):
        self.token = os.environ[config['token_env']]
        self.stream_url = os.environ[config['ioc_url_env']]
        self.domains_url = os.environ[config['domains_url_env']]

    def get_iocs(self, yara_rule: str, limit: int = 20) -> Dict[str, Set[str]]:
        headers = {'x-apikey': self.token}
        params = {'limit': limit, 'filter': f'notification_tag:"{yara_rule}"'}

        resp = requests.get(self.stream_url, headers=headers, params=params, timeout=30)
        resp.raise_for_status()
        iocs = resp.json().get('data', [])

        iocs_enriched = {}
        for ioc in iocs:
            ioc_id = ioc['id']
            domains = self._get_domains(ioc_id)
            if domains:
                iocs_enriched[ioc_id] = domains

        return iocs_enriched

    def _get_domains(self, file_hash: str) -> List[Dict[str, str]]:
        url = self.domains_url.format(file_hash)
        headers = {'x-apikey': self.token}
        resp = requests.get(url, headers=headers, timeout=30)
        if resp.status_code == 404:
            return []
        resp.raise_for_status()
        return {item['id']: item['attributes']['creation_date'] for item in resp.json().get('data', [])}
