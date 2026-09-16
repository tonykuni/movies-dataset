#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
CGC_MDL153_WorkflowComposer v0100 — 工作流重組台 + U/I 對接契約(批519 操作員令「規劃好所有 U/I 自小一點更專業 · 中央可以自適應式連結對接 U/I ·
WORKFLOW 圖可重整不同引擎形成新功能 · 對接口合約自適應式功能完善化 · 自動跳出實測真實結果 · VDF 資料庫分類歸納摘要 · 介面做好與 HTML U/I 對接規格」)
====================================================================
一個正主(L30)管四件事,全零網路、零 CDN、零彈窗、預設只讀:
  ① 目錄     catalog        冊上項(VIA_InputConsole_Spec 三家族 groups.items)=可重組的引擎積木(id/zh/family/verb/params/net/outputs/engine glob)
  ② 工作流   validate/run   VIA_Workflow_SSOT_v0100.json(種子八條;可加)→ 逐節點以匯流排 `call --item <id> --apply --profile test|run` 真跑
                            (家族境 python/閘/PYTHONHOME 撤除全在匯流排;net 項未開閘=GATED 誠實)→ VIA_Reports/workflow/WORKFLOW_latest.json + RUN_<ts>.json
                            合約自適應(L31/L40):節點在冊?→ 參數有預設(start/since/days/range/since_ym/code/vapone)/需操作員給(dir/codes/only/lanes/cats/vetf)
                            → 節點 net?→ 逐邊判 OK / DEFAULT / NEED_INPUT / GATED / ABSENT;整條=最壞
  ③ U/I 契約 ui-contract    掃 ui_support/VIA_UI_*.html + 產生器引用(registry/functional 程式檔實掃)→ 每頁:擁有者/家族/在不在/新鮮/大小/再生短令
                            → VIA_UI_Contract_v0100.json(SSOT;--apply 才寫入倉)+ VIA_Reports/ui/UI_CONTRACT_latest.json;中央(VCGC 十二段)自適應連結:在=連、不在=ABSENT
                            契約含「介面對接規格」:頁面零 CDN/內嵌快照(SNAPSHOT)+ 樞紐 127.0.0.1:8765 在聽才 LIVE/零彈窗(via-open 才開)/緊湊專業樣式 tokens
  ④ 頁       page           工作流重組台(左 目錄 · 中 工作流+SVG 鏈圖+JSON 匯出+執行短令 · 右 實測面板(五矩陣/RunGate/VTMRA/主控台/工作流最新真跑自動展開)
                            + VDF 庫分類歸納(價量/籌碼/營收/財報/ETF/宏觀/國際/VRN 報告)+ U/I 對接表)→ VIA_Reports/workflow/WORKFLOW_COMPOSER.html
                            (--publish 才複製到 ui_support/VIA_UI_WorkflowComposer_v0100.html 入倉)
  db-summary               VDF 資料庫分類歸納摘要(讀 CONSOLE_latest.json db.tables;每類 表數/列數/最新日/最壞滯後/燈)→ VIA_Reports/workflow/DB_SUMMARY_latest.json
律:只增不減;Zero-Hydra(引擎不重寫,只重組);尾版律(glob);誠實三態;閘不代設(net 項由匯流排問閘);零 CDN;零彈窗;子行程走匯流排。
用法:python3 CGC_MDL153_WorkflowComposer_v0100.py catalog [--family f] [--json] | validate [<wf_id>|--file F] | run <wf_id>|--file F [--profile test|run] [--continue] [--timeout N] [--json]
      | ui-contract [--apply] [--json] | db-summary [--json] | page [--publish] | status | --selftest
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
import html as _html
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
REPORTS = VIA / "VIA_Reports"
OUT = REPORTS / "workflow"
UI_SUPPORT = VIA / "supportive modules" / "ui_support"
WF_SSOT = HERE / "VIA_Workflow_SSOT_v0100.json"
UI_SSOT = HERE / "VIA_UI_Contract_v0100.json"
SPEC = HERE / "VIA_InputConsole_Spec_v0100.json"
VERSION = "0100"
BATCH = 519
PAGE_NAME = "VIA_UI_WorkflowComposer_v0100.html"

# 參數種類的自適應合約(L31):有預設=DEFAULT;要操作員給=NEED_INPUT;資料家可解=RESOLVE
PARAM_DEFAULT = {"start", "since", "days", "range", "since_ym", "code", "vapone", "gap-mode", "end", "db", "batch-size", "max-batches", "report", "max-days", "years", "limit"}
PARAM_INPUT = {"dir", "codes", "only", "lanes", "cats"}
PARAM_RESOLVE = {"vetf"}

# VDF 庫分類歸納(名→類;順序=優先)
DB_CATS = [
    ("價量", r"^(tw_daily_prices|tw_prices_adj|tw_listings|tw_universe|tw_trading_daily|tw_rest_daily|tw_daily)"),
    ("籌碼", r"^tw_chip"),
    ("營收", r"(monthly_revenue|revenue_momentum|etf_revenue)"),
    ("財報", r"^(tw_financial|fin_|financial)"),
    ("ETF", r"(^etf_|holdings|active_tw|etf_book|etf_stats)"),
    ("宏觀", r"(macro|fred|us_)"),
    ("國際", r"(^global|factset|analyst|features_daily|cross_)"),
    ("VRN 報告", r"^vrn_"),
    ("治理", r"(policy|via_|registry|ledger|sync)"),
]

# 已知頁 → 再生短令(自適應:頁在=連、缺=ABSENT;再生令只是提示,不代跑)
REFRESH = {
    "VIA_UI_MasterControl_v0100.html": "via-ui(Manager ui)", "VIA_UI_CentralGovernanceConsole_v0100.html": "via-vcgc page --publish",
    "VIA_UI_InputConsole_v0100.html": "via-console build", "VIA_UI_VDFArchitecture_v0100.html": "via-vdfarch build",
    "VIA_UI_VRNControlTower_v0100.html": "via-vrnui", "VIA_UI_DailyBrief_v0100.html": "via-vrnui", "VIA_UI_Dashboard_v0100.html": "via-famui vap",
    "VIA_UI_StdDashboard_v0100.html": "via-famui vap", "VIA_UI_VapStack_v0100.html": "via-bus one vap_stack", "VIA_UI_WorkflowComposer_v0100.html": "via-workflow page --publish",
    "VIA_UI_RevenueConsensusAnalysis_v0100.html": "via-vtmra(eng069 run)", "VIA_UI_ActiveETFHoldingsHistory_v0100.html": "via-etfhist",
    "VIA_UI_System_v0100.html": "via-famui vdf(MDL120 SystemUI)", "VIA_UI_CommandDeck_v0100.html": "VIA.ps1(DeckServer)", "VIA_UI_TestResults_v0100.html": "via-grid",
}
FAMILY_HINT = [("vrn", r"(VRN|DailyBrief|ReportCards|Revenue|InputConsole|StoryRotation)"), ("vdf", r"(VDF|ActiveETF|DataCatalog|GlobalMarkets|System_v)"),
               ("vap", r"(Vap|Dashboard|Plotly)"), ("central", r"(MasterControl|CentralGovernance|Command|Governance|Hub|Portal|Workflow|Handover|Charter|Roster|Registry|Sync|Intake|Lifecycle|Product|Project|Test|Atlas|Console|Template|Component|Prompt|PsAst|SSOT|Unified|UserTest|Base)")]

