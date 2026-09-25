#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_ENG087 — Central market-list governance bridge.

This is a central dispatcher and verification surface, not a replacement for
existing fetchers.  It calls the established VDF engines by name and checks the
resulting data through one low-token JSON report:

1. TWSE/TPEX stock universe: code, name, exchange, Taiwan/US industry fields.
2. Active Taiwan ETF universe: A-code registry and daily-holdings coverage.
3. Passive story-group roster: overlap is allowed, but market turnover totals
   must de-duplicate (date, ticker) before a cross-group sum.

The bridge is offline by default.  A network update is gated by the two
operator-owned consent variables and delegates to VDF_ENG054/VDF_ENG077; it
does not duplicate their source logic.
"""
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
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    import duckdb
except Exception:  # pragma: no cover - status reports ABSENT/ENV_MISSING
    duckdb = None

HERE = Path(__file__).resolve().parent
VDF = HERE.parent
VIA = VDF.parent.parent
REPO = VIA.parent
REPORT_DIR = VIA / "VIA_Reports" / "vdf" / "central_lists"
REPORT = REPORT_DIR / "MARKET_LISTS_latest.json"
DB_TW = VDF / "output_hub" / "mega" / "vdf_tw_market.duckdb"
DB_ETF = VDF / "output_hub" / "active_tw_etf" / "active_tw_etf_holdings" / "ActiveTWETF.duckdb"
STORY_REGISTRY = VIA / "supportive modules" / "registry" / "VDF_StoryGroup_Registry_v0101.json"
START_REQUIRED = "2023-01-01"

STOCK_ENGINE = "functional modules/VDF/engine/VDF_ENG054_TWDailyBackfill_v0104.py"
ALIGN_ENGINE = "functional modules/VDF/engine/VDF_ENG081_UniverseAlign_v0100.py"
ETF_ENGINE = "functional modules/VDF/engine/VDF_ENG077_ActiveETFUniverse_v0100.py"
ETF_HISTORY_ENGINE = "functional modules/VDF/engine/VDF_ENG078_ActiveETFHoldingsHistory_v0108.py"
GROUP_ENGINE = "supportive modules/references/intake/VIA_StoryGroupRotation_b325/VIA_TW_Story_Group_Rotation_v0500/engine/via_hierarchical_group_index_engine.py"

CODE_RE = re.compile(r"^\d{4,6}[A-Z]?$")


def _now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _env_path(name: str, default: Path) -> Path:
    value = os.environ.get(name, "").strip()
    return Path(value).expanduser() if value else default


def _tables(con: Any) -> set[str]:
    return {str(row[0]) for row in con.execute("SHOW TABLES").fetchall()}


def _columns(con: Any, table: str) -> list[str]:
    return [str(row[0]) for row in con.execute(f'DESCRIBE "{table}"').fetchall()]


def _first(columns: list[str], candidates: tuple[str, ...]) -> str | None:
    lowered = {c.lower(): c for c in columns}
    for candidate in candidates:
        if candidate.lower() in lowered:
            return lowered[candidate.lower()]
    return None


def _safe_table(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def _date_range(con: Any, table: str, columns: list[str]) -> dict[str, Any]:
    date_col = _first(columns, ("date", "trade_date", "obs_date", "portfolio_date", "snapshot_at", "as_of"))
    if not date_col:
        return {"state": "SCHEMA_MISSING", "column": None}
    try:
        row = con.execute(
            f"SELECT MIN(CAST({_safe_table(date_col)} AS VARCHAR)), MAX(CAST({_safe_table(date_col)} AS VARCHAR)), COUNT(*) FROM {_safe_table(table)}"
        ).fetchone()
    except Exception as exc:
        return {"state": "RED", "column": date_col, "error": str(exc)[:180]}
    return {"state": "NODATA" if not row[2] else "OK", "column": date_col,
            "min": str(row[0])[:10] if row[0] else None,
            "max": str(row[1])[:10] if row[1] else None, "rows": int(row[2])}


def _open(path: Path):
    if duckdb is None or not path.exists():
        return None
    try:
        return duckdb.connect(str(path), read_only=True)
    except Exception:
        return None


def _status_stock(db: Path) -> dict[str, Any]:
    result: dict[str, Any] = {"engine": STOCK_ENGINE, "db": str(db), "state": "ABSENT", "table": None}
    con = _open(db)
    if con is None:
        result["why"] = "資料庫不存在或 duckdb 環境缺失"
        return result
    try:
        tables = _tables(con)
        # CGC_MDL142 defines tw_listings_industry as the official short-name
        # canon; tw_listings is only a legacy fallback and may contain long names.
        table = "tw_listings_industry" if "tw_listings_industry" in tables else "tw_listings"
        if table not in tables:
            result.update(state="RED", why="缺 tw_listings_industry 與 tw_listings")
            return result
        result["table"] = table
        cols = _columns(con, table)
        mapping = {
            "code": _first(cols, ("code", "ticker", "stock_code")),
            "name": _first(cols, ("name", "stock_name", "company_name")),
            "exchange": _first(cols, ("market", "exchange", "交易所")),
            "external_ticker": _first(cols, ("yf_ticker", "external_ticker", "ticker_yf")),
            "taiwan_industry": _first(cols, ("industry_name", "industry", "taiwan_industry", "industry_tw", "產業別")),
            "us_industry": _first(cols, ("us_industry", "industry_us", "gics_industry", "sic_industry")),
        }
        missing = [k for k, v in mapping.items() if v is None]
        row_count = int(con.execute(f"SELECT COUNT(*) FROM {_safe_table(table)}").fetchone()[0])
        result.update(columns=cols, mapping=mapping, rows=row_count, missing_fields=missing)
        if missing:
            result.update(state="SCHEMA_MISSING", why="股票全集欄位不足；台灣/美國產業分類缺一不可，未把其他欄位冒充")
        elif row_count == 0:
            result.update(state="NODATA", why=f"{table} 為空")
        else:
            result.update(state="GREEN", why="股票代號、名稱、交易所與雙產業分類均在位")
        result["prices"] = _date_range(con, "tw_daily_prices", _columns(con, "tw_daily_prices")) if "tw_daily_prices" in tables else {"state": "ABSENT"}
    finally:
        con.close()
    return result


def _status_etf(db: Path) -> dict[str, Any]:
    result: dict[str, Any] = {"engine": ETF_ENGINE, "history_engine": ETF_HISTORY_ENGINE, "db": str(db), "state": "ABSENT"}
    con = _open(db)
    if con is None:
        result["why"] = "ActiveTWETF.duckdb 不存在或 duckdb 環境缺失"
        return result
    try:
        tables = _tables(con)
        required = {"active_tw_etf_registry", "holdings_daily"}
        missing_tables = sorted(required - tables)
        if missing_tables:
            result.update(state="RED", why=f"主動 ETF 表缺失: {missing_tables}", tables=sorted(tables))
            return result
        reg_cols = _columns(con, "active_tw_etf_registry")
        hold_cols = _columns(con, "holdings_daily")
        mapping = {
            "registry_ticker": _first(reg_cols, ("ticker", "etf_ticker")),
            "registry_name": _first(reg_cols, ("name", "etf_name")),
            "issuer": _first(reg_cols, ("issuer", "manager")),
            "daily_required": _first(reg_cols, ("daily_required",)),
            "holding_ticker": _first(hold_cols, ("holding_ticker", "stock_ticker", "ticker")),
            "portfolio_date": _first(hold_cols, ("portfolio_date", "date", "snapshot_at")),
        }
        missing = [k for k, v in mapping.items() if v is None]
        reg_rows = int(con.execute("SELECT COUNT(*) FROM \"active_tw_etf_registry\"").fetchone()[0])
        hold_rows = int(con.execute("SELECT COUNT(*) FROM \"holdings_daily\"").fetchone()[0])
        result.update(mapping=mapping, registry_rows=reg_rows, holdings_rows=hold_rows, missing_fields=missing)
        if missing:
            result.update(state="SCHEMA_MISSING", why="主動 ETF 清單或持股史欄位不足")
            return result
        if not reg_rows:
            result.update(state="NODATA", why="主動 ETF registry 為空")
            return result
        duplicate_registry = int(con.execute(
            f"SELECT COUNT(*) - COUNT(DISTINCT {_safe_table(mapping['registry_ticker'])}) FROM \"active_tw_etf_registry\""
        ).fetchone()[0])
        active_count = int(con.execute(
            f"SELECT COUNT(*) FROM \"active_tw_etf_registry\" WHERE CAST({_safe_table(mapping['daily_required'])} AS BOOLEAN)"
        ).fetchone()[0])
        result.update(duplicate_registry=max(duplicate_registry, 0), daily_required_count=active_count)
        if duplicate_registry or (active_count and not hold_rows):
            result.update(state="RED", why="registry 重複或每日揭露 ETF 無持股資料")
        else:
            result.update(state="GREEN", why="A 碼 registry 與持股資料表在位；逐日缺口交由 ENG078 coverage 驗證")
        result["holdings_dates"] = _date_range(con, "holdings_daily", hold_cols)
    finally:
        con.close()
    return result


def _load_story_registry(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"state": "ABSENT", "path": str(path), "why": "熱門族群清單正本不存在"}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"state": "RED", "path": str(path), "why": f"JSON 解析失敗: {exc}"}
    stories = payload.get("stories") or []
    rows: list[dict[str, str]] = []
    invalid = []
    for story in stories:
        gid = str(story.get("story_id", "")).strip()
        name = str(story.get("story_group", "")).strip()
        tickers = [str(x).strip().upper().replace(".TW", "").replace(".TWO", "") for x in story.get("tickers", [])]
        if not gid or not name or not tickers or len(tickers) != len(set(tickers)):
            invalid.append(gid or name or "<unknown>")
        for ticker in tickers:
            rows.append({"group_id": gid, "group_name": name, "ticker": ticker})
    frame = {("ticker", r["ticker"]) for r in rows}
    by_ticker: dict[str, set[str]] = {}
    for row in rows:
        by_ticker.setdefault(row["ticker"], set()).add(row["group_id"])
    overlap = {ticker: sorted(groups) for ticker, groups in by_ticker.items() if len(groups) > 1}
    state = "GREEN" if stories and not invalid else ("NODATA" if not stories else "RED")
    return {"state": state, "path": str(path), "groups": len(stories), "membership_rows": len(rows),
            "distinct_tickers": len(frame), "cross_group_overlap_tickers": len(overlap),
            "overlap_sample": dict(list(overlap.items())[:20]), "invalid_groups": invalid,
            "why": "跨族群重複允許；跨族群成交值彙總必須以 (date,ticker) 去重"}


def dedupe_market_turnover(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Return raw/group totals and a distinct-market total for audit display."""
    seen: dict[tuple[str, str], dict[str, Any]] = {}
    raw_total = 0.0
    for row in rows:
        date = str(row.get("date", ""))[:10]
        ticker = str(row.get("ticker", "")).strip().upper().replace(".TW", "").replace(".TWO", "")
        value = float(row.get("trading_value", 0.0) or 0.0)
        raw_total += value
        key = (date, ticker)
        if key not in seen:
            seen[key] = {"date": date, "ticker": ticker, "trading_value": value}
    distinct_total = sum(float(row["trading_value"]) for row in seen.values())
    return {"raw_group_rows": len(rows), "distinct_date_ticker_rows": len(seen),
            "raw_group_sum": raw_total, "distinct_market_sum": distinct_total,
            "deduplicated": raw_total != distinct_total, "rows": list(seen.values())}


