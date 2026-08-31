# -*- coding: utf-8 -*-
"""ENG-050 Explainable Project Health + Accuracy Aggregator."""
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
from collections import defaultdict
from datetime import datetime
from pathlib import Path
HERE=Path(__file__).resolve().parent;WORKOPS=HERE.parent;OUT=WORKOPS/"out"
PARAMS=HERE/"project_health_params.json";CARDS=OUT/"project_cards.json";CMT=OUT/"commitment_status.json"
INTEG=OUT/"evidence_integrity.json";PROG=OUT/"project_progress_estimate.json";CAL=OUT/"project_candidates_calibrated.json"
RESULT=OUT/"project_health.json"
def loadj(p,d):
    try:return json.loads(Path(p).read_text(encoding="utf-8-sig"))
    except Exception:return d
def atomic(p,o):
    Path(p).parent.mkdir(parents=True,exist_ok=True);t=Path(str(p)+".tmp")
    t.write_text(json.dumps(o,ensure_ascii=False,indent=2),encoding="utf-8");t.replace(p)
def clamp(x):return max(0,min(100,float(x)))
def build():
    p=loadj(PARAMS,{})
    cards=loadj(CARDS,{"cards":[]}).get("cards",[])
    cmts=defaultdict(list)
    for x in loadj(CMT,{"items":[]}).get("items",[]):cmts[x.get("project_id")].append(x)
    integ={x.get("project_id"):x for x in loadj(INTEG,{"items":[]}).get("items",[])}
    prog={x.get("project_id"):x for x in loadj(PROG,{"items":[]}).get("items",[])}
    # calibrated classification confidence is conversation-level; project gets max supporting confidence.
    class_conf=defaultdict(float)
    for item in loadj(CAL,{"items":[]}).get("items",[]):
        for c in item.get("candidates",[]):
            pid=c.get("project_id")
            if pid:class_conf[pid]=max(class_conf[pid],float(c.get("calibrated_confidence",0)))
    rows=[]
    for c in cards:
        pid=c.get("project_id");cs=cmts.get(pid,[])
        overdue=sum(x.get("status")=="OVERDUE" for x in cs);fulfilled=sum(x.get("status")=="FULFILLED" for x in cs)
        schedule=100
        if c.get("state_code")=="OVERDUE":schedule-=45
        if c.get("state_code")=="BLOCKED":schedule-=25
        schedule-=min(30,float(c.get("waiting_hours") or 0)/72*30)
        commitment=100 if not cs else 100*(fulfilled/len(cs))-overdue*15
        risk=100-(int(c.get("level",1))-1)*20
        information=100-len(c.get("missing_fields") or [])*15
        evidence=100*float(integ.get(pid,{}).get("field_coverage",0))
        if integ.get(pid,{}).get("contradiction_count",0):evidence-=40
        progress_conf=100*float(prog.get(pid,{}).get("confidence",0))
        components={"schedule":clamp(schedule),"commitment":clamp(commitment),"risk":clamp(risk),
                    "information":clamp(information),"evidence":clamp(evidence),"progress_confidence":clamp(progress_conf)}
        health=sum(components[k]*float(w) for k,w in p["health_weights"].items())
        # accuracy confidence
        accuracy_parts={
          "evidence_integrity":clamp(evidence),
          "progress_confidence":clamp(progress_conf),
          "information_completeness":clamp(information),
          "classification_confidence":100*float(class_conf.get(pid,0))
        }
        accuracy=sum(accuracy_parts[k]*float(w) for k,w in p["accuracy_weights"].items())
        if health>=80:band="GREEN"
        elif health>=65:band="YELLOW"
        elif health>=50:band="ORANGE"
        else:band="RED"
        hard=p.get("hard_review_gates",{})
        review_reasons=[]
        contradictions=int(integ.get(pid,{}).get("contradiction_count",0))
        if accuracy<65: review_reasons.append("aggregate_accuracy_below_65")
        if contradictions>int(hard.get("contradiction_count_max",0)): review_reasons.append("evidence_contradiction")
        cc=accuracy_parts["classification_confidence"]
        if cc>0 and cc<float(hard.get("classification_confidence_min_pct",60)): review_reasons.append("classification_confidence_too_low")
        if accuracy_parts["evidence_integrity"]<float(hard.get("evidence_integrity_min_pct",70)): review_reasons.append("evidence_integrity_too_low")
        pd=prog.get(pid,{}).get("progress_delta_pct")
        if pd is not None and abs(float(pd))>float(hard.get("absolute_progress_delta_max_pct",20)): review_reasons.append("user_system_progress_divergence")
        rows.append({"project_id":pid,"project_name":c.get("project_name"),"health_score":round(health,1),"health_band":band,
                     "accuracy_confidence_pct":round(accuracy,1),"components":components,"accuracy_components":accuracy_parts,
                     "review_required":bool(review_reasons),"review_reasons":review_reasons})
    rows.sort(key=lambda x:(x["review_required"],-x["health_score"]))
    doc={"version":"v0100","engine_id":"ENG-050","generated_at":datetime.now().isoformat(timespec="seconds"),"count":len(rows),"items":rows}
    atomic(RESULT,doc);return doc
def main():
    ap=argparse.ArgumentParser();ap.add_argument("command",nargs="?",default="build",choices=["build","status"]);a=ap.parse_args()
    if a.command=="build":print(json.dumps(build(),ensure_ascii=False,indent=2))
    else:print(json.dumps(loadj(RESULT,{}),ensure_ascii=False,indent=2))
    return 0
if __name__=="__main__":raise SystemExit(main())
