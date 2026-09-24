"""Appendix accuracy against ground truth (批730; operator 2026-09-24 "結果也要實測正確性").

32 realistic-style appendix pages (Taiwan investment advisers and foreign houses, Chinese and English disclosures,
rating-definition lines and tables) plus negative controls (source lines, peer tables, a distributor, label lines,
body-size text).  Every sentence was written for this test in the common shapes of sell-side disclosures; no report
content and no people's names.  CASES tuned the rules; HELDOUT was written afterwards and never used for tuning.
Pass mark: issuer 100% and rating words precision / recall 100% on both sets."""

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

ENGINE = Path(__file__).resolve().parents[1] / "engine"
BODY = ["營收展望與獲利預估說明,本季受惠新產品放量。", "毛利率維持高檔,費用率持平。", "資本支出計畫不變,現金流量穩定。",
        "法人持股比率上升,籌碼集中。", "下半年旺季效應可望延續。", "評價方面維持區間操作看法。"]

CASES = [
    ("kgi", ["本報告由凱基證券投資顧問股份有限公司(凱基投顧)提供,僅供參考,不構成任何投資建議。",
             "投資評等說明:",
             "增加持股(Outperform):預期未來12個月股價表現優於大盤指數",
             "中立(Neutral):預期未來12個月股價表現與大盤指數相當",
             "降低持股(Underperform):預期未來12個月股價表現落後大盤指數",
             "© 2026 KGI Securities Investment Advisory Co., Ltd. All rights reserved."],
     [], "KGI", {"增加持股", "中立", "降低持股"}),
    ("yuanta", ["元大證券投資顧問股份有限公司 版權所有,翻印必究。",
                "投資評等定義",
                "買進(BUY):預期未來12個月報酬率超過15%",
                "持有-超越同業(Hold-Outperform):預期未來12個月報酬率介於5%至15%",
                "持有-落後同業(Hold-Underperform):預期未來12個月報酬率介於-5%至5%",
                "賣出(SELL):預期未來12個月報酬率低於-5%"],
     [], "YUANTA", {"買進", "持有-超越同業", "持有-落後同業", "賣出"}),
    ("fubon", ["本研究報告由富邦證券投資顧問股份有限公司製作,僅供客戶參考。",
               "評等 定義",
               "買進 Buy 預期未來6至12個月股價上漲15%以上",
               "中立 Neutral 預期未來6至12個月股價介於-5%至15%",
               "賣出 Sell 預期未來6至12個月股價下跌5%以上"],
     [], "FUBON", {"買進", "中立", "賣出"}),
    ("capital", ["群益證券投資顧問股份有限公司 著作權所有,未經同意不得轉載。",
                 "強力買進(Strong Buy):預期未來12個月報酬率超過30%",
                 "買進(Buy):預期未來12個月報酬率介於15%至30%",
                 "中立(Neutral):預期未來12個月報酬率介於-10%至15%",
                 "賣出(Sell):預期未來12個月報酬率低於-10%"],
     [], "CAPITAL", {"強力買進", "買進", "中立", "賣出"}),
    ("sinopac", ["永豐證券投資顧問股份有限公司版權所有。本報告內容僅供參考。",
                 "買進(Buy):預期股價表現優於大盤15%以上",
                 "中立(Neutral):預期股價表現與大盤相當",
                 "賣出(Sell):預期股價表現落後大盤15%以上"],
     [], "SINOPAC", {"買進", "中立", "賣出"}),
    ("mega", ["兆豐證券投資顧問股份有限公司 版權所有",
              "評等定義",
              "買進:預期未來12個月股價漲幅超過20%",
              "區間操作:預期未來12個月股價漲跌幅介於-10%至20%",
              "賣出:預期未來12個月股價跌幅超過10%"],
     [], "MEGA", {"買進", "區間操作", "賣出"}),
    ("huanan", ["本報告係由華南證券投資顧問股份有限公司提供,非經同意不得轉載。",
                "買進（Buy）：預期未來12個月股價表現優於大盤",
                "中立（Neutral）：預期未來12個月股價表現與大盤相當",
                "賣出（Sell）：預期未來12個月股價表現落後大盤"],
     [], "HUANAN", {"買進", "中立", "賣出"}),
    ("ctbc", ["本報告由中國信託證券投資顧問股份有限公司提供,版權所有。",
              "增加持股(Overweight):預期股價表現優於大盤10%以上",
              "持有(Hold):預期股價表現與大盤差距在10%以內",
              "減少持股(Underweight):預期股價表現落後大盤10%以上"],
     [], "CTBC", {"增加持股", "持有", "減少持股"}),
    ("ms", ["Morgan Stanley Research. Important Disclosures on subject companies.",
            "Stock Ratings",
            "Overweight (O or Over) - The stock's total return is expected to exceed the average total return of the industry coverage universe.",
            "Equal-weight (E or Equal) - The stock's total return is expected to be in line with the average total return of the industry coverage universe.",
            "Underweight (U or Under) - The stock's total return is expected to be below the average total return of the industry coverage universe.",
            "Not-Rated (NR) - Currently the analyst does not have adequate conviction about the stock's total return relative to the benchmark."],
     [], "MS", {"Overweight", "Equal-weight", "Underweight", "Not-Rated"}),
    ("gs", ["Disclosure Appendix. This report was prepared by Goldman Sachs & Co. LLC.",
            "Buy: expected to outperform the coverage universe over the next 12 months.",
            "Neutral: expected to perform in line with the coverage universe over the next 12 months.",
            "Sell: expected to underperform the coverage universe over the next 12 months."],
     [], "GS", {"Buy", "Neutral", "Sell"}),
    ("jpm", ["Analyst Certification. J.P. Morgan Securities (Taiwan) Limited. All rights reserved.",
             "Overweight (OW): Over the next six to twelve months, we expect this stock will outperform the average total return of the stocks in the coverage universe.",
             "Neutral (N): Over the next six to twelve months, we expect this stock will perform in line with the average total return.",
             "Underweight (UW): Over the next six to twelve months, we expect this stock will underperform the average total return."],
     [], "JPM", {"Overweight", "Neutral", "Underweight"}),
    ("citi", ["Citi Research is a division of Citigroup Global Markets Inc. Important disclosures appear below.",
              "Buy (1): expected total return of 15% or more over the next 12 months.",
              "Neutral (2): expected total return between 5% and 15%.",
              "Sell (3): expected total return below 5%."],
     [], "CITI", {"Buy", "Neutral", "Sell"}),
    ("daiwa", ["This report is issued by Daiwa Capital Markets Hong Kong Limited. Disclaimer.",
               "Buy (1): the stock is expected to outperform the local market by more than 15% over the next 12 months.",
               "Outperform (2): the stock is expected to outperform the local market by 5-15%.",
               "Hold (3): the stock is expected to perform within 5% of the local market.",
               "Underperform (4): the stock is expected to underperform the local market by 5-15%.",
               "Sell (5): the stock is expected to underperform the local market by more than 15%."],
     [], "DAIWA", {"Buy", "Outperform", "Hold", "Underperform", "Sell"}),
    ("clsa", ["CLSA Limited. Important disclosures. All rights reserved.",
              "BUY: Total stock return (including dividends) expected to exceed 20% over the next 12 months.",
              "O-PF: Outperform, total return expected to exceed the market return.",
              "U-PF: Underperform, total return expected to be below the market return.",
              "SELL: Total stock return expected to be below nil."],
     [], "CLSA", {"BUY", "O-PF", "U-PF", "SELL"}),
    ("macq", ["Macquarie Capital Limited. Important disclosures.",
              "Outperform – return more than 5% in excess of the benchmark return.",
              "Neutral – return within 5% of the benchmark return.",
              "Underperform – return more than 5% below the benchmark return."],
     [], "MACQUARIE", {"Outperform", "Neutral", "Underperform"}),
    ("ubs", ["This research report has been prepared by UBS Securities Pte. Ltd. Disclaimer.",
             "Buy: forecast stock return is more than 6% above the market return assumption.",
             "Neutral: forecast stock return is within 6% of the market return assumption.",
             "Sell: forecast stock return is more than 6% below the market return assumption."],
     [], "UBS", {"Buy", "Neutral", "Sell"}),
    # ── negative controls ──
    ("source_only", ["資料來源:凱基投顧整理、TEJ", "註:以上資料僅供參考"], [], None, set()),
    ("peer_table_with_issuer", ["本報告由凱基證券投資顧問股份有限公司提供,版權所有。",
                                "同業評等彙整",
                                "元大證券 買進 目標價1200元",
                                "富邦證券 中立 目標價1000元"],
     [], "KGI", set()),
    ("peer_table_only", ["同業評等彙整", "元大證券 買進 目標價1200元", "富邦證券 中立 目標價1000元"], [], None, set()),
    ("body_size_other_broker", ["投資人應審慎評估風險。"], ["元大證券投資顧問股份有限公司 版權所有"], None, set()),
    ("tp_lines_are_not_ratings", ["本報告由永豐證券投資顧問股份有限公司提供,版權所有。",
                                  "目標價(TP):NT$1,200,預期上漲15%",
                                  "本益比(PE):預期2026年為18倍"],
     [], "SINOPAC", set()),
]

