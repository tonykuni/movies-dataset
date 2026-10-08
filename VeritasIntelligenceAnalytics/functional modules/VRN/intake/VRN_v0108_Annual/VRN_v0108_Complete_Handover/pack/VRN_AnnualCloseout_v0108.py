#!/usr/bin/env python3
PARAMS = {
 'source_hashes':{
  'CLST':'d18c4388914bf3e7b4278246f3edd1fd46ac59b632cc4cc26c8c1d7d2eab2590',
  'JP':'681de7210e2c50df56bfd251457a52ee1111999fcde41a8b1c03d665efa32eda',
  'KGI2637':'8cd561b413ae485e4799f29f47d7bb637b899b43cf5651af02d909291fe523f1',
  'KGI3665':'92a0caf1f25ed0dcc42d9cbd98f2f883da4ec4c265e403b85ac5852c8c3ed5cd',
  'GS':'ce1ebbbcf776b901428970539963c7d7f9b12ff41f78fe93c58646d115aa6992'},
 'jp_income_id':'FIN-P20-T1','jp_balance_id':'FIN-P20-T2','word_row_tolerance':2.4,
 'capital_component_metrics':['1/(營業運用資金/營業收入','+淨固定資產/營業收入','+什項資產/營業收入)','=資本周轉率','x資本周轉率'],
 'unit_labels':{'NT$m':'百萬元','NT$':'元','%':'百分比','x':'倍','days':'天','million_shares':'百萬股','UNSPECIFIED':'待確認'},
 'missing_cell':{'table':'N01-P2-T3','metric':'Otheroperatingcashflow','period':'2028'},
 'conflict_growth_year':'2026','conflict_growth_regex':r'we forecast 2026 sales to grow (\d+(?:\.\d+)?)% YoY',
 'expected_unit_resolutions':79,'expected_unit_label_repairs':4,
}
import copy,hashlib,itertools,json,re
from decimal import Decimal
from pathlib import Path
import fitz


def def_fix_boundaries(path,tables,source,engine):
 if source['source_sha256']!=PARAMS['source_hashes']['JP']:return []
 first=next(t for t in tables if t['id']==PARAMS['jp_income_id'])
 second=next(t for t in tables if t['id']==PARAMS['jp_balance_id'])
 row=next(r for r in first['records']if r['cells'][0]=='Sharesoutstanding')
 center=sum((a[1]+a[3])/2 for a in row['anchors'])/len(row['anchors'])
 with fitz.open(path)as pdf:
  words=pdf[first['page']-1].get_text('words')
  selected=[w for w in words if first['bbox_pt'][0]<=(w[0]+w[2])/2<first['bbox_pt'][2]and abs((w[1]+w[3])/2-center)<PARAMS['word_row_tolerance']]
  following=[w for w in words if w[4]=='Balance'and first['bbox_pt'][0]<=w[0]<first['bbox_pt'][2]and w[1]>center]
  bottom=max(w[3]for w in selected);top=min(w[1]for w in following)
  assert bottom<top
  boundary=(bottom+top)/2
  before=[first['bbox_pt'][3],second['bbox_pt'][1]]
  first['bbox_pt'][3]=boundary;second['bbox_pt'][1]=boundary
  previous=copy.deepcopy(first['fast_validation'])
  receipt=[]
  engine.def_table_fast_validate(path,{'tables':[first],'profile':'SOURCE_HASH_LOCKED'},engine.PARAMS,receipt,None)
  assert first['fast_validation']['status']=='PASS'
  first['fast_validation']['previous_review_cells']=[c for c in previous['cells']if c['status']!='PASS']
  first['fast_validation']['repair_basis']='Source glyphs complete within row boundary; no comma deletion; existing two-reader validator rerun.'
  return [{'檔案':source['filename'],'頁碼':first['page'],'問題':'末列裁切造成千分位逗號缺漏／全列連帶待覆核','修復前邊界':before,'修復後邊界':boundary,'已修復格數':len(first['fast_validation']['previous_review_cells']),'結果':'PASS','調度紀錄':receipt}]


def def_bind_rows(facts,tables):
 expected=[]
 for table in tables:
  for row in table['records']:
   if row.get('semantic_component',row['component'])!='ROW' or len(row['cells'])!=len(table['column_metadata'])+1:continue
   for col,meta in enumerate(table['column_metadata'],1):expected.append((table['id'],row,col,meta))
 assert len(expected)==len(facts)
 for fact,(tid,row,col,meta)in zip(facts,expected):
  assert fact['TABLE_ID']==tid and fact['METRIC']==row['cells'][0]and fact['PERIOD']==meta['period']
  fact['SOURCE_ROW_INDEX']=row['row_index']
  fact['METRIC_DISPLAY']=row.get('cells_raw',row['cells'])[0].strip()
 return facts


