"""VDF Manager v0119 — restore the complete public facade through VCGC.

Manager contract: read/read_engine and all inherited readers use v0117's current
scrape rules. collect(), measure() and the CLI share that same facade. The prior
measurement renderer is reused, never a second engine or a second consent ruler.
No network fetch, dependency install or database write is added. Independent
selftests preserve the caller's environment and write measurement HTML only in
a temporary directory. Original working fetch engines and tool locks stay intact.
"""
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

import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from functools import lru_cache
from unittest.mock import patch

# def 01_PARAMETERS
HERE = Path(__file__).resolve().parent
VERSION = 'v0119'
_STEM = 'VDF_SystemManager'


def _vnum(path):
    match = re.search(r'_v(\d+)$', Path(path).stem)
    return int(match.group(1)) if match else -1


def _load(path):
    spec = importlib.util.spec_from_file_location('vdf119_' + Path(path).stem, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@lru_cache(maxsize=1)
def _prior_chain():
    path = max((p for p in HERE.glob(_STEM + '_v*.py') if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
    chain = []
    seen = set()
    while isinstance(path, Path) and path.is_file() and path.resolve() not in seen:
        seen.add(path.resolve())
        module = _load(path)
        chain.append(module)
        path = vars(module).get('PRIOR')
    return tuple(chain)


@lru_cache(maxsize=1)
def _facade():
    for module in _prior_chain():
        factory = vars(module).get('_facade')
        if callable(factory):
            return factory()
    raise RuntimeError('VDF Manager facade owner is absent')


@lru_cache(maxsize=1)
def _measure_owner():
    for module in _prior_chain():
        if callable(vars(module).get('measure')):
            module._body = _facade
            return module
    raise RuntimeError('VDF Manager measurement owner is absent')


def __getattr__(name):
    return getattr(_facade(), name)


def read(domain, key=None, full=False):
    return _facade().read(domain, key, full)


def collect():
    return _facade().collect()


def measure():
    card = _measure_owner().measure()
    card['door'] = Path(__file__).stem
    return card


def main():
    if os.environ.get('VIA_FROM_VCGC') != 'YES':
        print('[VDF] 拒絕。只能經 via-vcgc。')
        return 2
    if 'measure' in sys.argv[1:]:
        card = measure()
        print(json.dumps(card, ensure_ascii=False, indent=1))
        return 0 if 'via-vdffetch' not in card['cmds_missing'] else 2
    return _facade().main()


def selftest():
    results = []
    def check(name, condition):
        results.append(bool(condition))
        print('  [' + ('OK' if condition else 'FAIL') + '] ' + name)
    before = dict(os.environ)
    prior = _prior_chain()[0]
    check('前版缺失可重現：read / read_engine / measure 未轉送',
          all(not hasattr(prior, name) for name in ('read', 'read_engine', 'measure')))
    body = _facade()
    public = ('read_policy', 'read_logic', 'read_factor', 'read_param', 'read_engine',
              'read_bridge', 'read_tool', 'read_handover', 'read_records', 'read_launch')
    check('完整公開讀取介面委派同一正主', all(__getattr__(name) is getattr(body, name) for name in public))
    actual = read('engine')
    check('實讀引擎冊與正主一致', actual == body.read_engine())
    cards = [body.scrape_gate_split({'VIA_SCRAPE_CONSENT': flag}) for flag in ('OFF', '', 'YES')]
    check('沿用新版爬取同意尺；OFF / 空值不視為開啟',
          all(c.get('off_is_closed') is True for c in cards) and cards[0]['value'] != 'YES' and cards[1]['value'] != 'YES' and cards[2]['value'] == 'YES')
    owner = _measure_owner()
    with tempfile.TemporaryDirectory(prefix='vdf-manager-119-') as name:
        page = Path(name) / 'matrix.html'
        with patch.object(owner, 'PAGE', page):
            card = measure()
        check('實量測沿用正主且不取料、不改庫', page.is_file() and card['door'] == Path(__file__).stem and card['fetched'] is False and card['chain_written'] is False and owner._body() is body)
    with patch.dict(os.environ, before, clear=True), contextlib.redirect_stdout(io.StringIO()):
        os.environ.pop('VIA_FROM_VCGC', None)
        denied = main() == 2
    check('唯一入口拒絕閘仍有效且環境還原', denied and dict(os.environ) == before)
    with patch.dict(os.environ, {'VIA_FROM_VCGC': 'YES'}), patch.object(body, 'main', return_value=7) as dispatch:
        with patch.object(sys, 'argv', [str(__file__), 'read', 'launch']):
            delegated = main()
        check('CLI 走新版 facade，保留原退出碼', delegated == 7 and dispatch.call_count == 1)
    try:
        __getattr__('VDF_MISSING_PUBLIC_API_SENTINEL')
    except AttributeError:
        missing = True
    else:
        missing = False
    check('不存在介面照實拋錯', missing)
    print(f'[計] VDF Manager 公開介面 {sum(results)}/{len(results)} · 正式資料未寫入')
    return 0 if all(results) else 1


if __name__ == '__main__':
    raise SystemExit(selftest() if '--selftest' in sys.argv else main())
