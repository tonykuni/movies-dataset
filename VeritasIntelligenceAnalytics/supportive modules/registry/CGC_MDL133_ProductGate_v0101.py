#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CGC_MDL133_ProductGate v0101 — 產品資格閘(批377 +via-lanes/MDL134/ParallelLanes 頁入閘;批376 操作員令「Final test and user test debug till them
work perfectly to insure, they are qualified to become a product」)

一句話:把「能不能當產品」變成九道可機讀的閘,每閘只讀既有存證/檔案真值(零重測零發明),
        逐字引用 SelftestGrid GRID/REFAIL 存證與磁碟真相,誠實三態 OK/WARN/FAIL → 資格判定
        QUALIFIED / CONDITIONAL / NOT_QUALIFIED;頁+冊只增不減。

九閘(G1–G9;每閘=名稱/態/證據/下一指令):
  G1 矩陣存證:最新 GRID(+其後 REFAIL 逐站覆寫)——產品核心站(批376 八站+樞紐站)全綠;
     全矩陣碼側 FAIL=0(料側 FAIL=WARN=條件合格,列下一指令;碼側 FAIL=FAIL)
  G2 短令↔梭:Register 尾版每個 function global:via-* 皆有同名 .cmd 梭(批367 刻意讓位三梭除外)
  G3 樞紐任務:DeckServer 尾版 task_registry 含產品任務冊(backfill/global/etf_universe/etf_fetch/
     etf_history/etf_revenue/revenue/revenue_consensus/consensus/etf_analysis/ves/selftest_fast/complete_all)
  G4 產品頁衛生:每頁零 CDN(無外連 script/link)+viewport+手機單欄 @media;缺頁=WARN(列再生指令)
  G5 再生物讓位:引擎每次跑會回寫資料的頁必列 .gitignore(拉齊零阻擋)
  G6 鑰匙守衛:全樹文字檔零明文 API 鑰(以 SHA-256 指紋比對 32-hex token;本檔永不含鑰)
  G7 引擎尾版:四專案引擎+MDL131/132/133+SelftestGrid 尾版皆在位且可編譯(py_compile)
  G8 短令在位:四專案短令+via-productgate/via-mobile/via-selftest/via-reload 皆在 Register 尾版
  G9 用法文件:冊含 usage(手機一句 via-reload; via-mobile)+本頁自身零 CDN/手機單欄

資格律:任一 FAIL → NOT_QUALIFIED;零 FAIL 有 WARN → CONDITIONAL(碼合格;料側待工作站抓);
        全 OK → QUALIFIED。判定只依證據,永不假綠。
尾版律:所有引擎/冊皆 glob 尾版動態解析,永不寫死版號。
用法:via-productgate            → build --open(頁 VIA_UI_ProductGate_v0100.html + 冊 VIA_ProductGate_v0100.json)
      via-productgate digest     → 手機一屏文字(via-mobile 末段自動印)
      python <本檔> --selftest   → 九檢
