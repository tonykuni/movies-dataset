#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ===== [VRN:ID:v0100] VRN-TST018 · test_VRN_Ocr · TEST =====
# AST 注入（只加註解，AST 不變）：類別 7 · 函式 21；逐一編號在 ssot/VRN_ID_SSOT_v0100.json
# ===== [VRN:ID:END] =====
"""VRN_Ocr v0100：Codex PR #62 那三條 P1 的回歸測試。

三條都是「上一版自以為接好了，其實沒有」：

P1-1  訊息說「OCR 已接」，但沒有任何地方真的呼叫 read() —— 換句話說只換了一句台詞。
P1-2  selftest 裡 import pymupdf 沒包起來，裝了 rapidocr 卻沒 pymupdf 的機器會整輪倒掉。
P1-3  get_textpage_ocr() 不給 language 預設 eng，中文讀出來是整段錯字；
      而且對影像檔不給 full=True 會直接丟 RuntimeError，一個字都讀不到。
"""

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
import unittest
from pathlib import Path

VRN = Path(__file__).resolve().parents[1]


# [VRN-ID] VRN-TST018-FNC001 · IO
def def_load(name, path):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


OCR = def_load("vrn_ocr_under_test", VRN / "engine" / "VRN_Ocr_v0100.py")
LOOP = def_load("vrn_loop_under_test", VRN / "engine" / "VRN_AutoTestLoop.py")


# [VRN-ID] VRN-TST018-CLS001 · CLASS
class def_OcrContractTests(unittest.TestCase):
    # [VRN-ID] VRN-TST018-FNC002 · TEST
    def test_result_is_always_tagged_as_ocr(self):
        """不管讀成功還失敗，source=OCR 與 lossy_cjk=True 都要在 —— 下游靠這兩個欄位決定不信它。"""
        for got in (OCR.read("/does/not/exist.png"), OCR.read(__file__)):
            self.assertEqual(got["source"], "OCR")
            self.assertIs(got["lossy_cjk"], True)

    # [VRN-ID] VRN-TST018-FNC003 · TEST
    def test_unreadable_file_returns_error_instead_of_raising(self):
        got = OCR.read("/does/not/exist.png")
        self.assertIsInstance(got.get("error"), str)
        self.assertTrue(got["error"])

    # [VRN-ID] VRN-TST018-FNC004 · TEST
    def test_tesseract_language_includes_the_chinese_pack_when_present(self):
        """P1-3：有 chi_tra 就要叫 chi_tra+eng。不指定語言，中文讀出來是整段錯字而不是掉字。"""
        saved = OCR._TESS_LANGS
        try:
            OCR._TESS_LANGS = ["chi_tra", "eng", "osd"]
            self.assertEqual(OCR.def_tess_lang(), "chi_tra+eng")
            self.assertTrue(OCR.available()["cjk"] or not OCR.shutil.which("tesseract"))
            OCR._TESS_LANGS = ["eng", "osd"]
            self.assertEqual(OCR.def_tess_lang(), "eng")
        finally:
            OCR._TESS_LANGS = saved

    # [VRN-ID] VRN-TST018-FNC020 · TEST
    def test_a_cjk_capable_backend_wins_over_an_english_only_tesseract(self):
        """P2-2：這個系統讀的是台股中文報告。沒有中文語言包的 Tesseract 讀中文是整段錯字
        （「6MB( 2330 / Simanaeia / HAS」），那不是降級是垃圾 ——
        同一台機器上還裝著自帶中文的 rapidocr，就該挑它。"""
        saved_langs, saved_which, saved_have = OCR._TESS_LANGS, OCR.shutil.which, OCR.def_have
        try:
            OCR._TESS_LANGS = ["eng", "osd"]                       # Tesseract 在，但沒有中文包
            OCR.shutil.which = lambda _n: "/usr/bin/tesseract"
            OCR.def_have = lambda name: True                       # pymupdf 與 rapidocr 都在
            av = OCR.available()
            self.assertEqual(av["engine"], "rapidocr", av["why"])
            self.assertTrue(av["cjk"])
            self.assertIn("讀不了中文", av["why"])

            OCR._TESS_LANGS = ["chi_tra", "eng"]                   # 有中文包就不用讓位
            self.assertEqual(OCR.available()["engine"], "pymupdf-tesseract")

            OCR._TESS_LANGS = ["eng"]                              # 三支都讀不了中文時照實說
            OCR.def_have = lambda name: name != "rapidocr_onnxruntime"
            av = OCR.available()
            self.assertEqual(av["engine"], "pymupdf-tesseract")
            self.assertFalse(av["cjk"])
            self.assertIn("只好用它", av["why"])
        finally:
            OCR._TESS_LANGS, OCR.shutil.which, OCR.def_have = saved_langs, saved_which, saved_have

    # [VRN-ID] VRN-TST018-FNC005 · TEST
    def test_a_known_image_really_comes_back_as_text(self):
        """P1-3 的另一半、也是整條的重點：真的畫一張已知圖、真的讀回來。

        影像檔不給 full=True 會丟「source or target not a PDF」—— 而那個例外被 read() 吞掉，
        看起來只是「讀到空的」。所以這裡不看原始碼有沒有寫 full=True，看讀不讀得回字。
        沒有引擎的機器走另一條：那就要回「沒有可用的 OCR 引擎」，一樣是斷言，不是跳過。
        """
        import tempfile
        if not OCR.available()["engine"]:
            self.assertEqual(OCR.read(__file__)["error"], "沒有可用的 OCR 引擎")
            return
        with tempfile.TemporaryDirectory(prefix="vrn_ocr_test_") as td:
            got = OCR.read(OCR.def_known_image(Path(td)))
        self.assertFalse(got["error"], got["error"])
        joined = got["text"].replace(" ", "")
        missing = [k for k in OCR.KNOWN_HARD if k.replace(" ", "") not in joined]
        self.assertEqual(missing, [], f"數字與拉丁字沒讀全：{got['text']!r}")
        self.assertGreater(got["chars"], 0)


