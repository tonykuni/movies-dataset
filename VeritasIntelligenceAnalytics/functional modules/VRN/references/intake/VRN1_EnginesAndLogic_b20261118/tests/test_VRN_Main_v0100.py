# -*- coding: utf-8 -*-
# ===== [VRN:ID:v0100] VRN-TST005 · test_VRN_Main_v0100 v0100 · TEST =====
# AST 注入（只加註解，AST 不變）：類別 26 · 函式 161；逐一編號在 ssot/VRN_ID_SSOT_v0100.json
# ===== [VRN:ID:END] =====
"""Unit tests for VRN_Main_v0100 (stdlib only): SSOT books, registry, accelerator wiring, standalone copy."""

from __future__ import annotations

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

import argparse
import ast
import csv
import importlib.util
import json
import os
import re
import subprocess
import stat
import sys
import tempfile
import textwrap
import threading
import unittest
from pathlib import Path

VRN_ROOT = Path(__file__).resolve().parents[1]
MAIN_PATH = VRN_ROOT / "VRN_Main_v0100.py"

# A stand-in accelerator with the public surface VRN_Main uses; the real one lives in the operator's mother tree.
STUB_ACCEL = textwrap.dedent('''
    CANONICAL = "SUP_MDL737_SuperAccelModule_v9999.py"
    CALLS = []
    def accel_map(fn, items, workers=None):
        CALLS.append(len(list(items)) if not isinstance(items, list) else len(items))
        return [(True, fn(x)) for x in items]
    def activate(apply_limits=True):
        return {"celeritas": False, "libs_total": 3, "libs_available": 1, "capability_real": 0,
                "capability_total": 0, "thread_budget": 2, "mode": "stub", "err": ""}
    def celeritas():
        return None
''')


# The same stand-in, but it records every activate() so a test can see WHEN the budget was applied.
STUB_ACCEL_RECORDING = STUB_ACCEL.replace(
    "def activate(apply_limits=True):\n",
    "ACTIVATED = []\ndef activate(apply_limits=True):\n    ACTIVATED.append(apply_limits)\n")
# A replacement that silently missed would make the test pass for the wrong reason.
assert "ACTIVATED.append" in STUB_ACCEL_RECORDING, "the recording stub must really record"


# [VRN-ID] VRN-TST005-FNC001 · IO
def load_main():
    name = "VRN_Main_v0100_under_test"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, str(MAIN_PATH))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


# [VRN-ID] VRN-TST005-FNC002 · LOGIC
def run_main(args, env_extra=None, cwd=None):
    env = dict(os.environ)
    env.pop("VIA_ACCEL_HOME", None)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env.update(env_extra or {})
    return subprocess.run([sys.executable, str(MAIN_PATH)] + list(args), capture_output=True, text=True,
                          encoding="utf-8", errors="replace", env=env, cwd=cwd, stdin=subprocess.DEVNULL, timeout=900)


# [VRN-ID] VRN-TST005-CLS001 · CLASS
class TestSsotBooks(unittest.TestCase):
    # [VRN-ID] VRN-TST005-FNC003 · LOGIC
    @classmethod
    def setUpClass(cls):
        cls.main = load_main()
        cls.rows = cls.main.def_check_ssot()

    # [VRN-ID] VRN-TST005-FNC004 · TEST
    def test_books_match_the_code(self):
        bad = [r for r in self.rows if r["status"] == "FAIL"]
        self.assertEqual(bad, [], "ssot/ books are stale: run `python VRN_Main_v0100.py build`")

    # [VRN-ID] VRN-TST005-FNC005 · TEST
    def test_every_regex_compiles_and_is_registered(self):
        book = json.loads((VRN_ROOT / "ssot" / "VRN_REGEX_SSOT_v0100.json").read_text(encoding="utf-8"))
        self.assertGreater(book["counts"]["patterns"], 100)
        self.assertEqual(book["counts"]["not_compiling"], 0)
        self.assertEqual(len({p["id"] for p in book["patterns"]}), len(book["patterns"]), "regex ids must be unique")
        self.assertIn("TW_STOCK_REGEX", book["ticker_master_registry"])

    # [VRN-ID] VRN-TST005-FNC006 · TEST
    def test_engines_read_only_vrn_knowledge(self):
        book = json.loads((VRN_ROOT / "ssot" / "VRN_SYNONYM_SSOT_v0100.json").read_text(encoding="utf-8"))
        self.assertEqual(book["knowledge_outside_vrn"], [])
        self.assertEqual(book["knowledge_paths_first_page"]["broker_dict"], "ssot/VRN_Broker_Dict_v0100.json")
        self.assertEqual(book["knowledge_paths_first_page"]["rating_dict"], "ssot/VRN_Rating_Dict_v0100.json")
        self.assertEqual(book["load_errors"], {})

    # [VRN-ID] VRN-TST005-FNC007 · TEST
    def test_ssot_copies_are_byte_identical_to_their_source_at_copy_time(self):
        index = json.loads((VRN_ROOT / "ssot" / "VRN_SSOT_INDEX_v0100.json").read_text(encoding="utf-8"))
        copies = [b for b in index["books"] if b.get("copied_from")]
        self.assertEqual(len(copies), 5, "3 knowledge books + 2026-10-11 Method / AnnualExtract from attachments/")
        for book in copies:
            self.assertEqual(book["sha256"], book["source_sha256_at_copy"], book["path"])

    # [VRN-ID] VRN-TST005-FNC008 · TEST
    def test_regex_builds_are_deterministic(self):
        a = self.main.def_build_regex_book()
        b = self.main.def_build_regex_book()
        self.assertEqual(json.dumps(a, ensure_ascii=False), json.dumps(b, ensure_ascii=False))

    # [VRN-ID] VRN-TST005-FNC009 · TEST
    def test_regex_extractor_reads_flags_from_the_right_argument(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "x.py").write_text(textwrap.dedent('''
                import re
                A = re.compile(r"ab+", re.I)
                def f(s):
                    re.search(r"c+", s, re.M)
                    re.sub(r"d", "e", s, 0, re.S)
                    re.search(r"no-flags", s)
                    return re.findall(s, s)
                PATTERN_TABLE = {"k": r"\\d{4}"}
                LABEL_PATTERNS = [(re.compile(r"z"), "label")]
            '''), encoding="utf-8")
            literal, dynamic = self.main.def_regex_sites("x.py", root=Path(tmp))
        flags = {item["pattern"]: item["flags"] for item in literal}
        self.assertEqual(flags["ab+"], "re.I")
        self.assertEqual(flags["c+"], "re.M")
        self.assertEqual(flags["d"], "re.S")
        self.assertEqual(flags["no-flags"], "")
        self.assertIn("\\d{4}", flags)
        self.assertNotIn("label", flags, "a label next to a compiled regex is not a pattern")
        self.assertEqual(len(dynamic), 1)


# [VRN-ID] VRN-TST005-CLS002 · CLASS
class TestRegistry(unittest.TestCase):
    # [VRN-ID] VRN-TST005-FNC010 · TEST
    def test_registry_matches_the_folder(self):
        rows = load_main().def_check_registry()
        bad = [r for r in rows if r["status"] == "FAIL"]
        self.assertEqual(bad, [], "VRN_REGISTRY_v0100.json is stale: run `python VRN_Main_v0100.py build`")

    # [VRN-ID] VRN-TST005-FNC011 · TEST
    def test_registry_lists_main_launcher_and_every_bridge(self):
        reg = json.loads((VRN_ROOT / "VRN_REGISTRY_v0100.json").read_text(encoding="utf-8"))
        kinds = {e["path"]: e["kind"] for e in reg["files"]}
        self.assertEqual(kinds["VRN_Main_v0100.py"], "MAIN")
        self.assertEqual(kinds["Invoke-VRN-Main-v0100.ps1"], "LAUNCHER")
        missing = [e["path"] for e in reg["files"] if e["bridge"] == "MISSING"]
        self.assertEqual(missing, [])

    # [VRN-ID] VRN-TST005-FNC012 · TEST
    def test_crlf_checkout_keeps_the_same_hash(self):
        main = load_main()
        with tempfile.TemporaryDirectory() as tmp:
            lf, crlf = Path(tmp, "a.json"), Path(tmp, "b.json")
            lf.write_bytes(b'{"a": 1}\n{"b": 2}\n')
            crlf.write_bytes(b'{"a": 1}\r\n{"b": 2}\r\n')
            self.assertEqual(main.def_sha256_file(lf), main.def_sha256_file(crlf))


# [VRN-ID] VRN-TST005-CLS003 · CLASS
class TestFilenameOracle(unittest.TestCase):
    # [VRN-ID] VRN-TST005-FNC013 · TEST
    def test_both_engines_answer_all_106_names(self):
        rows = load_main().def_gate_oracle()
        self.assertEqual([r for r in rows if r["status"] != "PASS"], [])


# [VRN-ID] VRN-TST005-CLS004 · CLASS
class TestAccelerator(unittest.TestCase):
    # [VRN-ID] VRN-TST005-FNC014 · TEST
    def test_absent_accelerator_is_a_warning_not_a_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            done = run_main(["--accel-home", str(Path(tmp) / "nowhere"), "accel"], env_extra={"USERPROFILE": tmp})
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertIn("[WARN]", done.stdout)
        self.assertIn("fallback", done.stdout)

    # [VRN-ID] VRN-TST005-FNC015 · TEST
    def test_accelerator_mounted_by_path_reaches_every_engine_bridge(self):
        probe = textwrap.dedent('''
            import importlib.util, sys
            spec = importlib.util.spec_from_file_location("vrn_main", sys.argv[1])
            main = importlib.util.module_from_spec(spec); sys.modules["vrn_main"] = main; spec.loader.exec_module(main)
            state = main.def_load_accelerator(sys.argv[2], activate=True)
            eng = main.def_load_engines()
            fp = eng["fp_mod"]; db = eng["db"]; ec = eng["ec"]
            mapped = main.def_parallel_map(lambda x: x * 2, [1, 2, 3])
            acc = sys.modules["VIA_SuperAccel_Module"]
            print(state["loaded"], state["source"], state["canonical"], state["activated"].get("thread_budget"))
            print(fp.VIA_ACCEL is acc, db.VIA_ACCEL is acc, ec.VIA_ACCEL is acc)
            print(mapped, acc.CALLS)
        ''')
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / "supportive modules"
            home.mkdir()
            (home / "VIA_SuperAccel_Module.py").write_text(STUB_ACCEL, encoding="utf-8")
            script = Path(tmp) / "probe.py"
            script.write_text(probe, encoding="utf-8")
            env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
            env.pop("VIA_ACCEL_HOME", None)
            done = subprocess.run([sys.executable, str(script), str(MAIN_PATH), str(home)], capture_output=True, text=True,
                                  encoding="utf-8", errors="replace", env=env, stdin=subprocess.DEVNULL, timeout=600)
        self.assertEqual(done.returncode, 0, done.stderr[-2000:])
        lines = done.stdout.strip().splitlines()
        self.assertEqual(lines[0], "True --accel-home SUP_MDL737_SuperAccelModule_v9999.py 2")
        self.assertEqual(lines[1], "True True True", "each engine's [VIA:ACCEL-BRIDGE] must see the mounted accelerator")
        self.assertEqual(lines[2], "[2, 4, 6] [3]", "parallel lanes go through accel_map when it is mounted")

    # [VRN-ID] VRN-TST005-FNC052 · LOGIC
    def _run_probe(self, probe, accel_body):
        """Run a probe script against a stand-in accelerator; return its stdout."""
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / "supportive modules"
            home.mkdir()
            (home / "VIA_SuperAccel_Module.py").write_text(accel_body, encoding="utf-8")
            script = Path(tmp) / "probe.py"
            script.write_text(probe, encoding="utf-8")
            env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
            env.pop("VIA_ACCEL_HOME", None)
            done = subprocess.run([sys.executable, str(script), str(MAIN_PATH), str(home)], capture_output=True,
                                  text=True, encoding="utf-8", errors="replace", env=env,
                                  stdin=subprocess.DEVNULL, timeout=600)
        self.assertEqual(done.returncode, 0, done.stderr[-2000:])
        return done.stdout

    # [VRN-ID] VRN-TST005-FNC026 · LOGIC
    def _all_accel_line(self, accel_body):
        """跑 `all` 的第一行（--skip-seal、run 換成 no-op），回 (加速器狀態字串, 之後逐檔掃描走的車道)。"""
        probe = textwrap.dedent('''
            import argparse, importlib.util, sys
            spec = importlib.util.spec_from_file_location("vrn_main", sys.argv[1])
            main = importlib.util.module_from_spec(spec); sys.modules["vrn_main"] = main; spec.loader.exec_module(main)
            main.def_cmd_run = lambda args: 0
            main.def_cmd_all(argparse.Namespace(accel_home=sys.argv[2], skip_seal=True))
            main.def_parallel_map(lambda x: x * 2, [1, 2, 3], action="probe")
            print("LANE", main.ACCEL_COVERAGE[-1]["lane"])
        ''')
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / "supportive modules"
            home.mkdir()
            (home / "VIA_SuperAccel_Module.py").write_text(accel_body, encoding="utf-8")
            script = Path(tmp) / "probe.py"
            script.write_text(probe, encoding="utf-8")
            env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
            env.pop("VIA_ACCEL_HOME", None)
            done = subprocess.run([sys.executable, str(script), str(MAIN_PATH), str(home)], capture_output=True, text=True,
                                  encoding="utf-8", errors="replace", env=env, stdin=subprocess.DEVNULL, timeout=600)
        self.assertEqual(done.returncode, 0, done.stderr[-2000:])
        lines = done.stdout.strip().splitlines()
        return lines[0].split("加速器：", 1)[1], lines[-1]

    # [VRN-ID] VRN-TST005-FNC027 · TEST
    def test_all_never_announces_an_accelerator_it_could_not_import(self):
        """檔案在不等於掛得上：只看 is_file() 的話，壞掉的加速器會被印成「掛上」—— 假綠燈。"""
        status, lane = self._all_accel_line('raise RuntimeError("壞掉的加速器")\n')
        self.assertTrue(status.startswith("沒掛上"), status)
        self.assertIn("RuntimeError", status, "the operator needs the import error, not just a verdict")
        self.assertEqual(lane, "LANE thread_pool")

    # [VRN-ID] VRN-TST005-FNC028 · TEST
    def test_all_mounts_the_accelerator_before_the_seal_steps(self):
        """build／lock 排在這一行之後，所以它們的逐檔掃描要已經吃得到 accel_map。"""
        status, lane = self._all_accel_line(STUB_ACCEL)
        self.assertTrue(status.startswith("掛上 · SUP_MDL737_SuperAccelModule_v9999.py"), status)
        self.assertEqual(lane, "LANE accel_map")

    # [VRN-ID] VRN-TST005-FNC053 · TEST
    def test_the_thread_budget_is_applied_before_the_first_seal_step(self):
        """操作員「指令第一步為提高 CPU/DRAM 效能」：build 之前就要套上，不是等到第四步的 run。

        舊行為是只掛載、不 activate，所以 build／lock／check 整段沒有預算。這裡把三個步驟
        換成 no-op，各自回報看到的 activate 次數：第一步就該看到 1。
        """
        probe = textwrap.dedent('''
            import argparse, importlib.util, sys
            spec = importlib.util.spec_from_file_location("vrn_main", sys.argv[1])
            main = importlib.util.module_from_spec(spec); sys.modules["vrn_main"] = main; spec.loader.exec_module(main)
            calls = lambda: len(sys.modules["VIA_SuperAccel_Module"].ACTIVATED)
            def seen(step):
                print(f"{step} {calls()}")
                return 0
            main.def_cmd_build = lambda: seen("build")
            main.def_cmd_lock = lambda a: seen("lock")
            main._all_check = lambda: seen("check")
            main.def_cmd_run = lambda a: seen("run")
            main.def_cmd_all(argparse.Namespace(accel_home=sys.argv[2], skip_seal=False, lock_home=""))
            print("total", calls())
        ''')
        out = self._run_probe(probe, STUB_ACCEL_RECORDING)
        self.assertIn("build 1", out, "build 之前加速器就要 activate 過，否則第一步沒有預算")
        self.assertIn("lock 1", out)
        self.assertIn("check 1", out)
        self.assertIn("run 1", out)
        self.assertIn("total 1", out, "一個行程只 activate 一次：P04 讀同一份 ACCEL_STATE，不重做一次判斷")
        self.assertIn("執行緒預算 2 已套用", out, "操作員要看到真的數字，不是一句「已套用」")

    # [VRN-ID] VRN-TST005-FNC054 · TEST
    def test_an_accelerator_without_a_budget_is_not_announced_as_applied(self):
        """回報裡沒有 thread_budget 就不能印「已套用」—— 假綠燈比沒有燈更糟。"""
        body = STUB_ACCEL.replace('"thread_budget": 2', '"thread_budget": 0')
        status, _lane = self._all_accel_line(body)
        self.assertIn("沒有回報執行緒預算", status, status)
        self.assertNotIn("已套用", status)

    # [VRN-ID] VRN-TST005-FNC055 · TEST
    def test_a_missing_accelerator_leaves_the_chain_running_and_says_so(self):
        """加速器不在時沒有東西可提高 —— 照實說，不假裝做了，也不自己補一套預算（補＝九頭龍）。"""
        status, _lane = self._all_accel_line('raise ImportError("不在")\n')
        self.assertTrue(status.startswith("沒掛上"), status)
        self.assertNotIn("執行緒預算", status, "沒掛上就不該報一個不存在的預算")

    # [VRN-ID] VRN-TST005-FNC016 · TEST
    def test_environment_variable_is_a_candidate(self):
        main = load_main()
        old = os.environ.get("VIA_ACCEL_HOME")
        os.environ["VIA_ACCEL_HOME"] = "/somewhere/supportive modules"
        try:
            sources = [s for s, _p in main.def_accel_candidates("")]
        finally:
            if old is None:
                os.environ.pop("VIA_ACCEL_HOME", None)
            else:
                os.environ["VIA_ACCEL_HOME"] = old
        self.assertEqual(sources[0], "VIA_ACCEL_HOME")
        self.assertIn("walk-up", sources)


