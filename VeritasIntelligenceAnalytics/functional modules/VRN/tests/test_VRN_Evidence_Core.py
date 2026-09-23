# -*- coding: utf-8 -*-
"""Unit tests for VRN_Evidence_Core (synthetic lines only; no report content is stored in the repo).

Each case mirrors a layout measured on the 2026-09-23 real corpus, written with invented names and
example domains: CTBC filler spaces, Daiwa-Cathay e-mail domain, MEGA label rows, KGI rating boxes,
JPM '(Dec-25)' targets, the 批679 deny list, unruled and transposed financial tables."""

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

ENGINE = Path(__file__).resolve().parents[1] / "engine"


def def_load(name):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, ENGINE / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def def_glyphs(text, x0=10.0, size=8.0, top=100.0, advance=None, gap=0.0):
    """One row of glyphs; `advance` is the glyph width, `gap` the extra space after each glyph."""
    out, x = [], x0
    for ch in text:
        width = advance if advance is not None else size * (1.0 if ord(ch) > 255 else 0.5)
        out.append({"text": ch, "x0": x, "x1": x + width, "top": top, "bottom": top + size, "size": size, "fontname": "F"})
        x += width + gap
    return out


ALIASES = {
    "KGI": ["凱基", "凱基投顧", "kgi"], "CTBC": ["中信", "中國信託", "ctbc", "中信金"], "CATHAY": ["國泰", "國泰證期", "cathay"],
    "DAIWA": ["大和", "daiwa"], "CLSA": ["clsa", "里昂"], "CAPITAL": ["群益", "capital"], "FIRST": ["第一", "first"],
    "MS": ["morgan stanley", "ms"], "MEGA": ["兆豐", "mega"], "YUANTA": ["元大"],
}
# 批728 (mother): denied names are never spelled out here -- the purge gate (CGC_MDL177 verify) counts a spelled-out
# denied name as live data.  The deny-list test reads them from CGC_MDL177 itself (CN_CANON / CN_ALIAS) at run time.


