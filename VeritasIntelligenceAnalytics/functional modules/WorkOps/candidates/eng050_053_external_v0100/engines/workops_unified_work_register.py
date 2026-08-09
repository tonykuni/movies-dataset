# -*- coding: utf-8 -*-
r"""Veritas WorkOps Unified Work Register v0100 (ENG-050)
Read-only derived register. It never replaces WOP/DEC/MLS/CMT/MTG source ledgers.
Output: out/unified_work_register.json + .csv
"""
from __future__ import annotations
import argparse,csv,io,json
from collections import Counter
from workops_control_common import *

RESULT=OUT/"unified_work_register.json"; CSV=OUT/"unified_work_register.csv"

def add(rows,typ,native,wop,title,owner="",status="",due="",next_action="",evidence="",source="",risk=""):
    rows.append({
      "work_key":f"{typ}:{native}","type":typ,"native_id":native,"wop":wop or "",
      "project_name":project_label(wop) if wop else "UNASSIGNED","title":title or native,
      "owner":owner or "","status":status or "UNKNOWN","due":due or "",
      "overdue":due_overdue(due,status),"next_action":next_action or "",
      "evidence":evidence or "","source":source or "","risk":risk or ""
    })

def build():
    rows=[]; t2w=thr2wop()
    for r in csvrows(OUT/"pending.csv"):
        thr=r.get("ThrID") or r.get("THR") or ""
        w=t2w.get(thr,"")
        try:wd=int(r.get("WaitingDays") or 0)
        except Exception:wd=0
        add(rows,"FOLLOWUP",thr,w,r.get("Subject") or "Pending follow-up",
            r.get("SenderEmail") or "", "WAITING_REPLY","",
            "Follow up" if thr else "Review routing",thr,"pending.csv",
            "T3" if wd>=7 else "")
    rs=jload(OUT/"reply_status.json",{})
    for thr,s in (rs.get("status",{}) or {}).items():
        add(rows,"THREAD",thr,t2w.get(thr,""),"Mail thread state","",s.get("status",""),
            "","Review latest reply",s.get("evidence",""),"reply_status.json",
            "RISK" if (rs.get("flags",{}).get(thr,{}) or {}).get("risk") else "")
    for d in decision_rows():
        w=wop_from_source(d.get("source"))
        add(rows,"DECISION",d.get("decision_id",""),w,d.get("what",""),d.get("owner",""),
            d.get("status",""),d.get("due",""),"Complete / update decision",
            d.get("source",""),"decision_log", "BLOCKED" if d.get("status")=="BLOCKED" else "")
    for mid,m in (jload(OUT/"milestones.json",{}).get("items",{}) or {}).items():
        add(rows,"MILESTONE",mid,m.get("wop",""),m.get("name",""),m.get("owner",""),
            m.get("status",""),m.get("due",""),"Complete milestone",
            m.get("evidence",""),"milestones.json")
    for cid,c in (jload(OUT/"commitments.json",{}).get("items",{}) or {}).items():
        add(rows,"COMMITMENT",cid,c.get("wop",""),c.get("what",""),c.get("owner",""),
            c.get("status",""),c.get("due",""),"Fulfill commitment",
            c.get("evidence",""),c.get("source_ref","") or "commitments.json",
            "BLOCKED" if c.get("status")=="BLOCKED" else "")
    for a in jload(OUT/"meeting_actions.json",{}).get("open_actions",[]) or []:
        native=a.get("action_id") or f"{a.get('mtg','MTG')}:{len(rows)+1}"
        w=wop_from_source(a.get("source") or a.get("thr") or "")
        add(rows,"MEETING_ACTION",native,w,a.get("item","Meeting action"),a.get("owner",""),
            a.get("status","OPEN"),a.get("due",""),"Complete meeting action",
            a.get("mtg",""),"meeting_actions.json")
    for c in jload(OUT/"closure_candidates.json",{}).get("candidates",[]) or []:
        add(rows,"CLOSURE_CANDIDATE",c.get("wop",""),c.get("wop",""),"Closure review","",
            "READY_TO_CONFIRM","","Human closure confirmation","; ".join(c.get("evidence",[])),
            "closure_candidates.json")
    for cid,c in (jload(OUT/"closures.json",{}).get("items",{}) or {}).items():
        add(rows,"CLOSURE",cid,c.get("wop",""),"Closed: "+str(c.get("reason","")),"",
            "CLOSED",c.get("ts","")[:10],"",c.get("reason",""),"closures.json")
    counts=Counter(x["type"] for x in rows)
    openish=[x for x in rows if x["status"] not in ("DONE","COMPLETED","FULFILLED","CLOSED","CANCELLED","已完成")]
    doc={"version":"v0100","engine_id":"ENG-050","generated_at":now(),"count":len(rows),
         "open_count":len(openish),"overdue_count":sum(bool(x["overdue"]) for x in rows),
         "by_type":dict(sorted(counts.items())),"items":rows,
         "governance":"DERIVED_ONLY / SOURCE_LEDGERS_REMAIN_CANON"}
    atomic_json(RESULT,doc)
    with io.open(CSV,"w",encoding="utf-8-sig",newline="") as f:
        cols=["work_key","type","native_id","wop","project_name","title","owner","status","due","overdue","next_action","evidence","source","risk"]
        w=csv.DictWriter(f,fieldnames=cols);w.writeheader();w.writerows([{k:x.get(k,"") for k in cols} for x in rows])
    return doc

def main():
    argparse.ArgumentParser().parse_args();d=build()
    print(json.dumps({k:d[k] for k in ("engine_id","count","open_count","overdue_count","by_type")},ensure_ascii=False,indent=2))
if __name__=="__main__":main()
