"""
VeritasAutoPlot™ VDF Connector Module
========================================
# ANCHOR:VAP_VDF_CONNECTOR_ENTRY

Complete data pipeline connector between VDF (VeritasDataForge) and AutoPlot.

Supports:
- VDF M01 BatchDownloader output: ohlcv_{ts}.parquet / .csv / DuckDB
- VDF CentralHub LEGO v6 output: {table}__{CAT}__{start}__{end}__{ts}.parquet/.csv
- VDF M02 AKShare/FRED Macro output: akshare_fred_macro.duckdb / csv / parquet
- Google Sheet public/shared URL read
- Auto-scan VDF output directory tree
- Smart file matching by ticker / table / date range
- Multi-DuckDB cross-query (M01 + M02 + LEGO v6)

Architecture:
  [ANCHOR:VAP_VDF_CONNECTOR_CORE]     VDFConnector — 主連接器
  [ANCHOR:VAP_VDF_SCANNER]            VDFOutputScanner — 自動掃描 VDF 輸出目錄
  [ANCHOR:VAP_VDF_GSHEET]             GSheetConnector — Google Sheet 讀取
  [ANCHOR:VAP_VDF_MULTI_DB]           MultiDBLoader — 多 DuckDB 跨庫查詢
  [ANCHOR:VAP_VDF_NAMING]             VDFNamingParser — VDF 檔名解析
  [ANCHOR:VAP_VDF_MACRO_BRIDGE]       MacroBridge — M02 宏觀經濟資料橋接
"""

import os
import re
import json
import glob
import hashlib
import datetime
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union


# ============================================================
# [ANCHOR:VAP_VDF_NAMING] VDF Export Filename Parser
# ============================================================

class VDFNamingParser:
    """
    Parse VDF export filenames to extract metadata.

    VDF naming conventions:
    - M01: ohlcv_{ts}.{ext}
    - LEGO v6: {table}__{category}__{start}__{end}__{ts}.{ext}
    - M02: {indicator}_{ts}.{ext}
    """

    # M01 pattern: ohlcv_20260319_151527.parquet
    M01_PATTERN = re.compile(
        r'^ohlcv_(\d{8}_\d{6})\.(csv|parquet|json)$', re.IGNORECASE
    )

    # LEGO v6 pattern: etf_daily__DEFAULT__2025-01-01__latest__20260319_151527.parquet
    LEGO_PATTERN = re.compile(
        r'^(\w+)__(\w+)__(\d{4}-\d{2}-\d{2})__(\w+)__(\d{8}_\d{6})\.(csv|parquet|json)$',
        re.IGNORECASE
    )

    # M02 pattern: akshare_fred_{region}_{ts}.parquet
    M02_PATTERN = re.compile(
        r'^(akshare_fred_\w+)_(\d{8}_\d{6})\.(csv|parquet|json)$', re.IGNORECASE
    )

    # DuckDB files
    DUCKDB_PATTERN = re.compile(r'^.*\.duckdb$', re.IGNORECASE)

    # VDF Schema table names (from CentralHub LEGO v6)
    VDF_TABLES = {
        'index_intl', 'stock_intl', 'etf_daily', 'fx_daily',
        'commodity_daily', 'rate_daily', 'crypto_daily', 'etf_flow_daily',
    }

    # M01 category mapping
    M01_CATEGORIES = {
        'TW_STOCKS', 'TW_INDICES', 'TW_ETFS',
        'US_STOCKS', 'US_INDICES', 'US_ETFS',
        'FOREX', 'CRYPTO', 'COMMODITIES', 'BONDS',
        'VOLATILITY', 'FUTURES', 'REITS',
    }

    @classmethod
    def parse(cls, filename: str) -> Optional[Dict[str, Any]]:
        """Parse a VDF export filename and return metadata."""
        name = Path(filename).name

        # Try LEGO v6 pattern first (most specific)
        m = cls.LEGO_PATTERN.match(name)
        if m:
            return {
                'source': 'LEGO_v6',
                'table': m.group(1),
                'category': m.group(2),
                'start_date': m.group(3),
                'end_date': m.group(4),
                'timestamp': m.group(5),
                'format': m.group(6).lower(),
                'is_vdf_table': m.group(1) in cls.VDF_TABLES,
            }

        # Try M01 pattern
        m = cls.M01_PATTERN.match(name)
        if m:
            return {
                'source': 'M01_BatchDownloader',
                'table': 'ohlcv_daily',
                'category': 'ALL',
                'timestamp': m.group(1),
                'format': m.group(2).lower(),
            }

        # Try M02 pattern
        m = cls.M02_PATTERN.match(name)
        if m:
            return {
                'source': 'M02_AKShareFRED',
                'table': m.group(1),
                'timestamp': m.group(2),
                'format': m.group(3).lower(),
            }

        # DuckDB
        if cls.DUCKDB_PATTERN.match(name):
            db_type = 'unknown'
            nl = name.lower()
            if 'intl_v6' in nl:
                db_type = 'LEGO_v6'
            elif 'batch_download' in nl:
                db_type = 'M01_BatchDownloader'
            elif 'akshare' in nl or 'fred' in nl or 'macro' in nl:
                db_type = 'M02_AKShareFRED'
            return {
                'source': db_type,
                'table': 'duckdb',
                'format': 'duckdb',
                'filename': name,
            }

        # Generic parquet/csv with VDF table name in filename
        ext = Path(name).suffix.lower().lstrip('.')
        if ext in ('csv', 'parquet', 'json'):
            stem = Path(name).stem.lower()
            for tbl in cls.VDF_TABLES:
                if tbl in stem:
                    return {
                        'source': 'VDF_generic',
                        'table': tbl,
                        'format': ext,
                    }
            # Check for M01 category keywords
            if 'ohlcv' in stem:
                return {
                    'source': 'M01_BatchDownloader',
                    'table': 'ohlcv_daily',
                    'format': ext,
                }

        return None


