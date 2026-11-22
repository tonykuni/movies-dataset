#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VIA_PanoramaGuard v0103 — 薄尾:範圍掃描的基線要連「範圍本身」一起算 · 貼回包與卡片列出阻擋原因

主機 2026-11-22 09:09 實跑(--changed-since origin/main~8):總判 FAIL_STOP,卡片只說「先處理 blocked」卻沒列原因。
根因(本工具 v0102 的錯):範圍掃描的基線只分「全樹 / 範圍」兩種,沒有分「哪一個範圍」。
  08:43 掃 286 檔(紅 N)→ main 前進後 09:09 掃 287 檔(紅 218)→ 被當成「同一個掃描變紅了」→ scan_baseline_regression 擋下。
本版:
  ① 範圍掃描的基線鍵 = 版本 + 範圍檔清單的指紋 → 不同範圍各自一條基線,不再互相比;同一範圍重掃才比(棘輪照舊)
  ② 卡片多 blocked(前 20 筆:檔 · 原因);貼回包在紅之前先列「[擋] …」
其餘全部照 v0102 / v0101。
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

import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VIA_PanoramaGuard"
TAIL3 = "0.1.3"


def _vnum(path) -> int:
    m = re.search(r"_v(\d+)$", Path(path).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
if PRIOR_PATH.stem in sys.modules:
    PRIOR = sys.modules[PRIOR_PATH.stem]
else:
    _spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem, PRIOR_PATH)
    PRIOR = importlib.util.module_from_spec(_spec)
    sys.modules[PRIOR_PATH.stem] = PRIOR
    _spec.loader.exec_module(PRIOR)
BASE = PRIOR.PRIOR          # v0101 本體(run_engine · VERSION 在這)
BASE_VERSION = PRIOR.BASE_VERSION
PRIOR.TAIL = TAIL3
BASE.VERSION = BASE_VERSION + "+" + TAIL3


def __getattr__(name):
    return getattr(PRIOR, name)


def scope_key(files) -> str:
    return hashlib.sha256("\n".join(sorted(files)).encode("utf-8")).hexdigest()[:12]


_PREV_RUN_ALL = PRIOR.run_all
_PREV_PASTE = PRIOR.pastepack
_PREV_POLICY = PRIOR._policy_key


def run_all(args) -> int:
    """照 v0102 跑;範圍掃描時把範圍指紋放進版本字串(→ project_key),不同範圍各自一條基線。"""
    base = BASE_VERSION + "+" + TAIL3
    real_inventory = PRIOR.inventory

    def keyed(root, conf):
        names = real_inventory(root, conf)
        if PRIOR.SCOPE["files"] is not None:
            BASE.VERSION = base + "+scope-" + scope_key(PRIOR.SCOPE["files"])
        return names
    BASE.inventory = keyed
    try:
        return _PREV_RUN_ALL(args)
    finally:
        BASE.inventory = real_inventory
        BASE.VERSION = base


def blocked_of(report: dict) -> list:
    return [list(b) for b in (report.get("blocked") or [])]


def pastepack(report, tools, gov, summary, limit=PRIOR.PASTE_LINES):
    text = _PREV_PASTE(report, tools, gov, summary, limit)
    bl = blocked_of(report)
    if not bl:
        return text
    lines = text.splitlines()
    extra = ["[擋 %d 筆] 本輪被擋下(修復覆層已收回、原檔沒動)" % len(bl)] + ["[擋] %s · %s" % (b[0], b[1]) for b in bl[:20]]
    keep = max(0, limit - len(extra))
    body, nxt = lines[:-1], lines[-1]
    body = body[:max(0, keep - 1)]
    return "\n".join(body[:3] + extra + body[3:] + [nxt]) + "\n"


def _policy_key(conf, rel) -> str:
    """快取鍵不跟著範圍指紋變(同內容 + 同規則 + 同版本就共用),否則每換一次範圍快取就全失效。"""
    keep = {k: conf.get(k) for k in ("static_guard_rules", "subsystems")}
    keep["contract"] = conf.get("api_contracts", {}).get(rel)
    return hashlib.sha256(BASE.json_bytes([BASE_VERSION + "+" + TAIL3, BASE.RULES, keep, rel])).hexdigest()


PRIOR.run_all = run_all
PRIOR.pastepack = pastepack
PRIOR._policy_key = _policy_key

def _card_hook():
    """v0102 的 run_all 在結尾 print 卡片;本版包一層把 blocked 加進卡片(讀收據,不重算)。"""
    import builtins
    real_print = builtins.print

    def hooked(*a, **k):
        if len(a) == 1 and isinstance(a[0], str) and a[0].startswith("{") and '"receipt"' in a[0] and k.get("file") is None:
            try:
                card = json.loads(a[0])
                rep = BASE.read_json(Path(card["receipt"]) / "report.json")
                bl = blocked_of(rep)
                if bl:
                    card["blocked"] = bl[:20]
                    card["blocked_total"] = len(bl)
                a = (json.dumps(card, ensure_ascii=False, indent=1),)
            except (ValueError, KeyError, OSError):
                pass
        return real_print(*a, **k)
    return real_print, hooked


