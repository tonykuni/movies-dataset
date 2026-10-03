#!/usr/bin/env python3
"""USMacroProbe v0102: deterministic isolated credential-resolution selftest."""
from __future__ import annotations
import os,sys,tempfile,importlib.util
from pathlib import Path
HERE=Path(__file__).resolve()
PRIOR_PATH=HERE.with_name('VDF_ENG110_USMacroProbe_v0101.py')
KEY_FILE=HERE.parent.parent/'output_hub/mega/.fred_api_key'
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
def prior():
    spec=importlib.util.spec_from_file_location('macro_probe_prior_v0102',PRIOR_PATH)
    mod=importlib.util.module_from_spec(spec);sys.modules[spec.name]=mod;spec.loader.exec_module(mod)
    return mod


def __getattr__(name):
    mod=prior()
    return getattr(mod,name) if hasattr(mod,name) else getattr(mod._prior(),name)


def key_from(env=None,key_file=None):
    environment=os.environ if env is None else env
    path=KEY_FILE if key_file is None else Path(key_file)
    value=environment.get('FRED_API_KEY','').strip()
    if value:
        return value,'env'
    if path.is_file():
        value=path.read_text(encoding='utf-8').strip()
        if value:
            return value,'keyfile'
    return '','missing'


def selftest():
    before=dict(os.environ);checks=[]
    with tempfile.TemporaryDirectory(prefix='via_macro_fixture_') as temporary:
        path=Path(temporary)/'fixture_key.txt'
        checks.append(('missing',key_from({},path)==('','missing')))
        path.write_text('fixture-file',encoding='utf-8')
        checks.append(('file',key_from({},path)==('fixture-file','keyfile')))
        checks.append(('env precedence',key_from({'FRED_API_KEY':'fixture-env'},path)==('fixture-env','env')))
        path.write_text(' ',encoding='utf-8')
        checks.append(('empty file',key_from({},path)==('','missing')))
    checks.append(('real environment unchanged',dict(os.environ)==before))
    checks.append(('old APIs retained',all(callable(getattr(prior()._prior(),n)) for n in ('dts_point','fred_point','plan'))))
    for name,ok in checks:
        print(('[OK] ' if ok else '[FAIL] ')+name)
    failed=sum(not ok for _,ok in checks);print(f'[計] OK {len(checks)-failed} · FAIL {failed}')
    return int(failed>0)


def main():
    if os.environ.get('VIA_FROM_VCGC')!='YES':
        print('[GATED] ONLY_VIA_ENTRY');return 2
    if sys.argv[1:]==['--selftest']:
        return selftest()
    return prior().main()


if __name__=='__main__':
    raise SystemExit(main())
