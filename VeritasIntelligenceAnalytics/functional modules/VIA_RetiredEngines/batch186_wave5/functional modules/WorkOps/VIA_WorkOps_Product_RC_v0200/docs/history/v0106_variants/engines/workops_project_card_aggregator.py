# -*- coding: utf-8 -*-
"""ENG-038 Project Card Aggregator.
Joins follow-up state + missing guard + project registry + latest follow-up pack into UI-ready JSON.
"""
from __future__ import annotations
import argparse,json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
HERE=Path(__file__).resolve().parent; WORKOPS=HERE.parent; OUT=WORKOPS/"out"
PARAMS=HERE/"project_card_params.json"; STATE=OUT/"followup_state.json"; MISSING=OUT/"missing_information.json"
PROJECTS=OUT/"project_registry.jsonl"; PACK=OUT/"daily_followup_pack.json"
CARDS=OUT/"project_cards.json"; SUMMARY=OUT/"project_cards_summary.json"
def loadj(p,d):
    try:return json.loads(Path(p).read_text(encoding="utf-8-sig"))
    except Exception:return d
def loadjl(p):
    rows=[]
    if not Path(p).exists():return rows
    for ln in Path(p).read_text(encoding="utf-8",errors="replace").splitlines():
        try: rows.append(json.loads(ln))
        except Exception: pass
    return rows
def atomic(p,o):
    Path(p).parent.mkdir(parents=True,exist_ok=True)
    t=Path(str(p)+".tmp"); t.write_text(json.dumps(o,ensure_ascii=False,indent=2),encoding="utf-8"); t.replace(p)
def latest_projects():
    cur={}
    for r in loadjl(PROJECTS):
        pid=r.get("project_id")
        if not pid:continue
        old=cur.get(pid,{})
        old.update({k:v for k,v in r.items() if v is not None})
        cur[pid]=old
    return cur
def build():
    p=loadj(PARAMS,{})
    state=loadj(STATE,{"cards":[]}); miss=loadj(MISSING,{"items":[]}); pack=loadj(PACK,{"items":[]})
    projects=latest_projects()
    mb=defaultdict(list)
    for m in miss.get("items",[]): mb[m.get("project_id") or m.get("case_id")].append(m)
    pb=defaultdict(list)
    for f in pack.get("items",[]): pb[f.get("project_id") or f.get("case_id")].append(f)
    cards=[]
    for c in state.get("cards",[]):
        pid=c.get("project_id",""); key=pid or c.get("case_id")
        pr=projects.get(pid,{})
        m=(mb.get(key) or [{}])[0]
        f=(pb.get(key) or [{}])[0]
        level=int(c.get("level",1))
        cards.append({
          "project_id":pid,"case_id":c.get("case_id"),"thr":c.get("thr"),
          "project_name":c.get("project_name") or pr.get("display_name") or pid or c.get("case_id"),
          "display_name":pr.get("display_name"),"state_code":c.get("state_code"),"level":level,
          "status_color":p.get("status_palette",{}).get(str(level),"#4C72B0"),
          "flash":level>=4 and not c.get("closed"),"closed":bool(c.get("closed")),
          "owner":c.get("owner",""),"due":c.get("due") or c.get("eta") or c.get("revised_eta"),
          "progress_pct":c.get("progress_pct"),"waiting_hours":c.get("waiting_hours",0),
          "issue":c.get("issue") or c.get("reason") or "",
          "next_action":c.get("next_action") or "",
          "missing_fields":m.get("missing",[])[:int(p.get("card",{}).get("top_missing_fields",3))],
          "missing_control_score":m.get("control_score",0),
          "followup_ready":bool(f),"followup_id":f.get("followup_id"),"template_key":f.get("template_key"),
          "language":f.get("language"),"close_candidate":bool(c.get("close_candidate") or c.get("state_code")=="DONE_CANDIDATE")
        })
    cards.sort(key=lambda x:(x["closed"],-x["level"],-int(x.get("waiting_hours") or 0)))
    summary={"active":sum(not x["closed"] for x in cards),
             "warning":sum(x["level"]==4 and not x["closed"] for x in cards),
             "critical":sum(x["level"]==5 and not x["closed"] for x in cards),
             "followup_ready":sum(x["followup_ready"] for x in cards),
             "close_candidates":sum(x["close_candidate"] and not x["closed"] for x in cards)}
    doc={"version":"v0100","engine_id":"ENG-038","generated_at":datetime.now().isoformat(timespec="seconds"),"count":len(cards),"cards":cards}
    atomic(CARDS,doc); atomic(SUMMARY,summary); return doc
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("command",nargs="?",default="build",choices=["build","status"])
    a=ap.parse_args()
    if a.command=="build":print(json.dumps(build(),ensure_ascii=False,indent=2))
    else:
        d=loadj(CARDS,{})
        print(f"ENG-038 project cards: {d.get('count',0)}")
    return 0
if __name__=="__main__": raise SystemExit(main())
