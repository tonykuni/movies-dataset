#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VDF_MDL004_TWFullMarketEngine v0104 — 薄尾(v0100–v0103 一字不動):前版自測要「跑完」才容忍那一行舊 ⓪

PR #776 Codex P2(實測確認):v0103 的 prior_fails() 只看抓到的 [FAIL] 行裡除了舊 ⓪ 沒有別的;
  v0102 子行程若印完 ⓪ 就崩(Traceback)或被訊號砍掉,後面九檢根本沒跑,v0103 仍判 T4 過、自測回 0。
本版只換這一支判法(掛在定義那一層 = v0103 模組層 prior_fails,v0103 自測照跑、讀到本版):
  ① 子行程沒逾時、returncode ≥ 0(不是被訊號砍)、輸出沒有 Traceback;
  ② 看得到 v0102 的總結行「[計] N 檢 OK a · FAIL b」,且 a + b = N;
  ③ b = 0 → rc 必須 0;b = 1 → 那一行必須是舊 ⓪、rc 必須 1;其他一律照實紅。
其餘照 v0103(`__getattr__` 轉接 · --offline-probe · 受治理的 main)。資料不離開本機;零網路;不碰 TA-Lib;不設同意閘。
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
except Exception:  # noqa: BLE001
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
    except Exception:  # noqa: BLE001
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import importlib.util
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
FAMILY = "VDF_MDL004_TWFullMarketEngine"
TAG = "VDF_MDL004_TWFullMarketEngine v0104"
SUMMARY_RX = re.compile(r"\[計\]\s*(\d+)\s*檢\s*OK\s*(\d+)\s*·\s*FAIL\s*(\d+)")


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(FAMILY + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum)
_spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem + "_for_v0104", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)                 # v0103(→ v0102 → v0101 → v0100)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
STALE_SIG = PRIOR.STALE_SIG
_PRIOR_FAILS_V0103 = PRIOR.prior_fails


def __getattr__(name):  # 尾版律 TAILAPI:前版公開名稱經本檔轉接
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def judge(rc: int, out: str) -> tuple:
    """(過?, 原因列)。只有「跑完 · 總結行對得上 · 不過的剛好是舊 ⓪」才過。"""
    why = []
    if rc < 0:
        why.append(f"子行程被訊號砍(rc {rc})")
    if "Traceback (most recent call last)" in out:
        why.append("子行程丟例外(Traceback)")
    m = None
    for m in SUMMARY_RX.finditer(out):
        pass
    if m is None:
        why.append("沒看到總結行(自測沒跑完)")
    fails = [ln.strip() for ln in out.splitlines() if "[FAIL]" in ln]
    other = [ln for ln in fails if STALE_SIG not in ln]
    if other:
        why.extend(other[:3])
    if m is not None:
        n, a, b = (int(x) for x in m.groups())
        if a + b != n:
            why.append(f"總結行對不上(N {n} · OK {a} · FAIL {b})")
        if b == 0 and rc != 0:
            why.append(f"全過卻 rc {rc}")
        if b == 1 and (rc != 1 or len(fails) != 1 or other):
            why.append(f"FAIL 1 但不是只有舊 ⓪(rc {rc} · FAIL 行 {len(fails)})")
        if b > 1:
            why.append(f"FAIL {b}(只容許舊 ⓪ 一行)")
    return (not why), why


def prior_fails(path: Path | None = None) -> tuple:
    """子行程實跑 v0102 自測,照 judge() 判;回 (過?, 原因列)(簽名同 v0103)。"""
    p = path or PRIOR.PRIOR_PATH
    env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
    for k in ("VIA_NET_CONSENT", "VIA_SCRAPE_CONSENT"):
        env.pop(k, None)
    try:
        cp = subprocess.run([sys.executable, str(p), "--selftest"], capture_output=True, text=True, encoding="utf-8",
                            errors="replace", timeout=900, stdin=subprocess.DEVNULL, env=env, cwd=str(Path(p).parent))
    except subprocess.TimeoutExpired:
        return False, [f"{Path(p).name} 自測逾時"]
    return judge(cp.returncode, (cp.stdout or "") + (cp.stderr or ""))


PRIOR.prior_fails = prior_fails                                 # v0103 自測 T4 讀模組層 prior_fails → 用本版判法


def selftest() -> int:
    rc_prior = PRIOR.selftest()                                 # v0103 四檢(T4 已是本版判法)
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + name + ((" · " + str(note)[:240]) if note and not cond else ""), flush=True)

    print(f"[計] {TAG} 薄尾加檢開始(前版自測要跑完才容忍舊 ⓪ · 合成子行程 · 零網路)", flush=True)
    stale = f"  [FAIL] {STALE_SIG}(…)"
    cases = {
        "good": (f"print({stale!r}); print('  [計] 10 檢 OK 9 · FAIL 1'); raise SystemExit(1)", True),
        "crash": (f"print({stale!r}); raise RuntimeError('boom')", False),
        "nosum": (f"print({stale!r}); raise SystemExit(1)", False),
        "signal": (f"import os, signal; print({stale!r}); os.kill(os.getpid(), signal.SIGKILL)", False),
        "other": (f"print({stale!r}); print('  [FAIL] ③ 別的'); print('  [計] 10 檢 OK 8 · FAIL 2'); raise SystemExit(1)", False),
        "allpass": ("print('  [計] 10 檢 OK 10 · FAIL 0')", True),
    }
    got = {}
    with tempfile.TemporaryDirectory(prefix="mdl004_104_") as td:
        for k, (code, _) in cases.items():
            if k == "signal" and os.name == "nt":
                continue
            fp = Path(td) / f"{k}.py"
            fp.write_text(code + "\n", encoding="utf-8")
            got[k] = prior_fails(fp)[0]
    want = {k: v for k, (_, v) in cases.items() if k in got}
    chk("U1 判法:跑完且只有舊 ⓪ → 過;印完 ⓪ 就崩 / 沒總結行 / 被訊號砍 / 有別的紅 → 不過;全過 rc 0 → 過", got == want, (got, want))
    chk("U2 v0103 自測 T4 讀到本版判法(掛在定義那一層)", PRIOR.prior_fails is prior_fails)
    real, why = prior_fails()
    chk("U3 真樹:v0102 子行程跑完 · 只有舊 ⓪ 一行不過", real, why)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("U4 加速器真的載到 · 第 3 行標記 · 網路橋在 · 不碰 TA-Lib",
        VIA_ACCEL is not None and src.splitlines()[2] == "# [VIA:ACCEL-BRIDGE:v0111]" and VIA_NET_TOOL_PATH is not None
        and not re.search(r"^\s*(import|from)\s+talib", src, re.M))
    good = rc_prior == 0 and all(ok)
    print(f"[計] {TAG} 自測 本版 {sum(ok)}/{len(ok)} · 前版 v0103 {'PASS' if rc_prior == 0 else 'FAIL'} · 合計 {'PASS' if good else 'FAIL'}", flush=True)
    return 0 if good else 1


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args:
        return selftest()
    return PRIOR.main(args)


if __name__ == "__main__":
    raise SystemExit(main())
