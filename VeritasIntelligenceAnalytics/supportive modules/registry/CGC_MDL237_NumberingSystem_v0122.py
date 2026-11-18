#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""CGC_MDL237_NumberingSystem v0122 — 薄尾(v0121 一字不動):前版鏈的自測拿真候選冊去跑時,候選上限照 1024,不退回 256。

實錄(2026-11-18 VCGC test --quick:本家族尾版自測紅,連三輪):
  [FAIL] ⑤ 真候選冊 × 真存冊 · ValueError: CANDIDATE_LIMIT(v0120 自測)· [FAIL] ⑥c 同(v0119 自測)
根因:v0121 把候選上限 256 → 1024(候選冊是累積冊,現有筆數已超過 256);但 v0121 自測跑前版鏈時「暫時拿掉本版補丁」,
  把上限也一起退回 256。前版自測的 ⑤ / ⑥c 讀的是真的候選冊(不是夾具),真冊筆數超過 256 → 一定被拒 → 尾版自測一定紅。
  發號本身沒壞(正式路徑的上限是 1024);壞的是「跑舊版自測時的上限」。
修法(只改這一件):本版自測呼叫 v0121 自測時,讓它跑前版鏈的那一段維持上限 1024;v0121 其餘的暫卸(引擎名 · 收件補丁 · 新型別)照它原樣。
  上限本身不動(仍是 1024,超過照樣拒);型別、檢測、發號規則全照 v0121;本檔不寫任何檔。
用法同 v0121;自測:python CGC_MDL237_NumberingSystem_v0122.py --selftest(VIA_SKIP_PRIOR_SELFTEST=1 只跑本版項)。
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
_STEM = "CGC_MDL237_NumberingSystem"
ENGINE = _STEM + "_v0122"
LIMIT = 1024


def _vnum_v0122(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


def _load_v0122(path, name: str):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0122(p) < _vnum_v0122(__file__)), key=_vnum_v0122)
PRIOR = _load_v0122(PRIOR_PATH, _STEM + "_prior_for_" + ENGINE)        # v0121:三類新型別 · 上限 1024
BASE = PRIOR.BASE
INTAKE = PRIOR.INTAKE
BASE.ENGINE = ENGINE


def __getattr__(name):
    return getattr(PRIOR, name)


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["--selftest"]:
        return selftest()
    return PRIOR.main(args)


def live_candidates():
    """真候選冊尾版有幾筆(只讀;讀不到回 None)。"""
    books = sorted((p for p in HERE.glob("VIA_AssetCandidates_SSOT_v*.json") if _vnum_v0122(p) >= 0), key=_vnum_v0122)
    if not books:
        return None
    try:
        d = json.loads(books[-1].read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    rows = (d.get("assets") or d.get("candidates")) if isinstance(d, dict) else d
    return len(rows) if isinstance(rows, list) else None


def prior_selftest_with_limit() -> int:
    """跑 v0121 自測;它跑前版鏈(v0120 → …)的那一段,候選上限維持 1024。跑完全部還原。"""
    chain = PRIOR.PRIOR                                  # v0120:v0121 自測裡的 PRIOR.selftest() 就是它
    orig = chain.selftest

    def kept():
        keep = INTAKE.MAX_CANDIDATES
        INTAKE.MAX_CANDIDATES = LIMIT
        try:
            return orig()
        finally:
            INTAKE.MAX_CANDIDATES = keep

    chain.selftest = kept
    BASE.ENGINE = PRIOR.ENGINE                           # v0121 自測會核對引擎名是它自己
    try:
        return PRIOR.selftest()
    finally:
        chain.selftest = orig
        BASE.ENGINE = ENGINE


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)[:200]) if note and not cond else ""), flush=True)

    print("=== %s · 薄尾自測(前版鏈拿真候選冊跑時上限照 1024)===" % ENGINE, flush=True)
    chk("① 前版是 v0121 · 上限 1024 在位(v0114 原值 256)", _vnum_v0122(PRIOR_PATH) == 121 and INTAKE.MAX_CANDIDATES == LIMIT and PRIOR.MAX_CANDIDATES_V0114 == 256, (PRIOR_PATH.name, INTAKE.MAX_CANDIDATES))
    n = live_candidates()
    chk("② 真候選冊筆數讀得到,而且在上限內(超過 256 就是舊上限會拒的原因)", n is not None and n <= LIMIT, n)
    print("  [注] 真候選冊尾版 %s 筆(舊上限 256 · 現行上限 %d)" % ("讀不到" if n is None else n, LIMIT), flush=True)
    capped = False
    try:
        INTAKE.make_plan([{}] * (LIMIT + 1))
    except ValueError as exc:
        capped = "CANDIDATE_LIMIT" in str(exc)
    chk("③ 上限沒有取消:超過 1024 照樣拒 CANDIDATE_LIMIT", capped)
    text = Path(__file__).read_text(encoding="utf-8")
    body = text.split("def live_candidates", 1)[0]
    chk("④ 加速器橋 · 網路橋在 · 不碰 TA-Lib · 本檔不寫任何檔", "[VIA:ACCEL-BRIDGE" in text and "[VIA:NET-BRIDGE" in text
        and not re.search(r"^\s*(import|from)\s+talib", text, re.M) and ".write_text(" not in text.split("def selftest", 1)[0] and "open(" not in body)
    rc_prior = 0
    if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") != "1":
        chain_fn = PRIOR.PRIOR.selftest
        rc_prior = prior_selftest_with_limit()
        chk("⑤ v0121 自測(含前版鏈 v0120 → …)rc 0;跑完引擎名 · 上限 · 前版的 selftest 都還原",
            rc_prior == 0 and BASE.ENGINE == ENGINE and INTAKE.MAX_CANDIDATES == LIMIT and PRIOR.PRIOR.selftest is chain_fn, "rc %s" % rc_prior)
    print("  [計] %s 本版 %d/%d · 前版鏈 %s · 合計 %s" % (ENGINE, sum(ok), len(ok), "PASS" if rc_prior == 0 else "FAIL", "PASS" if all(ok) else "FAIL"), flush=True)
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
