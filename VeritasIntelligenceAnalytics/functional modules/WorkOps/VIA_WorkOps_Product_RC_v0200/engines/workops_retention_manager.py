# -*- coding: utf-8 -*-
"""ENG-067 Local data-retention planner and explicit apply. Creates backup first."""
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
from datetime import datetime,timedelta,timezone
from pathlib import Path
from workops_backup_restore import backup
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;OUT=ROOT/"out";CFG=ROOT/"config"/"privacy_policy.json";PLAN=OUT/"retention_plan.json"
def j(p,d):
    try:return json.loads(Path(p).read_text(encoding="utf-8-sig"))
    except Exception:return d
def dt(s):
    try:return datetime.fromisoformat(str(s).replace("Z","+00:00"))
    except Exception:return None
def plan():
    cfg=j(CFG,{});days=int((cfg.get("retention") or {}).get("raw_email_events_days",365));cut=datetime.now(timezone.utc)-timedelta(days=days)
    raw=OUT/"email_raw_graph.jsonl";expire=[];keep=[]
    if raw.exists():
        for ln in raw.read_text(encoding="utf-8",errors="replace").splitlines():
            try:
                x=json.loads(ln);d=dt(x.get("received_time"))
                (expire if d and d.astimezone(timezone.utc)<cut else keep).append(x)
            except Exception:pass
    backups=sorted((ROOT/"backups").glob("VIA_WorkOps_Backup_*.zip"),key=lambda p:p.stat().st_mtime,reverse=True)
    keepn=int((cfg.get("retention") or {}).get("backup_keep_count",14));old_backups=[str(x) for x in backups[keepn:]]
    doc={"engine_id":"ENG-067","gate":"REVIEW_REQUIRED","raw_cutoff":cut.isoformat(),"raw_expire_count":len(expire),"raw_keep_count":len(keep),
         "old_backup_count":len(old_backups),"old_backups":old_backups,"apply_requires_confirm":True}
    PLAN.write_text(json.dumps(doc,ensure_ascii=False,indent=2),encoding="utf-8");return doc
def apply(confirm=False):
    if not confirm:raise RuntimeError("EXPLICIT_CONFIRM_REQUIRED")
    p=plan();b=backup();raw=OUT/"email_raw_graph.jsonl";cut=dt(p["raw_cutoff"]);keep=[]
    if raw.exists():
        for ln in raw.read_text(encoding="utf-8",errors="replace").splitlines():
            try:
                x=json.loads(ln);d=dt(x.get("received_time"))
                if not (d and d.astimezone(timezone.utc)<cut):keep.append(x)
            except Exception:pass
        with raw.open("w",encoding="utf-8") as f:
            for x in keep:f.write(json.dumps(x,ensure_ascii=False)+"\n")
    deleted=[]
    for s in p["old_backups"]:
        q=Path(s)
        # Never delete the backup just created.
        if q.exists() and str(q)!=b["backup"]:q.unlink();deleted.append(str(q))
    return {"gate":"PASS","pre_purge_backup":b,"raw_remaining":len(keep),"old_backups_deleted":deleted}
def main():
    ap=argparse.ArgumentParser();ap.add_argument("command",choices=["plan","apply"]);ap.add_argument("--confirm",action="store_true");a=ap.parse_args()
    o=plan() if a.command=="plan" else apply(a.confirm);print(json.dumps(o,ensure_ascii=False,indent=2));return 0
if __name__=="__main__":raise SystemExit(main())