# ============================================================
# [ANCHOR:VAP_VDF_SCANNER] VDF Output Directory Scanner
# ============================================================

class VDFOutputScanner:
    """
    Auto-scan VDF output directory tree to discover all available data files.

    Expected VDF directory structure:
    C:\\VeritasIntelligenceAnalytics\\VeritasDataForge\\
    ├── output/
    │   ├── VDF_CentralHub_LEGO_v6/
    │   │   ├── intl_v6.duckdb
    │   │   ├── etf_daily__DEFAULT__2025-01-01__latest__*.parquet
    │   │   └── ...
    │   ├── csv/
    │   │   └── ohlcv_*.csv
    │   ├── parquet/
    │   │   └── ohlcv_*.parquet
    │   └── json/
    │       └── ohlcv_*.json
    ├── VDF_M02/
    │   ├── akshare_fred_macro.duckdb
    │   ├── csv/
    │   ├── parquet/
    │   └── json/
    └── logs/
    """

    # Default VDF base paths (Windows paths mapped to cross-platform)
    DEFAULT_VDF_BASES = [
        r"C:\VeritasIntelligenceAnalytics\VeritasDataForge",
        r"C:\VeritasIntelligenceAnalytics\VeritasDataForge\output",
        r"C:\VeritasIntelligenceAnalytics\VeritasDataForge\output\VDF_CentralHub_LEGO_v6",
    ]

    SCAN_EXTENSIONS = {'.csv', '.parquet', '.json', '.duckdb'}

    def __init__(self, base_dirs: List[str] = None):
        self.base_dirs = base_dirs or []
        self._catalog = []

    def scan(self, base_dir: str = None, recursive: bool = True) -> List[Dict]:
        """
        Scan a directory for VDF output files.
        Returns a catalog of discovered files with parsed metadata.
        """
        if base_dir:
            dirs_to_scan = [base_dir]
        elif self.base_dirs:
            dirs_to_scan = self.base_dirs
        else:
            dirs_to_scan = self.DEFAULT_VDF_BASES

        catalog = []

        for d in dirs_to_scan:
            d = str(d)
            if not os.path.isdir(d):
                continue

            pattern = '**/*' if recursive else '*'
            for filepath in Path(d).glob(pattern):
                if not filepath.is_file():
                    continue
                if filepath.suffix.lower() not in self.SCAN_EXTENSIONS:
                    continue

                meta = VDFNamingParser.parse(filepath.name)
                if meta is None:
                    # Still record unknown files for manual inspection
                    meta = {
                        'source': 'unknown',
                        'table': 'unknown',
                        'format': filepath.suffix.lower().lstrip('.'),
                    }

                meta['filepath'] = str(filepath)
                meta['filesize'] = filepath.stat().st_size
                meta['modified'] = datetime.datetime.fromtimestamp(
                    filepath.stat().st_mtime
                ).strftime('%Y-%m-%d %H:%M:%S')

                catalog.append(meta)

        # Sort by modification time (newest first)
        catalog.sort(key=lambda x: x.get('modified', ''), reverse=True)
        self._catalog = catalog
        return catalog

    def get_latest(self, table: str = None, source: str = None,
                   fmt: str = None) -> Optional[Dict]:
        """Get the latest file matching criteria."""
        for item in self._catalog:
            if table and item.get('table') != table:
                continue
            if source and item.get('source') != source:
                continue
            if fmt and item.get('format') != fmt:
                continue
            return item
        return None

    def get_all(self, table: str = None, source: str = None,
                fmt: str = None) -> List[Dict]:
        """Get all files matching criteria."""
        results = []
        for item in self._catalog:
            if table and item.get('table') != table:
                continue
            if source and item.get('source') != source:
                continue
            if fmt and item.get('format') != fmt:
                continue
            results.append(item)
        return results

    def get_duckdb_files(self) -> List[Dict]:
        """Get all discovered DuckDB files."""
        return [item for item in self._catalog if item.get('format') == 'duckdb']

    def get_summary(self) -> Dict:
        """Get scan summary statistics."""
        sources = {}
        formats = {}
        tables = {}
        total_size = 0

        for item in self._catalog:
            src = item.get('source', 'unknown')
            fmt = item.get('format', 'unknown')
            tbl = item.get('table', 'unknown')

            sources[src] = sources.get(src, 0) + 1
            formats[fmt] = formats.get(fmt, 0) + 1
            tables[tbl] = tables.get(tbl, 0) + 1
            total_size += item.get('filesize', 0)

        return {
            'total_files': len(self._catalog),
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'by_source': sources,
            'by_format': formats,
            'by_table': tables,
        }


