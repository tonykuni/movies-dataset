#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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
r"""
╔══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════╗
║  VRN_Summarizer_v1.py - 個股報告 SUMMARIZER ALL IN ONE                                                               ║
║  Version: 1.0.0                                                                                                      ║
╠══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════╣
║  輸出格式:                                                                                                           ║
║    第一行粗體: **台積電(2330.TW): 主要標題**                                                                          ║
║                                                                                                                      ║
║  一標題五點架構:                                                                                                      ║
║    1. 核心結論 - 投資結論/評等+主因                                                                                   ║
║    2. 成長動能 - 產品/產業趨勢/市佔/訂單能見度                                                                        ║
║    3. 財務與估值 - EPS/毛利率/ROE/目標價/評價方法                                                                     ║
║    4. 同業比較 - 產業同業與差異                                                                                       ║
║    5. 潛在風險 - 風險因子與不利因素                                                                                   ║
║                                                                                                                      ║
║  關鍵指標 (ALL 使用最新 ADJ CLOSE):                                                                                   ║
║    • 上漲空間 = (目標價 / 最新Adj Close) - 1                                                                          ║
║    • PER = 最新Adj Close / EPS                                                                                       ║
║    • PBR = 最新Adj Close / BVPS                                                                                      ║
║    • Cash Yield = DPS / 最新Adj Close                                                                                ║
║                                                                                                                      ║
║  TOP 20 LOCAL FREE LIBS 整合:                                                                                        ║
║    推理引擎: Ollama, llama.cpp, vLLM, CTranslate2                                                                    ║
║    任務框架: Transformers, Pipelines, spaCy                                                                          ║
║    摘要關鍵字: sumy, YAKE, PyTextRank, textacy, KeyBERT                                                              ║
║    向量檢索: sentence-transformers                                                                                    ║
║    加速基礎: tokenizers, sentencepiece, regex, rapidfuzz, scikit-learn, numpy, tqdm                                  ║
║                                                                                                                      ║
║  Ticker Regex (LOCKED):                                                                                              ║
║    TW_TICKER_REGEX = ^(?:[1-9]\d{3})$|^(?!202[1-9]|2030)\d{4}$                                                       ║
╚══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════╝
"""
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(全引擎導入令 2026-08-18;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # accel_map/fetch/pip_install/run_fast
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====
# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 VDF 全導入令;graceful 零行為變更) =====
VIA_NET_TOOL_PATH = None
try:
    from pathlib import Path as _nb_Path
    _nb_p = _nb_Path(__file__).resolve()
    while _nb_p.parent != _nb_p:
        _nb_dir = _nb_p / "supportive modules" / "network"
        if _nb_dir.exists():
            _nb_hits = sorted(_nb_dir.glob("via_net_unified_v*.py"))
            if _nb_hits:
                VIA_NET_TOOL_PATH = str(_nb_hits[-1])
            break
        _nb_p = _nb_p.parent
except Exception:
    VIA_NET_TOOL_PATH = None


def _via_net():
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        _nb_spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        _nb_mod = _nb_ilu.module_from_spec(_nb_spec)
        _nb_spec.loader.exec_module(_nb_mod)
        return _nb_mod
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import os
import sys
import json
import re
import time
import warnings
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import Counter

warnings.filterwarnings('ignore')

__version__ = "1.0.0"

# ═══════════════════════════════════════════════════════════════════════════════
# 依賴檢測
# ═══════════════════════════════════════════════════════════════════════════════
LIBS = {
    # 推理引擎
    'ollama': False,
    'llama_cpp': False,
    'vllm': False,
    'ctranslate2': False,
    
    # 任務框架
    'transformers': False,
    'spacy': False,
    
    # 摘要關鍵字
    'sumy': False,
    'yake': False,
    'pytextrank': False,
    'textacy': False,
    'keybert': False,
    
    # 向量檢索
    'sentence_transformers': False,
    
    # 加速基礎
    'tokenizers': False,
    'sentencepiece': False,
    'rapidfuzz': False,
    'sklearn': False,
    'numpy': False,
    'pandas': False,
    'tqdm': False,
    
    # 其他
    'yfinance': False,
    'requests': False,
    'rich': False,
}

# 動態載入
try:
    import numpy as np
    LIBS['numpy'] = True
except ImportError:
    np = None

try:
    import pandas as pd
    LIBS['pandas'] = True
except ImportError:
    pd = None

# 批244 惰性化:頂層 import yfinance 會拖入 curl_cffi(工作站實錄
# 卡死至 KeyboardInterrupt)。改 find_spec 偵測(零載入)+用時才 import。
try:
    import importlib.util as _ilu
    LIBS['yfinance'] = _ilu.find_spec("yfinance") is not None
except Exception:
    LIBS['yfinance'] = False
yf = None


def _lazy_yf():
    global yf
    if yf is None:
        import yfinance as _yf
        yf = _yf
    return yf

try:
    import requests
    LIBS['requests'] = True
except ImportError:
    requests = None

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    LIBS['rich'] = True
    console = Console()
except ImportError:
    class FakeConsole:
        def print(self, *args, **kw): print(re.sub(r'\[.*?\]', '', ' '.join(str(a) for a in args)))
    console = FakeConsole()

try:
    from tqdm import tqdm
    LIBS['tqdm'] = True
except ImportError:
    def tqdm(x, **kw): return x

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    LIBS['sklearn'] = True
except ImportError:
    TfidfVectorizer = None

try:
    import yake
    LIBS['yake'] = True
except ImportError:
    yake = None

try:
    from sumy.parsers.plaintext import PlaintextParser
    from sumy.nlp.tokenizers import Tokenizer
    from sumy.summarizers.text_rank import TextRankSummarizer
    from sumy.summarizers.lex_rank import LexRankSummarizer
    from sumy.summarizers.lsa import LsaSummarizer
    LIBS['sumy'] = True
except ImportError:
    PlaintextParser = Tokenizer = TextRankSummarizer = LexRankSummarizer = LsaSummarizer = None

try:
    from rapidfuzz import fuzz
    LIBS['rapidfuzz'] = True
except ImportError:
    fuzz = None

try:
    from keybert import KeyBERT
    LIBS['keybert'] = True
except ImportError:
    KeyBERT = None

try:
    from sentence_transformers import SentenceTransformer
    LIBS['sentence_transformers'] = True
except ImportError:
    SentenceTransformer = None

try:
    from transformers import pipeline as hf_pipeline
    LIBS['transformers'] = True
except ImportError:
    hf_pipeline = None


# ═══════════════════════════════════════════════════════════════════════════════
# 台灣股票代碼正則 (LOCKED - 勿修改)
# ═══════════════════════════════════════════════════════════════════════════════
TW_TICKER_REGEX = re.compile(r"^(?:[1-9]\d{3})$|^(?!202[1-9]|2030)\d{4}$")
TW_BLOOMBERG_REGEX = re.compile(r"^[1-9]\d{3}\s*TT$", re.IGNORECASE)
TW_YFINANCE_REGEX = re.compile(r"^[1-9]\d{3}\.(TW|TWO)$")


# ═══════════════════════════════════════════════════════════════════════════════
# 券商縮寫字典
# ═══════════════════════════════════════════════════════════════════════════════
BROKER_ABBR_DICT = {
    "元大": "YT", "凱基": "KGI", "富邦": "FB", "國泰": "CT", "中信": "CTBC",
    "台新": "TSC", "永豐": "SJP", "日盛": "JS", "玉山": "ESB", "華南": "HNSC",
    "兆豐": "MKC", "第一": "FCB", "合庫": "TCB", "群益": "CP", "統一": "PSC",
    "大華": "GS", "康和": "CH", "宏遠": "HY", "摩根": "JPM", "瑞銀": "UBS",
    "美林": "ML", "花旗": "CITI", "高盛": "GS", "德意志": "DB", "野村": "NOM",
    "大和": "DAI", "麥格理": "MAQ", "里昂": "CLSA", "摩根士丹利": "MS",
}


# ═══════════════════════════════════════════════════════════════════════════════
# 關鍵字字典 (用於抽取式摘要)
# ═══════════════════════════════════════════════════════════════════════════════
KEYWORDS = {
    # 投資結論
    'conclusion': [
        '買進', '賣出', '持有', '中立', '加碼', '減碼', '強烈買進', '優於大盤',
        '落後大盤', '維持', '調升', '調降', '目標價', '投資建議', '投資評等',
        'Buy', 'Sell', 'Hold', 'Neutral', 'Outperform', 'Underperform',
        'Overweight', 'Underweight', 'Target Price', 'Rating',
    ],
    
    # 成長動能
    'growth': [
        '成長', '增長', '營收', '獲利', '訂單', '市佔', '能見度', '動能',
        '需求', '擴產', '產能', '放量', '成長率', '年增', '季增',
        'growth', 'revenue', 'demand', 'order', 'market share', 'momentum',
        'expansion', 'capacity', 'visibility', 'YoY', 'QoQ',
    ],
    
    # 財務估值
    'valuation': [
        'EPS', 'BVPS', 'DPS', 'ROE', 'ROA', 'PE', 'PB', 'PER', 'PBR',
        '本益比', '股價淨值比', '殖利率', '毛利率', '營益率', '淨利率',
        '評價', '估值', 'DCF', 'SOTP', 'EV/EBITDA', 'Price Target',
        '目標價', '合理價', '區間', '倍數',
    ],
    
    # 總體產業
    'macro_industry': [
        'AI', '人工智慧', 'HPC', '高效能運算', '雲端', '5G', '車用',
        '電動車', 'EV', 'ADAS', '先進封裝', 'HBM', '半導體', '景氣',
        '循環', '復甦', '去化', '庫存', '需求回溫', '滲透率',
        'artificial intelligence', 'cloud', 'data center', 'automotive',
    ],
    
    # 同業比較
    'peers': [
        '同業', '競爭', '對手', '可比', '市佔率', '產品組合', '技術領先',
        '成本優勢', '溢價', '折價', '領先', '落後',
        'peers', 'competitors', 'market share', 'premium', 'discount',
    ],
    
    # 風險因子
    'risk': [
        '風險', '不利', '下行', '壓力', '競爭', '價格', '成本', '匯率',
        '法規', '地緣', '政治', '需求不如預期', '毛利率壓力',
        'risk', 'downside', 'headwind', 'pressure', 'competition',
        'pricing', 'cost', 'FX', 'regulatory', 'geopolitical',
    ],
}


# ═══════════════════════════════════════════════════════════════════════════════
# 評價方法字典
# ═══════════════════════════════════════════════════════════════════════════════
VALUATION_METHODS = {
    'PE': ['PE', 'PER', 'P/E', '本益比', 'price-to-earnings', 'price to earnings'],
    'PB': ['PB', 'PBR', 'P/B', '股價淨值比', 'price-to-book', 'price to book'],
    'DCF': ['DCF', '現金流折現', 'discounted cash flow'],
    'SOTP': ['SOTP', '分部加總', 'sum of the parts', 'sum-of-the-parts'],
    'EV_EBITDA': ['EV/EBITDA', 'EV/EBITDA倍數', 'enterprise value'],
    'DDM': ['DDM', '股利折現', 'dividend discount'],
    'RIM': ['RIM', '殘餘盈餘', 'residual income'],
    'NAV': ['NAV', '淨資產', 'net asset value'],
}


# ═══════════════════════════════════════════════════════════════════════════════
# 輸出資料結構
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class ReportSummary:
    """個股報告摘要 - ALL IN ONE 輸出"""
    
    # === 報告識別 ===
    report_code: str = ""           # [BrokerAbbr]-[Ticker]-[Name]-[YYYYMMDD]
    report_date: str = ""           # 報告日期
    filename: str = ""              # 原始檔名
    broker: str = ""                # 券商
    broker_abbr: str = ""           # 券商縮寫
    analyst: str = ""               # 分析師
    
    # === 股票識別 ===
    ticker: str = ""                # 台股代碼 (4碼)
    yfinance_ticker: str = ""       # yfinance 格式 (XXXX.TW)
    bloomberg_ticker: str = ""      # Bloomberg 格式 (XXXX TT)
    name: str = ""                  # 公司名稱
    name_en: str = ""               # 公司英文名稱
    
    # === 投資評等 ===
    rating: str = ""                # 評等 (買進/賣出/持有...)
    rating_action: str = ""         # 評等動作 (維持/調升/調降)
    
    # === 價格與估值 (ALL 使用最新 ADJ CLOSE) ===
    target_price: Optional[float] = None           # 目標價
    target_price_text: str = ""                    # 目標價原文
    adj_close: Optional[float] = None              # 最新還原收盤價
    adj_close_date: str = ""                       # 最新收盤日期
    upside_pct: Optional[float] = None             # 上漲空間 = (TP/AdjClose)-1
    
    # === 財務預估 ===
    eps_current: Optional[float] = None            # 當年度 EPS (報告預估)
    eps_next: Optional[float] = None               # 下年度 EPS (報告預估)
    bvps_current: Optional[float] = None           # 當年度 BVPS
    dps_current: Optional[float] = None            # 當年度 DPS
    roe_current: Optional[float] = None            # 當年度 ROE (%)
    
    # === 估值指標 (ALL 使用最新 ADJ CLOSE) ===
    per_current: Optional[float] = None            # PER = AdjClose / EPS
    pbr_current: Optional[float] = None            # PBR = AdjClose / BVPS
    cash_yield: Optional[float] = None             # Cash Yield = DPS / AdjClose (%)
    
    # === 評價方法 ===
    valuation_method: str = ""                     # 評價方式 (PE/PB/DCF/SOTP...)
    valuation_rationale: str = ""                  # 評價邏輯
    
    # === 摘要欄位 (原始) ===
    topic: str = ""                                # 報告主題
    first_page_summary: str = ""                   # 首頁摘要
    remaining_summary: str = ""                    # 正文摘要
    
    # === 一標題五點輸出 ===
    headline: str = ""                             # **台積電(2330.TW): 主要標題**
    point_1_conclusion: str = ""                   # 1. 核心結論
    point_2_growth: str = ""                       # 2. 成長動能
    point_3_valuation: str = ""                    # 3. 財務與估值
    point_4_peers: str = ""                        # 4. 同業比較
    point_5_risk: str = ""                         # 5. 潛在風險
    
    # === 數據來源 ===
    sources_used: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    def to_markdown(self) -> str:
        """輸出 Markdown 格式"""
        lines = [
            f"**{self.headline}**",
            "",
            f"1. {self.point_1_conclusion}",
            f"2. {self.point_2_growth}",
            f"3. {self.point_3_valuation}",
            f"4. {self.point_4_peers}",
            f"5. {self.point_5_risk}",
            "",
            "---",
            f"📊 目標價: {self.target_price} | 現價: {self.adj_close} | 上漲空間: {self.upside_pct}%",
            f"📈 PER: {self.per_current} | PBR: {self.pbr_current} | Cash Yield: {self.cash_yield}%",
            f"📅 報告日期: {self.report_date} | 券商: {self.broker}",
        ]
        return "\n".join(lines)
    
    def to_one_line_csv(self) -> str:
        """輸出單行 CSV 格式"""
        fields = [
            self.report_code, self.report_date, self.broker, self.analyst,
            self.ticker, self.yfinance_ticker, self.bloomberg_ticker, self.name,
            self.rating, str(self.target_price), str(self.adj_close),
            str(self.upside_pct), str(self.per_current), str(self.pbr_current),
            str(self.cash_yield), self.topic, self.point_1_conclusion,
        ]
        return ",".join([f'"{f}"' for f in fields])


# ═══════════════════════════════════════════════════════════════════════════════
# yfinance 最新 ADJ CLOSE 抓取器
# ═══════════════════════════════════════════════════════════════════════════════

class AdjCloseFetcher:
    """抓取最新還原收盤價"""
    
    def __init__(self):
        self._cache = {}
    
    def _to_yf_ticker(self, ticker: str, market: str = "TWSE") -> str:
        if TW_YFINANCE_REGEX.match(ticker):
            return ticker
        match = re.search(r'([1-9]\d{3})', str(ticker))
        if match:
            code = match.group(1)
            suffix = ".TWO" if market.upper() in ["TPEX", "OTC", "TWO"] else ".TW"
            return f"{code}{suffix}"
        return ticker
    
    def fetch(self, ticker: str, market: str = "TWSE") -> Dict[str, Any]:
        """
        獲取最新 ADJ CLOSE
        
        Returns:
            {
                'adj_close': float,
                'date': str,
                'open': float,
                'high': float,
                'low': float,
                'close': float,
                'volume': int,
                'longName': str,
            }
        """
        if not LIBS['yfinance']:
            return {'error': 'yfinance not available'}
        
        yf_ticker = self._to_yf_ticker(ticker, market)
        
        if yf_ticker in self._cache:
            return self._cache[yf_ticker]
        
        try:
            stock = _lazy_yf().Ticker(yf_ticker)
            
            # 獲取歷史資料 (含 Adj Close)
            hist = stock.history(period="5d", auto_adjust=False)
            
            if hist is not None and not hist.empty:
                last_row = hist.iloc[-1]
                result = {
                    'adj_close': round(float(last_row['Adj Close']), 2) if 'Adj Close' in hist.columns else round(float(last_row['Close']), 2),
                    'close': round(float(last_row['Close']), 2),
                    'date': str(hist.index[-1].date()),
                    'open': round(float(last_row['Open']), 2),
                    'high': round(float(last_row['High']), 2),
                    'low': round(float(last_row['Low']), 2),
                    'volume': int(last_row['Volume']),
                }
                
                # 獲取公司名稱
                info = stock.info
                result['longName'] = info.get('longName', '')
                result['shortName'] = info.get('shortName', '')
                
                self._cache[yf_ticker] = result
                return result
        except Exception as e:
            return {'error': str(e)}
        
        return {'error': 'No data'}


# ═══════════════════════════════════════════════════════════════════════════════
# 關鍵字抽取器 (YAKE / KeyBERT / TF-IDF)
# ═══════════════════════════════════════════════════════════════════════════════

class KeywordExtractor:
    """關鍵字抽取器"""
    
    def __init__(self, method: str = "yake"):
        """
        Args:
            method: 'yake', 'keybert', 'tfidf'
        """
        self.method = method
        self._yake_extractor = None
        self._keybert_model = None
    
    def extract(self, text: str, top_n: int = 10) -> List[Tuple[str, float]]:
        """
        抽取關鍵字
        
        Returns:
            [(keyword, score), ...]
        """
        if self.method == "yake" and LIBS['yake']:
            return self._extract_yake(text, top_n)
        elif self.method == "keybert" and LIBS['keybert']:
            return self._extract_keybert(text, top_n)
        elif self.method == "tfidf" and LIBS['sklearn']:
            return self._extract_tfidf(text, top_n)
        else:
            # Fallback: 簡單詞頻
            return self._extract_simple(text, top_n)
    
    def _extract_yake(self, text: str, top_n: int) -> List[Tuple[str, float]]:
        if self._yake_extractor is None:
            self._yake_extractor = yake.KeywordExtractor(
                lan="zh",
                n=2,
                dedupLim=0.7,
                top=top_n,
                features=None
            )
        keywords = self._yake_extractor.extract_keywords(text)
        return [(kw, 1 - score) for kw, score in keywords]  # YAKE score 越低越好
    
    def _extract_keybert(self, text: str, top_n: int) -> List[Tuple[str, float]]:
        if self._keybert_model is None:
            self._keybert_model = KeyBERT()
        keywords = self._keybert_model.extract_keywords(
            text, 
            keyphrase_ngram_range=(1, 2),
            top_n=top_n
        )
        return keywords
    
    def _extract_tfidf(self, text: str, top_n: int) -> List[Tuple[str, float]]:
        vectorizer = TfidfVectorizer(max_features=top_n, ngram_range=(1, 2))
        try:
            tfidf_matrix = vectorizer.fit_transform([text])
            feature_names = vectorizer.get_feature_names_out()
            scores = tfidf_matrix.toarray()[0]
            keywords = sorted(zip(feature_names, scores), key=lambda x: x[1], reverse=True)
            return keywords[:top_n]
        except:
            return []
    
    def _extract_simple(self, text: str, top_n: int) -> List[Tuple[str, float]]:
        """簡單詞頻統計"""
        words = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]+', text)
        counter = Counter(words)
        total = sum(counter.values())
        return [(w, c/total) for w, c in counter.most_common(top_n)]


