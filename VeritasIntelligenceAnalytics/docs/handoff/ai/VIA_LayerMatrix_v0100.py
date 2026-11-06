#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VIA_LayerMatrix v0100 — VDF 分階層輸入 / 輸出 × VQG 分階層量化數據項目 的高度整合可驗證矩陣(操作員 2026-11-06 令)

操作員令:「用矩陣顯示 VDF 分階層輸入輸出 + VQG 分階層量化數據項目 高度整合矩陣可驗證很重請強化 · VCGC / VDF / VRN / VQG / VAP 皆為獨立系統原則不變 ·
檢視過去三天紀錄及近收尾 VDF / VRN」。

本支只讀:冊(VDF 資料架構律 · DataHome · 擷取族群冊 · 工作流冊 · 交接冊)· 樹上尾版(sha256)· 交接收據(rc / 標記 / 完成時間)· VQG 匯出夾(目錄 · 表頭 · SHA256SUMS)·
git 近三天紀錄(本地 git log,零網路)。不改任何系統的檔;輸出只寫在 --out(預設 VIA_Reports/layer_matrix)與 --snapshot 指定的文件。
可驗證:每一格都附「來源(檔 · sha256 前 12)/ 交接案(rc · 標記 · 日期)/ 匯出夾(SHA256SUMS)」,沒有證據的格照實標 NODATA,不冒充。
五系統對等(L120 / L123):矩陣是 VCGC 的攤開,不代表任何系統的驗收;VDF 曆三欄(session_index / available_on / market)仍是 VDF 自己的手(G2)。
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

VERSION = "v0100"
ENGINE = "VIA_LayerMatrix"
HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent.parent            # …/VeritasIntelligenceAnalytics
REPO = VIA.parent
REG = VIA / "supportive modules" / "registry"
EVID = VIA / "docs" / "handoff" / "evidence"
SYSTEMS = {"VCGC": "supportive modules/registry", "VDF": "functional modules/VDF", "VRN-2": "functional modules/VRN",
           "VQG": "functional modules/VQG", "VAP": "functional modules/VAP"}


def sha12(p: Path) -> str:
    try:
        return hashlib.sha256(p.read_bytes()).hexdigest()[:12]
    except OSError:
        return "-"


def tail(glob_pat: str, root: Path = VIA) -> Path | None:
    hits = sorted(root.glob(glob_pat))
    return hits[-1] if hits else None


def receipt(case: str) -> dict:
    p = EVID / (case + ".json")
    if not p.is_file():
        return {"case": case, "state": "NODATA"}
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"case": case, "state": "NODATA"}
    ok = d.get("rc") == 0 and bool(d.get("target_marker_seen"))
    return {"case": case, "rc": d.get("rc"), "marker": bool(d.get("target_marker_seen")), "at": str(d.get("completed_at", ""))[:10],
            "state": "GREEN" if ok else "RED"}


