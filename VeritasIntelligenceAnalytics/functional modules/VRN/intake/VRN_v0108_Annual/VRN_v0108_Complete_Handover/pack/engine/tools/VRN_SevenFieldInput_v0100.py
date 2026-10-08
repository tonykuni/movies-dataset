#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""七欄基本資料擷取；來源及衝突另存 audit；不改輸入或正式 SSOT。"""
from __future__ import annotations

# 01 | 可調參數（集中於頂部）
PARAMS = {
    "input_root": r"C:\測試樣本報告",
    "manifest": "VRN_TestInput_Links_20261005.csv",
    "output_root": "VRN_SevenField_Output",
    "repo_root": "",
    "roster": "",
    "max_pdf_pages": 2,
    "header_ratio": 0.28,
    "footer_ratio": 0.94,
    "ocr_dpi": 180,
    "ocr_timeout": 60,
    "ocr_language": "eng",
    "text_limit": 22000,
    "version": "v0100",
}
CORE_COLUMNS = ["REPORT_DATE", "FILENAME", "FORMAT", "SIZE", "TICKER", "NAME", "BROKER"]
BROKER_DISPLAY = {
    "CTBC": "中國信託證券投顧", "KGI": "凱基投顧", "HUANAN": "華南投顧",
    "MEGA": "兆豐投顧", "CATHAY": "國泰證期研究部", "CAPITAL": "群益證券",
    "TAISHIN": "台新投顧", "PRESIDENT": "統一投顧", "GS": "高盛",
    "MS": "摩根士丹利", "UBS": "瑞銀", "JPM": "摩根大通", "CITI": "花旗",
    "DAIWA": "大和證券", "MACQUARIE": "麥格理", "CLSA": "里昂證券",
    "GF": "廣發證券", "GFHK": "廣發證券（香港）",
}
BROKER_CONTENT = {
    "MS": [r"Morgan\s*Stanley", r"morganstanley\.com"],
    "JPM": [r"J\s*P\s*M\s*O\s*R\s*G\s*A\s*N", r"J\.?\s*P\.?\s*Morgan", r"jpmorgan\.com"],
    "MACQUARIE": [r"Macquarie"], "KGI": [r"凱基投顧", r"@kgi\.com"],
    "CTBC": [r"中國信託證券投顧", r"ctbcsis\.com", r"CTBC SECURITIES"],
    "HUANAN": [r"華南投顧"], "UBS": [r"\bUBS\b", r"@ubs\.com"],
    "CITI": [r"Citi Research", r"@citi\.com"], "GS": [r"Goldman Sachs", r"@gs\.com"],
    "DAIWA": [r"Daiwa", r"大和證券"], "CLSA": [r"\bCLSA\b"],
}
MONTHS = {
    "January": 1, "February": 2, "March": 3, "April": 4, "May": 5, "June": 6,
    "July": 7, "August": 8, "September": 9, "October": 10, "November": 11, "December": 12,
    "一月": 1, "二月": 2, "三月": 3, "四月": 4, "五月": 5, "六月": 6,
    "七月": 7, "八月": 8, "九月": 9, "十月": 10, "十一月": 11, "十二月": 12,
}

# 02 | 通用載入、來源核對
import argparse
import csv
import hashlib
import html
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
import zipfile
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
if (HERE / "deps").is_dir():
    sys.path.insert(0, str(HERE / "deps"))


