#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL172_VRNChainRunner v0107 — 薄尾:逾時冊上的節點被停掉時,留下「跑到哪」的證據

工作站 2026-09-28 19:58 實錄:VRN_AutoTestLoop 放寬到 900s 仍逾時 → NODATA「沒跑完=沒有結論」,但**看不出卡在哪**:
v0105 用 subprocess.run(capture_output) 等,逾時被停掉時已印出的輸出一併丟掉;子行程輸出又是區塊緩衝,停掉前可能一行都沒寫出來。
本尾版只對逾時冊(VIA_VRN_ChainNodeLedger 尾版)上有列名的節點:
  ① 子行程加 PYTHONUNBUFFERED=1(一行一行寫出來,停掉時才有東西可收);
  ② 逾時被停掉時,把已收到的 stdout + stderr 全文寫進 VIA_Reports/vrn_chain/timeout/<節點>.log,
     結果 detail 附最後一行非空輸出(例:AutoTestLoop 的 [進度] k/K),fix 指向那份 log。
態照舊 NODATA(逾時≠紅,批616);冊上沒列名的節點、--fast、一般跑完的節點全照 v0106(L04 舊版一字不動)。
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
import subprocess as _real_subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL172_VRNChainRunner"
PRIOR_PATH = [p for p in sorted(HERE.glob(_STEM + "_v*.py")) if p.name < Path(__file__).name][-1]
_spec = importlib.util.spec_from_file_location("vrnchain_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
VERSION = Path(__file__).stem.rsplit("_v", 1)[-1]


def _body_module(mod):
    """往回走到真正呼叫 subprocess 的那一層(具體實作 = 模組上有 subprocess 且沒有 PRIOR)。"""
    seen = 0
    while getattr(mod, "PRIOR", None) is not None and seen < 12:
        mod = mod.PRIOR
        seen += 1
    return mod


BODY = _body_module(PRIOR)
TIMEOUT_DIR = BODY.VIA / "VIA_Reports" / "vrn_chain" / "timeout"


class _Shim:
    """只換 run:加 PYTHONUNBUFFERED;逾時時把已收到的輸出記進 holder 再照原樣拋。其餘屬性原樣轉交。"""

    def __init__(self, holder: dict):
        self.holder = holder

    def __getattr__(self, name):
        return getattr(_real_subprocess, name)

    def run(self, *a, **kw):
        env = dict(kw.get("env") or os.environ)
        env["PYTHONUNBUFFERED"] = "1"
        kw["env"] = env
        try:
            return _real_subprocess.run(*a, **kw)
        except _real_subprocess.TimeoutExpired as exc:
            def _txt(x):
                return x.decode("utf-8", "replace") if isinstance(x, (bytes, bytearray)) else (x or "")
            self.holder["out"] = _txt(exc.stdout) + ("\n" if exc.stdout and exc.stderr else "") + _txt(exc.stderr)
            raise


def _last_line(text: str) -> str:
    lines = [ln.strip() for ln in (text or "").splitlines() if ln.strip()]
    return lines[-1][:160] if lines else ""


_PRIOR_RUN_NODE = PRIOR.run_node


def run_node(layer: str, node: dict, timeout: int) -> dict:
    fam = node.get("family") or ""
    table, _skipped = PRIOR.load_timeouts()
    if fam not in table or timeout != BODY.DEFAULT_TIMEOUT:
        return _PRIOR_RUN_NODE(layer, node, timeout)
    holder: dict = {}
    keep = BODY.subprocess
    BODY.subprocess = _Shim(holder)
    try:
        got = _PRIOR_RUN_NODE(layer, node, timeout)
    finally:
        BODY.subprocess = keep
    if "out" in holder and got.get("state") == "NODATA":
        TIMEOUT_DIR.mkdir(parents=True, exist_ok=True)
        log = TIMEOUT_DIR / f"{fam}.log"
        log.write_text(holder["out"], encoding="utf-8")
        last = _last_line(holder["out"]) or "(停掉前一行輸出都沒有)"
        got["detail"] = f"{got.get('detail')} · 停掉前最後一行:{last}"
        got["fix"] = f"看 {BODY.rel(log)}(停掉前全文)找卡住的那一段"
    return got


BODY.run_node = run_node          # v0105 的 collect / main 一律走本尾版(v0106 的放寬照樣在內層生效)


def __getattr__(name):
    return getattr(PRIOR, name)


def selftest() -> int:
    rc = PRIOR.selftest()
    results = []

    def chk(name, ok, note=""):
        results.append(bool(ok))
        print(f"  [{'OK' if ok else 'FAIL'}] {name}{(' · ' + note) if note else ''}")

    print(f"=== {_STEM} v{VERSION} 薄尾加檢(逾時留證據)===")
    chk("⓪ 往回找到具體實作(有 subprocess、沒有 PRIOR)", hasattr(BODY, "subprocess") and getattr(BODY, "PRIOR", None) is None, Path(BODY.__file__).name)
    probe = BODY.VIA / "VIA_Reports" / "_vrnchain_probe_v0107"
    probe.mkdir(parents=True, exist_ok=True)
    slow = probe / "hangprobe.py"
    slow.write_text('import sys, time\nif "--selftest" in sys.argv:\n    print("  [進度] 3/9 G06 批次")\n    print("  [進度] 4/9 G07 首頁")\n'
                    '    time.sleep(30)\n', encoding="utf-8")
    node = {"family": "PROBE_HANG", "tail": str(slow.relative_to(BODY.VIA))}
    keep_default, keep_cache = BODY.DEFAULT_TIMEOUT, list(PRIOR._LEDGER_CACHE)
    keep_load = PRIOR.load_timeouts
    try:
        BODY.DEFAULT_TIMEOUT = 2
        PRIOR.load_timeouts = lambda path=None: ({"PROBE_HANG": 3}, [])
        PRIOR._LEDGER_CACHE[:] = [({"PROBE_HANG": 3}, [])]
        g = run_node("L9_試", node, 2)
        log = TIMEOUT_DIR / "PROBE_HANG.log"
        body = log.read_text(encoding="utf-8") if log.is_file() else ""
        chk("① 冊上節點逾時:態照舊 NODATA,detail 附停掉前最後一行", g["state"] == "NODATA" and "4/9 G07 首頁" in g["detail"], g["detail"][-60:])
        chk("② 停掉前全文寫進 timeout/<節點>.log,fix 指向它", "3/9 G06 批次" in body and "PROBE_HANG.log" in g.get("fix", ""), BODY.rel(log))
        chk("③ 跑完後 subprocess 還原成原模組(只在這一格換)", BODY.subprocess is _real_subprocess)
        g2 = run_node("L9_試", dict(node, family="PROBE_OTHER"), 2)
        chk("④ 冊上沒列名:照 v0106(不寫 log、不附最後一行)", g2["state"] == "NODATA" and "停掉前" not in g2["detail"], g2["state"])
    finally:
        BODY.DEFAULT_TIMEOUT = keep_default
        PRIOR.load_timeouts = keep_load
        PRIOR._LEDGER_CACHE[:] = keep_cache
        for f in (slow, TIMEOUT_DIR / "PROBE_HANG.log"):
            if f.is_file():
                f.unlink()
        probe.rmdir()
    ok = rc == 0 and all(results)
    print(f"  [計] {_STEM} v{VERSION} 薄尾 {sum(results)}/{len(results)} · v0106 以下 {'PASS' if rc == 0 else 'FAIL'} · 合計 {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in a:
        print(f"=== VRN 六層鏈 v{VERSION} · v0105 廿六檢 + v0106 + v0107 薄尾加檢(沙盒零網路)===")
        return selftest()
    return BODY.main(a)


if __name__ == "__main__":
    sys.exit(main())
