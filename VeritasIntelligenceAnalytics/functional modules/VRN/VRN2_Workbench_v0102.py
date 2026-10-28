#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE]
# [VIA:ACCEL-BRIDGE:v0111] 動詞登記、耗時稽核及可驗證外掛；不冒稱已連到 Celeritas。
"""Windows/local VRN-2 workbench. JSON exchange, versioned Parquet lake, DuckDB merge."""
from __future__ import annotations
import argparse, ast, csv, datetime as dt, functools, hashlib, html, importlib.util, io, json, math, os, secrets, shutil, subprocess, sys, threading, time, urllib.parse, uuid
from pathlib import Path

# 1. Configuration and contracts
VERSION='v0102'
HOST='127.0.0.1'
CHUNK_BYTES=1024*1024
PAGE_SIZE=100
MEMORY_LIMIT='512MB'
THREADS=min(4,os.cpu_count() or 1)
MAX_JSON_BYTES=2*1024*1024
REPORT_EXTENSIONS={'.pdf','.doc','.docx','.txt','.png','.jpg','.jpeg','.tif','.tiff','.bmp','.webp','.gif'}
DATASETS=('BasicInfo','FinancialData','Summary','ContentData')
MAX_JOB_SECONDS=14400
PDF_WINDOWS_FONT=Path(os.environ.get('WINDIR','C:/Windows'))/'Fonts'/'msjh.ttc'
TZ=dt.timezone(dt.timedelta(hours=8))
POLICY_VERSION='VRN2_POLICY_v0104'
NUMBER_KEYS={'VALUE_NUM','VALUE_FINAL','VALUE_FINAL_CANONICAL','VALUE_ACTUAL','RECON_RATIO','RECON_DIFF','TARGET_PRICE','TARGET_PRICE(ADJ)','CURRENT_PRICE_REPORT','UPSIDE_ADJ','ADJ_CLOSE','ADJ_CLOSE_BEFORE_REPORT'}|{f'{k}_Y{i}' for k in ('DILUTED_EPS','DPS','BVPS','ROE','PER','PBR','CASH_YIELD') for i in range(3)}
DB_GATES=('VCGC','VDF','VRN-1','VAP','VSC','VRS')

# 2. Audit/instrumentation. All operational functions/methods use this boundary.
def verb(fn):
    @functools.wraps(fn)
    def wrapped(*args,**kwargs):
        start=time.monotonic()
        try:return fn(*args,**kwargs)
        finally:
            owner=args[0] if args else None
            state=getattr(owner,'state',None) or getattr(owner,'_state',None) or getattr(getattr(owner,'server',None),'state',None) or (owner if isinstance(owner,State) else None)
            if state is not None and hasattr(state,'metrics'):
                with state.metrics_lock:
                    item=state.metrics.setdefault(fn.__qualname__,{'calls':0,'seconds':0})
                    item['calls']+=1;item['seconds']+=time.monotonic()-start
    return wrapped

@verb
def now():return dt.datetime.now(TZ).isoformat(timespec='seconds')

@verb
def safe_json(obj):return json.dumps(obj,ensure_ascii=False,allow_nan=False,default=str)

@verb
def atomic_json(path,obj):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name(path.name+'.'+uuid.uuid4().hex+'.tmp')
    tmp.write_text(safe_json(obj),encoding='utf-8');os.replace(tmp,path)

@verb
def read_json(path,default):
    path=Path(path)
    return json.loads(path.read_text(encoding='utf-8-sig')) if path.is_file() else default

@verb
def file_hash(path):
    digest=hashlib.sha256()
    with Path(path).open('rb') as source:
        for chunk in iter(lambda:source.read(CHUNK_BYTES),b''):digest.update(chunk)
    return digest.hexdigest()

@verb
def text_hash(obj):return hashlib.sha256(safe_json(obj).encode('utf-8')).hexdigest()

@verb
def component_signature(root):
    folder=Path(root)/'functional modules'/'VRN';parts=[]
    for pattern in ('VRN_ENG397*_v*.py','VRN_ENG062*_v*.py','VRN_SystemManager_v*.py','VRN2_FinanceContract_v*.py'):
        candidates=sorted(folder.glob(pattern))
        if candidates:parts.append((candidates[-1].name,file_hash(candidates[-1])))
    for path in sorted((folder/'SSOT').glob('*.json')):parts.append((path.name,file_hash(path)))
    return text_hash([POLICY_VERSION,parts])

@verb
def extraction_signature(root):
    folder=Path(root)/'functional modules'/'VRN';parts=[]
    for pattern in ('VRN_ENG397*_v*.py','VRN2_OCRBridge*_v*.py'):
        candidates=sorted(folder.glob(pattern))
        if candidates:parts.append((candidates[-1].name,file_hash(candidates[-1])))
    return text_hash(['RAW_EXTRACTION_V1',parts,{k:os.environ.get(k,default) for k,default in [('VIA_VRN2_OCR_LADDER','200,325p'),('VIA_VRN2_OCR_MIN_CONF','0.85'),('VIA_VRN2_OCR_MIN_CHARS','40')]}])

@verb
def scan_coverage(path):
    tree=ast.parse(Path(path).read_text(encoding='utf-8'));found=[]
    for node in tree.body:
        nodes=[node] if isinstance(node,ast.FunctionDef) else [x for x in node.body if isinstance(x,ast.FunctionDef)] if isinstance(node,ast.ClassDef) else []
        for n in nodes:
            if n.name=='verb':continue # instrumentation infrastructure, not a work verb
            found.append({'verb':(node.name+'.' if isinstance(node,ast.ClassDef) else '')+n.name,'hook':any(isinstance(d,ast.Name) and d.id=='verb' for d in n.decorator_list)})
    return {'registered':sum(x['hook'] for x in found),'total':len(found),'verbs':found,'real_celeritas':'UNVERIFIED:需 PC 真實加速器正式 API 與執行證據','network':'只有鎖版 MarketFetch 可出網；Workbench 無直接外網傳輸'}

