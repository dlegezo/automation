import requests
import os
from typing import Dict


class Gist_To_Check:
    def __init__(self, config: Dict):
        self.gist_id = os.environ[config['gist_id_env']]
        self.token = os.environ[config['token_env']]
        self.base_url = os.environ[config['url_env']]
        self.filename = config['filename']

    def get_iocs(self, ioc_store: Dict) -> Dict:
        # from utils import build_csv_content

        headers = {
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        gist_url = self.base_url.format(self.gist_id)
        resp = requests.get(gist_url, headers=headers, timeout=30)
        resp.raise_for_status()

        gist_data = resp.json()

        if self.filename not in gist_data["files"]:
            raise FileNotFoundError(f"File '{self.filename}' not found in Gist {self.gist_id}")

        file_url = gist_data["files"][self.filename]["raw_url"]

        file_resp = requests.get(file_url)
        file_resp.raise_for_status()
        return file_resp.content.decode('utf-8')
