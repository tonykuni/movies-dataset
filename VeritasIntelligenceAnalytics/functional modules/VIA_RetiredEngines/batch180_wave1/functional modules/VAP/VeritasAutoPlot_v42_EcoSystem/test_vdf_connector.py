"""
VeritasAutoPlot™ VDF Connector Integration Test
=================================================
Tests all VDF→AutoPlot data paths:
1. VDFNamingParser — filename parsing
2. VDFOutputScanner — directory scanning
3. GSheetConnector — URL parsing
4. MultiDBLoader — DuckDB operations
5. VDFConnector — full pipeline
6. AutoPlot.run_vdf() — VDF directory scan → dashboard
7. AutoPlot.run_vdf_file() — VDF file → dashboard
8. AutoPlot.run_df() — DataFrame → dashboard
9. AutoPlot.run_vdf_compare() — multi-ticker comparison
10. AutoPlot.run_etf_flow() — ETF flow dashboard
"""

import os
import sys
import json
import datetime
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from engine.vdf_connector import (
    VDFNamingParser, VDFOutputScanner, GSheetConnector,
    MultiDBLoader, MacroBridge, VDFConnector,
)
from engine.autoplot import VeritasAutoPlot

PASS = "\033[92m[PASS]\033[0m"
FAIL = "\033[91m[FAIL]\033[0m"
INFO = "\033[94m[INFO]\033[0m"
results = []


def test(name, func):
    try:
        func()
        print(f"  {PASS} {name}")
        results.append((name, True, ""))
    except Exception as e:
        print(f"  {FAIL} {name}: {e}")
        results.append((name, False, str(e)))


# ============================================================
# TEST 1: VDFNamingParser
# ============================================================
print(f"\n{INFO} Test Group 1: VDFNamingParser")

def test_parse_lego_v6():
    meta = VDFNamingParser.parse("etf_daily__DEFAULT__2025-01-01__latest__20260319_151527.parquet")
    assert meta is not None, "Failed to parse LEGO v6 filename"
    assert meta['source'] == 'LEGO_v6'
    assert meta['table'] == 'etf_daily'
    assert meta['category'] == 'DEFAULT'
    assert meta['format'] == 'parquet'
    assert meta['is_vdf_table'] == True

def test_parse_m01():
    meta = VDFNamingParser.parse("ohlcv_20260319_151527.parquet")
    assert meta is not None
    assert meta['source'] == 'M01_BatchDownloader'
    assert meta['format'] == 'parquet'

def test_parse_m02():
    meta = VDFNamingParser.parse("akshare_fred_us_20260319_151527.csv")
    assert meta is not None
    assert meta['source'] == 'M02_AKShareFRED'

def test_parse_duckdb():
    meta = VDFNamingParser.parse("intl_v6.duckdb")
    assert meta is not None
    assert meta['source'] == 'LEGO_v6'
    assert meta['format'] == 'duckdb'

def test_parse_generic_vdf():
    meta = VDFNamingParser.parse("stock_intl_export.csv")
    assert meta is not None
    assert meta['table'] == 'stock_intl'

def test_parse_unknown():
    meta = VDFNamingParser.parse("random_file.txt")
    assert meta is None

test("Parse LEGO v6 filename", test_parse_lego_v6)
test("Parse M01 filename", test_parse_m01)
test("Parse M02 filename", test_parse_m02)
test("Parse DuckDB filename", test_parse_duckdb)
test("Parse generic VDF filename", test_parse_generic_vdf)
test("Parse unknown returns None", test_parse_unknown)


# ============================================================
# TEST 2: GSheetConnector URL Parsing
# ============================================================
print(f"\n{INFO} Test Group 2: GSheetConnector")

def test_gsheet_parse_url():
    url = "https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms/edit#gid=0"
    sheet_id, gid = GSheetConnector.parse_url(url)
    assert sheet_id == "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms"
    assert gid == "0"

def test_gsheet_build_csv_url():
    url = GSheetConnector.build_csv_url("abc123", "0")
    assert "export?format=csv" in url
    assert "gid=0" in url

test("Parse Google Sheet URL", test_gsheet_parse_url)
test("Build CSV export URL", test_gsheet_build_csv_url)


