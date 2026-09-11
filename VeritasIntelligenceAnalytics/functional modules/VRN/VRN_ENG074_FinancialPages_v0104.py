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

v0101→v0102(批403 操作員問「所有 VRN 檔案有拆解 FILENAME/首頁/財報頁
表格、讀取相互對照的引擎模組?」——盤點查出唯一缺口並補):
  盤點結論:①檔名拆解=ENG073 extract_one(四碼 ticker 逐驗 tw_listings
  名冊/BROKER_DICT 券商/三格式日期)在位 ②首頁=ENG072 v0105 分區+
  pdfplumber 法B 雙法逐區對照(AGREE/PARTIAL/DIVERGE)在位 ③財報頁表格
  =本引擎在位 ④檔名↔首頁對照=ENG073 交互驗證(ticker/官方名/升幅
  EXACT·ROUNDING_ONLY·FORMULA_MISMATCH·PARSE_SUSPECT)在位——但
  **財報頁表格從不與首頁/檔名對照**:v0101 只寫 vrn_report_financial,
  全樹亦只有本引擎讀它,ENG080 四點取的是 ENG073 的 vrn_report_metrics。
  故本版補第三邊,三角閉合(不另造引擎=Zero-Hydra,對照住在表格擁有者):
  crosscheck() 讀 vrn_report_basic(檔名邊)+vrn_report_metrics(首頁邊)
  ×vrn_report_financial(表格邊)→ vrn_report_crosscheck:
    · eps@期間:首頁 rx 值 vs 表格值 → AGREE(≤1%)/ROUNDING(≤5%)/
      UNIT_SCALE(比值近 1e±2/3/6=單位差,非錯)/DIVERGE/ONLY_FIRSTPAGE/
      ONLY_TABLE/MISSING_BOTH(誠實七態,不判死不覆寫)
    · ticker_on_fin_page:檔名 ticker 是否現身於該報告財報頁原文
    · report_date_vs_periods:報告日年 vs 表格最大 REPORT_STATED 年
      (表格已報年份晚於報告日=DATE_AHEAD 誠實可疑)
  派生層重算(同 report_file DELETE+INSERT);ENG073 兩表缺=誠實略過
  不 crash(先跑 ENG073);run 內建跑一次,亦可 --crosscheck 單獨重算。
用法:python3 VRN_ENG074_FinancialPages_v0104.py run [--dir 報告夾]
      [--no-cross] | --crosscheck | --status | --selftest
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


def _resolve_db(db: Path | None) -> Path | None:
    """批244:庫路徑誠實解析(工作站雙 clone 債——mega 庫可能在
    Downloads\movies-dataset 替根)。顯式 db=信任直用(selftest 建新
    庫);預設=主路徑→替根探測;全缺=None 誠實停 rc2 不 traceback。"""
    if db is not None:
        return Path(db)
    cands = [DB_TW]
    try:
        home = Path.home()
        rel = Path("movies-dataset/VeritasIntelligenceAnalytics/functional modules/VDF/output_hub/mega/vdf_tw_market.duckdb")
        cands += [home / "Downloads" / rel, home / rel]
    except Exception:
        pass
    for c in cands:
        if c and Path(c).exists():
            if Path(c) != DB_TW:
                print(f"[庫解析] 主路徑缺→改用替根庫:{c}(誠實提示)")
            return Path(c)
    print(f"[庫缺] {DB_TW} 不在且替根未尋獲=誠實停(rc2)。"
          "先跑 VDF_ENG065_DbImport 三包匯入,或確認 clone 根。")
    return None


import importlib.util
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
REPORTS = HERE / "input_reports"
#: 輸入規格正典(批442:與首頁全能引擎/ENG072 v0108/MDL139/MDL141 同一本冊)
SPEC_REL = Path("supportive modules") / "registry" / "VIA_InputConsole_Spec_v0100.json"


def _report_dirs(given: Path | None = None) -> tuple[list[Path], str]:
    """報告夾律:--dir > 冊 user.vrn_dir > 冊 dir_default;**incoming 一律併入**。"""
    import json as _json
    dirs: list[Path] = []
    blk, user, why = {}, "", "冊不在 → 只用內建預設"
    sp = VIA / SPEC_REL
    if sp.exists():
        try:
            d = _json.loads(sp.read_text(encoding="utf-8-sig"))
            blk = d["families"]["vrn"]["input"]
            user = str((d.get("user") or {}).get("vrn_dir") or "").strip()
            why = f"冊 {sp.name}"
        except Exception as exc:
            why = f"冊讀取失敗 {type(exc).__name__} → 內建預設"
    if given is not None:
        dirs.append(given)
    elif user:
        q = Path(user)
        dirs.append(q if q.is_absolute() else VIA / q)
    else:
        dirs.append(VIA / blk.get("dir_default", "functional modules/VRN/input_reports"))
    inc = VIA / blk.get("incoming", "functional modules/VRN/input/incoming")
    if inc not in dirs:
        dirs.append(inc)
    return dirs, why
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


