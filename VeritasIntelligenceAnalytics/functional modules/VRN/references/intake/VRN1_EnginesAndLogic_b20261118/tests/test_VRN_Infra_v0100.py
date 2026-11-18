#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ===== [VRN:ID:v0100] VRN-TST008 · test_VRN_Infra_v0100 v0100 · TEST =====
# AST 注入（只加註解，AST 不變）：類別 5 · 函式 29；逐一編號在 ssot/VRN_ID_SSOT_v0100.json
# ===== [VRN:ID:END] =====
"""TEMP store and its deletion rules, AST ID injection (comments only, AST unchanged, numbers never recycled),
the local VDF database reader (NAME / ADJ CLOSE, read-only), and the REGEX / synonym books by category."""

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

import ast
import hashlib
import importlib.util
import json
import os
import shutil
import sys
import tempfile
from datetime import datetime
import unittest
from pathlib import Path

VRN = Path(__file__).resolve().parents[1]


# [VRN-ID] VRN-TST008-FNC001 · IO
def def_load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


# [VRN-ID] VRN-TST008-FNC002 · LOGIC
def def_has(module):
    try:
        return importlib.util.find_spec(module) is not None
    except (ImportError, ValueError):
        return False


# [VRN-ID] VRN-TST008-CLS001 · CLASS
class def_TempStoreTests(unittest.TestCase):
    # [VRN-ID] VRN-TST008-FNC003 · LOGIC
    def setUp(self):
        self.T = def_load("vrn_test_tempstore", VRN / "engine" / "VRN_TempStore_v0100.py")
        self.saved = {k: os.environ.get(k) for k in ("VIA_TEMP_ROOT", "VRN_TEMP_RUN", "TEMP", "TMP", "TMPDIR")}
        self.tempdir = tempfile.gettempdir()
        self.root = tempfile.mkdtemp(prefix="vrn-temp-test-")
        os.environ["VIA_TEMP_ROOT"] = self.root

    # [VRN-ID] VRN-TST008-FNC004 · LOGIC
    def tearDown(self):
        if self.T.current_run() is not None:
            self.T.close_run()
        for k, v in self.saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        tempfile.tempdir = self.tempdir
        shutil.rmtree(self.root, ignore_errors=True)

    # [VRN-ID] VRN-TST008-FNC005 · TEST
    def test_rolling_marker_and_never_delete_rules(self):
        T = self.T
        for _ in range(3):
            T.open_run("vrn_t", keep=2)
            T.close_run()
        tool = Path(self.root) / "vrn_t"
        foreign = tool / "run_00000000_000000_000000_9"       # no VRN marker: never deleted
        foreign.mkdir()
        (foreign / "x.bin").write_bytes(b"x")
        guarded = tool / "run_00000000_000000_000000_8_ssot"   # marker, but a never-delete word in its path
        guarded.mkdir()
        (guarded / T.MARKER).write_text(json.dumps({"tool": "vrn_t", "engine": T.ENGINE}), encoding="utf-8")
        run = T.open_run("vrn_t", keep=1)
        left = sorted(p.name for p in tool.iterdir())
        self.assertIn(foreign.name, left)
        self.assertIn(guarded.name, left)
        self.assertIn(run.name, left, "the open run is never deleted")
        self.assertEqual(len([n for n in left if n not in (foreign.name, guarded.name)]), 1, "only the newest run of VRN's own")
        kept = {g["folder"]: g.get("kept_because") for g in T.LAST_SWEEP if not g.get("deleted")}
        self.assertEqual(kept.get(foreign.name), "no VRN owner marker")
        self.assertEqual(kept.get(guarded.name), "never-delete word in path")
        ledger = [json.loads(l) for l in (Path(self.root) / T.LEDGER).read_text(encoding="utf-8").splitlines()]
        self.assertTrue(ledger and all(row["by"] == T.ENGINE and row["rule"] for row in ledger))
        T.close_run()

    # [VRN-ID] VRN-TST008-FNC006 · TEST
    def test_temp_points_into_the_run_and_comes_back(self):
        T = self.T
        before = (os.environ.get("TEMP"), tempfile.gettempdir())
        run = T.open_run("vrn_t")
        self.assertEqual((os.environ["TEMP"], tempfile.gettempdir()), (str(run), str(run)))
        ref = T.put_json("pages", "a.pdf", {"lines": ["目標價 100"]})
        self.assertEqual(T.get_json(ref), {"lines": ["目標價 100"]})
        T.close_run(drop=True)
        self.assertEqual((os.environ.get("TEMP"), tempfile.gettempdir()), before)
        self.assertFalse(run.exists(), "drop at end deletes this run (and records it)")
        self.assertEqual(T.put_json("pages", "b.pdf", {}), "", "no open run: the caller keeps it in memory")

    # [VRN-ID] VRN-TST008-FNC022 · TEST
    def test_a_run_open_in_another_process_is_never_deleted(self):
        """Codex P1 on #40: two overlapping runs of one tool -- the other process's open run survives any sweep."""
        import subprocess
        child = ("import importlib.util, sys\n"
                 "spec = importlib.util.spec_from_file_location('t', sys.argv[1]); t = importlib.util.module_from_spec(spec)\n"
                 "spec.loader.exec_module(t)\n"
                 "print(t.open_run('vrn_t', redirect=False), flush=True)\n"
                 "sys.stdin.readline()\n"
                 "t.close_run()\n")
        env = dict(os.environ, VIA_TEMP_ROOT=self.root)
        proc = subprocess.Popen([sys.executable, "-c", child, str(VRN / "engine" / "VRN_TempStore_v0100.py")],
                                stdin=subprocess.PIPE, stdout=subprocess.PIPE, env=env, text=True)
        try:
            other = Path(proc.stdout.readline().strip())
            self.assertTrue(other.is_dir())
            mine = self.T.open_run("vrn_t", keep=1, max_gb=0.0000001)   # rolling and size cap both want it gone
            self.assertTrue(other.exists(), "the other process's open run is kept")
            kept = {g["folder"]: g.get("kept_because") for g in self.T.LAST_SWEEP if not g.get("deleted")}
            self.assertEqual(kept.get(other.name), "active run (lock held)")
            self.assertTrue(mine.exists())
            self.T.close_run()
        finally:
            proc.communicate("done\n", timeout=60)
        self.T.open_run("vrn_t", keep=1)                                  # once it has closed, it rolls like any other
        self.assertFalse(other.exists())

    # [VRN-ID] VRN-TST008-FNC029 · TEST
    def test_two_runs_in_the_same_clock_tick_do_not_collide(self):
        """Windows CI 2026-10-19 實際紅過：run_<時間戳>_<pid> 同一格時鐘開兩次就撞名。

        Windows 的系統時鐘一格約 15.6 ms，同一個 process 連開兩次 run 會拿到同一個 %f，
        mkdir(exist_ok=False) 直接丟 FileExistsError 把整輪帶走
        （實際紅在 run_20261019_072539_803660_6732）。這裡把時鐘凍住，讓那一格必然發生。
        """
        T = self.T
        frozen = datetime(2026, 10, 19, 7, 25, 39, 803660)
        real = T.datetime
        T.datetime = type("D", (), {"now": staticmethod(lambda: frozen)})
        try:
            first = T.open_run("vrn_t", keep=9)
            T.close_run()
            second = T.open_run("vrn_t", keep=9)
            T.close_run()
        finally:
            T.datetime = real
        self.assertNotEqual(first, second, "同一格時鐘的兩個 run 不可以是同一個資料夾")
        self.assertTrue(first.exists() and second.exists())
        # sweep 靠名字排序決定「舊的在前」，所以序號不能排到時間戳前面去
        self.assertEqual(sorted((first.name, second.name)), [first.name, second.name])
        self.assertTrue(second.name.startswith(first.name), (first.name, second.name))

    # [VRN-ID] VRN-TST008-FNC023 · TEST
    def test_a_failed_delete_is_recorded_as_failed(self):
        """Codex P2 on #40: rmtree hides errors; the ledger says FAILED and the folder is reported as kept."""
        T = self.T
        old = T.open_run("vrn_t", keep=9)
        T.close_run()
        real = T.shutil.rmtree
        T.shutil.rmtree = lambda *a, **k: None           # a file in use on Windows: nothing is removed
        try:
            T.open_run("vrn_t", keep=1)
        finally:
            T.shutil.rmtree = real
        self.assertTrue(old.exists())
        entry = next(g for g in T.LAST_SWEEP if g["folder"] == old.name)
        self.assertEqual((entry["deleted"], entry["kept_because"]), (False, "delete failed (file in use?)"))
        last = json.loads((Path(self.root) / T.LEDGER).read_text(encoding="utf-8").splitlines()[-1])
        self.assertEqual((last["purged"], last["result"]), (old.name, "FAILED"))
        T.close_run()

    # [VRN-ID] VRN-TST008-FNC007 · TEST
    def test_size_cap_deletes_oldest_first(self):
        T = self.T
        old = T.open_run("vrn_t", keep=9)
        (old / "big.bin").write_bytes(b"\0" * 300_000)
        T.close_run()
        new = T.open_run("vrn_t", keep=9, max_gb=0.0001)       # ~107 KB cap
        self.assertFalse(old.exists())
        self.assertTrue(new.exists())
        self.assertTrue(any(g.get("rule", "").startswith("max_gb") and g.get("deleted") for g in T.LAST_SWEEP))
        self.assertTrue(all("folder" in g for g in T.LAST_SWEEP), "every sweep entry names its folder (P10 reads it)")
        main = def_load("vrn_test_main_p10", VRN / "VRN_Main_v0100.py")
        rows = main.def_gate_temp({"run": str(new), "swept": list(T.LAST_SWEEP)}, {"mb": 0.0})
        self.assertIn(old.name, rows[1]["detail"])


