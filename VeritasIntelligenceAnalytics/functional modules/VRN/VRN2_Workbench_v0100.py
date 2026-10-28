#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111] 動詞登記、耗時稽核及可驗證外掛；不冒稱已連到 Celeritas。
"""Windows/local VRN-2 workbench. JSON exchange, versioned Parquet lake, DuckDB merge."""
from __future__ import annotations
import argparse, ast, csv, datetime as dt, functools, hashlib, html, http.server, importlib.util, io, json, math, os, secrets, shutil, subprocess, sys, threading, time, urllib.parse, uuid, webbrowser
from pathlib import Path

# 1. Configuration and contracts
VERSION='v0100'
HOST='127.0.0.1'
CHUNK_BYTES=1024*1024
PAGE_SIZE=100
MEMORY_LIMIT='512MB'
THREADS=min(4,os.cpu_count() or 1)
MAX_JSON_BYTES=2*1024*1024
REPORT_EXTENSIONS={'.pdf','.docx','.txt','.png','.jpg','.jpeg','.tif','.tiff'}
DATASETS=('BasicInfo','FinancialData','Summary')
MAX_JOB_SECONDS=14400
PDF_WINDOWS_FONT=Path(os.environ.get('WINDIR','C:/Windows'))/'Fonts'/'msjh.ttc'
TZ=dt.timezone(dt.timedelta(hours=8))
POLICY_VERSION='VRN2_POLICY_v0102'
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
            state=getattr(owner,'state',None) or getattr(getattr(owner,'server',None),'state',None) or (owner if isinstance(owner,State) else None)
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
        self.current_job=None;self.token=secrets.token_urlsafe(32)
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
        active=[dict(r) for r in self.files if not r['deleted']];by_meta={};by_hash={}
        for r in active:
            key=(r['modified_ms'],r['format'],r['size']);by_meta.setdefault(key,[]).append(r['id']);by_hash.setdefault(r['sha256'],[]).append(r['id'])
        for r in active:
            key=(r['modified_ms'],r['format'],r['size']);r['candidate_group']=text_hash(key)[:12] if len(by_meta[key])>1 else ''
            r['exact_group']=r['sha256'][:12] if len(by_hash[r['sha256']])>1 else ''
        return sorted(active,key=lambda r:(r['candidate_group'] or '~'+r['id'],r['name']))
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
                    parts=[rid] if dataset!='FinancialData' else [rid]+[str(r.get(k) or '') for k in ('ITEM','PERIOD_STD','REPORT_SCOPE','UNIT','PAGE','ZONE')]
                    r['_ROW_KEY']=text_hash(parts)
                    content={k:v for k,v in r.items() if k!='_UPDATED_AT'}
                    if r['_ROW_KEY'] in seen and seen[r['_ROW_KEY']]!=content:raise ValueError('同主鍵多個數值，停止合併並保留原資料庫')
                    seen[r['_ROW_KEY']]=content;rows.append(r)
                if not rows:
                    if dataset in cat['tables']:paths[dataset]=cat['tables'][dataset]
                    continue
                columns=list(dict.fromkeys(k for r in rows for k in r))
                if dataset=='BasicInfo':
                    spec=read_json(Path(__file__).with_name('VRN2_Policy_v0102.json'),{}).get('headers',[])
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
                        spec=read_json(Path(__file__).with_name('VRN2_Policy_v0102.json'),{}).get('headers',[]);keys=[h['key'] for h in spec];tails=['RECENT_REPORT_PRE_EARNINGS_FLAG','STATUS']
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
            if not documents or documents[0].get('pdf_sha256')!=rid or len([q for q in quotes if q.get('verbatim') and q.get('quote_sha256')==hashlib.sha256(str(q.get('text') or '').encode('utf-8')).hexdigest() and (q.get('reader')!='OCR' or q.get('visual_verified') is True)])<4:
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
            if r['format']!='pdf':tasks=['UNSUPPORTED:本成功基線僅驗收 PDF，其他格式保留待轉換']
            elif not receipt or receipt.get('signature')!=signature:tasks=['EXTRACT','VALIDATE','MERGE']
            elif receipt.get('missing'):tasks=['REPAIR_FIELDS:'+','.join(receipt['missing']),'VALIDATE','MERGE']
            elif not receipt.get('finance_verified'):tasks=['AUDIT_ONLY:官方資料/調整基準缺證據，不重抽 PDF']
            else:tasks=['CACHE_HIT']
            items.append({'id':r['id'],'sha256':r['sha256'],'name':r['name'],'tasks':tasks})
        unique={}
        for item in items:unique.setdefault(item['sha256'],item)
        return {'signature':signature,'policy':POLICY_VERSION,'items':items,'unique':list(unique.values()),'extraction_count':sum(any(t.startswith(('EXTRACT','REPAIR_FIELDS')) for t in r['tasks']) for r in unique.values()),'audit_only_count':sum(any(t.startswith('AUDIT_ONLY') for t in r['tasks']) for r in unique.values())}
    @verb
    def engines(self):
        modules=self.root/'functional modules'/'VRN';result=[]
        for family,inp,output in (('VRN_ENG397','PDF','JSON 分區/表格'),('VRN_ENG062','原文 JSON','四點原文 JSON'),('VRN2_MarketFetch','缺漏清單','官方資料及調整價 JSON'),('VRN_SystemManager','擷取結果 JSON','驗證資料冊 JSON'),('VRN2_FinanceContract','報告/官方 JSON','財務核對 JSON')):
            hits=sorted(modules.glob(family+'*_v*.py'));p=hits[-1] if hits else None
            result.append({'family':family,'version':p.name if p else None,'input':inp,'production':'由本輪工作日誌判定；存在不代表成功','output':output,'spec':'JSON / '+POLICY_VERSION,'status':'AVAILABLE_NOT_EXECUTED' if p else 'MISSING','hash':file_hash(p) if p else None})
        result.append({'family':'DuckDB / Parquet','status':'READY' if all(importlib.util.find_spec(n) for n in ('duckdb','pyarrow')) else 'MISSING_DEPENDENCY','input':'已驗證與待驗證分級 JSON','production':'主鍵合併 / 官方值優先 / 原子 catalog','output':'Parquet','spec':'UTF-8 metadata; numeric float64'})
        return result
    @verb
    def status(self):
        with self.lock:return {'version':VERSION,'root':str(self.root),'files':self.groups(),'recycle':[{'id':r['id'],'name':r['name']} for r in self.files if r['deleted']],'plan':self.plan(),'engines':self.engines(),'coverage':scan_coverage(__file__),'metrics':dict(self.metrics),'catalog':read_json(self.catalog,{}),'jobs':list(self.jobs.values()),'gates':read_json(self.home/'gates.json',{g:{'state':'UNCONFIGURED','reason':'需提供已註冊之本機入口，未猜測連結'} for g in DB_GATES})}

