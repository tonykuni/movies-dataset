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
basic_csv = sys.argv[3]
text_csv = sys.argv[4]
file_csv = sys.argv[5]
exception_csv = sys.argv[6]
heartbeat_out = sys.argv[7]
max_pages = int(sys.argv[8])
max_workers = int(sys.argv[9])
heartbeat_every = int(sys.argv[10])

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
rating_patterns = [
    "Buy","Hold","Sell","Neutral","Outperform","Underperform","Overweight","Equal-weight","Underweight",
    "買進","持有","賣出","中立","優於大盤","劣於大盤","增加持股","降低持股"
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

def find_rating(text):
    low = (text or "").lower()
    for r in rating_patterns:
        if r.lower() in low:
            return r
    return ""

def make_report_id(file_id, ticker, report_date):
    raw = "|".join([file_id or "", ticker or "", report_date or ""])
    return hashlib.sha1(raw.encode("utf-8","ignore")).hexdigest()[:16]

def heartbeat(done,total,extracted,failed,text_rows,start,last_path=""):
    elapsed=round(time.perf_counter()-start,3)
    avg=round(elapsed/done,4) if done else 0
    ppm=round(60/avg,2) if avg else 0
    payload={
        "generated_at":now(),
        "done":done,
        "total":total,
        "extracted":extracted,
        "failed":failed,
        "text_rows":text_rows,
        "elapsed_sec":elapsed,
        "avg_sec_per_pdf":avg,
        "pdf_per_min":ppm,
        "last_path":last_path
    }
    with open(heartbeat_out,"w",encoding="utf-8") as f:
        json.dump(payload,f,ensure_ascii=False,indent=2)

def extract_pdf(path):
    t0=time.perf_counter()
    file_id = sha12(path)
    name = os.path.basename(path)
    basic = None
    file_row = None
    text_rows = []
    exceptions = []

    if not HAS_FITZ:
        exceptions.append({
            "file_id":file_id,"report_id":"","issue_type":"ENGINE_MISSING","severity":"HIGH",
            "message":"PyMuPDF not available","path":path
        })
        return None, None, [], exceptions, 0, "FAIL_NO_FITZ"

    try:
        doc = fitz.open(path)
        page_count = doc.page_count
        lim = min(page_count, max_pages)
        first_text = ""
        total_chars = 0

        for i in range(lim):
            try:
                page = doc.load_page(i)
                txt = page.get_text("text") or ""
                if i == 0:
                    first_text = txt[:15000]
                total_chars += len(txt)

                if txt.strip():
                    text_rows.append({
                        "file_id":file_id,
                        "page":i+1,
                        "section":"page_text",
                        "text":txt[:50000],
                        "text_chars":len(txt),
                        "source_engine":"pymupdf",
                        "confidence":0.90,
                        "path":path
                    })
            except Exception as e:
                exceptions.append({
                    "file_id":file_id,"report_id":"","issue_type":"PAGE_TEXT_FAIL","severity":"MEDIUM",
                    "message":str(e),"path":path
                })

        doc.close()

        combo = name + "\n" + first_text
        ticker = find_ticker(combo)
        report_date = find_date(combo)
        broker = find_broker(combo)
        rating = find_rating(combo)
        report_id = make_report_id(file_id,ticker,report_date)

        review_required = False
        identity_score = 0
        if ticker: identity_score += 35
        if report_date: identity_score += 30
        if broker: identity_score += 20
        if rating: identity_score += 5
        if total_chars > 500: identity_score += 10

        if not ticker:
            review_required = True
            exceptions.append({"file_id":file_id,"report_id":report_id,"issue_type":"TICKER_MISSING","severity":"MEDIUM","message":"Ticker not found","path":path})
        if not report_date:
            review_required = True
            exceptions.append({"file_id":file_id,"report_id":report_id,"issue_type":"DATE_MISSING","severity":"MEDIUM","message":"Report date not found","path":path})
        if not broker:
            exceptions.append({"file_id":file_id,"report_id":report_id,"issue_type":"BROKER_MISSING","severity":"LOW","message":"Broker not found","path":path})

        basic = {
            "report_id":report_id,
            "file_id":file_id,
            "report_date":report_date,
            "ticker":ticker,
            "company_name":"",
            "broker":broker,
            "analyst":"",
            "rating":rating,
            "target_price":"",
            "currency":"",
            "identity_score":identity_score,
            "source_confidence":round(identity_score/100,3),
            "review_required":review_required,
            "file_name":name,
            "path":path
        }

        file_row = {
            "file_id":file_id,
            "file_name":name,
            "file_path":path,
            "file_size":os.path.getsize(path),
            "page_count":page_count,
            "pages_extracted":lim,
            "text_chars":total_chars,
            "has_text_layer":total_chars > 0,
            "ocr_required":total_chars < 300,
            "elapsed_sec":round(time.perf_counter()-t0,4),
            "status":"OK_EXTRACTED"
        }

        for tr in text_rows:
            tr["report_id"] = report_id
            tr["ticker"] = ticker
            tr["report_date"] = report_date
            tr["broker"] = broker

        for ex in exceptions:
            ex["report_id"] = ex.get("report_id") or report_id

        return basic, file_row, text_rows, exceptions, round(time.perf_counter()-t0,4), "OK_EXTRACTED"

    except Exception as e:
        exceptions.append({
            "file_id":file_id,
            "report_id":"",
            "issue_type":"PDF_READ_FAIL",
            "severity":"HIGH",
            "message":str(e),
            "path":path
        })
        return None, {
            "file_id":file_id,
            "file_name":name,
            "file_path":path,
            "file_size":os.path.getsize(path) if os.path.exists(path) else 0,
            "page_count":0,
            "pages_extracted":0,
            "text_chars":0,
            "has_text_layer":False,
            "ocr_required":True,
            "elapsed_sec":round(time.perf_counter()-t0,4),
            "status":"FAIL_READ_PDF"
        }, [], exceptions, round(time.perf_counter()-t0,4), "FAIL_READ_PDF"

with open(input_paths,"r",encoding="utf-8-sig") as f:
    paths=[x.strip() for x in f.read().splitlines() if x.strip() and os.path.exists(x.strip())]

start=time.perf_counter()
basic_rows=[]
file_rows=[]
text_rows_all=[]
exception_rows=[]
done=0
extracted=0
failed=0

heartbeat(0,len(paths),0,0,0,start,"")

with ThreadPoolExecutor(max_workers=max_workers) as ex:
    futs={ex.submit(extract_pdf,p):p for p in paths}
    for fut in as_completed(futs):
        p=futs[fut]
        try:
            basic, file_row, text_rows, exceptions, elapsed, status = fut.result()
        except Exception as e:
            basic=None
            file_row=None
            text_rows=[]
            exceptions=[{"file_id":"","report_id":"","issue_type":"WORKER_EXCEPTION","severity":"HIGH","message":str(e),"path":p}]
            status="FAIL_EXCEPTION"

        done += 1
        if basic:
            basic_rows.append(basic)
        if file_row:
            file_rows.append(file_row)
        if text_rows:
            text_rows_all.extend(text_rows)
        if exceptions:
            exception_rows.extend(exceptions)

        if str(status).startswith("OK"):
            extracted += 1
        else:
            failed += 1

        if done % heartbeat_every == 0 or done == len(paths):
            heartbeat(done,len(paths),extracted,failed,len(text_rows_all),start,p)
            print(json.dumps({"done":done,"total":len(paths),"extracted":extracted,"failed":failed,"text_rows":len(text_rows_all)},ensure_ascii=False), flush=True)

elapsed=round(time.perf_counter()-start,4)
avg=round(elapsed/len(paths),4) if paths else 0
ppm=round(60/avg,2) if avg else 0

def write_csv(path, rows, fields):
    with open(path,"w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k:r.get(k,"") for k in fields})

write_csv(basic_csv,basic_rows,[
    "report_id","file_id","report_date","ticker","company_name","broker","analyst","rating",
    "target_price","currency","identity_score","source_confidence","review_required","file_name","path"
])

write_csv(file_csv,file_rows,[
    "file_id","file_name","file_path","file_size","page_count","pages_extracted","text_chars",
    "has_text_layer","ocr_required","elapsed_sec","status"
])

write_csv(text_csv,text_rows_all,[
    "report_id","file_id","ticker","report_date","broker","page","section","text","text_chars",
    "source_engine","confidence","path"
])

write_csv(exception_csv,exception_rows,[
    "file_id","report_id","issue_type","severity","message","path"
])

summary={
    "generated_at":now(),
    "input_reports":len(paths),
    "extracted_reports":extracted,
    "failed_reports":failed,
    "basic_rows":len(basic_rows),
    "file_rows":len(file_rows),
    "text_rows":len(text_rows_all),
    "exception_rows":len(exception_rows),
    "elapsed_sec":elapsed,
    "avg_sec_per_pdf":avg,
    "pdf_per_min":ppm,
    "has_fitz":HAS_FITZ,
    "max_pages_per_pdf":max_pages,
    "max_workers":max_workers,
    "basic_csv":basic_csv,
    "file_csv":file_csv,
    "text_csv":text_csv,
    "exception_csv":exception_csv
}

with open(json_out,"w",encoding="utf-8") as f:
    json.dump(summary,f,ensure_ascii=False,indent=2)

heartbeat(len(paths),len(paths),extracted,failed,len(text_rows_all),start,"COMPLETE")

print(json.dumps(summary,ensure_ascii=False))