#!/usr/bin/env python3
"""Numbering v0113: semantic indicator IDs are not central declared-code claims."""
from __future__ import annotations
import importlib.util,sys,os
from pathlib import Path
HERE=Path(__file__).resolve()
PRIOR_PATH=HERE.with_name('CGC_MDL237_NumberingSystem_v0112.py')
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

def _load_prior():
    spec=importlib.util.spec_from_file_location('numbering_prior_v0113',PRIOR_PATH)
    module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
    return module


PRIOR=_load_prior()
BASE=PRIOR.BASE
_OLD_ITEMS=PRIOR.indicator_items


def indicator_items(book=None,source=PRIOR.SOURCE):
    rows=_OLD_ITEMS(book,source)
    for row in rows:
        row['indicator_id']=row.pop('declared_code')
    return rows


PRIOR.indicator_items=indicator_items


def __getattr__(name):
    return getattr(PRIOR,name)


def selftest():
    rc=PRIOR.selftest()
    rows=indicator_items()
    good=all('indicator_id' in x and 'declared_code' not in x for x in rows)
    print('[OK] semantic ID separated from central code' if good else '[FAIL] semantic ID in declared-code field')
    print(f'[計] OK {int(good)} · FAIL {int(not good)} · inherited_rc={rc}')
    return int(bool(rc) or not good)


def main(argv=None):
    return PRIOR.main(argv)


if __name__=='__main__':
    if os.environ.get('VIA_FROM_VCGC')!='YES':
        print('[GATED] ONLY_VIA_ENTRY');raise SystemExit(2)
    raise SystemExit(selftest() if sys.argv[1:]==['--selftest'] else main())
