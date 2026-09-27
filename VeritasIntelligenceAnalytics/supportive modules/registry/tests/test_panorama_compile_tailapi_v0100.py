#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL158 v0114 的兩類新檢(COMPILE · TAILAPI)沙盒驗收 —— 只寫暫存夾,不碰樹(L17)。

側線 2026-09-28。unittest 寫法,pytest 也收得到。
正控:加速橋注在 from __future__ 前 → COMPILE;尾版比前版少公開名稱又沒轉接 → TAILAPI。
負控:橋在 __future__ 後 → 無 COMPILE;尾版以 __getattr__ 或 exec 轉接 → 無 TAILAPI;非版號檔 → 不比。
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
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
REG = HERE.parent
PANO = sorted(REG.glob("CGC_MDL158_VIAPanoramaAuditRepair_v*.py"))[-1]
BRIDGE = "try:\n    import VIA_SuperAccel_Module as VIA_ACCEL\nexcept Exception:\n    VIA_ACCEL = None\n"


def _load():
    spec = importlib.util.spec_from_file_location("pano_under_test", PANO)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


class PanoramaCompileTailApi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = _load()

    def _classes(self, folder: Path, name: str, text: str) -> set:
        f = folder / name
        f.write_text(text, encoding="utf-8")
        return {i["cls"] for i in self.p.read_file(f)["issues"]}

    def test_bridge_above_future_is_compile(self):
        with tempfile.TemporaryDirectory() as d:
            bad = '"""doc"""\n' + BRIDGE + "from __future__ import annotations\nX = 1\n"
            self.assertIn("COMPILE", self._classes(Path(d), "ENG_A_v0001.py", bad))

    def test_bridge_below_future_is_clean(self):
        with tempfile.TemporaryDirectory() as d:
            good = '"""doc"""\nfrom __future__ import annotations\n' + BRIDGE + "X = 1\n"
            self.assertNotIn("COMPILE", self._classes(Path(d), "ENG_B_v0001.py", good))

    def test_tail_dropping_public_names_is_tailapi(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "MGR_v0001.py").write_text("def do_list():\n    return {}\n\ndef main():\n    return 0\n", encoding="utf-8")
            self.assertIn("TAILAPI", self._classes(root, "MGR_v0002.py", "def main():\n    return 0\n"))

    def test_tail_forwarding_by_getattr_or_exec_is_clean(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "MGR_v0001.py").write_text("def do_list():\n    return {}\n", encoding="utf-8")
            fwd = "def __getattr__(name):\n    raise AttributeError(name)\n\ndef main():\n    return 0\n"
            self.assertNotIn("TAILAPI", self._classes(root, "MGR_v0002.py", fwd))
            body = "exec(compile('', 'x', 'exec'), globals())\n\ndef main():\n    return 0\n"
            self.assertNotIn("TAILAPI", self._classes(root, "MGR_v0003.py", body))

    def test_thin_predecessor_walks_back_to_concrete(self):
        # Codex #328:v2 只是把 v1 載進來的薄尾;v3 丟掉 v1 的 do_list,光比 v2 會漏
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "MGR_v0001.py").write_text("def do_list():\n    return {}\n\ndef main():\n    return 0\n", encoding="utf-8")
            (root / "MGR_v0002.py").write_text('PRIOR = "MGR_v0001.py"\n\ndef main():\n    return 0\n', encoding="utf-8")
            self.assertIn("TAILAPI", self._classes(root, "MGR_v0003.py", 'PRIOR = "MGR_v0002.py"\n\ndef main():\n    return 0\n'))

    def test_unversioned_file_is_not_compared(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertNotIn("TAILAPI", self._classes(Path(d), "plain.py", "def main():\n    return 0\n"))


if __name__ == "__main__":
    unittest.main(verbosity=1)
