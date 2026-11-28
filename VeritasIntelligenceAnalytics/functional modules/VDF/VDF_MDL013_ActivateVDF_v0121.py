#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VDF_MDL013_ActivateVDF v0121 — 薄尾(v0100–v0120 一字不動):容忍舊 ③ 之前,先確認 v0119 自測真的跑完

同一類問題 PR #777 的 Codex P2 指在 MDL004 v0103(已由 v0104 修):前版印完那一行舊失敗之後若崩潰 / 被訊號砍掉,
  只看 [FAIL] 行就會誤判成「只有那一行不過」。v0120 的 T4 也是同一個寫法 —— 本版主動補上。
「跑完」的條件(全部成立才容忍舊 ③):沒逾時 · rc = 1(不是負的訊號碼、不是別的值)· 輸出沒有 Traceback ·
  最後一行是 v0119 自己的總結行「[計] VDF_MDL013_ActivateVDF v0119 前版鏈 rc 1 · FAIL」。
判法掛在 v0120 模組層的 prior_fails,所以 v0120 自己的 T4 也改用這個判法;其餘照 v0120(main 原樣轉交)。
零網路 · 不碰 TA-Lib · 不設同意閘 · 不裝套件。
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
from pathlib import Path

HERE = Path(__file__).resolve().parent
STEM = "VDF_MDL013_ActivateVDF"
TAG = "VDF_MDL013_ActivateVDF v0121"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(STEM + "_prior_for_v0121", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)                 # v0120
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name):  # 尾版律 TAILAPI:前版公開名稱經本檔轉接
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


SUMMARY_RX = re.compile(r"^\[計\] VDF_MDL013_ActivateVDF v0119 前版鏈 rc (-?\d+) · (PASS|FAIL)\s*$")


def completed(rc: int, text: str) -> tuple:
    """(跑完了?, 為什麼不算)。rc 0 = 綠,不必容忍;其餘照條件。"""
    lines = [ln.rstrip() for ln in (text or "").splitlines() if ln.strip()]
    last = lines[-1] if lines else ""
    m = SUMMARY_RX.match(last)
    if rc == 124:
        return False, "逾時"
    if rc < 0:
        return False, f"被訊號結束(rc {rc})"
    if "Traceback (most recent call last)" in (text or ""):
        return False, "輸出有 Traceback(崩了)"
    if not m:
        return False, "最後一行不是 v0119 的總結行(沒跑完)"
    if int(m.group(1)) != rc or (rc == 0) != (m.group(2) == "PASS"):
        return False, "總結行跟 rc 對不上"
    if rc not in (0, 1):
        return False, f"rc {rc} 不是 0 / 1"
    return True, ""


_ORIG_PRIOR_FAILS = PRIOR.prior_fails


def prior_fails() -> tuple:
    env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
    for k in ("VIA_NET_CONSENT", "VIA_SCRAPE_CONSENT"):
        env.pop(k, None)
    try:
        cp = subprocess.run([sys.executable, str(PRIOR.PRIOR_PATH), "--selftest"], capture_output=True, text=True, encoding="utf-8",
                            errors="replace", timeout=1500, stdin=subprocess.DEVNULL, env=env, cwd=str(HERE))
    except subprocess.TimeoutExpired:
        return 124, ["v0119 自測逾時"], []
    text = (cp.stdout or "") + "\n" + (cp.stderr or "")
    fails = [ln.strip() for ln in text.splitlines() if "[FAIL]" in ln or "[NG]" in ln]
    stale = [ln for ln in fails if PRIOR.STALE_SIG in ln]
    wrap = [ln for ln in fails if PRIOR.STALE_SIG not in ln and re.search(r"前版.{0,40}(自測|鏈)", ln)]
    other = [ln for ln in fails if ln not in stale and ln not in wrap]
    done, why = completed(cp.returncode, cp.stdout or "")
    if cp.returncode != 0 and not done:
        other = other + [f"v0119 自測沒跑完:{why}"]
    return cp.returncode, other, stale


PRIOR.prior_fails = prior_fails


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + name + ((" · " + str(note)[:240]) if note and not cond else ""), flush=True)

    print(f"[計] {TAG} 自測開始(本版 3 項 + 前版 {PRIOR_PATH.name} 自測 · 零網路)", flush=True)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("T1 加速器真的載到(VIA_ACCEL is not None)· 第 3 行標記 · 網路橋在 __future__ 之下",
        VIA_ACCEL is not None and src.splitlines()[2] == "# [VIA:ACCEL-BRIDGE:v0111]" and VIA_NET_TOOL_PATH is not None)
    stale = "  [FAIL] ③ 本版:指揮行程認得出 → 不等(1.02 秒)\n"
    tail_fail = "[計] VDF_MDL013_ActivateVDF v0119 前版鏈 rc 1 · FAIL\n"
    cases = {"跑完、只紅舊 ③": (1, stale + tail_fail, True), "印完舊 ③ 就崩": (1, stale + "Traceback (most recent call last):\nRuntimeError: x\n", False),
             "被訊號砍掉": (-9, stale, False), "沒有總結行": (1, stale, False), "總結行 rc 對不上": (1, stale + tail_fail.replace("rc 1", "rc 2"), False),
             "逾時": (124, stale, False), "rc 2": (2, stale + tail_fail.replace("rc 1", "rc 2"), False)}
    got = {k: completed(rc, t)[0] for k, (rc, t, _w) in cases.items()}
    chk("T2 「跑完」判法:合格 1 種過 · 崩 / 訊號 / 沒總結行 / 對不上 / 逾時 / 怪 rc 六種負控都不過",
        all(got[k] == w for k, (_r, _t, w) in cases.items()), got)
    rc = PRIOR.selftest() if callable(getattr(PRIOR, "selftest", None)) else 1
    chk("T3 前版 v0120 自測照過(它的 T4 已改用本版判法)", rc == 0 and PRIOR.prior_fails is prior_fails, rc)
    print(f"[計] {TAG} 自測 {sum(ok)}/{len(ok)} {'PASS' if all(ok) else 'FAIL'}", flush=True)
    return 0 if all(ok) else 1


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ["--selftest"]:
        return selftest()
    return PRIOR.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
