#!/usr/bin/env python3
"""VQG Polars three-solution candidate; VCGC only, offline until source binding is proven."""
from __future__ import annotations
import os, sys, json, math, hashlib, importlib.util
from pathlib import Path
from datetime import date, timedelta
# ===== 1. 所有運算參數集中 =====
ENGINE_ID = "VDF_ENG086_QuantGuardOneBridge"
VERSION = "v0102"
DEFAULT_WINDOW = 20
DEFAULT_WINDOWS = (5,10,20,60,120,240)
RSI_WINDOW = 14
MAX_WINDOW = 252
MAX_INPUT_ROWS = 5000
MAX_OUTPUT_ROWS = 100
MACD_FAST, MACD_SLOW, MACD_SIGNAL = 12,26,9
BAND_K, MAD_SIGMA, MAD_Z_SCALE = 2.0,1.4826,0.6745
DOWNSIDE_MIN = 5
ABS_TOL, REL_TOL = 1e-10,1e-6
HERE = Path(__file__).resolve()
VIA = HERE.parents[3]
POLICY_BOOK = VIA / "supportive modules/registry/VIA_QuantGuard_Policy_SSOT_v0101.json"
INDICATOR_BOOK = VIA / "supportive modules/registry/VIA_QuantGuard_Indicator_SSOT_v0101.json"
PRIOR_PATH = HERE.with_name("VDF_ENG086_QuantGuardOneBridge_v0101.py")
_PRIOR = None
NONCOMPARABLE = {"summary","returns","volatility","roc","slope","volume_zscore","beta"}
STATUS_FIELDS = {"link_id","owner","source_type","status","row_count","column_names","fingerprint8","checked_at","cached","error_code"}
FIXTURE_CONTEXT = {"entry":"VCGC","owner":"VDF","source_type":"parquet","purpose":"technical_analysis","frequency":"daily","calendar_verified":True,"price_field":"adj_close","link_id":"OFFLINE_SYNTHETIC","mode":"offline_fixture"}
# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(VDF 全導入令;惰性載入=import 時零網路、零行為變更) =====
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
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT;網路只認 AegisNexus);缺席回 None(誠實)"""
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
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(全樹導入令;graceful 零行為變更) =====
try:
    _sa_p = HERE
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====
# ===== 2. 相依與數值基元 =====
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


# ===== 3. 每個指標三解；内部才持有全時序 =====
def calculate_series(frame, window=None):
    """Internal single-ticker calculation. Public callers must use derived_cards."""
    pl=_polars(); p=_price(frame['adj_close']); n=window or DEFAULT_WINDOW
    blank=_series([None]*len(p)); r=_divide(p,p.shift(1))-1; log=_finite(p.log()-p.shift(1).log())
    volume=blank
    if 'volume' in frame.columns:
        v=_finite(frame['volume'].cast(pl.Float64))
        volume=v.zip_with(v>=0,blank)
        if frame['market'][0]=='TW':
            if 'daytrade_volume' not in frame.columns:
                volume=blank
            else:
                dt=_finite(frame['daytrade_volume'].cast(pl.Float64))
                volume=(v-dt).zip_with((dt>=0)&(dt<=v)&(v>=0),blank)
    count=p.is_not_null().cast(pl.Float64).cum_sum()
    avg=p.cum_sum()/count
    med=p.rolling_median(window_size=max(1,len(p)),min_samples=1)
    cum_mad=p.rolling_map(lambda a:(a.drop_nulls()-a.drop_nulls().median()).abs().median(),window_size=max(1,len(p)),min_samples=1)
    summary=({'mean':avg,'min':p.cum_min(),'max':p.cum_max(),'pstdev':_rolling(p,max(2,len(p)),'std',minimum=1,ddof=0),'count':count},
             {'median':med,'mad':cum_mad,'count':count},{'latest':blank,'count':count})
    gap=[];previous=None;missing=False
    for value in p.to_list():
        gap.append(value/previous-1 if value is not None and previous is not None and missing else None)
        if value is None:
            missing=True
        else:
            previous=value;missing=False
    ret={'summary':summary,'returns':(r,log,{'adjacent':r,'gap_return':_finite(_series(gap))}),
         'sma':(_rolling(p,n),_rolling(p,n,minimum=1),_compressed(p,n,'mean')),
         'ema':(_seeded_ema(p,n),_seeded_ema(p,n,first=True),_seeded_ema(p,n,alpha=1/n)),
         'volatility':(_rolling(r,n,'std'),_rolling(r,n,'std',ddof=0),_rolling(log,n,'std')),
         'zscore':(_z(p,n),_z(p,n,population=True,flat_zero=True),_robust_z(p,n)),
         'roc':(_divide(p,p.shift(n))-1,_finite(p.log()-p.shift(n).log()),_divide(p,p.shift(n))-1),
         'slope':(_slope(p,n),_slope(p,n,log=True),_slope(p,n,robust=True)),
         'volume_zscore':(_z(volume,n),_z(volume.log1p(),n),_robust_z(volume,n))}
    rn=window or RSI_WINDOW; delta=p-p.shift(1); gain=delta.clip(lower_bound=0); loss=(-delta).clip(lower_bound=0)
    ret['rsi']=(_rsi(_seeded_ema(gain,rn,1/rn),_seeded_ema(loss,rn,1/rn)),
                _rsi(_rolling(gain,rn),_rolling(loss,rn)),_rsi(_rolling(gain,rn),_rolling(loss,rn),True))
    peak=p.cum_max(); reset=[]; high=None
    for value in p.to_list():
        if value is None:
            high=None;reset.append(None)
        else:
            high=value if high is None else max(high,value);reset.append(value/high-1)
    ret['drawdown']=(_divide(p,peak)-1,_divide(p,_compressed(p,n,'max'))-1,_series(reset))
    b=blank
    if 'benchmark_adj_close' in frame.columns and 'benchmark_market' in frame.columns:
        if frame['benchmark_market'].n_unique()==1 and frame['benchmark_market'][0]==frame['market'][0]:
            bp=_price(frame['benchmark_adj_close']);b=_divide(bp,bp.shift(1))-1
    beta=_beta(r,b,n)
    ret['beta']=(beta,_beta(r,b,n,True),beta)
    # Multi-component indicators retain every component, including warm-up nulls.
    ema_diff=_seeded_ema(p,MACD_FAST)-_seeded_ema(p,MACD_SLOW)
    sma_diff=_rolling(p,MACD_FAST)-_rolling(p,MACD_SLOW)
    es=_seeded_ema(ema_diff,MACD_SIGNAL);ss=_rolling(sma_diff,MACD_SIGNAL)
    macd1={'line':ema_diff,'signal':es,'histogram':ema_diff-es}
    macd2={'line':sma_diff,'signal':ss,'histogram':sma_diff-ss}
    agreement=pl.Series([True]*len(p))
    for key in macd1:
        a,bv=macd1[key],macd2[key]
        agreement=agreement & a.is_not_null() & bv.is_not_null() & ((a-bv).abs()<=ABS_TOL+REL_TOL*bv.abs())
    ret['macd']=(macd1,macd2,{k:v.zip_with(agreement,blank) for k,v in macd1.items()})
    mean=_rolling(p,n);std1=_rolling(p,n,'std');std0=_rolling(p,n,'std',ddof=0)
    median=_rolling(p,n,'median');mad=_mad(p,n)
    ret['bollinger']=({'mid':mean,'upper':mean+BAND_K*std1,'lower':mean-BAND_K*std1},
                      {'mid':mean,'upper':mean+BAND_K*std0,'lower':mean-BAND_K*std0},
                      {k:v.zip_with(mad>0,blank) for k,v in {'mid':median,'upper':median+BAND_K*MAD_SIGMA*mad,'lower':median-BAND_K*MAD_SIGMA*mad}.items()})
    return ret


# ===== 4. 前置閘、白名單卡；不接受 SQL 或任意本機檔案 =====
def validate_frame(frame, context, window=None):
    pl=_polars()
    policy=json.loads(POLICY_BOOK.read_text(encoding='utf-8'))
    if (policy['limits']['max_input_rows']!=MAX_INPUT_ROWS or policy['limits']['max_output_rows']!=MAX_OUTPUT_ROWS or policy['limits']['max_window']!=MAX_WINDOW or policy['mode']['talib']!='forbidden'):
        raise ValueError('POLICY_IMPLEMENTATION_DRIFT')
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
    if context.get('mode')!='offline_fixture':
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


def derived_cards(frame, context, window=None, metrics=None):
    f=validate_frame(frame,context,window)
    book=json.loads(INDICATOR_BOOK.read_text(encoding='utf-8'))
    definitions={x['id']:x for x in book['indicators']}
    selected=list(definitions) if metrics is None else list(metrics)
    if not selected or len(set(selected))!=len(selected) or set(selected)-definitions.keys():
        raise ValueError('METRIC_NOT_IN_SSOT_OR_DUPLICATE')
    if f['ticker'].n_unique()*len(selected)*3>MAX_OUTPUT_ROWS:
        raise ValueError('OUTPUT_LIMIT_EXCEEDED_SELECT_FEWER_METRICS')
    cards=[]
    for part in f.partition_by('ticker',maintain_order=True):
        series=calculate_series(part,window)
        fingerprint=hashlib.sha256(part.write_json().encode()).hexdigest()[:8]
        for metric in selected:
            values=[_last(x) for x in series[metric]]; verdict=_verdict(metric,values)
            if metric=='returns' and all(x is not None for x in (values[0],values[1],values[2]['adjacent'])):
                verdict='NOT_COMPARABLE'
            for i,value in enumerate(values):
                nums=_numbers(value);valid=all(v is not None for v in nums)
                if metric=='returns' and i==2:
                    valid=value['adjacent'] is not None
                reason=None if valid else 'WARMUP_MISSING_OR_DEGENERATE'
                if metric=='summary' and i==2:
                    reason='RAW_LAST_PRICE_WITHHELD'
                if metric=='macd' and i==2 and not valid:
                    reason='WARMUP_OR_COMPONENT_DIVERGENCE'
                cards.append({'link_id':context['link_id'],'ticker':part['ticker'][0],
                  'date':part['date'][-1].strftime('%Y/%m/%d'),'indicator_id':definitions[metric]['stable_id'],
                  'solution_id':f'S{i+1}','purpose':context['purpose'],'value':value,
                  'valid':valid,'invalid_reason':reason,'verdict':verdict,'fingerprint8':fingerprint,
                  'coverage':_price(part.tail(window or definitions[metric].get('window',DEFAULT_WINDOW))['adj_close']).is_not_null().mean(),
                  'partial':_price(part.tail(window or definitions[metric].get('window',DEFAULT_WINDOW))['adj_close']).is_not_null().sum()<(window or definitions[metric].get('window',DEFAULT_WINDOW)),
                  'estimator':definitions[metric]['solutions'][i]['name'],
                  'calendar':'VDF_official_session_index','deployment':'CANDIDATE_OFFLINE',
                  'gap_policy':'compressed_valid_bars' if (metric=='sma' and i==2) or (metric=='drawdown' and i==1) else 'preserve_null_bars',
                  'unit':('log_price_per_session' if metric=='slope' and i==1 else 'price_per_session' if metric=='slope' else 'log_return' if metric in ('returns','roc') and i==1 else 'fraction' if metric in ('returns','roc','drawdown','volatility') else 'indicator_units')})
    return cards


def status_forward(card):
    if set(card)-STATUS_FIELDS:
        raise ValueError('STATUS_FIELD_NOT_WHITELISTED')
    return dict(card)


# ===== 5. 離線驗證；測試數現場計 =====
def fixture(days=90):
    pl=_polars();values=[100+0.2*i+3*math.sin(i/3) for i in range(days)]
    return pl.DataFrame({'ticker':['TEST.TW']*days,'date':[date(2026,1,1)+timedelta(days=i) for i in range(days)],
        'market':['TW']*days,'session_index':range(days),'adj_close':values,
        'benchmark_adj_close':values,'benchmark_market':['TW']*days,
        'volume':[1000.+i*4+20*math.sin(i) for i in range(days)],'daytrade_volume':[100.]*days})


def selftest():
    pl=_polars();checks=[]
    def check(name,condition):
        checks.append({'case':name,'pass':bool(condition)})
    def rejects(name,frame,ctx=None,**kwargs):
        try:
            derived_cards(frame,ctx or FIXTURE_CONTEXT,**kwargs)
        except ValueError:
            check(name,True)
        else:
            check(name,False)
    f=fixture();cards=derived_cards(f,FIXTURE_CONTEXT);s=calculate_series(f)
    check('14 indicators x 3 solutions',len(cards)==42 and len({x['indicator_id'] for x in cards})==14)
    check('no raw columns',all(not {'adj_close','volume','benchmark_adj_close','session_index'} & x.keys() for x in cards))
    check('self beta = 1',math.isclose(s['beta'][0][-1],1,rel_tol=1e-9))
    check('EMA SMA seed',math.isclose(s['ema'][0][DEFAULT_WINDOW-1],f['adj_close'].head(DEFAULT_WINDOW).mean(),rel_tol=1e-12))
    check('Bessel variance ratio',math.isclose(s['volatility'][0][-1]/s['volatility'][1][-1],math.sqrt(DEFAULT_WINDOW/(DEFAULT_WINDOW-1)),rel_tol=1e-10))
    linear=f.with_columns(pl.Series('adj_close',[100.+i for i in range(f.height)]));ls=calculate_series(linear)
    check('OLS slope independent oracle',math.isclose(ls['slope'][0][-1],1,abs_tol=1e-10))
    check('Theil Sen independent oracle',math.isclose(ls['slope'][2][-1],1,abs_tol=1e-10))
    check('ROC fixed lag fraction',math.isclose(ls['roc'][0][-1],189/169-1,abs_tol=1e-12))
    check('up RSI S1 100 S3 null',ls['rsi'][0][-1]==100 and ls['rsi'][2][-1] is None)
    flat=f.with_columns(pl.lit(100.).alias('adj_close'));flat_s=calculate_series(flat)
    check('flat RSI all null',all(x[-1] is None for x in flat_s['rsi']))
    check('flat z policy',flat_s['zscore'][0][-1] is None and flat_s['zscore'][1][-1]==0)
    check('constant SMA',flat_s['sma'][0][-1]==100)
    check('constant volatility zero',flat_s['volatility'][0][-1]==0)
    check('short MACD null',calculate_series(f.head(5))['macd'][0]['line'][-1] is None)
    bad=f.with_columns(pl.when(pl.col('session_index')==40).then(None).otherwise(pl.col('adj_close')).alias('adj_close'));bs=calculate_series(bad)
    check('gap return both sides null',bs['returns'][0][40] is None and bs['returns'][0][41] is None)
    check('strict SMA gap blocks',bs['sma'][0][45] is None)
    check('EMA reseeds after gap',bs['ema'][0][59] is None and bs['ema'][0][60] is not None)
    check('drawdown resets after gap',bs['drawdown'][2][41]==0)
    check('ROC inner gap does not discard fixed base',bs['roc'][0][45] is not None)
    future=f.with_columns(pl.when(pl.col('session_index')>=70).then(999999.).otherwise(pl.col('adj_close')).alias('adj_close'))
    future_s=calculate_series(future)
    for metric,solutions in s.items():
        for i,seq in enumerate(solutions):
            a=seq if isinstance(seq,dict) else {'value':seq};b=future_s[metric][i];b=b if isinstance(b,dict) else {'value':b}
            check('no lookahead '+metric+f' S{i+1}',all(a[k].head(70).equals(b[k].head(70)) for k in a))
    for value in (0.,-1.,float('nan'),float('inf')):
        invalid=f.with_columns(pl.when(pl.col('session_index')==89).then(value).otherwise(pl.col('adj_close')).alias('adj_close'))
        check('invalid price '+str(value),calculate_series(invalid)['returns'][0][-1] is None)
    badvol=f.with_columns(pl.when(pl.col('session_index')==89).then(999999.).otherwise(pl.col('daytrade_volume')).alias('daytrade_volume'))
    check('daytrade greater than total withheld',all(x[-1] is None for x in calculate_series(badvol)['volume_zscore']))
    mismatch=f.with_columns(pl.lit('US').alias('benchmark_market'))
    check('cross market beta withheld',all(x[-1] is None for x in calculate_series(mismatch)['beta']))
    check('log slope noncomparable',_verdict('slope',[1,0.01,1])=='NOT_COMPARABLE')
    check('divergence retained',_verdict('ema',[1,2,3])=='DIVERGE')
    rejects('duplicate date blocked',pl.concat([f,f.tail(1)]))
    rejects('missing calendar blocked',f,{**FIXTURE_CONTEXT,'calendar_verified':False})
    rejects('production source binding not bypassed',f,{**FIXTURE_CONTEXT,'mode':'production'})
    rejects('owner blocked',f,{**FIXTURE_CONTEXT,'owner':'EXTERNAL'})
    rejects('unadjusted blocked',f.drop('adj_close'))
    rejects('omitted session blocked',f.filter(pl.col('session_index')!=10))
    rejects('window >252 blocked',f,window=300)
    rejects('unknown metric blocked',f,metrics=['volume_stats'])
    rejects('output limit blocked',pl.concat([f,f.with_columns(pl.lit('B').alias('ticker')),f.with_columns(pl.lit('C').alias('ticker'))]))
    try:
        status_forward({'raw_rows':[]});check('status raw egress blocked',False)
    except ValueError:
        check('status raw egress blocked',True)
    failed=sum(not c['pass'] for c in checks)
    for c in checks:
        print(('[OK] ' if c['pass'] else '[FAIL] ')+c['case'])
    print(json.dumps({'engine':ENGINE_ID,'version':VERSION,'scope':'offline synthetic only','passed':len(checks)-failed,'failed':failed,'polars':pl.__version__,'production':'BLOCKED_PENDING_VCGC_SOURCE_BINDING'},ensure_ascii=False))
    print(f'[計] OK {len(checks)-failed} · FAIL {failed}')
    return int(failed>0)


# ===== 6. 既有入口相容，正式輸入未掛載不得悄悄使用舊出口 =====
def _run_features(frame,output_dir):
    raise ValueError('PRODUCTION_BLOCKED_PENDING_VCGC_SOURCE_BINDING')


def run_input(path=None,output=None):
    print('[GATED] PRODUCTION_BLOCKED_PENDING_VCGC_SOURCE_BINDING; no raw export')
    return 2


def status():
    print(json.dumps({'engine':ENGINE_ID,'version':VERSION,'status':'CANDIDATE_OFFLINE','library':'POLARS','production':'GATED','network':'OFF','ta_lib':'FORBIDDEN'}))
    return 0


def __getattr__(name):
    # Preserve old inspection helpers; execution paths above are explicitly overridden.
    global _PRIOR
    if _PRIOR is None:
        spec=importlib.util.spec_from_file_location(ENGINE_ID+'_prior',PRIOR_PATH)
        _PRIOR=importlib.util.module_from_spec(spec);sys.modules[spec.name]=_PRIOR;spec.loader.exec_module(_PRIOR)
    return getattr(_PRIOR,name)


def main():
    if os.environ.get('VIA_FROM_VCGC')!='YES':
        print('[GATED] ONLY_VIA_ENTRY');return 2
    argv=sys.argv[1:]
    if argv in (['--selftest'],['selftest']):
        try:
            return selftest()
        except ModuleNotFoundError as exc:
            print('[ABSENT] '+str(exc));return 3
    if argv in ([],['status'],['--status']):
        return status()
    return run_input()


if __name__=='__main__':
    raise SystemExit(main())
