import os
import requests
import json
from typing import Dict, List


def get_virustotal_ioc_stream(token: str, source: str) -> List[Dict]:
    headers = {'x-apikey': token}
    params = {'limit': 15,  # max available is 40
              'filter': f'notification_tag:"{source}"'}
    resp = requests.get(os.environ['VT_IOC_STREAM_URL'], headers=headers, params=params)
    resp.raise_for_status()
    data = resp.json()['data']
    iocs = list({ioc['id']: ioc for ioc in data}.values())
    return iocs


def get_file_contacted_domains(token: str, file_hash: str) -> Dict[str, List[str]]:
    url = os.environ['VT_FILE_ITW_DOMAINS_URL'].format(file_hash)
    headers = {'x-apikey': token}
    resp = requests.get(url, headers=headers)
    res = []
    if resp.status_code == 200:
        domain_data = resp.json().get('data', [])
        for entry in domain_data:
            res.append(entry['id'])
    else:
        print(f"Error {resp.status_code} for {file_hash}")
        return {}
    return {file_hash: res}


def update_gist(gist_id: str, token: str, filename: str, iocs: Dict[str, List[str]], type: str, malware: str) -> Dict:
    csv_content = "malware, type, parent, ioc\n"
    for parent, ioc_list in iocs.items():
        for ioc in ioc_list:
            csv_content += f"{malware}, {type}, {parent}, {ioc}\n"
    url = os.environ['GIST_UPDATE_URL'].format(gist_id)
    headers = {'Authorization': f'token {token}'}
    data = {
        'files': {
            filename: {
                'content': csv_content
            }
        }
    }
    resp = requests.patch(url, headers=headers, data=json.dumps(data))
    resp.raise_for_status()
    return resp.json()


def main():
    vt_token = os.environ['VT_TOKEN']
    gist_id = os.environ['GIST_ID']
    gist_token = os.environ['GIST_TOKEN']
    with open('config.json', 'r') as f:
        config = json.load(f)

    ioc_hashes = get_virustotal_ioc_stream(vt_token, config['source'])
    ioc_domains = {}
    for ioc in ioc_hashes:
        contacted = get_file_contacted_domains(vt_token, ioc['id'])
        ioc_domains.update(contacted)
    update_gist(gist_id, gist_token, 'iocs.csv', ioc_domains, 'domain', 'coruna')


if __name__ == "__main__":
    main()
