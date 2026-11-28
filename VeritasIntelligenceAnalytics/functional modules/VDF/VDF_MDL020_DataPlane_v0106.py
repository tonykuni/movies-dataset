#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VDF_MDL020_DataPlane v0106 — 薄尾(v0100–v0105 一字不動):v0102 歸位後,它釘舊冊的自測行照 v0104 的規矩算「已知」

2026-11-27 VDF 收尾實錄:
  · VCGC 11-23 退役批(prune_20261123_144317)把 v0102 搬進隔離區;但 v0103 以 glob 取前版,設計上就站在 v0102 上
    (v0103 L112「V2 = 前版(v0102;它的 V1 = v0101,P = v0100)」)→ 鏈被改成 v0103 → v0101。違反「仍被薄尾引用的舊模組不搬走」。
  · 本日以 CGC_MDL276 restore 把 v0102 從隔離區複製回原位(sha256 核過),鏈回到 v0105 → v0104 → v0103 → v0102 → v0101 → v0100。
  · 歸位後 v0102 自身自測 2/6:不過的四行全是「冊 v0102 的舊內容」(5 群 · 21 個輸出 · 價量群 2022 起 · 輸入 7 + 輸出 21)
    與 v0101 已知那一行 —— 操作員 2026-11-22 / 11-24 已定「2018 起」、冊尾版 22 個輸出,舊斷言本來就該過時;
    v0104 自己的六檢(冊上 22 個輸出 · 起始 2018-01-01 · 對齊)在 v0102 歸位後照樣全過 → 行為正確,只是前版自測釘舊冊。
本版只做一件事:把「v0103 ① 前版 0102 自測…」這一行加進 v0104 的 STALE_SIGS(已知 · 前版釘舊冊),
  但先在子行程實跑 v0102 自測,確認它的每一行 FAIL 都是舊冊斷言;有任何一行不是 → 不加,照實紅。
其餘一切照 v0105(雙橋 · `__getattr__` 轉接 · main 轉前版)。資料不離開本機;零網路;不碰 TA-Lib;不設同意閘。
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

# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(VDF 全導入令;惰性載入=import 時零網路、零行為變更) =====
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
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT;網路只認 AegisNexus);缺席回 None(誠實)"""
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
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FAMILY = "VDF_MDL020_DataPlane"
TAG = "VDF_MDL020_DataPlane v0106"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(FAMILY + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum)
_spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem + "_for_v0106", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name):
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def _v0104():
    """沿鏈找自己定義 STALE_SIGS 的那一版(v0104)。"""
    m = PRIOR
    while m is not None:
        if "STALE_SIGS" in vars(m) and "align_rows" in vars(m):
            return m
        m = vars(m).get("PRIOR")
    return None


V0102_LINE_SIG = "前版 0102 自測在隔離下照過(VDF_MDL020_DataPlane v0102 自測"
OLD_BOOK_SIGS = ("冊 v0102:5 群", "價量群 2022-01-01 起", "輸入 7 + 輸出 21", "v0101 自測照過(VDF_MDL020_DataPlane v0101 自測 9/11")


def v0102_fails_are_old_book(path: Path | None = None) -> tuple[bool, list]:
    """子行程實跑 v0102 自測:每一行 FAIL 都是舊冊斷言才回 True(照實:跑不起來 / 有別的紅 → False)。"""
    p = path or (HERE / "VDF_MDL020_DataPlane_v0102.py")
    if not p.is_file():
        return False, ["v0102 不在原位"]
    env = dict(os.environ, VIA_FROM_VDFSM="YES", PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
    for k in ("VIA_NET_CONSENT", "VIA_SCRAPE_CONSENT"):
        env.pop(k, None)
    cp = subprocess.run([sys.executable, str(p), "--selftest"], capture_output=True, text=True, encoding="utf-8", errors="replace",
                        timeout=1800, stdin=subprocess.DEVNULL, env=env, cwd=str(HERE))
    fails = [ln.strip() for ln in (cp.stdout + cp.stderr).splitlines() if "[FAIL]" in ln]
    other = [ln for ln in fails if not any(s in ln for s in OLD_BOOK_SIGS)]
    return bool(fails) and not other, other


def install_known() -> bool:
    m = _v0104()
    if m is None:
        return False
    ok, _other = v0102_fails_are_old_book()
    if ok and V0102_LINE_SIG not in m.STALE_SIGS:
        m.STALE_SIGS = tuple(m.STALE_SIGS) + (V0102_LINE_SIG,)
    return ok


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + name + ((" · " + str(note)[:240]) if note and not cond else ""), flush=True)

    print("[計] %s 自測開始(本版 4 項 + 前版 %s 自測 · 零網路)" % (TAG, PRIOR_PATH.name), flush=True)
    chk("T1 加速器真的載到(VIA_ACCEL is not None)· 第 3 行標記 · 雙橋在 __future__ 之下",
        VIA_ACCEL is not None and Path(__file__).read_text(encoding="utf-8").splitlines()[2] == "# [VIA:ACCEL-BRIDGE:v0111]"
        and VIA_NET_TOOL_PATH is not None)
    good, other = v0102_fails_are_old_book()
    chk("T2 v0102 歸位且它的每一行 FAIL 都是舊冊斷言(5 群 · 21 輸出 · 2022 起 · v0101 已知)", good, other[:2])
    known = install_known()
    m = _v0104()
    chk("T3 v0103 那一行已併入 v0104 的已知清單(只在 T2 成立時)", known and m is not None and V0102_LINE_SIG in m.STALE_SIGS)
    rc = PRIOR.selftest() if callable(getattr(PRIOR, "selftest", None)) else 1
    chk("T4 前版 v0105 自測照過(含 v0104 六檢 · 雙橋)", rc == 0, rc)
    print("[計] %s 自測 %d/%d %s" % (TAG, sum(ok), len(ok), "PASS" if all(ok) else "FAIL"), flush=True)
    return 0 if all(ok) else 1


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args in (["--selftest"], ["selftest"]):
        return selftest()
    return PRIOR.main(args) if callable(getattr(PRIOR, "main", None)) else 2


if __name__ == "__main__":
    raise SystemExit(main())
