#!/usr/bin/env python3
PARAMS = {
    'decimal_precision':50,
    'money_target_unit':'NT$m',
    'thousand_to_million_factor':'0.001',
    'rounding_mode':'ROUND_HALF_UP',
    'output_precision':'SOURCE_INTEGER_ELSE_ONE_DECIMAL',
    'missing_tokens':['','-','--','nm','n.m.','n.a.','na','nan'],
    'source_thousand_unit_regex':r'千元|仟元|(?:NT\$|NTD|TWD)\s*\(?\s*(?:k\b|[\u2019\u0027]?000\b|thousands?\b)',
}
import copy,json,re
from decimal import Decimal,InvalidOperation,ROUND_HALF_UP,getcontext
getcontext().prec=PARAMS['decimal_precision']


def def_number(raw):
    text=re.sub(r'\s+','',str(raw or '')).replace('−','-').replace('﹣','-').replace('－','-')
    if text.lower()in PARAMS['missing_tokens']:return None
    text=text.rstrip('%');negative=text.startswith('(')and text.endswith(')')
    if negative:text=text[1:-1]
    if ','in text:
        if not re.fullmatch(r'[+-]?\d{1,3}(?:,\d{3})+(?:\.\d+)?',text):return None
        text=text.replace(',','')
    if not re.fullmatch(r'[+-]?\d+(?:\.\d+)?',text):return None
    try:value=Decimal(text)
    except InvalidOperation:return None
    return -value if negative else value


def def_places(raw):
    text=str(raw).strip().rstrip('%').rstrip(')')
    match=re.search(r'\.(\d+)$',text)
    return len(match[1])if match else 0


def def_quantum(raw):
    return Decimal(1).scaleb(-def_places(raw))


def def_source_unit(fact,table):
    unit=fact['UNIT'];metric=fact['METRIC']
    if unit in ['%','x','days']or re.search(r'EPS|DPS|BVPS|每股|每\s?股',metric,re.I):return unit
    inline=re.search(PARAMS['source_thousand_unit_regex'],metric,re.I)
    header=' '.join(r.get('raw_text','')for r in table['records']if r['component']in ['HEADER','TITLE'])
    if inline or(unit in ['NT$m','UNSPECIFIED']and not re.search(r'Ratios|比率|投資回報',table['title'],re.I)and re.search(PARAMS['source_thousand_unit_regex'],header,re.I)):
        return 'NT$k'
    return unit


def def_normalize_fact(fact,table):
    assert fact['FREQUENCY']=='ANNUAL'and re.fullmatch(r'\d{4}',fact['PERIOD'])
    raw=fact['VALUE_TRIM'];value=def_number(raw);unit=def_source_unit(fact,table)
    factor=Decimal(PARAMS['thousand_to_million_factor'])if unit=='NT$k'else Decimal(1)
    normalized=value*factor if value is not None else None
    fact.update({'SOURCE_UNIT':unit,'SOURCE_VALUE_NUMERIC':fact['VALUE_NUMERIC'],
        'SOURCE_VALUE_DECIMAL':format(value,'f')if value is not None else None,
        'UNIT':PARAMS['money_target_unit']if unit=='NT$k'else unit,'SCALE_FACTOR':format(factor,'f'),
        'VALUE_CHECK_DECIMAL':format(normalized,'f')if normalized is not None else None,
        'VALUE_CHECK_NUMERIC':float(normalized)if normalized is not None else None,
        'SOURCE_DECIMAL_PLACES':def_places(raw)if value is not None else None,
        'OUTPUT_DECIMAL_PLACES':(0 if def_places(raw)==0 else 1)if unit in ['NT$k','NT$m']and value is not None else None,
        'ROUNDING_STAGE':'PENDING_ALL_ANNUAL_CHECKS','VALUE_DISPLAY':None})
    if unit=='NT$k':fact['UNIT_STATUS']='ASSIGNED_FROM_PRINTED_THOUSAND_UNIT'
    return fact


def def_validation_views(tables,facts):
    index={}
    for fact in facts:index[(fact['TABLE_ID'],fact['METRIC'],fact['PERIOD_RAW'],fact['VALUE_TRIM'])]=fact
    views=copy.deepcopy(tables)
    for table in views:
        for row in table['records']:
            row['cells_source']=row['cells'][:];row['cell_scale_factors']=['1']*len(row['cells'])
            if row.get('semantic_component',row['component'])!='ROW':continue
            for col,meta in enumerate(table['column_metadata'],1):
                key=(table['id'],row['cells'][0],meta['raw'],row['cells'][col])
                fact=index.get(key)
                if fact is None:continue
                if fact['VALUE_CHECK_DECIMAL']is not None:row['cells'][col]=fact['VALUE_CHECK_DECIMAL']
                row['cell_scale_factors'][col]=fact['SCALE_FACTOR']
        table['validation']=[];table['validation_value_basis']='DECIMAL_NORMALIZED_BEFORE_CHECK_NO_OUTPUT_ROUNDING'
    return views


