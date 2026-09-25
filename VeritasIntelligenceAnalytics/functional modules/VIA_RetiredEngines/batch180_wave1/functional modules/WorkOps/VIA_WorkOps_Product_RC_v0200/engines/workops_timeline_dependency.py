# -*- coding: utf-8 -*-
"""ENG-054 Project timeline reconstruction and dependency impact."""
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
import argparse,csv,json
from collections import defaultdict,deque
from datetime import datetime
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;OUT=ROOT/"out";TL=OUT/"project_timeline.json";DEP=OUT/"dependency_impact.json"
def jload(p,d):
    try:return json.loads(Path(p).read_text(encoding="utf-8-sig"))
    except Exception:return d
def jl(p):
    rows=[]
    if not Path(p).exists():return rows
    for ln in Path(p).read_text(encoding="utf-8",errors="replace").splitlines():
        try:rows.append(json.loads(ln))
        except Exception:pass
    return rows
def build():
    ev=defaultdict(list)
    emails=jl(OUT/"email_raw_graph.jsonl")
    # Link by known project only if classifier memory explicitly confirmed conversation.
    mem={}
    for r in jl(OUT/"classification_memory.jsonl"):
        if r.get("decision")=="ACCEPT" and r.get("conversation_id"):mem[r["conversation_id"]]=r.get("project_id")
    for x in emails:
        pid=mem.get(x.get("conversation_id"))
        if pid:ev[pid].append({"ts":x.get("received_time"),"type":"EMAIL","source_id":x.get("internet_message_id") or x.get("graph_id"),"label":x.get("subject")})
    for x in jload(OUT/"unified_work_register.json",{"items":[]}).get("items",[]):
        pid=x.get("project_id")
        if pid:ev[pid].append({"ts":x.get("updated_at"),"type":x.get("type"),"source_id":x.get("work_item_id"),"label":x.get("title"),"status":x.get("status")})
    for x in jl(OUT/"closure_events.jsonl"):
        pid=x.get("project_id")
        if pid and x.get("event")=="CLOSE_CONFIRMED":ev[pid].append({"ts":x.get("ts"),"type":"CLOSE","source_id":x.get("closure_id"),"label":"Case closed"})
    for pid in ev:ev[pid].sort(key=lambda x:x.get("ts") or "")
    timeline={"version":"v0200","engine_id":"ENG-054","generated_at":datetime.now().astimezone().isoformat(timespec="seconds"),
              "projects":[{"project_id":pid,"events":rows,"event_count":len(rows)} for pid,rows in sorted(ev.items())]}
    TL.write_text(json.dumps(timeline,ensure_ascii=False,indent=2),encoding="utf-8")
    items=jload(OUT/"unified_work_register.json",{"items":[]}).get("items",[])
    byid={x.get("work_item_id"):x for x in items};adj=defaultdict(list)
    for x in items:
        for dep in x.get("depends_on") or []:adj[dep].append(x.get("work_item_id"))
    impacts=[]
    for x in items:
        if x.get("status") not in ("OVERDUE","BLOCKED","NOT_READY","NOT_READY_CRITICAL"):continue
        start=x.get("work_item_id");seen=set();q=deque(adj.get(start,[]))
        while q:
            n=q.popleft()
            if n in seen:continue
            seen.add(n);q.extend(adj.get(n,[]))
        impacts.append({"source_work_item_id":start,"project_id":x.get("project_id"),"status":x.get("status"),
                        "downstream_count":len(seen),"downstream_ids":sorted(seen)})
    dep={"version":"v0200","engine_id":"ENG-054","generated_at":timeline["generated_at"],"items":impacts}
    DEP.write_text(json.dumps(dep,ensure_ascii=False,indent=2),encoding="utf-8")
    return {"timeline_projects":len(ev),"dependency_impacts":len(impacts)}
def main():
    ap=argparse.ArgumentParser();ap.add_argument("command",nargs="?",default="build",choices=["build","timeline","dependencies"]);a=ap.parse_args()
    if a.command=="build":o=build()
    elif a.command=="timeline":o=jload(TL,{})
    else:o=jload(DEP,{})
    print(json.dumps(o,ensure_ascii=False,indent=2));return 0
if __name__=="__main__":raise SystemExit(main())
