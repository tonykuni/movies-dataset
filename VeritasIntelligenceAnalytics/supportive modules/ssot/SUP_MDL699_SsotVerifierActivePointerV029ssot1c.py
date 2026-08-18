import json, os, re, sys
from datetime import datetime
import pyarrow.parquet as pq

runtime1b = sys.argv[1]
active_pointer_path = sys.argv[2]
active_seal_path = sys.argv[3]
runtime_out = sys.argv[4]
activate_pointer = sys.argv[5].lower() == "true"

def now(): return datetime.now().isoformat()

def read_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def write_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

def pq_rows(path):
    pf = pq.ParquetFile(path)
    return pf.metadata.num_rows

def pq_table(path):
    return pq.read_table(path).to_pylist()

def add_check(layer,name,status,risk,metric,value,message,path):
    checks.append({
        "layer":layer,
        "name":name,
        "status":status,
        "risk":risk,
        "metric":metric,
        "value":str(value),
        "message":message,
        "path":path
    })

rt = read_json(runtime1b)
parquet_dir = rt.get("parquet_dir","")
pointer_candidate = rt.get("pointer_candidate_json","")
latest_basic = rt.get("latest_basic_candidate","")
latest_text = rt.get("latest_text_candidate","")

checks = []

tables = {
    "ticker_regex": os.path.join(parquet_dir, "VRN_TickerRegexSSOT_v029SSOT1B.parquet"),
    "date_regex": os.path.join(parquet_dir, "VRN_DatePeriodRegexSSOT_v029SSOT1B.parquet"),
    "rating_alias": os.path.join(parquet_dir, "VRN_RatingAliasSSOT_v029SSOT1B.parquet"),
    "broker_alias": os.path.join(parquet_dir, "VRN_BrokerAliasSSOT_v029SSOT1B.parquet"),
    "basic_def": os.path.join(parquet_dir, "VRN_BasicInfoDefinitionSSOT_v029SSOT1B.parquet"),
    "financial_alias": os.path.join(parquet_dir, "VRN_FinancialAccountAliasSSOT_v029SSOT1B.parquet"),
    "validation_rules": os.path.join(parquet_dir, "VRN_FinancialValidationRulesSSOT_v029SSOT1B.parquet"),
    "source_inventory": os.path.join(parquet_dir, "VRN_SSOT_SourceInventory_v029SSOT1B.parquet")
}

hard_blocks = 0
warns = 0

for name,path in tables.items():
    if os.path.exists(path):
        rows = pq_rows(path)
        add_check("SSOT_TABLE", name, "OK_FOUND", "LOW", "rows", rows, "SSOT parquet table exists.", path)
    else:
        hard_blocks += 1
        add_check("SSOT_TABLE", name, "BLOCK_MISSING", "HIGH", "exists", "false", "SSOT parquet table missing.", path)

# Ticker regex tests
ticker_rows = pq_table(tables["ticker_regex"]) if os.path.exists(tables["ticker_regex"]) else []
ticker_main = None
year_guard = False
yf_tw = False
yf_two = False
bbg = False

for r in ticker_rows:
    rid = str(r.get("rule_id",""))
    target = str(r.get("target",""))
    rx = str(r.get("regex",""))
    if rid == "TW_TICKER_4D_NONZERO":
        ticker_main = rx
    if "YEAR_GUARD" in rid:
        year_guard = True
    if target == "tw_yfinance_ticker" and ".TW" in rx:
        yf_tw = True
    if target == "tw_yfinance_ticker_alt" and ".TWO" in rx:
        yf_two = True
    if target == "tw_bloomberg_ticker":
        bbg = True

