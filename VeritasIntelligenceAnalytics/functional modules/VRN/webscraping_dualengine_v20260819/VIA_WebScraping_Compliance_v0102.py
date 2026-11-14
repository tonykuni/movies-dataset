#!/usr/bin/env python3
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0111] 最新有版號的正本加速器(動態取最高 VeritasCeleritas_v####;退回鎖版 v1141)· 正本網路工具 VeritasAegisNexus_v1652(找不到 = 不改任何行為) =====
import importlib as _cb_il
import re as _cb_re
import sys as _cb_sys
from pathlib import Path as _cb_Path
_ACCEL, _ACCEL_VER = None, ""
_cb_p = _cb_Path(__file__).resolve()
while _cb_p.parent != _cb_p:
    if (_cb_p / "supportive modules").is_dir():
        _cb_sup = _cb_p / "supportive modules"
        _cb_c = sorted(list(_cb_sup.glob("VeritasCeleritas_v[0-9][0-9][0-9][0-9].py")) + list(_cb_sup.glob("*/VeritasCeleritas_v[0-9][0-9][0-9][0-9].py")),
                       key=lambda x: int(_cb_re.search(r"_v(\d{4})", x.name).group(1)))
        for _cb_d in [str(_cb_sup)] + ([str(_cb_c[-1].parent)] if _cb_c else []) + [str(x.parent) for x in list(_cb_sup.glob("*/VeritasAegisNexus_v1652.py"))[:1]]:
            if _cb_d not in _cb_sys.path:
                _cb_sys.path.insert(0, _cb_d)
        if _cb_c:
            try:
                _ACCEL, _ACCEL_VER = _cb_il.import_module(_cb_c[-1].stem), _cb_c[-1].stem
            except Exception:  # noqa: BLE001
                _ACCEL = None
        break
    _cb_p = _cb_p.parent
if _ACCEL is None:
    try:
        import VeritasCeleritas_v1141 as _ACCEL  # noqa: F401  退回鎖版
        _ACCEL_VER = "VeritasCeleritas_v1141"
    except Exception:  # noqa: BLE001
        _ACCEL = None


def _net():
    """正本網路工具(只在需要出網時載入;本引擎不出網)。"""
    try:
        import VeritasAegisNexus_v1652 as _NET  # noqa: WPS433
        return _NET
    except Exception:  # noqa: BLE001
        return None
# ===== [VIA:ACCEL-BRIDGE:END] =====
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
    apply("credit_card_candidate", lambda value: ("[REDACTED_CARD]" if mode == "full" else "****-****-****-" + re.sub(r"\D", "", value)[-4:]) if def_luhn_valid(value) else value)
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
