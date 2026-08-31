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

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from via_interface_engine import VIAMemoryWatchdog, VIASSOTRegistry
from via_interface_engine.demo import def_build_reference_engine
from via_interface_engine.twin import VIADigitalTwinTester
from via_interface_engine.ui import SchemaToHTMLRenderer


class UIAndTwinTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = TemporaryDirectory()
        VIASSOTRegistry.reset_for_testing()
        _, self.registry, self.executor = def_build_reference_engine(
            Path(self.temporary_directory.name) / "registry.sqlite3"
        )
        self.renderer = SchemaToHTMLRenderer()

    def tearDown(self) -> None:
        self.registry.shutdown()
        VIASSOTRegistry.reset_for_testing()
        self.temporary_directory.cleanup()

    def test_form_uses_stable_semantic_selectors(self) -> None:
        descriptor = self.registry.get("OrderProcessor")
        markup = self.renderer.render_form(descriptor)
        self.assertIn('data-via-command="OrderProcessor"', markup)
        self.assertIn('data-via-field="amount"', markup)
        self.assertIn('data-via-action="submit"', markup)
        self.assertIn('data-via-urn="VIA-MOD-PY-ORDER-', markup)

    def test_contract_constraints_are_projected_to_html(self) -> None:
        descriptor = self.registry.get("OrderProcessor")
        markup = self.renderer.render_form(descriptor)
        self.assertIn('max="100000000"', markup)
        self.assertIn('min="1e-06"', markup)
        self.assertIn('minlength="3"', markup)
        self.assertIn('maxlength="40"', markup)
        self.assertIn('pattern="^[A-Za-z0-9_-]+$"', markup)
        self.assertNotIn("novalidate", markup)

    def test_catalog_is_complete_light_html_document(self) -> None:
        document = self.renderer.render_catalog_document(self.registry)
        self.assertTrue(document.startswith("<!doctype html>"))
        self.assertIn("Contract-Driven UI", document)
        self.assertIn("#f4f8fb", document)

    def test_digital_twin_passes_contract_and_ui_checks(self) -> None:
        report = VIADigitalTwinTester(self.renderer).run_registry(self.registry)
        self.assertEqual(report.gate, "PASS")
        self.assertEqual(report.failed, 0)
        self.assertGreater(report.passed, 10)

    def test_frontend_bypass_is_still_rejected_by_backend_contract(self) -> None:
        envelope = self.executor.execute_safe(
            "OrderProcessor",
            {"order_id": "ORD-1", "amount": 0, "currency": "TWD"},
        )
        self.assertEqual(envelope.status.value, "REJECTED")

    def test_memory_watchdog_checks_ready_instance(self) -> None:
        results = VIAMemoryWatchdog(self.registry.ssot).scan_once()
        self.assertEqual(len(results), 1)
        self.assertTrue(next(iter(results.values())))


if __name__ == "__main__":
    unittest.main()
