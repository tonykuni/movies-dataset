#!/usr/bin/env python3
"""CGC237 v0115: one SSOT manager for conflict checks, central numbering and L1 sync."""
from __future__ import annotations
import argparse, importlib.util, json, os, sys, tempfile
from pathlib import Path
HERE = Path(__file__).resolve()
ENGINE = 'CGC_MDL237_NumberingSystem_v0115'
MAX_ACTIVE_RULES = 50000
MAX_REGEX_PER_SCOPE = 256
SNAPSHOT_NAME = 'SSOT_Manager_Snapshot.json'
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



def _module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module

PRIOR = _module(HERE.with_name('CGC_MDL237_NumberingSystem_v0114.py'), 'central_numbering_v0114')
BASE = PRIOR.BASE
_L1 = None
_ORIGINAL_PLAN = PRIOR.make_plan

def __getattr__(name):
    return getattr(PRIOR, name)

def l1():
    global _L1
    if _L1 is None:
        _L1 = _module(BASE.HERE.parent / '70_VRN_Rules/SUP_MDL866_VIAUnifiedNLPOrchestrator_v0107.py', 'central_manager_l1')
    return _L1

def fingerprint(value):
    return PRIOR.digest(value)

def project_rules(registered):
    """Derive an expendable view from central rows; never a second source of truth."""
    history, rules, holds = {}, [], []
    for row in registered:
        if row.get('asset_intake'):
            asset = row.get('candidate_asset', {})
            try:
                key = PRIOR.identity(asset); PRIOR.version_key(asset['version'])
            except (KeyError, TypeError, ValueError):
                holds.append({'code':row.get('code'),'reason':'INVALID_CENTRAL_ASSET','owner':row.get('sub'),'scope':row.get('scope')});continue
            history.setdefault(key, []).append(row)
        elif row.get('kind') == 'SYN' and str(row.get('cat','')).startswith('中央同義冊/') and row.get('lamp') == 'GREEN' and not row.get('gone_since'):
            rules.append({'code':row['code'],'owner':row['sub'],'scope':row['cat'].split('/',1)[1],
                'type':'SYNONYM','target':row.get('alias_of') or row['name'],'aliases':row.get('words',[]),
                'source_id':row.get('source'),'version':row.get('version'),'origin':'CENTRAL_UNION'})
    for versions in history.values():
        row=max(versions,key=lambda x:PRIOR.version_key(x['candidate_asset']['version']));a=row['candidate_asset']
        if a['asset_type'] not in ('SYNONYM','REGEX'):continue
        reason = 'INACTIVE_LATEST_VERSION' if row.get('lamp') != 'GREEN' or row.get('gone_since') else None
        try:
            checked=PRIOR.validate_candidate(a)
            if fingerprint(checked)!=row.get('definition_sha256'):reason='CENTRAL_DEFINITION_HASH_DRIFT'
            if checked['asset_type']=='REGEX':reason=reason or PRIOR.regex_check(checked)
        except (ValueError,TypeError,KeyError) as exc:reason=str(exc)
        if reason:
            holds.append({'code':row.get('code'),'owner':a.get('owner'),'scope':a.get('scope'),'reason':reason});continue
        rules.append({'code':row['code'],'owner':a['owner'],'scope':a['scope'],'type':a['asset_type'],
            'target':a['value'] if a['asset_type']=='SYNONYM' else a['semantic_key'],
            'aliases':a['aliases'] if a['asset_type']=='SYNONYM' else [],
            'pattern':a['value'] if a['asset_type']=='REGEX' else None,
            'source_id':a['source_id'],'version':a['version'],'origin':'CENTRAL_ASSET'})
    if len(rules)>MAX_ACTIVE_RULES:raise ValueError('ACTIVE_RULE_LIMIT')
    indexes, regex_groups, blocked = {}, {}, set()
    for r in rules:
        if r['type']=='SYNONYM':
            for alias in r['aliases']:
                indexes.setdefault((r['owner'],r['scope'],PRIOR.normalized(alias)),[]).append(r)
        else:regex_groups.setdefault((r['owner'],r['scope']),[]).append(r)
    for (owner,scope,term),group in indexes.items():
        if len({PRIOR.normalized(r['target']) for r in group})>1:
            codes=sorted({r['code'] for r in group});blocked.update(codes)
            holds.append({'owner':owner,'scope':scope,'term':term,'codes':codes,'reason':'ALIAS_MULTIPLE_TARGETS'})
    for (owner,scope,term),group in indexes.items():
        for r in group:
            target=PRIOR.normalized(r['target'])
            following=indexes.get((owner,scope,target),[])
            for next_rule in following:
                if PRIOR.normalized(next_rule['target'])!=target:
                    codes=sorted({r['code'],next_rule['code']});blocked.update(codes)
                    holds.append({'owner':owner,'scope':scope,'codes':codes,'reason':'ALIAS_REWRITE_CHAIN_OR_CYCLE'})
    for (owner,scope),group in regex_groups.items():
        if len(group)>MAX_REGEX_PER_SCOPE:
            blocked.update(r['code'] for r in group);holds.append({'owner':owner,'scope':scope,'reason':'REGEX_SCOPE_LIMIT'});continue
        for i,left in enumerate(group):
            for right in group[i+1:]:
                overlap=PRIOR.regex_overlap(left['pattern'],right['pattern'])
                if overlap is None or (overlap and left['target']!=right['target']):
                    codes=[left['code'],right['code']];blocked.update(codes)
                    holds.append({'owner':owner,'scope':scope,'codes':codes,'reason':'REGEX_OVERLAP_UNPROVEN' if overlap is None else 'REGEX_MULTIPLE_TARGETS'})
    active=sorted((r for r in rules if r['code'] not in blocked),key=lambda r:(r['owner'],r['scope'],r['code']))
    return {'rules':active,'holds':holds,'rules_sha256':fingerprint(active),'registration_authority':'VIA_Numbering_SSOT'}

