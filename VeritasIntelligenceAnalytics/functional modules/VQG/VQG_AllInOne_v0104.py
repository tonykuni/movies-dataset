#!/usr/bin/env python3
"""VeritaQuantGuard v0104 • [VIA:ACCEL-BRIDGE] DuckDB + Polars, local read-only.
python VQG_AllInOne_v0104.py --help
python VQG_AllInOne_v0104.py selftest
python VQG_AllInOne_v0104.py scan --root "C:/path/to/vdf_database"
python VQG_AllInOne_v0104.py calc --ticker 2330.TW --metrics sma rsi
python VQG_AllInOne_v0104.py activity
python VQG_AllInOne_v0104.py chart --ticker 2330.TW --out chart.html
"""
import argparse
import calendar
import hashlib
import inspect
import json
import math
import re
import sys
import tempfile
import unicodedata
import webbrowser
from contextlib import closing
from datetime import date, timedelta
from pathlib import Path

try:
    import duckdb
    import polars as pl
except ModuleNotFoundError as exc:
    raise SystemExit(f"目前 Python 缺少 {exc.name}。請改用已安裝 duckdb、polars 的 VIA 環境。") from exc

ROOT = Path.home()/'OneDrive/Documents/VeritasIntelligenceAnalytics/via_database/vdf_database'
VERSION = 'v0104'
DEFAULT_WINDOWS = (5,10,20,60,120,240)
DEFAULT_WINDOW, RSI_WINDOW = 20,14
MAX_WINDOW, MAX_INPUT_ROWS, MAX_OUTPUT_ROWS = 252,5000,100
MACD_FAST,MACD_SLOW,MACD_SIGNAL = 12,26,9
BAND_K,MAD_SIGMA,MAD_Z_SCALE,DOWNSIDE_MIN = 2.0,1.4826,0.6745,5
ABS_TOL,REL_TOL = 1e-10,1e-6
NONCOMPARABLE = {'summary','returns','volatility','roc','slope','volume_zscore','beta'}
FIXTURE_CONTEXT = dict(entry='VCGC',owner='VDF',source_type='parquet',purpose='technical_analysis',
                       frequency='daily',calendar_verified=True,price_field='adj_close',mode='offline_fixture')
CORE = {'summary': {'stable_id': 'VQG.IND.SUMMARY',
             'formula': 'latest, min, max, mean, pstdev of finite adj_close',
             'solutions': [{'id': 'S1', 'name': 'strict_finite', 'method': '只納入有限正價格；空集合回 null'},
                           {'id': 'S2', 'name': 'median_level', 'method': '用 median / MAD 描述位置，降低跳空影響'},
                           {'id': 'S3', 'name': 'last_valid_only', 'method': '只報告最後有效價與有效筆數，不做分布'}]},
 'returns': {'stable_id': 'VQG.IND.RETURNS',
             'formula': 'simple = p_t/p_{t-1}-1 ; log = ln(p_t/p_{t-1})',
             'solutions': [{'id': 'S1', 'name': 'simple_strict', 'method': '只對相鄰有效交易日計算；缺日兩側都 null'},
                           {'id': 'S2', 'name': 'log_strict', 'method': '同樣相鄰約束下取對數報酬'},
                           {'id': 'S3', 'name': 'gap_aware_hold', 'method': '缺日不填價；跨缺日報酬另欄 gap_return，不混入連續報酬'}]},
 'sma': {'stable_id': 'VQG.IND.SMA',
         'formula': 'SMA_n(t) = mean(p_{t-n+1..t})',
         'solutions': [{'id': 'S1', 'name': 'strict_window', 'method': '未滿 n 或視窗內有 null 則 null'},
                       {'id': 'S2', 'name': 'expanding_flagged', 'method': '未滿 n 用擴張均值並標記 partial=true，滿窗後等同 S1'},
                       {'id': 'S3', 'name': 'clean_remap', 'method': '先剔除 null 再算滿窗 SMA，映回原時間軸；coverage < 1 則標記'}],
         'window': 20},
 'ema': {'stable_id': 'VQG.IND.EMA',
         'formula': 'EMA_t = alpha*p_t + (1-alpha)*EMA_{t-1}, alpha=2/(n+1)',
         'solutions': [{'id': 'S1', 'name': 'sma_seed', 'method': '前 n 根 SMA 當種子，之前 null'},
                       {'id': 'S2', 'name': 'first_price_seed', 'method': '第一有效價當種子，標記 seed=first_price'},
                       {'id': 'S3', 'name': 'wilder_alpha', 'method': 'alpha=1/n 的 Wilder 平滑；未滿 n 為 null'}],
         'window': 20},
 'volatility': {'stable_id': 'VQG.IND.VOLATILITY',
                'formula': 'stdev of simple returns over n',
                'solutions': [{'id': 'S1', 'name': 'sample_simple', 'method': '簡單報酬樣本標準差，未滿窗 null，不年化'},
                              {'id': 'S2',
                               'name': 'population_simple',
                               'method': '母體標準差；與 S1 的理論比為 sqrt(n/(n-1))'},
                              {'id': 'S3',
                               'name': 'log_or_robust',
                               'method': '對數報酬樣本標準差；若高低價齊備改 Parkinson，否則維持 log'}],
                'window': 20},
 'zscore': {'stable_id': 'VQG.IND.ZSCORE',
            'formula': '(p_t - mean_n) / stdev_n',
            'solutions': [{'id': 'S1', 'name': 'sample_null_if_flat', 'method': '樣本標準差；std=0 回 null'},
                          {'id': 'S2',
                           'name': 'population_zero_if_flat',
                           'method': '母體標準差；價格等於均值且 std=0 回 0 並標記 flat'},
                          {'id': 'S3', 'name': 'mad_robust', 'method': '0.6745*(p-median)/MAD；MAD=0 回 null'}],
            'window': 20},
 'rsi': {'stable_id': 'VQG.IND.RSI',
         'formula': 'RSI = 100 - 100/(1+avg_gain/avg_loss)',
         'solutions': [{'id': 'S1', 'name': 'wilder', 'method': 'Wilder 平滑；損失為 0 且有漲幅時 100，全平回 null'},
                       {'id': 'S2', 'name': 'cutler_sma', 'method': '增益與損失取 SMA，不滿窗 null'},
                       {'id': 'S3',
                        'name': 'explicit_null_on_saturation',
                        'method': '同 Cutler，但損失為 0 或全平時回 null，不輸出 100/50 冒充訊號'}],
         'window': 14},
 'macd': {'stable_id': 'VQG.IND.MACD',
          'formula': 'MACD = EMA12-EMA26 ; signal = EMA9(MACD)',
          'solutions': [{'id': 'S1', 'name': 'ema_12_26_9', 'method': '標準 EMA MACD，未滿 26+信號暖機則 signal null'},
                        {'id': 'S2', 'name': 'sma_12_26_9', 'method': 'SMA 差與 SMA 信號，定義不同，只供分歧檢測'},
                        {'id': 'S3', 'name': 'withhold_if_short', 'method': '樣本不足或三解分歧超公差則整組 null，不外推'}],
          'window': 26},
 'bollinger': {'stable_id': 'VQG.IND.BOLLINGER',
               'formula': 'mid = SMA_n ; band = mid +/- k*stdev',
               'solutions': [{'id': 'S1', 'name': 'sample_k2', 'method': 'SMA 與樣本標準差，k=2，未滿窗 null'},
                             {'id': 'S2', 'name': 'population_k2', 'method': '改用母體標準差，寬度略窄'},
                             {'id': 'S3', 'name': 'robust_mad', 'method': '中位數 +/- 2*1.4826*MAD；MAD=0 回 null'}],
               'window': 20},
 'roc': {'stable_id': 'VQG.IND.ROC',
         'formula': 'ROC_n = p_t/p_{t-n}-1',
         'solutions': [{'id': 'S1', 'name': 'simple_fixed_lag', 'method': '只在恰好 n 根前有有效價時計算'},
                       {'id': 'S2', 'name': 'log_fixed_lag', 'method': '同 lag 的對數報酬'},
                       {'id': 'S3', 'name': 'reject_stale_base', 'method': '基期缺失即 null，禁止改抓更早價格'}],
         'window': 20},
 'slope': {'stable_id': 'VQG.IND.SLOPE',
           'formula': 'OLS slope of adj_close on 0..n-1',
           'solutions': [{'id': 'S1', 'name': 'ols_price', 'method': '等距交易日 OLS；視窗內有缺日則 null'},
                         {'id': 'S2', 'name': 'ols_log', 'method': '對 ln(price) 做 OLS，單位改為對數斜率'},
                         {'id': 'S3', 'name': 'theil_sen', 'method': '兩兩斜率中位數；少於 3 點 null'}],
           'window': 20},
 'drawdown': {'stable_id': 'VQG.IND.DRAWDOWN',
              'formula': 'p_t/running_peak - 1, peak causal',
              'solutions': [{'id': 'S1', 'name': 'causal_peak', 'method': '峰值只含當下與過去有效價'},
                            {'id': 'S2', 'name': 'window_peak_20', 'method': '只在近 20 個有效價內取峰值'},
                            {'id': 'S3', 'name': 'reset_on_gap', 'method': '價格缺日後峰值重設，不跨缺口沿用'}]},
 'volume_zscore': {'stable_id': 'VQG.IND.VOLUME_ZSCORE',
                   'formula': 'zscore of clean_volume',
                   'solutions': [{'id': 'S1', 'name': 'clean_sample_z', 'method': '台股扣當沖；壞列 null；樣本 z'},
                                 {'id': 'S2', 'name': 'log1p_z', 'method': '對 log1p(clean_volume) 做樣本 z，減輕右偏'},
                                 {'id': 'S3', 'name': 'robust_or_null', 'method': 'MAD z；全零或壞列比例過高則整窗 null'}],
                   'window': 20},
 'beta': {'stable_id': 'VQG.IND.BETA',
          'formula': 'beta = cov(r, r_b) / var(r_b)',
          'solutions': [{'id': 'S1', 'name': 'aligned_ols', 'method': '僅在兩邊都有有效報酬的日期計算'},
                        {'id': 'S2', 'name': 'downside_beta', 'method': '只取基準報酬 < 0 的子集；子集 < 5 則 null'},
                        {'id': 'S3', 'name': 'withhold_if_no_benchmark', 'method': '無基準或市場錯配則 null，禁止用美股填台股'}],
          'window': 20}}


