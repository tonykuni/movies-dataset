# -*- coding: utf-8 -*-
"""ENG-037 Missing Information Guard: converts vague work into explicit missing controls."""
from __future__ import annotations
import argparse,json
from datetime import datetime
from pathlib import Path
HERE=Path(__file__).resolve().parent; WORKOPS=HERE.parent; OUT=WORKOPS/"out"
PARAMS=HERE/"missing_information_params.json"; STATE=OUT/"followup_state.json"; RESULT=OUT/"missing_information.json"
def loadj(p,d):
    try:return json.loads(Path(p).read_text(encoding="utf-8-sig"))
    except Exception:return d
def atomic(p,o):
    Path(p).parent.mkdir(parents=True,exist_ok=True)
    t=Path(str(p)+".tmp"); t.write_text(json.dumps(o,ensure_ascii=False,indent=2),encoding="utf-8"); t.replace(p)
def scan():
    p=loadj(PARAMS,{})
    s=loadj(STATE,{"cards":[]}); out=[]
    for c in s.get("cards",[]):
        st=c.get("state_code","UNKNOWN"); req=p.get("rules",{}).get(st,[])
        missing=[x for x in req if c.get(x) in (None,"",[],{})]
        if not missing: continue
        score=sum(int(p.get("severity",{}).get(x,1)) for x in missing)
        out.append({"project_id":c.get("project_id"),"case_id":c.get("case_id"),"thr":c.get("thr"),
                    "project_name":c.get("project_name"),"state_code":st,"missing":missing,
                    "missing_count":len(missing),"control_score":score,
                    "gate":"BLOCK_CLOSE" if "evidence" in missing and st=="DONE_CANDIDATE" else "NEEDS_INFORMATION"})
    doc={"version":"v0100","engine_id":"ENG-037","generated_at":datetime.now().isoformat(timespec="seconds"),
         "count":len(out),"items":sorted(out,key=lambda x:x["control_score"],reverse=True)}
    atomic(RESULT,doc); return doc
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("command",nargs="?",default="scan",choices=["scan","status"])
    a=ap.parse_args()
    if a.command=="scan": print(json.dumps(scan(),ensure_ascii=False,indent=2))
    else:
        d=loadj(RESULT,{})
        print(f"ENG-037 missing-control items: {d.get('count',0)}")
    return 0
if __name__=="__main__": raise SystemExit(main())
