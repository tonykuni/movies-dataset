import json, os, re, sys, hashlib
from datetime import datetime
import pyarrow as pa
import pyarrow.parquet as pq

source_inventory_json = sys.argv[1]
parquet_dir = sys.argv[2]
json_dir = sys.argv[3]
runtime_json = sys.argv[4]
latest_basic = sys.argv[5]
latest_text = sys.argv[6]
latest_manifest = sys.argv[7]
latest_broker_runtime = sys.argv[8]

def now(): return datetime.now().isoformat()

def write_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

def rows_to_parquet(path, rows, schema_fields=None):
    fields = []
    if schema_fields:
        fields.extend(schema_fields)
    for r in rows:
        for k in r.keys():
            if k not in fields:
                fields.append(k)
    if rows:
        table = pa.table({k:[str(r.get(k,"")) if r.get(k,"") is not None else "" for r in rows] for k in fields})
    else:
        table = pa.table({k:pa.array([], type=pa.string()) for k in fields})
    pq.write_table(table, path, compression="zstd")

def sha12(s):
    return hashlib.sha1(str(s).encode("utf-8","ignore")).hexdigest()[:12]

with open(source_inventory_json, "r", encoding="utf-8") as f:
    sources = json.load(f)

# ==============================================================================
# 1. Regex / Ticker SSOT
# ==============================================================================
ticker_regex = [
    {
        "rule_id":"TW_TICKER_4D_NONZERO",
        "target":"tw_ticker",
        "regex":r"(?<!\d)([1-9]\d{3})(?!\d)",
        "definition":"台股四碼；第一碼不可為 0。",
        "negative_guard":"若 token 是 2021~2030，先標 YEAR_AMBIGUOUS，不可直接當 ticker。",
        "priority":"P0"
    },
    {
        "rule_id":"TW_YFINANCE_TW",
        "target":"tw_yfinance_ticker",
        "regex":r"(?<!\d)([1-9]\d{3})\.TW\b",
        "definition":"上市 yfinance ticker = TW_TICKER + .TW",
        "priority":"P0"
    },
    {
        "rule_id":"TW_YFINANCE_TWO",
        "target":"tw_yfinance_ticker_alt",
        "regex":r"(?<!\d)([1-9]\d{3})\.TWO\b",
        "definition":"上櫃 yfinance ticker = TW_TICKER + .TWO",
        "priority":"P0"
    },
    {
        "rule_id":"TW_BLOOMBERG_TT",
        "target":"tw_bloomberg_ticker",
        "regex":r"(?<!\d)([1-9]\d{3})\s*TT\b",
        "definition":"Bloomberg 台股 ticker = TW_TICKER + TT",
        "priority":"P0"
    },
    {
        "rule_id":"FILENAME_TOKENIZER",
        "target":"filename_token",
        "regex":r"[\u4e00-\u9fff]+|[A-Za-z]+|[1-9]\d*",
        "definition":"中英文標點符號與空白切開後，取連續中文、連續英文、連續數字 token，TRIM 後作候選。",
        "priority":"P0"
    },
    {
        "rule_id":"YEAR_AMBIGUOUS_2021_2030",
        "target":"year_guard",
        "regex":r"(?<!\d)(202[1-9]|2030)(?!\d)",
        "definition":"2021~2030 先視為年份候選；若同時符合 ticker，必須與第一頁代碼交叉驗證。",
        "priority":"P0"
    }
]

date_period_regex = [
    {"rule_id":"DATE_YYYYMMDD","target":"report_date","regex":r"(20\d{2})[-_./年]?(0[1-9]|1[0-2])[-_./月]?([0-2]\d|3[01])日?","definition":"西元年月日。"},
    {"rule_id":"DATE_ROC_YYYMMDD","target":"report_date","regex":r"(1[0-2]\d)[-_./年]?(0[1-9]|1[0-2])[-_./月]?([0-2]\d|3[01])日?","definition":"民國年月日，解析時 +1911。"},
    {"rule_id":"PERIOD_QUARTER_EN","target":"period_quarter","regex":r"\b(20\d{2})\s*Q([1-4])\b|\bQ([1-4])\s*(20\d{2})\b","definition":"2025Q1 / Q1 2025。"},
    {"rule_id":"PERIOD_QUARTER_ZH","target":"period_quarter","regex":r"(20\d{2})\s*年第?\s*([一二三四1234])\s*季","definition":"中文季度。"},
    {"rule_id":"PERIOD_MONTH","target":"period_month","regex":r"(20\d{2})[-_/年](0?[1-9]|1[0-2])月?","definition":"年月。"},
    {"rule_id":"PERIOD_YEAR","target":"period_year","regex":r"\b(20\d{2})\b","definition":"年份。"}
]

