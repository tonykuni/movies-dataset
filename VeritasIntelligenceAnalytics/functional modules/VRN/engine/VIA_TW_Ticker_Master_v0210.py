"""VIA-OS TW TICKER Master Module 2.1.0.

所有 *_REGEX 為字串，可供 re.fullmatch 與 JSON Schema 共用。
執行期只使用 Python 標準函式庫；格式候選與商品主檔核對分開回報。
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

import argparse
import json
import re
from collections.abc import Mapping
from datetime import date
from pathlib import Path

# ── 01｜參數與分類 SSOT：所有可調整設定集中於此 ──
MODULE_VERSION = "2.1.0"
SCHEMA_DIALECT = "https://json-schema.org/draft/2020-12/schema"
SCHEMA_ID = "urn:via:tw-ticker-master:2.1.0"
OUTPUT_ENCODING = "utf-8"
JSON_INDENT = 2
REGEX_FLAGS = re.ASCII
STRICT_END = r"$(?![\s\S])"
STOCK_BODY = r"[1-9][0-9]{3}"
NUMERIC_ETF_BODY = r"00[0-9]{2,4}"
OFFICIAL_MARKERS = "ABCDKLMRSTUV"
MARKER_BODY_TEMPLATE = r"(?:00[0-9]{3}{marker}|00[0-9]{marker}[0-9]{2})"
MAX_INPUT_LENGTH = 10
OFFICIAL_CODE_SOURCE = "https://twse-regulation.twse.com.tw/TW/law/DAT0201.aspx?FLCODE=FL033103"
SOURCE_RULE_REVISION = "2024-12-31"
SOURCE_CHECKED_DATE = "2026-09-21"
COMPATIBILITY_SOURCE = "ticker_regex_ssot_v0204.json (2026-09-10)"
DEFAULT_SCHEMA_NAME = "VIA_TW_Ticker_Master_v0210.schema.json"
DEFAULT_SSOT_NAME = "VIA_TW_Ticker_Regex_SSOT_v0210.json"
MARKET_TO_YAHOO = {"TWSE": "TW", "TPEX": "TWO"}
YAHOO_TO_MARKET = {value: key for key, value in MARKET_TO_YAHOO.items()}
PLATFORM_PREFIX = {"LOCAL": "TW", "YFINANCE": "TW_YFINANCE", "BLOOMBERG": "TW_BLOOMBERG"}
PLATFORM_SUFFIX = {"LOCAL": "", "YFINANCE": r"\.(TW|TWO)", "BLOOMBERG": r"[ ]TT"}
FIELD_PLATFORM = {"TW_TICKER": "LOCAL", "TW_YF_TICKER": "YFINANCE", "TW_BB_TICKER": "BLOOMBERG"}
MASTER_REQUIRED_FIELDS = ("market", "security_type", "source", "as_of")
CLASSIFICATION_FIELDS = ("asset_class", "management", "exposure", "trading_currency_class", "currency")

# category, marker, label, asset class, management, exposure, trading currency class
# UNKNOWN 表示該維度不能僅依代碼判斷；例如 L 可為股票、債券或期貨槓桿。
RULE_ROWS = (
    ("STOCK", None, "一般個股", "EQUITY", "NOT_APPLICABLE", "NOT_APPLICABLE", "UNKNOWN"),
    ("PASSIVE_STOCK_ETF", "", "被動股票 ETF 格式候選", "EQUITY", "PASSIVE", "STANDARD", "LOCAL"),
    ("ACTIVE_STOCK_ETF", "A", "主動股票 ETF 格式候選", "EQUITY", "ACTIVE", "STANDARD", "LOCAL"),
    ("PASSIVE_BOND_ETF", "B", "被動債券 ETF", "BOND", "PASSIVE", "STANDARD", "LOCAL"),
    ("ACTIVE_BOND_ETF", "D", "主動債券 ETF", "BOND", "ACTIVE", "STANDARD", "LOCAL"),
    ("LEVERAGED_ETF", "L", "槓桿型 ETF", "UNKNOWN", "PASSIVE", "LEVERAGED", "LOCAL"),
    ("INVERSE_ETF", "R", "反向型 ETF", "UNKNOWN", "PASSIVE", "INVERSE", "LOCAL"),
    ("FUTURES_ETF", "U", "一般期貨 ETF", "FUTURES", "PASSIVE", "STANDARD", "LOCAL"),
    ("BALANCED_ETF", "T", "平衡型 ETF", "MULTI_ASSET", "PASSIVE", "STANDARD", "LOCAL"),
    ("FOREIGN_CURRENCY_STANDARD_ETF", "K", "外幣交易一般 ETF", "UNKNOWN", "PASSIVE", "STANDARD", "FOREIGN"),
    ("FOREIGN_CURRENCY_BOND_ETF", "C", "外幣交易債券 ETF", "BOND", "PASSIVE", "STANDARD", "FOREIGN"),
    ("FOREIGN_CURRENCY_LEVERAGED_ETF", "M", "外幣交易槓桿 ETF", "UNKNOWN", "PASSIVE", "LEVERAGED", "FOREIGN"),
    ("FOREIGN_CURRENCY_INVERSE_ETF", "S", "外幣交易反向 ETF", "UNKNOWN", "PASSIVE", "INVERSE", "FOREIGN"),
    ("FOREIGN_CURRENCY_FUTURES_ETF", "V", "外幣交易期貨 ETF", "FUTURES", "PASSIVE", "STANDARD", "FOREIGN"),
)
RULES = {
    row[0]: {
        "marker": row[1], "label": row[2], "asset_class": row[3],
        "management": row[4], "exposure": row[5], "trading_currency_class": row[6],
    }
    for row in RULE_ROWS
}
CATEGORY_BODIES = {
    category: STOCK_BODY if rule["marker"] is None else (
        NUMERIC_ETF_BODY if rule["marker"] == "" else
        MARKER_BODY_TEMPLATE.replace("{marker}", rule["marker"])
    )
    for category, rule in RULES.items()
}
ETF_BODY = rf"(?:{NUMERIC_ETF_BODY}|00[0-9]{{3}}[{OFFICIAL_MARKERS}]|00[0-9][{OFFICIAL_MARKERS}][0-9]{{2}})"
SECURITY_BODY = rf"(?:{STOCK_BODY}|{ETF_BODY})"
PATTERN_BODIES = {**CATEGORY_BODIES, "ETF": ETF_BODY, "SECURITY": SECURITY_BODY}
REGEX_REGISTRY = {
    f"{prefix}_{category}_REGEX": rf"^({body}){PLATFORM_SUFFIX[platform]}{STRICT_END}"
    for platform, prefix in PLATFORM_PREFIX.items()
    for category, body in PATTERN_BODIES.items()
}
SHAPE_BODY = rf"(?:{STOCK_BODY}|{NUMERIC_ETF_BODY}|00[0-9]{{3}}[A-Z]|00[0-9][A-Z][0-9]{{2}})"
SHAPE_REGEX = {
    platform: re.compile(rf"^({SHAPE_BODY}){suffix}{STRICT_END}", REGEX_FLAGS)
    for platform, suffix in PLATFORM_SUFFIX.items()
}

# ── 02｜公開命名：三平台 × 14 分類 + ETF／SECURITY 合併規則 ──
TW_STOCK_REGEX = REGEX_REGISTRY["TW_STOCK_REGEX"]
TW_YFINANCE_STOCK_REGEX = REGEX_REGISTRY["TW_YFINANCE_STOCK_REGEX"]
TW_BLOOMBERG_STOCK_REGEX = REGEX_REGISTRY["TW_BLOOMBERG_STOCK_REGEX"]
TW_PASSIVE_STOCK_ETF_REGEX = REGEX_REGISTRY["TW_PASSIVE_STOCK_ETF_REGEX"]
TW_YFINANCE_PASSIVE_STOCK_ETF_REGEX = REGEX_REGISTRY["TW_YFINANCE_PASSIVE_STOCK_ETF_REGEX"]
TW_BLOOMBERG_PASSIVE_STOCK_ETF_REGEX = REGEX_REGISTRY["TW_BLOOMBERG_PASSIVE_STOCK_ETF_REGEX"]
TW_ACTIVE_STOCK_ETF_REGEX = REGEX_REGISTRY["TW_ACTIVE_STOCK_ETF_REGEX"]
TW_YFINANCE_ACTIVE_STOCK_ETF_REGEX = REGEX_REGISTRY["TW_YFINANCE_ACTIVE_STOCK_ETF_REGEX"]
TW_BLOOMBERG_ACTIVE_STOCK_ETF_REGEX = REGEX_REGISTRY["TW_BLOOMBERG_ACTIVE_STOCK_ETF_REGEX"]
TW_PASSIVE_BOND_ETF_REGEX = REGEX_REGISTRY["TW_PASSIVE_BOND_ETF_REGEX"]
TW_YFINANCE_PASSIVE_BOND_ETF_REGEX = REGEX_REGISTRY["TW_YFINANCE_PASSIVE_BOND_ETF_REGEX"]
TW_BLOOMBERG_PASSIVE_BOND_ETF_REGEX = REGEX_REGISTRY["TW_BLOOMBERG_PASSIVE_BOND_ETF_REGEX"]
TW_ACTIVE_BOND_ETF_REGEX = REGEX_REGISTRY["TW_ACTIVE_BOND_ETF_REGEX"]
TW_YFINANCE_ACTIVE_BOND_ETF_REGEX = REGEX_REGISTRY["TW_YFINANCE_ACTIVE_BOND_ETF_REGEX"]
TW_BLOOMBERG_ACTIVE_BOND_ETF_REGEX = REGEX_REGISTRY["TW_BLOOMBERG_ACTIVE_BOND_ETF_REGEX"]
TW_LEVERAGED_ETF_REGEX = REGEX_REGISTRY["TW_LEVERAGED_ETF_REGEX"]
TW_YFINANCE_LEVERAGED_ETF_REGEX = REGEX_REGISTRY["TW_YFINANCE_LEVERAGED_ETF_REGEX"]
TW_BLOOMBERG_LEVERAGED_ETF_REGEX = REGEX_REGISTRY["TW_BLOOMBERG_LEVERAGED_ETF_REGEX"]
TW_INVERSE_ETF_REGEX = REGEX_REGISTRY["TW_INVERSE_ETF_REGEX"]
TW_YFINANCE_INVERSE_ETF_REGEX = REGEX_REGISTRY["TW_YFINANCE_INVERSE_ETF_REGEX"]
TW_BLOOMBERG_INVERSE_ETF_REGEX = REGEX_REGISTRY["TW_BLOOMBERG_INVERSE_ETF_REGEX"]
TW_FUTURES_ETF_REGEX = REGEX_REGISTRY["TW_FUTURES_ETF_REGEX"]
TW_YFINANCE_FUTURES_ETF_REGEX = REGEX_REGISTRY["TW_YFINANCE_FUTURES_ETF_REGEX"]
TW_BLOOMBERG_FUTURES_ETF_REGEX = REGEX_REGISTRY["TW_BLOOMBERG_FUTURES_ETF_REGEX"]
TW_BALANCED_ETF_REGEX = REGEX_REGISTRY["TW_BALANCED_ETF_REGEX"]
TW_YFINANCE_BALANCED_ETF_REGEX = REGEX_REGISTRY["TW_YFINANCE_BALANCED_ETF_REGEX"]
TW_BLOOMBERG_BALANCED_ETF_REGEX = REGEX_REGISTRY["TW_BLOOMBERG_BALANCED_ETF_REGEX"]
TW_FOREIGN_CURRENCY_STANDARD_ETF_REGEX = REGEX_REGISTRY["TW_FOREIGN_CURRENCY_STANDARD_ETF_REGEX"]
TW_YFINANCE_FOREIGN_CURRENCY_STANDARD_ETF_REGEX = REGEX_REGISTRY["TW_YFINANCE_FOREIGN_CURRENCY_STANDARD_ETF_REGEX"]
TW_BLOOMBERG_FOREIGN_CURRENCY_STANDARD_ETF_REGEX = REGEX_REGISTRY["TW_BLOOMBERG_FOREIGN_CURRENCY_STANDARD_ETF_REGEX"]
TW_FOREIGN_CURRENCY_BOND_ETF_REGEX = REGEX_REGISTRY["TW_FOREIGN_CURRENCY_BOND_ETF_REGEX"]
TW_YFINANCE_FOREIGN_CURRENCY_BOND_ETF_REGEX = REGEX_REGISTRY["TW_YFINANCE_FOREIGN_CURRENCY_BOND_ETF_REGEX"]
TW_BLOOMBERG_FOREIGN_CURRENCY_BOND_ETF_REGEX = REGEX_REGISTRY["TW_BLOOMBERG_FOREIGN_CURRENCY_BOND_ETF_REGEX"]
TW_FOREIGN_CURRENCY_LEVERAGED_ETF_REGEX = REGEX_REGISTRY["TW_FOREIGN_CURRENCY_LEVERAGED_ETF_REGEX"]
TW_YFINANCE_FOREIGN_CURRENCY_LEVERAGED_ETF_REGEX = REGEX_REGISTRY["TW_YFINANCE_FOREIGN_CURRENCY_LEVERAGED_ETF_REGEX"]
TW_BLOOMBERG_FOREIGN_CURRENCY_LEVERAGED_ETF_REGEX = REGEX_REGISTRY["TW_BLOOMBERG_FOREIGN_CURRENCY_LEVERAGED_ETF_REGEX"]
TW_FOREIGN_CURRENCY_INVERSE_ETF_REGEX = REGEX_REGISTRY["TW_FOREIGN_CURRENCY_INVERSE_ETF_REGEX"]
TW_YFINANCE_FOREIGN_CURRENCY_INVERSE_ETF_REGEX = REGEX_REGISTRY["TW_YFINANCE_FOREIGN_CURRENCY_INVERSE_ETF_REGEX"]
TW_BLOOMBERG_FOREIGN_CURRENCY_INVERSE_ETF_REGEX = REGEX_REGISTRY["TW_BLOOMBERG_FOREIGN_CURRENCY_INVERSE_ETF_REGEX"]
TW_FOREIGN_CURRENCY_FUTURES_ETF_REGEX = REGEX_REGISTRY["TW_FOREIGN_CURRENCY_FUTURES_ETF_REGEX"]
TW_YFINANCE_FOREIGN_CURRENCY_FUTURES_ETF_REGEX = REGEX_REGISTRY["TW_YFINANCE_FOREIGN_CURRENCY_FUTURES_ETF_REGEX"]
TW_BLOOMBERG_FOREIGN_CURRENCY_FUTURES_ETF_REGEX = REGEX_REGISTRY["TW_BLOOMBERG_FOREIGN_CURRENCY_FUTURES_ETF_REGEX"]
TW_ETF_REGEX = REGEX_REGISTRY["TW_ETF_REGEX"]
TW_YFINANCE_ETF_REGEX = REGEX_REGISTRY["TW_YFINANCE_ETF_REGEX"]
TW_BLOOMBERG_ETF_REGEX = REGEX_REGISTRY["TW_BLOOMBERG_ETF_REGEX"]
TW_SECURITY_REGEX = REGEX_REGISTRY["TW_SECURITY_REGEX"]
TW_YFINANCE_SECURITY_REGEX = REGEX_REGISTRY["TW_YFINANCE_SECURITY_REGEX"]
TW_BLOOMBERG_SECURITY_REGEX = REGEX_REGISTRY["TW_BLOOMBERG_SECURITY_REGEX"]

# ── 03｜格式辨識與分類 ──
def classify_ticker(value: object, security_master: Mapping | None = None) -> dict:
    """辨識三平台與格式分類；主檔由呼叫端提供，本函式不連網。

    CANDIDATE 只表示格式通過；MASTER_MATCHED 表示與提供的主檔一致，
    不代表本函式已向交易所或 Yahoo/Bloomberg 查詢商品存在性。
    """
    result = {
        "input": value, "status": "INVALID", "format_valid": False,
        "master_matched": None, "platform": None, "local_code": None,
        "pattern_category": None, "marker": None, "code_style": None,
        "market_hint": None, "classification": {}, "classification_source": None,
        "reason": None,
    }
    if not isinstance(value, str) or not value or len(value) > MAX_INPUT_LENGTH:
        result["reason"] = "EXPECTED_NONEMPTY_STRING_WITH_VALID_LENGTH"
        return result
    platform, match = next(
        ((name, matched) for name, regex in SHAPE_REGEX.items()
         if (matched := regex.fullmatch(value))),
        (None, None),
    )
    if match is None:
        result["reason"] = "INVALID_CHARACTERS_LENGTH_OR_PLATFORM_SUFFIX"
        return result
    code = match.group(1)
    result.update(platform=platform, local_code=code)
    if platform == "YFINANCE":
        result["market_hint"] = YAHOO_TO_MARKET[match.group(2)]
    category = next(
        (name for name in RULES if re.fullmatch(REGEX_REGISTRY[f"TW_{name}_REGEX"], code, REGEX_FLAGS)),
        None,
    )
    if category is None:
        result.update(status="REVIEW", reason="UNRECOGNIZED_ETF_MARKER")
        return result
    rule = RULES[category]
    style = "NUMERIC" if code.isascii() and code.isdigit() else ("SUFFIX" if code[-1].isalpha() else "ROLLOVER")
    classification = {field: rule[field] for field in CLASSIFICATION_FIELDS if field in rule}
    classification["security_type"] = "STOCK" if category == "STOCK" else "ETF"
    classification["currency"] = None  # 外幣種類（USD/CNY 等）只能由主檔提供。
    result.update(
        status="CANDIDATE", format_valid=True, pattern_category=category,
        marker=rule["marker"], code_style=style, classification=classification,
        classification_source="REGEX_HINT",
        reason="ROLLOVER_REQUIRES_MASTER_CONFIRMATION" if style == "ROLLOVER" else "MASTER_NOT_PROVIDED",
    )
    if security_master is not None:
        return match_security_master(result, security_master)
    return result


def match_security_master(result: dict, security_master: Mapping) -> dict:
    """核對呼叫端的主檔，避免將市場、期貨槓桿與幣別猜成固定類型。"""
    checked = {**result, "classification": dict(result["classification"]), "master_matched": False}
    if not isinstance(security_master, Mapping):
        checked.update(status="MASTER_ERROR", reason="MASTER_MUST_BE_MAPPING")
        return checked
    record = security_master.get(result["local_code"])
    if record is None:
        checked.update(status="NOT_IN_MASTER", reason="LOCAL_CODE_NOT_FOUND")
        return checked
    if not isinstance(record, Mapping) or any(
        not isinstance(record.get(field), str) or not record[field].strip()
        for field in MASTER_REQUIRED_FIELDS
    ):
        checked.update(status="MASTER_ERROR", reason="MASTER_REQUIRED_FIELDS_MISSING")
        return checked
    try:
        date.fromisoformat(record["as_of"])
    except ValueError:
        checked.update(status="MASTER_ERROR", reason="INVALID_MASTER_AS_OF_DATE")
        return checked
    market = record["market"]
    if market not in MARKET_TO_YAHOO:
        checked.update(status="MASTER_ERROR", reason="UNSUPPORTED_MASTER_MARKET")
        return checked
    if record["security_type"] != result["classification"]["security_type"]:
        checked.update(status="MASTER_MISMATCH", reason="SECURITY_TYPE_MISMATCH")
        return checked
    if result["market_hint"] is not None and result["market_hint"] != market:
        checked.update(status="MASTER_MISMATCH", reason="YAHOO_MARKET_MISMATCH")
        return checked
    checked["classification"].update({field: record[field] for field in CLASSIFICATION_FIELDS if field in record})
    checked.update(
        status="MASTER_MATCHED", master_matched=True, market_hint=market,
        classification_source="CALLER_SUPPLIED_SECURITY_MASTER", reason=None,
        master_source=record["source"], master_as_of=record["as_of"],
    )
    return checked


def validate_ticker_triplet(record: object, security_master: Mapping | None = None) -> dict:
    """核對三欄格式、完整本地代碼相同及市場；不截取 ETF 的前四碼。"""
    if not isinstance(record, Mapping):
        return {"valid": False, "status": "INVALID", "errors": ["RECORD_MUST_BE_OBJECT"]}
    errors = []
    parsed = {}
    for field, platform in FIELD_PLATFORM.items():
        item = classify_ticker(record.get(field), security_master)
        parsed[field] = item
        if not item["format_valid"] or item["platform"] != platform:
            errors.append(f"{field}:INVALID_FORMAT_OR_PLATFORM")
        elif security_master is not None and not item["master_matched"]:
            errors.append(f"{field}:{item['reason']}")
    if not errors:
        if len({item["local_code"] for item in parsed.values()}) != 1:
            errors.append("LOCAL_CODES_DIFFER")
        if "MARKET" in record:
            if not isinstance(record["MARKET"], str) or record["MARKET"] not in MARKET_TO_YAHOO:
                errors.append("INVALID_MARKET")
            elif record["MARKET"] != parsed["TW_YF_TICKER"]["market_hint"]:
                errors.append("MARKET_AND_YAHOO_SUFFIX_DIFFER")
        if "SECURITY_CATEGORY" in record and record["SECURITY_CATEGORY"] != parsed["TW_TICKER"]["pattern_category"]:
            errors.append("SECURITY_CATEGORY_DIFFERS")
    return {
        "valid": not errors,
        "status": "INVALID" if errors else ("MASTER_MATCHED" if security_master is not None else "CANDIDATE"),
        "errors": errors, "fields": parsed,
    }

# ── 04｜JSON Schema 與 SSOT 匯出：名稱和 pattern 從同一份定義產生 ──
def build_json_schema() -> dict:
    """Schema 驗證各欄格式、相同分類與明示市場；代碼相等由 triplet 函式檢查。"""
    return {
        "$schema": SCHEMA_DIALECT, "$id": SCHEMA_ID,
        "title": "VIA-OS TW TICKER Master Module",
        "description": "Ordinary-stock and ETF format candidates. Product identity and cross-field code equality require the Python validator and a security master.",
        "type": "object", "required": list(FIELD_PLATFORM),
        "properties": {
            **{field: {"$ref": f"#/$defs/{PLATFORM_PREFIX[platform]}_SECURITY_REGEX"} for field, platform in FIELD_PLATFORM.items()},
            "MARKET": {"enum": list(MARKET_TO_YAHOO)},
            "SECURITY_CATEGORY": {"enum": list(RULES)},
        },
        "additionalProperties": True,
        "oneOf": [
            {"properties": {
                **{field: {"$ref": f"#/$defs/{PLATFORM_PREFIX[platform]}_{category}_REGEX"} for field, platform in FIELD_PLATFORM.items()},
                "SECURITY_CATEGORY": {"const": category},
            }} for category in RULES
        ],
        "allOf": [
            {
                "if": {"required": ["MARKET"], "properties": {"MARKET": {"const": market}}},
                "then": {"properties": {"TW_YF_TICKER": {"pattern": rf"^({SECURITY_BODY})\.{suffix}{STRICT_END}"}}},
            } for market, suffix in MARKET_TO_YAHOO.items()
        ],
        "$defs": {name: {"type": "string", "pattern": pattern} for name, pattern in REGEX_REGISTRY.items()},
        "$comment": "No remote fetching. Middle-letter rollover codes are compatibility candidates from the prior VIA SSOT. TT is the project's Bloomberg short format; optional Equity is intentionally not accepted.",
    }


def build_ssot() -> dict:
    """匯出公開命名、分類和可追溯的規則來源。"""
    return {
        "schema_version": MODULE_VERSION,
        "authority": "security_master_first_regex_candidate_second",
        "source": OFFICIAL_CODE_SOURCE,
        "source_rule_revision": SOURCE_RULE_REVISION,
        "source_checked_date": SOURCE_CHECKED_DATE,
        "compatibility_source": COMPATIBILITY_SOURCE,
        "scope": "Four-digit ordinary stocks and 00-prefixed Taiwan-listed ETF candidates; excludes preferred shares, ETNs, warrants, REITs and depositary receipts.",
        "platform_prefixes": PLATFORM_PREFIX, "categories": RULES,
        "regex": REGEX_REGISTRY,
        "notes": [
            "All public *_REGEX values are strings; re.fullmatch is recommended.",
            "Capture group 1 is the complete local code; Yahoo capture group 2 is TW or TWO.",
            "Numeric ETF codes support 4, 5, and 6 ASCII digits.",
            "Suffix markers have official coding support; middle-marker rollover forms are compatibility candidates, not a statement that every form is officially issued.",
            "K/C/M/S/V indicate foreign trading-currency classes; they do not specify USD, CNY, or investment geography.",
            "L/R/M/S do not identify the underlying asset class; use the security master.",
            "Unknown alphabetic markers return REVIEW and fail the strict ETF/SECURITY regex.",
            "No silent strip, upper, Unicode normalization or integer-to-string conversion.",
        ],
    }


def export_definitions(directory: str | Path) -> list[str]:
    """將 JSON Schema 與命名 SSOT 寫入指定目錄。"""
    target = Path(directory)
    target.mkdir(parents=True, exist_ok=True)
    paths = []
    for name, data in ((DEFAULT_SCHEMA_NAME, build_json_schema()), (DEFAULT_SSOT_NAME, build_ssot())):
        output = target / name
        output.write_text(json.dumps(data, ensure_ascii=False, indent=JSON_INDENT) + "\n", encoding=OUTPUT_ENCODING)
        paths.append(str(output.resolve()))
    return paths


def main(argv: list[str] | None = None) -> int:
    """命令列入口：分類、三欄核對、匯出規範。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tickers", nargs="*", help="本地、Yahoo 或 Bloomberg 短碼")
    parser.add_argument("--master", type=Path, help="以本地代碼為鍵的商品主檔 JSON")
    parser.add_argument("--triplet", type=Path, help="含三平台欄位的 JSON")
    parser.add_argument("--export", type=Path, help="匯出 JSON Schema 與 SSOT 至指定目錄")
    args = parser.parse_args(argv)
    try:
        master = json.loads(args.master.read_text(encoding="utf-8-sig")) if args.master else None
        results = [classify_ticker(ticker, master) for ticker in args.tickers]
        if args.triplet:
            results.append(validate_ticker_triplet(json.loads(args.triplet.read_text(encoding="utf-8-sig")), master))
        if args.export:
            results.append({"exported": export_definitions(args.export)})
        if not results:
            parser.print_help()
            return 0
        print(json.dumps(results, ensure_ascii=False, indent=JSON_INDENT))
        return int(any(item.get("status") in {"INVALID", "REVIEW", "MASTER_ERROR", "MASTER_MISMATCH", "NOT_IN_MASTER"} for item in results))
    except (OSError, ValueError) as error:
        parser.error(str(error))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
