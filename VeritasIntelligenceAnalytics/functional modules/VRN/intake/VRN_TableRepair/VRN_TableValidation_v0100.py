PARAMS={'version':'v0100','precision':50,'missing':['','-','--','—','N/A','NA','NM','N.M.'],
        'money_units':{'NT$k':('NT$m','0.001'),'NT$m':('NT$m','1')},'rounding':'ROUND_HALF_UP'}
import re
from decimal import Decimal,localcontext


def def_number(text,unit=None):
    raw=text.strip();compact=re.sub(r'\s*([(),.%+\-])\s*',r'\1',raw)
    missing=raw.upper() in PARAMS['missing']
    if missing:return {'source_decimal':None,'check_decimal':None,'source_unit':unit,'unit':unit,'interval':None,'output_decimal':None,'number_status':'MISSING'}
    negative=compact.startswith('(') and compact.endswith(')')
    if negative:compact=compact[1:-1]
    if compact.endswith('%'):compact=compact[:-1];unit=unit or '%'
    if not re.fullmatch(r'[+\-]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?',compact):
        return {'source_decimal':None,'check_decimal':None,'source_unit':unit,'unit':unit,'interval':None,'output_decimal':None,'number_status':'TEXT_OR_UNPARSEABLE'}
    with localcontext() as ctx:
        ctx.prec=PARAMS['precision'];value=Decimal(compact.replace(',',''))*(-1 if negative else 1)
        places=len(compact.split('.')[-1]) if '.' in compact else 0
        target,factor=PARAMS['money_units'].get(unit,(unit,'1'));factor=Decimal(factor)
        check=value*factor;half=Decimal('0.5').scaleb(-places)*factor;low=check-half;high=check+half
    return {'source_decimal':str(value),'check_decimal':str(check),'source_unit':unit,'unit':target,
            'interval':[str(low),str(high)],'source_places':places,'output_decimal':None,'number_status':'NUMBER'}


def def_formula(rule,cells):
    with localcontext() as ctx:
        ctx.prec=PARAMS['precision']
        try:inputs=[cells[key] for key in rule['inputs']];target=cells[rule['target']]
        except KeyError as exc:raise ValueError('UNKNOWN_FORMULA_CELL: '+str(exc))
        records=inputs+[target]
        if any(c['number']['check_decimal'] is None for c in records):return {'id':rule['id'],'status':'NOT_CALCULABLE','reason':'SOURCE_MISSING_OR_NON_NUMERIC'}
        if any(c['number']['unit'] is None for c in records):return {'id':rule['id'],'status':'NOT_CALCULABLE','reason':'UNITS_NOT_DECLARED'}
        periods=[c.get('period') for c in records]
        if any(p is None for p in periods):return {'id':rule['id'],'status':'NOT_CALCULABLE','reason':'PERIOD_NOT_DECLARED'}
        op=rule['op'];units=[c['number']['unit'] for c in records]
        if op!='growth' and len(set(periods))!=1:raise ValueError('FORMULA_PERIOD_MISMATCH')
        if op=='growth' and (len(inputs)!=2 or periods[0]!=periods[1]+1 or periods[-1]!=periods[0]):raise ValueError('GROWTH_PERIOD_ORDER_MISMATCH')
        if op in ['sum','difference'] and len(set(units))!=1:raise ValueError('FORMULA_UNIT_MISMATCH')
        if op in ['ratio','growth'] and (len(inputs)!=2 or units[0]!=units[1] or units[-1] not in ['%','x']):raise ValueError('RATIO_UNIT_MISMATCH')
        intervals=[tuple(Decimal(x) for x in c['number']['interval']) for c in inputs]
        values=[Decimal(c['number']['check_decimal']) for c in inputs]
        if op in ['sum','difference']:
            weights=[Decimal(str(x)) for x in rule.get('weights',[1]*len(inputs) if op=='sum' else [1,-1])]
            if len(weights)!=len(inputs):raise ValueError('INVALID_FORMULA_WEIGHTS')
            result=sum(v*w for v,w in zip(values,weights))
            low=sum(min(a*w,b*w) for (a,b),w in zip(intervals,weights));high=sum(max(a*w,b*w) for (a,b),w in zip(intervals,weights))
        elif op in ['ratio','growth']:
            (a,b),(c,d)=intervals
            if c<=0<=d:return {'id':rule['id'],'status':'NOT_CALCULABLE','reason':'DENOMINATOR_INTERVAL_CROSSES_ZERO'}
            multiplier=Decimal(100 if units[-1]=='%' else 1);offset=1 if op=='growth' else 0
            result=(values[0]/values[1]-offset)*multiplier
            limits=[(x/y-offset)*multiplier for x in (a,b) for y in (c,d)];low,high=min(limits),max(limits)
        else:raise ValueError('UNKNOWN_FORMULA_OPERATOR')
        target_low,target_high=(Decimal(x) for x in target['number']['interval'])
        return {'id':rule['id'],'status':'PASS' if max(low,target_low)<=min(high,target_high) else 'FAIL',
                'inputs':rule['inputs'],'target':rule['target'],'op':op,'calculated_decimal':str(result),
                'calculated_interval':[str(low),str(high)],'source_target_interval':[str(target_low),str(target_high)],
                'basis':'Printed precision intervals before display rounding'}