def def_legacy_equations(table,filename,restore):
    metrics={};growth=False;checks=[]
    for row in table['records']:
        if row['component']!='ROW':continue
        if re.search(r'成長|Growth',row['cells'][0],re.I):growth=True
        if re.search(r'獲利|損益|資產|Profitability|Income',row['cells'][0],re.I):growth=False
        if growth:continue
        key=restore.canonical_metric(row['cells'][0])
        if key and key not in metrics:metrics[key]=row
    rules=[('gross_profit','revenue','cost','SUBTRACT_EXPENSE'),('op_profit','gross_profit','opex','SUBTRACT_EXPENSE'),('assets','liabilities','equity','ADD'),('gross_margin','gross_profit','revenue','RATIO_PCT'),('op_margin','op_profit','revenue','RATIO_PCT'),('net_margin','net_profit','revenue','RATIO_PCT')]
    for target,a,b,operation in rules:
        if not all(k in metrics for k in [target,a,b]):continue
        for col,meta in enumerate(table['column_metadata'],1):
            assert meta['frequency']=='ANNUAL'
            raw=[metrics[k]['cells'][col]for k in [target,a,b]];numbers=[def_number(v)for v in raw]
            if None in numbers:continue
            actual,x,y=numbers
            if operation=='RATIO_PCT'and y==0:continue
            calculated=x-abs(y)if operation=='SUBTRACT_EXPENSE'else x+y if operation=='ADD'else x/y*100
            inputs=[(metrics[a],col,1),(metrics[b],col,1)]
            interval=def_formula_interval(metrics[target],col,inputs,operation)
            tolerance=interval['tolerance']
            difference=actual-calculated
            rule=f'{target}={a}{"-"if operation=="SUBTRACT_EXPENSE"else"+"if operation=="ADD"else"/"}{b}'
            checks.append({'檔案':filename,'頁碼':table['page'],'表格':table['title'],'年度':meta['period'],'算式':rule,
                '來源值':float(actual),'驗算值':float(calculated),'差異':float(difference),'容許捨入差':float(tolerance),
                '結果':'PASS'if interval['passed'] else'FAIL_REVIEW','說明':'先統一金額單位，Decimal 完整精度驗算；最終輸出才依來源格式捨入',
                '算式輸入原值':json.dumps([metrics[k].get('cells_source',metrics[k]['cells'])[col]for k in [target,a,b]],ensure_ascii=False),
                '算式輸入驗算值':json.dumps(raw,ensure_ascii=False),'驗算值完整精度':format(calculated,'f'),'差異完整精度':format(difference,'f'),'容許差完整精度':format(tolerance,'f'),'驗算區間下界':format(interval['low'],'f'),'驗算區間上界':format(interval['high'],'f'),'容差依據':'來源印刷精度區間；沒有固定寬鬆門檻'})
    return checks


def def_operand_interval(row,col):
    value=def_number(row['cells'][col])
    original=row.get('cells_source',row['cells'])[col]
    scale=Decimal(row.get('cell_scale_factors',['1']*len(row['cells']))[col])
    half=def_quantum(original)*scale/2
    return value,value-half,value+half


def def_formula_interval(target,col,inputs,operation):
    from itertools import product
    actual,al,ah=def_operand_interval(target,col)
    operands=[def_operand_interval(row,index)for row,index,sign in inputs]
    values=[o[0]for o in operands];spans=[o[1:]for o in operands]
    if operation in ['SUM','ADD']:
        calculated=sum(v*sign for v,(_,_,sign)in zip(values,inputs))
        low=sum(min(x*sign for x in span)for span,(_,_,sign)in zip(spans,inputs))
        high=sum(max(x*sign for x in span)for span,(_,_,sign)in zip(spans,inputs))
    elif operation=='SUBTRACT_EXPENSE':
        calculated=values[0]-abs(values[1]);absolute=[abs(x)for x in spans[1]]
        least=Decimal(0)if spans[1][0]<=0<=spans[1][1]else min(absolute)
        low=spans[0][0]-max(absolute);high=spans[0][1]-least
    elif operation in ['RATIO','RATIO_PCT','GROWTH']:
        if spans[1][0]<=0<=spans[1][1]:raise ValueError('DENOMINATOR_ROUNDING_INTERVAL_CONTAINS_ZERO')
        shift=1 if operation=='GROWTH'else 0
        calculated=(values[0]/values[1]-shift)*100
        corners=[(x/y-shift)*100 for x,y in product(*spans)];low,high=min(corners),max(corners)
    else:raise ValueError(operation)
    return {'calculated':calculated,'low':low,'high':high,'tolerance':(ah-al)/2+max(calculated-low,high-calculated),'passed':al<=high and low<=ah}


