#!/usr/bin/env python3
from __future__ import annotations

import base64
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "subsystem_builder_v0106_4", ROOT / "scripts" / "build_subsystem_workspaces_v0106_4.py"
)
assert SPEC is not None and SPEC.loader is not None
BUILDER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILDER)
MODEL = ROOT / "data" / "source_model_v0105.json.gz"
if not MODEL.is_file():
    MODEL = Path.home() / "VIA_Matrix_Governance_Full_Model_v0105_1_20261106.json.gz"
EXPECTED_ROWS = {"VCGC": 22, "VDF": 50, "VRN": 24426, "VQG": 33, "VAP": 2135, "Database": 0}
EXPECTED_RED = {"VCGC": 3, "VDF": 1, "VRN": 1, "VQG": 3, "VAP": 3, "Database": 0}
REQUIRED_FIELDS = ("id", "version", "completion_time", "tools")


def mini_model() -> dict:
    row = {
        "status": "RED",
        "id": "A-1",
        "ssot_name": "Owned",
        "system": "VCGC",
        "source": "x.py",
        "source_sha256": "a" * 64,
        "version": "v1",
        "kind": "FILE",
        "scope": "STATIC",
        "evidence": ["SOURCE"],
        "custom": "=SUM(A1:A2)",
        "error_detail": "NOT_OBSERVED",
    }
    other = {**row, "id": "B-1", "system": "VDF", "status": "YELLOW"}
    shared = {**row, "id": "S-1", "system": "VIA_SHARED", "status": "YELLOW"}
    matrices = {name: [] for name in BUILDER.ALL_MATRIX_NAMES}
    matrices["files"] = [row, other, shared]
    matrices["systems"] = [{**row, "id": "SYS-1"}]
    return {"version": "v0105", "counts": {}, "matrices": matrices, "errors": [], "meta": {"actual_release": "RED / BLOCKED"}}


def display_rows(model: dict, system: str) -> list[dict]:
    result = []
    for category in BUILDER.ALL_MATRIX_NAMES:
        for raw in BUILDER.filtered_matrix(model, system)[category]:
            item = {**raw, "category": category}
            for key in REQUIRED_FIELDS:
                item.setdefault(key, "NOT_OBSERVED")
            result.append(item)
    return result


def chunk_rows(rows: list[dict], size: int = 100) -> list[list[dict]]:
    return [rows[start : start + size] for start in range(0, len(rows), size)] or [[]]


