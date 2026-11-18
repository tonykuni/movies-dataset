#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ===== [VRN:ID:v0100] VRN-TST002 · test_VRN_BookCheck · TEST =====
# AST 注入（只加註解，AST 不變）：類別 3 · 函式 25；逐一編號在 ssot/VRN_ID_SSOT_v0100.json
# ===== [VRN:ID:END] =====
"""VRN_BookCheck v0100: the books harvested on 2026-10-10 load from VRN's own ssot/, agree with their own
examples, and read engine answers back without changing them (broker / e-mail / phone / rating / target
price / financial accounts / identities / field states)."""

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

import hashlib
import importlib.util
import json
import sys
import unittest
from pathlib import Path

VRN = Path(__file__).resolve().parents[1]
ENGINE = VRN / "engine"


# [VRN-ID] VRN-TST002-FNC001 · IO
def def_load(name):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, ENGINE / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


# [VRN-ID] VRN-TST002-CLS001 · CLASS
class def_BookCheckTests(unittest.TestCase):
    # [VRN-ID] VRN-TST002-FNC002 · LOGIC
    @classmethod
    def setUpClass(cls):
        cls.B = def_load("VRN_BookCheck_v0100")
        cls.loaded = cls.B.load_books(local=False)
        cls.books = cls.B.Books(cls.loaded, vrn_own_brokers=("GF", "CITIC", "CSC", "CICC", "HAITONG", "GTJA"))

    # [VRN-ID] VRN-TST002-FNC003 · TEST
    def test_books_are_vrn_own_copies_with_provenance(self):
        self.assertEqual(self.loaded["missing"], [])
        for path in self.loaded["paths"].values():
            self.assertEqual(Path(path).parent, VRN / "ssot", "read from VRN's own ssot/, never outside")
        prov = json.loads((VRN / "ssot" / "VRN_BOOKS_PROVENANCE_v0100.json").read_text(encoding="utf-8"))
        for row in prov["books"]:
            data = (VRN / row["file"]).read_bytes().replace(b"\r\n", b"\n")
            self.assertEqual(hashlib.sha256(data).hexdigest(), row["sha256_lf"], "byte copy unchanged: " + row["file"])
        cats = {c for row in prov["books"] for c in row["categories"]}
        for want in ("BROKER DICT", "RATING LIST", "TARGET PRICE DICT", "EMAIL", "TEL", "FINANCIAL ACCOUNT", "VALIDATION METHOD"):
            self.assertIn(want, cats, "every category the operator named has a book")

    # [VRN-ID] VRN-TST002-FNC004 · TEST
    def test_books_agree_with_their_own_examples(self):
        for row in self.B.book_selftest(self.loaded):
            self.assertTrue(row["ok"], row)

    # [VRN-ID] VRN-TST002-FNC005 · TEST
    def test_first_page_read_back(self):
        page = ["凱基證券 研究部", "分析師 王小明", "Tel: (02) 2181-8888", "xiaoming.wang@kgi.com", "Target Price NT$1,100", "評等: 買進"]
        res = self.books.check_first_page({"broker": "KGI", "rating": "買進", "target_price": 1100.0,
                                           "tel": ["(02) 2181-8888"], "lines": page})
        self.assertEqual({k: v["state"] for k, v in res.items()},
                         {"broker": "IN_BOOK", "email": "NAMED", "email_broker": "AGREE", "tel": "AGREE",
                          "rating": "IN_BOOK", "target_price": "AGREE"})
        # the engine read 1, the book reads 1,100 (S05 v0103 thousands separators) -> DISAGREE, both values kept
        res = self.books.check_first_page({"broker": "KGI", "target_price": 1.0, "lines": page})
        self.assertEqual(res["target_price"]["state"], "DISAGREE")
        self.assertIn("1100", res["target_price"]["detail"])
        # a phone the engine missed, a previous target that is not the target, a domain that names another broker
        res = self.books.check_first_page({"broker": "KGI", "tel": [], "target_price": 90.0,
                                           "lines": ["電話 +886-2-2181-8888", "前次目標價 120", "目標價 90", "amy@gs.com"]})
        self.assertEqual(res["tel"]["state"], "BOOK_ONLY")
        self.assertEqual(res["target_price"]["state"], "AGREE")
        self.assertEqual(res["email_broker"]["state"], "DISAGREE")

    # [VRN-ID] VRN-TST002-FNC006 · TEST
    def test_mainland_brokers_are_vrn_own_and_staff_mailbox_unverifiable(self):
        self.assertEqual(self.books.check_first_page({"broker": "GF"})["broker"]["state"], "VRN_OWN")
        res = self.books.check_first_page({"broker": "HUANAN", "lines": ["10863@entrust.com.tw"]})
        self.assertEqual(res["email"]["state"], "UNVERIFIABLE", "a numeric local part is a staff id, not a name")
        self.assertEqual(res["email_broker"]["state"], "AGREE", "entrust.com.tw is HUANAN in the books")

    # [VRN-ID] VRN-TST002-FNC011 · TEST
    def test_operator_run_2026_10_11_book_side_fixes(self):
        """Daiwa-Cathay mailboxes are Daiwa in the broker book; a year span is not a phone."""
        res = self.books.check_first_page({"broker": "DAIWA", "lines": ["Analyst  rick.hsu@daiwacm-cathay.com.tw"]})
        self.assertEqual(res["email_broker"]["state"], "AGREE", res["email_broker"]["detail"])
        res = self.books.check_first_page({"broker": "MEGA", "tel": [], "lines": ["預估 EPS 2025-2026 年成長", "Tel: (02)2181-8888"]})
        self.assertEqual(res["tel"]["state"], "BOOK_ONLY")
        self.assertNotIn("20252026", res["tel"]["detail"])
        self.assertIn("0221818888", res["tel"]["detail"])

    # [VRN-ID] VRN-TST002-FNC007 · TEST
    def test_rating_words_are_looked_up_not_classified(self):
        self.assertEqual(self.books.rating_in_book("Overweight"), "IN_BOOK")
        self.assertEqual(self.books.rating_in_book("強力買進"), "IN_BOOK")
        self.assertEqual(self.books.rating_in_book(None), "NONE")
        self.assertEqual(self.books.rating_in_book("火箭升空"), "NOT_IN_BOOK")

    # [VRN-ID] VRN-TST002-FNC008 · TEST
    def test_financial_accounts_and_identities(self):
        B, bk = self.B, self.books
        self.assertNotIn(bk.account_of("營業收入淨額"), (None, "NOISE"))
        self.assertNotIn(bk.account_of("Total current assets"), (None, "NOISE"))
        self.assertEqual(bk.account_of("2025"), "NOISE")
        rows = [{"ReportID": "R1", "TableID": "T", "PeriodLabelRaw": "2025", "MetricName": m, "MetricNameRaw": raw, "Value": v}
                for m, raw, v in (("Revenue", "營收", 100.0), ("GrossProfit", "毛利", 40.0), ("GrossMargin", "毛利率", 40.0),
                                  ("TotalAssets", "總資產", 300.0), ("TotalLiabilities", "總負債", 100.0), ("Equity", "股東權益", 150.0),
                                  ("", "應收帳款", 12.0))]
        idn = bk.check_identities(rows)
        self.assertEqual(idn["tally"]["GM_DIV"], {"PASS": 1})
        self.assertEqual(idn["tally"]["BS_ADD"], {"FAIL": 1}, "300 != 100 + 150: shown, never corrected")
        self.assertEqual(idn["tally"]["GP_SUB"], {"INSUFFICIENT": 1}, "no COGS row: honest INSUFFICIENT")
        acc = bk.check_accounts(rows)
        self.assertEqual(acc["tally"].get("book_only"), 1, "應收帳款: the books name it, the engine does not")
        self.assertEqual(B.identity_state({"op": "div", "a": "net_income", "b": "shares", "target": "eps", "tol_rel": 0.03},
                                          {"net_income": 10.0, "shares": 0.0, "eps": 1.0}), "DIV_ZERO")

    # [VRN-ID] VRN-TST002-FNC009 · TEST
    def test_field_state_matches_the_spec_book(self):
        f = self.B.field_state
        self.assertEqual([f(1, 1, wired=False), f(1, 1, pending=True), f(0, 0), f(0, 5, gated=True), f(0, 5), f(95, 100), f(94, 100),
                          f(50, 100, gated=True)],
                         ["NOT_WIRED", "SOURCE_PENDING", "NODATA", "GATED", "NODATA", "GREEN", "PARTIAL", "GATED"])
        spec = json.loads((VRN / "ssot" / "VIA_VRN_FieldSpec_SSOT_v0100.json").read_text(encoding="utf-8"))
        self.assertEqual(len(spec["fields"]), 15)

    # [VRN-ID] VRN-TST002-FNC010 · TEST
    def test_evidence_core_reads_its_own_newest_rule_books(self):
        core = def_load("VRN_Evidence_Core")
        found = core.find_rule_books()
        for key, name in (("field_rules", "VRN_FieldRules_SSOT_v0101.json"), ("report_field_rules", "VIA_VRN_ReportFieldRules_SSOT_v0101.json")):
            self.assertEqual((Path(found[key]).parent.name, Path(found[key]).name), ("ssot", name))
        words = core.merged_rating_words(core.load_rules())
        self.assertIn("buy", words)


