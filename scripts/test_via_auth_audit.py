"""Focused checks for redaction and fail-closed source detection."""

import json
import tempfile
import unittest
from pathlib import Path

from via_auth_audit import analyze, latest


class AuthAuditTests(unittest.TestCase):
    def test_latest_numeric_version(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "Gate_v0099.py").write_text("", encoding="utf-8")
            (root / "Gate_v0100.py").write_text("", encoding="utf-8")
            self.assertEqual(latest(root, "Gate").name, "Gate_v0100.py")

    def test_no_secret_value_or_key_file_read(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            via = root / "VeritasIntelligenceAnalytics"
            reg = via / "supportive modules" / "registry"
            reg.mkdir(parents=True)
            (root / "streamlit_app.py").write_text("import streamlit as st\nst.title('Movies')\n", encoding="utf-8")
            (reg / "Register-VIA-Commands-v0001.ps1").write_text("function global:via-gates {}", encoding="utf-8")
            # An output file with a credential must never be opened or reflected.
            key = via / "functional modules" / "VDF" / "output_hub" / "mega" / ".fred_api_key"
            key.parent.mkdir(parents=True)
            key.write_text("TEST_SECRET_DO_NOT_PRINT", encoding="utf-8")
            report = analyze(root, {"FRED_API_KEY": "TEST_SECRET_DO_NOT_PRINT",
                                    "VIA_NET_CONSENT": "YES", "VIA_SCRAPE_CONSENT": "unexpected-private-value"})
            serialized = json.dumps(report, ensure_ascii=False)
            self.assertNotIn("TEST_SECRET_DO_NOT_PRINT", serialized)
            self.assertNotIn("unexpected-private-value", serialized)
            self.assertEqual(report["current_environment"]["scrape"], "CLOSED")
            self.assertEqual(report["sources"][0]["state"], "ABSENT")
            self.assertTrue(all(x["state"] == "REVIEW" for x in report["sources"][1:]))


if __name__ == "__main__":
    unittest.main()
