#!/usr/bin/env python3
"""Central numbering v0112: VQG indicator references and bounded local text tools."""
from __future__ import annotations
import os, sys, json, hashlib, importlib.util, unicodedata
from pathlib import Path
# ===== 1. Parameters =====
HERE=Path(__file__).resolve()
PRIOR_PATH=HERE.with_name('CGC_MDL237_NumberingSystem_v0111.py')
SOURCE='supportive modules/registry/VIA_QuantGuard_Indicator_SSOT_v0101.json'
OWNER='VDF_ENG086_QuantGuardOneBridge'
FUZZY_THRESHOLD=90
FUZZY_LIMIT=5
TICKER_PATTERN=r'^[1-9][0-9]{3}\.(TW|TWO)$'
OPTIONAL_MODULES=('polars','duckdb','pydantic','flashtext','re2','regex','ahocorasick','rapidfuzz','jellyfish','polyfuzz','recordlinkage','spacy','gensim','fasttext','nltk','pandera')
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
# ===== 2. 前版接續，保留中央唯一發號權 =====
def _load_prior():
    spec=importlib.util.spec_from_file_location('numbering_prior_v0112',PRIOR_PATH)
    mod=importlib.util.module_from_spec(spec);sys.modules[spec.name]=mod;spec.loader.exec_module(mod)
    return mod


PRIOR=_load_prior()
BASE=PRIOR.BASE
_PREVIOUS_COLLECT=BASE.collect


def __getattr__(name):
    return getattr(PRIOR,name)


def validate_definition(row):
    from pydantic import ConfigDict, create_model
    model=create_model('IndicatorIdentity',__config__=ConfigDict(strict=True,extra='forbid'),
        id=(str,...),stable_id=(str,...),family=(str,...),source_identity=(str,...),library=(str,...))
    keys=('id','stable_id','family','source_identity','library')
    result=model.model_validate({k:row[k] for k in keys}).model_dump()
    if not all(result.values()) or result['library']!='POLARS' or result['stable_id']!='VQG.IND.'+result['id'].upper():
        raise ValueError('INVALID_INDICATOR_IDENTITY')
    return result


def indicator_items(book=None, source=SOURCE):
    data=json.loads((BASE.VIA/source).read_text(encoding='utf-8')) if book is None else book
    definitions=data['indicators'];seen=set();rows=[]
    for definition in definitions:
        x=validate_definition(definition)
        if x['id'] in seen:
            raise ValueError('DUPLICATE_INDICATOR_ID')
        seen.add(x['id'])
        pointer='indicators[id='+x['id']+']'
        # Source path is part of identity. Same content at different origins is NOT deduplicated.
        rows.append(BASE.item('LGC',source+'#'+pointer,x['stable_id'],'VQG/Indicator/'+x['family'],source,
            OWNER+' → derived_cards',BASE.updated(source),'VDF',data['version'],'AMBER',
            '候選契約；正式來源綁定未驗收',declared_code=x['stable_id'],source_pointer=pointer,
            owner_engine=OWNER,subsystem_owner='VQG',source_identity=x['source_identity'],
            definition_sha256=hashlib.sha256(json.dumps(definition,sort_keys=True,ensure_ascii=False).encode()).hexdigest()))
    return rows


def collect():
    rows,notes=_PREVIOUS_COLLECT()
    rows.extend(indicator_items())
    return rows,notes


BASE.collect=collect


# ===== 3. 本地正規化工具；模糊比對只產生候選 =====
def normalize_labels(values, alias_rows):
    import polars as pl
    aliases={}
    for source,canonical in alias_rows:
        key=unicodedata.normalize('NFKC',source).strip().casefold()
        if not key or not canonical:
            raise ValueError('EMPTY_ALIAS')
        if key in aliases and aliases[key]!=canonical:
            raise ValueError('AMBIGUOUS_ALIAS:'+key)
        aliases[key]=canonical
    normalized=[unicodedata.normalize('NFKC',x).strip().casefold() if x is not None else None for x in values]
    return pl.Series('canonical',normalized,dtype=pl.String).replace_strict(aliases,default=None)


def replace_text_literals(texts, aliases):
    import polars as pl
    if any(not x for x in aliases):
        raise ValueError('EMPTY_LITERAL')
    pairs=sorted(aliases.items(),key=lambda x:(-len(x[0]),x[0]))
    series=pl.Series(texts,dtype=pl.String)
    return series.str.replace_many(dict(pairs),leftmost=True) if pairs else series


