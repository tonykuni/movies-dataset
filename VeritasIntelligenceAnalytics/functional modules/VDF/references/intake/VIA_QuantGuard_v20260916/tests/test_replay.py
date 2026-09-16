from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import polars as pl
import pytest

from quant_engine import (
    DeterministicReplay,
    DuckDBPointInTimeStore,
    PointInTimeStore,
    ReplayConfig,
    ReplaySession,
    assert_future_append_invariant,
    assert_no_future_rows,
    build_replay_sessions,
    stable_frame_hash,
)

UTC = timezone.utc
pytestmark = pytest.mark.anti_lookahead


def ts(day: date, hour: int) -> datetime:
    return datetime(day.year, day.month, day.day, hour, tzinfo=UTC)


def revision_frame(days: int = 8) -> pl.DataFrame:
    rows: list[dict[str, object]] = []
    start = date(2024, 1, 1)
    revision_id = 1
    for market, ticker, close_hour in [("TW", "2330", 6), ("US", "SPY", 21)]:
        for index in range(days):
            session = start + timedelta(days=index)
            value = 100.0 + index if market == "TW" else 400.0 + index
            rows.append({
                "market_code": market,
                "ticker": ticker,
                "interval": "1d",
                "field_group": "market_bar",
                "market_session_date": session,
                "revision_id": revision_id,
                "revision_no": 1,
                "available_at": ts(session, close_hour + 1),
                "confirmed_at": ts(session, close_hour + 2),
                "revision_status": "confirmed",
                "adj_close": value,
                "adj_high": value * 1.01,
                "adj_low": value * 0.99,
                "non_day_trade_volume": 1000.0 + index,
                "close_utc": ts(session, close_hour),
                "bar_closed_at": ts(session, close_hour),
            })
            revision_id += 1
    # A T+2 corrected version must not be visible at the T+1 cutoff.
    corrected = dict(rows[2])
    corrected.update({
        "revision_id": revision_id,
        "revision_no": 2,
        "available_at": ts(date(2024, 1, 5), 8),
        "confirmed_at": ts(date(2024, 1, 5), 9),
        "adj_close": 999.0,
    })
    rows.append(corrected)
    return pl.DataFrame(rows)


def test_confirmed_only_hides_t_plus_2_revision_until_available():
    store = PointInTimeStore(revision_frame())
    before_revision = store.as_of(
        ts(date(2024, 1, 4), 12),
        market_code="TW",
        ticker="2330",
    )
    after_revision = store.as_of(
        ts(date(2024, 1, 5), 12),
        market_code="TW",
        ticker="2330",
    )
    assert before_revision.filter(pl.col("market_session_date") == date(2024, 1, 3)).select("adj_close").item() == 102.0
    assert after_revision.filter(pl.col("market_session_date") == date(2024, 1, 3)).select("adj_close").item() == 999.0


def test_late_us_close_is_not_visible_to_same_day_taiwan_cutoff():
    frame = revision_frame(days=3)
    cutoff = ts(date(2024, 1, 2), 10)
    store = PointInTimeStore(frame)
    us = store.as_of(cutoff, market_code="US")
    # The US row for Jan 2 is published/confirmed after the Taiwan cutoff;
    # the Jan 1 US close is the only valid external observation.
    assert us.get_column("market_session_date").to_list() == [date(2024, 1, 1)]


def test_initial_release_can_show_provisional_but_confirmed_only_cannot():
    frame = revision_frame().with_columns(
        pl.when(
            (pl.col("market_code") == "TW")
            & (pl.col("market_session_date") == date(2024, 1, 4))
        ).then(pl.lit("provisional")).otherwise(pl.col("revision_status")).alias("revision_status")
    ).with_columns(
        pl.when(
            (pl.col("market_code") == "TW")
            & (pl.col("market_session_date") == date(2024, 1, 4))
        ).then(None).otherwise(pl.col("confirmed_at")).alias("confirmed_at")
    )
    store = PointInTimeStore(frame)
    cutoff = ts(date(2024, 1, 4), 12)
    assert store.as_of(cutoff, market_code="TW", policy="confirmed_only").filter(
        pl.col("market_session_date") == date(2024, 1, 4)
    ).is_empty()
    assert store.as_of(cutoff, market_code="TW", policy="initial_release").filter(
        pl.col("market_session_date") == date(2024, 1, 4)
    ).height == 1


def test_future_append_invariance_and_future_row_guard():
    before = revision_frame()
    future = dict(before.row(0, named=True))
    future.update({
        "revision_id": 999,
        "revision_no": 1,
        "market_session_date": date(2025, 1, 1),
        "available_at": ts(date(2025, 1, 1), 8),
        "confirmed_at": ts(date(2025, 1, 1), 9),
        "close_utc": ts(date(2025, 1, 1), 6),
        "bar_closed_at": ts(date(2025, 1, 1), 6),
    })
    after = pl.concat([before, pl.DataFrame([future])], how="vertical_relaxed")
    cutoff = ts(date(2024, 1, 4), 12)
    assert_future_append_invariant(before, after, cutoff)
    assert_no_future_rows(before.filter(pl.col("available_at") <= cutoff), cutoff)
    with pytest.raises(AssertionError, match="future rows"):
        assert_no_future_rows(after, cutoff)