# [VRN-ID] VRN-TST005-CLS008 · CLASS
class TestUiVerify(unittest.TestCase):
    """收尾目標是「HTML U/I 輸出驗證無誤」：寫出來不算數,要跟 JSON 對得上才算數。"""

    PAYLOAD = {"main": "VRN_Main_v0100.py", "generated": "2026-10-16T15:00:00", "samples": "",
               "verdict": "AMBER", "counts": {"PASS": 2, "WARN": 1, "FAIL": 0, "SKIP": 0},
               "accelerator": {"canonical": ""}, "autotest": {}, "out": "", "accel_coverage": [], "temp": {}}

    # [VRN-ID] VRN-TST005-FNC029 · LOGIC
    def _written(self, tmp):
        main = load_main()
        payload = dict(self.PAYLOAD, rows=[main.def_row("P01", "甲", "PASS", "x"),
                                           main.def_row("P01", "乙", "PASS", "y"),
                                           main.def_row("P02", "丙", "WARN", "z")])
        return main, *main.def_write_report(Path(tmp), payload)

    # [VRN-ID] VRN-TST005-FNC030 · LOGIC
    def _failed(self, main, j, h):
        return [r["item"] for r in main.def_gate_ui_html(j, h) if r["status"] == "FAIL"]

    # [VRN-ID] VRN-TST005-FNC031 · TEST
    def test_the_report_it_just_wrote_passes_its_own_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            main, j, h = self._written(tmp)
            self.assertEqual(self._failed(main, j, h), [])

    # [VRN-ID] VRN-TST005-FNC056 · TEST
    def test_the_acceptance_table_does_not_inflate_the_gate_row_count(self):
        """驗收表每份報告一列,但「閘列數與 JSON 相符」比的是**閘表格** —— 數到別張表就不是比同一種量。"""
        with tempfile.TemporaryDirectory() as tmp:
            main = load_main()
            accept = {"rows": [{"file": f"r{i}.pdf", "doc_class": "STOCK", "checked": True, "parts": 29,
                                "open": 0, "verdict": "過關", "why": ""} for i in range(40)],
                      "checked": 40, "passed": 40, "files": 40, "rule": main.ACCEPT_RULE, "folder": ""}
            payload = dict(self.PAYLOAD, acceptance=accept,
                           rows=[main.def_row("P01", "甲", "PASS", "x"), main.def_row("P01", "乙", "PASS", "y"),
                                 main.def_row("P02", "丙", "WARN", "z")])
            j, h = main.def_write_report(Path(tmp), payload)
            doc = h.read_text(encoding="utf-8")
            self.assertIn("驗收 · 每一份報告是否 100% 過關", doc, "驗收那一段要真的畫出來")
            self.assertGreater(doc.count("<tr>"), 40, "40 份報告要有 40 列,否則這個測試沒在測東西")
            self.assertEqual(self._failed(main, j, h), [])

    # [VRN-ID] VRN-TST005-FNC057 · TEST
    def test_a_report_with_an_open_fix_item_is_not_counted_as_passed(self):
        """「過關」不是這裡定的 —— 待修清單上優先 0／1／2 的項算待修,優先 3（SINGLE）不算。"""
        main = load_main()
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "autotest" / "round1" / "titletrim"
            folder.mkdir(parents=True)
            (folder / "VRN_TitleTrim_Results_v0100.json").write_text(json.dumps([
                {"file": "好.pdf", "status": "OK", "doc_class": "STOCK", "parts": [1, 2]},
                {"file": "壞.pdf", "status": "OK", "doc_class": "STOCK", "parts": [1, 2]},
                {"file": "只有一條讀法.pdf", "status": "OK", "doc_class": "STOCK", "parts": [1]},
                {"file": "晨會.pdf", "status": "NOT_STOCK", "doc_class": "NEWS_DIGEST", "parts": []},
            ], ensure_ascii=False), encoding="utf-8")
            (folder / "VRN_FixList_v0100.json").write_text(json.dumps({"header": {}, "rows": [
                {"file": "壞.pdf", "part": "cover.broker", "state": "MISSING", "priority": 1},
                {"file": "只有一條讀法.pdf", "part": "cover.tel", "state": "SINGLE", "priority": 3},
            ]}, ensure_ascii=False), encoding="utf-8")
            got = main.def_acceptance(Path(tmp))
        by = {r["file"]: r["verdict"] for r in got["rows"]}
        self.assertEqual(by["好.pdf"], "過關")
        self.assertEqual(by["壞.pdf"], "待修")
        self.assertEqual(by["只有一條讀法.pdf"], "過關", "SINGLE 是鎖不住,不是讀錯")
        self.assertEqual(by["晨會.pdf"], "未逐項驗", "非個股沒有逐項部位,不混進分母")
        self.assertEqual((got["passed"], got["checked"], got["files"]), (2, 3, 4))
        self.assertEqual([r["status"] for r in main.def_gate_acceptance(got)], ["WARN"])

    # [VRN-ID] VRN-TST005-FNC032 · TEST
    def test_a_count_that_disagrees_with_the_json_is_a_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            main, j, h = self._written(tmp)
            h.write_text(h.read_text(encoding="utf-8").replace("WARN 1", "WARN 7"), encoding="utf-8")
            self.assertIn("計數與 JSON 相符", self._failed(main, j, h))

    # [VRN-ID] VRN-TST005-FNC033 · TEST
    def test_a_verdict_that_disagrees_with_the_json_is_a_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            main, j, h = self._written(tmp)
            h.write_text(h.read_text(encoding="utf-8").replace("AMBER", "GREEN"), encoding="utf-8")
            self.assertIn("結論與 JSON 相符", self._failed(main, j, h))

    # [VRN-ID] VRN-TST005-FNC045 · TEST
    def test_only_the_headline_cell_counts_not_the_word_somewhere_else(self):
        """整份文件 substring 比對會放過寫錯的主標：迴圈摘要那一段也寫著同一個結論。

        Codex PR #55 P2 的實測 —— 主標改成 GREEN、JSON 說 RED,舊寫法六項全綠。
        """
        main = load_main()
        payload = dict(self.PAYLOAD, verdict="RED", rows=[main.def_row("P01", "甲", "PASS", "x")],
                       counts={"PASS": 1, "WARN": 0, "FAIL": 0, "SKIP": 0},
                       autotest={"loop": "L", "verdict": "RED", "counts": {"PASS": 1}})
        with tempfile.TemporaryDirectory() as tmp:
            j, h = main.def_write_report(Path(tmp), payload)
            doc = h.read_text(encoding="utf-8")
            self.assertEqual(self._failed(main, j, h), [])
            # 主標寫錯,但 RED 這個字仍留在迴圈摘要那一段
            h.write_text(doc.replace('class="v">RED', 'class="v">GREEN', 1), encoding="utf-8")
            self.assertIn("RED", h.read_text(encoding="utf-8"), "the word must still be elsewhere, or this proves nothing")
            self.assertIn("結論與 JSON 相符", self._failed(main, j, h))
            # 計數同理：主標那一格改掉就要紅
            h.write_text(doc.replace("WARN 0", "WARN 9", 1), encoding="utf-8")
            self.assertIn("計數與 JSON 相符", self._failed(main, j, h))

    # [VRN-ID] VRN-TST005-FNC034 · TEST
    def test_a_dropped_row_and_an_unclosed_tag_are_both_failures(self):
        with tempfile.TemporaryDirectory() as tmp:
            main, j, h = self._written(tmp)
            doc = h.read_text(encoding="utf-8")
            h.write_text(doc.replace("<tr><td>P02</td>", "<td>P02</td>", 1), encoding="utf-8")
            self.assertIn("閘列數與 JSON 相符", self._failed(main, j, h))
            h.write_text(doc.replace("</table>", ""), encoding="utf-8")
            self.assertIn("標籤開合", self._failed(main, j, h))

    # [VRN-ID] VRN-TST005-FNC035 · TEST
    def test_the_loop_detail_link_points_at_the_file_that_is_really_there(self):
        """迴圈明細在 out/autotest/ 底下,報告在 out/ —— href 寫裸檔名就點不到。"""
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            (out / "autotest").mkdir()
            detail = out / "autotest" / "VRN_AutoTest_Report.html"
            detail.write_text("<!doctype html><html><body>detail</body></html>", encoding="utf-8")
            main = load_main()
            payload = dict(self.PAYLOAD, rows=[main.def_row("P01", "甲", "PASS", "x")],
                           counts={"PASS": 1, "WARN": 0, "FAIL": 0, "SKIP": 0},
                           autotest={"loop": "L1", "verdict": "AMBER", "counts": {"PASS": 1}, "html": str(detail)})
            j, h = main.def_write_report(out, payload)
            self.assertIn("href='autotest/VRN_AutoTest_Report.html'", h.read_text(encoding="utf-8"),
                          "href must be relative to the report, not a bare filename")
            self.assertEqual(self._failed(main, j, h), [])

    # [VRN-ID] VRN-TST005-FNC136 · LOGIC
    def def_with_record(self, tmp, rows):
        """一輪實測的樣子：G20 的代號紀錄 json 擺在 autotest/round1/titletrim/ 底下。"""
        out = Path(tmp)
        (out / "autotest" / "round1" / "titletrim").mkdir(parents=True)
        (out / "autotest" / "round1" / "titletrim" / "vrn_ticker_record.json").write_text(
            json.dumps(rows, ensure_ascii=False), encoding="utf-8")
        main = load_main()
        payload = dict(self.PAYLOAD, rows=[main.def_row("P01", "甲", "PASS", "x")],
                       counts={"PASS": 1, "WARN": 0, "FAIL": 0, "SKIP": 0})
        return main, *main.def_write_report(out, payload)

    REC = [{"file": "a.pdf", "ticker": "6873", "ticker_state": "VERIFIED",
            "upside_pct": 29.99, "upside_pct_state": "DERIVED",
            "target_price_original": 182.5, "target_price_original_state": "VERIFIED"},
           {"file": "b.pdf", "ticker": "3706", "ticker_state": "VERIFIED",
            "upside_pct": 29.96, "upside_pct_state": "DERIVED",
            "target_price_original": 190.0, "target_price_original_state": "VERIFIED"}]

    # [VRN-ID] VRN-TST005-FNC137 · TEST
    def test_the_record_reaches_the_html_the_operator_opens(self):
        """代號紀錄以前只有 CSV 與 `matrix --view record` 看得到 —— 收尾的 HTML 一個字都沒有，
        所以 G20 修好的欄位操作員看不見。"""
        with tempfile.TemporaryDirectory() as tmp:
            main, j, h = self.def_with_record(tmp, self.REC)
            doc = h.read_text(encoding="utf-8")
            self.assertIn("代號紀錄 · 四碼代號 → 15 欄", doc)
            self.assertIn("上漲%", doc, "15 欄要整排畫出來，不是只畫幾欄")
            self.assertIn("29.99 推", doc, "推（DERIVED）的記號要跟值一起出現在畫面上")
            self.assertIn("個股報告 <b>2</b>", doc)
            self.assertEqual(self._failed(main, j, h), [])

    # [VRN-ID] VRN-TST005-FNC138 · TEST
    def test_the_html_record_must_agree_with_g20(self):
        """畫了一張表、數字卻是另一回事，和「結論對不上」同一種危險 —— 要紅。"""
        with tempfile.TemporaryDirectory() as tmp:
            main, j, h = self.def_with_record(tmp, self.REC)
            doc = h.read_text(encoding="utf-8")
            cut = doc.split('<tbody class="rec">', 1)
            body, rest = cut[1].split("</tbody>", 1)
            first = body.split("</tr>", 1)[0] + "</tr>"
            h.write_text(cut[0] + '<tbody class="rec">' + first + "</tbody>" + rest, encoding="utf-8")
            self.assertEqual(self._failed(main, j, h), ["代號紀錄與 G20 相符"], "少畫一份就要說出來")

    # [VRN-ID] VRN-TST005-FNC139 · TEST
    def test_no_record_no_section_and_still_green(self):
        """沒有 G20 結果的資料夾（例如只跑 selftest）就不畫這一段，也不可以因此變紅。"""
        with tempfile.TemporaryDirectory() as tmp:
            main, j, h = self._written(tmp)
            self.assertNotIn("代號紀錄 · 四碼代號", h.read_text(encoding="utf-8"))
            self.assertEqual(self._failed(main, j, h), [])

    # [VRN-ID] VRN-TST005-FNC036 · TEST
    def test_a_link_that_points_nowhere_is_a_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            main, j, h = self._written(tmp)
            doc = h.read_text(encoding="utf-8")
            h.write_text(doc.replace("</table>", "</table><p><a href='nowhere.html'>x</a></p>"), encoding="utf-8")
            self.assertEqual(self._failed(main, j, h), ["連結連得到（1 個）"])

    # [VRN-ID] VRN-TST005-FNC037 · TEST
    def test_a_missing_report_is_a_failure_not_a_skip(self):
        with tempfile.TemporaryDirectory() as tmp:
            main, j, h = self._written(tmp)
            h.unlink()
            self.assertEqual(self._failed(main, j, h), ["HTML 報告"])


