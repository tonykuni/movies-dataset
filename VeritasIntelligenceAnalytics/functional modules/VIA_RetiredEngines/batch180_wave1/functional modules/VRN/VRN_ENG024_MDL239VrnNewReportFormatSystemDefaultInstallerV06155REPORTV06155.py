# -*- coding: utf-8 -*-
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(全引擎導入令 2026-08-18;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # accel_map/fetch/pip_install/run_fast
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

import ast
import copy
import hashlib
import html
import json
import py_compile
import re
import shutil
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any


VERSION = "VRN_NEW_REPORT_FORMAT_SYSTEM_DEFAULT_INSTALLER_V06155"


def def_now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def def_sha256(path: Path) -> str:
    if not path.exists():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def def_backup_if_exists(path: Path, tag: str) -> str:
    if not path.exists():
        return ""
    backup = path.with_name(path.name + f".bak_{tag}_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    shutil.copy2(path, backup)
    return str(backup)


def def_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def def_write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def def_light(sev: str) -> str:
    s = str(sev or "").upper()
    if s in ["OK", "PASS", "YES", "READY", "INSTALLED"]:
        return "🟢 INPUT 🟢 DB 🟢 TRUST"
    if s in ["WARN", "PLAN", "REVIEW"]:
        return "🟢 INPUT 🟡 DB 🟡 TRUST"
    return "🔴 INPUT 🔴 DB 🔴 TRUST"


def def_gate_module_code() -> str:
    return r'''# -*- coding: utf-8 -*-
"""
VIS_VRN_NewReportCompatibilityGate_v01.py

def Role:
    新報告格式 / 新券商 compatibility gate。
    用於判斷新報告是否可沿用既有 VRN pipeline，或需要新增 broker adapter / table adapter / OCR isolated flow。

def Safety:
    - No OCR
    - No DB write
    - No canonical mutation
    - No SSOT mutation
    - Staging decision only
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any


VERSION = "VIS_VRN_NewReportCompatibilityGate_v01"


def def_clean_text(x: Any) -> str:
    s = "" if x is None else str(x)
    s = s.replace("\u3000", " ")
    return re.sub(r"\s+", " ", s).strip()


def def_norm(x: Any) -> str:
    return re.sub(r"[\s_\-\/\(\)（）\[\]【】{}:：,，.。]+", "", str(x or "").lower())


def def_safe_int(x: Any, default: int = 0) -> int:
    try:
        return int(float(str(x).replace(",", "").replace("%", "").strip()))
    except Exception:
        return default


@dataclass
class CompatibilityDecision:
    filename: str = ""
    broker_raw: str = ""
    broker_abbrev: str = ""
    ticker: str = ""
    report_date: str = ""
    route: str = "MANUAL_REVIEW_ONLY"
    compatibility_score: int = 0
    broker_known: bool = False
    report_identity_ok: bool = False
    basicinfo_ok: bool = False
    table_locator_ok: bool = False
    financial_validation_ok: bool = False
    needs_broker_adapter: bool = False
    needs_table_adapter: bool = False
    needs_ocr_isolated: bool = False
    needs_ssot_alias_candidate: bool = False
    no_mutation: bool = True
    reason: str = ""


def def_load_adapter_registry(path: str | Path) -> dict:
    p = Path(path)
    if not p.exists():
        return {"brokers": {}, "global_rules": {}}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {"brokers": {}, "global_rules": {}, "load_error": str(p)}


def def_detect_broker_from_filename(filename: str, registry: dict) -> tuple[str, str, bool]:
    fn = def_norm(filename)
    brokers = registry.get("brokers", {})
    for abbrev, cfg in brokers.items():
        aliases = cfg.get("broker_alias", [])
        for a in aliases:
            if def_norm(a) and def_norm(a) in fn:
                return a, abbrev, True
    return "", "", False


def def_score_report_identity(payload: dict) -> tuple[bool, int, list[str]]:
    reason = []
    score = 0

    ticker = def_clean_text(payload.get("ticker"))
    report_date = def_clean_text(payload.get("report_date") or payload.get("Report date"))

    if re.fullmatch(r"[1-9]\d{3}", ticker or "") and not re.fullmatch(r"202[1-9]|2030", ticker or ""):
        score += 25
    else:
        reason.append("ticker missing or invalid")

    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", report_date or ""):
        score += 25
    else:
        reason.append("report date missing or invalid")

    return score >= 40, score, reason


def def_score_basicinfo(payload: dict) -> tuple[bool, int, list[str]]:
    reason = []
    score = 0

    analyst = def_clean_text(payload.get("analyst"))
    rating = def_clean_text(payload.get("rating"))
    target_price = def_clean_text(payload.get("target_price") or payload.get("target price"))
    valuation_method = def_clean_text(payload.get("valuation_method") or payload.get("valuation method"))

    if analyst and analyst not in {"聯絡方式", "研究員", "analyst"}:
        score += 20
    else:
        reason.append("analyst missing or contact-zone contaminated")

    if rating:
        score += 15
    else:
        reason.append("rating missing")

    if target_price or "not rated" in rating.lower() or "未評等" in rating:
        score += 20
    else:
        reason.append("target price missing and not optional")

    if valuation_method:
        score += 10
    else:
        reason.append("valuation method missing")

    return score >= 45, score, reason


def def_score_table_locator(payload: dict) -> tuple[bool, int, list[str]]:
    reason = []
    score = 0

    pages_with_tables = def_safe_int(payload.get("pages_with_tables"))
    table_candidate_rows = def_safe_int(payload.get("table_candidate_rows"))
    page_review_queue = def_safe_int(payload.get("page_review_queue"))

    if pages_with_tables > 0:
        score += 25
    else:
        reason.append("no pages with tables")

    if table_candidate_rows > 0:
        score += 25
    else:
        reason.append("no table candidate rows")

    if page_review_queue == 0:
        score += 10
    else:
        reason.append("page review queue not empty")

    return score >= 40, score, reason


def def_score_financial_validation(payload: dict) -> tuple[bool, int, list[str]]:
    reason = []
    score = 0

    recon_ready = def_safe_int(payload.get("recon_ready"))
    formula_ready = def_safe_int(payload.get("formula_ready_clean_rows"))
    context_required = def_safe_int(payload.get("formula_context_required_rows"))
    year_quarantine = def_safe_int(payload.get("year_quarantine_rows"))

    if recon_ready > 0:
        score += 25
    else:
        reason.append("no reconstruction-ready table")

    if formula_ready > 0:
        score += 10

    if context_required == 0:
        score += 20
    else:
        reason.append("formula context still required")

    if year_quarantine == 0:
        score += 10
    else:
        reason.append("year quarantine exists")

    return score >= 35, score, reason


def def_decide_new_report(payload: dict, registry: dict) -> dict:
    filename = def_clean_text(payload.get("filename"))
    broker_raw = def_clean_text(payload.get("broker") or payload.get("broker_raw"))

    detected_raw, detected_abbrev, broker_known = def_detect_broker_from_filename(filename + " " + broker_raw, registry)

    identity_ok, identity_score, identity_reason = def_score_report_identity(payload)
    basic_ok, basic_score, basic_reason = def_score_basicinfo(payload)
    table_ok, table_score, table_reason = def_score_table_locator(payload)
    fin_ok, fin_score, fin_reason = def_score_financial_validation(payload)

    score = identity_score + basic_score + table_score + fin_score
    reasons = []
    reasons.extend(identity_reason)
    reasons.extend(basic_reason)
    reasons.extend(table_reason)
    reasons.extend(fin_reason)

    needs_broker_adapter = not broker_known
    needs_table_adapter = table_ok and not fin_ok
    needs_ocr = bool(payload.get("text_layer_weak")) and not table_ok
    needs_ssot_alias = bool(payload.get("ssot_alias_candidate")) and not needs_table_adapter

    if identity_ok and basic_ok and table_ok and fin_ok and broker_known:
        route = "PASS_FULLY_EXTRACTED"
    elif needs_broker_adapter:
        route = "BROKER_UNKNOWN_NEEDS_ADAPTER"
    elif not basic_ok:
        route = "PARTIAL_BASICINFO_NEEDS_ADAPTER"
    elif table_ok and not fin_ok:
        route = "TABLE_RECON_REQUIRED"
    elif needs_ocr:
        route = "OCR_REQUIRED_ISOLATED"
    elif needs_ssot_alias:
        route = "SSOT_ALIAS_CANDIDATE"
    else:
        route = "PARTIAL_NEEDS_ADAPTER"

    decision = CompatibilityDecision(
        filename=filename,
        broker_raw=broker_raw or detected_raw,
        broker_abbrev=detected_abbrev,
        ticker=def_clean_text(payload.get("ticker")),
        report_date=def_clean_text(payload.get("report_date") or payload.get("Report date")),
        route=route,
        compatibility_score=score,
        broker_known=broker_known,
        report_identity_ok=identity_ok,
        basicinfo_ok=basic_ok,
        table_locator_ok=table_ok,
        financial_validation_ok=fin_ok,
        needs_broker_adapter=needs_broker_adapter,
        needs_table_adapter=needs_table_adapter,
        needs_ocr_isolated=needs_ocr,
        needs_ssot_alias_candidate=needs_ssot_alias,
        no_mutation=True,
        reason=" | ".join(reasons) if reasons else "all gates passed",
    )
    return asdict(decision)


def def_batch_decide(payloads: list[dict], registry_path: str | Path) -> list[dict]:
    registry = def_load_adapter_registry(registry_path)
    return [def_decide_new_report(p, registry) for p in payloads]


def def_required_next_action(decision: dict) -> str:
    route = decision.get("route", "")
    if route == "PASS_FULLY_EXTRACTED":
        return "ALLOW_STAGING_TO_FINAL_REVIEW"
    if route == "BROKER_UNKNOWN_NEEDS_ADAPTER":
        return "CREATE_BROKER_ADAPTER_STAGING_ONLY"
    if route == "PARTIAL_BASICINFO_NEEDS_ADAPTER":
        return "CREATE_BASICINFO_ZONE_ADAPTER"
    if route == "TABLE_RECON_REQUIRED":
        return "RUN_TARGETED_TABLE_RECON_VALIDATION_DRYRUN"
    if route == "OCR_REQUIRED_ISOLATED":
        return "RUN_ISOLATED_PAGE_OCR_PREFLIGHT_ONLY"
    if route == "SSOT_ALIAS_CANDIDATE":
        return "CREATE_ADD_ONLY_SSOT_ALIAS_CANDIDATE"
    return "MANUAL_REVIEW_ONLY"


if __name__ == "__main__":
    print(json.dumps({
        "version": VERSION,
        "role": "new report format compatibility gate",
        "safety": "staging only / no mutation",
    }, ensure_ascii=False, indent=2))
'''


def def_registry_obj() -> dict:
    return {
        "version": "VIS_VRN_AdapterRegistry_v01",
        "generated_at": def_now(),
        "policy": {
            "mode": "ADD_ONLY_REGISTRY",
            "no_canonical_mutation": True,
            "no_ssot_mutation": True,
            "no_db_write": True,
            "no_ocr_by_default": True,
            "new_report_must_pass_compatibility_gate": True,
            "unknown_broker_never_enters_final_matrix": True,
            "target_price_must_come_from_report_not_yfinance": True,
            "yfinance_consensus_is_market_reference_not_report_target_price": True
        },
        "global_rules": {
            "ticker_regex": "^(?!202[1-9])(?!2030)[1-9]\\d{3}$",
            "report_year_window": "report_year_minus_3_to_plus_3",
            "filename_tokenization": [
                "split continuous digits",
                "split continuous English",
                "split continuous Chinese",
                "trim left right whitespace",
                "long numeric token is date candidate",
                "four-digit numeric token is ticker candidate"
            ],
            "date_rules": [
                "YYYYMMDD",
                "ROC YYYMMDD",
                "omitted 20 YYMMDD",
                "filename date priority then first-page zone cross-check"
            ],
            "analyst_rules": [
                "Chinese analyst name normally 2-4 Chinese characters",
                "English analyst name normally two capitalized words",
                "exclude 聯絡方式 / 研究員 / analyst title as name",
                "email left side may contain English analyst name",
                "email right side may contain broker domain",
                "phone starts with +886 or (02)",
                "analyst usually above email/phone zone"
            ],
            "target_price_rules": [
                "target price must be separated from previous target price",
                "do not fill report target price from YFinance consensus",
                "not rated / NR may allow target price optional",
                "year-like values must not be target price unless comma/price pattern is clear"
            ],
            "financial_rules": [
                "valuation tables are excluded from FinancialData canonical transform",
                "diluted EPS is preferred for all valuation calculations",
                "if EPS type is unclear, smaller EPS is treated as diluted EPS",
                "historical official data + add/sub formula + division formula increase confidence",
                "table must pass row/column/header/body/source-note validation before DB transform"
            ],
            "table_capture_zone": [
                "table title",
                "table number/caption",
                "3 rows above",
                "full header rows",
                "full body",
                "source note",
                "2 rows below"
            ]
        },
        "brokers": {
            "HuaNan": {
                "broker_alias": ["華南投顧", "華南", "HuaNan", "Hua Nan", "Hua Nan Securities"],
                "broker_abbrev": "HuaNan",
                "analyst_zone": "email_phone_zone_above_right_of_research_title",
                "memo_has_analyst": False,
                "target_price_zone": "top_left_right_and_title_body",
                "table_style": "wide_year_columns",
                "special_notes": [
                    "研究員右邊或上方是真正 analyst",
                    "聯絡方式不是 analyst",
                    "訪談報告或 memo 通常沒有 analyst"
                ]
            },
            "GS": {
                "broker_alias": ["GS", "Goldman", "Goldman Sachs"],
                "broker_abbrev": "GS",
                "target_price_optional_if_not_disclosed": True,
                "table_style": "global_broker_pdf_standard",
                "special_notes": ["Do not use YFinance target price as report target price"]
            },
            "JPM": {
                "broker_alias": ["JP", "JPM", "JP Morgan", "J.P. Morgan", "JPMorgan"],
                "broker_abbrev": "JPM",
                "table_style": "global_broker_pdf_standard"
            },
            "MS": {
                "broker_alias": ["MS", "Morgan Stanley"],
                "broker_abbrev": "MS",
                "table_style": "global_broker_pdf_standard"
            },
            "Daiwa": {
                "broker_alias": ["Daiwa", "大和"],
                "broker_abbrev": "Daiwa",
                "table_style": "global_broker_pdf_standard",
                "special_notes": ["Comma price like 2,009.00 is price, not year"]
            },
            "Citi": {
                "broker_alias": ["Citi", "Citigroup"],
                "broker_abbrev": "Citi",
                "table_style": "global_broker_pdf_standard"
            },
            "CTBC": {
                "broker_alias": ["CTBC", "中信", "中國信託", "中國信託投顧"],
                "broker_abbrev": "CTBC",
                "table_style": "tw_broker_pdf_standard"
            },
            "Mega": {
                "broker_alias": ["Mega", "兆豐", "兆豐投顧"],
                "broker_abbrev": "Mega",
                "table_style": "tw_broker_pdf_standard"
            },
            "Cathay": {
                "broker_alias": ["Cathay", "國泰", "國泰證期", "國泰證期研究部"],
                "broker_abbrev": "Cathay",
                "table_style": "tw_broker_pdf_standard"
            },
            "CLST": {
                "broker_alias": ["CLST", "CLSA", "里昂"],
                "broker_abbrev": "CLST",
                "table_style": "global_broker_pdf_standard"
            },
            "FFHC": {
                "broker_alias": ["第一金", "First Financial Holding", "FFHC"],
                "broker_abbrev": "FFHC",
                "table_style": "tw_broker_pdf_standard"
            },
            "PSC": {
                "broker_alias": ["統一", "統一證券", "President Securities", "PSC"],
                "broker_abbrev": "PSC",
                "table_style": "tw_broker_pdf_standard"
            },
            "CSC": {
                "broker_alias": ["群益", "群益金鼎", "群益金鼎證券", "Capital Securities", "CSC"],
                "broker_abbrev": "CSC",
                "table_style": "tw_broker_pdf_standard"
            }
        },
        "adapter_routes": {
            "PASS_FULLY_EXTRACTED": {
                "allow_final_matrix": True,
                "action": "ALLOW_STAGING_TO_FINAL_REVIEW"
            },
            "BROKER_UNKNOWN_NEEDS_ADAPTER": {
                "allow_final_matrix": False,
                "action": "CREATE_BROKER_ADAPTER_STAGING_ONLY"
            },
            "PARTIAL_BASICINFO_NEEDS_ADAPTER": {
                "allow_final_matrix": False,
                "action": "CREATE_BASICINFO_ZONE_ADAPTER"
            },
            "TABLE_RECON_REQUIRED": {
                "allow_final_matrix": False,
                "action": "RUN_TARGETED_TABLE_RECON_VALIDATION_DRYRUN"
            },
            "OCR_REQUIRED_ISOLATED": {
                "allow_final_matrix": False,
                "action": "RUN_ISOLATED_PAGE_OCR_PREFLIGHT_ONLY"
            },
            "SSOT_ALIAS_CANDIDATE": {
                "allow_final_matrix": False,
                "action": "CREATE_ADD_ONLY_SSOT_ALIAS_CANDIDATE"
            },
            "MANUAL_REVIEW_ONLY": {
                "allow_final_matrix": False,
                "action": "MANUAL_REVIEW_ONLY"
            }
        }
    }


def def_playbook_text() -> str:
    return """# VIS_VRN_NewReport_Format_Playbook_v01

def 目的
將新報告格式 / 新券商增加變成系統預設治理流程，不再每次臨時想方法。

def 核心原則
- 新報告先進 Compatibility Gate，不直接進正式 canonical。
- 新券商先進 Adapter Registry，不改主流程。
- 新格式先做 staging / dry run / report，不寫 DB。
- BasicInfo 成功不代表 FinancialData 成功。
- FinancialData 成功必須經過 table reconstruction validation。
- Target Price 只能來自報告，不可用 YFinance consensus 假填。
- YFinance 是 market reference，不是 report evidence。
- SSOT alias 只增不減，且 candidate groups 必須大於 0 才可考慮 append-only patch。
- OCR 只在 text-layer 失敗且高優先頁面才可 isolated preflight。

def 新報告進入流程
1. File Intake
   - PDF / Word / Image 轉高品質 PDF，DPI=400。
   - 先保留原始檔，不刪除。

2. Compatibility Gate
   - filename tokenization
   - ticker / report date / broker / analyst / target price / rating
   - table locator
   - financial validation
   - mutation safety check

3. Decision Route
   - PASS_FULLY_EXTRACTED
   - BROKER_UNKNOWN_NEEDS_ADAPTER
   - PARTIAL_BASICINFO_NEEDS_ADAPTER
   - TABLE_RECON_REQUIRED
   - OCR_REQUIRED_ISOLATED
   - SSOT_ALIAS_CANDIDATE
   - MANUAL_REVIEW_ONLY

4. Adapter Registry
   - broker alias
   - analyst zone
   - target price zone
   - table style
   - memo / visit behavior
   - special exceptions

5. Table Validation
   - table title
   - table number/caption
   - 3 rows above
   - full header rows
   - full body
   - source note
   - 2 rows below
   - row count / column count / header text / numeric body / merged cell fill

6. FinancialData Validation
   - report year ±3
   - historical official data
   - add/sub formula
   - division formula
   - diluted EPS priority
   - valuation table excluded from FinancialData canonical

def 新券商加入規則
- 只新增 registry broker block。
- 不修改既有 broker adapter。
- 不修改 canonical extraction main flow。
- 新 broker 先 staging only，通過 compatibility scorecard 後再允許 final matrix。

def UI 預設頁面
- P01 Executive Seal Dashboard
- P02 BasicInfo Final Matrix
- P03 FinancialData Matrix
- P04 Repair Queue Control
- P05 Targeted Table Dry Run
- P06 New Report Compatibility Gate
- P07 Broker Adapter Registry
- P08 Extraction Skill Pack / Learning Queue

def 完成標準
新報告能回答：
- 哪裡成功？
- 哪裡失敗？
- 是 broker 問題、analyst zone 問題、target price 問題、table 問題、financial validation 問題、還是 OCR 問題？
- 是否需要 adapter？
- 是否可 append-only 更新？
- 是否禁止進 final matrix？
"""


def def_write_html_report(path: Path, rows: list[dict], registry: dict) -> None:
    css = """
body{margin:0;background:#07111f;color:#eef6ff;font-family:Segoe UI,'Microsoft JhengHei',Arial,sans-serif;font-size:12px}
header{padding:26px 34px;background:#0d1b2f;border-bottom:1px solid #1f3557}
h1{margin:0;font-size:25px}.sub{color:#9fb3c8;margin-top:8px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(185px,1fr));gap:14px;padding:22px 34px}
.kpi{background:#0d1b2f;border:1px solid #1f3557;border-radius:18px;padding:16px}
.v{font-size:25px;font-weight:800}.k{color:#9fb3c8}
main{padding:0 34px 34px}
.card{background:#0d1b2f;border:1px solid #1f3557;border-radius:18px;padding:18px;margin:18px 0}
.table-wrap{overflow:auto;max-height:76vh;border:1px solid #1f3557;border-radius:14px}
table{border-collapse:collapse;min-width:100%;width:max-content}
th{position:sticky;top:0;background:#132541;padding:10px;text-align:center}
td{padding:8px 10px;border-bottom:1px solid rgba(255,255,255,.08);vertical-align:top;max-width:980px;white-space:normal;word-break:break-word}
td.left{text-align:left}td.center{text-align:center}
"""
    fields = []
    for r in rows:
        for k in r:
            if k not in fields:
                fields.append(k)

    th = "".join(f"<th>{html.escape(str(k))}</th>" for k in fields)
    trs = []
    for r in rows:
        tds = []
        for k in fields:
            v = "" if r.get(k) is None else str(r.get(k, ""))
            cls = "left" if any(x in k.lower() for x in ["file", "path", "error", "recommendation"]) else "center"
            tds.append(f"<td class='{cls}'>{html.escape(v)}</td>")
        trs.append("<tr>" + "".join(tds) + "</tr>")

    cards = {
        "Final": "PASS" if all(r.get("Severity") == "OK" for r in rows) else "REVIEW",
        "Installed Assets": len(rows),
        "Broker Adapters": len(registry.get("brokers", {})),
        "Routes": len(registry.get("adapter_routes", {})),
        "No Canonical": "YES",
        "No SSOT": "YES",
        "No DB": "YES",
        "No OCR": "YES"
    }
    card_html = "".join(f"<div class='kpi'><div class='v'>{html.escape(str(v))}</div><div class='k'>{html.escape(str(k))}</div></div>" for k, v in cards.items())

    doc = f"""<!doctype html><html><head><meta charset="utf-8"><title>VRN New Report Format System Default Installer v06155</title><style>{css}</style></head>
<body><header><h1>VRN · New Report Format System Default Installer v0.6.15.5</h1>
<div class="sub">Compatibility Gate · Adapter Registry · Format Playbook · no mutation</div></header>
<div class="grid">{card_html}</div>
<main><section class="card"><h2>01 Install Matrix</h2><div class="table-wrap"><table><thead><tr>{th}</tr></thead><tbody>{''.join(trs)}</tbody></table></div></section>
<section class="card"><h2>02 Default Strategy</h2>
<p>新報告先通過 Compatibility Gate，再由 Adapter Registry 決定是否可進 final matrix。未知券商、新版格式、表格錯位、OCR 需求全部進 staging queue，不污染主流程。</p>
</section></main></body></html>"""
    path.write_text(doc, encoding="utf-8")


def def_main() -> None:
    if len(sys.argv) < 6:
        raise SystemExit("usage: py <gate_module> <registry_json> <playbook_md> <run_dir> <tag>")

    gate_module = Path(sys.argv[1])
    registry_json = Path(sys.argv[2])
    playbook_md = Path(sys.argv[3])
    run_dir = Path(sys.argv[4])
    tag = sys.argv[5]

    run_dir.mkdir(parents=True, exist_ok=True)

    rows = []

    assets = [
        ("NewReportCompatibilityGate", gate_module, def_gate_module_code()),
        ("AdapterRegistry", registry_json, json.dumps(def_registry_obj(), ensure_ascii=False, indent=2)),
        ("NewReportFormatPlaybook", playbook_md, def_playbook_text()),
    ]

    for name, path, text in assets:
        before_hash = def_sha256(path)
        backup = def_backup_if_exists(path, tag)
        def_write_text(path, text)
        after_hash = def_sha256(path)

        compile_ok = ""
        ast_ok = ""
        error = ""

        if path.suffix.lower() == ".py":
            try:
                ast.parse(path.read_text(encoding="utf-8"))
                ast_ok = "YES"
            except Exception as e:
                ast_ok = "NO"
                error += f"AST:{type(e).__name__}:{e}; "
            try:
                py_compile.compile(str(path), doraise=True)
                compile_ok = "YES"
            except Exception as e:
                compile_ok = "NO"
                error += f"COMPILE:{type(e).__name__}:{e}; "
        else:
            ast_ok = "N/A"
            compile_ok = "N/A"

        rows.append({
            "Status Lights": def_light("OK" if not error else "ERR"),
            "Asset": name,
            "Path": str(path),
            "Backup": backup,
            "Before SHA256": before_hash,
            "After SHA256": after_hash,
            "AST": ast_ok,
            "Compile": compile_ok,
            "Installed": "YES" if path.exists() else "NO",
            "Severity": "OK" if not error else "ERR",
            "Error": error,
        })

    registry = def_registry_obj()

    report_html = run_dir / "VRN_New_Report_Format_System_Default_Installer_v06155.html"
    report_json = run_dir / "vrn_new_report_format_system_default_installer_v06155.json"

    result = {
        "version": VERSION,
        "generated_at": def_now(),
        "system_pass": all(r["Severity"] == "OK" for r in rows),
        "mode": "ADD_ONLY_BACKUP_IF_EXISTS_NO_CANONICAL_NO_SSOT_NO_DB_NO_OCR_NO_NETWORK",
        "assets": rows,
        "outputs": {
            "html": str(report_html),
            "json": str(report_json),
            "gate_module": str(gate_module),
            "registry_json": str(registry_json),
            "playbook_md": str(playbook_md),
        }
    }

    def_write_json(report_json, result)
    def_write_html_report(report_html, rows, registry)

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        def_main()
    except Exception:
        print(traceback.format_exc())
        raise