# ---------------------------------------------------------------- VDF 分階層(輸入 / 輸出)
VDF_LAYERS = [
    {"id": "VDF-L0", "name": "清單 · 宇宙(輸入範圍)", "inputs": ["輸入範圍冊 VDF_InputUniverse / TaiwanStockGroup.json", "擷取族群冊 VDF_FetchGroups_SSOT 尾版", "官方名錄(TWSE / TPEX;主動 ETF 名錄)"],
     "outputs": ["tw_list(股票全集)", "etf_list(主動 ETF 宇宙)", "族群成員 × 起始日"],
     "engines": ["functional modules/VDF/VDF_MDL012_FetchGroups_v*.py", "functional modules/VDF/VDF_ENG093_LaunchConsole_v*.py", "functional modules/VDF/engine/VDF_ENG231_GlobalListings_v*.py"],
     "books": ["functional modules/VDF/VDF_FetchGroups_SSOT_v0102.json", "functional modules/VDF/TaiwanStockGroup.json"],
     "cases": ["vdf_lists", "vdf_list_stock_v0102", "vdf_list_etf", "vdf_universe", "vdf_fetch_groups_v0108"]},
    {"id": "VDF-L1", "name": "擷取(價量 · 籌碼 · 成交值 · 指數;經 VIA 網路工具)", "inputs": ["L0 清單", "網路工具 SUP_MDL740 / AegisNexus v1652(鎖冊)", "fetch_ledger 預算(R-DB-04)"],
     "outputs": ["單位檔 output_hub/<table>_<stamp>.parquet(tw__ / gl__)", "fetch_ledger.jsonl(請求 · 位元組 · 失敗)", "亂碼解碼收據(ENG235)"],
     "engines": ["functional modules/VDF/VDF_MDL008_*_v*.py", "functional modules/VDF/VDF_MDL011_*_v*.py", "functional modules/VDF/engine/VDF_ENG235_MojibakeRepair_v*.py", "supportive modules/network/SUP_MDL740_NetUnified_v*.py"],
     "books": ["functional modules/VDF/VDF_DataArchitecture_Rule_SSOT_v0100.json", "supportive modules/registry/VIA_ToolVersion_Lock_v0100.json"],
     "cases": ["vdf_fetch_v0107", "vdf_fetch_system", "vdf_fetch_integration", "mojibake_repair_v0100", "netunified_v0119"]},
    {"id": "VDF-L2", "name": "增量 · 覆蓋閘 · 對齊(擷取前看現況 · anti-join 不重複)", "inputs": ["L1 單位檔", "既有分區 parquet(ticker=/year=)", "交易日曆(加權 / 櫃買官方日資料)"],
     "outputs": ["(ticker × 交易日)三態圖(已有 / 缺口 / 過期)", "增量寫入(主鍵 date, ticker;重複 = RED)", "價量 × 籌碼對齊表"],
     "engines": ["functional modules/VDF/engine/VDF_ENG089_IncrementalFetchGate_v*.py", "functional modules/VDF/engine/VDF_ENG090_DataCoverageGate_v*.py", "functional modules/VDF/engine/VDF_ENG054_TWDailyBackfill_v*.py", "functional modules/VDF/engine/VDF_ENG064_HistoryBackfill_v*.py"],
     "books": ["functional modules/VDF/VDF_DataArchitecture_Rule_SSOT_v0100.json"],
     "cases": ["vdf_incgate_catalog", "vdf_index_incr", "vdf_refill", "vdf_xsrc_verifier"]},
    {"id": "VDF-L3", "name": "DuckDB 庫(每子題一庫 · 只管理 parquet)", "inputs": ["L2 增量分區", "DataHome 冊(家 → 庫夾)"],
     "outputs": ["VDF_TWEquity_Daily · ActiveTWETF · VDF_TWIndex_Daily · VDF_Universe …(.duckdb VIEW → parquet)", "db check / db verify 收據"],
     "engines": ["functional modules/VDF/engine/VDF_ENG079_LocalDbConsolidate_v*.py", "functional modules/VDF/engine/VDF_ENG065_DbImport_v*.py", "functional modules/VDF/VDF_SystemManager_v*.py"],
     "books": ["functional modules/VDF/VDF_DataHome_SSOT_v0101.json", "functional modules/VDF/VDF_DataArchitecture_Rule_SSOT_v0100.json"],
     "cases": ["vdf_local_db", "vdf_manager_db_verify", "db_import_v0102", "vdf_manager_v0157"]},
    {"id": "VDF-L4", "name": "輸出 · 對接(給 VQG / VAP 等應用;只讀)", "inputs": ["L3 庫 · output_hub 增量批次檔"],
     "outputs": ["output_hub/<table>_<stamp>.parquet(增量批次;被取代的列 superseded)", "欄:date · ticker · adj_close · volume(+ 曆三欄 session_index · available_on · market = VDF 自己的手,G2)"],
     "engines": ["functional modules/VDF/VDF_SystemManager_v*.py", "functional modules/VDF/ActivateVDF_v*.py"],
     "books": ["functional modules/VDF/VDF_DataHome_SSOT_v0101.json", "functional modules/VDF/VDF_AdjPrice_Rule_SSOT_v0100.json"],
     "cases": ["vdf_eng045_outputhub", "vdf_activatevdf", "vdf_manager_split_xcheck"]},
]

# ---------------------------------------------------------------- VQG 分階層(量化數據項目)
SERIES_SEMANTICS = {"date": "交易日(x 軸)", "ticker": "代號(.TW / .TWO / 美股)", "adj_close": "還原價(ADJUSTED_PRICE_ONLY)", "volume": "成交量",
                    "turnover": "成交值", "daytrade_volume": "當沖量", "daytrade_turnover": "當沖值", "clean_volume": "扣當沖量", "clean_turnover": "扣當沖值",
                    "market": "市場(TW / US;曆規則)", "session_index": "交易日序(VDF 曆;VQG 推算 = 🟡)", "available_on": "可用日(截止日:TW = 隔天 · US = 當日)",
                    "source_files": "來源批次檔", "engine_version": "VQG 版本"}
