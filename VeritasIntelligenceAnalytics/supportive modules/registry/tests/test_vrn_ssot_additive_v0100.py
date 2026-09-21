#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN SSOT 增補審計 單元測試 v0100(側線 2026-09-21;stdlib unittest;零網路;只落暫存)。

操作員令「整合優化 UNITTEST FOR ALL」——五件上傳裡唯一的新料是 VIA_SSOT_Additive_Audit_v0100 審計包。
本檔把「收容 × 樞紐 v0111 × 正主橋 ENG088 × 包內自帶測試」四層一次測完,而且每一層都對回**證據**:
  T01 收容:manifest 逐件 sha256/bytes 現場對;重複件的活樹側 md5 現場重算;baseline 副本只差檔尾換行
  T02 樞紐:增補讀冊口四態、只增不減實證、多義只攤開、候選 PENDING_OPERATOR、源碼衛生、--selftest rc0
  T03 包內測試:暫存副本實跑 30+48 檢;收容夾 sha 前後相同
  T04 落差:九型代表碼兩把尺同答;K/C/M/S/V 不在正典;上漲空間兩套口徑都留
  T05 橋:--selftest rc0、落檔只有一個出口、status --json、tests --no-report 零觸碰

跨機器敏感點(L93):只對收容夾(.gitattributes `-text`,位元跨機器不變)算 sha;
.py 源碼只做子字串檢查(CRLF 無影響);子行程用本行程 python(格子跑就是家族境)。

跑法:python "supportive modules/registry/tests/test_vrn_ssot_additive_v0100.py"   (格子站同一句)
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
import warnings
from pathlib import Path

sys.dont_write_bytecode = True
REG = Path(__file__).resolve().parent.parent
VIA = REG.parent.parent
ROOT = VIA.parent
PY = sys.executable


def newest(folder: Path, pat: str) -> Path | None:
    hits = sorted(x for x in folder.glob(pat) if "__pycache__" not in x.parts)
    return hits[-1] if hits else None


INTAKE = newest(VIA / "functional modules/VRN/references/intake", "VIA_SSOT_Additive_Audit_v*")
HUB = newest(VIA / "supportive modules/70_VRN_Rules", "SUP_MDL749_VRNFieldRuleHub_v*.py")
BRIDGE = newest(VIA / "functional modules/VRN", "VRN_ENG088_SsotAdditiveBridge_v*.py")


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def md5(p: Path) -> str:
    return hashlib.md5(p.read_bytes()).hexdigest()


def tree_sha(d: Path) -> str:
    h = hashlib.sha256()
    for p in sorted(x for x in d.rglob("*") if x.is_file() and "__pycache__" not in x.parts):
        h.update(p.relative_to(d).as_posix().encode("utf-8")); h.update(b"\0"); h.update(p.read_bytes()); h.update(b"\0")
    return h.hexdigest()


def env() -> dict:
    e = dict(os.environ)
    e.update({"VIA_NET_DISABLED": "1", "VIA_SELFTEST": "1", "PYTHONDONTWRITEBYTECODE": "1",
              "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"})
    return e


def run(args: list, cwd: Path, timeout: int = 900) -> subprocess.CompletedProcess:
    return subprocess.run([PY, *args], capture_output=True, text=True, timeout=timeout, cwd=str(cwd),
                          env=env(), stdin=subprocess.DEVNULL, encoding="utf-8", errors="replace")


