import json,os,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];ENG=ROOT/"engines";OUT=ROOT/"out";FIX=ROOT/"tests"/"fixtures"
def run(script,*args):
 env=os.environ.copy();env["PYTHONPATH"]=str(ENG);return subprocess.run([sys.executable,str(ENG/script),*args],cwd=ROOT,env=env,text=True,capture_output=True)
def reset():
 if OUT.exists():shutil.rmtree(OUT)
 OUT.mkdir();shutil.copy(FIX/"followup_state_v0103.json",OUT/"followup_state.json")
def seed():
 rows=[{"event":"CREATE","project_id":"PRJ-20260809-000001","display_name":"India PSU Transfer","default_language":"zh-TW","default_template":"blocked_recovery"},{"event":"CREATE","project_id":"PRJ-20260809-000002","display_name":"Approval Project","default_language":"en"},{"event":"CREATE","project_id":"PRJ-20260809-000003","display_name":"Normal Work","default_language":"zh-CN"}]
 with (OUT/"project_registry.jsonl").open("w",encoding="utf-8") as f:
  for r in rows:f.write(json.dumps(r,ensure_ascii=False)+"\n")
def pipe():
 seed();assert run("workops_missing_information_guard.py","scan").returncode==0;assert run("workops_followup_pack_builder.py","build","--language","zh-TW").returncode==0;assert run("workops_project_card_aggregator.py","build").returncode==0
def test_close():
 reset();pipe();d=json.loads(run("workops_closure_intelligence.py","detect").stdout);x=next(z for z in d["items"] if z["project_id"]=="PRJ-20260809-000002");assert x["ready_for_human_confirmation"]
 r=run("workops_closure_intelligence.py","confirm","--project-id","PRJ-20260809-000002","--reason","ISSUE_RESOLVED");assert r.returncode==0 and "CLS-" in r.stdout
 r2=run("workops_closure_intelligence.py","confirm","--project-id","PRJ-20260809-000002","--reason","ISSUE_RESOLVED");assert "ALREADY_CLOSED" in r2.stdout
def test_watch():
 reset();pipe();assert run("workops_closure_intelligence.py","detect").returncode==0;d=json.loads(run("workops_watchlist_prioritizer.py","build").stdout);assert d["today"]["count"]>=2 and d["watchlist"]["count"]>=1
def test_lifecycle():
 reset();r=run("workops_module_lifecycle_manager.py","health");assert r.returncode==0,r.stderr;d=json.loads(r.stdout);ids={x["module_id"] for x in d["modules"]};assert {"ENG-035","ENG-039","ENG-040"}.issubset(ids)
 c=OUT/"candidate.py";c.write_text("print('candidate')\n",encoding="utf-8");p=json.loads(run("workops_module_lifecycle_manager.py","propose","ENG-035",str(c)).stdout);assert p["activation_performed"] is False