def load_module(path: Path, tag: str):
    spec = importlib.util.spec_from_file_location(tag, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"無法載入：{path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[tag] = module
    spec.loader.exec_module(module)
    return module


def latest(directory: Path, stem: str) -> Path:
    files = list(directory.glob(stem + "_v*.py"))
    if not files:
        raise FileNotFoundError(f"缺工具：{directory / stem}")
    return max(files, key=lambda p: int(re.search(r"_v(\d+)\.py$", p.name).group(1)))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def load_tools(repo: str):
    vdf_dir = Path(repo) / "functional modules" / "VDF" if repo else HERE / "repo_tools"
    if not vdf_dir.is_dir():
        vdf_dir = HERE / "repo_tools"
    vdf_path = latest(vdf_dir, "VDF_MDL009_TWStockList")
    reader_path = Path(repo) / "functional modules" / "VRN" / "vrn_sample_reader.py" if repo else HERE / "repo_tools" / "vrn_sample_reader.py"
    if not reader_path.is_file():
        reader_path = HERE / "repo_tools" / "vrn_sample_reader.py"
    return load_module(vdf_path, "vrn_input_vdf_tool"), load_module(reader_path, "vrn_input_reader"), {
        "VDF_TOOL_PATH": str(vdf_path), "VDF_TOOL_SHA256": sha256(vdf_path),
        "VRN_READER_PATH": str(reader_path), "VRN_READER_SHA256": sha256(reader_path),
        "VDF_FUNCTION": "keyed_row_v0100", "VRN_FUNCTION": "find_broker / read_text",
    }


def canonical_date(y: str | int, m: str | int, d: str | int) -> str | None:
    try:
        yy = int(y)
        yy = yy + 1911 if 100 <= yy < 200 else (2000 + yy if yy < 100 else yy)
        return date(yy, int(m), int(d)).isoformat() if 1900 <= yy <= 2100 else None
    except (ValueError, TypeError):
        return None


def dates_in(text: str, compact: bool = False) -> list[dict]:
    s = unicodedata.normalize("NFKC", text)
    result = []
    patterns = [
        (r"(?<!\d)(\d{3,4})\s*[年/.-]\s*(\d{1,2})\s*[月/.-]\s*(\d{1,2})(?:\s*日)?(?!\d)", "SEPARATED"),
    ]
    if compact:
        patterns += [
            (r"(?<!\d)(20\d{2})([01]\d)([0-3]\d)(?!\d)", "AD8"),
            (r"(?<!\d)(1\d{2})([01]\d)([0-3]\d)(?!\d)", "ROC7"),
            (r"(?<!\d)(\d{2})([01]\d)([0-3]\d)(?!\d)", "YYMMDD"),
        ]
    for pattern, kind in patterns:
        for m in re.finditer(pattern, s):
            value = canonical_date(*m.groups())
            if value:
                result.append({"date": value, "raw": m.group(0), "span": m.span(), "kind": kind})
    for name, month in MONTHS.items():
        token = re.escape(name)
        for pattern, reverse in [(rf"(?<!\d)(\d{{1,2}})\s+{token}\s*,?\s*(\d{{4}})(?!\d)", False),
                                 (rf"{token}\s*(\d{{1,2}})\s*,?\s+(\d{{4}})(?!\d)", False)]:
            for m in re.finditer(pattern, s, re.I):
                value = canonical_date(m.group(2), month, m.group(1))
                if value:
                    result.append({"date": value, "raw": m.group(0), "span": m.span(), "kind": "NAMED_MONTH"})
    # 去掉短日期與較長日期重疊的命中；絕不把無年 MMDD 補上當年。
    result.sort(key=lambda x: (x["span"][0], -(x["span"][1] - x["span"][0])))
    accepted = []
    for row in result:
        if not any(row["span"][0] < a["span"][1] and a["span"][0] < row["span"][1] for a in accepted):
            accepted.append(row)
    return accepted


def load_official_names(vdf, roster: str) -> tuple[dict, dict]:
    names, sources = {}, []
    if roster:
        import pandas as pd
        p = Path(roster)
        frame = pd.read_parquet(p) if p.suffix.lower() == ".parquet" else pd.read_csv(p, dtype=str, encoding="utf-8-sig")
        for record in frame.fillna("").to_dict("records"):
            code = str(record.get("ticker", "")).strip()
            market = str(record.get("market", "")).upper()
            if not re.fullmatch(r"[1-9]\d{3}", code) or market not in ("TWSE", "TPEX"):
                continue
            r = vdf.keyed_row_v0100(str(record.get("date", "")), code, str(record.get("name", "")), market)
            r.update(name_source="VDF_MASTER_LIST", source_url=vdf.SRC["twse_basic" if market == "TWSE" else "tpex_basic"], source_path=str(p))
            if r["name"]:
                names[code] = r
        sources.append({"path": str(p), "sha256": sha256(p), "mode": "VDF_MASTER_LIST"})
    else:
        for market, filename in [("TWSE", "twse_basic_snapshot_20260805.json"), ("TPEX", "tpex_basic_snapshot_20260805.json")]:
            p = HERE / "official_raw" / filename
            rows = json.loads(p.read_text(encoding="utf-8"))
            for record in rows:
                code = str(record.get("公司代號") or record.get("SecuritiesCompanyCode") or "").strip()
                short = str(record.get("公司簡稱") or record.get("CompanyAbbreviation") or "").strip()
                if not re.fullmatch(r"[1-9]\d{3}", code) or not short:
                    continue
                raw_date = str(record.get("出表日期") or record.get("Date") or "")
                found = dates_in(raw_date, compact=True)
                r = vdf.keyed_row_v0100(found[0]["date"] if found else "", code, short, market)
                r.update(name_source="VDF_OFFICIAL_SNAPSHOT", source_url=vdf.SRC["twse_basic" if market == "TWSE" else "tpex_basic"],
                         source_path=str(p), full_name=record.get("公司名稱") or record.get("CompanyName"),
                         english_name=record.get("英文簡稱") or record.get("Symbol") or "")
                if code in names and names[code]["market"] != market:
                    raise RuntimeError(f"兩所重號：{code}")
                names[code] = r
            sources.append({"path": str(p), "sha256": sha256(p), "mode": "OFFICIAL_SNAPSHOT", "source_rows": len(rows)})
    if not names:
        raise RuntimeError("VDF 名冊為空；無法核对 NAME。")
    return names, {"name_count": len(names), "sources": sources, "tool": vdf.TAG}


# 03 | 讀取實體檔案：格式、大小、首頁版面與必要 OCR
def detect_format(path: Path) -> str:
    with path.open("rb") as fh:
        head = fh.read(1024)
    if b"%PDF-" in head:
        return "PDF"
    if head.startswith(b"PK"):
        try:
            with zipfile.ZipFile(path) as z:
                if "word/document.xml" in z.namelist():
                    return "DOCX"
        except zipfile.BadZipFile:
            return "CORRUPT_ZIP"
    if head.startswith(b"\xff\xd8\xff"):
        return "JPG"
    if head.startswith(b"\x89PNG"):
        return "PNG"
    if head.startswith(bytes.fromhex("D0CF11E0A1B11AE1")):
        return "OLE_DOCUMENT"
    return "TXT" if path.suffix.lower() == ".txt" else "UNKNOWN"


def ocr_image(image_path: Path) -> tuple[str, str]:
    executable = shutil.which("tesseract")
    if not executable:
        return "", "OCR_TOOL_ABSENT"
    r = subprocess.run([executable, str(image_path), "stdout", "-l", PARAMS["ocr_language"], "--psm", "3"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=PARAMS["ocr_timeout"])
    return (r.stdout, "TESSERACT_OCR") if r.returncode == 0 else ("", "OCR_ERROR:" + r.stderr[:150])


def read_document(path: Path, fmt: str, reader) -> dict:
    result = {"text": "", "header_lines": [], "method": "", "page_count": None, "error": ""}
    try:
        if fmt == "PDF":
            import fitz
            with fitz.open(path) as doc:
                result["page_count"] = len(doc)
                texts = []
                for i in range(min(len(doc), PARAMS["max_pdf_pages"])):
                    page = doc[i]
                    raw = page.get_text(sort=True)
                    if len(raw.strip()) < 30:
                        with tempfile.TemporaryDirectory(prefix="VRN_HeaderOCR_") as tmp:
                            image_path = Path(tmp) / "page.png"
                            page.get_pixmap(dpi=PARAMS["ocr_dpi"]).save(image_path)
                            raw, method = ocr_image(image_path)
                            result["method"] += f"P{i + 1}:{method};"
                            # OCR 全頁首段作候選；OCR 證據一直保持標記。
                            for line in raw.splitlines()[:15]:
                                result["header_lines"].append({"text": line, "page": i + 1, "y": None, "method": method})
                    else:
                        result["method"] += f"P{i + 1}:PYMUPDF_LAYOUT;"
                        for block in page.get_text("dict")["blocks"]:
                            for line in block.get("lines", []):
                                s = "".join(span["text"] for span in line["spans"])
                                y = line["bbox"][1] / page.rect.height
                                if y <= PARAMS["header_ratio"] or y >= PARAMS["footer_ratio"]:
                                    result["header_lines"].append({"text": s, "page": i + 1, "y": round(y, 5), "method": "PYMUPDF_LAYOUT"})
                    texts.append(raw)
                result["text"] = "\n".join(texts)[:PARAMS["text_limit"]]
            # PyMuPDF 缺字/空白時再讀既有 VRN reader（其 PDF 讀法是 pypdf）。
            if not result["text"].strip():
                text, method = reader.read_text(path, PARAMS["text_limit"])
                result["text"], result["method"] = text, result["method"] + method
        elif fmt in ("DOCX", "TXT"):
            text, method = reader.read_text(path, PARAMS["text_limit"])
            result.update(text=text, method=method)
            for line in text.splitlines()[:10]:
                result["header_lines"].append({"text": line, "page": 1, "y": None, "method": method})
        elif fmt in ("JPG", "PNG"):
            text, method = ocr_image(path)
            result.update(text=text[:PARAMS["text_limit"]], method=method)
            result["header_lines"] = [{"text": x, "page": 1, "y": None, "method": method} for x in text.splitlines()[:15]]
        else:
            result["method"] = "UNSUPPORTED_SIGNATURE"
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {str(exc)[:200]}"
        result["method"] = result["method"] or "READ_ERROR"
    return result


# 04 | 日期／代碼／券商比對；所有衝突保留
def filename_tickers(filename: str, names: dict) -> list[str]:
    s = unicodedata.normalize("NFKC", Path(filename).stem)
    for row in reversed(dates_in(s, compact=True)):
        a, b = row["span"]
        s = s[:a] + " " * (b - a) + s[b:]
    candidates = []
    for m in re.finditer(r"(?<!\d)([1-9]\d{3})(?!\d)", s):
        code = m.group(1)
        # 年份標題不可當代碼；真年區代碼仍可由名稱／代號位置核對。
        if re.match(r"\s*年", s[m.end():]):
            continue
        if code.startswith(("19", "20")) and m.end() < len(s) and re.match(r"[A-Za-z\u4e00-\u9fff]", s[m.end():]):
            if code not in names or names[code]["name"] not in s:
                continue
        candidates.append(code)
    return list(dict.fromkeys(candidates))


def document_tickers(document: dict, names: dict) -> list[str]:
    s = unicodedata.normalize("NFKC", document["text"])
    codes = re.findall(r"(?<!\d)([1-9]\d{3})(?:\s*\.\s*TW(?:O)?\b|\s*TT\b)", s, re.I)
    for line in document["header_lines"]:
        text = line["text"]
        for m in re.finditer(r"[\u4e00-\u9fffA-Za-z][^()]{0,40}\(([1-9]\d{3})\)", text):
            code = m.group(1)
            if code in names:
                codes.append(code)
    return list(dict.fromkeys(codes))


def filename_broker(filename: str, reader) -> tuple[str | None, str]:
    stem = Path(filename).stem
    if re.search(r"(?<![A-Z])GFHK(?![A-Z])", stem, re.I):
        return "GFHK", "FILENAME_CANDIDATE"
    if re.search(r"(?<![A-Z])GF(?![A-Z])", stem, re.I) or "廣發" in stem:
        return "GF", "FILENAME_CANDIDATE"
    broker, source = reader.find_broker(stem)
    return broker, source


def extract_record(entry: dict, root: Path, names: dict, reader) -> tuple[dict, dict]:
    filename = entry["filename"]
    if Path(filename).name != filename:
        raise ValueError("清單 filename 必須是單一檔名。")
    path = root / filename
    exists = path.is_file()
    fmt = detect_format(path) if exists else Path(filename).suffix.lstrip(".").upper()
    size = path.stat().st_size if exists else None
    doc = read_document(path, fmt, reader) if exists else {"text": "", "header_lines": [], "method": "FILE_NOT_AVAILABLE", "page_count": None, "error": ""}
    file_dates = dates_in(filename, compact=True)
    header_dates = []
    for line in doc["header_lines"]:
        for found in dates_in(line["text"], compact=fmt in ("DOCX", "TXT")):
            # 不採前日價格、歷史評等、財表日期作報告日期。
            if re.search(r"收盤|closing|price\s*\(|target|前次|前日", line["text"], re.I):
                continue
            header_dates.append({**found, **line})
    header_values = list(dict.fromkeys(x["date"] for x in header_dates))
    file_date = file_dates[0]["date"] if file_dates else None
    report_date = header_values[0] if len(header_values) == 1 else file_date
    report_source = "DOCUMENT_HEADER" if len(header_values) == 1 else ("FILENAME" if file_date else "NODATA")
    ft = filename_tickers(filename, names)
    dt = document_tickers(doc, names)
    ticker = ft[0] if len(ft) == 1 else (dt[0] if not ft and len(dt) == 1 else None)
    ticker_source = "FILENAME" if len(ft) == 1 else ("DOCUMENT" if ticker else "NODATA_OR_MULTI")
    broker, broker_source = filename_broker(filename, reader)
    broker_hits = [code for code, patterns in BROKER_CONTENT.items() if any(re.search(rx, doc["text"], re.I) for rx in patterns)]
    if not broker and len(broker_hits) == 1:
        broker, broker_source = broker_hits[0], "DOCUMENT"
    official = names.get(ticker, {}) if ticker else {}
    flags = []
    if file_date and header_values and any(x != file_date for x in header_values):
        flags.append("DATE_CONFLICT")
    if len(header_values) > 1:
        flags.append("MULTIPLE_HEADER_DATES")
    if len(ft) > 1 or (not ft and len(dt) > 1):
        flags.append("MULTIPLE_TICKERS")
    if ticker and dt and ticker not in dt:
        flags.append("TICKER_CONFLICT")
    if broker_hits and broker and broker not in broker_hits:
        flags.append("BROKER_CONFLICT")
    if ticker and not official:
        flags.append("TICKER_NOT_IN_OFFICIAL_ROSTER")
    if exists and not doc["text"].strip():
        flags.append("DOCUMENT_TEXT_NODATA")
    if exists and fmt != Path(filename).suffix.lstrip(".").upper():
        flags.append("FORMAT_EXTENSION_MISMATCH")
    status = "MISSING_FILE" if not exists else ("REVIEW" if flags or doc["error"] else "READ_OK")
    core = dict(zip(CORE_COLUMNS, [report_date, filename, fmt, size, ticker, official.get("name"), BROKER_DISPLAY.get(broker, broker)]))
    audit = {"INPUT_ID": entry["input_id"], **core, "STATUS": status, "INPUT_PATH": str(path), "READ_METHOD": doc["method"],
             "FILE_SHA256": sha256(path) if exists else None, "PAGE_COUNT": doc["page_count"], "FORMAT_SOURCE": "SIGNATURE" if exists else "EXTENSION_ONLY",
             "REPORT_DATE_FILENAME": file_date, "REPORT_DATE_HEADER": header_values, "REPORT_DATE_SOURCE": report_source,
             "DATE_EVIDENCE": [{k: v for k, v in x.items() if k != "span"} for x in header_dates],
             "TICKER_FILENAME": ft, "TICKER_DOCUMENT": dt, "TICKER_SOURCE": ticker_source,
             "NAME_SOURCE": official.get("name_source"), "NAME_SOURCE_DATE": official.get("date"), "NAME_SOURCE_URL": official.get("source_url"),
             "MARKET": official.get("market"), "YF_TICKER": official.get("yf_ticker"), "BROKER_CODE": broker, "BROKER_SOURCE": broker_source,
             "BROKER_DOCUMENT": broker_hits, "FLAGS": flags, "READ_ERROR": doc["error"], "TEXT_CHARS": len(doc["text"])}
    return core, audit


# 05 | DataFrame／CSV／Parquet／DuckDB／可讀矩陣
def write_outputs(rows: list[dict], audits: list[dict], out: Path, evidence: dict) -> dict:
    import pandas as pd
    import pyarrow as pa
    import pyarrow.parquet as pq
    schema = pa.schema([(c, pa.int64() if c == "SIZE" else pa.string()) for c in CORE_COLUMNS])
    frame = pd.DataFrame(rows, columns=CORE_COLUMNS)
    frame["SIZE"] = pd.array(frame["SIZE"], dtype="Int64")
    frame.to_csv(out / "StockReportBasicInfo.csv", index=False, encoding="utf-8-sig")
    pq.write_table(pa.Table.from_pylist(rows, schema=schema), out / "StockReportBasicInfo.parquet", compression="zstd")
    flat = [{k: json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else v for k, v in a.items()} for a in audits]
    pd.DataFrame(flat).to_csv(out / "StockReportBasicInfo_Audit.csv", index=False, encoding="utf-8-sig")
    pq.write_table(pa.Table.from_pylist(flat), out / "StockReportBasicInfo_Audit.parquet", compression="zstd")
    (out / "StockReportBasicInfo.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    summary = {"rows": len(rows), "status": dict(Counter(a["STATUS"] for a in audits)),
               "date_conflicts": [a["INPUT_ID"] for a in audits if "DATE_CONFLICT" in a["FLAGS"]],
               "missing": {c: sum(r[c] is None or r[c] == "" for r in rows) for c in CORE_COLUMNS}, "evidence": evidence}
    try:
        import duckdb
        con = duckdb.connect(str(out / "VRN_SevenField.duckdb"))
        tmp = out / "_temp"
        tmp.mkdir(exist_ok=True)
        con.execute("SET temp_directory = ?", [str(tmp)])
        con.execute("SET memory_limit = '256MB'")
        con.execute("CREATE TABLE BasicInfo AS SELECT * FROM read_parquet(?)", [str(out / "StockReportBasicInfo.parquet")])
        con.execute("CREATE TABLE InputAudit AS SELECT * FROM read_parquet(?)", [str(out / "StockReportBasicInfo_Audit.parquet")])
        summary["duckdb_rows"] = con.execute("SELECT COUNT(*) FROM BasicInfo").fetchone()[0]
        con.close()
    except ImportError:
        summary["duckdb_status"] = "DEPENDENCY_ABSENT"
    (out / "RunSummary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    cells = []
    for a in audits:
        cells.append("<tr data-status='" + a["STATUS"] + "'>" + "".join("<td>" + html.escape(str(a.get(c) if a.get(c) is not None else "")) + "</td>"
                     for c in ["INPUT_ID", *CORE_COLUMNS, "STATUS", "FLAGS", "NAME_SOURCE_DATE"]) + "</tr>")
    markup = """<!doctype html><html lang='zh-Hant'><meta charset='utf-8'><title>VRN 七欄輸入核對</title>
<style>body{background:#faf8f3;color:#333;font:12px system-ui;margin:20px}h1{font-size:17px}table{border-collapse:collapse;width:100%}td,th{border:1px solid #ddd;padding:5px;text-align:left;word-break:break-word}tr[data-status=REVIEW]{background:#fff0cf}tr[data-status=MISSING_FILE]{color:#888}input,select{padding:6px}th{position:sticky;top:0;background:#efeee8}</style>
<b>VERITAS INTELLIGENCE ANALYTICS</b><div>DISCIPLINA • PRUDENTIA • INTEGRITAS</div><b>AI-Powered Research &amp; Decision Intelligence Platform</b>
<h1>VRN — REPORT_DATE / FILENAME / FORMAT / SIZE / TICKER / NAME / BROKER</h1>
<p>SIZE = bytes；空白 SIZE 表示未讀實體檔。NAME 由 VDF 官方名冊核對，來源日期另列。檔名與文件衝突列為 REVIEW。</p>
<input id=q placeholder='搜尋檔名／代碼'><select id=s><option value=''>全部</option><option>READ_OK</option><option>REVIEW</option><option>MISSING_FILE</option></select>
<a href='StockReportBasicInfo.csv'>CSV</a> · <a href='StockReportBasicInfo.parquet'>Parquet</a> · <a href='RunSummary.json'>JSON</a>
<div style='overflow:auto'><table><thead><tr>""" + "".join("<th>" + c + "</th>" for c in ["INPUT_ID", *CORE_COLUMNS, "STATUS", "FLAGS", "NAME_SOURCE_DATE"]) + "</tr></thead><tbody>" + "".join(cells) + """</tbody></table></div>
<script>function filter(){for(const r of document.querySelectorAll('tbody tr'))r.hidden=!r.textContent.toLowerCase().includes(q.value.toLowerCase())||(s.value&&r.dataset.status!==s.value)}q.oninput=filter;s.onchange=filter;</script></html>"""
    (out / "VRN_SevenField_Matrix.html").write_text(markup, encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    for flag in ("input_root", "manifest", "output_root", "repo_root", "roster"):
        parser.add_argument("--" + flag.replace("_", "-"), default=PARAMS[flag])
    args = parser.parse_args()
    manifest = Path(args.manifest)
    if not manifest.is_absolute():
        manifest = HERE / manifest
    with manifest.open(encoding="utf-8-sig", newline="") as fh:
        entries = list(csv.DictReader(fh))
    if not entries or len({e["input_id"] for e in entries}) != len(entries):
        raise ValueError("清單無資料或 INPUT_ID 重複。")
    vdf, reader, tool_evidence = load_tools(args.repo_root)
    names, name_evidence = load_official_names(vdf, args.roster)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%fZ")
    out = Path(args.output_root).resolve() / stamp
    out.mkdir(parents=True, exist_ok=False)
    rows, audits = [], []
    with (out / "InputAudit.jsonl").open("a", encoding="utf-8") as journal:
        for i, entry in enumerate(entries, 1):
            core, audit = extract_record(entry, Path(args.input_root), names, reader)
            rows.append(core)
            audits.append(audit)
            journal.write(json.dumps(audit, ensure_ascii=False) + "\n")
            journal.flush()
            if i == 1 or i % 10 == 0 or i == len(entries):
                print(f"[進度] {i}/{len(entries)} ({i * 100 // len(entries)}%) {audit['STATUS']}", flush=True)
    evidence = {"version": PARAMS["version"], "manifest_sha256": sha256(manifest), "tools": tool_evidence, "names": name_evidence}
    summary = write_outputs(rows, audits, out, evidence)
    print(json.dumps({"output": str(out), **{k: summary[k] for k in ("rows", "status", "date_conflicts", "missing")}}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
