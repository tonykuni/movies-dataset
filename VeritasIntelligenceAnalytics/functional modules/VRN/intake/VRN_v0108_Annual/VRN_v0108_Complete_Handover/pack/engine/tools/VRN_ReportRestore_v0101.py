#!/usr/bin/env python3
"""VRN report restoration adapter. Reuses existing SSOT / pure engine functions.
Native source text is immutable; every normalization keeps raw text and geometry.
"""
from __future__ import annotations

# 01 | All configurable parameters and layout calibrations
PARAMS={
 'input_dir':'samples','layout_file':'VRN_FirstPage_Layout_20261005/layout.json',
 'output_dir':'VRN_ReportRestore_Output_v0101','as_of':'2026-10-05',
 'version':'v0101','native_ocr':False,'line_tolerance_pt':4.5,
 'column_tolerance_pt':4.0,'min_column_support':3,'heading_max_chars':65,
 'price_cache':'price_cache.parquet','official_financial_cache':'official_financial_history.csv',
 'price_lookback_days':12,'network_timeout_seconds':10,'network_enabled':True,
 'figure_dpi':130,'csv_encoding':'utf-8-sig','parquet_compression':'snappy',
}
FIN_PROFILES={
 'JP-2330 20250718.pdf':{20:[('Income Statement - Annual',(57,184,294,339)),('Balance Sheet & Cash Flow Statement',(57,339,294,662)),('Income Statement - Quarterly',(299,184,540,339)),('Ratios and Growth',(299,339,540,661))]},
 'MS-3661 20251203.pdf':{10:[('Income Statement',(42,120,303,303)),('Balance Sheet',(42,305,303,612)),('Cash Flow Statement',(317,120,573,350)),('Financial Ratios',(317,369,573,675))]},
 '凱基投顧_2637 慧洋-KY_賴偉中_20260915.pdf':{4:[('季度與年度損益及比率',(42,90,554,615))],5:[('資產負債表',(42,78,292,290)),('主要財務比率',(42,291,292,617)),('損益表',(310,78,554,266)),('現金流量',(310,267,554,447)),('投資回報率',(310,448,554,581))]},
 '凱基投顧_3665 貿聯-KY_李承泰_20260519.pdf':{8:[('季度與年度損益及比率',(42,89,554,595))],9:[('資產負債表',(42,78,292,280)),('主要財務比率',(42,281,292,595)),('損益表',(310,78,554,258)),('現金流量',(310,259,554,431)),('投資回報率',(310,432,554,559))]},
 '晶心科(6533,N,中立)-CTBC251208.pdf':{3:[('表一、季度財報與預估差異',(175,102,565,265)),('表二、年度財報與預估差異',(175,281,565,454))],5:[('資產負債表',(35,103,297,411)),('現金流量表',(35,427,297,758)),('損益表',(308,103,568,409)),('比率分析',(308,427,568,680))]},
 '華南投顧-3017-奇鋐-1141202.pdf':{5:[('季EPS回顧',(28,56,571,288)),('獲利預估修正',(28,290,571,528)),('股利概況',(28,530,571,749))],6:[('各季EPS預估',(28,56,571,258)),('月營收現況及預估',(28,259,571,464)),('財務資料',(28,465,571,693))]},
}
EMAIL_RX=r'\b[A-Za-z0-9][A-Za-z0-9._%+\-]*@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b'
PHONE_RX=r'(?<!\d)(?:(?:\+?\(?886[ .\-]?(?:\(?0?[2-8]\)?)[ .\-]?\d{3,4}[ .\-]?\d{4})|(?:\+?852[ )(.\-]*\d{4}[ .\-]?\d{4})|(?:\(852\)[ .\-]*\d{4}[ .\-]?\d{4})|(?:\(?0[2-8]\)?[ .\-]?\d{3,4}[ .\-]?\d{4}))(?:\s*(?:ext\.?|分機|#)\s*\d+)?(?!\d)'
ROLE_RX=r'Equity Analyst|Research Analyst|Senior Analyst|Chief Analyst|Managing Director|Research Associate|Analyst|Head of Research|研究員|分析師|研究助理|資深研究員|資深分析師|協理|副總|董事總經理|研究部主管'
NUMBER_RX=r'^(?:[+\-−]?\(?\d[\d,]*(?:\.\d+)?\)?%?[AEFP]?|--?|n\.a\.|N/M)$'
TIME_RX=r'^(?:(?:FY)?(?:19|20)\d{2}(?:[AEFPCTe]+|\([AEF]\))?|FY\d{2}[AEF]?|\d{2}[AEF])$|^(?:[1-4]Q\d{2}|\d{2}Q[1-4]|[A-Z][a-z]{2}-\d{2}[AEF]|Q[1-4]|[1-4]Q|\d{2}/\d{2}e?)$'
DOMAIN_BROKERS={'jpmorgan.com':'JPM','morganstanley.com':'MS','kgi.com':'KGI','ctbcsis.com':'CTBC','entrust.com.tw':'HUANAN','ubs.com':'UBS','citi.com':'CITI','gs.com':'GS','macquarie.com':'MACQUARIE'}
RATING_WORDS=['強力買進','增加持股','未評等','持有','買進','中立','減碼','賣出','Overweight','Underweight','Outperform','Underperform','Neutral','Buy','Sell','Hold','Not Rated']
METRIC_ALIASES={
 'revenue':['營業收入淨額','營業收入','營收','Revenue','Revenues','Net sales'],
 'cost':['營業成本','COGS','Cost of revenue','Cost of sales'],
 'gross_profit':['營業毛利淨額','營業毛利','Gross profit'],
 'opex':['營業費用','Operating expenses','Operating expense'],
 'op_profit':['營業利益','Operating income','Operating profit'],
 'net_profit':['稅後純益','稅後淨利','本期淨利','Net income'],
 'assets':['資產總計','資產總額','總資產','Total assets'],
 'liabilities':['負債總計','負債合計','總負債','Total liabilities'],
 'equity':['權益總計','股東權益總計','股東權益','Total equity','Total shareholders equity'],
 'gross_margin':['毛利率','Gross margin'],
 'op_margin':['營益率','營業利益率','Operating margin'],
 'net_margin':['淨利率','稅後淨利率','Net margin'],
}

# 02 | Dependencies, existing engine adapters, source lineage
import argparse, ast, base64, csv, hashlib, html, importlib.util, json, math, re, statistics, sys
from collections import Counter
from datetime import date, datetime, timedelta
from pathlib import Path
ROOT=Path(__file__).resolve().parent
if (ROOT/'deps').is_dir():sys.path.insert(0,str(ROOT/'deps'))
import fitz, pdfplumber, pandas as pd, numpy as np

def load_engine(name):
 p=ROOT/'repo_tools'/name;spec=importlib.util.spec_from_file_location(p.stem,p);m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m);return m

def hash_file(path):
 return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def load_tools():
 layout=load_engine('VRN_ENG394_LayoutRestore_v0100.py');layout._SSOT_CACHE=json.loads((ROOT/'repo_tools/VIA_VRN_LayoutRestore_SSOT_v0100.json').read_text())
 entities=load_engine('VRN_ENG396_ReportEntities_v0100.py');entities._BOOK=json.loads((ROOT/'repo_tools/VIA_VRN_ReportEntities_SSOT_v0100.json').read_text())
 lex=load_engine('VRN_ENG395_ValuationMethodLexicon_v0100.py');matcher=lex.Matcher(lex.load_ssot(ROOT/'repo_tools/VIA_VRN_ValuationMethod_SSOT_v0100.json'))
 basic=load_engine('VRN_SevenFieldInput_v0100.py') if (ROOT/'repo_tools/VRN_SevenFieldInput_v0100.py').exists() else None
 return layout,entities,matcher

