#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ===== [VRN:ID:v0100] VRN-TST011 · test_VRN_Lock · TEST =====
# AST 注入（只加註解，AST 不變）：類別 1 · 函式 11；逐一編號在 ssot/VRN_ID_SSOT_v0100.json
# ===== [VRN:ID:END] =====
"""VRN_Lock v0100 (operator 2026-10-11「正確鎖功能鎖成功部分及引擎 位成功的持續實測實際修正直到輸出正確可驗證無誤」): the engine
lock is current (a logic change without new proof fails here), the output ledger never lives in VRN, a locked part that changes is
BROKEN, and what is not verified is on the fix list."""

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
import os
import sys
import tempfile
import unittest
from pathlib import Path

VRN = Path(__file__).resolve().parents[1]


# [VRN-ID] VRN-TST011-FNC001 · IO
def def_load(name, path):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


# [VRN-ID] VRN-TST011-CLS001 · CLASS
class def_LockTests(unittest.TestCase):
    # [VRN-ID] VRN-TST011-FNC002 · LOGIC
    @classmethod
    def setUpClass(cls):
        cls.L = def_load("VRN_Lock_v0100", VRN / "engine" / "VRN_Lock_v0100.py")

    # [VRN-ID] VRN-TST011-FNC003 · TEST
    def test_selftest(self):
        self.assertEqual(self.L.selftest(verbose=False), 0)

    # [VRN-ID] VRN-TST011-FNC004 · TEST
    def test_engine_lock_is_current(self):
        """A locked engine whose logic changed fails here until `VRN_Main_v0100.py lock` proves it again."""
        rows = self.L.check_engine_lock()
        bad = [r for r in rows if r["state"] in ("CHANGED", "MISSING", "NO_BOOK")]
        self.assertEqual(bad, [])
        held = {r["file"] for r in rows if r["state"] == "HELD"}
        for rel in ("engine/VRN_TitleTrim_v0100.py", "engine/VRN_Lock_v0100.py", "engine/VRN_PageRegions_v0100.py",
                    "engine/VIA_VRN_FirstPageEngine.py", "ssot/VRN_TitleTrim_SSOT_v0100.json", "ssot/VRN_Method_SSOT_v0100.json"):
            self.assertIn(rel, held)
        book = json.loads((VRN / "ssot" / "VRN_EngineLock_SSOT_v0100.json").read_text(encoding="utf-8"))
        self.assertTrue(all(p["ok"] for p in book["proofs"].values()), "every engine in the lock was proven on its known answers")
        self.assertNotIn("engine/VRN_AutoTestLoop.py", self.L.targets(), "the test orchestrator is not an output engine")

    # [VRN-ID] VRN-TST011-FNC008 · TEST
    def test_fingerprint_is_the_same_on_every_python(self):
        """ast.dump changed between Python 3.12 and 3.13: the lock uses its own canonical walk (same hash on 3.11, 3.12, 3.13)."""
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "g.py"
            src.write_text('def f(x, *a, k=None):\n    """doc"""\n    return [y async for y in x] if k else f"{x!r:>4}"\n', encoding="utf-8")
            self.assertEqual(self.L.ast_sha(src), "9b63db77dcdf67c29d7fa281b0f1d85d19fd42ae57c1d60fb6eafa7b769993e9")

    # [VRN-ID] VRN-TST011-FNC005 · TEST
    def test_proofs_name_real_files(self):
        rules = self.L.rules()
        for name, spec in rules["proofs"].items():
            for rel in spec["covers"]:
                self.assertTrue((VRN / rel).is_file(), f"{name}: {rel}")

    # [VRN-ID] VRN-TST011-FNC006 · TEST
    def test_ledger_is_never_inside_vrn(self):
        saved = os.environ.pop("VRN_LOCK_HOME", None)
        try:
            home, _why = self.L.ledger_home(str(VRN / "ssot"))
            self.assertNotIn(VRN.resolve(), home.resolve().parents)
            self.assertNotEqual(home.resolve(), VRN.resolve())
        finally:
            if saved is not None:
                os.environ["VRN_LOCK_HOME"] = saved

    # [VRN-ID] VRN-TST011-FNC007 · TEST
    def test_a_locked_part_that_changes_is_broken(self):
        with tempfile.TemporaryDirectory() as tmp:
            item = {"file": "a.pdf", "file_sha256": "ef" * 32, "part": "annual.gross_profit@2025", "value": 504.0, "state": "VERIFIED"}
            first = self.L.Ledger(tmp).apply([item], {})
            self.assertEqual(first["counts"].get("NEW"), 1)
            again = self.L.Ledger(tmp).apply([dict(item, value="504")], {})
            self.assertEqual(again["counts"].get("HELD"), 1)
            worse = self.L.Ledger(tmp).apply([dict(item, value=50.4, state="REPORT_CHECK")], {})
            self.assertEqual(worse["verdict"], "RED")
            self.assertEqual(worse["rows"][0]["locked_value"], "504")

    # round 4 (2026-10-12): the operator's ledger held the phone as '223269899' (read as a number); the same phone written
    # '886223269899' is HELD, an extension appended to the number is BROKEN
    # [VRN-ID] VRN-TST011-FNC009 · TEST
    def test_a_phone_is_the_same_phone_by_its_last_eight_digits(self):
        with tempfile.TemporaryDirectory() as tmp:
            tel = {"file": "a.pdf", "file_sha256": "ab" * 32, "part": "cover.tel", "value": "0223269899", "state": "VERIFIED"}
            self.L.Ledger(tmp).apply([tel], {})
            again = self.L.Ledger(tmp).apply([dict(tel, value="886223269899")], {})
            self.assertEqual(again["counts"].get("HELD"), 1)
            worse = self.L.Ledger(tmp).apply([dict(tel, value="8862232698997960")], {})
            self.assertEqual(worse["counts"].get("BROKEN"), 1)
            self.assertTrue(self.L.same_value("cover.tel", "223269899", "886223269899"))
            self.assertEqual(self.L.canonical("886223269899"), "886223269899")

    # round 5 (2026-10-12): the ledger written before round 4 holds phones as '8.862232698e+11' (ten significant digits,
    # lossy); the same phone written in full is HELD and the ledger takes the full form, a different phone is BROKEN
    # [VRN-ID] VRN-TST011-FNC010 · TEST
    def test_a_lossy_float_in_the_ledger_is_the_same_value_and_is_healed(self):
        L = self.L
        self.assertTrue(L.same_value("cover.tel", "8.862232698e+11", "886223269812"))
        self.assertFalse(L.same_value("cover.tel", "8.862232698e+11", "886223269999"))
        self.assertFalse(L.lossy_same("886223269812", "886223269812"), "only a lossy old value is read this way")
        with tempfile.TemporaryDirectory() as tmp:
            key = f"{'ab' * 8}|cover.tel"
            ledger = L.Ledger(tmp)
            ledger.data.setdefault("parts", {})[key] = {"file": "a.pdf", "file_sha256": "ab" * 32, "part": "cover.tel",
                                                        "value": "8.862232698e+11", "locked_at": "t"}
            ledger.save()
            tel = {"file": "a.pdf", "file_sha256": "ab" * 32, "part": "cover.tel", "value": "886223269812", "state": "VERIFIED"}
            got = L.Ledger(tmp).apply([tel], {})
            self.assertEqual((got["counts"].get("HELD"), got["rows"][0]["lock"]), (1, "HELD"))
            self.assertEqual(L.Ledger(tmp).data["parts"][key]["value"], "886223269812", "healed on disk")
            worse = L.Ledger(tmp).apply([dict(tel, value="886223269999")], {})
            self.assertEqual(worse["counts"].get("BROKEN"), 1)


    # 2026-10-13 operator「公司名稱價格一率至DATABASE去取」: a value that now comes from the database is a change of source, not a
    # regression; the same company written with -KY or its company form is the same value
    # [VRN-ID] VRN-TST011-FNC011 · TEST
    def test_a_value_from_the_database_replaces_the_lock_without_breaking(self):
        L = self.L
        with tempfile.TemporaryDirectory() as tmp:
            base = {"file": "a.pdf", "file_sha256": "ef" * 32, "state": "VERIFIED"}
            L.Ledger(tmp).apply([dict(base, part="title.company", value="Wiwynn")], {})
            got = L.Ledger(tmp).apply([dict(base, part="title.company", value="緯穎", source="db")], {})
            self.assertEqual(got["rows"][0]["lock"], "NEW")
            self.assertEqual(got["counts"].get("BROKEN", 0), 0)
            self.assertEqual(L.Ledger(tmp).data["parts"][f"{'ef' * 8}|title.company"]["source"], "db")
            again = L.Ledger(tmp).apply([dict(base, part="title.company", value="廣達", source="db")], {})
            self.assertEqual(again["counts"].get("BROKEN"), 1, "once from the database, a different value is a regression again")
        self.assertTrue(L.same_value("title.company", "慧洋", "慧洋-KY"))
        self.assertTrue(L.same_value("title.company", "頎邦", "頎邦科技股份有限公司"))
        self.assertFalse(L.same_value("title.company", "台積電", "聯電"))

if __name__ == "__main__":
    unittest.main()