# ==============================================================================
# 2. Rating SSOT
# ==============================================================================
rating_alias = [
    {"canonical":"BUY","alias":"Buy","language":"en","rank":"positive"},
    {"canonical":"BUY","alias":"買進","language":"zh","rank":"positive"},
    {"canonical":"BUY","alias":"增加持股","language":"zh","rank":"positive"},
    {"canonical":"OUTPERFORM","alias":"Outperform","language":"en","rank":"positive"},
    {"canonical":"OUTPERFORM","alias":"優於大盤","language":"zh","rank":"positive"},
    {"canonical":"OVERWEIGHT","alias":"Overweight","language":"en","rank":"positive"},
    {"canonical":"HOLD","alias":"Hold","language":"en","rank":"neutral"},
    {"canonical":"HOLD","alias":"持有","language":"zh","rank":"neutral"},
    {"canonical":"NEUTRAL","alias":"Neutral","language":"en","rank":"neutral"},
    {"canonical":"NEUTRAL","alias":"中立","language":"zh","rank":"neutral"},
    {"canonical":"EQUAL_WEIGHT","alias":"Equal-weight","language":"en","rank":"neutral"},
    {"canonical":"SELL","alias":"Sell","language":"en","rank":"negative"},
    {"canonical":"SELL","alias":"賣出","language":"zh","rank":"negative"},
    {"canonical":"UNDERPERFORM","alias":"Underperform","language":"en","rank":"negative"},
    {"canonical":"UNDERPERFORM","alias":"劣於大盤","language":"zh","rank":"negative"},
    {"canonical":"UNDERWEIGHT","alias":"Underweight","language":"en","rank":"negative"}
]

