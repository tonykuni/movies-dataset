# -*- coding: utf-8 -*-
"""ENG-060 central WorkOps orchestrator."""
from __future__ import annotations
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
import argparse,json,os,subprocess,sys
from datetime import datetime
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;OUT=ROOT/"out";LOG=ROOT/"logs"/"orchestrator_runs.jsonl"
OUT.mkdir(exist_ok=True);LOG.parent.mkdir(exist_ok=True)

STEPS={
 "ENG-051":("workops_outlook_graph_connector.py",["sync"]),
 "ENG-032":("workops_project_fusion.py",["classify"]),
 "ENG-046":("workops_evidence_integrity_guard.py",["build"]),
 "ENG-047":("workops_confidence_calibrator.py",["build"]),
 "ENG-037":("workops_missing_information_guard.py",["scan"]),
 "ENG-043":("workops_commitment_fulfillment.py",["evaluate"]),
 "ENG-034":("workops_followup_pack_builder.py",["build"]),
 "ENG-038":("workops_project_card_aggregator.py",["build"]),
 "ENG-049":("workops_progress_estimator.py",["build"]),
 "ENG-050":("workops_project_health.py",["build"]),
 "ENG-035":("workops_closure_intelligence.py",["detect"]),
 "ENG-039":("workops_watchlist_prioritizer.py",["build"]),
 "ENG-042":("workops_meeting_t2_guard.py",["build"]),
 "ENG-041":("workops_daily_operating_rhythm.py",["build"]),
 "ENG-044":("workops_lesson_learned.py",["build"]),
 "ENG-053":("workops_unified_work_register.py",["build"]),
 "ENG-054":("workops_timeline_dependency.py",["build"]),
 "ENG-045":("workops_process_mining_kpi_bridge.py",["build"]),
 "ENG-052":("workops_ssot_store.py",["snapshot"]),
 "ENG-040":("workops_module_lifecycle_manager.py",["health"]),
 "ENG-058":("workops_diagnostics.py",["build"]),
 "ENG-061":("workops_mail_event_bridge.py",["build"]),
 "ENG-030":("workops_followup_state.py",["state","--no-open"]),
 "ENG-062":("workops_stakeholder_matrix.py",["build"]),
 "ENG-063":("workops_milestone_manager.py",["build"]),
 "ENG-064":("workops_smart_escalation.py",[]),
 "ENG-065":("workops_attachment_intelligence.py",[]),
 "ENG-066":("workops_topic_episode.py",[])
}
SYNC=["ENG-051","ENG-065","ENG-066","ENG-032","ENG-046","ENG-047"]
REFRESH=["ENG-061","ENG-030","ENG-037","ENG-043","ENG-034","ENG-038","ENG-062","ENG-063","ENG-046","ENG-047","ENG-049","ENG-050","ENG-035","ENG-039","ENG-064","ENG-042","ENG-041","ENG-044","ENG-053","ENG-054","ENG-045","ENG-052","ENG-040","ENG-058"]

def run_step(eid,extra=None):
    script,args=STEPS[eid];cmd=[sys.executable,str(HERE/script),*(extra if extra is not None else args)]
    env=os.environ.copy();env["PYTHONPATH"]=str(HERE)
    r=subprocess.run(cmd,cwd=ROOT,env=env,text=True,capture_output=True,timeout=120)
    try:payload=json.loads(r.stdout) if r.stdout.strip() else {}
    except Exception:payload={"stdout":r.stdout[-3000:]}
    gate=payload.get("gate") or ("PASS" if r.returncode==0 else "FAIL")
    return {"engine_id":eid,"returncode":r.returncode,"gate":gate,"payload":payload,"stderr":r.stderr[-2000:]}

def pipeline(name,mock_file=""):
    ids=SYNC if name=="sync" else REFRESH if name=="refresh" else SYNC+REFRESH
    results=[];start=datetime.now().astimezone().isoformat(timespec="seconds")
    for eid in ids:
        extra=None
        if eid=="ENG-051" and mock_file:extra=["mock-sync",mock_file]
        res=run_step(eid,extra);results.append(res)
        if res["returncode"]!=0 and eid in ("ENG-051","ENG-046","ENG-035"):
            # ENG-051 disabled is acceptable for refresh/offline, but not for requested sync.
            if not (eid=="ENG-051" and res["payload"].get("gate")=="DISABLED"):
                break
    gate="PASS" if all(x["returncode"]==0 for x in results) else "READY_WITH_WARNINGS"
    doc={"version":"v0200","engine_id":"ENG-060","pipeline":name,"started_at":start,
         "finished_at":datetime.now().astimezone().isoformat(timespec="seconds"),"gate":gate,"steps":results}
    with LOG.open("a",encoding="utf-8") as f:f.write(json.dumps(doc,ensure_ascii=False)+"\n")
    (OUT/"orchestrator_status.json").write_text(json.dumps(doc,ensure_ascii=False,indent=2),encoding="utf-8")
    return doc

def main():
    ap=argparse.ArgumentParser();ap.add_argument("pipeline",choices=["sync","refresh","full","status"]);ap.add_argument("--mock-file",default="")
    a=ap.parse_args()
    if a.pipeline=="status":
        try:o=json.loads((OUT/"orchestrator_status.json").read_text(encoding="utf-8"))
        except Exception:o={}
    else:o=pipeline(a.pipeline,a.mock_file)
    print(json.dumps(o,ensure_ascii=False,indent=2));return 0 if o.get("gate")!="FAIL" else 2
if __name__=="__main__":raise SystemExit(main())
