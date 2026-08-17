# -*- coding: utf-8 -*-
"""ENG-031 Mandatory Reply Builder.
Input: out/followup_state.json
Output: out/followup_pack.json and append-only followup_drafts.jsonl
No Outlook send action exists in this engine.
"""
from __future__ import annotations
import argparse, json
from datetime import datetime
from pathlib import Path
from workops_autocode import next_code

HERE=Path(__file__).resolve().parent
WORKOPS=HERE.parent
OUT=WORKOPS/"out"
PARAMS=HERE/"mandatory_reply_params.json"
STATE=OUT/"followup_state.json"
PACK=OUT/"followup_pack.json"
DRAFTS=OUT/"followup_drafts.jsonl"

def loadj(p,d):
    try:return json.loads(Path(p).read_text(encoding="utf-8-sig"))
    except Exception:return d
def atomic(p,obj):
    Path(p).parent.mkdir(parents=True,exist_ok=True)
    t=Path(str(p)+".tmp")
    t.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding="utf-8")
    t.replace(p)
def build_questions(card, params):
    st=card.get("state_code","UNKNOWN")
    q=params["mandatory_questions"]
    rows=[{"key":"status",**q["status"]}]
    for key in ("delay_reason","plan_b"):
        if st in q[key].get("required_when",[]): rows.append({"key":key,**q[key]})
    return rows
def render_body(card, questions, fup_id):
    lines=[
      f"Project / 專案: {card.get('project_name','')}",
      f"Case ID: {card.get('case_id','')}",
      f"Follow-up ID: {fup_id}","","Please reply using the choices below.",
      "請依下列選項回覆，以便系統正確更新專案狀態。",""
    ]
    for i,q in enumerate(questions,1):
        lines.append(f"Q{i}. {q.get('label_zh')} / {q.get('label_en')}")
        for n,o in enumerate(q.get("options",[]),1):
            lines.append(f"  {n}. {o.get('zh')} / {o.get('en')} [{o.get('key')}]")
        lines.append("")
    lines += ["---",f"==VIA-FOLLOWUP== {fup_id}"]
    return "\n".join(lines)
def build():
    p=loadj(PARAMS,{})
    state=loadj(STATE,{"cards":[]})
    e=p.get("followup_eligibility",{})
    allowed=set(e.get("include_state_codes",[]))
    rows=[]
    for c in state.get("cards",[]):
        if c.get("closed") and e.get("exclude_closed",True): continue
        if int(c.get("level",0))<int(e.get("minimum_level",2)): continue
        if allowed and c.get("state_code") not in allowed: continue
        fup=next_code("FUP")
        qs=build_questions(c,p)
        rows.append({
          "followup_id":fup,"case_id":c.get("case_id"),"thr":c.get("thr"),
          "project_name":c.get("project_name"),"level":c.get("level"),
          "state_code":c.get("state_code"),"recipient_hint":c.get("sender",""),
          "subject":f"{p.get('draft_policy',{}).get('subject_prefix','[VIA Follow-up]')} {c.get('project_name','')}",
          "questions":qs,"body_text":render_body(c,qs,fup),
          "human_confirm_required":True,"send_allowed":False
        })
        if len(rows)>=int(e.get("max_items",50)): break
    doc={"version":"v0100","engine_id":"ENG-031","generated_at":datetime.now().isoformat(timespec="seconds"),
         "count":len(rows),"items":rows}
    atomic(PACK,doc)
    if rows:
        OUT.mkdir(parents=True,exist_ok=True)
        with DRAFTS.open("a",encoding="utf-8") as f:
            for r in rows:f.write(json.dumps(r,ensure_ascii=False)+"\n")
    return doc
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("command",nargs="?",default="build",choices=["build","status"])
    a=ap.parse_args()
    if a.command=="build":
        print(json.dumps(build(),ensure_ascii=False,indent=2))
    else:
        d=loadj(PACK,{})
        print(f"ENG-031 follow-up pack: {d.get('count',0)}")
    return 0
if __name__=="__main__": raise SystemExit(main())
