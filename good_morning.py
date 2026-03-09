import os
import requests
import json


def get_virustotal_ioc_stream(token: str, source: str) -> list:
    headers = {'x-apikey': token}
    params = {'limit': 40} # max available is 40
    resp = requests.get(os.environ['VT_IOC_STREAM_URL'], headers=headers, params=params)
    resp.raise_for_status()
    data = resp.json()['data']
    iocs = []
    for ioc in data:
        if source in ioc.get('context_attributes').get('tags'):
            iocs.append(ioc)
    return iocs


def get_file_contacted_domains(token: str, file_hash: str) -> list[str]:
    url = os.environ['VT_FILE_ITW_DOMAINS_URL'].format(file_hash)
    headers = {'x-apikey': token}
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        domain_data = resp.json().get('data', [])
        return [entry['id'] for entry in domain_data]
    print(f"Error {resp.status_code} for {file_hash}")
    return []


def update_gist(gist_id: str, token: str, filename: str, iocs: set, type:str, malware: str) -> dict:
    csv_content = "malware, type, ioc\n" + "\n".join(
        f"{malware}, {type}, {ioc}" for ioc in iocs
    )
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

    ioc_hashes = get_virustotal_ioc_stream(vt_token, 'ios_coruna_gti')
    ioc_domains = set()
    for ioc in ioc_hashes:
        for domain in get_file_contacted_domains(vt_token, ioc['id']):
            ioc_domains.add(domain)
    update_gist(gist_id, gist_token, 'iocs.csv', ioc_domains, 'domain', 'coruna')


if __name__ == "__main__":
    main()
