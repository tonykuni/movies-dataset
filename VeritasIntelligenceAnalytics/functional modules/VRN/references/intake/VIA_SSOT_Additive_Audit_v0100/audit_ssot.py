#!/usr/bin/env python3
"""Read-only baseline audit; writes only this delivery's generated outputs.
No repository mutations, no report-file reads, no network, no runtime installation.
"""
from __future__ import annotations
import ast
import copy
import hashlib
import html
import json
import re
import unicodedata
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

# ===== Parameters / immutable baseline =====
ROOT = Path(__file__).resolve().parent
BASE = ROOT / 'baseline'
COMMIT = '8e8e766f2c3d3aa42e89b78d643869faeb094cb4'
KEY_BRIDGE = {'BOA':'BOFA','MCQ':'MACQUARIE','JP':'JPM','JPMORGAN':'JPM',
              'MORGANSTANLEY':'MS','FIRSTSEC':'FIRST','CREDITSUISSE':'CS','IBF':'WATERLAND',
              'MEGABANK':'MEGA','HUANAN':'HUANAN'}
SCENARIOS = {'Base Case':'BASE','Bull Case':'BULL','Bear Case':'BEAR'}
QUARTER_DOT_RX = r'(?<![A-Za-z0-9])(?P<year>(?:19|20)[0-9]{2})\.Q(?P<quarter>[1-4])(?![A-Za-z0-9])'
CTBC_MMDD_RX = r'(?i:CTBC)(?P<month>0[1-9]|1[0-2])(?P<day>0[1-9]|[12][0-9]|3[01])(?![0-9])'
STOCK_EXTRACT_RX = r'(?<![A-Za-z0-9])([1-9][0-9]{3})(?: ?TT|\.(?:TWO|TW))?(?![A-Za-z0-9])'
CTBC_RATING_RX = r'\((?P<ticker>[1-9][0-9]{3}),(?P<short>NR|OW|B|N)[_,](?P<label>未評等|增加持股|買進|中立)\)'
RATING_PAIRS = {('NR','未評等'):'NOT_RATED',('OW','增加持股'):'BUY',('B','買進'):'BUY',('N','中立'):'HOLD'}
ETF_TYPES = {'PASSIVE_STOCK_ETF':r'00[0-9]{2,4}', 'ACTIVE_STOCK_ETF':r'00[0-9]{3}A',
 'PASSIVE_BOND_ETF':r'00[0-9]{3}B','ACTIVE_BOND_ETF':r'00[0-9]{3}D',
 'LEVERAGED_ETF':r'00[0-9]{3}L','INVERSE_ETF':r'00[0-9]{3}R',
 'FUTURES_ETF':r'00[0-9]{3}U','BALANCED_ETF':r'00[0-9]{3}T',
 'FOREIGN_CURRENCY_STANDARD_ETF':r'00[0-9]{3}K','FOREIGN_CURRENCY_BOND_ETF':r'00[0-9]{3}C',
 'FOREIGN_CURRENCY_LEVERAGED_ETF':r'00[0-9]{3}M','FOREIGN_CURRENCY_INVERSE_ETF':r'00[0-9]{3}S',
 'FOREIGN_CURRENCY_FUTURES_ETF':r'00[0-9]{3}V'}

