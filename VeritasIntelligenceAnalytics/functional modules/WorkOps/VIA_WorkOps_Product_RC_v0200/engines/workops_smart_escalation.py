# -*- coding: utf-8 -*-
"""ENG-064 Smart escalation recommendations only."""
from __future__ import annotations
import argparse,json
from datetime import datetime
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;OUT=ROOT/"out";RESULT=OUT/"escalation_candidates.json"
def j(p,d):
    try:return json.loads(Path(p).read_text(encoding="utf-8-sig"))
    except Exception:return d
def build():
    rows=[]
    for x in j(OUT/"today_queue.json",{"items":[]}).get("items",[]):
        lvl=int(x.get("level",1));wh=float(x.get("waiting_hours") or 0);st=x.get("state_code")
        if lvl>=5 and wh>=24:rows.append({"project_id":x.get("project_id"),"project_name":x.get("project_name"),"code":"CRITICAL_DUE","priority":100,"reason":"Level 5 and waiting >=24h","human_confirmation_required":True})
        elif lvl>=4 and wh>=48:rows.append({"project_id":x.get("project_id"),"project_name":x.get("project_name"),"code":"WARNING_NO_REPLY","priority":80,"reason":"Level 4+ and no reply >=48h","human_confirmation_required":True})
        if st=="OVERDUE":rows.append({"project_id":x.get("project_id"),"project_name":x.get("project_name"),"code":"OVERDUE_WORK","priority":90,"reason":"Work item overdue","human_confirmation_required":True})
    for m in j(OUT/"meeting_t2_guard.json",{"items":[]}).get("items",[]):
        if str(m.get("gate","")).startswith("NOT_READY"):
            rows.append({"project_id":m.get("project_id"),"project_name":m.get("project_name"),"code":"MEETING_NOT_READY","priority":85,"reason":f"{m.get('phase')} meeting readiness {m.get('gate')}","human_confirmation_required":True})
    # de-dupe by project+code
    seen=set();ded=[]
    for x in sorted(rows,key=lambda z:-z["priority"]):
        k=(x.get("project_id"),x["code"])
        if k not in seen:seen.add(k);ded.append(x)
    doc={"version":"v0200","engine_id":"ENG-064","generated_at":datetime.now().astimezone().isoformat(timespec="seconds"),"count":len(ded),"items":ded}
    RESULT.write_text(json.dumps(doc,ensure_ascii=False,indent=2),encoding="utf-8");return doc
def main():
    argparse.ArgumentParser().parse_args();print(json.dumps(build(),ensure_ascii=False,indent=2));return 0
if __name__=="__main__":raise SystemExit(main())
