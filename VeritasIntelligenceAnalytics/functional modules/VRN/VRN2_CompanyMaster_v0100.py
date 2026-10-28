#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111] 官方公司名稱外掛；出網僅透過已鎖版橋接。
"""TWSE/TPEx master snapshots. English short name is not an English full name."""
from __future__ import annotations
import datetime as dt, hashlib, importlib.util, json, re, sys
from pathlib import Path
from VRN2_Workbench_v0101 import verb

VERSION='v0100'
TTL_DAYS=7
ENDPOINTS={'TWSE':'https://openapi.twse.com.tw/v1/opendata/t187ap03_L','TPEX':'https://www.tpex.org.tw/openapi/v1/mopsfin_t187ap03_O'}
FIELDS={
 'ticker':('公司代號','SecuritiesCompanyCode'),
 'zh_full':('公司名稱','CompanyName','CompanyFullName'),
 'zh_short':('公司簡稱','CompanyAbbreviation'),
 'en_short':('英文簡稱','Symbol','EnglishCompanyAbbreviation'),
 'en_full':('英文名稱','EnglishCompanyFullName'),
 'source_date':('出表日期','Date')}
TZ=dt.timezone(dt.timedelta(hours=8))


@verb
def normalize(row,market,source):
    if market not in ENDPOINTS or source!=ENDPOINTS[market]:raise ValueError('不是已核對的官方公司主檔端點')
    out={key:next((str(row[n]).strip() for n in names if row.get(n) is not None and str(row[n]).strip() not in ('','－','—','-')),None) for key,names in FIELDS.items()}
    if not re.fullmatch('[1-9][0-9]{3}',out['ticker'] or ''):return None
    out.update(market=market,source=source,version=VERSION)
    out['verified']=bool(out['zh_short'] and out['en_short'])
    out['notes']=[] if out['en_full'] else ['EN_FULL_MISSING:官方回應沒有英文全名，不用英文簡稱冒充']
    return out


@verb
def read_cache(home):
    home=Path(home);path=home/'catalog.json'
    if not path.is_file():return {},{}
    catalog=json.loads(path.read_text(encoding='utf-8'));records={}
    for market,item in catalog.get('markets',{}).items():
        path=home/item['json']
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=item['sha256']:raise ValueError('公司主檔快取雜湊不符')
        for record in json.loads(path.read_text(encoding='utf-8')):
            prior=records.get(record['ticker'])
            if prior and prior['market']!=record['market']:
                record=dict(record,verified=False,notes=['MARKET_CONFLICT:上市與上櫃主檔同時出現，需查明生效日期'])
            records[record['ticker']]=record
    return records,catalog


@verb
def persist_market(home,market,rows,at=None):
    import pyarrow as pa
    import pyarrow.parquet as pq
    home=Path(home);home.mkdir(parents=True,exist_ok=True);at=at or dt.datetime.now(TZ)
    normalized=[r for row in rows if (r:=normalize(row,market,ENDPOINTS[market])) is not None]
    seen={}
    for r in normalized:
        if r['ticker'] in seen and seen[r['ticker']]!=r:raise ValueError('官方公司主檔同一代碼內容衝突')
        seen[r['ticker']]=r
    if not seen:raise ValueError('官方主檔沒有可用四碼個股，不更新快取')
    tag=at.strftime('%Y%m%d_%H%M%S_%f');jsonpath=home/(market+'_'+tag+'.json');parquet=home/(market+'_'+tag+'.parquet')
    raw=json.dumps(list(seen.values()),ensure_ascii=False,indent=2,allow_nan=False).encode('utf-8');jsonpath.write_bytes(raw)
    pq.write_table(pa.Table.from_pylist(list(seen.values())),parquet,compression='zstd')
    catalog_path=home/'catalog.json';catalog=json.loads(catalog_path.read_text()) if catalog_path.is_file() else {'markets':{}}
    catalog['markets'][market]={'json':jsonpath.name,'parquet':parquet.name,'sha256':hashlib.sha256(raw).hexdigest(),'retrieved_at':at.isoformat(),'source':ENDPOINTS[market]}
    tmp=catalog_path.with_suffix('.tmp');tmp.write_text(json.dumps(catalog,ensure_ascii=False,indent=2),encoding='utf-8');tmp.replace(catalog_path)
    return list(seen.values())


