#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ===== [VRN:ID:v0100] VRN-TST009 · test_VRN_PageRegions · TEST =====
# AST 注入（只加註解，AST 不變）：類別 5 · 函式 36；逐一編號在 ssot/VRN_ID_SSOT_v0100.json
# ===== [VRN:ID:END] =====
"""VRN_PageRegions v0100 (operator 2026-10-11): stock reports only; file name decomposed; pages cut left / right then
top / bottom; tables restored into rows; add / subtract / divide identities; target price and valuation; one SQLite file.
The mother engines are byte copies and read VRN's own books."""

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
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

VRN = Path(__file__).resolve().parents[1]


# [VRN-ID] VRN-TST009-FNC001 · IO
def def_load(name, path):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


# [VRN-ID] VRN-TST009-FNC002 · LOGIC
def def_has_fitz():
    return importlib.util.find_spec("fitz") is not None


# [VRN-ID] VRN-TST009-CLS001 · CLASS
class def_PageRegionsTests(unittest.TestCase):
    # [VRN-ID] VRN-TST009-FNC003 · LOGIC
    @classmethod
    def setUpClass(cls):
        cls.R = def_load("VRN_PageRegions_v0100", VRN / "engine" / "VRN_PageRegions_v0100.py")
        cls.M = cls.R.mother()

    # [VRN-ID] VRN-TST009-FNC004 · TEST
    def test_mother_engines_are_byte_copies_reading_vrn_books(self):
        self.assertEqual(self.M.errors, {})
        self.assertEqual(len(self.M.describe()["engines"]), len(self.R.MOTHER_FILES))
        self.assertEqual(len(self.M.describe()["books"]), len(self.R.BOOK_FILES))
        prov = json.loads((VRN / "ssot" / "VRN_ENGINES_PROVENANCE_v0100.json").read_text(encoding="utf-8"))
        for row in prov["engines"] + prov["books"]:
            data = (VRN / row["file"]).read_bytes().replace(b"\r\n", b"\n")
            self.assertEqual(hashlib.sha256(data).hexdigest(), row["sha256_lf"], "byte copy unchanged: " + row["file"])
        for row in prov["engines"]:
            self.assertNotIn(b"[VRN-ID]", (VRN / row["file"]).read_bytes(), "no comment injection into a mother engine")
            self.assertRegex(row["id"], r"^VRN-MOM\d{3}$")
        layout = self.M.e394._SSOT_CACHE
        self.assertEqual(layout["_path"], "VRN_LayoutRestore_SSOT_v0100.json", "ENG394 reads VRN's copy, not the mother registry")

    # [VRN-ID] VRN-TST009-FNC005 · TEST
    def test_file_name_decomposed_and_only_stock_reports_go_on(self):
        stock = self.R.decompose(self.M, "凱基_2330台積電_20260901_公司更新.pdf")
        self.assertEqual((stock["doc_class"], stock["ticker"]), ("STOCK", "2330"))
        self.assertIn("台積電", stock.get("company_names") or [])
        other = self.R.analyze(VRN / "does-not-exist.pdf", "元大_半導體產業_20260901_產業報告.pdf")
        # 2026-10-15：產業報告改走 COVERAGE（不再是 NOT_STOCK），但仍然不照個股那一套拆。
        self.assertEqual(other["status"], "COVERAGE")
        self.assertEqual(other["process"], "COVERAGE")
        self.assertEqual(other["rows_shape"], "ONE_PER_COVERED_COMPANY")
        self.assertEqual(other["rows"], [], "COVERAGE 不產出個股形狀的列")
        self.assertIn("COVERAGE", other["why"])

    # [VRN-ID] VRN-TST009-FNC006 · TEST
    def test_labels_and_periods(self):
        P = self.R.period_of
        self.assertEqual([P(x)["key"] for x in ("2025E", "FY25", "1Q26", "2026Q2", "2H25", "113年", "114年第3季")],
                         ["2025", "2025", "2026Q1", "2026Q2", "2025H2", "2024", "2025Q3"])
        self.assertIsNone(P("Year to 31 Dec"))
        L = self.M.ledger
        self.assertEqual([L.lookup(x) for x in ("營業毛利(利益)", "毛利率(%)", "每股盈餘(元)", "COGS", "流通在外股數(百萬股)", "營收")],
                         ["gross_profit", "gross_margin", "basic_eps", "cogs", "shares", "revenue"])
        self.assertEqual(self.R.unit_of("毛利率(%)"), "%")

    # [VRN-ID] VRN-TST009-FNC013 · TEST
    def test_fiscal_year_written_as_month_and_year(self):
        """Real run 2026-10-12: foreign brokers print fiscal years as 12/25E or Dec-25E; a date (11/27) or a month (Jan-25) is not one."""
        P = self.R.period_of
        self.assertEqual([(P(x) or {}).get("key") for x in ("12/24", "12/25E", "FY12/25E", "3/26F", "Dec-24A", "Mar-26E")],
                         ["2024", "2025", "2025", "2026", "2024", "2026"])
        self.assertEqual([P(x) for x in ("11/27", "Jan-25", "13/25")], [None, None, None])

    # [VRN-ID] VRN-TST009-FNC007 · LOGIC
    def _rows(self, table):
        return [{"file": "t", "anchor": "p1·T", "page": 1, "metric_raw": k, "metric": k, "block": self.M.ledger.block_of.get(k, ""),
                 "period_raw": p, "period": p, "kind": "", "value": v, "printed": str(v), "unit": ""}
                for k, by in table.items() for p, v in by.items()]

    # [VRN-ID] VRN-TST009-FNC008 · TEST
    def test_add_subtract_divide_measured_never_corrected(self):
        table = {"revenue": {"2025": 1000.0}, "cogs": {"2025": 600.0}, "gross_profit": {"2025": 400.0}, "gross_margin": {"2025": 40.0},
                 "assets": {"2025": 2000.0}, "liabilities": {"2025": 800.0}, "equity_total": {"2025": 1000.0},
                 "net_income": {"2025": 260.0}, "shares": {"2025": 25000.0}, "basic_eps": {"2025": 10.4},
                 "op_margin": {"2025": 0.27}, "operating_income": {"2025": 270.0},
                 "cash_end": {"2025": 500.0}, "cash_begin": {"2025": 400.0}, "cfo": {"2025": 300.0}, "cfi": {"2025": -150.0},
                 "cff": {"2025": -50.0}}
        checks, conflicts = self.R.check_rows(self.M, self._rows(table))
        state = {c["id"]: c["state"] for c in checks}
        self.assertEqual(state["GP_SUB"], "PASS")
        self.assertEqual(state["GM_DIV"], "PASS")
        self.assertEqual(state["BS_ADD"], "FAIL", "2000 vs 800 + 1000: shown, never corrected")
        self.assertEqual(state["OPM_DIV"], "UNIT_SCALE", "0.27 printed for 27 %")
        self.assertEqual(state["EPS_DIV"], "UNIT_SCALE", "shares in thousands: x1000 named, not fixed")
        self.assertEqual(state["CF_ADD"], "INCOMPLETE_COMPONENTS", "Method def09: a missing FX line is never assumed zero")
        self.assertEqual(conflicts, [])
        self.assertEqual(table["equity_total"]["2025"], 1000.0)

    # [VRN-ID] VRN-TST009-FNC012 · TEST
    def test_operator_upload_labels_and_rules_2026_10_11(self):
        """The curated upload book: exact labels, whole-label patterns (never a substring), and three more checks."""
        L = self.M.ledger
        self.assertEqual([L.lookup(x) for x in ("流動資產總計", "購置不動產、廠房及設備", "稅前純益", "負債及權益總計", "debt", "原物料")],
                         ["current_assets", "capex", "pretax_income", "total_liabilities_equity", "", ""])
        table = {"net_change_in_cash": {"2025": 100.0}, "cfo": {"2025": 300.0}, "cfi": {"2025": -150.0}, "cff": {"2025": -60.0},
                 "fx_effect": {"2025": 10.0}, "total_liabilities_equity": {"2025": 2000.0}, "liabilities": {"2025": 800.0},
                 "equity_total": {"2025": 1200.0}, "basic_eps": {"2025": 10.0}, "diluted_eps": {"2025": 10.8}}
        state = {c["id"]: c["state"] for c in self.R.check_rows(self.M, self._rows(table))[0]}
        self.assertEqual((state["CF_NET"], state["BS_TLE"], state["EPS_DIL_LE"]), ("PASS", "PASS", "WARN"))

    # [VRN-ID] VRN-TST009-FNC009 · TEST
    def test_growth_and_annual_sum(self):
        table = {"net_income": {"2024": -50.0, "2025": 120.0}, "net_income_yoy": {"2025": 340.0},
                 "revenue": {"2025": 3700.0, "2025Q1": 800.0, "2025Q2": 900.0, "2025Q3": 950.0, "2025Q4": 1050.0},
                 "revenue_yoy": {"2025": 15.0}}
        checks, _ = self.R.check_rows(self.M, self._rows(table))
        state = {c["id"]: c["state"] for c in checks}
        self.assertEqual(state["YOY:net_income_yoy"], "TURNAROUND_TO_PROFIT")
        self.assertEqual(state["ANNUAL_SUM:revenue"], "PASS")
        self.assertEqual(state["YOY:revenue_yoy"], "INSUFFICIENT", "no 2024 revenue: said, never guessed")

    # [VRN-ID] VRN-TST009-FNC010 · TEST
    def test_target_price_revision_and_valuation_from_text(self):
        ent = self.R.entities(self.M, ["我們將目標價由 NT$1,000 上調至 NT$1,200，以 20x 2026E EPS 60 元評價。", "另以 DCF 交叉驗證。"],
                              "凱基_2330台積電_20260901.pdf")
        tp = ent["target_price"]
        self.assertEqual((tp["prior"], tp["current"], tp["direction"]), (1000.0, 1200.0, "up"))
        self.assertTrue(any(v["method"] == "VAL_PE" and v["check"] == "VERIFIED" for v in ent["valuation"]))
        self.assertIn("VAL_DCF", ent["valuation_methods"])

    # [VRN-ID] VRN-TST009-FNC011 · TEST
    @unittest.skipUnless(def_has_fitz(), "PyMuPDF not installed")
    def test_known_answer_reports_end_to_end(self):
        with tempfile.TemporaryDirectory() as tmp:
            truths = self.R.build_fixtures(Path(tmp) / "fx")
            results, lane = self.R.analyze_many([(Path(tmp) / "fx" / t["file"], t["file"]) for t in truths], temp_dir=Path(tmp) / "w",
                                                workers=2)
            self.assertEqual(lane["lane"], "worker_process")
            bad = [c for r, t in zip(results, truths) for c in self.R.check_fixture(r, t) if not c[1]]
            self.assertEqual(bad, [])
            counts = self.R.write_db(results, Path(tmp) / self.R.DB_NAME)
            self.assertEqual(counts["reports"], 4)
            con = sqlite3.connect(str(Path(tmp) / self.R.DB_NAME))
            try:
                got = con.execute("SELECT value FROM rows_ WHERE metric='gross_profit' AND period='2025'").fetchone()
                lr = con.execute("SELECT COUNT(DISTINCT left_right) FROM regions WHERE category='table' AND left_right<>''").fetchone()
            finally:
                con.close()
            self.assertEqual(got[0], 504.0)
            self.assertEqual(lr[0], 2, "the income statement on the left, the balance sheet on the right")


