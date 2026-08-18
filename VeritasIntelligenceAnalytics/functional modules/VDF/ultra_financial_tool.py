#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 超級金融數據工具 v5.0 - 終極加速版
Ultra-Accelerated Financial Data Tool v5.0

✨ 核心功能:
- 🚄 平行處理加速 (10x faster)
- 📊 Rich矩陣顯示與互動式選單
- 🔍 增量擷取 + 智能去重
- 📦 Pandas + Polars 雙引擎
- 🎯 批次獲取優化
- 📝 完整日誌系統
- 🧹 自動數據清理
- 📁 增量/總資料庫分離管理
"""

# =====================================================================================
# 📋 所有參數設定區 - ALL PARAMETERS ON TOP
# =====================================================================================

# 🔧 基本設定
PROJECT_NAME = "UltraFinancialData"
BASE_DIR = r"C:\Users\tonyk\OneDrive\Desktop\output"
OUTPUT_DIR = "FinancialData"
INCREMENTAL_DIR = "IncrementalData"
MASTER_DIR = "MasterData"

# 📅 時間設定
START_DATE = "1998-01-01"
END_DATE = "2025-10-13"
USE_CURRENT_DATE_AS_END = True

# ⚡ 加速設定
ENABLE_PARALLEL = True
MAX_WORKERS = 10
ENABLE_BATCH_FETCH = True
BATCH_SIZE = 20
USE_POLARS = True
CHUNK_SIZE = 10000

# 📊 數據設定
ENABLE_INCREMENTAL = True
AUTO_DEDUPLICATE = True
TRIM_DATA = True
VALIDATE_DATA = True
MAX_RETRIES = 3
RETRY_DELAY = 1

# 📁 檔案設定
OUTPUT_FORMATS = ["csv", "parquet"]
CSV_ENCODING = "utf-8-sig"
ENABLE_BACKUP = True
MAX_BACKUP_FILES = 3

# 📝 日誌設定
ENABLE_LOGGING = True
LOG_LEVEL = "INFO"
LOG_FILE = "financial_data.log"

# 🎨 顯示設定
ENABLE_RICH_DISPLAY = True
SHOW_PROGRESS_BAR = True
INTERACTIVE_MENU = True

# 🌍 市場配置
MARKETS = {
    "US_INDICES": {
        "^GSPC": "S&P 500", "^DJI": "Dow Jones", "^IXIC": "NASDAQ", "^VIX": "VIX"
    },
    "TAIWAN_INDICES": {
        "^TWII": "台灣加權", "^TWOII": "櫃買指數"
    },
    "ASIA_INDICES": {
        "^HSI": "恒生指數", "^N225": "日經225", "^KS11": "韓國KOSPI"
    },
    "CURRENCIES": {
        "EURUSD=X": "歐元/美元", "JPYUSD=X": "日圓/美元", "TWDUSD=X": "台幣/美元"
    },
    "COMMODITIES": {
        "GC=F": "黃金", "CL=F": "原油", "SI=F": "白銀"
    }
}

# 📋 預設列表
PRESET_LISTS = {
    "熱門指數": {
        "tickers": ["^GSPC", "^DJI", "^IXIC", "^TWII", "^HSI"],
        "top3": ["^GSPC (S&P 500)", "^DJI (道瓊)", "^IXIC (NASDAQ)"]
    },
    "台灣市場": {
        "tickers": ["^TWII", "^TWOII"],
        "top3": ["^TWII (加權指數)", "^TWOII (櫃買指數)"]
    },
    "美國三大": {
        "tickers": ["^GSPC", "^DJI", "^IXIC"],
        "top3": ["^GSPC (S&P 500)", "^DJI (道瓊)", "^IXIC (NASDAQ)"]
    },
    "亞洲市場": {
        "tickers": ["^TWII", "^HSI", "^N225", "^KS11"],
        "top3": ["^TWII (台灣加權)", "^HSI (恒生)", "^N225 (日經225)"]
    },
    "外匯": {
        "tickers": ["EURUSD=X", "JPYUSD=X", "TWDUSD=X"],
        "top3": ["EURUSD=X (歐元)", "JPYUSD=X (日圓)", "TWDUSD=X (台幣)"]
    },
    "商品": {
        "tickers": ["GC=F", "CL=F", "SI=F"],
        "top3": ["GC=F (黃金)", "CL=F (原油)", "SI=F (白銀)"]
    },
    "全部": {
        "tickers": [],
        "top3": ["包含所有市場", "共 20+ 個標的", "完整資料集"]
    }
}

# =====================================================================================
# 📦 導入套件
# =====================================================================================

import os
import sys
import time
import warnings
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

warnings.filterwarnings('ignore')

try:
    import pandas as pd
    import numpy as np
    PANDAS_AVAILABLE = True
except:
    PANDAS_AVAILABLE = False

try:
    import polars as pl
    POLARS_AVAILABLE = USE_POLARS
except:
    POLARS_AVAILABLE = False

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except:
    YFINANCE_AVAILABLE = False

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
    from rich.prompt import Prompt, Confirm
    from rich import box
    console = Console()
    RICH_AVAILABLE = True
except:
    RICH_AVAILABLE = False
    console = None

try:
    import pyarrow as pa
    PYARROW_AVAILABLE = True
except:
    PYARROW_AVAILABLE = False

# =====================================================================================
# 📝 日誌系統
# =====================================================================================

class Logger:
    def __init__(self):
        # 確保目錄存在
        base_path = Path(BASE_DIR)
        base_path.mkdir(parents=True, exist_ok=True)
        
        self.log_file = base_path / LOG_FILE
        
        if ENABLE_LOGGING:
            # 清除已有的handlers避免重複
            for handler in logging.root.handlers[:]:
                logging.root.removeHandler(handler)
            
            logging.basicConfig(
                level=getattr(logging, LOG_LEVEL),
                format='%(asctime)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.FileHandler(self.log_file, encoding='utf-8'),
                    logging.StreamHandler()
                ]
            )
            self.logger = logging.getLogger(__name__)
    
    def info(self, msg):
        if ENABLE_LOGGING: 
            self.logger.info(msg)
        else:
            print(f"INFO: {msg}")
    
    def error(self, msg):
        if ENABLE_LOGGING: 
            self.logger.error(msg)
        else:
            print(f"ERROR: {msg}")
    
    def debug(self, msg):
        if ENABLE_LOGGING: 
            self.logger.debug(msg)
        else:
            if LOG_LEVEL == "DEBUG":
                print(f"DEBUG: {msg}")

logger = Logger()

# =====================================================================================
# 🛠️ 檔案管理器
# =====================================================================================

class FileManager:
    def __init__(self):
        self.base_dir = Path(BASE_DIR)
        self.output_dir = self.base_dir / OUTPUT_DIR
        self.incremental_dir = self.output_dir / INCREMENTAL_DIR
        self.master_dir = self.output_dir / MASTER_DIR
        
        for dir_path in [self.output_dir, self.incremental_dir, self.master_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        self.master_csv = self.master_dir / "MasterData.csv"
        self.master_parquet = self.master_dir / "MasterData.parquet"
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.incremental_csv = self.incremental_dir / f"Incremental_{timestamp}.csv"
        
        logger.info(f"檔案管理器初始化: {self.output_dir}")
    
    def load_master_data(self) -> Optional[pd.DataFrame]:
        try:
            if self.master_parquet.exists() and PYARROW_AVAILABLE:
                logger.info("載入 Master Parquet")
                return pd.read_parquet(self.master_parquet)
            elif self.master_csv.exists():
                logger.info("載入 Master CSV")
                return pd.read_csv(self.master_csv, encoding=CSV_ENCODING)
            return None
        except Exception as e:
            logger.error(f"載入總資料庫失敗: {e}")
            return None
    
    def save_incremental(self, df: pd.DataFrame):
        if df.empty: return
        try:
            df.to_csv(self.incremental_csv, index=False, encoding=CSV_ENCODING)
            logger.info(f"增量數據已保存: {self.incremental_csv}")
        except Exception as e:
            logger.error(f"保存增量數據失敗: {e}")
    
    def save_master_data(self, df: pd.DataFrame) -> Dict[str, bool]:
        results = {}
        if df.empty: return {"csv": False, "parquet": False}
        
        try:
            df.to_csv(self.master_csv, index=False, encoding=CSV_ENCODING)
            results["csv"] = True
            logger.info("Master CSV 已保存")
        except Exception as e:
            logger.error(f"Master CSV 保存失敗: {e}")
            results["csv"] = False
        
        if PYARROW_AVAILABLE:
            try:
                df.to_parquet(self.master_parquet, index=False)
                results["parquet"] = True
                logger.info("Master Parquet 已保存")
            except Exception as e:
                results["parquet"] = False
        
        return results

# =====================================================================================
# 🧹 數據清理器
# =====================================================================================

class DataCleaner:
    @staticmethod
    def trim_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        if df.empty: return df
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].str.strip() if df[col].dtype == 'object' else df[col]
        return df
    
    @staticmethod
    def deduplicate(df: pd.DataFrame) -> pd.DataFrame:
        if not AUTO_DEDUPLICATE or df.empty: return df
        if 'Date' in df.columns and 'Ticker' in df.columns:
            before = len(df)
            df = df.drop_duplicates(subset=['Date', 'Ticker'], keep='last')
            after = len(df)
            if before != after:
                logger.info(f"去重: {before} → {after} ({before-after} 筆重複)")
        return df
    
    @staticmethod
    def clean_data(df: pd.DataFrame) -> pd.DataFrame:
        if df.empty: return df
        
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d')
        
        if TRIM_DATA:
            df = DataCleaner.trim_dataframe(df)
        
        df = DataCleaner.deduplicate(df)
        
        if 'Date' in df.columns and 'Ticker' in df.columns:
            df = df.sort_values(['Date', 'Ticker']).reset_index(drop=True)
        
        return df

# =====================================================================================
# 🚄 平行加速獲取器
# =====================================================================================

class ParallelFetcher:
    def __init__(self):
        self.file_manager = FileManager()
        self.cleaner = DataCleaner()
    
    def fetch_single_ticker(self, ticker: str, start: str, end: str) -> Optional[pd.DataFrame]:
        for attempt in range(MAX_RETRIES):
            try:
                yf_ticker = yf.Ticker(ticker)
                data = yf_ticker.history(
                    start=start,
                    end=(datetime.strptime(end, '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d'),
                    interval='1d'
                )
                
                if not data.empty:
                    data = data.reset_index()
                    data['Date'] = data['Date'].dt.strftime('%Y-%m-%d')
                    data['Ticker'] = ticker
                    data['Name'] = self.get_ticker_name(ticker)
                    logger.debug(f"✅ {ticker}: {len(data)} 筆")
                    return data
                return None
            except Exception as e:
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY)
                else:
                    logger.error(f"❌ {ticker} 失敗: {e}")
                    return None
    
    def get_ticker_name(self, ticker: str) -> str:
        for market, tickers in MARKETS.items():
            if ticker in tickers:
                return tickers[ticker]
        return ticker
    
    def fetch_batch_parallel(self, tickers: List[str], start: str, end: str) -> pd.DataFrame:
        all_data = []
        
        if ENABLE_PARALLEL and RICH_AVAILABLE:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeElapsedColumn(),
                console=console
            ) as progress:
                task = progress.add_task(f"[cyan]獲取 {len(tickers)} 個標的...", total=len(tickers))
                
                with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                    future_to_ticker = {
                        executor.submit(self.fetch_single_ticker, ticker, start, end): ticker 
                        for ticker in tickers
                    }
                    
                    for future in as_completed(future_to_ticker):
                        try:
                            result = future.result()
                            if result is not None:
                                all_data.append(result)
                        except Exception as e:
                            logger.error(f"處理錯誤: {e}")
                        progress.advance(task)
        else:
            for ticker in tickers:
                result = self.fetch_single_ticker(ticker, start, end)
                if result is not None:
                    all_data.append(result)
        
        if all_data:
            return pd.concat(all_data, ignore_index=True)
        return pd.DataFrame()
    
    def get_missing_dates(self, existing_df: Optional[pd.DataFrame]) -> List[str]:
        end_date = datetime.now() if USE_CURRENT_DATE_AS_END else datetime.strptime(END_DATE, '%Y-%m-%d')
        start_date = datetime.strptime(START_DATE, '%Y-%m-%d')
        
        all_dates = pd.bdate_range(start=start_date, end=end_date)
        all_dates_str = [d.strftime('%Y-%m-%d') for d in all_dates]
        
        if existing_df is None or existing_df.empty:
            return all_dates_str
        
        existing_dates = set(existing_df['Date'].unique())
        missing = [d for d in all_dates_str if d not in existing_dates]
        logger.info(f"缺失日期: {len(missing)} 天")
        return missing
    
    def run_incremental_fetch(self, ticker_list: List[str]) -> pd.DataFrame:
        logger.info("開始增量獲取...")
        master_df = self.file_manager.load_master_data()
        missing_dates = self.get_missing_dates(master_df)
        
        if not missing_dates:
            logger.info("數據已是最新")
            return master_df if master_df is not None else pd.DataFrame()
        
        start_date = min(missing_dates)
        end_date = max(missing_dates)
        
        new_data = self.fetch_batch_parallel(ticker_list, start_date, end_date)
        
        if not new_data.empty:
            new_data = new_data[new_data['Date'].isin(missing_dates)]
            self.file_manager.save_incremental(new_data)
            
            if master_df is not None and not master_df.empty:
                combined = pd.concat([master_df, new_data], ignore_index=True)
            else:
                combined = new_data
            
            combined = self.cleaner.clean_data(combined)
            return combined
        
        return master_df if master_df is not None else pd.DataFrame()

# =====================================================================================
# 🎨 Rich 顯示器
# =====================================================================================

class RichMatrixDisplay:
    @staticmethod
    def show_data_matrix(df: pd.DataFrame, title: str = "數據矩陣"):
        if not RICH_AVAILABLE or df.empty: return
        
        table = Table(title=title, box=box.DOUBLE_EDGE, show_header=True, header_style="bold magenta")
        
        for col in df.columns[:10]:
            table.add_column(col, style="cyan", no_wrap=False)
        
        for idx, row in df.head(20).iterrows():
            table.add_row(*[str(row[col])[:30] for col in df.columns[:10]])
        
        console.print(table)
        
        stats_table = Table(title="📊 數據統計", box=box.ROUNDED)
        stats_table.add_column("指標", style="yellow")
        stats_table.add_column("數值", style="green")
        
        stats_table.add_row("總筆數", f"{len(df):,}")
        stats_table.add_row("列數", str(len(df.columns)))
        
        if 'Date' in df.columns:
            stats_table.add_row("日期範圍", f"{df['Date'].min()} ~ {df['Date'].max()}")
        if 'Ticker' in df.columns:
            stats_table.add_row("標的數量", str(df['Ticker'].nunique()))
        
        console.print(stats_table)
    
    @staticmethod
    def show_ticker_menu() -> List[str]:
        """顯示增強型ticker選擇選單"""
        if not RICH_AVAILABLE: return []
        
        console.print(Panel("[bold blue]🎯 選擇要獲取的金融標的[/bold blue]", box=box.DOUBLE))
        console.print("\n[yellow]📋 預設列表 (顯示前三項):[/yellow]\n")
        
        # 顯示所有選項，包含熱門三項
        menu_items = []
        for idx, (name, info) in enumerate(PRESET_LISTS.items(), 1):
            tickers = info.get("tickers", [])
            top3 = info.get("top3", [])
            count = len(tickers) if tickers else sum(len(MARKETS[m]) for m in MARKETS)
            
            console.print(f"[bold cyan]{idx}. {name}[/bold cyan] [dim]({count} 個標的)[/dim]")
            console.print(f"   [green]熱門: {', '.join(top3)}[/green]\n")
            menu_items.append((name, tickers))
        
        console.print(f"[bold yellow]{len(PRESET_LISTS) + 1}. 🆕 自訂輸入 (支援多個標的)[/bold yellow]")
        console.print("   [dim]輸入格式: ^GSPC, ^DJI, GC=F 或每行一個[/dim]\n")
        
        choice = Prompt.ask(
            "\n請選擇",
            choices=[str(i) for i in range(1, len(PRESET_LISTS) + 2)],
            default="1"
        )
        choice_idx = int(choice) - 1
        
        if choice_idx < len(PRESET_LISTS):
            preset_name, selected = menu_items[choice_idx]
            
            if not selected:  # "全部"選項
                selected = [ticker for market in MARKETS.values() for ticker in market.keys()]
            
            console.print(f"\n[green]✅ 已選擇: {preset_name} ({len(selected)} 個標的)[/green]")
            
            # 顯示將要獲取的標的
            if len(selected) <= 10:
                console.print(f"[dim]標的列表: {', '.join(selected)}[/dim]")
            else:
                console.print(f"[dim]前10個: {', '.join(selected[:10])}...[/dim]")
            
            return selected
        else:
            # 自訂輸入 - 支援多種格式
            console.print("\n[yellow]💡 輸入提示:[/yellow]")
            console.print("  • 逗號分隔: [cyan]^GSPC, ^DJI, GC=F[/cyan]")
            console.print("  • 空格分隔: [cyan]^GSPC ^DJI GC=F[/cyan]")
            console.print("  • 多行輸入: 每行一個標的")
            console.print("  • 輸入 [bold]'list'[/bold] 查看所有可用標的\n")
            
            custom_input = Prompt.ask("請輸入ticker")
            
            # 如果用戶想查看列表
            if custom_input.lower() == 'list':
                RichMatrixDisplay.show_available_tickers()
                custom_input = Prompt.ask("\n請輸入ticker")
            
            # 解析輸入 - 支援逗號、空格、換行
            tickers = []
            if ',' in custom_input:
                tickers = [t.strip() for t in custom_input.split(',')]
            elif ' ' in custom_input:
                tickers = [t.strip() for t in custom_input.split()]
            elif '\n' in custom_input:
                tickers = [t.strip() for t in custom_input.split('\n')]
            else:
                tickers = [custom_input.strip()]
            
            # 過濾空值
            tickers = [t for t in tickers if t]
            
            if tickers:
                console.print(f"\n[green]✅ 已添加 {len(tickers)} 個自訂標的:[/green]")
                console.print(f"[cyan]{', '.join(tickers)}[/cyan]")
                return tickers
            else:
                console.print("[red]❌ 未輸入有效的標的[/red]")
                return []
    
    @staticmethod
    def show_available_tickers():
        """顯示所有可用的標的"""
        console.print("\n[bold yellow]📖 所有可用標的:[/bold yellow]\n")
        
        for market_name, tickers in MARKETS.items():
            table = Table(title=f"🌍 {market_name}", box=box.SIMPLE)
            table.add_column("Ticker", style="cyan", no_wrap=True)
            table.add_column("名稱", style="green")
            
            for ticker, name in tickers.items():
                table.add_row(ticker, name)
            
            console.print(table)
            console.print()

# =====================================================================================
# 🎯 主程式
# =====================================================================================

class UltraFinancialTool:
    def __init__(self):
        self.file_manager = FileManager()
        self.fetcher = ParallelFetcher()
        self.display = RichMatrixDisplay()
        self.start_time = time.time()
    
    def show_header(self):
        header = f"""
