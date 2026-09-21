"""VRN evidence-oriented pure functions. Inputs are official records and layout/cell adapters.
No network calls, repository writes, OCR, or invented report facts.
"""
from __future__ import annotations
import re
import statistics
import unicodedata
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import PureWindowsPath

# ===== 1. Parameters =====
OFFICIAL_SOURCES = {'TWSE', 'TPEX', 'MOPS'}
TWO_DIGIT_YEAR_BASE = 2000
MIN_SHORT_YEAR = 20
TOKEN_REGEX = r'[\u3400-\u9fff]+|[A-Za-z]+|[0-9]+|[^\u3400-\u9fffA-Za-z0-9\s]+'
CODE_REGEX = r'(?<![A-Za-z0-9])(?P<code>00[0-9]{2,4}[A-Z]?|[1-9][0-9]{3})(?P<suffix>\.(?:TWO|TW)| ?TT)?(?![A-Za-z0-9])'
FONT_TITLE_RATIO = 1.35
FONT_SUBTITLE_RATIO = 1.15
FOOTER_Y_RATIO = 0.90
RELATIVE_TOLERANCE = Decimal('0.005')
ABSOLUTE_TOLERANCE = Decimal('0.01')
CELL_KEY_FIELDS = ('ticker','period','concept','scope','currency','unit','accounting_basis')
FACT_FIELDS = ('ticker','period','value','unit','currency','kind','evidence_ids')
RELEVANT_SMALL_TEXT = r'目標|評等|評級|Rating|Target|EPS|單位|稀釋|股價|收盤|日期|[0-9]{4}年'
END_SENTENCE = r'[。！？!?]$'

# ===== 2. Filename / code / company identity =====
def normalize_text(text: str) -> str:
    return re.sub(r'[ \t\u3000]+',' ',unicodedata.normalize('NFKC',text)).strip()

def parse_filename(filename: str) -> dict:
    basename=PureWindowsPath(filename).name
    stem=re.sub(r'\.(?:pdf|docx?|txt|jpe?g|png)$','',basename,flags=re.I)
    text=normalize_text(stem)
    text=re.sub(r'\(20\)(?=[0-9]{6}(?![0-9]))','20',text)
    dates=[]
    protected=[]
    for m in re.finditer(r'(?<![0-9])[0-9]{6,8}(?![0-9])',text):
        token=m.group()
        if token.startswith('00'):
            continue
        year=None
        if len(token)==8 and token.startswith('20'):
            year=int(token[:4])
        elif len(token)==7 and token.startswith('1'):
            year=int(token[:3])+1911
        elif len(token)==6 and int(token[:2])>=MIN_SHORT_YEAR:
            year=TWO_DIGIT_YEAR_BASE+int(token[:2])
        try:
            value=date(year,int(token[-4:-2]),int(token[-2:])).isoformat() if year else None
        except ValueError:
            value=None
        dates.append({'raw':token,'iso':value,'status':'DAY' if value else 'INVALID_OR_UNKNOWN_DATE','span':list(m.span())})
        protected.append(m.span())
    for m in re.finditer(r'(?<![0-9])(?P<y>20[0-9]{2})[-/](?P<m>[0-9]{1,2})[-/](?P<d>[0-9]{1,2})(?![0-9])',text):
        try:
            value=date(int(m['y']),int(m['m']),int(m['d'])).isoformat()
        except ValueError:
            value=None
        dates.append({'raw':m.group(),'iso':value,'status':'DAY' if value else 'INVALID_OR_UNKNOWN_DATE','span':list(m.span())})
        protected.append(m.span())
    for m in re.finditer(r'(?i:CTBC)(0[1-9]|1[0-2])(0[1-9]|[12][0-9]|3[01])(?![0-9])',text):
        dates.append({'raw':m.group(),'iso':None,'month':int(m[1]),'day':int(m[2]),'status':'YEAR_MISSING','span':list(m.span())})
        protected.append(m.span())
    codes=[]
    for m in re.finditer(CODE_REGEX,text):
        if any(m.start()<b and m.end()>a for a,b in protected):
            continue
        code=m['code']
        ambiguous_year=bool(re.fullmatch(r'20[0-9]{2}',code) and not m['suffix'])
        codes.append({'raw':m.group(),'local_code':code,'suffix':m['suffix'],'span':list(m.span()),
                      'status':'YEAR_OR_STOCK_AMBIGUOUS' if ambiguous_year else 'CANDIDATE'})
        protected.append(m.span())
    tokens=[{'text':m.group().strip(),'span':list(m.span())} for m in re.finditer(TOKEN_REGEX,text)]
    return {'raw':filename,'normalized':text,'tokens':tokens,'codes':codes,'dates':dates,
            'protected_spans':protected,'span_space':'normalized_filename','company_name_source':'OFFICIAL_LOOKUP_REQUIRED'}

