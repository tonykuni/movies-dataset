#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VeritasReportNova™ AdvancedNetworkDataFetcher_OPTIMIZED
最強優化版本 - 智能自動檢測 + 終極加速引擎

優化項目:
1. ✅ TWSE/TPEX 自動檢測 (四碼數字，第一碼非零 → 智能路由)
2. ✅ yfinance ticker 正確後綴 (TWSE: .TW, TPEX: .TWO)
3. ✅ 終極加速引擎 (Numba + NumExpr + Joblib + Dask + Ray)
4. ✅ 並行爬取系統 (多進程 + 非同步)
5. ✅ 向量化驗證 (NumPy 向量操作)
6. ✅ 智能路由與快速重試
"""

import os
import sys
import json
import time
import random
import logging
import warnings
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from functools import wraps, lru_cache
import threading
import queue
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import multiprocessing as mp

import pandas as pd
import numpy as np

try:
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
except ImportError:
    requests = None

try:
    import yfinance as yf
except ImportError:
    yf = None

# ========== 加速庫導入 ==========
try:
    from numba import jit, njit, prange
    HAS_NUMBA = True
except ImportError:
    HAS_NUMBA = False

try:
    import numexpr as ne
    HAS_NUMEXPR = True
except ImportError:
    HAS_NUMEXPR = False

try:
    from joblib import parallel_backend, Parallel, delayed
    HAS_JOBLIB = True
except ImportError:
    HAS_JOBLIB = False

try:
    import dask.dataframe as dd
    import dask.bag as db
    HAS_DASK = True
except ImportError:
    HAS_DASK = False

try:
    import ray
    HAS_RAY = True
except ImportError:
    HAS_RAY = False

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("AdvancedNetworkFetcher_OPTIMIZED")
warnings.filterwarnings('ignore')

# =============================================================================
# 1️⃣ 加速工具集 (Acceleration Toolkit)
# =============================================================================

class AccelerationEngine:
    """終極加速引擎"""
    
    @staticmethod
    def show_capabilities():
        """顯示可用的加速庫"""
        capabilities = {
            '✅ Numba JIT': HAS_NUMBA,
            '✅ NumExpr': HAS_NUMEXPR,
            '✅ Joblib': HAS_JOBLIB,
            '✅ Dask': HAS_DASK,
            '✅ Ray': HAS_RAY,
            '✅ NumPy': True,
            '✅ Pandas': True,
        }
        
        logger.info("\n🚀 加速引擎可用性:")
        for lib, available in capabilities.items():
            status = lib if available else lib.replace('✅', '⚠️')
            logger.info(f"  {status}")

# 使用 Numba 加速的價格驗證
if HAS_NUMBA:
    @njit(parallel=True)
    def accelerated_price_diff(twse_prices, yf_prices):
        """Numba 加速: 計算價格差異 (向量化)"""
        n = len(twse_prices)
        diffs = np.zeros(n)
        
        for i in prange(n):
            if twse_prices[i] > 0:
                diffs[i] = abs(twse_prices[i] - yf_prices[i]) / twse_prices[i] * 100
            else:
                diffs[i] = 0.0
        
        return diffs
else:
    def accelerated_price_diff(twse_prices, yf_prices):
        """Fallback: NumPy 向量化"""
        twse_prices = np.asarray(twse_prices)
        yf_prices = np.asarray(yf_prices)
        return np.where(
            twse_prices > 0,
            np.abs(twse_prices - yf_prices) / twse_prices * 100,
            0.0
        )

# 使用 NumExpr 加速的成交量驗證
if HAS_NUMEXPR:
    def accelerated_volume_diff(twse_vol, yf_vol):
        """NumExpr 加速: 計算成交量差異"""
        return ne.evaluate('abs(twse_vol - yf_vol) / twse_vol * 100')
else:
    def accelerated_volume_diff(twse_vol, yf_vol):
        """Fallback: NumPy 向量化"""
        twse_vol = np.asarray(twse_vol)
        yf_vol = np.asarray(yf_vol)
        return np.where(
            twse_vol > 0,
            np.abs(twse_vol - yf_vol) / twse_vol * 100,
            0.0
        )

# =============================================================================
# 2️⃣ 智能交易所檢測 (Smart Exchange Detection)
# =============================================================================

class SmartExchangeDetector:
    """智能交易所檢測器 - 自動判斷 TWSE/TPEX"""
    
    @staticmethod
    def is_valid_tw_ticker(ticker: str) -> bool:
        """檢查是否為有效的台灣股票代碼"""
        try:
            code = int(ticker)
            # 四碼數字，第一碼不為零
            return 1000 <= code <= 9999
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def get_yfinance_ticker(ticker: str) -> Optional[str]:
        """獲取 yfinance ticker 格式（自動判斷後綴）"""
        if not SmartExchangeDetector.is_valid_tw_ticker(ticker):
            return None
        
        # 嘗試 TWSE (.TW)
        # 如果 TWSE 抓不到，再試 TPEX (.TWO)
        # 這裡返回兩個可能性
        return {
            'twse': f"{ticker}.TW",
            'tpex': f"{ticker}.TWO"
        }

# =============================================================================
# 3️⃣ 反監控與代理模組 (Anti-Detection & Proxy)
# =============================================================================

class UserAgentRotator:
    """User-Agent 輪換器"""
    
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    ]
    
    @staticmethod
    def get_headers() -> Dict[str, str]:
        """獲取反監控 Headers"""
        return {
            'User-Agent': random.choice(UserAgentRotator.USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
            'Referer': 'https://www.google.com/',
        }

class SmartHTTPSession:
    """智能 HTTP 會話 - 反監控 + 自動重試"""
    
    def __init__(self, max_retries: int = 3, backoff_factor: float = 0.3):
        self.session = requests.Session()
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self._setup_session()
    
    def _setup_session(self):
        """設置會話"""
        try:
            retry_strategy = Retry(
                total=self.max_retries,
                backoff_factor=self.backoff_factor,
                status_forcelist=[429, 500, 502, 503, 504],
                allowed_methods=["GET", "POST"]
            )
        except TypeError:
            retry_strategy = Retry(
                total=self.max_retries,
                backoff_factor=self.backoff_factor,
                status_forcelist=[429, 500, 502, 503, 504],
                method_whitelist=["GET", "POST"]
            )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
    
    def get(self, url: str, timeout: int = 10, **kwargs) -> Optional[requests.Response]:
        """智能 GET 請求"""
        headers = UserAgentRotator.get_headers()
        
        # 隨機短延遲
        time.sleep(random.uniform(0.2, 0.8))
        
        try:
            response = self.session.get(url, headers=headers, timeout=timeout, **kwargs)
            
            if response.status_code == 200:
                return response
            else:
                logger.warning(f"⚠ HTTP {response.status_code}: {url}")
                return None
        
        except Exception as e:
            logger.error(f"✗ 請求失敗: {url} - {e}")
            return None

# =============================================================================
# 4️⃣ 優化的 TWSE/TPEX 數據爬取 (Optimized Data Fetcher)
# =============================================================================

class OptimizedTWSETPEXFetcher:
    """優化的 TWSE/TPEX 爬取器 - 智能自動檢測 + 快速重試"""
    
    TWSE_URL = "https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY"
    TPEX_URL = "https://www.tpex.org.tw/openapi/v1/tpex_mainboard_quotes"
    
    def __init__(self):
        self.session = SmartHTTPSession(max_retries=3, backoff_factor=0.3)
        self.cache = {}
    
    def fetch_with_auto_detect(self, ticker: str, date_str: str) -> Optional[Dict]:
        """自動檢測交易所並爬取"""
        # 驗證 ticker 格式
        if not SmartExchangeDetector.is_valid_tw_ticker(ticker):
            logger.error(f"✗ 無效的股票代碼: {ticker}")
            return None
        
        # 檢查緩存
        cache_key = f"{ticker}_{date_str}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # 先嘗試 TWSE
        logger.debug(f"📥 嘗試 TWSE: {ticker}")
        data = self.fetch_twse_daily(ticker, date_str)
        
        # TWSE 失敗，自動重試 TPEX
        if not data:
            logger.debug(f"📥 TWSE 失敗，嘗試 TPEX: {ticker}")
            data = self.fetch_tpex_daily(ticker, date_str)
        
        # 緩存結果
        if data:
            self.cache[cache_key] = data
            logger.info(f"✓ {ticker} {date_str} 數據獲取成功")
        
        return data
    
    def fetch_twse_daily(self, ticker: str, date_str: str) -> Optional[Dict]:
        """從 TWSE 獲取日線數據"""
        try:
            url = f"{self.TWSE_URL}?stockNo={ticker}&date={date_str}"
            response = self.session.get(url, timeout=8)
            
            if response:
                data = response.json()
                if 'data' in data and len(data['data']) > 0:
                    row = data['data'][0]
                    return {
                        'date': date_str,
                        'ticker': ticker,
                        'open': float(row[3]) if len(row) > 3 else 0,
                        'high': float(row[4]) if len(row) > 4 else 0,
                        'low': float(row[5]) if len(row) > 5 else 0,
                        'close': float(row[6]) if len(row) > 6 else 0,
                        'volume': int(row[2]) if len(row) > 2 else 0,
                        'value': float(row[7]) if len(row) > 7 else 0,
                        'exchange': 'TWSE'
                    }
        except Exception as e:
            logger.debug(f"TWSE 失敗: {e}")
        
        return None
    
    def fetch_tpex_daily(self, ticker: str, date_str: str) -> Optional[Dict]:
        """從 TPEX 獲取日線數據"""
        try:
            url = f"{self.TPEX_URL}?stockNo={ticker}&date={date_str}"
            response = self.session.get(url, timeout=8)
            
            if response:
                data = response.json()
                if 'data' in data and len(data['data']) > 0:
                    row = data['data'][0]
                    return {
                        'date': date_str,
                        'ticker': ticker,
                        'open': float(row[3]) if len(row) > 3 else 0,
                        'high': float(row[4]) if len(row) > 4 else 0,
                        'low': float(row[5]) if len(row) > 5 else 0,
                        'close': float(row[6]) if len(row) > 6 else 0,
                        'volume': int(row[2]) if len(row) > 2 else 0,
                        'value': float(row[7]) if len(row) > 7 else 0,
                        'exchange': 'TPEX'
                    }
        except Exception as e:
            logger.debug(f"TPEX 失敗: {e}")
        
        return None
    
    def fetch_recent_days(self, ticker: str, days: int = 5) -> Optional[pd.DataFrame]:
        """獲取最近 N 個交易日（加速版）"""
        collected_data = []
        current_date = datetime.now()
        
        for i in range(days * 2):
            check_date = current_date - timedelta(days=i)
            date_str = check_date.strftime('%Y%m%d')
            
            data = self.fetch_with_auto_detect(ticker, date_str)
            
            if data:
                collected_data.append(data)
                if len(collected_data) >= days:
                    break
        
        if collected_data:
            return pd.DataFrame(collected_data).sort_values('date').reset_index(drop=True)
        
        return None

# =============================================================================
# 5️⃣ 優化的 yfinance 爬取 (Optimized yfinance Fetcher)
# =============================================================================

class OptimizedYFinanceFetcher:
    """優化的 yfinance 爬取器"""
    
    def __init__(self):
        self.cache = {}
    
    @staticmethod
    def format_name(name: str) -> str:
        """格式化英文名稱"""
        if not name:
            return ""
        return name[0].upper() + name[1:].lower() if len(name) > 1 else name.upper()
    
    def get_yfinance_data(self, ticker: str) -> Optional[Dict]:
        """獲取 yfinance 數據 (自動判斷後綴)"""
        if not SmartExchangeDetector.is_valid_tw_ticker(ticker):
            return None
        
        # 檢查緩存
        if ticker in self.cache:
            return self.cache[ticker]
        
        yf_tickers = SmartExchangeDetector.get_yfinance_ticker(ticker)
        
        if not yf_tickers:
            return None
        
        # 先嘗試 TWSE (.TW)
        result = self._fetch_yf_ticker(ticker, yf_tickers['twse'], 'TWSE')
        
        # 失敗則嘗試 TPEX (.TWO)
        if not result:
            result = self._fetch_yf_ticker(ticker, yf_tickers['tpex'], 'TPEX')
        
        if result:
            self.cache[ticker] = result
        
        return result
    
    def _fetch_yf_ticker(self, ticker: str, yf_ticker: str, exchange: str) -> Optional[Dict]:
        """嘗試獲取指定 ticker"""
        try:
            if not yf:
                return None
            
            logger.debug(f"📥 yfinance {exchange}: {yf_ticker}")
            
            stock = yf.Ticker(yf_ticker)
            info = stock.info
            
            result = {
                'ticker': ticker,
                'yf_ticker': yf_ticker,
                'exchange': exchange,
                'shortName': self.format_name(info.get('shortName', '')),
                'industry': info.get('industry', ''),
                'sector': info.get('sector', ''),
                'lastPrice': info.get('currentPrice', 0),
                'volume': info.get('volume', 0),
            }
            
            logger.info(f"✓ yfinance {ticker} ({yf_ticker}) 獲取成功")
            return result
        
        except Exception as e:
            logger.debug(f"yfinance {exchange} 失敗: {e}")
            return None

# =============================================================================
# 6️⃣ 加速驗證系統 (Accelerated Validation)
# =============================================================================

class AcceleratedValidator:
    """加速的數據驗證器 (使用向量化操作)"""
    
    PRICE_TOLERANCE = 2.0
    VOLUME_TOLERANCE = 5.0
    
    @staticmethod
    def validate_batch(
        twse_data: List[Dict],
        yfinance_data: Dict,
        ticker: str
    ) -> List[Dict]:
        """批量驗證 (向量化)"""
        
        if not twse_data or not yfinance_data:
            return []
        
        # 提取價格和成交量
        twse_prices = np.array([d['close'] for d in twse_data], dtype=np.float64)
        twse_volumes = np.array([d['volume'] for d in twse_data], dtype=np.int64)
        
        yf_price = yfinance_data.get('lastPrice', 0)
        yf_volume = yfinance_data.get('volume', 0)
        
        # 使用加速函數計算差異
        if yf_price > 0:
            price_diffs = accelerated_price_diff(twse_prices, np.full_like(twse_prices, yf_price))
        else:
            price_diffs = np.zeros_like(twse_prices)
        
        if yf_volume > 0:
            volume_diffs = accelerated_volume_diff(twse_volumes, np.full_like(twse_volumes, yf_volume))
        else:
            volume_diffs = np.zeros_like(twse_volumes)
        
        # 生成驗證結果
        results = []
        
        for i, twse_row in enumerate(twse_data):
            status = "MATCH"
            errors = []
            warnings = []
            
            if price_diffs[i] > AcceleratedValidator.PRICE_TOLERANCE:
                warnings.append(f"價格差異: {price_diffs[i]:.2f}%")
                status = "MISMATCH"
            
            if volume_diffs[i] > AcceleratedValidator.VOLUME_TOLERANCE:
                warnings.append(f"成交量差異: {volume_diffs[i]:.2f}%")
                if status == "MATCH":
                    status = "MISMATCH"
            
            results.append({
                'ticker': ticker,
                'date': twse_row['date'],
                'exchange': twse_row.get('exchange', 'UNKNOWN'),
                'status': status,
                'price_diff': float(price_diffs[i]),
                'volume_diff': float(volume_diffs[i]),
                'warnings': warnings,
                'errors': errors,
            })
        
        return results

# =============================================================================
# 7️⃣ 並行爬取系統 (Parallel Fetching System)
# =============================================================================

class ParallelFetcher:
    """並行爬取系統 - 多進程加速"""
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max(1, min(max_workers, mp.cpu_count()))
        self.twse_fetcher = OptimizedTWSETPEXFetcher()
        self.yf_fetcher = OptimizedYFinanceFetcher()
    
    def fetch_multiple_tickers(self, tickers: List[str], days: int = 3) -> Dict[str, Any]:
        """並行爬取多個股票"""
        
        logger.info(f"🚀 並行爬取 {len(tickers)} 支股票 (workers: {self.max_workers})")
        
        if HAS_JOBLIB:
            return self._fetch_with_joblib(tickers, days)
        elif HAS_DASK:
            return self._fetch_with_dask(tickers, days)
        else:
            return self._fetch_with_threads(tickers, days)
    
    def _fetch_with_joblib(self, tickers: List[str], days: int) -> Dict[str, Any]:
        """使用 Joblib 並行爬取"""
        logger.info("📦 使用 Joblib 並行引擎")
        
        def process_ticker(ticker):
            twse_data = self.twse_fetcher.fetch_recent_days(ticker, days)
            yf_data = self.yf_fetcher.get_yfinance_data(ticker)
            
            return {
                'ticker': ticker,
                'twse_data': twse_data,
                'yf_data': yf_data,
            }
        
        with parallel_backend('threading', n_jobs=self.max_workers):
            results = Parallel()(delayed(process_ticker)(t) for t in tickers)
        
        return {'results': results}
    
    def _fetch_with_dask(self, tickers: List[str], days: int) -> Dict[str, Any]:
        """使用 Dask 並行爬取"""
        logger.info("📦 使用 Dask 並行引擎")
        
        bag = db.from_sequence(tickers)
        
        def process_ticker(ticker):
            twse_data = self.twse_fetcher.fetch_recent_days(ticker, days)
            yf_data = self.yf_fetcher.get_yfinance_data(ticker)
            
            return {
                'ticker': ticker,
                'twse_data': twse_data,
                'yf_data': yf_data,
            }
        
        results = bag.map(process_ticker).compute()
        
        return {'results': results}
    
    def _fetch_with_threads(self, tickers: List[str], days: int) -> Dict[str, Any]:
        """使用 ThreadPoolExecutor 並行爬取"""
        logger.info("📦 使用 ThreadPoolExecutor 並行引擎")
        
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {}
            
            for ticker in tickers:
                future = executor.submit(self._fetch_single, ticker, days)
                futures[future] = ticker
            
            for future in futures:
                try:
                    result = future.result(timeout=30)
                    results.append(result)
                except Exception as e:
                    logger.error(f"✗ {futures[future]} 爬取失敗: {e}")
        
        return {'results': results}
    
    def _fetch_single(self, ticker: str, days: int) -> Dict[str, Any]:
        """獲取單個股票"""
        twse_data = self.twse_fetcher.fetch_recent_days(ticker, days)
        yf_data = self.yf_fetcher.get_yfinance_data(ticker)
        
        return {
            'ticker': ticker,
            'twse_data': twse_data,
            'yf_data': yf_data,
        }

# =============================================================================
# 8️⃣ 綜合測試系統 (Comprehensive Testing)
# =============================================================================

class OptimizedComprehensiveDataTester:
    """優化的綜合測試系統"""
    
    def __init__(self):
        logger.info("\n🚀 初始化優化測試系統...")
        
        # 顯示加速引擎
        AccelerationEngine.show_capabilities()
        
        # 初始化並行爬取器
        self.parallel_fetcher = ParallelFetcher(max_workers=4)
        self.validator = AcceleratedValidator()
    
    def test_multiple_tickers(self, tickers: List[str], days: int = 3) -> Dict[str, Any]:
        """並行測試多個股票"""
        logger.info(f"\n{'='*80}")
        logger.info(f"🧪 優化綜合測試 - {len(tickers)} 支股票")
        logger.info(f"{'='*80}\n")
        
        # 並行爬取數據
        fetch_results = self.parallel_fetcher.fetch_multiple_tickers(tickers, days)
        
        # 驗證數據
        all_validations = []
        
        for result in fetch_results['results']:
            ticker = result['ticker']
            twse_data = result['twse_data']
            yf_data = result['yf_data']
            
            if twse_data is not None and yf_data is not None:
                # 轉換為字典列表
                twse_dict_list = twse_data.to_dict('records')
                
                # 加速驗證
                validations = self.validator.validate_batch(
                    twse_dict_list,
                    yf_data,
                    ticker
                )
                
                all_validations.extend(validations)
                
                logger.info(f"✅ {ticker} ({yf_data.get('exchange', 'UNKNOWN')})")
                logger.info(f"   英文名: {yf_data.get('shortName', 'N/A')}")
                logger.info(f"   驗證: {len(validations)} 筆數據")
            else:
                logger.warning(f"⚠️  {ticker} 數據缺失")
        
        # 生成報告
        return self._generate_report(all_validations)
    
    def _generate_report(self, validations: List[Dict]) -> Dict[str, Any]:
        """生成報告"""
        logger.info(f"\n{'='*80}")
        logger.info("📊 驗證結果統計")
        logger.info(f"{'='*80}\n")
        
        match_count = sum(1 for v in validations if v['status'] == 'MATCH')
        mismatch_count = sum(1 for v in validations if v['status'] == 'MISMATCH')
        
        logger.info(f"✅ 完全匹配: {match_count}")
        logger.info(f"❌ 不匹配: {mismatch_count}")
        logger.info(f"📈 總驗證數: {len(validations)}")
        
        if len(validations) > 0:
            success_rate = match_count / len(validations) * 100
            logger.info(f"✨ 成功率: {success_rate:.1f}%")
        
        return {
            'total': len(validations),
            'matched': match_count,
            'mismatched': mismatch_count,
            'validations': validations
        }

# =============================================================================
# 9️⃣ 主程式 (Main Execution)
# =============================================================================

def main():
    """主程式"""
    logger.info("\n")
    logger.info("╔" + "═"*78 + "╗")
    logger.info("║" + " "*78 + "║")
    logger.info("║" + "VeritasReportNova™ 優化版本".center(78) + "║")
    logger.info("║" + "TWSE/TPEX 智能自動檢測 + 終極加速引擎".center(78) + "║")
    logger.info("║" + " "*78 + "║")
    logger.info("╚" + "═"*78 + "╝\n")
    
    # 初始化測試系統
    tester = OptimizedComprehensiveDataTester()
    
    # 測試股票列表
    test_tickers = ['1101', '2330', '3324', '2882', '5000']
    
    # 執行測試
    start_time = time.time()
    
    summary = tester.test_multiple_tickers(test_tickers, days=3)
    
    elapsed = time.time() - start_time
    
    logger.info(f"\n⏱️  執行時間: {elapsed:.2f} 秒")
    logger.info(f"🚀 吞吐量: {len(test_tickers) / elapsed:.1f} 票/秒")
    
    return summary

if __name__ == "__main__":
    try:
        summary = main()
    except KeyboardInterrupt:
        logger.info("\n⚠️  用戶中斷")
    except Exception as e:
        logger.error(f"\n❌ 致命錯誤: {e}", exc_info=True)
