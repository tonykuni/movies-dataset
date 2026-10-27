#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111] VRN-2 bridge · accelerator marker (accelfix 認得的現役橋標記)
# [VIA:NET-BRIDGE:v0100] 本引擎只讀本機 VDF 資料庫 · 不連網 · VDF 本身的擷取路由走鎖版網路工具(http_bytes / post_json)不在此檔
"""VRN2_VDFBridge v0100 — VRN-2 → VDF 唯讀橋(探測模式)。

目的:在不動 VDF 任何引擎、不連網的前提下,找出 VDF 本機資料庫裡能給 VRN-2 用的三類資料集:
  ① 上市櫃清單(代號 → 名稱 · 市場 TWSE / TPEX → yfinance 後綴 .TW / .TWO)
  ② 日線(代號 · 日期 · 收盤 / 還原收盤 → ADJ CLOSE · 報告日前收盤)
  ③ 財報數據(對照 VRN-2 年度數據冊)
並附三種台股代碼的規則與互填(前四碼原則):TWSE/TPEX 4 碼 ↔ yfinance 4 碼 + .TW/.TWO ↔ Bloomberg 4 碼 + TT。

動詞:
  --probe [--root <VIA 根>] [--data-home <vdf_database>]   掃描候選資料集 → VIA_Reports/vrn2/vdf_bridge/VRN2_VDFBridge_Probe_latest.{json,md}
  --selftest                                                 代碼規則與分類自測(合成資料)
--fill(把 NAME / YFINANCE / ADJ CLOSE 填進基本資料冊)留待探測結果確認欄位後的下一版,本版不動任何既有輸出冊。
"""
from __future__ import annotations

import datetime
import json
import os
import re
import sys
from pathlib import Path

VERSION = "v0100"
_BASE = re.compile(r"^([1-9]\d{3})$")
_YF = re.compile(r"^([1-9]\d{3})\.(TW|TWO)$")
_BB = re.compile(r"^([1-9]\d{3})\s+TT$")
_KW = {
    "listing": re.compile(r"(?i)list|listing|universe|company|companies|ticker|symbol|上市|上櫃|基本資料|TWEquity|MDL001|MDL004|isin|stock_info|t187"),
    "price": re.compile(r"(?i)price|close|daily|ohlc|quote|yfinance|yf_|MDL002|股價|日線|行情|PriceDaily"),
    "financial": re.compile(r"(?i)financ|fin_|mops|income|balance|cashflow|eps|revenue|財報|損益|資產負債|MDL00[5-7]"),
}
_EXT = {".parquet", ".duckdb", ".db", ".csv", ".json", ".feather", ".sqlite"}


def ticker_forms(code: str, market: str | None = None) -> dict:
    """三種形式互填:輸入任一形式 → 基礎 4 碼 · Bloomberg 必填 · yfinance 需市場(TWSE→.TW · TPEX→.TWO)或原字串已帶後綴。"""
    s = (code or "").strip().upper()
    base, suffix = "", ""
    m = _BASE.match(s) or _YF.match(s) or _BB.match(s)
    if m:
        base = m.group(1)
        if _YF.match(s):
            suffix = _YF.match(s).group(2)
    if not base:
        return {"base": "", "yfinance": "", "bloomberg": "", "status": "不合三種形式"}
    mk = {"TWSE": "TW", "TPEX": "TWO", "TW": "TW", "TWO": "TWO", "上市": "TW", "上櫃": "TWO"}.get((market or "").upper() if market else "", "")
    yf = "%s.%s" % (base, suffix or mk) if (suffix or mk) else ""
    return {"base": base, "yfinance": yf, "bloomberg": "%s TT" % base, "status": "齊" if yf else "缺市場別(需上市櫃清單)"}


def first4_check(filename: str, p1_ticker: str) -> tuple:
    """前四碼原則:檔名第一個 4 碼(首碼非 0 · 不是年份 19xx/20xx 緊接月日)須等於首頁代號。"""
    cands = [m.group(1) for m in re.finditer(r"(?<!\d)([1-9]\d{3})(?!\d)", filename or "")]
    cands = [c for c in cands if not (c[:2] in ("19", "20") and re.search(c + r"\d{4}", filename or ""))]
    base = ticker_forms(p1_ticker)["base"]
    if not cands or not base:
        return "GRAY", "檔名無 4 碼或首頁無代號"
    return ("GREEN", "檔名 %s = 首頁 %s" % (cands[0], base)) if cands[0] == base or base in cands else ("RED", "檔名 %s ≠ 首頁 %s" % (cands, base))


