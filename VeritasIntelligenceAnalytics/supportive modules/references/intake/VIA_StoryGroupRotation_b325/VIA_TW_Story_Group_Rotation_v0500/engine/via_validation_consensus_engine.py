from __future__ import annotations

"""Robustness reconciliation and human-review queues for group validation.

The engine never averages p-values, correlations or roles.  It keeps every
factor/window result intact and uses conservative agreement rules only to form
a review status.  No membership is changed automatically.
"""

from dataclasses import dataclass
from typing import Any

import pandas as pd


ENGINE_ID = "VIA_VALIDATION_CONSENSUS_V0500"
ENGINE_VERSION = "0.5.0"
EXPECTED_FACTOR_LANES = ("LaggedCap", "LaggedETR")
EXPECTED_WINDOWS = (60, 120, 240)
MEMBER_ROLES = ("LEAD", "PEER", "LAG", "UNRELATED")


@dataclass(frozen=True)
class ValidationConsensusConfig:
    factor_lanes: tuple[str, ...] = EXPECTED_FACTOR_LANES
    windows: tuple[int, ...] = EXPECTED_WINDOWS


def def_reconcile_group_decisions(
    group_validation: pd.DataFrame,
    config: ValidationConsensusConfig = ValidationConsensusConfig(),
) -> pd.DataFrame:
    required = {
        "SnapshotDate",
        "Window",
        "GroupId",
        "GroupDecision",
        "EvidenceStatus",
        "ResidualFactorLane",
    }
    missing = sorted(required.difference(group_validation.columns))
    if missing:
        raise ValueError(f"group validation consensus missing columns: {missing}")
    frame = group_validation.copy()
    frame["SnapshotDate"] = pd.to_datetime(frame["SnapshotDate"], errors="coerce").dt.normalize()
    frame["Window"] = pd.to_numeric(frame["Window"], errors="coerce").astype("Int64")
    duplicate = frame.duplicated(
        ["SnapshotDate", "Window", "GroupId", "ResidualFactorLane"], keep=False
    )
    if duplicate.any():
        raise ValueError("duplicate factor-lane group validation evidence")

    rows: list[dict[str, Any]] = []
    keys = ["SnapshotDate", "Window", "GroupId"]
    for key, group in frame.groupby(keys, sort=True, dropna=False):
        snapshot, window, group_id = key
        expected_lanes = set(config.factor_lanes)
        observed_lanes = set(
            group["ResidualFactorLane"].fillna("").astype(str).str.strip()
        )
        missing_lanes = sorted(expected_lanes.difference(observed_lanes))
        unexpected_lanes = sorted(observed_lanes.difference(expected_lanes))
        exact_grid = (
            not missing_lanes
            and not unexpected_lanes
            and len(group) == len(config.factor_lanes)
        )
        decision_values = (
            group["GroupDecision"].fillna("").astype(str).str.strip().str.upper()
        )
        decisions_complete = decision_values.isin({"PASS", "FAIL"}).all()
        decisions = set(decision_values)
        ready = group["EvidenceStatus"].astype(str).str.upper().eq("READY").all()
        if unexpected_lanes:
            robust = "HOLD"
            status = "HOLD_UNEXPECTED_FACTOR_LANE"
        elif missing_lanes or not exact_grid:
            robust = "HOLD"
            status = "HOLD_MISSING_FACTOR_LANE"
        elif not ready:
            robust = "HOLD"
            status = "HOLD_BLOCKED_FACTOR_EVIDENCE"
        elif not decisions_complete:
            robust = "HOLD"
            status = "HOLD_INVALID_OR_MISSING_GROUP_DECISION"
        elif decisions == {"PASS"}:
            robust = "PASS"
            status = "PASS_BOTH_RESIDUAL_MODELS"
        elif decisions == {"FAIL"}:
            robust = "FAIL"
            status = "FAIL_BOTH_RESIDUAL_MODELS"
        else:
            robust = "HOLD"
            status = "HOLD_RESIDUAL_MODEL_DISAGREEMENT"
        rows.append(
            {
                "SnapshotDate": snapshot,
                "Window": int(window),
                "GroupId": group_id,
                "GroupName": group["GroupName"].iloc[0] if "GroupName" in group else group_id,
                "RobustGroupDecision": robust,
                "GroupConsensusStatus": status,
                "ObservedFactorLanes": "|".join(sorted(observed_lanes)),
                "MissingFactorLanes": "|".join(missing_lanes),
                "UnexpectedFactorLanes": "|".join(unexpected_lanes),
                "ReconciliationPolicy": "INTERSECTION_AGREEMENT_NO_NUMERIC_AGGREGATION",
            }
        )
    return pd.DataFrame(rows).sort_values(["SnapshotDate", "Window", "GroupId"]).reset_index(drop=True)