INDICATOR_FIELDS = ["request_key", "ticker", "indicator", "window", "solution", "observation_date", "available_on", "value", "value_json", "quality",
                    "source_snapshot", "engine_version"]
VQG_LAYERS = [
    {"id": "VQG-Q0", "name": "VDF 目錄(整理全部;無論有無加工)", "items": ["entries[].file / bytes / mtime / sha256", "table · snapshot · superseded(被新批次取代)", "columns · rows · tickers_sample", "unreadable 照列"],
     "engines": ["functional modules/VQG/VQG_AllInOne_v*.py"], "books": ["docs/handoff/ai/VIA_VQG_to_VAP_Contract_20261106.md"], "cases": ["vqg"], "export_file": "vqg_vdf_catalog.json"},
    {"id": "VQG-Q1", "name": "SERIES(無加工一票一表 + 長表)", "items": [f"{k}:{v}" for k, v in SERIES_SEMANTICS.items()],
     "engines": ["functional modules/VQG/VQG_AllInOne_v*.py"], "books": ["docs/handoff/ai/VIA_VQG_to_VAP_Contract_20261106.md"], "cases": ["vqg"], "export_file": "vqg_series.csv"},
    {"id": "VQG-Q2", "name": "INDICATOR_RESULT(有加工一票一表 + 長表;QuantGuard 唯一正主)", "items": ["欄 <指標>_<窗>_<解>(例 SMA_20_S1 · RSI_14_S1)", "結構值展開 MACD_26_S1_line / _signal / _histogram", "最近 N 點(先濾截止日 ≤ as-of 再取 N)", "長表欄:" + " · ".join(INDICATOR_FIELDS)],
     "engines": ["functional modules/VQG/VQG_AllInOne_v*.py", "functional modules/VDF/engine/VDF_ENG086_QuantGuardOneBridge_v*.py"], "books": ["docs/handoff/ai/VIA_VQG_to_VAP_Contract_20261106.md"], "cases": ["vqg"], "export_file": "vqg_indicator_results.csv"},
    {"id": "VQG-Q3", "name": "連線證據(VIA-VQG-VAP-CONNECTION-MANIFEST/1.0)", "items": ["contractId VQG-SERIES-v1 / VQG-INDICATOR-v1", "sourceId · AUTHORIZED · readOnly · PARQUET", "limits 5000 / 100 / 252 · xField · fieldSemantics", "fingerprint = sha256(排序 JSON)· pricePolicy ADJUSTED_PRICE_ONLY · taLibPolicy CALCULATE_ONLY_NO_FETCH"],
     "engines": ["functional modules/VQG/VQG_AllInOne_v*.py"], "books": ["docs/handoff/ai/VIA_VQG_to_VAP_Contract_20261106.md"], "cases": ["vqg"], "export_file": "vqg_connection_manifest.json"},
    {"id": "VQG-Q4", "name": "VAP 匯入(U/I 閘:列 ≥ 3 · x 唯一且遞增 · 數值欄 ≥ 2)", "items": ["VAP_AllInOne_v0300.config.json(formalInputAuthority VQG · allowedRoots)", "export_receipt.json 每表 ui_gate", "SHA256SUMS.txt 全檔"],
     "engines": ["functional modules/VAP/intake/allinone_v0300/VAP_AllInOne_v*.py"], "books": ["docs/handoff/ai/VIA_Atlas_VisualLock_20261106.md"], "cases": [], "export_file": "export_receipt.json"},
]

