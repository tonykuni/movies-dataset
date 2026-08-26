# -*- coding: utf-8 -*-
"""ENG-044 Lesson Learned Engine."""
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
HERE=Path(__file__).resolve().parent;WORKOPS=HERE.parent;OUT=WORKOPS/"out"
CLOSE=OUT/"closure_events.jsonl";CMT=OUT/"commitment_status.json";CARDS=OUT/"project_cards.json"
CAND=OUT/"lesson_candidates.json";REG=OUT/"lesson_registry.jsonl"
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
def append(p,o):
    OUT.mkdir(parents=True,exist_ok=True)
    with Path(p).open("a",encoding="utf-8") as f:f.write(json.dumps(o,ensure_ascii=False)+"\n")
def build():
    cards={x.get("project_id"):x for x in loadj(CARDS,{"cards":[]}).get("cards",[]) if x.get("project_id")}
    rows=[];seen=set()
    for e in loadjl(CLOSE):
        if e.get("event")!="CLOSE_CONFIRMED":continue
        pid=e.get("project_id");k=("CLOSE",e.get("closure_id"))
        if k in seen:continue
        seen.add(k);c=cards.get(pid,{})
        rows.append({"trigger":"CLOSE_CONFIRMED","source_id":e.get("closure_id"),"project_id":pid,"project_name":e.get("project_name") or c.get("project_name"),
                     "situation":c.get("issue") or "Closed project/case","root_cause":"","what_worked":"","what_failed":"",
                     "prevention":"","reuse_rule":"","evidence":e.get("evidence"),"human_confirmation_required":True})
    for x in loadj(CMT,{"items":[]}).get("items",[]):
        if x.get("status")!="OVERDUE":continue
        k=("CMT",x.get("commitment_id"))
        if k in seen:continue
        seen.add(k)
        rows.append({"trigger":"BROKEN_COMMITMENT","source_id":x.get("commitment_id"),"project_id":x.get("project_id"),"project_name":x.get("project_name"),
                     "situation":x.get("commitment_text"),"root_cause":"","what_worked":"","what_failed":"",
                     "prevention":"","reuse_rule":"Add earlier checkpoint before commitment due date","evidence":x.get("evidence"),"human_confirmation_required":True})
    doc={"version":"v0100","engine_id":"ENG-044","generated_at":datetime.now().isoformat(timespec="seconds"),"count":len(rows),"items":rows}
    atomic(CAND,doc);return doc
def confirm(index,root_cause,prevention,reuse_rule=""):
    d=loadj(CAND,{"items":[]})
    if index<0 or index>=len(d.get("items",[])):raise SystemExit("candidate index out of range")
    x=d["items"][index]
    if not root_cause or not prevention:raise SystemExit("root_cause and prevention required")
    evt={**x,"event":"LESSON_CONFIRMED","lesson_id":next_code("LLN"),"ts":datetime.now().isoformat(timespec="seconds"),
         "root_cause":root_cause,"prevention":prevention,"reuse_rule":reuse_rule or x.get("reuse_rule") or "","human_confirmed":True}
    append(REG,evt);print(json.dumps(evt,ensure_ascii=False,indent=2));return 0
def main():
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest="cmd",required=True);sub.add_parser("build")
    c=sub.add_parser("confirm");c.add_argument("index",type=int);c.add_argument("--root-cause",required=True);c.add_argument("--prevention",required=True);c.add_argument("--reuse-rule",default="")
    sub.add_parser("list");a=ap.parse_args()
    if a.cmd=="build":print(json.dumps(build(),ensure_ascii=False,indent=2));return 0
    if a.cmd=="confirm":return confirm(a.index,a.root_cause,a.prevention,a.reuse_rule)
    print(json.dumps(loadjl(REG),ensure_ascii=False,indent=2));return 0
if __name__=="__main__":raise SystemExit(main())