def def_reconcile_member_roles(
    member_roles: pd.DataFrame,
    group_consensus: pd.DataFrame,
    config: ValidationConsensusConfig = ValidationConsensusConfig(),
) -> pd.DataFrame:
    required = {
        "SnapshotDate",
        "Window",
        "GroupId",
        "Ticker",
        "Role",
        "EvidenceStatus",
        "ResidualFactorLane",
    }
    missing = sorted(required.difference(member_roles.columns))
    if missing:
        raise ValueError(f"member role consensus missing columns: {missing}")
    frame = member_roles.copy()
    frame["SnapshotDate"] = pd.to_datetime(frame["SnapshotDate"], errors="coerce").dt.normalize()
    frame["Window"] = pd.to_numeric(frame["Window"], errors="coerce").astype("Int64")
    duplicate = frame.duplicated(
        ["SnapshotDate", "Window", "GroupId", "Ticker", "ResidualFactorLane"],
        keep=False,
    )
    if duplicate.any():
        raise ValueError("duplicate factor-lane member role evidence")
    group_lookup = group_consensus.set_index(["SnapshotDate", "Window", "GroupId"])
    rows: list[dict[str, Any]] = []
    keys = ["SnapshotDate", "Window", "GroupId", "Ticker"]
    for key, group in frame.groupby(keys, sort=True, dropna=False):
        snapshot, window, group_id, ticker = key
        group_key = (snapshot, window, group_id)
        if group_key not in group_lookup.index:
            raise ValueError(f"member evidence has no group consensus row: {group_key}")
        robust_group = str(group_lookup.loc[group_key, "RobustGroupDecision"])
        expected_lanes = set(config.factor_lanes)
        observed_lanes = set(
            group["ResidualFactorLane"].fillna("").astype(str).str.strip()
        )
        missing_lanes = sorted(expected_lanes.difference(observed_lanes))
        unexpected_lanes = sorted(observed_lanes.difference(expected_lanes))
        exact_grid = (
            not missing_lanes
            and not unexpected_lanes
            and len(group) == len(config.factor_lanes)
        )
        ready = group["EvidenceStatus"].astype(str).str.upper().eq("READY").all()
        role_values = group["Role"].fillna("").astype(str).str.strip().str.upper()
        roles_complete = role_values.isin(MEMBER_ROLES).all()
        roles = set(role_values)
        if unexpected_lanes:
            role = pd.NA
            status = "HOLD_UNEXPECTED_FACTOR_LANE"
        elif missing_lanes or not exact_grid:
            role = pd.NA
            status = "HOLD_MISSING_FACTOR_LANE"
        elif robust_group != "PASS":
            role = pd.NA
            status = "HOLD_GROUP_NOT_ROBUST_PASS"
        elif not ready:
            role = pd.NA
            status = "HOLD_BLOCKED_MEMBER_EVIDENCE"
        elif not roles_complete:
            role = pd.NA
            status = "HOLD_INVALID_OR_MISSING_MEMBER_ROLE"
        elif len(roles) == 1 and roles.issubset(MEMBER_ROLES):
            role = next(iter(roles))
            status = "PASS_ROLE_AGREES_ACROSS_RESIDUAL_MODELS"
        else:
            role = pd.NA
            status = "HOLD_ROLE_MODEL_DISAGREEMENT"
        rows.append(
            {
                "SnapshotDate": snapshot,
                "Window": int(window),
                "GroupId": group_id,
                "Ticker": ticker,
                "RoleConsensus": role,
                "RoleConsensusStatus": status,
                "RobustGroupDecision": robust_group,
                "ObservedFactorLanes": "|".join(sorted(observed_lanes)),
                "MissingFactorLanes": "|".join(missing_lanes),
                "UnexpectedFactorLanes": "|".join(unexpected_lanes),
                "ReconciliationPolicy": "EXACT_ROLE_AGREEMENT_NO_VOTE_NO_WEIGHT",
            }
        )
    return pd.DataFrame(rows).sort_values(
        ["SnapshotDate", "Window", "GroupId", "Ticker"]
    ).reset_index(drop=True)