# ===== Load / normalization =====
def read_json(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def write_json(name, value):
    (ROOT/name).write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n',encoding='utf-8')

def norm(value):
    return re.sub(r'\s+', ' ', unicodedata.normalize('NFKC', value)).strip().casefold()

def canonical(key):
    key = key.upper()
    return KEY_BRIDGE.get(key,key)

def add_index(index, alias, key, source):
    index[norm(alias)].append({'canonical':key,'source':source,'raw':alias})

def indexes(institution, rules, broker_list, intake):
    brokers, ratings = defaultdict(list), defaultdict(list)
    for section in ('domestic_brokers','foreign_brokers'):
        for key,item in institution[section].items():
            for alias in item['aliases']:
                add_index(brokers,alias,key,'institution.'+section)
    for item in broker_list['brokers']:
        key = canonical(item['canonical_en'])
        # Crosswalk is grounded in exact overlapping aliases, not name guessing.
        owners = {e['canonical'] for a in item['aliases'] for e in brokers.get(norm(a),[])}
        if len(owners)==1:
            key = next(iter(owners))
        elif item['canonical']=='GF':
            key='GF'
        for alias in item['aliases']:
            add_index(brokers,alias,key,'broker_list')
    for key,aliases in rules['broker']['extra_table'].items():
        for alias in aliases:
            add_index(brokers,alias,canonical(key),'field_rules.broker.extra_table')
    for key,item in institution['broker_ratings'].items():
        for alias in item['aliases']:
            add_index(ratings,alias,key,'institution.broker_ratings')
    for key,aliases in rules['rating']['canon_map'].items():
        for alias in aliases:
            add_index(ratings,alias,key,'field_rules.rating.canon_map')
    for alias,key in rules['rating']['local_scale'].items():
        add_index(ratings,alias,key,'field_rules.rating.local_scale')
    # Reproduce only the hub's documented intake mapping and collision exclusion.
    grp={'strong_buy':'BUY','buy':'BUY','hold':'HOLD','sell':'SELL','strong_sell':'SELL','not_rated':'NOT_RATED'}
    for group,aliases in intake['keyword_sets'].items():
        for alias in aliases:
            field_owners={e['canonical'] for e in ratings.get(norm(alias),[]) if e['source'].startswith('field_rules')}
            if field_owners and grp[group] not in field_owners:
                continue
            add_index(ratings,alias,grp[group],'hub.intake_words')
    # These words exist in the intake book but are not all consumed by intake_words().
    for key,item in intake['levels'].items():
        for alias in item['zh']+item['en']:
            add_index(ratings,alias,key,'intake.levels.VOCABULARY_ONLY')
    return brokers,ratings

# ===== Verbatim function isolation (never import or execute the hub module) =====
def baseline_probe(rules):
    source=(BASE/'SUP_MDL749_VRNFieldRuleHub_v0110.py').read_text(encoding='utf-8')
    tree=ast.parse(source)
    needed={'parse_date_any','parse_quarter_any','_yy2yyyy'}
    selected=ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in needed],type_ignores=[])
    namespace={'_re':re,'date_patterns':lambda:rules['date']['patterns'],
               'period_rules':lambda:rules['period'],
               '_EN_MON':{m:i+1 for i,m in enumerate('JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC'.split())}}
    exec(compile(selected,'isolated_baseline_functions','exec'),namespace)
    return {'date_20250230':namespace['parse_date_any']('20250230'),
            'quarter_3Q26':namespace['parse_quarter_any']('3Q26'),
            'quarter_2025_dot_Q1':namespace['parse_quarter_any']('2025.Q1'),
            'bb_tab_accepted':bool(re.fullmatch(rules['ticker']['platform']['corrected']['TW_BB_TICKER'],'2330\tTT')),
            'bb_compact_accepted':bool(re.fullmatch(rules['ticker']['platform']['corrected']['TW_BB_TICKER'],'3014TT')),
            'scope':'Only three isolated baseline functions and recorded regex; not an end-to-end engine test.'}

# ===== Structured differences / additive namespace =====
def compare_aliases(user, brokers, ratings, institution):
    rows=[]
    for key,aliases in user['broker_aliases'].items():
        target=canonical(key)
        for alias in aliases:
            found=brokers.get(norm(alias),[])
            owners={e['canonical'] for e in found}
            state='CONFLICT' if owners and owners!={target} else 'EXISTING' if owners else 'CANDIDATE'
            rows.append({'field':'broker','input_key':key,'canonical':target,'alias':alias,'status':state,'existing':found})
    for key,item in user['ratings'].items():
        target=key.upper()
        assert institution['broker_ratings'][target]['code']==item['code']
        for alias in item['aliases']:
            found=ratings.get(norm(alias),[])
            owners={e['canonical'] for e in found}
            state='BASELINE_DIVERGENCE' if owners and owners!={target} else 'EXISTING' if owners else 'CANDIDATE_CONTEXT_REQUIRED'
            rows.append({'field':'rating','input_key':key,'canonical':target,'code':item['code'],'alias':alias,'status':state,'existing':found})
    tp={norm(a) for a in institution['research_fields']['TARGET_PRICE']['aliases']}
    for alias in user['target_price_aliases']:
        state='EXISTING' if norm(alias) in tp else 'SEPARATE_SCENARIO_FIELD' if alias in SCENARIOS else 'CANDIDATE'
        rows.append({'field':'target_price','alias':alias,'status':state})
    return rows

