import json, sys, time, csv, re
from datetime import datetime
import pyarrow as pa
import pyarrow.parquet as pq

basic_in, text_in, basic_out, audit_out, audit_csv, runtime_js, heartbeat = sys.argv[1:8]

def now(): return datetime.now().isoformat()
def hb(stage,done=0,total=0,extra=None):
    with open(heartbeat,"w",encoding="utf-8") as f:
        json.dump({"generated_at":now(),"stage":stage,"done":done,"total":total,"extra":extra or {}},f,ensure_ascii=False,indent=2)

TEXT_SAFE=["Goldman Sachs","Morgan Stanley","J.P. Morgan","JPMorgan","JP Morgan","Macquarie","Jefferies",
 "Nomura","Daiwa","CLSA","Citigroup","UBS","HSBC","KGI Securities","KGI","Yuanta","SinoPac","Cathay",
 "Mega Securities","Capital Securities","元大","凱基","國泰","富邦","兆豐","永豐","群益","玉山","統一","中信","第一金","華南","台新"]
TEXT_SAFE=sorted(set(TEXT_SAFE),key=len,reverse=True)
def is_blank(v): return v is None or str(v).strip()==""
def find_broker_safe(t):
    low=(t or "").lower()
    for b in TEXT_SAFE:
        if b.lower() in low: return b
    return ""

def pick(names, regexes, avoid=()):
    for rx in regexes:
        for n in names:
            if n not in avoid and re.search(rx,n,re.I): return n
    return None

start=time.perf_counter(); hb("START")
bt=pq.read_table(basic_in); basic=bt.to_pylist()
tt=pq.read_table(text_in); names=tt.column_names; text=tt.to_pylist()

# --- AUTO-DETECT columns (no more guessing) ---
key_col = pick(names,[r'^report_id$',r'report.?id']) or pick(names,[r'^file_id$',r'file.?id'])
page_col= pick(names,[r'^page$',r'page.?(no|num|idx|index)',r'^(idx|index|order|seq)$',r'chunk.?(id|idx|index)'])
text_col= pick(names,[r'(^|_)(text|content|body|ocr)(_|$)',r'report.?text',r'chunk.?text'])
if not text_col:
    # fallback: longest average-length string column (excluding key/page)
    cand=[n for n in names if n not in (key_col,page_col)]
    best=None;bestlen=-1
    sample=text[:200] if text else []
    for n in cand:
        avg=sum(len(str(r.get(n,"") or "")) for r in sample)/max(1,len(sample))
        if avg>bestlen: bestlen=avg;best=n
    text_col=best

hb("INDEX_TEXT",0,len(text))
# group rows by key; capture page-1 zone (min page) text
def keyval(r): return str(r.get(key_col,"") or "")
def pageval(r):
    if not page_col: return None
    v=str(r.get(page_col,"")).strip()
    try: return float(v)
    except: return None

bykey={}
for r in text:
    k=keyval(r)
    if k=="" : continue
    bykey.setdefault(k,[]).append(r)

def letterhead(k):
    rows=bykey.get(k)
    if not rows: return ""
    if page_col:
        pgs=[pageval(r) for r in rows if pageval(r) is not None]
        if pgs:
            mn=min(pgs)
            zone=[r for r in rows if pageval(r)==mn]
            return " ".join(str(r.get(text_col,"") or "") for r in zone)[:4000]
    # no page col: first 2 rows by appearance
    return " ".join(str(r.get(text_col,"") or "") for r in rows[:2])[:4000]

# coverage diagnostics
blank_rows=[r for r in basic if is_blank(r.get("broker"))]
target_keys=set(str(r.get(key_col,"") or "") for r in blank_rows)
text_keys=set(bykey.keys())
target_with_text=len(target_keys & text_keys)
target_without_text=len(target_keys - text_keys)

filled=0; audit=[]; done=0
hb("BACKFILL",0,len(basic))
for r in basic:
    if is_blank(r.get("broker")):
        k=str(r.get(key_col,"") or "")
        b=find_broker_safe(letterhead(k))
        if b:
            r["broker"]=b;r["broker_source"]="report_text_zone1";r["broker_backfilled"]="True";filled+=1
            audit.append({"report_id":r.get("report_id",""),"file_id":r.get("file_id",""),"field":"broker",
                          "action":"BACKFILL_FROM_REPORTTEXT_ZONE1","value":b,"join_key":key_col,"path":r.get("path","")})
        else:
            r.setdefault("broker_source","");r.setdefault("broker_backfilled","False")
    else:
        r.setdefault("broker_source","existing");r.setdefault("broker_backfilled","False")
    done+=1
    if done%50==0: hb("BACKFILL",done,len(basic))
after_missing=sum(1 for r in basic if is_blank(r.get("broker")))

def write_pq(path,rows,sf=None):
    if rows:
        f=sorted(set(str(k) for row in rows for k in row.keys() if k is not None))
        if sf:
            for s in sf:
                if s not in f: f.append(s)
        tbl=pa.table({k:[str(row.get(k,"")) if row.get(k,"") is not None else "" for row in rows] for k in f})
    else:
        f=[str(s) for s in (sf or ["_empty"])]; tbl=pa.table({k:pa.array([],type=pa.string()) for k in f})
    pq.write_table(tbl,path,compression="zstd")
hb("WRITE")
write_pq(basic_out,basic)
write_pq(audit_out,audit,["report_id","file_id","field","action","value","join_key","path"])
with open(audit_csv,"w",encoding="utf-8-sig",newline="") as f:
    fld=["report_id","file_id","field","action","value","join_key","path"]
    w=csv.DictWriter(f,fieldnames=fld,extrasaction="ignore");w.writeheader()
    for a in audit[:300]: w.writerow(a)

elapsed=round(time.perf_counter()-start,4)
summary={"generated_at":now(),"status":"VRN_1C41_BROKER_BACKFILL_DONE",
 "detected_text_schema":names,"resolved_key_col":key_col,"resolved_page_col":page_col,"resolved_text_col":text_col,
 "basic_rows":len(basic),"text_rows":len(text),
 "before_missing_broker":len(blank_rows),"after_missing_broker":after_missing,"broker_backfilled":filled,
 "target_with_text":target_with_text,"target_without_text":target_without_text,
 "basic_parquet":basic_out,"audit_parquet":audit_out,"elapsed_sec":elapsed}
with open(runtime_js,"w",encoding="utf-8") as f: json.dump(summary,f,ensure_ascii=False,indent=2)
hb("COMPLETE")
print(json.dumps(summary,ensure_ascii=False))