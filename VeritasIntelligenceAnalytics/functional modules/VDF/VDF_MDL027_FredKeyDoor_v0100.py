#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Runtime password door for FRED_API_KEY. This process only. Nothing is written.

  py -3 VDF_MDL027_FredKeyDoor_v0100.py
  py -3 VDF_MDL027_FredKeyDoor_v0100.py status
  py -3 VDF_MDL027_FredKeyDoor_v0100.py selftest
"""
from __future__ import annotations

import json
import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs

PAGE = """<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>VDF FRED 鑰匙</title>
<style>
  body { margin: 0; background: #1c242c; color: #d5ddd8; font: 16px/1.45 "Segoe UI", sans-serif; }
  main { max-width: 34rem; margin: 8vh auto; padding: 1.5rem; background: #243038; border: 1px solid #3d4f5f; }
  h1 { font-size: 1.15rem; font-weight: 600; margin: 0 0 .4rem; }
  p { color: #aeb8b4; margin: 0 0 1rem; }
  label { display: block; margin-bottom .35rem; }
  input { width: 100%; box-sizing: border-box; padding: .55rem .7rem; background: #1c242c; color: #d5ddd8; border: 1px solid #3d4f5f; }
  button { margin-top .8rem; background: #3d4f5f; color: #d5ddd8; border: 0; padding: .55rem 1rem; cursor: pointer; }
  #out { margin-top: 1rem; white-space: pre-wrap; }
</style>
</head>
<body>
<main>
  <h1>FRED 鑰匙 · 只在這次行程</h1>
  <p>值不寫進檔案、日誌、倉庫，也不進瀏覽器儲存。使用者環境裡已經有的鑰匙會照舊留著；這裡只覆寫這支程式自己的行程。</p>
  <form id="f" method="post" action="/use" autocomplete="off">
    <label for="k">FRED_API_KEY</label>
    <input id="k" name="FRED_API_KEY" type="password" autocomplete="off" spellcheck="false">
    <button type="submit">只在這次行程使用</button>
  </form>
  <div id="out"></div>
</main>
<script>
  fetch("/status").then(r => r.json()).then(j => {
    document.getElementById("out").textContent = "目前 " + j.state + " · 來源 " + j.source;
  });
  document.getElementById("f").addEventListener("submit", async (ev) => {
    ev.preventDefault();
    const body = new URLSearchParams(new FormData(ev.target));
    const res = await fetch("/use", {method: "POST", headers: {"Content-Type": "application/x-www-form-urlencoded"}, body});
    const j = await res.json();
    document.getElementById("out").textContent = j.message;
    ev.target.reset();
  });
</script>
</body>
</html>
"""


def load_accel():
    import VIA_SuperAccel_Module as via_accel
    return via_accel


def key_file() -> Path | None:
    door = Path(__file__).resolve().parent / "output_hub" / "mega" / ".fred_api_key"
    return door if door.is_file() else None


def presence() -> dict:
    value = os.environ.get("FRED_API_KEY", "").strip()
    if value:
        return {"state": "present", "source": "env", "length": len(value)}
    if key_file() is not None:
        return {"state": "present", "source": "keyfile", "length": None}
    return {"state": "missing", "source": "missing", "length": 0}


def use_key(value: str) -> dict:
    value = (value or "").strip()
    if not value:
        return {"ok": False, "message": "空白，這次行程沒有改。"}
    os.environ["FRED_API_KEY"] = value
    card = presence()
    return {"ok": True, "message": "這次行程已有鑰匙。長度 %s。沒有寫進使用者環境，也沒有寫檔。" % card["length"]}


def status_text() -> str:
    card = presence()
    return "fred_key=%s source=%s" % (card["state"], card["source"])


class Door(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        return

    def _send(self, code: int, body: bytes, kind: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", kind)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/status":
            self._send(200, json.dumps(presence()).encode(), "application/json")
            return
        self._send(200, PAGE.encode("utf-8"), "text/html; charset=utf-8")

    def do_POST(self):
        if self.path != "/use":
            self._send(404, b"{}", "application/json")
            return
        size = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(size).decode("utf-8", "replace")
        value = (parse_qs(raw).get("FRED_API_KEY") or [""])[0]
        self._send(200, json.dumps(use_key(value), ensure_ascii=False).encode(), "application/json")


def serve() -> int:
    server = ThreadingHTTPServer(("127.0.0.1", 0), Door)
    host, port = server.server_address
    print("FRED door http://%s:%s" % (host, port), flush=True)
    print(status_text(), flush=True)
    print("Ctrl+C 結束。鑰匙只活在這支行程。", flush=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        thread.join()
    except KeyboardInterrupt:
        pass
    server.shutdown()
    return 0


def selftest() -> int:
    secret = "fixture-key-not-real"
    before = os.environ.get("FRED_API_KEY")
    os.environ.pop("FRED_API_KEY", None)
    fails = []
    try:
        if presence()["state"] == "present" and presence()["source"] == "env":
            fails.append("env leaked into missing check")
        os.environ["FRED_API_KEY"] = secret
        card = presence()
        blob = json.dumps(card)
        if secret in blob or secret in PAGE or secret in status_text().replace("length=", ""):
            # status_text must not contain the secret; length is allowed
            if secret in status_text() or secret in blob:
                fails.append("value printed")
        if card["length"] != len(secret) or card["source"] != "env":
            fails.append("card")
        blank = use_key("  ")
        if blank["ok"] or os.environ.get("FRED_API_KEY") != secret:
            fails.append("blank")
        if "localStorage" in PAGE or 'type="password"' not in PAGE:
            fails.append("page")
    finally:
        if before is None:
            os.environ.pop("FRED_API_KEY", None)
        else:
            os.environ["FRED_API_KEY"] = before
    if fails:
        print("[FAIL] " + "; ".join(fails))
        return 1
    print("[OK] password door keeps the value out of status, page, and files")
    print(status_text())
    return 0


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    cmd = argv[0] if argv else "serve"
    if cmd == "selftest":
        return selftest()
    if cmd == "status":
        print(status_text(), flush=True)
        return 0
    if cmd != "serve":
        print("verbs: serve status selftest", flush=True)
        return 2
    return serve()


if __name__ == "__main__":
    raise SystemExit(main())