HELDOUT = [
    ("cathay_legal_name", ["國泰證券投資顧問股份有限公司 地址:台北市敦化南路二段 電話:(02)2700-8399",
                           "買進(Buy):預期未來12個月報酬率超過15%",
                           "中立(Neutral):預期未來12個月報酬率介於-5%至15%",
                           "減碼(Underweight):預期未來12個月報酬率低於-5%"],
     [], "CATHAY", {"買進", "中立", "減碼"}),
    ("president_bare_table", ["統一證券投資顧問股份有限公司 版權所有",
                              "評等 說明",
                              "買進    預期未來12個月上漲空間大於15%",
                              "持有    預期未來12個月上漲空間介於-5%至15%",
                              "賣出    預期未來12個月下跌空間大於5%"],
     [], "PRESIDENT", {"買進", "持有", "賣出"}),
    ("esun_fullwidth", ["玉山證券投資顧問股份有限公司著作權所有",
                        "買進（BUY）：預期報酬率大於20%",
                        "中立（HOLD）：預期報酬率介於0%至20%",
                        "賣出（SELL）：預期報酬率小於0%"],
     [], "ESUN", {"買進", "中立", "賣出"}),
    ("first_made_by", ["本報告係第一金證券投資顧問股份有限公司所製作,僅供參考",
                       "增加持股 Outperform 預期股價表現優於大盤",
                       "中立 Neutral 預期股價表現與大盤相當",
                       "減少持股 Underperform 預期股價表現落後大盤"],
     [], "FIRST", {"增加持股", "中立", "減少持股"}),
    ("nomura", ["Nomura Securities Co., Ltd. Disclosures required in Taiwan.",
                "Buy: The stock's 12-month potential return is greater than 10% relative to the benchmark.",
                "Neutral: The stock's 12-month potential return is within 10% of the benchmark.",
                "Reduce: The stock's 12-month potential return is lower than the benchmark by more than 10%."],
     [], "NOMURA", {"Buy", "Neutral", "Reduce"}),
    ("bofa_upper_dash", ["BofA Securities Inc. Important Disclosures. Rating System:",
                         "BUY - Total return expectation within 12 months is 10% or more.",
                         "NEUTRAL - Total return expectation within 12 months is 0% to 10%.",
                         "UNDERPERFORM - Total return expectation within 12 months is below 0%."],
     [], "BOFA", {"BUY", "NEUTRAL", "UNDERPERFORM"}),
    ("cs_style", ["Credit Suisse Securities (Europe) Limited. Disclaimer.",
                  "Outperform (O): The stock's total return is expected to outperform the relevant benchmark by at least 10%.",
                  "Neutral (N): The stock's total return is expected to be in line with the relevant benchmark.",
                  "Underperform (U): The stock's total return is expected to underperform the relevant benchmark by at least 10%."],
     [], "CS", {"Outperform", "Neutral", "Underperform"}),
    ("distributor_named", ["本報告由凱基證券投資顧問股份有限公司提供,並由元大證券股份有限公司於台灣地區轉發,版權所有。"],
     [], "KGI", set()),
    ("labels_not_ratings", ["本報告由富邦證券投資顧問股份有限公司提供,版權所有。",
                            "Valuation: our target price of NT$1,200 implies 15% upside.",
                            "Risks: slower demand and expected margin pressure.",
                            "Catalyst: new products expected in 2H26.",
                            "Analyst Certification: the views expressed accurately reflect personal views."],
     [], "FUBON", set()),
    ("foreign_peer_table", ["Consensus overview", "Morgan Stanley Overweight PT 1,300", "Goldman Sachs Buy PT 1,250"],
     [], None, set()),
    ("exchange_source", ["資料來源:台灣證券交易所、公開資訊觀測站", "本資料僅供參考"], [], None, set()),
]