# ---------------------------------------------------------------- 整合矩陣(VDF 層 × VQG 層)
INTEGRATION = {
    ("VDF-L4", "VQG-Q0"): ("output_hub 批次檔 → 目錄逐檔 sha256 / rows / columns / superseded", "export:vqg_vdf_catalog.json"),
    ("VDF-L4", "VQG-Q1"): ("date · ticker · adj_close · volume 直接進 SERIES;當沖 / 成交值欄有就帶", "export:vqg_series.csv"),
    ("VDF-L2", "VQG-Q1"): ("曆三欄 session_index / available_on / market:VDF 出就用 VDF(strict),沒有才由日線推(derive = 🟡;G2 不代改)", "book:functional modules/VDF/VDF_DataArchitecture_Rule_SSOT_v0100.json"),
    ("VDF-L4", "VQG-Q2"): ("還原價序列 → QuantGuard 指標(ADJUSTED_PRICE_ONLY;TA-Lib 禁用 L50)", "export:vqg_indicator_results.csv"),
    ("VDF-L3", "VQG-Q0"): ("VQG 只讀 VDF 家(VDF_DataHome_SSOT / VQG_VDF_ROOT);收據夾在 VDF 庫裡 → rc 2 不寫(樹簽章不變)", "book:functional modules/VDF/VDF_DataHome_SSOT_v0101.json"),
    ("VDF-L4", "VQG-Q3"): ("每表 upstreamEvidence 指回 VDF 批次檔 sha256 → 指紋", "export:vqg_connection_manifest.json"),
    ("VDF-L4", "VQG-Q4"): ("VAP 只經 config allowedRoots 讀匯出夾;VQG 不 import VAP · VAP 不 import VQG", "export:VAP_AllInOne_v0300.config.json"),
}


def export_columns(export_dir: Path | None, name: str) -> dict:
    """匯出夾一檔的可驗證事實:CSV 表頭(欄)· JSON 頂層鍵 · SHA256SUMS 裡的雜湊。零 duckdb 依賴。"""
    if not export_dir:
        return {"state": "NODATA", "why": "沒給 --export"}
    p = export_dir / name
    if not p.is_file():
        return {"state": "NODATA", "why": f"{name} 不在匯出夾"}
    out = {"state": "GREEN", "file": name, "sha12": sha12(p), "bytes": p.stat().st_size}
    sums = export_dir / "SHA256SUMS.txt"
    if sums.is_file():
        listed = any(name in line for line in sums.read_text(encoding="utf-8", errors="ignore").splitlines())
        out["in_sha256sums"] = listed
    if name.endswith(".csv"):
        with p.open(encoding="utf-8", newline="") as f:
            out["columns"] = next(csv.reader(f), [])
        out["rows"] = max(0, sum(1 for _ in p.open(encoding="utf-8", errors="ignore")) - 1)
    elif name.endswith(".json"):
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
            out["keys"] = list(d.keys())[:14] if isinstance(d, dict) else f"list[{len(d)}]"
            if isinstance(d, dict) and "entries" in d:
                out["entries"] = len(d["entries"])
            if isinstance(d, dict) and "connections" in d:
                out["connections"] = len(d["connections"])
        except ValueError:
            out["state"] = "RED"
    return out


def resolve(layer: dict) -> dict:
    eng = []
    for pat in layer["engines"]:
        t = tail(pat)
        eng.append({"pattern": pat, "tail": str(t.relative_to(VIA)) if t else None, "sha12": sha12(t) if t else "-", "state": "GREEN" if t else "NODATA"})
    books = [{"file": b, "sha12": sha12(VIA / b), "state": "GREEN" if (VIA / b).is_file() else "NODATA"} for b in layer["books"]]
    cases = [receipt(c) for c in layer["cases"]]
    states = [e["state"] for e in eng] + [b["state"] for b in books] + [c["state"] for c in cases if c["state"] != "NODATA"]
    lamp = "RED" if "RED" in states else ("YELLOW" if "NODATA" in states or any(c["state"] == "NODATA" for c in cases) else "GREEN")
    return dict(layer, engines_resolved=eng, books_resolved=books, cases_resolved=cases, lamp=lamp)


def git_recent(days: int = 3) -> dict:
    out = {}
    for name, rel in SYSTEMS.items():
        try:
            r = subprocess.run(["git", "-C", str(REPO), "log", f"--since={days} days ago", "--format=%h %ad %s", "--date=short", "--", f"VeritasIntelligenceAnalytics/{rel}"],
                               capture_output=True, text=True, timeout=60)
            lines = [l for l in r.stdout.splitlines() if l.strip()]
        except (OSError, subprocess.SubprocessError):
            lines = []
        out[name] = {"n": len(lines), "commits": [l[:160] for l in lines[:12]]}
    return out


