#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:MODULE_SPEC:START]
# MODULE_NAME:       vdf_api_server
# MODULE_VERSION:    1.0.0
# MODULE_ROLE:       Lightweight HTTP API wrapping VDF_SystemManager.
#                    Serves the cockpit HTML UI and exposes JSON endpoints
#                    for matrix edit, category run, log stream, output listing.
# MODULE_ZONE:       D5
# MODULE_TYPE:       SERVICE
# DEPENDENCIES:      stdlib only (http.server, json, threading)
# ERROR_POLICY:      RETURN_SAFE_DEFAULT
# SAFE_SKIP:         True
# MERGE_UNIT_ID:     VDF-D5-API-001
# [VIA:MODULE_SPEC:END]
"""
VDF API server.

Endpoints
---------
GET  /                       → cockpit UI (HTML)
GET  /api/matrix             → return full matrix JSON
POST /api/matrix             → save matrix JSON
GET  /api/categories         → list categories with fetcher readiness
GET  /api/outputs            → list output parquet files (rows + size + mtime)
POST /api/run                → kick off a run (body: {mode, category?, ticker?, start?, end?, skip_chips?, output_format?})
GET  /api/run/status         → current run status + tail of log
POST /api/run/cancel         → request cancel (best-effort)
GET  /api/log/stream         → SSE stream of log lines
GET  /api/health             → health probe

Design notes
------------
- Pure stdlib. No flask/fastapi.
- Single background thread for the active run; only one at a time.
- Log buffer (ring) held in memory + tail of last 500 lines exposed.
- CORS open for local UI.
"""

from __future__ import annotations

import io
import json
import logging
import os
import queue
import subprocess
import sys
import threading
import time
import traceback
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse, parse_qs

# Setup paths
_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
sys.path.insert(0, str(_HERE))

# Setup logger
log = logging.getLogger("VDF.api")
log.setLevel(logging.INFO)

# Defer SystemManager imports until needed (avoid double-init logging)
_SYS_MOD_CACHE = None
def _load_system():
    global _SYS_MOD_CACHE
    if _SYS_MOD_CACHE is not None:
        return _SYS_MOD_CACHE
    from vdf_core import (
        FetchMatrix, ParquetStore, VDFRunner, _lazy_register, REGISTRY,
        DEFAULT_MATRIX_PATH, DEFAULT_OUTPUT_DIR, DEFAULT_TEMP_DIR,
        PROD_OUTPUT_DIR, PROD_TEMP_DIR, FRED_API_KEY,
    )
    _SYS_MOD_CACHE = locals().copy()
    return _SYS_MOD_CACHE


# ===== Run state ============================================================

class RunState:
    """Singleton holding the current run state. Only one run at a time."""

    def __init__(self):
        self.lock = threading.Lock()
        self.thread: Optional[threading.Thread] = None
        self.is_running = False
        self.cancel_requested = False
        self.started_at: Optional[str] = None
        self.finished_at: Optional[str] = None
        self.last_request: Dict[str, Any] = {}
        self.last_result: Dict[str, Any] = {}
        self.log_buffer: List[str] = []  # last 500 lines
        self.log_subscribers: List[queue.Queue] = []

    def append_log(self, line: str):
        with self.lock:
            self.log_buffer.append(line)
            if len(self.log_buffer) > 500:
                self.log_buffer = self.log_buffer[-500:]
            for q in self.log_subscribers:
                try:
                    q.put_nowait(line)
                except queue.Full:
                    pass

    def snapshot(self) -> Dict[str, Any]:
        with self.lock:
            return {
                "is_running": self.is_running,
                "cancel_requested": self.cancel_requested,
                "started_at": self.started_at,
                "finished_at": self.finished_at,
                "last_request": dict(self.last_request),
                "last_result": dict(self.last_result),
                "log_tail": list(self.log_buffer[-200:]),
            }


RUN = RunState()


# ===== Log handler that pushes into RUN.log_buffer ==========================