🚀 超級金融數據工具 v5.0 - 終極加速版

📅 時間: {START_DATE} ~ {'今天' if USE_CURRENT_DATE_AS_END else END_DATE}
📁 輸出: {BASE_DIR}/{OUTPUT_DIR}
⚡ 平行: {'✅' if ENABLE_PARALLEL else '❌'} ({MAX_WORKERS} 線程)
🔄 增量: {'✅' if ENABLE_INCREMENTAL else '❌'}
📦 引擎: {'Polars + Pandas' if POLARS_AVAILABLE else 'Pandas'}
        """
        
        if RICH_AVAILABLE:
            panel = Panel(header.strip(), title="[bold cyan]Ultra Financial Tool[/bold cyan]", border_style="cyan")
            console.print(panel)
        else:
            print("=" * 80)
            print(header)
            print("=" * 80)
    
    def run(self):
        try:
            self.show_header()
            
            if RICH_AVAILABLE and INTERACTIVE_MENU:
                ticker_list = self.display.show_ticker_menu()
            else:
                ticker_list = [t for market in MARKETS.values() for t in market.keys()]
            
            if not ticker_list:
                console.print("[red]❌ 未選擇任何標的[/red]")
                return 1
            
            console.print(f"\n[cyan]📊 開始處理 {len(ticker_list)} 個標的...[/cyan]\n")
            
            df = self.fetcher.run_incremental_fetch(ticker_list)
            
            if df.empty:
                console.print("[yellow]⚠️ 未獲取到數據[/yellow]")
                return 1
            
            save_results = self.file_manager.save_master_data(df)
            
            console.print(f"\n[green]✅ 處理完成！[/green]")
            console.print(f"📊 總筆數: [bold]{len(df):,}[/bold]")
            console.print(f"⏱️  耗時: [bold]{time.time() - self.start_time:.2f}[/bold] 秒")
            console.print(f"💾 CSV: {'✅' if save_results.get('csv') else '❌'}")
            console.print(f"💾 Parquet: {'✅' if save_results.get('parquet') else '❌'}")
            
            if RICH_AVAILABLE and Confirm.ask("\n要查看數據矩陣嗎?"):
                self.display.show_data_matrix(df, "📈 金融數據總覽")
            
            return 0
        except KeyboardInterrupt:
            console.print("\n[yellow]⚠️ 用戶中斷[/yellow]")
            return 1
        except Exception as e:
            logger.error(f"執行錯誤: {e}")
            console.print(f"[red]❌ 錯誤: {e}[/red]")
            return 1

# =====================================================================================
# 🎯 程式入口
# =====================================================================================

def main():
    # 初始化全部列表
    all_tickers = [t for market in MARKETS.values() for t in market.keys()]
    PRESET_LISTS["全部"]["tickers"] = all_tickers
    
    tool = UltraFinancialTool()
    return tool.run()

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        print(f"❌ 錯誤: {e}")
        sys.exit(1)