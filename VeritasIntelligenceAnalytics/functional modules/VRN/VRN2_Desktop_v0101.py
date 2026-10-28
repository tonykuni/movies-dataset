#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE]
# [VIA:ACCEL-BRIDGE:v0111] 本機 WebView2 JS API；不開啟 HTTP socket。
"""Native serverless host for VRN-2. HTML is passed in memory, never as a local URL."""
from __future__ import annotations
import argparse,base64,contextlib,hashlib,io,json,os,shutil,subprocess,sys,threading,uuid
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from VRN2_Workbench_v0102 import State,verb,read_json,atomic_json,now,CHUNK_BYTES
VERSION='v0101'
HTML_NAME='VRN2_UI_Preview_v0150.htm'
WINDOW_TITLE='VRN-2｜VRN2_UI_Preview_v0150.htm｜NON-SERVER'
WIDTH=1440
HEIGHT=920
UPLOAD_CHUNK=256*1024
MAX_UPLOADS=32

@verb
def legacy_session_active(home):
    path=Path(home)/'session.lock'
    if not path.is_file():return False
    try:pid=int(path.read_text().strip())
    except (ValueError,OSError):return True
    if pid<=0:return True
    if os.name=='nt':
        import ctypes
        from ctypes import wintypes
        kernel=ctypes.WinDLL('kernel32',use_last_error=True)
        kernel.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];kernel.OpenProcess.restype=wintypes.HANDLE
        kernel.GetExitCodeProcess.argtypes=[wintypes.HANDLE,ctypes.POINTER(wintypes.DWORD)];kernel.GetExitCodeProcess.restype=wintypes.BOOL
        kernel.CloseHandle.argtypes=[wintypes.HANDLE];kernel.CloseHandle.restype=wintypes.BOOL
        handle=kernel.OpenProcess(0x1000,False,pid)
        if not handle:return ctypes.get_last_error()==5
        code=wintypes.DWORD()
        try:return bool(kernel.GetExitCodeProcess(handle,ctypes.byref(code))) and code.value==259
        finally:kernel.CloseHandle(handle)
    try:os.kill(pid,0);return True
    except ProcessLookupError:return False
    except PermissionError:return True

