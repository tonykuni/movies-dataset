"""Speed without changing a single answer (批731; operator 2026-09-24「PS PY檔案都要依規定裝加速器  剛剛跑好慢」).

The workstation's 106-report self-test took 20 minutes for the batch alone and was stopped at the 1800 s ceiling.
What changed, and what each test pins:
  * the batch spreads reports over worker processes (VRN_BatchPool) -> the output rows are the same, in the same order;
  * the evidence core parses a page / an appendix once per file version -> the answer is the same, callers get copies,
    and a file edited in place is read again;
  * the broker deny check normalises its list once -> the same verdicts as the per-call version it replaced;
  * the idempotency gate re-ingests an evenly spread, fixed sample."""

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

import argparse
import importlib.util
import json
import os
import re
import shutil
import sys
import tempfile
import time
import unicodedata
import unittest
from pathlib import Path

ENGINE = Path(__file__).resolve().parents[1] / "engine"


def def_load(name, filename):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, ENGINE / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def def_pdf(path, lines, pages=3):
    import fitz
    doc = fitz.open()
    for p in range(pages):
        page = doc.new_page(width=595, height=842)
        for i, t in enumerate(lines):
            page.insert_text((50, 60 + 16 * i), f"{t} {p}", fontsize=10 if p == 0 else 6, fontname="china-t")
    doc.save(str(path))
    doc.close()


@unittest.skipUnless(importlib.util.find_spec("fitz") and importlib.util.find_spec("pdfplumber"), "PDF libraries absent")
class EvidenceCacheTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.C = def_load("vrn_evidence_core_batch_speed", "VRN_Evidence_Core.py")
        cls.tmp = tempfile.TemporaryDirectory()
        cls.pdf = Path(cls.tmp.name) / "KGI-2330 20260924.pdf"
        def_pdf(cls.pdf, ["台積電 公司更新 買進", "本報告由凱基證券投資顧問股份有限公司提供,版權所有。", "買進(Buy):預期報酬率超過15%"])

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_a_page_is_parsed_once_and_callers_get_copies(self):
        a = self.C.pdf_page_chars(str(self.pdf), 0)
        b = self.C.pdf_page_chars(str(self.pdf), 0)
        self.assertEqual(a, b)
        self.assertIsNot(a[0], b[0])
        a[0][0]["text"] = "changed by a caller"
        self.assertNotEqual(self.C.pdf_page_chars(str(self.pdf), 0)[0][0]["text"], "changed by a caller")
        self.assertEqual(a[1], self.C._pdf_page_chars_parse(str(self.pdf), 0)[1])

    def test_a_file_edited_in_place_is_read_again(self):
        path = Path(self.tmp.name) / "edited.pdf"
        def_pdf(path, ["第一版 買進"], pages=2)
        first = "".join(c["text"] for c in self.C.pdf_page_chars(str(path), 0)[0])
        appendix_first = self.C.appendix_lines(str(path))
        time.sleep(0.01)
        def_pdf(path, ["第二版 賣出 已改寫"], pages=3)
        os.utime(path, ns=(time.time_ns(), time.time_ns() + 1_000_000))
        second = "".join(c["text"] for c in self.C.pdf_page_chars(str(path), 0)[0])
        self.assertIn("第一版", first)
        self.assertIn("第二版", second)
        self.assertNotEqual(appendix_first[1]["n_pages"], self.C.appendix_lines(str(path))[1]["n_pages"])

    def test_the_appendix_answer_is_the_uncached_answer(self):
        self.assertEqual(self.C.appendix_lines(str(self.pdf)), self.C._appendix_lines_read(str(self.pdf)))
        self.assertEqual(self.C.pdf_page_count(str(self.pdf)), self.C._pdf_page_count_open(str(self.pdf)))


