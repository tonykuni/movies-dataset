#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""讀取 C:\\測試樣本報告 的券商研報樣本。

檔名一定解析。內文依副檔名讀：PDF / DOCX / TXT / JPG。
缺套件或掃不到文字就誠實 NODATA，不猜。GF / 廣發檔名標 DENY。
不寫正式庫。

用法
  python vrn_sample_reader.py --dir "C:\\測試樣本報告" --out vrn_sample_out
  python vrn_sample_reader.py --selftest
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
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: F401
except ImportError:
    VIA_ACCEL = None
# ===== [VIA:ACCEL-BRIDGE:END] =====

import argparse
import csv
import json
import re
import sys
from pathlib import Path

BROKER_PREFIX = {
    "CTBC": "CTBC", "中信": "CTBC", "中國信託": "CTBC",
    "兆豐": "MEGA", "國泰": "CATHAY", "群益": "CAPITAL",
    "華南": "HUANAN", "台新": "TAISHIN", "統一": "PRESIDENT",
    "凱基": "KGI", "元大": "YUANTA", "富邦": "FUBON",
    "永豐": "SINOPAC", "第一金": "FIRST", "玉山": "ESUN",
    "康和": "CONCORD", "元富": "MASTERLINK",
    "GS": "GS", "MS": "MS", "UBS": "UBS", "JPM": "JPM", "JP": "JPM",
    "CITI": "CITI", "DAIWA": "DAIWA", "MQ": "MACQUARIE",
    "CLST": "CLSA", "CLSA": "CLSA", "HSBC": "HSBC", "NOMURA": "NOMURA",
}
DENY_PREFIX = ("GF", "GFHK", "廣發")
RATING = {
    "NR": "NOT_RATED", "未評等": "NOT_RATED", "NOTE": "NOT_RATED",
    "OW": "BUY", "增加持股": "BUY", "買進": "BUY", "B": "BUY",
    "N": "HOLD", "中立": "HOLD", "持有": "HOLD",
    "賣出": "SELL", "減碼": "SELL",
}
TICKER_RX = re.compile(r"(?<!\d)([1-9]\d{3}|00\d{2,4})(?!\d)")
ROC_RX = re.compile(r"(?<!\d)(1\d{2})(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])(?!\d)")
AD8_RX = re.compile(r"(?<!\d)(20\d{2})(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])(?!\d)")
YYMMDD_RX = re.compile(r"(?<!\d)(2[3-9])(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])(?!\d)")


def roc_to_iso(y, m, d):
    return f"{int(y) + 1911:04d}-{int(m):02d}-{int(d):02d}"


def yy_to_iso(y, m, d):
    return f"{2000 + int(y):04d}-{int(m):02d}-{int(d):02d}"


def find_date(stem: str):
    m = AD8_RX.search(stem)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}", "AD8"
    m = ROC_RX.search(stem)
    if m and not stem[max(0, m.start() - 2):m.start()].endswith("20"):
        return roc_to_iso(*m.groups()), "ROC7"
    m = YYMMDD_RX.search(stem)
    if m:
        return yy_to_iso(*m.groups()), "YYMMDD"
    return None, "NODATA"


def find_broker(stem: str):
    upper = stem.upper()
    if upper.startswith(DENY_PREFIX) or "廣發" in stem:
        return None, "DENY"
    for token, code in sorted(BROKER_PREFIX.items(), key=lambda kv: len(kv[0]), reverse=True):
        if token.isascii():
            if re.search(rf"(?<![A-Z]){token}(?![A-Z])", upper):
                return code, "FILENAME"
        elif token in stem:
            return code, "FILENAME"
    return None, "NODATA"


def find_rating(stem: str):
    m = re.search(r"\((?:[^,]+,\s*)?(NR|OW|N|B)(?:_|，|,|\))", stem, re.I)
    if m:
        return RATING.get(m.group(1).upper(), None)
    for word, code in (("未評等", "NOT_RATED"), ("增加持股", "BUY"), ("買進", "BUY"), ("中立", "HOLD")):
        if word in stem:
            return code
    return None


def find_ticker(stem: str):
    m = re.search(r"\((\d{4})\s*(TT)?", stem, re.I)
    if m:
        return m.group(1), ("BB" if m.group(2) else "LOCAL")
    m = re.search(r"(?<!\d)(\d{4})\s*TT\b", stem, re.I)
    if m:
        return m.group(1), "BB"
    m = re.match(r"(\d{4})(?!\d)", stem)
    if m:
        return m.group(1), "LOCAL"
    m = re.search(r"[-_](\d{4})(?!\d)", stem)
    if m:
        return m.group(1), "LOCAL"
    return None, "NODATA"


def doc_kind(stem: str, ticker: str | None):
    if any(w in stem for w in ("晨會", "早報", "盤勢", "盤後", "市場觀察")):
        return "MORNING"
    if any(w in stem for w in ("總經", "聯準會", "債券", "ETF", "論壇", "專題", "產業", "展望", "趨勢")):
        return "INDUSTRY_MACRO"
    if ticker:
        return "EQUITY"
    return "OTHER"


