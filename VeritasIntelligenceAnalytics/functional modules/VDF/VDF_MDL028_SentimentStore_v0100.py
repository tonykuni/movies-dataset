#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CNN Fear & Greed and AAII from 2022-01-01, through the versioned tools VCGC's bridge points at.

The unversioned shim does not count. The body must be *_vNNNN*.
Does not set VIA_NET_CONSENT. Does not write the FRED key.

  py -3 VDF_MDL028_SentimentStore_v0100.py fetch
  py -3 VDF_MDL028_SentimentStore_v0100.py selftest
"""
from __future__ import annotations

import html
import importlib.util
import io
import json
import os
import re
import sys
import time
from datetime import date, datetime, timezone
from pathlib import Path

START = date(2022, 1, 1)
CNN_URL = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata/2022-01-01"
AAII_URL = "https://www.aaii.com/files/surveys/sentiment.xls"
VER = re.compile(r"_v\d{4}")
SUBS = (
    "market_momentum_sp500",
    "stock_price_strength",
    "stock_price_breadth",
    "put_call_options",
    "junk_bond_demand",
    "market_volatility_vix",
    "safe_haven_demand",
)

# Same accelerator bridge VCGC v0199 uses. The version that counts is CANONICAL.
try:
    _sa = Path(__file__).resolve()
    while _sa.parent != _sa:
        if (_sa / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            sys.path.insert(0, str(_sa / "supportive modules"))
            break
        _sa = _sa.parent
    import VIA_SuperAccel_Module as VIA_ACCEL
except Exception:
    VIA_ACCEL = None


def _net_path() -> Path | None:
    here = Path(__file__).resolve()
    while here.parent != here:
        folder = here / "supportive modules" / "network"
        if folder.is_dir():
            hits = sorted(folder.glob("via_net_unified_v*.py"))
            return hits[-1] if hits else None
        here = here.parent
    return None


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def tools() -> dict:
    if VIA_ACCEL is None or not callable(getattr(VIA_ACCEL, "accel_map", None)):
        raise RuntimeError("versioned accelerator absent")
    accel_ver = str(getattr(VIA_ACCEL, "CANONICAL", ""))
    if not VER.search(accel_ver):
        raise RuntimeError("accelerator has no version: %s" % accel_ver)
    path = _net_path()
    if path is None:
        raise RuntimeError("versioned net tool absent")
    net = _load(path, "vdf_via_net_unified")
    net_ver = str(getattr(net, "CANONICAL", path.name))
    if not VER.search(net_ver) or not callable(getattr(net, "http_bytes", None)):
        raise RuntimeError("net body has no version: %s" % net_ver)
    return {"net": net, "accel": VIA_ACCEL, "net_ver": net_ver, "accel_ver": accel_ver, "bridge": path.name}


def _day(ms: float) -> date:
    return datetime.fromtimestamp(ms / 1000, timezone.utc).date()


def parse_cnn(raw: bytes) -> tuple[list, list]:
    js = json.loads(raw)
    main = []
    for row in (js.get("fear_and_greed_historical") or {}).get("data") or []:
        if row.get("x") is None:
            continue
        day = _day(float(row["x"]))
        if day < START:
            continue
        main.append((day.isoformat(), float(row.get("y") or 0), str(row.get("rating") or "")))
    subs = []
    for key in SUBS:
        for row in (js.get(key) or {}).get("data") or []:
            if row.get("x") is None:
                continue
            day = _day(float(row["x"]))
            if day < START:
                continue
            subs.append((day.isoformat(), key, float(row.get("y") or 0), str(row.get("rating") or "")))
    return main, subs


def parse_aaii(raw: bytes) -> list:
    import pandas as pd
    frame = pd.read_excel(io.BytesIO(raw), header=None)
    rows = []
    for i in range(len(frame)):
        stamp = frame.iat[i, 0]
        if not hasattr(stamp, "year"):
            continue
        bull, neut, bear = frame.iat[i, 1], frame.iat[i, 2], frame.iat[i, 3]
        if pd.isna(bull) or pd.isna(bear):
            continue
        day = stamp.date()
        if day < START:
            continue
        rows.append((day.isoformat(), float(bull), float(neut), float(bear)))
    return rows


def _copy(con, table: str, path: Path) -> None:
    con.execute("COPY %s TO '%s' (FORMAT PARQUET)" % (table, path.as_posix()))


def store(main, subs, aaii, out: Path) -> dict:
    import duckdb
    out.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    con.execute("CREATE TABLE cnn (date DATE, score DOUBLE, rating VARCHAR)")
    con.execute("CREATE TABLE cnn_sub (date DATE, indicator VARCHAR, value DOUBLE, rating VARCHAR)")
    con.execute("CREATE TABLE aaii (date DATE, bullish DOUBLE, neutral DOUBLE, bearish DOUBLE)")
    if main:
        con.executemany("INSERT INTO cnn VALUES (?,?,?)", main)
    if subs:
        con.executemany("INSERT INTO cnn_sub VALUES (?,?,?,?)", subs)
    if aaii:
        con.executemany("INSERT INTO aaii VALUES (?,?,?,?)", aaii)
    con.execute("""
        CREATE TABLE sentiment_daily AS
        SELECT date, 'CNN_FEAR_GREED' AS series, score AS value, rating, 'CNN' AS source FROM cnn
        UNION ALL
        SELECT date, indicator, value, rating, 'CNN' FROM cnn_sub
        UNION ALL
        SELECT date, 'AAII_BULLISH', bullish, '', 'AAII' FROM aaii
        UNION ALL
        SELECT date, 'AAII_NEUTRAL', neutral, '', 'AAII' FROM aaii
        UNION ALL
        SELECT date, 'AAII_BEARISH', bearish, '', 'AAII' FROM aaii
    """)
    files = {
        "cnn": out / "cnn_fear_greed.parquet",
        "sub": out / "cnn_subindicators.parquet",
        "aaii": out / "aaii_sentiment.parquet",
        "official": out / "gl__sentiment_daily.parquet",
    }
    _copy(con, "cnn", files["cnn"])
    _copy(con, "cnn_sub", files["sub"])
    _copy(con, "aaii", files["aaii"])
    _copy(con, "sentiment_daily", files["official"])
    con.close()
    return files


def _q(con, sql: str):
    cur = con.execute(sql)
    return [d[0] for d in cur.description], cur.fetchall()


def _table(headers, rows) -> str:
    head = "".join("<th>%s</th>" % html.escape(str(h)) for h in headers)
    body = []
    for row in rows:
        body.append("<tr>" + "".join("<td>%s</td>" % html.escape("" if v is None else str(v)) for v in row) + "</tr>")
    return "<table><thead><tr>%s</tr></thead><tbody>%s</tbody></table>" % (head, "".join(body))


def render(files: dict, meta: dict, out: Path) -> Path:
    import duckdb
    con = duckdb.connect()
    cnn, sub, aaii = (p.as_posix() for p in (files["cnn"], files["sub"], files["aaii"]))
    summary_h, summary = _q(con, """
        SELECT 'CNN' AS src, count(*) AS n, min(date), max(date), round(last(score ORDER BY date), 2)
        FROM read_parquet('%s')
        UNION ALL
        SELECT 'AAII', count(*), min(date), max(date), round(100 * last(bearish ORDER BY date), 2)
        FROM read_parquet('%s')
    """ % (cnn, aaii))
    latest_h, latest = _q(con, """
        SELECT indicator, round(value, 1), rating, date
        FROM (
            SELECT *, row_number() OVER (PARTITION BY indicator ORDER BY date DESC) AS rn
            FROM read_parquet('%s')
        ) WHERE rn = 1 ORDER BY indicator
    """ % sub)
    recent_h, recent = _q(con, """
        SELECT date, round(100 * bullish, 2), round(100 * neutral, 2), round(100 * bearish, 2),
               round(100 * (bullish - bearish), 2)
        FROM read_parquet('%s') ORDER BY date DESC LIMIT 8
    """ % aaii)
    page = out / "sentiment.html"
    page.write_text("""<!DOCTYPE html>
