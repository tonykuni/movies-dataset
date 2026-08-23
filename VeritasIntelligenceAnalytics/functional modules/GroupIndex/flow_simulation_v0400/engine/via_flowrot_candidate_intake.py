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
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


CANDIDATE_SOURCE_NAME = "3d616edd-3f96-44cf-9e5d-c885bf414120.html"
CANDIDATE_SOURCE_VERSION = "ATTACHED_FLOWROT_V21_2026-08-18"
CANDIDATE_ID_POLICY = "NONCANONICAL_CANDIDATE_ID"
ROLE_MAP = {"L": "LEADER", "P": "PEER", "G": "LAGGARD"}
MARKET_MAP = {"上市": ("TWSE", ".TW"), "上櫃": ("TPEX", ".TWO")}
EXPECTED_MISSING_VDF = {"半導體設備", "資安/系統整合", "觀光餐飲", "ASIC 設計服務"}

DEVILS_ADVOCATE_EXCLUSIONS = [
    {"Topic": "量子科技", "Reason": "無乾淨上市純概念龍頭；曝險分散且無法形成可靠 L/P/G。"},
    {"Topic": "矽光子", "Reason": "與 CPO 共封裝光學高度重疊，分立會稀釋群內同步性。"},
    {"Topic": "HDD / SSD 儲存", "Reason": "核心標的已歸記憶體，另立會造成雙重歸屬污染廣度。"},
    {"Topic": "無人機", "Reason": "上市純標的不足，暫留軍工航太子群。"},
    {"Topic": "智慧眼鏡 / AR / AI PC", "Reason": "多為光學、PCB、ODM 子集，避免重複計數與題材稀釋。"},
]

ERRATA = [
    {"Key": "2301", "Correction": "2301 為光寶科，不是台達電；台達電代碼為 2308。"},
    {"Key": "2308", "Correction": "允許機器人與電源管理多群歸屬；全市場 breadth 以唯一代碼去重。"},
    {"Key": "GROUP_COLOR", "Correction": "航運顏色鍵統一拆為貨櫃航運與散裝航運。"},
]


def _decode_bundled_template(path: Path) -> str:
    outer = path.read_text(encoding="utf-8")
    match = re.search(r'<script type="__bundler/template">\s*(".*")\s*</script>', outer, re.S)
    if not match:
        raise ValueError(f"Bundled template payload not found: {path}")
    return json.loads(match.group(1))


