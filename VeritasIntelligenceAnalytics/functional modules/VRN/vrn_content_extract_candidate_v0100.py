# =====================================================================================
# VRN Content Extract CANDIDATE v0100 — 內容級擷取候選引擎(DRY-RUN 專用)
# 狀態: CANDIDATE · 範疇凍結未解 — 本引擎只允許 dry-run:
#   輸出 run-local CSV/JSON(VIA_Reports,不入庫),永不寫 SSOT/parquet/DuckDB。
#   --commit 一律拒絕,直到 audit_tools 存在 VRN_ContentExtract_ACTIVATION_RECORD_*.json
#   (由操作員在 via-probe 裁決 GO 後點名開啟的 hash-locked 交易產生)。
# 地基: FNC-001 InvestmentPatternMatcher.extract_value(141 欄位/525 樣式,含數值/單位/信心)
#       ENG-004 同義字引擎(canonical 錨點)
#       輸出列對齊 VRN_REPORT_FINANCIAL_DATA_SSOT_v0100 核心欄(可對齊者填,缺者 null+原因)
# 用法: py vrn_content_extract_candidate_v0100.py [PDF資料夾] [--limit N]
# =====================================================================================
import os, sys, csv, json, glob, hashlib, datetime as dt

HERE = os.path.dirname(os.path.abspath(__file__))
VIA = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)

ACTIVATION_GLOB = os.path.join(VIA, "supportive modules", "audit_tools", "VRN_ContentExtract_ACTIVATION_RECORD_*.json")

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
    if "--commit" in argv:
        if not glob.glob(ACTIVATION_GLOB):
            print("[拒絕] --commit 需要啟用記錄(via-probe GO 裁決後由操作員點名開啟 hash-locked 交易)。")
            print("[拒絕] 目前僅允許 dry-run。範疇凍結維持。")
            return 2
    target = next((a for a in argv if not a.startswith("--") and not a.isdigit()), None)
    limit = int(argv[argv.index("--limit") + 1]) if "--limit" in argv else 20
    cands = [target] if target else [os.path.join(HERE, "input", "incoming"), os.path.join(HERE, "input", "processed")]
    pdf_dir = next((c for c in cands if c and os.path.isdir(c) and any(f.lower().endswith(".pdf") for f in os.listdir(c))), None)

    print("=" * 62)
    print("  VRN Content Extract CANDIDATE v0100  |  DRY-RUN(不寫 SSOT)")
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
                "report_id": "DRYRUN_%s" % sha12, "ticker": "", "company_name": "",
                "report_date": "", "statement_type": stmt,
                "account_raw": ev.source_text[:120], "account_canonical": key,
                "period_label": "DRYRUN_UNPARSED", "fiscal_year": "", "fiscal_quarter": "",
                "period_type": "", "value_raw": ev.source_text[:120],
                "value_numeric": ev.value, "unit": ev.unit, "currency": "", "scale": "",
                "source_table_id": "TEXT_PROBE:%s" % f,
                "record_hash": hashlib.sha256(("%s|%s|%s|%s" % (sha12, key, ev.value, f)).encode()).hexdigest()[:16],
                "null_reason": "ticker/date/period 屬 BasicInfo 管線職責,dry-run 不併跑",
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
    print("[結果] %d 檔 → %d 列候選財務資料(平均 %.1f 列/檔)" % (len(pdfs), len(rows), summary["avg_rows_per_pdf"]))
    print("[輸出] %s (run-local,不入庫)" % out_csv)
    print("[閘門] 寫入 SSOT 需 ACTIVATION_RECORD — via-probe GO 後由操作員點名開啟。")

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]) or 0)
