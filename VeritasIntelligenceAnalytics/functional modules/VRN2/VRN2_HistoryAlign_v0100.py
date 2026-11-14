#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VRN2_HistoryAlign v0100 — 歷史數據對齊 · 歷史覆蓋預估 · 加減乘除檢驗 · 刪除區(操作員 2026-10-29)。

操作員令:「一定要擷取歷史資料去做數字對齊 至少有一期要對 然後歷史覆蓋預估 加減法 乘除法檢驗數字 被歷史數據刪掉的部分放刪除區」。

輸入(只讀 · 一個位元組都不改):
  VIA_Reports/vrn2/output/VRN2_FinancialData_latest.json   VRN-2 年度數據冊(REPORT_DATE · FILENAME · TICKER · ITEM · PERIOD · VALUE · PAGE · TABLE · SECTION …)
  VIA_Reports/vrn2/market/VRN2_Market_latest.json          ⑥e 市場擷取(共用 VRN2_MarketFetch --fill)的 per_file[檔名].financial_annual[{year, std, value, unit, basis}](MOPS / TWSE 歷史年度財報)
規則:
  ① 科目對應:報告 ITEM → 標準科目(revenue · gross_profit · operating_income · pretax · net_income · eps · equity · dps · cogs · tax;同義字表 · 比率列(% / 率 / margin / 倍)不算金額)。
  ② 期間:只對年度(2023A · 2024 · Dec-24A · FY24 · 12/25 · 2025E/F/CT);季度(1Q24 · Mar-24)不對。A = 實際 · E / F / CT = 預估 · 沒標 = 未知。
  ③ 單位自動對:報告金額未知單位 × 倍率 s ∈ {1, 1000, 0.001, 1e6, 1e-6} → 與歷史(換成百萬台幣)比,0.97 ≤ 比值 ≤ 1.03 算對上;取對上最多的倍率(同票取 1)。
     每股(EPS / DPS)倍率固定 1。**至少一期對上**(金額或 EPS)這份報告才進入覆蓋;一期都沒對上 → 不覆蓋、黃燈、照實說。
  ④ 歷史覆蓋預估:對上的報告,凡歷史有 (科目, 年度) 的格 → VALUE_FINAL = 歷史(百萬台幣 / 元)· VALUE_SOURCE = HISTORY(MOPS / TWSE);報告原值留在 VALUE_REPORT;
     報告值與歷史差 > 3%(比值在 0.97 ~ 1.03 之外)→ 這列的報告值進刪除區 Deleted(DELETED_REASON · HISTORY_VALUE),對齊冊放歷史值。
     沒有歷史的年度(預估 / 未來)→ VALUE_FINAL = 報告值 × 倍率(百萬台幣)· VALUE_SOURCE = REPORT(估)。
  ⑤ 加減法 / 乘除法檢驗(每份每年度 · 用 VALUE_FINAL):毛利 = 營收 − 營業成本 · 稅前 − 所得稅 = 稅後 · 營業利益 ≤ 毛利;
     毛利率 / 營益率 / 淨利率列 = 對應比 × 100(容忍 1 個百分點)· ROE 列 ≈ 淨利 / 權益(容忍 3 點)· 營收成長率列 = 營收 ÷ 前一年 − 1(容忍 1 點)。只報不改。
輸出(只增):
  output/VRN2_FinancialAligned_latest.json / .csv(/ .parquet · 有 pyarrow 才寫)  每列 = 原冊欄位 + VALUE_REPORT · VALUE_FINAL · UNIT_FINAL · VALUE_SOURCE · RECON_RATIO · RECON_DIFF · SCALE · STD · YEAR · KIND
  output/VRN2_Deleted_latest.json / .csv                                           刪除區(被歷史數據否定的報告值 · 帶理由與歷史值)
  VIA_Reports/vrn2/VRN2_HistoryAlign_latest.json                                   收據(lamp · files{檔名: matched_periods · scale · overrides · deleted · checks} · totals)