<html lang="zh-Hant"><head><meta charset="utf-8"><title>VDF 情緒 2022 至今</title>
<style>
body{margin:0;background:#1c242c;color:#d5ddd8;font:15px/1.45 "Segoe UI",sans-serif}
main{max-width:62rem;margin:2rem auto;padding:0 1rem}
h1{font-size:1.2rem;font-weight:600} p,li{color:#aeb8b4}
table{border-collapse:collapse;width:100%%;margin:1rem 0;background:#243038}
th,td{border:1px solid #3d4f5f;padding:.35rem .5rem;text-align:left}
th{background:#3d4f5f;font-weight:600}
</style></head><body><main>
<h1>CNN Fear & Greed / AAII · 2022-01-01 至今</h1>
<ul>
<li>網路本體 %s</li>
<li>加速本體 %s</li>
<li>橋 %s · 抓取 %s 毫秒 · 經由 %s</li>
</ul>
<h2>DuckDB 讀 Parquet</h2>
%s
<p>AAII 最後一欄是看空百分比。CNN 最後一欄是指數。</p>
<h2>CNN 子項最新</h2>
%s
<h2>AAII 近八週（百分比）</h2>
%s
</main></body></html>""" % (
        html.escape(meta["net_ver"]), html.escape(meta["accel_ver"]), html.escape(meta["bridge"]),
        meta["ms"], html.escape(meta["via"]),
        _table(summary_h, summary), _table(latest_h, latest), _table(recent_h, recent),
    ), encoding="utf-8")
    return page


def fetch(out: Path | None = None) -> int:
    begun = time.perf_counter()
    got = tools()
    net = got["net"]
    state = net.gate_state() if callable(getattr(net, "gate_state", None)) else {}
    if not state.get("open"):
        print("DENY net gate closed. Set VIA_NET_CONSENT=YES and VIA_SCRAPE_CONSENT. This file does not set them.")
        return 2
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://edition.cnn.com/markets/fear-and-greed",
        "Accept": "*/*",
    }
    jobs = [(CNN_URL, headers), (AAII_URL, {"User-Agent": headers["User-Agent"], "Accept": "*/*"})]

    def pull(item):
        url, hdr = item
        return got["net"].http_bytes(url, timeout=60, headers=hdr)

    pulled = got["accel"].accel_map(pull, jobs)
    if not all(ok and isinstance(res, dict) and res.get("state") == "OK" for ok, res in pulled):
        print("FAIL fetch", [(ok, (res.get("state"), res.get("note")) if isinstance(res, dict) else res) for ok, res in pulled])
        return 1
    cnn_raw, aaii_raw = pulled[0][1]["data"], pulled[1][1]["data"]
    via = pulled[0][1].get("via", "")
    main, subs = parse_cnn(cnn_raw)
    aaii = parse_aaii(aaii_raw)
    if not main or not aaii:
        print("FAIL empty cnn=%d aaii=%d" % (len(main), len(aaii)))
        return 1
    dest = out or (Path(__file__).resolve().parent / "output_hub" / "mega" / "sentiment_2022")
    files = store(main, subs, aaii, dest)
    ms = int((time.perf_counter() - begun) * 1000)
    page = render(files, {"net_ver": got["net_ver"], "accel_ver": got["accel_ver"], "bridge": got["bridge"], "ms": ms, "via": str(via)}, dest)
    print("net=%s" % got["net_ver"])
    print("accel=%s" % got["accel_ver"])
    print("bridge=%s via=%s" % (got["bridge"], via))
    print("cnn=%d sub=%d aaii=%d from=%s" % (len(main), len(subs), len(aaii), START.isoformat()))
    print("ms=%d" % ms)
    print("html=%s" % page)
    return 0


def selftest() -> int:
    got = tools()
    main, subs = parse_cnn(json.dumps({
        "fear_and_greed_historical": {"data": [
            {"x": 1609459200000, "y": 1, "rating": "old"},
            {"x": 1641168000000, "y": 40, "rating": "fear"},
        ]},
        "market_momentum_sp500": {"data": [{"x": 1641168000000, "y": 10, "rating": "fear"}]},
    }).encode())
    if len(main) != 1 or main[0][0] < "2022-01-01":
        print("[FAIL] date filter", main)
        return 1
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        files = store(main, subs, [("2022-01-06", 0.3, 0.2, 0.5)], Path(td))
        import duckdb
        cols = [r[0] for r in duckdb.connect().execute("DESCRIBE SELECT * FROM read_parquet(?)", [str(files["official"])]).fetchall()]
        n, k = duckdb.connect().execute(
            "SELECT count(*), count(DISTINCT (date, series)) FROM read_parquet(?)", [str(files["official"])]).fetchone()
        if cols != ["date", "series", "value", "rating", "source"] or n != k or n != 1 + len(subs) + 3:
            print("[FAIL] official frame", cols, n, k)
            return 1
        page = render(files, {"net_ver": got["net_ver"], "accel_ver": got["accel_ver"], "bridge": got["bridge"], "ms": 1, "via": "test"}, Path(td))
        text = page.read_text(encoding="utf-8")
        if got["net_ver"] not in text or "2022-01-03" not in text and "2022-01-06" not in text:
            print("[FAIL] html", text[:200])
            return 1
    if not VER.search(got["net_ver"]) or not VER.search(got["accel_ver"]):
        print("[FAIL] version")
        return 1
    print("[OK] %s + %s" % (got["net_ver"], got["accel_ver"]))
    return 0


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    cmd = argv[0] if argv else "fetch"
    if cmd == "selftest":
        return selftest()
    if cmd != "fetch":
        print("verbs: fetch selftest")
        return 2
    return fetch()


if __name__ == "__main__":
    raise SystemExit(main())
