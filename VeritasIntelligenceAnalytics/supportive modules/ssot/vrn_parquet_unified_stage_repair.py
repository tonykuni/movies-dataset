import csv, json, os, re, sys, hashlib, time
from datetime import datetime

try:
    csv.field_size_limit(sys.maxsize)
except Exception:
    pass

import pyarrow as pa
import pyarrow.parquet as pq

basic_in = sys.argv[1]
file_in = sys.argv[2]
text_in = sys.argv[3]
exception_in = sys.argv[4]

basic_parquet = sys.argv[5]
file_parquet = sys.argv[6]
text_parquet = sys.argv[7]
exception_parquet = sys.argv[8]
mapping_parquet = sys.argv[9]
audit_parquet = sys.argv[10]

basic_audit_csv = sys.argv[11]
exception_audit_csv = sys.argv[12]
mapping_audit_csv = sys.argv[13]

runtime_json = sys.argv[14]
heartbeat_json = sys.argv[15]
batch_size = int(sys.argv[16])

date_res = [
    re.compile(r"(20\d{2})[-_./]?(0[1-9]|1[0-2])[-_./]?([0-2]\d|3[01])"),
    re.compile(r"(1[0-2]\d)[-_./]?(0[1-9]|1[0-2])[-_./]?([0-2]\d|3[01])")
]

broker_patterns = [
    "Citi","Citigroup","Goldman","Goldman Sachs","GS","Daiwa","Morgan Stanley","MS","CLSA",
    "Nomura","UBS","JPM","JP Morgan","Jefferies","Macquarie","HSBC",
    "元大","凱基","國泰","富邦","兆豐","永豐","群益","玉山","統一","中信","第一金","華南","台新",
    "KGI","Yuanta","Fubon","Sinopac","Cathay","Mega","Capital"
]

def now():
    return datetime.now().isoformat()

