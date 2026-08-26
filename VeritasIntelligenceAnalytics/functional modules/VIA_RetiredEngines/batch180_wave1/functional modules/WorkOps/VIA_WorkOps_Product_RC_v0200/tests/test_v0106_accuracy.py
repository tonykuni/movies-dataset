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
import json, os, shutil, subprocess, sys, tempfile
from pathlib import Path

SRC=Path(__file__).resolve().parents[1]

def run(eng,work,script,*args):
    env=os.environ.copy();env["PYTHONPATH"]=str(eng)
    r=subprocess.run([sys.executable,str(eng/script),*args],cwd=work,env=env,text=True,capture_output=True,timeout=15)
    assert r.returncode==0,(script,r.stderr,r.stdout)
    return json.loads(r.stdout)

def test_accuracy_hard_gates():
    tmp=Path(tempfile.mkdtemp())/"work"
    shutil.copytree(SRC,tmp)
    out=tmp/"out";shutil.rmtree(out,ignore_errors=True);out.mkdir()
    eng=tmp/"engines"
    with (out/"project_registry.jsonl").open("w",encoding="utf-8") as f:
        f.write(json.dumps({"event":"CREATE","project_id":"PRJ-20260809-000001","display_name":"India Transfer"})+"\n")
        f.write(json.dumps({"event":"CREATE","project_id":"PRJ-20260809-000002","display_name":"Project B"})+"\n")
    (out/"project_cards.json").write_text(json.dumps({"cards":[
      {"project_id":"PRJ-20260809-000001","project_name":"India Transfer","owner":"Chris","state_code":"BLOCKED","level":4,"closed":False,"due":"2026-08-12","waiting_hours":55,"progress_pct":80,"missing_fields":["plan_b"],"evidence":"EML-1"},
      {"project_id":"PRJ-20260809-000002","project_name":"Project B","owner":"Mary","state_code":"IN_PROGRESS","level":3,"closed":True,"due":"2026-08-13","waiting_hours":4,"progress_pct":90,"missing_fields":[]}
    ]}),encoding="utf-8")
    (out/"commitment_status.json").write_text(json.dumps({"items":[
      {"commitment_id":"CMT1","project_id":"PRJ-20260809-000001","status":"OVERDUE","due_at":"2026-08-08T17:00:00+08:00","evidence":"EML-CMT1"},
      {"commitment_id":"CMT2","project_id":"PRJ-20260809-000001","status":"FULFILLED","due_at":"2026-08-07T17:00:00+08:00","evidence":"EML-CMT2","fulfillment_evidence":"EML-F2"}
    ]}),encoding="utf-8")
    (out/"closure_candidates.json").write_text('{"items":[]}',encoding="utf-8")
    (out/"project_candidates.json").write_text(json.dumps({"items":[{"conversation_id":"C-A","candidates":[
      {"project_id":"PRJ-20260809-000001","display_name":"India Transfer","score":0.82,"evidence":["subject:0.90"]},
      {"project_id":"PRJ-20260809-000002","display_name":"Project B","score":0.78,"evidence":["subject:0.80"]}
    ]}]}),encoding="utf-8")
    (out/"classification_memory.jsonl").write_text("",encoding="utf-8")
    (out/"milestone_registry.jsonl").write_text(
      json.dumps({"project_id":"PRJ-20260809-000001","milestone_id":"M1","status":"COMPLETED"})+"\n"+
      json.dumps({"project_id":"PRJ-20260809-000001","milestone_id":"M2","status":"OPEN"})+"\n",encoding="utf-8")
    integ=run(eng,tmp,"VIA_ENG114_WorkopsEvidenceIntegrityGuard.py","build")
    cal=run(eng,tmp,"VIA_ENG111_WorkopsConfidenceCalibrator.py","build")
    prog=run(eng,tmp,"workops_progress_estimator.py","build")
    health=run(eng,tmp,"workops_project_health.py","build")
    assert integ["fail_closed"]==1
    assert cal["items"][0]["candidates"][0]["calibrated_confidence"]==0.55
    p=next(x for x in prog["items"] if x["project_id"]=="PRJ-20260809-000001")
    assert p["progress_delta_pct"] < -20
    h=next(x for x in health["items"] if x["project_id"]=="PRJ-20260809-000001")
    assert h["review_required"] is True
    assert "classification_confidence_too_low" in h["review_reasons"]
    assert "user_system_progress_divergence" in h["review_reasons"]
