#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ===== [VRN:ID:v0100] VRN-TST012 · test_VRN_TitleTrim · TEST =====
# AST 注入（只加註解，AST 不變）：類別 8 · 函式 74；逐一編號在 ssot/VRN_ID_SSOT_v0100.json
# ===== [VRN:ID:END] =====
"""VRN_TitleTrim v0100 (operator 2026-10-11「只擷取個股報告的標題分拆識別 首頁及年度財報頁來進行基本資料清理TRIM後分拆識別
實測實修正」): Method def02 TRIM (raw kept, numbers never lost), the title in def02 segments without a first-line assumption, page 1
and the annual financial pages read again after TRIM, and VERIFIED only where two independent readings agree."""

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

import copy
import importlib.util
import json
import sys
import tempfile
import unicodedata
import unittest
from pathlib import Path

VRN = Path(__file__).resolve().parents[1]


# [VRN-ID] VRN-TST012-FNC001 · IO
def def_load(name, path):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


# [VRN-ID] VRN-TST012-FNC002 · LOGIC
def def_has(name):
    return importlib.util.find_spec(name) is not None


# [VRN-ID] VRN-TST012-CLS001 · CLASS
class def_TitleTrimTests(unittest.TestCase):
    # [VRN-ID] VRN-TST012-FNC003 · LOGIC
    @classmethod
    def setUpClass(cls):
        cls.T = def_load("VRN_TitleTrim_v0100", VRN / "engine" / "VRN_TitleTrim_v0100.py")
        cls.B = cls.T.books()
        cls.brd = cls.T.first_page_engine().brd
        cls.T._LOCALDB = False                              # the operator's database stays out of the known answers on every machine

    # [VRN-ID] VRN-TST012-FNC004 · TEST
    def test_trim_follows_method_def02_and_never_loses_a_number(self):
        method = json.loads((VRN / "ssot" / "VRN_Method_SSOT_v0100.json").read_text(encoding="utf-8"))
        self.assertEqual(self.B.book["trim"]["steps"], method["def02_title"]["normalize_steps"], "the eight steps are the Method book's")
        t = self.T.trim("（１２３）　－４５％​ ＮＴ＄１，２００ 臺積電⽑利")
        self.assertEqual(t["clean"], "(123) -45% NT$1,200 台積電毛利")
        self.assertEqual(t["raw"], "（１２３）　－４５％​ ＮＴ＄１，２００ 臺積電⽑利", "the printed text is kept as printed")
        self.assertEqual(t["loss"], [])
        self.assertEqual([(n["value"], n["kind"]) for n in t["numbers"]], [(-123.0, "amount"), (-45.0, "pct"), (1200.0, "amount")])
        self.assertEqual(self.T.trim("1.2x")["numbers"][0]["kind"], "multiple", "def16: a multiple is never a percentage")
        bad = copy.deepcopy(self.B.book)
        bad["trim"]["invisible"].append("5")                       # a broken book that deletes a digit must be caught
        broken = self.T.Books(bad, self.B.method)
        self.assertIn("數字", self.T.trim("目標價 1,250", broken)["loss"])

    # [VRN-ID] VRN-TST012-FNC005 · TEST
    def test_book_carries_no_hidden_characters(self):
        raw = (VRN / "ssot" / "VRN_TitleTrim_SSOT_v0100.json").read_text(encoding="utf-8")
        hidden = [hex(ord(c)) for c in raw if unicodedata.category(c) in ("Cf", "Cc", "Zs", "Co") and c not in " \n"]
        self.assertEqual(hidden, [], "invisible / bidi characters are written as \\u escapes in the book")

    # [VRN-ID] VRN-TST012-FNC006 · TEST
    def test_title_segments_in_def02_order(self):
        for case in self.T.TITLE_CASES:
            self.assertEqual(self.T.check_title_case(case, self.B, self.brd), [], case["text"])
        d = self.T.decompose_title("2025 年展望：燁輝 (2023) 營運回溫", {"filename": {"ticker": ""}}, self.B, self.brd)
        self.assertEqual(d["segments"]["ticker"]["state"], "REVIEW", "a year-band code with no second source is never taken as a ticker")

    # [VRN-ID] VRN-TST012-FNC007 · TEST
    def test_no_first_line_assumption(self):
        page = {"width": 595, "height": 842, "meta_title": "Microsoft Word - x.docx", "lines": [
            {"text": "凱基證券投資顧問 KGI Securities Research 2026/09/01", "size": 8.0, "bold": False, "bbox": [], "top": 40.0, "x0": 40},
            {"text": "台積電(2330 TT) 先進製程需求強勁", "size": 18.0, "bold": True, "bbox": [], "top": 80.0, "x0": 40},
            {"text": "我們預估 2026 年 EPS 60 元。", "size": 10.0, "bold": False, "bbox": [], "top": 120.0, "x0": 40}]}
        got = self.T.pick_title(page, {"filename": {"ticker": "2330", "company_names": ["台積電"]}}, self.B, self.brd)
        self.assertEqual(got["text"], "台積電(2330 TT) 先進製程需求強勁")
        self.assertNotIn("META", [c["source"] for c in got["candidates"]], "a Word file name is not a title")

    # [VRN-ID] VRN-TST012-FNC008 · TEST
    def test_two_independent_readings_or_it_is_not_verified(self):
        ctx = {"filename": {"ticker": "2330", "company_names": ["台積電"], "broker": "KGI", "date": "2026-09-01", "stem": "x"},
               "engine": {"ticker": "2330", "rating_action": "UPGRADE", "target_price": 104.0, "broker": "KGI"}, "basic": {}, "entities": {}}
        title = {"text": "台積電(2330 TT) 維持買進", "segments": {"ticker": {"value": "2330", "state": "READ"},
                                                               "company": {"value": "台積電", "state": "READ"},
                                                               "rating_action": {"value": "MAINTAIN", "state": "READ"},
                                                               "tp_change": {"value": "", "state": "NOT_PRINTED"},
                                                               "report_type": {"value": "", "state": "NOT_PRINTED"}}}
        cover = {"fields": {"target_price": {"value": 1200.0}, "broker": {"value": "KGI"}, "current_price": {"value": 1000.0}}}
        parts = {p["part"]: p for p in self.T.verify(title, cover, ctx, self.B, self.brd)}
        self.assertEqual(parts["title.ticker"]["state"], "VERIFIED")
        self.assertEqual(parts["title.company"]["state"], "VERIFIED")
        self.assertEqual(parts["title.rating_action"]["state"], "CONFLICT", "維持 vs the engine's 上調 (from 目標價上調): shown, never picked")
        self.assertEqual(parts["cover.target_price"]["state"], "CONFLICT", "1200 vs 104")
        self.assertEqual(parts["cover.current_price"]["state"], "SINGLE")
        self.assertEqual(parts["cover.broker"]["state"], "VERIFIED")
        self.assertEqual(parts["title.tp_change"]["state"], "NOT_PRINTED")
        self.assertEqual(parts["cover.date"]["state"], "SINGLE", "only the file name gives the date here")

    # [VRN-ID] VRN-TST012-FNC009 · TEST
    def test_label_inside_an_email_is_not_a_label(self):
        hits = self.T._label_hits("分析師 王小明 analyst@example-research.com (02)2181-8888", self.B.labels["analyst"], self.B)
        self.assertEqual([h[0] for h in hits], ["分析師"])
        self.assertTrue(hits[0][1].startswith("王小明"))

    # [VRN-ID] VRN-TST012-FNC010 · TEST
    def test_database_engine_is_the_second_reader_of_the_tables(self):
        result = {"file": "t.pdf", "status": "OK", "sentences": [], "checks": [], "rows": [], "tables": [
            {"anchor": "p3·T1", "subcategory": "", "title": "", "columns": ["項目 (NT$ 百萬元)", "2024A", "2025E", "2026E"],
             "rows": [["營收", "11,507", "13,661", "16,293"], ["稅後淨利", "1,380", "1,707", "2,118"], ["毛利率(%)", "38.5", "39.2", "40.1"]]}]}
        db = [{"MetricNameRaw": "營收", "PeriodLabelRaw": "2024A", "Value": 11507.0}, {"MetricNameRaw": "營收", "PeriodLabelRaw": "2025E", "Value": 13661.0},
              {"MetricNameRaw": "稅後淨利", "PeriodLabelRaw": "2024A", "Value": 1380.0},
              {"MetricNameRaw": "稅後淨利", "PeriodLabelRaw": "2025E", "Value": 1770.0}]   # one cell read differently
        an = self.T.annual(result, self.B, db)
        self.assertEqual([p["page"] for p in an["pages"]], [3])
        parts = {p["part"]: p for p in self.T.annual_parts(an)}
        self.assertEqual(parts["annual.revenue@2024"]["state"], "VERIFIED")
        self.assertEqual(parts["annual.net_income@2025"]["state"], "CONFLICT", "1707 vs the database engine's 1770: shown, never picked")
        self.assertEqual(parts["annual.gross_margin@2026"]["state"], "SINGLE", "no second reading, no identity: not locked")

    # [VRN-ID] VRN-TST012-FNC012 · TEST
    def test_real_run_2026_10_12_reading_fixes(self):
        """C:\\測試樣本報告 first run: a two-line title is the same title; a dated price is the price; generic words are not brokers."""
        self.assertEqual(self.T._bare("泓德能源(6873) - 逢低買進 $208", self.B), self.T._bare("泓德能源(6873) 逢低買進 $208", self.B))
        stripped = self.B.date_like_rx.sub(" ", "(2025/11/27) 90.2")
        self.assertEqual([n["value"] for n in self.T.numbers(stripped, self.B)], [90.2])
        self.assertEqual([n["value"] for n in self.T.numbers(self.B.date_like_rx.sub(" ", "169.5"), self.B)], [169.5], "169.5 is a price")
        zones = [{"line": 1, "zone": "TopHeader", "clean": "First half review 2026"}, {"line": 2, "zone": "Footer", "clean": "兆豐證券 研究部"}]
        got = self.T._broker_of(zones, self.brd, self.B)
        self.assertEqual((got or {}).get("value"), "MEGA", "'First half' is not 第一金; the disclaimer is read last but still read")
        hits = self.T._label_hits("前次目標價:345 目標價:208", self.B.labels["target_price"], self.B)
        self.assertEqual(hits[0][1].split()[0], "208")
        rows = self.T.title_rows([{"file": "x.pdf", "status": "OK", "title": {"text": "", "segments": {}}}])
        self.assertEqual(rows[0]["ticker_state"], "NO_TITLE")

    # [VRN-ID] VRN-TST012-FNC013 · TEST
    def test_real_run_2026_10_12_round_two(self):
        """C:\\測試樣本報告 second run (1b4e718): 第一階段 is not 第一金; the covered company's own name is not the broker; a number
        followed by (F) or -11x is not a price; target, price and upside vote only when one pair adds up; ENG396 reading the
        前次 line is set aside."""
        body = [{"line": 1, "zone": "SummaryBox", "clean": "步開始認列,菲律賓方面第一階段300MW將開始認"}]
        self.assertIsNone(self.T._broker_of(body, self.brd, self.B), "第一階段 is not 第一金")
        for text, want in (("第一金證券 研究部", "FIRST"), ("統一投顧 研究部", "PRESIDENT")):
            got = self.T._broker_of([{"line": 1, "zone": "TopHeader", "clean": text}], self.brd, self.B)
            self.assertEqual((got or {}).get("value"), want, text)
        zones = [{"line": 1, "zone": "TitleZone", "clean": "中信金(2891) 獲利成長延續"}, {"line": 2, "zone": "AnalystBox", "clean": "凱基證券 研究部"}]
        self.assertEqual(self.T._broker_of(zones, self.brd, self.B)["value"], "CTBC", "without the company name the title reads as a broker")
        self.assertEqual(self.T._broker_of(zones, self.brd, self.B, ("中信金",))["value"], "KGI", "the covered company is not the broker")
        for text in ("對應約 12X 26(F) PER", "10-11x,低於過往區間"):
            nums = self.T.numbers(text, self.B)
            prices = [n for n in nums if n["kind"] == "amount" and not self.B.not_price_after_rx.match(text[n["end"]:])]
            self.assertEqual(prices, [], text)
        tp = [("page", "首頁（TRIM）", 125.0), ("engine", "首頁引擎", 145.0), ("entities", "ENG396 全文", 125.0)]
        cp = [("page", "首頁（TRIM）", 10.0), ("engine", "首頁引擎", 118.0)]
        self.assertEqual(self.T._arith_pair(tp, cp, 23.0, 0.01), (145.0, 118.0), "145 / 118 - 1 = 22.9% (printed 23%)")
        self.assertEqual(self.T._arith_pair(tp, cp, 50.0, 0.01), (None, None), "nothing adds up: no vote")
        same = lambda a, b: abs(float(a) - float(b)) < 1e-6   # noqa: E731
        self.assertEqual(self.T._not_prior(345.0, [345.0], same), (None, {"ENG396 全文（讀到前次那一行，不計）": 345.0}))
        self.assertEqual(self.T._not_prior(208.0, [345.0], same), (208.0, {}))

    # [VRN-ID] VRN-TST012-FNC014 · TEST
    def test_real_run_2026_10_12_round_three(self):
        """C:\\測試樣本報告 third run (552f44d): the line under 前次投資建議 is found by geometry when body lines of the other column
        sit between them; +886 2 phones; every contact on the page counts; an NR report has no target to miss."""
        B = self.B
        mk = lambda text, x, y, size=8.0: {"text": text, "size": size, "bold": False, "bbox": [x, y - size, x + 150, y + 2], "top": y - size, "x0": x}  # noqa: E731
        lines = sorted([mk("前次投資建議：2025/06/03", 420, 150), mk("本公司未對本股票評等", 40, 158, 10.0), mk("「買進」,目標價: 78", 420, 166),
                        mk("收盤價：45.5", 420, 182)], key=lambda l: (l["top"], l["x0"]))
        clean = [self.T.trim(l["text"], B)["clean"] for l in lines]
        flags = self.T._prior_lines(lines, clean, B)
        self.assertEqual([c for c, f in zip(clean, flags) if f], ["「買進」,目標價: 78"], "the same column, not the body line between")
        page = {"height": 842.0, "lines": lines}
        cover = self.T.cover_fields(page, {"joined": []}, B, self.brd)
        self.assertNotIn("target_price", cover["fields"], "78 is the previous target")
        self.assertEqual(cover["prior_target_prices"], [78.0])
        self.assertEqual(cover["fields"]["current_price"]["value"], 45.5)
        text_lines = [{"text": t, "size": 0.0, "bold": False, "bbox": [], "top": float(i), "x0": 0.0}
                      for i, t in enumerate(["前次評等：", "買進 目標價 100", "目標價 120"])]
        self.assertEqual(self.T._prior_lines(text_lines, [l["text"] for l in text_lines], B), [False, True, False], "no box: reading order")
        self.assertEqual(B.tel_rx.search("Tel: +886 2 2326 9812").group(0), "+886 2 2326 9812")
        self.assertIsNone(B.tel_rx.search("2025/11/28 90.2"))
        f = {"email": {"value": "jacky.lee@x.com", "all": ["jacky.lee@x.com", "ezio.huang@x.com"]}}
        p = self.T._contact_vote("cover.email", f, "email", "Ezio.Huang@x.com", lambda v: str(v or "").casefold())
        self.assertEqual((p["state"], p["value"]), ("VERIFIED", "Ezio.Huang@x.com"), "the engine's analyst is one of the page's two")
        p = self.T._contact_vote("cover.email", f, "email", "nobody@y.com", lambda v: str(v or "").casefold())
        self.assertEqual(p["state"], "CONFLICT")
        title = {"text": "瑞基(4171) 未評等", "segments": {"rating_action": {"value": "NOT_RATED", "state": "READ"}}}
        ctx = {"filename": {"rating": "NR_未評等", "ticker": "4171"}, "engine": {"rating_action": "MAINTAIN", "rating": ""}, "basic": {}, "entities": {}}
        parts = {p["part"]: p for p in self.T.verify(title, {"zones": [], "fields": {}}, ctx, B, self.brd)}
        self.assertEqual((parts["title.rating_action"]["state"], parts["title.rating_action"]["value"]), ("VERIFIED", "NOT_RATED"))
        self.assertEqual(parts["cover.target_price"]["state"], "NOT_PRINTED", "an NR report prints no target: not MISSING")
        self.assertIn("未評等", parts["cover.target_price"]["why"])

    # [VRN-ID] VRN-TST012-FNC015 · TEST
    def test_real_run_2026_10_12_round_four(self):
        """C:\\測試樣本報告 fourth run (02cd986): '前次投資建議 2025.08.06:' is a 前次 line; 'TP from 3,600 to 4,200' is 4,200;
        '12M price target' is not the share price; an extension stays out of the phone; a junk engine title does not vote."""
        B = self.B
        self.assertTrue(B.prior_line_rx.search("前次投資建議 2025.08.06:"))
        self.assertTrue(B.prior_line_rx.search("前次投資建議：2025/06/03"))
        self.assertFalse(B.prior_line_rx.search("前次投資建議 2025.08.06:目標價125元"))
        lines = [{"text": t, "size": 0.0, "bold": False, "bbox": [], "top": float(i), "x0": 0.0}
                 for i, t in enumerate(["投資評等  目標價", "逢低買進  $145", "前次投資建議 2025.08.06:", "目標價125 元「逢低買進」"])]
        cover = self.T.cover_fields({"height": 0.0, "lines": lines}, {"joined": []}, B, self.brd)
        self.assertEqual((cover["fields"]["target_price"]["value"], cover["prior_target_prices"]), (145.0, [125.0]))
        en = [{"text": t, "size": 0.0, "bold": False, "bbox": [], "top": float(i), "x0": 0.0}
              for i, t in enumerate(["We raise our TP from NT$3,600 to NT$4,200. Maintain BUY.", "12M price target NT$4,200.00",
                                     "Share price (30 Sep 2025) NT$3,300.00", "Tel: +886 2 2326 9899 ext. 7960"])]
        cover = self.T.cover_fields({"height": 0.0, "lines": en}, {"joined": []}, B, self.brd)
        f = cover["fields"]
        self.assertEqual((f["target_price"]["value"], f["current_price"]["value"], cover["prior_target_prices"]), (4200.0, 3300.0, [3600.0]))
        self.assertEqual(f["tel"]["value"], "886223269899", "the extension 7960 is not part of the number")
        self.assertTrue(self.T._title_junk("I", "未評等 - AMAX-KY (6933 TT)", "6933", B))
        self.assertTrue(self.T._title_junk("團泰期賃 國泰證券子公司 2023/10/05", "聯陽3014 TT ( 電子上游-IC 設計 )", "3014", B))
        self.assertFalse(self.T._title_junk("泓德能源(6873) 逢低買進 $208", "泓德能源(6873) - 逢低買進 $208", "6873", B))

    # [VRN-ID] VRN-TST012-FNC016 · TEST
    def test_real_run_2026_10_12_round_five(self):
        """C:\\測試樣本報告 fifth run (889085e), the local DB now present: 緯穎 is not compared with Wiwynn (another script), 頎邦 is
        頎邦科技股份有限公司 and 慧洋 is 慧洋-KY; '4 Jun 2025' and 'May 19, 2026' are dates, not prices; daiwacm-cathay.com is DAIWA."""
        B, T = self.B, self.T
        for a, b in (("慧洋", "慧洋-KY"), ("頎邦", "頎邦科技股份有限公司"), ("Wiwynn", "Wiwynn Corp"), ("矽力*-KY", "矽力-KY"),
                     ("Delta Electronics", "Delta Electronics Co., Ltd.")):
            self.assertTrue(T._company_same(a, b, B), (a, b))
        for a, b in (("中信金", "凱基"), ("Wiwynn", "緯穎"), ("台積電", "聯電")):
            self.assertFalse(T._company_same(a, b, B), (a, b))
        seg = lambda v, st: {"value": v, "state": st}  # noqa: E731
        segments = {"ticker": seg("6669", "READ"), "company": seg("", "NOT_PRINTED"), "rating_action": seg("", "NOT_PRINTED"),
                    "tp_change": seg("", "NOT_PRINTED"), "report_type": seg("", "NOT_PRINTED")}
        ctx = {"filename": {"ticker": "6669", "company_names": [], "broker": "CLSA", "date": "2026-10-01", "stem": "x"},
               "engine": {"ticker": "6669", "company": "Wiwynn", "target_price": 4200.0, "broker": "CLSA"}, "basic": {"NameDB": "緯穎"}, "entities": {}}
        cover = {"fields": {"target_price": {"value": 4200.0}, "broker": {"value": "CLSA"}, "current_price": {"value": 3300.0}}}
        parts = {p["part"]: p for p in T.verify({"text": "Wiwynn (6669 TT)", "segments": segments}, cover, ctx, B, self.brd)}
        self.assertNotEqual(parts["title.company"]["state"], "CONFLICT", "Wiwynn vs 緯穎 is two scripts, not two readings")
        self.assertEqual(parts["title.company"]["value"], "緯穎", "2026-10-13: the company name is the database's")
        self.assertIn("首頁引擎（不同文字，不比）", parts["title.company"]["sources"])
        segments["company"] = seg("頎邦", "READ")
        ctx["engine"]["company"], ctx["basic"]["NameDB"] = "頎邦", "頎邦科技股份有限公司"
        parts = {p["part"]: p for p in T.verify({"text": "頎邦(6147 TT)", "segments": segments}, cover, ctx, B, self.brd)}
        self.assertEqual(parts["title.company"]["state"], "VERIFIED", "the DB's official name carries the company form")
        for text, want in (("Price (as of 4 Jun 2025) NT$114.0", 114.0), ("股價 (May 19, 2026) 480.5", 480.5), ("Share price 19 May 2026 NT$88.0", 88.0)):
            lines = [{"text": text, "size": 0.0, "bold": False, "bbox": [], "top": 0.0, "x0": 0.0}]
            got = T.cover_fields({"height": 0.0, "lines": lines}, {"joined": []}, B, self.brd)
            self.assertEqual(got["fields"]["current_price"]["value"], want, text)
        self.assertEqual(T._domain_broker("daiwacm-cathay.com"), "DAIWA")
        self.assertEqual(T._domain_broker("research.kgi.com"), "KGI")
        self.assertIsNone(T._domain_broker("example.org"))

    # [VRN-ID] VRN-TST012-FNC017 · TEST
    def test_real_run_2026_10_12_round_five_b(self):
        """The rerun on 889085e (20261012T232328): KGI prices read as the day of the report date (19 / 15 / 17), Daiwa Hold
        reports print 'Target price: n.a.', and the console needs the page line behind each fix row."""
        B, T = self.B, self.T
        line = lambda i, t: {"text": t, "size": 0.0, "bold": False, "bbox": [], "top": float(i), "x0": 0.0}  # noqa: E731
        for text, want in (("收盤價(5月19日) 300.5", 300.5), ("Price May 19 NT$300.0", 300.0), ("Share price (19-May-26) 88.5", 88.5),
                           ("股價 (May 19, 2026) 480.5", 480.5)):
            got = T.cover_fields({"height": 0.0, "lines": [line(0, text)]}, {"joined": []}, B, self.brd)
            self.assertEqual(got["fields"]["current_price"]["value"], want, text)
        got = T.cover_fields({"height": 0.0, "lines": [line(0, "The stock may 10 times"), line(1, "目標價 15.5")]}, {"joined": []}, B, self.brd)
        self.assertEqual(got["fields"]["target_price"]["value"], 15.5, "a small price is still a price")
        cover = T.cover_fields({"height": 0.0, "lines": [line(0, "Rating: Hold"), line(1, "Target price (TWD): n.a."), line(2, "Share price: TWD2,470")]},
                               {"joined": []}, B, self.brd)
        self.assertEqual(cover["declared_na"]["target_price"]["line"], 2)
        seg = lambda v, st: {"value": v, "state": st}  # noqa: E731
        segments = {"ticker": seg("3653", "READ"), "company": seg("", "NOT_PRINTED"), "rating_action": seg("", "NOT_PRINTED"),
                    "tp_change": seg("", "NOT_PRINTED"), "report_type": seg("", "NOT_PRINTED")}
        ctx = {"filename": {"ticker": "3653", "company_names": [], "broker": "DAIWA", "date": "2025-10-02", "stem": "x"},
               "engine": {"ticker": "3653", "broker": "DAIWA", "current_price": 2470.0}, "basic": {}, "entities": {}}
        parts = {p["part"]: p for p in T.verify({"text": "Jentech (3653 TT)", "segments": segments}, cover, ctx, B, self.brd)}
        self.assertEqual(parts["cover.target_price"]["state"], "NOT_PRINTED", "the report says there is no TP")
        self.assertIn("n.a.", parts["cover.target_price"]["why"])
        cover.pop("declared_na")
        parts = {p["part"]: p for p in T.verify({"text": "Jentech (3653 TT)", "segments": segments}, cover, ctx, B, self.brd)}
        self.assertEqual(parts["cover.target_price"]["state"], "MISSING", "without the n.a. line a missing TP stays MISSING")
        res = {"file": "a.pdf", "status": "OK", "title": {"text": "健策(3653 TT)"},
               "cover": {"zones": [{"line": 1, "clean": "健策 Jentech"}, {"line": 2, "clean": "Share price (4 Jun 2025) NT$114.0"}, {"line": 3, "clean": "目標價：見內文"}],
                         "fields": {"current_price": {"value": 114.0, "line": 2}}},
               "parts": [{"part": "cover.current_price", "state": "CONFLICT", "value": 114.0, "sources": {"首頁（TRIM）": 114.0, "首頁引擎": 4.0}},
                         {"part": "cover.target_price", "state": "MISSING", "value": ""},
                         {"part": "title.company", "state": "CONFLICT", "value": "健策"}]}
        rows = {r["part"]: r for r in T.fix_rows([res])}
        self.assertEqual(rows["cover.current_price"]["evidence"], "行 2: Share price (4 Jun 2025) NT$114.0")
        self.assertTrue(rows["cover.target_price"]["evidence"].startswith("行 3（有標籤，TRIM 沒讀到值）"))
        self.assertEqual(rows["title.company"]["evidence"], "標題: 健策(3653 TT)")
        self.assertEqual([r["state"] for r in T.fix_rows([res])][:2], ["CONFLICT", "CONFLICT"], "conflicts first")

    # [VRN-ID] VRN-TST012-FNC019 · TEST
    def test_company_and_price_come_from_the_database(self):
        """Operator 2026-10-13「公司名稱價格一率至DATABASE去取」: the value is the database's; the report's readings check it."""
        B, T = self.B, self.T
        seg = lambda v, st: {"value": v, "state": st}  # noqa: E731
        segments = {"ticker": seg("2637", "READ"), "company": seg("慧洋", "READ"), "rating_action": seg("", "NOT_PRINTED"),
                    "tp_change": seg("", "NOT_PRINTED"), "report_type": seg("", "NOT_PRINTED")}
        quotes = {"name": "慧洋-KY", "closes": {"basis": ("2026-09-14", 95.1), "same": ("2026-09-15", 96.9)}}
        ctx = {"filename": {"ticker": "2637", "company_names": ["慧洋"], "broker": "KGI", "date": "2026-09-15", "stem": "x"},
               "engine": {"ticker": "2637", "company": "慧洋", "broker": "KGI", "date": "2026-09-15", "current_price": 96.9},
               "basic": {}, "entities": {}, "db": lambda code, date: dict(quotes, closes=quotes["closes"] if date else None)}
        cover = lambda cp: {"fields": {"date": {"value": "2026-09-15"}, "current_price": {"value": cp}}}  # noqa: E731
        parts = {p["part"]: p for p in T.verify({"text": "慧洋(2637 TT)", "segments": segments}, cover(96.9), ctx, B, self.brd)}
        c, p = parts["title.company"], parts["cover.current_price"]
        self.assertEqual((c["value"], c["state"], c["source"], c["printed"]), ("慧洋-KY", "VERIFIED", "db", "慧洋"))
        self.assertEqual((p["value"], p["state"], p["date"], p["source"]), (96.9, "VERIFIED", "2026-09-15", "db"), "the report-day close")
        parts = {p["part"]: p for p in T.verify({"text": "慧洋(2637 TT)", "segments": segments}, cover(95.1),
                                                dict(ctx, engine=dict(ctx["engine"], current_price=95.1)), B, self.brd)}
        self.assertEqual((parts["cover.current_price"]["value"], parts["cover.current_price"]["date"]), (95.1, "2026-09-14"), "the previous close")
        parts = {p["part"]: p for p in T.verify({"text": "慧洋(2637 TT)", "segments": segments}, cover(318.0),
                                                dict(ctx, engine=dict(ctx["engine"], current_price=None)), B, self.brd)}
        self.assertEqual((parts["cover.current_price"]["value"], parts["cover.current_price"]["state"]), (95.1, "CONFLICT"),
                         "a printed price no close matches: the database's value, flagged for a person")
        parts = {p["part"]: p for p in T.verify({"text": "慧洋(2637 TT)", "segments": segments}, {"fields": {"date": {"value": "2026-09-15"}}},
                                                dict(ctx, engine=dict(ctx["engine"], current_price=None)), B, self.brd)}
        self.assertEqual((parts["cover.current_price"]["value"], parts["cover.current_price"]["state"]), (95.1, "SINGLE"), "nothing printed")
        segments["company"] = seg("賴偉中", "READ")
        parts = {p["part"]: p for p in T.verify({"text": "賴偉中(2637 TT)", "segments": segments}, cover(96.9),
                                                dict(ctx, filename=dict(ctx["filename"], company_names=[]), engine=dict(ctx["engine"], company="")), B, self.brd)}
        self.assertEqual((parts["title.company"]["value"], parts["title.company"]["state"]), ("慧洋-KY", "CONFLICT"),
                         "a reading that names someone else is shown, the name stays the database's")
        nodb = {p["part"]: p for p in T.verify({"text": "慧洋(2637 TT)", "segments": dict(segments, company=seg("慧洋", "READ"))}, cover(96.9),
                                               dict(ctx, db=None), B, self.brd)}
        self.assertNotIn("source", nodb["cover.current_price"], "no database: the report's readings as before")

    # [VRN-ID] VRN-TST012-FNC018 · TEST
    def test_real_run_2026_10_13_round_six(self):
        """C:\\測試樣本報告 sixth run (b42f45f, FAIL 0): every CONFLICT the console printed, from its own page line."""
        B, T, brd = self.B, self.T, self.brd
        line = lambda i, t, z=0.0: {"text": t, "size": 0.0, "bold": False, "bbox": [], "top": float(i), "x0": z}  # noqa: E731
        page = lambda *ts: {"height": 0.0, "lines": [line(i, x) for i, x in enumerate(ts)]}  # noqa: E731
        f = lambda *ts, **kw: T.cover_fields(page(*ts), {"joined": []}, B, brd, **kw)["fields"]  # noqa: E731
        # brokers: an e-mail domain, a digit before 元大, 在台新增, 中信銀
        self.assertEqual(f("Helen Chien", "helen.chien@daiwacm-cathay.com.tw")["broker"]["value"], "DAIWA")
        self.assertNotIn("broker", f("7.75%,優於預期,EPS 3.37元大致符合預期。"))
        self.assertNotIn("broker", f("今年已在台新增10家分店,全台分店數達139家"))
        self.assertNotIn("broker", f("16%至231億元,主要中信銀提存前獲利年增17%"), "中信銀 is the covered group's bank")
        self.assertEqual(f("元大投顧 研究部")["broker"]["value"], "YUANTA")
        self.assertEqual(f("華南永昌證券投資顧問")["broker"]["value"], "HUANAN")
        # dates: '150.8 / 4,777' is not ROC 150-08-04; real dates still read
        self.assertEqual(T._date_of("市值 : (NT$bn/US$mn) 150.8 / 4,777", B)[0], None)
        self.assertEqual(T._date_of("市值 : (NT$bn/US$mn) 105.4 / 3,316", B)[0], None)
        for s, want in (("2025/12/06", "2025-12-06"), ("114.12.02", "2025-12-02"), ("114/12/2", "2025-12-02"), ("2026年5月19日", "2026-05-19")):
            self.assertEqual(T._date_of(s, B)[0], want, s)
        # prices: the 52-week range is not the price; upside in prose is not the upside
        got = f("52 週股價 (低 \\ 高) (NT$): 318.0 -466.0", "股價 (NT$): 320.0")
        self.assertEqual(got["current_price"]["value"], 320.0)
        self.assertNotIn("upside", f("potential upside to our mid-term growth rate of 15% once these turns materialize."))
        self.assertEqual(f("Upside: 15.2%")["upside"]["value"], 15.2)
        # contacts glued to a table cell
        got = f("13.7terry.lee@kgi.com", "7.6886 2 2181 8710 )淨負債比率(%)")
        self.assertEqual(got["email"]["value"], "terry.lee@kgi.com")
        self.assertNotIn("tel", got)
        # rating: ESG 評等 is not the rating; 區間持有 is printed whole
        self.assertNotIn("rating", f("ESG 評等社會(S) 經濟(E) 環境(E) 揭露(D)"))
        self.assertEqual(f("慧洋-KY投資評等區間持有,目標價78元;隱含漲幅 13.2%")["rating"]["value"], "區間持有")
        # title: 未評等 before the company; banners and a metadata title do not vote
        d = T.decompose_title("未評等瑞基(4171 TT)", {"filename": {"ticker": "4171", "company_names": ["瑞基"]}}, B, brd)
        self.assertEqual(d["segments"]["company"]["value"], "瑞基")
        self.assertTrue(T._title_junk("個股報告", "南亞(1303 TT)", "1303", B, "南亞"))
        self.assertTrue(T._title_junk("投資 顧問", "神達3706 TT (電子-電腦及週邊設備)", "3706", B, "神達"))
        self.assertFalse(T._title_junk("TSMC Overweight", "TSMC (2330 TT) Overweight", "2330", B, "TSMC"))
        seg = lambda v, st: {"value": v, "state": st}  # noqa: E731
        segments = {"ticker": seg("6533", "READ"), "company": seg("晶心科", "READ"), "rating_action": seg("", "NOT_PRINTED"),
                    "tp_change": seg("", "NOT_PRINTED"), "report_type": seg("", "NOT_PRINTED")}
        ctx = {"filename": {"ticker": "6533", "company_names": ["晶心科"], "broker": "CTBC", "date": "2025-12-08", "stem": "晶心科(6533,N,中立)-CTBC251208"},
               "engine": {"ticker": "6533", "company": "晶心科", "broker": "CTBC", "date": "2025-12-06", "target_price": 300.0, "title": "個股報告"},
               "basic": {}, "entities": {"target_price": {"current": 2026.0}}}
        cover = {"fields": {"date": {"value": "2025-12-06"}, "target_price": {"value": 300.0}, "broker": {"value": "CTBC"}}}
        parts = {p["part"]: p for p in T.verify({"text": "晶心科(6533 TT) 中立(Neutral)", "segments": segments, "source": "TOP25"}, cover, ctx, B, brd)}
        self.assertEqual(parts["cover.date"]["state"], "VERIFIED", "the page prints 12/06; the file is named on the send date")
        self.assertIn("檔名（晚 2 天，常是發送日，不比）", parts["cover.date"]["sources"])
        self.assertEqual(parts["cover.target_price"]["state"], "VERIFIED", "ENG396's 2026 is a year")
        self.assertIn("ENG396 全文（像年份，不計）", parts["cover.target_price"]["sources"])
        self.assertNotEqual(parts["title.text"]["state"], "CONFLICT", "個股報告 is the template banner")
        ctx["filename"]["date"] = "2025-12-20"
        parts = {p["part"]: p for p in T.verify({"text": "晶心科(6533 TT)", "segments": segments}, cover, ctx, B, brd)}
        self.assertEqual(parts["cover.date"]["state"], "CONFLICT", "two weeks later is not a send date")
        meta = {p["part"]: p for p in T.verify({"text": "tsmc(2330TW)-JPM-250718", "segments": segments, "source": "META"}, cover,
                                               dict(ctx, engine=dict(ctx["engine"], title="TSMC Overweight")), B, brd)}
        self.assertNotEqual(meta["title.text"]["state"], "CONFLICT", "a PDF metadata Title is not printed on the page")
        # short reports: no rating / TP printed is NOT_PRINTED
        sctx = {"filename": {"ticker": "7728", "company_names": ["光焱"], "broker": "CTBC", "date": "2026-09-18", "stem": "光焱(7728,Note)-CTBC260918"},
                "engine": {"ticker": "7728", "broker": "CTBC"}, "basic": {}, "entities": {}}
        parts = {p["part"]: p for p in T.verify({"text": "光焱(7728 TT)法說/座談摘要", "segments": segments}, {"fields": {}}, sctx, B, brd)}
        self.assertEqual((parts["cover.target_price"]["state"], parts["cover.rating"]["state"]), ("NOT_PRINTED", "NOT_PRINTED"))
        self.assertTrue(T._is_short_report("華南投顧-3038-全台-Memo-20251209", B))
        self.assertFalse(T._is_short_report("凱基投顧_1476 儒鴻_劉昃恩_20260519 henry", B), "nr inside a word is not NR")
        # evidence: 'FTPS' does not carry the label TP
        res = {"file": "a.pdf", "status": "OK", "cover": {"zones": [{"line": 35, "clean": "SS-PST、FTPS 等,對比同業"}], "fields": {}},
               "parts": [{"part": "cover.target_price", "state": "MISSING", "value": ""}]}
        self.assertEqual(T.fix_rows([res])[0]["evidence"], "")

    # [VRN-ID] VRN-TST012-FNC011 · TEST
    @unittest.skipUnless(def_has("fitz"), "PyMuPDF not installed")
    def test_messy_reports_end_to_end(self):
        R, _M = self.T.regions()
        with tempfile.TemporaryDirectory() as tmp:
            truths = self.T.build_fixtures(Path(tmp) / "fx")
            # 數字不寫死（寫死就得三個檔一起改）：**每一份寫出去的樣本都要有已知答案**，一份都不能漏
            self.assertEqual(sorted(tr["file"] for tr in truths),
                             sorted(f.name for f in (Path(tmp) / "fx").glob("*.pdf")))
            for tr in truths:
                path = Path(tmp) / "fx" / tr["file"]
                res = self.T.analyze(path, tr["file"], R.analyze(path, tr["file"]))
                self.assertEqual([(i, d) for i, ok, d in self.T.check_fixture(res, tr) if not ok], [], tr["file"])
                if tr.get("gain"):
                    cells = {f"{c['metric']}@{c['period']}": c for c in res["annual"]["cells"] if c["metric"]}
                    self.assertIsNone(cells["revenue@2024"]["value_before"], "G15 alone cannot read １，０００")
                    self.assertEqual(cells["revenue@2024"]["value"], 1000.0, "after TRIM it can")
            other = self.T.analyze(Path(tmp) / "none.pdf", "元大_半導體產業_20260901_產業報告.pdf")
            self.assertEqual(other["status"], "NOT_STOCK")


