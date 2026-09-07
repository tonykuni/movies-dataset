#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CGC_MDL138_FamilyUI v0100 — VDF/VRN/VAP 家族 U/I 再生閘(批388)
====================================================================
操作員令(批388):「若能跑 vdf vrn 的 u/i」。
「U/I 能跑」的誠實定義=以家族境 python 真跑頁面產生器 → 產物頁在位且本次新鮮(mtime ≥ 起跑)、零 CDN
→ 一頁索引 FAMILY_UI_latest.html(file:// 真連結;零 CDN)供 via-open 一鍵開;頁面只走瀏覽器道(批378 零跳出律)。
冊(尾版 glob;零發明=皆母倉現役產生器):
  vdf:VDF_ENG073 DataArchitecture build → VIA_UI_VDFArchitecture_v0100.html;CGC_MDL120 SystemUI(六主體含 VDF/首頁擷取資料;
      base 先跑,ModuleNotFoundError 才退家族境)→ VIA_UI_System_v0100.html;靜態:VIA_VDF_Fetch_ONE__Standalone/VDF_MDL501 控制器
  vrn:VRN_ENG079 ControlTower run → VIA_UI_VRNControlTower_v0100.html;VRN_ENG068 DailyBrief run → VIA_UI_DailyBrief_v0100.html;
      VRN_ENG080 FourPointDigest run → VIA_Reports/vrn/four_point/DIGEST_latest.html(資料閘:報告表缺=YELLOW 資料側);靜態:VisualLock 側欄
  vap:VAP_ENG009 DashboardUI run → VIA_UI_Dashboard_v0100.html;VAP_ENG014 StdDashboard run → VIA_UI_StdDashboard_v0100.html;靜態:VAP ONE Standalone
判定:族內任一產生器 FAIL(rc≠0 且無頁)=RED;資料側(rc≠0 但頁在/資料閘)或頁舊或靜態缺=YELLOW;全新鮮=GREEN;總判=最壞。
樞紐燈:127.0.0.1:8765 在聽=LIVE(SystemUI/MasterControl 可從樞紐重取);否=SNAPSHOT(頁內嵌快照;誠實)。
落 VIA_Reports/ui/FAMILY_UI_latest.json + FAMILY_UI_latest.html + logs/family_ui.log。
律:只增不減;正本零觸碰(產生器唯讀複用=Zero-Hydra);誠實三態;零網路(樞紐探針僅本機);尾版律;頁面零跳出(本檔不開瀏覽器;via-open 才開)。
用法:python3 CGC_MDL138_FamilyUI_v0100.py run [--family vdf,vrn,vap|all] [--no-build] [--json] [--quiet] | status | --selftest
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
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

import datetime as _dt
import html
import importlib.util
import json
import os
import re
import socket
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
OUT = VIA / "VIA_Reports" / "ui"
LOG = VIA / "logs" / "family_ui.log"
HUB_PORT = 8765
VERBS = ("run", "status")
CDN_RX = re.compile(r"<(?:script|link)[^>]+(?:src|href)=[\"']https?://", re.I)

ROSTER = {
    "vdf": [
        {"zh": "VDF 資料架構矩陣", "dir": "functional modules/VDF/engine", "glob": "VDF_ENG073_DataArchitecture_v*.py", "args": ["build"],
         "page": "supportive modules/ui_support/VIA_UI_VDFArchitecture_v0100.html", "timeout": 300, "python": "family"},
        {"zh": "系統總台六主體(VIA 首頁擷取資料/VDF/VAP/ETF/族群/月營收)", "dir": "supportive modules/registry", "glob": "CGC_MDL120_SystemUI_v*.py", "args": [],
         "page": "supportive modules/ui_support/VIA_UI_System_v0100.html", "timeout": 300, "python": "base_then_family"},
    ],
    "vrn": [
        {"zh": "VRN 控制塔(產出索引/共識全景/共識明細)", "dir": "functional modules/VRN", "glob": "VRN_ENG079_ControlTowerDashboard_v*.py", "args": ["run"],
         "page": "supportive modules/ui_support/VIA_UI_VRNControlTower_v0100.html", "timeout": 300, "python": "family"},
        {"zh": "VRN 每日觀察摘要", "dir": "functional modules/VRN", "glob": "VRN_ENG068_DailyBrief_v*.py", "args": ["run"],
         "page": "supportive modules/ui_support/VIA_UI_DailyBrief_v0100.html", "timeout": 300, "python": "family"},
        {"zh": "VRN 一題四點文摘(潛在上漲空間/目標價除權息調整)", "dir": "functional modules/VRN", "glob": "VRN_ENG080_FourPointDigest_v*.py", "args": ["run"],
         "page": "VIA_Reports/vrn/four_point/DIGEST_latest.html", "timeout": 600, "python": "family", "data_gate": True},
    ],
    "vap": [
        {"zh": "VAP 儀表板", "dir": "functional modules/VAP/engine", "glob": "VAP_ENG009_DashboardUI_v*.py", "args": ["run"],
         "page": "supportive modules/ui_support/VIA_UI_Dashboard_v0100.html", "timeout": 300, "python": "family"},
        {"zh": "VAP 標準 Plotly 儀表板", "dir": "functional modules/VAP/engine", "glob": "VAP_ENG014_StdDashboardTemplate_v*.py", "args": ["run"],
         "page": "supportive modules/ui_support/VIA_UI_StdDashboard_v0100.html", "timeout": 300, "python": "family"},
    ],
}
STATIC = {
    "vdf": [("VDF Fetch ONE 單檔工作台", "functional modules/VDF/VIA_VDF_Fetch_ONE__Standalone.html"), ("VDF 資料模組控制器", "functional modules/VDF/VDF_MDL501_DataModuleController.html")],
    "vrn": [("VRN VisualLock 側欄", "supportive modules/VIA_VisualLock/VIA_VRN_VisualLock_Sidebar_v0159.html")],
    "vap": [("VAP ONE 單檔工作台", "functional modules/VAP/VIA_VAP_ONE__Standalone.html")],
}
HUB_PAGES = [("總控台 MasterControl", "supportive modules/ui_support/VIA_UI_MasterControl_v0100.html"), ("總控矩陣 v0700", "supportive modules/ui_support/VIA_MasterControl_Matrix_v0700.html"), ("輸入主控台 InputConsole(批390)", "supportive modules/ui_support/VIA_UI_InputConsole_v0100.html")]


def _ts() -> str:
    return _dt.datetime.now().strftime("%Y%m%d_%H%M%S")


def _newest(root: Path, pat: str) -> Path | None:
    hits = sorted(root.glob(pat)) if root.exists() else []
    return hits[-1] if hits else None


def _say(s: str, quiet: bool = False) -> None:
    if not quiet:
        try:
            print(s, flush=True)
        except (BrokenPipeError, UnicodeEncodeError):
            pass


def log_event(kind: str, msg: str, **kw) -> None:
    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"ts": _dt.datetime.now().isoformat(timespec="seconds"), "kind": kind, "msg": msg, **kw}, ensure_ascii=False) + "\n")
    except Exception:
        pass