def parse_filename(name: str) -> dict:
    stem = Path(name).stem
    ticker, ticker_src = find_ticker(stem)
    date, date_src = find_date(stem)
    broker, broker_src = find_broker(stem)
    rating = find_rating(stem)
    upside = None
    um = re.search(r"([+-]?\d+(?:\.\d+)?)_", stem)
    if um and "評等" in stem:
        upside = float(um.group(1))
    return {
        "filename": name,
        "ticker": ticker,
        "ticker_src": ticker_src,
        "yfinance_ticker": f"{ticker}.TW" if ticker else None,
        "bloomberg_ticker": f"{ticker} TT" if ticker else None,
        "report_date": date,
        "date_src": date_src,
        "broker": broker,
        "broker_src": broker_src,
        "rating": rating,
        "upside_pct_filename": upside,
        "doc_kind": doc_kind(stem, ticker),
        "ext": Path(name).suffix.lower(),
    }


def read_text(path: Path, limit: int = 20000) -> tuple[str, str]:
    ext = path.suffix.lower()
    try:
        if ext == ".txt":
            return path.read_text(encoding="utf-8", errors="replace")[:limit], "TXT"
        if ext == ".docx":
            import zipfile
            import xml.etree.ElementTree as ET
            with zipfile.ZipFile(path) as zf:
                xml = zf.read("word/document.xml")
            root = ET.fromstring(xml)
            ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
            text = "\n".join(t.text or "" for t in root.findall(".//w:t", ns))
            return text[:limit], "DOCX"
        if ext == ".pdf":
            try:
                from pypdf import PdfReader
                reader = PdfReader(str(path))
                pages = []
                for i, page in enumerate(reader.pages[:3]):
                    pages.append(page.extract_text() or "")
                return "\n".join(pages)[:limit], "PDF_TEXT"
            except Exception as exc:
                return "", f"PDF_NODATA:{type(exc).__name__}"
        if ext in {".jpg", ".jpeg", ".png"}:
            return "", "IMAGE_NEEDS_OCR"
    except Exception as exc:
        return "", f"READ_FAIL:{type(exc).__name__}"
    return "", "UNSUPPORTED"


def scan(folder: Path) -> list[dict]:
    rows = []
    for path in sorted(folder.iterdir()):
        if not path.is_file():
            continue
        rec = parse_filename(path.name)
        text, how = read_text(path)
        rec["read_status"] = how
        rec["text_chars"] = len(text)
        rec["text_head"] = text[:400]
        rows.append(rec)
    return rows


def write_out(rows: list[dict], out: Path):
    out.mkdir(parents=True, exist_ok=True)
    (out / "sample_index.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    with (out / "sample_index.csv").open("w", encoding="utf-8-sig", newline="") as fh:
        fields = ["filename", "doc_kind", "ticker", "broker", "broker_src", "rating", "report_date", "date_src", "read_status", "text_chars"]
        writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    return {"files": len(rows), "with_ticker": sum(bool(r["ticker"]) for r in rows), "deny": sum(r["broker_src"] == "DENY" for r in rows)}


def selftest():
    names = [
        "華南投顧-6143-振曜-1141128.pdf",
        "瑞基(4171,NR_未評等)-CTBC251208.pdf",
        "【國泰證期研究部】神達(3706 TT)-初次評等買進(+30.4_)-大顯神威，營運騰達-20250822.pdf",
        "3014TT-20231005.pdf",
        "GS-1590 20231012.pdf",
        "GFHK - Apple update 20260915.pdf",
        "20250819兆豐個股報告-泓德能源(6873).pdf",
        "啟碁(6285,OW_增加持股)-CTBC260915.pdf",
        "凱基投顧_1476 儒鴻_劉昃恩_20260519.pdf",
        "926708.jpg",
    ]
    rows = [parse_filename(n) for n in names]
    checks = [
        rows[0]["ticker"] == "6143" and rows[0]["broker"] == "HUANAN" and rows[0]["report_date"] == "2025-11-28",
        rows[1]["ticker"] == "4171" and rows[1]["rating"] == "NOT_RATED" and rows[1]["broker"] == "CTBC",
        rows[2]["ticker"] == "3706" and rows[2]["broker"] == "CATHAY" and rows[2]["rating"] == "BUY" and rows[2]["upside_pct_filename"] == 30.4,
        rows[3]["ticker"] == "3014" and rows[3]["report_date"] == "2023-10-05",
        rows[4]["broker"] == "GS" and rows[4]["ticker"] == "1590",
        rows[5]["broker_src"] == "DENY",
        rows[6]["broker"] == "MEGA" and rows[6]["ticker"] == "6873",
        rows[7]["rating"] == "BUY" and rows[7]["report_date"] == "2026-09-15",
        rows[8]["ticker"] == "1476" and rows[8]["broker"] == "KGI",
        rows[9]["ticker"] is None and rows[9]["ext"] == ".jpg",
    ]
    print(json.dumps({"ok": all(checks), "failed": [i for i, ok in enumerate(checks) if not ok], "sample": rows[0]}, ensure_ascii=False, indent=2))
    return 0 if all(checks) else 1


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", default=r"C:\測試樣本報告")
    parser.add_argument("--out", default="vrn_sample_out")
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args(argv)
    if args.selftest:
        return selftest()
    folder = Path(args.dir)
    if not folder.is_dir():
        print(json.dumps({"ok": False, "error": "DIR_NOT_FOUND", "dir": str(folder)}, ensure_ascii=False))
        return 2
    stats = write_out(scan(folder), Path(args.out))
    print(json.dumps({"ok": True, **stats, "out": args.out}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
