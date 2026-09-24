#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF 修正循環 · 誠實態單元測試 v0100(側線 2026-09-21 c;stdlib unittest;零網路;只落暫存)。

操作員令「檢視 VDF 現況 · 測試修正各引擎 · 全景式分析 · 識別錯誤 · 避免傷害引擎 · 避免九頭龍 · TEST DEBUG TILL IT WORKS」。
全格子 289 站容器實跑 FAIL 82,其中大半只有一個根因:第三方套件不在本境,而每支引擎各自把它寫成 FAIL。修在尺上,不修在 60 支引擎上:
  T01 格子 v0439 分類器:ModuleNotFoundError 的第三方套件 → 境缺(SKIP);自家模組名 → 不算(那是壞掉)
  T02 鏈跑器 v0102:假引擎 import 不存在的套件 → ABSENT 且具名;假引擎普通炸 → RED(負控)
  T03 四支引擎新版的 rc 語意(容器沒有 duckdb/pyarrow/庫):ENG081/ENG079/ENG045 → rc3 ABSENT;ENG058 → rc2 NODATA;輸出帶三把尺都認的字樣
  T04 頁接規格(批672):ENG076/ENG078 render() 只有一份 <style>、頁尾署名 CGC_MDL173、舊 CSS 不在、自測 ⑦ 要的字樣都在
  T05 匯流排 v0130 ㉟:本境無 duckdb → [ABSENT] 不進分母,計數行以 done 數為準
  T06 對接口 v0102:LL133 自家族不進版史分母(_SELF_FAMILY);CGC_MDL164 selfref 對本口判 SAFE