def _schema(p: Path) -> dict:
    out = {"file": str(p), "ext": p.suffix.lower(), "size": p.stat().st_size, "columns": [], "rows": None, "tables": []}
    try:
        if p.suffix.lower() == ".parquet":
            import pyarrow.parquet as pq
            f = pq.ParquetFile(str(p))
            out["columns"] = [str(c) for c in f.schema_arrow.names][:60]
            out["rows"] = f.metadata.num_rows
        elif p.suffix.lower() in (".duckdb", ".db", ".sqlite"):
            import duckdb
            con = duckdb.connect(str(p), read_only=True)
            for (t,) in con.execute("select table_name from information_schema.tables").fetchall()[:40]:
                cols = [r[0] for r in con.execute('select column_name from information_schema.columns where table_name = ?', [t]).fetchall()]
                out["tables"].append({"table": t, "columns": cols[:40]})
            con.close()
        elif p.suffix.lower() == ".csv":
            with p.open("r", encoding="utf-8-sig", errors="replace") as fh:
                out["columns"] = [c.strip() for c in fh.readline().split(",")][:60]
        elif p.suffix.lower() == ".json" and p.stat().st_size < 2_000_000:
            d = json.loads(p.read_text(encoding="utf-8", errors="replace"))
            out["columns"] = list(d.keys())[:40] if isinstance(d, dict) else (list(d[0].keys())[:40] if d and isinstance(d[0], dict) else [])
    except Exception as exc:  # noqa: BLE001
        out["error"] = type(exc).__name__
    return out


def _fit(sch: dict) -> dict:
    cols = " ".join(sch.get("columns") or []) + " " + " ".join(c for t in sch.get("tables") or [] for c in t.get("columns") or [])
    cl = cols.lower()
    return {"ticker": bool(re.search(r"ticker|symbol|code|代號|股票代碼|series_id|stock_id", cl)),
            "date": bool(re.search(r"date|trade_date|日期|time", cl)),
            "close": bool(re.search(r"close|收盤|px_value", cl)),
            "adj": bool(re.search(r"adj|還原|adjusted", cl)),
            "name": bool(re.search(r"name|名稱|公司|company", cl)),
            "market": bool(re.search(r"market|exchange|上市|上櫃|board|listed", cl))}


def probe(root: Path, data_home: Path, out_dir: Path, max_files: int = 6000) -> dict:
    roots = [data_home, root / "functional modules" / "VDF", root / "via_database", root / "dict" / "VDF", root / "VIA_Reports" / "vdf"]
    seen, found = set(), []
    entry = None
    for base in roots:
        if not base.is_dir():
            continue
        for p in base.rglob("*"):
            if len(seen) >= max_files:
                break
            if not p.is_file() or p.suffix.lower() not in _EXT or p in seen:
                continue
            seen.add(p)
            if p.name.startswith("VDF_DASHBOARD_FIS_ENTRYPOINT"):
                entry = str(p)
            kinds = [k for k, rx in _KW.items() if rx.search(p.name) or rx.search(str(p.parent.name))]
            if not kinds or p.stat().st_size < 200:
                continue
            sch = _schema(p)
            sch["kinds"] = kinds
            sch["fit"] = _fit(sch)
            found.append(sch)
    def score(s):
        f = s["fit"]
        return (int(f["ticker"]) + int(f["date"]) + int(f["close"]) + 2 * int(f["adj"]) + int(f["name"]) + int(f["market"]), s["size"])
    found.sort(key=score, reverse=True)
    rep = {"version": VERSION, "ts": datetime.datetime.now().isoformat(timespec="seconds"), "roots": [str(r) for r in roots], "roots_exist": [str(r) for r in roots if r.is_dir()],
           "scanned": len(seen), "entrypoint": entry,
           "listing": [s for s in found if "listing" in s["kinds"] and s["fit"]["name"]][:8],
           "price": [s for s in found if "price" in s["kinds"] and (s["fit"]["close"] or s["fit"]["adj"])][:8],
           "financial": [s for s in found if "financial" in s["kinds"]][:8],
           "other": [{"file": s["file"], "kinds": s["kinds"]} for s in found][:30]}
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "VRN2_VDFBridge_Probe_latest.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    md = ["# VRN2 VDF 橋探測 %s · %s" % (VERSION, rep["ts"]), "", "掃 %d 檔 · 根 %s · 入口 JSON %s" % (len(seen), " | ".join(rep["roots_exist"]) or "(都不存在)", entry or "無"), ""]
    for k, lab in (("listing", "① 上市櫃清單候選(代號 → 名稱 / 市場)"), ("price", "② 日線候選(收盤 / 還原收盤)"), ("financial", "③ 財報候選")):
        md.append("## %s · %d" % (lab, len(rep[k])))
        for s in rep[k]:
            f = s["fit"]
            md.append("- %s · %s · 列 %s · 代號%s 日期%s 收盤%s 還原%s 名稱%s 市場%s · 欄 %s" % (Path(s["file"]).name, s["ext"], s["rows"], *("✓" if f[x] else "✗" for x in ("ticker", "date", "close", "adj", "name", "market")), ", ".join((s["columns"] or [c for t in s["tables"] for c in t["columns"]])[:12])))
        md.append("")
    (out_dir / "VRN2_VDFBridge_Probe_latest.md").write_text("\n".join(md), encoding="utf-8")
    return rep


