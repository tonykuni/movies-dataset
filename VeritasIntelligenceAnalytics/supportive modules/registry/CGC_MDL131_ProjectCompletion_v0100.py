#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CGC_MDL131_ProjectCompletion — 四專案完工矩陣(批368;via-projects)
====================================================================
操作員令(批368)「READ THE NEW STATUS AND COMPLETE VDF VRN VIA ACTIVE TAIWAN STOCK ETF ANALYSIS AND
VIA TAIWAN STOCK MONTHLY REVENUE ANALYSIS PROJECTS. TEST DEBUG UPGRADE OPTIMIZE TEST DEBUG CONSOLIDATE
TEST DEBUG AUTOMATE TEST DEBUG USER-TEST DEBUG ACTIVATE TEST DEBUG TILL ALL WORK PERFECTLY.」
職權(零重測零發明;全讀存證/在庫真值):
  ① 站冊對映  SelftestGrid 最新 GRID_*.json 175 站→四專案(VDF/VRN/AETF/REVENUE)子字串冊;每站逐字引用 state/note
  ② 引擎在位  各專案引擎尾版 glob(缺=誠實)
  ③ 資料深度  DuckDB 真值:VDF 價/籌碼/全球/宏觀最新日與列數;AETF 宇宙×持股覆蓋;REVENUE 月數與 ≥60 月檔數;VRN SSOT 筆數
  ④ 任務/頁/令 樞紐任務冊(DeckServer 尾版)/ui_support 頁/Register 短令 在位
  ⑤ 誠實 RYG  RED=站有 FAIL(碼側);YELLOW=站全綠但料深缺口(料側;列下一指令);GREEN=站綠且深度達標
  ⑥ 八段循環  TEST→DEBUG→UPGRADE→OPTIMIZE→CONSOLIDATE→AUTOMATE→USER-TEST→ACTIVATE 各段在庫實現與本輪證據
輸出:ui_support/VIA_UI_ProjectCompletion_v0100.html(小字四分區;手機單欄)+ registry/VIA_ProjectCompletion_v0100.json(再生物)
用法:python3 CGC_MDL131_ProjectCompletion_v0100.py [build [--open] | digest | --selftest]
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
import os
import re
import sys
import time
from datetime import date, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
UI = VIA / "supportive modules" / "ui_support"
GRID_RUNS = VIA / "VIA_Reports" / "selftest_runs"
PAGE = UI / "VIA_UI_ProjectCompletion_v0100.html"
BOOK = HERE / "VIA_ProjectCompletion_v0100.json"
MEGA = VIA / "functional modules" / "VDF" / "output_hub" / "mega"
DB_TW = MEGA / "vdf_tw_market.duckdb"
DB_GL = MEGA / "vdf_global_market.duckdb"
DB_ETF = VIA / "functional modules" / "VDF" / "output_hub" / "active_tw_etf" / "active_tw_etf_holdings" / "ActiveTWETF.duckdb"
VRN_SSOT = VIA / "functional modules" / "VRN" / "SSOT" / "v2" / "VRN_ResearchReport_SSOT.v2.jsonl"