# 3. Managed input and incremental lake
class State:
    @verb
    def __init__(self,root,launcher,home=None):
        self.root=Path(root).resolve();self.launcher=Path(launcher).resolve()
        self.home=Path(home or self.root/'VIA_Reports'/'vrn2'/'workbench').resolve()
        self.home.mkdir(parents=True,exist_ok=True)
        self.lock=threading.RLock();self.metrics_lock=threading.Lock();self.metrics={};self.delete_tickets={};self.jobs={}
        self.manifest=self.home/'inputs.json';self.catalog=self.home/'lake'/'catalog.json'
        self.files=read_json(self.manifest,[]);self.receipts=read_json(self.home/'receipts.json',{})
        self.current_job=None;self.token=secrets.token_urlsafe(32);self.progress={'phase':'READY','percent':0,'label':'等待輸入','lamp':'YELLOW'};self.ui_ready=False;self.environment_cache=None;self._active_process=None
        from VRN2_Reconcile_v0100 import Review
        self.review=Review(self);self._worker_thread=None;self._stop_event=threading.Event()
        self.launch_signature=component_signature(self.root)
        # An interrupted worker never becomes success just because its PDF exists.
        for p in (self.home/'jobs').glob('*/job.json'):
            job=read_json(p,{})
            if job.get('status') in ('RUNNING','QUEUED'):job.update(status='INTERRUPTED',ended=now());atomic_json(p,job)
            self.jobs[job.get('id',p.parent.name)]=job
    @verb
    def save_inputs(self):atomic_json(self.manifest,self.files)
    @verb
    def event(self,action,payload):
        path=self.home/'audit.jsonl'
        with path.open('a',encoding='utf-8') as f:f.write(safe_json({'at':now(),'action':action,'payload':payload})+'\n')
    @verb
    def import_stream(self,name,modified_ms,stream,length):
        name=Path(str(name).replace('\\','/')).name
        if not name or Path(name).suffix.lower() not in REPORT_EXTENSIONS:raise ValueError('不支援的報告格式')
        if length<0:raise ValueError('無效容量')
        ident=uuid.uuid4().hex;folder=self.home/'input'/ident;folder.mkdir(parents=True)
        target=folder/name;digest=hashlib.sha256();remaining=length
        try:
            with target.open('xb') as f:
                while remaining:
                    data=stream.read(min(CHUNK_BYTES,remaining))
                    if not data:raise ValueError('檔案未完整傳入')
                    f.write(data);digest.update(data);remaining-=len(data)
            record={'id':ident,'name':name,'path':str(target),'size':length,'modified_ms':int(modified_ms or 0),'format':target.suffix.lower()[1:],'sha256':digest.hexdigest(),'imported':now(),'deleted':False}
            with self.lock:self.files.append(record);self.save_inputs();self.event('IMPORT',{'id':ident,'sha256':record['sha256']})
            return record
        except BaseException:
            shutil.rmtree(folder);raise
    @verb
    def import_paths(self,paths):
        result=[]
        for p in paths:
            source=Path(p).resolve();stat=source.stat()
            if not source.is_file() or source.is_symlink():raise ValueError('只接受一般檔案')
            with source.open('rb') as stream:result.append(self.import_stream(source.name,int(stat.st_mtime*1000),stream,stat.st_size))
        return result
    @verb
    def groups(self):
        active=[dict(r) for r in self.files if not r['deleted']];sizes={};names={};identities={};hashes={}
        for r in active:
            sizes.setdefault((r['format'],r['size']),[]).append(r['id']);names.setdefault(r['name'].casefold(),[]).append(r['id']);hashes.setdefault(r['sha256'],[]).append(r['id'])
            receipt=self.receipts.get(r['sha256'],{});identity=receipt.get('report_identity')
            if identity and all(identity.get(k) for k in ('ticker','broker','report_date','report')):identities.setdefault((identity['ticker'],identity['broker'],identity['report_date'],identity['report']),[]).append(r['id'])
        for r in active:
            r['candidate_group']=text_hash([r['format'],r['size']])[:10] if len(sizes[(r['format'],r['size'])])>1 else ''
            r['name_group']=text_hash(r['name'].casefold())[:10] if len(names[r['name'].casefold()])>1 else ''
            identity=self.receipts.get(r['sha256'],{}).get('report_identity') or {};key=tuple(identity.get(k) for k in ('ticker','broker','report_date','report'))
            r['identity_group']=text_hash(key)[:10] if key in identities and len(identities[key])>1 else ''
            r['exact_group']=r['sha256'][:12] if len(hashes[r['sha256']])>1 else ''
        return sorted(active,key=lambda r:(r['format'],r['size'],r['name'].casefold(),r['identity_group'],r['sha256']))
    @verb
    def delete_preview(self,ids):
        with self.lock:
            ids=set(ids);items=[r for r in self.files if r['id'] in ids and not r['deleted']]
            if len(items)!=len(ids) or not items:raise ValueError('勾選清單已變動或為空')
            ticket=secrets.token_urlsafe(24);self.delete_tickets[ticket]={'expires':time.time()+300,'items':{r['id']:r['sha256'] for r in items}}
            return {'ticket':ticket,'items':[{'id':r['id'],'name':r['name'],'size':r['size']} for r in items],'scope':'僅刪除本系統匯入副本，原始來源保留，可復原'}
    @verb
    def delete_confirm(self,ticket):
        with self.lock:
            if self.current_job:raise ValueError('工作執行中，暫不變更輸入')
            approved=self.delete_tickets.pop(ticket,None)
            if not approved or approved['expires']<time.time():raise ValueError('刪除確認已過期')
            items=[r for r in self.files if r['id'] in approved['items']]
            for r in items:
                if r['deleted'] or file_hash(r['path'])!=approved['items'][r['id']]:raise ValueError('副本已變更，請重新確認')
            moved=[]
            try:
                for r in items:
                    source=Path(r['path']);dest=self.home/'recycle'/r['id']/r['name'];dest.parent.mkdir(parents=True,exist_ok=True);os.replace(source,dest)
                    moved.append((r,source,dest));r.update(deleted=True,recycle_path=str(dest))
                self.save_inputs()
            except BaseException:
                for r,source,dest in reversed(moved):os.replace(dest,source);r['deleted']=False
                raise
            self.event('DELETE_COPIES',list(approved['items']));return {'deleted':len(items),'restorable':True}
    @verb
    def restore(self,ids):
        with self.lock:
            count=0
            for r in self.files:
                if r['id'] in ids and r['deleted']:
                    dest=Path(r['path']);dest.parent.mkdir(parents=True,exist_ok=True);os.replace(r['recycle_path'],dest);r['deleted']=False;count+=1
            self.save_inputs();self.event('RESTORE',ids);return {'restored':count}
    @verb
    def connect(self):
        import duckdb
        con=duckdb.connect();con.execute(f"SET memory_limit='{MEMORY_LIMIT}'");con.execute(f'SET threads={THREADS}')
        spill=self.home/'temp';spill.mkdir(exist_ok=True);con.execute('SET temp_directory=?',[str(spill)])
        return con
    @verb
    def ingest(self,books,report_ids,signature):
        import pyarrow as pa
        import pyarrow.parquet as pq
        with self.lock:
            cat=read_json(self.catalog,{'version':0,'tables':{}});version=cat['version']+1;paths={}
            snapshot=self.home/'lake'/'snapshots'/f'{version:08d}_{uuid.uuid4().hex[:8]}';snapshot.mkdir(parents=True)
            for dataset in DATASETS:
                rows=[];seen={}
                for original in books.get(dataset,[]):
                    r=dict(original);fname=r.get('FILENAME');rid=report_ids.get(fname)
                    if not rid:raise ValueError('輸出無法對應本輪報告內容指紋：'+str(fname))
                    r['REPORT_ID']=rid;r['_SIGNATURE']=signature;r['_UPDATED_AT']=now()
                    r['_OFFICIAL_RANK']=int(dataset=='FinancialData' and (r.get('ACTUAL_OVERRIDE') is True))
                    parts=([rid]+[str(r.get(k) or '') for k in ('PAGE','ZONE','ROW','KIND')]) if dataset=='ContentData' else [rid] if dataset!='FinancialData' else [rid]+[str(r.get(k) or '') for k in ('ITEM','PERIOD_STD','REPORT_SCOPE','UNIT','PAGE','ZONE')]
                    r['_ROW_KEY']=text_hash(parts)
                    content={k:v for k,v in r.items() if k!='_UPDATED_AT'}
                    if r['_ROW_KEY'] in seen and seen[r['_ROW_KEY']]!=content:raise ValueError('同主鍵多個數值，停止合併並保留原資料庫')
                    seen[r['_ROW_KEY']]=content;rows.append(r)
                if not rows:
                    if dataset in cat['tables']:paths[dataset]=cat['tables'][dataset]
                    continue
                columns=list(dict.fromkeys(k for r in rows for k in r))
                if dataset=='BasicInfo':
                    spec=read_json(Path(__file__).with_name('VRN2_Policy_v0104.json'),{}).get('headers',[])
                    keys=[h['key'] for h in spec];tails=['RECENT_REPORT_PRE_EARNINGS_FLAG','STATUS']
                    columns=[k for k in keys if k not in tails]+[k for k in columns if k not in keys]+tails
                arrays={} 
                for key in columns:
                    vals=[r.get(key) for r in rows]
                    if key in NUMBER_KEYS:
                        vals=[None if v in ('',None) else float(v) for v in vals]
                        if any(v is not None and not math.isfinite(v) for v in vals):raise ValueError('非有限數字拒絕進庫')
                        arrays[key]=pa.array(vals,type=pa.float64())
                    elif key=='_OFFICIAL_RANK':arrays[key]=pa.array(vals,type=pa.int8())
                    else:arrays[key]=pa.array([None if v is None else safe_json(v) if isinstance(v,(dict,list,bool)) else str(v) for v in vals],type=pa.string())
                incoming=snapshot/(dataset+'_incoming.parquet');pq.write_table(pa.table(arrays),incoming,compression='zstd')
                target=snapshot/(dataset+'.parquet');old=cat['tables'].get(dataset)
                with self.connect() as con:
                    con.read_parquet(str(incoming)).create_view('incoming_raw');con.execute('CREATE VIEW incoming AS SELECT *,1 AS _priority FROM incoming_raw')
                    if old:
                        con.read_parquet(old).create_view('previous_raw');con.execute('CREATE VIEW previous AS SELECT *,0 AS _priority FROM previous_raw')
                        sql='SELECT * FROM previous UNION ALL BY NAME SELECT * FROM incoming'
                    else:sql='SELECT * FROM incoming'
                    con.execute('CREATE TEMP TABLE merged AS SELECT * EXCLUDE(_priority) FROM ('+sql+') QUALIFY row_number() OVER(PARTITION BY _ROW_KEY ORDER BY _OFFICIAL_RANK DESC,_priority DESC)=1')
                    names=[row[0] for row in con.execute('DESCRIBE merged').fetchall()]
                    if dataset=='BasicInfo':
                        spec=read_json(Path(__file__).with_name('VRN2_Policy_v0104.json'),{}).get('headers',[]);keys=[h['key'] for h in spec];tails=['RECENT_REPORT_PRE_EARNINGS_FLAG','STATUS']
                        names=[k for k in keys if k not in tails]+[k for k in names if k not in keys]+tails
                    selected=','.join('"'+name.replace('"','""')+'"' for name in names)
                    con.execute('COPY (SELECT '+selected+' FROM merged) TO ? (FORMAT PARQUET, COMPRESSION ZSTD)',[str(target)])
                incoming.unlink();paths[dataset]=str(target)
            # Catalog is the atomic commit for ALL datasets. Earlier snapshots remain recoverable.
            new={'version':version,'updated':now(),'tables':paths,'policy':POLICY_VERSION}
            atomic_json(self.catalog,new);self.event('PARQUET_COMMIT',new)
            return new
    @verb
    def table(self,dataset,offset=0,limit=PAGE_SIZE):
        if dataset not in DATASETS+('Combined',):raise ValueError('未知資料冊')
        offset=max(0,int(offset));limit=min(PAGE_SIZE,max(1,int(limit)))
        cat=read_json(self.catalog,{'tables':{}})
        if dataset=='Combined':
            base=self.table('BasicInfo',offset,limit);rows=[];ids=[b['REPORT_ID'] for b in base['rows']];groups={}
            with self.connect() as con:
                for ds in ('FinancialData','Summary'):
                    path=cat['tables'].get(ds);groups[ds]={}
                    if path and ids:
                        found=con.execute('SELECT REPORT_ID,to_json(list(t)) FROM read_parquet(?) t WHERE REPORT_ID=ANY(?) GROUP BY REPORT_ID',[path,ids]).fetchall()
                        groups[ds]={rid:json.loads(payload) for rid,payload in found}
                for b in base['rows']:
                    rows.append({'Basic Info':b,'Financial Data':groups['FinancialData'].get(b['REPORT_ID'],[]),'Bullet Points Summary':groups['Summary'].get(b['REPORT_ID'],[])})
            return {'rows':rows,'total':base['total'],'offset':offset,'limit':limit,'dataset':dataset}
        path=cat['tables'].get(dataset)
        if not path:return {'rows':[],'total':0,'offset':offset,'limit':limit,'dataset':dataset}
        with self.connect() as con:
            total=con.execute('SELECT count(*) FROM read_parquet(?)',[path]).fetchone()[0]
            cur=con.execute('SELECT * FROM read_parquet(?) ORDER BY REPORT_ID,_ROW_KEY LIMIT ? OFFSET ?',[path,limit,offset]);names=[x[0] for x in cur.description];rows=[dict(zip(names,r)) for r in cur.fetchall()]
        return {'rows':rows,'total':total,'offset':offset,'limit':limit,'dataset':dataset}
    @verb
    def evidence_signature(self):
        folder=self.root/'VIA_Reports'/'vrn2'/'market'
        return text_hash([(n,file_hash(folder/n) if (folder/n).is_file() else None) for n in ('VRN2_Market_latest.json','VRN2_VerifiedEvidence.json')])
    @verb
    def audit_existing(self,items):
        """Revalidate lake records after official evidence changes, without invoking the PDF extractor."""
        ids={r['sha256'] for r in items};books={};mapping={}
        for ds in DATASETS:
            rows=[];offset=0
            while True:
                batch=self.table(ds,offset);offset+=batch['limit']
                for source in batch['rows']:
                    if source.get('REPORT_ID') not in ids:continue
                    row=dict(source)
                    for key in ('RAW_EVIDENCE','SOURCE_TEXT','ADJUSTED_VALUATION'):
                        if isinstance(row.get(key),str):row[key]=json.loads(row[key])
                    mapping[row['FILENAME']]=row['REPORT_ID'];rows.append(row)
                if offset>=batch['total']:break
            books[ds]=rows
        contract=Path(__file__).with_name('VRN2_FinanceContract_v0101.py')
        spec=importlib.util.spec_from_file_location('vrn2_reaudit',contract);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
        market_home=self.root/'VIA_Reports'/'vrn2'/'market';market=read_json(market_home/'VRN2_Market_latest.json',{'per_file':{}})
        extra=read_json(market_home/'VRN2_VerifiedEvidence.json',{'per_file':{}})
        for name,values in extra.get('per_file',{}).items():
            if name in mapping:market.setdefault('per_file',{}).setdefault(name,{}).update(values)
        proof=mod.apply_contract(books['BasicInfo'],books['FinancialData'],books['Summary'],market)
        for name,record in proof['files'].items():
            rid=mapping[name];receipt=self.receipts.get(rid,{})
            prior=read_json(self.home/'jobs'/receipt.get('job','missing')/'outputs'/'output'/'VRN2_SummarySource_latest.json',{})
            documents=[d for d in prior.get('documents',[]) if d.get('file')==name]
            quotes=documents[0].get('points',[]) if documents else []
            if not documents or documents[0].get('pdf_sha256')!=receipt.get('normalized_sha256',rid) or len([q for q in quotes if q.get('verbatim') and q.get('quote_sha256')==hashlib.sha256(str(q.get('text') or '').encode('utf-8')).hexdigest() and (q.get('reader')!='OCR' or q.get('visual_verified') is True)])<4:
                record['verified']=False;record['issues'].append('FOUR_SOURCE_QUOTES_UNVERIFIED')
        proof['verified']=bool(proof['files']) and all(r['verified'] for r in proof['files'].values())
        for row in books['BasicInfo']:
            rec=proof['files'][row['FILENAME']]
            if not rec['verified']:row['STATUS']='UNVERIFIED | '+' | '.join(rec['issues'])
        self.ingest(books,mapping,component_signature(self.root))
        for name,rid in mapping.items():self.receipts[rid].update(finance_verified=proof['files'][name]['verified'],evidence_signature=self.evidence_signature())
        atomic_json(self.home/'receipts.json',self.receipts);atomic_json(self.home/'VRN2_Reaudit_latest.json',proof)
        self.event('AUDIT_WITHOUT_PDF',{'reports':len(mapping),'verified':proof['verified']})
        return {'status':'AUDITED_VERIFIED' if proof['verified'] else 'AUDITED_UNVERIFIED','validation':proof,'message':'已用更新的官方證據重新驗證；沒有重抽 PDF'}

    @verb
    def plan(self):
        signature=component_signature(self.root);items=[]
        for r in self.groups():
            receipt=self.receipts.get(r['sha256']);tasks=[]
            if not receipt:tasks=['EXTRACT','VALIDATE','MERGE']
            elif receipt.get('extraction_signature') and receipt['extraction_signature']!=extraction_signature(self.root):tasks=['EXTRACT_CHANGED_ENGINE','VALIDATE','MERGE']
            elif receipt.get('missing'):tasks=['REPAIR_FIELDS:'+','.join(receipt['missing']),'VALIDATE','MERGE']
            elif receipt.get('signature')!=signature or not receipt.get('finance_verified'):tasks=['AUDIT_ONLY:既有擷取保留；政策/官方證據核對不重抽檔案']
            else:tasks=['CACHE_HIT']
            items.append({'id':r['id'],'sha256':r['sha256'],'name':r['name'],'tasks':tasks})
        unique={}
        for item in items:unique.setdefault(item['sha256'],item)
        return {'signature':signature,'policy':POLICY_VERSION,'items':items,'unique':list(unique.values()),'extraction_count':sum(any(t.startswith(('EXTRACT','REPAIR_FIELDS')) for t in r['tasks']) for r in unique.values()),'audit_only_count':sum(any(t.startswith('AUDIT_ONLY') for t in r['tasks']) for r in unique.values())}
    @verb
    def engines(self):
        modules=self.root/'functional modules'/'VRN';result=[]
        for family,inp,output in (('VRN_ENG397','PDF','JSON 分區/表格'),('VRN_ENG062','原文 JSON','四點原文 JSON'),('VRN2_MarketFetch','缺漏清單','官方資料及調整價 JSON'),('VRN_SystemManager','擷取結果 JSON','驗證資料冊 JSON'),('VRN2_FinanceContract','報告/官方 JSON','財務核對 JSON'),('VRN2_DocumentBridge','PDF/WORD/TXT/IMAGE','PDF 及來源證據 JSON'),('VRN2_ContentRepair','資料庫缺漏／頁面探測','全部頁面文字塊／表格列／OCR JSON'),('VRN2_Reconcile','來源與既有證據','唯讀矩陣 JSON'),('VRN2_CompanyMaster','四碼 TICKER','官方中英文簡稱 JSON')):
            hits=sorted(modules.glob(family+'*_v*.py'));p=hits[-1] if hits else None
            result.append({'family':family,'version':p.name if p else None,'input':inp,'production':'由本輪工作日誌判定；存在不代表成功','output':output,'spec':'JSON / '+POLICY_VERSION,'status':'AVAILABLE_NOT_EXECUTED' if p else 'MISSING','hash':file_hash(p) if p else None})
        result.append({'family':'DuckDB / Parquet','status':'READY' if all(importlib.util.find_spec(n) for n in ('duckdb','pyarrow')) else 'MISSING_DEPENDENCY','input':'已驗證與待驗證分級 JSON','production':'主鍵合併 / 官方值優先 / 原子 catalog','output':'Parquet','spec':'UTF-8 metadata; numeric float64'})
        return result
    @verb
    def status(self):
        with self.lock:return {'version':VERSION,'root':str(self.root),'files':self.groups(),'recycle':[{'id':r['id'],'name':r['name']} for r in self.files if r['deleted']],'plan':self.plan(),'engines':self.engines(),'coverage':scan_coverage(__file__),'metrics':dict(self.metrics),'catalog':read_json(self.catalog,{}),'jobs':list(self.jobs.values()),'progress':dict(self.progress),'environment':self.environment(),'review_progress':dict(self.review.progress),'inventory_status':self.review.inventory_status, 'transport':'NATIVE_JS_API_NO_HTTP','gates':read_json(self.home/'gates.json',{g:{'state':'UNCONFIGURED','reason':'需提供已註冊之本機入口，未猜測連結'} for g in DB_GATES})}

