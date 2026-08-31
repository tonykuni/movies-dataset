from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import fitz
from PIL import Image, ImageDraw, ImageFont

from adapter_sdk import (
    AdapterConfig,
    AdapterContext,
    AdapterElement,
    AdapterProbe,
    AdapterResult,
    BaseAdapter,
    STATUS_FAIL,
    STATUS_PASS,
    STATUS_SKIPPED_POLICY,
    STATUS_TIMEOUT,
    evaluate_acceptance,
    utc_timestamp,
)
from all_backend_engines import build_all_adapters
from multi_engine_orchestrator import (
    OrchestratorConfig,
    execute_route,
    fuse_results,
    load_orchestrator_config,
    run_orchestrator,
)
from test_generic_layout_engine import build_synthetic_pdf


class MultiEngineOrchestratorTests(unittest.TestCase):
    def test_attachment_yaml_stack_loads_in_priority_order(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "stack.yaml"
            path.write_text(
                """pdf_extraction_engine:
  version: 2026
  strategy: light_to_heavy_fallback
  mode: auto
  engines:
    - name: pymupdf
      enabled: true
      priority: 2
    - name: pdfplumber
      enabled: true
      priority: 1
    - name: paddleocr
      enabled: false
      priority: 3
""",
                encoding="utf-8",
            )
            config = load_orchestrator_config(path)
            self.assertEqual(config.selected_adapters, ["pdfplumber", "pymupdf"])
            self.assertEqual(config.disabled_adapters, ["paddleocr"])
            self.assertEqual(config.stack_metadata["strategy"], "light_to_heavy_fallback")

    def test_attachment_yaml_rejects_unknown_engine_fields(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "bad.yaml"
            path.write_text(
                """pdf_extraction_engine:
  engines:
    - name: pdfplumber
      priority: 1
      typo_field: true
""",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "unknown keys"):
                load_orchestrator_config(path)

    def test_registry_contains_all_unique_engines_in_resource_order(self) -> None:
        adapters = build_all_adapters()
        names = [adapter.name for adapter in adapters]
        self.assertEqual(len(names), 32)
        self.assertEqual(len(names), len(set(names)))
        self.assertEqual(names[0], "pdfplumber")
        self.assertEqual(names[-1], "adobe_extract_api")
        self.assertEqual(
            [(adapter.resource_level, adapter.priority) for adapter in adapters],
            sorted((adapter.resource_level, adapter.priority) for adapter in adapters),
        )

    def test_every_probe_is_safe(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            context = AdapterContext(
                input_path=root / "probe.pdf",
                work_dir=root,
                config=AdapterConfig(ocr_languages="eng"),
            )
            for adapter in build_all_adapters():
                with self.subTest(adapter=adapter.name):
                    probe = adapter.probe(context)
                    self.assertEqual(probe.name, adapter.name)
                    self.assertIsInstance(probe.available, bool)

    def test_auto_route_stops_after_pdfplumber_quality_gate(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "synthetic.pdf"
            build_synthetic_pdf(source)
            run = run_orchestrator(
                source,
                root / "output",
                OrchestratorConfig(run_core_layout=False),
            )
            self.assertEqual(run.route, ["pdfplumber"])
            self.assertTrue(run.adapter_results[0].accepted)
            self.assertIn("required capabilities met", run.stop_reason)
            self.assertGreater(len(run.canonical_elements), 0)

    def test_second_identical_run_uses_adapter_cache(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "synthetic.pdf"
            output = root / "output"
            build_synthetic_pdf(source)
            config = OrchestratorConfig(run_core_layout=False)
            first = run_orchestrator(source, output, config)
            second = run_orchestrator(source, output, config)
            self.assertFalse(first.adapter_results[0].cache_hit)
            self.assertTrue(second.adapter_results[0].cache_hit)
            self.assertEqual(second.adapter_results[0].duration_ms, 0)
            self.assertGreaterEqual(second.adapter_results[0].cache_source_duration_ms or 0, 0)

    def test_three_engine_consensus_route(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "synthetic.pdf"
            build_synthetic_pdf(source)
            run = run_orchestrator(
                source,
                root / "output",
                OrchestratorConfig(mode="consensus", run_core_layout=False),
            )
            self.assertEqual(run.route, ["pdfplumber", "pymupdf", "pdfminer_six"])
            self.assertTrue(all(result.status == STATUS_PASS for result in run.adapter_results))
            self.assertGreater(len(run.canonical_elements), 0)
            self.assertTrue(any(len(element.source_adapters) >= 2 for element in run.canonical_elements))

    @unittest.skipUnless(shutil.which("tesseract"), "tesseract executable unavailable")
    def test_scanned_image_jumps_to_ocr_lane(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "scan.png"
            image = Image.new("RGB", (1400, 900), "white")
            draw = ImageDraw.Draw(image)
            font_path = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
            font = ImageFont.truetype(str(font_path), 54) if font_path.exists() else ImageFont.load_default()
            draw.text((80, 100), "SCANNED LAYOUT DOCUMENT", fill="black", font=font)
            draw.text((80, 230), "OCR fallback must preserve bounding boxes.", fill="black", font=font)
            image.save(source)
            config = OrchestratorConfig(run_core_layout=False)
            config.adapter.ocr_languages = "eng"
            run = run_orchestrator(source, root / "output", config)
            self.assertEqual(run.route[0], "pdfplumber")
            self.assertEqual(run.route[-1], "tesseract")
            self.assertTrue(run.document_profile["probable_scanned"])
            self.assertTrue(run.adapter_results[-1].accepted)
            self.assertGreater(len(run.canonical_elements), 0)
            self.assertEqual(run.route_decisions[0]["decision"], "jump_to_ocr")
            self.assertNotIn(STATUS_SKIPPED_POLICY, [result.status for result in run.adapter_results])

    @unittest.skipUnless(shutil.which("tesseract"), "tesseract executable unavailable")
    def test_image_only_pdf_jumps_to_ocr_lane(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            raster_path = root / "page.png"
            source = root / "scan.pdf"
            image = Image.new("RGB", (1400, 900), "white")
            draw = ImageDraw.Draw(image)
            font_path = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
            font = ImageFont.truetype(str(font_path), 54) if font_path.exists() else ImageFont.load_default()
            draw.text((80, 100), "IMAGE ONLY PDF", fill="black", font=font)
            draw.text((80, 230), "The PDF has no native text layer.", fill="black", font=font)
            image.save(raster_path)
            document = fitz.open()
            page = document.new_page(width=595, height=842)
            page.insert_image(page.rect, filename=str(raster_path))
            document.save(source)
            document.close()

            config = OrchestratorConfig(run_core_layout=False)
            config.adapter.ocr_languages = "eng"
            run = run_orchestrator(source, root / "output", config)
            self.assertEqual(run.route[0], "pdfplumber")
            self.assertEqual(run.route[-1], "tesseract")
            self.assertTrue(run.document_profile["probable_scanned"])
            self.assertTrue(run.adapter_results[-1].accepted)
            self.assertGreater(len(run.canonical_elements), 0)

    def test_fusion_records_multiple_sources(self) -> None:
        probe_a = AdapterProbe(name="a", available=True)
        probe_b = AdapterProbe(name="b", available=True)
        element_a = AdapterElement(page=1, text="Revenue 100", bbox=[10, 10, 100, 20], confidence=0.90, metadata={"page_width": 200, "page_height": 100})
        element_b = AdapterElement(page=1, text="Revenue 100", bbox=[11, 10, 101, 20], confidence=0.85, metadata={"page_width": 200, "page_height": 100})
        result_a = AdapterResult("a", 1, 1, STATUS_PASS, utc_timestamp(), 1, ["text"], probe_a, elements=[element_a])
        result_b = AdapterResult("b", 2, 2, STATUS_PASS, utc_timestamp(), 1, ["text"], probe_b, elements=[element_b])
        fused = fuse_results([result_a, result_b], 0.35)
        self.assertEqual(len(fused), 1)
        self.assertEqual(fused[0].source_adapters, ["a", "b"])
        self.assertGreater(fused[0].confidence, 0.90)
        self.assertIsNotNone(fused[0].bbox_normalized)

    def test_structure_only_result_uses_structure_gate(self) -> None:
        probe = AdapterProbe(name="layout", available=True)
        result = AdapterResult(
            "layout", 4, 1, STATUS_PASS, utc_timestamp(), 1,
            ["layout", "bbox", "vision"], probe,
            elements=[AdapterElement(page=1, bbox=[1, 2, 30, 40], element_type="FIGURE")],
        )
        accepted, reason, basis = evaluate_acceptance(result, AdapterConfig())
        self.assertTrue(accepted)
        self.assertEqual(basis, "structure")
        self.assertIn("structural", reason)

    def test_artifact_only_result_uses_artifact_gate(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            artifact = Path(temporary_directory) / "searchable.pdf"
            artifact.write_bytes(b"%PDF-1.4\n")
            probe = AdapterProbe(name="ocrmypdf", available=True)
            result = AdapterResult(
                "ocrmypdf", 5, 1, STATUS_PASS, utc_timestamp(), 1,
                ["ocr", "searchable_pdf", "preprocess"], probe,
                artifacts={"searchable_pdf": str(artifact)},
            )
            accepted, _, basis = evaluate_acceptance(result, AdapterConfig())
            self.assertTrue(accepted)
            self.assertEqual(basis, "artifact")

    def test_timeout_isolated_as_status(self) -> None:
        class TimeoutAdapter(BaseAdapter):
            name = "timeout"
            capabilities = ("text",)

            def probe(self, context: AdapterContext) -> AdapterProbe:
                return AdapterProbe(name=self.name, available=True)

            def extract(self, context: AdapterContext) -> AdapterResult:
                raise subprocess.TimeoutExpired(["fake"], 1)

        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "input.pdf"
            source.write_bytes(b"%PDF-1.4\n")
            context = AdapterContext(source, root, AdapterConfig())
            self.assertEqual(TimeoutAdapter().run(context).status, STATUS_TIMEOUT)

    def test_all_mode_continues_after_backend_failure(self) -> None:
        class FailingAdapter(BaseAdapter):
            name = "failing"
            capabilities = ("text",)

            def probe(self, context: AdapterContext) -> AdapterProbe:
                return AdapterProbe(name=self.name, available=True)

            def extract(self, context: AdapterContext) -> AdapterResult:
                raise RuntimeError("injected failure")

        class PassingAdapter(BaseAdapter):
            name = "passing"
            priority = 2
            capabilities = ("text", "bbox", "layout")

            def probe(self, context: AdapterContext) -> AdapterProbe:
                return AdapterProbe(name=self.name, available=True)

            def extract(self, context: AdapterContext) -> AdapterResult:
                probe = self.probe(context)
                return AdapterResult(
                    self.name, 1, 2, STATUS_PASS, utc_timestamp(), 0,
                    list(self.capabilities), probe,
                    elements=[AdapterElement(page=1, text="A sufficiently long injected backend result for quality acceptance.", bbox=[1, 1, 20, 10])],
                    document_text="A sufficiently long injected backend result for quality acceptance.",
                )

        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "input.pdf"
            source.write_bytes(b"%PDF-1.4\n")
            config = OrchestratorConfig(mode="all", run_core_layout=False, use_cache=False)
            with patch("multi_engine_orchestrator.build_route", return_value=[FailingAdapter(), PassingAdapter()]):
                results, route, _, _, _ = execute_route(source, root / "work", config)
            self.assertEqual(route, ["failing", "passing"])
            self.assertEqual([result.status for result in results], [STATUS_FAIL, STATUS_PASS])

    def test_heavy_backend_respects_memory_gate(self) -> None:
        class HeavyAdapter(BaseAdapter):
            name = "heavy"
            heavy = True
            capabilities = ("layout", "bbox")

            def probe(self, context: AdapterContext) -> AdapterProbe:
                return AdapterProbe(name=self.name, available=True)

            def extract(self, context: AdapterContext) -> AdapterResult:
                raise AssertionError("memory-gated adapter must not execute")

        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "input.pdf"
            source.write_bytes(b"%PDF-1.4\n")
            config = OrchestratorConfig(mode="all", run_core_layout=False, use_cache=False)
            config.adapter.min_free_memory_gb_heavy = 1_000_000.0
            with patch("multi_engine_orchestrator.build_route", return_value=[HeavyAdapter()]):
                with patch("adapter_sdk.available_memory_gb", return_value=1.0):
                    results, _, _, _, _ = execute_route(source, root / "work", config)
            self.assertEqual(results[0].status, STATUS_SKIPPED_POLICY)


if __name__ == "__main__":
    unittest.main()