class T01_Intake(unittest.TestCase):
    """收容件零觸碰有證據:manifest 逐件對、重複件現場重算。"""

    @classmethod
    def setUpClass(cls):
        assert INTAKE is not None, "收容夾 VIA_SSOT_Additive_Audit_v* 不在"
        mans = sorted(INTAKE.glob("_INTAKE_MANIFEST_*.json"))
        assert mans, "manifest 不在"
        cls.man_path = mans[-1]
        cls.man = json.loads(cls.man_path.read_text(encoding="utf-8"))

    def test_01_manifest_matches_bytes(self):
        self.assertEqual(self.man.get("schema"), "VIA.IntakeManifest.v1")
        files = self.man["files"]
        self.assertGreaterEqual(len(files), 30)
        for f in files:
            p = INTAKE / f["name"]
            self.assertTrue(p.is_file(), f["name"])
            self.assertEqual(p.stat().st_size, f["bytes"], f["name"])
            self.assertEqual(sha256(p), f["sha256"], f["name"])
            self.assertEqual(md5(p), f["md5"], f["name"])
        on_disk = sorted(x.relative_to(INTAKE).as_posix() for x in INTAKE.rglob("*")
                         if x.is_file() and x.name != self.man_path.name and "__pycache__" not in x.parts)
        self.assertEqual(on_disk, sorted(f["name"] for f in files), "夾內有冊外的檔或少了冊上的檔")

    def test_02_duplicates_recomputed_on_live_side(self):
        dups = self.man["duplicates_not_reintaken"]
        self.assertEqual(len(dups), 2)
        for d in dups:
            live = VIA / d["live_copy"]
            self.assertTrue(live.is_file(), d["live_copy"])
            self.assertEqual(md5(live), d["live_md5"], "活樹側 md5 與收容時記的不同(活樹收容件被動了?)")
            self.assertTrue(d["identical"])
            self.assertEqual(d["live_md5"], d["upload_md5"], "上傳件與活樹收容件不相同,不該標 duplicate")
        prov = {u["upload_name"]: u for u in self.man["uploads_provenance"]}
        self.assertEqual(prov["VIA_CNYES_FactSet_YFinance_Consensus_Fusion_Engine_v0120_2.py"]["md5"], dups[0]["live_md5"])
        self.assertEqual(prov["SYNONYM_LIBRARY_2.json"]["md5"], md5(INTAKE / "SYNONYM_LIBRARY.json"))
        self.assertEqual(prov["VRN_WORKFLOW_SPEC.md"]["md5"], md5(INTAKE / "VRN_WORKFLOW_SPEC.md"))
        self.assertEqual(prov["VIA_SSOT_Additive_Audit_v0100.zip"]["disposition"], "INTAKEN_HERE")

    def test_03_baseline_copies_differ_only_by_newline(self):
        rows = self.man["baseline_vs_tree"]["rows"]
        self.assertGreaterEqual(len(rows), 8)
        self.assertEqual({r["verdict"] for r in rows} - {"IDENTICAL", "TRAILING_NEWLINE_ONLY", "EOL_ONLY", "NOT_IN_PACKAGE"}, set(),
                         "baseline 副本與活樹有內容差(CONTENT_DIFF):包的 baseline_bytes_unchanged 證不了活樹")
        for r in rows:
            if r["verdict"] != "NOT_IN_PACKAGE":
                self.assertEqual(r["blob_claimed"], r["blob_at_8e8e766f"], r["repository_path"])

    def test_04_intake_is_byte_locked_in_gitattributes(self):
        ga = (ROOT / ".gitattributes").read_text(encoding="utf-8")
        self.assertIn("references/intake/** -text", ga)


