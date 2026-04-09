import requests
import os
import json

api_key = os.getenv("TLPBLACK_TOKEN")
username = os.getenv("TLPBLACK_USER")
password = os.getenv("TLPBLACK_PASS")

ioc = {
  "indicator": ["clientepj.com", "aliempregoraiz.site"],
  "max_rows": 10
}
pdns = {
  "ip": ["18.139.9.214"],
  "domain": [],
  "tag": [],
  "max_rows": 10
}

tlpblack_url = 'https://app.tlpblack.net/api/'
nightfall_url = f'{tlpblack_url}nightfall/v1/world_data_get'
yaraql_url = f'{tlpblack_url}yaraql/v1/task_new'
iocs_url = f'{tlpblack_url}iocs/v1/search'
pdns_url = f'{tlpblack_url}pdns/v1/search'

headers = {'Content-Type': 'application/json', 'X-API-Key': api_key}

response = requests.post(iocs_url, headers=headers, json=ioc, auth=(username, password))

if response.status_code == 200:
    print(json.dumps(response.json(), indent=2))
else:
    print(f'Error: {response.status_code}, {json.dumps(response.json(), indent=2)}')