def named_regexes():
    local={'STOCK':r'[1-9][0-9]{3}',**ETF_TYPES}
    local['ETF']='(?:'+'|'.join(ETF_TYPES.values())+')'
    local['SECURITY']='(?:'+local['STOCK']+'|'+local['ETF']+')'
    output={}
    for kind,body in local.items():
        for prefix,suffix in [('TW',''),('TW_YFINANCE',r'\.(?:TW|TWO)'),('TW_BLOOMBERG',' TT')]:
            output[f'{prefix}_{kind}_REGEX']='^(?:'+body+')'+suffix+r'$(?![\s\S])'
    return output

def make_overlay(diff):
    return {'schema':'VIA.SSOT.AdditiveCandidate.v1','baseline_commit':COMMIT,
      'mode':'REVIEWABLE_CANDIDATE_NOT_INSTALLED','runtime_enabled':False,
      'operations_policy':'New namespace only. No existing key, alias, code, pattern, or historical value is replaced or deleted.',
      'key_crosswalk':{'BOA':'BOFA','MCQ':'MACQUARIE','JP':'JPM','MQ':'MACQUARIE','CLST':'CLSA'},
      'key_crosswalk_note':'Crosswalk preserves source key and source registry. Compatibility gates in broker_list remain in force; this audit does not enable them.',
      'user_instruction':'有差異的也列入同義字。All differences are included with provenance; no conflicting mapping is discarded.',
      'alias_additions':[dict(x, inclusion='INCLUDED', resolution='SOURCE_SCOPED' if x['status']=='BASELINE_DIVERGENCE' else 'CONTEXT_REQUIRED') for x in diff if x['status']!='EXISTING'],
      'alias_candidate_guard':'All candidates need a field cue or exact structured field, case-insensitive longest-match, Latin boundaries; rating action and coverage status retained separately.',
      'review_queue':[{'token':'GFHK','suggested_owner':'GF','status':'NEEDS_REPORT_EVIDENCE','reason':'GF is registered; GFHK not found in inspected registries. Do not auto-map from prefix.'}],
      'scenario_aliases':SCENARIOS,
      'scenario_guard':'Scenario token alone never implies target price. Require an explicit price label/currency and preserve BASE/BULL/BEAR separately.',
      'regex_extensions':{'TW_YEAR_QUARTER_DOT_REGEX':QUARTER_DOT_RX,'CTBC_FILENAME_MMDD_REGEX':CTBC_MMDD_RX,
                          'CTBC_FILENAME_RATING_REGEX':CTBC_RATING_RX,**named_regexes()},
      'semantic_guards':{'calendar':'datetime.date; reject impossible dates','MMDD':'YEAR_MISSING, never infer current year',
                         'Note':'Report label only; not automatically NOT_RATED','ticker':'Format only; actual instrument, exchange, asset class, currency and provider listing need a security master',
                         'Bloomberg':'Strict canonical single ASCII space TT; keep compact 3014TT as a separate filename normalization observation',
                         'compatibility':'Known old acceptance is preserved in baseline. Strict new validators are opt-in and may reject old whitespace/Unicode inputs.'},
      'ticker_source':'https://twse-regulation.twse.com.tw/TW/law/DAT0201.aspx?FLCODE=FL033103',
      'ticker_scope':'14 lexical classes / 48 names. 00-prefix scope follows this repo and observed ETF identifiers; not every Taiwan security. Suffix must be the sixth character. No unverified interior-letter expansion. U/V separated; L/R/M/S do not reveal underlying assets.'}