# [VRN-ID] VRN-TST008-CLS002 · CLASS
class def_AstIdTests(unittest.TestCase):
    # [VRN-ID] VRN-TST008-FNC008 · LOGIC
    def setUp(self):
        self.work = Path(tempfile.mkdtemp(prefix="vrn-astid-"))
        for sub in ("engine", "tests", "ssot"):
            (self.work / sub).mkdir()
        (self.work / "engine" / "VRN_Toy.py").write_text(
            '# -*- coding: utf-8 -*-\n"""Toy engine."""\nTOY_VERSION = "v0101"\n\n\n'
            'class Box:\n    """A box."""\n\n    def load_items(self):\n        return [1]\n\n\n'
            '@staticmethod\ndef extract_price(text):\n    """Read a price."""\n    return 1\n', encoding="utf-8")
        (self.work / "Invoke-Toy.ps1").write_text("﻿<#\n.SYNOPSIS\n  toy\n#>\nparam()\n", encoding="utf-8")
        self.A = def_load("vrn_test_astid", VRN / "engine" / "VRN_AstId_v0100.py")

    # [VRN-ID] VRN-TST008-FNC009 · LOGIC
    def tearDown(self):
        shutil.rmtree(self.work, ignore_errors=True)

    # [VRN-ID] VRN-TST008-FNC010 · TEST
    def test_comments_only_idempotent_and_numbers_never_recycled(self):
        A, toy = self.A, self.work / "engine" / "VRN_Toy.py"
        before = ast.dump(ast.parse(toy.read_text(encoding="utf-8")))
        r1 = A.run(write=True, root=self.work)
        self.assertEqual(r1["refused"], [])
        text = toy.read_text(encoding="utf-8")
        self.assertEqual(ast.dump(ast.parse(text)), before, "AST unchanged: only comments were added")
        self.assertTrue(text.startswith("# -*- coding: utf-8 -*-\n# ===== [VRN:ID:v0100] VRN-ENG010 · VRN_Toy v0101"))
        self.assertIn("# [VRN-ID] VRN-ENG010-FNC002 · EXTRACT\n@staticmethod\ndef extract_price", text)
        self.assertIn("    # [VRN-ID] VRN-ENG010-FNC001 · IO\n    def load_items", text)
        self.assertEqual(A.run(write=True, root=self.work)["changed"], 0, "a second build changes nothing")
        self.assertEqual(A.check(self.work), [])
        ps = (self.work / "Invoke-Toy.ps1").read_text(encoding="utf-8")
        self.assertTrue(ps.startswith("﻿# ===== [VRN:ID:v0100] VRN-PSL001"), "launcher header after the BOM")
        # remove a function, add another: the old number is RETIRED, the new one is not a recycled number
        toy.write_text(toy.read_text(encoding="utf-8").replace("def extract_price(text):", "def extract_rate(text):"), encoding="utf-8")
        self.assertTrue(any("no number" in p or "stale" in p for p in A.check(self.work)))
        A.run(write=True, root=self.work)
        book = json.loads((self.work / "ssot" / "VRN_ID_SSOT_v0100.json").read_text(encoding="utf-8"))
        items = {v["qualname"]: v for v in book["items"].values()}
        self.assertEqual(items["extract_price"]["state"], "RETIRED")
        self.assertEqual(items["extract_rate"]["id"], "VRN-ENG010-FNC003")

    # [VRN-ID] VRN-TST008-FNC011 · TEST
    def test_a_change_to_the_program_is_refused(self):
        A = self.A
        tag = "# [VRN-ID] " + "VRN-ENG001-FNC001 · LOGIC"
        plan = A.plan("engine/VRN_Toy.py", "ENG", "x = '" + tag + "'\n", A.load_book(self.work))
        self.assertTrue(plan["ok"], "a tag-like text inside a one-line string is not a line of its own: left alone")
        plan = A.plan("engine/VRN_Toy.py", "ENG", 's = """\n' + tag + '\n"""\n', A.load_book(self.work))
        self.assertFalse(plan["ok"], "stripping would change the string, so the AST would change: refused, never written")


