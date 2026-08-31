"""
VeritasAutoPlot™ Main Pipeline v4.1
=====================================
# ANCHOR:VAP_PIPELINE_ENTRY

One-click autonomous data visualization engine.

Input Sources (v4.1):
  - Any file: CSV / Excel / Parquet / JSON
  - VDF DuckDB: intl_v6.duckdb / batch_download.duckdb / akshare_fred_macro.duckdb
  - VDF Export: Parquet / CSV from M01 BatchDownloader / CentralHub LEGO v6
  - VDF M02: AKShare / FRED macro data
  - Google Sheet: Public or shared URL
  - VDF Directory: Auto-scan entire VDF output tree

Output: Standalone HTML dashboard with all charts, insights, and asset registry.
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
import os
import datetime
import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Union

from .data_loader import VeritasDataLoader, VeritasDataProfiler
from .ta_engine import VeritasTAEngine, VeritasQuantEngine
from .bubble_valuation import BubbleEngine, ValuationEngine
from .event_matrix import EVENT_MATRIX, detect_sector
from .chart_engine import (
    chart_price_ma, chart_candlestick, chart_macd, chart_rsi, chart_kd,
    chart_dual_axis, chart_bubble_radar, chart_valuation,
    chart_distribution, chart_drawdown, chart_full_stack,
)
from .html_renderer import VeritasHTMLRenderer
from .design_system import COLORS
from .vdf_connector import (
    VDFConnector, VDFOutputScanner, GSheetConnector,
    MultiDBLoader, VDFNamingParser, MacroBridge,
)
from .vdf_bridge import VDFBridge, VDFFlowEngine, VDFPanoramicVisualizer


class VeritasAutoPlot:
    """
    Main autonomous pipeline with full VDF ecosystem integration.

    Usage (v4.1):
        engine = VeritasAutoPlot()

        # ── Classic: Single file ──
        engine.run("data.csv")
        engine.save()

        # ── VDF: Auto-scan directory ──
        engine.run_vdf(vdf_base="C:\\VeritasIntelligenceAnalytics\\VeritasDataForge",
                       ticker="NVDA")
        engine.save()

        # ── VDF: Specific Parquet ──
        engine.run_vdf_file("etf_daily__DEFAULT__2025-01-01__latest__20260319.parquet",
                            ticker="SMH")
        engine.save()

        # ── Google Sheet ──
        engine.run_gsheet("https://docs.google.com/spreadsheets/d/xxx")
        engine.save()

        # ── VDF: Multi-ticker comparison ──
        engine.run_vdf_compare(
            vdf_base="C:\\VeritasIntelligenceAnalytics\\VeritasDataForge",
            tickers=["NVDA", "AMD", "TSM"],
            table="stock_intl"
        )
        engine.save()

        # ── VDF: Macro dashboard ──
        engine.run_macro(vdf_base="...", regions=["US", "EU", "CN"])
        engine.save()
    """

    def __init__(self, output_dir: str = None):
        # Core engines
        self.loader = VeritasDataLoader()
        self.profiler = VeritasDataProfiler()
        self.ta = VeritasTAEngine()
        self.quant = VeritasQuantEngine()
        self.bubble = BubbleEngine()
        self.valuation = ValuationEngine()

        # VDF integration
        self.vdf_connector = None  # Lazy init
        self.vdf_bridge = VDFBridge()
        self.flow_engine = VDFFlowEngine()

        # Output
        self.output_dir = output_dir or os.path.join(os.path.dirname(__file__), '..', 'output')
        os.makedirs(self.output_dir, exist_ok=True)

        # State
        self._df = None
        self._profile = None
        self._quant_metrics = None
        self._html = None
        self._asset_registry = []
        self._insights = []
        self._timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self._source_info = {}

    # ═══════════════════════════════════════════════════════════
    # PUBLIC API: Classic File Input
    # ═══════════════════════════════════════════════════════════

    def run(self, filepath: str, asset_name: str = None) -> str:
        """
        Execute the full pipeline from a single file.
        """
        # ── 1. LOAD ──────────────────────────────────────────────
        self._df = self.loader.load(filepath)
        filename = Path(filepath).stem
        asset_name = asset_name or filename
        sector = detect_sector(filename)
        self._source_info = {'type': 'file', 'path': filepath, 'format': Path(filepath).suffix}

        return self._execute_pipeline(asset_name, sector)

    # ═══════════════════════════════════════════════════════════
    # PUBLIC API: VDF Directory Auto-Scan
    # ═══════════════════════════════════════════════════════════

    def run_vdf(self, vdf_base: str, ticker: str,
                table: str = None,
                start_date: str = None,
                end_date: str = None,
                asset_name: str = None) -> str:
        """
        Auto-scan VDF output directory and load data for a specific ticker.

        Args:
            vdf_base: VDF base directory
            ticker: Ticker symbol (e.g., "NVDA", "2330.TW")
            table: Optional table filter (e.g., "stock_intl", "etf_daily")
            start_date: Optional start date filter
            end_date: Optional end date filter
            asset_name: Optional display name
        """
        # Initialize connector
        self.vdf_connector = VDFConnector(vdf_base=vdf_base)
        scan_result = self.vdf_connector.scan()

        # Load data
        self._df = self.vdf_connector.load_ticker(
            ticker, table=table,
            start_date=start_date, end_date=end_date
        )

        if self._df.empty:
            raise ValueError(
                f"No data found for ticker '{ticker}' in VDF directory: {vdf_base}\n"
                f"Scan result: {scan_result}"
            )

        asset_name = asset_name or ticker
        sector = detect_sector(ticker)
        self._source_info = {
            'type': 'vdf_scan', 'vdf_base': vdf_base,
            'ticker': ticker, 'table': table,
            'scan_summary': scan_result,
        }

        return self._execute_pipeline(asset_name, sector)

    # ═══════════════════════════════════════════════════════════
    # PUBLIC API: VDF Specific File
    # ═══════════════════════════════════════════════════════════

    def run_vdf_file(self, filepath: str, ticker: str = None,
                     asset_name: str = None) -> str:
        """
        Load from a specific VDF export file (Parquet/CSV/JSON).

        Args:
            filepath: Path to VDF export file
            ticker: Optional ticker filter
            asset_name: Optional display name
        """
        self.vdf_connector = VDFConnector()
        self._df = self.vdf_connector.load_file(filepath, ticker=ticker)

        if self._df.empty:
            raise ValueError(f"No data loaded from: {filepath}")

        # Parse filename for metadata
        meta = VDFNamingParser.parse(filepath)
        asset_name = asset_name or ticker or Path(filepath).stem
        sector = detect_sector(asset_name)
        self._source_info = {
            'type': 'vdf_file', 'path': filepath,
            'ticker': ticker, 'file_meta': meta,
        }

        return self._execute_pipeline(asset_name, sector)

    # ═══════════════════════════════════════════════════════════
    # PUBLIC API: Google Sheet
    # ═══════════════════════════════════════════════════════════

    def run_gsheet(self, url: str, gid: str = None,
                   asset_name: str = None) -> str:
        """
        Load data from a Google Sheet URL.

        Args:
            url: Google Sheet URL (must be public or shared with link)
            gid: Optional sheet GID (tab number)
            asset_name: Optional display name
        """
        self.vdf_connector = VDFConnector(gsheet_urls=[url])
        self._df = self.vdf_connector.load_gsheet(url, gid=gid)

        if self._df.empty:
            raise ValueError(f"No data loaded from Google Sheet: {url}")

        asset_name = asset_name or "Google Sheet Data"
        sector = detect_sector(asset_name)
        self._source_info = {'type': 'gsheet', 'url': url, 'gid': gid}

        return self._execute_pipeline(asset_name, sector)

    # ═══════════════════════════════════════════════════════════
    # PUBLIC API: VDF Multi-Ticker Comparison
    # ═══════════════════════════════════════════════════════════

    def run_vdf_compare(self, vdf_base: str, tickers: List[str],
                        table: str = None,
                        start_date: str = None,
                        end_date: str = None,
                        asset_name: str = None) -> str:
        """
        Load multiple tickers from VDF and generate comparison dashboard.

        Args:
            vdf_base: VDF base directory
            tickers: List of ticker symbols
            table: Optional table filter
            start_date: Optional start date
            end_date: Optional end date
            asset_name: Optional display name
        """
        self.vdf_connector = VDFConnector(vdf_base=vdf_base)
        self.vdf_connector.scan()

        # Load all tickers
        all_dfs = {}
        for t in tickers:
            df = self.vdf_connector.load_ticker(
                t, table=table,
                start_date=start_date, end_date=end_date
            )
            if not df.empty and 'Main_Price' in df.columns:
                all_dfs[t] = df

        if not all_dfs:
            raise ValueError(f"No data found for tickers: {tickers}")

        # Build comparison DataFrame
        comparison = pd.DataFrame()
        for t, df in all_dfs.items():
            comparison[t] = df['Main_Price']

        # Normalize to 100
        comparison_norm = comparison.div(comparison.iloc[0]) * 100

        asset_name = asset_name or f"Compare: {', '.join(tickers)}"
        self._source_info = {
            'type': 'vdf_compare', 'vdf_base': vdf_base,
            'tickers': tickers, 'table': table,
        }

        # Generate comparison charts
        charts = []
        import plotly.graph_objects as go

        # Normalized comparison
        fig = go.Figure()
        for t in comparison_norm.columns:
            fig.add_trace(go.Scatter(
                x=comparison_norm.index, y=comparison_norm[t],
                name=t, mode='lines',
            ))
        fig.update_layout(
            title=f"Normalized Price Comparison (Base=100)",
            template='plotly_dark',
            paper_bgcolor='#0a0a0f',
            plot_bgcolor='#0a0a0f',
            font=dict(family='Inter, sans-serif', color='#e0e0e0'),
            height=500,
        )
        self._register_asset("multi_compare_normalized")
        charts.append({
            'id': 'compare_norm', 'title': 'Normalized Comparison',
            'figure': fig, 'tab_group': 'Comparison',
        })

        # Correlation heatmap
        corr = comparison.pct_change().dropna().corr()
        fig_corr = go.Figure(data=go.Heatmap(
            z=corr.values, x=corr.columns, y=corr.index,
            colorscale='RdBu_r', zmin=-1, zmax=1,
            text=corr.round(3).values, texttemplate='%{text}',
        ))
        fig_corr.update_layout(
            title='Return Correlation Matrix',
            template='plotly_dark',
            paper_bgcolor='#0a0a0f',
            plot_bgcolor='#0a0a0f',
            font=dict(family='Inter, sans-serif', color='#e0e0e0'),
            height=450,
        )
        self._register_asset("correlation_matrix")
        charts.append({
            'id': 'correlation', 'title': 'Correlation Matrix',
            'figure': fig_corr, 'tab_group': 'Comparison',
        })

        # Individual TA for each ticker
        for t, df in all_dfs.items():
            df_ta = self.ta.calculate_all(df.copy())
            fig_ta = chart_price_ma(df_ta, title=f'{t} Price & MA')
            self._register_asset(f"price_ma_{t}")
            charts.append({
                'id': f'price_ma_{t}', 'title': f'{t} — Price & MA',
                'figure': fig_ta, 'tab_group': f'{t} Detail',
            })

        # KPI cards
        kpi_cards = [
            {"label": "TICKERS", "value": str(len(all_dfs)), "accent": "--bl"},
        ]
        for t, df in all_dfs.items():
            if 'Main_Price' in df.columns and len(df) > 1:
                ret = (df['Main_Price'].iloc[-1] / df['Main_Price'].iloc[0] - 1) * 100
                kpi_cards.append({
                    "label": t,
                    "value": f"{df['Main_Price'].iloc[-1]:,.2f}",
                    "accent": "--gn" if ret > 0 else "--co",
                    "delta": f"{'+'if ret>0 else ''}{ret:.1f}%",
                })

        # Insights
        insights = [f"Comparing {len(all_dfs)} assets: {', '.join(all_dfs.keys())}"]
        if len(corr) > 1:
            max_corr = corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool)).stack()
            if len(max_corr) > 0:
                max_pair = max_corr.idxmax()
                insights.append(
                    f"Highest correlation: {max_pair[0]} ↔ {max_pair[1]} ({max_corr.max():.3f})"
                )
                min_pair = max_corr.idxmin()
                insights.append(
                    f"Lowest correlation: {min_pair[0]} ↔ {min_pair[1]} ({max_corr.min():.3f})"
                )

        # Render
        self._insights = insights
        self._html = VeritasHTMLRenderer.render_dashboard(
            title=asset_name,
            subtitle="v4.1 VDF Compare",
            kpi_cards=kpi_cards,
            charts=charts,
            tables=[],
            insights=insights,
            event_log=[],
            data_profile={'source': 'vdf_compare', 'tickers': tickers},
            asset_registry=self._asset_registry,
        )

        return self._html

    # ═══════════════════════════════════════════════════════════
    # PUBLIC API: VDF Macro Dashboard
    # ═══════════════════════════════════════════════════════════

    def run_macro(self, vdf_base: str = None,
                  macro_file: str = None,
                  regions: List[str] = None,
                  asset_name: str = None) -> str:
        """
        Generate a macro economic dashboard from M02 data.

        Args:
            vdf_base: VDF base directory (auto-scan for M02 data)
            macro_file: Direct path to M02 export file
            regions: Regions to include (e.g., ["US", "EU", "CN"])
            asset_name: Optional display name
        """
        regions = regions or ['US', 'EU', 'CN', 'JP', 'TW']
        asset_name = asset_name or "Global Macro Dashboard"

        charts = []
        kpi_cards = []
        tables = []
        insights = []

        # Load macro data
        macro_dfs = {}
        if macro_file:
            for region in regions:
                try:
                    df = MacroBridge.load_macro_from_parquet(macro_file, region=region)
                    if not df.empty:
                        macro_dfs[region] = df
                except Exception:
                    pass
        elif vdf_base:
            self.vdf_connector = VDFConnector(vdf_base=vdf_base)
            self.vdf_connector.scan()
            for region in regions:
                try:
                    df = self.vdf_connector.load_macro(region=region)
                    if not df.empty:
                        macro_dfs[region] = df
                except Exception:
                    pass

        if macro_dfs:
            kpi_cards.append({
                "label": "REGIONS", "value": str(len(macro_dfs)), "accent": "--bl"
            })

            import plotly.graph_objects as go

            # Build charts per region
            for region, df in macro_dfs.items():
                region_info = MacroBridge.REGIONS.get(region, {})
                label = region_info.get('label', region)
                flag = region_info.get('flag', '')

                numeric_cols = df.select_dtypes(include=[np.number]).columns[:6]
                if len(numeric_cols) > 0:
                    fig = go.Figure()
                    for col in numeric_cols:
                        fig.add_trace(go.Scatter(
                            x=df.index, y=df[col],
                            name=col, mode='lines',
                        ))
                    fig.update_layout(
                        title=f"{flag} {label} Macro Indicators",
                        template='plotly_dark',
                        paper_bgcolor='#0a0a0f',
                        plot_bgcolor='#0a0a0f',
                        font=dict(family='Inter, sans-serif', color='#e0e0e0'),
                        height=400,
                    )
                    self._register_asset(f"macro_{region}")
                    charts.append({
                        'id': f'macro_{region}',
                        'title': f'{flag} {label} Macro',
                        'figure': fig,
                        'tab_group': f'{flag} {label}',
                    })

            insights.append(f"Macro data loaded for {len(macro_dfs)} regions: {', '.join(macro_dfs.keys())}")
        else:
            insights.append("No macro data available. Ensure VDF M02 has been executed.")
            kpi_cards.append({"label": "STATUS", "value": "NO DATA", "accent": "--co"})

        self._source_info = {
            'type': 'macro', 'vdf_base': vdf_base,
            'macro_file': macro_file, 'regions': regions,
        }
        self._insights = insights

        self._html = VeritasHTMLRenderer.render_dashboard(
            title=asset_name,
            subtitle="v4.1 Macro",
            kpi_cards=kpi_cards,
            charts=charts,
            tables=tables,
            insights=insights,
            event_log=[],
            data_profile={'source': 'macro', 'regions': list(macro_dfs.keys())},
            asset_registry=self._asset_registry,
        )

        return self._html

    # ═══════════════════════════════════════════════════════════
    # PUBLIC API: VDF ETF Flow Dashboard
    # ═══════════════════════════════════════════════════════════

    def run_etf_flow(self, vdf_base: str = None,
                     flow_file: str = None,
                     tickers: List[str] = None,
                     asset_name: str = None) -> str:
        """
        Generate ETF fund flow dashboard from VDF data.

        Args:
            vdf_base: VDF base directory
            flow_file: Direct path to etf_flow_daily export
            tickers: ETF tickers to analyze
            asset_name: Optional display name
        """
        from .chart_flow import (
            chart_dvol_ratio, chart_flow_summary, chart_etf_matrix,
            chart_rs_flow, chart_price_flow_overlay,
        )

        asset_name = asset_name or "ETF Flow Monitor"
        tickers = tickers or ['SMH', 'QQQ', 'SPY', 'IWM']

        charts = []
        kpi_cards = []
        insights = []
        all_flow_dfs = {}

        # Load flow data
        if vdf_base:
            self.vdf_connector = VDFConnector(vdf_base=vdf_base)
            self.vdf_connector.scan()

            for t in tickers:
                try:
                    df = self.vdf_connector.load_ticker(t, table='etf_flow_daily')
                    if df.empty:
                        df = self.vdf_connector.load_ticker(t, table='etf_daily')
                        if not df.empty:
                            df = self.flow_engine.calculate_flow(df)
                    if not df.empty:
                        all_flow_dfs[t] = df
                except Exception:
                    pass

        elif flow_file:
            for t in tickers:
                try:
                    df = self.vdf_bridge.load_etf_flow(flow_file, ticker=t)
                    if not df.empty:
                        all_flow_dfs[t] = df
                except Exception:
                    pass

        # Generate flow charts
        for t, df in all_flow_dfs.items():
            if 'dvol_ratio' in df.columns:
                fig = chart_dvol_ratio(df, title=f'{t} Dollar Volume Ratio')
                self._register_asset(f"dvol_ratio_{t}")
                charts.append({
                    'id': f'dvol_{t}', 'title': f'{t} — dvol_ratio',
                    'figure': fig, 'tab_group': 'Flow Analysis',
                })

            if 'flow_label' in df.columns:
                fig = chart_flow_summary(df, title=f'{t} Flow Summary')
                self._register_asset(f"flow_summary_{t}")
                charts.append({
                    'id': f'flow_{t}', 'title': f'{t} — Flow',
                    'figure': fig, 'tab_group': 'Flow Analysis',
                })

        # KPI
        kpi_cards.append({"label": "ETFs", "value": str(len(all_flow_dfs)), "accent": "--bl"})
        for t, df in all_flow_dfs.items():
            if 'flow_label' in df.columns:
                latest = df['flow_label'].iloc[-1] if len(df) > 0 else 'N/A'
                accent = "--gn" if latest == 'INFLOW' else "--co" if latest == 'OUTFLOW' else "--am"
                kpi_cards.append({"label": t, "value": latest, "accent": accent})

        insights.append(f"ETF Flow analysis for {len(all_flow_dfs)} tickers: {', '.join(all_flow_dfs.keys())}")

        self._source_info = {'type': 'etf_flow', 'tickers': tickers}
        self._insights = insights

        self._html = VeritasHTMLRenderer.render_dashboard(
            title=asset_name,
            subtitle="v4.1 ETF Flow",
            kpi_cards=kpi_cards,
            charts=charts,
            tables=[],
            insights=insights,
            event_log=[],
            data_profile={'source': 'etf_flow', 'tickers': list(all_flow_dfs.keys())},
            asset_registry=self._asset_registry,
        )

        return self._html

    # ═══════════════════════════════════════════════════════════
    # PUBLIC API: DataFrame Direct Input
    # ═══════════════════════════════════════════════════════════

    def run_df(self, df: pd.DataFrame, asset_name: str = "DataFrame") -> str:
        """
        Run pipeline directly from a pandas DataFrame.
        Useful for programmatic integration with VDF modules.
        """
        self._df = df.copy()
        self._source_info = {'type': 'dataframe', 'shape': df.shape}

        # Ensure standardization
        if 'Main_Price' not in self._df.columns:
            price_cols = ['adj_close', 'close', 'Close', 'Adj Close', 'price', 'value']
            for col in price_cols:
                if col in self._df.columns:
                    self._df['Main_Price'] = pd.to_numeric(self._df[col], errors='coerce')
                    break

        sector = detect_sector(asset_name)
        return self._execute_pipeline(asset_name, sector)

    # ═══════════════════════════════════════════════════════════
    # SAVE & OUTPUT
    # ═══════════════════════════════════════════════════════════

    def save(self, filepath: str = None) -> str:
        """Save the generated HTML to a file."""
        if self._html is None:
            raise RuntimeError("No HTML generated. Run the pipeline first.")

        if filepath is None:
            filepath = os.path.join(self.output_dir, f"VeritasAutoPlot_{self._timestamp}.html")

        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(self._html)

        return filepath

    def get_structured_output(self) -> dict:
        """Return the structured output as specified by the system."""
        return {
            "plots": [a for a in self._asset_registry if a['asset_type'] == 'plot'],
            "insights": self._insights,
            "data_profile": self._profile,
            "asset_registry": self._asset_registry,
            "source_info": self._source_info,
        }

    def get_vdf_catalog(self) -> List[Dict]:
        """Get the VDF file catalog (after scan)."""
        if self.vdf_connector:
            return self.vdf_connector.get_catalog()
        return []

    def get_vdf_summary(self) -> Dict:
        """Get VDF scan summary."""
        if self.vdf_connector:
            return self.vdf_connector.get_summary()
        return {}

    # ═══════════════════════════════════════════════════════════
    # INTERNAL: Core Pipeline Execution
    # ═══════════════════════════════════════════════════════════

    def _execute_pipeline(self, asset_name: str, sector: str) -> str:
        """
        # ANCHOR:VAP_PIPELINE_CORE
        Core pipeline shared by all input methods.
        """
        # ── 2. PROFILE ───────────────────────────────────────────
        self._profile = self.profiler.profile(self._df)
        self._profile['asset_name'] = asset_name
        self._profile['sector'] = sector
        self._profile['source'] = self._source_info.get('type', 'unknown')

        # ── 3. TECHNICAL ANALYSIS ────────────────────────────────
        if 'Main_Price' in self._df.columns:
            self._df = self.ta.calculate_all(self._df)

        # ── 4. QUANT METRICS ────────────────────────────────────
        if 'Main_Price' in self._df.columns and len(self._df) > 30:
            self._quant_metrics = self.quant.calc_metrics(self._df)
        else:
            self._quant_metrics = {}

        # ── 5. BUBBLE DETECTION ──────────────────────────────────
        if 'Main_Price' in self._df.columns and len(self._df) > 60:
            self._df = self.bubble.detect(self._df)

        # ── 6. VALUATION ────────────────────────────────────────
        if 'Main_Price' in self._df.columns and len(self._df) > 30:
            self._df = self.valuation.calculate(self._df)

        # ── 7. GENERATE CHARTS ──────────────────────────────────
        charts = self._generate_charts(asset_name)

        # ── 8. GENERATE INSIGHTS ────────────────────────────────
        self._insights = self._generate_insights(asset_name)

        # ── 9. BUILD KPI CARDS ──────────────────────────────────
        kpi_cards = self._build_kpi_cards()

        # ── 10. BUILD TABLES ────────────────────────────────────
        tables = self._build_tables()

        # ── 11. BUILD EVENT LOG ─────────────────────────────────
        event_log = self._build_event_log()

        # ── 12. RENDER HTML ─────────────────────────────────────
        # ANCHOR:VAP_PIPELINE_RENDER
        self._html = VeritasHTMLRenderer.render_dashboard(
            title=f"{asset_name} Analysis",
            subtitle="v4.1",
            kpi_cards=kpi_cards,
            charts=charts,
            tables=tables,
            insights=self._insights,
            event_log=event_log,
            data_profile=self._profile,
            asset_registry=self._asset_registry,
        )

        # ANCHOR:VAP_PIPELINE_EXIT
        return self._html

    # ═══════════════════════════════════════════════════════════
    # PRIVATE METHODS
    # ═══════════════════════════════════════════════════════════

    def _register_asset(self, viz_type: str, params: dict = None) -> str:
        """Register a Smart Asset and return its ID."""
        asset_id = f"VAP_{self._timestamp}_{len(self._asset_registry):03d}"
        self._asset_registry.append({
            "asset_id": asset_id,
            "asset_type": "plot",
            "visualization_type": viz_type,
            "generation_timestamp": self._timestamp,
            "parameters": params or {},
        })
        return asset_id

    def _generate_charts(self, asset_name: str) -> list:
        """Generate all applicable charts based on data profile."""
        charts = []

        if 'Main_Price' not in self._df.columns:
            return charts

        # 1. Full Stack (Price + Volume + MACD + RSI)
        self._register_asset("full_stack")
        charts.append({
            'id': 'full_stack',
            'title': f'{asset_name} — Full Technical Analysis',
            'figure': chart_full_stack(self._df, title=f'{asset_name} Technical Analysis'),
            'tab_group': 'Technical Analysis',
        })

        # 2. Price + MA
        self._register_asset("price_ma")
        charts.append({
            'id': 'price_ma',
            'title': f'{asset_name} — Price & Moving Averages',
            'figure': chart_price_ma(self._df, title=f'{asset_name} Price & MA'),
            'tab_group': 'Price & MA',
        })

        # 3. Candlestick (if OHLC available)
        if self._profile.get('has_ohlc'):
            self._register_asset("candlestick")
            charts.append({
                'id': 'candlestick',
                'title': f'{asset_name} — K-Line',
                'figure': chart_candlestick(self._df, title=f'{asset_name} K-Line'),
                'tab_group': 'Price & MA',
            })

        # 4. MACD
        if 'MACD' in self._df.columns:
            self._register_asset("macd")
            charts.append({
                'id': 'macd',
                'title': 'MACD Oscillator',
                'figure': chart_macd(self._df),
                'tab_group': 'Oscillators',
            })

        # 5. RSI
        if 'RSI' in self._df.columns:
            self._register_asset("rsi")
            charts.append({
                'id': 'rsi',
                'title': 'RSI (14)',
                'figure': chart_rsi(self._df),
                'tab_group': 'Oscillators',
            })

        # 6. KD
        if 'K' in self._df.columns:
            self._register_asset("kd")
            charts.append({
                'id': 'kd',
                'title': 'KD Stochastic',
                'figure': chart_kd(self._df),
                'tab_group': 'Oscillators',
            })

        # 7. Distribution
        if 'Daily_Ret' in self._df.columns:
            self._register_asset("distribution")
            charts.append({
                'id': 'distribution',
                'title': 'Return Distribution',
                'figure': chart_distribution(self._df),
                'tab_group': 'Quant Analysis',
            })

        # 8. Drawdown
        if 'Drawdown' in self._df.columns:
            self._register_asset("drawdown")
            charts.append({
                'id': 'drawdown',
                'title': 'Underwater Plot (Drawdown)',
                'figure': chart_drawdown(self._df),
                'tab_group': 'Quant Analysis',
            })

        # 9. Bubble Radar
        if 'Z_Score' in self._df.columns:
            self._register_asset("bubble_radar")
            charts.append({
                'id': 'bubble_radar',
                'title': 'Bubble Radar (Z-Score)',
                'figure': chart_bubble_radar(self._df),
                'tab_group': 'Bubble & Valuation',
            })

        # 10. Valuation Channel
        if 'Fair_Value' in self._df.columns:
            self._register_asset("valuation_channel")
            charts.append({
                'id': 'valuation',
                'title': 'Valuation Channel (Log-Linear Regression)',
                'figure': chart_valuation(self._df),
                'tab_group': 'Bubble & Valuation',
            })

        return charts

    def _build_kpi_cards(self) -> list:
        """Build KPI cards from quant metrics."""
        cards = []

        if not self._quant_metrics:
            cards.append({"label": "ROWS", "value": str(self._profile.get('rows', 0)), "accent": "--bl"})
            cards.append({"label": "COLUMNS", "value": str(self._profile.get('columns', 0)), "accent": "--tl"})
            # Source info
            src = self._source_info.get('type', 'file')
            cards.append({"label": "SOURCE", "value": src.upper(), "accent": "--vi"})
            return cards

        q = self._quant_metrics

        # Price
        if 'Main_Price' in self._df.columns:
            last_price = self._df['Main_Price'].iloc[-1]
            cards.append({
                "label": "LAST PRICE",
                "value": f"{last_price:,.2f}",
                "accent": "--bl",
            })

        # CAGR
        cagr = q.get('CAGR', 0)
        cards.append({
            "label": "CAGR",
            "value": f"{cagr*100:.2f}%",
            "accent": "--gn" if cagr > 0 else "--co",
            "delta": f"{'+'if cagr>0 else ''}{cagr*100:.2f}%",
        })

        # Volatility
        vol = q.get('Volatility', 0)
        cards.append({
            "label": "VOLATILITY",
            "value": f"{vol*100:.1f}%",
            "accent": "--am",
        })

        # Sharpe
        sharpe = q.get('Sharpe_Ratio', 0)
        cards.append({
            "label": "SHARPE",
            "value": f"{sharpe:.2f}",
            "accent": "--gn" if sharpe > 1 else "--am" if sharpe > 0 else "--co",
        })

        # Max Drawdown
        mdd = q.get('Max_Drawdown', 0)
        cards.append({
            "label": "MAX DD",
            "value": f"{mdd*100:.1f}%",
            "accent": "--co",
        })

        # Win Rate
        wr = q.get('Win_Rate', 0)
        cards.append({
            "label": "WIN RATE",
            "value": f"{wr*100:.1f}%",
            "accent": "--gn" if wr > 0.5 else "--co",
        })

        # Source
        src = self._source_info.get('type', 'file')
        cards.append({"label": "SOURCE", "value": src.upper(), "accent": "--vi"})

        # Valuation Score
        val_score = self._df.attrs.get('valuation_score')
        if val_score is not None:
            status = "CHEAP" if val_score < 30 else "FAIR" if val_score < 70 else "EXPENSIVE"
            accent = "--gn" if val_score < 30 else "--am" if val_score < 70 else "--co"
            cards.append({
                "label": "VALUATION",
                "value": f"{val_score:.0f}/100",
                "accent": accent,
                "delta": status,
            })

        # Bubble Z-Score
        if 'Z_Score' in self._df.columns:
            z_current = self._df['Z_Score'].iloc[-1]
            if not np.isnan(z_current):
                cards.append({
                    "label": "BUBBLE Z",
                    "value": f"{z_current:.2f}\u03c3",
                    "accent": "--co" if abs(z_current) > 2 else "--gn",
                })

        return cards

    def _build_tables(self) -> list:
        """Build data tables for the dashboard."""
        tables = []

        # Quant Metrics Table
        if self._quant_metrics:
            q = self._quant_metrics
            rows = [
                ["Total Return", f"{q.get('Total_Return',0)*100:.2f}%"],
                ["CAGR (Annualized)", f"{q.get('CAGR',0)*100:.2f}%"],
                ["Volatility (Annualized)", f"{q.get('Volatility',0)*100:.2f}%"],
                ["Sharpe Ratio", f"{q.get('Sharpe_Ratio',0):.3f}"],
                ["Sortino Ratio", f"{q.get('Sortino_Ratio',0):.3f}"],
                ["Max Drawdown", f"{q.get('Max_Drawdown',0)*100:.2f}%"],
                ["Skewness", f"{q.get('Skewness',0):.3f}"],
                ["Kurtosis", f"{q.get('Kurtosis',0):.3f}"],
                ["VaR (95%)", f"{q.get('VaR_95',0)*100:.2f}%"],
                ["Win Rate", f"{q.get('Win_Rate',0)*100:.1f}%"],
                ["Total Days", f"{q.get('Total_Days',0):,}"],
                ["Years", f"{q.get('Years',0):.2f}"],
            ]
            tables.append({
                "id": "quant_metrics",
                "title": "Quantitative Metrics",
                "headers": ["Metric", "Value"],
                "rows": rows,
            })

        # Bubble Events Table
        if 'Z_Score' in self._df.columns:
            bubble_events = self.bubble.get_bubble_events(self._df)
            if not bubble_events.empty:
                rows = []
                for idx, row in bubble_events.iterrows():
                    date_str = str(idx)[:10] if hasattr(idx, 'strftime') else str(idx)
                    rows.append([
                        date_str,
                        f"{row['Main_Price']:,.2f}",
                        f"{row['Deviation_Pct']:.1f}%",
                        f"{row['Z_Score']:.2f}\u03c3",
                        row['Bubble_Status'],
                    ])
                tables.append({
                    "id": "bubble_events",
                    "title": "Bubble Events (Top Z-Score)",
                    "headers": ["Date", "Price", "Deviation", "Z-Score", "Status"],
                    "rows": rows,
                })

        # Recent Data Table (last 20 rows)
        if 'Main_Price' in self._df.columns:
            recent = self._df.tail(20).iloc[::-1]
            cols_to_show = ['Main_Price']
            for c in ['SMA_20', 'SMA_60', 'RSI', 'MACD', 'Daily_Ret']:
                if c in recent.columns:
                    cols_to_show.append(c)

            rows = []
            for idx, row in recent.iterrows():
                date_str = str(idx)[:10] if hasattr(idx, 'strftime') else str(idx)
                vals = [date_str]
                for c in cols_to_show:
                    v = row[c]
                    if pd.notna(v):
                        vals.append(f"{v:.2f}" if isinstance(v, float) else str(v))
                    else:
                        vals.append("\u2014")
                rows.append(vals)

            tables.append({
                "id": "recent_data",
                "title": "Recent Data (Last 20)",
                "headers": ["Date"] + cols_to_show,
                "rows": rows,
            })

        # Source Info Table
        if self._source_info:
            src_rows = []
            for k, v in self._source_info.items():
                if isinstance(v, (dict, list)):
                    v = json.dumps(v, ensure_ascii=False, default=str)[:80]
                src_rows.append([str(k), str(v)])
            tables.append({
                "id": "source_info",
                "title": "Data Source Info",
                "headers": ["Property", "Value"],
                "rows": src_rows,
            })

        return tables

    def _build_event_log(self) -> list:
        """Build event log from EVENT_MATRIX matching the data date range."""
        if not isinstance(self._df.index, pd.DatetimeIndex):
            return []

        events = []
        data_start = self._df.index.min()
        data_end = self._df.index.max()

        for crisis in EVENT_MATRIX:
            crisis_start = pd.Timestamp(crisis['start'])
            crisis_end = pd.Timestamp(crisis['end'])

            if crisis_end < data_start or crisis_start > data_end:
                continue

            for sub in crisis.get('subEvents', []):
                sub_date = pd.Timestamp(sub['date'])
                if data_start <= sub_date <= data_end:
                    events.append({
                        "date": sub['date'],
                        "label": f"[{crisis['name']}] {sub['label']}",
                        "color": sub.get('color', crisis['color']),
                        "url": crisis.get('urls', [''])[0] if crisis.get('urls') else '',
                    })

        events.sort(key=lambda x: x['date'])
        return events

    def _generate_insights(self, asset_name: str) -> list:
        """Generate data-driven insights."""
        insights = []

        if not self._quant_metrics:
            insights.append(f"Data loaded: {self._profile.get('rows', 0)} rows, {self._profile.get('columns', 0)} columns.")
            src = self._source_info.get('type', 'file')
            insights.append(f"Data source: {src}")
            return insights

        q = self._quant_metrics

        # Source
        src = self._source_info.get('type', 'file')
        if src != 'file':
            insights.append(f"Data loaded from {src.upper()} source via VDF Connector.")

        # Trend
        cagr = q.get('CAGR', 0)
        if cagr > 0.15:
            insights.append(f"{asset_name} exhibits strong long-term growth with CAGR of {cagr*100:.1f}%, significantly outperforming risk-free rate.")
        elif cagr > 0:
            insights.append(f"{asset_name} shows moderate positive trend with CAGR of {cagr*100:.1f}%.")
        else:
            insights.append(f"{asset_name} is in a declining trend with negative CAGR of {cagr*100:.1f}%.")

        # Risk
        sharpe = q.get('Sharpe_Ratio', 0)
        if sharpe > 1.0:
            insights.append(f"Risk-adjusted performance is excellent (Sharpe: {sharpe:.2f}). Returns adequately compensate for volatility.")
        elif sharpe > 0:
            insights.append(f"Risk-adjusted return is positive but moderate (Sharpe: {sharpe:.2f}).")
        else:
            insights.append(f"Risk-adjusted return is negative (Sharpe: {sharpe:.2f}), indicating returns do not justify the risk taken.")

        # Drawdown
        mdd = q.get('Max_Drawdown', 0)
        insights.append(f"Maximum drawdown reached {mdd*100:.1f}%, representing the worst peak-to-trough loss in the observed period.")

        # Distribution Shape
        skew = q.get('Skewness', 0)
        kurt = q.get('Kurtosis', 0)
        if skew < -0.5:
            insights.append(f"Return distribution is negatively skewed ({skew:.2f}), indicating higher frequency of extreme losses (crash risk).")
        if kurt > 3:
            insights.append(f"Excess kurtosis of {kurt:.2f} indicates fat tails — extreme events occur more frequently than normal distribution predicts.")

        # Bubble Status
        if 'Z_Score' in self._df.columns:
            z_current = self._df['Z_Score'].iloc[-1]
            if not np.isnan(z_current):
                if z_current > 3:
                    insights.append(f"BUBBLE ALERT: Current Z-Score is {z_current:.2f}\u03c3, indicating price is statistically detached from its long-term trend.")
                elif z_current < -3:
                    insights.append(f"OVERSOLD SIGNAL: Current Z-Score is {z_current:.2f}\u03c3, suggesting potential mean-reversion opportunity.")
                else:
                    insights.append(f"Bubble Index (Z-Score) is {z_current:.2f}\u03c3 \u2014 within normal statistical range.")

        # Valuation
        val_score = self._df.attrs.get('valuation_score')
        if val_score is not None:
            if val_score < 30:
                insights.append(f"Valuation score is {val_score:.0f}/100 \u2014 price is below the log-linear regression channel, suggesting undervaluation.")
            elif val_score > 70:
                insights.append(f"Valuation score is {val_score:.0f}/100 \u2014 price is above the regression channel, indicating potential overvaluation.")
            else:
                insights.append(f"Valuation score is {val_score:.0f}/100 \u2014 price is within the fair value range of the regression channel.")

        # RSI
        if 'RSI' in self._df.columns:
            rsi_current = self._df['RSI'].iloc[-1]
            if not np.isnan(rsi_current):
                if rsi_current > 70:
                    insights.append(f"RSI is at {rsi_current:.1f} (overbought territory), suggesting potential short-term pullback.")
                elif rsi_current < 30:
                    insights.append(f"RSI is at {rsi_current:.1f} (oversold territory), suggesting potential short-term bounce.")

        return insights
