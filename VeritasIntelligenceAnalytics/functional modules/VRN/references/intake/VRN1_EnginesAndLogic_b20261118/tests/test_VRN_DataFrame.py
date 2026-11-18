#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ===== [VRN:ID:v0100] VRN-TST010 · test_VRN_DataFrame · TEST =====
# AST 注入（只加註解，AST 不變）：類別 2 · 函式 17；逐一編號在 ssot/VRN_ID_SSOT_v0100.json
# ===== [VRN:ID:END] =====
"""VRN_DataFrame v0100 (operator 2026-10-11「範圍限縮獨立系統VRN 輸出DATAFRAME 請確認完成」): every VRN output table as a
pandas DataFrame, checked against ssot/VRN_Output_Header_SSOT_v0101.json (v0100's 13 tables + 5) with the mother's CGC_MDL249
check_table."""

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
import re
import sys
import tempfile
import unittest
from pathlib import Path

VRN = Path(__file__).resolve().parents[1]


# [VRN-ID] VRN-TST010-FNC001 · IO
def def_load(name, path):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


# [VRN-ID] VRN-TST010-FNC002 · LOGIC
def def_has(name):
    return importlib.util.find_spec(name) is not None


# [VRN-ID] VRN-TST010-FNC010 · LOGIC
def undo_edit(tables, entry):
    """Put one declared change back. A null column means the edit is on the table, not a column.

    field == "column" is a whole column: from null means the version added it (undo = drop it),
    otherwise the column spec itself was replaced (undo = put the old spec back).
    field == "table" is a whole table, the same way.
    """
    if entry["field"] == "table":
        # 整張表：from 是 null 表示那一版新增了它，還原就是把整張拿掉
        if entry["from"] is None:
            tables.pop(entry["table"], None)
        else:
            tables[entry["table"]] = entry["from"]
        return
    target = tables[entry["table"]]
    if entry["field"] == "column":
        cols = target["columns"]
        at = next(i for i, c in enumerate(cols) if c["name"] == entry["column"])
        if entry["from"] is None:
            cols.pop(at)
        else:
            cols[at] = entry["from"]
        return
    if entry.get("column"):
        target = next(c for c in target["columns"] if c["name"] == entry["column"])
    target[entry["field"]] = entry["from"]