def synonym_library(user, brokers, ratings, institution):
    """Append every supplied mapping; resolve by source namespace, never last-write-wins."""
    output={'broker':copy.deepcopy(dict(brokers)),'rating':copy.deepcopy(dict(ratings)),'target_price':{},'scenario':{}}
    for field,index in [('broker',output['broker']),('rating',output['rating'])]:
        for item in index.values():
            for record in item:
                record['inclusion']='INCLUDED_BASELINE'
    for key,aliases in user['broker_aliases'].items():
        for alias in aliases:
            output['broker'].setdefault(norm(alias),[]).append({'raw':alias,'canonical':canonical(key),'input_key':key,'source':'USER_DICTIONARY','inclusion':'INCLUDED'})
    for key,item in user['ratings'].items():
        for alias in item['aliases']:
            output['rating'].setdefault(norm(alias),[]).append({'raw':alias,'canonical':key.upper(),'code':item['code'],'source':'USER_DICTIONARY','inclusion':'INCLUDED'})
    for alias in institution['research_fields']['TARGET_PRICE']['aliases']:
        output['target_price'].setdefault(norm(alias),[]).append({'raw':alias,'canonical':'TARGET_PRICE','source':'institution.research_fields'})
    for alias in user['target_price_aliases']:
        output['target_price'].setdefault(norm(alias),[]).append({'raw':alias,'canonical':'TARGET_PRICE','source':'USER_DICTIONARY',
          'requires_price_context':True,'scenario':SCENARIOS.get(alias),'inclusion':'INCLUDED'})
    for alias,key in SCENARIOS.items():
        output['scenario'][norm(alias)]=[{'raw':alias,'canonical':key,'source':'USER_DICTIONARY','requires_price_context':True}]
    return {'schema':'VIA.Synonyms.SourceScoped.v1','baseline_commit':COMMIT,'only_add':True,
      'instruction':'差異也收錄；既有對應保留；同詞多義按來源欄位判定，無來源回傳所有候選。',
      'normalization':'NFKC + casefold + whitespace collapse; original spelling preserved in raw',
      'scopes':output,'unverified_tokens':[{'raw':'GFHK','suggested_owner':'GF','confirmed_owner':None,'inclusion':'INCLUDED_UNVERIFIED'}]}

def resolve_synonym(library, field, alias, source=None):
    matches=library['scopes'].get(field,{}).get(norm(alias),[])
    selected=[m for m in matches if source is None or m['source']==source]
    owners=sorted({m['canonical'] for m in selected})
    return {'status':'RESOLVED' if len(owners)==1 else 'SOURCE_REQUIRED' if owners else 'UNKNOWN',
            'canonical':owners[0] if len(owners)==1 else None,'candidates':owners,'evidence':selected}

# ===== Filename-only diagnostics (not a replacement production parser) =====
def extract_dates(name, rules):
    out=[]
    occupied=[]
    for p in rules['date']['patterns']:
        if p['gran']!='DAY':
            continue
        for m in re.finditer(p['rx'],name,re.I):
            if any(m.start()<end and m.end()>start for start,end in occupied):
                continue
            g=m.groups()
            if p['era'] not in ('AD','AD2','ROC'):
                continue  # The supplied filenames contain only numeric report dates.
            y=int(g[0])+(1911 if p['era']=='ROC' else 2000 if p['era']=='AD2' else 0)
            try:
                value=date(y,int(g[1]),int(g[2])).isoformat()
                status='VALID_FILENAME_DATE'
            except ValueError:
                value=None
                status='INVALID_CALENDAR_DATE'
            occupied.append(m.span())
            out.append({'raw':m.group(),'value':value,'status':status,'rule':p['id'],'span':list(m.span())})
    return out

