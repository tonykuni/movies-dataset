"""三輪排程、20 風險、正式接線與 AST 同批修復的隔離測試。"""
from __future__ import annotations
import argparse
import copy
import importlib.util
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
SPEC=importlib.util.spec_from_file_location('via_v3_fixture',HERE/'test_panorama_fusion_v0300.py')
base=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(base)
engine=base.engine


class WorkflowTests(unittest.TestCase):
    setUpClass=classmethod(base.Acceptance.setUpClass.__func__)
    tearDownClass=classmethod(base.Acceptance.tearDownClass.__func__)
    write=base.Acceptance.write
    tool=base.Acceptance.tool
    persist=base.Acceptance.persist
    def setUp(self) -> None:
        base.Acceptance.setUp(self)
        self.cfg['workflow'].update(env_gate=False,governed_lock_gate=False,max_parallel=2)
        self.persist()
    def review(self) -> dict:
        return engine.triple_review(self.cfg)
    def patch_file(self,items: list[dict]) -> None:
        p=self.base/'patches.json';engine.save(p,items);self.cfg['workflow']['patch_file']=str(p);self.persist()
    def patch_for(self,name: str,symbol: str,replacement: str) -> dict:
        return {'path':name,'symbol':symbol,'before_sha256':engine.sha((self.root/name).read_bytes()),'replacement_def':replacement}
    def test_fixed_three_rounds_and_reverse_fresh_validation(self) -> None:
        r=self.review();self.assertEqual(r['round_count'],3);self.assertEqual([v['direction'] for v in r['rounds']],['FORWARD','REVERSE','FORWARD'])
        self.assertEqual(r['status'],'STABLE');self.assertTrue(all(x['etag_status']=='FRESH_SHA_AST' for x in r['rounds'][2]['files']))
    def test_change_between_rounds_is_not_cached_away(self) -> None:
        real=engine.check_round
        def changed(cfg: dict,number: int,expected: dict | None = None) -> dict:
            if number==2:self.write('ocr_a.py',base.PURE+'# source moved\n')
            return real(cfg,number,expected)
        with patch.object(engine,'check_round',side_effect=changed):r=self.review()
        self.assertEqual(r['status'],'BLOCKED');self.assertIn('ocr_a.py',r['rounds'][1]['drift'])
    def test_missing_registered_file_still_counted_all_rounds(self) -> None:
        (self.root/'ocr_b.py').unlink();r=self.review()
        self.assertEqual(r['status'],'BLOCKED')
        self.assertTrue(all((x['expected'],x['scanned'],len(x['skipped']))==(3,2,1) for x in r['rounds']))
    def test_twenty_unique_risks_with_concrete_responses(self) -> None:
        self.assertEqual(len(engine.RISK_CATALOG),20)
        self.assertEqual({r[0] for r in engine.RISK_CATALOG},{'R'+str(i).zfill(2) for i in range(1,21)})
        self.assertTrue(all(d and s for _,_,d,s in engine.RISK_CATALOG))
    def test_unconnected_sources_never_become_production_green(self) -> None:
        r=engine.run_workflow(self.cfg,'2',offline=True,repair=False)
        self.assertEqual(r['round_count'],3);self.assertFalse(r['native_acceptance']);self.assertEqual(r['risks']['count'],20)
        risk={x['id']:x for x in r['risks']['rows']};self.assertEqual(risk['R07']['status'],'PENDING');self.assertEqual(risk['R18']['status'],'PENDING')
    def test_graph_gate_prevents_batch_business_execution(self) -> None:
        self.cfg['adapters'].pop('graphify');self.persist()
        with patch.object(engine,'fusion',side_effect=AssertionError('no business execution')):r=engine.run_workflow(self.cfg,'1')
        self.assertEqual(r['status'],'BLOCKED');self.assertFalse(r['applied']);self.assertFalse(r['preflight_pass'])
    def test_utf8_ast_byte_coordinates_preserve_neighbor_literals(self) -> None:
        text='def f() -> None:\n    x="中文"; print(x) # 原註解\n'
        call=next(n for n in engine.ast.walk(engine.ast.parse(text)) if isinstance(n,engine.ast.Call))
        fn=call.func
        value=engine.ast_byte_edits(text,[{'line':fn.lineno,'col':fn.col_offset,'end_line':fn.end_lineno,'end_col':fn.end_col_offset,'before':'print','text':'logger'}])
        self.assertIn('x="中文"; logger(x) # 原註解',value)
    def test_overlapping_ast_edits_refused(self) -> None:
        text='value=1\n';e={'line':1,'col':0,'end_line':1,'end_col':5,'text':'other','before':'value'}
        with self.assertRaisesRegex(ValueError,'OVERLAP'):engine.ast_byte_edits(text,[e,e])
    def test_two_defs_same_file_one_prepared_task(self) -> None:
        name='nlp_patch.py';raw='def a(x):\n    return x+1\ndef b(y):\n    return y+2\n';self.write(name,raw);self.required.append(name);self.persist()
        self.patch_file([self.patch_for(name,'a','def a(x: int) -> int:\n    return x+1'),self.patch_for(name,'b','def b(y: int) -> int:\n    return y+2')])
        before=(self.root/name).read_bytes();r=engine.batch_prepare(self.cfg,self.review())
        self.assertEqual(r['status'],'READY',r['errors']);self.assertEqual(r['changed_files'],1);self.assertEqual((self.root/name).read_bytes(),before)
        self.assertIn('def b(y: int) -> int:',r['prepared'][name].decode());self.assertTrue((Path(r['candidate_preview'])/name).is_file())
    def test_duplicate_same_symbol_patch_not_last_writer_wins(self) -> None:
        p=self.patch_for('ocr_a.py','plus',base.PURE);self.patch_file([p,p]);r=engine.batch_prepare(self.cfg,self.review())
        self.assertEqual(r['status'],'BLOCKED');self.assertIn('OVERLAP',str(r['errors']))
    def test_signature_binding_change_blocks_patch(self) -> None:
        p=self.patch_for('ocr_a.py','plus','def plus(x: int, extra: int) -> int:\n    return x+extra')
        with self.assertRaisesRegex(ValueError,'API_BINDING'):engine.prepare_file_task(self.cfg,'ocr_a.py',(self.root/'ocr_a.py').read_bytes(),[p])
    def test_anchor_inside_def_cannot_disappear(self) -> None:
        name='nlp_anchor.py';self.write(name,'def f(x: int) -> int:\n    # [AST-ANCHOR: KEEP]\n    return x\n')
        p=self.patch_for(name,'f','def f(x: int) -> int:\n    return x')
        with self.assertRaisesRegex(ValueError,'ANCHOR_LOSS'):engine.prepare_file_task(self.cfg,name,(self.root/name).read_bytes(),[p])
    def test_stale_patch_sha_does_not_touch_source(self) -> None:
        p=self.patch_for('ocr_a.py','plus',base.PURE);p['before_sha256']='0'*64;before=(self.root/'ocr_a.py').read_bytes()
        with self.assertRaisesRegex(ValueError,'SOURCE_HASH'):engine.prepare_file_task(self.cfg,'ocr_a.py',before,[p])
        self.assertEqual((self.root/'ocr_a.py').read_bytes(),before)
    def test_parallel_layers_and_ordered_dependencies(self) -> None:
        tasks=[{'path':n} for n in ('a.py','b.py','c.py','d.py')];r=engine.task_batches(tasks,[('a.py','c.py'),('b.py','c.py'),('c.py','d.py')])
        self.assertEqual([l['parallel'] for l in r['layers']],[['a.py','b.py'],['c.py'],['d.py']])
    def test_same_file_tasks_cannot_parallel_overwrite(self) -> None:
        with self.assertRaisesRegex(ValueError,'SAME_FILE'):engine.task_batches([{'path':'a.py'},{'path':'a.py'}],[])
    def test_cycle_does_not_silently_run_in_arbitrary_order(self) -> None:
        r=engine.task_batches([{'path':n} for n in ('a.py','b.py','c.py')],[('a.py','b.py'),('b.py','a.py')])
        self.assertEqual(r['layers'][0]['parallel'],['c.py']);self.assertEqual(r['blocked_cycle'],['a.py','b.py'])
    def test_import_dependency_drives_file_order(self) -> None:
        files={'ocr_a.py':base.PURE.encode(),'nlp_driver.py':b'from ocr_a import plus\n'}
        self.assertIn(('ocr_a.py','nlp_driver.py'),engine.dependency_edges(files,[]))
    def test_mcp_autofix_writes_stderr_and_preserves_json_stdout(self) -> None:
        name='mcp.py';raw='def debug(x: str) -> str:\n    print("中文", x)\n    return x\n# [AST-ANCHOR: MCP]\n'
        self.cfg['fusion']['mcp_modules']=[name];r=engine.prepare_file_task(self.cfg,name,raw.encode(),[])
        target=self.base/name;target.write_bytes(r['data'])
        command='import importlib.util,json,sys; s=importlib.util.spec_from_file_location("fixture_mcp",sys.argv[1]); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); v=m.debug("ok"); sys.stdout.write(json.dumps({"value":v}))'
        result=subprocess.run([sys.executable,'-B','-c',command,str(target)],capture_output=True,text=True,timeout=10)
        self.assertEqual(result.returncode,0,result.stderr);self.assertEqual(json.loads(result.stdout),{'value':'ok'});self.assertIn('中文 ok',result.stderr)
    def test_explicit_file_print_is_not_blindly_redirected(self) -> None:
        name='mcp.py';self.cfg['fusion']['mcp_modules']=[name];raw=b'import sys\ndef f() -> None:\n    print("x",file=sys.stdout)\n'
        r=engine.prepare_file_task(self.cfg,name,raw,[]);self.assertEqual(r['data'],raw)
    def test_plain_adjacent_duplicate_import_only(self) -> None:
        raw=b'import json\nimport json\nfrom os import getcwd\nfrom os import getcwd\n'
        r=engine.prepare_file_task(self.cfg,'x.py',raw,[])
        self.assertEqual(r['data'].count(b'import json'),1);self.assertEqual(r['data'].count(b'from os import getcwd'),2)
    def test_prepared_baseline_drift_stops_core(self) -> None:
        raw=(self.root/'ocr_a.py').read_bytes()
        with self.assertRaisesRegex(ValueError,'PREPARED_BASELINE_DRIFT'):engine.fusion(self.cfg,prepared={'ocr_a.py':raw+b'\n'},prepared_hashes={'ocr_a.py':'bad'})
        self.assertEqual((self.root/'ocr_a.py').read_bytes(),raw)
    def test_whole_workflow_apply_in_fixture_not_native_green(self) -> None:
        r=engine.run_workflow(self.cfg,'both',apply=True)
        self.assertEqual(r['status'],'APPLIED_VERIFIED',r.get('core'));self.assertEqual(r['final']['status'],'PASS');self.assertEqual(r['round_count'],3)
        self.assertFalse(r['native_acceptance']);self.assertTrue((self.root/engine.COMMAND_BINDINGS_FILE).is_file())
    def test_retirement_with_stale_manifest_rolls_back_at_final_scope_gate(self) -> None:
        r=engine.run_workflow(self.cfg,'1',apply=True,retire=True)
        self.assertEqual(r['status'],'ROLLED_BACK_FINAL_AUDIT');self.assertFalse(r['applied']);self.assertTrue((self.root/'ocr_b.py').is_file())
    def test_final_manager_regression_rolls_back_after_live_pass(self) -> None:
        real=engine.adapter;count=[0]
        def fail_final(cfg: dict,name: str,**kwargs: str) -> dict:
            if name=='test_matrix' and kwargs.get('candidate')==cfg['root']:
                count[0]+=1
                if count[0]>=2:return {'status':'BLOCKED'}
            return real(cfg,name,**kwargs)
        original=(self.root/'ocr_a.py').read_bytes()
        with patch.object(engine,'adapter',side_effect=fail_final):r=engine.run_workflow(self.cfg,'1',apply=True)
        self.assertEqual(r['status'],'ROLLED_BACK_FINAL_AUDIT');self.assertEqual((self.root/'ocr_a.py').read_bytes(),original)
    def test_v2_config_migrates_without_overwriting_previous(self) -> None:
        old=self.base/'old.json';value=copy.deepcopy(self.cfg);value['schema']='VIA.PanoramaFusion.v2';engine.save(old,value);digest=engine.sha(old.read_bytes())
        cfg=engine.config(argparse.Namespace(config=old,root=None,work=None))
        self.assertEqual(cfg['schema'],engine.SCHEMA);self.assertNotEqual(cfg['config_path'],str(old));self.assertEqual(engine.sha(old.read_bytes()),digest)
    def test_large_graph_backup_and_restore(self) -> None:
        target=self.root/'graph.json';content=b'{"text":"'+b'x'*(9*1024*1024)+b'"}';target.write_bytes(content)
        self.cfg['backup_roots']=[{'label':'graph','path':str(self.root),'patterns':['graph.json']}]
        b=engine.backup(self.cfg);self.assertTrue(b['verified_before_prune']);target.write_bytes(b'{}');engine.restore_backup(self.cfg,Path(b['snapshot']))
        self.assertEqual(engine.sha(target.read_bytes()),engine.sha(content))
    def test_duplicate_transaction_target_conflict_is_preflight_only(self) -> None:
        p=self.root/'x.txt';p.write_bytes(b'a');one={'target':str(p),'expected':engine.sha(b'a'),'data':'Yg=='};two={**one,'data':'Yw=='}
        with self.assertRaisesRegex(ValueError,'DUPLICATE_TARGET'):engine.transaction(self.cfg,[one,two])
        self.assertEqual(p.read_bytes(),b'a')
    def test_http_alias_and_session_are_not_missed(self) -> None:
        examples=['import requests as rq\nrq.get("https://example.invalid")','from httpx import get as fetch\nfetch("https://example.invalid")','import requests as rq\ns=rq.Session()\ns.get("https://example.invalid")']
        for source in examples:self.assertTrue(engine.skeleton(source.encode(),'fetch.py')['network'])
    def test_short_command_aliases_and_catalog_have_no_fake_registration(self) -> None:
        r=engine.token_tools(self.cfg);self.assertEqual(r['status'],'CATALOG_ONLY');self.assertIn('REQUIRES_OFFICIAL',r['aliases']['status'])
        self.assertEqual(r['aliases']['aliases']['via-fuse']['action'],1);self.assertEqual(r['aliases']['aliases']['via-panorama']['action'],2)
    def test_accelerator_map_api_actually_called_and_capped(self) -> None:
        module,_=engine.load_tool(self.cfg,'accelerator');real=module.parallel_map
        with patch.object(module,'parallel_map',wraps=real) as mapped:
            values,evidence=engine.accelerated_map(self.cfg,lambda x:x+'!', ['a','b'],99)
        self.assertEqual(values,['a!','b!']);self.assertTrue(evidence['executed']);self.assertEqual(mapped.call_count,1);self.assertLessEqual(mapped.call_args.kwargs['max_workers'],2)
    def test_duplicate_top_level_symbols_detected(self) -> None:
        card=engine.skeleton(b'def f() -> int:\n    return 1\ndef f() -> int:\n    return 2\n','x.py')
        self.assertEqual(card['duplicate_bindings'],['f']);self.assertTrue(any(i['rule']=='DUPLICATE_SYMBOL_BINDING' for i in card['issues']))
    def test_token_dispatch_rejects_uncontrolled_fix_verb(self) -> None:
        with self.assertRaisesRegex(ValueError,'ALLOWLIST'):engine.token_dispatch(self.cfg,'fix',[])
    def test_model_patch_cannot_add_destructive_call(self) -> None:
        old=engine.ast.parse('def f(x: int) -> int:\n    return x').body[0]
        new=engine.ast.parse('def f(x: int) -> int:\n    __import__("os").remove("victim")\n    return x').body[0]
        with self.assertRaisesRegex(ValueError,'EFFECT_CALL'):engine.validate_patch_effects(self.cfg,old,new)
    def test_model_patch_cannot_change_existing_io_target(self) -> None:
        old=engine.ast.parse('def f() -> None:\n    os.remove("expected")').body[0]
        new=engine.ast.parse('def f() -> None:\n    os.remove("unexpected")').body[0]
        with self.assertRaisesRegex(ValueError,'EFFECT_CALL'):engine.validate_patch_effects(self.cfg,old,new)
    def test_model_patch_cannot_add_environment_store(self) -> None:
        old=engine.ast.parse('def f() -> None:\n    return None').body[0]
        new=engine.ast.parse('def f() -> None:\n    os.environ["VIA_NET_CONSENT"]="yes"').body[0]
        with self.assertRaisesRegex(ValueError,'EXTERNAL_STORE'):engine.validate_patch_effects(self.cfg,old,new)
    def test_owned_duckdb_gate_has_no_sqlite_fallback(self) -> None:
        r=engine.context_storage_gate(self.cfg);self.assertEqual(r['status'],'BLOCKED');self.assertFalse(r['sqlite_fallback'])
    def test_context_store_requires_exact_packet_hash(self) -> None:
        packet=self.work/'packet.json';engine.save(packet,{'status':'test'})
        def response(cfg: dict,name: str,**kwargs: str) -> dict:
            return {'status':'PASS','data':{'owner':'VCGC','duckdb_verified':True,'parquet_verified':True,'receipt_sha256':'wrong'}}
        with patch.object(engine,'adapter',side_effect=response):r=engine.context_store(self.cfg,packet)
        self.assertEqual(r['status'],'BLOCKED');self.assertIn('HASH',r['reason'])
    def test_context_store_accepts_verified_owner_sink(self) -> None:
        packet=self.work/'packet.json';engine.save(packet,{'status':'test'})
        def response(cfg: dict,name: str,**kwargs: str) -> dict:
            return {'status':'PASS','data':{'owner':'VCGC','duckdb_verified':True,'parquet_verified':True,'receipt_sha256':engine.sha(packet.read_bytes())}}
        with patch.object(engine,'adapter',side_effect=response):r=engine.context_store(self.cfg,packet)
        self.assertEqual(r['status'],'PASS');self.assertFalse(r['sqlite_fallback'])
    def test_required_context_failure_rolls_back_applied_source(self) -> None:
        review=self.review();self.cfg['native_required']=True;review['accelerator']['locked']=True;review['graphify']['scope_verified']=True;before=(self.root/'ocr_a.py').read_bytes()
        def applied(cfg: dict,*args: object,**kwargs: object) -> dict:
            operation={'target':str(self.root/'ocr_a.py'),'expected':engine.sha(before),'data':base.base64.b64encode(before+b'\n').decode()}
            txn=engine.transaction(cfg,[operation])
            return {'status':'APPLIED_VERIFIED','applied':True,'transaction':txn,'original_actions':3,'final_actions':3,'before':{'status':'PASS'},'after':{'status':'PASS'},'manager':{},'retirement':{'eligible':[]}}
        with patch.object(engine,'triple_review',return_value=review),patch.object(engine,'verify_graph_scope',return_value={'status':'PASS','scope_verified':True}),patch.object(engine,'audit_envs',return_value={'status':'PASS','vcgc_env_coverage':100.0,'missing_count':0}),patch.object(engine,'governed_tools',return_value={'status':'PASS'}),patch.object(engine,'context_storage_gate',return_value={'status':'PASS'}),patch.object(engine,'context_store',return_value={'status':'BLOCKED'}),patch.object(engine,'fusion',side_effect=applied):r=engine.run_workflow(self.cfg,'1',apply=True)
        self.assertEqual(r['status'],'ROLLED_BACK_CONTEXT_STORE');self.assertFalse(r['applied']);self.assertEqual((self.root/'ocr_a.py').read_bytes(),before)
    def test_capability_catalog_keeps_planned_items_unverified(self) -> None:
        r=engine.token_tools(self.cfg)['vcgc_capability_snapshot'];self.assertEqual(len(r['external']),13);self.assertEqual(len(r['token_saving']),32)
        self.assertTrue(any(x['status'].startswith('NOT_IMPLEMENTED') for x in r['token_saving']))
    def test_auto_repair_false_never_calls_fusion_even_with_apply(self) -> None:
        self.cfg['workflow']['auto_repair']=False;self.persist()
        with patch.object(engine,'fusion',side_effect=AssertionError('repair disabled')):r=engine.run_workflow(self.cfg,'both',apply=True)
        self.assertEqual(r['status'],'REVIEW_ONLY');self.assertFalse(r['applied'])
    def test_native_graph_requires_source_scope_proof_not_generic_pass(self) -> None:
        self.cfg['native_required']=True;r=self.review()
        self.assertFalse(r['graphify']['scope_verified']);self.assertEqual(r['graphify']['scope_verification']['adapter']['status'],'PASS')
    def test_graph_scope_excludes_derived_json_and_avoids_self_reference(self) -> None:
        self.cfg['native_required']=True
        def verified(cfg: dict,name: str,**kwargs: str) -> dict:
            data=engine.load(Path(kwargs['manifest']));return {'status':'PASS','data':{'source_manifest_sha256':data['source_manifest_sha256'],'coverage_complete':True,'uncovered':0}}
        with patch.object(engine,'adapter',side_effect=verified):
            first=engine.verify_graph_scope(self.cfg,{'a.py':'a'*64,'graph.json':'b'*64})
            second=engine.verify_graph_scope(self.cfg,{'a.py':'a'*64,'graph.json':'c'*64})
        self.assertTrue(first['scope_verified']);self.assertEqual(first['module_count'],1);self.assertEqual(first['source_manifest_sha256'],second['source_manifest_sha256'])
    def test_large_routine_scope_keeps_all_counts_without_sending_all_signatures(self) -> None:
        cards=[engine.skeleton(base.PURE.encode(),'ocr_'+str(i)+'.py') for i in range(80)]
        reduced=engine.summarize_routine_cards(cards)
        self.assertEqual(sum(c['source_count'] for c in reduced),80);self.assertTrue(all(not c['symbols'] for c in reduced))
        r=engine.route_review(self.cfg,'routine summary',cards)
        self.assertEqual(r['status'],'PASS');self.assertEqual(r['input_files'],80);self.assertTrue(r['scope_compression'])
    def test_syntax_error_is_reported_while_independent_patch_is_staged(self) -> None:
        self.write('bad.py','def broken(:\n');self.required.append('bad.py')
        self.write('ocr_a.py','def plus(x, /, *, step=1):\n    return x+step\n');self.persist()
        self.patch_file([self.patch_for('ocr_a.py','plus',base.PURE)])
        original=(self.root/'ocr_a.py').read_bytes();r=engine.batch_prepare(self.cfg,self.review())
        self.assertEqual(r['status'],'BLOCKED');self.assertIn('bad.py',str(r['errors']));self.assertIn('ocr_a.py',r['prepared']);self.assertEqual((self.root/'ocr_a.py').read_bytes(),original)
    def test_readonly_two_cli_aliases_produce_three_round_receipts(self) -> None:
        for action in ('1','2'):
            result=subprocess.run([sys.executable,str(base.SOURCE),'--config',self.cfg['config_path'],action,'--offline','--check-only'],capture_output=True,text=True,timeout=30)
            value=json.loads(result.stdout);self.assertEqual(value['round_count'],3);self.assertFalse(value['applied'])


def main() -> int:
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(WorkflowTests);result=unittest.TextTestRunner(stream=sys.stderr,verbosity=2).run(suite)
    value={'schema':engine.SCHEMA,'version':engine.VERSION,'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped),'passed':result.wasSuccessful(),'scope':'isolated Linux fixtures, local mock model, no Windows PC or native registration'}
    sys.stdout.write(json.dumps(value)+'\n');return 0 if result.wasSuccessful() else 1


if __name__=='__main__':raise SystemExit(main())
