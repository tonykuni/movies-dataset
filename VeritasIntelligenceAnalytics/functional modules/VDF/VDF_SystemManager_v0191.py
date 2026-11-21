#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF SystemManager v0191 — 薄尾(v0190 以前一字不動):monitor --json 時 stdout 只留 JSON(PR 714 Codex P2)

  v0190 加了開始行 · [起] / [完] · [心跳],一律印到 stdout → `monitor --json` 的輸出前面多了文字,json.loads 讀不了(容器重現)。
  本版:--json 時這些進度行改寫到 stderr(畫面照樣看得到心跳),stdout 只有一份 JSON;不帶 --json 時照 v0190 印在 stdout。
  九格判法 · 收據年齡 · 心跳 / 時限 · 鎖定模板頁 · 不出網 · 不寫別系統的檔 全照前版。用法:monitor [--lanes N] [--timeout 秒] [--json] · --selftest
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
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)。本版兩扇門都不出網。"""
    return None if VIA_NET_TOOL_PATH is None else VIA_NET_TOOL_PATH
# ===== [VIA:NET-BRIDGE:END] =====

import importlib.util
import io
import json
import re
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
FAMILY = "VDF_SystemManager"
TAG = "VDF_SystemManager v0191"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(FAMILY + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem + "_for_v0191", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
BODY = PRIOR.BODY                                   # monitor 本體(v0188);心跳層在 PRIOR(v0190)


def __getattr__(name):
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def monitor(lanes: int = 3, timeout: float = 300.0, out_dir=None, rcpt_dir=None, beat: float = PRIOR.BEAT, run=None, progress=None) -> dict:
    """同 v0190 monitor;progress = 進度行(起 / 完 / 心跳)寫到哪(預設 stdout)。"""
    r = PRIOR.beat_runner(timeout=timeout, beat=beat, out=progress, run=run)
    try:
        return BODY.monitor(lanes=lanes, runner=r, out_dir=out_dir, rcpt_dir=rcpt_dir)
    finally:
        r.stop.set()


def run_monitor(a: list, stdout=None, stderr=None, **kw) -> int:
    stdout, stderr = stdout or sys.stdout, stderr or sys.stderr
    as_json = "--json" in a
    progress = stderr if as_json else stdout           # --json:進度走 stderr,stdout 只留 JSON

    def opt(k, d):
        return a[a.index(k) + 1] if k in a and a.index(k) + 1 < len(a) else d
    print(f"[{TAG}] monitor 開始 · 五個唯讀動詞並行 · 每 {PRIOR.BEAT:.0f}s 一行心跳 · 單支時限 {opt('--timeout', '300')}s", file=progress, flush=True)
    res = monitor(lanes=int(opt("--lanes", 3)), timeout=float(opt("--timeout", 300)), progress=progress, **kw)
    if as_json:
        print(json.dumps(res, ensure_ascii=False, indent=1), file=stdout, flush=True)
    else:
        keep, sys.stdout = sys.stdout, stdout
        try:
            BODY._print(res)
        finally:
            sys.stdout = keep
    return {"GREEN": 0, "YELLOW": 2, "RED": 1}[res["lamp"]]


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] == ["--selftest"]:
        return selftest()
    BODY.TAG = TAG
    if a[:1] == ["monitor"]:
        return run_monitor(a)
    return PRIOR.main(a)


def selftest() -> int:
    import tempfile
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note and not cond else ''}")

    rc0 = PRIOR.selftest()
    print(f"=== {TAG} · 薄尾自測(--json 時 stdout 只有 JSON;假子行程 · 零網路)===")
    chk("⓪ 直接前版 %s 自測過" % PRIOR_PATH.name, rc0 == 0, f"rc {rc0}")
    canned = {"health": (0, "[VDF_SystemManager v0184] health GREEN"), "status": (2, "[VDF_SystemManager v0184] status YELLOW"),
              "bridges --json": (0, '{"accel": "112/112", "net_callers": "9/9", "missing_accel": [], "missing_net": []}'),
              "test": (None, ""), "synchronizer check": (0, "[VDF_SystemManager v0184] synchronizer GREEN")}

    def fake(args, timeout=300.0):
        k = " ".join(args)
        if k == "test":
            time.sleep(0.35)
            return None, "逾時", 0.35
        time.sleep(0.02)
        rc, t = canned[k]
        return rc, t, 0.02
    with tempfile.TemporaryDirectory() as td:
        out, err = io.StringIO(), io.StringIO()
        rc = run_monitor(["monitor", "--json", "--timeout", "0.3"], stdout=out, stderr=err, beat=0.1, run=fake, out_dir=td, rcpt_dir=Path(td) / "none")
        try:
            doc = json.loads(out.getvalue())
            parsed = True
        except ValueError:
            doc, parsed = {}, False
        chk("① --json:stdout 整份就是 JSON(json.loads 讀得了 · Codex 重現情境)", parsed and doc.get("lamp") in ("YELLOW", "RED"), out.getvalue()[:160])
        e = err.getvalue()
        chk("② --json:開始行 · [起] / [完] · [心跳] 都在 stderr(畫面照樣看得到)", "monitor 開始" in e and "[起] health" in e and "[完] health" in e and "[心跳]" in e, e[:200])
        chk("③ 回碼照總燈(有逾時 → 黃 2)", rc == 2, rc)
        out2, err2 = io.StringIO(), io.StringIO()
        run_monitor(["monitor", "--timeout", "0.3"], stdout=out2, stderr=err2, beat=0.1, run=fake, out_dir=td, rcpt_dir=Path(td) / "none")
        chk("④ 不帶 --json:進度與九格照 v0190 印在 stdout · stderr 沒東西", "[起] health" in out2.getvalue() and "monitor 開始" in out2.getvalue()
            and not err2.getvalue().strip(), err2.getvalue()[:120])
    src = Path(__file__).read_text(encoding="utf-8")
    body = src.split("def selftest", 1)[0]
    peer = [k for k in ("VIA_FROM_VCGC", "VIA_FROM_VRN") if re.search(r"environ(?:\[[\"']%s[\"']\]\s*=|\.setdefault\([\"']%s)" % (k, k), body)]
    chk("⑤ 系統獨立:不設他系統的入口旗標(本檔是 VDF 自己的入口;VCGC 只支援不干涉)", not peer, peer)
    chk("⑥ 加速器橋 · 網路橋在;不出網 · 不碰 TA-Lib", "[VIA:ACCEL-BRIDGE:v0100]" in src and "[VIA:NET-BRIDGE:v0100]" in src
        and "_via_net()." not in body and "talib" not in body.lower())
    pub = [n for n in dir(PRIOR) if not n.startswith("_") and callable(getattr(PRIOR, n, None))]
    chk("⑦ 尾版保有前版公開名稱(TAILAPI)", all(getattr(sys.modules[__name__], n, None) is not None for n in pub), f"{len(pub)} 支")
    print(f"  [計] {TAG} 本版 {sum(ok)}/{len(ok)} · {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