def extract_broker(name, brokers):
    hits=[]
    subject_spans=[m.span() for m in re.finditer(r'(?:^|_)[1-9][0-9]{3} +[^_]+(?=_)',name)]
    for entries in brokers.values():
        alias=entries[0]['raw']
        ascii_token=bool(re.fullmatch(r'[A-Za-z .]+',alias))
        rx=(r'(?<![A-Za-z])'+re.escape(alias)+r'(?![A-Za-z])') if ascii_token else re.escape(alias)
        for m in re.finditer(rx,name,re.I):
            if any(a<=m.start() and m.end()<=b for a,b in subject_spans):
                continue
            hits.append((m.start(),m.end(),entries))
    maximal=[h for h in hits if not any(a<=h[0] and b>=h[1] and b-a>h[1]-h[0] for a,b,_ in hits)]
    owners=sorted({e['canonical'] for _,_,entries in maximal for e in entries})
    return {'value':owners[0] if len(owners)==1 else None,'candidates':owners,
            'status':'FILENAME_CANDIDATE' if len(owners)==1 else 'CONFLICT' if owners else 'NO_REGISTERED_ALIAS',
            'matches':sorted({name[a:b] for a,b,_ in maximal})}

def parse_filename(name, rules, brokers):
    dates=extract_dates(name,rules)
    masked=list(name)
    for d in dates:
        a,b=d['span']; masked[a:b]=' '* (b-a)
    partial=[]
    for m in re.finditer(CTBC_MMDD_RX,name):
        partial.append({'raw':m.group(),'month':int(m['month']),'day':int(m['day']),'status':'YEAR_MISSING'})
        masked[m.start():m.end()]=' '*(m.end()-m.start())
    text=''.join(masked)
    # Shield quarter/year/long numeric tokens before searching ticker candidates.
    text=re.sub(r'(?<![0-9])[1-4]Q[0-9]{2,4}(?![0-9])',' ',text,flags=re.I)
    text=re.sub(r'(?<![0-9])20[0-9]{2}(?![0-9])',' ',text)
    tickers=sorted(set(m[1] for m in re.finditer(STOCK_EXTRACT_RX,text)))
    quarters=[f'20{m[2]}-Q{m[1]}' for m in re.finditer(r'(?<![A-Za-z0-9])([1-4])Q([0-9]{2})(?![A-Za-z0-9])',name,re.I)]
    broker=extract_broker(name,brokers)
    rating=None
    if broker['value']=='CTBC':
        m=re.search(CTBC_RATING_RX,name)
        if m and (m['short'],m['label']) in RATING_PAIRS:
            rating={'value':RATING_PAIRS[m['short'],m['label']],'raw':m.group(),'scope':'CTBC_STRUCTURED_FILENAME','verified_in_document':False}
    if '初次評等買進' in name:
        rating={'value':'BUY','raw':'初次評等買進','action':'INITIATED','verified_in_document':False}
    notes=[]
    if ',Note)' in name: notes.append('Note is a report label; rating remains unknown.')
    if 'GFHK' in name: notes.append('GFHK requires evidence; no automatic GF prefix match.')
    if re.search(r'(?<![0-9])[0-9]{4}TT',name): notes.append('Compact Bloomberg-like filename token; canonical output requires one space.')
    valid=sorted({d['value'] for d in dates if d['value']})
    return {'filename':name,'broker':broker,'report_date':valid[0] if len(valid)==1 else None,
      'date_status':'FILENAME_CANDIDATE' if len(valid)==1 else 'CONFLICT' if len(valid)>1 else 'YEAR_MISSING' if partial else 'NO_COMPLETE_DATE',
      'date_evidence':dates,'partial_dates':partial,'ticker_candidates':tickers,'security_master_verified':False,
      'quarter':quarters,'rating':rating,'notes':notes,'first_page_crosscheck':'NOT_RUN_NO_FILE_BYTES'}

