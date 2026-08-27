# -*- coding: utf-8 -*-
"""ENG-048 Feedback Weight Optimizer.
Learns reliability from ACCEPT/REJECT history and proposes a JSON overlay only.
"""
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
from collections import defaultdict
from datetime import datetime
from pathlib import Path
HERE=Path(__file__).resolve().parent;WORKOPS=HERE.parent;OUT=WORKOPS/"out"
PARAMS=HERE/"feedback_weight_optimizer_params.json";BASE=HERE/"project_fusion_params.json"
MEM=OUT/"classification_memory.jsonl";RESULT=OUT/"classification_weight_overlay_proposal.json"
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
    Path(p).parent.mkdir(parents=True,exist_ok=True);t=Path(str(p)+".tmp")
    t.write_text(json.dumps(o,ensure_ascii=False,indent=2),encoding="utf-8");t.replace(p)
def build():
    p=loadj(PARAMS,{});base=loadj(BASE,{}).get("weights",{})
    stat=defaultdict(lambda:{"accept":0,"reject":0,"total":0})
    for r in loadjl(MEM):
        dec=r.get("decision")
        if dec not in ("ACCEPT","REJECT"):continue
        signals=r.get("signals") or {}
        active=[]
        if isinstance(signals,dict):active=[k for k,v in signals.items() if v not in (None,0,False,"")]
        active += ["outlook_folder"] if r.get("folders") else []
        active += ["product_code"] if r.get("product_codes") else []
        active=set(active)
        for s in active:
            stat[s]["total"]+=1
            stat[s]["accept" if dec=="ACCEPT" else "reject"]+=1
    min_n=int(p.get("minimum_confirmations",5));lr=float(p.get("learning_rate",0.10));lo=float(p["weight_bounds"]["min"]);hi=float(p["weight_bounds"]["max"])
    proposed=dict(base);details={}
    aliases={"folder":"outlook_folder","product":"product_code","control":"control_sheet","subject":"subject","body":"body","stakeholder":"stakeholder","confirmed":"confirmed_memory"}
    for raw,s in stat.items():
        key=aliases.get(raw,raw)
        if key not in base:continue
        n=s["total"];rate=s["accept"]/n if n else 0
        if n<min_n:
            details[key]={"n":n,"accept_rate":round(rate,3),"action":"HOLD_INSUFFICIENT_DATA","old_weight":base[key],"new_weight":base[key]}
            continue
        adjustment=(rate-0.5)*2*lr
        new=max(lo,min(hi,float(base[key])+adjustment))
        proposed[key]=round(new,3)
        details[key]={"n":n,"accept_rate":round(rate,3),"action":"PROPOSE","old_weight":base[key],"new_weight":round(new,3)}
    doc={"version":"v0100","engine_id":"ENG-048","generated_at":datetime.now().isoformat(timespec="seconds"),
         "gate":"REVIEW_REQUIRED","base_weights":base,"proposed_weights":proposed,"details":details,
         "activation_performed":False}
    atomic(RESULT,doc);return doc
def main():
    ap=argparse.ArgumentParser();ap.add_argument("command",nargs="?",default="build",choices=["build","status"]);a=ap.parse_args()
    if a.command=="build":print(json.dumps(build(),ensure_ascii=False,indent=2))
    else:print(json.dumps(loadj(RESULT,{}),ensure_ascii=False,indent=2))
    return 0
if __name__=="__main__":raise SystemExit(main())
