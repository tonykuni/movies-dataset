from __future__ import annotations

import threading
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from via_interface_engine import (
    ModuleState,
    ReadWriteLock,
    SSOTAutoRegistrar,
    StaticManifestScanner,
    VIAFileWatchdog,
    VIASSOTRegistry,
)
from via_interface_engine.exceptions import LifecycleError


# def TEST PARAMETERS
VALID_PLUGIN_SOURCE = '''
__manifest__ = {
    "name": "PaymentRules",
    "version": "2.1.0",
    "author": "VIA",
    "language": "PY",
    "capability": "PAYMENT",
    "dependencies": []
}
'''

RISKY_PLUGIN_SOURCE = '''
import plugins.private_payment
__manifest__ = {
    "name": "RiskyPayment",
    "version": "1.0.0",
    "author": "VIA"
}
eval("1 + 1")
'''


class SSOTAndDiscoveryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        VIASSOTRegistry.reset_for_testing()
        self.ssot = VIASSOTRegistry(self.root / "registry.sqlite3")

    def tearDown(self) -> None:
        VIASSOTRegistry.reset_for_testing()
        self.temporary_directory.cleanup()

    def test_registry_is_process_singleton_for_same_database(self) -> None:
        second = VIASSOTRegistry(self.root / "registry.sqlite3")
        self.assertIs(self.ssot, second)

    def test_singleton_rejects_database_switch_inside_same_process(self) -> None:
        with self.assertRaises(LifecycleError):
            VIASSOTRegistry(self.root / "different.sqlite3")

    def test_rw_lock_serializes_writers_and_protects_readers(self) -> None:
        lock = ReadWriteLock()
        values: list[int] = []

        def def_write(value: int) -> None:
            with lock.write_locked():
                values.append(value)

        threads = [threading.Thread(target=def_write, args=(value,)) for value in range(8)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        with lock.read_locked():
            self.assertEqual(sorted(values), list(range(8)))

    def test_static_scanner_accepts_literal_manifest_without_importing(self) -> None:
        candidate_path = self.root / "payment.py"
        candidate_path.write_text(VALID_PLUGIN_SOURCE, encoding="utf-8")
        candidate = StaticManifestScanner().scan(candidate_path)
        self.assertTrue(candidate.accepted)
        self.assertEqual(candidate.manifest.name, "PaymentRules")  # type: ignore[union-attr]
        self.assertEqual(candidate.findings, ())

    def test_static_scanner_rejects_dynamic_execution_and_private_import(self) -> None:
        candidate_path = self.root / "risky.py"
        candidate_path.write_text(RISKY_PLUGIN_SOURCE, encoding="utf-8")
        candidate = StaticManifestScanner().scan(candidate_path)
        self.assertFalse(candidate.accepted)
        finding_codes = {item.code for item in candidate.findings}
        self.assertIn("FORBIDDEN_DYNAMIC_CALL", finding_codes)
        self.assertIn("PRIVATE_PLUGIN_IMPORT", finding_codes)

    def test_auto_registrar_allocates_urn_but_does_not_execute_candidate(self) -> None:
        candidate_path = self.root / "payment.py"
        candidate_path.write_text(VALID_PLUGIN_SOURCE, encoding="utf-8")
        candidate, resource_urn = SSOTAutoRegistrar(self.ssot).process_path(candidate_path)
        self.assertTrue(candidate.accepted)
        self.assertRegex(
            resource_urn or "",
            r"^VIA-MOD-PY-PAYMENT-\d{8}-\d{4,}$",
        )
        record = self.ssot.resolve(resource_urn or "")
        self.assertIsNone(record.instance)
        self.assertEqual(record.state, ModuleState.DISCOVERED)
        self.assertEqual(record.instance_locator, "staged://no-instance")

    def test_watchdog_reports_only_changed_supported_files(self) -> None:
        watch_root = self.root / "watch"
        watch_root.mkdir()
        changed_paths: list[Path] = []
        watchdog = VIAFileWatchdog(watch_root, changed_paths.append)
        ignored_path = watch_root / "notes.txt"
        candidate_path = watch_root / "payment.py"
        ignored_path.write_text("ignore", encoding="utf-8")
        candidate_path.write_text(VALID_PLUGIN_SOURCE, encoding="utf-8")
        changed = watchdog.scan_once()
        self.assertEqual(changed, (candidate_path.resolve(),))
        self.assertEqual(changed_paths, [candidate_path.resolve()])


if __name__ == "__main__":
    unittest.main()
