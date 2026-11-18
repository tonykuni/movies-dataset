#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VDF_ENG094_ActiveETFActivity v0103 — 薄尾:接回「在尾版上替換 analyze,build 會用到」這一格(v0102 漏了)。

2026-11-18 GitHub CI(VDF · manager and daily data contracts)實錄:
  test_via_etf_activity_v0100 取家族尾版後 patch 尾版的 analyze,再叫 build,斷言 analyze 被叫 1 次 → 實得 0 次。
根因:v0101 特別留了這一格(analyze 放在尾版自己的 namespace,build 執行時把前版的 analyze 換成尾版當下那一支);
  v0102 是純轉接的薄尾,尾版上沒有自己的 analyze / build,測試換到的那一支沒有人用。
本版(v0102 · v0101 一字不動):照 v0101 的接法在本檔放 analyze 與 build;build 執行期間把 v0101 的 analyze 換成本檔當下的那一支,跑完還原。
v0102 的系統獨立修正(VCGC 的尺不在 / 壞掉時用 VDF 自己的尺)原樣保留;其餘公開名稱、main、指令列原樣轉交。
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

import importlib.util
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_ENG094_ActiveETFActivity"
VERSION = Path(__file__).stem.rsplit("_v", 1)[-1]


def _vnum(p) -> int:
    m = re.search(r"_v(\d+)$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location("eng094_prior_for_v" + VERSION, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)          # v0102(同意尺的退路)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
BODY = PRIOR.PRIOR                                      # v0101(它的 build 會把自己那一格 analyze 交給 v0100)


def __getattr__(name: str):
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


# build 內部叫的 analyze 走本模組這一格(替換本尾版的 analyze 就等於替換本體的;CI 的 test_via_etf_activity 取尾版後 patch 這裡)
analyze = BODY.analyze


def build(*args, **kwargs):
    """前版 build 原樣;只把它呼叫的 analyze 換成本模組當下的 analyze(可被測試替換),跑完還原。"""
    orig = BODY.analyze
    BODY.analyze = globals()["analyze"]
    try:
        return BODY.build(*args, **kwargs)
    finally:
        BODY.analyze = orig


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in a or "selftest" in a:
        return selftest()
    return PRIOR.main(argv)


def selftest() -> int:
    import tempfile
    from unittest import mock
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)) if note else ""))

    print("=== %s v%s 薄尾自測(尾版上替換 analyze,build 用得到;零網路)===" % (_STEM, VERSION))
    me = sys.modules[__name__]
    calls = []
    saved_build, saved_an = BODY.build, BODY.analyze

    def fake_body_build(*a, **k):
        return ("built", BODY.analyze("x"))

    BODY.build = fake_body_build
    try:
        with mock.patch.object(me, "analyze", side_effect=lambda v: calls.append(v) or "patched"):
            got = build()
        mid = BODY.analyze
    finally:
        BODY.build = saved_build
    chk("① 在尾版上替換 analyze → build 用到的就是替換後那一支(CI 那個斷言)", got == ("built", "patched") and calls == ["x"], got)
    chk("② build 跑完本體的 analyze 還原", mid is saved_an and BODY.analyze is saved_an)
    neg = []
    with mock.patch.object(PRIOR, "analyze", side_effect=lambda v: neg.append(v) or "p", create=True):
        BODY.build = lambda *a, **k: BODY.analyze("y")
        try:
            saved = BODY.analyze
            BODY.analyze = lambda v: "body"
            r_neg = PRIOR.build() if "build" in vars(PRIOR) else BODY.build()
        finally:
            BODY.analyze = saved
            BODY.build = saved_build
    chk("③ 負控:在 v0102 上替換 analyze,build 用不到(本版要修的就是這個)", neg == [] and r_neg == "body", r_neg)
    chk("④ v0102 的同意尺退路還在:經本版拿得到 ruler / vdf_gate_open,而且本體 fetch 用的是它", callable(me.ruler) and me.vdf_gate_open({}) is False and BODY.consent_open is PRIOR.consent_open)
    chk("⑤ 其他公開名稱原樣轉交(plan · inspect_database · fund_interval)", all(callable(getattr(me, n, None)) for n in ("inspect_database", "fetch", "read_metrics")))
    with tempfile.TemporaryDirectory(prefix="eng094_v0103_") as td:
        chk("⑥ 庫不在:inspect_database 回 NODATA(經本版呼叫,行為同前版)", me.inspect_database(Path(td) / "missing.duckdb")["state"] == "NODATA")
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑦ 加速器橋真的匯入 · 不含本機路徑 · 不寫同意值", "import VIA_SuperAccel_Module as VIA_ACCEL" in src and ("C:" + "\\Users") not in src and ("_CONSENT\"] " + "=") not in src)
    rc = PRIOR.selftest()
    chk("⑧ 前版(v0102 → v0101)自測照過", rc == 0, "rc %s" % rc)
    good = all(ok)
    print("[計] %s v%s 本版 %d/%d · %s" % (_STEM, VERSION, sum(ok), len(ok), "PASS" if good else "FAIL"))
    return 0 if good else 1


if __name__ == "__main__":
    raise SystemExit(main())