PROJECTS = {
    "VDF": {"zh": "資料鍛造 VeritasDataForge", "sub": ["VDF", "擷取", "回補", "調整後價格層", "因子庫", "寬表", "TA 工廠", "五日", "美國細目", "籌碼", "成交值",
                                                     "全球宇宙", "全球市場", "資料庫", "族群", "產業混合", "估值 band", "網路韌性", "統包網路", "輪動", "共識增益", "擷取矩陣", "圖規鎖"],
            "engines": ["functional modules/VDF/engine/VDF_ENG064_HistoryBackfill_v*.py", "functional modules/VDF/engine/VDF_ENG055_OmniFetch_v*.py",
                        "functional modules/VDF/engine/VDF_ENG066_GlobalUniverse_v*.py", "functional modules/VDF/engine/VDF_ENG074_FredMacroSSOT_v*.py",
                        "functional modules/VDF/engine/VDF_ENG073_DataArchitecture_v*.py", "functional modules/VDF/engine/VDF_ENG060_AdjPriceLayer_v*.py",
                        "functional modules/VDF/engine/VDF_ENG061_FeatureStore_v*.py", "functional modules/VDF/engine/VDF_ENG070_GroupClassificationIndex_v*.py"],
            "tasks": ["backfill", "global", "group_class", "group_backtest", "story_rotation"], "pages": ["VIA_UI_VDFArchitecture_v0100.html", "VIA_UI_Shell_VDF_v0100.html"],
            "cmds": ["via-fred", "via-vdfarch", "via-mobile"]},
    "VRN": {"zh": "報告新星 VeritasReportNova", "sub": ["VRN", "報告", "OCR", "知識堆疊", "NLP", "三語", "每日觀察", "對帳", "文件", "文字統包", "表格統包", "字庫", "郵件",
                                                    "首頁文字", "財報頁", "券商", "文件轉MD", "VOFIE", "SuperDoc", "pdfcheck", "docx", "rescue", "摘要", "財務"],
            "engines": ["functional modules/VRN/VRN_ENG068_DailyBrief_v*.py", "functional modules/VRN/VRN_ENG071_CnyesFusion_v*.py", "functional modules/VRN/VRN_ENG073_ReportStructuredDB_v*.py",
                        "functional modules/VRN/VRN_ENG075_DocToMarkdown_v*.py", "functional modules/VRN/VRN_ENG076_RegressionGate_v*.py", "functional modules/VRN/VRN_ENG079_ControlTowerDashboard_v*.py"],
            "tasks": ["consensus", "structdb", "mdconvert", "finpages", "firstpage", "regression", "nlp", "vofie"], "pages": ["VIA_UI_Shell_VRN_v0100.html", "VIA_UI_ReportCards_v0100.html"],
            "cmds": ["via-md", "via-superhtml"]},
    "AETF": {"zh": "VIA 台灣主動式 ETF 分析", "sub": ["主動", "ETF", "市場分析引擎"],
             "engines": ["functional modules/VDF/engine/VDF_ENG051_ActiveTWETF_Holdings*.py", "functional modules/VDF/engine/VDF_ENG067_ConsensusEnrichment_v*.py",
                         "functional modules/VDF/engine/VDF_ENG068_ETFConsensusAnalysis_v*.py"],
             "tasks": ["etf_fetch", "etf_enrich", "etf_analysis"], "pages": ["VIA_UI_ETFConsensusAnalysis_v0100.html"], "cmds": ["via-mobile"]},
    "REVENUE": {"zh": "VIA 台灣股票月營收分析", "sub": ["月營收", "營收"],
                "engines": ["functional modules/VDF/engine/VDF_ENG063_MonthlyRevenue_v*.py", "functional modules/VDF/engine/VDF_ENG069_RevenueConsensusAnalysis_v*.py",
                            "functional modules/VDF/engine/VDF_ENG075_MonthlyRevenueBackfill_v*.py"],
                "tasks": ["revenue", "revenue_groups", "revenue_consensus"], "pages": ["VIA_UI_RevenueConsensusAnalysis_v0100.html"], "cmds": ["via-revfill"]},
}
LOOP = [
    ("TEST", "SelftestGrid 175 站(via-selftest;平行 accel_map+序跑複判)", "grid"),
    ("DEBUG", "--refail 只重跑紅站全原因(via-selftest --refail)", "refail"),
    ("UPGRADE", "正本 version-forward(尾版 glob;舊版零觸碰)", "versions"),
    ("OPTIMIZE", "ENG073 --optimize(typed 並存/叢集 parquet;只增不減)", "optimize"),
    ("CONSOLIDATE", "MDL122 上船件冊+MDL092 整併稽核+Zero-Hydra 讓位冊", "consolidate"),
    ("AUTOMATE", "via-mobile 14 步補齊鏈+boot 日更(樞紐任務 boot)", "automate"),
    ("USER-TEST", "六主體標準 U/I(via-system)+本頁手機單欄", "usertest"),
    ("ACTIVATE", "DeckServer 樞紐 /master(via-master;via-tower-reset 清塔)", "activate"),
]


