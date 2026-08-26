# -*- coding: utf-8 -*-
"""ENG-053 Unified Work Register: one operational queue across projects."""
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
import argparse,json
from datetime import datetime
from pathlib import Path
from workops_autocode import next_code
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;OUT=ROOT/"out";LINK=OUT/"work_item_link_registry.jsonl";RESULT=OUT/"unified_work_register.json"
def jload(p,d):
    try:return json.loads(Path(p).read_text(encoding="utf-8-sig"))
    except Exception:return d
def jl(p):
    rows=[]
    if not Path(p).exists():return rows
    for ln in Path(p).read_text(encoding="utf-8",errors="replace").splitlines():
        try:rows.append(json.loads(ln))
        except Exception:pass
    return rows
def append(p,o):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open("a",encoding="utf-8") as f:f.write(json.dumps(o,ensure_ascii=False)+"\n")
def id_for(kind,source_id,prefix):
    key=f"{kind}|{source_id}"
    for r in jl(LINK):
        if r.get("key")==key:return r["work_item_id"]
    wid=next_code(prefix);append(LINK,{"key":key,"work_item_id":wid,"created_at":datetime.now().astimezone().isoformat(timespec="seconds")});return wid
def item(kind,source,prefix,title,project_id="",project_name="",owner="",status="",due="",next_action="",evidence="",priority=0,depends=None):
    sid=str(source or title)
    return {"work_item_id":id_for(kind,sid,prefix),"source_id":source,"type":kind,"project_id":project_id,"project_name":project_name,
      "title":title,"owner":owner,"status":status,"priority":priority,"due_at":due,"next_action":next_action,"evidence_id":evidence,
      "depends_on":depends or [],"updated_at":datetime.now().astimezone().isoformat(timespec="seconds")}
def build():
    rows=[]
    cards=jload(OUT/"project_cards.json",{"cards":[]}).get("cards",[])
    for c in cards:
        if c.get("closed"):continue
        pid=c.get("project_id");pn=c.get("project_name");st=c.get("state_code","")
        if c.get("issue"):
            rows.append(item("ISSUE",c.get("case_id") or pid,"ISS",c["issue"],pid,pn,c.get("owner",""),st,c.get("due") or "",c.get("next_action") or "",c.get("evidence") or "",int(c.get("level",1))*10))
        if c.get("next_action"):
            rows.append(item("ACTION",(c.get("case_id") or pid)+"|ACTION","ACT",c["next_action"],pid,pn,c.get("owner",""),st,c.get("due") or "","",c.get("evidence") or "",int(c.get("level",1))*10))
        if int(c.get("level",1))>=4:
            rows.append(item("RISK",(c.get("case_id") or pid)+"|RISK","RSK",f"Level {c.get('level')} project risk",pid,pn,c.get("owner",""),st,c.get("due") or "",c.get("next_action") or "","",int(c.get("level",1))*10))
    for c in jload(OUT/"commitment_status.json",{"items":[]}).get("items",[]):
        rows.append(item("COMMITMENT",c.get("commitment_id"),"CMT",c.get("commitment_text") or "Commitment",c.get("project_id"),c.get("project_name"),c.get("owner"),c.get("status"),c.get("due_at"),"",c.get("fulfillment_evidence") or c.get("evidence"),50 if c.get("status")=="OVERDUE" else 20))
    for pr in jload(OUT/"milestone_summary.json",{"projects":[]}).get("projects",[]):
        for m in pr.get("milestones",[]):
            if m.get("status")!="COMPLETED":
                rows.append(item("ACTION",m.get("milestone_id"),"ACT","Milestone: "+str(m.get("name") or ""),pr.get("project_id"),pr.get("project_name") or "",m.get("owner") or "",m.get("status") or "OPEN",m.get("target_date") or "","Complete milestone",m.get("evidence") or "",35))
    for f in jload(OUT/"daily_followup_pack.json",{"items":[]}).get("items",[]):
        rows.append(item("FOLLOWUP",f.get("followup_id"),"FUP",f"Follow-up: {f.get('project_name','')}",f.get("project_id"),f.get("project_name"),"",f.get("state_code"),"", "Prepare/review draft","",30))
    for m in jload(OUT/"meeting_t2_guard.json",{"items":[]}).get("items",[]):
        if m.get("gate")!="READY":
            rows.append(item("MEETING_ACTION",m.get("meeting_id"),"ACT",f"Meeting readiness: {m.get('gate')}",m.get("project_id"),m.get("project_name"),"",m.get("gate"),m.get("start_at"),"Resolve meeting preparation gaps","",40+m.get("readiness_score",0)))
    for c in jload(OUT/"closure_candidates.json",{"items":[]}).get("items",[]):
        if c.get("ready_for_human_confirmation"):
            rows.append(item("CLOSE",(c.get("project_id") or c.get("case_id"))+"|CLOSE","CLS","Confirm closure",c.get("project_id"),c.get("project_name"),"", "READY_TO_CONFIRM","", "Human confirmation required",c.get("evidence"),15))
    rows.sort(key=lambda x:(-int(x.get("priority") or 0),x.get("due_at") or "9999"))
    doc={"version":"v0200","engine_id":"ENG-053","generated_at":datetime.now().astimezone().isoformat(timespec="seconds"),"count":len(rows),"items":rows}
    RESULT.write_text(json.dumps(doc,ensure_ascii=False,indent=2),encoding="utf-8");return doc
def main():
    ap=argparse.ArgumentParser();ap.add_argument("command",nargs="?",default="build",choices=["build","status"]);a=ap.parse_args()
    print(json.dumps(build() if a.command=="build" else jload(RESULT,{}),ensure_ascii=False,indent=2));return 0
if __name__=="__main__":raise SystemExit(main())