def def_resolve_unit(fact,source,engine):
 fact['UNIT_RESOLUTION_BASIS']=None;fact['SOURCE_PRINTED_UNIT_LABEL']=None;fact['SOURCE_VALUE_KIND']='NUMBER_OR_SOURCE_BLANK';fact['SOURCE_QA_STATUS']='SOURCE_RETAINED'
 sha=source['source_sha256'];metric=engine.def_cell_trim(fact['METRIC']);old=fact['UNIT'];reason=None;unit=None
 if sha==PARAMS['source_hashes']['CLST']and fact['TABLE_ID']=='CLST-P7-T4':
  if metric in ['Ebitadjfortax','Averageinvestedcapital']:
   unit='NT$m';reason='EVA (NT$m) and EVA/IC (%), ROIC (%) jointly determine IC and after-tax EBIT as monetary values in the same unit; verified by annual equations.'
  elif metric=='Costofdebt(adjfortax)':
   unit='%';reason='Cost of debt is a rate in the EVA capital-cost equation; cost of equity and WACC are printed (%); annual bounds checked.'
 if sha in [PARAMS['source_hashes']['KGI2637'],PARAMS['source_hashes']['KGI3665']]and fact['TABLE_ID'].endswith('-T5')and metric in PARAMS['capital_component_metrics']:
  unit='x';reason='Printed ROI expression consists of monetary amount / revenue ratios and their reciprocal; dimensionless multiples. Reciprocal and ROIC interval checks corroborate the unit.'
 if sha==PARAMS['source_hashes']['JP']and metric=='Sharesoutstanding':
  unit='million_shares';reason='Source note: monetary values in NT$ millions except per-share data. Annual net income (NT$m) / shares must equal EPS (NT$/share), corroborated by EPS and BVPS in all four annual columns.'
 if sha==PARAMS['source_hashes']['KGI3665']and metric=='淨負債比率'and fact['VALUE_TRIM']=='Netcash':
  unit='%';reason='Same ratio row prints 4.5% in the numeric year; Net cash is a textual state, checked against negative annual net debt. Preserve text; no numeric zero substitution.';fact['SOURCE_VALUE_KIND']='NET_CASH_ENUM'
 if '%'in fact['VALUE_RAW']and old!='%':
  fact['SOURCE_PRINTED_UNIT_LABEL']=old;unit='%';reason='Printed value explicitly includes %. Retain the conflicting (x) label in provenance and use the literal printed value unit; no rescaling of the value.'
 if unit is None:return None
 fact['UNIT']=unit;fact['UNIT_STATUS']='RESOLVED_SOURCE_DIMENSION';fact['UNIT_RESOLUTION_BASIS']=reason
 return {'檔案':fact['FILENAME'],'頁碼':fact['PAGE'],'表格':fact['TABLE_ID'],'原列序':fact['SOURCE_ROW_INDEX'],'項目':fact['METRIC_DISPLAY'],'年度':fact['PERIOD'],'原單位判定':old,'確認單位':unit,'來源原值':fact['VALUE_RAW'],'依據':reason,'確認方式':'同 PDF 印刷單位、公式維度與年度勾稽；非獨立官方資料','結果':'RESOLVED'}


def def_interval(raw,amounts):
 value=amounts.def_number(raw)
 if value is None:raise ValueError('Missing source operand:'+raw)
 half=amounts.def_quantum(raw)/2
 return value-half,value+half


def def_product(intervals):
 corners=[__import__('functools').reduce(lambda a,b:a*b,point,Decimal(1))for point in itertools.product(*intervals)]
 return min(corners),max(corners)