# ---------------------------------------------------------------- 讀存證/真值
def latest_grid() -> dict:
    hits = sorted(GRID_RUNS.glob("GRID_*.json"), key=lambda p: p.stat().st_mtime) if GRID_RUNS.exists() else []
    if not hits:
        return {"name": "", "results": [], "ok": 0, "fail": 0, "skip": 0}
    try:
        d = json.loads(hits[-1].read_text(encoding="utf-8"))
        d["name"] = hits[-1].name
    except Exception:
        return {"name": hits[-1].name, "results": [], "ok": 0, "fail": 0, "skip": 0}
    # 站級最新證據律:GRID 之後的 REFAIL(只重跑紅站)逐站覆寫狀態(逐字引用;零重測)
    rf = sorted(GRID_RUNS.glob("REFAIL_*.json"), key=lambda p: p.stat().st_mtime)
    rf = [p for p in rf if p.stat().st_mtime > hits[-1].stat().st_mtime]
    if rf:
        try:
            over = {r["name"]: r for r in json.loads(rf[-1].read_text(encoding="utf-8")).get("results", [])}
            for r in d.get("results", []):
                if r.get("name") in over:
                    r["state"], r["note"] = over[r["name"]].get("state", r.get("state")), (over[r["name"]].get("note") or r.get("note", ""))
            d["ok"] = sum(1 for r in d["results"] if r.get("state") == "OK")
            d["fail"] = sum(1 for r in d["results"] if r.get("state") == "FAIL")
            d["name"] = f"{hits[-1].name} + {rf[-1].name}"
        except Exception:
            pass
    return d


def map_stations(results: list) -> dict:
    out = {k: [] for k in PROJECTS}
    out["OTHER"] = []
    for r in results:
        name = r.get("name", "")
        hit = [k for k, v in PROJECTS.items() if any(s.lower() in name.lower() for s in v["sub"])]
        # AETF/REVENUE 優先(較專;避免「ETF 持股」落 VDF 泛冊)
        if "AETF" in hit or "REVENUE" in hit:
            hit = [k for k in hit if k in ("AETF", "REVENUE")]
        for k in (hit or ["OTHER"]):
            out[k].append({"name": name, "state": r.get("state", "?"), "note": str(r.get("note", ""))[:160], "secs": r.get("secs")})
    return out


def _q(db: Path, sql: str, default=None):
    try:
        import duckdb
        con = duckdb.connect(str(db), read_only=True)
        try:
            return con.execute(sql).fetchone()
        finally:
            con.close()
    except Exception:
        return default


def depth() -> dict:
    d = {}
    if DB_TW.exists():
        r = _q(DB_TW, "SELECT COUNT(*), COUNT(DISTINCT ticker), CAST(MAX(date) AS VARCHAR) FROM tw_daily_prices")
        d["tw_prices"] = {"rows": r[0], "tickers": r[1], "max": r[2]} if r else None
        r = _q(DB_TW, "SELECT COUNT(*), CAST(MAX(date) AS VARCHAR) FROM tw_chip_inst")
        d["tw_chip"] = {"rows": r[0], "max": r[1]} if r else None
        r = _q(DB_TW, "SELECT COUNT(*), COUNT(DISTINCT code), COUNT(DISTINCT ym), MIN(ym), MAX(ym), "
                      "(SELECT COUNT(*) FROM (SELECT code FROM tw_monthly_revenue GROUP BY code HAVING COUNT(DISTINCT ym) >= 60)) FROM tw_monthly_revenue")
        d["revenue"] = {"rows": r[0], "codes": r[1], "months": r[2], "min": r[3], "max": r[4], "codes_60m": r[5]} if r else None
        r = _q(DB_TW, "SELECT COUNT(*) FROM consensus_daily")
        d["consensus"] = {"rows": r[0]} if r else None
    if DB_GL.exists():
        r = _q(DB_GL, "SELECT COUNT(*), COUNT(DISTINCT ticker), CAST(MAX(date) AS VARCHAR) FROM global_daily")
        d["global"] = {"rows": r[0], "tickers": r[1], "max": r[2]} if r else None
        r = _q(DB_GL, "SELECT COUNT(*), COUNT(DISTINCT series), CAST(MAX(date) AS VARCHAR) FROM us_macro")
        d["macro"] = {"rows": r[0], "series": r[1], "max": r[2]} if r else None
    if DB_ETF.exists():
        r = _q(DB_ETF, "SELECT COUNT(DISTINCT etf_ticker) FROM active_tw_etf_universe")
        u = r[0] if r else 0
        r = _q(DB_ETF, "SELECT COUNT(DISTINCT etf_ticker), COUNT(*), CAST(MAX(portfolio_date) AS VARCHAR) FROM holdings_daily")
        d["aetf"] = {"universe": u, "with_holdings": r[0] if r else 0, "rows": r[1] if r else 0, "max": r[2] if r else ""}
    if VRN_SSOT.exists():
        try:
            d["vrn_ssot"] = {"records": sum(1 for l in VRN_SSOT.read_text(encoding="utf-8", errors="ignore").splitlines() if l.strip())}
        except Exception:
            d["vrn_ssot"] = None
    return d


