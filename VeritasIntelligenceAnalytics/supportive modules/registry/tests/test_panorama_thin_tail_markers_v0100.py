#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL158 v0115 的 ⑭ 薄尾憑據(Z234)沙盒驗收 —— 只寫暫存夾,不碰樹(L17)。

側線 2026-09-28。unittest 寫法,pytest 也收得到。
正控:尾版以 exec/runpy 載入較舊同族本體 → 憑據在本體裡也算齊;退役件在本體裡復活照樣 RED。
負控:只在說明/註解提到舊版(沒有載入)→ 不往回走,憑據不在尾版就是 RED。
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


def _load():
    spec = importlib.util.spec_from_file_location("pano_thin_tail_under_test", PANO)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


class PanoramaThinTailMarkers(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = _load()

    def _verify(self, root: Path, glob: str, markers=(), absent=()):
        saved = self.p.VIA
        self.p.VIA = root
        try:
            return self.p._verify_one({"kind": "tail_contains", "dir": ".", "glob": glob,
                                       "markers": list(markers), "markers_absent": list(absent)}, {}, {})
        finally:
            self.p.VIA = saved

    def test_exec_body_markers_count(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "MGR_v0001.py").write_text("TASK_FORMAL_NAMES = {}\n", encoding="utf-8")
            (root / "MGR_v0002.py").write_text(
                "from pathlib import Path\nexec(Path(__file__).with_name('MGR_v0001.py').read_text())\n", encoding="utf-8")
            self.assertEqual(self._verify(root, "MGR_v*.py", ["TASK_FORMAL_NAMES"])[0], "GREEN")

    def test_runpy_chain_walks_back_to_concrete(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "ENG_v0001.py").write_text("def _newest_rel():\n    return 1\n", encoding="utf-8")
            (root / "ENG_v0002.py").write_text("import runpy\nG = runpy.run_path('ENG_v0001.py')\n", encoding="utf-8")
            (root / "ENG_v0003.py").write_text(
                "import importlib.util\nS = importlib.util.spec_from_file_location('b', 'ENG_v0002.py')\nME = 'ENG_v0003.py'\n",
                encoding="utf-8")
            chain = [q.name for q in self.p._loaded_chain(root / "ENG_v0003.py")]
            self.assertEqual(chain, ["ENG_v0003.py", "ENG_v0002.py", "ENG_v0001.py"])
            self.assertEqual(self._verify(root, "ENG_v*.py", ["_newest_rel"])[0], "GREEN")

    def test_retired_key_in_loaded_body_is_red(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "MGR_v0001.py").write_text('K = {"talib_probe": 1}\n', encoding="utf-8")
            (root / "MGR_v0002.py").write_text("exec(open('MGR_v0001.py').read())\n", encoding="utf-8")
            self.assertEqual(self._verify(root, "MGR_v*.py", absent=['"talib_probe":'])[0], "RED")

    def test_prose_mention_is_not_a_load(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "ENG_v0001.py").write_text("MARK = 1\n", encoding="utf-8")
            (root / "ENG_v0002.py").write_text(
                '"""v0001 to v0002: ENG_v0001.py stays on disk"""\nimport importlib\n# was ENG_v0001.py\nX = 1\n',
                encoding="utf-8")
            self.assertEqual([q.name for q in self.p._loaded_chain(root / "ENG_v0002.py")], ["ENG_v0002.py"])
            self.assertEqual(self._verify(root, "ENG_v*.py", ["MARK"])[0], "RED")


if __name__ == "__main__":
    unittest.main()
