from pathlib import Path
import importlib.util,sys,tempfile,subprocess,time,signal,json
engine=Path(__file__).resolve().parent.parent/'CGC_MDL149_VeritasCentralGovernanceConsole_v0194.py'
spec=importlib.util.spec_from_file_location('adaptive_qa',engine);m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
with tempfile.TemporaryDirectory() as temp:
 base=Path(temp);root=base/'source';root.mkdir();out=base/'out';out.mkdir();p=root/'VDF_sample_v0100.py';p.write_text('def old(): return 1\n');before=m.scan([root],out)
 script="import importlib.util,sys\nfrom pathlib import Path\np="+repr(str(engine))+"\ns=importlib.util.spec_from_file_location('watchtest',p);m=importlib.util.module_from_spec(s);sys.modules[s.name]=m;s.loader.exec_module(m)\nm.AUTO_POLL_SECONDS=0.05;m.AUTO_DEEP_SECONDS=1;m.AUTO_COOLDOWN_SECONDS=0.1;m.WATCH_INTERVAL_SECONDS=0.02\nm.watch(["+repr(str(root))+"],Path("+repr(str(out))+"),None)\n"
 with (base/'watch.log').open('wb') as log:
  proc=subprocess.Popen([sys.executable,'-c',script],stdout=log,stderr=log)
  try:
   until=time.monotonic()+10
   while not (out/'adaptive_status.json').exists() and time.monotonic()<until:time.sleep(.05)
   assert (out/'adaptive_status.json').exists(),'watch not started'
   p.write_text('def old(): return 2\ndef newly_added(): return 3\n')
   while time.monotonic()<until:
    current=m.load_snapshot(out)
    if current['run_id']!=before['run_id']:break
    time.sleep(.05)
   assert current['run_id']!=before['run_id'],'snapshot did not refresh';assert len(current['features'])==2,'new function omitted';assert current['feature_delta']['added'],'missing feature delta'
   proc.send_signal(signal.SIGINT);proc.wait(timeout=5);assert proc.returncode==0
   assert m.read_json(out/'session.json')['expires_at']<=m.utc_now()
   result={'status':'PASS','tests':4,'passed':4,'scope':'Actual background watcher on temporary local files, shortened polling intervals','checks':['automatic refresh after source edit','new function discovered','feature delta populated','clean stop expires session'],'engine_sha256':m.file_hash(engine)}
  finally:
   if proc.poll() is None:proc.kill();proc.wait()
m.atomic_json(Path(__file__).parent/'adaptive_result.json',result);print(json.dumps(result))