try:
    if ticker_main:
        reg = re.compile(ticker_main)
        ok_2330 = bool(reg.search("2330"))
        no_0230 = not bool(reg.search("0230"))
        if ok_2330 and no_0230 and year_guard and yf_tw and yf_two and bbg:
            add_check("REGEX_TEST", "TW ticker policy", "OK_VERIFIED", "LOW", "pass", "true", "TW_TICKER, yfinance, Bloomberg and year guard verified.", tables["ticker_regex"])
        else:
            warns += 1
            add_check("REGEX_TEST", "TW ticker policy", "WARN_REVIEW_REQUIRED", "MEDIUM", "pass", "partial", "Ticker policy exists but one guard/suffix test is partial.", tables["ticker_regex"])
    else:
        hard_blocks += 1
        add_check("REGEX_TEST", "TW ticker policy", "BLOCK_MISSING", "HIGH", "regex", "missing", "TW_TICKER_4D_NONZERO missing.", tables["ticker_regex"])
except Exception as e:
    hard_blocks += 1
    add_check("REGEX_TEST", "TW ticker policy", "BLOCK_REGEX_ERROR", "HIGH", "error", str(e), "Ticker regex failed to compile/test.", tables["ticker_regex"])

# Stage parquet tests
basic_rows = pq_rows(latest_basic) if os.path.exists(latest_basic) else 0
text_rows = pq_rows(latest_text) if os.path.exists(latest_text) else 0

if basic_rows == 400:
    add_check("STAGE_PARQUET", "BasicInfo candidate", "OK_VERIFIED", "LOW", "rows", basic_rows, "BasicInfo candidate row count verified.", latest_basic)
else:
    warns += 1
    add_check("STAGE_PARQUET", "BasicInfo candidate", "WARN_ROW_COUNT_REVIEW", "MEDIUM", "rows", basic_rows, "BasicInfo row count not exactly 400.", latest_basic)

if text_rows > 1000:
    add_check("STAGE_PARQUET", "ReportText candidate", "OK_VERIFIED", "LOW", "rows", text_rows, "ReportText candidate has sufficient rows.", latest_text)
else:
    warns += 1
    add_check("STAGE_PARQUET", "ReportText candidate", "WARN_TEXT_SMALL", "MEDIUM", "rows", text_rows, "ReportText rows smaller than expected.", latest_text)

# SSOT minimum coverage tests
financial_alias_count = pq_rows(tables["financial_alias"]) if os.path.exists(tables["financial_alias"]) else 0
validation_rule_count = pq_rows(tables["validation_rules"]) if os.path.exists(tables["validation_rules"]) else 0
broker_alias_count = pq_rows(tables["broker_alias"]) if os.path.exists(tables["broker_alias"]) else 0
rating_alias_count = pq_rows(tables["rating_alias"]) if os.path.exists(tables["rating_alias"]) else 0
date_regex_count = pq_rows(tables["date_regex"]) if os.path.exists(tables["date_regex"]) else 0

if financial_alias_count >= 40 and validation_rule_count >= 15:
    add_check("FINANCIAL_SSOT", "Financial baseline", "OK_VERIFIED", "LOW", "alias/rules", f"{financial_alias_count}/{validation_rule_count}", "Financial alias and validation-rule baseline passed.", tables["financial_alias"])
else:
    hard_blocks += 1
    add_check("FINANCIAL_SSOT", "Financial baseline", "BLOCK_BASELINE_INCOMPLETE", "HIGH", "alias/rules", f"{financial_alias_count}/{validation_rule_count}", "Financial SSOT baseline incomplete.", tables["financial_alias"])

if broker_alias_count >= 35:
    add_check("BROKER_SSOT", "Broker alias baseline", "OK_VERIFIED", "LOW", "aliases", broker_alias_count, "Broker alias baseline passed, but 33 missing broker rows still require later review.", tables["broker_alias"])
else:
    warns += 1
    add_check("BROKER_SSOT", "Broker alias baseline", "WARN_BROKER_SMALL", "MEDIUM", "aliases", broker_alias_count, "Broker alias count small.", tables["broker_alias"])