# [VRN-ID] VRN-TST008-CLS003 · CLASS
@unittest.skipUnless(def_has("duckdb"), "duckdb not installed")
class def_LocalDBTests(unittest.TestCase):
    # [VRN-ID] VRN-TST008-FNC012 · LOGIC
    @classmethod
    def setUpClass(cls):
        import duckdb
        cls.L = def_load("vrn_test_localdb", VRN / "engine" / "VRN_LocalDB_v0100.py")
        cls.home = Path(tempfile.mkdtemp(prefix="vrn-localdb-"))
        db = cls.home / "vdf_database" / "output_hub" / "mega" / "vdf_tw_market.duckdb"
        db.parent.mkdir(parents=True)
        con = duckdb.connect(str(db))
        con.execute("CREATE TABLE tw_listings_industry(code VARCHAR, name VARCHAR, market VARCHAR, industry_name VARCHAR, yf_ticker VARCHAR)")
        con.execute("INSERT INTO tw_listings_industry VALUES ('2330','台積電','TWSE','半導體','2330.TW')")
        con.execute("CREATE TABLE tw_listings(code VARCHAR, name VARCHAR, market VARCHAR, yf_ticker VARCHAR)")
        con.execute("INSERT INTO tw_listings VALUES ('6488','環球晶','TPEX', NULL)")
        con.execute("CREATE TABLE tw_daily_prices(date DATE, ticker VARCHAR, open DOUBLE, high DOUBLE, low DOUBLE, close DOUBLE, adj_close DOUBLE, volume DOUBLE)")
        con.execute("INSERT INTO tw_daily_prices VALUES ('2026-08-01','2330.TW',0,0,0,800,720,1), ('2026-10-08','2330.TW',0,0,0,1000,1000,1),"
                    "('2026-10-07','6488.TWO',0,0,0,400,380,1), ('2026-10-08','6488.TWO',0,0,0,410,NULL,1)")
        con.close()
        replica = cls.home / "vdf_database" / "output_hub" / "mega_repo_x" / "vdf_tw_market.duckdb"
        replica.parent.mkdir()
        shutil.copy(db, replica)
        cls.db = db

    # [VRN-ID] VRN-TST008-FNC013 · LOGIC
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.home, ignore_errors=True)

    # [VRN-ID] VRN-TST008-FNC014 · LOGIC
    def setUp(self):
        os.environ["VIA_DATA_HOME"] = str(self.home)

    # [VRN-ID] VRN-TST008-FNC015 · LOGIC
    def tearDown(self):
        os.environ.pop("VIA_DATA_HOME", None)

    # [VRN-ID] VRN-TST008-FNC016 · TEST
    def test_name_adj_close_and_factor_chain(self):
        ldb = self.L.LocalDB(today="2026-10-10")
        try:
            self.assertEqual((ldb.status, ldb.path), ("OK", self.db), "repo replicas are skipped")
            f = ldb.fields({"TW_TICKER": "2330", "ReportDate": "2026-09-15", "TargetPrice": 1100})
            self.assertEqual((f["NameDB"], f["AdjCloseReportDate"], f["AdjCloseReport"]), ("台積電", "2026-08-01", 720.0))
            self.assertAlmostEqual(f["TargetPriceAdj"], 1100 * 0.9 / 1.0)
            self.assertEqual(f["LocalDBStatus"], "OK_STALE_REPORT_PRICE", "basis 45 days before the report: kept, marked")
            g = ldb.fields({"TW_TICKER": "6488", "ReportDate": "2026-10-08"})
            self.assertEqual((g["NameDB"], g["NameDBSource"]), ("環球晶", "tw_listings"))
            self.assertEqual((g["AdjCloseLatestDate"], g["AdjCloseLatest"]), ("2026-10-07", 380.0),
                             "the day without adj_close is skipped; close never stands in")
            self.assertEqual(ldb.fields({"TW_TICKER": ""})["LocalDBStatus"], "NO_TICKER")
        finally:
            ldb.close()

    # [VRN-ID] VRN-TST008-FNC017 · TEST
    def test_engine_adds_columns_only(self):
        db_mod = def_load("vrn_test_db_engine", VRN / "engine" / "VRN_Integrated_ReportDatabase_Engine.py")
        cols = db_mod.BASICINFO_COLUMNS
        self.assertEqual(cols[-12:], list(self.L.COLUMNS), "appended at the end, in order")
        ldb = db_mod.open_local_db()
        try:
            row = {"TW_TICKER": "2330", "ReportDate": "2026-10-09", "Name": "台積電(頁面)", "LocalDBStatus": "kept?"}
            extra = db_mod.local_db_fields(ldb, row)
            self.assertNotIn("Name", extra)
            self.assertEqual(extra["NameDB"], "台積電")
        finally:
            ldb.close()


