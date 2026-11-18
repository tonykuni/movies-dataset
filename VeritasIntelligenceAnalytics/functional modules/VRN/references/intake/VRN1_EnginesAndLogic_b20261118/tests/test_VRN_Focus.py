#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ===== [VRN:ID:v0100] VRN-TST013 · test_VRN_Focus · TEST =====
# AST 注入（只加註解，AST 不變）：類別 1 · 函式 16；逐一編號在 ssot/VRN_ID_SSOT_v0100.json
# ===== [VRN:ID:END] =====
"""VRN_Focus v0100 (operator 2026-10-11「只擷取個股報告中的FILENAME / 1ST PAGE / 年度財報頁進行處理 其他多餘的」): non-stock files
are not processed; a stock report keeps page 1 and its annual financial pages; the focus copy is the same text and the same bytes
every time; the original is only read; page numbers go back to the original's."""

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
import sys
import tempfile
import unittest
from pathlib import Path

VRN = Path(__file__).resolve().parents[1]


# [VRN-ID] VRN-TST013-FNC001 · IO
def def_load(name, path):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


# [VRN-ID] VRN-TST013-FNC002 · LOGIC
def def_has(name):
    return importlib.util.find_spec(name) is not None


# [VRN-ID] VRN-TST013-CLS001 · CLASS
class def_FocusTests(unittest.TestCase):
    # [VRN-ID] VRN-TST013-FNC003 · LOGIC
    @classmethod
    def setUpClass(cls):
        cls.F = def_load("VRN_Focus_v0100", VRN / "engine" / "VRN_Focus_v0100.py")

    # [VRN-ID] VRN-TST013-FNC013 · LOGIC
    def _corpus(self, tmp, n=6):
        """幾份小 PDF —— 兩條路要比的是同一批輸入。"""
        if not def_has("fitz"):
            self.skipTest("pymupdf missing")
        import fitz
        src = Path(tmp) / "in"
        src.mkdir()
        for i in range(n):
            d = fitz.open()
            for page_no in range(3):
                pg = d.new_page()
                pg.insert_text((50, 100), f"report {i} page {page_no}", fontsize=11)
            d.save(src / f"凱基_2330台積電_2026090{i}_公司更新.pdf")
            d.close()
        return src

    # [VRN-ID] VRN-TST013-FNC014 · TEST
    def test_worker_lane_and_in_process_lane_give_the_same_answer(self):
        """優化只准讓它變快,不准讓它換答案 —— 判讀逐檔相同,聚焦副本逐檔 SHA-256 相同。"""
        import hashlib
        import os
        fields = ("file", "kept", "process", "mode", "keep", "doc_class", "pages_total", "untouched")
        with tempfile.TemporaryDirectory() as tmp:
            src = self._corpus(tmp)
            items = [(q, q.name) for q in sorted(src.iterdir())]

            # [VRN-ID] VRN-TST013-FNC015 · LOGIC
            def run(folder, inproc):
                keep = os.environ.get("VRN_FOCUS_INPROC")
                os.environ["VRN_FOCUS_INPROC"] = "1" if inproc else "0"
                try:
                    return self.F.build(items, Path(tmp) / folder)
                finally:
                    os.environ.pop("VRN_FOCUS_INPROC", None)
                    if keep is not None:
                        os.environ["VRN_FOCUS_INPROC"] = keep

            seq, par = run("seq", True), run("par", False)

            # [VRN-ID] VRN-TST013-FNC016 · LOGIC
            def tree(folder):
                d = Path(tmp) / folder
                return {q.relative_to(d).as_posix(): hashlib.sha256(q.read_bytes()).hexdigest()
                        for q in sorted(d.rglob("*")) if q.is_file()}
            self.assertEqual(tree("seq"), tree("par"),
                             "every focus copy must be byte-identical, not just the manifest")
        self.assertEqual(seq.get("lane"), "sequential", seq.get("lane"))
        self.assertEqual(par.get("lane"), "worker_process", par.get("lane"))
        self.assertEqual(par.get("failed_chunks"), 0, "a chunk that died would be redone in-process and must be reported")
        self.assertEqual([{k: f.get(k) for k in fields} for f in seq["files"]],
                         [{k: f.get(k) for k in fields} for f in par["files"]],
                         "the worker lane must not change a single judgement")
        self.assertEqual(seq["counts"], par["counts"])

    # [VRN-ID] VRN-TST013-FNC017 · TEST
    def test_a_tiny_batch_stays_in_process(self):
        """只有兩份就開子行程,開銷比省下來的多 —— 門檻要守住。"""
        with tempfile.TemporaryDirectory() as tmp:
            src = self._corpus(tmp, n=2)
            man = self.F.build([(q, q.name) for q in sorted(src.iterdir())], Path(tmp) / "out")
        self.assertEqual(man.get("lane"), "sequential")

    # [VRN-ID] VRN-TST013-FNC004 · TEST
    def test_annual_page_is_read_from_the_page_text(self):
        annual = "損益表(NT$百萬元)\n2024A\n2025E\n2026E\n營業收入\n1,000\n1,200\n1,500\n營業成本\n600\n696\n840\n營業毛利\n400\n504\n660\n每股盈餘(元)\n8.0\n10.4\n14.4"
        self.assertTrue(self.F.page_kind(annual)["annual"])
        quarter = "季營收(NT$十億元)\n1Q26\n2Q26\n3Q26\n4Q26\n2026\n營業收入\n800\n900\n950\n1,050\n3,700"
        self.assertFalse(self.F.page_kind(quarter)["annual"], "quarters are not an annual financial page")
        body = "先進製程與先進封裝需求延續，2025 年與 2026 年營收成長動能明確，毛利率可望維持在高檔。" * 6
        self.assertFalse(self.F.page_kind(body)["annual"], "body text that mentions years is not a financial page")

    # [VRN-ID] VRN-TST013-FNC008 · TEST
    def test_a_report_with_no_annual_page_says_what_it_saw(self):
        gs = "Key data\nDec FYE\n12/24\n12/25E\n12/26E\nRevenue (NT$ mn)\n1,000\n1,200\n1,500\nEPS (NT$)\n8.0\n10.4\n14.4\nNet income\n200\n260\n360\nEBITDA\n300\n360\n450"
        self.assertTrue(self.F.page_kind(gs)["annual"], "12/24 · 12/25E · 12/26E are fiscal years")
        odd = self.F.page_kind("FYE Mar-25\nSales\n100\n200\nWeird label\n3\n4")
        self.assertIn("Mar-25", odd["unparsed_periods"])
        self.assertIn("Weird label", odd["unmapped_labels"])

    # [VRN-ID] VRN-TST013-FNC009 · TEST
    def test_each_doc_class_has_its_own_policy(self):
        """2026-10-15：非個股不再一律丟掉，每一類各有自己的處理路徑（冊說了算，不是程式寫死）。"""
        focus, _annual = self.F.rules()
        want = {"STOCK": ("FULL", "ONE_PER_REPORT"),
                "INDUSTRY_OUTLOOK": ("COVERAGE", "ONE_PER_COVERED_COMPANY"),
                "NEWS_DIGEST": ("REGISTER", "ONE_PER_REPORT"),
                "OTHER_INVEST": ("REGISTER", "ONE_PER_REPORT"),
                "OTHER": ("REGISTER", "ONE_PER_REPORT")}
        for cls, (process, rows) in want.items():
            rule = self.F.class_policy(focus, cls)
            self.assertEqual((rule["process"], rule["rows"]), (process, rows), cls)
        unseen = self.F.class_policy(focus, "A_CLASS_NOBODY_HAS_SEEN")
        self.assertEqual(unseen["process"], "REGISTER", "沒見過的類別要登錄下來，不是靜靜丟掉")

    # [VRN-ID] VRN-TST013-FNC010 · TEST
    def test_policy_falls_back_to_the_old_scope_when_the_book_says_nothing(self):
        """冊裡沒有 doc_class_policy 時退回 2026-10-11 G19 的舊範圍 —— 不是全部放行。"""
        self.assertEqual(self.F.class_policy({}, "STOCK")["process"], "FULL")
        self.assertEqual(self.F.class_policy({}, "INDUSTRY_OUTLOOK")["process"], "SKIP")

    # [VRN-ID] VRN-TST013-FNC006 · TEST
    def test_page_numbers_go_back_to_the_original(self):
        row = {"page_map": {"1": 1, "2": 7, "3": 8}}
        self.assertEqual([self.F.original_page(row, p) for p in (1, 2, 3, None)], [1, 7, 8, None])
        self.assertEqual(self.F.original_page({"page_map": {}}, 4), 4, "a whole copy keeps its page numbers")

    # [VRN-ID] VRN-TST013-FNC011 · TEST
    @unittest.skipUnless(def_has("fitz"), "PyMuPDF not installed")
    def test_industry_report_lists_every_covered_company(self):
        """產業報告涵蓋多家：代號與名稱都要抽出來，內文的年份不得被當成代號。"""
        import fitz  # type: ignore
        pages = [["元大證券投資顧問  半導體產業展望", "受評公司一覽",
                  "台積電 (2330)   買進   目標價 1,200", "聯發科 (2454)   區間操作", "聯電 (2303)   中立"],
                 ["個別公司評論", "日月光投控 (3711) 先進封裝產能滿載。",
                  "本頁提及 2026 年與 2025 年展望，並非代號。"],
                 ["免責聲明：本報告僅供參考，不構成投資建議。"]]
        with tempfile.TemporaryDirectory(prefix="vrn-coverage-") as tmp:
            path = Path(tmp) / "元大_半導體產業_20260901_產業報告.pdf"
            doc = fitz.open()
            for lines in pages:
                page = doc.new_page()
                for i, line in enumerate(lines):
                    page.insert_text((60, 80 + 22 * i), line, fontname="china-t", fontsize=11)
            doc.save(str(path))
            doc.close()
            got = self.F.plan(path, path.name)
        self.assertEqual((got["doc_class"], got["process"], got["rows"]),
                         ("INDUSTRY_OUTLOOK", "COVERAGE", "ONE_PER_COVERED_COMPANY"))
        self.assertTrue(got["kept"], "產業報告現在要處理")
        tickers = [c["ticker"] for c in got["covered"]]
        self.assertEqual(sorted(tickers), ["2303", "2330", "2454", "3711"])
        self.assertNotIn("2026", tickers, "內文的年份不是代號")
        self.assertNotIn("2025", tickers, "內文的年份不是代號")
        names = {c["ticker"]: c["name_on_page"] for c in got["covered"]}
        self.assertEqual(names["2330"], "台積電")
        self.assertEqual(got["keep"], [1, 2], "免責聲明那一頁沒有代號，不留")

    # [VRN-ID] VRN-TST013-FNC012 · TEST
    @unittest.skipUnless(def_has("fitz"), "PyMuPDF not installed")
    def test_register_only_classes_keep_just_the_first_page(self):
        """其他投資報告：只分類登錄，留首頁取後設資料，不抽財務。"""
        import fitz  # type: ignore
        with tempfile.TemporaryDirectory(prefix="vrn-register-") as tmp:
            path = Path(tmp) / "凱基_台股晨報_20260310.pdf"
            doc = fitz.open()
            for n in range(3):
                page = doc.new_page()
                page.insert_text((60, 80), f"台股晨報 第 {n + 1} 頁", fontname="china-t", fontsize=11)
            doc.save(str(path))
            doc.close()
            got = self.F.plan(path, path.name)
        self.assertEqual((got["doc_class"], got["process"]), ("NEWS_DIGEST", "REGISTER"))
        self.assertTrue(got["kept"])
        self.assertEqual(got["keep"], [1], "只留首頁")
        self.assertEqual(got["covered"], [], "REGISTER 不抽受評公司")

    # [VRN-ID] VRN-TST013-FNC007 · TEST
    @unittest.skipUnless(def_has("fitz"), "PyMuPDF not installed")
    def test_known_answers(self):
        rc, rows = self.F.selftest(verbose=False)
        self.assertEqual([(i, d) for i, ok, d in rows if not ok], [])
        self.assertEqual(rc, 0)


if __name__ == "__main__":
    unittest.main()
