#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VRN2_HistoryAlign v0102 — v0101 薄尾(v0101 / v0100 留著一字不改):科目對應只收「就是這個科目」的列 · 檢驗分得出「不過」和「口徑不明」。

桌機 2026-10-29 14:40 ⑬b「檢驗 534(不過 120)」、容器只修回合「檢驗 218(不過 85)」—— 逐筆看,不過的大多不是數字錯,是科目對錯列:
  · 「Other Revenue」(其他營收)被當成總營收 → 歷史覆蓋 / 淨利率 77.8% / 營收成長率都錯;「Sales growth of OEM business (%)」被當成營收成長率。
  · 「Taxes payable」(應付所得稅 · 資產負債表)被當成所得稅;「Total liabs & equity」「Minorities/other equity」被當成股東權益(ROE 算出 −5,381%)。
  · 報告把營業成本寫成負數「(176,457)」→ 營收 − 成本 = 營收 + 成本。
v0102:
  ① 金額 / 每股科目:先用 v0100 的同義字表對,再排除「其中一部分 / 別的口徑」的列 —— other / 其他 · segment / business / 部門 / 事業 · 「… of …」·
     payable / receivable / 應付 / 應收 · liab / 負債 · minority / non-controlling / 少數 / 非控制 · deferred / 遞延 · paid / cash / 現金 ·
     adjusted / core / recurring / normalised / pro forma / non-GAAP / 調整後 / 核心 / 經常性 · equity income / associates / 權益法 · return on / debt / to equity。
     排除的列 STD 空:不覆蓋、不進刪除區、不參與檢驗(照原冊)。
  ② 比率列(毛利率 · 營益率 · 淨利率 · ROE · 營收成長率)同樣排除部門 / 事業 / 「… of …」/ 其他 / 調整後。
  ③ 檢驗:營業成本取絕對值;ROE 用期末或(期初 + 期末)/ 2 的權益都算對;兩邊差到不像同一口徑(加減差 > 50% · 乘除差 3 倍以上或正負相反)
     → UNCLEAR(口徑不明 · 不算不過);收據 totals 多 checks_unclear,why 多「口徑不明 N」。
  ④ 其餘照 v0101(對上才覆蓋 · 別單位對上覆蓋不刪 · 同數量級才刪 · 口徑不明不動 · 成長 / % 段落當比率)。
