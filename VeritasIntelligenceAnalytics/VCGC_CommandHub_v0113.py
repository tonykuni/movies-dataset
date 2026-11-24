#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VCGC_CommandHub v0113 — 薄尾(v0100–v0112 一字不動):舊短令 via-vdffetch / via-vrnrun 照原意只跑自己那一段

操作員 2026-11-24「所有的指令全部 PY 化導入加速器 · 向外擷取的指令導入網路工具 · 短指令檢視可用就可用」→ 逐條檢視中樞指令冊:
  新指令 21 條 help 全過、舊名 21 條都指得到新名;背後 20 支程式語法樹都真的匯入加速器;對外擷取的入口(VDF 管理器 · VDF 並行
  啟動器)有網路橋;VDF 現役尾版 115 支全有加速器,用到網路套件的 11 支全有網路橋。
  唯一錯的:v0102 把舊名 via-vdffetch(VDF 擷取)與 via-vrnrun(VRN 跑報告)都導到 via-run(全線 VDF → VRN),
  打 via-vdffetch 會連 VRN 一起跑、打 via-vrnrun 會先跑 VDF 擷取。
本版:舊名帶上原意的範圍 —— via-vdffetch → via-run --vdf-only · via-vrnrun → via-run --vrn-only(其餘參數原樣轉;
  已經自己給 --vdf-only / --vrn-only 的照給的;--plan 照樣帶範圍)。via-fetch 照舊 = 全線。不 import 他系統。零 TA-Lib。
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
_STEM = "VCGC_CommandHub"
TAG = "VCGC_CommandHub v0113"


def _vnum(p) -> int:
    m = re.search(r"_v(\d+)$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
if PRIOR_PATH.stem in sys.modules:
    PRIOR = sys.modules[PRIOR_PATH.stem]
else:
    _spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem, PRIOR_PATH)
    PRIOR = importlib.util.module_from_spec(_spec)
    sys.modules[PRIOR_PATH.stem] = PRIOR
    _spec.loader.exec_module(PRIOR)


def __getattr__(name):
    return getattr(PRIOR, name)


def _owner(name: str):
    """前版鏈上自己定義 name 的那一版(換在真正被讀的那一層;R4 換錯層)。"""
    m, seen = PRIOR, set()
    while m is not None and id(m) not in seen:
        seen.add(id(m))
        if name in vars(m):
            return m
        m = vars(m).get("PRIOR") or vars(m).get("P0")
    return None


DISPATCH_OWNER = _owner("dispatch")          # v0102:main 的 x 動詞叫它模組裡的 dispatch
_DISPATCH0 = DISPATCH_OWNER.dispatch
LEGACY_SCOPE = {"via-vdffetch": "--vdf-only", "via-vrnrun": "--vrn-only"}
_SCOPE_FLAGS = {"--vdf-only", "--vrn-only"}


def legacy_args(name: str, args: list) -> tuple:
    """舊名 → (新名, 參數);只有 LEGACY_SCOPE 那兩條會補範圍旗標,其他原樣。"""
    if name in LEGACY_SCOPE:
        new = DISPATCH_OWNER.LEGACY[name]
        if not any(a in _SCOPE_FLAGS for a in args):
            args = [LEGACY_SCOPE[name], *args]
        return new, list(args)
    return name, list(args)


def dispatch(name: str, args: list) -> int:
    if name in LEGACY_SCOPE:
        new, a = legacy_args(name, args)
        print("[去重] %s 已併入 %s · 照原意只跑 %s(%s)" % (name, new, "VDF" if "vdf" in name else "VRN", " ".join(a)), file=sys.stderr)
        return DISPATCH_OWNER.main(DISPATCH_OWNER.CMD[new]["target"] + a)
    return _DISPATCH0(name, args)


DISPATCH_OWNER.dispatch = dispatch
_c = DISPATCH_OWNER.CMD.get("via-run")
if _c is not None and "via-vdffetch" not in _c["help"]:
    _c["help"] += " 舊名 via-vdffetch = --vdf-only · via-vrnrun = --vrn-only · via-fetch = 全線。"


def main(argv: list | None = None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    return PRIOR.main(a)


def selftest() -> int:
    import contextlib
    import io
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + name + ((" · " + str(note)[:300]) if note and not cond else ""), flush=True)

    print("[計] %s 自測開始(本版 4 項 · 前版 %s)" % (TAG, PRIOR_PATH.name), flush=True)
    chk("T1 換在 main 讀的那一層(v0102 的 dispatch)· 前版 v0112 · 舊名表裡兩條都指 via-run",
        Path(DISPATCH_OWNER.__file__).name == "VCGC_CommandHub_v0102.py" and DISPATCH_OWNER.dispatch is dispatch
        and PRIOR_PATH.name == "VCGC_CommandHub_v0112.py" and all(DISPATCH_OWNER.LEGACY[k] == "via-run" for k in LEGACY_SCOPE))
    chk("T2 via-vdffetch → run --vdf-only · via-vrnrun → run --vrn-only · --plan 也帶範圍 · 自己給了範圍照給的 · via-fetch 照舊全線",
        legacy_args("via-vdffetch", []) == ("via-run", ["--vdf-only"]) and legacy_args("via-vrnrun", ["--yes"]) == ("via-run", ["--vrn-only", "--yes"])
        and legacy_args("via-vdffetch", ["--plan"]) == ("via-run", ["--vdf-only", "--plan"])
        and legacy_args("via-vrnrun", ["--vdf-only"]) == ("via-run", ["--vdf-only"]) and legacy_args("via-fetch", []) == ("via-fetch", []))
    seen = []
    keep = DISPATCH_OWNER.main
    try:
        DISPATCH_OWNER.main = lambda a=None: seen.append(list(a)) or 0
        with contextlib.redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()):
            r = [main(["x", "via-vdffetch"]), main(["x", "via-vrnrun", "--yes"]), DISPATCH_OWNER.dispatch("via-vdffetch", [])]
    finally:
        DISPATCH_OWNER.main = keep
    chk("T3 PS 載入器的路(x 舊名)與選單的路(dispatch)都帶上範圍旗標進 run",
        r == [0, 0, 0] and seen[-3:] == [["run", "--vdf-only"], ["run", "--vrn-only", "--yes"], ["run", "--vdf-only"]], seen)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("T4 檔面:加速器橋 · 零 TA-Lib · 不寫同意閘 · 不 import 他系統",
        "[VIA:ACCEL-BRIDGE:v0100]" in src and not re.search(r"^\s*(import|from)\s+talib", src, re.M)
        and not re.search(r"os\.environ\[[\"']VIA_(NET|SCRAPE)_CONSENT", src) and not re.search(r"^\s*(import|from)\s+(VDF_|VRN_|VQG_|VAP_)", src, re.M))
    n = sum(ok)
    print("[計] %s 自測 %d/%d · %s" % (TAG, n, len(ok), "PASS" if n == len(ok) else "FAIL"), flush=True)
    print("[前版] %s 自測(dispatch 還原成前版的)" % PRIOR_PATH.name, flush=True)
    DISPATCH_OWNER.dispatch = _DISPATCH0
    try:
        rc_prior = PRIOR.selftest()
    finally:
        DISPATCH_OWNER.dispatch = dispatch
    print("[計] %s 自測 OK %d · FAIL %d · 前版 rc=%s" % (TAG, n, len(ok) - n, rc_prior), flush=True)
    return 0 if n == len(ok) and rc_prior == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
