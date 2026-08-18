# -*- coding: utf-8 -*-
"""ENG-046 Evidence Integrity & Contradiction Guard."""
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
HERE=Path(__file__).resolve().parent; WORKOPS=HERE.parent; OUT=WORKOPS/"out"
PARAMS=HERE/"evidence_integrity_params.json"; CARDS=OUT/"project_cards.json"; CMT=OUT/"commitment_status.json"
CLOSE=OUT/"closure_candidates.json"; REG=OUT/"project_registry.jsonl"; RESULT=OUT/"evidence_integrity.json"

def loadj(p,d):
    try:return json.loads(Path(p).read_text(encoding="utf-8-sig"))
    except Exception:return d
def loadjl(p):
    rows=[]
    if not Path(p).exists():return rows
    for ln in Path(p).read_text(encoding="utf-8",errors="replace").splitlines():
        try:rows.append(json.loads(ln))
        except Exception:pass
    return rows
def atomic(p,o):
    Path(p).parent.mkdir(parents=True,exist_ok=True); t=Path(str(p)+".tmp")
    t.write_text(json.dumps(o,ensure_ascii=False,indent=2),encoding="utf-8"); t.replace(p)
def project_latest():
    cur={}
    for r in loadjl(REG):
        pid=r.get("project_id")
        if not pid:continue
        x=cur.get(pid,{})
        x.update({k:v for k,v in r.items() if v is not None})
        cur[pid]=x
    return cur

def build():
    cards=loadj(CARDS,{"cards":[]}).get("cards",[])
    cmts=loadj(CMT,{"items":[]}).get("items",[])
    close=loadj(CLOSE,{"items":[]}).get("items",[])
    preg=project_latest()
    bycmt={}
    for c in cmts: bycmt.setdefault(c.get("project_id"),[]).append(c)
    byclose={}
    for c in close: byclose.setdefault(c.get("project_id"),[]).append(c)
    rows=[]
    for c in cards:
        pid=c.get("project_id"); issues=[]; evidence=[]
        if pid and pid not in preg:
            issues.append({"code":"PROJECT_ID_NOT_REGISTERED","severity":"HIGH","field":"project_id"})
        if c.get("closed") and c.get("state_code") in ("IN_PROGRESS","WAITING","BLOCKED","OVERDUE"):
            issues.append({"code":"CLOSED_BUT_ACTIVE_STATE","severity":"HIGH","field":"state_code"})
        if c.get("state_code")=="DONE_CANDIDATE" and not (c.get("evidence") or c.get("evidence_id")):
            issues.append({"code":"DONE_WITHOUT_EVIDENCE","severity":"HIGH","field":"evidence"})
        if c.get("state_code")=="OVERDUE" and not (c.get("due") or c.get("eta") or c.get("revised_eta")):
            issues.append({"code":"OVERDUE_WITHOUT_DUE","severity":"HIGH","field":"due"})
        for x in bycmt.get(pid,[]):
            if x.get("status")=="FULFILLED" and not x.get("fulfillment_evidence"):
                issues.append({"code":"FULFILLED_COMMITMENT_WITHOUT_EVIDENCE","severity":"HIGH","source_id":x.get("commitment_id")})
            if x.get("status")=="OVERDUE" and not x.get("due_at"):
                issues.append({"code":"OVERDUE_COMMITMENT_WITHOUT_DUE","severity":"HIGH","source_id":x.get("commitment_id")})
        for x in byclose.get(pid,[]):
            if x.get("ready_for_human_confirmation") and not x.get("evidence"):
                issues.append({"code":"CLOSE_READY_WITHOUT_EVIDENCE","severity":"HIGH"})
        if c.get("evidence") or c.get("evidence_id"): evidence.append(c.get("evidence") or c.get("evidence_id"))
        evidence += [x.get("evidence") for x in bycmt.get(pid,[]) if x.get("evidence")]
        contradiction_count=len([x for x in issues if x["severity"]=="HIGH"])
        coverage_fields=["project_id","owner","state_code"]
        if c.get("state_code") in ("IN_PROGRESS","WAITING","BLOCKED","OVERDUE"):coverage_fields.append("due")
        present=0
        for f in coverage_fields:
            if f=="due":
                if c.get("due") or c.get("eta") or c.get("revised_eta"):present+=1
            elif c.get(f):present+=1
        coverage=round(present/max(1,len(coverage_fields)),3)
        gate="PASS" if contradiction_count==0 and coverage>=0.75 else "REVIEW" if contradiction_count==0 else "FAIL_CLOSED"
        rows.append({"project_id":pid,"case_id":c.get("case_id"),"project_name":c.get("project_name"),
                     "evidence_ids":sorted(set(evidence)),"evidence_count":len(set(evidence)),
                     "field_coverage":coverage,"contradiction_count":contradiction_count,
                     "issues":issues,"gate":gate})
    doc={"version":"v0100","engine_id":"ENG-046","generated_at":datetime.now().isoformat(timespec="seconds"),
         "count":len(rows),"fail_closed":sum(x["gate"]=="FAIL_CLOSED" for x in rows),
         "review":sum(x["gate"]=="REVIEW" for x in rows),"items":rows}
    atomic(RESULT,doc);return doc

def main():
    ap=argparse.ArgumentParser();ap.add_argument("command",nargs="?",default="build",choices=["build","status"]);a=ap.parse_args()
    if a.command=="build":print(json.dumps(build(),ensure_ascii=False,indent=2))
    else:print(json.dumps(loadj(RESULT,{}),ensure_ascii=False,indent=2))
    return 0
if __name__=="__main__":raise SystemExit(main())