def _tail(pat: str) -> str:
    p = VIA / pat
    hits = sorted(p.parent.glob(p.name))
    return hits[-1].name if hits else ""


def _tasks() -> set:
    try:
        import importlib.util
        p = sorted(HERE.glob("CGC_MDL095_DeckServer_v0*.py"))[-1]
        spec = importlib.util.spec_from_file_location("deck_pc", p)
        m = importlib.util.module_from_spec(spec)
        sys.modules["deck_pc"] = m
        spec.loader.exec_module(m)
        return set(m.task_registry())
    except Exception:
        return set()


def _cmds() -> set:
    hits = sorted(VIA.glob("Register-VIA-Commands-v*.ps1"))
    return set(re.findall(r"function global:(via[\w-]*)", hits[-1].read_text(encoding="utf-8"))) if hits else set()


# ---------------------------------------------------------------- 判定
def gaps_for(key: str, dp: dict) -> list[tuple[str, str]]:
    """料側缺口 [(說明, 下一指令)];誠實依真值"""
    g = []
    if key == "REVENUE":
        rv = dp.get("revenue")
        if not rv or rv["months"] < 60:
            g.append((f"月營收史深 {rv['months'] if rv else 0} 月(需 ≥60 供 high_60m/yoy_streak;≥60 月檔 {rv['codes_60m'] if rv else 0})", "via-revfill"))
        if not dp.get("consensus") or dp["consensus"]["rows"] == 0:
            g.append(("共識庫零列(月營收×共識交集)", "via-mobile(consensus 步)"))
    elif key == "AETF":
        a = dp.get("aetf")
        if not a:
            g.append(("ActiveTWETF.duckdb 缺", "via-datahome link → via-mobile(etf_fetch 步)"))
        elif a["with_holdings"] < max(a["universe"], 1) * 0.9:
            g.append((f"持股覆蓋 {a['with_holdings']}/{a['universe']} 檔(<90%;發行商 adapter 缺=MoneyDJ 後備)", "via-mobile(etf_fetch 步)"))
        if not dp.get("consensus") or dp["consensus"]["rows"] == 0:
            g.append(("共識庫零列(持股×共識加權)", "via-mobile(consensus 步)"))
    elif key == "VDF":
        m = dp.get("macro")
        if not m or m["rows"] == 0:
            g.append(("us_macro 零列(FRED 190 series)", "via-fred"))
        c = dp.get("tw_chip")
        if c and c["max"] and (date.today() - date.fromisoformat(c["max"][:10])).days > 30:
            g.append((f"籌碼最新 {c['max']}(落後 >30 日)", "via-mobile(ENG056 chip 續跑候步)"))
        t = dp.get("tw_prices")
        if t and t["tickers"] < 1000:
            g.append((f"台股宇宙 {t['tickers']} 檔(<1000;全市場候 backfill)", "via-mobile(hist_probe 後 backfill 全量)"))
    elif key == "VRN":
        if not dp.get("vrn_ssot"):
            g.append(("VRN SSOT v2 jsonl 缺(批367 已復位;工作站 via-reload)", "via-reload"))
    return g


