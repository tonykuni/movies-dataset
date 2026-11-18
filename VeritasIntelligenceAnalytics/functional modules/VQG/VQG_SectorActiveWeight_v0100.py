#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VQG analysis: fund sector overweight versus the VDF S&P 500 weight table.

Reads VDF output only. No network. A missing 13F table is a skip, not a fake score.
Zero holdings stay in the grid, so an empty sector is an underweight of the whole benchmark weight.

  py -3 VQG_SectorActiveWeight_v0100.py selftest
  py -3 VQG_SectorActiveWeight_v0100.py run --vdf DIR --holdings DB
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

VIEW_ACTIVE = """
CREATE OR REPLACE VIEW v_13f_fund_sector_active_weights AS
WITH fund_quarters AS (
    SELECT DISTINCT
        h.cik,
        i.institution_name,
        COALESCE(i.strategy_group, 'HIGH_CONVICTION') AS strategy_group,
        h.report_date,
        h.q_rank
    FROM v_13f_holdings_with_sector h
    LEFT JOIN dim_institutions i ON h.cik = i.cik
),
full_sector_grid AS (
    SELECT fq.cik, fq.institution_name, fq.strategy_group, fq.report_date, fq.q_rank,
           g.gics_sector, g.spdr_sector_etf
    FROM fund_quarters fq
    CROSS JOIN dim_gics_sectors g
),
fund_sector_agg AS (
    SELECT cik, report_date, gics_sector,
           COUNT(DISTINCT CASE WHEN curr_shares > 0 THEN ticker END) AS held_stocks_count,
           COUNT(CASE WHEN action_type IN ('NEW_BUY', 'ADD') THEN 1 END) AS bullish_actions,
           COUNT(CASE WHEN action_type IN ('REDUCE', 'SOLD_OUT') THEN 1 END) AS bearish_actions,
           SUM(curr_value_usd) AS sector_value_usd,
           SUM(curr_weight_pct) AS raw_sector_weight_pct,
           arg_max(ticker, curr_value_usd) AS top_holding_ticker,
           MAX(curr_weight_pct) AS top_holding_weight_pct
    FROM v_13f_holdings_with_sector
    WHERE put_call = 'SHARE' AND asset_class = 'EQUITY'
      AND gics_sector IN (SELECT gics_sector FROM dim_gics_sectors)
    GROUP BY cik, report_date, gics_sector
),
fund_quarter_totals AS (
    SELECT cik, report_date, SUM(sector_value_usd) AS total_classified_equity_usd
    FROM fund_sector_agg GROUP BY cik, report_date
),
merged_active AS (
    SELECT g.cik, g.institution_name, g.strategy_group, g.report_date, g.q_rank, g.gics_sector, g.spdr_sector_etf,
           COALESCE(a.held_stocks_count, 0) AS held_stocks_count,
           COALESCE(a.bullish_actions, 0) AS bullish_actions,
           COALESCE(a.bearish_actions, 0) AS bearish_actions,
           ROUND(COALESCE(a.sector_value_usd, 0.0) / 1e6, 2) AS sector_value_musd,
           ROUND(COALESCE(a.raw_sector_weight_pct, 0.0), 2) AS fund_raw_weight_pct,
           ROUND(CASE WHEN COALESCE(t.total_classified_equity_usd, 0) > 0
                      THEN COALESCE(a.sector_value_usd, 0.0) * 100.0 / t.total_classified_equity_usd
                      ELSE 0.0 END, 2) AS fund_norm_weight_pct,
           ROUND(bm.sp500_weight_pct, 2) AS sp500_weight_pct,
           a.top_holding_ticker,
           ROUND(COALESCE(a.top_holding_weight_pct, 0.0), 2) AS top_holding_weight_pct
    FROM full_sector_grid g
    LEFT JOIN fund_sector_agg a
      ON g.cik = a.cik AND g.report_date = a.report_date AND g.gics_sector = a.gics_sector
    LEFT JOIN fund_quarter_totals t
      ON g.cik = t.cik AND g.report_date = t.report_date
    LEFT JOIN LATERAL (
        SELECT bm.sp500_weight_pct
        FROM fact_sp500_sector_weights bm
        WHERE bm.gics_sector = g.gics_sector
          AND bm.report_date <= g.report_date
        ORDER BY bm.report_date DESC
        LIMIT 1
    ) bm ON TRUE
)
SELECT m.*,
       ROUND(m.fund_norm_weight_pct - m.sp500_weight_pct, 2) AS active_weight_pct,
       ROUND(m.fund_norm_weight_pct / NULLIF(m.sp500_weight_pct, 0), 2) AS relative_weight_ratio,
       LAG(ROUND(m.fund_norm_weight_pct - m.sp500_weight_pct, 2)) OVER (
           PARTITION BY m.cik, m.gics_sector ORDER BY m.report_date
       ) AS prev_active_weight_pct,
       ROUND(
           (m.fund_norm_weight_pct - m.sp500_weight_pct)
           - LAG(m.fund_norm_weight_pct - m.sp500_weight_pct) OVER (
               PARTITION BY m.cik, m.gics_sector ORDER BY m.report_date
           ), 2
       ) AS active_weight_qoq_delta_pct,
       CASE
           WHEN m.held_stocks_count = 0 THEN 'ZERO_EXPOSURE_UW'
           WHEN (m.fund_norm_weight_pct - m.sp500_weight_pct) >= 5.0 THEN 'STRONG_OVERWEIGHT'
           WHEN (m.fund_norm_weight_pct - m.sp500_weight_pct) >= 1.5 THEN 'OVERWEIGHT'
           WHEN (m.fund_norm_weight_pct - m.sp500_weight_pct) <= -5.0 THEN 'STRONG_UNDERWEIGHT'
           WHEN (m.fund_norm_weight_pct - m.sp500_weight_pct) <= -1.5 THEN 'UNDERWEIGHT'
           ELSE 'NEUTRAL_WEIGHT'
       END AS tilt_status
FROM merged_active m
"""

