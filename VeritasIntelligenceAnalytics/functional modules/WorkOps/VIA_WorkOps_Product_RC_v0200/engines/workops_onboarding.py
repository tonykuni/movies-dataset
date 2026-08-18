# -*- coding: utf-8 -*-
"""ENG-059 Onboarding state machine."""
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
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;CFG=ROOT/"config"/"onboarding_steps.json";STATE=ROOT/"runtime"/"onboarding_state.json"
def jload(p,d):
    try:return json.loads(Path(p).read_text(encoding="utf-8-sig"))
    except Exception:return d
def status():
    steps=jload(CFG,{}).get("steps",[]);st=jload(STATE,{"completed":[]})
    done=set(st.get("completed",[]));return {"steps":[{**x,"completed":x["key"] in done} for x in steps],"completed":len(done),"total":len(steps),"ready":"READY" in done}
def complete(key):
    steps={x["key"] for x in jload(CFG,{}).get("steps",[])}
    if key not in steps:raise RuntimeError("UNKNOWN_ONBOARDING_STEP")
    st=jload(STATE,{"completed":[]});done=list(dict.fromkeys(st.get("completed",[])+[key]));st={"completed":done,"updated_at":datetime.now().astimezone().isoformat(timespec="seconds")}
    STATE.parent.mkdir(parents=True,exist_ok=True);STATE.write_text(json.dumps(st,ensure_ascii=False,indent=2),encoding="utf-8");return status()
def reset():
    if STATE.exists():STATE.unlink()
    return status()
def main():
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest="cmd",required=True);sub.add_parser("status")
    c=sub.add_parser("complete");c.add_argument("step");sub.add_parser("reset");a=ap.parse_args()
    o=status() if a.cmd=="status" else complete(a.step) if a.cmd=="complete" else reset()
    print(json.dumps(o,ensure_ascii=False,indent=2));return 0
if __name__=="__main__":raise SystemExit(main())