# ==============================================================================
# 3. Broker Alias SSOT
# ==============================================================================
broker_alias = [
    {"broker_id":"MEGA","canonical":"兆豐","alias":"兆豐","language":"zh","safe_for_text":True},
    {"broker_id":"MEGA","canonical":"兆豐","alias":"Mega Securities","language":"en","safe_for_text":True},
    {"broker_id":"YUANTA","canonical":"元大","alias":"元大","language":"zh","safe_for_text":True},
    {"broker_id":"YUANTA","canonical":"元大","alias":"Yuanta","language":"en","safe_for_text":True},
    {"broker_id":"KGI","canonical":"凱基","alias":"凱基","language":"zh","safe_for_text":True},
    {"broker_id":"KGI","canonical":"凱基","alias":"KGI Securities","language":"en","safe_for_text":True},
    {"broker_id":"CATHAY","canonical":"國泰","alias":"國泰","language":"zh","safe_for_text":True},
    {"broker_id":"CATHAY","canonical":"國泰","alias":"Cathay Securities","language":"en","safe_for_text":True},
    {"broker_id":"FUBON","canonical":"富邦","alias":"富邦","language":"zh","safe_for_text":True},
    {"broker_id":"FUBON","canonical":"富邦","alias":"Fubon","language":"en","safe_for_text":True},
    {"broker_id":"SINOPAC","canonical":"永豐","alias":"永豐","language":"zh","safe_for_text":True},
    {"broker_id":"SINOPAC","canonical":"永豐","alias":"SinoPac","language":"en","safe_for_text":True},
    {"broker_id":"CAPITAL","canonical":"群益","alias":"群益","language":"zh","safe_for_text":True},
    {"broker_id":"CAPITAL","canonical":"群益","alias":"Capital Securities","language":"en","safe_for_text":True},
    {"broker_id":"ESUN","canonical":"玉山","alias":"玉山","language":"zh","safe_for_text":True},
    {"broker_id":"UNIFIED","canonical":"統一","alias":"統一","language":"zh","safe_for_text":True},
    {"broker_id":"CTBC","canonical":"中信","alias":"中信","language":"zh","safe_for_text":True},
    {"broker_id":"FIRST","canonical":"第一金","alias":"第一金","language":"zh","safe_for_text":True},
    {"broker_id":"HUA_NAN","canonical":"華南","alias":"華南","language":"zh","safe_for_text":True},
    {"broker_id":"TAISHIN","canonical":"台新","alias":"台新","language":"zh","safe_for_text":True},
    {"broker_id":"CITI","canonical":"Citi","alias":"Citigroup","language":"en","safe_for_text":True},
    {"broker_id":"CITI","canonical":"Citi","alias":"Citi","language":"en","safe_for_text":False},
    {"broker_id":"GOLDMAN","canonical":"Goldman Sachs","alias":"Goldman Sachs","language":"en","safe_for_text":True},
    {"broker_id":"GOLDMAN","canonical":"Goldman Sachs","alias":"GS","language":"en","safe_for_text":False},
    {"broker_id":"MORGAN_STANLEY","canonical":"Morgan Stanley","alias":"Morgan Stanley","language":"en","safe_for_text":True},
    {"broker_id":"MORGAN_STANLEY","canonical":"Morgan Stanley","alias":"MS","language":"en","safe_for_text":False},
    {"broker_id":"JP_MORGAN","canonical":"J.P. Morgan","alias":"J.P. Morgan","language":"en","safe_for_text":True},
    {"broker_id":"JP_MORGAN","canonical":"J.P. Morgan","alias":"JP Morgan","language":"en","safe_for_text":True},
    {"broker_id":"MACQUARIE","canonical":"Macquarie","alias":"Macquarie","language":"en","safe_for_text":True},
    {"broker_id":"DAIWA","canonical":"Daiwa","alias":"Daiwa","language":"en","safe_for_text":True},
    {"broker_id":"NOMURA","canonical":"Nomura","alias":"Nomura","language":"en","safe_for_text":True},
    {"broker_id":"UBS","canonical":"UBS","alias":"UBS","language":"en","safe_for_text":True},
    {"broker_id":"HSBC","canonical":"HSBC","alias":"HSBC","language":"en","safe_for_text":True},
    {"broker_id":"CLSA","canonical":"CLSA","alias":"CLSA","language":"en","safe_for_text":True},
    {"broker_id":"JEFFERIES","canonical":"Jefferies","alias":"Jefferies","language":"en","safe_for_text":True}
]

# ==============================================================================
# 4. BasicInfo / Output Definition SSOT
# ==============================================================================
basic_info_fields = [
    {"field":"report_id","definition":"報告唯一 ID；由 file_id/path/ticker/report_date/broker stable hash 產生。","required":"true"},
    {"field":"file_id","definition":"文件唯一 ID；由檔案 hash / path / filename 產生。","required":"true"},
    {"field":"ticker","definition":"台股四碼代號；第一碼不可為 0。","required":"true"},
    {"field":"tw_ticker","definition":"同 ticker，標準化台股四碼。","required":"true"},
    {"field":"tw_yfinance_ticker","definition":"上市為 2330.TW，上櫃為 1234.TWO。","required":"false"},
    {"field":"tw_bloomberg_ticker","definition":"2330 TT 形式。","required":"false"},
    {"field":"company_name","definition":"公司中文或英文名稱。","required":"false"},
    {"field":"broker","definition":"券商 canonical name。","required":"false"},
    {"field":"analyst","definition":"分析師。","required":"false"},
    {"field":"rating","definition":"投資評等 canonical。","required":"false"},
    {"field":"target_price","definition":"目標價。","required":"false"},
    {"field":"report_date","definition":"報告日期。","required":"false"},
    {"field":"period","definition":"財務預估或資料期間。","required":"false"},
    {"field":"source_path","definition":"原始 PDF 路徑。","required":"true"}
]

