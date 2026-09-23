"""Broker publisher geometry regression; no network or production data writes."""
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
import os
from pathlib import Path
import sys
import tempfile
import unittest


class BrokerSourceZonesTest(unittest.TestCase):
    def test_small_publishers_on_both_sides_exclude_body(self):
        try:
            import fitz
        except ImportError:
            self.skipTest("PyMuPDF absent; publisher geometry not verified")
        vrn = Path(__file__).resolve().parents[1]
        path = sorted(vrn.glob("VRN_ENG072_FirstPageText_v*.py"))[-1]
        spec = importlib.util.spec_from_file_location(path.stem, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as td:
            pdf = Path(td) / "publisher.pdf"
            doc = fitz.open()
            page = doc.new_page(width=600, height=800)
            page.insert_text((20, 30), "KGI Securities", fontsize=6)
            page.insert_text((380, 40), "Daiwa Securities", fontsize=6)
            page.insert_text((20, 350), "YUANTA Securities body", fontsize=12)
            doc.save(pdf)
            doc.close()
            result = module.extract_page1_zones(pdf)
        self.assertIsNotNone(result)
        self.assertIn("KGI Securities", result["broker_zones"]["left"])
        self.assertIn("Daiwa Securities", result["broker_zones"]["right"])
        self.assertNotIn("YUANTA", str(result["broker_zones"]))
        self.assertIn("YUANTA", result["body"])


if __name__ == "__main__":
    os.environ["VIA_SELFTEST"] = "1"
    unittest.main()
