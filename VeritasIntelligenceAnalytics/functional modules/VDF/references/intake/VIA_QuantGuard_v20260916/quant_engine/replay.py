"""Integrated point-in-time store, deterministic replay, and anti-lookahead guards.

The module is intentionally self-contained at the orchestration boundary:
revision visibility, as-of selection, cross-market alignment, feature execution,
replay manifests, and test guards live here. Indicator mathematics remains in
``core.py``, ``risk.py``, and ``statistics.py`` and is called through one stable
runner interface.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Literal, Mapping, Protocol, Sequence

import polars as pl

from .core import build_feature_matrix
from .governance import align_confirmed_closes, normalize_market_timestamp

ReplayPolicy = Literal["confirmed_only", "initial_release"]

REVISION_REQUIRED_COLUMNS = {
    "market_code",
    "ticker",
    "interval",
    "market_session_date",
    "available_at",
    "revision_id",
    "revision_no",
    "revision_status",
    "confirmed_at",
}
REVISION_KEY = [
    "market_code",
    "ticker",
    "interval",
    "field_group",
    "market_session_date",
]

SQL_REVISION_SCHEMA = """
CREATE TABLE IF NOT EXISTS market_observation_revision (
    revision_id BIGINT PRIMARY KEY,
    market_code VARCHAR NOT NULL,
    ticker VARCHAR NOT NULL,
    interval VARCHAR NOT NULL,
    field_group VARCHAR NOT NULL DEFAULT 'market_bar',
    market_session_date DATE NOT NULL,
    revision_no INTEGER NOT NULL,
    bar_closed_at TIMESTAMP WITH TIME ZONE,
    available_at TIMESTAMP WITH TIME ZONE NOT NULL,
    confirmed_at TIMESTAMP WITH TIME ZONE,
    superseded_at TIMESTAMP WITH TIME ZONE,
    revision_status VARCHAR NOT NULL,
    adj_open DOUBLE,
    adj_high DOUBLE,
    adj_low DOUBLE,
    adj_close DOUBLE,
    non_day_trade_volume DOUBLE,
    non_day_trade_turnover DOUBLE,
    close_utc TIMESTAMP WITH TIME ZONE,
    source_ref VARCHAR,
    source_hash VARCHAR,
    parser_version VARCHAR,
    calendar_version VARCHAR,
    UNIQUE (market_code, ticker, interval, field_group, market_session_date, revision_no)
)
"""
SQL_REVISION_COLUMNS = (
    "revision_id", "market_code", "ticker", "interval", "field_group",
    "market_session_date", "revision_no", "bar_closed_at", "available_at",
    "confirmed_at", "superseded_at", "revision_status", "adj_open", "adj_high",
    "adj_low", "adj_close", "non_day_trade_volume", "non_day_trade_turnover",
    "close_utc", "source_ref", "source_hash", "parser_version", "calendar_version",
)
_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


@dataclass(frozen=True)
class ReplayConfig:
    """Immutable replay policy shared by every cutoff in one run."""

    policy: ReplayPolicy = "confirmed_only"
    interval: str = "1d"
    decision_market: str = "TW"
    benchmark_market: str = "US"
    execution_lag_sessions: int = 1
    engine_version: str = "TW-QUANT-ENGINE-REPLAY/0.1.0"

    def __post_init__(self) -> None:
        if self.policy not in {"confirmed_only", "initial_release"}:
            raise ValueError("policy must be confirmed_only or initial_release")
        if not self.interval:
            raise ValueError("interval must not be empty")
        if self.execution_lag_sessions < 0:
            raise ValueError("execution_lag_sessions must be >= 0")


@dataclass(frozen=True)
class ReplaySession:
    """One decision session supplied by a versioned exchange calendar."""

    market_code: str
    session_date: date
    cutoff_utc: datetime
    status: str = "open"
    execution_utc: datetime | None = None
    calendar_version: str = "unknown"

    def __post_init__(self) -> None:
        if self.status not in {"open", "early_close"}:
            raise ValueError("replay sessions must be open or early_close")
        if self.cutoff_utc.tzinfo is None:
            raise ValueError("cutoff_utc must be timezone-aware")
        if self.execution_utc is not None and self.execution_utc.tzinfo is None:
            raise ValueError("execution_utc must be timezone-aware")


@dataclass
class ReplayManifest:
    """Audit metadata for one deterministic replay run."""

    replay_id: str
    cutoff_utc: str
    policy: ReplayPolicy
    engine_version: str
    ssot_version: str
    calendar_versions: dict[str, str]
    input_snapshot_hash: str
    output_hash: str
    rows_seen: int
    rows_excluded_as_unconfirmed: int
    future_rows_rejected: int
    data_quality: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def write_json(self, path: str | Path) -> Path:
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(
            json.dumps(self.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return destination


@dataclass
class ReplayResult:
    """Feature rows and manifests emitted by a replay run."""

    decisions: pl.DataFrame
    manifests: list[ReplayManifest]


class PointInTimeStore:
    """Immutable in-memory normalized revision store.

    The same contract can be backed by DuckDB or PostgreSQL later. The public
    method remains ``as_of`` so calculations never need to know the storage
    implementation.
    """

    def __init__(self, revisions: pl.DataFrame | pl.LazyFrame):
        frame = revisions.collect() if isinstance(revisions, pl.LazyFrame) else revisions.clone()
        self._frame = self._normalize(frame)

    @staticmethod
    def _normalize(frame: pl.DataFrame) -> pl.DataFrame:
        missing = REVISION_REQUIRED_COLUMNS - set(frame.columns)
        if missing:
            raise ValueError(f"revision store missing columns: {sorted(missing)}")
        if "field_group" not in frame.columns:
            frame = frame.with_columns(pl.lit("market_bar").alias("field_group"))
        for column in ("available_at", "confirmed_at", "bar_closed_at", "superseded_at"):
            if column in frame.columns:
                frame = frame.with_columns(
                    pl.col(column).cast(pl.Datetime(time_zone="UTC")).alias(column)
                )
        frame = frame.with_columns(
            pl.col("market_session_date").cast(pl.Date),
            pl.col("interval").cast(pl.String),
            pl.col("market_code").cast(pl.String),
            pl.col("ticker").cast(pl.String),
            pl.col("revision_status").cast(pl.String),
        )
        if frame.select(pl.col("revision_id").is_duplicated().any()).item():
            raise ValueError("revision_id must be globally unique")
        duplicate_versions = frame.select(
            pl.struct(REVISION_KEY + ["revision_no"]).is_duplicated().any()
        ).item()
        if duplicate_versions:
            raise ValueError("duplicate revision_no for an observation key")
        return frame.sort(REVISION_KEY + ["available_at", "revision_no", "revision_id"])

    @property
    def frame(self) -> pl.DataFrame:
        return self._frame.clone()

    def as_of(
        self,
        cutoff_utc: datetime,
        *,
        market_code: str | None = None,
        ticker: str | None = None,
        interval: str = "1d",
        policy: ReplayPolicy = "confirmed_only",
        max_session_date: date | None = None,
        fields: Sequence[str] | None = None,
    ) -> pl.DataFrame:
        """Return the latest revision visible at one historical cutoff.

        ``confirmed_only`` requires both ``available_at`` and
        ``confirmed_at`` to be no later than the cutoff. ``initial_release``
        permits provisional rows after their first availability, but keeps the
        quality state in the returned data. Future rows are never selected.
        """

        cutoff = _utc_datetime(cutoff_utc)
        if policy not in {"confirmed_only", "initial_release"}:
            raise ValueError("unknown replay policy")
        q = self._frame.filter(
            (pl.col("interval") == interval)
            & (pl.col("available_at") <= cutoff)
        )
        if market_code is not None:
            q = q.filter(pl.col("market_code") == market_code)
        if ticker is not None:
            q = q.filter(pl.col("ticker") == ticker)
        if max_session_date is not None:
            q = q.filter(pl.col("market_session_date") <= max_session_date)

        if "superseded_at" in q.columns:
            q = q.filter(
                pl.col("superseded_at").is_null()
                | (pl.col("superseded_at") > cutoff)
            )
        q = q.filter(pl.col("revision_status") != "retracted")
        if policy == "confirmed_only":
            q = q.filter(
                pl.col("revision_status").is_in(["confirmed", "final"])
                & pl.col("confirmed_at").is_not_null()
                & (pl.col("confirmed_at") <= cutoff)
            )
        else:
            q = q.filter(pl.col("revision_status").is_in(["provisional", "confirmed", "final"]))

        # The final row is the last version available at this cutoff. This is
        # the in-memory equivalent of ROW_NUMBER() OVER (...) in SQL.
        q = q.sort(REVISION_KEY + ["available_at", "revision_no", "revision_id"])
        q = q.unique(subset=REVISION_KEY, keep="last", maintain_order=True)
        q = q.sort(["market_code", "ticker", "market_session_date"])
        visible_future = q.filter(pl.col("available_at") > cutoff)
        if visible_future.height:
            raise AssertionError("as_of selected a row available after cutoff")
        if fields is not None:
            requested = list(dict.fromkeys(list(REVISION_KEY) + list(fields)))
            missing = set(requested) - set(q.columns)
            if missing:
                raise ValueError(f"requested fields missing from revision store: {sorted(missing)}")
            q = q.select(requested)
        return q

    def count_visible_excluded(self, cutoff_utc: datetime, **kwargs: Any) -> tuple[int, int]:
        """Return total candidate rows and rows excluded by confirmed-only policy."""

        cutoff = _utc_datetime(cutoff_utc)
        base = self._frame.filter(pl.col("available_at") <= cutoff)
        for key in ("market_code", "ticker", "interval"):
            if kwargs.get(key) is not None:
                base = base.filter(pl.col(key) == kwargs[key])
        visible = self.as_of(cutoff, **kwargs)
        return base.height, max(base.height - visible.height, 0)


class PointInTimeReader(Protocol):
    """Minimal backend contract consumed by ``DeterministicReplay``."""

    def as_of(
        self,
        cutoff_utc: datetime,
        *,
        market_code: str | None = None,
        ticker: str | None = None,
        interval: str = "1d",
        policy: ReplayPolicy = "confirmed_only",
        max_session_date: date | None = None,
        fields: Sequence[str] | None = None,
    ) -> pl.DataFrame: ...


class _DatabasePointInTimeStore:
    """DB-API implementation shared by DuckDB and PostgreSQL."""

    placeholder = "?"

    def __init__(self, connection: Any, *, table: str = "market_observation_revision"):
        if not _IDENTIFIER.fullmatch(table):
            raise ValueError("table must be a simple SQL identifier")
        self.connection = connection
        self.table = table

    def create_schema(self) -> None:
        self._execute(SQL_REVISION_SCHEMA.replace("market_observation_revision", self.table))

    def close(self) -> None:
        self.connection.close()

    def append(self, revisions: pl.DataFrame | pl.LazyFrame) -> int:
        """Validate and append normalized revisions without updating old rows."""

        frame = revisions.collect() if isinstance(revisions, pl.LazyFrame) else revisions.clone()
        normalized = PointInTimeStore._normalize(frame)
        missing = {"close_utc"} - set(normalized.columns)
        if missing:
            raise ValueError(f"database revision frame missing columns: {sorted(missing)}")
        columns = [column for column in SQL_REVISION_COLUMNS if column in normalized.columns]
        if set(REVISION_REQUIRED_COLUMNS) - set(columns):
            raise ValueError("database append does not satisfy revision contract")
        values = [tuple(row[column] for column in columns) for row in normalized.to_dicts()]
        placeholders = ", ".join([self.placeholder] * len(columns))
        query = (
            f"INSERT INTO {self.table} ({', '.join(columns)}) "
            f"VALUES ({placeholders})"
        )
        self._executemany(query, values)
        return len(values)

    def as_of(
        self,
        cutoff_utc: datetime,
        *,
        market_code: str | None = None,
        ticker: str | None = None,
        interval: str = "1d",
        policy: ReplayPolicy = "confirmed_only",
        max_session_date: date | None = None,
        fields: Sequence[str] | None = None,
    ) -> pl.DataFrame:
        """Run the same revision visibility contract in a persistent database."""

        cutoff = _utc_datetime(cutoff_utc)
        if policy not in {"confirmed_only", "initial_release"}:
            raise ValueError("unknown replay policy")
        where = ["o.interval = ?", "o.available_at <= ?"]
        params: list[Any] = [interval, cutoff]
        if market_code is not None:
            where.append("o.market_code = ?")
            params.append(market_code)
        if ticker is not None:
            where.append("o.ticker = ?")
            params.append(ticker)
        if max_session_date is not None:
            where.append("o.market_session_date <= ?")
            params.append(max_session_date)
        where.append("o.revision_status <> 'retracted'")
        if policy == "confirmed_only":
            where.extend([
                "o.revision_status IN ('confirmed', 'final')",
                "o.confirmed_at IS NOT NULL",
                "o.confirmed_at <= ?",
            ])
            params.append(cutoff)
        else:
            where.append("o.revision_status IN ('provisional', 'confirmed', 'final')")
        selected = ", ".join(f"o.{column}" for column in SQL_REVISION_COLUMNS)
        query = f"""
            SELECT {selected}
            FROM (
                SELECT {selected},
                       ROW_NUMBER() OVER (
                           PARTITION BY o.market_code, o.ticker, o.interval,
                                        o.field_group, o.market_session_date
                           ORDER BY o.available_at DESC,
                                    o.revision_no DESC,
                                    o.revision_id DESC
                       ) AS _rn
                FROM {self.table} o
                WHERE {' AND '.join(where)}
            ) visible
            WHERE _rn = 1
            ORDER BY market_code, ticker, market_session_date
        """.replace("SELECT o.", "SELECT ").replace("o.", "")
        # The replacement above keeps the query portable between DuckDB and
        # PostgreSQL while table/column identifiers remain controlled constants.
        frame = self._query(query, params)
        if fields is not None:
            requested = list(dict.fromkeys(list(REVISION_KEY) + list(fields)))
            missing = set(requested) - set(frame.columns)
            if missing:
                raise ValueError(f"requested fields missing from database: {sorted(missing)}")
            frame = frame.select(requested)
        return frame

    def count_visible_excluded(self, cutoff_utc: datetime, **kwargs: Any) -> tuple[int, int]:
        cutoff = _utc_datetime(cutoff_utc)
        where = ["available_at <= ?"]
        params: list[Any] = [cutoff]
        for key in ("market_code", "ticker", "interval"):
            if kwargs.get(key) is not None:
                where.append(f"{key} = ?")
                params.append(kwargs[key])
        total = self._scalar(
            f"SELECT COUNT(*) FROM {self.table} WHERE {' AND '.join(where)}",
            params,
        )
        visible = self.as_of(cutoff, **kwargs).height
        return int(total), max(int(total) - visible, 0)

    def _query(self, query: str, params: Sequence[Any]) -> pl.DataFrame:
        cursor = self._cursor()
        try:
            cursor.execute(self._adapt_placeholders(query), list(params))
            rows = cursor.fetchall()
            names = [item[0] for item in cursor.description]
        finally:
            self._close_cursor(cursor)
        return pl.DataFrame(rows, schema=names, orient="row") if rows else pl.DataFrame(schema=names)

    def _scalar(self, query: str, params: Sequence[Any]) -> Any:
        frame = self._query(query, params)
        return frame.item(0, 0)

    def _execute(self, query: str, params: Sequence[Any] | None = None) -> None:
        cursor = self._cursor()
        try:
            cursor.execute(self._adapt_placeholders(query), list(params or []))
        finally:
            self._close_cursor(cursor)
        self._commit()

    def _executemany(self, query: str, rows: Sequence[Sequence[Any]]) -> None:
        cursor = self._cursor()
        try:
            cursor.executemany(self._adapt_placeholders(query), rows)
        finally:
            self._close_cursor(cursor)
        self._commit()

    def _adapt_placeholders(self, query: str) -> str:
        return query if self.placeholder == "?" else query.replace("?", self.placeholder)

    def _cursor(self) -> Any:
        return self.connection.cursor()

    def _close_cursor(self, cursor: Any) -> None:
        close = getattr(cursor, "close", None)
        if close is not None:
            close()

    def _commit(self) -> None:
        commit = getattr(self.connection, "commit", None)
        if commit is not None:
            commit()


class DuckDBPointInTimeStore(_DatabasePointInTimeStore):
    """Persistent DuckDB backend; install with ``pip install duckdb``."""

    @classmethod
    def connect(
        cls,
        path: str | Path,
        *,
        table: str = "market_observation_revision",
        read_only: bool = False,
    ) -> "DuckDBPointInTimeStore":
        try:
            import duckdb
        except ImportError as exc:  # pragma: no cover - dependency-gated
            raise ImportError("DuckDB backend requires: pip install duckdb") from exc
        return cls(
            duckdb.connect(str(path), read_only=read_only),
            table=table,
        )


class PostgresPointInTimeStore(_DatabasePointInTimeStore):
    """PostgreSQL backend using psycopg 3; install with ``pip install psycopg[binary]``."""

    placeholder = "%s"

    @classmethod
    def connect(
        cls,
        dsn: str,
        *,
        table: str = "market_observation_revision",
    ) -> "PostgresPointInTimeStore":
        try:
            import psycopg
        except ImportError as exc:  # pragma: no cover - dependency-gated
            raise ImportError("PostgreSQL backend requires: pip install psycopg[binary]") from exc
        return cls(psycopg.connect(dsn), table=table)


class DeterministicReplay:
    """Run the same feature function on each historical information set."""

    def __init__(
        self,
        store: PointInTimeReader,
        *,
        config: ReplayConfig | None = None,
        ssot_version: str = "TW-QUANT-ENGINE-SSOT/0.3.0",
    ):
        self.store = store
        self.config = config or ReplayConfig()
        self.ssot_version = ssot_version

    def run(
        self,
        sessions: Iterable[ReplaySession],
        *,
        feature_fn: Callable[..., pl.DataFrame] = build_feature_matrix,
        feature_kwargs: Mapping[str, Any] | None = None,
        decision_fn: Callable[[pl.DataFrame], Mapping[str, Any] | None] | None = None,
    ) -> ReplayResult:
        """Replay features at each decision cutoff and emit audit manifests."""

        rows: list[pl.DataFrame] = []
        manifests: list[ReplayManifest] = []
        kwargs = dict(feature_kwargs or {})
        for session in sessions:
            if session.market_code != self.config.decision_market:
                raise ValueError("session market does not match ReplayConfig.decision_market")
            tw_visible = self.store.as_of(
                session.cutoff_utc,
                market_code=self.config.decision_market,
                interval=self.config.interval,
                policy=self.config.policy,
                max_session_date=session.session_date,
            )
            us_visible = self.store.as_of(
                session.cutoff_utc,
                market_code=self.config.benchmark_market,
                interval=self.config.interval,
                policy=self.config.policy,
                max_session_date=None,
            )
            tw_engine = _to_engine_frame(tw_visible)
            benchmark = _build_benchmark(tw_visible, us_visible)
            call_kwargs = dict(kwargs)
            call_kwargs["benchmark"] = benchmark
            feature_frame = feature_fn(tw_engine, **call_kwargs)
            current = _latest_session(feature_frame, session.session_date)
            if current.is_empty():
                continue
            if decision_fn is not None:
                decision = decision_fn(current)
                if decision:
                    current = current.with_columns(
                        [pl.lit(value).alias(key) for key, value in decision.items()]
                    )
            current = current.with_columns([
                pl.lit(session.cutoff_utc).alias("replay_cutoff_utc"),
                pl.lit(self.config.policy).alias("replay_policy"),
                pl.lit(session.calendar_version).alias("calendar_version"),
                pl.lit(session.execution_utc).alias("execution_utc"),
            ])
            rows.append(current)
            total_seen, excluded = self.store.count_visible_excluded(
                session.cutoff_utc,
                market_code=self.config.decision_market,
                interval=self.config.interval,
                policy=self.config.policy,
                max_session_date=session.session_date,
            )
            manifests.append(ReplayManifest(
                replay_id=f"{session.cutoff_utc.isoformat()}__{self.config.decision_market}__{self.config.policy}",
                cutoff_utc=session.cutoff_utc.isoformat(),
                policy=self.config.policy,
                engine_version=self.config.engine_version,
                ssot_version=self.ssot_version,
                calendar_versions={self.config.decision_market: session.calendar_version},
                input_snapshot_hash=stable_frame_hash(tw_visible),
                output_hash=stable_frame_hash(current),
                rows_seen=total_seen,
                rows_excluded_as_unconfirmed=excluded,
                future_rows_rejected=0,
                data_quality={
                    "benchmark_rows": us_visible.height,
                    "aligned_benchmark_rows": benchmark.height,
                },
            ))
        decisions = pl.concat(rows, how="diagonal_relaxed") if rows else pl.DataFrame()
        return ReplayResult(decisions=decisions, manifests=manifests)


def _utc_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ValueError("cutoff timestamps must be timezone-aware")
    return value.astimezone(timezone.utc)


def _to_engine_frame(frame: pl.DataFrame) -> pl.DataFrame:
    """Map normalized market storage columns to the calculation contract."""

    if "market_session_date" not in frame.columns:
        raise ValueError("revision frame needs market_session_date")
    result = frame.rename({"market_session_date": "date"})
    if "adj_high" in result.columns and "adj_low" in result.columns:
        return result
    if {"high", "low", "close"}.issubset(result.columns):
        return result
    raise ValueError("replay price rows need adj_high/adj_low or high/low/close")


def _build_benchmark(tw: pl.DataFrame, us: pl.DataFrame) -> pl.DataFrame:
    if tw.is_empty() or us.is_empty():
        return pl.DataFrame({"date": [], "adj_close": []}, schema={"date": pl.Date, "adj_close": pl.Float64})
    # Availability is market-session based. Multiple TW securities and
    # multiple US benchmark rows should not duplicate the benchmark join.
    tw_line = tw.sort(["market_session_date", "close_utc"]).unique(
        subset=["market_session_date"], keep="first"
    )
    us_line = us.sort(["market_session_date", "close_utc"]).unique(
        subset=["market_session_date"], keep="first"
    )
    combined = pl.concat([
        tw_line.select(["market_code", "market_session_date", "close_utc", "adj_close"]),
        us_line.select(["market_code", "market_session_date", "close_utc", "adj_close"]),
    ], how="vertical_relaxed")
    aligned = align_confirmed_closes(combined, left_market="TW", right_market="US")
    return aligned.select([
        pl.col("session_date").alias("date"),
        pl.col("right_adj_close").alias("adj_close"),
    ])


def _latest_session(frame: pl.DataFrame, session_date: date) -> pl.DataFrame:
    if "date" not in frame.columns:
        raise ValueError("feature function must return a date column")
    return frame.filter(pl.col("date") == session_date)


def stable_frame_hash(frame: pl.DataFrame | pl.LazyFrame) -> str:
    """Hash a frame independently of row order while preserving values."""

    df = frame.collect() if isinstance(frame, pl.LazyFrame) else frame
    if df.is_empty():
        payload = {"columns": df.columns, "rows": []}
    else:
        sort_columns = list(df.columns)
        canonical = df.sort(sort_columns).to_dicts()
        payload = {"columns": df.columns, "rows": canonical}
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def assert_no_future_rows(
    frame: pl.DataFrame | pl.LazyFrame,
    cutoff_utc: datetime,
    *,
    timestamp_col: str = "available_at",
) -> None:
    """Raise if an input snapshot contains a row unavailable at cutoff."""

    cutoff = _utc_datetime(cutoff_utc)
    df = frame.collect() if isinstance(frame, pl.LazyFrame) else frame
    if timestamp_col not in df.columns:
        raise ValueError(f"frame missing timestamp column: {timestamp_col}")
    future = df.filter(pl.col(timestamp_col) > cutoff)
    if future.height:
        raise AssertionError(
            f"future rows detected: {future.height} rows have {timestamp_col} > cutoff"
        )


def assert_future_append_invariant(
    before: pl.DataFrame,
    after: pl.DataFrame,
    cutoff_utc: datetime,
    *,
    key_columns: Sequence[str] = ("market_code", "ticker", "interval", "market_session_date"),
) -> None:
    """Assert that appending future data does not alter the past snapshot."""

    cutoff = _utc_datetime(cutoff_utc)
    before_past = before.filter(pl.col("available_at") <= cutoff).sort(list(key_columns))
    after_past = after.filter(pl.col("available_at") <= cutoff).sort(list(key_columns))
    if stable_frame_hash(before_past) != stable_frame_hash(after_past):
        raise AssertionError("future append changed the historical point-in-time snapshot")


def build_replay_sessions(
    calendar: pl.DataFrame | pl.LazyFrame,
    *,
    market_code: str = "TW",
    start: date | None = None,
    end: date | None = None,
    execution_lag_sessions: int = 1,
) -> list[ReplaySession]:
    """Convert an official calendar table into validated replay sessions."""

    frame = calendar.collect() if isinstance(calendar, pl.LazyFrame) else calendar
    required = {"market_code", "session_date", "status", "close_utc"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"calendar missing columns: {sorted(missing)}")
    frame = frame.filter(
        (pl.col("market_code") == market_code)
        & pl.col("status").is_in(["open", "early_close"])
    ).sort("session_date")
    if start is not None:
        frame = frame.filter(pl.col("session_date") >= start)
    if end is not None:
        frame = frame.filter(pl.col("session_date") <= end)
    dates = frame.get_column("session_date").to_list()
    close_times = frame.get_column("close_utc").to_list()
    execution_times = frame.get_column("open_utc").to_list() if "open_utc" in frame.columns else close_times
    status = frame.get_column("status").to_list()
    version = frame.get_column("calendar_version").to_list() if "calendar_version" in frame.columns else ["unknown"] * frame.height
    sessions: list[ReplaySession] = []
    for index, (session_date, close_utc, session_status) in enumerate(zip(dates, close_times, status)):
        execution_index = index + execution_lag_sessions
        execution = execution_times[execution_index] if execution_index < len(execution_times) else None
        sessions.append(ReplaySession(
            market_code=market_code,
            session_date=session_date,
            cutoff_utc=_utc_datetime(close_utc),
            status=session_status,
            execution_utc=execution,
            calendar_version=version[index],
        ))
    return sessions


__all__ = [
    "DeterministicReplay",
    "DuckDBPointInTimeStore",
    "PostgresPointInTimeStore",
    "PointInTimeStore",
    "PointInTimeReader",
    "ReplayConfig",
    "ReplayManifest",
    "ReplayResult",
    "ReplaySession",
    "ReplayPolicy",
    "align_confirmed_closes",
    "assert_future_append_invariant",
    "assert_no_future_rows",
    "build_replay_sessions",
    "normalize_market_timestamp",
    "stable_frame_hash",
    "SQL_REVISION_SCHEMA",
]
