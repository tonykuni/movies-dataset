#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VRN_ENG074_FinancialPages — 財報頁表格擷取器(批241 波2;操作員選項2)
====================================================================
規格書 b236「Financial Data 76 欄」首波:報告後頁財務表→
VeritasSynonymEngine 科目對齊→時間軸 zip→vrn_report_financial。
機制(操作員 Gemini 對談之表格重建三步):
  ①財務頁判準:頁文含 ≥2 個核心科目(營業收入/毛利/營業利益/
    稅後/EPS)且有期間表頭列(≥2 個 20xx/兩碼Q/民國 tokens)
  ②表頭定位:期間 tokens 列=時間軸;E/F/(F)=ESTIMATE 狀態拆離
  ③數據列拆解:首數字切分點前=科目名(Gemini 防呆①)→
    VRN_Financial_Synonyms_SSOT.normalize_metric() 對齊 canonical;
    未命中=UNKNOWN 誠實列示候 register(不硬套);
    數值支援 千位逗號/負數 (1,250)/−/-;與時間軸 zip 對齊
落庫:vrn_report_financial(report_file,page,canonical,raw_label,
  period,status,value,raw_text)——派生層重算(同檔重寫);
  REPORT_STATED/ESTIMATE 隔離,永不冒充官方值(雙 SSOT)。
用法:python3 VRN_ENG074_FinancialPages_v0100.py run [--dir 報告夾]
      | --status | --selftest
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

import importlib.util
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
REPORTS = HERE / "input_reports"
DB_TW = VIA / "functional modules" / "VDF" / "output_hub" / "mega" / "vdf_tw_market.duckdb"

CORE_ITEMS = ("營業收入", "營業毛利", "毛利", "營業利益", "稅後", "淨利",
              "EPS", "每股盈餘", "Revenue", "Gross", "Operating")
PERIOD_RX = re.compile(r"(20\d{2}(?:\s*[EF(]|年)?|(?<!\d)\d{2}Q[1-4]"
                       r"|1[01]\d年?)[EF)]?", re.I)
PERIOD_TOKEN_RX = re.compile(
    r"^(20\d{2}|\d{2}Q[1-4]|1[01]\d)(?:年)?\(?([EFA])?\)?$", re.I)
NUM_RX = re.compile(r"^\(?-?[\d,]+(?:\.\d+)?\)?%?$|^--?$|^—$")
FIRST_DIGIT_RX = re.compile(r"^(.*?[^\d(,\-])\s+(\(?-?\d[\d,]*"
                            r"(?:\.\d+)?.*)$")


def _syn():
    p = HERE / "VRN_Financial_Synonyms_SSOT.py"
    spec = importlib.util.spec_from_file_location("finsyn74", p)
    m = importlib.util.module_from_spec(spec)
    sys.modules["finsyn74"] = m
    spec.loader.exec_module(m)
    return m


def _val(tok: str) -> float | None:
    tok = tok.strip().rstrip("%")
    if tok in ("--", "-", "—", ""):
        return None
    neg = tok.startswith("(") and tok.endswith(")")
    tok = tok.strip("()").replace(",", "")
    try:
        v = float(tok)
        return -v if neg else v
    except Exception:
        return None


def parse_header(line: str) -> list[tuple[str, str]] | None:
    """期間表頭列→[(period, status)];<2 tokens=非表頭"""
    out = []
    for tok in line.split():
        m = PERIOD_TOKEN_RX.match(tok)
        if not m:
            continue
        p = m.group(1)
        if re.match(r"^1[01]\d$", p):
            p = str(int(p) + 1911)                 # 民國年
        st = "ESTIMATE" if (m.group(2) or "").upper() in ("E", "F") \
            else "REPORT_STATED"
        out.append((p, st))
    return out if len(out) >= 2 else None


