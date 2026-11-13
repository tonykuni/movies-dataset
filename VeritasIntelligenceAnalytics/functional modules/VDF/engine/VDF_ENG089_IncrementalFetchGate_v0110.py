#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
VDF_ENG089_IncrementalFetchGate v0110 — v0109 薄尾(v0109 一字不動):呼叫端設 CATALOG 要落到本體(v0108 的修法,v0109 漏帶)。

實錄(2026-11-13 容器全量重跑 VDF_SystemManager v0171 test):ENG089 v0109 自測過了,卻換 VDF_ENG093_LaunchConsole FAIL ——
  ENG093 照慣例 `g.CATALOG = <指定目錄>` 再叫 `g.plan()`;v0109 只用模組 __getattr__ 轉接前版,
  `g.CATALOG = x` 落在 v0109 自己身上,v0108 的 CATALOG 沒動 → 本體照讀預設目錄(= v0108 修過的同一個坑,v0109 薄尾把它重新挖開)。
本版:自己持有 CATALOG(呼叫端設它就落在這裡);plan() / scan() / catalog_freshness() 每次進來先把它寫到 v0108(v0108 再同步到本體),
  其餘全照 v0109(自測 ⑬′ · audit · 算法一字不動)。零網路 · 零寫庫 · 不用 TA-Lib · 不寫同意閘。
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

import importlib.util
import re
import sys
import tempfile
from pathlib import Path

VERSION = "0110"
HERE = Path(__file__).resolve().parent
_STEM = "VDF_ENG089_IncrementalFetchGate"


def _vnum(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_v0110", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
V0108 = PRIOR.PRIOR                     # 持有 CATALOG 並同步本體的那一版
DEFAULT_CATALOG = V0108.DEFAULT_CATALOG
CATALOG = V0108.CATALOG


def __getattr__(name: str):
    return getattr(PRIOR, name)


def _push() -> None:
    V0108.CATALOG = CATALOG             # 呼叫端設在本版的值 → v0108 → (v0108._sync)本體


def plan(*a, **k):
    _push()
    return V0108.plan(*a, **k)


def scan(*a, **k):
    _push()
    return V0108.scan(*a, **k)


def catalog_freshness(*a, **k):
    _push()
    return V0108.catalog_freshness(*a, **k)


def selftest() -> int:
    global CATALOG
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}", flush=True)

    print(f"=== VDF_ENG089 增量擷取閘 v{VERSION} · 薄尾自測(呼叫端設 CATALOG 要落到本體;其餘照 v0109)===", flush=True)
    g = sys.modules.get(__name__)
    with tempfile.TemporaryDirectory() as td:
        miss = Path(td) / "R49_NO_SUCH_CATALOG.json"
        try:
            if g is not None:
                g.CATALOG = miss               # 跟 ENG093 一樣:設在模組上
            else:
                CATALOG = miss
            r0 = plan("2024-01-01", "2024-01-10", False)
            chk("① 呼叫端在本版設 CATALOG → 本體真的讀那個檔(ABSENT 原因點名它)", r0.get("state") == "ABSENT" and miss.name in str(r0), str(r0.get("why"))[:70])
        finally:
            CATALOG = DEFAULT_CATALOG
            if g is not None:
                g.CATALOG = DEFAULT_CATALOG
        _push()
        V0108._sync()
        chk("② 還原後本體回到預設目錄", V0108.BODY.CATALOG == DEFAULT_CATALOG, V0108.BODY.CATALOG.name)
    rc = PRIOR.selftest()                  # v0109:前版鏈 + ⑬′
    chk("③ v0109 自測(前版鏈 + ⑬′)通過", rc == 0, f"rc {rc}")
    n = sum(ok)
    print(f"  [計] VDF_ENG089 v{VERSION} 薄尾 {n}/{len(ok)} · 合計 {'PASS' if n == len(ok) else 'FAIL'}", flush=True)
    return 0 if n == len(ok) else 1


def main() -> int:
    if "--selftest" in sys.argv[1:]:
        return selftest()
    _push()
    return PRIOR.main()


if __name__ == "__main__":
    sys.exit(main())
