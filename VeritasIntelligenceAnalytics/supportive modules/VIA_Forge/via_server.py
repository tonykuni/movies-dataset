#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
VIA Forge Server  ——  via_server.py   (\u8584\u5f8c\u7aef\uff0cstdlib\uff0c\u96f6\u984d\u5916\u4f9d\u8cf4)
================================================================================
\u53ea\u8ca0\u8cac\u50b3\u8f38\uff1aserve UI + JSON API\uff0c\u5be6\u969b\u8655\u7406\u5168\u90fd\u4e1f\u7d66 via_forge.ForgeEngine\u3002

  GET  /              -> ui/index.html
  GET  /api/health    -> {status, caps, supported, root, port}
  GET  /api/config    -> SSOT config (read-only view)
  POST /api/scan      -> {dir|paths[], fix?} -> records + summary
  POST /api/export    -> {format} -> report path
  POST /api/shutdown  -> graceful stop
================================================================================
"""

import os
import sys
import json
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from via_forge import ForgeEngine, load_config, load_registry, TOOLS
try:
    import via_connect as _connect
except Exception:
    _connect = None
try:
    import via_pmine as _pmine
except Exception:
    _pmine = None
try:
    import via_sink as _sink
except Exception:
    _sink = None
try:
    import via_panorama as _panorama
except Exception:
    _panorama = None
try:
    import via_mailforge as _mailforge
except Exception:
    _mailforge = None

CFG = load_config()
REG = load_registry()
UI_DIR = os.path.join(HERE, "ui")
try:
    import via_manager as _mgrmod
    MANAGER = _mgrmod.get_manager(CFG)
    _LAST = MANAGER.state          # \u5171\u7528\u8a9e\u6599\u72c0\u614b\u7531 SystemManager \u64c1\u6709
except Exception:
    MANAGER = None
    _LAST = {"records": [], "summary": {}}
_ENGINE = None


def engine():
    global _ENGINE
    if _ENGINE is None:
        _ENGINE = ForgeEngine(CFG, REG)
    return _ENGINE


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, body, ctype="application/json"):
        if isinstance(body, (dict, list)):
            body = json.dumps(body, ensure_ascii=False)
        data = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype + "; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Access-Control-Allow-Origin", "http://127.0.0.1:%d" % CFG["server"]["port"])
        self.end_headers()
        self.wfile.write(data)

    def _body(self):
        n = int(self.headers.get("Content-Length", 0))
        if n <= 0:
            return {}
        try:
            return json.loads(self.rfile.read(n).decode("utf-8"))
        except Exception:
            return {}

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            fp = os.path.join(UI_DIR, "index.html")
            if os.path.exists(fp):
                with open(fp, "rb") as f:
                    self._send(200, f.read(), "text/html")
            else:
                self._send(404, {"error": "ui missing"})
            return
        if self.path == "/api/health":
            self._send(200, {"status": "ok", "caps": TOOLS.matrix(),
                             "supported": engine().supported(),
                             "root": CFG["paths"]["root"], "port": CFG["server"]["port"]})
            return
        if self.path == "/api/system":
            if MANAGER is None:
                self._send(200, {"available": False, "note": "manager not loaded"})
            else:
                self._send(200, {"available": True, **MANAGER.status()})
            return
        if self.path == "/api/config":
            self._send(200, {k: v for k, v in CFG.items() if not k.startswith("_")})
            return
        if self.path == "/api/connect/status":
            if MANAGER is None:
                self._send(200, {"available": False, "note": "manager not loaded"})
            else:
                self._send(200, {"available": True, **MANAGER.dispatch("connect.status")})
            return
        self._send(404, {"error": "not found"})

    def do_POST(self):
        body = self._body()
        if self.path == "/api/connect/pull":
            if MANAGER is None:
                self._send(400, {"error": "manager not loaded"}); return
            conn = body.get("connector")
            if conn not in ("gmail", "drive", "outlook", "local_outlook"):
                self._send(400, {"error": "connector must be gmail|drive|outlook|local_outlook"}); return
            self._send(200, MANAGER.dispatch("connect.pull", connector=conn,
                       max_items=body.get("max", 50)))
            return
        if self.path == "/api/pmine":
            if MANAGER is None:
                self._send(400, {"error": "manager not loaded"}); return
            if not MANAGER.records():
                self._send(400, {"error": "no records; run /api/scan or /api/connect/pull first"}); return
            self._send(200, MANAGER.dispatch("mine", context=body.get("context", "General"),
                       control=body.get("control", True), mine=body.get("mine", True),
                       ssot=body.get("ssot", True)))
            return
        if self.path in ("/api/pending/list", "/api/pending/regenerate", "/api/pending/approve"):
            if MANAGER is None:
                self._send(400, {"error": "manager not loaded"}); return
            if self.path == "/api/pending/list":
                self._send(200, MANAGER.dispatch("pending.list", kind=body.get("kind")))
            elif self.path == "/api/pending/regenerate":
                self._send(200, MANAGER.dispatch("pending.regenerate"))
            else:
                self._send(200, MANAGER.dispatch("pending.approve", pend_id=body.get("pend_id"),
                           decision=body.get("decision", "APPROVED"), note=body.get("note", "")))
            return
        if self.path == "/api/outlook":
            if MANAGER is None:
                self._send(400, {"error": "manager not loaded"}); return
            self._send(200, MANAGER.dispatch("outlook.oneclick", days_back=body.get("days_back", 7), max_items=body.get("max_items", 100), since=body.get("since"), until=body.get("until"), keyword=body.get("keyword")))
            return
        if self.path == "/api/rebuild":
            if MANAGER is None:
                self._send(400, {"error": "manager not loaded"}); return
            self._send(200, MANAGER.dispatch("rebuild", control_sheet=body.get("control_sheet")))
            return
        if self.path == "/api/signal":
            if MANAGER is None:
                self._send(400, {"error": "manager not loaded"}); return
            self._send(200, MANAGER.dispatch("signal.board"))
            return
        if self.path == "/api/ops":
            if MANAGER is None:
                self._send(400, {"error": "manager not loaded"}); return
            self._send(200, MANAGER.dispatch("ops.board", owner=(body.get("owner") or "").strip() or None))
            return
        if self.path == "/api/project/export":
            if MANAGER is None:
                self._send(400, {"error": "manager not loaded"}); return
            self._send(200, MANAGER.dispatch("project.export",
                       name=body.get("name", "\u5c08\u6848"), topic=body.get("topic"),
                       since=body.get("since"), until=body.get("until")))
            return
        if self.path == "/api/project":
            if MANAGER is None:
                self._send(400, {"error": "manager not loaded"}); return
            proj = MANAGER.dispatch("project.create",
                                    name=body.get("name", "\u5c08\u6848"), topic=body.get("topic"),
                                    since=body.get("since"), until=body.get("until"),
                                    calendar=body.get("calendar"))
            try:
                path = os.path.join(CFG["paths"]["reports"], "project.html")
                MANAGER.engine("mailhub").project_html(proj, path)
                proj["report_path"] = path
            except Exception:
                pass
            self._send(200, proj)
            return
        if self.path in ("/api/mail/intelligence", "/api/mail/clusters",
                         "/api/mail/replystatus", "/api/mail/stakeholders"):
            if MANAGER is None:
                self._send(400, {"error": "manager not loaded"}); return
            target = (body.get("target") or "").strip() or None
            action = {"/api/mail/intelligence": "mail.intelligence",
                      "/api/mail/clusters": "mail.clusters",
                      "/api/mail/replystatus": "mail.replystatus",
                      "/api/mail/stakeholders": "mail.stakeholders"}[self.path]
            self._send(200, MANAGER.dispatch(action, target=target))
            return
        if self.path == "/api/panorama":
            if MANAGER is None:
                self._send(400, {"error": "manager not loaded"}); return
            self._send(200, MANAGER.dispatch("panorama", audit=body.get("audit", True)))
            return
        if self.path == "/api/sink":
            if MANAGER is None:
                self._send(400, {"error": "manager not loaded"}); return
            if not MANAGER.records():
                self._send(400, {"error": "no records; scan or pull first"}); return
            fmts = body.get("formats") or CFG.get("sink", {}).get("default_formats", ["json"])
            self._send(200, {"exports": MANAGER.dispatch("sink", formats=fmts)})
            return
        if self.path == "/api/upload":
            files = body.get("files") or []
            if not files:
                self._send(400, {"error": "no files"}); return
            import base64 as _b64
            inbox = CFG["paths"]["inbox"]; os.makedirs(inbox, exist_ok=True)
            saved = []
            for f in files[:200]:
                name = os.path.basename(f.get("name", "upload.bin"))
                try:
                    raw = _b64.b64decode((f.get("b64") or "").split(",")[-1])
                    p = os.path.join(inbox, name)
                    with open(p, "wb") as fh:
                        fh.write(raw)
                    saved.append(p)
                except Exception:
                    continue
            if not saved:
                self._send(400, {"error": "no valid files decoded"}); return
            r = MANAGER.dispatch("scan", target=saved, do_fix=body.get("fix", True))
            self._send(200, {"summary": r["summary"], "records": r["records"], "saved": len(saved)})
            return
        if self.path == "/api/scan":
            if MANAGER is None:
                self._send(400, {"error": "manager not loaded"}); return
            target = body.get("dir") or body.get("paths")
            if not target:
                self._send(400, {"error": "missing dir or paths"}); return
            r = MANAGER.dispatch("scan", target=target, do_fix=body.get("fix", True))
            self._send(200, {"summary": r["summary"], "records": r["records"]})
            return
        if self.path == "/api/export":
            fmt = body.get("format", CFG["export"]["default"])
            eng = engine()
            out = CFG["paths"]["reports"]; os.makedirs(out, exist_ok=True)
            recs, summ = _LAST["records"], _LAST["summary"]
            fn = {"json": "forge_report.json", "csv": "forge_records.csv",
                  "xlsx": "forge_records.xlsx", "html": "forge_report.html"}[fmt]
            path = os.path.join(out, fn)
            if fmt in ("json", "html"):
                getattr(eng, "export_" + fmt)(recs, summ, path)
            else:
                getattr(eng, "export_" + fmt)(recs, path)
            self._send(200, {"path": path, "format": fmt})
            return
        if self.path == "/api/shutdown":
            if CFG["server"]["shutdown_endpoint"]:
                self._send(200, {"status": "shutting down"})
                threading.Thread(target=self.server.shutdown, daemon=True).start()
            else:
                self._send(403, {"error": "disabled"})
            return
        self._send(404, {"error": "not found"})


def _pick_port(cfg):
    import socket
    lo, hi = cfg["server"]["port_fallback_range"]
    for port in range(lo, hi + 1):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.bind((cfg["server"]["host"], port)); s.close(); return port
        except OSError:
            s.close(); continue
    return cfg["server"]["port"]


def serve(open_browser=None):
    port = _pick_port(CFG); CFG["server"]["port"] = port
    httpd = ThreadingHTTPServer((CFG["server"]["host"], port), Handler)
    url = "http://%s:%d/" % (CFG["server"]["host"], port)
    sys.stderr.write("@@PROGRESS|100|server ready %s\n" % url); sys.stderr.flush()
    print("VIA Forge server: %s" % url)
    ob = CFG["server"]["open_browser"] if open_browser is None else open_browser
    if ob:
        try:
            webbrowser.open(url)
        except Exception:
            pass
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()


def selftest():
    p = 0; f = 0
    def ck(n, c):
        nonlocal p, f
        if c: p += 1; print("  [PASS] server: %s" % n)
        else: f += 1; print("  [FAIL] server: %s" % n)
    ck("engine builds", engine() is not None)
    ck("supported superset", len(engine().supported()) >= 28)
    ck("port in range", CFG["server"]["port_fallback_range"][0] <= _pick_port(CFG) <= CFG["server"]["port_fallback_range"][1])
    ck("caps dict", isinstance(TOOLS.matrix(), dict))
    return p, f


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--no-browser", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        a, b = selftest(); print("server: %d PASS / %d FAIL" % (a, b)); sys.exit(0 if b == 0 else 1)
    serve(open_browser=not args.no_browser)