# 4. Focused jobs. The successful extractor stays external and unchanged.
    @verb
    def start_job(self):
        with self.lock:
            missing=[name for name in ('duckdb','pyarrow') if importlib.util.find_spec(name) is None]
            if missing:
                atomic_json(self.home/'VRN2_ENV_REQUEST.json',{'packages':missing,'owner':'VCGC'})
                raise ValueError('缺套件，已建立 VCGC 請求：'+','.join(missing))
            if self.current_job:raise ValueError('已有工作執行中')
            plan=self.plan();self._stop_event.clear()
            selected=[r for r in plan['unique'] if any(t.startswith(('EXTRACT','REPAIR_FIELDS')) for t in r['tasks'])]
            if not selected:
                changed=[r for r in plan['unique'] if any(t.startswith('AUDIT_ONLY') for t in r['tasks']) and self.receipts.get(r['sha256'],{}).get('evidence_signature')!=self.evidence_signature()]
                if changed:return self.audit_existing(changed)
                return {'status':'WAITING_EVIDENCE' if plan['audit_only_count'] else 'CACHE_HIT','plan':plan,'message':'未重抽 PDF；待官方補件/資料政策修復' if plan['audit_only_count'] else '資料庫已有相同內容與版本的資料'}
            ident=uuid.uuid4().hex;job={'id':ident,'status':'QUEUED','started':now(),'plan':plan,'files':selected};self.jobs[ident]=job;self.current_job=ident
            folder=self.home/'jobs'/ident;folder.mkdir(parents=True);atomic_json(folder/'job.json',job)
            thread=threading.Thread(target=self.run_job,args=(ident,),daemon=True);self._worker_thread=thread;thread.start();return job
    @verb
    def run_job(self,ident):
        job=self.jobs[ident];folder=self.home/'jobs'/ident;outputs=folder/'outputs';stage=folder/'input';stage.mkdir()
        try:
            job['status']='RUNNING';self.set_progress(job,5,'檢查輸入與快取');atomic_json(folder/'job.json',job);mapping={};seen=set();provenance={};job['conversion_errors']=[]
            for index,item in enumerate(job['files'],1):
                self.set_progress(job,5+int(14*(index-1)/max(1,len(job['files']))),'準備來源 '+str(index)+'/'+str(len(job['files']))+' · '+item['name'])
                record=next(r for r in self.files if r['id']==item['id']);source=Path(record['path'])
                if file_hash(source)!=item['sha256']:raise ValueError('輸入內容已變更')
                name=source.stem+'.pdf'
                if name.casefold() in seen:name=source.stem+'_'+item['sha256'][:12]+'.pdf'
                seen.add(name.casefold())
                try:
                    if self._stop_event.is_set():raise InterruptedError('使用者已關閉工作台')
                    from VRN2_DocumentBridge_v0100 import normalize
                    provenance[name]=normalize(source,stage/name);mapping[name]=item['sha256']
                except Exception as exc:job['conversion_errors'].append({'source_document':source.name,'error':str(exc)})
            atomic_json(folder/'source_provenance.json',provenance)
            if not mapping:raise RuntimeError('沒有可送往擷取引擎的來源；詳見轉換錯誤')
            self.set_progress(job,20,'輸入副本準備完成');atomic_json(folder/'report_ids.json',mapping)
            # Focused market input only; avoid old BasicInfo including unrelated reports.
            old=read_json(self.root/'VIA_Reports'/'vrn2'/'output'/'VRN2_BasicInfo_latest.json',[])
            focus=[r for r in old if r.get('FILENAME') in mapping];atomic_json(folder/'focus_basic.json',focus)
            env=dict(os.environ,VIA_ROOT=str(self.root),VIA_VRN_INPUT=str(stage),VIA_VRN2_JOB_OUTPUT=str(outputs),VIA_VRN2_MARKET_HOME=str(self.root/'VIA_Reports'/'vrn2'/'market'),VIA_VRN2_NO_PUSH='1',VIA_NO_OPEN='1',VIA_VRN2_P1_CACHE=str(self.root/'VIA_Reports'/'vrn2'/'p1_cache'),VIA_VRN2_OCR_CACHE=str(self.root/'VIA_Reports'/'vrn2'/'ocr_cache'),VIA_VRN2_ALLOW_ALL_INPUTS='1',PYTHONUTF8='1',PYTHONIOENCODING='utf-8')
            command=[sys.executable,'-X','utf8',str(self.launcher),'--focused-run','--focus-basic',str(folder/'focus_basic.json')]
            with (folder/'process.log').open('w',encoding='utf-8') as log:
                result=self.run_process(command,env,log,job)
            if result.returncode:raise RuntimeError('擷取程序 exit '+str(result.returncode)+'；詳見本輪日誌')
            self.set_progress(job,75,'讀取本輪結果與驗證');books={d:read_json(outputs/'output'/('VRN2_'+d+'_latest.json'),[]) for d in DATASETS}
            if not books['BasicInfo']:raise RuntimeError('本輪沒有 BasicInfo，拒絕沿用舊輸出')
            observed={r.get('FILENAME') for r in books['BasicInfo']}
            if not observed.issubset(mapping):raise RuntimeError('原管理器未遵守本輪範圍；不合併非本輪資料')
            proof=read_json(outputs/'output'/'VRN2_FinanceValidation_latest.json',{})
            signature=component_signature(self.root)
            for dataset,rows in books.items():
                for row in rows:
                    source=provenance.get(row.get('FILENAME'),{})
                    row['SOURCE_DOCUMENT']=source.get('source_document');row['NORMALIZED_PDF_SHA256']=source.get('pdf_sha256');row['CONVERSION_STATUS']=source.get('status')
                    if source.get('conversion_verified') is False:
                        row['STATUS']='UNVERIFIED_CONVERSION | '+str(row.get('STATUS') or '')
                        proof.setdefault('files',{}).setdefault(row['FILENAME'],{}).update(verified=False)
                        proof['verified']=False
            job['missing_output_reports']=sorted(set(mapping)-observed)
            if job['missing_output_reports']:proof['verified']=False
            self.preserve_successful_fields(books,mapping,job)
            for name in job.get('preserved_summaries',[]):
                proof.setdefault('files',{}).setdefault(name,{}).update(verified=False)
                proof['verified']=False
            self.set_progress(job,88,'DuckDB 合併 Parquet');self.ingest(books,mapping,signature)
            for fname,rid in mapping.items():
                row=next((r for r in books['BasicInfo'] if r.get('FILENAME')==fname),None)
                missing=[k for k in ('REPORT_DATE','TICKER','BROKER') if not row or row.get(k) in ('',None)]
                if not any(r.get('FILENAME')==fname for r in books['Summary']):missing.append('SUMMARY')
                if not any(r.get('FILENAME')==fname for r in books['FinancialData']):
                    if not row or 'NOT_APPLICABLE' not in str(row.get('STATUS','')):missing.append('FINANCIAL_DATA')
                self.receipts[rid]={'signature':signature,'extraction_signature':extraction_signature(self.root),'normalized_sha256':provenance[fname]['pdf_sha256'],'has_summary':any(s.get('FILENAME')==fname and all(s.get('POINT_'+str(i)) for i in range(1,5)) for s in books['Summary']),'missing':missing,'finance_verified':bool((proof.get('files',{}).get(fname) or {}).get('verified')),'evidence_signature':self.evidence_signature(),'report_identity':{'ticker':row.get('TICKER') if row else None,'broker':row.get('BROKER') if row else None,'report_date':row.get('REPORT_DATE') if row else None,'report':next((x.get('TITLE_ORIGINAL') or x.get('TITLE') for x in books['Summary'] if x.get('FILENAME')==fname),None)},'job':ident,'at':now()}
            atomic_json(self.home/'receipts.json',self.receipts)
            job.update(status='PARTIAL_INPUT_ERRORS' if job['conversion_errors'] or job['missing_output_reports'] else 'VERIFIED' if proof.get('verified') else 'EXTRACTED_UNVERIFIED',catalog=read_json(self.catalog,{}));self.set_progress(job,100,'本輪工作結束；'+('驗證通過' if proof.get('verified') else '尚有待驗證資料'),'GREEN' if proof.get('verified') and not job['conversion_errors'] else 'YELLOW')
        except Exception as exc:
            job.update(status='FAILED',error=str(exc));self.set_progress(job,job.get('progress',{}).get('percent',0),'執行失敗：'+str(exc),'RED')
        finally:
            with self.lock:job['ended']=now();atomic_json(folder/'job.json',job);self.current_job=None;self.event('JOB_FINISH',{'id':ident,'status':job['status']})
    @verb
    def page_data(self,page):
        if page=='overview':return self.status()
        if page in DATASETS+('Combined',):
            rows=[];offset=0
            while True:
                batch=self.table(page,offset);rows.extend(batch['rows']);offset+=batch['limit']
                if offset>=batch['total']:break
            return {'dataset':page,'total':len(rows),'rows':rows,'catalog':read_json(self.catalog,{})}
        if page in ('reconcile','ssot','parameters','engines','modules','definitions','environment','policies','archives','registry'):
            payload=self.review.page(page);rows=list(payload['rows']);offset=len(rows)
            while offset<payload['total']:
                rows.extend(self.review.page(page,offset)['rows']);offset=len(rows)
            payload['rows']=rows;return payload
        if page=='handover':return {'overview':self.status(),'policy':read_json(Path(__file__).with_name('VRN2_Policy_v0104.json'),{}),'review':{'probe':self.review.page('reconcile'),'inventory':self.review.inventory_cache,'reference':self.review.reference},'known_limits':['真機舊管理器鏈與 v1652 需另行實測','函式登記覆蓋不等於真實加速器與網路實測覆蓋','Parquet 仍受磁碟、記憶體與時間限制','Google Sheets 連線未啟用，不以 urllib 或 SDK 繞過鎖版網路工具']}
        raise ValueError('未知頁面')
    @verb
    def export(self,page,format):
        if format not in ('json','md','pdf','csv'):raise ValueError('不支援匯出格式')
        payload=self.page_data(page);folder=self.home/'exports';folder.mkdir(exist_ok=True);path=folder/(page+'_'+uuid.uuid4().hex[:8]+'.'+format)
        if format=='json':path.write_text(json.dumps(payload,ensure_ascii=False,allow_nan=False,indent=2,default=str),encoding='utf-8')
        elif format=='md':path.write_text('# VRN-2 '+page+'\n\n'+now()+'\n\n```json\n'+json.dumps(payload,ensure_ascii=False,indent=2,default=str)+'\n```\n',encoding='utf-8')
        elif format=='csv':
            if page not in DATASETS:raise ValueError('CSV 請選單一平面資料冊；整合資料使用 JSON/Parquet')
            rows=payload['rows'];cols=list(dict.fromkeys(k for r in rows for k in r));labels={}
            if page=='BasicInfo':
                spec=read_json(Path(__file__).with_name('VRN2_Policy_v0104.json'),{}).get('headers',[])
                cols=[h['key'] for h in spec];labels={h['key']:h['en'] for h in spec}
            with path.open('w',encoding='utf-8-sig',newline='') as f:
                writer=csv.writer(f);writer.writerow([labels.get(k,k) for k in cols])
                for row in rows:
                    writer.writerow([("'"+row[k] if isinstance(row.get(k),str) and row[k].startswith(('=','+','-','@')) else row.get(k)) for k in cols])
        else:
            from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer
            from reportlab.lib.styles import ParagraphStyle
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            if PDF_WINDOWS_FONT.is_file():
                font=TTFont('VRN2Unicode',str(PDF_WINDOWS_FONT),subfontIndex=0)
            else:
                import fitz
                font=TTFont('VRN2Unicode',io.BytesIO(fitz.Font('cjk').buffer))
            pdfmetrics.registerFont(font)
            style=ParagraphStyle('body',fontName='VRN2Unicode',fontSize=9,leading=13,wordWrap='CJK')
            story=[Paragraph('VRN-2 '+html.escape(page)+' / '+now(),style),Spacer(1,12)]
            for line in json.dumps(payload,ensure_ascii=False,indent=2,default=str).splitlines():
                # Split arbitrarily long values; no PDF row is silently omitted.
                for i in range(0,max(1,len(line)),100):story.append(Paragraph(html.escape(line[i:i+100]),style))
            SimpleDocTemplate(str(path),leftMargin=32,rightMargin=32,topMargin=32,bottomMargin=32).build(story)
        self.event('EXPORT',{'page':page,'format':format,'path':path.name});return path

