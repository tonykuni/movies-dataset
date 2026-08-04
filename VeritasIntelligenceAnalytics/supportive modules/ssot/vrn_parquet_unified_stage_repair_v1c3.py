import csv, json, os, re, sys, hashlib, time
from datetime import datetime
import pyarrow as pa
import pyarrow.parquet as pq

# FIX P-B: Windows-safe field size limit (avoid >128KB field crash)
def set_field_limit():
    lim = sys.maxsize
    while lim > 4096:
        try:
            csv.field_size_limit(lim); return lim
        except OverflowError:
            lim = int(lim / 2)
    return csv.field_size_limit()
set_field_limit()

(basic_in,file_in,text_in,exception_in,
 basic_parquet,file_parquet,text_parquet,exception_parquet,mapping_parquet,audit_parquet,
 basic_audit_csv,exception_audit_csv,mapping_audit_csv,
 runtime_json,heartbeat_json) = sys.argv[1:16]
batch_size = int(sys.argv[16])

date_res=[re.compile(r"(20\d{2})[-_./]?(0[1-9]|1[0-2])[-_./]?([0-2]\d|3[01])"),
          re.compile(r"(1[0-2]\d)[-_./]?(0[1-9]|1[0-2])[-_./]?([0-2]\d|3[01])")]
broker_patterns=["Citi","Citigroup","Goldman","Goldman Sachs","GS","Daiwa","Morgan Stanley","MS","CLSA",
 "Nomura","UBS","JPM","JP Morgan","Jefferies","Macquarie","HSBC","元大","凱基","國泰","富邦","兆豐",
 "永豐","群益","玉山","統一","中信","第一金","華南","台新","KGI","Yuanta","Fubon","Sinopac","Cathay","Mega","Capital"]

def now(): return datetime.now().isoformat()
def write_heartbeat(stage,done=0,total=0,extra=None):
    with open(heartbeat_json,"w",encoding="utf-8") as f:
        json.dump({"generated_at":now(),"stage":stage,"done":done,"total":total,"extra":extra or {}},f,ensure_ascii=False,indent=2)

# FIX P-A: sanitize ragged rows. None restkey -> _csv_overflow ; flatten lists ; str-coerce keys.
# Append-only: never drops data; adds _csv_overflow/_ragged columns; row gets flagged for review.
def sanitize_row(row):
    clean={}; overflow=[]; ragged=False
    for k,v in row.items():
        if k is None:
            ragged=True
            if isinstance(v,list): overflow.extend("" if x is None else str(x) for x in v)
            elif v is not None:    overflow.append(str(v))
            continue
        kk=str(k)
        if isinstance(v,list):
            ragged=True; clean[kk]=",".join("" if x is None else str(x) for x in v)
        else:
            clean[kk]="" if v is None else str(v)
    clean["_csv_overflow"]=",".join(overflow)
    clean["_ragged"]="True" if ragged else "False"
    return clean,ragged

def read_csv(path):
    rows=[]; ragged=0
    with open(path,"r",encoding="utf-8-sig",newline="") as f:
        rd=csv.DictReader(f); fields=list(rd.fieldnames or [])
        for raw in rd:
            r,rg=sanitize_row(raw)
            if rg: ragged+=1
            rows.append(r)
    for extra in ("_csv_overflow","_ragged"):
        if extra not in fields: fields.append(extra)
    return rows,fields,ragged

def write_csv_sample(path,rows,fields,limit=300):
    with open(path,"w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore"); w.writeheader()
        for r in rows[:limit]: w.writerow({k:r.get(k,"") for k in fields})

# FIX P-C + P-D: robust field union (no None key) + empty input still keeps schema columns
def rows_to_parquet(path,rows,schema_fields=None):
    if rows:
        fields=sorted(set(str(k) for r in rows for k in r.keys() if k is not None))
        if schema_fields:
            for sf in schema_fields:
                if sf not in fields: fields.append(sf)
        cols={k:[str(r.get(k,"")) if r.get(k,"") is not None else "" for r in rows] for k in fields}
        table=pa.table(cols)
    else:
        fields=[str(s) for s in (schema_fields or ["_empty"])]
        table=pa.table({k:pa.array([],type=pa.string()) for k in fields})
    pq.write_table(table,path,compression="zstd")

def find_date(t):
    t=t or ""
    for r in date_res:
        m=r.search(t)
        if m:
            y=int(m.group(1))
            if y<1911: y+=1911
            return f"{y}-{m.group(2)}-{m.group(3)}"
    return ""
