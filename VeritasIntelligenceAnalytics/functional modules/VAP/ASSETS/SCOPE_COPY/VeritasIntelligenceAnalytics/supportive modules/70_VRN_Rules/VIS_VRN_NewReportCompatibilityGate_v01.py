# -*- coding: utf-8 -*-
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

# ======================================================================================
# VRN_V139O_SUPPORTIVE_BRIDGE_APPEND_ONLY START
# def Purpose:
# def   - Append-only supportive bridge for VRN production modules
# def   - Safe optional imports only; no DB write, no SSOT mutation, no network execution
# def   - Enables downstream audit to detect Aegis / Celeritas / EnvManager / NoHang coverage
# ======================================================================================

VRN_V139O_SUPPORTIVE_BRIDGE_ENABLED = True
VRN_V139O_NOHANG_WATCHDOG_ENABLED = True
VRN_V139O_DB_WRITE_ENABLE = False
VRN_V139O_SSOT_MUTATION_ENABLE = False
VRN_V139O_NETWORK_ENABLE = False

VRN_V139O_AEGIS_PATH = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module\VeritasAegisNexus.py"
VRN_V139O_CELERITAS_PATH = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module\VeritasCeleritas.py"
VRN_V139O_ENV_MANAGER_PATH = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module\VIA_EnvManager.py"

def def_vrn_v139o_optional_import_module(module_name, module_path):
    import importlib.util
    import sys
    from pathlib import Path

    result = {
        "module": str(module_name),
        "path": str(module_path),
        "exists": False,
        "import_ok": False,
        "error": "",
    }

    try:
        p = Path(str(module_path))
        result["exists"] = p.exists()
        if not p.exists():
            result["error"] = "missing"
            return result

        spec = importlib.util.spec_from_file_location(str(module_name), str(p))
        mod = importlib.util.module_from_spec(spec)
        sys.modules[str(module_name)] = mod
        spec.loader.exec_module(mod)
        result["import_ok"] = True
        return result
    except BaseException as e:
        result["error"] = str(e)
        return result

def def_vrn_v139o_supportive_bridge_health():
    return {
        "bridge": "VRN_V139O_SUPPORTIVE_BRIDGE_APPEND_ONLY",
        "aegis": def_vrn_v139o_optional_import_module("VeritasAegisNexus", VRN_V139O_AEGIS_PATH),
        "celeritas": def_vrn_v139o_optional_import_module("VeritasCeleritas", VRN_V139O_CELERITAS_PATH),
        "envmanager": def_vrn_v139o_optional_import_module("VIA_EnvManager", VRN_V139O_ENV_MANAGER_PATH),
        "nohang_watchdog": VRN_V139O_NOHANG_WATCHDOG_ENABLED,
        "db_write": VRN_V139O_DB_WRITE_ENABLE,
        "ssot_mutation": VRN_V139O_SSOT_MUTATION_ENABLE,
        "network": VRN_V139O_NETWORK_ENABLE,
    }

# VRN_V139O_SUPPORTIVE_BRIDGE_APPEND_ONLY END

