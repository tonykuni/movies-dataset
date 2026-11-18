#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ===== [VRN:ID:v0100] VRN-TST017 · test_VRN_RunCache · TEST =====
# AST 注入（只加註解，AST 不變）：類別 3 · 函式 17；逐一編號在 ssot/VRN_ID_SSOT_v0100.json
# ===== [VRN:ID:END] =====
"""VRN_RunCache v0100 (operator 2026-10-13「過去跑過的資料在輸入還沒換之前不要刪除 TEMP 避免重跑」): what a run read is used again
while its inputs (file bytes, engine code, the books it reads, library versions) are the same; nothing stale is ever served."""

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
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

VRN = Path(__file__).resolve().parents[1]


# [VRN-ID] VRN-TST017-FNC001 · IO
def def_load(name, path):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


# [VRN-ID] VRN-TST017-CLS001 · CLASS
class def_RunCacheTests(unittest.TestCase):
    # [VRN-ID] VRN-TST017-FNC002 · LOGIC
    @classmethod
    def setUpClass(cls):
        cls.C = def_load("VRN_RunCache_v0100", VRN / "engine" / "VRN_RunCache_v0100.py")

    # [VRN-ID] VRN-TST017-FNC003 · TEST
    def test_selftest(self):
        self.assertEqual(self.C.selftest(verbose=False), 0)

    # [VRN-ID] VRN-TST017-FNC008 · LOGIC
    def _res(self, **env):
        """在乾淨的環境變數下取一次資源預算。"""
        import os
        keys = ("VIA_VRN_WORKERS", "VIA_VRN_WORKER_GB", "VIA_VRN_WORKERS_MAX",
                "VIA_CACHE_SHARE", "VIA_CACHE_MAX_GB")
        old = {k: os.environ.get(k) for k in keys}
        for k in keys:
            os.environ.pop(k, None)
        os.environ.update({k: str(v) for k, v in env.items()})
        try:
            return self.C.cache_resources()
        finally:
            for k, v in old.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v

    # [VRN-ID] VRN-TST017-FNC009 · TEST
    def test_the_budget_says_which_limit_is_holding_it_back(self):
        """操作員問「記憶體不夠怎麼辦」，第一步是讓他看得到現在卡在哪一項 —— 不然調哪個旋鈕都是猜的。"""
        tight = self._res(VIA_VRN_WORKER_GB=4096)       # 每支要 4 TB：記憶體一定先到頂
        self.assertEqual(tight["workers"], 1)
        self.assertEqual(tight["bottleneck"], "記憶體")
        self.assertIn("記憶體", tight["why"])
        capped = self._res(VIA_VRN_WORKERS_MAX=1)
        self.assertEqual(capped["workers"], 1)
        self.assertEqual(capped["bottleneck"], "上限")

    # [VRN-ID] VRN-TST017-FNC010 · TEST
    def test_the_operator_can_override_the_worker_count_and_the_temp_share(self):
        forced = self._res(VIA_VRN_WORKERS=2)
        self.assertEqual(forced["workers"], 2)
        self.assertIn("VIA_VRN_WORKERS", forced["bottleneck"])
        base, wide = self._res(), self._res(VIA_CACHE_SHARE=0.9)
        self.assertGreaterEqual(wide["budget_gb"], base["budget_gb"],
                                "TEMP 佔比調高，快取上限不該變小")

    # [VRN-ID] VRN-TST017-FNC011 · TEST
    def test_a_bad_environment_value_is_ignored_instead_of_breaking_the_run(self):
        """打錯一個環境變數不該讓整輪跑不動 —— 讀不懂就當沒設,超出範圍就夾住。"""
        base = self._res()
        for bad in ("abc", "", "nan", "inf", "-1"):
            with self.subTest(value=bad):
                got = self._res(VIA_VRN_WORKER_GB=bad)
                self.assertGreaterEqual(got["workers"], 1)
                self.assertIsInstance(got["budget_gb"], float)
        self.assertEqual(self._res(VIA_VRN_WORKER_GB="abc")["workers"], base["workers"],
                         "讀不懂的值要退回預設,不是變成另一個數字")

    # [VRN-ID] VRN-TST017-FNC012 · TEST
    def test_no_environment_variable_means_the_old_numbers(self):
        """預設不可以變:沒設任何旋鈕時,預算要和加旋鈕之前算出來的一樣。"""
        import os
        r = self._res()
        cpu = os.cpu_count() or 1
        self.assertEqual(r["by_cpu"], cpu - 1 if cpu > 2 else cpu, "仍然留一核")
        self.assertEqual(r["ceiling"], 8, "上限仍然是 8")
        self.assertEqual(r["per_worker_gb"], 0.6, "每支子行程仍然假設 0.6 GB")
        self.assertEqual(r["workers"], max(1, min(r["by_cpu"], r["by_mem"], 8)))

    # [VRN-ID] VRN-TST017-FNC004 · TEST
    def test_each_step_depends_on_what_it_reads(self):
        C = self.C
        for step in ("batch", "first_page", "regions"):
            data = C.cache_data_files(step)
            for generated in C.DATA_NOT_READ:
                self.assertNotIn(generated, data, step)
            self.assertIn("ssot/VRN_Method_SSOT_v0100.json", data, "a book the step does not name is still counted (slower, never stale)")
        for step in ("batch", "first_page"):            # ENG002 / FPE 真的沒開 TitleTrim 冊
            self.assertNotIn("ssot/VRN_TitleTrim_SSOT_v0100.json", C.cache_data_files(step), step)
        # 2026-10-20：這一行原本也要求 regions 跳過 TitleTrim 冊 —— 那是把缺陷寫進測試。
        # PageRegions 的 focus_book() 讀的就是它（doc_class_policy 決定 FULL／COVERAGE／REGISTER／SKIP）。
        self.assertIn("ssot/VRN_TitleTrim_SSOT_v0100.json", C.cache_data_files("regions"),
                      "PageRegions 讀這本,鑰匙就要蓋住它")
        self.assertIn("engine/VRN_TitleTrim_v0100.py", C.cache_code_files("focus"), "focus uses TitleTrim's trim()")
        self.assertIn("engine/mother/VRN_ENG394_LayoutRestore_v0100.py", C.cache_code_files("regions"))
        for rel in C.cache_code_files("batch") + C.cache_code_files("first_page"):
            self.assertTrue((VRN / rel).is_file(), rel)

    # [VRN-ID] VRN-TST017-FNC005 · TEST
    def test_a_windows_path_is_rewritten_in_every_form(self):
        forms = self.C.cache_path_forms(r"C:\Users\op\AppData\Local\VRN_Main\20261013T003019\autotest\round1\vrn_db")
        self.assertIn(r"C:\\Users\\op\\AppData\\Local\\VRN_Main\\20261013T003019\\autotest\\round1\\vrn_db", forms, "JSON-escaped")
        self.assertIn("C:/Users/op/AppData/Local/VRN_Main/20261013T003019/autotest/round1/vrn_db", forms)

    # [VRN-ID] VRN-TST017-FNC006 · TEST
    def test_the_loop_reuses_the_database_folder_only_while_its_inputs_are_the_same(self):
        C = self.C
        loop = def_load("vrn_autotest_loop_cache_test", VRN / "engine" / "VRN_AutoTestLoop.py")

        # [VRN-ID] VRN-TST017-CLS002 · CLASS
        class FakeDb:
            calls = 0

            # [VRN-ID] VRN-TST017-FNC007 · LOGIC
            def process_batch(self, args):
                FakeDb.calls += 1
                out = Path(args.output)
                out.mkdir(parents=True, exist_ok=True)
                (out / "summary.json").write_text(json.dumps({"output": str(out), "input": args.input}), encoding="utf-8")
                return {"output": str(out), "files": len(list(Path(args.input).iterdir()))}
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            src = td / "focus"
            src.mkdir()
            (src / "a.pdf").write_bytes(b"%PDF-1 a")
            cache = C.RunCache(td / "cache")
            loop.RUN_CACHE = cache
            try:
                args = lambda run: argparse.Namespace(input=str(src), output=str(td / run / "vrn_db"), run_id="R1", csv=True)  # noqa: E731
                first = loop.def_process_batch(FakeDb(), args("run1"), "G06")
                second = loop.def_process_batch(FakeDb(), args("run2"), "G06")
                self.assertEqual(FakeDb.calls, 1, "same input files, same engine: not read again")
                self.assertEqual(second["output"], str(td / "run2" / "vrn_db"), "the old run's path became this run's")
                saved = (td / "run2" / "vrn_db" / "summary.json").read_text(encoding="utf-8")
                self.assertEqual(json.loads(saved)["output"], str(td / "run2" / "vrn_db"), "the path written inside the folder is this run's")
                self.assertNotIn("run1", saved)
                self.assertEqual(first["files"], second["files"])
                (src / "a.pdf").write_bytes(b"%PDF-1 changed")
                loop.def_process_batch(FakeDb(), args("run3"), "G06")
                self.assertEqual(FakeDb.calls, 2, "the input changed: read again")
            finally:
                loop.RUN_CACHE = None
                cache.cache_close()


