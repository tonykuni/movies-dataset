"""Host-neutral VUSIPE adapters: Python call, JSONL stdin/stdout, and HTTP JSON."""

from __future__ import annotations

# PARAMETERS
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
DEFAULT_RUNTIME_DIR = "vusipe_runtime"
MAX_REQUEST_BYTES = 4_000_000

import argparse
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Mapping, Sequence

from VUSIPE import UniversalSemanticPlugin, create_plugin


class GenericModuleAdapter:
    """Minimal interface any Python host can wrap without VIA dependencies."""

    def __init__(self, runtime_dir: str | Path = DEFAULT_RUNTIME_DIR):
        self.plugin = create_plugin(runtime_dir)

    def invoke(self, action: str, payload: Mapping[str, Any]) -> dict[str, Any]:
        return self.plugin.invoke({"action": action, "payload": dict(payload)})

    def close(self) -> None:
        self.plugin.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        self.close()


def run_jsonl(runtime_dir: str | Path = DEFAULT_RUNTIME_DIR) -> int:
    plugin = UniversalSemanticPlugin(runtime_dir)
    try:
        for line in sys.stdin:
            try:
                request = json.loads(line)
                response = plugin.invoke(request)
            except Exception as exc:
                response = {"gate": "FAIL", "error": type(exc).__name__, "message": str(exc)}
            print(json.dumps(response, ensure_ascii=False, sort_keys=True), flush=True)
    finally:
        plugin.close()
    return 0


def make_handler(plugin: UniversalSemanticPlugin):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/health":
                self._send(plugin.invoke({"action": "health", "payload": {}}))
            elif self.path == "/capabilities":
                self._send(plugin.invoke({"action": "capabilities", "payload": {}}))
            else:
                self._send({"gate": "FAIL", "error": "NOT_FOUND"}, 404)

        def do_POST(self):
            if self.path != "/invoke":
                self._send({"gate": "FAIL", "error": "NOT_FOUND"}, 404)
                return
            size = int(self.headers.get("Content-Length", "0"))
            if size <= 0 or size > MAX_REQUEST_BYTES:
                self._send({"gate": "FAIL", "error": "INVALID_REQUEST_SIZE"}, 413)
                return
            try:
                request = json.loads(self.rfile.read(size))
                self._send(plugin.invoke(request))
            except Exception as exc:
                self._send({"gate": "FAIL", "error": type(exc).__name__, "message": str(exc)}, 400)

        def _send(self, payload: Mapping[str, Any], status: int = 200):
            raw = json.dumps(dict(payload), ensure_ascii=False, sort_keys=True).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def log_message(self, format, *args):
            return

    return Handler


def run_http(runtime_dir: str | Path, host: str, port: int) -> int:
    plugin = UniversalSemanticPlugin(runtime_dir)
    server = ThreadingHTTPServer((host, port), make_handler(plugin))
    try:
        server.serve_forever()
    finally:
        server.server_close()
        plugin.close()
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="VUSIPE host-neutral adapters")
    parser.add_argument("mode", choices=("jsonl", "http"))
    parser.add_argument("--runtime-dir", default=DEFAULT_RUNTIME_DIR)
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return run_jsonl(args.runtime_dir) if args.mode == "jsonl" else run_http(args.runtime_dir, args.host, args.port)


if __name__ == "__main__":
    raise SystemExit(main())
