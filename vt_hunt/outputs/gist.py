import requests
import os
from typing import Dict


class Gist:
    def __init__(self, config: Dict):
        self.gist_id = os.environ[config['gist_id_env']]
        self.token = os.environ[config['token_env']]
        self.base_url = os.environ[config['url_env']]
        self.filename = config['filename']

    def store(self, ioc_store: Dict) -> Dict:
        """Store ioc_store as CSV in Gist."""
        from utils import build_csv_content
        csv_content = build_csv_content(ioc_store)

        url = self.base_url.format(self.gist_id)
        headers = {
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        data = {'files': {self.filename: {'content': csv_content}}}

        resp = requests.patch(url, headers=headers, json=data, timeout=30)
        resp.raise_for_status()
        return resp.json()
