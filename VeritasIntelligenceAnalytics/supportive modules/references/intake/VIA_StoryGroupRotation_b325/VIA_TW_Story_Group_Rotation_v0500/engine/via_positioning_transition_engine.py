from __future__ import annotations

"""Point-in-time transition ledger for exact stock-positioning consensus.

The stock-positioning engine describes evidence visible on one session.  This
module answers a narrower question: were four specified observations seen in
order, using only signals that had become effective at that point in time?

No score, rank, trade instruction, or causal conclusion is produced.  An
incomplete sequence expires after its own ``EvidenceWindowDays`` trading
sessions.  Observed distribution or price-breakdown evidence resets the
sequence immediately.
"""

from hashlib import sha256
import json
from typing import Any, Iterable, Mapping

import pandas as pd

if __package__:
    from .via_time_utils import def_available_at_utc, def_local_calendar_date
else:  # direct execution from the engine directory
    from via_time_utils import def_available_at_utc, def_local_calendar_date


ENGINE_ID = "VIA_POSITIONING_TRANSITION_LEDGER_V0500"
ENGINE_VERSION = "0.5.0"
EXACT_CONSENSUS_STATUS = "PASS_EXACT_FACTOR_MODEL_AGREEMENT"
EX_TSMC_UNIVERSE = "TWSE_TPEX_COMMON_EQUITY_EX_2330"
EMPTY_HASH = "0" * 64
TSMC_BASE = "2330"

ORDERED_PHASES = (
    "DIRECTIONAL_CAPITAL_SETTLEMENT_OBSERVED",
    "PRICE_PULLBACK_OR_SIDEWAYS_WITH_SETTLED_CAPITAL_OBSERVED",
    "STABLE_POSITIONING_DURING_PRICE_PULLBACK_OR_SIDEWAYS_OBSERVED",
    "PRICE_RESTART_AFTER_STABLE_POSITIONING_OBSERVED",
)
PHASE_ORDINAL = {phase: ordinal for ordinal, phase in enumerate(ORDERED_PHASES, 1)}

DISTRIBUTION_PHASES = {
    "EARLY_DISTRIBUTION_WHILE_PRICE_HOLDS_OBSERVED",
}
BREAKDOWN_PHASES = {
    "EXIT_WITH_PRICE_BREAKDOWN_OBSERVED",
}
DISTRIBUTION_CATEGORIES = {
    "EARLY_EXIT_BEFORE_PRICE_WEAKNESS",
    "DIRECTIONAL_DISTRIBUTION_WITHOUT_ATTENTION_CONFIRMATION",
}
BREAKDOWN_CATEGORIES = {
    "EXIT_WITH_PRICE_WEAKNESS_CONFIRMATION",
}

REQUIRED_COLUMNS = {
    "Date",
    "Ticker",
    "EvidenceWindowDays",
    "DirectionalLane",
    "ConsensusStatus",
    "ConsensusEvidenceCategory",
    "ConsensusPositioningSequencePhase",
    "SignalAvailableAt",
    "EffectiveDate",
    "MarketUniverse",
    "TSMCExcluded",
}


def def_ticker_base(value: Any) -> str:
    text = str(value or "").strip().upper().replace(" ", "")
    return text.removesuffix(".TWO").removesuffix(".TW")


def def_prepare_trading_calendar(values: Iterable[Any]) -> pd.DatetimeIndex:
    dates = [def_local_calendar_date(value) for value in values]
    calendar = pd.DatetimeIndex(sorted({value for value in dates if not pd.isna(value)}))
    if calendar.empty:
        raise ValueError("trading_calendar cannot be empty")
    return calendar


def def_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().upper() in {"TRUE", "T", "1", "YES", "Y"}


