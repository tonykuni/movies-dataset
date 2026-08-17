# -*- coding: utf-8 -*-
"""ENG-047 Confidence Calibration & Accuracy Gate.
Re-scores project candidates using signal diversity, margin, confirmed memory and integrity.
Never auto-confirms a project.
"""
from __future__ import annotations
import argparse,json,re
from datetime import datetime
from pathlib import Path
HERE=Path(__file__).resolve().parent;WORKOPS=HERE.parent;OUT=WORKOPS/"out"
POLICY=HERE/"accuracy_policy.json";PARAMS=HERE/"confidence_calibration_params.json"
CAND=OUT/"project_candidates.json";MEM=OUT/"classification_memory.jsonl";INTEG=OUT/"evidence_integrity.json"
RESULT=OUT/"project_candidates_calibrated.json"

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
def band(score,policy):
    for b in policy.get("confidence_bands",[]):
        if float(b["min"])<=score<=float(b["max"]):return b["code"]
    return "E"
def signal_kind(e):
    s=str(e).lower()
    for k in ("confirmed","control","product","folder","subject","body","stakeholder"):
        if s.startswith(k):return k
    return "other"
def build():
    p=loadj(PARAMS,{});policy=loadj(POLICY,{})
    integrity={x.get("project_id"):x for x in loadj(INTEG,{"items":[]}).get("items",[])}
    rows=[]
    for item in loadj(CAND,{"items":[]}).get("items",[]):
        cc=[]
        ranked=item.get("candidates",[])
        second=float(ranked[1].get("score",0)) if len(ranked)>1 else 0
        for i,c in enumerate(ranked):
            raw=max(0,min(0.99,float(c.get("score",0))))
            sigs={signal_kind(x) for x in c.get("evidence",[]) if signal_kind(x)!="other"}
            score=raw
            reasons=[]
            if len(sigs)==1:
                score-=float(policy.get("penalties",{}).get("single_signal",0.15));reasons.append("single_signal_penalty")
            if len(sigs)>=3:
                score+=float(policy.get("reward",{}).get("three_or_more_independent_signals",0.08));reasons.append("multi_signal_reward")
            if "confirmed" in sigs:
                score+=float(policy.get("reward",{}).get("human_confirmation",0.15));reasons.append("confirmed_memory_reward")
            if "control" in sigs and ("subject" in sigs or "body" in sigs):
                score+=float(policy.get("reward",{}).get("structured_and_email_agree",0.10));reasons.append("structured_email_agreement")
            margin=raw-second if i==0 else raw
            if i==0 and len(ranked)>1 and margin<float(p.get("minimum_candidate_margin",0.12)):
                score-=float(policy.get("penalties",{}).get("low_margin_candidate",0.12));reasons.append("low_margin_penalty")
            integ=integrity.get(c.get("project_id"),{})
            contradictions=int(integ.get("contradiction_count",0))
            score-=contradictions*float(policy.get("penalties",{}).get("contradiction_each",0.20))
            if contradictions:reasons.append("integrity_contradiction_penalty")
            score=max(0,min(0.99,score))
            cc.append({**c,"raw_score":round(raw,3),"calibrated_confidence":round(score,3),
                       "confidence_band":band(score,policy),"signal_count":len(sigs),"signal_types":sorted(sigs),
                       "margin_to_second":round(margin,3) if i==0 else None,"calibration_reasons":reasons})
        top=cc[0]["calibrated_confidence"] if cc else 0
        g=policy.get("gates",{}).get("project_classification",{})
        gate="STRONG_SUGGESTION" if top>=float(g.get("strong_suggestion_min",0.85)) else "REVIEW" if top>=float(g.get("review_min",0.60)) else "UNCERTAIN"
        rows.append({**item,"candidates":cc,"calibrated_gate":gate,"user_confirmation_required":True})
    doc={"version":"v0100","engine_id":"ENG-047","generated_at":datetime.now().isoformat(timespec="seconds"),"count":len(rows),"items":rows}
    atomic(RESULT,doc);return doc
def main():
    ap=argparse.ArgumentParser();ap.add_argument("command",nargs="?",default="build",choices=["build","status"]);a=ap.parse_args()
    if a.command=="build":print(json.dumps(build(),ensure_ascii=False,indent=2))
    else:print(json.dumps(loadj(RESULT,{}),ensure_ascii=False,indent=2))
    return 0
if __name__=="__main__":raise SystemExit(main())