def find_broker(t):
    low=(t or "").lower()
    for b in broker_patterns:
        if b.lower() in low: return b
    return ""
def stable_id(row):
    raw="|".join([row.get("file_id",""),row.get("path",""),row.get("file_name",""),row.get("ticker",""),row.get("report_date",""),row.get("broker","")])
    return hashlib.sha1(raw.encode("utf-8","ignore")).hexdigest()[:20]

start=time.perf_counter(); write_heartbeat("START")
basic_rows,basic_fields,basic_ragged=read_csv(basic_in)
file_rows,file_fields,file_ragged=read_csv(file_in)
exception_rows,exception_fields,exception_ragged=read_csv(exception_in)

before_ids=[r.get("report_id","") for r in basic_rows]
before_duplicate_report_ids=len(before_ids)-len(set(before_ids))
before_missing_date=sum(1 for r in basic_rows if not r.get("report_date"))
before_missing_broker=sum(1 for r in basic_rows if not r.get("broker"))
before_missing_ticker=sum(1 for r in basic_rows if not r.get("ticker"))
before_review=sum(1 for r in basic_rows if str(r.get("review_required","")).lower() in ("true","1","yes"))

old_to_new_by_file_id={}; old_to_new_by_report_id={}; mapping_rows=[]; audit_rows=[]
seen=set(); date_filled=0; broker_filled=0
write_heartbeat("REKEY_BASIC",0,len(basic_rows))
for idx,row in enumerate(basic_rows,start=1):
    old_id=row.get("report_id","")
    context=" ".join([row.get("file_name",""),row.get("path",""),row.get("ticker",""),row.get("broker","")])
    if not row.get("report_date"):
        d=find_date(context)
        if d:
            row["report_date"]=d; date_filled+=1
            audit_rows.append({"file_id":row.get("file_id",""),"old_report_id":old_id,"field":"report_date","action":"FILLED_FROM_FILENAME_OR_PATH","value":d,"path":row.get("path","")})
    if not row.get("broker"):
        b=find_broker(context)
        if b:
            row["broker"]=b; broker_filled+=1
            audit_rows.append({"file_id":row.get("file_id",""),"old_report_id":old_id,"field":"broker","action":"FILLED_FROM_FILENAME_OR_PATH","value":b,"path":row.get("path","")})
    new_id=stable_id(row)
    if new_id in seen:
        new_id=hashlib.sha1((new_id+"|"+row.get("file_id","")+"|"+row.get("path","")+"|"+old_id).encode("utf-8","ignore")).hexdigest()[:24]
    seen.add(new_id)
    row["report_id_original"]=old_id; row["report_id"]=new_id
    fid=row.get("file_id",""); old_to_new_by_file_id[fid]=new_id
    if old_id: old_to_new_by_report_id[old_id]=new_id
    # FIX S-3: ragged rows are data-integrity suspects -> force review (no realign guess)
    if (not row.get("ticker")) or (not row.get("report_date")) or row.get("_ragged")=="True":
        row["review_required"]="True"
    elif str(row.get("review_required","")).lower() in ("true","1","yes"):
        row["review_required"]="False"
    mapping_rows.append({"file_id":fid,"old_report_id":old_id,"new_report_id":new_id,"ticker":row.get("ticker",""),"report_date":row.get("report_date",""),"broker":row.get("broker",""),"path":row.get("path","")})
    if idx%50==0: write_heartbeat("REKEY_BASIC",idx,len(basic_rows))

for r in file_rows:
    fid=r.get("file_id","")
    r.setdefault("report_id",""); r.setdefault("report_id_original",r.get("report_id",""))
    if fid in old_to_new_by_file_id: r["report_id"]=old_to_new_by_file_id[fid]
for r in exception_rows:
    fid=r.get("file_id",""); old=r.get("report_id",""); r["report_id_original"]=old
    if fid in old_to_new_by_file_id: r["report_id"]=old_to_new_by_file_id[fid]
    elif old in old_to_new_by_report_id: r["report_id"]=old_to_new_by_report_id[old]

write_heartbeat("WRITE_SMALL_PARQUET")
rows_to_parquet(basic_parquet,basic_rows,basic_fields)
rows_to_parquet(file_parquet,file_rows,file_fields)
rows_to_parquet(exception_parquet,exception_rows,exception_fields)
rows_to_parquet(mapping_parquet,mapping_rows,["file_id","old_report_id","new_report_id","ticker","report_date","broker","path"])
rows_to_parquet(audit_parquet,audit_rows,["file_id","old_report_id","field","action","value","path"])
write_csv_sample(basic_audit_csv,basic_rows,list(basic_rows[0].keys()) if basic_rows else [])
write_csv_sample(exception_audit_csv,exception_rows,list(exception_rows[0].keys()) if exception_rows else exception_fields)
write_csv_sample(mapping_audit_csv,mapping_rows,["file_id","old_report_id","new_report_id","ticker","report_date","broker","path"])

