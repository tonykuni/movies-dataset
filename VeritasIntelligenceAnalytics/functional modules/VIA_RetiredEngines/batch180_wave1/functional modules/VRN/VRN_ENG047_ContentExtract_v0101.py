# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(全引擎導入令 2026-08-18;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # accel_map/fetch/pip_install/run_fast
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====
# =====================================================================================
# VRN Content Extract v0101 — 內容級擷取引擎(ACTIVE,啟用交易後版本)
# 狀態: ACTIVE — 操作員 2026-08-05 點名啟用(probe GO:平均 21 命中/檔;dry-run 260 列)。
# v0101 相對 candidate v0100:
#   (a) BasicInfo 輕量補齊:ticker(TickerRegexSSOT v0100 樣式)、report_date(檔名日期)、
#       broker(VRN_BROKER_LIST_v01 二十家,CJK 無邊界/ASCII 字母邊界,長別名優先)
#   (b) --commit 落地:append-only 寫入 output/FINANCIAL_DATA_STORE.csv,record_hash 去重,
#       永不覆寫既有列(只增不減);store 屬產出物不入 git
# 原 dry-run 行為完整保留(預設仍 dry-run):
#   輸出 run-local CSV/JSON(VIA_Reports,不入庫),永不寫 SSOT/parquet/DuckDB。
#   --commit 一律拒絕,直到 audit_tools 存在 VRN_ContentExtract_ACTIVATION_RECORD_*.json
#   (由操作員在 via-probe 裁決 GO 後點名開啟的 hash-locked 交易產生)。
# 地基: FNC-001 InvestmentPatternMatcher.extract_value(141 欄位/525 樣式,含數值/單位/信心)
#       ENG-004 同義字引擎(canonical 錨點)
#       輸出列對齊 VRN_REPORT_FINANCIAL_DATA_SSOT_v0100 核心欄(可對齊者填,缺者 null+原因)
# 用法: py VRN_ENG046_ContentExtractCandidate_v0100.py [PDF資料夾] [--limit N]
# =====================================================================================
import os, re, sys, csv, json, glob, hashlib, datetime as dt

HERE = os.path.dirname(os.path.abspath(__file__))
VIA = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)

ACTIVATION_GLOB = os.path.join(VIA, "supportive modules", "audit_tools", "VRN_ContentExtract_ACTIVATION_RECORD_*.json")
STORE = os.path.join(HERE, "output", "FINANCIAL_DATA_STORE.csv")
_TICKER_RE = re.compile(r"(?<!\d)([1-9]\d{3})(?!\d)")
_DATE_RES = [re.compile(r"(20\d{2})[-_.]?(0[1-9]|1[0-2])[-_.]?(0[1-9]|[12]\d|3[01])")]

def _load_brokers():
    p = os.path.join(HERE, "registry", "VRN_BROKER_LIST_v01.json")
    out = []
    try:
        d = json.load(open(p, encoding="utf-8-sig"))
        for b in d.get("brokers", []):
            for a in sorted(set(b.get("aliases", [])), key=len, reverse=True):
                out.append((a, b.get("canonical", "")))
        out.sort(key=lambda x: -len(x[0]))
    except Exception:
        pass
    return out

_BROKERS = _load_brokers()

def parse_meta(fname):
    """檔名 → (ticker, report_date, broker);找不到者留空(誠實 null)。"""
    stem = os.path.splitext(fname)[0]
    date = ""
    for rx in _DATE_RES:
        m = rx.search(stem)
        if m:
            date = "%s/%s/%s" % m.groups()
            stem_nodate = stem.replace(m.group(0), " ")
            break
    else:
        stem_nodate = stem
    ticker = ""
    m = _TICKER_RE.search(stem_nodate)
    if m:
        ticker = m.group(1)
    broker = ""
    for alias, canon in _BROKERS:
        if re.search(r"[\u3400-\u9fff]", alias):
            if alias in stem:
                broker = canon; break
        else:
            if re.search(r"(?<![A-Za-z])%s(?![A-Za-z])" % re.escape(alias), stem):
                broker = canon; break
    return ticker, date, broker

def extract_text(path, max_pages=8):
    try:
        from pypdf import PdfReader
        return "\n".join((p.extract_text() or "") for p in PdfReader(path).pages[:max_pages])
    except Exception:
        pass
    try:
        from PyPDF2 import PdfReader
        return "\n".join((p.extract_text() or "") for p in PdfReader(path).pages[:max_pages])
    except Exception:
        pass
    try:
        from pdfminer.high_level import extract_text as pm
        return pm(path, maxpages=max_pages)
    except Exception:
        return None

