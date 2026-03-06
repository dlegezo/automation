import requests
import json
import auth


def get_virustotal_ioc_stream(token: str) -> list:
    headers = {'x-apikey': token}
    resp = requests.get(auth.VT_IOC_STREAM_URL, headers=headers)
    resp.raise_for_status()
    return resp.json()['data']


def get_file_contacted_domains(token, file_hash: str) -> list[str]:
    url = auth.VT_FILE_ITW_DOMAINS_URL.format(file_hash)
    headers = {'x-apikey': token}
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        domain_data = resp.json().get('data', [])
        return [entry['id'] for entry in domain_data]
    print(f"Error {resp.status_code} for {file_hash}")
    return []


def update_gist(gist_id, filename, content, token):
    url = auth.GIST_UPDATE_URL.format(gist_id)
    headers = {'Authorization': f'token {token}'}
    data = {
        'files': {
            filename: {
                'content': content
            }
        }
    }
    resp = requests.patch(url, headers=headers, data=json.dumps(data))
    resp.raise_for_status()
    return resp.json()


def main():
    ioc_hashes = get_virustotal_ioc_stream(auth.VT_TOKEN)
    ioc_domains = set()

    for ioc in ioc_hashes:
        for domain in get_file_contacted_domains(auth.VT_TOKEN, ioc['id']):
            ioc_domains.add(domain)
    csv_content = "malware,ioc\n" + "\n".join(
        f"coruna,{domain}" for domain in ioc_domains
    )
    update_gist(auth.GIST_ID, 'iocs.csv', csv_content, auth.GIST_TOKEN)


if __name__ == "__main__":
    main()
