# -*- coding: utf-8 -*-
"""ENG-049 Evidence-based Project Progress Estimator."""
from __future__ import annotations
import argparse,json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
HERE=Path(__file__).resolve().parent;WORKOPS=HERE.parent;OUT=WORKOPS/"out"
PARAMS=HERE/"progress_estimator_params.json";CARDS=OUT/"project_cards.json";CMT=OUT/"commitment_status.json"
INTEG=OUT/"evidence_integrity.json";MILE=OUT/"milestone_registry.jsonl";RESULT=OUT/"project_progress_estimate.json"
def loadj(p,d):
    try:return json.loads(Path(p).read_text(encoding="utf-8-sig"))
    except Exception:return d
def loadjl(p):
    rows=[]
    if not Path(p).exists():return rows
    for ln in Path(p).read_text(encoding="utf-8",errors="replace").splitlines():
        try:rows.append(json.loads(ln))
        except Exception:pass
    return rows
def atomic(p,o):
    Path(p).parent.mkdir(parents=True,exist_ok=True);t=Path(str(p)+".tmp")
    t.write_text(json.dumps(o,ensure_ascii=False,indent=2),encoding="utf-8");t.replace(p)
def build():
    p=loadj(PARAMS,{})
    cards=loadj(CARDS,{"cards":[]}).get("cards",[]);cmts=loadj(CMT,{"items":[]}).get("items",[])
    integ={x.get("project_id"):x for x in loadj(INTEG,{"items":[]}).get("items",[])}
    miles=defaultdict(list)
    for m in loadjl(MILE):
        if m.get("project_id"):miles[m["project_id"]].append(m)
    cby=defaultdict(list)
    for c in cmts:
        if c.get("project_id"):cby[c["project_id"]].append(c)
    rows=[]
    for c in cards:
        pid=c.get("project_id");factors={};conf_parts=[]
        cs=cby.get(pid,[])
        if cs:
            done=sum(x.get("status")=="FULFILLED" for x in cs);factors["completed_commitments"]=done/len(cs);conf_parts.append(1.0)
        else:factors["completed_commitments"]=None
        ms=miles.get(pid,[])
        if ms:
            done=sum(str(x.get("status","")).upper() in ("DONE","COMPLETED","CLOSED") for x in ms);factors["milestones"]=done/len(ms);conf_parts.append(1.0)
        else:factors["milestones"]=None
        # action proxy from current state; conservative.
        factors["open_actions"]=1.0 if c.get("closed") else 0.75 if c.get("state_code")=="DONE_CANDIDATE" else 0.55 if c.get("state_code")=="IN_PROGRESS" else 0.35
        conf_parts.append(0.65)
        cov=float(integ.get(pid,{}).get("field_coverage",0));factors["evidence_coverage"]=cov;conf_parts.append(cov)
        factors["closure_readiness"]=1.0 if c.get("closed") else 0.9 if c.get("close_candidate") else 0.0;conf_parts.append(0.8)
        weighted=0;used=0
        for k,w in p.get("weights",{}).items():
            v=factors.get(k)
            if v is None:continue
            weighted+=float(w)*float(v);used+=float(w)
        base=100*(weighted/used if used else 0)
        penalties=0
        penalties+=sum(x.get("status")=="OVERDUE" for x in cs)*float(p["penalties"]["overdue_commitment_each"])
        if c.get("state_code")=="BLOCKED":penalties+=float(p["penalties"]["blocked"])
        if int(c.get("level",1))>=5:penalties+=float(p["penalties"]["critical_risk"])
        penalties+=len(c.get("missing_fields") or [])*float(p["penalties"]["missing_control_each"])
        est=max(0,min(100,base-penalties))
        confidence=sum(conf_parts)/len(conf_parts) if conf_parts else 0
        user=c.get("progress_pct")
        delta=None if user is None else round(est-float(user),1)
        gate="PUBLISH_WITH_USER_PROGRESS" if confidence>=float(p["gates"]["confidence_publish_min"]) else "REVIEW_LOW_CONFIDENCE"
        rows.append({"project_id":pid,"project_name":c.get("project_name"),"user_progress_pct":user,
                     "system_estimated_progress_pct":round(est,1),"progress_delta_pct":delta,
                     "confidence":round(confidence,3),"gate":gate,"factors":factors,"penalty_points":round(penalties,1)})
    doc={"version":"v0100","engine_id":"ENG-049","generated_at":datetime.now().isoformat(timespec="seconds"),"count":len(rows),"items":rows}
    atomic(RESULT,doc);return doc
def main():
    ap=argparse.ArgumentParser();ap.add_argument("command",nargs="?",default="build",choices=["build","status"]);a=ap.parse_args()
    if a.command=="build":print(json.dumps(build(),ensure_ascii=False,indent=2))
    else:print(json.dumps(loadj(RESULT,{}),ensure_ascii=False,indent=2))
    return 0
if __name__=="__main__":raise SystemExit(main())
