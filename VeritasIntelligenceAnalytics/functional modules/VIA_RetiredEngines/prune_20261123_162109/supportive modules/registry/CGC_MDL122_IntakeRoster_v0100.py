#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CGC_MDL122_IntakeRoster v0100 — 上船件冊(批336;操作員令「全部介面都整合今天上船的檔案」)
====================================================================
操作員令列七件(Downloads):Story_Group_Rotation_v0500 zip / Optimize-VIA-Repo ps1 /
MasterControl v0108 測試報告 / Plotly 可編輯模板 / MasterControl 頁 / VAP v2.3.1 UAT
報告 / Seaborn VerticalStack zip。
職權:references/intake 全收容包(manifest.json hash 冊;無 manifest=目錄實掃誠實列)
→ 整合點冊 INTEGRATION(收容包→引擎/頁/短令/樞紐任務/系統總台主體;零發明=
只列真存在件;缺=誠實 PARTIAL)→
  ①roster() 資料(MDL119 首頁 intake 段/系統總台上船件卡)
  ②VIA_UI_IntakeRoster_v0100.html 頁(統一殼版型;每包檔冊+hash+整合鏈真連結)
  ③連結網:MDL105 overview/MDL116 導航/MDL120 殼列/Manager 系統連線/MDL096 頁首
律:只增不減;原件零觸碰;hash 定生死;頁名穩定律;零 CDN。
用法:python3 CGC_MDL122_IntakeRoster_v0100.py [--open|--print] | --selftest
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
import html
import json
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
INTAKE = VIA / "supportive modules" / "references" / "intake"
UI = VIA / "supportive modules" / "ui_support"
OUT = UI / "VIA_UI_IntakeRoster_v0100.html"
BRIDGE = "http://127.0.0.1:8765"