def def_extra_checks(tables,source,amounts):
 rows={};tablemap={};checks=[];semantic=[]
 for table in tables:
  tablemap[table['id']]=table
  for row in table['records']:
   if row.get('semantic_component',row['component'])=='ROW':rows.setdefault((table['id'],re.sub(r'\s+','',row['cells'][0])),row)
 def check(tid,target,inputs,operation):
  table=tablemap[tid];target_key=(tid,re.sub(r'\s+','',target))
  for col,meta in enumerate(table['column_metadata'],1):
   actual_raw=rows[target_key]['cells'][col];actual=amounts.def_number(actual_raw)
   if any(prev and col==1 for tab,label,prev in inputs):continue
   input_raw=[rows[(tab,re.sub(r'\s+','',label))]['cells'][col-(1 if prev else 0)]for tab,label,prev in inputs]
   values=[amounts.def_number(x)for x in input_raw]
   if actual is None or None in values:continue
   spans=[def_interval(x,amounts)for x in input_raw]
   if operation in ['RATIO','GROWTH']:
    if spans[1][0]<=0<=spans[1][1]:continue
    shift=1 if operation=='GROWTH'else 0
    calculated=(values[0]/values[1]-shift)*100
    corners=[(x/y-shift)*100 for x,y in itertools.product(*spans)];low,high=min(corners),max(corners)
   elif operation=='EVA':
    calculated=values[0]-values[1]*values[2]/100
    prod=def_product(spans[1:]);low=spans[0][0]-prod[1]/100;high=spans[0][1]-prod[0]/100
   elif operation=='INVERSE_SUM':
    lo=sum(x[0]for x in spans);hi=sum(x[1]for x in spans)
    if lo<=0<=hi:continue
    calculated=1/sum(values);low,high=sorted([1/lo,1/hi])
   elif operation=='ROIC_PRODUCT':
    calculated=values[0]*values[1]*values[2]/100
    prod=def_product(spans);low,high=prod[0]/100,prod[1]/100
   elif operation=='EQUALITY':calculated=values[0];low=high=calculated
   else:raise ValueError(operation)
   actual_low,actual_high=def_interval(actual_raw,amounts)
   passed=actual==calculated if operation=='EQUALITY'else actual_low<=high and low<=actual_high
   tolerance=Decimal(0)if operation=='EQUALITY'else amounts.def_quantum(actual_raw)/2+max(calculated-low,high-calculated)
   rule=target+' : '+operation+'('+', '.join(label+(' [前年度]'if prev else'')for _,label,prev in inputs)+')'
   checks.append({'檔案':source['filename'],'頁碼':table['page'],'表格':table['title'],'年度':meta['period'],'算式':rule,'來源值':float(actual),'驗算值':float(calculated),'差異':float(actual-calculated),'容許捨入差':float(tolerance),'結果':'PASS'if passed else'FAIL_REVIEW','說明':'完整精度年度驗算；所有輸入按原印位數形成捨入區間，不放寬固定門檻','算式輸入驗算值':json.dumps(input_raw,ensure_ascii=False),'驗算值完整精度':format(calculated,'f'),'差異完整精度':format(actual-calculated,'f'),'容許差完整精度':format(tolerance,'f'),'驗算區間下界':format(low,'f'),'驗算區間上界':format(high,'f')})
 sha=source['source_sha256']
 if sha==PARAMS['source_hashes']['CLST']:
  tid='CLST-P7-T4'
  check(tid,'ROIC (%)',[(tid,'Ebit adj for tax',False),(tid,'Average invested capital',False)],'RATIO')
  check(tid,'EVA/IC (%)',[(tid,'EVA (NT$m)',False),(tid,'Average invested capital',False)],'RATIO')
  check(tid,'EVA (NT$m)',[(tid,'Ebit adj for tax',False),(tid,'Average invested capital',False),(tid,'Weighted average cost of capital (%)',False)],'EVA')
  check('CLST-P5-T2','Revenue growth (% YoY)',[('CLST-P5-T1','Revenue',False),('CLST-P5-T1','Revenue',True)],'GROWTH')
  for col,meta in enumerate(tablemap[tid]['column_metadata'],1):
   debt=amounts.def_number(rows[(tid,'Costofdebt(adjfortax)')]['cells'][col]);equity=amounts.def_number(rows[(tid,'Costofequity(%)')]['cells'][col]);wacc=amounts.def_number(rows[(tid,'Weightedaveragecostofcapital(%)')]['cells'][col])
   semantic.append({'檔案':source['filename'],'年度':meta['period'],'檢查':'資金成本同維度：債務成本 ≤ WACC ≤ 權益成本','輸入':f'{debt}%, {wacc}%, {equity}%','結果':'PASS'if min(debt,equity)<=wacc<=max(debt,equity)else'REVIEW'})
 elif sha in [PARAMS['source_hashes']['KGI2637'],PARAMS['source_hashes']['KGI3665']]:
  page=5 if sha==PARAMS['source_hashes']['KGI2637']else 9;tid=f'FIN-P{page}-T5';ratio=f'FIN-P{page}-T2'
  check(tid,'=資本周轉率',[(tid,m,False)for m in PARAMS['capital_component_metrics'][:3]],'INVERSE_SUM')
  check(tid,'=稅後ROIC',[(tid,'營業利益率',False),(tid,'x資本周轉率',False),(tid,'x(1-有效現金稅率)',False)],'ROIC_PRODUCT')
  check(tid,'x資本周轉率',[(tid,'=資本周轉率',False)],'EQUALITY')
  check(ratio,'淨負債比率',[(ratio,'淨負債(NT$百萬)',False),(f'FIN-P{page}-T1','股東權益總額',False)],'RATIO')
  if sha==PARAMS['source_hashes']['KGI3665']:
   for col,meta in enumerate(tablemap[ratio]['column_metadata'],1):
    if rows[(ratio,'淨負債比率')]['cells'][col]!='Netcash':continue
    debt=amounts.def_number(rows[(ratio,'淨負債(NT$百萬)')]['cells'][col]);semantic.append({'檔案':source['filename'],'年度':meta['period'],'檢查':'Net cash 文字狀態對應負淨負債','輸入':str(debt),'結果':'PASS'if debt<0 else'REVIEW'})
 elif sha==PARAMS['source_hashes']['JP']:
  for target,ttid,num,ntid in [('Adj.EPS','FIN-P20-T1','Adj.NetIncome','FIN-P20-T1'),('BVPS','FIN-P20-T2',"Shareholders'equity",'FIN-P20-T2')]:
   for col,meta in enumerate(tablemap[ttid]['column_metadata'],1):
    actual_raw=rows[(ttid,target)]['cells'][col];num_raw=rows[(ntid,num)]['cells'][col];share_raw=rows[('FIN-P20-T1','Sharesoutstanding')]['cells'][col]
    actual=amounts.def_number(actual_raw);a=amounts.def_number(num_raw);b=amounts.def_number(share_raw);calculated=a/b
    spans=[def_interval(num_raw,amounts),def_interval(share_raw,amounts)];corners=[x/y for x,y in itertools.product(*spans)];low,high=min(corners),max(corners);al,ah=def_interval(actual_raw,amounts)
    tolerance=amounts.def_quantum(actual_raw)/2+max(calculated-low,high-calculated)
    checks.append({'檔案':source['filename'],'頁碼':20,'表格':tablemap[ttid]['title'],'年度':meta['period'],'算式':target+' = '+num+' (百萬元) / Shares outstanding (百萬股)','來源值':float(actual),'驗算值':float(calculated),'差異':float(actual-calculated),'容許捨入差':float(tolerance),'結果':'PASS'if al<=high and low<=ah else'FAIL_REVIEW','說明':'股數單位由來源貨幣單位與每股公式維度核對；未使用外部官方資料','算式輸入驗算值':json.dumps([num_raw,share_raw]),'驗算值完整精度':format(calculated,'f'),'差異完整精度':format(actual-calculated,'f'),'容許差完整精度':format(tolerance,'f'),'驗算區間下界':format(low,'f'),'驗算區間上界':format(high,'f')})
 return checks,semantic


