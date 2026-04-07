# CTI Parser API Documentation

This document describes the HTTP endpoints implemented in `cti_parser/api/server.py`.

## Overview

Base URL (default): `http://127.0.0.1:8080`

Data sources used by the API:

- `cti_parser/inbound/inbound.json`
- `cti_parser/outbound/*.json` (per-report files)

## Endpoint: `GET /api/v1/list`

Returns full unfiltered content of `inbound/inbound.json`.

### Success Response

Status: `200 OK`

Response body: exact contents of `inbound/inbound.json`.

Schema reference: `cti_parser/schemes/pipeline-schema.json`

## Endpoint: `GET /api/v1/reports`

Returns aggregated report objects from all JSON files in `outbound/`.

### Success Response

Status: `200 OK`

Response body shape:

```json
{
  "$schema": "../schemes/iocs-schema.json",
  "$id": "iocs.json",
  "reports": [
    { "metadata": { }, "iocs": [], "ttps": [] }
  ]
}
```

Schema reference: `cti_parser/schemes/iocs-schema.json`

## Error Responses

### File Not Found

Status: `404 Not Found`

```json
{
  "error": "inbound/inbound.json not found"
}
```

or

```json
{
  "error": "outbound directory not found"
}
```

### Invalid JSON or Read Failure

Status: `500 Internal Server Error`

```json
{ "error": "outbound/<file>.json is not valid JSON" }
```

or

```json
{
  "error": "failed to read inbound/inbound.json"
}
```

### Unknown Route

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

Test endpoints:

```bash
curl http://127.0.0.1:8080/api/v1/list
curl http://127.0.0.1:8080/api/v1/reports
```