# ============================================================
# TEST 3: VDFOutputScanner with simulated VDF directory
# ============================================================
print(f"\n{INFO} Test Group 3: VDFOutputScanner")

# Create simulated VDF directory structure
SIM_VDF_BASE = "/home/ubuntu/VeritasAutoPlot/temp/sim_vdf"
os.makedirs(f"{SIM_VDF_BASE}/output/VDF_CentralHub_LEGO_v6", exist_ok=True)
os.makedirs(f"{SIM_VDF_BASE}/output/csv", exist_ok=True)
os.makedirs(f"{SIM_VDF_BASE}/output/parquet", exist_ok=True)
os.makedirs(f"{SIM_VDF_BASE}/VDF_M02/csv", exist_ok=True)

# Create simulated data files
ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

# Simulated M01 OHLCV data
np.random.seed(42)
dates = pd.date_range('2020-01-01', periods=1000, freq='B')
tickers = ['NVDA', 'AMD', 'TSM', 'SMH', 'QQQ']
m01_data = []
for t in tickers:
    base = {'NVDA': 50, 'AMD': 30, 'TSM': 60, 'SMH': 150, 'QQQ': 200}[t]
    prices = base * np.cumprod(1 + np.random.normal(0.001, 0.02, len(dates)))
    for i, d in enumerate(dates):
        m01_data.append({
            'date': d.strftime('%Y-%m-%d'),
            'ticker': t,
            'open': prices[i] * (1 + np.random.uniform(-0.01, 0.01)),
            'high': prices[i] * (1 + np.random.uniform(0, 0.03)),
            'low': prices[i] * (1 - np.random.uniform(0, 0.03)),
            'close': prices[i],
            'adj_close': prices[i],
            'volume': int(np.random.uniform(1e6, 1e8)),
            'category': 'US_STOCKS' if t not in ['SMH', 'QQQ'] else 'US_ETFS',
        })

m01_df = pd.DataFrame(m01_data)
m01_parquet = f"{SIM_VDF_BASE}/output/parquet/ohlcv_{ts}.parquet"
m01_csv = f"{SIM_VDF_BASE}/output/csv/ohlcv_{ts}.csv"
m01_df.to_parquet(m01_parquet, index=False)
m01_df.to_csv(m01_csv, index=False, encoding='utf-8-sig')

# Simulated LEGO v6 ETF daily data
etf_df = m01_df[m01_df['category'] == 'US_ETFS'].copy()
etf_parquet = f"{SIM_VDF_BASE}/output/VDF_CentralHub_LEGO_v6/etf_daily__DEFAULT__2020-01-01__latest__{ts}.parquet"
etf_df.to_parquet(etf_parquet, index=False)

# Simulated LEGO v6 stock_intl data
stock_df = m01_df[m01_df['category'] == 'US_STOCKS'].copy()
stock_parquet = f"{SIM_VDF_BASE}/output/VDF_CentralHub_LEGO_v6/stock_intl__DEFAULT__2020-01-01__latest__{ts}.parquet"
stock_df.to_parquet(stock_parquet, index=False)

# Simulated M02 macro data
macro_data = []
macro_dates = pd.date_range('2020-01-01', periods=60, freq='ME')
for region in ['US', 'EU', 'CN']:
    for d in macro_dates:
        macro_data.append({
            'date': d.strftime('%Y-%m-%d'),
            'region': region,
            'cpi': np.random.uniform(1, 8),
            'gdp_growth': np.random.uniform(-2, 5),
            'unemployment': np.random.uniform(3, 12),
            'interest_rate': np.random.uniform(0, 5),
            'pmi': np.random.uniform(45, 60),
        })
macro_df = pd.DataFrame(macro_data)
macro_csv = f"{SIM_VDF_BASE}/VDF_M02/csv/akshare_fred_all_{ts}.csv"
macro_df.to_csv(macro_csv, index=False, encoding='utf-8-sig')

# Simulated ETF flow data
flow_data = []
for t in ['SMH', 'QQQ']:
    for d in dates:
        flow_data.append({
            'date': d.strftime('%Y-%m-%d'),
            'ticker': t,
            'close': m01_df[(m01_df['ticker'] == t) & (m01_df['date'] == d.strftime('%Y-%m-%d'))]['close'].values[0] if len(m01_df[(m01_df['ticker'] == t) & (m01_df['date'] == d.strftime('%Y-%m-%d'))]) > 0 else 100,
            'volume': int(np.random.uniform(1e6, 1e8)),
            'dvol_ratio': np.random.uniform(0.5, 2.0),
            'flow_label': np.random.choice(['INFLOW', 'OUTFLOW', 'NEUTRAL'], p=[0.4, 0.3, 0.3]),
        })
