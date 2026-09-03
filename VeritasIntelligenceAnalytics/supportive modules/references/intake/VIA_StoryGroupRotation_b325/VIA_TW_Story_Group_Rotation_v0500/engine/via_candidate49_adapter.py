from __future__ import annotations

"""Adapter that promotes the 49-group file from UI queue to validation cohort.

Source-reported roles and numeric scores are retained only in the untouched
source file.  Runtime classification never consumes those fields.  Statistical
validation may run on a candidate before it is approved for index inclusion;
index membership remains fail-closed until a separate approval event exists.
"""

# =============================================================================
# def 00 PARAMETERS
# =============================================================================

import hashlib
from typing import Any

import pandas as pd


ENGINE_ID = "VIA_CANDIDATE49_ADAPTER_V0500"
ENGINE_VERSION = "0.5.0"
EXPECTED_GROUP_COUNT = 49
EXPECTED_MEMBERSHIP_ROWS = 252
EXPECTED_DISTINCT_TICKERS = 241

REQUIRED_COLUMNS = {
    "CandidateGroupId",
    "GroupName",
    "Ticker",
    "Name",
    "Market",
    "CandidateRole",
    "SourceVersion",
    "EvidenceTier",
    "VerificationIssue",
}


def def_ticker_base(value: object) -> str:
    text = str(value or "").strip().upper()
    return text.removesuffix(".TW").removesuffix(".TWO")


def def_normalize_ticker(value: object, market: object) -> str:
    text = str(value or "").strip().upper()
    if text.endswith((".TW", ".TWO")):
        return text
    return def_ticker_base(text) + (".TWO" if str(market).strip().upper() == "TPEX" else ".TW")


def def_membership_id(group_id: str, ticker: str, proposed_at: pd.Timestamp) -> str:
    payload = f"{group_id}|{ticker}|{proposed_at.isoformat()}"
    return "VIA-MBR-C49-" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:18].upper()


def def_prepare_candidate49(
    raw: pd.DataFrame,
    proposed_at: str | pd.Timestamp,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    missing = sorted(REQUIRED_COLUMNS.difference(raw.columns))
    if missing:
        raise ValueError(f"candidate49 input missing required columns: {missing}")
    frame = raw.copy()
    frame["GroupId"] = frame["CandidateGroupId"].astype(str).str.strip()
    frame["Ticker"] = [
        def_normalize_ticker(ticker, market)
        for ticker, market in zip(frame["Ticker"], frame["Market"], strict=False)
    ]
    frame["TickerBase"] = frame["Ticker"].map(def_ticker_base)
    frame["ProposedAt"] = pd.Timestamp(proposed_at)
    frame["L1"] = "TAIWAN_STORY_THEMES"
    frame["L2"] = frame["GroupName"].astype(str).str.strip()
    frame["L3"] = "UNSPECIFIED_REQUIRES_STORY_FUNCTION_REVIEW"
    frame["CandidateRolePrior"] = frame["CandidateRole"].astype(str).str.upper()
    issue = frame["VerificationIssue"].fillna("").astype(str).str.strip()
    duplicate = frame.duplicated(["GroupId", "Ticker"], keep=False)
    frame["IntakeStatus"] = "PASS_VALIDATION_COHORT"
    frame.loc[issue.ne(""), "IntakeStatus"] = "BLOCKED_SOURCE_VERIFICATION_ISSUE"
    frame.loc[duplicate, "IntakeStatus"] = "BLOCKED_DUPLICATE_GROUP_TICKER_CONFLICT"
    frame["ValidationEligible"] = frame["IntakeStatus"].eq("PASS_VALIDATION_COHORT")
    frame["IndexEligible"] = False
    frame["Decision"] = "PROPOSED"
    frame["DecisionStatus"] = "AWAITING_STATISTICAL_VALIDATION_AND_HUMAN_APPROVAL"
    frame["MembershipId"] = [
        def_membership_id(group, ticker, pd.Timestamp(proposed_at))
        for group, ticker in zip(frame["GroupId"], frame["Ticker"], strict=False)
    ]
    keep = [
        "MembershipId",
        "GroupId",
        "GroupName",
        "L1",
        "L2",
        "L3",
        "Ticker",
        "TickerBase",
        "Name",
        "Market",
        "CandidateRolePrior",
        "ProposedAt",
        "Decision",
        "DecisionStatus",
        "ValidationEligible",
        "IndexEligible",
        "IntakeStatus",
        "EvidenceTier",
        "SourceVersion",
        "VerificationIssue",
    ]
    output = frame[keep].copy()
    audit = {
        "GroupCount": int(output["GroupId"].nunique()),
        "MembershipRows": int(len(output)),
        "DistinctTickers": int(output["Ticker"].nunique()),
        "MultiGroupTickerCount": int(output.groupby("Ticker")["GroupId"].nunique().gt(1).sum()),
        "BlockedRows": int((~output["ValidationEligible"]).sum()),
        "CandidateRolesConsumedByRuntime": 0,
        "IndexEligibleBeforeApproval": int(output["IndexEligible"].sum()),
    }
    audit["DeclaredShapeMatches"] = (
        audit["GroupCount"] == EXPECTED_GROUP_COUNT
        and audit["MembershipRows"] == EXPECTED_MEMBERSHIP_ROWS
        and audit["DistinctTickers"] == EXPECTED_DISTINCT_TICKERS
    )
    return output, audit


def def_validation_cohort(candidate: pd.DataFrame) -> pd.DataFrame:
    """Return statistically testable rows without pretending they are approved."""

    required = {"ValidationEligible", "GroupId", "Ticker"}
    missing = sorted(required.difference(candidate.columns))
    if missing:
        raise ValueError(f"candidate cohort missing required columns: {missing}")
    return candidate.loc[candidate["ValidationEligible"]].copy().reset_index(drop=True)