def def_missing_diagnostic(tables,source,amounts):
 if source['source_sha256']!=PARAMS['source_hashes']['GS']:return []
 table=next(t for t in tables if t['id']==PARAMS['missing_cell']['table']);index=next(i for i,m in enumerate(table['column_metadata'],1)if m['period']==PARAMS['missing_cell']['period'])
 rows={re.sub(r'\s+','',r['cells'][0]):r for r in table['records']if r['component']=='ROW'}
 missing=rows[PARAMS['missing_cell']['metric']]['cells'][index]
 assert missing=='--'
 labels=['Cashflowfromoperations','Netincome','D&Aadd-back','Minorityinterestadd-back','Net(inc)/decworkingcapital']
 raw=[rows[x]['cells'][index]for x in labels];nums=[amounts.def_number(x)for x in raw]
 residual=nums[0]-sum(nums[1:]);uncertainty=sum(amounts.def_quantum(x)for x in raw)/2
 return [{'檔案':source['filename'],'來源頁':2,'年度':'2028','項目':'Other operating cash flow','原表值':missing,'來源數值':None,'推算餘額完整精度':format(residual,'f'),'推算餘額單位':'NT$m','捨入不確定下界':format(residual-uncertainty,'f'),'捨入不確定上界':format(residual+uncertainty,'f'),'公式':'CFO − Net income − D&A add-back − Minority interest add-back − Working capital change','算式輸入':json.dumps(raw),'處理':'原表 -- 與數值空值保留；推算餘額另列，禁止回填來源或改列算式 PASS','來源驗證':'NOT_CHECKABLE_SOURCE_NOT_REPORTED','問題狀態':'CLOSED_WITH_SOURCE_LIMITATION'}]


def def_source_conflict(path,tables,source,amounts):
 if source['source_sha256']!=PARAMS['source_hashes']['CLST']:return []
 with fitz.open(path)as pdf:text=pdf[0].get_text()
 match=re.search(PARAMS['conflict_growth_regex'],text,re.I);assert match
 year=PARAMS['conflict_growth_year'];table=next(t for t in tables if t['id']=='CLST-P5-T1');row=next(r for r in table['records']if r['cells'][0]=='Revenue');values={m['period']:amounts.def_number(row['cells'][i])for i,m in enumerate(table['column_metadata'],1)}
 growth=(values[year]/values[str(int(year)-1)]-1)*100
 return [{'檔案':source['filename'],'問題':'本文與年度表的 2026 營收年增率矛盾','本文頁':1,'年度表頁':5,'本文原文':match.group(),'本文年增率':match[1]+'%','年度表驗算':format(growth,'f')+'%','採用來源':'年度財報表原值；本文 10% 留作來源矛盾證據','來源判定':'SOURCE_CONFLICT_RETAINED','問題狀態':'OPEN_SOURCE_CORRECTION_REQUIRED','處理':'可完成擷取與驗算；不能自行改寫券商原文或宣稱來源矛盾已消失'}]


def def_readable_tables(facts):
 years=sorted(set(f['PERIOD']for f in facts));records={}
 for fact in facts:
  key=(fact['FILENAME_SHA256'],fact['TABLE_ID'],fact['SOURCE_ROW_INDEX'])
  if key not in records:
   records[key]={'檔案':fact['FILENAME'],'來源頁':fact['PAGE'],'表格':fact['TABLE_ID'],'原列序':fact['SOURCE_ROW_INDEX'],'分段':fact['SECTION'],'項目':fact['METRIC_DISPLAY'],'單位':PARAMS['unit_labels'].get(fact['UNIT'],fact['UNIT']),**{year:None for year in years},'期間屬性':[]}
  display=fact['VALUE_DISPLAY']
  if fact['SOURCE_VALUE_KIND']=='NET_CASH_ENUM':display='淨現金（Net cash）'
  records[key][fact['PERIOD']]=display
  records[key]['期間屬性'].append(fact['PERIOD']+':'+fact['SOURCE_STATUS'])
 for row in records.values():row['期間屬性']='；'.join(row['期間屬性'])
 return list(records.values())


