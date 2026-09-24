# -*- coding: utf-8 -*-
"""Tests for VRN_AutoTestLoop: document-free gates always run; the synthetic corpus loop runs when the PDF/Parquet stack is present."""
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
import json
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOOP = HERE.parent / "engine" / "VRN_AutoTestLoop.py"
SELFTEST_SECONDS = 16   # rough cost in the loop's self-test (批731: it runs the costliest units first)


def def_load():
    spec = importlib.util.spec_from_file_location("vrn_autotest_loop_test", str(LOOP))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


def def_has(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, ValueError):
        return False


class def_AutoTestLoopTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.loop = def_load()
        cls.engines = cls.loop.Engines()

    def test_engines_load(self) -> None:
        self.assertEqual(self.engines.errors, {})
        self.assertIsNotNone(self.engines.fpe)

    def test_document_free_gates_have_no_failures(self) -> None:
        rows = self.loop.def_gate_compile() + self.loop.def_gate_selftest(self.engines) + self.loop.def_gate_filename_oracle(self.engines)
        failures = [r for r in rows if r["status"] == "FAIL"]
        self.assertEqual(failures, [])
        self.assertTrue(any(r["gate"] == "G03 FILENAME" and r["status"] == "PASS" for r in rows))

    def test_audit_gate_reruns_the_30_checks(self) -> None:
        with tempfile.TemporaryDirectory(prefix="vrn-audit-") as temporary:
            rows = self.loop.def_gate_audit(Path(temporary))
        self.assertEqual(rows[0]["status"], "PASS", rows[0])

    def test_roster_and_oracle_names_are_available(self) -> None:
        self.assertGreaterEqual(len(self.loop.def_load_oracle()), 100)

    def test_html_report_renders(self) -> None:
        report = {"verdict": "GREEN", "samples": "x", "real_mode": False, "rounds_run": 1, "rounds_max": 3, "generated": "now",
                  "counts": {"PASS": 1, "WARN": 0, "SKIP": 0, "FAIL": 0}, "fixes_applied": [], "file_count": 1,
                  "rounds": [{"round": 1, "verdict": "GREEN", "rows": [self.loop.def_row("G01 COMPILE", "x.py", "PASS")]}]}
        html = self.loop.def_render_html(report)
        self.assertIn("GREEN", html)
        self.assertIn("G01 COMPILE", html)

    @unittest.skipUnless(def_has("fitz") and def_has("pandas") and def_has("pyarrow"), "PDF/Parquet stack not installed")
    def test_synthetic_loop_ends_green_or_amber(self) -> None:
        with tempfile.TemporaryDirectory(prefix="vrn-loop-") as temporary:
            code = self.loop.def_main(["--synthetic", "--limit", "8", "--rounds", "2", "--no-audit", "--quiet", "--out", temporary])
            report = json.loads((Path(temporary) / "VRN_AutoTest_Report.json").read_text(encoding="utf-8"))
        self.assertEqual(code, 0, report["counts"])
        self.assertIn(report["verdict"], ("GREEN", "AMBER"))
        self.assertEqual(report["counts"]["FAIL"], 0)
        self.assertGreaterEqual(report["file_count"], 8)


if __name__ == "__main__":
    unittest.main()