# [VRN-ID] VRN-TST009-CLS002 · CLASS
class TestDocxTables(unittest.TestCase):
    """2026-10-19 實測：`_docx_text` 把 Word 表格攤平成一欄。

    Word 的表格**每個儲存格裡都有自己的 `<w:p>`**，而舊的讀法是抓全文所有 `<w:p>`
    用換行接起來 —— 一張 15 列 4 欄的表於是變成 60 行一欄，行列結構整個沒了。
    量到的後果（合成語料 107 檔）：

        .pdf   98 檔 → 51 檔有財務列 → 2142 列
        .docx   7 檔 →  0 檔         →    0 列

    非 PDF 的財務表是整張不見，不是掉幾個字。這裡驗的是**形狀**：一列一行、欄間 tab、
    順序照文件走。驗不到的那一半照實說在 VRN_SYSTEM 文件裡 ——
    ENG394（母倉鏡像，不是本倉能改）不認年度欄頭，所以修完形狀仍然沒有財務列。
    """

    # [VRN-ID] VRN-TST009-FNC014 · LOGIC
    @classmethod
    def setUpClass(cls):
        cls.R = def_load("VRN_PageRegions_v0100", VRN / "engine" / "VRN_PageRegions_v0100.py")

    # [VRN-ID] VRN-TST009-FNC015 · LOGIC
    @staticmethod
    def def_docx(blocks):
        """用 w:p／w:tbl 片段組一個最小的 .docx；blocks 是 ('p', 文字) 或 ('tbl', [[欄…]…])。"""
        import zipfile
        parts = []
        for kind, payload in blocks:
            if kind == "p":
                parts.append(f"<w:p><w:r><w:t>{payload}</w:t></w:r></w:p>")
            else:
                rows = ""
                for row in payload:
                    cells = "".join(f"<w:tc><w:p><w:r><w:t>{c}</w:t></w:r></w:p></w:tc>" for c in row)
                    rows += f"<w:tr>{cells}</w:tr>"
                parts.append(f"<w:tbl>{rows}</w:tbl>")
        xml = ('<?xml version="1.0"?><w:document xmlns:w="x"><w:body>' + "".join(parts) + "</w:body></w:document>")
        handle = tempfile.NamedTemporaryFile(suffix=".docx", delete=False)
        handle.close()
        with zipfile.ZipFile(handle.name, "w") as z:
            z.writestr("word/document.xml", xml)
        return Path(handle.name)

    # [VRN-ID] VRN-TST009-FNC016 · TEST
    def test_one_line_per_row_with_tabs_between_cells(self):
        path = self.def_docx([("p", "本文一"),
                              ("tbl", [["項目 (NT$ 百萬元)", "2024A", "2025E"], ["營收", "10,137", "12,151"]]),
                              ("p", "表後的本文")])
        try:
            lines = self.R._docx_text(path).splitlines()
        finally:
            path.unlink(missing_ok=True)
        self.assertEqual(lines, ["本文一",
                                 "項目 (NT$ 百萬元)\t2024A\t2025E",
                                 "營收\t10,137\t12,151",
                                 "表後的本文"], "一列一行、欄間 tab、順序照文件")

    # [VRN-ID] VRN-TST009-FNC017 · TEST
    def test_cells_do_not_each_become_their_own_line(self):
        """舊寫法會把 2 列 3 欄變成 6 行 —— 這條就是釘那個退步。"""
        path = self.def_docx([("tbl", [["a", "b", "c"], ["d", "e", "f"]])])
        try:
            lines = self.R._docx_text(path).splitlines()
        finally:
            path.unlink(missing_ok=True)
        self.assertEqual(len(lines), 2, f"2 列的表應該出 2 行，拿到 {len(lines)} 行")
        self.assertEqual([l.count("\t") for l in lines], [2, 2])

    # [VRN-ID] VRN-TST009-FNC018 · TEST
    def test_a_cell_with_several_paragraphs_stays_one_cell(self):
        import zipfile
        handle = tempfile.NamedTemporaryFile(suffix=".docx", delete=False)
        handle.close()
        cell = "<w:tc><w:p><w:r><w:t>上行</w:t></w:r></w:p><w:p><w:r><w:t>下行</w:t></w:r></w:p></w:tc>"
        xml = ('<?xml version="1.0"?><w:document xmlns:w="x"><w:body>'
               f"<w:tbl><w:tr>{cell}<w:tc><w:p><w:r><w:t>9</w:t></w:r></w:p></w:tc></w:tr></w:tbl>"
               "</w:body></w:document>")
        with zipfile.ZipFile(handle.name, "w") as z:
            z.writestr("word/document.xml", xml)
        try:
            lines = self.R._docx_text(Path(handle.name)).splitlines()
        finally:
            Path(handle.name).unlink(missing_ok=True)
        self.assertEqual(lines, ["上行下行\t9"], "同一格裡的多段不可以拆成兩欄")

    # [VRN-ID] VRN-TST009-FNC019 · TEST
    def test_text_outside_tables_is_unchanged(self):
        """封面欄位（VRN_TitleTrim 也吃這支）靠的是表外段落 —— 它們不可以變。"""
        path = self.def_docx([("p", "華南證券投資顧問  HUANAN Securities Research"),
                              ("p", "世界健身(2762 TT)"),
                              ("tbl", [["營收", "1"]]),
                              ("p", "尾註")])
        try:
            lines = self.R._docx_text(path).splitlines()
        finally:
            path.unlink(missing_ok=True)
        self.assertEqual([l for l in lines if "\t" not in l],
                         ["華南證券投資顧問  HUANAN Securities Research", "世界健身(2762 TT)", "尾註"])


