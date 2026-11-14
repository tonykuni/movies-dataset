#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL247_SSOTPanorama v0101 — 薄尾:他系統的管理器改版後,全景不再整格當掉(讀不到 = NODATA,照實指路)

2026-11-13 / 14 容器實錄:`ssot panorama` 的「註冊@VCGC」是 RED,訊息是
AttributeError: module 'VDF_SystemManager_…' has no attribute 'collect'。
根因:本體 v0100 的 probe_managers 直接呼叫 VDF / VRN 管理器的 collect();VDF 管理器 2026-11-13 重寫成單檔(v0173 起)後
沒有這個名稱。VCGC 對他系統只讀監控(L123):讀不到對方自報,該格應該是 NODATA 並寫明原因,而不是讓整個 probe 丟例外、
連 VCGC 自己那一格都被記成「正主呼叫失敗」的紅(假紅;跟 CGC_MDL245 v0107 / v0108 修的同型)。
本版只換一支 probe_managers(同時換進 PROBES 表):
  管理器不在            → ABSENT(同 v0100)
  沒有 collect()        → NODATA「尾版沒有 collect()」+ 指路(由該系統的管理器補自報介面;VCGC 不代修)
  collect() 丟例外      → NODATA 並帶例外類別與訊息(不吞:寫進格子)
  collect() 正常        → 判法照 v0100(上行七處)
其餘整支照 v0100(含只收 VIA_FROM_VCGC 呼叫的閘)。只讀,不寫冊,不改他系統的檔。
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
        spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        module = _nb_ilu.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import importlib.util
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL247_SSOTPanorama"
ENGINE = Path(__file__).stem


