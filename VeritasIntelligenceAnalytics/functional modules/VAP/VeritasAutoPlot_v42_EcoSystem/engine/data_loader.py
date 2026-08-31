"""
VeritasAutoPlot™ Data Loader Engine
====================================
Universal Adapter for CSV / Excel / Parquet / JSON
Auto-encoding detection (UTF-8 / Big5 / GBK)
Smart column mapping & price priority logic
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
import pandas as pd
import numpy as np
import json
import os
from pathlib import Path


class VeritasDataLoader:
    """Universal data loader with auto-encoding and smart column mapping."""

    ENCODING_CHAIN = ['utf-8', 'utf-8-sig', 'cp950', 'big5', 'gbk', 'latin-1']

    DATE_CANDIDATES = [
        'date', 'Date', 'DATE', 'datetime', 'Datetime',
        'time', 'Time', 'timestamp', 'Timestamp',
        '日期', '時間', 'trade_date', 'TradeDate'
    ]

    PRICE_PRIORITY = [
        'Adj Close', 'adj close', 'Adj_Close', 'adj_close',
        'Close', 'close', 'CLOSE', '收盤價', '收盤',
        'Price', 'price', 'Value', 'value', 'Last'
    ]

    def __init__(self):
        self.load_log = []

    def load(self, filepath: str) -> pd.DataFrame:
        """
        Main entry point. Loads any supported file format.
        Returns a standardized DataFrame with DatetimeIndex and Main_Price column.
        """
        filepath = str(filepath)
        ext = Path(filepath).suffix.lower()

        loaders = {
            '.csv':     self._load_csv,
            '.tsv':     self._load_tsv,
            '.xlsx':    self._load_excel,
            '.xls':     self._load_excel,
            '.parquet': self._load_parquet,
            '.json':    self._load_json,
        }

        loader = loaders.get(ext)
        if loader is None:
            raise ValueError(f"Unsupported file format: {ext}")

        df = loader(filepath)
        self.load_log.append(f"Loaded {filepath} ({ext}): {len(df)} rows, {len(df.columns)} cols")

        # Standardize
        df = self._standardize_date_index(df)
        df = self._standardize_price(df)

        return df

    # ── CSV with auto-encoding ──────────────────────────────────
    def _load_csv(self, filepath: str) -> pd.DataFrame:
        for enc in self.ENCODING_CHAIN:
            try:
                df = pd.read_csv(filepath, encoding=enc)
                self.load_log.append(f"  CSV encoding detected: {enc}")
                return df
            except (UnicodeDecodeError, UnicodeError):
                continue
        raise ValueError(f"Cannot decode CSV: {filepath}")

    def _load_tsv(self, filepath: str) -> pd.DataFrame:
        for enc in self.ENCODING_CHAIN:
            try:
                df = pd.read_csv(filepath, encoding=enc, sep='\t')
                return df
            except (UnicodeDecodeError, UnicodeError):
                continue
        raise ValueError(f"Cannot decode TSV: {filepath}")

    # ── Excel ───────────────────────────────────────────────────
    def _load_excel(self, filepath: str) -> pd.DataFrame:
        return pd.read_excel(filepath)

    # ── Parquet ─────────────────────────────────────────────────
    def _load_parquet(self, filepath: str) -> pd.DataFrame:
        return pd.read_parquet(filepath)

    # ── JSON ────────────────────────────────────────────────────
    def _load_json(self, filepath: str) -> pd.DataFrame:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, list):
            return pd.DataFrame(data)
        elif isinstance(data, dict):
            # Try common structures
            for key in ['data', 'records', 'results', 'rows']:
                if key in data and isinstance(data[key], list):
                    return pd.DataFrame(data[key])
            return pd.DataFrame(data)
        raise ValueError("Unrecognized JSON structure")

    # ── Standardization ─────────────────────────────────────────
    def _standardize_date_index(self, df: pd.DataFrame) -> pd.DataFrame:
        """Detect date column and set as DatetimeIndex."""
        # Already has datetime index
        if isinstance(df.index, pd.DatetimeIndex):
            return df.sort_index()

        # Search for date column
        for col_name in self.DATE_CANDIDATES:
            if col_name in df.columns:
                try:
                    df[col_name] = pd.to_datetime(df[col_name])
                    df = df.set_index(col_name).sort_index()
                    self.load_log.append(f"  Date column: {col_name}")
                    return df
                except Exception:
                    continue

        # Try first column if it looks like dates
        first_col = df.columns[0]
        try:
            test = pd.to_datetime(df[first_col].head(10))
            if test.notna().sum() >= 5:
                df[first_col] = pd.to_datetime(df[first_col])
                df = df.set_index(first_col).sort_index()
                self.load_log.append(f"  Date column (auto-detected): {first_col}")
                return df
        except Exception:
            pass

        self.load_log.append("  WARNING: No date column detected, using integer index")
        return df

    def _standardize_price(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply price priority logic: Adj Close > Close > first numeric."""
        cols_lower = {c.lower().strip(): c for c in df.columns}

        for candidate in self.PRICE_PRIORITY:
            key = candidate.lower().strip()
            if key in cols_lower:
                actual_col = cols_lower[key]
                df['Main_Price'] = pd.to_numeric(df[actual_col], errors='coerce')
                self.load_log.append(f"  Price column: {actual_col} → Main_Price")
                return df

        # Fallback: first numeric column
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            df['Main_Price'] = df[numeric_cols[0]]
            self.load_log.append(f"  Price column (fallback): {numeric_cols[0]} → Main_Price")

        return df


class VeritasDataProfiler:
    """Automatic data profiling for the Auto Analysis Engine."""

    @staticmethod
    def profile(df: pd.DataFrame) -> dict:
        """Generate a data profile summary."""
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        non_numeric = [c for c in df.columns if c not in numeric_cols]

        # Detect frequency
        freq = "unknown"
        if isinstance(df.index, pd.DatetimeIndex) and len(df) > 2:
            diffs = df.index.to_series().diff().dropna()
            median_days = diffs.dt.days.median()
            if median_days <= 1:
                freq = "daily"
            elif median_days <= 7:
                freq = "weekly"
            elif median_days <= 35:
                freq = "monthly"
            elif median_days <= 100:
                freq = "quarterly"
            else:
                freq = "yearly"

        profile = {
            "rows": len(df),
            "columns": len(df.columns),
            "numeric_columns": numeric_cols,
            "non_numeric_columns": non_numeric,
            "frequency": freq,
            "date_range": {
                "start": str(df.index.min()) if isinstance(df.index, pd.DatetimeIndex) else None,
                "end": str(df.index.max()) if isinstance(df.index, pd.DatetimeIndex) else None,
            },
            "missing_values": df.isnull().sum().to_dict(),
            "has_ohlc": all(
                any(c.lower() == name for c in df.columns)
                for name in ['open', 'high', 'low', 'close']
            ),
            "has_volume": any('vol' in c.lower() for c in df.columns),
        }

        return profile
