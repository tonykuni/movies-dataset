# -*- coding: utf-8 -*-
"""ENG-045 Process Mining KPI Bridge."""
from __future__ import annotations
import argparse,csv,json
from datetime import datetime
from pathlib import Path
HERE=Path(__file__).resolve().parent;WORKOPS=HERE.parent;OUT=WORKOPS/"out"
CARDS=OUT/"project_cards.json";PACK=OUT/"daily_followup_pack.json";CMT=OUT/"commitment_status.json";CKPI=OUT/"commitment_kpi.json"
MEET=OUT/"meeting_t2_guard.json";CLOSE=OUT/"closure_events.jsonl";LESSON=OUT/"lesson_registry.jsonl"
KPI=OUT/"management_kpi.json";EVENTS=OUT/"process_event_log.csv"
def loadj(p,d):
    try:return json.loads(Path(p).read_text(encoding="utf-8-sig"))
    except Exception:return d
def loadjl(p):
    out=[]
    if not Path(p).exists():return out
    for ln in Path(p).read_text(encoding="utf-8",errors="replace").splitlines():
        try:out.append(json.loads(ln))
        except Exception:pass
    return out
def atomic(p,o):
    Path(p).parent.mkdir(parents=True,exist_ok=True);t=Path(str(p)+".tmp")
    t.write_text(json.dumps(o,ensure_ascii=False,indent=2),encoding="utf-8");t.replace(p)
def build():
    cards=loadj(CARDS,{"cards":[]}).get("cards",[]);pack=loadj(PACK,{"items":[]}).get("items",[])
    cmts=loadj(CMT,{"items":[]}).get("items",[]);ck=loadj(CKPI,{})
    meet=loadj(MEET,{"items":[]}).get("items",[]);close=loadjl(CLOSE);less=loadjl(LESSON)
    active=[x for x in cards if not x.get("closed")]
    waiting=[float(x.get("waiting_hours") or 0) for x in active]
    kpi={
      "generated_at":datetime.now().isoformat(timespec="seconds"),
      "active_projects":len(active),"warning_projects":sum(int(x.get("level",1))==4 for x in active),
      "critical_projects":sum(int(x.get("level",1))==5 for x in active),
      "followup_ready":sum(bool(x.get("followup_ready")) for x in active),
      "close_candidates":sum(bool(x.get("close_candidate")) for x in active),
      "commitment_fulfillment_rate_pct":ck.get("fulfillment_rate_pct"),
      "overdue_commitments":sum(x.get("status")=="OVERDUE" for x in cmts),
      "meeting_not_ready":sum(str(x.get("gate","")).startswith("NOT_READY") for x in meet),
      "avg_waiting_hours":round(sum(waiting)/len(waiting),1) if waiting else 0,
      "lesson_count":len(less)
    }
    atomic(KPI,kpi)
    rows=[];ts=kpi["generated_at"]
    for x in cards:
        rows.append({"case:concept:name":x.get("project_id") or x.get("case_id"),"concept:name":"Project_State_Snapshot",
                     "time:timestamp":ts,"org:resource":x.get("owner",""),"state":x.get("state_code",""),
                     "source_id":x.get("project_id") or x.get("case_id"),"evidence_id":""})
    for x in pack:
        rows.append({"case:concept:name":x.get("project_id") or x.get("case_id"),"concept:name":"Followup_Prepared",
                     "time:timestamp":ts,"org:resource":"","state":x.get("state_code",""),"source_id":x.get("followup_id",""),"evidence_id":""})
    for x in cmts:
        rows.append({"case:concept:name":x.get("project_id") or x.get("case_id"),"concept:name":"Commitment_"+str(x.get("status","")),
                     "time:timestamp":ts,"org:resource":x.get("owner",""),"state":x.get("status",""),"source_id":x.get("commitment_id",""),"evidence_id":x.get("evidence","")})
    for x in close:
        if x.get("event")=="CLOSE_CONFIRMED":
            rows.append({"case:concept:name":x.get("project_id") or x.get("case_id"),"concept:name":"Case_Closed",
                         "time:timestamp":x.get("ts") or ts,"org:resource":x.get("confirmed_by",""),"state":"CLOSED","source_id":x.get("closure_id",""),"evidence_id":x.get("evidence","")})
    for x in less:
        if x.get("event")=="LESSON_CONFIRMED":
            rows.append({"case:concept:name":x.get("project_id"),"concept:name":"Lesson_Learned",
                         "time:timestamp":x.get("ts") or ts,"org:resource":"","state":"CONFIRMED","source_id":x.get("lesson_id",""),"evidence_id":x.get("evidence","")})
    OUT.mkdir(parents=True,exist_ok=True)
    with EVENTS.open("w",encoding="utf-8-sig",newline="") as f:
        cols=["case:concept:name","concept:name","time:timestamp","org:resource","state","source_id","evidence_id"]
        w=csv.DictWriter(f,fieldnames=cols);w.writeheader();w.writerows(rows)
    return {"kpi":kpi,"event_rows":len(rows),"event_log":str(EVENTS)}
def main():
    ap=argparse.ArgumentParser();ap.add_argument("command",nargs="?",default="build",choices=["build","kpi"]);a=ap.parse_args()
    if a.command=="build":print(json.dumps(build(),ensure_ascii=False,indent=2))
    else:print(json.dumps(loadj(KPI,{}),ensure_ascii=False,indent=2))
    return 0
if __name__=="__main__":raise SystemExit(main())
