#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ===== [VRN:ID:v0100] VRN-ENG018 · VRN_TruthMatrix_v0100 v0100 · ENGINE =====
# AST 注入（只加註解，AST 不變）：類別 0 · 函式 23；逐一編號在 ssot/VRN_ID_SSOT_v0100.json
# ===== [VRN:ID:END] =====
"""
VRN_TruthMatrix v0100 -- the mother's first-page matrix (a pasted table: one report per row, 代號 / 券商 / 報告日 / 官方證券名 /
TP / 評等 / gate verdicts) turned into the G11 truth file the VRN loop already reads (`run --truth`).

Operator 2026-10-12: pasted 「VRN 個股報告解讀矩陣 · VIA_VRN_FirstPageEngine v0113 · 2026-09-11 · 64 件」 as the known answers.
The matrix is a third reader of the same reports; what it states is the truth row, what it does not state is marked
`unknown` so G11 does not judge it (a matrix with no 現價 column must not make every current price a false positive).

Rules
- The truth file is written on the operator's machine, never inside the VRN tree (the tree refuses it): 真值檔只在操作員手上。
- Brokers go through the merged book (ssot/VRN_TickerRecord_SSOT_v0100.json): GOLDMAN -> GS, MORGANSTANLEY -> MS; an alias two
  books dispute (a list) is kept as `accept.broker`, both readings accepted.
- The rating level is the matrix's word (BUY / HOLD / SELL / NOT_RATED; ADD counts as BUY as in the evidence core); G11 compares
  the engine's printed word through the same level table, the engine output stays as printed.
- A date is judged only when the matrix's own verdict for the row is PASS (file name and page agreed there); a missing TP is
  "none printed" only when the matrix says the report declared it (N/A_TP_DECLARED_NA), otherwise unknown.
- Nothing is read from the reports here: the converter only re-keys a table it is given.
"""

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

import argparse
import json
import re
import sys
import tempfile
from pathlib import Path

TRUTH_VERSION = "v0100"
VRN_ROOT = Path(__file__).resolve().parents[1]
BOOK_PATH = VRN_ROOT / "ssot" / "VRN_TickerRecord_SSOT_v0100.json"

FILE_RX = re.compile(r"\.(?:pdf|docx?|txt|xlsx?|pptx?|html?|csv|md)$", re.I)
EMPTY = {"", "-", "—", "–", "n/a", "na", "none", "null", "nan"}
COLUMN_NAMES = {
    "file": ("報告檔", "檔名", "檔案", "file", "filename", "report"),
    "type": ("型別", "類型", "type", "report_type"),
    "ticker_page": ("代號(頁面)", "代號（頁面）", "代號(頁)", "頁面代號", "ticker_page", "ticker(page)"),
    "ticker_file": ("代號(檔名)", "代號（檔名）", "檔名代號", "代號", "ticker", "ticker_file", "ticker(filename)"),
    "broker_page": ("券商(頁面)", "券商（頁面）", "券商(頁)", "頁面券商", "broker_page", "broker(page)"),
    "broker_file": ("券商(檔名)", "券商（檔名）", "檔名券商", "券商", "broker", "broker_file", "broker(filename)"),
    "date": ("報告日", "日期", "報告日期", "date", "page_date", "report_date"),
    "name_file": ("名稱(檔名)", "名稱（檔名）", "檔名名稱", "name_file"),
    "company": ("官方證券名", "官方名", "證券名", "公司", "company", "company_name", "name"),
    "target_price": ("tp", "目標價", "target", "target_price", "targetprice"),
    "tp_gate": ("target_price_gate", "tp_gate"),
    "rating": ("評等", "rating"),
    "text_layer": ("文字層", "text", "text_layer"),
    "verdict": ("總判", "verdict", "overall"),
    "current_price": ("現價", "收盤價", "股價", "current_price", "price"),
    "analyst": ("分析師", "analyst", "analysts"),
}
GATE_COLUMNS = ("filename_vs_page", "zone_presence", "target_price", "tp_evidence", "tp_self_consistency", "text_consensus",
                "name_match", "tp_twd_band", "nonstock_tp_leak")
