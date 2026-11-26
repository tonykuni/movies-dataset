#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VCGC_CommandHub v0119 — 薄尾(v0100–v0118 一字不動):自測不吃本機 Graphify 計時檔

PR #740 Codex(P2):v0117 自測 ④ 要求「預設輸出夾的 VIA_Graphify_timing.json 不存在」。可是正式跑過一次
`via-graph build` 之後,那個檔本來就會留著(下次估秒數用)→ 之後每次 v0117 自測都 rc 1,C-hub-v0117 收據變假紅。
本版(行為不變,只改自測):
  ① 跑前版鏈自測時,把鏈上每一版的 GRAPH_OUT 暫時指到暫存夾(跑完還原)→ 那一檢只看暫存夾,不吃本機狀態;
  ② 本版自己的檢查改成 Codex 建議的判法:正式計時檔「跑前跑後狀態一樣」(有就比內容雜湊,沒有就仍然沒有)。
版號說明:v0118 由開著的 PR #747 持有(NLP / layout / markdown 單一入口),本版取 v0119;前版照 glob 取比自己小的最大版,
兩支 PR 不論誰先合,鏈都是 v0119 → v0118 → v0117 → …。正式動詞全部交給前版。不 import 他系統;零 TA-Lib;不設同意閘。
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

import contextlib
import hashlib
import importlib.util
import io
import re
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VCGC_CommandHub"
TAG = "VCGC_CommandHub v0119"


def _vnum(p) -> int:
    m = re.search(r"_v(\d+)$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem + "_for_v0119", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name):  # 尾版律 TAILAPI:前版公開名稱經本檔轉接
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def chain_modules() -> list:
    """沿 .PRIOR 往下走,回整條前版鏈的模組(去重)。"""
    out, m, seen = [], PRIOR, set()
    while m is not None and id(m) not in seen:
        seen.add(id(m))
        out.append(m)
        m = getattr(m, "__dict__", {}).get("PRIOR")
    return out


@contextlib.contextmanager
def graph_out_redirected(tmp: Path):
    """鏈上每一版自己定義的 GRAPH_OUT 暫時指到 tmp;離開時原樣還原。"""
    keep = [(m, m.__dict__["GRAPH_OUT"]) for m in chain_modules() if "GRAPH_OUT" in m.__dict__]
    try:
        for m, _v in keep:
            m.GRAPH_OUT = tmp
        yield len(keep)
    finally:
        for m, v in keep:
            m.GRAPH_OUT = v


def _timing_mod():
    return next((m for m in chain_modules() if "timing_path" in m.__dict__ and "pb_run" in m.__dict__), None)


def _state(p: Path):
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None


def main(argv: list | None = None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    return PRIOR.main(a)


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + name + ((" · " + str(note)[:240]) if note and not cond else ""), flush=True)

    print(f"[計] {TAG} 自測開始(本版 4 項 · 前版鏈 {PRIOR_PATH.name} 起在同一行程)", flush=True)
    chk("T1 加速器真的載到(VIA_ACCEL is not None)", VIA_ACCEL is not None)
    tm = _timing_mod()
    real = tm.timing_path() if tm else None
    before = _state(real) if real else "?"
    rc_r = None
    if tm:
        keep = tm._graph_rules
        tm._graph_rules = lambda: ({"VCGC": "supportive modules/registry"}, tm.EXCLUDES_FALLBACK)
        try:
            with tempfile.TemporaryDirectory(prefix="hub119t_") as tt:
                r = tm.pb_run([sys.executable, "-c", "import time; time.sleep(0.3)", "graphify", "run", "--system", "VCGC"],
                              out_stream=io.StringIO(), tty=True, timing_out=Path(tt))
                rc_r = r.returncode
                wrote = (Path(tt) / "VIA_Graphify_timing.json").is_file()
        finally:
            tm._graph_rules = keep
    chk("T2 正式計時檔跑前跑後狀態一樣(有就同雜湊、沒有就仍沒有)· 測試只寫暫存夾",
        tm is not None and rc_r == 0 and wrote and _state(real) == before, (str(real), before, rc_r))
    with tempfile.TemporaryDirectory(prefix="hub119c_") as tc:
        tcp = Path(tc)
        planted = tcp / "VIA_Graphify_timing.json"
        with graph_out_redirected(tcp) as n:
            ok_redirect = n >= 1 and tm is not None and tm.timing_path() == planted
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc_prior = PRIOR.selftest()
        restored = tm is not None and tm.timing_path() == real
    print(buf.getvalue()[-500:], end="", flush=True)
    chk("T3 前版鏈自測(GRAPH_OUT 暫指暫存夾,不吃本機計時檔)照過 · 跑完 GRAPH_OUT 還原",
        ok_redirect and rc_prior == 0 and restored, (ok_redirect, rc_prior, restored))
    src = Path(__file__).read_text(encoding="utf-8")
    chk("T4 第 3 行加速器標記 · glob 取前版 · 零 TA-Lib · 不 import 他系統 · 不設同意閘",
        src.splitlines()[2].strip() == "# [VIA:ACCEL-BRIDGE:v0111]" and "HERE.glob(_STEM" in src
        and not re.search(r"^\s*(import|from)\s+talib", src, re.M) and not re.search(r"^\s*(import|from)\s+(VDF_|VRN_|VQG_|VAP_|CGC_)", src, re.M)
        and not re.search(r"os\.environ\[[\"']VIA_(NET|SCRAPE)_CONSENT[\"']\]\s*=", src))
    n = sum(ok)
    print(f"[計] {TAG} 自測 {n}/{len(ok)} {'PASS' if n == len(ok) else 'FAIL'}", flush=True)
    return 0 if n == len(ok) else 1


if __name__ == "__main__":
    raise SystemExit(main())
