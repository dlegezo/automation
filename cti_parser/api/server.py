#!/usr/bin/env python3
"""
Simple local HTTP server for CTI Parser.

Accepts a report URL and creates a skeleton .json in parsed/ that conforms
to iocs-schema.json, ready for manual or automated IOC filling.

Usage:
    python server.py [port]   (default: 8080)

Endpoints:
    GET  /        HTML form
    POST /parse   { url, created? } -> creates parsed/<host>_<date>.json
"""

import json
import os
import re
import sys
from datetime import date
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARSED_DIR = os.path.join(BASE_DIR, "parsed")
SCHEMA_REF = "../schemes/iocs-schema.json"

_DATE_RE = re.compile(r"^(0[1-9]|[12][0-9]|3[01])/(0[1-9]|1[0-2])/[0-9]{4}$")

HTML_FORM = """<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><title>CTI Parser</title>
<style>
  body { font-family: sans-serif; max-width: 640px; margin: 40px auto; }
  input[type=text] { width: 100%; padding: 6px; margin: 6px 0 12px; box-sizing: border-box; }
  button { padding: 8px 20px; cursor: pointer; }
  #result { margin-top: 16px; white-space: pre; background: #f4f4f4; padding: 12px; }
</style>
</head>
<body>
<h2>CTI Report Parser</h2>
<form id="frm">
  <label>Report URL or local file path <em>(required)</em></label>
  <input type="text" name="url" placeholder="https://example.org/report.pdf">
  <label>Report date <em>(DD/MM/YYYY — leave blank for today)</em></label>
  <input type="text" name="created" placeholder="27/03/2026">
  <button type="submit">Create skeleton JSON</button>
</form>
<div id="result"></div>
<script>
document.getElementById("frm").addEventListener("submit", async e => {
  e.preventDefault();
  const data = new URLSearchParams(new FormData(e.target));
  const res  = await fetch("/parse", { method: "POST", body: data });
  const text = await res.text();
  document.getElementById("result").textContent =
    (res.ok ? "Created: " : "Error: ") + text;
});
</script>
</body>
</html>
"""


def _safe_filename(url: str) -> str:
    """Derive a filesystem-safe filename stem from a URL."""
    parsed = urlparse(url)
    host = parsed.netloc or "local"
    host = re.sub(r"[^a-zA-Z0-9._-]", "_", host)
    return f"{host}_{date.today().strftime('%Y%m%d')}.json"


def _unique_path(filename: str) -> str:
    """Return a path that does not already exist, appending _N as needed."""
    path = os.path.join(PARSED_DIR, filename)
    if not os.path.exists(path):
        return path
    base, ext = os.path.splitext(filename)
    counter = 1
    while True:
        path = os.path.join(PARSED_DIR, f"{base}_{counter}{ext}")
        if not os.path.exists(path):
            return path
        counter += 1


def _build_skeleton(url: str, created: str) -> dict:
    return {
        "$schema": SCHEMA_REF,
        "reports": [
            {
                "url": url,
                "created": created,
                "tags": [],
                "iocs": [],
                "ttps": [],
                "queries": [],
                "xrefs": [],
            }
        ],
    }


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print(f"  {self.address_string()}  {fmt % args}")

    def _respond(self, status: int, content_type: str, body: str):
        encoded = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _error(self, status: int, message: str):
        self._respond(status, "application/json",
                      json.dumps({"error": message}, indent=2))

    # ------------------------------------------------------------------
    def do_GET(self):
        if self.path in ("/", ""):
            self._respond(200, "text/html; charset=utf-8", HTML_FORM)
        else:
            self._error(404, "not found")

    def do_POST(self):
        if self.path != "/parse":
            self._error(404, "not found")
            return

        length = int(self.headers.get("Content-Length", 0))
        if length > 8192:
            self._error(413, "request too large")
            return

        raw = self.rfile.read(length).decode("utf-8")
        params = parse_qs(raw)

        url = params.get("url", [""])[0].strip()
        created_raw = params.get("created", [""])[0].strip()

        # --- validate url ---
        if not url:
            self._error(400, "url is required")
            return
        scheme = urlparse(url).scheme
        if scheme not in ("http", "https", "file", ""):
            self._error(400, "url scheme must be http, https, or a local file path")
            return

        # --- validate / default created date ---
        if created_raw:
            if not _DATE_RE.match(created_raw):
                self._error(400, "created must be DD/MM/YYYY")
                return
            created = created_raw
        else:
            created = date.today().strftime("%d/%m/%Y")

        # --- write skeleton ---
        os.makedirs(PARSED_DIR, exist_ok=True)
        out_path = _unique_path(_safe_filename(url))
        with open(out_path, "w", encoding="utf-8") as fh:
            json.dump(_build_skeleton(url, created), fh, indent=2)

        rel = os.path.relpath(out_path, BASE_DIR).replace("\\", "/")
        self._respond(
            201,
            "application/json",
            json.dumps({"status": "created", "file": rel,
                        "url": url, "created": created}, indent=2),
        )


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    server = HTTPServer(("127.0.0.1", port), Handler)
    print(f"CTI Parser server  →  http://127.0.0.1:{port}/")
    print(f"Output directory   →  {PARSED_DIR}")
    print("Ctrl+C to stop.\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