def def_load(name, filename):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, ENGINE / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def def_pdf(path, small, big):
    import fitz
    doc = fitz.open()
    p1 = doc.new_page(width=595, height=842)
    p1.insert_text((60, 70), "台積電 (2330 TT) 公司更新", fontsize=16, fontname="china-t")
    for i, t in enumerate(BODY):
        p1.insert_text((60, 120 + 22 * i), t, fontsize=10, fontname="china-t")
    p2 = doc.new_page(width=595, height=842)
    for i, t in enumerate(BODY):
        p2.insert_text((60, 120 + 22 * i), t, fontsize=10, fontname="china-t")
    p3 = doc.new_page(width=595, height=842)
    for i, t in enumerate(small):
        p3.insert_text((40, 80 + 12 * i), t, fontsize=6, fontname="china-t")
    for i, t in enumerate(big):
        p3.insert_text((40, 500 + 22 * i), t, fontsize=10, fontname="china-t")
    doc.save(str(path))
    doc.close()


@unittest.skipUnless(importlib.util.find_spec("fitz") and importlib.util.find_spec("pdfplumber"),
                     "PyMuPDF / pdfplumber absent; appendix geometry not verified")
class AppendixAccuracyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.C = def_load("vrn_evidence_core_appendix_accuracy", "VRN_Evidence_Core.py")
        cls.table = cls.C.ssot_alias_table()
        cls.tmp = tempfile.TemporaryDirectory()

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def measure(self, cases):
        wrong_issuer, extra, missed, n_words = [], [], [], 0
        for cid, small, big, truth_issuer, truth_words in cases:
            path = Path(self.tmp.name) / (cid + ".pdf")
            def_pdf(path, small, big)
            ev = self.C.appendix_evidence(str(path), alias_table=self.table)
            b = ev["broker"]
            pred = b.get("broker") if b.get("strong") else None
            if pred != truth_issuer:
                wrong_issuer.append((cid, truth_issuer, pred, b.get("tier")))
            got = {r["word"] for r in ev["rating_scale"]}
            n_words += len(truth_words)
            extra += [(cid, w) for w in sorted(got - truth_words)]
            missed += [(cid, w) for w in sorted(truth_words - got)]
        return wrong_issuer, extra, missed, n_words

    def test_tuning_set(self):
        wrong, extra, missed, n = self.measure(CASES)
        self.assertEqual((wrong, extra, missed), ([], [], []), f"{len(CASES)} pages · {n} rating words")

    def test_heldout_set(self):
        wrong, extra, missed, n = self.measure(HELDOUT)
        self.assertEqual((wrong, extra, missed), ([], [], []), f"{len(HELDOUT)} pages · {n} rating words")

    def test_page1_grading_passes_no_guard(self):
        # the issuer guard is appendix-only: a page-1 line with a peer-table shape keeps its v0101 ISSUER tier
        line = ["富邦證券 中立 目標價1000元"]
        plain = self.C.broker_evidence(line, self.table)
        guarded = self.C.broker_evidence(line, self.table, issuer_guard=self.C._appendix_issuer_line)
        self.assertEqual(plain["tier"], "ISSUER")
        self.assertNotEqual(guarded["tier"], "ISSUER")


if __name__ == "__main__":
    unittest.main()