def main(argv):
    commit = "--commit" in argv
    if commit and not glob.glob(ACTIVATION_GLOB):
        print("[拒絕] --commit 需要啟用記錄。目前僅允許 dry-run。")
        return 2
    target = next((a for a in argv if not a.startswith("--") and not a.isdigit()), None)
    limit = int(argv[argv.index("--limit") + 1]) if "--limit" in argv else 20
    cands = [target] if target else [os.path.join(HERE, "input", "incoming"), os.path.join(HERE, "input", "processed")]
    pdf_dir = next((c for c in cands if c and os.path.isdir(c) and any(f.lower().endswith(".pdf") for f in os.listdir(c))), None)

    print("=" * 62)
    print("  VRN Content Extract v0101 ACTIVE  |  %s" % ("COMMIT 落地" if commit else "DRY-RUN"))
    print("=" * 62)
    from InvestmentRegexPattern_VALIDATED import InvestmentPatternMatcher, ALL_PATTERNS
    matcher = InvestmentPatternMatcher()
    if not pdf_dir:
        print("[語料] MISS — input/incoming 與 input/processed 皆無 PDF。")
        return 1
    pdfs = sorted(f for f in os.listdir(pdf_dir) if f.lower().endswith(".pdf"))[:limit]
    print("[語料] %s · %d 檔 · 欄位定義 %d" % (os.path.relpath(pdf_dir, VIA), len(pdfs), len(ALL_PATTERNS)))

    rows, per_pdf = [], []
    now = dt.datetime.now().strftime("%Y/%m/%d")
    for i, f in enumerate(pdfs):
        p = os.path.join(pdf_dir, f)
        sha12 = hashlib.sha256(open(p, "rb").read()).hexdigest()[:12]
        mt_ticker, mt_date, mt_broker = parse_meta(f)
        text = extract_text(p)
        sys.stdout.write("\r[%-20s] %3d%%  %s" % ("#" * int((i + 1) / len(pdfs) * 20), int((i + 1) / len(pdfs) * 100), f[:44]))
        sys.stdout.flush()
        if not text or len(text.strip()) < 40:
            per_pdf.append({"pdf": f, "rows": 0, "note": "NO_TEXT"})
            continue
        n0 = len(rows)
        for key in ALL_PATTERNS:
            ev = matcher.extract_value(text, key)
            if ev is None:
                continue
            stmt = ev.statement.value if hasattr(ev.statement, "value") else str(ev.statement)
            rows.append({
                "report_id": ("RPT_%s" if commit else "DRYRUN_%s") % sha12,
                "ticker": mt_ticker, "company_name": "", "report_date": mt_date,
                "broker": mt_broker, "statement_type": stmt,
                "account_raw": ev.source_text[:120], "account_canonical": key,
                "period_label": "DRYRUN_UNPARSED", "fiscal_year": "", "fiscal_quarter": "",
                "period_type": "", "value_raw": ev.source_text[:120],
                "value_numeric": ev.value, "unit": ev.unit, "currency": "", "scale": "",
                "source_table_id": "TEXT_PROBE:%s" % f,
                "record_hash": hashlib.sha256(("%s|%s|%s|%s" % (sha12, key, ev.value, f)).encode()).hexdigest()[:16],
                "null_reason": "company_name 需 ticker registry;period 屬表格欄位解析,本版未併跑",
                "confidence": ev.confidence,
            })
        per_pdf.append({"pdf": f, "rows": len(rows) - n0, "note": "OK"})
    print()
    out_dir = os.path.join(VIA, "VIA_Reports")
    os.makedirs(out_dir, exist_ok=True)
    out_csv = os.path.join(out_dir, "VRN_ContentExtract_DRYRUN.csv")
    if rows:
        w = csv.DictWriter(open(out_csv, "w", newline="", encoding="utf-8-sig"), fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    summary = {"candidate": "vrn_content_extract_candidate_v0100", "ts": dt.datetime.now().isoformat(timespec="seconds"),
               "mode": "DRY_RUN", "pdfs": len(pdfs), "rows_extracted": len(rows),
               "avg_rows_per_pdf": round(len(rows) / max(1, len([x for x in per_pdf if x["note"] == "OK"])), 1),
               "per_pdf": per_pdf, "generated": now, "writes_to_ssot": False}
    json.dump(summary, open(os.path.join(out_dir, "VRN_ContentExtract_DRYRUN_summary.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("[結果] %d 檔 → %d 列財務資料(平均 %.1f 列/檔)" % (len(pdfs), len(rows), summary["avg_rows_per_pdf"]))
    print("[輸出] %s (run-local)" % out_csv)
    if commit and rows:
        os.makedirs(os.path.dirname(STORE), exist_ok=True)
        existing = set()
        if os.path.exists(STORE):
            with open(STORE, encoding="utf-8-sig") as fh:
                for r0 in csv.DictReader(fh):
                    existing.add(r0.get("record_hash", ""))
        fresh = [r for r in rows if r["record_hash"] not in existing]
        write_header = not os.path.exists(STORE)
        with open(STORE, "a", newline="", encoding="utf-8-sig") as fh:
            w2 = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            if write_header:
                w2.writeheader()
            w2.writerows(fresh)
        print("[COMMIT] append-only 入庫 %d 列(去重跳過 %d)→ %s" % (len(fresh), len(rows) - len(fresh), STORE))
    elif not commit:
        print("[閘門] --commit 落地至 FINANCIAL_DATA_STORE(append-only,record_hash 去重)。")

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]) or 0)
