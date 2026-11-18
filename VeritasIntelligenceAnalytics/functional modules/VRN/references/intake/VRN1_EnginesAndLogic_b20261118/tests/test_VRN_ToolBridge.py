# -*- coding: utf-8 -*-
# ===== [VRN:ID:v0100] VRN-TST021 · test_VRN_ToolBridge · TEST =====
# AST 注入（只加註解，AST 不變）：類別 1 · 函式 11；逐一編號在 ssot/VRN_ID_SSOT_v0100.json
# ===== [VRN:ID:END] =====
"""Unit tests for VRN_ToolBridge v0100（VRN-1 借出 / 借入工具 · 2026-10-20 操作員「VRN-1 VRN-2 工具可相互取用 · 獨立系統兩個 MAIN」）。"""
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
import hashlib
import importlib.util
import io
import json
import os
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parent / "engine" / "VRN_ToolBridge_v0100.py"


# [VRN-ID] VRN-TST021-FNC001 · IO
def def_load():
    spec = importlib.util.spec_from_file_location("vrn_toolbridge_test", str(ENGINE))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


# [VRN-ID] VRN-TST021-CLS001 · CLASS
class def_ToolBridgeTests(unittest.TestCase):
    """自己的工具冊 sha256 對得上；借別的系統的工具要逐檔核對、不在對方的夾留檔；借不到只用自己的。"""

    # [VRN-ID] VRN-TST021-FNC002 · LOGIC
    @classmethod
    def setUpClass(cls):
        cls.B = def_load()

    # [VRN-ID] VRN-TST021-FNC003 · LOGIC
    def setUp(self):
        self.keep = os.environ.get("VIA_VRN2_ROOT")

    # [VRN-ID] VRN-TST021-FNC004 · LOGIC
    def tearDown(self):
        if self.keep is None:
            os.environ.pop("VIA_VRN2_ROOT", None)
        else:
            os.environ["VIA_VRN2_ROOT"] = self.keep

    # [VRN-ID] VRN-TST021-FNC005 · LOGIC
    def peer(self, td: Path, ready=True):
        B = self.B
        via = td / "VIA"
        tool = via / "functional modules" / "VRN" / "tool.py"
        tool.parent.mkdir(parents=True)
        tool.write_text("def near(pdf, page, item, value=None):\n    return {'section': 'Growth (%)', 'found': True}\n", encoding="utf-8")
        mf = via.joinpath(*B.VRN2_MANIFEST)
        mf.parent.mkdir(parents=True)
        rel = "functional modules/VRN/tool.py"
        sha = hashlib.sha256(tool.read_bytes()).hexdigest()
        mf.write_text(json.dumps({"schema": B.SCHEMA, "system": "VRN-2", "root": str(via),
                                  "offers": [{"id": "section.near", "file": rel, "entry": "near", "ready": ready, "why": "x",
                                              "files": [{"file": rel, "sha256": sha}]}]}), encoding="utf-8")
        os.environ["VIA_VRN2_ROOT"] = str(via)
        return via, tool, mf

    # [VRN-ID] VRN-TST021-FNC006 · TEST
    def test_own_manifest_offers_pivot_and_is_deterministic(self):
        B = self.B
        a, b = B.manifest(), B.manifest()
        self.assertEqual(a, b)
        self.assertEqual([o["id"] for o in a["offers"]], ["table.pivot_db"])
        self.assertNotIn("written", a)

    # [VRN-ID] VRN-TST021-FNC007 · TEST
    def test_committed_manifest_matches_the_files(self):
        B = self.B
        if B.MANIFEST.is_file():
            self.assertEqual(B.check_manifest(), [])

    # [VRN-ID] VRN-TST021-FNC008 · TEST
    def test_check_flags_a_stale_sha(self):
        B = self.B
        with tempfile.TemporaryDirectory() as td:
            book = B.manifest()
            book["offers"][0]["files"][0]["sha256"] = "0" * 64
            p = Path(td) / "m.json"
            p.write_text(json.dumps(book), encoding="utf-8")
            issues = B.check_manifest(p, B.REPO_ROOT if B.REPO_ROOT != B.VRN_ROOT else B.VRN_ROOT)
            self.assertTrue(any("build" in i for i in issues))

    # [VRN-ID] VRN-TST021-FNC009 · TEST
    def test_borrow_checks_sha_and_leaves_no_pycache(self):
        B = self.B
        with tempfile.TemporaryDirectory() as td:
            _via, tool, mf = self.peer(Path(td))
            fn, rec = B.borrow("section.near", mf)
            self.assertEqual(fn("x.pdf", 1, "EPS")["section"], "Growth (%)")
            self.assertEqual(rec["from"], "VRN-2")
            self.assertFalse((tool.parent / "__pycache__").exists())
            tool.write_text(tool.read_text(encoding="utf-8") + "# edited\n", encoding="utf-8")
            with self.assertRaises(B.BorrowError):
                B.borrow("section.near", mf)

    # [VRN-ID] VRN-TST021-FNC010 · TEST
    def test_peer_marks_tool_unusable(self):
        B = self.B
        with tempfile.TemporaryDirectory() as td:
            self.peer(Path(td), ready=False)
            got = B.borrow_all(("section.near",))
            self.assertEqual(got["rows"][0]["state"], "REFUSED")
            self.assertNotIn("section.near", got["tools"])

    # [VRN-ID] VRN-TST021-FNC011 · TEST
    def test_selftest_passes(self):
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(self.B.selftest(verbose=False), 0)


if __name__ == "__main__":
    unittest.main()