# [VRN-ID] VRN-TST008-CLS004 · CLASS
class def_BookCategoryTests(unittest.TestCase):
    # [VRN-ID] VRN-TST008-FNC018 · LOGIC
    @classmethod
    def setUpClass(cls):
        cls.M = def_load("vrn_test_main", VRN / "VRN_Main_v0100.py")

    # [VRN-ID] VRN-TST008-FNC019 · TEST
    def test_regex_book_has_every_category_once(self):
        book = self.M.def_build_regex_book()
        cats = set(book["counts"]["categories"])
        for want in ("DATE", "BROKER", "EMAIL", "TEL_TW", "TEL_HK", "RATING", "TICKER_TW", "TICKER_YF", "TICKER_BBG", "TARGET_PRICE"):
            self.assertIn(want, cats)
        texts = [e["pattern"] for e in book["patterns"]] + [e["pattern"] for e in book["book_patterns"] if "pattern" in e]
        self.assertEqual(len(texts), len(set(texts)), "a pattern is written once (book copies link to the code entry)")
        self.assertFalse([e for e in book["patterns"] if e["pattern"].endswith(".py")], "the scanner's file list is not a regex")

    # [VRN-ID] VRN-TST008-FNC020 · TEST
    def test_synonym_book_has_the_operator_categories(self):
        book = self.M.def_build_synonym_book()
        terms = book["scopes"]["book_terms"]
        for want in ("DATE", "BROKER", "EMAIL", "RATING", "TICKER_TW", "TICKER_YF", "TICKER_BBG", "TARGET_PRICE", "NAME", "ADJ_CLOSE"):
            self.assertIn(want, terms)
            self.assertTrue(any(terms[want]["terms"].values()), want)
        self.assertEqual(book["conflicts"]["book_broker_vs_runtime"]["split"], [])

    # [VRN-ID] VRN-TST008-FNC021 · TEST
    def test_parallel_map_records_its_lane(self):
        self.M.ACCEL_COVERAGE.clear()
        self.assertEqual(self.M.def_parallel_map(lambda x: x * 2, [3, 1, 2], action="t"), [6, 2, 4])
        self.assertEqual(self.M.ACCEL_COVERAGE[-1]["action"], "t")
        self.assertIn(self.M.ACCEL_COVERAGE[-1]["lane"], ("accel_map", "thread_pool"))