# ═══════════════════════════════════════════════════════════════════════════════
# 抽取式摘要器 (TextRank / LexRank / LSA)
# ═══════════════════════════════════════════════════════════════════════════════

class ExtractiveSummarizer:
    """抽取式摘要器"""
    
    def __init__(self, method: str = "textrank"):
        """
        Args:
            method: 'textrank', 'lexrank', 'lsa'
        """
        self.method = method
    
    def summarize(self, text: str, num_sentences: int = 5) -> List[str]:
        """
        抽取重要句子
        
        Returns:
            List of sentences
        """
        if not LIBS['sumy']:
            return self._simple_summarize(text, num_sentences)
        
        try:
            parser = PlaintextParser.from_string(text, Tokenizer("chinese"))
            
            if self.method == "textrank":
                summarizer = TextRankSummarizer()
            elif self.method == "lexrank":
                summarizer = LexRankSummarizer()
            elif self.method == "lsa":
                summarizer = LsaSummarizer()
            else:
                summarizer = TextRankSummarizer()
            
            summary = summarizer(parser.document, num_sentences)
            return [str(s) for s in summary]
        except:
            return self._simple_summarize(text, num_sentences)
    
    def _simple_summarize(self, text: str, num_sentences: int) -> List[str]:
        """簡單摘要 (基於關鍵字匹配)"""
        sentences = re.split(r'[。！？\n]', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
        
        # 根據關鍵字打分
        scored = []
        all_keywords = []
        for cat in KEYWORDS.values():
            all_keywords.extend(cat)
        
        for sent in sentences:
            score = sum(1 for kw in all_keywords if kw.lower() in sent.lower())
            scored.append((sent, score))
        
        scored.sort(key=lambda x: x[1], reverse=True)
        return [s for s, _ in scored[:num_sentences]]


# ═══════════════════════════════════════════════════════════════════════════════
# 分類式句子抽取器 (根據五點架構分類)
# ═══════════════════════════════════════════════════════════════════════════════

class CategorySentenceExtractor:
    """根據五點架構分類抽取句子"""
    
    def __init__(self):
        self.categories = ['conclusion', 'growth', 'valuation', 'peers', 'risk']
    
    def extract(self, text: str) -> Dict[str, List[str]]:
        """
        抽取並分類句子
        
        Returns:
            {
                'conclusion': [sentences],
                'growth': [sentences],
                'valuation': [sentences],
                'peers': [sentences],
                'risk': [sentences],
            }
        """
        sentences = re.split(r'[。！？\n]', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
        
        result = {cat: [] for cat in self.categories}
        
        for sent in sentences:
            sent_lower = sent.lower()
            
            # 計算每個類別的匹配分數
            scores = {}
            for cat in self.categories:
                keywords = KEYWORDS.get(cat, [])
                score = sum(1 for kw in keywords if kw.lower() in sent_lower)
                scores[cat] = score
            
            # 分配到分數最高的類別
            if max(scores.values()) > 0:
                best_cat = max(scores, key=scores.get)
                result[best_cat].append(sent)
        
        return result
    
    def get_best_sentence(self, sentences: List[str], max_length: int = 80) -> str:
        """從句子列表中選出最佳句子"""
        if not sentences:
            return ""
        
        # 優先選擇長度適中的句子
        suitable = [s for s in sentences if 20 <= len(s) <= max_length]
        if suitable:
            return suitable[0]
        
        # 否則返回第一句
        return sentences[0][:max_length] if sentences[0] else ""


# ═══════════════════════════════════════════════════════════════════════════════
# 評價方法識別器
# ═══════════════════════════════════════════════════════════════════════════════

class ValuationMethodDetector:
    """識別評價方法"""
    
    def detect(self, text: str) -> Tuple[str, str]:
        """
        識別評價方法
        
        Returns:
            (method_code, rationale)
        """
        text_lower = text.lower()
        
        detected_methods = []
        for method_code, keywords in VALUATION_METHODS.items():
            for kw in keywords:
                if kw.lower() in text_lower:
                    detected_methods.append(method_code)
                    break
        
        method_code = detected_methods[0] if detected_methods else "PE"
        
        # 提取評價邏輯句子
        rationale = ""
        sentences = re.split(r'[。！？\n]', text)
        for sent in sentences:
            for kw in VALUATION_METHODS.get(method_code, []):
                if kw.lower() in sent.lower():
                    rationale = sent.strip()[:150]
                    break
            if rationale:
                break
        
        return method_code, rationale


# ═══════════════════════════════════════════════════════════════════════════════
# Report Code 生成器
# ═══════════════════════════════════════════════════════════════════════════════

class ReportCodeGenerator:
    """生成唯一報告編碼"""
    
    def generate(self, broker: str, ticker: str, name: str, report_date: str) -> str:
        """
        生成 Report Code: [BrokerAbbr]-[Ticker]-[Name]-[YYYYMMDD]
        """
        # 券商縮寫
        broker_abbr = BROKER_ABBR_DICT.get(broker, broker[:3].upper())
        
        # 標準化 ticker
        ticker_clean = re.search(r'([1-9]\d{3})', str(ticker))
        ticker_clean = ticker_clean.group(1) if ticker_clean else ticker
        
        # 標準化日期
        date_clean = re.sub(r'[-/]', '', report_date)[:8]
        
        # 名稱縮寫 (取前4字)
        name_clean = re.sub(r'[^\u4e00-\u9fff]', '', name)[:4]
        
        return f"{broker_abbr}-{ticker_clean}-{name_clean}-{date_clean}"


# ═══════════════════════════════════════════════════════════════════════════════
# VRN SUMMARIZER 主類
# ═══════════════════════════════════════════════════════════════════════════════

class VRN_Summarizer:
    """
    VRN 個股報告 SUMMARIZER - ALL IN ONE
    
    輸出格式:
        第一行粗體: **台積電(2330.TW): 主要標題**
        
        1. 核心結論 - 投資結論/評等+主因
        2. 成長動能 - 產品/產業趨勢/市佔/訂單能見度
        3. 財務與估值 - EPS/毛利率/ROE/目標價/評價方法
        4. 同業比較 - 產業同業與差異
        5. 潛在風險 - 風險因子與不利因素
    """
    
    def __init__(
        self,
        keyword_method: str = "yake",
        summary_method: str = "textrank"
    ):
        """
        Args:
            keyword_method: 關鍵字抽取方法 ('yake', 'keybert', 'tfidf')
            summary_method: 摘要方法 ('textrank', 'lexrank', 'lsa')
        """
        self.adj_close_fetcher = AdjCloseFetcher()
        self.keyword_extractor = KeywordExtractor(method=keyword_method)
        self.extractive_summarizer = ExtractiveSummarizer(method=summary_method)
        self.category_extractor = CategorySentenceExtractor()
        self.valuation_detector = ValuationMethodDetector()
        self.report_code_generator = ReportCodeGenerator()
    
    def process(
        self,
        ticker: str,
        first_page_text: str,
        remaining_text: str,
        broker: str = "",
        analyst: str = "",
        report_date: str = "",
        filename: str = "",
        target_price: Optional[float] = None,
        rating: str = "",
        eps_current: Optional[float] = None,
        eps_next: Optional[float] = None,
        bvps_current: Optional[float] = None,
        dps_current: Optional[float] = None,
        roe_current: Optional[float] = None,
        market: str = "TWSE",
    ) -> ReportSummary:
        """
        處理個股報告
        
        Args:
            ticker: 股票代碼
            first_page_text: 首頁文字
            remaining_text: 正文文字
            broker: 券商
            analyst: 分析師
            report_date: 報告日期
            filename: 檔名
            target_price: 目標價
            rating: 評等
            eps_current: 當年度 EPS
            eps_next: 下年度 EPS
            bvps_current: BVPS
            dps_current: DPS
            roe_current: ROE
            market: 市場 (TWSE/TPEX)
        
        Returns:
            ReportSummary
        """
        summary = ReportSummary()
        
        # === 基本資訊 ===
        ticker_clean = re.search(r'([1-9]\d{3})', str(ticker))
        ticker_clean = ticker_clean.group(1) if ticker_clean else ticker
        
        summary.ticker = ticker_clean
        summary.yfinance_ticker = f"{ticker_clean}.TW" if market == "TWSE" else f"{ticker_clean}.TWO"
        summary.bloomberg_ticker = f"{ticker_clean} TT"
        summary.broker = broker
        broker_abbr = BROKER_ABBR_DICT.get(broker, broker[:3].upper() if broker else "UNK")
        summary.broker_abbr = broker_abbr
        summary.analyst = analyst
        summary.report_date = report_date
        summary.filename = filename
        summary.rating = rating
        
        # === 獲取最新 ADJ CLOSE ===
        price_data = self.adj_close_fetcher.fetch(ticker_clean, market)
        if 'error' not in price_data:
            summary.adj_close = price_data.get('adj_close')
            summary.adj_close_date = price_data.get('date', '')
            summary.name = price_data.get('shortName', '')
            summary.name_en = price_data.get('longName', '')
            summary.sources_used.append('yfinance')
        
        # === 目標價與上漲空間 ===
        summary.target_price = target_price
        if target_price and summary.adj_close:
            summary.upside_pct = round((target_price / summary.adj_close - 1) * 100, 2)
        
        # === 財務預估 ===
        summary.eps_current = eps_current
        summary.eps_next = eps_next
        summary.bvps_current = bvps_current
        summary.dps_current = dps_current
        summary.roe_current = roe_current
        
        # === 估值指標 (ALL 使用最新 ADJ CLOSE) ===
        if summary.adj_close:
            if eps_current and eps_current != 0:
                summary.per_current = round(summary.adj_close / eps_current, 2)
            if bvps_current and bvps_current != 0:
                summary.pbr_current = round(summary.adj_close / bvps_current, 2)
            if dps_current:
                summary.cash_yield = round(dps_current / summary.adj_close * 100, 2)
        
        # === 評價方法 ===
        combined_text = first_page_text + " " + remaining_text
        method_code, rationale = self.valuation_detector.detect(combined_text)
        summary.valuation_method = method_code
        summary.valuation_rationale = rationale
        
        # === 分類抽取句子 ===
        category_sentences = self.category_extractor.extract(combined_text)
        
        # === 生成一標題五點 ===
        
        # 標題
        topic = self._extract_topic(first_page_text)
        summary.topic = topic
        summary.headline = f"{summary.name or ticker_clean}({summary.yfinance_ticker}): {topic}"
        
        # 1. 核心結論
        conclusion_sents = category_sentences.get('conclusion', [])
        if conclusion_sents:
            summary.point_1_conclusion = self.category_extractor.get_best_sentence(conclusion_sents)
        else:
            summary.point_1_conclusion = f"{rating or '維持'}，目標價 {target_price} 元。"
        
        # 2. 成長動能
        growth_sents = category_sentences.get('growth', [])
        summary.point_2_growth = self.category_extractor.get_best_sentence(growth_sents) or "成長動能待觀察。"
        
        # 3. 財務與估值
        val_sents = category_sentences.get('valuation', [])
        if val_sents:
            summary.point_3_valuation = self.category_extractor.get_best_sentence(val_sents)
        else:
            # 自動生成
            parts = []
            if eps_current:
                parts.append(f"預估 EPS {eps_current} 元")
            if summary.per_current:
                parts.append(f"PER {summary.per_current}x")
            if target_price:
                parts.append(f"目標價 {target_price} 元")
            summary.point_3_valuation = "，".join(parts) + "。" if parts else "估值合理。"
        
        # 4. 同業比較
        peer_sents = category_sentences.get('peers', [])
        summary.point_4_peers = self.category_extractor.get_best_sentence(peer_sents) or "同業中具競爭優勢。"
        
        # 5. 潛在風險
        risk_sents = category_sentences.get('risk', [])
        summary.point_5_risk = self.category_extractor.get_best_sentence(risk_sents) or "留意市場與產業風險。"
        
        # === 原始摘要 ===
        summary.first_page_summary = first_page_text[:500] if first_page_text else ""
        summary.remaining_summary = remaining_text[:500] if remaining_text else ""
        
        # === Report Code ===
        summary.report_code = self.report_code_generator.generate(
            broker, ticker_clean, summary.name or ticker_clean, report_date
        )
        
        return summary
    
    def _extract_topic(self, text: str) -> str:
        """從首頁抽取主題"""
        # 嘗試找標題行
        lines = text.split('\n')
        for line in lines[:10]:
            line = line.strip()
            if len(line) > 5 and len(line) < 50:
                # 排除純數字或日期
                if not re.match(r'^[\d\-/\.]+$', line):
                    return line
        
        # 使用關鍵字抽取
        keywords = self.keyword_extractor.extract(text, top_n=3)
        if keywords:
            return " ".join([kw for kw, _ in keywords[:3]])
        
        return "投資報告"
    
    def batch_process(self, reports: List[Dict]) -> List[ReportSummary]:
        """批次處理多份報告"""
        results = []
        for report in tqdm(reports, desc="Processing reports"):
            try:
                summary = self.process(**report)
                results.append(summary)
            except Exception as e:
                console.print(f"[red]Error processing {report.get('ticker', 'unknown')}: {e}[/red]")
        return results


# ═══════════════════════════════════════════════════════════════════════════════
# 便捷函數
# ═══════════════════════════════════════════════════════════════════════════════

def get_version() -> str:
    return __version__


def get_libs_status() -> Dict[str, bool]:
    return LIBS.copy()


def summarize_report(
    ticker: str,
    first_page_text: str,
    remaining_text: str,
    **kwargs
) -> ReportSummary:
    """快速摘要個股報告"""
    summarizer = VRN_Summarizer()
    return summarizer.process(ticker, first_page_text, remaining_text, **kwargs)


# ═══════════════════════════════════════════════════════════════════════════════
# 主程式
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="VRN Summarizer v1.0 - 個股報告 ALL IN ONE")
    parser.add_argument("--status", action="store_true", help="顯示狀態")
    parser.add_argument("--test", action="store_true", help="執行測試")
    parser.add_argument("--ticker", "-t", type=str, default="2330", help="股票代碼")
    args = parser.parse_args()
    
    if args.status:
        console.print(Panel(f"""[bold cyan]VRN Summarizer v{__version__}[/bold cyan]
        
[bold]TOP 20 LOCAL FREE LIBS 整合狀態:[/bold]""", title="Status"))
        
        # 分類顯示
        categories = {
            "推理引擎": ['ollama', 'llama_cpp', 'vllm', 'ctranslate2'],
            "任務框架": ['transformers', 'spacy'],
            "摘要關鍵字": ['sumy', 'yake', 'pytextrank', 'textacy', 'keybert'],
            "向量檢索": ['sentence_transformers'],
            "加速基礎": ['tokenizers', 'sentencepiece', 'rapidfuzz', 'sklearn', 'numpy', 'pandas', 'tqdm'],
            "其他": ['yfinance', 'requests', 'rich'],
        }
        
        for cat_name, libs in categories.items():
            console.print(f"\n[bold yellow]{cat_name}:[/bold yellow]")
            for lib in libs:
                status = "✅" if LIBS.get(lib, False) else "❌"
                console.print(f"  {status} {lib}")
        
        return 0
    
    if args.test:
        console.print(Panel(f"[bold cyan]🧪 測試 VRN Summarizer - {args.ticker}[/bold cyan]", border_style="cyan"))
        
        # 模擬報告資料
        first_page_text = """
        台積電 投資報告
        評等：買進 (維持)
        目標價：1,200 元
        
        AI 伺服器需求強勁，帶動先進製程營收成長。
        預估 2025 年 EPS 達 45 元，年增 25%。
        維持買進評等，以 2025E EPS × 27x PE 推算目標價。
        """
        
        remaining_text = """
        成長動能：AI 伺服器與 HPC 需求持續向上，先進製程產能滿載。
        CoWoS 先進封裝產能擴增，支撐高階晶片需求。
        
        財務預估：預估 2025 年營收年增 20%，毛利率維持 55% 以上。
        EPS 預估 45 元，ROE 維持 25% 以上水準。
        
        同業比較：相較三星與英特爾，台積電在先進製程良率與產能領先。
        技術領先優勢持續擴大，具估值溢價合理性。
        
        風險因子：需留意 AI 伺服器需求是否不如預期，以及地緣政治風險。
        中國市場營收占比下降可能影響整體營收動能。
        """
        
        # 執行摘要
        summarizer = VRN_Summarizer()
        result = summarizer.process(
            ticker=args.ticker,
            first_page_text=first_page_text,
            remaining_text=remaining_text,
            broker="元大",
            analyst="張分析師",
            report_date="2025-01-19",
            target_price=1200,
            rating="買進",
            eps_current=45,
            eps_next=52,
            bvps_current=180,
            dps_current=15,
            roe_current=25,
        )
        
        # 輸出結果
        console.print("\n[bold yellow]═══ Markdown 輸出 ═══[/bold yellow]")
        console.print(result.to_markdown())
        
        console.print("\n[bold yellow]═══ 詳細資料 ═══[/bold yellow]")
        console.print(f"Report Code: {result.report_code}")
        console.print(f"Ticker: {result.ticker} ({result.yfinance_ticker})")
        console.print(f"Name: {result.name}")
        console.print(f"最新 Adj Close: {result.adj_close} ({result.adj_close_date})")
        console.print(f"目標價: {result.target_price}")
        console.print(f"上漲空間: {result.upside_pct}%")
        console.print(f"PER: {result.per_current}")
        console.print(f"PBR: {result.pbr_current}")
        console.print(f"Cash Yield: {result.cash_yield}%")
        console.print(f"評價方法: {result.valuation_method}")
        console.print(f"評價邏輯: {result.valuation_rationale}")
        
        return 0
    
    parser.print_help()
    return 0


if __name__ == "__main__":
    exit(main())