# [VRN-ID] VRN-TST012-CLS002 · CLASS
class def_AnalystIsNotTheCompanyTests(unittest.TestCase):
    """操作員 2026-10-19：「多數讀到分析師是錯的 修那個 不要放寬門檻」。

    `_company_before`（代號前面那一段）在凱基的標題上會取到人：`賴偉中(2637 TT)`。
    判斷借 VRN_Evidence_Core.is_analyst_name，名單由 ctx["analysts"] 帶進來 ——
    這裡不另寫一份姓氏表。
    """

    # [VRN-ID] VRN-TST012-FNC020 · LOGIC
    @classmethod
    def setUpClass(cls):
        cls.T = def_load("VRN_TitleTrim_v0100", VRN / "engine" / "VRN_TitleTrim_v0100.py")
        cls.B = cls.T.books()
        cls.brd = cls.T.first_page_engine().brd
        cls.T._LOCALDB = False

    TITLE = "賴偉中(2637 TT) 營運動能延續,評價仍具吸引力"

    # [VRN-ID] VRN-TST012-FNC021 · LOGIC
    def def_ctx(self, analysts):
        return {"filename": {"ticker": "2637", "company_names": ["慧洋"]}, "analysts": analysts}

    # [VRN-ID] VRN-TST012-FNC022 · TEST
    def test_without_the_name_list_the_person_is_read_as_the_company(self):
        """先證明這組測試抓得到東西：名單空著就是修之前的行為（公司 = 賴偉中）。"""
        d = self.T.decompose_title(self.TITLE, self.def_ctx([]), self.B, self.brd)
        self.assertEqual(d["segments"]["company"]["value"], "賴偉中")

    # [VRN-ID] VRN-TST012-FNC023 · TEST
    def test_the_analyst_is_not_the_company(self):
        d = self.T.decompose_title(self.TITLE, self.def_ctx(["賴偉中"]), self.B, self.brd)
        seg = d["segments"]["company"]
        self.assertEqual(seg["value"], "", "分析師不是公司")
        self.assertEqual(seg["state"], "NOT_PRINTED")
        self.assertEqual(seg.get("rejected"), "賴偉中", "擋掉誰要說出來")
        self.assertIn("分析師", seg.get("why", ""))

    # [VRN-ID] VRN-TST012-FNC024 · TEST
    def test_the_file_name_is_not_borrowed_as_the_title_reading(self):
        """標題沒印公司就是沒印：**不准**拿檔名頂上。

        頂上去的話「標題」這一票的值其實來自檔名，而 _vote 數的是群組數 ——
        標題＋檔名就會變成「兩個來源一致」，一個來源假裝成兩個。
        （同一條線我在 Codex P1 那條 thread 上拒絕過，自己這邊也不能做。）
        """
        d = self.T.decompose_title(self.TITLE, self.def_ctx(["賴偉中"]), self.B, self.brd)
        self.assertNotEqual(d["segments"]["company"]["value"], "慧洋", "檔名的答案不准算成標題讀到的")

    # [VRN-ID] VRN-TST012-FNC025 · TEST
    def test_the_core_view_does_not_swallow_the_rejected_name(self):
        """認出是人名之後那一段**還是「用掉了」** —— 不標的話核心觀點會把它收進去。

        2026-10-19 G18 鎖就是這樣擋下我這一改的連帶退步：
        `營運動能延續,評價仍具吸引力` → `賴偉中, 營運動能延續,評價仍具吸引力`。
        """
        before = self.T.decompose_title(self.TITLE, self.def_ctx([]), self.B, self.brd)
        after = self.T.decompose_title(self.TITLE, self.def_ctx(["賴偉中"]), self.B, self.brd)
        self.assertEqual(after["segments"]["core_view"]["value"], before["segments"]["core_view"]["value"],
                         "擋掉公司名不可以動到核心觀點")
        self.assertNotIn("賴偉中", after["segments"]["core_view"]["value"])

    # [VRN-ID] VRN-TST012-FNC026 · TEST
    def test_a_real_company_is_untouched(self):
        """同樣版型、代號前面是真公司（儒鴻）：一個字都不准動。"""
        d = self.T.decompose_title("儒鴻(1476 TT) 營運動能延續,評價仍具吸引力",
                                   {"filename": {"ticker": "1476", "company_names": ["儒鴻"]}, "analysts": ["劉昃恩", "王小明"]},
                                   self.B, self.brd)
        self.assertEqual(d["segments"]["company"]["value"], "儒鴻")
        self.assertEqual(d["segments"]["company"]["state"], "READ")

    # [VRN-ID] VRN-TST012-FNC027 · TEST
    def test_the_name_list_is_computed_even_without_a_first_page_result(self):
        """非 PDF 沒有首頁引擎結果時，檔名那一半照樣算得出來。

        2026-10-19 實測：PDF 的三檔都修好了，`.txt` 那一檔沒有 —— 名單是空的。
        ticker 一定要傳進去，不然 `國光生(4142,Note)` 的公司名會被當成人名擋掉。
        """
        names = self.T._analyst_names("3653健策凱基投顧 向子慧 (3).txt", {}, "3653")
        self.assertIn("向子慧", names, "首頁引擎沒跑也要算得出檔名那一半")
        self.assertEqual(self.T._analyst_names("國光生(4142,Note)-CTBC260917.pdf", {}, "4142"), [],
                         "貼著代號的那一段是公司，不是分析師")
        both = self.T._analyst_names("凱基投顧_2637 慧洋-KY_賴偉中_20260915.pdf", {"analyst_names": ["王小明"]}, "2637")
        self.assertEqual(sorted(both), ["王小明", "賴偉中"], "首頁帶上來的 ∪ 檔名算出來的")