class DenyCheckTest(unittest.TestCase):
    """The cached deny check against the per-call version it replaced (copied here as the reference)."""

    @classmethod
    def setUpClass(cls):
        cls.C = def_load("vrn_evidence_core_batch_speed", "VRN_Evidence_Core.py")

    def ref_norm(self, value):
        return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", str(value or ""))).strip().casefold()

    def ref_denied(self, value):
        n = self.ref_norm(value)
        return bool(n) and any(self.ref_norm(k) == n for k in self.C.deny_phrases())

    def ref_shadowed(self, alias, text):
        a = self.ref_norm(alias)
        if not a:
            return False
        if self.ref_denied(a):
            return True
        low = self.ref_norm(text)
        a_spans = list(self.C._alias_spans(a, low))
        if not a_spans:
            return False
        d_spans = []
        for d in self.C.deny_phrases():
            dn = self.ref_norm(d)
            if len(dn) >= len(a) and a in dn:
                d_spans.extend(self.C._alias_spans(dn, low))
        return bool(d_spans) and all(any(ds <= s0 and t0 <= dt for ds, dt in d_spans) for s0, t0 in a_spans)

    def test_same_verdicts_as_the_per_call_version(self):
        phrases = list(self.C.deny_phrases())[:12]
        # a denied phrase that contains the legitimate alias 中信, taken from the list itself (no denied name is spelled
        # in this file -- CGC_MDL177 counts them): the alias is shadowed in one span and free in the other
        longer = next((d for d in self.C.deny_phrases() if "中信" in d and d != "中信"), "")
        aliases = ["中信", "摩根士丹利", "凱基", "元大", "MS", "GS", "Citi", ""] + phrases
        texts = ["本報告由凱基證券投資顧問股份有限公司提供", f"{longer} 研究部 · 中信投顧 買進", f"{longer} 研究部",
                 "Morgan Stanley Research 摩根士丹利", "  ".join(phrases[:3]), ""]
        self.assertTrue(longer, "the deny list names a longer phrase that contains 中信")
        for alias in aliases:
            self.assertEqual(self.C.is_denied_token(alias), self.ref_denied(alias), alias)
            for text in texts:
                self.assertEqual(self.C.deny_shadowed(alias, text), self.ref_shadowed(alias, text), (alias, text))


@unittest.skipUnless(importlib.util.find_spec("fitz") and importlib.util.find_spec("pandas") and importlib.util.find_spec("pyarrow"),
                     "fitz / pandas / pyarrow absent")
class BatchPoolTest(unittest.TestCase):
    def test_the_pool_writes_the_same_rows_in_the_same_order(self):
        db = def_load("vrn_autotest_database_batch_speed", "VRN_Integrated_ReportDatabase_Engine.py")
        pool = def_load("VRN_BatchPool", "VRN_BatchPool.py")
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "in"
            src.mkdir()
            for i, (b, c) in enumerate([("元大", 2330), ("凱基", 2317), ("富邦", 2454), ("群益", 3231), ("永豐", 2308),
                                         ("兆豐", 3706), ("華南", 2606), ("統一", 1301)]):
                def_pdf(src / f"2026092{i + 1}{b}個股報告-測試({c}).pdf", [f"測試公司 ({c}) 公司更新 買進 目標價 {100 + i}元", "預估營收成長"], pages=2)
            outs = {}
            for workers in ("1", "2"):
                os.environ["VRN_BATCH_WORKERS"] = workers
                try:
                    out = Path(td) / f"out{workers}"
                    args = argparse.Namespace(input=str(src), output=str(out), ticker_ssot="", broker_ssot="", rating_ssot="",
                                              online_name_update=False, csv=False, json=True, duckdb=False, google_sheet="",
                                              google_credentials="", run_id="SPEED", self_test=False)
                    db.process_batch(args)
                    outs[workers] = json.loads((out / db.BASICINFO_JSON_NAME).read_text(encoding="utf-8"))
                finally:
                    os.environ.pop("VRN_BATCH_WORKERS", None)
            drop = ("ExtractedAt", "CreatedAt", "UpdatedAt", "ProcessedAt")
            strip = [[{k: v for k, v in r.items() if k not in drop} for r in outs[w]] for w in ("1", "2")]
            self.assertEqual(len(strip[0]), 8)
            self.assertEqual(strip[0], strip[1])
        self.assertEqual(pool.workers_for(3), 1, "a few files stay in this process")

    def test_workers_follow_the_budget_and_the_switch(self):
        pool = def_load("VRN_BatchPool", "VRN_BatchPool.py")
        old = {k: os.environ.get(k) for k in ("VRN_BATCH_WORKERS", "VIA_ACCEL_ACTIVE_THREADS")}
        try:
            os.environ["VRN_BATCH_WORKERS"] = "1"
            self.assertEqual(pool.workers_for(106), 1)
            os.environ.pop("VRN_BATCH_WORKERS")
            os.environ["VIA_ACCEL_ACTIVE_THREADS"] = "3"
            self.assertEqual(pool.workers_for(106), 3)
            os.environ["VIA_ACCEL_ACTIVE_THREADS"] = "40"
            self.assertEqual(pool.workers_for(106), pool.MAX_WORKERS)
        finally:
            for k, v in old.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v