def def_finalize_fact(fact,all_checks_completed):
    if not all_checks_completed:raise RuntimeError('OUTPUT_ROUNDING_BEFORE_ALL_ANNUAL_CHECKS')
    raw=fact['VALUE_CHECK_DECIMAL'];places=fact['OUTPUT_DECIMAL_PLACES']
    if raw is not None and places is not None:
        rounded=Decimal(raw).quantize(Decimal(1).scaleb(-places),rounding=ROUND_HALF_UP)
        if rounded==0:rounded=abs(rounded)
        fact['VALUE_NUMERIC']=int(rounded)if places==0 else float(rounded)
        fact['VALUE_DISPLAY']=format(rounded,f'.{places}f')
        fact['ROUNDING_STAGE']='AFTER_ALL_ANNUAL_CHECKS'
    else:
        fact['VALUE_DISPLAY']=fact['VALUE_TRIM'];fact['ROUNDING_STAGE']='NOT_MONETARY_OR_SOURCE_MISSING_NO_ROUNDING'
    return fact


def def_selftest(restore=None):
    receipts=[]
    base={'FREQUENCY':'ANNUAL','PERIOD':'2026','UNIT':'NT$m','METRIC':'Revenue','VALUE_NUMERIC':None}
    cases=[('1234','NT$k','1.234','1'),('1250','NT$k','1.250','1'),('1500','NT$k','1.500','2'),('(1500)','NT$k','-1.500','-2'),('1234.5','NT$k','1.2345','1.2'),('1250.0','NT$k','1.2500','1.3'),('12.35','NT$m','12.35','12.4'),('(12.35)','NT$m','-12.35','-12.4'),('1234','NT$m','1234','1234'),('--','NT$m',None,'--'),('6.345','NT$','6.345','6.345'),('25.345%','%','25.345','25.345%')]
    for raw,unit,exact,display in cases:
        fact={**base,'UNIT':unit,'VALUE_TRIM':raw};table={'title':'Income Statement','records':[]}
        if unit=='NT$k':table['records']=[{'component':'HEADER','raw_text':'NT$ thousand / 千元'}]
        fact=def_normalize_fact(fact,table)
        assert fact['VALUE_CHECK_DECIMAL']==exact
        fact=def_finalize_fact(fact,True);assert fact['VALUE_DISPLAY']==display,(raw,fact)
        receipts.append({'測試':f'{raw} {unit}','完整精度':exact,'最終顯示':display,'結果':'PASS'})
    try:def_finalize_fact({},False)
    except RuntimeError:receipts.append({'測試':'驗算完成前禁止捨入','結果':'PASS'})
    else:raise AssertionError('Rounding gate not enforced')
    left=Decimal('1200')*Decimal('.001');right=Decimal('149')*Decimal('.001');target=Decimal('1349')*Decimal('.001')
    assert left+right==target and left.quantize(Decimal('1'))+right.quantize(Decimal('1'))!=target
    receipts.append({'測試':'先捨入會破壞加總，完整精度加總正確','結果':'PASS'})
    if restore is not None:
        for source_assets,expected_status in [('1349','PASS'),('1399','FAIL_REVIEW')]:
            labels=['資產總計','負債總計','權益總計'];values=[source_assets,'1200','149']
            table={'id':'UNIT-TEST','title':'Balance Sheet','page':1,'column_metadata':[{'raw':'2026','period':'2026','frequency':'ANNUAL'}],
                'records':[{'component':'HEADER','raw_text':'金額單位：千元','cells':['NT$千元','2026']}]+[{'component':'ROW','semantic_component':'ROW','cells':[label,value]}for label,value in zip(labels,values)]}
            facts=[]
            for label,value in zip(labels,values):
                fact={'FREQUENCY':'ANNUAL','PERIOD':'2026','PERIOD_RAW':'2026','UNIT':'NT$m','METRIC':label,'VALUE_NUMERIC':int(value),'VALUE_TRIM':value,'TABLE_ID':'UNIT-TEST'}
                facts.append(def_normalize_fact(fact,table))
            view=def_validation_views([table],facts)[0]
            checks=def_legacy_equations(view,'SYNTHETIC_UNIT_TEST_ONLY',restore)
            assert len(checks)==1 and checks[0]['結果']==expected_status
            for fact in facts:def_finalize_fact(fact,True)
            assert facts[0]['VALUE_DISPLAY']=='1' and facts[1]['VALUE_DISPLAY']=='1' and facts[2]['VALUE_DISPLAY']=='0'
            receipts.append({'測試':'完整千元轉百萬元流程 '+expected_status,'完整精度':checks[0]['差異完整精度'],'結果':'PASS','說明':'有效／無效來源最終都顯示 1=1+0；仍以未捨入值判定，避免捨入掩蓋來源差異'})
    return receipts