def test_stable_hash_is_independent_of_row_order():
    frame = pl.DataFrame({"b": [2, 1], "a": ["y", "x"]})
    reversed_frame = frame.reverse()
    assert stable_frame_hash(frame) == stable_frame_hash(reversed_frame)


def test_replay_sessions_use_next_open_for_execution():
    calendar = pl.DataFrame({
        "market_code": ["TW", "TW", "TW"],
        "session_date": [date(2024, 1, 1), date(2024, 1, 2), date(2024, 1, 3)],
        "status": ["open", "early_close", "open"],
        "open_utc": [ts(date(2024, 1, 1), 1), ts(date(2024, 1, 2), 1), ts(date(2024, 1, 3), 1)],
        "close_utc": [ts(date(2024, 1, 1), 6), ts(date(2024, 1, 2), 6), ts(date(2024, 1, 3), 6)],
        "calendar_version": ["v1", "v1", "v1"],
    })
    sessions = build_replay_sessions(calendar, execution_lag_sessions=1)
    assert sessions[0].execution_utc == ts(date(2024, 1, 2), 1)
    assert sessions[-1].execution_utc is None


def test_deterministic_replay_emits_manifest_and_only_current_session(tmp_path):
    store = PointInTimeStore(revision_frame(days=5))
    sessions = [
        ReplaySession("TW", date(2024, 1, 2), ts(date(2024, 1, 2), 10), execution_utc=ts(date(2024, 1, 3), 1), calendar_version="v1"),
        ReplaySession("TW", date(2024, 1, 3), ts(date(2024, 1, 3), 10), execution_utc=ts(date(2024, 1, 4), 1), calendar_version="v1"),
    ]

    def fake_features(frame: pl.DataFrame, *, benchmark: pl.DataFrame) -> pl.DataFrame:
        return frame.select(["date", "ticker", "adj_close"]).with_columns(
            pl.lit("paper_signal").alias("signal")
        )

    result = DeterministicReplay(store, config=ReplayConfig()).run(
        sessions,
        feature_fn=fake_features,
    )
    assert result.decisions.height == 2
    assert result.decisions.select("date").to_series().to_list() == [date(2024, 1, 2), date(2024, 1, 3)]
    assert len(result.manifests) == 2
    assert all(manifest.policy == "confirmed_only" for manifest in result.manifests)
    assert all(manifest.future_rows_rejected == 0 for manifest in result.manifests)
    assert result.decisions.select("replay_cutoff_utc").n_unique() == 2
    manifest_path = result.manifests[0].write_json(tmp_path / "manifest.json")
    assert manifest_path.exists()
    assert '"policy": "confirmed_only"' in manifest_path.read_text(encoding="utf-8")


def test_store_rejects_duplicate_revision_versions():
    frame = revision_frame().vstack(revision_frame().head(1))
    with pytest.raises(ValueError, match="revision_id must be globally unique"):
        PointInTimeStore(frame)


def test_store_requires_confirmed_at_for_revision_contract():
    with pytest.raises(ValueError, match="missing columns"):
        PointInTimeStore(revision_frame().drop("confirmed_at"))


def test_duckdb_backend_matches_memory_as_of_contract(tmp_path):
    pytest.importorskip("duckdb")
    backend = DuckDBPointInTimeStore.connect(tmp_path / "replay.duckdb")
    try:
        backend.create_schema()
        source = revision_frame(days=5)
        assert backend.append(source) == source.height
        memory = PointInTimeStore(source).as_of(
            ts(date(2024, 1, 4), 12),
            market_code="TW",
            ticker="2330",
        )
        persistent = backend.as_of(
            ts(date(2024, 1, 4), 12),
            market_code="TW",
            ticker="2330",
        )
        assert persistent.select(["market_session_date", "adj_close"]).to_dicts() == memory.select([
            "market_session_date", "adj_close"
        ]).to_dicts()
        def fake_features(frame: pl.DataFrame, *, benchmark: pl.DataFrame) -> pl.DataFrame:
            return frame.select(["date", "ticker", "adj_close"])

        replay = DeterministicReplay(backend).run(
            [ReplaySession("TW", date(2024, 1, 2), ts(date(2024, 1, 2), 12))],
            feature_fn=fake_features,
        )
        assert replay.decisions.height == 1
        assert replay.manifests[0].input_snapshot_hash
    finally:
        backend.close()


@pytest.mark.postgres
def test_postgres_backend_matches_memory_as_of_contract():
    dsn = __import__("os").environ.get("TEST_POSTGRES_DSN")
    if not dsn:
        pytest.skip("TEST_POSTGRES_DSN is not configured")
    from quant_engine import PostgresPointInTimeStore

    backend = PostgresPointInTimeStore.connect(dsn)
    try:
        backend._execute("DROP TABLE IF EXISTS market_observation_revision")
        backend.create_schema()
        source = revision_frame(days=5)
        assert backend.append(source) == source.height
        memory = PointInTimeStore(source).as_of(
            ts(date(2024, 1, 4), 12),
            market_code="TW",
            ticker="2330",
        )
        persistent = backend.as_of(
            ts(date(2024, 1, 4), 12),
            market_code="TW",
            ticker="2330",
        )
        assert persistent.select(["market_session_date", "adj_close"]).to_dicts() == memory.select([
            "market_session_date", "adj_close"
        ]).to_dicts()
    finally:
        backend._execute("DROP TABLE IF EXISTS market_observation_revision")
        backend.close()
