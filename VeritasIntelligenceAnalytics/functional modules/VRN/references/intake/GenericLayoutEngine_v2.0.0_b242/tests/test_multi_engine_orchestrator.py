from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

import fitz
from PIL import Image, ImageDraw, ImageFont

from adapter_sdk import AdapterConfig, AdapterContext, AdapterElement, AdapterProbe, AdapterResult, STATUS_PASS, utc_timestamp
from all_backend_engines import build_all_adapters
from multi_engine_orchestrator import OrchestratorConfig, fuse_results, run_orchestrator
from test_generic_layout_engine import build_synthetic_pdf


class MultiEngineOrchestratorTests(unittest.TestCase):
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
        element_a = AdapterElement(page=1, text="Revenue 100", bbox=[10, 10, 100, 20], confidence=0.90)
        element_b = AdapterElement(page=1, text="Revenue 100", bbox=[11, 10, 101, 20], confidence=0.85)
        result_a = AdapterResult("a", 1, 1, STATUS_PASS, utc_timestamp(), 1, ["text"], probe_a, elements=[element_a])
        result_b = AdapterResult("b", 2, 2, STATUS_PASS, utc_timestamp(), 1, ["text"], probe_b, elements=[element_b])
        fused = fuse_results([result_a, result_b], 0.35)
        self.assertEqual(len(fused), 1)
        self.assertEqual(fused[0].source_adapters, ["a", "b"])
        self.assertGreater(fused[0].confidence, 0.90)


if __name__ == "__main__":
    unittest.main()
