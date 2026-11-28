#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VDF_MDL022_SafeParallelLaunch v0114 — 薄尾(v0100–v0113 一字不動):自測只驗本版與直接前版 v0113(裁定甲)

桌機 2026-11-28 vv 實錄(VDF_SystemManager vv · 8 支):v0113 自測紅在 ⑥「前版 v0112 自測單獨跑:綠或黃」——
  v0112 13/14,紅在它自己的 ⑦「前版 v0111 自測單獨跑」。容器裡同一條鏈全綠 → 紅的是往下兩層的舊自測吃到主機狀態,
  不是 v0113 的功能(①–⑤ 全在暫存夾造資料:剩餘時間 · 中斷黃框 · 本輪摘要 · 日誌錯誤行 · summary)。
操作員 2026-11-19 裁定「甲」、2026-11-28「前版鏈比照裁定甲」:尾版自測只驗本版與直接前版。
本版只改自測(start / summary / 其餘動詞照 v0113):
  ① 直接前版 v0113 的自測在本行程照跑;它 ⑥ 起子行程跑 v0112 那一步換成「未跑(裁定甲)」,輸出照實改寫,不印成 OK。
  ② v0113 的公開名稱從本版都拿得到(TAILAPI);跑完 subprocess.run 已還原。
  ③ 加速器 · 網路工具橋在且執行時載到 · 不設同意閘 · 不含本機路徑。
v0112 以前的自測沒有刪,要看仍可各自 --selftest;它們的結果不再算進本版。
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
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STEM = "VDF_MDL022_SafeParallelLaunch"
VERSION = "v0114"
TAG = f"{STEM} {VERSION}"
SKIPPED = "[略] 裁定甲:v0112 以前的前版鏈不算進本版(未跑)"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(str(p)).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(f"{STEM}_prior_for_{VERSION}", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)              # v0113
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
GRAND = PRIOR.PRIOR_PATH                                     # v0112(v0113 ⑥ 子行程跑的那支)


def __getattr__(name):  # 尾版律 TAILAPI:前版公開名稱經本檔轉接
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    return PRIOR.main(args)


def _is_grand_selftest(cmd) -> bool:
    try:
        parts = [str(x) for x in cmd]
    except TypeError:
        return False
    return "--selftest" in parts and any(Path(x).name == GRAND.name for x in parts)


def selftest() -> int:
    real_run = subprocess.run
    stubbed = []

    def run(cmd, *a, **k):
        if _is_grand_selftest(cmd):
            stubbed.append(Path(GRAND).name)
            return subprocess.CompletedProcess(cmd, 0, stdout=SKIPPED + "\n", stderr="")
        return real_run(cmd, *a, **k)

    buf = io.StringIO()
    subprocess.run = run
    try:
        with contextlib.redirect_stdout(buf):
            rc13 = PRIOR.selftest()
    finally:
        subprocess.run = real_run
    lines = buf.getvalue().splitlines()
    for ln in lines:
        if "⑥" in ln and "前版 v0112" in ln:
            ln = "  [略] ⑥ 前版 v0112 自測單獨跑:不算進本版(裁定甲 · 未跑)"
        elif ln.startswith("[selftest]") and "v0113" in ln:
            ln = ln + " · 其中 ⑥ 未跑(裁定甲)"
        print(ln, flush=True)
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'NG'}] {name}" + (f" · {str(note)[:300]}" if note and not cond else ""), flush=True)

    print(f"=== {TAG} · 薄尾自測(裁定甲:本版 + 直接前版 v0113)===", flush=True)
    ng = [ln.strip()[:160] for ln in lines if "[NG]" in ln]
    chk("① 直接前版 v0113 的自測全過(加速 · 網路 · ①–⑤ · 檔面;⑥ 的 v0112 子行程換成「未跑」)", rc13 == 0 and not ng and stubbed == [GRAND.name],
        (rc13, ng[:3], stubbed))
    chk("② subprocess.run 已還原(本版沒改到任何前版名稱)", subprocess.run is real_run)
    pub = [k for k, v in vars(PRIOR).items() if not k.startswith("_") and callable(v)]
    me = sys.modules.get(__name__)
    chk("③ 前版 v0113 的公開名稱從本版都拿得到(TAILAPI)", bool(pub) and all(hasattr(me, k) for k in pub), len(pub))
    src = Path(__file__).read_text(encoding="utf-8")
    chk("④ 加速器 · 網路工具橋在且載到 · 零 TA-Lib · 不設同意閘 · 不含本機路徑", VIA_ACCEL is not None and VIA_NET_TOOL_PATH is not None
        and src.splitlines()[2].startswith("# [VIA:ACCEL-BRIDGE") and not re.search(r"^\s*(import|from)\s+talib", src, re.M)
        and not re.search(r"^\s*os\.environ\[[\"']VIA_(NET|SCRAPE)_CONSENT[\"']\]\s*=", src, re.M) and "C:\\Users\\" + "tonyk" not in src)
    print("  [INFO] v0112 以前的自測不再算進本版(裁定甲);要看仍可各自 --selftest", flush=True)
    good = all(ok)
    print(f"[selftest] {TAG} {sum(ok)}/{len(ok)} {'PASS' if good else 'FAIL'} · 直接前版 v0113 {'PASS' if rc13 == 0 else 'rc ' + str(rc13)}", flush=True)
    return 0 if good else 1


if __name__ == "__main__":
    sys.exit(main())