# ===== 批403:三方對照(檔名 × 首頁 × 財報頁表格)=====================
CROSS_COLS = ("report_file", "ticker", "dimension", "period",
              "first_page_value", "table_value", "ratio", "state", "note",
              "checked_at")
# 單位差常見倍率(千元/百萬元/元 之間;比值落此附近=UNIT_SCALE 非 DIVERGE)
UNIT_FACTORS = (1e3, 1e2, 1e6, 1e-2, 1e-3, 1e-6)


def compare_values(a: float | None, b: float | None) -> tuple[str, float | None]:
    """a=首頁邊值 b=表格邊值;回 (state, ratio=b/a)。誠實七態,不判死。"""
    if a is None and b is None:
        return "MISSING_BOTH", None
    if a is None:
        return "ONLY_TABLE", None
    if b is None:
        return "ONLY_FIRSTPAGE", None
    if a == 0 or b == 0:
        return ("AGREE", 1.0) if a == b else ("DIVERGE", None)
    ratio = b / a
    diff = abs(b - a) / abs(a)
    if diff <= 0.01:
        return "AGREE", ratio
    if diff <= 0.05:
        return "ROUNDING", ratio
    for f in UNIT_FACTORS:
        if abs(ratio / f - 1.0) <= 0.02:
            return "UNIT_SCALE", ratio
    return "DIVERGE", ratio


def _has_table(con, name: str) -> bool:
    try:
        con.execute(f"SELECT 1 FROM {name} LIMIT 1")
        return True
    except Exception:
        return False