LIMIT = MAX_INPUT_ROWS
MAX_TTL_DAYS = 30
CACHE_NAME = 'vqg_internal_v0104.duckdb'

# None 表示完整因果前綴；整數是視窗之外的歷史根數。
EXTRA = {'summary':None,'returns':None,'sma':None,'ema':None,'volatility':1,'zscore':0,
         'rsi':None,'macd':None,'bollinger':0,'roc':1,'slope':0,'drawdown':None,'volume_zscore':0,'beta':1}
OPTIONAL = {'volume_zscore':['clean_volume','volume','daytrade_volume'], 'beta':['benchmark_adj_close','benchmark_market']}
PRICE_KEYS = ['ticker','date','session_index','market','adj_close','available_on']
REPORT_KEYS = ['report_id','ticker','report_date','available_on']
FIXED = {'summary','returns','macd'}
FIELDS = {'request_key':'VARCHAR','solution_id':'VARCHAR','link_id':'VARCHAR','report_id':'VARCHAR',
          'report_link':'VARCHAR','report_date':'DATE','report_available_on':'DATE','ticker':'VARCHAR','as_of':'DATE','observation_date':'DATE','indicator_id':'VARCHAR',
          'window_n':'INTEGER','estimator':'VARCHAR','value_num':'DOUBLE','value_json':'VARCHAR',
          'unit':'VARCHAR','valid':'BOOLEAN','invalid_reason':'VARCHAR','verdict':'VARCHAR',
          'coverage':'DOUBLE','input_sha256':'VARCHAR','formula_sha256':'VARCHAR','engine_version':'VARCHAR'}




SPECIAL = {'rsi':14,'summary':20,'returns':2,'macd':26}
INDEX_IDS = {'TWSE':('^TWII','TAIEX','TWSE','加權指數','發行量加權股價指數'),
             'TPEX':('^TWOII','TPEX','OTC','櫃買指數','櫃檯指數')}
COLUMN_ALIASES = {
 'date':('date','trade_date','交易日期','日期','交易日'),
 'ticker':('yf_ticker','yahoo_finance_ticker','ticker_symbol','ticker','stock_id','code','證券代號','股票代號','指數代號'),
 'market':('market','exchange','市場','交易所'), 'session_index':('session_index','交易日序號'),
 'available_on':('available_on','published_date','release_date','公告日期','首次可用日'),
 'adj_close':('adj_close','adjusted_close','還原收盤價','調整後收盤價'),
 'volume':('volume','trading_volume','trade_volume','成交股數','總成交股數'),
 'turnover':('turnover','trading_value','trade_value','成交金額','成交值','總成交金額'),
 'daytrade_volume':('daytrade_volume','day_trade_volume','當沖成交股數','當日沖銷交易成交股數','當沖量'),
 'daytrade_turnover':('daytrade_turnover','daytrade_value','day_trade_value','當沖成交金額','當日沖銷成交金額','當沖成交值'),
 'clean_volume':('clean_volume','non_day_trade_volume','volume(扣當沖)','成交量(扣當沖)'),
 'clean_turnover':('clean_turnover','clean_value','turnover(扣當沖)','成交值(扣當沖)'),
 'benchmark_market':('benchmark_market',),'benchmark_adj_close':('benchmark_adj_close',),
 'report_id':('report_id','file_name'),'report_date':('report_date',),
 'month':('month','year_month','revenue_month','資料年月','營收年月'),
 'monthly_revenue':('monthly_revenue','revenue','當月營收','當月營業收入','本月營收'),
}
FLOW = ('volume','turnover','daytrade_volume','daytrade_turnover','clean_volume','clean_turnover')


def _polars():
    import polars as pl
    return pl

def _series(values):
    return _polars().Series(values, dtype=_polars().Float64)

def _finite(s):
    return s.zip_with(s.is_finite().fill_null(False), _series([None] * len(s)))

def _price(s):
    return _finite(s.cast(_polars().Float64)).zip_with(s.cast(_polars().Float64) > 0, _series([None] * len(s)))

def _divide(a, b):
    return _finite(a / b).zip_with(b != 0, _series([None] * len(b)))

def _rolling(s, n, kind='mean', minimum=None, ddof=1):
    fn = getattr(s, 'rolling_' + kind)
    kwargs = {'window_size': n, 'min_samples': n if minimum is None else minimum}
    if kind == 'std':
        kwargs['ddof'] = ddof
    return fn(**kwargs)

def _seeded_ema(s, n, alpha=None, first=False):
    """Explicit SMA seed followed by native Polars ewm_mean; reseed after null."""
    values, out, start = s.to_list(), [None] * len(s), 0
    while start < len(values):
        if values[start] is None:
            start += 1
            continue
        end = start
        while end < len(values) and values[end] is not None:
            end += 1
        segment = s.slice(start, end-start)
        warm = 1 if first else n
        if len(segment) >= warm:
            seed = segment[0] if first else segment.head(n).mean()
            native = _series([seed] + segment.slice(warm).to_list()).ewm_mean(
                alpha=alpha or 2/(n+1), adjust=False, min_samples=1, ignore_nulls=False)
            out[start+warm-1:end] = native.to_list()
        start = end
    return _finite(_series(out))

def _mad(s, n):
    return s.rolling_map(lambda a: (a-a.median()).abs().median(), window_size=n, min_samples=n)

def _z(s, n, population=False, flat_zero=False):
    mean, std = _rolling(s,n), _rolling(s,n,'std',ddof=0 if population else 1)
    z = _divide(s-mean, std)
    if flat_zero:
        z = _series([0.0]*len(s)).zip_with((std == 0) & s.is_not_null(), z)
    return z

def _robust_z(s,n):
    return _divide(MAD_Z_SCALE*(s-_rolling(s,n,'median')), _mad(s,n))

def _compressed(s,n,kind):
    valid = s.drop_nulls()
    calc = _rolling(valid,n,kind).to_list()
    it = iter(calc)
    return _series([next(it) if v is not None else None for v in s.to_list()])

def _rsi(gain,loss,strict_saturation=False):
    result = _divide(100*gain, gain+loss)
    if strict_saturation:
        result = result.zip_with(loss > 0, _series([None]*len(loss)))
    return result

def _slope(s,n,log=False,robust=False):
    if n < 3:
        return _series([None]*len(s))
    x = _series(range(n)); center = x-x.mean(); denom=(center*center).sum()
    def calc(a):
        if robust:
            vals=a.to_list()
            return _series([(vals[j]-vals[i])/(j-i) for i in range(n) for j in range(i+1,n)]).median()
        return ((a-a.mean())*center).sum()/denom
    return (s.log() if log else s).rolling_map(calc,window_size=n,min_samples=n)

