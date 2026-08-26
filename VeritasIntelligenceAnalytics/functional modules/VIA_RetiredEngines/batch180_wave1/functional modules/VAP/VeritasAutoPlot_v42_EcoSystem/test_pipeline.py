"""
VeritasAutoPlot™ Pipeline Test
================================
Generates sample financial data and runs the full pipeline.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# ── 1. Generate Sample OHLCV Data (Simulated TWSE-like) ─────────
def generate_sample_data(ticker="2330_TSMC", days=1200, start_price=500):
    """Generate realistic OHLCV data with trend, volatility clusters, and events."""
    np.random.seed(42)
    dates = pd.bdate_range(end=datetime(2026, 3, 19), periods=days)

    # Price simulation with regime changes
    returns = np.random.normal(0.0003, 0.015, days)

    # Add volatility clusters (simulate crises)
    for i in range(days):
        # COVID crash simulation
        if 800 < i < 830:
            returns[i] = np.random.normal(-0.02, 0.04)
        # Recovery rally
        elif 830 < i < 900:
            returns[i] = np.random.normal(0.005, 0.02)
        # 2022 bear market
        elif 500 < i < 600:
            returns[i] = np.random.normal(-0.001, 0.025)
        # AI bubble
        elif 950 < i < 1050:
            returns[i] = np.random.normal(0.003, 0.02)

    prices = start_price * np.cumprod(1 + returns)

    # Generate OHLC from close
    high = prices * (1 + np.abs(np.random.normal(0, 0.01, days)))
    low = prices * (1 - np.abs(np.random.normal(0, 0.01, days)))
    open_p = prices * (1 + np.random.normal(0, 0.005, days))

    # Volume with correlation to volatility
    base_vol = np.random.lognormal(mean=15, sigma=0.5, size=days)
    vol_factor = 1 + 5 * np.abs(returns)
    volume = (base_vol * vol_factor).astype(int)

    df = pd.DataFrame({
        'Date': dates,
        'Open': np.round(open_p, 2),
        'High': np.round(high, 2),
        'Low': np.round(low, 2),
        'Close': np.round(prices, 2),
        'Volume': volume,
    })

    # Save to CSV
    csv_path = os.path.join(os.path.dirname(__file__), 'sample_data', f'{ticker}.csv')
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    df.to_csv(csv_path, index=False)
    print(f"[OK] Sample data saved: {csv_path} ({len(df)} rows)")
    return csv_path


# ── 2. Run Pipeline ─────────────────────────────────────────────
def test_pipeline():
    print("=" * 60)
    print("  VeritasAutoPlot™ Pipeline Test")
    print("=" * 60)

    # Generate sample data
    csv_path = generate_sample_data()

    # Import and run
    from engine.autoplot import VeritasAutoPlot

    engine = VeritasAutoPlot(output_dir=os.path.join(os.path.dirname(__file__), 'output'))

    print("\n[1/3] Running pipeline...")
    html = engine.run(csv_path, asset_name="2330 TSMC")

    print(f"[2/3] HTML generated: {len(html):,} bytes")

    # Save
    output_path = engine.save()
    print(f"[3/3] Saved to: {output_path}")

    # Print structured output
    output = engine.get_structured_output()
    print(f"\n{'─' * 40}")
    print(f"  Plots:    {len(output['plots'])}")
    print(f"  Insights: {len(output['insights'])}")
    print(f"  Profile:  {list(output['data_profile'].keys())}")
    print(f"  Assets:   {len(output['asset_registry'])}")
    print(f"{'─' * 40}")

    for i, insight in enumerate(output['insights'], 1):
        print(f"  [{i}] {insight}")

    print(f"\n{'=' * 60}")
    print(f"  TEST COMPLETE — Output: {output_path}")
    print(f"{'=' * 60}")

    return output_path


if __name__ == '__main__':
    test_pipeline()
