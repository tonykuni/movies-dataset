# -*- coding: utf-8 -*-
"""
VIS_VRN_HistoricalValidationPolicy_v0100.py

VERITAS INTELLIGENCE ANALYTICS
VeritasReportNova Historical Validation Policy

Purpose:
- Broker report extracted FinancialData is observation only.
- Historical validation, Add/Sub validation, and Division validation must use historical / official / market-derived evidence.
- Broker report data must not validate itself.
- BasicInfo broker opinion fields stay broker_report priority and must not be overwritten by external sources.

Safety:
- No network call in this module.
- No production DB write.
- No mutation.
- Pure policy + deterministic validators.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


P_POLICY_VERSION = "VIS_VRN_HistoricalValidationPolicy_v0100"
P_NETWORK_ENABLED = False
P_DB_WRITE_ENABLED = False
P_MUTATION_ENABLED = False

P_REPORT_OBSERVATION_ONLY = True
P_HISTORICAL_VALIDATION_REQUIRES_HISTORICAL_SOURCE = True
P_DISABLE_REPORT_AS_VALIDATION_TRUTH = True

P_ALLOWED_HISTORICAL_SOURCE_TYPES = {
    "official_twse",
    "official_tpex",
    "mops",
    "yfinance",
    "historical_database",
    "vdf_duckdb",
    "audited_financial_history",
    "market_derived_history",
}

P_REPORT_SOURCE_TYPES = {
    "broker_report",
    "pdf_extract",
    "pdf_table",
    "report_table",
    "report_text",
}

P_BASICINFO_BROKER_OPINION_FIELDS = {
    "Rating",
    "Target Price",
    "TP",
    "Forecast EPS",
    "Analyst",
    "Broker",
    "Recommendation",
}

P_FINANCIAL_VALIDATION_CHECKS = {
    "historical_range_check": {
        "enabled": True,
        "truth_source": "historical_only",
        "report_source_allowed_as_truth": False,
    },
    "add_sub_check": {
        "enabled": True,
        "truth_source": "historical_or_ssot_formula",
        "report_source_allowed_as_truth": False,
    },
    "division_check": {
        "enabled": True,
        "truth_source": "historical_or_market_derived",
        "report_source_allowed_as_truth": False,
        "stage_a_scale_band": [0.5, 3.0],
        "stage_b_tolerance_pct": [1, 5, 10],
    },
}


@dataclass(frozen=True)
class def_ValidationSource:
    source_type: str
    source_name: str
    source_path: str = ""
    period_start: str = ""
    period_end: str = ""
    confidence: float = 0.0


def def_is_report_source(source_type: str) -> bool:
    return str(source_type).strip().lower() in P_REPORT_SOURCE_TYPES


def def_is_historical_source(source_type: str) -> bool:
    return str(source_type).strip().lower() in P_ALLOWED_HISTORICAL_SOURCE_TYPES


def def_get_policy() -> Dict[str, Any]:
    return {
        "policy_version": P_POLICY_VERSION,
        "network_enabled": P_NETWORK_ENABLED,
        "db_write_enabled": P_DB_WRITE_ENABLED,
        "mutation_enabled": P_MUTATION_ENABLED,
        "report_observation_only": P_REPORT_OBSERVATION_ONLY,
        "disable_report_as_validation_truth": P_DISABLE_REPORT_AS_VALIDATION_TRUTH,
        "allowed_historical_source_types": sorted(P_ALLOWED_HISTORICAL_SOURCE_TYPES),
        "report_source_types": sorted(P_REPORT_SOURCE_TYPES),
        "basicinfo_broker_opinion_fields": sorted(P_BASICINFO_BROKER_OPINION_FIELDS),
        "financial_validation_checks": P_FINANCIAL_VALIDATION_CHECKS,
    }


def def_should_use_report_as_basicinfo_value(field_name: str) -> bool:
    return str(field_name).strip() in P_BASICINFO_BROKER_OPINION_FIELDS


def def_can_use_source_for_historical_validation(source_type: str) -> bool:
    return def_is_historical_source(source_type)


def def_can_use_source_for_financial_truth(source_type: str) -> bool:
    if def_is_report_source(source_type):
        return False
    return def_is_historical_source(source_type)


def def_classify_validation_source(source: Dict[str, Any]) -> Dict[str, Any]:
    source_type = str(source.get("source_type", "")).strip().lower()

    if def_is_report_source(source_type):
        return {
            "source_role": "OBSERVATION_ONLY",
            "allowed_for_basicinfo_opinion": True,
            "allowed_for_financial_truth": False,
            "allowed_for_historical_check": False,
            "reason": "broker/pdf report data is extracted observation, not validation truth",
        }

    if def_is_historical_source(source_type):
        return {
            "source_role": "HISTORICAL_VALIDATION_TRUTH",
            "allowed_for_basicinfo_opinion": False,
            "allowed_for_financial_truth": True,
            "allowed_for_historical_check": True,
            "reason": "historical / official / market-derived source is allowed for validation",
        }

    return {
        "source_role": "UNKNOWN_REVIEW_REQUIRED",
        "allowed_for_basicinfo_opinion": False,
        "allowed_for_financial_truth": False,
        "allowed_for_historical_check": False,
        "reason": "unknown source type requires manual review",
    }


def def_validate_historical_interval_source(
    source_type: str,
    period_start: str,
    period_end: str,
) -> Dict[str, Any]:
    if not def_can_use_source_for_historical_validation(source_type):
        return {
            "status": "BLOCK",
            "risk": "RED",
            "message": "Historical interval validation requires historical / official source. Report source is not allowed.",
            "source_type": source_type,
            "period_start": period_start,
            "period_end": period_end,
        }

    return {
        "status": "PASS",
        "risk": "GREEN",
        "message": "Historical interval source accepted.",
        "source_type": source_type,
        "period_start": period_start,
        "period_end": period_end,
    }


def def_validate_add_sub_source(source_type: str) -> Dict[str, Any]:
    if not def_can_use_source_for_financial_truth(source_type):
        return {
            "status": "BLOCK",
            "risk": "RED",
            "check": "add_sub_check",
            "message": "Add/Sub check cannot use broker report data as truth.",
            "source_type": source_type,
        }

    return {
        "status": "PASS",
        "risk": "GREEN",
        "check": "add_sub_check",
        "message": "Add/Sub source accepted.",
        "source_type": source_type,
    }


def def_validate_division_source(source_type: str) -> Dict[str, Any]:
    if not def_can_use_source_for_financial_truth(source_type):
        return {
            "status": "BLOCK",
            "risk": "RED",
            "check": "division_check",
            "message": "Division check cannot use broker report data as truth.",
            "source_type": source_type,
        }

    return {
        "status": "PASS",
        "risk": "GREEN",
        "check": "division_check",
        "message": "Division source accepted.",
        "source_type": source_type,
    }


def def_validate_row_policy(row: Dict[str, Any]) -> Dict[str, Any]:
    source_type = str(row.get("source_type", row.get("Source Type", row.get("source", "")))).strip().lower()
    check_type = str(row.get("check_type", row.get("Check Type", ""))).strip().lower()

    if check_type in {"historical", "historical_range_check"}:
        return def_validate_historical_interval_source(
            source_type=source_type,
            period_start=str(row.get("period_start", "")),
            period_end=str(row.get("period_end", "")),
        )

    if check_type in {"add_sub", "add_sub_check"}:
        return def_validate_add_sub_source(source_type=source_type)

    if check_type in {"division", "division_check"}:
        return def_validate_division_source(source_type=source_type)

    source_class = def_classify_validation_source({"source_type": source_type})
    return {
        "status": "REVIEW",
        "risk": "YELLOW",
        "check": check_type,
        "message": "Unknown check type; source classified for review.",
        "source_type": source_type,
        "source_class": source_class,
    }


def def_self_check() -> Dict[str, Any]:
    tests = [
        def_validate_historical_interval_source("broker_report", "2023", "2025"),
        def_validate_historical_interval_source("yfinance", "2023", "2025"),
        def_validate_add_sub_source("pdf_table"),
        def_validate_add_sub_source("mops"),
        def_validate_division_source("report_text"),
        def_validate_division_source("historical_database"),
    ]

    blocked = [x for x in tests if x.get("status") == "BLOCK"]
    passed = [x for x in tests if x.get("status") == "PASS"]

    return {
        "policy_version": P_POLICY_VERSION,
        "tests": tests,
        "blocked_count": len(blocked),
        "passed_count": len(passed),
        "hard_pass": len(blocked) == 3 and len(passed) == 3,
    }


if __name__ == "__main__":
    import json
    print(json.dumps(def_self_check(), ensure_ascii=False, indent=2))