def _beta(r,b,n,downside=False):
    # Pairwise mask before every statistic; never use independently compressed arrays.
    valid = r.is_not_null() & b.is_not_null()
    if downside:
        valid = valid & (b < 0)
    null = _series([None]*len(r)); a=r.zip_with(valid,null); x=b.zip_with(valid,null)
    count=valid.cast(_polars().Float64).rolling_sum(window_size=n,min_samples=n)
    ex=_rolling(x,n,minimum=1); ea=_rolling(a,n,minimum=1)
    var=_rolling(x*x,n,minimum=1)-ex*ex
    cov=_rolling(a*x,n,minimum=1)-ea*ex
    result=_divide(cov,var)
    return result.zip_with((count >= (DOWNSIDE_MIN if downside else n)) & (var > 0),null)

def _last(value):
    if isinstance(value,dict):
        return {k:_last(v) for k,v in value.items()}
    v=value[-1]
    return float(v) if v is not None and math.isfinite(v) else None

def _numbers(value):
    if isinstance(value,dict):
        return list(value.values())
    return [value]

def _verdict(metric, values):
    if not all(all(v is not None for v in _numbers(x)) for x in values):
        return 'PARTIAL' if any(any(v is not None for v in _numbers(x)) for x in values) else 'WITHHELD'
    # Different units/estimators are explicitly not claimed to agree.
    if metric in NONCOMPARABLE:
        return 'NOT_COMPARABLE'
    triples=list(zip(*[_numbers(x) for x in values]))
    return 'AGREE' if all(max(x)-min(x)<=ABS_TOL+REL_TOL*max(abs(v) for v in x) for x in triples) else 'DIVERGE'

def validate_frame(frame, context, window=None):
    pl=_polars()
    if context.get('entry')!='VCGC' or context.get('owner') not in ('VDF','VRN'):
        raise ValueError('VCGC_OWNER_REQUIRED')
    if context.get('source_type') not in ('parquet','duckdb','sqlite'):
        raise ValueError('SOURCE_TYPE_DENIED')
    if context.get('purpose') not in ('technical_analysis','statistics'):
        raise ValueError('PURPOSE_DENIED')
    if context.get('frequency')!='daily' or context.get('calendar_verified') is not True:
        raise ValueError('VERIFIED_DAILY_CALENDAR_REQUIRED')
    if not context.get('link_id') or context.get('price_field')!='adj_close':
        raise ValueError('ADJUSTED_PRICE_AND_LINK_REQUIRED')
    if context.get('mode') not in ('offline_fixture','local_readonly'):
        raise ValueError('PRODUCTION_BLOCKED_PENDING_VCGC_SOURCE_BINDING')
    if window is not None and (isinstance(window,bool) or not isinstance(window,int) or not 2<=window<=MAX_WINDOW):
        raise ValueError('WINDOW_OUT_OF_RANGE')
    required={'ticker','date','market','session_index','adj_close'}
    if not required.issubset(frame.columns):
        raise ValueError('SCHEMA_MISSING:'+','.join(sorted(required-set(frame.columns))))
    if not 0<frame.height<=MAX_INPUT_ROWS:
        raise ValueError('INPUT_ROWS_OUT_OF_RANGE')
    if frame.select(pl.struct('ticker','date').is_duplicated().any()).item():
        raise ValueError('DUPLICATE_TICKER_DATE')
    for column in ('ticker','date','market','session_index'):
        if frame[column].null_count():
            raise ValueError('NULL_IDENTITY:'+column)
    if not frame.schema['session_index'].is_integer():
        raise ValueError('SESSION_INDEX_MUST_BE_INTEGER')
    if frame.schema['date']!=pl.Date:
        raise ValueError('DATE_TYPE_REQUIRED')
    if frame.filter(~pl.col('market').is_in(['TW','US'])).height:
        raise ValueError('UNSUPPORTED_MARKET')
    result=frame.sort(['ticker','date'])
    for part in result.partition_by('ticker',maintain_order=True):
        if part['market'].n_unique()!=1:
            raise ValueError('MIXED_MARKET')
        if any(x!=1 for x in part['session_index'].diff().drop_nulls().to_list()):
            raise ValueError('OMITTED_SESSION_INSERT_EXPLICIT_NULL_UPSTREAM')
    return result

def fixture(days=90):
    pl=_polars();values=[100+0.2*i+3*math.sin(i/3) for i in range(days)]
    return pl.DataFrame({'ticker':['TEST.TW']*days,'date':[date(2026,1,1)+timedelta(days=i) for i in range(days)],
        'market':['TW']*days,'session_index':range(days),'adj_close':values,
        'benchmark_adj_close':values,'benchmark_market':['TW']*days,
        'volume':[1000.+i*4+20*math.sin(i) for i in range(days)],'daytrade_volume':[100.]*days})

def summary(frame, n):
    p = _price(frame['adj_close']).drop_nulls()
    count = len(p)
    return (dict(mean=p.mean(), min=p.min(), max=p.max(), pstdev=p.std(ddof=0), count=count),
            dict(median=p.median(), mad=(p-p.median()).abs().median() if count else None, count=count),
            dict(latest=None, count=count))

def returns(frame, n):
    p = _price(frame['adj_close'])
    simple = _last(_divide(p, p.shift(1)) - 1)
    log_return = _last(_finite(p.log() - p.shift(1).log()))
    previous = p.head(len(p)-1).drop_nulls()
    gap = None
    if len(p) > 1 and p[-1] is not None and p[-2] is None and len(previous):
        gap = p[-1] / previous[-1] - 1
    return simple, log_return, dict(adjacent=simple, gap_return=gap)

def sma(frame, n):
    p = _price(frame['adj_close'])
    return tuple(_last(x) for x in (_rolling(p,n), _rolling(p,n,minimum=1),
                                          _compressed(p,n,'mean')))

def ema(frame, n):
    p = _price(frame['adj_close'])
    return tuple(_last(x) for x in (_seeded_ema(p,n), _seeded_ema(p,n,first=True),
                                          _seeded_ema(p,n,alpha=1/n)))

def volatility(frame, n):
    p = _price(frame['adj_close'])
    r = _divide(p,p.shift(1)) - 1
    log_r = _finite(p.log() - p.shift(1).log())
    return tuple(_last(x) for x in (_rolling(r,n,'std'), _rolling(r,n,'std',ddof=0),
                                          _rolling(log_r,n,'std')))

def zscore(frame, n):
    p = _price(frame['adj_close'])
    return tuple(_last(x) for x in (_z(p,n), _z(p,n,population=True,flat_zero=True),
                                          _robust_z(p,n)))

def rsi(frame, n):
    p = _price(frame['adj_close'])
    delta = p - p.shift(1)
    gain, loss = delta.clip(lower_bound=0), (-delta).clip(lower_bound=0)
    g, l = _rolling(gain,n), _rolling(loss,n)
    return tuple(_last(x) for x in (_rsi(_seeded_ema(gain,n,1/n),_seeded_ema(loss,n,1/n)),
                                          _rsi(g,l), _rsi(g,l,True)))

def macd(frame, n):
    p = _price(frame['adj_close'])
    e = _seeded_ema(p,MACD_FAST) - _seeded_ema(p,MACD_SLOW)
    s = _rolling(p,MACD_FAST) - _rolling(p,MACD_SLOW)
    es, ss = _seeded_ema(e,MACD_SIGNAL), _rolling(s,MACD_SIGNAL)
    first = _last(dict(line=e,signal=es,histogram=e-es))
    second = _last(dict(line=s,signal=ss,histogram=s-ss))
    agree = all(a is not None and b is not None and abs(a-b) <= ABS_TOL + REL_TOL*abs(b)
                for a,b in zip(first.values(), second.values()))
    return first, second, {k: v if agree else None for k,v in first.items()}

def bollinger(frame, n):
    p = _price(frame['adj_close'])
    mean, med = _rolling(p,n), _rolling(p,n,'median')
    mad = _mad(p,n)
    results = []
    for center, width in [(mean,_rolling(p,n,'std')), (mean,_rolling(p,n,'std',ddof=0)),
                          (med,MAD_SIGMA*mad)]:
        results.append(_last(dict(mid=center,upper=center+BAND_K*width,lower=center-BAND_K*width)))
    if mad[-1] is None or mad[-1] <= 0:
        results[2] = dict.fromkeys(results[2])
    return tuple(results)

