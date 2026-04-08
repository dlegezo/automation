import requests
import clickhouse_connect
from datetime import datetime

ATTACK_URL = 'https://raw.githubusercontent.com/mitre-attack/attack-stix-data/master/enterprise-attack/enterprise-attack.json'
CLICKHOUSE_HOST = 'localhost'
CLICKHOUSE_PORT = 8123
CLICKHOUSE_USER = 'default'
CLICKHOUSE_PASSWORD = 'default'
CLICKHOUSE_DATABASE = 'default'


def parse_modified(value: str) -> datetime:
    if not value:
        return datetime(1970, 1, 1, 0, 0, 0)
    value = value.replace('Z', '+00:00')
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is not None:
        dt = dt.replace(tzinfo=None)
    return dt.replace(microsecond=0)


resp = requests.get(ATTACK_URL, timeout=60)
resp.raise_for_status()
data = resp.json()
objects = data.get('objects', [])

sub_to_parent = {}
for obj in objects:
    if obj.get('type') == 'relationship' and obj.get('relationship_type') == 'subtechnique-of':
        sub_to_parent[obj.get('source_ref')] = obj.get('target_ref')

stix_to_attack = {}
for obj in objects:
    if obj.get('type') == 'attack-pattern':
        for ref in obj.get('external_references', []):
            if ref.get('source_name') == 'mitre-attack' and ref.get('external_id'):
                stix_to_attack[obj['id']] = ref['external_id']
                break

rows = []
for obj in objects:
    if obj.get('type') != 'attack-pattern':
        continue

    attack_id = stix_to_attack.get(obj.get('id'))
    if not attack_id:
        continue

    tactics = [
        phase.get('phase_name')
        for phase in obj.get('kill_chain_phases', [])
        if phase.get('kill_chain_name') == 'mitre-attack' and phase.get('phase_name')
    ]

    parent_attack_id = None
    parent_stix = sub_to_parent.get(obj.get('id'))
    if parent_stix:
        parent_attack_id = stix_to_attack.get(parent_stix)

    rows.append([
        attack_id,
        obj.get('id'),
        obj.get('name', ''),
        1 if obj.get('x_mitre_is_subtechnique') else 0,
        parent_attack_id,
        tactics,
        obj.get('x_mitre_platforms', []),
        obj.get('description', ''),
        1 if obj.get('revoked') else 0,
        1 if obj.get('x_mitre_deprecated') else 0,
        parse_modified(obj.get('modified')),
    ])

client = clickhouse_connect.get_client(
    host=CLICKHOUSE_HOST,
    port=CLICKHOUSE_PORT,
    username=CLICKHOUSE_USER,
    password=CLICKHOUSE_PASSWORD,
    database=CLICKHOUSE_DATABASE,
)

client.command('''
CREATE TABLE IF NOT EXISTS dim_mitre_technique
(
    attack_id LowCardinality(String),
    stix_id String,
    name String,
    is_subtechnique UInt8,
    parent_attack_id Nullable(String),
    tactics Array(LowCardinality(String)),
    platforms Array(LowCardinality(String)),
    description String,
    revoked UInt8,
    deprecated UInt8,
    modified_at DateTime
)
ENGINE = ReplacingMergeTree(modified_at)
ORDER BY attack_id
''')

client.insert(
    'dim_mitre_technique',
    rows,
    column_names=[
        'attack_id',
        'stix_id',
        'name',
        'is_subtechnique',
        'parent_attack_id',
        'tactics',
        'platforms',
        'description',
        'revoked',
        'deprecated',
        'modified_at',
    ],
)

print(f'Inserted {len(rows)} ATT&CK techniques/sub-techniques into dim_mitre_technique')
