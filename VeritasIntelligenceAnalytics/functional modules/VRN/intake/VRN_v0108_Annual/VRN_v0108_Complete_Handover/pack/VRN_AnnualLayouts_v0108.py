#!/usr/bin/env python3
PARAMS = {
 'input_root':'upload','row_y_tolerance':1.8,'second_reader_y_tolerance':2.6,
 'profiles':[
  {'filename':'GS-6415 20260517.pdf','sha':'ce1ebbbcf776b901428970539963c7d7f9b12ff41f78fe93c58646d115aa6992','id':'N01','broker':'Goldman Sachs','periods':['2025','2026E','2027E','2028E'],'printed':['12/25','12/26E','12/27E','12/28E'],
   'tables':[(2,'Income Statement (NT$ mn)',[311,41,564,270],55.74,'NT$m'),(2,'Balance Sheet (NT$ mn)',[311,272,564,520],287.28,'NT$m'),(2,'Cash Flow (NT$ mn)',[311,521,564,733],536.81,'NT$m'),(2,'Ratios & Valuation',[50,87,302,280],101.66,'MIXED'),(2,'Growth & Margins (%)',[50,282,302,368],297.2,'%')]},
  {'filename':'MS-2308 20251128.pdf','sha':'85f3d1eff2a36709258badcab2b19e71fddc72e45d86597f57fc3cd997684a8e','id':'N02','broker':'Morgan Stanley','periods':['2023','2024','2025E','2026E','2027E'],
   'tables':[(5,'Consolidated Income Statements',[42,141,313,290],151.22,'NT$m'),(5,'Consolidated Cash Flow Statements',[323,141,571,307],151.22,'NT$m'),(5,'Consolidated Balance Sheets',[42,330,313,539],340.36,'NT$m'),(5,'Consolidated Financial Ratios',[323,322,571,539],331.77,'MIXED')]},
  {'filename':'Daiwa-1319 20231011(20261006-122413).pdf','sha':'8117029e75b120c8e0eee65ea40d8eb92ddf13c6922a7d80353ec5bbb29a7cf8','id':'N03','broker':'Daiwa','periods':['2018','2019','2020','2021','2022','2023E','2024E','2025E'],
   'tables':[(3,'Key assumptions',[41,101,425,152],113.2,'%'),(3,'Profit and loss (TWDm)',[41,163,425,393],175.35,'NT$m'),(3,'Cash flow (TWDm)',[41,403,425,605],415.15,'NT$m'),(4,'Balance sheet (TWDm)',[41,101,425,350],113.2,'NT$m'),(4,'Key ratios (%)',[41,359,425,580],371.65,'MIXED')]}
 ],
 'excluded':[
  {'filename':'Citi-3231 20250604(20261006-122410).pdf','sha':'3bd909165b536b7f1cf45d409cbe047e527bb3a8d5013569424d441d1be86a64','reason':'第 2 頁為季／年混合盈餘預估；本次只取獨立年度財報明細，排除混合表與首頁摘要'},
  {'filename':'華南投顧-3017-奇鋐-1141202(20261006-122001).pdf','sha':'e234c75d51ba1f4015d7f471e6c9d13badfb67fb74922b63fa48d1d980517ebc','reason':'第 5 頁為年度預估修正／股利表，第 6 頁為季／月資料；無獨立年度財報明細'},
  {'filename':'瑞基(4171,NR_未評等)-CTBC251208(20261006-122004).pdf','sha':'47933b9924468f2af9b4a31c101210471a3c68d5c4be9efd43b7fc2486ec3853','reason':'SHA256 與既有瑞基原檔相同，已去重；無獨立年度財報明細'}
 ]
}
from decimal import Decimal
import hashlib,json,re
from pathlib import Path
import fitz,pdfplumber


def def_hash(path):
 return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def def_numeric_token(text):
 return bool(re.fullmatch(r'(?:[+\-−]?\(?\d[\d,]*(?:\.\d+)?%?\)?%?|--?|n\.a\.|nm|n\.m\.)',text,re.I))


def def_cells(words,right,engine):
 cells=['']*(len(right)+1);counts=[0]*len(cells)
 for word in sorted(words,key=lambda w:w['bbox'][0]):
  col=1+min(range(len(right)),key=lambda j:abs(word['bbox'][2]-right[j])) if def_numeric_token(word['text']) else 0
  cells[col]+=(' ' if cells[col] else '')+word['text'];counts[col]+=1
 return cells,[engine.def_cell_trim(c) for c in cells],counts