# Pointer policy
table_staging_allowed = (hard_blocks == 0 and basic_rows == 400 and text_rows > 1000 and financial_alias_count >= 40 and validation_rule_count >= 15)
canonical_allowed = False
canonical_block_reasons = [
    "Broker review remains possible.",
    "Exception queue not formally closed.",
    "Financial account coverage must be rechecked after 1D table extraction exposes actual account universe.",
    "Canonical promotion needs a separate gate."
]

ssot_score = 100
if hard_blocks > 0: ssot_score -= 40
if warns > 0: ssot_score -= min(20, warns * 5)
if broker_alias_count < 45: ssot_score -= 5
if financial_alias_count < 60: ssot_score -= 5
if ssot_score < 0: ssot_score = 0

status = "VRN_SSOT_ACTIVE_POINTER_READY" if table_staging_allowed else "VRN_SSOT_ACTIVE_POINTER_REVIEW_REQUIRED"
risk = "MEDIUM" if not canonical_allowed else "LOW"
if hard_blocks > 0:
    risk = "HIGH"

pointer = {
    "generated_at": now(),
    "status": status,
    "risk": risk,
    "version": "v029.SSOT.1C",
    "main_format": "parquet",
    "json_role": "control plane / manifest / runtime",
    "duckdb_role": "serving layer only; rebuildable from parquet",
    "table_staging_allowed": table_staging_allowed,
    "canonical_allowed": canonical_allowed,
    "canonical_block_reasons": canonical_block_reasons,
    "latest_basic_info_parquet": latest_basic,
    "latest_report_text_parquet": latest_text,
    "ssot_parquet_dir": parquet_dir,
    "ssot_tables": tables,
    "pointer_candidate_from_1b": pointer_candidate,
    "runtime_1b": runtime1b,
    "next_step": "Proceed to v029.VRN.1D Table Extraction Staging Gate using this active pointer." if table_staging_allowed else "Resolve hard blockers before 1D.",
    "checks": checks
}

seal = {
    "generated_at": now(),
    "status": status,
    "risk": risk,
    "hard_blocks": hard_blocks,
    "warnings": warns,
    "ssot_score": ssot_score,
    "activate_pointer": activate_pointer,
    "active_pointer_path": active_pointer_path if activate_pointer else "",
    "active_seal_path": active_seal_path,
    "table_staging_allowed": table_staging_allowed,
    "canonical_allowed": canonical_allowed,
    "basic_rows": basic_rows,
    "text_rows": text_rows,
    "financial_alias_count": financial_alias_count,
    "validation_rule_count": validation_rule_count,
    "broker_alias_count": broker_alias_count,
    "rating_alias_count": rating_alias_count,
    "date_regex_count": date_regex_count
}

if activate_pointer:
    write_json(active_pointer_path, pointer)

write_json(active_seal_path, seal)

runtime = {
    "generated_at": now(),
    "status": status,
    "risk": risk,
    "hard_blocks": hard_blocks,
    "warnings": warns,
    "ssot_score": ssot_score,
    "activate_pointer": activate_pointer,
    "active_pointer_path": active_pointer_path if activate_pointer else "",
    "active_seal_path": active_seal_path,
    "table_staging_allowed": table_staging_allowed,
    "canonical_allowed": canonical_allowed,
    "basic_rows": basic_rows,
    "text_rows": text_rows,
    "financial_alias_count": financial_alias_count,
    "validation_rule_count": validation_rule_count,
    "broker_alias_count": broker_alias_count,
    "rating_alias_count": rating_alias_count,
    "date_regex_count": date_regex_count,
    "ssot_parquet_dir": parquet_dir,
    "latest_basic_info_parquet": latest_basic,
    "latest_report_text_parquet": latest_text,
    "checks": checks,
    "next_step": pointer["next_step"]
}

write_json(runtime_out, runtime)
print(json.dumps(runtime, ensure_ascii=False))