def def_build_membership_review_queue(
    member_consensus: pd.DataFrame,
    membership: pd.DataFrame,
    config: ValidationConsensusConfig = ValidationConsensusConfig(),
) -> pd.DataFrame:
    """Create ADD/REMOVE review candidates; never mutate canonical membership."""

    required = {"GroupId", "Ticker"}
    missing = sorted(required.difference(membership.columns))
    if missing:
        raise ValueError(f"review membership missing columns: {missing}")
    if "EventType" in membership.columns:
        raise ValueError("review queue requires materialized membership, not raw events")
    members = membership.copy()
    if "IndexEligible" not in members:
        members["IndexEligible"] = members.get(
            "Decision", pd.Series("PROPOSED", index=members.index)
        ).astype(str).str.upper().eq("APPROVED")
    latest_snapshot = member_consensus["SnapshotDate"].max()
    evidence = member_consensus.loc[
        member_consensus["SnapshotDate"].eq(latest_snapshot)
    ].copy()
    rows: list[dict[str, Any]] = []
    for _, member in members.drop_duplicates(["GroupId", "Ticker"]).iterrows():
        history = evidence.loc[
            evidence["GroupId"].eq(member["GroupId"])
            & evidence["Ticker"].astype(str).str.replace(r"\.(TW|TWO)$", "", regex=True).eq(
                str(member["Ticker"]).upper().replace(".TWO", "").replace(".TW", "")
            )
        ]
        observed_windows = set(pd.to_numeric(history["Window"], errors="coerce").dropna().astype(int))
        complete = set(config.windows).issubset(observed_windows)
        selected = history.loc[history["Window"].isin(config.windows)]
        all_group_pass = complete and selected["RobustGroupDecision"].eq("PASS").all()
        roles = selected["RoleConsensus"].dropna().astype(str).str.upper()
        approved = bool(member["IndexEligible"])
        if approved and all_group_pass and len(roles) == len(config.windows) and roles.eq("UNRELATED").all():
            action = "REMOVE_CANDIDATE"
            status = "AWAITING_HUMAN_APPROVAL"
        elif (not approved) and all_group_pass and len(roles) == len(config.windows) and roles.isin({"LEAD", "PEER", "LAG"}).all():
            action = "ADD_REVIEW_CANDIDATE"
            status = "AWAITING_HUMAN_APPROVAL"
        else:
            action = "NO_ACTION"
            status = "HOLD_NO_ROBUST_ALL_WINDOW_EVIDENCE"
        rows.append(
            {
                "SnapshotDate": latest_snapshot,
                "GroupId": member["GroupId"],
                "Ticker": member["Ticker"],
                "CurrentIndexEligible": approved,
                "ObservedWindows": "|".join(map(str, sorted(observed_windows))),
                "ReviewAction": action,
                "ReviewStatus": status,
                "AutomaticCanonicalMutation": False,
                "EarliestEffect": "NEXT_TRADING_SESSION_AFTER_EXPLICIT_APPROVAL",
            }
        )
    return pd.DataFrame(rows).sort_values(["ReviewAction", "GroupId", "Ticker"]).reset_index(drop=True)


def def_run_self_test() -> dict[str, Any]:
    group_rows: list[dict[str, Any]] = []
    member_rows: list[dict[str, Any]] = []
    for window in EXPECTED_WINDOWS:
        for lane in EXPECTED_FACTOR_LANES:
            group_rows.append(
                {
                    "SnapshotDate": "2026-01-05",
                    "Window": window,
                    "GroupId": "G1",
                    "GroupName": "CPO",
                    "GroupDecision": "PASS",
                    "EvidenceStatus": "READY",
                    "ResidualFactorLane": lane,
                }
            )
            member_rows.append(
                {
                    "SnapshotDate": "2026-01-05",
                    "Window": window,
                    "GroupId": "G1",
                    "Ticker": "9999",
                    "Role": "UNRELATED",
                    "EvidenceStatus": "READY",
                    "ResidualFactorLane": lane,
                }
            )
    groups = def_reconcile_group_decisions(pd.DataFrame(group_rows))
    members = def_reconcile_member_roles(pd.DataFrame(member_rows), groups)
    queue = def_build_membership_review_queue(
        members,
        pd.DataFrame(
            [{"GroupId": "G1", "Ticker": "9999.TW", "IndexEligible": True}]
        ),
    )
    assert groups["RobustGroupDecision"].eq("PASS").all()
    assert members["RoleConsensus"].eq("UNRELATED").all()
    assert queue["ReviewAction"].eq("REMOVE_CANDIDATE").all()
    assert not queue["AutomaticCanonicalMutation"].any()
    assert not any("score" in column.lower() for frame in (groups, members, queue) for column in frame.columns)
    return {"Status": "PASS", "GroupRows": len(groups), "MemberRows": len(members), "QueueRows": len(queue)}


if __name__ == "__main__":
    print(def_run_self_test())
