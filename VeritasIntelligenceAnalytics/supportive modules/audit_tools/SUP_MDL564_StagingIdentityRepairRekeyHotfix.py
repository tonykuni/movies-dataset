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
import csv, json, os, re, sys, hashlib
from datetime import datetime

try:
    csv.field_size_limit(sys.maxsize)
except Exception:
    pass

basic_in = sys.argv[1]
file_in = sys.argv[2]
text_in = sys.argv[3]
exception_in = sys.argv[4]

basic_out = sys.argv[5]
file_out = sys.argv[6]
exception_out = sys.argv[7]
mapping_out = sys.argv[8]
audit_out = sys.argv[9]
text_lazy_map_json = sys.argv[10]
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

def line_count(path):
    count = 0
    with open(path, "r", encoding="utf-8-sig", errors="ignore") as f:
        for _ in f:
            count += 1
    return count

basic_rows = read_csv(basic_in)
file_rows = read_csv(file_in)
exception_rows = read_csv(exception_in)
text_lines = line_count(text_in)

before_ids = [r.get("report_id","") for r in basic_rows]
before_duplicate_report_ids = len(before_ids) - len(set(before_ids))
before_missing_date = sum(1 for r in basic_rows if not r.get("report_date"))
before_missing_broker = sum(1 for r in basic_rows if not r.get("broker"))
before_missing_ticker = sum(1 for r in basic_rows if not r.get("ticker"))
before_review_required = sum(1 for r in basic_rows if str(r.get("review_required","")).lower() in ("true","1","yes"))

old_to_new_by_file_id = {}
old_to_new_by_report_id = {}
audit = []
mapping_rows = []

seen = set()
date_filled = 0
broker_filled = 0

for row in basic_rows:
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

    if new_id in seen:
        new_id = hashlib.sha1((new_id + "|" + row.get("file_id","") + "|" + row.get("path","") + "|" + old_id).encode("utf-8","ignore")).hexdigest()[:24]

    seen.add(new_id)

    row["report_id_original"] = old_id
    row["report_id"] = new_id

    old_to_new_by_file_id[row.get("file_id","")] = new_id
    if old_id:
        old_to_new_by_report_id[old_id] = new_id

    if not row.get("ticker") or not row.get("report_date"):
        row["review_required"] = "True"
    else:
        if str(row.get("review_required","")).lower() in ("true","1","yes"):
            row["review_required"] = "False"

    mapping_rows.append({
        "file_id":row.get("file_id",""),
        "old_report_id":old_id,
        "new_report_id":new_id,
        "ticker":row.get("ticker",""),
        "report_date":row.get("report_date",""),
        "broker":row.get("broker",""),
        "path":row.get("path","")
    })

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

basic_fields = list(basic_rows[0].keys()) if basic_rows else []
file_fields = list(file_rows[0].keys()) if file_rows else []
exception_fields = list(exception_rows[0].keys()) if exception_rows else []

write_csv(basic_out, basic_rows, basic_fields)
write_csv(file_out, file_rows, file_fields)
write_csv(exception_out, exception_rows, exception_fields)
write_csv(mapping_out, mapping_rows, ["file_id","old_report_id","new_report_id","ticker","report_date","broker","path"])

if audit:
    write_csv(audit_out, audit, ["file_id","old_report_id","field","action","value","path"])
else:
    write_csv(audit_out, [], ["file_id","old_report_id","field","action","value","path"])

after_ids = [r.get("report_id","") for r in basic_rows]
after_duplicate_report_ids = len(after_ids) - len(set(after_ids))
after_missing_date = sum(1 for r in basic_rows if not r.get("report_date"))
after_missing_broker = sum(1 for r in basic_rows if not r.get("broker"))
after_missing_ticker = sum(1 for r in basic_rows if not r.get("ticker"))
after_review_required = sum(1 for r in basic_rows if str(r.get("review_required","")).lower() in ("true","1","yes"))

lazy_mapping = {
    "mode":"lazy_report_id_mapping_for_text_stage",
    "reason":"ReportText CSV is very large; do not rewrite text in hotfix. Use file_id/report_id mapping during downstream joins.",
    "original_text_csv":text_in,
    "original_text_lines":text_lines,
    "mapping_csv":mapping_out,
    "mapping_key_primary":"file_id",
    "mapping_key_secondary":"old_report_id",
    "new_report_id_column":"new_report_id"
}

with open(text_lazy_map_json, "w", encoding="utf-8") as f:
    json.dump(lazy_mapping, f, ensure_ascii=False, indent=2)

summary = {
    "generated_at": datetime.now().isoformat(),
    "status": "VRN_1C1_HOTFIX_STAGING_IDENTITY_REPAIRED",
    "risk": "LOW" if after_duplicate_report_ids == 0 and after_missing_ticker == 0 else "MEDIUM",
    "basic_rows": len(basic_rows),
    "file_rows": len(file_rows),
    "exception_rows": len(exception_rows),
    "text_original_lines": text_lines,
    "text_rewrite": False,
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
    "basic_fixed_csv": basic_out,
    "file_fixed_csv": file_out,
    "exception_fixed_csv": exception_out,
    "mapping_csv": mapping_out,
    "audit_csv": audit_out,
    "text_lazy_map_json": text_lazy_map_json
}

with open(runtime_out, "w", encoding="utf-8") as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)

print(json.dumps(summary, ensure_ascii=False))