# ==============================================================================
# 5. Financial Account Alias SSOT
# ==============================================================================
fin_alias = [
    # Income statement
    {"statement":"IS","canonical":"revenue","alias":"營業收入","operator_group":"sales"},
    {"statement":"IS","canonical":"revenue","alias":"Revenue","operator_group":"sales"},
    {"statement":"IS","canonical":"net_sales","alias":"銷貨收入淨額","operator_group":"sales"},
    {"statement":"IS","canonical":"gross_profit","alias":"營業毛利","operator_group":"profit"},
    {"statement":"IS","canonical":"gross_profit","alias":"Gross Profit","operator_group":"profit"},
    {"statement":"IS","canonical":"operating_expense","alias":"營業費用","operator_group":"expense"},
    {"statement":"IS","canonical":"selling_expense","alias":"推銷費用","operator_group":"expense"},
    {"statement":"IS","canonical":"admin_expense","alias":"管理費用","operator_group":"expense"},
    {"statement":"IS","canonical":"r_and_d_expense","alias":"研發費用","operator_group":"expense"},
    {"statement":"IS","canonical":"operating_income","alias":"營業利益","operator_group":"profit"},
    {"statement":"IS","canonical":"operating_income","alias":"Operating Income","operator_group":"profit"},
    {"statement":"IS","canonical":"pretax_income","alias":"稅前淨利","operator_group":"profit"},
    {"statement":"IS","canonical":"tax_expense","alias":"所得稅費用","operator_group":"expense"},
    {"statement":"IS","canonical":"net_income","alias":"本期淨利","operator_group":"profit"},
    {"statement":"IS","canonical":"net_income","alias":"Net Income","operator_group":"profit"},
    {"statement":"IS","canonical":"eps","alias":"每股盈餘","operator_group":"per_share"},
    {"statement":"IS","canonical":"eps","alias":"EPS","operator_group":"per_share"},
    # Balance sheet
    {"statement":"BS","canonical":"cash_and_equivalents","alias":"現金及約當現金","operator_group":"asset"},
    {"statement":"BS","canonical":"accounts_receivable","alias":"應收帳款","operator_group":"asset"},
    {"statement":"BS","canonical":"inventory","alias":"存貨","operator_group":"asset"},
    {"statement":"BS","canonical":"current_assets","alias":"流動資產","operator_group":"asset"},
    {"statement":"BS","canonical":"ppe","alias":"不動產廠房及設備","operator_group":"asset"},
    {"statement":"BS","canonical":"total_assets","alias":"資產總計","operator_group":"asset"},
    {"statement":"BS","canonical":"accounts_payable","alias":"應付帳款","operator_group":"liability"},
    {"statement":"BS","canonical":"current_liabilities","alias":"流動負債","operator_group":"liability"},
    {"statement":"BS","canonical":"long_term_debt","alias":"長期借款","operator_group":"liability"},
    {"statement":"BS","canonical":"total_liabilities","alias":"負債總計","operator_group":"liability"},
    {"statement":"BS","canonical":"share_capital","alias":"股本","operator_group":"equity"},
    {"statement":"BS","canonical":"retained_earnings","alias":"保留盈餘","operator_group":"equity"},
    {"statement":"BS","canonical":"total_equity","alias":"權益總計","operator_group":"equity"},
    # Cash flow
    {"statement":"CF","canonical":"cfo","alias":"營業活動現金流量","operator_group":"cashflow"},
    {"statement":"CF","canonical":"capex","alias":"資本支出","operator_group":"cashflow"},
    {"statement":"CF","canonical":"cfi","alias":"投資活動現金流量","operator_group":"cashflow"},
    {"statement":"CF","canonical":"cff","alias":"籌資活動現金流量","operator_group":"cashflow"},
    {"statement":"CF","canonical":"fcf","alias":"自由現金流","operator_group":"cashflow"},
    # Ratios / analysis
    {"statement":"RATIO","canonical":"gross_margin","alias":"毛利率","operator_group":"margin"},
    {"statement":"RATIO","canonical":"operating_margin","alias":"營益率","operator_group":"margin"},
    {"statement":"RATIO","canonical":"net_margin","alias":"淨利率","operator_group":"margin"},
    {"statement":"RATIO","canonical":"roe","alias":"ROE","operator_group":"return"},
    {"statement":"RATIO","canonical":"roa","alias":"ROA","operator_group":"return"},
    {"statement":"RATIO","canonical":"debt_ratio","alias":"負債比率","operator_group":"leverage"},
    {"statement":"RATIO","canonical":"current_ratio","alias":"流動比率","operator_group":"liquidity"}
]