動詞:align --root <VIA 根> [--fin <冊>] [--market <json>] [--out <輸出夾>] · --selftest
[VIA:AST-CLASS] 類別 = 資料對齊引擎(VRN-2)· 入口 = ActivateVRN-2 ⑬b / 本檔 CLI
"""
from __future__ import annotations

import csv
import datetime as _dt
import json
import os
import re
import sys
import tempfile
from pathlib import Path

VERSION = "v0100"
DISPLAY_NAME = "VRN2_HistoryAlign"
TAG = "歷史對齊 v0100"
TOL_LO, TOL_HI = 0.97, 1.03
SCALES = (1.0, 1000.0, 0.001, 1e6, 1e-6)
SCALE_LABEL = {1.0: "×1(報告已是百萬)", 1000.0: "×1000(報告為十億)", 0.001: "÷1000(報告為千元)", 1e6: "×1,000,000", 1e-6: "÷1,000,000(報告為元)"}
MONEY = ("revenue", "gross_profit", "operating_income", "pretax", "net_income", "equity", "cogs", "tax", "ebitda", "total_assets")
PER_SHARE = ("eps", "dps", "bvps")
SYN = {
    "revenue": ("營收", "營業收入", "營業收入淨額", "營業收入合計", "淨營收", "revenue", "revenues", "net sales", "sales", "total revenue", "turnover", "net revenue"),
    "cogs": ("營業成本", "銷貨成本", "cogs", "cost of goods sold", "cost of sales", "cost of revenue"),
    "gross_profit": ("毛利", "營業毛利", "gross profit", "gross income"),
    "operating_income": ("營業利益", "營業利益(損失)", "營益", "營業淨利", "operating income", "operating profit", "op. income", "op income", "op profit", "ebit"),
    "ebitda": ("ebitda",),
    "pretax": ("稅前純益", "稅前淨利", "稅前利益", "稅前盈餘", "profit before tax", "pre-tax profit", "pretax profit", "pretax income", "pbt", "income before tax"),
    "tax": ("所得稅", "所得稅費用", "income tax", "tax expense", "taxes", "tax"),
    "net_income": ("稅後淨利", "本期淨利", "淨利", "稅後純益", "稅後盈餘", "歸屬母公司淨利", "母公司淨利", "net income", "net profit", "net earnings", "profit after tax", "ni", "net income attributable", "reported net profit"),
    "eps": ("每股盈餘", "每股盈餘 (元)", "每股盈餘 (nt$)", "eps", "eps (nt$)", "eps (nt$) ", "diluted eps", "eps (diluted)", "reported eps", "每股淨利", "每股稅後盈餘"),
    "dps": ("現金股利", "每股現金股利", "每股股利", "dps", "dividend per share", "cash dividend", "dps (nt$)"),
    "equity": ("股東權益", "權益總額", "權益總計", "淨值", "股東權益總額", "shareholders' equity", "shareholders equity", "total equity", "equity", "book value"),
    "total_assets": ("資產總額", "資產總計", "total assets"),
    "bvps": ("每股淨值", "bvps", "book value per share"),
}
RATIO_ROWS = {"gross_margin": ("毛利率", "gross margin", "gm", "gm (%)"), "op_margin": ("營益率", "營業利益率", "營利率", "operating margin", "opm", "op margin"), "net_margin": ("淨利率", "net margin", "nm", "net profit margin"),
              "roe": ("roe", "roe (%)", "股東權益報酬率"), "rev_growth": ("營收成長率", "營收成長", "revenue growth", "sales growth", "revenue yoy", "yoy growth")}
HIST_STD = {"revenue": "revenue", "operating_income": "operating_income", "net_income": "net_income", "eps_diluted": "eps", "eps_basic": "eps_basic", "equity": "equity", "dps_cash": "dps"}
_PERIOD = re.compile(r"^(?:FY|Dec[-\s]?|12/)?\s*(20\d{2}|\d{2})\s*([A-Za-z]{0,2})$", re.I)
_QUARTER = re.compile(r"(^[1-4]Q|Q[1-4]|Mar|Jun|Sep|Sept|[36]/|9/|1H|2H|H[12])", re.I)


def say(line: str) -> None:
    try:
        print(line, flush=True)
    except UnicodeEncodeError:
        print(line.encode("utf-8", "replace").decode("ascii", "replace"), flush=True)


def now() -> str:
    return _dt.datetime.now().isoformat(timespec="seconds")


def _norm(text) -> str:
    return re.sub(r"\s+", " ", str(text or "").strip().lower()).replace("（", "(").replace("）", ")")


def std_of(item) -> str:
    """報告 ITEM → 標準科目;比率 / 百分比 / 倍數列回 ''(不是金額)。同義字先長後短、整字比對優先、再含字比對。"""
    t = _norm(item)
    if not t:
        return ""
    base = re.sub(r"\((?:nt\$|ntd|twd|us\$|usd|rmb|hk\$|bn|mn|m|k|thousand|million|billion|元|百萬|千元|十億|十億元|百萬元|仟元|\s|,)+\)", "", t).strip()
    if re.search(r"%|率|margin|growth|yoy|qoq|\(x\)|倍|ratio|yield|turnover days|days", base) and base not in ("turnover",):
        return ""
    for std, names in SYN.items():
        for n in sorted(names, key=len, reverse=True):
            if base == n or t == n:
                return std
    for std, names in SYN.items():
        for n in sorted(names, key=len, reverse=True):
            if len(n) >= 3 and (base.startswith(n + " ") or base.endswith(" " + n) or (n in base and not re.search(r"[a-z]", n))):
                if std in ("eps", "dps", "bvps") or std in MONEY:
                    return std
    return ""


def ratio_of(item) -> str:
    t = _norm(item)
    base = re.sub(r"\((?:%|x)\)", "", t).strip()
    for key, names in RATIO_ROWS.items():
        for n in sorted(names, key=len, reverse=True):
            if base == n or t == n or base.startswith(n + " "):
                return key
    return ""


def period_of(text) -> tuple:
    """期間字 → (年度, 類別 A / E / ?);季度或看不懂 → (None, '')。"""
    s = str(text or "").strip()
    if not s or _QUARTER.search(s):
        return None, ""
    m = _PERIOD.match(s)
    if not m:
        return None, ""
    y = int(m.group(1))
    y = y + 2000 if y < 100 else y
    suf = m.group(2).upper()
    kind = "A" if suf == "A" else ("E" if suf in ("E", "F", "CT", "P", "C") else "?")
    return y, kind


def num(value):
    s = str(value if value is not None else "").strip()
    if not s or s.lower() in ("n.a.", "na", "n/a", "nm", "-", "—", "nil", "none"):
        return None
    neg = s.startswith("(") and s.endswith(")") or s.startswith("-") or s.startswith("−")
    s = re.sub(r"[(),%\s]|x$|倍$|^nt\$|^twd|^\$|^-|^−", "", s, flags=re.I)
    if not re.fullmatch(r"\d+(\.\d+)?", s):
        return None
    v = float(s)
    return -v if neg else v


def hist_to_mn(value, unit) -> float | None:
    """歷史值 → 百萬台幣(千元 ÷ 1000 · 元 ÷ 1e6 · 百萬 ×1 · 沒標 → 視為 MOPS 千元)。"""
    if value is None:
        return None
    u = _norm(unit)
    if "百萬" in u or "million" in u or u in ("mn", "m"):
        return float(value)
    if "千" in u or "thousand" in u or u in ("k", "000"):
        return float(value) / 1000.0
    if u in ("元", "ntd", "twd", "nt$") or "dollar" in u:
        return float(value) / 1e6
    return float(value) / 1000.0


def history_of(market: dict, filename: str) -> tuple:
    """market per_file[檔名].financial_annual → {(std, year): 值(金額百萬 · 每股元)} + 有沒有歷史。"""
    rec = (market.get("per_file") or {}).get(filename) or {}
    fa = rec.get("financial_annual") or []
    out = {}
    for x in fa:
        std = HIST_STD.get(str(x.get("std")), "")
        if not std or x.get("value") is None:
            continue
        y = int(x.get("year"))
        if std in ("eps", "eps_basic", "dps"):
            v = float(x["value"])
            key = "eps" if std in ("eps", "eps_basic") else std
            if key == "eps" and std == "eps_basic" and ("eps", y) in out:
                continue
            out[(key, y)] = v
        else:
            out[(std, y)] = hist_to_mn(x["value"], x.get("unit"))
    return out, bool(fa)


def pick_scale(pairs: list) -> tuple:
    """pairs = [(報告值, 歷史百萬)] → (倍率, 對上數)。沒有一對 → (None, 0)。"""
    best, best_n = None, 0
    for s in SCALES:
        n = sum(1 for r, h in pairs if h and r is not None and TOL_LO <= (r * s) / h <= TOL_HI)
        if n > best_n:
            best, best_n = s, n
    return best, best_n


def _out_row(row: dict, extra: dict) -> dict:
    r = {k: v for k, v in row.items() if not str(k).startswith("_")}
    r.update(extra)
    return r


def align_file(rows: list, hist: dict, has_hist: bool) -> dict:
    """一份報告:對單位 → 覆蓋 → 刪除區 → 檢驗。回 {aligned, deleted, receipt}。"""
    parsed = []
    for row in rows:
        std = std_of(row.get("ITEM"))
        y, kind = period_of(row.get("PERIOD"))
        parsed.append((row, std, y, kind, num(row.get("VALUE")), ratio_of(row.get("ITEM"))))
    money_pairs = [(v, hist.get((std, y))) for row, std, y, kind, v, _ in parsed if std in MONEY and y and kind != "E" and v is not None and hist.get((std, y))]
    eps_pairs = [(v, hist.get((std, y))) for row, std, y, kind, v, _ in parsed if std in PER_SHARE and y and kind != "E" and v is not None and hist.get((std, y))]
    scale, n_money = pick_scale(money_pairs)
    n_eps = sum(1 for r, h in eps_pairs if h and TOL_LO <= r / h <= TOL_HI)
    matched = n_money + n_eps
    receipt = {"rows": len(rows), "has_history": has_hist, "history_cells": len(hist), "matched_periods": matched, "matched_money": n_money, "matched_per_share": n_eps,
               "scale": scale, "scale_label": SCALE_LABEL.get(scale, "—") if scale else ("未定(只有每股對上)" if matched else "—"), "overrides": 0, "deleted": 0, "checks": [], "checks_pass": "—"}
    aligned, deleted = [], []
    if not has_hist:
        receipt.update(lamp="GRAY", why="沒有歷史資料(⑥e 市場擷取沒有這份的年度財報)· 不覆蓋 · 報告值照原冊")
    elif matched == 0:
        receipt.update(lamp="YELLOW", why="沒有一期對上(金額 %d 對 · 每股 %d 對 · 歷史格 %d)· 不覆蓋 · 報告值照原冊" % (len(money_pairs), len(eps_pairs), len(hist)))
    else:
        receipt.update(lamp="GREEN", why="對上 %d 期(金額 %d · 每股 %d)· 倍率 %s" % (matched, n_money, n_eps, receipt["scale_label"]))
    overriding = receipt["lamp"] == "GREEN"
    final = {}
    for row, std, y, kind, v, ratio_key in parsed:
        is_money = std in MONEY
        is_ps = std in PER_SHARE
        s = scale if (is_money and scale) else 1.0
        h = hist.get((std, y)) if (std and y) else None
        extra = {"STD": std, "YEAR": y, "KIND": kind, "SCALE": s if is_money else 1.0, "VALUE_REPORT": row.get("VALUE"), "RECON_RATIO": None, "RECON_DIFF": None}
        unit = "百萬台幣" if (is_money and scale) else ("元/股" if is_ps else ("%" if (ratio_key or re.search(r"%|率|margin", _norm(row.get("ITEM")))) else "原單位"))
        if overriding and h is not None and (is_money and scale or is_ps):
            ratio = (v * s) / h if (v is not None and h) else None
            extra.update(VALUE_FINAL=round(h, 6), UNIT_FINAL=unit, VALUE_SOURCE="HISTORY(MOPS / TWSE)", RECON_RATIO=round(ratio, 6) if ratio is not None else None, RECON_DIFF=round(v * s - h, 6) if v is not None else None)
            receipt["overrides"] += 1
            if v is not None and ratio is not None and not (TOL_LO <= ratio <= TOL_HI):
                deleted.append(_out_row(row, {"STD": std, "YEAR": y, "HISTORY_VALUE": round(h, 6), "UNIT_HISTORY": unit, "SCALE": s, "RECON_RATIO": round(ratio, 6), "DELETED_REASON": "與歷史數據差 > 3%%(報告 %s × %s = %s · 歷史 %s · 比值 %.4f)→ 歷史覆蓋" % (row.get("VALUE"), s, round(v * s, 4), round(h, 4), ratio)}))
                extra["VALUE_SOURCE"] = "HISTORY(覆蓋 · 報告值進刪除區)"
                receipt["deleted"] += 1
        else:
            if v is not None and (is_money and scale):
                extra.update(VALUE_FINAL=round(v * s, 6), UNIT_FINAL=unit, VALUE_SOURCE=_source(kind, y, v, has_hist, overriding))
            else:
                extra.update(VALUE_FINAL=v if v is not None else row.get("VALUE"), UNIT_FINAL=unit, VALUE_SOURCE=_source(kind, y, v, has_hist, overriding))
        out = _out_row(row, extra)
        aligned.append(out)
        if y and v is not None:
            key = (std or ("ratio:" + ratio_key if ratio_key else ""), y)
            if key[0] and key not in final:
                final[key] = out["VALUE_FINAL"] if isinstance(out["VALUE_FINAL"], (int, float)) else v
    receipt["checks"] = checks(final)
    n_ok = sum(1 for c in receipt["checks"] if c["verdict"] == "PASS")
    receipt["checks_pass"] = "%d/%d" % (n_ok, len(receipt["checks"])) if receipt["checks"] else "—"
    return {"aligned": aligned, "deleted": deleted, "receipt": receipt}


def _source(kind: str, year, value, has_hist: bool, overriding: bool) -> str:
    """報告值的來源標記:非數值 · 非年度(季度)· 預估 · 對上的報告沒這格歷史 · 有歷史但一期都沒對上 · 沒歷史。"""
    if value is None:
        return "REPORT(非數值)"
    if year is None:
        return "REPORT(非年度 · 不對歷史)"
    if kind == "E":
        return "REPORT(估)"
    if overriding:
        return "REPORT(無歷史)"
    return "REPORT(未對齊)" if has_hist else "REPORT"


def checks(final: dict) -> list:
    """加減法 / 乘除法:只報不改。final = {(std 或 ratio:key, 年度): VALUE_FINAL}。"""
    out = []
    years = sorted({y for _, y in final})

    def g(k, y):
        return final.get((k, y))

    def add(y, name, lhs, rhs, tol, kind):
        if lhs is None or rhs is None:
            return
        ok = abs(lhs - rhs) <= tol
        out.append({"year": y, "check": name, "kind": kind, "lhs": round(lhs, 4), "rhs": round(rhs, 4), "tolerance": tol, "verdict": "PASS" if ok else "FAIL"})

    for y in years:
        rev, cogs, gp, oi, pbt, tax, ni, eq = (g(k, y) for k in ("revenue", "cogs", "gross_profit", "operating_income", "pretax", "tax", "net_income", "equity"))
        if rev is not None and cogs is not None and gp is not None:
            add(y, "加減法 毛利 = 營收 − 營業成本", gp, rev - cogs, max(1.0, abs(rev) * 0.01), "add_sub")
        if pbt is not None and tax is not None and ni is not None:
            add(y, "加減法 稅後 = 稅前 − 所得稅", ni, pbt - abs(tax), max(1.0, abs(pbt) * 0.02), "add_sub")
        if gp is not None and oi is not None:
            out.append({"year": y, "check": "加減法 營業利益 ≤ 毛利", "kind": "add_sub", "lhs": round(oi, 4), "rhs": round(gp, 4), "tolerance": 0, "verdict": "PASS" if oi <= gp + max(1.0, abs(gp) * 0.001) else "FAIL"})
        for key, numer, label in (("gross_margin", gp, "毛利率 = 毛利 ÷ 營收"), ("op_margin", oi, "營益率 = 營業利益 ÷ 營收"), ("net_margin", ni, "淨利率 = 淨利 ÷ 營收")):
            r = g("ratio:" + key, y)
            if r is not None and numer is not None and rev:
                add(y, "乘除法 " + label, r, numer / rev * 100.0, 1.0, "mul_div")
        roe = g("ratio:roe", y)
        if roe is not None and ni is not None and eq:
            add(y, "乘除法 ROE ≈ 淨利 ÷ 權益", roe, ni / eq * 100.0, 3.0, "mul_div")
        gr = g("ratio:rev_growth", y)
        rev0 = g("revenue", y - 1)
        if gr is not None and rev is not None and rev0:
            add(y, "乘除法 營收成長率 = 營收 ÷ 前一年 − 1", gr, (rev / rev0 - 1.0) * 100.0, 1.0, "mul_div")
    return out


def _write_books(out_dir: Path, aligned: list, deleted: list) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    written = {}
    for name, rows in (("FinancialAligned", aligned), ("Deleted", deleted)):
        jp = out_dir / ("VRN2_%s_latest.json" % name)
        tmp = jp.with_suffix(".tmp")
        tmp.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
        tmp.replace(jp)
        cols = []
        for r in rows:
            for k in r:
                if k not in cols:
                    cols.append(k)
        cp = out_dir / ("VRN2_%s_latest.csv" % name)
        with cp.open("w", encoding="utf-8-sig", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=cols)
            w.writeheader()
            for r in rows:
                w.writerow({k: ("" if r.get(k) is None else r.get(k)) for k in cols})
        written[name] = {"json": str(jp), "csv": str(cp), "rows": len(rows)}
        try:
            import pyarrow as pa  # noqa: WPS433
            import pyarrow.parquet as pq  # noqa: WPS433
            table = pa.Table.from_pylist([{k: ("" if r.get(k) is None else (r.get(k) if isinstance(r.get(k), (int, float, str)) else json.dumps(r.get(k), ensure_ascii=False))) for k in cols} for r in rows]) if rows else pa.table({c: pa.array([], pa.string()) for c in cols or ["FILENAME"]})
            pp = out_dir / ("VRN2_%s_latest.parquet" % name)
            pq.write_table(table, str(pp), compression="zstd")
            written[name]["parquet"] = str(pp)
        except Exception as error:  # noqa: BLE001
            written[name]["parquet"] = "(沒寫:%s)" % type(error).__name__
    return written


def align(root: Path, fin_path: Path | None = None, market_path: Path | None = None, out_dir: Path | None = None) -> dict:
    root = Path(root)
    v2 = root / "VIA_Reports" / "vrn2"
    fin_path = Path(fin_path) if fin_path else v2 / "output" / "VRN2_FinancialData_latest.json"
    market_path = Path(market_path) if market_path else v2 / "market" / "VRN2_Market_latest.json"
    out_dir = Path(out_dir) if out_dir else v2 / "output"
    rec = {"engine": "%s %s" % (DISPLAY_NAME, TAG), "verb": "align", "at": now(), "fin": str(fin_path), "market": str(market_path), "files": {}, "totals": {},
           "rule": "至少一期(金額 0.97 ~ 1.03 · 倍率自動 · 每股 ×1)對上才覆蓋;歷史覆蓋預估;差 > 3% 的報告值進刪除區;加減 / 乘除檢驗只報不改"}
    if not fin_path.is_file():
        rec.update(lamp="GRAY", why="沒有年度數據冊 %s" % fin_path.name)
        return _finish(v2, rec)
    try:
        rows = json.loads(fin_path.read_text(encoding="utf-8"))
    except Exception as error:  # noqa: BLE001
        rec.update(lamp="RED", why="年度數據冊讀不了:%s: %s" % (type(error).__name__, str(error)[:120]))
        return _finish(v2, rec)
    market = {}
    if market_path.is_file():
        try:
            market = json.loads(market_path.read_text(encoding="utf-8"))
        except Exception as error:  # noqa: BLE001
            rec.update(lamp="YELLOW", why="市場資料讀不了:%s" % type(error).__name__)
    if not market:
        rec.update(lamp="GRAY", why="沒有市場資料 %s(⑥e 沒跑或沒抓到)· 不覆蓋" % market_path.name, totals={"files": len({r.get("FILENAME") for r in rows if isinstance(r, dict)}), "files_matched": 0, "files_unmatched": 0, "files_no_history": 0, "overrides": 0, "deleted": 0})
        return _finish(v2, rec)
    by_file = {}
    for r in rows:
        if isinstance(r, dict):
            by_file.setdefault(str(r.get("FILENAME") or ""), []).append(r)
    aligned_all, deleted_all = [], []
    t = {"files": len(by_file), "files_matched": 0, "files_unmatched": 0, "files_no_history": 0, "overrides": 0, "deleted": 0, "checks": 0, "checks_fail": 0}
    for name, frows in sorted(by_file.items()):
        hist, has_hist = history_of(market, name)
        res = align_file(frows, hist, has_hist)
        aligned_all += res["aligned"]
        deleted_all += res["deleted"]
        rc = res["receipt"]
        rec["files"][name] = rc
        t["overrides"] += rc["overrides"]
        t["deleted"] += rc["deleted"]
        t["checks"] += len(rc["checks"])
        t["checks_fail"] += sum(1 for c in rc["checks"] if c["verdict"] == "FAIL")
        t["files_matched" if rc["lamp"] == "GREEN" else ("files_no_history" if rc["lamp"] == "GRAY" else "files_unmatched")] += 1
    rec["totals"] = t
    rec["written"] = _write_books(out_dir, aligned_all, deleted_all)
    if t["files_matched"] and not t["files_unmatched"]:
        rec["lamp"] = "GREEN"
    elif t["files_matched"]:
        rec["lamp"] = "YELLOW"
    else:
        rec["lamp"] = "YELLOW" if t["files_unmatched"] else "GRAY"
    rec["why"] = "對上 %d · 沒對上 %d · 無歷史 %d(共 %d 份)· 覆蓋 %d 格 · 刪除區 %d 列 · 檢驗 %d(不過 %d)" % (t["files_matched"], t["files_unmatched"], t["files_no_history"], t["files"], t["overrides"], t["deleted"], t["checks"], t["checks_fail"])
    return _finish(v2, rec)


def _finish(v2: Path, rec: dict) -> dict:
    try:
        v2.mkdir(parents=True, exist_ok=True)
        p = v2 / "VRN2_HistoryAlign_latest.json"
        tmp = p.with_suffix(".tmp")
        tmp.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
        tmp.replace(p)
        rec["receipt"] = str(p)
    except OSError as error:
        rec["receipt_error"] = "%s: %s" % (type(error).__name__, error)
    return rec


# ===== selftest =====
def _fixture(root: Path) -> None:
    v2 = root / "VIA_Reports" / "vrn2"
    (v2 / "output").mkdir(parents=True)
    (v2 / "market").mkdir()
    A, B, C = "A-2330 20260101.pdf", "B-2454 20260102.pdf", "C-6669 20260103.pdf"
    fin = []

    def add(f, item, period, value, page=5):
        fin.append({"REPORT_DATE": "2026-01-0" + f[0].lower().replace("a", "1").replace("b", "2").replace("c", "3"), "FILENAME": f, "TICKER": f[2:6], "BROKER": f[0], "PAGE": page, "TABLE": "P5·F·01·TB", "ITEM": item, "PERIOD": period, "VALUE": value, "VERIFY": "VERIFIED", "ROW": 1, "SECTION": ""})
    # A:報告以十億為單位(bn)· 2024A / 2025A 實際 · 2026E 預估;淨利 2025A 報告值錯(差 > 3%)· EPS 對;毛利率 / 淨利率列
    for p, rev, cogs, gp, ni, eps, gm, nm in (("2024A", "2,000.0", "1,000.0", "1,000.0", "500.0", "19.30", "50.0%", "25.0%"), ("2025A", "2,894.3", "1,200.0", "1,694.3", "999.9", "45.25", "58.5%", "34.5%"), ("2026E", "3,500.0", "1,400.0", "2,100.0", "1,400.0", "54.00", "60.0%", "40.0%")):
        add(A, "Revenue (NT$ bn)", p, rev); add(A, "COGS", p, cogs); add(A, "Gross profit", p, gp); add(A, "Net income", p, ni); add(A, "EPS (NT$)", p, eps); add(A, "GM (%)", p, gm); add(A, "NM (%)", p, nm)
    add(A, "Revenue (NT$ bn)", "1Q24", "500.0")
    # B:報告值跟歷史完全對不上
    add(B, "營收", "2024A", "123,456"); add(B, "營收", "2025E", "150,000"); add(B, "每股盈餘 (元)", "2024A", "3.33")
    # C:沒有歷史
    add(C, "Revenue", "2024A", "88,000")
    json.dump(fin, open(v2 / "output" / "VRN2_FinancialData_latest.json", "w", encoding="utf-8"), ensure_ascii=False)
    market = {"version": "v0112", "ts": now(), "per_file": {
        A: {"ticker": "2330", "financial_annual": [{"year": 2024, "std": "revenue", "value": 2000123000.0, "unit": "千元", "basis": "ANNUAL"}, {"year": 2024, "std": "net_income", "value": 500050000.0, "unit": "千元", "basis": "ANNUAL"},
                                                   {"year": 2025, "std": "revenue", "value": 2894307699.0, "unit": "千元", "basis": "ANNUAL"}, {"year": 2025, "std": "net_income", "value": 1173268000.0, "unit": "千元", "basis": "ANNUAL"},
                                                   {"year": 2025, "std": "eps_diluted", "value": 45.25, "unit": "元", "basis": "ANNUAL"}, {"year": 2024, "std": "eps_diluted", "value": 19.30, "unit": "元", "basis": "ANNUAL"}]},
        B: {"ticker": "2454", "financial_annual": [{"year": 2024, "std": "revenue", "value": 999999999.0, "unit": "千元", "basis": "ANNUAL"}, {"year": 2024, "std": "eps_diluted", "value": 70.0, "unit": "元", "basis": "ANNUAL"}]},
        C: {"ticker": "6669", "financial_annual": []}}}
    json.dump(market, open(v2 / "market" / "VRN2_Market_latest.json", "w", encoding="utf-8"), ensure_ascii=False)


def selftest() -> int:
    bad = []

    def chk(label, cond):
        say(("[PASS] " if cond else "[FAIL] ") + label)
        if not cond:
            bad.append(label)

    chk("① 科目同義字:營收 / Revenue (NT$ bn) / Net income / 每股盈餘 (元) / 股東權益 → 標準科目;毛利率 / ROE (%) / P/E (x) 不是金額", std_of("營收") == "revenue" and std_of("Revenue (NT$ bn)") == "revenue" and std_of("Net income") == "net_income" and std_of("每股盈餘 (元)") == "eps" and std_of("Shareholders' equity") == "equity" and std_of("毛利率 (%)") == "" and std_of("ROE (%)") == "" and std_of("P/E (x)") == "" and ratio_of("淨利率 (%)") == "net_margin" and ratio_of("ROE (%)") == "roe")
    chk("② 期間:2023A → A · 2025E / 2027F / 2025CT → E · 2024 → ? · Dec-24A / FY24 / 12/25 → 年度;1Q24 / Mar-24 → 不對", period_of("2023A") == (2023, "A") and period_of("2025E")[1] == "E" and period_of("2027F") == (2027, "E") and period_of("2025CT") == (2025, "E") and period_of("2024") == (2024, "?") and period_of("Dec-24A") == (2024, "A") and period_of("FY24") == (2024, "?") and period_of("12/25") == (2025, "?") and period_of("1Q24") == (None, "") and period_of("Mar-24") == (None, ""))
    chk("③ 數字:(1,234) 負 · 28.9% · 18.2x · n.a. → None", num("(1,234)") == -1234.0 and num("28.9%") == 28.9 and num("18.2x") == 18.2 and num("n.a.") is None and num("") is None)
    chk("④ 歷史單位:千元 ÷ 1000 · 元 ÷ 1e6 · 百萬 ×1 · 沒標 = 千元", hist_to_mn(2894307699.0, "千元") == 2894307.699 and hist_to_mn(5e6, "元") == 5.0 and hist_to_mn(7.5, "百萬") == 7.5 and hist_to_mn(1000.0, None) == 1.0)
    chk("⑤ 倍率:報告 bn 對歷史百萬 → ×1000 · 對上 2", pick_scale([(2894.3, 2894307.699), (2000.0, 2000123.0), (999.9, 1173268.0)]) == (1000.0, 2))
    with tempfile.TemporaryDirectory(prefix="vrn2-hist-") as td:
        root = Path(td)
        _fixture(root)
        r = align(root)
        fa, fb, fc = (r["files"][n] for n in ("A-2330 20260101.pdf", "B-2454 20260102.pdf", "C-6669 20260103.pdf"))
        chk("⑥ A 對上:倍率 ×1000 · 金額 3 期(2024 營收 / 淨利 · 2025 營收)+ EPS 2 期 · 綠", fa["lamp"] == "GREEN" and fa["scale"] == 1000.0 and fa["matched_money"] == 3 and fa["matched_per_share"] == 2 and fa["matched_periods"] == 5)
        al = json.loads((root / "VIA_Reports" / "vrn2" / "output" / "VRN2_FinancialAligned_latest.json").read_text(encoding="utf-8"))
        de = json.loads((root / "VIA_Reports" / "vrn2" / "output" / "VRN2_Deleted_latest.json").read_text(encoding="utf-8"))
        a_ni25 = next(x for x in al if x["FILENAME"].startswith("A-") and x["STD"] == "net_income" and x["YEAR"] == 2025)
        a_rev26 = next(x for x in al if x["FILENAME"].startswith("A-") and x["STD"] == "revenue" and x["YEAR"] == 2026)
        a_rev25 = next(x for x in al if x["FILENAME"].startswith("A-") and x["STD"] == "revenue" and x["YEAR"] == 2025)
        a_q = next(x for x in al if x["FILENAME"].startswith("A-") and x["PERIOD"] == "1Q24")
        chk("⑦ 歷史覆蓋:2025A 營收 VALUE_FINAL = 歷史 2,894,307.699 百萬 · VALUE_REPORT 留 2,894.3 · 比值 1.0 · 來源 HISTORY", a_rev25["VALUE_FINAL"] == 2894307.699 and a_rev25["VALUE_REPORT"] == "2,894.3" and abs(a_rev25["RECON_RATIO"] - 1.0) < 1e-4 and a_rev25["VALUE_SOURCE"].startswith("HISTORY") and a_rev25["UNIT_FINAL"] == "百萬台幣")
        chk("⑧ 刪除區:2025A 淨利報告 999.9 bn vs 歷史 1,173,268 百萬(比值 0.85)→ Deleted 1 列帶理由 · 對齊冊放歷史值 · 來源註明進刪除區", len(de) == 1 and de[0]["STD"] == "net_income" and de[0]["YEAR"] == 2025 and "差 > 3%" in de[0]["DELETED_REASON"] and de[0]["HISTORY_VALUE"] == 1173268.0 and a_ni25["VALUE_FINAL"] == 1173268.0 and "刪除區" in a_ni25["VALUE_SOURCE"] and fa["deleted"] == 1)
        chk("⑨ 預估保留:2026E 營收 = 3,500 × 1000 = 3,500,000 百萬 · 來源 REPORT(估);季度列不對(KIND 空 · 原單位照算)", a_rev26["VALUE_FINAL"] == 3500000.0 and a_rev26["VALUE_SOURCE"] == "REPORT(估)" and a_q["YEAR"] is None and a_q["VALUE_SOURCE"] == "REPORT(非年度 · 不對歷史)")
        cks = fa["checks"]
        gp24 = next(c for c in cks if c["year"] == 2024 and "毛利 = 營收" in c["check"])
        nm25 = next(c for c in cks if c["year"] == 2025 and "淨利率" in c["check"])
        gm25 = next(c for c in cks if c["year"] == 2025 and "毛利率" in c["check"])
        chk("⑩ 檢驗:2024 毛利 = 營收 − 成本 PASS · 2025 淨利率 34.5 vs 歷史淨利 / 營收 40.5 → FAIL · 2025 毛利率 58.5 PASS · checks_pass 字串", gp24["verdict"] == "PASS" and nm25["verdict"] == "FAIL" and gm25["verdict"] == "PASS" and re.fullmatch(r"\d+/\d+", fa["checks_pass"]))
        chk("⑪ B 沒有一期對上 → 黃 · 不覆蓋 · 報告值照原冊(VALUE_SOURCE REPORT(未對齊))· C 沒歷史 → 灰", fb["lamp"] == "YELLOW" and fb["overrides"] == 0 and "沒有一期對上" in fb["why"] and next(x for x in al if x["FILENAME"].startswith("B-") and x["PERIOD"] == "2024A")["VALUE_SOURCE"] == "REPORT(未對齊)" and fc["lamp"] == "GRAY" and "沒有歷史資料" in fc["why"])
        chk("⑫ 總表:對上 1 · 沒對上 1 · 無歷史 1 · 整體黃 · 收據 + csv 寫出 · 原冊沒動", r["lamp"] == "YELLOW" and r["totals"]["files_matched"] == 1 and r["totals"]["files_unmatched"] == 1 and r["totals"]["files_no_history"] == 1 and (root / "VIA_Reports" / "vrn2" / "VRN2_HistoryAlign_latest.json").is_file() and (root / "VIA_Reports" / "vrn2" / "output" / "VRN2_Deleted_latest.csv").is_file() and len(json.loads((root / "VIA_Reports" / "vrn2" / "output" / "VRN2_FinancialData_latest.json").read_text(encoding="utf-8"))) == 26)
        (root / "VIA_Reports" / "vrn2" / "market" / "VRN2_Market_latest.json").unlink()
        r2 = align(root)
        chk("⑬ 沒有市場資料 → 灰 · 不覆蓋 · 收據照寫", r2["lamp"] == "GRAY" and "沒有市場資料" in r2["why"])
        r3 = align(root / "nowhere")
        chk("⑭ 沒有年度數據冊 → 灰", r3["lamp"] == "GRAY" and "沒有年度數據冊" in r3["why"])
    say("[%s] %s %s --selftest · 14 項 · 不過 %d" % ("PASS" if not bad else "FAIL", DISPLAY_NAME, VERSION, len(bad)))
    return 0 if not bad else 1


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in argv:
        return selftest()

    def opt(k, d=None):
        return argv[argv.index(k) + 1] if k in argv and argv.index(k) + 1 < len(argv) else d
    if not argv or argv[0] != "align":
        say(__doc__)
        return 2
    root = Path(opt("--root") or os.environ.get("VIA_ROOT") or Path(__file__).resolve().parent.parent.parent)
    r = align(root, opt("--fin"), opt("--market"), opt("--out"))
    say("[%s] %s · %s" % (r.get("lamp"), TAG, r.get("why")))
    return 0 if r.get("lamp") in ("GREEN", "YELLOW", "GRAY") else 1


if __name__ == "__main__":
    sys.exit(main())