class SubsystemBuilderV0106_2Tests(unittest.TestCase):
    def test_strict_duplicate_and_nonfinite_json_rejected(self):
        with self.assertRaises(BUILDER.BuildError):
            BUILDER.strict_json_loads('{"x":1,"x":2}')
        with self.assertRaises(BUILDER.BuildError):
            BUILDER.strict_json_loads('{"x":NaN}')

    def test_exact_system_filter_and_lossless_row(self):
        model = mini_model()
        original = json.loads(json.dumps(model["matrices"]["files"][0]))
        filtered = BUILDER.filtered_matrix(model, "VCGC")
        self.assertEqual([row["id"] for row in filtered["files"]], ["A-1"])
        self.assertEqual(filtered["files"][0], original)
        self.assertFalse(any(row.get("system") == "VIA_SHARED" for row in filtered["files"]))

    def test_shared_subset_is_separate_and_not_promoted(self):
        model = mini_model()
        shared = BUILDER.shared_subset(model)
        self.assertEqual(len(shared), 1)
        self.assertEqual(shared[0]["row"]["system"], "VIA_SHARED")
        own = BUILDER.filtered_matrix(model, "VCGC")
        self.assertEqual(sum(map(len, own.values())), 2)
        self.assertEqual(BUILDER.stats_for("VCGC", own, shared)["rows_total"], 2)

    def test_original_category_order_and_union_contract(self):
        self.assertEqual(BUILDER.ALL_MATRIX_NAMES, ("systems", "io", "commands", "files", "environment", "policy", "conflicts", "requirements", "tests"))
        self.assertEqual(BUILDER.STATUS_CODES, ("RED", "YELLOW", "GREEN"))
        js = (ROOT / "scripts" / "subsystem_v0106_4.js").read_text(encoding="utf-8")
        self.assertIn("const columns = ['status', 'id', 'ssot_name', 'category', 'version', 'completion_time', 'tools']", js)
        self.assertIn("columns.push('error_detail')", js)
        self.assertIn("r.system == system exactly", js)

    def test_payload_has_gzip_sha_and_native_decode_contract(self):
        model = mini_model()
        source = {"path": "source.gz", "sha256": "b" * 64, "bytes": 10, "raw_bytes": 100, "raw_sha256": "c" * 64, "model_version": "v0105"}
        envelope, details = BUILDER.make_payload(model, source, "VCGC", BUILDER.shared_subset(model))
        compressed = base64.b64decode(envelope["base64"])
        self.assertEqual(hashlib.sha256(compressed).hexdigest(), envelope["gzip_sha256"])
        decoded = json.loads(gzip.decompress(compressed))
        self.assertEqual(decoded["LAST_MATRIX"]["files"][0]["id"], "A-1")
        self.assertIn("DATABASE_HISTORICAL_GOVERNANCE", decoded)
        self.assertIn("DecompressionStream", (ROOT / "scripts" / "subsystem_v0106_4.js").read_text(encoding="utf-8"))
        self.assertIn("crypto.subtle", (ROOT / "scripts" / "subsystem_v0106_4.js").read_text(encoding="utf-8"))
        self.assertGreater(details["stats"]["rows_total"], 0)

    def test_supplemental_observations_are_pinned_and_non_native(self):
        observations = BUILDER.load_supplemental_observations(ROOT)
        self.assertEqual(observations["kind"], "SHARED_CANDIDATE_OR_SESSION_OBSERVATIONS")
        self.assertTrue(observations["not_native_test_counts"])
        self.assertEqual(observations["live"]["github"]["health_result"], "PASS_READ_ONLY_3_GETS")
        self.assertEqual(observations["token_context"]["count"], 5)
        self.assertEqual(observations["token_tools"]["count"], 5)
        self.assertEqual(observations["provenance"]["observations"]["sha256"], BUILDER.EXPECTED_OBSERVATIONS_SHA256)
        self.assertEqual(observations["provenance"]["token_context"]["sha256"], BUILDER.EXPECTED_TOKEN_CONTEXT_SHA256)
        self.assertEqual(observations["provenance"]["token_tools"]["sha256"], BUILDER.EXPECTED_TOKEN_TOOLS_SHA256)
        self.assertNotIn("argv", json.dumps(observations, ensure_ascii=False))

    def test_historical_database_sources_are_separate_and_pinned(self):
        history = BUILDER.load_database_historical_governance(ROOT)
        self.assertFalse(history["live"])
        self.assertEqual(history["owned_rows"], 0)
        self.assertEqual(len(history["matrix_records"]), 1)
        self.assertEqual(len(history["coverage_records"]), 1)
        self.assertEqual(history["provenance"]["matrix"]["sha256"], BUILDER.EXPECTED_HISTORICAL_MATRIX_SHA256)
        self.assertEqual(history["provenance"]["coverage"]["sha256"], BUILDER.EXPECTED_HISTORICAL_COVERAGE_SHA256)

    def test_safe_script_json_and_no_innerhtml_or_external_assets(self):
        escaped = BUILDER.safe_script_json({"value": "</script><img src=\"https://bad\">&"})
        self.assertNotIn("</script>", escaped)
        self.assertIn(r"\u003c/script\u003e", escaped)
        for name in ("subsystem_v0106_4.html", "subsystem_v0106_4.js"):
            source = (ROOT / "scripts" / name).read_text(encoding="utf-8")
            self.assertNotIn("innerHTML", source)
            self.assertNotRegex(source, r"(?:src|href)=[\"']https?://")

    def test_logo_descriptor_pin_and_locked_titles(self):
        descriptor = json.loads((ROOT / "data" / "brand_asset_v0105.json").read_text(encoding="utf-8"))
        asset = ROOT / descriptor["assets"]["embedded_header"]["path"]
        self.assertEqual(BUILDER.sha256_file(asset), descriptor["assets"]["embedded_header"]["sha256"])
        html = (ROOT / "scripts" / "subsystem_v0106_4.html").read_text(encoding="utf-8")
        self.assertIn("VIA · ARCHITECTURE BASELINE · 2026-11-05 · ENGINE v0103", html)
        self.assertIn("VIA System Architecture &amp; Integration Blueprint", html)
        self.assertIn("ENG049 v0102 VISUAL LOCK", html)
        self.assertIn("v0106.4 CANDIDATE", html)
        self.assertIn('href="governance-preview-v0105.3.html"', html)

    def test_csv_formula_safe_print_and_red_only_animation_contracts(self):
        js = (ROOT / "scripts" / "subsystem_v0106_4.js").read_text(encoding="utf-8")
        css = (ROOT / "scripts" / "subsystem_v0106_4.css").read_text(encoding="utf-8")
        self.assertIn(r"/^\s*[=+@-]/", js)
        self.assertIn("redSlowPulse 2.8s", css)
        self.assertIn(".status-dot.yellow", css)
        self.assertIn(".status-dot.green", css)
        self.assertIn("prefers-reduced-motion: reduce", css)
        self.assertIn("PDF_PART_SIZE = 100", js)
        self.assertIn("el('article', 'print-record')", js)
        self.assertIn("Native print dialog", js)
        self.assertNotIn("function printTable", js)
        self.assertNotIn(".print-matrix", css)

    def test_source_caps_and_hash_pin_are_explicit(self):
        self.assertEqual(BUILDER.MAX_GZIP_BYTES, 80 * 1024 * 1024)
        self.assertEqual(BUILDER.MAX_RAW_BYTES, 80 * 1024 * 1024)
        self.assertRegex(BUILDER.EXPECTED_SOURCE_SHA256, r"^[0-9a-f]{64}$")
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "bad.json.gz"
            path.write_bytes(gzip.compress(b'{"version":"v0105"}'))
            with self.assertRaises(BUILDER.BuildError):
                BUILDER.load_authoritative_model(path, expected_sha256="0" * 64, expected_bytes=path.stat().st_size)

    def test_output_create_once_refuses_changed_bytes(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "out.bin"
            BUILDER._create_once(path, b"one")
            BUILDER._create_once(path, b"one")
            with self.assertRaises(BUILDER.BuildError):
                BUILDER._create_once(path, b"two")

    def test_real_source_exact_counts_reds_and_pinned_hash(self):
        model, source = BUILDER.load_authoritative_model(MODEL)
        self.assertEqual(source["sha256"], BUILDER.EXPECTED_SOURCE_SHA256)
        self.assertEqual(source["raw_sha256"], BUILDER.EXPECTED_RAW_SHA256)
        for system, total in EXPECTED_ROWS.items():
            own = BUILDER.filtered_matrix(model, system)
            self.assertEqual(sum(len(rows) for rows in own.values()), total)
            flat = [row for rows in own.values() for row in rows]
            self.assertEqual(sum(BUILDER.status_code(row.get("status")) == "RED" for row in flat), EXPECTED_RED[system])
            if system != "Database":
                self.assertEqual(own["systems"][0]["status"], "RED")
            else:
                self.assertTrue(all(len(rows) == 0 for rows in own.values()))
        self.assertEqual(source["raw_bytes"], 35440522)

    def test_chunk_completeness_nonoverlap_and_full_fields(self):
        model, _ = BUILDER.load_authoritative_model(MODEL)
        for system, expected in EXPECTED_ROWS.items():
            raw_records = [(category, index, row) for category in BUILDER.ALL_MATRIX_NAMES for index, row in enumerate(BUILDER.filtered_matrix(model, system)[category])]
            display_records = display_rows(model, system)
            chunks = chunk_rows(display_records, 100)
            flattened = [row for chunk in chunks for row in chunk]
            self.assertEqual(len(flattened), expected)
            self.assertEqual(len(flattened), sum(len(chunk) for chunk in chunks))
            self.assertEqual(len({(row.get("category"), row.get("id"), index) for index, row in enumerate(flattened)}), expected)
            for (_, _, raw), displayed in zip(raw_records, display_records):
                self.assertTrue(set(raw).issubset(displayed))
                self.assertTrue(all(key in displayed and displayed[key] == "NOT_OBSERVED" for key in REQUIRED_FIELDS if key not in raw))
            if expected:
                self.assertEqual(display_records[0]["id"], flattened[0]["id"])
                self.assertEqual(display_records[-1]["id"], flattened[-1]["id"])

    def test_required_missing_fields_and_explicit_source_semantics(self):
        js = (ROOT / "scripts" / "subsystem_v0106_4.js").read_text(encoding="utf-8")
        self.assertIn("if (value === false && stage === 'registration' && key === 'formal_registration') return 'NOT_REGISTERED false'", js)
        self.assertIn("installed_status", js)
        self.assertIn("function stageStatusCode", js)
        self.assertIn("normalized === 'PASS'", js)
        self.assertIn("normalized === 'FAIL'", js)
        self.assertIn("raw_last_matrix_lossless", js)
        self.assertIn("DISPLAY_MATRIX", js)

    def test_workflow_is_evidence_map_first_and_edges_never_fabricated(self):
        js = (ROOT / "scripts" / "subsystem_v0106_4.js").read_text(encoding="utf-8")
        html = (ROOT / "scripts" / "subsystem_v0106_4.html").read_text(encoding="utf-8")
        self.assertIn("Evidence Relationship Map", html)
        self.assertIn("label: 'DECLARED'", js)
        self.assertIn("nodes are intentionally unconnected", js)
        self.assertNotIn("for (const row of allOwnedRows())", js[js.index("function relationshipEdges"):js.index("function renderWorkflow")])
        self.assertIn("border-left: 2px dashed", (ROOT / "scripts" / "subsystem_v0106_4.css").read_text(encoding="utf-8"))

    def test_manifest_if_built_has_safety_flags_and_separate_counts(self):
        manifest_path = ROOT / "data" / "subsystem_manifest_v0106_4.json"
        if not manifest_path.exists():
            self.fail("v0106.4 build must run before this suite; no silent skip")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["version"], "v0106.4")
        self.assertFalse(manifest["formal_registration"])
        self.assertFalse(manifest["production"])
        self.assertTrue(all(value is False for value in manifest["safety_flags"].values()))
        self.assertEqual(manifest["shared_subset"]["rows"], 116)
        self.assertEqual(manifest["source_counts"]["shared_rows_separate"], 116)
        self.assertEqual(manifest["source_counts"]["supplemental_token_context_rows"], 5)
        self.assertEqual(manifest["source_counts"]["supplemental_token_tools_rows"], 5)
        self.assertEqual(manifest["database_historical_governance"]["matrix"]["sha256"], BUILDER.EXPECTED_HISTORICAL_MATRIX_SHA256)
        for page in manifest["systems"].values():
            self.assertLess(page["bytes"], 3 * 1024 * 1024)


if __name__ == "__main__":
    unittest.main()