def def_validate(table,gold=None,candidates=None):
    from VRN_TableGeometry_v0100 import def_key
    cells={c['id']:c for c in table['cells']}
    for cell in cells.values():cell['number']=def_number(cell['text'],cell.get('unit'))
    equations=[def_formula(rule,cells) for rule in table.get('equations',[])]
    table['formula_checks']=equations;table['formula_status']='NOT_REQUESTED' if not equations else 'PASS' if all(x['status']=='PASS' for x in equations) else 'REVIEW'
    # Display quantization occurs only after all formula calculations have completed.
    for cell in cells.values():
        number=cell['number']
        if number['check_decimal'] is not None:
            with localcontext() as ctx:
                ctx.prec=PARAMS['precision']
                places=0 if number['source_places']==0 else 1
                number['output_decimal']=str(Decimal(number['check_decimal']).quantize(Decimal(1).scaleb(-places),rounding=PARAMS['rounding'])) if number['source_unit'] in PARAMS['money_units'] else number['check_decimal']
            number['rounding_stage']='AFTER_ALL_REQUESTED_FORMULAS'
    gold_checks=[]
    if gold is not None:
        expected={c['id']:c for c in gold['cells']}
        keys_match=set(expected)==set(cells)
        table['gold_shape_match']=keys_match and table['rows']==gold['rows'] and table['cols']==gold['cols']
        for key,cell in cells.items():
            original=expected.get(key)
            match=bool(original is not None and def_key(cell['text'])==def_key(original['text']) and cell['rowspan']==original.get('rowspan',1) and cell['colspan']==original.get('colspan',1))
            gold_checks.append({'cell_id':key,'status':'PASS' if match else 'FAIL','actual':cell['text'],'expected':original['text'] if original else None})
        table['gold_missing_cell_ids']=sorted(set(expected)-set(cells))
        table['gold_status']='PASS' if table['gold_shape_match'] and all(x['status']=='PASS' for x in gold_checks) else 'FAIL'
    else:table['gold_status']='NOT_PROVIDED'
    table['gold_checks']=gold_checks
    comparisons=[]
    actual=[['' for _ in range(table['cols'])] for _ in range(table['rows'])]
    for cell in cells.values():actual[cell['row']][cell['col']]=cell['text']
    for candidate in candidates or []:
        before=candidate['matrix'];diff=[]
        for r in range(max(len(before),len(actual))):
            old=before[r] if r<len(before) else []
            new=actual[r] if r<len(actual) else []
            for c in range(max(len(old),len(new))):
                left=old[c] if c<len(old) else None;right=new[c] if c<len(new) else None
                if left is None or right is None or def_key(left)!=def_key(right):diff.append({'row':r,'col':c,'before':left,'after':right})
        comparisons.append({'engine':candidate.get('engine','EXTERNAL'),'input_matrix':before,'differences':diff,
                             'policy':'New values reread from source; never mutate candidate or fill numeric blanks'})
    table['candidate_comparisons']=comparisons
    verified=table['gold_status']=='PASS' and table['native_check_status']=='PASS' and table['formula_status'] in ['PASS','NOT_REQUESTED']
    table['structure_status']='GOLD_SPANS_MATCH' if table['gold_status']=='PASS' else 'REQUIRES_GOLD_OR_HUMAN_REVIEW'
    table['reconstruction_status']='VERIFIED_AGAINST_GOLD' if verified else 'REVIEW'
    table['claim_scope']='Supplied table/cell scope only; not whole PDF discovery, official truth or pixel-identical typography'
    return table


def def_continuations(tables):
    """Join only explicitly linked, consecutively paged, verified segments with equal headers."""
    from VRN_TableGeometry_v0100 import def_key
    groups={}
    for table in tables:
        if table.get('continuation_group'):groups.setdefault(table['continuation_group'],[]).append(table)
    output=[]
    for name,segments in groups.items():
        segments=sorted(segments,key=lambda t:t['page']);headers=[];reasons=[]
        for t in segments:
            hr=t.get('header_rows',[])
            headers.append([(c['row'],c['col'],c['rowspan'],c['colspan'],def_key(c['text'])) for c in sorted(t['cells'],key=lambda c:(c['row'],c['col'])) if c['row'] in hr])
            if not hr or not headers[-1]:reasons.append('HEADER_REQUIRED')
            if t['reconstruction_status']!='VERIFIED_AGAINST_GOLD':reasons.append('SEGMENT_NOT_VERIFIED')
            if any(c['row'] in hr and c['row']+c['rowspan']-1 not in hr for c in t['cells']):reasons.append('SPAN_CROSSES_HEADER_BODY')
        if len(segments)<2:reasons.append('NEED_MULTIPLE_SEGMENTS')
        if len({t['cols'] for t in segments})>1 or any(h!=headers[0] for h in headers):reasons.append('HEADER_OR_COLUMN_CONFLICT')
        if any(b['page']!=a['page']+1 for a,b in zip(segments,segments[1:])):reasons.append('NONCONSECUTIVE_PAGES')
        cells=[]
        if not reasons:
            for t in segments:
                cells.extend({'source_table':t['id'],'source_page':t['page'],'cell':c} for c in t['cells'] if c['row'] not in t['header_rows'])
        output.append({'group':name,'status':'VERIFIED_EXPLICIT_CONTINUATION' if not reasons else 'REVIEW','reasons':sorted(set(reasons)),
                       'segment_ids':[t['id'] for t in segments],'body_cells':cells,'policy':'No value summation; keep source page/cell IDs; repeated identical headers referenced once'})
    return output