VIEW_SHARE = """
CREATE OR REPLACE VIEW v_13f_fund_sector_active_share AS
SELECT cik, institution_name, strategy_group, report_date,
       ROUND(0.5 * SUM(ABS(active_weight_pct)), 2) AS sector_active_share_pct,
       COUNT(CASE WHEN held_stocks_count > 0 THEN 1 END) AS active_sectors_count,
       arg_max(gics_sector, active_weight_pct) AS max_overweight_sector,
       MAX(active_weight_pct) AS max_overweight_pct,
       arg_min(gics_sector, active_weight_pct) AS max_underweight_sector,
       MIN(active_weight_pct) AS max_underweight_pct
FROM v_13f_fund_sector_active_weights
GROUP BY cik, institution_name, strategy_group, report_date
"""

QUERY_CONSENSUS = """
SELECT report_date, gics_sector, spdr_sector_etf,
       MAX(sp500_weight_pct) AS sp500_bm_weight_pct,
       ROUND(AVG(fund_norm_weight_pct), 2) AS avg_fund_weight_pct,
       ROUND(AVG(active_weight_pct), 2) AS avg_active_weight_pct,
       ROUND(AVG(active_weight_qoq_delta_pct), 2) AS avg_active_qoq_shift_pct,
       COUNT(CASE WHEN active_weight_pct >= 1.5 THEN 1 END) AS overweight_funds,
       COUNT(CASE WHEN active_weight_pct <= -1.5 THEN 1 END) AS underweight_funds,
       COUNT(CASE WHEN held_stocks_count = 0 THEN 1 END) AS zero_exposure_funds
FROM v_13f_fund_sector_active_weights
WHERE strategy_group = 'HIGH_CONVICTION'
GROUP BY report_date, gics_sector, spdr_sector_etf
ORDER BY report_date, avg_active_weight_pct DESC
"""

QUERY_FUND = """
SELECT institution_name, report_date, gics_sector, held_stocks_count,
       fund_norm_weight_pct, sp500_weight_pct, active_weight_pct, tilt_status, top_holding_ticker
FROM v_13f_fund_sector_active_weights
WHERE cik = ?
ORDER BY report_date, active_weight_pct DESC
"""

QUERY_ACTIVE_SHARE = """
SELECT institution_name, strategy_group, report_date, sector_active_share_pct,
       active_sectors_count, max_overweight_sector, max_overweight_pct,
       max_underweight_sector, max_underweight_pct
FROM v_13f_fund_sector_active_share
ORDER BY sector_active_share_pct DESC
"""


def attach_views(con) -> None:
    con.execute(VIEW_ACTIVE)
    con.execute(VIEW_SHARE)