# ===== Verification / generated evidence =====
def verify(rows, overlay, probes, snapshot_before, library, user):
    byname={r['filename']:r for r in rows}
    checks={}
    checks['sample_count_106']=len(rows)==106
    checks['no_year_in_ticker']=all('2026' not in r['ticker_candidates'] for r in rows)
    checks['image_number_not_date_or_ticker']=not byname['926708.jpg']['report_date'] and not byname['926708.jpg']['ticker_candidates']
    checks['MMDD_no_invented_year']=all(byname[f'主動式ETF籌碼追蹤-CTBC09{d}.pdf']['date_status']=='YEAR_MISSING' for d in ('15','16'))
    checks['ROC_1141128']=byname['華南投顧-6143-振曜-1141128.pdf']['report_date']=='2025-11-28'
    checks['compact_BB_3014']=byname['3014TT-20231005.pdf']['ticker_candidates']==['3014']
    checks['CLST_registered']=byname['CLST-6669 20251001.pdf']['broker']['value']=='CLSA'
    checks['JP_registered']=byname['JP-2330 20250718.pdf']['broker']['value']=='JPM'
    checks['GFHK_not_guessed']=byname['GFHK - Apple update 20260915.pdf']['broker']['value'] is None
    checks['Note_not_NR']=all(r['rating'] is None for r in rows if ',Note)' in r['filename'])
    checks['invalid_calendar_rejected']=extract_dates('20250230',read_json(BASE/'VRN_FieldRules_SSOT_v0100.json')['rules'])[0]['value'] is None
    checks['baseline_invalid_date_reproduced']=probes['date_20250230'].get('iso')=='2025-02-30'
    checks['baseline_dot_quarter_gap_reproduced']=probes['quarter_2025_dot_Q1']=={}
    checks['new_dot_quarter']=bool(re.fullmatch(QUARTER_DOT_RX,'2025.Q1'))
    rx=overlay['regex_extensions']
    checks['48_ticker_names']=len(named_regexes())==48
    checks['strict_BB_space']=bool(re.fullmatch(rx['TW_BLOOMBERG_STOCK_REGEX'],'2330 TT')) and not re.fullmatch(rx['TW_BLOOMBERG_STOCK_REGEX'],'2330\tTT')
    checks['ETF_legacy_lengths']=all(re.fullmatch(rx['TW_PASSIVE_STOCK_ETF_REGEX'],x) for x in ('0050','00878','006208'))
    checks['ETF_currency_missing_suffixes_added']=all(re.fullmatch(rx['TW_ETF_REGEX'],'00123'+s) for s in 'CKMSV')
    checks['fullwidth_and_trailing_newline_rejected']=not re.search(rx['TW_STOCK_REGEX'],'２３３０') and not re.search(rx['TW_STOCK_REGEX'],'2330\n')
    checks['synthetic_type_partition']=all(sum(bool(re.fullmatch('^(?:'+b+')$', '00123'+s)) for b in ETF_TYPES.values())==1 for s in 'ABCDKLMRSTUV')
    checks['baseline_bytes_unchanged']=all(hashlib.sha256(p.read_bytes()).hexdigest()==v for p,v in snapshot_before.items())
    checks['no_crosscheck_claim']=all(r['first_page_crosscheck']=='NOT_RUN_NO_FILE_BYTES' for r in rows)
    checks['all_new_regex_compile']=all(re.compile(v) is not None for v in rx.values())
    checks['company_name_not_broker']=byname['凱基投顧_2891 中信金_施志鴻_20260519.pdf']['broker']['value']=='KGI'
    checks['all_differences_included']=all(x['inclusion']=='INCLUDED' for x in overlay['alias_additions'])
    checks['all_user_rating_aliases_preserved']=all(any(e['raw']==a and e['canonical']==k.upper() and e['source']=='USER_DICTIONARY' for e in library['scopes']['rating'][norm(a)]) for k,v in user['ratings'].items() for a in v['aliases'])
    checks['all_user_broker_aliases_preserved']=all(any(e['raw']==a and e['input_key']==k for e in library['scopes']['broker'][norm(a)] if e['source']=='USER_DICTIONARY') for k,v in user['broker_aliases'].items() for a in v)
    checks['Accumulate_conflict_not_overwritten']=resolve_synonym(library,'rating','Accumulate')['candidates']==['ADD','BUY']
    checks['source_scoped_user_Accumulate']=resolve_synonym(library,'rating','Accumulate','USER_DICTIONARY')['canonical']=='BUY'
    checks['source_scoped_baseline_Accumulate']=resolve_synonym(library,'rating','Accumulate','field_rules.rating.canon_map')['canonical']=='ADD'
    return {'checks':checks,'passed':sum(checks.values()),'total':len(checks),'all_passed':all(checks.values()),
            'limits':'Tests validate this diagnostic and isolated baseline findings, not current production wiring, broker compatibility gates, or actual report pages.'}