def write_heartbeat(stage, done=0, total=0, extra=None):
    payload = {
        "generated_at": now(),
        "stage": stage,
        "done": done,
        "total": total,
        "extra": extra or {}
    }
    with open(heartbeat_json, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

def read_csv_list(path):
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def write_csv_sample(path, rows, fields, limit=300):
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows[:limit]:
            w.writerow({k:r.get(k,"") for k in fields})

def rows_to_parquet(path, rows):
    if not rows:
        table = pa.table({})
    else:
        fields = sorted(set(k for r in rows for k in r.keys()))
        cols = {k:[str(r.get(k,"")) if r.get(k,"") is not None else "" for r in rows] for k in fields}
        table = pa.table(cols)
    pq.write_table(table, path, compression="zstd")

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

def stable_id(row):
    raw = "|".join([
        row.get("file_id",""),
        row.get("path",""),
        row.get("file_name",""),
        row.get("ticker",""),
        row.get("report_date",""),
        row.get("broker","")
    ])
    return hashlib.sha1(raw.encode("utf-8","ignore")).hexdigest()[:20]

def count_lines(path):
    c = 0
    with open(path, "r", encoding="utf-8-sig", errors="ignore") as f:
        for _ in f:
            c += 1
    return c

start = time.perf_counter()
write_heartbeat("START")

basic_rows = read_csv_list(basic_in)
file_rows = read_csv_list(file_in)
exception_rows = read_csv_list(exception_in)

before_ids = [r.get("report_id","") for r in basic_rows]
before_duplicate_report_ids = len(before_ids) - len(set(before_ids))
before_missing_date = sum(1 for r in basic_rows if not r.get("report_date"))
before_missing_broker = sum(1 for r in basic_rows if not r.get("broker"))
before_missing_ticker = sum(1 for r in basic_rows if not r.get("ticker"))
before_review_required = sum(1 for r in basic_rows if str(r.get("review_required","")).lower() in ("true","1","yes"))

old_to_new_by_file_id = {}
old_to_new_by_report_id = {}
mapping_rows = []
audit_rows = []
seen = set()
date_filled = 0
broker_filled = 0

write_heartbeat("REKEY_BASIC", 0, len(basic_rows))

for idx, row in enumerate(basic_rows, start=1):
    old_id = row.get("report_id","")
    context = " ".join([
        row.get("file_name",""),
        row.get("path",""),
        row.get("ticker",""),
        row.get("broker","")
    ])

    if not row.get("report_date"):
        d = find_date(context)
        if d:
            row["report_date"] = d
            date_filled += 1
            audit_rows.append({
                "file_id": row.get("file_id",""),
                "old_report_id": old_id,
                "field": "report_date",
                "action": "FILLED_FROM_FILENAME_OR_PATH",
                "value": d,
                "path": row.get("path","")
            })

    if not row.get("broker"):
        b = find_broker(context)
        if b:
            row["broker"] = b
            broker_filled += 1
            audit_rows.append({
                "file_id": row.get("file_id",""),
                "old_report_id": old_id,
                "field": "broker",
                "action": "FILLED_FROM_FILENAME_OR_PATH",
                "value": b,
                "path": row.get("path","")
            })

    new_id = stable_id(row)

    if new_id in seen:
        new_id = hashlib.sha1((new_id + "|" + row.get("file_id","") + "|" + row.get("path","") + "|" + old_id).encode("utf-8","ignore")).hexdigest()[:24]

    seen.add(new_id)

    row["report_id_original"] = old_id
    row["report_id"] = new_id

    fid = row.get("file_id","")
    old_to_new_by_file_id[fid] = new_id
    if old_id:
        old_to_new_by_report_id[old_id] = new_id

    if not row.get("ticker") or not row.get("report_date"):
        row["review_required"] = "True"
    else:
        if str(row.get("review_required","")).lower() in ("true","1","yes"):
            row["review_required"] = "False"

    mapping_rows.append({
        "file_id": fid,
        "old_report_id": old_id,
        "new_report_id": new_id,
        "ticker": row.get("ticker",""),
        "report_date": row.get("report_date",""),
        "broker": row.get("broker",""),
        "path": row.get("path","")
    })

    if idx % 50 == 0:
        write_heartbeat("REKEY_BASIC", idx, len(basic_rows))

for r in file_rows:
    fid = r.get("file_id","")
    if "report_id" not in r:
        r["report_id"] = ""
    if "report_id_original" not in r:
        r["report_id_original"] = r.get("report_id","")
    if fid in old_to_new_by_file_id:
        r["report_id"] = old_to_new_by_file_id[fid]

for r in exception_rows:
    fid = r.get("file_id","")
    old = r.get("report_id","")
    r["report_id_original"] = old
    if fid in old_to_new_by_file_id:
        r["report_id"] = old_to_new_by_file_id[fid]
    elif old in old_to_new_by_report_id:
        r["report_id"] = old_to_new_by_report_id[old]

write_heartbeat("WRITE_SMALL_PARQUET")
rows_to_parquet(basic_parquet, basic_rows)
rows_to_parquet(file_parquet, file_rows)
rows_to_parquet(exception_parquet, exception_rows)
rows_to_parquet(mapping_parquet, mapping_rows)
rows_to_parquet(audit_parquet, audit_rows)

write_csv_sample(basic_audit_csv, basic_rows, list(basic_rows[0].keys()) if basic_rows else [])
write_csv_sample(exception_audit_csv, exception_rows, list(exception_rows[0].keys()) if exception_rows else [])
write_csv_sample(mapping_audit_csv, mapping_rows, ["file_id","old_report_id","new_report_id","ticker","report_date","broker","path"])

write_heartbeat("WRITE_TEXT_PARQUET", 0, 0)

# Streaming rewrite ReportText to parquet with new report_id by file_id / old_report_id.
writer = None
text_rows = 0
text_batches = 0
text_fields = None
batch = []

def flush_batch(batch_rows):
    global writer, text_batches, text_fields
    if not batch_rows:
        return
    fields = text_fields
    cols = {k:[str(r.get(k,"")) if r.get(k,"") is not None else "" for r in batch_rows] for k in fields}
    table = pa.table(cols)
    if writer is None:
        writer = pq.ParquetWriter(text_parquet, table.schema, compression="zstd")
    writer.write_table(table)
    text_batches += 1

with open(text_in, "r", encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f)
    text_fields = list(reader.fieldnames or [])
    if "report_id_original" not in text_fields:
        text_fields.append("report_id_original")
    for r in reader:
        old = r.get("report_id","")
        fid = r.get("file_id","")
        r["report_id_original"] = old
        if fid in old_to_new_by_file_id:
            r["report_id"] = old_to_new_by_file_id[fid]
        elif old in old_to_new_by_report_id:
            r["report_id"] = old_to_new_by_report_id[old]

        batch.append(r)
        text_rows += 1

        if len(batch) >= batch_size:
            flush_batch(batch)
            batch = []
            write_heartbeat("WRITE_TEXT_PARQUET", text_rows, 0, {"batches": text_batches})

if batch:
    flush_batch(batch)
    batch = []

if writer is not None:
    writer.close()
else:
    # empty text parquet
    pq.write_table(pa.table({}), text_parquet, compression="zstd")

after_ids = [r.get("report_id","") for r in basic_rows]
after_duplicate_report_ids = len(after_ids) - len(set(after_ids))
after_missing_date = sum(1 for r in basic_rows if not r.get("report_date"))
after_missing_broker = sum(1 for r in basic_rows if not r.get("broker"))
after_missing_ticker = sum(1 for r in basic_rows if not r.get("ticker"))
after_review_required = sum(1 for r in basic_rows if str(r.get("review_required","")).lower() in ("true","1","yes"))

# Parquet validation metadata
def pq_rows(path):
    pf = pq.ParquetFile(path)
    return pf.metadata.num_rows

validate = {
    "basic_parquet_rows": pq_rows(basic_parquet),
    "file_parquet_rows": pq_rows(file_parquet),
    "text_parquet_rows": pq_rows(text_parquet),
    "exception_parquet_rows": pq_rows(exception_parquet),
    "mapping_parquet_rows": pq_rows(mapping_parquet),
    "audit_parquet_rows": pq_rows(audit_parquet)
}

elapsed = round(time.perf_counter() - start, 4)

summary = {
    "generated_at": now(),
    "status": "VRN_1C2_PARQUET_UNIFIED_STAGE_REPAIRED",
    "risk": "LOW" if after_duplicate_report_ids == 0 and after_missing_ticker == 0 else "MEDIUM",
    "format_main": "parquet",
    "csv_role": "audit_sample_only",
    "basic_rows": len(basic_rows),
    "file_rows": len(file_rows),
    "text_rows": text_rows,
    "text_batches": text_batches,
    "exception_rows": len(exception_rows),
    "before_duplicate_report_ids": before_duplicate_report_ids,
    "before_missing_report_date": before_missing_date,
    "before_missing_broker": before_missing_broker,
    "before_missing_ticker": before_missing_ticker,
    "before_review_required": before_review_required,
    "date_filled": date_filled,
    "broker_filled": broker_filled,
    "after_duplicate_report_ids": after_duplicate_report_ids,
    "after_missing_report_date": after_missing_date,
    "after_missing_broker": after_missing_broker,
    "after_missing_ticker": after_missing_ticker,
    "after_review_required": after_review_required,
    "elapsed_sec": elapsed,
    "parquet_validation": validate,
    "basic_parquet": basic_parquet,
    "file_parquet": file_parquet,
    "text_parquet": text_parquet,
    "exception_parquet": exception_parquet,
    "mapping_parquet": mapping_parquet,
    "audit_parquet": audit_parquet,
    "basic_audit_csv": basic_audit_csv,
    "exception_audit_csv": exception_audit_csv,
    "mapping_audit_csv": mapping_audit_csv
}

with open(runtime_json, "w", encoding="utf-8") as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)

write_heartbeat("COMPLETE", text_rows, text_rows, {"elapsed_sec": elapsed})
print(json.dumps(summary, ensure_ascii=False))