def selftest() -> int:
    import duckdb
    con = duckdb.connect()
    con.execute("CREATE TABLE dim_gics_sectors (gics_sector VARCHAR, spdr_sector_etf VARCHAR)")
    con.execute("INSERT INTO dim_gics_sectors VALUES ('Information Technology','XLK'), ('Utilities','XLU')")
    con.execute("""
        CREATE TABLE fact_sp500_sector_weights (
            report_date DATE, gics_sector VARCHAR, spdr_sector_etf VARCHAR,
            etf_close_price DOUBLE, sp500_weight_pct DOUBLE, weight_source VARCHAR, updated_at VARCHAR
        )
    """)
    con.execute("""
        INSERT INTO fact_sp500_sector_weights VALUES
        ('2024-06-28','Information Technology','XLK',100,60,'FIXTURE',''),
        ('2024-06-28','Utilities','XLU',100,40,'FIXTURE','')
    """)
    con.execute("CREATE TABLE dim_institutions (cik VARCHAR, institution_name VARCHAR, strategy_group VARCHAR)")
    con.execute("INSERT INTO dim_institutions VALUES ('0001','Fixture Fund','HIGH_CONVICTION')")
    con.execute("""
        CREATE TABLE holdings (
            cik VARCHAR, report_date DATE, q_rank INTEGER, put_call VARCHAR, asset_class VARCHAR,
            gics_sector VARCHAR, ticker VARCHAR, curr_shares DOUBLE, action_type VARCHAR,
            curr_value_usd DOUBLE, curr_weight_pct DOUBLE
        )
    """)
    con.execute("""
        INSERT INTO holdings VALUES
        ('0001','2024-06-30',1,'SHARE','EQUITY','Information Technology','AAPL',10,'NEW_BUY',100,100)
    """)
    con.execute("CREATE VIEW v_13f_holdings_with_sector AS SELECT * FROM holdings")
    attach_views(con)
    row = con.execute("""
        SELECT fund_norm_weight_pct, sp500_weight_pct, active_weight_pct, tilt_status
        FROM v_13f_fund_sector_active_weights
        WHERE gics_sector = 'Utilities'
    """).fetchone()
    share = con.execute("SELECT sector_active_share_pct, active_sectors_count FROM v_13f_fund_sector_active_share").fetchone()
    fails = []
    if row != (0.0, 40.0, -40.0, "ZERO_EXPOSURE_UW"):
        fails.append("utilities %s" % (row,))
    # 0.5 * (|100-60| + |0-40|) = 40
    if share != (40.0, 1):
        fails.append("share %s" % (share,))
    if fails:
        print("[FAIL] " + ", ".join(fails))
        return 1
    print("[OK] zero-utilities active=-40 share=40")
    return 0


def run(vdf: Path, holdings: Path | None, out: Path) -> int:
    import duckdb
    weight_db = vdf / "sp500_sector.duckdb"
    if not weight_db.is_file():
        print("[FAIL] missing %s" % weight_db)
        return 1
    con = duckdb.connect()
    q = lambda path: "'" + path.as_posix().replace("'", "''") + "'"
    con.execute("ATTACH %s AS vdf (READ_ONLY)" % q(weight_db))
    con.execute("CREATE VIEW dim_gics_sectors AS SELECT * FROM vdf.canon.dim_gics_sectors")
    con.execute("CREATE VIEW fact_sp500_sector_weights AS SELECT * FROM vdf.canon.fact_sp500_sector_weights")
    if holdings is None or not holdings.is_file():
        n = con.execute("SELECT COUNT(*), COUNT(DISTINCT report_date) FROM fact_sp500_sector_weights").fetchone()
        print("[SKIP] no 13F holdings. benchmark rows=%s dates=%s" % (n[0], n[1]))
        return 0
    con.execute("ATTACH %s AS hf (READ_ONLY)" % q(holdings))
    con.execute("CREATE VIEW v_13f_holdings_with_sector AS SELECT * FROM hf.v_13f_holdings_with_sector")
    con.execute("CREATE VIEW dim_institutions AS SELECT * FROM hf.dim_institutions")
    attach_views(con)
    out.mkdir(parents=True, exist_ok=True)
    con.execute("COPY (SELECT * FROM v_13f_fund_sector_active_weights) TO %s (FORMAT PARQUET, COMPRESSION ZSTD)" % q(out / "active_weights.parquet"))
    con.execute("COPY (SELECT * FROM v_13f_fund_sector_active_share) TO %s (FORMAT PARQUET, COMPRESSION ZSTD)" % q(out / "active_share.parquet"))
    summary = con.execute(QUERY_ACTIVE_SHARE).fetchall()
    (out / "active_share.json").write_text(json.dumps(summary, default=str), encoding="utf-8")
    print("[PASS] funds=%d -> %s" % (len(summary), out))
    return 0


def main(argv: list[str] | None = None) -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("cmd", choices=("selftest", "run"))
    parser.add_argument("--vdf", type=Path, default=Path("sp500_sector"))
    parser.add_argument("--holdings", type=Path, default=None)
    parser.add_argument("--out", type=Path, default=Path("vqg_sector"))
    args = parser.parse_args(argv)
    if args.cmd == "selftest":
        return selftest()
    return run(args.vdf, args.holdings, args.out)


if __name__ == "__main__":
    raise SystemExit(main())
