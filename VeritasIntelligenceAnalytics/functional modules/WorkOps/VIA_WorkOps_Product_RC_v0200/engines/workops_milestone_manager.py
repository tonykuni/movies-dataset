# -*- coding: utf-8 -*-
"""ENG-063 Append-only project milestone manager."""
from __future__ import annotations
import argparse,json
from datetime import datetime
from pathlib import Path
from workops_autocode import next_code
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;OUT=ROOT/"out";REG=OUT/"milestone_registry.jsonl";SUMMARY=OUT/"milestone_summary.json"
def jl(p):
    rows=[]
    if not p.exists():return rows
    for ln in p.read_text(encoding="utf-8",errors="replace").splitlines():
        try:rows.append(json.loads(ln))
        except Exception:pass
    return rows
def append(o):
    OUT.mkdir(exist_ok=True)
    with REG.open("a",encoding="utf-8") as f:f.write(json.dumps(o,ensure_ascii=False)+"\n")
def current():
    cur={}
    for e in jl(REG):
        mid=e.get("milestone_id")
        if not mid:continue
        x=cur.get(mid,{})
        if e.get("event")=="CREATE":x.update(e)
        elif e.get("event")=="UPDATE_TARGET":x["target_date"]=e.get("target_date");x["target_change_reason"]=e.get("reason")
        elif e.get("event")=="COMPLETE":x["status"]="COMPLETED";x["actual_date"]=e.get("actual_date");x["evidence"]=e.get("evidence")
        elif e.get("event")=="REOPEN":x["status"]="OPEN";x["reopen_reason"]=e.get("reason")
        cur[mid]=x
    return cur
def build():
    cur=current();projects={}
    for x in cur.values():
        p=projects.setdefault(x.get("project_id"),{"project_id":x.get("project_id"),"milestones":[]});p["milestones"].append(x)
    for p in projects.values():
        ms=p["milestones"];w=sum(float(x.get("weight") or 1) for x in ms);done=sum(float(x.get("weight") or 1) for x in ms if x.get("status")=="COMPLETED")
        p["weighted_progress_pct"]=round(100*done/max(1,w),1);p["total"]=len(ms);p["completed"]=sum(x.get("status")=="COMPLETED" for x in ms)
    doc={"version":"v0200","engine_id":"ENG-063","generated_at":datetime.now().astimezone().isoformat(timespec="seconds"),"projects":list(projects.values())}
    SUMMARY.write_text(json.dumps(doc,ensure_ascii=False,indent=2),encoding="utf-8");return doc
def create(project_id,name,target_date,owner="",weight=1.0):
    e={"event":"CREATE","milestone_id":next_code("MLS"),"project_id":project_id,"name":name,"target_date":target_date,"owner":owner,"weight":weight,"status":"OPEN","ts":datetime.now().astimezone().isoformat(timespec="seconds"),"human_confirmed":True};append(e);build();return e
def complete(mid,evidence,actual_date=""):
    if mid not in current():raise RuntimeError("UNKNOWN_MILESTONE")
    if not evidence:raise RuntimeError("EVIDENCE_REQUIRED")
    e={"event":"COMPLETE","milestone_id":mid,"actual_date":actual_date or datetime.now().date().isoformat(),"evidence":evidence,"ts":datetime.now().astimezone().isoformat(timespec="seconds"),"human_confirmed":True};append(e);build();return e
def main():
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest="cmd",required=True);sub.add_parser("build")
    c=sub.add_parser("create");c.add_argument("project_id");c.add_argument("name");c.add_argument("target_date");c.add_argument("--owner",default="");c.add_argument("--weight",type=float,default=1)
    d=sub.add_parser("complete");d.add_argument("milestone_id");d.add_argument("--evidence",required=True);d.add_argument("--actual-date",default="");a=ap.parse_args()
    o=build() if a.cmd=="build" else create(a.project_id,a.name,a.target_date,a.owner,a.weight) if a.cmd=="create" else complete(a.milestone_id,a.evidence,a.actual_date)
    print(json.dumps(o,ensure_ascii=False,indent=2));return 0
if __name__=="__main__":raise SystemExit(main())