# 5. HTTP Windows I/O. Loopback only; writes require a per-launch secret.



    @verb
    def set_progress(self,job,percent,label,lamp='YELLOW'):
        progress={'phase':job.get('status','RUNNING'),'percent':max(0,min(100,max(int(percent),int(job.get('progress',{}).get('percent',0))))),'label':label,'lamp':lamp,'updated':now(),'basis':'已完成的流程階段；擷取區間依實際 k/N 日誌'}
        job['progress']=progress;self.progress=progress
        if os.environ.get('VIA_VRN2_NATIVE_HOST')=='1':print('VRN2_JOB_PROGRESS '+json.dumps(dict(progress,job=job['id']),ensure_ascii=False),flush=True)
        atomic_json(self.home/'jobs'/job['id']/'job.json',job)
    @verb
    def run_process(self,command,env,log,job,timeout=MAX_JOB_SECONDS):
        import queue,re,signal
        process=subprocess.Popen(command,env=env,cwd=str(self.launcher.parent),stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace',bufsize=1,start_new_session=(os.name!='nt'))
        self._active_process=process
        lines=queue.Queue()
        def reader():
            for line in process.stdout:lines.put(line)
            lines.put(None)
        thread=threading.Thread(target=reader,daemon=True);thread.start();started=time.monotonic();last=started;ended=False
        try:
            if self._stop_event.is_set():raise InterruptedError('工作台已關閉')
            self.set_progress(job,25,'擷取／OCR 執行中（等待實際進度）')
            while not ended or process.poll() is None:
                try:
                    line=lines.get(timeout=.25)
                    if line is None:ended=True
                    else:
                        log.write(line);log.flush();last=time.monotonic()
                        match=re.search(r'\[(?:切|驗收)\]\s*(\d+)/(\d+)',line)
                        if match and int(match[2]):self.set_progress(job,25+int(45*int(match[1])/int(match[2])),line.strip()[:180])
                except queue.Empty:pass
                if self._stop_event.is_set():raise InterruptedError('工作台已關閉')
                if time.monotonic()-started>timeout:raise TimeoutError('單輪超過總時限')
                if time.monotonic()-last>20:
                    self.progress.update(label='引擎仍執行中；已等待 '+str(int(time.monotonic()-started))+' 秒，沒有虛增百分比',updated=now());last=time.monotonic()
            return subprocess.CompletedProcess(command,process.wait())
        except BaseException:
            if process.poll() is None:
                if os.name=='nt':subprocess.run(['taskkill','/PID',str(process.pid),'/T','/F'],capture_output=True)
                else:os.killpg(process.pid,signal.SIGTERM)
            raise
        finally:thread.join(timeout=2);process.stdout.close();self._active_process=None
    @verb
    def environment(self):
        if self.environment_cache is None:
            import importlib.metadata
            result=[]
            for module,package in [('duckdb','duckdb'),('pyarrow','pyarrow'),('pandas','pandas'),('fitz','PyMuPDF'),('reportlab','reportlab'),('webview','pywebview'),('lxml','lxml'),('yfinance','yfinance')]:
                present=importlib.util.find_spec(module) is not None
                try:version=importlib.metadata.version(package) if present else None
                except importlib.metadata.PackageNotFoundError:version='可定位模組；版本未登記'
                result.append({'component':package,'status':'GREEN' if present else 'RED','version':version,'evidence':'模組可定位；不等同全部功能實測' if present else '此 Python 環境未定位到模組'})
            result.append({'component':'Python ENV','status':'GREEN','version':sys.version.split()[0],'evidence':sys.executable})
            self.environment_cache=result
        rows=[dict(x) for x in self.environment_cache]
        rows.append({'component':'HTML ↔ Python bridge','status':'GREEN' if self.ui_ready else 'YELLOW','version':'WebView2 / JS API','evidence':'已收到 pywebviewready' if self.ui_ready else '等待桌面橋接握手'})
        template=self.root/'supportive modules'/'ps7'/'VeritasCeleritas.PS7.Template.ps1'
        rows.append({'component':'PS7 加速模板','status':'GREEN' if os.environ.get('VIA_VRN2_PS_TEMPLATE_LOADED')=='1' else 'YELLOW','version':template.name,'evidence':'PS 已載入模板' if os.environ.get('VIA_VRN2_PS_TEMPLATE_LOADED')=='1' else '未收到 PS 模板載入證據'})
        info=json.loads(os.environ.get('VIA_VRN2_PY_ACCEL_INFO') or '{}')
        rows.append({'component':'Python accelerator module','status':'GREEN' if info.get('status')=='LOADED' else 'YELLOW','version':info.get('version') or info.get('status') or '待載入','evidence':info.get('evidence') or '未收到載入證據'})
        rows.append({'component':'Per-verb acceleration','status':'YELLOW','version':'runtime evidence pending','evidence':'動詞插樁可觀測；未冒稱實際加速器 100% 執行'})
        return rows

    @verb
    def refresh_company_names(self):
        """Update official company prefixes in the lake without re-extracting PDF files."""
        import VRN2_CompanyMaster_v0100 as company
        records,errors=company.ensure(self.root,self.root/'VIA_Reports'/'vrn2'/'market'/'company_master')
        books={};mapping={}
        for ds in DATASETS:
            offset=0;items=[]
            while True:
                batch=self.table(ds,offset);items.extend(batch['rows']);offset+=batch['limit']
                if offset>=batch['total']:break
            books[ds]=items
            for row in items:mapping[row['FILENAME']]=row['REPORT_ID']
        issues=company.prefix_titles(books['BasicInfo'],books['Summary'],records)
        for row in books['BasicInfo']:
            if row.get('FILENAME') in issues:row['STATUS']='UNVERIFIED | '+str(row.get('STATUS') or '')+' | '+issues[row['FILENAME']]
        if books['BasicInfo']:self.ingest(books,mapping,component_signature(self.root))
        result={'updated':len(books['Summary'])-len(issues),'unverified':len(issues),'errors':errors}
        self.event('OFFICIAL_COMPANY_NAMES',result);return result
    @verb
    def import_existing(self):
        if read_json(self.catalog,{}).get('tables'):return {'status':'CACHE_PRESENT','message':'已有 Parquet 主庫，未重複匯入'}
        folder=self.root/'VIA_Reports'/'vrn2'/'output'
        books={ds:read_json(folder/('VRN2_'+ds+'_latest.json'),[]) for ds in DATASETS}
        if not books['BasicInfo']:return {'status':'NO_LEGACY_DATA','message':'沒有既有 JSON 輸出，等待匯入報告'}
        mapping={};unresolved=[];source=Path(os.environ.get('VIA_VRN_INPUT') or r'C:\測試樣本報告')
        for row in books['BasicInfo']:
            name=row.get('FILENAME');p=source/str(name)
            if p.is_file():mapping[name]=file_hash(p)
            else:
                mapping[name]='legacy-unverified-'+text_hash(name);unresolved.append(name)
                row['STATUS']='UNVERIFIED | 原始 PDF 指紋尚未核對 | '+str(row.get('STATUS') or '')
        self.ingest(books,mapping,component_signature(self.root))
        for row in books['BasicInfo']:
            rid=mapping[row['FILENAME']];receipt=self.receipts.setdefault(rid,{})
            receipt.update(signature=component_signature(self.root),extraction_signature=extraction_signature(self.root),finance_verified=False,reused_legacy_unverified=True,missing=[k for k in ('REPORT_DATE','TICKER','BROKER') if not row.get(k)],has_summary=any(s.get('FILENAME')==row['FILENAME'] and all(s.get('POINT_'+str(i)) for i in range(1,5)) for s in books['Summary']))
            if not any(s.get('FILENAME')==row['FILENAME'] for s in books['Summary']):receipt['missing'].append('SUMMARY')
            if not any(s.get('FILENAME')==row['FILENAME'] for s in books['FinancialData']) and 'NOT_APPLICABLE' not in str(row.get('STATUS')):receipt['missing'].append('FINANCIAL_DATA')
            receipt['report_identity']={'ticker':row.get('TICKER'),'broker':row.get('BROKER'),'report_date':row.get('REPORT_DATE'),'report':next((s.get('TITLE_ORIGINAL') or s.get('TITLE') for s in books['Summary'] if s.get('FILENAME')==row['FILENAME']),None)}
        atomic_json(self.home/'receipts.json',self.receipts)
        result={'status':'LEGACY_IMPORTED_UNVERIFIED','reports':len(books['BasicInfo']),'unresolved_source_files':unresolved,'message':'既有結果已匯入 Parquet；未重抽 PDF，未冒稱新政策驗收通過'}
        self.event('IMPORT_EXISTING_RESULTS',result);return result

    @verb
    def stop_worker(self):
        self._stop_event.set()
        process=self._active_process
        if process is not None and process.poll() is None:
            if os.name=='nt':subprocess.run(['taskkill','/PID',str(process.pid),'/T','/F'],capture_output=True)
            else:
                import signal
                os.killpg(process.pid,signal.SIGTERM)
            try:process.wait(timeout=10)
            except subprocess.TimeoutExpired:process.kill()
        thread=self._worker_thread
        if thread and thread is not threading.current_thread():thread.join(timeout=12)
        return {'stopped':process is not None,'worker_pending':bool(thread and thread.is_alive())}


    @verb
    def preserve_successful_fields(self,books,mapping,job):
        """Keep already-populated fields on same content; never replace a good summary on an OCR repair."""
        wanted=set(mapping.values());old={}
        for ds in ('BasicInfo','Summary'):
            rows=[];offset=0
            while True:
                batch=self.table(ds,offset);rows.extend(r for r in batch['rows'] if r.get('REPORT_ID') in wanted);offset+=batch['limit']
                if offset>=batch['total']:break
            old[ds]={r['REPORT_ID']:r for r in rows}
        tasks={item['sha256']:item['tasks'] for item in job['files']}
        job['preserved_summaries']=[]
        for ds in ('BasicInfo','Summary'):
            for i,row in enumerate(books[ds]):
                rid=mapping.get(row.get('FILENAME'));prior=old[ds].get(rid)
                if not prior:continue
                if ds=='Summary' and all(prior.get('POINT_'+str(n)) for n in range(1,5)) and not any('SUMMARY' in t for t in tasks.get(rid,[])):
                    preserved={k:v for k,v in prior.items() if not k.startswith('_')};preserved['FILENAME']=row['FILENAME'];books[ds][i]=preserved;job['preserved_summaries'].append(row['FILENAME'])
                elif ds=='BasicInfo':
                    for key,value in prior.items():
                        if not key.startswith('_') and key not in ('STATUS','RECENT_REPORT_PRE_EARNINGS_FLAG') and row.get(key) in ('',None) and value not in ('',None):row[key]=value
        return books

    @verb
    def import_source(self):
        from VRN2_Reconcile_v0100 import SOURCE_DIRECTORY,EXTENSIONS
        if self.current_job:raise ValueError('執行中；請待本輪結束後匯入')
        if not SOURCE_DIRECTORY.is_dir():raise FileNotFoundError(str(SOURCE_DIRECTORY))
        existing={(r.get('source_path'),r.get('source_size'),r.get('source_mtime_ns')) for r in self.files if not r['deleted']};added=0;skipped=0;errors=[]
        for path in sorted(SOURCE_DIRECTORY.rglob('*')):
            if not path.is_file() or path.is_symlink() or path.suffix.lower() not in EXTENSIONS:continue
            stat=path.stat();key=(str(path),stat.st_size,stat.st_mtime_ns)
            if key in existing:skipped+=1;continue
            try:
                record=self.import_paths([path])[0];record.update(source_path=str(path),source_size=stat.st_size,source_mtime_ns=stat.st_mtime_ns);self.save_inputs();added+=1
            except Exception as exc:errors.append({'file':str(path),'error':str(exc)})
        return {'added':added,'unchanged_skipped':skipped,'errors':errors,'message':f'已匯入 {added}、未變更略過 {skipped}；原檔保留'}


    @verb
    def start_content_repair(self):
        with self.lock:
            if self.current_job:raise ValueError('已有工作執行中')
            if self.review.progress['status']!='DONE':raise ValueError('請先完成唯讀內容層探測')
            missing=[name for name in ('duckdb','pyarrow') if importlib.util.find_spec(name) is None]
            if missing:raise ValueError('缺少資料庫套件：'+','.join(missing))
            from VRN2_ContentRepair_v0100 import repair
            ident=uuid.uuid4().hex;job={'id':ident,'kind':'CONTENT_SUPPLEMENT','status':'QUEUED','started':now()};self.jobs[ident]=job;self.current_job=ident;self._stop_event.clear()
            atomic_json(self.home/'jobs'/ident/'job.json',job)
            self._worker_thread=threading.Thread(target=repair,args=(self,ident),daemon=True);self._worker_thread.start();return job
