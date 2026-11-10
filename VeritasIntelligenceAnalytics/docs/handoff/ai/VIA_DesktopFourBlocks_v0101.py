#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""VIA_DesktopFourBlocks v0101 — 薄尾(v0100 一字不動):④ VDF 擷取預設族群改 ALL(操作員 2026-11-10「VRN VDF 應該都該完工了發生甚麼事 · 我現在要抓資料」)。

v0100 的 GROUPS_DEFAULT 寫死 TW_EQUITY,TW_ETF,US_MACRO_FRED,CN_AKSHARE,GLOBAL_INDEX,這五個名字在 VDF_MDL012_FetchGroups 的族群冊裡一個都不存在
(有效:TW_PRICE_VOL / TW_CHIP / TW_MONTHLY_REV / TW_INDEX / TW_ACTIVE_ETF / TW_FIN / INTL_FIN / INTL_DAILY / CN_MACRO / CN_NBS / GLOBAL_MACRO /
SHIPPING / US_MACRO / SENTIMENT)→ ④ 看道 0.2 秒就 KeyError rc 1,真抓永遠沒起跑(2026-11-10 容器實錄)。
本版:預設 ALL(族群由 VDF 自己的冊決定,VCGC 不替 VDF 寫族群名;L123);其他段、參數、收據照 v0100。
自測:前版鏈 v0100(乾淨子行程)+ 本版 3 項。
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
except Exception:  # noqa: BLE001
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

import importlib.util
import os
import subprocess
import sys
from pathlib import Path

VERSION = "v0101"
HERE = Path(__file__).resolve().parent
_PRIOR_FILE = HERE / "VIA_DesktopFourBlocks_v0100.py"
_spec = importlib.util.spec_from_file_location("VIA_DesktopFourBlocks_v0100", _PRIOR_FILE)
P = importlib.util.module_from_spec(_spec)
sys.modules["VIA_DesktopFourBlocks_v0100"] = P
_spec.loader.exec_module(P)

_V0100_GROUPS = P.GROUPS_DEFAULT
P.GROUPS_DEFAULT = "ALL"                 # make_parser() 在呼叫時讀模組全域 → --groups 預設 ALL
P.VERSION = VERSION
P.TAG = "VIA_DesktopFourBlocks " + VERSION
GROUPS_DEFAULT, TAG = P.GROUPS_DEFAULT, P.TAG
VIA = HERE.parents[2]


def selftest() -> int:
    cp = subprocess.run([sys.executable, str(_PRIOR_FILE), "--selftest"], cwd=str(HERE), capture_output=True, text=True, encoding="utf-8", errors="replace",
                        timeout=1800, env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    print("\n".join(l for l in (cp.stdout or "").splitlines() if l.startswith(("[計]", "  [OK]", "  [FAIL]")))[-4000:])
    rc_prior = cp.returncode
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)) if note else ""))
    args = P.make_parser().parse_args(["--blocks", "4", "--dry-only"])
    chk("ⓐ ④ 預設族群 = ALL(v0100 的 %s 不再當預設)" % _V0100_GROUPS, args.groups == "ALL" and P.GROUPS_DEFAULT == "ALL", args.groups)
    mdl012 = P.tail_of(VIA / "functional modules" / "VDF", "VDF_MDL012_FetchGroups_v*.py")
    if mdl012 is None:
        chk("ⓑ 倉內 VDF_MDL012_FetchGroups 尾版看道 ALL rc 0", False, "找不到 FetchGroups 尾版")
        chk("ⓒ v0100 預設族群在 VDF 族群冊確實不存在(回歸證據)", False, "找不到 FetchGroups 尾版")
    else:
        base = [sys.executable, str(mdl012), "run", "--jobs", "5", "--mode", "live", "--dry"]
        good = subprocess.run(base[:3] + ["--groups", "ALL"] + base[3:], cwd=str(mdl012.parent), capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=600)
        chk("ⓑ 倉內 %s 看道 --groups ALL --dry → rc 0 · 列出道 / 族群(只列不抓 · 零網路)" % mdl012.name, good.returncode == 0 and "族群" in good.stdout and "道 " in good.stdout,
            "rc %s" % good.returncode)
        bad = subprocess.run(base[:3] + ["--groups", _V0100_GROUPS] + base[3:], cwd=str(mdl012.parent), capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=600)
        chk("ⓒ v0100 預設族群在 VDF 族群冊不存在 → 同一指令 rc ≠ 0 · KeyError 無此族群(回歸證據:v0100 桌機 ④ 永遠起不了跑)",
            bad.returncode != 0 and "無此族群" in (bad.stdout + bad.stderr), "rc %s" % bad.returncode)
    bad_n = len(ok) - sum(ok)
    print("[%s] %s selftest · 本版 %d/%d · 前版鏈 v0100 %s" % ("PASS" if not bad_n and rc_prior == 0 else "FAIL", TAG, sum(ok), len(ok), "PASS" if rc_prior == 0 else "FAIL"), flush=True)
    return 0 if not bad_n and rc_prior == 0 else 1


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args:
        return selftest()
    return P.main(args)


def __getattr__(name):
    return getattr(P, name)


if __name__ == "__main__":
    sys.exit(main())