# [VRN-ID] VRN-TST017-CLS003 · CLASS
class TestTheKeyCoversEveryBookTheStepReads(unittest.TestCase):
    """步驟的答案靠哪些冊，鑰匙就要算進哪些冊 —— 不然改了冊會吃到舊答案。

    實測 2026-10-20：`DATA_NOT_READ_BY["regions"]` 宣告 regions 不讀 `VRN_TitleTrim_SSOT_v0100.json`，
    但 `VRN_PageRegions_v0100.py` 的 `focus_book()` 讀的就是它 —— 而那裡住著 `doc_class_policy`，
    決定一份報告走 FULL／COVERAGE／REGISTER／SKIP，也就是**到底要不要處理**。
    把 INDUSTRY_OUTLOOK 從 COVERAGE 改成 SKIP：focus 的鑰匙變了，**regions 的一個字沒變**。
    """

    # [VRN-ID] VRN-TST017-FNC013 · LOGIC
    @classmethod
    def setUpClass(cls):
        cls.C = def_load("VRN_RunCache_v0100", VRN / "engine" / "VRN_RunCache_v0100.py")

    # 唯一的例外，而且寫清楚為什麼：`focus` 的程式碼裡（TitleTrim 的 `_domain_broker`）提到合併冊，
    # 但 focus 快取裝的是「留哪幾頁」的清冊，那條路不會叫 `_domain_broker`；合併冊每輪 build 都重生，
    # 算進去等於每輪必失。真要改成算進去，請連同這一行的理由一起改掉。
    ALLOWED = {("focus", "ssot/VRN_TickerRecord_SSOT_v0100.json")}

    # [VRN-ID] VRN-TST017-FNC014 · LOGIC
    def def_key(self, step):
        return self.C.RunCache(home=str(Path(tempfile.gettempdir()) / "vrn_key_probe")).cache_step_parts(step)

    # [VRN-ID] VRN-TST017-FNC015 · TEST
    def test_editing_the_routing_policy_moves_the_keys_of_the_steps_that_read_it(self):
        """實測型守門：真的改冊、真的比鑰匙，不是讀宣告。"""
        book = VRN / "ssot" / "VRN_TitleTrim_SSOT_v0100.json"
        kept = book.read_text(encoding="utf-8")
        before = {s: self.def_key(s) for s in ("focus", "batch", "first_page", "regions")}
        try:
            data = json.loads(kept)
            data["focus"]["doc_class_policy"]["INDUSTRY_OUTLOOK"]["process"] = "SKIP"
            book.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
            after = {s: self.def_key(s) for s in before}
        finally:
            book.write_text(kept, encoding="utf-8")
        for step in ("focus", "regions"):
            self.assertNotEqual(before[step], after[step], f"{step} 讀這本冊，鑰匙卻沒跟著變：改冊會吃到舊答案")
        for step in ("batch", "first_page"):
            self.assertEqual(before[step], after[step], f"{step} 沒讀這本冊，不該被連帶失效")

    # [VRN-ID] VRN-TST017-FNC016 · TEST
    def test_no_step_skips_a_file_its_own_code_actually_opens(self):
        """掃原始碼：宣告「沒讀」的檔，不准出現在這個步驟程式碼的字串常數裡（註解與 docstring 不算）。"""
        root = VRN
        # [VRN-ID] VRN-TST017-FNC017 · LOGIC
        def def_literals(rel):
            try:
                tree = ast.parse((root / rel).read_text(encoding="utf-8", errors="replace"))
            except Exception:                                  # noqa: BLE001
                return set()
            docs = {ast.get_docstring(n, clean=False) for n in ast.walk(tree)
                    if isinstance(n, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))}
            return {n.value for n in ast.walk(tree)
                    if isinstance(n, ast.Constant) and isinstance(n.value, str) and n.value not in docs}
        for step in ("focus", "batch", "first_page", "regions"):
            lits = set()
            for rel in self.C.cache_code_files(step):
                if (root / rel).is_file():
                    lits |= def_literals(rel)
            skipped = self.C.DATA_NOT_READ | self.C.DATA_NOT_READ_BY.get(step, set())
            liars = [f for f in sorted(skipped) if Path(f).name in lits and (step, f) not in self.ALLOWED]
            self.assertEqual(liars, [], f"{step} 說沒讀，程式碼卻拿這些檔名當字串用：{liars}")


if __name__ == "__main__":
    unittest.main()
