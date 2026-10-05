#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_SystemManager v0130 — 薄尾:refill 動詞 = 無資料族群補擷取(FRED → 政府單位 → AkShare)由 VDF System Manager 控管

操作員 2026-10-05:「FOR THOSE NO DATA USE FRED KEY AND OTHER GOVERNMENT UNIT AND AKSHARE TO FETCH」。
refill [--home 資料庫夾] [--groups X,Y] [--as-of D] [--apply] [--timeout S]
  交 VDF 自己的 MDL012 尾版 refill(路線在族群冊 refill 分層;沒 --apply = 只列計畫;--apply 要本視窗雙閘)。
  在本行程呼叫(不另起 python、不經 VCGC 也能跑);其餘動詞照 v0129。
同意閘(VIA_NET_CONSENT / VIA_SCRAPE_CONSENT)與 FRED_API_KEY 是操作員的手,本版不讀值、不寫。不碰 TA-Lib。
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

# ===== [VIA:LIB-BRIDGE:v0100] 三庫正典橋(批597;缺席大聲拋,不 graceful) =====
import sys as _lb_sys
from pathlib import Path as _lb_Path
_lb_p = _lb_Path(__file__).resolve()
while _lb_p.parent != _lb_p:
    if (_lb_p / "supportive modules").is_dir():
        _lb_sys.path.insert(0, str(_lb_p / "supportive modules"))
        break
    _lb_p = _lb_p.parent
import VIA_LibCanon as _LIB          # 正典缺席=大聲拋,不假裝有(LL151)
# ===== [VIA:LIB-BRIDGE:END] =====

import contextlib
import importlib.util
import io
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_SystemManager"
TAG = f"{_STEM} v{Path(__file__).stem.rsplit('_v', 1)[-1]}"
ENTRY_VDFSM = "VIA_FROM_VDFSM"


def _vnum_v0130(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0130(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0130(p) < _vnum_v0130(__file__)), key=_vnum_v0130)
PRIOR = _load_v0130(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)
VERBS_v0130 = tuple(PRIOR.VERBS_v0129) + ("refill",)


def __getattr__(name):
    return getattr(PRIOR, name)


def refill(rest: list) -> int:
    m = PRIOR.mdl012()
    if m is None:
        print(f"[ABSENT] {TAG}:VDF_MDL012_FetchGroups_v*.py 不在這棵樹")
        return 3
    if not hasattr(m, "cmd_refill"):
        print(f"[ABSENT] {TAG}:MDL012 尾版沒有 refill 動詞(要 v0104 以上)")
        return 3
    print(f"=== VDF 無資料族群補擷取(VDF System Manager 總控 · {TAG})===", flush=True)
    rc, _ = PRIOR.call(m, ["refill"] + list(rest))
    return rc


def main(argv=None) -> int:
    """refill 由本版接;其餘動詞照 v0129(activate · 總控標記 · 未知動詞拒跑)。"""
    args = list(sys.argv[1:] if argv is None else argv)
    if args[:1] != ["refill"]:
        return PRIOR.main(args)
    had_vc, keep_vc = "VIA_FROM_VCGC" in os.environ, os.environ.get("VIA_FROM_VCGC")
    had_sm, keep_sm = ENTRY_VDFSM in os.environ, os.environ.get(ENTRY_VDFSM)
    os.environ[ENTRY_VDFSM] = "YES"
    os.environ["VIA_FROM_VCGC"] = "YES"
    try:
        return refill(args[1:])
    finally:
        for k, had, keep in (("VIA_FROM_VCGC", had_vc, keep_vc), (ENTRY_VDFSM, had_sm, keep_sm)):
            if had:
                os.environ[k] = keep
            else:
                os.environ.pop(k, None)


def selftest() -> int:
    prior_rc = PRIOR.selftest()
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)[:300]) if note and not cond else ''}")

    print(f"=== {TAG} · 薄尾自測(refill:無資料族群補擷取)===")
    import shutil
    import tempfile
    tmp = Path(tempfile.mkdtemp(prefix="vdfsm130_"))
    saved = {k: os.environ.pop(k, None) for k in ("VIA_FROM_VCGC", ENTRY_VDFSM, "VIA_NET_CONSENT", "VIA_SCRAPE_CONSENT")}
    try:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc_plan = main(["refill", "--home", str(tmp / "mega"), "--groups", "US_MACRO,CN_NBS"])
            rc_gated = main(["refill", "--home", str(tmp / "mega"), "--groups", "US_MACRO", "--apply"])
            rc_bad = main(["refill", "--nope"])
        out = buf.getvalue()
        left = [k for k in ("VIA_FROM_VCGC", ENTRY_VDFSM) if k in os.environ]
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        wrote = (tmp / "_reports").exists()
        shutil.rmtree(tmp, ignore_errors=True)
    chk("① refill 交 MDL012 尾版:沒 --apply = 只列計畫 rc 0(兩族群都在 · 分層都列)",
        rc_plan == 0 and "只列計畫" in out and "US_MACRO" in out and "CN_NBS" in out and "FRED" in out and "AKSHARE" in out, out[-300:])
    chk("② --apply 沒開雙閘 = GATED rc 4、零寫檔(本版不代設同意閘)", rc_gated == 4 and "GATED" in out and not wrote, rc_gated)
    chk("③ 參數錯照 argparse 拒(rc 2);結束環境還原", rc_bad == 2 and not left, (rc_bad, left))
    text = Path(__file__).read_text(encoding="utf-8")
    chk("④ refill 進動詞表;加速器橋 · 網路工具橋 · 正典橋在;不碰 TA-Lib;不寫同意閘 / 不讀 FRED 鑰",
        "refill" in VERBS_v0130 and "[VIA:ACCEL-BRIDGE" in text and "[VIA:NET-BRIDGE" in text and "[VIA:LIB-BRIDGE" in text
        and not re.search(r"^\s*(import|from)\s+talib", text, re.M) and not re.search(r"environ\[[\"']VIA_(NET|SCRAPE)_CONSENT", text)
        and "FRED_API_KEY\"]" not in text and "getenv(\"FRED" not in text)
    print(f"  [計] {TAG} 本版 {sum(ok)}/{len(ok)} · 前版 {'PASS' if prior_rc == 0 else 'FAIL'} · 合計 {'PASS' if all(ok) and prior_rc == 0 else 'FAIL'}")
    return 0 if all(ok) and prior_rc == 0 else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if sys.argv[1:] == ["--selftest"] else main())