# [VRN-ID] VRN-TST005-CLS010 · CLASS
class TestAutoOpen(unittest.TestCase):
    """「輸出後驗證無誤 自動跳出 U/I」—— 驗證無誤是條件,不是形容詞。"""

    # [VRN-ID] VRN-TST005-FNC040 · TEST
    def test_a_report_whose_numbers_disagree_with_the_json_is_not_opened(self):
        main = load_main()
        self.assertEqual(main.def_open_report("x.html", "AMBER", False, ui_ok=False), "ui-fail")

    # [VRN-ID] VRN-TST005-FNC041 · TEST
    def test_a_red_verdict_is_not_opened_even_when_the_html_checks_out(self):
        main = load_main()
        self.assertEqual(main.def_open_report("x.html", "RED", False, ui_ok=True), "RED")

    # [VRN-ID] VRN-TST005-FNC042 · TEST
    def test_a_clean_amber_report_is_not_blocked_by_either_gate(self):
        main = load_main()
        # 這台機器沒有桌面環境,所以會停在 headless —— 重點是它走過了前兩道,不是被擋下。
        self.assertNotIn(main.def_open_report("x.html", "AMBER", False, ui_ok=True), ("ui-fail", "RED"))


# [VRN-ID] VRN-TST005-CLS011 · CLASS
class TestWrapupRule(unittest.TestCase):
    """操作員 2026-10-17：輸出驗證無誤才算收尾完成 —— 這是規則,不是習慣。"""

    OK = [{"item": "結論與 JSON 相符", "status": "PASS"}]
    BAD = [{"item": "結論與 JSON 相符", "status": "FAIL"}]

    # [VRN-ID] VRN-TST005-FNC047 · TEST
    def test_all_green_is_the_only_way_to_be_done(self):
        main = load_main()
        self.assertTrue(main.def_wrapup({"FAIL": 0}, self.OK)["done"])

    # [VRN-ID] VRN-TST005-FNC048 · TEST
    def test_a_failing_gate_blocks_the_wrapup(self):
        w = load_main().def_wrapup({"FAIL": 3}, self.OK)
        self.assertFalse(w["done"])
        self.assertIn("閘 FAIL 3", w["blockers"])

    # [VRN-ID] VRN-TST005-FNC049 · TEST
    def test_a_report_that_disagrees_with_its_json_blocks_the_wrapup(self):
        """跑完了、檔案也產出來了,但 HTML 跟 JSON 對不上 —— 那不是收尾完成。"""
        w = load_main().def_wrapup({"FAIL": 0}, self.BAD)
        self.assertFalse(w["done"])
        self.assertTrue(any("UI 驗證對不上" in b for b in w["blockers"]), w["blockers"])

    # [VRN-ID] VRN-TST005-FNC050 · TEST
    def test_a_broken_chain_upstream_blocks_the_wrapup(self):
        w = load_main().def_wrapup({"FAIL": 0}, self.OK, chain_rc=2)
        self.assertFalse(w["done"])

    # [VRN-ID] VRN-TST005-FNC051 · TEST
    def test_the_capsule_says_so_on_its_first_line(self):
        """交接摘要的抬頭就要講 —— 看起來乾淨、底下卻沒驗過的摘要比沒有摘要危險。"""
        main = load_main()
        cap = {"protocol": "REFERENCE_FIRST_DELTA_ONLY", "max_chars": 12000, "max_items": 24, "source": "test"}
        with tempfile.TemporaryDirectory() as tmp:
            pb = Path(tmp) / "VRN_PasteBack_v0100.txt"
            pb.write_text("前言\n== 一、燈號 ==\n內容\n", encoding="utf-8")
            good = Path(main.def_write_capsule(pb, cap, main.def_wrapup({"FAIL": 0}, self.OK))["path"]
                        ).read_text(encoding="utf-8")
            bad = Path(main.def_write_capsule(pb, cap, main.def_wrapup({"FAIL": 2}, self.BAD))["path"]
                       ).read_text(encoding="utf-8")
        self.assertTrue(good.startswith("[收尾] 完成"), good[:80])
        self.assertTrue(bad.startswith("[收尾] **未完成**"), bad[:80])
        self.assertIn("不是可以交出去的結果", bad)
        self.assertIn("閘 FAIL 2", bad)


# [VRN-ID] VRN-TST005-CLS012 · CLASS
class TestSyncGate(unittest.TestCase):
    """操作員 2026-10-19「成功確認收尾登陸上傳」—— 只有收尾完成的那一輪才上得去。

    判準不在這裡重算：`def_sync_blockers` 只讀報告 JSON 裡 `def_wrapup` 寫下的那一份。
    會這樣寫是因為另一條路已經出過事 —— 同一個判斷長兩顆頭，改了一邊另一邊就靜靜用舊規則。
    """

    # [VRN-ID] VRN-TST005-FNC058 · REPORT
    @staticmethod
    def def_report(tmp, wrapup, counts=None):
        run = Path(tmp) / "run1"
        run.mkdir(parents=True, exist_ok=True)
        payload = {"verdict": "AMBER", "counts": counts or {"FAIL": 0, "WARN": 2, "PASS": 9}}
        if wrapup is not None:
            payload["wrapup"] = wrapup
        (run / "VRN_Main_Report_v0100.json").write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        return run

    # [VRN-ID] VRN-TST005-FNC059 · TEST
    def test_a_finished_run_is_the_only_thing_that_may_be_uploaded(self):
        main = load_main()
        with tempfile.TemporaryDirectory() as tmp:
            run = self.def_report(tmp, {"done": True, "blockers": [], "rule": main.WRAPUP_RULE})
            blockers, payload = main.def_sync_blockers(run)
        self.assertEqual(blockers, [])
        self.assertEqual(payload["verdict"], "AMBER")

    # [VRN-ID] VRN-TST005-FNC060 · TEST
    def test_an_unfinished_run_is_refused_with_its_own_reason(self):
        """擋下來還要講清楚卡在哪 —— 只說「不上傳」等於叫人自己去猜。"""
        main = load_main()
        with tempfile.TemporaryDirectory() as tmp:
            run = self.def_report(tmp, {"done": False, "blockers": ["閘 FAIL 3"], "rule": main.WRAPUP_RULE})
            blockers, _ = main.def_sync_blockers(run)
        self.assertTrue(blockers)
        self.assertIn("閘 FAIL 3", blockers[0])

    # [VRN-ID] VRN-TST005-FNC061 · TEST
    def test_a_report_without_a_verdict_is_refused_not_assumed_good(self):
        """舊版 MAIN 跑出來的報告沒有 `wrapup` 這個鍵。沒有判決就是沒有判決,不可以當成過了。"""
        main = load_main()
        with tempfile.TemporaryDirectory() as tmp:
            run = self.def_report(tmp, None)
            blockers, _ = main.def_sync_blockers(run)
        self.assertTrue(blockers)
        self.assertIn("沒有收尾判決", blockers[0])

    # [VRN-ID] VRN-TST005-FNC062 · TEST
    def test_no_run_at_all_is_refused(self):
        main = load_main()
        with tempfile.TemporaryDirectory() as tmp:
            self.assertTrue(main.def_sync_blockers(Path(tmp) / "nope")[0])
        self.assertTrue(main.def_sync_blockers(None)[0])

    # [VRN-ID] VRN-TST005-FNC070 · LOGIC
    @staticmethod
    def def_fn_body(name):
        """原始碼裡某個函式的本體。守門抽成具名函式之後,要分別盯「呼叫端」與「守門本身」。"""
        main = load_main()
        _, _, tail = Path(main.__file__).read_text(encoding="utf-8").partition(f"def {name}")
        return tail.split("\ndef ")[0]

    # [VRN-ID] VRN-TST005-FNC065 · LOGIC
    @staticmethod
    def def_sync_body():
        return TestSyncGate.def_fn_body("def_cmd_sync")

    # [VRN-ID] VRN-TST005-FNC066 · TEST
    def test_the_gate_runs_even_when_the_worktree_is_clean(self):
        """Codex PR #70 P1：守門不能寫在「有東西要提交」的分支裡。

        工作樹乾淨但有還沒推的 commit —— 那條路一個閘都沒過,照樣拿舊報告的綠燈推出去。
        所以閘要在函式這一層跑,不是巢在 `if changed` 底下。
        """
        body = self.def_sync_body()
        for line in body.splitlines():
            if "def_sync_tree_ok(" in line and "if not" in line:
                indent = len(line) - len(line.lstrip())
                self.assertEqual(indent, 4, f"一致性閘巢在條件裡（縮排 {indent}）,乾淨的樹就跳過了")
                return
        self.fail("找不到函式層的一致性閘")

    # [VRN-ID] VRN-TST005-FNC067 · TEST
    def test_the_report_is_bound_to_the_tree_by_a_registry_fingerprint(self):
        """Codex PR #70 P1：一致只說明「冊與檔現在對得上」,不說明**這份報告驗的就是這些檔**。"""
        main = load_main()
        source = Path(main.__file__).read_text(encoding="utf-8")
        self.assertIn('wrap["registry_sha256"]', source, "收尾判決沒帶註冊冊指紋")
        self.assertIn("registry_sha256", self.def_fn_body("def_sync_tree_ok"), "守門沒比對那個指紋")

    # [VRN-ID] VRN-TST005-FNC068 · TEST
    def test_fetch_and_fast_forward_happen_before_the_local_commit(self):
        """Codex PR #70 P2：先 commit 再 fetch,遠端有進度時必然判成分叉。

        那會留下一顆孤兒 commit,而它本來只要快轉就好。
        """
        body = self.def_sync_body()
        fetch = body.find('"fetch", "origin"')
        ff = body.find('"merge", "--ff-only"')
        commit = body.find('"commit", "-m"')
        for name, pos in (("fetch", fetch), ("ff", ff), ("commit", commit)):
            self.assertGreater(pos, 0, f"sync 裡找不到 {name}")
        self.assertLess(fetch, commit, "fetch 要在本機 commit 之前")
        self.assertLess(ff, commit, "快轉要在本機 commit 之前")

    # [VRN-ID] VRN-TST005-FNC071 · TEST
    def test_the_tree_is_checked_again_after_the_fast_forward(self):
        """Codex PR #71 P1：快轉換掉 HEAD 與工作樹,開頭問過的那棵樹已經不是這一棵。

        遠端帶進來的檔 + 本機還沒提交的改動,這個組合沒有任何一輪實測驗過,
        註冊冊指紋也可能因此對不上。所以提交與推之前要照同一套再問一次。

        這是同一類錯誤的第三次:閘跑的那一刻,和真正送出去的那一刻,不是同一刻。
        """
        body = self.def_sync_body()
        calls = [i for i in range(len(body)) if body.startswith("def_sync_tree_ok(", i)]
        self.assertGreaterEqual(len(calls), 2, "快轉之後沒有再驗一次,只在開頭驗")
        ff = body.find('"merge", "--ff-only"')
        commit = body.find('"commit", "-m"')
        self.assertGreater(ff, 0, "找不到快轉")
        after_ff = [i for i in calls if i > ff]
        self.assertTrue(after_ff, "快轉之後一次都沒再驗")
        self.assertLess(min(after_ff), commit, "快轉後那次要在 commit 之前,放在後面等於沒擋")


    # [VRN-ID] VRN-TST005-FNC069 · TEST
    def test_a_branch_missing_on_origin_is_a_first_push_not_a_fatal(self):
        """Codex PR #70 P2：origin 上還沒有這個分支時 `git fetch origin <branch>` 會 fatal。

        那不是錯誤,是「第一次推」。先問 ls-remote 才分得出「遠端沒有這個分支」
        和「連不上遠端」—— 直接把 fetch 的非零當成致命,新分支就永遠推不出去。
        """
        body = self.def_sync_body()
        ls = body.find('"ls-remote"')
        fetch = body.find('"fetch", "origin"')
        self.assertGreater(ls, 0, "sync 沒先問 ls-remote")
        self.assertLess(ls, fetch, "ls-remote 要在 fetch 之前,才分得出「沒有這個分支」")
        self.assertIn("第一次推", body, "沒有「遠端還沒有這個分支」那條路的說明")


    # [VRN-ID] VRN-TST005-FNC064 · TEST
    def test_sync_re_checks_the_tree_right_before_it_commits(self):
        """那一輪的綠燈是**跑 check 那一刻**的綠燈,提交發生在之後。

        2026-10-19 實跑踩到:鏈跑到一半改了文件,build 已經過去了,註冊冊記的是舊 SHA,
        sync 照樣提交照樣推 —— 推上去那顆 commit 自己 check 是 RED(`87ce66e`)。
        **驗過的東西,不一定就是提交出去的東西。** 所以 add 之前要再驗一次,
        而且用的是 check 指令那四組,不是另寫一套判準。
        """
        main = load_main()
        source = Path(main.__file__).read_text(encoding="utf-8")
        _, _, tail = source.partition("def def_cmd_sync")
        self.assertTrue(tail, "找不到 def_cmd_sync")
        body = tail.split("\ndef ")[0]
        guard = body.find("def_sync_tree_ok(")
        add = body.find('"add", "-A"')
        self.assertGreater(guard, 0, "sync 提交前沒有再驗一次冊與註冊冊")
        self.assertGreater(add, 0, "sync 裡找不到 git add")
        self.assertLess(guard, add, "一致性檢查要在 git add **之前**,放在後面等於沒擋")
        gate = self.def_fn_body("def_sync_tree_ok")
        for name in ("def_check_ssot()", "def_check_registry()", "def_gate_astid()", "def_gate_engine_lock()"):
            self.assertIn(name, gate, f"{name} 沒被用到 —— 守門要跟 check 指令同一套")

    # [VRN-ID] VRN-TST005-FNC063 · TEST
    def test_the_run_report_carries_the_verdict_so_nobody_has_to_re_derive_it(self):
        """報告 JSON 要帶著 `wrapup`。少了它,下游就只能自己再判一次 —— 那正是要避免的。"""
        main = load_main()
        source = Path(main.__file__).read_text(encoding="utf-8")
        self.assertIn('payload["wrapup"] = wrap', source,
                      "def_wrapup 的結果沒有寫回報告 JSON,sync 讀不到唯一那份判準")


