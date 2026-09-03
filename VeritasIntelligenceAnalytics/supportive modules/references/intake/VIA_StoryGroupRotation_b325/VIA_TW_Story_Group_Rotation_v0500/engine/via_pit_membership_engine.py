from __future__ import annotations

"""Point-in-time story-group membership ledger.

The ledger is event based.  A stock may belong to more than one story group, but
the same ``GroupId + Ticker`` relationship has one independent event stream.
Approved changes become effective on the first trading session strictly after
the approval date (or a later requested ``ValidFrom`` session).
"""

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping

import numpy as np
import pandas as pd


# =============================================================================
# PARAMETERS
# =============================================================================
ENGINE_ID = "VIA_PIT_STORY_MEMBERSHIP_ENGINE"
ENGINE_VERSION = "0.5.0"
APPROVAL_TIMEZONE = "Asia/Taipei"
VALID_TO_POLICY = "INCLUSIVE"
EVENT_HASH_ALGORITHM = "SHA256"
EVENT_ID_DIGEST_BYTES = 8
EVENT_TYPES = ("ADD", "REMOVE", "KEEP")
APPROVAL_STATUSES = ("PENDING", "APPROVED", "REJECTED")
APPROVED_STATUS = "APPROVED"
KNOWLEDGE_TIMESTAMP_COLUMNS = (
    "ApprovedAt",
    "RecordedAt",
    "KnownAt",
    "AvailableAt",
    "IngestedAt",
)
TICKER_SUFFIXES = (".TW", ".TWO")
EMPTY_HASH = "0" * 64
REQUIRED_EVENT_COLUMNS = (
    "EventType",
    "GroupId",
    "GroupName",
    "Ticker",
    "ApprovedAt",
    "ValidFrom",
    "ValidTo",
)
OPTIONAL_EVENT_DEFAULTS: dict[str, Any] = {
    "EventId": "",
    "Sequence": pd.NA,
    "ApprovalStatus": "PENDING",
    "Reason": "",
    "SourceVersion": "UNSPECIFIED",
    "SupersedesEventId": "",
    "RecordedAt": "",
    "KnownAt": "",
    "AvailableAt": "",
    "IngestedAt": "",
    "PreviousLedgerHash": "",
    "LedgerHash": "",
    # Optional audited story exposure.  It is never inferred here; downstream
    # conserved views use it only when every active assignment is complete.
    "ExposureShare": np.nan,
}
HASH_FIELDS = (
    "Sequence",
    "EventId",
    "EventType",
    "GroupId",
    "GroupName",
    "Ticker",
    "ApprovalStatus",
    "ApprovedAt",
    "ValidFrom",
    "ValidTo",
    "EffectiveDate",
    "ExposureShare",
    "Reason",
    "SourceVersion",
    "SupersedesEventId",
    "RecordedAt",
    "KnownAt",
    "AvailableAt",
    "IngestedAt",
    "EventKnownAt",
)
MATERIALIZED_COLUMNS = (
    "AsOfDate",
    "GroupId",
    "GroupName",
    "Ticker",
    "MembershipValidFrom",
    "MembershipValidTo",
    "ApprovedAt",
    "CurrentEventId",
    "SourceVersion",
    "Reason",
    "EvidenceStatus",
    "ExposureShare",
)


def def_normalize_ticker(value: Any) -> str:
    ticker = str(value).strip().upper().replace(" ", "")
    if ticker.endswith(".TW.TW"):
        ticker = ticker[:-3]
    if ticker.endswith(".TWO.TWO"):
        ticker = ticker[:-4]
    return ticker


def def_prepare_trading_calendar(trading_calendar: Iterable[Any]) -> pd.DatetimeIndex:
    parsed = pd.to_datetime(pd.Index(list(trading_calendar)), errors="coerce")
    parsed = pd.DatetimeIndex(parsed).dropna().tz_localize(None).normalize().unique().sort_values()
    if len(parsed) == 0:
        raise ValueError("trading_calendar contains no valid sessions")
    return parsed


def def_parse_local_timestamp(value: Any) -> pd.Timestamp | pd.NaT:
    if value is None or (isinstance(value, float) and pd.isna(value)) or str(value).strip() == "":
        return pd.NaT
    parsed = pd.Timestamp(value)
    if parsed.tzinfo is None:
        return parsed.tz_localize(APPROVAL_TIMEZONE)
    return parsed.tz_convert(APPROVAL_TIMEZONE)