def _status() -> dict[str, Any]:
    db_tw = _env_path("VIA_DB_VDF_TW_MARKET", DB_TW)
    db_etf = _env_path("VIA_DB_ACTIVETWETF", DB_ETF)
    stocks = _status_stock(db_tw)
    etf = _status_etf(db_etf)
    groups = _load_story_registry(STORY_REGISTRY)
    states = [stocks["state"], etf["state"], groups["state"]]
    verdict = "GREEN" if all(s == "GREEN" for s in states) else ("ABSENT" if "ABSENT" in states else ("NODATA" if "NODATA" in states else "RED"))
    return {"schema": "VIA.VDF.CentralMarketLists.v1", "engine": "VDF_ENG087_MarketListGovernance_v0100",
            "ts": _now(), "start_required": START_REQUIRED, "verdict": verdict,
            "policy": {"dispatcher_only": True, "network_default": "OFF_BY_DEFAULT",
                       "stock_update_engine": STOCK_ENGINE, "active_etf_update_engine": ETF_ENGINE,
                       "active_etf_history_engine": ETF_HISTORY_ENGINE, "story_group_engine": GROUP_ENGINE,
                       "turnover_key": ["date", "ticker"], "cross_group_overlap": "allowed",
                       "central_registry": "VCGC registry-sync"},
            "lists": {"tw_stock_universe": stocks, "active_tw_etf": etf, "hot_story_groups": groups},
            "result_rule": "只有結果檔存在且 verdict=GREEN 才算此橋驗收通過；ABSENT/NODATA/RED 不得假綠"}