def closeout_review() -> dict:
    """近收尾 VDF / VRN:交接收據綠 / 紅(前綴)· 近兩版 SettleAll 文件 · 交接 §31 一行。"""
    rows = {}
    for sysname, prefixes in (("VDF", ("vdf_", "db_import", "mojibake")), ("VRN-2", ("vrn_", "cov_vrn", "provenance", "metrics_resolve")), ("VQG", ("vqg",)), ("VCGC", ("vcgc_", "ui_engine", "health_matrix", "celeritas", "tool_", "version_panorama", "numbering", "handoff", "sweeper", "accel"))):
        greens = reds = 0
        red_names = []
        for p in EVID.glob("*.json"):
            if not p.stem.startswith(prefixes):
                continue
            r = receipt(p.stem)
            if r["state"] == "GREEN":
                greens += 1
            elif r["state"] == "RED":
                reds += 1
                red_names.append(p.stem)
        rows[sysname] = {"green": greens, "red": reds, "red_cases": sorted(red_names)[:24]}
    docs = sorted((HERE).glob("VIA_SettleAll_v*.md"))[-2:]
    rows["settleall_docs"] = [{"file": d.name, "sha12": sha12(d)} for d in docs]
    hand = HERE / "VRN2_Handover_latest.md"
    rows["handover"] = {"file": hand.name, "sha12": sha12(hand), "sections": sum(1 for l in hand.read_text(encoding="utf-8", errors="ignore").splitlines() if l.startswith("## "))} if hand.is_file() else {"state": "NODATA"}
    return rows


def build(export_dir: Path | None) -> dict:
    vdf = [resolve(l) for l in VDF_LAYERS]
    vqg = []
    for l in VQG_LAYERS:
        r = resolve(l)
        r["export"] = export_columns(export_dir, l["export_file"])
        if r["export"]["state"] == "NODATA" and r["lamp"] == "GREEN":
            r["lamp"] = "YELLOW"
        vqg.append(r)
    cells = []
    for (a, b), (text, ev) in INTEGRATION.items():
        kind, _, ref = ev.partition(":")
        if kind == "export":
            e = export_columns(export_dir, ref)
            state = e["state"]
            evid = f"匯出夾 {ref} sha {e.get('sha12', '-')}" if state == "GREEN" else f"匯出夾 {ref}:{e.get('why', 'NODATA')}"
        else:
            p = VIA / ref
            state = "GREEN" if p.is_file() else "NODATA"
            evid = f"冊 {ref} sha {sha12(p)}" if p.is_file() else f"冊 {ref} 不在"
        if "🟡" in text:
            state = "YELLOW" if state == "GREEN" else state
        cells.append({"vdf": a, "vqg": b, "link": text, "evidence": evid, "state": state})
    return {"schema": "VIA.LayerMatrix.v1", "engine": f"{ENGINE} {VERSION}", "at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S +0000"),
            "principle": "VCGC / VDF / VRN-2 / VQG / VAP 皆為獨立系統(L120 / L123);本矩陣只讀攤開,不代改、不代驗收",
            "export_dir": str(export_dir) if export_dir else None, "vdf_layers": vdf, "vqg_layers": vqg, "integration": cells,
            "recent_commits_3d": git_recent(3), "closeout_review": closeout_review()}


LAMP = {"GREEN": "🟢", "YELLOW": "🟡", "RED": "🔴", "NODATA": "⚪"}