def hub_live(port: int = HUB_PORT) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.3):
            return True
    except Exception:
        return False


def python_for(family: str) -> dict:
    """家族境 python(MDL136 正本解析;缺=base 退路誠實)"""
    p = _newest(HERE, "CGC_MDL136_EntryBridge_v*.py")
    if p:
        try:
            spec = importlib.util.spec_from_file_location("entry_bridge_famui", p)
            m = importlib.util.module_from_spec(spec)
            sys.modules["entry_bridge_famui"] = m
            spec.loader.exec_module(m)
            return m.resolve_env_python(family)
        except Exception:
            pass
    return {"family": family, "env": "", "python": sys.executable, "source": "base 退路(MDL136 缺)", "state": "BASE_FALLBACK"}


def needs_family_retry(text: str) -> bool:
    return "ModuleNotFoundError" in (text or "") or "No module named" in (text or "")


def page_check(page: Path, t0: float) -> dict:
    if not page.exists():
        return {"exists": False, "fresh": False, "size": 0, "cdn": False}
    st = page.stat()
    txt = ""
    try:
        txt = page.read_text(encoding="utf-8", errors="replace")
    except Exception:
        pass
    return {"exists": True, "fresh": st.st_mtime >= t0 - 1, "size": st.st_size, "cdn": bool(CDN_RX.search(txt)), "mtime": _dt.datetime.fromtimestamp(st.st_mtime).isoformat(timespec="seconds")}