class T02_Hub(unittest.TestCase):
    """樞紐 v0111 增補讀冊口。"""

    @classmethod
    def setUpClass(cls):
        assert HUB is not None
        cls.hub = load(HUB, "_hub_under_test")
        assert hasattr(cls.hub, "resolve_synonym"), f"{HUB.name} 沒有增補讀冊口(要 v0111+)"
        cls.lib = cls.hub.additive_library()

    def test_05_library_ok_and_scopes(self):
        self.assertEqual(self.lib["state"], "OK", self.lib["why"])
        sc = self.hub.additive_scopes(self.lib["lib"])
        self.assertTrue({"broker", "rating", "target_price", "scenario", "rating_label", "valuation_method", "financial_concept"} <= set(sc))
        self.assertGreaterEqual(sum(sc.values()), 400)

    def test_06_resolve_four_states_and_rc_table(self):
        r = self.hub.resolve_synonym("Accumulate", "rating")
        self.assertEqual((r["status"], r["candidates"], r["canonical"]), ("SOURCE_REQUIRED", ["ADD", "BUY"], None))
        self.assertEqual(self.hub.resolve_synonym("Accumulate", "rating", source="field_rules.rating.canon_map")["canonical"], "ADD")
        self.assertEqual(self.hub.resolve_synonym("目標價", "target_price")["canonical"], "TARGET_PRICE")
        self.assertEqual(self.hub.resolve_synonym("ＴＡＲＧＥＴ  price", "target_price")["status"], "RESOLVED")
        self.assertEqual(self.hub.resolve_synonym("沒有這個詞xyz", "rating")["status"], "UNKNOWN")
        self.assertEqual(self.hub.resolve_synonym("目標價", "no_such_scope")["status"], "UNKNOWN")
        self.assertEqual(self.hub.ADDITIVE_RC, {"RESOLVED": 0, "SOURCE_REQUIRED": 1, "UNKNOWN": 2, "ABSENT": 3})

    def test_07_only_add_invariant(self):
        mine = {self.hub._norm_additive(a): ks for a, ks in self.hub._canon_of_alias().items()}
        self.assertGreaterEqual(len(mine), 30)
        for a, ks in mine.items():
            r = self.hub.resolve_synonym(a, "rating", lib=self.lib["lib"])
            self.assertNotEqual(r["status"], "UNKNOWN", f"樞紐別名 {a!r} 在增補冊上不見了(減了)")
            self.assertTrue(ks & set(r["candidates"]), f"樞紐別名 {a!r} 的正典 {ks} 不在候選 {r['candidates']}(既有對應被改)")
        for w in self.hub.rating_words():
            self.assertNotEqual(self.hub.resolve_synonym(w, "rating", lib=self.lib["lib"])["status"], "UNKNOWN", w)

    def test_08_conflicts_laid_out_not_ruled(self):
        before = json.dumps(self.lib["lib"], sort_keys=True, ensure_ascii=False)
        cf = self.hub.additive_conflicts(self.lib["lib"])
        self.assertEqual(json.dumps(self.lib["lib"], sort_keys=True, ensure_ascii=False), before, "讀冊改了冊")
        self.assertEqual(cf["state"], "YELLOW")
        self.assertEqual(cf["n"], 10)
        self.assertEqual(cf["hub_intake_conflicts"], ["Accumulate", "Add"])
        aliases = {r["alias"] for r in cf["rows"]}
        self.assertTrue({"accumulate", "add", "strong buy", "strong sell"} <= aliases)
        for r in cf["rows"]:
            self.assertGreaterEqual(len(r["canons"]), 2)
            for c in r["canons"]:
                self.assertTrue(r["by_source"][c], f"{r['alias']} → {c} 沒帶來源")
        self.assertEqual(len(cf["vs_hub"]), 4)

    def test_09_candidates_pending_operator(self):
        c = self.hub.additive_candidates(lib=self.lib["lib"], path=self.lib["path"])
        self.assertEqual(c["state"], "OK")
        self.assertGreaterEqual(len(c["candidates"]), 34)
        self.assertTrue(all(x["disposition"] == "PENDING_OPERATOR" for x in c["candidates"]))
        self.assertEqual(c["mode"], "REVIEWABLE_CANDIDATE_NOT_INSTALLED")
        self.assertIs(c["runtime_enabled"], False)

    def test_10_source_hygiene(self):
        src = HUB.read_text(encoding="utf-8")
        head = src.split("\ndef selftest()")[0]
        for k in ("import requests", "import httpx", "import urllib"):
            self.assertNotIn(k, head)
        self.assertNotIn(".write_text(", head, "樞紐主體不落檔")
        self.assertIn('"additive"', head)
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            compile(src, str(HUB), "exec")

    def test_11_hub_selftest_rc0(self):
        r = run([str(HUB), "--selftest"], HUB.parent)
        self.assertEqual(r.returncode, 0, (r.stdout + r.stderr)[-1500:])
        m = re.search(r"\[計\] (\d+) 檢 OK (\d+) · FAIL (\d+)", r.stdout)
        self.assertIsNotNone(m, r.stdout[-600:])
        self.assertGreaterEqual(int(m.group(1)), 48)
        self.assertEqual(m.group(3), "0")