# [VRN-ID] VRN-TST018-CLS002 · CLASS
class def_OcrDegradationTests(unittest.TestCase):
    """P1-2：環境缺東西是「這台機器驗不到」，不是紅燈，更不該讓整輪倒掉。"""

    # [VRN-ID] VRN-TST018-FNC006 · TEST
    def test_missing_fixture_dependency_is_a_gap_not_a_failure(self):
        saved = OCR.def_known_image
        try:
            # [VRN-ID] VRN-TST018-FNC007 · LOGIC
            def boom(_folder):
                raise ModuleNotFoundError("No module named 'pymupdf'")
            OCR.def_known_image = boom
            checks = OCR.def_checks()
            states = {state for _n, state, _d in checks}
            if OCR.available()["engine"]:
                self.assertIn("GAP", states, "畫不出已知圖要記成 GAP，不能默默跳過")
            self.assertNotIn("FAIL", states, "環境缺件不該判紅 —— 那會讓 lock 因為環境而擋下來")
            self.assertEqual(OCR.selftest(verbose=False), 0)
        finally:
            OCR.def_known_image = saved

    # [VRN-ID] VRN-TST018-FNC021 · TEST
    def test_no_engine_at_all_records_the_unrun_read_as_a_gap(self):
        """P2-1：沒有引擎 ＝ 讀取那一條根本沒跑。不記 GAP，統計會寫「沒驗到 0」，
        而 lock 收到 rc=0 就把 ocr 當成證過了 —— 驗一個沒跑到的東西，等於沒驗。"""
        saved = OCR.def_have
        try:
            OCR.def_have = lambda _name: False
            checks = OCR.def_checks()
            gaps = [n for n, state, _d in checks if state == "GAP"]
            self.assertTrue(gaps, "沒有引擎時要記下「讀取那一條沒跑」，不能讓統計寫成沒驗到 0")
            self.assertTrue(any("沒跑" in n for n in gaps), gaps)
        finally:
            OCR.def_have = saved

    # [VRN-ID] VRN-TST018-FNC008 · TEST
    def test_no_engine_at_all_still_returns_zero(self):
        saved = OCR.def_have
        try:
            OCR.def_have = lambda _name: False
            checks = OCR.def_checks()
            self.assertNotIn("FAIL", {state for _n, state, _d in checks})
            self.assertEqual(OCR.selftest(verbose=False), 0)
        finally:
            OCR.def_have = saved

    # [VRN-ID] VRN-TST018-FNC009 · TEST
    def test_every_check_carries_one_of_the_three_states(self):
        """三態就是三態 —— 多一個狀態 P22 就畫不出來（它用 dict 查表，查不到會 KeyError）。"""
        for name, state, _detail in OCR.def_checks():
            self.assertIn(state, ("PASS", "FAIL", "GAP"), name)


