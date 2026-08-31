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
import csv, json, os, re, sys, time, hashlib
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

input_paths = sys.argv[1]
json_out = sys.argv[2]
csv_out = sys.argv[3]
qualified_txt = sys.argv[4]
heartbeat_out = sys.argv[5]
max_pages = int(sys.argv[6])
max_workers = int(sys.argv[7])
heartbeat_every = int(sys.argv[8])

try:
    import fitz
    HAS_FITZ = True
except Exception:
    HAS_FITZ = False

ticker_re = re.compile(r"(?<!\d)([1-9]\d{3})(?:\s?TT|\.TW|\.TWO)?(?!\d)", re.I)
date_res = [
    re.compile(r"(20\d{2})[-_./]?(0[1-9]|1[0-2])[-_./]?([0-2]\d|3[01])"),
    re.compile(r"(1[0-2]\d)[-_./]?(0[1-9]|1[0-2])[-_./]?([0-2]\d|3[01])")
]

broker_patterns = [
    "Citi","Citigroup","Goldman","Goldman Sachs","GS","Daiwa","Morgan Stanley","MS","CLSA",
    "Nomura","UBS","JPM","JP Morgan","Jefferies","Macquarie","HSBC",
    "元大","凱基","國泰","富邦","兆豐","永豐","群益","玉山","統一","中信","第一金","華南","台新"
]

keywords = [
    "buy","sell","hold","neutral","outperform","underperform","target price","rating",
    "eps","revenue","earnings","valuation","upgrade","downgrade","initiation",
    "買進","賣出","持有","中立","優於大盤","劣於大盤","目標價","評等","初評","調升","調降",
    "營收","獲利","每股盈餘","財測","投資評等","研究報告","個股報告"
]

def now():
    return datetime.now().isoformat()

def sha12(path):
    try:
        h=hashlib.sha1()
        with open(path,"rb") as f:
            h.update(f.read(1024*1024))
        return h.hexdigest()[:12]
    except Exception:
        return ""

def find_ticker(text):
    m = ticker_re.search(text or "")
    return m.group(1) if m else ""

def find_date(text):
    text = text or ""
    for r in date_res:
        m = r.search(text)
        if m:
            y = int(m.group(1))
            if y < 1911:
                y += 1911
            return f"{y}-{m.group(2)}-{m.group(3)}"
    return ""

def find_broker(text):
    low = (text or "").lower()
    for b in broker_patterns:
        if b.lower() in low:
            return b
    return ""

def keyword_hits(text):
    low = (text or "").lower()
    return [k for k in keywords if k.lower() in low]

def extract_text_fast(path):
    if not HAS_FITZ:
        return 0, "", 0, "NO_FITZ"
    try:
        doc = fitz.open(path)
        pages = doc.page_count
        lim = min(pages, max_pages)
        parts = []
        for i in range(lim):
            try:
                parts.append(doc.load_page(i).get_text("text") or "")
            except Exception:
                pass
        doc.close()
        first_text = parts[0][:12000] if parts else ""
        text_chars = sum(len(x) for x in parts)
        return pages, first_text, text_chars, ""
    except Exception as e:
        return 0, "", 0, str(e)

def eval_pdf(path):
    t0=time.perf_counter()
    name=os.path.basename(path)
    base=os.path.splitext(name)[0]
    pages, first_text, text_chars, err = extract_text_fast(path)
    combined = base + "\n" + first_text[:12000]

    ticker = find_ticker(combined)
    report_date = find_date(combined)
    broker = find_broker(combined)
    hits = keyword_hits(combined)

    score=0
    if ticker: score += 35
    if report_date: score += 25
    if broker: score += 15
    if len(hits)>=2: score += 20
    elif len(hits)==1: score += 10
    if text_chars > 500: score += 5

    qualified = (score >= 55 and not err)
    status = "QUALIFIED_FAST" if qualified else "REVIEW_REQUIRED_FAST"
    risk = "LOW" if qualified else "MEDIUM"

    if err:
        status = "FAIL_READ_PDF"
        risk = "HIGH"

    reason=[]
    if not ticker: reason.append("ticker_missing")
    if not report_date: reason.append("date_missing")
    if not broker: reason.append("broker_missing")
    if len(hits)==0: reason.append("keyword_missing")
    if err: reason.append(err)

    return {
        "file_id": sha12(path),
        "qualified": qualified,
        "status": status,
        "risk": risk,
        "score": score,
        "elapsed_sec": round(time.perf_counter()-t0,4),
        "pages": pages,
        "text_chars": text_chars,
        "ticker": ticker,
        "report_date": report_date,
        "broker": broker,
        "keyword_hits": ";".join(hits[:12]),
        "reason": "; ".join(reason),
        "file_name": name,
        "path": path
    }