def roc(frame, n):
    p = _price(frame['adj_close'])
    simple = _last(_divide(p,p.shift(n))-1)
    return simple, _last(_finite(p.log()-p.shift(n).log())), simple

def slope(frame, n):
    p = _price(frame['adj_close'])
    return tuple(_last(x) for x in (_slope(p,n), _slope(p,n,log=True), _slope(p,n,robust=True)))

def drawdown(frame, n):
    p = _price(frame['adj_close'])
    if p[-1] is None:
        return None, None, None
    high = p[-1]
    for value in reversed(p.to_list()):
        if value is None:
            break
        high = max(high, value)
    return (p[-1]/p.max()-1, _last(_divide(p,_compressed(p,n,'max'))-1), p[-1]/high-1)

def volume_zscore(frame, n):
    volume = net_series(frame,'volume')
    return tuple(_last(x) for x in (_z(volume,n), _z(volume.log1p(),n), _robust_z(volume,n)))

def beta(frame, n):
    if not {'benchmark_adj_close','benchmark_market'}.issubset(frame.columns):
        return None, None, None
    if frame['benchmark_market'].n_unique() != 1 or frame['benchmark_market'][0] != frame['market'][0]:
        return None, None, None
    p, bp = _price(frame['adj_close']), _price(frame['benchmark_adj_close'])
    r, b = _divide(p,p.shift(1))-1, _divide(bp,bp.shift(1))-1
    full = _last(_beta(r,b,n))
    return full, _last(_beta(r,b,n,True)), full

def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',',':'), allow_nan=False, default=str)

def sha(value):
    return hashlib.sha256(value).hexdigest()

def formula_id(metric):
    # Exclude unrelated indicator functions; a change to shared machinery invalidates all.
    parts = [SHARED_HASH, CORE[metric], inspect.getsource(globals()[metric]), pl.__version__,duckdb.__version__]
    return sha(canonical(parts).encode())

def source(binding, producer, keys):
    path = Path(binding['path']).resolve(strict=True)
    root = Path(binding['vdf_root']).resolve(strict=True)
    if (binding.get('producer') != producer or binding.get('custodian') != 'VDF' or
        binding.get('mode') not in ('offline_fixture','local_readonly') or not binding.get('link_id') or
        path.suffix.lower() != '.parquet' or not path.is_file() or not path.is_relative_to(root)):
        raise ValueError('UNBOUND_SOURCE')
    # 只開啟確切的本地單檔。禁用 DuckDB 檔名 glob，防止匹配額外檔案。
    if any(ch in str(path) for ch in '*?[]'):
        raise ValueError('EXACT_PATH_REQUIRED')
    mapping = {key:binding.get('columns',{}).get(key,key) for key in keys}
    if mapping.get('adj_close','').strip().casefold() in {'close','收盤價','收盤'}:
        raise ValueError('UNADJUSTED_PRICE_BLOCKED')
    schema = pl.read_parquet_schema(path)
    missing = set(mapping.values()) - set(schema)
    if missing:
        raise ValueError('MISSING_COLUMNS: '+','.join(sorted(missing)))
    if len(set(mapping.values())) != len(mapping):
        raise ValueError('DUPLICATE_MAPPING')
    for field in ('date','available_on','report_date'):
        if field in mapping and schema[mapping[field]] != pl.Date:
            raise ValueError('DATE_COLUMN_REQUIRED: '+field)
    return path, mapping, schema

def ident(name):
    return '"' + name.replace('"','""') + '"'

def report_anchor(conn, binding, report_id, as_of):
    path, m, _ = source(binding,'VRN',REPORT_KEYS)
    rows = conn.execute(f'SELECT {ident(m["ticker"])},{ident(m["report_date"])},{ident(m["available_on"])} '
                f'FROM read_parquet(?) WHERE {ident(m["report_id"])}=? AND {ident(m["available_on"])}<=? LIMIT 2',
                [str(path), report_id, as_of]).fetchall()
    if len(rows) != 1 or not rows[0][0] or rows[0][1] is None or rows[0][1] > rows[0][2]:
        raise ValueError('REPORT_MISSING_AMBIGUOUS_OR_FUTURE')
    return rows[0]

def read_prices(conn, binding, specs, ticker, cutoff, budget):
    path, mapping, schema = source(binding,'VDF',PRICE_KEYS)
    if binding.get('calendar_verified') is not True or binding.get('frequency') != 'daily':
        raise ValueError('VERIFIED_DAILY_CALENDAR_REQUIRED')
    for key in sorted({col for metric in specs for col in OPTIONAL.get(metric, [])}):
        name = binding.get('columns',{}).get(key,key)
        if name in schema:
            mapping[key] = name
    cols = ','.join(f'{ident(raw)} AS {ident(key)}' for key,raw in mapping.items())
    # SMA S3 與 gap return 可能需要更早的有效價。先查最短前綴，遇缺值才擴讀。
    flexible = {'sma','returns'}
    full = any(EXTRA[m] is None and m not in flexible for m in specs)
    widths = {m:(2 if m=='returns' else n+(EXTRA[m] or 0)) for m,n in specs.items()}
    nrows = budget if full else max(widths.values())
    # 多讀一根檢查截斷處同日重複；完整前綴超限不得任意截斷 EMA 種子。
    sql = f'''SELECT {cols} FROM read_parquet(?) WHERE {ident(mapping['ticker'])}=?
      AND {ident(mapping['date'])}<=? AND {ident(mapping['available_on'])}<=?
      AND ({ident(mapping['market'])}<>'TW' OR {ident(mapping['date'])}<?)
      ORDER BY {ident(mapping['date'])} DESC LIMIT ?'''
    def fetch(size):
        rows = conn.execute(sql,[str(path),ticker,cutoff,cutoff,cutoff,size+1]).fetchall()
        return pl.DataFrame(rows,schema={k:schema[v] for k,v in mapping.items()},orient='row')

    frame = fetch(nrows)
    if not full and len(frame)>nrows and any(
        _price(frame.head(widths[m])['adj_close']).null_count() for m in flexible.intersection(specs)
    ):
        nrows, full = budget, True
        frame = fetch(nrows)
    if len(frame) > nrows and (full or frame['date'][nrows-1] == frame['date'][nrows]):
        raise ValueError('HISTORY_LIMIT_OR_DUPLICATE_BOUNDARY')
    frame = frame.head(nrows).reverse()
    if len(frame) == 0:
        raise ValueError('NO_VISIBLE_PRICE')
    if (frame['available_on'] < frame['date']).any():
        raise ValueError('INVALID_AVAILABILITY')
    return validate_frame(frame,{**FIXTURE_CONTEXT,'mode':binding['mode'],'link_id':binding['link_id']})

def coverage(frame, metric, n):
    tail = frame.tail(n)
    if metric == 'volume_zscore':
        return net_series(tail,'volume').is_not_null().sum()/n
    if metric == 'beta':
        if not {'benchmark_market','benchmark_adj_close'}.issubset(tail.columns):
            return 0.0
        if (tail['benchmark_market']!=tail['market']).fill_null(True).any():
            return 0.0
        p, b = _price(frame['adj_close']), _price(frame['benchmark_adj_close'])
        mask = p.is_not_null() & b.is_not_null()
        return (mask & mask.shift(1)).tail(n).fill_null(False).sum()/n
    need = 2 if metric == 'returns' else n+1 if metric in {'roc','volatility','rsi'} else n
    if metric == 'summary':
        need = len(frame)
    return _price(frame.tail(need)['adj_close']).is_not_null().sum()/need

def units(metric, i):
    if metric in {'summary','macd'}:
        return 'component_specific'
    if metric in {'sma','ema','bollinger'}:
        return 'price'
    if metric=='slope':
        return 'log_price_per_session' if i==1 else 'price_per_session'
    if metric in {'roc','returns','volatility','drawdown'}:
        return 'log_return' if i==1 and metric in {'returns','roc'} else 'fraction'
    return 'rsi_points' if metric=='rsi' else 'dimensionless'

