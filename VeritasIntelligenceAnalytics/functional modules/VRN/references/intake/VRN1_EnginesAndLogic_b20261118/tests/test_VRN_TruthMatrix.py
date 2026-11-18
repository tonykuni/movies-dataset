#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ===== [VRN:ID:v0100] VRN-TST016 · test_VRN_TruthMatrix · TEST =====
# AST 注入（只加註解，AST 不變）：類別 1 · 函式 6；逐一編號在 ssot/VRN_ID_SSOT_v0100.json
# ===== [VRN:ID:END] =====
"""VRN_TruthMatrix v0100 (operator 2026-10-12, the mother's FirstPageEngine v0113 matrix pasted as known answers): the pasted
table becomes the G11 truth file; what the matrix does not state is `unknown` and G11 does not judge it."""

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


# [VRN-ID] VRN-TST016-FNC001 · IO
def def_load(name, path):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


# [VRN-ID] VRN-TST016-CLS001 · CLASS
class def_TruthMatrixTests(unittest.TestCase):
    # [VRN-ID] VRN-TST016-FNC002 · LOGIC
    @classmethod
    def setUpClass(cls):
        cls.T = def_load("VRN_TruthMatrix_v0100", VRN / "engine" / "VRN_TruthMatrix_v0100.py")

    # [VRN-ID] VRN-TST016-FNC003 · TEST
    def test_selftest(self):
        self.assertEqual(self.T.selftest(verbose=False), 0)

    # [VRN-ID] VRN-TST016-FNC004 · TEST
    def test_the_merged_book_maps_the_mother_s_broker_names(self):
        T = self.T
        book = T.load_record_book()
        self.assertTrue(book, "ssot/VRN_TickerRecord_SSOT_v0100.json")
        for printed, key in (("GOLDMAN", "GS"), ("JPMORGAN", "JPM"), ("MORGANSTANLEY", "MS"), ("MACQUARIE", "MCQ"), ("凱基", "KGI"),
                             ("CITI", "CITI"), ("CLSA", "CLSA"), ("DAIWA", "DAIWA"), ("MEGA", "MEGA"), ("HUANAN", "HUANAN")):
            got, accepted, known = T.lookup_broker_key(printed, book)
            self.assertEqual(got, key, printed)
            self.assertTrue(known and got in accepted, printed)
        got, accepted, _k = T.lookup_broker_key("Morgan Stanley", book)
        self.assertEqual(got, "MS", "the engine book's reading leads; the old book's JPM stays accepted")
        self.assertIn("JPM", accepted)

    # [VRN-ID] VRN-TST016-FNC005 · TEST
    def test_unknown_fields_are_not_judged_by_g11(self):
        T = self.T
        loop = def_load("VRN_AutoTestLoop", VRN / "engine" / "VRN_AutoTestLoop.py")
        rows = {r["file"]: r for r in T.build_truth_rows(T.read_matrix_text(T.sample_text()), T.SAMPLE_BOOK)}
        level = lambda word: {"買進": "BUY", "BUY": "BUY", "中立": "HOLD"}.get(str(word).strip().upper() if word else "", None)  # noqa: E731
        stock = rows["20260101測試證券個股報告-測試公司(1234).pdf"]
        got = {"type": "STOCK", "ticker": "1234", "broker": "MEGA", "denied": False, "page_date": "2026-01-01", "rating": "買進",
               "target_price": 100.0, "current_price": 88.5, "company": "測試公司", "analysts": []}
        hard, _soft, state = loop.def_truth_compare(stock, got, level)
        self.assertEqual(hard, [], "a current price the matrix never had is not a false positive")
        self.assertNotIn("current_price", state)
        self.assertEqual((state["ticker"], state["broker"], state["page_date"], state["rating"], state["target_price"]), ("OK",) * 5)
        gs = rows["GS-5678 20260102.pdf"]
        hard, _soft, state = loop.def_truth_compare(gs, dict(got, ticker="5678", broker="GS", page_date="2026-01-09", rating="中立", target_price=999.0), level)
        self.assertEqual(hard, [], "TP unknown and a date the mother did not verify are not judged")
        self.assertNotIn("page_date", state)
        self.assertNotIn("target_price", state)
        hard, _soft, _state = loop.def_truth_compare(gs, dict(got, ticker="8888", broker="GS", rating="中立"), level)
        self.assertTrue(any(h.startswith("ticker") for h in hard), "the code is vouched for")
        market = rows["測試晨會報告20260104.pdf"]
        hard, _soft, state = loop.def_truth_compare(market, {"type": "MARKET", "ticker": None, "broker": "PRESIDENT", "denied": False,
                                                             "page_date": None, "rating": None, "target_price": 570.0, "current_price": None,
                                                             "company": None, "analysts": []}, level)
        self.assertEqual(state["target_price"], "FALSE_POSITIVE", "a TP on a non-stock report is still a leak")
        plain = {"file": "x.pdf", "report_type": "STOCK", "ticker": "1234", "broker": "MEGA", "page_date": None, "on_page1": {},
                 "rating": None, "target_price": None, "current_price": None, "accept": {}, "company_name": None, "text_layer": True, "analysts": []}
        hard, _soft, state = loop.def_truth_compare(plain, got, level)
        self.assertEqual(state["current_price"], "FALSE_POSITIVE", "a truth row without `unknown` is judged exactly as before")

    # [VRN-ID] VRN-TST016-FNC006 · TEST
    def test_the_truth_file_never_lands_inside_the_tree(self):
        T = self.T
        with self.assertRaises(ValueError):
            T.write_truth_file(VRN / "ssot" / "never.json", [])
        self.assertFalse((VRN / "ssot" / "never.json").exists())


if __name__ == "__main__":
    unittest.main()
