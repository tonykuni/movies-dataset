# -*- coding: utf-8 -*-
"""ENG-043 Commitment Fulfillment Engine.
Candidate -> human confirmation -> immutable CMT id -> evaluate -> fulfill/revise with evidence.
"""
from __future__ import annotations
import argparse,json
from datetime import datetime, timedelta
from pathlib import Path
try:
    from zoneinfo import ZoneInfo
except Exception:
    ZoneInfo=None
from workops_autocode import next_code

HERE=Path(__file__).resolve().parent;WORKOPS=HERE.parent;OUT=WORKOPS/"out"
PARAMS=HERE/"commitment_fulfillment_params.json";STATE=OUT/"followup_state.json"
INPUT=OUT/"commitment_candidates_input.jsonl";CAND=OUT/"commitment_candidates.json"
REG=OUT/"commitment_registry.jsonl";STATUS=OUT/"commitment_status.json";KPI=OUT/"commitment_kpi.json"

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
def append(p,o):
    OUT.mkdir(parents=True,exist_ok=True)
    with Path(p).open("a",encoding="utf-8") as f:f.write(json.dumps(o,ensure_ascii=False)+"\n")
def now():
    tz=ZoneInfo("Asia/Taipei") if ZoneInfo else None
    return datetime.now(tz=tz) if tz else datetime.now()
def parse_dt(s):
    if not s:return None
    s=str(s).strip()
    try:
        d=datetime.fromisoformat(s)
        if d.tzinfo is None and ZoneInfo:d=d.replace(tzinfo=ZoneInfo("Asia/Taipei"))
        return d
    except Exception:
        try:
            d=datetime.strptime(s[:10],"%Y-%m-%d").replace(hour=17)
            if ZoneInfo:d=d.replace(tzinfo=ZoneInfo("Asia/Taipei"))
            return d
        except Exception:return None
def current_registry():
    cur={}
    for e in loadjl(REG):
        cid=e.get("commitment_id")
        if not cid:continue
        x=cur.get(cid,{})
        if e.get("event")=="REGISTER":
            x.update(e)
            x["current_due_at"]=e.get("due_at")
            x["status_override"]=None
        elif e.get("event")=="REVISE_DUE":
            x["current_due_at"]=e.get("new_due_at")
            x["last_revision_reason"]=e.get("reason")
            x["last_revision_evidence"]=e.get("evidence")
        elif e.get("event")=="FULFILL":
            x["fulfilled_at"]=e.get("ts");x["fulfillment_evidence"]=e.get("evidence");x["status_override"]="FULFILLED"
        elif e.get("event")=="CANCEL":
            x["status_override"]="CANCELLED";x["cancel_reason"]=e.get("reason")
        cur[cid]=x
    return cur
def scan():
    p=loadj(PARAMS,{})
    rows=[];seen=set()
    # Explicit upstream candidate feed.
    for x in loadjl(INPUT):
        k=(x.get("source_id"),x.get("commitment_text"),x.get("due_at"))
        if k in seen:continue
        seen.add(k);rows.append({**x,"candidate_source":"explicit_input","human_confirmation_required":True})
    # Derive candidates from structured follow-up state only when ETA exists.
    for c in loadj(STATE,{"cards":[]}).get("cards",[]):
        due=c.get("revised_eta") or c.get("eta")
        owner=c.get("owner")
        if not due or not owner:continue
        text=c.get("commitment_text") or c.get("next_action") or c.get("issue") or "Complete current committed action"
        evidence=c.get("evidence") or c.get("evidence_id") or c.get("source_id") or c.get("thr") or ""
        k=(c.get("project_id") or c.get("case_id"),text,due)
        if k in seen:continue
        seen.add(k)
        rows.append({
          "project_id":c.get("project_id"),"case_id":c.get("case_id"),"thr":c.get("thr"),
          "project_name":c.get("project_name"),"owner":owner,"due_at":due,
          "commitment_text":text,"evidence":evidence,
          "candidate_source":"followup_state_derived",
          "human_confirmation_required":True,
          "confidence":0.70 if evidence else 0.55
        })
    doc={"version":"v0100","engine_id":"ENG-043","generated_at":now().isoformat(timespec="seconds"),
         "count":len(rows),"items":rows}
    atomic(CAND,doc);return doc
def confirm(index:int):
    d=loadj(CAND,{"items":[]})
    if index<0 or index>=len(d.get("items",[])):raise SystemExit("candidate index out of range")
    x=d["items"][index]
    missing=[]
    if not (x.get("project_id") or x.get("case_id")):missing.append("project_id_or_case")
    for f in ("owner","due_at","commitment_text","evidence"):
        if not x.get(f):missing.append(f)
    if missing:raise SystemExit("cannot register; missing: "+",".join(missing))
    evt={"event":"REGISTER","ts":now().isoformat(timespec="seconds"),"commitment_id":next_code("CMT"),
         "project_id":x.get("project_id"),"case_id":x.get("case_id"),"thr":x.get("thr"),
         "project_name":x.get("project_name"),"owner":x.get("owner"),"due_at":x.get("due_at"),
         "commitment_text":x.get("commitment_text"),"evidence":x.get("evidence"),
         "source_candidate":x.get("candidate_source"),"human_confirmed":True}
    append(REG,evt);evaluate();print(json.dumps(evt,ensure_ascii=False,indent=2));return 0