def run_item(item: dict, fam: str, root: Path, build: bool, py_fn=None, runner=None) -> dict:
    py_fn = py_fn or python_for
    runner = runner or subprocess.run
    eng = _newest(root / item["dir"], item["glob"])
    page = root / item["page"]
    rec = {"zh": item["zh"], "engine": eng.name if eng else "", "page": str(page), "state": "", "python": "", "secs": 0, "note": "", "tail": []}
    if not eng:
        rec["state"], rec["note"] = "MISSING", f"產生器缺 {item['glob']}"
        return rec
    t0 = time.time()
    if not build:
        pc = page_check(page, 0)
        rec["state"] = "OK" if pc["exists"] else "MISSING"
        rec["note"] = f"--no-build 只驗頁:{'在位 ' + pc.get('mtime', '') if pc['exists'] else '頁缺'}"
        rec.update({"page_check": pc})
        return rec
    fam_py = py_fn(fam)
    order = [sys.executable, fam_py["python"]] if item.get("python") == "base_then_family" else [fam_py["python"]]
    env = dict(os.environ)
    env.update({"PYTHONUTF8": "1", "VIA_NO_OPEN": "1", "PYTHONIOENCODING": "utf-8"})
    last = None
    for i, py in enumerate(order):
        try:
            r = runner([py, str(eng), *item["args"]], capture_output=True, text=True, timeout=item.get("timeout", 300), stdin=subprocess.DEVNULL, cwd=str(eng.parent), env=env,
                       encoding="utf-8", errors="replace")
            out = (r.stdout or "") + (r.stderr or "")
            last = (r.returncode, out)
            rec["python"] = py
            if r.returncode == 0 or not (i + 1 < len(order) and needs_family_retry(out)):
                break
            rec["note"] = "base 缺庫 → 退家族境重跑;"
        except subprocess.TimeoutExpired:
            last = (124, f"逾時 {item.get('timeout', 300)}s")
            rec["python"] = py
            break
        except Exception as exc:
            last = (1, str(exc)[:200])
            rec["python"] = py
            break
    rc, out = last
    rec["secs"] = round(time.time() - t0, 1)
    rec["tail"] = [l[:160] for l in out.strip().splitlines() if l.strip()][-2:]
    pc = page_check(page, t0)
    rec["page_check"] = pc
    if rc == 0 and pc["exists"] and pc["fresh"]:
        rec["state"] = "OK"
        rec["note"] += ("頁新鮮" + (";外連資源(非零 CDN)" if pc["cdn"] else ""))
    elif rc == 0 and pc["exists"]:
        rec["state"] = "STALE"
        rec["note"] += "rc0 但頁未更新(產生器另有輸出路徑或無變更)"
    elif rc != 0 and item.get("data_gate"):
        rec["state"] = "DATA"
        rec["note"] += "資料側(報告表/價表缺=引擎誠實停;頁" + ("在位舊版" if pc["exists"] else "缺") + ")"
    elif rc != 0 and pc["exists"]:
        rec["state"] = "DATA"
        rec["note"] += f"rc{rc};舊頁在位"
    else:
        rec["state"] = "FAIL"
        rec["note"] += f"rc{rc};頁缺"
    log_event("ITEM", f"{fam} {rec['engine']} {rec['state']}", rc=rc, page=str(page))
    return rec


