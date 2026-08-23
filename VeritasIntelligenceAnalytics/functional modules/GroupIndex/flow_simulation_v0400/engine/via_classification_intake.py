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

import ast
import html
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import pandas as pd


# =============================================================================
# PARAMETERS · attachment intake is read-only and never mutates canonical SSOT
# =============================================================================
CORE_GROUP_COUNT = 31
CORE_MEMBER_ROWS = 149
ALLOWED_CANDIDATE_ROLES = {"LEADER", "PEER", "LAGGARD"}
SOURCE_HTML_NAME = "554d172e-eb27-4209-906d-d25c6a4a5316.html"
MARKET_SOURCE_NAMES = (
    "8bd5bc08-9d82-4fb1-98d0-1763f5210a27.py",
    "9df6891b-d309-4af6-bc58-a21b2907308e.py",
)
TICKER_CODE_PATTERN = re.compile(r"^[1-9][0-9]{3}$")


def def_clean_html_text(value: str) -> str:
    without_tags = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", html.unescape(without_tags)).strip()


def def_literal_dict_from_python(path: Path) -> list[dict[str, Any]]:
    """Read literal taxonomy dictionaries without importing or executing source."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (SyntaxError, UnicodeError):
        return []
    values: list[dict[str, Any]] = []
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(
            isinstance(target, ast.Name)
            and target.id in {"PURIFIED_SECTOR_MATRIX_V2", "VIA_TAXONOMY_V1_1"}
            for target in node.targets
        ):
            continue
        try:
            payload = ast.literal_eval(node.value)
        except (ValueError, TypeError, SyntaxError):
            continue
        if isinstance(payload, dict):
            values.append(payload)
    return values


def def_build_market_lookup(reference_dir: Path) -> dict[str, tuple[str, str, bool]]:
    candidates: defaultdict[str, list[tuple[str, str]]] = defaultdict(list)
    for source_name in MARKET_SOURCE_NAMES:
        source_path = reference_dir / source_name
        if not source_path.exists():
            continue
        for taxonomy in def_literal_dict_from_python(source_path):
            for members in taxonomy.values():
                if not isinstance(members, list):
                    continue
                for member in members:
                    if not isinstance(member, dict):
                        continue
                    raw_ticker = str(member.get("ticker", "")).strip().upper()
                    code = raw_ticker.split(".")[0]
                    raw_market = str(member.get("market", "")).strip().upper()
                    suffix = raw_ticker.split(".", 1)[1] if "." in raw_ticker else raw_market
                    if not TICKER_CODE_PATTERN.fullmatch(code):
                        continue
                    market = "TPEX" if suffix in {"TWO", "TPEX"} else "TWSE" if suffix in {"TW", "TWSE"} else "REVIEW"
                    if market != "REVIEW":
                        candidates[code].append((market, source_name))
    resolved: dict[str, tuple[str, str, bool]] = {}
    for code, observations in candidates.items():
        counts = Counter(market for market, _ in observations)
        market, frequency = counts.most_common(1)[0]
        verified = frequency == sum(counts.values())
        sources = "+".join(sorted({source for observed_market, source in observations if observed_market == market}))
        resolved[code] = (market, sources, verified)
    return resolved


def def_extract_candidate_membership(source_html: Path, reference_dir: Path) -> tuple[pd.DataFrame, dict[str, Any]]:
    source = source_html.read_text(encoding="utf-8")
    group_blocks = re.findall(r'<details class="grp">(.*?)</details>', source, flags=re.DOTALL)[:CORE_GROUP_COUNT]
    market_lookup = def_build_market_lookup(reference_dir)
    rows: list[dict[str, Any]] = []
    for group_number, block in enumerate(group_blocks, start=1):
        name_match = re.search(r'<span class="gnm">(.*?)</span>', block, flags=re.DOTALL)
        body_match = re.search(r"<tbody>(.*?)</tbody>", block, flags=re.DOTALL)
        if not name_match or not body_match:
            continue
        group_name = def_clean_html_text(name_match.group(1))
        member_rows = re.findall(r"<tr>(.*?)</tr>", body_match.group(1), flags=re.DOTALL)
        for member_row in member_rows:
            cells = re.findall(r"<td[^>]*>(.*?)</td>", member_row, flags=re.DOTALL)
            if len(cells) < 3:
                continue
            code, member_name, role = (def_clean_html_text(cell) for cell in cells[:3])
            market, market_source, market_verified = market_lookup.get(
                code,
                ("REVIEW", "FIXTURE_DEFAULT_TW_NOT_VERIFIED", False),
            )
            suffix = ".TWO" if market == "TPEX" else ".TW"
            rows.append(
                {
                    "GroupId": f"TWG{group_number:03d}",
                    "GroupName": group_name,
                    "Ticker": f"{code}{suffix}",
                    "TickerCode": code,
                    "Name": member_name,
                    "CandidateRole": role,
                    "IndexEligible": True,
                    "FlowEligible": True,
                    "DisplayOnly": False,
                    "PrimaryEconomicIdentity": group_name,
                    "Market": market,
                    "MarketVerified": market_verified,
                    "MarketSource": market_source,
                    "UITier": "STANDARD",
                    "SourceVersion": "ATTACHED_31_GROUP_149_CANDIDATE_REVIEW",
                }
            )
    membership = pd.DataFrame(rows)
    if not membership.empty:
        group_sizes = membership.groupby("GroupId")["Ticker"].transform("size")
        membership["UITier"] = group_sizes.map(lambda size: "WIDE" if size >= 6 else "STANDARD")
    duplicate_pair_count = int(membership.duplicated(["GroupId", "TickerCode"], keep=False).sum()) if not membership.empty else 0
    invalid_ticker_count = int((~membership["TickerCode"].astype(str).str.fullmatch(TICKER_CODE_PATTERN)).sum()) if not membership.empty else 0
    invalid_role_count = int((~membership["CandidateRole"].isin(ALLOWED_CANDIDATE_ROLES)).sum()) if not membership.empty else 0
    multi_group = membership.groupby("TickerCode")["GroupId"].nunique() if not membership.empty else pd.Series(dtype=int)
    quality = {
        "Source": str(source_html),
        "IntakePolicy": "READ_ONLY_CANDIDATE_REVIEW",
        "CanonicalMutation": 0,
        "GroupCount": int(membership["GroupId"].nunique()) if not membership.empty else 0,
        "MembershipRows": int(len(membership)),
        "DistinctTickers": int(membership["TickerCode"].nunique()) if not membership.empty else 0,
        "DuplicateGroupTickerRows": duplicate_pair_count,
        "InvalidTickerRows": invalid_ticker_count,
        "InvalidRoleRows": invalid_role_count,
        "MultiGroupTickerCount": int((multi_group > 1).sum()),
        "UnverifiedMarketRows": int((~membership["MarketVerified"].astype(bool)).sum()) if not membership.empty else 0,
        "RoleCounts": membership["CandidateRole"].value_counts().to_dict() if not membership.empty else {},
        "ExpectedGroupCount": CORE_GROUP_COUNT,
        "ExpectedMembershipRows": CORE_MEMBER_ROWS,
    }
    quality["Gate"] = (
        "CANDIDATE_LIST_STRUCTURE_PASS_MARKET_REVIEW_REQUIRED"
        if quality["GroupCount"] == CORE_GROUP_COUNT
        and quality["MembershipRows"] == CORE_MEMBER_ROWS
        and duplicate_pair_count == 0
        and invalid_ticker_count == 0
        and invalid_role_count == 0
        else "FAIL_CLOSED_CANDIDATE_LIST_STRUCTURE"
    )
    if quality["Gate"].startswith("FAIL_CLOSED"):
        raise ValueError(f"Classification candidate list failed structure gate: {json.dumps(quality, ensure_ascii=False)}")
    return membership.sort_values(["GroupId", "CandidateRole", "TickerCode"]).reset_index(drop=True), quality


def def_write_candidate_membership(project_root: Path, output_path: Path) -> dict[str, Any]:
    reference_dir = project_root / "references" / "intake"
    membership, quality = def_extract_candidate_membership(reference_dir / SOURCE_HTML_NAME, reference_dir)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    membership.to_csv(output_path, index=False, encoding="utf-8-sig")
    evidence_path = project_root / "evidence" / "classification_candidate_quality.json"
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text(json.dumps(quality, ensure_ascii=False, indent=2), encoding="utf-8")
    return quality