def _vnum(path) -> int:
    m = re.search(r"_v(\d+)$", Path(path).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location("_ssot_panorama_prior_v0101", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
BASE = PRIOR
while "PRIOR" in vars(BASE):
    BASE = vars(BASE)["PRIOR"]
_V0100_PROBE = BASE.probe_managers
MANAGERS = (("VDF", "VDF", "VDF_SystemManager"), ("VRN", "VRN", "VRN_SystemManager"))


def probe_managers(ctx) -> list:
    """同 v0100,但對方沒有 collect() 或 collect() 丟例外時記 NODATA(帶原因),不讓整個 probe 當掉。"""
    out, cell = [], BASE.cell
    for lay, sub, stem in MANAGERS:
        folder = BASE.VIA / "functional modules" / sub
        mgr = (ctx.get("managers") or {}).get(lay)
        if mgr is None:
            mgr = BASE.owner(stem, folder)
        if mgr is None:
            out.append(cell("REG", lay, "ABSENT", f"{stem} 不在", stem))
            continue
        collect = getattr(mgr, "collect", None)
        if not callable(collect):
            out.append(cell("REG", lay, "NODATA", f"{stem} 尾版沒有 collect()(管理器改版後沒有這個自報介面;VCGC 只讀,讀不到 = 無資料)",
                            stem, f"由 {lay} 自己的管理器補上行自報(collect → upstream.seven);VCGC 不代修(L123)"))
            continue
        try:
            up = (collect() or {}).get("upstream") or {}
        except Exception as exc:  # noqa: BLE001 — 對方的錯寫進格子,不吞、也不讓它拖垮別格
            out.append(cell("REG", lay, "NODATA", f"{stem}.collect() 丟例外 {type(exc).__name__}: {str(exc)[:120]}",
                            stem, f"由 {lay} 自己的管理器修;VCGC 不代修(L123)"))
            continue
        seven = up.get("seven") or {}
        miss = [k for k, v in seven.items() if not v]
        out.append(cell("REG", lay, "GREEN" if seven and not miss else ("YELLOW" if seven else "NODATA"),
                        f"上行七處 {up.get('done', 0)}/{len(seven) or 7}" + (f" · 缺 {miss}" if miss else "") + f" · 總管理器 {up.get('via_manager', '?')}",
                        stem + " upstream", "補缺的那一處(spec / grid / register / deck / manager / inventory / handover)" if miss else "", up.get("done")))
    return out


BASE.probe_managers = probe_managers
BASE.PROBES = tuple((n, g, o, probe_managers if f is _V0100_PROBE else f) for n, g, o, f in BASE.PROBES)
BASE.ENGINE = ENGINE


def __getattr__(name: str):
    return getattr(PRIOR, name)


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args:
        return selftest()
    if os.environ.get("VIA_FROM_VCGC") != "YES":        # 同 v0100:只收 VCGC 呼叫(席位檢查認這個閘)
        print(json.dumps({"via": "vcgc", "state": "DENY", "why": "only via-vcgc(via-vcgc ssot panorama)"}, ensure_ascii=False))
        return 2
    return PRIOR.main(args)


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)[:200]) if note and not cond else ''}")

    print(f"=== {ENGINE} · 薄尾自測(他系統管理器讀不到 → NODATA,不當掉)===")

    class NoCollect:
        pass

    class Boom:
        @staticmethod
        def collect():
            raise RuntimeError("壞了")

    class Good:
        @staticmethod
        def collect():
            return {"upstream": {"seven": {k: True for k in "abcdefg"}, "done": 7, "via_manager": "v0001"}}

    class Half:
        @staticmethod
        def collect():
            return {"upstream": {"seven": {"a": True, "b": False}, "done": 1}}

    def states(**mgrs):
        return {c["layer"]: c["state"] for c in probe_managers({"managers": mgrs})}

    try:
        _V0100_PROBE({"managers": {"VDF": NoCollect(), "VRN": Good()}})
        old_raises = False
    except AttributeError:
        old_raises = True
    chk("① 重現根因:本體 v0100 遇沒有 collect() 的管理器會丟 AttributeError", old_raises)
    got = probe_managers({"managers": {"VDF": NoCollect(), "VRN": Good()}})
    chk("② 沒有 collect() → 該層 NODATA 並寫明原因與指路;另一層照常判 GREEN",
        states(VDF=NoCollect(), VRN=Good()) == {"VDF": "NODATA", "VRN": "GREEN"} and "collect()" in got[0]["detail"] and "不代修" in (got[0].get("next") or ""), got)
    b = probe_managers({"managers": {"VDF": Boom(), "VRN": Good()}})
    chk("③ collect() 丟例外 → NODATA,例外類別與訊息寫進格子(不吞)", b[0]["state"] == "NODATA" and "RuntimeError" in b[0]["detail"] and "壞了" in b[0]["detail"], b[0])
    chk("④ 正常回報照 v0100 判:七處齊 GREEN · 有缺 YELLOW", states(VDF=Good(), VRN=Half()) == {"VDF": "GREEN", "VRN": "YELLOW"})
    chk("⑤ 換裝在位:PROBES 表裡的 managers 已是新版,其餘 probe 沒動",
        [f for n, _g, _o, f in BASE.PROBES if n == "managers"] == [probe_managers] and len(BASE.PROBES) == 7
        and all(f is not _V0100_PROBE for _n, _g, _o, f in BASE.PROBES))
    real = probe_managers({})
    chk("⑥ 實樹:VDF / VRN 兩層都有格、都不是丟例外", {c["layer"] for c in real} == {"VDF", "VRN"}, real)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑦ 加速器橋 · 網路橋在;不碰 TA-Lib", "VIA:ACCEL-BRIDGE" in src and "VIA:NET-BRIDGE" in src and not re.search(r"^\s*(import|from)\s+talib", src, re.M))
    print(f"  [{ENGINE}] 薄尾 {sum(ok)}/{len(ok)} {'PASS' if all(ok) else 'FAIL'}")
    rc = PRIOR.selftest()
    return rc if all(ok) else 1


if __name__ == "__main__":
    raise SystemExit(main())