TYPE_LABELS = (("STOCK", ("個股", "stock", "company")), ("INDUSTRY", ("產業", "industry", "sector")),
               ("MARKET", ("大盤晨報", "大盤", "晨報", "晨會", "海外", "日股", "港股", "美股", "market", "daily", "morning", "overseas")),
               ("EVENT", ("研討會", "論壇", "event", "forum", "conference", "seminar")), ("MACRO", ("總經", "macro")),
               ("ETF", ("etf",)))
RATING_LEVELS = {"BUY": "BUY", "ADD": "BUY", "ACCUMULATE": "BUY", "OVERWEIGHT": "BUY", "OW": "BUY", "OUTPERFORM": "BUY", "OP": "BUY",
                 "STRONG BUY": "BUY", "買進": "BUY", "逢低買進": "BUY", "增持": "BUY", "HOLD": "HOLD", "NEUTRAL": "HOLD", "N": "HOLD",
                 "EQUAL-WEIGHT": "HOLD", "EQUALWEIGHT": "HOLD", "EW": "HOLD", "MARKET PERFORM": "HOLD", "MP": "HOLD", "中立": "HOLD",
                 "持有": "HOLD", "區間操作": "HOLD", "SELL": "SELL", "REDUCE": "SELL", "UNDERWEIGHT": "SELL", "UW": "SELL",
                 "UNDERPERFORM": "SELL", "UP": "SELL", "賣出": "SELL", "減持": "SELL", "NOT_RATED": "NOT_RATED", "NOT RATED": "NOT_RATED",
                 "NR": "NOT_RATED", "UNRATED": "NOT_RATED", "未評等": "NOT_RATED", "不予評等": "NOT_RATED"}


# [VRN-ID] VRN-ENG018-FNC001 · LOGIC
def text_cells(line):
    """One pasted line -> its cells: tab-separated (a table copied from the browser), '|' (markdown) or 2+ spaces."""
    s = line.rstrip("\r\n")
    if "\t" in s:
        return [c.strip() for c in s.split("\t")]
    st = s.strip()
    if st.startswith("|") and st.count("|") >= 3:
        cells = [c.strip() for c in st.strip("|").split("|")]
        return cells
    return [c.strip() for c in re.split(r"\s{2,}", st) if c.strip() != ""]


# [VRN-ID] VRN-ENG018-FNC002 · LOGIC
def fold_column(name):
    return re.sub(r"\s+", "", str(name or "")).casefold().replace("（", "(").replace("）", ")")


# [VRN-ID] VRN-ENG018-FNC003 · LOGIC
def table_columns(header):
    """Header cells -> {role: index}; the matrix's gate columns keep their own names (verdicts, read as given)."""
    cols = {}
    folded = [fold_column(h) for h in header]
    for role, names in COLUMN_NAMES.items():
        wanted = [fold_column(n) for n in names]
        for i, h in enumerate(folded):
            if h in wanted and role not in cols and i not in cols.values():
                cols[role] = i
                break
    for g in GATE_COLUMNS:
        for i, h in enumerate(folded):
            if h == g and i not in cols.values():
                cols["gate:" + g] = i
                break
    return cols


# [VRN-ID] VRN-ENG018-FNC004 · IO
def read_matrix_text(text):
    """The pasted page (noise lines, the header, the rows, whatever follows) -> {"columns": {...}, "rows": [cells], "header": [...]}.
    A row is a line whose first cell is a file name."""
    lines = str(text or "").splitlines()
    header, cols, start = None, {}, 0
    for i, line in enumerate(lines):
        cells = text_cells(line)
        if len(cells) >= 3:
            c = table_columns(cells)
            if "file" in c and ("type" in c or "ticker_page" in c or "ticker_file" in c or "date" in c):
                header, cols, start = cells, c, i + 1
                break
    if header is None:
        return {"columns": {}, "header": [], "rows": [], "skipped": len(lines)}
    rows, skipped = [], 0
    for line in lines[start:]:
        if not line.strip():
            continue
        cells = text_cells(line)
        if len(cells) < 2 or not FILE_RX.search(cells[cols["file"]] if cols["file"] < len(cells) else ""):
            skipped += 1
            continue
        if len(cells) < len(header):
            cells = cells + [""] * (len(header) - len(cells))
        rows.append(cells)
    return {"columns": cols, "header": header, "rows": rows, "skipped": skipped}


# [VRN-ID] VRN-ENG018-FNC005 · IO
def load_record_book(path=None):
    try:
        return json.loads(Path(path or BOOK_PATH).read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}


