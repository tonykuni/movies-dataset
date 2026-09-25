"""
oneshot_simulator.py — Simulates the PowerShell OneShot activator in Python.

Runs every check the PS1 will run, so we can debug and verify the activation
logic works end-to-end before deploying to Windows.

Mirrors the 6 phases:
  1. PREFLIGHT
  2. SUPPORTIVE
  3. CONSOLIDATE
  4. HEALTH CHECK
  5. TEST SUITE
  6. ACTIVATE (skipped in sandbox)
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

import sys
import os
import json
import subprocess
import time
from pathlib import Path
from collections import OrderedDict

# Mimic PS variable structure
VIA_ROOT          = Path("/home/claude/VDF_final").parent  # sim: real is OneDrive/.../module
VDF_ROOT          = Path("/home/claude/VDF_final")
SUPPORTIVE_ROOT   = VDF_ROOT / "supportive_module"

REQUIRED_SUPPORTIVE = ['VIA_EnvManager.py', 'VeritasAegisNexus.py', 'VeritasCeleritas.py']
OPTIONAL_SUPPORTIVE = [
    'VIA_SSOT_Unified.py', 'VIA_RegistryCore_v1.py',
    'VIA_Runtime_Bridge_All_in_One.py', 'VIA_Panorama_AST_RuntimeInjector.py'
]

VDF_LAYOUT = {
    'config':  ['via_master_ssot.json', 'macro_ssot.json', 'tw_consensus_ssot.json', 'vdf_fetch_matrix.json'],
    'src':     ['vdf_supportive_bridge.py', 'vdf_fetchers_market.py', 'vdf_fetchers_macro.py',
                'vdf_fetchers_financials.py', 'vdf_fetchers_fiscal.py', 'vdf_fetchers_sentiment.py',
                'vdf_fetchers_etf_holdings.py', 'vdf_fetchers_consensus.py', 'vdf_fetchers_derived.py',
                'vdf_fetchers_tdcc.py', 'vdf_fetchers_fed.py',
                'vdf_tests_v4.py', 'vdf_core.py', 'vdf_api.py'],
    'cockpit': ['index.html', 'cockpit.css', 'cockpit.js'],
}

CHECKLIST: OrderedDict[str, str] = OrderedDict()
PYTHON = sys.executable


# ANSI colors
class C:
    OK = '\033[32m'; FAIL = '\033[31m'; WARN = '\033[33m'; INFO = '\033[36m'
    DIM = '\033[90m'; TITLE = '\033[35m'; RST = '\033[0m'


def banner(text: str, char: str = '='):
    line = char * 78
    print(); print(f"{C.TITLE}{line}{C.RST}")
    print(f"{C.TITLE}  {text}{C.RST}")
    print(f"{C.TITLE}{line}{C.RST}")


def step(label: str, n: int, total: int):
    print()
    print(f"  {C.INFO}┌─ PHASE {n}/{total} · {label}{C.RST}")
    print(f"  {C.INFO}│{C.RST}")


def check(name: str, status: str = 'INFO', detail: str = ''):
    markers = {
        'OK':   ('✓', C.OK),
        'FAIL': ('✗', C.FAIL),
        'WARN': ('⚠', C.WARN),
        'SKIP': ('○', C.DIM),
        'INFO': ('ℹ', C.INFO),
    }
    m, col = markers.get(status, ('?', C.RST))
    padded = name.ljust(50)
    if detail:
        print(f"  │  {col}{m} {padded}{C.RST} {C.DIM}{detail}{C.RST}")
    else:
        print(f"  │  {col}{m} {padded}{C.RST}")
    CHECKLIST[name] = status


# ============================================================
# PHASE 1
# ============================================================
def phase1_preflight():
    step('PREFLIGHT — environment probe', 1, 6)

    if VIA_ROOT.exists():
        check('VIA module root exists', 'OK', str(VIA_ROOT))
    else:
        check('VIA module root exists', 'FAIL', f"Not found: {VIA_ROOT}")
        raise RuntimeError("VIA root missing")

    if SUPPORTIVE_ROOT.exists():
        check('Supportive module root exists', 'OK', str(SUPPORTIVE_ROOT))
    else:
        check('Supportive module root exists', 'FAIL', str(SUPPORTIVE_ROOT))
        raise RuntimeError("Supportive root missing")

    if not VDF_ROOT.exists():
        VDF_ROOT.mkdir(parents=True, exist_ok=True)
        check('VDF root created', 'OK', str(VDF_ROOT))
    else:
        check('VDF root exists', 'OK', str(VDF_ROOT))

    try:
        version = subprocess.check_output([PYTHON, '--version'], text=True).strip()
        check('Python interpreter found', 'OK', f"{PYTHON} [{version}]")
    except Exception as e:
        check('Python interpreter found', 'FAIL', str(e))
        raise


# ============================================================
# PHASE 2
# ============================================================
def phase2_supportive():
    step('SUPPORTIVE — verify 3 required + check optional', 2, 6)

    missing = []
    for name in REQUIRED_SUPPORTIVE:
        path = SUPPORTIVE_ROOT / name
        if path.exists():
            kb = path.stat().st_size // 1024
            check(f'Required: {name}', 'OK', f'{kb} KB')
        else:
            check(f'Required: {name}', 'FAIL', f'Not found at {path}')
            missing.append(name)
    if missing:
        raise RuntimeError(f"Missing required: {missing}")

    for name in OPTIONAL_SUPPORTIVE:
        path = SUPPORTIVE_ROOT / name
        if path.exists():
            check(f'Optional: {name}', 'OK', 'available')
        else:
            check(f'Optional: {name}', 'SKIP', 'not present (OK)')

    # Python import probe
    print(f"  │")
    print(f"  │  {C.DIM}Probing import of 3 required supportive modules...{C.RST}")
    code = f"""