def def_table(path,page,other,profile,spec,index,engine):
 pno,title,box,hy,unit=spec
 words=[{'text':w[4],'bbox':list(w[:4])}for w in page.get_text('words') if box[0]<=(w[0]+w[2])/2<box[2] and box[1]<=(w[1]+w[3])/2<box[3]]
 printed=profile.get('printed',profile['periods'])
 headers=sorted([w for w in words if abs(w['bbox'][1]-hy)<.8 and w['text'] in printed],key=lambda w:w['bbox'][0])
 assert [w['text'] for w in headers]==printed,(title,headers)
 right=[w['bbox'][2]for w in headers]
 groups=[]
 for word in sorted(words,key=lambda w:((w['bbox'][1]+w['bbox'][3])/2,w['bbox'][0])):
  cy=(word['bbox'][1]+word['bbox'][3])/2
  if cy<=hy+8:continue
  group=next((g for g in groups[-3:]if abs(g['y']-cy)<=PARAMS['row_y_tolerance']),None)
  if group is None:group={'y':cy,'words':[]};groups.append(group)
  group['words'].append(word)
 second=[{'text':w['text'],'bbox':[w['x0'],w['top'],w['x1'],w['bottom']]}for w in other.extract_words(x_tolerance=1,y_tolerance=1) if box[0]<=(w['x0']+w['x1'])/2<box[2] and box[1]<=(w['top']+w['bottom'])/2<box[3]]
 records=[];audit=[];tableid=profile['id']+f'-P{pno}-T{index}'
 for group in groups:
  raw,cells,counts=def_cells(group['words'],right,engine)
  component='SOURCE'if cells[0].startswith('Source:')else'ROW'if any(cells[1:])else'SECTION'
  record={'component':component,'semantic_component':component,'row_index':len(records)+1,'page':pno,'zone':'INFO','block_id':tableid,'cells':cells,'cells_raw':raw,'cells_trim':cells,'text':' | '.join(cells),'raw_text':' '.join(w['text']for w in group['words']),'anchors':[w['bbox']for w in group['words']],'source_y':group['y'],'status':'SOURCE_TWO_READER_CALIBRATED','source_column_words':group['words']}
  records.append(record)
  if component!='ROW':continue
  assert cells[0],('EXTRA_NUMERIC_ROW',tableid,record)
  assert all(c==1 for c in counts[1:]),('EXTRA_OR_MISSING_COLUMN_TOKEN',tableid,record,counts)
  independent=[w for w in second if abs((w['bbox'][1]+w['bbox'][3])/2-group['y'])<=PARAMS['second_reader_y_tolerance']]
  _,comparison,_=def_cells(independent,right,engine)
  for col,(a,b)in enumerate(zip(cells,comparison)):
   audit.append({'row_index':record['row_index'],'column':col,'native_trim':a,'plumber_trim':b,'restored_trim':a,'status':'PASS'if a==b else'REVIEW'})
 metadata=[engine.def_period(p)for p in profile['periods']]
 for m,raw in zip(metadata,printed):m['raw']=raw
 return {'id':tableid,'report_id':profile['id'],'page':pno,'title':title,'bbox_pt':box,'period_headers':['ITEM']+printed,'printed_headers':printed,'column_metadata':metadata,'column_right_anchors':right,'column_edges_pt':[box[0],min(w['bbox'][0]for w in headers)-3]+[(a+b)/2 for a,b in zip(right,right[1:])]+[box[2]],'records':records,'source_sha256':profile['sha'],'source_text':profile['broker'],'unit_default':unit,'validation':[],'fast_validation':{'status':'PASS'if all(c['status']=='PASS'for c in audit)else'REVIEW','cells':audit},'period_basis':'Source-locked annual financial statements with successive fiscal years; printed FY end / Year End Dec / Year to 31 Dec. Month-end alone never determines annual frequency.'}


def def_sources(engine):
 sources=[];excluded=[]
 for profile in PARAMS['profiles']:
  path=Path(PARAMS['input_root'])/profile['filename'];assert def_hash(path)==profile['sha']
  tables=[]
  with fitz.open(path)as doc,pdfplumber.open(path)as second:
   for index,spec in enumerate(profile['tables'],1):tables.append(def_table(path,doc[spec[0]-1],second.pages[spec[0]-1],profile,spec,index,engine))
  sources.append({'filename':profile['filename'],'source_path':str(path.resolve()),'source_sha256':profile['sha'],'job_id':profile['id'],'metadata':{'doc_kind':'SINGLE_STOCK'},'restoration':{'tables':tables}})
 for item in PARAMS['excluded']:
  path=Path(PARAMS['input_root'])/item['filename'];assert def_hash(path)==item['sha']
  excluded.append({'檔案':item['filename'],'處理':'本版不納入','理由':item['reason'],'原檔雜湊':'PASS'})
 return sources,excluded


