#!/usr/bin/env python3
"""Exercise the known local TokenEngine; no installation, upstream, or SSOT writes."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ENGINE_SHA='ca3c38ee00d2d7df5af71bcaea59ab7e7c73a15ec1d1f7b03218127efaf62af5'


def run(root):
    engine=root/'engines/tooling/via_agent_os_unified_readonly_hardened.py'
    if engine.is_symlink() or hashlib.sha256(engine.read_bytes()).hexdigest()!=ENGINE_SHA:
        raise ValueError('STOP_SOURCE_INTEGRITY')
    rows=[]
    env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONIOENCODING='utf-8')
    def command(name,args,data='',checks=None):
        started=time.perf_counter()
        proc=subprocess.run([sys.executable,'-B',str(engine),*args],input=data,text=True,encoding='utf-8',capture_output=True,env=env,timeout=30,cwd=root)
        duration=time.perf_counter()-started
        out=json.loads(proc.stdout)
        if proc.returncode!=0 or checks and not checks(out):raise ValueError('FAILED '+name)
        summary={k:v for k,v in out.items() if k!='prepared_text'}
        row={'name':name,'system':'VCGC','status':'PASS / LOCAL FIXTURE','argv':['python','-B','engines/tooling/'+engine.name,*args],'duration_seconds':round(duration,6),'actual_exit':proc.returncode,'result':summary}
        rows.append(row)
        return out
    command('Agent OS selftest',['selftest'],checks=lambda x:x.get('tests_run')==48 and x.get('failures')==0 and x.get('errors')==0)
    command('8 Skills acceptance',['skills','test'],checks=lambda x:x.get('status')=='PASS')
    sample={'systems':['VCGC','VDF','VRN','VQG','VAP','Database'],'policy':'independent peers','contracts':[{'from':'VDF','to':'VQG','enabled':False} for _ in range(20)]}
    payload=json.dumps(sample,ensure_ascii=False,indent=4)
    compact=command('JSON semantic compact',['context','--include-text'],payload,lambda x:x.get('mode')=='json_lossless_semantic_compact' and x.get('lossy') is False and json.loads(x['prepared_text'])==sample)
    passthrough='VIA：既有VCGC工具保留；各系統独立，metadata只讀。'
    command('CJK lossless passthrough',['context','--include-text'],passthrough,lambda x:x['prepared_text']==passthrough and x['tokens_before_est']==x['tokens_after_est'] and x['lossy'] is False)
    lines=['ordinary fixture record '+str(i) for i in range(500)]
    lines[210]='VQG source binding fixture-only proof'
    query=command('Opt-in query extraction',['context','--allow-lossy','--query','VQG binding','--max-lines','20','--include-text'],'\n'.join(lines),lambda x:x.get('lossy') is True and '[L211]' in x['prepared_text'] and len(x['prepared_text'].splitlines())<=20)
    if hashlib.sha256(engine.read_bytes()).hexdigest()!=ENGINE_SHA:raise ValueError('source changed')
    return {'generated_at':datetime.now(timezone.utc).isoformat(),'integration_policy':'VCGC_EXISTING_PLUS_NEW_ATLAS_AND_LOCAL_TOOLS','engine_sha256':ENGINE_SHA,'engine_version':'Agent OS hardened v1.0.2','status':'PASS_LOCAL_TOOL_TESTS','rows':rows,'count':len(rows),'provider_calls':0,'provider_billing_tokens':'NOT_MEASURED','formal_registration':False,'existing_vcgc_engine_modified':False,'live_vcgc_connected':False,'activated_scope':'explicit local CLI invocations in this test only; no persistent host wiring','notes':['Each request uses one context preparation path; no chained double compression. This does not replace the VCGC provisioning engine.','Token savings are heuristics on synthetic inputs; query extraction is lossy and opt-in.','No financial/stock return claims or live database tests.']}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--package-root',type=Path,default=Path(__file__).resolve().parents[1]);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    if a.out.exists() or a.out.is_symlink():raise SystemExit('refuse existing output')
    result=run(a.package_root.resolve())
    with a.out.open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps({'status':result['status'],'count':result['count'],'out':str(a.out)},ensure_ascii=False))
