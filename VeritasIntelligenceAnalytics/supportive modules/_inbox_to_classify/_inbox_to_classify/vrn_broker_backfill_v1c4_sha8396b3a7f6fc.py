import json, sys, time, csv
from datetime import datetime
import pyarrow as pa
import pyarrow.parquet as pq

basic_in, text_in, basic_out, audit_out, audit_csv, runtime_js, heartbeat = sys.argv[1:8]

def now(): return datetime.now().isoformat()
def hb(stage,done=0,total=0,extra=None):
    with open(heartbeat,"w",encoding="utf-8") as f:
        json.dump({"generated_at":now(),"stage":stage,"done":done,"total":total,"extra":extra or {}},f,ensure_ascii=False,indent=2)

# TEXT-SAFE broker list: Chinese full names + unambiguous long English.
# Bare 2-letter abbreviations (MS/GS) deliberately EXCLUDED.
TEXT_SAFE = [
 "Goldman Sachs","Morgan Stanley","J.P. Morgan","JPMorgan","JP Morgan","Macquarie","Jefferies",
 "Nomura","Daiwa","CLSA","Citigroup","UBS","HSBC","KGI Securities","KGI","Yuanta","SinoPac",
 "Cathay","Mega Securities","Capital Securities",
 "元大","凱基","國泰","富邦","兆豐","永豐","群益","玉山","統一","中信","第一金","華南","台新"]
TEXT_SAFE = sorted(set(TEXT_SAFE), key=len, reverse=True)

def is_blank(v): return v is None or str(v).strip()==""
def find_broker_safe(text):
    low_l=(text or "").lower()
    for b in TEXT_SAFE:
        if b.lower() in low_l: return b
    return ""

start=time.perf_counter(); hb("START")
basic = pq.read_table(basic_in).to_pylist()
text  = pq.read_table(text_in).to_pylist()

hb("INDEX_TEXT", 0, len(text))
page1 = {}; firstrow = {}
for r in text:
    rid = str(r.get("report_id","") or "")
    if rid=="" : continue
    if rid not in firstrow: firstrow[rid] = r.get("text","") or ""
    if str(r.get("page","")).strip()=="1":
        page1.setdefault(rid, []).append(r.get("text","") or "")

def letterhead(rid):
    if rid in page1: return " ".join(page1[rid])[:4000]
    return (firstrow.get(rid,"") or "")[:4000]

before_missing = sum(1 for r in basic if is_blank(r.get("broker")))
filled=0; audit=[]; done=0
hb("BACKFILL", 0, len(basic))
for r in basic:
    if is_blank(r.get("broker")):
        rid = str(r.get("report_id","") or "")
        b = find_broker_safe(letterhead(rid))
        if b:
            r["broker"]=b; r["broker_source"]="report_text_page1"; r["broker_backfilled"]="True"; filled+=1
            audit.append({"report_id":rid,"file_id":r.get("file_id",""),"field":"broker",
                          "action":"BACKFILL_FROM_REPORTTEXT_PAGE1","value":b,
                          "matched_in":"page1" if rid in page1 else "firstrow","path":r.get("path","")})
        else:
            r.setdefault("broker_source",""); r.setdefault("broker_backfilled","False")
    else:
        r.setdefault("broker_source","existing"); r.setdefault("broker_backfilled","False")
    done+=1
    if done%50==0: hb("BACKFILL", done, len(basic))

after_missing = sum(1 for r in basic if is_blank(r.get("broker")))

def write_pq(path, rows, schema_fields=None):
    if rows:
        fields=sorted(set(str(k) for row in rows for k in row.keys() if k is not None))
        if schema_fields:
            for sf in schema_fields:
                if sf not in fields: fields.append(sf)
        cols={k:[str(row.get(k,"")) if row.get(k,"") is not None else "" for row in rows] for k in fields}
        tbl=pa.table(cols)
    else:
        fields=[str(s) for s in (schema_fields or ["_empty"])]
        tbl=pa.table({k:pa.array([],type=pa.string()) for k in fields})
    pq.write_table(tbl, path, compression="zstd")

hb("WRITE")
write_pq(basic_out, basic)
write_pq(audit_out, audit, ["report_id","file_id","field","action","value","matched_in","path"])
with open(audit_csv,"w",encoding="utf-8-sig",newline="") as f:
    fld=["report_id","file_id","field","action","value","matched_in","path"]
    w=csv.DictWriter(f,fieldnames=fld,extrasaction="ignore"); w.writeheader()
    for a in audit[:300]: w.writerow(a)

elapsed=round(time.perf_counter()-start,4)
summary={"generated_at":now(),"status":"VRN_1C4_BROKER_BACKFILL_DONE",
 "basic_rows":len(basic),"text_rows":len(text),
 "before_missing_broker":before_missing,"after_missing_broker":after_missing,
 "broker_backfilled":filled,"basic_parquet":basic_out,"audit_parquet":audit_out,"elapsed_sec":elapsed}
with open(runtime_js,"w",encoding="utf-8") as f: json.dump(summary,f,ensure_ascii=False,indent=2)
hb("COMPLETE")
print(json.dumps(summary,ensure_ascii=False))