# [VRN-ID] VRN-TST010-CLS001 · CLASS
class def_DataFrameTests(unittest.TestCase):
    # [VRN-ID] VRN-TST010-FNC003 · LOGIC
    @classmethod
    def setUpClass(cls):
        cls.D = def_load("VRN_DataFrame_v0100", VRN / "engine" / "VRN_DataFrame_v0100.py")
        cls.book = cls.D.load_book()

    # [VRN-ID] VRN-TST010-FNC004 · TEST
    def test_header_book_covers_every_output_and_matches_the_engines(self):
        tables = self.book["tables"]
        self.assertEqual(len(tables), 21)
        undone = json.loads(json.dumps(tables))                 # v0103's documented edits put back -> must equal v0102 word for word
        undone.pop("vrn_ticker_record", None)                   # v0104's one new table (def_HeaderBookV0104Tests checks it)
        for key in sorted(k for k in self.book if re.fullmatch(r"changes_v\d{4}", k)):   # every version's own edit list
            for e in self.book[key]:
                undo_edit(undone, e)
        v0102 = json.loads((VRN / "ssot" / "VRN_Output_Header_SSOT_v0102.json").read_text(encoding="utf-8"))["tables"]
        self.assertEqual(undone, v0102, "v0103 = v0102 + only the edits it lists")
        v0101 = json.loads((VRN / "ssot" / "VRN_Output_Header_SSOT_v0101.json").read_text(encoding="utf-8"))["tables"]
        self.assertEqual(len(v0101), 18)
        for tid, spec in v0101.items():
            self.assertEqual(v0102[tid], spec, f"v0102 keeps v0101's {tid} header word for word")
        old = json.loads((VRN / "ssot" / "VRN_Output_Header_SSOT_v0100.json").read_text(encoding="utf-8"))["tables"]
        self.assertEqual(len(old), 13)
        for tid, spec in old.items():
            self.assertEqual(v0101[tid], spec, f"v0101 keeps v0100's {tid} header word for word (a new version, never an edit)")
        lock = self.D.load_lock()
        for tid, spec in tables.items():
            for c in spec["columns"]:
                self.assertIn(c["dtype"], lock.DTYPES, f"{tid}.{c['name']}")
            self.assertTrue(any(c.get("key") for c in spec["columns"]), f"{tid} has a primary key")
        src = (VRN / "engine" / "VRN_Integrated_ReportDatabase_Engine.py").read_text(encoding="utf-8")
        for tid, const in (("vrn_basic_info", "BASICINFO_COLUMNS"), ("vrn_financial_data", "FINANCIALDATA_COLUMNS")):
            engine_cols = re.findall(r'"([^"]+)"', re.search(const + r"\s*=\s*\[(.*?)\]", src, re.S).group(1))
            self.assertEqual([c["name"] for c in tables[tid]["columns"]], engine_cols, f"{tid} header = the engine's column order")
        regions = (VRN / "engine" / "VRN_PageRegions_v0100.py").read_text(encoding="utf-8")
        for tid, spec in tables.items():
            if spec["source"]["kind"] == "sqlite":
                m = re.search(r'CREATE TABLE IF NOT EXISTS %s \((.*?)\);' % re.escape(spec["source"]["table"]), regions, re.S)
                cols = [part.strip().split()[0] for part in m.group(1).split(",")]
                self.assertEqual([c["name"] for c in spec["columns"]], cols, f"{tid} header = the SQLite schema")

    # [VRN-ID] VRN-TST010-FNC005 · TEST
    def test_lock_is_the_mother_byte_copy(self):
        prov = json.loads((VRN / "ssot" / "VRN_ENGINES_PROVENANCE_v0100.json").read_text(encoding="utf-8"))
        row = next(e for e in prov["engines"] if e["file"].endswith("CGC_MDL249_DataFrameLock_v0100.py"))
        data = (VRN / row["file"]).read_bytes().replace(b"\r\n", b"\n")
        self.assertEqual(hashlib.sha256(data).hexdigest(), row["sha256_lf"])

    # [VRN-ID] VRN-TST010-FNC006 · TEST
    @unittest.skipUnless(def_has("pandas"), "pandas not installed")
    def test_every_judgement_of_the_lock(self):
        import pandas as pd
        lock = self.D.load_lock()
        spec = {"min_rows": 1, "extra_ok": False, "columns": [{"name": "id", "dtype": "str", "required": True, "key": True},
                                                              {"name": "v", "dtype": "float", "required": True}, {"name": "d", "dtype": "date"}]}
        lamp = lambda frame: lock.check_table("t", spec, frame=pd.DataFrame(frame))["lamp"]
        self.assertEqual(lamp({"id": ["a", "b"], "v": ["1", "2.5"], "d": ["2026-10-11", ""]}), "GREEN")
        self.assertEqual(lamp({"id": ["a"], "d": [""]}), "RED")
        self.assertEqual(lamp({"id": ["a"], "v": ["1"], "d": [""], "x": ["?"]}), "YELLOW")
        self.assertEqual(lamp({"id": ["a", "a"], "v": ["1", "2"], "d": ["", ""]}), "RED")
        self.assertEqual(lamp({"id": ["a"], "v": ["one"], "d": [""]}), "RED")
        self.assertEqual(lamp({"id": ["a"], "v": ["1"], "d": ["not a date"]}), "RED")
        self.assertEqual(lamp({"id": [], "v": [], "d": []}), "RED")

    # [VRN-ID] VRN-TST010-FNC007 · TEST
    @unittest.skipUnless(def_has("pandas") and def_has("fitz"), "pandas / PyMuPDF not installed")
    def test_regions_database_becomes_green_dataframes(self):
        import pandas as pd
        R = def_load("VRN_PageRegions_v0100", VRN / "engine" / "VRN_PageRegions_v0100.py")
        with tempfile.TemporaryDirectory() as tmp:
            truths = R.build_fixtures(Path(tmp) / "fx")
            results, _lane = R.analyze_many([(Path(tmp) / "fx" / t["file"], t["file"]) for t in truths], temp_dir=Path(tmp) / "w", workers=2)
            R.write_db(results, Path(tmp) / R.DB_NAME)
            book = dict(self.book, tables={k: v for k, v in self.book["tables"].items() if k.startswith("vrn_regions_")})
            rep = self.D.check(tmp, book=book)
            self.assertEqual({r["table"]: r["lamp"] for r in rep["tables"]}, {k: "GREEN" for k in book["tables"]})
            rows = pd.read_csv(Path(tmp) / "dataframes" / "vrn_regions_rows.csv", encoding="utf-8-sig")
            got = rows[(rows["metric"] == "gross_profit") & (rows["period"].astype(str) == "2025")]["value"].tolist()
            self.assertEqual(got, [504.0], "the restored number survives into the written DataFrame")
            self.assertTrue((Path(tmp) / "dataframes" / "VRN_DataFrame_Lock_v0100.json").is_file())


