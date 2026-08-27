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

import ast
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
CORE_PATH = PACKAGE_ROOT / "via_v0140b_windows_handle_core.py"
CONTRACT_PATH = PACKAGE_ROOT / "v0140B_WindowsHandleContract.json"
RULES_PATH = PACKAGE_ROOT / "v0140B_WindowsHandleRules.json"
TOKEN = "VIA_APPROVE_V0140B_WINDOWS_FILE_HANDLE_ACQUISITION_SANDBOX_VALIDATION_READ_ONLY"

SPEC = importlib.util.spec_from_file_location("windows_handle_core", CORE_PATH)
assert SPEC and SPEC.loader
CORE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CORE)


class WindowsHandleContractTests(unittest.TestCase):
    def test_contract_declares_six_unique_sequential_engines(self) -> None:
        contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
        engines = [item["id"] for item in contract["engines"]]
        self.assertEqual(engines, ["H01", "H02", "H03", "H04", "H05", "H06"])
        self.assertEqual(len(set(engines)), 6)
        self.assertEqual(
            contract["coordination_model"]["execution"],
            "SEQUENTIAL_POWERSHELL7_PROCESS_ISOLATION",
        )
        self.assertEqual(contract["coordination_model"]["cross_subsystem_matrix_rows"], 18)

    def test_all_python_sources_have_valid_ast(self) -> None:
        for path in sorted(PACKAGE_ROOT.glob("*.py")):
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

    def test_wrapper_identities_are_unique(self) -> None:
        for engine_id, wrapper_name in CORE.DEF_WRAPPERS.items():
            text = (PACKAGE_ROOT / wrapper_name).read_text(encoding="utf-8")
            self.assertEqual(text.count(f'def_lane_entry("{engine_id}")'), 1)

    def test_buffer_profile_is_non_persistent_and_unhashed(self) -> None:
        profile = CORE.def_buffer_profile(b"\xef\xbb\xbfA,B\n1,2\n")
        self.assertEqual(profile["bom"], "UTF8")
        self.assertEqual(profile["bytes_read"], 11)
        self.assertFalse(profile["raw_content_persisted"])
        self.assertFalse(profile["content_hash_computed"])

    def test_recall_attributes_block_content_open(self) -> None:
        rules = json.loads(RULES_PATH.read_text(encoding="utf-8"))
        value = 4096 | 262144 | 4194304
        names = CORE.def_decode_file_attributes(value, rules)
        self.assertEqual(names, ["OFFLINE", "RECALL_ON_OPEN", "RECALL_ON_DATA_ACCESS"])

    def test_guarded_skip_has_no_attempt_success_or_bytes(self) -> None:
        for probe in (
            lambda: CORE.def_probe_pathlib("never-open", 32, False),
            lambda: CORE.def_probe_os_open("never-open", 32, False),
            lambda: CORE.def_probe_createfilew("never-open", 32, False, False),
        ):
            result = probe()
            self.assertTrue(result["outcome"].startswith("SKIPPED"))
            self.assertEqual(
                (result["source_open_attempts"], result["source_open_successes"], result["source_bytes_read"]),
                (0, 0, 0),
            )

    def test_inconsistent_probe_metrics_are_rejected(self) -> None:
        result = CORE.def_probe_result("BROKEN", 0, 0, 7)
        with self.assertRaisesRegex(ValueError, "Positive source bytes"):
            CORE.def_validate_content_probe_result(result, 64)

    def test_python_strategies_read_only_a_bounded_buffer(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture = Path(temp_dir) / "Standardized_Prices.csv"
            payload = b"Date,Ticker,Close\n2025-01-15,3067.TWO,39.1\n"
            fixture.write_bytes(payload)
            before = fixture.read_bytes()
            for probe in (CORE.def_probe_pathlib, CORE.def_probe_os_open):
                result = probe(str(fixture), 16, True)
                self.assertEqual(result["outcome"], "OPEN_SUCCESS")
                self.assertEqual(result["source_open_attempts"], 1)
                self.assertEqual(result["source_open_successes"], 1)
                self.assertEqual(result["source_bytes_read"], 16)
                self.assertFalse(result["buffer_profile"]["raw_content_persisted"])
            self.assertEqual(fixture.read_bytes(), before)

    def test_extended_windows_path_forms(self) -> None:
        self.assertEqual(
            CORE.def_extended_windows_path(r"\\server\share\x.csv"),
            r"\\?\UNC\server\share\x.csv",
        )
        already = r"\\?\C:\long\x.csv"
        self.assertEqual(CORE.def_extended_windows_path(already), already)

    def test_wrong_approval_token_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            lane = Path(temp_dir) / "lane"
            command = self._lane_command("H01", lane, Path(temp_dir) / "x.csv", "WRONG")
            process = subprocess.run(command, text=True, capture_output=True, check=False, env=self._test_env())
            self.assertEqual(process.returncode, 2)
            summary = json.loads((lane / "TERMINAL_SUMMARY.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["status"], "FAIL")
            self.assertEqual(summary["source_open_attempts"], 0)

    def test_full_six_process_sequence_and_hydra_detection(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            fixture = Path(temp_dir) / "Standardized_Prices.csv"
            fixture.write_bytes(b"Date,Ticker,Close\n2025-01-15,3067.TWO,39.1\n")
            authorized = False
            for index, engine_id in enumerate(CORE.DEF_ENGINE_NAMES, start=1):
                lane = run_dir / "lanes" / f"{engine_id}_{CORE.DEF_ENGINE_NAMES[engine_id]}"
                command = self._lane_command(engine_id, lane, fixture, TOKEN, index, authorized)
                process = subprocess.run(command, text=True, capture_output=True, check=False, env=self._test_env())
                self.assertEqual(process.returncode, 0, process.stderr)
                summary = json.loads((lane / "TERMINAL_SUMMARY.json").read_text(encoding="utf-8"))
                self.assertTrue(summary["terminal"])
                if engine_id == "H01":
                    authorized = bool(summary["content_read_authorized"])
            aggregate = self._aggregate_command(run_dir)
            process = subprocess.run(aggregate, text=True, capture_output=True, check=False, env=self._test_env())
            self.assertEqual(process.returncode, 0, process.stderr)
            summary_path = run_dir / "VIA_v0140B_WindowsHandle_Summary.json"
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            self.assertEqual(summary["final_gate"], CORE.DEF_PASS_GATE)
            self.assertEqual((summary["terminal_engines"], summary["pass_engines"]), (6, 6))
            self.assertEqual(summary["cross_subsystem_rows"], 18)
            self.assertGreaterEqual(summary["source_open_successes"], 1)
            self.assertGreater(summary["source_bytes_read"], 0)
            self.assertEqual(summary["hydra_violations"], 0)

            h06 = run_dir / "lanes" / f"H06_{CORE.DEF_ENGINE_NAMES['H06']}" / "TERMINAL_SUMMARY.json"
            duplicate = json.loads(h06.read_text(encoding="utf-8"))
            duplicate["lane_root"] = json.loads(
                (run_dir / "lanes" / f"H05_{CORE.DEF_ENGINE_NAMES['H05']}" / "TERMINAL_SUMMARY.json").read_text(encoding="utf-8")
            )["lane_root"]
            h06.write_text(json.dumps(duplicate), encoding="utf-8")
            process = subprocess.run(aggregate, text=True, capture_output=True, check=False, env=self._test_env())
            self.assertEqual(process.returncode, 2)
            failed = json.loads(summary_path.read_text(encoding="utf-8"))
            self.assertEqual(failed["final_gate"], CORE.DEF_FAIL_GATE)
            self.assertIn("LANE_ROOT_NOT_UNIQUE", failed["hydra_evidence"])

    def test_insufficient_preflight_never_opens_content_and_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            missing = Path(temp_dir) / "missing.csv"
            authorized = False
            for index, engine_id in enumerate(CORE.DEF_ENGINE_NAMES, start=1):
                lane = run_dir / "lanes" / f"{engine_id}_{CORE.DEF_ENGINE_NAMES[engine_id]}"
                command = self._lane_command(engine_id, lane, missing, TOKEN, index, authorized)
                process = subprocess.run(command, text=True, capture_output=True, check=False, env=self._test_env())
                self.assertEqual(process.returncode, 0, process.stderr)
                summary = json.loads((lane / "TERMINAL_SUMMARY.json").read_text(encoding="utf-8"))
                if engine_id == "H01":
                    self.assertEqual(summary["outcome"], "PREFLIGHT_METADATA_INSUFFICIENT")
                    authorized = bool(summary["content_read_authorized"])
            process = subprocess.run(
                self._aggregate_command(run_dir), text=True, capture_output=True, check=False, env=self._test_env()
            )
            self.assertEqual(process.returncode, 2)
            summary = json.loads(
                (run_dir / "VIA_v0140B_WindowsHandle_Summary.json").read_text(encoding="utf-8")
            )
            self.assertEqual(summary["final_gate"], CORE.DEF_FAIL_GATE)
            self.assertEqual(
                (summary["source_open_attempts"], summary["source_open_successes"], summary["source_bytes_read"]),
                (0, 0, 0),
            )

    @staticmethod
    def _test_env() -> dict[str, str]:
        env = os.environ.copy()
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        env["VIA_ALLOW_PARQUET_UNAVAILABLE_FOR_PACKAGE_TEST"] = "1"
        return env

    @staticmethod
    def _lane_command(
        engine_id: str,
        lane: Path,
        fixture: Path,
        token: str,
        sequence_index: int = 1,
        authorized: bool = False,
    ) -> list[str]:
        return [
            sys.executable,
            str(PACKAGE_ROOT / CORE.DEF_WRAPPERS[engine_id]),
            "--lane", engine_id,
            "--lane-root", str(lane),
            "--package-root", str(PACKAGE_ROOT),
            "--contract", str(CONTRACT_PATH),
            "--rules", str(RULES_PATH),
            "--source-path", str(fixture),
            "--approval-token", token,
            "--sequence-index", str(sequence_index),
            "--content-read-authorized", "true" if authorized else "false",
            "--self-test",
        ]

    @staticmethod
    def _aggregate_command(run_dir: Path) -> list[str]:
        return [
            sys.executable,
            str(CORE_PATH),
            "--aggregate",
            "--run-dir", str(run_dir),
            "--package-root", str(PACKAGE_ROOT),
            "--contract", str(CONTRACT_PATH),
            "--rules", str(RULES_PATH),
            "--approval-token", TOKEN,
        ]


if __name__ == "__main__":
    unittest.main(verbosity=2)
