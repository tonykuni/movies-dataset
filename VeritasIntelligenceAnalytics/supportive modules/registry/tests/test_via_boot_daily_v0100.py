"""真正執行雙載體的隔離假引擎：查庫先行、失敗重試、互斥與完成標記。"""
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(graceful 缺席零影響) =====
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
    VIA_ACCEL = None
# ===== [VIA:ACCEL-BRIDGE:END] =====

from datetime import datetime
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

REG = Path(__file__).resolve().parents[1]


class BootDaily(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.via = root / 'VeritasIntelligenceAnalytics'
        self.reg = self.via / 'supportive modules/registry'
        self.reg.mkdir(parents=True)
        texts = [(REG / ('via_boot_update.' + ext)).read_text(encoding='utf-8') for ext in ('sh', 'ps1')]
        for ext, text in zip(('sh', 'ps1'), texts):
            # 舊 Linux 環境自補的絕對目錄也留在暫存區；不改本輪待驗控制流程。
            text = text.replace('/root/Downloads', str(root / 'Downloads'))
            text = text.replace('/root/OneDrive', str(root / 'OneDrive'))
            (self.reg / ('via_boot_update.' + ext)).write_text(text, encoding='utf-8')
        for name in set(re.findall(r'(?:CGC|VDF|VRN|VAP|GRP)_[A-Za-z0-9_*]+\.py', '\n'.join(texts))):
            d = {'CGC': self.reg, 'VDF': self.via / 'functional modules/VDF/engine',
                 'VRN': self.via / 'functional modules/VRN', 'VAP': self.via / 'functional modules/VAP/engine',
                 'GRP': self.via / 'functional modules/GroupIndex/engine'}[name[:3]]
            d.mkdir(parents=True, exist_ok=True)
            (d / name.replace('*', '9999')).write_text('# isolated fake engine\n')
        self.bin = root / 'bin'
        self.bin.mkdir()
        fake = self.bin / 'fake_python.py'
        fake.write_text('''import json, os, sys
from pathlib import Path
args = sys.argv[1:]
if not args or args == ["-"]:
    sys.stdin.read()
    sys.exit(0)
name = Path(args[0]).name
if "envpy" in args:
    print(json.dumps({"state":"fixture","source":"fixture","python":os.environ["FAKE_PYTHON"]}))
    sys.exit(0)
with open(os.environ["FAKE_CALLS"], "a", encoding="utf-8") as f:
    f.write(json.dumps({"name":name,"args":args[1:]}) + "\\n")
if not Path(args[0]).is_file(): sys.exit(3)
sys.exit(1 if os.environ.get("FAKE_FAIL") and os.environ["FAKE_FAIL"] in name else 0)
''', encoding='utf-8')
        for name in ('python', 'python3'):
            p = self.bin / (name + ('.cmd' if os.name == 'nt' else ''))
            if os.name == 'nt':
                p.write_text(f'@"{sys.executable}" "{fake}" %*\r\n@exit /b %errorlevel%\r\n')
            else:
                p.write_text(f'#!/bin/sh\nexec "{sys.executable}" "{fake}" "$@"\n')
                p.chmod(0o755)
        self.calls = root / 'calls.jsonl'
        self.env = {**os.environ, 'PATH': str(self.bin) + os.pathsep + os.environ['PATH'],
                    'FAKE_CALLS': str(self.calls), 'FAKE_PYTHON': str(self.bin / ('python.cmd' if os.name == 'nt' else 'python')),
                    'PYTHONUTF8': '1', 'PYTHONIOENCODING': 'utf-8'}
        self.mega = self.via / 'functional modules/VDF/output_hub/mega'
        self.mega.mkdir(parents=True)
        self.mark = self.mega / '.last_boot_update'
        self.verified = self.mega / '.last_boot_update.verified'
        self.lock = self.mega / '.last_boot_update.lock'

    def run_boot(self, ext, fail=''):
        if os.name == 'nt' and ext == 'sh':
            self.skipTest('POSIX 載體在 Linux 實跑；Windows 只驗原生 PowerShell')
        executable = shutil.which('bash') if ext == 'sh' else (os.environ.get('VIA_TEST_PWSH') or shutil.which('pwsh'))
        if not executable:
            self.skipTest(ext + ' runtime unavailable')
        cmd = [executable, str(self.reg / ('via_boot_update.' + ext))] if ext == 'sh' else [
            executable, '-NoProfile', '-File', str(self.reg / 'via_boot_update.ps1')]
        return subprocess.run(cmd, env={**self.env, 'FAKE_FAIL': fail}, text=True,
                              encoding='utf-8', errors='replace', capture_output=True, timeout=40)

    def records(self):
        return [json.loads(s) for s in self.calls.read_text().splitlines()] if self.calls.exists() else []

    def scenario(self, ext, case):
        if case == 'preflight':
            r = self.run_boot(ext, 'CGC_MDL123')
            self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
            self.assertEqual(len(self.records()), 1)
            self.assertFalse(self.mark.exists())
        elif case == 'failure_retry':
            r = self.run_boot(ext, 'VDF_ENG077')
            self.assertNotEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertFalse(self.mark.exists())
            self.assertFalse(self.verified.exists())
            before = len(self.records())
            r = self.run_boot(ext)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertGreater(len(self.records()), before)
            self.assertTrue(self.mark.exists() and self.verified.exists())
        elif case == 'success_skip':
            r = self.run_boot(ext)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            records = self.records()
            self.assertIn('CGC_MDL123', records[0]['name'])
            self.assertIn('VDF_ENG089', records[1]['name'])
            self.assertIn('VDF_ENG055', records[2]['name'])
            last_cnyes = next(i for i, x in enumerate(records) if 'VRN_ENG071' in x['name'])
            self.assertIn('VRN_ENG069', records[last_cnyes + 1]['name'])
            r = self.run_boot(ext)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertEqual(len(self.records()), len(records))
        elif case == 'legacy_marker':
            self.mark.write_text(datetime.now().strftime('%Y-%m-%d'))
            r = self.run_boot(ext)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertGreater(len(self.records()), 3)
        elif case == 'lock':
            self.lock.mkdir()
            r = self.run_boot(ext)
            self.assertEqual(r.returncode, 3, r.stdout + r.stderr)
            self.assertEqual(self.records(), [])
            self.assertTrue(self.lock.exists())
            return
        elif case == 'missing':
            for p in self.via.rglob('VDF_ENG077*.py'):
                p.unlink()
            r = self.run_boot(ext)
            self.assertNotEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertFalse(self.mark.exists())
        self.assertFalse(self.lock.exists(), 'owned lock leaked')


for _ext in ('sh', 'ps1'):
    for _case in ('preflight', 'failure_retry', 'success_skip', 'legacy_marker', 'lock', 'missing'):
        def test(self, ext=_ext, case=_case):
            self.scenario(ext, case)
        setattr(BootDaily, 'test_' + _ext + '_' + _case, test)


if __name__ == '__main__':
    unittest.main()