def official_company(ticker: str, records: list[dict], as_of: str | None = None) -> dict:
    if not re.fullmatch(r'[1-9][0-9]{3}',ticker):
        return {'status':'NOT_FOUR_DIGIT_STOCK','ticker':ticker}
    candidates=[r for r in records if r.get('ticker')==ticker and r.get('source') in OFFICIAL_SOURCES
                and r.get('source_url') and r.get('as_of')
                and (as_of is None or r['as_of']<=as_of)]
    if not candidates:
        return {'status':'OFFICIAL_LOOKUP_REQUIRED','ticker':ticker,'official_name':None}
    latest={}
    for r in candidates:
        if r['source'] not in latest or r['as_of']>latest[r['source']]['as_of']:
            latest[r['source']]=r
    # Compare the same semantic name field only; full and short names are different fields.
    securities=[r for r in latest.values() if r.get('official_security_name')]
    names={r['official_security_name'] for r in securities}
    if len(names)>1:
        return {'status':'OFFICIAL_NAME_CONFLICT','ticker':ticker,'candidates':securities}
    markets={r.get('market') for r in latest.values() if r.get('market')}
    if len(markets)>1:
        return {'status':'OFFICIAL_MARKET_CONFLICT','ticker':ticker,'candidates':list(latest.values())}
    chosen=next(iter(securities),None)
    if chosen is None:
        return {'status':'OFFICIAL_SECURITY_NAME_MISSING','ticker':ticker,'candidates':list(latest.values())}
    return {'status':'OFFICIAL_RECORD_MATCH','ticker':ticker,'official_name':chosen['official_security_name'],
            'market':next(iter(markets),None),'records':list(latest.values()),'raw_name_unchanged':True}

def crosscheck_codes(filename_codes: list[str], first_page_codes: list[str], market: str | None = None) -> dict:
    observations=[]
    for source,items in [('FILENAME',filename_codes),('PAGE1',first_page_codes)]:
        for item in items:
            m=re.fullmatch(r'(?P<code>00[0-9]{2,4}[A-Z]?|[1-9][0-9]{3})(?P<suffix>\.(?:TWO|TW)| ?TT)?',item.strip())
            observations.append({'source':source,'raw':item,'local_code':m['code'] if m else None,
                                 'suffix':m['suffix'] if m else None})
    valid=[o for o in observations if o['local_code']]
    codes={o['local_code'] for o in valid}
    markets={o['suffix'] for o in valid if o['suffix'] in ('.TW','.TWO')}
    expected={'TWSE':'.TW','TPEX':'.TWO'}.get(market)
    if len(codes)>1:
        state='MISMATCH'
    elif len(markets)>1 or expected and any(v!=expected for v in markets):
        state='MARKET_MISMATCH'
    elif any(o['local_code'] is None for o in observations):
        state='UNPARSEABLE_OBSERVATION'
    elif {o['source'] for o in valid}!={'FILENAME','PAGE1'}:
        state='INSUFFICIENT_EVIDENCE'
    else:
        state='MATCH'
    return {'status':state,'local_code':next(iter(codes)) if len(codes)==1 else None,
            'market_verified':bool(expected) and state=='MATCH','evidence':observations}