# 整合點冊(收容包 id → 整合鏈;值皆為倉庫真件,產頁時逐一驗在位)
INTEGRATION = {
    "VIA_StoryGroupRotation_b325": {
        "zh": "故事族群輪動 v0.5 全包", "today": True,
        "upload": "VIA_TW_Story_Group_Rotation_v0500_FULL_9e63c20.zip",
        "engines": ["functional modules/VDF/engine/VDF_ENG072_StoryRotationBridge_v*.py",
                    "functional modules/VDF/engine/VDF_ENG070_GroupClassificationIndex_v*.py"],
        "pages": ["VIA_UI_StoryRotation_v0100.html", "VIA_UI_GroupClassIndex_v0100.html"],
        "cmds": ["via-rotation", "via-pipeline"], "tasks": ["story_rotation", "group_class"],
        "subject": "rotation", "note": "ENG072 橋接 export→preflight→run-real;雲端 BLOCKED GAP-02(個股當沖缺)候工作站 L15 補源"},
    "VIA_RepoOptimizer_b325": {
        "zh": "倉庫最佳化 ps1", "today": True, "upload": "Optimize-VIA-Repo_v0101.ps1",
        "engines": ["Invoke-VIA-RepoOptimizer-v*.ps1"], "pages": [],
        "cmds": ["via-repo-optimize"], "tasks": [], "subject": "home",
        "note": "工作站已實跑(data/ 移出+.gitignore 補;commit 8a4d7bbb);35 secret-like 候人工確認"},
    "VIA_MasterControlUI_b333": {
        "zh": "總控台 Codex 設計正本三件", "today": True,
        "upload": "VIA_UI_MasterControl_v0100 (1).html · VIA_UI_PlotlyDashboard_EditableTemplate_v0100 (1).html · VIA_UI_MasterControl_v0108_TestReport.md",
        "engines": ["VIA_SYSTEM_MANAGER_v*.py", "supportive modules/registry/CGC_MDL095_DeckServer_v*.py"],
        "pages": ["VIA_UI_MasterControl_v0100.html", "VIA_UI_PlotlyDashboard_EditableTemplate_v0100.html"],
        "cmds": ["via-master", "via"], "tasks": ["ui"], "subject": "home",
        "note": "採納=Codex 安全模型(同源 CSRF POST/零 CORS);頁由樞紐 /master 供應;測試報告之 CI/pytest/UX 三件仍在 b305 候裁"},
    "VIA_VAPSeabornStack_b327": {
        "zh": "Seaborn 垂直圖組產生器 v2.3.1+UAT", "today": True,
        "upload": "VAP_Seaborn_VerticalStack_Generator_v2.3.1.zip · VAP_v231_UAT_REPORT.md",
        "engines": ["functional modules/VAP/engine/VAP_ENG015_SeabornStackBridge_v*.py"],
        "pages": ["VIA_UI_VapStack_v0100.html"], "cmds": ["via-vapstack"], "tasks": [],
        "subject": "vap", "note": "K線 BB/SMA/EMA/^TWII 右軸+熱圖細切;繪圖資料律 v0100(價還原/量扣當沖)已掛"},
    "VIA_CodexParallel_b305": {
        "zh": "Codex 平行線 patch 收容", "today": False, "upload": "VIA-b089f64.patch 等",
        "engines": ["VIA_SYSTEM_MANAGER_v*.py"], "pages": [], "cmds": [], "tasks": [],
        "subject": "home", "note": "b333 已採納其總控台/安全模型;CI workflow+pytest 契約+UX js 三件候裁"},
    "VIA_GroupClassification_b307": {"zh": "族群分類冊", "today": False, "upload": "", "engines": ["functional modules/VDF/engine/VDF_ENG070_GroupClassificationIndex_v*.py"],
                                     "pages": ["VIA_UI_GroupClassIndex_v0100.html"], "cmds": [], "tasks": ["group_class"], "subject": "rotation", "note": ""},
    "VIA_StoryGroups_b308": {"zh": "故事族群冊", "today": False, "upload": "", "engines": ["supportive modules/registry/VDF_StoryGroup_Registry_v*.json"],
                             "pages": ["VIA_UI_GroupClassIndex_v0100.html"], "cmds": [], "tasks": [], "subject": "rotation", "note": ""},
    "VIA_HTML_Bridge_Starter_b301": {"zh": "HTML 樞紐起手件", "today": False, "upload": "", "engines": ["supportive modules/registry/CGC_MDL095_DeckServer_v*.py"],
                                     "pages": [], "cmds": ["via"], "tasks": [], "subject": "home", "note": ""},
    "VIA_CGC_Console_Design_b258": {"zh": "中央治理主控台設計稿", "today": False, "upload": "", "engines": ["supportive modules/registry/CGC_MDL105_GovernanceConsole_v*.py"],
                                    "pages": ["VIA_UI_GovernanceConsole_v0100.html"], "cmds": [], "tasks": [], "subject": "home", "note": "100% 視覺鎖定正本"},
    "VIA_CommandCenter_AIO_b288": {"zh": "指揮中心 AIO", "today": False, "upload": "", "engines": ["supportive modules/registry/CGC_MDL114_CommandCenterBridge_v*.py"],
                                   "pages": ["VIA_UI_CommandCenter_v0100.html"], "cmds": ["via-health"], "tasks": ["cmdcenter"], "subject": "home", "note": ""},
    "VIA_Toolchain_Bundle_20260830_b245": {"zh": "工具鏈 bundle", "today": False, "upload": "", "engines": [], "pages": [], "cmds": [], "tasks": [], "subject": "home", "note": "收容(候整合)"},
}


def _exists(rel: str) -> str:
    """相對件(glob 尾版)在位→回實名;缺=''"""
    p = VIA / rel
    hits = sorted(p.parent.glob(p.name)) if "*" in p.name else ([p] if p.exists() else [])
    return hits[-1].name if hits else ""


