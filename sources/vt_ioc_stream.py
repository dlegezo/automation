import requests
import os
from typing import Dict, List, Set

class Vt_Ioc_Stream:
    def __init__(self, config: Dict):
        self.token = os.environ[config['token_env']]
        self.stream_url = os.environ[config['ioc_url_env']]
        self.domains_url = os.environ[config['domains_url_env']]
    
    def load_iocs(self, yara_rule: str, limit: int = 20) -> Dict[str, Set[str]]:
        headers = {'x-apikey': self.token}
        params = {'limit': limit, 'filter': f'notification_tag:"{yara_rule}" entity_type:file'}
        
        resp = requests.get(self.stream_url, headers=headers, params=params, timeout=30)
        resp.raise_for_status()
        hashes = resp.json().get('data', [])
        
        hash_domains = {}
        for ioc in hashes:
            hash_id = ioc['id']
            domains = self._get_domains(hash_id)
            if domains:
                hash_domains[hash_id] = set(domains)
        
        return hash_domains
    
    def _get_domains(self, file_hash: str) -> List[str]:
        url = self.domains_url.format(file_hash)
        headers = {'x-apikey': self.token}
        resp = requests.get(url, headers=headers, timeout=30)
        if resp.status_code == 404:
            return []
        resp.raise_for_status()
        return [item['id'] for item in resp.json().get('data', [])]