# [VRN-ID] VRN-TST018-CLS003 · CLASS
class def_LoopRoutesImagesThroughOcrTests(unittest.TestCase):
    """P1-1：影像檔要**真的**送進 OCR，不是只把訊息改成「已接」。"""

    # [VRN-ID] VRN-TST018-CLS004 · CLASS
    class _FakeOcr:
        # [VRN-ID] VRN-TST018-FNC010 · INIT
        def __init__(self):
            self.seen = []

        # [VRN-ID] VRN-TST018-FNC011 · LOGIC
        def available(self):
            return {"engine": "fake", "why": "測試用", "checked": [], "cjk": True}

        # [VRN-ID] VRN-TST018-FNC012 · LOGIC
        def read(self, path):
            self.seen.append(path)
            return {"engine": "fake", "lang": "chi_tra+eng", "lines": ["台積電 2330"],
                    "text": "台積電 2330", "chars": 11, "source": "OCR", "lossy_cjk": True, "error": ""}

    # [VRN-ID] VRN-TST018-CLS005 · CLASS
    class _Engines:
        # [VRN-ID] VRN-TST018-FNC013 · INIT
        def __init__(self, ocr):
            self.ocr = ocr
            self.errors = {}

    # [VRN-ID] VRN-TST018-FNC014 · TEST
    def test_the_image_is_actually_read(self):
        fake = self._FakeOcr()
        note = LOOP.def_ocr_note(self._Engines(fake), "/tmp/926708.jpg")
        self.assertEqual(fake.seen, ["/tmp/926708.jpg"], "沒有真的呼叫 read()，那就還是在說謊")
        self.assertIn("11 字", note)
        self.assertIn("台積電 2330", note)

    # [VRN-ID] VRN-TST018-FNC015 · TEST
    def test_the_note_says_the_text_does_not_enter_judgement(self):
        note = LOOP.def_ocr_note(self._Engines(self._FakeOcr()), "/tmp/926708.jpg")
        self.assertIn("不進判讀", note)
        self.assertIn("lossy_cjk", note)

    # [VRN-ID] VRN-TST018-FNC016 · TEST
    def test_absent_engine_is_said_plainly(self):
        # [VRN-ID] VRN-TST018-CLS006 · CLASS
        class _None(self._FakeOcr):
            # [VRN-ID] VRN-TST018-FNC017 · LOGIC
            def available(self):
                return {"engine": "", "why": "三支都不在", "checked": [], "cjk": False}

        note = LOOP.def_ocr_note(self._Engines(_None()), "/tmp/926708.jpg")
        self.assertIn("沒有 OCR 引擎", note)
        self.assertNotIn("讀到", note)

    # [VRN-ID] VRN-TST018-FNC018 · TEST
    def test_a_throwing_engine_does_not_break_the_run(self):
        # [VRN-ID] VRN-TST018-CLS007 · CLASS
        class _Boom(self._FakeOcr):
            # [VRN-ID] VRN-TST018-FNC019 · LOGIC
            def read(self, path):
                raise RuntimeError("壞掉了")

        note = LOOP.def_ocr_note(self._Engines(_Boom()), "/tmp/926708.jpg")
        self.assertIn("RuntimeError", note)


if __name__ == "__main__":
    unittest.main(verbosity=2)