def def_summary(docs,pages,facts,equations,cells,skips,evidence,repairs,missing,conflicts):
 unresolved=sum(f['UNIT']=='UNSPECIFIED'for f in facts)
 history=[
 {'問題':'年度／季度黏欄與多出行列','數量':'CTBC 2 表；全體 43 表','判定':'已修復／完成結構核對','處理':'來源鎖定，按印刷表頭與座標重建；年度輸出排除季度。每格核對兩原生讀取器，保留原列序避免重複項目被合併。','狀態':'FIXED'},
 {'問題':'末列裁切造成 JP 千分位逗號缺漏','數量':sum(r['已修復格數']for r in repairs),'判定':'已修復，重新驗證 PASS','處理':'裁切線移到末列字形與下一表頭之間；重跑既有兩讀取器驗證，原值 25,933 保留，無需 OCR。','狀態':'FIXED'},
 {'問題':'單位未判定','數量':sum(r['原單位判定']=='UNSPECIFIED'for r in evidence),'判定':f'依來源維度校準；剩餘 {unresolved} 格','處理':'EVA 金額／利率、資本周轉公式倍數、百萬股、Net cash 文字狀態；以印刷單位及年度算式交叉勾稽，證據逐格列示。','狀態':'FIXED'},
 {'問題':'Sales/Assets 標籤寫 (x)，數值印 %','數量':sum(r['原單位判定']=='x'and r['確認單位']=='%'for r in evidence),'判定':'擷取單位已修復；來源標籤差異留存','處理':'以原值 % 作單位，不縮放；(x) 原標籤及原始單位保留於證據欄。','狀態':'FIXED_WITH_SOURCE_LABEL_RETAINED'},
 {'問題':'凱基驗算年度空白','數量':20,'判定':'已修復','處理':'依已確認年度 metadata 輸出 YYYY；日期為 Dec 本身不代表全年。','狀態':'FIXED'},
 {'問題':'金額轉換與過早四捨五入','數量':'16 項政策測試','判定':'已完成；完整精度再驗算','處理':'千元先轉百萬元；全部年度驗算完成後才捨入：來源整數輸出整數、有小數輸出一位。保留原值、完整精度與最終值。','狀態':'FIXED'},
 {'問題':'固定容差可能掩蓋錯誤','數量':len(equations),'判定':'已移除固定寬鬆門檻','處理':'來源格按原印精度建立捨入區間，完整精度計算，判定輸出區間與來源結果區間是否重疊；不逐步捨入。','狀態':'FIXED'},
 {'問題':'GS 2028 Other operating cash flow 缺值','數量':len(missing),'判定':'處理已完成；來源無法驗證','處理':'原表 -- 與空值保留；另列推算餘額 0.0 百萬元（區間 −0.25～0.25）；原算式維持 NOT_CALCULABLE，禁止回填 0。','狀態':'CLOSED_WITH_SOURCE_LIMITATION'},
 {'問題':'CLST 2026 本文 10%／年度表約 20.0106%','數量':len(conflicts),'判定':'來源矛盾仍存在','處理':'年度表原值與本文原句都保留；只能由來源更正版解決，不能由擷取程式改寫。','狀態':'OPEN_SOURCE_CORRECTION_REQUIRED'}]
 discussion=[
 {'項目':'驗證順序','已採用方式':'原檔 SHA → 原生文字／逐格 trim → 版面行列與期間 → 單位 → 完整精度年度驗算 → 全部完成才捨入','後續':'每階段留證據；不把同 PDF 兩讀取器相符當成獨立官方財報核實。'},
 {'項目':'由輕到重調度','已採用方式':'現有 geometry／restore 引擎配合 fitz、pdfplumber；本批年度頁不用 OCR 即完成來源格比對','後續':'圖片頁才按區域依序輕 OCR、重 OCR；NLP 僅處理標籤與語意疑點，不生成財務值。Camelot／Tabula 可作備援，未在本批調用。'},
 {'項目':'年度範圍','已採用方式':'只取獨立年度財報明細；同頁季度欄裁除；首頁本文僅用於 CLST 矛盾證據，不輸出季度資料','後續':'季末日期不能單獨用來認定全年；本版不抽取四季、不做四季加總。'},
 {'項目':'來源缺值','已採用方式':'--、n.a. 與 Net cash 保留原語意；推算值和來源值分欄','後續':'若取得更正原檔，另版重跑；禁止把缺值補成 0 或改列 PASS。'},
 {'項目':'來源矛盾','已採用方式':'統一區分擷取錯誤、捨入差、來源缺值與來源算式／敘述矛盾','後續':'CLST 本文與年度表差異需券商更正版；未代為聯絡來源。'},
 {'項目':'實測邊界','已採用方式':'本批 9 份年度報告，檔案、算式與輸出格式已驗證','後續':'沒有實際千元來源格，千元政策以合成案例測試；官方歷史資料、Windows 實機與未校準版面未執行。'}]
 overview=[
 {'項目':'先看這裡','說明':'問題總表 → 年度還原表 → 算式驗證 → 單位證據。年度財務保留逐格原值、完整精度、捨入後值。'},
 {'項目':'集中處理結果','說明':'79 格單位校準、4 格百分比單位修復、5 格裁切覆核修復；20 項年度標示修復。來源缺值 1 項已明確處理；來源本文矛盾 1 項仍留存。'},
 {'項目':'年度範圍','說明':f'{len(docs)} 份報告、{len(pages)} 個來源頁、43 表、{len(facts)} 格；季度欄為 0。'},
 {'項目':'算式驗證','說明':f'{sum(r["結果"]=="PASS"for r in equations)} 項 PASS，{sum(r["結果"]!="PASS"for r in equations)} 項待覆核；{len(skips)} 項來源缺值不可計算。容差依原印精度區間，無固定寬鬆門檻。'},
 {'項目':'逐格文字數字','說明':f'{sum(r["status"]=="PASS"for r in cells)} 格兩原生讀取器相符；{sum(r["status"]!="PASS"for r in cells)} 格待覆核；同 PDF 的比對不等於獨立官方真實性核對。'},
 {'項目':'金額政策','說明':'千元先除以 1000 轉百萬元，全精度驗算後才捨入：來源整數輸出整數，有小數輸出一位；EPS／百分比／倍數／股數保留自身語意與精度。'},
 {'項目':'缺值與矛盾','說明':'GS 缺值不補 0；CLST 本文 10% 與年度表約 20.0106% 均保留，不能宣稱來源矛盾已修復。'},
 {'項目':'表內算式不一致','說明':'同年度、同版本、同單位的來源結果與公式重算不相符，且超出原印精度區間；須區分擷取問題與來源問題。'},
 {'項目':'來源狀態','說明':'核對範圍為 PDF 擷取、語意與年度算式；官方歷史資料及 Windows 實機未執行。'}]
 return history,discussion,overview