def make_plan(candidates, registered=(), legacy=()):
    registered=list(registered);legacy=list(legacy)
    plan=_ORIGINAL_PLAN(candidates,registered,legacy)
    projected=list(registered)
    projected.extend(dict(row,code=row.get('code') or 'legacy:'+str(i)) for i,row in enumerate(legacy) if not row.get('asset_intake'))
    for i,(raw,result) in enumerate(zip(candidates,plan['results'])):
        if result['state'] not in ('READY','REGISTERED'):continue
        asset=PRIOR.validate_candidate(raw)
        projected.append({'code':'candidate:'+str(i),'asset_intake':True,'candidate_asset':asset,
                          'definition_sha256':fingerprint(asset),'lamp':'GREEN'})
    catalog=project_rules(projected)
    for hold in catalog['holds']:
        for code in hold.get('codes',[]):
            if not code.startswith('candidate:'):continue
            result=plan['results'][int(code.split(':')[1])]
            result['reasons']=sorted(set(result['reasons']+[hold['reason']]))
            result['state']='REVIEW' if 'UNPROVEN' in hold['reason'] else 'BLOCKED'
    plan['ready']=sum(x['state']=='READY' for x in plan['results'])
    plan['blocked']=sum(x['state'] in ('BLOCKED','REVIEW') for x in plan['results'])
    return plan

# Existing collect -> candidate_items resolves this stronger plan before central allocation.
PRIOR.make_plan = make_plan

def clean_managed(records, catalog, owner):
    """Owner/scope-bound synonym normalization and registered Regex full-field matching."""
    import re2, unicodedata
    if owner not in PRIOR.OWNERS:raise ValueError('OWNER_REQUIRED')
    rules=[r for r in catalog['rules'] if r['owner']==owner]
    aliases=[];lineage={};known={r['scope'] for r in rules}
    for r in rules:
        if r['type']!='SYNONYM':continue
        for term in r['aliases']:
            if not term.strip() or PRIOR.normalized(term).isdigit():continue
            aliases.append({'scope':r['scope'],'term':term,'canonical':r['target'],'rule_code':r['code']})
            lineage.setdefault((r['scope'],PRIOR.normalized(term)),set()).add(r['code'])
    result=l1().clean_batch(records,aliases)
    compiled=[(r,re2.compile(r['pattern'])) for r in rules if r['type']=='REGEX']
    for row in result['rows']:
        for match in row['exact_matches']:match['rule_codes']=sorted(lineage[(row['scope'],match['term'])])
        row['owner']=owner;row['ssot_rule_hits']=[]
        if row['original_text'] is not None:
            text=unicodedata.normalize('NFKC',row['original_text']).strip()
            row['ssot_rule_hits']=[{'rule_code':r['code'],'semantic_key':r['target'],'source_id':r['source_id']} for r,rx in compiled if r['scope']==row['scope'] and rx.fullmatch(text)]
        if row['original_text'] and any(r['scope']==row['scope'] for r,_ in compiled) and not row['ssot_rule_hits']:
            row['errors'].append({'reason':'NO_REGISTERED_REGEX_MATCH'});row['status']='QUARANTINE'
        conflicts=[h for h in catalog['holds'] if h.get('owner')==owner and h.get('scope')==row['scope']]
        if conflicts:
            row['errors'].append({'reason':'CENTRAL_RULE_CONFLICT','conflicts':conflicts});row['status']='QUARANTINE'
        elif row['scope'] not in known and row['status'] not in ('QUARANTINE','NODATA'):
            row['status']='REVIEW';row['errors'].append({'reason':'UNKNOWN_RULE_SCOPE'})
    l1().validate_frame(result['rows'])
    result['state']='PARTIAL' if result['quarantine'] or any(x['status'] in ('QUARANTINE','REVIEW') for x in result['rows']) else 'CANDIDATE'
    result['central_rules_sha256']=catalog['rules_sha256']
    return result

