#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""CGC_MDL253_ToolingInventory v0106 — 薄尾:自測只驗本版與直接前版 v0105(裁定甲);v0105 ⑪ 往下跑 v0104 鏈的那一步不算進本版

實錄(2026-11-28,交接閘 VCGC 紅列 tooling · engine-params-body · outputs-tools-ast · CCWT v0105):
  v0105 本版 ①–⑩ 全過,紅在 ⑪「暫時拿掉本版補丁跑 v0104 自測」。v0104 ⑧ 用 v0104 自己的掃法(每家只解析尾版那一支),
  要它看到 CGC_MDL237 尾版與 VDF_SSOTSync_v0100.py —— 但 CGC_MDL237 尾版是薄尾、SSOT 字面在前版本體裡(這正是 v0105 修的盲點),
  VDF_SSOTSync 的尾版也早已是 v0104。拔掉 v0105 的修正再跑 v0104,⑧ 必紅:釘著當時的世界,不是功能壞。
  (v0102 ⑤「VRN 工具每一版都有中央編號」原紅在 SUP_MDL866 v0110 未編號;操作員 2026-11-28 裁定 SUP_MDL866 歸 VCGC,已發 VIA-SUP-MDL1212,⑤ 轉綠。)
操作員 2026-11-19 裁定「甲」、2026-11-28「前版鏈比照裁定甲」:尾版自測只驗本版與直接前版。
本版只改自測(v0100 … v0105 一字不動;全景 · 冊查詢 · 引擎參數 · ssot 動詞 · main 照 v0105):
  ① 直接前版 v0105 的 ①–⑩ 在本行程照跑(含真樹 ⑧ CGC_MDL237 尾版看得到 v0100 本體讀的三本冊 · ⑨ 不退步);
     ⑪ 那一步改成「不算進本版」,輸出裡照實改寫成「未跑(裁定甲)」,不印成 PASS。
  ② 前版 v0105 的公開名稱從本版都拿得到(TAILAPI);v0104 的 selftest 跑完已還原。
  ③ 加速器橋在且執行時載到 · 不碰 TA-Lib。只 ast.parse,不執行被讀的檔。
v0104 以前的自測沒有刪,要看仍可各自 --selftest;它們的結果不再算進本版。
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
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL253_ToolingInventory"
TAG = f"{_STEM} v{Path(__file__).stem.rsplit('_v', 1)[-1]}"
SKIPPED = "[計] 裁定甲:v0104 以前的前版鏈不算進本版(未跑)"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)          # v0105 → v0104 → … → v0100
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
V0104 = PRIOR.PRIOR


def __getattr__(name):
    return getattr(PRIOR, name)


def _chain_skipped() -> int:
    print("  " + SKIPPED, flush=True)
    return 0


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ["--selftest"]:
        return selftest()
    return PRIOR.main(argv)


def selftest() -> int:
    keep = V0104.selftest
    V0104.selftest = _chain_skipped
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            rc5 = PRIOR.selftest()                       # v0105 ①–⑩ 照跑;⑪ 呼叫的 v0104 自測換成「未跑」
    finally:
        V0104.selftest = keep
    for ln in buf.getvalue().splitlines():
        if "⑪" in ln:
            ln = "  [略] ⑪ 前版 v0104 自測:不算進本版(裁定甲 · 未跑)"
        elif "[計]" in ln and "前版" in ln and SKIPPED not in ln:
            ln = ln.replace("前版 PASS", "前版 未跑(裁定甲)")
        print(ln, flush=True)
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)[:300]) if note else ''}", flush=True)

    print(f"=== {TAG} · 薄尾自測(裁定甲:本版 + 直接前版 v0105)===", flush=True)
    out = buf.getvalue()
    fails = [ln.strip()[:160] for ln in out.splitlines() if "[FAIL]" in ln]
    chk("① 直接前版 v0105 的 ①–⑩ 全過(含真樹 ⑧ 前版鏈繼承的冊 · ⑨ 不退步)", rc5 == 0 and not fails and SKIPPED in out, fails[:3])
    chk("② v0104 的 selftest 已還原(本版沒改到前版)", V0104.selftest is keep)
    pub = [k for k, v in vars(PRIOR).items() if not k.startswith("_") and callable(v)]
    me_mod = sys.modules.get(__name__)
    chk("③ 前版 v0105 的公開名稱從本版都拿得到(TAILAPI)", bool(pub) and all(hasattr(me_mod, k) for k in pub), len(pub))
    text = Path(__file__).read_text(encoding="utf-8")
    chk("④ 加速器橋在且執行時載到 · 不碰 TA-Lib", "[VIA:ACCEL-BRIDGE" in text and VIA_ACCEL is not None
        and not re.search(r"^\s*(import|from)\s+talib", text, re.M))
    print("  [INFO] v0104 以前的自測不再算進本版(裁定甲);要看仍可各自 --selftest", flush=True)
    good = all(ok)
    print(f"  [計] {TAG} 本版 {sum(ok)}/{len(ok)} · 直接前版 v0105 {'PASS' if rc5 == 0 else 'rc ' + str(rc5)} · 合計 {'PASS' if good else 'FAIL'}", flush=True)
    return 0 if good else 1


if __name__ == "__main__":
    raise SystemExit(main())