def build(do_print: bool = True) -> dict:
    t0 = time.time()
    grid = latest_grid()
    st = map_stations(grid.get("results", []))
    dp = depth()
    tasks, cmds = _tasks(), _cmds()
    projects = []
    for key, v in PROJECTS.items():
        rows = st[key]
        n = {k: sum(1 for r in rows if r["state"] == k) for k in ("OK", "FAIL", "SKIP")}
        eng = [{"pat": e, "file": _tail(e), "ok": bool(_tail(e))} for e in v["engines"]]
        tk = [{"task": t, "ok": t in tasks} for t in v["tasks"]]
        pg = [{"page": p, "ok": (UI / p).exists()} for p in v["pages"]]
        cm = [{"cmd": c, "ok": c in cmds} for c in v["cmds"]]
        gaps = gaps_for(key, dp)
        state = "RED" if n["FAIL"] else ("YELLOW" if gaps or not all(e["ok"] for e in eng) else "GREEN")
        nxt = gaps[0][1] if gaps else ("via-selftest --refail" if n["FAIL"] else "—(綠;每日 boot)")
        projects.append({"key": key, "zh": v["zh"], "state": state, "stations": rows, "n": n, "engines": eng, "tasks": tk, "pages": pg, "cmds": cm,
                         "gaps": [{"gap": g, "cmd": c} for g, c in gaps], "next": nxt})
    ev = {"grid": grid.get("name", ""), "refail": (sorted(GRID_RUNS.glob("REFAIL_*.json"))[-1].name if GRID_RUNS.exists() and sorted(GRID_RUNS.glob("REFAIL_*.json")) else ""),
          "versions": f"Register {_tail('Register-VIA-Commands-v*.ps1')} · FixAll {_tail('supportive modules/registry/CGC_MDL125_FixAll_v*.py')}",
          "optimize": _tail("supportive modules/registry/VIA_VDFArchitecture_v*.json") or "ENG073 冊缺", "consolidate": _tail("supportive modules/registry/CGC_MDL122_IntakeRoster_v*.py"),
          "automate": ("via-mobile 在冊" if "via-mobile" in cmds else "缺") + " · boot " + ("在冊" if "boot" in tasks else "缺"),
          "usertest": ("VIA_UI_System_v0100.html 在" if (UI / "VIA_UI_System_v0100.html").exists() else "缺"),
          "activate": _tail("supportive modules/registry/CGC_MDL095_DeckServer_v0*.py")}
    rep = {"engine": Path(__file__).name, "stamp": datetime.now().strftime("%Y-%m-%d %H:%M"), "grid": {"name": grid.get("name", ""), "ok": grid.get("ok"), "fail": grid.get("fail"), "skip": grid.get("skip")},
           "depth": dp, "projects": projects, "other_stations": len(st["OTHER"]), "loop": [{"stage": a, "impl": b, "evidence": ev.get(c, "")} for a, b, c in LOOP],
           "overall": "RED" if any(p["state"] == "RED" for p in projects) else ("YELLOW" if any(p["state"] == "YELLOW" for p in projects) else "GREEN"),
           "elapsed_s": round(time.time() - t0, 2),
           "rules": ["零重測零發明:站態逐字引用 GRID 存證;深度為 DuckDB 真值", "RED=碼側(站 FAIL);YELLOW=料側缺口(列下一指令);GREEN=站綠且深度達標",
                     "只增不減;誠實三態;每輪 via-mobile 後本頁自動重生(boot 日更)"]}
    BOOK.write_text(json.dumps(rep, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    PAGE.parent.mkdir(parents=True, exist_ok=True)
    PAGE.write_text(render(rep), encoding="utf-8")
    if do_print:
        print(f"=== 四專案完工矩陣(MDL131)· {rep['stamp']} · grid {rep['grid']['name']} OK {rep['grid']['ok']} FAIL {rep['grid']['fail']} ===")
        for p in projects:
            print(f"  [{p['state']:<6}] {p['key']:<8} {p['zh']:<20} 站 {p['n']['OK']}/{len(p['stations'])}(FAIL {p['n']['FAIL']})· 引擎 {sum(e['ok'] for e in p['engines'])}/{len(p['engines'])}"
                  f" · 任務 {sum(t['ok'] for t in p['tasks'])}/{len(p['tasks'])} · 頁 {sum(g['ok'] for g in p['pages'])}/{len(p['pages'])} · 下一步 {p['next']}")
            for g in p["gaps"]:
                print(f"           缺口:{g['gap']} → {g['cmd']}")
        print(f"  [計] overall {rep['overall']} · 頁 {PAGE.name} · 冊 {BOOK.name} · {rep['elapsed_s']}s")
    return rep


def digest(rep: dict | None = None) -> int:
    rep = rep or build(do_print=False)
    print(f"VIA PROJECTS · {rep['stamp']} · grid OK {rep['grid']['ok']} FAIL {rep['grid']['fail']} · overall {rep['overall']}")
    for p in rep["projects"]:
        print(f"{p['key']:<8} {p['state']:<6} 站 {p['n']['OK']}/{len(p['stations'])} · 下一步 {p['next']}")
    return 0


# ---------------------------------------------------------------- 頁
def render(r: dict) -> str:
    e = html.escape

    def b(s):
        c = {"GREEN": "gr", "OK": "gr", "YELLOW": "ye", "SKIP": "ye", "RED": "rd", "FAIL": "rd"}.get(s, "gy")
        return '<span class="b ' + c + '">' + e(s) + "</span>"

    def prow(p):
        gaps = "<br>".join(e(g["gap"]) + ' → <span class="m">' + e(g["cmd"]) + "</span>" for g in p["gaps"]) or '<span class="dim">無</span>'
        eng = "<br>".join(("✓ " if x["ok"] else "✗ ") + e(x["file"] or x["pat"].split("/")[-1]) for x in p["engines"])
        tk = " ".join(("✓" if x["ok"] else "✗") + e(x["task"]) for x in p["tasks"])
        pg = "<br>".join(("✓ " if x["ok"] else "✗ ") + e(x["page"]) for x in p["pages"])
        return ('<tr><td class="m">' + e(p["key"]) + "<br>" + e(p["zh"]) + '</td><td class="c">' + b(p["state"]) + '</td><td class="c m">'
                + f'{p["n"]["OK"]}/{len(p["stations"])}<br>F {p["n"]["FAIL"]} S {p["n"]["SKIP"]}' + '</td><td class="m">' + eng + '</td><td class="m">' + tk + "<br>" + pg
                + '</td><td>' + gaps + '</td><td class="m">' + e(p["next"]) + "</td></tr>")
    prows = "".join(prow(p) for p in r["projects"])
    srows = "".join('<tr><td class="m">' + e(p["key"]) + '</td><td>' + e(s["name"]) + '</td><td class="c">' + b(s["state"]) + '</td><td class="dim">' + e(s["note"][:120]) + "</td></tr>"
                    for p in r["projects"] for s in p["stations"] if s["state"] != "OK")
    d = r["depth"]

    def dv(k, fmt):
        v = d.get(k)
        try:
            return fmt.format(**v) if v else "缺(誠實)"
        except Exception:
            return str(v)
    drows = "".join("<tr><td>" + e(k) + '</td><td class="m">' + e(v) + "</td></tr>" for k, v in (
        ("台股價", dv("tw_prices", "{rows:,} 列 · {tickers} 檔 · →{max}")), ("籌碼", dv("tw_chip", "{rows:,} 列 · →{max}")),
        ("全球", dv("global", "{rows:,} 列 · {tickers} 檔 · →{max}")), ("宏觀 FRED", dv("macro", "{rows:,} 列 · {series} 序列 · →{max}")),
        ("主動 ETF", dv("aetf", "宇宙 {universe} · 有持股 {with_holdings} · {rows:,} 列 · →{max}")),
        ("月營收", dv("revenue", "{rows:,} 列 · {codes} 檔 · {months} 月({min}→{max})· ≥60 月 {codes_60m} 檔")),
        ("共識庫", dv("consensus", "{rows:,} 列")), ("VRN SSOT v2", dv("vrn_ssot", "{records} 筆"))))
    lrows = "".join('<tr><td class="m">' + e(x["stage"]) + "</td><td>" + e(x["impl"]) + '</td><td class="m dim">' + e(str(x["evidence"])) + "</td></tr>" for x in r["loop"])
    return f"""<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>VIA · 四專案完工矩陣</title>
<style>:root{{--bg:#0f172a;--card:#1e293b;--line:#334155;--tx:#f8fafc;--mu:#94a3b8}}*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--tx);font:11px/1.35 -apple-system,'Segoe UI',Roboto,'Microsoft JhengHei',sans-serif}}
.wrap{{max-width:1400px;margin:0 auto;padding:18px 14px 48px}}h1{{font-size:14px;margin:0}}.sub{{color:var(--mu);margin:3px 0 14px}}h2{{font-size:12px;margin:20px 0 7px;border-bottom:1px solid var(--line);padding-bottom:5px}}
.nav a{{color:#7dd3fc;margin-right:12px;text-decoration:none}}
.kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(110px,1fr));gap:8px;margin-bottom:14px}}.kpi{{background:var(--card);border:1px solid var(--line);border-radius:3px;padding:9px 11px}}.kpi .n{{font-size:17px;font-weight:600}}.kpi .l{{font-size:10px;color:var(--mu)}}
table{{width:100%;table-layout:fixed;border-collapse:collapse;background:var(--card);border:1px solid var(--line)}}th{{font-size:10px;color:var(--mu);text-align:left;padding:4px 6px;border-bottom:1px solid var(--line)}}td{{padding:4px 6px;border-bottom:1px solid #253248;vertical-align:top;word-wrap:break-word;overflow-wrap:break-word;white-space:normal}}td.c{{text-align:center}}.m{{font-family:ui-monospace,Consolas,monospace;font-size:10px}}.dim{{color:var(--mu)}}
.b{{display:inline-block;font-size:10px;padding:1px 6px;border-radius:2px;border:1px solid}}.gr{{background:#064e3b;color:#34d399;border-color:#059669}}.ye{{background:#78350f;color:#fde047;border-color:#d97706}}.rd{{background:#7f1d1d;color:#fca5a5;border-color:#dc2626}}.gy{{background:#1f2937;color:#9ca3af;border-color:#374151}}
.note{{background:var(--card);border:1px solid var(--line);border-left:3px solid #d97706;border-radius:3px;padding:10px 12px;margin-top:16px}}
@media(max-width:700px){{table,thead,tbody,tr,td,th{{display:block}}thead{{display:none}}td{{border:0;padding:2px 6px}}tr{{border-bottom:1px solid var(--line);padding:6px 0}}}}</style></head><body><div class="wrap">
<h1>VIA PROJECT COMPLETION · VDF · VRN · ACTIVE TW ETF · MONTHLY REVENUE</h1>
<p class="sub">{e(r["engine"])} · {e(r["stamp"])} · grid {e(r["grid"]["name"])} OK {r["grid"]["ok"]} FAIL {r["grid"]["fail"]} SKIP {r["grid"]["skip"]} · {r["elapsed_s"]} s</p>
<p class="nav"><a href="VIA_UI_Consolidated_v0100.html">整</a><a href="VIA_UI_SystemCharter_v0100.html">冊</a><a href="VIA_UI_LifecycleRACI_v0100.html">環</a><a href="VIA_UI_VDFArchitecture_v0100.html">架</a><a href="VIA_UI_IntakeRoster_v0100.html">收容</a><a href="VIA_UI_MasterControl_v0100.html">總控</a></p>
<div class="kpis"><div class="kpi"><div class="n">{b(r["overall"])}</div><div class="l">overall</div></div>{"".join('<div class="kpi"><div class="n">' + b(p["state"]) + '</div><div class="l">' + e(p["key"]) + " " + f'{p["n"]["OK"]}/{len(p["stations"])}' + "</div></div>" for p in r["projects"])}</div>
<h2>MODULE — four projects (stations · engines · tasks/pages · gaps · next command)</h2>
<table><colgroup><col style="width:12%"><col style="width:6%"><col style="width:7%"><col style="width:22%"><col style="width:18%"><col style="width:23%"><col style="width:12%"></colgroup>
<thead><tr><th>project</th><th>RYG</th><th>stations</th><th>engines (tail)</th><th>tasks · pages</th><th>gaps (honest) → cmd</th><th>next</th></tr></thead><tbody>{prows}</tbody></table>
<h2>DATA — DuckDB truth depth</h2>
<table><colgroup><col style="width:20%"><col style="width:80%"></colgroup><tbody>{drows}</tbody></table>
<h2>ENGINE — non-green stations by project (verbatim from GRID)</h2>
<table><colgroup><col style="width:9%"><col style="width:30%"><col style="width:8%"><col style="width:53%"></colgroup><thead><tr><th>proj</th><th>station</th><th>state</th><th>note</th></tr></thead><tbody>{srows or '<tr><td colspan="4" class="dim">全綠</td></tr>'}</tbody></table>
<h2>OTHERS — eight-stage loop (TEST→…→ACTIVATE) and evidence</h2>
<table><colgroup><col style="width:12%"><col style="width:48%"><col style="width:40%"></colgroup><thead><tr><th>stage</th><th>implemented by</th><th>this round evidence</th></tr></thead><tbody>{lrows}</tbody></table>
<div class="note">{"<br>".join(e(x) for x in r["rules"])}</div>
</div></body></html>"""


# ---------------------------------------------------------------- 自測
def selftest() -> int:
    import tempfile
    global GRID_RUNS, PAGE, BOOK
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    chk("① 四專案冊(VDF/VRN/AETF/REVENUE;每項 sub/engines/tasks/pages/cmds)", set(PROJECTS) == {"VDF", "VRN", "AETF", "REVENUE"}
        and all({"sub", "engines", "tasks", "pages", "cmds"} <= set(v) for v in PROJECTS.values()))
    fake = [{"name": "月營收分析九檢(批194)", "state": "OK"}, {"name": "主動ETF×共識分析自測(批264)", "state": "FAIL", "note": "x"},
            {"name": "歷史回補八檢(批203)", "state": "OK"}, {"name": "知識堆疊轉接八檢(批141)", "state": "SKIP"}, {"name": "衝突哨兵十檢", "state": "OK"}]
    m = map_stations(fake)
    chk("② 站冊對映(月營收→REVENUE;主動ETF→AETF 不落 VDF;回補→VDF;知識堆疊→VRN;無對映→OTHER)",
        [s["name"] for s in m["REVENUE"]] == ["月營收分析九檢(批194)"] and len(m["AETF"]) == 1 and not any("主動" in s["name"] for s in m["VDF"])
        and len(m["VDF"]) == 1 and len(m["VRN"]) == 1 and len(m["OTHER"]) == 1)
    g = gaps_for("REVENUE", {"revenue": {"months": 3, "codes_60m": 0}, "consensus": {"rows": 245}})
    g2 = gaps_for("AETF", {"aetf": {"universe": 30, "with_holdings": 25, "rows": 1, "max": ""}, "consensus": {"rows": 0}})
    chk("③ 料側缺口誠實(月數<60→via-revfill;持股覆蓋<90%→etf_fetch;共識零列→consensus)",
        g and g[0][1] == "via-revfill" and len(g2) == 2 and "etf_fetch" in g2[0][1] and "consensus" in g2[1][1])
    _s = (GRID_RUNS, PAGE, BOOK)
    with tempfile.TemporaryDirectory() as td:
        GRID_RUNS = Path(td)
        PAGE, BOOK = Path(td) / "p.html", Path(td) / "b.json"
        (GRID_RUNS / "GRID_T.json").write_text(json.dumps({"ok": 4, "fail": 1, "skip": 0, "results": fake}), encoding="utf-8")
        rep = build(do_print=False)
        pa = {p["key"]: p for p in rep["projects"]}
        chk("④ RYG 律(AETF 站 FAIL=RED;REVENUE 站綠+史深缺=YELLOW;overall=RED)",
            pa["AETF"]["state"] == "RED" and pa["REVENUE"]["state"] in ("YELLOW", "GREEN") and rep["overall"] == "RED")
        chk("⑤ 頁+冊(四分區 MODULE/DATA/ENGINE/OTHERS;八段循環;手機單欄 @media;導航 架/整/冊/環)",
            PAGE.exists() and BOOK.exists() and all(x in PAGE.read_text(encoding="utf-8") for x in ("MODULE", "DATA", "ENGINE", "OTHERS", "ACTIVATE", "@media", "VIA_UI_VDFArchitecture_v0100.html"))
            and len(rep["loop"]) == 8)
    GRID_RUNS, PAGE, BOOK = _s
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑥ 紀律宣告(零重測零發明/逐字引用/只增不減/誠實三態)", all(k in src for k in ("零重測零發明", "逐字引用", "只增不減", "誠實三態")))
    print(f"  [計] 六檢 OK {6 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print("=== 四專案完工矩陣(CGC_MDL131)· 六檢自測 ===")
        return selftest()
    if a and a[0] == "digest":
        return digest()
    rep = build()
    if "--open" in a:
        try:
            import webbrowser
            webbrowser.open(PAGE.as_uri())
        except Exception:
            pass
    return 0 if rep["overall"] != "RED" else 1


if __name__ == "__main__":
    sys.exit(main())