# [VRN-ID] VRN-TST005-CLS009 · CLASS
class TestCapsuleBudget(unittest.TestCase):
    """省 token 的預算是 VCGC 的正本,VRN 只讀不訂 —— 讀不到就要說自己用了內建值。"""

    # [VRN-ID] VRN-TST005-FNC038 · TEST
    def test_budget_comes_from_the_root_ssot_and_says_so(self):
        cap = load_main().def_capsule_budget()
        self.assertEqual(cap["protocol"], "REFERENCE_FIRST_DELTA_ONLY")
        self.assertEqual(cap["source"], "root-ssot", cap)
        import json as _json
        from pathlib import Path as _Path
        root = _json.loads((_Path(load_main().VRN_ROOT).parents[1] / "config" / "ssot" / "VIA_SystemMaster.via")
                           .read_text(encoding="utf-8-sig"))
        want = root["token_governance"]["capsule_policy"]
        self.assertEqual((cap["max_chars"], cap["max_items"]), (want["max_chars"], want["max_items"]),
                         "budget must be the SSOT's number, never a second copy")

    # [VRN-ID] VRN-TST005-FNC043 · TEST
    def test_a_capsule_fits_the_budget_and_names_what_it_left_out(self):
        main = load_main()
        cap = {"protocol": "REFERENCE_FIRST_DELTA_ONLY", "max_chars": 600, "max_items": 24, "source": "test"}
        with tempfile.TemporaryDirectory() as tmp:
            pb = Path(tmp) / "VRN_PasteBack_v0100.txt"
            pb.write_text("前言一行\n" + "".join(f"== {n}、段 ==\n" + "x" * 300 + "\n" for n in "一二三四五"),
                          encoding="utf-8")
            got = main.def_write_capsule(pb, cap)
            body = Path(got["path"]).read_text(encoding="utf-8")
        self.assertLessEqual(got["chars"], cap["max_chars"], body[:400])
        self.assertTrue(got["left"], "a 1500-char source under a 600-char budget must drop something")
        for name in got["left"]:
            self.assertIn(name, body, "an omitted section must be named, not silently truncated")
        self.assertIn(str(pb), body, "reference first: the full file's path must be in the capsule")
        self.assertIn(cap["protocol"], body)

    # [VRN-ID] VRN-TST005-FNC046 · TEST
    def test_no_section_length_can_push_the_capsule_over_the_budget(self):
        """單一長度測不出這件事 —— 原本那一案剛好沒踩中,Codex PR #55 掃出 600 上限寫 643 字。

        省略那一行的長度取決於省掉哪幾段,所以會不會超出跟各段長度有關;逐一掃過才算證明。
        """
        main = load_main()
        cap = {"protocol": "REFERENCE_FIRST_DELTA_ONLY", "max_chars": 600, "max_items": 24, "source": "test"}
        worst = 0
        with tempfile.TemporaryDirectory() as tmp:
            pb = Path(tmp) / "VRN_PasteBack_v0100.txt"
            for n in range(1, 900, 7):
                pb.write_text("前\n== 一、段 ==\n" + "x" * n
                              + "\n== 二、名字夠長才看得出問題的那一段 ==\nyyy\n", encoding="utf-8")
                got = main.def_write_capsule(pb, cap)
                real = len(Path(got["path"]).read_text(encoding="utf-8"))
                self.assertEqual(got["chars"], real, "reported size must be the file's real size")
                worst = max(worst, real)
        self.assertLessEqual(worst, cap["max_chars"], f"largest capsule written was {worst}")

    # [VRN-ID] VRN-TST005-FNC044 · TEST
    def test_a_capsule_that_already_fits_drops_nothing(self):
        main = load_main()
        cap = {"protocol": "REFERENCE_FIRST_DELTA_ONLY", "max_chars": 12000, "max_items": 24, "source": "test"}
        with tempfile.TemporaryDirectory() as tmp:
            pb = Path(tmp) / "VRN_PasteBack_v0100.txt"
            pb.write_text("前言\n== 一、段 ==\n短\n", encoding="utf-8")
            got = main.def_write_capsule(pb, cap)
        self.assertEqual(got["left"], [])

    # [VRN-ID] VRN-TST005-FNC039 · TEST
    def test_an_unreadable_policy_falls_back_and_is_labelled_engine_default(self):
        main = load_main()
        keep = main.CAPSULE_POLICY_PATH
        try:
            main.CAPSULE_POLICY_PATH = Path(tempfile.gettempdir()) / "no_such_VIA_SystemMaster.via"
            cap = main.def_capsule_budget()
        finally:
            main.CAPSULE_POLICY_PATH = keep
        self.assertEqual(cap["source"], "engine-default")
        self.assertTrue(cap["why"], "a fallback that does not say why is a silent default")


# [VRN-ID] VRN-TST005-CLS005 · CLASS
class TestStandalone(unittest.TestCase):
    # [VRN-ID] VRN-TST005-FNC017 · TEST
    def test_vrn_folder_copied_alone_still_answers_from_its_own_books(self):
        rc, rows = load_main().def_cmd_standalone()
        self.assertEqual(rc, 0, rows)
        inside = [r for r in rows if "知識書都在 VRN 資料夾內" in r["item"]]
        self.assertEqual(len(inside), 1)
        self.assertEqual(inside[0]["status"], "PASS", inside[0]["detail"])


# [VRN-ID] VRN-TST005-CLS006 · CLASS
class TestCli(unittest.TestCase):
    # [VRN-ID] VRN-TST005-FNC018 · TEST
    def test_check_command_passes_on_the_committed_tree(self):
        done = run_main(["check"])
        self.assertEqual(done.returncode, 0, done.stdout[-1500:] + done.stderr[-1500:])
        self.assertIn("[CHECK]", done.stdout)

    # [VRN-ID] VRN-TST005-FNC019 · TEST
    def test_main_keeps_the_standalone_gate_seat(self):
        text = MAIN_PATH.read_text(encoding="utf-8")
        for needle in ("VIA_FROM_VCGC", "def main", "def selftest", 'os.environ["VIA_FROM_VCGC"] = "YES"'):
            self.assertIn(needle, text)
        self.assertNotIn("VIA_NET_CONSENT\"] =", text)
        self.assertNotIn("VIA_SCRAPE_CONSENT\"] =", text)


# [VRN-ID] VRN-TST005-CLS025 · CLASS
class def_LauncherBranchDefaultTests(unittest.TestCase):
    """啟動器不准把分支名寫死 —— 寫死的那一刻就開始過期。

    實測 2026-10-20：`Invoke-VRN-Main-v0100.ps1` 的 `-Branch` 預設值是
    `claude/amazing-hawking-tjzssr`，而那條分支早就不是在跑的那一條。
    `-Command update` 不帶參數跑下去，會**安靜地把操作員切到舊碼** ——
    而且跑起來一切正常，只是跑的是上個月的 VRN。
    """

    LAUNCHERS = ("Invoke-VRN-Main-v0100.ps1", "Invoke-VRN-AutoTest.ps1")

    # [VRN-ID] VRN-TST005-FNC154 · TEST
    def test_no_launcher_hard_codes_a_working_branch(self):
        """任何一支啟動器的參數預設值都不准長得像一條工作分支。"""
        bad = []
        for name in self.LAUNCHERS:
            path = VRN_ROOT / name
            if not path.is_file():
                continue
            for line in path.read_text(encoding="utf-8").splitlines():
                stripped = line.strip()
                if not stripped.startswith("[string]$") or "=" not in stripped:
                    continue                                 # 只看 param() 的預設值，不看註解與說明
                value = stripped.split("=", 1)[1].strip().strip(",").strip("'\"")
                if re.fullmatch(r"(claude|codex|grok|via)/[\w.-]+", value):
                    bad.append(f"{name}: {stripped}")
        self.assertEqual(bad, [], f"啟動器把分支名寫死了（會過期，然後安靜地把人切到舊碼）：{bad}")

    # [VRN-ID] VRN-TST005-FNC155 · TEST
    def test_update_falls_back_to_the_branch_you_are_on(self):
        """沒給 -Branch 時要跟著現在 checkout 的那一條走，detached 才退回 main。"""
        src = (VRN_ROOT / "Invoke-VRN-Main-v0100.ps1").read_text(encoding="utf-8")
        self.assertIn("[string]$Branch = ''", src, "-Branch 的預設值要留空，由 update 那段決定")
        self.assertIn("if (-not $Branch) {", src, "update 那段要有「沒給就用現在這一條」的處理")
        body = "\n".join(src.split("if (-not $Branch) {", 1)[1].splitlines()[:6])
        self.assertIn("$VrnVersion.Branch", body, "要用現在 checkout 的那一條")
        self.assertIn("'main'", body, "detached 時要有退路")

    # [VRN-ID] VRN-TST005-FNC156 · TEST
    def test_the_parameter_is_documented(self):
        """改了語意就要寫下來 —— 不然下一個人只會看到一個空字串。"""
        src = (VRN_ROOT / "Invoke-VRN-Main-v0100.ps1").read_text(encoding="utf-8")
        self.assertIn(".PARAMETER Branch", src, "-Branch 要有說明段")


# [VRN-ID] VRN-TST005-CLS026 · CLASS
class def_AccelCoverageVerdictTests(unittest.TestCase):
    """P09 的燈號要看「這個動作做完了沒」，不是看「跑在哪條車道」。

    實測 2026-10-21（107 檔）：外層 20 個 WARN 裡有 **16 個**是 P09 ACCEL，其中包含
    `cache · 107 項 · 0.0 秒 · 檔案與讀法都沒變：沿用上次的還原結果`（最好的結果）、
    `worker_process · 106 項 · 掛掉 0 塊、本行程補做 0 份`（成功）、
    以及 `逐一（加速器未掛上）· 判讀邏輯不可動`（照設計就是不拆）。

    根因 `ok = e["lane"] in ("accel_map", "process_mount")` —— 只看車道名，
    完全不看它自己量到的 items / seconds / failed_chunks。而那兩條 PASS 車道都要
    `VIA_SuperAccel_Module.py`（在母倉、不在本倉），所以這台機器上 **P09 的每一列在開跑前就註定是 WARN**。
    更要緊的是「加速器在不在」P04 ACCEL 已經判過一次 —— 同一個判斷做兩遍，就是這個倉最忌諱的九頭龍。
    """

    # [VRN-ID] VRN-TST005-FNC157 · LOGIC
    @classmethod
    def setUpClass(cls):
        cls.M = load_main()

    # [VRN-ID] VRN-TST005-FNC158 · LOGIC
    def def_rows(self, cov):
        M = self.M
        keep = list(M.ACCEL_COVERAGE)
        M.ACCEL_COVERAGE.clear()
        try:
            return {r["item"]: r for r in M.def_gate_accel_coverage(cov)}
        finally:
            M.ACCEL_COVERAGE.clear()
            M.ACCEL_COVERAGE.extend(keep)

    # [VRN-ID] VRN-TST005-FNC159 · TEST
    def test_a_cache_hit_is_not_a_warning(self):
        """沿用上次的結果是最好的結果，不是警告。"""
        got = self.def_rows([{"action": "G15 版面還原：TEMP 快取", "lane": "cache", "items": 107, "seconds": 0.0,
                              "why": "檔案與讀法都沒變：沿用上次的還原結果"}])
        self.assertEqual(got["G15 版面還原：TEMP 快取"]["status"], "PASS")

    # [VRN-ID] VRN-TST005-FNC160 · TEST
    def test_worker_process_passes_when_nothing_died_and_warns_when_something_did(self):
        """子行程分塊：掛掉 0 塊是成功；真的掛了才是警告 —— 而且要看結構化的數字，不是解析那句中文。"""
        ok = self.def_rows([{"action": "G19 聚焦", "lane": "worker_process", "items": 106, "seconds": 42.4, "failed": 0}])
        self.assertEqual(ok["G19 聚焦"]["status"], "PASS", "掛掉 0 塊不是警告")
        bad = self.def_rows([{"action": "G19 聚焦", "lane": "worker_process", "items": 106, "seconds": 42.4, "failed": 2}])
        self.assertEqual(bad["G19 聚焦"]["status"], "WARN", "真的掛了塊才是警告")
        self.assertIn("2", str(bad["G19 聚焦"]["detail"]), "掛了幾塊要印出來")

    # [VRN-ID] VRN-TST005-FNC161 · TEST
    def test_a_step_that_is_serial_by_design_is_not_a_warning(self):
        """照設計就不拆執行緒（判讀邏輯不可動）—— 那是規矩，不是沒做到。"""
        got = self.def_rows([{"action": "G06 資料庫引擎整批判讀", "lane": "sequential", "items": 107, "seconds": 6.2,
                              "why": "引擎自己的逐檔順序與 upsert，不拆執行緒（判讀邏輯不可動）", "by_design": True}])
        self.assertEqual(got["G06 資料庫引擎整批判讀"]["status"], "PASS")

    # [VRN-ID] VRN-TST005-FNC162 · TEST
    def test_serial_without_a_reason_is_still_a_warning(self):
        """護欄：真的一條接一條跑、又說不出理由，仍然要紅字 —— 不是把門檻放寬。"""
        got = self.def_rows([{"action": "某個步驟", "lane": "sequential", "items": 107, "seconds": 90.0}])
        self.assertEqual(got["某個步驟"]["status"], "WARN")

    # [VRN-ID] VRN-TST005-FNC163 · TEST
    def test_p09_does_not_judge_the_accelerator_a_second_time(self):
        """九頭龍：加速器在不在是 P04 ACCEL 的事。P09 只說每個動作跑在哪條車道、做完了沒。

        整輪都沒有加速器（退回執行緒池 / 快取 / 子行程），但每個動作都做完了 —— P09 一列都不該紅。
        """
        cov = [{"action": "a", "lane": "thread_pool", "items": 25, "seconds": 1.6, "why": "加速器未掛上：stdlib 執行緒池"},
               {"action": "b", "lane": "cache", "items": 107, "seconds": 0.0},
               {"action": "c", "lane": "worker_process", "items": 106, "seconds": 42.4, "failed": 0}]
        got = self.def_rows(cov)
        self.assertEqual([r["status"] for r in got.values()], ["PASS"] * len(got),
                         "加速器不在不是 P09 的判斷 —— P04 ACCEL 已經判過一次了")
        summary = next(r for k, r in got.items() if "加速器覆蓋" in k)
        self.assertIn("退回", str(summary["detail"]), "車道分佈照實印出來，資訊不可以不見")


if __name__ == "__main__":
    unittest.main()