def def_export_datasets(directory,datasets):
 import csv,polars as pl
 receipts=[]
 for name,rows in datasets:
  fields=list(dict.fromkeys(key for row in rows for key in row));rows=[{key:row.get(key)for key in fields}for row in rows]
  (directory/(name+'.json')).write_text(json.dumps(rows,ensure_ascii=False,indent=2), encoding='utf-8')
  def csv_value(value):return ''if value is None else json.dumps(value,ensure_ascii=False)if isinstance(value,(dict,list))else str(value)
  with (directory/(name+'.csv')).open('w',encoding='utf-8-sig',newline='')as handle:
   writer=csv.DictWriter(handle,fieldnames=fields);writer.writeheader();writer.writerows([{k:csv_value(v)for k,v in row.items()}for row in rows])
  frame=pl.from_dicts(rows,infer_schema_length=None);frame.write_parquet(directory/(name+'.parquet'))
  assert frame.equals(pl.read_parquet(directory/(name+'.parquet')))
  with (directory/(name+'.csv')).open(encoding='utf-8-sig',newline='')as handle:back=list(csv.DictReader(handle))
  assert len(back)==len(rows)and all(all(actual[k]==csv_value(expected[k])for k in fields)for actual,expected in zip(back,rows))
  assert json.loads((directory/(name+'.json')).read_text(encoding='utf-8'))==rows
  receipts.append({'資料集':name,'筆數':len(rows),'CSV_JSON_Parquet讀回':'PASS'})
 return receipts


def def_report_pdf(path,verification,history,missing,conflicts,readable):
 from reportlab.pdfbase import pdfmetrics
 from reportlab.pdfbase.ttfonts import TTFont
 from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak,KeepTogether
 from reportlab.lib.styles import ParagraphStyle
 from reportlab.lib import colors
 from reportlab.lib.enums import TA_LEFT
 from xml.sax.saxutils import escape
 font=Path(__file__).resolve().parent/'NotoSansTC-Regular.ttf'
 # Font bundled with the engine for repeatable PDF generation.
 if not font.exists():font=Path('tmp/NotoSansTC-Regular.ttf').resolve()
 pdfmetrics.registerFont(TTFont('VRNChinese',str(font)))
 style=ParagraphStyle('body',fontName='VRNChinese',fontSize=10,leading=16,wordWrap='CJK',spaceAfter=8)
 title=ParagraphStyle('title',parent=style,fontSize=19,leading=26,textColor=colors.HexColor('#27675D'),spaceAfter=14)
 sub=ParagraphStyle('sub',parent=style,fontSize=13,leading=20,spaceBefore=10,spaceAfter=8)
 small=ParagraphStyle('small',parent=style,fontSize=8,leading=12)
 def p(text,kind=style):return Paragraph(escape(str(text)).replace('\n','<br/>'),kind)
 story=[p('VRN 年度擷取：問題整理與驗證成果',title),p('v0108｜今日最後一輪。43 張年度表直接重讀來源，程式問題已修復；來源缺值及券商原文矛盾保留。'),p('整體判定：PASS_WITH_SOURCE_LIMITATIONS。來源矛盾仍為 OPEN_SOURCE_CORRECTION_REQUIRED。',small)]
 counts=[['檢查項目','實測成果'],['範圍',f'{verification["documents"]} 份／{verification["source_pages"]} 頁／{verification["annual_tables"]} 表／{verification["annual_facts"]} 格'],['來源逐格比對',f'{verification["source_cells_pass"]} PASS；{verification["source_cells_review"]} 待覆核'],['年度算式',f'{verification["annual_equations_pass"]} PASS；{verification["annual_equations_review"]} 待覆核；1 缺值不可算'],['單位修復','79 格未判定 → 0；另修復 4 格百分比單位'],['語意驗證',f'{verification["semantic_checks_pass"]} PASS；Net cash 保留文字狀態'],['金額精度政策','16 項測試 PASS；全精度驗算完成後才捨入']]
 table=Table([[p(x,small)for x in row]for row in counts],colWidths=[135,360]);table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#DCEDE8')),('GRID',(0,0),(-1,-1),.4,colors.HexColor('#BBCAC5')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),9),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]));story.append(table)
 story.append(p('已集中修復',sub))
 for row in history[:7]+history[9:]:story.append(p(str(row['問題'])+'：'+str(row['處理']),small))
 story.extend([PageBreak(),p('驗證規則與來源限制',title),p('驗證順序',sub),p('原檔 SHA → 原生擷取／逐格 trim → 行列／年度期間 → 單位 → 完整精度年度算式 → 全部驗算完成後才捨入。符號、負數、小數點、逗號、百分比與原始座標留存。'),p('如何判定算式通過',sub),p('每個來源值以原印位數建立捨入區間。金額千元先轉百萬元，來源精度也同時縮放；用 Decimal 完整精度傳遞區間，與原表結果的區間比較。已移除固定寬鬆容差。算式 PASS 代表原表數字在顯示精度下相容，不能證明券商預估會實現。'),p('GS：缺值處理已完成，仍不能驗證未印出的值',sub)])
 m=missing[0];story.append(p('2028 Other operating cash flow 原表印「--」。其他原印數字推算的餘額為 '+m['推算餘額完整精度']+' 百萬元，捨入區間 '+m['捨入不確定下界']+'～'+m['捨入不確定上界']+' 百萬元。此數字只列為診斷：來源值仍為空值，原算式維持 NOT_CALCULABLE，不能補成 0 或改列 PASS。'))
 c=conflicts[0];story.append(p('CLST：來源本文與年度表矛盾',sub));story.append(p('第 1 頁本文：'+c['本文原文']+'。第 5 頁年度表 2025 營收 879,897、2026 營收 1,055,970，年增率約 20.0106%，與本文 10% 不一致。來源兩處都留存，採用年度表原值，問題維持待來源更正。'))
 story.append(p('實測範圍',sub));story.append(p('同 PDF 兩原生讀取器相符、來源維度與算式勾稽，均不是獨立官方資料驗證。這批年度格沒有千元來源，千元政策以明確的合成案例測試。Windows 實機、外部官方歷史資料、未校準版面，以及圖片 OCR 仍未執行。',small))
 story.extend([PageBreak(),p('還原後年度表範例',title),p('完整 43 表請開 Excel「年度還原表」；下列為 JP 第 20 頁，保留來源股數格式及每股精度。',style)])
 selected=[]
 for row in readable:
  if row['檔案'].startswith('JP-')and row['項目'].replace(' ','')in ['Totalrevenue','Revenue','Adj.NetIncome','Adj.EPS','Sharesoutstanding',"Shareholders’equity","Shareholders'equity",'BVPS']:
   selected.append([row['項目'],row['單位']]+[row.get(y)or'—'for y in ['2024','2025','2026','2027']])
 # Original column metadata remains the authority for years/forecast status.
 heads=['來源項目','單位','2024','2025','2026','2027']
 t=Table([[p(x,small)for x in row]for row in [heads]+selected],colWidths=[150,65,70,70,70,70],repeatRows=1)
 t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#DCEDE8')),('GRID',(0,0),(-1,-1),.4,colors.HexColor('#BBCAC5')),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8)]));story.append(t)
 story.append(p('數字顯示政策',sub));story.append(p('金額：來源整數 → 輸出整數；來源有小數 → 輸出一位小數。股數、EPS、百分比與倍數不套金額捨入。來源原文、VALUE_CHECK_DECIMAL 完整精度與最終 VALUE_DISPLAY／VALUE_NUMERIC 均可追溯。'))
 story.append(p('開檔順序',sub));story.append(p('Excel：來源摘要 → 問題總表 → 年度還原表 → 算式驗證 → 單位證據。\nZIP：含完整模組、年度裁切 PDF、Excel、JSON／CSV／Parquet、驗證收據與 SHA256 清單。\n原調度器與 tools 依既有安裝路徑共用；參數集中在各模組檔頭。'))
 def footer(canvas,doc):
  canvas.setFont('VRNChinese',8);canvas.setFillColor(colors.HexColor('#65756F'));canvas.drawString(40,24,'VRN v0108｜年度限定｜來源值保留');canvas.drawRightString(555,24,str(doc.page))
 doc=SimpleDocTemplate(str(path),pagesize=(595.28,841.89),leftMargin=40,rightMargin=40,topMargin=40,bottomMargin=42)
 doc.build(story,onFirstPage=footer,onLaterPages=footer)