def def_parse_date(value: Any) -> pd.Timestamp | pd.NaT:
    if value is None or (isinstance(value, float) and pd.isna(value)) or str(value).strip() == "":
        return pd.NaT
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return pd.NaT
    stamp = pd.Timestamp(parsed)
    if stamp.tzinfo is not None:
        stamp = stamp.tz_convert(APPROVAL_TIMEZONE).tz_localize(None)
    return stamp.normalize()


def def_next_trading_session(approved_at: Any, trading_calendar: Iterable[Any]) -> pd.Timestamp | pd.NaT:
    approved = def_parse_local_timestamp(approved_at)
    if pd.isna(approved):
        return pd.NaT
    calendar = def_prepare_trading_calendar(trading_calendar)
    approval_date = approved.tz_localize(None).normalize()
    candidates = calendar[calendar > approval_date]
    return candidates[0] if len(candidates) else pd.NaT


def def_first_session_on_or_after(value: Any, trading_calendar: Iterable[Any]) -> pd.Timestamp | pd.NaT:
    requested = def_parse_date(value)
    if pd.isna(requested):
        return pd.NaT
    calendar = def_prepare_trading_calendar(trading_calendar)
    candidates = calendar[calendar >= requested]
    return candidates[0] if len(candidates) else pd.NaT


def def_effective_session(
    approved_at: Any,
    valid_from: Any,
    trading_calendar: Iterable[Any],
) -> pd.Timestamp | pd.NaT:
    next_session = def_next_trading_session(approved_at, trading_calendar)
    if pd.isna(next_session):
        return pd.NaT
    requested = def_parse_date(valid_from)
    if pd.isna(requested) or requested <= next_session:
        return next_session
    return def_first_session_on_or_after(requested, trading_calendar)


def def_iso_timestamp(value: Any) -> str:
    parsed = def_parse_local_timestamp(value)
    return "" if pd.isna(parsed) else parsed.isoformat()


def def_iso_date(value: Any) -> str:
    parsed = def_parse_date(value)
    return "" if pd.isna(parsed) else parsed.strftime("%Y-%m-%d")


def def_event_known_at(row: Mapping[str, Any]) -> pd.Timestamp | pd.NaT:
    """Return the latest populated timestamp required to know an event.

    A historical approval is not point-in-time visible before it was recorded,
    made available, or ingested.  Optional knowledge gates are enforced only
    when populated; any populated but invalid timestamp fails closed.
    """

    timestamps: list[pd.Timestamp] = []
    for column in KNOWLEDGE_TIMESTAMP_COLUMNS:
        value = row.get(column)
        if value is None or (isinstance(value, float) and pd.isna(value)):
            continue
        if str(value).strip() == "":
            continue
        try:
            parsed = def_parse_local_timestamp(value)
        except (TypeError, ValueError, OverflowError) as error:
            raise ValueError(
                f"invalid membership knowledge timestamp in {column}"
            ) from error
        if pd.isna(parsed):
            raise ValueError(f"invalid membership knowledge timestamp in {column}")
        timestamps.append(pd.Timestamp(parsed))
    return max(timestamps) if timestamps else pd.NaT