跑法:python "supportive modules/registry/tests/test_vdf_honest_states_v0100.py"(格子站同一句;py3.11 與 3.12 同過)
"""
from __future__ import annotations
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

import contextlib
import importlib.util
import io
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
REG = Path(__file__).resolve().parent.parent
VIA = REG.parent.parent
ENG = VIA / "functional modules" / "VDF" / "engine"
PY = sys.executable
_MODS: dict = {}


def newest(folder: Path, pat: str) -> Path | None:
    hits = sorted(x for x in folder.glob(pat) if "__pycache__" not in x.parts)
    return hits[-1] if hits else None


def load(name: str, path: Path):
    if name in _MODS:
        return _MODS[name]
    sp = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(sp)
    sys.modules[name] = m
    with contextlib.redirect_stdout(io.StringIO()):
        sp.loader.exec_module(m)
    _MODS[name] = m
    return m


def run(argv, timeout=600, env=None):
    e = dict(os.environ); e["PYTHONDONTWRITEBYTECODE"] = "1"; e.update(env or {})
    return subprocess.run([PY, *[str(x) for x in argv]], capture_output=True, text=True, timeout=timeout, env=e, cwd=str(VIA))


def has_mod(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


class T01_GridClassifier(unittest.TestCase):
    def test_01_third_party_vs_local(self):
        g = load("ut_grid", newest(REG, "CGC_MDL064_SelftestGrid_v????.py"))
        self.assertTrue(callable(getattr(g, "_missing_third_party", None)), "格子沒有境缺分類器")
        self.assertEqual(g._missing_third_party("x\nModuleNotFoundError: No module named 'duckdb'\nModuleNotFoundError: No module named 'pandas.core'\n"), ["duckdb", "pandas"])
        self.assertEqual(g._missing_third_party("ModuleNotFoundError: No module named 'via_params_central_v0108'"), [])
        self.assertEqual(g._missing_third_party(""), [])

    def test_02_run_one_skips_env_absent(self):
        g = load("ut_grid", newest(REG, "CGC_MDL064_SelftestGrid_v????.py"))
        with tempfile.TemporaryDirectory() as td:
            miss = Path(td) / "fake_missing.py"; miss.write_text("import zz_pkg_not_installed_9z\n", encoding="utf-8")
            rc3 = Path(td) / "fake_absent.py"; rc3.write_text("print('[ABSENT] x');raise SystemExit(3)\n", encoding="utf-8")
            bad = Path(td) / "fake_bad.py"; bad.write_text("raise SystemExit(1)\n", encoding="utf-8")
            r1 = g.run_one({"name": "缺件", "path": str(miss), "args": [], "expect": "rc0", "timeout": 60})
            r2 = g.run_one({"name": "自報缺", "path": str(rc3), "args": [], "expect": "rc0", "timeout": 60})
            r3 = g.run_one({"name": "壞掉", "path": str(bad), "args": [], "expect": "rc0", "timeout": 60})
        self.assertEqual(r1["state"], "SKIP"); self.assertIn("zz_pkg_not_installed_9z", r1["note"]); self.assertIn("環境缺件", r1["note"])
        self.assertEqual(r2["state"], "SKIP"); self.assertIn("rc=3", r2["note"])
        self.assertEqual(r3["state"], "FAIL")


class T02_ChainRunner(unittest.TestCase):
    def test_01_named_absent_and_red_control(self):
        m = load("ut_mdl170", newest(REG, "CGC_MDL170_VDFChainRunner_v????.py"))
        self.assertTrue(callable(getattr(m, "_missing_pkgs", None)))
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            (d / "VDF_ENG998_FakeMissing_v0100.py").write_text("import zz_pkg_not_installed_9z\n", encoding="utf-8")
            (d / "VDF_ENG997_FakeBroken_v0100.py").write_text("raise SystemExit(1)\n", encoding="utf-8")
            saved = m.VDF_ENG; m.VDF_ENG = d
            try:
                a = m.run_one("9a", "缺件", "VDF_ENG998_FakeMissing_v*.py", [], 60, "rc0", "x", m.DEFAULT_SINCE)
                b = m.run_one("9b", "壞掉", "VDF_ENG997_FakeBroken_v*.py", [], 60, "rc0", "x", m.DEFAULT_SINCE)
            finally:
                m.VDF_ENG = saved
        self.assertEqual(a["state"], "ABSENT"); self.assertIn("zz_pkg_not_installed_9z", a["detail"]); self.assertIn("via_vdf_312", a["fix"])
        self.assertEqual(b["state"], "RED")


class T03_EngineRcSemantics(unittest.TestCase):
    """容器沒有 duckdb/pyarrow/庫 → 引擎要說 ABSENT/NODATA(rc3/rc2),不是 FAIL(rc1)。有套件的機器上這些檢照舊真跑(本檔只驗缺件那條路)。"""

    def _sel(self, pat):
        p = newest(ENG, pat); self.assertIsNotNone(p, pat)
        return p, run([p, "--selftest"])

    @unittest.skipIf(has_mod("duckdb"), "本境有 duckdb:缺件路徑不可測(工作站走真跑)")
    def test_01_eng081_eng079_absent_rc3(self):
        for pat in ("VDF_ENG081_UniverseAlign_v????.py", "VDF_ENG079_LocalDbConsolidate_v????.py"):
            p, r = self._sel(pat)
            self.assertEqual(r.returncode, 3, f"{p.name}: rc={r.returncode}\n{r.stdout[-400:]}")
            self.assertIn("[ABSENT]", r.stdout); self.assertIn("ModuleNotFoundError: No module named 'duckdb'", r.stdout); self.assertNotIn("[FAIL]", r.stdout)

    def test_02_eng058_nodata_rc2_when_db_missing(self):
        p = newest(ENG, "VDF_ENG058_IndustryUnifiedMap_v????.py")
        m = load("ut_eng058", p)
        if Path(m.DB_TW).exists():
            self.skipTest("本境有產業庫:缺料路徑不可測")
        r = run([p, "--selftest"])
        self.assertEqual(r.returncode, 2, r.stdout[-400:]); self.assertIn("[NODATA]", r.stdout); self.assertNotIn("[FAIL]", r.stdout)

    @unittest.skipIf(has_mod("duckdb") and has_mod("pyarrow"), "本境套件齊:缺件路徑不可測")
    def test_03_eng045_absent_not_in_denominator(self):
        p = newest(VIA / "functional modules" / "VDF", "VDF_ENG045_OutputHub_v????.py")
        r = run([p, "--selftest"])
        self.assertEqual(r.returncode, 3, r.stdout[-500:])
        self.assertIn("[ABSENT]", r.stdout); self.assertNotIn("[FAIL]", r.stdout)
        tally = [ln for ln in r.stdout.splitlines() if ln.strip().startswith("[計]") and "檢通過" in ln][-1]
        self.assertIn("ABSENT", tally)
        a, b = tally.split("[計]")[1].strip().split(" ")[0].split("/")
        self.assertEqual(a, b, tally)


class T04_PagesOnSpec(unittest.TestCase):
    def test_01_eng076_render_spec_only(self):
        m = load("ut_eng076", newest(ENG, "VDF_ENG076_ETFRevenueMomentum_v????.py"))
        self.assertIn("CGC_MDL173", Path(m.__file__).read_text(encoding="utf-8"))
        res = {"asof_ym": "2026-08", "n_months": 36, "holdings": [1, 2], "note": "合成",
               "etfs": [{"rank": 1, "etf_ticker": "00981A", "etf_name": "測試", "n_holdings": 30, "cov_w": 88.5, "w_yoy": 12.3, "med_yoy": 9.1, "pos_share_w": 70.0, "w_mom": 1.2, "high60_share_w": 40.0, "top": [{"code": "2330", "yoy": 25.0}], "flag": ""},
                        {"rank": 2, "etf_ticker": "00982A", "etf_name": None, "n_holdings": 20, "cov_w": None, "w_yoy": None, "med_yoy": None, "pos_share_w": None, "w_mom": None, "high60_share_w": None, "top": [], "flag": "LOW_COVERAGE"}],
               "overlap": [{"code": "2330", "name": "台積電", "n_etf": 2, "w_sum": 12.5, "yoy": 25.0, "streak": 3, "high60": True}]}
        h = m.render(res)
        self.assertEqual(h.count("<style>"), 1); self.assertIn("排版規格 CGC_MDL173", h); self.assertNotIn("--card:#1e293b", h)
        for tok in ("@media", "VIA_UI_ProjectCompletion_v0100.html", "史深", "LOW_COVERAGE", "<table class='m'>", "<div class='kpi'>"):
            self.assertIn(tok, h, tok)
        self.assertNotIn('src="http', h); self.assertNotIn("src='http", h)

    def test_02_eng078_render_spec_only(self):
        m = load("ut_eng078", newest(ENG, "VDF_ENG078_ActiveETFHoldingsHistory_v????.py"))
        self.assertIn("CGC_MDL173", Path(m.__file__).read_text(encoding="utf-8"))
        cov = {"today": "2026-09-21", "etfs": [{"ticker": "00981A", "name": "測試", "issuer": "統一", "listing": "2025-05-06", "listing_src": "twse", "first_snapshot": "2025-05-07", "last_snapshot": "2026-09-19", "have_days": 300, "expected_days": 340, "coverage_pct": 88.2, "state": "PARTIAL", "today_ok": False, "missing_head": ["2026-09-20"]}]}
        lanes = {"lanes": [{"id": "MONEYDJ", "kind": "latest", "state": "VERIFIED", "url": "https://x", "note": "最新日"}]}
        h = m.render(cov, lanes, {"state": "OK", "tried": 1, "filled": 0, "no_source": 1, "verified_dated_lanes": 0})
        self.assertEqual(h.count("<style>"), 1); self.assertIn("排版規格 CGC_MDL173", h); self.assertNotIn("--card:#1e293b", h)
        for tok in ("@media", "LANES", "COVERAGE", "s-YELLOW", "VIA_UI_ProjectCompletion_v0100.html"):
            self.assertIn(tok, h, tok)
        self.assertNotIn('src="http', h)


class T05_BusHygieneHonest(unittest.TestCase):
    @unittest.skipIf(has_mod("duckdb"), "本境有 duckdb:㉟ 真跑,缺件路徑不可測")
    def test_01_absent_not_fail(self):
        p = newest(REG, "CGC_MDL148_EngineBus_v????.py")
        r = run([p, "--selftest"], timeout=900)
        self.assertEqual(r.returncode, 0, r.stdout[-600:])
        self.assertIn("[ABSENT] ㉟", r.stdout); self.assertNotIn("[FAIL] ㉟", r.stdout)
        tally = [ln for ln in r.stdout.splitlines() if ln.strip().startswith("[計]")][-1]
        self.assertIn("FAIL 0", tally)


class T06_DoorSelfFamily(unittest.TestCase):
    def test_01_self_family_excluded_and_audit_safe(self):
        door = newest(VIA / "functional modules" / "VDF", "VDF_SystemManager_v????.py")
        src = door.read_text(encoding="utf-8")
        self.assertIn("_SELF_FAMILY", src)
        d = load("ut_door", door)
        br = d.read_bridge()
        hist_py = br["history"]["py"]
        n_self = sum(1 for q in (VIA / "functional modules" / "VDF").rglob("VDF_SystemManager_v????.py"))
        self.assertGreater(n_self, 0)
        total = sum(1 for q in (VIA / "functional modules" / "VDF").rglob("*.py") if "references" not in q.parts and "__pycache__" not in q.parts)
        self.assertEqual(hist_py, total - n_self)
        a = load("ut_mdl164", newest(REG, "CGC_MDL164_*_v????.py"))
        sr = a.selfref()
        mine = [r for r in sr["rows"] if r["family"] == "VDF_SystemManager"]
        self.assertTrue(mine and mine[0]["state"] == "SAFE", mine)
        self.assertFalse([r for r in sr["new_offenders"] if r["family"] == "VDF_SystemManager"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