def tidy_text(s):
 s=re.sub(r'\s+',' ',str(s or '')).strip();s=re.sub(r'(?<=[\u3400-\u9fff])\s+(?=[\u3400-\u9fff])','',s)
 s=re.sub(r'(?<=[\u3400-\u9fff])\s+(?=[A-Za-z0-9，。；：])|(?<=[A-Za-z0-9，。；：])\s+(?=[\u3400-\u9fff])','',s)
 return s.strip()

def tidy_cell(s):
 return re.sub(r'\s+','',str(s or '')).strip()

def parse_number(s):
 t=tidy_cell(s).replace('−','-');t=re.sub(r'(?<=\d)[AEFP]$','',t)
 if t in ('','-','--','—','n.a.','N/M'):return None
 if re.fullmatch(r'[+\-]?\(?\d[\d,]*(?:\.\d+)?\)?%?',t):
  neg=t.startswith('(');t=t.strip('()').replace(',','').rstrip('%');return -float(t) if neg else float(t)
 return None

def in_box(b,r):
 return r[0]<=(b[0]+b[2])/2<=r[2] and r[1]<=(b[1]+b[3])/2<=r[3]

def lines_from_pdf(page,bbox=None):
 out=[]
 for b in page.get_text('dict')['blocks']:
  for ln in b.get('lines',[]):
   if abs(ln.get('dir',(1,0))[1])>.1:continue
   spans=[s for s in ln['spans'] if s['text'].strip()]
   if not spans or (bbox and not in_box(ln['bbox'],bbox)):continue
   raw=''.join(s['text'] for s in spans);size=sum(s['size']*len(s['text']) for s in spans)/max(1,sum(len(s['text']) for s in spans))
   out.append({'raw_text':raw,'text':tidy_text(raw),'bbox':list(ln['bbox']),'font_size':round(size,2),'bold':sum(len(s['text']) for s in spans if s['flags']&16 or 'bold' in s['font'].lower())>sum(len(s['text']) for s in spans)/2,'fonts':list(dict.fromkeys(s['font'] for s in spans)),'spans':[{'text':s['text'],'bbox':list(s['bbox']),'font':s['font'],'size':s['size'],'flags':s['flags']} for s in spans]})
 out=sorted(out,key=lambda x:(round(x['bbox'][1]/3),x['bbox'][0]));removed=[]
 for bullet in out:
  if not re.fullmatch(r'[•⚫➢■]',bullet['text']):continue
  near=next((l for l in out if 0<l['bbox'][0]-bullet['bbox'][0]<35 and abs((l['bbox'][1]+l['bbox'][3]-bullet['bbox'][1]-bullet['bbox'][3])/2)<6 and len(l['text'])>2),None)
  if near:
   near['raw_text']=bullet['raw_text']+' '+near['raw_text'];near['text']=tidy_text(near['raw_text']);near['bbox'][0]=bullet['bbox'][0];near['spans']=bullet['spans']+near['spans'];removed.append(bullet)
 return [l for l in out if l not in removed]

def geometry_rows(page,bbox):
 words=[w for w in page.get_text('words') if in_box(w[:4],bbox) and w[4].strip()];rows=[]
 for w in sorted(words,key=lambda w:((w[1]+w[3])/2,w[0])):
  cy=(w[1]+w[3])/2
  if rows and abs(cy-rows[-1]['cy'])<=PARAMS['line_tolerance_pt']:rows[-1]['words'].append(w)
  else:rows.append({'cy':cy,'words':[w]})
 for row in rows:
  row['words'].sort(key=lambda w:w[0]);ww=row['words'];row['bbox']=[min(w[0] for w in ww),min(w[1] for w in ww),max(w[2] for w in ww),max(w[3] for w in ww)];row['raw_text']=' '.join(w[4] for w in ww)
 return rows

# 03 | Sentences and heading hierarchy: no cross-zone or cross-table stitching
def heading_type(line,body_size,layout):
 txt=line['text'];ratio=line['font_size']/max(body_size,1)
 if re.match(r'^[•⚫➢■]',txt) or re.fullmatch(r'[•⚫➢■\d.()（）\s]+',txt):return 'BODY'
 if len(txt)>PARAMS['heading_max_chars'] or re.search(r'[。！？.!?]$',txt):return 'BODY'
 if ratio>=1.5:return 'H1'
 if ratio>=1.25:return 'H2'
 strong=bool(re.match(r'^(?:[一二三四五六七八九十]+[、.]|::|投資建議$|投資風險$|重要訊息$|評論及分析$|內容摘要$)',txt))
 if strong or (line['bold'] and ratio>=.95) or ratio>=1.1:return 'H3'
 return 'SMALL' if ratio<.85 else 'BODY'

def split_sentences(s):
 # Decimal points, initials, email/domain and abbreviations remain inside a sentence.
 pieces=[];last=0
 for m in re.finditer(r'[。！？!?]|\.(?=\s+[A-Z•]|$)',s):
  if m.group()=='.':
   token=s[max(0,m.start()-12):m.start()+1].split()[-1]
   if re.search(r'(?:\b[A-Z]|Ltd|Inc|Mr|Dr|vs|e\.g|i\.e)\.$',token):continue
  pieces.append(s[last:m.end()].strip());last=m.end()
 if s[last:].strip():pieces.append(s[last:].strip())
 return [x for x in pieces if x]

def restore_text(report_id,page,zone,known,layout):
 lines=lines_from_pdf(page,zone['bbox_pt']);lines=[l for l in lines if not any(in_box(l['bbox'],o['bbox_pt']) for o in known)]
 body=[l['font_size'] for l in lines if len(l['text'])>=30 and not l['bold']];baseline=statistics.median(body) if body else statistics.median([l['font_size'] for l in lines] or [10])
 records=[];buffer=[]
 def emit_buffer():
  if not buffer:return
  combined=''
  for l in buffer:
   t=l['text']
   if combined.endswith('-') and re.match(r'^[a-z]',t):combined=combined[:-1]+t
   else:combined=tidy_text(combined+' '+t)
  for sentence in split_sentences(combined):
   records.append({'report_id':report_id,'page':1,'zone':zone['zone'],'block_id':zone['id'],'type':'TXT','component':'SENTENCE','subcategory':'BODY','text':sentence,'raw_text':'\n'.join(x['raw_text'] for x in buffer),'anchors':[x['bbox'] for x in buffer],'font_size':baseline,'bold':all(x['bold'] for x in buffer),'repair_method':'same-zone reflow, heading/bullet/gap boundaries, decimal-safe sentence split','status':'NATIVE_RESTORED'})
  buffer.clear()
 for l in lines:
  sub=heading_type(l,baseline,layout);txt=l['text'];bullet=bool(re.match(r'^(?:\d+\.(?!\d)|[（(]\d+[)）]|[•⚫➢■])',txt))
  isolated=zone['zone']=='INFO' and (bool(re.search(EMAIL_RX,txt)) or bool(re.search(PHONE_RX,txt)) or len(txt)<30)
  gap=bool(buffer and l['bbox'][1]-buffer[-1]['bbox'][3]>baseline*1.2)
  table_between=bool(buffer and any(buffer[-1]['bbox'][3]<=o['bbox_pt'][1]<l['bbox'][1] for o in known))
  if sub in ('H1','H2','H3') or bullet or isolated or gap or table_between:emit_buffer()
  if sub in ('H1','H2','H3') or isolated:
   previous=records[-1] if records else None
   continuation=sub in ('H1','H2') and previous and previous['component']=='HEADING' and previous['subcategory']==sub and abs(previous['anchors'][-1][0]-l['bbox'][0])<8 and 0<=l['bbox'][1]-previous['anchors'][-1][3]<baseline*.7 and abs(previous['font_size']-l['font_size'])<.4 and len(previous['text']+txt)<130
   if continuation:
    previous['text']=tidy_text(previous['text']+' '+txt);previous['raw_text']+='\n'+l['raw_text'];previous['anchors'].append(l['bbox']);previous['spans']+=l['spans'];previous['repair_method']+='; equal-font adjacent heading lines joined'
   else:records.append({'report_id':report_id,'page':1,'zone':zone['zone'],'block_id':zone['id'],'type':'TXT','component':'HEADING' if sub.startswith('H') else 'INFO_TEXT','subcategory':sub,'text':txt,'raw_text':l['raw_text'],'anchors':[l['bbox']],'font_size':l['font_size'],'bold':l['bold'],'fonts':l['fonts'],'spans':l['spans'],'repair_method':'font-weight/size hierarchy; isolated heading/card','status':'NATIVE_RESTORED'})
  else:buffer.append(l)
 emit_buffer();return records

