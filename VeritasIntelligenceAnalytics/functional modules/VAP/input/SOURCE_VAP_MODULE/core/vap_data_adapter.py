#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  APM-001: vap_data_adapter.py - VDF Auto-Format Data Adapter               ║
║  Module ID: APM-001 | Version: 4.0.0                                       ║
║  Reads: Parquet, CSV, TSV, Excel, DuckDB, JSON                            ║
║  Output: Standardized DataFrame with adj_close priority                    ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import os
import logging
from pathlib import Path
from typing import Optional, Union, List

import pandas as pd
import numpy as np

from vap_config import VAPPaths, resolve_ohlcv_columns, get_price_column

logger = logging.getLogger(__name__)


class VAPDataAdapter:
    """
    Unified data adapter for VeritasAutoPlot.
    Auto-detects format and normalizes to standard OHLCV DataFrame.
    Adj Close priority: if adj_close exists, 'close' column maps to it.
    """

    SUPPORTED_EXTENSIONS = {
        ".parquet": "parquet", ".pq": "parquet",
        ".csv": "csv", ".tsv": "tsv",
        ".xlsx": "excel", ".xls": "excel",
        ".duckdb": "duckdb", ".db": "duckdb",
        ".json": "json",
    }

    def __init__(self, vdf_root: Optional[Path] = None):
        self.vdf_root = vdf_root or VAPPaths.VDF_ROOT

    def auto_load(self, source: Union[str, Path], **kwargs) -> pd.DataFrame:
        """
        Auto-detect file format and load into standardized DataFrame.
        """
        source = Path(source)
        if not source.exists():
            # Try VDF root
            vdf_path = self.vdf_root / source
            if vdf_path.exists():
                source = vdf_path
            else:
                raise FileNotFoundError(f"Data source not found: {source}")

        ext = source.suffix.lower()
        fmt = self.SUPPORTED_EXTENSIONS.get(ext)
        if not fmt:
            raise ValueError(f"Unsupported format: {ext}. Supported: {list(self.SUPPORTED_EXTENSIONS.keys())}")

        logger.info(f"Loading {fmt}: {source}")

        loader = getattr(self, f"_load_{fmt}")
        df = loader(source, **kwargs)
        df = self._normalize(df)
        return df

    def _load_parquet(self, path: Path, **kwargs) -> pd.DataFrame:
        return pd.read_parquet(path, **kwargs)

    def _load_csv(self, path: Path, **kwargs) -> pd.DataFrame:
        # Auto-detect encoding
        for enc in ["utf-8", "utf-8-sig", "cp950", "big5", "gb2312", "latin1"]:
            try:
                return pd.read_csv(path, encoding=enc, **kwargs)
            except (UnicodeDecodeError, UnicodeError):
                continue
        return pd.read_csv(path, encoding="utf-8", errors="replace", **kwargs)

    def _load_tsv(self, path: Path, **kwargs) -> pd.DataFrame:
        kwargs.setdefault("sep", "\t")
        return self._load_csv(path, **kwargs)

    def _load_excel(self, path: Path, **kwargs) -> pd.DataFrame:
        return pd.read_excel(path, engine="openpyxl", **kwargs)

    def _load_duckdb(self, path: Path, table: str = None, query: str = None, **kwargs) -> pd.DataFrame:
        import duckdb
        conn = duckdb.connect(str(path), read_only=True)
        try:
            if query:
                return conn.execute(query).fetchdf()
            if table:
                return conn.execute(f"SELECT * FROM {table}").fetchdf()
            # List tables and use first one
            tables = conn.execute("SHOW TABLES").fetchdf()
            if len(tables) == 0:
                raise ValueError(f"No tables found in {path}")
            tbl = tables.iloc[0, 0]
            logger.info(f"Auto-selected table: {tbl}")
            return conn.execute(f"SELECT * FROM {tbl}").fetchdf()
        finally:
            conn.close()

    def _load_json(self, path: Path, **kwargs) -> pd.DataFrame:
        return pd.read_json(path, **kwargs)

    def _normalize(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize DataFrame:
        1. Detect and set date index
        2. Sort by date ascending
        3. Standardize column names (lowercase)
        4. Apply adj_close priority
        """
        # Lowercase columns for matching
        rename_map = {}
        for col in df.columns:
            lower = col.lower().replace(" ", "_")
            if lower != col and lower not in df.columns:
                rename_map[col] = lower

        if rename_map:
            df = df.rename(columns=rename_map)

        # Detect date column
        date_candidates = ["date", "datetime", "timestamp", "time", "trade_date", "日期"]
        for dc in date_candidates:
            if dc in df.columns:
                df[dc] = pd.to_datetime(df[dc], errors="coerce")
                df = df.set_index(dc)
                break

        if not isinstance(df.index, pd.DatetimeIndex):
            # Try parsing index as date
            try:
                df.index = pd.to_datetime(df.index)
            except Exception:
                pass

        # Sort ascending
        df = df.sort_index(ascending=True)

        # Remove pure NaN rows
        ohlcv = [c for c in ["open","high","low","close","adj_close","volume"] if c in df.columns]
        if ohlcv:
            df = df.dropna(subset=ohlcv, how="all")

        # Ensure numeric
        for col in df.columns:
            if col in ["open","high","low","close","adj_close","volume",
                       "adj_open","adj_high","adj_low"]:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        logger.info(f"Normalized: {len(df)} rows, {len(df.columns)} cols, index={type(df.index).__name__}")
        return df

    def list_vdf_sources(self) -> List[dict]:
        """List available data files in VDF root."""
        sources = []
        if not self.vdf_root.exists():
            return sources
        for ext in self.SUPPORTED_EXTENSIONS:
            for f in self.vdf_root.rglob(f"*{ext}"):
                sources.append({
                    "name": f.stem,
                    "path": str(f),
                    "format": self.SUPPORTED_EXTENSIONS[ext],
                    "size_mb": round(f.stat().st_size / 1024 / 1024, 2),
                })
        return sorted(sources, key=lambda x: x["name"])

    @staticmethod
    def generate_demo_data(ticker: str = "2330.TW", days: int = 500) -> pd.DataFrame:
        """Generate realistic demo OHLCV data for testing."""
        np.random.seed(42)
        dates = pd.bdate_range(end=pd.Timestamp.now(), periods=days)
        base_price = 600.0
        returns = np.random.normal(0.0005, 0.02, days)
        prices = base_price * np.exp(np.cumsum(returns))

        df = pd.DataFrame({
            "open":      prices * (1 + np.random.uniform(-0.01, 0.01, days)),
            "high":      prices * (1 + np.random.uniform(0.005, 0.03, days)),
            "low":       prices * (1 - np.random.uniform(0.005, 0.03, days)),
            "close":     prices,
            "adj_close": prices * 0.98,  # Simulate adj factor
            "volume":    np.random.randint(10000, 100000, days).astype(float),
        }, index=dates)
        df.index.name = "date"
        return df


if __name__ == "__main__":
    adapter = VAPDataAdapter()
    demo = adapter.generate_demo_data()
    print(f"Demo data: {demo.shape}")
    print(f"Columns: {list(demo.columns)}")
    cols = resolve_ohlcv_columns(demo)
    print(f"OHLCV mapping: {cols}")
    print(f"Close column (adj priority): {get_price_column(demo)}")
    print(demo.tail())