class T03_PackageTests(unittest.TestCase):
    """包內自帶測試在暫存副本實跑;收容夾位元不動。"""

    def test_12_package_tests_pass_in_temp_copy(self):
        before = tree_sha(INTAKE)
        with tempfile.TemporaryDirectory(prefix="via_t03_") as td:
            work = Path(td) / INTAKE.name
            shutil.copytree(INTAKE, work, ignore=shutil.ignore_patterns("__pycache__"))
            r1 = run([str(work / "audit_ssot.py")], work)
            self.assertEqual(r1.returncode, 0, (r1.stdout + r1.stderr)[-1500:])
            au = json.loads((work / "AUDIT_SUMMARY.json").read_text(encoding="utf-8"))["qa"]
            self.assertTrue(au["all_passed"])
            self.assertEqual(au["passed"], au["total"])
            self.assertGreaterEqual(au["total"], 30)
            r2 = run([str(work / "test_vrn_evidence.py")], work)
            self.assertEqual(r2.returncode, 0, (r2.stdout + r2.stderr)[-1500:])
            qa = json.loads((work / "VRN_WORKFLOW_QA.json").read_text(encoding="utf-8"))
            q = qa.get("qa") if isinstance(qa.get("qa"), dict) else qa
            if "passed" in q and "total" in q:
                self.assertEqual(q["passed"], q["total"])
                self.assertGreaterEqual(q["total"], 48)
            else:
                ch = q.get("checks") or {}
                self.assertGreaterEqual(len(ch), 48)
                self.assertTrue(all(v is True for v in ch.values()), [k for k, v in ch.items() if v is not True])
        self.assertEqual(tree_sha(INTAKE), before, "收容夾被動了")


class T04_Drift(unittest.TestCase):
    """包內尺 vs 正典。"""

    @classmethod
    def setUpClass(cls):
        cls.hub = load(HUB, "_hub_for_drift")
        cls.rx = {k: v["pattern"] for k, v in json.loads((INTAKE / "ticker_schema.json").read_text(encoding="utf-8"))["$defs"].items()}
        cls.core = load(INTAKE / "VRN_Evidence_Core.py", "_core_under_test")

    def test_13_nine_types_agree_on_representatives(self):
        type2rx = {"一般個股": "TW_STOCK_REGEX", "被動股票ETF": "TW_PASSIVE_STOCK_ETF_REGEX", "主動股票ETF": "TW_ACTIVE_STOCK_ETF_REGEX",
                   "被動債券ETF": "TW_PASSIVE_BOND_ETF_REGEX", "主動債券ETF": "TW_ACTIVE_BOND_ETF_REGEX", "槓桿型ETF": "TW_LEVERAGED_ETF_REGEX",
                   "反向型ETF": "TW_INVERSE_ETF_REGEX", "期貨型ETF": "TW_FUTURES_ETF_REGEX", "平衡型ETF": "TW_BALANCED_ETF_REGEX"}
        probes = {"2330": "一般個股", "0050": "被動股票ETF", "006208": "被動股票ETF", "00878": "被動股票ETF", "00981A": "主動股票ETF",
                  "00679B": "被動債券ETF", "00987D": "主動債券ETF", "00631L": "槓桿型ETF", "00632R": "反向型ETF",
                  "00635U": "期貨型ETF", "00713T": "平衡型ETF"}
        for code, want in probes.items():
            self.assertEqual(self.hub.ticker_kind(code)[0], want, code)
            hit = [t for t, n in type2rx.items() if re.fullmatch(self.rx[n], code)]
            self.assertEqual(hit, [want], code)

    def test_14_extra_types_absent_from_canon(self):
        canon = [t for t, _ in self.hub.ticker_rules()["corrected"]["types_ordered"]]
        self.assertEqual(len(canon), 9)
        for s in "KCMS":
            self.assertEqual(self.hub.ticker_kind(f"00999{s}")[0], "UNCLASSIFIED", s)
            self.assertTrue(any(re.fullmatch(self.rx[n], f"00999{s}") for n in self.rx if "FOREIGN_CURRENCY" in n), s)
        self.assertEqual(self.hub.ticker_kind("00999V")[0], "期貨型ETF")
        self.assertTrue(re.fullmatch(self.rx["TW_FOREIGN_CURRENCY_FUTURES_ETF_REGEX"], "00999V"))
        self.assertFalse(re.fullmatch(self.rx["TW_FUTURES_ETF_REGEX"], "00999V"))

    def test_15_upside_policy_divergence_recorded_not_merged(self):
        tgt = {"value": "100", "currency": "TWD", "share_basis": "PER_SHARE", "adjustment_basis": "RAW"}
        px = {"value": "80", "currency": "TWD", "share_basis": "PER_SHARE", "adjustment_basis": "ADJ",
              "price_type": "ADJUSTED_CLOSE", "as_of": "2026-09-18"}
        self.assertEqual(self.core.compute_upside(tgt, px)["status"], "BASIS_MISMATCH")
        ok = self.core.compute_upside({**tgt, "adjustment_basis": "ADJ"}, px)
        self.assertEqual(ok["status"], "CALCULATED")
        self.assertAlmostEqual(ok["upside_pct"], 25.0, places=6)
        laws = json.loads((VIA / "supportive modules/registry/VIA_Policy_Laws_SSOT_v0100.json").read_text(encoding="utf-8"))
        txt = json.dumps(laws, ensure_ascii=False)
        self.assertIn('"id": "L99"', txt)
        self.assertIn("ADJ CLOSE", txt)