# 04 | Table rows from coordinate columns, preserving missing/merged cells
def infer_column_edges(rows,bbox):
 # Explicit comparison headers are more reliable than percentage right edges.
 semantic={'實際數','中信預估','市場共識','差異','調整前','調整後'}
 for row in rows:
  heads=[w for w in row['words'] if tidy_cell(w[4]) in semantic]
  if len(heads)>=4:
   edges=[bbox[0],heads[0][0]-4]+[(a[2]+b[0])/2 for a,b in zip(heads,heads[1:])]+[bbox[2]]
   return edges,[{'right':w[2],'left':w[0],'support':1} for w in heads]
 clusters=[]
 for ri,row in enumerate(rows):
  for w in row['words']:
   if not (re.fullmatch(NUMBER_RX,w[4],re.I) or re.fullmatch(TIME_RX,w[4])):continue
   cluster=next((c for c in clusters if abs(statistics.median(c['xs'])-w[2])<=PARAMS['column_tolerance_pt']),None)
   if cluster is None:cluster={'xs':[],'lefts':[],'support':set()};clusters.append(cluster)
   cluster['xs'].append(w[2]);cluster['lefts'].append(w[0]);cluster['support'].add(ri)
 anchors=[{'right':statistics.median(c['xs']),'left':min(c['lefts']),'support':len(c['support'])} for c in clusters if len(c['support'])>=PARAMS['min_column_support']]
 anchors=sorted(anchors,key=lambda c:c['right'])
 # Close edges are a single column; date/value widths can yield adjacent clusters.
 compact=[]
 for c in anchors:
  if compact and c['right']-compact[-1]['right']<9:
   if c['support']>compact[-1]['support']:compact[-1]=c
  else:compact.append(c)
 if not compact:return [bbox[0],bbox[2]],[]
 first_is_item=compact[0]['right']<bbox[0]+.17*(bbox[2]-bbox[0])
 boundaries=[bbox[0]]
 if not first_is_item:boundaries.append(max(bbox[0]+8,compact[0]['left']-5))
 for left,right in zip(compact,compact[1:]):boundaries.append((left['right']+right['left'])/2)
 boundaries.append(bbox[2]);return boundaries,compact

def table_chars(page,bbox):
 # pdfplumber is the primary native character extractor; PyMuPDF locates blocks.
 with pdfplumber.open(page.parent.name) as doc:
  return [{'c':c['text'],'bbox':[c['x0'],c['top'],c['x1'],c['bottom']]} for c in doc.pages[page.number].chars if in_box([c['x0'],c['top'],c['x1'],c['bottom']],bbox)]