@contextlib.contextmanager
@verb
def exclusive_session(home):
    home=Path(home);home.mkdir(parents=True,exist_ok=True)
    stream=(home/'desktop_session.lock').open('a+b')
    try:
        stream.seek(0)
        if os.name=='nt':
            import msvcrt
            if not stream.read(1):stream.write(b'0');stream.flush()
            stream.seek(0);msvcrt.locking(stream.fileno(),msvcrt.LK_NBLCK,1)
        else:
            import fcntl
            fcntl.flock(stream.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        yield
    finally:stream.close() # OS releases the lock after normal exit OR a crashed process.

class NativeApi:
    @verb
    def __init__(self,state):self._state=state;self._uploads={};self._upload_lock=threading.RLock();self._window=None
    @verb
    def get_state(self):return self._state.status()
    @verb
    def ready(self):
        self._state.ui_ready=True
        atomic_json(self._state.home/'VRN2_Desktop_Startup.json',{'at':now(),'status':'UI_READY','transport':'NO_HTTP','environment':self._state.environment()})
        print('VRN2_UI_READY '+json.dumps({'percent':100,'transport':'NATIVE_JS_API_NO_HTTP','html':HTML_NAME},ensure_ascii=False),flush=True)
        return {'ready':True,'transport':'NATIVE_JS_API_NO_HTTP'}
    @verb
    def begin_upload(self,name,modified,size):
        size=int(size)
        if size<0 or size+CHUNK_BYTES>shutil.disk_usage(self._state.home).free:raise ValueError('容量無效或磁碟空間不足')
        with self._upload_lock:
            if len(self._uploads)>=MAX_UPLOADS:raise ValueError('同時未完成匯入過多')
            ident=uuid.uuid4().hex;folder=self._state.home/'upload_temp';folder.mkdir(exist_ok=True);path=folder/(ident+'.part')
            self._uploads[ident]={'name':name,'modified':modified,'size':size,'received':0,'path':path,'stream':path.open('xb')}
        return {'id':ident,'chunk_size':UPLOAD_CHUNK}
    @verb
    def write_upload(self,ident,encoded,offset):
        if len(encoded)>4*((UPLOAD_CHUNK+2)//3)+4:raise ValueError('單次匯入區塊過大')
        data=base64.b64decode(encoded,validate=True)
        with self._upload_lock:
            item=self._uploads[ident]
            if int(offset)!=item['received'] or item['received']+len(data)>item['size']:raise ValueError('匯入區塊順序或容量錯誤')
            item['stream'].write(data);item['received']+=len(data)
            return {'received':item['received'],'percent':100*item['received']/max(1,item['size'])}
    @verb
    def finish_upload(self,ident):
        with self._upload_lock:
            item=self._uploads.pop(ident);item['stream'].close()
        try:
            if item['received']!=item['size']:raise ValueError('檔案未完整傳入')
            with item['path'].open('rb') as source:return self._state.import_stream(item['name'],item['modified'],source,item['size'])
        finally:item['path'].unlink(missing_ok=True)
    @verb
    def abort_upload(self,ident):
        with self._upload_lock:item=self._uploads.pop(ident,None)
        if item:item['stream'].close();item['path'].unlink(missing_ok=True)
        return {'aborted':bool(item)}
    @verb
    def close_uploads(self):
        for ident in list(self._uploads):self.abort_upload(ident)
    @verb
    def invoke(self,action,body=None):
        body=body or {};state=self._state
        if action=='status':return state.status()
        if action=='review':return state.review.page(body.get('dataset','reconcile'),body.get('offset',0))
        if action=='repair_content':return state.start_content_repair()
        if action=='probe':return state.review.begin()
        if action=='import_source':return state.import_source()
        if action=='reference':return state.review.reference_html(body.get('path',''))
        if action=='pick_reference':
            if not self._window:raise RuntimeError('桌面視窗尚未就緒')
            import webview
            kinds=getattr(webview,'FileDialog',None);kind=kinds.OPEN if kinds else webview.OPEN_DIALOG
            paths=self._window.create_file_dialog(kind,allow_multiple=False,file_types=('HTML (*.html;*.htm)',))
            if not paths:return {'cancelled':True}
            candidate=Path(paths[0]);allowed=(state.root/'VIA_Reports').resolve()
            if not candidate.resolve().is_relative_to(allowed):
                # Explicit picker authorizes this one local visual reference; do not expand other read roots.
                text=candidate.read_text(encoding='utf-8-sig');state.review.reference={'path':str(candidate),'sha256':hashlib.sha256(candidate.read_bytes()).hexdigest(),'mode':'USER_SELECTED_READ_ONLY_VISUAL_REFERENCE'}
                return {'html':text,'reference':state.review.reference}
            return state.review.reference_html(paths[0])
        if action=='table':return state.table(body.get('dataset','BasicInfo'),body.get('offset',0))
        if action=='delete_preview':return state.delete_preview(body.get('ids',[]))
        if action=='delete_confirm':return state.delete_confirm(body.get('ticket',''))
        if action=='restore':return state.restore(body.get('ids',[]))
        if action=='start':return state.start_job()
        if action=='pick':
            if not self._window:raise RuntimeError('桌面視窗尚未就緒')
            import webview
            kinds=getattr(webview,'FileDialog',None)
            kind=kinds.OPEN if kinds else webview.OPEN_DIALOG
            paths=self._window.create_file_dialog(kind,allow_multiple=True,file_types=('Reports (*.pdf;*.doc;*.docx;*.txt;*.png;*.jpg;*.jpeg;*.tif;*.tiff;*.bmp;*.webp;*.gif)',))
            return state.import_paths(paths or [])
        if action=='export':
            path=state.export(body.get('page','overview'),body.get('format','json'))
            if os.name=='nt':os.startfile(str(path.parent))
            return {'path':str(path),'message':'匯出完成：'+str(path)}
        if action=='gate':
            entry=read_json(state.home/'gates.json',{}).get(body.get('name'),{})
            command=entry.get('command')
            if entry.get('state')!='REGISTERED' or not isinstance(command,list) or not command or not Path(command[0]).is_file():raise ValueError('尚未註冊可用 Gate')
            subprocess.Popen(command,cwd=str(state.root));return {'started':body.get('name')}
        if action=='names':return state.refresh_company_names()
        if action=='import_existing':return state.import_existing()
        if action=='handover':return state.page_data('handover')
        raise ValueError('未知桌面動作')

@verb
def build_page(state):
    template=(HERE/HTML_NAME).read_text(encoding='utf-8')
    return template.replace('__BOOT__',json.dumps({'demo':False,'native':True,'sample':None,'headers':read_json(HERE/'VRN2_Policy_v0104.json',{}).get('headers',[])},ensure_ascii=False).replace('<','\\u003c'),1)

@verb
def main(argv=None):
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,required=True);parser.add_argument('--launcher',type=Path,required=True);args=parser.parse_args(argv)
    home=args.root/'VIA_Reports'/'vrn2'/'workbench'
    # Explicit user launch overrides the stale NO_OPEN flag; extraction workers set it separately.
    os.environ.pop('VIA_NO_OPEN',None)
    os.environ['VIA_VRN2_NATIVE_HOST']='1'
    if legacy_session_active(home):raise RuntimeError('舊版 v0148 程序仍在執行或鎖無法確認；請先在舊 PowerShell 按 Ctrl+C，避免兩個版本同時更新資料庫')
    with exclusive_session(home):
        state=State(args.root,args.launcher,home);api=NativeApi(state)
        atomic_json(home/'VRN2_Desktop_Startup.json',{'at':now(),'status':'STARTING','transport':'NO_HTTP','python':sys.executable,'environment':state.environment()})
        try:
            import webview
            window=webview.create_window(WINDOW_TITLE,html=build_page(state),js_api=api,width=WIDTH,height=HEIGHT,min_size=(820,620),text_select=True)
            api._window=window
            print('[U/I] '+str(HERE/HTML_NAME)+' · WebView2 / NON-SERVER',flush=True)
            print('VRN2_STARTUP '+json.dumps({'percent':75,'stage':'WebView2 載入 HTML，等待橋接握手'},ensure_ascii=False),flush=True)
            webview.start(gui='edgechromium' if os.name=='nt' else None,http_server=False,private_mode=True,debug=False)
            if not state.ui_ready:raise RuntimeError('視窗已結束，但沒有收到 HTML/Python 就緒握手')
        except Exception as exc:
            atomic_json(home/'VRN2_Desktop_Startup.json',{'at':now(),'status':'FAILED','error':str(exc),'environment':state.environment()})
            print('[RED] 桌面啟動失敗：'+str(exc)+'；請檢查本輪 Startup JSON。未退回 HTTP 服務。',flush=True)
            raise
        finally:state.stop_worker();api.close_uploads()
    return 0

if __name__=='__main__':raise SystemExit(main())