def match_broker_partial(filename: str, library: dict, excluded_names: list[str] | None = None) -> dict:
    text=normalize_text(PureWindowsPath(filename).name)
    masks=[]
    for name in excluded_names or []:
        masks.extend(m.span() for m in re.finditer(re.escape(normalize_text(name)),text,re.I))
    masks.extend(m.span() for m in re.finditer(r'(?:^|_)[1-9][0-9]{3} +[^_]+(?=_)',text))
    hits=[]
    for alias,entries in library['scopes']['broker'].items():
        raw=entries[0]['raw']
        latin=bool(re.search(r'[A-Za-z]',raw))
        rx=(r'(?<![A-Za-z])' if latin else '')+re.escape(raw)+(r'(?![A-Za-z])' if latin else '')
        for m in re.finditer(rx,text,re.I):
            if any(a<=m.start() and m.end()<=b for a,b in masks):
                continue
            hits.append({'raw':m.group(),'span':m.span(),'owners':sorted({e['canonical'] for e in entries})})
    selected=[h for h in hits if not any(v['span'][0]<=h['span'][0] and v['span'][1]>=h['span'][1]
             and v['span'][1]-v['span'][0]>h['span'][1]-h['span'][0] for v in hits)]
    owners=sorted({o for h in selected for o in h['owners']})
    return {'status':'MATCH' if len(owners)==1 else 'AMBIGUOUS' if owners else 'NO_MATCH',
            'broker':owners[0] if len(owners)==1 else None,'evidence':selected}

# ===== 3. Layout labels / conservative repair =====
def classify_page1_lines(lines: list[dict], page_height: float, body_font_size: float | None = None) -> list[dict]:
    if page_height<=0:
        raise ValueError('page_height must be positive')
    sizes=[x['font_size'] for x in lines if x.get('font_size',0)>0]
    body=body_font_size or (statistics.median(sizes) if sizes else 0)
    output=[]
    for item in lines:
        row=dict(item)
        text=normalize_text(item['text'])
        ratio=item.get('font_size',body)/body if body else 1
        relevant=bool(re.search(RELEVANT_SMALL_TEXT,text,re.I))
        region=item.get('region','UNKNOWN')
        if item['bbox'][1]/page_height>=FOOTER_Y_RATIO and ratio<1 and not relevant:
            role='FOOTER_IRRELEVANT'
        elif item.get('is_table_cell'):
            role='TABLE_CELL'
        elif region in ('LEFT_INFO','RIGHT_INFO') and relevant:
            role='FIELD_VALUE'
        elif ratio>=FONT_TITLE_RATIO and region in ('TOP','BODY'):
            role='MAIN_TITLE'
        elif ratio>=FONT_SUBTITLE_RATIO and item.get('bold') and not re.search(END_SENTENCE,text):
            role='SECTION_TITLE'
        elif relevant and ratio<1:
            role='RELEVANT_SMALL_PRINT'
        else:
            role='BODY_SENTENCE'
        row.update(clean_text=text,role=role,body_font_size=body,role_status='HEURISTIC_NEEDS_LAYOUT_QA')
        output.append(row)
    return output

def repair_lines(lines: list[dict]) -> list[dict]:
    output=[]
    for row in lines:
        value={'text':normalize_text(row.get('clean_text',row['text'])),'source_ids':[row['id']],
               'block_id':row['block_id'],'column_id':row['column_id'],'role':row['role'],
               'page':row.get('page',1),'repair_actions':[],'bbox':row['bbox']}
        previous=output[-1] if output else None
        gap=row['bbox'][1]-previous['bbox'][3] if previous else None
        compatible=bool(previous and previous['block_id']==row['block_id'] and previous['column_id']==row['column_id']
            and previous['page']==value['page'] and previous['role']==value['role']=='BODY_SENTENCE'
            and gap is not None and 0<=gap<=1.5*row.get('font_size',10)
            and abs(previous['bbox'][0]-row['bbox'][0])<=2*row.get('font_size',10)
            and not re.search(END_SENTENCE,previous['text']))
        if compatible:
            left,right=previous['text'],value['text']
            glue='' if re.search(r'[\u3400-\u9fff]$',left) and re.match(r'[\u3400-\u9fff]',right) else ' '
            previous['text']=left+glue+right
            previous['source_ids']+=value['source_ids']
            previous['repair_actions'].append('JOIN_WITHIN_SAME_BLOCK_COLUMN')
            previous['bbox']=[previous['bbox'][0],previous['bbox'][1],max(previous['bbox'][2],row['bbox'][2]),row['bbox'][3]]
        else:
            output.append(value)
    # Chinese sentence boundaries are safe; English abbreviations/decimals stay intact for an NLP adapter.
    result=[]
    for row in output:
        pieces=re.split(r'(?<=[。！？!?])',row['text']) if row['role']=='BODY_SENTENCE' else [row['text']]
        for piece in pieces:
            if piece.strip():
                result.append(dict(row,text=piece.strip()))
    return result

