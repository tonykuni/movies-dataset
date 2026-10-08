"""Single engine first, then dual only when candidates fail structural checks.
All candidates are kept. Agreement is not proof of original-PDF correctness.
No OCR, cloud parsing, installation or mutation of source PDFs.
"""
from pathlib import Path
import concurrent.futures, hashlib, importlib.util, json, re, subprocess
import pdfplumber
CONFIG={'single_order':['pdfplumber','camelot','tabula'],'camelot_enabled':True,'camelot_flavors':['stream','lattice'],'camelot_optional_flavors':['network','hybrid'],'camelot_stream_options':{'row_tol':3,'column_tol':0},'camelot_lattice_options':{'line_scale':40},'dual_pairs':[['pdfplumber','camelot'],['pdfplumber','tabula']],'ocr_enabled':False,'cloud_enabled':False}

def clean(s):return re.sub(r'\s+','',str(s or '')).strip()
def numbers(rows):
 return [clean(c).replace('−','-') for r in rows for c in r if re.fullmatch(r'[+\-−]?\(?\d[\d,]*(?:\.\d+)?\)?%?[AEFP]?',clean(c))]

def assess(rows,reference):
 nums=numbers(rows);expected=numbers(reference)
 from collections import Counter
 a,b=Counter(nums),Counter(expected);matched=sum((a&b).values())
 recall=matched/max(1,len(expected));precision=matched/max(1,len(nums))
 widths=[len(r) for r in rows];nonempty=sum(bool(clean(c)) for r in rows for c in r)
 return {'rows':len(rows),'columns_max':max(widths,default=0),'numeric_precision':round(precision,4),'numeric_recall':round(recall,4),'nonempty_cells':nonempty,'pass':bool(rows and len(expected)>=3 and recall>=.97 and precision>=.97 and all(len(r)==len(reference[0]) for r in rows)), 'meaning':'agreement with coordinate reconstruction only; source geometry and arithmetic still require review'}

def camelot_candidates(path,page,bbox,page_height,reference):
 """Optional adapter; never installs dependencies or downloads models."""
 if not CONFIG['camelot_enabled']:return [{'engine':'camelot','status':'DISABLED_BY_CONFIG'}]
 if not importlib.util.find_spec('camelot'):return [{'engine':'camelot','status':'DEPENDENCY_UNAVAILABLE','installation_owner':'USER_DESIGNATED_OTHER_PERSON'}]
 import camelot
 results=[];area=f'{bbox[0]},{page_height-bbox[1]},{bbox[2]},{page_height-bbox[3]}'
 for flavor in CONFIG['camelot_flavors']:
  try:
   if flavor not in ('stream','lattice','network','hybrid'):raise ValueError('Only explicit native-text parsers enabled; no ML/OCR or auto route')
   options=CONFIG['camelot_stream_options'] if flavor=='stream' else CONFIG['camelot_lattice_options'] if flavor=='lattice' else {}
   found=camelot.read_pdf(str(path),pages=str(page),flavor=flavor,table_areas=[area],**options)
   for item in found:
    rows=[[clean(c) for c in row] for row in item.df.fillna('').values.tolist()];spans=[]
    for ri,row in enumerate(getattr(item,'cells',[])):
     for ci,cell in enumerate(row):
      if getattr(cell,'hspan',False) or getattr(cell,'vspan',False):spans.append({'row':ri,'column':ci,'bbox_bottom_origin':[cell.x1,cell.y1,cell.x2,cell.y2],'horizontal_span':bool(getattr(cell,'hspan',False)),'vertical_span':bool(getattr(cell,'vspan',False)),'action':'EVIDENCE_ONLY_NO_NUMERIC_FILL'})
    results.append({'engine':'camelot','engine_version':getattr(camelot,'__version__','UNKNOWN'),'mode':flavor,'cells':rows,'quality':assess(rows,reference),'parsing_report':getattr(item,'parsing_report',{}),'span_evidence':spans,'area_bottom_origin':area,'coordinate_conversion':'x0,height-y0,x1,height-y1'})
  except Exception as ex:results.append({'engine':'camelot','mode':flavor,'status':'ENGINE_ERROR','error':str(ex)[:240]})
 return results or [{'engine':'camelot','status':'NO_TABLE_FOUND'}]