def _extract_json_array(template: str, method_name: str = "_groups()") -> list[Any]:
    method_start = template.find(method_name)
    if method_start < 0:
        raise ValueError(f"{method_name} not found in bundled template")
    start = template.find("[", method_start)
    if start < 0:
        raise ValueError("Candidate group array opening bracket not found")
    depth = 0
    in_string = False
    escaped = False
    for index in range(start, len(template)):
        char = template[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "[":
            depth += 1
        elif char == "]":
            depth -= 1
            if depth == 0:
                return json.loads(template[start : index + 1])
    raise ValueError("Candidate group array closing bracket not found")


def def_extract_flowrot_candidate(
    source_path: Path,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    """Extract the attached 49-group proposal without mutating canonical membership."""
    raw_groups = _extract_json_array(_decode_bundled_template(source_path))
    group_rows: list[dict[str, Any]] = []
    member_rows: list[dict[str, Any]] = []
    for ordinal, group in enumerate(raw_groups, start=1):
        if not isinstance(group, list) or len(group) != 5:
            raise ValueError(f"Unexpected candidate group shape at row {ordinal}: {group!r}")
        group_name, attention, leadership, change_1d, members = group
        candidate_id = f"C49-{ordinal:03d}"
        evidence = (
            "VDF_REQUIRED"
            if attention is None or leadership is None
            else "SOURCE_REPORTED_SOURCED_UNVERIFIED"
        )
        group_rows.append(
            {
                "CandidateGroupId": candidate_id,
                "GroupName": str(group_name),
                "SourceReportedAttentionScore": attention,
                "SourceReportedLeadershipScore": leadership,
                "SourceReportedChange1D": change_1d,
                "EvidenceTier": evidence,
                "CandidateIdPolicy": CANDIDATE_ID_POLICY,
                "SourceVersion": CANDIDATE_SOURCE_VERSION,
                "CanonicalMutation": 0,
            }
        )
        for member in members:
            if not isinstance(member, list) or len(member) != 7:
                raise ValueError(f"Unexpected candidate member shape in {group_name}: {member!r}")
            name, code, market_label, source_role, score_1, score_2, change = member
            if market_label not in MARKET_MAP:
                raise ValueError(f"Unknown market label {market_label!r} for {code}")
            if source_role not in ROLE_MAP:
                raise ValueError(f"Unknown role {source_role!r} for {code}")
            market, suffix = MARKET_MAP[market_label]
            member_rows.append(
                {
                    "CandidateGroupId": candidate_id,
                    "GroupName": str(group_name),
                    "TickerCode": str(code),
                    "Ticker": f"{code}{suffix}",
                    "Name": str(name),
                    "Market": market,
                    "MarketLabel": market_label,
                    "CandidateRole": ROLE_MAP[source_role],
                    "SizeTier": "NEEDS_FETCH",
                    "SizeBucketPolicy": "ROLLING_MARKET_CAP_P90_P60_QUARTERLY_APPEND_ONLY",
                    "CapitalControlStyle": "NEEDS_FETCH",
                    "SourceReportedMemberScore1": score_1,
                    "SourceReportedMemberScore2": score_2,
                    "SourceReportedChange1D": change,
                    "EvidenceTier": evidence,
                    "CandidateIdPolicy": CANDIDATE_ID_POLICY,
                    "SourceVersion": CANDIDATE_SOURCE_VERSION,
                    "CanonicalMutation": 0,
                }
            )
    groups = pd.DataFrame(group_rows)
    members = pd.DataFrame(member_rows)
    duplicate_mask = members.duplicated(["CandidateGroupId", "TickerCode"], keep=False)
    duplicate_rows = int(members.duplicated(["CandidateGroupId", "TickerCode"]).sum())
    members["VerificationIssue"] = ""
    members.loc[duplicate_mask, "VerificationIssue"] = "DUPLICATE_GROUP_TICKER_CONFLICT"
    duplicate_group_ids = set(members.loc[duplicate_mask, "CandidateGroupId"])
    groups["InputIntegrityStatus"] = np.where(
        groups["CandidateGroupId"].isin(duplicate_group_ids),
        "BLOCKED_DUPLICATE_GROUP_TICKER",
        "PASS",
    )
    ticker_counts = members.groupby("TickerCode")["CandidateGroupId"].nunique()
    missing_vdf = set(groups.loc[groups["EvidenceTier"] == "VDF_REQUIRED", "GroupName"])
    quality: dict[str, Any] = {
        "SourceFile": source_path.name,
        "SourceVersion": CANDIDATE_SOURCE_VERSION,
        "EvidenceInterpretation": "SOURCE_REPORTED_SOURCED_UNVERIFIED_NOT_MEASURED",
        "GroupCount": int(len(groups)),
        "MembershipRows": int(len(members)),
        "DistinctTickers": int(members["TickerCode"].nunique()),
        "DuplicateGroupTickerRows": duplicate_rows,
        "DuplicateDetails": members.loc[
            duplicate_mask,
            ["CandidateGroupId", "GroupName", "TickerCode", "Name", "CandidateRole"],
        ].to_dict(orient="records"),
        "MultiGroupTickerCount": int((ticker_counts > 1).sum()),
        "RoleCounts": dict(Counter(members["CandidateRole"])),
        "MarketCounts": dict(Counter(members["Market"])),
        "MissingVDFGroups": sorted(missing_vdf),
        "MissingVDFGroupsMatchDeclared": missing_vdf == EXPECTED_MISSING_VDF,
        "CandidateIdPolicy": CANDIDATE_ID_POLICY,
        "CanonicalMutation": 0,
        "DevilsAdvocateExclusions": DEVILS_ADVOCATE_EXCLUSIONS,
        "Errata": ERRATA,
    }
    return groups, members, quality


def def_validate_flowrot_candidate(
    groups: pd.DataFrame,
    members: pd.DataFrame,
    quality: dict[str, Any],
) -> None:
    expected = {
        "GroupCount": 49,
        "MembershipRows": 252,
        "DistinctTickers": 241,
        "DuplicateGroupTickerRows": 1,
    }
    for key, value in expected.items():
        if quality.get(key) != value:
            raise ValueError(f"Candidate {key} mismatch: {quality.get(key)} != {value}")
    if quality["RoleCounts"] != {"LEADER": 63, "PEER": 126, "LAGGARD": 63}:
        raise ValueError(f"Candidate role counts mismatch: {quality['RoleCounts']}")
    if quality["MarketCounts"] != {"TWSE": 190, "TPEX": 62}:
        raise ValueError(f"Candidate market counts mismatch: {quality['MarketCounts']}")
    if not quality["MissingVDFGroupsMatchDeclared"]:
        raise ValueError(f"Unexpected missing VDF groups: {quality['MissingVDFGroups']}")
    lite_on = members.loc[members["TickerCode"] == "2301", "Name"].drop_duplicates().tolist()
    if lite_on != ["光寶科"]:
        raise ValueError(f"2301 errata failed: {lite_on}")
    delta_groups = set(members.loc[members["TickerCode"] == "2308", "GroupName"])
    if delta_groups != {"機器人", "電源管理"}:
        raise ValueError(f"2308 multi-group ownership mismatch: {sorted(delta_groups)}")
    if groups["CandidateGroupId"].duplicated().any():
        raise ValueError("Candidate group ids are not unique")


def def_write_flowrot_candidate(
    source_path: Path,
    input_dir: Path,
    evidence_dir: Path,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    groups, members, quality = def_extract_flowrot_candidate(source_path)
    def_validate_flowrot_candidate(groups, members, quality)
    input_dir.mkdir(parents=True, exist_ok=True)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    groups.to_csv(input_dir / "candidate_group_metrics_v21.csv", index=False, encoding="utf-8-sig")
    members.to_csv(input_dir / "candidate_membership_v21.csv", index=False, encoding="utf-8-sig")
    (evidence_dir / "candidate_49_quality.json").write_text(
        json.dumps(quality, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return groups, members, quality