import sys
sys.path.insert(0, r'{SUPPORTIVE_ROOT}')
for mod in {REQUIRED_SUPPORTIVE!r}:
    name = mod.replace('.py', '')
    try:
        __import__(name)
        print(f'{{name}}=LOADED')
    except Exception as e:
        print(f'{{name}}=FAIL: {{type(e).__name__}}: {{e}}')
"""
    result = subprocess.run([PYTHON, '-c', code], capture_output=True, text=True, timeout=60)
    for line in result.stdout.split('\n'):
        line = line.strip()
        if not line or '=' not in line:
            continue
        mod, status = line.split('=', 1)
        if status == 'LOADED':
            check(f'Python import: {mod}', 'OK', 'live import successful')
        else:
            check(f'Python import: {mod}', 'FAIL', status)


# ============================================================
# PHASE 3
# ============================================================
def phase3_consolidate():
    step('CONSOLIDATE — ensure VDF files in place', 3, 6)

    for subdir, files in VDF_LAYOUT.items():
        target = VDF_ROOT / subdir
        if not target.exists():
            target.mkdir(parents=True, exist_ok=True)
            check(f'Created {subdir}/', 'OK', str(target))
        else:
            check(f'Subdirectory {subdir}/', 'OK', 'exists')

        missing = [f for f in files if not (target / f).exists()]
        if not missing:
            check(f'  {subdir}: all files present', 'OK', f'{len(files)} files')
        else:
            check(f'  {subdir}: missing files', 'WARN', ', '.join(missing))

    for d in ('temp', 'output', 'logs'):
        path = VDF_ROOT / d
        path.mkdir(exist_ok=True)
        check(f'Runtime dir: {d}/', 'OK', str(path))


# ============================================================
# PHASE 4
# ============================================================
def phase4_health():
    step('HEALTH — bridge.is_alive() + env_health()', 4, 6)

    code = f"""
import sys, json
sys.path.insert(0, r'{SUPPORTIVE_ROOT}')
sys.path.insert(0, r'{VDF_ROOT / "src"}')
try:
    import vdf_supportive_bridge as bridge
    health = bridge.is_alive()
    env = bridge.env_health()
    py = bridge.detect_python()
    print(json.dumps({{'health': health, 'env': env, 'py': py}}, default=str, ensure_ascii=False))
except Exception as e:
    print(f'BRIDGE_FAIL: {{type(e).__name__}}: {{e}}')