# [VRN-ID] VRN-TST012-CLS003 · CLASS
class def_BrokerNotPrintedTests(unittest.TestCase):
    """操作員 2026-10-20：「把那 3 筆缺的補到 100% 過關」，以及回答 Codex P1 時給的位置規則：
    「券商名收穫縮寫同義字等一定位在 FILENAME 首頁 各頁下方小字體頁尾 或是報告後方小字體附錄等」。

    所以「沒印券商」要照那四個位置判。實測兩檔（3014TT-20231005.pdf、6933_AMAX-KY_個股介紹報告.pdf）
    四個位置全都沒有：對照組的跨頁重複帶是 `兆豐證券投資顧問MEGA Securities Research`，
    這兩檔的重複帶只有標題行本身。報告沒印就是沒印：記 NOT_PRINTED。

    **讀券商的門檻一條都沒動** —— 該在的位置有字卻讀不到，照舊 MISSING（那是字典缺口，要紅）。
    """

    # [VRN-ID] VRN-TST012-FNC028 · LOGIC
    @classmethod
    def setUpClass(cls):
        cls.T = def_load("VRN_TitleTrim_v0100", VRN / "engine" / "VRN_TitleTrim_v0100.py")
        cls.B = cls.T.books()
        cls.brd = cls.T.first_page_engine().brd
        cls.T._LOCALDB = False

    TITLE = {"text": "測試公司(3014 TT) 營運動能延續", "segments": {}}
    BAND = "跨頁重複(出現在 40/40 頁:頁眉 / 頁尾 / 浮水印)"

    # [VRN-ID] VRN-TST012-FNC029 · LOGIC
    @staticmethod
    def def_zones(*lines):
        return [{"line": i + 1, "zone": "TopHeader", "clean": t} for i, t in enumerate(lines)]

    # [VRN-ID] VRN-TST012-FNC033 · LOGIC
    def def_ctx(self, bands=(), stem="3014TT-20231005"):
        return {"filename": {"ticker": "3014", "stem": stem}, "engine": {}, "basic": {}, "entities": {},
                "bands": list(bands)}

    # [VRN-ID] VRN-TST012-FNC034 · LOGIC
    def def_cover(self):
        return {"zones": self.def_zones("測試公司(3014 TT) 營運動能延續",
                                        "分析師 王小明  analyst@example-research.com  (02)2181-8888"), "fields": {}}

    # [VRN-ID] VRN-TST012-FNC035 · LOGIC
    def def_state(self, ctx):
        parts = {p["part"]: p for p in self.T.verify(self.TITLE, self.def_cover(), ctx, self.B, self.brd)}
        return parts["cover.broker"]["state"]

    # [VRN-ID] VRN-TST012-FNC036 · TEST
    def test_the_word_test_comes_from_the_book_and_ignores_emails(self):
        slot = lambda cover, ctx=None: self.T._broker_slot_has_text({}, cover, ctx or {}, self.B)  # noqa: E731
        self.assertTrue(slot({"zones": self.def_zones("兆豐證券 研究部")}))
        self.assertTrue(slot({"zones": self.def_zones("KGI Securities Research")}))
        # e-mail／網址裡的字不算（冊 broker_alias_rule_r6）。不清掉的話每份報告都「有券商名」——
        # 我第一次量就是被 example-research.com 裡的 research 騙過去。
        self.assertFalse(slot({"zones": self.def_zones("分析師 王小明  analyst@example-research.com")}),
                         "e-mail 裡的 research 不算券商名")
        self.assertTrue(slot({"zones": self.def_zones("測試公司(3014 TT)")}, {"filename": {"stem": "凱基投顧_3014_20231005"}}),
                        "檔名也是該在的位置之一")
        self.assertTrue(slot({"zones": []}), "讀不到首頁就回 True：保守，維持 MISSING")

    # [VRN-ID] VRN-TST012-FNC037 · TEST
    def test_no_broker_in_any_of_the_four_places_is_not_printed(self):
        bands = [{"reason": self.BAND, "head": "測試公司(3014 TT)營運動能延續，評價仍具吸引"},
                 {"reason": "小字免責 / 聲明", "head": "本報告僅供參考，不構成投資建議。Disclosure: synthetic sample"}]
        self.assertEqual(self.def_state(self.def_ctx(bands)), "NOT_PRINTED", "報告沒印發行機構：不是沒讀到")

    # [VRN-ID] VRN-TST012-FNC038 · TEST
    def test_a_publisher_band_we_failed_to_read_stays_missing(self):
        """Codex PR #74 P1：報告在各頁頁尾印了不認得的券商名（`Jefferies`，後面沒接 Securities）。

        不靠詞表，靠結構：跨頁重複帶裡只要有「不是本報告標題」的文字，就表示發行機構帶存在
        而我們沒讀到 —— 那是字典缺口，不是合法缺席，不准灌進完成度。
        """
        bands = [{"reason": self.BAND, "head": "測試公司(3014 TT)營運動能延續，評價仍具吸引"},
                 {"reason": self.BAND, "head": "Jefferies"}]
        self.assertEqual(self.def_state(self.def_ctx(bands)), "MISSING",
                         "發行機構帶有字卻沒讀到：字典缺口，不准改判成沒印")

    # [VRN-ID] VRN-TST012-FNC039 · TEST
    def test_an_institution_word_on_the_page_keeps_missing(self):
        """首頁有機構字卻讀不到 —— 那也是真缺陷，照舊 MISSING。"""
        cover = {"zones": self.def_zones("測試公司(3014 TT) 營運動能延續", "某某證券投資顧問股份有限公司"), "fields": {}}
        parts = {p["part"]: p for p in self.T.verify(self.TITLE, cover, self.def_ctx(), self.B, self.brd)}
        self.assertEqual(parts["cover.broker"]["state"], "MISSING",
                         "頁上有「證券投資顧問」卻沒讀到券商：這是讀漏，不准改判成沒印")

    # [VRN-ID] VRN-TST012-FNC040 · TEST
    def test_a_disclaimer_that_names_the_issuer_keeps_missing(self):
        """後方小字附錄也是該在的位置之一：免責聲明裡寫了發行機構卻沒讀到，照舊 MISSING。"""
        bands = [{"reason": self.BAND, "head": "測試公司(3014 TT)營運動能延續，評價仍具吸引"},
                 {"reason": "小字免責 / 聲明", "head": "本報告由某某證券投資顧問股份有限公司提供"}]
        self.assertEqual(self.def_state(self.def_ctx(bands)), "MISSING")