def save_snapshot(report, folder):
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True);path=folder/SNAPSHOT_NAME
    payload={'schema':'VIA.SSOTManager.v1','engine':ENGINE,'source_fingerprint':report['source_fingerprint'],
             'plan':report['plan'],'catalog':report['catalog']}
    expected=fingerprint(payload)
    if path.is_file():
        try:
            old=json.loads(path.read_text(encoding='utf-8'))
            if isinstance(old,dict) and old.get('sha256')==expected and fingerprint(old.get('payload'))==expected:return {'state':'REUSED','path':str(path),'sha256':expected}
        except (ValueError,UnicodeError):
            old=None  # Invalid cache is rebuilt below; central source remains authoritative.
    fd,tmp=tempfile.mkstemp(prefix='ssot_manager_',dir=folder);os.close(fd);tmp=Path(tmp)
    try:
        tmp.write_text(json.dumps({'sha256':expected,'payload':payload},ensure_ascii=False,indent=2)+'\n',encoding='utf-8');os.replace(tmp,path)
    finally:tmp.unlink(missing_ok=True)
    return {'state':'UPDATED','path':str(path),'sha256':expected}

def snapshot(candidates=None):
    path=BASE._newest(BASE.HERE,PRIOR.BOOK_PATTERN)
    if path is None:raise ValueError('NO_CANDIDATE_BOOK')
    book=PRIOR.read_book(path if candidates is None else Path(candidates))
    registered=list(BASE.load_state()['rows'].values())
    # Central published rules are the preview authority; committed apply runs the full collector again.
    legacy=[r for r in registered if not r.get('asset_intake') and r.get('kind') in ('SYN','RGX')]
    plan=PRIOR.make_plan(book['assets'],registered,legacy)
    return {'engine':ENGINE,'candidate_book':BASE._rel(path),'plan':plan,'catalog':project_rules(registered),
        'source_fingerprint':fingerprint({'candidate_book':book,'central_rows':registered,'legacy_rules':legacy})}

def manage(options):
    if options.apply and (options.action!='sync' or options.candidates):raise ValueError('APPLY_ONLY_COMMITTED_CENTRAL_SYNC')
    def execute():
        report=snapshot(options.candidates)
        report['allocation']={'requested':options.apply,'performed':False,'rc':None}
        if options.apply and report['plan']['ready']:
            # Already inside the same central writer lock. v0113 runs committed scoped allocator.
            rc=PRIOR.PRIOR.main(['--apply','--scope',report['candidate_book']])
            if rc: return {'state':'BLOCKED','allocation_rc':rc,'before':report},2
            report=snapshot();report['allocation']={'requested':True,'performed':True,'rc':rc}
            if report['plan']['ready']:
                report['state']='BLOCKED';report['reason']='CENTRAL_ALLOCATION_INCOMPLETE';return report,2
        report['state']='REVIEW' if report['plan']['blocked'] or report['catalog']['holds'] else 'READY_NOT_REGISTERED' if report['plan']['ready'] else 'SYNCED'
        if options.input:
            report['cleaned']=clean_managed(l1().read_json(options.input),report['catalog'],options.owner)
            if report['cleaned']['state']=='PARTIAL':report['state']='REVIEW'
        if options.out:
            report['snapshot']=save_snapshot(report,options.out)
            if 'cleaned' in report:report['export']=l1().export_batch(report['cleaned'],options.out)
        return report,2 if report['state'] in ('REVIEW','READY_NOT_REGISTERED') else 0
    if not options.apply:return execute()
    result=[]
    rc=PRIOR.with_writer_lock(lambda: result.append(execute()) or result[-1][1])
    return result[0] if result else ({'state':'HOLD','reason':'CENTRAL_WRITER_BUSY'},rc)