# ============================================================
# [ANCHOR:VAP_VDF_GSHEET] Google Sheet Connector
# ============================================================

class GSheetConnector:
    """
    Read data from Google Sheets (public or shared with link).

    Supports:
    - Public Google Sheet URL → CSV export → pandas DataFrame
    - Sheet ID + GID extraction
    - Multi-sheet reading
    - Auto-retry with timeout
    """

    GSHEET_URL_PATTERN = re.compile(
        r'https://docs\.google\.com/spreadsheets/d/([a-zA-Z0-9_-]+)(?:/edit.*gid=(\d+))?'
    )

    @classmethod
    def parse_url(cls, url: str) -> Tuple[Optional[str], Optional[str]]:
        """Extract sheet_id and gid from a Google Sheet URL."""
        m = cls.GSHEET_URL_PATTERN.search(url)
        if m:
            return m.group(1), m.group(2)
        return None, None

    @classmethod
    def build_csv_url(cls, sheet_id: str, gid: str = None) -> str:
        """Build the CSV export URL for a Google Sheet."""
        base = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
        if gid:
            base += f"&gid={gid}"
        return base

    @classmethod
    def read(cls, url_or_id: str, gid: str = None,
             sheet_name: str = None,
             timeout: int = 30,
             retries: int = 3) -> pd.DataFrame:
        """
        Read a Google Sheet as a pandas DataFrame.

        Args:
            url_or_id: Full Google Sheet URL or just the sheet ID
            gid: Sheet GID (tab number, 0-indexed)
            sheet_name: Not used for CSV export, kept for API compatibility
            timeout: Request timeout in seconds
            retries: Number of retry attempts

        Returns:
            pd.DataFrame
        """
        import io

        # Parse URL if full URL provided
        if 'docs.google.com' in url_or_id:
            sheet_id, parsed_gid = cls.parse_url(url_or_id)
            if sheet_id is None:
                raise ValueError(f"Cannot parse Google Sheet URL: {url_or_id}")
            if gid is None:
                gid = parsed_gid
        else:
            sheet_id = url_or_id

        csv_url = cls.build_csv_url(sheet_id, gid)

        # Try reading with retries
        last_error = None
        for attempt in range(retries):
            try:
                df = pd.read_csv(csv_url, encoding='utf-8')
                return df
            except Exception as e:
                last_error = e
                if attempt < retries - 1:
                    import time
                    time.sleep(2 ** attempt)  # Exponential backoff

        raise ConnectionError(
            f"Failed to read Google Sheet after {retries} attempts: {last_error}"
        )

    @classmethod
    def read_all_sheets(cls, url_or_id: str,
                        gids: List[str] = None,
                        timeout: int = 30) -> Dict[str, pd.DataFrame]:
        """
        Read multiple sheets from the same Google Spreadsheet.

        Args:
            url_or_id: Full URL or sheet ID
            gids: List of GIDs to read. If None, reads gid=0 only.

        Returns:
            Dict of {gid: DataFrame}
        """
        if gids is None:
            gids = ['0']

        results = {}
        for gid in gids:
            try:
                df = cls.read(url_or_id, gid=gid, timeout=timeout)
                results[gid] = df
            except Exception as e:
                results[gid] = pd.DataFrame()  # Empty on error

        return results