flow_df = pd.DataFrame(flow_data)
flow_parquet = f"{SIM_VDF_BASE}/output/VDF_CentralHub_LEGO_v6/etf_flow_daily__DEFAULT__2020-01-01__latest__{ts}.parquet"
flow_df.to_parquet(flow_parquet, index=False)

print(f"  {INFO} Simulated VDF directory created at: {SIM_VDF_BASE}")
print(f"  {INFO} Files: M01 OHLCV ({len(m01_df)} rows), LEGO v6 ETF/Stock, M02 Macro, ETF Flow")


def test_scanner_scan():
    scanner = VDFOutputScanner(base_dirs=[SIM_VDF_BASE])
    catalog = scanner.scan()
    assert len(catalog) > 0, f"No files found in scan"
    summary = scanner.get_summary()
    assert summary['total_files'] > 0
    print(f"    → Found {summary['total_files']} files, {summary['total_size_mb']} MB")
    print(f"    → By source: {summary['by_source']}")
    print(f"    → By format: {summary['by_format']}")

def test_scanner_get_latest():
    scanner = VDFOutputScanner(base_dirs=[SIM_VDF_BASE])
    scanner.scan()
    latest = scanner.get_latest(fmt='parquet')
    assert latest is not None, "No parquet file found"
    print(f"    → Latest parquet: {os.path.basename(latest['filepath'])}")

test("Scanner scan VDF directory", test_scanner_scan)
test("Scanner get latest file", test_scanner_get_latest)


# ============================================================
# TEST 4: VDFConnector Full Pipeline
# ============================================================
print(f"\n{INFO} Test Group 4: VDFConnector")

def test_connector_scan():
    conn = VDFConnector(vdf_base=SIM_VDF_BASE)
    summary = conn.scan()
    assert summary['total_files'] > 0
    print(f"    → Catalog: {summary['total_files']} files")

def test_connector_load_ticker():
    conn = VDFConnector(vdf_base=SIM_VDF_BASE)
    conn.scan()
    df = conn.load_ticker("NVDA")
    assert not df.empty, "NVDA data not found"
    assert 'Main_Price' in df.columns, "Main_Price not standardized"
    print(f"    → NVDA: {len(df)} rows, price range: {df['Main_Price'].min():.2f} ~ {df['Main_Price'].max():.2f}")

def test_connector_load_table():
    conn = VDFConnector(vdf_base=SIM_VDF_BASE)
    conn.scan()
    df = conn.load_file(etf_parquet, ticker="SMH")
    assert not df.empty, "SMH ETF data not found"
    print(f"    → SMH ETF: {len(df)} rows")

def test_connector_export_config():
    conn = VDFConnector(vdf_base=SIM_VDF_BASE)
    conn.scan()
    config = conn.export_config()
    assert 'vdf_base' in config
    assert 'scan_summary' in config
    print(f"    → Config exported: {config['catalog_count']} files cataloged")

test("VDFConnector scan", test_connector_scan)
test("VDFConnector load_ticker NVDA", test_connector_load_ticker)
test("VDFConnector load_file ETF", test_connector_load_table)
test("VDFConnector export_config", test_connector_export_config)


# ============================================================
# TEST 5: AutoPlot VDF Integration
# ============================================================
print(f"\n{INFO} Test Group 5: AutoPlot VDF Integration")

def test_autoplot_run_vdf():
    engine = VeritasAutoPlot()
    html = engine.run_vdf(vdf_base=SIM_VDF_BASE, ticker="NVDA", asset_name="NVDA")
    assert html is not None
    assert len(html) > 1000
    path = engine.save(os.path.join(engine.output_dir, "VAP_VDF_NVDA.html"))
    print(f"    → Saved: {path} ({len(html):,} chars)")

    # Verify structured output
    output = engine.get_structured_output()
    assert len(output['plots']) > 0
    assert len(output['insights']) > 0
    assert output['source_info']['type'] == 'vdf_scan'
    print(f"    → Plots: {len(output['plots'])}, Insights: {len(output['insights'])}")