# [VRN-ID] VRN-TST005-CLS007 · CLASS
class TestPasteBack(unittest.TestCase):
    """Round 3 (2026-10-12): the paste-back file keeps text, tables and categories apart, and carries the first-page lines."""

    # [VRN-ID] VRN-TST005-FNC020 · TEST
    def test_pasteback_has_five_parts_and_evidence(self) -> None:
        spec = importlib.util.spec_from_file_location("vrn_main_pasteback_test", str(MAIN_PATH))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp) / "20261012T000000"
            (run / "autotest" / "round1" / "titletrim").mkdir(parents=True)
            w = lambda rel, obj: (run / rel).write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")  # noqa: E731
            w("VRN_Main_Report_v0100.json", {"generated": "t", "samples": "C:\\x", "verdict": "AMBER", "counts": {"FAIL": 0, "WARN": 1, "SKIP": 0, "PASS": 1},
                                             "rows": [{"gate": "G00", "item": "a", "status": "WARN", "detail": "d"}, {"gate": "G01", "item": "b", "status": "PASS"}]})
            w("autotest/VRN_AutoTest_Report.json", {"rounds": [{"round": 1, "verdict": "AMBER", "counts": {"WARN": 1},
                                                                "rows": [{"gate": "G17 TITLETRIM", "name": "n", "status": "WARN", "detail": "x"}]}],
                                                    "focus": {"counts": {"files": 3, "stock": 2, "pages_total": 5, "pages_kept": 2, "annual_pages": 1}},
                                                    "lock": {"counts": {"NEW": 1, "HELD": 2, "BROKEN": 0, "OPEN": 3}}})
            w("autotest/round1/titletrim/VRN_FixList_v0100.json", {"header": {"generated": "t", "files": 2, "stock": 2, "states": {"CONFLICT": 1}},
               "rows": [{"file": "a.pdf", "part": "cover.target_price", "state": "CONFLICT", "lock": "OPEN", "priority": 1, "value": 78.0, "why": "w",
                         "sources": json.dumps({"首頁（TRIM）": 78.0, "首頁引擎": 128.0, "首頁那一行": "L2 目標價 78", "區塊": "RatingBox"}, ensure_ascii=False)},
                        {"file": "a.pdf", "part": "annual.unmapped:怪列標@2025", "state": "UNMAPPED", "lock": "", "priority": 2, "value": "", "why": "", "sources": "{}"},
                        {"file": "b.pdf", "part": "cover.tel", "state": "SINGLE", "lock": "", "priority": 3, "value": "1", "why": "", "sources": "{}"}]})
            w("autotest/round1/titletrim/VRN_TitleTrim_Results_v0100.json",
              [{"file": "a.pdf", "cover": {"zones": [{"line": 1, "zone": "TopHeader", "clean": "頁首", "x0": 40.0},
                                                     {"line": 2, "zone": "RatingBox", "clean": "目標價 78", "x0": 420.0, "prior": True}]}}])
            (run / "autotest" / "VRN_Focus_Manifest_v0100.csv").write_text("檔案,類別,處理\na.pdf,STOCK,是\nz.pdf,INDUSTRY,否\n", encoding="utf-8-sig")
            got = mod.def_write_pasteback(run)
            text = Path(got["path"]).read_text(encoding="utf-8")
            for mark in ("== 一、燈號", "== 二、數字", "== 三、待修清單", "== 四、首頁原文", "== 五、聚焦清冊", "| 燈 | 閘 | 項目 | 說明 |",
                         "cover.target_price×1", "| a.pdf | CONFLICT/OPEN | 78.0 |", "L2 [RatingBox] x420 ★前次 目標價 78", "| 怪列標 | 1 |", "| cover.tel | 1 |"):
                self.assertIn(mark, text, mark)
            self.assertNotIn("z.pdf", text, "non-stock rows are not pasted")
            self.assertEqual(got["evidence_files"], 1)
            self.assertEqual(mod.def_latest_run(Path(tmp)), run)

    # 2026-10-13: six independent pre-steps side by side; rows in the listed order, a silenced step does not silence the console
    # [VRN-ID] VRN-TST005-FNC022 · TEST
    def test_pre_steps_run_side_by_side_and_keep_their_order(self) -> None:
        spec = importlib.util.spec_from_file_location("vrn_main_side_by_side_test", str(MAIN_PATH))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
        import threading
        import time as _time
        seen = []
        barrier = threading.Barrier(3, timeout=10)

        # [VRN-ID] VRN-TST005-FNC023 · LOGIC
        def step(i: int):
            # [VRN-ID] VRN-TST005-FNC024 · LOGIC
            def run():
                barrier.wait()                            # all three are running at the same time, or this times out
                with mod.def_quiet():
                    print("noise that must not reach the console")
                    _time.sleep(0.05)
                seen.append(i)
                return [mod.def_row("P0X", f"step {i}", "PASS")]
            return run

        # [VRN-ID] VRN-TST005-FNC025 · LOGIC
        def broken():
            raise ValueError("boom")
        real = sys.stdout
        rows = mod.def_run_steps_side_by_side([("a", step(1)), ("b", step(2)), ("c", step(3)), ("d", broken)])
        self.assertIs(sys.stdout, real, "the console is given back")
        self.assertEqual([r["item"] for r in rows[:3]], ["step 1", "step 2", "step 3"], "rows in the listed order")
        self.assertEqual((rows[3]["status"], rows[3]["item"]), ("FAIL", "d"))
        self.assertEqual(sorted(seen), [1, 2, 3])

    # round 5b (2026-10-12): the operator passed the pasted matrix text as -Truth; it is converted first
    # [VRN-ID] VRN-TST005-FNC021 · TEST
    def test_truth_accepts_the_pasted_matrix(self) -> None:
        spec = importlib.util.spec_from_file_location("vrn_main_truth_test", str(MAIN_PATH))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
        tm = mod.def_load_module("VRN_Main_truthmatrix", mod.ENGINE_FILES["truthmatrix"])
        with tempfile.TemporaryDirectory() as tmp:
            pasted = Path(tmp) / "v0113.txt"
            pasted.write_text(tm.sample_text(), encoding="utf-8")
            got = mod.def_load_truth_file(str(pasted))
            self.assertTrue(got.endswith("v0113.truth.json"))
            self.assertEqual(len(json.loads(Path(got).read_text(encoding="utf-8"))), 7)
            self.assertEqual(mod.def_load_truth_file(got), got, "a truth JSON is used as given")
            junk = Path(tmp) / "junk.txt"
            junk.write_text("nothing here", encoding="utf-8")
            self.assertEqual(mod.def_load_truth_file(str(junk)), str(junk), "not convertible: the loop reports it as unreadable")


# [VRN-ID] VRN-TST005-CLS013 · CLASS
class TestFixPriorityOneHead(unittest.TestCase):
    """2026-10-19 實測：「待修清單上的項擋不擋收尾」長了三顆頭,同一張報告上並排印出相反的答案。

        P21 驗收   PASS   逐項驗過的報告 3/3 份 100% 過關
        G00 LOCK   WARN   待修 3 項

    講的是同樣那三項 priority 3 SINGLE。def_acceptance 算「優先 ≤ 2」(對,而且有文件),
    G00 LOCK 和 AutoTestLoop G18 都算「有列就 WARN」—— 那兩處不是做了別的決定,是從來沒問
    這個問題。門檻收到 VRN_AutoTestLoop.def_fix_blocks 一處,三邊都走它。
    """

    # [VRN-ID] VRN-TST005-FNC072 · LOGIC
    @staticmethod
    def def_loop():
        main = load_main()
        return main.def_fix_rule()

    # [VRN-ID] VRN-TST005-FNC073 · LOGIC
    @staticmethod
    def def_fixture(tmp, priorities):
        """一輪實測的 titletrim 產物:一份個股報告,待修清單上的優先序由呼叫端給。"""
        folder = Path(tmp) / "autotest" / "round1" / "titletrim"
        folder.mkdir(parents=True, exist_ok=True)
        results = [{"file": "A-2330-x.pdf", "status": "OK", "doc_class": "STOCK",
                    "parts": [{"part": "cover.current_price", "state": "SINGLE"}]}]
        rows = [{"file": "A-2330-x.pdf", "part": f"cover.p{i}", "state": "SINGLE", "priority": p}
                for i, p in enumerate(priorities)]
        (folder / "VRN_TitleTrim_Results_v0100.json").write_text(
            json.dumps(results, ensure_ascii=False), encoding="utf-8")
        (folder / "VRN_FixList_v0100.json").write_text(
            json.dumps({"rows": rows}, ensure_ascii=False), encoding="utf-8")
        return Path(tmp)

    # [VRN-ID] VRN-TST005-FNC074 · TEST
    def test_single_does_not_block_but_nought_one_two_do(self):
        """ACCEPT_RULE 寫的那句話,現在是真的只有一處在判。"""
        blocks = self.def_loop().def_fix_blocks
        self.assertFalse(blocks({"priority": 3}), "優先 3 是 SINGLE:鎖不住,不是讀錯")
        for p in (0, 1, 2):
            self.assertTrue(blocks({"priority": p}), f"優先 {p} 要擋")

    # [VRN-ID] VRN-TST005-FNC075 · TEST
    def test_an_unreadable_priority_counts_as_blocking(self):
        """讀不出優先序就當它擋著 —— 不知道不等於沒事。"""
        blocks = self.def_loop().def_fix_blocks
        self.assertTrue(blocks({}))
        self.assertTrue(blocks({"priority": "?"}))
        self.assertTrue(blocks(None))

    # [VRN-ID] VRN-TST005-FNC076 · TEST
    def test_the_two_input_shapes_cannot_disagree(self):
        """G00 LOCK 只拿到 {優先序: 項數},G18 拿到整份清單 —— 兩個形狀要同一個答案。

        JSON 來回之後鍵會變字串,所以字串鍵也要一起驗:那正是 G00 LOCK 讀到的樣子。
        """
        loop = self.def_loop()
        for mix in ([3, 3, 3], [1, 3], [0, 1, 2, 3], [2], []):
            rows = [{"priority": p} for p in mix]
            counts_int = {}
            for p in mix:
                counts_int[p] = counts_int.get(p, 0) + 1
            counts_str = {str(k): v for k, v in counts_int.items()}
            want = loop.def_fix_blocking(rows)
            if mix:
                self.assertEqual(loop.def_fix_blocking_from_counts(counts_int), want, f"int 鍵 {mix}")
                self.assertEqual(loop.def_fix_blocking_from_counts(counts_str), want, f"str 鍵 {mix}")

    # [VRN-ID] VRN-TST005-FNC077 · TEST
    def test_no_breakdown_is_unknown_not_zero(self):
        """算不出來要回 None,呼叫端才能照實說「算不出來」。回 0 會把不知道印成綠燈。"""
        f = self.def_loop().def_fix_blocking_from_counts
        self.assertIsNone(f({}))
        self.assertIsNone(f(None))
        self.assertIsNone(f({"不是數字": 1}))
        self.assertEqual(f({"3": 3}), 0)

    # [VRN-ID] VRN-TST005-FNC078 · TEST
    def test_acceptance_passes_when_only_single_is_left(self):
        """真的叫 def_acceptance,不是驗那支函式旁邊的東西。"""
        main = load_main()
        with tempfile.TemporaryDirectory() as tmp:
            accept = main.def_acceptance(self.def_fixture(tmp, [3, 3, 3]))
        self.assertEqual((accept["passed"], accept["checked"]), (1, 1))
        self.assertEqual(accept["rows"][0]["verdict"], "過關")

    # [VRN-ID] VRN-TST005-FNC079 · TEST
    def test_acceptance_holds_a_file_with_a_blocking_item(self):
        main = load_main()
        with tempfile.TemporaryDirectory() as tmp:
            accept = main.def_acceptance(self.def_fixture(tmp, [3, 2]))
        self.assertEqual((accept["passed"], accept["checked"]), (0, 1))
        self.assertEqual(accept["rows"][0]["verdict"], "待修")

    # [VRN-ID] VRN-TST005-FNC080 · TEST
    def test_the_lock_row_asks_the_rule_instead_of_counting_rows(self):
        """守門抽成函式之後還要盯呼叫端 —— 這條列的燈號不可以再看「清單有沒有列」。"""
        body = TestSyncGate.def_fn_body("def_cmd_run_body")
        head = body.split("G00 MATRIX")[0]
        self.assertIn("def_fix_blocking_from_counts", head, "G00 LOCK 要問共用的門檻")
        self.assertNotIn('("WARN" if (locked.get("fix_list") or {}).get("rows") else "PASS")', head,
                         "舊的「有列就 WARN」不可以留著")

    # [VRN-ID] VRN-TST005-FNC081 · TEST
    def test_an_empty_fix_list_is_not_reported_as_unknown(self):
        """清單空的時候 fix_priority 是 {},問門檻會拿到 None,照樣會印成 WARN —— 那是退步。

        改這條的時候我自己先做出了這個退步,所以把它釘在測試裡。
        """
        main = load_main()
        with tempfile.TemporaryDirectory() as tmp:
            accept = main.def_acceptance(self.def_fixture(tmp, []))
        self.assertEqual((accept["passed"], accept["checked"]), (1, 1))
        body = TestSyncGate.def_fn_body("def_cmd_run_body")
        self.assertIn("0 if not fix_rows_n else", body.split("G00 MATRIX")[0],
                      "清單空的就不該去問門檻")

    # [VRN-ID] VRN-TST005-FNC082 · TEST
    def test_only_one_file_decides_the_threshold(self):
        """第四顆頭長出來的那一天,這條會紅。"""
        root = VRN_ROOT
        owners = set()
        for path in root.rglob("*.py"):
            rel = path.relative_to(root).as_posix()
            if rel.startswith("tests/") or "/intake/" in rel or "/references/" in rel:
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            for line in text.splitlines():
                if "FIX_BLOCKING_MAX" in line or ("priority" in line and "<=" in line):
                    owners.add(rel)
        self.assertEqual(owners, {"engine/VRN_AutoTestLoop.py"},
                         f"門檻只能住在一支檔案裡,現在是 {sorted(owners)}")


