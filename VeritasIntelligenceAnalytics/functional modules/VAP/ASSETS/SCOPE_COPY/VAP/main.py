#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  VeritasAutoPlot v4.0 - CLI Entry Point                                    ║
║  main.py | Veritas Intelligence Analytics                                  ║
║                                                                            ║
║  Usage:                                                                    ║
║    python main.py --demo                      # Run demo with all charts   ║
║    python main.py --source data.csv --chart technical --output png         ║
║    python main.py --template TPL-TECH-001 --ticker 2330.TW                ║
║    python main.py --serve --port 8080         # Launch web UI              ║
║    python main.py --health                    # System health check        ║
║    python main.py --indicators all --source demo                          ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
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

import argparse
import sys
import logging
from pathlib import Path
from datetime import datetime

# Add project paths
sys.path.insert(0, str(Path(__file__).parent / "core"))
sys.path.insert(0, str(Path(__file__).parent / "charts"))
sys.path.insert(0, str(Path(__file__).parent / "api"))

from vap_config import VAPPaths, STANDARD_PERIODS, CHART_DEFAULTS, INDICATOR_DEFAULTS, CDL_PATTERNS
from vap_data_adapter import VAPDataAdapter
from vap_indicators import VAPIndicatorEngine
from vap_templates import VAPTemplateManager
from vap_export import VAPExportEngine
from vap_annotations import VAPAnnotationEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("VAP")


def cmd_health():
    """System health check."""
    print("=" * 60)
    print("  VeritasAutoPlot v4.0 - Health Check")
    print("=" * 60)
    checks = {
        "Root dir":    VAPPaths.ROOT.exists(),
        "VDF root":    VAPPaths.VDF_ROOT.exists(),
        "Core env":    VAPPaths.CORE_ENV.exists(),
        "Output dir":  VAPPaths.OUTPUT.exists() or True,  # Will be created
        "Template dir": VAPPaths.TEMPLATES.exists() or True,
    }

    # Check imports
    try:
        import talib
        checks["TA-Lib"] = True
        checks["TA-Lib version"] = talib.__version__
    except ImportError:
        checks["TA-Lib"] = False

    try:
        import plotly
        checks["Plotly"] = plotly.__version__
    except ImportError:
        checks["Plotly"] = False

    try:
        import pandas
        checks["Pandas"] = pandas.__version__
    except ImportError:
        checks["Pandas"] = False

    for k, v in checks.items():
        status = "PASS" if v else "FAIL"
        print(f"  [{status}] {k}: {v}")

    print(f"\n  Indicators registered: {len(INDICATOR_DEFAULTS)}")
    print(f"  CDL patterns: {len(CDL_PATTERNS)}")
    print(f"  Standard periods: {STANDARD_PERIODS}")
    print("=" * 60)