def selftest() -> int:
    ok = 0
    t = ticker_forms("2330"); a = t["bloomberg"] == "2330 TT" and t["status"].startswith("缺市場別")
    t2 = ticker_forms("8358.TWO"); b = t2["yfinance"] == "8358.TWO" and t2["base"] == "8358"
    t3 = ticker_forms("2330 TT", "TWSE"); c = t3["yfinance"] == "2330.TW"
    d = ticker_forms("0050")["status"] == "不合三種形式"
    e = first4_check("20250819兆豐個股報告-泓德能源(6873).pdf", "6873.TW")[0] == "GREEN" and first4_check("GS-2317 20251205.pdf", "2330")[0] == "RED"
    for cond, name in ((a, "基礎 → Bloomberg 必填 · yfinance 缺市場"), (b, "yfinance 反推基礎"), (c, "Bloomberg + 市場 → yfinance"), (d, "ETF 0050 不在範圍"), (e, "前四碼原則:年份不誤認 · 不符判紅")):
        print("  [%s] %s" % ("OK" if cond else "FAIL", name)); ok += int(cond)
    import tempfile
    td = Path(tempfile.mkdtemp()); (td / "vdf_database").mkdir()
    try:
        import pandas as pd
        pd.DataFrame({"ticker": ["2330", "8358"], "name": ["台積電", "同開"], "market": ["TWSE", "TPEX"]}).to_parquet(td / "vdf_database" / "VDF_TW_Listing.parquet")
        pd.DataFrame({"trade_date": ["2025-08-18"], "series_id": ["2330.TW__Close"], "px_value": [1130.0]}).to_parquet(td / "vdf_database" / "VDF_TW_PriceDaily_Long.parquet")
        rep = probe(td, td / "vdf_database", td / "out")
        f = len(rep["listing"]) == 1 and len(rep["price"]) == 1 and rep["price"][0]["fit"]["close"]
    except Exception as exc:  # noqa: BLE001
        f = False; print("  探測合成資料失敗", type(exc).__name__)
    print("  [%s] 探測分類:清單 / 日線各 1" % ("OK" if f else "FAIL")); ok += int(f)
    print("[計] VRN2_VDFBridge %s 自測 %d/6 · %s" % (VERSION, ok, "PASS" if ok == 6 else "FAIL"))
    return 0 if ok == 6 else 1


def main(argv: list) -> int:
    if "--selftest" in argv:
        return selftest()
    if "--probe" in argv:
        root = Path(argv[argv.index("--root") + 1]) if "--root" in argv else Path(__file__).resolve().parents[2]
        dh = Path(argv[argv.index("--data-home") + 1]) if "--data-home" in argv else Path(os.environ.get("USERPROFILE", str(Path.home()))) / "OneDrive" / "Documents" / "VeritasIntelligenceAnalytics" / "via_database" / "vdf_database"
        out = Path(argv[argv.index("--out") + 1]) if "--out" in argv else root / "VIA_Reports" / "vrn2" / "vdf_bridge"
        rep = probe(root, dh, out)
        print("[計] VDF 橋探測 · 掃 %d 檔 · 根存在 %d/%d · 入口 JSON %s · 清單候選 %d · 日線候選 %d · 財報候選 %d · 報告 %s" % (
            rep["scanned"], len(rep["roots_exist"]), len(rep["roots"]), "有" if rep["entrypoint"] else "無", len(rep["listing"]), len(rep["price"]), len(rep["financial"]), out / "VRN2_VDFBridge_Probe_latest.md"))
        for k in ("listing", "price", "financial"):
            for s in rep[k][:3]:
                print("[計]   %s · %s · 欄 %s" % (k, Path(s["file"]).name, ", ".join((s["columns"] or [c for t in s["tables"] for c in t["columns"]])[:8])))
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