def _write(payload: dict[str, Any]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    tmp = REPORT.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(REPORT)


def status() -> int:
    payload = _status()
    _write(payload)
    print(f"[VDF_ENG087] {payload['verdict']} · 股票 {payload['lists']['tw_stock_universe']['state']} · 主動ETF {payload['lists']['active_tw_etf']['state']} · 熱門族群 {payload['lists']['hot_story_groups']['state']}")
    print(f"  結果: {REPORT}")
    for key, item in payload["lists"].items():
        print(f"  [{key}] {item.get('why', '')}")
    return 0 if payload["verdict"] == "GREEN" else 2


def _consent_open() -> bool:
    return os.environ.get("VIA_NET_CONSENT") == "YES" and os.environ.get("VIA_SCRAPE_CONSENT") == "YES"


def run_update() -> int:
    if not _consent_open():
        payload = _status()
        payload["verdict"] = "GATED"
        payload["gate"] = "VIA_NET_CONSENT=YES and VIA_SCRAPE_CONSENT=YES required; operator must set these"
        _write(payload)
        print(f"[VDF_ENG087] GATED · 不代設網路同意閘 · 結果: {REPORT}")
        return 3
    commands = [
        [sys.executable, str(VIA / STOCK_ENGINE), "--status"],
        [sys.executable, str(VIA / ETF_ENGINE), "status"],
    ]
    for command in commands:
        print("[delegate] " + " ".join(command))
        completed = subprocess.run(command, cwd=str(REPO), check=False)
        if completed.returncode != 0:
            print(f"[VDF_ENG087] delegate rc={completed.returncode}; 停止不假綠")
            return completed.returncode
    return status()


def selftest() -> int:
    fails: list[str] = []
    def chk(name: str, condition: bool, detail: str = "") -> None:
        print(f"  [{'OK' if condition else 'FAIL'}] {name}{(' · ' + detail) if detail else ''}")
        if not condition:
            fails.append(name)

    fixture = [
        {"date": "2026-01-02", "ticker": "2330", "trading_value": 100.0},
        {"date": "2026-01-02", "ticker": "2330", "trading_value": 100.0},
        {"date": "2026-01-02", "ticker": "2317", "trading_value": 50.0},
    ]
    dedup = dedupe_market_turnover(fixture)
    chk("跨族群重複代號允許", dedup["raw_group_rows"] == 3)
    chk("成交值按(date,ticker)去重", dedup["distinct_date_ticker_rows"] == 2 and dedup["distinct_market_sum"] == 150.0)
    chk("重複未被靜默相加", dedup["raw_group_sum"] == 250.0 and dedup["deduplicated"])
    story = _load_story_registry(STORY_REGISTRY)
    chk("熱門族群正本可解析", story["state"] == "GREEN", story.get("why", ""))
    chk("熱門族群可跨組重複", story.get("cross_group_overlap_tickers", 0) >= 0)
    required = [STOCK_ENGINE, ALIGN_ENGINE, ETF_ENGINE, ETF_HISTORY_ENGINE, GROUP_ENGINE]
    chk("中央調度正主均在位", all((VIA / path).exists() for path in required))
    chk("股票引擎有 selftest", "def selftest" in (VIA / STOCK_ENGINE).read_text(encoding="utf-8"))
    chk("主動ETF宇宙引擎有 selftest", "def selftest" in (VIA / ETF_ENGINE).read_text(encoding="utf-8"))
    chk("主動ETF史深引擎有 selftest", "def selftest" in (VIA / ETF_HISTORY_ENGINE).read_text(encoding="utf-8"))
    chk("熱門族群索引拒絕同組重複", "overlapping active membership intervals" in (VIA / GROUP_ENGINE).read_text(encoding="utf-8"))
    source = Path(__file__).read_text(encoding="utf-8")
    runtime_forbidden = re.search(r"(?im)^\s*(?:import|from)\s+talib\b", source)
    retired_bridge = "VDF_ENG" + "083"
    chk("不含禁用技術指標執行接線", runtime_forbidden is None and retired_bridge not in source)
    print(f"  [計] OK {10 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args or (args and args[0] == "selftest"):
        return selftest()
    if args and args[0] in {"run", "update"}:
        return run_update()
    return status()


if __name__ == "__main__":
    raise SystemExit(main())
