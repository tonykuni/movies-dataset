#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ===== [VRN:ID:v0100] VRN-TST014 · test_VRN_Matrix · TEST =====
# AST 注入（只加註解，AST 不變）：類別 1 · 函式 7；逐一編號在 ssot/VRN_ID_SSOT_v0100.json
# ===== [VRN:ID:END] =====
"""VRN_Matrix v0100 (operator 2026-10-12「real test and output validated results in matrix by rich for my reviewing」): one row
per stock report, one column per part, value + state + lock; rich when installed, the same text otherwise; CJK widths right."""

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
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

VRN = Path(__file__).resolve().parents[1]


# [VRN-ID] VRN-TST014-FNC001 · IO
def def_load(name, path):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


# [VRN-ID] VRN-TST014-CLS001 · CLASS
class def_MatrixTests(unittest.TestCase):
    # [VRN-ID] VRN-TST014-FNC002 · LOGIC
    @classmethod
    def setUpClass(cls):
        cls.M = def_load("VRN_Matrix_v0100", VRN / "engine" / "VRN_Matrix_v0100.py")

    # [VRN-ID] VRN-TST014-FNC003 · TEST
    def test_selftest(self):
        self.assertEqual(self.M.selftest(verbose=False), 0)

    # [VRN-ID] VRN-TST014-FNC004 · TEST
    def test_widths_and_clipping_are_cjk_aware(self):
        M = self.M
        self.assertEqual((M.text_width("台積電"), M.text_width("TSMC"), M.text_width("台積電 TSMC")), (6, 4, 11))
        self.assertEqual(M.clip_text("泓德能源股份有限公司", 8), "泓德能…")
        self.assertEqual(M.pad_text("台積", 6), "台積  ")

    # [VRN-ID] VRN-TST014-FNC005 · TEST
    def test_a_real_run_folder_renders_and_writes_the_text_copy(self):
        M = self.M
        results = [{"file": "a.pdf", "status": "OK", "parts": [{"part": "title.ticker", "value": "2330", "state": "VERIFIED"},
                                                              {"part": "cover.target_price", "value": 1200.0, "state": "CONFLICT"}]}]
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp) / "20261012T000000"
            (run / "autotest" / "round1" / "titletrim").mkdir(parents=True)
            (run / "autotest" / "round1" / "titletrim" / "VRN_TitleTrim_Results_v0100.json").write_text(json.dumps(results), encoding="utf-8")
            (run / "autotest" / "round1" / "titletrim" / "vrn_lock_status.json").write_text(
                json.dumps([{"file": "a.pdf", "part": "title.ticker", "lock": "HELD"}]), encoding="utf-8")
            buf = io.StringIO()
            got = M.show_report_matrix(run, plain=True, stream=buf)
            self.assertEqual((got["rendered"], got["rows"]), ("plain", 1))
            text = (run / M.OUT_NAME).read_text(encoding="utf-8")
            self.assertIn("2330 ✓鎖", text)
            self.assertIn("1200 ✗", text)
            self.assertNotIn("\x1b[", text, "the file copy carries no colours")
            self.assertIn("[MATRIX-CONSOLE] plain", buf.getvalue())

    # [VRN-ID] VRN-TST014-FNC007 · TEST
    def test_a_derived_part_is_shown_as_derived_not_as_not_printed(self):
        """2026-10-21 第二十三輪：首頁沒印上漲%、VRN 算得出來 → 部位是 DERIVED（推），不是「報告沒印」（–）。

        實測那一輪部位矩陣印「上漲% –59」，而同一輪代號紀錄那一欄 59/59 都是 DERIVED、有值。
        這一條同時守住兩件事：格子要印「推」，而且部位總計那張表要有 DERIVED 這一欄（少了它，
        59 格推算值在總計上整個消失）。
        """
        M = self.M
        model = M.build_report_matrix([{"file": "a.pdf", "status": "OK", "parts": [
            {"part": "title.ticker", "value": "6873", "state": "VERIFIED"},
            {"part": "cover.target_price", "value": 208.0, "state": "VERIFIED"},
            {"part": "cover.current_price", "value": 160.0, "state": "VERIFIED"},
            {"part": "cover.upside", "value": 30.0, "state": "DERIVED", "sources": {"VRN 重算": 30.0}}]}])
        text = "\n".join(M.render_plain(model))
        self.assertIn("30 推", text, "算出來的上漲% 要印成推（DERIVED），不是 –（報告沒印）")
        self.assertIn("推 報告沒印、VRN 算得出來", M.LEGEND, "圖例要解釋得了部位那張表上的推")
        self.assertEqual(model["totals"]["cover.upside"].get("DERIVED"), 1, "部位總計要數得到它")
        self.assertIn("DERIVED", M.TOTAL_STATES_WITH_ANNUAL, "部位總計表要有 DERIVED 這一欄，否則推算值印不出來")

    # [VRN-ID] VRN-TST014-FNC006 · TEST
    def test_rich_is_optional(self):
        """Nothing is installed by VRN: with rich the table is printed by rich, without it the text path is taken."""
        M = self.M
        model = M.build_report_matrix([{"file": "a.pdf", "status": "OK", "parts": [{"part": "title.ticker", "value": "2330", "state": "VERIFIED"}]}])
        if M.table_has_rich():
            self.assertTrue(M.render_rich(model))
        else:
            self.assertFalse(M.render_rich(model))
        self.assertTrue(any("2330 ✓" in l for l in M.render_plain(model)))


if __name__ == "__main__":
    unittest.main()