def crosscheck(con, stems: list[str] | None = None,
               do_print: bool = True) -> dict:
    """三方對照落 vrn_report_crosscheck;ENG073 兩表缺=誠實略過(不 crash)"""
    from datetime import datetime
    if not _has_table(con, "vrn_report_financial"):
        if do_print:
            print("  [對照] vrn_report_financial 未建=誠實略(先 run)")
        return {"skipped": "NO_FINANCIAL"}
    if not (_has_table(con, "vrn_report_basic")
            and _has_table(con, "vrn_report_metrics")):
        if do_print:
            print("  [對照] ENG073 兩表(basic/metrics)缺=誠實略過,"
                  "不假綠;先跑 VRN_ENG073_ReportStructuredDB run")
        return {"skipped": "NO_ENG073"}
    con.execute(f"""CREATE TABLE IF NOT EXISTS vrn_report_crosscheck(
        report_file VARCHAR, ticker VARCHAR, dimension VARCHAR,
        period VARCHAR, first_page_value DOUBLE, table_value DOUBLE,
        ratio DOUBLE, state VARCHAR, note VARCHAR, checked_at VARCHAR)""")
    if stems is None:
        stems = [r[0] for r in con.execute(
            "SELECT DISTINCT report_file FROM vrn_report_financial").fetchall()]
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    tally: dict[str, int] = {}
    rows_all = []
    for stem in stems:
        b = con.execute(
            "SELECT ticker, report_date FROM vrn_report_basic "
            "WHERE report_file=?", [stem]).fetchone()
        ticker, rdate = (b[0] or "", b[1] or "") if b else ("", "")
        fp = {}                                   # 首頁邊:(metric, period)→值
        for mt, per, val in con.execute(
                "SELECT metric, period, value FROM vrn_report_metrics "
                "WHERE report_file=? AND value IS NOT NULL", [stem]).fetchall():
            fp.setdefault((mt, per), val)
        tb = {}                                   # 表格邊:(canonical, period)→值
        for cn, per, val in con.execute(
                "SELECT canonical, period, value FROM vrn_report_financial "
                "WHERE report_file=? AND value IS NOT NULL", [stem]).fetchall():
            if cn:
                tb.setdefault((cn, per), val)
        rows = []
        # ① eps(兩邊共有之正典鍵;eps_diluted 併看,表格優先精確鍵)
        keys = {k for k in fp if k[0] == "eps"} | \
               {k for k in tb if k[0] in ("eps", "eps_diluted")}
        for _m, per in sorted({(("eps"), k[1]) for k in keys}):
            a = fp.get(("eps", per))
            b2 = tb.get(("eps", per))
            if b2 is None:
                b2 = tb.get(("eps_diluted", per))
            st, ratio = compare_values(a, b2)
            rows.append((stem, ticker, "eps", per, a, b2, ratio, st,
                         "首頁 rx × 財報頁表格", ts))
        # ② 表格獨有之正典科目(首頁無對照=誠實列 ONLY_TABLE 供人工核)
        for (cn, per), val in sorted(tb.items()):
            if cn in ("eps", "eps_diluted"):
                continue
            rows.append((stem, ticker, cn, per, None, val, None,
                         "ONLY_TABLE", "表格獨有科目(首頁無同名值)", ts))
        # ③ 檔名 ticker ↔ 財報頁原文(第三邊:檔名 × 表格)
        if ticker:
            hit = con.execute(
                "SELECT count(*) FROM vrn_report_financial WHERE "
                "report_file=? AND raw_text LIKE ?",
                [stem, f"%{ticker}%"]).fetchone()[0]
            rows.append((stem, ticker, "ticker_on_fin_page", "", None, None,
                         None,
                         "TICKER_ON_FIN_PAGE" if hit else "TICKER_NOT_ON_FIN_PAGE",
                         f"財報頁原文命中 {hit} 列(未命中非錯=多數表格不重印代號)",
                         ts))
        else:
            rows.append((stem, "", "ticker_on_fin_page", "", None, None, None,
                         "NO_TICKER", "檔名無在冊四碼(研討會/晨報誠實非個股)",
                         ts))
        # ④ 報告日 ↔ 表格已報期間(表格已報年晚於報告日=誠實可疑)
        stated = con.execute(
            "SELECT max(CAST(substr(period,1,4) AS INTEGER)) FROM "
            "vrn_report_financial WHERE report_file=? AND status='REPORT_STATED'"
            " AND substr(period,1,4) SIMILAR TO '[0-9]{4}'", [stem]).fetchone()
        smax = stated[0] if stated else None
        ryear = int(rdate[:4]) if rdate[:4].isdigit() else None
        if ryear is None:
            st4, note4 = "NO_DATE", "檔名無可解析日期"
        elif smax is None:
            st4, note4 = "NO_TABLE_STATED", "表格無已報期間(全為預估或無表)"
        elif smax > ryear:
            st4, note4 = "DATE_AHEAD", f"表格已報 {smax} > 報告日 {ryear}=誠實可疑"
        else:
            st4, note4 = "DATE_CONSISTENT", f"表格已報 {smax} ≤ 報告日 {ryear}"
        rows.append((stem, ticker, "report_date_vs_periods", rdate,
                     float(ryear) if ryear else None,
                     float(smax) if smax else None, None, st4, note4, ts))
        con.execute("DELETE FROM vrn_report_crosscheck WHERE report_file=?",
                    [stem])                        # 派生層重算
        for r in rows:
            con.execute("INSERT INTO vrn_report_crosscheck VALUES "
                        "(?,?,?,?,?,?,?,?,?,?)", list(r))
            tally[r[7]] = tally.get(r[7], 0) + 1
        rows_all += rows
    if do_print:
        head = " · ".join(f"{k} {v}" for k, v in sorted(
            tally.items(), key=lambda x: -x[1]))
        print(f"  [對照] {len(stems)} 件 × 三邊 → {len(rows_all)} 列 · {head}")
    return {"reports": len(stems), "rows": len(rows_all), "tally": tally}


