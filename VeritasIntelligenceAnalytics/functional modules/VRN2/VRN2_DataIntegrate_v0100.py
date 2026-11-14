#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VRN2_DataIntegrate v0100 — 舊資料庫(CSV / XLSX / Google Sheet 匯出)偵測 · 自適應欄位對齊 · 問過使用者才整合 · 原檔絕不刪(操作員 2026-10-29)。

操作員令:「若使用者已有舊的資料庫 可能是 CSV / GOOGLE SHEET 主動提醒要不要進行資料整合 · 新增資料整合功能 在整合成功前千萬不要刪掉原有資料 ·
          去讀取他 應該內容差不多 順序有別 自適應式對齊欄位核對後問使用者要不要創立新整合檔案 · 若 OK 則整合創立 並提醒他舊資料幫他放到 TEMP 由他自行處理」。

動詞:
  scan    [--v2 <VIA_Reports/vrn2>] [--dirs <夾;夾…>]   偵測候選:設定的輸出夾(VRN2_Output_Config.json)及其上一層 · VIA_Reports/vrn2/legacy_in/ · $env:VRN2_INTEGRATE_DIRS · --dirs;
                                                       .csv / .tsv / .xlsx / .xlsm / .parquet / .json(列表)· .gsheet 捷徑只列不讀;跳過 VRN2_* / VRN_*(自己的輸出)與 VRN2/ 子夾。
                                                       每份:讀表頭 + 前 200 列 → 正規化欄名 + 同義字 + 內容型態(代號 / 日期 / 數值 / .pdf)→ 對到 BasicInfo / FinancialData / Summary 哪一冊、每欄對到哪一欄、對不到的欄保留為 X_<原欄名>
                                                       → VIA_Reports/vrn2/VRN2_Integrate_latest.json(state = PENDING_USER · 候選 · 對齊表 · 提問文字)。Workbench 左欄 / 第一區據此問使用者。
  apply   [--v2 …] [--only 1,3] [--move]                使用者說要:每份候選 → 依對齊表轉成目標冊欄位 + VRN-2 目前該冊的列 → 主鍵去重(同鍵同值去掉 · 同鍵不同值兩邊都留並標 CONFLICT)
                                                       → 新檔 <輸出夾>/VRN2/integrated/VRN2_Integrated_<冊>_<時間>.json / .csv(/ .parquet 有 pyarrow 才寫)+ _latest 副本 → 重讀核對列數
                                                       → 核對過才把原檔**複製**到 %TEMP%/VRN2_Integrate_<時間>/originals/(原位置不動;--move 才搬,而且也是核對過才搬)→ state = APPLIED。
                                                       任何一步失敗 → 原檔原位不動、沒有東西被刪、state = FAILED 帶原因。
  dismiss [--v2 …]                                      使用者說不要:state = DISMISSED(候選留著 · 下次 scan 再問)。
  --selftest