class def_EvidenceCoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.C = def_load("VRN_Evidence_Core")

    # ---- mother 批728: one deny gate, longest wins (overlay deny_keys + CGC_MDL177) -----------------
    def test_one_deny_gate_longest_wins(self):
        C = self.C
        phrases = C.deny_phrases()
        if not phrases:
            self.skipTest("mother deny books absent")
        table = {"JPM": ["摩根大通", "j.p. morgan"], "MS": ["摩根士丹利", "morgan stanley"], "CTBC": ["中信", "中信投顧", "ctbc"]}
        leaky = dict(table)
        leaky["JPM"] = table["JPM"] + [p for p in phrases if len(p) == 2 and p.startswith("摩")]   # a book that still carries them
        for text in [f"本報告由{p}研究部出具" for p in phrases]:
            self.assertIsNone(C.broker_evidence([text], leaky)["broker"], "deny list leaked: " + text)
        self.assertEqual(C.broker_evidence(["摩根士丹利證券研究部"], leaky)["broker"], "MS", "a longer legitimate alias keeps its span")
        self.assertEqual(C.broker_evidence(["本報告由摩根大通發布"], leaky)["broker"], "JPM")
        self.assertEqual(C.broker_evidence(["中信投顧研究部"], table)["broker"], "CTBC")
        shadow_probe = [p for p in phrases if len(p) > 2 and p.startswith(table["CTBC"][0])]
        for p in shadow_probe:
            self.assertTrue(C.deny_shadowed(table["CTBC"][0], p + "研究部"), "a short legit alias inside a denied name: " + p)
        self.assertFalse(C.deny_shadowed(table["CTBC"][0], "中信投顧"), "no denied name here")
        self.assertTrue(all(C.is_denied_token(p) for p in phrases))
        self.assertFalse(C.is_denied_token("JPM"))
        self.assertEqual(C.compare_broker(phrases[-1], {"broker": None}), "DENIED")

    # ---- mother 批728: the engines load the sibling core, never a foreign module of the same name -------
    def test_engines_ignore_a_foreign_module_named_like_the_core(self):
        import sys
        import types
        engine_dir = ENGINE
        decoy = types.ModuleType("VRN_Evidence_Core")
        decoy.__file__ = str(ENGINE.parent / "references" / "intake" / "decoy" / "VRN_Evidence_Core.py")
        saved = {k: sys.modules.get(k) for k in ("VRN_Evidence_Core", "vrn_engine_evidence_core")}
        sys.modules["VRN_Evidence_Core"] = decoy
        sys.modules.pop("vrn_engine_evidence_core", None)
        try:
            for name in ("VIA_VRN_FirstPageEngine.py", "VRN_Integrated_ReportDatabase_Engine.py"):
                spec = importlib.util.spec_from_file_location("decoy_probe_" + name[:-3], str(engine_dir / name))
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                core = mod.EVIDENCE_CORE if hasattr(mod, "EVIDENCE_CORE") else mod.optional_import_evidence_core()
                self.assertIsNotNone(core, name)
                self.assertEqual(Path(core.__file__).resolve(), (engine_dir / "VRN_Evidence_Core.py").resolve(), name)
                self.assertIsNot(core, decoy, name)
        finally:
            for k, v in saved.items():
                if v is None:
                    sys.modules.pop(k, None)
                else:
                    sys.modules[k] = v

    # ---- text lines -------------------------------------------------
    def test_filler_spaces_and_word_gaps(self):
        C = self.C
        row = def_glyphs("目標價", size=8.0) + def_glyphs("310.00", x0=60.0, size=8.0, advance=4.0, gap=1.0)
        row += [{"text": " ", "x0": 25.0, "x1": 27.0, "top": 100.0, "bottom": 108.0, "size": 8.0}]
        self.assertEqual(C.join_row(row), "目標價 310.00", "filler space glyphs vanish, tracked digits stay one number")
        words = def_glyphs("Stock", x0=10, size=10, advance=5) + def_glyphs("Rating", x0=38, size=10, advance=5)
        self.assertEqual(C.join_row(words), "Stock Rating", "a 0.3 em gap writes a space")

    def test_overlay_glyph_is_dropped(self):
        C = self.C
        row = def_glyphs("九", x0=10, size=8) + [{"text": "4", "x0": 13.0, "x1": 16.0, "top": 100, "bottom": 105, "size": 5.0}]
        row += def_glyphs("月", x0=18.5, size=8)
        self.assertEqual(C.join_row(row), "九月")

    # ---- broker evidence --------------------------------------------
    def test_broker_tiers_and_generic_words(self):
        C = self.C
        ev = C.broker_evidence(["The first quarter was strong", "Capital expenditure rose", "analyst@daiwacm-cathay.com.tw"], ALIASES)
        self.assertEqual((ev["broker"], ev["tier"], ev["strong"]), ("DAIWA", "EMAIL", True), "Daiwa-Cathay domain is Daiwa research")
        ev = C.broker_evidence(["市場第一季營收", "本報告由凱基證券投資顧問發布"], ALIASES)
        self.assertEqual((ev["broker"], ev["tier"]), ("KGI", "ISSUER"))
        ev = C.broker_evidence(["中信金(2891 TT) 獲利成長"], ALIASES)
        self.assertIsNone(ev["broker"], "a company name next to its code is not broker evidence (LL67)")
        self.assertEqual(C.compare_broker("KGI", {"broker": "YUANTA", "strong": False, "candidates": {"YUANTA": {"BODY": 1}}}),
                         "INSUFFICIENT_EVIDENCE", "weak page evidence never contradicts the filename")

    def test_deny_list_first(self):
        C = self.C
        if C.vcgc("purge") is None:
            self.skipTest("VCGC mirror absent")
        purge = C.vcgc("purge")
        denied_aliases = sorted(getattr(purge, "CN_ALIAS", ()))
        denied_canon = sorted(getattr(purge, "CN_CANON", ()))
        self.assertTrue(denied_aliases and denied_canon, "CGC_MDL177 exposes its deny list")
        # a table that (wrongly) still carries a denied broker must not resolve it: the deny list runs first
        leaky = dict(ALIASES)
        leaky[denied_canon[0]] = [a.lower() for a in denied_aliases]
        self.assertIsNone(C.broker_evidence(["china international capital 研究部"], leaky)["broker"])
        for alias in denied_aliases:
            got = C.broker_evidence([f"{alias} (Hong Kong) Brokerage", f"本報告由 {alias} 發布"], leaky)["broker"]
            self.assertIsNone(got, "deny list leaked: " + alias)
        self.assertEqual(C.compare_broker(denied_canon[0], {"broker": None}), "DENIED")
        for text, key in (("中國信託證券投顧", "CTBC"), ("國泰證期研究部", "CATHAY"), ("CLSA Limited", "CLSA")):
            self.assertEqual(C.broker_evidence([text], ALIASES)["broker"], key, "negative control: " + text)

    # ---- report type / ticker / tri-code ----------------------------
    def test_report_type_and_tri_code(self):
        C = self.C
        lines = ["Example Tech (5274 TT)", "Target price: TWD1,200.00 (from TWD900.00)", "Share price (14 Sep): TWD900.00"]
        a = C.analyze("260914_daiwa_example.pdf", lines, ALIASES, text_layer=True)
        self.assertEqual((a["report_type"]["type"], a["ticker"]["ticker"], a["target_price"]["value"]), ("STOCK", "5274", 1200.0))
        a = C.analyze("凱基投顧_鋼鐵產業_王小明_20260518.pdf", ["產業報告", "中鋼 (2002 TT，NT$18.2，持有) 和中鴻 (2014 TT，NT$17.1，持有)"],
                      ALIASES, text_layer=True)
        self.assertEqual(a["report_type"]["type"], "INDUSTRY")
        self.assertIsNone(a["rating"]["value"], "an industry report carries no stock rating")
        codes = C.page_codes(["Hon Hai (2317.TW): results", "peers: Quanta (2382.TW)"])
        self.assertEqual(C.tri_code("2317", codes)["verdict"], "PASS", "peers on the page do not break PASS")
        self.assertEqual(C.tri_code("2330", codes)["verdict"], "MISMATCH")
        self.assertEqual(C.tri_code(None, [])["verdict"], "N/A")

    # ---- rating -----------------------------------------------------
    def test_rating_forms(self):
        C = self.C
        cases = [
            (["Stock Rating Equal-weight"], "HOLD"), (["12-month rating Neutral"], "HOLD"),
            (["儒鴻", "持有‧維持"], "HOLD"), (["買進 – 初次評等"], "BUY"), (["宏致 (3605 TT, NT$140, 增加持股)"], "BUY"),
            (["Share price (11 Oct): TWD78.90 | Up/downside: +26.7% Buy"], "BUY"), (["TSMC Overweight"], "BUY"),
            (["growth; Buy (on CL)"], "BUY"), (["NT$3,300.00 - OUTPERFORM"], "BUY"), (["投資評等 買進"], "BUY"),
            (["維持「逢低買進」投資評等"], "ADD"), (["Maintained Hold"], "HOLD"),
        ]
        for lines, want in cases:
            self.assertEqual(C.extract_rating(lines)["value"], want, lines)
        self.assertIsNone(C.extract_rating(["前次評等 買進"])["value"], "the previous rating never counts")
        self.assertIsNone(C.extract_rating(["評等分級：買進（預期未來六個月股價漲幅超過+30%）"])["value"])
        self.assertIsNone(C.extract_rating(["前次投資建議：2024.12.09", "「買進」,目標價:$345"])["value"])
        slot = C.extract_rating([], "光焱(7728,Note)-CTBC260918.pdf")
        self.assertEqual((slot["value"], slot["state"]), (None, "UNRATED_SLOT"), "Note is a report type, not a rating")
        self.assertEqual(C.extract_rating([], "晶心科(6533,N,中立)-CTBC251208.pdf")["value"], "HOLD")

    def test_canonical_rating_key(self):
        C = self.C
        inst = C.institution_ssot()
        self.assertEqual(C.canonical_rating_key("逢低買進", "ADD", None, inst)[0], "BUY")
        self.assertEqual(C.canonical_rating_key("強力買進", "BUY", "STRONG_BUY", inst)[0], "STRONG_BUY")

    # ---- prices -----------------------------------------------------
    def test_target_and_current_price(self):
        C = self.C
        tp = lambda lines: C.extract_target_price(lines)["value"]
        cp = lambda lines: C.extract_current_price(lines)["value"]
        self.assertEqual(tp(["Price Target (Dec-25):NT$1275.0"]), 1275.0, "(Dec-25) is a horizon, not the price")
        self.assertEqual(tp(["凱基維持「持有」投資評等，目標價由 85 元上調至 104 元"]), 104.0)
        self.assertEqual(tp(["前次目標價 (NT$) 85.00", "12 個月目標價 (NT$) 104.0"]), 104.0)
        self.assertIsNone(tp(["Up/downside to price target (%) 38"]))
        self.assertEqual(tp(["投資評等 目標價", "範例公司(1234) 逢低買進 $208", "前次投資建議：2024.12.09", "「買進」,目標價:$345"]), 208.0)
        self.assertEqual(tp(["raising 12-month TP to TWD26,660"]), 26660.0)
        self.assertEqual(cp(["Shr price, close (Oct 7, 2025) NT$3,510.00"]), 3510.0)
        self.assertEqual(cp(["收盤價 May 19 (NT$) 320.0"]), 320.0)
        self.assertEqual(cp(["NT$3,300.00 - OUTPERFORM"]), 3300.0)
        self.assertIsNone(cp(["Target price NT$165.00"]), "a target is never the current price")

    # ---- dates ------------------------------------------------------
    def test_dates(self):
        C = self.C
        first = lambda lines, fn=None: C.choose_page_date(C.page_dates(lines), fn)["iso"]
        self.assertEqual(first(["九月 15, 2026"]), "2026-09-15")
        self.assertEqual(first(["04 Jun 202507:41:23 ET"]), "2025-06-04")
        self.assertEqual(first(["December 3, 2025 08:17 PM GMT"]), "2025-12-03")
        self.assertEqual(first(["訪談報告 2025年12月2日"]), "2025-12-02")
        self.assertIsNone(first(["債券ETF周報", "2026 / 9 / 7 至 2026 / 9 / 11"]), "a covered week is not a report date")
        self.assertEqual(first(["2 0 2 6", "三", "9/16"]), "2026-09-16", "cover year + month/day")
        self.assertIsNone(first(["前次投資建議：2024.12.09"]))

    # ---- analysts ---------------------------------------------------
    def test_local_signatures(self):
        C = self.C
        names = lambda lines: [a["name"] for a in C.extract_analysts(lines)]
        self.assertIn("王小明", names(["報告日期：2025.08.19 研 究 員：王小明"]))
        self.assertIn("陳大文", names(["• 報 告 人：陳大文"]))
        self.assertTrue(C._same_person("John Q Public", "John Public"))
        self.assertEqual(C.reverse_name("mei-ling.chen"), "Mei-Ling Chen")

    # ---- tables -----------------------------------------------------
    def test_column_and_transposed_tables(self):
        C = self.C
        chars = []
        top = 100.0
        for label, cells in (("", ["2024A", "2025F", "2026F"]), ("EPS (NT$)", ["5.20", "6.10", "7.00"]),
                             ("Revenue (NT$ mn)", ["1,000", "1,200", "1,400"]), ("EPS growth (%)", ["10.0", "17.3", "14.8"])):
            chars += def_glyphs(label, x0=10, size=8, top=top)
            for k, cell in enumerate(cells):
                chars += def_glyphs(cell, x0=150 + 60 * k, size=8, top=top)
            top += 12
        tables = C.column_tables(chars)
        self.assertEqual(tables[0]["Rows"][0], ["", "2024A", "2025F", "2026F"])
        labels = [r[0] for r in tables[0]["Rows"][1:]]
        self.assertEqual(labels, ["EPS (NT$)", "Revenue (NT$ mn)"], "growth rows are not EPS")
        self.assertEqual(C.normalize_period_label("Dec-24A"), "2024A")
        chars, top = [], 300.0
        chars += def_glyphs("Year", x0=10, size=8, top=top)
        for k, head in enumerate(["EPS", "EPS", "P/E"]):
            chars += def_glyphs(head, x0=150 + 60 * k, size=8, top=top)
        top += 12
        for k, unit in enumerate(["(NT$)", "YoY(%)", "(x)"]):
            chars += def_glyphs(unit, x0=150 + 60 * k, size=8, top=top)
        for year, vals in (("2024A", ["5.20", "10.0", "15.0"]), ("2025E", ["6.10", "17.3", "12.8"]), ("2026E", ["7.00", "14.8", "11.1"])):
            top += 12
            chars += def_glyphs(year, x0=10, size=8, top=top)
            for k, v in enumerate(vals):
                chars += def_glyphs(v, x0=150 + 60 * k, size=8, top=top)
        t = C.transposed_tables(chars)[0]["Rows"]
        self.assertEqual(t[0], ["", "2024A", "2025E", "2026E"])
        self.assertEqual([r[0] for r in t[1:]], ["EPS (NT$)", "P/E (x)"], "the YoY column is dropped")
        self.assertEqual(t[1][1:], ["5.20", "6.10", "7.00"])


if __name__ == "__main__":
    unittest.main()
