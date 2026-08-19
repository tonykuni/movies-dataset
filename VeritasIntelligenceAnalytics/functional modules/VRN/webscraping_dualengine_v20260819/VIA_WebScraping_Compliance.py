#!/usr/bin/env python3
from __future__ import annotations
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

SSOT_PATH = Path(__file__).with_name("VIA_WebScraping_Compliance_SSOT.json")
TW_ID_MAP = {letter: value for letter, value in zip("ABCDEFGHJKLMNPQRSTUVXYWZIO", [10,11,12,13,14,15,16,17,34,18,19,20,21,22,35,23,24,25,26,27,28,29,32,30,31,33])}

@dataclass
class ComplianceFinding:
    code: str
    severity: str
    evidence: str

def def_load_compliance_ssot(path: Path = SSOT_PATH) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not data.get("required_consent_token") or not data.get("pii"): raise ValueError("INVALID_COMPLIANCE_SSOT")
    return data

def def_validate_consent(token: str, purpose: str, authorization_basis: str, ssot: dict[str, Any] | None = None) -> list[ComplianceFinding]:
    ssot = ssot or def_load_compliance_ssot(); findings = []
    if token != ssot["required_consent_token"]: findings.append(ComplianceFinding("CONSENT_MISSING", "BLOCK", "Required explicit token not supplied"))
    if len((purpose or "").strip()) < 8: findings.append(ComplianceFinding("PURPOSE_MISSING", "BLOCK", "Purpose must be explicit"))
    if len((authorization_basis or "").strip()) < 8: findings.append(ComplianceFinding("AUTHORIZATION_BASIS_MISSING", "BLOCK", "Authorization basis must be explicit"))
    return findings

def def_luhn_valid(value: str) -> bool:
    digits = [int(x) for x in re.sub(r"\D", "", value)]
    if not 13 <= len(digits) <= 19 or len(set(digits)) == 1: return False
    total = 0; parity = len(digits) % 2
    for index, digit in enumerate(digits):
        if index % 2 == parity:
            digit *= 2
            if digit > 9: digit -= 9
        total += digit
    return total % 10 == 0

def def_tw_id_valid(value: str) -> bool:
    value = value.upper(); mapped = TW_ID_MAP.get(value[0]) if len(value) == 10 else None
    if mapped is None or not value[1:].isdigit(): return False
    digits = [mapped // 10, mapped % 10] + [int(x) for x in value[1:]]
    weights = [1, 9, 8, 7, 6, 5, 4, 3, 2, 1, 1]
    return sum(x * y for x, y in zip(digits, weights)) % 10 == 0

def def_redact_pii(text: str, mode: str = "partial", ssot: dict[str, Any] | None = None) -> tuple[str, dict[str, int]]:
    if not text or mode == "off": return text, {}
    ssot = ssot or def_load_compliance_ssot(); counts: dict[str, int] = {}
    def apply(name: str, handler):
        nonlocal text
        pattern = re.compile(ssot["pii"][name], re.I)
        def replace(match):
            replacement = handler(match.group(0))
            if replacement != match.group(0): counts[name] = counts.get(name, 0) + 1
            return replacement
        text = pattern.sub(replace, text)
    apply("email", lambda value: "[REDACTED_EMAIL]" if mode == "full" else f"{value.split('@')[0][:1]}***@{value.split('@',1)[1]}")
    def mobile(value: str) -> str:
        clean = re.sub(r"[ -]", "", value)
        return "[REDACTED_MOBILE]" if mode == "full" else f"{clean[:4]}***{clean[-3:]}"
    apply("tw_mobile", mobile)
    apply("tw_id_candidate", lambda value: ("[REDACTED_TW_ID]" if mode == "full" else f"{value[:2]}******{value[-2:]}") if def_tw_id_valid(value) else value)
    apply("credit_card_candidate", lambda value: ("[REDACTED_CARD]" if mode == "full" else f"****-****-****-{re.sub(r'\D','',value)[-4:]}") if def_luhn_valid(value) else value)
    return text, counts

def def_scan_terms_text(text: str, ssot: dict[str, Any] | None = None) -> dict[str, Any]:
    ssot = ssot or def_load_compliance_ssot(); evidence = []
    for pattern in ssot["terms_prohibition_patterns"]:
        if re.search(pattern, text or "", re.I): evidence.append(pattern)
    score = len(evidence)
    return {"risk": "HIGH" if score >= ssot["terms_high_risk_threshold"] else "LOW",
            "score": score, "evidence": evidence, "legal_review_required": score > 0,
            "disclaimer": "Automated ToS screening is not a legal opinion."}

def def_compliance_payload(text: str, pii_mode: str = "partial") -> tuple[str, dict[str, Any]]:
    redacted, counts = def_redact_pii(text, pii_mode); terms = def_scan_terms_text(text)
    return redacted, {"pii_mode": pii_mode, "pii_redaction_counts": counts, "terms_scan": terms,
                      "gate": "REVIEW_REQUIRED" if terms["legal_review_required"] else "PASS"}

def def_self_test() -> None:
    assert def_luhn_valid("4111 1111 1111 1111") and not def_luhn_valid("2026 2026 2026 2026")
    assert def_tw_id_valid("A123456789") and not def_tw_id_valid("A123456788")
    safe, counts = def_redact_pii("A123456789 0912-345-678 a.test@example.com 4111-1111-1111-1111")
    assert "A123456789" not in safe and sum(counts.values()) == 4
    assert def_scan_terms_text("You may not scrape or crawl this service")["risk"] == "HIGH"

if __name__ == "__main__": def_self_test(); print("def COMPLIANCE_SELF_TEST: PASS")