def def_prepare_exact_consensus(
    consensus: pd.DataFrame,
    trading_calendar: Iterable[Any],
    *,
    as_of: Any | None = None,
) -> tuple[pd.DataFrame, pd.DatetimeIndex]:
    """Validate the exact-consensus boundary and apply an optional PIT cut-off."""

    missing = sorted(REQUIRED_COLUMNS.difference(consensus.columns))
    if missing:
        raise ValueError(f"positioning transition input missing columns: {missing}")
    forbidden = [
        column
        for column in consensus.columns
        if "score" in str(column).lower()
        or "revenue" in str(column).lower()
        or "營收" in str(column)
    ]
    if forbidden:
        raise ValueError(
            "positioning transition input cannot contain score or revenue fields: "
            f"{sorted(map(str, forbidden))}"
        )

    calendar = def_prepare_trading_calendar(trading_calendar)
    frame = consensus.copy()
    frame["Date"] = frame["Date"].map(def_local_calendar_date)
    frame["EffectiveDate"] = frame["EffectiveDate"].map(def_local_calendar_date)
    frame["SignalAvailableAt"] = frame["SignalAvailableAt"].map(
        def_available_at_utc
    )
    frame["Ticker"] = frame["Ticker"].map(def_ticker_base)
    frame["DirectionalLane"] = (
        frame["DirectionalLane"].fillna("").astype(str).str.strip().str.upper()
    )
    frame["EvidenceWindowDays"] = pd.to_numeric(
        frame["EvidenceWindowDays"], errors="coerce"
    ).astype("Int64")
    frame["ConsensusStatus"] = (
        frame["ConsensusStatus"].fillna("").astype(str).str.strip().str.upper()
    )
    frame["ConsensusEvidenceCategory"] = (
        frame["ConsensusEvidenceCategory"].fillna("").astype(str).str.strip().str.upper()
    )
    frame["ConsensusPositioningSequencePhase"] = (
        frame["ConsensusPositioningSequencePhase"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.upper()
    )

    if as_of is not None:
        cutoff = def_available_at_utc(as_of)
        if pd.isna(cutoff):
            raise ValueError(f"invalid as_of timestamp: {as_of!r}")
        cutoff_date = def_local_calendar_date(cutoff)
        frame = frame.loc[
            frame["SignalAvailableAt"].le(cutoff)
            & frame["EffectiveDate"].le(cutoff_date)
        ].copy()

    if frame.empty:
        return frame, calendar
    invalid_keys = (
        frame["Date"].isna()
        | frame["EffectiveDate"].isna()
        | frame["SignalAvailableAt"].isna()
        | frame["Ticker"].eq("")
        | frame["DirectionalLane"].eq("")
        | frame["EvidenceWindowDays"].isna()
        | frame["EvidenceWindowDays"].lt(2)
    )
    if invalid_keys.any():
        raise ValueError(
            f"positioning transition input has {int(invalid_keys.sum())} invalid PIT keys"
        )
    non_exact = frame["ConsensusStatus"].ne(EXACT_CONSENSUS_STATUS)
    if non_exact.any():
        raise ValueError(
            "positioning transition ledger accepts exact factor-model consensus only"
        )
    wrong_universe = frame["MarketUniverse"].astype(str).ne(EX_TSMC_UNIVERSE)
    tsmc_not_excluded = ~frame["TSMCExcluded"].map(def_bool)
    contains_tsmc = frame["Ticker"].eq(TSMC_BASE)
    if wrong_universe.any() or tsmc_not_excluded.any() or contains_tsmc.any():
        raise ValueError("positioning transition input violates ex-2330 provenance")

    keys = ["Date", "Ticker", "EvidenceWindowDays", "DirectionalLane"]
    duplicate = frame.duplicated(keys, keep=False)
    if duplicate.any():
        raise ValueError(
            f"positioning transition input has {int(duplicate.sum())} duplicate consensus rows"
        )
    duplicate_effective = frame.duplicated(
        ["EffectiveDate", "Ticker", "EvidenceWindowDays", "DirectionalLane"],
        keep=False,
    )
    if duplicate_effective.any():
        raise ValueError("a transition stream cannot advance twice on one effective session")

    calendar_set = set(calendar)
    off_calendar = ~frame["EffectiveDate"].isin(calendar_set)
    if off_calendar.any():
        raise ValueError("EffectiveDate must be a supplied trading session")
    available_local_date = frame["SignalAvailableAt"].map(def_local_calendar_date)
    boundary = pd.concat([frame["Date"], available_local_date], axis=1).max(axis=1)
    if frame["EffectiveDate"].le(boundary).any():
        raise ValueError(
            "EffectiveDate must be after both evidence date and latest availability date"
        )

    return (
        frame.sort_values(
            [
                "Ticker",
                "EvidenceWindowDays",
                "DirectionalLane",
                "EffectiveDate",
                "SignalAvailableAt",
                "Date",
            ],
            kind="stable",
        ).reset_index(drop=True),
        calendar,
    )


def def_sequence_id(
    ticker: str,
    window: int,
    lane: str,
    cycle: int,
    started: pd.Timestamp,
) -> str:
    canonical = f"{ticker}|{window}|{lane}|{cycle}|{started:%Y-%m-%d}"
    return "VIA-PSEQ-" + sha256(canonical.encode("utf-8")).hexdigest()[:24].upper()


def def_canonical_value(value: Any) -> Any:
    if value is None or pd.isna(value):
        return None
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if hasattr(value, "item"):
        return value.item()
    return value


def def_transition_hash(record: Mapping[str, Any], previous_hash: str) -> str:
    excluded = {"PreviousTransitionHash", "TransitionHash"}
    payload = {
        key: def_canonical_value(value)
        for key, value in record.items()
        if key not in excluded
    }
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return sha256(f"{previous_hash}|{canonical}".encode("utf-8")).hexdigest().upper()


def def_reset_reason(phase: str, category: str) -> str:
    reasons: list[str] = []
    if phase in BREAKDOWN_PHASES or category in BREAKDOWN_CATEGORIES:
        reasons.append("PRICE_BREAKDOWN_OBSERVED")
    if phase in DISTRIBUTION_PHASES or category in DISTRIBUTION_CATEGORIES:
        reasons.append("DISTRIBUTION_OBSERVED")
    return "|".join(reasons)


def def_expected_next_phase(stage: int) -> str:
    return ORDERED_PHASES[stage] if 0 <= stage < len(ORDERED_PHASES) else "RESET_REQUIRED_FOR_NEW_SEQUENCE"


def def_build_positioning_transition_ledger(
    exact_consensus: pd.DataFrame,
    trading_calendar: Iterable[Any],
    *,
    as_of: Any | None = None,
) -> pd.DataFrame:
    """Build a deterministic PIT ledger of four-stage observed transitions.

    State streams are independent for every ticker, evidence window, and
    directional lane.  ``EvidenceWindowDays`` is also the maximum trading-
    session age of an incomplete sequence; there is no fixed expiry parameter.
    """

    frame, calendar = def_prepare_exact_consensus(
        exact_consensus, trading_calendar, as_of=as_of
    )
    if frame.empty:
        return pd.DataFrame()
    session_number = {pd.Timestamp(date): index for index, date in enumerate(calendar)}
    output: list[dict[str, Any]] = []
    stream_keys = ["Ticker", "EvidenceWindowDays", "DirectionalLane"]

    for stream_key, observations in frame.groupby(
        stream_keys, sort=True, observed=True
    ):
        ticker, window_value, lane = stream_key
        window = int(window_value)
        stage = 0
        cycle = 0
        sequence_id = ""
        started = pd.NaT
        completed = pd.NaT
        previous_hash = EMPTY_HASH
        stream_sequence = 0

        for source in observations.itertuples(index=False):
            stream_sequence += 1
            effective = pd.Timestamp(source.EffectiveDate)
            phase = str(source.ConsensusPositioningSequencePhase)
            category = str(source.ConsensusEvidenceCategory)
            prior_stage = stage
            prior_sequence_id = sequence_id
            prior_started = started
            reset_reasons: list[str] = []

            incomplete_expired = (
                0 < stage < len(ORDERED_PHASES)
                and not pd.isna(started)
                and session_number[effective] - session_number[pd.Timestamp(started)] > window
            )
            if incomplete_expired:
                reset_reasons.append("EVIDENCE_WINDOW_EXPIRED")

            reversal = def_reset_reason(phase, category)
            if reversal:
                reset_reasons.extend(reversal.split("|"))

            if reset_reasons:
                stage = 0
                sequence_id = ""
                started = pd.NaT
                completed = pd.NaT

            observed_ordinal = PHASE_ORDINAL.get(phase)
            accepted = False
            if reversal:
                transition_event = "RESET_ON_DISTRIBUTION_OR_BREAKDOWN"
                transition_status = "PASS_OBSERVED_RESET"
            elif observed_ordinal == 1 and stage == 0:
                cycle += 1
                stage = 1
                started = effective
                sequence_id = def_sequence_id(ticker, window, lane, cycle, started)
                accepted = True
                transition_event = (
                    "RESET_EXPIRED_THEN_START_STAGE_1"
                    if reset_reasons
                    else "START_STAGE_1"
                )
                transition_status = "PASS_ORDERED_TRANSITION"
            elif observed_ordinal is not None and observed_ordinal == stage + 1:
                stage = observed_ordinal
                accepted = True
                if stage == len(ORDERED_PHASES):
                    completed = effective
                    transition_event = "COMPLETE_STAGE_4"
                else:
                    transition_event = f"ADVANCE_TO_STAGE_{stage}"
                transition_status = "PASS_ORDERED_TRANSITION"
            elif observed_ordinal is not None and observed_ordinal == stage and stage > 0:
                accepted = True
                transition_event = f"RECONFIRM_STAGE_{stage}"
                transition_status = "PASS_STAGE_RECONFIRMED"
            elif observed_ordinal is not None and observed_ordinal < stage:
                transition_event = "PRIOR_STAGE_REOBSERVED_NO_REGRESSION"
                transition_status = "HOLD_NO_REGRESSION"
            elif observed_ordinal is not None:
                transition_event = (
                    "RESET_SEQUENCE_EXPIRED"
                    if "EVIDENCE_WINDOW_EXPIRED" in reset_reasons
                    else "OUT_OF_ORDER_PHASE_IGNORED"
                )
                transition_status = "HOLD_OUT_OF_ORDER_PHASE"
            elif reset_reasons:
                transition_event = "RESET_SEQUENCE_EXPIRED"
                transition_status = "PASS_OBSERVED_RESET"
            else:
                transition_event = "NO_ORDERED_PHASE_CHANGE"
                transition_status = "NO_SEQUENCE_CHANGE"

            expiry = pd.NaT
            if 0 < stage < len(ORDERED_PHASES) and not pd.isna(started):
                expiry_index = session_number[pd.Timestamp(started)] + window
                if expiry_index < len(calendar):
                    expiry = pd.Timestamp(calendar[expiry_index])

            verified_phase = ORDERED_PHASES[stage - 1] if stage else "NO_ACTIVE_SEQUENCE"
            record: dict[str, Any] = {
                "EngineId": ENGINE_ID,
                "EngineVersion": ENGINE_VERSION,
                "StreamSequence": stream_sequence,
                "Ticker": ticker,
                "EvidenceWindowDays": window,
                "DirectionalLane": lane,
                "EvidenceDate": pd.Timestamp(source.Date),
                "SignalAvailableAt": pd.Timestamp(source.SignalAvailableAt),
                "EffectiveDate": effective,
                "ConsensusStatus": source.ConsensusStatus,
                "ConsensusEvidenceCategory": category,
                "ObservedConsensusPhase": phase,
                "PriorVerifiedPhase": (
                    ORDERED_PHASES[prior_stage - 1]
                    if prior_stage
                    else "NO_ACTIVE_SEQUENCE"
                ),
                "VerifiedPhase": verified_phase,
                "ExpectedNextPhase": def_expected_next_phase(stage),
                "ObservedPhaseAccepted": accepted,
                "TransitionEvent": transition_event,
                "TransitionStatus": transition_status,
                "ResetReason": "|".join(dict.fromkeys(reset_reasons)),
                "PriorSequenceId": prior_sequence_id,
                "SequenceId": sequence_id,
                "SequenceStartedEffectiveDate": started,
                "PriorSequenceStartedEffectiveDate": prior_started,
                "SequenceExpiryEffectiveDate": expiry,
                "SequenceCompletedEffectiveDate": completed,
                "SequenceComplete": stage == len(ORDERED_PHASES),
                "ExpiryPolicy": "INCOMPLETE_SEQUENCE_EXPIRES_AFTER_EVIDENCE_WINDOW_TRADING_SESSIONS",
                "OrderingPolicy": "STRICT_FOUR_PHASE_ORDER_NO_SKIPS_NO_REGRESSION",
                "Interpretation": "OBSERVED_PIT_ORDER_ONLY_NOT_CAUSAL",
                "MarketUniverse": EX_TSMC_UNIVERSE,
                "TSMCExcluded": True,
                "TradeInstruction": False,
                "PreviousTransitionHash": previous_hash,
            }
            record["TransitionEventId"] = "VIA-PTEVT-" + sha256(
                (
                    f"{ticker}|{window}|{lane}|{source.Date}|"
                    f"{source.SignalAvailableAt}|{effective}|{stream_sequence}"
                ).encode("utf-8")
            ).hexdigest()[:24].upper()
            record["TransitionHash"] = def_transition_hash(record, previous_hash)
            previous_hash = record["TransitionHash"]
            output.append(record)

    keys = [
        "Ticker",
        "EvidenceWindowDays",
        "DirectionalLane",
        "EffectiveDate",
        "StreamSequence",
    ]
    return pd.DataFrame(output).sort_values(keys, kind="stable").reset_index(drop=True)


def def_latest_positioning_transition_state(
    ledger: pd.DataFrame,
    trading_calendar: Iterable[Any] | None = None,
    *,
    as_of: Any | None = None,
) -> pd.DataFrame:
    """Materialize each stream, including clock-driven expiry at ``as_of``.

    The immutable ledger records exact observations.  Expiry is deterministic
    even when no later exact observation arrives, so this derived view resets
    a stale incomplete sequence on the first session after its permitted
    evidence window.  Both ``trading_calendar`` and ``as_of`` are required to
    activate that materialization; callers omitting them receive the legacy
    latest-observation view.
    """

    if ledger.empty:
        return ledger.copy()
    required = {
        "Ticker",
        "EvidenceWindowDays",
        "DirectionalLane",
        "EffectiveDate",
        "StreamSequence",
    }
    missing = sorted(required.difference(ledger.columns))
    if missing:
        raise ValueError(f"positioning transition ledger missing columns: {missing}")
    ordered = ledger.sort_values(
        [
            "Ticker",
            "EvidenceWindowDays",
            "DirectionalLane",
            "EffectiveDate",
            "StreamSequence",
        ],
        kind="stable",
    )
    latest = ordered.drop_duplicates(
        ["Ticker", "EvidenceWindowDays", "DirectionalLane"], keep="last"
    ).reset_index(drop=True)
    latest["StateAsOf"] = pd.NaT
    latest["MaterializedStateEffectiveDate"] = latest["EffectiveDate"]
    latest["StateMaterializationStatus"] = "LATEST_IMMUTABLE_LEDGER_OBSERVATION"
    latest["ExpiredSequenceId"] = ""
    if (trading_calendar is None) != (as_of is None):
        raise ValueError(
            "trading_calendar and as_of must be supplied together for expiry materialization"
        )
    if trading_calendar is None:
        return latest

    calendar = def_prepare_trading_calendar(trading_calendar)
    cutoff = def_available_at_utc(as_of)
    if pd.isna(cutoff):
        raise ValueError(f"invalid as_of timestamp: {as_of!r}")
    cutoff_date = def_local_calendar_date(cutoff)
    if cutoff_date > calendar.max():
        raise ValueError("trading_calendar does not cover transition state as_of")
    latest["StateAsOf"] = cutoff
    for index, state in latest.iterrows():
        if bool(state.get("SequenceComplete", False)):
            continue
        expiry = def_local_calendar_date(state.get("SequenceExpiryEffectiveDate"))
        if pd.isna(expiry) or str(state.get("VerifiedPhase")) == "NO_ACTIVE_SEQUENCE":
            continue
        reset_sessions = calendar[calendar > expiry]
        if not len(reset_sessions) or pd.Timestamp(reset_sessions[0]) > cutoff_date:
            continue
        reset_effective = pd.Timestamp(reset_sessions[0])
        latest.at[index, "ExpiredSequenceId"] = str(state.get("SequenceId", ""))
        latest.at[index, "PriorVerifiedPhase"] = state["VerifiedPhase"]
        latest.at[index, "VerifiedPhase"] = "NO_ACTIVE_SEQUENCE"
        latest.at[index, "ExpectedNextPhase"] = ORDERED_PHASES[0]
        latest.at[index, "SequenceId"] = ""
        latest.at[index, "SequenceStartedEffectiveDate"] = pd.NaT
        latest.at[index, "SequenceExpiryEffectiveDate"] = pd.NaT
        latest.at[index, "SequenceComplete"] = False
        latest.at[index, "ResetReason"] = "EVIDENCE_WINDOW_EXPIRED"
        latest.at[index, "TransitionEvent"] = "MATERIALIZED_CLOCK_DRIVEN_EXPIRY"
        latest.at[index, "TransitionStatus"] = "PASS_CLOCK_DRIVEN_RESET"
        latest.at[index, "MaterializedStateEffectiveDate"] = reset_effective
        latest.at[index, "StateMaterializationStatus"] = (
            "RESET_EXPIRED_WITHOUT_NEW_EXACT_OBSERVATION"
        )
    return latest


def def_self_test() -> dict[str, Any]:
    calendar = pd.bdate_range("2026-01-02", periods=24)

    def row(
        ticker: str,
        window: int,
        lane: str,
        evidence_index: int,
        phase: str,
        category: str = "NO_CONVERGENT_EVIDENCE",
    ) -> dict[str, Any]:
        evidence_date = calendar[evidence_index]
        effective_date = calendar[evidence_index + 1]
        return {
            "Date": evidence_date,
            "Ticker": ticker,
            "EvidenceWindowDays": window,
            "DirectionalLane": lane,
            "ConsensusStatus": EXACT_CONSENSUS_STATUS,
            "ConsensusEvidenceCategory": category,
            "ConsensusPositioningSequencePhase": phase,
            "SignalAvailableAt": pd.Timestamp(
                f"{evidence_date:%Y-%m-%d} 14:30:00", tz="Asia/Taipei"
            ),
            "EffectiveDate": effective_date,
            "MarketUniverse": EX_TSMC_UNIVERSE,
            "TSMCExcluded": True,
            "TradeInstruction": False,
        }

    neutral = "NO_ORDERED_POSITIONING_PHASE_EVIDENCE"
    rows = [
        # Complete sequence; stage 3 is first seen out of order and ignored.
        row("1111", 6, "FOREIGN", 0, ORDERED_PHASES[0]),
        row("1111", 6, "FOREIGN", 1, ORDERED_PHASES[2]),
        row("1111", 6, "FOREIGN", 2, ORDERED_PHASES[1]),
        row("1111", 6, "FOREIGN", 3, ORDERED_PHASES[2]),
        row("1111", 6, "FOREIGN", 4, ORDERED_PHASES[3]),
        # Window-driven expiry: stage 2 arrives more than two sessions later.
        row("2222", 2, "DOMESTIC_EX_FOREIGN", 0, ORDERED_PHASES[0]),
        row("2222", 2, "DOMESTIC_EX_FOREIGN", 1, neutral),
        row("2222", 2, "DOMESTIC_EX_FOREIGN", 4, ORDERED_PHASES[1]),
        # Distribution reset.
        row("3333", 6, "ACTIVE_ETF", 0, ORDERED_PHASES[0]),
        row("3333", 6, "ACTIVE_ETF", 1, ORDERED_PHASES[1]),
        row(
            "3333",
            6,
            "ACTIVE_ETF",
            2,
            "EARLY_DISTRIBUTION_WHILE_PRICE_HOLDS_OBSERVED",
            "EARLY_EXIT_BEFORE_PRICE_WEAKNESS",
        ),
        # Breakdown reset after stage 3.
        row("4444", 6, "FOREIGN", 0, ORDERED_PHASES[0]),
        row("4444", 6, "FOREIGN", 1, ORDERED_PHASES[1]),
        row("4444", 6, "FOREIGN", 2, ORDERED_PHASES[2]),
        row(
            "4444",
            6,
            "FOREIGN",
            3,
            "EXIT_WITH_PRICE_BREAKDOWN_OBSERVED",
            "EXIT_WITH_PRICE_WEAKNESS_CONFIRMATION",
        ),
    ]
    source = pd.DataFrame(rows)
    ledger = def_build_positioning_transition_ledger(source, calendar)
    latest = def_latest_positioning_transition_state(ledger).set_index("Ticker")

    assertions = 0
    assert latest.loc["1111", "SequenceComplete"]
    assertions += 1
    assert latest.loc["1111", "VerifiedPhase"] == ORDERED_PHASES[3]
    assertions += 1
    out_of_order = ledger.loc[
        ledger["Ticker"].eq("1111")
        & ledger["ObservedConsensusPhase"].eq(ORDERED_PHASES[2])
    ].iloc[0]
    assert out_of_order["TransitionStatus"] == "HOLD_OUT_OF_ORDER_PHASE"
    assertions += 1
    expired = ledger.loc[ledger["Ticker"].eq("2222")].iloc[-1]
    assert "EVIDENCE_WINDOW_EXPIRED" in expired["ResetReason"]
    assertions += 1
    assert expired["VerifiedPhase"] == "NO_ACTIVE_SEQUENCE"
    assertions += 1
    assert "DISTRIBUTION_OBSERVED" in latest.loc["3333", "ResetReason"]
    assertions += 1
    assert latest.loc["3333", "VerifiedPhase"] == "NO_ACTIVE_SEQUENCE"
    assertions += 1
    assert "PRICE_BREAKDOWN_OBSERVED" in latest.loc["4444", "ResetReason"]
    assertions += 1
    assert latest.loc["4444", "VerifiedPhase"] == "NO_ACTIVE_SEQUENCE"
    assertions += 1
    assert not ledger["TradeInstruction"].any()
    assertions += 1
    assert ledger["Interpretation"].eq("OBSERVED_PIT_ORDER_ONLY_NOT_CAUSAL").all()
    assertions += 1
    assert not any("score" in str(column).lower() for column in ledger.columns)
    assertions += 1

    cutoff = source["SignalAvailableAt"].map(def_available_at_utc).max()
    baseline = def_build_positioning_transition_ledger(source, calendar, as_of=cutoff)
    future = row("1111", 6, "FOREIGN", 10, ORDERED_PHASES[0])
    future_source = pd.concat([source, pd.DataFrame([future])], ignore_index=True)
    with_future = def_build_positioning_transition_ledger(
        future_source, calendar, as_of=cutoff
    )
    pd.testing.assert_frame_equal(baseline, with_future)
    assertions += 1

    invalid = source.iloc[[0]].copy()
    invalid["ConsensusStatus"] = "HOLD_FACTOR_MODEL_DISAGREEMENT"
    try:
        def_build_positioning_transition_ledger(invalid, calendar)
    except ValueError:
        assertions += 1
    else:
        raise AssertionError("non-exact consensus entered transition ledger")

    tsmc = source.iloc[[0]].copy()
    tsmc["Ticker"] = "2330.TW"
    try:
        def_build_positioning_transition_ledger(tsmc, calendar)
    except ValueError:
        assertions += 1
    else:
        raise AssertionError("TSMC entered ex-2330 transition ledger")

    return {
        "EngineId": ENGINE_ID,
        "EngineVersion": ENGINE_VERSION,
        "Status": "PASS",
        "Assertions": assertions,
        "LedgerRows": len(ledger),
        "CompletedSequences": int(ledger["SequenceComplete"].sum()),
        "ResetEvents": int(ledger["ResetReason"].ne("").sum()),
    }


if __name__ == "__main__":
    print(json.dumps(def_self_test(), ensure_ascii=False, indent=2, default=str))
