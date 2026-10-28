#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE]
# [VIA:ACCEL-BRIDGE:v0111] 所有作業動詞可觀測；不把插樁宣稱成實際加速。
"""Read-only content, SSOT, code and policy matrices. Never writes a database."""
from __future__ import annotations
import ast,collections,hashlib,json,os,re,threading,time,zipfile
from pathlib import Path
from xml.etree import ElementTree as ET
from VRN2_Workbench_v0102 import verb,now,file_hash

# Editable input parameters. No hidden stock, page-count, file-count or size filter.
SOURCE_DIRECTORY=Path(os.environ.get('VIA_VRN_SOURCE') or r'C:\測試樣本報告')
EXTENSIONS={'.pdf','.doc','.docx','.txt','.png','.jpg','.jpeg','.tif','.tiff','.bmp','.webp','.gif'}
PROBE_MIN_CHARS=40
PROBE_MAX_BAD_RATIO=.02
REVIEW_PAGE_SIZE=100
INVENTORY_TTL_SECONDS=60
XML_NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}

@verb
def decode_text(data):
    for encoding in ('utf-8-sig','utf-16' if data[:2] in (b'\xff\xfe',b'\xfe\xff') else 'utf-8','cp950'):
        try:return data.decode(encoding),encoding
        except UnicodeError:pass
    raise ValueError('文字編碼未能無損識別，保留原檔待核對')

@verb
def word_text(path):
    with zipfile.ZipFile(path) as z:
        node=ET.fromstring(z.read('word/document.xml'))
    paragraphs=[''.join(x.text or '' for x in p.findall('.//w:t',XML_NS)) for p in node.findall('.//w:p',XML_NS)]
    return '\n'.join(paragraphs),len(node.findall('.//w:tbl/w:tr',XML_NS)),len(node.findall('.//{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}inline'))

@verb
def probe(path):
    """Inspect every PDF page without rasterising or starting any OCR model."""
    path=Path(path);ext=path.suffix.lower();rows=[]
    if ext=='.pdf':
        import fitz
        with fitz.open(path) as doc:
            if doc.needs_pass:raise ValueError('加密 PDF 需要密碼，未略過或假裝成功')
            for number,page in enumerate(doc,1):
                blocks=[b for b in page.get_text('blocks') if len(b)>6 and b[6]==0]
                text='\n'.join(b[4] for b in blocks);chars=len(text.strip())
                bad=sum(c=='\ufffd' or '\ue000'<=c<='\uf8ff' for c in text)/max(1,len(text))
                has_image=bool(page.get_images());has_vectors=bool(page.get_drawings()) if not chars and not has_image else False
                mode='OCR_CANDIDATE' if bad>PROBE_MAX_BAD_RATIO or (chars<PROBE_MIN_CHARS and (has_image or has_vectors)) else 'TEXT_LAYER' if chars>=PROBE_MIN_CHARS else 'SPARSE_NATIVE_TEXT' if chars else 'EMPTY_PAGE'
                rows.append({'page':number,'text_blocks':len(blocks),'characters':chars,'table_rows':None,'bad_ratio':bad,'content_probe':mode,'reason':'文字層字數／錯碼篩查；OCR 候選尚非辨識失敗'})
    elif ext=='.txt':
        text,encoding=decode_text(path.read_bytes());rows=[{'page':None,'text_blocks':len([s for s in text.split('\n\n') if s.strip()]),'characters':len(text),'table_rows':None,'content_probe':'NATIVE_TEXT','encoding':encoding}]
    elif ext=='.docx':
        text,count,images=word_text(path);rows=[{'page':None,'text_blocks':len(text.splitlines()),'characters':len(text),'table_rows':count,'inline_images':images,'content_probe':'WORD_NATIVE_TEXT' if text.strip() else 'WORD_RENDER_OCR_CANDIDATE'}]
    elif ext=='.doc':rows=[{'page':None,'text_blocks':None,'table_rows':None,'content_probe':'WORD_RENDER_REQUIRED'}]
    else:
        from PIL import Image
        with Image.open(path) as im:
            for number in range(getattr(im,'n_frames',1)):
                im.seek(number);rows.append({'page':number+1,'text_blocks':0,'table_rows':None,'pixels':list(im.size),'content_probe':'IMAGE_OCR_CANDIDATE'})
    return rows

@verb
def load_json(path,default):
    try:return json.loads(Path(path).read_text(encoding='utf-8-sig'))
    except (ValueError,OSError):return default