def evaluate():
    p=loadj(PARAMS,{})
    current=current_registry();nowdt=now();rows=[]
    due_soon=float(p.get("status_rules",{}).get("due_soon_hours",24))
    for cid,x in current.items():
        if x.get("status_override") in ("FULFILLED","CANCELLED"):
            st=x["status_override"];hours=None
        else:
            d=parse_dt(x.get("current_due_at") or x.get("due_at"))
            if not d:st="UNKNOWN_DUE";hours=None
            else:
                hours=(d-nowdt).total_seconds()/3600
                if hours<0:st="OVERDUE"
                elif hours<=due_soon:st="DUE_SOON"
                else:st="OPEN"
        rows.append({
          "commitment_id":cid,"project_id":x.get("project_id"),"case_id":x.get("case_id"),"thr":x.get("thr"),
          "project_name":x.get("project_name"),"owner":x.get("owner"),
          "commitment_text":x.get("commitment_text"),"due_at":x.get("current_due_at") or x.get("due_at"),
          "original_due_at":x.get("due_at"),"status":st,"hours_to_due":None if hours is None else round(hours,1),
          "evidence":x.get("evidence"),"fulfilled_at":x.get("fulfilled_at"),
          "fulfillment_evidence":x.get("fulfillment_evidence")
        })
    rows.sort(key=lambda z:({"OVERDUE":0,"DUE_SOON":1,"OPEN":2,"UNKNOWN_DUE":3,"FULFILLED":4,"CANCELLED":5}.get(z["status"],9), z.get("due_at") or ""))
    counts={k:sum(x["status"]==k for x in rows) for k in ("OPEN","DUE_SOON","OVERDUE","FULFILLED","CANCELLED","UNKNOWN_DUE")}
    denom=counts["FULFILLED"]+counts["OVERDUE"]
    fulfillment_rate=round(counts["FULFILLED"]/denom*100,1) if denom else None
    doc={"version":"v0100","engine_id":"ENG-043","generated_at":nowdt.isoformat(timespec="seconds"),
         "count":len(rows),"counts":counts,"items":rows}
    atomic(STATUS,doc)
    atomic(KPI,{"version":"v0100","generated_at":doc["generated_at"],"registered":len(rows),
                "fulfilled":counts["FULFILLED"],"overdue":counts["OVERDUE"],"due_soon":counts["DUE_SOON"],
                "fulfillment_rate_pct":fulfillment_rate})
    return doc
def fulfill(cid,evidence):
    if cid not in current_registry():raise SystemExit("unknown commitment_id")
    if not evidence:raise SystemExit("evidence required")
    append(REG,{"event":"FULFILL","ts":now().isoformat(timespec="seconds"),"commitment_id":cid,"evidence":evidence,"human_confirmed":True})
    evaluate();return 0
def revise(cid,new_due,reason,evidence):
    if cid not in current_registry():raise SystemExit("unknown commitment_id")
    if not parse_dt(new_due):raise SystemExit("invalid new due date/time")
    if not reason or not evidence:raise SystemExit("reason and evidence required")
    append(REG,{"event":"REVISE_DUE","ts":now().isoformat(timespec="seconds"),"commitment_id":cid,
                "new_due_at":new_due,"reason":reason,"evidence":evidence,"human_confirmed":True})
    evaluate();return 0
def main():
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest="cmd",required=True)
    sub.add_parser("scan")
    c=sub.add_parser("confirm");c.add_argument("index",type=int)
    sub.add_parser("evaluate")
    f=sub.add_parser("fulfill");f.add_argument("commitment_id");f.add_argument("--evidence",required=True)
    r=sub.add_parser("revise");r.add_argument("commitment_id");r.add_argument("--new-due",required=True);r.add_argument("--reason",required=True);r.add_argument("--evidence",required=True)
    sub.add_parser("status")
    a=ap.parse_args()
    if a.cmd=="scan":print(json.dumps(scan(),ensure_ascii=False,indent=2));return 0
    if a.cmd=="confirm":return confirm(a.index)
    if a.cmd=="evaluate":print(json.dumps(evaluate(),ensure_ascii=False,indent=2));return 0
    if a.cmd=="fulfill":return fulfill(a.commitment_id,a.evidence)
    if a.cmd=="revise":return revise(a.commitment_id,a.new_due,a.reason,a.evidence)
    print(json.dumps(loadj(STATUS,{}),ensure_ascii=False,indent=2));return 0
if __name__=="__main__":raise SystemExit(main())
