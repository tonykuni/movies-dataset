from __future__ import annotations

import hashlib
import tempfile
import unittest
import zipfile
from pathlib import Path

from via_nlp_engine.bundle_ops import PACKAGE_FILENAMES, export_reconstruction_package, read_document_bundle
from via_nlp_engine.knowledge import CodeExtractor, KnowledgeBuilder
from via_nlp_engine.text_ops import TextProcessor


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LEXICON_PATH = PROJECT_ROOT / "data" / "lexicon" / "ssot_lexicon.json"
GOVERNANCE_PATH = PROJECT_ROOT / "config" / "governance.json"


class BundleReconstructionTests(unittest.TestCase):
    def test_windows_one_click_wrapper_passes_static_powershell_gate(self) -> None:
        script = PROJECT_ROOT / "scripts" / "Invoke-VIA-DiscussionReconstruction.ps1"
        syntax, spec = CodeExtractor()._inspect("powershell", script.read_text(encoding="utf-8"))
        self.assertIn(syntax["status"], {"valid", "valid_lexical_only"})
        self.assertIn("Invoke-VIADiscussionReconstruction", spec["functions"])
        self.assertIn("Start-VIADiscussionReconstruction", spec["functions"])

    def test_bundle_intake_is_deterministic_and_every_record_is_reconstructable(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "b.md").write_text("User: 決定使用 Python。\n", encoding="utf-8")
            (root / "a.txt").write_text("Assistant: 請保留來源。\n", encoding="utf-8")
            (root / "ignored.exe").write_bytes(b"ignored")
            bundle = read_document_bundle([root])
            self.assertEqual(bundle["completeness"]["file_count"], 2)
            self.assertTrue(bundle["completeness"]["all_extracted_records_exactly_reconstructable"])
            self.assertEqual(
                [item["source_name"] for item in bundle["source_record_ledger"]],
                ["a.txt", "b.md"],
            )
            self.assertNotIn("path", bundle["source_record_ledger"][0])
            for record in bundle["source_record_ledger"]:
                span = record["combined_content_span"]
                recovered = bundle["text"][span["start"] : span["end"]]
                self.assertEqual(hashlib.sha256(recovered.encode("utf-8")).hexdigest(), record["extracted_text_sha256"])

    def test_exported_handoff_package_is_reproducible_and_complete(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "discussion.md"
            source.write_text(
                "User: 決定採用 MAX_BATCH = 32。\n```python\ndef run(value):\n    return value\n```\n",
                encoding="utf-8",
            )
            bundle = read_document_bundle([source])
            builder = KnowledgeBuilder(TextProcessor(LEXICON_PATH), GOVERNANCE_PATH)
            knowledge = builder.knowledge(bundle["text"])
            process_result = {
                "request_id": "TEST-REQUEST",
                "task": "knowledge",
                "language": "mixed",
                "output": knowledge,
                "route": {},
                "resources_before": {},
                "resources_after": {},
                "elapsed_ms": 1.0,
                "cache_hit": False,
                "warnings": [],
                "engine_version": "1.4.0",
            }
            output_dir = root / "output"
            first = export_reconstruction_package(output_dir, bundle, process_result)
            second = export_reconstruction_package(output_dir, bundle, process_result)
            self.assertEqual(first["archive_sha256"], second["archive_sha256"])
            archive = Path(second["archive"])
            with zipfile.ZipFile(archive) as package:
                self.assertIsNone(package.testzip())
                names = set(package.namelist())
            self.assertIn(PACKAGE_FILENAMES["full"], names)
            self.assertIn(PACKAGE_FILENAMES["knowledge_registry"], names)
            self.assertIn(PACKAGE_FILENAMES["code_reconstruction"], names)
            self.assertIn(PACKAGE_FILENAMES["mind_map"], names)
            self.assertIn(PACKAGE_FILENAMES["mind_map_evolution"], names)
            self.assertIn(PACKAGE_FILENAMES["instruction_reconstruction"], names)
            self.assertIn(PACKAGE_FILENAMES["bilingual_knowledge_body"], names)
            self.assertIn(PACKAGE_FILENAMES["handoff"], names)


if __name__ == "__main__":
    unittest.main()