def valid_tickers(values):
    import duckdb
    # DuckDB uses RE2, parameter binding, memory-only connection, zero extension installation.
    with duckdb.connect(':memory:') as connection:
        return [connection.execute('SELECT regexp_full_match(?, ?)',[v,TICKER_PATTERN]).fetchone()[0] if v is not None else False for v in values]


def fuzzy_candidates(value,choices):
    if importlib.util.find_spec('rapidfuzz') is None:
        return {'status':'ABSENT','candidates':[],'auto_apply':False}
    from rapidfuzz import process, fuzz
    found=process.extract(value,choices,scorer=fuzz.WRatio,score_cutoff=FUZZY_THRESHOLD,limit=FUZZY_LIMIT)
    return {'status':'REVIEW','candidates':[{'text':x[0],'score':x[1]} for x in found],'auto_apply':False}


def tool_inventory():
    return [{'module':x,'available':importlib.util.find_spec(x) is not None,
             'role':'ACTIVE' if x in ('polars','duckdb','pydantic') else 'OPTIONAL_NOT_ACTIVATED',
             'auto_install':False} for x in OPTIONAL_MODULES]


# ===== 4. 新增契約測試與 CLI =====
def selftest():
    checks=[]
    def check(name,ok):
        checks.append((name,bool(ok)));print(('[OK] ' if ok else '[FAIL] ')+name)
    rows=indicator_items();check('14 unique indicators',len(rows)==14 and len({r['key'] for r in rows})==14)
    check('no duplicate formulas stored',all('formula' not in r for r in rows))
    fixture={'rows':{},'subs':['VDF'],'cats':{}}
    state=BASE.assign(rows,fixture);before={k:v['code'] for k,v in state['rows'].items()}
    state=BASE.assign(rows,state);check('idempotent numbering',before=={k:v['code'] for k,v in state['rows'].items()})
    check('unique numbers',len(set(before.values()))==14)
    book=json.loads((BASE.VIA/SOURCE).read_text(encoding='utf-8'))
    copied=indicator_items(book,source='other_source.json');state=BASE.assign(rows+copied,state)
    check('same values different source different identities',len(state['rows'])==28)
    changed=json.loads(json.dumps(book));changed['version']='1.0.2'
    state=BASE.assign(rows+indicator_items(changed),state)
    check('version history append only',all(state['rows'][k]['code']==v for k,v in before.items()) and len(state['rows'])==42)
    try:
        duplicate=json.loads(json.dumps(book));duplicate['indicators'].append(duplicate['indicators'][0]);indicator_items(duplicate)
        check('duplicate rejected',False)
    except ValueError:
        check('duplicate rejected',True)
    check('NFKC exact aliases',normalize_labels(['ＲＳＩ',' rsi ',None,'rsi2'],[('RSI','VQG.IND.RSI')]).to_list()==['VQG.IND.RSI','VQG.IND.RSI',None,None])
    try:
        normalize_labels(['a'],[('a','one'),('Ａ','two')]);check('ambiguous alias rejected',False)
    except ValueError:
        check('ambiguous alias rejected',True)
    check('longest literal wins',replace_text_literals(['台積電與台積'],{'台積':'A','台積電':'B'}).to_list()==['B與A'])
    check('DuckDB RE2 anchored tickers',valid_tickers(['2330.TW','6488.TWO','bad2330.TW',None])==[True,True,False,False])
    check('fuzzy never changes identity',fuzzy_candidates('rsi',['RSI'])['auto_apply'] is False)
    try:
        malformed=dict(book['indicators'][0]);malformed['id']=123;validate_definition(malformed);check('strict schema rejects coercion',False)
    except ValueError:
        check('strict schema rejects coercion',True)
    check('no installer in optional tools',all(x['auto_install'] is False for x in tool_inventory()))
    check('central collector retained',BASE.collect is collect and callable(BASE.assign))
    failed=sum(not ok for _,ok in checks)
    print(f'[計] OK {len(checks)-failed} · FAIL {failed} · scope=new-contract-and-central-assign')
    return int(failed>0)


def main(argv=None):
    args=sys.argv[1:] if argv is None else argv
    if args==['tools']:
        print(json.dumps(tool_inventory(),ensure_ascii=False));return 0
    return PRIOR.main(argv)


if __name__=='__main__':
    if os.environ.get('VIA_FROM_VCGC')!='YES':
        print('[GATED] ONLY_VIA_ENTRY');raise SystemExit(2)
    try:
        raise SystemExit(selftest() if sys.argv[1:]==['--selftest'] else main())
    except ModuleNotFoundError as exc:
        print('[ABSENT] '+str(exc));raise SystemExit(3)