STYLE_TOKENS = {"font": "'Segoe UI',system-ui,-apple-system,'Noto Sans TC',sans-serif", "size": "12.5px", "line": "1.45", "radius": "6px", "gap": "10px",
                "bg": "#f6f7f9", "panel": "#ffffff", "ink": "#1f2937", "muted": "#6b7280", "line_color": "#e5e7eb", "accent": "#1d4ed8",
                "lamps": {"GREEN": "#15803d", "OK": "#15803d", "YELLOW": "#b45309", "AMBER": "#b45309", "RED": "#b91c1c", "FAIL": "#b91c1c", "GATED": "#6d28d9", "ABSENT": "#6b7280", "NODATA": "#0e7490", "PLAN": "#1d4ed8", "TIMEOUT": "#9a3412", "DEFAULT": "#0f766e", "NEED_INPUT": "#b45309"},
                "rule": "小而專業:12.5px 字級、緊湊表格、單色系、無裝飾陰影;燈色只講狀態;零 CDN;手機單欄 @media(max-width:900px)"}


def _now() -> str:
    return _dt.datetime.now().isoformat(timespec="seconds")


def _json(p: Path) -> dict | None:
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except Exception:
        return None


def _newest(root: Path, pat: str) -> Path | None:
    hits = sorted(root.glob(pat)) if root.exists() else []
    return hits[-1] if hits else None


def _arg(a: list, flag: str, default=None):
    if flag in a:
        i = a.index(flag)
        if i + 1 < len(a):
            return a[i + 1]
    return default


# ---------------------------------------------------------------- ① 目錄
def load_catalog(spec_path: Path = SPEC) -> list:
    s = _json(spec_path) or {}
    rows = []
    for fam, f in (s.get("families") or {}).items():
        for g in f.get("groups") or []:
            for it in g.get("items") or []:
                e = it.get("engine") or {}
                rows.append({"id": it.get("id"), "zh": it.get("zh"), "family": fam, "group": g.get("id"), "verb": e.get("verb") or [], "glob": e.get("glob"), "dir": e.get("dir"),
                             "params": it.get("params") or [], "net": bool(it.get("net")), "outputs": it.get("outputs") or []})
    return rows


def catalog_index(rows: list) -> dict:
    return {r["id"]: r for r in rows if r.get("id")}


# ---------------------------------------------------------------- ② 工作流:合約自適應
def node_check(item: dict | None, item_id: str) -> dict:
    if item is None:
        return {"id": item_id, "state": "ABSENT", "why": "冊上無此項(VIA_InputConsole_Spec)"}
    need = [p for p in item.get("params", []) if p in PARAM_INPUT]
    dflt = [p for p in item.get("params", []) if p in PARAM_DEFAULT]
    res = [p for p in item.get("params", []) if p in PARAM_RESOLVE]
    unknown = [p for p in item.get("params", []) if p not in PARAM_INPUT | PARAM_DEFAULT | PARAM_RESOLVE]
    if item.get("net"):
        st, why = "GATED", "觸網項:匯流排問同意閘(VIA_NET_CONSENT/SCRAPE;我不代設)"
    elif need or unknown:
        st, why = "NEED_INPUT", "要操作員給:" + ",".join(need + unknown)
    elif dflt or res:
        st, why = "DEFAULT", "參數有預設/可解:" + ",".join(dflt + res)
    else:
        st, why = "OK", "無外參"
    return {"id": item_id, "family": item.get("family"), "state": st, "why": why, "need": need, "default": dflt, "resolve": res, "net": bool(item.get("net"))}


def edge_check(a: dict | None, b: dict | None) -> dict:
    if not a or not b:
        return {"state": "ABSENT", "why": "端點不在冊"}
    same = a.get("family") == b.get("family")
    hand = [o for o in a.get("outputs", []) if isinstance(o, str)]
    return {"state": "OK" if same else "CROSS", "why": ("同家族;交接 " + ";".join(x[:28] for x in hand[:2])) if same else "跨家族(各自家族境 python;交接靠庫/報告檔)"}


_ORDER = {"ABSENT": 0, "GATED": 1, "NEED_INPUT": 2, "CROSS": 3, "DEFAULT": 4, "OK": 5}


def validate(wf: dict, rows: list | None = None) -> dict:
    rows = rows if rows is not None else load_catalog()
    idx = catalog_index(rows)
    nodes = [node_check(idx.get(n), n) for n in wf.get("nodes") or []]
    edges = [dict(edge_check(idx.get(a), idx.get(b)), **{"from": a, "to": b}) for a, b in zip(wf.get("nodes") or [], (wf.get("nodes") or [])[1:])]
    states = [n["state"] for n in nodes] + [e["state"] for e in edges if e["state"] in ("ABSENT",)]
    worst = min(states, key=lambda s: _ORDER.get(s, 9)) if states else "OK"
    return {"id": wf.get("id"), "zh": wf.get("zh"), "profile": wf.get("profile", "test"), "n": len(nodes), "verdict": worst, "nodes": nodes, "edges": edges,
            "families": sorted({n.get("family") for n in nodes if n.get("family")}), "net_nodes": [n["id"] for n in nodes if n.get("net")], "need_input": [n["id"] for n in nodes if n["state"] == "NEED_INPUT"]}


def load_workflows(path: Path = WF_SSOT) -> list:
    return (_json(path) or {}).get("workflows") or []


def find_workflow(wf_id: str, path: Path = WF_SSOT) -> dict | None:
    return next((w for w in load_workflows(path) if w.get("id") == wf_id), None)


def _bus_path() -> Path | None:
    return _newest(HERE, "CGC_MDL148_EngineBus_v*.py")


def bus_runner(item_id: str, profile: str, timeout: int) -> dict:
    """真跑一節點=匯流排 call --item <id> --apply --profile <p>(家族境/閘/環境全在匯流排;本檔不另起爐灶)。"""
    bp = _bus_path()
    if not bp:
        return {"id": item_id, "state": "ABSENT", "why": "匯流排 CGC_MDL148_EngineBus_v*.py 缺"}
    argv = [sys.executable, str(bp), "call", "--item", item_id, "--apply", "--profile", profile]
    t0 = _dt.datetime.now()
    try:
        r = subprocess.run(argv, capture_output=True, text=True, timeout=timeout, cwd=str(VIA))
        out = r.stdout or ""
        js = None
        if "{" in out:
            try:
                js = json.loads(out[out.index("{"):])
            except Exception:
                js = None
        rec = {"id": item_id, "state": (js or {}).get("state") or ("GREEN" if r.returncode == 0 else "RED"), "why": (js or {}).get("why") or "", "rc": r.returncode,
               "engine": (js or {}).get("engine"), "tail": [l for l in ((js or {}).get("stdout_tail") or out).splitlines() if l.strip()][-6:] if js or out else [l for l in (r.stderr or "").splitlines() if l.strip()][-4:]}
    except subprocess.TimeoutExpired:
        rec = {"id": item_id, "state": "TIMEOUT", "why": f"逾時 {timeout}s", "rc": None, "tail": []}
    except Exception as exc:
        rec = {"id": item_id, "state": "RED", "why": f"{type(exc).__name__}:{str(exc)[:100]}", "rc": 1, "tail": []}
    rec["secs"] = round((_dt.datetime.now() - t0).total_seconds(), 1)
    return rec


