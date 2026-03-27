#!/usr/bin/env python3
"""Simple CTI API server.

Usage:
    python server.py [port]

Endpoints:
    GET /api/v1/list   Returns only report names from inbound/inbound.json
    GET /api/v1/reports
                      Returns full outbound/outbound.json (unfiltered)
    GET /api/v1/reports/{property}/{enum?}
                      Returns corresponding values from outbound/outbound.json
"""

import json
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INBOUND_FILE = os.path.join(BASE_DIR, "inbound", "inbound.json")
OUTBOUND_FILE = os.path.join(BASE_DIR, "outbound", "outbound.json")
SCHEMA_FILE = os.path.join(BASE_DIR, "schemes", "iocs-schema.json")


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print(f"  {self.address_string()}  {fmt % args}")

    def _respond_json(self, status: int, payload: dict):
        body = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _load_json(self, file_path: str, label: str):
        if not os.path.exists(file_path):
            return None, (404, {"error": f"{label} not found"})
        try:
            with open(file_path, "r", encoding="utf-8") as fh:
                return json.load(fh), None
        except json.JSONDecodeError:
            return None, (500, {"error": f"{label} is not valid JSON"})
        except OSError:
            return None, (500, {"error": f"failed to read {label}"})

    def _schema_report_properties(self):
        schema, error = self._load_json(SCHEMA_FILE, "schemes/iocs-schema.json")
        if error:
            return None, error

        try:
            properties = schema["reports"]["items"]["properties"]
        except (TypeError, KeyError):
            return None, (500, {"error": "iocs-schema.json has invalid reports schema format"})

        if not isinstance(properties, dict):
            return None, (500, {"error": "iocs-schema.json reports properties must be an object"})
        return properties, None

    def _enum_descriptor_for_property(self, prop_schema: dict):
        if not isinstance(prop_schema, dict):
            return None

        # direct enum, ex: {"type": "string", "enum": [...]}
        direct_enum = prop_schema.get("enum")
        if isinstance(direct_enum, list) and all(isinstance(v, str) for v in direct_enum):
            return {"mode": "direct", "values": set(direct_enum)}

        # array of objects with enum sub-property, ex: queries[].type, iocs[].type
        items = prop_schema.get("items")
        if not isinstance(items, dict):
            return None

        item_props = items.get("properties")
        if not isinstance(item_props, dict):
            return None

        for field_name, field_schema in item_props.items():
            enum_values = field_schema.get("enum") if isinstance(field_schema, dict) else None
            if isinstance(enum_values, list) and all(isinstance(v, str) for v in enum_values):
                return {
                    "mode": "item_field",
                    "field": field_name,
                    "values": set(enum_values),
                }

        return None

    def do_GET(self):
        path = urlparse(self.path).path

        if path == "/api/v1/list":
            payload, error = self._load_json(INBOUND_FILE, "inbound/inbound.json")
            if error:
                self._respond_json(error[0], error[1])
                return

            source = payload.get("source")
            if not isinstance(source, list):
                self._respond_json(500, {"error": "inbound/inbound.json has invalid 'source' format"})
                return

            names = [item.get("name") for item in source if isinstance(item, dict) and item.get("name")]
            self._respond_json(200, {"names": names})
            return

        if path.startswith("/api/v1/reports"):
            parts = [p for p in path.split("/") if p]
            # Expected forms:
            # /api/v1/reports
            # /api/v1/reports/{property}
            # /api/v1/reports/{property}/{enum_value}
            if len(parts) not in (3, 4, 5):
                self._respond_json(404, {"error": "not found"})
                return

            prop_name = parts[3] if len(parts) >= 4 else None
            enum_value = parts[4] if len(parts) == 5 else None

            outbound, error = self._load_json(OUTBOUND_FILE, "outbound/outbound.json")
            if error:
                self._respond_json(error[0], error[1])
                return

            if prop_name is None:
                self._respond_json(200, outbound)
                return

            properties, error = self._schema_report_properties()
            if error:
                self._respond_json(error[0], error[1])
                return

            if prop_name not in properties:
                self._respond_json(
                    400,
                    {
                        "error": "unknown report property",
                        "property": prop_name,
                        "allowed": sorted(properties.keys()),
                    },
                )
                return

            reports = outbound.get("reports") if isinstance(outbound, dict) else None
            if not isinstance(reports, list):
                self._respond_json(500, {"error": "outbound/outbound.json has invalid 'reports' format"})
                return

            prop_schema = properties[prop_name]
            enum_descriptor = self._enum_descriptor_for_property(prop_schema)
            if enum_value and not enum_descriptor:
                self._respond_json(
                    400,
                    {
                        "error": "property is not enum-based",
                        "property": prop_name,
                    },
                )
                return

            if enum_value and enum_value not in enum_descriptor["values"]:
                self._respond_json(
                    400,
                    {
                        "error": "unsupported enum value",
                        "property": prop_name,
                        "enum_value": enum_value,
                        "allowed": sorted(enum_descriptor["values"]),
                    },
                )
                return

            values = []
            for report in reports:
                if not isinstance(report, dict) or prop_name not in report:
                    continue

                report_value = report[prop_name]

                if not enum_descriptor:
                    values.append(report_value)
                    continue

                if enum_descriptor["mode"] == "direct":
                    if enum_value is None or report_value == enum_value:
                        values.append(report_value)
                    continue

                if enum_descriptor["mode"] == "item_field" and isinstance(report_value, list):
                    enum_field = enum_descriptor["field"]
                    for item in report_value:
                        if not isinstance(item, dict):
                            continue
                        if enum_value is None or item.get(enum_field) == enum_value:
                            values.append(item)

            response = {
                "property": prop_name,
                "count": len(values),
                "values": values,
            }
            if enum_descriptor:
                response["enum_field"] = enum_descriptor.get("field")
            if enum_value is not None:
                response["enum_value"] = enum_value

            self._respond_json(200, response)
            return

        self._respond_json(404, {"error": "not found"})


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    server = HTTPServer(("127.0.0.1", port), Handler)
    print(f"CTI API server -> http://127.0.0.1:{port}/api/v1/reports")
    print("Ctrl+C to stop.\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