def def_unit(table,metric):
 if '(%)'in metric:return '%'
 if table['unit_default']=='%':return '%'
 if 'EPS' in metric or 'DPS' in metric or 'BVPS' in metric or 'BPS 'in metric or '(NT$)'in metric or '(TWD)'in metric:return 'NT$'
 if '(X)'in metric.upper() or re.search(r'cover \(x\)|ratio \(x\)',metric,re.I):return 'x'
 if re.search(r'days|inventoryday|AP/NPdays|AR/NRdays|Cashconversion',metric,re.I):return 'days'
 if table['unit_default']=='NT$m':return '%'if 'ratio (%)'in metric else'NT$m'
 if re.search(r'margin|growth|YoY|ROE|ROA|ROIC|ROCE|taxrate|equity|assets|Yield|payout|Cash div|Cash flow yield|Net debt|ROAA|net margin|gross margin',metric,re.I):return '%'
 if '(NT$)'in metric:return 'NT$'
 if metric in ['Sales','Operatingprofits','Pretaxprofits','Netprofits','Others']:return '%'
 return 'UNSPECIFIED'


def def_equations(tables,filename,engine,restore,amounts):
 rows={}
 for t in tables:
  rows[t['title']]={}
  for r in t['records']:
   if r['component']=='ROW':rows[t['title']].setdefault(engine.def_cell_trim(r['cells'][0]),r)
 ts={t['title']:t for t in tables};checks=[];skips=[]
 def check(title,target,inputs,operation,prev=False):
  table=ts[title];target=engine.def_cell_trim(target)
  inputs=[(tab,engine.def_cell_trim(label),sign)for tab,label,sign in inputs]
  if target not in rows[title]:raise ValueError('MISSING_FORMULA_LABEL:'+target)
  for col,m in enumerate(table['column_metadata'],1):
   raw=[rows[title][target]['cells'][col]]
   for tab,label,sign in inputs:
    if label not in rows[tab]:raise ValueError('MISSING_FORMULA_INPUT:'+label)
    raw.append(rows[tab][label]['cells'][col])
   if prev:
    if col==1:continue
    raw.append(rows[inputs[0][0]][inputs[0][1]]['cells'][col-1])
   nums=[amounts.def_number(x)for x in raw]
   rule=target+' = '+(' + '.join(('− 'if sign<0 else'')+label for tab,label,sign in inputs)if operation=='SUM'else f'{inputs[0][1]} / {inputs[1][1]} × 100'if operation=='RATIO'else f'({inputs[0][1]} / 前年度 − 1) × 100')
   if None in nums or(operation in ['RATIO','GROWTH']and nums[-1]==0):
    skips.append({'檔案':filename,'頁碼':table['page'],'表格':title,'年度':m['period'],'算式':rule,'結果':'NOT_CALCULABLE','理由':'來源印 --／n.a. 或分母為零；未當成 0 或 PASS'});continue
   actual=nums[0]
   operands=[(rows[tab][label],col,sign)for tab,label,sign in inputs]
   if prev:operands.append((rows[inputs[0][0]][inputs[0][1]],col-1,1))
   interval=amounts.def_formula_interval(rows[title][target],col,operands,operation)
   calculated=interval['calculated'];tolerance=interval['tolerance']
   checks.append({'檔案':filename,'頁碼':table['page'],'表格':title,'年度':m['period'],'算式':rule,'來源值':float(actual),'驗算值':float(calculated),'差異':float(actual-calculated),'容許捨入差':float(tolerance),'結果':'PASS'if interval['passed'] else'FAIL_REVIEW','說明':'原值保留；來源同年度／同版本；跨表比率與年度年增率驗算','算式輸入驗算值':json.dumps(raw,ensure_ascii=False),'驗算值完整精度':format(calculated,'f'),'差異完整精度':format(actual-calculated,'f'),'容許差完整精度':format(tolerance,'f'),'驗算區間下界':format(interval['low'],'f'),'驗算區間上界':format(interval['high'],'f'),'容差依據':'來源印刷精度區間；沒有固定寬鬆門檻'})
 def sumrule(title,target,*labels):check(title,target,[(title,label,1)for label in labels],'SUM')
 if filename.startswith('GS'):
  inc='Income Statement (NT$ mn)';bs='Balance Sheet (NT$ mn)';cf='Cash Flow (NT$ mn)';ratio='Growth & Margins (%)'
  sumrule(inc,'EBIT','EBITDA','Depreciation & amortization')
  sumrule(bs,'Total current assets','Cash & cash equivalents','Accounts receivable','Inventory','Other current assets')
  sumrule(bs,'Total assets','Total current assets','Net PP&E','Net intangibles','Total investments','Other long-term assets')
  sumrule(bs,'Total liabilities','Total current liabilities','Total long-term liabilities')
  sumrule(bs,'Total liabilities & equity','Total liabilities','Total common equity','Minority interest')
  sumrule(cf,'Cash flow from operations','Net income','D&A add-back','Minority interest add-back','Net (inc)/dec working capital','Other operating cash flow')
  sumrule(cf,'Total cash flow','Cash flow from operations','Cash flow from investing','Cash flow from financing')
  sumrule(cf,'Free cash flow','Cash flow from operations','Capital expenditures')
  for target,label in [('EBIT margin','EBIT'),('EBITDA margin','EBITDA'),('Net income margin','Net inc. (post-exceptionals)')]:check(ratio,target,[(inc,label,1),(inc,'Total revenue',1)],'RATIO')
  for target,label in [('Total revenue growth','Total revenue'),('EBITDA growth','EBITDA'),('EPS growth','EPS (diluted, post-except) (NT$)'),('DPS growth','DPS (NT$)')]:check(ratio,target,[(inc,label,1)],'GROWTH',True)
 elif filename.startswith('MS'):
  inc='Consolidated Income Statements';bs='Consolidated Balance Sheets';cf='Consolidated Cash Flow Statements';ratio='Consolidated Financial Ratios'
  sumrule(inc,'Gross profit','Net sales','COGS');sumrule(inc,'Operating income','Gross profit','Operating expenses')
  sumrule(inc,'Pre-tax income','Operating income','Non-operating income')
  sumrule(inc,'Net income','Pre-tax income','Income tax','Minority interests')
  sumrule(bs,'Total Assets','Current Assets','Long-term investments','Fixed assets','Other assets')
  sumrule(bs,'Total Liabilities','Total current liabilities','L/T debt','Other LT liabilities')
  sumrule(bs,'Total Liab./SE','Total Liabilities',"Shareholders' equity")
  sumrule(cf,'Operating CF','Net Profits','Depreciation & Amort.','Change in WC','Other adjustments')
  for target,label in [('Gross margin','Gross profit'),('Operating margin','Operating income'),('Net margin','Net income')]:check(ratio,target,[(inc,label,1),(inc,'Net sales',1)],'RATIO')
 elif filename.startswith('Daiwa'):
  inc='Profit and loss (TWDm)';bs='Balance sheet (TWDm)';cf='Cash flow (TWDm)';ratio='Key ratios (%)'
  sumrule(inc,'Total Revenue','AM','OEM-China','Other Revenue')
  sumrule(inc,'Operating profit','Total Revenue','COGS','SG&A','Other op. expenses')
  sumrule(inc,'Pre-tax profit','Operating profit','Net-interest inc./(exp.)','Assoc/forex/extraord./others')
  sumrule(inc,'Net profit (reported)','Pre-tax profit','Tax','Min. int./pref. div./others')
  sumrule(bs,'Total current assets','Cash & short-term investment','Inventory','Accounts receivable','Other current assets')
  sumrule(bs,'Total assets','Total current assets','Fixed assets','Goodwill & intangibles','Other non-current assets')
  sumrule(bs,'Total current liabilities','Short-term debt','Accounts payable','Other current liabilities')
  sumrule(bs,'Total liabilities','Total current liabilities','Long-term debt','Other non-current liabilities')
  sumrule(bs,"Shareholders' equity",'Share capital','Reserves/R.E./others')
  sumrule(bs,'Total equity & liabilities','Total liabilities',"Shareholders' equity",'Minority interests')
  sumrule(cf,'Cash flow from operations','Profit before tax','Depreciation and amortisation','Tax paid','Change in working capital','Other operational CF items')
  sumrule(cf,'Cash flow from investing','Capex','Net (acquisitions)/disposals','Other investing CF items')
  sumrule(cf,'Cash flow from financing','Change in debt','Net share issues/(repurchases)','Dividends paid','Other financing CF items')
  sumrule(cf,'Change in cash','Cash flow from operations','Cash flow from investing','Cash flow from financing','Forex effect/others')
  for target,label in [('Operating-profit margin','Operating profit'),('Net profit margin','Net profit (reported)'),('EBITDA margin','EBITDA')]:check(ratio,target,[(inc,label,1),(inc,'Total Revenue',1)],'RATIO')
  for target,label in [('Sales (YoY)','Total Revenue'),('EBITDA (YoY)','EBITDA'),('Operating profit (YoY)','Operating profit'),('Net profit (YoY)','Net profit (reported)')]:check(ratio,target,[(inc,label,1)],'GROWTH',True)
 return checks,skips
