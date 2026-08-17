# -*- coding: utf-8 -*-
"""ENG-062 Stakeholder registry + RACI candidates. Role inference is never canonical until confirmed."""
from __future__ import annotations
import argparse,json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from workops_autocode import next_code
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;OUT=ROOT/"out";REG=OUT/"stakeholder_registry.jsonl";ROLE=OUT/"stakeholder_role_registry.jsonl";RESULT=OUT/"stakeholder_matrix.json"
def jl(p):
    rows=[]
    if not Path(p).exists():return rows
    for ln in Path(p).read_text(encoding="utf-8",errors="replace").splitlines():
        try:rows.append(json.loads(ln))
        except Exception:pass
    return rows
def jload(p,d):
    try:return json.loads(Path(p).read_text(encoding="utf-8-sig"))
    except Exception:return d
def append(p,o):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open("a",encoding="utf-8") as f:f.write(json.dumps(o,ensure_ascii=False)+"\n")
def confirmed_projects():
    return {r.get("conversation_id"):r.get("project_id") for r in jl(OUT/"classification_memory.jsonl") if r.get("decision")=="ACCEPT"}
def stakeholder_ids():
    m={}
    for r in jl(REG):
        if r.get("email"):m[r["email"].lower()]=r.get("stakeholder_id")
    return m
def sid(email,name=""):
    e=(email or "").lower().strip();m=stakeholder_ids()
    if e in m:return m[e]
    x=next_code("STK");append(REG,{"event":"REGISTER","stakeholder_id":x,"email":e,"display_name":name or e,"ts":datetime.now().astimezone().isoformat(timespec="seconds")});return x
def confirmed_roles():
    cur={}
    for r in jl(ROLE):
        if r.get("event")=="CONFIRM_ROLE":cur[(r.get("project_id"),r.get("stakeholder_id"))]=r.get("role")
    return cur
def build():
    pm=confirmed_projects();stats=defaultdict(lambda:defaultdict(lambda:{"sent":0,"to":0,"cc":0,"names":set()}))
    for x in jl(OUT/"email_raw_graph.jsonl"):
        pid=pm.get(x.get("conversation_id"))
        if not pid:continue
        se=(x.get("sender_email") or "").lower()
        if se:stats[pid][se]["sent"]+=1;stats[pid][se]["names"].add(x.get("sender_name") or se)
        for e in x.get("to_list") or []:stats[pid][e.lower()]["to"]+=1
        for e in x.get("cc_list") or []:stats[pid][e.lower()]["cc"]+=1
    cards={x.get("project_id"):x for x in jload(OUT/"project_cards.json",{"cards":[]}).get("cards",[])}
    confirmed=confirmed_roles();rows=[]
    for pid,people in stats.items():
        members=[]
        owner=(cards.get(pid,{}).get("owner") or "").lower()
        for email,s in people.items():
            stid=sid(email,next(iter(s["names"]),email));total=s["sent"]+s["to"]+s["cc"];ccr=s["cc"]/max(1,total)
            if owner and email==owner:role="RESPONSIBLE";conf=.95
            elif ccr>=.70:role="INFORMED";conf=.75
            elif ccr>=.40:role="CONSULTED";conf=.70
            elif s["sent"]>=max(s["to"],s["cc"],1):role="RESPONSIBLE";conf=.65
            else:role="PARTICIPANT";conf=.55
            cr=confirmed.get((pid,stid))
            members.append({"stakeholder_id":stid,"email":email,"display_name":next(iter(s["names"]),email),
             "sent_count":s["sent"],"to_count":s["to"],"cc_count":s["cc"],"candidate_role":role,"candidate_confidence":conf,
             "confirmed_role":cr,"effective_role":cr or role,"human_confirmation_required":cr is None})
        rows.append({"project_id":pid,"project_name":cards.get(pid,{}).get("project_name") or pid,"members":sorted(members,key=lambda z:-(z["sent_count"]+z["to_count"]+z["cc_count"]))})
    doc={"version":"v0200","engine_id":"ENG-062","generated_at":datetime.now().astimezone().isoformat(timespec="seconds"),"projects":rows}
    RESULT.write_text(json.dumps(doc,ensure_ascii=False,indent=2),encoding="utf-8");return doc
def confirm(project_id,stakeholder_id,role):
    if role not in ("RESPONSIBLE","ACCOUNTABLE","CONSULTED","INFORMED","PARTICIPANT"):raise RuntimeError("INVALID_ROLE")
    append(ROLE,{"event":"CONFIRM_ROLE","project_id":project_id,"stakeholder_id":stakeholder_id,"role":role,"human_confirmed":True,"ts":datetime.now().astimezone().isoformat(timespec="seconds")})
    return {"gate":"PASS","project_id":project_id,"stakeholder_id":stakeholder_id,"role":role}
def main():
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest="cmd",required=True);sub.add_parser("build")
    c=sub.add_parser("confirm");c.add_argument("project_id");c.add_argument("stakeholder_id");c.add_argument("role");a=ap.parse_args()
    o=build() if a.cmd=="build" else confirm(a.project_id,a.stakeholder_id,a.role);print(json.dumps(o,ensure_ascii=False,indent=2));return 0
if __name__=="__main__":raise SystemExit(main())
