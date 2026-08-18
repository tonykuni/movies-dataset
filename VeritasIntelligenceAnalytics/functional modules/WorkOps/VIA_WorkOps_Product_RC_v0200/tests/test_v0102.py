# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(全引擎導入令 2026-08-18;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # accel_map/fetch/pip_install/run_fast
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====
import json, os, shutil, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; ENG=ROOT/"engines"; OUT=ROOT/"out"; FIX=ROOT/"tests"/"fixtures"
def run(script,*args):
    env=os.environ.copy(); env["PYTHONPATH"]=str(ENG)
    return subprocess.run([sys.executable,str(ENG/script),*args],cwd=ROOT,env=env,text=True,capture_output=True)
def reset():
    if OUT.exists(): shutil.rmtree(OUT)
    OUT.mkdir()
    shutil.copy(FIX/"followup_state_v0102.json",OUT/"followup_state.json")
def seed_projects():
    rows=[
      {"event":"CREATE","project_id":"PRJ-20260809-000001","display_name":"India PSU Transfer","default_language":"zh-TW","default_template":"blocked_recovery"},
      {"event":"CREATE","project_id":"PRJ-20260809-000002","display_name":"Approval Project","default_language":"en"},
      {"event":"CREATE","project_id":"PRJ-20260809-000003","display_name":"Normal Work","default_language":"zh-CN"}
    ]
    with (OUT/"project_registry.jsonl").open("w",encoding="utf-8") as f:
        for r in rows:f.write(json.dumps(r,ensure_ascii=False)+"\n")
def test_multilingual_pack_and_templates_coexist():
    reset(); seed_projects()
    r=run("workops_followup_pack_builder.py","build","--language","zh-TW"); assert r.returncode==0,r.stderr
    d=json.loads(r.stdout); assert d["count"]>=2
    langs={x["project_id"]:x["language"] for x in d["items"]}
    assert langs["PRJ-20260809-000001"]=="zh-TW"
    assert langs["PRJ-20260809-000002"]=="en"
    assert any(x["template_key"]=="closure_confirmation" for x in d["items"])
    # run override must coexist, not alter registry
    r=run("workops_followup_pack_builder.py","build","--language","zh-CN","--template","progress_followup")
    d2=json.loads(r.stdout); assert all(x["template_key"]=="progress_followup" for x in d2["items"])
def test_missing_guard_blocks_weak_close():
    reset()
    # Remove evidence from close candidate to prove guard catches it.
    d=json.loads((OUT/"followup_state.json").read_text(encoding="utf-8"))
    for c in d["cards"]:
        if c["state_code"]=="DONE_CANDIDATE": c["evidence"]=""
    (OUT/"followup_state.json").write_text(json.dumps(d,ensure_ascii=False),encoding="utf-8")
    r=run("workops_missing_information_guard.py","scan"); assert r.returncode==0,r.stderr
    m=json.loads(r.stdout)
    close=next(x for x in m["items"] if x["state_code"]=="DONE_CANDIDATE")
    assert close["gate"]=="BLOCK_CLOSE" and "evidence" in close["missing"]
def test_card_aggregator():
    reset(); seed_projects()
    assert run("workops_missing_information_guard.py","scan").returncode==0
    assert run("workops_followup_pack_builder.py","build","--language","zh-TW").returncode==0
    r=run("workops_project_card_aggregator.py","build"); assert r.returncode==0,r.stderr
    d=json.loads(r.stdout); assert d["count"]==3
    b=next(x for x in d["cards"] if x["project_id"]=="PRJ-20260809-000001")
    assert b["flash"] is True and b["followup_ready"] is True
