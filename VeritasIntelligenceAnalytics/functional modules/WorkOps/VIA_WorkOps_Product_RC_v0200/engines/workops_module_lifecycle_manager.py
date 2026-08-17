# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse,hashlib,json,py_compile
from datetime import datetime
from pathlib import Path
HERE=Path(__file__).resolve().parent;WORKOPS=HERE.parent;OUT=WORKOPS/"out"
MANIFESTS=WORKOPS.parent.parent.parent.parent/"manifests"
if not MANIFESTS.exists():MANIFESTS=WORKOPS.parent.parent.parent/"manifests"
if not MANIFESTS.exists():MANIFESTS=HERE.parent/"manifests"
PARAMS=HERE/"module_lifecycle_params.json";SNAP=OUT/"module_registry_snapshot.json";PROPOSALS=OUT/"module_replacement_proposals.jsonl"
MAP={"ENG-031":"workops_mandatory_reply_builder.py","ENG-032":"workops_project_fusion.py","ENG-033":"workops_project_registration.py","ENG-034":"workops_followup_pack_builder.py","ENG-035":"workops_closure_intelligence.py","ENG-037":"workops_missing_information_guard.py","ENG-038":"workops_project_card_aggregator.py","ENG-039":"workops_watchlist_prioritizer.py","ENG-040":"workops_module_lifecycle_manager.py","ENG-041":"workops_daily_operating_rhythm.py","ENG-043":"workops_commitment_fulfillment.py","ENG-042":"workops_meeting_t2_guard.py","ENG-044":"workops_lesson_learned.py","ENG-045":"workops_process_mining_kpi_bridge.py","ENG-046":"workops_evidence_integrity_guard.py","ENG-047":"workops_confidence_calibrator.py","ENG-048":"workops_feedback_weight_optimizer.py","ENG-049":"workops_progress_estimator.py","ENG-050":"workops_project_health.py","ENG-051":"workops_outlook_graph_connector.py","ENG-052":"workops_ssot_store.py","ENG-053":"workops_unified_work_register.py","ENG-054":"workops_timeline_dependency.py","ENG-055":"workops_accuracy_benchmark.py","ENG-056":"workops_unified_search.py","ENG-057":"workops_backup_restore.py","ENG-058":"workops_diagnostics.py","ENG-059":"workops_onboarding.py","ENG-060":"workops_orchestrator.py","ENG-061":"workops_mail_event_bridge.py","ENG-062":"workops_stakeholder_matrix.py","ENG-063":"workops_milestone_manager.py","ENG-064":"workops_smart_escalation.py","ENG-065":"workops_attachment_intelligence.py","ENG-066":"workops_topic_episode.py","ENG-067":"workops_retention_manager.py"}
def loadj(p,d):
    try:return json.loads(Path(p).read_text(encoding="utf-8-sig"))
    except Exception:return d
def sha(p):
    h=hashlib.sha256()
    with Path(p).open("rb") as f:
        for b in iter(lambda:f.read(1048576),b""):h.update(b)
    return h.hexdigest()
def atomic(p,o):
    Path(p).parent.mkdir(parents=True,exist_ok=True);t=Path(str(p)+".tmp");t.write_text(json.dumps(o,ensure_ascii=False,indent=2),encoding="utf-8");t.replace(p)
def append(p,o):
    OUT.mkdir(parents=True,exist_ok=True)
    with Path(p).open("a",encoding="utf-8") as f:f.write(json.dumps(o,ensure_ascii=False)+"\n")
def health():
    req=loadj(PARAMS,{}).get("required_manifest_fields",[]);rows=[]
    for mf in sorted(MANIFESTS.glob("ENG-*.manifest.json")):
        m=loadj(mf,{});mid=m.get("module_id") or mf.stem.split(".")[0];miss=[x for x in req if x not in m];ename=MAP.get(mid);ep=HERE/ename if ename else None
        comp=None;err=""
        if ep and ep.exists():
            try:py_compile.compile(str(ep),doraise=True);comp=True
            except Exception as e:comp=False;err=str(e)
        row={"module_id":mid,"name":m.get("name"),"version":m.get("version"),"manifest":mf.name,"manifest_valid":not miss,"missing_manifest_fields":miss,
        "engine":ename,"engine_exists":bool(ep and ep.exists()),"engine_sha256":sha(ep) if ep and ep.exists() else "","python_compile":comp,"compile_error":err,
        "permissions":m.get("permissions",{}),"lego_contract":m.get("lego_contract","")}
        row["health"]="PASS" if row["manifest_valid"] and row["engine_exists"] and comp is True else "WARN";rows.append(row)
    doc={"version":"v0100","engine_id":"ENG-040","generated_at":datetime.now().isoformat(timespec="seconds"),"gate":"PASS" if rows and all(x["health"]=="PASS" for x in rows) else "REVIEW","count":len(rows),"modules":rows}
    atomic(SNAP,doc);return doc
def propose(mid,candidate,notes=""):
    cur=next((x for x in health()["modules"] if x["module_id"]==mid),None)
    if not cur:raise SystemExit("module not registered")
    cp=Path(candidate)
    if not cp.exists():raise SystemExit("candidate file not found")
    comp=None;err=""
    if cp.suffix.lower()==".py":
        try:py_compile.compile(str(cp),doraise=True);comp=True
        except Exception as e:comp=False;err=str(e)
    evt={"proposal_id":"MRP-"+datetime.now().strftime("%Y%m%d%H%M%S%f"),"ts":datetime.now().isoformat(timespec="seconds"),"module_id":mid,
    "current_engine":cur.get("engine"),"current_sha256":cur.get("engine_sha256"),"candidate_path":str(cp),"candidate_sha256":sha(cp),
    "candidate_compile":comp,"candidate_compile_error":err,"notes":notes,"gate":"REVIEW_REQUIRED" if comp is not False else "REJECT_COMPILE_FAIL","activation_performed":False}
    append(PROPOSALS,evt);print(json.dumps(evt,ensure_ascii=False,indent=2));return 0
def main():
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest="cmd",required=True);sub.add_parser("health");p=sub.add_parser("propose");p.add_argument("module_id");p.add_argument("candidate_path");p.add_argument("--notes",default="");a=ap.parse_args()
    if a.cmd=="health":print(json.dumps(health(),ensure_ascii=False,indent=2));return 0
    return propose(a.module_id,a.candidate_path,a.notes)
if __name__=="__main__":raise SystemExit(main())