# 4. Focused jobs. The successful extractor stays external and unchanged.
    @verb
    def start_job(self):
        with self.lock:
            missing=[name for name in ('duckdb','pyarrow') if importlib.util.find_spec(name) is None]
            if missing:
                atomic_json(self.home/'VRN2_ENV_REQUEST.json',{'packages':missing,'owner':'VCGC'})
                raise ValueError('缺套件，已建立 VCGC 請求：'+','.join(missing))
            if self.current_job:raise ValueError('已有工作執行中')
            plan=self.plan();unsupported=[i for i in plan['items'] if i['tasks'][0].startswith('UNSUPPORTED')]
            if unsupported:raise ValueError('已匯入非 PDF；本基線尚無已驗收轉換器，請先移除這些匯入副本或轉為 PDF')
            selected=[r for r in plan['unique'] if any(t.startswith(('EXTRACT','REPAIR_FIELDS')) for t in r['tasks'])]
            if not selected:
                changed=[r for r in plan['unique'] if any(t.startswith('AUDIT_ONLY') for t in r['tasks']) and self.receipts.get(r['sha256'],{}).get('evidence_signature')!=self.evidence_signature()]
                if changed:return self.audit_existing(changed)
                return {'status':'WAITING_EVIDENCE' if plan['audit_only_count'] else 'CACHE_HIT','plan':plan,'message':'未重抽 PDF；待官方補件/資料政策修復' if plan['audit_only_count'] else '資料庫已有相同內容與版本的資料'}
            ident=uuid.uuid4().hex;job={'id':ident,'status':'QUEUED','started':now(),'plan':plan,'files':selected};self.jobs[ident]=job;self.current_job=ident
            folder=self.home/'jobs'/ident;folder.mkdir(parents=True);atomic_json(folder/'job.json',job)
            thread=threading.Thread(target=self.run_job,args=(ident,),daemon=True);thread.start();return job
    @verb
    def run_job(self,ident):
        job=self.jobs[ident];folder=self.home/'jobs'/ident;outputs=folder/'outputs';stage=folder/'input';stage.mkdir()
        try:
            job['status']='RUNNING';atomic_json(folder/'job.json',job);mapping={};seen=set()
            for item in job['files']:
                record=next(r for r in self.files if r['id']==item['id']);source=Path(record['path'])
                if file_hash(source)!=item['sha256']:raise ValueError('輸入內容已變更')
                name=source.name
                if name.casefold() in seen:name=source.stem+'_'+item['sha256'][:12]+source.suffix
                seen.add(name.casefold());shutil.copy2(source,stage/name);mapping[name]=item['sha256']
            atomic_json(folder/'report_ids.json',mapping)
            # Focused market input only; avoid old BasicInfo including unrelated reports.
            old=read_json(self.root/'VIA_Reports'/'vrn2'/'output'/'VRN2_BasicInfo_latest.json',[])
            focus=[r for r in old if r.get('FILENAME') in mapping];atomic_json(folder/'focus_basic.json',focus)
            env=dict(os.environ,VIA_ROOT=str(self.root),VIA_VRN_INPUT=str(stage),VIA_VRN2_JOB_OUTPUT=str(outputs),VIA_VRN2_MARKET_HOME=str(self.root/'VIA_Reports'/'vrn2'/'market'),VIA_VRN2_NO_PUSH='1',VIA_NO_OPEN='1',PYTHONUTF8='1',PYTHONIOENCODING='utf-8')
            command=[sys.executable,'-X','utf8',str(self.launcher),'--focused-run','--focus-basic',str(folder/'focus_basic.json')]
            with (folder/'process.log').open('w',encoding='utf-8') as log:
                result=subprocess.run(command,env=env,cwd=str(self.launcher.parent),stdout=log,stderr=subprocess.STDOUT,timeout=MAX_JOB_SECONDS)
            if result.returncode:raise RuntimeError('擷取程序 exit '+str(result.returncode)+'；詳見本輪日誌')
            books={d:read_json(outputs/'output'/('VRN2_'+d+'_latest.json'),[]) for d in DATASETS}
            if not books['BasicInfo']:raise RuntimeError('本輪沒有 BasicInfo，拒絕沿用舊輸出')
            observed={r.get('FILENAME') for r in books['BasicInfo']}
            if not observed.issubset(mapping):raise RuntimeError('原管理器未遵守本輪範圍；不合併非本輪資料')
            proof=read_json(outputs/'output'/'VRN2_FinanceValidation_latest.json',{})
            signature=component_signature(self.root);self.ingest(books,mapping,signature)
            for fname,rid in mapping.items():
                row=next((r for r in books['BasicInfo'] if r.get('FILENAME')==fname),None)
                missing=[k for k in ('REPORT_DATE','TICKER','BROKER') if not row or row.get(k) in ('',None)]
                if not any(r.get('FILENAME')==fname for r in books['Summary']):missing.append('SUMMARY')
                if not any(r.get('FILENAME')==fname for r in books['FinancialData']):
                    if not row or 'NOT_APPLICABLE' not in str(row.get('STATUS','')):missing.append('FINANCIAL_DATA')
                self.receipts[rid]={'signature':signature,'missing':missing,'finance_verified':bool((proof.get('files',{}).get(fname) or {}).get('verified')),'evidence_signature':self.evidence_signature(),'job':ident,'at':now()}
            atomic_json(self.home/'receipts.json',self.receipts)
            job.update(status='VERIFIED' if proof.get('verified') else 'EXTRACTED_UNVERIFIED',catalog=read_json(self.catalog,{}))
        except Exception as exc:job.update(status='FAILED',error=str(exc))
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
        if page=='handover':return {'overview':self.status(),'policy':read_json(Path(__file__).with_name('VRN2_Policy_v0102.json'),{}),'known_limits':['真機舊管理器鏈與 v1652 需另行實測','函式登記覆蓋不等於真實加速器與網路實測覆蓋','Parquet 仍受磁碟、記憶體與時間限制','Google Sheets 連線未啟用，不以 urllib 或 SDK 繞過鎖版網路工具']}
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
                spec=read_json(Path(__file__).with_name('VRN2_Policy_v0102.json'),{}).get('headers',[])
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
class Handler(http.server.BaseHTTPRequestHandler):
    @verb
    def log_message(self,*args):pass
    @verb
    def authorized(self):
        parsed=urllib.parse.urlsplit(self.path);query=urllib.parse.parse_qs(parsed.query)
        token=self.headers.get('X-VRN-Token') or query.get('token',[''])[0]
        return secrets.compare_digest(token,self.server.state.token)
    @verb
    def send(self,status,body,mime='application/json; charset=utf-8'):
        if not isinstance(body,bytes):body=(safe_json(body) if not isinstance(body,str) else body).encode('utf-8')
        self.send_response(status);self.send_header('Content-Type',mime);self.send_header('Content-Length',str(len(body)));self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.send_header('Referrer-Policy','no-referrer');self.end_headers();self.wfile.write(body)
    @verb
    def do_GET(self):
        if not self.authorized():return self.send(403,{'error':'未授權'})
        parsed=urllib.parse.urlsplit(self.path);query=urllib.parse.parse_qs(parsed.query);state=self.server.state
        try:
            if parsed.path=='/':
                template=Path(__file__).with_name('VRN2_Workbench_UI_v0100.html').read_text(encoding='utf-8');return self.send(200,template.replace('__BOOT__',safe_json({'token':state.token,'demo':False}).replace('<','\\u003c')),'text/html; charset=utf-8')
            if parsed.path=='/api/status':return self.send(200,state.status())
            if parsed.path=='/api/table':return self.send(200,state.table(query.get('dataset',['BasicInfo'])[0],int(query.get('offset',['0'])[0])))
            if parsed.path=='/api/export':
                file=state.export(query.get('page',['overview'])[0],query.get('format',['json'])[0]);return self.send(200,file.read_bytes(),{'.pdf':'application/pdf','.json':'application/json; charset=utf-8','.md':'text/markdown; charset=utf-8','.csv':'text/csv; charset=utf-8'}[file.suffix])
            self.send(404,{'error':'未知路徑'})
        except Exception as exc:self.send(400,{'error':str(exc)})
    @verb
    def do_POST(self):
        state=self.server.state;origin=self.headers.get('Origin');base='http://'+HOST+':'+str(self.server.server_port)
        if not self.authorized() or origin not in (None,base):return self.send(403,{'error':'未授權的來源'})
        try:
            parsed=urllib.parse.urlsplit(self.path);size=int(self.headers.get('Content-Length','0'))
            if parsed.path=='/api/upload':
                query=urllib.parse.parse_qs(parsed.query);free=shutil.disk_usage(state.home).free
                if size<0 or size+CHUNK_BYTES>free:raise ValueError('磁碟容量不足或容量無效')
                return self.send(200,state.import_stream(query.get('name',[''])[0],query.get('modified',['0'])[0],self.rfile,size))
            if size<0 or size>MAX_JSON_BYTES:raise ValueError('JSON 命令過大')
            command=json.loads(self.rfile.read(size).decode('utf-8')) if size else {}
            if parsed.path=='/api/delete/preview':result=state.delete_preview(command.get('ids',[]))
            elif parsed.path=='/api/delete/confirm':result=state.delete_confirm(command.get('ticket',''))
            elif parsed.path=='/api/restore':result=state.restore(command.get('ids',[]))
            elif parsed.path=='/api/start':result=state.start_job()
            elif parsed.path=='/api/pick':
                # A fresh child owns Tk's UI thread. Paths are never accepted from the web page.
                run=subprocess.run([sys.executable,'-X','utf8',str(Path(__file__).resolve()),'--native-pick'],capture_output=True,text=True,encoding='utf-8',timeout=600)
                if run.returncode:raise RuntimeError('Windows 選檔未完成：'+run.stderr[-500:])
                result=state.import_paths(json.loads(run.stdout))
            elif parsed.path=='/api/gate':
                gates=read_json(state.home/'gates.json',{});entry=gates.get(command.get('name'),{})
                if entry.get('state')!='REGISTERED' or not entry.get('command'):raise ValueError('系統 Gate 尚未註冊；不猜測或執行任意命令')
                # Commands must be an administrator/user supplied list in the local config, never from HTTP input.
                cmd=entry['command']
                if not isinstance(cmd,list) or not cmd or not Path(cmd[0]).is_file():raise ValueError('Gate 程式不存在')
                subprocess.Popen(cmd,cwd=str(state.root));result={'started':command['name']}
            else:return self.send(404,{'error':'未知動作'})
            self.send(200,result)
        except Exception as exc:self.send(400,{'error':str(exc)})