def make_rows(frame, metric, n, common):
    values = globals()[metric](frame,n)
    verdict = _verdict(metric,values)
    cov = coverage(frame,metric,n)
    if metric=='rsi' and values[:2] == (100.0,100.0) and values[2] is None:
        verdict = 'DIVERGE'
    elif metric=='sma' and (cov<1 or frame['adj_close'][-1] is None):
        verdict = 'PARTIAL' if any(v is not None for v in values) else 'WITHHELD'
    elif metric=='returns' and values[0] is not None and values[1] is not None:
        verdict = 'NOT_COMPARABLE'
    elif metric in {'ema','drawdown','bollinger','zscore','macd','rsi'} and verdict in {'AGREE','DIVERGE'}:
        verdict = 'NOT_COMPARABLE'
    rows = []
    for i,value in enumerate(values):
        nums = _numbers(value)
        valid = all(x is not None and math.isfinite(x) for x in nums)
        if metric=='returns' and i==2:
            valid = any(x is not None and math.isfinite(x) for x in nums)
        reason = None if valid else 'WARMUP_MISSING_OR_DEGENERATE'
        if metric=='summary' and i==2:
            reason = 'RAW_LAST_PRICE_WITHHELD'
        rows.append(dict(common,solution_id=f'S{i+1}',estimator=CORE[metric]['solutions'][i]['name'],
                         value_num=value if isinstance(value,(int,float)) else None,
                         value_json=canonical(value),unit=units(metric,i),valid=valid,
                         invalid_reason=reason,verdict=verdict,coverage=cov))
    return rows

def open_cache(directory, roots):
    path = Path(directory).resolve()/CACHE_NAME
    if any(path.is_relative_to(Path(r).resolve()) for r in roots):
        raise ValueError('CACHE_INSIDE_SOURCE_ROOT')
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.resolve() != path:
        raise ValueError('CACHE_LINK_DENIED')
    conn = duckdb.connect(str(path))
    columns = ','.join(f'{ident(k)} {v}' for k,v in FIELDS.items())
    conn.execute(f'CREATE TABLE IF NOT EXISTS vqg_result ({columns},expires_on DATE NOT NULL,'
                 'PRIMARY KEY(request_key,solution_id))')
    return conn

def calculate(request, resolve, *, cache_dir=None, ttl_days=7):
    """VCGC 呼叫端提供可信 resolve(link_id)。正式接線仍受上游 production gate 管控。"""
    if request.get('mode') not in ('offline_fixture','local_readonly'):
        raise ValueError('PRODUCTION_BLOCKED_PENDING_VCGC_SOURCE_BINDING')
    if type(ttl_days) is not int or not 1 <= ttl_days <= MAX_TTL_DAYS:
        raise ValueError('TTL_OUT_OF_RANGE')
    as_of = date.fromisoformat(request['as_of'])
    metrics = request['metrics']
    if not isinstance(metrics,list) or not metrics or len(metrics)!=len(set(metrics)) or set(metrics)-CORE.keys():
        raise ValueError('EXPLICIT_UNIQUE_CORE_METRICS_REQUIRED')
    windows = request.get('windows',{})
    if set(windows)-set(metrics) or set(windows)&FIXED:
        raise ValueError('INVALID_WINDOW_OVERRIDE')
    price_link = request['price_link']
    binding = resolve(price_link)
    if binding['link_id']!=price_link:
        raise ValueError('LINK_MISMATCH')
    bindings = [binding]
    report_id = request.get('report_id')
    if bool(report_id)!=bool(request.get('report_link')):
        raise ValueError('REPORT_LINK_AND_ID_REQUIRED')
    with closing(duckdb.connect()) as scan:
        cutoff, ticker = as_of, request.get('ticker')
        anchor = None
        if report_id:
            report = resolve(request['report_link'])
            if report['link_id'] != request['report_link']:
                raise ValueError('LINK_MISMATCH')
            bindings.append(report)
            anchor = report_anchor(scan,report,report_id,as_of)
            if ticker is not None and ticker != anchor[0]:
                raise ValueError('REPORT_TICKER_MISMATCH')
            ticker, cutoff, _ = anchor
        if not isinstance(ticker,str) or not ticker.strip():
            raise ValueError('TICKER_REQUIRED')
        plan = window_plan(metrics,windows)
        specs = {m:max(n for key,n in plan if key==m) for m in metrics}
        data = read_prices(scan,binding,specs,ticker,cutoff,LIMIT-int(bool(anchor)))
        cache = open_cache(cache_dir,[b['vdf_root'] for b in bindings]) if cache_dir else None
        output, executed, hits = [], [], []
        try:
            if cache:
                cache.begin()
                cache.execute('DELETE FROM vqg_result WHERE expires_on<=current_date')
            for metric,n in plan:
                columns = PRICE_KEYS+[k for k in OPTIONAL.get(metric,[]) if k in data.columns]
                frame = data.select(columns)
                if EXTRA[metric] is not None:
                    frame = frame.tail(n+EXTRA[metric])
                elif metric in {'sma','returns'}:
                    needed = n if metric=='sma' else 2
                    valid = _price(frame['adj_close']).is_not_null().to_list()
                    indices = [index for index,ok in enumerate(valid) if ok]
                    if len(indices)>=needed:
                        frame = frame.slice(indices[-needed])
                inputs = sha((frame.write_json()+canonical([anchor,price_link,request.get('report_link')])).encode())
                formula = formula_id(metric)
                logical_key = sha(canonical([price_link,request.get('report_link'),report_id,ticker,
                                             as_of,metric,n]).encode())
                if cache:
                    cur = cache.execute('SELECT '+','.join(FIELDS)+' FROM vqg_result WHERE '
                        'request_key=? AND input_sha256=? AND formula_sha256=? ORDER BY solution_id',
                        [logical_key,inputs,formula])
                    match = [dict(zip(FIELDS,row)) for row in cur.fetchall()]
                    if len(match)==3:
                        output.extend(match)
                        hits.append(metric)
                        continue
                common = dict(request_key=logical_key,link_id=price_link,report_id=report_id,ticker=ticker,
                              report_link=request.get('report_link'),report_date=anchor[1] if anchor else None,
                              report_available_on=anchor[2] if anchor else None,
                              as_of=as_of,observation_date=frame['date'][-1],indicator_id=CORE[metric]['stable_id'],
                              window_n=n,engine_version=VERSION,input_sha256=inputs,formula_sha256=formula)
                rows = make_rows(frame,metric,n,common)
                if cache:
                    cache.execute('DELETE FROM vqg_result WHERE request_key=?',[logical_key])
                    marks = ','.join('?' for _ in range(len(FIELDS)+1))
                    cache.executemany('INSERT INTO vqg_result VALUES ('+marks+')',
                        [[r[k] for k in FIELDS]+[date.today()+timedelta(days=ttl_days)] for r in rows])
                output.extend(rows)
                executed.append(metric)
            if cache:
                cache.commit()
        finally:
            if cache:
                cache.close()
    return output,dict(executed=executed,cache_hits=hits)

def export_snapshot(rows, parent):
    """僅封存本次非空衍生資料。兩檔完成後才以 rename 對外可見。"""
    import shutil
    import uuid
    parent = Path(parent)
    parent.mkdir(parents=True,exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix='.vqg-',dir=parent))
    try:
        frame = pl.DataFrame(rows,schema={k:{'VARCHAR':pl.String,'DOUBLE':pl.Float64,'DATE':pl.Date,
                              'BOOLEAN':pl.Boolean,'INTEGER':pl.Int32}[t] for k,t in FIELDS.items()})
        frame.write_parquet(stage/'vqg_result.parquet',compression='zstd')
        frame.write_csv(stage/'vqg_result.csv',include_bom=True,date_format='%Y/%m/%d')
        target = parent/('vqg_'+uuid.uuid4().hex)
        stage.rename(target)
        return target
    finally:
        if stage.exists():
            shutil.rmtree(stage)

def window_plan(metrics, windows):
    plan = []
    for m in metrics:
        values = windows.get(m, (SPECIAL[m],) if m in SPECIAL else DEFAULT_WINDOWS)
        if isinstance(values,int):
            values = [values]
        if not values or any(type(n)!=int or not 2<=n<=MAX_WINDOW for n in values) or len(set(values))!=len(values):
            raise ValueError('INVALID_WINDOWS')
        plan.extend((m,n) for n in values)
    if len(plan)*3>MAX_OUTPUT_ROWS:
        raise ValueError('OUTPUT_LIMIT: 請分批指定指標，或縮減 --windows')
    return plan


def net_series(frame, key):
    """同一口徑、同一單位的總額與當沖相減；已扣欄位不再扣第二次。"""
    def column(name):
        if name in frame.columns:
            return _finite(frame[name].cast(pl.Float64,strict=False))
        return _series([None]*frame.height)
    total, dt, supplied = column(key),column('daytrade_'+key),column('clean_'+key)
    derived = total-dt
    known = total.is_not_null() & dt.is_not_null()
    invalid = (total<0).fill_null(False) | (dt<0).fill_null(False) | (dt>total).fill_null(False)
    invalid |= (supplied<0).fill_null(False) | (supplied>total).fill_null(False)
    invalid |= (known & supplied.is_not_null() & ((supplied-derived).abs()>1e-6)).fill_null(False)
    net = supplied.fill_null(derived)
    return net.zip_with(~invalid,_series([None]*frame.height))