@verb
def flatten(value,prefix=''):
    result=[]
    if isinstance(value,dict):
        for key,item in value.items():result.extend(flatten(item,(prefix+'.' if prefix else '')+str(key)))
    elif isinstance(value,list):
        for i,item in enumerate(value):result.extend(flatten(item,f'{prefix}[{i}]'))
    else:result.append({'key':prefix,'value':value})
    return result

class Review:
    @verb
    def __init__(self,state):
        self.state=state;self.lock=threading.RLock();self.rows=[];self.path_cache={};self.inventory_cache=None;self.inventory_at=0;self.inventory_status='IDLE';self.inventory_error=None
        self.progress={'status':'IDLE','percent':0,'completed':0,'total':0,'message':'尚未掃描；唯讀、零落庫'};self.reference=None
    @verb
    def begin(self):
        with self.lock:
            if self.progress['status']=='RUNNING':return dict(self.progress)
            self.progress={'status':'RUNNING','percent':0,'completed':0,'total':0,'message':'列舉來源檔案；未啟動 OCR／未重抽摘要'}
        threading.Thread(target=self.scan,daemon=True).start();return dict(self.progress)
    @verb
    def existing_records(self):
        records={}
        for home in (self.state.root/'VIA_Reports'/'vrn'/'p1view',self.state.root/'VIA_Reports'/'vrn2'/'p1view'):
            path=home/'P1VIEW_latest.json'
            data=load_json(path,[])
            if isinstance(data,list):
                for r in data:
                    if isinstance(r,dict) and r.get('file'):records.setdefault(Path(r['file']).name,[]).append((r,str(path)))
        return records
    @verb
    def scan(self):
        try:
            source=SOURCE_DIRECTORY
            if not source.is_dir():raise FileNotFoundError('來源資料夾不存在：'+str(source))
            files=sorted(p for p in source.rglob('*') if p.is_file() and not p.is_symlink() and p.suffix.lower() in EXTENSIONS)
            existing=self.existing_records();results=[];total=len(files);self.progress.update(total=total)
            name_counts=collections.Counter(p.name.casefold() for p in files)
            for i,path in enumerate(files,1):
                stat=path.stat();key=(str(path),stat.st_size,stat.st_mtime_ns);cached=self.path_cache.get(key)
                if cached:row=dict(cached)
                else:
                    row={'source_document':str(path.relative_to(source)),'pdf_name':path.name if path.suffix.lower()=='.pdf' else None,'path':str(path),'format':path.suffix.lower()[1:],'bytes':stat.st_size,'modified_ns':stat.st_mtime_ns,'status':'PROBED_READ_ONLY'}
                    try:
                        row['sha256']=file_hash(path);pages=probe(path);row['pages']=pages
                        row['text_blocks']=sum(p.get('text_blocks') or 0 for p in pages);row['table_rows']=sum(p['table_rows'] for p in pages if p.get('table_rows') is not None) if any(p.get('table_rows') is not None for p in pages) else None
                        row['ocr_pages']=[p['page'] for p in pages if 'OCR_CANDIDATE' in p['content_probe']]
                        row['content_probe']='OCR_CANDIDATES' if row['ocr_pages'] else 'NATIVE_LAYER_PROBED'
                        row['status']='PROBED_UNVERIFIED';row['coverage']='ALL_PAGES_PROBED' if path.suffix.lower()=='.pdf' else 'SOURCE_PROBED'
                    except Exception as exc:row.update(status='ERROR',error=type(exc).__name__+': '+str(exc),content_probe='FAILED',coverage='UNVERIFIED')
                    self.path_cache[key]=dict(row)
                # File-name joining alone does not certify content identity. Keep old counts as evidence only.
                old=existing.get(path.name,[])
                row['prior_evidence']=[]
                for rec,evidence_path in old:
                    if name_counts[path.name.casefold()]>1:row['join_status']='AMBIGUOUS_SAME_NAME';continue
                    pages=rec.get('pages') or [];numbers=[p.get('pno') for p in pages]
                    row['prior_evidence'].append({'path':evidence_path,'coverage':'FIRSTPAGE' if numbers==[1] else 'SELECTED_PAGES','page_numbers':numbers,'table_rows':sum(len(z.get('rows') or []) for p in pages for z in p.get('zones') or []),'hash_verified':bool(row.get('sha256') and (rec.get('sha256')==row['sha256'] or rec.get('pdf_sha256')==row['sha256'])),'lamp':rec.get('lamp')})
                row.setdefault('join_status','NAME_ONLY_UNVERIFIED' if old else 'NO_PRIOR_RECORD')
                receipt=self.state.receipts.get(row.get('sha256'),{})
                row['preserve_successful_summary']=receipt.get('has_summary') or receipt.get('report_identity',{}).get('report') is not None
                row['next_action']='REUSE_SUMMARY_FOCUS_OCR' if row['preserve_successful_summary'] and row.get('ocr_pages') else 'REUSE_EXISTING_REAUDIT' if row['preserve_successful_summary'] else 'FOCUS_OCR' if row.get('ocr_pages') else 'EXTRACT_IF_DATABASE_MISSING'
                results.append(row)
                with self.lock:self.rows=list(results);self.progress.update(completed=i,percent=100*i/max(1,total),message=path.name)
            self.progress.update(status='DONE',percent=100,message='內容層探測完成；未執行 OCR、未更新資料庫',at=now())
        except Exception as exc:self.progress.update(status='FAILED',message=str(exc))
    @verb
    def start_inventory(self):
        with self.lock:
            if self.inventory_status=='RUNNING':return self.inventory_status
            if self.inventory_cache and time.monotonic()-self.inventory_at<INVENTORY_TTL_SECONDS:return self.inventory_status
            self.inventory_status='RUNNING'
        threading.Thread(target=self.build_inventory,daemon=True).start();return self.inventory_status
    @verb
    def build_inventory(self):
        try:
            result=self.inventory();self.inventory_cache=result;self.inventory_at=time.monotonic();self.inventory_error=None;self.inventory_status='DONE'
        except Exception as exc:self.inventory_error=str(exc);self.inventory_status='FAILED'
    @verb
    def inventory(self):
        modules=self.state.root/'functional modules'/'VRN';code=[];defs=[];libs=[];ssot=[];policies=[];conflicts=[];params=[]
        sources=list(modules.rglob('*.py')) if modules.is_dir() else []
        for path in sorted(sources):
            if any(part in ('__pycache__','.git') for part in path.parts):continue
            relative=str(path.relative_to(modules));family=re.sub(r'_v\d+.*$','',path.stem)
            record={'file':relative,'family':family,'type':'ENG' if '_ENG' in path.name else 'MDL','sha256':file_hash(path),'status':'STATIC_ONLY_NOT_EXECUTED'}
            try:
                tree=ast.parse(path.read_text(encoding='utf-8-sig'))
                for node in ast.walk(tree):
                    if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):
                        defs.append({'file':relative,'type':'CLSS' if isinstance(node,ast.ClassDef) else 'FNC','name':node.name,'line':node.lineno,'instrumented':any('verb' in ast.unparse(d) or 'accel' in ast.unparse(d).lower() for d in node.decorator_list)})
                    if isinstance(node,(ast.Import,ast.ImportFrom)):
                        names=[x.name for x in node.names] if isinstance(node,ast.Import) else [node.module or '.']
                        libs.extend({'file':relative,'type':'LIB','module':n,'line':node.lineno} for n in names)
                    if isinstance(node,ast.Assign) and any(isinstance(n,ast.Name) and n.id.isupper() for n in node.targets):
                        try:value=ast.literal_eval(node.value)
                        except (ValueError,TypeError):continue
                        if isinstance(value,(str,int,float,bool,type(None))) and len(str(value))<1000:
                            for n in node.targets:
                                if isinstance(n,ast.Name) and n.id.isupper() and not re.search(r'B64|TOKEN|SECRET|PASS|CRED|KEY|SHA',n.id):params.append({'source':relative,'parameter':n.id,'value':value,'basis':'static literal; may be overridden at runtime'})
            except (SyntaxError,UnicodeError) as exc:record['status']='SYNTAX_ERROR';conflicts.append({'file':relative,'type':'SYNTAX_ERROR','detail':str(exc),'status':'RED'})
            code.append(record)
        json_files=set((modules/'SSOT').rglob('*.json')) if (modules/'SSOT').is_dir() else set()
        json_files.update(modules.glob('*Policy*.json'));json_files.update((self.state.root/'VIA_Reports'/'vrn2'/'ssot_unified').glob('*.json'))
        for path in sorted(json_files):
            duplicates=[]
            @verb
            def pairs(items):
                output={}
                for k,v in items:
                    if k in output:duplicates.append(k)
                    output[k]=v
                return output
            try:
                obj=json.loads(path.read_text(encoding='utf-8-sig'),object_pairs_hook=pairs)
                target=policies if 'policy' in path.name.lower() else ssot
                target.extend(dict(file=str(path),sha256=file_hash(path),**r) for r in flatten(obj))
                for k in duplicates:conflicts.append({'file':str(path),'type':'DUPLICATE_JSON_KEY','detail':k,'status':'RED'})
                for r in flatten(obj):
                    if 'conflict' in r['key'].lower() and r['value'] not in (None,False,0,'',[],{}):conflicts.append({'file':str(path),'type':'DECLARED_SSOT_CONFLICT','detail':r,'status':'YELLOW'})
            except (ValueError,OSError) as exc:conflicts.append({'file':str(path),'type':'JSON_INVALID','detail':str(exc),'status':'RED'})
        # Local tool locks are checked by hash without importing tools or making network requests.
        tool_rows=[];lock=self.state.root/'supportive modules'/'registry'/'VIA_ToolVersion_Lock_v0100.json'
        for name,item in load_json(lock,{}).items():
            if not isinstance(item,dict) or not item.get('path'):continue
            raw=Path(item['path']);options=[raw] if raw.is_absolute() else [self.state.root/raw,self.state.root.parent/raw];actual=next((p for p in options if p.is_file()),None)
            expected=item.get('sha256');status='UNVERIFIED'
            if actual and expected:
                data=actual.read_bytes();status='HASH_MATCH' if expected in (hashlib.sha256(data).hexdigest(),hashlib.sha256(data.replace(b'\r\n',b'\n')).hexdigest()) else 'HASH_MISMATCH'
            elif not actual:status='MISSING'
            tool_rows.append({'tool':name,'path':str(actual or raw),'status':status,'expected_sha256':expected})
            if status!='HASH_MATCH':conflicts.append({'file':str(actual or raw),'type':'TOOL_LOCK_'+status,'detail':name,'status':'RED' if status=='HASH_MISMATCH' else 'YELLOW'})
        return {'modules':code,'definitions':defs,'libraries':libs,'ssot':ssot,'parameters':params,'policies':policies,'tools':tool_rows,'conflicts':conflicts,'environment':self.state.environment(),'engines':self.state.engines()+[r for r in code if r['type']=='ENG'],'note':'靜態掃描；不匯入舊管理器鏈，不做自動安裝，不代表所有功能已驗收。'}
    @verb
    def report_candidates(self):
        result=[]
        base=self.state.root/'VIA_Reports'
        if base.is_dir():
            for p in base.rglob('*.htm*'):
                if p.suffix.lower() not in ('.htm','.html') or p.is_symlink():continue
                text=p.read_text(encoding='utf-8-sig',errors='replace')
                score=sum(token.lower() in text.lower() for token in ('matrix','矩陣','BasicInfo','FinancialData','Summary','SSOT','reconcile'))
                if score>=3 or 'VRN-RECONCILE' in text:result.append({'path':str(p),'name':p.name,'matrix_integration_score':score,'modified_ns':p.stat().st_mtime_ns,'is_reconcile':('VRN-RECONCILE' in text),'sha256':file_hash(p)})
        return sorted(result,key=lambda r:(r['is_reconcile'],r['matrix_integration_score'],r['modified_ns']),reverse=True)
    @verb
    def reference_html(self,path):
        # Return content to a sandboxed iframe. No file write, network, or script permission.
        candidate=Path(path).resolve();allowed=(self.state.root/'VIA_Reports').resolve()
        if candidate.suffix.lower() not in ('.html','.htm') or not candidate.is_relative_to(allowed):raise ValueError('請選本系統報告目錄內的 HTML')
        text=candidate.read_text(encoding='utf-8-sig',errors='strict')
        self.reference={'path':str(candidate),'sha256':file_hash(candidate),'at':now(),'mode':'READ_ONLY_VISUAL_REFERENCE'}
        return {'html':text,'reference':self.reference,'note':'保留原 HTML 視覺。唯讀 iframe 不允許腳本、外連或操作後端。'}
    @verb
    def page(self,dataset,offset=0):
        offset=max(0,int(offset));inventory=self.inventory_cache or {};self.start_inventory()
        if dataset=='reconcile':rows=[{k:v for k,v in row.items() if k!='path'} for row in self.rows]
        elif dataset=='archives':rows=self.report_candidates()
        elif dataset=='environment':rows=inventory.get('environment',[])+inventory.get('tools',[])+inventory.get('conflicts',[])
        elif dataset=='registry':rows=inventory.get('modules',[])+inventory.get('definitions',[])+inventory.get('libraries',[])
        elif dataset=='definitions':rows=inventory.get('definitions',[])+inventory.get('libraries',[])
        else:rows=inventory.get(dataset,[])
        return {'dataset':dataset,'rows':rows[offset:offset+REVIEW_PAGE_SIZE],'offset':offset,'limit':REVIEW_PAGE_SIZE,'total':len(rows),'scan':dict(self.progress),'inventory_status':self.inventory_status,'inventory_error':self.inventory_error,'reference':self.reference,'read_only':True,'zero_database_writes':True,'source_directory':str(SOURCE_DIRECTORY)}