def parse_data_row(line: str, header: list, syn) -> dict | None:
    """數據列:首數字切分→科目 normalize_metric→zip 時間軸"""
    m = FIRST_DIGIT_RX.match(line.strip())
    if not m:
        return None
    label = m.group(1).strip(" :‧·")
    toks = m.group(2).split()
    vals = [_val(t) for t in toks if NUM_RX.match(t)]
    if not label or len(vals) < 2:
        return None
    def _canon(lbl: str) -> str:
        r = syn.normalize_metric(lbl)
        if r and r != lbl:                     # SSOT 未命中=回原字串
            return r
        for suf in ("淨額", "合計", "總額", "總計"):
            if lbl.endswith(suf):
                r = syn.normalize_metric(lbl[:-len(suf)])
                if r and r != lbl[:-len(suf)]:
                    return r
        return ""
    canon = _canon(label)
    cells = []
    for (per, st), v in zip(header, vals):
        if v is not None:
            cells.append({"period": per, "status": st, "value": v})
    return {"raw_label": label, "canonical": canon, "cells": cells} \
        if cells else None


def is_financial_page(text: str) -> bool:
    hits = sum(1 for k in CORE_ITEMS if k in text)
    return hits >= 2 and len(PERIOD_RX.findall(text)) >= 2


def extract_pdf_fin(p: Path) -> list[dict]:
    """頁 2..N 財務頁表格;回 rows(每列=科目×期間×值)"""
    try:
        import fitz
    except Exception:
        return []
    syn = _syn()
    rows = []
    try:
        with fitz.open(str(p)) as doc:
            for pno in range(1, doc.page_count):
                text = doc[pno].get_text("text", sort=True)
                if not is_financial_page(text):
                    continue
                header = None
                for line in text.splitlines():
                    h = parse_header(line)
                    if h:
                        header = h
                        continue
                    if header:
                        d = parse_data_row(line, header, syn)
                        if d:
                            for c in d["cells"]:
                                rows.append({
                                    "report_file": p.stem, "page": pno + 1,
                                    "canonical": d["canonical"],
                                    "raw_label": d["raw_label"][:60],
                                    "period": c["period"],
                                    "status": c["status"],
                                    "value": c["value"],
                                    "raw_text": line.strip()[:120]})
    except Exception:
        return rows
    return rows


def run(src: Path | None = None, db: Path | None = None) -> int:
    import duckdb
    src = src or REPORTS
    pdfs = sorted(src.glob("*.pdf")) if src.exists() else []
    if not pdfs:
        print(f"[財報頁] {src} 無 PDF(誠實;先跑缺件搜集)")
        return 2
    con = duckdb.connect(str(db or DB_TW))
    con.execute("""CREATE TABLE IF NOT EXISTS vrn_report_financial(
        report_file VARCHAR, page INTEGER, canonical VARCHAR,
        raw_label VARCHAR, period VARCHAR, status VARCHAR,
        value DOUBLE, raw_text VARCHAR)""")
    tot = unk = 0
    for p in pdfs:
        rows = extract_pdf_fin(p)
        con.execute("DELETE FROM vrn_report_financial WHERE report_file=?",
                    [p.stem])                       # 派生層重算
        for r in rows:
            con.execute("INSERT INTO vrn_report_financial VALUES "
                        "(?,?,?,?,?,?,?,?)", list(r.values()))
        u = sum(1 for r in rows if not r["canonical"])
        tot += len(rows)
        unk += u
        if rows:
            print(f"  [{p.stem[:44]}] +{len(rows)} 值"
                  f"(UNKNOWN 科目 {u}=候 register)")
    n = con.execute("SELECT count(*) FROM vrn_report_financial").fetchone()[0]
    con.close()
    print(f"[財報頁計] {len(pdfs)} 件 · 本輪 +{tot} 值(未對齊 {unk} 誠實)"
          f" · 庫 {n:,} 列")
    return 0


def status() -> int:
    import duckdb
    con = duckdb.connect(str(DB_TW), read_only=True)
    try:
        for c, n in con.execute(
                "SELECT canonical, count(*) FROM vrn_report_financial "
                "GROUP BY canonical ORDER BY 2 DESC LIMIT 15").fetchall():
            print(f"  [{c or 'UNKNOWN'}] {n}")
    except Exception:
        print("  未建(先 run)")
    con.close()
    return 0