# ==============================================================================
# 6. Financial Validation Rules
# ==============================================================================
validation_rules = [
    {"rule_id":"IS_GROSS_PROFIT","formula":"gross_profit = revenue - cost_of_goods_sold","method":"subtraction","severity":"HIGH","tolerance":"abs<=1 or pct<=0.5%"},
    {"rule_id":"IS_OPERATING_INCOME","formula":"operating_income = gross_profit - operating_expense","method":"subtraction","severity":"HIGH","tolerance":"abs<=1 or pct<=0.5%"},
    {"rule_id":"IS_PRETAX_INCOME","formula":"pretax_income = operating_income + non_operating_income_expense","method":"addition","severity":"MEDIUM","tolerance":"abs<=1 or pct<=0.5%"},
    {"rule_id":"IS_NET_INCOME","formula":"net_income = pretax_income - tax_expense","method":"subtraction","severity":"HIGH","tolerance":"abs<=1 or pct<=0.5%"},
    {"rule_id":"BS_BALANCE","formula":"total_assets = total_liabilities + total_equity","method":"addition","severity":"HIGH","tolerance":"abs<=1 or pct<=0.5%"},
    {"rule_id":"CF_FCF","formula":"fcf = cfo - capex","method":"subtraction","severity":"MEDIUM","tolerance":"abs<=1 or pct<=1.0%"},
    {"rule_id":"RATIO_GROSS_MARGIN","formula":"gross_margin = gross_profit / revenue","method":"division","severity":"MEDIUM","tolerance":"abs<=0.005"},
    {"rule_id":"RATIO_OPERATING_MARGIN","formula":"operating_margin = operating_income / revenue","method":"division","severity":"MEDIUM","tolerance":"abs<=0.005"},
    {"rule_id":"RATIO_NET_MARGIN","formula":"net_margin = net_income / revenue","method":"division","severity":"MEDIUM","tolerance":"abs<=0.005"},
    {"rule_id":"RATIO_ROE","formula":"roe = net_income / average_total_equity","method":"division","severity":"MEDIUM","tolerance":"abs<=0.01"},
    {"rule_id":"RATIO_ROA","formula":"roa = net_income / average_total_assets","method":"division","severity":"MEDIUM","tolerance":"abs<=0.01"},
    {"rule_id":"RATIO_CURRENT_RATIO","formula":"current_ratio = current_assets / current_liabilities","method":"division","severity":"LOW","tolerance":"abs<=0.05"},
    {"rule_id":"RATIO_DEBT_RATIO","formula":"debt_ratio = total_liabilities / total_assets","method":"division","severity":"LOW","tolerance":"abs<=0.01"},
    {"rule_id":"TICKER_CROSS_CHECK","formula":"filename_tw_ticker[0:4] = page_info_tw_ticker[0:4] = bloomberg[0:4] = yfinance[0:4]","method":"string_cross_check","severity":"HIGH","tolerance":"exact"},
    {"rule_id":"YEAR_GUARD","formula":"if token in 2021..2030 then require page-code confirmation before using as tw_ticker","method":"guardrail","severity":"HIGH","tolerance":"exact"}
]

# ==============================================================================
# 7. Source Inventory and SSOT Table Outputs
# ==============================================================================
source_inventory = []
for s in sources:
    name = s.get("name","")
    p = s.get("path","")
    source_inventory.append({
        "source_id": sha12(p),
        "name": name,
        "path": p,
        "class_hint": ",".join([x for x in ["SSOT","Broker","Alias","Financial","Rule","Regex","Ticker","Rating","Date","Period","BasicInfo","Quality"] if x.lower() in name.lower()]),
        "last_write_time": s.get("last_write_time",""),
        "length": s.get("length","")
    })