# [VRN-ID] VRN-TST005-CLS014 · CLASS
class TestAtomicJsonWrite(unittest.TestCase):
    """2026-10-19 實測:def_write_json 本來是裸的 write_text。

    400 次並行讀裡 296 次讀到半份 JSON（原寫法）；原子換檔之後 0 次。
    收尾報告正是 def_sync_blockers 要讀回來的那一份,所以半份報告等於整條收尾鏈
    斷在一個看不見的地方 —— 而操作員確實會同時跑 VRN 與 VDF。
    """

    # [VRN-ID] VRN-TST005-FNC083 · TEST
    def test_a_reader_never_sees_half_a_report(self):
        """讀的那一側走正式的 def_read_json —— 驗了函式不等於驗了那條路。"""
        main = load_main()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "VRN_Main_Report_v0100.json"
            main.def_write_json(path, {"rows": [{"i": i, "t": "x" * 200} for i in range(400)]})
            torn, wrote_bad, stop = [], [], []

            # [VRN-ID] VRN-TST005-FNC084 · LOGIC
            def writer():
                n = 0
                while not stop:
                    try:
                        main.def_write_json(path, {"rows": [{"i": i, "t": "y" * 200} for i in range((n % 400) + 1)]})
                    except Exception as error:  # noqa: BLE001 — 寫的那一側死掉也要算數,不能只死在執行緒裡
                        wrote_bad.append(error.__class__.__name__)
                    n += 1

            thread = threading.Thread(target=writer, daemon=True)
            thread.start()
            try:
                for _ in range(400):
                    try:
                        main.def_read_json(path)
                    except Exception as error:  # noqa: BLE001
                        torn.append(error.__class__.__name__)
            finally:
                stop.append(True)
                thread.join(timeout=5)
        self.assertEqual(torn, [], f"讀壞 {len(torn)} 次")
        self.assertEqual(wrote_bad, [], f"寫壞 {len(wrote_bad)} 次")

    # [VRN-ID] VRN-TST005-FNC109 · TEST
    def test_a_planted_symlink_on_the_temp_path_is_not_followed(self):
        """Codex PR #72 P1，實測證實過的：可預測的 tmp 名字可以被先放一個 symlink 佔住，
        `write_text` 會跟著它走 —— 當時受害者檔被報告內容整個覆蓋，而目標檔變成指向它的
        symlink。mkstemp 的 O_CREAT|O_EXCL 讓名字不可預測、存在就失敗。

        這裡連**舊版會用的兩種名字**都預埋，確保不是換個寫法繼續可預測。
        """
        main = load_main()
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            victim = folder / "someone_else.txt"
            victim.write_text("別人的檔\n", encoding="utf-8")
            target = folder / "report.json"
            for name in (f"{target.name}.{os.getpid()}.{threading.get_ident()}.tmp", f"{target.name}.tmp"):
                (folder / name).symlink_to(victim)
            main.def_write_json(target, {"secret": "報告內容"})
            self.assertEqual(victim.read_text(encoding="utf-8"), "別人的檔\n", "受害者檔被寫穿了")
            self.assertFalse(target.is_symlink(), "目標變成 symlink")
            self.assertEqual(json.loads(target.read_text(encoding="utf-8")), {"secret": "報告內容"})

    # 原本這裡是「原始碼裡要有 os.getpid()」那種斷言。唯一性現在由 O_EXCL 保證，
    # 名字長什麼樣不再是重點 —— 要驗的是行為，上下兩條都是真的跑。
    # [VRN-ID] VRN-TST005-FNC110 · TEST
    def test_the_destination_keeps_its_own_permissions(self):
        """Codex PR #72 P1：tmp＋rename 會讓目標沿用 tmp 的 mode。
        POSIX 實測 0600 的報告被換成 0644 —— 等於把內容攤開給同機器其他人看。

        **比的是「換檔前後一樣」，不是某個字面值。** 第一版拿 `0o600` 去比，
        在 Windows 上從來就不可能過：那裡 `os.chmod` 只認唯讀位元，
        `chmod(0o600)` 之後 `st_mode` 仍然回 0o666（CI 紅在 `438 != 384`）。
        比「維持原樣」才是這條真正要驗的性質，而且兩個平台都成立。
        """
        main = load_main()
        with tempfile.TemporaryDirectory() as tmp:
            for want in (0o600, 0o644):
                path = Path(tmp) / f"r{want:o}.json"
                path.write_text('{"a": 1}', encoding="utf-8")
                os.chmod(path, want)
                before = stat.S_IMODE(path.stat().st_mode)   # Windows 上這不一定等於 want
                main.def_write_json(path, {"a": 2})
                self.assertEqual(stat.S_IMODE(path.stat().st_mode), before,
                                 f"換檔把 {before:04o} 改掉了")

    # [VRN-ID] VRN-TST005-FNC117 · TEST
    @unittest.skipIf(os.name == "nt", "Windows 沒有 POSIX 權限位；os.chmod 只認唯讀位元")
    def test_a_brand_new_file_is_not_widened(self):
        """目標不存在時沒有舊權限可抄，留 mkstemp 的 0600 —— 比 umask 預設更緊，不可以更鬆。"""
        main = load_main()
        with tempfile.TemporaryDirectory() as tmp:
            fresh = Path(tmp) / "new.json"
            main.def_write_json(fresh, {"a": 1})
            self.assertEqual(stat.S_IMODE(fresh.stat().st_mode), 0o600)

    # [VRN-ID] VRN-TST005-FNC111 · TEST
    def test_the_temp_file_sits_beside_the_target(self):
        """os.replace 跨檔案系統會失敗 —— tmp 必須和目標同一個資料夾。"""
        main = load_main()
        source = Path(main.__file__).read_text(encoding="utf-8")
        body = source.partition("def def_write_atomic")[2].split("\nACCESS_ATTEMPTS")[0]
        self.assertIn("tempfile.mkstemp(dir=str(path.parent)", body, "tmp 要建在目標的資料夾裡")
        self.assertIn("os.replace(tmp, path)", body)

    # [VRN-ID] VRN-TST005-FNC107 · TEST
    def test_two_threads_writing_one_path_do_not_tear_it(self):
        """斷言原始碼帶 thread id 不等於驗過它 —— 真的開兩條執行緒寫同一個檔。

        只帶 pid 的版本在這裡會壞:兩條執行緒算出同一個 tmp 名字,A 要換檔的瞬間
        B 已經把它截短重寫。VRN_Lock.save() 的那個 bug 就是這樣,實測讀壞 70 次。
        """
        main = load_main()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "shared.json"
            main.def_write_json(path, {"seed": True})
            torn, wrote_bad, stop = [], [], []

            # [VRN-ID] VRN-TST005-FNC108 · LOGIC
            def writer(tag):
                n = 0
                while not stop:
                    try:
                        main.def_write_json(path, {"by": tag, "rows": [tag * 80] * ((n % 300) + 1)})
                    except Exception as error:  # noqa: BLE001
                        wrote_bad.append(error.__class__.__name__)
                    n += 1

            threads = [threading.Thread(target=writer, args=(c,), daemon=True) for c in ("y", "z")]
            for thread in threads:
                thread.start()
            try:
                for _ in range(300):
                    try:
                        main.def_read_json(path)
                    except Exception as error:  # noqa: BLE001
                        torn.append(error.__class__.__name__)
            finally:
                stop.append(True)
                for thread in threads:
                    thread.join(timeout=5)
            leftovers = [p.name for p in Path(tmp).iterdir() if p.name.endswith(".tmp")]
        self.assertEqual(torn, [], f"讀壞 {len(torn)} 次")
        self.assertEqual(wrote_bad, [], f"寫壞 {len(wrote_bad)} 次：{wrote_bad[:3]}")
        self.assertEqual(leftovers, [], f"tmp 殘留:{leftovers}")

    # [VRN-ID] VRN-TST005-FNC086 · TEST
    def test_a_failed_write_leaves_the_original_whole_and_no_litter(self):
        main = load_main()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "r.json"
            main.def_write_json(path, {"keep": "me"})
            with self.assertRaises(TypeError):
                main.def_write_json(path, {"bad": object()})
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), {"keep": "me"},
                             "寫壞的那一次,原檔一個位元組都沒動")
            self.assertEqual([p.name for p in Path(tmp).iterdir()], ["r.json"], "tmp 不留在現場")


# [VRN-ID] VRN-TST005-CLS015 · CLASS
class TestTempSpaceGate(unittest.TestCase):
    """2026-10-19:P10 TEMP 報本輪夾、報清掉幾輪,就是不報剩餘空間 —— 而 TEMP 是這條鏈上
    唯一真的會用完的資源。用完的樣子不是一聲乾淨的錯誤,是半份檔案留在那裡。

    第一版我拿 budget_gb 當門檻,而 budget = min(cap, 剩餘的 25%),所以 free < budget
    恆不成立 —— WARN 分支永遠跑不到。所以這裡每一個分支都要有自己的測試:
    一道永遠不會警告的閘,和沒有這道閘是一樣的。
    """

    # [VRN-ID] VRN-TST005-CLS016 · CLASS
    class Usage:
        # [VRN-ID] VRN-TST005-FNC087 · INIT
        def __init__(self, free_gb, total_gb=252.0):
            self.free = int(free_gb * (1 << 30))
            self.total = int(total_gb * (1 << 30))
            self.used = self.total - self.free

    # [VRN-ID] VRN-TST005-FNC088 · LOGIC
    def def_row_for(self, free_gb):
        import shutil
        from unittest import mock
        main = load_main()
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.object(shutil, "disk_usage", return_value=self.Usage(free_gb)):
                rows = main.def_gate_temp_space(tmp)
        self.assertEqual(len(rows), 1)
        return rows[0]

    # [VRN-ID] VRN-TST005-FNC089 · TEST
    def test_a_full_temp_fails(self):
        row = self.def_row_for(0.4)
        self.assertEqual(row["status"], "FAIL")
        self.assertIn("半份檔案", row["detail"])

    # [VRN-ID] VRN-TST005-FNC090 · TEST
    def test_too_little_for_the_cache_to_ever_fill_warns(self):
        """這個分支必須跑得到 —— 第一版就是死在這裡。"""
        row = self.def_row_for(4.0)
        self.assertEqual(row["status"], "WARN")
        self.assertIn("VIA_CACHE_MAX_GB", row["detail"])

    # [VRN-ID] VRN-TST005-FNC091 · TEST
    def test_plenty_of_room_passes(self):
        row = self.def_row_for(60.0)
        self.assertEqual(row["status"], "PASS")

    # [VRN-ID] VRN-TST005-FNC092 · TEST
    def test_every_branch_is_reachable(self):
        """三個燈號都要有一組輸入打得到,不然這道閘是裝飾品。"""
        got = {self.def_row_for(gb)["status"] for gb in (0.4, 4.0, 60.0)}
        self.assertEqual(got, {"FAIL", "WARN", "PASS"})

    # [VRN-ID] VRN-TST005-FNC093 · TEST
    def test_the_gate_is_wired_into_p10_not_just_defined(self):
        """驗了函式不等於驗了那條路 —— P10 真的要把這一列帶出來。"""
        main = load_main()
        with tempfile.TemporaryDirectory() as tmp:
            rows = main.def_gate_temp(({"run": tmp, "swept": []}), {"mb": 1.0})
        items = [r["item"] for r in rows]
        self.assertTrue(any("剩餘空間" in i for i in items), f"P10 沒有帶出空間列:{items}")
        self.assertTrue(all(r["gate"] == "P10 TEMP" for r in rows))

    # [VRN-ID] VRN-TST005-FNC094 · TEST
    def test_an_unmeasurable_temp_says_so_instead_of_passing(self):
        import shutil
        from unittest import mock
        main = load_main()
        with mock.patch.object(shutil, "disk_usage", side_effect=OSError("nope")):
            rows = main.def_gate_temp_space("/definitely/not/here")
        self.assertEqual(rows[0]["status"], "WARN")
        self.assertIn("量不到", rows[0]["detail"])


# [VRN-ID] VRN-TST005-CLS017 · CLASS
class TestAccessRetry(unittest.TestCase):
    """2026-10-19 CI 教的,而且**這台 Linux 驗不到**:Windows 上 `os.replace` 在目標檔
    被另一個握把開著時丟 `PermissionError: [WinError 5]`,讀的那一側在換檔的瞬間也會。

    不重試的話,原子寫入在操作員那台（Windows）會把「讀到半份」換成「這一輪直接炸掉」,
    那不是改善。所以這裡測的是重試邏輯本身 —— 它不看平台,我在 Linux 上也證得了。
    """

    # [VRN-ID] VRN-TST005-FNC095 · TEST
    def test_a_transient_denial_is_waited_out(self):
        main = load_main()
        calls = []

        # [VRN-ID] VRN-TST005-FNC096 · LOGIC
        def flaky():
            calls.append(1)
            if len(calls) < 4:
                raise PermissionError(5, "Access is denied")
            return "done"

        self.assertEqual(main.def_retry_access(flaky), "done")
        self.assertEqual(len(calls), 4, "前三次該被等過去")

    # [VRN-ID] VRN-TST005-FNC097 · TEST
    def test_a_permanent_denial_is_raised_not_swallowed(self):
        """撐過 1 秒還是不行就不是暫時的 —— 吞掉它會變成另一種假綠燈。"""
        main = load_main()
        calls = []

        # [VRN-ID] VRN-TST005-FNC098 · LOGIC
        def always():
            calls.append(1)
            raise PermissionError(5, "Access is denied")

        with self.assertRaises(PermissionError):
            main.def_retry_access(always)
        self.assertEqual(len(calls), main.ACCESS_ATTEMPTS)

    # [VRN-ID] VRN-TST005-FNC099 · TEST
    def test_other_errors_are_not_retried(self):
        """檔案不在就是不在,重試 20 次只是讓錯誤慢一秒才出現。"""
        main = load_main()
        calls = []

        # [VRN-ID] VRN-TST005-FNC100 · LOGIC
        def missing():
            calls.append(1)
            raise FileNotFoundError(2, "no such file")

        with self.assertRaises(FileNotFoundError):
            main.def_retry_access(missing)
        self.assertEqual(len(calls), 1)

    # [VRN-ID] VRN-TST005-FNC101 · TEST
    def test_the_write_path_actually_goes_through_the_retry(self):
        """驗了函式不等於驗了那條路:寫入與讀取都要真的走它。"""
        main = load_main()
        source = Path(main.__file__).read_text(encoding="utf-8")
        write_body = source.partition("def def_write_atomic")[2].split("\nACCESS_ATTEMPTS")[0]
        self.assertIn("def_retry_access(lambda: os.replace(tmp, path))", write_body)
        read_body = source.partition("def def_read_json")[2].split("\ndef ")[0]
        self.assertIn("def_retry_access", read_body)

    # [VRN-ID] VRN-TST005-FNC102 · TEST
    def test_the_window_is_about_a_second(self):
        """太短擋不住防毒／索引器,太長會把真正的權限問題拖成一分鐘。"""
        main = load_main()
        self.assertGreaterEqual(main.ACCESS_ATTEMPTS * main.ACCESS_PAUSE, 0.5)
        self.assertLessEqual(main.ACCESS_ATTEMPTS * main.ACCESS_PAUSE, 3.0)


# [VRN-ID] VRN-TST005-CLS018 · CLASS
class TestLedgerTmpName(unittest.TestCase):
    """2026-10-19 實測:鎖帳本的 tmp 檔名沒帶 pid。

    兩個寫入者對 400 次讀:共用 tmp 讀壞 70 次、換檔時 tmp 已被搶走 156 次;
    帶 pid／thread 之後都是 0。帳本是擋退步的那一份 —— 它壞掉等於守門自己先倒。
    """

    # [VRN-ID] VRN-TST005-FNC103 · LOGIC
    @staticmethod
    def def_save_body():
        main = load_main()
        lock = main.def_load_module("VRN_Main_locktest", main.ENGINE_FILES["lock"])
        source = Path(lock.__file__).read_text(encoding="utf-8")
        body = source.partition("    def save(self):")[2].split("\n    def ")[0]
        # 只看程式碼：註解裡引用舊寫法是為了講清楚為什麼改，不該讓守門誤判成「舊碼還在」
        return "\n".join(ln for ln in body.splitlines() if not ln.lstrip().startswith("#"))

    # [VRN-ID] VRN-TST005-FNC112 · TEST
    def test_the_temp_name_is_neither_shared_nor_predictable(self):
        """兩個問題一起解：固定名字會讓兩個行程撞在一起（實測讀壞 70 次），
        而**可預測**的名字還可以被先放 symlink 佔住（Codex PR #72 P1）。
        mkstemp 的 O_CREAT|O_EXCL 兩個都堵住，唯一性不再靠自己組名字。"""
        body = self.def_save_body()
        self.assertIn("tempfile.mkstemp(", body)
        self.assertNotIn('with_suffix(".tmp")', body, "舊的共用檔名不可以留著")
        self.assertNotIn("os.getpid()", body, "名字不該再是可預測的組合")

    # [VRN-ID] VRN-TST005-FNC105 · TEST
    def test_the_temp_file_stays_in_the_ledger_folder(self):
        """os.replace 跨檔案系統會失敗 —— tmp 必須和帳本同一個資料夾。"""
        body = self.def_save_body()
        self.assertIn("dir=str(self.home)", body, "tmp 要建在帳本自己的資料夾裡")
        self.assertIn("os.replace(tmp, self.path)", body)

    # [VRN-ID] VRN-TST005-FNC106 · TEST
    def test_a_real_save_still_round_trips(self):
        """改了檔名之後，存檔本身要照樣能存能讀回來。"""
        main = load_main()
        lock = main.def_load_module("VRN_Main_locktest", main.ENGINE_FILES["lock"])
        with tempfile.TemporaryDirectory() as tmp:
            ledger = lock.Ledger(Path(tmp))
            ledger.data["parts"] = {"a|cover.x": {"value": "1"}}
            ledger.save()
            back = json.loads(Path(ledger.path).read_text(encoding="utf-8"))
            self.assertEqual(back["parts"], {"a|cover.x": {"value": "1"}})
            leftovers = [p.name for p in Path(tmp).iterdir() if p.name.endswith(".tmp")]
            self.assertEqual(leftovers, [], f"tmp 不留在現場:{leftovers}")