# [VRN-ID] VRN-ENG018-FNC006 · LOGIC
def fold_alias(s):
    return re.sub(r"[^0-9a-z一-鿿]", "", str(s or "").casefold())


_ALIAS_CACHE = {}


# [VRN-ID] VRN-ENG018-FNC007 · LOGIC
def lookup_broker_key(name, book):
    """A broker as the matrix prints it (GOLDMAN, MORGANSTANLEY, 凱基) -> (canonical key, accepted keys) through the merged book;
    a disputed alias keeps every reading; an alias no book knows is kept as printed (upper case) and flagged."""
    n = fold_alias(name)
    if not n:
        return None, [], False
    key = id(book)
    if key not in _ALIAS_CACHE:
        table = {}
        for alias, it in ((book.get("broker") or {}).get("entries") or {}).items():
            canon = it.get("canonical") if isinstance(it, dict) else None
            if canon:
                table.setdefault(fold_alias(alias), canon)
        canon_keys = {fold_alias(c if isinstance(c, str) else c[0]): (c if isinstance(c, str) else c[0]) for c in table.values()}
        _ALIAS_CACHE[key] = (table, canon_keys)
    table, canon_keys = _ALIAS_CACHE[key]
    canon = table.get(n)
    if canon is None and n in canon_keys:
        canon = canon_keys[n]
    if canon is None:
        return str(name).strip().upper(), [], False
    printed = re.sub(r"[^0-9A-Z]", "", str(name).upper())
    if isinstance(canon, list):
        first = lookup_preferred_key(name, canon, book)
        accepted = [first] + [c for c in canon if c != first]
    else:
        first, accepted = canon, [canon]
    if printed and printed not in accepted and re.fullmatch(r"[A-Z][A-Z0-9]{1,15}", printed):
        accepted.append(printed)      # the mother's own key (MACQUARIE) where the merged book says MCQ: the engine may answer either
    return first, accepted, True


# [VRN-ID] VRN-ENG018-FNC008 · LOGIC
def lookup_preferred_key(alias, canonicals, book):
    """A disputed alias (Morgan Stanley: JPM in one old book, MS everywhere else): the reading of the engine's own book
    (VRN_Broker_Dict_v0103) first, else the reading most books give, else the first listed."""
    n = fold_alias(alias)
    for c in book.get("conflicts") or []:
        if fold_alias(c.get("alias")) != n:
            continue
        votes = c.get("canonicals") or {}
        if isinstance(votes, dict):
            for key, books in votes.items():
                if key in canonicals and any("Broker_Dict_v0103" in str(b) for b in (books or [])):
                    return key
            ranked = sorted((k for k in votes if k in canonicals), key=lambda k: (-len(votes[k] or []), canonicals.index(k)))
            if ranked:
                return ranked[0]
    return canonicals[0]


# [VRN-ID] VRN-ENG018-FNC009 · LOGIC
def lookup_rating_level(word, book=None):
    """The matrix's rating word -> the level G11 compares (BUY / HOLD / SELL / NOT_RATED); None when no table knows it."""
    w = re.sub(r"\s+", " ", str(word or "")).strip().strip("「」()（）").upper()
    if not w:
        return None
    if w in RATING_LEVELS:
        return RATING_LEVELS[w]
    for alias, it in (((book or {}).get("rating") or {}).get("entries") or {}).items():
        if fold_alias(alias) == fold_alias(w) and isinstance(it, dict):
            canon = it.get("canonical")
            canon = canon[0] if isinstance(canon, list) and canon else canon
            if isinstance(canon, str):
                return RATING_LEVELS.get(canon.upper(), canon.upper())
    return None


# [VRN-ID] VRN-ENG018-FNC010 · LOGIC
def lookup_report_type(label):
    s = str(label or "").strip()
    if not s:
        return "OTHER"
    if s.upper() in ("STOCK", "INDUSTRY", "MARKET", "EVENT", "MACRO", "ETF", "OTHER"):
        return s.upper()
    low = s.casefold()
    for kind, words in TYPE_LABELS:
        if any(w.casefold() in low for w in words):
            return kind
    return "OTHER"