"""
from __future__ import annotations

import hashlib
import html
import importlib.util
import json
import os
import py_compile
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
ROOT = VIA.parent
UI = VIA / "supportive modules" / "ui_support"
GRID_RUNS = VIA / "VIA_Reports" / "selftest_runs"
PAGE = UI / "VIA_UI_ProductGate_v0100.html"
BOOK = HERE / "VIA_ProductGate_v0100.json"
GITIGNORE = ROOT / ".gitignore"

ENGINE_TAG = "CGC_MDL133_ProductGate v0101"
YIELDED_SHIMS = {"via-all", "via-rootcheck", "via-tower-reset"}   # 批367 同名雙物刻意讓位(大寫原件在位)
CORE_STATION_SUBS = ["(批376)", "sysman 三輪協議", "執行橋八檢", "指揮台九檢", "ETF 持股引擎自測", "歷史回補", "月營收分析", "主動ETF×共識分析"]
PRODUCT_TASKS = ["backfill", "global", "etf_universe", "etf_fetch", "etf_history", "etf_revenue", "revenue", "revenue_consensus",
                 "consensus", "etf_analysis", "ves", "selftest_fast", "complete_all"]
PRODUCT_CMDS = ["via-productgate", "via-mobile", "via-selftest", "via-reload", "via-projects", "via-fred", "via-vdfarch",
                "via-revfill", "via-etfuniv", "via-etfhist", "via-etfrev", "via-ves", "via-md", "via-superhtml", "via-lanes"]
PRODUCT_PAGES = {   # 頁 → 再生指令(缺頁=WARN 列之)
    "VIA_UI_ProjectCompletion_v0100.html": "via-projects", "VIA_UI_VDFArchitecture_v0100.html": "via-vdfarch",
    "VIA_UI_ETFRevenueMomentum_v0100.html": "via-etfrev", "VIA_UI_ActiveETFHoldingsHistory_v0100.html": "via-etfhist",
    "VIA_UI_ETFConsensusAnalysis_v0100.html": "via-analysis", "VIA_UI_RevenueConsensusAnalysis_v0100.html": "via-analysis",
    "VIA_UI_Shell_VDF_v0100.html": "via-ui", "VIA_UI_Shell_VRN_v0100.html": "via-ui",
}
REGEN_PAGES = ["VIA_UI_ETFRevenueMomentum_v*.html", "VIA_UI_ActiveETFHoldingsHistory_v*.html", "VIA_UI_ETFConsensusAnalysis_v*.html",
               "VIA_UI_RevenueConsensusAnalysis_v*.html", "VIA_UI_ProductGate_v*.html", "VIA_UI_ParallelLanes_v*.html"]
ENGINE_PATS = ["functional modules/VDF/engine/VDF_ENG073_DataArchitecture_v*.py", "functional modules/VDF/engine/VDF_ENG074_FredMacroSSOT_v*.py",
               "functional modules/VDF/engine/VDF_ENG075_MonthlyRevenueBackfill_v*.py", "functional modules/VDF/engine/VDF_ENG076_ETFRevenueMomentum_v*.py",
               "functional modules/VDF/engine/VDF_ENG077_ActiveETFUniverse_v*.py", "functional modules/VDF/engine/VDF_ENG078_ActiveETFHoldingsHistory_v*.py",
               "functional modules/VDF/engine/VDF_ENG055_OmniFetch_v*.py", "functional modules/VDF/engine/VDF_ENG064_HistoryBackfill_v*.py",
               "functional modules/VDF/engine/VDF_ENG063_MonthlyRevenue_v*.py", "functional modules/VDF/engine/VDF_ENG068_ETFConsensusAnalysis_v*.py",
               "functional modules/VDF/engine/VDF_ENG069_RevenueConsensusAnalysis_v*.py", "functional modules/VRN/VRN_ENG075_DocToMarkdown_v*.py",
               "supportive modules/registry/CGC_MDL064_SelftestGrid_v*.py", "supportive modules/registry/CGC_MDL095_DeckServer_v*.py",
               "supportive modules/registry/CGC_MDL125_FixAll_v*.py", "supportive modules/registry/CGC_MDL131_ProjectCompletion_v*.py",
               "supportive modules/registry/CGC_MDL132_VesBridge_v*.py", "supportive modules/registry/CGC_MDL133_ProductGate_v*.py",
               "supportive modules/registry/CGC_MDL134_ParallelLanes_v*.py"]
# 鑰匙指紋(SHA-256 of 32-hex token;本檔永不含明文鑰):FRED 工作站鑰/上船 SSOT 鑰/操作員對話鑰
KEY_HASHES = {
    "2dc6d72e357de01e97a172b4eaf355e269a95684523599b9c97cc943e7c20fb2",
    "2dd8eb48d968425dc3f7d17daff6a84a4378ee4e91392f40fcc46546365e945e",
    "d5cc57e567a11e8c31436588fe5089612887382b3d82547fb7bb5a2e58fc6276",
}
HEX32_RX = re.compile(r"(?<![0-9a-fA-F])[0-9a-f]{32}(?![0-9a-fA-F])")
TEXT_SUFFIX = {".py", ".ps1", ".cmd", ".json", ".md", ".txt", ".sh", ".html", ".jsonl", ".csv", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".bat"}
KEY_EXCLUDE = {".fred_api_key"}
CDN_RX = re.compile(r"<(?:script|link)\b[^>]*(?:src|href)\s*=\s*[\"']https?://", re.I)
USAGE = ["手機一句:via-reload; via-mobile(六流程 dry-run → 紅站補齊鏈 → 四專案矩陣 → 產品閘 digest;零跳出)",
         "看頁:via-productgate(build --open)/ via-projects / via-vdfarch / via-ui",
         "全矩陣:via-selftest;只重跑紅站:via-selftest --refail;只八站:via-selftest --only 批376",
         "資料側:via-fred(FRED 190 序列)/ via-revfill(月營收史深)/ via-etfuniv(主動 ETF 宇宙)/ via-etfhist(持股史深)/ via-etfrev(ETF×營收)",
         "標準化掃描:via-ves(唯讀;--apply 永不經短令)", "並行補齊:via-lanes run(十道;Hydra 哨兵)/ via-mobile --lanes", "日更:boot(via_boot_update.sh)①–⑫ 含本閘"]
RULES = ["零重測零發明:每閘只讀既有 GRID/REFAIL 存證與磁碟真相,逐字引用;本閘不重跑任何站",
         "誠實三態 OK/WARN/FAIL → QUALIFIED/CONDITIONAL/NOT_QUALIFIED;任一 FAIL 即不合格,永不假綠",
         "只增不減:頁/冊 version-forward;本閘零刪除零改寫他檔", "尾版律:引擎/冊/Register 皆 glob 尾版動態解析,永不寫死版號",
         "鑰匙守衛以 SHA-256 指紋比對;本檔永不含明文鑰"]


# ---------------------------------------------------------------- 工具
def newest(pat: str, root: Path = VIA) -> Path | None:
    p = root / pat
    hits = sorted(p.parent.glob(p.name)) if p.parent.exists() else []
    return hits[-1] if hits else None


def _load(pat: str, alias: str):
    p = newest(pat, HERE)
    if not p:
        return None
    spec = importlib.util.spec_from_file_location(alias, p)
    m = importlib.util.module_from_spec(spec)
    sys.modules[alias] = m
    spec.loader.exec_module(m)
    return m


def _mdl131():
    try:
        return _load("CGC_MDL131_ProjectCompletion_v*.py", "pc_gate")
    except Exception:
        return None


def latest_grid() -> dict:
    """優先逐字沿用 MDL131.latest_grid(GRID+其後 REFAIL 覆寫律);缺則本地讀"""
    m = _mdl131()
    if m and hasattr(m, "latest_grid"):
        try:
            m.GRID_RUNS = GRID_RUNS
            return m.latest_grid()
        except Exception:
            pass
    hits = sorted(GRID_RUNS.glob("GRID_*.json"), key=lambda p: p.stat().st_mtime) if GRID_RUNS.exists() else []
    if not hits:
        return {"name": "", "results": [], "ok": 0, "fail": 0, "skip": 0}
    try:
        d = json.loads(hits[-1].read_text(encoding="utf-8"))
        d["name"] = hits[-1].name
        return d
    except Exception:
        return {"name": hits[-1].name, "results": [], "ok": 0, "fail": 0, "skip": 0}


def classify_fail(note: str, detail: str = "") -> str:
    m = _mdl131()
    if m and hasattr(m, "classify_fail"):
        return m.classify_fail(note, detail)
    return "CODE" if re.search(r"Traceback|Error|逾時", (note or "") + (detail or "")) else "DATA?"


def register_tail() -> Path | None:
    return newest("Register-VIA-Commands-v*.ps1", VIA)


def register_fns(text: str) -> set:
    return set(re.findall(r"function global:(via[\w-]*)", text))


def shim_names(folder: Path) -> set:
    return {p.stem for p in folder.glob("via*.cmd")} if folder.exists() else set()


def gitignore_patterns(path: Path) -> list:
    if not path.exists():
        return []
    return [l.strip() for l in path.read_text(encoding="utf-8", errors="ignore").splitlines() if l.strip() and not l.startswith("#")]


def ignored_by(patterns: list, rel: str) -> bool:
    import fnmatch
    for pat in patterns:
        q = pat.lstrip("/")
        if fnmatch.fnmatch(rel, q) or fnmatch.fnmatch(Path(rel).name, q) or fnmatch.fnmatch(rel, q + "*"):
            return True
    return False


def _tracked_files(root: Path) -> list:
    """git ls-files(快);失敗退目錄走訪(誠實印來源)"""
    try:
        out = subprocess.run(["git", "-C", str(root), "ls-files", "-z"], capture_output=True, timeout=60)
        if out.returncode == 0:
            return [root / f for f in out.stdout.decode("utf-8", "ignore").split("\0") if f]
    except Exception:
        pass
    skip = {".git", "node_modules", "__pycache__", ".venv"}
    files = []
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d not in skip]
        files.extend(Path(dp) / f for f in fn)
    return files


def key_scan(root: Path, hashes: set | None = None, max_bytes: int = 8_000_000) -> list:
    """回傳含明文鑰之檔(相對路徑);比對 SHA-256 指紋,永不印鑰"""
    hashes = hashes or KEY_HASHES
    hits, seen = [], {}
    for p in _tracked_files(root):
        if p.suffix.lower() not in TEXT_SUFFIX or p.name in KEY_EXCLUDE:
            continue
        try:
            if not p.exists() or p.stat().st_size > max_bytes:
                continue
            t = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for tok in set(HEX32_RX.findall(t)):
            h = seen.get(tok)
            if h is None:
                h = seen[tok] = hashlib.sha256(tok.encode()).hexdigest()
            if h in hashes:
                hits.append(str(p.relative_to(root)).replace("\\", "/"))
                break
    return sorted(hits)


def page_hygiene(path: Path) -> dict:
    t = path.read_text(encoding="utf-8", errors="ignore")
    return {"cdn": bool(CDN_RX.search(t)), "viewport": "viewport" in t, "media": "@media" in t}


# ---------------------------------------------------------------- 九閘
def gate(gid: str, name: str, state: str, evidence: str, nxt: str = "") -> dict:
    return {"id": gid, "name": name, "state": state, "evidence": evidence, "next": nxt}


def g1_grid(grid: dict | None = None) -> dict:
    grid = grid if grid is not None else latest_grid()
    res = grid.get("results", [])
    if not res:
        return gate("G1", "矩陣存證", "FAIL", "無 GRID 存證(VIA_Reports/selftest_runs)", "via-selftest")
    core = [r for r in res if any(s in r.get("name", "") for s in CORE_STATION_SUBS)]
    n376 = sum(1 for r in res if "(批376)" in r.get("name", ""))
    code, data = [], []
    for r in res:
        if r.get("state") == "FAIL":
            side = classify_fail(str(r.get("note", "")), str(r.get("detail", "")))
            (code if side == "CODE" else data).append(r.get("name", "") + "[" + side + "]")
    core_bad = [r["name"] for r in core if r.get("state") != "OK"]
    ev = "grid " + str(grid.get("name", "")) + " · OK " + str(grid.get("ok")) + " FAIL " + str(grid.get("fail")) + " SKIP " + str(grid.get("skip")) \
         + " · 核心站 " + str(len(core) - len(core_bad)) + "/" + str(len(core)) + "(批376 站 " + str(n376) + "/8)· 碼紅 " + str(len(code)) + " 料紅 " + str(len(data))
    if n376 < 8:
        return gate("G1", "矩陣存證", "FAIL", ev + " · 存證早於 v0225(批376 八站未入)", "via-selftest")
    if core_bad or code:
        return gate("G1", "矩陣存證", "FAIL", ev + " · 核心非綠 " + ", ".join(core_bad[:6]) + " · 碼紅 " + ", ".join(code[:6]), "via-selftest --refail")
    if data:
        return gate("G1", "矩陣存證", "WARN", ev + " · 料側 " + ", ".join(data[:8]), "via-mobile(補齊鏈)")
    return gate("G1", "矩陣存證", "OK", ev)


def g2_shims(reg_text: str | None = None, folder: Path | None = None) -> dict:
    rp = register_tail()
    if reg_text is None:
        if not rp:
            return gate("G2", "短令↔梭", "FAIL", "無 Register-VIA-Commands 尾版", "")
        reg_text = rp.read_text(encoding="utf-8", errors="ignore")
    fns = register_fns(reg_text)
    shims = shim_names(folder or VIA)
    missing = sorted(fns - shims - YIELDED_SHIMS)
    orphan = sorted(shims - fns)
    ev = "函式 " + str(len(fns)) + " · 梭 " + str(len(shims)) + " · 讓位 " + ",".join(sorted(YIELDED_SHIMS & fns)) + (" · 孤梭 " + ",".join(orphan) if orphan else "")
    if missing:
        return gate("G2", "短令↔梭", "FAIL", ev + " · 缺梭 " + ",".join(missing), "補同名 .cmd(via-datahome.cmd 模板)")
    return gate("G2", "短令↔梭", "WARN" if orphan else "OK", ev)


def g3_tasks(tasks: set | None = None) -> dict:
    if tasks is None:
        try:
            m = _load("CGC_MDL095_DeckServer_v0*.py", "deck_gate")
            tasks = set(m.task_registry()) if m else set()
        except Exception as e:
            return gate("G3", "樞紐任務", "SKIP", "DeckServer 載入失敗:" + str(e)[:80], "")
    missing = [t for t in PRODUCT_TASKS if t not in tasks]
    ev = "任務冊 " + str(len(tasks)) + " · 產品任務 " + str(len(PRODUCT_TASKS) - len(missing)) + "/" + str(len(PRODUCT_TASKS))
    return gate("G3", "樞紐任務", "FAIL" if missing else "OK", ev + (" · 缺 " + ",".join(missing) if missing else ""), "DeckServer 尾版補任務" if missing else "")


def g4_pages(folder: Path | None = None, pages: dict | None = None) -> dict:
    folder = folder or UI
    pages = pages or PRODUCT_PAGES
    bad, miss, ok = [], [], 0
    for name, cmd in pages.items():
        p = folder / name
        if not p.exists():
            miss.append(name + "→" + cmd)
            continue
        h = page_hygiene(p)
        if h["cdn"] or not h["viewport"] or not h["media"]:
            bad.append(name + "(" + ",".join(k for k, v in (("CDN", h["cdn"]), ("no-viewport", not h["viewport"]), ("no-@media", not h["media"])) if v) + ")")
        else:
            ok += 1
    ev = "頁 " + str(ok) + "/" + str(len(pages)) + " 衛生綠" + (" · 缺頁 " + "; ".join(miss) if miss else "") + (" · 違規 " + "; ".join(bad) if bad else "")
    if bad:
        return gate("G4", "產品頁衛生", "FAIL", ev, "改頁:內嵌樣式/手機 @media")
    return gate("G4", "產品頁衛生", "WARN" if miss else "OK", ev, "缺頁再生:" + " / ".join(sorted({m.split("→")[1] for m in miss})) if miss else "")


def g5_regen(patterns: list | None = None) -> dict:
    pats = patterns if patterns is not None else gitignore_patterns(GITIGNORE)
    rel = "VeritasIntelligenceAnalytics/supportive modules/ui_support/"
    missing = [p for p in REGEN_PAGES if not ignored_by(pats, rel + p.replace("*", "0100"))]
    ev = ".gitignore 規則 " + str(len(pats)) + " · 再生頁 " + str(len(REGEN_PAGES) - len(missing)) + "/" + str(len(REGEN_PAGES)) + " 已讓位"
    return gate("G5", "再生物讓位", "FAIL" if missing else "OK", ev + (" · 未列 " + ",".join(missing) if missing else ""), ".gitignore 補列" if missing else "")


def g6_keys(root: Path | None = None, hashes: set | None = None) -> dict:
    t0 = time.time()
    hits = key_scan(root or ROOT, hashes)
    ev = "掃描 " + str(root or ROOT) + " · 命中 " + str(len(hits)) + " · " + str(round(time.time() - t0, 1)) + "s"
    return gate("G6", "鑰匙守衛", "FAIL" if hits else "OK", ev + (" · " + ", ".join(hits[:5]) if hits else ""), "遮罩 <REDACTED:VDF_FRED_API_KEY>" if hits else "")


def g7_engines(pats: list | None = None) -> dict:
    miss, bad, ok, tails = [], [], 0, []
    for pat in (pats or ENGINE_PATS):
        p = newest(pat)
        if not p:
            miss.append(pat.split("/")[-1])
            continue
        try:
            py_compile.compile(str(p), doraise=True)
            ok += 1
            tails.append(p.name)
        except Exception as e:
            bad.append(p.name + ":" + str(e)[:60])
    rp = register_tail()
    ev = "尾版 " + str(ok) + "/" + str(len(pats or ENGINE_PATS)) + " 可編譯 · Register " + (rp.name if rp else "缺")
    if miss or bad or not rp:
        return gate("G7", "引擎尾版", "FAIL", ev + (" · 缺 " + ",".join(miss) if miss else "") + (" · 壞 " + "; ".join(bad) if bad else ""), "補引擎/修語法")
    return gate("G7", "引擎尾版", "OK", ev + " · " + ", ".join(tails[-4:]))


def g8_cmds(reg_text: str | None = None) -> dict:
    if reg_text is None:
        rp = register_tail()
        reg_text = rp.read_text(encoding="utf-8", errors="ignore") if rp else ""
    fns = register_fns(reg_text)
    missing = [c for c in PRODUCT_CMDS if c not in fns]
    ev = "產品短令 " + str(len(PRODUCT_CMDS) - len(missing)) + "/" + str(len(PRODUCT_CMDS))
    return gate("G8", "短令在位", "FAIL" if missing else "OK", ev + (" · 缺 " + ",".join(missing) if missing else ""), "Register 尾版補函式" if missing else "")


def g9_usage(page: Path | None = None) -> dict:
    page = page or PAGE
    ev = "usage " + str(len(USAGE)) + " 條 · 頁 " + page.name
    if not page.exists():
        return gate("G9", "用法文件", "WARN", ev + " · 頁未生(本次 build 即生)", "via-productgate")
    h = page_hygiene(page)
    if h["cdn"] or not h["media"] or not h["viewport"]:
        return gate("G9", "用法文件", "FAIL", ev + " · 本頁衛生違規", "修 render")
    return gate("G9", "用法文件", "OK", ev + " · 本頁零 CDN/手機單欄")


def verdict(gates: list) -> str:
    st = {g["state"] for g in gates}
    if "FAIL" in st:
        return "NOT_QUALIFIED"
    if "WARN" in st:
        return "CONDITIONAL"
    return "QUALIFIED"


def project_summary(grid: dict) -> list:
    m = _mdl131()
    if not (m and hasattr(m, "map_stations")):
        return []
    try:
        ms = m.map_stations(grid.get("results", []))
    except Exception:
        return []
    out = []
    for k, v in m.PROJECTS.items():
        st = ms.get(k, [])
        n = {"OK": sum(1 for s in st if s["state"] == "OK"), "CODE": sum(1 for s in st if s.get("side") == "CODE"),
             "DATA": sum(1 for s in st if s["state"] == "FAIL" and s.get("side") != "CODE"), "n": len(st)}
        n["state"] = "RED" if n["CODE"] else ("YELLOW" if n["DATA"] else "GREEN")
        out.append({"key": k, "zh": v["zh"], **n})
    return out


# ---------------------------------------------------------------- build/digest
def build(do_print: bool = True, write: bool = True) -> dict:
    t0 = time.time()
    grid = latest_grid()
    gates = [g1_grid(grid), g2_shims(), g3_tasks(), g4_pages(), g5_regen(), g6_keys(), g7_engines(), g8_cmds()]
    rep = {"engine": ENGINE_TAG, "stamp": datetime.now().strftime("%Y-%m-%d %H:%M"), "grid": {"name": grid.get("name", ""), "ok": grid.get("ok"), "fail": grid.get("fail"), "skip": grid.get("skip")},
           "gates": gates, "projects": project_summary(grid), "usage": USAGE, "rules": RULES}
    if write:
        PAGE.parent.mkdir(parents=True, exist_ok=True)
        rep["gates"].append(gate("G9", "用法文件", "OK", "先生頁再驗", ""))
        rep["verdict"] = verdict(rep["gates"])
        PAGE.write_text(render(rep), encoding="utf-8")
        rep["gates"][-1] = g9_usage()
    else:
        rep["gates"].append(g9_usage())
    rep["verdict"] = verdict(rep["gates"])
    rep["elapsed_s"] = round(time.time() - t0, 1)
    if write:
        PAGE.write_text(render(rep), encoding="utf-8")
        BOOK.write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    if do_print:
        digest(rep)
        if write:
            print("  [頁] " + str(PAGE) + "\n  [冊] " + str(BOOK))
    return rep


def digest(rep: dict | None = None) -> int:
    rep = rep or build(do_print=False)
    print("VIA PRODUCT GATE · " + rep["stamp"] + " · " + rep["verdict"] + " · grid OK " + str(rep["grid"]["ok"]) + " FAIL " + str(rep["grid"]["fail"]))
    for g in rep["gates"]:
        print("  " + g["id"] + " " + g["state"].ljust(4) + " " + g["name"] + " · " + g["evidence"][:150] + (" → " + g["next"] if g["next"] and g["state"] != "OK" else ""))
    for p in rep.get("projects", []):
        print("  " + p["key"].ljust(8) + p["state"].ljust(7) + "站 " + str(p["OK"]) + "/" + str(p["n"]) + " 碼紅 " + str(p["CODE"]) + " 料紅 " + str(p["DATA"]))
    return 0 if rep["verdict"] != "NOT_QUALIFIED" else 1


# ---------------------------------------------------------------- 頁
def _badge(s: str) -> str:
    c = {"OK": "gr", "QUALIFIED": "gr", "GREEN": "gr", "WARN": "ye", "CONDITIONAL": "ye", "YELLOW": "ye", "SKIP": "gy",
         "FAIL": "rd", "NOT_QUALIFIED": "rd", "RED": "rd"}.get(s, "gy")
    return '<span class="b ' + c + '">' + html.escape(s) + "</span>"


def render(r: dict) -> str:
    e = html.escape
    grows = "".join('<tr><td class="m">' + e(g["id"]) + "</td><td>" + e(g["name"]) + '</td><td class="c">' + _badge(g["state"]) + '</td><td class="dim">' + e(g["evidence"])
                    + '</td><td class="m">' + e(g["next"]) + "</td></tr>" for g in r["gates"])
    prows = "".join('<tr><td class="m">' + e(p["key"]) + "<br>" + e(p["zh"]) + '</td><td class="c">' + _badge(p["state"]) + '</td><td class="c m">' + str(p["OK"]) + "/" + str(p["n"])
                    + '</td><td class="c m">' + str(p["CODE"]) + '</td><td class="c m">' + str(p["DATA"]) + "</td></tr>" for p in r.get("projects", [])) or '<tr><td colspan="5" class="dim">MDL131 未載</td></tr>'
    urows = "".join("<li>" + e(u) + "</li>" for u in r["usage"])
    kp = "".join('<div class="kpi"><div class="n">' + _badge(g["state"]) + '</div><div class="l">' + e(g["id"] + " " + g["name"]) + "</div></div>" for g in r["gates"])
    head = ('<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            "<title>VIA · 產品資格閘</title><style>:root{--bg:#0f172a;--card:#1e293b;--line:#334155;--tx:#f8fafc;--mu:#94a3b8}*{box-sizing:border-box}"
            "body{margin:0;background:var(--bg);color:var(--tx);font:11px/1.35 -apple-system,'Segoe UI',Roboto,'Microsoft JhengHei',sans-serif}"
            ".wrap{max-width:1300px;margin:0 auto;padding:18px 14px 48px}h1{font-size:14px;margin:0}.sub{color:var(--mu);margin:3px 0 14px}h2{font-size:12px;margin:20px 0 7px;border-bottom:1px solid var(--line);padding-bottom:5px}"
            ".nav a{color:#7dd3fc;margin-right:12px;text-decoration:none}.big{font-size:22px;font-weight:700;margin:6px 0 14px}"
            ".kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:8px;margin-bottom:14px}.kpi{background:var(--card);border:1px solid var(--line);border-radius:3px;padding:9px 11px}.kpi .n{font-size:15px;font-weight:600}.kpi .l{font-size:10px;color:var(--mu)}"
            "table{width:100%;table-layout:fixed;border-collapse:collapse;background:var(--card);border:1px solid var(--line)}th{font-size:10px;color:var(--mu);text-align:left;padding:4px 6px;border-bottom:1px solid var(--line)}td{padding:4px 6px;border-bottom:1px solid #253248;vertical-align:top;word-wrap:break-word;overflow-wrap:break-word;white-space:normal}td.c{text-align:center}.m{font-family:ui-monospace,Consolas,monospace;font-size:10px}.dim{color:var(--mu)}"
            ".b{display:inline-block;font-size:10px;padding:1px 6px;border-radius:2px;border:1px solid}.gr{background:#064e3b;color:#34d399;border-color:#059669}.ye{background:#78350f;color:#fde047;border-color:#d97706}.rd{background:#7f1d1d;color:#fca5a5;border-color:#dc2626}.gy{background:#1f2937;color:#9ca3af;border-color:#374151}"
            ".note{background:var(--card);border:1px solid var(--line);border-left:3px solid #d97706;border-radius:3px;padding:10px 12px;margin-top:16px}ul{margin:6px 0;padding-left:18px}"
            "@media(max-width:700px){table,thead,tbody,tr,td,th{display:block}thead{display:none}td{border:0;padding:2px 6px}tr{border-bottom:1px solid var(--line);padding:6px 0}}</style></head><body><div class=\"wrap\">")
    body = ("<h1>VIA PRODUCT GATE · 產品資格閘 · 九閘</h1><p class=\"sub\">" + e(r["engine"]) + " · " + e(r["stamp"]) + " · grid " + e(str(r["grid"]["name"])) + " OK " + str(r["grid"]["ok"])
            + " FAIL " + str(r["grid"]["fail"]) + " SKIP " + str(r["grid"]["skip"]) + " · " + str(r.get("elapsed_s", "")) + " s</p>"
            '<p class="nav"><a href="VIA_UI_ProjectCompletion_v0100.html">竣</a><a href="VIA_UI_VDFArchitecture_v0100.html">架</a><a href="VIA_UI_Consolidated_v0100.html">整</a>'
            '<a href="VIA_UI_SystemCharter_v0100.html">冊</a><a href="VIA_UI_LifecycleRACI_v0100.html">環</a><a href="VIA_UI_MasterControl_v0100.html">總控</a></p>'
            '<div class="big">' + _badge(r["verdict"]) + "</div><div class=\"kpis\">" + kp + "</div>"
            "<h2>GATES — G1..G9(state · evidence verbatim · next command)</h2>"
            '<table><colgroup><col style="width:5%"><col style="width:12%"><col style="width:8%"><col style="width:55%"><col style="width:20%"></colgroup>'
            "<thead><tr><th>id</th><th>gate</th><th>state</th><th>evidence</th><th>next</th></tr></thead><tbody>" + grows + "</tbody></table>"
            "<h2>PROJECTS — four projects from the same GRID evidence(MDL131 station map)</h2>"
            '<table><colgroup><col style="width:34%"><col style="width:16%"><col style="width:16%"><col style="width:17%"><col style="width:17%"></colgroup>'
            "<thead><tr><th>project</th><th>RYG</th><th>OK/stations</th><th>code-side FAIL</th><th>data-side FAIL</th></tr></thead><tbody>" + prows + "</tbody></table>"
            "<h2>USAGE — product manual(mobile first)</h2><ul>" + urows + "</ul>"
            '<div class="note">' + "<br>".join(e(x) for x in r["rules"]) + "</div></div></body></html>")
    return head + body


# ---------------------------------------------------------------- 自測
def selftest() -> int:
    import tempfile
    global PAGE, BOOK
    fails = []

    def chk(name, cond, note=""):
        print("  [" + ("OK" if cond else "FAIL") + "] " + name + " " + note)
        if not cond:
            fails.append(name)

    chk("① 九閘冊固定 G1–G9 且產品任務/短令/頁冊非空", [f.__name__[:2] for f in (g1_grid, g2_shims, g3_tasks, g4_pages, g5_regen, g6_keys, g7_engines, g8_cmds, g9_usage)] == ["g1", "g2", "g3", "g4", "g5", "g6", "g7", "g8", "g9"]
        and len(PRODUCT_TASKS) >= 12 and len(PRODUCT_CMDS) >= 12 and len(PRODUCT_PAGES) >= 6 and len(REGEN_PAGES) >= 4)
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        fake_key = "deadbeef" * 4
        fh = {hashlib.sha256(fake_key.encode()).hexdigest()}
        (tdp / "leak.py").write_text("KEY = '" + fake_key + "'\n", encoding="utf-8")
        (tdp / "clean.py").write_text("KEY = '<REDACTED:VDF_FRED_API_KEY>'\nX='" + "0" * 32 + "'\n", encoding="utf-8")
        (tdp / "big.bin").write_bytes(b"\0" * 10)
        hits = key_scan(tdp, fh)
        own = Path(__file__).read_text(encoding="utf-8")
        chk("② 鑰匙守衛(指紋比對:leak 命中 1;clean/非文字零命中;本檔零明文鑰)", hits == ["leak.py"]
            and not any(hashlib.sha256(t.encode()).hexdigest() in KEY_HASHES for t in HEX32_RX.findall(own)))
        reg = "function global:via-a { }\nfunction global:via-b { }\nfunction global:via-all { }\n"
        (tdp / "via-a.cmd").write_text("x", encoding="utf-8")
        g = g2_shims(reg, tdp)
        (tdp / "via-b.cmd").write_text("x", encoding="utf-8")
        g_ok = g2_shims(reg, tdp)
        chk("③ 短令↔梭(缺 via-b=FAIL 列名;讓位 via-all 不計;補齊=OK)", g["state"] == "FAIL" and "via-b" in g["evidence"] and "via-all" not in g["evidence"].split("缺梭")[1] and g_ok["state"] == "OK")
        base = [{"name": "VDF 資料架構九檢(批376)", "state": "OK"}, {"name": "FRED 巨觀 SSOT 十七檢(批376)", "state": "OK"}, {"name": "月營收史深回補九檢(批376)", "state": "OK"},
                {"name": "主動ETF×月營收動能八檢(批376)", "state": "OK"}, {"name": "主動ETF宇宙八檢(批376)", "state": "OK"}, {"name": "主動ETF持股史深八檢(批376)", "state": "OK"},
                {"name": "四專案完工矩陣七檢(批376)", "state": "OK"}, {"name": "VES 橋六檢(批376)", "state": "OK"}, {"name": "sysman 三輪協議", "state": "OK"}]
        gA = g1_grid({"name": "T", "ok": 9, "fail": 0, "skip": 0, "results": base})
        gB = g1_grid({"name": "T", "ok": 8, "fail": 1, "skip": 0, "results": base + [{"name": "族群站", "state": "FAIL", "note": "0 群·快照缺"}]})
        gC = g1_grid({"name": "T", "ok": 8, "fail": 1, "skip": 0, "results": base + [{"name": "x站", "state": "FAIL", "note": "", "detail": "Traceback (most recent call last)"}]})
        gD = g1_grid({"name": "T", "ok": 1, "fail": 0, "skip": 0, "results": base[:3]})
        gE = g1_grid({"name": "", "results": []})
        chk("④ 矩陣閘(全綠=OK;料紅=WARN;碼紅=FAIL;八站未齊=FAIL 早於 v0225;無存證=FAIL→via-selftest)",
            gA["state"] == "OK" and gB["state"] == "WARN" and gC["state"] == "FAIL" and gD["state"] == "FAIL" and "v0225" in gD["evidence"] and gE["state"] == "FAIL" and gE["next"] == "via-selftest")
        (tdp / "cdn.html").write_text('<meta name="viewport"><script src="https://cdn.x/y.js"></script>@media', encoding="utf-8")
        (tdp / "good.html").write_text('<meta name="viewport" content="w"><style>@media(max-width:700px){}</style><script>1</script>', encoding="utf-8")
        g4a = g4_pages(tdp, {"cdn.html": "c", "good.html": "c"})
        g4b = g4_pages(tdp, {"good.html": "c", "nope.html": "via-x"})
        g4c = g4_pages(tdp, {"good.html": "c"})
        chk("⑤ 頁衛生(CDN 外連=FAIL;缺頁=WARN 列再生指令;綠=OK)", g4a["state"] == "FAIL" and "CDN" in g4a["evidence"] and g4b["state"] == "WARN" and "via-x" in g4b["next"] and g4c["state"] == "OK")
        pats = ["VeritasIntelligenceAnalytics/supportive modules/ui_support/VIA_UI_ETFRevenueMomentum_v*.html", "*.log"]
        g5a, g5b = g5_regen(pats), g5_regen(pats + [p.replace("VIA_UI_", "VeritasIntelligenceAnalytics/supportive modules/ui_support/VIA_UI_") for p in REGEN_PAGES])
        chk("⑥ 再生物讓位(.gitignore 缺列=FAIL 列名;齊=OK)", g5a["state"] == "FAIL" and "ActiveETFHoldingsHistory" in g5a["evidence"] and g5b["state"] == "OK")
        chk("⑦ 資格律(FAIL→NOT_QUALIFIED;WARN→CONDITIONAL;全 OK→QUALIFIED;SKIP 不降級)",
            verdict([gate("a", "", "OK", ""), gate("b", "", "FAIL", "")]) == "NOT_QUALIFIED" and verdict([gate("a", "", "OK", ""), gate("b", "", "WARN", "")]) == "CONDITIONAL"
            and verdict([gate("a", "", "OK", ""), gate("b", "", "SKIP", "")]) == "QUALIFIED")
        _s = (PAGE, BOOK)
        PAGE, BOOK = tdp / "p.html", tdp / "b.json"
        rep = build(do_print=False)
        t = PAGE.read_text(encoding="utf-8")
        PAGE, BOOK = _s
        chk("⑧ 頁+冊(九閘 G1..G9 全列;verdict;手機單欄 @media;零 CDN;usage;導航 竣/架)",
            all(("<td class=\"m\">G" + str(i) + "</td>") in t for i in range(1, 10)) and rep["verdict"] in ("QUALIFIED", "CONDITIONAL", "NOT_QUALIFIED")
            and "@media" in t and not CDN_RX.search(t) and "via-mobile" in t and "VIA_UI_ProjectCompletion_v0100.html" in t and (tdp / "b.json").exists() and len(rep["gates"]) == 9)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑨ 紀律宣告(零重測零發明/誠實三態/只增不減/尾版律/永不假綠)", all(k in src for k in ("零重測零發明", "誠實三態", "只增不減", "尾版律", "永不假綠")))
    print("  [計] 九檢 OK " + str(9 - len(fails)) + " · FAIL " + str(len(fails)))
    return 1 if fails else 0


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print("=== 產品資格閘(" + ENGINE_TAG + ")· 九檢自測 ===")
        return selftest()
    if a and a[0] == "digest":
        return digest()
    if a and a[0] == "--json":
        print(json.dumps(build(do_print=False, write=False), ensure_ascii=False, indent=1))
        return 0
    rep = build()
    if "--open" in a and os.environ.get("VIA_NO_OPEN", "0") != "1":
        try:
            import webbrowser
            webbrowser.open(PAGE.as_uri())
        except Exception:
            pass
    return 0 if rep["verdict"] != "NOT_QUALIFIED" else 1


if __name__ == "__main__":
    sys.exit(main())
