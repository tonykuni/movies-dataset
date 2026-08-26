"""
VeritasAutoPlot™ Full Integration Test
========================================
Tests:
1. Standard pipeline (CSV → HTML)
2. VDF Schema compatible data
3. ETF Flow visualization
4. VDF PANORAMIC_DATA visualization
5. Multi-ticker comparison
6. VRN Anchor AST registry export
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json


def generate_vdf_compatible_data():
    """Generate sample data matching VDF Schema v6 format."""
    np.random.seed(42)
    days = 1200
    dates = pd.bdate_range(end=datetime(2026, 3, 19), periods=days)

    tickers = {
        "^GSPC": ("S&P 500", 4500, 0.0004, 0.012),
        "^IXIC": ("NASDAQ", 14000, 0.0005, 0.016),
        "TSM":   ("TSMC", 150, 0.0006, 0.018),
        "NVDA":  ("NVIDIA", 500, 0.001, 0.025),
        "SMH":   ("VanEck Semi ETF", 250, 0.0007, 0.020),
        "QQQ":   ("Invesco QQQ", 380, 0.0005, 0.015),
    }

    all_data = {}
    for ticker, (name, start_price, mu, sigma) in tickers.items():
        returns = np.random.normal(mu, sigma, days)
        # Add crisis simulation
        for i in range(days):
            if 800 < i < 830:
                returns[i] = np.random.normal(-0.02, 0.04)
            elif 830 < i < 900:
                returns[i] = np.random.normal(0.005, 0.02)
            elif 950 < i < 1050:
                returns[i] = np.random.normal(0.003, 0.02)

        prices = start_price * np.cumprod(1 + returns)
        high = prices * (1 + np.abs(np.random.normal(0, 0.01, days)))
        low = prices * (1 - np.abs(np.random.normal(0, 0.01, days)))
        open_p = prices * (1 + np.random.normal(0, 0.005, days))
        volume = np.random.lognormal(mean=15, sigma=0.5, size=days).astype(int)

        df = pd.DataFrame({
            'Date': dates.strftime('%Y-%m-%d'),
            'ticker': ticker,
            'open': np.round(open_p, 2),
            'high': np.round(high, 2),
            'low': np.round(low, 2),
            'close': np.round(prices, 2),
            'adj_close': np.round(prices * (1 + np.random.normal(0, 0.001, days)), 2),
            'volume': volume,
        })

        all_data[ticker] = df

    return all_data


def test_1_standard_pipeline():
    """Test 1: Standard CSV → HTML pipeline."""
    print("\n" + "=" * 60)
    print("  TEST 1: Standard Pipeline (CSV → HTML)")
    print("=" * 60)

    from engine.autoplot import VeritasAutoPlot

    # Generate single ticker CSV
    all_data = generate_vdf_compatible_data()
    csv_path = os.path.join(os.path.dirname(__file__), 'sample_data', 'TSM_stock.csv')
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)

    df = all_data['TSM'].copy()
    df = df.rename(columns={'close': 'Close', 'open': 'Open', 'high': 'High',
                            'low': 'Low', 'volume': 'Volume', 'adj_close': 'Adj Close'})
    df.to_csv(csv_path, index=False)

    engine = VeritasAutoPlot(output_dir=os.path.join(os.path.dirname(__file__), 'output'))
    html = engine.run(csv_path, asset_name="TSM (TSMC ADR)")
    output_path = engine.save()

    output = engine.get_structured_output()
    print(f"  [OK] Plots: {len(output['plots'])}")
    print(f"  [OK] Insights: {len(output['insights'])}")
    print(f"  [OK] HTML: {len(html):,} bytes → {output_path}")

    return output_path


def test_2_vdf_schema_data():
    """Test 2: VDF Schema compatible multi-table data."""
    print("\n" + "=" * 60)
    print("  TEST 2: VDF Schema Compatible Data")
    print("=" * 60)

    from engine.vdf_bridge import VDFBridge

    bridge = VDFBridge()

    # Generate VDF-format CSV
    all_data = generate_vdf_compatible_data()

    # Save as VDF-format export
    data_dir = os.path.join(os.path.dirname(__file__), 'sample_data', 'vdf_export')
    os.makedirs(data_dir, exist_ok=True)

    # stock_intl format
    stock_df = all_data['NVDA'].copy()
    stock_path = os.path.join(data_dir, 'stock_intl_C02_20210101_20260319.csv')
    stock_df.to_csv(stock_path, index=False, encoding='utf-8-sig')

    # Load via bridge
    df = bridge.load_from_vdf_export(stock_path, table_hint='stock_intl', ticker='NVDA')
    print(f"  [OK] VDF stock_intl loaded: {len(df)} rows, Main_Price present: {'Main_Price' in df.columns}")

    # Run through pipeline
    from engine.autoplot import VeritasAutoPlot
    engine = VeritasAutoPlot(output_dir=os.path.join(os.path.dirname(__file__), 'output'))

    # Save standardized data as CSV for pipeline
    temp_csv = os.path.join(data_dir, 'nvda_standardized.csv')
    df_export = df.reset_index()
    df_export.rename(columns={'date': 'Date'}, inplace=True)
    df_export.to_csv(temp_csv, index=False)

    html = engine.run(temp_csv, asset_name="NVDA (NVIDIA)")
    output_path = engine.save(os.path.join(os.path.dirname(__file__), 'output', 'VAP_NVDA_VDF.html'))
    print(f"  [OK] VDF pipeline complete → {output_path}")

    return output_path


def test_3_etf_flow():
    """Test 3: ETF Fund Flow visualization."""
    print("\n" + "=" * 60)
    print("  TEST 3: ETF Fund Flow Visualization")
    print("=" * 60)

    from engine.vdf_bridge import VDFFlowEngine
    from engine.chart_flow import chart_dvol_ratio, chart_price_flow_overlay
    from engine.html_renderer import VeritasHTMLRenderer

    all_data = generate_vdf_compatible_data()
    flow_engine = VDFFlowEngine()

    # Calculate flow for SMH
    smh = all_data['SMH'].copy()
    smh['Date'] = pd.to_datetime(smh['Date'])
    smh = smh.set_index('Date').sort_index()
    smh.rename(columns={'close': 'Close', 'volume': 'Volume'}, inplace=True)
    smh['Main_Price'] = smh['Close']

    smh = flow_engine.calculate_flow(smh)

    # Generate charts
    charts = [
        {
            'id': 'dvol_ratio',
            'title': 'SMH — Dollar Volume Ratio',
            'figure': chart_dvol_ratio(smh, title='SMH Dollar Volume Ratio'),
            'tab_group': 'Fund Flow',
        },
        {
            'id': 'price_flow',
            'title': 'SMH — Price with Flow Overlay',
            'figure': chart_price_flow_overlay(smh, title='SMH Price + Fund Flow'),
            'tab_group': 'Fund Flow',
        },
    ]

    # Count flow events
    inflow_count = len(smh[smh['flow_label'] == 'INFLOW'])
    outflow_count = len(smh[smh['flow_label'] == 'OUTFLOW'])

    kpi_cards = [
        {"label": "INFLOW EVENTS", "value": str(inflow_count), "accent": "--gn"},
        {"label": "OUTFLOW EVENTS", "value": str(outflow_count), "accent": "--co"},
        {"label": "LATEST DVOL RATIO", "value": f"{smh['dvol_ratio'].iloc[-1]:.2f}x", "accent": "--bl"},
        {"label": "LATEST FLOW", "value": smh['flow_label'].iloc[-1], "accent": "--am"},
    ]

    html = VeritasHTMLRenderer.render_dashboard(
        title="SMH ETF Fund Flow Analysis",
        subtitle="VDF CentralHub LEGO v6",
        kpi_cards=kpi_cards,
        charts=charts,
    )

    output_path = os.path.join(os.path.dirname(__file__), 'output', 'VAP_SMH_Flow.html')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"  [OK] INFLOW events: {inflow_count}")
    print(f"  [OK] OUTFLOW events: {outflow_count}")
    print(f"  [OK] Flow dashboard → {output_path}")

    return output_path


def test_4_panoramic_data():
    """Test 4: VDF PANORAMIC_DATA visualization."""
    print("\n" + "=" * 60)
    print("  TEST 4: VDF PANORAMIC_DATA Visualization")
    print("=" * 60)

    from engine.vdf_bridge import VDFBridge, VDFPanoramicVisualizer
    from engine.html_renderer import VeritasHTMLRenderer

    bridge = VDFBridge()

    # Load real PANORAMIC_DATA
    panoramic_path = '/home/ubuntu/upload/pasted_file_tFyNO7_VDF_PANORAMIC_DATA_20260219_024823.json'
    if os.path.exists(panoramic_path):
        panoramic = bridge.load_panoramic_data(panoramic_path)
        viz = VDFPanoramicVisualizer()

        kpi_cards = viz.build_panoramic_kpi(panoramic)
        tables = viz.build_panoramic_tables(panoramic)

        html = VeritasHTMLRenderer.render_dashboard(
            title="VDF System Panoramic View",
            subtitle="PANORAMIC_DATA Visualization",
            kpi_cards=kpi_cards,
            charts=[],
            tables=tables,
            data_profile=panoramic.get('meta', {}),
        )

        output_path = os.path.join(os.path.dirname(__file__), 'output', 'VAP_VDF_Panoramic.html')
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"  [OK] Panoramic KPIs: {len(kpi_cards)}")
        print(f"  [OK] Panoramic Tables: {len(tables)}")
        print(f"  [OK] Panoramic dashboard → {output_path}")
        return output_path
    else:
        print("  [SKIP] PANORAMIC_DATA file not found")
        return None


def test_5_anchor_registry():
    """Test 5: VRN Anchor AST Registry export."""
    print("\n" + "=" * 60)
    print("  TEST 5: VRN Anchor AST Registry Export")
    print("=" * 60)

    from engine.vdf_bridge import VDFBridge

    # Export anchor registry
    anchor_path = os.path.join(os.path.dirname(__file__), 'output', 'VAP_Anchor_AST_Registry.json')
    VDFBridge.export_anchor_registry(anchor_path)

    with open(anchor_path, 'r') as f:
        registry = json.load(f)

    anchors = registry['modules']['VAP_CORE']['anchors']
    print(f"  [OK] Anchor points exported: {len(anchors)}")
    for a in anchors:
        print(f"       {a}")
    print(f"  [OK] Registry → {anchor_path}")

    # Test AST ID generation
    test_path = "engine/autoplot.py"
    ast_id = VDFBridge.generate_ast_id(test_path)
    print(f"  [OK] AST ID for '{test_path}': {ast_id}")

    return anchor_path


def test_6_multi_comparison():
    """Test 6: Multi-ticker comparison dashboard."""
    print("\n" + "=" * 60)
    print("  TEST 6: Multi-Ticker Comparison Dashboard")
    print("=" * 60)

    from engine.autoplot import VeritasAutoPlot
    from engine.chart_engine import chart_dual_axis
    from engine.html_renderer import VeritasHTMLRenderer
    from engine.ta_engine import VeritasTAEngine, VeritasQuantEngine
    from engine.data_loader import VeritasDataLoader

    all_data = generate_vdf_compatible_data()
    loader = VeritasDataLoader()
    ta = VeritasTAEngine()
    quant = VeritasQuantEngine()

    # Prepare multi-ticker data
    tickers_to_compare = ['TSM', 'NVDA', 'SMH', 'QQQ']
    processed = {}
    metrics_list = []

    for ticker in tickers_to_compare:
        df = all_data[ticker].copy()
        csv_path = os.path.join(os.path.dirname(__file__), 'sample_data', f'{ticker}_compare.csv')
        df.to_csv(csv_path, index=False)

        loaded = loader.load(csv_path)
        if 'Main_Price' in loaded.columns:
            loaded = ta.calculate_all(loaded)
            m = quant.calc_metrics(loaded)
            m['ticker'] = ticker
            metrics_list.append(m)
            processed[ticker] = loaded

    # Build comparison charts
    charts = []

    # Normalized price comparison
    import plotly.graph_objects as go
    fig = go.Figure()
    for ticker, df in processed.items():
        normalized = df['Main_Price'] / df['Main_Price'].iloc[0] * 100
        fig.add_trace(go.Scatter(
            x=df.index, y=normalized,
            mode='lines', name=ticker,
        ))
    fig.update_layout(
        template="plotly_white",
        plot_bgcolor="#ffffff", paper_bgcolor="#ffffff",
        font={"family": "'DM Sans', sans-serif", "size": 12, "color": "#1e1d1a"},
        title="Normalized Price Comparison (Base=100)",
        hovermode="x unified",
        legend={"orientation": "h", "y": -0.15, "x": 0.5, "xanchor": "center"},
        margin={"t": 50, "r": 60, "b": 50, "l": 60},
    )
    fig.update_xaxes(gridcolor="#dbd9d3")
    fig.update_yaxes(gridcolor="#dbd9d3")

    charts.append({
        'id': 'normalized_compare',
        'title': 'Normalized Price Comparison',
        'figure': fig,
        'tab_group': 'Comparison',
    })

    # Dual axis: TSM vs NVDA
    if 'TSM' in processed and 'NVDA' in processed:
        # Align dates
        common = processed['TSM'].index.intersection(processed['NVDA'].index)
        merged = pd.DataFrame({
            'TSM': processed['TSM'].loc[common, 'Main_Price'],
            'NVDA': processed['NVDA'].loc[common, 'Main_Price'],
        })
        charts.append({
            'id': 'tsm_vs_nvda',
            'title': 'TSM vs NVDA (Dual Axis)',
            'figure': chart_dual_axis(merged, 'TSM', 'NVDA', title='TSM vs NVDA'),
            'tab_group': 'Comparison',
        })

    # KPI cards from metrics
    kpi_cards = []
    for m in metrics_list:
        kpi_cards.append({
            "label": m['ticker'],
            "value": f"CAGR {m.get('CAGR',0)*100:.1f}%",
            "accent": "--gn" if m.get('CAGR', 0) > 0 else "--co",
            "delta": f"Sharpe {m.get('Sharpe_Ratio',0):.2f}",
        })

    # Metrics comparison table
    headers = ["Ticker", "CAGR", "Volatility", "Sharpe", "Max DD", "Win Rate"]
    rows = []
    for m in metrics_list:
        rows.append([
            m['ticker'],
            f"{m.get('CAGR',0)*100:.2f}%",
            f"{m.get('Volatility',0)*100:.1f}%",
            f"{m.get('Sharpe_Ratio',0):.3f}",
            f"{m.get('Max_Drawdown',0)*100:.1f}%",
            f"{m.get('Win_Rate',0)*100:.1f}%",
        ])

    tables = [{
        "id": "comparison_metrics",
        "title": "Quantitative Metrics Comparison",
        "headers": headers,
        "rows": rows,
    }]

    html = VeritasHTMLRenderer.render_dashboard(
        title="Multi-Ticker Comparison",
        subtitle="VDF Cross-Asset Analysis",
        kpi_cards=kpi_cards,
        charts=charts,
        tables=tables,
    )

    output_path = os.path.join(os.path.dirname(__file__), 'output', 'VAP_MultiCompare.html')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"  [OK] Tickers compared: {len(tickers_to_compare)}")
    print(f"  [OK] Charts: {len(charts)}")
    print(f"  [OK] Multi-comparison dashboard → {output_path}")

    return output_path


# ── MAIN ─────────────────────────────────────────────────────
if __name__ == '__main__':
    print("=" * 60)
    print("  VeritasAutoPlot™ Full Integration Test Suite")
    print("  VDF/VRN Ecosystem Compatibility Verification")
    print("=" * 60)

    results = {}

    results['test_1'] = test_1_standard_pipeline()
    results['test_2'] = test_2_vdf_schema_data()
    results['test_3'] = test_3_etf_flow()
    results['test_4'] = test_4_panoramic_data()
    results['test_5'] = test_5_anchor_registry()
    results['test_6'] = test_6_multi_comparison()

    print("\n" + "=" * 60)
    print("  INTEGRATION TEST RESULTS")
    print("=" * 60)
    for test_name, path in results.items():
        status = "PASS" if path else "SKIP"
        print(f"  [{status}] {test_name}: {path or 'N/A'}")

    print(f"\n  All outputs in: {os.path.join(os.path.dirname(__file__), 'output')}")
    print("=" * 60)
