#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ===== [VRN:ID:v0100] VRN-TST015 · test_VRN_TickerRecord · TEST =====
# AST 注入（只加註解，AST 不變）：類別 3 · 函式 27；逐一編號在 ssot/VRN_ID_SSOT_v0100.json
# ===== [VRN:ID:END] =====
"""VRN_TickerRecord v0100 (operator 2026-10-12): the 4-digit code as the key, 15 fields per report; one merged book with
provenance, duplicates folded, conflicts shown; the book on disk is never older than its sources."""

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
import json
import pathlib
import time
import sys
import tempfile
import unittest
from pathlib import Path

VRN = Path(__file__).resolve().parents[1]


# [VRN-ID] VRN-TST015-FNC001 · IO
def def_load(name, path):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


# [VRN-ID] VRN-TST015-CLS001 · CLASS
class def_TickerRecordTests(unittest.TestCase):
    # [VRN-ID] VRN-TST015-FNC002 · LOGIC
    @classmethod
    def setUpClass(cls):
        cls.R = def_load("VRN_TickerRecord_v0100", VRN / "engine" / "VRN_TickerRecord_v0100.py")

    # [VRN-ID] VRN-TST015-FNC003 · TEST
    def test_selftest(self):
        self.assertEqual(self.R.selftest(verbose=False), 0)

    # [VRN-ID] VRN-TST015-FNC013 · TEST
    def test_write_book_keeps_the_timestamp_when_nothing_changed(self):
        """重跑 build 不該只因為跑過就換 `generated`。

        舊行為每跑一次 build 就蓋一個新時間戳,同一個 v0100 檔名在 GitHub 與本機
        之間內容就不同,治理閘判成「版本號衝突(同名不同內容)」,但實質內容一樣。
        """
        R = self.R
        with tempfile.TemporaryDirectory() as box:
            book_path = pathlib.Path(box) / "VRN_TickerRecord_SSOT_v0100.json"
            R.write_book(book_path)
            first = book_path.read_text(encoding="utf-8")
            stamp = json.loads(first)["generated"]
            time.sleep(1.1)  # 時間戳的解析度是秒,要確定「沒變」不是因為同一秒
            R.write_book(book_path)
            second = book_path.read_text(encoding="utf-8")
            self.assertEqual(json.loads(second)["generated"], stamp)
            self.assertEqual(first, second)

    # [VRN-ID] VRN-TST015-FNC014 · TEST
    def test_write_book_takes_a_new_timestamp_when_the_content_changed(self):
        """內容真的變了才換時間戳 —— 不是永遠不換。"""
        R = self.R
        with tempfile.TemporaryDirectory() as box:
            book_path = pathlib.Path(box) / "VRN_TickerRecord_SSOT_v0100.json"
            R.write_book(book_path)
            stale = json.loads(book_path.read_text(encoding="utf-8"))
            stale["generated"] = "2000-01-01T00:00:00"
            stale["broker"] = {"count": -1, "conflicts": [], "duplicates_folded": 0}
            book_path.write_text(json.dumps(stale, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
            R.write_book(book_path)
            self.assertNotEqual(json.loads(book_path.read_text(encoding="utf-8"))["generated"],
                                "2000-01-01T00:00:00")

    # [VRN-ID] VRN-TST015-FNC004 · TEST
    def test_the_book_on_disk_is_built_from_the_sources_and_is_current(self):
        R = self.R
        book = json.loads(R.BOOK_PATH.read_text(encoding="utf-8"))
        self.assertEqual(book["schema"], "VRN_TickerRecord_SSOT_v0100")
        self.assertEqual(list(book["fields"].keys()), [k for k, _z, _s in R.FIELDS], "the operator's 15 fields in order")
        self.assertGreater(book["broker"]["count"], 200, "every broker alias of every book, folded")
        self.assertGreater(book["broker"]["duplicates_folded"], 100, "the books overlap: duplicates are folded, not repeated")
        self.assertGreater(book["email_domain"]["count"], 20)
        self.assertGreater(book["rating"]["count"], 60)
        self.assertGreater(book["merge"]["counts"]["regex"], 40)
        for scope in ("broker", "email_domain", "rating"):
            for alias, it in list(book[scope]["entries"].items())[:50]:
                self.assertTrue(it["from"], f"{scope}:{alias} names its books")
        for c in book["conflicts"]:
            self.assertGreaterEqual(len(c["canonicals"]), 2, "a conflict is two canonicals for one alias, both kept")
        ok, why = R.check_record_book()
        self.assertTrue(ok, why)
        rebuilt = R.build_book(generated=book["generated"])
        self.assertEqual(json.dumps(rebuilt, ensure_ascii=False, sort_keys=True), json.dumps(book, ensure_ascii=False, sort_keys=True), "deterministic")

    # [VRN-ID] VRN-TST015-FNC005 · TEST
    def test_canonical_broker_keys_are_the_engine_s(self):
        R = self.R
        book = json.loads(R.BOOK_PATH.read_text(encoding="utf-8"))
        e = book["broker"]["entries"]
        for alias, key in (("凱基", "KGI"), ("兆豐", "MEGA"), ("元大", "YUANTA"), ("Goldman Sachs", "GS")):
            self.assertEqual(e[alias]["canonical"], key, alias)
        ms = e["Morgan Stanley"]["canonical"]
        self.assertTrue(ms == "MS" or (isinstance(ms, list) and "MS" in ms), "MS is one of the readings; a book that says otherwise is listed as a conflict")
        if isinstance(ms, list):
            self.assertTrue(any(c["alias"] == "Morgan Stanley" for c in book["conflicts"]))
        self.assertNotIn("YT", [v["canonical"] for v in e.values() if isinstance(v["canonical"], str)], "v0100's abbr YT is an alias of YUANTA, not a canonical")

    # [VRN-ID] VRN-TST015-FNC006 · TEST
    def test_record_of_a_report_without_a_database(self):
        R = self.R
        res = {"file": "20250819兆豐個股報告-泓德能源(6873).pdf", "status": "OK",
               "parts": [{"part": "title.ticker", "value": "6873", "state": "VERIFIED"}, {"part": "title.company", "value": "泓德能源", "state": "VERIFIED"},
                         {"part": "cover.broker", "value": "MEGA", "state": "VERIFIED"}, {"part": "cover.target_price", "value": 208.0, "state": "VERIFIED"},
                         {"part": "cover.current_price", "value": 169.5, "state": "SINGLE"}, {"part": "cover.upside", "value": 22.7, "state": "VERIFIED"}]}
        rec = R.record_of(res, {"LocalDBStatus": "ABSENT"}, {}, {})
        self.assertEqual((rec["ticker"]["value"], rec["bloomberg_ticker"]["value"], rec["bloomberg_ticker"]["state"]), ("6873", "6873 TT", "DERIVED"))
        self.assertEqual(rec["name"]["value"], "泓德能源")
        self.assertEqual(rec["adj_close"]["state"], "ABSENT", "the DB column says why")
        self.assertEqual(rec["upside_pct"]["calc"], 22.71)

    # 2026-10-13: the company part's value is the database's name; the record still compares the report's own reading with it
    # [VRN-ID] VRN-TST015-FNC008 · TEST
    def test_the_record_compares_the_report_reading_with_the_database_name(self):
        R = self.R
        res = {"file": "x.pdf", "status": "OK",
               "parts": [{"part": "title.ticker", "value": "2637", "state": "VERIFIED"},
                         {"part": "title.company", "value": "慧洋-KY", "state": "VERIFIED", "source": "db", "printed": "慧洋"}]}
        rec = R.record_of(res, {"LocalDBStatus": "OK", "NameDB": "慧洋-KY"}, {}, {})
        self.assertEqual((rec["name"]["value"], rec["name"]["state"]), ("慧洋-KY", "VERIFIED"))
        res["parts"][1]["printed"] = "Wisdom Marine"
        rec = R.record_of(res, {"LocalDBStatus": "OK", "NameDB": "慧洋-KY"}, {}, {})
        self.assertEqual(rec["name"]["state"], "DB", "an English reading cannot confirm a Chinese name")
        self.assertEqual(rec["english_name"]["value"], "Wisdom Marine")

    # PR 41 review: the listing's English-name column was read but never reached the record
    # [VRN-ID] VRN-TST015-FNC009 · TEST
    def test_the_english_name_comes_from_the_database_when_it_has_one(self):
        R = self.R

        # [VRN-ID] VRN-TST015-CLS002 · CLASS
        class FakeDb:
            status = "OK"

            # [VRN-ID] VRN-TST015-FNC010 · LOGIC
            def names(self):
                return {"2637": ("慧洋-KY", "TWSE", "2637.TW", "tw_listings")}

            # [VRN-ID] VRN-TST015-FNC011 · LOGIC
            def name_en(self, code):
                return {"2637": "Wisdom Marine Lines"}.get(code, "")

            # [VRN-ID] VRN-TST015-FNC012 · LOGIC
            def quote(self, code, report_date):
                return "2637.TW", "adj_close", None

        listing = R.lookup_code_record("2637", db=FakeDb())
        self.assertEqual(listing["name_en"], "Wisdom Marine Lines")
        res = {"file": "x.pdf", "status": "OK",
               "parts": [{"part": "title.ticker", "value": "2637", "state": "VERIFIED"},
                         {"part": "title.company", "value": "慧洋-KY", "state": "VERIFIED", "source": "db", "printed": "慧洋"}]}
        rec = R.record_of(res, {"LocalDBStatus": "OK", "NameDB": "慧洋-KY"}, {}, listing)
        self.assertEqual((rec["english_name"]["value"], rec["english_name"]["state"]), ("Wisdom Marine Lines", "DB"),
                         "the report printed only the Chinese name: the database's English name, not NOT_PRINTED")
        res["parts"][1]["printed"] = "Wisdom Marine"
        rec = R.record_of(res, {"LocalDBStatus": "OK", "NameDB": "慧洋-KY"}, {}, listing)
        self.assertEqual((rec["english_name"]["value"], rec["english_name"]["state"]), ("Wisdom Marine Lines", "VERIFIED"))
        self.assertEqual(R.lookup_code_record("9999", db=FakeDb())["name_en"], "")

    # round 5 (2026-10-12): the operator's Windows checkout is CRLF; the same book must hash the same or G20 calls it stale
    # 2026-10-20 實測：代號紀錄只問了首頁引擎一條讀法，YF／Bloomberg 兩欄 59 份報告裡 58 筆 SINGLE、
    # 永遠鎖不住；而 TRIM 那一側本來就讀到了同一批碼（`title.market` 用的就是它），只是沒交出來。
    # [VRN-ID] VRN-TST015-FNC015 · LOGIC
    @staticmethod
    def def_res(trim_codes=None, parts=None):
        res = {"file": "x.pdf", "status": "OK",
               "parts": parts or [{"part": "title.ticker", "value": "6873", "state": "VERIFIED"}]}
        if trim_codes is not None:
            res["cover"] = {"fields": {"page_codes": {"codes": trim_codes}}}
        return res

    # [VRN-ID] VRN-TST015-FNC016 · TEST
    def test_two_readings_of_the_printed_code_lock_it(self):
        """沒有本機資料庫也該鎖得住：首頁引擎與 TRIM 讀的是**兩條**讀法，對上就是 VERIFIED。"""
        codes = [{"raw": "6873.TW", "core": "6873", "platform": "yfinance", "market": "TWSE"},
                 {"raw": "6873 TT", "core": "6873", "platform": "bloomberg", "market": ""}]
        rec = self.R.record_of(self.def_res(codes), {"LocalDBStatus": "ABSENT"}, {"page_codes": codes}, {})
        self.assertEqual((rec["yfinance_ticker"]["value"], rec["yfinance_ticker"]["state"]), ("6873.TW", "VERIFIED"))
        self.assertEqual((rec["bloomberg_ticker"]["value"], rec["bloomberg_ticker"]["state"]), ("6873 TT", "VERIFIED"))

    # [VRN-ID] VRN-TST015-FNC017 · TEST
    def test_a_printed_code_is_never_missing_just_because_the_engine_skipped_the_file(self):
        """`3653健策…txt` 第 3 行印著 `Yahoo 3653.TW`，但 .txt 沒有首頁引擎結果 ——
        舊碼記成 MISSING（紙上明明印了），Bloomberg 還記成「推：<代號> TT」（其實是印的）。"""
        codes = [{"raw": "3653.TW", "core": "3653", "platform": "yfinance", "market": "TWSE"},
                 {"raw": "3653 TT", "core": "3653", "platform": "bloomberg", "market": ""}]
        parts = [{"part": "title.ticker", "value": "3653", "state": "VERIFIED"}]
        rec = self.R.record_of(self.def_res(codes, parts), {"LocalDBStatus": "ABSENT"}, {}, {})
        self.assertEqual((rec["yfinance_ticker"]["value"], rec["yfinance_ticker"]["state"]), ("3653.TW", "SINGLE"))
        self.assertEqual(rec["bloomberg_ticker"]["state"], "SINGLE", "印在紙上就不是推算出來的")
        self.assertIn("印", rec["bloomberg_ticker"]["source"])

    # [VRN-ID] VRN-TST015-FNC018 · TEST
    def test_two_readings_that_disagree_are_a_conflict(self):
        """不一致不准挑一個當答案。"""
        rec = self.R.record_of(self.def_res([{"raw": "6873.TWO", "core": "6873", "platform": "yfinance", "market": "TPEX"}]),
                               {}, {"page_codes": [{"raw": "6873.TW", "core": "6873", "platform": "yfinance", "market": "TWSE"}]}, {})
        self.assertEqual(rec["yfinance_ticker"]["state"], "CONFLICT")

    # [VRN-ID] VRN-TST015-FNC020 · TEST
    def test_the_database_cannot_paper_over_two_readings_that_disagree(self):
        """Codex PR #76 P2：資料庫對上其中一條，不能把**兩條讀法互相不一致**蓋掉 —— 那正是 G20 要喊的那一種。"""
        trim = [{"raw": "6873.TWO", "core": "6873", "platform": "yfinance", "market": "TPEX"}]
        fpe = {"page_codes": [{"raw": "6873.TW", "core": "6873", "platform": "yfinance", "market": "TWSE"}]}
        db = {"yfinance_ticker": "6873.TW", "yf_source": "localdb.yf_ticker"}
        self.assertEqual(self.R.record_of(self.def_res(trim), {}, fpe, db)["yfinance_ticker"]["state"], "CONFLICT")
        same = [{"raw": "6873.TW", "core": "6873", "platform": "yfinance", "market": "TWSE"}]
        self.assertEqual(self.R.record_of(self.def_res(same), {}, fpe, db)["yfinance_ticker"]["state"], "VERIFIED",
                         "兩條一致時資料庫照舊是第三個佐證")

    # [VRN-ID] VRN-TST015-FNC019 · TEST
    def test_nothing_printed_still_falls_back_to_the_derived_code(self):
        """兩邊都沒讀到才輪到推算 —— 原本的行為一個字都沒變。"""
        rec = self.R.record_of(self.def_res([]), {"LocalDBStatus": "ABSENT"}, {}, {})
        self.assertEqual((rec["bloomberg_ticker"]["value"], rec["bloomberg_ticker"]["state"]), ("6873 TT", "DERIVED"))
        self.assertEqual(rec["yfinance_ticker"]["state"], "MISSING")

    # [VRN-ID] VRN-TST015-FNC007 · TEST
    def test_source_hashes_ignore_crlf(self):
        with tempfile.TemporaryDirectory() as tmp:
            lf, crlf = Path(tmp) / "lf.json", Path(tmp) / "crlf.json"
            lf.write_bytes(b'{\n  "a": 1\n}\n')
            crlf.write_bytes(b'{\r\n  "a": 1\r\n}\r\n')
            self.assertEqual(self.R.file_sha256(lf), self.R.file_sha256(crlf))
            self.assertNotEqual(self.R.file_sha256(lf), self.R.file_sha256(Path(tmp) / "missing.json"))


# [VRN-ID] VRN-TST015-CLS003 · CLASS
class def_UpsideThatVrnRecomputedTests(unittest.TestCase):
    """算得出來的上漲空間，不可以記成「報告沒印」。

    實測 2026-10-20：`vrn_ticker_record.upside_pct_state` 59/59 都是 NOT_PRINTED、值是空的，
    而同一輪的另外兩張表把同一個數字當成 DERIVED 印出來 —— 四重點第 1 點「上漲空間 29.99%
    (DERIVED)」、`vrn_basic_info.UpsideDownsidePct` 29.99（與 `upside_pct_calc` 59/59 相符）。
    連 `cover.upside` 這個部位自己的 why 都寫著「沒印；VRN 重算 29.99%（def03）」。
    代號那幾欄（put_code）早就有 DERIVED 這一格 —— 這一欄沒跟上。
    """

    # [VRN-ID] VRN-TST015-FNC021 · LOGIC
    @classmethod
    def setUpClass(cls):
        cls.R = def_load("VRN_TickerRecord_v0100", VRN / "engine" / "VRN_TickerRecord_v0100.py")

    # [VRN-ID] VRN-TST015-FNC022 · LOGIC
    @staticmethod
    def def_res(printed_upside=None, tp=208.0, cp=160.0):
        parts = [{"part": "title.ticker", "value": "6873", "state": "VERIFIED"}]
        if tp is not None:
            parts.append({"part": "cover.target_price", "value": tp, "state": "VERIFIED"})
        if cp is not None:
            parts.append({"part": "cover.current_price", "value": cp, "state": "VERIFIED", "close": cp})
        if printed_upside is not None:
            parts.append({"part": "cover.upside", "value": printed_upside, "state": "VERIFIED"})
        return {"file": "x.pdf", "status": "OK", "parts": parts}

    # [VRN-ID] VRN-TST015-FNC023 · LOGIC
    def def_rec(self, **kw):
        return self.R.record_of(self.def_res(**kw), {"LocalDBStatus": "ABSENT"}, {}, {})

    # [VRN-ID] VRN-TST015-FNC024 · TEST
    def test_not_printed_but_recomputed_is_derived(self):
        rec = self.def_rec()["upside_pct"]
        self.assertEqual(rec["state"], "DERIVED", "算得出來就不是「報告沒印」")
        self.assertEqual(rec["value"], 30.0, "(208 − 160) ÷ 160 = 30.00%")
        self.assertEqual(rec["value"], rec["calc"], "交出去的值就是它自己算的那個，不另算一次")

    # [VRN-ID] VRN-TST015-FNC025 · TEST
    def test_a_printed_upside_still_wins(self):
        """紙上印了就用紙上的，一個字都不改 —— 重算的值仍然擺在 calc 供對照。"""
        rec = self.def_rec(printed_upside=29.5)["upside_pct"]
        self.assertEqual((rec["value"], rec["state"]), (29.5, "VERIFIED"))
        self.assertEqual(rec["calc"], 30.0, "重算的數字照舊留著，兩邊差多少看得見")

    # [VRN-ID] VRN-TST015-FNC026 · TEST
    def test_nothing_to_compute_is_still_not_printed(self):
        """沒有目標價或沒有現價就真的算不出來 —— 這時候才是 NOT_PRINTED，不可以編一個。"""
        for kw in ({"tp": None}, {"cp": None}, {"tp": None, "cp": None}):
            with self.subTest(**kw):
                rec = self.def_rec(**kw)["upside_pct"]
                self.assertEqual(rec["state"], "NOT_PRINTED")
                self.assertEqual(rec["value"], "")
                self.assertIsNone(rec["calc"])

    # [VRN-ID] VRN-TST015-FNC027 · TEST
    def test_the_fifteen_column_gate_still_accepts_this_column(self):
        """握手：G20 的守門擋的是哪幾種狀態，從它自己的原始碼讀出來比對 —— 兩邊各寫各的就會斷。"""
        gate = (VRN / "engine" / "VRN_AutoTestLoop.py").read_text(encoding="utf-8")
        self.assertIn('in ("MISSING", "CONFLICT")', gate, "G20 換了擋的狀態就要同步看這一欄")
        self.assertNotIn("DERIVED", '("MISSING", "CONFLICT")')
        self.assertEqual(self.def_rec()["upside_pct"]["state"], "DERIVED", "推算得出來不該被擋")
        self.assertIn("upside_pct", [k for k, _zh, _src in self.R.FIELDS], "這一欄本來就在 15 欄裡")


if __name__ == "__main__":
    unittest.main()