# [VRN-ID] VRN-TST009-CLS003 · CLASS
class TestGluedBrokerInFileName(unittest.TestCase):
    """操作員 2026-10-20：「把那 3 筆缺的補到 100% 過關」。

    `3653健策凱基投顧 向子慧 (3).txt` 的公司（健策）在正文出現 **0 次**，只黏在檔名裡，
    而且代號＋公司＋券商三段之間一個分隔符都沒有。ENG396 是 MIRROR_MOTHER（不能改），
    它要看得到邊界才認得公司名 —— 所以 VRN 這邊把 token 切開，**公司名還是由 ENG396 認**。
    """

    # [VRN-ID] VRN-TST009-FNC020 · LOGIC
    @classmethod
    def setUpClass(cls):
        cls.R = def_load("VRN_PageRegions_v0100", VRN / "engine" / "VRN_PageRegions_v0100.py")

    # [VRN-ID] VRN-TST009-FNC021 · TEST
    def test_the_split_opens_only_the_shape_it_is_for(self):
        split = self.R._split_glued_broker
        aliases = ["凱基投顧", "凱基", "華南投顧", "兆豐"]
        self.assertEqual(split("3653健策凱基投顧 向子慧 (3)", "3653", aliases),
                         "_3653_健策_凱基投顧 向子慧 (3)")
        # 實測語料裡另外三個「長得像」的 token，三道守門逐一擋掉
        self.assertEqual(split("晶心科(6533,N,中立)-CTBC251208", "6533", aliases), "", "逗號開頭不是公司名，尾巴也沒有券商別名")
        self.assertEqual(split("第一場 2026年投資大趨勢 - 華南投顧 -1141201", "3653", aliases), "", "2026 不是這份報告的代號")
        self.assertEqual(split("第二場 2026海外投資展望 - 華南永昌海外商品部", "2026", aliases), "", "尾巴不是冊上的券商別名")
        self.assertEqual(split("3653健策", "3653", aliases), "", "沒有券商黏在後面：走原本那條 workaround，不是這一條")
        self.assertEqual(split("3653凱基投顧", "3653", aliases), "", "切完公司名是空的")
        self.assertEqual(split("3653健策凱基投顧", "3653", []), "", "冊讀不到就不切")
        self.assertEqual(split("3653健策凱基投顧", "", aliases), "", "沒有代號就不切")

    # [VRN-ID] VRN-TST009-FNC022 · TEST
    def test_eng396_names_the_company_once_the_boundary_is_open(self):
        """端到端：檔名拆解要給出 健策 —— 而且名字是 ENG396 認的，不是這裡剝字串剝出來的。"""
        M = self.R.mother()
        if M.e396 is None:
            self.skipTest("ENG396 不在")
        self.assertIn("凱基投顧", M.broker_aliases(), "冊上要有這個中文別名，切點才找得到")
        row = self.R.decompose(M, "3653健策凱基投顧 向子慧 (3).txt")
        self.assertEqual(row.get("ticker"), "3653")
        self.assertEqual(row.get("company_names"), ["健策"])
        # 原本就認得的檔名一字不動
        self.assertEqual(self.R.decompose(M, "凱基投顧_2637 慧洋-KY_賴偉中_20260915.pdf").get("company_names"), ["慧洋"])

    # [VRN-ID] VRN-TST009-FNC023 · TEST
    def test_the_alias_set_is_the_one_the_engines_use(self):
        """別名要取**首頁引擎組好的那一張表**，不是生冊的 `aliases` 陣列。

        Codex PR #74 P2：生冊 v0100 有 10 筆記錄（華南、日盛、統一、大華、合庫、康和、宏遠、
        麥格理、里昂、摩根士丹利）的 canonical key 本身就是中文名、底下卻沒有 `aliases` 陣列。
        只讀 `aliases` 會把它們整批漏掉 —— `3653健策華南投顧.txt` 照樣切不開（實測他舉的例子就是這一個）。
        """
        M = self.R.mother()
        if M.e396 is None:
            self.skipTest("ENG396 不在")
        names = M.broker_aliases()
        for one in ("華南投顧", "華南", "華南永昌", "日盛", "摩根士丹利", "凱基投顧"):
            self.assertIn(one, names, f"{one} 要在別名集合裡")
        self.assertEqual(self.R.decompose(M, "3653健策華南投顧.txt").get("company_names"), ["健策"],
                         "Codex 舉的那一個檔名")

    # [VRN-ID] VRN-TST009-FNC024 · TEST
    def test_the_cheap_shape_check_guards_the_lazy_load(self):
        """沒有「代號後面黏中文」的 token 就連問都不問 —— 別名表要載首頁引擎，不能每個檔都載。"""
        glued = self.R._glued_token
        self.assertEqual(glued("3653健策凱基投顧 向子慧 (3)", "3653"), "3653健策凱基投顧")
        self.assertEqual(glued("凱基投顧_2637 慧洋-KY_賴偉中_20260915", "2637"), "", "代號自己一個 token，沒黏")
        self.assertEqual(glued("GS-1590 20251203", "1590"), "")
        self.assertEqual(glued("3653健策", ""), "", "沒有代號就不問")


