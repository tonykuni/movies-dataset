"""SDD v0103: 交接遺漏阻止加鎖，未完成交接項阻止假收尾。2026-09-29。"""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(批102 全樹導入令;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 VDF 全導入令;graceful 零行為變更) =====
VIA_NET_TOOL_PATH = None
try:
    from pathlib import Path as _nb_Path
    _nb_p = _nb_Path(__file__).resolve()
    while _nb_p.parent != _nb_p:
        _nb_dir = _nb_p / "supportive modules" / "network"
        if _nb_dir.exists():
            _nb_hits = sorted(_nb_dir.glob("via_net_unified_v*.py"))
            if _nb_hits:
                VIA_NET_TOOL_PATH = str(_nb_hits[-1])
            break
        _nb_p = _nb_p.parent
except Exception:
    VIA_NET_TOOL_PATH = None


def _via_net():
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        module = _nb_ilu.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import importlib.util
import sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
_STEM="CGC_MDL245_SDDValidator"
PRIOR_PATH=max(p for p in HERE.glob(_STEM+"_v*.py") if p.name<Path(__file__).name)
def _load(path,name):
    s=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(s)
    sys.modules[name]=m
    s.loader.exec_module(m)
    return m
PRIOR=_load(PRIOR_PATH,"_sdd_prior_v0103")
BASE=PRIOR
while "PRIOR" in vars(BASE):
    BASE=vars(BASE)["PRIOR"]
_CLOSEOUT=BASE.closeout
_LOCK=BASE.lock
_REGISTERS=BASE._registers

def _registers():
    by_id, numbers = _REGISTERS()
    inventory = BASE._json(HERE / "VIA_Component_Inventory_SSOT_v0100.json", {}) or {}
    for row in inventory.get("records", []):
        if row.get("category") == "system" and row.get("state") == "ACTIVE":
            by_id.setdefault(row.get("identity"), row)
    return by_id, numbers

BASE._registers = _registers

def guard():
    return _load(max(HERE.glob("CGC_MDL140_HandoverConsole_v*.py")),"_sdd_handoff_guard").audit()

def merge_closeout(report, continuity):
    result=dict(report, handoff=continuity["lamp"], handoff_pending=len(continuity["pending"]))
    if continuity["lamp"] != "GREEN" or continuity["closeout_lamp"] != "GREEN":
        result["verdict"]="OPEN"
    return result

def closeout(apply=False):
    continuity=guard()
    if continuity["lamp"]=="GREEN" and continuity["closeout_lamp"]=="GREEN":
        return merge_closeout(_CLOSEOUT(apply),continuity)
    result=merge_closeout(_CLOSEOUT(False),continuity)
    print("[交接收尾閘] OPEN; continuity="+continuity["lamp"]+"; pending="+str(len(continuity["pending"])))
    return result

def lock(apply=False):
    continuity=guard()
    if continuity["lamp"] != "GREEN":
        print("[交接加鎖閘] 拒寫：先補交接遺漏或更新相依證據")
        return None
    return _LOCK(apply)

BASE.closeout=closeout
BASE.lock=lock

def __getattr__(name):
    return getattr(PRIOR,name)

def main(argv=None):
    return PRIOR.main(argv)

def selftest():
    from unittest.mock import Mock, patch
    failure=PRIOR.selftest()
    checks=[]
    for lamp,pending,closed in [("GREEN",[],True),("GREEN",["x"],False),("YELLOW",[],False),("RED",[],False)]:
        c={"lamp":lamp,"pending":pending,"closeout_lamp":"YELLOW" if pending else lamp}
        checks.append((merge_closeout({"verdict":"CLOSED"},c)["verdict"]=="CLOSED")==closed)
    checks.append(merge_closeout({"verdict":"OPEN"},{"lamp":"GREEN","pending":[],"closeout_lamp":"GREEN"})["verdict"]=="OPEN")
    fixture={"records":[{"category":"system","state":"ACTIVE","identity":"VRN_SystemManager","code":"VIA-SYS-0011"},
                        {"category":"system","state":"RETIRED","identity":"OldManager"}]}
    with patch.dict(globals(), {"_REGISTERS":lambda: ({}, {})}), patch.object(BASE, "_json", return_value=fixture):
        registered, _ = _registers()
        checks.append("VRN_SystemManager" in registered and "OldManager" not in registered)
    writer=Mock(return_value={"wkf":{}})
    with patch.dict(globals(), {"guard":lambda:{"lamp":"RED"}, "_LOCK":writer}):
        checks.append(lock(True) is None and not writer.called)
    n=bool(failure)+sum(not x for x in checks)
    print("[交接收尾] fail="+str(n))
    return int(bool(n))
if __name__=="__main__":
    raise SystemExit(selftest() if sys.argv[1:]==["--selftest"] else main())
