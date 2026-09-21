#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF 子系統管理對接口 單元測試 v0102(側線 2026-09-21;stdlib unittest;零網路;只落暫存)。
v0101→v0102(側線 2026-09-21 d;操作員令「擷取 VDF 的資料 · 完善到可啟動」):+T07 啟動就緒(對接口 v0103 launch)——
  合成負控(.ps1 少一步 → RED 點名;補上 → GREEN;裸 python → STALE)· 真 via_boot_update.sh↔.ps1 同鏈且 .ps1 含 Z94 那 13 步 + 家族境 python ·
  launch --no-probe --json 形狀與 rc 語意(L16 五態碼)· 同意閘前後同 · 下一步卡第一行對得上燈 · 格子第三站(launch --no-probe)· status/links 帶啟動段。
  T05 格子站 2 → 3(v0101 釘死「兩站」,第三站一上就紅——把暫態釘成不變量,同 ⑱ 那一課;改成集合等式)。其餘沿用 v0101。
v0100→v0101(側線 2026-09-21 c):T02 兩把尺對得上的尾版數改成**結構等式**(= 橋掃器沒排除的尾版數),不再釘 ≥40——還沒 commit 的新版尾版被橋掃器判 untracked 排除,釘死數字在那一刻就紅(把暫態釘成不變量,同 ⑱ 那一課)。

操作員令「建立 VDF_SystemManager 與 VIA 對接 · VDF 所有引擎找出來 · 讀取 VIA 政策所有 PY 檔案一定要接加速器 · 所有 VDF 都要加裝網路工具」。
本檔把「對接口本體 × VCGC 下行委派 × 橋律兩把尺 × 七處登記」一次測完,每一層都對回**證據**:
  T01 本體:--selftest rc0 且零污染(VIA_Reports/vdf_system 前後檔數相同);status --json 形狀(schema · 九盞燈 · rc 語意)
  T02 橋律:對接口的逐支判定與 CGC_MDL124.scan 同答(HAS↔True;兩把尺不許各說各話);對接口自己檔頭兩座橋都在(所有 VDF 都要加裝網路工具——本口也是 VDF 件)
  T03 VCGC:v0119 起 vdf_system() 經對接口讀(九盞燈 · 連結 · 七鍵);ENGINE_GLOBS 含 VDF 根;對接口是受治理家族;模擬缺席 → ABSENT 不炸不退回舊路
  T04 快照:sync 乾跑零寫 → --apply 落四件 → 再 sync 全 SAME
  T05 七處:規格項 · 格子兩站 · Deck 任務(argv 尾 status 且檔在)· Manager 兩名 · 中央冊 ACTIVE 號 · 交接文;Register 短令**只量不假設**(L70 候許可)
  T06 讀器:logic 分開報「無版號」(L04 外)· bridge 單支回三鍵 · tool 兩支正典在位且不判 RED · records 指標不複本 · 零網路 · 同意閘只讀