# [VRN-ID] VRN-TST012-CLS004 · CLASS
class def_CloseNextToTargetTests(unittest.TestCase):
    """第七輪實測：`cover.current_price` 在 59 份個股報告**全部**只有首頁引擎一個來源，永遠對不上第二來源。

    同一行印著「投資評等:賣出 目標價:NT$182.5 收盤價:NT$140.4」，目標價讀得到、收盤價讀不到 ——
    同一行、同一套讀法，一個讀到一個沒讀到，這個不對稱就是缺陷。

    根因：現價守門「前後 14 字內有 target／目標／12M 的不是現價」，**後面**那側本來就是錨定的
    （`re.match`），**前面**那側卻是 14 字內到處找（`re.search`）。TRIM 把連續空白收成一個空白之後，
    前一欄自己的「目標價:NT$182.5」整段落進「收盤價」前面那 14 字，把收盤價殺掉。

    門檻一個字都沒放寬：冊上那串字還是那串字，只是改成要**緊鄰**標籤 —— 和後面那側同一把尺。
    冊上自己舉的兩個例子（`12M price target`、`52 週股價 (低 \\ 高)`）照樣擋，下面逐條驗。
    """

    # [VRN-ID] VRN-TST012-FNC041 · LOGIC
    @classmethod
    def setUpClass(cls):
        cls.T = def_load("VRN_TitleTrim_v0100", VRN / "engine" / "VRN_TitleTrim_v0100.py")
        cls.B = cls.T.books()
        cls.T._LOCALDB = False

    # [VRN-ID] VRN-TST012-FNC042 · IO
    def def_read(self, *lines):
        """走真正那條路：`cover_fields`，不是直接戳守門函式（驗了函式不等於驗了那條路）。"""
        page = {"height": 842.0,
                "lines": [{"text": t, "top": 150.0 + 16 * i, "size": 8.0, "bbox": [420.0, 150.0 + 16 * i, 560.0, 158.0 + 16 * i]}
                          for i, t in enumerate(lines)]}
        fields = self.T.cover_fields(page, {"joined": []}, self.B, None)["fields"]
        return {k: (fields.get(k) or {}).get("value") for k in ("target_price", "current_price")}

    # [VRN-ID] VRN-TST012-FNC043 · TEST
    def test_the_close_on_the_same_line_as_the_target_is_read(self):
        """59/59 的真實版型：一行三欄。兩個價都要讀到，而且各是各的。"""
        got = self.def_read("投資評等：賣出    目標價：NT$182.5    收盤價：NT$140.4")
        self.assertEqual(got, {"target_price": 182.5, "current_price": 140.4},
                         "同一行印的收盤價被前一欄的『目標價』誤殺了")

    # [VRN-ID] VRN-TST012-FNC044 · TEST
    def test_trim_collapsing_the_spaces_does_not_change_the_answer(self):
        """TRIM 把多空白收成一個空白 —— 那正是把『目標價』推進 14 字窗的手。收完照樣要讀到。"""
        self.assertEqual(self.def_read("投資評等:買進 目標價:NT$190.0 收盤價:NT$146.2"),
                         {"target_price": 190.0, "current_price": 146.2})

    # [VRN-ID] VRN-TST012-FNC045 · TEST
    def test_a_twelve_month_price_target_is_still_not_a_close(self):
        """冊上 `current_price_rule` 自己舉的例子：`12M price target NT$4,200` 是目標價，不是現價。"""
        self.assertIsNone(self.def_read("12M price target NT$4,200")["current_price"],
                          "門檻被放寬了：12M 的目標價被當成現價")

    # [VRN-ID] VRN-TST012-FNC046 · TEST
    def test_a_twelve_month_target_price_is_still_not_a_close(self):
        """`12M target price`：把 target 擺在標籤前面也一樣擋 —— 前側看的就是緊鄰標籤那一段。"""
        self.assertIsNone(self.def_read("12M target price NT$200")["current_price"])

    # [VRN-ID] VRN-TST012-FNC047 · TEST
    def test_a_fifty_two_week_range_is_still_not_a_close(self):
        """冊上 `current_price_rule_r6`：「52 週股價 (低 \\ 高) (NT$): 318.0 -466.0」是一年區間（儒鴻讀成 318、貿聯讀成 600）。"""
        self.assertIsNone(self.def_read("52 週股價 (低 \\ 高) (NT$): 318.0 -466.0")["current_price"])

    # [VRN-ID] VRN-TST012-FNC048 · TEST
    def test_the_word_has_to_touch_the_label(self):
        """同一個字 `12M`：緊鄰標籤 → 擋；隔著另一個欄位的標籤和數字 → 不算。這就是這次改的那條線。"""
        self.assertIsNone(self.def_read("12M 收盤價:NT$140.4")["current_price"], "緊鄰標籤的 12M 要擋")
        self.assertEqual(self.def_read("12M 目標價:NT$182.5 收盤價:NT$140.4")["current_price"], 140.4,
                         "那個 12M 是前一欄目標價的，不是收盤價的")

    # [VRN-ID] VRN-TST012-FNC050 · TEST
    def test_punctuation_between_the_word_and_the_label_still_blocks(self):
        """Codex PR #75 P2：分隔符號不准列舉。

        `Target-Price`、`Target (Price):`、`12M-Price`、`52週-股價` 裡那個字還是緊鄰標籤，
        中間只是一個沒被列舉到的標點 —— 列舉版會把目標價當成現價讀進來（實測前三個都讀成 4200）。
        判準改成問「間隔裡還有沒有字母、數字、漢字」，就不必數標點。
        """
        for text in ("Target-Price NT$4,200", "Target (Price): NT$4,200", "12M-Price NT$4,200",
                     "52週-股價 318", "(12M) Price NT$4,200"):
            self.assertIsNone(self.def_read(text)["current_price"], text)

    # [VRN-ID] VRN-TST012-FNC051 · TEST
    def test_the_word_after_the_label_is_judged_the_same_way(self):
        """兩側同一把尺（護欄：修前修後都綠）。

        `Price-Target` 在修之前就取不到值，但那是**取值那一段剛好湊不出數字**，不是守門擋的；
        現在是守門擋的。最後一條確認沒有擋過頭：後面那個目標價屬於另一欄，收盤價照讀。
        """
        self.assertIsNone(self.def_read("Price-Target NT$4,200")["current_price"])
        self.assertIsNone(self.def_read("Price (Target): NT$4,200")["current_price"])
        self.assertEqual(self.def_read("收盤價:NT$140.4 目標價:NT$182.5")["current_price"], 140.4,
                         "後面那個目標價是另一欄的，不是這個標籤的")

    # [VRN-ID] VRN-TST012-FNC049 · TEST
    def test_the_rule_in_the_book_says_adjacent(self):
        """冊與碼不准各說各話（九頭龍）：冊上 `current_price_rule` 要寫明是緊鄰，不是 14 字內到處找。"""
        self.assertIn("緊鄰", self.B.book["cover"]["current_price_rule"])
        self.assertIn("收盤價", self.B.book["cover"]["current_price_rule_r7"])