# [VRN-ID] VRN-TST009-CLS004 · CLASS
class TestTextBodyThatTheMotherDropped(unittest.TestCase):
    """文字檔沒有版面座標，母引擎 ENG394 的扁平表解析會把內文一起吃掉。

    實測 2026-10-20（106 檔）：8 個 .docx／.txt **每一檔**都只收到八成 ——
    `3653健策…txt` 387 字只收 312 字，漏的正是「主要動能…毛利率可望維持在高檔」與
    「催化因素…風險…」那兩句（四重點第 3、4 點的料）；合成語料上 12 行內文可以一行都不收。
    母引擎在 `engine/mother/` 是鏡像不能改，所以補在 VRN 這一側：
    **來源裡整行沒被收走的，照原文補回 body**，並把補了幾行記在完整度那一列。
    """

    # [VRN-ID] VRN-TST009-FNC025 · LOGIC
    @classmethod
    def setUpClass(cls):
        cls.R = def_load("VRN_PageRegions_v0100", VRN / "engine" / "VRN_PageRegions_v0100.py")
        cls.M = cls.R.Mother()
        if cls.M.e394 is None:
            raise unittest.SkipTest("ENG394 不在")

    TEXT = "\n".join(["凱基證券投資顧問  KGI Securities Research",
                      "向子慧(3653 TT)  營運動能延續，評價仍具吸引力",
                      "報告日期：2026/09/16    Bloomberg 3653 TT    Yahoo 3653.TW",
                      "投資評等：賣出    目標價：NT$632.5    收盤價：NT$486.5",
                      "分析師 王小明  analyst@example-research.com  (02)2181-8888",
                      "我們預估向子慧 2025 年稀釋 EPS 13.23 元，2026 年 17.07 元。",
                      "主要動能來自 AI 伺服器需求、產品組合改善與新產能開出，毛利率可望維持在高檔。",
                      "催化因素：新客戶認證通過、下半年旺季；風險：匯率波動與原物料成本上升。",
                      "項目 (NT$ 百萬元)\t2024A\t2025E\t2026E",
                      "營收\t19,727\t22,721\t26,073",
                      "毛利率(%)\t38.5\t39.2\t40.1",
                      "稅後淨利\t2,367\t2,840\t3,389",
                      "每股盈餘(元)\t10.81\t13.23\t17.07", ""])

    # [VRN-ID] VRN-TST009-FNC026 · TEST
    def test_every_character_of_a_text_report_is_captured(self):
        """冊上的規矩就是 ≥ 99.9% GREEN。修之前這一份是 80.62% RED、漏 75 字。"""
        page = (self.M.e394.text_restore(self.TEXT)["completeness"]["pages"] or [{}])[0]
        self.assertEqual((page["state"], page["missing_chars"]), ("GREEN", 0), page)
        self.assertEqual(page["captured"], 100.0)

    # [VRN-ID] VRN-TST009-FNC027 · TEST
    def test_the_dropped_lines_come_back_verbatim_and_say_so(self):
        """補回來的是**原文**，而且標得出來是補的 —— 補不等於沒事。"""
        res = self.M.e394.text_restore(self.TEXT)
        back = [b["text"] for b in res["body"] if b.get("recovered")]
        self.assertIn("主要動能來自 AI 伺服器需求、產品組合改善與新產能開出，毛利率可望維持在高檔。", back)
        self.assertIn("催化因素：新客戶認證通過、下半年旺季；風險：匯率波動與原物料成本上升。", back)
        self.assertEqual((res["completeness"]["pages"] or [{}])[0]["recovered_lines"], len(back))
        self.assertTrue(all(b.get("why") for b in res["body"] if b.get("recovered")), "補的要寫為什麼")
        bare = lambda t: "".join(str(t or "").split())
        for b in [x for x in res["body"] if x.get("recovered")]:
            at, to = b["anchor"][1:].split("-")                      # 定位照母引擎的寫法 c<起>-<迄>，而且真的指到原文
            # 比對去掉空白再比：母引擎自己會把連續空白收掉，但一個字都不准多、不准少
            self.assertEqual(bare(self.TEXT[int(at):int(to)]), bare(b["text"]), b["anchor"])
        for b in [x for x in res["body"] if x.get("recovered") and x["text"] in self.TEXT]:
            self.assertEqual(b["subcategory"], "BODY", "句子表的次類別是必填欄")

    # [VRN-ID] VRN-TST009-FNC028 · TEST
    def test_a_line_the_mother_did_keep_is_not_added_twice(self):
        """母引擎收走的行不准再補一次（表格那幾行也算收走了）。"""
        res = self.M.e394.text_restore(self.TEXT)
        back = [b["text"] for b in res["body"] if b.get("recovered")]
        for line in ("向子慧(3653 TT)  營運動能延續，評價仍具吸引力", "營收\t19,727\t22,721\t26,073",
                     "項目 (NT$ 百萬元)\t2024A\t2025E\t2026E"):
            self.assertNotIn(line.strip(), back, line)

    # [VRN-ID] VRN-TST009-FNC029 · TEST
    def test_a_half_captured_line_is_extended_not_duplicated(self):
        """Codex PR #78 P2：母引擎只收到半行時，整行補回去會和原塊重疊、同一句出現兩次。

        用**來源字元區間**判重疊（不是模糊比字）：疊到了就把原塊的尾巴接長，不另開一塊。
        """
        res = self.M.e394.text_restore(self.TEXT)
        joined = "".join(b["text"] for b in res["body"])
        self.assertEqual(joined.count("催化因素"), 1, "補回的句子不准和原塊重疊")
        eps = "我們預估向子慧"
        self.assertEqual(sum(1 for b in res["body"] if eps.replace(" ", "") in b["text"].replace(" ", "")), 1,
                         [b["text"][-30:] for b in res["body"]])
        host = next(b for b in res["body"] if eps.replace(" ", "") in b["text"].replace(" ", ""))
        self.assertTrue(host["text"].replace(" ", "").endswith("17.07元。"), host["text"][-20:])

    # [VRN-ID] VRN-TST009-FNC030 · TEST
    def test_recovered_lines_are_numbered_in_source_order(self):
        """Codex PR #78 P2：表在前、內文在後時，補回的塊接在最後面會讓句號倒著發。"""
        table = "\n".join(["項目 (NT$ 百萬元)\t2024A\t2025E\t2026E", "營收\t19,727\t22,721\t26,073",
                           "毛利率(%)\t38.5\t39.2\t40.1", "稅後淨利\t2,367\t2,840\t3,389",
                           "每股盈餘(元)\t10.81\t13.23\t17.07"])
        res = self.M.e394.text_restore("開頭這一句在表前面，會被吞掉。\n第二句也在表前面。\n" + table + "\n結論這一句在表後面。")
        starts = [int(b["anchor"][1:].split("-")[0]) for b in res["body"]]
        self.assertEqual(starts, sorted(starts), [(b["no"], b["anchor"], b["text"][:16]) for b in res["body"]])
        self.assertTrue(res["body"][0]["text"].startswith("開頭這一句"), res["body"][0]["text"][:20])

    # [VRN-ID] VRN-TST009-FNC031 · TEST
    def test_the_recovery_is_written_out_not_just_held_in_memory(self):
        """Codex PR #78 P2：補回的證據要留在輸出表裡，不能只活在記憶體 ——
        `vrn_regions_completeness.recovered_lines` 與 `vrn_regions_sentences.recovered` 都要有，冊上也要宣告。"""
        book = json.loads((VRN / "ssot" / "VRN_Output_Header_SSOT_v0109.json").read_text(encoding="utf-8"))
        for table, name in (("vrn_regions_completeness", "recovered_lines"), ("vrn_regions_sentences", "recovered")):
            self.assertIn(name, [c["name"] for c in book["tables"][table]["columns"]], table)
        src = (VRN / "engine" / "VRN_PageRegions_v0100.py").read_text(encoding="utf-8")
        self.assertIn("recovered_lines INTEGER", src, "SQLite 的 completeness 表要有這一欄")
        self.assertIn("recovered INTEGER", src, "SQLite 的 sentences 表要有這一欄")

    # [VRN-ID] VRN-TST009-FNC032 · TEST
    def test_nothing_to_recover_stays_nothing(self):
        """沒有漏的時候一行都不補（護欄：補回機制不准無中生有）。"""
        res = self.M.e394.text_restore("只有一行內文，沒有表。\n第二行也是內文。")
        page = (res["completeness"]["pages"] or [{}])[0]
        self.assertEqual(page["state"], "GREEN")
        self.assertEqual(page["recovered_lines"], 0, [b["text"] for b in res["body"] if b.get("recovered")])