class IdempotencySampleTest(unittest.TestCase):
    def test_the_sample_is_fixed_spread_and_bounded(self):
        loop = def_load("vrn_autotest_loop_batch_speed", "VRN_AutoTestLoop.py")
        names = [f"r{i:03d}.pdf" for i in range(106)]
        pick = loop.def_g08_pick(list(reversed(names)), 12, False)
        self.assertEqual(len(pick), 12)
        self.assertEqual(len(set(pick)), 12)
        self.assertEqual(pick, loop.def_g08_pick(names, 12, False))
        self.assertEqual(pick[0], "r000.pdf")
        self.assertEqual(pick[-1], "r105.pdf", "the newest report (names start with the date) is always re-ingested")
        idx = [names.index(p) for p in pick]
        gaps = {b - a for a, b in zip(idx, idx[1:])}
        self.assertLessEqual(max(gaps) - min(gaps), 1, gaps)
        self.assertEqual(loop.def_g08_pick(names, 1, False), ["r105.pdf"])
        self.assertEqual(loop.def_g08_pick(names, 12, True), names)
        self.assertEqual(loop.def_g08_pick(names[:5], 12, False), names[:5])
        for n in range(13, 40):
            self.assertEqual(len(set(loop.def_g08_pick(names[:n], 12, False))), 12, n)


class SelfTestSplitTest(unittest.TestCase):
    """The loop's self-test runs VRN/tests side by side: every test in exactly one unit, costliest first, and a unit
    that fails or dies is reported, never dropped."""

    @classmethod
    def setUpClass(cls):
        cls.loop = def_load("vrn_autotest_loop_batch_speed", "VRN_AutoTestLoop.py")
        cls.tmp = tempfile.TemporaryDirectory()
        d = Path(cls.tmp.name)
        body = "import unittest\n\nclass Base(unittest.TestCase):\n    pass\n\n"
        for c, n in (("A", 2), ("B", 1), ("C", 3)):
            body += f"class {c}(Base):\n" + "".join(f"    def test_{c}{i}(self):\n        pass\n\n" for i in range(n))
        (d / "test_heavy.py").write_text("SELFTEST_SECONDS = 30\n" + body, encoding="utf-8")
        (d / "test_light.py").write_text("import unittest\n\nclass L(unittest.TestCase):\n    def test_one(self):\n"
                                         "        pass\n", encoding="utf-8")
        (d / "test_broken.py").write_text("import unittest\n\nclass X(unittest.TestCase):\n    def test_bad(self):\n"
                                          "        self.assertEqual(1, 2)\n", encoding="utf-8")
        cls.dir = d

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def run_unit(self, spec):
        import contextlib
        import io
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            self.loop.def_unit_file(spec)
        line = [x for x in buf.getvalue().splitlines() if x.startswith(self.loop.UNIT_MARK)][-1]
        return json.loads(line[len(self.loop.UNIT_MARK):])

    def test_every_test_runs_in_exactly_one_part(self):
        heavy = str(self.dir / "test_heavy.py")
        whole = self.run_unit(heavy)["run"]
        parts = [self.run_unit(f"{heavy}::{k}/3")["run"] for k in range(3)]
        self.assertEqual(whole, 6)
        self.assertEqual(sum(parts), whole)
        self.assertEqual(sorted(parts), [1, 2, 3], "one class per part: the classes are dealt out, not the tests")

    def test_the_costliest_units_come_first(self):
        specs = self.loop.def_unit_specs(self.dir, 3)
        self.assertEqual([Path(s.partition("::")[0]).name for s in specs[:3]], ["test_heavy.py"] * 3)
        self.assertEqual(len([s for s in specs if "test_heavy.py" in s]), 3)     # four classes, three workers
        one = self.loop.def_unit_specs(self.dir, 1)
        self.assertEqual(len(one), 3)
        self.assertFalse([s for s in one if "::" in s], "one worker: whole files only")
        self.assertTrue(one[0].endswith("test_heavy.py"))

    def test_a_failing_or_dead_unit_is_reported(self):
        got = self.loop.def_unit_child(str(self.dir / "test_broken.py"))
        self.assertEqual(got["run"], 1)
        self.assertEqual(len(got["bad"]), 1)
        gone = self.loop.def_unit_child(str(self.dir / "test_missing.py::0/2"))
        self.assertTrue(gone["bad"] or gone["run"] == 0)


if __name__ == "__main__":
    unittest.main()
