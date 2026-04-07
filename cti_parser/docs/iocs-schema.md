# IOCs Schema Documentation

This document describes the JSON schema defined in `cti_parser/schemes/iocs-schema.json`.

## Overview

The schema defines parsed CTI reports with:

- report metadata envelope (`metadata`)
- indicators (`iocs`)
- vulnerabilities (`vulns`)
- techniques (`ttps`)
- detection logic (`queries`)
- graph-style relationships (`xrefs` with directional `from` and `to` edges)

Schema metadata:

- `$schema`: `https://json-schema.org/draft/2020-12/schema`
- `$id`: `iocs-schema.json`
- `description`: `Parsed CTI reports`

## Top-Level Structure

| Property | Type | Required | Description |
|---|---|---|---|
| `reports` | array | Yes | List of parsed CTI report objects. |

## `reports` Items

Required fields: `metadata`, `iocs`, `ttps`

| Field | Type | Required | Description |
|---|---|---|---|
| `metadata` | object | Yes | Report metadata object with source and triage context. |
| `iocs` | array | Yes | IOC objects. |
| `vulns` | array | No | Vulnerability objects. |
| `ttps` | array | Yes | TTP objects. |
| `queries` | array | No | Query objects. |
| `xrefs` | array | No | Cross-reference objects. |

## `metadata` Object

Required fields: `url`, `created`, `severity`, `confidence`, `tags`, `actor`

| Field | Type | Required | Constraints | Description |
|---|---|---|---|---|
| `url` | string | Yes | format: `uri` | URL of source CTI report, web or local file path. |
| `created` | string | Yes | pattern: `^(0[1-9]|[12][0-9]|3[01])/(0[1-9]|1[0-2])/([0-9]{4})$` | Date in `DD/MM/YYYY` format. |
| `severity` | number | Yes | range: `0..1` | Jaccard similarity share of common tags between report tags and inbound `tags_of_interest`. |
| `confidence` | string | Yes | enum: `low`, `medium`, `high` | Analyst confidence in extracted report intelligence. |
| `tags` | string[] | Yes | none | Labels associated with the report. |
| `actor` | string | Yes | pattern: `^G[0-9]{4}$` | Threat actor in MITRE ATT&CK group format (G####), for example `G0007`. |

## `iocs` Items

Required fields: `id`, `type`, `malign`, `value`

| Field | Type | Required | Constraints | Description |
|---|---|---|---|---|
| `id` | string | Yes | pattern: `^ioc-[0-9]+$` | IOC identifier. |
| `type` | string | Yes | enum: `ip`, `domain`, `url`, `email`, `filename`, `filepath`, `process`, `cmdline`, `regkey`, `mutex`, `pipe`, `service`, `cert` | IOC kind. |
| `malign` | boolean | Yes | none | `true` for malicious/detectable, `false` for benign/informational. |
| `hash` | string | No | enum: `sha1`, `sha256`, `md5` | Hash type for `type = file`. |
| `cert_serial` | string | No | allowed only for `file`, `domain`, `ip` | Certificate serial number for code-signing or TLS/SSL context. |
| `value` | string | Yes | none | IOC value. |
| `comment` | string | No | none | Analyst context. |

Notes:

- `hash` can be used to indicate hash algorithm metadata for file-related indicators.
- `malign` is required in schema for every IOC entry.

## `vulns` Items

Required fields: `id`, `comment`

| Field | Type | Required | Constraints | Description |
|---|---|---|---|---|
| `id` | string | Yes | pattern: `^CVE-[0-9]{4}-[0-9]{4,}$` | Vulnerability CVE identifier. |
| `comment` | string | Yes | none | Context for how the vulnerability is used or referenced. |

## `ttps` Items

Required fields: `id`, `comment`

| Field | Type | Required | Constraints | Description |
|---|---|---|---|---|
| `id` | string | Yes | pattern: `^T[0-9]{4}(\.[0-9]{3})?$` | MITRE ATT&CK technique ID. |
| `comment` | string | Yes | none | Context for the technique usage. |

## `queries` Items

Required fields: `id`, `type`, `value`

| Field | Type | Required | Constraints | Description |
|---|---|---|---|---|
| `id` | string | Yes | pattern: `^query-[0-9]+$` | Query identifier. |
| `type` | string | Yes | enum: `kql`, `yara`, `spl`, `sigma`, `sql` | Query language/type. |
| `value` | string | Yes | none | Query content. |
| `comment` | string | No | none | Analyst context. |

## `xrefs` Items

Required fields: `id`, `type`

| Field | Type | Required | Constraints | Description |
|---|---|---|---|---|
| `id` | string | Yes | pattern: `^xref-[0-9]+$` | Cross-reference identifier. |
| `type` | string | Yes | enum: `creates`, `uses`, `follows` | Relationship type. |
| `from` | string[] | No | none | Source entities in the relationship. |
| `to` | string[] | No | none | Target entities in the relationship. |
| `comment` | string | No | none | Extra relationship context. |

Notes:

- Keep direct query-to-IOC coverage in `queries[].iocs`.
- Use `xrefs` for directional graph edges that need explicit relationship semantics.

## Mermaid Diagram

Source diagram: [../diagrams/iocs-schema.mmd](../diagrams/iocs-schema.mmd)

## Example Valid Document

```json
{
  "reports": [
    {
      "metadata": {
        "url": "https://example.org/reports/cti-001",
        "created": "27/03/2026",
        "severity": 0.4286,
        "confidence": "medium",
        "tags": ["apt", "phishing"],
        "actor": "G0007"
      },
      "iocs": [
        {
          "id": "ioc-1",
          "type": "filename",
          "malign": true,
          "hash": "sha256",
          "cert_serial": "12A34BCD56",
          "value": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
          "comment": "Malware dropper"
        },
        {
          "id": "ioc-2",
          "type": "email",
          "malign": true,
          "value": "operator@malicious.example.com"
        }
      ],
      "vulns": [
        {
          "id": "CVE-2026-21509",
          "comment": "Client-side exploit used in this campaign"
        }
      ],
      "ttps": [
        {
          "id": "T1203",
          "comment": "T1203 exploitation observed"
        }
      ],
      "queries": [
        {
          "id": "query-1",
          "type": "kql",
          "value": "DeviceFileEvents | where SHA256 == 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'",
          "comment": "Hunt for known sample"
        }
      ],
      "xrefs": [
        {
          "id": "xref-1",
          "type": "uses",
          "from": ["ioc-1"],
          "to": ["T1203"],
          "comment": "This malware sample is linked to exploitation technique T1203"
        }
      ]
    }
  ]
}
```

## Validation Notes

- `metadata.created` must strictly match `DD/MM/YYYY`.
- `metadata.severity` must be a number from `0` to `1`.
- `metadata.confidence` accepts only: `low`, `medium`, `high`.
- `metadata.tags` and `metadata.actor` are required.
- `metadata.actor` must match `^G[0-9]{4}$`.
- `iocs[].type` accepts only: `ip`, `domain`, `url`, `email`, `filename`, `filepath`, `process`, `cmdline`, `regkey`, `mutex`, `pipe`, `service`, `cert`.
- `iocs[].malign` is required on every IOC entry.
- `iocs[].hash` accepts only: `sha1`, `sha256`, `md5`.
- `vulns[].id` must match `CVE-YYYY-NNNN` style format.
- `xrefs[].type` accepts only: `creates`, `uses`, `follows`.
- `xrefs[].from` and `xrefs[].to` define directional edges between entities.
- `queries[].type` accepts only: `kql`, `yara`, `spl`, `sigma`, `sql`.