跑法:python "supportive modules/registry/tests/test_vdf_system_manager_v0100.py"   (格子站同一句;py3.11 與 3.12 同過)
"""
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
REG = Path(__file__).resolve().parent.parent
VIA = REG.parent.parent
VDF = VIA / "functional modules" / "VDF"
PY = sys.executable


def newest(folder: Path, pat: str) -> Path | None:
    hits = sorted(x for x in folder.glob(pat) if "__pycache__" not in x.parts)
    return hits[-1] if hits else None


DOOR = newest(VDF, "VDF_SystemManager_v*.py")
VCGC = newest(REG, "CGC_MDL149_VeritasCentralGovernanceConsole_v*.py")
SWEEPER = newest(REG, "CGC_MDL124_BridgeSweeper_v*.py")
_MODS: dict = {}


def load(name: str, path: Path):
    """惰性載入(載入期間印字吞掉);同名只載一次。"""
    if name in _MODS:
        return _MODS[name]
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    with contextlib.redirect_stdout(io.StringIO()):
        spec.loader.exec_module(m)
    _MODS[name] = m
    return m


def run(argv: list, env: dict | None = None, timeout: int = 900) -> subprocess.CompletedProcess:
    e = dict(os.environ)
    e.update(env or {})
    e["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run([PY, *[str(x) for x in argv]], capture_output=True, text=True, timeout=timeout, env=e, cwd=str(VIA))


def tail_json(text: str) -> dict:
    """status --json 先印人看的行再印 JSON:從第一個單獨的 `{` 行起解析。"""
    lines = text.splitlines()
    i = next(k for k, ln in enumerate(lines) if ln.strip() == "{")
    return json.loads("\n".join(lines[i:]))


def listing(p: Path) -> list:
    return sorted(x.name for x in p.glob("*")) if p.is_dir() else []


class T01_Door(unittest.TestCase):
    def test_01_files_present(self):
        self.assertIsNotNone(DOOR, "functional modules/VDF/VDF_SystemManager_v*.py 缺")
        self.assertIsNotNone(VCGC)
        self.assertIsNotNone(SWEEPER)
        self.assertRegex(DOOR.name, r"^VDF_SystemManager_v\d{4}\.py$")

    def test_02_selftest_rc0_zero_pollution(self):
        real = VIA / "VIA_Reports" / "vdf_system"
        before = listing(real)
        with tempfile.TemporaryDirectory(prefix="vdfsys_ut_") as td:
            r = run([DOOR, "--selftest"], {"VIA_VDFSYS_REPORTS": td, "VIA_SELFTEST": "1"})
        self.assertEqual(r.returncode, 0, r.stdout[-2500:] + r.stderr[-800:])
        self.assertIn("FAIL 0", r.stdout)
        self.assertNotIn("[FAIL]", r.stdout)
        self.assertEqual(listing(real), before, "自測污染了真快照夾")

    def test_03_status_json_shape(self):
        with tempfile.TemporaryDirectory(prefix="vdfsys_ut_") as td:
            r = run([DOOR, "status", "--json"], {"VIA_VDFSYS_REPORTS": td})
        self.assertIn(r.returncode, (0, 1, 2), r.stderr[-800:])
        j = tail_json(r.stdout)
        self.assertEqual(j.get("schema"), "VIA.VDF.SystemManager.v1")
        lamps = j.get("lamps") or {}
        self.assertEqual(set(lamps), {"policy", "logic", "factor", "param", "engine", "bridge", "tool", "handover", "records"})
        self.assertTrue(all(v in ("GREEN", "NODATA", "GATED", "ABSENT", "STALE", "RED") for v in lamps.values()), lamps)
        self.assertEqual(j.get("rc"), r.returncode)
        self.assertEqual(j.get("rc_name"), {0: "GREEN", 1: "RED", 2: "STALE/NODATA"}[j["rc"]])
        self.assertGreater(sum((j.get("link_counts") or {}).values()), 0)
        self.assertEqual(j.get("mode"), "subsystem")


class T02_BridgeLaw(unittest.TestCase):
    def test_01_two_rulers_agree(self):
        door = load("ut_vdfsys", DOOR)
        sw = load("ut_sweeper", SWEEPER)
        br = door.read_bridge()
        self.assertEqual(br["state"], "GREEN", br.get("why"))
        self.assertEqual(br["accel"]["missing"], [])
        self.assertEqual(br["net"]["callers_missing"], [])
        self.assertIn("CGC_MDL124", br["ruler"]["marks"])
        acc = {r["file"]: r["state"] for r in sw.scan("functional modules/VDF", "accel")}
        net = {r["file"]: r["state"] for r in sw.scan("functional modules/VDF", "net")}
        checked = 0
        for row in br["rows"]:
            f = row["tail"]
            if acc.get(f) in ("HAS", "MISSING"):
                self.assertEqual(row["accel"], acc[f] == "HAS", f)
                checked += 1
            if net.get(f) in ("HAS", "MISSING"):
                self.assertEqual(row["net"], net[f] == "HAS", f)
        comparable = sum(1 for row in br["rows"] if not row["excluded"] and acc.get(row["tail"]) in ("HAS", "MISSING"))
        self.assertEqual(checked, comparable, "兩把尺對得上的尾版數必須等於橋掃器沒排除的尾版數")
        self.assertGreaterEqual(checked, 30, "兩把尺對得上的尾版太少")

    def test_02_door_itself_carries_both_bridges(self):
        src = DOOR.read_text(encoding="utf-8")
        sw = load("ut_sweeper", SWEEPER)
        self.assertIn(sw.ACCEL_START, src)
        self.assertIn(sw.NET_START, src)
        self.assertIn(sw.NET_END, src)
        self.assertIn("def _via_net", src)
        self.assertEqual(src.count("[VIA:NET-BRIDGE:END]"), 1)


class T03_VcgcDelegation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.v = load("ut_vcgc", VCGC)

    def test_01_present(self):
        v = self.v
        self.assertTrue(callable(getattr(v, "_vdfsys", None)))
        self.assertTrue(callable(getattr(v, "vdf_system", None)))
        self.assertIn(("functional modules/VDF", "*_v????.py"), v.ENGINE_GLOBS)
        tails = v._tail_files()
        self.assertIn("VDF_SystemManager", tails)
        self.assertIn("VDF_ENG045_OutputHub", tails)
        vd = v.vdf_system()
        self.assertIsInstance(vd.get("lamps"), dict)
        self.assertEqual(len(vd["lamps"]), 9)
        self.assertGreater(vd.get("links") or 0, 0)
        self.assertEqual(len(vd.get("seven") or {}), 7)
        self.assertIsInstance((vd.get("bridge") or {}).get("tails"), int)
        self.assertGreaterEqual(vd["bridge"]["tails"], 40)

    def test_02_absent_is_absent_not_crash(self):
        v = self.v
        saved = dict(v._VDFSYS)
        v._VDFSYS["mod"], v._VDFSYS["why"] = None, "ut:模擬缺席"
        try:
            vd = v.vdf_system()
        finally:
            v._VDFSYS.clear()
            v._VDFSYS.update(saved)
        self.assertEqual(vd.get("state"), "ABSENT")
        self.assertIn("模擬缺席", vd.get("why", ""))

    def test_03_snapshot_and_onepage_carry_section(self):
        v = self.v
        src = VCGC.read_text(encoding="utf-8")
        self.assertIn('"vdf_system": vdf_system()', src)
        self.assertIn("## 十四 · VDF 子系統管理對接口", src)
        self.assertIn("二十六檢", src)
        self.assertNotIn("二十五檢 OK", src)


class T04_Snapshot(unittest.TestCase):
    def test_01_dry_apply_same(self):
        door = load("ut_vdfsys", DOOR)
        with tempfile.TemporaryDirectory(prefix="vdfsys_ut_") as td:
            old = os.environ.get("VIA_VDFSYS_REPORTS")
            os.environ["VIA_VDFSYS_REPORTS"] = td
            try:
                self.assertEqual(str(door.REPORTS()), td)
                s1 = door.sync(False)
                self.assertEqual(listing(Path(td)), [], "乾跑寫了檔")
                self.assertFalse(s1["written"])
                self.assertEqual(s1["diff"]["NEW"], len(s1["links"]))
                s2 = door.sync(True)
                names = listing(Path(td))
                self.assertIn("VDF_SYSTEM_latest.json", names)
                self.assertIn("VDF_SYSTEM_latest.md", names)
                self.assertIn("LEDGER.tsv", names)
                self.assertTrue(any(n.endswith(".html") for n in names), names)
                self.assertTrue(s2["written"])
                s3 = door.sync(False)
                self.assertEqual((s3["diff"]["NEW"], s3["diff"]["GONE"], s3["diff"]["CHANGED"]), (0, 0, 0), s3["diff"])
                self.assertEqual(s3["diff"]["SAME"], len(s3["links"]))
            finally:
                if old is None:
                    os.environ.pop("VIA_VDFSYS_REPORTS", None)
                else:
                    os.environ["VIA_VDFSYS_REPORTS"] = old


class T05_SevenPlaces(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.v = load("ut_vcgc", VCGC)

    def test_01_spec(self):
        items = [i for i in self.v.spec_items()["items"] if i["id"] == "vdf_system"]
        self.assertEqual(len(items), 1)
        it = items[0]
        self.assertEqual(it["family"], "vdf")
        self.assertEqual(it["glob"], "VDF_SystemManager_v*.py")
        self.assertEqual(it["verb"], ["status"])
        self.assertFalse(it["net"])
        j = json.loads((REG / "VIA_InputConsole_Spec_v0100.json").read_text(encoding="utf-8"))
        grp = [g for g in j["families"]["vdf"]["groups"] if g.get("id") == "management"]
        self.assertEqual(len(grp), 1)
        self.assertEqual(grp[0]["items"][0].get("test_verb"), ["--selftest"])

    def test_02_grid_three_stations(self):
        st = [s for s in self.v.grid_stations()["stations"] if "VDF_SystemManager" in s["path"]]
        self.assertEqual(sorted(tuple(s["args"]) for s in st), [("--selftest",), ("launch", "--no-probe"), ("status",)], [s["name"] for s in st])
        self.assertTrue(all(s["present"] is True for s in st))
        names = {tuple(s["args"]): s["name"] for s in st}
        self.assertIn("廿九檢", names[("--selftest",)])
        self.assertIn("啟動就緒", names[("launch", "--no-probe")])

    def test_03_deck_tasks(self):
        tasks = self.v.deck_tasks()["tasks"]
        for key, fam in (("vdf_system", "VDF_SystemManager"), ("vrn_system", "VRN_SystemManager")):
            self.assertIn(key, tasks)
            argv = tasks[key]["argv"]
            self.assertEqual(argv[-1], "status")
            self.assertIn(fam, Path(argv[1]).name)
            self.assertTrue(Path(argv[1]).is_file(), argv[1])
            self.assertFalse(tasks[key]["net"])

    def test_04_manager_names_pure_chinese(self):
        m = self.v.manager_names()
        for key in ("vdf_system", "vrn_system"):
            self.assertIn(key, m["tasks"])
            self.assertIsNone(re.search(r"[A-Za-z]{2,}_[A-Za-z0-9_]+|(?:ENG|MDL)\d+", m["tasks"][key]), m["tasks"][key])
        for key in ("VDF_SystemManager", "VRN_SystemManager"):
            self.assertIn(key, m["engines"])
            self.assertIsNone(re.search(r"[A-Za-z]{2,}_[A-Za-z0-9_]+|(?:ENG|MDL)\d+", m["engines"][key]), m["engines"][key])

    def test_05_inventory_active_codes(self):
        recs = {r["key"]: r for r in self.v.component_registry()["records"]}
        for key, prefix in (("system|VDF_SystemManager", "VIA-SYS-"), ("engine|VDF_ENG045_OutputHub", "VIA-ENG-"), ("system|vdf_input_matrix", "VIA-SYS-")):
            self.assertIn(key, recs)
            self.assertEqual(recs[key].get("state", "ACTIVE"), "ACTIVE")
            self.assertTrue(recs[key]["code"].startswith(prefix), recs[key]["code"])

    def test_06_handover_doc_and_register_measured_not_assumed(self):
        docs = [q for q in (VIA / "docs").glob("*.md") if "VDF_SystemManager" in q.read_text(encoding="utf-8", errors="replace")]
        self.assertGreater(len(docs), 0, "交接文沒有提到 VDF_SystemManager")
        door = load("ut_vdfsys", DOOR)
        up = door.upstream()
        self.assertEqual(set(up["seven"]), {"spec", "grid", "register", "deck", "manager", "inventory", "handover"})
        for k in ("spec", "grid", "deck", "manager", "handover"):
            self.assertTrue(up["seven"][k], f"{k} 未登")
        self.assertTrue(str(up["seven"]["inventory"]).startswith("VIA-SYS-"))
        reg = newest(VIA, "Register-VIA-Commands-v*.ps1")
        has_cmd = bool(reg) and ("function global:via-vdfsys" in reg.read_text(encoding="utf-8", errors="replace"))
        self.assertEqual(bool(up["seven"]["register"]), has_cmd, "Register 短令登沒登要量,不假綠")


class T06_Readers(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.door = load("ut_vdfsys", DOOR)

    def test_01_logic_reports_unversioned_separately(self):
        lo = self.door.read("logic")
        self.assertIn(lo["state"], ("GREEN", "STALE"))
        cards = lo["cards"]
        self.assertIsInstance(cards.get("unversioned"), list)
        self.assertIsInstance(cards.get("book_only"), list)
        self.assertTrue(set(cards["unversioned"]).isdisjoint(cards["book_only"]))
        eng = VDF / "engine"
        for f in cards["unversioned"]:
            self.assertTrue((eng / f"{f}.py").is_file() or (VDF / f"{f}.py").is_file(), f)
            self.assertFalse(list(eng.glob(f"{f}_v????.py")), f"{f} 有尾版檔卻被報成無版號")

    def test_02_bridge_single_key(self):
        r = self.door.read("bridge", "VDF_ENG054")
        hit = r.get("hit") or {}
        self.assertTrue({"accel", "net", "net_caller"} <= set(hit), hit)
        self.assertTrue(hit["accel"] and hit["net"])
        miss = self.door.read("bridge", "NOPE_ENG999")
        self.assertIsNone(miss.get("hit"))

    def test_03_tools_present_not_red(self):
        t = self.door.read("tool")
        self.assertIn(t["state"], ("GREEN", "STALE"))
        for name in ("VeritasCeleritas.py", "VeritasAegisNexus.py"):
            self.assertIn(name, t["tools"])
            self.assertTrue(t["tools"][name]["exists"], name)

    def test_04_records_pointers_not_copies(self):
        r = self.door.read("records")
        self.assertIn(r["state"], ("GREEN", "NODATA"))
        self.assertIn("VDF", json.dumps(r, ensure_ascii=False, default=str))

    def test_05_zero_network_consent_readonly(self):
        src = DOOR.read_text(encoding="utf-8").split("def selftest(")[0]
        self.assertIsNone(re.search(r"^\s*(import requests|from requests|import socket|import urllib\.request)", src, re.M))
        self.assertIsNone(re.search(r"environ\[\s*['\"]VIA_(NET|SCRAPE)_CONSENT['\"]\s*\]\s*=", src))
        self.assertNotIn("putenv(", src)
        self.assertNotIn("pip install", src)


class T07_Launch(unittest.TestCase):
    """啟動就緒(對接口 v0103 launch):只量不動手——閘與境是操作員的手,對接口把「差什麼」量出來、把下一行印出來。"""
    Z94_STEPS = ("VDF_ENG077_ActiveETFUniverse", "VDF_ENG078_ActiveETFHoldingsHistory", "VDF_ENG076_ETFRevenueMomentum", "CGC_MDL131_ProjectCompletion",
                 "CGC_MDL133_ProductGate", "CGC_MDL135_EnvGovernance", "CGC_MDL136_EntryBridge", "VDF_ENG079_LocalDbConsolidate", "CGC_MDL137_RunGate",
                 "VDF_ENG081_UniverseAlign", "CGC_MDL139_InputConsole", "CGC_MDL140_HandoverConsole", "CGC_MDL141_ClosingGate")

    @classmethod
    def setUpClass(cls):
        cls.door = load("ut_vdfsys", DOOR)

    def test_01_parity_negative_control(self):
        d = self.door
        with tempfile.TemporaryDirectory(prefix="vdfsys_ut_") as td:
            sh, ps = Path(td) / "b.sh", Path(td) / "b.ps1"
            sh.write_text("python3 \"$(newest 'VDF_ENG055_OmniFetch_v*.py')\" run\n# newest 'VDF_ENG999_Ghost_v*.py'\n"
                          "python3 \"$ENG/VDF_ENG051_ActiveTWETF_Holdings.py\"\npython3 \"$(ls \"$REG\"/CGC_MDL088_SystemTestPages_v*.py | sort | tail -1)\" run\n", encoding="utf-8")
            ps.write_text("Step \"x\" (Newest $ENG \"VDF_ENG055_OmniFetch_v*.py\") @(\"run\")\nStep \"y\" (Join-Path $ENG \"VDF_ENG051_ActiveTWETF_Holdings.py\") @()\n", encoding="utf-8")
            neg = d.chain_parity(sh, ps)
            self.assertEqual(neg["state"], "RED")
            self.assertEqual(neg["only_sh"], ["CGC_MDL088_SystemTestPages"])
            self.assertEqual(neg["steps_sh"], 3, "整行註解裡的鬼引擎不算步")
            ps.write_text(ps.read_text(encoding="utf-8") + "Step \"z\" (Newest $REG \"CGC_MDL088_SystemTestPages_v*.py\") @(\"run\")\n", encoding="utf-8")
            bare = d.chain_parity(sh, ps)
            self.assertEqual(bare["state"], "STALE", "步齊但裸 python=STALE(批384 律)")
            ps.write_text(ps.read_text(encoding="utf-8") + "$PY = & python $envpy envpy vdf\n", encoding="utf-8")
            pos = d.chain_parity(sh, ps)
            self.assertEqual(pos["state"], "GREEN", pos.get("why"))
            self.assertEqual(pos["only_sh"], [])
            self.assertEqual(pos["only_ps1"], [])
            gone = d.chain_parity(sh, Path(td) / "nope.ps1")
            self.assertEqual(gone["state"], "ABSENT")

    def test_02_real_boot_chain_two_carriers_same_chain(self):
        d = self.door
        real = d.chain_parity()
        self.assertEqual(real["state"], "GREEN", real.get("why"))
        self.assertGreaterEqual(real["steps_sh"], 40)
        self.assertEqual(real["steps_sh"], real["steps_ps1"])
        ps_steps = d.chain_steps((REG / "via_boot_update.ps1").read_text(encoding="utf-8"))
        for fam in self.Z94_STEPS:
            self.assertIn(fam, ps_steps, f"{fam} 不在 .ps1(Z94 那 13 步)")
        src = (REG / "via_boot_update.ps1").read_text(encoding="utf-8")
        self.assertIn("envpy vdf", src, ".ps1 家族境 python 要走 CGC_MDL136 envpy 正本")
        self.assertIn("& $PY $script", src)
        self.assertNotIn("& python $script", src)
        self.assertNotIn("\r", src, "L93:本檔在庫是 LF")

    def test_03_launch_no_probe_json_shape_and_rc(self):
        with tempfile.TemporaryDirectory(prefix="vdfsys_ut_") as td:
            r = run([DOOR, "launch", "--no-probe", "--json"], {"VIA_VDFSYS_REPORTS": td})
        self.assertIn(r.returncode, (0, 1, 2, 3, 4), r.stderr[-800:])
        j = tail_json(r.stdout)
        self.assertEqual(j.get("rc"), r.returncode)
        self.assertIn(j.get("state"), ("GREEN", "RED", "NODATA", "ABSENT", "GATED", "STALE"))
        for k in ("python", "libs", "consent", "net_tool", "launchers", "parity", "evidence", "data", "next", "why"):
            self.assertIn(k, j, k)
        self.assertFalse(j["probe"])
        self.assertEqual(j["parity"]["state"], "GREEN", j["parity"].get("why"))
        self.assertEqual(j["launchers"]["cmds_missing"], [], "Register 尾版少了啟動要用的短令")
        self.assertTrue(j["launchers"]["fetch_ps1"] and j["launchers"]["lanes"] and j["launchers"]["chain_runner"])
        self.assertIn("CGC_MDL137", j["python"]["ruler"])
        self.assertGreaterEqual(len(j["next"]), 3)
        self.assertNotIn("啟動器/鏈缺", j["why"])

    def test_04_rc_table_and_next_card_match_state(self):
        d = self.door
        self.assertEqual(d.LAUNCH_RC, {"GREEN": 0, "RED": 1, "NODATA": 2, "ABSENT": 3, "GATED": 4})
        before = (os.environ.get("VIA_NET_CONSENT"), os.environ.get("VIA_SCRAPE_CONSENT"))
        r = d.read_launch(probe=False)
        self.assertEqual((os.environ.get("VIA_NET_CONSENT"), os.environ.get("VIA_SCRAPE_CONSENT")), before, "啟動就緒動了同意閘")
        self.assertEqual(r["rc"], d.LAUNCH_RC[r["state"]])
        first = r["next"][0]
        expect = {"GATED": "[你的手] $env:VIA_NET_CONSENT", "ABSENT": "[你的手] ", "RED": "[修] ", "GREEN": "via-vdffetch"}[r["state"]]
        self.assertTrue(first.startswith(expect), (r["state"], first))
        self.assertTrue(any("via_boot_update.ps1" in ln for ln in r["next"]), "下一步卡要指到每日鏈")

    def test_05_status_and_links_carry_launch(self):
        d = self.door
        with tempfile.TemporaryDirectory(prefix="vdfsys_ut_") as td:
            old = os.environ.get("VIA_VDFSYS_REPORTS")
            os.environ["VIA_VDFSYS_REPORTS"] = td
            try:
                s = d.collect()
            finally:
                if old is None:
                    os.environ.pop("VIA_VDFSYS_REPORTS", None)
                else:
                    os.environ["VIA_VDFSYS_REPORTS"] = old
        self.assertIn(s["launch"]["state"], d.LAMPS)
        self.assertFalse(s["launch"]["probe"], "status 走零子行程版")
        ids = {l["id"] for l in s["links"] if l.get("domain") == "launch"}
        self.assertEqual(ids, {"launch:boot_sh", "launch:boot_ps1", "launch:fetch", "launch:lanes"})
        self.assertEqual(s["rc"], d.rc_of(s), "啟動燈不折進本口 rc(RC_SCOPE 不含 launch)")
        self.assertNotIn("launch", d.RC_SCOPE)
        md = d.to_markdown(s)
        self.assertIn("一之三 · 啟動就緒", md)
        self.assertIn("下一步 1.", md)
        rows = {r["domain"]: r for r in d.catalog()}
        self.assertIn("launch", rows)
        self.assertIn("via-vdffetch", rows["launch"]["canon"])

    def test_06_launch_source_reads_only(self):
        src = DOOR.read_text(encoding="utf-8").split("def selftest(")[0]
        seg = src.split("def read_launch(")[1].split("def _print_launch(")[0]
        self.assertNotIn("subprocess.run(", seg, "現探委派 CGC_MDL137.probe_libs,本口不自起子行程")
        self.assertNotIn("environ[", seg)
        self.assertNotIn("install", seg.lower().replace("install_missing", ""))
        self.assertIn("probe_libs", seg)
        self.assertIn("python_for", seg)
        self.assertIn("FAMILY_LIBS", seg)


if __name__ == "__main__":
    unittest.main(verbosity=2)