def main():
    snapshot={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in BASE.glob('*') if p.is_file()}
    institution=read_json(BASE/'VIA_Financial_Institution_SSOT_v0100.json')['registries']
    rules=read_json(BASE/'VRN_FieldRules_SSOT_v0100.json')['rules']
    user=read_json(ROOT/'user_aliases.json')
    brokers,ratings=indexes(institution,rules,read_json(BASE/'broker_list.json'),read_json(BASE/'intake_rating.json'))
    diff=compare_aliases(user,brokers,ratings,institution)
    overlay=make_overlay(diff)
    library=synonym_library(user,brokers,ratings,institution)
    rows=[parse_filename(n,rules,brokers) for n in (ROOT/'sample_filenames.txt').read_text(encoding='utf-8').splitlines() if n]
    probes=baseline_probe(rules)
    conflicts={field:{alias:entries for alias,entries in index.items() if len({e['canonical'] for e in entries})>1} for field,index in [('broker',brokers),('rating',ratings)]}
    qa=verify(rows,overlay,probes,snapshot,library,user)
    summary={'baseline_commit':COMMIT,'sample_count':len(rows),'full_date_count':sum(r['report_date'] is not None for r in rows),
             'ticker_candidate_count':sum(bool(r['ticker_candidates']) for r in rows),'broker_candidate_count':sum(r['broker']['value'] is not None for r in rows),
             'rating_candidate_count':sum(r['rating'] is not None for r in rows),'date_status':dict(Counter(r['date_status'] for r in rows)),
             'alias_status':dict(Counter(x['status'] for x in diff)),'cross_registry_conflicts':{k:len(v) for k,v in conflicts.items()},'qa':qa}
    for name,obj in [('SYNONYM_LIBRARY.json',library),('ALIAS_COMPARISON.json',diff),('ADDITIVE_CANDIDATE.json',overlay),('FILENAME_RESULTS.json',rows),
                     ('BASELINE_PROBES.json',probes),('CROSS_REGISTRY_CONFLICTS.json',conflicts),('AUDIT_SUMMARY.json',summary)]:
        write_json(name,obj)
    columns=['#','檔名','券商候選','日期候選','代碼候選','評等候選','日期狀態']
    table=['<tr>'+''.join('<th>'+html.escape(c)+'</th>' for c in columns)+'</tr>']
    for i,r in enumerate(rows,1):
        values=[i,r['filename'],r['broker']['value'] or '待核實',r['report_date'] or '—',', '.join(r['ticker_candidates']) or '—',(r['rating'] or {}).get('value','—'),r['date_status']]
        table.append('<tr>'+''.join('<td>'+html.escape(str(v))+'</td>' for v in values)+'</tr>')
    (ROOT/'FILENAME_RESULTS.html').write_text('<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><title>VIA SSOT 檔名測試</title><style>body{font:15px system-ui;margin:28px;color:#172735}table{border-collapse:collapse;width:100%}th,td{border:1px solid #dce3e8;padding:9px;text-align:left}th{background:#e7f2f5;position:sticky;top:0}tr:nth-child(even){background:#f7f9fa}h1{font-size:24px}</style><h1>VIA SSOT：106 個檔名的候選擷取</h1><p>基準 '+COMMIT+'。僅分析使用者貼上的檔名；未取得報告檔案，未核驗首頁或證券主檔。此頁是獨立診斷器輸出，不代表現役引擎通過率。</p><table>'+''.join(table)+'</table></html>',encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False,indent=2))
    if not qa['all_passed']:
        raise SystemExit(1)

if __name__=='__main__':
    main()