def run_workflow(wf: dict, profile: str | None = None, continue_on_red: bool = False, timeout: int = 1800, runner=None, out: Path = OUT, do_print: bool = True) -> dict:
    runner = runner or bus_runner
    profile = profile or wf.get("profile") or "test"
    v = validate(wf)
    rep = {"schema": "VIA.Workflow.run.v1", "id": wf.get("id"), "zh": wf.get("zh"), "profile": profile, "ts": _now(), "validate": v["verdict"], "results": [], "verdict": "GREEN", "counts": {}}
    if do_print:
        print(f"=== [via-workflow run] {wf.get('id')} · {wf.get('zh')} · profile {profile} · 合約 {v['verdict']} · 節點 {v['n']} ===")
    stop = False
    for n in wf.get("nodes") or []:
        if stop:
            rep["results"].append({"id": n, "state": "SKIP", "why": "前節點 RED/TIMEOUT(--continue 才續跑)"})
            continue
        r = runner(n, profile, timeout)
        rep["results"].append(r)
        if do_print:
            print(f"  [{r['state']:<7}] {n:<22} {r.get('secs', 0)}s {str(r.get('why') or '')[:110]}")
            for l in (r.get("tail") or [])[-2:]:
                print(f"           │ {l[:150]}")
        if r["state"] in ("RED", "TIMEOUT") and not continue_on_red:
            stop = True
    for r in rep["results"]:
        rep["counts"][r["state"]] = rep["counts"].get(r["state"], 0) + 1
    if any(r["state"] in ("RED", "TIMEOUT") for r in rep["results"]):
        rep["verdict"] = "RED"
    elif any(r["state"] in ("GATED", "ABSENT", "NODATA", "AMBER", "SKIP") for r in rep["results"]):
        rep["verdict"] = "YELLOW"
    out.mkdir(parents=True, exist_ok=True)
    stamp = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    (out / f"RUN_{stamp}_{wf.get('id')}.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    (out / "WORKFLOW_latest.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    if do_print:
        print(f"[via-workflow] 判定 {rep['verdict']} · {rep['counts']} · 存證 {out / 'WORKFLOW_latest.json'} · 頁:via-workflow page(實測面板自動帶最新一跑)")
    return rep


# ---------------------------------------------------------------- ③ U/I 契約
_UI_RX = re.compile(r"VIA_UI_[A-Za-z0-9]+_v\d{4}\.html")


def _scan_owners(roots: list) -> dict:
    owners: dict = {}
    for root in roots:
        if not root.exists():
            continue
        for p in (root.glob("*.py") if root == VIA else root.rglob("*.py")):
            sp = str(p)
            if "/references/" in sp or "RetiredEngines" in sp or "SCOPE_COPY" in sp or "__pycache__" in sp:
                continue
            try:
                t = p.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            for name in set(_UI_RX.findall(t)):
                owners.setdefault(name, set()).add(p.name)
    return owners


def _family_of(name: str) -> str:
    for fam, rx in FAMILY_HINT:
        if re.search(rx, name):
            return fam
    return "central"


KNOWN_OWNERS = {"VIA_UI_VDFArchitecture_v0100.html": ("functional modules/VDF/engine", "VDF_ENG073_DataArchitecture_v*.py"),   # 產生器組字串出頁名,實掃找不到 → 冊上明給(仍取尾版)
                "VIA_UI_VRNControlTower_v0100.html": ("functional modules/VRN", "VRN_ENG079_ControlTower*_v*.py")}
_LINKERS = re.compile(r"^CGC_MDL(064|095|105|116|122|136|138|148|153)_")     # 格子/指揮台/治理台/統一殼/本檔=連結者(引用很多頁),不是頁的正主


def _owner_pick(refs: set, page: str = "") -> str:
    """擁有者(一頁一產生器):①頁名詞幹 ↔ 引擎名詞幹相扣(VIA_UI_InputConsole ↔ CGC_MDL139_InputConsole)取尾版;②否則引用它最多版的非連結者家族尾版;③再否則任一引擎尾版。"""
    if page in KNOWN_OWNERS:
        d, g = KNOWN_OWNERS[page]
        hit = _newest(VIA / d, g)
        if hit:
            return hit.name
    eng = sorted(x for x in refs if re.match(r"^(CGC_MDL|VRN_ENG|VDF_ENG|VAP_ENG|SUP_MDL)\d+_|^VIA_SYSTEM_MANAGER_v", x))
    stem = re.sub(r"^VIA_UI_|_v\d{4}\.html$", "", page).lower()
    if stem:
        hit = [x for x in eng if (lambda n: n and (stem in n or n in stem))(re.sub(r"^(CGC_MDL|VRN_ENG|VDF_ENG|VAP_ENG|SUP_MDL)\d+_|_v\d{4}\.py$", "", x).lower().replace("via_system_manager", "mastercontrol"))]
        if hit:
            return sorted(hit)[-1]
    fam: dict = {}
    for c in eng:
        if _LINKERS.match(c):
            continue
        fam.setdefault(re.sub(r"_v\d{4}\.py$", "", c), []).append(c)
    if fam:
        k = sorted(fam, key=lambda k: -len(fam[k]))[0]
        return sorted(fam[k])[-1]
    return eng[-1] if eng else ""


def ui_contract(ui_dir: Path = UI_SUPPORT, scan_roots: list | None = None, extra: list | None = None) -> dict:
    roots = scan_roots if scan_roots is not None else [VIA / "supportive modules" / "registry", VIA / "functional modules", VIA]   # VIA 根=Manager(總控頁產生器)
    owners = _scan_owners(roots)
    pages = []
    now = _dt.datetime.now()
    names = sorted(x.name for x in ui_dir.glob("VIA_UI_*.html")) if ui_dir.exists() else []
    for name in names:
        p = ui_dir / name
        st = p.stat()
        age_d = round((now - _dt.datetime.fromtimestamp(st.st_mtime)).total_seconds() / 86400, 1)
        refs = owners.get(name, set())
        pages.append({"page": name, "path": str(p), "family": _family_of(name), "owner": _owner_pick(refs, name), "refs": len(refs), "exists": True, "kb": round(st.st_size / 1024, 1),
                      "mtime": _dt.datetime.fromtimestamp(st.st_mtime).isoformat(timespec="seconds"), "age_days": age_d, "fresh": age_d <= 7, "refresh": REFRESH.get(name, ""), "lamp": "GREEN" if age_d <= 7 else "YELLOW"})
    for e in (extra or []):
        p = Path(e["path"])
        ok = p.exists()
        pages.append({"page": e["page"], "path": str(p), "family": e.get("family", "central"), "owner": e.get("owner", ""), "refs": 0, "exists": ok, "kb": round(p.stat().st_size / 1024, 1) if ok else 0,
                      "mtime": _dt.datetime.fromtimestamp(p.stat().st_mtime).isoformat(timespec="seconds") if ok else "", "age_days": None, "fresh": ok, "refresh": e.get("refresh", ""), "lamp": "GREEN" if ok else "ABSENT"})
    by_fam: dict = {}
    for pg in pages:
        by_fam[pg["family"]] = by_fam.get(pg["family"], 0) + 1
    return {"schema": "VIA.UIContract.v1", "batch": f"批{BATCH}", "ts": _now(), "ui_dir": str(ui_dir), "n": len(pages), "by_family": by_fam,
            "spec": {"zero_cdn": "頁面不得引用 https:// 的 script/link;字型走系統字", "snapshot_live": "頁面內嵌 JSON 快照(SNAPSHOT);樞紐 http://127.0.0.1:8765 在聽才 LIVE 重取(/api/console/status),失敗靜默",
                     "no_popup": "產生器不開瀏覽器;via-open 才開(零彈窗律)", "owner_rule": "一頁一產生器(L30);中央(VCGC 十二段)只連結不重造;頁在=連、不在=ABSENT",
                     "handoff": "引擎→頁:引擎落 JSON 於 VIA_Reports/<家族>/*_latest.json,產生器讀 JSON 產頁;頁不直讀庫", "style": STYLE_TOKENS},
            "pages": pages}


def write_ui_contract(apply: bool = False, do_print: bool = True) -> dict:
    extra = [{"page": "FAMILY_UI_latest.html", "path": str(REPORTS / "ui" / "FAMILY_UI_latest.html"), "family": "central", "owner": "CGC_MDL138_FamilyUI", "refresh": "via-famui all"},
             {"page": "WORKFLOW_COMPOSER.html", "path": str(OUT / "WORKFLOW_COMPOSER.html"), "family": "central", "owner": "CGC_MDL153_WorkflowComposer", "refresh": "via-workflow page"}]
    c = ui_contract(extra=extra)
    (REPORTS / "ui").mkdir(parents=True, exist_ok=True)
    (REPORTS / "ui" / "UI_CONTRACT_latest.json").write_text(json.dumps(c, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    if apply:
        UI_SSOT.write_text(json.dumps(c, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    if do_print:
        print(f"=== [via-workflow ui-contract] 頁 {c['n']} · {c['by_family']} · {'已寫入 SSOT ' + UI_SSOT.name if apply else '只落 VIA_Reports/ui(--apply 才入倉)'} ===")
        for pg in c["pages"]:
            print(f"  [{pg['lamp']:<6}] {pg['family']:<7} {pg['page']:<46} {pg['owner'] or '-':<48} {pg['kb']:>7} KB · {pg['refresh'] or '-'}")
    return c


# ---------------------------------------------------------------- db-summary
def db_summary(tables: dict | None = None, console_path: Path | None = None) -> dict:
    if tables is None:
        j = _json(console_path or (REPORTS / "console" / "CONSOLE_latest.json")) or {}
        tables = ((j.get("db") or {}).get("tables") or {})
        src = (j.get("db") or {}).get("source") or ("ABSENT" if not j else "")
    else:
        src = "given"
    cats: dict = {c: {"cat": c, "tables": [], "rows": 0, "newest": "", "worst_lag": None} for c, _ in DB_CATS}
    cats["其他"] = {"cat": "其他", "tables": [], "rows": 0, "newest": "", "worst_lag": None}
    for t, v in sorted((tables or {}).items()):
        cat = next((c for c, rx in DB_CATS if re.search(rx, t)), "其他")
        e = cats[cat]
        e["tables"].append(t)
        e["rows"] += int((v or {}).get("rows") or 0)
        mx = str((v or {}).get("max") or "")[:10]
        if mx and mx > e["newest"]:
            e["newest"] = mx
        lag = (v or {}).get("lag_days")
        if isinstance(lag, int):
            e["worst_lag"] = lag if e["worst_lag"] is None else max(e["worst_lag"], lag)
    rows = []
    for c in list(dict.fromkeys([c for c, _ in DB_CATS] + ["其他"])):
        e = cats[c]
        if not e["tables"]:
            continue
        lag = e["worst_lag"]
        e["n"] = len(e["tables"])
        e["lamp"] = "GREEN" if isinstance(lag, int) and lag <= 3 else ("YELLOW" if isinstance(lag, int) and lag <= 14 else ("NODATA" if lag is None else "RED"))
        rows.append(e)
    return {"schema": "VIA.DBSummary.v1", "ts": _now(), "source": src, "n_tables": len(tables or {}), "categories": rows,
            "verdict": ("ABSENT" if not tables else ("RED" if any(r["lamp"] == "RED" for r in rows) else ("YELLOW" if any(r["lamp"] == "YELLOW" for r in rows) else "GREEN")))}


def write_db_summary(do_print: bool = True) -> dict:
    d = db_summary()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "DB_SUMMARY_latest.json").write_text(json.dumps(d, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    if do_print:
        print(f"=== [via-workflow db-summary] VDF 庫分類歸納 · {d['verdict']} · 表 {d['n_tables']} · 來源 {d['source']} ===")
        for r in d["categories"]:
            print(f"  [{r['lamp']:<6}] {r['cat']:<7} 表 {r['n']:>2} · 列 {r['rows']:>12,} · 最新 {r['newest'] or '-':<10} · 最壞滯後 {r['worst_lag'] if r['worst_lag'] is not None else '?'} 日 · {', '.join(r['tables'][:6])}{'…' if len(r['tables']) > 6 else ''}")
    return d


# ---------------------------------------------------------------- 實測面板(最新真跑;誠實 ABSENT)
def latest_results() -> dict:
    def lamp(j, key="verdict"):
        return (j or {}).get(key) or ("ABSENT" if j is None else "?")
    bus = _json(REPORTS / "engine_bus" / "ENGINE_BUS_latest.json")
    rg = _json(REPORTS / "rungate" / "RUNGATE_latest.json")
    vt = _json(REPORTS / "vtmra" / "VTMRA_latest.json")
    co = _json(REPORTS / "console" / "CONSOLE_latest.json")
    vc = _json(REPORTS / "vcgc" / "VCGC_latest.json")
    wf = _json(OUT / "WORKFLOW_latest.json")
    cy = _json(REPORTS / "central_governance" / "CYCLES_latest.json")
    return {"bus": {"state": "ABSENT" if bus is None else "OK", "ts": (bus or {}).get("ts"), "profile": (bus or {}).get("profile"), "counts": (bus or {}).get("counts"),
                    "reds": [{"id": r.get("id"), "why": str(r.get("why") or "")[:120]} for r in (bus or {}).get("results", []) if r.get("state") in ("RED", "TIMEOUT")][:12]},
            "rungate": {"state": lamp(rg), "ts": (rg or {}).get("ts"), "families": (rg or {}).get("families") if isinstance((rg or {}).get("families"), dict) else None},
            "vtmra": {"state": lamp(vt), "ts": (vt or {}).get("ts"), "members": {r.get("id"): r.get("state") for r in (vt or {}).get("results", [])}},
            "console": {"state": lamp(co), "ts": (co or {}).get("ts"), "tables": len(((co or {}).get("db") or {}).get("tables") or {}), "reports": len(((co or {}).get("vrn") or {}).get("reports") or [])},
            "vcgc": {"state": "ABSENT" if vc is None else "OK", "ts": (vc or {}).get("ts"), "batch": (vc or {}).get("batch")},
            "workflow": {"state": lamp(wf), "id": (wf or {}).get("id"), "ts": (wf or {}).get("ts"), "counts": (wf or {}).get("counts"), "results": [{"id": r.get("id"), "state": r.get("state"), "why": str(r.get("why") or "")[:100], "secs": r.get("secs")} for r in (wf or {}).get("results", [])]},
            "cycles": {"state": lamp(cy), "n": (cy or {}).get("n"), "live": (cy or {}).get("live"), "by_zone": (cy or {}).get("by_zone")}}


# ---------------------------------------------------------------- ④ 頁(零 CDN;內嵌快照;緊湊專業)
_PAGE = r"""<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>VIA 工作流重組台 v__VERSION__</title>
<style>
:root{--font:__FONT__;--size:__SIZE__;--bg:__BG__;--panel:__PANEL__;--ink:__INK__;--muted:__MUTED__;--line:__LINE__;--accent:__ACCENT__}
*{box-sizing:border-box}body{margin:0;font-family:var(--font);font-size:var(--size);line-height:1.45;background:var(--bg);color:var(--ink)}
header{padding:10px 16px;background:var(--panel);border-bottom:1px solid var(--line);display:flex;gap:14px;align-items:baseline;flex-wrap:wrap}
header h1{font-size:15px;margin:0}header small{color:var(--muted)}
main{display:grid;grid-template-columns:270px 1fr 380px;gap:10px;padding:10px}
@media(max-width:900px){main{grid-template-columns:1fr}}
section{background:var(--panel);border:1px solid var(--line);border-radius:6px;padding:10px;min-width:0}
h2{font-size:13px;margin:0 0 8px;color:#111827}h3{font-size:12px;margin:10px 0 4px;color:var(--muted);font-weight:600}
table{border-collapse:collapse;width:100%;font-size:12px}th,td{border-bottom:1px solid var(--line);padding:3px 5px;text-align:left;vertical-align:top}th{color:var(--muted);font-weight:600}
.chip{display:inline-block;padding:0 6px;border-radius:9px;color:#fff;font-size:11px;line-height:17px}
.item{padding:3px 6px;border:1px solid var(--line);border-radius:5px;margin:3px 0;cursor:pointer;background:#fafafa}.item:hover{border-color:var(--accent)}
.item b{font-weight:600}.item small{color:var(--muted)}
.node{display:inline-flex;align-items:center;gap:4px;padding:2px 6px;border:1px solid var(--line);border-radius:5px;margin:2px;background:#f3f4f6}
.node button{border:0;background:transparent;cursor:pointer;color:var(--muted);padding:0 2px}
textarea{width:100%;font:11px/1.4 Consolas,monospace;border:1px solid var(--line);border-radius:5px;padding:6px;min-height:110px}
code,pre{font:11px/1.4 Consolas,monospace}pre{background:#f3f4f6;padding:6px;border-radius:5px;white-space:pre-wrap;word-break:break-all;margin:4px 0}
select,input,button.b{font:inherit;padding:3px 6px;border:1px solid var(--line);border-radius:5px;background:#fff}button.b{cursor:pointer}
.muted{color:var(--muted)}.k{white-space:nowrap}.wrap{word-break:break-all}
svg text{font-size:10px;fill:#1f2937}
</style></head><body>
<header><h1>VIA 工作流重組台 <small>v__VERSION__ · 批__BATCH__ · __TS__</small></h1><small>目錄=冊上引擎積木 · 重組=依序點選 · 執行只經匯流排(閘不變)· 零 CDN · 零彈窗 · 樞紐 <span id="hub">SNAPSHOT</span></small></header>
<main>
<section><h2>目錄(引擎積木)</h2><input id="q" placeholder="篩選 id/中文" style="width:100%;margin-bottom:6px"><div id="catalog"></div></section>
<section><h2>工作流</h2>
<div style="display:flex;gap:6px;flex-wrap:wrap;align-items:center"><select id="wfsel"></select><button class="b" id="newwf">新工作流</button><label class="muted">profile <select id="profile"><option>test</option><option>run</option></select></label><button class="b" id="validate">驗合約</button></div>
<div id="nodes" style="margin:8px 0"></div>
<div id="graph"></div>
<div id="valid"></div>
<h3>執行(貼到 PowerShell;頁面不代跑=零彈窗律)</h3><pre id="cmd"></pre>
<h3>匯出 JSON(存回 VIA_Workflow_SSOT_v0100.json 的 workflows[] 即入冊)</h3><textarea id="json"></textarea>
</section>
<section><h2>實測面板(最新真跑;自動展開)</h2><div id="results"></div>
<h2 style="margin-top:12px">VDF 庫分類歸納</h2><div id="dbsum"></div>
<h2 style="margin-top:12px">U/I 對接(頁在=連;不在=ABSENT)</h2><div id="uic"></div></section>
</main>
<script id="via-data" type="application/json">__JSON__</script>
<script>
(function(){
var D=JSON.parse(document.getElementById('via-data').textContent);var L=D.lamps||{};
function esc(s){return String(s==null?'':s).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]});}
function chip(s){s=String(s==null?'?':s);return '<span class="chip" style="background:'+(L[s]||'#6b7280')+'">'+esc(s)+'</span>';}
var idx={};D.catalog.forEach(function(r){idx[r.id]=r;});
var wfs=JSON.parse(JSON.stringify(D.workflows||[]));var cur=wfs.length?0:-1;
function renderCatalog(){var q=(document.getElementById('q').value||'').toLowerCase();var fams={};D.catalog.forEach(function(r){if(q&&(r.id+' '+r.zh).toLowerCase().indexOf(q)<0)return;(fams[r.family]=fams[r.family]||[]).push(r);});
 var h='';Object.keys(fams).forEach(function(f){h+='<h3>'+esc(f)+' · '+fams[f].length+'</h3>';fams[f].forEach(function(r){h+='<div class="item" data-id="'+esc(r.id)+'"><b>'+esc(r.id)+'</b> '+(r.net?chip('GATED'):'')+'<br><small>'+esc(r.zh)+'</small></div>';});});
 document.getElementById('catalog').innerHTML=h;}
function renderWfSel(){var s=document.getElementById('wfsel');s.innerHTML=wfs.map(function(w,i){return '<option value="'+i+'"'+(i===cur?' selected':'')+'>'+esc(w.id)+' · '+esc(w.zh||'')+'</option>';}).join('');}
function nodeState(id){var r=idx[id];if(!r)return ['ABSENT','冊上無此項'];if(r.net)return ['GATED','觸網:匯流排問閘'];var need=(r.params||[]).filter(function(p){return D.param_input.indexOf(p)>=0;});if(need.length)return ['NEED_INPUT','要給:'+need.join(',')];if((r.params||[]).length)return ['DEFAULT','參數有預設'];return ['OK','無外參'];}
function renderNodes(){var el=document.getElementById('nodes');if(cur<0){el.innerHTML='<span class="muted">尚無工作流:按「新工作流」再從左側點積木</span>';return;}var w=wfs[cur];
 el.innerHTML=(w.nodes||[]).map(function(n,i){var st=nodeState(n);return '<span class="node">'+chip(st[0])+' <b>'+esc(n)+'</b><button data-i="'+i+'" data-op="up">▲</button><button data-i="'+i+'" data-op="down">▼</button><button data-i="'+i+'" data-op="del">✕</button></span>';}).join(' → ')||'<span class="muted">(空;點左側積木加入)</span>';
 renderGraph();renderCmd();document.getElementById('json').value=JSON.stringify(w,null,1);}
function renderGraph(){var g=document.getElementById('graph');if(cur<0){g.innerHTML='';return;}var w=wfs[cur];var n=(w.nodes||[]).length;if(!n){g.innerHTML='';return;}var W=Math.max(320,n*150),H=70;var s='<svg width="100%" viewBox="0 0 '+W+' '+H+'" style="max-width:'+W+'px">';
 (w.nodes||[]).forEach(function(id,i){var x=20+i*150,st=nodeState(id)[0];s+='<rect x="'+x+'" y="20" width="120" height="30" rx="6" fill="#f3f4f6" stroke="'+(L[st]||'#6b7280')+'" stroke-width="1.5"/><text x="'+(x+60)+'" y="39" text-anchor="middle">'+esc(id.length>16?id.slice(0,15)+'…':id)+'</text>';if(i<n-1){s+='<line x1="'+(x+120)+'" y1="35" x2="'+(x+150)+'" y2="35" stroke="#9ca3af" stroke-width="1.5"/><polygon points="'+(x+146)+',31 '+(x+150)+',35 '+(x+146)+',39" fill="#9ca3af"/>';}});
 g.innerHTML=s+'</svg>';}
function renderCmd(){var w=wfs[cur];var p=document.getElementById('profile').value;var inCatalog=D.workflow_ids.indexOf(w.id)>=0;document.getElementById('cmd').textContent=inCatalog?('via-workflow run '+w.id+' --profile '+p):('# 先把匯出 JSON 存成 my_wf.json,再:\nvia-workflow run --file .\\my_wf.json --profile '+p);}
function validateNow(){if(cur<0)return;var w=wfs[cur];var worst='OK',order={ABSENT:0,GATED:1,NEED_INPUT:2,DEFAULT:4,OK:5};var rows=(w.nodes||[]).map(function(n){var st=nodeState(n);if(order[st[0]]<order[worst])worst=st[0];return '<tr><td>'+esc(n)+'</td><td>'+chip(st[0])+'</td><td>'+esc(st[1])+'</td><td>'+esc((idx[n]||{}).family||'-')+'</td></tr>';});
 document.getElementById('valid').innerHTML='<h3>合約自適應(L31/L40)· 整條 '+chip(worst)+'</h3><table><tr><th>節點</th><th>態</th><th>因由</th><th>家族</th></tr>'+rows.join('')+'</table>';}
document.getElementById('catalog').addEventListener('click',function(e){var it=e.target.closest('.item');if(!it)return;if(cur<0){wfs.push({id:'my_workflow',zh:'新工作流',profile:'test',nodes:[]});cur=wfs.length-1;renderWfSel();}wfs[cur].nodes.push(it.getAttribute('data-id'));renderNodes();validateNow();});
document.getElementById('nodes').addEventListener('click',function(e){var b=e.target.closest('button');if(!b||cur<0)return;var i=+b.getAttribute('data-i'),op=b.getAttribute('data-op'),a=wfs[cur].nodes;if(op==='del')a.splice(i,1);if(op==='up'&&i>0){var t=a[i-1];a[i-1]=a[i];a[i]=t;}if(op==='down'&&i<a.length-1){var t2=a[i+1];a[i+1]=a[i];a[i]=t2;}renderNodes();validateNow();});
document.getElementById('wfsel').addEventListener('change',function(e){cur=+e.target.value;renderNodes();validateNow();});
document.getElementById('newwf').addEventListener('click',function(){var id=prompt('工作流 id(英數底線)','my_workflow')||'my_workflow';wfs.push({id:id,zh:'新工作流',profile:'test',nodes:[]});cur=wfs.length-1;renderWfSel();renderNodes();validateNow();});
document.getElementById('profile').addEventListener('change',renderCmd);document.getElementById('validate').addEventListener('click',validateNow);document.getElementById('q').addEventListener('input',renderCatalog);
function renderResults(){var R=D.results||{};var h='';
 var wf=R.workflow||{};h+='<h3>工作流最新一跑 '+chip(wf.state)+' '+esc(wf.id||'')+' <span class="muted">'+esc(wf.ts||'')+'</span></h3>';if((wf.results||[]).length){h+='<table>'+wf.results.map(function(r){return '<tr><td class="k">'+esc(r.id)+'</td><td>'+chip(r.state)+'</td><td>'+esc(r.secs||'')+'s</td><td class="wrap">'+esc(r.why||'')+'</td></tr>';}).join('')+'</table>';}
 var b=R.bus||{};h+='<h3>五矩陣 '+chip(b.state)+' <span class="muted">'+esc(b.ts||'')+' · '+esc(b.profile||'')+'</span></h3><div>'+esc(JSON.stringify(b.counts||{}))+'</div>';if((b.reds||[]).length){h+='<table>'+b.reds.map(function(r){return '<tr><td class="k">'+esc(r.id)+'</td><td class="wrap">'+esc(r.why)+'</td></tr>';}).join('')+'</table>';}
 var g=R.rungate||{};h+='<h3>RunGate '+chip(g.state)+' <span class="muted">'+esc(g.ts||'')+'</span></h3>';
 var v=R.vtmra||{};h+='<h3>VTMRA '+chip(v.state)+' <span class="muted">'+esc(v.ts||'')+'</span></h3><div>'+Object.keys(v.members||{}).map(function(k){return esc(k)+' '+chip(v.members[k]);}).join(' ')+'</div>';
 var c=R.console||{};h+='<h3>主控台 '+chip(c.state)+' <span class="muted">'+esc(c.ts||'')+' · 庫表 '+esc(c.tables)+' · VRN 報告 '+esc(c.reports)+'</span></h3>';
 var y=R.cycles||{};h+='<h3>G17 循環判讀 '+chip(y.state)+' <span class="muted">圈 '+esc(y.n)+' · 活樹 '+esc(y.live)+' · '+esc(JSON.stringify(y.by_zone||{}))+'</span></h3>';
 document.getElementById('results').innerHTML=h;}
function renderDb(){var S=D.db_summary||{};var h='<div>'+chip(S.verdict)+' 表 '+esc(S.n_tables)+' · 來源 '+esc(S.source||'-')+'</div><table><tr><th>類</th><th>燈</th><th>表</th><th>列</th><th>最新</th><th>最壞滯後</th></tr>'+(S.categories||[]).map(function(r){return '<tr><td>'+esc(r.cat)+'</td><td>'+chip(r.lamp)+'</td><td>'+esc(r.n)+'</td><td>'+esc((r.rows||0).toLocaleString())+'</td><td>'+esc(r.newest||'-')+'</td><td>'+esc(r.worst_lag==null?'?':r.worst_lag)+'</td></tr>';}).join('')+'</table>';document.getElementById('dbsum').innerHTML=h;}
function renderUi(){var U=D.ui||{};var h='<div class="muted">頁 '+esc(U.n)+' · '+esc(JSON.stringify(U.by_family||{}))+'</div><table><tr><th>頁</th><th>燈</th><th>擁有者</th><th>再生</th></tr>'+(U.pages||[]).map(function(p){var link=p.exists?'<a href="file:///'+esc(String(p.path).replace(/\\/g,'/'))+'">'+esc(p.page)+'</a>':esc(p.page);return '<tr><td class="wrap">'+link+'</td><td>'+chip(p.lamp)+'</td><td class="wrap">'+esc(p.owner||'-')+'</td><td class="wrap">'+esc(p.refresh||'-')+'</td></tr>';}).join('')+'</table>';document.getElementById('uic').innerHTML=h;}
renderCatalog();renderWfSel();renderNodes();validateNow();renderResults();renderDb();renderUi();
try{var ctl=new AbortController();setTimeout(function(){ctl.abort();},1500);fetch('http://127.0.0.1:8765/api/console/status',{signal:ctl.signal}).then(function(r){return r.ok?r.json():null;}).then(function(j){if(j){document.getElementById('hub').textContent='LIVE';}}).catch(function(){});}catch(e){}
})();
</script></body></html>
"""


def page_html(catalog: list, workflows: list, results: dict, dbs: dict, ui: dict, ts: str | None = None) -> str:
    data = {"catalog": catalog, "workflows": workflows, "workflow_ids": [w.get("id") for w in workflows], "results": results, "db_summary": dbs, "ui": {"n": ui.get("n"), "by_family": ui.get("by_family"), "pages": ui.get("pages", [])},
            "param_input": sorted(PARAM_INPUT), "lamps": STYLE_TOKENS["lamps"]}
    t = STYLE_TOKENS
    js = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    return (_PAGE.replace("__VERSION__", VERSION).replace("__BATCH__", str(BATCH)).replace("__TS__", _html.escape(ts or _now())).replace("__FONT__", t["font"]).replace("__SIZE__", t["size"])
            .replace("__BG__", t["bg"]).replace("__PANEL__", t["panel"]).replace("__INK__", t["ink"]).replace("__MUTED__", t["muted"]).replace("__LINE__", t["line_color"]).replace("__ACCENT__", t["accent"]).replace("__JSON__", js))


def write_page(publish: bool = False, do_print: bool = True) -> dict:
    cat = load_catalog()
    wfs = load_workflows()
    res = latest_results()
    dbs = db_summary()
    ui = _json(REPORTS / "ui" / "UI_CONTRACT_latest.json") or _json(UI_SSOT) or ui_contract()
    html = page_html(cat, wfs, res, dbs, ui)
    OUT.mkdir(parents=True, exist_ok=True)
    p = OUT / "WORKFLOW_COMPOSER.html"
    p.write_text(html, encoding="utf-8")
    pub = None
    if publish:
        UI_SUPPORT.mkdir(parents=True, exist_ok=True)
        pub = UI_SUPPORT / PAGE_NAME
        pub.write_text(html, encoding="utf-8")
    if do_print:
        print(f"=== [via-workflow page] 積木 {len(cat)} · 工作流 {len(wfs)} · 實測面板 {res['workflow']['state']}/{res['bus']['state']}/{res['rungate']['state']}/{res['vtmra']['state']} · 庫分類 {dbs['verdict']} · U/I 頁 {ui.get('n')} → {p}" + (f" · 已發佈 {pub}" if pub else " (未入倉;--publish 才入倉)") + " · 開:via-open")
    return {"out": str(p), "published": str(pub) if pub else None, "n_catalog": len(cat), "n_workflows": len(wfs)}


# ---------------------------------------------------------------- selftest
def selftest() -> int:
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    rows = load_catalog()
    idx = catalog_index(rows)
    chk("① 目錄=冊上三家族項(id/zh/family/verb/params/net/outputs);≥40 項;id 唯一", len(rows) >= 40 and len(idx) == len(rows) and {"vdf", "vrn", "vap"} <= {r["family"] for r in rows} and all("verb" in r and "outputs" in r for r in rows), f"({len(rows)} 項)")
    wfs = load_workflows()
    seeds_ok = all(all(n in idx for n in w.get("nodes", [])) for w in wfs)
    chk("② 種子工作流八條全在冊(每節點 id 都解析得到;VATETF/VTMRA/VRN/VDF/VAP 各有)", len(wfs) >= 8 and seeds_ok and {"vatetf_pipeline", "vtmra_family", "vrn_report_chain", "vdf_daily_update", "vap_charts"} <= {w["id"] for w in wfs},
        f"({[n for w in wfs for n in w.get('nodes', []) if n not in idx]} 缺)")
    v1 = validate(find_workflow("vrn_logic_nlp") or {"id": "x", "nodes": []}, rows)
    v2 = validate(find_workflow("vdf_daily_update") or {"id": "x", "nodes": []}, rows)
    v3 = validate({"id": "bad", "nodes": ["vrn_logic", "no_such_item"]}, rows)
    v4 = validate({"id": "mix", "nodes": ["vrn_firstpage", "vap_stack"]}, rows)
    chk("③ 合約自適應:零網路無外參=OK;觸網=GATED;冊上無此項=ABSENT(整條最壞);要操作員給參數=NEED_INPUT;跨家族邊=CROSS", v1["verdict"] == "OK" and v2["verdict"] == "GATED" and v3["verdict"] == "ABSENT" and v4["nodes"][0]["state"] == "NEED_INPUT" and v4["edges"][0]["state"] == "CROSS" and "vrn_firstpage" in v4["need_input"])
    with tempfile.TemporaryDirectory() as td:
        T = Path(td)
        calls = []

        def fake(item_id, profile, timeout):
            calls.append((item_id, profile))
            return {"id": item_id, "state": {"vrn_logic": "GREEN", "fin_logic": "RED", "vrn_nlp": "GREEN"}.get(item_id, "GREEN"), "why": "", "secs": 0.1, "tail": []}
        r1 = run_workflow({"id": "t", "zh": "t", "profile": "test", "nodes": ["vrn_logic", "fin_logic", "vrn_nlp"]}, runner=fake, out=T, do_print=False)
        r2 = run_workflow({"id": "t2", "zh": "t", "profile": "test", "nodes": ["vrn_logic", "fin_logic", "vrn_nlp"]}, runner=fake, out=T, continue_on_red=True, do_print=False)
        chk("④ 執行:逐節點經 runner(匯流排 call --item --apply --profile);RED 後預設 SKIP 其餘(--continue 才續);判定 RED/YELLOW/GREEN;落 RUN_<ts>+WORKFLOW_latest",
            r1["verdict"] == "RED" and [x["state"] for x in r1["results"]] == ["GREEN", "RED", "SKIP"] and [x["state"] for x in r2["results"]] == ["GREEN", "RED", "GREEN"] and (T / "WORKFLOW_latest.json").exists() and len(list(T.glob("RUN_*.json"))) == 2 and calls[0] == ("vrn_logic", "test"))
        r3 = run_workflow({"id": "t3", "nodes": ["a", "b"]}, runner=lambda i, p, t: {"id": i, "state": "GATED" if i == "a" else "GREEN", "why": "閘", "secs": 0}, out=T, do_print=False)
        chk("⑤ GATED/ABSENT/NODATA 節點=YELLOW 不冒充綠、也不當壞", r3["verdict"] == "YELLOW" and r3["counts"] == {"GATED": 1, "GREEN": 1})
        ud = T / "ui"
        ud.mkdir()
        (ud / "VIA_UI_Alpha_v0100.html").write_text("<html>a</html>", encoding="utf-8")
        (ud / "VIA_UI_VRNControlTower_v0100.html").write_text("<html>b</html>", encoding="utf-8")
        eng = T / "eng"
        eng.mkdir()
        (eng / "CGC_MDL999_AlphaGen_v0102.py").write_text('OUT = "VIA_UI_Alpha_v0100.html"\n', encoding="utf-8")
        (eng / "CGC_MDL999_AlphaGen_v0101.py").write_text('OUT = "VIA_UI_Alpha_v0100.html"\n', encoding="utf-8")
        (eng / "CGC_MDL095_DeckServer_v0999.py").write_text('X = "VIA_UI_Alpha_v0100.html"\n', encoding="utf-8")
        c = ui_contract(ui_dir=ud, scan_roots=[eng], extra=[{"page": "GHOST.html", "path": str(T / "nope.html"), "family": "central", "owner": "X", "refresh": "via-x"}])
        pg = {p["page"]: p for p in c["pages"]}
        chk("⑥ U/I 契約:掃頁+產生器引用→擁有者=正主尾版(連結者 Deck/Grid 不算)、家族推斷、在/新鮮/大小/再生令;不在=ABSENT 誠實;規格段(零 CDN/SNAPSHOT-LIVE/零彈窗/一頁一產生器/樣式 tokens)",
            pg["VIA_UI_Alpha_v0100.html"]["owner"] == "CGC_MDL999_AlphaGen_v0102.py" and pg["VIA_UI_Alpha_v0100.html"]["refs"] == 3 and pg["VIA_UI_VRNControlTower_v0100.html"]["family"] == "vrn" and pg["VIA_UI_VRNControlTower_v0100.html"]["refresh"] == "via-vrnui"
            and pg["GHOST.html"]["lamp"] == "ABSENT" and not pg["GHOST.html"]["exists"] and all(k in c["spec"] for k in ("zero_cdn", "snapshot_live", "no_popup", "owner_rule", "style")) and c["n"] == 3)
        d = db_summary(tables={"tw_daily_prices": {"rows": 100, "max": "2026-09-12", "lag_days": 3}, "tw_chip_inst": {"rows": 5, "max": "2026-09-01", "lag_days": 14}, "vrn_report_basic": {"rows": 7}, "weird_x": {"rows": 1, "max": "2025-01-01", "lag_days": 400}, "us_macro": {"rows": 9, "max": "2026-09-14", "lag_days": 1}})
        cm = {r["cat"]: r for r in d["categories"]}
        chk("⑦ 庫分類歸納:價量/籌碼/VRN 報告/宏觀/其他 分對;列數加總;最新日取最大;最壞滯後取最大;燈 GREEN≤3/YELLOW≤14/RED/NODATA(無日期欄);整體最壞",
            cm["價量"]["lamp"] == "GREEN" and cm["籌碼"]["lamp"] == "YELLOW" and cm["VRN 報告"]["lamp"] == "NODATA" and cm["其他"]["lamp"] == "RED" and cm["宏觀"]["newest"] == "2026-09-14" and d["verdict"] == "RED" and d["n_tables"] == 5)
        chk("⑧ 空庫=ABSENT 誠實", db_summary(tables={})["verdict"] == "ABSENT")
        html = page_html(rows, wfs, {"workflow": {"state": "ABSENT", "results": []}, "bus": {"state": "ABSENT", "reds": []}, "rungate": {"state": "ABSENT"}, "vtmra": {"state": "ABSENT", "members": {}}, "console": {"state": "ABSENT"}, "vcgc": {}, "cycles": {"state": "ABSENT"}}, d, c, ts="2026-09-15T00:00:00")
        chk("⑨ 頁:零 CDN(無 https:// script/link)· 內嵌 JSON 快照 · 三欄(目錄/工作流+SVG/實測面板+庫分類+U/I 對接)· 手機單欄 · 緊湊字級 · 樞紐 LIVE 探針只打 127.0.0.1",
            not re.search(r'<(?:script|link)[^>]+https?://', html, re.I) and 'id="via-data"' in html and all(k in html for k in ("目錄(引擎積木)", "工作流", "實測面板", "VDF 庫分類歸納", "U/I 對接", "@media(max-width:900px)", "12.5px")) and "127.0.0.1:8765" in html and html.count("http") == html.count("http://127.0.0.1"))
        chk("⑩ 頁快照含目錄/工作流/庫分類/U/I 契約且 </ 逸出(不破 script)", '"workflow_ids"' in html and "vrn_logic_nlp" in html and "<\\/" in html or "</" not in json.dumps({"a": "</x>"}).replace("</", "<\\/"))
    ws = _json(WF_SSOT) or {}
    chk("⑪ SSOT 冊:VIA_Workflow_SSOT_v0100.json schema/batch/workflows(每條 id/zh/profile/nodes);profile ∈ test|run", ws.get("schema") == "VIA.Workflow.SSOT.v1" and all(set(w) >= {"id", "zh", "profile", "nodes"} and w["profile"] in ("test", "run") for w in ws.get("workflows", [])))
    src = Path(__file__).read_text(encoding="utf-8").split("def selftest")[0]
    chk("⑫ 律:零網路(無 requests/httpx/urllib)· 執行只經匯流排(call --item --apply)· 閘不代設(無 VIA_NET_CONSENT 賦值)· 零彈窗(無 webbrowser/startfile)· --publish 才入倉",
        all(("import " + k) not in src for k in ("requests", "httpx", "urllib", "webbrowser")) and '"call", "--item"' in src and "VIA_NET_CONSENT'] =" not in src and 'VIA_NET_CONSENT"] =' not in src and "startfile" not in src and "publish" in src)
    print(f"  [計] 十二檢 OK {12 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


# ---------------------------------------------------------------- CLI
def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print(f"=== 工作流重組台(CGC_MDL153 v{VERSION})· 十二檢自測(零網路;臨時夾)===")
        return selftest()
    verb = a[0] if a and not a[0].startswith("-") else "status"
    rest = a[1:]
    as_json = "--json" in a
    if verb == "catalog":
        rows = load_catalog()
        fam = _arg(rest, "--family")
        rows = [r for r in rows if not fam or r["family"] == fam]
        if as_json:
            print(json.dumps(rows, ensure_ascii=False, indent=1))
        else:
            print(f"=== [via-workflow catalog] 引擎積木 {len(rows)} 項(冊 VIA_InputConsole_Spec;net=觸網要閘)===")
            for r in rows:
                print(f"  {r['family']:<4} {r['id']:<22} {'NET' if r['net'] else '   '} verb {','.join(map(str, r['verb'])):<22} params {','.join(r['params']) or '-':<18} {str(r['zh'])[:48]}")
        return 0
    if verb in ("validate", "run"):
        f = _arg(rest, "--file")
        wf = _json(Path(f)) if f else find_workflow(rest[0] if rest and not rest[0].startswith("-") else "")
        if not wf:
            print("  [FAIL] 給 <wf_id>(冊上)或 --file <json>;冊:" + ",".join(w.get("id", "?") for w in load_workflows()))
            return 2
        if verb == "validate":
            v = validate(wf)
            if as_json:
                print(json.dumps(v, ensure_ascii=False, indent=1))
            else:
                print(f"=== [via-workflow validate] {v['id']} · {v['zh']} · 整條 {v['verdict']} · 家族 {v['families']} · 觸網 {v['net_nodes']} · 要給 {v['need_input']} ===")
                for n in v["nodes"]:
                    print(f"  [{n['state']:<10}] {n['id']:<22} {n['why']}")
                for e in v["edges"]:
                    print(f"     {e['from']} → {e['to']}: {e['state']} {e['why']}")
            return 0 if v["verdict"] not in ("ABSENT",) else 1
        rep = run_workflow(wf, profile=_arg(rest, "--profile"), continue_on_red="--continue" in rest, timeout=int(_arg(rest, "--timeout", "1800") or 1800), do_print=not as_json)
        if as_json:
            print(json.dumps(rep, ensure_ascii=False, indent=1))
        return 0 if rep["verdict"] == "GREEN" else (1 if rep["verdict"] == "RED" else 0)
    if verb == "ui-contract":
        c = write_ui_contract(apply="--apply" in rest, do_print=not as_json)
        if as_json:
            print(json.dumps(c, ensure_ascii=False, indent=1))
        return 0
    if verb == "db-summary":
        d = write_db_summary(do_print=not as_json)
        if as_json:
            print(json.dumps(d, ensure_ascii=False, indent=1))
        return 0
    if verb == "page":
        write_page(publish="--publish" in rest)
        return 0
    if verb == "status":
        res = latest_results()
        print(f"=== [via-workflow] 工作流重組台 v{VERSION} · 積木 {len(load_catalog())} · 工作流 {len(load_workflows())} · 最新一跑 {res['workflow']['state']} {res['workflow']['id'] or ''} · U/I 契約 {'在' if UI_SSOT.exists() else 'ABSENT(via-workflow ui-contract --apply)'} ===")
        print("  動詞:catalog | validate <id> | run <id> [--profile test|run] [--continue] | ui-contract [--apply] | db-summary | page [--publish]")
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
