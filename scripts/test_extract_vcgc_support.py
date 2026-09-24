"""Safety and archive integrity checks for VCGC extraction."""

import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

import extract_vcgc_support as tool


class ExtractVcgcTests(unittest.TestCase):
    def test_numeric_tail_and_zip_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            support = root / tool.VIA_REL / "supportive modules" / "registry"
            support.mkdir(parents=True)
            (support / "F_v0099.py").write_text("old\n", encoding="utf-8")
            (support / "F_v0100.py").write_text("new\n", encoding="utf-8")
            with patch.object(tool, "FAMILIES", ("F",)):
                report, paths = tool.inventory(root)
                self.assertEqual(paths[0].name, "F_v0100.py")
                archive = root / "snapshot.zip"
                tool.write_zip(archive, root, report, paths)
                with self.assertRaisesRegex(ValueError, "overwrite"):
                    tool.write_zip(archive, root, report, paths)
            with zipfile.ZipFile(archive) as zf:
                record = json.loads(zf.read("VCGC_SUPPORT_MANIFEST.json"))["files"][0]
                self.assertEqual(record["sha256"], hashlib.sha256(zf.read(record["path"])).hexdigest())

    def test_refuse_missing_or_escaping_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            support = root / tool.VIA_REL / "supportive modules"
            support.mkdir(parents=True)
            with patch.object(tool, "FAMILIES", ("F",)):
                report, paths = tool.inventory(root)
                with self.assertRaisesRegex(ValueError, "partial"):
                    tool.write_zip(root / "missing.zip", root, report, paths)
                self.assertFalse((root / "missing.zip").exists())
                outside = root / "elsewhere.py"
                outside.write_text("print('outside')\n", encoding="utf-8")
                (support / "F_v0100.py").symlink_to(outside)
                with self.assertRaisesRegex(ValueError, "Unsafe"):
                    tool.select_sources(root / tool.VIA_REL)

    def test_changed_source_leaves_no_partial_zip(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            support = root / tool.VIA_REL / "supportive modules"
            support.mkdir(parents=True)
            path = support / "F_v0100.py"
            path.write_text("before", encoding="utf-8")
            with patch.object(tool, "FAMILIES", ("F",)):
                report, paths = tool.inventory(root)
            path.write_text("after", encoding="utf-8")
            target = root / "changed.zip"
            with self.assertRaisesRegex(ValueError, "changed"):
                tool.write_zip(target, root, report, paths)
            self.assertFalse(target.exists())
            self.assertFalse(list(root.glob(".vcgc_support_*.zip")))


if __name__ == "__main__":
    unittest.main()