# ===== 4. Numeric evidence / latest-price upside / summary contract =====
def decimal_value(value) -> Decimal | None:
    if value is None or isinstance(value,bool):
        return None
    text=str(value).strip().replace(',','')
    if text in ('','—','–','-','N/A','NA','null'):
        return None
    if re.fullmatch(r'\([0-9.]+\)',text):
        text='-'+text[1:-1]
    try:
        number=Decimal(text)
        return number if number.is_finite() else None
    except InvalidOperation:
        return None

def compute_upside(target: dict, price: dict) -> dict:
    tp,close=decimal_value(target.get('value')),decimal_value(price.get('value'))
    if tp is None or close is None or tp<=0 or close<=0:
        return {'status':'MISSING_OR_INVALID_PRICE','upside_pct':None}
    required=('currency','share_basis','adjustment_basis')
    if any(not target.get(k) or not price.get(k) or target[k]!=price[k] for k in required):
        return {'status':'BASIS_MISMATCH','upside_pct':None,'target':target,'price':price}
    if price.get('price_type')!='ADJUSTED_CLOSE' or not price.get('as_of'):
        return {'status':'ADJUSTED_CLOSE_EVIDENCE_REQUIRED','upside_pct':None}
    return {'status':'CALCULATED','upside_pct':float((tp/close-1)*100),'target_price':float(tp),
            'adjusted_close':float(close),'price_as_of':price['as_of'],'formula':'(target / adjusted_close - 1) * 100',
            'provenance':'DERIVED','target_evidence':target.get('evidence_ids',[])}

def build_four_point_summary(company: dict, ticker_yahoo: str, headline: dict, facts: list[dict], upside: dict) -> dict:
    accepted=[f for f in facts if f.get('page')==1 and f.get('evidence_ids')]
    rejected=[f for f in facts if f not in accepted]
    name=company.get('official_name') if company.get('status')=='OFFICIAL_RECORD_MATCH' else None
    ticker_match=re.fullmatch(r'([1-9][0-9]{3})\.(TW|TWO)',ticker_yahoo)
    expected={'TWSE':'TW','TPEX':'TWO'}.get(company.get('market'))
    identity_ok=bool(ticker_match and ticker_match[1]==company.get('ticker') and expected==ticker_match[2])
    title=headline.get('text') if headline.get('page')==1 and headline.get('evidence_ids') else None
    groups=[('VALUATION',{'target_price','rating','valuation_method','valuation_reason','valuation_inputs'}),
            ('DILUTED_EPS',{'diluted_eps','eps_growth','eps_growth_reason'}),
            ('OPERATING_DRIVERS',{'operating_driver','highlight'}),
            ('CATALYSTS_RISKS',{'catalyst','risk','condition'})]
    points=[]
    for group,kinds in groups:
        selected=[f for f in accepted if f.get('kind') in kinds]
        points.append({'id':len(points)+1,'category':group,'facts':selected,
                       'status':'GROUNDED_FACTS' if selected else 'NOT_DISCLOSED_ON_PAGE1'})
    points[0]['current_upside']=upside
    if not any(f.get('kind')=='diluted_eps' for f in points[1]['facts']):
        points[1]['status']='DILUTED_EPS_NOT_DISCLOSED'
    return {'header':f'{name}({ticker_yahoo})-{title}' if name and title and identity_ok else None,
            'identity_status':'MATCH' if identity_ok else 'IDENTITY_UNVERIFIED',
            'points':points,'rejected_non_page1_or_ungrounded':rejected,
            'state':'STRUCTURED_SUMMARY_INPUTS','narrative_rendering':'Use only facts and evidence; no invented connective claims.'}