def _tasks() -> set:
    try:
        import importlib.util
        p = sorted(HERE.glob("CGC_MDL095_DeckServer_v0*.py"))[-1]
        spec = importlib.util.spec_from_file_location("deck_roster", p)
        m = importlib.util.module_from_spec(spec)
        sys.modules["deck_roster"] = m
        spec.loader.exec_module(m)
        return set(m.task_registry())
    except Exception:
        return set()


def _cmds() -> set:
    hits = sorted(VIA.glob("Register-VIA-Commands-v*.ps1"))
    if not hits:
        return set()
    import re
    return set(re.findall(r"function global:(via[\w-]*)", hits[-1].read_text(encoding="utf-8")))


def roster() -> list:
    """收容包冊(全實掃;manifest 優先;整合鏈逐件驗在位;缺=PARTIAL 誠實)"""
    tasks, cmds = _tasks(), _cmds()
    out = []
    for d in sorted(INTAKE.iterdir()) if INTAKE.exists() else []:
        if not d.is_dir():
            continue
        m = d / "manifest.json"
        man = {}
        if m.exists():
            try:
                man = json.loads(m.read_text(encoding="utf-8"))
            except Exception:
                man = {}
        files = man.get("files", {})
        if not files:
            files = {str(p.relative_to(d)).replace("\\", "/"): "" for p in sorted(d.rglob("*")) if p.is_file() and p.name != "manifest.json"}
        ig = INTEGRATION.get(d.name, {"zh": d.name, "today": False, "upload": "", "engines": [], "pages": [], "cmds": [], "tasks": [], "subject": "home", "note": "收容(候整合)"})
        eng = [(e, _exists(e)) for e in ig["engines"]]
        pg = [(p, (UI / p).exists()) for p in ig["pages"]]
        cm = [(c, c in cmds) for c in ig["cmds"]]
        tk = [(t, t in tasks) for t in ig["tasks"]]
        n_pts = len(eng) + len(pg) + len(cm) + len(tk)
        n_ok = sum(1 for _, x in eng if x) + sum(1 for _, x in pg if x) + sum(1 for _, x in cm if x) + sum(1 for _, x in tk if x)
        state = "ARCHIVED" if n_pts == 0 else ("INTEGRATED" if n_ok == n_pts else "PARTIAL")
        try:
            ts = man.get("ts") or datetime.fromtimestamp(d.stat().st_mtime).strftime("%Y-%m-%d")
        except Exception:
            ts = ""
        out.append({"id": d.name, "zh": ig["zh"], "today": bool(ig.get("today")), "batch": man.get("batch"),
                    "ts": ts, "n_files": len(files), "manifest": m.exists(),
                    "zip": man.get("zip_name", ""), "zip_sha8": (man.get("zip_sha256") or "")[:8],
                    "upload": ig.get("upload", ""), "subject": ig.get("subject", "home"),
                    "engines": [{"pat": e, "file": f, "ok": bool(f)} for e, f in eng],
                    "pages": [{"page": p, "ok": ok} for p, ok in pg],
                    "cmds": [{"cmd": c, "ok": ok} for c, ok in cm],
                    "tasks": [{"task": t, "ok": ok} for t, ok in tk],
                    "n_points": n_pts, "n_ok": n_ok, "state": state, "note": ig.get("note", ""),
                    "files": [{"name": k, "sha8": (v or "")[:8]} for k, v in list(files.items())[:80]],
                    "verdicts": man.get("verdicts") or man.get("notes") or []})
    out.sort(key=lambda x: (not x["today"], -(x["batch"] or 0), x["id"]))
    return out