# [VRN-ID] VRN-TST008-CLS005 · CLASS
class def_LocalSsotTests(unittest.TestCase):
    """2026-10-11: VRN's ssot/03_ssot copies, the newest book of each family, and P13 (the operator's local 03_ssot, read-only)."""

    # [VRN-ID] VRN-TST008-FNC024 · LOGIC
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.local = Path(self.tmp.name) / "03_ssot"
        self.local.mkdir()
        self.saved = os.environ.get("VRN_LOCAL_SSOT")
        os.environ["VRN_LOCAL_SSOT"] = str(self.local)
        self.M = def_load("vrn_test_main_p13", VRN / "VRN_Main_v0100.py")
        self.B = def_load("vrn_test_bookcheck_p13", VRN / "engine" / "VRN_BookCheck_v0100.py")

    # [VRN-ID] VRN-TST008-FNC025 · LOGIC
    def tearDown(self):
        if self.saved is None:
            os.environ.pop("VRN_LOCAL_SSOT", None)
        else:
            os.environ["VRN_LOCAL_SSOT"] = self.saved
        self.tmp.cleanup()

    # [VRN-ID] VRN-TST008-FNC026 · TEST
    def test_03ssot_copies_match_their_provenance(self):
        prov = json.loads((VRN / "ssot" / "VRN_03SSOT_PROVENANCE_v0100.json").read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(prov["books"]), 30)
        for row in prov["books"]:
            data = (VRN / row["file"]).read_bytes().replace(b"\r\n", b"\n")
            self.assertEqual(hashlib.sha256(data).hexdigest(), row["sha256_lf"], "byte copy unchanged: " + row["file"])
            self.assertTrue(row["file"].startswith("ssot/03_ssot/"), row["file"])

    # [VRN-ID] VRN-TST008-FNC027 · TEST
    def test_newest_book_of_each_family_wins_and_local_can_be_turned_off(self):
        lex = (VRN / "ssot" / "VRN_FinLexicon_SSOT_v0109.json").read_bytes()
        (self.local / "VRN_FinLexicon_SSOT_v0110.json").write_bytes(lex)
        (self.local / "VRN_FinLexicon_SSOT_v0111.integration.json").write_bytes(b"{}")
        on = self.B.load_books()
        self.assertEqual(Path(on["paths"]["lexicon"]).name, "VRN_FinLexicon_SSOT_v0110.json", "v0110 beats v0109; a report is not a book")
        self.assertEqual(on["sources"]["lexicon"], "本機 03_ssot")
        self.assertEqual(on["sources"]["s05"], "VRN ssot", "S05 v0103 in ssot/ beats the v0102 copy in ssot/03_ssot/")
        off = self.B.load_books(local=False)
        self.assertEqual(Path(off["paths"]["lexicon"]).name, "VRN_FinLexicon_SSOT_v0109.json")
        os.environ["VRN_LOCAL_SSOT"] = ""
        self.assertIsNone(self.B.local_ssot_dir(), "an empty VRN_LOCAL_SSOT turns the local folder off")

    # [VRN-ID] VRN-TST008-FNC028 · TEST
    def test_p13_compares_read_only(self):
        mine = VRN / "ssot" / "03_ssot"
        (self.local / "VRN_DocClass_SSOT_v0100.json").write_bytes((mine / "VRN_DocClass_SSOT_v0100.json").read_bytes())
        (self.local / "VRN_TabFields_v0100.json").write_bytes(b'{"changed": true}')
        (self.local / "VRN_ValuationMethod_SSOT_v0101.json").write_bytes(b"{}")
        (self.local / "VRN_Only_Here_v0100.json").write_bytes(b"{}")
        before = {p.name: p.read_bytes() for p in self.local.iterdir()}
        rows = self.M.def_gate_local_ssot(Path(self.tmp.name))
        states = {r["file"]: r["state"] for r in self.M.def_compare_local_ssot(self.local)["rows"]}
        self.assertEqual(states["VRN_DocClass_SSOT_v0100.json"], "SAME")
        self.assertEqual(states["VRN_TabFields_v0100.json"], "DIFFERENT")
        self.assertEqual(states["VRN_ValuationMethod_SSOT_v0101.json"], "NEWER")
        self.assertEqual(states["VRN_Only_Here_v0100.json"], "LOCAL_ONLY")
        self.assertEqual(states["VRN_ReportMeasure_v0101.json"], "VRN_ONLY")
        self.assertEqual([r["status"] for r in rows], ["PASS", "WARN"])
        self.assertIn("本機 03_ssot：4 檔", rows[0]["item"], "the local folder's own files, not VRN's")
        self.assertTrue(rows[1]["detail"].index("VRN_ValuationMethod") < rows[1]["detail"].index("VRN_Only_Here"), "newer books first")
        self.assertTrue((Path(self.tmp.name) / "VRN_LocalSSOT_Compare_v0100.json").exists())
        self.assertEqual({p.name: p.read_bytes() for p in self.local.iterdir()}, before, "nothing is written in the local folder")
        os.environ["VRN_LOCAL_SSOT"] = ""
        self.assertEqual([r["status"] for r in self.M.def_gate_local_ssot(None)], ["SKIP"])


if __name__ == "__main__":
    unittest.main()
