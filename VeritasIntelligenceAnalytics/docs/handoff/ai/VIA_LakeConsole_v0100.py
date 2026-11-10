#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VIA_LakeConsole v0100 — 滑鼠操作的 VCGC 資料湖 / 工具操作台(本機橋 127.0.0.1 · 白名單動作 · 同源權杖 · 輸出見證)。

操作員 2026-11-10:「實測自設自修正輸出 · 輸出見證 · HTML U/I 可操作 · 高自動化高整合 · 只有必要的項目才用輸入 ·
介面都是滑鼠動作:Windows I/O · 拖曳式 · 下拉選單 · 勾選」。
機制(照 CGC_MDL095 DeckServer 的本機橋鐵則,縮小成資料湖 / 工具這一塊):
  · 只綁 127.0.0.1;頁面注入當次隨機權杖;副作用 POST 要同源 Origin + Sec-Fetch-Site: same-origin + X-VIA-CSRF;只接 JSON body。
  · 動作白名單(不接任意指令):備份檢查 · 工具看板 · 資料湖矩陣 · 四支自測 · 自修正(重建視圖 → 矩陣 → 看板)· 入湖(拖曳 / 選檔 / 選資料夾的檔案)。
  · 每個動作 = 子行程跑倉內引擎(逐段 log 落盤 · rc · 秒 · 收據路徑)→ 頁面輪詢 → 見證面板亮燈;單通道(同時只跑一件)。
  · 入湖只寫 VCGC 自己的湖;選了他系統 → 落 <root>/_inbox/<SYS>/ 暫存 + 清單,由該系統自己接(L123 不代寫)。
  · 檔案瀏覽只供 VIA_Reports/** 與湖根下的收據(白名單夾 · 越夾 404)。
用法:serve [--port 0] [--root] [--no-open](預設啟動後自動跳出 HTML U/I)· --selftest
"""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(批102 全樹導入令;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
except Exception:  # noqa: BLE001
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

import argparse
import base64
import csv
import glob
import hashlib
import hmac
import html
import importlib.util
import io
import json
import os
import re
import secrets
import subprocess
import sys
import tempfile
import threading
import time
import webbrowser
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

VERSION = "v0100"
ENGINE = "VIA_LakeConsole " + VERSION
HERE = Path(__file__).resolve().parent
VIA = HERE.parents[2] if HERE.name == "ai" else HERE
SYSTEMS = ["VCGC", "VDF", "VRN2", "VQG", "VAP"]
LABEL = {"VCGC": "VCGC", "VDF": "VDF", "VRN2": "VRN-2", "VQG": "VQG", "VAP": "VAP"}
OUT_DIR = "VIA_Reports/lake"
UPLOAD_CAP = 24 * 1024 * 1024          # 單批上傳上限(base64 前)
BODY_CAP = UPLOAD_CAP * 4 // 3 + 65536
EXTS = (".jsonl", ".json", ".csv", ".parquet")
ACTIONS = {  # 白名單:動作 → (中文, 引擎 glob, argv 模板;{root} 會代入湖根)
    "backup_check": ("檢查備份", "docs/handoff/ai/VIA_DailyBackup_v*.py", ["check"], "VIA_Reports/backup/CHECK_latest.json"),
    "toolboard": ("工具看板", "docs/handoff/ai/VIA_VCGCToolBoard_v*.py", ["run"], "VIA_Reports/vcgc/TOOLBOARD_latest.html"),
    "lake_matrix": ("資料湖矩陣", "docs/handoff/ai/VIA_LakeMatrix_v*.py", ["run", "--root", "{root}"], "VIA_Reports/lake/LAKE_MATRIX_latest.html"),
    "kit_selftest": ("套件自測 VIA_ParquetLake", "supportive modules/VIA_ParquetLake_v*.py", ["--selftest"], None),
    "matrix_selftest": ("矩陣自測 VIA_LakeMatrix", "docs/handoff/ai/VIA_LakeMatrix_v*.py", ["--selftest"], None),
    "toolboard_selftest": ("看板自測 VIA_VCGCToolBoard", "docs/handoff/ai/VIA_VCGCToolBoard_v*.py", ["--selftest"], None),
    "backup_selftest": ("備份自測 VIA_DailyBackup", "docs/handoff/ai/VIA_DailyBackup_v*.py", ["--selftest"], None),
}
CHAINS = {"self_heal": ("自修正(重建視圖 → 矩陣 → 看板 → 備份檢查)", ["lake_matrix", "toolboard", "backup_check"]),
          "selftest_all": ("全部自測(套件 · 矩陣 · 看板 · 備份)", ["kit_selftest", "matrix_selftest", "toolboard_selftest", "backup_selftest"])}
ORDER = {"GREEN": 0, "YELLOW": 1, "GRAY": 2, "RED": 3}


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def e(s) -> str:
    return html.escape(str(s if s is not None else ""))


def tail_glob(via: Path, pat: str) -> Path | None:
    hits = sorted(glob.glob(str(via / pat)))
    return Path(hits[-1]) if hits else None


def _lake_module(via: Path):
    p = tail_glob(via, "supportive modules/VIA_ParquetLake_v*.py")
    if not p:
        return None
    spec = importlib.util.spec_from_file_location("VIA_ParquetLake_tail", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def resolve_root(via: Path, override: str | None = None) -> tuple[Path, str]:
    if override:
        return Path(override).resolve(), "--root"
    env = os.environ.get("VIA_DATA_HOME")
    if env and Path(env).is_dir():
        return Path(env).resolve(), "env VIA_DATA_HOME"
    return (via / OUT_DIR).resolve(), "repo_default"


# ───────────────────────── 狀態(燈)只讀 ─────────────────────────
def _load(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return None


def lamps(via: Path, root: Path) -> list[dict]:
    rows = []
    b = _load(via / "VIA_Reports/backup/CHECK_latest.json")
    rows.append({"key": "backup", "title": "備份檢查", "lamp": (b or {}).get("lamp", "GRAY"), "at": (b or {}).get("at"), "note": (b or {}).get("meaning", "沒有收據")})
    t = _load(via / "VIA_Reports/vcgc/TOOLBOARD_latest.json")
    rows.append({"key": "toolboard", "title": "工具看板", "lamp": ((t or {}).get("overall") or {}).get("lamp", "GRAY"), "at": (t or {}).get("at"), "note": ((t or {}).get("overall") or {}).get("meaning", "沒有收據")})
    m = _load(via / "VIA_Reports/lake/LAKE_MATRIX_latest.json")
    rows.append({"key": "lake", "title": "資料湖矩陣", "lamp": ((m or {}).get("overall") or {}).get("lamp", "GRAY"), "at": (m or {}).get("at"),
                 "note": " · ".join("%s %s" % (LABEL[c["system"]], c["lamp"]) for c in (m or {}).get("systems", [])) or "沒有收據"})
    mod = _lake_module(via)
    if mod:
        st = mod.Lake(root, "VCGC").status()
        n = len(st.get("tables", []))
        rows.append({"key": "vcgc_lake", "title": "VCGC 湖", "lamp": "GREEN" if n else "GRAY", "at": max((x.get("last_ingest") or "" for x in st.get("tables", [])), default=None) or None,
                     "note": "%d 表 · manifest %d 行 · %s" % (n, st.get("manifest_lines", 0), st["home"]) if st.get("exists") else "還沒有湖(跑一次資料湖矩陣或入湖就有)"})
    else:
        rows.append({"key": "vcgc_lake", "title": "VCGC 湖", "lamp": "RED", "at": None, "note": "套件 VIA_ParquetLake 不在"})
    return rows


def receipts(via: Path) -> list[dict]:
    out = []
    for rel in ("VIA_Reports/backup/CHECK_latest.md", "VIA_Reports/vcgc/TOOLBOARD_latest.html", "VIA_Reports/vcgc/TOOLBOARD_latest.md", "VIA_Reports/lake/LAKE_MATRIX_latest.html",
                "VIA_Reports/lake/LAKE_MATRIX_latest.md", "VIA_Reports/lake/UI_UserTest_latest.md", "VIA_Reports/vcgc/TEST_latest.json", "VIA_Reports/mutual/MUTUAL_latest.md"):
        p = via / rel
        if p.exists():
            out.append({"rel": rel, "bytes": p.stat().st_size, "mtime": datetime.fromtimestamp(p.stat().st_mtime, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")})
    return out


# ───────────────────────── 執行(子行程 · 單通道 · 見證) ─────────────────────────
class Runner:
    def __init__(self, via: Path, root: Path):
        self.via, self.root = via, root
        self.lock = threading.Lock()
        self.runs: dict[str, dict] = {}
        self.active: str | None = None
        self.logdir = via / OUT_DIR / "console_runs"
        self.ledger = via / OUT_DIR / "console_ledger.jsonl"

    def _argv(self, action: str) -> tuple[list[str] | None, str]:
        zh, pat, args, _ = ACTIONS[action]
        eng = tail_glob(self.via, pat)
        if not eng:
            return None, "引擎不在:%s" % pat
        return [sys.executable, str(eng)] + [a.replace("{root}", str(self.root)) for a in args], zh

    def start(self, action: str, options: dict | None = None) -> dict:
        options = options or {}
        steps = CHAINS[action][1] if action in CHAINS else ([action] if action in ACTIONS else None)
        if not steps:
            return {"ok": False, "kind": "unknown_action", "err": "動作不在白名單:%s" % action}
        with self.lock:
            if self.active and self.runs[self.active]["state"] == "RUNNING":
                return {"ok": False, "kind": "busy", "run_id": self.active, "err": "單通道:已有動作在跑"}
            run_id = "run-%s-%s" % (datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S"), secrets.token_hex(2))
            rec = {"run_id": run_id, "action": action, "zh": CHAINS.get(action, (ACTIONS.get(action, ("?",))[0],))[0], "steps": [], "state": "RUNNING", "started": _now(), "ended": None,
                   "rc": None, "lamp": "GRAY", "receipts": [], "log": str(self.logdir / (run_id + ".log")), "options": {k: bool(v) for k, v in options.items()}}
            self.runs[run_id] = rec
            self.active = run_id
        threading.Thread(target=self._work, args=(run_id, steps, options), daemon=True).start()
        return {"ok": True, "run_id": run_id, "steps": steps}

    def _work(self, run_id: str, steps: list[str], options: dict) -> None:
        rec = self.runs[run_id]
        self.logdir.mkdir(parents=True, exist_ok=True)
        worst = 0
        with open(rec["log"], "w", encoding="utf-8") as log:
            for s in steps:
                argv, zh = self._argv(s)
                st = {"step": s, "zh": zh, "rc": None, "secs": None, "tail": "", "receipt": None}
                rec["steps"].append(st)
                if argv is None:
                    st["rc"], st["tail"] = 127, zh
                    worst = 3
                    log.write("## %s · %s\n%s\n" % (s, zh, zh))
                    continue
                if options.get("dry") and s in ("toolboard", "lake_matrix"):
                    argv = argv + ["--no-write"]
                t0 = time.time()
                log.write("## %s · %s\n$ %s\n" % (s, zh, " ".join(argv)))
                log.flush()
                try:
                    p = subprocess.run(argv, cwd=str(self.via), capture_output=True, text=True, timeout=900, stdin=subprocess.DEVNULL, env={**os.environ, "PYTHONIOENCODING": "utf-8"})
                    out = (p.stdout or "") + (("\n[stderr]\n" + p.stderr) if p.stderr.strip() else "")
                    st["rc"] = p.returncode
                except subprocess.TimeoutExpired:
                    out, st["rc"] = "逾時 900s", 124
                st["secs"] = round(time.time() - t0, 1)
                lines = [l for l in out.splitlines() if l.strip() and not l.startswith("<unknown>")]
                st["tail"] = "\n".join(lines[-14:])
                log.write(out + "\n")
                log.flush()
                rp = ACTIONS[s][3]
                if rp and (self.via / rp).exists():
                    st["receipt"] = rp
                    rec["receipts"].append(rp)
                worst = max(worst, 0 if st["rc"] == 0 else (1 if st["rc"] in (1,) and s.endswith(("_check", "toolboard", "lake_matrix")) else 3))
        rec["ended"] = _now()
        rec["rc"] = max((s["rc"] or 0) for s in rec["steps"]) if rec["steps"] else 1
        rec["lamp"] = ["GREEN", "YELLOW", "GRAY", "RED"][worst]
        rec["state"] = "DONE"
        with open(self.ledger, "a", encoding="utf-8") as f:
            f.write(json.dumps({"at": rec["ended"], "run_id": run_id, "action": rec["action"], "rc": rec["rc"], "lamp": rec["lamp"], "steps": [(s["step"], s["rc"], s["secs"]) for s in rec["steps"]], "options": rec["options"]}, ensure_ascii=False) + "\n")

    def status(self, run_id: str | None = None) -> dict:
        if run_id:
            r = self.runs.get(run_id)
            return r or {"ok": False, "err": "no such run"}
        return {"active": self.active, "runs": sorted(self.runs.values(), key=lambda r: r["started"], reverse=True)[:20]}


# ───────────────────────── 入湖(拖曳 / 選檔 / 選資料夾) ─────────────────────────
def _rows_from_bytes(name: str, data: bytes) -> tuple[list[dict], str]:
    ext = Path(name).suffix.lower()
    if ext == ".jsonl":
        rows = []
        for line in data.decode("utf-8", "replace").splitlines():
            line = line.strip()
            if line:
                try:
                    r = json.loads(line)
                    if isinstance(r, dict):
                        rows.append(r)
                except ValueError:
                    pass
        return rows, "jsonl"
    if ext == ".json":
        try:
            obj = json.loads(data.decode("utf-8", "replace"))
        except ValueError:
            return [], "json(壞)"
        if isinstance(obj, list):
            return [r for r in obj if isinstance(r, dict)], "json[list]"
        if isinstance(obj, dict):
            for v in obj.values():
                if isinstance(v, list) and v and all(isinstance(x, dict) for x in v):
                    return v, "json[dict→first list]"
            return [obj], "json[dict]"
        return [], "json(非表)"
    if ext == ".csv":
        txt = data.decode("utf-8-sig", "replace")
        return list(csv.DictReader(io.StringIO(txt))), "csv"
    if ext == ".parquet":
        try:
            import duckdb
            with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as tf:
                tf.write(data)
                tmp = tf.name
            try:
                con = duckdb.connect()
                cur = con.execute("select * from read_parquet('%s')" % tmp.replace("'", "''"))
                cols = [c[0] for c in cur.description]
                rows = [dict(zip(cols, r)) for r in cur.fetchall()]
                con.close()
            finally:
                os.unlink(tmp)
            return rows, "parquet"
        except Exception as ex:  # noqa: BLE001
            return [], "parquet(壞:%s)" % str(ex)[:60]
    return [], "不支援 %s" % ext


def preview(files: list[dict]) -> dict:
    """files = [{name, b64}] → 每檔欄位 / 列數 / 建議表名與主鍵(給頁面畫下拉與勾選)。"""
    out = []
    for f in files:
        name = str(f.get("name", ""))[:200]
        try:
            data = base64.b64decode(f.get("b64", ""), validate=True)
        except Exception:  # noqa: BLE001
            out.append({"name": name, "ok": False, "err": "base64 壞"})
            continue
        rows, kind = _rows_from_bytes(name, data)
        cols = []
        for r in rows[:200]:
            for k in r:
                if k not in cols:
                    cols.append(str(k))
        stem = re.sub(r"[^A-Za-z0-9_]", "_", Path(name).stem).strip("_") or "t"
        guess = [c for c in cols if c.lower() in ("id", "ts", "at", "date", "run", "stamp", "code", "ticker", "key")][:2] or cols[:1]
        out.append({"name": name, "ok": bool(rows), "kind": kind, "rows": len(rows), "cols": cols[:60], "table": stem[:60], "keys": guess, "bytes": len(data), "sha16": hashlib.sha256(data).hexdigest()[:16]})
    return {"files": out}


def ingest(via: Path, root: Path, system: str, files: list[dict], table: str, keys: list[str], dedupe: bool = True) -> dict:
    system = str(system).upper().replace("-", "")
    if system not in SYSTEMS:
        return {"ok": False, "err": "系統不在五系統"}
    if system != "VCGC":  # L123:不代寫他系統的湖 → 暫存收件夾 + 清單
        inbox = root / "_inbox" / system
        inbox.mkdir(parents=True, exist_ok=True)
        saved = []
        for f in files:
            name = Path(str(f.get("name", "f"))).name[:200]
            data = base64.b64decode(f.get("b64", ""))
            dest = inbox / ("%s-%s" % (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"), name))
            dest.write_bytes(data)
            saved.append({"file": str(dest.relative_to(root)), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
        with (inbox / "_inbox.jsonl").open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({"at": _now(), "system": system, "table": table, "keys": keys, "files": saved}, ensure_ascii=False) + "\n")
        return {"ok": True, "mode": "inbox", "system": system, "saved": saved, "note": "VCGC 不代寫 %s 的湖(L123);檔案已落 _inbox/%s,由 %s 自己 import VIA_ParquetLake 接入" % (LABEL[system], system, LABEL[system])}
    mod = _lake_module(via)
    if not mod:
        return {"ok": False, "err": "套件 VIA_ParquetLake 不在"}
    lk = mod.Lake(root, "VCGC")
    rows_all = []
    per = []
    for f in files:
        name = str(f.get("name", ""))
        rows, kind = _rows_from_bytes(name, base64.b64decode(f.get("b64", "")))
        per.append({"name": name, "kind": kind, "rows": len(rows)})
        rows_all += rows
    if not rows_all:
        return {"ok": False, "err": "沒有可入湖的列", "files": per}
    table = mod.safe_name(table or "upload")
    keys = [k for k in keys if k] or ([list(rows_all[0].keys())[0]] if rows_all[0] else [])
    r = lk.append(table, rows_all, keys=keys, dedupe=bool(dedupe))
    st = [t for t in lk.status()["tables"] if t["table"] == table]
    return {"ok": True, "mode": "lake", "system": "VCGC", "table": table, "keys": keys, "files": per, "result": r, "table_status": st[0] if st else None,
            "catalog": str(lk.catalog), "view": "v_" + table}


# ───────────────────────── HTML(滑鼠操作 · 權杖注入) ─────────────────────────
CSS = """
:root{--bg:#f6f7f9;--fg:#1d2430;--mute:#5d6676;--line:#d9dee6;--card:#fff;--g:#1f9d55;--y:#d99a00;--r:#c62828;--n:#7a8290;--acc:#2f5fb3;--head:56px}
@media(prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#0f1318;--fg:#e6e9ee;--mute:#9aa3b2;--line:#273040;--card:#161c24;--acc:#7aa2f7;color-scheme:dark}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:clamp(14px,.35vw + 13px,15.5px)/1.5 system-ui,-apple-system,"Segoe UI","Noto Sans TC",sans-serif;overflow-wrap:anywhere}
header{position:sticky;top:0;z-index:5;height:var(--head);display:flex;align-items:center;gap:.8rem;padding:0 max(16px,env(safe-area-inset-right,0px)) 0 max(16px,env(safe-area-inset-left,0px));background:var(--card);border-bottom:1px solid var(--line)}
header h1{font-size:1.05rem;margin:0;font-weight:650;white-space:nowrap}header .meta{color:var(--mute);font-size:.82rem;margin-left:auto;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
main{padding:1rem max(16px,env(safe-area-inset-right,0px)) 2rem max(16px,env(safe-area-inset-left,0px));max-width:1400px;margin:0 auto;min-width:0}
.lamp{display:inline-block;min-width:4.6em;text-align:center;padding:.1em .55em;border-radius:999px;font-weight:650;font-size:.8rem;color:#fff;background:var(--n)}
.lamp.GREEN{background:var(--g)}.lamp.YELLOW{background:var(--y)}.lamp.RED{background:var(--r)}.lamp.GRAY{background:var(--n)}.lamp.big{font-size:1.05rem;padding:.25em .9em}
.strip{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:.7rem;margin:.8rem 0 1rem}
.tile,.panel{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:.8rem .95rem;min-width:0}.tile .t{font-weight:650;margin:.2rem 0}.tile .s,.s{color:var(--mute);font-size:.82rem}
.grid{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1.4fr);gap:.9rem}@media(max-width:900px){.grid{grid-template-columns:1fr}}
h2{font-size:1.05rem;margin:0 0 .6rem}h3{font-size:.95rem;margin:.9rem 0 .4rem}
label.f{display:block;color:var(--mute);font-size:.82rem;margin:.5rem 0 .15rem}select,button,input[type=text]{font:inherit;color:var(--fg);background:var(--card);border:1px solid var(--line);border-radius:8px;padding:.4em .7em}
select{width:100%}button{cursor:pointer}button.primary{background:var(--acc);color:#fff;border-color:var(--acc);font-weight:650}button:disabled{opacity:.5;cursor:not-allowed}
.ck{display:inline-flex;gap:.35rem;align-items:center;margin:.3rem .9rem .3rem 0;cursor:pointer}.row{display:flex;gap:.5rem;flex-wrap:wrap;align-items:center;margin:.5rem 0}
#drop{border:2px dashed var(--line);border-radius:10px;padding:1.2rem;text-align:center;color:var(--mute);margin:.5rem 0}#drop.on{border-color:var(--acc);background:rgba(47,95,179,.06)}
table{border-collapse:collapse;width:100%;font-size:.86rem}th,td{border-bottom:1px solid var(--line);padding:.3rem .45rem;text-align:left;vertical-align:top}th{color:var(--mute);font-weight:600}
pre{background:rgba(127,127,127,.1);padding:.6rem;border-radius:8px;font-size:.8rem;max-height:18rem;overflow:auto;white-space:pre-wrap}code{font-size:.85em;background:rgba(127,127,127,.12);padding:.05em .3em;border-radius:4px}
.hidden{display:none}#witness .lamp.big{margin-right:.5rem}.wrap{overflow-x:auto}a{color:var(--acc)}
"""

JS = r"""
(function(){
  var T=document.body.dataset.token, H={'Content-Type':'application/json','X-VIA-CSRF':T};
  var $=function(id){return document.getElementById(id);};
  function esc(s){return String(s==null?'':s).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}
  function lamp(l,big){return '<span class="lamp '+esc(l)+(big?' big':'')+'">'+esc(l)+'</span>';}
  function post(path,body){return fetch(path,{method:'POST',headers:H,credentials:'same-origin',body:JSON.stringify(body||{})}).then(function(r){return r.json();});}
  function get(path){return fetch(path,{credentials:'same-origin'}).then(function(r){return r.json();});}
  function refreshLamps(){return get('/lamps').then(function(d){
    $('lamps').innerHTML=d.lamps.map(function(r){return '<div class="tile">'+lamp(r.lamp)+'<div class="t">'+esc(r.title)+'</div><div class="s">'+esc(r.note)+'</div><div class="s">'+esc(r.at||'—')+'</div></div>';}).join('');
    var worst=d.lamps.reduce(function(a,r){var o={GREEN:0,YELLOW:1,GRAY:2,RED:3};return o[r.lamp]>o[a]?r.lamp:a;},'GREEN');
    $('overall').outerHTML='<span id="overall" class="lamp big '+esc(worst)+'">'+esc(worst)+'</span>';
    $('receipts').innerHTML=d.receipts.map(function(r){return '<tr><td><a href="/files/'+esc(r.rel)+'" target="_blank" rel="noopener">'+esc(r.rel)+'</a></td><td>'+esc(r.mtime)+'</td><td class="num">'+esc(r.bytes)+'</td></tr>';}).join('')||'<tr><td colspan="3" class="s">還沒有收據</td></tr>';
  });}
  var poll=null;
  function showRun(r){
    var html=lamp(r.lamp,true)+'<strong>'+esc(r.zh)+'</strong> <span class="s">'+esc(r.run_id)+' · '+esc(r.state)+(r.ended?' · 結束 '+esc(r.ended):'')+'</span>';
    html+='<table><thead><tr><th>步</th><th>rc</th><th>秒</th><th>收據</th></tr></thead><tbody>'+r.steps.map(function(s){return '<tr><td>'+esc(s.zh)+'</td><td>'+(s.rc==null?'…':lamp(s.rc===0?'GREEN':'RED')+' '+esc(s.rc))+'</td><td>'+esc(s.secs==null?'…':s.secs)+'</td><td>'+(s.receipt?'<a href="/files/'+esc(s.receipt)+'" target="_blank" rel="noopener">'+esc(s.receipt)+'</a>':'—')+'</td></tr>';}).join('')+'</tbody></table>';
    html+=r.steps.map(function(s){return s.tail?'<h3>'+esc(s.zh)+' · 輸出尾段</h3><pre>'+esc(s.tail)+'</pre>':'';}).join('');
    html+='<div class="s">log <a href="/files/'+esc(r.log.split('/VIA_Reports/')[1]?'VIA_Reports/'+r.log.split('/VIA_Reports/')[1]:'')+'" target="_blank" rel="noopener">'+esc(r.log)+'</a></div>';
    $('witness').innerHTML=html; $('witness').dataset.state=r.state; $('witness').dataset.lamp=r.lamp;
  }
  function track(run_id){ if(poll)clearInterval(poll); poll=setInterval(function(){get('/status?run='+encodeURIComponent(run_id)).then(function(r){showRun(r); if(r.state==='DONE'){clearInterval(poll);poll=null;$('run').disabled=false;refreshLamps();loadHistory();}});},700); }
  $('run').addEventListener('click',function(){
    $('run').disabled=true; $('witness').innerHTML='<span class="s">啟動中…</span>'; $('witness').dataset.state='STARTING';
    post('/run',{action:$('act').value,options:{dry:$('opt-dry').checked,open:$('opt-open').checked}}).then(function(d){ if(!d.ok){$('witness').innerHTML=lamp('RED',true)+esc(d.err||'失敗');$('witness').dataset.state='ERROR';$('run').disabled=false;return;} track(d.run_id); });
  });
  function loadHistory(){get('/status').then(function(d){$('history').innerHTML=(d.runs||[]).map(function(r){return '<tr><td>'+lamp(r.lamp)+'</td><td>'+esc(r.zh)+'</td><td>'+esc(r.started)+'</td><td>'+esc(r.rc==null?'…':r.rc)+'</td><td>'+esc(r.steps.map(function(s){return s.step+':'+s.rc;}).join(' · '))+'</td></tr>';}).join('')||'<tr><td colspan="5" class="s">本次尚無執行</td></tr>';});}
  // 入湖:拖曳 / 選檔 / 選資料夾 → 預覽 → 勾主鍵 → 入湖
  var FILES=[];
  function readFiles(list){var arr=[].slice.call(list||[]).filter(function(f){return /\.(jsonl|json|csv|parquet)$/i.test(f.name);}); if(!arr.length){$('pv').innerHTML='<span class="s">沒有支援的檔(jsonl / json / csv / parquet)</span>';return;}
    Promise.all(arr.map(function(f){return new Promise(function(res){var rd=new FileReader();rd.onload=function(){res({name:f.webkitRelativePath||f.name,b64:String(rd.result).split(',')[1]||''});};rd.readAsDataURL(f);});})).then(function(fs){FILES=fs;return post('/preview',{files:fs});}).then(renderPreview);}
  function renderPreview(d){
    var ok=d.files.filter(function(f){return f.ok;}); var cols=[]; ok.forEach(function(f){f.cols.forEach(function(c){if(cols.indexOf(c)<0)cols.push(c);});});
    var tables={}; ok.forEach(function(f){tables[f.table]=1;});
    var h='<table><thead><tr><th>檔</th><th>格式</th><th>列</th><th>欄</th></tr></thead><tbody>'+d.files.map(function(f){return '<tr><td>'+esc(f.name)+'</td><td>'+esc(f.ok?f.kind:('✗ '+(f.err||f.kind)))+'</td><td>'+esc(f.rows||0)+'</td><td>'+esc((f.cols||[]).length)+'</td></tr>';}).join('')+'</tbody></table>';
    h+='<label class="f">表名(下拉)</label><select id="tbl">'+Object.keys(tables).map(function(t){return '<option>'+esc(t)+'</option>';}).join('')+(Object.keys(tables).length>1?'<option value="__merged">merged(全部合一表)</option>':'')+'</select>';
    h+='<label class="f">主鍵(勾選;同主鍵再來 = 增量跳過)</label><div id="keys">'+cols.map(function(c){var g=ok.some(function(f){return f.keys.indexOf(c)>=0;});return '<label class="ck"><input type="checkbox" class="kc" value="'+esc(c)+'"'+(g?' checked':'')+'> '+esc(c)+'</label>';}).join('')+'</div>';
    h+='<div class="row"><label class="ck"><input type="checkbox" id="dedupe" checked> 增量(同主鍵跳過)</label><button class="primary" id="ingest"'+(ok.length?'':' disabled')+'>入湖 → '+esc($('sys').options[$('sys').selectedIndex].text)+'</button></div><div id="ingest-out"></div>';
    $('pv').innerHTML=h;
    $('ingest').addEventListener('click',function(){ $('ingest').disabled=true; var keys=[].slice.call(document.querySelectorAll('.kc:checked')).map(function(x){return x.value;});
      post('/ingest',{system:$('sys').value,files:FILES,table:$('tbl').value,keys:keys,dedupe:$('dedupe').checked}).then(function(r){ $('ingest').disabled=false;
        if(!r.ok){$('ingest-out').innerHTML=lamp('RED')+' '+esc(r.err||'失敗');return;}
        if(r.mode==='inbox'){$('ingest-out').innerHTML=lamp('YELLOW')+' '+esc(r.note)+'<pre>'+esc(JSON.stringify(r.saved,null,1))+'</pre>';}
        else{$('ingest-out').innerHTML=lamp('GREEN')+' 表 <code>'+esc(r.table)+'</code> 新入 '+esc(r.result.added)+' · 跳過 '+esc(r.result.skipped)+' · 主鍵 '+esc(r.keys.join(','))+' · 視圖 <code>'+esc(r.view)+'</code>'+(r.table_status?' · 視圖列 '+esc(r.table_status.rows_view)+' · 分片 '+esc(r.table_status.parts):'')+'<div class="s">管家 '+esc(r.catalog)+'</div>';}
        $('ingest-out').dataset.mode=r.mode||'err'; refreshLamps(); });
    });
  }
  var dz=$('drop'); dz.addEventListener('dragover',function(ev){ev.preventDefault();dz.classList.add('on');}); dz.addEventListener('dragleave',function(){dz.classList.remove('on');});
  dz.addEventListener('drop',function(ev){ev.preventDefault();dz.classList.remove('on');readFiles(ev.dataTransfer.files);});
  $('pick-files').addEventListener('click',function(){$('fi').click();}); $('pick-dir').addEventListener('click',function(){$('di').click();});
  $('fi').addEventListener('change',function(){readFiles(this.files);}); $('di').addEventListener('change',function(){readFiles(this.files);});
  $('refresh').addEventListener('click',refreshLamps);
  $('sys').addEventListener('change',function(){var b=$('ingest'); if(b)b.textContent='入湖 → '+$('sys').options[$('sys').selectedIndex].text; $('sys-note').textContent=$('sys').value==='VCGC'?'VCGC 自己的湖:直接入 Parquet + DuckDB 視圖':'他系統:檔案落 _inbox/'+$('sys').value+'(VCGC 不代寫,由該系統自己接)';});
  refreshLamps(); loadHistory();
})();
"""


def page_html(via: Path, root: Path, root_src: str, token: str) -> str:
    acts = "".join('<option value="%s">%s</option>' % (k, e(v[0])) for k, v in ACTIONS.items()) + "".join('<option value="%s">%s</option>' % (k, e(v[0])) for k, v in CHAINS.items())
    syss = "".join('<option value="%s">%s</option>' % (s, LABEL[s]) for s in SYSTEMS)
    return ("<!DOCTYPE html><html lang=\"zh-Hant\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1,viewport-fit=cover\">"
            "<title>VCGC 資料湖操作台 · %s</title><style>%s</style></head><body data-token=\"%s\">"
            "<header><span id=\"overall\" class=\"lamp big GRAY\">GRAY</span><h1>VCGC 資料湖操作台</h1><span class=\"meta\">%s · 湖根 %s(%s)· 只綁 127.0.0.1</span></header><main>"
            "<section id=\"lamps\" class=\"strip\"></section>"
            "<div class=\"grid\"><div class=\"panel\" id=\"actions\"><h2>動作(下拉 → 勾選 → 執行)</h2>"
            "<label class=\"f\">動作</label><select id=\"act\">%s</select>"
            "<div class=\"row\"><label class=\"ck\"><input type=\"checkbox\" id=\"opt-dry\"> 只看不寫(看板 / 矩陣 --no-write)</label><label class=\"ck\"><input type=\"checkbox\" id=\"opt-open\"> 完成後打開收據</label></div>"
            "<div class=\"row\"><button class=\"primary\" id=\"run\">執行</button><button id=\"refresh\">重新整理燈號</button></div>"
            "<h3>入湖(拖曳 · 選檔案 · 選資料夾)</h3><label class=\"f\">目標系統</label><select id=\"sys\">%s</select><div class=\"s\" id=\"sys-note\">VCGC 自己的湖:直接入 Parquet + DuckDB 視圖</div>"
            "<div id=\"drop\">把 .jsonl / .json / .csv / .parquet 拖到這裡</div>"
            "<div class=\"row\"><button id=\"pick-files\">選檔案…</button><button id=\"pick-dir\">選資料夾…</button><input type=\"file\" id=\"fi\" class=\"hidden\" multiple accept=\".jsonl,.json,.csv,.parquet\"><input type=\"file\" id=\"di\" class=\"hidden\" webkitdirectory directory multiple></div>"
            "<div id=\"pv\"></div></div>"
            "<div class=\"panel\"><h2>輸出見證</h2><div id=\"witness\" data-state=\"IDLE\"><span class=\"s\">選一個動作按「執行」;每步 rc · 秒 · 收據 · 輸出尾段都會列在這裡</span></div>"
            "<h3>收據(點開)</h3><div class=\"wrap\"><table><thead><tr><th>檔</th><th>更新</th><th>bytes</th></tr></thead><tbody id=\"receipts\"></tbody></table></div>"
            "<h3>本次執行紀錄</h3><div class=\"wrap\"><table><thead><tr><th>燈</th><th>動作</th><th>開始</th><th>rc</th><th>步</th></tr></thead><tbody id=\"history\"></tbody></table></div></div></div>"
            "<p class=\"s\">白名單動作 · 子行程跑倉內引擎 · 單通道 · 入湖只寫 VCGC 自己的湖(他系統 → _inbox)· 同源權杖 · 本機橋。</p>"
            "<script>%s</script></main></body></html>") % (e(_now()), CSS, e(token), e(ENGINE), e(root), e(root_src), acts, syss, JS)


# ───────────────────────── HTTP 橋 ─────────────────────────
def make_handler(via: Path, root: Path, root_src: str, token: str, runner: Runner):
    allowed_dirs = [via / "VIA_Reports", root]

    class H(BaseHTTPRequestHandler):
        server_version = "VIALakeConsole/" + VERSION

        def log_message(self, fmt, *args):  # 安靜
            pass

        def _origin(self) -> str:
            return "http://%s" % self.headers.get("Host", "")

        def _host_ok(self) -> bool:
            host = self.headers.get("Host", "")
            return host.startswith("127.0.0.1:") or host.startswith("localhost:") or host in ("127.0.0.1", "localhost")

        def _json(self, obj, code=200):
            data = json.dumps(obj, ensure_ascii=False, default=str).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)

        def _bytes(self, data: bytes, ctype: str, code=200):
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(data)

        def _trusted(self) -> bool:
            return (self._host_ok() and self.headers.get("Origin", "") == self._origin() and self.headers.get("Sec-Fetch-Site", "") == "same-origin"
                    and hmac.compare_digest(self.headers.get("X-VIA-CSRF", ""), token))

        def _drain(self):
            try:
                n = int(self.headers.get("Content-Length", "0") or 0)
                if 0 < n <= BODY_CAP:
                    self.rfile.read(n)
            except Exception:  # noqa: BLE001
                pass

        def do_GET(self):
            try:
                self._get()
            except Exception as ex:  # noqa: BLE001
                try:
                    self._json({"ok": False, "err": "server: %s" % str(ex)[:300]}, 500)
                except Exception:  # noqa: BLE001
                    pass

        def _get(self):
            u = urlparse(self.path)
            if not self._host_ok():
                return self._json({"ok": False, "err": "Host 不在本機"}, 421)
            if u.path == "/":
                return self._bytes(page_html(via, root, root_src, token).encode("utf-8"), "text/html; charset=utf-8")
            if u.path == "/ping":
                return self._json({"ok": True, "engine": ENGINE, "at": _now()})
            if u.path == "/lamps":
                return self._json({"lamps": lamps(via, root), "receipts": receipts(via), "root": str(root), "root_source": root_src})
            if u.path == "/status":
                q = parse_qs(u.query)
                return self._json(runner.status((q.get("run") or [None])[0]))
            if u.path.startswith("/files/"):
                rel = u.path[len("/files/"):]
                if ".." in rel or rel.startswith("/"):
                    return self._json({"ok": False, "err": "路徑不合法"}, 400)
                cand = [(d / rel) if not rel.startswith("VIA_Reports/") else (via / rel) for d in allowed_dirs]
                for p in cand:
                    try:
                        rp = p.resolve()
                    except OSError:
                        continue
                    if rp.is_file() and any(str(rp).startswith(str(d.resolve())) for d in allowed_dirs):
                        ext = rp.suffix.lower()
                        ctype = {".html": "text/html; charset=utf-8", ".md": "text/plain; charset=utf-8", ".json": "application/json; charset=utf-8", ".txt": "text/plain; charset=utf-8",
                                 ".log": "text/plain; charset=utf-8", ".jsonl": "text/plain; charset=utf-8", ".png": "image/png"}.get(ext, "application/octet-stream")
                        return self._bytes(rp.read_bytes(), ctype)
                return self._json({"ok": False, "err": "不在白名單夾或不存在"}, 404)
            return self._json({"ok": False, "err": "no such path"}, 404)

        def do_POST(self):
            try:
                self._post()
            except Exception as ex:  # noqa: BLE001 — 任何例外都回 JSON 500,不默默斷線(見證要看得到錯)
                try:
                    self._json({"ok": False, "err": "server: %s" % str(ex)[:300]}, 500)
                except Exception:  # noqa: BLE001
                    pass

        def _post(self):
            u = urlparse(self.path)
            if not self._host_ok():
                self._drain()
                return self._json({"ok": False, "err": "Host 不在本機"}, 421)
            if u.path not in ("/run", "/preview", "/ingest"):
                self._drain()
                return self._json({"ok": False, "err": "POST 路徑不在白名單"}, 404)
            if not self._trusted():
                self._drain()
                return self._json({"ok": False, "err": "非當次本機同源頁或權杖無效"}, 403)
            try:
                n = int(self.headers.get("Content-Length", "0") or 0)
            except ValueError:
                n = -1
            if n <= 0 or n > BODY_CAP:
                self._drain()
                return self._json({"ok": False, "err": "body 大小不合法(上限 %d MiB)" % (UPLOAD_CAP // 1048576)}, 413)
            try:
                body = json.loads(self.rfile.read(n).decode("utf-8"))
                if not isinstance(body, dict):
                    raise ValueError
            except Exception:  # noqa: BLE001
                return self._json({"ok": False, "err": "只接受 JSON 物件"}, 400)
            if u.path == "/run":
                if set(body) - {"action", "options"} or "action" not in body:
                    return self._json({"ok": False, "err": "欄位只准 action · options"}, 400)
                r = runner.start(str(body["action"]), body.get("options") if isinstance(body.get("options"), dict) else {})
                return self._json(r, 202 if r.get("ok") else (409 if r.get("kind") == "busy" else 400))
            files = body.get("files")
            if not isinstance(files, list) or not files or len(files) > 200 or not all(isinstance(f, dict) and isinstance(f.get("name"), str) and isinstance(f.get("b64"), str) for f in files):
                return self._json({"ok": False, "err": "files 要是 [{name, b64}](1–200 檔)"}, 400)
            if u.path == "/preview":
                return self._json(preview(files))
            keys = body.get("keys") if isinstance(body.get("keys"), list) else []
            r = ingest(via, root, str(body.get("system", "VCGC")), files, str(body.get("table", "")), [str(k) for k in keys][:8], bool(body.get("dedupe", True)))
            return self._json(r, 200 if r.get("ok") else 400)

    return H


def serve(via: Path, root: str | None = None, port: int = 0, open_after: bool = False, ready: list | None = None, block: bool = True):
    r, src = resolve_root(via, root)
    token = secrets.token_urlsafe(24)
    runner = Runner(via, r)
    srv = ThreadingHTTPServer(("127.0.0.1", port), make_handler(via, r, src, token, runner))
    url = "http://127.0.0.1:%d/" % srv.server_address[1]
    (via / OUT_DIR).mkdir(parents=True, exist_ok=True)
    (via / OUT_DIR / "CONSOLE_latest.json").write_text(json.dumps({"engine": ENGINE, "at": _now(), "url": url, "lake_root": str(r), "lake_root_source": src, "actions": list(ACTIONS) + list(CHAINS),
                                                                   "rule": "只綁 127.0.0.1 · 白名單動作 · 同源權杖 · 入湖只寫 VCGC 湖"}, ensure_ascii=False, indent=1), encoding="utf-8")
    print("[%s] %s · %s · 湖根 %s(%s)· Ctrl+C 停" % ("GREEN", ENGINE, url, r, src), flush=True)
    if ready is not None:
        ready.append((srv, url, token, runner))
    if open_after:
        webbrowser.open(url)
    if block:
        try:
            srv.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            srv.server_close()
    return srv


# ───────────────────────── 自測(真橋 · 本機 · 零外網) ─────────────────────────
def selftest() -> int:
    import urllib.request
    import urllib.error
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)) if note else ""))

    def req(url, method="GET", body=None, headers=None):
        data = json.dumps(body).encode("utf-8") if body is not None else None
        rq = urllib.request.Request(url, data=data, method=method, headers=headers or {})
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))  # 本機橋不走環境代理(容器 HTTPS_PROXY 會攔 127.0.0.1)
        try:
            with opener.open(rq, timeout=30) as resp:
                return resp.status, json.loads(resp.read().decode("utf-8")) if "json" in resp.headers.get("Content-Type", "") else resp.read()
        except urllib.error.HTTPError as ex:
            raw = ex.read()
            try:
                return ex.code, json.loads(raw.decode("utf-8"))
            except ValueError:
                return ex.code, raw
    with tempfile.TemporaryDirectory(prefix="via_console_") as td:
        via = Path(td) / "VeritasIntelligenceAnalytics"
        (via / "supportive modules").mkdir(parents=True)
        (via / "docs/handoff/ai").mkdir(parents=True)
        (via / "supportive modules" / "VIA_ParquetLake_v0100.py").write_text((VIA / "supportive modules" / "VIA_ParquetLake_v0100.py").read_text(encoding="utf-8"), encoding="utf-8")
        (via / "docs/handoff/ai" / "VIA_DailyBackup_v0100.py").write_text("import sys\nprint('[YELLOW] fake backup check')\nsys.exit(0)\n", encoding="utf-8")
        (via / "VIA_Reports/backup").mkdir(parents=True)
        (via / "VIA_Reports/backup/CHECK_latest.json").write_text(json.dumps({"lamp": "YELLOW", "at": "2026-11-10T01:00:00Z", "meaning": "fixture"}), encoding="utf-8")
        (via / "VIA_Reports/backup/CHECK_latest.md").write_text("# fixture\n", encoding="utf-8")
        ready = []
        srv = serve(via, None, 0, False, ready, block=False)
        th = threading.Thread(target=srv.serve_forever, daemon=True)
        th.start()
        try:
            _, url, token, runner = ready[0]
            origin = url.rstrip("/")
            good = {"Content-Type": "application/json", "Origin": origin, "Sec-Fetch-Site": "same-origin", "X-VIA-CSRF": token}
            code, page = req(url)
            chk("ⓐ GET / 回頁:權杖注入 · 下拉(動作 · 系統)· 勾選 · 拖曳區 · 選檔 / 選資料夾(webkitdirectory)· 見證面板 · 一支 script",
                code == 200 and token in page.decode("utf-8") and all(k in page.decode("utf-8") for k in ('id="act"', 'id="sys"', 'id="opt-dry"', 'id="drop"', 'webkitdirectory', 'id="witness"', 'id="run"')) and page.decode("utf-8").count("<script>") == 1)
            code, d = req(url + "lamps")
            chk("ⓑ GET /lamps:四盞(備份 YELLOW · 看板 GRAY · 矩陣 GRAY · VCGC 湖 GRAY)+ 收據 1 份", code == 200 and [r["lamp"] for r in d["lamps"]] == ["YELLOW", "GRAY", "GRAY", "GRAY"] and len(d["receipts"]) == 1)
            code, d = req(url + "run", "POST", {"action": "backup_check"}, {"Content-Type": "application/json"})
            chk("ⓒ POST 無同源 / 權杖 → 403", code == 403 and not d["ok"])
            code, d = req(url + "run", "POST", {"action": "backup_check"}, {**good, "X-VIA-CSRF": "wrong"})
            chk("ⓓ 權杖錯 → 403", code == 403)
            code, d = req(url + "run", "POST", {"action": "rm -rf"}, good)
            chk("ⓔ 動作不在白名單 → 400", code == 400 and d["kind"] == "unknown_action")
            code, d = req(url + "run", "POST", {"action": "backup_check", "extra": 1}, good)
            chk("ⓕ 多餘欄位 → 400(嚴格 body)", code == 400)
            code, d = req(url + "run", "POST", {"action": "backup_check"}, good)
            rid = d.get("run_id")
            chk("ⓖ 白名單動作 → 202 + run_id", code == 202 and d["ok"] and rid)
            for _ in range(100):
                _, st = req(url + "status?run=" + rid)
                if st.get("state") == "DONE":
                    break
                time.sleep(0.1)
            chk("ⓗ 子行程跑完:rc 0 · GREEN · 收據 CHECK_latest.json · log 落盤 · 帳 1 行", st["state"] == "DONE" and st["rc"] == 0 and st["lamp"] == "GREEN" and st["receipts"] == ["VIA_Reports/backup/CHECK_latest.json"]
                and Path(st["log"]).exists() and (via / OUT_DIR / "console_ledger.jsonl").exists(), {k: st[k] for k in ("rc", "lamp")})
            code, d = req(url + "run", "POST", {"action": "lake_matrix"}, good)
            chk("ⓘ 引擎不在(矩陣未放入夾具)→ 202 後步 rc 127 · 整件 RED(不假綠)", code == 202 or True)
            rid2 = d.get("run_id")
            for _ in range(60):
                _, st2 = req(url + "status?run=" + rid2)
                if st2.get("state") == "DONE":
                    break
                time.sleep(0.1)
            ok[-1] = st2["state"] == "DONE" and st2["steps"][0]["rc"] == 127 and st2["lamp"] == "RED"
            print("  [%s] ⓘ(補判)引擎不在 → rc 127 · RED" % ("OK" if ok[-1] else "FAIL"))
            files = [{"name": "ledger.jsonl", "b64": base64.b64encode(b'{"ts":"2026-11-10T00:00:00Z","id":"a","n":1}\n{"ts":"2026-11-10T00:00:01Z","id":"b","n":2}\n').decode()},
                     {"name": "x.csv", "b64": base64.b64encode(b"ts,id,n\n2026-11-10T00:00:02Z,c,3\n").decode()}]
            code, d = req(url + "preview", "POST", {"files": files}, good)
            chk("ⓙ /preview:jsonl 2 列 · csv 1 列 · 欄 ts/id/n · 建議主鍵 ts,id · 表名由檔名", code == 200 and [f["rows"] for f in d["files"]] == [2, 1] and d["files"][0]["cols"] == ["ts", "id", "n"] and d["files"][0]["keys"] == ["ts", "id"] and d["files"][0]["table"] == "ledger")
            code, d = req(url + "ingest", "POST", {"system": "VCGC", "files": files, "table": "ledger", "keys": ["ts", "id"], "dedupe": True}, good)
            chk("ⓚ /ingest VCGC:3 列入湖 · 視圖 v_ledger · 視圖列 3", code == 200 and d["ok"] and d["mode"] == "lake" and d["result"]["added"] == 3 and d["view"] == "v_ledger" and d["table_status"]["rows_view"] == 3, d.get("result"))
            code, d = req(url + "ingest", "POST", {"system": "VCGC", "files": files, "table": "ledger", "keys": ["ts", "id"], "dedupe": True}, good)
            chk("ⓛ 同檔再入 → 增量 0 新入 3 跳過", d["result"]["added"] == 0 and d["result"]["skipped"] == 3)
            code, d = req(url + "ingest", "POST", {"system": "VDF", "files": files, "table": "ledger", "keys": ["id"], "dedupe": True}, good)
            root = resolve_root(via)[0]
            chk("ⓜ 他系統(VDF)入湖 → 不代寫:落 _inbox/VDF 2 檔 + 清單 · VDF 湖夾不建", code == 200 and d["mode"] == "inbox" and len(d["saved"]) == 2 and (root / "_inbox" / "VDF" / "_inbox.jsonl").exists() and not (root / "VDF").exists())
            code, d = req(url + "files/VIA_Reports/backup/CHECK_latest.md")
            code2, d2 = req(url + "files/../../etc/passwd")
            code3, _ = req(url + "files/VIA_Reports/../../supportive%20modules/VIA_ParquetLake_v0100.py")
            chk("ⓝ /files 白名單:收據可讀 · .. 擋 400 · 越夾 404", code == 200 and b"fixture" in d and code2 == 400 and code3 in (400, 404))
            _, l2 = req(url + "lamps")
            chk("ⓞ 入湖後燈:VCGC 湖 GREEN(1 表)", [r for r in l2["lamps"] if r["key"] == "vcgc_lake"][0]["lamp"] == "GREEN")
            chk("ⓟ CONSOLE_latest.json 落檔 · url 只在 127.0.0.1", (via / OUT_DIR / "CONSOLE_latest.json").exists() and url.startswith("http://127.0.0.1:"))
        finally:
            srv.shutdown()
            srv.server_close()
    src = Path(__file__).read_text(encoding="utf-8")
    chk("ⓠ 邊界:只綁 127.0.0.1 · 不直連外(無 requests / socket 匯入)· 子行程只跑白名單引擎(sys.executable + 倉內尾版 · 無 shell)",
        '("127.0.0.1", port)' in src and not re.search(r"^\s*(import|from)\s+(requests|socket)\b", src, re.M) and not re.search(r"shell\s*=\s*True", src.split("def selftest()")[0]) and "sys.executable, str(eng)" in src)
    bad = len(ok) - sum(ok)
    print("[%s] %s selftest · %d/%d" % ("PASS" if not bad else "FAIL", ENGINE, sum(ok), len(ok)), flush=True)
    return 0 if not bad else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="VIA_LakeConsole", description=__doc__.splitlines()[0])
    ap.add_argument("verb", nargs="?", default="serve", choices=["serve", "selftest"])
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--port", type=int, default=0, help="0 = 隨機空埠(預設);桌機可指定如 8766")
    ap.add_argument("--root", default=None)
    ap.add_argument("--via", default=None)
    ap.add_argument("--open", action="store_true", help="(預設即開)啟動後自動跳出 HTML U/I")
    ap.add_argument("--no-open", action="store_true", help="不自動開瀏覽器(CI / 容器 / 背景服務用)")
    a = ap.parse_args(argv)
    if a.selftest or a.verb == "selftest":
        return selftest()
    via = Path(a.via).resolve() if a.via else VIA
    if (via / "VeritasIntelligenceAnalytics").is_dir():
        via = via / "VeritasIntelligenceAnalytics"
    serve(via, a.root, a.port, open_after=not a.no_open)  # 操作員 2026-11-10:「啟動後自動跳出 HTML U/I」→ 預設開
    return 0


if __name__ == "__main__":
    sys.exit(main())
