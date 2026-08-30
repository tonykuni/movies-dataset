"""
VeritasAutoPlot™ VDF Bridge Module
====================================
# ANCHOR:VAP_VDF_BRIDGE_ENTRY
Bridges VeritasAutoPlot with the VeritasDataForge (VDF) ecosystem.

Supports:
- VDF Schema v6: 7 CAT tables (index_intl, stock_intl, etf_daily, fx_daily,
  commodity_daily, rate_daily, crypto_daily, etf_flow_daily)
- DuckDB direct read
- VDF PANORAMIC_DATA JSON ingestion
- VDF_ASSET_REGISTRY format output (AST-SHA1 encoding)
- VRN Anchor AST system compatibility
- ETF Flow (dvol_ratio / INFLOW / OUTFLOW) visualization support
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
import json
import hashlib
import datetime
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# ============================================================
# VDF SCHEMA DEFINITIONS (from VDF_CentralHub_LEGO_v6_schema.json)
# ============================================================

VDF_SCHEMA = {
    "index_intl": {
        "cat": "CAT-01", "pk": ["date", "ticker"],
        "ticker_col": "ticker", "auto_adjust": True,
        "label": "國際指數",
    },
    "stock_intl": {
        "cat": "CAT-02", "pk": ["date", "ticker"],
        "ticker_col": "ticker", "auto_adjust": False,
        "label": "國際個股",
    },
    "etf_daily": {
        "cat": "CAT-03", "pk": ["date", "ticker"],
        "ticker_col": "ticker", "auto_adjust": False,
        "label": "國際 ETF",
        "extra_group": "etf_category",
    },
    "fx_daily": {
        "cat": "CAT-04", "pk": ["date", "pair"],
        "ticker_col": "pair", "auto_adjust": False,
        "label": "外匯",
    },
    "commodity_daily": {
        "cat": "CAT-05", "pk": ["date", "ticker"],
        "ticker_col": "ticker", "auto_adjust": False,
        "label": "商品/期貨",
        "has_roll_warn": True,
    },
    "rate_daily": {
        "cat": "CAT-06", "pk": ["date", "ticker"],
        "ticker_col": "ticker", "auto_adjust": False,
        "label": "殖利率",
    },
    "crypto_daily": {
        "cat": "CAT-07", "pk": ["date", "symbol"],
        "ticker_col": "symbol", "auto_adjust": False,
        "label": "加密貨幣",
    },
    "etf_flow_daily": {
        "cat": "CAT-03-FLOW", "pk": ["date", "ticker"],
        "ticker_col": "ticker", "auto_adjust": False,
        "label": "ETF 資金流",
        "extra_group": "etf_category",
    },
}


class VDFBridge:
    """
    # ANCHOR:VAP_VDF_BRIDGE_CORE
    Bridge between VeritasAutoPlot and VeritasDataForge ecosystem.
    """

    def __init__(self):
        self._duckdb_available = False
        try:
            import duckdb
            self._duckdb_available = True
        except ImportError:
            pass

    # ── DuckDB Direct Read ─────────────────────────────────────
    def load_from_duckdb(self, db_path: str, table: str,
                         ticker: str = None,
                         start_date: str = None,
                         end_date: str = None) -> pd.DataFrame:
        """
        # ANCHOR:VAP_VDF_DUCKDB_LOAD
        Load data directly from VDF DuckDB (intl_v6.duckdb).
        """
        if not self._duckdb_available:
            raise ImportError("duckdb not installed. Run: pip install duckdb")

        import duckdb

        schema = VDF_SCHEMA.get(table)
        if schema is None:
            raise ValueError(f"Unknown VDF table: {table}. Valid: {list(VDF_SCHEMA.keys())}")

        ticker_col = schema['ticker_col']

        query = f"SELECT * FROM {table}"
        conditions = []

        if ticker:
            conditions.append(f"{ticker_col} = '{ticker}'")
        if start_date:
            conditions.append(f"date >= '{start_date}'")
        if end_date:
            conditions.append(f"date <= '{end_date}'")

        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY date"

        con = duckdb.connect(db_path, read_only=True)
        df = con.execute(query).fetchdf()
        con.close()

        return self._standardize_vdf_df(df, schema)

    # ── CSV/Parquet from VDF Export ────────────────────────────
    def load_from_vdf_export(self, filepath: str,
                             table_hint: str = None,
                             ticker: str = None) -> pd.DataFrame:
        """
        # ANCHOR:VAP_VDF_EXPORT_LOAD
        Load from VDF-exported CSV/Parquet files.
        Naming convention: {table}_{CAT}_{start}_{end}_{ts}.{ext}
        """
        path = Path(filepath)
        ext = path.suffix.lower()

        if ext == '.csv':
            df = pd.read_csv(filepath, encoding='utf-8-sig')
        elif ext == '.parquet':
            df = pd.read_parquet(filepath)
        elif ext == '.json':
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, list):
                df = pd.DataFrame(data)
            elif isinstance(data, dict):
                for key in ['data', 'records', 'results', 'rows']:
                    if key in data and isinstance(data[key], list):
                        df = pd.DataFrame(data[key])
                        break
                else:
                    df = pd.DataFrame(data)
        else:
            raise ValueError(f"Unsupported VDF export format: {ext}")

        # Auto-detect table from filename
        if table_hint is None:
            stem = path.stem.lower()
            for tbl_name in VDF_SCHEMA:
                if tbl_name in stem:
                    table_hint = tbl_name
                    break

        schema = VDF_SCHEMA.get(table_hint, {})

        # Filter by ticker if needed
        if ticker and schema.get('ticker_col') and schema['ticker_col'] in df.columns:
            df = df[df[schema['ticker_col']] == ticker]

        return self._standardize_vdf_df(df, schema)

    # ── PANORAMIC_DATA JSON ────────────────────────────────────
    def load_panoramic_data(self, filepath: str) -> dict:
        """
        # ANCHOR:VAP_VDF_PANORAMIC_LOAD
        Load VDF PANORAMIC_DATA JSON for system health visualization.
        Returns structured dict for dashboard rendering.
        """
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            data = json.load(f)

        result = {
            "meta": data.get("Meta", {}),
            "summary": data.get("Summary", {}),
            "modules": data.get("Modules", []),
            "workflows": data.get("Workflows", []),
            "issues": data.get("Issues", []),
            "db_health": data.get("Summary", {}).get("DBHealthScore", 0),
        }

        return result

    # ── ETF Flow Data ──────────────────────────────────────────
    def load_etf_flow(self, filepath_or_db: str,
                      ticker: str = None,
                      is_duckdb: bool = False) -> pd.DataFrame:
        """
        # ANCHOR:VAP_VDF_ETF_FLOW_LOAD
        Load ETF flow data (dvol_ratio, INFLOW/OUTFLOW labels).
        """
        if is_duckdb:
            return self.load_from_duckdb(filepath_or_db, 'etf_flow_daily', ticker=ticker)
        else:
            return self.load_from_vdf_export(filepath_or_db, table_hint='etf_flow_daily', ticker=ticker)

    # ── Multi-Ticker Batch Load ────────────────────────────────
    def load_multi_ticker(self, filepath_or_db: str, table: str,
                          tickers: List[str],
                          is_duckdb: bool = False) -> Dict[str, pd.DataFrame]:
        """
        # ANCHOR:VAP_VDF_MULTI_LOAD
        Load multiple tickers from the same table.
        Returns dict of {ticker: DataFrame}.
        """
        results = {}
        for ticker in tickers:
            try:
                if is_duckdb:
                    df = self.load_from_duckdb(filepath_or_db, table, ticker=ticker)
                else:
                    df = self.load_from_vdf_export(filepath_or_db, table_hint=table, ticker=ticker)
                if len(df) > 0:
                    results[ticker] = df
            except Exception as e:
                results[ticker] = pd.DataFrame()  # Empty on error
        return results

    # ── Standardization ────────────────────────────────────────
    def _standardize_vdf_df(self, df: pd.DataFrame, schema: dict) -> pd.DataFrame:
        """
        # ANCHOR:VAP_VDF_STANDARDIZE
        Standardize VDF DataFrame to AutoPlot format.
        - Set DatetimeIndex
        - Map price columns
        - Handle adj_close logic
        """
        if df.empty:
            return df

        # Date index
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            df = df.set_index('date').sort_index()

        # Price mapping: use adj_close if available and auto_adjust=false
        auto_adj = schema.get('auto_adjust', False)

        if not auto_adj and 'adj_close' in df.columns:
            df['Main_Price'] = pd.to_numeric(df['adj_close'], errors='coerce')
        elif 'close' in df.columns:
            df['Main_Price'] = pd.to_numeric(df['close'], errors='coerce')
        elif 'Close' in df.columns:
            df['Main_Price'] = pd.to_numeric(df['Close'], errors='coerce')

        # Map OHLC columns to standard names (case-insensitive)
        col_map = {}
        for col in df.columns:
            cl = col.lower()
            if cl == 'open' and 'Open' not in df.columns:
                col_map[col] = 'Open'
            elif cl == 'high' and 'High' not in df.columns:
                col_map[col] = 'High'
            elif cl == 'low' and 'Low' not in df.columns:
                col_map[col] = 'Low'
            elif cl == 'close' and 'Close' not in df.columns:
                col_map[col] = 'Close'
            elif cl == 'volume' and 'Volume' not in df.columns:
                col_map[col] = 'Volume'

        if col_map:
            df = df.rename(columns=col_map)

        return df

    # ── Asset ID Generation (VDF-compatible) ───────────────────
    @staticmethod
    def generate_ast_id(relative_path: str) -> str:
        """
        # ANCHOR:VAP_VDF_AST_ID
        Generate VDF-compatible Smart Asset ID: AST-<SHA1_10>
        """
        sha1 = hashlib.sha1(relative_path.encode('utf-8')).hexdigest()[:10].upper()
        return f"AST-{sha1}"

    # ── VDF ASSET_REGISTRY Export ──────────────────────────────
    @staticmethod
    def export_asset_registry(assets: list, output_path: str) -> str:
        """
        # ANCHOR:VAP_VDF_REGISTRY_EXPORT
        Export AutoPlot assets in VDF_ASSET_REGISTRY compatible format.
        """
        registry = []
        for asset in assets:
            registry.append({
                "AssetID": asset.get('asset_id', ''),
                "Function": asset.get('visualization_type', ''),
                "Layer": "VAP_VISUALIZATION",
                "Line": 0,
                "Type": asset.get('asset_type', 'plot'),
                "Timestamp": asset.get('generation_timestamp', ''),
            })

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(registry, f, ensure_ascii=False, indent=2)

        return output_path

    # ── VRN Anchor AST Registry Export ─────────────────────────
    @staticmethod
    def export_anchor_registry(output_path: str) -> str:
        """
        # ANCHOR:VAP_VDF_ANCHOR_EXPORT
        Export AutoPlot's anchor points for VRN integration.
        """
        registry = {
            "description": "VeritasAutoPlot Anchor AST Registry — VRN 整合定位點",
            "modules": {
                "VAP_CORE": {
                    "ast_prefix": "AST-VAP",
                    "anchors": [
                        "ANCHOR:VAP_VDF_BRIDGE_ENTRY",
                        "ANCHOR:VAP_VDF_BRIDGE_CORE",
                        "ANCHOR:VAP_VDF_DUCKDB_LOAD",
                        "ANCHOR:VAP_VDF_EXPORT_LOAD",
                        "ANCHOR:VAP_VDF_PANORAMIC_LOAD",
                        "ANCHOR:VAP_VDF_ETF_FLOW_LOAD",
                        "ANCHOR:VAP_VDF_MULTI_LOAD",
                        "ANCHOR:VAP_VDF_STANDARDIZE",
                        "ANCHOR:VAP_VDF_AST_ID",
                        "ANCHOR:VAP_VDF_REGISTRY_EXPORT",
                        "ANCHOR:VAP_VDF_ANCHOR_EXPORT",
                        "ANCHOR:VAP_PIPELINE_ENTRY",
                        "ANCHOR:VAP_PIPELINE_EXIT",
                    ],
                    "name": "VeritasAutoPlot",
                    "output_verify_from": True,
                }
            },
            "sequence": ["VAP_CORE"],
            "output_verify_modules": ["VAP_CORE"],
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(registry, f, ensure_ascii=False, indent=2)

        return output_path


class VDFFlowEngine:
    """
    # ANCHOR:VAP_VDF_FLOW_ENGINE
    ETF Fund Flow visualization engine.
    Supports dvol_ratio / INFLOW / OUTFLOW / RS_flow from VDF CentralHub LEGO v6.
    """

    @staticmethod
    def calculate_flow(df: pd.DataFrame,
                       dvol_ma_window: int = 20,
                       inflow_threshold: float = 2.0) -> pd.DataFrame:
        """Calculate fund flow indicators from raw OHLCV data."""
        df = df.copy()

        if 'Close' in df.columns and 'Volume' in df.columns:
            close_col, vol_col = 'Close', 'Volume'
        elif 'close' in df.columns and 'volume' in df.columns:
            close_col, vol_col = 'close', 'volume'
        else:
            return df

        df['dollar_vol'] = df[close_col] * df[vol_col]
        df['dvol_ma'] = df['dollar_vol'].rolling(dvol_ma_window, min_periods=5).mean()
        df['dvol_ratio'] = df['dollar_vol'] / (df['dvol_ma'] + 1e-10)

        # Daily change
        df['close_change'] = df[close_col].diff()

        # Label
        df['flow_label'] = 'NEUTRAL'
        df.loc[(df['dvol_ratio'] >= inflow_threshold) & (df['close_change'] > 0), 'flow_label'] = 'INFLOW'
        df.loc[(df['dvol_ratio'] >= inflow_threshold) & (df['close_change'] < 0), 'flow_label'] = 'OUTFLOW'

        return df

    @staticmethod
    def calculate_rs_flow(df_target: pd.DataFrame, df_base: pd.DataFrame,
                          price_col: str = 'Main_Price') -> pd.DataFrame:
        """Calculate Relative Strength flow between two assets."""
        # Align dates
        common_idx = df_target.index.intersection(df_base.index)
        target = df_target.loc[common_idx, price_col]
        base = df_base.loc[common_idx, price_col]

        target_ret = target.pct_change()
        base_ret = base.pct_change()

        rs = (target_ret + 1e-10) / (base_ret + 1e-10)

        result = pd.DataFrame({
            'RS_flow': rs,
            'Target_Ret': target_ret,
            'Base_Ret': base_ret,
        }, index=common_idx)

        return result


class VDFPanoramicVisualizer:
    """
    # ANCHOR:VAP_VDF_PANORAMIC_VIZ
    Visualize VDF PANORAMIC_DATA as AutoPlot dashboard components.
    """

    @staticmethod
    def build_panoramic_kpi(panoramic: dict) -> list:
        """Build KPI cards from PANORAMIC_DATA summary."""
        summary = panoramic.get('summary', {})
        cards = [
            {
                "label": "TOTAL FILES",
                "value": str(summary.get('TotalFiles', 0)),
                "accent": "--bl",
            },
            {
                "label": "TOTAL LINES",
                "value": f"{summary.get('TotalLines', 0):,.0f}",
                "accent": "--tl",
            },
            {
                "label": "DB HEALTH",
                "value": f"{summary.get('DBHealthScore', 0)}%",
                "accent": "--gn" if summary.get('DBHealthScore', 0) > 70 else "--am" if summary.get('DBHealthScore', 0) > 40 else "--co",
            },
            {
                "label": "ISSUES HIGH",
                "value": str(summary.get('IssueHigh', 0)),
                "accent": "--co" if summary.get('IssueHigh', 0) > 0 else "--gn",
            },
            {
                "label": "WORKFLOWS",
                "value": f"{summary.get('WorkflowsComplete', 0)}/{summary.get('WorkflowsTotal', 0)}",
                "accent": "--gn" if summary.get('WorkflowsComplete', 0) == summary.get('WorkflowsTotal', 0) else "--am",
            },
            {
                "label": "MODULES",
                "value": str(summary.get('ModuleCount', 0)),
                "accent": "--vi",
            },
        ]
        return cards

    @staticmethod
    def build_panoramic_tables(panoramic: dict) -> list:
        """Build tables from PANORAMIC_DATA."""
        tables = []

        # Modules table
        modules = panoramic.get('modules', [])
        if modules:
            rows = []
            for m in modules:
                rows.append([
                    m.get('Name', ''),
                    m.get('Role', ''),
                    str(m.get('Lines', 0)),
                    m.get('Health', ''),
                    m.get('Status', ''),
                    m.get('LastMod', ''),
                ])
            tables.append({
                "id": "panoramic_modules",
                "title": "VDF Modules",
                "headers": ["Name", "Role", "Lines", "Health", "Status", "Last Modified"],
                "rows": rows,
            })

        # Workflows table
        workflows = panoramic.get('workflows', [])
        if workflows:
            rows = []
            for w in workflows:
                rows.append([
                    w.get('ID', ''),
                    w.get('Name', ''),
                    str(w.get('Progress', 0)) + '%',
                    w.get('Status', ''),
                    w.get('FlowPath', ''),
                    w.get('Gap', ''),
                ])
            tables.append({
                "id": "panoramic_workflows",
                "title": "VDF Workflows",
                "headers": ["ID", "Name", "Progress", "Status", "Flow", "Gap"],
                "rows": rows,
            })

        return tables