# [VRN-ID] VRN-TST009-CLS005 · CLASS
class TestHelperEnginesThatAreNotHere(unittest.TestCase):
    """母引擎自己還要叫的**助手引擎**缺席，要有人喊。

    實測 2026-10-20：`engine/mother/` 只鏡了五支，而 ENG393 DocClassVerify 還要 eng072／eng073／eng114，
    三支都不在。ENG393 整路靜默降級 —— 107 檔實測 `broker_raw` 0/107、`report_date` 0/107、
    `fine_kind_eng073` 與 `fine_type_eng114` 全 None，連「這四位數是不是年份」的代號守衛
    （ENG073 的 `_date_spans` / `_is_year_like`）都沒跑 —— 而 `Mother.errors` 是空的。

    本機 VDF 資料庫缺席會在三個地方報出來；缺一支**引擎**卻一聲不響。不知道不等於沒事。
    """

    # [VRN-ID] VRN-TST009-FNC033 · LOGIC
    @classmethod
    def setUpClass(cls):
        cls.R = def_load("VRN_PageRegions_v0100", VRN / "engine" / "VRN_PageRegions_v0100.py")
        cls.M = cls.R.Mother()

    # [VRN-ID] VRN-TST009-FNC034 · TEST
    def test_the_absent_helpers_are_named(self):
        """缺哪幾支要指名道姓，不是只說「有東西缺」。"""
        self.assertTrue(self.M.degraded, "ENG393 的三支助手都不在這個倉裡，不該是空的")
        self.assertEqual(sorted(self.M.degraded), ["eng393:eng072", "eng393:eng073", "eng393:eng114"],
                         self.M.degraded)
        self.assertTrue(all(v for v in self.M.degraded.values()), "每一支都要寫為什麼")

    # [VRN-ID] VRN-TST009-FNC035 · TEST
    def test_absent_helpers_do_not_blow_up_the_regions_gate(self):
        """助手缺席不致命：不准混進 errors —— 混進去 G15 會直接 FAIL 收攤，讀得到的值就全不驗了。"""
        self.assertNotIn("eng393:eng073", self.M.errors)
        self.assertEqual(self.M.errors, {}, "這個倉的五支母引擎與冊都在")
        self.assertIn("degraded", self.M.describe())

    # [VRN-ID] VRN-TST009-FNC036 · TEST
    def test_the_probe_only_asks_zero_argument_accessors(self):
        """探測不准把要參數的函式也叫下去（ENG392 的 eng072_check 就是），叫爆了不算助手缺席。"""
        self.assertNotIn("eng392:eng072_check", self.M.degraded)
        for key in self.M.degraded:
            self.assertRegex(key, r"^eng\d{3}:eng\d{3}$", key)


if __name__ == "__main__":
    unittest.main()