def norm(value):
    return re.sub(r'[\s_()（）\-]','',unicodedata.normalize('NFKC',str(value)).casefold())


def discover(root):
    root = Path(root).expanduser().resolve(strict=True)
    if not root.is_dir():
        raise ValueError('VDF_ROOT_NOT_DIRECTORY')
    sources,errors = [],[]
    for path in sorted(root.rglob('*')):
        if path.suffix.lower()!='.parquet' or not path.resolve().is_relative_to(root):
            continue
        try:
            schema = pl.read_parquet_schema(path)
            by_name = {norm(c):c for c in schema}
            if len(by_name)!=len(schema):
                raise ValueError('AMBIGUOUS_NORMALIZED_COLUMNS')
            cols = {k:next(by_name[norm(a)] for a in aliases if norm(a) in by_name)
                    for k,aliases in COLUMN_ALIASES.items() if any(norm(a) in by_name for a in aliases)}
            if cols:
                sources.append((path,cols))
        except Exception as exc:
            errors.append((str(path.relative_to(root)),type(exc).__name__))
    return sources,errors


def symbol_aliases(symbol):
    for ids in INDEX_IDS.values():
        if symbol.upper() in ids:
            return ids
    # 台灣數字代碼依 VDF 股票命名。外國市場不去除後綴。
    if re.fullmatch(r'\d{4,6}[A-Z]?\.(TW|TWO)',symbol.upper()):
        return symbol.upper(),symbol.upper().split('.')[0]
    return (symbol.upper(),)


def date_expr(col,monthly=False):
    raw = pl.col(col).cast(pl.String).str.strip_chars().str.replace_all('/','-')
    if monthly:
        raw = pl.when(raw.str.contains(r'^\d{6}$')).then(raw.str.slice(0,4)+'-'+raw.str.slice(4,2)).otherwise(raw)
        raw = pl.when(raw.str.contains(r'^\d{4}-\d{2}$')).then(raw+'-01').otherwise(raw)
    return pl.coalesce(raw.str.strptime(pl.Date,'%Y-%m-%d',strict=False),
                       raw.str.strptime(pl.Date,'%Y%m%d',strict=False))


def load_series(sources,symbol,fields,as_of,start=None,kind='daily',available_cutoff=True,tail_rows=None):
    """依商品與日期篩選再收集。多檔以日期合併；衝突拒絕，不任選版本。"""
    records = {}
    for path,cols in sources:
        if 'report_id' in cols and 'report_date' in cols:
            continue  # VRN provides report anchors and never substitutes for a market feed.
        is_month = 'monthly_revenue' in cols
        if kind=='monthly' and not is_month or kind=='daily' and is_month:
            continue
        date_key = 'month' if kind=='monthly' and 'month' in cols else 'date'
        keys = [k for k in fields if k in cols]
        if date_key not in cols or not keys or not set(keys)-{'market','session_index','available_on'}:
            continue
        aliases = symbol_aliases(symbol)
        if 'ticker' in cols:
            match = pl.col(cols['ticker']).cast(pl.String).str.to_uppercase().is_in(aliases)
        elif 'market' in cols and any(symbol.upper() in ids for ids in INDEX_IDS.values()) and re.search(
                r'market|index|指數|大盤', path.stem,re.I):
            # 僅限有市場別的市場彙總表，絕不拿單一個股或 ETF 代替指數。
            match = pl.col(cols['market']).cast(pl.String).str.to_uppercase().is_in(aliases)
        else:
            continue
        dt = date_expr(cols[date_key],kind=='monthly')
        if kind=='monthly':
            dt = dt.dt.month_end()
        query = pl.scan_parquet(path).filter(match)
        if kind=='monthly' and available_cutoff and 'available_on' not in cols:
            if query.limit(1).collect().height:
                raise ValueError(f'PUBLICATION_DATE_REQUIRED: {path.name}')
            continue
        if kind=='monthly' and set(keys)=={'available_on'}:
            continue
        query = query.filter(dt<=as_of)
        if start:
            query = query.filter(dt>=start)
        if available_cutoff and 'available_on' in cols:
            query = query.filter(date_expr(cols['available_on'])<=as_of)
        exprs = [dt.alias('date')]
        for k in keys:
            col = pl.col(cols[k])
            if k=='available_on':
                col = date_expr(cols[k])
            elif k in (*FLOW,'adj_close','benchmark_adj_close','monthly_revenue'):
                col = col.cast(pl.Float64,strict=True)
            exprs.append(col.alias(k))
        projected = query.select(exprs)
        if tail_rows is not None:
            projected = projected.sort('date',descending=True).limit(tail_rows+1)
        data = projected.limit(MAX_INPUT_ROWS+1).collect()
        if data.height>MAX_INPUT_ROWS:
            raise ValueError(f'HISTORY_LIMIT: {path.name}；請設定 --start')
        if data['date'].n_unique()!=data.height:
            raise ValueError(f'DUPLICATE_DATE: {path.name} {symbol}')
        for row in data.iter_rows(named=True):
            day = row.pop('date')
            target = records.setdefault(day,{'date':day})
            for k,v in row.items():
                if v is None:
                    continue
                if k in target and target[k]!=v:
                    raise ValueError(f'CONFLICT: {symbol} {day} {k} {path.name}')
                target[k]=v
        if len(records)>MAX_INPUT_ROWS:
            raise ValueError('HISTORY_LIMIT: 請縮小日期範圍')
    days = sorted(records)
    if tail_rows is not None:
        days = days[-tail_rows:]
    return [records[k] for k in days]


def as_frame(rows,fields):
    schema = {'date':pl.Date}
    for k in fields:
        schema[k] = pl.Date if k=='available_on' else pl.Int64 if k=='session_index' else pl.String if k in ('market','benchmark_market') else pl.Float64
    return pl.from_dicts(rows,schema=schema)


def activity(sources,as_of,start=None):
    blocks = []
    for label,symbol in [('TWSE','^TWII'),('TPEX','^TWOII'),('TSMC','2330.TW')]:
        rows = load_series(sources,symbol,FLOW,as_of,start)
        frame = as_frame(rows,FLOW)
        blocks.append({r['date']:(r['net_volume'],r['net_turnover']) for r in
                      frame.select('date',net_series(frame,'volume').alias('net_volume'),
                                   net_series(frame,'turnover').alias('net_turnover')).to_dicts()})
    result = []
    for d in sorted(set().union(*blocks)):
        tw,otc,chip = (b.get(d,(None,None)) for b in blocks)
        ex = tuple(a-b if a is not None and b is not None and a>=b else None for a,b in zip(tw,chip))
        for label,pair in zip(('TWSE','TPEX','2330.TW','TWSE_EX_2330'),(tw,otc,chip,ex)):
            result.append(dict(date=d,factor=label,net_volume=pair[0],net_turnover=pair[1],
                               status='OK' if None not in pair else 'MISSING_OR_INVALID'))
    return result


def market_code(v):
    v=str(v).upper()
    if v in ('TW','TWSE','TPEX','TWO','上市','上櫃'):
        return 'TW'
    if v in ('US','NYSE','NASDAQ'):
        return 'US'
    raise ValueError(f'MARKET_UNRESOLVED: {v}')


def apply_calendar(sources,records):
    """Use an identified VDF market calendar when the price file lacks session ordinals."""
    needed = {(r['market'],r['date']) for r in records if 'session_index' not in r}
    if not needed:
        return
    found = {}
    for path,cols in sources:
        if not re.search(r'calendar|trading_sessions|交易(日曆|曆)',path.stem,re.I):
            continue
        if not {'market','date','session_index'}<=cols.keys():
            continue
        dt=date_expr(cols['date'])
        low,high=min(d for _,d in needed),max(d for _,d in needed)
        data=pl.scan_parquet(path).filter(dt.is_between(low,high)).select(
            dt.alias('date'),pl.col(cols['market']).alias('market'),
            pl.col(cols['session_index']).alias('session_index')).collect()
        for day,market,index in data.iter_rows():
            key=(market_code(market),day)
            if key in needed and index is not None:
                if key in found and found[key]!=index:
                    raise ValueError('CONFLICTING_CALENDARS')
                found[key]=index
    for row in records:
        key=(row['market'],row['date'])
        if key in found:
            row.setdefault('session_index',found[key])