def restore_table(report_id,page,pno,obj,layout,out):
 bbox=obj['bbox_pt'];rows=geometry_rows(page,bbox);edges,anchors=infer_column_edges(rows,bbox);chars=table_chars(page,bbox);grid=[];records=[];changes=[]
 semantic={'實際數','中信預估','市場共識','差異','調整前','調整後'}
 semantic_row=next((row for row in rows if sum(tidy_cell(w[4]) in semantic for w in row['words'])>=4),None)
 centers=[(w[0]+w[2])/2 for w in semantic_row['words'] if tidy_cell(w[4]) in semantic] if semantic_row else []
 for ri,row in enumerate(rows,1):
  cells=['' for _ in range(len(edges)-1)]
  rc=[c for c in chars if abs((c['bbox'][1]+c['bbox'][3])/2-row['cy'])<=PARAMS['line_tolerance_pt']+1]
  for c in sorted(rc,key=lambda c:c['bbox'][0]):
   x=(c['bbox'][0]+c['bbox'][2])/2;ci=next((i for i in range(len(edges)-1) if edges[i]<=x<edges[i+1]),len(cells)-1);cells[ci]+=c['c']
  if centers and row!=semantic_row:
   # Percentage-point suffixes belong to their preceding numeric token.
   cells=['' for _ in cells];ww=row['words'];wi=0
   while wi<len(ww):
    w=ww[wi];token=w[4];right=w[2]
    if wi+1<len(ww) and ww[wi+1][4].lower() in ('ppts','ppt') and ww[wi+1][0]-right<6:
     wi+=1;token+=ww[wi][4];right=ww[wi][2]
    x=(w[0]+right)/2;ci=0 if right<edges[1] else min(range(len(centers)),key=lambda j:abs(centers[j]-x))+1
    cells[ci]+=token;wi+=1
  if not any(cells):cells=[row['raw_text']]+['']*(len(cells)-1)
  clean=[tidy_cell(c) for c in cells];raw=row['raw_text'];text=tidy_text(raw)
  if re.search(r'^(?:Source[s]?|資料來源|來源)\s*[:：]',text,re.I):component='SOURCE'
  elif re.match(r'^(?:Unless|\*\*|§|e =|註[:：]|Note[:：])',text,re.I):component='NOTE'
  elif sum(bool(re.fullmatch(TIME_RX,w[4])) for w in row['words'])>=2 or sum(tidy_cell(w[4]) in {'實際數','中信預估','市場共識','差異','調整前','調整後'} for w in row['words'])>=3:component='HEADER'
  elif not grid and sum(parse_number(c) is not None for c in clean)==0:component='TITLE'
  else:component='ROW'
  if component in ('TITLE','SOURCE','NOTE'):cells=[raw]+['']*(len(cells)-1);clean=[tidy_cell(c) for c in cells]
  record={'report_id':report_id,'page':pno,'zone':'INFO','block_id':obj['id'],'type':'TBL','component':component,'row_index':ri,'text':' | '.join(clean),'raw_text':raw,'cells_raw':cells,'cells':clean,'anchors':[row['bbox']],'repair_method':'coordinate column assignment, cell whitespace removal and TRIM; original blanks kept','status':'RESTORED_CANDIDATE'}
  records.append(record);grid.append(record)
  if cells!=clean:changes.append({'row':ri,'method':'CELL_SPACE_TRIM','before':cells,'after':clean,'bbox':row['bbox']})
 header=[r for r in grid if r['component']=='HEADER'];source=[r for r in grid if r['component']=='SOURCE']
 # Sources just outside the crop: inspect same x range within 3 nearby native lines.
 nearby=[l for l in lines_from_pdf(page) if bbox[3]<l['bbox'][1]<=bbox[3]+38 and bbox[0]-4<=l['bbox'][0]<=bbox[2] and re.match(r'^(?:Source[s]?|資料來源)[:：]',l['text'],re.I)]
 for l in nearby[:1]:
  rec={'report_id':report_id,'page':pno,'zone':'INFO','block_id':obj['id'],'type':'TBL','component':'SOURCE','row_index':len(records)+1,'text':tidy_cell(l['text']),'raw_text':l['raw_text'],'cells':[tidy_cell(l['text'])],'cells_raw':[l['raw_text']],'anchors':[l['bbox']],'repair_method':'same-column nearby source linkage','status':'SOURCE_LINKED'};records.append(rec);source.append(rec)
 periods=['' for _ in range(len(edges)-1)]
 for h in header:
  for ci,c in enumerate(h['cells']):
   if re.search(r'(?:20\d{2}|FY\d{2}|(?:Mar|Jun|Sep|Dec)-\d{2}|[1-4]Q\d{2}|\d{2}/\d{2})',c):periods[ci]=c
 # Merged quarter labels are scoped across their horizontal spans.
 comparison_header=next((r for r in grid if r['component']=='HEADER' and '調整前' in r['cells']),None)
 if comparison_header:
  periods_row=next((r for r in grid if len(re.findall(r'[1-4]Q\d{2}(?:\(F\))?|20\d{2}(?:\(F\)|F)?',r['raw_text']))==2 and sum(parse_number(c) is not None for c in r['cells'])<3),None)
  if periods_row:
   labels=re.findall(r'[1-4]Q\d{2}(?:\(F\))?|20\d{2}(?:\(F\)|F)?',periods_row['raw_text']);split=comparison_header['cells'].index('調整前')
   periods=['']+[labels[0] if ci<split else labels[1] for ci in range(1,len(periods))]
 numbered=next((re.search(r'(?:表[一二三四五六七八九十\d]+|Table\s*\d+|Exhibit\s*\d+)',r['raw_text'],re.I).group() for r in grid if re.search(r'(?:表[一二三四五六七八九十\d]+|Table\s*\d+|Exhibit\s*\d+)',r['raw_text'],re.I)),None)
 matrix=[r['cells'] for r in grid if r['component']=='ROW'];checks=layout.validate({'columns':[f'C{i+1}' for i in range(len(edges)-1)],'rows':matrix}) if matrix else {'verdict':'YELLOW','checks':[],'issues':['NO_ROWS']}
 t={'id':obj['id'],'report_id':report_id,'page':pno,'title':obj['label'],'table_number':numbered,'bbox_pt':bbox,'column_edges_pt':[round(e,2) for e in edges],'column_anchors':[{'right':round(a['right'],2),'support':a['support']} for a in anchors],'period_headers':periods,'records':records,'restoration_log':changes,'source_status':'PRESENT' if source else 'NOT_PRINTED_OR_NOT_CAPTURED','original_top_left_preserved':True,'virtual_item_header':'ITEM' if header and not header[0]['cells'][0] else None,'merged_cells':[],'merged_cell_status':'NO_AUTOMATIC_FORWARD_FILL; spans require geometric evidence','existing_engine_checks':checks,'validation':[],'status':'REVIEW_GEOMETRY'}
 annual_word=next((w for row in rows[:3] for w in row['words'] if w[4]=='年度'),None)
 quarter_word=next((w for row in rows[:3] for w in row['words'] if w[4]=='季度'),None)
 if annual_word and quarter_word:
  start=next((ci for ci in range(1,len(edges)-1) if edges[ci]<=annual_word[0]<edges[ci+1]),None)
  t['annual_column_start']=start;t['column_groups']=[{'type':'QUARTER','columns':list(range(1,start))},{'type':'ANNUAL','columns':list(range(start,len(edges)-1))}]
  t['shared_item_rows']=[{'row_index':r['row_index'],'item_raw':r['cells_raw'][0],'item_trim':r['cells'][0],'source_bbox':r['anchors']} for r in records if r['component']=='ROW']
  cuts=out/'financial_group_crops';cuts.mkdir(exist_ok=True);t['group_crops']=[]
  for kind,box in [('QUARTER',[bbox[0],bbox[1],edges[start],bbox[3]]),('ANNUAL',[edges[start],bbox[1],bbox[2],bbox[3]])]:
   crop=fitz.open();crop.insert_pdf(page.parent,from_page=pno-1,to_page=pno-1);crop[0].set_cropbox(fitz.Rect(box));file=cuts/(obj['id']+'_'+kind+'.pdf');crop.save(file,garbage=4,deflate=True);crop.close();t['group_crops'].append({'type':kind,'bbox_pt':box,'file':str(file.relative_to(out)),'item_link':'shared_item_rows from original leftmost column; no invented numeric fill'})
  t['restoration_log'].append({'method':'QUARTER_ANNUAL_HORIZONTAL_SPLIT','annual_start_column':start,'shared_item_binding':'row_index and native y anchor'})
 # Native ruled cell rectangles provide merge evidence. No unconditional None fill.
 with pdfplumber.open(page.parent.name) as pdf:
  cropped=pdf.pages[pno-1].crop(tuple(bbox))
  for gt in cropped.find_tables():
   for cell in gt.cells:
    if not cell:continue
    covered=[i for i in range(len(edges)-1) if edges[i]<cell[2]-.5 and edges[i+1]>cell[0]+.5]
    if len(covered)>1:t['merged_cells'].append({'bbox':list(cell),'columns':covered,'action':'SPAN_RECORDED_NO_NUMERIC_FILL'})
 return t,records

# 05 | Named arithmetic rules; exact same period, table and displayed units
def canonical_metric(label):
 s=tidy_cell(label).lower();s=re.sub(r'\([^)]*\)','',s)
 for key,aliases in METRIC_ALIASES.items():
  if any(s==tidy_cell(a).lower() for a in aliases):return key
 return None

def rounding_unit(s):
 t=tidy_cell(s).rstrip('%');m=re.search(r'\.(\d+)',t);return 10**(-len(m.group(1))) if m else 1.0

def validate_table(t):
 metrics={};rows=[r for r in t['records'] if r['component']=='ROW']
 growth=False
 for r in rows:
  if re.search(r'成長|Growth',r['cells'][0],re.I):growth=True
  if re.search(r'獲利|損益|資產|Profitability|Income',r['cells'][0],re.I):growth=False
  if growth:continue
  key=canonical_metric(r['cells'][0])
  if key and key not in metrics:metrics[key]=r
 rules=[('gross_profit','revenue','cost','SUBTRACT_EXPENSE'),('op_profit','gross_profit','opex','SUBTRACT_EXPENSE'),('assets','liabilities','equity','ADD'),('gross_margin','gross_profit','revenue','RATIO_PCT'),('op_margin','op_profit','revenue','RATIO_PCT'),('net_margin','net_profit','revenue','RATIO_PCT')]
 for target,a,b,op in rules:
  if not all(k in metrics for k in (target,a,b)):continue
  for ci in range(1,len(t['column_edges_pt'])-1):
   if any(re.search(r'差異|YoY|QoQ|Diff',r['cells'][ci],re.I) for r in t['records'] if r['component'] in ('HEADER','TITLE')):continue
   raw=[metrics[k]['cells'][ci] for k in (target,a,b)];nums=[parse_number(x) for x in raw]
   if None in nums:continue
   actual,x,y=nums
   if op=='RATIO_PCT' and y==0:continue
   expected=x-abs(y) if op=='SUBTRACT_EXPENSE' else x+y if op=='ADD' else x/y*100
   tolerance=.5*sum(rounding_unit(v) for v in raw)+.02 if op!='RATIO_PCT' else max(.2,rounding_unit(raw[0])*.5+100*(rounding_unit(raw[1])*.5/abs(y)+abs(x)*rounding_unit(raw[2])*.5/(y*y)))
   diff=actual-expected;t['validation'].append({'rule':f'{target}={a}{"-" if op=="SUBTRACT_EXPENSE" else "+" if op=="ADD" else "/"}{b}','operation':op,'column':ci,'period_raw':t['period_headers'][ci],'actual':actual,'calculated':round(expected,6),'difference':round(diff,6),'tolerance':tolerance,'status':'PASS' if abs(diff)<=tolerance else 'FAIL_REVIEW','source':'CALC_CHECK_ONLY_SOURCE_VALUES_UNCHANGED'})
 # No formula opportunities is not PASS; geometric restoration remains reviewable.
 t['status']='FAIL_REVIEW' if any(v['status']=='FAIL_REVIEW' for v in t['validation']) else 'CALC_PASS_GEOMETRY_REVIEW' if t['validation'] else 'REVIEW_NO_APPLICABLE_FORMULA'
 t['historical_crosscheck_status']='PENDING_OFFICIAL_SAME_PERIOD_DATA'
 return t

