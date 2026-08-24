"""
VeritasAutoPlot™ Engine Package
"""
from .data_loader import VeritasDataLoader, VeritasDataProfiler
from .ta_engine import VeritasTAEngine, VeritasQuantEngine
from .chart_engine import (
    chart_price_ma, chart_candlestick, chart_macd, chart_rsi, chart_kd,
    chart_dual_axis, chart_bubble_radar, chart_valuation,
    chart_distribution, chart_drawdown, chart_full_stack,
)
from .bubble_valuation import BubbleEngine, ValuationEngine
from .event_matrix import EVENT_MATRIX, detect_sector
from .design_system import *
from .html_renderer import VeritasHTMLRenderer
from .autoplot import VeritasAutoPlot
from .vdf_bridge import VDFBridge, VDFFlowEngine, VDFPanoramicVisualizer, VDF_SCHEMA
from .chart_flow import (
    chart_dvol_ratio, chart_flow_summary, chart_etf_matrix,
    chart_rs_flow, chart_price_flow_overlay,
)
from .vdf_connector import (
    VDFConnector, VDFOutputScanner, GSheetConnector,
    MultiDBLoader, VDFNamingParser, MacroBridge,
)
from .via_integration import (
    VIAAssetBridge, SSOTBridge, VPNConnector, VeritasAutoPlotVIA,
)