def to_md(m: dict) -> str:
    L = [f"# VDF 分階層輸入 / 輸出 × VQG 分階層量化數據項目 —— 高度整合可驗證矩陣({m['engine']} · {m['at']})", "",
         f"> {m['principle']}。匯出夾:`{m['export_dir'] or 'NODATA(沒給 --export)'}`。每格證據:尾版 sha256 前 12 · 冊 sha · 交接案 rc / 標記 / 日期 · 匯出夾 SHA256SUMS。", "",
         "## 一、VDF 分階層(輸入 → 輸出)", "", "| 燈 | 層 | 輸入 | 輸出 | 引擎尾版(sha12) | 冊(sha12) | 交接案(rc · 標記 · 日期) |", "|---|---|---|---|---|---|---|"]
    for l in m["vdf_layers"]:
        eng = "<br>".join(f"`{e['tail'] or e['pattern']}` {e['sha12']}" for e in l["engines_resolved"])
        books = "<br>".join(f"`{b['file'].split('/')[-1]}` {b['sha12']}" for b in l["books_resolved"])
        cases = "<br>".join(f"{LAMP[c['state']]} {c['case']} rc {c.get('rc', '-')} · {'標記' if c.get('marker') else '無標記'} · {c.get('at', '-')}" if c["state"] != "NODATA" else f"⚪ {c['case']} NODATA" for c in l["cases_resolved"])
        L.append(f"| {LAMP[l['lamp']]} | **{l['id']}** {l['name']} | {'<br>'.join(l['inputs'])} | {'<br>'.join(l['outputs'])} | {eng} | {books} | {cases} |")
    L += ["", "## 二、VQG 分階層(量化數據項目)", "", "| 燈 | 層 | 量化數據項目 | 匯出夾實測(欄 · 列 · sha12 · SHA256SUMS) | 引擎 / 冊 | 交接案 |", "|---|---|---|---|---|---|"]
    for l in m["vqg_layers"]:
        e = l["export"]
        live = (f"`{e['file']}` sha {e['sha12']} · {'在' if e.get('in_sha256sums') else '不在'} SHA256SUMS" + (f" · 欄 {len(e['columns'])}:{' · '.join(e['columns'][:16])}" if e.get("columns") else "") + (f" · 列 {e['rows']}" if "rows" in e else "") + (f" · entries {e['entries']}" if "entries" in e else "") + (f" · connections {e['connections']}" if "connections" in e else "")) if e["state"] == "GREEN" else f"⚪ {e.get('why', 'NODATA')}"
        eng = "<br>".join(f"`{x['tail'].split('/')[-1] if x['tail'] else x['pattern']}` {x['sha12']}" for x in l["engines_resolved"]) + "<br>" + "<br>".join(f"`{b['file'].split('/')[-1]}` {b['sha12']}" for b in l["books_resolved"])
        cases = "<br>".join(f"{LAMP[c['state']]} {c['case']} rc {c.get('rc', '-')} · {c.get('at', '-')}" if c["state"] != "NODATA" else f"⚪ {c['case']}" for c in l["cases_resolved"]) or "—"
        L.append(f"| {LAMP[l['lamp']]} | **{l['id']}** {l['name']} | {'<br>'.join(l['items'])} | {live} | {eng} | {cases} |")
    L += ["", "## 三、整合矩陣(VDF 層 × VQG 層;格 = 契約 + 證據)", "", "| VDF ＼ VQG | " + " | ".join(l["id"] for l in m["vqg_layers"]) + " |", "|---|" + "---|" * len(m["vqg_layers"])]
    for v in m["vdf_layers"]:
        row = [f"**{v['id']}**"]
        for q in m["vqg_layers"]:
            c = next((x for x in m["integration"] if x["vdf"] == v["id"] and x["vqg"] == q["id"]), None)
            row.append(f"{LAMP[c['state']]} {c['link']}<br><sub>{c['evidence']}</sub>" if c else "—")
        L.append("| " + " | ".join(row) + " |")
    L += ["", "## 四、過去三天紀錄(git log · 本地)", ""]
    for s, r in m["recent_commits_3d"].items():
        L.append(f"- **{s}**:{r['n']} 提交" + ("".join(f"<br>　`{c}`" for c in r["commits"][:6]) if r["commits"] else ""))
    cr = m["closeout_review"]
    L += ["", "## 五、近收尾 VDF / VRN(交接收據 · 文件)", "", "| 系統 | 收據綠 | 收據紅 | 紅案 |", "|---|---|---|---|"]
    for s in ("VDF", "VRN-2", "VQG", "VCGC"):
        L.append(f"| {s} | {cr[s]['green']} | {cr[s]['red']} | {' · '.join(cr[s]['red_cases'][:12]) or '—'} |")
    L.append("")
    L.append("- SettleAll 近兩版文件:" + " · ".join(f"`{d['file']}` {d['sha12']}" for d in cr["settleall_docs"]) + f";交接 `{cr['handover'].get('file', '-')}` 節 {cr['handover'].get('sections', '-')} sha {cr['handover'].get('sha12', '-')}")
    return "\n".join(L) + "\n"


