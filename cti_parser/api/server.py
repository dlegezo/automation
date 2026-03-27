#!/usr/bin/env python3
"""Simple CTI API server.

Usage:
    python server.py [port]

Endpoints:
    GET /api/v1/list   Returns inbound/inbound.json
"""

import json
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INBOUND_FILE = os.path.join(BASE_DIR, "inbound", "inbound.json")


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

    def do_GET(self):
        path = urlparse(self.path).path

        if path == "/api/v1/list":
            if not os.path.exists(INBOUND_FILE):
                self._respond_json(404, {"error": "inbound/inbound.json not found"})
                return

            try:
                with open(INBOUND_FILE, "r", encoding="utf-8") as fh:
                    payload = json.load(fh)
            except json.JSONDecodeError:
                self._respond_json(500, {"error": "inbound/inbound.json is not valid JSON"})
                return
            except OSError:
                self._respond_json(500, {"error": "failed to read inbound/inbound.json"})
                return

            self._respond_json(200, payload)
            return

        self._respond_json(404, {"error": "not found"})


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    server = HTTPServer(("127.0.0.1", port), Handler)
    print(f"CTI API server -> http://127.0.0.1:{port}/api/v1/list")
    print("Ctrl+C to stop.\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