write_heartbeat("WRITE_TEXT_PARQUET",0,0)
writer=None; text_rows=0; text_batches=0; text_fields=None; text_ragged=0; batch=[]
def flush_batch(rows):
    global writer,text_batches
    if not rows: return
    cols={k:[str(r.get(k,"")) if r.get(k,"") is not None else "" for r in rows] for k in text_fields}
    table=pa.table(cols)
    if writer is None:
        writer=pq.ParquetWriter(text_parquet,table.schema,compression="zstd")
    writer.write_table(table); text_batches+=1
with open(text_in,"r",encoding="utf-8-sig",newline="") as f:
    reader=csv.DictReader(f)
    text_fields=list(reader.fieldnames or [])
    for extra in ("report_id_original","_csv_overflow","_ragged"):
        if extra not in text_fields: text_fields.append(extra)
    for raw in reader:
        r,rg=sanitize_row(raw)
        if rg: text_ragged+=1
        old=r.get("report_id",""); fid=r.get("file_id",""); r["report_id_original"]=old
        if fid in old_to_new_by_file_id: r["report_id"]=old_to_new_by_file_id[fid]
        elif old in old_to_new_by_report_id: r["report_id"]=old_to_new_by_report_id[old]
        batch.append(r); text_rows+=1
        if len(batch)>=batch_size:
            flush_batch(batch); batch=[]
            write_heartbeat("WRITE_TEXT_PARQUET",text_rows,0,{"batches":text_batches})
if batch: flush_batch(batch); batch=[]
if writer is not None: writer.close()
else: rows_to_parquet(text_parquet,[],text_fields)

after_ids=[r.get("report_id","") for r in basic_rows]
after_dup=len(after_ids)-len(set(after_ids))
after_md=sum(1 for r in basic_rows if not r.get("report_date"))
after_mb=sum(1 for r in basic_rows if not r.get("broker"))
after_mt=sum(1 for r in basic_rows if not r.get("ticker"))
after_review=sum(1 for r in basic_rows if str(r.get("review_required","")).lower() in ("true","1","yes"))
def pq_rows(p): return pq.ParquetFile(p).metadata.num_rows
validate={"basic":pq_rows(basic_parquet),"file":pq_rows(file_parquet),"text":pq_rows(text_parquet),"exception":pq_rows(exception_parquet),"mapping":pq_rows(mapping_parquet),"audit":pq_rows(audit_parquet)}
elapsed=round(time.perf_counter()-start,4)
ragged_total=basic_ragged+file_ragged+exception_ragged+text_ragged
summary={"generated_at":now(),"status":"VRN_1C3_PARQUET_UNIFIED_STAGE_REPAIRED",
 "risk":"LOW" if (after_dup==0 and after_mt==0) else "MEDIUM",
 "format_main":"parquet","csv_role":"audit_sample_only",
 "basic_rows":len(basic_rows),"file_rows":len(file_rows),"text_rows":text_rows,"text_batches":text_batches,"exception_rows":len(exception_rows),
 "before_duplicate_report_ids":before_duplicate_report_ids,"before_missing_report_date":before_missing_date,
 "before_missing_broker":before_missing_broker,"before_missing_ticker":before_missing_ticker,"before_review_required":before_review,
 "date_filled":date_filled,"broker_filled":broker_filled,
 "after_duplicate_report_ids":after_dup,"after_missing_report_date":after_md,"after_missing_broker":after_mb,
 "after_missing_ticker":after_mt,"after_review_required":after_review,
 "ragged_basic":basic_ragged,"ragged_file":file_ragged,"ragged_exception":exception_ragged,"ragged_text":text_ragged,"ragged_total":ragged_total,
 "elapsed_sec":elapsed,"parquet_validation":validate,
 "basic_parquet":basic_parquet,"file_parquet":file_parquet,"text_parquet":text_parquet,
 "exception_parquet":exception_parquet,"mapping_parquet":mapping_parquet,"audit_parquet":audit_parquet}
with open(runtime_json,"w",encoding="utf-8") as f: json.dump(summary,f,ensure_ascii=False,indent=2)
write_heartbeat("COMPLETE",text_rows,text_rows,{"elapsed_sec":elapsed})
print(json.dumps(summary,ensure_ascii=False))