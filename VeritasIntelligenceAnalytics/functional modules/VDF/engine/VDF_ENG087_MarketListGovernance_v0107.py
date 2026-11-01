#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_ENG087 v0107 — thin tail: STOCK_CODE / ACTIVE_ETF_CODE written with [0-9] (= VDF_InputUniverse_SSOT v0104).

v0100 … v0106 stay (L04). Operator 2026-11-01:「正則兩條照你說的改」. The input-universe book v0104 rewrote
IN-01 / IN-02 code_regex from \\d to [0-9] (VCGC's central regex contract only proves [0-9], and needs examples), and
`VDF_SystemManager universe check` compares the book's code_regex with this engine's patterns character by character, so the
engine moves in the same step:
    STOCK_CODE      ^[1-9]\\d{3}$  →  ^[1-9][0-9]{3}$
    ACTIVE_ETF_CODE ^00\\d{3}A$    →  ^00[0-9]{3}A$
Same result for every ASCII code; non-ASCII digits (e.g. full-width ２３３０) no longer count as a code.
The new patterns are put into v0105's module globals (where load_stock_list / the list builders read them), so every
v0105 / v0106 verb uses them; everything else forwards to v0106 via __getattr__.
Runs only through VCGC (VIA_FROM_VCGC=YES) except `--selftest` (offline, deterministic). Zero network; read-only on DBs.
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

import importlib.util
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VDF = HERE.parent
STEM = "VDF_ENG087_MarketListGovernance"
TAG = "VDF_ENG087 v" + Path(__file__).stem.rsplit("_v", 1)[-1]
BOOK_GLOB = "VDF_InputUniverse_SSOT_v[0-9][0-9][0-9][0-9].json"


def _vnum(p: Path) -> int:
    m = re.search(r"_v(\d{4})\.(?:py|json)$", Path(p).name)
    return int(m.group(1)) if m else -1


_PRIOR_PATH = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum)
_SPEC = importlib.util.spec_from_file_location("eng087_prior_of_" + Path(__file__).stem, _PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = PRIOR
_SPEC.loader.exec_module(PRIOR)

STOCK_CODE = re.compile(r"^[1-9][0-9]{3}$")          # = VDF_InputUniverse_SSOT v0104 IN-01 code_regex
ACTIVE_ETF_CODE = re.compile(r"^00[0-9]{3}A$")       # = VDF_InputUniverse_SSOT v0104 IN-02 code_regex
_OWNER = PRIOR.load_stock_list.__globals__            # v0105 本體全域(清單函式在這裡讀 STOCK_CODE / ACTIVE_ETF_CODE)
_ORIG = {k: _OWNER[k] for k in ("STOCK_CODE", "ACTIVE_ETF_CODE")}


def _patch() -> None:
    _OWNER["STOCK_CODE"], _OWNER["ACTIVE_ETF_CODE"] = STOCK_CODE, ACTIVE_ETF_CODE


def _unpatch() -> None:
    _OWNER.update(_ORIG)


_patch()


def __getattr__(name: str):
    """PEP 562:v0106(以及其後轉的 v0105 …)公開面照舊可叫。"""
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def book_tail() -> Path | None:
    hits = sorted(VDF.glob(BOOK_GLOB), key=_vnum)
    return hits[-1] if hits else None


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] == ["--selftest"]:
        return selftest()
    _patch()
    return PRIOR.main(a)