# [VRN-ID] VRN-TST002-CLS002 · CLASS
class def_FinancialIdentityWiringTests(unittest.TestCase):
    """2026-10-19：七條財報恆等式一條都沒跑過 —— 174 個桶全 INSUFFICIENT。

    兩個不同的原因疊在一起，兩個都要擋住再犯：

    1. 冊上的 `cogs`／`opex`／`net_margin`／`shares` 在 IDENTITY_OPERANDS 裡**沒有對映**，
       所以四條恆等式結構上永遠評估不了。報告上印 INSUFFICIENT，看起來像「這次資料剛好不全」。
    2. 合成語料只印四列，剩下三條湊不齊運算元。

    另外還揪出一個**輸出值錯誤**（不只是缺漏）：「淨利率(%)」當時被認成 NetIncome，
    也就是把百分比寫進金額欄位。
    """

    # [VRN-ID] VRN-TST002-FNC012 · LOGIC
    @classmethod
    def setUpClass(cls):
        cls.bc = def_load("VRN_BookCheck_v0100")
        cls.db = def_load("VRN_Integrated_ReportDatabase_Engine")
        cls.atl = def_load("VRN_AutoTestLoop")
        book = json.loads((VRN / "ssot" / "VRN_FieldRules_SSOT_v0101.json").read_text(encoding="utf-8"))

        # [VRN-ID] VRN-TST002-FNC013 · LOGIC
        def walk(obj):
            if isinstance(obj, dict):
                if "id" in obj and "op" in obj:
                    yield obj
                for value in obj.values():
                    yield from walk(value)
            elif isinstance(obj, list):
                for value in obj:
                    yield from walk(value)

        cls.identities = list(walk(book))

    # [VRN-ID] VRN-TST002-FNC014 · TEST
    def test_every_identity_operand_is_wired_to_a_metric_name(self):
        """冊上點名的運算元都要對映得到，否則那條恆等式永遠是 INSUFFICIENT。"""
        wired = set(self.bc.IDENTITY_OPERANDS.values())
        unwired = sorted({o for i in self.identities
                          for o in (i.get("target"), i.get("a"), i.get("b")) if o and o not in wired})
        self.assertEqual(unwired, [], f"這些運算元沒有 MetricName 對映得到，恆等式永遠跑不動：{unwired}")

    # [VRN-ID] VRN-TST002-FNC015 · TEST
    def test_every_wired_operand_has_a_label_the_engine_recognises(self):
        """對映得到還不夠 —— 引擎要認得出報告上那個中文標籤，否則整列會被丟掉。"""
        labels = {"revenue": "營收", "cogs": "營業成本", "gross_profit": "毛利", "gross_margin": "毛利率(%)",
                  "opex": "營業費用", "op_profit": "營業利益", "op_margin": "營業利益率(%)",
                  "net_income": "稅後淨利", "net_margin": "淨利率(%)", "eps": "每股盈餘(元)",
                  "shares": "流通股數", "total_assets": "總資產", "total_liabilities": "總負債",
                  "equity": "股東權益"}
        for metric, operand in self.bc.IDENTITY_OPERANDS.items():
            label = labels.get(operand)
            self.assertIsNotNone(label, f"{operand} 沒有列出對應的中文標籤，這個測試自己就不完整")
            self.assertEqual(self.db.normalize_metric_name(label), metric,
                             f"報告上印「{label}」要認成 {metric}")

    # [VRN-ID] VRN-TST002-FNC016 · TEST
    def test_a_percentage_label_is_not_filed_as_an_amount(self):
        """「淨利率(%)」曾經被認成 NetIncome —— 把百分比寫進金額欄，是輸出值錯誤不是缺漏。"""
        for label in ("淨利率(%)", "稅後淨利率(%)", "純益率(%)"):
            self.assertEqual(self.db.normalize_metric_name(label), "NetMargin", label)
        for label in ("稅後淨利", "淨利", "歸屬母公司淨利"):
            self.assertEqual(self.db.normalize_metric_name(label), "NetIncome", label)

    # [VRN-ID] VRN-TST002-FNC017 · TEST
    def test_the_synthetic_corpus_carries_every_operand_so_the_checks_run(self):
        """語料湊得齊，七條才跑得動。湊不齊 = 檢查永遠不執行 = 等於沒有檢查。"""
        truth = {"revenue": {2024: 10_000, 2025: 12_000, 2026: 14_500},
                 "eps": {2024: 3.0, 2025: 4.0, 2026: 5.0}, "stock": True}
        wired = set(self.bc.IDENTITY_OPERANDS.values())
        needed = {o for i in self.identities for o in (i.get("target"), i.get("a"), i.get("b")) if o}
        for year in (2024, 2025, 2026):
            figures = self.atl.def_fin_figures(truth, year)
            self.assertTrue(needed <= set(figures), f"{year} 少了 {sorted(needed - set(figures))}")
            for ident in self.identities:
                self.assertEqual(self.bc.identity_state(ident, figures), "PASS",
                                 f"{year} {ident['id']} 應該成立：{figures}")
        self.assertTrue(needed <= wired)

    # [VRN-ID] VRN-TST002-FNC018 · TEST
    def test_the_identities_actually_bite_when_a_number_is_wrong(self):
        """只會過的檢查等於沒有檢查 —— 每一條都要證明它抓得出錯的那一邊。"""
        truth = {"revenue": {2025: 12_000}, "eps": {2025: 4.0}, "stock": True}
        good = self.atl.def_fin_figures(truth, 2025)
        broken_by = {"GP_SUB": "gross_profit", "GM_DIV": "gross_margin", "OP_SUB": "op_profit",
                     "OPM_DIV": "op_margin", "NM_DIV": "net_margin", "BS_ADD": "total_assets",
                     "EPS_DIV": "eps"}
        for ident in self.identities:
            field = broken_by[ident["id"]]
            bad = dict(good)
            bad[field] = good[field] * 1.5 + 7.0          # 遠遠超出任何一條的容差
            self.assertEqual(self.bc.identity_state(ident, bad), "FAIL",
                             f"{ident['id']} 把 {field} 弄錯了卻沒抓到")

    # [VRN-ID] VRN-TST002-FNC019 · TEST
    def test_a_missing_operand_is_insufficient_not_a_silent_pass(self):
        truth = {"revenue": {2025: 12_000}, "eps": {2025: 4.0}, "stock": True}
        good = self.atl.def_fin_figures(truth, 2025)
        for ident in self.identities:
            for field in (ident.get("target"), ident.get("a"), ident.get("b")):
                if not field:
                    continue
                short = {k: v for k, v in good.items() if k != field}
                self.assertEqual(self.bc.identity_state(ident, short), "INSUFFICIENT",
                                 f"{ident['id']} 少了 {field} 要回 INSUFFICIENT")


