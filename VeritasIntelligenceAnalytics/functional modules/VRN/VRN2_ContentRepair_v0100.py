#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE]
# [VIA:ACCEL-BRIDGE:v0111]
"""All-page content supplement. Successful BasicInfo/financial/summary books are untouched."""
from __future__ import annotations
import importlib.util,json,os,sys,uuid
from pathlib import Path
from VRN2_Workbench_v0102 import verb,file_hash,read_json,atomic_json,now,text_hash
from VRN2_Reconcile_v0100 import probe
from VRN2_DocumentBridge_v0100 import normalize
PAGE_OCR_TIMEOUT=300

class IsolatedOCR:
    @verb
    def __init__(self,state,job,folder):self.state=state;self.job=job;self.folder=Path(folder)
    @verb
    def ocr_page(self,page,stem,pdf_path,pno):
        output=self.state.home/'jobs'/self.job['id']/('ocr_'+uuid.uuid4().hex+'.json')
        command=[sys.executable,'-X','utf8',str(Path(__file__).resolve()),'--ocr-page',str(pdf_path),str(pno),str(output),str(self.folder)]
        with (output.parent/'content_ocr.log').open('a',encoding='utf-8') as log:
            result=self.state.run_process(command,dict(os.environ),log,self.job,timeout=PAGE_OCR_TIMEOUT)
        if result.returncode:raise RuntimeError('隔離 OCR 子程序失敗；詳見 content_ocr.log')
        record=read_json(output,{})
        return record.get('zones',[]),record.get('evidence',{'status':'無 OCR 回覆'})

@verb
def ocr_environment(folder):
    home=Path(os.environ.get('VIA_ENVS_HOME') or Path.home()/'envs')/'vrn2_ocr'
    py=Path(os.environ.get('VIA_VRN2_OCR_PY') or home/('Scripts/python.exe' if os.name=='nt' else 'bin/python'))
    bridges=sorted(home.glob('VRN2_OCRBridge_v*.py'))+sorted(Path(folder).glob('VRN2_OCRBridge_v*.py'))
    bridge=Path(os.environ['VIA_VRN2_OCR_BRIDGE']) if os.environ.get('VIA_VRN2_OCR_BRIDGE') else bridges[-1] if bridges else None
    if py.is_file() and bridge and bridge.is_file():
        os.environ.update(VIA_VRN2_OCR_PY=str(py),VIA_VRN2_OCR_BRIDGE=str(bridge));return {'python':str(py),'bridge':str(bridge),'status':'LOCATED_NOT_MODEL_TESTED'}
    return {'status':'MISSING','reason':'未定位既有隔離 OCR Python／橋；不重新安裝或下載模型'}

@verb
def load_ocr_engine(folder):
    paths=sorted(Path(folder).glob('VRN_ENG397_P1Segment_v[0-9][0-9][0-9][0-9].py'))
    if not paths:raise FileNotFoundError('沒有既有 ENG397 OCR 介面')
    path=paths[-1];compile(path.read_text(encoding='utf-8-sig'),str(path),'exec')
    spec=importlib.util.spec_from_file_location('vrn2_content_ocr_'+file_hash(path)[:12],path);module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
    if not callable(vars(module).get('ocr_page')):raise RuntimeError('ENG397 沒有明確 ocr_page 介面；未探測猜測其他動詞')
    return module,path

