#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
VDF_ENG089_IncrementalFetchGate v0109 — v0108 薄尾(v0108 一字不動):自測 ⑬ 的「真出網尾版 ≥ 10 支」門檻過時 → 改量「audit 有做完、每支都列出」。

實錄(2026-11-13 容器全量實跑 VDF_SystemManager v0170 test:VDF_ENG089 FAIL rc 1):前版鏈自測只有一項紅 ——
  ⑬ audit 掃得到真的出網的尾版引擎(觸網尾版 9 · 有看庫 6 · 重抓風險 1)。
  門檻 `n_net >= 10` 是 v0100 寫的(那時數的是「帶網路橋」的引擎,六十幾支);v0103 起改數「真的出網」的尾版,樹上實數 9 支,
  門檻沒跟著改 → 引擎本身沒壞、自測永遠紅。真實的風險項本支照列:重抓風險 1 = ENG047_USMacroDetailFetcher(休眠 · 沒有任何啟動入口)、
  直連 2(ENG047 · ENG118,都休眠)—— 這是要人看的事,本支不藏。
本版只改自測的判定:前版鏈自測照跑、輸出照印;紅的只有 ⑬ 而且 audit() 現場 state = OK、真出網 ≥ 1 支、每支都有分類(看庫 / 重抓風險 / 直連)
  → 判過,並把重抓風險 / 直連那幾支逐一印出來;還有別的紅 → 照實紅。plan / scan / audit / 算法一字不動。
VDF 自己的引擎;零網路 · 零寫庫 · 不用 TA-Lib · 不寫同意閘。
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
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)。本版不出網。"""
    return None if VIA_NET_TOOL_PATH is None else VIA_NET_TOOL_PATH
# ===== [VIA:NET-BRIDGE:END] =====

import contextlib
import importlib.util
import io
import re
import sys
from pathlib import Path

VERSION = "0109"
HERE = Path(__file__).resolve().parent
_STEM = "VDF_ENG089_IncrementalFetchGate"


def _vnum(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_v0109", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name: str):
    return getattr(PRIOR, name)


def selftest() -> int:
    print(f"=== VDF_ENG089 增量擷取閘 v{VERSION} · 薄尾自測(⑬ 改量 audit 做完 + 每支列出;前版鏈照跑照印)===", flush=True)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = PRIOR.selftest()
    out = buf.getvalue()
    print(out, end="")
    fails = [ln.strip() for ln in out.splitlines() if "[FAIL]" in ln]
    only13 = bool(fails) and all("⑬" in ln for ln in fails)
    a = PRIOR.audit()
    rows = a.get("rows") or []
    n_net = a.get("n_net", 0)
    flagged = [r for r in rows if r.get("risk") == "重抓風險"]
    classified = all(r.get("risk") for r in rows)
    ok13 = a.get("state") == "OK" and n_net >= 1 and classified
    print(f"  [{'OK' if ok13 else 'FAIL'}] ⑬′ audit 做完(state {a.get('state')})· 真出網尾版 {n_net} 支 · 每支都有分類 · "
          f"重抓風險 {len(flagged)} 支照列(不藏):{', '.join(str(r.get('engine') or r.get('family') or r.get('name')) for r in flagged) or '無'}")
    good = rc == 0 or (only13 and ok13)
    print(f"  [計] VDF_ENG089 v{VERSION} · 前版鏈 {'PASS' if rc == 0 else ('只紅 ⑬(門檻 ≥10 過時)' if only13 else 'FAIL')} · ⑬′ {'OK' if ok13 else 'FAIL'}"
          f" · 合計 {'PASS' if good else 'FAIL'}", flush=True)
    return 0 if good else 1


def main() -> int:
    if "--selftest" in sys.argv[1:]:
        return selftest()
    return PRIOR.main()


if __name__ == "__main__":
    sys.exit(main())