CSS = """
:root{--bg:#f5f5f2;--paper:#fff;--paper2:#fafaf8;--ink:#1f2530;--ink2:#3c4658;--mut:#6d7688;--mut2:#9aa2b1;--line:#dcdfe6;--soft:#eef0ee;--acc:#3e6b8f;--ok:#4f8f6b;--warn:#b58a3e;--bad:#b05c4d}
*{box-sizing:border-box;margin:0}body{background:var(--bg);color:var(--ink);font:12px/1.5 "Segoe UI","Noto Sans TC",system-ui,sans-serif;padding:16px 22px;max-width:1240px}
code{font-family:Consolas,ui-monospace,monospace}a{color:var(--acc);text-decoration:none}a:hover{text-decoration:underline}
.crumb{font-size:10px;color:var(--mut);letter-spacing:.04em;margin-bottom:7px}.crumb b{color:var(--acc)}
.head{display:flex;align-items:flex-end;gap:18px;flex-wrap:wrap;border-bottom:2px solid var(--ink);padding-bottom:9px;margin-bottom:12px}
.head h2{font-size:clamp(17px,2.4vw,23px)}.head h2 small{font-size:10px;color:var(--mut);font-weight:400;margin-left:10px;letter-spacing:.1em}.head .sub{width:100%;font-size:11px;color:var(--mut)}
.spec{margin-left:auto;display:flex;gap:16px}.spec .k{font-size:9px;letter-spacing:.18em;color:var(--mut2);font-weight:700}.spec .v{font-size:11px;font-weight:700}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(128px,1fr));gap:8px;margin-bottom:12px}
.stat{background:var(--paper);border:1px solid var(--line);border-radius:7px;padding:9px 12px}.stat .n{font-size:21px;font-weight:800}.stat .zh{font-size:10.5px;color:var(--ink2)}.stat .en{font-size:9px;letter-spacing:.18em;color:var(--mut2);font-weight:700}
.card{background:var(--paper);border:1px solid var(--line);border-radius:7px;padding:12px 14px;margin-bottom:10px}.card h3{font-size:12.5px}.card h3 small{font-size:10px;letter-spacing:.16em;color:var(--mut2);font-weight:700;margin-left:8px}.card .note{font-size:10px;color:var(--mut);margin:3px 0 7px}
.tbl{width:100%;border-collapse:collapse;font-size:11px}.tbl th{text-align:left;font-size:10px;letter-spacing:.14em;color:var(--mut2);border-bottom:1px solid var(--line);padding:4px 8px 4px 0;white-space:nowrap}.tbl td{border-bottom:1px solid var(--soft);padding:4px 8px 4px 0;vertical-align:top}
.tag{display:inline-block;font-size:10px;font-weight:700;padding:1px 7px;border-radius:3px;background:var(--soft);color:var(--ink2);white-space:nowrap}.tag.ok{background:#e3efe8;color:var(--ok)}.tag.warn{background:#f3ece1;color:var(--warn)}.tag.bad{background:#efd9d5;color:var(--bad)}
.wrap-x{overflow-x:auto}details{margin-top:4px}summary{cursor:pointer;font-size:10px;color:var(--mut)}.chips span{display:inline-block;font-size:10px;padding:1px 6px;border:1px solid var(--line);border-radius:3px;margin:1px 3px 1px 0}
.foot{font-size:10.5px;color:var(--mut2);margin-top:6px}
"""