class _BufferLogHandler(logging.Handler):
    def emit(self, record):
        try:
            line = self.format(record)
            RUN.append_log(line)
        except Exception:
            pass


def _install_log_capture():
    h = _BufferLogHandler()
    h.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
    h.setLevel(logging.INFO)
    logging.getLogger().addHandler(h)


# ===== Run worker ===========================================================

def _do_run(req: Dict[str, Any], sys_mod: Dict[str, Any]):
    """Background runner thread body."""
    RUN.started_at = datetime.now().isoformat()
    RUN.finished_at = None
    RUN.cancel_requested = False
    RUN.last_request = dict(req)
    RUN.last_result = {}

    try:
        FetchMatrix = sys_mod["FetchMatrix"]
        ParquetStore = sys_mod["ParquetStore"]
        VDFRunner = sys_mod["VDFRunner"]
        _lazy_register = sys_mod["_lazy_register"]

        matrix_path = Path(req.get("matrix_path", str(sys_mod["DEFAULT_MATRIX_PATH"])))
        matrix = FetchMatrix.load(matrix_path)
        log.info("[API] matrix loaded: %d categories", len(matrix.categories))

        if req.get("prod_paths"):
            out_dir = sys_mod["PROD_OUTPUT_DIR"]
            tmp_dir = sys_mod["PROD_TEMP_DIR"]
        else:
            out_dir = sys_mod["DEFAULT_OUTPUT_DIR"]
            tmp_dir = sys_mod["DEFAULT_TEMP_DIR"]
        store = ParquetStore(out_dir, tmp_dir)
        log.info("[API] output=%s", out_dir)

        # dates
        start = req.get("start") or matrix.global_cfg.get("default_start_date", "2010-01-01")
        end = req.get("end") or datetime.now().strftime("%Y-%m-%d")

        ctx = {
            "start": start,
            "end": end,
            "output_format": req.get("output_format", "parquet"),
            # Priority: request body > env > matrix default
            "fred_api_key": (
                req.get("fred_api_key")
                or sys_mod["FRED_API_KEY"]
                or matrix.global_cfg.get("fred_api_key_default", "")
            ),
            "limit": req.get("limit"),
            "full_refresh": bool(req.get("full_refresh")),
            "skip_chips": bool(req.get("skip_chips")),
            "ticker_override": req.get("ticker"),
            "store": store,
            "matrix": matrix,
        }

        _lazy_register()

        runner = VDFRunner(matrix=matrix, store=store, ctx=ctx)

        mode = req.get("mode", "full")
        if mode == "full":
            runner.run_all()
        elif mode == "category":
            cat = req.get("category")
            if not cat:
                raise ValueError("category required when mode=category")
            runner.run_one(cat)
        elif mode == "ticker":
            tk = (req.get("ticker") or "").upper()
            if not tk:
                raise ValueError("ticker required when mode=ticker")
            if tk.endswith(".TW") or tk.endswith(".TWO"):
                cat = "tw_stock"
            elif tk in ("^TWII", "^TWO"):
                cat = "tw_index"
            elif "=X" in tk:
                cat = "fx"
            elif "=F" in tk:
                cat = "commodity"
            else:
                cat = "intl_stock"
            runner.run_one(cat)
        else:
            raise ValueError(f"unknown mode: {mode}")

        RUN.last_result = {"ok": True, "report": runner.report}
        log.info("[API] run completed")
    except Exception as e:
        log.error("[API] run failed: %s", e)
        log.error(traceback.format_exc())
        RUN.last_result = {"ok": False, "error": str(e), "traceback": traceback.format_exc()}
    finally:
        RUN.is_running = False
        RUN.finished_at = datetime.now().isoformat()


def start_run(req: Dict[str, Any], sys_mod: Dict[str, Any]) -> Dict[str, Any]:
    if RUN.is_running:
        return {"ok": False, "error": "run_already_in_progress"}
    RUN.is_running = True
    RUN.thread = threading.Thread(target=_do_run, args=(req, sys_mod), daemon=True)
    RUN.thread.start()
    return {"ok": True, "started_at": RUN.started_at}


