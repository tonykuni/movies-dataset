#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VIA_VCGC_ApplyRun v0108 — 薄尾:go 一開跑先安全同步桌機倉(VIA_RepoSafeSync 尾版 --apply);倉更新了就改由更新後的 ApplyRun 尾版重跑

操作員 2026-11-21 桌機實錄:`git pull` 被一個桌機自己生、main 上同名的未追蹤檔擋下 → 桌機停在舊 main(少 52 個提交)
→ go 跑的是 ApplyRun v0104 / v0105 與舊引擎,紅燈全是舊程式的燈;操作員:「自動完成速度快」。
本版只加一件事(其餘全照 v0107 · 前版一字不動):
  go(沒帶 --no-sync)→ 先叫 VIA_RepoSafeSync 尾版 --apply(只快轉 · 擋路的同名檔先搬到倉外備份 · main 為準 · 不刪檔):
    SYNCED      → 本檔可能已被更新 → 以「更新後的 ApplyRun 尾版」重跑同一組參數 + --no-sync(只重跑一次,不會循環)
    UP_TO_DATE  → 照常往下(本檔就是最新)
    其他(不在 main · 本機有自己的提交 · 連不到)→ 印原因與要打的那一行,照現有程式往下跑並標黃(不擋)
  --no-sync:跳過同步(重跑那一次自動帶)。
不代設同意閘;不碰 TA-Lib;不改 .ps1。用法同 v0107:go [--via-db <夾>] [--vrn-source <夾>] [--no-sync] … · --selftest
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
# [VIA:NET-BRIDGE] 留名:本檔不出網(git 由 VIA_RepoSafeSync 叫)

import importlib.util
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VIA_VCGC_ApplyRun"
VERSION = "v0108"
TAG = "VIA_VCGC_ApplyRun " + VERSION
SYNC_GLOB = "VIA_RepoSafeSync_v*.py"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem + "_for_v0108", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
BASE = PRIOR.BASE


def __getattr__(name):
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def _tail(glob: str):
    hits = sorted((p for p in HERE.glob(glob) if _vnum(p) >= 0), key=_vnum)
    return hits[-1] if hits else None


def sync_first(runner=None) -> tuple:
    """回 (狀態, 印的行)。狀態:SYNCED / UP_TO_DATE / SKIP / 其他(照原因往下)。"""
    tool = _tail(SYNC_GLOB)
    if tool is None:
        return "SKIP", [f"[{TAG}] 倉同步略過:VIA_RepoSafeSync 不在"]
    try:
        cp = (runner or subprocess.run)([sys.executable, str(tool), "--apply", "--repo", str(HERE)], capture_output=True, text=True,
                                        encoding="utf-8", errors="replace", timeout=900)
    except Exception as exc:  # noqa: BLE001
        return "ERROR", [f"[{TAG}] 倉同步沒跑完:{type(exc).__name__}: {str(exc)[:120]}(照現有程式往下 · 黃)"]
    lines = [x for x in (cp.stdout or "").splitlines() if x.strip()]
    m = re.search(r"\] (SYNCED|UP_TO_DATE|WRONG_BRANCH|DIVERGED|FETCH_FAIL|FF_FAIL|NOT_REPO|BEHIND) ", lines[0] if lines else "")
    st = m.group(1) if m else ("UP_TO_DATE" if cp.returncode == 0 else "ERROR")
    if st not in ("SYNCED", "UP_TO_DATE"):
        lines.append(f"[{TAG}] 倉沒更新 → 照現有程式往下跑(結果可能是舊程式的燈 · 黃)")
    return st, lines


def main(argv=None, runner=None, rerun=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a == ["--selftest"]:
        return selftest()
    if a[:1] == ["go"]:
        if "--no-sync" in a:
            a.remove("--no-sync")
        else:
            st, lines = sync_first(runner)
            for ln in lines:
                print(ln, flush=True)
            if st == "SYNCED":
                new = _tail(_STEM + "_v*.py")
                print(f"[{TAG}] 倉已快轉 → 改由 {new.name} 重跑同一組參數(--no-sync)", flush=True)
                cmd = [sys.executable, str(new)] + a + ["--no-sync"]
                return (rerun or (lambda c: subprocess.run(c).returncode))(cmd)
    return PRIOR.main(a)


def selftest() -> int:
    import contextlib
    import io
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)) if note and not cond else ""), flush=True)

    rc0 = PRIOR.selftest()
    print(f"=== {TAG} · 薄尾自測(go 先安全同步桌機倉;假子行程 · 零網路)===", flush=True)
    chk("⓪ 前版 v0107 自測過", rc0 == 0, f"rc {rc0}")

    def fake(state, rc=0):
        return lambda cmd, **k: subprocess.CompletedProcess(cmd, rc, f"[VIA_RepoSafeSync v0100] {state} · main x → origin/main y\n", "")
    seen, ran = {}, []
    keep = PRIOR.main
    PRIOR.main = lambda a: ran.append(list(a)) or 0
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            rc_s = main(["go", "--via-db", "X"], runner=fake("SYNCED"), rerun=lambda c: seen.setdefault("cmd", c) and 0)
            rc_u = main(["go", "--no-backup"], runner=fake("UP_TO_DATE"))
            rc_w = main(["go"], runner=fake("WRONG_BRANCH", 2))
            rc_n = main(["go", "--no-sync"], runner=lambda *x, **k: (_ for _ in ()).throw(AssertionError("不該叫同步")))
    finally:
        PRIOR.main = keep
    cmd = seen.get("cmd") or []
    chk("① SYNCED → 以 ApplyRun 尾版重跑同一組參數 + --no-sync(不再進前版)",
        cmd[1:2] and Path(cmd[1]).name.startswith(_STEM + "_v") and cmd[2:] == ["go", "--via-db", "X", "--no-sync"] and ran[:1] != [["go", "--via-db", "X"]], cmd)
    chk("② UP_TO_DATE → 照常交 v0107(參數原樣)", ["go", "--no-backup"] in ran, ran)
    chk("③ 不在 main / 分歧 → 照現有程式往下(不擋)", ["go"] in ran, ran)
    chk("④ --no-sync → 不叫同步 · 交 v0107 時拿掉 --no-sync", ran.count(["go"]) == 2, ran)
    st, lines = sync_first(runner=lambda *x, **k: (_ for _ in ()).throw(OSError("boom")))
    chk("⑤ 同步工具起不來 → ERROR 一行說明(不丟例外)", st == "ERROR" and "沒跑完" in lines[0], lines)
    chk("⑥ 同步工具在(%s)" % (_tail(SYNC_GLOB).name if _tail(SYNC_GLOB) else "—"), _tail(SYNC_GLOB) is not None)
    src = Path(__file__).read_text(encoding="utf-8")
    body = src.split("def selftest", 1)[0]
    chk("⑦ 加速器橋在 · 網路橋留名;不碰 TA-Lib;不寫同意閘", "[VIA:ACCEL-BRIDGE:v0100]" in src and "[VIA:NET-BRIDGE" in src
        and not re.search(r"^\s*(import|from)\s+talib", src, re.M) and not re.search(r"environ\[[\"']VIA_(NET|SCRAPE)_CONSENT", body))
    names = [n for n in dir(PRIOR) if not n.startswith("_") and callable(getattr(PRIOR, n, None))]
    chk("⑧ 尾版保有前版公開名稱(TAILAPI)", all(getattr(sys.modules[__name__], n, None) is not None for n in names), f"{len(names)} 支")
    print(f"  [計] {TAG} 本版 {sum(ok)}/{len(ok)} · {'PASS' if all(ok) else 'FAIL'}", flush=True)
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