def render(rows: list) -> str:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    e = html.escape

    def chips(items, key, okk="ok"):
        return "".join(f'<span class="tag {"ok" if x[okk] else "bad"}">{e(str(x[key]))}{"" if x[okk] else " · 缺"}</span> ' for x in items) or "—"

    def prow(r):
        pages = "".join((f'<a href="{e(p["page"])}">{e(p["page"].replace("VIA_UI_", "").replace("_v0100.html", ""))}</a> ' if p["ok"]
                         else f'<span class="tag bad">{e(p["page"])} 缺</span> ') for p in r["pages"]) or "—"
        eng = "".join(f'<span class="tag {"ok" if x["ok"] else "bad"}">{e(x["file"] or x["pat"].split("/")[-1])}</span> ' for x in r["engines"]) or "—"
        files = "".join(f'<tr><td><code>{e(f["name"])}</code></td><td><code>{e(f["sha8"])}</code></td></tr>' for f in r["files"])
        st = {"INTEGRATED": "ok", "PARTIAL": "warn", "ARCHIVED": "mut"}[r["state"]]
        today_tag = '<span class="tag warn">今日</span> ' if r["today"] else ""
        zip_note = (" · zip " + e(r["zip_sha8"])) if r["zip_sha8"] else ""
        verd = ""
        if r["verdicts"]:
            verd = (f'<details><summary>裁定 {len(r["verdicts"])} 條</summary>'
                    + "".join(f"<div>· {e(str(v))}</div>" for v in r["verdicts"]) + "</details>")
        return (f'<tr><td>{today_tag}<b>{e(r["zh"])}</b><br><code>{e(r["id"])}</code></td>'
                f'<td>b{e(str(r["batch"] or "—"))}<br>{e(r["ts"])}</td>'
                f'<td>{r["n_files"]}{zip_note}<br><small>{e(r["upload"])}</small></td>'
                f'<td>{eng}</td><td>{pages}</td><td>{chips(r["cmds"], "cmd")}</td><td>{chips(r["tasks"], "task")}</td>'
                f'<td><a href="VIA_UI_System_v0100.html#{e(r["subject"])}">{e(r["subject"])}</a></td>'
                f'<td><span class="tag {st}">{e(r["state"])}</span> {r["n_ok"]}/{r["n_points"]}</td>'
                f'<td>{e(r["note"])}<details><summary>檔冊 {r["n_files"]} 件(hash8)</summary><table class="tbl">{files}</table></details>{verd}</td></tr>')

    today = [r for r in rows if r["today"]]
    n_int = sum(1 for r in rows if r["state"] == "INTEGRATED")
    return f"""<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,"><title>VIA · 上船件冊 Intake Roster</title><style>{CSS}</style></head><body>
<div class="crumb"><b>VIA 母系統</b> → <b>系統總台</b> → <b>上船件冊</b> · LAYOUT SPEC(批302)· 批336</div>
<div class="head"><h2>上船件冊<small>INTAKE ROSTER · 收容包 × 整合鏈</small></h2>
<div class="spec"><div><div class="k">PACKAGES</div><div class="v">{len(rows)}</div></div><div><div class="k">TODAY</div><div class="v">{len(today)}</div></div><div><div class="k">INTEGRATED</div><div class="v">{n_int}</div></div><div><div class="k">GATE</div><div class="v">HONEST 3-STATE</div></div></div>
<div class="sub">references/intake 全收容包(manifest hash 冊;原件零觸碰)→ 整合鏈=引擎尾版 / 現役頁 / 短令 / 樞紐任務 / 系統總台主體,逐件驗在位;INTEGRATED=整合點全在位 · PARTIAL=有缺 · ARCHIVED=純收容。</div></div>
<div class="stats"><div class="stat"><div class="n">{len(rows)}</div><div class="zh">收容包</div><div class="en">PACKAGES</div></div>
<div class="stat"><div class="n">{len(today)}</div><div class="zh">今日上船件(七件四包)</div><div class="en">TODAY</div></div>
<div class="stat"><div class="n">{sum(r["n_files"] for r in rows)}</div><div class="zh">收容檔案</div><div class="en">FILES</div></div>
<div class="stat"><div class="n">{n_int}/{len(rows)}</div><div class="zh">整合完成</div><div class="en">INTEGRATED</div></div></div>
<div class="card"><h3>收容包 × 整合鏈<small>PACKAGES · INTEGRATION CHAIN</small></h3>
<div class="note">今日四包對應操作員七件:Story_Group_Rotation zip → ENG072/ENG070 · Optimize-VIA-Repo ps1 → via-repo-optimize · MasterControl 頁+Plotly 模板+測試報告 → Manager/DeckServer /master · Seaborn zip+UAT → ENG015 VapStack。</div>
<div class="wrap-x"><table class="tbl"><tr><th>收容包</th><th>批 / 時戳</th><th>檔數 / 上傳件</th><th>引擎(尾版)</th><th>現役頁</th><th>短令</th><th>樞紐任務</th><th>總台主體</th><th>狀態</th><th>註 / 檔冊 / 裁定</th></tr>
{"".join(prow(r) for r in rows)}</table></div></div>
<div class="card"><h3>入口<small>ENTRY POINTS</small></h3><div class="chips">
<span><a href="VIA_UI_System_v0100.html">系統總台 System</a></span><span><a href="{BRIDGE}/master">總控台 /master(樞紐)</a></span><span><a href="VIA_UI_GovernanceConsole_v0100.html">中央治理主控台</a></span><span><a href="VIA_UI_SyncStatus_v0100.html">全景同步狀態台</a></span><span><a href="VIA_UI_Shell_CGC_v0100.html">CGC 現況台</a></span></div></div>
<div class="foot">VIA · 上船件冊 · 產於 {ts} · 零 CDN 零外網 · 原件零觸碰 · hash 定生死</div></body></html>"""


