# CTI Parser API Documentation

This document describes the HTTP endpoints implemented in `cti_parser/api/server.py`.

## Overview

Base URL (default): `http://127.0.0.1:8080`

Data sources used by the API:

- `cti_parser/inbound/inbound.json`
- `cti_parser/outbound/outbound.json`
- `cti_parser/schemes/iocs-schema.json`

## Endpoint: `GET /api/v1/list`

Returns only report names from `inbound/inbound.json`.

### Success Response

Status: `200 OK`

```json
{
  "names": [
    "sednit-reloaded-back-trenches",
    "handala-hack-unveiling-groups-modus-operandi"
  ]
}
```

### Errors

- `404`: `inbound/inbound.json not found`
- `500`: invalid JSON or unreadable file

## Endpoint: `GET /api/v1/reports`

Returns full unfiltered content of `outbound/outbound.json`.

### Example Request

- `GET /api/v1/reports`

## Endpoint: `GET /api/v1/reports/{property}`

Returns values of a top-level `reports` property from `outbound/outbound.json`.

`{property}` must exist in `reports.items.properties` in `iocs-schema.json`.

### Example Requests

- `GET /api/v1/reports/url`
- `GET /api/v1/reports/queries`
- `GET /api/v1/reports/iocs`
- `GET /api/v1/reports/xrefs`

### Success Response (example)

```json
{
  "property": "url",
  "count": 2,
  "values": [
    "https://www.welivesecurity.com/en/eset-research/sednit-reloaded-back-trenches/",
    "https://research.checkpoint.com/2026/handala-hack-unveiling-groups-modus-operandi/"
  ]
}
```

## Endpoint: `GET /api/v1/reports/{property}/{enum_value}`

Filters enum-based properties using enum values from `iocs-schema.json`.

Supported for properties that are enum-based, including arrays of objects with an enum field (for example `iocs[].type`, `queries[].type`, `xrefs[].type`).

### Example Requests

- `GET /api/v1/reports/queries/kql`
- `GET /api/v1/reports/queries/yara`
- `GET /api/v1/reports/iocs/ip`
- `GET /api/v1/reports/iocs/sha1`
- `GET /api/v1/reports/xrefs/created_by`

### Success Response (example)

```json
{
  "property": "queries",
  "enum_field": "type",
  "enum_value": "kql",
  "count": 3,
  "values": [
    {
      "id": "query-1",
      "type": "kql",
      "value": "..."
    }
  ]
}
```

## Common Error Responses

### Unknown Property

Status: `400 Bad Request`

```json
{
  "error": "unknown report property",
  "property": "unknown_prop",
  "allowed": ["created", "iocs", "queries", "tags", "ttps", "url", "xrefs"]
}
```

### Property Is Not Enum-Based

Status: `400 Bad Request`

```json
{
  "error": "property is not enum-based",
  "property": "url"
}
```

### Unsupported Enum Value

Status: `400 Bad Request`

```json
{
  "error": "unsupported enum value",
  "property": "queries",
  "enum_value": "lucene",
  "allowed": ["kql", "sigma", "spl", "sql", "yara"]
}
```

### Not Found

Status: `404 Not Found`

```json
{
  "error": "not found"
}
```

## Run Server

From workspace root:

```bash
python cti_parser/api/server.py
```

Then test, for example:

```bash
curl http://127.0.0.1:8080/api/v1/list
curl http://127.0.0.1:8080/api/v1/reports
curl http://127.0.0.1:8080/api/v1/reports/queries/kql
```