def selftest() -> int:
    import argparse
    import io
    import os
    import subprocess
    import tempfile
    import unittest
    from unittest import mock

    class Tail3(unittest.TestCase):
        def setUp(self):
            self.td = tempfile.TemporaryDirectory()
            self.addCleanup(self.td.cleanup)
            self.root = Path(self.td.name) / "src"
            self.root.mkdir()
            self.out = Path(self.td.name) / "out"
            PRIOR.SCOPE["files"] = None
            self.addCleanup(lambda: PRIOR.SCOPE.update(files=None))

        def put(self, rel, text):
            p = self.root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding="utf-8")

        def call(self, **kw):
            base = dict(root=str(self.root), output=str(self.out), mode="scan", workers=2, require_accelerator=False, project_tests=False,
                        suite=None, tools="none", tool_timeout=60, changed_since=None, paths=None, if_etag=None, no_cache=True,
                        profile="generic", paste_lines=PRIOR.PASTE_LINES, narrow_except=False, draft_docstrings=False, commit=False, tool_fix=False)
            base.update(kw)
            real, hooked = _card_hook()
            buf = io.StringIO()
            with mock.patch("builtins.print", hooked), mock.patch("sys.stdout", new=buf):
                rc = run_all(argparse.Namespace(**base))
            return rc, json.loads(buf.getvalue())

        def test_S1_different_scopes_do_not_block_each_other(self):
            self.put("a.py", "# [AST-ANCHOR: A]\nX = 1\n")
            self.put("b.py", "try:\n    pass\nexcept:\n    pass\n")           # 有紅
            rc1, c1 = self.call(paths=["a.py"])
            rc2, c2 = self.call(paths=["a.py", "b.py"])                     # 範圍變大、紅變多:不同範圍 → 不擋
            self.assertNotEqual(c2.get("decision"), "FAIL_STOP", c2.get("blocked"))
            self.assertNotIn("blocked", c2)

        def test_S2_same_scope_still_ratchets(self):
            self.put("b.py", "X = 1\n")
            self.call(paths=["b.py"])
            self.put("b.py", "try:\n    pass\nexcept:\n    pass\n")
            rc, c = self.call(paths=["b.py"])                               # 同一範圍變紅 → 照舊擋
            self.assertEqual(c["decision"], "FAIL_STOP")
            self.assertTrue(any(b[1] == "scan_baseline_regression" for b in c["blocked"]), c.get("blocked"))
            pack = Path(c["pastepack"]).read_text(encoding="utf-8").splitlines()
            self.assertTrue(any(x.startswith("[擋]") and "scan_baseline_regression" in x for x in pack))
            self.assertTrue(pack[-1].startswith("NEXT:"))
            self.assertLessEqual(len(pack), PRIOR.PASTE_LINES)

        def test_S3_version_restored_after_run(self):
            self.put("a.py", "X = 1\n")
            self.call(paths=["a.py"])
            self.assertEqual(BASE.VERSION, BASE_VERSION + "+" + TAIL3)

        def test_S4_file_surface(self):
            text = Path(__file__).read_text(encoding="utf-8")
            self.assertEqual(text.splitlines()[2].strip(), "# [VIA:ACCEL-BRIDGE:v0111]")
            self.assertFalse(re.search(r"^\s*(import|from)\s+talib", text, re.M))

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(Tail3)
    ok = unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful()
    print("[計] VIA_PanoramaGuard v%s 本版 %d 項 · %s" % (TAIL3, suite.countTestCases(), "PASS" if ok else "FAIL"), flush=True)
    keep = (PRIOR.run_all, PRIOR.pastepack, PRIOR._policy_key)
    PRIOR.run_all, PRIOR.pastepack, PRIOR._policy_key = _PREV_RUN_ALL, _PREV_PASTE, _PREV_POLICY
    PRIOR.TAIL = "0.1.2"
    BASE.VERSION = BASE_VERSION + "+0.1.2"
    try:
        rc_prior = PRIOR.selftest()
    finally:
        PRIOR.run_all, PRIOR.pastepack, PRIOR._policy_key = keep
        PRIOR.TAIL = TAIL3
        BASE.VERSION = BASE_VERSION + "+" + TAIL3
    good = ok and rc_prior == 0
    print("[計] VIA_PanoramaGuard v%s 自測 %s" % (TAIL3, "PASS" if good else "FAIL"), flush=True)
    return 0 if good else 2


def main() -> int:
    if sys.argv[1:2] == ["selftest"]:
        return selftest()
    import builtins
    real, hooked = _card_hook()
    builtins.print = hooked
    try:
        return PRIOR.main()
    finally:
        builtins.print = real


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, RuntimeError, KeyError, TypeError, RecursionError) as err:
        print("VIA BLOCKED · %s · %s" % (type(err).__name__, err), file=sys.stderr)
        sys.exit(2)