tables = {
    "VRN_TickerRegexSSOT": ticker_regex,
    "VRN_DatePeriodRegexSSOT": date_period_regex,
    "VRN_RatingAliasSSOT": rating_alias,
    "VRN_BrokerAliasSSOT": broker_alias,
    "VRN_BasicInfoDefinitionSSOT": basic_info_fields,
    "VRN_FinancialAccountAliasSSOT": fin_alias,
    "VRN_FinancialValidationRulesSSOT": validation_rules,
    "VRN_SSOT_SourceInventory": source_inventory
}

parquet_paths = {}
json_paths = {}
for name, rows in tables.items():
    pq_path = os.path.join(parquet_dir, f"{name}_v029SSOT1B.parquet")
    js_path = os.path.join(json_dir, f"{name}_v029SSOT1B.json")
    rows_to_parquet(pq_path, rows)
    write_json(js_path, rows)
    parquet_paths[name] = pq_path
    json_paths[name] = js_path

active_stage_pointer_candidate = {
    "generated_at": now(),
    "status": "VRN_ACTIVE_STAGE_POINTER_CANDIDATE_READY",
    "risk": "MEDIUM",
    "main_format": "parquet",
    "basic_info_candidate": latest_basic,
    "report_text_candidate": latest_text,
    "parquet_manifest_1c3": latest_manifest,
    "broker_runtime_1c41": latest_broker_runtime,
    "ssot_parquet": parquet_paths,
    "ssot_json": json_paths,
    "rules": {
        "tw_ticker_regex": "(?<!\\d)([1-9]\\d{3})(?!\\d)",
        "tw_yfinance_ticker": "{TW_TICKER}.TW or {TW_TICKER}.TWO",
        "tw_bloomberg_ticker": "{TW_TICKER} TT",
        "filename_tokenizer": "split by Chinese/English punctuation and spaces; continuous Chinese/English/digit tokens",
        "year_guard": "2021~2030 must not be accepted as ticker unless confirmed by page code cross-check"
    },
    "promotion_allowed": False,
    "canonical_allowed": False,
    "next_step": "Run SSOT verifier; then VRN 1D table extraction staging."
}
pointer_candidate_json = os.path.join(json_dir, "VRN_ACTIVE_STAGE_POINTER_CANDIDATE_v029SSOT1B.json")
write_json(pointer_candidate_json, active_stage_pointer_candidate)

unified_ssot = {
    "generated_at": now(),
    "status": "VRN_UNIFIED_SSOT_CANDIDATE_READY",
    "version": "v029.SSOT.1B",
    "parquet_ssot": parquet_paths,
    "json_control": json_paths,
    "active_stage_pointer_candidate": pointer_candidate_json,
    "latest_basic": latest_basic,
    "latest_text": latest_text,
    "definition": {
        "json_role": "control plane / manifest / runtime / audit summary",
        "parquet_role": "main SSOT payload",
        "duckdb_role": "serving layer, rebuildable from parquet"
    }
}
unified_json = os.path.join(json_dir, "VIA_UnifiedInput_SSOT_v029SSOT1B.json")
write_json(unified_json, unified_ssot)

runtime = {
    "generated_at": now(),
    "status": "VRN_UNIFIED_SSOT_BUILT_READY",
    "risk": "LOW",
    "ssot_table_count": len(tables),
    "ticker_regex_count": len(ticker_regex),
    "date_regex_count": len(date_period_regex),
    "rating_alias_count": len(rating_alias),
    "broker_alias_count": len(broker_alias),
    "basic_info_field_count": len(basic_info_fields),
    "financial_alias_count": len(fin_alias),
    "validation_rule_count": len(validation_rules),
    "source_inventory_count": len(source_inventory),
    "parquet_paths": parquet_paths,
    "json_paths": json_paths,
    "pointer_candidate_json": pointer_candidate_json,
    "unified_ssot_json": unified_json
}
write_json(runtime_json, runtime)
print(json.dumps(runtime, ensure_ascii=False))