def run(families: list | None = None, build: bool = True, do_print: bool = True, quiet: bool = False, root: Path = VIA, reports: Path = OUT,
        roster: dict | None = None, static: dict | None = None, py_fn=None, runner=None, hub_fn=None) -> dict:
    q = quiet or not do_print
    roster = roster if roster is not None else ROSTER
    static = static if static is not None else STATIC
    families = [f for f in (families or list(roster)) if f in roster]
    live = (hub_fn or hub_live)()
    rep = {"schema": "VIA.FamilyUI.v1", "ts": _dt.datetime.now().isoformat(timespec="seconds"), "via": str(root), "hub": "LIVE" if live else "SNAPSHOT",
           "families": {}, "verdict": "GREEN", "hub_pages": []}
    _say(f"=== [via-famui] 家族 U/I 再生閘 · 族 {','.join(families)} · 樞紐 127.0.0.1:{HUB_PORT} {'LIVE' if live else 'SNAPSHOT(樞紐未起;頁內嵌快照;via 可帶起)'} ===", q)
    order = {"GREEN": 0, "YELLOW": 1, "RED": 2}
    worst = 0
    for fam in families:
        items = [run_item(it, fam, root, build, py_fn, runner) for it in roster.get(fam, [])]
        for r in items:
            lampc = {"OK": "GREEN", "STALE": "YELLOW", "DATA": "YELLOW", "MISSING": "YELLOW", "FAIL": "RED"}[r["state"]]
            _say(f"{lampc:<7} {fam:<4} {r['zh'][:28]:<28} {r['state']:<7} {Path(r['page']).name} · {r['secs']}s · {r['note']}"[:220], q)
        st_rows = []
        for zh, rel in static.get(fam, []):
            p = root / rel
            st_rows.append({"zh": zh, "page": str(p), "state": "OK" if p.exists() else "MISSING"})
        v = "RED" if any(r["state"] == "FAIL" for r in items) else ("YELLOW" if any(r["state"] in ("STALE", "DATA", "MISSING") for r in items) or any(s["state"] != "OK" for s in st_rows) else "GREEN")
        worst = max(worst, order[v])
        rep["families"][fam] = {"verdict": v, "items": items, "static": st_rows,
                                "summary": {"ok": sum(1 for r in items if r["state"] == "OK"), "n": len(items), "static_ok": sum(1 for s in st_rows if s["state"] == "OK"), "static_n": len(st_rows)}}
        s = rep["families"][fam]["summary"]
        _say(f"{v:<7} {fam:<4} 頁 {s['ok']}/{s['n']} 新鮮 · 靜態 {s['static_ok']}/{s['static_n']} 在位", q)
    for zh, rel in HUB_PAGES:
        p = root / rel
        rep["hub_pages"].append({"zh": zh, "page": str(p), "state": "OK" if p.exists() else "MISSING"})
    rep["verdict"] = ["GREEN", "YELLOW", "RED"][worst]
    rep["open"] = [f"via-open \"{reports / 'FAMILY_UI_latest.html'}\"(索引;一鍵)"] + [f"via-open {n}" for n in ("VDF", "VRN", "總控")]
    try:
        reports.mkdir(parents=True, exist_ok=True)
        (reports / f"FAMILY_UI_{_ts()}.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
        (reports / "FAMILY_UI_latest.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
        (reports / "FAMILY_UI_latest.html").write_text(render_index(rep), encoding="utf-8")
    except Exception as exc:
        _say(f"YELLOW  Report 存證失敗 {str(exc)[:60]}", q)
    log_event("RUN", rep["verdict"], families={k: v["verdict"] for k, v in rep["families"].items()}, hub=rep["hub"])
    _say(f"[via-famui] 判定 {rep['verdict']} · 索引 {reports / 'FAMILY_UI_latest.html'} · 開頁:{' | '.join(rep['open'])}", q)
    return rep


def _file_url(p: str) -> str:
    return "file:///" + str(p).replace("\\", "/").lstrip("/")


def render_index(rep: dict) -> str:
    col = {"GREEN": "#34d399", "YELLOW": "#fde047", "RED": "#fca5a5"}
    st_col = {"OK": "#34d399", "STALE": "#fde047", "DATA": "#fde047", "MISSING": "#94a3b8", "FAIL": "#fca5a5"}
    rows = ""
    for fam, f in rep["families"].items():
        rows += f"<tr><th colspan='4' style='color:{col.get(f['verdict'], '#ddd')}'>{fam.upper()} · {f['verdict']} · 頁 {f['summary']['ok']}/{f['summary']['n']} 新鮮</th></tr>"
        for r in f["items"]:
            rows += (f"<tr><td style='color:{st_col.get(r['state'], '#ddd')}'>{r['state']}</td><td>{html.escape(r['zh'])}</td>"
                     f"<td><a href='{html.escape(_file_url(r['page']))}'>{html.escape(Path(r['page']).name)}</a></td><td>{html.escape(r.get('note', ''))} {html.escape(' | '.join(r.get('tail') or []))}</td></tr>")
        for s in f["static"]:
            rows += f"<tr><td style='color:{st_col.get(s['state'], '#ddd')}'>{s['state']}</td><td>{html.escape(s['zh'])}(靜態)</td><td><a href='{html.escape(_file_url(s['page']))}'>{html.escape(Path(s['page']).name)}</a></td><td>靜態頁;只開不再生</td></tr>"
    hub = "".join(f"<tr><td style='color:{st_col.get(h['state'], '#ddd')}'>{h['state']}</td><td>{html.escape(h['zh'])}</td><td><a href='{html.escape(_file_url(h['page']))}'>{html.escape(Path(h['page']).name)}</a></td><td>樞紐 {html.escape(rep['hub'])}</td></tr>" for h in rep["hub_pages"])
    return ("<!doctype html><html lang='zh-Hant'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
            "<title>VIA 家族 U/I 索引</title><style>body{background:#0f172a;color:#f8fafc;font:11px/1.35 -apple-system,'Segoe UI',Roboto,Arial,sans-serif;padding:12px}"
            "table{border-collapse:collapse;width:100%}td,th{border:1px solid #334155;padding:3px 6px;text-align:left;vertical-align:top}th{background:#1e293b}a{color:#38bdf8}</style></head><body>"
            f"<h1 style='font-size:14px;margin:0 0 6px'>VDF/VRN/VAP 家族 U/I 索引 · {html.escape(rep['verdict'])} · {html.escape(rep['ts'])} · 樞紐 {html.escape(rep['hub'])}</h1>"
            "<div style='color:#94a3b8;margin-bottom:8px'>頁面以家族境 python 再生;連結為本機 file:// 真路徑;零 CDN;樞紐 SNAPSHOT 時頁內嵌快照(輸入 via 可帶起樞紐)</div>"
            f"<table><tr><th>狀態</th><th>頁</th><th>檔</th><th>備註</th></tr>{rows}<tr><th colspan='4'>樞紐頁</th></tr>{hub}</table></body></html>")


def status() -> int:
    p = OUT / "FAMILY_UI_latest.json"
    if not p.exists():
        _say("GREY    FamilyUI  未跑;via-famui vdf|vrn|vap|all [--open]")
        return 2
    rep = json.loads(p.read_text(encoding="utf-8"))
    _say(f"[via-famui status] {rep['verdict']} · {rep['ts']} · 樞紐 {rep['hub']}")
    for fam, f in rep["families"].items():
        _say(f"{f['verdict']:<7} {fam:<4} 頁 {f['summary']['ok']}/{f['summary']['n']} 新鮮 · 靜態 {f['summary']['static_ok']}/{f['summary']['static_n']}")
        for r in f["items"]:
            _say(f"  [{r['state']:<7}] {r['zh'][:30]} · {Path(r['page']).name} · {r.get('note', '')}")
    return 0 if rep["verdict"] != "RED" else 1


# ---------------------------------------------------------------- 自測
def selftest() -> int:
    import tempfile
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)
    chk("① 動詞白名單+CDN 偵測+家族退路判準",
        next((x for x in ["--family", "vrn"] if x in VERBS), "run") == "run" and bool(CDN_RX.search('<script src="https://cdn.x/y.js">')) and not CDN_RX.search('<a href="https://x">')
        and needs_family_retry("ModuleNotFoundError: No module named 'duckdb'") and not needs_family_retry("ok"))
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "eng").mkdir()
        (root / "ui").mkdir()
        ok_py = root / "eng" / "GEN_OK_v0100.py"
        ok_py.write_text("import sys, pathlib; pathlib.Path(sys.argv[1]).write_text('<html><body>ok</body></html>', encoding='utf-8'); print('built')\n", encoding="utf-8")
        cdn_py = root / "eng" / "GEN_CDN_v0100.py"
        cdn_py.write_text("import sys, pathlib; pathlib.Path(sys.argv[1]).write_text('<html><script src=\"https://cdn.x/y.js\"></script></html>', encoding='utf-8')\n", encoding="utf-8")
        bad_py = root / "eng" / "GEN_BAD_v0100.py"
        bad_py.write_text("import sys; print('boom', file=sys.stderr); sys.exit(1)\n", encoding="utf-8")
        gate_py = root / "eng" / "GEN_GATE_v0100.py"
        gate_py.write_text("import sys; print('vrn_report_basic 缺'); sys.exit(1)\n", encoding="utf-8")
        mod_py = root / "eng" / "GEN_MOD_v0100.py"
        mod_py.write_text("import sys, os, pathlib\nif os.environ.get('FAKE_FAMILY') != '1':\n    print(\"ModuleNotFoundError: No module named 'duckdb'\", file=sys.stderr); sys.exit(1)\npathlib.Path(sys.argv[1]).write_text('<html>fam</html>', encoding='utf-8')\n", encoding="utf-8")
        (root / "static_ok.html").write_text("<html></html>", encoding="utf-8")
        roster = {"vdf": [{"zh": "OK 頁", "dir": "eng", "glob": "GEN_OK_v*.py", "args": [str(root / "ui" / "ok.html")], "page": "ui/ok.html", "timeout": 30, "python": "family"},
                          {"zh": "CDN 頁", "dir": "eng", "glob": "GEN_CDN_v*.py", "args": [str(root / "ui" / "cdn.html")], "page": "ui/cdn.html", "timeout": 30, "python": "family"}],
                  "vrn": [{"zh": "資料閘頁", "dir": "eng", "glob": "GEN_GATE_v*.py", "args": [], "page": "ui/gate.html", "timeout": 30, "python": "family", "data_gate": True},
                          {"zh": "缺產生器", "dir": "eng", "glob": "GEN_NONE_v*.py", "args": [], "page": "ui/none.html", "timeout": 30, "python": "family"}],
                  "vap": [{"zh": "壞頁", "dir": "eng", "glob": "GEN_BAD_v*.py", "args": [], "page": "ui/bad.html", "timeout": 30, "python": "family"}]}
        static = {"vdf": [("靜態在", "static_ok.html")], "vrn": [("靜態缺", "static_none.html")], "vap": []}
        fake_py = lambda fam: {"family": fam, "env": f"via_{fam}_312", "python": sys.executable, "state": "OK"}  # noqa: E731
        rep = run(None, True, do_print=False, root=root, reports=root / "rep", roster=roster, static=static, py_fn=fake_py, hub_fn=lambda: False)
        vdf, vrn, vap = rep["families"]["vdf"], rep["families"]["vrn"], rep["families"]["vap"]
        chk("② 產生器真跑+頁新鮮判準(OK 頁=OK;CDN 頁=OK 但註外連)", vdf["items"][0]["state"] == "OK" and vdf["items"][1]["state"] == "OK" and "外連" in vdf["items"][1]["note"] and vdf["verdict"] == "GREEN")
        chk("③ 資料閘(rc≠0 資料側=DATA=YELLOW)+產生器缺=MISSING+靜態缺=YELLOW", vrn["items"][0]["state"] == "DATA" and vrn["items"][1]["state"] == "MISSING" and vrn["static"][0]["state"] == "MISSING" and vrn["verdict"] == "YELLOW")
        chk("④ rc≠0 且無頁=FAIL=RED;總判最壞 RED;樞紐 SNAPSHOT 誠實", vap["items"][0]["state"] == "FAIL" and vap["verdict"] == "RED" and rep["verdict"] == "RED" and rep["hub"] == "SNAPSHOT")
        idx = (root / "rep" / "FAMILY_UI_latest.html").read_text(encoding="utf-8")
        chk("⑤ 索引頁(file:// 真連結;零 CDN;JSON 落檔)", "file:///" in idx and not CDN_RX.search(idx) and (root / "rep" / "FAMILY_UI_latest.json").exists() and "ok.html" in idx)
        roster2 = {"vdf": [{"zh": "base 先跑退家族", "dir": "eng", "glob": "GEN_MOD_v*.py", "args": [str(root / "ui" / "mod.html")], "page": "ui/mod.html", "timeout": 30, "python": "base_then_family"}]}
        calls = []

        def runner(argv, **kw):
            calls.append(argv[0])
            env = dict(kw.get("env") or {})
            if len(calls) == 2:
                env["FAKE_FAMILY"] = "1"
            kw["env"] = env
            return subprocess.run(argv, **kw)
        rep2 = run(["vdf"], True, do_print=False, root=root, reports=root / "rep2", roster=roster2, static={}, py_fn=fake_py, runner=runner, hub_fn=lambda: True)
        it = rep2["families"]["vdf"]["items"][0]
        chk("⑥ base 先跑遇 ModuleNotFoundError → 退家族境重跑成功(OK;註記);樞紐 LIVE", len(calls) == 2 and it["state"] == "OK" and "退家族境" in it["note"] and rep2["hub"] == "LIVE")
        rep3 = run(["vdf"], False, do_print=False, root=root, reports=root / "rep3", roster=roster, static=static, py_fn=fake_py, hub_fn=lambda: False)
        chk("⑦ --no-build 只驗頁在位(不跑產生器)", rep3["families"]["vdf"]["items"][0]["state"] == "OK" and "只驗頁" in rep3["families"]["vdf"]["items"][0]["note"])
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑧ 紀律宣告(只增不減/正本零觸碰/誠實三態/零網路/尾版律/零跳出/Zero-Hydra/ACCEL-BRIDGE)",
        all(k in src for k in ("只增不減", "正本零觸碰", "誠實三態", "零網路", "尾版律", "零跳出", "Zero-Hydra", "ACCEL-BRIDGE")))
    print(f"  [計] 八檢 OK {8 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def _arg(a: list, flag: str, default=None):
    if flag in a:
        i = a.index(flag)
        if i + 1 < len(a):
            return a[i + 1]
    return default


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print("=== 家族 U/I 再生閘(CGC_MDL138_FamilyUI)· 八檢自測(零網路)===")
        return selftest()
    verb = next((x for x in a if x in VERBS), "run")
    fam = _arg(a, "--family") or "all"
    fams = None if fam == "all" else [x.strip() for x in fam.split(",") if x.strip()]
    try:
        if verb == "run":
            rep = run(fams, "--no-build" not in a, do_print="--json" not in a, quiet="--quiet" in a)
            if "--json" in a:
                print(json.dumps(rep, ensure_ascii=False, indent=1))
            return 0 if rep["verdict"] != "RED" else 1
        if verb == "status":
            return status()
        print(__doc__)
        return 2
    except BrokenPipeError:
        return 0


if __name__ == "__main__":
    sys.exit(main())