# [VRN-ID] VRN-TST012-CLS005 · CLASS
class def_PageCodesReachTheRecordTests(unittest.TestCase):
    """首頁印的 `Bloomberg 6873 TT  Yahoo 6873.TW`：TRIM 這一側本來就讀到了（`title.market` 用的就是同一批 hits），
    但只留下市場別交出去。代號紀錄（G20）於是只剩首頁引擎一條讀法 —— 59 份報告裡 58 筆 SINGLE、永遠鎖不住。

    這一組驗的是**那條路**，不只是函式：TitleTrim 交出來的鍵，要正好是 TickerRecord 讀的那個鍵
    （`FPE_KEYS_FOR_TRIM` 那次就是栽在這裡：函式對了，鍵沒接上）。
    """

    # [VRN-ID] VRN-TST012-FNC052 · LOGIC
    @classmethod
    def setUpClass(cls):
        cls.T = def_load("VRN_TitleTrim_v0100", VRN / "engine" / "VRN_TitleTrim_v0100.py")
        cls.R = def_load("VRN_TickerRecord_v0100", VRN / "engine" / "VRN_TickerRecord_v0100.py")
        cls.B = cls.T.books()
        cls.T._LOCALDB = False

    LINES = ["泓德能源(6873 TT) 營運動能延續", "報告日期：2025/08/19    Bloomberg 6873 TT    Yahoo 6873.TW"]

    # [VRN-ID] VRN-TST012-FNC053 · LOGIC
    def def_cover(self):
        page = {"height": 842.0,
                "lines": [{"text": t, "top": 80.0 + 24 * i, "size": 12.0, "bbox": [40.0, 80.0 + 24 * i, 500.0, 92.0 + 24 * i]}
                          for i, t in enumerate(self.LINES)]}
        return self.T.cover_fields(page, {"joined": []}, self.B, None)

    # [VRN-ID] VRN-TST012-FNC054 · TEST
    def test_trim_hands_over_the_printed_codes_in_the_engine_s_own_shape(self):
        """形狀照首頁引擎的 page_codes（raw / core / platform / market），不另造一種。"""
        codes = (self.def_cover()["fields"].get("page_codes") or {}).get("codes") or []
        got = {c["platform"]: c for c in codes}
        self.assertEqual(sorted(got), ["bloomberg", "yfinance"], codes)
        self.assertEqual((got["yfinance"]["raw"], got["yfinance"]["core"], got["yfinance"]["market"]), ("6873.TW", "6873", "TWSE"))
        self.assertEqual((got["bloomberg"]["raw"], got["bloomberg"]["core"]), ("6873 TT", "6873"))

    # [VRN-ID] VRN-TST012-FNC055 · TEST
    def test_the_record_locks_the_codes_from_the_two_readings(self):
        """整條路：TitleTrim 的 cover → 代號紀錄。兩條讀法一致 → VERIFIED（原本是 SINGLE）。"""
        cover = self.def_cover()
        res = {"file": "x.pdf", "status": "OK", "cover": cover,
               "parts": [{"part": "title.ticker", "value": "6873", "state": "VERIFIED"}]}
        fpe = {"page_codes": [{"raw": "6873.TW", "core": "6873", "platform": "yfinance", "market": "TWSE"},
                              {"raw": "6873 TT", "core": "6873", "platform": "bloomberg", "market": ""}]}
        rec = self.R.record_of(res, {"LocalDBStatus": "ABSENT"}, fpe, {})
        self.assertEqual(rec["yfinance_ticker"]["state"], "VERIFIED", rec["yfinance_ticker"])
        self.assertEqual(rec["bloomberg_ticker"]["state"], "VERIFIED", rec["bloomberg_ticker"])

    # [VRN-ID] VRN-TST012-FNC057 · TEST
    def test_a_code_printed_only_inside_brackets_still_counts(self):
        """Codex PR #76 P2：`鴻海 (2317.TW)`、`TSMC (2330 TT)` 常常是整頁唯一印的碼。

        `_ticker_hits` 先用 paren_rx 吃掉它、壓住後面重疊的 yahoo／bloomberg 比對，`how` 停在 "paren" ——
        漏掉它，代號紀錄就還是只有首頁引擎一條讀法。
        """
        self.LINES = ["鴻海 (2317.TW) 法說會摘要"]
        got = {c["platform"]: c for c in (self.def_cover()["fields"].get("page_codes") or {}).get("codes") or []}
        self.assertEqual((got["yfinance"]["raw"], got["yfinance"]["market"]), ("2317.TW", "TWSE"), got)
        self.LINES = ["TSMC (2330 TT) 先進製程"]
        got = {c["platform"]: c for c in (self.def_cover()["fields"].get("page_codes") or {}).get("codes") or []}
        self.assertEqual(got["bloomberg"]["raw"], "2330 TT", got)

    # [VRN-ID] VRN-TST012-FNC058 · TEST
    def test_brackets_that_are_not_platform_codes_stay_out(self):
        """認不認得問冊上同一組式子，不是看到括號就收：`(4142,Note)`、`(2637-KY)` 不是平台碼。"""
        for text in ("國光生(4142,Note)-CTBC260917", "慧洋-KY(2637-KY) 速報", "泓德能源(6873) 營運動能延續"):
            self.LINES = [text]
            self.assertEqual((self.def_cover()["fields"].get("page_codes") or {}).get("codes"), None, text)

    # [VRN-ID] VRN-TST012-FNC056 · TEST
    def test_the_key_titletrim_publishes_is_the_key_the_record_reads(self):
        """鍵名不准兩邊各寫各的：從代號紀錄的原始碼把它讀的鍵抓出來，必須是 TitleTrim 交出來的那一個。"""
        source = (VRN / "engine" / "VRN_TickerRecord_v0100.py").read_text(encoding="utf-8")
        self.assertIn('.get("page_codes") or {}).get("codes")', source,
                      "代號紀錄換了鍵名就要同步改 TitleTrim，不然這條路又斷掉")
        self.assertIn("page_codes", self.def_cover()["fields"])