# [VRN-ID] VRN-TST005-CLS019 · CLASS
class TestTempSpacePreflight(unittest.TestCase):
    """Codex PR #72 P2:空間閘本來只在收尾時跑,也就是 AutoTestLoop 把 TEMP 寫滿**之後**。

    一道防磁碟耗盡的閘跑在耗盡之後,等於沒有這道閘 —— 和這一輪一直在抓的
    「閘跑的那一刻和真正出事的那一刻不是同一刻」是同一個毛病,而這次是我自己寫的。
    """

    # [VRN-ID] VRN-TST005-FNC113 · TEST
    def test_the_space_check_runs_before_the_heavy_work(self):
        """順序本身就是這條的全部 —— 所以這一條驗的就是順序。"""
        main = load_main()
        body = TestSyncGate.def_fn_body("def_cmd_run_body")
        guard = body.find("def_gate_temp_space")
        heavy = body.find('def_load_module("VRN_Main_autotest"')
        self.assertGreater(guard, -1, "前置檢查不見了")
        self.assertGreater(heavy, -1, "找不到 AutoTestLoop 的啟動點")
        self.assertLess(guard, heavy, "空間檢查必須在 AutoTestLoop 之前")

    # [VRN-ID] VRN-TST005-FNC114 · TEST
    def test_a_full_temp_stops_the_run_before_it_starts(self):
        """不是只驗有呼叫 —— 真的叫 def_cmd_run_body,看它停不停得下來。"""
        import shutil
        from unittest import mock
        main = load_main()

        # [VRN-ID] VRN-TST005-CLS020 · CLASS
        class Usage:
            # [VRN-ID] VRN-TST005-FNC115 · INIT
            def __init__(self):
                self.total = 252 * (1 << 30)
                self.free = int(0.3 * (1 << 30))
                self.used = self.total - self.free

        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "run"
            out.mkdir()
            args = argparse.Namespace(accel_home="", synthetic=True, rounds=1, truth="", no_audit=True,
                                      limit=0, lock_home="", no_focus=True, no_open=True, out=str(out))
            with mock.patch.object(shutil, "disk_usage", return_value=Usage()):
                code = main.def_cmd_run_body(args, "", out, {"run": str(out)})
            self.assertEqual(code, 1, "TEMP 不夠卻還是往下跑了")
            self.assertEqual(list(out.iterdir()), [], "擋下來之後不該留下任何中介檔")

    # [VRN-ID] VRN-TST005-FNC116 · TEST
    def test_the_reporting_row_is_still_there_at_the_end(self):
        """擋下來是防線,收尾那一列是回報 —— 兩個都要在,而且是同一支函式。"""
        main = load_main()
        body = TestSyncGate.def_fn_body("def_gate_temp")
        self.assertIn("def_gate_temp_space", body, "P10 收尾仍要帶出空間列")
        source = Path(main.__file__).read_text(encoding="utf-8")
        self.assertEqual(source.count("def def_gate_temp_space"), 1, "判準只能有一份")


# [VRN-ID] VRN-TST005-CLS021 · CLASS
class TestTimeFormatGate(unittest.TestCase):
    """操作員 2026-10-19：「時間擷取後格式一律為 YYYY / YYYY-MM / YYYY-MM-DD」。

    規則沒有閘在管就不是規則 —— 這組釘的是那道閘,以及它的比對器。
    比對器我寫壞過兩次,兩次方向相反:
      子字串      → CompanyNameCan[date] 被當成時間欄（誤判 29 次）
      正則詞邊界  → camelCase 的 Report[Date]Display 整欄漏掉（150 筆斜線日期沒抓到,閘還報 PASS）
    所以兩個方向都要有測試。
    """

    # [VRN-ID] VRN-TST005-FNC118 · TEST
    def test_the_matcher_catches_camel_case_and_not_candidate(self):
        main = load_main()
        for name in ("ReportDate", "ReportDateDisplay", "PageDate", "FilenameDate",
                     "FiscalYear", "period", "period_raw", "PartialDates", "日期"):
            self.assertTrue(main.def_time_field(name), f"{name} 應該算時間欄")
        for name in ("CompanyNameCandidate", "BrokerCandidate", "TargetPrice", "Analyst", "RunID"):
            self.assertFalse(main.def_time_field(name), f"{name} 不是時間欄")

    # [VRN-ID] VRN-TST005-FNC119 · LOGIC
    @staticmethod
    def def_frame(tmp, header, rows):
        folder = Path(tmp) / "autotest" / "round1" / "dataframes"
        folder.mkdir(parents=True, exist_ok=True)
        with (folder / "vrn_probe.csv").open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=header)
            writer.writeheader()
            for r in rows:
                writer.writerow(r)
        return Path(tmp)

    # [VRN-ID] VRN-TST005-FNC120 · TEST
    def test_a_slash_date_fails_the_gate(self):
        main = load_main()
        with tempfile.TemporaryDirectory() as tmp:
            out = self.def_frame(tmp, ["ReportDate"], [{"ReportDate": "2025/08/19"}])
            rows = main.def_gate_time_format(main.def_time_scan(out))
        self.assertEqual(rows[0]["status"], "FAIL")
        self.assertTrue(any("2025/08/19" in r["detail"] for r in rows), "要把違規的值印出來")

    # [VRN-ID] VRN-TST005-FNC121 · TEST
    def test_the_three_canonical_forms_pass(self):
        main = load_main()
        with tempfile.TemporaryDirectory() as tmp:
            out = self.def_frame(tmp, ["ReportDate"],
                                 [{"ReportDate": "2025"}, {"ReportDate": "2025-08"}, {"ReportDate": "2025-08-19"}])
            rows = main.def_gate_time_format(main.def_time_scan(out))
        self.assertEqual(rows[0]["status"], "PASS")
        self.assertIn("合規 3 筆", rows[0]["detail"])

    # [VRN-ID] VRN-TST005-FNC122 · TEST
    def test_a_raw_column_is_exempt_and_named(self):
        """原文欄存在的理由就是留住來源長什麼樣 —— 但例外要看得見,不是默默跳過。"""
        main = load_main()
        with tempfile.TemporaryDirectory() as tmp:
            out = self.def_frame(tmp, ["period_raw"], [{"period_raw": "2024A"}])
            rows = main.def_gate_time_format(main.def_time_scan(out))
        self.assertEqual(rows[0]["status"], "PASS")
        self.assertIn("period_raw", rows[0]["detail"], "排除了就要點名")

    # [VRN-ID] VRN-TST005-FNC123 · TEST
    def test_a_structured_value_is_not_a_time_value(self):
        """PartialDates 裝的是「為什麼沒擷取到」的診斷（YEAR_MISSING,三種形式本來就表達不了）。"""
        main = load_main()
        with tempfile.TemporaryDirectory() as tmp:
            out = self.def_frame(tmp, ["PartialDates"],
                                 [{"PartialDates": '[{"day": 15, "month": 9, "status": "YEAR_MISSING"}]'}])
            rows = main.def_gate_time_format(main.def_time_scan(out))
        self.assertEqual(rows[0]["status"], "PASS")
        self.assertIn("結構不是時間值", rows[0]["detail"])

    # [VRN-ID] VRN-TST005-FNC133 · TEST
    def test_a_bad_value_without_a_four_digit_year_still_fails(self):
        """Codex PR #73 P2：第一版用「值裡有沒有連續四位數字」當前置濾網,沒有的就跳過。

        那條濾網放過的**正是最該抓的**：民國年 `114/12/02`、`Q1`、`unknown` 都沒有連續四位數字,
        閘照報 PASS。濾網已經拆掉 —— 非空、欄名在管、不是結構值,就一定要過 TIME_OK_RX。
        實測語料裡被它濾掉的有 24564 筆（`PeriodType=FY`）,一筆都沒驗過。
        """
        main = load_main()
        for value in ("114/12/02", "Q1", "unknown", "9/15", "民國一一四年"):
            with tempfile.TemporaryDirectory() as tmp:
                out = self.def_frame(tmp, ["ReportDate"], [{"ReportDate": value}])
                rows = main.def_gate_time_format(main.def_time_scan(out))
            self.assertEqual(rows[0]["status"], "FAIL", f"{value} 不是三種形式之一，要紅")
            self.assertTrue(any(value[:20] in r["detail"] for r in rows), f"{value} 要被印出來")

    # [VRN-ID] VRN-TST005-FNC134 · TEST
    def test_a_column_about_a_time_is_exempt_and_named(self):
        """`PeriodType=FY` 說的是期別的**種類**,`DateConflict` 說的是為什麼對不上 —— 都不是時間值。

        例外照欄名明講、在說明欄點名,不是靠「值長得不像時間」默默濾掉（那條濾網連真違規一起放過）。
        """
        main = load_main()
        self.assertTrue(main.def_time_about("PeriodType"))
        self.assertTrue(main.def_time_about("DateConflict"))
        self.assertTrue(main.def_time_about("PeriodLabelRaw"))
        for name in ("ReportDate", "ReportDateDisplay", "FiscalYear", "period"):
            self.assertFalse(main.def_time_about(name), f"{name} 裝的就是時間值，不准被排除")
        with tempfile.TemporaryDirectory() as tmp:
            out = self.def_frame(tmp, ["PeriodType", "ReportDate"],
                                 [{"PeriodType": "FY", "ReportDate": "2025-08-19"}])
            scan = main.def_time_scan(out)
            rows = main.def_gate_time_format(scan)
        self.assertEqual(rows[0]["status"], "PASS")
        self.assertEqual(scan["about"], {"vrn_probe.csv:PeriodType": 1})
        self.assertIn("PeriodType", rows[0]["detail"], "排除了就要點名")
        self.assertIn("合規 1 筆", rows[0]["detail"], "ReportDate 還是要驗")

    # [VRN-ID] VRN-TST005-FNC135 · TEST
    def test_every_value_is_accounted_for(self):
        """進去幾個非空值,四類加起來就要是幾個 —— 不可以有值無聲消失。

        閘報 PASS 的前提是「每一個值都分到了一類」,而不是「我沒看到紅的」。
        """
        main = load_main()
        header = ["ReportDate", "period_raw", "PeriodType", "PartialDates"]
        rows_in = [{"ReportDate": "2025-08-19", "period_raw": "2024A", "PeriodType": "FY",
                    "PartialDates": '[{"day": 15}]'},
                   {"ReportDate": "2025/08/19", "period_raw": "2025E", "PeriodType": "CY",
                    "PartialDates": '[{"day": 16}]'}]
        with tempfile.TemporaryDirectory() as tmp:
            scan = main.def_time_scan(self.def_frame(tmp, header, rows_in))
        counted = (sum(scan["ok"].values()) + sum(v["n"] for v in scan["bad"].values())
                   + sum(scan["skipped"].values()) + sum(scan["about"].values())
                   + sum(scan["structured"].values()))
        self.assertEqual(counted, len(rows_in) * len(header), "每一個非空值都要分到一類")
        self.assertEqual(sum(scan["ok"].values()), 1)
        self.assertEqual(sum(v["n"] for v in scan["bad"].values()), 1)


# [VRN-ID] VRN-TST005-CLS022 · CLASS
class TestCrossSourceGate(unittest.TestCase):
    """操作員 2026-10-19：「相互對照兩個以上相同即算對照成功」。

    那條規則本來就在 VRN_TitleTrim._vote（`len(top["groups"]) >= 2`），以前只活在 why
    那句中文裡。現在 _vote 一併記下 agree，閘讀數字不解析散文 —— 自己再判一次就是第二顆頭。
    """

    # [VRN-ID] VRN-TST005-FNC124 · LOGIC
    @staticmethod
    def def_parts(tmp, rows):
        folder = Path(tmp) / "autotest" / "round1" / "dataframes"
        folder.mkdir(parents=True, exist_ok=True)
        header = ["file", "part", "state", "agree", "sources", "why"]
        with (folder / "vrn_trim_parts.csv").open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=header)
            writer.writeheader()
            for r in rows:
                writer.writerow({k: r.get(k, "") for k in header})
        return Path(tmp)

    # [VRN-ID] VRN-TST005-FNC125 · TEST
    def test_two_agreeing_sources_pass(self):
        main = load_main()
        with tempfile.TemporaryDirectory() as tmp:
            out = self.def_parts(tmp, [{"file": "a.pdf", "part": "title.ticker", "state": "VERIFIED", "agree": "2"},
                                       {"file": "a.pdf", "part": "cover.rating", "state": "VERIFIED", "agree": "3"}])
            scan = main.def_cross_source_scan(out)
            rows = main.def_gate_cross_source(scan)
        self.assertEqual((scan["verified"], scan["with_agree"], scan["violations"]), (2, 2, []))
        self.assertEqual(rows[0]["status"], "PASS")

    # [VRN-ID] VRN-TST005-FNC126 · TEST
    def test_one_source_marked_verified_is_a_violation(self):
        """標成對照成功卻只有一個來源支持 —— 那正是這道閘要抓的。"""
        main = load_main()
        with tempfile.TemporaryDirectory() as tmp:
            out = self.def_parts(tmp, [{"file": "a.pdf", "part": "cover.broker", "state": "VERIFIED", "agree": "1"}])
            rows = main.def_gate_cross_source(main.def_cross_source_scan(out))
        self.assertEqual(rows[0]["status"], "FAIL")
        self.assertTrue(any("cover.broker" in r["item"] for r in rows))

    # [VRN-ID] VRN-TST005-FNC127 · TEST
    def test_a_part_outside_the_shared_rule_is_named_not_counted_as_a_violation(self):
        """title.core_view 這種從別的部位繼承狀態的,沒有 agree —— 照實點名,不混進違規。"""
        main = load_main()
        with tempfile.TemporaryDirectory() as tmp:
            out = self.def_parts(tmp, [{"file": "a.pdf", "part": "title.core_view", "state": "VERIFIED", "agree": ""}])
            scan = main.def_cross_source_scan(out)
            rows = main.def_gate_cross_source(scan)
        self.assertEqual(scan["violations"], [])
        self.assertEqual(scan["own_path"], {"title.core_view": 1})
        self.assertEqual(rows[0]["status"], "PASS")
        self.assertIn("title.core_view", rows[0]["detail"], "沒走共用判準的要看得見")

    # [VRN-ID] VRN-TST005-FNC128 · TEST
    def test_the_headline_counts_only_what_this_rule_checked(self):
        """標題不准把沒驗到的算成驗過的。

        我第一版的標題是「對照成功的部位 {verified} 個」—— 實測 1310 個 VERIFIED 裡只有 640 個
        走這條規則,剩下 670 個是別條路徑判的。那句話會被讀成「1310 個都過了兩來源對照」,
        也就是把這條規則**沒驗到**的部位算成驗過了。「不知道不等於沒事」,同樣地,
        「別人驗的」也不等於「我驗過的」。
        """
        main = load_main()
        with tempfile.TemporaryDirectory() as tmp:
            out = self.def_parts(tmp, [{"file": "a.pdf", "part": "title.ticker", "state": "VERIFIED", "agree": "2"}]
                                 + [{"file": "a.pdf", "part": f"annual.revenue@202{i}", "state": "VERIFIED", "agree": ""}
                                    for i in range(4)])
            scan = main.def_cross_source_scan(out)
            rows = main.def_gate_cross_source(scan)
        self.assertEqual((scan["verified"], scan["with_agree"]), (5, 1))
        self.assertEqual(scan["own_kinds"], {"annual.*": 4}, "整群要數得出來,不是只列前幾名")
        head = rows[0]["item"]
        self.assertIn("1 個", head, "標題要說的是這條規則真的驗到的那 1 個")
        self.assertNotIn("對照成功的部位 5", head)
        self.assertIn("各自路徑另計 4 個", head, "沒驗到的那 4 個要在標題上就看得見")
        self.assertEqual(rows[0]["status"], "PASS")