# [VRN-ID] VRN-ENG018-FNC011 · LOGIC
def text_date_iso(s):
    """2025-08-19 / 2025/8/19 / 20250819 / 114.12.02 / 1141202 (ROC) -> ISO; anything else as given."""
    t = str(s or "").strip()
    if not t:
        return None
    m = re.fullmatch(r"(\d{4})[-/.年]\s*(\d{1,2})[-/.月]\s*(\d{1,2})\s*日?", t)
    if m:
        return f"{int(m.group(1)):04d}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    m = re.fullmatch(r"(\d{4})(\d{2})(\d{2})", t)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    m = re.fullmatch(r"(1\d{2})[-/.年]?\s*(\d{1,2})[-/.月]?\s*(\d{1,2})\s*日?", t)
    if m and len(t) in (7, 8, 9, 10):
        return f"{int(m.group(1)) + 1911:04d}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    return t


# [VRN-ID] VRN-ENG018-FNC012 · LOGIC
def text_number(s):
    t = str(s or "").strip().replace(",", "")
    if t.casefold() in EMPTY:
        return None
    m = re.fullmatch(r"[^\d-]*(-?\d+(?:\.\d+)?)[^\d]*", t)
    try:
        return float(m.group(1)) if m else None
    except (TypeError, ValueError):
        return None


# [VRN-ID] VRN-ENG018-FNC013 · LOGIC
def cell_of(cells, cols, role):
    i = cols.get(role)
    if i is None or i >= len(cells):
        return None
    v = str(cells[i]).strip()
    return None if v.casefold() in EMPTY else v


# [VRN-ID] VRN-ENG018-FNC014 · BUILD
def build_truth_row(cells, cols, book, source=""):
    """One matrix row -> one G11 truth row (the schema docs/VIA_VRN_AUTOTEST.md describes) plus `unknown` and `source`."""
    file = cell_of(cells, cols, "file") or ""
    kind = lookup_report_type(cell_of(cells, cols, "type"))
    stock = kind == "STOCK"
    verdict = (cell_of(cells, cols, "verdict") or "").upper()
    text_layer = (cell_of(cells, cols, "text_layer") or "OK").upper()
    has_text = text_layer not in ("NO_TEXT", "NONE", "IMAGE", "OCR")
    ticker = cell_of(cells, cols, "ticker_page") or cell_of(cells, cols, "ticker_file")
    ticker = ticker if ticker and re.fullmatch(r"\d{4,6}[A-Z]?", ticker) else None
    unknown = []
    notes = {}
    b_page, b_file = cell_of(cells, cols, "broker_page"), cell_of(cells, cols, "broker_file")
    broker, accept = None, {}
    keys, known = [], []
    for raw in (b_page, b_file):
        if raw:
            k, acc, ok = lookup_broker_key(raw, book)
            if k and k not in keys:
                keys.append(k)
            for a in acc:
                if a not in keys:
                    keys.append(a)
            known.append(ok)
            if not ok:
                notes.setdefault("broker_unmapped", []).append(raw)
    if keys:
        broker = keys[0]
        if len(keys) > 1:
            accept["broker"] = keys
    else:
        unknown.append("broker")
    date = text_date_iso(cell_of(cells, cols, "date"))
    on_page1 = {}
    if date:
        on_page1["page_date"] = bool(has_text and verdict == "PASS")
    else:
        unknown.append("page_date")
    rating = None
    if stock:
        word = cell_of(cells, cols, "rating")
        rating = lookup_rating_level(word, book) if word else None
        if rating:
            on_page1["rating"] = has_text
            notes["rating_as_printed"] = word
        else:
            unknown.append("rating")
            if word:
                notes["rating_unmapped"] = word
    tp = text_number(cell_of(cells, cols, "target_price")) if stock else None
    if stock:
        gate_tp = (cell_of(cells, cols, "gate:target_price") or "").upper()
        if tp is not None:
            on_page1["target_price"] = has_text
        elif gate_tp not in ("N/A_TP_DECLARED_NA", "NA_DECLARED", "DECLARED_NA"):
            unknown.append("target_price")
        notes["target_price_gate"] = gate_tp or None
    current = text_number(cell_of(cells, cols, "current_price")) if stock else None
    if stock:
        if current is not None:
            on_page1["current_price"] = has_text
        else:
            unknown.append("current_price")
        if ticker is None:
            unknown.append("ticker")
    company = cell_of(cells, cols, "company") or cell_of(cells, cols, "name_file")
    analysts = [a.strip() for a in re.split(r"[|;；,，/]", cell_of(cells, cols, "analyst") or "") if a.strip()]
    row = {"file": file, "report_type": kind, "ticker": ticker, "broker": broker, "page_date": date, "on_page1": on_page1,
           "rating": rating, "target_price": tp, "current_price": current, "accept": accept, "company_name": company if stock else None,
           "text_layer": has_text, "analysts": analysts, "unknown": unknown,
           "source": {"matrix": source or "pasted matrix", "type_label": cell_of(cells, cols, "type"), "verdict": verdict or None,
                      "text_layer": text_layer, "broker_as_printed": {"page": b_page, "filename": b_file},
                      "gates": {g: cell_of(cells, cols, "gate:" + g) for g in GATE_COLUMNS if ("gate:" + g) in cols}, **notes}}
    return row


