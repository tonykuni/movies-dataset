# -*- coding: utf-8 -*-
r"""Veritas WorkOps Commitment Intelligence v0100 (ENG-051)
Tracks explicit promises as CMT-####. Structured sources become candidates only.
No email-NLP guess is auto-promoted. Create/accept/reschedule/fulfill are human commands.
"""
from __future__ import annotations
import argparse,json
from workops_control_common import *
P=OUT/"commitments.json"; CAND=OUT/"commitment_candidates.json"

def load(): return jload(P,{"seq":0,"items":{}})
def save(d): atomic_json(P,d)
def existing_source_refs(d): return {str(x.get("source_ref","")) for x in d.get("items",{}).values() if x.get("source_ref")}
def candidates():
    d=load();seen=existing_source_refs(d);items=[]
    for x in decision_rows():
        did=x.get("decision_id","")
        if not did or did in seen or x.get("status")=="DONE":continue
        w=wop_from_source(x.get("source"))
        if x.get("owner") and (x.get("due") or x.get("what")) and w:
            items.append({"candidate_id":f"DEC:{did}","source_ref":did,"source_type":"DECISION","wop":w,
                          "what":x.get("what",""),"owner":x.get("owner",""),"due":x.get("due",""),
                          "status":"OPEN","confidence":"STRUCTURED_SOURCE","human_confirmation_required":True})
    for mid,m in (jload(OUT/"milestones.json",{}).get("items",{}) or {}).items():
        if mid in seen or m.get("status")=="COMPLETED":continue
        if m.get("owner") and m.get("due") and m.get("wop") in wop_registry():
            items.append({"candidate_id":f"MLS:{mid}","source_ref":mid,"source_type":"MILESTONE","wop":m.get("wop",""),
                          "what":m.get("name",""),"owner":m.get("owner",""),"due":m.get("due",""),
                          "status":"OPEN","confidence":"STRUCTURED_SOURCE","human_confirmation_required":True})
    doc={"version":"v0100","engine_id":"ENG-051","generated_at":now(),"count":len(items),"items":items}
    atomic_json(CAND,doc);return doc
def create(wop,what,owner,due="",source_ref=""):
    if not wop.startswith("WOP-") or wop not in wop_registry():raise SystemExit("valid existing WOP required")
    if not what or not owner:raise SystemExit("what and owner required")
    d=load()
    if source_ref and source_ref in existing_source_refs(d):
        old=next((k for k,v in d["items"].items() if v.get("source_ref")==source_ref),None)
        return {"gate":"ALREADY_EXISTS","commitment_id":old}
    d["seq"]+=1;cid="CMT-%04d"%d["seq"]
    d["items"][cid]={"wop":wop,"what":what,"owner":owner,"due":due,"status":"OPEN","source_ref":source_ref,
                     "created":now(),"evidence":"","history":[{"ts":now(),"ev":"CREATE","human_confirmed":True}]}
    save(d);return {"gate":"PASS","commitment_id":cid,**d["items"][cid]}
def accept(candidate_id):
    c=next((x for x in candidates()["items"] if x.get("candidate_id")==candidate_id),None)
    if not c:raise SystemExit("candidate not found")
    return create(c["wop"],c["what"],c["owner"],c["due"],c["source_ref"])
def state(cid,status,reason=""):
    d=load();it=d["items"].get(cid)
    if not it:raise SystemExit("unknown commitment")
    allowed={"OPEN","IN_PROGRESS","WAITING","BLOCKED","CANCELLED"}
    if status not in allowed:raise SystemExit("invalid status")
    it["status"]=status;append_hist(it,"STATUS",f"{status}:{reason}");save(d)
    return {"gate":"PASS","commitment_id":cid,"status":status}
def reschedule(cid,due,reason):
    if not reason:raise SystemExit("reschedule reason required")
    d=load();it=d["items"].get(cid)
    if not it:raise SystemExit("unknown commitment")
    old=it.get("due","");it["due"]=due;append_hist(it,"RESCHEDULE",f"{old}->{due};{reason}");save(d)
    return {"gate":"PASS","commitment_id":cid,"due":due}
def fulfill(cid,evidence):
    if not evidence:raise SystemExit("evidence required")
    d=load();it=d["items"].get(cid)
    if not it:raise SystemExit("unknown commitment")
    it["status"]="FULFILLED";it["fulfilled_at"]=now();it["evidence"]=evidence
    append_hist(it,"FULFILL",evidence);save(d)
    return {"gate":"PASS","commitment_id":cid,"status":"FULFILLED","evidence":evidence}
def status_doc():
    d=load();items=[]
    for cid,x in d["items"].items():
        items.append({"commitment_id":cid,**x,"overdue":due_overdue(x.get("due",""),x.get("status",""))})
    return {"version":"v0100","engine_id":"ENG-051","generated_at":now(),"count":len(items),
            "open":sum(x["status"] not in ("FULFILLED","CANCELLED") for x in items),
            "overdue":sum(bool(x["overdue"]) for x in items),"items":items}
def main():
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest="cmd",required=True)
    sub.add_parser("candidates");sub.add_parser("status")
    c=sub.add_parser("create");c.add_argument("wop");c.add_argument("what");c.add_argument("owner");c.add_argument("--due",default="");c.add_argument("--source",default="")
    a=sub.add_parser("accept");a.add_argument("candidate_id")
    s=sub.add_parser("state");s.add_argument("commitment_id");s.add_argument("status");s.add_argument("--reason",default="")
    r=sub.add_parser("reschedule");r.add_argument("commitment_id");r.add_argument("due");r.add_argument("--reason",required=True)
    f=sub.add_parser("fulfill");f.add_argument("commitment_id");f.add_argument("--evidence",required=True)
    z=ap.parse_args()
    if z.cmd=="candidates":o=candidates()
    elif z.cmd=="status":o=status_doc()
    elif z.cmd=="create":o=create(z.wop,z.what,z.owner,z.due,z.source)
    elif z.cmd=="accept":o=accept(z.candidate_id)
    elif z.cmd=="state":o=state(z.commitment_id,z.status,z.reason)
    elif z.cmd=="reschedule":o=reschedule(z.commitment_id,z.due,z.reason)
    else:o=fulfill(z.commitment_id,z.evidence)
    print(json.dumps(o,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