if __name__ == "__main__":
    unittest.main()


# [VRN-ID] VRN-TST010-CLS002 · CLASS
class def_HeaderBookV0104Tests(unittest.TestCase):
    """v0104 (2026-10-12, 4-digit code -> 15 fields) = v0103's 19 tables untouched + vrn_ticker_record."""

    # [VRN-ID] VRN-TST010-FNC008 · TEST
    def test_v0104_is_v0103_plus_the_record_table(self):
        root = Path(__file__).resolve().parents[1] / "ssot"
        old = json.loads((root / "VRN_Output_Header_SSOT_v0103.json").read_text(encoding="utf-8"))["tables"]
        new = json.loads((root / "VRN_Output_Header_SSOT_v0104.json").read_text(encoding="utf-8"))["tables"]
        for name, spec in old.items():
            self.assertEqual(json.dumps(spec, sort_keys=True), json.dumps(new[name], sort_keys=True), name)
        self.assertEqual(sorted(set(new) - set(old)), ["vrn_ticker_record"])
        cols = [c["name"] for c in new["vrn_ticker_record"]["columns"]]
        self.assertEqual(cols[:4], ["file", "ticker", "yfinance_ticker", "bloomberg_ticker"])
        self.assertIn("upside_pct_state", cols)
        self.assertIn("adj_close_before_report_date", cols)

    # [VRN-ID] VRN-TST010-FNC011 · TEST
    def test_v0105_is_v0104_plus_only_the_edits_it_declares(self):
        """v0105（2026-10-15 產業報告一報告 N 列）：vrn_basic_info 主鍵 = (ReportID, TW_TICKER)，其餘逐字不動。"""
        root = Path(__file__).resolve().parents[1] / "ssot"
        old = json.loads((root / "VRN_Output_Header_SSOT_v0104.json").read_text(encoding="utf-8"))["tables"]
        book = json.loads((root / "VRN_Output_Header_SSOT_v0105.json").read_text(encoding="utf-8"))
        undone = json.loads(json.dumps(book["tables"]))
        for e in book["changes_v0105"]:
            undo_edit(undone, e)
        self.assertEqual(undone, old, "v0105 = v0104 + only the edits it lists")

    # [VRN-ID] VRN-TST010-FNC012 · TEST
    def test_v0106_is_v0105_plus_only_the_edits_it_declares(self):
        """v0106（2026-10-15 三條報告路徑同步）：vrn_focus_files 多一欄 process，其餘逐字不動。"""
        root = VRN / "ssot"
        old = json.loads((root / "VRN_Output_Header_SSOT_v0105.json").read_text(encoding="utf-8"))["tables"]
        book = json.loads((root / "VRN_Output_Header_SSOT_v0106.json").read_text(encoding="utf-8"))
        undone = json.loads(json.dumps(book["tables"]))
        for e in book["changes_v0106"]:
            undo_edit(undone, e)
        self.assertEqual(undone, old, "v0106 = v0105 + only the edits it lists")
        self.assertEqual(book["supersedes"], "VRN_Output_Header_SSOT_v0105.json（原封保留）")
        names = [c["name"] for c in book["tables"]["vrn_focus_files"]["columns"]]
        self.assertIn("process", names, "G06 的三條報告路徑就是照這一欄分流的，冊上要有")
        keys = [c["name"] for c in book["tables"]["vrn_basic_info"]["columns"] if c.get("key")]
        self.assertEqual(keys, ["ReportID", "TW_TICKER"], "一報告 N 列要靠 TW_TICKER 才分得開")

    # [VRN-ID] VRN-TST010-FNC013 · TEST
    def test_v0107_is_v0106_plus_the_summary_points_table(self):
        """v0107（2026-10-16 一標題四重點）：多一張 vrn_summary_points，v0106 的 20 張逐字不動。"""
        root = VRN / "ssot"
        old = json.loads((root / "VRN_Output_Header_SSOT_v0106.json").read_text(encoding="utf-8"))["tables"]
        book = json.loads((root / "VRN_Output_Header_SSOT_v0107.json").read_text(encoding="utf-8"))
        new = book["tables"]
        self.assertEqual(set(new) - set(old), {"vrn_summary_points"}, "這一版只多一張表")
        self.assertEqual(set(old) - set(new), set(), "一張都不准少")
        for tid, spec in old.items():
            self.assertEqual(new[tid], spec, f"v0107 keeps v0106's {tid} header word for word")
        self.assertEqual(book["schema"], "VRN_Output_Header_SSOT_v0107")
        self.assertEqual(book["supersedes"], "VRN_Output_Header_SSOT_v0106.json（原封保留）")
        keys = [c["name"] for c in new["vrn_summary_points"]["columns"] if c["key"]]
        self.assertEqual(keys, ["file", "point_no"], "一份報告四列，所以鍵是 file + point_no")

    # [VRN-ID] VRN-TST010-FNC014 · TEST
    def test_v0108_is_v0107_plus_only_the_agree_column(self):
        """v0108（2026-10-19 操作員「相互對照兩個以上相同即算對照成功」）：vrn_trim_parts 多一欄 agree，21 張表的其餘逐字不動。

        這一條擋的是「冊沒跟上輸出」：欄一加、冊沒加，G16 就判 vrn_trim_parts YELLOW（多出冊上沒有的欄），
        而 YELLOW 不是紅燈、很容易被當成本來就這樣帶過去——v0106 的 process 欄就是這樣紅過一次。
        """
        root = VRN / "ssot"
        old = json.loads((root / "VRN_Output_Header_SSOT_v0107.json").read_text(encoding="utf-8"))["tables"]
        book = json.loads((root / "VRN_Output_Header_SSOT_v0108.json").read_text(encoding="utf-8"))
        undone = json.loads(json.dumps(book["tables"]))
        for e in book["changes_v0108"]:
            undo_edit(undone, e)
        self.assertEqual(undone, old, "v0108 = v0107 + only the edits it lists")
        self.assertEqual(book["schema"], "VRN_Output_Header_SSOT_v0108")
        self.assertEqual(book["supersedes"], "VRN_Output_Header_SSOT_v0107.json（原封保留）")
        self.assertEqual(set(book["tables"]), set(old), "這一版一張表都沒加、沒減")
        spec = next(c for c in book["tables"]["vrn_trim_parts"]["columns"] if c["name"] == "agree")
        self.assertEqual((spec["dtype"], spec["required"], spec["key"]), ("str", False, False),
                         "整數與空字串混在同一欄，G16 寫 parquet 會 ArrowInvalid；一律 str")

    # [VRN-ID] VRN-TST010-FNC016 · TEST
    def test_v0109_is_v0108_plus_only_the_recovery_columns(self):
        """v0109（Codex PR #78 P2「補不等於沒事，要留得下來」）：
        `vrn_regions_completeness` 多一欄 `recovered_lines`、`vrn_regions_sentences` 多一欄 `recovered`，
        21 張表的其餘逐字不動。兩張表都是 `extra_ok: false`，欄加了冊沒加就是 YELLOW。
        """
        root = VRN / "ssot"
        old = json.loads((root / "VRN_Output_Header_SSOT_v0108.json").read_text(encoding="utf-8"))["tables"]
        book = json.loads((root / "VRN_Output_Header_SSOT_v0109.json").read_text(encoding="utf-8"))
        undone = json.loads(json.dumps(book["tables"]))
        for e in book["changes_v0109"]:
            undo_edit(undone, e)
        self.assertEqual(undone, old, "v0109 = v0108 + only the edits it lists")
        self.assertEqual(book["schema"], "VRN_Output_Header_SSOT_v0109")
        self.assertEqual(book["supersedes"], "VRN_Output_Header_SSOT_v0108.json（原封保留）")
        self.assertEqual(set(book["tables"]), set(old), "這一版一張表都沒加、沒減")
        for table, name in (("vrn_regions_completeness", "recovered_lines"), ("vrn_regions_sentences", "recovered")):
            spec = next(c for c in book["tables"][table]["columns"] if c["name"] == name)
            self.assertEqual((spec["dtype"], spec["required"], spec["key"]), ("int", False, False), table)

    # [VRN-ID] VRN-TST010-FNC017 · TEST
    def test_v0110_is_v0109_plus_only_the_confidence_rename(self):
        """v0110（操作員 2026-10-20 裁定「改名加註」）：`vrn_financial_data.ConfidenceScore`
        改名成 `ConfidenceScorePrior`，zh 說清楚它是寫死的先驗值；21 張表的其餘逐字不動。

        實測的理由：那一欄 24,564 列**全部是 0.72**，來源是引擎裡的一行字面值
        `0.72 if period.get("FiscalYear") else 0.62`，冊上沒有任何地方定義它怎麼算 ——
        而旁邊就是 ValidationStatus=PASS，叫它「信心分數」會讓看報表的人以為量過。
        """
        root = VRN / "ssot"
        old = json.loads((root / "VRN_Output_Header_SSOT_v0109.json").read_text(encoding="utf-8"))["tables"]
        book = json.loads((root / "VRN_Output_Header_SSOT_v0110.json").read_text(encoding="utf-8"))
        undone = json.loads(json.dumps(book["tables"]))
        for e in book["changes_v0110"]:
            undo_edit(undone, e)
        self.assertEqual(undone, old, "v0110 = v0109 + only the edit it lists")
        self.assertEqual(book["schema"], "VRN_Output_Header_SSOT_v0110")
        self.assertEqual(book["supersedes"], "VRN_Output_Header_SSOT_v0109.json（原封保留）")
        self.assertEqual(set(book["tables"]), set(old), "這一版一張表都沒加、沒減")
        fin = [c["name"] for c in book["tables"]["vrn_financial_data"]["columns"]]
        self.assertIn("ConfidenceScorePrior", fin)
        self.assertNotIn("ConfidenceScore", fin, "改名就是改名，不可以兩個名字並存")
        spec = next(c for c in book["tables"]["vrn_financial_data"]["columns"] if c["name"] == "ConfidenceScorePrior")
        self.assertIn("固定先驗值", spec["zh"], "名字改了還不夠，冊上要寫它是什麼")
        basic = [c["name"] for c in book["tables"]["vrn_basic_info"]["columns"]]
        self.assertIn("ConfidenceScore", basic,
                      "basic_info 那一欄是 score_basicinfo_confidence() 真的算出來的，不准被一起改掉")

    # [VRN-ID] VRN-TST010-FNC018 · TEST
    def test_the_engine_writes_the_renamed_column_and_leaves_the_measured_one(self):
        """冊改了、引擎沒改就是兩邊各說各話 —— 從引擎原始碼的欄位清單讀出來比對。"""
        src = (VRN / "engine" / "VRN_Integrated_ReportDatabase_Engine.py").read_text(encoding="utf-8")
        self.assertIn('"ConfidenceScorePrior": 0.72 if period.get("FiscalYear") else 0.62', src,
                      "財報數字那一列寫出去的鍵要是新名字")
        self.assertIn('"ConfidenceScore": confidence', src,
                      "basic_info 那一列仍然寫 ConfidenceScore（它是算出來的）")
        block = re.search(r"FINANCIALDATA_NUMERIC_COLUMNS = \((.*?)\)", src, re.S).group(1)
        self.assertIn("ConfidenceScorePrior", block)
        self.assertNotIn('"ConfidenceScore"', block)

    # [VRN-ID] VRN-TST010-FNC015 · TEST
    def test_the_book_in_use_declares_every_column_titletrim_writes(self):
        """表頭冊跟 G17 的輸出是同一份判斷：part_rows 寫出的欄，冊上一欄都不准少、不准多。

        驗的是「跑的那一本」（engine 的 HEADER_BOOK），不是我手挑的檔名——換版忘了改常數，這一條就紅。
        """
        D = def_load("VRN_DataFrame_v0100", VRN / "engine" / "VRN_DataFrame_v0100.py")
        book = D.load_book()
        # 2026-10-20 第二十一輪：原本寫死 "v0110"，於是每出一本新冊這一條就紅一次，
        # 而紅的原因跟它要守的事（欄位對不對）無關。改成問 ssot/ 自己：跑的那一本要是號碼最大的那一本。
        newest = max(q.stem.rsplit("_v", 1)[1] for q in (VRN / "ssot").glob("VRN_Output_Header_SSOT_v*.json"))
        self.assertEqual(book["version"], "v" + newest, "HEADER_BOOK 要指到 ssot/ 裡號碼最大的那一本")
        src = (VRN / "engine" / "VRN_TitleTrim_v0100.py").read_text(encoding="utf-8")
        body = re.search(r"def part_rows\(results\):(.*?)\n    return out", src, re.S).group(1)
        written = re.findall(r'"([a-z_]+)":', body)
        declared = [c["name"] for c in book["tables"]["vrn_trim_parts"]["columns"]]
        self.assertEqual(sorted(set(written)), sorted(declared), "part_rows 寫的欄 = vrn_trim_parts 冊上的欄")