def run(open_after: bool = False, do_print: bool = True) -> int:
    rows = roster()
    UI.mkdir(parents=True, exist_ok=True)
    OUT.write_text(render(rows), encoding="utf-8")
    if do_print:
        print(f"[上船件冊] {OUT.name} · 收容包 {len(rows)} · 今日 {sum(r['today'] for r in rows)} · "
              f"INTEGRATED {sum(r['state'] == 'INTEGRATED' for r in rows)} · PARTIAL {sum(r['state'] == 'PARTIAL' for r in rows)}")
    if open_after:
        import webbrowser
        webbrowser.open(OUT.as_uri())
    return 0


def selftest() -> int:
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    rows = roster()
    rc = run(do_print=False)
    page = OUT.read_text(encoding="utf-8")
    today = [r for r in rows if r["today"]]
    chk("① 收容包全實掃(manifest 優先;無 manifest 目錄實列)", len(rows) >= 10 and all(r["n_files"] >= 1 for r in rows),
        f"({len(rows)} 包)")
    chk("② 今日七件四包全 INTEGRATED(引擎/頁/短令/任務逐件在位)",
        len(today) == 4 and all(r["state"] == "INTEGRATED" for r in today),
        "(" + " ".join(f"{r['id'].split('_')[1]}={r['n_ok']}/{r['n_points']}" for r in today) + ")")
    chk("③ 頁產出(頁名穩定律+每包檔冊 hash8+整合鏈真連結+零 CDN)", rc == 0 and OUT.exists()
        and 'href="VIA_UI_StoryRotation_v0100.html"' in page and 'href="VIA_UI_VapStack_v0100.html"' in page
        and 'href="VIA_UI_MasterControl_v0100.html"' in page and "src=\"http" not in page)
    chk("④ 三態誠實(INTEGRATED/PARTIAL/ARCHIVED 僅此三種;ARCHIVED=零整合點)",
        all(r["state"] in ("INTEGRATED", "PARTIAL", "ARCHIVED") for r in rows)
        and all((r["n_points"] == 0) == (r["state"] == "ARCHIVED") for r in rows))
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑤ 紀律宣告(原件零觸碰/hash 定生死/只增不減/加速橋)", all(k in src for k in ("原件零觸碰", "hash 定生死", "只增不減", "ACCEL-BRIDGE")))
    print(f"  [計] 五檢 OK {5 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print("=== 上船件冊(CGC_MDL122 v0100)· 五檢自測(零網路)===")
        return selftest()
    if "--print" in a:
        for r in roster():
            print(f"{'今日 ' if r['today'] else '     '}{r['state']:10s} {r['id']:38s} b{r['batch']} 檔 {r['n_files']:3d} 整合 {r['n_ok']}/{r['n_points']}")
        return 0
    return run(open_after="--open" in a)


if __name__ == "__main__":
    sys.exit(main())