def run(src: Path | None = None, db: Path | None = None,
        cross: bool = True) -> int:
    import duckdb
    # 批442:報告夾綁**輸入規格正典**(與首頁全能引擎、ENG072 v0108、MDL141 同一本冊)。
    # v0103 把 input_reports 寫死成唯一預設,而操作員的 64 份報告住在 input/incoming
    # ——ENG072 v0107 犯過一模一樣的病(批438),同一個錯不該在第二支引擎再犯一次。
    dirs, spec_why = _report_dirs(src)
    pdfs, diag = [], []
    for d in dirs:
        got = sorted(d.glob("*.pdf")) if d.is_dir() else []
        diag.append((d, "夾不存在" if not d.is_dir()
                     else ("夾是空的" if not any(d.iterdir()) else f"{len(got)} 件 PDF")))
        pdfs.extend(got)
    pdfs = sorted({f.resolve(): f for f in pdfs}.values())
    if not pdfs:
        print(f"[財報頁] 無 PDF(誠實;先跑缺件搜集)· 夾律={spec_why}")
        for d, st in diag:
            print(f"   · {d} → {st}")
        return 2
    src = dirs[0]
    print(f"[財報頁] 夾律={spec_why};取件 {len(pdfs)} 份 · "
          + " · ".join(f"{d.name}={st}" for d, st in diag))
    dbp = _resolve_db(Path(db) if db else None)
    if dbp is None:
        return 2
    con = duckdb.connect(str(dbp))
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
    if cross:                                       # 批403:三方對照同輪落庫
        crosscheck(con, [p.stem for p in pdfs])
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
    try:                                            # 批403:三方對照分佈
        rs = con.execute(
            "SELECT dimension, state, count(*) FROM vrn_report_crosscheck "
            "GROUP BY 1,2 ORDER BY 3 DESC LIMIT 12").fetchall()
        print("  --- 三方對照(檔名×首頁×財報頁表格)---")
        for d, st, n in rs:
            print(f"  [{d}] {st} {n}")
        if not rs:
            print("  (無列;先 run 或 --crosscheck)")
    except Exception:
        print("  三方對照表未建(先 run 或 --crosscheck)")
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
    # --- 批403 三方對照四檢 -------------------------------------------
    chk("⑪ 對照狀態律(AGREE≤1%/ROUNDING≤5%/UNIT_SCALE 千百萬倍/DIVERGE/單邊/雙缺)",
        compare_values(10.0, 10.05)[0] == "AGREE"
        and compare_values(10.0, 10.4)[0] == "ROUNDING"
        and compare_values(10.0, 10000.0)[0] == "UNIT_SCALE"
        and compare_values(10.0, 25.0)[0] == "DIVERGE"
        and compare_values(10.0, None)[0] == "ONLY_FIRSTPAGE"
        and compare_values(None, 10.0)[0] == "ONLY_TABLE"
        and compare_values(None, None)[0] == "MISSING_BOTH")
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        import fitz
        doc = fitz.open()
        doc.new_page().insert_text((40, 60), "COVER PAGE")
        pg = doc.new_page()
        pg.insert_text((40, 60), "6873 2023 2024 2025(F)", fontname="china-t")
        pg.insert_text((40, 80), "營業收入淨額 5,839 10,125 12,108",
                       fontname="china-t")
        pg.insert_text((40, 100), "每股盈餘 1.20 2.40 3.10", fontname="china-t")
        doc.save(str(tdp / "6873_2024-05-06_元大.pdf"))
        doc.close()
        dbp = tdp / "x.duckdb"
        c0 = duckdb.connect(str(dbp))
        c0.execute("CREATE TABLE vrn_report_basic(report_file VARCHAR,"
                   " ticker VARCHAR, report_date VARCHAR)")
        c0.execute("INSERT INTO vrn_report_basic VALUES "
                   "('6873_2024-05-06_元大','6873','2024-05-06')")
        c0.execute("CREATE TABLE vrn_report_metrics(report_file VARCHAR,"
                   " metric VARCHAR, period VARCHAR, status VARCHAR,"
                   " value DOUBLE, raw_text VARCHAR)")
        c0.execute("INSERT INTO vrn_report_metrics VALUES "
                   "('6873_2024-05-06_元大','eps','2024','STATED',2.40,''),"
                   "('6873_2024-05-06_元大','eps','2025','ESTIMATE',9.90,'')")
        c0.close()
        rc = run(tdp, dbp)
        con = duckdb.connect(str(dbp))
        got = dict(con.execute(
            "SELECT period, state FROM vrn_report_crosscheck "
            "WHERE dimension='eps'").fetchall())
        onlyt = con.execute(
            "SELECT count(*) FROM vrn_report_crosscheck WHERE "
            "dimension='revenue' AND state='ONLY_TABLE'").fetchone()[0]
        tk = con.execute(
            "SELECT state FROM vrn_report_crosscheck WHERE "
            "dimension='ticker_on_fin_page'").fetchone()
        dt = con.execute(
            "SELECT state, note FROM vrn_report_crosscheck WHERE "
            "dimension='report_date_vs_periods'").fetchone()
        n1 = con.execute("SELECT count(*) FROM vrn_report_crosscheck").fetchone()[0]
        run(tdp, dbp)                               # 冪等重跑
        n2 = con.execute("SELECT count(*) FROM vrn_report_crosscheck").fetchone()[0]
        con.close()
        chk("⑫ 三方對照端到端(首頁 eps 2024=2.40 對表格 2.40=AGREE;"
            "2025 首頁 9.90 對表格 3.10=DIVERGE)",
            rc == 0 and got.get("2024") == "AGREE"
            and got.get("2025") == "DIVERGE", f"{got}")
        chk("⑬ 表格獨有科目 ONLY_TABLE + 檔名↔財報頁 ticker + 報告日 vs 期間",
            onlyt >= 1 and tk is not None
            and tk[0].startswith("TICKER_")
            and dt is not None and dt[0] == "DATE_CONSISTENT", f"{tk} {dt}")
        chk("⑭ 對照冪等(派生層重算不倍增)", n1 == n2 and n1 > 0)
    with tempfile.TemporaryDirectory() as td2:
        dbp2 = Path(td2) / "y.duckdb"
        c1 = duckdb.connect(str(dbp2))
        c1.execute("CREATE TABLE vrn_report_financial(report_file VARCHAR,"
                   " page INTEGER, canonical VARCHAR, raw_label VARCHAR,"
                   " period VARCHAR, status VARCHAR, value DOUBLE,"
                   " raw_text VARCHAR)")
        r0 = crosscheck(c1, do_print=False)
        c1.close()
        chk("⑮ ENG073 兩表缺=誠實略過不 crash(指路先跑 ENG073)",
            r0.get("skipped") == "NO_ENG073")
    # ⑯ 批425:run 動詞的 --db 必須真的傳進 run()(v0102 寫死 None)。
    # 攔真實呼叫來證明,不掃原始碼字串。
    _seen = {}
    _real_run, _real_argv = globals()["run"], sys.argv
    try:
        globals()["run"] = lambda src=None, db=None, cross=True: (_seen.update(
            {"src": src, "db": db, "cross": cross}) or 0)
        sys.argv = ["x", "run", "--dir", "/tmp/_d_", "--db", "/tmp/_b_.duckdb"]
        _rc = main()
    finally:
        globals()["run"], sys.argv = _real_run, _real_argv
    chk("⑯ run 動詞的 --db 真的接到 run()(批425:v0102 是 run(d, None, ...),"
        "db 那格寫死 None,`run --db X` 永遠寫進預設庫;--db 只有 --crosscheck 分支"
        "解析得到=更難察覺。實跑證據:ENG074 印「對照 28 列」而收尾讀 X 是「已對照 0/5」)",
        _rc == 0 and str(_seen.get("db")) == "/tmp/_b_.duckdb"
        and str(_seen.get("src")) == "/tmp/_d_" and _seen.get("cross") is True,
        f"(src={_seen.get('src')} db={_seen.get('db')} cross={_seen.get('cross')})")

    print(f"  [計] 十六檢 OK {16 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def _argval(args: list, flag: str) -> Path | None:
    """旗標取值(缺值=誠實 None,不 IndexError);批425 與 ENG072/ENG073 同慣例"""
    if flag not in args:
        return None
    i = args.index(flag) + 1
    if i >= len(args) or args[i].startswith("--"):
        print(f"[旗標] {flag} 後面沒有值=忽略(誠實提示,不當作預設)")
        return None
    return Path(args[i])


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== 財報頁表格擷取器(VRN_ENG074 v0103)· 十六檢自測(零網路)===")
        return selftest()
    if "--status" in args:
        return status()
    if "--crosscheck" in args:                      # 批403:單獨重算三方對照
        import duckdb
        dbp = _resolve_db(Path(args[args.index("--db") + 1])
                          if "--db" in args else None)
        if dbp is None:
            return 2
        con = duckdb.connect(str(dbp))
        r = crosscheck(con)
        con.close()
        return 2 if r.get("skipped") else 0
    if args and args[0] == "run":
        # 批425(沙盒實跑整條鏈時發現):v0102 這裡是 run(d, None, ...) ——
        # db 那一格**寫死 None**,所以 `run --db X` 永遠寫進預設庫。
        # (--db 在 --crosscheck 分支有解析,唯獨 run 這條沒有=更難察覺。)
        # 實跑證據:ENG074 印「對照 5 件 → 28 列」,收尾閘讀 X 卻是「已對照 0/5」,
        # 因為 28 列根本不在 X 裡。與批423 $StageTimeoutSec、ENG073 --dir/--db、
        # MDL141 --db 同一家族:參數在、線沒接。
        d = _argval(args, "--dir")
        return run(d, _argval(args, "--db"), "--no-cross" not in args)
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main())