# [VRN-ID] VRN-TST012-CLS006 · CLASS
class def_ContactLinesAreNotTitlesTests(unittest.TestCase):
    """2026-10-20 第二輪：MS / CLSA 分析師欄的電話被當成標題（電話裡的四碼算成代號）；瑞基同一列右邊的「未評等」排到左邊。"""

    # [VRN-ID] VRN-TST012-FNC059 · LOGIC
    @classmethod
    def setUpClass(cls):
        cls.T = def_load("VRN_TitleTrim_v0100", VRN / "engine" / "VRN_TitleTrim_v0100.py")
        cls.B = cls.T.books()

    # [VRN-ID] VRN-TST012-FNC060 · TEST
    def test_a_phone_line_is_not_a_title_and_its_digits_are_not_a_ticker(self):
        T, B = self.T, self.B
        for s in ("+886 2 2730-2865", "+852 2848-7310", "Charlie.Chan@morganstanley.com"):
            self.assertTrue(T._contact_line(s, B), s)
        for s in ("Wistron (3231.TW)", "Read-across from AWS re:Invent", "7.6886 2 2181 8710"):
            self.assertFalse(T._contact_line(s, B), s)
        self.assertEqual(T._ticker_hits("+886 2 2326 8179", B), [])
        self.assertEqual([h["code"] for h in T._ticker_hits("Wistron (3231.TW)", B)], ["3231"])

    # [VRN-ID] VRN-TST012-FNC061 · TEST
    def test_title_lines_join_across_the_analyst_column_and_stop_at_a_contact_line(self):
        T, B = self.T, self.B
        line = lambda i, t, x0, x1, top, size: {"text": t, "size": size, "bold": False, "bbox": [x0, top, x1, top + size], "top": top, "x0": x0}  # noqa: E731
        ms = {"height": 800.0, "width": 600.0, "meta_title": "", "lines": [
            line(0, "Delta Electronics Inc. | Asia Pacific", 42, 257, 80, 14.0), line(1, "Sharon Shih", 384, 428, 90, 8.5),
            line(2, "What's Next?  Business", 42, 273, 107, 24.0), line(3, "+886 2 2730-2865", 528, 570, 110, 5.25),
            line(4, "Samantha Chen", 384, 441, 122, 8.5), line(5, "Extension to Power AI", 42, 261, 137, 24.0),
            line(6, "+886 2 2730-2876", 528, 570, 142, 5.25)]}
        self.assertEqual(T.pick_title(ms, {"filename": {}}, B)["text"], "What's Next? Business - Extension to Power AI")
        clsa = {"height": 800.0, "width": 600.0, "meta_title": "", "lines": [
            line(0, "Expect better-than-feared 4Q25 and promising 2026 outlook", 184, 498, 145, 11.0),
            line(1, "+886 2 2326 8179", 184, 260, 156, 11.0), line(2, "We forecast sales to be NT$85.0bn", 184, 560, 167, 11.0)]}
        self.assertNotIn("8179", T.pick_title(clsa, {"filename": {}}, B)["text"])

    # [VRN-ID] VRN-TST012-FNC062 · TEST
    def test_the_code_box_is_not_the_title_and_the_rating_box_does_not_join_it(self):
        """JPM：代號欄「2330.TW, 2330 TT」分數贏過「TSMC」，公司就讀成 Overweight；華南標題接到「投資建議」那一行；
        瑞基同一列、同字級的「未評等」在右邊，要照左到右併進標題。"""
        T, B = self.T, self.B
        self.assertTrue(T._label_led("投資建議", B) and T._label_led("Price (17 Jul 25):NT$1130.0", B) and T._label_led("Rating: Buy", B))
        self.assertFalse(T._label_led("TP raised to NT$1,350 on AI demand", B), "以標籤字開頭的句子還是標題的一部分")
        line = lambda t, x0, x1, top, size: {"text": t, "size": size, "bold": False, "bbox": [x0, top, x1, top + size], "top": top, "x0": x0}  # noqa: E731
        jpm = {"height": 800.0, "width": 600.0, "meta_title": "", "lines": [
            line("JPMORGAN", 96, 213, 79, 12.25), line("TSMC", 96, 147, 140, 18.27), line("Overweight", 406, 476, 142, 12.79),
            line("2330.TW, 2330 TT", 406, 466, 160, 7.31), line("Margin test passed; On to 2026 with strong AI and N2", 96, 378, 167, 11.87)]}
        self.assertEqual(T.pick_title(jpm, {"filename": {}}, B)["text"], "TSMC")
        ruiji = {"height": 800.0, "width": 600.0, "meta_title": "", "lines": [
            line("未評等", 422, 470, 124.8, 16.0), line("瑞基(4171 TT)", 216, 330, 126.0, 16.0)]}
        self.assertEqual(T.pick_title(ruiji, {"filename": {}}, B)["text"], "瑞基(4171 TT) 未評等")

    # [VRN-ID] VRN-TST012-FNC063 · TEST
    def test_a_company_only_title_takes_the_headline_below_it(self):
        """CLSA：最大字只有「Wiwynn」，標題在下面同一欄的「Smoother transition」，中間夾著評等價格行；
        核心觀點不收公司名、也不收 -KY 上市註記；首頁引擎讀成同一列兩欄（TSMC Overweight）也算同一行標題。"""
        T, B = self.T, self.B
        line = lambda t, x0, x1, top, size: {"text": t, "size": size, "bold": False, "bbox": [x0, top, x1, top + size], "top": top, "x0": x0}  # noqa: E731
        body = [line("We forecast Wiwynn's September sales to be NT$85.0bn", 184, 562, 161 + 12 * k, 10.08) for k in range(6)]
        clsa = {"height": 800.0, "width": 600.0, "meta_title": "", "lines": [
            line("Wiwynn", 184, 308, 24, 31.92), line("NT$3,300.00 - OUTPERFORM", 184, 367, 64, 12.96),
            line("Smoother transition", 185, 387, 118, 22.08), line("Kevin SW Chen", 33, 120, 129, 12.0)] + body}
        self.assertEqual(T.pick_title(clsa, {"filename": {}}, B)["text"], "Wiwynn - Smoother transition")
        core = lambda t, ctx: T.decompose_title(t, ctx, B)["segments"]["core_view"]["value"]  # noqa: E731
        self.assertEqual(core("Wiwynn - Smoother transition", {"engine": {"company": "Wiwynn"}}), "Smoother transition")
        self.assertEqual(core("慧洋-KY - 獲利將創四年新高,但評價已高", {"filename": {"company_names": ["慧洋"]}}), "獲利將創四年新高,但評價已高")
        self.assertEqual(core("KYEC rallies on AI test demand", {}), "KYEC rallies on AI test demand", "KY 開頭的英文字不是上市註記")