# ============================================================
# [ANCHOR:VAP_VDF_MULTI_DB] Multi-DuckDB Cross-Query Loader
# ============================================================

class MultiDBLoader:
    """
    Load data from multiple VDF DuckDB databases.

    Supports:
    - intl_v6.duckdb (LEGO v6: 8 tables)
    - batch_download.duckdb (M01: ohlcv_daily)
    - akshare_fred_macro.duckdb (M02: macro tables)
    """

    def __init__(self):
        self._duckdb = None
        try:
            import duckdb
            self._duckdb = duckdb
        except ImportError:
            pass

    def is_available(self) -> bool:
        return self._duckdb is not None

    def list_tables(self, db_path: str) -> List[str]:
        """List all tables in a DuckDB file."""
        if not self.is_available():
            return []
        try:
            con = self._duckdb.connect(db_path, read_only=True)
            tables = con.execute("SHOW TABLES").fetchall()
            con.close()
            return [t[0] for t in tables]
        except Exception:
            return []

    def table_info(self, db_path: str, table: str) -> Dict:
        """Get table schema and row count."""
        if not self.is_available():
            return {}
        try:
            con = self._duckdb.connect(db_path, read_only=True)
            # Column info
            cols = con.execute(f"PRAGMA table_info('{table}')").fetchall()
            # Row count
            count = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            con.close()
            return {
                'table': table,
                'columns': [{'name': c[1], 'type': c[2]} for c in cols],
                'row_count': count,
            }
        except Exception as e:
            return {'error': str(e)}

    def query(self, db_path: str, sql: str) -> pd.DataFrame:
        """Execute arbitrary SQL on a DuckDB file."""
        if not self.is_available():
            raise ImportError("duckdb not installed")
        con = self._duckdb.connect(db_path, read_only=True)
        df = con.execute(sql).fetchdf()
        con.close()
        return df

    def load_table(self, db_path: str, table: str,
                   ticker: str = None, ticker_col: str = 'ticker',
                   start_date: str = None, end_date: str = None,
                   date_col: str = 'date',
                   limit: int = None) -> pd.DataFrame:
        """Load a table with optional filtering."""
        if not self.is_available():
            raise ImportError("duckdb not installed")

        sql = f"SELECT * FROM {table}"
        conditions = []

        if ticker:
            conditions.append(f"{ticker_col} = '{ticker}'")
        if start_date:
            conditions.append(f"{date_col} >= '{start_date}'")
        if end_date:
            conditions.append(f"{date_col} <= '{end_date}'")

        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        sql += f" ORDER BY {date_col}"
        if limit:
            sql += f" LIMIT {limit}"

        con = self._duckdb.connect(db_path, read_only=True)
        df = con.execute(sql).fetchdf()
        con.close()
        return df

    def load_m01_ohlcv(self, db_path: str, ticker: str = None,
                       category: str = None,
                       start_date: str = None,
                       end_date: str = None) -> pd.DataFrame:
        """Load from M01 BatchDownloader DuckDB (ohlcv_daily table)."""
        sql = "SELECT * FROM ohlcv_daily"
        conditions = []

        if ticker:
            conditions.append(f"ticker = '{ticker}'")
        if category:
            conditions.append(f"category = '{category}'")
        if start_date:
            conditions.append(f"date >= '{start_date}'")
        if end_date:
            conditions.append(f"date <= '{end_date}'")

        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        sql += " ORDER BY date"

        return self.query(db_path, sql)

    def load_m02_macro(self, db_path: str, table: str = None,
                       region: str = None,
                       indicator: str = None) -> pd.DataFrame:
        """Load from M02 AKShare/FRED DuckDB."""
        if table is None:
            # Auto-detect: try common M02 table names
            tables = self.list_tables(db_path)
            macro_tables = [t for t in tables if 'macro' in t.lower()]
            if not macro_tables:
                raise ValueError(f"No macro tables found in {db_path}. Tables: {tables}")
            table = macro_tables[0]

        sql = f"SELECT * FROM {table}"
        conditions = []

        if region:
            conditions.append(f"region = '{region}'")
        if indicator:
            conditions.append(f"indicator_key = '{indicator}'")

        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        sql += " ORDER BY date"

        return self.query(db_path, sql)

    def cross_query(self, db_paths: Dict[str, str], sql: str) -> pd.DataFrame:
        """
        Execute a cross-database query by attaching multiple DuckDB files.

        Args:
            db_paths: Dict of {alias: filepath}
            sql: SQL query using aliases (e.g., "SELECT * FROM m01.ohlcv_daily")
        """
        if not self.is_available():
            raise ImportError("duckdb not installed")

        con = self._duckdb.connect(':memory:')
        try:
            for alias, path in db_paths.items():
                con.execute(f"ATTACH '{path}' AS {alias} (READ_ONLY)")
            df = con.execute(sql).fetchdf()
        finally:
            con.close()
        return df


