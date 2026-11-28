#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VDF_MDL020_DataPlane v0107 — 薄尾(v0100–v0106 一字不動):自測只驗本版與直接前版 v0106(裁定甲)

實錄(2026-11-28,容器與桌機 vv 都紅):v0106 1/4 —— 紅的全是往下的舊自測:
  · v0106 T2 / T3 子行程跑 v0102 自測,看它「每一行 FAIL 都是舊冊斷言」;v0102 → v0101 那串的 FAIL 行數隨機器狀態變
    (容器 v0101 8/11、桌機 9/11),字樣一對不上就紅。
  · v0104 子行程跑 v0103 自測(v0103 → v0102 → v0101 → v0100),同一串舊自測再紅一次 → v0104 rc 1 → v0105 T1 → v0106 T4。
  · 功能本體 v0104 自己的六檢(parquet align:冊上 22 個輸出 · 起始 2018-01-01 · 欄序 / 型別 / 缺欄對齊 · 正典庫不動)全過。
操作員 2026-11-19 裁定「甲」、2026-11-28「前版鏈比照裁定甲」:尾版自測只驗本版與直接前版。
本版只改自測(parquet status / sync / align / view 與其餘動詞照 v0106):
  ① 直接前版 v0106 的自測在本行程照跑:T1 雙橋 · T4 它的前版 v0105(雙橋)→ 功能本體 v0104 六檢在暫存資料家照跑;
     往下到 v0103 / v0102 的兩個子行程(v0104 的前版自測 · v0106 T2 的 v0102 自測)換成「未跑(裁定甲)」,輸出照實改寫。
  ② v0106 的公開名稱從本版都拿得到(TAILAPI);subprocess.run 已還原、v0104 的已知清單沒被改。
  ③ 加速器 · 網路工具橋在且執行時載到 · 零 TA-Lib · 不設同意閘 · 不含本機路徑。
v0103 以前的自測沒有刪,要看仍可各自 --selftest;它們的結果不再算進本版。
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
FAMILY = "VDF_MDL020_DataPlane"
TAG = "VDF_MDL020_DataPlane v0107"
SKIPPED = "[略] 裁定甲:v0103 以前的前版鏈不算進本版(未跑)"
DEEP = ("VDF_MDL020_DataPlane_v0103.py", "VDF_MDL020_DataPlane_v0102.py")     # 本版不往下跑的兩支
DEEP_CHECKS = ("T2 v0102 歸位", "T3 v0103 那一行")                            # v0106 裡看 v0102 子行程的兩檢


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(str(p)).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(FAMILY + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum)
_spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem + "_for_v0107", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)                                # v0106
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name):  # 尾版律 TAILAPI:前版公開名稱經本檔轉接
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args in (["--selftest"], ["selftest"]):
        return selftest()
    return PRIOR.main(args)


def _deep_selftest(cmd) -> str | None:
    try:
        parts = [str(x) for x in cmd]
    except TypeError:
        return None
    if "--selftest" not in parts:
        return None
    return next((Path(x).name for x in parts if Path(x).name in DEEP), None)


def selftest() -> int:
    real_run = subprocess.run
    stubbed = []

    def run(cmd, *a, **k):
        hit = _deep_selftest(cmd)
        if hit:
            stubbed.append(hit)
            return subprocess.CompletedProcess(cmd, 0, stdout=SKIPPED + "\n", stderr="")
        return real_run(cmd, *a, **k)

    v4 = PRIOR._v0104()
    sigs = tuple(v4.STALE_SIGS) if v4 is not None else None
    buf = io.StringIO()
    subprocess.run = run
    try:
        with contextlib.redirect_stdout(buf):
            PRIOR.selftest()
    finally:
        subprocess.run = real_run
    lines = buf.getvalue().splitlines()
    for ln in lines:
        hit = next((c for c in DEEP_CHECKS if c in ln), None) if "[FAIL]" in ln else None
        if hit:
            ln = "  [略] v0106 " + hit + "…(子行程跑 v0102 自測):不算進本版(裁定甲 · 未跑)"
        elif ln.startswith("[計]") and "v0106 自測" in ln and "FAIL" in ln:
            ln = ln + " · 不過的兩行就是上面未跑的 T2 / T3(裁定甲)"
        elif ln.startswith("[前版]") and "v0103" in ln:
            ln = ln + " —— 未跑(裁定甲)"
        print(ln, flush=True)
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + name + ((" · " + str(note)[:300]) if note and not cond else ""), flush=True)

    print("=== %s · 薄尾自測(裁定甲:本版 + 直接前版 v0106)===" % TAG, flush=True)
    fails = [ln.strip()[:160] for ln in lines if "[FAIL]" in ln]
    other = [ln for ln in fails if not any(c in ln for c in DEEP_CHECKS)]
    want = {"OK] T1 加速器真的載到", "OK] T4 前版 v0105 自測照過", "OK] T1 前版自測照過", "OK] T2 雙橋在", "OK] T3 網路工具惰性載入"}
    seen = {w for w in want if any(w in ln for ln in lines)}
    six = [ln for ln in lines if "VDF_MDL020_DataPlane v0104 自測 OK 6 · FAIL 0 · 前版 rc=0" in ln]
    chk("① 直接前版 v0106:T1 雙橋 · T4 前版 v0105 雙橋三檢 · 功能本體 v0104 六檢全過(往下到 v0103 / v0102 的子行程未跑)",
        not other and seen == want and len(six) == 1 and sorted(set(stubbed)) == sorted(DEEP), (other[:3], sorted(want - seen), stubbed))
    chk("② subprocess.run 已還原 · v0104 的已知清單(STALE_SIGS)沒被改", subprocess.run is real_run
        and (v4 is None or tuple(v4.STALE_SIGS) == sigs))
    pub = [k for k, v in vars(PRIOR).items() if not k.startswith("_") and callable(v)]
    me = sys.modules.get(__name__)
    chk("③ 前版 v0106 的公開名稱從本版都拿得到(TAILAPI)", bool(pub) and all(hasattr(me, k) for k in pub), len(pub))
    src = Path(__file__).read_text(encoding="utf-8")
    chk("④ 加速器 · 網路工具橋在且載到 · 零 TA-Lib · 不設同意閘 · 不含本機路徑", VIA_ACCEL is not None and VIA_NET_TOOL_PATH is not None
        and src.splitlines()[2].startswith("# [VIA:ACCEL-BRIDGE") and not re.search(r"^\s*(import|from)\s+talib", src, re.M)
        and not re.search(r"^\s*os\.environ\[[\"']VIA_(NET|SCRAPE)_CONSENT[\"']\]\s*=", src, re.M) and "C:\\Users\\" + "tonyk" not in src)
    print("  [INFO] v0103 以前的自測不再算進本版(裁定甲);要看仍可各自 --selftest", flush=True)
    good = all(ok)
    print("[計] %s 自測 %d/%d %s" % (TAG, sum(ok), len(ok), "PASS" if good else "FAIL"), flush=True)
    return 0 if good else 1


if __name__ == "__main__":
    raise SystemExit(main())