def run_local(sources,args):
    metrics = args.metrics
    if not metrics or len(metrics)!=len(set(metrics)) or set(metrics)-CORE.keys():
        raise ValueError('UNKNOWN_OR_DUPLICATE_METRIC')
    asof = args.as_of
    windows = {m:args.windows for m in metrics if m not in SPECIAL} if args.windows else {}
    request = dict(mode='local_readonly',ticker=args.ticker,price_link='vdf.daily',metrics=metrics,
                   as_of=asof.isoformat(),windows=windows)
    bindings = {}
    root = Path(args.root).resolve()
    if args.report_id:
        report_sources = [(p,c) for p,c in sources if set(REPORT_KEYS)<=c.keys()]
        if len(report_sources)!=1:
            raise ValueError('REPORT_SOURCE_MISSING_OR_AMBIGUOUS')
        p,c=report_sources[0]
        report = dict(path=p,columns=c,vdf_root=root,mode='local_readonly',producer='VRN',custodian='VDF',link_id='vrn.reports')
        bindings['vrn.reports']=report
        with closing(duckdb.connect()) as conn:
            rt,cutoff,_ = report_anchor(conn,report,args.report_id,asof)
        if args.ticker and args.ticker!=rt:
            raise ValueError('REPORT_TICKER_MISMATCH')
        request.update(ticker=rt,report_id=args.report_id,report_link='vrn.reports')
    else:
        cutoff=asof
    symbol = request['ticker']
    if not symbol:
        raise ValueError('TICKER_REQUIRED')
    extras = sorted({k for m in metrics for k in OPTIONAL.get(m,[])})
    keys = ['adj_close','available_on','session_index','market']+extras
    plan = window_plan(metrics,windows)
    finite = all(EXTRA[m] is not None or m in ('sma','returns') for m,n in plan)
    # One extra bar covers the TW strictly-before-cutoff rule. Gaps in flexible
    # estimators can require an older valid observation, so retry with full history.
    count = 1+max((2 if m=='returns' else n+(EXTRA[m] or 0)) for m,n in plan) if finite else None
    records = load_series(sources,symbol,keys,cutoff,args.start,tail_rows=count)
    if count and len(records)==count and any(m in ('sma','returns') for m in metrics):
        if any(r.get('adj_close') is None or not math.isfinite(r['adj_close']) or r['adj_close']<=0 for r in records):
            records = load_series(sources,symbol,keys,cutoff,args.start)
    if not records:
        raise ValueError('NO_VISIBLE_PRICE')
    for row in records:
        if row.get('market') is None and (symbol.endswith(('.TW','.TWO')) or symbol in ('^TWII','^TWOII')):
            row['market']='TW'
        row['market']=market_code(row.get('market'))
        if 'benchmark_market' in row:
            row['benchmark_market']=market_code(row['benchmark_market'])
    apply_calendar(sources,records)
    for row in records:
        if 'session_index' not in row or 'available_on' not in row:
            raise ValueError('NEED_VDF_CALENDAR_OR_AVAILABILITY: 指標需 VDF 交易序號與實際可用日期')
    frame = as_frame(records,keys).with_columns(pl.lit(symbol).alias('ticker'))
    if args.cache_dir and Path(args.cache_dir).resolve().is_relative_to(root):
        raise ValueError('CACHE_INSIDE_SOURCE_ROOT')
    with tempfile.TemporaryDirectory(prefix='vqg_') as tmp:
        stage=Path(tmp)/'selected.parquet'
        frame.write_parquet(stage)
        price_link='vdf.daily.'+sha(str(root).encode())[:16]
        request['price_link']=price_link
        bindings[price_link]=dict(path=stage,vdf_root=tmp,producer='VDF',custodian='VDF',mode='local_readonly',
                       link_id=price_link,calendar_verified=True,frequency='daily')
        return calculate(request,bindings.__getitem__,cache_dir=args.cache_dir)


def chart_series(sources,symbol,field,freq,axis,as_of,start):
    if (freq=='monthly') != (field=='monthly_revenue'):
        raise ValueError('FREQUENCY_FIELD_MISMATCH')
    fields = list(FLOW) if field in ('clean_volume','clean_turnover') else [field]
    rows = load_series(sources,symbol,fields+['available_on'],as_of,start,kind=freq,
                       available_cutoff=(axis=='available'))
    result = {}
    for r in rows:
        if axis=='available':
            x=r.get('available_on')
            if x is None or x<r['date']:
                raise ValueError('PUBLICATION_DATE_REQUIRED')
        else:
            x=r['date']
        if x in result:
            raise ValueError('MULTIPLE_PERIODS_AT_ONE_X')
        if field in ('clean_volume','clean_turnover'):
            value=net_series(as_frame([r],fields),field.removeprefix('clean_'))[0]
        else:
            value=r.get(field)
        if value is not None and (not math.isfinite(value) or (field=='adj_close' and value<=0)):
            value=None
        result[x]=value
    if not result:
        raise ValueError(f'NO_CHART_SERIES: {symbol} {field}')
    return result


def write_chart(left,right,labels,monthly,out):
    import html
    dates=sorted(set(left)|set(right))
    def x(d):
        return 95+770*(d-dates[0]).days/max(1,(dates[-1]-dates[0]).days)
    svg=['<svg viewBox="0 0 960 370" role="img" aria-label="雙軸時間序列">',
         '<path d="M90 25V302H870V25" stroke="#888" fill="none"/>']
    for side,series in enumerate((left,right)):
        vals=[v for v in series.values() if v is not None]
        if not vals:
            raise ValueError(f'SERIES_ALL_NULL: {labels[side]}')
        lo,hi=min(vals),max(vals)
        if hi==lo:
            pad=max(abs(lo)*0.01,1)
            lo,hi=lo-pad,hi+pad
        color=('#006a72','#a14c18')[side]
        for i in range(5):
            val=lo+(hi-lo)*i/4
            svg.append(f'<text x="{85 if side==0 else 875}" y="{305-68*i}" text-anchor="{"end" if side==0 else "start"}" fill="{color}">{val:.5g}</text>')
        previous=None
        for d in dates:
            v=series.get(d)
            if v is None:
                previous=None
                continue
            px,py=x(d),300-272*(v-lo)/(hi-lo)
            if previous is not None and not monthly[side]:
                svg.append(f'<line x1="{previous[0]}" y1="{previous[1]}" x2="{px}" y2="{py}" stroke="{color}"/>')
            svg.append(f'<circle cx="{px}" cy="{py}" r="{4 if monthly[side] else 2}" fill="{color}"><title>{d} · {v:.8g}</title></circle>')
            previous=(px,py)
        svg.append(f'<text x="{92 if side==0 else 870}" y="18" fill="{color}" text-anchor="{"start" if side==0 else "end"}">{html.escape(labels[side])}</text>')
    for d in sorted({dates[round(i*(len(dates)-1)/4)] for i in range(5)}):
        svg.append(f'<text x="{x(d)}" y="328" text-anchor="middle">{d}</text>')
    svg.append('</svg>')
    table=''.join('<tr><td>'+d.isoformat()+'</td>'+''.join('<td>'+('—' if s.get(d) is None else f'{s[d]:.8g}')+'</td>' for s in (left,right))+'</tr>' for d in dates)
    doc='<!doctype html><meta charset="utf-8"><title>VQG 雙軸圖</title><style>body{max-width:1100px;margin:2em auto;font:14px system-ui;color:#20373b}svg{width:100%;font:11px system-ui}td,th{padding:3px 16px;text-align:right}</style><h2>VQG 雙軸時間圖</h2><p>左右軸獨立刻度。日期取聯集，缺值保留空白。月資料只顯示觀測點。</p>'+''.join(svg)+'<details><summary>檢視日期與數值</summary><table><tr><th>日期</th>'+''.join('<th>'+html.escape(label)+'</th>' for label in labels)+'</tr>'+table+'</table></details>'
    out.write_text(doc,encoding='utf-8')