"""
    result = subprocess.run([PYTHON, '-c', code], capture_output=True, text=True, timeout=60)
    out = result.stdout.strip()

    if 'BRIDGE_FAIL' in out:
        check('Bridge import', 'FAIL', out.split('BRIDGE_FAIL: ')[-1].strip())
        return

    # Extract JSON line (filter warnings)
    json_line = None
    for line in out.split('\n'):
        line = line.strip()
        if line.startswith('{'):
            json_line = line
            break

    if not json_line:
        check('Bridge output parse', 'FAIL', 'No JSON in output')
        return

    try:
        data = json.loads(json_line)
    except json.JSONDecodeError as e:
        check('Bridge output parse', 'FAIL', f'JSON error: {e}')
        return

    h = data.get('health', {})
    if h.get('aegis', {}).get('loaded'):
        check('Bridge: VeritasAegisNexus', 'OK', 'ResilientHTTPClient ready')
    else:
        check('Bridge: VeritasAegisNexus', 'FAIL', 'not loaded')

    if h.get('celeritas', {}).get('loaded'):
        threads = h['celeritas'].get('recommended_threads', '?')
        check('Bridge: VeritasCeleritas', 'OK', f'parallel_map + cache · threads={threads}')
    else:
        check('Bridge: VeritasCeleritas', 'FAIL', 'not loaded')

    if h.get('envmanager', {}).get('loaded'):
        check('Bridge: VIA_EnvManager', 'OK', 'env_health + detect_python ready')
    else:
        check('Bridge: VIA_EnvManager', 'FAIL', 'not loaded')

    py = data.get('py', {})
    if py:
        ver = py.get('version', '?').split()[0]
        check('Python version (from EnvManager)', 'INFO', ver)


# ============================================================
# PHASE 5
# ============================================================
def phase5_tests():
    step('TEST SUITE — vdf_tests_v4.py', 5, 6)

    test_script = VDF_ROOT / 'src' / 'vdf_tests_v4.py'
    if not test_script.exists():
        check('Test suite file', 'FAIL', f'Not found: {test_script}')
        return False

    check('Running vdf_tests_v4.py...', 'INFO', '(5-15 sec expected)')
    print(f"  │")

    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'
    result = subprocess.run(
        [PYTHON, str(test_script)],
        capture_output=True, text=True, timeout=120, env=env
    )
    output = result.stdout

    # Parse TOTAL line
    import re
    m = re.search(r'TOTAL:\s+(\d+)\s+pass.*?(\d+)\s+fail.*?(\d+)\s+skip\s*\((\d+)', output)
    if m:
        p, f, s, t = int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4))
        if f == 0:
            check(f'Test result: {p}/{t} pass', 'OK', f'({s} skipped)')
        else:
            check(f'Test result: {f} failed', 'FAIL', f'{p} passed of {t}')
    else:
        check('Test result parse', 'WARN', 'Could not parse summary')

    # Per-category
    for line in output.split('\n'):
        cat_match = re.match(r'\s+(\w+)\s+(\d+)\s+/\s+(\d+)\s+passed', line)
        if cat_match:
            cat, p, t = cat_match.group(1), int(cat_match.group(2)), int(cat_match.group(3))
            status = 'OK' if p == t else 'FAIL'
            check(f'  Category: {cat}', status, f'{p}/{t} passed')

    return result.returncode == 0


# ============================================================
# SUMMARY
# ============================================================
def show_summary():
    banner('VDF v4.2 ACTIVATION COMPLETE — CHECKLIST')

    ok    = sum(1 for v in CHECKLIST.values() if v == 'OK')
    fail  = sum(1 for v in CHECKLIST.values() if v == 'FAIL')
    warn  = sum(1 for v in CHECKLIST.values() if v == 'WARN')
    skip  = sum(1 for v in CHECKLIST.values() if v == 'SKIP')
    info  = sum(1 for v in CHECKLIST.values() if v == 'INFO')
    total = len(CHECKLIST)

    print()
    print(f"  {C.INFO}Total checks: {total}{C.RST}")
    print(f"    {C.OK}✓ OK:    {ok}{C.RST}")
    if warn:  print(f"    {C.WARN}⚠ WARN:  {warn}{C.RST}")
    if fail:  print(f"    {C.FAIL}✗ FAIL:  {fail}{C.RST}")
    if skip:  print(f"    {C.DIM}○ SKIP:  {skip}{C.RST}")
    if info:  print(f"    {C.INFO}ℹ INFO:  {info}{C.RST}")
    print()

    if fail == 0:
        print(f"  {C.OK}STATUS: ✓ ALL SYSTEMS GO{C.RST}")
    elif fail <= 2:
        print(f"  {C.WARN}STATUS: ⚠ DEGRADED — {fail} failures (usable){C.RST}")
    else:
        print(f"  {C.FAIL}STATUS: ✗ FAULT — {fail} failures{C.RST}")

    if fail > 0:
        print()
        print(f"  {C.FAIL}FAILED CHECKS:{C.RST}")
        for k, v in CHECKLIST.items():
            if v == 'FAIL':
                print(f"    {C.FAIL}✗ {k}{C.RST}")

    return fail == 0


# ============================================================
# MAIN
# ============================================================
if __name__ == '__main__':
    banner('VeritasDataForge v4.2 — ONE-SHOT ACTIVATOR (Python simulation)')
    print(f"  {C.INFO}VIA root:   {VIA_ROOT}{C.RST}")
    print(f"  {C.INFO}VDF root:   {VDF_ROOT}{C.RST}")

    t0 = time.time()
    try:
        phase1_preflight()
        phase2_supportive()
        phase3_consolidate()
        phase4_health()
        phase5_tests()
        # Phase 6 ACTIVATE skipped in sandbox

        ok = show_summary()
        elapsed = time.time() - t0
        print(f"  {C.DIM}Elapsed: {elapsed:.1f} sec{C.RST}")
        sys.exit(0 if ok else 1)
    except Exception as e:
        print(f"\n  {C.FAIL}╳ FATAL: {type(e).__name__}: {e}{C.RST}")
        show_summary()
        sys.exit(1)
