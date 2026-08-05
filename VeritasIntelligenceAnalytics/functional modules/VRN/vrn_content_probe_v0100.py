# =====================================================================================
# VRN Content Probe v0100 — 內容級擷取 Stage-0 可行性探測(唯讀,不寫任何 SSOT/DB)
# 目的: 在重開「VRN 內容級擷取」凍結範疇之前,以真實 PDF 語料量測兩塊 ACTIVE 地基的覆蓋率:
#   FNC-001 InvestmentRegexPattern_VALIDATED (525 patterns) — 欄位命中統計(分六大報表域)
#   ENG-004 via_synonym_engine — canonical 錨點解析健檢
# 治理: 唯讀提案型(公定處理模式 R1);輸出 run-local 報告(VIA_Reports,不入庫);
#       PDF 文字抽取 detect-only(pypdf → pdfminer 後備;皆缺則誠實 MISS,不安裝不聯網)
# 用法: py vrn_content_probe_v0100.py [PDF資料夾] [--limit N] [--no-open]
#       預設資料夾 = input/incoming;空則自動改試 input/processed
# =====================================================================================
import os, sys, json, datetime as dt

HERE = os.path.dirname(os.path.abspath(__file__))
VIA = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(VIA, "supportive modules", "ssot"))

def extract_text(path, max_pages=6):
    try:
        from pypdf import PdfReader
        r = PdfReader(path)
        return "\n".join((p.extract_text() or "") for p in r.pages[:max_pages]), "pypdf"
    except Exception:
        pass
    try:
        from PyPDF2 import PdfReader
        r = PdfReader(path)
        return "\n".join((p.extract_text() or "") for p in r.pages[:max_pages]), "PyPDF2"
    except Exception:
        pass
    try:
        from pdfminer.high_level import extract_text as pm
        return pm(path, maxpages=max_pages), "pdfminer"
    except Exception:
        return None, None

def main(argv):
    target = None
    limit = 20
    for a in argv:
        if a == "--no-open":
            continue
        elif a.startswith("--limit"):
            pass
        elif a.isdigit():
            limit = int(a)
        elif target is None:
            target = a
    if "--limit" in argv:
        limit = int(argv[argv.index("--limit") + 1])
    cands = [target] if target else [os.path.join(HERE, "input", "incoming"), os.path.join(HERE, "input", "processed")]
    pdf_dir = next((c for c in cands if c and os.path.isdir(c) and any(f.lower().endswith(".pdf") for f in os.listdir(c))), None)

    print("=" * 62)
    print("  VRN Content Probe v0100  |  內容級擷取 Stage-0 可行性探測(唯讀)")
    print("=" * 62)

    from InvestmentRegexPattern_VALIDATED import ALL_PATTERNS
    from via_synonym_engine_v0100 import build as build_syn
    syn = build_syn()
    print("[地基] FNC-001 patterns=%d 域 · ENG-004 canonicals=%d" % (len(ALL_PATTERNS), len(syn.canonical)))

    if not pdf_dir:
        print("[語料] MISS — %s 皆無 PDF;把研報 PDF 放進 input/incoming 再跑一次" % " / ".join(os.path.relpath(c, VIA) for c in cands))
        return
    pdfs = sorted(f for f in os.listdir(pdf_dir) if f.lower().endswith(".pdf"))[:limit]
    print("[語料] %s · 取樣 %d 檔(上限 --limit)" % (os.path.relpath(pdf_dir, VIA), len(pdfs)))

    per_pdf, domain_tally, extractor_used = [], {}, None
    miss_extract = 0
    for i, f in enumerate(pdfs):
        text, ex = extract_text(os.path.join(pdf_dir, f))
        sys.stdout.write("\r[%-20s] %3d%%  探測 %s" % ("#" * int((i + 1) / len(pdfs) * 20), int((i + 1) / len(pdfs) * 100), f[:40]))
        sys.stdout.flush()
        if not text or len(text.strip()) < 40:
            miss_extract += 1
            per_pdf.append({"pdf": f, "status": "NO_TEXT(掃描版或抽取器缺席)", "hits": 0})
            continue
        extractor_used = extractor_used or ex
        hits = {}
        for key, pd in ALL_PATTERNS.items():
            if pd.match(text):
                dom = pd.statement.value if hasattr(pd.statement, "value") else str(pd.statement)
                hits[key] = dom
                domain_tally[dom] = domain_tally.get(dom, 0) + 1
        per_pdf.append({"pdf": f, "status": "OK", "hits": len(hits), "chars": len(text)})
    print()
    ok_pdfs = [p for p in per_pdf if p["status"] == "OK"]
    avg = (sum(p["hits"] for p in ok_pdfs) / len(ok_pdfs)) if ok_pdfs else 0
    verdict = ("GO — 平均每檔命中 %.0f 個欄位 pattern,足以支撐內容級擷取重開" % avg) if avg >= 15 else \
              ("PARTIAL — 平均命中 %.0f,建議先擴充 pattern 或檢查 PDF 品質" % avg) if ok_pdfs else \
              "NO_TEXT — 全數無文字層(需 OCR 路線)或抽取器缺席(pip install pypdf)"
    rep = {"probe": "vrn_content_probe_v0100", "ts": dt.datetime.now().isoformat(timespec="seconds"),
           "corpus_dir": os.path.relpath(pdf_dir, VIA), "sampled": len(pdfs), "text_ok": len(ok_pdfs),
           "no_text": miss_extract, "extractor": extractor_used or "NONE",
           "avg_pattern_hits_per_pdf": round(avg, 1), "domain_tally": domain_tally,
           "synonym_canonicals": len(syn.canonical), "verdict": verdict, "per_pdf": per_pdf,
           "read_only": True}
    out_dir = os.path.join(VIA, "VIA_Reports")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "VRN_ContentProbe_Report.json")
    json.dump(rep, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("[域統計] " + " · ".join("%s:%d" % kv for kv in sorted(domain_tally.items())) if domain_tally else "[域統計] 無命中")
    print("[裁決] " + verdict)
    print("[報告] " + out + " (run-local,不入庫)")

if __name__ == "__main__":
    main(sys.argv[1:])