def selftest():
    from types import SimpleNamespace
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp)
        f=fixture(300)
        f=f.with_columns((pl.col('date')+pl.duration(days=1)).alias('available_on'))
        frames=[]
        for sym,mult in [('2330.TW',1),('^TWII',4),('^TWOII',2)]:
            frames.append(f.with_columns(pl.lit(sym).alias('ticker'),
                (pl.col('volume')*mult).alias('volume'),(pl.col('daytrade_volume')*mult).alias('daytrade_volume'),
                (pl.col('volume')*mult*20).alias('turnover'),(pl.col('daytrade_volume')*mult*20).alias('daytrade_turnover')))
        pl.concat(frames).write_parquet(root/'vdf.parquet')
        pl.DataFrame(dict(ticker=['2330.TW']*2,month=['2026-01','2026-02'],monthly_revenue=[10.,12.],
            available_on=[date(2026,2,10),date(2026,3,10)])).write_parquet(root/'monthly.parquet')
        src,errors=discover(root)
        assert not errors and len(src)==2
        args=SimpleNamespace(root=root,ticker='2330.TW',metrics=['sma','rsi','macd'],windows=None,
                             as_of=date(2026,12,1),start=None,report_id=None,cache_dir=None)
        rows,_=run_local(src,args)
        assert len(rows)==24 and {r['window_n'] for r in rows if r['indicator_id'].endswith('SMA')}==set(DEFAULT_WINDOWS)
        assert all(r['window_n']==14 for r in rows if r['indicator_id'].endswith('RSI'))
        for m in CORE:
            args.metrics=[m]
            args.windows=[20] if m not in SPECIAL else None
            observed,_=run_local(src,args)
            assert len(observed)==3 and all(r['solution_id']==f'S{i+1}' for i,r in enumerate(observed))
        fac=activity(src,args.as_of)
        first={r['factor']:r for r in fac if r['date']==f['date'][0]}
        for label,mult in [('TWSE',4),('TPEX',2),('2330.TW',1),('TWSE_EX_2330',3)]:
            assert first[label]['net_volume']==900*mult and first[label]['net_turnover']==18000*mult
        test=pl.DataFrame(dict(volume=[100.,100.,100.,100.],daytrade_volume=[10.,None,110.,10.],clean_volume=[90.,None,None,89.]))
        assert net_series(test,'volume').to_list()==[90.,None,None,None]
        assert net_series(pl.DataFrame(dict(clean_turnover=[88.])), 'turnover')[0]==88
        d=chart_series(src,'2330.TW','adj_close','daily','period',args.as_of,None)
        m=chart_series(src,'2330.TW','monthly_revenue','monthly','period',args.as_of,None)
        released=chart_series(src,'2330.TW','monthly_revenue','monthly','available',date(2026,2,15),None)
        assert set(released)=={date(2026,2,10)} and set(m)=={date(2026,1,31),date(2026,2,28)}
        write_chart(d,m,('日價','月營收'),(False,True),root/'dual.html')
        assert '<svg' in (root/'dual.html').read_text(encoding='utf-8')
        assert all(v is None for v in net_series(pl.DataFrame(dict(volume=[5.,0.])), 'volume'))
        print('PASS · 14 核心三解入口、六窗口、特殊參數、四組淨量值、缺值與重扣防護、雙時間口徑及離線雙軸圖')


def main():
    parser=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('command',nargs='?',default='scan',choices=['scan','catalog','calc','activity','chart','selftest','test','demo','run-fixture'])
    parser.add_argument('--root',type=Path,default=ROOT,help='VDF Parquet 根目錄，含子資料夾')
    parser.add_argument('--ticker')
    parser.add_argument('--metrics',nargs='+',default=['sma'])
    parser.add_argument('--windows',nargs='+',type=int)
    parser.add_argument('--report-id')
    parser.add_argument('--as-of',type=date.fromisoformat,default=date.today())
    parser.add_argument('--start',type=date.fromisoformat)
    parser.add_argument('--cache-dir',type=Path)
    parser.add_argument('--export-dir',type=Path)
    parser.add_argument('--request',type=Path)
    parser.add_argument('--catalog',type=Path)
    parser.add_argument('--out',type=Path,default=Path('VQG_dual_axis.html'))
    parser.add_argument('--right-ticker')
    parser.add_argument('--left-field',choices=['adj_close','clean_volume','clean_turnover'],default='adj_close')
    parser.add_argument('--right-field',choices=['monthly_revenue','adj_close','clean_volume','clean_turnover'],default='monthly_revenue')
    parser.add_argument('--axis',choices=['period','available'],default='period',help='period 經濟期間；available 公布/可用日')
    parser.add_argument('--open',action='store_true')
    args=parser.parse_args()
    if args.command in ('test','selftest'):
        selftest()
        return
    if args.command=='catalog':
        print(canonical({k:v['formula'] for k,v in CORE.items()}))
        return
    if args.command=='demo':
        with tempfile.TemporaryDirectory() as tmp:
            args.root=Path(tmp)
            f=fixture(300).with_columns((pl.col('date')+pl.duration(days=1)).alias('available_on'))
            f.write_parquet(args.root/'daily.parquet')
            args.ticker='TEST.TW'
            args.as_of=f['available_on'][-1]
            rows,stats=run_local(discover(args.root)[0],args)
            print(canonical(stats),canonical(rows))
        return
    if args.command=='run-fixture':
        if not args.request or not args.catalog:
            parser.error('run-fixture requires --request --catalog')
        req=json.loads(args.request.read_text('utf-8-sig'))
        links=json.loads(args.catalog.read_text('utf-8-sig'))
        if args.export_dir and any(args.export_dir.resolve().is_relative_to(Path(b['vdf_root']).resolve()) for b in links.values()):
            raise ValueError('EXPORT_INSIDE_SOURCE_ROOT')
        rows,stats=calculate(req,links.__getitem__,cache_dir=args.cache_dir)
        print(canonical(stats),canonical(rows))
        if args.export_dir:
            print(export_snapshot(rows,args.export_dir))
        return
    sources,errors=discover(args.root)
    if args.command=='scan':
        for path,cols in sources:
            print(path.relative_to(args.root.resolve()), ', '.join(cols))
        print(canonical(dict(recognized=len(sources),errors=errors)))
        return
    if errors:
        print('略過無法讀取的 Parquet：'+canonical(errors),file=sys.stderr)
    for out in (args.cache_dir,args.export_dir,args.out if args.command=='chart' else None):
        if out and out.resolve().is_relative_to(args.root.resolve()):
            raise ValueError('OUTPUT_INSIDE_SOURCE_ROOT')
    if args.command=='calc':
        rows,stats=run_local(sources,args)
        print(canonical(stats),canonical(rows))
        if args.export_dir:
            print(export_snapshot(rows,args.export_dir))
    elif args.command=='activity':
        rows=activity(sources,args.as_of,args.start)
        if not rows:
            raise ValueError('NO_MATCHING_VDF_ACTIVITY')
        result=pl.DataFrame(rows,infer_schema_length=None)
        if args.export_dir:
            print(export_factor_snapshot(result,args.export_dir))
        print(result.tail(4))
    else:
        if not args.ticker:
            parser.error('chart requires --ticker')
        right=args.right_ticker or args.ticker
        monthly=args.right_field=='monthly_revenue'
        left_values=chart_series(sources,args.ticker,args.left_field,'daily',args.axis,args.as_of,args.start)
        right_values=chart_series(sources,right,args.right_field,'monthly' if monthly else 'daily',args.axis,args.as_of,args.start)
        if args.out.suffix.lower()!='.html':
            raise ValueError('HTML_OUTPUT_REQUIRED')
        args.out.parent.mkdir(parents=True,exist_ok=True)
        write_chart(left_values,right_values,(f'{args.ticker} {args.left_field} ({args.axis})',f'{right} {args.right_field} ({args.axis})'),(False,monthly),args.out)
        print(args.out.resolve())
        if args.open:
            webbrowser.open(args.out.resolve().as_uri())


def export_factor_snapshot(frame,parent):
    import shutil
    import uuid
    parent.mkdir(parents=True,exist_ok=True)
    stage=Path(tempfile.mkdtemp(prefix='.vqg-',dir=parent))
    try:
        frame.write_parquet(stage/'activity.parquet',compression='zstd')
        frame.write_csv(stage/'activity.csv',include_bom=True,date_format='%Y/%m/%d')
        target=parent/('activity_'+uuid.uuid4().hex)
        stage.rename(target)
        return target
    finally:
        if stage.exists():
            shutil.rmtree(stage)


def shared_digest():
    import ast
    source_text=Path(__file__).read_text(encoding='utf-8-sig')
    tree=ast.parse(source_text)
    shared=[node for node in tree.body if not (isinstance(node,ast.FunctionDef) and node.name in CORE)]
    return sha(ast.dump(ast.Module(body=shared,type_ignores=[])).encode())


SHARED_HASH=shared_digest()

if __name__=='__main__':
    main()