# ===== 5. Annual financial data comparison / arithmetic validation =====
def financial_key(cell: dict) -> tuple | None:
    if any(cell.get(k) in (None,'') for k in CELL_KEY_FIELDS):
        return None
    return tuple(cell[k] for k in CELL_KEY_FIELDS)

def within_tolerance(left: Decimal, right: Decimal, absolute=ABSOLUTE_TOLERANCE, relative=RELATIVE_TOLERANCE) -> bool:
    return abs(left-right)<=max(absolute,abs(right)*relative)

def reconcile_financial_cells(report_cells: list[dict], official_cells: list[dict], known_as_of: str | None = None) -> dict:
    output=[]
    anchors=[]
    for r in report_cells:
        key=financial_key(r)
        row={'report':r,'canonical_value':r.get('value'),'canonical_source':'REPORT','status':'UNVERIFIED'}
        if r.get('actual_or_estimate')!='ACTUAL':
            row['status']='FORECAST_PRESERVED'
            output.append(row)
            continue
        matches=[o for o in official_cells if key and financial_key(o)==key and o.get('actual_or_estimate')=='ACTUAL'
                 and o.get('source') in OFFICIAL_SOURCES and o.get('source_url') and o.get('published_at')
                 and (known_as_of is None or o['published_at']<=known_as_of)]
        if not key:
            row['status']='SEMANTIC_KEY_MISSING'
        elif matches:
            newest=max(o['published_at'] for o in matches)
            best=[o for o in matches if o['published_at']==newest]
            values={decimal_value(o.get('value')) for o in best}
            if len(values)!=1 or None in values:
                row.update(status='OFFICIAL_CONFLICT_OR_MISSING',official_candidates=best)
            else:
                o=best[0]
                a,b=decimal_value(r.get('value')),decimal_value(o['value'])
                row.update(canonical_value=o['value'],canonical_source=o['source'],official=o,
                           status='MATCH' if a is not None and within_tolerance(a,b) else 'OFFICIAL_PREFERRED_WITH_DIFFERENCE',
                           delta=float(a-b) if a is not None else None)
                if row['status']=='MATCH' and a!=0 and r.get('evidence_ids'):
                    anchors.append({'key':list(key),'report_evidence':r.get('evidence_ids',[]),'official_url':o['source_url']})
        output.append(row)
    return {'cells':output,'alignment_anchor_found':bool(anchors),'anchors':anchors,
            'extracted_cells_verified':bool(output) and all(r['status']=='MATCH' for r in output),
            'table_verified':False,
            'coverage_verified':False,'coverage_reason':'Requires source-page/table/cell inventory from document adapter.'}

def check_arithmetic(operation: str, operands: list, expected, *, same_basis: bool = False) -> dict:
    if not same_basis:
        return {'status':'BASIS_CHECK_REQUIRED'}
    numbers=[decimal_value(v) for v in operands]
    target=decimal_value(expected)
    if target is None or any(n is None for n in numbers) or not numbers:
        return {'status':'MISSING_INPUT'}
    if operation=='SUM':
        calculated=sum(numbers)
    elif operation=='SUBTRACT' and len(numbers)==2:
        calculated=numbers[0]-numbers[1]
    elif operation in ('DIVIDE','RATIO_PERCENT') and len(numbers)==2:
        if numbers[1]==0:
            return {'status':'ZERO_DENOMINATOR'}
        calculated=numbers[0]/numbers[1]*(100 if operation=='RATIO_PERCENT' else 1)
    else:
        return {'status':'UNSUPPORTED_OPERATION'}
    return {'status':'PASS' if within_tolerance(calculated,target) else 'FAIL',
            'calculated':float(calculated),'expected':float(target),'delta':float(calculated-target)}
