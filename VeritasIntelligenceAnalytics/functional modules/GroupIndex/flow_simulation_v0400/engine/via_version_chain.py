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

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

import pandas as pd


PIPELINE_STAGES = ("FETCH", "CLASSIFY", "VALIDATE", "INDEX", "OBSERVE", "FLOW")
EVIDENCE_STRENGTH = {
    "MEASURED": 0,
    "DERIVED": 1,
    "PROXY": 2,
    "ESTIMATED": 3,
    "SOURCE_REPORTED_SOURCED_UNVERIFIED": 4,
    "CONTROLLED_FIXTURE": 5,
    "UNAVAILABLE": 6,
}


def def_weakest_evidence(*tiers: str) -> str:
    unknown = [tier for tier in tiers if tier not in EVIDENCE_STRENGTH]
    if unknown:
        raise ValueError(f"Unknown evidence tier(s): {unknown}")
    return max(tiers, key=lambda tier: EVIDENCE_STRENGTH[tier])


def _artifact_id(stage: str, payload: dict[str, Any]) -> str:
    digest = hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()[:16].upper()
    return f"VIA-{stage}-{digest}"


def def_build_candidate_version_chain(
    candidate_validation: pd.DataFrame,
    *,
    asof_date: str,
    source_ref: str,
    parameters_digest: str,
) -> pd.DataFrame:
    """Build a monotone provenance chain. INDEX is blocked unless every selected group validates."""
    validated_count = int(candidate_validation["ValidationStatus"].eq("PASS").sum())
    total_count = int(len(candidate_validation))
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    specs = [
        ("FETCH", "FETCH-VDF", "1.1", "SOURCE_REPORTED_SOURCED_UNVERIFIED", "PASS_WITH_UNVERIFIED_SOURCE", ""),
        ("CLASSIFY", "CLASSIFY-VIA-TAX", "2.1", "DERIVED", "CANDIDATE_REVIEW", "CANONICAL_MUTATION_PROHIBITED"),
        ("VALIDATE", "M-01/M-02/M-03", "1.1", "UNAVAILABLE", "BLOCKED", f"validated={validated_count}/{total_count}"),
        ("INDEX", "M-05", "1.1", "DERIVED", "BLOCKED", "VALIDATE_NOT_PASS"),
        ("OBSERVE", "M-06/M-07", "1.1", "UNAVAILABLE", "BLOCKED", "INDEX_NOT_GENERATED"),
        ("FLOW", "M-08/M-09", "1.1", "UNAVAILABLE", "BLOCKED", "CANONICAL_FLOW_SOURCE_NOT_CONNECTED"),
    ]
    rows: list[dict[str, Any]] = []
    inherited = "MEASURED"
    upstream_ids: list[str] = []
    for stage, method_id, method_version, own_tier, status, block_reason in specs:
        inherited = def_weakest_evidence(inherited, own_tier)
        payload = {
            "Stage": stage,
            "MethodId": method_id,
            "MethodVersion": method_version,
            "SourceRefs": source_ref,
            "AsOfDate": asof_date,
            "OwnEvidenceTier": own_tier,
            "InheritedEvidenceTier": inherited,
            "Status": status,
            "BlockReason": block_reason,
            "UpstreamArtifactIds": upstream_ids.copy(),
            "ParametersDigest": parameters_digest,
        }
        artifact_id = _artifact_id(stage, payload)
        rows.append({**payload, "ArtifactId": artifact_id, "GeneratedAt": now})
        upstream_ids = [artifact_id]
    return pd.DataFrame(rows)


def def_validate_candidate_groups(
    groups: pd.DataFrame,
    *,
    attention_min: float,
    leadership_min: float,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for row in groups.to_dict(orient="records"):
        attention = row.get("SourceReportedAttentionScore")
        leadership = row.get("SourceReportedLeadershipScore")
        if row.get("InputIntegrityStatus") != "PASS":
            status = "BLOCKED_INPUT_INTEGRITY"
            reason = str(row.get("InputIntegrityStatus"))
        elif pd.isna(attention) or pd.isna(leadership):
            status = "BLOCKED_VDF_REQUIRED"
            reason = "ATTENTION_OR_LEADERSHIP_MISSING"
        elif float(attention) < attention_min or float(leadership) < leadership_min:
            status = "BLOCKED_THRESHOLD"
            reason = "ATTENTION_AND_OR_LEADERSHIP_BELOW_SSOT"
        else:
            status = "BLOCKED_MISSING_STATISTICAL_EVIDENCE"
            reason = "PCA_CCF_PERMUTATION_NOT_VERIFIED"
        rows.append(
            {
                **row,
                "AttentionThreshold": attention_min,
                "LeadershipThreshold": leadership_min,
                "ValidationStatus": "PASS" if status == "PASS" else status,
                "IndexGenerationStatus": "ELIGIBLE" if status == "PASS" else "BLOCKED",
                "BlockReason": reason,
            }
        )
    return pd.DataFrame(rows)