# [VRN-ID] VRN-TST002-CLS003 · CLASS
class def_CorpusLabelsAreAllMappableTests(unittest.TestCase):
    """語料印出來的每一個列標，版面引擎都要對得到科目。

    2026-10-19：把財務表補齊之後，「總負債」與「股東權益」對不到科目 —— 306 個
    UNMAPPED、優先 2，驗收從 57/59 掉到 8/59。不是對映器的錯：它照
    `def05 unmappable_rule：REVIEW_REQUIRED，不猜` 拒絕猜，然後把缺口指出來。
    真正的缺口在操作員冊 —— 它替「資產」補了券商用語「總資產」，卻沒替
    「負債」「權益」補上對稱的「總負債」「股東權益」。

    這一條擋的是整類問題：語料加了新列、冊沒跟上，測試就紅，不用等跑完整輪才發現。
    """

    # [VRN-ID] VRN-TST002-FNC020 · LOGIC
    @classmethod
    def setUpClass(cls):
        cls.regions = def_load("VRN_PageRegions_v0100")
        cls.atl = def_load("VRN_AutoTestLoop")
        ssot = VRN / "ssot"

        # [VRN-ID] VRN-TST002-FNC021 · LOGIC
        def book(name):
            path = ssot / name
            return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}

        cls.ledger = cls.regions.Ledger(book("VRN_FinIdentity_SSOT_v0100.json"),
                                        book("VRN_AnnualExtract_SSOT_v0100.json"),
                                        book("VRN_Method_SSOT_v0100.json"),
                                        book("VRN_OperatorLabels_SSOT_v0100.json"))

    # [VRN-ID] VRN-TST002-FNC022 · TEST
    def test_every_row_label_the_corpus_prints_maps_to_an_operand(self):
        truth = {"revenue": {2024: 10_000, 2025: 12_000, 2026: 14_500},
                 "eps": {2024: 3.0, 2025: 4.0, 2026: 5.0}, "stock": True}
        rows = self.atl.def_table_rows(truth)
        unmapped = [r[0] for r in rows[1:] if not self.ledger.lookup(r[0])]
        self.assertEqual(unmapped, [], f"語料印了這些列標，冊卻對不到科目：{unmapped}")

    # [VRN-ID] VRN-TST002-FNC023 · TEST
    def test_the_broker_wording_for_the_balance_sheet_is_in_the_book(self):
        """券商寫「總資產／總負債／股東權益」，MOPS 寫「資產總額／負債總額／權益總額」，兩套都要認得。"""
        for label, key in (("總資產", "assets"), ("總負債", "liabilities"), ("股東權益", "equity_total"),
                           ("資產總額", "assets"), ("負債總額", "liabilities"), ("權益總額", "equity_total")):
            self.assertEqual(self.ledger.lookup(label), key, label)

    # [VRN-ID] VRN-TST002-FNC024 · TEST
    def test_a_ratio_label_is_not_swallowed_by_the_amount_label(self):
        """補「總負債」不可以把「總負債比率」搶過來 —— 那會讓比率被當成金額。"""
        self.assertEqual(self.ledger.lookup("總負債比率"), "debt_ratio")
        self.assertEqual(self.ledger.lookup("負債比率"), "debt_ratio")

    # [VRN-ID] VRN-TST002-FNC025 · TEST
    def test_the_books_do_not_claim_the_same_label_for_two_operands(self):
        added = {"總負債", "股東權益"}
        clash = [c for c in self.ledger.conflicts if c.get("label") in added]
        self.assertEqual(clash, [], f"新加的標籤和既有的撞了：{clash}")


if __name__ == "__main__":
    unittest.main()
