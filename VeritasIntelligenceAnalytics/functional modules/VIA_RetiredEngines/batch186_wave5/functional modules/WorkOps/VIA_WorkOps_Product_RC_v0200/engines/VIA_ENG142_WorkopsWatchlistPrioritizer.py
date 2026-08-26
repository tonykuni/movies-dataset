# -*- coding: utf-8 -*-
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(全引擎導入令 2026-08-18;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # accel_map/fetch/pip_install/run_fast
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====
import argparse,json
from datetime import datetime
from pathlib import Path
HERE=Path(__file__).resolve().parent;WORKOPS=HERE.parent;OUT=WORKOPS/"out"
PARAMS=HERE/"watchlist_prioritizer_params.json";CARDS=OUT/"project_cards.json";CLOSURE=OUT/"closure_candidates.json";WATCH=OUT/"watchlist.json";TODAY=OUT/"today_queue.json"
def loadj(p,d):
    try:return json.loads(Path(p).read_text(encoding="utf-8-sig"))
    except Exception:return d
def atomic(p,o):
    Path(p).parent.mkdir(parents=True,exist_ok=True);t=Path(str(p)+".tmp");t.write_text(json.dumps(o,ensure_ascii=False,indent=2),encoding="utf-8");t.replace(p)
def score(c,w):
    s=int(c.get("level",1))*int(w.get("level",10));wh=float(c.get("waiting_hours") or 0)
    s+=int(w.get("waiting_72h",8)) if wh>=72 else int(w.get("waiting_48h",5)) if wh>=48 else int(w.get("waiting_24h",2)) if wh>=24 else 0
    s+=len(c.get("missing_fields") or [])*int(w.get("missing_control_point",4))
    if c.get("close_candidate"):s+=int(w.get("close_candidate",1))
    if c.get("followup_ready"):s+=int(w.get("followup_ready",2))
    if c.get("state_code")=="OVERDUE":s+=int(w.get("overdue_state",8))
    if c.get("state_code")=="BLOCKED":s+=int(w.get("blocked_state",7))
    return s
def build():
    p=loadj(PARAMS,{}); cards=loadj(CARDS,{"cards":[]}).get("cards",[]);cl=loadj(CLOSURE,{"items":[]})
    cr={(x.get("project_id") or x.get("case_id") or x.get("thr")):x.get("ready_for_human_confirmation") for x in cl.get("items",[])}
    rows=[];labels=p.get("labels",{})
    for c in cards:
        if c.get("closed"):continue
        k=c.get("project_id") or c.get("case_id") or c.get("thr")
        acts=list(p.get("action_rules",{}).get(c.get("state_code"),[]))
        if c.get("close_candidate") and "CONFIRM_CLOSE" not in acts:acts.append("CONFIRM_CLOSE")
        rows.append({**c,"priority_score":score(c,p.get("weights",{})),
        "recommended_actions":[{"key":a,"labels":labels.get(a,{})} for a in acts],"close_ready":bool(cr.get(k))})
    rows.sort(key=lambda x:(-x["priority_score"],-int(x.get("level",1)),-int(x.get("waiting_hours") or 0)))
    q=p.get("queues",{});today=rows[:int(q.get("today_max",12))];watch=[x for x in rows if int(x.get("level",1))>=int(q.get("watchlist_min_level",4))][:int(q.get("watchlist_max",20))]
    now=datetime.now().isoformat(timespec="seconds");td={"version":"v0100","engine_id":"ENG-039","generated_at":now,"count":len(today),"items":today};wa={"version":"v0100","engine_id":"ENG-039","generated_at":now,"count":len(watch),"items":watch}
    atomic(TODAY,td);atomic(WATCH,wa);return td,wa
def main():
    ap=argparse.ArgumentParser();ap.add_argument("command",nargs="?",default="build",choices=["build","today","watchlist"]);a=ap.parse_args()
    if a.command=="build":
        td,wa=build();print(json.dumps({"today":td,"watchlist":wa},ensure_ascii=False,indent=2))
    elif a.command=="today":print(json.dumps(loadj(TODAY,{}),ensure_ascii=False,indent=2))
    else:print(json.dumps(loadj(WATCH,{}),ensure_ascii=False,indent=2))
    return 0
if __name__=="__main__":raise SystemExit(main())