# ============================================================
# [ANCHOR:VAP_VDF_MACRO_BRIDGE] M02 Macro Data Bridge
# ============================================================

class MacroBridge:
    """
    Bridge M02 AKShare/FRED macro data to AutoPlot visualization.

    Supports:
    - 5-region macro indicators (US/EU/CN/JP/TW)
    - PMI cross-country comparison
    - Sentiment indicators (VIX, Yield Spread, etc.)
    - FRED time series
    """

    # Region → indicator mapping (from M02 Config)
    REGIONS = {
        'US': {
            'label': '美國', 'flag': '🇺🇸',
            'key_indicators': ['us_cpi', 'us_gdp', 'us_unemployment', 'us_interest',
                               'us_ism_pmi', 'us_nonfarm', 'us_retail_sales'],
        },
        'EU': {
            'label': '歐元區', 'flag': '🇪🇺',
            'key_indicators': ['eu_cpi', 'eu_gdp', 'eu_unemployment', 'eu_interest',
                               'eu_pmi_mfg', 'eu_pmi_svc'],
        },
        'CN': {
            'label': '中國', 'flag': '🇨🇳',
            'key_indicators': ['cn_cpi', 'cn_gdp', 'cn_pmi_mfg', 'cn_interest',
                               'cn_m2', 'cn_industrial'],
        },
        'JP': {
            'label': '日本', 'flag': '🇯🇵',
            'key_indicators': ['jp_cpi', 'jp_gdp', 'jp_unemployment', 'jp_interest'],
        },
        'TW': {
            'label': '台灣', 'flag': '🇹🇼',
            'key_indicators': ['tw_cpi', 'tw_gdp', 'tw_unemployment', 'tw_interest',
                               'tw_exports', 'tw_imports'],
        },
    }

    SENTIMENT_INDICATORS = {
        'vix': {'label': 'VIX 恐慌指數', 'fred': 'VIXCLS'},
        'yield_spread': {'label': '10Y-2Y 殖利率利差', 'fred': 'T10Y2Y'},
        'ted_spread': {'label': 'TED 利差', 'fred': 'TEDRATE'},
        'financial_stress': {'label': '金融壓力指數', 'fred': 'STLFSI2'},
        'breakeven_5y': {'label': '5Y 通膨預期', 'fred': 'T5YIE'},
    }

    @classmethod
    def load_macro_from_parquet(cls, filepath: str,
                                region: str = None) -> pd.DataFrame:
        """Load M02 macro data from Parquet/CSV export."""
        ext = Path(filepath).suffix.lower()
        if ext == '.parquet':
            df = pd.read_parquet(filepath)
        elif ext == '.csv':
            df = pd.read_csv(filepath, encoding='utf-8-sig')
        else:
            raise ValueError(f"Unsupported format: {ext}")

        if region and 'region' in df.columns:
            df = df[df['region'] == region]

        # Standardize date
        for col in ['date', 'Date', 'datetime', 'period']:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
                df = df.set_index(col).sort_index()
                break

        return df

    @classmethod
    def build_macro_comparison(cls, data: Dict[str, pd.DataFrame],
                                indicator: str) -> pd.DataFrame:
        """
        Build a cross-region comparison DataFrame for a specific indicator.

        Args:
            data: Dict of {region: DataFrame}
            indicator: Indicator column name

        Returns:
            DataFrame with regions as columns, date as index
        """
        frames = {}
        for region, df in data.items():
            if indicator in df.columns:
                frames[region] = df[indicator]
            elif 'value' in df.columns:
                frames[region] = df['value']

        if not frames:
            return pd.DataFrame()

        return pd.DataFrame(frames)


