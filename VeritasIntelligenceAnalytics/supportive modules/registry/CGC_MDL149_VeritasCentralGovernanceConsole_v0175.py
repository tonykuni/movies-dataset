"""VCGC v0175 — current entry, managers and workflow catalog in concise help.

The complete v0174 governance chain remains the only dispatcher: token first,
entry gate, accelerator/network locks, policy, numbering, environment, subsystem
managers, events and synchronization. Help names the active version and reads
the existing workflow SSOT instead of presenting only the v0142 legacy menu.
No fetcher, extractor, workflow executor, consent rule or code allocator is copied.
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
import json
import os
from pathlib import Path
import re
import sys

# def 01_PARAMETERS
HERE = Path(__file__).resolve().parent
VIA = HERE.parents[1]
VERSION = 'v0175'
_STEM = 'CGC_MDL149_VeritasCentralGovernanceConsole'


def _vnum(path):
    match = re.search(r'_v(\d+)$', Path(path).stem)
    return int(match.group(1)) if match else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + '_v*.py') if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum)
_spec = importlib.util.spec_from_file_location('vcgc_prior_for_' + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name):
    return getattr(PRIOR, name)


def help_catalog():
    """Read-only catalog: current registered workflow codes and locked tool owners."""
    lock = json.loads((HERE / 'VIA_ToolVersion_Lock_v0100.json').read_text(encoding='utf-8'))
    workflows = []
    managers = {}
    for family in ('VCGC', 'VDF', 'VRN'):
        book = max(HERE.glob('VIA_Workflow_' + family + '_SSOT_v*.json'), key=_vnum)
        data = json.loads(book.read_text(encoding='utf-8'))
        workflows.extend({'code': w['code'], 'name': w['name'], 'owner': book.name} for w in data['workflows'])
        if family != 'VCGC':
            root = VIA / 'functional modules' / family
            managers[family] = max(root.glob(family + '_SystemManager_v*.py'), key=_vnum).name
    return {'entry': Path(__file__).name, 'previous': PRIOR_PATH.name, 'managers': managers,
            'tools': {name: {'version': lock[name]['version'], 'path': lock[name]['path']} for name in ('accelerator', 'network', 'layout', 'nlp', 'token', 'frame')},
            'workflows': workflows}


def show_current_help():
    card = help_catalog()
    print('\n[目前生效入口] ' + card['entry'] + '；上方 v0142 為沿用的基礎用法。')
    print('  token                         啟用並實測六項省 Token 工具')
    print('  enter [--card] [--no-pull]     唯一入口流程；--card 只檢查，完整啟動交給 go')
    print('  go [原操作台參數]             既有 PowerShell 唯一編排，不另建執行器')
    print('  run [--family vdf|vrn|core] <引擎> [參數]  經 VCGC 閘與事件紀錄逐項執行')
    print('  sync-check / registry-sync [--apply]     同步檢查／原中央 writer 自動編號')
    print('  workflow [輪號] / events [筆數]           流程符合性／真實事件')
    print('  run CGC_MDL245_SDDValidator check|selftests|real|lock|closeout  SDD 驗證與收尾')
    print('  Manager：' + ' · '.join(f'{key} → {value}' for key, value in card['managers'].items()))
    print('  鎖定工具：' + ' · '.join(f'{key} {value["version"]}' for key, value in card['tools'].items()))
    print('  工作流 SSOT：' + str(len(card['workflows'])) + ' 條；登錄不代表本機已實測通過。')
    for row in card['workflows']:
        print('    ' + row['code'] + ' · ' + row['name'])


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if os.environ.get('VIA_FROM_VCGC') != 'YES':
        return PRIOR.main(args)
    rc = PRIOR.main(args)
    if rc == 0 and args == ['help']:
        show_current_help()
    return rc


def selftest():
    return PRIOR.selftest()


if __name__ == '__main__':
    raise SystemExit(selftest() if '--selftest' in sys.argv[1:] else main())