def def_build_event_id(row: Mapping[str, Any]) -> str:
    identity = {
        "EventType": str(row.get("EventType", "")).upper(),
        "GroupId": str(row.get("GroupId", "")).strip(),
        "Ticker": def_normalize_ticker(row.get("Ticker", "")),
        "ApprovedAt": def_iso_timestamp(row.get("ApprovedAt")),
        "ValidFrom": def_iso_date(row.get("ValidFrom")),
        "ValidTo": def_iso_date(row.get("ValidTo")),
        "ExposureShare": (
            ""
            if pd.isna(row.get("ExposureShare", np.nan))
            else float(row.get("ExposureShare"))
        ),
        "SourceVersion": str(row.get("SourceVersion", "UNSPECIFIED")),
        "Reason": str(row.get("Reason", "")),
    }
    digest = hashlib.blake2s(
        json.dumps(identity, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8"),
        digest_size=EVENT_ID_DIGEST_BYTES,
    ).hexdigest().upper()
    return f"MEM-{digest}"


def def_hash_event(row: Mapping[str, Any], previous_hash: str) -> str:
    payload = {field: row.get(field, "") for field in HASH_FIELDS}
    canonical = json.dumps(
        {"PreviousLedgerHash": previous_hash, "Event": payload},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest().upper()


def def_normalize_membership_events(
    events: pd.DataFrame,
    trading_calendar: Iterable[Any],
    *,
    build_missing_hash_chain: bool = True,
) -> pd.DataFrame:
    missing = [column for column in REQUIRED_EVENT_COLUMNS if column not in events.columns]
    if missing:
        raise ValueError(f"membership events missing required columns: {missing}")
    calendar = def_prepare_trading_calendar(trading_calendar)
    frame = events.copy().reset_index(drop=True)
    for column, default in OPTIONAL_EVENT_DEFAULTS.items():
        if column not in frame.columns:
            frame[column] = default
    if frame.empty:
        frame["EffectiveDate"] = pd.Series(dtype="object")
        return frame

    frame["EventType"] = frame["EventType"].fillna("").astype(str).str.strip().str.upper()
    frame["GroupId"] = frame["GroupId"].fillna("").astype(str).str.strip()
    frame["GroupName"] = frame["GroupName"].fillna("").astype(str).str.strip()
    frame["Ticker"] = frame["Ticker"].map(def_normalize_ticker)
    frame["ApprovalStatus"] = frame["ApprovalStatus"].fillna("PENDING").astype(str).str.strip().str.upper()
    for column in ["Reason", "SourceVersion", "SupersedesEventId"]:
        frame[column] = frame[column].fillna("").astype(str).str.strip()
    for column in [
        "EventId",
        "RecordedAt",
        "KnownAt",
        "AvailableAt",
        "IngestedAt",
        "PreviousLedgerHash",
        "LedgerHash",
    ]:
        frame[column] = frame[column].fillna("").astype(str).str.strip()

    if frame["Sequence"].isna().any():
        if frame["Sequence"].notna().any():
            raise ValueError("Sequence must be supplied for all rows or none")
        frame["Sequence"] = pd.RangeIndex(1, len(frame) + 1)
    frame["Sequence"] = pd.to_numeric(frame["Sequence"], errors="raise").astype(int)
    frame["ExposureShare"] = pd.to_numeric(frame["ExposureShare"], errors="coerce")
    invalid_exposure = frame["ExposureShare"].notna() & ~frame["ExposureShare"].between(
        0.0, 1.0
    )
    if invalid_exposure.any():
        raise ValueError("ExposureShare must be within [0, 1] when audited")

    frame["ApprovedAt"] = frame["ApprovedAt"].map(def_iso_timestamp)
    frame["ValidFrom"] = frame["ValidFrom"].map(def_iso_date)
    frame["ValidTo"] = frame["ValidTo"].map(def_iso_date)
    frame["RecordedAt"] = frame["RecordedAt"].map(def_iso_timestamp)
    frame["KnownAt"] = frame["KnownAt"].map(def_iso_timestamp)
    frame["AvailableAt"] = frame["AvailableAt"].map(def_iso_timestamp)
    frame["IngestedAt"] = frame["IngestedAt"].map(def_iso_timestamp)
    frame["EventKnownAt"] = frame.apply(
        lambda row: def_iso_timestamp(def_event_known_at(row)), axis=1
    )
    frame["EffectiveDate"] = ""
    approved_mask = frame["ApprovalStatus"].eq(APPROVED_STATUS)
    frame.loc[approved_mask, "EffectiveDate"] = frame.loc[approved_mask].apply(
        lambda row: def_iso_date(def_effective_session(row["ApprovedAt"], row["ValidFrom"], calendar)),
        axis=1,
    )
    frame["EventId"] = frame.apply(
        lambda row: str(row["EventId"]).strip() or def_build_event_id(row), axis=1
    )
    frame = frame.sort_values("Sequence", kind="stable").reset_index(drop=True)

    if build_missing_hash_chain:
        previous = EMPTY_HASH
        previous_values: list[str] = []
        hash_values: list[str] = []
        for row in frame.to_dict(orient="records"):
            supplied_previous = str(row.get("PreviousLedgerHash", "")).strip().upper()
            supplied_hash = str(row.get("LedgerHash", "")).strip().upper()
            if supplied_previous and supplied_previous != previous:
                raise ValueError(
                    f"hash chain previous value mismatch at Sequence={row['Sequence']}"
                )
            calculated = def_hash_event(row, previous)
            if supplied_hash and supplied_hash != calculated:
                raise ValueError(f"hash mismatch at Sequence={row['Sequence']}")
            previous_values.append(previous)
            hash_values.append(calculated)
            previous = calculated
        frame["PreviousLedgerHash"] = previous_values
        frame["LedgerHash"] = hash_values
    return frame


def def_validate_membership_event_chain(events: pd.DataFrame) -> dict[str, Any]:
    if events.empty:
        return {
            "EngineId": ENGINE_ID,
            "EngineVersion": ENGINE_VERSION,
            "Status": "PASS_EMPTY_LEDGER",
            "Rows": 0,
            "ActiveRelationshipStreams": 0,
            "MultiGroupTickerCount": 0,
        }
    required = set(REQUIRED_EVENT_COLUMNS) | {
        "EventId",
        "Sequence",
        "ApprovalStatus",
        "EffectiveDate",
        "EventKnownAt",
        "PreviousLedgerHash",
        "LedgerHash",
    }
    missing = sorted(required.difference(events.columns))
    if missing:
        raise ValueError(f"normalized membership ledger missing columns: {missing}")
    frame = events.sort_values("Sequence", kind="stable").reset_index(drop=True)
    if frame["EventId"].duplicated().any():
        raise ValueError("EventId must be unique")
    expected_sequence = list(range(1, len(frame) + 1))
    if frame["Sequence"].tolist() != expected_sequence:
        raise ValueError("Sequence must be contiguous and append-only from 1")
    invalid_types = sorted(set(frame["EventType"]).difference(EVENT_TYPES))
    invalid_approvals = sorted(set(frame["ApprovalStatus"]).difference(APPROVAL_STATUSES))
    if invalid_types or invalid_approvals:
        raise ValueError(
            f"invalid event contract: EventType={invalid_types}; ApprovalStatus={invalid_approvals}"
        )
    if frame["GroupId"].eq("").any() or frame["GroupName"].eq("").any():
        raise ValueError("GroupId and GroupName cannot be blank")
    if (~frame["Ticker"].str.endswith(TICKER_SUFFIXES)).any():
        bad = frame.loc[~frame["Ticker"].str.endswith(TICKER_SUFFIXES), "Ticker"].tolist()
        raise ValueError(f"unsupported Taiwan ticker suffixes: {bad}")

    previous = EMPTY_HASH
    for row in frame.to_dict(orient="records"):
        expected_known_at = def_iso_timestamp(def_event_known_at(row))
        if str(row["EventKnownAt"]) != expected_known_at:
            raise ValueError(
                f"EventKnownAt does not match knowledge gates at Sequence={row['Sequence']}"
            )
        if str(row["PreviousLedgerHash"]).upper() != previous:
            raise ValueError(f"broken previous hash at Sequence={row['Sequence']}")
        expected = def_hash_event(row, previous)
        if str(row["LedgerHash"]).upper() != expected:
            raise ValueError(f"broken event hash at Sequence={row['Sequence']}")
        previous = expected
        if row["ApprovalStatus"] == APPROVED_STATUS:
            approved = def_parse_local_timestamp(row["ApprovedAt"])
            effective = def_parse_date(row["EffectiveDate"])
            if pd.isna(approved) or pd.isna(effective):
                raise ValueError(f"approved event has no effective session: {row['EventId']}")
            approval_date = approved.tz_localize(None).normalize()
            if effective <= approval_date:
                raise ValueError(f"approved event is not effective next session: {row['EventId']}")
            valid_to = def_parse_date(row["ValidTo"])
            if row["EventType"] == "ADD" and not pd.isna(valid_to) and valid_to < effective:
                raise ValueError(f"ADD ValidTo precedes EffectiveDate: {row['EventId']}")

    approved = frame.loc[frame["ApprovalStatus"].eq(APPROVED_STATUS)].copy()
    active: dict[tuple[str, str], bool] = {}
    active_valid_to: dict[tuple[str, str], pd.Timestamp | pd.NaT] = {}
    for row in approved.sort_values(["EffectiveDate", "Sequence"], kind="stable").itertuples(index=False):
        key = (row.GroupId, row.Ticker)
        prior = active.get(key, False)
        event_date = def_parse_date(row.EffectiveDate)
        prior_valid_to = active_valid_to.get(key, pd.NaT)
        if prior and not pd.isna(prior_valid_to) and event_date > prior_valid_to:
            prior = False
            active[key] = False
        if row.EventType == "ADD" and prior:
            raise ValueError(f"duplicate active ADD for {key} at {row.EventId}")
        if row.EventType == "REMOVE" and not prior:
            raise ValueError(f"REMOVE without active membership for {key} at {row.EventId}")
        if row.EventType == "ADD":
            active[key] = True
            active_valid_to[key] = def_parse_date(row.ValidTo)
        elif row.EventType == "REMOVE":
            active[key] = False
            active_valid_to[key] = pd.NaT

    active_adds = approved.loc[approved["EventType"].eq("ADD")]
    multi_counts = active_adds.groupby("Ticker")["GroupId"].nunique()
    return {
        "EngineId": ENGINE_ID,
        "EngineVersion": ENGINE_VERSION,
        "Status": "PASS",
        "Rows": int(len(frame)),
        "ApprovedRows": int(len(approved)),
        "RelationshipStreams": int(frame.groupby(["GroupId", "Ticker"]).ngroups),
        "MultiGroupTickerCount": int((multi_counts > 1).sum()),
        "HashAlgorithm": EVENT_HASH_ALGORITHM,
        "LastLedgerHash": str(frame["LedgerHash"].iloc[-1]),
        "ValidToPolicy": VALID_TO_POLICY,
    }


def def_append_membership_event(
    ledger: pd.DataFrame,
    event: Mapping[str, Any],
    trading_calendar: Iterable[Any],
) -> pd.DataFrame:
    calendar = def_prepare_trading_calendar(trading_calendar)
    if ledger.empty:
        existing = pd.DataFrame(columns=list(REQUIRED_EVENT_COLUMNS))
    else:
        existing = def_normalize_membership_events(ledger, calendar)
        def_validate_membership_event_chain(existing)

    candidate = dict(event)
    for column in REQUIRED_EVENT_COLUMNS:
        candidate.setdefault(column, "")
    candidate.setdefault("ApprovalStatus", "PENDING")
    candidate.setdefault("Reason", "")
    candidate.setdefault("SourceVersion", "UNSPECIFIED")
    candidate.setdefault("SupersedesEventId", "")
    candidate.setdefault("RecordedAt", datetime.now(timezone.utc).isoformat())
    candidate["Sequence"] = len(existing) + 1
    candidate.setdefault("EventId", "")
    new_row = pd.DataFrame([candidate])
    combined = pd.concat([existing, new_row], ignore_index=True, sort=False)
    normalized = def_normalize_membership_events(combined, calendar)
    def_validate_membership_event_chain(normalized)
    if not existing.empty:
        preserved = normalized.iloc[: len(existing)][existing.columns].reset_index(drop=True)
        pd.testing.assert_frame_equal(existing.reset_index(drop=True), preserved, check_dtype=False)
    return normalized


def def_apply_approved_change_next_session(
    ledger: pd.DataFrame,
    change: Mapping[str, Any],
    trading_calendar: Iterable[Any],
) -> pd.DataFrame:
    approved = dict(change)
    approved["ApprovalStatus"] = APPROVED_STATUS
    if pd.isna(def_parse_local_timestamp(approved.get("ApprovedAt"))):
        raise ValueError("ApprovedAt is required for an approved membership change")
    return def_append_membership_event(ledger, approved, trading_calendar)


def def_materialize_membership_asof(
    events: pd.DataFrame,
    as_of_date: Any,
    trading_calendar: Iterable[Any],
) -> pd.DataFrame:
    as_of = def_parse_date(as_of_date)
    if pd.isna(as_of):
        raise ValueError(f"invalid as_of_date: {as_of_date!r}")
    normalized = def_normalize_membership_events(events, trading_calendar)
    def_validate_membership_event_chain(normalized)
    approved = normalized.loc[
        normalized["ApprovalStatus"].eq(APPROVED_STATUS)
        & normalized["EffectiveDate"].ne("")
        & (pd.to_datetime(normalized["EffectiveDate"]) <= as_of)
    ].sort_values(["EffectiveDate", "Sequence"], kind="stable")

    state: dict[tuple[str, str], dict[str, Any]] = {}
    for row in approved.to_dict(orient="records"):
        key = (row["GroupId"], row["Ticker"])
        current = state.get(key, {"Active": False})
        if row["EventType"] == "ADD":
            current = {
                "Active": True,
                "AsOfDate": as_of,
                "GroupId": row["GroupId"],
                "GroupName": row["GroupName"],
                "Ticker": row["Ticker"],
                "MembershipValidFrom": def_parse_date(row["EffectiveDate"]),
                "MembershipValidTo": def_parse_date(row["ValidTo"]),
                "ApprovedAt": row["ApprovedAt"],
                "CurrentEventId": row["EventId"],
                "SourceVersion": row["SourceVersion"],
                "Reason": row["Reason"],
                "EvidenceStatus": "APPROVED_EFFECTIVE",
                "ExposureShare": row.get("ExposureShare", np.nan),
            }
        elif row["EventType"] == "REMOVE":
            current["Active"] = False
            current["RemovedByEventId"] = row["EventId"]
        elif row["EventType"] == "KEEP" and current.get("Active", False):
            current["CurrentEventId"] = row["EventId"]
            current["ApprovedAt"] = row["ApprovedAt"]
            current["Reason"] = row["Reason"]
            if pd.notna(row.get("ExposureShare", np.nan)):
                # An audited allocation change starts a new economic interval.
                # Keeping the original ValidFrom here would make an as-of view
                # imply that the revised share was already known historically.
                if not np.isclose(
                    float(current.get("ExposureShare", np.nan)),
                    float(row["ExposureShare"]),
                    equal_nan=True,
                ):
                    current["MembershipValidFrom"] = def_parse_date(
                        row["EffectiveDate"]
                    )
                current["ExposureShare"] = row["ExposureShare"]
        state[key] = current

    rows: list[dict[str, Any]] = []
    for current in state.values():
        if not current.get("Active", False):
            continue
        valid_to = current.get("MembershipValidTo", pd.NaT)
        if not pd.isna(valid_to) and as_of > valid_to:
            continue
        rows.append({column: current.get(column, "") for column in MATERIALIZED_COLUMNS})
    if not rows:
        return pd.DataFrame(columns=MATERIALIZED_COLUMNS)
    result = pd.DataFrame(rows)
    result["AsOfDate"] = pd.to_datetime(result["AsOfDate"])
    result["MembershipValidFrom"] = pd.to_datetime(result["MembershipValidFrom"])
    result["MembershipValidTo"] = pd.to_datetime(result["MembershipValidTo"])
    return result.sort_values(["GroupId", "Ticker"]).reset_index(drop=True)


def def_materialize_membership_history(
    events: pd.DataFrame,
    trading_calendar: Iterable[Any],
    *,
    as_of_date: Any | None = None,
    known_at: Any | None = None,
) -> pd.DataFrame:
    """Build replayable approved intervals from the immutable event ledger.

    The ledger remains the source of truth.  This table is a derived view for
    historical validation and T-1 index replay; a REMOVE closes the prior ADD
    on the trading session immediately before the removal becomes effective.
    ``as_of_date`` retains the legacy effective-date cut-off.  ``known_at``
    instead retains every approved event known by an exact timestamp, including
    a next-session change that is known but not yet effective; this is required
    to map scheduled T+1 evidence without consulting a later approval.  Exact
    knowledge time is the latest populated value across ApprovedAt, RecordedAt,
    KnownAt, AvailableAt, and IngestedAt.
    """

    calendar = def_prepare_trading_calendar(trading_calendar)
    normalized = def_normalize_membership_events(events, calendar)
    def_validate_membership_event_chain(normalized)
    approved = normalized.loc[
        normalized["ApprovalStatus"].eq(APPROVED_STATUS)
        & normalized["EffectiveDate"].ne("")
    ].copy()
    approved["EffectiveTimestamp"] = pd.to_datetime(
        approved["EffectiveDate"], errors="coerce"
    ).dt.normalize()
    if as_of_date is not None and known_at is not None:
        raise ValueError("as_of_date and known_at are mutually exclusive")
    if known_at is not None:
        knowledge_cutoff = def_parse_local_timestamp(known_at)
        if pd.isna(knowledge_cutoff):
            raise ValueError(f"invalid known_at: {known_at!r}")
        event_known_at = approved["EventKnownAt"].map(def_parse_local_timestamp)
        approved = approved.loc[
            event_known_at.notna() & event_known_at.le(knowledge_cutoff)
        ].copy()
    elif as_of_date is not None:
        cutoff = def_parse_date(as_of_date)
        if pd.isna(cutoff):
            raise ValueError(f"invalid as_of_date: {as_of_date!r}")
        approved = approved.loc[approved["EffectiveTimestamp"].le(cutoff)]

    rows: list[dict[str, Any]] = []
    open_intervals: dict[tuple[str, str], dict[str, Any]] = {}
    ordered = approved.sort_values(["EffectiveTimestamp", "Sequence"], kind="stable")
    for event in ordered.to_dict(orient="records"):
        key = (str(event["GroupId"]), str(event["Ticker"]))
        event_type = str(event["EventType"])
        effective = pd.Timestamp(event["EffectiveTimestamp"])
        if event_type == "ADD":
            previous = open_intervals.get(key)
            if previous is not None:
                previous_valid_to = previous.get("ValidTo", pd.NaT)
                if pd.isna(previous_valid_to) or pd.Timestamp(previous_valid_to) >= effective:
                    raise ValueError(f"overlapping derived ADD interval: {event['EventId']}")
                rows.append(open_intervals.pop(key))
            record = {
                "GroupId": event["GroupId"],
                "GroupName": event["GroupName"],
                "L3": event["GroupId"],
                "Ticker": event["Ticker"],
                "ValidFrom": effective,
                "ValidTo": def_parse_date(event["ValidTo"]),
                "ApprovedAt": event["ApprovedAt"],
                "KnownAt": event["EventKnownAt"],
                "Decision": "APPROVED",
                "ApprovalStatus": "APPROVED",
                "ValidationEligible": True,
                "IndexEligible": True,
                "AddEventId": event["EventId"],
                "RemoveEventId": "",
                "LastKeepEventId": "",
                "SourceVersion": event["SourceVersion"],
                "Reason": event["Reason"],
                "HistoryViewStatus": "DERIVED_FROM_APPEND_ONLY_EVENT_LEDGER",
                "ExposureShare": event.get("ExposureShare", np.nan),
            }
            open_intervals[key] = record
        elif event_type == "KEEP" and key in open_intervals:
            current = open_intervals[key]
            current["LastKeepEventId"] = event["EventId"]
            revised_share = event.get("ExposureShare", np.nan)
            share_changed = pd.notna(revised_share) and not np.isclose(
                float(current.get("ExposureShare", np.nan)),
                float(revised_share),
                equal_nan=True,
            )
            if share_changed:
                existing_valid_to = current.get("ValidTo", pd.NaT)
                if not pd.isna(existing_valid_to) and pd.Timestamp(
                    existing_valid_to
                ) < effective:
                    raise ValueError(
                        f"KEEP revises an expired membership interval: {event['EventId']}"
                    )
                prior_sessions = calendar[calendar < effective]
                if not len(prior_sessions):
                    raise ValueError(
                        f"KEEP share revision has no prior trading session: {event['EventId']}"
                    )
                prior = current.copy()
                prior["ValidTo"] = min(
                    pd.Timestamp(prior_sessions[-1]),
                    pd.Timestamp(existing_valid_to)
                    if not pd.isna(existing_valid_to)
                    else pd.Timestamp(prior_sessions[-1]),
                )
                # The historical interval boundary is only knowable once this
                # KEEP revision itself has passed every knowledge gate.
                prior["KnownAt"] = event["EventKnownAt"]
                rows.append(prior)
                revised = current.copy()
                revised["ValidFrom"] = effective
                revised["ValidTo"] = existing_valid_to
                revised["ApprovedAt"] = event["ApprovedAt"]
                revised["KnownAt"] = event["EventKnownAt"]
                revised["SourceVersion"] = event["SourceVersion"]
                revised["Reason"] = event["Reason"]
                revised["ExposureShare"] = revised_share
                revised["LastKeepEventId"] = event["EventId"]
                open_intervals[key] = revised
        elif event_type == "REMOVE":
            record = open_intervals.pop(key)
            prior_sessions = calendar[calendar < effective]
            if not len(prior_sessions):
                raise ValueError(f"REMOVE has no prior trading session: {event['EventId']}")
            removal_valid_to = pd.Timestamp(prior_sessions[-1])
            existing_valid_to = record.get("ValidTo", pd.NaT)
            if not pd.isna(existing_valid_to):
                removal_valid_to = min(removal_valid_to, pd.Timestamp(existing_valid_to))
            record["ValidTo"] = removal_valid_to
            record["KnownAt"] = event["EventKnownAt"]
            record["RemoveEventId"] = event["EventId"]
            rows.append(record)

    rows.extend(open_intervals.values())
    columns = [
        "GroupId",
        "GroupName",
        "L3",
        "Ticker",
        "ValidFrom",
        "ValidTo",
        "ApprovedAt",
        "KnownAt",
        "Decision",
        "ApprovalStatus",
        "ValidationEligible",
        "IndexEligible",
        "AddEventId",
        "RemoveEventId",
        "SourceVersion",
        "Reason",
        "HistoryViewStatus",
        "ExposureShare",
        "LastKeepEventId",
    ]
    if not rows:
        return pd.DataFrame(columns=columns)
    result = pd.DataFrame(rows)
    result["ValidFrom"] = pd.to_datetime(result["ValidFrom"], errors="coerce").dt.normalize()
    result["ValidTo"] = pd.to_datetime(result["ValidTo"], errors="coerce").dt.normalize()
    invalid = result["ValidTo"].notna() & result["ValidTo"].lt(result["ValidFrom"])
    if invalid.any():
        raise ValueError("derived membership history contains an invalid interval")
    return result[columns].sort_values(["GroupId", "Ticker", "ValidFrom"]).reset_index(drop=True)


def def_run_self_test() -> dict[str, Any]:
    calendar = pd.bdate_range("2026-01-02", periods=12)
    ledger = pd.DataFrame(columns=list(REQUIRED_EVENT_COLUMNS))
    base = {
        "EventType": "ADD",
        "GroupName": "CPO 共封裝光學",
        "Ticker": "3081.TWO",
        "ApprovedAt": "2026-01-02 16:30:00+08:00",
        "ValidFrom": "",
        "ValidTo": "",
        "SourceVersion": "SELF_TEST",
        "Reason": "story evidence approved",
    }
    ledger = def_apply_approved_change_next_session(ledger, {**base, "GroupId": "CPO"}, calendar)
    ledger = def_apply_approved_change_next_session(
        ledger,
        {**base, "GroupId": "OPTICAL", "GroupName": "光通訊"},
        calendar,
    )
    before = def_materialize_membership_asof(ledger, "2026-01-02", calendar)
    effective = def_materialize_membership_asof(ledger, "2026-01-05", calendar)
    if not before.empty or len(effective) != 2:
        raise AssertionError("next-session or multi-group membership contract failed")
    frozen = ledger.copy(deep=True)
    ledger = def_apply_approved_change_next_session(
        ledger,
        {
            "EventType": "REMOVE",
            "GroupId": "CPO",
            "GroupName": "CPO 共封裝光學",
            "Ticker": "3081.TWO",
            "ApprovedAt": "2026-01-05 17:00:00+08:00",
            "ValidFrom": "",
            "ValidTo": "",
            "SourceVersion": "SELF_TEST",
            "Reason": "approved removal",
        },
        calendar,
    )
    pd.testing.assert_frame_equal(frozen, ledger.iloc[:-1][frozen.columns].reset_index(drop=True))
    monday = def_materialize_membership_asof(ledger, "2026-01-05", calendar)
    tuesday = def_materialize_membership_asof(ledger, "2026-01-06", calendar)
    if len(monday) != 2 or set(tuesday["GroupId"]) != {"OPTICAL"}:
        raise AssertionError("approved REMOVE did not become effective on the next session")
    tampered = ledger.copy()
    tampered.loc[0, "Reason"] = "history rewritten"
    try:
        def_validate_membership_event_chain(tampered)
    except ValueError:
        pass
    else:
        raise AssertionError("membership hash chain did not reject historical mutation")
    quality = def_validate_membership_event_chain(ledger)
    quality["SelfTestStatus"] = "PASS"
    return quality


if __name__ == "__main__":
    print(json.dumps(def_run_self_test(), ensure_ascii=False, indent=2))