def to_html(m: dict, md: str) -> str:
    rows = []
    for line in md.splitlines():
        if line.startswith("# "):
            rows.append(f"<h1>{html.escape(line[2:])}</h1>")
        elif line.startswith("## "):
            rows.append(f"<h2>{html.escape(line[3:])}</h2>")
        elif line.startswith("> "):
            rows.append(f"<p class='note'>{html.escape(line[2:])}</p>")
        elif line.startswith("|---"):
            continue
        elif line.startswith("| "):
            cells = [c.strip() for c in line.strip().strip("|").split(" | ")]
            tag = "th" if (rows and not rows[-1].startswith("<tr")) else "td"
            body = "".join(f"<{tag}>{html.escape(c).replace('&lt;br&gt;', '<br>').replace('&lt;sub&gt;', '<sub>').replace('&lt;/sub&gt;', '</sub>').replace('`', '')}</{tag}>" for c in cells)
            rows.append(("<table><tr>" if tag == "th" else "<tr>") + body + "</tr>")
            if tag == "th":
                continue
        elif line.startswith("- "):
            rows.append(f"<li>{html.escape(line[2:]).replace('&lt;br&gt;', '<br>').replace('`', '')}</li>")
        elif not line.strip():
            if rows and rows[-1].startswith("<tr"):
                rows.append("</table>")
    if rows and rows[-1].startswith("<tr"):
        rows.append("</table>")
    css = ("body{font-family:system-ui,'Noto Sans TC',sans-serif;font-size:13px;color:#1c2430;background:#f7f8fa;margin:0;padding:18px 24px;max-width:1500px}"
           "h1{font-size:19px}h2{font-size:15px;margin-top:22px;border-left:4px solid #2c6e9b;padding-left:8px}table{border-collapse:collapse;width:100%;margin:6px 0 10px;background:#fff}"
           "th,td{border:1px solid #d7dde5;padding:5px 7px;vertical-align:top;text-align:left}th{background:#e9eef4}sub{color:#5a6b7d;font-size:10px}p.note{color:#4b5563}li{margin:3px 0}")
    return f"<!doctype html><html lang='zh-Hant'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>VIA 分階層整合矩陣 {html.escape(m['at'])}</title><style>{css}</style></head><body>{''.join(rows)}</body></html>\n"


