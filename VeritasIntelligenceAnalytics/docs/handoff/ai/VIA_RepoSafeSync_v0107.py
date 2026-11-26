#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VIA_RepoSafeSync v0107 — 薄尾(v0100–v0106 一字不動):收據與畫面的 tool 寫實際跑的尾版

PR #740 Codex(P3):v0106 的 main 交給 v0105 的 main,v0105 又把 BASE.TAG 設成它自己的「v0105」→
`--apply` 寫的 REPO_SYNC_latest.json 與結果摘要都寫 v0105,分不出跑的是有進度條 / 中斷處理的 v0106 還是真的 v0105。
本版:交棒前把 v0105 與 v0106 模組的 TAG 換成本版(跑完還原),同步判法、進度條、收據格式全照 v0106。
不 import 他系統;零 TA-Lib;零網路(git 自己連)。用法同前:python VIA_RepoSafeSync_v0107.py [--apply] [--repo …] · --selftest
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
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
FAMILY = "VIA_RepoSafeSync"
TAG = "VIA_RepoSafeSync v0107"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.parent.glob(FAMILY + "_v*.py") if 0 <= _vnum(p) < _vnum(HERE)), key=_vnum)
_spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem + "_for_v0107", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)               # v0106
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
V5, BASE = PRIOR.PRIOR, PRIOR.BASE                          # v0105(main 會把 BASE.TAG 設成 V5.TAG)· v0100 本體


def __getattr__(name):  # 尾版律 TAILAPI:前版公開名稱經本檔轉接
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] == ["--selftest"]:
        return selftest()
    keep = (PRIOR.TAG, V5.TAG)
    PRIOR.TAG = V5.TAG = TAG
    try:
        return PRIOR.main(a)
    finally:
        PRIOR.TAG, V5.TAG = keep


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + name + ((" · " + str(note)[:240]) if note and not cond else ""), flush=True)

    print(f"[計] {TAG} 自測開始(本版 4 項 · 前版 {PRIOR_PATH.name} 在子行程)", flush=True)
    chk("T1 加速器真的載到(VIA_ACCEL is not None)", VIA_ACCEL is not None)
    seen = {}
    keep_main = BASE.main
    BASE.main = lambda argv=None: seen.update(tag=BASE.TAG) or 0
    try:
        rc = main(["--repo", str(HERE.parent)])
    finally:
        BASE.main = keep_main
    chk("T2 交棒到 v0100 本體時 BASE.TAG = 本版(收據 tool 欄寫 v0107,不再寫 v0105)· 跑完前版 TAG 還原",
        rc == 0 and seen.get("tag") == TAG and PRIOR.TAG == "VIA_RepoSafeSync v0106" and V5.TAG == "VIA_RepoSafeSync v0105", seen)
    cp = subprocess.run([sys.executable, "-B", str(PRIOR_PATH), "--selftest"], capture_output=True, text=True, encoding="utf-8",
                        errors="replace", timeout=1800)
    chk(f"T3 前版 {PRIOR_PATH.name} 自測照過(子行程)", cp.returncode == 0, [x for x in cp.stdout.splitlines() if "FAIL" in x][:3])
    src = HERE.read_text(encoding="utf-8")
    chk("T4 第 3 行加速器標記 · glob 取前版 · 零 TA-Lib · 不 import 他系統 · 不設同意閘",
        src.splitlines()[2].strip() == "# [VIA:ACCEL-BRIDGE:v0111]" and "HERE.parent.glob(FAMILY" in src
        and not re.search(r"^\s*(import|from)\s+talib", src, re.M) and not re.search(r"^\s*(import|from)\s+(VDF|VRN|VQG|VAP)", src, re.M)
        and not re.search(r"^\s*os\.environ\[[\"']VIA_(NET|SCRAPE)_CONSENT[\"']\]\s*=", src, re.M))
    n = sum(ok)
    print(f"[計] {TAG} 自測 {n}/{len(ok)} {'PASS' if n == len(ok) else 'FAIL'}", flush=True)
    return 0 if n == len(ok) else 1


if __name__ == "__main__":
    raise SystemExit(main())
