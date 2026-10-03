#!/usr/bin/env python3
"""ForwardVintageDoor v0101: full hash lock, both CLI aliases, no environment mutation."""
from __future__ import annotations
import os,sys,json,hashlib,importlib.util
from pathlib import Path
HERE=Path(__file__).resolve()
ENGINE=HERE.with_name('VDF_ENG117_ForwardVintage_v0102.py')
LOCKS={'VDF_ENG117_ForwardVintage_v0102.py': '22899fed83032fe350bdef7ccb987edff28c6aab234d2c91dce23b1b5726a778', 'VDF_ENG117_ForwardVintage_v0101.py': 'e28273420c6b3cda7624df2c7df00b08e294153f86660264164186dbb06461ab'}
# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(VDF 全導入令;惰性載入=import 時零網路、零行為變更) =====
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
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT;網路只認 AegisNexus);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        _nb_spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        _nb_mod = _nb_ilu.module_from_spec(_nb_spec)
        _nb_spec.loader.exec_module(_nb_mod)
        return _nb_mod
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(全樹導入令;graceful 零行為變更) =====
try:
    _sa_p = HERE
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

def allowed():
    return os.environ.get('VIA_FROM_VCGC')=='YES'


def verify_hashes():
    return all(hashlib.sha256(HERE.with_name(name).read_bytes()).hexdigest()==digest for name,digest in LOCKS.items())


def load():
    if not verify_hashes():
        raise ValueError('SOURCE_HASH_MISMATCH')
    spec=importlib.util.spec_from_file_location('forward_vintage_door_target',ENGINE)
    module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
    return module


def run():
    if not allowed():
        return {'state':'GATED','why':'ONLY_VIA_ENTRY'}
    try:
        result=load().run_self_test()
    except ImportError as exc:
        return {'state':'ABSENT','why':str(exc)}
    return {'state':result['status'],'tests':result['tests'],'sha256':LOCKS[ENGINE.name]}


def selftest():
    before=dict(os.environ)
    ok=allowed() and verify_hashes()
    print('[OK] full source SHA256 lock' if ok else '[FAIL] source lock or entry')
    unchanged=before==dict(os.environ)
    print('[OK] no environment mutation' if unchanged else '[FAIL] environment mutated')
    print(f'[計] OK {int(ok)+int(unchanged)} · FAIL {int(not ok)+int(not unchanged)}')
    return 0 if ok and unchanged else 1


def main():
    if not allowed():
        print('[GATED] ONLY_VIA_ENTRY');return 2
    if sys.argv[1:]==['--selftest']:
        return selftest()
    result=run();print(json.dumps(result,ensure_ascii=False,default=str))
    return {'pass':0,'GATED':2,'ABSENT':3}.get(result['state'],1)


if __name__=='__main__':
    raise SystemExit(main())