def main(argv=None):
    args=list(sys.argv[1:] if argv is None else argv)
    if args==['--selftest']:return selftest()
    if args[:1]!=['manager']:return PRIOR.main(args)
    if os.environ.get('VIA_FROM_VCGC')!='YES':print('[DENY] VCGC only');return 2
    parser=argparse.ArgumentParser(prog=ENGINE+' manager')
    parser.add_argument('action',choices=('plan','sync','conflicts','show'))
    parser.add_argument('--apply',action='store_true');parser.add_argument('--candidates')
    parser.add_argument('--input');parser.add_argument('--owner',choices=sorted(PRIOR.OWNERS),default='VCGC');parser.add_argument('--out')
    try:
        report,rc=manage(parser.parse_args(args[1:]))
    except (ValueError,TypeError,KeyError,OSError) as exc:
        print(json.dumps({'state':'BLOCKED','reason':str(exc)},ensure_ascii=False));return 2
    print(json.dumps(report,ensure_ascii=False,indent=2));return rc

def selftest():
    import copy
    from unittest.mock import patch
    checks=[]
    def check(name,value):
        checks.append(bool(value));print(('  [OK] ' if value else '  [FAIL] ')+name)
    check('prior central conflict / allocation 30-case suite',PRIOR.selftest()==0)
    def registered(assets):
        items,plan=PRIOR.candidate_items(assets,'fixture.json')
        state=BASE.assign(items,{'rows':{},'subs':['VDF','VCGC'],'cats':{}})
        return list(state['rows'].values())
    a=PRIOR.fixture('buy',asset_type='SYNONYM',scope='rating',semantic_key='buy',value='BUY',aliases=['買進','buy'])
    b=dict(a,source_id='fixture:B')
    rows=registered([a,b]);catalog=project_rules(rows)
    check('same target distinct sources keep two central codes',len(catalog['rules'])==2 and len({r['code'] for r in catalog['rules']})==2)
    incoming=[{'record_id':'r1','source_id':'feed:A','scope':'rating','text':'買進'}]
    result=clean_managed(incoming,catalog,'VDF')
    check('registered alias immediately reaches L1',result['rows'][0]['canonical_text']=='BUY')
    check('all rule source IDs preserved in match',len(result['rows'][0]['exact_matches'][0]['rule_codes'])==2)
    check('L1 input never inherits rule ID as entity ID',result['rows'][0]['ssot_code'] is None)
    check('owner boundary cannot borrow another owner rules',clean_managed(incoming,catalog,'VRN')['rows'][0]['status']=='REVIEW')
    check('unknown scope held',clean_managed([dict(incoming[0],scope='unknown')],catalog,'VDF')['state']=='PARTIAL')
    forged=copy.deepcopy(rows);forged[0]['candidate_asset']['value']='SELL'
    check('central definition digest drift held',project_rules(forged)['holds'][0]['reason']=='CENTRAL_DEFINITION_HASH_DRIFT')
    newer=dict(a,version='1.0.1',supersedes='1.0.0',aliases=['買入','buy'])
    items,_=PRIOR.candidate_items([newer],'fixture2.json',rows[:1]);newstate=BASE.assign(items,{'rows':{(r['kind'],r['key']):r for r in rows[:1]},'subs':['VDF'],'cats':{}})
    newcatalog=project_rules(list(newstate['rows'].values()))
    check('latest explicit version removes old alias from active projection',len(newcatalog['rules'])==1 and '買進' not in newcatalog['rules'][0]['aliases'])
    latest=max(newstate['rows'].values(),key=lambda r:PRIOR.version_key(r['candidate_asset']['version']));latest['gone_since']='fixture'
    check('retired latest cannot reactivate predecessor',not project_rules(list(newstate['rows'].values()))['rules'])
    c=dict(a,candidate_id='sell',source_id='fixture:C',value='SELL')
    check('NFKC alias conflict cannot receive ID',make_plan([a,c])['blocked']==2)
    chain_a=dict(a,aliases=['alpha'],value='beta');chain_b=dict(c,aliases=['beta'],value='gamma')
    check('rewrite chains blocked before numbering',make_plan([chain_a,chain_b])['blocked']==2)
    check('cycles blocked before numbering',make_plan([chain_a,dict(chain_b,value='alpha')])['blocked']==2)
    check('identical term in other owner not conflict',make_plan([a,dict(c,owner='VRN')])['blocked']==0)
    rx=PRIOR.fixture('ticker',asset_type='REGEX',scope='ticker',semantic_key='tw',value=r'^[1-9][0-9]{3}\.TW$',positive=['2330.TW'],negative=['bad'])
    regexcat=project_rules(registered([rx]));matched=clean_managed([dict(incoming[0],scope='ticker',text='2330.TW')],regexcat,'VDF')
    check('registered RE2 full-field match reaches L1',len(matched['rows'][0]['ssot_rule_hits'])==1)
    check('registered Regex rejects nonmatching input',clean_managed([dict(incoming[0],scope='ticker',text='12330.TW')],regexcat,'VDF')['rows'][0]['status']=='QUARANTINE')
    check('RE2 does not truncate invalid ticker',not clean_managed([dict(incoming[0],scope='ticker',text='12330.TW')],regexcat,'VDF')['rows'][0]['ssot_rule_hits'])
    check('overlapping Regex distinct meanings blocked',make_plan([rx,dict(rx,candidate_id='other',source_id='fixture:B',semantic_key='other')])['blocked']==2)
    check('unsupported Regex proof remains review',make_plan([dict(rx,value=r'^[0-9]+\.TW$')])['results'][0]['state']=='REVIEW')
    with tempfile.TemporaryDirectory() as tmp:
        report={'source_fingerprint':'abc','plan':{'ready':0},'catalog':catalog}
        check('automatic snapshot first build',save_snapshot(report,tmp)['state']=='UPDATED')
        check('unchanged SSOT snapshot reused',save_snapshot(report,tmp)['state']=='REUSED')
        report['source_fingerprint']='changed'
        check('source drift triggers automatic refresh',save_snapshot(report,tmp)['state']=='UPDATED')
        Path(tmp,SNAPSHOT_NAME).write_text('{bad')
        check('corrupt cache never authoritative',save_snapshot(report,tmp)['state']=='UPDATED')
        Path(tmp,SNAPSHOT_NAME).write_text('[]')
        check('wrong cache schema rebuilt',save_snapshot(report,tmp)['state']=='UPDATED')
    report={'source_fingerprint':'fixture','candidate_book':'fixture.json','plan':{'ready':1,'blocked':0},'catalog':catalog}
    final=copy.deepcopy(report);final['plan']['ready']=0
    options=argparse.Namespace(action='sync',apply=True,candidates=None,input=None,owner='VDF',out=None)
    with patch(__name__+'.snapshot',side_effect=[report,final]),patch.object(PRIOR,'with_writer_lock',side_effect=lambda f:f()),patch.object(PRIOR.PRIOR,'main',return_value=0) as allocate:
        got,rc=manage(options)
        check('single manager dispatches sole committed central allocator',rc==0 and allocate.call_args.args[0]==['--apply','--scope','fixture.json'])
    with patch(__name__+'.snapshot',return_value=final),patch.object(PRIOR,'with_writer_lock',side_effect=lambda f:f()),patch.object(PRIOR.PRIOR,'main') as allocate:
        got,rc=manage(options);check('already registered rerun allocates nothing',rc==0 and not allocate.called)
    with patch(__name__+'.snapshot',return_value=report),patch.object(PRIOR,'with_writer_lock',side_effect=lambda f:f()),patch.object(PRIOR.PRIOR,'main',return_value=0):
        got,rc=manage(options);check('allocator success without registration cannot be green',rc==2 and got['reason']=='CENTRAL_ALLOCATION_INCOMPLETE')
    with patch.object(PRIOR,'with_writer_lock',return_value=2):
        got,rc=manage(options);check('busy central writer retained',rc==2 and got['state']=='HOLD')
    print(f'[計] unified manager OK {sum(checks)} · FAIL {len(checks)-sum(checks)}; prior suite separately reported')
    return 0 if all(checks) else 1

if __name__ == '__main__':
    sys.exit(main())
