"""Focused safety tests for the MDL135 eight-hub extension."""
import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

MODULE = Path(__file__).with_name("CGC_MDL135_EnvGovernance_8Hub_v0100.py")
if not MODULE.exists():
    MODULE = (Path(__file__).resolve().parents[1] / "supportive modules" / "registry"
              / "CGC_MDL135_EnvGovernance_8Hub_v0100.py")
SPEC = importlib.util.spec_from_file_location("eight_hub", MODULE)
EXT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(EXT)


class FakeCore:
    def __init__(self):
        self.applied = []

    def run_cmd(self, argv, timeout=0):
        if "--dry-run" in argv:
            return {"rc": 0, "out": "resolved", "err": ""}
        return {"rc": 0, "out": "No broken requirements found.", "err": ""}

    def canon(self, name):
        return name.lower()

    def tools_apply(self, plan, approve, bootstrap_prechecked=False):
        self.applied.extend(plan["stages"])
        return {"ran": len(plan["stages"]), "fails": 0}

    def unitest_gate(self):
        return True, "GREEN"

    def rungate_bootstrap_only(self):
        return False, ""


class EightHubTests(unittest.TestCase):
    def test_execute_with_bad_base_does_not_invoke_install(self):
        core = FakeCore()
        core._arg_after = lambda args, key: None
        core._consent = lambda: True
        with tempfile.TemporaryDirectory() as tmp:
            core.OUT = Path(tmp)
            core.LKGC_LATEST = Path(tmp) / "LKGC_latest.json"
            snap = {"rows": [{"env": "BASE", "state": "BLOCK", "checks": {
                "interpreter_identity": {"state": "BLOCK", "detail": "changed"}}}],
                "drift": {"state": "CHANGED", "why": "different interpreter"},
                "toolplan": {"stages": [{"id": "T01", "kind": "INSTALL_TOOLS",
                                        "env": "via_vrn", "pkgs": ["duckdb"]}]},
                "base_analysis": {}, "diagnostics": {}, "runtime_commands": {},
                "baseline": "baseline", "roster": "roster"}
            with patch.object(EXT, "_snapshot", return_value=snap), patch.object(
                EXT, "_apply_green", side_effect=AssertionError("must not install")):
                rc = EXT.run(core, ["--execute"])
        self.assertEqual(rc, 2)
        self.assertFalse(core.applied)

    def test_conflicted_base_blocks(self):
        core = FakeCore()
        row = EXT._risk_row(core, {"env": {"name": "BASE", "py": "python"}, "ok": True,
                                    "python": "3.13", "dists": {"torch": {"ver": "2"}},
                                    "conflicts": [{"kind": "MISSING"}]},
                            {"state": "OK"}, {"stages": [], "external": []},
                            {"base": {"never_in_base_families": ["deep_learning"]},
                             "families": {"deep_learning": {"members": ["torch"]}}})
        self.assertEqual(row["state"], "BLOCK")
        self.assertEqual(row["checks"]["family_isolation"]["state"], "BLOCK")

    def test_only_green_install_stages_reach_existing_installer(self):
        core = FakeCore()
        plan = {"stages": [
            {"id": "T01", "kind": "INSTALL_TOOLS", "env": "via_vrn", "pkgs": ["duckdb"], "deps": []},
            {"id": "T02", "kind": "VERIFY_TOOLS", "env": "via_vrn", "deps": ["T01"]},
            {"id": "T03", "kind": "REPAIR_TOOLS", "env": "via_bad", "pkgs": ["numpy"], "deps": []},
            {"id": "T04", "kind": "INSTALL_TOOLS", "env": "via_bad", "pkgs": ["pandas"], "deps": ["T03"]},
        ]}
        result = EXT._apply_green(core, [{"env": "via_vrn", "state": "PASS"},
                                         {"env": "via_bad", "state": "BLOCK"}],
                                  [{"env": "via_vrn", "state": "PASS"}], plan)
        self.assertEqual([s["id"] for s in core.applied], ["T01", "T02"])
        self.assertEqual(result["summary"]["ran"], 2)

    def test_provision_never_overwrites_an_existing_or_non_via_dir(self):
        core = FakeCore()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "via_existing").mkdir()
            plan = {"stages": [
                {"kind": "ENSURE_ENV", "env": "via_existing", "python": "3.12"},
                {"kind": "ENSURE_ENV", "env": "bad_name", "python": "3.12"},
            ]}
            with patch.object(EXT.shutil, "which", return_value="uv"):
                rows = EXT._provision_missing(core, plan, str(root))
            self.assertEqual([r["state"] for r in rows], ["BLOCK", "BLOCK"])
            self.assertTrue((root / "via_existing").exists())

    def test_canonical_installer_bootstrap_only_allows_install(self):
        source = MODULE.with_name("CGC_MDL135_EnvGovernance_v0114.py")
        if not source.exists():
            self.skipTest("canonical MDL135 source is not in this isolated layout")
        spec = importlib.util.spec_from_file_location("via_envgov_test", source)
        gov = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(gov)
        stages = [
            {"id": "R", "kind": "REPAIR_TOOLS", "env": "via_vrn", "py": "python",
             "pkgs": ["broken"], "deps": [], "result": {}},
            {"id": "I", "kind": "INSTALL_TOOLS", "env": "via_vrn", "py": "python",
             "pkgs": ["duckdb"], "deps": [], "result": {}},
        ]
        with tempfile.TemporaryDirectory() as temp, patch.object(gov, "_consent", return_value=True), \
             patch.object(gov, "unitest_gate", return_value=(False, "family missing")), \
             patch.object(gov, "run_cmd", return_value={"rc": 0, "out": "ok", "err": "", "s": 0}), \
             patch.object(gov, "log_event"), patch.object(gov, "OUT", Path(temp)):
            plan = {"stages": [dict(s) for s in stages]}
            result = gov.tools_apply(plan, True, bootstrap_prechecked=True)
            self.assertEqual(result["ran"], 1)
            self.assertEqual(plan["stages"][0]["result"]["state"], "SKIP")
            self.assertEqual(plan["stages"][1]["result"]["state"], "OK")
            blocked = {"stages": [dict(s) for s in stages]}
            result = gov.tools_apply(blocked, True)
            self.assertEqual(result["ran"], 0)


if __name__ == "__main__":
    unittest.main()