動詞同 v0100:align --root <VIA 根> [--fin] [--market] [--out] · --selftest
"""
from __future__ import annotations

import importlib.util
import json
import re
import sys
import tempfile
from pathlib import Path

VERSION = "v0102"
DISPLAY_NAME = "VRN2_HistoryAlign"
TAG = "歷史對齊 v0102"
PRIOR_NAME = "VRN2_HistoryAlign_v0101.py"
HERE = Path(__file__).resolve().parent
_NOT_THIS = re.compile(r"\bother\b|其他|segment|business|部門|事業|業務|\bof\b|payable|receivable|應付|應收|liab|負債|minorit|non-?controlling|少數|非控制|deferred|遞延|"
                       r"\bpaid\b|\bcash\b|現金|adjusted|\badj\b|\badj\.|\bcore\b|recurring|normali[sz]ed|pro ?forma|non-?gaap|調整後|核心|經常性|"
                       r"equity income|equity-method|associates|權益法|投資收益|return on|\bdebt\b|to equity|/ ?equity", re.I)
_NOT_THIS_RATIO = re.compile(r"segment|business|部門|事業|\bof\b|\bother\b|其他|adjusted|\badj\b|\bcore\b|調整後|核心", re.I)
GROSS_ADD_SUB = 0.5          # 加減法兩邊差 > 50% → 口徑不明
GROSS_MUL_DIV = 3.0          # 乘除法差 3 倍以上(或正負相反)→ 口徑不明
MINORITY_GAP = 0.15          # 稅後與「稅前 − 所得稅」差在 15% 內 → 多半是少數股權 / 優先股股利那一列 → 口徑不明
SAME_VALUE = 0.001           # 同一年同科目的兩個值差 ≤ 0.1% 算同一個值(四捨五入)


def _prior():
    for path in (HERE / PRIOR_NAME, HERE.parent.parent / "v147" / "new" / PRIOR_NAME):
        if path.is_file():
            spec = importlib.util.spec_from_file_location("vrn2_historyalign_prior_v0101", path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)
            return module
    raise FileNotFoundError("前版 %s 不在 %s" % (PRIOR_NAME, HERE))


PRIOR = _prior()
BASE = PRIOR.PRIOR                       # v0100(v0101 的 align_file 透過它取 std_of / ratio_of / checks)
for _name in dir(PRIOR):
    if not _name.startswith("__") and _name not in globals():
        globals()[_name] = getattr(PRIOR, _name)
BASE.TAG = TAG
_native_std_of = BASE.std_of
_native_ratio_of = BASE.ratio_of


def std_of(item) -> str:
    std = _native_std_of(item)
    if std and _NOT_THIS.search(BASE._norm(item)):
        return ""
    return std


def ratio_of(item) -> str:
    key = _native_ratio_of(item)
    if key and _NOT_THIS_RATIO.search(BASE._norm(item)):
        return ""
    return key


def _gross(lhs: float, rhs: float, kind: str) -> bool:
    if kind == "add_sub":
        return abs(lhs - rhs) > GROSS_ADD_SUB * max(abs(lhs), abs(rhs), 1.0)
    if lhs == 0 or rhs == 0:
        return abs(lhs - rhs) > 1.0
    if (lhs > 0) != (rhs > 0):
        return True
    big, small = max(abs(lhs), abs(rhs)), min(abs(lhs), abs(rhs))
    return big / small >= GROSS_MUL_DIV


def checks(final: dict) -> list:
    """加減法 / 乘除法:只報不改 · 成本取絕對值 · ROE 期末或平均權益 · 差到不像同口徑 → UNCLEAR。"""
    out = []
    years = sorted({y for _, y in final})

    def g(k, y):
        return final.get((k, y))

    def add(y, name, lhs, rhs, tol, kind, alt=None, minority=False):
        if lhs is None or rhs is None:
            return
        ok = abs(lhs - rhs) <= tol or (alt is not None and abs(lhs - alt) <= tol)
        verdict = "PASS" if ok else ("UNCLEAR" if _gross(lhs, rhs, kind) else "FAIL")
        note = "兩邊差到不像同一口徑(多半是科目列不是同一個口徑)· 不算不過" if verdict == "UNCLEAR" else ""
        if verdict == "FAIL" and minority and abs(rhs - lhs) <= MINORITY_GAP * max(abs(rhs), 1.0):
            verdict, note = "UNCLEAR", "稅後與「稅前 − 所得稅」差 %.1f%%(在 %d%% 內 · 多半是少數股權 / 優先股股利 / 非常損益那一列)· 不算不過" % (abs(rhs - lhs) / max(abs(rhs), 1.0) * 100, MINORITY_GAP * 100)
        item = {"year": y, "check": name, "kind": kind, "lhs": round(lhs, 4), "rhs": round(rhs, 4), "tolerance": tol, "verdict": verdict}
        if alt is not None:
            item["rhs_alt"] = round(alt, 4)
        if note:
            item["note"] = note
        out.append(item)

    for y in years:
        rev, cogs, gp, oi, pbt, tax, ni, eq = (g(k, y) for k in ("revenue", "cogs", "gross_profit", "operating_income", "pretax", "tax", "net_income", "equity"))
        if rev is not None and cogs is not None and gp is not None:
            add(y, "加減法 毛利 = 營收 − 營業成本", gp, rev - abs(cogs), max(1.0, abs(rev) * 0.01), "add_sub")
        if pbt is not None and tax is not None and ni is not None:
            add(y, "加減法 稅後 = 稅前 − 所得稅", ni, pbt - abs(tax), max(1.0, abs(pbt) * 0.02), "add_sub", minority=True)
        if gp is not None and oi is not None:
            out.append({"year": y, "check": "加減法 營業利益 ≤ 毛利", "kind": "add_sub", "lhs": round(oi, 4), "rhs": round(gp, 4), "tolerance": 0, "verdict": "PASS" if oi <= gp + max(1.0, abs(gp) * 0.001) else "FAIL"})
        for key, numer, label in (("gross_margin", gp, "毛利率 = 毛利 ÷ 營收"), ("op_margin", oi, "營益率 = 營業利益 ÷ 營收"), ("net_margin", ni, "淨利率 = 淨利 ÷ 營收")):
            r = g("ratio:" + key, y)
            if r is not None and numer is not None and rev:
                add(y, "乘除法 " + label, r, numer / rev * 100.0, 1.0, "mul_div")
        roe = g("ratio:roe", y)
        if roe is not None and ni is not None and eq:
            eq0 = g("equity", y - 1)
            avg = ni / ((eq + eq0) / 2.0) * 100.0 if eq0 else None
            add(y, "乘除法 ROE ≈ 淨利 ÷ 權益(期末或平均)", roe, ni / eq * 100.0, 3.0, "mul_div", alt=avg)
        gr = g("ratio:rev_growth", y)
        rev0 = g("revenue", y - 1)
        if gr is not None and rev is not None and rev0:
            add(y, "乘除法 營收成長率 = 營收 ÷ 前一年 − 1", gr, (rev / rev0 - 1.0) * 100.0, 1.0, "mul_div")
    return out


def pick_final(aligned: list) -> dict:
    """檢驗用的「每 (科目, 年度) 一個值」:有歷史覆蓋 → 歷史值;否則取這份報告裡最常出現的值(預估調整表的舊估 / 共識 / 變動 % 只出現一次,
    現行預估會在多張表重複出現);金額 / 每股科目不收帶 % 的值;比率列用 ratio_of(ITEM)。"""
    groups = {}
    for row in aligned:
        y = row.get("YEAR")
        std = row.get("STD") or ""
        raw = str(row.get("VALUE_REPORT") if row.get("VALUE_REPORT") is not None else row.get("VALUE") or "")
        if not y:
            continue
        if std:
            if "%" in raw:
                continue
            key = (std, y)
        else:
            rk = ratio_of(row.get("ITEM"))
            if not rk:
                continue
            key = ("ratio:" + rk, y)
        v = row.get("VALUE_FINAL")
        if not isinstance(v, (int, float)):
            v = BASE.num(v)
        if v is None:
            continue
        groups.setdefault(key, []).append((float(v), str(row.get("VALUE_SOURCE") or "").startswith("HISTORY")))
    final = {}
    for key, vals in groups.items():
        hist = [v for v, h in vals if h]
        if hist:
            final[key] = hist[0]
            continue
        best, best_n = None, 0
        for v, _ in vals:
            n = sum(1 for w, _ in vals if abs(w - v) <= SAME_VALUE * max(abs(v), abs(w), 1e-9))
            if n > best_n:
                best, best_n = v, n
        final[key] = best
    return final


BASE.std_of = std_of          # v0101 align_file 用 P.std_of / P.ratio_of / P.checks(P = v0100)→ 本版
BASE.ratio_of = ratio_of
BASE.checks = checks
_native_align = BASE.align
_native_align_file = BASE.align_file          # v0101 的 align_file(v0101 已綁進 v0100)


def align_file(rows: list, hist: dict, has_hist: bool) -> dict:
    res = _native_align_file(rows, hist, has_hist)
    rc = res["receipt"]
    rc["checks"] = checks(pick_final(res["aligned"]))
    n_ok = sum(1 for c in rc["checks"] if c["verdict"] == "PASS")
    rc["checks_pass"] = "%d/%d" % (n_ok, len(rc["checks"])) if rc["checks"] else "—"
    rc["checks_unclear"] = sum(1 for c in rc["checks"] if c["verdict"] == "UNCLEAR")
    return res


BASE.align_file = align_file


def align(root: Path, fin_path=None, market_path=None, out_dir=None) -> dict:
    rec = _native_align(root, fin_path, market_path, out_dir)
    t = rec.get("totals") or {}
    if rec.get("files"):
        t["checks_unclear"] = sum(1 for f in rec["files"].values() for c in (f.get("checks") or []) if c.get("verdict") == "UNCLEAR")
        t["std_excluded_rule"] = "v0102 排除:其他 / 部門 / 事業 / … of … / 應付 / 負債 / 少數 / 遞延 / 現金 / 調整後 / 核心 / 權益法 / return on / debt"
        rec["totals"] = t
        if "檢驗" in str(rec.get("why", "")) and t["checks_unclear"]:
            rec["why"] = str(rec["why"]).rstrip(")") + " · 口徑不明 %d)" % t["checks_unclear"] if str(rec["why"]).endswith(")") else str(rec["why"]) + " · 口徑不明 %d" % t["checks_unclear"]
        v2 = Path(root) / "VIA_Reports" / "vrn2"
        BASE._finish(v2, rec)
    return rec


BASE.align = align
PRIOR.align = align


def selftest() -> int:
    bad = []

    def chk(label, cond):
        BASE.say(("[PASS] " if cond else "[FAIL] ") + label)
        if not cond:
            bad.append(label)

    rc = PRIOR.selftest()                               # v0101 的 ① ~ ⑥(std_of / checks 已是本版)
    if rc != 0:
        bad.append("v0101 ① ~ ⑥")
    cases = {"Other Revenue": "", "Total Revenue": "revenue", "Revenue (NT$ bn)": "revenue", "Taxes payable": "", "Income tax": "tax", "Total liabs & equity": "",
             "Minorities/other equity": "", "Total equity": "equity", "Shareholders' equity": "equity", "Equity income": "", "Return on equity": "", "Net debt/equity": "",
             "Net profit (adjusted)": "", "Net profit (reported)": "net_income", "Core EPS": "", "EPS (NT$)": "eps", "Cogs (ex-D&A)": "cogs", "Gross Profit (ex-D&A)": "gross_profit",
             "Other operating income": "", "Operating income": "operating_income", "其他營業收入": "", "營業收入": "revenue", "歸屬母公司淨利": "net_income", "Taxes paid": ""}
    got = {k: std_of(k) for k in cases}
    chk("⑦ 科目:其他營收 / 應付所得稅 / 負債與權益合計 / 少數權益 / 權益法收益 / ROE 字樣 / 調整後淨利 / 核心 EPS → 空;總營收 / 所得稅 / 權益總額 / 報告淨利 / EPS / 成本(ex-D&A)照對",
        got == cases)
    if got != cases:
        BASE.say("    差異:%s" % {k: (v, cases[k]) for k, v in got.items() if v != cases[k]})
    rcases = {"Sales growth of OEM business (%)": "", "Revenue growth (% YoY)": "rev_growth", "Net profit margin (%)": "net_margin", "GM (%)": "gross_margin", "Adj ROE (%)": "", "ROE (%)": "roe"}
    rgot = {k: ratio_of(k) for k in rcases}
    chk("⑧ 比率列:「Sales growth of OEM business」/「Adj ROE」→ 空;營收成長 / 淨利率 / 毛利率 / ROE 照對", rgot == rcases)
    ck = checks({("revenue", 2021): 192626.0, ("cogs", 2021): -176457.0, ("gross_profit", 2021): 16169.0, ("net_income", 2021): 8655.0, ("equity", 2021): 27370.0, ("equity", 2020): 24000.0,
                 ("ratio:roe", 2021): 36.0, ("ratio:net_margin", 2021): 4.5, ("revenue", 2022): 292876.0, ("ratio:net_margin", 2022): 48.0, ("net_income", 2022): 14175.0})
    by = {(c["year"], c["check"].split(" ")[1]): c["verdict"] for c in ck}
    chk("⑨ 檢驗:成本寫負數 (176,457) → 毛利 PASS · ROE 36.0 期末權益差 4.4 · 用平均權益 → PASS · 2022 淨利率 48 vs 4.8 → UNCLEAR(不算不過)",
        by.get((2021, "毛利")) == "PASS" and by.get((2021, "ROE")) == "PASS" and by.get((2022, "淨利率")) == "UNCLEAR" and by.get((2021, "淨利率")) == "PASS")
    gs = [{"STD": "revenue", "YEAR": 2027, "VALUE_REPORT": v, "VALUE_FINAL": BASE.num(v), "VALUE_SOURCE": "REPORT", "ITEM": "Revenue"} for v in ("28,399", "31,181", "9.8%", "27,326", "31,181", "31,181.2")]
    gs += [{"STD": "gross_profit", "YEAR": 2027, "VALUE_REPORT": v, "VALUE_FINAL": BASE.num(v), "VALUE_SOURCE": "REPORT", "ITEM": "Gross profit"} for v in ("15,205", "17,076", "12.3%", "14,554", "17,076")]
    gs += [{"STD": "", "YEAR": 2027, "VALUE_REPORT": "54.8%", "VALUE_FINAL": 54.8, "VALUE_SOURCE": "REPORT", "ITEM": "Gross margin"}]
    pf = pick_final(gs)
    ck2 = checks(pf)
    dw = checks({("pretax", 2019): 2358.0, ("tax", 2019): -502.0, ("net_income", 2019): 1984.0, ("pretax", 2020): 1000.0, ("tax", 2020): -200.0, ("net_income", 2020): 500.0})
    dv = {c["year"]: c["verdict"] for c in dw if "稅後" in c["check"]}
    chk("⑪ 預估調整表(舊估 28,399 / 新估 31,181 / 變動 9.8% / 共識 27,326)→ 取最常出現的 31,181 · 毛利 17,076 · 毛利率 54.8% 檢驗 PASS;稅後 1,984 vs 1,856(差 6.9%)→ 口徑不明 · 差 37.5% → 不過",
        pf.get(("revenue", 2027)) == 31181.0 and pf.get(("gross_profit", 2027)) == 17076.0 and any(c["verdict"] == "PASS" and "毛利率" in c["check"] for c in ck2) and dv == {2019: "UNCLEAR", 2020: "FAIL"})
    with tempfile.TemporaryDirectory(prefix="vrn2-hist102-") as td:
        root = Path(td)
        BASE._fixture(root)
        v2 = root / "VIA_Reports" / "vrn2"
        fin = json.loads((v2 / "output" / "VRN2_FinancialData_latest.json").read_text(encoding="utf-8"))
        A = "A-2330 20260101.pdf"
        for item, period, value in (("Other Revenue", "2024A", "2,000"), ("Taxes payable", "2024A", "0"), ("Total liabs & equity", "2024A", "9,000,000"), ("Net profit (adjusted)", "2025A", "1,100.0")):
            fin.append({"REPORT_DATE": "2026-01-01", "FILENAME": A, "TICKER": "2330", "BROKER": "A", "PAGE": 6, "TABLE": "P6·F·09·TB", "ITEM": item, "PERIOD": period, "VALUE": value, "VERIFY": "VERIFIED", "ROW": 9, "SECTION": ""})
        (v2 / "output" / "VRN2_FinancialData_latest.json").write_text(json.dumps(fin, ensure_ascii=False), encoding="utf-8")
        r = align(root)
        al = json.loads((v2 / "output" / "VRN2_FinancialAligned_latest.json").read_text(encoding="utf-8"))
        de = json.loads((v2 / "output" / "VRN2_Deleted_latest.json").read_text(encoding="utf-8"))
        extra = [x for x in al if x["FILENAME"] == A and x["ITEM"] in ("Other Revenue", "Taxes payable", "Total liabs & equity", "Net profit (adjusted)")]
        saved = json.loads((v2 / "VRN2_HistoryAlign_latest.json").read_text(encoding="utf-8"))
        chk("⑩ 端到端:加進來的 4 列(其他營收 · 應付所得稅 · 負債與權益合計 · 調整後淨利)STD 空 · 不覆蓋 · 不進刪除區 · 刪除區仍只有 2025A 淨利 1 列 · 收據 totals 有 checks_unclear 且寫回檔案",
            len(extra) == 4 and all(x["STD"] == "" and not str(x["VALUE_SOURCE"]).startswith("HISTORY") for x in extra) and len(de) == 1 and de[0]["STD"] == "net_income"
            and "checks_unclear" in (r.get("totals") or {}) and "checks_unclear" in (saved.get("totals") or {}) and r["files"][A]["lamp"] == "GREEN")
    BASE.say("[%s] %s %s --selftest · 11 項 · 不過 %d" % ("PASS" if not bad else "FAIL", DISPLAY_NAME, VERSION, len(bad)))
    return 0 if not bad else 1


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in argv:
        return selftest()
    return BASE.main(argv)


if __name__ == "__main__":
    sys.exit(main())