# ===== HTTP handler =========================================================

class VDFRequestHandler(BaseHTTPRequestHandler):
    server_version = "VDF-API/1.0"

    # silence default logging
    def log_message(self, format, *args):
        pass

    def _send(self, code: int, body: bytes, content_type: str = "application/json", extra_headers: Optional[Dict[str, str]] = None):
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        if extra_headers:
            for k, v in extra_headers.items():
                self.send_header(k, v)
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def _send_json(self, code: int, obj: Any):
        body = json.dumps(obj, default=str).encode("utf-8")
        self._send(code, body, "application/json; charset=utf-8")

    def _read_body(self) -> Dict[str, Any]:
        n = int(self.headers.get("Content-Length", 0))
        if n <= 0:
            return {}
        raw = self.rfile.read(n)
        try:
            return json.loads(raw.decode("utf-8"))
        except Exception:
            return {}

    def do_OPTIONS(self):
        self._send(204, b"")

    def do_GET(self):
        parsed = urlparse(self.path)
        p = parsed.path
        q = parse_qs(parsed.query)
        try:
            if p == "/" or p == "/index.html":
                self._serve_static("cockpit/index.html", "text/html; charset=utf-8")
            elif p == "/cockpit.css":
                self._serve_static("cockpit/cockpit.css", "text/css; charset=utf-8")
            elif p == "/cockpit.js":
                self._serve_static("cockpit/cockpit.js", "application/javascript; charset=utf-8")
            elif p == "/api/health":
                self._send_json(200, {"ok": True, "service": "VDF-API", "version": "1.0"})
            elif p == "/api/matrix":
                self._api_get_matrix()
            elif p == "/api/categories":
                self._api_list_categories()
            elif p == "/api/outputs":
                self._api_list_outputs()
            elif p == "/api/run/status":
                self._send_json(200, RUN.snapshot())
            elif p == "/api/log/stream":
                self._api_log_stream()
            else:
                self._send_json(404, {"ok": False, "error": "not_found", "path": p})
        except Exception as e:
            log.error("[API] GET %s failed: %s", p, e)
            log.error(traceback.format_exc())
            self._send_json(500, {"ok": False, "error": str(e)})

    def do_POST(self):
        parsed = urlparse(self.path)
        p = parsed.path
        try:
            if p == "/api/matrix":
                self._api_save_matrix()
            elif p == "/api/run":
                self._api_start_run()
            elif p == "/api/run/cancel":
                RUN.cancel_requested = True
                self._send_json(200, {"ok": True, "msg": "cancel_requested"})
            else:
                self._send_json(404, {"ok": False, "error": "not_found", "path": p})
        except Exception as e:
            log.error("[API] POST %s failed: %s", p, e)
            log.error(traceback.format_exc())
            self._send_json(500, {"ok": False, "error": str(e)})

    # ---- static ----

    def _serve_static(self, rel_path: str, content_type: str):
        fp = _ROOT / rel_path
        if not fp.exists():
            # also try src/cockpit/...
            fp = _HERE / Path(rel_path).name
            if not fp.exists():
                self._send_json(404, {"ok": False, "error": f"static_not_found:{rel_path}"})
                return
        body = fp.read_bytes()
        self._send(200, body, content_type)

    # ---- /api/matrix ----

    def _matrix_path(self) -> Path:
        return _ROOT / "config" / "vdf_fetch_matrix.json"

    def _api_get_matrix(self):
        fp = self._matrix_path()
        if not fp.exists():
            self._send_json(404, {"ok": False, "error": "matrix_not_found"})
            return
        data = json.loads(fp.read_text(encoding="utf-8"))
        self._send_json(200, {"ok": True, "matrix": data, "path": str(fp)})

    def _api_save_matrix(self):
        body = self._read_body()
        if "matrix" not in body:
            self._send_json(400, {"ok": False, "error": "matrix_required"})
            return
        fp = self._matrix_path()
        # backup
        if fp.exists():
            bak = fp.with_suffix(f".bak_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            bak.write_bytes(fp.read_bytes())
        fp.write_text(json.dumps(body["matrix"], indent=2, ensure_ascii=False), encoding="utf-8")
        log.info("[API] matrix saved (%d bytes)", fp.stat().st_size)
        self._send_json(200, {"ok": True, "path": str(fp), "bytes": fp.stat().st_size})

    # ---- /api/categories ----

    def _api_list_categories(self):
        sys_mod = _load_system()
        FetchMatrix = sys_mod["FetchMatrix"]
        _lazy_register = sys_mod["_lazy_register"]
        REGISTRY = sys_mod["REGISTRY"]
        _lazy_register()
        try:
            matrix = FetchMatrix.load(self._matrix_path())
            out = []
            for c in matrix.categories:
                n_items = len(c.tickers) + len(c.indicators)
                out.append({
                    "id": c.id,
                    "name": c.name,
                    "description": c.description,
                    "output_file": c.output_file,
                    "update_frequency": c.update_frequency,
                    "n_items": n_items,
                    "ready": REGISTRY.get(c.id) is not None,
                    "primary_key": c.primary_key,
                    "source_pipeline": c.source_pipeline,
                })
            self._send_json(200, {"ok": True, "categories": out})
        except Exception as e:
            self._send_json(500, {"ok": False, "error": str(e)})

    # ---- /api/outputs ----

    def _api_list_outputs(self):
        sys_mod = _load_system()
        out_dir = sys_mod["DEFAULT_OUTPUT_DIR"]
        if not out_dir.exists():
            self._send_json(200, {"ok": True, "outputs": []})
            return
        items = []
        for f in sorted(out_dir.glob("*.parquet")):
            try:
                stat = f.stat()
                rows = None
                try:
                    import pyarrow.parquet as pq
                    rows = pq.read_metadata(f).num_rows
                except Exception:
                    pass
                items.append({
                    "name": f.name,
                    "bytes": stat.st_size,
                    "mtime": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "rows": rows,
                })
            except Exception:
                continue
        self._send_json(200, {"ok": True, "outputs": items, "output_dir": str(out_dir)})

    # ---- /api/run ----

    def _api_start_run(self):
        body = self._read_body()
        sys_mod = _load_system()
        result = start_run(body, sys_mod)
        code = 200 if result.get("ok") else 409
        self._send_json(code, result)

    # ---- /api/log/stream (SSE) ----

    def _api_log_stream(self):
        # Server-Sent Events
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        q: queue.Queue = queue.Queue(maxsize=1000)
        with RUN.lock:
            RUN.log_subscribers.append(q)
            # also prime with current tail
            tail = list(RUN.log_buffer[-50:])
        try:
            # send tail first
            for line in tail:
                self._sse_send(line)
            # stream loop
            while True:
                try:
                    line = q.get(timeout=15)
                    self._sse_send(line)
                except queue.Empty:
                    # heartbeat
                    try:
                        self.wfile.write(b": keepalive\n\n")
                        self.wfile.flush()
                    except (BrokenPipeError, ConnectionResetError):
                        break
        except Exception:
            pass
        finally:
            with RUN.lock:
                try:
                    RUN.log_subscribers.remove(q)
                except ValueError:
                    pass

    def _sse_send(self, line: str):
        try:
            payload = "data: " + line.replace("\r", "").replace("\n", " ") + "\n\n"
            self.wfile.write(payload.encode("utf-8"))
            self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            raise


# ===== Entry ================================================================

def main(host: str = "127.0.0.1", port: int = 8765):
    _install_log_capture()
    log.info("[API] starting on http://%s:%d", host, port)

    server = ThreadingHTTPServer((host, port), VDFRequestHandler)
    log.info("[API] cockpit UI:  http://%s:%d/", host, port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log.info("[API] shutting down")
        server.server_close()


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8765)
    args = p.parse_args()
    main(args.host, args.port)
