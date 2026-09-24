"""Appendix small print (批729; operator 2026-09-24): the last pages name the issuer and print the rating scale.

Synthetic PDFs only (PyMuPDF writes them into a temporary folder); no report content is stored in the repo.
Denied names are read from the deny gate at run time, never spelled here (CGC_MDL177 counts spelled names)."""

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
import re
import sys
import tempfile
import unittest
from pathlib import Path

ENGINE = Path(__file__).resolve().parents[1] / "engine"
ALIASES = {"KGI": ["凱基", "凱基投顧", "kgi"], "YUANTA": ["元大", "yuanta"]}
BODY = ["營收展望與獲利預估說明,本季受惠新產品放量。", "毛利率維持高檔,費用率持平。", "資本支出計畫不變,現金流量穩定。",
        "法人持股比率上升,籌碼集中。", "下半年旺季效應可望延續。", "評價方面維持區間操作看法。"]


def def_load(name, filename):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, ENGINE / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def def_pdf(path, pages):
    """pages: [[(x, y, text, size), ...], ...] -> a PDF with CJK text (built-in china-t font)."""
    import fitz
    doc = fitz.open()
    for items in pages:
        page = doc.new_page(width=595, height=842)
        for x, y, text, size in items:
            page.insert_text((x, y), text, fontsize=size, fontname="china-t")
    doc.save(str(path))
    doc.close()


def def_page1(extra=()):
    rows = [(60, 70, "台積電 (2330 TT) 公司更新", 16)]
    rows += [(60, 120 + 22 * i, t, 10) for i, t in enumerate(BODY)]
    rows += [(60, 300 + 22 * i, t, 10) for i, t in enumerate(extra)]
    return rows


def def_appendix(small, body=()):
    rows = [(40, 80 + 12 * i, t, 6) for i, t in enumerate(small)]
    rows += [(40, 500 + 22 * i, t, 10) for i, t in enumerate(body)]
    return rows


@unittest.skipUnless(importlib.util.find_spec("fitz") and importlib.util.find_spec("pdfplumber"),
                     "PyMuPDF / pdfplumber absent; appendix geometry not verified")
class AppendixTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.C = def_load("vrn_evidence_core_appendix_test", "VRN_Evidence_Core.py")
        cls.tmp = tempfile.TemporaryDirectory()
        cls.dir = Path(cls.tmp.name)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def pdf(self, name, pages):
        path = self.dir / name
        def_pdf(path, pages)
        return path

    def fpe(self):
        mod = def_load("via_vrn_first_page_engine_appendix_test", "VIA_VRN_FirstPageEngine.py")
        if not hasattr(self.__class__, "_engine"):
            self.__class__._engine = mod.FirstPageEngine()
        return mod, self.__class__._engine

    def run_fpe(self, name, path):
        mod, eng = self.fpe()
        chars, size = mod._chars_from_pdf(str(path))
        return eng.run(name, chars=chars, page_width=size[0], page_height=size[1], source_path=str(path))

    # ── the small-print filter and the issuer ────────────────────────────────────────
    def test_small_print_on_the_last_pages_names_the_issuer(self):
        path = self.pdf("a.pdf", [def_page1(), [(60, 120 + 22 * i, t, 10) for i, t in enumerate(BODY)],
                                  def_appendix(["本報告由凱基證券投資顧問股份有限公司發佈,版權所有。", "投資人應審慎評估風險。"],
                                               body=["元大 研究部 市場觀點 本文字級"])])
        lines, info = self.C.appendix_lines(str(path))
        self.assertEqual(info["state"], "OK")
        self.assertEqual(info["body_size"], 10.0)
        self.assertTrue(lines and all(l["size"] < info["threshold"] for l in lines), lines)
        self.assertFalse(any("元大" in l["text"] for l in lines), "a body-size line is not small print")
        ev = self.C.appendix_evidence(str(path), alias_table=ALIASES)
        self.assertEqual(ev["broker"]["broker"], "KGI")
        self.assertTrue(ev["broker"]["strong"])
        self.assertTrue(all(e.get("page") == 3 for e in ev["broker"]["evidence"]))

    def test_one_page_pdf_has_no_appendix(self):
        path = self.pdf("one.pdf", [def_page1()])
        lines, info = self.C.appendix_lines(str(path))
        self.assertEqual((lines, info["state"]), ([], "NODATA"))
        self.assertIn("one page", info["why"])

    def test_page1_grading_is_unchanged_without_the_appendix_forms(self):
        lines = ["凱基 版權所有"]
        plain = self.C.broker_evidence(lines, ALIASES)
        widened = self.C.broker_evidence(lines, ALIASES, disclosure_rx=self.C.APPENDIX_DISCLOSURE_RX)
        self.assertNotEqual(plain["tier"], "DISCLOSURE", "page-1 grading must stay v0101")
        self.assertEqual(widened["tier"], "DISCLOSURE")

    def test_a_denied_name_in_small_print_is_never_the_issuer(self):
        denied = next(d for d in self.C.deny_phrases() if re.fullmatch(r"[一-鿿]{2,4}", d))
        path = self.pdf("deny.pdf", [def_page1(), def_appendix([denied + "證券研究部 版權所有", "投資人應審慎評估風險。"])])
        ev = self.C.appendix_evidence(str(path), alias_table=ALIASES)
        self.assertIsNone(ev["broker"]["broker"])
        self.assertTrue(any(e["tier"] == "DENIED" for e in ev["broker"]["evidence"]))

    # ── the first-page engine: fill a weak page 1, never overrule a strong one ───────────────
    def test_appendix_fills_a_weak_page1(self):
        path = self.pdf("weak.pdf", [def_page1(), def_appendix(["本報告由凱基證券投資顧問股份有限公司發佈,版權所有。"])])
        out = self.run_fpe("台積電2330_公司更新.pdf", path)
        self.assertEqual(out["broker"], "KGI")
        self.assertTrue(str(out["broker_tier"]).startswith("APPENDIX_"), out.get("broker_tier"))
        self.assertTrue(out["appendix"]["strong"])

    def test_a_strong_page1_is_never_overruled(self):
        path = self.pdf("strong.pdf", [def_page1(extra=["分析師 王小明 analyst.one@kgi.com"]),
                                       def_appendix(["本報告由元大證券投資顧問股份有限公司發佈,版權所有。"])])
        out = self.run_fpe("台積電2330_公司更新.pdf", path)
        self.assertEqual(out["broker"], "KGI", out.get("broker_tier"))
        self.assertEqual(out["broker_tier"], "EMAIL")
        self.assertEqual(out["appendix"]["broker"], "YUANTA")

    def test_an_appendix_issuer_against_the_filename_is_flagged_not_silently_taken(self):
        path = self.pdf("conflict.pdf", [def_page1(), def_appendix(["本報告由凱基證券投資顧問股份有限公司發佈,版權所有。"])])
        out = self.run_fpe("元大_台積電2330_20260901.pdf", path)
        self.assertEqual(out["broker_filename"], "YUANTA")
        self.assertEqual(out["broker"], "YUANTA")
        self.assertEqual(out.get("broker_conflict", {}).get("appendix"), "KGI")
        self.assertEqual(out["broker_conflict"]["state"], "REVIEW")

    # ── the rating scale: candidates only ─────────────────────────────────────────────
    def test_rating_scale_known_new_and_suggested(self):
        words = self.C.merged_rating_words(self.C.load_rules())
        new_cn, new_lat = "甲乙試評", "Qzxv"
        self.assertEqual(self.C.normalize_rating_word(new_cn, words), (None, None), "fixture word must be unknown")
        self.assertEqual(self.C.normalize_rating_word(new_lat, words), (None, None), "fixture word must be unknown")
        buy, _ = self.C.normalize_rating_word("Buy", words)
        outp, _ = self.C.normalize_rating_word("Outperform", words)
        self.assertIsNotNone(buy)
        self.assertIsNotNone(outp)
        lines = ["評等定義", "買進(Buy):預期未來12個月報酬率超過15%", new_cn + "(Outperform):預期表現優於大盤",
                 "丙丁試評(" + new_lat + "):預期表現落後大盤", "目標價(TP):NT$1,200,預期上漲15%", "資料來源:TEJ"]
        got = {r["word"]: r for r in self.C.rating_scale(lines, words=words)}
        self.assertEqual(set(got), {"買進", new_cn, "丙丁試評"})
        self.assertTrue(got["買進"]["word_known"] and got["買進"]["alt_known"])
        self.assertIsNone(got["買進"]["suggested"])
        self.assertFalse(got[new_cn]["word_known"])
        self.assertEqual(got[new_cn]["suggested"], outp, "a NEW word is suggested only through its KNOWN pair")
        self.assertIsNone(got["丙丁試評"]["suggested"], "two unknown words get no suggestion")

    def test_the_first_page_engine_carries_the_rating_scale(self):
        path = self.pdf("scale.pdf", [def_page1(), def_appendix(["本報告由凱基證券投資顧問股份有限公司發佈,版權所有。",
                                                                  "買進(Buy):預期未來12個月報酬率超過15%"])])
        out = self.run_fpe("台積電2330_公司更新.pdf", path)
        self.assertEqual([r["word"] for r in out["appendix"]["rating_scale"]], ["買進"])

    # ── the CLI writes a report, never a book ─────────────────────────────────────────
    def test_cli_writes_the_report_only_under_its_out_folder(self):
        src = self.dir / "cli_in"
        src.mkdir(exist_ok=True)
        def_pdf(src / "r.pdf", [def_page1(), def_appendix(["本報告由凱基證券投資顧問股份有限公司發佈,版權所有。",
                                                            "甲乙試評(Outperform):預期表現優於大盤"])])
        out = self.dir / "cli_out"
        rc = self.C.main(["appendix", str(src), "--out", str(out)])
        self.assertEqual(rc, 0)
        rep = json.loads((out / "APPENDIX_latest.json").read_text(encoding="utf-8"))
        self.assertEqual((rep["n_files"], rep["n_with_small_print"]), (1, 1))
        self.assertIn("甲乙試評", [w["word"] for w in rep["new_words"]])
        self.assertTrue((out / "APPENDIX_latest.md").is_file())
        self.assertEqual(self.C.main(["appendix", str(self.dir / "no_such_folder")]), 2)


if __name__ == "__main__":
    unittest.main()