class T05_Bridge(unittest.TestCase):
    """正主橋 ENG088。"""

    @classmethod
    def setUpClass(cls):
        assert BRIDGE is not None, "VRN_ENG088_SsotAdditiveBridge_v*.py 不在"

    def test_16_bridge_selftest_rc0(self):
        r = run([str(BRIDGE), "--selftest"], BRIDGE.parent)
        self.assertEqual(r.returncode, 0, (r.stdout + r.stderr)[-2000:])
        m = re.search(r"\[計\] (\d+) 檢 OK (\d+) · FAIL (\d+)", r.stdout)
        self.assertIsNotNone(m)
        self.assertGreaterEqual(int(m.group(1)), 19)
        self.assertEqual(m.group(3), "0")

    def test_17_bridge_write_paths_single_exit(self):
        src = BRIDGE.read_text(encoding="utf-8")
        code = src.split("\ndef selftest", 1)[0]
        self.assertNotIn('"--apply"', code)
        for k in ("import requests", "import httpx", "import urllib"):
            self.assertNotIn(k, code)
        ws = [m.start() for m in re.finditer(r"\.write_text\(|open\([^)]*[\"']w", code)]
        a, b = code.index("def _write("), code.index("def _out_dir(")
        self.assertTrue(ws and all(a < i < b for i in ws), "寫檔呼叫出現在 _write 之外")
        self.assertIn("sys.dont_write_bytecode = True", code)
        self.assertIn("[VIA:ACCEL-BRIDGE", src)
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            compile(src, str(BRIDGE), "exec")

    def test_18_bridge_status_json(self):
        r = run([str(BRIDGE), "status", "--json"], BRIDGE.parent)
        self.assertEqual(r.returncode, 0, r.stderr[-800:])
        s = json.loads(r.stdout)
        self.assertEqual(s["state"], "OK")
        self.assertEqual(s["package"]["state"], "OK")
        self.assertEqual(s["library"]["state"], "OK")
        self.assertGreaterEqual(sum(s["scopes"].values()), 400)

    def test_19_bridge_tests_verb_zero_touch(self):
        before = tree_sha(INTAKE)
        r = run([str(BRIDGE), "tests", "--no-report", "--json"], BRIDGE.parent)
        self.assertEqual(r.returncode, 0, (r.stdout + r.stderr)[-1500:])
        t = json.loads(r.stdout)
        self.assertEqual(t["state"], "GREEN")
        self.assertIs(t["zero_touch"], True)
        self.assertEqual([x["state"] for x in t["rows"]], ["GREEN", "GREEN"])
        self.assertEqual(tree_sha(INTAKE), before)
        self.assertFalse(any(x.name == "__pycache__" for x in INTAKE.rglob("*")), "收容夾長出 __pycache__")

    def test_20_bridge_drift_rows_carry_next_step(self):
        r = run([str(BRIDGE), "drift", "--no-report", "--json"], BRIDGE.parent)
        self.assertEqual(r.returncode, 0, (r.stdout + r.stderr)[-1500:])
        d = json.loads(r.stdout)
        self.assertIn(d["state"], ("GREEN", "YELLOW"))
        ids = [x["id"] for x in d["rows"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue({"TICKER_TYPES", "TICKER_EXTRA_TYPES", "UPSIDE_BASIS", "BROKER_PARTIAL", "DATE_PARSE", "RATING_POLYSEMY"} <= set(ids))
        for x in d["rows"]:
            self.assertIn(x["level"], ("GREEN", "YELLOW", "RED", "NODATA"))
            self.assertTrue(x["next"])
        by = {x["id"]: x for x in d["rows"]}
        self.assertEqual(by["TICKER_TYPES"]["level"], "GREEN")
        self.assertEqual(by["UPSIDE_BASIS"]["eg"]["pkg_mismatched_basis"], "BASIS_MISMATCH")


if __name__ == "__main__":
    unittest.main(verbosity=2)