# ============================================================
# [ANCHOR:VAP_VDF_CONNECTOR_CORE] Main VDF Connector
# ============================================================

class VDFConnector:
    """
    Main connector class that orchestrates all VDF data sources.

    Usage:
        connector = VDFConnector(vdf_base="C:\\VeritasIntelligenceAnalytics\\VeritasDataForge")
        connector.scan()  # Auto-discover all VDF outputs

        # Load specific data
        df = connector.load_ticker("NVDA", source="M01")
        df = connector.load_table("etf_daily", ticker="SMH")
        df = connector.load_macro(region="US")
        df = connector.load_gsheet("https://docs.google.com/spreadsheets/d/...")

        # Get catalog
        catalog = connector.get_catalog()
        summary = connector.get_summary()
    """

    def __init__(self, vdf_base: str = None,
                 extra_dirs: List[str] = None,
                 gsheet_urls: List[str] = None):
        """
        Initialize VDF Connector.

        Args:
            vdf_base: VDF base directory (e.g., C:\\VeritasIntelligenceAnalytics\\VeritasDataForge)
            extra_dirs: Additional directories to scan
            gsheet_urls: Google Sheet URLs to register
        """
        self.vdf_base = vdf_base
        self.extra_dirs = extra_dirs or []
        self.gsheet_urls = gsheet_urls or []

        self.scanner = VDFOutputScanner()
        self.gsheet = GSheetConnector()
        self.multi_db = MultiDBLoader()
        self.macro = MacroBridge()
        self.naming = VDFNamingParser()

        self._catalog = []
        self._db_registry = {}  # {alias: db_path}
        self._gsheet_cache = {}

    def scan(self, base_dir: str = None) -> Dict:
        """
        Scan VDF output directories and build catalog.
        Returns scan summary.
        """
        scan_dir = base_dir or self.vdf_base

        # Build list of directories to scan
        dirs = []
        if scan_dir:
            dirs.append(scan_dir)
            # Also scan common subdirectories
            for sub in ['output', 'csv', 'parquet', 'json',
                        'output/VDF_CentralHub_LEGO_v6',
                        'VDF_M02', 'VDF_M02/csv', 'VDF_M02/parquet']:
                subdir = os.path.join(scan_dir, sub)
                if os.path.isdir(subdir):
                    dirs.append(subdir)

        for d in self.extra_dirs:
            if os.path.isdir(d):
                dirs.append(d)

        self.scanner.base_dirs = dirs
        self._catalog = self.scanner.scan()

        # Auto-register DuckDB files
        for db_info in self.scanner.get_duckdb_files():
            db_path = db_info['filepath']
            source = db_info.get('source', 'unknown')
            alias = source.lower().replace(' ', '_')
            self._db_registry[alias] = db_path

        return self.scanner.get_summary()

    def get_catalog(self) -> List[Dict]:
        """Get the full file catalog."""
        return self._catalog

    def get_summary(self) -> Dict:
        """Get scan summary."""
        summary = self.scanner.get_summary()
        summary['duckdb_databases'] = self._db_registry
        summary['gsheet_urls'] = self.gsheet_urls
        return summary

    # ── Load by Ticker ─────────────────────────────────────────
    def load_ticker(self, ticker: str,
                    source: str = None,
                    table: str = None,
                    start_date: str = None,
                    end_date: str = None,
                    prefer_format: str = 'parquet') -> pd.DataFrame:
        """
        Load data for a specific ticker from the best available source.

        Priority: DuckDB → Parquet → CSV → JSON

        Args:
            ticker: Ticker symbol (e.g., "NVDA", "2330.TW", "SMH")
            source: Force specific source ("M01", "LEGO_v6", etc.)
            table: Force specific table
            start_date: Filter start date
            end_date: Filter end date
            prefer_format: Preferred file format
        """
        # Strategy 1: Try DuckDB first (fastest)
        for alias, db_path in self._db_registry.items():
            if source and source.lower() not in alias:
                continue
            try:
                tables = self.multi_db.list_tables(db_path)
                for tbl in tables:
                    if table and tbl != table:
                        continue
                    # Detect ticker column
                    info = self.multi_db.table_info(db_path, tbl)
                    col_names = [c['name'] for c in info.get('columns', [])]
                    ticker_col = 'ticker'
                    if 'symbol' in col_names:
                        ticker_col = 'symbol'
                    elif 'pair' in col_names:
                        ticker_col = 'pair'

                    if ticker_col not in col_names:
                        continue

                    df = self.multi_db.load_table(
                        db_path, tbl, ticker=ticker, ticker_col=ticker_col,
                        start_date=start_date, end_date=end_date
                    )
                    if len(df) > 0:
                        return self._standardize(df)
            except Exception:
                continue

        # Strategy 2: Try Parquet/CSV files
        for fmt in [prefer_format, 'parquet', 'csv', 'json']:
            files = self.scanner.get_all(table=table, fmt=fmt)
            if not files and table is None:
                files = self.scanner.get_all(fmt=fmt)

            for f_info in files:
                try:
                    filepath = f_info['filepath']
                    df = self._load_file(filepath)
                    # Filter by ticker
                    for col in ['ticker', 'symbol', 'pair', 'Ticker', 'Symbol']:
                        if col in df.columns:
                            filtered = df[df[col] == ticker]
                            if len(filtered) > 0:
                                return self._standardize(filtered)
                except Exception:
                    continue

        return pd.DataFrame()  # Empty if not found

    # ── Load by Table ──────────────────────────────────────────
    def load_table(self, table: str,
                   ticker: str = None,
                   start_date: str = None,
                   end_date: str = None) -> pd.DataFrame:
        """Load an entire VDF table."""
        # Try DuckDB first
        for alias, db_path in self._db_registry.items():
            try:
                tables = self.multi_db.list_tables(db_path)
                if table in tables:
                    # Detect ticker column from VDF schema
                    schema = VDFNamingParser.VDF_TABLES
                    ticker_col = 'ticker'
                    if table == 'fx_daily':
                        ticker_col = 'pair'
                    elif table == 'crypto_daily':
                        ticker_col = 'symbol'

                    df = self.multi_db.load_table(
                        db_path, table, ticker=ticker, ticker_col=ticker_col,
                        start_date=start_date, end_date=end_date
                    )
                    if len(df) > 0:
                        return self._standardize(df)
            except Exception:
                continue

        # Try files
        files = self.scanner.get_all(table=table)
        if files:
            filepath = files[0]['filepath']
            df = self._load_file(filepath)
            if ticker:
                for col in ['ticker', 'symbol', 'pair']:
                    if col in df.columns:
                        df = df[df[col] == ticker]
                        break
            return self._standardize(df)

        return pd.DataFrame()

    # ── Load Macro Data ────────────────────────────────────────
    def load_macro(self, region: str = None,
                   indicator: str = None,
                   source_db: str = None) -> pd.DataFrame:
        """Load M02 macro data."""
        # Try M02 DuckDB
        for alias, db_path in self._db_registry.items():
            if 'm02' in alias or 'akshare' in alias or 'macro' in alias:
                try:
                    return self.multi_db.load_m02_macro(
                        db_path, region=region, indicator=indicator
                    )
                except Exception:
                    continue

        # Try Parquet/CSV files
        files = self.scanner.get_all(source='M02_AKShareFRED')
        for f_info in files:
            try:
                df = self.macro.load_macro_from_parquet(
                    f_info['filepath'], region=region
                )
                if len(df) > 0:
                    return df
            except Exception:
                continue

        return pd.DataFrame()

    # ── Load Google Sheet ──────────────────────────────────────
    def load_gsheet(self, url: str, gid: str = None) -> pd.DataFrame:
        """Load data from a Google Sheet URL."""
        cache_key = f"{url}_{gid}"
        if cache_key in self._gsheet_cache:
            return self._gsheet_cache[cache_key]

        df = self.gsheet.read(url, gid=gid)
        df = self._standardize(df)
        self._gsheet_cache[cache_key] = df
        return df

    # ── Load from File Path ────────────────────────────────────
    def load_file(self, filepath: str, ticker: str = None) -> pd.DataFrame:
        """Load from a specific file path (Parquet/CSV/JSON)."""
        df = self._load_file(filepath)
        if ticker:
            for col in ['ticker', 'symbol', 'pair', 'Ticker', 'Symbol']:
                if col in df.columns:
                    filtered = df[df[col] == ticker]
                    if len(filtered) > 0:
                        return self._standardize(filtered)
        return self._standardize(df)

    # ── Internal Helpers ───────────────────────────────────────
    def _load_file(self, filepath: str) -> pd.DataFrame:
        """Load any supported file format."""
        ext = Path(filepath).suffix.lower()
        if ext == '.parquet':
            return pd.read_parquet(filepath)
        elif ext == '.csv':
            # Try multiple encodings (VDF uses utf-8-sig)
            for enc in ['utf-8-sig', 'utf-8', 'cp950', 'big5', 'latin-1']:
                try:
                    return pd.read_csv(filepath, encoding=enc)
                except (UnicodeDecodeError, UnicodeError):
                    continue
            raise ValueError(f"Cannot decode: {filepath}")
        elif ext == '.json':
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, list):
                return pd.DataFrame(data)
            elif isinstance(data, dict):
                for key in ['data', 'records', 'results', 'rows']:
                    if key in data and isinstance(data[key], list):
                        return pd.DataFrame(data[key])
                return pd.DataFrame(data)
        raise ValueError(f"Unsupported format: {ext}")

    def _standardize(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize DataFrame for AutoPlot consumption."""
        if df.empty:
            return df

        df = df.copy()

        # Date index
        date_cols = ['date', 'Date', 'DATE', 'datetime', 'Datetime', 'trade_date']
        for col in date_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
                df = df.set_index(col).sort_index()
                break

        # Price mapping
        price_priority = [
            'adj_close', 'Adj Close', 'Adj_Close',
            'close', 'Close', 'CLOSE',
            'Main_Price', 'price', 'Price', 'value', 'Value',
        ]
        if 'Main_Price' not in df.columns:
            for col in price_priority:
                if col in df.columns:
                    df['Main_Price'] = pd.to_numeric(df[col], errors='coerce')
                    break

        # OHLC standardization
        col_map = {}
        for c in df.columns:
            cl = c.lower().strip()
            if cl == 'open' and 'Open' not in df.columns:
                col_map[c] = 'Open'
            elif cl == 'high' and 'High' not in df.columns:
                col_map[c] = 'High'
            elif cl == 'low' and 'Low' not in df.columns:
                col_map[c] = 'Low'
            elif cl == 'close' and 'Close' not in df.columns:
                col_map[c] = 'Close'
            elif cl == 'volume' and 'Volume' not in df.columns:
                col_map[c] = 'Volume'
        if col_map:
            df = df.rename(columns=col_map)

        return df

    # ── Export Connection Config ───────────────────────────────
    def export_config(self, output_path: str = None) -> Dict:
        """
        Export the current connection configuration as JSON.
        Can be used to restore the connector state.
        """
        config = {
            'vdf_base': self.vdf_base,
            'extra_dirs': self.extra_dirs,
            'gsheet_urls': self.gsheet_urls,
            'db_registry': self._db_registry,
            'catalog_count': len(self._catalog),
            'scan_summary': self.get_summary(),
            'generated_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'system': 'VeritasAutoPlot_VDFConnector_v1.0',
        }

        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2, default=str)

        return config

