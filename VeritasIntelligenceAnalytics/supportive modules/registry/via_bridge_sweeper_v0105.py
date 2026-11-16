#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""via_bridge_sweeper v0105 — v0104 薄尾(v0104 一字不動):掛上 VCGC 正尺(CGC_MDL124)認得的標準加速器橋塊

緣由(2026-11-15 · PR 647 Codex P1):v0104 檔頭只有 `# [VIA:ACCEL-BRIDGE:v0111]` 一行註記,VCGC 正尺 CGC_MDL124 v0111
認的是標準橋塊 `# ===== [VIA:ACCEL-BRIDGE:v0100] …`,所以全樹加速器量尺報這一支「缺」。上一輪把橋塊**就地**注進 v0104,
違反 AGENTS.md 第 4 條「修改開新版;已鎖成功來源維持原樣」—— v0104 是交接案 C-bridge-sweeper-v0104 的對象,收據記著它的 SHA。
本版:v0104 原封還原(SHA 與收據一致),橋塊放在本版;其餘行為一字不動,全部轉給 v0104(v0104 再接 v0103)。
自測:① 本檔有標準橋塊(用正尺自己的常數判)② v0104 一字不動(SHA = 交接收據記的那個)
      ③ 正尺掃本檔 = 已掛(HAS)④ 前版 v0104 自測(乾淨子行程,含它的前版鏈)rc 0。不連網 · 不寫任何檔。
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

import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path

VERSION = "v0105"
STEM = "via_bridge_sweeper"
HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
CASE_RECEIPT = VIA / "docs" / "handoff" / "evidence" / "C-bridge-sweeper-v0104.json"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name):
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def _ruler():
    """VCGC 正尺 CGC_MDL124 BridgeSweeper 尾版(只讀它的常數與 scan;不注入)。"""
    tail = max(HERE.glob("CGC_MDL124_BridgeSweeper_v*.py"), key=_vnum)
    spec = importlib.util.spec_from_file_location("CGC_MDL124_ruler_for_" + Path(__file__).stem, tail)
    mod = importlib.util.module_from_spec(spec)
    argv, sys.argv = sys.argv, [str(tail)]
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.argv = argv
    return tail, mod


def _receipt_sha(rel: str) -> str:
    try:
        d = json.loads(CASE_RECEIPT.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return ""
    return str((d.get("dependencies") or {}).get(rel) or "")


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)) if note and not cond else ""), flush=True)

    src = Path(__file__).read_text(encoding="utf-8")
    tail, ruler = _ruler()
    chk("① 本檔有標準加速器橋塊(正尺 %s 的 ACCEL_START / END)" % tail.stem, ruler.ACCEL_START in src and ruler.ACCEL_END in src)
    rel = PRIOR_PATH.relative_to(VIA).as_posix()
    want = _receipt_sha(rel)
    have = hashlib.sha256(PRIOR_PATH.read_bytes()).hexdigest()
    chk("② 前版 %s 一字不動:SHA = 交接收據 C-bridge-sweeper-v0104 記的 %s…" % (PRIOR_PATH.stem, want[:12]), bool(want) and have == want, have[:12])
    rows = {r["file"]: r["state"] for r in ruler.scan(HERE.relative_to(VIA).as_posix(), "accel")}
    me, prior = Path(__file__).resolve().relative_to(VIA).as_posix(), rel
    chk("③ 正尺掃描:本版 = 已掛(HAS)· 前版 = 版史(不算缺)", rows.get(me) == "HAS" and rows.get(prior) == "EXCLUDED", (rows.get(me), rows.get(prior)))
    cp = subprocess.run([sys.executable, str(PRIOR_PATH), "--selftest"], cwd=str(HERE), capture_output=True, text=True, encoding="utf-8",
                        errors="replace", timeout=900, env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    for ln in (cp.stdout or "").splitlines()[-3:]:
        print("    │ " + ln, flush=True)
    chk("④ 前版 %s 自測(乾淨子行程,含前版鏈)rc 0" % PRIOR_PATH.stem, cp.returncode == 0, "rc %s" % cp.returncode)
    n = sum(ok)
    print("[%s] via_bridge_sweeper %s selftest · 本版 %d/%d" % ("PASS" if n == len(ok) else "FAIL", VERSION, n, len(ok)), flush=True)
    return 0 if n == len(ok) else 1


def main() -> int:
    if "--selftest" in sys.argv[1:]:
        return selftest()
    return PRIOR.main()


if __name__ == "__main__":
    sys.exit(main())
