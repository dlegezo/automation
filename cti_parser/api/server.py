#!/usr/bin/env python3
"""Simple CTI API server.

Usage:
    python server.py [port]

Endpoints:
    GET /api/v1/list     Returns full inbound/inbound.json
    GET /api/v1/reports  Returns full outbound/outbound.json
"""

import json
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INBOUND_FILE = os.path.join(BASE_DIR, "inbound", "inbound.json")
OUTBOUND_FILE = os.path.join(BASE_DIR, "outbound", "outbound.json")


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

    def do_GET(self):
        path = urlparse(self.path).path

        if path == "/api/v1/list":
            payload, error = self._load_json(INBOUND_FILE, "inbound/inbound.json")
            if error:
                self._respond_json(error[0], error[1])
                return

            self._respond_json(200, payload)
            return

        if path == "/api/v1/reports":
            outbound, error = self._load_json(OUTBOUND_FILE, "outbound/outbound.json")
            if error:
                self._respond_json(error[0], error[1])
                return

            self._respond_json(200, outbound)
            return

        self._respond_json(404, {"error": "not found"})


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    server = HTTPServer(("127.0.0.1", port), Handler)
    print(f"CTI API server -> http://127.0.0.1:{port}/api/v1/list")
    print(f"CTI API server -> http://127.0.0.1:{port}/api/v1/reports")
    print("Ctrl+C to stop.\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