# [VRN-ID] VRN-ENG018-FNC015 · BUILD
def build_truth_rows(parsed, book=None, source=""):
    book = book if book is not None else load_record_book()
    cols = parsed.get("columns") or {}
    rows = []
    seen = set()
    for cells in parsed.get("rows") or []:
        row = build_truth_row(cells, cols, book, source)
        if not row["file"] or row["file"] in seen:
            continue
        seen.add(row["file"])
        rows.append(row)
    return rows


# [VRN-ID] VRN-ENG018-FNC016 · LOGIC
def summarize_truth_rows(rows):
    kinds, unknown, unmapped = {}, {}, []
    for r in rows:
        kinds[r["report_type"]] = kinds.get(r["report_type"], 0) + 1
        for u in r.get("unknown") or []:
            unknown[u] = unknown.get(u, 0) + 1
        unmapped += (r.get("source") or {}).get("broker_unmapped") or []
    return {"rows": len(rows), "stock": kinds.get("STOCK", 0), "non_stock": len(rows) - kinds.get("STOCK", 0), "types": kinds,
            "unknown": unknown, "broker_unmapped": sorted(set(unmapped)),
            "judged": {"page_date": sum(1 for r in rows if (r.get("on_page1") or {}).get("page_date")),
                       "rating": sum(1 for r in rows if (r.get("on_page1") or {}).get("rating")),
                       "target_price": sum(1 for r in rows if (r.get("on_page1") or {}).get("target_price"))}}


# [VRN-ID] VRN-ENG018-FNC017 · VALIDATE
def check_truth_path(path, root=VRN_ROOT):
    """The truth file stays on the operator's machine: a path inside the VRN tree is refused (真值檔不入庫)."""
    try:
        Path(path).resolve().relative_to(Path(root).resolve())
        return False, f"真值檔不入庫：{path} 在 VRN 樹裡；請寫到樹外（例如 %LOCALAPPDATA%\\VRN_Main\\truth）"
    except ValueError:
        return True, ""


