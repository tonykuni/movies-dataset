# -*- coding: utf-8 -*-
"""ENG-030 WorkOps Follow-up State Engine v0100.
Reads existing WorkOps outputs only; appends local confirmation events. No Outlook send/move/delete.
"""
from __future__ import annotations
import argparse, csv, json, mimetypes, os, sys, threading, webbrowser
from datetime import datetime, timezone
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORKOPS = HERE.parent
OUT = WORKOPS / "out"
UI = WORKOPS / "ui" / "followup"
PARAMS_P = HERE / "followup_state_params.json"
REPLY_STATUS_P = OUT / "reply_status.json"
REPLY_EVENTS_P = OUT / "reply_events.jsonl"
WOP_REGISTRY_P = OUT / "wop_registry.json"
CLOSE_EVENTS_P = OUT / "followup_close_events.jsonl"
STATE_P = OUT / "followup_state.json"


def load_json(path, default):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except Exception:
        return default


def load_jsonl(path):
    rows = []
    if not Path(path).exists(): return rows
    for line in Path(path).read_text(encoding="utf-8", errors="replace").splitlines():
        try: rows.append(json.loads(line))
        except Exception: pass
    return rows


def atomic_write_json(path, obj):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(str(path) + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def parse_dt(v):
    if not v: return None
    for fn in (
        lambda: datetime.fromisoformat(str(v).replace("Z", "+00:00")),
        lambda: datetime.strptime(str(v)[:19], "%Y-%m-%d %H:%M:%S"),
        lambda: datetime.strptime(str(v)[:10], "%Y-%m-%d"),
    ):
        try:
            d = fn()
            return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
        except Exception: pass
    return None


def hours_since(v, now):
    d = parse_dt(v)
    if not d: return 0.0
    if not now.tzinfo: now = now.replace(tzinfo=timezone.utc)
    if not d.tzinfo: d = d.replace(tzinfo=timezone.utc)
    return max(0.0, (now.astimezone(timezone.utc) - d.astimezone(timezone.utc)).total_seconds()/3600)


def score_to_level(score, params):
    for band in params["risk_scoring"]["score_to_level"]:
        if band["min"] <= score <= band["max"]: return int(band["level"])
    return 5


def read_wop_map():
    d = load_json(WOP_REGISTRY_P, {})
    if isinstance(d, dict):
        for key in ("projects", "map", "registry"):
            if isinstance(d.get(key), dict): return d[key]
    return {}


def latest_reply_events():
    latest = {}
    for e in load_jsonl(REPLY_EVENTS_P):
        k = e.get("thr") or e.get("conv")
        if not k: continue
        if k not in latest or (e.get("mail_date", "") >= latest[k].get("mail_date", "")):
            latest[k] = e
    return latest


def closed_map():
    m = {}
    for e in load_jsonl(CLOSE_EVENTS_P):
        k = e.get("case_id") or e.get("thr")
        if k: m[k] = e
    return m


def compute_state():
    params = load_json(PARAMS_P, {})
    status_doc = load_json(REPLY_STATUS_P, {"status": {}})
    statuses = status_doc.get("status", {}) if isinstance(status_doc, dict) else {}
    events = latest_reply_events()
    wops = read_wop_map()
    closes = closed_map()
    now = datetime.now(timezone.utc)
    cards = []

    keys = sorted(set(statuses) | set(events))
    for thr in keys:
        st = statuses.get(thr, {})
        ev = events.get(thr, {})
        raw_status = st.get("status") or ev.get("status") or "未解析"
        state_code = params.get("reply_status_map", {}).get(raw_status, "UNKNOWN")
        wait_h = hours_since(st.get("mail_date") or ev.get("mail_date"), now)
        score, reasons = 0, []
        t = params.get("timing", {})
        if wait_h >= t.get("reply_critical_hours", 72): score += 3; reasons.append("等待回覆超過 72 小時")
        elif wait_h >= t.get("reply_warning_hours", 48): score += 2; reasons.append("等待回覆超過 48 小時")
        elif wait_h >= t.get("reply_attention_hours", 24): score += 1; reasons.append("等待回覆超過 24 小時")
        if state_code == "BLOCKED": score += 3; reasons.append("回覆狀態為卡關")
        if state_code == "NEED_HELP": score += 2; reasons.append("對方需要協助")
        text = ((ev.get("subject") or "") + " " + (ev.get("evidence") or "")).lower()
        if any(k.lower() in text for k in params.get("materiality", {}).get("keywords", [])):
            score += 2; reasons.append("涉及重大/關鍵事項")
        level = score_to_level(score, params)
        if state_code == "DONE_CANDIDATE":
            level = min(level, 3)
            reasons.append("收到完成訊號，等待人工確認結案")
        label = params.get("status_levels", {}).get(str(level), {})
        project = wops.get(thr, {}) if isinstance(wops.get(thr, {}), dict) else {}
        case_id = project.get("wop_id") or project.get("id") or thr
        is_closed = case_id in closes or thr in closes
        if is_closed:
            level = 1; state_code = "CLOSED"; reasons = ["已人工確認結案"]
            label = params.get("status_levels", {}).get("1", {})
        required = params.get("required_fields_by_status", {}).get(state_code, [])
        cards.append({
            "thr": thr, "case_id": case_id, "project_id": project.get("wop_id") if str(project.get("wop_id","")).startswith("PRJ-") else "",
            "project_name": project.get("name") or project.get("display_name") or thr,
            "status_raw": raw_status, "state_code": state_code, "level": level,
            "level_code": label.get("code", "UNKNOWN"), "level_label": label.get("label_zh", "未知"),
            "color": label.get("color", "#999999"), "flash": bool(label.get("flash")) and not is_closed,
            "waiting_hours": round(wait_h, 1), "last_mail_date": st.get("mail_date") or ev.get("mail_date", ""),
            "subject": ev.get("subject", ""), "sender": ev.get("sender", ""), "evidence": ev.get("evidence", ""),
            "owner": ev.get("sender", ""), "eta": ev.get("eta", ""), "reason": ev.get("reason", ""),
            "plan_b": ev.get("plan_b", ""), "next_action": ev.get("next_action", ""),
            "risk_score": score, "reasons": reasons, "required_fields": required,
            "close_candidate": state_code == "DONE_CANDIDATE" and not is_closed, "closed": is_closed
        })
    cards.sort(key=lambda x: (-x["level"], -x["waiting_hours"], x["case_id"]))
    watch_min = int(params.get("watchlist", {}).get("minimum_level", 4))
    watch = [c for c in cards if (c["level"] >= watch_min or c["close_candidate"]) and not c["closed"]]
    state = {"version": "v0100", "generated_at": datetime.now().isoformat(timespec="seconds"), "cards": cards, "watchlist": watch[:int(params.get("watchlist",{}).get("max_visible",12))], "summary": {"projects": len(cards), "critical": sum(c["level"]==5 for c in cards), "warning": sum(c["level"]==4 for c in cards), "close_candidates": sum(c["close_candidate"] for c in cards), "watchlist": len(watch)}}
    atomic_write_json(STATE_P, state)
    return state


def append_close(payload):
    case_id = str(payload.get("case_id") or "").strip()
    if not case_id: raise ValueError("case_id required")
    reason = str(payload.get("reason") or "").strip()
    if not reason: raise ValueError("closure reason required")
    ev = {"ts": datetime.now().isoformat(timespec="seconds"), "event": "CONFIRM_CLOSE", "case_id": case_id, "thr": payload.get("thr", ""), "reason": reason, "evidence": payload.get("evidence", ""), "confirmed_by": payload.get("confirmed_by", "LOCAL_USER")}
    OUT.mkdir(parents=True, exist_ok=True)
    with CLOSE_EVENTS_P.open("a", encoding="utf-8") as f: f.write(json.dumps(ev, ensure_ascii=False) + "\n")
    return ev


class Handler(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        rel = path.split("?",1)[0].split("#",1)[0].lstrip("/") or "index.html"
        return str(UI / rel)
    def log_message(self, fmt, *args): pass
    def send_json(self, obj, code=200):
        b = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code); self.send_header("Content-Type","application/json; charset=utf-8"); self.send_header("Content-Length",str(len(b))); self.end_headers(); self.wfile.write(b)
    def do_GET(self):
        if self.path.startswith("/api/state"): return self.send_json(compute_state())
        if self.path.startswith("/api/params"): return self.send_json(load_json(PARAMS_P, {}))
        return super().do_GET()
    def do_POST(self):
        n = int(self.headers.get("Content-Length","0") or 0)
        try: payload = json.loads(self.rfile.read(n).decode("utf-8")) if n else {}
        except Exception: return self.send_json({"ok":False,"error":"invalid json"},400)
        if self.path.startswith("/api/close"):
            try: ev = append_close(payload); return self.send_json({"ok":True,"event":ev,"state":compute_state()})
            except Exception as e: return self.send_json({"ok":False,"error":str(e)},400)
        return self.send_json({"ok":False,"error":"not found"},404)


def serve(open_browser=True):
    p = load_json(PARAMS_P, {})
    host = p.get("server",{}).get("host","127.0.0.1"); port = int(p.get("server",{}).get("port",8775))
    compute_state(); httpd = ThreadingHTTPServer((host,port), Handler)
    url = f"http://{host}:{port}/"
    print(f"[READY] Follow-up UI {url}")
    if open_browser and p.get("server",{}).get("open_browser",True): threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    try: httpd.serve_forever()
    except KeyboardInterrupt: pass


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("command", nargs="?", default="state", choices=["state","serve"]); ap.add_argument("--no-open", action="store_true"); a=ap.parse_args()
    if a.command == "state": print(json.dumps(compute_state(), ensure_ascii=False, indent=2)); return 0
    serve(not a.no_open); return 0

if __name__ == "__main__": sys.exit(main())
