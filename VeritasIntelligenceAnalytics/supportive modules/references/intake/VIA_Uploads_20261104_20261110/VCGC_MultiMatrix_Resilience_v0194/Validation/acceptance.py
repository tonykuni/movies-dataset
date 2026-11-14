from pathlib import Path
import importlib.util,sys,json,tempfile,unittest,hashlib,shutil,contextlib,io
ENGINE=Path(__file__).resolve().parent.parent/'CGC_MDL149_VeritasCentralGovernanceConsole_v0194.py'
spec=importlib.util.spec_from_file_location('matrix_engine',ENGINE);m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
class Acceptance(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.base=Path(self.temp.name);self.root=self.base/'project';self.root.mkdir();self.out=self.base/'report';self.out.mkdir()
 def tearDown(self):self.temp.cleanup()
 def native_fixture(self):
  via=self.root/'VeritasIntelligenceAnalytics';reg=via/'supportive modules/registry';reg.mkdir(parents=True)
  prior=reg/(m.ENGINE_FAMILY+'_v0192.py');prior.write_text('import sys\ndef main(argv=None):\n print("FIXTURE_NATIVE", argv or sys.argv[1:]); return 0\nif __name__=="__main__": raise SystemExit(main())\n')
  for name,key in [('VIA_Requirements_SSOT','requirements'),('VIA_Workflow_VCGC_SSOT','workflows'),('VIA_VCGC_FunctionInventory_SSOT','stations')]:m.atomic_json(reg/(name+'_v0100.json'),{'schema':'native-test-fixture','version':'v0100',key:[]})
  return via,reg,prior
 def test_full_install_plan_and_apply(self):
  via,reg,prior=self.native_fixture();oldhash=m.file_hash(prior);plan=m.install([self.root],self.out,ENGINE.with_name(m.FRONTEND_NAME),False);self.assertEqual(plan['state'],'PLAN_READY');self.assertEqual(len(plan['writes']),5)
  report=m.install([self.root],self.out,ENGINE.with_name(m.FRONTEND_NAME),True);self.assertEqual(report['state'],'INSTALLED');self.assertEqual(m.file_hash(prior),oldhash);self.assertTrue((reg/(m.ENGINE_FAMILY+'_v0194.py')).exists());again=m.install([self.root],self.out,ENGINE.with_name(m.FRONTEND_NAME),True);self.assertEqual(again['state'],'ALREADY_INSTALLED');self.assertEqual(report['registration']['closeout'],'PENDING_NATIVE_AUDIT_REVIEW_AND_CHECKPOINT')
 def test_corrupt_installed_frontend_detected(self):
  via,reg,prior=self.native_fixture();plan=m.prepare_install(via,ENGINE.with_name(m.FRONTEND_NAME));m.commit_transaction(plan,self.out);(via/'supportive modules/VCGC_Matrix'/m.FRONTEND_NAME).write_text('changed')
  with self.assertRaises(RuntimeError):m.prepare_install(via,ENGINE.with_name(m.FRONTEND_NAME))
 def test_registry_race_detected(self):
  via,reg,prior=self.native_fixture();plan=m.prepare_install(via,ENGINE.with_name(m.FRONTEND_NAME));m.atomic_json(reg/'VIA_Requirements_SSOT_v0100.json',{'changed':1})
  with self.assertRaises(RuntimeError):m.commit_transaction(plan,self.out)
 def test_install_collision_no_partial(self):
  via,reg,prior=self.native_fixture();plan=m.prepare_install(via,ENGINE.with_name(m.FRONTEND_NAME));target=Path(plan['writes'][2]['path']);target.write_text('collision')
  with self.assertRaises(FileExistsError):m.commit_transaction(plan,self.out)
  self.assertFalse(Path(plan['writes'][0]['path']).exists())
 def test_real_test_plan_receipt(self):
  entity=self.root/'VQG_factor_v0100.py';entity.write_text('def compute(x):\n return x*2\n');test=self.root/'test_factor.py';output=self.out/'result.json';test.write_text(f'import json,uuid\nfrom pathlib import Path\nfrom VQG_factor_v0100 import compute\nPath({str(output)!r}).write_text(json.dumps({{"value":compute(2),"run_id":str(uuid.uuid4())}}))\n');m.scan([self.root],self.out)
  plan={'schema':'via.matrix.test-plan/1','tests':[{'id':'unit_factor','stage':'UNIT','entity':str(entity),'script':str(test),'script_sha256':m.file_hash(test),'result_json':str(output),'assertions':[{'path':'value','equals':4}]}]};p=self.out/'plan.json';m.atomic_json(p,plan);r=m.run_test_plan(p,[self.root],self.out);self.assertEqual(r[0]['validation_state'],'PASS');updated=m.scan([self.root],self.out);self.assertEqual(next(x for x in updated['files'] if x['path']==str(entity))['tests']['UNIT'],'PASS')
  entity.write_text('def compute(x):\n return x*3\n');stale=m.scan([self.root],self.out);self.assertEqual(next(x for x in stale['files'] if x['path']==str(entity))['tests']['UNIT'],'STALE')
 def test_process_timeout(self):
  test=self.root/'slow.py';test.write_text('import time\ntime.sleep(20)\n');r=m.run_process([sys.executable,str(test)],self.root,self.out,'timeout',0.25);self.assertTrue(r['timed_out']);self.assertEqual(r['state'],'TIMEOUT')
 def test_file_queue_end_to_end(self):
  (self.root/'a.py').write_text('x=1');session=m.create_session(self.out,[self.root]);job={'schema':'via.matrix.job/1','id':'job-acceptance','session_id':session['session_id'],'token':session['token'],'action':'scan'};m.atomic_json(self.out/'jobs/job-acceptance.json',job);result=m.process_jobs(session,self.out,ENGINE.with_name(m.FRONTEND_NAME));self.assertEqual(result[0]['state'],'COMPLETED');self.assertTrue((self.out/m.FRONTEND_NAME).exists());m.atomic_json(self.out/'jobs/job-acceptance.json',job);r=m.process_jobs(session,self.out,ENGINE.with_name(m.FRONTEND_NAME));self.assertEqual(r[0]['state'],'REJECTED_OR_FAILED')
 def test_old_verb_delegation(self):
  via,reg,prior=self.native_fixture();m.commit_transaction(m.prepare_install(via,ENGINE.with_name(m.FRONTEND_NAME)),self.out);result=m.run_process([sys.executable,str(reg/ENGINE.name),'functions'],via,self.out,'old-verb');self.assertEqual(result['exit_code'],0);self.assertIn('FIXTURE_NATIVE',Path(result['log']).read_text())
 def test_json_xss_escaped_in_report(self):
  (self.root/'weird.py').write_text('LABEL="</script><script>alert(1)</script>"\n');state=m.scan([self.root],self.out,ENGINE.with_name(m.FRONTEND_NAME));html=(self.out/m.FRONTEND_NAME).read_text();self.assertNotIn('</script><script>alert(1)',html);self.assertIn('\\u003c/script>',html)
 def test_json_large_catalog(self):
  p=self.root/'VQG_metrics_v0100.json';m.atomic_json(p,{'indicators':{'return':{'formula':'adj_close / adj_close.shift(n) - 1','window':[5,10,20,60,120,240]}}});item=m.inspect_artifact({'path':str(p)});self.assertEqual(len(item['catalog_entries']),1);self.assertEqual(item['catalog_entries'][0]['state'],'DECLARED_NOT_EXECUTED')
 def test_csv_bom_and_parquet(self):
  (self.root/'a.py').write_text('x=1');m.scan([self.root],self.out);self.assertTrue((self.out/'files.csv').read_bytes().startswith(b'\xef\xbb\xbf'));self.assertIn(m.read_json(self.out/'exports.json')['parquet']['state'],['WRITTEN','NOT_AVAILABLE'])
 def test_ps_actual_parser_when_available(self):
  if not shutil.which('pwsh'):self.skipTest('PowerShell not installed; real Windows acceptance pending')
  p=self.root/'a.ps1';p.write_text('function Get-Test { param($x) $x }');data=m.powershell_parse([str(p)],self.out);self.assertEqual(data[str(p)]['parser'],'powershell-ast')
 def test_symlink_accounted_as_unknown(self):
  p=self.root/'linked.py';target=self.base/'actual.py';target.write_text('x=1');p.symlink_to(target);_,excluded,errors=m.enumerate_tree([self.root]);self.assertTrue(excluded);self.assertTrue(errors)
 def test_output_excluded_from_source_scan(self):
  output=self.root/'report';output.mkdir();(output/'generated.py').write_text('x=1');(self.root/'a.py').write_text('x=1');items,_,_=m.enumerate_tree([self.root],output);self.assertEqual(len(items),1)
stream=io.StringIO()
with contextlib.redirect_stdout(io.StringIO()):r=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Acceptance))
result={'scope':'isolated fixture native console; actual Windows systems NOT_RUN','tests':r.testsRun,'passed':r.testsRun-len(r.failures)-len(r.errors)-len(r.skipped),'skipped':len(r.skipped),'failures':len(r.failures),'errors':len(r.errors),'details':stream.getvalue(),'status':'PASS_WITH_EXPLICIT_SKIP' if r.wasSuccessful() else 'FAIL'};m.atomic_json(Path(__file__).parent/'acceptance_result.json',result);print(json.dumps({k:v for k,v in result.items() if k!='details'},ensure_ascii=False));print(stream.getvalue())
raise SystemExit(0 if r.wasSuccessful() else 1)
