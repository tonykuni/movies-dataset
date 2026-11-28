"""PanoramaFusion 的隔離 fixture 測試；不連正式 VIA、外部模型或個人 PC。"""
from __future__ import annotations
import base64
import copy
import importlib.metadata
import importlib.util
import io
import json
import os
import signal
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "VIA_PanoramaFusion_SuperEngine_v0300.py"
spec = importlib.util.spec_from_file_location("via_dual_engine", SOURCE)
engine = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = engine
spec.loader.exec_module(engine)

PURE = '''def plus(x: int, /, *, step: int = 1) -> int:
    """增加固定步長。"""
    return x + step
# [AST-ANCHOR: PURE]
'''
DRIVER = '''import json,sys,pathlib
verb=sys.argv[1]
data={"status":"PASS"}
if verb=="matrix":
    root=pathlib.Path(sys.argv[2]);sys.path.insert(0,str(root))
    try:
        import nlp_driver
        assert nlp_driver.calculate(3)==4
        data.update(all_verbs_pass=True,expected_verbs=["calculate"],tested_verbs=["calculate"],locked_success_before=1,locked_success_after=1,native_pass=True,output_verified=True,ui_verified=True,sdd="GREEN",closeout_lamp="GREEN")
        if (root/"FAIL_LIVE").exists():data["status"]="BLOCKED"
    except BaseException as e:data={"status":"BLOCKED","error":type(e).__name__}
sys.stdout.write(json.dumps(data))
sys.exit(0 if data["status"]=="PASS" else 1)
'''


class Router(BaseHTTPRequestHandler):
    requests_seen = []
    reject = False
    def do_POST(self):
        body=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        type(self).requests_seen.append(body)
        if type(self).reject:
            self.send_response(401);self.end_headers();return
        result={"choices":[{"message":{"content":'{"status":"PASS","notes":[]}'}}],"model":"fixture-low","usage":{"prompt_tokens":3,"completion_tokens":2}}
        raw=json.dumps(result).encode();self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
    def do_GET(self):
        value={"status":"ok","authenticated":self.headers.get('Authorization')=='Bearer fixture-secret',"session_id":"test-session"}
        raw=json.dumps(value).encode();self.send_response(200);self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
    def log_message(self,*args):
        return


class Acceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.http=ThreadingHTTPServer(('127.0.0.1',0),Router)
        cls.http_thread=threading.Thread(target=cls.http.serve_forever,daemon=True);cls.http_thread.start()
        cls.url='http://127.0.0.1:'+str(cls.http.server_port)
    @classmethod
    def tearDownClass(cls):
        cls.http.shutdown();cls.http.server_close();cls.http_thread.join()
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='via-dual-fixture-');self.addCleanup(self.temp.cleanup)
        self.base=Path(self.temp.name);self.root=self.base/'root';self.work=self.base/'work';self.root.mkdir();self.work.mkdir()
        self.cfg=engine.make_config(self.root,self.work);self.cfg.update(native_required=False,config_path=str(self.work/'config.json'))
        self.cfg['fusion'].update(closed_world=True)
        self.driver=self.base/'driver.py';self.driver.write_text(DRIVER)
        self.cfg['adapters']={k:{'command':[sys.executable,str(self.driver),'gate']} for k in ('gate','handoff','functions','graphify')}
        self.cfg['adapters']['test_matrix']={'command':[sys.executable,str(self.driver),'matrix','{candidate}']}
        self.cfg['router'].update(url=self.url)
        self.envpatch=patch.dict(os.environ,{'VIA_ROUTINE_MODEL':'fixture-low','OMNIROUTE_API_KEY':'fixture-key','VIA_REMOTE_SESSION_TOKEN':'fixture-secret'})
        self.envpatch.start();self.addCleanup(self.envpatch.stop)
        self.write('ocr_a.py',PURE);self.write('ocr_b.py',PURE)
        self.write('nlp_driver.py','from ocr_b import plus\ndef calculate(x: int) -> int:\n    return plus(x)\n# [AST-ANCHOR: CALLER]\n')
        self.required=['ocr_a.py','ocr_b.py','nlp_driver.py']
        self.cases=[{'action':p+'::plus','args':[3],'expected':4,'benchmark_group':'OCR.plus','case_id':'value-3'} for p in ('ocr_a.py','ocr_b.py')]+[{'action':'nlp_driver.py::calculate','args':[3],'expected':4}]
        self.cases_file=self.base/'contracts.json';engine.save(self.cases_file,self.cases);self.cfg['fusion']['contracts']=str(self.cases_file)
        self.tool('accelerator','accelerator.py','def parallel_map(fn: object, values: list, max_workers: int = 2, mode: str = "thread") -> list:\n    return list(map(fn, values))\n')
        self.tool('network','network.py','def allow_url(url: str) -> bool:\n    return url.startswith("https://")\n')
        self.persist()
        Router.reject=False;Router.requests_seen=[]
    def write(self,name,text):
        p=self.root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(text.encode() if isinstance(text,str) else text);return p
    def tool(self,name,path,text):
        p=self.write(path,text);lock=self.root/engine.LOCK_REL;lock.parent.mkdir(parents=True,exist_ok=True)
        book=engine.load(lock) if lock.exists() else {}
        book[name]={'path':path,'version':'fixture','sha256':engine.sha(p.read_bytes())};engine.save(lock,book)
    def persist(self):
        engine.save(self.root/'panorama.manifest.json',{'include_files':self.required})
        engine.save(Path(self.cfg['config_path']),self.cfg);engine.accel_env(self.cfg)
    def fuse(self,**kwargs):
        self.persist();return engine.fusion(self.cfg,**kwargs)
    def test_two_actions_cli(self):
        for command in ('scan','fusion'):
            result=subprocess.run([sys.executable,str(SOURCE),'--config',self.cfg['config_path'],command,'--offline'],capture_output=True,timeout=30)
            self.assertIn(result.returncode,(0,1,2));value=json.loads(result.stdout)
            self.assertNotIn(value.get('reason'),('AttributeError','SyntaxError'))
    def test_scan_registered_coverage_and_cache(self):
        a=engine.scan(self.cfg,True);b=engine.scan(self.cfg,True)
        self.assertEqual((a['expected'],a['scanned'],len(a['skipped'])),(3,3,0))
        self.assertTrue(all(x.get('etag_status')=='304_NOT_MODIFIED' for x in b['files']))
        self.assertEqual(a['acceptance'],'BLOCKED_OR_PENDING')
    def test_unknown_manifest_not_full_green(self):
        (self.root/'panorama.manifest.json').unlink()
        result=engine.scan(self.cfg,True)
        self.assertEqual(result['scope_authority'],'DISCOVERY_ONLY')
        self.assertEqual(result['acceptance'],'BLOCKED_OR_PENDING')
    def test_registered_missing_is_listed(self):
        (self.root/'ocr_b.py').unlink();r=engine.scan(self.cfg,True)
        self.assertEqual(r['expected'],3);self.assertEqual(r['scanned'],2);self.assertEqual(r['skipped'][0]['reason'],'REGISTERED_MISSING')
    def test_read_does_not_execute_source(self):
        self.write('side.py','raise RuntimeError("DO_NOT_EXECUTE")\n');self.required.append('side.py');self.persist()
        result=engine.scan(self.cfg,True)
        self.assertEqual(result['scanned'],4)
    def test_graphify_lookup(self):
        path=self.base/'graph.json';engine.save(path,{'nodes':[{'id':'a','label':'OCR','source_file':'ocr_a.py'}],'links':[{'source':'a','target':'b'}]})
        self.cfg['graph_file']=str(path);r=engine.graph_query(self.cfg,'OCR')
        self.assertEqual(r['total_hits'],1);self.assertEqual(len(r['paths']),1)
    def test_conversation_export(self):
        path=self.base/'conversations.json';engine.save(path,[{'id':'x','title':'sample','mapping':{'a':{},'b':{}}}])
        self.cfg['conversation_exports']=[{'provider':'ChatGPT','path':str(path)}]
        r=engine.conversation_index(self.cfg)
        self.assertEqual(r['sources'][0]['entries'][0]['messages'],2)
        self.assertEqual(r['coverage']['Claude'],'NOT_CONNECTED_NO_EXPORT')
    def test_router_rejects_401(self):
        Router.reject=True
        r=engine.route_review(self.cfg,'routine',[])
        self.assertEqual(r['status'],'BLOCKED')
    def test_router_redacts_parameter_default(self):
        card=engine.skeleton(b'def f(api_key: str = "SECRET_CANARY") -> str:\n    return api_key\n','a.py')
        r=engine.route_review(self.cfg,'routine',[card])
        self.assertEqual(r['status'],'PASS')
        self.assertNotIn('SECRET_CANARY',json.dumps(Router.requests_seen))
    def test_high_model_only_deep(self):
        self.cfg['router']['deep_model_env']='VIA_DEEP_MODEL'
        with patch.dict(os.environ,{'VIA_DEEP_MODEL':'fixture-deep'}):
            engine.route_review(self.cfg,'routine',[]);engine.route_review(self.cfg,'repair',[],True)
        self.assertEqual([r['model'] for r in Router.requests_seen],['fixture-low','fixture-deep'])
    def test_mcp_stdio_print_guard(self):
        raw=b'def f() -> None:\n    print("message",sep="|")\n'
        self.assertNotIn('MCP_STDOUT_PRINT',str(engine.skeleton(raw,'a.py',False)))
        self.assertIn('MCP_STDOUT_PRINT',str(engine.skeleton(raw,'a.py',True)))
    def test_exec_eval_iterrows_apply_guard(self):
        source=b'def f(x: object) -> object:\n    eval("1")\n    x.iterrows()\n    return x.apply(str)\n'
        rules={r['rule'] for r in engine.skeleton(source,'a.py')['issues']}
        self.assertTrue({'DYNAMIC_EXECUTION','ROW_LOOP_OR_APPLY'}.issubset(rules))
    def test_type_hints_and_anchor_guard(self):
        card=engine.skeleton(b'def f(x): return x\n','a.py')
        self.assertIn('TYPE_HINT_MISSING',str(card));self.assertIn('ANCHOR_MISSING',str(card))
    def test_bridge_future_decorator_encoding(self):
        raw=b'\xef\xbb\xbf#!/usr/bin/python\r\nfrom __future__ import annotations\r\n@decorator\r\ndef f(x: str) -> str:\r\n    return x\r\n'
        value=engine.inject_bridges(raw,True)
        self.assertTrue(value.startswith(b'\xef\xbb\xbf'))
        self.assertIn(b'@decorator\r\ndef f',value)
        self.assertLess(value.index(b'from __future__'),value.index(b'_via_accel_env()'))
    def test_bridge_rejects_name_collision(self):
        with self.assertRaisesRegex(ValueError,'COLLISION'):
            engine.inject_bridges(b'_via_accel_env=3\n',False)
    def test_import_only_network_not_claim_transport(self):
        self.write('network_job.py','import urllib.request\ndef fetch(url: str) -> object:\n    return urllib.request.urlopen(url)\n# [AST-ANCHOR: NETWORK]\n')
        self.required.append('network_job.py');r=self.fuse(offline=True)
        self.assertIn('NETWORK_CALL_CONTRACT_PENDING',r['blocked'])
        self.assertFalse(r['network_transport_verified'])
    def test_full_fusion_candidate_and_coverage(self):
        r=self.fuse()
        self.assertEqual(r['status'],'READY',r['blocked'])
        self.assertEqual(r['before']['status'],'PASS');self.assertEqual(r['after']['status'],'PASS')
        self.assertEqual(r['bridge_coverage']['effective'],r['bridge_coverage']['expected'])
        candidate=Path(r['candidate'])
        self.assertTrue((candidate/'VIA_OCR_FNC_v0300.py').is_file())
        self.assertTrue((candidate/'VIA_NLP_FNC_v0300.py').is_file())
        self.assertEqual(r['original_actions'],r['final_actions'])
    def test_safe_retire_rewrites_callers_and_restores(self):
        r=self.fuse(apply=True,retire=True)
        self.assertEqual(r['status'],'APPLIED_VERIFIED',r['blocked'])
        self.assertFalse((self.root/'ocr_b.py').exists())
        self.assertIn('from ocr_a import plus',(self.root/'nlp_driver.py').read_text())
        registry=engine.load(self.root/'VIA_FNC_REGISTRY_v0300.json')
        self.assertEqual(registry['actions']['ocr_b.py::plus']['path'],'ocr_a.py')
        engine.recover_transaction(self.cfg,Path(r['transaction']['journal']))
        self.assertTrue((self.root/'ocr_b.py').is_file())
        self.assertEqual((self.root/'ocr_b.py').read_text(),PURE)
        self.assertIn('from ocr_b import plus',(self.root/'nlp_driver.py').read_text())
    def test_no_retirement_without_closed_world(self):
        self.cfg['fusion']['closed_world']=False;r=self.fuse(retire=True)
        self.assertFalse(r['retirement']['eligible']);self.assertIn('CLOSED_WORLD',str(r['retirement']['retained']))
    def test_no_retirement_when_context_dependent(self):
        value='VALUE=7\ndef f(x: int) -> int:\n    return x+VALUE\n'
        self.write('ocr_a.py',value);self.write('ocr_b.py',value)
        files={n:(self.root/n).read_bytes() for n in ('ocr_a.py','ocr_b.py')};idx=engine.fusion_index(files)
        r=engine.retirement_plan(self.cfg,files,idx,[{'action':n+'::f'} for n in files])
        self.assertFalse(r['eligible']);self.assertIn('CONTEXT',str(r['retained']))
    def test_no_retirement_missing_api_case(self):
        self.cases=self.cases[:1];engine.save(self.cases_file,self.cases)
        files={n:(self.root/n).read_bytes() for n in self.required};idx=engine.fusion_index(files)
        r=engine.retirement_plan(self.cfg,files,idx,self.cases)
        self.assertFalse(r['eligible']);self.assertIn('CONTRACT_MISSING',str(r['retained']))
    def test_dynamic_import_blocks_retirement(self):
        self.write('dynamic.py','import importlib\ndef dynamic(x: str) -> object:\n    return importlib.import_module(x)\n')
        files={n:(self.root/n).read_bytes() for n in self.required+['dynamic.py']}
        r=engine.retirement_plan(self.cfg,files,engine.fusion_index(files),self.cases)
        self.assertFalse(r['eligible']);self.assertIn('DYNAMIC',str(r['retained']))
    def test_native_pending_blocks_apply(self):
        self.cfg['native_required']=True;r=self.fuse(apply=True,retire=True)
        self.assertFalse(r['applied']);self.assertTrue((self.root/'ocr_b.py').exists())
        self.assertIn('NATIVE_OUTPUT_UI_SDD_PENDING',r['blocked'])
    def test_model_missing_blocks_apply(self):
        self.cfg['router']['url']='';r=self.fuse(apply=True)
        self.assertIn('OMNIROUTE_REQUIRED',r['blocked']);self.assertFalse(r['applied'])
    def test_failed_contract_blocks_apply(self):
        self.cases[0]['expected']=999;engine.save(self.cases_file,self.cases)
        r=self.fuse(apply=True,retire=True)
        self.assertIn('CONTRACTS_NOT_PASS',r['blocked']);self.assertFalse(r['applied'])
    def test_read_only_gate_blocks_apply(self):
        self.cfg['adapters'].pop('gate');r=self.fuse(apply=True)
        self.assertIn('VCGC_READ_ONLY_GATE',r['blocked']);self.assertFalse(r['applied'])
    def test_gate_failure_prevents_business_code_execution(self):
        self.cfg['adapters'].pop('gate')
        with patch.object(engine,'contracts_run',side_effect=AssertionError('business execution forbidden')),patch.object(engine,'probe_candidate_bridges',side_effect=AssertionError('probe forbidden')):
            r=self.fuse(apply=True,retire=True)
        self.assertEqual(r['before']['status'],'BLOCKED_PRE_EXECUTION_GATE')
        self.assertFalse(r['applied'])
    def test_graphify_missing_blocks_business_execution(self):
        self.cfg['adapters'].pop('graphify')
        with patch.object(engine,'contracts_run',side_effect=AssertionError('graph first')):r=self.fuse(apply=True)
        self.assertIn('GRAPHIFY_REQUIRED',r['blocked']);self.assertFalse(r['applied'])
    def test_deep_patch_annotations_multiple_defs_one_source_sha(self):
        name='nlp_fix.py';raw=b'def a(x):\n    return x+1\ndef b(y):\n    return y+2\n'
        files={name:raw};patches=[{'path':name,'symbol':symbol,'before_sha256':engine.sha(raw),'replacement_def':replacement} for symbol,replacement in [('a','def a(x: int) -> int:\n    return x+1'),('b','def b(y: int) -> int:\n    return y+2')]]
        reply={'status':'PASS','outputs':[{'content':json.dumps({'patches':patches})}]}
        with patch.object(engine,'route_review',return_value=reply) as review:r=engine.deep_patches(self.cfg,files,[engine.skeleton(raw,name)])
        self.assertEqual(r['changed'],[name]);self.assertEqual(engine.counted_red(files,[]),{})
        windows=review.call_args.args[2];self.assertEqual(len(windows),2);self.assertTrue(all(c['sha256']==engine.sha(raw) for c in windows))
    def test_deep_patch_cannot_remove_anchor(self):
        name='nlp_fix.py';raw=b'def a(x):\n    # [AST-ANCHOR: KEEP]\n    return x+1\n';files={name:raw}
        value={'patches':[{'path':name,'symbol':'a','before_sha256':engine.sha(raw),'replacement_def':'def a(x: int) -> int:\n    return x+1'}]}
        with patch.object(engine,'route_review',return_value={'status':'PASS','outputs':[{'content':json.dumps(value)}]}):
            with self.assertRaisesRegex(ValueError,'ANCHOR_LOSS'):engine.deep_patches(self.cfg,files,[engine.skeleton(raw,name)])
        self.assertEqual(files[name],raw)
    def test_deep_patch_credentials_not_sent(self):
        name='nlp_fix.py';raw=b'def a(x, api_key="private-default"):\n    return x\n';files={name:raw}
        with patch.object(engine,'route_review',side_effect=AssertionError('no secret egress')):r=engine.deep_patches(self.cfg,files,[engine.skeleton(raw,name)])
        self.assertEqual(r['status'],'BLOCKED');self.assertEqual(files[name],raw)
    def test_live_failure_rolls_back_source_and_retirement(self):
        self.write('FAIL_LIVE','fail after source switch only')
        r=self.fuse(apply=True,retire=True)
        self.assertEqual(r['status'],'ROLLED_BACK',r)
        self.assertFalse(r['applied']);self.assertEqual((self.root/'ocr_b.py').read_text(),PURE)
        self.assertIn('from ocr_b import plus',(self.root/'nlp_driver.py').read_text())
        self.assertFalse((self.root/engine.BRIDGE_FILE).exists())
    def test_real_benchmark_rankings(self):
        r=self.fuse();rows=r['rankings']['OCR.plus']
        self.assertEqual(len(rows),2);self.assertTrue(all(x['verified_cases']==1 for x in rows))
        self.assertLessEqual(rows[0]['mean_seconds'],rows[1]['mean_seconds'])
    def test_incomparable_benchmark_not_ranked(self):
        cases=[{'action':'a','args':[1],'expected':2,'benchmark_group':'g','case_id':'x'},{'action':'b','args':[2],'expected':3,'benchmark_group':'g','case_id':'x'}]
        evidence={'status':'PASS','results':[{'ok':True,'seconds':1},{'ok':True,'seconds':.1}]}
        self.assertEqual(engine.benchmark_rankings(cases,evidence),{})
    def test_manager_empty_verbs_not_pass(self):
        self.assertFalse(engine.manager_parity({'all_verbs_pass':True}))
        self.assertFalse(engine.manager_parity({'all_verbs_pass':True,'expected_verbs':[],'tested_verbs':[],'locked_success_before':0,'locked_success_after':0}))
    def test_spans_preserve_other_code(self):
        text='# keep\ndef a() -> int:\n    return 1\ndef b() -> int:\n    return 2\n'
        value=engine.apply_spans(text,[(1,3,'def a() -> int:\n    return 3\n')])
        self.assertIn('# keep',value);self.assertIn('def b() -> int:\n    return 2',value)
        with self.assertRaises(ValueError):engine.apply_spans(text,[(1,4,''),(2,3,'')])
    def test_transaction_failure_rolls_back(self):
        a=self.write('first.txt','old1');b=self.write('second.txt','old2')
        operations=[{'target':str(p),'expected':engine.sha(p.read_bytes()),'data':base64.b64encode(v).decode()} for p,v in ((a,b'new1'),(b,b'new2'))]
        original=engine.atomic
        def fail(path,value):
            if path==b and value==b'new2':raise OSError('injected write failure')
            return original(path,value)
        with patch.object(engine,'atomic',side_effect=fail):
            with self.assertRaises(OSError):engine.transaction(self.cfg,operations)
        self.assertEqual(a.read_bytes(),b'old1');self.assertEqual(b.read_bytes(),b'old2')
    def test_transaction_cas_no_overwrite(self):
        p=self.write('x.txt','newer')
        with self.assertRaisesRegex(ValueError,'COMPARE_AND_SWAP'):
            engine.transaction(self.cfg,[{'target':str(p),'expected':engine.sha(b'old'),'data':base64.b64encode(b'candidate').decode()}])
        self.assertEqual(p.read_text(),'newer')
    def test_recovery_does_not_overwrite_new_change(self):
        p=self.write('x.txt','old');r=engine.transaction(self.cfg,[{'target':str(p),'expected':engine.sha(b'old'),'data':base64.b64encode(b'new').decode()}])
        p.write_text('someone else')
        with self.assertRaisesRegex(ValueError,'RECOVERY_COMPARE'):
            engine.recover_transaction(self.cfg,Path(r['journal']))
        self.assertEqual(p.read_text(),'someone else')
    def test_backup_incremental_rotation_restore(self):
        self.cfg['backup_roots']=[{'label':'test','path':str(self.root),'patterns':['*.txt']}]
        p=self.write('note.txt','version 0');first=engine.backup(self.cfg)
        same=engine.backup(self.cfg);self.assertEqual(same['incremental_blobs'],0)
        for n in range(1,7):p.write_text('version '+str(n));last=engine.backup(self.cfg)
        self.assertEqual(last['retained'],5)
        engine.restore_backup(self.cfg,Path(last['snapshot']));self.assertEqual(p.read_text(),'version 6')
        self.assertTrue(Path(first['snapshot']).name not in [x.name for x in (self.work/'backups/snapshots').glob('*')])
    def test_corrupt_backup_rejected(self):
        self.cfg['backup_roots']=[{'label':'test','path':str(self.root),'patterns':['*.txt']}]
        self.write('x.txt','x');r=engine.backup(self.cfg);book=engine.load(Path(r['snapshot']));digest=book['body']['entries'][0]['sha256']
        (self.work/'backups/blobs'/digest).write_bytes(b'bad')
        with self.assertRaisesRegex(ValueError,'BACKUP_CONTENT_CORRUPT'):engine.restore_backup(self.cfg,Path(r['snapshot']))
    def test_environment_unknown_not_100(self):
        r=engine.audit_envs(self.cfg)
        self.assertIsNone(r['vcgc_env_coverage']);self.assertIsNone(r['missing_count']);self.assertEqual(r['status'],'BLOCKED')
    def test_environment_missing_spec(self):
        p=self.root/'via_missing';p.mkdir();(p/'pyvenv.cfg').write_text('')
        self.cfg['env_roots']=[str(self.root)];r=engine.audit_envs(self.cfg)
        self.assertEqual(r['expected_environments'],1);self.assertIn('UNOWNED_ENV',str(r))
    def test_forbidden_lib_detector(self):
        env=self.root/'via_core';(env/'bin').mkdir(parents=True);py=env/('Scripts/python.exe' if os.name=='nt' else 'bin/python');py.parent.mkdir(exist_ok=True)
        py.write_bytes(b'fake')
        requirement={'path':str(env),'owner':'VCGC','required':[{'name':'pip','version':'1','module':'pip'}]}
        result={'checks':[{'name':'pip','installed':'1','version_ok':True,'import_ok':True}],'distributions':{'pip':'1','FinMind':'1','opencv_python':'1'}}
        proc=subprocess.CompletedProcess([],0,engine.encode(result),b'')
        with patch.object(engine.subprocess,'run',return_value=proc):r=engine.audit_one_env(self.cfg,requirement,cache=False)
        self.assertEqual(r['status'],'BLOCKED');self.assertEqual(len(r['forbidden']),2)
    def test_environment_install_must_use_vcgc_adapter(self):
        r=engine.repair_environment(self.cfg,{'path':str(self.root/'via_core')})
        self.assertEqual(r['status'],'BLOCKED');self.assertIn('ADAPTER',r['reason'])
    def test_environment_without_import_target_cannot_claim_coverage(self):
        requirement={'path':str(self.root/'via_core'),'owner':'VCGC','required':[{'name':'pip','version':'1'}]}
        r=engine.audit_one_env(self.cfg,requirement)
        self.assertEqual(r['status'],'BLOCKED');self.assertIsNone(r['coverage'])
    def test_failed_installer_cannot_be_promoted_by_passing_probe(self):
        p=self.root/'via_core';p.mkdir();self.cfg['environments']=[{'path':str(p),'owner':'VCGC','required':[{'name':'pip','version':'1'}]}]
        before={'status':'BLOCKED','path':str(p),'coverage':0.0,'missing_count':1}
        repaired={'status':'BLOCKED','audit':{'status':'PASS','coverage':100.0,'missing_count':0}}
        with patch.object(engine,'audit_one_env',return_value=before),patch.object(engine,'repair_environment',return_value=repaired):r=engine.audit_envs(self.cfg,True)
        self.assertEqual(r['status'],'BLOCKED');self.assertIsNone(r['vcgc_env_coverage'])
    def test_restricted_sdk_change_invalidates_environment_cache(self):
        env=self.root/'via_core';py=env/('Scripts/python.exe' if os.name=='nt' else 'bin/python');py.parent.mkdir(parents=True);py.write_bytes(b'fake')
        requirement={'path':str(env),'owner':'VCGC','required':[{'name':'pip','version':'1','module':'pip'}]}
        result={'checks':[{'name':'pip','installed':'1','version_ok':True,'import_ok':True}],'distributions':{'pip':'1','cloud-sdk':'1'}}
        proc=subprocess.CompletedProcess([],0,engine.encode(result),b'')
        with patch.object(engine.subprocess,'run',return_value=proc):
            first=engine.audit_one_env(self.cfg,requirement)
            self.cfg['restricted_cloud_sdks']=['cloud-sdk'];second=engine.audit_one_env(self.cfg,requirement)
        self.assertEqual(first['status'],'PASS');self.assertEqual(second['status'],'BLOCKED')
    def test_accelerator_hash_gate(self):
        self.write('accelerator.py','raise RuntimeError("must not run")\n')
        r=engine.accel_env(self.cfg)
        self.assertFalse(r['locked']);self.assertEqual(r['error'],'ValueError')
    def test_identical_tool_bytes_do_not_share_project_module_identity(self):
        first,_=engine.load_tool(self.cfg,'accelerator')
        other=self.base/'another_project';other.mkdir();cfg=engine.make_config(other,self.base/'another_work')
        lock=engine.load(self.root/engine.LOCK_REL);path=other/'accelerator.py';path.write_bytes((self.root/'accelerator.py').read_bytes());engine.save(other/engine.LOCK_REL,lock)
        second,_=engine.load_tool(cfg,'accelerator')
        self.assertIsNot(first,second);self.assertEqual(Path(second.__file__),path)
    def test_remote_missing_not_online(self):
        self.assertEqual(engine.remote_probe(self.cfg)['status'],'BLOCKED')
    def test_remote_local_not_public_online(self):
        self.cfg['remote'].update(local_health_url=self.url+'/health',expected_session='test-session')
        r=engine.remote_probe(self.cfg)
        self.assertEqual(r['status'],'LOCAL_ONLY');self.assertTrue(r['local_authenticated'])
    def test_remote_wrong_session_rejected(self):
        self.cfg['remote'].update(local_health_url=self.url+'/health',expected_session='wrong')
        r=engine.remote_probe(self.cfg);self.assertEqual(r['status'],'BLOCKED')
    def test_remote_online_requires_both_authenticated_probes(self):
        self.cfg['remote'].update(local_health_url=self.url+'/health',public_health_url='https://example.invalid/health',expected_session='x')
        value={'status':'ONLINE','authenticated':True,'session_id':'x'}
        with patch.object(engine,'http_json',return_value=value),patch.object(engine,'adapter',return_value={'status':'PASS'}):r=engine.remote_probe(self.cfg)
        self.assertEqual(r['status'],'ONLINE')
    def test_remote_public_session_mismatch_never_online(self):
        self.cfg['remote'].update(local_health_url=self.url+'/health',public_health_url='https://example.invalid/health',expected_session='x')
        values=[{'status':'ONLINE','authenticated':True,'session_id':'x'},{'status':'ONLINE','authenticated':True,'session_id':'other'}]
        with patch.object(engine,'http_json',side_effect=values),patch.object(engine,'adapter',return_value={'status':'PASS'}):r=engine.remote_probe(self.cfg)
        self.assertEqual(r['status'],'LOCAL_ONLY');self.assertFalse(r['public_authenticated'])
    def test_process_identity_mismatch_not_killed(self):
        record={'pid':os.getpid(),'created':'not-the-process','command_sha256':'wrong'}
        self.assertFalse(engine.stop_owned(record))
    def test_depressure_does_not_delete_unknown_temp(self):
        p=self.work/'user_temp.tmp';p.write_text('keep')
        with patch.object(engine,'pressure',return_value={'cpu':0,'ram':0}):r=engine.de_pressure(self.cfg)
        self.assertEqual(r['status'],'PASS');self.assertTrue(p.exists())
    def test_real_three_independent_processes(self):
        self.persist()
        with patch.object(engine,'pressure',return_value={'cpu':0,'ram':0}):r=engine.boot(self.cfg,seconds=3)
        self.addCleanup(lambda:engine.stop(self.cfg,Path(r['session'])))
        self.assertEqual(len({p['pid'] for p in r['processes']}),3)
        self.assertEqual(r['status'],'DEGRADED')
        for n in (1,2,3):self.assertTrue((Path(r['session'])/f'lane{n}_health.json').is_file())
    def test_path_restrictions(self):
        for value in ('../x','C:/x','/tmp/x','a\\b','CON.txt','a?.py'):
            with self.assertRaises(ValueError):engine.relative(value)
    def test_onedrive_cloud_tags_are_not_misclassified_as_links(self):
        for variant in range(16):
            value=type('WinStat',(),{'st_mode':0,'st_file_attributes':0x400,'st_reparse_tag':0x9000001A|(variant<<12)})()
            with patch.object(Path,'lstat',return_value=value):self.assertFalse(engine.linked(self.root))
    def test_junction_symlink_and_unknown_reparse_tags_remain_blocked(self):
        for tag in (0xA0000003,0xA000000C,0,0x800000FF):
            value=type('WinStat',(),{'st_mode':0,'st_file_attributes':0x400,'st_reparse_tag':tag})()
            with patch.object(Path,'lstat',return_value=value):self.assertTrue(engine.linked(self.root))


def main():
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(Acceptance)
    result=unittest.TextTestRunner(stream=sys.stderr,verbosity=2).run(suite)
    data={'schema':engine.SCHEMA,'version':engine.VERSION,'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped),'passed':result.wasSuccessful(),'scope':'Linux fixtures; router is local mock; no user PC, real model inference, real remote service or VIA production acceptance'}
    sys.stdout.write(json.dumps(data,ensure_ascii=False)+'\n')
    return 0 if result.wasSuccessful() else 1


if __name__=='__main__':
    raise SystemExit(main())
