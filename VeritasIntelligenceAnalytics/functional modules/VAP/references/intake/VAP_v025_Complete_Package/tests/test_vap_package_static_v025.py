import json
import hashlib
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "ui" / "VAP_Workbench_v025.html").read_text(encoding="utf-8")


class IdCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []

    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key == "id":
                self.ids.append(value)


class PackageStaticTests(unittest.TestCase):
    def test_workbench_version_and_modules(self):
        self.assertIn("const APP_VERSION = 'v025'", HTML)
        for name in ("vap-core-engine-v025.js", "vap-plotly-renderer-v025.js", "vap-runtime-bridge-v025.js"):
            self.assertIn('../js/' + name, HTML)
            self.assertTrue((ROOT / "js" / name).exists())

    def test_ui_topology_and_unique_ids(self):
        parser = IdCollector()
        parser.feed(HTML)
        self.assertEqual(len(parser.ids), len(set(parser.ids)))
        self.assertEqual(len(re.findall(r'id="flowStep[1-7]"', HTML)), 7)
        self.assertIn('id="runtimeEndpoint"', HTML)
        self.assertIn('id="pairParameterToggle"', HTML)
        self.assertIn('id="savedImageSearch"', HTML)

    def test_governance_and_workflow_contracts(self):
        for evidence in (
            "VIA-VDF-VAP-CONNECTION-MANIFEST/1.0", "Adjusted Price", "TA-Lib",
            "SYNC CONNECTED", "persistSnapshotToRuntime", "waitForRuntimeRefresh",
            "STRICT_INTERSECTION_SHARED_DOMAIN_BOTTOM_AXIS_ONLY", "US T → Next TW Trading Day",
            "VIA-VAP-OBSERVATION-SPEC/1.0", "pairObservationFrequency", "pairObservationMode",
            "saveObservationBookmark", "pairEvidenceBadge",
        ):
            self.assertIn(evidence, HTML)
        self.assertIn("const QA_REQUIRED_FULL_TESTS = 136", HTML)
        self.assertIn("const QA_REQUIRED_USER_TESTS = 72", HTML)
        self.assertEqual(len(re.findall(r"\{layer:'[A-Z_]+'\s*,name:", HTML)), 136)
        self.assertEqual(len(re.findall(r"\{id:'UAT-[0-9]+'", HTML)), 72)

    def test_config_and_vdf_manifest(self):
        config = json.loads((ROOT / "config" / "vap_runtime_config.json").read_text(encoding="utf-8"))
        manifest = json.loads((ROOT / "config" / "vdf_connection_manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(config["host"], "127.0.0.1")
        self.assertTrue(config["syncConnectOnStart"])
        self.assertEqual(manifest["schema"], "VIA-VDF-VAP-CONNECTION-MANIFEST/1.0")
        self.assertEqual(manifest["stockConnectionTemplate"]["adjustedPriceField"], "adjClose")
        self.assertEqual(manifest["stockConnectionTemplate"]["taLibEvidence"]["engine"], "TA-Lib")

    def test_powershell_launcher_contract(self):
        launcher = (ROOT / "Invoke-VAP-v025.ps1").read_text(encoding="utf-8")
        for token in ("param(", "function def_Write-Step", "--run-self-test", "--sync-connect", "VDF → Adjusted Price Gate → TA-Lib", "InstallBrowserTests", "npm install --no-audit --no-fund"):
            self.assertIn(token, launcher)
        self.assertNotIn("Remove-Item", launcher)

    def test_browser_user_test_contract(self):
        package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
        browser_test = (ROOT / "tests" / "test_browser_uat_v025.js").read_text(encoding="utf-8")
        runner = (ROOT / "tests" / "run_all_tests_v025.py").read_text(encoding="utf-8")
        self.assertIn("playwright", package["devDependencies"])
        for token in ("runTestDebugActivate", "fullCounts.PASS >= 136", "userCounts.PASS >= 72", "pairEvidenceBadge", "pairParametersCollapsed"):
            self.assertIn(token, browser_test)
        self.assertIn("def_find_browser", runner)
        self.assertIn("test_browser_uat_v025.js", runner)

    def test_package_manifest_integrity(self):
        manifest = json.loads((ROOT / "spec" / "vap_package_manifest_v025.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["schema"], "VIA-VAP-PACKAGE-MANIFEST/1.1")
        self.assertEqual(manifest["fileCount"], len(manifest["files"]))
        for relative, expected in manifest["files"].items():
            file_path = ROOT / relative
            self.assertTrue(file_path.is_file(), relative)
            self.assertEqual(hashlib.sha256(file_path.read_bytes()).hexdigest(), expected, relative)


if __name__ == "__main__":
    unittest.main()
