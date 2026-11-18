#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF fetch: S&P 500 GICS sector weights reconstructed from the latest anchor and SPDR prices.

Does not read 13F and does not score funds. VQG owns that.
History is price drift, not a stored official back history. The label says so.

  py -3 VDF_ENG240_SP500SectorWeight_v0100.py selftest
  py -3 VDF_ENG240_SP500SectorWeight_v0100.py fetch --out DIR [--start 2018-01-01]
"""
from __future__ import annotations

# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(SUP_MDL737 最新尾版;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    _sa_env = __import__("os").environ.get("VIA")
    if _sa_env:
        _sa_sys.path.insert(0, _sa_env)
        _sa_hit = _sa_Path(_sa_env) / "supportive modules"
        if (_sa_hit / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_hit))
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
except Exception:
    VIA_ACCEL = None
# ===== [VIA:ACCEL-BRIDGE:END] =====
# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(via_net_unified 最新→SUP_MDL740;graceful) =====
VIA_NET_TOOL_PATH = None
try:
    from pathlib import Path as _nb_Path
    _nb_candidates = []
    _nb_env = __import__("os").environ.get("VIA")
    if _nb_env:
        _nb_candidates.append(_nb_Path(_nb_env))
    _nb_p = _nb_Path(__file__).resolve()
    while _nb_p.parent != _nb_p:
        _nb_candidates.append(_nb_p)
        _nb_p = _nb_p.parent
    for _nb_p in _nb_candidates:
        _nb_dir = _nb_p / "supportive modules" / "network"
        if _nb_dir.exists():
            _nb_hits = sorted(_nb_dir.glob("via_net_unified_v*.py"))
            if _nb_hits:
                VIA_NET_TOOL_PATH = str(_nb_hits[-1])
            break
except Exception:
    VIA_NET_TOOL_PATH = None


def _via_net():
    """Newest via_net_unified. None when the tool or consent path is absent."""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        module = _nb_ilu.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import json
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

SECTORS = (
    {"gics_sector": "Information Technology", "spdr_etf": "XLK", "yf_spy_key": "technology", "fallback_wt": 31.8},
    {"gics_sector": "Financials", "spdr_etf": "XLF", "yf_spy_key": "financial_services", "fallback_wt": 13.4},
    {"gics_sector": "Health Care", "spdr_etf": "XLV", "yf_spy_key": "healthcare", "fallback_wt": 11.2},
    {"gics_sector": "Consumer Discretionary", "spdr_etf": "XLY", "yf_spy_key": "consumer_cyclical", "fallback_wt": 10.6},
    {"gics_sector": "Communication Services", "spdr_etf": "XLC", "yf_spy_key": "communication_services", "fallback_wt": 9.1},
    {"gics_sector": "Industrials", "spdr_etf": "XLI", "yf_spy_key": "industrials", "fallback_wt": 8.4},
    {"gics_sector": "Consumer Staples", "spdr_etf": "XLP", "yf_spy_key": "consumer_defensive", "fallback_wt": 5.7},
    {"gics_sector": "Energy", "spdr_etf": "XLE", "yf_spy_key": "energy", "fallback_wt": 3.3},
    {"gics_sector": "Utilities", "spdr_etf": "XLU", "yf_spy_key": "utilities", "fallback_wt": 2.4},
    {"gics_sector": "Real Estate", "spdr_etf": "XLRE", "yf_spy_key": "realestate", "fallback_wt": 2.1},
    {"gics_sector": "Materials", "spdr_etf": "XLB", "yf_spy_key": "basic_materials", "fallback_wt": 2.0},
)
MOPS_HOSTS = ("mops.twse.com.tw", "mopsov.twse.com.tw", "mopsfin.twse.com.tw")


def http_json(url: str):
    host = urllib.parse.urlparse(url).hostname or ""
    if host in MOPS_HOSTS:
        raise RuntimeError("MOPS blocked")
    net = _via_net()
    if net is not None:
        got = net.http_json(url)
        if isinstance(got, dict) and got.get("state") == "OK" and got.get("data") is not None:
            return got["data"]
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
    last = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=40) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            last = exc
            time.sleep(0.4 * (attempt + 1))
    raise last


def chart_closes(symbol: str, start: str) -> list[dict]:
    period1 = int(datetime.fromisoformat(start).replace(tzinfo=timezone.utc).timestamp())
    url = (
        "https://query1.finance.yahoo.com/v8/finance/chart/"
        + urllib.parse.quote(symbol)
        + "?period1=%d&period2=%d&interval=1d" % (period1, int(time.time()) + 86400)
    )
    payload = http_json(url)
    result = ((payload.get("chart") or {}).get("result") or [None])[0] or {}
    stamps = result.get("timestamp") or []
    quote = ((result.get("indicators") or {}).get("quote") or [{}])[0]
    closes = quote.get("close") or []
    rows = []
    for i, stamp in enumerate(stamps):
        if i < len(closes) and closes[i] is not None:
            rows.append({
                "symbol": symbol,
                "date": datetime.fromtimestamp(stamp, timezone.utc).date().isoformat(),
                "close": float(closes[i]),
            })
    return rows


def anchor_weights() -> tuple[dict, str]:
    """Latest SPY sector weights. Fallback is labeled, never called official."""
    fallback = {row["gics_sector"]: row["fallback_wt"] for row in SECTORS}
    _via_net()
    try:
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor())
        opener.open(urllib.request.Request("https://fc.yahoo.com", headers={"User-Agent": "Mozilla/5.0"}), timeout=20).read(80)
        crumb = opener.open(urllib.request.Request("https://query1.finance.yahoo.com/v1/test/getcrumb", headers={"User-Agent": "Mozilla/5.0"}), timeout=20).read().decode()
        url = "https://query1.finance.yahoo.com/v10/finance/quoteSummary/SPY?modules=topHoldings&crumb=" + urllib.parse.quote(crumb)
        raw = opener.open(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=30).read()
        sectors = json.loads(raw.decode())["quoteSummary"]["result"][0]["topHoldings"]["sectorWeightings"]
        found = {}
        for item in sectors:
            if not isinstance(item, dict):
                continue
            for key, value in item.items():
                found[key] = float(value) * 100.0
        mapped = {row["gics_sector"]: found.get(row["yf_spy_key"], 0.0) for row in SECTORS}
        total = sum(mapped.values())
        if total > 80.0:
            return {key: value * 100.0 / total for key, value in mapped.items()}, "SPY_OFFICIAL_DRIFTED"
    except Exception:
        pass
    total = sum(fallback.values())
    return {key: value * 100.0 / total for key, value in fallback.items()}, "CALIBRATED_BASELINE_DRIFTED"


def quarter_ends(days: list[str]) -> list[str]:
    picked = {}
    for day in sorted(days):
        year, month = int(day[:4]), int(day[5:7])
        quarter = (month - 1) // 3 + 1
        picked[(year, quarter)] = day
    return [picked[key] for key in sorted(picked)]


def reconstruct(prices: dict[str, dict[str, float]], weights: dict[str, float], days: list[str], source: str) -> list[dict]:
    """Wi,t = Wi,T * (Pi,t / Pi,T) / sum_j, then times 100. T is the last price date."""
    last_day = max(days)
    latest = {row["spdr_etf"]: prices[row["spdr_etf"]][last_day] for row in SECTORS}
    now = datetime.now(timezone.utc).isoformat()
    out = []
    for day in days:
        raw = {}
        px = {}
        for row in SECTORS:
            etf = row["spdr_etf"]
            price_t = prices[etf][day]
            price_T = latest[etf]
            raw[row["gics_sector"]] = weights[row["gics_sector"]] * (price_t / price_T if price_T else 1.0)
            px[row["gics_sector"]] = price_t
        scale = sum(raw.values()) or 1.0
        for row in SECTORS:
            name = row["gics_sector"]
            out.append({
                "report_date": day,
                "gics_sector": name,
                "spdr_sector_etf": row["spdr_etf"],
                "etf_close_price": round(px[name], 4),
                "sp500_weight_pct": round(raw[name] / scale * 100.0, 4),
                "weight_source": source,
                "updated_at": now,
            })
    return out


def aligned_prices(frames: dict[str, list[dict]]) -> dict[str, dict[str, float]]:
    common = None
    maps = {}
    for row in SECTORS:
        etf = row["spdr_etf"]
        maps[etf] = {item["date"]: item["close"] for item in frames[etf]}
        common = set(maps[etf]) if common is None else common & set(maps[etf])
    days = sorted(common)
    return {etf: {day: maps[etf][day] for day in days} for etf in maps}, days


def store(out: Path, prices_rows: list[dict], weight_rows: list[dict]) -> None:
    import duckdb
    out.mkdir(parents=True, exist_ok=True)
    def dump(name, rows):
        path = out / (name + ".jsonl")
        with path.open("w", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(row) + "\n")
        return path
    con = duckdb.connect(str(out / "sp500_sector.duckdb"))
    con.execute("CREATE SCHEMA IF NOT EXISTS canon")
    px = dump("prices", prices_rows)
    wt = dump("weights", weight_rows)
    def q(path: Path) -> str:
        return "'" + path.as_posix().replace("'", "''") + "'"
    con.execute("CREATE OR REPLACE TABLE canon.spdr_prices AS SELECT * FROM read_json_auto(%s)" % q(px))
    con.execute("CREATE OR REPLACE TABLE canon.fact_sp500_sector_weights AS SELECT * FROM read_json_auto(%s)" % q(wt))
    con.execute("CREATE OR REPLACE TABLE canon.dim_gics_sectors AS SELECT DISTINCT gics_sector, spdr_sector_etf AS spdr_sector_etf FROM canon.fact_sp500_sector_weights")
    con.execute("COPY canon.spdr_prices TO %s (FORMAT PARQUET, COMPRESSION ZSTD)" % q(out / "spdr_prices.parquet"))
    con.execute("COPY canon.fact_sp500_sector_weights TO %s (FORMAT PARQUET, COMPRESSION ZSTD)" % q(out / "fact_sp500_sector_weights.parquet"))
    px.unlink()
    wt.unlink()
    con.close()


def selftest() -> int:
    day, last = "2024-03-28", "2024-06-28"
    prices = {}
    for row in SECTORS:
        prices[row["spdr_etf"]] = {day: 100.0, last: 100.0}
    prices["XLK"][day] = 50.0
    weights = {row["gics_sector"]: row["fallback_wt"] for row in SECTORS}
    built = reconstruct(prices, weights, [day, last], "FIXTURE")
    by_day = {}
    for row in built:
        by_day.setdefault(row["report_date"], {})[row["gics_sector"]] = row["sp500_weight_pct"]
    fails = []
    if abs(sum(by_day[day].values()) - 100.0) > 0.02 or abs(sum(by_day[last].values()) - 100.0) > 0.02:
        fails.append("sum")
    if not by_day[day]["Information Technology"] < by_day[last]["Information Technology"]:
        fails.append("tech drift")
    if quarter_ends(["2024-02-01", "2024-03-28", "2024-04-02", "2024-06-28"]) != [day, last]:
        fails.append("quarters")
    if fails:
        print("[FAIL] " + ", ".join(fails))
        return 1
    print("[OK] tech drift %.2f -> %.2f" % (by_day[day]["Information Technology"], by_day[last]["Information Technology"]))
    return 0


def fetch(out: Path, start: str) -> int:
    weights, source = anchor_weights()
    frames = {}
    price_rows = []
    for row in SECTORS:
        rows = chart_closes(row["spdr_etf"], start)
        if len(rows) < 20:
            print("[FAIL] %s bars=%d" % (row["spdr_etf"], len(rows)))
            return 1
        frames[row["spdr_etf"]] = rows
        price_rows.extend(rows)
        print("[OK] %s %d %s..%s" % (row["spdr_etf"], len(rows), rows[0]["date"], rows[-1]["date"]))
    prices, days = aligned_prices(frames)
    ends = quarter_ends(days)
    # also keep the latest session, even if it is not a quarter end
    if days[-1] not in ends:
        ends.append(days[-1])
    built = reconstruct(prices, weights, ends, source)
    store(out, price_rows, built)
    print("[PASS] source=%s dates=%d rows=%d -> %s" % (source, len(ends), len(built), out))
    return 0


def main(argv: list[str] | None = None) -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("cmd", choices=("selftest", "fetch"))
    parser.add_argument("--out", type=Path, default=Path("sp500_sector"))
    parser.add_argument("--start", default="2018-01-01")
    args = parser.parse_args(argv)
    if args.cmd == "selftest":
        return selftest()
    return fetch(args.out, args.start)


if __name__ == "__main__":
    raise SystemExit(main())