@verb
def content_records(pdf,source_document,ocr_engine=None,stop=None):
    import fitz
    pdf=Path(pdf);pages=probe(pdf);rows=[];issues=[];ocr_doc=None
    try:
        with fitz.open(pdf) as doc:
            for info,page in zip(pages,doc):
                if stop and stop.is_set():raise InterruptedError('使用者已停止工作')
                pno=info['page']
                for n,block in enumerate(page.get_text('blocks'),1):
                    if len(block)>6 and block[6]==0:rows.append({'FILENAME':source_document,'PAGE':pno,'ZONE':'TEXT_'+str(n),'KIND':'TEXT_BLOCK','TEXT':block[4],'BBOX':list(block[:4]),'ENGINE':'PyMuPDF native','STATUS':'NATIVE_SOURCE_TEXT'})
                try:
                    tables=page.find_tables()
                    for n,table in enumerate(tables.tables,1):
                        for ri,values in enumerate(table.extract(),1):
                            rows.append({'FILENAME':source_document,'PAGE':pno,'ZONE':'TABLE_'+str(n),'ROW':ri,'KIND':'TABLE_ROW','CELLS':values,'BBOX':list(table.bbox),'ENGINE':'PyMuPDF native table','STATUS':'TABLE_STRUCTURE_UNVERIFIED'})
                except Exception as exc:issues.append({'page':pno,'kind':'TABLE_EXTRACTION_FAILED','reason':str(exc)})
                if info['content_probe']=='OCR_CANDIDATE':
                    if ocr_engine is None:issues.append({'page':pno,'kind':'OCR_PENDING','reason':'缺 OCR 引擎／隔離環境'});continue
                    if ocr_doc is None:
                        import pdfplumber
                        ocr_doc=pdfplumber.open(pdf)
                    zones,evidence=ocr_engine.ocr_page(ocr_doc.pages[pno-1],pdf.stem+'_p'+str(pno),pdf_path=pdf,pno=pno)
                    if not zones:issues.append({'page':pno,'kind':'OCR_PENDING','reason':evidence});continue
                    for n,zone in enumerate(zones,1):
                        for ri,record in enumerate(zone.get('records') or [],1):rows.append({'FILENAME':source_document,'PAGE':pno,'ZONE':'OCR_'+str(n),'ROW':ri,'KIND':'OCR_TEXT_BLOCK','TEXT':record.get('text'),'BBOX':zone.get('bbox'),'ENGINE':zone.get('engine'),'OCR_EVIDENCE':evidence,'STATUS':'OCR_PENDING_VISUAL_VERIFICATION'})
                        for ri,values in enumerate(zone.get('rows') or [],1):rows.append({'FILENAME':source_document,'PAGE':pno,'ZONE':'OCR_TABLE_'+str(n),'ROW':ri,'KIND':'OCR_TABLE_ROW','CELLS':values,'BBOX':zone.get('bbox'),'ENGINE':zone.get('engine'),'STATUS':'OCR_PENDING_VISUAL_VERIFICATION'})
        return rows,issues
    finally:
        if ocr_doc is not None:ocr_doc.close()