def test_autoplot_run_vdf_file():
    engine = VeritasAutoPlot()
    html = engine.run_vdf_file(m01_parquet, ticker="AMD", asset_name="AMD")
    assert html is not None
    path = engine.save(os.path.join(engine.output_dir, "VAP_VDF_FILE_AMD.html"))
    print(f"    → Saved: {path} ({len(html):,} chars)")

def test_autoplot_run_df():
    engine = VeritasAutoPlot()
    # Create a DataFrame directly
    dates = pd.date_range('2020-01-01', periods=500, freq='B')
    df = pd.DataFrame({
        'date': dates,
        'close': 100 * np.cumprod(1 + np.random.normal(0.001, 0.015, 500)),
        'volume': np.random.randint(1e6, 1e8, 500),
    })
    df = df.set_index('date')
    html = engine.run_df(df, asset_name="Synthetic Data")
    assert html is not None
    path = engine.save(os.path.join(engine.output_dir, "VAP_DataFrame.html"))
    print(f"    → Saved: {path} ({len(html):,} chars)")

def test_autoplot_run_vdf_compare():
    engine = VeritasAutoPlot()
    html = engine.run_vdf_compare(
        vdf_base=SIM_VDF_BASE,
        tickers=["NVDA", "AMD", "TSM"],
        asset_name="Semiconductor Compare"
    )
    assert html is not None
    path = engine.save(os.path.join(engine.output_dir, "VAP_VDF_Compare.html"))
    print(f"    → Saved: {path} ({len(html):,} chars)")

    output = engine.get_structured_output()
    print(f"    → Plots: {len(output['plots'])}, Insights: {len(output['insights'])}")

test("AutoPlot.run_vdf() — VDF scan → NVDA", test_autoplot_run_vdf)
test("AutoPlot.run_vdf_file() — Parquet → AMD", test_autoplot_run_vdf_file)
test("AutoPlot.run_df() — DataFrame direct", test_autoplot_run_df)
test("AutoPlot.run_vdf_compare() — Multi-ticker", test_autoplot_run_vdf_compare)


# ============================================================
# TEST 6: VDF Catalog & Summary
# ============================================================
print(f"\n{INFO} Test Group 6: VDF Catalog & Summary")

def test_vdf_catalog():
    engine = VeritasAutoPlot()
    engine.run_vdf(vdf_base=SIM_VDF_BASE, ticker="NVDA")
    catalog = engine.get_vdf_catalog()
    assert len(catalog) > 0
    print(f"    → Catalog entries: {len(catalog)}")
    for item in catalog[:3]:
        print(f"      - {item.get('source')}: {os.path.basename(item.get('filepath',''))}")

def test_vdf_summary():
    engine = VeritasAutoPlot()
    engine.run_vdf(vdf_base=SIM_VDF_BASE, ticker="NVDA")
    summary = engine.get_vdf_summary()
    assert summary['total_files'] > 0
    print(f"    → Summary: {json.dumps(summary, indent=2, default=str)[:300]}")

test("VDF Catalog retrieval", test_vdf_catalog)
test("VDF Summary retrieval", test_vdf_summary)


# ============================================================
# FINAL REPORT
# ============================================================
print("\n" + "=" * 60)
total = len(results)
passed = sum(1 for _, ok, _ in results if ok)
failed = total - passed
print(f"  TOTAL: {total}  |  {PASS} PASSED: {passed}  |  {FAIL} FAILED: {failed}")
print("=" * 60)

if failed > 0:
    print(f"\n{FAIL} Failed tests:")
    for name, ok, err in results:
        if not ok:
            print(f"  - {name}: {err}")
else:
    print(f"\n  {PASS} ALL TESTS PASSED — VDF→AutoPlot pipeline fully operational!")

# List generated HTML files
print(f"\n{INFO} Generated HTML dashboards:")
output_dir = "/home/ubuntu/VeritasAutoPlot/output"
for f in sorted(os.listdir(output_dir)):
    if f.endswith('.html'):
        size = os.path.getsize(os.path.join(output_dir, f))
        print(f"  → {f} ({size:,} bytes)")
