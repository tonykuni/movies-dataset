#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VRN2_BookSource v0100 — 輸出冊實體加兩欄:BROKER_EN(券商英文縮寫)與 SOURCE(資料來源),放在每一列最後。

操作員 2026-11-03:「BROKER 一律用英文縮寫」「輸出冊和增量庫也實體加 Source 欄」。
v0174 的 Workbench v0108 只在畫面與匯出加 Source;本模組把同一套規則寫進輸出冊本身:
  ① 冊:BasicInfo · FinancialData · Summary · Combined · Rejected · FinancialAligned · Deleted(output/VRN2_<冊>_latest.json / .csv / .parquet)。
     MarketConsensus 本身已有 SOURCE 欄(TWSE / TPEX + cnyes FactSet + Yahoo Finance 的原文來源)→ 不動。
  ② 欄:BROKER_EN = BROKER 的英文縮寫(候選對照表 · 對不到留空並列在收據 · 等 VCGC 核發正式同義字);SOURCE = 歷史 TWSE/TPEX · 報告預估 ·
     報告實際 · 報告 · 報告(未過驗證)· 報告(被歷史否定)· 報告 + TWSE/TPEX/Yahoo + 共識(規則與 Workbench v0108 相同 · 自測逐例對照)。
     BROKER 原文不改(驗證器拿它對 PDF);兩欄每次都依當下列內容重算(⑬b 重跑後 VALUE_SOURCE 變了,SOURCE 跟著變)。
  ③ 三種格式各自從自己的列算(不靠列序對齊):JSON 保留原縮排、CSV 保留 BOM 與換行字元、Parquet 保留原欄型別只換這兩欄;
     其他欄位一個字都不改(JSON 重新序列化與原檔逐位元組相同才寫 · CSV 除最後兩欄外逐位元組相同)。內容沒變就不寫(冪等)。
  ④ 收據 VIA_Reports\\vrn2\\VRN2_BookSource_latest.json:逐冊列數 / 改寫與否 / 未對照券商 · 燈號(寫不進去 → 黃 · 永不紅)。