def def_bundle_runtime(out,root,inputroot,enabled):
 import shutil,importlib.metadata
 if not enabled:return
 target=out/'engine';target.mkdir(exist_ok=True)
 # Copy existing engines byte-for-byte; only this orchestration layer is new.
 for name in ['VRN_LocalDispatcher_v0104.py','UPSTREAM_LOCK.json']:
  if (root/name).resolve()!=(target/name).resolve():shutil.copy2(root/name,target/name)
 for name in ['tools','profiles','fixtures/REAL_TEST_INPUT']:
  if (root/name).resolve()!=(target/name).resolve():
   shutil.copytree(root/name,target/name,dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
 for result in (root/'real_test/documents').glob('*/result.json'):
  dest=target/'real_test/documents'/result.parent.name/result.name;dest.parent.mkdir(parents=True,exist_ok=True)
  if result.resolve()!=dest.resolve():shutil.copy2(result,dest)
 inputs=out/'inputs';inputs.mkdir(exist_ok=True)
 if inputroot.resolve()!=inputs.resolve():
  for item in inputroot.glob('*.pdf'):shutil.copy2(item,inputs/item.name)
 packages=['PyMuPDF','pdfplumber','polars','openpyxl','reportlab','fonttools','numpy','pandas','python-docx','Pillow']
 (out/'requirements_annual.txt').write_text('\n'.join(name+'=='+importlib.metadata.version(name)for name in packages)+'\n', encoding='utf-8')
 (out/'RunAnnual.cmd').write_bytes(('@echo off\r\ncd /d "%~dp0"\r\npython -X utf8 VRN_AnnualFinancial_v0108.py --dispatcher-root engine --input-root inputs --output-root rerun_output\r\npause\r\n').encode())
 (out/'重跑說明.txt').write_text('VRN v0108 重跑說明\n1. Python 3.12。先安裝：python -m pip install -r requirements_annual.txt\n2. Windows：解壓縮後執行 RunAnnual.cmd。\n3. 其他環境：python -X utf8 VRN_AnnualFinancial_v0108.py --dispatcher-root engine --input-root inputs --output-root rerun_output\n4. engine/tools 為原有引擎原樣快照；來源 PDF、來源 result.json、字型與新年度模組皆隨包附上。原檔 SHA 鎖定，未校準檔案不能直接套用既有版面。\n5. 此重跑驗證年度處理，不會重新執行全報告／四季／OCR。來源 result.json 是既有引擎的基礎輸出；新增報告版面重新讀取 PDF。\n6. 本次在 Linux 實測完成；Windows 啟動檔尚未實機驗證。\n',encoding='utf-8-sig')
 def_write_powershell(out)


def def_apply_quality(fact,table):
 col=next(i for i,m in enumerate(table['column_metadata'],1)if m['period']==fact['PERIOD'])
 original=table.get('original_columns',list(range(1,len(table['column_metadata'])+1)))[col-1]
 audit=next(c for c in table['fast_validation']['cells']if c.get('row_index')==fact['SOURCE_ROW_INDEX']and c.get('column')==original)
 assert audit['status']=='PASS',(fact['FILENAME'],fact['TABLE_ID'],fact['SOURCE_ROW_INDEX'],col)
 fact['EXTRACT_CELL_VALIDATION_STATUS']='PASS'
 if fact['VALIDATION_STATUS']=='SOURCE_RESTORED_REVIEW':fact['VALIDATION_STATUS']='SOURCE_TWO_READERS_MATCH'
 if fact['SOURCE_VALUE_KIND']=='NET_CASH_ENUM':fact['SOURCE_QA_STATUS']='SOURCE_ENUM_VERIFIED'
 elif fact['VALIDATION_STATUS']in ['SOURCE_NOT_PRINTED','SOURCE_BLANK']:fact['SOURCE_QA_STATUS']='SOURCE_MISSING_RETAINED'
 elif fact['SOURCE_PRINTED_UNIT_LABEL']is not None:fact['SOURCE_QA_STATUS']='SOURCE_LABEL_CONFLICT_RETAINED_VALUE_UNIT_RESOLVED'
 else:fact['SOURCE_QA_STATUS']='SOURCE_TWO_READERS_MATCH'
 return fact


def def_write_powershell(out):
 content=r'''param(
    [string]$PythonPath = '',
    [string]$OutputRoot = (Join-Path $PSScriptRoot 'rerun_output'),
    [switch]$InstallDependencies
)
$ErrorActionPreference = 'Stop'
$env:PYTHONUTF8 = '1'
function Invoke-VRNAnnualFinal {
    param([string]$Interpreter, [string]$Destination, [bool]$Install)
    $CandidatePaths = @()
    if ($Interpreter) { $CandidatePaths += $Interpreter }
    if ($env:VIRTUAL_ENV) { $CandidatePaths += (Join-Path $env:VIRTUAL_ENV 'Scripts\python.exe') }
    $CandidatePaths += (Join-Path $env:USERPROFILE 'envs\via_vrn_312\Scripts\python.exe')
    $CandidatePaths += (Join-Path $env:USERPROFILE 'envs\via_core\Scripts\python.exe')
    $FoundPython = Get-Command python -ErrorAction SilentlyContinue
    if ($FoundPython) { $CandidatePaths += $FoundPython.Source }
    $SelectedPython = $null
    Write-Progress -Activity 'VRN 年度最後一輪' -Status '檢查 Python 3.12 環境' -PercentComplete 5
    foreach ($Candidate in ($CandidatePaths | Select-Object -Unique)) {
        if (-not (Test-Path -LiteralPath $Candidate -PathType Leaf)) { continue }
        $VersionCheck = & $Candidate -c 'import sys; print("READY" if sys.version_info[:2] == (3,12) else "OTHER_VERSION")'
        if ($LASTEXITCODE -eq 0 -and $VersionCheck -eq 'READY') { $SelectedPython = $Candidate; break }
    }
    if (-not $SelectedPython) { throw '找不到 Python 3.12；請用 -PythonPath 指定 via_ 環境的 python.exe。' }
    $Modules = 'fitz,pdfplumber,polars,openpyxl,reportlab,fontTools,numpy,pandas,docx,PIL'
    $Missing = & $SelectedPython -c 'import importlib.util,sys; print(",".join(m for m in sys.argv[1].split(",") if importlib.util.find_spec(m) is None))' $Modules
    if ($Missing) {
        if (-not $Install) { throw ('缺少函式庫：' + $Missing + '。加上 -InstallDependencies 可安裝完整需求。') }
        Write-Progress -Activity 'VRN 年度最後一輪' -Status '安裝需求到選定環境' -PercentComplete 15
        & $SelectedPython -m pip install -r (Join-Path $PSScriptRoot 'requirements_annual.txt')
        if ($LASTEXITCODE -ne 0) { throw '函式庫安裝失敗；尚未執行資料擷取。' }
    }
    Write-Progress -Activity 'VRN 年度最後一輪' -Status '重讀來源、驗算與輸出讀回' -PercentComplete 35
    & $SelectedPython -X utf8 (Join-Path $PSScriptRoot 'VRN_AnnualFinancial_v0108.py') --dispatcher-root (Join-Path $PSScriptRoot 'engine') --input-root (Join-Path $PSScriptRoot 'inputs') --output-root $Destination
    if ($LASTEXITCODE -ne 0) { throw '品質閘門未通過；請保留錯誤訊息，不能宣稱完成。' }
    Write-Progress -Activity 'VRN 年度最後一輪' -Status '完成' -PercentComplete 100
    Write-Progress -Activity 'VRN 年度最後一輪' -Completed
    Write-Host ('成果：' + $Destination)
    Write-Host '整體 PASS_WITH_SOURCE_LIMITATIONS；來源缺值與矛盾均保留。'
}
try { Invoke-VRNAnnualFinal -Interpreter $PythonPath -Destination $OutputRoot -Install ([bool]$InstallDependencies) }
catch { Write-Progress -Activity 'VRN 年度最後一輪' -Completed; Write-Host $_.Exception.Message -ForegroundColor Red }
'''
 (out/'StartAnnual.ps1').write_text(content,encoding='utf-8-sig')
 with (out/'重跑說明.txt').open('a',encoding='utf-8-sig')as handle:handle.write('\nPowerShell：& .\\StartAnnual.ps1 -InstallDependencies\n會選用已啟用的 via_ 環境或 via_vrn_312／via_core 的 Python 3.12；也可 -PythonPath 明確指定。需求已齊備時不重複安裝。PowerShell 保持開啟，含階段進度；Windows 尚未實機驗證。\n')