def run(export_dir: Path | None, out: Path, snapshot: Path | None) -> dict:
    m = build(export_dir)
    md = to_md(m)
    out.mkdir(parents=True, exist_ok=True)
    (out / "VIA_LayerMatrix_latest.json").write_text(json.dumps(m, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    (out / "VIA_LayerMatrix_latest.md").write_text(md, encoding="utf-8")
    (out / "VIA_LayerMatrix_latest.html").write_text(to_html(m, md), encoding="utf-8")
    if snapshot:
        snapshot.parent.mkdir(parents=True, exist_ok=True)
        snapshot.write_text(md, encoding="utf-8")
        snapshot.with_suffix(".html").write_text(to_html(m, md), encoding="utf-8")
    return m


def selftest() -> int:
    results = []

    def chk(name, ok, note=""):
        results.append(bool(ok))
        print(f"  [{'OK' if ok else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    print(f"=== {ENGINE} {VERSION} 自測(只讀 · 零網路 · 只寫沙盒)===")
    text = Path(__file__).read_text(encoding="utf-8")
    chk("① 零網路 import · 不 import 任何系統模組(只讀檔)", not any(f"import {x}" in text for x in ("urllib", "requests", "httpx", "socket", "duckdb", "polars", "pandas")) and "[VIA:ACCEL-BRIDGE" in text)
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        ex = d / "export"
        ex.mkdir()
        (ex / "vqg_series.csv").write_text("date,ticker,adj_close,volume\n2026-11-03,2330.TW,1.0,2\n2026-11-04,2330.TW,1.1,3\n", encoding="utf-8")
        (ex / "vqg_indicator_results.csv").write_text(",".join(INDICATOR_FIELDS) + "\n", encoding="utf-8")
        (ex / "vqg_vdf_catalog.json").write_text(json.dumps({"schema": "VIA-VQG-VDF-CATALOG/1.0", "entries": [{"file": "a.parquet"}]}), encoding="utf-8")
        (ex / "vqg_connection_manifest.json").write_text(json.dumps({"schema": "VIA-VQG-VAP-CONNECTION-MANIFEST/1.0", "connections": [{}, {}]}), encoding="utf-8")
        (ex / "export_receipt.json").write_text("{}", encoding="utf-8")
        (ex / "VAP_AllInOne_v0300.config.json").write_text("{}", encoding="utf-8")
        (ex / "SHA256SUMS.txt").write_text("x  vqg_series.csv\nx  vqg_indicator_results.csv\n", encoding="utf-8")
        before = sorted(p.name for p in VIA.rglob("*") if p.is_file() and "VIA_Reports" not in p.parts and "__pycache__" not in p.parts)[:0]  # 不逐檔簽(大樹);改用時間戳比對 registry
        reg_mtime = max(p.stat().st_mtime for p in REG.glob("*.json"))
        m = run(ex, d / "out", d / "snap" / "VIA_LayerMatrix_test.md")
        e1 = export_columns(ex, "vqg_series.csv")
        chk("② 匯出夾實測:CSV 表頭 4 欄 · 列 2 · 在 SHA256SUMS;JSON entries / connections 計數", e1["columns"] == ["date", "ticker", "adj_close", "volume"] and e1["rows"] == 2 and e1["in_sha256sums"] is True
            and export_columns(ex, "vqg_vdf_catalog.json")["entries"] == 1 and export_columns(ex, "vqg_connection_manifest.json")["connections"] == 2)
        chk("③ 沒有的檔照實 NODATA(不冒充)", export_columns(ex, "nothing.csv")["state"] == "NODATA" and export_columns(None, "x")["state"] == "NODATA")
        eng_missing = [e["pattern"] for l in m["vdf_layers"] + m["vqg_layers"] for e in l["engines_resolved"] if e["state"] != "GREEN"]
        chk("④ 真樹:每層的引擎 glob 都解析到尾版(帶 sha12)", not eng_missing, f"缺 {eng_missing}")
        book_missing = [b["file"] for l in m["vdf_layers"] + m["vqg_layers"] for b in l["books_resolved"] if b["state"] != "GREEN"]
        chk("⑤ 真樹:每層引用的冊都在(帶 sha12)", not book_missing, f"缺 {book_missing}")
        cont = json.loads((REG / "VIA_Handoff_Continuity_SSOT_v0100.json").read_text(encoding="utf-8"))["test_cases"]
        unknown = [c for l in m["vdf_layers"] + m["vqg_layers"] for c in l["cases"] if c not in cont]
        chk("⑥ 每層引用的交接案都登在交接冊(收據照 rc / 標記)", not unknown, f"不在冊 {unknown}")
        chk("⑦ 整合矩陣每格都有證據字串 · 五層 × 五層 7 格 · 曆三欄那格照實 🟡", all(c["evidence"] for c in m["integration"]) and len(m["integration"]) == 7
            and next(c for c in m["integration"] if c["vdf"] == "VDF-L2")["state"] in ("YELLOW", "NODATA"))
        files = sorted(p.name for p in (d / "out").iterdir())
        chk("⑧ 三種輸出 + 快照 md / html 都寫在沙盒", files == ["VIA_LayerMatrix_latest.html", "VIA_LayerMatrix_latest.json", "VIA_LayerMatrix_latest.md"] and (d / "snap" / "VIA_LayerMatrix_test.html").is_file())
        chk("⑨ 近三天 git 紀錄五系統都有計數 · 近收尾四系統收據綠 / 紅都有數", set(m["recent_commits_3d"]) == set(SYSTEMS) and all(k in m["closeout_review"] for k in ("VDF", "VRN-2", "VQG", "VCGC")))
        chk("⑩ 只讀:registry 冊的 mtime 沒動(本支不改任何系統的檔)", max(p.stat().st_mtime for p in REG.glob("*.json")) == reg_mtime)
    ok = all(results)
    print(f"  [計] {ENGINE} {VERSION} 自測 {sum(results)}/{len(results)} · {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=f"{ENGINE} {VERSION}")
    ap.add_argument("--export", help="VQG 匯出夾 vap_export_<stamp>(有就實測欄 / 列 / SHA)")
    ap.add_argument("--out", default=str(VIA / "VIA_Reports" / "layer_matrix"))
    ap.add_argument("--snapshot", help="另存一份 md(+html)到指定路徑(例 docs/handoff/ai/VIA_VDF_VQG_LayerMatrix_<日期>.md)")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    m = run(Path(a.export).resolve() if a.export else None, Path(a.out), Path(a.snapshot) if a.snapshot else None)
    lamps = [l["lamp"] for l in m["vdf_layers"] + m["vqg_layers"]] + [c["state"] for c in m["integration"]]
    print(f"[{ENGINE} {VERSION}] VDF 層 {len(m['vdf_layers'])} · VQG 層 {len(m['vqg_layers'])} · 整合格 {len(m['integration'])} · 燈 綠 {lamps.count('GREEN')} 黃 {lamps.count('YELLOW')} 紅 {lamps.count('RED')} 無據 {lamps.count('NODATA')} · 頁 {Path(a.out) / 'VIA_LayerMatrix_latest.html'}")
    return 0 if "RED" not in lamps else 1


if __name__ == "__main__":
    raise SystemExit(main())
