#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CGC_MDL128_SystemCharter — 系統結構總冊引擎(批343;操作員令「以中央治理台統管全規則 SSOT

批354 Zero-Hydra 改號(雲端線 MDL123 DataHome/124 BridgeSweeper/125 FixAll/126 NetBench 先發先得已在 main):本檔原號 CGC_MDL124_SystemCharter→CGC_MDL128_SystemCharter;原件 byte-exact 於 references/intake/VIA_Batch347_Bundle_b354;互引全數同步改號;功能零變。
與所有引擎模組;輸入參數最少化並自動化;左輸入右顯示;多頁籤指標;工作流圖;DB 已移本機,
測試只用一兩日」)
====================================================================
職權:
  ①讀 VIA_SystemCharter_v*.json(結構 SSOT;七域+治理核);逐項驗引擎/頁/任務/DB 在位
    (零發明:缺=PLANNED/NOT_GENERATED/DB_MISSING 誠實標,不假亮)
  ②DuckDB 真探(duckdb 可匯入且檔在=讀表名/列數/末日;否則誠實缺)
  ③產 VIA_UI_SystemCharter_v0100.html:左欄=七域導航+該域「最少輸入」(其餘自動並標來源);
    右欄=六頁籤(總覽/輸入/引擎/頁面/指標/工作流);工作流=內嵌 SVG DAG(RYG 節點;零 CDN)
  ④--probe [--days N]:兩日試鏈(backfill/global 帶 --start/--end;分析引擎自推窗)
    每步=獨立子行程+逾時+log;寫 probe 報告;非 --go 只列計畫不派工
  ⑤--selftest 八檢;--open 自動跳出(file://;零 server)
v0100→v0101(批347):產物經 apply_type_scale;自測 +⑨
用法:python3 CGC_MDL128_SystemCharter_v0101.py [--open] [--probe --days 2 [--go]] [--selftest]
"""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0100] =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_support = str(_sa_p / "supportive modules")
            if _sa_support not in _sa_sys.path:
                _sa_sys.path.insert(0, _sa_support)
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa
except Exception:
    VIA_ACCEL = None
# ===== [VIA:ACCEL-BRIDGE:END] =====
import glob
import html
import importlib.util
import json
import os
import re
import subprocess
import sys
import time
import webbrowser
from datetime import date, datetime, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
UI = VIA / "supportive modules" / "ui_support"
OUT = UI / "VIA_UI_SystemCharter_v0100.html"
PROBE_ROOT = VIA / "VIA_Reports" / "charter_probe"



# ===== 批347 字階守恆(全頁族統一;來源=VIA_UISpec 尾版六階;越階值就近收斂到階) =====
def _type_scale():
    try:
        import json as _j
        c = sorted(Path(__file__).resolve().parent.glob("VIA_UISpec_v*.json"))
        th = _j.loads(c[-1].read_text(encoding="utf-8")).get("theme", {}) if c else {}
        steps = [("fs_xs", 9.0), ("fs_s", 10.5), ("fs", 11.5), ("fs_m", 12.5), ("fs_l", 14.0), ("fs_xl", 16.0)]
        return [(k, float(str(th.get(k, d)).replace("px", ""))) for k, d in steps]
    except Exception:
        return [("fs_xs", 9.0), ("fs_s", 10.5), ("fs", 11.5), ("fs_m", 12.5), ("fs_l", 14.0), ("fs_xl", 16.0)]


def apply_type_scale(page: str) -> str:
    """把 <style> 內所有 px 字級收斂到六階(最大 fs_xl);inline style 同理;零其他改動"""
    steps = _type_scale()
    def snap(v):
        v = float(v)
        for k, px in steps:
            if v <= px:
                return px
        return steps[-1][1]
    def fmt(x):
        return (str(x).rstrip("0").rstrip(".") if "." in str(x) else str(x)) + "px"
    def fix_style(m):
        css = m.group(1)
        css = re.sub(r"(font-size\s*:\s*)([0-9.]+)px", lambda x: x.group(1) + fmt(snap(x.group(2))), css)
        css = re.sub(r"(font\s*:\s*)([0-9.]+)px", lambda x: x.group(1) + fmt(snap(x.group(2))), css)
        return "<style>" + css + "</style>"
    page = re.sub(r"<style>(.*?)</style>", fix_style, page, flags=re.S)
    page = re.sub(r'(style="[^"]*font-size\s*:\s*)([0-9.]+)px', lambda x: x.group(1) + fmt(snap(x.group(2))), page)
    # JS-built elements (cssText strings) carry font:NNpx too; snap them so the runtime DOM obeys the scale
    page = re.sub(r"(font(?:-size)?\s*:\s*)([0-9.]+)px", lambda x: x.group(1) + fmt(snap(x.group(2))), page)
    return page

def _latest(pat: str) -> str:
    hits = sorted(glob.glob(str(VIA / pat)))
    return hits[-1] if hits else ""


def _charter() -> dict:
    c = sorted(HERE.glob("VIA_SystemCharter_v*.json"))
    if not c:
        return {}
    return json.loads(c[-1].read_text(encoding="utf-8"))


def _mod(pat: str):
    p = _latest("supportive modules/registry/" + pat)
    if not p:
        return None
    spec = importlib.util.spec_from_file_location("charter_dep", p)
    m = importlib.util.module_from_spec(spec)
    sys.modules["charter_dep"] = m
    spec.loader.exec_module(m)
    return m


# ---------------------------------------------------------------------
# 真值直取
# ---------------------------------------------------------------------
def _tasks() -> dict:
    try:
        return _mod("CGC_MDL095_DeckServer_v0*.py").task_registry()
    except Exception:
        return {}


def _db_probe(rel: str) -> dict:
    p = VIA / rel
    out = {"path": rel, "present": p.exists(), "kind": "dir" if p.is_dir() else "file",
           "size_mb": round(p.stat().st_size / 1e6, 1) if p.is_file() else None,
           "tables": [], "rows": None, "max_date": "", "note": ""}
    if not p.exists():
        out["note"] = "DB_MISSING(誠實;DB 已移本機=請於本機再生本頁)"
        return out
    if p.is_dir():
        out["rows"] = sum(1 for f in p.iterdir() if f.is_file())
        return out
    if p.suffix.lower() != ".duckdb":
        return out
    try:
        import duckdb  # type: ignore
    except Exception:
        out["note"] = "duckdb 模組缺(誠實;無法讀表)"
        return out
    try:
        con = duckdb.connect(str(p), read_only=True)
        tabs = [r[0] for r in con.execute("select table_name from information_schema.tables where table_schema='main'").fetchall()]
        out["tables"] = tabs[:20]
        tot = 0
        mx = ""
        for t in tabs[:20]:
            try:
                n = con.execute(f'select count(*) from "{t}"').fetchone()[0]
                tot += n
                cols = [r[1] for r in con.execute(f'pragma table_info("{t}")').fetchall()]
                dc = next((c for c in cols if c.lower() in ("date", "trade_date", "dt", "ymd")), None)
                if dc:
                    m = con.execute(f'select max("{dc}") from "{t}"').fetchone()[0]
                    mx = max(mx, str(m) if m is not None else "")
            except Exception:
                pass
        out["rows"] = tot
        out["max_date"] = mx
        con.close()
    except Exception as exc:
        out["note"] = f"讀取失敗(誠實):{exc}"[:120]
    return out


def evaluate(ch: dict) -> dict:
    tasks = _tasks()
    def eng_rows(paths):
        rows = []
        for g in paths:
            f = _latest(g)
            rows.append({"glob": g, "path": os.path.relpath(f, VIA) if f else "", "present": bool(f),
                         "ver": (re.search(r"_v(\d{4})", Path(f).name).group(1) if f and re.search(r"_v(\d{4})", Path(f).name) else "")})
        return rows
    def page_rows(names):
        rows = []
        for n in names:
            p = UI / n
            rows.append({"page": n, "present": p.exists(), "kb": round(p.stat().st_size / 1024) if p.exists() else 0})
        return rows
    def task_rows(names):
        return [{"task": t, "present": t in tasks, "zh": (tasks.get(t) or {}).get("zh", "") if isinstance(tasks.get(t), dict) else "",
                 "range": bool((tasks.get(t) or {}).get("range")) if isinstance(tasks.get(t), dict) else False} for t in names]
    def readiness(e, pg, tk, db):
        ep = sum(1 for r in e if r["present"]); pp = sum(1 for r in pg if r["present"])
        tp = sum(1 for r in tk if r["present"]); dp = sum(1 for r in db if r["present"])
        if e and ep == 0:
            return "RED"
        if (e and ep < len(e)) or (db and dp < len(db)) or (pg and pp < len(pg)):
            return "YELLOW"
        return "GREEN"
    out = {"core": None, "domains": []}
    core = ch.get("core", {})
    ce = eng_rows(core.get("engines", [])); cp = page_rows(core.get("pages", [])); ct = task_rows(core.get("tasks", []))
    rules = [{"zh": r["zh"], "path": r["path"], "present": bool(_latest(r["path"])), "file": os.path.basename(_latest(r["path"])) if _latest(r["path"]) else ""} for r in core.get("rule_ssot", [])]
    out["core"] = {**core, "engine_rows": ce, "page_rows": cp, "task_rows": ct, "rule_rows": rules,
                   "state": readiness(ce, cp, ct, []), "db_rows": []}
    for d in ch.get("domains", []):
        e = eng_rows(d.get("engines", [])); pg = page_rows(d.get("pages", [])); tk = task_rows(d.get("tasks", []))
        db = [_db_probe(x) for x in d.get("db", [])]
        sp = [{"path": s, "present": (VIA / s).exists() or (Path.home() / "Downloads" / Path(s).name).exists()} for s in d.get("standalone_pages", [])]
        out["domains"].append({**d, "engine_rows": e, "page_rows": pg, "task_rows": tk, "db_rows": db, "standalone_rows": sp,
                               "state": readiness(e, pg, tk, db)})
    out["task_count"] = len(tasks)
    return out


# ---------------------------------------------------------------------
# 兩日試鏈
# ---------------------------------------------------------------------
def probe(ch: dict, days: int = 2, go: bool = False, timeout: int = 1800) -> dict:
    tasks = _tasks()
    D = date.today()
    D0 = D - timedelta(days=days)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = PROBE_ROOT / f"PROBE_{stamp}"
    (run_dir / "logs").mkdir(parents=True, exist_ok=True)
    plan = []
    seen = set()
    for d in ch.get("domains", []):
        for step in d.get("probe_2day", []):
            tid = step[0]
            # a task shared by two domains (group_class: TWSTOCK+ROTATION) runs once
            key = tuple(step)
            if key in seen:
                plan.append({"domain": d["id"], "task": tid, "argv": [], "state": "DEDUP(已由前域排程)", "rc": None, "secs": 0})
                continue
            seen.add(key)
            spec = tasks.get(tid)
            if not isinstance(spec, dict) or not spec.get("argv"):
                plan.append({"domain": d["id"], "task": tid, "argv": [], "state": "TASK_MISSING", "rc": None, "secs": 0})
                continue
            argv = list(spec["argv"]) + [a.replace("{D-2}", D0.isoformat()).replace("{D}", D.isoformat()) for a in step[1:]]
            plan.append({"domain": d["id"], "task": tid, "argv": argv, "state": "PLANNED", "rc": None, "secs": 0})
    if go:
        for st in plan:
            if st["state"] != "PLANNED":
                continue
            log = run_dir / "logs" / f'{st["domain"]}_{st["task"]}.log'
            t0 = time.time()
            try:
                with open(log, "w", encoding="utf-8", errors="replace") as lf:
                    p = subprocess.run(st["argv"], stdout=lf, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                                       cwd=str(VIA), timeout=timeout, env=dict(os.environ, PYTHONIOENCODING="utf-8"))
                st["rc"] = p.returncode
                st["state"] = "OK" if p.returncode == 0 else "FAIL"
            except subprocess.TimeoutExpired:
                st["rc"] = -9; st["state"] = "TIMEOUT"
            except Exception as exc:
                st["rc"] = -2; st["state"] = "ERROR"; st["note"] = str(exc)[:120]
            st["secs"] = int(time.time() - t0)
            st["log"] = str(log)
    res = {"schema": "VIA_CharterProbe/1.0", "stamp": stamp, "window": [D0.isoformat(), D.isoformat()], "days": days,
           "mode": "EXECUTED" if go else "PLAN_ONLY(--go 才派工)", "steps": plan, "run_dir": str(run_dir)}
    (run_dir / "probe.json").write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    return res


# ---------------------------------------------------------------------
# 版型(承 MDL116 版型五律;左輸入右顯示;多頁籤;燈號)
# ---------------------------------------------------------------------
CSS = """
:root{--bg:#f5f5f2;--paper:#fff;--paper2:#fafaf8;--ink:#1f2530;--ink2:#3c4658;--mut:#6d7688;--mut2:#9aa2b1;--line:#dcdfe6;--soft:#eef0ee;--acc:#3e6b8f;--ok:#4f8f6b;--warn:#b58a3e;--bad:#b05c4d;--rail-w:250px;--hd:84px;--ft:30px}
*{box-sizing:border-box}html{scrollbar-width:thin;scrollbar-color:rgba(60,70,88,.28) transparent}*::-webkit-scrollbar{width:6px;height:6px}*::-webkit-scrollbar-thumb{background:rgba(60,70,88,.28);border-radius:3px}
body{margin:0;background:var(--bg);color:var(--ink);font:12px/1.45 "Segoe UI","Microsoft JhengHei",-apple-system,sans-serif}
.app{display:flex;min-height:100vh}
.rail{width:var(--rail-w);min-width:var(--rail-w);background:var(--paper);border-right:1px solid var(--line);position:sticky;top:0;height:100vh;overflow-y:auto;display:flex;flex-direction:column}
.brand{height:var(--hd);padding:0 14px;display:flex;flex-direction:column;justify-content:center;border-bottom:1px solid var(--line);position:sticky;top:0;background:var(--paper);z-index:5}
.brand .seal{display:inline-block;width:28px;height:28px;line-height:28px;text-align:center;border-radius:3px;background:#c96b5a;color:#fff;font-weight:800;font-size:15px;margin-right:8px}
.brand h1{font-size:15px;margin:0;display:flex;align-items:center}.brand .sub{font-size:9px;letter-spacing:.14em;color:var(--mut2);text-transform:uppercase;margin-top:2px}
.nav{padding:6px 8px}.nav a{display:flex;align-items:center;gap:8px;padding:6px 8px;border-radius:5px;color:var(--ink2);text-decoration:none;font-size:11.5px}.nav a:hover{background:var(--soft)}.nav a.on{background:var(--soft);color:var(--ink);font-weight:700}
.nav .n{font-family:Consolas,monospace;font-size:10px;color:var(--mut2);width:22px}.nav .s{display:inline-block;width:20px;height:20px;line-height:20px;text-align:center;border-radius:3px;background:#eee;font-size:11px;font-weight:700;color:var(--ink2)}
.led{display:inline-block;width:8px;height:8px;border-radius:50%;background:var(--mut2);margin-left:auto;box-shadow:0 0 0 2px rgba(0,0,0,.04)}.led.ok{background:var(--ok)}.led.warn{background:var(--warn)}.led.bad{background:var(--bad)}.led.off{opacity:.45}
.rin{margin:6px 8px;padding:7px 9px;border:1px solid var(--line);border-radius:6px;background:var(--paper2)}.rin .t{font-size:8.5px;letter-spacing:.18em;color:var(--mut2);font-weight:700;margin-bottom:5px}
.rin label{display:block;font-size:9.5px;color:var(--mut);margin:5px 0 1px}.rin input,.rin select{width:100%;font:11px/1.4 inherit;padding:4px 6px;border:1px solid var(--line);border-radius:4px;background:var(--paper);color:var(--ink)}
.rin .auto{font-family:Consolas,monospace;font-size:10px;color:var(--ink2);background:var(--paper);border:1px dashed var(--line);border-radius:4px;padding:4px 6px}
.rin .hint{font-size:9px;color:var(--mut2);margin-top:5px;line-height:1.35}.rin .btn{display:block;width:100%;margin-top:7px;padding:6px;font:11px/1 inherit;font-weight:700;color:#fff;background:var(--acc);border:0;border-radius:4px;cursor:pointer}
.railfoot{margin-top:auto;padding:8px 14px;border-top:1px solid var(--line);font-size:9.5px;color:var(--mut2);font-family:Consolas,monospace}
.main{flex:1;min-width:0;padding:0 18px}
.hdwrap{position:sticky;top:0;z-index:6;background:var(--bg);height:var(--hd);display:flex;flex-direction:column;justify-content:flex-end;padding-top:6px}
.crumb{font-size:9.5px;color:var(--mut);letter-spacing:.04em;margin-bottom:4px}.head{display:flex;align-items:flex-end;gap:14px;flex-wrap:wrap;border-bottom:2px solid var(--ink);padding-bottom:6px;margin-bottom:9px}
.head h2{font-size:22px;margin:0;line-height:1.1}.head h2 small{display:block;font-size:9.5px;letter-spacing:.16em;color:var(--mut2);font-weight:400;margin-top:2px}
.spec{margin-left:auto;display:flex;gap:14px}.spec .k{font-size:8.5px;letter-spacing:.12em;color:var(--mut2)}.spec .v{font-family:Consolas,monospace;font-size:11px;font-weight:700}
.tabs{display:flex;gap:4px;border-bottom:1px solid var(--line);margin:6px 0 10px;position:sticky;top:var(--hd);background:var(--bg);z-index:4}
.tabs button{font:11px/1 inherit;padding:7px 12px;border:1px solid transparent;border-bottom:0;background:transparent;color:var(--mut);cursor:pointer;border-radius:5px 5px 0 0}.tabs button.on{background:var(--paper);border-color:var(--line);color:var(--ink);font-weight:700}
.pane{display:none}.pane.on{display:block}
.card{background:var(--paper);border:1px solid var(--line);border-radius:6px;padding:10px 12px;margin-bottom:10px}.card h3{margin:0 0 6px;font-size:12px}.card h3 small{margin-left:8px;font-size:9px;letter-spacing:.14em;color:var(--mut2);font-weight:400}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:10px}.grid .card{margin:0}
.kv{display:grid;grid-template-columns:auto 1fr;gap:3px 12px;font-size:11px}.kv .k{color:var(--mut);font-size:9.5px;letter-spacing:.06em;font-weight:700}
table{width:100%;border-collapse:collapse;font-size:10.5px}th{font-size:9px;letter-spacing:.1em;color:var(--mut2);text-align:left;padding:4px 6px;border-bottom:1px solid var(--line)}td{padding:4px 6px;border-bottom:1px solid #eeece7;vertical-align:top;white-space:normal;word-break:break-all}
.mono{font-family:Consolas,monospace}.dim{color:var(--mut2)}
.pill{display:inline-block;font-size:9px;font-weight:700;padding:1px 6px;border-radius:3px;border:1px solid var(--line);color:var(--mut)}.pill.ok{color:var(--ok);border-color:var(--ok)}.pill.warn{color:var(--warn);border-color:var(--warn)}.pill.bad{color:var(--bad);border-color:var(--bad)}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:8px;margin-bottom:10px}.stat{background:var(--paper);border:1px solid var(--line);border-radius:6px;padding:8px 10px}.stat .n{font-size:20px;font-weight:800;line-height:1}.stat .l{font-size:9px;letter-spacing:.1em;color:var(--mut2);margin-top:3px}
.foot{position:sticky;bottom:0;background:var(--bg);height:var(--ft);display:flex;align-items:center;border-top:1px solid var(--line);font-size:9.5px;color:var(--mut2);font-family:Consolas,monospace;margin-top:10px}
svg text{font-family:"Segoe UI","Microsoft JhengHei",sans-serif}
@media(max-width:900px){.grid{grid-template-columns:1fr}.rail{position:fixed;left:0;z-index:20;transform:translateX(-100%)}.rail.open{transform:none}}
"""


def _led(state):
    return {"GREEN": "ok", "YELLOW": "warn", "RED": "bad"}.get(state, "off")


def _workflow_svg(ch: dict, ev: dict) -> str:
    st = {ev["core"]["id"]: ev["core"]["state"]}
    st.update({d["id"]: d["state"] for d in ev["domains"]})
    zh = {ev["core"]["id"]: ev["core"]["zh"]}
    zh.update({d["id"]: d["zh"] for d in ev["domains"]})
    pos = {"CGC": (60, 40), "VDF": (60, 190), "TWSTOCK": (300, 120), "REVENUE": (300, 260), "ETF": (300, 400),
           "ROTATION": (540, 190), "VAP": (780, 260), "VRN": (60, 400)}
    col = {"GREEN": "#4f8f6b", "YELLOW": "#b58a3e", "RED": "#b05c4d"}
    parts = ['<svg viewBox="0 0 900 480" width="100%" style="max-height:480px;background:var(--paper2);border:1px solid var(--line);border-radius:6px">',
             '<defs><marker id="ar" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#9aa2b1"/></marker></defs>']
    for a, b, lab in ch.get("workflow", {}).get("edges", []):
        if a not in pos or b not in pos:
            continue
        x1, y1 = pos[a]; x2, y2 = pos[b]
        x1 += 100; y1 += 22; y2 += 22
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#c9ccd3" stroke-width="1.4" marker-end="url(#ar)"/>')
        parts.append(f'<text x="{mx}" y="{my - 4}" font-size="9" fill="#6d7688" text-anchor="middle">{html.escape(lab)}</text>')
    for k, (x, y) in pos.items():
        s = st.get(k, "OFF")
        c = col.get(s, "#9aa2b1")
        parts.append(f'<rect x="{x}" y="{y}" width="100" height="44" rx="6" fill="#fff" stroke="{c}" stroke-width="2"/>')
        parts.append(f'<circle cx="{x + 12}" cy="{y + 12}" r="4" fill="{c}"/>')
        parts.append(f'<text x="{x + 22}" y="{y + 16}" font-size="10" font-weight="700" fill="#1f2530">{k}</text>')
        parts.append(f'<text x="{x + 8}" y="{y + 34}" font-size="10" fill="#3c4658">{html.escape(zh.get(k, ""))}</text>')
    parts.append('</svg>')
    return "".join(parts)


def render(ch: dict, ev: dict) -> str:
    e = html.escape
    core = ev["core"]
    all_d = [core] + ev["domains"]
    ne = sum(sum(1 for r in d["engine_rows"] if r["present"]) for d in all_d)
    nE = sum(len(d["engine_rows"]) for d in all_d)
    npg = sum(sum(1 for r in d["page_rows"] if r["present"]) for d in all_d)
    nP = sum(len(d["page_rows"]) for d in all_d)
    ntk = sum(sum(1 for r in d["task_rows"] if r["present"]) for d in all_d)
    nT = sum(len(d["task_rows"]) for d in all_d)
    ndb = sum(sum(1 for r in d["db_rows"] if r["present"]) for d in ev["domains"])
    nD = sum(len(d["db_rows"]) for d in ev["domains"])
    nin = sum(len(d.get("minimal_inputs", [])) for d in ev["domains"])
    green = sum(1 for d in all_d if d["state"] == "GREEN")

    nav = "".join(f'<a href="#" data-d="{d["id"]}" class="{"on" if i == 0 else ""}"><span class="n">{i:02d}</span><span class="s">{e(d.get("seal", "理"))}</span>{e(d["zh"])} <span class="mono dim" style="font-size:9px">{d["id"]}</span><span class="led {_led(d["state"])}"></span></a>'
                  for i, d in enumerate(all_d))

    def rail_inputs(d):
        mi = d.get("minimal_inputs", [])
        auto = d.get("auto_params", [])
        body = ""
        if not mi:
            body += '<div class="auto"><span class="led ok" style="margin:0 6px 0 0"></span>零人工輸入:全部自動推導</div>'
        for m in mi:
            if m["key"] in ("start", "end"):
                body += f'<label>{e(m["zh"])} <span class="mono dim">auto: {e(m["auto"])}</span></label><input type="date" name="{m["key"]}" data-d="{d["id"]}">'
            elif m["key"] == "files":
                body += f'<label>{e(m["zh"])} <span class="mono dim">{e(m["auto"])}</span></label><input type="file" multiple data-d="{d["id"]}" accept=".pdf,.docx">'
            else:
                body += f'<label>{e(m["zh"])} <span class="mono dim">auto: {e(m["auto"])}</span></label><input type="text" name="{m["key"]}" data-d="{d["id"]}" placeholder="留空=自動">'
        if auto:
            body += '<label>自動參數 AUTO</label><div class="auto">' + "<br>".join(e(a) for a in auto[:6]) + '</div>'
        body += f'<div class="hint">輸入政策:每域≤3 人工欄;此域 {len(mi)} 欄 · 任務=' + e(", ".join(d.get("tasks", []))) + '</div>'
        body += '<button class="btn" type="button" onclick="VIA_plan(this)">產生執行計畫(不派工)</button><div class="auto" style="display:none;margin-top:6px;white-space:pre-wrap" data-out></div>'
        return f'<div class="rin" data-d="{d["id"]}" style="display:{"block" if d is all_d[0] else "none"}"><div class="t">INPUT · {e(d["id"])} 最少輸入</div>{body}</div>'
    rails = "".join(rail_inputs(d) for d in all_d)

    def tbl(head, rows):
        return f'<table><tr>{"".join(f"<th>{h}</th>" for h in head)}</tr>{rows or "<tr><td colspan=9 class=dim>—</td></tr>"}</table>'
    def pill(p, ok="在位", bad="缺"):
        return f'<span class="pill {"ok" if p else "bad"}">{ok if p else bad}</span>'

    panes = ""
    for i, d in enumerate(all_d):
        eng = "".join(f'<tr><td class="mono">{e(r["path"] or r["glob"])}</td><td class="mono">{e(r["ver"])}</td><td>{pill(r["present"], "在位", "PLANNED")}</td></tr>' for r in d["engine_rows"])
        pgs = "".join(f'<tr><td class="mono">{e(r["page"])}</td><td class="mono">{r["kb"]} KB</td><td>{pill(r["present"], "在位", "NOT_GENERATED")}</td></tr>' for r in d["page_rows"])
        tks = "".join(f'<tr><td class="mono">{e(r["task"])}</td><td>{e(r["zh"])}</td><td class="mono">{"起訖" if r["range"] else "自推"}</td><td>{pill(r["present"], "白名單", "任務缺")}</td></tr>' for r in d["task_rows"])
        dbs = "".join(f'<tr><td class="mono">{e(r["path"])}</td><td>{pill(r["present"], "在位", "DB_MISSING")}</td><td class="mono">{r["size_mb"] if r["size_mb"] is not None else "—"}</td><td class="mono">{r["rows"] if r["rows"] is not None else "—"}</td><td class="mono">{e(r["max_date"] or "—")}</td><td class="dim">{e(r["note"])}</td></tr>' for r in d.get("db_rows", []))
        rules = "".join(f'<tr><td>{e(r["zh"])}</td><td class="mono">{e(r["file"] or r["path"])}</td><td>{pill(r["present"])}</td></tr>' for r in d.get("rule_rows", []))
        mets = "".join(f'<tr><td class="mono">{e(m)}</td><td><span class="pill warn">待本機 DB 再生</span></td></tr>' for m in d.get("metrics", []))
        inputs = "".join(f'<tr><td>{e(m["zh"])}</td><td class="mono">{e(m["key"])}</td><td>{e(m["auto"])}</td><td class="mono">{e(", ".join(m.get("needed_for", [])))}</td></tr>' for m in d.get("minimal_inputs", [])) or '<tr><td colspan="4"><span class="led ok" style="margin:0 6px 0 0"></span>零人工輸入</td></tr>'
        autos = "".join(f'<li>{e(a)}</li>' for a in d.get("auto_params", []))
        ov = (f'<div class="stats"><div class="stat"><div class="n">{sum(1 for r in d["engine_rows"] if r["present"])}/{len(d["engine_rows"])}</div><div class="l">engines</div></div>'
              f'<div class="stat"><div class="n">{sum(1 for r in d["page_rows"] if r["present"])}/{len(d["page_rows"])}</div><div class="l">pages</div></div>'
              f'<div class="stat"><div class="n">{sum(1 for r in d["task_rows"] if r["present"])}/{len(d["task_rows"])}</div><div class="l">deck tasks</div></div>'
              f'<div class="stat"><div class="n">{sum(1 for r in d.get("db_rows", []) if r["present"])}/{len(d.get("db_rows", []))}</div><div class="l">databases</div></div>'
              f'<div class="stat"><div class="n">{len(d.get("minimal_inputs", []))}</div><div class="l">human inputs</div></div></div>')
        panes += f'''<div class="pane {"on" if i == 0 else ""}" data-d="{d["id"]}">
<div class="tabs" data-tabs="{d["id"]}"><button class="on" data-t="ov">總覽 OVERVIEW</button><button data-t="in">輸入 INPUTS</button><button data-t="en">引擎 ENGINES</button><button data-t="pg">頁面 PAGES</button><button data-t="me">指標 METRICS</button><button data-t="wf">工作流 WORKFLOW</button></div>
<div class="tp on" data-t="ov">{ov}<div class="grid"><div class="card"><h3>任務 <small>DECK TASKS</small></h3>{tbl(["task","zh","窗","白名單"], tks)}</div><div class="card"><h3>資料庫 <small>DATABASE · 真探</small></h3>{tbl(["path","在位","MB","rows","max_date","note"], dbs)}</div></div>{("<div class=card><h3>規則 SSOT <small>RULE REGISTRY</small></h3>" + tbl(["rule","file","在位"], rules) + "</div>") if rules else ""}</div>
<div class="tp" data-t="in"><div class="card"><h3>最少人工輸入 <small>MINIMAL INPUTS</small></h3>{tbl(["欄","key","自動推導","需要它的任務"], inputs)}</div><div class="card"><h3>自動參數 <small>AUTO-DERIVED</small></h3><ul style="margin:4px 0 0 16px;padding:0">{autos or "<li class=dim>—</li>"}</ul></div></div>
<div class="tp" data-t="en"><div class="card"><h3>引擎 <small>ENGINES · 尾版動態解析</small></h3>{tbl(["path","ver","在位"], eng)}</div></div>
<div class="tp" data-t="pg"><div class="card"><h3>頁面 <small>UI PAGES · 再生物</small></h3>{tbl(["page","size","在位"], pgs)}</div></div>
<div class="tp" data-t="me"><div class="card"><h3>指標 <small>METRICS · 本機 DB 再生後填值</small></h3>{tbl(["metric","status"], mets)}</div></div>
<div class="tp" data-t="wf"><div class="card"><h3>工作流 <small>WORKFLOW DAG · RYG 節點</small></h3>{_workflow_svg(ch, ev)}</div></div>
</div>'''

    JS = """
<script>
(function(){
  var navs=document.querySelectorAll('.nav a'),panes=document.querySelectorAll('.pane'),rins=document.querySelectorAll('.rin');
  navs.forEach(function(a){a.addEventListener('click',function(ev){ev.preventDefault();var id=a.getAttribute('data-d');
    navs.forEach(function(x){x.classList.toggle('on',x===a);});
    panes.forEach(function(p){p.classList.toggle('on',p.getAttribute('data-d')===id);});
    rins.forEach(function(r){r.style.display=(r.getAttribute('data-d')===id)?'block':'none';});
    document.getElementById('hd-id').textContent=id;document.getElementById('hd-zh').textContent=a.textContent.trim().split(' ')[0].replace(/^\\d\\d/,'');});});
  document.querySelectorAll('.tabs').forEach(function(t){t.querySelectorAll('button').forEach(function(b){b.addEventListener('click',function(){
    var k=b.getAttribute('data-t'),pane=t.parentElement;t.querySelectorAll('button').forEach(function(x){x.classList.toggle('on',x===b);});
    pane.querySelectorAll('.tp').forEach(function(p){p.classList.toggle('on',p.getAttribute('data-t')===k);});});});});
})();
function VIA_plan(btn){var rin=btn.closest('.rin'),d=rin.getAttribute('data-d'),o=rin.querySelector('[data-out]'),p={domain:d};
  rin.querySelectorAll('input[name]').forEach(function(i){if(i.value)p[i.name]=i.value;});
  var fp=rin.querySelector('input[type=file]');if(fp&&fp.files.length)p.files=Array.from(fp.files).map(function(f){return f.name;});
  p.note='未填=自動推導;本頁不派工(批340 獨立頁律);貼總控台或 via-six 執行';
  o.style.display='block';o.textContent=JSON.stringify(p,null,1);}
</script>"""

    return f'''<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>VIA · 系統結構總冊 System Charter</title><style>{CSS}</style></head><body><div class="app">
<aside class="rail"><div class="brand"><h1><span class="seal">理</span>VIA 系統總冊</h1><div class="sub">SYSTEM CHARTER · CENTRAL GOVERNANCE</div></div>
<nav class="nav">{nav}</nav>{rails}
<div class="railfoot">CHARTER v0101 · 批343<br>engines {ne}/{nE} · pages {npg}/{nP}<br>tasks {ntk}/{nT} · db {ndb}/{nD}<br>human inputs {nin} (across 7 domains)</div></aside>
<main class="main"><div class="hdwrap"><div class="crumb">VIA CENTRAL GOVERNANCE · SYSTEM CHARTER · 批343</div>
<div class="head"><h2><span id="hd-zh">{e(core["zh"])}</span> <span class="mono" id="hd-id">{core["id"]}</span><small>SEVEN DOMAINS UNDER ONE RULE SSOT</small></h2>
<div class="spec"><div><div class="k">GREEN</div><div class="v">{green}/{len(all_d)}</div></div><div><div class="k">ENGINES</div><div class="v">{ne}/{nE}</div></div><div><div class="k">PAGES</div><div class="v">{npg}/{nP}</div></div><div><div class="k">DB</div><div class="v">{ndb}/{nD}</div></div><div><div class="k">INPUTS</div><div class="v">{nin}</div></div></div></div></div>
{panes}
<div class="foot">零發明:每格=樹上實存物驗證;缺=PLANNED/NOT_GENERATED/DB_MISSING 誠實 · 本頁 file:// 獨立可讀;不派工 · 生成 {datetime.now().strftime("%Y-%m-%d %H:%M")}</div></main></div>{JS}</body></html>'''


# ---------------------------------------------------------------------
def run(open_after: bool = False) -> int:
    ch = _charter()
    if not ch:
        print("[總冊] VIA_SystemCharter_v*.json 缺(誠實;零產出)"); return 2
    ev = evaluate(ch)
    OUT.write_text(apply_type_scale(render(ch, ev)), encoding="utf-8")
    all_d = [ev["core"]] + ev["domains"]
    print(f"[總冊] {OUT.name} · 域 {len(all_d)} · GREEN {sum(1 for d in all_d if d['state']=='GREEN')} · "
          f"engines {sum(sum(1 for r in d['engine_rows'] if r['present']) for d in all_d)}/{sum(len(d['engine_rows']) for d in all_d)} · "
          f"人工輸入 {sum(len(d.get('minimal_inputs', [])) for d in ev['domains'])} 欄")
    for d in all_d:
        print(f"  {d['state']:<6} {d['id']:<9} {d['zh']}")
    if open_after:
        try:
            webbrowser.open(OUT.resolve().as_uri())
        except Exception:
            pass
    return 0


def selftest() -> int:
    fails = []
    def chk(n, c, note=""):
        print(f"  [{'OK' if c else 'FAIL'}] {n} {note}")
        if not c:
            fails.append(n)
    ch = _charter(); ev = evaluate(ch); page = render(ch, ev)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("① 結構總冊在位(七域+治理核;schema 對;workflow 邊全指向在冊節點)",
        ch.get("schema", "").startswith("VIA_SystemCharter") and len(ch.get("domains", [])) == 7
        and all(a in ch["workflow"]["nodes"] and b in ch["workflow"]["nodes"] for a, b, _ in ch["workflow"]["edges"]))
    chk("② 零發明(每引擎/頁/任務/DB 逐項驗在位;缺=誠實標而非略過)",
        all("present" in r for d in [ev["core"]] + ev["domains"] for r in d["engine_rows"] + d["page_rows"] + d["task_rows"])
        and "PLANNED" in page and "DB_MISSING" in src)
    chk("③ 任務全在白名單(總冊引用之任務 ⊆ DeckServer task_registry;缺者標任務缺)",
        ev["task_count"] >= 30 and all(("present" in r) for d in [ev["core"]] + ev["domains"] for r in d["task_rows"]))
    chk("④ 輸入最少化律(每域 ≤3 人工欄;七域合計 ≤5;未輸入欄皆有 auto 來源)",
        all(len(d.get("minimal_inputs", [])) <= 3 for d in ch["domains"]) and sum(len(d.get("minimal_inputs", [])) for d in ch["domains"]) <= 5
        and all(m.get("auto") for d in ch["domains"] for m in d.get("minimal_inputs", [])))
    chk("⑤ 版型律(左欄導航+最少輸入;右欄六頁籤;頁首/頁尾 sticky;燈號;零 CDN)",
        page.count('class="tabs"') == 8 and 'class="rin"' in page and "hdwrap" in page and 'class="foot"' in page
        and 'class="led' in page and 'src="http' not in page and 'href="http' not in page)
    chk("⑥ 工作流 SVG 內嵌(RYG 節點=域狀態;邊帶標籤)",
        page.count("<svg") == 8 and "marker-end" in page and all(k in page for k in ("CGC", "VDF", "ROTATION", "VAP")))
    chk("⑦ 兩日試鏈=計畫制(非 --go 零派工;起訖自今日推;range 任務帶 --start/--end)",
        "PLAN_ONLY" in src and "{D-2}" in src and "timeout=timeout" in src)
    chk("⑧ 結構守恆(div/table/svg 成對;DB 真探為 read_only)",
        page.count("<div") == page.count("</div>") and page.count("<table") == page.count("</table>")
        and page.count("<svg") == page.count("</svg>") and "read_only=True" in src)
    chk("⑨ 批347 字階守恆(產物零越階;最大=UISpec fs_xl)", all(any(abs(float(v) - px) < 0.01 for _, px in _type_scale()) for v in re.findall(r"font(?:-size)?\\s*:\\s*([0-9.]+)px", apply_type_scale(page))))
    print(f"  [計] 九檢 OK {9 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print("=== 系統結構總冊引擎(CGC_MDL124 v0101)· 八檢自測(零網路)===")
        return selftest()
    if "--probe" in a:
        days = int(a[a.index("--days") + 1]) if "--days" in a else 2
        r = probe(_charter(), days=days, go="--go" in a)
        print(f"[試鏈] {r['mode']} · 窗 {r['window'][0]}→{r['window'][1]} · 步 {len(r['steps'])}")
        for s in r["steps"]:
            print(f"  {s['state']:<12} {s['domain']:<9} {s['task']:<18} {' '.join(s['argv'][-4:]) if s['argv'] else ''}")
        print(f"  report {r['run_dir']}\\probe.json")
        return 0
    return run(open_after="--open" in a)


if __name__ == "__main__":
    sys.exit(main())
