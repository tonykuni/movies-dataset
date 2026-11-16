#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""via_bridge_sweeper v0106 — v0105 薄尾(v0105 一字不動):豁免清單補 VAP 原件收容夾 functional modules/VAP/intake/

緣由(2026-11-16 · 併 main 後 handoff C-bridge-sweeper-v0104 / v0105 紅):活樹量尺報 加速缺 9 · 網路缺 2。逐件查:
  · 加速缺 9 支全在 functional modules/VAP/intake/(VeritasAutoPlot_v4.2_extras_20261113 · VAP_Core_SSOT_Bootstrap_v1)——
    VAP 收進來的外部包原件,正本不就地修改;v0104 已把 supportive modules/intake/ · functional modules/VRN/intake/ 列進
    EXEMPT_INTAKE,VAP 的收容夾漏列(main 2026-11-13 才收進來)。本版只補這一個夾:照樣計數(EXEMPT_INTAKE 數字 +9),不從清單消失。
  · 網路缺 2 支(docs/handoff/ai/VIA_NetFetch_v0100 · VIA_PlaywrightProbe_v0100)是 VCGC 自己的工具 → 已各出 v0101 薄尾補標準網路橋
    (尾版律:v0100 成版史,量尺只看尾版),不靠豁免。
其餘判準、注入、undo 全照 v0105 → v0104 → v0103。只增不減:豁免只加不減;不刪任何橋、不改任何檔。不用 TA-Lib。
自測:① 標準加速器橋 ② 真樹活樹 加速缺 0 · 網路缺 0(VAP 收容 9 支記在 EXEMPT_INTAKE)③ VAP 收容夾的 .py 一支都沒被改(git 乾淨)
      ④ 前版 v0105 自測:只准紅在「真樹活樹」(前版沒有 VAP 豁免)與 v0105 自己的「本版 = 尾版」檢查(有 v0106 後必然成版史)兩件,其他任何紅照實紅。
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

import importlib.util
import os
import re
import subprocess
import sys
from pathlib import Path

STEM = "via_bridge_sweeper"
VERSION = "v0106"
HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
ADDED_EXEMPT_INTAKE = ("functional modules/VAP/intake/",)


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
V0104 = PRIOR.PRIOR                       # v0104(帶 P = v0103 本體 · EXEMPT_INTAKE)
P = V0104.P
P.EXEMPT_INTAKE = tuple(P.EXEMPT_INTAKE) + tuple(x for x in ADDED_EXEMPT_INTAKE if x not in P.EXEMPT_INTAKE)
V0104.EXEMPT_INTAKE = P.EXEMPT_INTAKE
EXEMPT_INTAKE = P.EXEMPT_INTAKE


def __getattr__(name):
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)[:300]) if note and not cond else ""), flush=True)

    print("=== via_bridge_sweeper %s · 薄尾自測(VAP 原件收容夾豁免)===" % VERSION, flush=True)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("① 本檔有標準加速器橋塊", "# ===== [VIA:ACCEL-BRIDGE:v0100]" in src and "import VIA_SuperAccel_Module" in src)
    a = P.audit()
    chk("② 真樹活樹:加速缺 0 · 網路缺 0;VAP 收容照樣計數(EXEMPT_INTAKE %s)" % a["exempt"].get("EXEMPT_INTAKE"),
        not a["accel_miss"] and not a["net_miss"], {"accel": a["accel_miss"][:3], "net": a["net_miss"][:3]})
    st = subprocess.run(["git", "status", "--porcelain", "--", "functional modules/VAP/intake/"], cwd=str(VIA), capture_output=True, text=True)
    chk("③ VAP 收容夾一個位元組都沒動(git 乾淨)", st.returncode == 0 and not st.stdout.strip(), st.stdout[:200])
    cp = subprocess.run([sys.executable, str(PRIOR_PATH), "--selftest"], cwd=str(HERE), capture_output=True, text=True, encoding="utf-8",
                        errors="replace", timeout=900, env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    fails = [ln.strip() for ln in (cp.stdout or "").splitlines() if "[FAIL]" in ln]
    expected = ("真樹活樹",                                  # 前版沒有 VAP 豁免 —— 本版要修的那件
                "③ 正尺掃描:本版 = 已掛(HAS)",                # v0105 自己的「我是尾版」檢查;有了 v0106 它就成版史(EXCLUDED),本來就該這樣
                "前版 via_bridge_sweeper_v0104 自測")          # 上面兩件的連鎖總判
    allowed = [f for f in fails if any(x in f for x in expected) or re.search(r"\[FAIL\] via_bridge_sweeper v010[45] selftest", f)]
    chk("④ 前版 v0105 自測:rc 0,或只紅在「真樹活樹」與「v0105 已不是尾版」兩件預期項(其他任何紅照實紅)",
        cp.returncode == 0 or (fails and len(allowed) == len(fails) and any("真樹活樹" in f for f in fails)), fails[:4])
    n = sum(ok)
    print("[%s] via_bridge_sweeper %s selftest · 本版 %d/%d" % ("PASS" if n == len(ok) else "FAIL", VERSION, n, len(ok)), flush=True)
    return 0 if n == len(ok) else 1


def main() -> int:
    if "--selftest" in sys.argv[1:]:
        return selftest()
    return PRIOR.main()


if __name__ == "__main__":
    sys.exit(main())