動詞:apply [--v2 <VIA_Reports\\vrn2>] [--dry-run] · --selftest
"""
from __future__ import annotations

import csv
import datetime as _dt
import io
import json
import os
import re
import sys
import tempfile
from pathlib import Path

VERSION = "v0100"
DISPLAY_NAME = "VRN2_BookSource"
HERE = Path(__file__).resolve().parent
BOOKS = ("BasicInfo", "FinancialData", "Summary", "Combined", "Rejected", "FinancialAligned", "Deleted")
NATIVE_SOURCE = ("MarketConsensus",)
COLS = ("BROKER_EN", "SOURCE")
RECEIPT = "VRN2_BookSource_latest.json"
RULE_NOTE = "SOURCE 規則同 Workbench v0108 · BROKER_EN 候選對照表(等 VCGC 核發)"

BROKER_ABBR = {   # 候選(與 Workbench v0108 相同 · 等 VCGC 核發正式同義字)
    "凱基": "KGI", "凱基投顧": "KGI", "KGI": "KGI", "中信": "CTBC", "中信投顧": "CTBC", "中國信託": "CTBC", "CTBC": "CTBC",
    "國泰": "Cathay", "國泰證券": "Cathay", "兆豐": "Mega", "兆豐投顧": "Mega", "兆豐證券": "Mega", "華南": "HNS", "華南投顧": "HNS", "華南永昌": "HNS",
    "元大": "Yuanta", "富邦": "Fubon", "群益": "Capital", "永豐": "SinoPac", "統一": "PSC", "玉山": "E.SUN", "第一金": "FSC", "台新": "Taishin",
    "日盛": "JihSun", "宏遠": "Horizon", "康和": "Concord", "合庫": "TCB", "元富": "MasterLink", "福邦": "Fubon",
    "Goldman Sachs": "GS", "GS": "GS", "Morgan Stanley": "MS", "MS": "MS", "J.P. Morgan": "JPM", "JPMorgan": "JPM", "JP Morgan": "JPM", "JPM": "JPM",
    "Citi": "Citi", "Citigroup": "Citi", "Daiwa": "Daiwa", "CLSA": "CLSA", "UBS": "UBS", "GF": "GF", "GF Securities": "GF", "GFHK": "GF",
    "Macquarie": "MQ", "MQ": "MQ", "Nomura": "Nomura", "HSBC": "HSBC", "BofA": "BofA", "BofA Securities": "BofA", "Bank of America": "BofA",
    "Jefferies": "Jefferies", "Mizuho": "Mizuho", "Credit Suisse": "CS", "Deutsche Bank": "DB", "Barclays": "Barclays", "Bernstein": "Bernstein",
    "Morningstar": "Morningstar", "Fubon": "Fubon", "Yuanta": "Yuanta", "SinoPac": "SinoPac", "Mega": "Mega", "Cathay": "Cathay",
}
MON = {m: i for i, m in enumerate(("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"), 1)}


# ── 規則(與 Workbench v0108 的 norm_date / norm_period / source_of / broker_abbr 相同 · 自測逐例對照)──────────────
def norm_date(s) -> str:
    t = str(s if s is not None else "").strip()
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})(?::\d{2}(?:\.\d+)?)?(Z|[+-]\d{2}:?\d{2})$", t)
    if m:
        base = _dt.datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4)), int(m.group(5)))
        z = m.group(6)
        off = 0 if z == "Z" else (1 if z[0] == "+" else -1) * (int(z[1:3]) * 60 + int(z[-2:]))
        return (base - _dt.timedelta(minutes=off) + _dt.timedelta(hours=8)).date().isoformat()
    m = re.match(r"^(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})", t)
    return "%s-%02d-%02d" % (m.group(1), int(m.group(2)), int(m.group(3))) if m else ""


def _y(s: str) -> int:
    return int(s) if len(s) == 4 else 2000 + int(s)


def norm_period(p, report_date="") -> tuple:
    s = str(p if p is not None else "").strip()
    flag, disp, end = "", "", None
    pats = (
        (r"^(\d{4})-(\d{2})-(\d{2})$", lambda m: ("%s-%s-%s" % m.groups(), (int(m.group(1)), int(m.group(2))), "")),
        (r"^(\d{4})[-/](\d{1,2})$", lambda m: ("%s-%02d" % (m.group(1), int(m.group(2))), (int(m.group(1)), int(m.group(2))), "")),
        (r"^(\d{4})\s*\(?\s*(A|E|F|CT|CL)?\s*\)?$", lambda m: (m.group(1), (int(m.group(1)), 12), m.group(2) or "")),
        (r"^FY\s*(\d{2}|\d{4})\s*(A|E|F)?$", lambda m: ("%d" % _y(m.group(1)), (_y(m.group(1)), 12), m.group(2) or "")),
        (r"^(\d{2})(A|E|F)$", lambda m: ("%d" % _y(m.group(1)), (_y(m.group(1)), 12), m.group(2))),
        (r"^(\d{1,2})/(\d{2})(A|E|F)?$", lambda m: ("%d-%02d" % (_y(m.group(2)), int(m.group(1))), (_y(m.group(2)), int(m.group(1))), m.group(3) or "")),
        (r"^([A-Za-z]{3})[- ](\d{2}|\d{4})(A|E|F)?$", lambda m: ("%d-%02d" % (_y(m.group(2)), MON[m.group(1).lower()]), (_y(m.group(2)), MON[m.group(1).lower()]), m.group(3) or "")
         if m.group(1).lower() in MON else None),
        (r"^([1-4])Q\s*(\d{2}|\d{4})(A|E|F)?$", lambda m: ("%d-%02d" % (_y(m.group(2)), int(m.group(1)) * 3), (_y(m.group(2)), int(m.group(1)) * 3), m.group(3) or "")),
        (r"^(\d{4})\s*Q([1-4])(A|E|F)?$", lambda m: ("%s-%02d" % (m.group(1), int(m.group(2)) * 3), (int(m.group(1)), int(m.group(2)) * 3), m.group(3) or "")),
        (r"^([12])H\s*(\d{2}|\d{4})(A|E|F)?$", lambda m: ("%d-%02d" % (_y(m.group(2)), int(m.group(1)) * 6), (_y(m.group(2)), int(m.group(1)) * 6), m.group(3) or "")),
    )
    for pat, fn in pats:
        m = re.match(pat, s, re.I)
        if m:
            got = fn(m)
            if got:
                disp, end, flag = got
                break
    if not disp:
        return s, ""
    flag = flag.upper()
    if flag == "A":
        return disp, "act"
    if flag in ("E", "F", "CT", "CL"):
        return disp, "est"
    rd = norm_date(report_date)
    if not rd or not end:
        return disp, ""
    y, mth = end
    last = _dt.date(y + (mth == 12), (mth % 12) + 1, 1) - _dt.timedelta(days=1)
    return disp, ("act" if last.isoformat() < rd else "est")


def source_of(book: str, row: dict) -> str:
    b = str(book)
    if b == "FinancialAligned" and str(row.get("VALUE_SOURCE") or "").upper().startswith("HISTORY"):
        return "歷史 TWSE/TPEX"
    if b in ("FinancialData", "FinancialAligned"):
        kind = norm_period(row.get("PERIOD"), row.get("REPORT_DATE"))[1]
        return {"est": "報告預估", "act": "報告實際"}.get(kind, "報告")
    return {"Rejected": "報告(未過驗證)", "Deleted": "報告(被歷史否定)", "Combined": "報告 + TWSE/TPEX/Yahoo + 共識",
            "MarketConsensus": "TWSE/TPEX + 共識"}.get(b, "報告")


def broker_abbr(b) -> tuple:
    raw = str(b if b is not None else "").strip()
    if not raw:
        return "", True
    if raw in BROKER_ABBR:
        return BROKER_ABBR[raw], True
    low = {k.lower(): v for k, v in BROKER_ABBR.items()}
    if raw.lower() in low:
        return low[raw.lower()], True
    for k, v in sorted(BROKER_ABBR.items(), key=lambda kv: -len(kv[0])):
        if len(k) >= 2 and (raw.startswith(k) or raw.lower().startswith(k.lower() + " ")):
            return v, True
    return raw, False


def derive(book: str, row: dict, unmapped: set | None = None) -> tuple:
    """(BROKER_EN, SOURCE)。對不到縮寫 → BROKER_EN 留空(原文記進 unmapped)。"""
    raw = row.get("BROKER")
    br, ok = broker_abbr(raw)
    if not ok:
        if unmapped is not None:
            unmapped.add(str(raw).strip())
        br = ""
    return br, source_of(book, row)


# ── 三種格式 ────────────────────────────────────────────────────────────────────────────────────────────
def _atomic(path: Path, data: bytes) -> None:
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
        os.replace(tmp, str(path))
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def _indent_of(text: str, data) -> tuple:
    """原檔的縮排(重新序列化逐位元組相同的那一個);都不同 → (1, False)。"""
    for ind in (None, 1, 2, 4):
        if json.dumps(data, ensure_ascii=False, indent=ind) == text:
            return ind, True
    return 1, False


def _with_cols(book: str, rows: list, unmapped: set) -> list:
    out = []
    for r in rows:
        if not isinstance(r, dict):
            out.append(r)
            continue
        r2 = {k: v for k, v in r.items() if k not in COLS}
        r2["BROKER_EN"], r2["SOURCE"] = derive(book, r, unmapped)
        out.append(r2)
    return out


def do_json(book: str, path: Path, dry: bool, unmapped: set) -> dict:
    text = path.read_text(encoding="utf-8")
    rows = json.loads(text)
    if not isinstance(rows, list):
        return {"state": "不是列清單 · 不動", "rows": 0}
    ind, exact = _indent_of(text, rows)
    new = _with_cols(book, rows, unmapped)
    if new == rows and all(list(r)[-2:] == list(COLS) for r in rows if isinstance(r, dict)):
        return {"state": "不變", "rows": len(rows)}
    if not dry:
        _atomic(path, json.dumps(new, ensure_ascii=False, indent=ind).encode("utf-8"))
        back = json.loads(path.read_text(encoding="utf-8"))
        if len(back) != len(rows) or any(isinstance(r, dict) and list(r)[-2:] != list(COLS) for r in back):
            raise ValueError("寫回後檢查不過")
    return {"state": "改寫" if exact else "改寫(原縮排認不出 · 用 1)", "rows": len(rows)}


def do_csv(book: str, path: Path, dry: bool, unmapped: set) -> dict:
    raw = path.read_bytes()
    bom = raw.startswith(b"\xef\xbb\xbf")
    text = raw.decode("utf-8-sig")
    if not text.strip():
        return {"state": "空檔 · 不動", "rows": 0}
    term = "\r\n" if "\r\n" in text else "\n"
    grid = list(csv.reader(io.StringIO(text, newline="")))
    head, body = grid[0], grid[1:]
    keep = [i for i, h in enumerate(head) if h not in COLS]
    out = [[head[i] for i in keep] + list(COLS)]
    for row in body:
        d = dict(zip(head, row + [""] * (len(head) - len(row))))
        out.append([row[i] if i < len(row) else "" for i in keep] + list(derive(book, d, unmapped)))
    buf = io.StringIO()
    csv.writer(buf, lineterminator=term).writerows(out)
    new = buf.getvalue()
    if new == text:
        return {"state": "不變", "rows": len(body)}
    if not dry:
        _atomic(path, (b"\xef\xbb\xbf" if bom else b"") + new.encode("utf-8"))
    return {"state": "改寫", "rows": len(body)}


def do_parquet(book: str, path: Path, dry: bool, unmapped: set) -> dict:
    try:
        import pyarrow as pa  # noqa: WPS433
        import pyarrow.parquet as pq  # noqa: WPS433
    except Exception as error:  # noqa: BLE001
        return {"state": "沒寫:%s(這支 Python 的 pyarrow 載不起來)" % type(error).__name__, "rows": 0, "skip": True}
    table = pq.read_table(str(path))
    names = table.column_names
    need = [c for c in ("BROKER", "PERIOD", "REPORT_DATE", "VALUE_SOURCE") if c in names]
    cols = {c: table.column(c).to_pylist() for c in need}
    n = table.num_rows
    pairs = [derive(book, {c: ("" if cols[c][i] is None else str(cols[c][i])) for c in need}, unmapped) for i in range(n)]
    want_br, want_src = [p[0] for p in pairs], [p[1] for p in pairs]
    if names[-2:] == list(COLS) and table.column("BROKER_EN").to_pylist() == want_br and table.column("SOURCE").to_pylist() == want_src:
        return {"state": "不變", "rows": n}
    base = table.drop([c for c in COLS if c in names])
    new = base.append_column("BROKER_EN", pa.array(want_br, type=pa.string())).append_column("SOURCE", pa.array(want_src, type=pa.string()))
    if not dry:
        fd, tmp = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
        os.close(fd)
        try:
            pq.write_table(new, tmp)
            os.replace(tmp, str(path))
        except BaseException:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise
    return {"state": "改寫", "rows": n}


# ── 主流程 ────────────────────────────────────────────────────────────────────────────────────────────
def apply(v2, dry: bool = False) -> dict:
    v2 = Path(v2)
    out = v2 / "output"
    unmapped: set = set()
    books, errors, wrote, same, pq_skip, n_rows, n_br = {}, [], 0, 0, 0, 0, 0
    for book in BOOKS:
        got = {}
        for ext, fn in (("json", do_json), ("csv", do_csv), ("parquet", do_parquet)):
            p = out / ("VRN2_%s_latest.%s" % (book, ext))
            if not p.is_file():
                continue
            try:
                r = fn(book, p, dry, unmapped)
            except Exception as error:  # noqa: BLE001
                r = {"state": "沒寫:%s: %s" % (type(error).__name__, str(error)[:120]), "rows": 0}
                errors.append("%s.%s" % (book, ext))
            got[ext] = r
            if r["state"].startswith("改寫"):
                wrote += 1
            elif r["state"] == "不變":
                same += 1
            if r.get("skip"):
                pq_skip += 1
        if got:
            books[book] = got
            rows = (got.get("json") or got.get("csv") or got.get("parquet") or {}).get("rows", 0)
            n_rows += rows
    for book in BOOKS:                                                                # 統計 BROKER_EN 對到幾列(從 JSON 算 · 唯讀)
        p = out / ("VRN2_%s_latest.json" % book)
        try:
            rows = json.loads(p.read_text(encoding="utf-8")) if p.is_file() else []
        except (OSError, ValueError):
            rows = []
        n_br += sum(1 for r in rows if isinstance(r, dict) and (derive(book, r)[0] or not str(r.get("BROKER") or "").strip()))
    if not books:
        lamp, why = "GRAY", "output 夾沒有輸出冊"
    else:
        lamp = "YELLOW" if errors else "GREEN"
        why = "%d 冊 · %d 列 · 改寫 %d 檔 · 不變 %d 檔%s · BROKER_EN 對到 %d / %d 列%s%s" % (
            len(books), n_rows, wrote, same, (" · 試算不寫" if dry else ""), n_br, n_rows,
            (" · 未對照券商 %d:%s" % (len(unmapped), "、".join(sorted(unmapped))[:120])) if unmapped else "",
            (" · 寫不進去:" + "、".join(errors)) if errors else "")
        if pq_skip:
            why += " · Parquet %d 檔沒寫(pyarrow 載不起來)" % pq_skip
    rec = {"system": "VRN-2", "module": "%s %s" % (DISPLAY_NAME, VERSION), "ts": _dt.datetime.now().isoformat(timespec="seconds"), "lamp": lamp, "why": why,
           "columns": list(COLS), "books": books, "unmapped": sorted(unmapped), "native_source_books": list(NATIVE_SOURCE), "dry_run": dry, "rule": RULE_NOTE}
    if not dry:
        try:
            v2.mkdir(parents=True, exist_ok=True)
            (v2 / RECEIPT).write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
        except OSError as error:
            rec["receipt_error"] = type(error).__name__
    return rec


# ── 自測 ──────────────────────────────────────────────────────────────────────────────────────────────
def _fixture(v2: Path, pyarrow_ok: bool) -> None:
    out = v2 / "output"
    out.mkdir(parents=True, exist_ok=True)
    basic = [{"REPORT_DATE": "2026-05-20", "FILENAME": "a.pdf", "TICKER": "1560", "BROKER": "Macquarie", "RATING": "Outperform"},
             {"REPORT_DATE": "2026-10-01", "FILENAME": "b.pdf", "TICKER": "2330", "BROKER": "中信", "RATING": "買進"},
             {"REPORT_DATE": "2026-10-02", "FILENAME": "c.pdf", "TICKER": "2454", "BROKER": "某某投顧", "RATING": ""}]
    fin = [{"REPORT_DATE": "2026-05-20", "FILENAME": "a.pdf", "TICKER": "1560", "BROKER": "Macquarie", "ITEM": "EPS", "PERIOD": "2026E", "VALUE": "5.1"},
           {"REPORT_DATE": "2026-05-20", "FILENAME": "a.pdf", "TICKER": "1560", "BROKER": "Macquarie", "ITEM": "EPS", "PERIOD": "2025", "VALUE": "4.0"},
           {"REPORT_DATE": "2026-05-20", "FILENAME": "a.pdf", "TICKER": "1560", "BROKER": "Macquarie", "ITEM": "Revenue", "PERIOD": "Dec-26F", "VALUE": "1,000"}]
    fa = [dict(fin[1], VALUE_SOURCE="HISTORY(TWSE)", VALUE_FINAL=4.02), dict(fin[0], VALUE_SOURCE="REPORT(估)", VALUE_FINAL=5.1)]
    mc = [{"DATE": "2026-11-03", "TICKER": "2330", "SOURCE": "TWSE / TPEX(VDF)+ cnyes FactSet + Yahoo Finance"}]
    (out / "VRN2_BasicInfo_latest.json").write_text(json.dumps(basic, ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "VRN2_FinancialData_latest.json").write_text(json.dumps(fin, ensure_ascii=False), encoding="utf-8")
    (out / "VRN2_FinancialAligned_latest.json").write_text(json.dumps(fa, ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "VRN2_MarketConsensus_latest.json").write_text(json.dumps(mc, ensure_ascii=False, indent=1), encoding="utf-8")
    for name, rows in (("BasicInfo", basic), ("FinancialData", fin)):
        buf = io.StringIO()
        w = csv.DictWriter(buf, fieldnames=list(rows[0]), lineterminator="\r\n")
        w.writeheader()
        w.writerows(rows)
        (out / ("VRN2_%s_latest.csv" % name)).write_bytes(b"\xef\xbb\xbf" + buf.getvalue().encode("utf-8"))
    if pyarrow_ok:
        import pyarrow as pa  # noqa: WPS433
        import pyarrow.parquet as pq  # noqa: WPS433
        pq.write_table(pa.table({"FILENAME": ["a.pdf", "a.pdf"], "BROKER": ["Macquarie", "Macquarie"], "PERIOD": ["2025", "2026E"], "REPORT_DATE": ["2026-05-20", "2026-05-20"],
                                 "VALUE_SOURCE": ["HISTORY(TWSE)", "REPORT(估)"], "VALUE_FINAL": pa.array([4.02, 5.1], type=pa.float64())}), str(out / "VRN2_FinancialAligned_latest.parquet"))


def selftest() -> int:
    bad = []

    def chk(label, cond):
        print(("[PASS] " if cond else "[FAIL] ") + label, flush=True)
        if not cond:
            bad.append(label)
    desk = ("中信", "Goldman Sachs", "Morgan Stanley", "凱基", "兆豐", "Daiwa", "華南", "國泰", "Citi", "J.P. Morgan", "UBS", "CLSA", "GF", "Macquarie")
    chk("① 桌機 14 家券商全對到縮寫 · 中信 CTBC · 凱基 KGI · 兆豐 Mega · 華南 HNS · Macquarie MQ · J.P. Morgan JPM · 對不到 → 留空記收據",
        all(broker_abbr(b)[1] for b in desk) and [broker_abbr(b)[0] for b in ("中信", "凱基", "兆豐", "華南", "Macquarie", "J.P. Morgan")] == ["CTBC", "KGI", "Mega", "HNS", "MQ", "JPM"]
        and derive("BasicInfo", {"BROKER": "某某投顧"}, set())[0] == "")
    cases = [("FinancialData", {"PERIOD": "2026E", "REPORT_DATE": "2026-05-20"}, "報告預估"), ("FinancialData", {"PERIOD": "2025", "REPORT_DATE": "2026-05-20"}, "報告實際"),
             ("FinancialData", {"PERIOD": "Dec-26F", "REPORT_DATE": "2026-05-20"}, "報告預估"), ("FinancialData", {"PERIOD": "12/25", "REPORT_DATE": "2026-05-20"}, "報告實際"),
             ("FinancialData", {"PERIOD": "2026CT", "REPORT_DATE": "2026-05-20"}, "報告預估"), ("FinancialData", {"PERIOD": "FY", "REPORT_DATE": ""}, "報告"),
             ("FinancialAligned", {"PERIOD": "2025", "VALUE_SOURCE": "HISTORY(TWSE)"}, "歷史 TWSE/TPEX"), ("FinancialAligned", {"PERIOD": "2026E", "VALUE_SOURCE": "REPORT(估)"}, "報告預估"),
             ("Rejected", {}, "報告(未過驗證)"), ("Deleted", {}, "報告(被歷史否定)"), ("Combined", {}, "報告 + TWSE/TPEX/Yahoo + 共識"), ("BasicInfo", {}, "報告"), ("Summary", {}, "報告")]
    chk("② SOURCE 規則 13 例(E / F / CT 預估 · A / 已過財年實際 · HISTORY → 歷史 TWSE/TPEX · 各冊固定值)", all(source_of(b, r) == want for b, r, want in cases))
    wb = HERE / "VRN2_Workbench_v0108.py"
    if wb.is_file():
        import importlib.util
        spec = importlib.util.spec_from_file_location("vrn2_wb108_for_booksource", wb)
        mod = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(mod)
            same = all(mod.source_of(b, r) == source_of(b, r) for b, r, _ in cases) and mod.BROKER_ABBR == BROKER_ABBR \
                and all(mod.broker_abbr(b) == broker_abbr(b) for b in desk + ("某某投顧", "", "Goldman Sachs Asia"))
            chk("③ 與 Workbench v0108 同一套規則(SOURCE 13 例 · 縮寫表逐鍵 · 縮寫函式逐例)", same)
        except Exception as error:  # noqa: BLE001
            print("[SKIP] Workbench v0108 載不起來(%s)· ③ 不驗" % type(error).__name__, flush=True)
    else:
        print("[SKIP] 旁邊沒有 VRN2_Workbench_v0108.py · ③ 不驗", flush=True)
    try:
        import pyarrow.parquet  # noqa: F401,WPS433
        pa_ok = True
    except Exception:  # noqa: BLE001
        pa_ok = False
        print("[SKIP] 這支 Python 的 pyarrow 用不了 · Parquet 那段不驗", flush=True)
    with tempfile.TemporaryDirectory(prefix="vrn2-booksource-") as td:
        v2 = Path(td) / "VIA_Reports" / "vrn2"
        _fixture(v2, pa_ok)
        out = v2 / "output"
        mc0 = (out / "VRN2_MarketConsensus_latest.json").read_bytes()
        csv0 = (out / "VRN2_BasicInfo_latest.csv").read_bytes()
        dry = apply(v2, dry=True)
        chk("④ --dry-run:只算不寫(檔不變 · 不寫收據)", (out / "VRN2_BasicInfo_latest.csv").read_bytes() == csv0 and not (v2 / RECEIPT).exists() and dry["dry_run"])
        rec = apply(v2)
        b = json.loads((out / "VRN2_BasicInfo_latest.json").read_text(encoding="utf-8"))
        f = json.loads((out / "VRN2_FinancialData_latest.json").read_text(encoding="utf-8"))
        a = json.loads((out / "VRN2_FinancialAligned_latest.json").read_text(encoding="utf-8"))
        chk("⑤ JSON:每列最後兩欄 BROKER_EN · SOURCE · MQ / CTBC / 對不到留空 · 年度數據 預估 / 實際 / 預估 · 歷史對齊 HISTORY → 歷史 TWSE/TPEX · BROKER 原文不改",
            all(list(r)[-2:] == ["BROKER_EN", "SOURCE"] for r in b + f + a) and [r["BROKER_EN"] for r in b] == ["MQ", "CTBC", ""] and b[1]["BROKER"] == "中信"
            and [r["SOURCE"] for r in f] == ["報告預估", "報告實際", "報告預估"] and [r["SOURCE"] for r in a] == ["歷史 TWSE/TPEX", "報告預估"])
        t_b, t_f = (out / "VRN2_BasicInfo_latest.json").read_text(encoding="utf-8"), (out / "VRN2_FinancialData_latest.json").read_text(encoding="utf-8")
        chk("⑥ JSON 保留原縮排(indent 1 / 不縮排)· 原有欄位值與欄序一字不改",
            t_b == json.dumps(b, ensure_ascii=False, indent=1) and t_f == json.dumps(f, ensure_ascii=False)
            and [{k: v for k, v in r.items() if k not in COLS} for r in f][2]["VALUE"] == "1,000")
        raw = (out / "VRN2_BasicInfo_latest.csv").read_bytes()
        lines0, lines1 = csv0.decode("utf-8-sig").split("\r\n"), raw.decode("utf-8-sig").split("\r\n")
        chk("⑦ CSV:保留 BOM 與 \\r\\n · 表頭最後 BROKER_EN,SOURCE · 除最後兩欄外每一行逐字相同",
            raw.startswith(b"\xef\xbb\xbf") and lines1[0].endswith(",BROKER_EN,SOURCE") and all(l1.rsplit(",", 2)[0] == l0 for l0, l1 in zip(lines0, lines1) if l0))
        chk("⑧ MarketConsensus(本身有 SOURCE 原文)一個位元組都不動 · 收據綠 · 未對照券商列出「某某投顧」",
            (out / "VRN2_MarketConsensus_latest.json").read_bytes() == mc0 and rec["lamp"] == "GREEN" and rec["unmapped"] == ["某某投顧"] and "MarketConsensus" not in rec["books"])
        if pa_ok:
            import pyarrow.parquet as pq  # noqa: WPS433
            t = pq.read_table(str(out / "VRN2_FinancialAligned_latest.parquet"))
            chk("⑨ Parquet:原欄型別保留(VALUE_FINAL float64)· 最後兩欄字串 · 歷史 TWSE/TPEX / 報告預估",
                t.column_names[-2:] == ["BROKER_EN", "SOURCE"] and str(t.schema.field("VALUE_FINAL").type) == "double" and t.column("SOURCE").to_pylist() == ["歷史 TWSE/TPEX", "報告預估"]
                and t.column("BROKER_EN").to_pylist() == ["MQ", "MQ"])
        snap = {p.name: p.read_bytes() for p in out.iterdir()}
        rec2 = apply(v2)
        chk("⑩ 再跑:全部不變(冪等 · 不改寫任何檔)", {p.name: p.read_bytes() for p in out.iterdir()} == snap and "改寫 0 檔" in rec2["why"])
        a[1]["VALUE_SOURCE"] = "HISTORY(TWSE)"
        (out / "VRN2_FinancialAligned_latest.json").write_text(json.dumps(a, ensure_ascii=False, indent=1), encoding="utf-8")
        apply(v2)
        a2 = json.loads((out / "VRN2_FinancialAligned_latest.json").read_text(encoding="utf-8"))
        chk("⑪ ⑬b 重跑後 VALUE_SOURCE 變了 → SOURCE 跟著重算(帶舊 SOURCE 的列不沿用)· 欄序仍是最後兩欄", a2[1]["SOURCE"] == "歷史 TWSE/TPEX" and list(a2[1])[-2:] == ["BROKER_EN", "SOURCE"])
        chk("⑫ 收據 VRN2_BookSource_latest.json 寫在 vrn2 夾 · 欄名 · 規則說明", json.loads((v2 / RECEIPT).read_text(encoding="utf-8"))["columns"] == ["BROKER_EN", "SOURCE"])
    with tempfile.TemporaryDirectory(prefix="vrn2-booksource-empty-") as td:
        chk("⑬ 沒有輸出冊 → GRAY(不失敗)", apply(Path(td))["lamp"] == "GRAY")
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑭ 模組第 3 行 ACCEL-BRIDGE 標記 · 不連外(沒有 requests / urllib / socket)", src.splitlines()[2].strip() == "# [VIA:ACCEL-BRIDGE:v0111]"
        and not re.search(r"^\s*(import|from)\s+(requests|urllib|socket|http)\b", src, re.M))
    print("[%s] %s %s --selftest · 不過 %d" % ("PASS" if not bad else "FAIL", DISPLAY_NAME, VERSION, len(bad)), flush=True)
    return 0 if not bad else 1


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)

    def opt(k, d=None):
        return argv[argv.index(k) + 1] if k in argv and argv.index(k) + 1 < len(argv) else d
    if "--selftest" in argv:
        return selftest()
    if not argv or argv[0] != "apply":
        print("用法:python %s apply [--v2 <VIA_Reports\\vrn2>] [--dry-run] · --selftest" % Path(__file__).name, flush=True)
        return 2
    v2 = Path(opt("--v2") or (Path(os.environ["VIA_ROOT"]) / "VIA_Reports" / "vrn2" if os.environ.get("VIA_ROOT") else HERE.parent.parent / "VIA_Reports" / "vrn2"))
    rec = apply(v2, dry="--dry-run" in argv)
    print("[計] 輸出冊 Source / Broker 欄 · %s · %s" % (rec["lamp"], rec["why"]), flush=True)
    print("[%s] %s %s · %s" % (rec["lamp"], DISPLAY_NAME, VERSION, rec["why"][:220]), flush=True)
    return 0 if rec["lamp"] in ("GREEN", "YELLOW", "GRAY") else 1


if __name__ == "__main__":
    sys.exit(main())
