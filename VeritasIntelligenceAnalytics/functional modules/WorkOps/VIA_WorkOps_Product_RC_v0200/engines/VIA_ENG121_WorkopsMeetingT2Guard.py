# -*- coding: utf-8 -*-
"""ENG-042 Meeting T-2 Preparation Guard."""
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
try:
    from zoneinfo import ZoneInfo
except Exception:
    ZoneInfo=None
HERE=Path(__file__).resolve().parent;WORKOPS=HERE.parent;OUT=WORKOPS/"out"
PARAMS=HERE/"meeting_t2_guard_params.json";MEETINGS=OUT/"meeting_registry.jsonl";CARDS=OUT/"project_cards.json"
CMT=OUT/"commitment_status.json";MISSING=OUT/"missing_information.json";RESULT=OUT/"meeting_t2_guard.json"
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
    Path(p).parent.mkdir(parents=True,exist_ok=True);t=Path(str(p)+".tmp")
    t.write_text(json.dumps(o,ensure_ascii=False,indent=2),encoding="utf-8");t.replace(p)
def now():
    tz=ZoneInfo("Asia/Taipei") if ZoneInfo else None
    return datetime.now(tz=tz) if tz else datetime.now()
def dt(s):
    if not s:return None
    try:
        d=datetime.fromisoformat(str(s))
        if d.tzinfo is None and ZoneInfo:d=d.replace(tzinfo=ZoneInfo("Asia/Taipei"))
        return d
    except Exception:return None
def build(override_now=""):
    p=loadj(PARAMS,{})
    n=datetime.fromisoformat(override_now) if override_now else now()
    if n.tzinfo is None and ZoneInfo:n=n.replace(tzinfo=ZoneInfo("Asia/Taipei"))
    cards={x.get("project_id"):x for x in loadj(CARDS,{"cards":[]}).get("cards",[]) if x.get("project_id")}
    cmts=loadj(CMT,{"items":[]}).get("items",[])
    miss=loadj(MISSING,{"items":[]}).get("items",[])
    miss_by={}
    for x in miss: miss_by.setdefault(x.get("project_id"),[]).append(x)
    rows=[]
    for m in loadjl(MEETINGS):
        start=dt(m.get("start_at")); 
        if not start: continue
        hours=(start-n).total_seconds()/3600
        if hours<0 or hours>float(p.get("windows",{}).get("t2_hours",48)): continue
        pid=m.get("project_id"); c=cards.get(pid,{})
        issues=[];score=0;w=p.get("severity_weights",{})
        if not m.get("agenda"):
            issues.append({"code":"MISSING_AGENDA","weight":w.get("missing_agenda",2)});score+=w.get("missing_agenda",2)
        if not (m.get("owner") or c.get("owner")):
            issues.append({"code":"MISSING_OWNER","weight":w.get("missing_owner",4)});score+=w.get("missing_owner",4)
        for fld in (c.get("missing_fields") or []):
            if fld in ("evidence","attachment","required_materials"):
                issues.append({"code":"MISSING_MATERIAL","field":fld,"weight":w.get("missing_material",4)});score+=w.get("missing_material",4)
        for x in cmts:
            if x.get("project_id")==pid and x.get("status")=="OVERDUE":
                issues.append({"code":"OVERDUE_COMMITMENT","commitment_id":x.get("commitment_id"),"weight":w.get("overdue_commitment",5)});score+=w.get("overdue_commitment",5)
        if int(c.get("level",1))>=5:
            issues.append({"code":"OPEN_HIGH_RISK","weight":w.get("open_high_risk",5)});score+=w.get("open_high_risk",5)
        if c.get("state_code")=="BLOCKED":
            issues.append({"code":"BLOCKED_ACTION","weight":w.get("blocked_action",4)});score+=w.get("blocked_action",4)
        gate="READY"
        if score>=10: gate="NOT_READY_CRITICAL"
        elif score>=5: gate="NOT_READY"
        elif score>0: gate="READY_WITH_WARNINGS"
        phase="T-2" if hours>24 else "T-1" if hours>8 else "URGENT"
        rows.append({"meeting_id":m.get("meeting_id"),"project_id":pid,"project_name":m.get("project_name") or c.get("project_name"),
                     "start_at":m.get("start_at"),"hours_to_meeting":round(hours,1),"phase":phase,
                     "readiness_score":score,"gate":gate,"issues":issues,"human_confirmation_required":True})
    rows.sort(key=lambda x:(x["hours_to_meeting"],-x["readiness_score"]))
    doc={"version":"v0100","engine_id":"ENG-042","generated_at":n.isoformat(timespec="seconds"),
         "count":len(rows),"not_ready":sum(x["gate"].startswith("NOT_READY") for x in rows),"items":rows}
    atomic(RESULT,doc);return doc
def main():
    ap=argparse.ArgumentParser();ap.add_argument("command",nargs="?",default="build",choices=["build","status"]);ap.add_argument("--now",default="")
    a=ap.parse_args()
    if a.command=="build":print(json.dumps(build(a.now),ensure_ascii=False,indent=2))
    else:print(json.dumps(loadj(RESULT,{}),ensure_ascii=False,indent=2))
    return 0
if __name__=="__main__":raise SystemExit(main())