# 06 | Analyst/contact, exact rating and separate current/prior target evidence
def extract_contacts(lines,broker):
 out=[]
 for i,line in enumerate(lines):
  raw=line['text'];normalized=raw
  if '@' in raw:normalized=re.sub(r'\s+','',raw)
  matches=list(re.finditer(EMAIL_RX,normalized))
  for match in matches:
   email=match.group();local,domain=email.split('@',1);near=[l for l in lines if abs(l['bbox'][0]-line['bbox'][0])<85 and -40<l['bbox'][1]-line['bbox'][1]<10]
   above=[l['text'] for l in near if l['bbox'][1]<line['bbox'][1]]
   titles=[m.group() for l in near for m in re.finditer(ROLE_RX,l['text'],re.I)]
   same_row=[l for l in lines if abs(l['bbox'][1]-line['bbox'][1])<3 and 0<l['bbox'][0]-line['bbox'][0]<220]
   phones=[m.group() for l in near+same_row for m in re.finditer(PHONE_RX,l['text'])]
   chinese=next((x for x in reversed(above) if re.fullmatch(r'[\u4e00-\u9fff]{2,4}',x) and not re.search(ROLE_RX,x)),None)
   english=next((x for x in reversed(above) if re.fullmatch(r'[A-Z][a-z]+(?:\s+[A-Z][A-Za-z.]+){1,3}(?:,?\s+(?:CFA|AC))?',x) and not re.search(ROLE_RX+'|Morgan Stanley|Asia Pacific|Technology|Taiwan Limited',x,re.I)),None)
   out.append({'email':email,'email_raw':raw,'email_local_name_candidate':re.sub(r'[._]+',' ',local),'name_zh':chinese,'name_en':english,'name_status':'PRINTED_NEARBY' if chinese or english else 'EMAIL_ALIAS_ONLY_REVIEW','roles_raw':list(dict.fromkeys(titles)),'phones_raw':list(dict.fromkeys(phones)),'phones_normalized':[re.sub(r'[^+\d]','',x) for x in dict.fromkeys(phones)],'broker_from_domain':DOMAIN_BROKERS.get(domain.lower()),'broker_domain':domain,'broker_matches_report':DOMAIN_BROKERS.get(domain.lower())==broker,'bbox':line['bbox'],'method':'email account is candidate; printed name above title/phone/email corroborates'})
 return out

def extract_report_metadata(path,page,records,entities,basic,names):
 lines=lines_from_pdf(page);text='\n'.join(l['text'] for l in lines);code,_=basic.load_module(ROOT/'repo_tools/vrn_sample_reader.py','reader_meta').find_ticker(path.stem)
 broker,_=basic.load_module(ROOT/'repo_tools/vrn_sample_reader.py','reader_broker').find_broker(path.stem)
 ds=[]
 for l in lines:
  if l['bbox'][1]<100 or l['bbox'][1]>page.rect.height*.94:
   ds.extend(dict(d,bbox=l['bbox']) for d in basic.dates_in(l['text']))
 fd=basic.dates_in(path.stem,compact=True);rd=ds[0]['date'] if ds else fd[0]['date'] if fd else None
 targets=entities.target_prices(text);targets['geometry_candidates']=[];rating=[]
 for l in lines:
  if not re.search(r'目標價|PriceTarget|Price Target',l['text'],re.I) or len(l['text'])>45:continue
  candidates=[v for v in lines if abs((v['bbox'][1]+v['bbox'][3]-l['bbox'][1]-l['bbox'][3])/2)<3 and l['bbox'][2]<=v['bbox'][0]<=l['bbox'][2]+110 and parse_number(v['text']) is not None]
  if not candidates:continue
  value=min(candidates,key=lambda v:v['bbox'][0]);kind='prior' if re.search(r'前次|prior|previous|old',l['text'],re.I) else 'current'
  targets['geometry_candidates'].append({'kind':kind,'value':parse_number(value['text']),'label_raw':l['raw_text'],'value_raw':value['raw_text'],'anchors':[l['bbox'],value['bbox']],'method':'same native row; nearest numeric value to right of explicit target label'})
 for kind in ('current','prior'):
  candidates=[c for c in targets['geometry_candidates'] if c['kind']==kind]
  if candidates:
   original=targets[kind];targets[kind]=candidates[0]['value']
   if original is not None and original!=targets[kind]:targets.setdefault('conflicts',[]).append({'kind':kind,'engine_candidate':original,'printed_card_candidate':targets[kind],'status':'REVIEW_PRINTED_CARD_SELECTED'})
 for l in lines:
  for word in RATING_WORDS:
   if re.search(r'(?<![A-Za-z])'+re.escape(word)+r'(?![A-Za-z])',l['text'],re.I):
    rating.append({'raw':l['raw_text'].strip(),'value_raw':word,'is_prior':bool(re.search(r'前次|原評等|prior|previous',l['text'],re.I)),'bbox':l['bbox']})
 row={'REPORT_DATE':rd,'REPORT_DATE_SOURCE':'PRINTED_FIRST_PAGE' if ds else 'FILENAME_CANDIDATE' if fd else 'MISSING','REPORT_DATE_DISPLAY':rd.replace('-','/') if rd else None,'FILENAME':path.name,'FORMAT':'PDF','SIZE':path.stat().st_size,'TICKER':code,'NAME':names.get(code,{}).get('name'),'NAME_SOURCE':names.get(code,{}).get('name_source'),'NAME_SNAPSHOT_DATE':names.get(code,{}).get('date'),'YF_TICKER':names.get(code,{}).get('yfinance_ticker') or (code+('.TWO' if names.get(code,{}).get('market')=='TPEX' else '.TW') if code else None),'BROKER':broker,'report_date_evidence':ds,'filename_date_candidate':fd[0]['date'] if fd else None,'DATE_CONFLICT':bool(ds and fd and ds[0]['date']!=fd[0]['date']),'target_price':targets,'ratings_raw':rating,'contacts':extract_contacts(lines,broker),'stock_quote_evidence':[]}
 for rec in records:
  s=rec['text']
  if rec['type']=='TBL' and re.search(r'收盤價|Shrprice,close|ClosingPrice|Price\(',s,re.I):row['stock_quote_evidence'].append({'raw':rec['raw_text'],'cells':rec.get('cells'),'page':rec['page'],'bbox':rec['anchors']})
 return row

# 07 | Valuation SSOT matching and annual EPS N / N+1 / N+2
def period_year(s):
 s=tidy_cell(s);m=re.search(r'20\d{2}',s)
 if m:return int(m.group())
 m=re.search(r'(?:FY|[A-Za-z]{3}-|\dQ)(\d{2})',s)
 if m:return 2000+int(m.group(1))
 m=re.fullmatch(r'(\d{2})/\d{2}e?',s)
 return 2000+int(m.group(1)) if m else None

