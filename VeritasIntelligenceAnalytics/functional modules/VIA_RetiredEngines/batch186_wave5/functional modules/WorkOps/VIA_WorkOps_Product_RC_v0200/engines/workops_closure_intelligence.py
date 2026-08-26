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
from workops_autocode import next_code
HERE=Path(__file__).resolve().parent; WORKOPS=HERE.parent; OUT=WORKOPS/"out"
PARAMS=HERE/"closure_intelligence_params.json"; STATE=OUT/"followup_state.json"; MISSING=OUT/"missing_information.json"
CAND=OUT/"closure_candidates.json"; EVENTS=OUT/"closure_events.jsonl"; STATUS=OUT/"closure_status.json"
def loadj(p,d):
    try:return json.loads(Path(p).read_text(encoding="utf-8-sig"))
    except Exception:return d
def loadjl(p):
    out=[]
    if not Path(p).exists():return out
    for ln in Path(p).read_text(encoding="utf-8",errors="replace").splitlines():
        try:out.append(json.loads(ln))
        except Exception:pass
    return out
def atomic(p,o):
    Path(p).parent.mkdir(parents=True,exist_ok=True); t=Path(str(p)+".tmp")
    t.write_text(json.dumps(o,ensure_ascii=False,indent=2),encoding="utf-8"); t.replace(p)
def append(p,o):
    OUT.mkdir(parents=True,exist_ok=True)
    with Path(p).open("a",encoding="utf-8") as f:f.write(json.dumps(o,ensure_ascii=False)+"\n")
def closed():
    s=set()
    for e in loadjl(EVENTS):
        if e.get("event")=="CLOSE_CONFIRMED":
            k=e.get("project_id") or e.get("case_id") or e.get("thr")
            if k:s.add(k)
    return s
def rebuild_status():
    st={}
    for e in loadjl(EVENTS):
        k=e.get("project_id") or e.get("case_id") or e.get("thr")
        if k:st[k]=e
    atomic(STATUS,{"version":"v0100","updated_at":datetime.now().isoformat(timespec="seconds"),"status":st})
def detect():
    p=loadj(PARAMS,{})
    missing={}
    for x in loadj(MISSING,{"items":[]}).get("items",[]):
        missing[x.get("project_id") or x.get("case_id") or x.get("thr")]=x
    done=closed(); rows=[]
    for c in loadj(STATE,{"cards":[]}).get("cards",[]):
        k=c.get("project_id") or c.get("case_id") or c.get("thr")
        if not k or k in done or c.get("closed") or c.get("state_code") not in p.get("candidate_states",[]):continue
        mm=missing.get(k,{}); mf=set(mm.get("missing",[])); blockers=[x for x in p.get("blocking_missing_fields",[]) if x in mf]
        ev=c.get("evidence") or c.get("evidence_id") or ""; ready=bool(ev) and not blockers
        rows.append({"project_id":c.get("project_id"),"case_id":c.get("case_id"),"thr":c.get("thr"),
        "project_name":c.get("project_name"),"state_code":c.get("state_code"),"evidence":ev,"missing_fields":sorted(mf),
        "blockers":blockers,"ready_for_human_confirmation":ready,
        "gate":"READY_TO_CONFIRM" if ready else "BLOCKED_MISSING_INFORMATION","human_confirmation_required":True})
    doc={"version":"v0100","engine_id":"ENG-035","generated_at":datetime.now().isoformat(timespec="seconds"),
    "count":len(rows),"ready_count":sum(x["ready_for_human_confirmation"] for x in rows),"items":rows}
    atomic(CAND,doc); rebuild_status(); return doc
def confirm(project_id="",case_id="",thr="",reason="",confirmed_by="USER"):
    allowed={x["key"] for x in loadj(PARAMS,{}).get("allowed_reasons",[])}
    if reason not in allowed:raise SystemExit("invalid closure reason")
    target=None
    for x in loadj(CAND,{"items":[]}).get("items",[]):
        if project_id and x.get("project_id")==project_id:target=x;break
        if case_id and x.get("case_id")==case_id:target=x;break
        if thr and x.get("thr")==thr:target=x;break
    if not target:raise SystemExit("closure candidate not found; run detect first")
    if not target.get("ready_for_human_confirmation"):raise SystemExit("closure blocked by missing information")
    k=target.get("project_id") or target.get("case_id") or target.get("thr")
    if k in closed():
        print(json.dumps({"status":"ALREADY_CLOSED","key":k},ensure_ascii=False));return 0
    evt={"event":"CLOSE_CONFIRMED","closure_id":next_code("CLS"),"ts":datetime.now().isoformat(timespec="seconds"),
    "project_id":target.get("project_id"),"case_id":target.get("case_id"),"thr":target.get("thr"),
    "project_name":target.get("project_name"),"reason":reason,"evidence":target.get("evidence"),
    "confirmed_by":confirmed_by,"human_confirmed":True,"logical_archive":True}
    append(EVENTS,evt);rebuild_status();print(json.dumps(evt,ensure_ascii=False,indent=2));return 0
def main():
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest="cmd",required=True);sub.add_parser("detect")
    c=sub.add_parser("confirm");c.add_argument("--project-id",default="");c.add_argument("--case-id",default="");c.add_argument("--thr",default="")
    c.add_argument("--reason",required=True);c.add_argument("--confirmed-by",default="USER");sub.add_parser("status");a=ap.parse_args()
    if a.cmd=="detect":print(json.dumps(detect(),ensure_ascii=False,indent=2));return 0
    if a.cmd=="confirm":return confirm(a.project_id,a.case_id,a.thr,a.reason,a.confirmed_by)
    print(json.dumps(loadj(STATUS,{}),ensure_ascii=False,indent=2));return 0
if __name__=="__main__":raise SystemExit(main())
