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
ROOT=Path(__file__).resolve().parents[1]
ENG=ROOT/"engines"; OUT=ROOT/"out"; FIX=ROOT/"tests"/"fixtures"

def run(script,*args):
    env=os.environ.copy(); env["PYTHONPATH"]=str(ENG)
    return subprocess.run([sys.executable,str(ENG/script),*args],cwd=ROOT,env=env,text=True,capture_output=True)

def reset():
    if OUT.exists(): shutil.rmtree(OUT)
    OUT.mkdir()
def test_autocode():
    reset(); sys.path.insert(0,str(ENG))
    import workops_autocode as a
    a.SEQ_P=OUT/"autocode_sequence.json"; a.LOCK_P=OUT/".autocode_sequence.lock"; a.OUT=OUT
    x=a.next_code("PRJ","2026-08-09"); y=a.next_code("PRJ","2026-08-09")
    assert x=="PRJ-20260809-000001" and y=="PRJ-20260809-000002"
def test_registration_and_fusion():
    reset()
    r=run("workops_project_registration.py","create","India PSU Transfer"); assert r.returncode==0, r.stderr
    pid=json.loads(r.stdout)["project_id"]
    shutil.copy(FIX/"mails.csv",OUT/"mails.csv")
    # Build a live control-sheet anchor using the immutable project id.
    ctrl=(FIX/"control_sheet.csv").read_text(encoding="utf-8-sig").replace("PLACEHOLDER",pid)
    (OUT/"control_sheet.csv").write_text(ctrl,encoding="utf-8-sig")
    r=run("workops_project_fusion.py","classify"); assert r.returncode==0, r.stderr
    d=json.loads(r.stdout); assert d["count"]==2
    # confirm one mapping and rerun; memory must become strongest signal.
    r=run("workops_project_registration.py","accept","C1",pid,"--folder","Inbox\\India","--product","PSU-1234"); assert r.returncode==0
    r=run("workops_project_fusion.py","classify"); d=json.loads(r.stdout)
    c1=next(x for x in d["items"] if x["conversation_id"]=="C1")
    assert c1["candidates"][0]["project_id"]==pid
    assert c1["user_confirmation_required"] is True
def test_reply_builder():
    reset(); shutil.copy(FIX/"followup_state.json",OUT/"followup_state.json")
    r=run("workops_mandatory_reply_builder.py","build"); assert r.returncode==0, r.stderr
    d=json.loads(r.stdout); assert d["count"]==1
    item=d["items"][0]
    assert item["send_allowed"] is False
    assert any(q["key"]=="plan_b" for q in item["questions"])