# [VRN-ID] VRN-TST012-CLS007 · CLASS
class def_HowManyAgreedIsAlwaysOnTheRecordTests(unittest.TestCase):
    """有兩個以上來源的部位，一定要說「幾組讀成同一個」—— 不然跨來源對照看不到它。

    操作員 2026-10-19：「相互對照兩個以上相同即算對照成功」。那條規則讀的是部位上的 `agree`
    （支持採用值的來源群組數），`_vote` 會寫，但**手工組 part 的四條路都沒寫**。
    實測 2026-10-20：612 個 `annual.*` 部位 state=VERIFIED、三個來源同值，`agree` 卻是空的，
    跨來源對照因此把它們全歸進「別條路徑」—— 對上印 699，實際上是 1311。
    """

    # [VRN-ID] VRN-TST012-FNC064 · LOGIC
    @classmethod
    def setUpClass(cls):
        cls.T = def_load("VRN_TitleTrim_v0100", VRN / "engine" / "VRN_TitleTrim_v0100.py")
        cls.B = cls.T.books()
        cls.brd = cls.T.first_page_engine().brd
        cls.T._LOCALDB = False

    # [VRN-ID] VRN-TST012-FNC065 · LOGIC
    def def_annual(self):
        """表三列 × 三期；資料庫引擎讀到其中兩列，稅後淨利 2025 讀成別的數字。"""
        result = {"file": "t.pdf", "status": "OK", "sentences": [], "checks": [], "rows": [], "tables": [
            {"anchor": "p3·T1", "subcategory": "", "title": "", "columns": ["項目 (NT$ 百萬元)", "2024A", "2025E", "2026E"],
             "rows": [["營收", "11,507", "13,661", "16,293"], ["稅後淨利", "1,380", "1,707", "2,118"], ["毛利率(%)", "38.5", "39.2", "40.1"]]}]}
        db = [{"MetricNameRaw": "營收", "PeriodLabelRaw": "2024A", "Value": 11507.0},
              {"MetricNameRaw": "營收", "PeriodLabelRaw": "2025E", "Value": 13661.0},
              {"MetricNameRaw": "稅後淨利", "PeriodLabelRaw": "2024A", "Value": 1380.0},
              {"MetricNameRaw": "稅後淨利", "PeriodLabelRaw": "2025E", "Value": 1770.0}]
        return {p["part"]: p for p in self.T.annual_parts(self.T.annual(result, self.B, db))}

    # [VRN-ID] VRN-TST012-FNC066 · TEST
    def test_the_annual_path_says_how_many_readers_agreed(self):
        """年度財報這條路以前只寫 state 不寫 agree —— 兩條讀法對上的事實落不到紙上。"""
        parts = self.def_annual()
        both = parts["annual.revenue@2024"]
        self.assertEqual(both["state"], "VERIFIED")
        self.assertEqual(both["agree"], 2, "表格與資料庫引擎讀到同一個數字,就是兩組對上")
        alone = parts["annual.gross_margin@2026"]
        self.assertEqual(alone["state"], "SINGLE")
        self.assertEqual(alone["agree"], 1, "只有表格讀到,就是一組")
        clash = parts["annual.net_income@2025"]
        self.assertEqual(clash["state"], "CONFLICT")
        self.assertEqual(clash["agree"], 1, "讀法不一致的時候,支持採用值的只有表格那一組")

    # [VRN-ID] VRN-TST012-FNC067 · TEST
    def test_the_count_matches_the_sources_it_shows(self):
        """數字不能和它自己列出來的來源各說各話。"""
        for name, part in self.def_annual().items():
            with self.subTest(part=name):
                shown = [v for v in (part.get("sources") or {}).values() if v not in (None, "")]
                self.assertLessEqual(part["agree"], len(shown), name)
                self.assertGreaterEqual(part["agree"], 1, name)

    # [VRN-ID] VRN-TST012-FNC068 · TEST
    def test_a_title_segment_the_title_did_not_print_keeps_the_count(self):
        """標題沒印就不採用它的值,但各來源讀到什麼與幾組一致要一起留著。"""
        voted = self.T._vote("title.rating_action", [("fn", "檔名", "NOT_RATED"),
                                                     ("eng", "首頁引擎", "MAINTAIN")], lambda a, b: a == b)
        kept = self.T._title_only({"rating_action": {"state": "NOT_PRINTED"}}, "rating_action", voted)
        self.assertEqual(kept["state"], "NOT_PRINTED")
        self.assertEqual(len(kept["sources"]), 2, "兩個來源照列")
        self.assertEqual(kept["agree"], voted["agree"], "_vote 算過的數字不准在重組 dict 的時候掉了")

    # [VRN-ID] VRN-TST012-FNC069 · TEST
    def test_the_database_backed_parts_say_it_too(self):
        """公司名取資料庫、現價取資料庫這兩條路也是手工組 part —— 同一個洞。"""
        comp = self.T._db_company_part("泓德能源", [("title", "標題", "泓德能源"), ("fn", "檔名", "泓德能源")], self.B)
        self.assertEqual(comp["state"], "VERIFIED")
        self.assertEqual(comp["agree"], 3, "資料庫一組 + 標題 + 檔名")
        lone = self.T._db_company_part("泓德能源", [], self.B)
        self.assertEqual((lone["state"], lone["agree"]), ("SINGLE", 1))
        quote = {"basis": ("2025-08-18", 208.0), "same": None, "basis_adj": ("2025-08-18", 205.0),
                 "same_adj": None, "latest_adj": ("2025-08-19", 206.0)}
        price = self.T._db_price_part(quote, [("cover", "首頁", 208.0)], lambda a, b: float(a) == float(b))
        self.assertEqual(price["state"], "VERIFIED")
        self.assertEqual(price["agree"], 2, "資料庫一組 + 首頁讀到同一個收盤價")

    # [VRN-ID] VRN-TST012-FNC070 · TEST
    def test_no_part_with_two_sources_leaves_the_count_blank(self):
        """守門：這一支不是為了某一條路寫的 —— 任何一條造部位的路漏了 agree 都要在這裡紅。"""
        made = list(self.def_annual().values())
        made.append(self.T._db_company_part("泓德能源", [("title", "標題", "泓德能源")], self.B))
        made.append(self.T._title_only({"tp_change": {"state": "NOT_PRINTED"}}, "tp_change",
                                       self.T._vote("title.tp_change", [("fn", "檔名", "208"), ("eng", "首頁引擎", "208")],
                                                    lambda a, b: a == b)))
        blind = [p["part"] for p in made
                 if len([v for v in (p.get("sources") or {}).values() if v not in (None, "")]) >= 2
                 and not str(p.get("agree") if p.get("agree") is not None else "").strip().isdigit()]
        self.assertEqual(blind, [], "有兩個以上來源卻沒說幾組對上,跨來源對照就看不到它")