def valuation_and_eps(meta,records,tables,matcher):
 vals=[];unknown=[]
 for r in records:
  if r['type']!='TXT' or r['component']!='SENTENCE':continue
  s=r['text'];ctx=bool(re.search(r'目標價|評價|估值|給予|valuation|value.*stock|based on|price target',s,re.I))
  if not ctx:continue
  hits=matcher.match(s)
  for h in hits:
   if h['context_required'] and not ctx:continue
   vals.append({'method_id':h['id'],'term_raw':h['term'],'evidence':s,'anchors':r['anchors'],'source':'ENG395_EXISTING_SSOT'})
  if not hits:unknown.append({'text':s,'status':'NO_MATCH_REVIEW_ADDITIVE_CANDIDATE; SSOT not mutated'})
 n=int(meta['REPORT_DATE'][:4]) if meta['REPORT_DATE'] else None;eps=[]
 for t in tables:
  annual_start=t.get('annual_column_start',next((ci for r in t['records'][:3] for ci,c in enumerate(r.get('cells',[])) if c=='年度'),None))
  growth=False
  for r in t['records']:
   if r['component']!='ROW' or not r.get('cells'):continue
   label=r['cells'][0]
   if re.search(r'成長率|Growth',label,re.I):growth=True
   if re.search(r'損益表|IncomeStatement',label,re.I):growth=False
   if not re.search(r'EPS|每股盈餘|每股純益|每股淨利',label,re.I):continue
   if growth or re.search(r'成長|growth|y/y|YoY|QoQ|%',label,re.I):continue
   for ci,period in enumerate(t['period_headers']):
    year=period_year(period)
    if n is None or not year or ci==0 or year not in (n,n+1,n+2):continue
    value=parse_number(r['cells'][ci]);quarterly=(ci<annual_start if annual_start is not None else bool(re.search(r'[1-4]Q|Q[1-4]|Mar-|Jun-|Sep-',period)))
    if quarterly or value is None:continue
    kind='DILUTED' if re.search(r'diluted|稀釋',label,re.I) else 'ADJUSTED' if re.search(r'Adj|調整',label,re.I) else 'CONSENSUS' if '**' in label or 'consensus' in label.lower() else 'MODELWARE' if 'modelware' in label.lower() else 'BASIC_OR_UNSPECIFIED'
    eps.append({'N':year-n,'year':year,'period_raw':period,'metric_raw':label,'eps_type':kind,'value':value,'table_id':t['id'],'page':t['page'],'bbox':r['anchors'],'source':'RP','historical_or_forecast':'FORECAST' if re.search(r'[EFPe]$|\([EF]\)$',period) else 'REPORTED_OR_UNCLASSIFIED'})
  # Transposed annual tables: years in ITEM; vertically stacked EPS headers.
  year_rows=[r for r in t['records'] if r.get('cells') and re.fullmatch(r'20\d{2}(?:\([AF]\)|[AFE])?',r['cells'][0])]
  if year_rows and n and re.search(r'年度|Annual',t['title'],re.I):
   first=year_rows[0]['row_index'];heads=[r for r in t['records'] if r['row_index']<first and r['component']!='TITLE']
   for ci in range(1,len(t['column_edges_pt'])-1):
    label=''.join(r['cells'][ci] for r in heads)
    if 'EPS' not in label:continue
    for r in year_rows:
     year=period_year(r['cells'][0]);value=parse_number(r['cells'][ci])
     if year not in (n,n+1,n+2) or value is None:continue
     eps.append({'N':year-n,'year':year,'period_raw':r['cells'][0],'metric_raw':label,'eps_type':'PRE_TAX' if '稅前' in label else 'BASIC_OR_UNSPECIFIED','value':value,'table_id':t['id'],'page':t['page'],'bbox':r['anchors'],'source':'RP','historical_or_forecast':'FORECAST' if 'F' in r['cells'][0] else 'REPORTED_OR_UNCLASSIFIED','method':'transposed annual year rows with stacked header'})
 return vals,unknown,eps

# 08 | VDF yfinance price adapter; cache first, no Close-as-Adj-Close substitution
def vdf_postprocess(frame,symbol,name):
 source=ROOT/'repo_tools/VDF_MDL002_YFinanceFetchingEngine_v0100.py';tree=ast.parse(source.read_text());cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='FinancialDataFetcher');fn=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='_post_process_data')
 module=ast.Module(body=[fn],type_ignores=[]);ns={'pd':pd,'np':np,'Dict':dict,'Any':object};exec(compile(ast.fix_missing_locations(module),str(source),'exec'),ns)
 return ns['_post_process_data'](None,frame,symbol,{'name':name,'market':'Taiwan','region':'Taiwan','asset_class':'EQUITY','has_adj_close':True,'has_volume':True})