@verb
def main(argv=None):
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path);parser.add_argument('--launcher',type=Path);parser.add_argument('--home',type=Path);parser.add_argument('--no-open',action='store_true');parser.add_argument('--native-pick',action='store_true');args=parser.parse_args(argv)
    if args.native_pick:
        import tkinter as tk
        from tkinter import filedialog
        app=tk.Tk();app.withdraw()
        paths=filedialog.askopenfilenames(title='選擇 VRN-2 報告',filetypes=[('Reports','*.pdf *.docx *.txt *.png *.jpg *.jpeg *.tif *.tiff')]);app.destroy();print(json.dumps(paths,ensure_ascii=False));return 0
    if not args.root or not args.launcher:parser.error('--root and --launcher required')
    home=Path(args.home or args.root/'VIA_Reports'/'vrn2'/'workbench');home.mkdir(parents=True,exist_ok=True)
    # Prevent two independent writers or job schedulers from owning the same lake.
    lock=home/'session.lock'
    fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY);os.write(fd,str(os.getpid()).encode());os.close(fd)
    try:
        state=State(args.root,args.launcher,home)
        server=http.server.ThreadingHTTPServer((HOST,0),Handler);server.state=state
        url=f'http://{HOST}:{server.server_port}/?token={state.token}'
        print('[U/I] '+url,flush=True);print('VRN-2 工作台執行中；關閉此視窗後服務停止。',flush=True)
        if not args.no_open:webbrowser.open(url)
        server.serve_forever()
    except KeyboardInterrupt:return 0
    finally:lock.unlink(missing_ok=True)

if __name__=='__main__':raise SystemExit(main())