def selftest() -> int:
    p = f = 0

    def chk(name, cond, note=""):
        nonlocal p, f
        if cond:
            p += 1
            print("  [OK] %s" % name)
        else:
            f += 1
            print("  [FAIL] %s%s" % (name, (" · " + str(note)[:300]) if note else ""))

    print("=== %s · 薄尾自測(代號正則改寫成 [0-9] · 與範圍冊逐字一致)===" % TAG)
    bp = book_tail()
    ins = {i.get("id"): i for i in (json.loads(bp.read_text(encoding="utf-8")).get("inputs") or [])} if bp else {}
    chk("① 與範圍冊尾版逐字一致(%s):IN-01 = STOCK_CODE · IN-02 = ACTIVE_ETF_CODE" % (bp.name if bp else "無冊"),
        ins.get("IN-01", {}).get("code_regex") == STOCK_CODE.pattern and ins.get("IN-02", {}).get("code_regex") == ACTIVE_ETF_CODE.pattern,
        {k: v.get("code_regex") for k, v in ins.items()})
    old_s, old_e = re.compile(_ORIG["STOCK_CODE"].pattern), re.compile(_ORIG["ACTIVE_ETF_CODE"].pattern)
    samples = ["2330", "1101", "9958", "0050", "91234", "233", "2330.TW", "00981A", "00980A", "00980D", "0098A", "009810A", "00981a"]
    same = all(bool(STOCK_CODE.fullmatch(x)) == bool(old_s.fullmatch(x)) and bool(ACTIVE_ETF_CODE.fullmatch(x)) == bool(old_e.fullmatch(x)) for x in samples)
    chk("② ASCII 代號結果和 v0105 舊式一模一樣(%d 個樣本)· 全形數字不再算代號(２３３０ · ００９８１Ａ)" % len(samples),
        same and not STOCK_CODE.fullmatch("２３３０") and old_s.fullmatch("2３３０") and not ACTIVE_ETF_CODE.fullmatch("00９８１A"))
    chk("③ 冊上正反例全對(IN-01 正 %s / 反 %s · IN-02 正 %s / 反 %s)" % (ins.get("IN-01", {}).get("code_regex_positive"), ins.get("IN-01", {}).get("code_regex_negative"),
                                                                ins.get("IN-02", {}).get("code_regex_positive"), ins.get("IN-02", {}).get("code_regex_negative")),
        all(STOCK_CODE.fullmatch(x) for x in ins.get("IN-01", {}).get("code_regex_positive") or ["x"])
        and not any(STOCK_CODE.fullmatch(x) for x in ins.get("IN-01", {}).get("code_regex_negative") or [])
        and all(ACTIVE_ETF_CODE.fullmatch(x) for x in ins.get("IN-02", {}).get("code_regex_positive") or ["x"])
        and not any(ACTIVE_ETF_CODE.fullmatch(x) for x in ins.get("IN-02", {}).get("code_regex_negative") or []))
    chk("④ 換裝在位:v0105 本體全域用新式(清單函式讀到的就是本版)· 尾版公開面 STOCK_CODE / ACTIVE_ETF_CODE = 新式 · 其餘照轉(load_stock_list 可叫)",
        _OWNER["STOCK_CODE"] is STOCK_CODE and _OWNER["ACTIVE_ETF_CODE"] is ACTIVE_ETF_CODE and callable(getattr(sys.modules[__name__], "load_stock_list", None)))
    src = Path(__file__).read_text(encoding="utf-8")
    body = src.split("def selftest", 1)[0]
    chk("⑤ VDF 獨立:不匯入他系統程式 · 兩座橋在 · 零網路 · 同意閘不讀不寫 · 不碰 TA-Lib",
        not re.search(r"^\s*(import|from)\s+(CGC_|VRN_|VCGC|requests|httpx|urllib\.request)", src, re.M) and "VIA:ACCEL-BRIDGE" in src and "VIA:NET-BRIDGE" in src
        and "CONSENT\"] =" not in body and "talib" not in body.lower())
    if f:
        print("[計] %s 本版 %d/%d · FAIL" % (TAG, p, p + f))
        return 1
    print("[計] %s 本版 %d/%d · PASS" % (TAG, p, p + f))
    if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1":
        return 0
    _unpatch()
    try:
        rc = PRIOR.selftest()
    finally:
        _patch()
    print("[計] %s 前版鏈 rc %s · %s" % (TAG, rc, "PASS" if rc == 0 else "FAIL"))
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