# [VRN-ID] VRN-ENG018-FNC018 · IO
def write_truth_file(path, rows, root=VRN_ROOT):
    ok, why = check_truth_path(path, root)
    if not ok:
        raise ValueError(why)
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(rows, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return p


# [VRN-ID] VRN-ENG018-FNC019 · IO
def read_pasted_file(path):
    """The pasted matrix saved by the operator: UTF-8 (BOM or not), UTF-16 (Notepad), or the Windows code page."""
    raw = Path(path).read_bytes()
    if raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff"):
        return raw.decode("utf-16")
    for enc in ("utf-8-sig", "cp950", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


# [VRN-ID] VRN-ENG018-FNC020 · LOGIC
def convert_matrix_file(src, out=None, source="", book=None):
    text = read_pasted_file(src)
    parsed = read_matrix_text(text)
    rows = build_truth_rows(parsed, book=book, source=source or Path(src).name)
    out_path = Path(out) if out else Path(src).with_suffix(".truth.json")
    written = write_truth_file(out_path, rows) if rows else None
    return {"parsed": {"columns": sorted(parsed["columns"]), "rows": len(parsed["rows"]), "skipped": parsed.get("skipped", 0)},
            "summary": summarize_truth_rows(rows), "out": str(written) if written else "", "rows": rows}


SAMPLE_HEADER = ("報告檔\t型別\t代號(檔名)\t代號(頁面)\t券商(檔名)\t券商(頁面)\t報告日\t名稱(檔名)\t官方證券名\t對帳\t產業別\tTP\tTP態\t評等\t文字層\t總判\t"
                 "filename_vs_page\tzone_presence\ttarget_price\ttp_evidence\ttp_self_consistency\ttext_consensus\tname_match\ttp_twd_band\tnonstock_tp_leak")
SAMPLE_ROWS = [
    "20260101測試證券個股報告-測試公司(1234).pdf\t個股\t1234\t1234\tMEGA\tMEGA\t2026-01-01\t測試公司\t測試公司股份有限公司\tMATCH\t-\t100.0\tNA\tBUY\tOK\tPASS\tPASS\tPASS\tPASS\tPASS\tPASS\tPASS\tPASS\t-\t-",
    "GS-5678 20260102.pdf\t個股\t5678\t5678\tGOLDMAN\tGOLDMAN\t2026-01-02\t-\t某某公司\tNO_HINT\t-\t-\tNA\tHOLD\tOK\tWARN\tPASS\tPASS\tWARN\t-\t-\tWARN\tN/A\t-\t-",
    "Daiwa-9999 20260103.pdf\t個股\t9999\t9999\tDAIWA\tDAIWA\t2026-01-03\t-\t另一公司\tNO_HINT\t-\t-\tNA\tHOLD\tOK\tPASS\tPASS\tPASS\tN/A_TP_DECLARED_NA\t-\t-\tPASS\tN/A\t-\t-",
    "測試晨會報告20260104.pdf\t大盤晨報\t-\t-\tPRESIDENT\t-\t2026-01-04\t-\t-\tNO_TICKER\t-\t-\tNA\tBUY\tOK\tPASS\tPASS\tN/A_NON_STOCK\tN/A_NON_STOCK\t-\t-\tPASS\tN/A_NON_STOCK\t-\t-",
    "第一場 測試研討會 - 測試投顧.pdf\t研討會\t-\t-\tHUANAN\t-\t-\t-\t-\tNO_TICKER\t-\t-\tNA\t-\tOK\tPASS\tPASS\tN/A_NON_STOCK\tN/A_NON_STOCK\t-\t-\tPASS\tN/A_NON_STOCK\t-\t-",
    "測試投顧-2468-測試二-Memo-20260105.docx\t個股\t2468\t2468\tHUANAN\t-\t2026-01-05\t測試二\t測試二\tMATCH\t-\t-\tNA\tADD\tTEXT_ONLY\tWARN\tPASS\tPASS\tWARN\t-\t-\tN/A_NO_SIDECAR\tPASS\t-\t-",
    "MQ-1357 20260106.pdf\t個股\t1357\t1357\tMACQUARIE\t-\t2026-01-06\t-\t掃描公司\tNO_HINT\t-\t-\tNA\t-\tNO_TEXT\tN/A\tN/A_NO_TEXT\tN/A_NO_TEXT\tN/A_NO_TEXT\t-\t-\tN/A_NO_SIDECAR\tN/A\t-\t-",
]
SAMPLE_BOOK = {"broker": {"entries": {"Goldman": {"canonical": "GS"}, "MEGA": {"canonical": "MEGA"}, "Daiwa": {"canonical": "DAIWA"},
                                      "President": {"canonical": "PRESIDENT"}, "華南": {"canonical": "HUANAN"}, "Huanan": {"canonical": "HUANAN"},
                                      "Macquarie": {"canonical": "MCQ"}, "中信": {"canonical": ["CTBC", "CITIC"]}}},
               "rating": {"entries": {"Overweight": {"canonical": "BUY"}}}}


# [VRN-ID] VRN-ENG018-FNC021 · LOGIC
def sample_text():
    return "VRN 個股報告解讀矩陣 · 測試\n2026-01-01 · 7 件\n① DETAILED SUMMARY MATRIX\n" + SAMPLE_HEADER + "\n" + "\n".join(SAMPLE_ROWS) + "\n零 CDN · 零外部資源\n"


# [VRN-ID] VRN-ENG018-FNC022 · ENTRY
def selftest(verbose=True):
    checks = []
    parsed = read_matrix_text(sample_text())
    checks.append(("貼文裡找到表頭與 7 列，雜訊行跳過", len(parsed["rows"]) == 7 and parsed["columns"].get("file") == 0 and "gate:target_price" in parsed["columns"], parsed["columns"]))
    rows = build_truth_rows(parsed, SAMPLE_BOOK, "selftest")
    by = {r["file"]: r for r in rows}
    a = by["20260101測試證券個股報告-測試公司(1234).pdf"]
    checks.append(("個股列：型別 STOCK、代號、券商、日期、評等 BUY、目標價 100；總判 PASS 才判日期",
                   (a["report_type"], a["ticker"], a["broker"], a["page_date"], a["rating"], a["target_price"]) == ("STOCK", "1234", "MEGA", "2026-01-01", "BUY", 100.0)
                   and a["on_page1"] == {"page_date": True, "rating": True, "target_price": True} and a["company_name"] == "測試公司股份有限公司", a))
    checks.append(("矩陣沒有現價欄：現價列為不保證（unknown），不當誤報", "current_price" in a["unknown"] and a["current_price"] is None, a["unknown"]))
    g = by["GS-5678 20260102.pdf"]
    checks.append(("GOLDMAN 經合併冊 → GS；總判 WARN 的日期不判；目標價 '-' 而閘 WARN = 不保證",
                   g["broker"] == "GS" and g["on_page1"].get("page_date") is False and "target_price" in g["unknown"] and g["target_price"] is None, g))
    d = by["Daiwa-9999 20260103.pdf"]
    checks.append(("報告自己說沒目標價（N/A_TP_DECLARED_NA）= 真值『沒印』，不是不保證", d["target_price"] is None and "target_price" not in d["unknown"], d["unknown"]))
    m = by["測試晨會報告20260104.pdf"]
    checks.append(("大盤晨報 → MARKET，非個股列沒有評等／目標價／公司名", m["report_type"] == "MARKET" and m["rating"] is None and m["target_price"] is None and m["company_name"] is None, m))
    e = by["第一場 測試研討會 - 測試投顧.pdf"]
    checks.append(("研討會 → EVENT；沒有報告日 = 日期不保證", e["report_type"] == "EVENT" and e["page_date"] is None and "page_date" in e["unknown"], e))
    x = by["測試投顧-2468-測試二-Memo-20260105.docx"]
    checks.append(("TEXT_ONLY 的 docx 有文字層；ADD 算 BUY 一級", x["text_layer"] is True and x["rating"] == "BUY" and x["source"]["rating_as_printed"] == "ADD", x))
    q = by["MQ-1357 20260106.pdf"]
    checks.append(("NO_TEXT 的掃描檔：text_layer False、評等不保證；MACQUARIE → MCQ", q["text_layer"] is False and "rating" in q["unknown"] and q["broker"] == "MCQ", q))
    k, acc, ok = lookup_broker_key("中信", SAMPLE_BOOK)
    checks.append(("兩本冊有爭議的別名：兩個讀法都收（accept.broker）", k == "CTBC" and acc == ["CTBC", "CITIC"] and ok, (k, acc)))
    k2, acc2, ok2 = lookup_broker_key("NOBODY SEC", SAMPLE_BOOK)
    checks.append(("沒有一本冊認得的券商：照印、標記", k2 == "NOBODY SEC" and not ok2, (k2, acc2)))
    checks.append(("日期寫法：2025/8/19、20250819、1141202（民國）都成 ISO",
                   (text_date_iso("2025/8/19"), text_date_iso("20250819"), text_date_iso("1141202")) == ("2025-08-19", "2025-08-19", "2025-12-02"), None))
    checks.append(("評等詞 → 等級：Overweight（冊）、中立、NR", (lookup_rating_level("Overweight", SAMPLE_BOOK), lookup_rating_level("中立"), lookup_rating_level("NR")) == ("BUY", "HOLD", "NOT_RATED"), None))
    md = "| 報告檔 | 型別 | 代號(頁面) | 券商(頁面) | 報告日 | TP | 評等 |\n|---|---|---|---|---|---|---|\n| X-1111 20260107.pdf | 個股 | 1111 | MEGA | 2026-01-07 | 50 | SELL |\n"
    pm = build_truth_rows(read_matrix_text(md), SAMPLE_BOOK)
    checks.append(("markdown 表格也讀得到", len(pm) == 1 and pm[0]["ticker"] == "1111" and pm[0]["rating"] == "SELL" and pm[0]["target_price"] == 50.0, pm))
    with tempfile.TemporaryDirectory() as td:
        src = Path(td) / "pasted.txt"
        src.write_text(sample_text(), encoding="utf-8")
        got = convert_matrix_file(src, source="selftest", book=SAMPLE_BOOK)
        back = json.loads(Path(got["out"]).read_text(encoding="utf-8"))
        checks.append(("寫檔：真值 JSON 讀回相同；摘要算對", back == rows and got["summary"]["stock"] == 5 and got["summary"]["non_stock"] == 2 and got["out"].endswith(".truth.json"), got["summary"]))
        src16 = Path(td) / "pasted16.txt"
        src16.write_bytes(sample_text().encode("utf-16"))
        checks.append(("記事本存的 UTF-16 也讀得到", len(build_truth_rows(read_matrix_text(read_pasted_file(src16)), SAMPLE_BOOK)) == 7, None))
        ok_in, why = check_truth_path(VRN_ROOT / "ssot" / "x.json")
        checks.append(("真值檔不入庫：VRN 樹裡的路徑拒寫", not ok_in and "不入庫" in why, why))
    real = load_record_book()
    if real:
        rk = [lookup_broker_key(n, real)[0] for n in ("GOLDMAN", "JPMORGAN", "MORGANSTANLEY", "MACQUARIE")]
        checks.append(("合併冊在：母倉的 GOLDMAN／JPMORGAN／MORGANSTANLEY／MACQUARIE 對到 GS／JPM／MS／MCQ", rk == ["GS", "JPM", "MS", "MCQ"], rk))
        checks.append(("母倉自己的鍵（MACQUARIE）也收：首頁引擎答 MACQUARIE", "MACQUARIE" in lookup_broker_key("MACQUARIE", real)[1], None))
    bad = [c for c in checks if not c[1]]
    if verbose:
        for name, ok, detail in checks:
            print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + ("" if ok else f" · {str(detail)[:300]}"))
        print(f"[TRUTHMATRIX] {TRUTH_VERSION} · {len(checks) - len(bad)}/{len(checks)}")
    return 0 if not bad else 1


# [VRN-ID] VRN-ENG018-FNC023 · ENTRY
def main(argv=None):
    parser = argparse.ArgumentParser(prog="VRN_TruthMatrix_v0100.py", description="母倉首頁矩陣貼文 → G11 真值檔（只在操作員手上）")
    sub = parser.add_subparsers(dest="command")
    p_c = sub.add_parser("convert", help="貼文檔 → 真值 JSON")
    p_c.add_argument("src")
    p_c.add_argument("--out", default="", help="真值 JSON（預設 <src>.truth.json；不能在 VRN 樹裡）")
    p_c.add_argument("--source", default="", help="來源說明（例如 VIA_VRN_FirstPageEngine v0113 2026-09-11）")
    sub.add_parser("selftest")
    args = parser.parse_args(argv)
    if args.command == "convert":
        try:
            got = convert_matrix_file(args.src, args.out or None, args.source)
        except ValueError as error:
            print(f"[TRUTH-MATRIX] {error}")
            return 1
        s = got["summary"]
        if not s["rows"]:
            print(f"[TRUTH-MATRIX] 貼文裡沒有矩陣列（表頭要有 報告檔 與 型別／代號／報告日；跳過 {got['parsed']['skipped']} 行）")
            return 1
        unk = " · ".join(f"{k} {v}" for k, v in sorted(s["unknown"].items()))
        print(f"[TRUTH-MATRIX] {s['rows']} 列 → 真值 {s['rows']} 筆（個股 {s['stock']} · 非個股 {s['non_stock']}）· 判日期 {s['judged']['page_date']} · "
              f"判評等 {s['judged']['rating']} · 判目標價 {s['judged']['target_price']} · 不保證：{unk or '無'}"
              + (f" · 券商沒對到：{', '.join(s['broker_unmapped'])}" if s["broker_unmapped"] else "") + f" · {got['out']}（只在操作員手上，不入庫）")
        print(f"[TRUTH-MATRIX] 用法：VRN_Main_v0100.py run --truth \"{got['out']}\"  或啟動器 -Truth \"{got['out']}\"")
        return 0
    return selftest()


if __name__ == "__main__":
    sys.exit(main())