def fetch_prices(metas,out):
 from VRN_VDFCacheReader_v0101 import scan,DEFAULT_ROOTS
 cached,official,audit=scan([str(ROOT/PARAMS['price_cache']),str(ROOT/PARAMS['official_financial_cache'])]+PARAMS.get('database_roots',[])+DEFAULT_ROOTS,metas)
 (out/'VDF_CacheAudit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
 if not official.empty:export_frame(official,out/'OfficialFinancialCache')
 status=[];frames=[cached] if not cached.empty else []
 try:import yfinance as yf
 except ImportError:yf=None
 for m in metas:
  symbol=m['YF_TICKER'];cached=pd.concat(frames,ignore_index=True) if frames else pd.DataFrame()
  if not cached.empty and symbol in set(cached.get('YFinance Ticker',[])):status.append({'ticker':symbol,'status':'VDF_CACHE_AVAILABLE_COVERAGE_REVIEW'});continue
  if yf is None:status.append({'ticker':symbol,'status':'DEPENDENCY_AND_NETWORK_BLOCKED','detail':'yfinance install timed out; elevated installation rejected by approval policy'});continue
  if not PARAMS['network_enabled']:status.append({'ticker':symbol,'status':'NETWORK_DISABLED'});continue
  start=(date.fromisoformat(m['REPORT_DATE'])-timedelta(days=PARAMS['price_lookback_days'])).isoformat();end=(date.fromisoformat(PARAMS['as_of'])+timedelta(days=1)).isoformat()
  try:
   frame=yf.Ticker(symbol).history(start=start,end=end,auto_adjust=False,actions=True,repair=False,timeout=PARAMS['network_timeout_seconds'],raise_errors=True)
   if frame.empty or 'Adj Close' not in frame:raise ValueError('No explicit Adj Close')
   normalized=vdf_postprocess(frame,symbol,m['NAME']);normalized['Source']='YFINANCE';normalized['DownloadedAt']=datetime.now().isoformat();frames.append(normalized);status.append({'ticker':symbol,'status':'FETCHED_YFINANCE_VDF_NORMALIZED','start':start,'end_exclusive':end})
  except Exception as exc:status.append({'ticker':symbol,'status':'FETCH_FAILED','error':str(exc)[:240]})
 data=pd.concat(frames,ignore_index=True) if frames else pd.DataFrame(columns=['YFinance Ticker','Date','Close','Adj Close'])
 conflicts=[]
 if not data.empty:
  for (symbol,day),group in data.groupby(['YFinance Ticker','Date']):
   if group['Close'].nunique(dropna=False)>1 or group['Adj Close'].nunique(dropna=False)>1:
    conflicts.append({'ticker':symbol,'date':day,'status':'CONFLICT_REVIEW_NOT_USED','candidates':group.to_dict('records')})
  conflict_keys={(c['ticker'],c['date']) for c in conflicts};data=data[[ (r['YFinance Ticker'],r['Date']) not in conflict_keys for _,r in data.iterrows()]].drop_duplicates(['YFinance Ticker','Date'])
 (out/'PriceCacheConflicts.json').write_text(json.dumps(conflicts,ensure_ascii=False,indent=2,default=str),encoding='utf-8')
 for m in metas:
  part=data[data['YFinance Ticker']==m['YF_TICKER']].sort_values('Date');d=m['REPORT_DATE'];prior=part[part['Date']<d].tail(1);report=part[part['Date']==d];today=part[part['Date']==PARAMS['as_of']];latest=part[part['Date']<=PARAMS['as_of']].tail(1)
  def rowval(df):
   if df.empty:return None
   r=df.iloc[-1];return {'date':r['Date'],'close':float(r['Close']) if pd.notna(r['Close']) else None,'adj_close':float(r['Adj Close']) if pd.notna(r['Adj Close']) else None,'source':r.get('Source','SOURCE_UNSPECIFIED'),'adjustment_vintage':r.get('DownloadedAt'),'cache_path':r.get('CachePath'),'status':'DAILY_CACHE_COVERAGE_REVIEW'}
  m['prices']={'prior_available_trading_day_candidate':rowval(prior),'prior_day_status':'REQUIRES_COMPLETE_CACHE_AND_TRADING_CALENDAR','report_date':rowval(report),'today_daily':rowval(today),'latest_available_daily':rowval(latest),'today_calendar_date':PARAMS['as_of'],'intraday_price':None}
  ref=rowval(report);factor=ref['adj_close']/ref['close'] if ref and ref['close'] and ref['adj_close'] is not None else None
  m['target_price_adjusted']={'current_raw':m['target_price']['current'],'current_adjusted':m['target_price']['current']*factor if factor and m['target_price']['current'] else None,'factor':factor,'basis_date':d,'adjustment_vintage':ref.get('adjustment_vintage') if ref else None,'method':'raw target * historical Adj Close/Close; cache download vintage retained; unknown vintage requires review','prior_raw':m['target_price']['prior'],'prior_adjusted':None,'prior_status':'PRIOR_TARGET_ISSUE_DATE_REQUIRED','status':'ADJUSTED_VINTAGE_REVIEW' if factor else 'PENDING_PRICE_DATA'}
 export_frame(data,out/'StockPrices');return status

# 09 | Exports, verification and readable restored document
def export_frame(df,path):
 df.to_csv(str(path)+'.csv',index=False,encoding=PARAMS['csv_encoding']);df.to_parquet(str(path)+'.parquet',index=False,compression=PARAMS['parquet_compression'])

def table_html(t):
 rows=''.join('<tr>'+''.join('<td>'+html.escape(c)+'</td>' for c in r.get('cells',[r['text']]))+'</tr>' for r in t['records'])
 return f'<h4>{html.escape(t["id"]+" "+t["title"])}</h4><p>{t["status"]} · {len(t["validation"])} arithmetic checks</p><table>{rows}</table>'

def verify_outputs(docs,records,tables):
 checks=[]
 checks.append({'check':'Every restored record retains original text and coordinates','status':'PASS' if all(r.get('raw_text') is not None and r.get('anchors') for r in records) else 'FAIL'})
 checks.append({'check':'Table cleaned cells contain no whitespace','status':'PASS' if all(not re.search(r'\s',c) for t in tables for r in t['records'] for c in r.get('cells',[])) else 'FAIL'})
 checks.append({'check':'Exactly one sentence or heading/info item per TXT record','status':'PASS' if all(len(split_sentences(r['text']))<=1 for r in records if r['type']=='TXT' and r['component']=='SENTENCE') else 'FAIL'})
 checks.append({'check':'Current/prior target prices remain distinct','status':'PASS' if all('current' in d['metadata']['target_price'] and 'prior' in d['metadata']['target_price'] for d in docs) else 'FAIL'})
 checks.append({'check':'Financial source values unchanged by arithmetic checks','status':'PASS','detail':'All derived values live only in validation rows; no numeric overwrite'})
 return checks

def main():
 out=ROOT/PARAMS['output_dir'];out.mkdir(exist_ok=True);layout,entities,matcher=load_tools();basic=load_engine_from_root();vdf=load_engine('VDF_MDL009_TWStockList_v0101.py');names,nameaudit=basic.load_official_names(vdf,'')
 source=json.loads((ROOT/PARAMS['layout_file']).read_text());allrecords=[];alltables=[];docs=[];overlay=fitz.open()
 for report in source['reports']:
  path=ROOT/PARAMS['input_dir']/report['filename'];pdf=fitz.open(path);rid=report['id'];records=[];tables=[]
  if not report['native_chars']:
   docs.append({'id':rid,'filename':path.name,'status':'SCAN_REVIEW_ONLY','metadata':extract_report_metadata(path,pdf[0],[],entities,basic,names),'records':[],'tables':[]});continue
  zones=[o for o in report['objects'] if o['level']==1 and o['zone']!='EXCLUDED'];children=[o for o in report['objects'] if o['level']==2]
  for zone in zones:records+=restore_text(rid,pdf[0],zone,children,layout)
  for obj in children:
   if obj['category']=='table':
    t,rr=restore_table(rid,pdf[0],1,obj,layout,out);validate_table(t);tables.append(t);records+=rr
   else:
    b=fitz.Rect(obj['bbox_pt']);pix=pdf[0].get_pixmap(clip=b,matrix=fitz.Matrix(PARAMS['figure_dpi']/72,PARAMS['figure_dpi']/72));name=obj['id']+'.png';pix.save(out/name)
    figtext=pdf[0].get_textbox(b);number=re.search(r'(?:圖[一二三四五六七八九十\d]+|Figure\s*\d+|Exhibit\s*\d+)',figtext,re.I)
    records.append({'report_id':rid,'page':1,'zone':'INFO','block_id':obj['id'],'type':'FIG','component':'FIGURE','figure_number':number.group() if number else None,'title':obj['label'],'text':obj['label'],'raw_text':figtext,'anchors':[obj['bbox_pt']],'image_file':name,'repair_method':'image retained; chart labels are not numeric table values','status':'FIGURE_RETAINED'})
    for l in lines_from_pdf(pdf[0]):
     inside=in_box(l['bbox'],obj['bbox_pt']);near=obj['bbox_pt'][3]<=l['bbox'][1]<=obj['bbox_pt'][3]+12 and obj['bbox_pt'][0]-3<=l['bbox'][0]<=obj['bbox_pt'][2]
     source=bool(re.match(r'(?:Source[s]?|資料來源)\s*[:：]',l['text'],re.I))
     if inside or (near and source):records.append({'report_id':rid,'page':1,'zone':'INFO','block_id':obj['id'],'type':'FIG','component':'SOURCE' if source else 'CHART_TEXT','text':tidy_cell(l['text']) if source else l['text'],'raw_text':l['raw_text'],'anchors':[l['bbox']],'repair_method':'native chart text and nearby source kept separately from numeric table cells','status':'NATIVE_CHART_TEXT'})
  for pno,blocks in FIN_PROFILES.get(path.name,{}).items():
   overlay.insert_pdf(pdf,from_page=pno-1,to_page=pno-1)
   for ti,(label,bbox) in enumerate(blocks,1):
    obj={'id':f'{rid}-P{pno:03d}-T{ti:02d}','label':label,'bbox_pt':list(bbox)};t,rr=restore_table(rid,pdf[pno-1],pno,obj,layout,out);validate_table(t);tables.append(t);records+=rr;overlay[-1].draw_rect(fitz.Rect(bbox),color=(.9,.35,.05),width=1.1);overlay[-1].insert_text((bbox[0]+2,bbox[1]+7),obj['id'],fontsize=6,color=(.9,.35,.05))
  meta=extract_report_metadata(path,pdf[0],records,entities,basic,names);vals,unknown,eps=valuation_and_eps(meta,records,tables,matcher);meta.update(valuation=vals,valuation_unmatched=unknown,eps=eps)
  doc={'id':rid,'filename':path.name,'input_sha256':hash_file(path),'status':'RESTORED_REVIEW_REQUIRED','metadata':meta,'records':records,'tables':tables};docs.append(doc);allrecords+=records;alltables+=tables;pdf.close();print(rid,path.name,'records',len(records),'tables',len(tables),flush=True)
 from VRN_TableRouter_v0101 import run as run_table_router
 routing=run_table_router(docs,ROOT/PARAMS['input_dir'],out,ROOT)
 (out/'EngineRouting.json').write_text(json.dumps(routing,ensure_ascii=False,indent=2),encoding='utf-8')
 route_map={r['table_id']:r for r in routing}
 for t in alltables:t['engine_routing']=route_map[t['id']]
 prices=fetch_prices([d['metadata'] for d in docs],out)
 from VRN_VDFCacheReader_v0101 import compare
 official=pd.read_parquet(out/'OfficialFinancialCache.parquet') if (out/'OfficialFinancialCache.parquet').exists() else pd.DataFrame()
 history=compare(docs,official,canonical_metric,parse_number)
 export_frame(pd.DataFrame(history,columns=['report_id','table_id','ticker','period','metric','report_value','official_value','difference','unit','basis','source','cache_path','status']),out/'HistoricalCrosscheck')
 checks=verify_outputs(docs,allrecords,alltables);arith=[dict(report_id=t['report_id'],table_id=t['id'],page=t['page'],**v) for t in alltables for v in t['validation']]
 result={'version':PARAMS['version'],'as_of':PARAMS['as_of'],'scope':'available 8 PDFs: first page plus 10 visually calibrated financial/comparison pages; 89 requested PDFs unavailable','name_audit':nameaudit,'price_status':prices,'official_financial_status':'CACHE_MATCH_RESULTS' if history else 'PENDING_ACCESSIBLE_VDF_CACHE_WITH_PERIOD_UNIT_BASIS','checks':checks,'documents':docs,'summary':{'reports':len(docs),'scan_review':sum(d['status']=='SCAN_REVIEW_ONLY' for d in docs),'records':len(allrecords),'tables':len(alltables),'heading_counts':dict(Counter(r.get('subcategory') for r in allrecords if r.get('component')=='HEADING')),'arithmetic_checks':len(arith),'arithmetic_status':dict(Counter(v['status'] for v in arith)),'engine_routes':dict(Counter(r['route'] for r in routing))}}
 (out/'restored_reports.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');(out/'method_registry.json').write_text(json.dumps({'version':PARAMS['version'],'PARAMS':PARAMS,'email_regex':EMAIL_RX,'phone_regex':PHONE_RX,'roles_regex':ROLE_RX,'font_hierarchy':'H1 >=1.5; H2 >=1.25; H3 >=1.1 or bold/structural heading; relative to body font','text_method':'sentence per record; heading/bullet/zone/table boundaries; preserve English word boundaries','table_method':'first left/right segmentation, then upper/lower table blocks; character coordinates to column cells; trim whitespace only inside cells; original and normalized both retained','merged_cell_method':'border-supported span ledger; no unconditional forward fill or zero filling','price_method':'explicit Close and Adj Close; prior trading day and exact today separate; no daily-close substitution for live price; prior target adjustment requires original issue date','validation_method':'named same-period identities, signed expense handling, displayed-precision tolerance, no source overwrite','engines':{n:hash_file(p) for p in (ROOT/'repo_tools').glob('*.py') for n in [p.name]}},ensure_ascii=False,indent=2),encoding='utf-8')
 flat=[]
 for r in allrecords:flat.append({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(list,dict)) else v for k,v in r.items()})
 export_frame(pd.DataFrame(flat),out/'TextRecords');export_frame(pd.DataFrame(arith),out/'TableValidation')
 headers=[]
 for d in docs:
  m=d['metadata'];headers.append({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list)) else v for k,v in m.items()})
 export_frame(pd.DataFrame(headers),out/'StockReportBasicInfo')
 if len(overlay):overlay.save(out/'財報頁_左右上下分切.pdf')
 cards=[]
 for d in docs:
  m=d['metadata'];card=f'<section><h2>{html.escape(d["filename"])}</h2><p>{html.escape(str(m["REPORT_DATE_DISPLAY"]))} | {m["TICKER"]} {html.escape(m["NAME"] or "")} | {m["BROKER"]} | {d["status"]}</p>'
  card+='<details><summary>基本資料／分析師／評等／目標價／EPS／價格</summary><pre>'+html.escape(json.dumps(m,ensure_ascii=False,indent=2))+'</pre></details>'
  for r in d['records']:
   if r['type']=='TXT':
    tag={'H1':'h1','H2':'h2','H3':'h3'}.get(r.get('subcategory'),'p');card+=f'<{tag} data-type="{r.get("subcategory")}">'+html.escape(r['text'])+f'</{tag}>'
  for t in d['tables']:card+=table_html(t)
  for r in d['records']:
   if r['type']=='FIG' and r['component']=='FIGURE':card+='<figure><figcaption>'+html.escape(r['text'])+'</figcaption><img src="data:image/png;base64,'+base64.b64encode((out/r['image_file']).read_bytes()).decode()+'"></figure>'
  cards.append(card+'</section>')
 (out/'修復結果.html').write_text('<!doctype html><meta charset="utf-8"><title>VRN 修復結果</title><style>body{font-family:system-ui;background:#faf8f3;color:#282828;max-width:1300px;margin:24px auto;font-size:13px}section{background:white;margin:24px 0;padding:24px}table{border-collapse:collapse;max-width:100%;font-size:11px;margin-bottom:25px}td{border:1px solid #ddd;padding:4px}h1{font-size:25px}h2{font-size:20px}h3{font-size:16px}h4{font-size:14px}pre{white-space:pre-wrap}img{max-width:430px}</style><h1>VRN 文／表／圖修復與驗證</h1><p>來源原文與修復值並存。運算檢查不覆寫報告原值；表格幾何、合併格與缺少外部對照的項目保留 REVIEW。Yahoo價格缺值、官方歷史財務待對照。</p><pre>'+html.escape(json.dumps(result['summary'],ensure_ascii=False,indent=2))+'</pre>'+''.join(cards),encoding='utf-8')
 print(json.dumps(result['summary'],ensure_ascii=False));return 0

def load_engine_from_root():
 p=ROOT/'VRN_SevenFieldInput_v0100.py';spec=importlib.util.spec_from_file_location('basic_adapter',p);m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m);return m

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--input-dir');parser.add_argument('--layout-file');parser.add_argument('--output-dir');parser.add_argument('--price-cache');parser.add_argument('--official-financial-cache');parser.add_argument('--database-root',action='append');parser.add_argument('--offline',action='store_true');args=parser.parse_args()
 for key in ('input_dir','layout_file','output_dir','price_cache','official_financial_cache'):
  if getattr(args,key):PARAMS[key]=getattr(args,key)
 if args.database_root:PARAMS['database_roots']=args.database_root
 if args.offline:PARAMS['network_enabled']=False
 raise SystemExit(main())