def one_table(t,path,jar,candidate_dir):
 bbox=t['bbox_pt'];reference=[r['cells'] for r in t['records'] if r['component'] in ('ROW','HEADER')];candidates=[]
 availability=bool(importlib.util.find_spec('camelot'))
 signature=hashlib.sha256(json.dumps([reference,bbox,t['page'],path.stat().st_size,path.stat().st_mtime_ns,t['validation'],availability,CONFIG],ensure_ascii=False,sort_keys=True).encode()).hexdigest()
 saved=candidate_dir/(t['id']+'.json')
 if saved.is_file():
  previous=json.loads(saved.read_text(encoding='utf-8'))
  if previous.get('input_signature')==signature:return {k:v for k,v in previous.items() if k!='candidates'}|{'candidate_count':len(previous['candidates']),'cache_reused':True}
 arithmetic_failed=any(v['status']=='FAIL_REVIEW' for v in t['validation'])
 with pdfplumber.open(path) as pdf:
  height=pdf.pages[t['page']-1].height
  crop=pdf.pages[t['page']-1].crop(tuple(bbox))
  for mode in ('lines','text'):
   settings={'vertical_strategy':mode,'horizontal_strategy':mode,'intersection_tolerance':6,'text_x_tolerance':2,'text_y_tolerance':3}
   for rows in crop.extract_tables(settings):
    rows=[[clean(c) for c in r] for r in rows];candidates.append({'engine':'pdfplumber','mode':mode,'cells':rows,'quality':assess(rows,reference)})
 primary=next((c for c in candidates if c['quality']['pass']),None) if not arithmetic_failed else None
 route='SINGLE_PDFPLUMBER' if primary else None
 if not primary and CONFIG['camelot_enabled']:
  candidates+=camelot_candidates(path,t['page'],bbox,height,reference)
  primary=next((c for c in candidates if c.get('quality',{}).get('pass') and c['engine']=='camelot'),None) if not arithmetic_failed else None
  if primary:route='SINGLE_CAMELOT'
 if not primary and jar.is_file():
  for mode,flag in [('stream','-t'),('lattice','-l')]:
   try:
    call=subprocess.run(['java','-jar',str(jar),'-p',str(t['page']),'-a',f'{bbox[1]},{bbox[0]},{bbox[3]},{bbox[2]}',flag,'-f','JSON',str(path)],capture_output=True,text=True,timeout=30)
    if call.returncode:raise ValueError(call.stderr[-160:])
    for item in json.loads(call.stdout or '[]'):
     rows=[[clean(c.get('text','')) for c in r] for r in item.get('data',[])];candidates.append({'engine':'tabula','mode':mode,'cells':rows,'quality':assess(rows,reference)})
   except Exception as ex:candidates.append({'engine':'tabula','mode':mode,'error':str(ex)[:160]})
   primary=next((c for c in candidates if c.get('quality',{}).get('pass') and c['engine']=='tabula'),None) if not arithmetic_failed else None
   if primary:route='SINGLE_TABULA';break
 if not primary:route='DUAL_PDFPLUMBER_CAMELOT_REVIEW' if any(c['engine']=='camelot' and c.get('cells') for c in candidates) else 'DUAL_PDFPLUMBER_TABULA_REVIEW' if any(c['engine']=='tabula' for c in candidates) else 'DUAL_UNAVAILABLE_REVIEW'
 # Preserve originals; weak candidate agreement never overwrites numeric source.
 payload={'table_id':t['id'],'input_signature':signature,'page':t['page'],'bbox_pt':bbox,'route':route,'arithmetic_failed':arithmetic_failed,'primary':{'engine':primary['engine'],'mode':primary['mode']} if primary else None,'candidates':candidates,'retained_grid':'pdfplumber characters assigned using native geometry; candidates require adjudication','camelot_status':'AVAILABLE' if importlib.util.find_spec('camelot') else 'DEPENDENCY_UNAVAILABLE','status':'CANDIDATE_AGREEMENT_GEOMETRY_REVIEW' if primary else 'DUAL_REVIEW_REQUIRED'}
 (candidate_dir/(t['id']+'.json')).write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')
 return {k:v for k,v in payload.items() if k!='candidates'}|{'candidate_count':len(candidates)}

def run(docs,input_dir,out,root):
 candidate_dir=out/'engine_candidates';candidate_dir.mkdir(exist_ok=True);jar=root/'deps/tabula/tabula-1.0.5-jar-with-dependencies.jar'
 if not jar.is_file() and importlib.util.find_spec('tabula'):
  import tabula
  jars=list(Path(tabula.__file__).parent.glob('*.jar'))
  if jars:jar=jars[0]
 jobs=[(t,input_dir/d['filename']) for d in docs for t in d['tables']]
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
  futures=[pool.submit(one_table,t,path,jar,candidate_dir) for t,path in jobs];results=[]
  for i,f in enumerate(futures):
   results.append(f.result())
   if i%10==0:print('table router',i+1,'/',len(jobs),flush=True)
 return results
