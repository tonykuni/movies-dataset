import csv, json, os, re, sys, hashlib
from datetime import datetime

basic_in = sys.argv[1]
file_in = sys.argv[2]
text_in = sys.argv[3]
exception_in = sys.argv[4]

basic_out = sys.argv[5]
file_out = sys.argv[6]
text_out = sys.argv[7]
exception_out = sys.argv[8]
mapping_out = sys.argv[9]
audit_out = sys.argv[10]
runtime_out = sys.argv[11]

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

def read_csv(path):
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def write_csv(path, rows, fields):
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k:r.get(k,"") for k in fields})

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

basic_rows = read_csv(basic_in)
file_rows = read_csv(file_in)
exception_rows = read_csv(exception_in)

before_missing_date = sum(1 for r in basic_rows if not r.get("report_date"))
before_missing_broker = sum(1 for r in basic_rows if not r.get("broker"))
before_duplicates = len([g for g in {}])

old_to_new = {}
audit = []

seen_new = set()
duplicate_new = 0
date_filled = 0
broker_filled = 0
review_remaining = 0

for row in basic_rows:
    old_id = row.get("report_id","")
    context = " ".join([row.get("file_name",""), row.get("path","")])

    if not row.get("report_date"):
        d = find_date(context)
        if d:
            row["report_date"] = d
            date_filled += 1
            audit.append({
                "file_id":row.get("file_id",""),
                "old_report_id":old_id,
                "field":"report_date",
                "action":"FILLED_FROM_FILENAME_OR_PATH",
                "value":d,
                "path":row.get("path","")
            })

    if not row.get("broker"):
        b = find_broker(context)
        if b:
            row["broker"] = b
            broker_filled += 1
            audit.append({
                "file_id":row.get("file_id",""),
                "old_report_id":old_id,
                "field":"broker",
                "action":"FILLED_FROM_FILENAME_OR_PATH",
                "value":b,
                "path":row.get("path","")
            })

    new_id = stable_id(row)
    if new_id in seen_new:
        # Extremely unlikely, add file_id suffix
        new_id = hashlib.sha1((new_id + "|" + row.get("file_id","") + "|" + row.get("path","")).encode("utf-8","ignore")).hexdigest()[:24]
        duplicate_new += 1

    seen_new.add(new_id)
    row["report_id_original"] = old_id
    row["report_id"] = new_id
    old_to_new[row.get("file_id","")] = new_id

    if not row.get("report_date") or not row.get("ticker"):
        row["review_required"] = "True"
        review_remaining += 1
    else:
        if str(row.get("review_required","")).lower() in ("true","1","yes"):
            if row.get("report_date") and row.get("ticker"):
                row["review_required"] = "False"

mapping_rows = []
for row in basic_rows:
    mapping_rows.append({
        "file_id":row.get("file_id",""),
        "old_report_id":row.get("report_id_original",""),
        "new_report_id":row.get("report_id",""),
        "ticker":row.get("ticker",""),
        "report_date":row.get("report_date",""),
        "broker":row.get("broker",""),
        "path":row.get("path","")
    })

# Rewrite text CSV streaming because it is huge
with open(text_in, "r", encoding="utf-8-sig", newline="") as src, open(text_out, "w", encoding="utf-8-sig", newline="") as dst:
    reader = csv.DictReader(src)
    fields = list(reader.fieldnames or [])
    if "report_id_original" not in fields:
        fields.append("report_id_original")
    writer = csv.DictWriter(dst, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    text_count = 0
    for r in reader:
        old = r.get("report_id","")
        fid = r.get("file_id","")
        r["report_id_original"] = old
        if fid in old_to_new:
            r["report_id"] = old_to_new[fid]
        writer.writerow(r)
        text_count += 1

# Rewrite exception CSV
for r in exception_rows:
    old = r.get("report_id","")
    fid = r.get("file_id","")
    r["report_id_original"] = old
    if fid in old_to_new:
        r["report_id"] = old_to_new[fid]

# File registry does not always have report_id; add if possible by file_id
for r in file_rows:
    fid = r.get("file_id","")
    if "report_id" not in r:
        r["report_id"] = ""
    if fid in old_to_new:
        r["report_id"] = old_to_new[fid]

basic_fields = list(basic_rows[0].keys()) if basic_rows else []
file_fields = list(file_rows[0].keys()) if file_rows else []
exception_fields = list(exception_rows[0].keys()) if exception_rows else []

write_csv(basic_out, basic_rows, basic_fields)
write_csv(file_out, file_rows, file_fields)
write_csv(exception_out, exception_rows, exception_fields)
write_csv(mapping_out, mapping_rows, ["file_id","old_report_id","new_report_id","ticker","report_date","broker","path"])
write_csv(audit_out, audit, ["file_id","old_report_id","field","action","value","path"])

after_missing_date = sum(1 for r in basic_rows if not r.get("report_date"))
after_missing_broker = sum(1 for r in basic_rows if not r.get("broker"))
after_missing_ticker = sum(1 for r in basic_rows if not r.get("ticker"))
after_review_required = sum(1 for r in basic_rows if str(r.get("review_required","")).lower() in ("true","1","yes"))

ids = [r.get("report_id","") for r in basic_rows]
after_duplicate_report_ids = len(ids) - len(set(ids))

summary = {
    "generated_at": datetime.now().isoformat(),
    "status": "VRN_1C1_STAGING_IDENTITY_REPAIRED",
    "risk": "LOW" if after_duplicate_report_ids == 0 and after_missing_ticker == 0 else "MEDIUM",
    "basic_rows": len(basic_rows),
    "file_rows": len(file_rows),
    "text_rows": text_count,
    "exception_rows": len(exception_rows),
    "before_missing_report_date": before_missing_date,
    "before_missing_broker": before_missing_broker,
    "date_filled": date_filled,
    "broker_filled": broker_filled,
    "after_missing_report_date": after_missing_date,
    "after_missing_broker": after_missing_broker,
    "after_missing_ticker": after_missing_ticker,
    "after_review_required": after_review_required,
    "after_duplicate_report_ids": after_duplicate_report_ids,
    "duplicate_new_fallback_count": duplicate_new,
    "basic_fixed_csv": basic_out,
    "file_fixed_csv": file_out,
    "text_fixed_csv": text_out,
    "exception_fixed_csv": exception_out,
    "mapping_csv": mapping_out,
    "audit_csv": audit_out
}

with open(runtime_out, "w", encoding="utf-8") as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)

print(json.dumps(summary, ensure_ascii=False))