@verb
def repair(state,ident):
    job=state.jobs[ident];folder=state.home/'jobs'/ident;job.update(status='RUNNING',issues=[]);rows=[];mapping={};folder.mkdir(parents=True,exist_ok=True)
    try:
        modules=state.root/'functional modules'/'VRN';environment=ocr_environment(modules);engine=None
        engines=sorted(modules.glob('VRN_ENG397_P1Segment_v[0-9][0-9][0-9][0-9].py'));engine_sha=file_hash(engines[-1]) if engines else 'NO_ENGINE'
        raw_signature=text_hash([file_hash(__file__),file_hash(Path(__file__).with_name('VRN2_DocumentBridge_v0100.py')),engine_sha,{k:os.environ.get(k,v) for k,v in [('VIA_VRN2_OCR_LADDER','200,325p'),('VIA_VRN2_OCR_MIN_CONF','0.85'),('VIA_VRN2_OCR_MIN_CHARS','40')]}])
        if environment['status']!='MISSING':engine=IsolatedOCR(state,job,modules)
        os.environ.setdefault('VIA_VRN2_OCR_CACHE',str(state.root/'VIA_Reports'/'vrn2'/'ocr_cache'))
        ledger=read_json(state.home/'content_receipts.json',{});existing_path=read_json(state.catalog,{}).get('tables',{}).get('ContentData');existing_counts={}
        if existing_path and Path(existing_path).is_file():
            with state.connect() as con:existing_counts=dict(con.execute('SELECT REPORT_ID,count(*) FROM read_parquet(?) GROUP BY REPORT_ID',[existing_path]).fetchall())
        sources=list({r['sha256']:r for r in state.review.rows if r.get('sha256') and r.get('status')!='ERROR'}.values());job['source_count']=len(sources);job['cache_hits']=0
        for i,source in enumerate(sources,1):
            state.set_progress(job,5+int(80*(i-1)/max(1,len(sources))),'內容層 '+str(i)+'/'+str(len(sources))+' · '+source['source_document'])
            if state._stop_event.is_set():raise InterruptedError('工作台已關閉')
            rid=source['sha256'];name=source['source_document'];mapping[name]=rid;key=rid+'_'+raw_signature[:16]
            if file_hash(source['path'])!=rid:
                job['issues'].append({'source_document':name,'kind':'SOURCE_CHANGED','reason':'來源已變動，請重新探測'});continue
            if ledger.get(rid,{}).get('signature')==raw_signature and ledger[rid].get('complete') and existing_counts.get(rid,0)==ledger[rid].get('rows',-1):job['cache_hits']+=1;continue
            try:
                if file_hash(source['path'])!=rid:raise ValueError('來源已變動，請重新探測')
                cache=state.home/'content_work'/key;cache.mkdir(parents=True,exist_ok=True);pdf=cache/'source.pdf';provenance=read_json(cache/'provenance.json',{})
                if not pdf.is_file() or provenance.get('source_sha256')!=rid or file_hash(pdf)!=provenance.get('pdf_sha256'):
                    provenance=normalize(source['path'],pdf);atomic_json(cache/'provenance.json',provenance)
                found,issues=content_records(pdf,name,engine,state._stop_event)
                for row in found:row.update(SOURCE_DOCUMENT=name,SOURCE_SHA256=rid,NORMALIZED_PDF_SHA256=provenance['pdf_sha256'],CONVERSION_STATUS=provenance['status'])
                rows.extend(found);job['issues'].extend(dict(source_document=name,**issue) for issue in issues)
                atomic_json(cache/'ContentData.json',found);ledger[rid]={'signature':raw_signature,'complete':not issues,'rows':len(found),'at':now()}
            except Exception as exc:job['issues'].append({'source_document':name,'kind':'CONTENT_FAILED','reason':str(exc)})
        if rows:state.ingest({'ContentData':rows},mapping,raw_signature)
        atomic_json(state.home/'content_receipts.json',ledger);job.update(status='CONTENT_PARTIAL' if job['issues'] else 'CONTENT_EXTRACTED',rows=len(rows),ocr_environment=environment)
        state.set_progress(job,100,'內容層補件結束；原 BASIC INFO／FINANCIAL／SUMMARY 保留，OCR 原圖與數值驗證另列','YELLOW')
    except Exception as exc:job.update(status='FAILED',error=str(exc));state.set_progress(job,job.get('progress',{}).get('percent',0),str(exc),'RED')
    finally:
        with state.lock:
            job['ended']=now();atomic_json(folder/'job.json',job);state.current_job=None;state.event('CONTENT_REPAIR',{'id':ident,'status':job['status']})

@verb
def main(argv):
    import pdfplumber
    if len(argv)!=5 or argv[0]!='--ocr-page':raise ValueError('僅接受 --ocr-page PDF PAGE OUTPUT MODULE_FOLDER')
    _,pdf,pno,output,folder=argv
    engine,_=load_ocr_engine(folder)
    with pdfplumber.open(pdf) as document:zones,evidence=engine.ocr_page(document.pages[int(pno)-1],Path(pdf).stem+'_p'+pno,pdf_path=Path(pdf),pno=int(pno))
    atomic_json(output,{'zones':zones,'evidence':evidence})
    return 0

if __name__=='__main__':raise SystemExit(main(sys.argv[1:]))