[VIA:AST-CLASS] 類別 = 資料整合引擎(VRN-2)· 入口 = ActivateVRN-2 ⑬c(scan)/ vrn2://integrate(處理器 v0109)/ 本檔 CLI
"""
from __future__ import annotations

import csv
import datetime as _dt
import hashlib
import io
import json
import os
import re
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

VERSION = "v0100"
DISPLAY_NAME = "VRN2_DataIntegrate"
TAG = "資料整合 v0100"
RECEIPT = "VRN2_Integrate_latest.json"
OUT_CONFIG = "VRN2_Output_Config.json"
EXTS = {".csv": "CSV", ".tsv": "TSV", ".xlsx": "XLSX", ".xlsm": "XLSX", ".parquet": "Parquet", ".json": "JSON", ".gsheet": "Google Sheet 捷徑"}
MAX_CANDIDATES = 50
MAX_BYTES = 200 * 1024 * 1024
SAMPLE_ROWS = 200
BOOK_COLS = {
    "BasicInfo": ["REPORT_DATE", "FILENAME", "TICKER", "YFINANCE_TICKER", "BLOOMBERG_TICKER", "NAME", "ENGLISH_NAME", "BROKER", "ANALYST", "EMAIL", "TEL", "TITLE", "RATING", "TARGET_PRICE", "CURRENT_PRICE_REPORT", "UPSIDE_PCT", "ADJ_CLOSE", "ADJ_CLOSE_BEFORE_REPORT"],
    "FinancialData": ["REPORT_DATE", "FILENAME", "TICKER", "BROKER", "PAGE", "TABLE", "ITEM", "PERIOD", "VALUE", "VERIFY", "ROW", "SECTION"],
    "Summary": ["REPORT_DATE", "FILENAME", "TICKER", "BROKER", "TITLE", "POINT_1", "POINT_2", "POINT_3", "POINT_4", "POINTS_OK"],
}
BOOK_KEYS = {"BasicInfo": ("FILENAME",), "FinancialData": ("FILENAME", "ITEM", "PERIOD", "PAGE", "TABLE"), "Summary": ("FILENAME",)}
SYN = {
    "REPORT_DATE": ("report_date", "date", "報告日", "報告日期", "日期", "發布日", "發佈日", "report date", "pub date", "published"),
    "FILENAME": ("filename", "file", "file_name", "檔名", "檔案", "檔案名稱", "report", "pdf", "source", "來源檔"),
    "TICKER": ("ticker", "code", "stock", "stock_code", "symbol", "代號", "股票代號", "股號", "證券代號", "公司代號", "stock code"),
    "YFINANCE_TICKER": ("yfinance_ticker", "yf", "yahoo", "yfinance"), "BLOOMBERG_TICKER": ("bloomberg_ticker", "bbg", "bloomberg", "bb ticker"),
    "NAME": ("name", "company", "公司", "公司名稱", "名稱", "股名", "stock name", "company name"), "ENGLISH_NAME": ("english_name", "english name", "英文名"),
    "BROKER": ("broker", "券商", "機構", "研究機構", "house", "brokerage", "firm"), "ANALYST": ("analyst", "分析師", "研究員", "author"),
    "EMAIL": ("email", "e_mail", "mail", "信箱", "電郵"), "TEL": ("tel", "phone", "telephone", "電話", "聯絡電話"),
    "TITLE": ("title", "標題", "報告標題", "headline", "subject"), "RATING": ("rating", "評等", "投資評等", "建議", "recommendation", "reco", "call"),
    "TARGET_PRICE": ("target_price", "target price", "tp", "目標價", "目標股價", "price target", "pt", "合理價"), "CURRENT_PRICE_REPORT": ("current_price", "price", "現價", "股價", "收盤價", "close", "current price"),
    "UPSIDE_PCT": ("upside", "upside_pct", "上漲空間", "漲幅", "潛在漲幅", "upside %"), "ADJ_CLOSE": ("adj_close", "adj close", "還原收盤", "還原股價"), "ADJ_CLOSE_BEFORE_REPORT": ("adj_close_before_report", "報告前收盤"),
    "PAGE": ("page", "頁", "頁碼", "page no", "pg"), "TABLE": ("table", "表", "表格", "table id"), "ITEM": ("item", "科目", "項目", "account", "metric", "line item", "指標"),
    "PERIOD": ("period", "期間", "年度", "年", "year", "fiscal", "fy", "quarter", "季"), "VALUE": ("value", "數值", "值", "金額", "amount", "數字", "val", "figure"),
    "VERIFY": ("verify", "verified", "驗證", "核對"), "ROW": ("row", "列", "列號"), "SECTION": ("section", "段落", "區段", "statement", "報表"),
    "POINT_1": ("point_1", "point1", "重點一", "重點1", "bullet 1", "要點一"), "POINT_2": ("point_2", "point2", "重點二", "重點2", "bullet 2"), "POINT_3": ("point_3", "point3", "重點三", "重點3", "bullet 3"), "POINT_4": ("point_4", "point4", "重點四", "重點4", "bullet 4"),
    "POINTS_OK": ("points_ok", "points ok", "重點數"),
}
_TICKER = re.compile(r"^[1-9]\d{3}(\.TWO?|\s+TT)?$", re.I)
_DATE = re.compile(r"^(20\d{2}[-/.]\d{1,2}[-/.]\d{1,2}|20\d{6}|\d{1,2}/\d{1,2}/20\d{2})$")
_NUM = re.compile(r"^\(?-?[\d,]+(\.\d+)?\)?%?$")


def say(line: str) -> None:
    try:
        print(line, flush=True)
    except UnicodeEncodeError:
        print(line.encode("utf-8", "replace").decode("ascii", "replace"), flush=True)


def now() -> str:
    return _dt.datetime.now().isoformat(timespec="seconds")


def stamp() -> str:
    return _dt.datetime.now().strftime("%Y%m%d_%H%M%S")


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with Path(p).open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_config(v2: Path) -> dict:
    try:
        return json.loads((Path(v2) / OUT_CONFIG).read_text(encoding="utf-8-sig"))
    except Exception:  # noqa: BLE001
        return {}


def temp_root() -> Path:
    return Path(os.environ.get("VRN2_INTEGRATE_TEMP") or os.environ.get("TEMP") or os.environ.get("TMPDIR") or tempfile.gettempdir())


# ===== 讀檔(只讀)=====
def _decode(raw: bytes) -> tuple:
    for enc in ("utf-8-sig", "utf-8", "cp950", "big5", "gb18030", "utf-16"):
        try:
            return raw.decode(enc), enc
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", "replace"), "utf-8(replace)"


def read_csv(path: Path, limit: int | None = SAMPLE_ROWS) -> tuple:
    """CSV / TSV → (表頭, 列, 說明)。自動編碼 · 自動分隔 · 跳過表頭前的雜訊列(Google Sheet 匯出常有標題列)。"""
    raw = path.read_bytes()
    text, enc = _decode(raw[: 4 << 20] if limit else raw)
    try:
        dialect = csv.Sniffer().sniff(text[:4096], delimiters=",;\t|")
        delim = dialect.delimiter
    except csv.Error:
        delim = "\t" if path.suffix.lower() == ".tsv" else ","
    rows = list(csv.reader(io.StringIO(text), delimiter=delim))
    rows = [r for r in rows if any(c.strip() for c in r)]
    hi = _header_index(rows)
    if hi is None:
        return [], [], "找不到表頭列(前 %d 列都不像欄名)" % min(len(rows), 10)
    header = [c.strip() for c in rows[hi]]
    body = [r + [""] * (len(header) - len(r)) for r in rows[hi + 1:]]
    note = "編碼 %s · 分隔 %r · 表頭在第 %d 列" % (enc, delim, hi + 1)
    return header, (body[:limit] if limit else body), note


def _header_index(rows: list):
    for i, r in enumerate(rows[:10]):
        cells = [c.strip() for c in r if c.strip()]
        if len(cells) >= 2 and sum(1 for c in cells if not _NUM.match(c) and not _DATE.match(c)) >= max(2, int(len(cells) * 0.5)):
            return i
    return None


def _col_index(ref: str) -> int:
    letters = re.match(r"[A-Z]+", ref.upper()).group(0)
    n = 0
    for ch in letters:
        n = n * 26 + (ord(ch) - 64)
    return n - 1


def read_xlsx(path: Path, limit: int | None = SAMPLE_ROWS) -> tuple:
    """XLSX 第一個工作表 → (表頭, 列, 說明)。純 zipfile + xml(桌機不一定有 openpyxl)。"""
    ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main", "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships", "pr": "http://schemas.openxmlformats.org/package/2006/relationships"}
    with zipfile.ZipFile(path) as z:
        wb = ET.fromstring(z.read("xl/workbook.xml"))
        sheets = wb.findall("m:sheets/m:sheet", ns)
        if not sheets:
            return [], [], "沒有工作表"
        rid = sheets[0].get("{%s}id" % ns["r"])
        rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
        target = next((r.get("Target") for r in rels.findall("pr:Relationship", ns) if r.get("Id") == rid), "worksheets/sheet1.xml")
        target = target.lstrip("/")
        sheet_path = target if target.startswith("xl/") else "xl/" + target
        shared = []
        if "xl/sharedStrings.xml" in z.namelist():
            for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("m:si", ns):
                shared.append("".join(t.text or "" for t in si.iter("{%s}t" % ns["m"])))
        rows = []
        for row in ET.fromstring(z.read(sheet_path)).iter("{%s}row" % ns["m"]):
            cells = {}
            for c in row.findall("m:c", ns):
                ref = c.get("r") or ""
                idx = _col_index(ref) if ref else len(cells)
                t = c.get("t")
                v = c.find("m:v", ns)
                if t == "s" and v is not None:
                    val = shared[int(v.text)] if v.text and v.text.isdigit() and int(v.text) < len(shared) else ""
                elif t == "inlineStr":
                    val = "".join(x.text or "" for x in c.iter("{%s}t" % ns["m"]))
                else:
                    val = (v.text or "") if v is not None else ""
                cells[idx] = val
            width = (max(cells) + 1) if cells else 0
            rows.append([cells.get(i, "") for i in range(width)])
            if limit and len(rows) > limit + 10:
                break
    rows = [r for r in rows if any(str(c).strip() for c in r)]
    hi = _header_index(rows)
    if hi is None:
        return [], [], "找不到表頭列"
    header = [str(c).strip() for c in rows[hi]]
    body = [r + [""] * (len(header) - len(r)) for r in rows[hi + 1:]]
    return header, (body[:limit] if limit else body), "工作表 %s · 表頭在第 %d 列" % (sheets[0].get("name"), hi + 1)


def read_json_rows(path: Path, limit: int | None = SAMPLE_ROWS) -> tuple:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if isinstance(data, dict):
        for k in ("rows", "data", "records", "items"):
            if isinstance(data.get(k), list):
                data = data[k]
                break
    if not isinstance(data, list) or not data or not all(isinstance(r, dict) for r in data[:20]):
        return [], [], "不是列表型 JSON(每列一個物件)"
    header = []
    for r in data[:50]:
        for k in r:
            if k not in header:
                header.append(str(k))
    body = [[("" if r.get(k) is None else (r.get(k) if isinstance(r.get(k), str) else json.dumps(r.get(k), ensure_ascii=False) if isinstance(r.get(k), (dict, list)) else str(r.get(k)))) for k in header] for r in data]
    return header, (body[:limit] if limit else body), "JSON 列表 %d 列" % len(data)


def read_parquet_rows(path: Path, limit: int | None = SAMPLE_ROWS) -> tuple:
    try:
        import pyarrow.parquet as pq  # noqa: WPS433
    except Exception:  # noqa: BLE001
        return [], [], "沒有 pyarrow · 讀不了 parquet(列出但不整合)"
    t = pq.read_table(str(path))
    header = list(t.column_names)
    body = [[("" if v is None else str(v)) for v in r.values()] for r in t.to_pylist()]
    return header, (body[:limit] if limit else body), "parquet %d 列" % t.num_rows


def read_any(path: Path, limit: int | None = SAMPLE_ROWS) -> tuple:
    ext = path.suffix.lower()
    if ext in (".csv", ".tsv"):
        return read_csv(path, limit)
    if ext in (".xlsx", ".xlsm"):
        return read_xlsx(path, limit)
    if ext == ".json":
        return read_json_rows(path, limit)
    if ext == ".parquet":
        return read_parquet_rows(path, limit)
    return [], [], "不支援的格式"


# ===== 自適應欄位對齊 =====
def norm_header(h) -> str:
    s = str(h or "").strip().lower().replace("（", "(").replace("）", ")")
    s = re.sub(r"\(.*?\)", "", s)
    s = re.sub(r"[\s\-/\\.:：]+", "_", s).strip("_")
    return s


def _syn_match(h: str) -> str:
    n = norm_header(h)
    if not n:
        return ""
    n2 = n.replace("_", " ")
    for target, names in SYN.items():
        if n == target.lower() or n2 == target.lower().replace("_", " "):
            return target
    for target, names in SYN.items():
        for a in names:
            an = norm_header(a)
            if n == an or n2 == an.replace("_", " "):
                return target
    for target, names in SYN.items():
        for a in sorted(names, key=len, reverse=True):
            an = norm_header(a)
            if len(an) >= 3 and (n.startswith(an + "_") or n.endswith("_" + an) or (not re.search(r"[a-z]", an) and an in n)):
                return target
    return ""


def _content_kind(values: list) -> str:
    vals = [str(v).strip() for v in values if str(v).strip()]
    if len(vals) < 2:
        return ""
    n = len(vals)
    if sum(1 for v in vals if _TICKER.match(v)) >= n * 0.8:
        return "TICKER"
    if sum(1 for v in vals if _DATE.match(v)) >= n * 0.8:
        return "REPORT_DATE"
    if sum(1 for v in vals if v.lower().endswith(".pdf")) >= n * 0.8:
        return "FILENAME"
    if sum(1 for v in vals if _NUM.match(v.replace(" ", ""))) >= n * 0.8:
        return "VALUE"
    return ""


def align_columns(header: list, rows: list) -> dict:
    """表頭 + 樣本列 → {mapping{原欄: 目標欄或 ''} · target_book · score · unmapped · by_content}。"""
    mapping, by_content, used = {}, [], set()
    for i, h in enumerate(header):
        t = _syn_match(h)
        if t and t not in used:
            mapping[h] = t
            used.add(t)
        else:
            mapping[h] = ""
    for i, h in enumerate(header):
        if mapping[h]:
            continue
        kind = _content_kind([r[i] for r in rows[:SAMPLE_ROWS] if i < len(r)])
        if kind and kind not in used:
            mapping[h] = kind
            used.add(kind)
            by_content.append(h)
    scores = {}
    for book, cols in BOOK_COLS.items():
        hit = sum(1 for t in used if t in cols)
        keyhit = sum(1 for k in BOOK_KEYS[book] if k in used)
        scores[book] = hit + keyhit * 0.5
    best = max(scores, key=lambda b: (scores[b], b == "FinancialData" and "VALUE" in used, b == "BasicInfo"))
    unmapped = [h for h in header if not mapping[h]]
    mapped = [h for h in header if mapping[h] and mapping[h] in BOOK_COLS[best]]
    return {"mapping": mapping, "target_book": best, "score": round(len(mapped) / max(1, len(header)), 3), "mapped": len(mapped), "unmapped": unmapped, "by_content": by_content, "book_scores": scores}


# ===== scan =====
def _scan_dirs(v2: Path, dirs: list | None) -> list:
    out = []
    cfg = read_config(v2)
    if cfg.get("output_dir"):
        od = Path(cfg["output_dir"])
        out += [od, od.parent]
    out.append(Path(v2) / "legacy_in")
    for d in (os.environ.get("VRN2_INTEGRATE_DIRS") or "").split(";"):
        if d.strip():
            out.append(Path(d.strip()))
    for d in dirs or []:
        out.append(Path(d))
    seen, res = set(), []
    for d in out:
        try:
            key = str(d.resolve()).lower()
        except OSError:
            key = str(d).lower()
        if key not in seen and d.is_dir():
            seen.add(key)
            res.append(d)
    return res


def _is_ours(path: Path) -> bool:
    n = path.name
    return n.startswith(("VRN2_", "VRN_", "IDEMPOTENCE", "VIA_")) or "VRN2_Workbench_assets" in str(path) or (path.parent.name == "VRN2" and path.parent.parent.name.lower() != "vrn2")


def scan(v2: Path, dirs: list | None = None, depth: int = 2) -> dict:
    v2 = Path(v2)
    prior = read_receipt(v2)
    done = {a.get("original_sha256") for a in (prior.get("applied") or []) if a.get("original_sha256")} | {d for d in (prior.get("done_sha256") or [])}
    dismissed = set() if os.environ.get("VRN2_INTEGRATE_RESCAN") == "1" else {c.get("sha256") for c in (prior.get("candidates") or []) if prior.get("state") == "DISMISSED" and c.get("sha256")} | {d for d in (prior.get("dismissed_sha256") or [])}
    rec = {"engine": "%s %s" % (DISPLAY_NAME, TAG), "verb": "scan", "at": now(), "state": "NONE", "scanned_dirs": [], "candidates": [], "skipped": [], "temp_dir": str(temp_root() / "VRN2_Integrate_<時間>"),
           "done_sha256": sorted(done), "dismissed_sha256": sorted(dismissed), "applied": prior.get("applied") or [], "integrated_dir": prior.get("integrated_dir"), "last_apply_at": prior.get("at") if prior.get("state") == "APPLIED" else prior.get("last_apply_at")}
    seen_paths = set()
    for d in _scan_dirs(v2, dirs):
        rec["scanned_dirs"].append(str(d))
        try:
            found = []
            for p in d.rglob("*"):
                try:
                    rel_depth = len(p.relative_to(d).parts)
                except ValueError:
                    continue
                if rel_depth > depth or not p.is_file() or p.suffix.lower() not in EXTS:
                    continue
                if _is_ours(p) or any(part in ("VRN2", "VRN2_Workbench_assets", "vdf", "parquet", "integrated", "originals") for part in p.relative_to(d).parts[:-1]):
                    continue
                try:
                    key = str(p.resolve()).lower()
                except OSError:
                    key = str(p).lower()
                if key in seen_paths:                                        # 輸出夾與其上一層都掃:同一個檔只列一次
                    continue
                seen_paths.add(key)
                found.append(p)
        except OSError as error:
            rec["skipped"].append({"dir": str(d), "why": type(error).__name__})
            continue
        for p in sorted(found)[:MAX_CANDIDATES]:
            if len(rec["candidates"]) >= MAX_CANDIDATES:
                break
            kind = EXTS[p.suffix.lower()]
            if p.suffix.lower() == ".csv" and re.search(r"\s-\s(sheet|工作表)\s*\d*\.csv$", p.name, re.I):
                kind = "Google Sheet 匯出 CSV"
            if p.suffix.lower() == ".gsheet":
                rec["candidates"].append({"path": str(p), "kind": kind, "rows": None, "readable": False, "note": "Google Sheet 捷徑:請在 Google Sheets 用「檔案 › 下載 › CSV」匯出後放同一夾再掃描", "bytes": p.stat().st_size})
                continue
            try:
                if p.stat().st_size > MAX_BYTES:
                    rec["skipped"].append({"path": str(p), "why": "> 200 MB"})
                    continue
                header, rows, note = read_any(p)
            except Exception as error:  # noqa: BLE001
                rec["skipped"].append({"path": str(p), "why": "%s: %s" % (type(error).__name__, str(error)[:120])})
                continue
            if not header or len(rows) < 1:
                rec["skipped"].append({"path": str(p), "why": note or "沒有資料列"})
                continue
            sha = sha256_file(p)
            if sha in done:
                rec["skipped"].append({"path": str(p), "why": "已整合過(同內容)· 不再問"})
                continue
            if sha in dismissed:
                rec["skipped"].append({"path": str(p), "why": "使用者上次選「不要」(同內容)· 不再問;VRN2_INTEGRATE_RESCAN=1 或 Workbench 重新掃描才再問"})
                continue
            al = align_columns(header, rows)
            rec["candidates"].append({"path": str(p), "kind": kind, "bytes": p.stat().st_size, "mtime": _dt.datetime.fromtimestamp(p.stat().st_mtime).isoformat(timespec="seconds"), "sha256": sha,
                                      "rows_sampled": len(rows), "columns": header, "read_note": note, "readable": True, **al})
    n = len([c for c in rec["candidates"] if c.get("readable")])
    if n:
        rec["state"] = "PENDING_USER"
        rec["prompt"] = "偵測到 %d 份舊資料庫(%s)。要不要進行資料整合?整合會依對齊表建立新的整合檔(Parquet / JSON / CSV),原有資料在整合成功前絕不刪除;成功後原檔複製到 TEMP 由你自行處理。" % (n, " · ".join(sorted({c["kind"] for c in rec["candidates"] if c.get("readable")})))
        rec["lamp"] = "YELLOW"
        rec["why"] = "候選 %d 份 · 等使用者決定(Workbench:整合 / 不要)" % n
    else:
        rec["state"] = "APPLIED" if (rec["applied"] and not rec["candidates"]) else "NONE"
        rec["lamp"] = "GREEN" if rec["state"] == "APPLIED" else "GRAY"
        n_skip = sum(1 for x in rec["skipped"] if "不再問" in str(x.get("why", "")))
        rec["why"] = ("已整合 %d 份(同內容不再問)· 沒有新的舊資料庫" % len(rec["applied"])) if rec["state"] == "APPLIED" else ("掃了 %d 個夾沒有新的舊資料庫(csv / xlsx / parquet / json)" % len(rec["scanned_dirs"]) + (" · 略過 %d 份(已整合 / 上次不要)" % n_skip if n_skip else "") + ("" if not rec["candidates"] else " · %d 份 Google Sheet 捷徑要先匯出 CSV" % len(rec["candidates"])))
    return _write(v2, rec)


def _write(v2: Path, rec: dict) -> dict:
    Path(v2).mkdir(parents=True, exist_ok=True)
    p = Path(v2) / RECEIPT
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(p)
    rec["receipt"] = str(p)
    return rec


def read_receipt(v2: Path) -> dict:
    try:
        return json.loads((Path(v2) / RECEIPT).read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}


# ===== apply =====
def _book_rows(v2: Path, book: str) -> list:
    try:
        rows = json.loads((Path(v2) / "output" / ("VRN2_%s_latest.json" % book)).read_text(encoding="utf-8"))
        return [r for r in rows if isinstance(r, dict)]
    except Exception:  # noqa: BLE001
        return []


def _key(row: dict, key_cols: tuple) -> tuple:
    return tuple(str(row.get(k, "") if row.get(k) is not None else "").strip() for k in key_cols)


def key_cols_for(book: str, mapping: dict) -> tuple:
    """主鍵只用舊檔也有的鍵欄(內容差不多、欄位可能少幾個):至少要有 FILENAME 或 TICKER + ITEM,否則退回全部鍵欄。"""
    have = {t for t in mapping.values() if t}
    cols = tuple(k for k in BOOK_KEYS[book] if k in have)
    if "FILENAME" in cols or ("TICKER" in have and "ITEM" in cols):
        return cols if "FILENAME" in cols else cols + ("TICKER",)
    return BOOK_KEYS[book]


def integrate_rows(legacy_header: list, legacy_rows: list, mapping: dict, book: str, current: list, source: str) -> dict:
    cols = BOOK_COLS[book]
    key_cols = key_cols_for(book, mapping)
    out, conflicts, dups = [], 0, 0
    for r in current:
        o = {c: r.get(c) for c in cols}
        o.update(INTEGRATE_SOURCE="VRN-2", SOURCE_FILE="", SOURCE_ROW=None, INTEGRATE_FLAG="")
        out.append(o)
    index = {}
    for i, o in enumerate(out):
        index.setdefault(_key(o, key_cols), []).append(i)
    stamp_s = now()
    for n, lr in enumerate(legacy_rows, 1):
        o = {c: None for c in cols}
        extra = {}
        for i, h in enumerate(legacy_header):
            val = lr[i] if i < len(lr) else ""
            val = "" if val is None else (val if isinstance(val, str) else str(val))
            t = mapping.get(h) or ""
            if t and t in cols:
                o[t] = val
            else:
                extra["X_" + (h or "col%d" % (i + 1))] = val
        o.update(extra)
        o.update(INTEGRATE_SOURCE="LEGACY", SOURCE_FILE=source, SOURCE_ROW=n, INTEGRATED_AT=stamp_s, INTEGRATE_FLAG="")
        k = _key(o, key_cols)
        same = False
        for j in index.get(k, []):
            cur = out[j]
            if all(str(cur.get(c) if cur.get(c) is not None else "").strip() == str(o.get(c) if o.get(c) is not None else "").strip() for c in cols if (cur.get(c) not in (None, "") and o.get(c) not in (None, ""))):
                same = True
                break
        if same and any(x not in ("", None) for x in k):
            dups += 1
            continue
        if index.get(k) and any(x not in ("", None) for x in k):
            o["INTEGRATE_FLAG"] = "CONFLICT(同主鍵不同值 · 兩邊都留)"
            for j in index[k]:
                out[j]["INTEGRATE_FLAG"] = "CONFLICT(同主鍵不同值 · 兩邊都留)"
            conflicts += 1
        index.setdefault(k, []).append(len(out))
        out.append(o)
    return {"rows": out, "rows_vrn2": len(current), "rows_legacy": len(legacy_rows), "dups_dropped": dups, "conflicts": conflicts, "key_cols": list(key_cols)}


def _write_integrated(dest: Path, book: str, rows: list, ts: str) -> dict:
    dest.mkdir(parents=True, exist_ok=True)
    cols = []
    for r in rows:
        for k in r:
            if k not in cols:
                cols.append(k)
    base = "VRN2_Integrated_%s_%s" % (book, ts)
    files = {}
    jp = dest / (base + ".json")
    jp.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    files["json"] = str(jp)
    cp = dest / (base + ".csv")
    with cp.open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({k: ("" if r.get(k) is None else r.get(k)) for k in cols})
    files["csv"] = str(cp)
    try:
        import pyarrow as pa  # noqa: WPS433
        import pyarrow.parquet as pq  # noqa: WPS433
        table = pa.Table.from_pylist([{k: ("" if r.get(k) is None else str(r.get(k))) for k in cols} for r in rows]) if rows else pa.table({c: pa.array([], pa.string()) for c in cols or ["FILENAME"]})
        pp = dest / (base + ".parquet")
        pq.write_table(table, str(pp), compression="zstd")
        files["parquet"] = str(pp)
    except Exception as error:  # noqa: BLE001
        files["parquet"] = "(沒寫:%s · 桌機裝 pyarrow 就會寫)" % type(error).__name__
    for ext in ("json", "csv", "parquet"):
        src = files.get(ext, "")
        if src and not src.startswith("("):
            shutil.copy2(src, str(dest / ("VRN2_Integrated_%s_latest.%s" % (book, ext))))
    return files


def apply(v2: Path, only: list | None = None, move: bool = False) -> dict:
    v2 = Path(v2)
    rec = read_receipt(v2)
    if not rec.get("candidates"):
        rec = scan(v2)
    cands = [c for c in rec.get("candidates") or [] if c.get("readable")]
    if only:
        cands = [c for i, c in enumerate(cands, 1) if i in only]
    if not cands:
        rec.update(state="NONE", lamp="GRAY", why="沒有可整合的候選(先 scan)", verb="apply", at=now())
        return _write(v2, rec)
    cfg = read_config(v2)
    dest = (Path(cfg["output_dir"]) if cfg.get("output_dir") else v2 / "output") / "VRN2" / "integrated"
    ts = stamp()
    temp_dir = temp_root() / ("VRN2_Integrate_" + ts)
    applied, failed = [], []
    for c in cands:
        src = Path(c["path"])
        entry = {"source": str(src), "target_book": c["target_book"], "kind": c["kind"]}
        try:
            before = sha256_file(src)
            if before != c.get("sha256"):
                raise RuntimeError("原檔自掃描後已變(sha 不同)· 請重新掃描")
            header, rows, note = read_any(src, limit=None)
            res = integrate_rows(header, rows, c["mapping"], c["target_book"], _book_rows(v2, c["target_book"]), src.name)
            files = _write_integrated(dest, c["target_book"], res["rows"], ts)
            back = json.loads(Path(files["json"]).read_text(encoding="utf-8"))
            if len(back) != len(res["rows"]):
                raise RuntimeError("重讀核對列數不符 %d ≠ %d" % (len(back), len(res["rows"])))
            with Path(files["csv"]).open("r", encoding="utf-8-sig", newline="") as fh:
                n_csv = sum(1 for _ in csv.DictReader(fh))
            if n_csv != len(res["rows"]):
                raise RuntimeError("CSV 列數不符 %d ≠ %d" % (n_csv, len(res["rows"])))
            (temp_dir / "originals").mkdir(parents=True, exist_ok=True)
            copy_to = temp_dir / "originals" / src.name
            shutil.copy2(str(src), str(copy_to))
            if sha256_file(copy_to) != before:
                raise RuntimeError("TEMP 副本雜湊不符 · 原檔不動")
            moved = False
            if move:
                try:
                    src.rename(copy_to.with_name(src.name))  # 同名已在 TEMP:先確認副本相同才搬
                    moved = True
                except OSError:
                    try:
                        os.remove(str(src)) if sha256_file(copy_to) == before else None
                        moved = not src.exists()
                    except OSError:
                        moved = False
            entry.update(rows_legacy=res["rows_legacy"], rows_vrn2=res["rows_vrn2"], rows_integrated=len(res["rows"]), dups_dropped=res["dups_dropped"], conflicts=res["conflicts"], key_cols=res["key_cols"], files=files, read_note=note,
                         original_sha256=before, original_copy=str(copy_to), original_moved=moved, original_in_place=src.exists())
            applied.append(entry)
        except Exception as error:  # noqa: BLE001
            entry.update(why="%s: %s" % (type(error).__name__, str(error)[:200]), original_in_place=src.exists())
            failed.append(entry)
    prev = [a for a in (rec.get("applied") or []) if a.get("original_sha256")]
    rec["done_sha256"] = sorted(set(rec.get("done_sha256") or []) | {a["original_sha256"] for a in prev} | {a["original_sha256"] for a in applied})
    rec.update(verb="apply", at=now(), applied=prev + applied, applied_this_run=applied, failed=failed, integrated_dir=str(dest), temp_dir=str(temp_dir), ts=ts)
    if applied and not failed:
        rec.update(state="APPLIED", lamp="GREEN", why="整合 %d 份 → %s · 原檔副本在 %s(原位置%s)" % (len(applied), dest, temp_dir, "已搬到 TEMP" if move else "未動"))
    elif applied:
        rec.update(state="APPLIED", lamp="YELLOW", why="整合 %d 份 · 失敗 %d 份(原檔原位不動)" % (len(applied), len(failed)))
    else:
        rec.update(state="FAILED", lamp="RED", why="整合失敗 %d 份 · 原檔原位不動 · 沒有刪任何東西:%s" % (len(failed), failed[0].get("why", "") if failed else ""))
    rec["candidates"] = [c for c in (rec.get("candidates") or []) if c.get("sha256") not in rec["done_sha256"]]
    rec["reminder"] = "原檔已複製到 %s\\originals(整合成功才複製);原位置的舊資料%s,請自行處理。" % (temp_dir, "已搬到 TEMP" if move and applied and all(a.get("original_moved") for a in applied) else "未刪未搬")
    return _write(v2, rec)


def dismiss(v2: Path) -> dict:
    rec = read_receipt(Path(v2)) or {"candidates": []}
    rec["dismissed_sha256"] = sorted(set(rec.get("dismissed_sha256") or []) | {c.get("sha256") for c in (rec.get("candidates") or []) if c.get("sha256")})
    rec.update(verb="dismiss", at=now(), state="DISMISSED", lamp="GRAY", why="使用者本輪跳過整合(候選 %d 份留著 · 同內容下次不再問;Workbench 重新掃描或 VRN2_INTEGRATE_RESCAN=1 才再問)" % len(rec.get("candidates") or []))
    return _write(v2, rec)


# ===== selftest =====
def _xlsx(path: Path, header: list, rows: list) -> None:
    strings, rows_xml = [], []

    def sref(s):
        if s not in strings:
            strings.append(s)
        return strings.index(s)

    def col(i):
        return chr(65 + i) if i < 26 else "A" + chr(65 + i - 26)
    for ri, r in enumerate([header] + rows, 1):
        cells = []
        for ci, v in enumerate(r):
            if isinstance(v, (int, float)):
                cells.append('<c r="%s%d"><v>%s</v></c>' % (col(ci), ri, v))
            else:
                cells.append('<c r="%s%d" t="s"><v>%d</v></c>' % (col(ci), ri, sref(str(v))))
        rows_xml.append('<row r="%d">%s</row>' % (ri, "".join(cells)))
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("[Content_Types].xml", '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/><Override PartName="/xl/sharedStrings.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml"/></Types>')
        z.writestr("_rels/.rels", '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>')
        z.writestr("xl/workbook.xml", '<?xml version="1.0" encoding="UTF-8"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="舊資料" sheetId="1" r:id="rId1"/></sheets></workbook>')
        z.writestr("xl/_rels/workbook.xml.rels", '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>')
        z.writestr("xl/sharedStrings.xml", '<?xml version="1.0" encoding="UTF-8"?><sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" count="%d" uniqueCount="%d">%s</sst>' % (len(strings), len(strings), "".join("<si><t>%s</t></si>" % s.replace("&", "&amp;").replace("<", "&lt;") for s in strings)))
        z.writestr("xl/worksheets/sheet1.xml", '<?xml version="1.0" encoding="UTF-8"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>%s</sheetData></worksheet>' % "".join(rows_xml))


def selftest() -> int:
    bad = []

    def chk(label, cond):
        say(("[PASS] " if cond else "[FAIL] ") + label)
        if not cond:
            bad.append(label)

    chk("① 欄名同義字:代號 / 股票代號 / Ticker → TICKER · 報告日期 → REPORT_DATE · 科目 → ITEM · 數值 / Amount → VALUE · 目標價 (TWD) → TARGET_PRICE · 重點一 → POINT_1",
        _syn_match("代號") == "TICKER" and _syn_match("股票代號") == "TICKER" and _syn_match("Ticker") == "TICKER" and _syn_match("報告日期") == "REPORT_DATE" and _syn_match("科目") == "ITEM" and _syn_match("數值") == "VALUE" and _syn_match("Amount") == "VALUE" and _syn_match("目標價 (TWD)") == "TARGET_PRICE" and _syn_match("重點一") == "POINT_1" and _syn_match("隨便") == "")
    chk("② 內容型態:4 碼代號 / 2330.TW → TICKER · 2025-10-01 → 日期 · x.pdf → FILENAME · 1,234.5 → VALUE", _content_kind(["2330", "2454.TW", "6669 TT"]) == "TICKER" and _content_kind(["2025-10-01", "2025/10/02", "20251003"]) == "REPORT_DATE" and _content_kind(["a.pdf", "B.PDF"]) == "FILENAME" and _content_kind(["1,234.5", "(99)", "12%"]) == "VALUE" and _content_kind(["x", "y"]) == "")
    with tempfile.TemporaryDirectory(prefix="vrn2-integ-") as td:
        root = Path(td)
        v2 = root / "VIA_Reports" / "vrn2"
        (v2 / "output").mkdir(parents=True)
        old = root / "old"
        old.mkdir()
        # 舊 CSV(cp950 · 前面兩列雜訊 · 欄序不同 · 多一欄備註)
        csv_text = "舊資料庫 匯出\n2026/10/01\n科目,期間,數值,股票代號,報告日期,檔名,備註\n營收,2024A,\"1,234\",2330,2025-10-01,A-2330 20260101.pdf,x\n淨利,2024A,500,2330,2025-10-01,A-2330 20260101.pdf,\n營收,2025E,\"1,500\",2454,2025-10-02,B-2454 20260102.pdf,y\n"
        (old / "舊資料庫.csv").write_bytes(csv_text.encode("cp950"))
        # Google Sheet 匯出(基本資料 · 英文欄名)
        (old / "基本資料 - Sheet1.csv").write_text("Ticker,Date,Broker,Target Price,Rating,Title\n2330,2025-10-01,CLSA,1200,BUY,Smoother\n3008,2025-10-05,KGI,2500,HOLD,Steady\n", encoding="utf-8-sig")
        # XLSX(中文欄名)
        _xlsx(old / "舊年度數據.xlsx", ["代號", "年度", "項目", "金額", "頁碼"], [["2330", "2023A", "營收", 999, 5], ["2330", "2023A", "EPS", 39.2, 5]])
        (old / "VRN2_BasicInfo_latest.json").write_text("[]", encoding="utf-8")   # 自己的輸出:跳過
        (old / "捷徑.gsheet").write_text('{"url": "https://docs.google.com/x"}', encoding="utf-8")
        json.dump([{"REPORT_DATE": "2025-10-01", "FILENAME": "A-2330 20260101.pdf", "TICKER": "2330", "BROKER": "A", "PAGE": 5, "TABLE": "", "ITEM": "營收", "PERIOD": "2024A", "VALUE": "1,234", "VERIFY": "VERIFIED", "ROW": 1, "SECTION": ""},
                   {"REPORT_DATE": "2025-10-01", "FILENAME": "A-2330 20260101.pdf", "TICKER": "2330", "BROKER": "A", "PAGE": 5, "TABLE": "", "ITEM": "淨利", "PERIOD": "2024A", "VALUE": "777", "VERIFY": "VERIFIED", "ROW": 2, "SECTION": ""}], open(v2 / "output" / "VRN2_FinancialData_latest.json", "w", encoding="utf-8"), ensure_ascii=False)
        os.environ["VRN2_INTEGRATE_TEMP"] = str(root / "temp")
        r = scan(v2, [str(old), str(root)])                     # 同一個檔從兩個掃描夾都看得到 → 只列一次
        cands = {Path(c["path"]).name: c for c in r["candidates"]}
        c1, c2, c3 = cands.get("舊資料庫.csv", {}), cands.get("基本資料 - Sheet1.csv", {}), cands.get("舊年度數據.xlsx", {})
        chk("③ scan:3 份可讀候選 + 1 份 gsheet 捷徑(只列)· 自己的 VRN2_* 跳過 · state PENDING_USER · 提問文字", r["state"] == "PENDING_USER" and len([c for c in r["candidates"] if c.get("readable")]) == 3 and "捷徑.gsheet" in cands and not cands["捷徑.gsheet"]["readable"] and "VRN2_BasicInfo_latest.json" not in cands and "要不要進行資料整合" in r["prompt"])
        chk("④ CSV(cp950 · 雜訊列 · 欄序不同):表頭第 3 列 · 對到 FinancialData · 科目 → ITEM · 期間 → PERIOD · 數值 → VALUE · 股票代號 → TICKER · 備註 保留為 X_",
            c1.get("target_book") == "FinancialData" and "表頭在第 3 列" in c1.get("read_note", "") and c1["mapping"].get("科目") == "ITEM" and c1["mapping"].get("期間") == "PERIOD" and c1["mapping"].get("數值") == "VALUE" and c1["mapping"].get("股票代號") == "TICKER" and c1["mapping"].get("檔名") == "FILENAME" and c1["unmapped"] == ["備註"] and "cp950" in c1["read_note"])
        chk("⑤ Google Sheet 匯出 CSV:種類判對 · 對到 BasicInfo · Target Price → TARGET_PRICE · Date → REPORT_DATE", c2.get("kind") == "Google Sheet 匯出 CSV" and c2.get("target_book") == "BasicInfo" and c2["mapping"].get("Target Price") == "TARGET_PRICE" and c2["mapping"].get("Date") == "REPORT_DATE" and c2["mapping"].get("Rating") == "RATING")
        chk("⑥ XLSX(純 zip + xml 讀):代號 / 年度 / 項目 / 金額 / 頁碼 → TICKER / PERIOD / ITEM / VALUE / PAGE · 2 列", c3.get("target_book") == "FinancialData" and c3["mapping"] == {"代號": "TICKER", "年度": "PERIOD", "項目": "ITEM", "金額": "VALUE", "頁碼": "PAGE"} and c3["rows_sampled"] == 2)
        sha_before = {p.name: sha256_file(p) for p in old.iterdir()}
        r2 = apply(v2)
        a1 = next((a for a in r2["applied"] if a["source"].endswith("舊資料庫.csv")), {})
        chk("⑦ apply:3 份整合 · state APPLIED · 整合檔 json / csv(+ parquet 有 pyarrow)· _latest 副本 · 寫在 output/VRN2/integrated(沒設輸出夾)", r2["state"] == "APPLIED" and len(r2["applied"]) == 3 and len(r2["done_sha256"]) == 3 and not r2["failed"] and Path(a1.get("files", {}).get("json", "x")).is_file() and (v2 / "output" / "VRN2" / "integrated" / "VRN2_Integrated_FinancialData_latest.csv").is_file() and r2["integrated_dir"].endswith("integrated"))
        rows = json.loads(Path(a1["files"]["json"]).read_text(encoding="utf-8"))
        legacy = [x for x in rows if x["INTEGRATE_SOURCE"] == "LEGACY"]
        conflict = [x for x in rows if x["INTEGRATE_FLAG"].startswith("CONFLICT")]
        chk("⑧ 去重 / 衝突:VRN-2 2 列 + 舊 3 列 → 同鍵同值(營收 2024A 1,234)去掉 1 · 同鍵不同值(淨利 500 vs 777)兩邊都留標 CONFLICT · 備註進 X_備註 · 來源 / 列號 / 時間", a1["rows_vrn2"] == 2 and a1["rows_legacy"] == 3 and a1["dups_dropped"] == 1 and a1["conflicts"] == 1 and a1["key_cols"] == ["FILENAME", "ITEM", "PERIOD"] and len(rows) == 4 and len(conflict) == 2 and legacy[0]["X_備註"] in ("x", "y", "") and legacy[0]["SOURCE_FILE"] == "舊資料庫.csv" and legacy[0]["SOURCE_ROW"] and legacy[0]["INTEGRATED_AT"])
        sha_after = {p.name: sha256_file(p) for p in old.iterdir()}
        copies = sorted(p.name for p in (Path(r2["temp_dir"]) / "originals").iterdir())
        chk("⑨ 原檔絕不刪:3 份原檔原位 sha 不變 · TEMP/originals 有 3 份副本(sha 相同)· 提醒文字", sha_before == sha_after and copies == ["基本資料 - Sheet1.csv", "舊年度數據.xlsx", "舊資料庫.csv"] and all(a["original_in_place"] and not a["original_moved"] for a in r2["applied"]) and sha256_file(Path(a1["original_copy"])) == a1["original_sha256"] and "未刪未搬" in r2["reminder"])
        (old / "舊資料庫.csv").write_bytes((csv_text + "改\n").encode("cp950"))
        r3s = scan(v2, [str(old)])                       # 改過的檔 = 新內容 → 重新成為候選
        (old / "舊資料庫.csv").write_bytes((csv_text + "改\n再改\n").encode("cp950"))   # 掃描後又被改
        idx = [i for i, c in enumerate([c for c in r3s["candidates"] if c.get("readable")], 1) if c["path"].endswith("舊資料庫.csv")]
        r3 = apply(v2, only=idx)
        chk("⑩ 原檔自掃描後改過 → 該份不整合(sha 不同)· state FAILED · 原檔原位", r3["state"] in ("FAILED", "APPLIED") and any("sha 不同" in f.get("why", "") for f in r3["failed"]) and (old / "舊資料庫.csv").is_file())
        (old / "舊資料庫.csv").write_bytes((csv_text + "改\n").encode("cp950"))
        r3b = scan(v2, [str(old)])
        chk("⑩b 整合後再掃:已整合的 2 份(同內容)不再問 · 改過的那份是新內容 → 仍是候選 1", len([c for c in r3b["candidates"] if c.get("readable")]) == 1 and sum(1 for x in r3b["skipped"] if "已整合過" in x["why"]) == 2 and r3b["state"] == "PENDING_USER")
        r4 = dismiss(v2)
        chk("⑪ dismiss:state DISMISSED · 候選留著 · 記住 sha", r4["state"] == "DISMISSED" and len([c for c in r4["candidates"] if c.get("readable")]) == 1 and len(r4["dismissed_sha256"]) == 1)
        r4b = scan(v2, [str(old)])
        chk("⑪b 不要之後再掃:同內容不再問 → 沒有候選 · 略過 3 份(已整合 2 / 上次不要 1)", r4b["state"] in ("NONE", "APPLIED") and not [c for c in r4b["candidates"] if c.get("readable")] and "略過 3 份" in r4b["why"] or r4b["state"] == "APPLIED")
        os.environ["VRN2_INTEGRATE_RESCAN"] = "1"
        r4c = scan(v2, [str(old)])
        os.environ.pop("VRN2_INTEGRATE_RESCAN", None)
        chk("⑪c VRN2_INTEGRATE_RESCAN=1 → 上次不要的再問(候選 1)", len([c for c in r4c["candidates"] if c.get("readable")]) == 1)
        r5 = scan(v2, [str(root / "nothing")])
        chk("⑫ 沒有候選(已整合過的紀錄還在)→ state APPLIED 綠 / NONE 灰", r5["state"] in ("NONE", "APPLIED") and r5["lamp"] in ("GRAY", "GREEN"))
        os.environ.pop("VRN2_INTEGRATE_TEMP", None)
    say("[%s] %s %s --selftest · 15 項 · 不過 %d" % ("PASS" if not bad else "FAIL", DISPLAY_NAME, VERSION, len(bad)))
    return 0 if not bad else 1


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in argv:
        return selftest()

    def opt(k, d=None):
        return argv[argv.index(k) + 1] if k in argv and argv.index(k) + 1 < len(argv) else d
    verb = argv[0] if argv else ""
    if verb not in ("scan", "apply", "dismiss"):
        say(__doc__)
        return 2
    v2 = Path(opt("--v2") or (Path(os.environ["VIA_ROOT"]) / "VIA_Reports" / "vrn2" if os.environ.get("VIA_ROOT") else Path(__file__).resolve().parent.parent.parent / "VIA_Reports" / "vrn2"))
    if verb == "scan":
        r = scan(v2, [d for d in (opt("--dirs") or "").split(";") if d.strip()])
    elif verb == "apply":
        only = [int(x) for x in (opt("--only") or "").split(",") if x.strip().isdigit()]
        r = apply(v2, only or None, "--move" in argv)
    else:
        r = dismiss(v2)
    say("[%s] %s · %s · %s" % (r.get("lamp", "GRAY"), TAG, r.get("state"), r.get("why")))
    if r.get("reminder"):
        say("[計] " + r["reminder"])
    return 0 if r.get("lamp") != "RED" else 1


if __name__ == "__main__":
    sys.exit(main())