# [VRN-ID] VRN-TST005-CLS023 · CLASS
class TestSyncCommitMessage(unittest.TestCase):
    """sync 那顆 commit 的訊息：倉內不寫死署名，署名由環境變數進來。

    鏈的規矩是「不手動提交」，所以要附署名就得讓 sync 自己附 —— 但署名內容
    不該被烙進倉裡。測的是 def_cmd_sync 真正呼叫的那一支（它只呼叫這裡）。
    """

    # [VRN-ID] VRN-TST005-FNC129 · LOGIC
    @staticmethod
    def def_msg(main, trailer):
        keep = os.environ.get(main.SYNC_TRAILER_ENV)
        if trailer is None:
            os.environ.pop(main.SYNC_TRAILER_ENV, None)
        else:
            os.environ[main.SYNC_TRAILER_ENV] = trailer
        try:
            return main.def_commit_message("AMBER", {"FAIL": 0, "WARN": 21}, "/tmp/run")
        finally:
            if keep is None:
                os.environ.pop(main.SYNC_TRAILER_ENV, None)
            else:
                os.environ[main.SYNC_TRAILER_ENV] = keep

    # [VRN-ID] VRN-TST005-FNC130 · TEST
    def test_no_trailer_set_changes_nothing(self):
        main = load_main()
        message = self.def_msg(main, None)
        self.assertTrue(message.startswith(main.SYNC_COMMIT_PREFIX + "："))
        self.assertIn("FAIL=0 WARN=21", message)
        self.assertIn("報告：/tmp/run", message)
        self.assertEqual(message, self.def_msg(main, "   \n  \n"), "只有空白的署名等於沒設")

    # [VRN-ID] VRN-TST005-FNC131 · TEST
    def test_the_trailer_lands_at_the_end_one_line_each(self):
        main = load_main()
        message = self.def_msg(main, "Co-Authored-By: Someone <x@y>\nRef: https://example.invalid/abc\n")
        lines = [line for line in message.splitlines() if line.strip()]
        self.assertEqual(lines[-2:], ["Co-Authored-By: Someone <x@y>", "Ref: https://example.invalid/abc"],
                         "署名要在最後，一行一條")
        self.assertTrue(message.endswith("\n"), "commit 訊息結尾留換行")
        self.assertIn("報告：/tmp/run", message, "原本的內容一個字都不准掉")

    # [VRN-ID] VRN-TST005-FNC132 · TEST
    def test_the_repository_source_carries_no_signature_text(self):
        """倉內的碼不准寫死署名內容 —— 不然換一個跑鏈的人就要改碼。"""
        src = MAIN_PATH.read_text(encoding="utf-8")
        body = src.split("def def_commit_message", 1)[1].split("\ndef ", 1)[0]
        self.assertIn("os.environ.get(SYNC_TRAILER_ENV)", body, "署名要從環境變數讀")
        self.assertNotIn("Co-Authored-By", body, "署名文字不准寫在倉裡")
        sync = src.split("def def_cmd_sync", 1)[1].split("\ndef ", 1)[0]
        self.assertIn("def_commit_message(", sync, "sync 要呼叫它")
        self.assertNotIn("SYNC_COMMIT_PREFIX", sync, "訊息只准有一個產生處，sync 裡不准自己再組一份")


# [VRN-ID] VRN-TST005-CLS024 · CLASS
class def_MergePolicyTests(unittest.TestCase):
    """操作員 2026-10-20「解決 GITHUB 衝突問題」。

    根因量過：兩條分支只要都跑過鏈，`git merge` 必定在每輪重生的那幾個檔上撞車，
    而 git 會把 `<<<<<<<` 寫進 JSON 冊裡 —— 冊當場不再是合法 JSON。
    SSOT_BOOKS 上本來就有 `generated` 旗標，可是（一）只標到 4 本、（二）**沒有任何人讀它**。
    """

    # [VRN-ID] VRN-TST005-FNC140 · LOGIC
    @classmethod
    def setUpClass(cls):
        cls.main = load_main()

    # [VRN-ID] VRN-TST005-FNC141 · TEST
    def test_build_writes_nothing_that_the_declaration_misses(self):
        """`build` 裡每一個 `def_write_json(<常數>, …)` 的目標，都要在宣告上。

        這條不是拿清單比清單（那只是把同一份名單抄兩次），是**讀 build 的 AST**：
        build 真的會寫誰，就必須宣告誰。2026-10-20 之前 INDEX 冊就是這樣漏掉的。
        """
        tree = ast.parse(Path(self.main.__file__).read_text(encoding="utf-8"))
        body = next(n for n in ast.walk(tree)
                    if isinstance(n, ast.FunctionDef) and n.name == "def_cmd_build")
        targets = {node.args[0].id for node in ast.walk(body)
                   if isinstance(node, ast.Call) and getattr(node.func, "id", "") == "def_write_json"
                   and node.args and isinstance(node.args[0], ast.Name)}
        self.assertGreaterEqual(len(targets), 4, "build 的 AST 掃不到寫檔動作：這條測試自己壞了")
        declared = set(self.main.def_generated_paths())
        missing = sorted(name for name in targets
                         if self.main.def_rel(getattr(self.main, name)) not in declared)
        self.assertEqual(missing, [], "build 會整個重寫這些檔，宣告上卻沒有："
                                      f"{missing} —— 合併時 git 會把衝突標記寫進去")

    # [VRN-ID] VRN-TST005-FNC142 · TEST
    def test_a_book_whose_role_says_generated_carries_the_flag(self):
        """說明欄寫「生成」是散文，沒有人讀得到；旗標才是機器看得懂的那一份。"""
        prose = [spec["path"] for spec in self.main.SSOT_BOOKS
                 if "生成" in spec["role"] and not spec.get("generated")]
        self.assertEqual(prose, [], f"這幾本的說明寫了是生成的，卻沒標 generated: True：{prose}")

    # [VRN-ID] VRN-TST005-FNC143 · TEST
    def test_every_declared_path_is_really_there(self):
        """宣告了卻不存在 = 宣告在描述一個不存在的世界。"""
        gone = [p for p in self.main.def_generated_paths() if not (self.main.VRN_ROOT / p).is_file()]
        self.assertEqual(gone, [], f"宣告上有、磁碟上沒有：{gone}")

    # [VRN-ID] VRN-TST005-FNC144 · TEST
    def test_the_merge_policy_file_matches_the_declaration(self):
        """`.gitattributes` 要跟宣告逐字相同 —— 這就是「旗標真的被接起來」的那一環。"""
        rows = self.main.def_gate_gitattributes()
        self.assertEqual([r for r in rows if r["status"] == "FAIL"], [],
                         "`.gitattributes` 跟宣告對不上：跑 build")
        text = self.main.GITATTRIBUTES_PATH.read_text(encoding="utf-8")
        for path in self.main.def_generated_paths():
            self.assertIn(f"{path} ", text, f"{path} 沒有合併規矩")

    # [VRN-ID] VRN-TST005-FNC145 · TEST
    def test_the_gate_goes_red_when_the_policy_file_drifts(self):
        """守門要會紅才叫守門 —— 檔不見、或被手改，都要是 FAIL。"""
        keep = self.main.GITATTRIBUTES_PATH
        with tempfile.TemporaryDirectory() as tmp:
            try:
                self.main.GITATTRIBUTES_PATH = Path(tmp) / ".gitattributes"
                gone = self.main.def_gate_gitattributes()
                self.assertEqual([r["status"] for r in gone], ["FAIL"], "檔不見了還放行")
                self.main.GITATTRIBUTES_PATH.write_text("# 手改的\n", encoding="utf-8")
                stale = self.main.def_gate_gitattributes()
                self.assertEqual([r["status"] for r in stale], ["FAIL"], "被手改了還放行")
                self.assertIn("少了", stale[0]["detail"], "紅了要說少了哪些")
            finally:
                self.main.GITATTRIBUTES_PATH = keep

    # [VRN-ID] VRN-TST005-FNC146 · LOGIC
    def _fixture(self, tmp, filename, mine, theirs):
        """兩條分支各改同一個檔，帶著真的 `.gitattributes` 做一次真的 git merge。"""
        root = Path(tmp)
        # [VRN-ID] VRN-TST005-FNC147 · LOGIC
        def git(*a):
            return subprocess.run(["git", *a], cwd=str(root), capture_output=True, text=True,
                                  encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL, timeout=120)
        git("init", "-q", "-b", "mine", ".")
        git("config", "user.email", "t@example.invalid")
        git("config", "user.name", "t")
        (root / "ssot").mkdir(exist_ok=True)
        (root / ".gitattributes").write_text(self.main.def_build_gitattributes(), encoding="utf-8")
        (root / filename).write_text('{"base": 1}\n' if filename.endswith(".json") else "base\n", encoding="utf-8")
        git("add", "-A"); git("commit", "-qm", "base")
        git("switch", "-qc", "theirs")
        (root / filename).write_text(theirs, encoding="utf-8")
        git("commit", "-qam", "theirs")
        git("switch", "-q", "mine")
        (root / filename).write_text(mine, encoding="utf-8")
        git("commit", "-qam", "mine")
        git("merge", "theirs")
        stuck = [x for x in git("diff", "--name-only", "--diff-filter=U").stdout.splitlines() if x.strip()]
        return (root / filename).read_text(encoding="utf-8"), stuck

    # [VRN-ID] VRN-TST005-FNC148 · TEST
    def test_a_declared_book_never_gets_conflict_markers_in_it(self):
        """每輪重生的冊，合併之後必須還是合法 JSON —— 但路徑照樣算衝突，不准安靜選掉。"""
        book = "ssot/VRN_REGEX_SSOT_v0100.json"
        self.assertIn(book, self.main.def_generated_paths(), "這條測試挑的檔要在宣告上")
        with tempfile.TemporaryDirectory() as tmp:
            text, stuck = self._fixture(tmp, book, '{"mine": 1}\n', '{"theirs": 1}\n')
        self.assertNotIn("<<<<<<<", text, "衝突標記被寫進 JSON 冊裡了")
        json.loads(text)                                   # 不是合法 JSON 就直接丟例外
        self.assertEqual(stuck, [book], "路徑要照樣算衝突：重生過才算解掉，不是安靜取一邊")

    # [VRN-ID] VRN-TST005-FNC149 · TEST
    def test_an_undeclared_file_still_stops_for_a_human(self):
        """沒宣告的檔（原始碼、測試、手寫的冊）照 git 原本的規矩走 —— 不准被一起關掉。"""
        src = "engine/VRN_TitleTrim_v0100.py"
        self.assertNotIn(src, self.main.def_generated_paths(), "原始碼不該在重生清單上")
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "engine").mkdir(parents=True, exist_ok=True)
            text, stuck = self._fixture(tmp, src, "x = 1\n", "x = 2\n")
        self.assertIn("<<<<<<<", text, "沒宣告的檔應該照常留衝突標記給人看")
        self.assertEqual(stuck, [src])

    # [VRN-ID] VRN-TST005-FNC150 · TEST
    def test_the_append_only_log_keeps_both_sides(self):
        """只往後加的日誌：兩邊的輪次都要留，一行都不准掉。"""
        log = self.main.MERGE_UNION_FILES[0]
        with tempfile.TemporaryDirectory() as tmp:
            text, stuck = self._fixture(tmp, log, "base\n## 我這邊這一輪\n", "base\n## 他那邊那一輪\n")
        self.assertIn("我這邊這一輪", text)
        self.assertIn("他那邊那一輪", text)
        self.assertEqual(stuck, [], "union 併得起來就不該還卡著")

    # [VRN-ID] VRN-TST005-FNC153 · TEST
    def test_the_paths_merge_compares_are_the_ones_git_prints(self):
        """git 回報衝突時給的是**相對倉根**的路徑；宣告給的是相對 VRN 根的。

        這條是自己踩過才加的：第一版拿 `def_rel(VRN_ROOT)` 當前綴，算出來是 `"."`，
        於是每一個重生檔都被判成「要人判」—— 方向安全，可是指令整個沒用。
        所以不比字串長相，直接拿 `git ls-files` 問倉：換算出來的每一條都要真的是被追蹤的檔。
        """
        root = self.main.def_repo_root(self.main.VRN_ROOT)
        self.assertIsNotNone(root, "這條測試要在 git 工作樹裡跑")
        tracked = set(subprocess.run(["git", "ls-files"], cwd=str(root), capture_output=True,
                                     text=True, encoding="utf-8", timeout=120).stdout.splitlines())
        self.assertGreater(len(tracked), 100, "git ls-files 讀不到東西：這條測試自己壞了")
        translated = self.main.def_generated_paths_from(root)
        self.assertEqual(len(translated), len(self.main.def_generated_paths()))
        missing = [path for path in translated if path not in tracked]
        self.assertEqual(missing, [], f"換算出來的路徑 git 不認得：{missing}")

    # [VRN-ID] VRN-TST005-FNC151 · TEST
    def test_merge_refuses_to_guess_on_anything_it_did_not_declare(self):
        """`merge` 的分工要寫在碼裡：髒樹不併、沒宣告的衝突一律停、重生不是取一邊。"""
        body = Path(self.main.__file__).read_text(encoding="utf-8")
        body = body.split("def def_cmd_merge", 1)[1].split("\ndef ", 1)[0]
        self.assertIn("沒提交的改動", body, "髒樹要拒絕")
        self.assertIn("def_generated_paths_from(root)", body, "重生清單要從同一份宣告來，不准另抄一份")
        self.assertIn("def_cmd_build()", body, "機器重生的檔要真的重生")
        self.assertIn("def_cmd_lock(", body, "引擎鎖那一本也要重生")
        self.assertIn("_all_check()", body, "提交前要用 check 同一套判準，不自己再寫一套")
        self.assertIn("這支不猜", body, "沒宣告的衝突要停下來交給人")

    # [VRN-ID] VRN-TST005-FNC152 · TEST
    def test_merge_does_nothing_without_apply(self):
        """預設空跑 —— 跟 sync 同一個規矩：一個管寫入、一個管連網。"""
        done = run_main(["merge", "--help"])
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertIn("--apply", done.stdout)
        parser_src = Path(self.main.__file__).read_text(encoding="utf-8")
        parser_src = parser_src.split('sub.add_parser("merge"', 1)[1].split("p_sync", 1)[0]
        self.assertIn('"--apply", action="store_true"', parser_src, "--apply 不准預設開著")
