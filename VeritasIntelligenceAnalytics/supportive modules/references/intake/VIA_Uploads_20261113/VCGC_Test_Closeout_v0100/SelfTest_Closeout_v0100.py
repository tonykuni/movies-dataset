# [VIA:ACCEL-BRIDGE] Regression tests for VCGC Test Closeout v0100
import asyncio
import copy
import json
import os
import sys
import tempfile
import threading
import unittest
import uuid
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from unittest.mock import patch

import VCGC_Test_Closeout_v0100 as app

BASE = Path(__file__).resolve().parent
FIXTURE = BASE / "Profile_Repair_Demo_v0100.json"


class CloseoutTests(unittest.TestCase):
    def setUp(self):
        context = tempfile.TemporaryDirectory(prefix="vcgc-closeout-測試-")
        self.addCleanup(context.cleanup)
        self.root = Path(context.name)
        self.home = self.root / "state"
        self.profile = self.root / "profile.json"
        self.source = self.root / "input"
        self.source.mkdir()
        self.plan = app.read_json(FIXTURE)
        self.plan["source"] = "input"
        for item in self.plan["inputs"]:
            dest = self.source / item
            dest.parent.mkdir(exist_ok=True)
            dest.write_bytes((BASE / item).read_bytes())
        self.plan["checks"] = [c for c in self.plan["checks"] if c["id"] != "native-selftest"]
        self.plan["requirements"]["governance"] = ["INTEGRATION", "CLOSE_OUT"]
        self.plan["checks"][1]["requirements"] = ["fixture"]
        self.plan["checks"][-1]["depends"].remove("native-selftest")
        self.plan["checks"][2] = {"id":"native-faults","stage":"INTEGRATION","kind":"file",
                                   "path":"fixtures/actual.csv","requirements":["governance"]}
        self.plan["repairs"] = []

    def assert_code(self, name, operation):
        with self.assertRaises(app.GateError) as context:
            operation()
        self.assertEqual(context.exception.code, name)

    def launch(self, previous=None, **settings):
        app.save(self.profile, self.plan)
        identity = str(uuid.uuid4())
        result = app.run_pipeline(self.home, self.profile, identity, previous, **settings)
        return identity, result

    def test_native_inventory_and_real_tests(self):
        self.assertEqual(app.inventory()["matrix"]["count"], 14)
        self.assertEqual(app.inventory()["token_history"]["count"], 6)
        self.assertEqual(len(app.cases()), 30)
        result = app.run_pipeline(self.home, BASE / "Profile_VCGC_Native_v0100.json", str(uuid.uuid4()))
        self.assertEqual(result["state"], "PASS_LOCAL")
        self.assertEqual(app.evidence(self.home, result["run_id"], "native-selftest")["proof"]["tests"], 45)
        self.assertEqual(app.evidence(self.home, result["run_id"], "native-faults")["proof"]["tests"], 22)

    def test_f09_interrupted_non_replay_safe_check_stays_blocked(self):
        self.plan["checks"][1]["assertions"].pop()
        check = next(item for item in self.plan["checks"] if item["id"] == "generate")
        check["replay_safe"] = False
        app.save(self.profile, self.plan)
        identity = str(uuid.uuid4())
        original = app.run_check

        def interrupt(item, *args):
            if item["id"] == "generate":
                raise KeyboardInterrupt
            return original(item, *args)

        with patch.object(app, "run_check", side_effect=interrupt), self.assertRaises(KeyboardInterrupt):
            app.run_pipeline(self.home, self.profile, identity)
        self.assert_code("F09", lambda: app.run_pipeline(self.home, self.profile, identity))

    def test_f13_real_subprocess_timeout(self):
        log = self.root / "timeout.log"
        process = app.run_command([sys.executable, "-c", "import time; time.sleep(8)"], self.root, 1, log)
        self.assertTrue(process["timeout"])
        self.assertTrue(process["cleaned"])
        self.assertIsInstance(process["exit"], int)
        self.assertTrue(log.is_file())

    def test_f21_missing_phase_and_dependency(self):
        bad = copy.deepcopy(self.plan)
        bad["checks"][0]["depends"] = ["seal"]
        self.assert_code("F21", lambda: app.validate_profile(bad))
        bad = copy.deepcopy(self.plan)
        bad["checks"].pop()
        self.assert_code("F21", lambda: app.validate_profile(bad))

    def test_f22_empty_junit(self):
        junit = self.root / "result.xml"
        junit.write_text('<testsuite tests="0"/>', encoding="utf-8")
        self.assert_code("F22", lambda: app.check_output(junit, "junit", []))
        junit.write_text('<testsuite><testcase name="x"><skipped/></testcase></testsuite>', encoding="utf-8")
        self.assert_code("F22", lambda: app.check_output(junit, "junit", []))
        junit.write_text('<testsuite><testcase name="x"/></testsuite>', encoding="utf-8")
        self.assertEqual(app.check_output(junit, "junit", [])["cases"], 1)

    def test_f23_retry_is_review(self):
        check = {"id":"retry","kind":"command","argv":["python","-c","pass"],
                 "output":"out.json","format":"json","assertions":[{"path":["ok"],"equals":True}],
                 "retry_timeout":True,"replay_safe":True}
        local = self.root / "logs"
        local.mkdir()
        outcomes = [{"exit":1,"timeout":True,"cleaned":True},{"exit":0,"timeout":False,"cleaned":True}]
        def run(argv, cwd, timeout, log):
            result = outcomes.pop(0)
            if not outcomes:
                app.save(cwd / "out.json", {"ok":True})
            return result
        with patch.object(app, "run_command", side_effect=run):
            self.assert_code("F23", lambda: app.run_check(check, self.source, local, {}))

    def test_f24_stale_output_refused(self):
        stale = self.source / "out.json"
        app.save(stale, {"ok":True})
        check = {"id":"fresh","kind":"command","argv":["python","-c","pass"],
                 "output":"out.json","format":"json","assertions":[{"path":["ok"],"equals":True}]}
        with patch.object(app, "run_command") as runner:
            self.assert_code("F24", lambda: app.run_check(check, self.source, self.root, {}))
            runner.assert_not_called()

    def test_f25_duplicate_and_type(self):
        table = self.root / "duplicate.csv"
        table.write_text("id,value\nA,1\nA,2\n", encoding="utf-8")
        self.assert_code("F25", lambda: app.csv_rows(table, ["id"]))
        result = self.root / "typed.json"
        app.save(result, {"ok":True})
        self.assert_code("F16", lambda: app.check_output(result, "json", [{"path":["ok"],"equals":1}]))

    def test_f26_logs_stay_local(self):
        test = next(check for check in self.plan["checks"] if check["id"] == "generate")
        self.plan["checks"][1]["assertions"].pop()
        test["argv"] = ["python","-c","import sys; print('FIXTURE-SECRET'); sys.exit(1)"]
        identity, result = self.launch()
        self.assertEqual(result["state"], "BLOCKED")
        row = app.evidence(self.home, identity, "generate")
        self.assertNotIn("FIXTURE-SECRET", str(row) + str(app.feedback(self.home, identity)))
        _, epoch, _ = app.completed_run(self.home, identity)
        self.assertIn("FIXTURE-SECRET", (epoch / "baseline/logs/generate.1.log").read_text())

    def test_f27_delta_budget_and_idempotence(self):
        first, result = self.launch()
        self.assertEqual(result["state"], "BLOCKED")
        second, _ = self.launch(previous=first)
        delta = app.feedback(self.home, second, first, 500)
        self.assertEqual(delta["failures"], [])
        self.assertGreater(delta["unchanged"], 0)
        self.assertLessEqual(len(app.encoded(delta)), 500)
        again = app.run_pipeline(self.home, self.profile, second, first)
        self.assertEqual(again["run_id"], second)
        self.assertEqual(len(list((self.home / "runs" / second / "epochs").iterdir())), 1)

    def test_f28_input_mutation_isolated(self):
        self.plan["checks"][1]["assertions"].pop()
        check = next(check for check in self.plan["checks"] if check["id"] == "generate")
        path = "fixtures/needs_repair.json"
        original = (self.source / path).read_bytes()
        check["argv"] = ["python","-c",f"from pathlib import Path; Path({path!r}).write_text('modified')"]
        identity, result = self.launch()
        self.assertEqual(result["state"], "BLOCKED")
        self.assertEqual(app.evidence(self.home, identity, "generate")["code"], "F28")
        self.assertEqual((self.source / path).read_bytes(), original)

    def test_f29_guarded_repair(self):
        self.plan["repairs"] = copy.deepcopy(app.read_json(FIXTURE)["repairs"])
        self.plan["repairs"][0]["expected_sha256"] = "0" * 64
        _, result = self.launch()
        self.assertIn("F29", {row["case"] for row in result["failures"]})
        self.plan["repairs"] = copy.deepcopy(app.read_json(FIXTURE)["repairs"])
        identity, result = self.launch()
        self.assertEqual(result["state"], "PASS_LOCAL")
        self.assertEqual(result["repairs"], 1)
        self.assertEqual(app.evidence(self.home, identity, "input-contract", "baseline")["status"], "FAIL")
        self.assertEqual(app.evidence(self.home, identity, "input-contract", "impact")["status"], "PASS")
        self.assertEqual(app.evidence(self.home, identity, "input-contract", "final")["status"], "PASS")
        self.assertNotIn("ready", app.read_json(self.source / "fixtures/needs_repair.json"))

    def test_f30_final_regression_and_sealed_archive(self):
        self.plan["repairs"] = copy.deepcopy(app.read_json(FIXTURE)["repairs"])
        (self.source / "fixtures/actual.csv").write_text("id,value\nA,999\n", encoding="utf-8")
        identity, result = self.launch()
        self.assertIn("F30", {row["case"] for row in result["failures"]})
        self.assertEqual(app.evidence(self.home, identity, "generate", "impact")["status"], "PASS")
        self.assertEqual(app.evidence(self.home, identity, "csv-reconciliation", "final")["status"], "FAIL")
        _, epoch, _ = app.completed_run(self.home, identity)
        (epoch / "report.html").write_text("changed", encoding="utf-8")
        self.assert_code("F30", lambda: app.completed_run(self.home, identity))

    def test_graph_relationship_enriches_impact(self):
        root = self.root
        graph = root / "graph.json"
        app.save(graph, {"nodes":[{"id":"a","source_file":"fixtures/needs_repair.json"},
                                 {"id":"b","source_file":"fixtures/actual.csv"}],
                         "links":[{"source":"a","target":"b"}]})
        impacted = app.graph_impact(graph, {"fixtures/needs_repair.json"}, root)
        self.assertIn("fixtures/actual.csv", impacted)
        self.assertIn("csv-reconciliation", app.impact_checks({**self.plan, "repairs":[]}, set(), impacted))

    @unittest.skipIf(os.name == "nt", "Executable Graphify test fixture is POSIX")
    def test_graphify_adapter_with_local_cli_fixture(self):
        exe = self.root / "graphify"
        exe.write_text(
            f"#!{sys.executable}\nimport json, sys\nfrom pathlib import Path\n"
            "assert sys.argv[1:5] == ['extract', '.', '--code-only', '--out']\n"
            "out=Path(sys.argv[5])/'graphify-out'\nout.mkdir()\n"
            "(out/'graph.json').write_text(json.dumps({'nodes':[{'id':'a','source_file':'fixtures/build_fixture.py'}],'links':[]}))\n",
            encoding="utf-8")
        exe.chmod(0o755)
        env = {"PATH":str(self.root) + os.pathsep + os.environ["PATH"]}
        with patch.dict(os.environ, env):
            _, result = self.launch(graphify_sha=app.file_sha(exe))
        self.assertEqual(result["graphify"]["state"], "INDEXED")
        self.assertEqual(result["graphify"]["nodes"], 1)

    def test_omniroute_scope_and_dedup(self):
        identity, _ = self.launch()
        calls = []

        class Stub(BaseHTTPRequestHandler):
            def do_POST(self):
                payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                calls.append((self.path, payload))
                result = json.dumps({"choices":[{"message":{"content":"檢查結果契約。"}}],
                                     "usage":{"total_tokens":91}}).encode()
                self.send_response(200)
                self.send_header("Content-Length", str(len(result)))
                self.end_headers()
                self.wfile.write(result)

            def log_message(self, *args):
                pass

        with HTTPServer(("127.0.0.1",0), Stub) as server:
            worker = threading.Thread(target=server.serve_forever, daemon=True)
            worker.start()
            try:
                with patch.dict(os.environ, {"VIA_OMNIROUTE_API_KEY":"fixture-only"}):
                    first = app.omniroute(self.home, identity, "qa/combo", server.server_port)
                    second = app.omniroute(self.home, identity, "qa/combo", server.server_port)
            finally:
                server.shutdown()
                worker.join()
        self.assertEqual(first, second)
        self.assertEqual(first["state"], "ADVICE_ONLY")
        self.assertEqual(first["usage"]["total_tokens"], 91)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][0], "/v1/chat/completions")
        items = json.loads(calls[0][1]["messages"][1]["content"])
        self.assertTrue(items and all(set(item) == {"case","stage"} for item in items))

    @unittest.skipUnless(app.importlib.util.find_spec("mcp"), "Optional MCP dependency unavailable")
    def test_mcp_stdio_shared_tools(self):
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client
        app.save(self.profile, self.plan)

        async def probe():
            params = StdioServerParameters(command=sys.executable, args=[str(BASE / "VCGC_Test_Closeout_v0100.py"),
                                "--home", str(self.home), "mcp", "--profile", str(self.profile)])
            async with stdio_client(params) as (rx, tx):
                async with ClientSession(rx, tx) as session:
                    await session.initialize()
                    tools = {tool.name for tool in (await session.list_tools()).tools}
                    self.assertEqual(len(tools), 6)
                    identity = str(uuid.uuid4())
                    output = await session.call_tool("vcgc_closeout_run", {"request_id":identity})
                    self.assertFalse(output.isError)
                    self.assertEqual(output.structuredContent["state"], "BLOCKED")
                    for name, arguments in {
                        "verbs":{}, "status":{"run_id":identity},
                        "feedback":{"run_id":identity}, "case":{"case_id":"F16"},
                        "evidence":{"run_id":identity,"check_id":"input-contract"},
                    }.items():
                        result = await session.call_tool(f"vcgc_closeout_{name}", arguments)
                        self.assertFalse(result.isError, result)
                    app.save(self.profile, {**self.plan, "id":"changed-profile"})
                    rejected = await session.call_tool("vcgc_closeout_run", {"request_id":str(uuid.uuid4())})
                    self.assertTrue(rejected.isError)

        asyncio.run(probe())


if __name__ == "__main__":
    unittest.main(verbosity=2)