def write_heartbeat(done,total,qualified,failed,start,last_path=""):
    elapsed=round(time.perf_counter()-start,3)
    avg=round(elapsed/done,4) if done else 0
    pdf_per_min=round(60/avg,2) if avg else 0
    payload={
        "generated_at":now(),
        "done":done,
        "total":total,
        "qualified":qualified,
        "failed":failed,
        "elapsed_sec":elapsed,
        "avg_sec_per_pdf":avg,
        "pdf_per_min":pdf_per_min,
        "last_path":last_path
    }
    with open(heartbeat_out,"w",encoding="utf-8") as f:
        json.dump(payload,f,ensure_ascii=False,indent=2)

with open(input_paths,"r",encoding="utf-8-sig") as f:
    paths=[x.strip() for x in f.read().splitlines() if x.strip() and os.path.exists(x.strip())]

rows=[]
start=time.perf_counter()
done=0
qualified_count=0
failed_count=0

write_heartbeat(0,len(paths),0,0,start,"")

if not HAS_FITZ:
    rows=[{
        "file_id":"",
        "qualified":False,
        "status":"FAIL_NO_FITZ",
        "risk":"HIGH",
        "score":0,
        "elapsed_sec":0,
        "pages":0,
        "text_chars":0,
        "ticker":"",
        "report_date":"",
        "broker":"",
        "keyword_hits":"",
        "reason":"PyMuPDF not available",
        "file_name":os.path.basename(p),
        "path":p
    } for p in paths]
else:
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futs={ex.submit(eval_pdf,p):p for p in paths}
        for fut in as_completed(futs):
            p=futs[fut]
            try:
                r=fut.result()
            except Exception as e:
                r={
                    "file_id":"",
                    "qualified":False,
                    "status":"FAIL_EXCEPTION",
                    "risk":"HIGH",
                    "score":0,
                    "elapsed_sec":0,
                    "pages":0,
                    "text_chars":0,
                    "ticker":"",
                    "report_date":"",
                    "broker":"",
                    "keyword_hits":"",
                    "reason":str(e),
                    "file_name":os.path.basename(p),
                    "path":p
                }
            rows.append(r)
            done += 1
            if r.get("qualified"):
                qualified_count += 1
            if str(r.get("status","")).startswith("FAIL"):
                failed_count += 1
            if done % heartbeat_every == 0 or done == len(paths):
                write_heartbeat(done,len(paths),qualified_count,failed_count,start,p)
                print(json.dumps({"done":done,"total":len(paths),"qualified":qualified_count,"failed":failed_count},ensure_ascii=False), flush=True)

elapsed=round(time.perf_counter()-start,4)
qualified=[r for r in rows if r["qualified"]]
failed=[r for r in rows if str(r["status"]).startswith("FAIL")]
avg=round(elapsed/len(rows),4) if rows else 0
pdf_per_min=round(60/avg,2) if avg>0 else 0

summary={
    "generated_at":now(),
    "input_candidates":len(paths),
    "refined_qualified":len(qualified),
    "failed":len(failed),
    "elapsed_sec":elapsed,
    "avg_sec_per_pdf":avg,
    "pdf_per_min":pdf_per_min,
    "has_fitz":HAS_FITZ,
    "max_pages":max_pages,
    "max_workers":max_workers,
    "rows":rows
}

with open(json_out,"w",encoding="utf-8") as f:
    json.dump(summary,f,ensure_ascii=False,indent=2)

fieldnames=[
    "file_id","qualified","status","risk","score","elapsed_sec","pages","text_chars",
    "ticker","report_date","broker","keyword_hits","reason","file_name","path"
]

with open(csv_out,"w",encoding="utf-8-sig",newline="") as f:
    w=csv.DictWriter(f,fieldnames=fieldnames)
    w.writeheader()
    for r in rows:
        w.writerow({k:r.get(k,"") for k in fieldnames})

with open(qualified_txt,"w",encoding="utf-8") as f:
    for r in qualified:
        f.write(r["path"]+"\n")

write_heartbeat(len(paths),len(paths),len(qualified),len(failed),start,"COMPLETE")

print(json.dumps({
    "input_candidates":len(paths),
    "refined_qualified":len(qualified),
    "failed":len(failed),
    "elapsed_sec":elapsed,
    "avg_sec_per_pdf":avg,
    "pdf_per_min":pdf_per_min,
    "has_fitz":HAS_FITZ,
    "max_workers":max_workers
},ensure_ascii=False))