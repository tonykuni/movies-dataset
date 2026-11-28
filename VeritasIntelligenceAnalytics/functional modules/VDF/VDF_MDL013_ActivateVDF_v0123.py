#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VDF_MDL013_ActivateVDF v0123 — 薄尾(v0100–v0122 一字不動):自測只驗本版與直接前版 v0122(裁定甲)

桌機 2026-11-28 vv 實錄:MDL013 紅在往下的前版鏈 —— v0121「T3 前版 v0120 自測照過」→ v0120「T4 v0119 自測」
  → v0119 鏈裡 v0112 的「Ⓛ 測試庫整段」在主機上 V1「回原表逐筆」不符 16265 筆(容器同一夾具 0 筆:那一檢在主機讀到夾具以外的表,
  是 v0112 自測的隔離問題,要主機證據另案查)。v0122 自己的 T1 雙橋 · T2 指揮行程排隊門檻(0.9 秒)兩檢不吃本機狀態。
操作員 2026-11-19 裁定「甲」、2026-11-28「前版鏈比照裁定甲」:尾版自測只驗本版與直接前版。
本版只改自測(其餘動詞照 v0122):
  ① 直接前版 v0122 的自測在本行程照跑(T1 雙橋 · T2 排隊門檻);它往下跑 v0121 鏈那一步換成「未跑(裁定甲)」,輸出照實寫,不印成 PASS。
  ② v0122 的公開名稱從本版都拿得到(TAILAPI);v0121 的 selftest 跑完已還原。
  ③ 加速器 · 網路工具橋在且執行時載到 · 零 TA-Lib · 不設同意閘 · 不含本機路徑。
v0121 以前的自測沒有刪,要看仍可各自 --selftest;它們的結果不再算進本版。
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
# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 VDF 全導入令;graceful 零行為變更) =====
VIA_NET_TOOL_PATH = None
try:
    from pathlib import Path as _nb_Path
    _nb_p = _nb_Path(__file__).resolve()
    while _nb_p.parent != _nb_p:
        _nb_dir = _nb_p / "supportive modules" / "network"
        if _nb_dir.exists():
            _nb_hits = sorted(_nb_dir.glob("via_net_unified_v*.py"))
            if _nb_hits:
                VIA_NET_TOOL_PATH = str(_nb_hits[-1])
            break
        _nb_p = _nb_p.parent
except Exception:
    VIA_NET_TOOL_PATH = None


def _via_net():
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        _nb_spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        _nb_mod = _nb_ilu.module_from_spec(_nb_spec)
        _nb_spec.loader.exec_module(_nb_mod)
        return _nb_mod
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import contextlib
import importlib.util
import io
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STEM = "VDF_MDL013_ActivateVDF"
VERSION = "v0123"
TAG = f"{STEM} {VERSION}"
SKIPPED = "[略] 裁定甲:v0121 以前的前版鏈不算進本版(未跑)"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(str(p)).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(f"{STEM}_prior_for_{VERSION}", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)              # v0122
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
GRAND = PRIOR.PRIOR                                          # v0121(直接前版往下跑的那一層)
_SKIP_CALLS = []


def __getattr__(name):  # 尾版律 TAILAPI:前版公開名稱經本檔轉接
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    return PRIOR.main(args)


def _chain_skipped() -> int:
    _SKIP_CALLS.append(1)
    print("  " + SKIPPED, flush=True)
    return 0


def selftest() -> int:
    keep = GRAND.selftest
    _SKIP_CALLS.clear()
    GRAND.selftest = _chain_skipped
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            rc_p = PRIOR.selftest()
    finally:
        GRAND.selftest = keep
    lines = buf.getvalue().splitlines()
    for ln in lines:
        if ln.startswith("[計]") and "v0122" in ln and ("PASS" in ln or "FAIL" in ln):
            ln = ln + " · 其中往下的 v0121 鏈未跑(裁定甲)"
        print(ln, flush=True)
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + name + ((" · " + str(note)[:300]) if note and not cond else ""), flush=True)

    print(f"=== {TAG} · 薄尾自測(裁定甲:本版 + 直接前版 v0122)===", flush=True)
    fails = [ln.strip()[:160] for ln in lines if "[FAIL]" in ln]
    chk("① 直接前版 v0122 的自測全過(T1 雙橋 · T2 排隊門檻;往下的 v0121 鏈換成「未跑」)", rc_p == 0 and not fails and _SKIP_CALLS == [1],
        (rc_p, fails[:3], len(_SKIP_CALLS)))
    chk("② v0121 的 selftest 已還原(本版沒改到前版)", GRAND.selftest is keep)
    pub = [k for k, v in vars(PRIOR).items() if not k.startswith("_") and callable(v)]
    me = sys.modules.get(__name__)
    chk("③ 前版 v0122 的公開名稱從本版都拿得到(TAILAPI)", bool(pub) and all(hasattr(me, k) for k in pub), len(pub))
    src = Path(__file__).read_text(encoding="utf-8")
    chk("④ 加速器 · 網路工具橋在且載到 · 零 TA-Lib · 不設同意閘 · 不含本機路徑", VIA_ACCEL is not None and VIA_NET_TOOL_PATH is not None
        and src.splitlines()[2].startswith("# [VIA:ACCEL-BRIDGE") and not re.search(r"^\s*(import|from)\s+talib", src, re.M)
        and not re.search(r"^\s*os\.environ\[[\"']VIA_(NET|SCRAPE)_CONSENT[\"']\]\s*=", src, re.M) and "C:\\Users\\" + "tonyk" not in src)
    print("  [INFO] v0121 以前的自測不再算進本版(裁定甲);要看仍可各自 --selftest", flush=True)
    good = all(ok)
    print(f"[計] {TAG} 自測 {sum(ok)}/{len(ok)} {'PASS' if good else 'FAIL'} · 直接前版 v0122 {'PASS' if rc_p == 0 else 'rc ' + str(rc_p)}", flush=True)
    return 0 if good else 1


if __name__ == "__main__":
    raise SystemExit(main())