# [VRN-ID] VRN-TST012-CLS008 · CLASS
class def_UpsideThatVrnRecomputedIsNotNotPrintedTests(unittest.TestCase):
    """算得出來的上漲空間，部位自己也不可以記成「報告沒印」。

    實測 2026-10-21（107 檔）：`vrn_trim_parts` 的 `cover.upside` 59/59 都是 `value=""` ·
    `state=NOT_PRINTED`，數字只活在 why 那句中文「沒印；VRN 重算 29.99%（def03）」。
    第十七輪把代號紀錄那一欄改成 DERIVED 了（`vrn_ticker_record.upside_pct` 59/59 DERIVED、
    有值），四重點與 `basic_info.UpsideDownsidePct` 也早就印同一個數字 —— **部位這一層沒跟上**，
    所以操作員每一輪在終端看到的部位矩陣印「上漲% –59」＝報告沒印。
    第十七輪自己寫下的結語就是「同一個事實在三張表上要說同一句話」：這是第四張。
    """

    # [VRN-ID] VRN-TST012-FNC071 · LOGIC
    @classmethod
    def setUpClass(cls):
        cls.T = def_load("VRN_TitleTrim_v0100", VRN / "engine" / "VRN_TitleTrim_v0100.py")
        cls.B = cls.T.books()
        cls.brd = cls.T.first_page_engine().brd
        cls.T._LOCALDB = False

    # [VRN-ID] VRN-TST012-FNC072 · LOGIC
    def def_parts(self, tp=208.0, cp=160.0, printed_upside=None):
        seg = lambda v, st: {"value": v, "state": st}  # noqa: E731
        segments = {"ticker": seg("6873", "READ"), "company": seg("泓德能源", "READ"), "rating_action": seg("", "NOT_PRINTED"),
                    "tp_change": seg("", "NOT_PRINTED"), "report_type": seg("", "NOT_PRINTED")}
        fields = {"date": {"value": "2025-08-19"}}
        if tp is not None:
            fields["target_price"] = {"value": tp}
        if cp is not None:
            fields["current_price"] = {"value": cp}
        if printed_upside is not None:
            fields["upside"] = {"value": printed_upside}
        ctx = {"filename": {"ticker": "6873", "company_names": ["泓德能源"], "broker": "MEGA", "date": "2025-08-19", "stem": "x"},
               "engine": {"ticker": "6873", "company": "泓德能源", "broker": "MEGA", "date": "2025-08-19",
                          "target_price": tp, "current_price": cp},
               "basic": {}, "entities": {}, "db": None}
        return {p["part"]: p for p in self.T.verify({"text": "泓德能源(6873 TT)", "segments": segments},
                                                    {"zones": [], "fields": fields}, ctx, self.B, self.brd)}

    # [VRN-ID] VRN-TST012-FNC073 · TEST
    def test_not_printed_but_recomputed_is_derived_on_the_part_itself(self):
        up = self.def_parts()["cover.upside"]
        self.assertEqual(up["state"], "DERIVED", "算得出來就不是「報告沒印」—— 代號那幾欄早就有這一格")
        self.assertEqual(up["value"], 30.0, "(208 − 160) ÷ 160 = 30.00%")

    # [VRN-ID] VRN-TST012-FNC074 · TEST
    def test_the_number_does_not_live_only_in_the_prose(self):
        """守門：why 裡寫得出那個數字，欄位就不可以是空的 —— 下游要驗只能去解析散文。"""
        up = self.def_parts()["cover.upside"]
        self.assertRegex(str(up.get("why") or ""), r"重算", "沒印而算得出來時，why 本來就說了重算")
        self.assertNotEqual(str(up.get("value") or "").strip(), "", "算出來的數字要在欄位裡，不是只在那句中文裡")
        self.assertIn("VRN 重算", up.get("sources") or {}, "重算是一條讀法，要掛在 sources 上，跨來源對照才看得到")

    # [VRN-ID] VRN-TST012-FNC075 · TEST
    def test_a_printed_upside_still_wins(self):
        """紙上印了就用紙上的，一個字都不改。"""
        up = self.def_parts(printed_upside=29.8)["cover.upside"]
        self.assertEqual(up["value"], 29.8, "印了就用印的")
        self.assertIn(up["state"], ("VERIFIED", "SINGLE"), "印了的那一條照舊走比對，不走 DERIVED")

    # [VRN-ID] VRN-TST012-FNC076 · TEST
    def test_without_a_target_or_a_price_it_really_is_not_printed(self):
        """不過度延伸：算不出來的時候，NOT_PRINTED 才是誠實的答案。"""
        for kw in ({"tp": None}, {"cp": None}):
            with self.subTest(**kw):
                up = self.def_parts(**kw)["cover.upside"]
                self.assertEqual(up["state"], "NOT_PRINTED", "沒目標價或沒現價就真的算不出來")
                self.assertEqual(str(up.get("value") or "").strip(), "")

    # [VRN-ID] VRN-TST012-FNC077 · TEST
    def test_the_part_and_the_ticker_record_say_the_same_number(self):
        """同一個事實在兩張表上說同一句話：部位交出去的值，就是代號紀錄印出來的值。"""
        R = def_load("VRN_TickerRecord_v0100", VRN / "engine" / "VRN_TickerRecord_v0100.py")
        parts = self.def_parts()
        res = {"file": "x.pdf", "status": "OK", "parts": list(parts.values())}
        rec = R.record_of(res, {"LocalDBStatus": "ABSENT"}, {}, {})["upside_pct"]
        self.assertEqual(rec["state"], parts["cover.upside"]["state"], "兩張表的狀態要一樣")
        self.assertEqual(rec["value"], parts["cover.upside"]["value"], "兩張表的數字要一樣")
        self.assertNotIn("首頁印的", rec.get("why") or "", "首頁沒印的值不可以寫成「首頁印的」")


if __name__ == "__main__":
    unittest.main()