def cmd_demo():
    """Run full demo with all chart types."""
    print("VeritasAutoPlot v4.0 - Demo Mode")
    print("-" * 40)

    # Generate demo data
    adapter = VAPDataAdapter()
    df = adapter.generate_demo_data(ticker="2330.TW", days=500)
    print(f"Demo data: {df.shape[0]} rows, {df.shape[1]} cols")
    print(f"Adj close column used: {df.columns[4]}")  # adj_close

    # Compute indicators
    engine = VAPIndicatorEngine(df)
    engine.compute_standard_set()
    df = engine.get_result()
    computed = [c for c in df.columns if c not in ["open", "high", "low", "close", "adj_close", "volume"]]
    print(f"Computed {len(computed)} indicator columns")

    # Annotations
    ann = VAPAnnotationEngine(df)
    crisis_zones = ann.detect_crisis_zones(threshold=0.10)
    high_marker, low_marker = ann.find_high_low()
    print(f"Crisis zones: {len(crisis_zones)}")
    print(f"High: {high_marker.label}")
    print(f"Low: {low_marker.label}")

    # Build technical chart
    from vap_chart_technical import VAPTechnicalChart
    tech_chart = VAPTechnicalChart(df)
    fig = tech_chart.build()

    # Add annotations
    shapes = ann.to_plotly_shapes(crisis_zones)
    annotations = ann.to_plotly_annotations(high_marker, low_marker)
    fig.update_layout(shapes=shapes, annotations=annotations)

    # Export
    exporter = VAPExportEngine()
    results = exporter.export_both(fig, base_name="VAP_demo_technical")
    print(f"Exported: {results}")

    # Two-axis chart
    from vap_chart_twoaxis import VAPTwoAxisChart
    twoaxis = VAPTwoAxisChart(df)
    fig2 = twoaxis.build(left_col="close", right_col="volume")
    exporter.export_png(fig2, "VAP_demo_twoaxis.png")
    print("Two-axis chart exported")

    # Stack chart
    from vap_chart_stack import VAPStackChart
    stack = VAPStackChart(df)
    stack_panels = [
        {"columns": ["close", "SMA_20", "SMA_60"], "chart_type": "line", "title": "Price + SMA"},
        {"columns": ["volume"], "chart_type": "bar", "title": "Volume"},
        {"columns": ["MACD_HIST"], "chart_type": "bar", "title": "MACD Histogram"},
        {"columns": ["RSI_14"], "chart_type": "line", "title": "RSI(14)"},
    ]
    fig3 = stack.build(stack_panels)
    exporter.export_png(fig3, "VAP_demo_stack.png")
    print("Stack chart exported")

    # Heatmap
    from vap_chart_heatmap import VAPHeatmapChart
    heatmap = VAPHeatmapChart(df)
    indicator_cols = [c for c in df.columns if any(c.startswith(p) for p in ["SMA_", "EMA_", "RSI_"])]
    if len(indicator_cols) >= 3:
        fig4 = heatmap.build_correlation(columns=indicator_cols[:8])
        exporter.export_png(fig4, "VAP_demo_heatmap.png")
        print("Heatmap exported")

    # Dashboard
    from vap_chart_dashboard import VAPDashboard
    dashboard = VAPDashboard(df)
    fig5 = dashboard.build()
    exporter.export_both(fig5, base_name="VAP_demo_dashboard")
    print("Dashboard exported")

    print("\n" + "=" * 40)
    print("Demo complete! Check output directory.")
    print(f"Output: {VAPPaths.OUTPUT}")


def cmd_compute(args):
    """Compute indicators on source data."""
    adapter = VAPDataAdapter()
    if args.source == "demo":
        df = adapter.generate_demo_data(days=args.days or 500)
    else:
        df = adapter.auto_load(args.source)

    engine = VAPIndicatorEngine(df)

    if args.indicators == "all":
        engine.compute_all()
    elif args.indicators == "standard":
        engine.compute_standard_set()
    elif args.indicators == "patterns":
        engine.compute_pattern_summary()
    else:
        for ind in args.indicators.split(","):
            ind = ind.strip()
            try:
                engine.compute_by_name(ind.upper())
            except ValueError as e:
                print(f"  WARN: {e}")

    result = engine.get_result()
    original_cols = set(df.columns)
    new_cols = [c for c in result.columns if c not in original_cols]

    print(f"\nResult: {result.shape[0]} rows x {result.shape[1]} cols")
    print(f"Close column (adj priority): {engine.col_map['close']}")
    print(f"New columns ({len(new_cols)}):")
    for c in sorted(new_cols):
        last_val = result[c].dropna().iloc[-1] if not result[c].dropna().empty else "NaN"
        print(f"  {c}: {last_val}")


def cmd_serve(args):
    """Launch FastAPI server."""
    from vap_server import run_server
    print(f"Starting VeritasAutoPlot server on port {args.port}...")
    run_server(port=args.port)


def main():
    parser = argparse.ArgumentParser(
        description="VeritasAutoPlot v4.0 - Financial Charting & Dashboard CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--health", action="store_true", help="System health check")
    parser.add_argument("--demo", action="store_true", help="Run full demo")
    parser.add_argument("--serve", action="store_true", help="Launch web API server")
    parser.add_argument("--port", type=int, default=8080, help="Server port (default: 8080)")
    parser.add_argument("--source", type=str, default="demo", help="Data source path or 'demo'")
    parser.add_argument("--indicators", type=str, default=None,
                        help="Indicators: 'standard', 'all', 'patterns', or comma-separated")
    parser.add_argument("--chart", type=str, choices=["technical", "twoaxis", "stack", "heatmap", "dashboard"],
                        help="Chart type to render")
    parser.add_argument("--output", type=str, choices=["png", "html", "both"], default="both",
                        help="Export format")
    parser.add_argument("--template", type=str, help="Template name to load")
    parser.add_argument("--ticker", type=str, default="2330.TW", help="Ticker symbol")
    parser.add_argument("--days", type=int, default=500, help="Number of days for demo data")

    args = parser.parse_args()

    if args.health:
        cmd_health()
    elif args.demo:
        cmd_demo()
    elif args.serve:
        cmd_serve(args)
    elif args.indicators:
        cmd_compute(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
