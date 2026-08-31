from __future__ import annotations

import json
import shutil
import sqlite3
import tempfile
import unittest
from pathlib import Path

import fitz
from PIL import Image, ImageDraw, ImageFont

from generic_layout_engine import EngineConfig, analyze_document


def build_synthetic_pdf(path: Path) -> None:
    image_path = path.with_suffix(".figure.png")
    figure = Image.new("RGB", (360, 180), "white")
    draw = ImageDraw.Draw(figure)
    draw.line((30, 145, 330, 145), fill="black", width=2)
    draw.line((30, 20, 30, 145), fill="black", width=2)
    draw.line((30, 130, 100, 90, 180, 105, 260, 50, 330, 35), fill="#2f80ed", width=4)
    draw.text((42, 24), "Series A", fill="black")
    figure.save(image_path)

    document = fitz.open()
    for page_number in (1, 2):
        page = document.new_page(width=595, height=842)
        page.insert_text((42, 32), "Generic Layout Engine Test", fontsize=7)
        page.insert_text((230, 805), f"- {page_number} -", fontsize=7)
        if page_number == 1:
            page.insert_text((42, 82), "Annual Research Report", fontsize=22, fontname="hebo")
            page.insert_text((42, 122), "1. Executive Overview", fontsize=16, fontname="hebo")
            page.insert_text((42, 150), "This is the main body paragraph used to establish the body font size.", fontsize=10)
            page.insert_text((42, 170), "A second body line confirms paragraph-level classification.", fontsize=10)
            page.insert_text((42, 210), "1.1 Key Observation", fontsize=12, fontname="hebo")
            page.insert_text((42, 232), "The document contains a table and one figure for layout testing.", fontsize=10)

            page.insert_text((42, 280), "Table 1: Quarterly Data", fontsize=10, fontname="hebo")
            x_values = [42, 180, 300, 420, 540]
            y_values = [300, 330, 360, 390]
            for x in x_values:
                page.draw_line((x, y_values[0]), (x, y_values[-1]), color=(0, 0, 0), width=0.8)
            for y in y_values:
                page.draw_line((x_values[0], y), (x_values[-1], y), color=(0, 0, 0), width=0.8)
            table_text = [
                (50, 320, "Metric"), (190, 320, "Q1"), (310, 320, "Q2"), (430, 320, "Q3"),
                (50, 350, "Revenue"), (190, 350, "100"), (310, 350, "120"), (430, 350, "150"),
                (50, 380, "Profit"), (190, 380, "20"), (310, 380, "25"), (430, 380, "31"),
            ]
            for x, y, text in table_text:
                page.insert_text((x, y), text, fontsize=8)
            page.insert_text((42, 408), "Source: Synthetic data", fontsize=7)

            page.insert_text((42, 452), "Figure 1: Trend Overview", fontsize=10, fontname="hebo")
            page.insert_image(fitz.Rect(42, 465, 402, 645), filename=str(image_path))
            page.insert_text((42, 662), "Source: Generated locally", fontsize=7)
        else:
            page.insert_text((42, 90), "2. Closing Notes", fontsize=16, fontname="hebo")
            page.insert_text((42, 120), "This page confirms repeated running headers and footers.", fontsize=10)
            page.insert_text((42, 690), "Important disclosures: This synthetic document is not investment advice.", fontsize=7)
            page.insert_text((42, 705), "Disclaimer: generated only for software verification.", fontsize=7)
    document.save(path)
    document.close()
    image_path.unlink(missing_ok=True)


class GenericLayoutEngineTests(unittest.TestCase):
    def test_end_to_end(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temp_path = Path(temporary_directory)
            source = temp_path / "synthetic.pdf"
            output = temp_path / "output"
            build_synthetic_pdf(source)
            config = EngineConfig(ocr_mode="never", dpi=120)
            document, outputs = analyze_document(source, output, config)

            self.assertEqual(document.statistics["page_count"], 2)
            self.assertGreater(document.statistics["element_count"], 10)
            categories = {
                (element.element_type, element.subtype)
                for page in document.pages
                for element in page.elements
            }
            self.assertIn(("TEXT", "H1"), categories)
            self.assertIn(("TEXT", "H2"), categories)
            self.assertIn(("META", "PAGE_NUMBER"), categories)
            self.assertIn(("TABLE", "CONTENT"), categories)
            self.assertIn(("FIGURE", "CONTENT"), categories)
            self.assertIn(("FIGURE", "CAPTION"), categories)

            element_ids = [element.element_id for page in document.pages for element in page.elements]
            self.assertEqual(len(element_ids), len(set(element_ids)))
            self.assertTrue(
                all(element.source_fingerprint for page in document.pages for element in page.elements)
            )

            for key in ("json", "jsonl", "csv", "sqlite", "html", "manifest"):
                self.assertTrue(outputs[key])
                self.assertTrue((output / str(outputs[key])).exists())

            payload = json.loads((output / "layout_document.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["schema_version"], "GLE-LAYOUT/1.0")
            self.assertTrue(payload["pages"][0]["elements"])

            connection = sqlite3.connect(output / "layout.sqlite")
            try:
                count = connection.execute("SELECT COUNT(*) FROM elements").fetchone()[0]
            finally:
                connection.close()
            self.assertEqual(count, document.statistics["element_count"])

    def test_config_rejects_invalid_ocr_mode(self) -> None:
        config = EngineConfig(ocr_mode="invalid")
        with self.assertRaisesRegex(ValueError, "ocr_mode"):
            config.validate()

    @unittest.skipUnless(shutil.which("tesseract"), "tesseract executable is unavailable")
    def test_image_ocr_lane(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temp_path = Path(temporary_directory)
            image_path = temp_path / "scan.png"
            output = temp_path / "ocr_output"
            image = Image.new("RGB", (1400, 900), "white")
            draw = ImageDraw.Draw(image)
            font_path = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
            font = ImageFont.truetype(str(font_path), 56) if font_path.exists() else ImageFont.load_default()
            draw.text((90, 100), "SCANNED DOCUMENT TITLE", fill="black", font=font)
            draw.text((90, 240), "This page tests local OCR layout extraction.", fill="black", font=font)
            image.save(image_path)

            config = EngineConfig(ocr_mode="always", ocr_languages="eng", dpi=180)
            document, _ = analyze_document(image_path, output, config)
            self.assertEqual(document.statistics["page_count"], 1)
            self.assertEqual(document.statistics["ocr_page_count"], 1)
            self.assertGreater(document.statistics["element_count"], 0)
            self.assertTrue(any("tesseract" in element.source_method for element in document.pages[0].elements))


if __name__ == "__main__":
    unittest.main()