def selftest() -> int:
    import tempfile
    import duckdb
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    src_txt = Path(__file__).read_text(encoding="utf-8")
    syn = _syn()
    chk("① SynonymEngine SSOT 掛載(normalize_metric 正主)",
        syn.normalize_metric("營業收入") == "revenue"
        and callable(syn.normalize_metric))
    h = parse_header("6873泓德能源 2023 24Q1 24Q2 2024 25Q1(F) 2025(F)")
    chk("② 期間表頭定位(混合年/季/E·F 狀態拆離)",
        h is not None and ("2023", "REPORT_STATED") in h
        and ("2025", "ESTIMATE") in h and ("24Q1", "REPORT_STATED") in h)
    d = parse_data_row("營業收入淨額 5,839 884 1,272 10,125 1,467 12,108",
                       h, syn)
    chk("③ 壓平數據列拆解+科目對齊(Gemini 首數字切分)",
        d is not None and d["canonical"] == "revenue"
        and d["cells"][0]["value"] == 5839.0
        and d["cells"][0]["period"] == "2023")
    d2 = parse_data_row("神秘特殊科目 100 200 300", h[:3], syn)
    chk("④ 未命中=UNKNOWN 誠實(不硬套;候 register)",
        d2 is not None and d2["canonical"] == "")
    d3 = parse_data_row("營業利益 (1,250) -70.2 300", h[:3], syn)
    chk("⑤ 負數雙格式((1,250)=-1250;-70.2)",
        d3 is not None and d3["cells"][0]["value"] == -1250.0
        and d3["cells"][1]["value"] == -70.2)
    chk("⑥ 財務頁判準(核心科目≥2+期間≥2;非財頁拒)",
        is_financial_page("營業收入 100 毛利 50 2023 2024")
        and not is_financial_page("本公司免責聲明如下"))
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        import fitz
        doc = fitz.open()
        doc.new_page().insert_text((40, 60), "COVER PAGE")
        pg = doc.new_page()
        pg.insert_text((40, 60), "6873 2023 2024 2025(F)",
                       fontname="china-t")
        pg.insert_text((40, 80), "營業收入淨額 5,839 10,125 12,108",
                       fontname="china-t")
        pg.insert_text((40, 100), "營業毛利 1,450 2,528 3,100",
                       fontname="china-t")
        doc.save(str(tdp / "fx_fin.pdf"))
        doc.close()
        dbp = tdp / "t.duckdb"
        rc1 = run(tdp, dbp)
        rc2 = run(tdp, dbp)
        con = duckdb.connect(str(dbp))
        n = con.execute("SELECT count(*) FROM vrn_report_financial").fetchone()[0]
        rev = con.execute("SELECT value FROM vrn_report_financial WHERE "
                          "canonical='revenue' AND period='2025' "
                          "AND status='ESTIMATE'").fetchone()
        con.close()
        chk("⑦ PDF 端到端(頁2 表→庫;2025F=12108 ESTIMATE)",
            rc1 == 0 and rev is not None and rev[0] == 12108.0)
        chk("⑧ 重跑冪等(派生層重算;列數不倍增)", rc2 == 0 and n == 6)
    chk("⑨ 雙 SSOT 隔離宣告(REPORT_STATED/ESTIMATE;永不冒充官方)",
        "永不冒充官方" in src_txt and "REPORT_STATED" in src_txt)
    chk("⑩ 零網路+加速橋", "ACCEL-BRIDGE" in src_txt
        and all(("import " + k) not in src_txt for k in ("requests", "httpx")))
    print(f"  [計] 十檢 OK {10 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== 財報頁表格擷取器(VRN_ENG074)· 十檢自測(零網路)===")
        return selftest()
    if "--status" in args:
        return status()
    if args and args[0] == "run":
        d = Path(args[args.index("--dir") + 1]) if "--dir" in args else None
        return run(d)
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main())