@verb
def locked_get(root,url):
    """Use exactly the hash-checked VDF bridge, including its redirect and DENY handling."""
    folder=Path(root)/'functional modules'/'VRN';sys.path.insert(0,str(folder))
    modules=sorted(folder.glob('VRN2_MarketFetch_v[0-9][0-9][0-9][0-9].py'))
    if not modules:raise FileNotFoundError('缺 MarketFetch 鎖版橋接')
    spec=importlib.util.spec_from_file_location('vrn_company_market',modules[-1]);mf=importlib.util.module_from_spec(spec);spec.loader.exec_module(mf)
    lock=Path(root)/'supportive modules'/'registry'/'VIA_ToolVersion_Lock_v0100.json'
    if not lock.is_file():raise PermissionError('沒有鎖版網路工具，不以獨立傳輸抓公司名稱')
    shim,note=mf.shim_root(Path(root))
    if not shim:raise PermissionError(note)
    engine=mf.engine_path()
    if not engine:raise FileNotFoundError('缺 VDF 原始官方資料引擎')
    spec=importlib.util.spec_from_file_location('vrn_company_vdf',engine);vdf=importlib.util.module_from_spec(spec);spec.loader.exec_module(vdf)
    bridge=vdf.def_via_bridges(shim)
    if bridge.get('network')!='LOCKED_VIA':raise PermissionError('不是已鎖版 VIA 網路路徑')
    return vdf.def_bridge_official_bytes(bridge['module'],url)


@verb
def ensure(root,home,force=False,getter=None):
    records,catalog=read_cache(home);errors=[];failed=set();today=dt.datetime.now(TZ)
    for market,url in ENDPOINTS.items():
        meta=catalog.get('markets',{}).get(market,{})
        try:fresh=0<=(today-dt.datetime.fromisoformat(meta['retrieved_at'])).total_seconds()<TTL_DAYS*86400
        except (KeyError,ValueError):fresh=False
        if fresh and not force:continue
        try:
            raw=(getter(url) if getter else locked_get(root,url));rows=json.loads(raw.decode('utf-8-sig'))
            if not isinstance(rows,list):raise ValueError('官方回應不是陣列')
            persist_market(home,market,rows,today)
        except PermissionError:raise
        except Exception as exc:
            failed.add(market);errors.append(market+':'+type(exc).__name__+':'+str(exc))
    records,_=read_cache(home)
    for record in records.values():
        if record['market'] in failed:record.update(verified=False,notes=record.get('notes',[])+['STALE:官方刷新未成功'])
    return records,errors


@verb
def prefix_titles(basic,summaries,records):
    byfile={r.get('FILENAME'):r for r in basic};issues={}
    for summary in summaries:
        row=byfile.get(summary.get('FILENAME'),{});code=str(row.get('TICKER') or '').split('.')[0].split()[0] if row.get('TICKER') else ''
        record=records.get(code);original=summary.setdefault('TITLE_ORIGINAL',summary.get('TITLE') or '')
        if not original:issues[str(summary.get('FILENAME'))]='SUMMARY_TITLE_ORIGINAL_MISSING'
        if record and record.get('verified'):
            row.update(NAME=record['zh_short'],COMPANY_SHORT_NAME_ZH=record['zh_short'],COMPANY_SHORT_NAME_EN=record['en_short'],COMPANY_NAME_EN_FULL=record['en_full'],COMPANY_NAME_SOURCE=record['source'])
            summary['TITLE']=f"{record['zh_short']} / {record['en_short']} ({code})｜{original}"
            summary['COMPANY_NAME_STATUS']='VERIFIED';summary['COMPANY_NAME_SOURCE']=record['source']
            summary['COMPANY_NAME_SOURCE_DATE']=record.get('source_date')
            if record.get('notes'):row['STATUS']=str(row.get('STATUS') or '')+' | '+' | '.join(record['notes'])
        else:
            summary['TITLE']=f"{code or '代碼未確認'} 公司簡稱待官方核對｜{original}"
            summary['COMPANY_NAME_STATUS']='UNVERIFIED';issues[str(summary.get('FILENAME'))]='COMPANY_SHORT_NAME_UNVERIFIED'
    for row in basic:
        for key in ('RECENT_REPORT_PRE_EARNINGS_FLAG','STATUS'):
            if key in row:row[key]=row.pop(key)
    for row in summaries:
        if 'STATUS' in row:row['STATUS']=row.pop('STATUS')
    return issues
