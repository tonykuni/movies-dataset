#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF SystemManager v0190 — 薄尾(v0189 以前一字不動):monitor 長跑要有心跳、逐動詞回報、單一動詞有時限(主機 2026-11-21 實錄「卡斷」)

  主機實錄:monitor 並行跑五個唯讀動詞,全部跑完才印 → test(各引擎自測)在桌機要好幾分鐘,畫面一直沒字,看起來卡住。
  違反 CLAUDE.md「長跑要有心跳:子行程每 30 秒內至少一行」。本版:
    · 每 20 秒印一行 [心跳]:還在等哪幾個動詞 · 各跑了幾秒;
    · 每個動詞一跑完就先印它那一格的燈與一行結果;
    · 單一動詞超過時限(預設 300 秒,--timeout N 可改)→ 停掉那一支、那一格照實記黃(逾時),其餘照跑。
  九格判法 · 收據年齡(v0189)· 鎖定模板頁 · 不出網 · 不寫別系統的檔 全照前版。用法:monitor [--lanes N] [--timeout 秒] [--json] · --selftest
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
import json
import re
import sys
import threading
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
FAMILY = "VDF_SystemManager"
TAG = "VDF_SystemManager v0190"
BEAT = 20.0


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(FAMILY + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem + "_for_v0190", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
BODY = next(m for m in (PRIOR, getattr(PRIOR, "PRIOR", None)) if m is not None and "monitor" in vars(m))   # monitor 本體(v0188)


def __getattr__(name):
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def beat_runner(timeout: float = 300.0, beat: float = BEAT, out=None, run=None):
    """包住本體的 _run:開始 / 結束各印一行;另起心跳執行緒每 beat 秒印還在跑的動詞;逾時由 _run 的 timeout 停掉。"""
    out = out or sys.stdout
    run = run or BODY._run
    live, lock, stop = {}, threading.Lock(), threading.Event()

    def say(msg):
        print(msg, file=out, flush=True)

    def heart():
        while not stop.wait(beat):
            with lock:
                items = [f"{k} {time.time() - t0:.0f}s" for k, t0 in live.items()]
            if items:
                say(f"  [心跳] 還在跑 {len(items)} 支:" + " · ".join(items) + f"(單支時限 {timeout:.0f}s)")
    th = threading.Thread(target=heart, daemon=True)
    th.start()

    def runner(args):
        name = " ".join(args)
        with lock:
            live[name] = time.time()
        say(f"  [起] {name}")
        try:
            rc, text, secs = run(args, timeout=timeout)
        finally:
            with lock:
                live.pop(name, None)
        if rc is None:
            text = f"[黃] 逾時 {timeout:.0f}s 停掉(單支時限;--timeout 可改)\n" + (text or "")
            rc = 2
        lamp = BODY._lamp_of(text, rc) if name != "bridges --json" else ("GREEN" if rc == 0 else "YELLOW")
        say(f"  [完] {name} · {lamp} · rc {rc} · {secs}s")
        return rc, text, secs
    runner.stop = stop
    return runner


def monitor(lanes: int = 3, timeout: float = 300.0, out_dir=None, rcpt_dir=None, beat: float = BEAT, run=None) -> dict:
    r = beat_runner(timeout=timeout, beat=beat, run=run)
    try:
        return BODY.monitor(lanes=lanes, runner=r, out_dir=out_dir, rcpt_dir=rcpt_dir)
    finally:
        r.stop.set()


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] == ["--selftest"]:
        return selftest()
    BODY.TAG = TAG
    if a[:1] == ["monitor"]:
        def opt(k, d):
            return a[a.index(k) + 1] if k in a and a.index(k) + 1 < len(a) else d
        print(f"[{TAG}] monitor 開始 · 五個唯讀動詞並行 · 每 {BEAT:.0f}s 一行心跳 · 單支時限 {opt('--timeout', '300')}s", flush=True)
        res = monitor(lanes=int(opt("--lanes", 3)), timeout=float(opt("--timeout", 300)))
        if "--json" in a:
            print(json.dumps(res, ensure_ascii=False, indent=1))
        else:
            BODY._print(res)
        return {"GREEN": 0, "YELLOW": 2, "RED": 1}[res["lamp"]]
    return PRIOR.main(a)


def selftest() -> int:
    import io
    import tempfile
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note and not cond else ''}")

    rc0 = PRIOR.selftest()
    print(f"=== {TAG} · 薄尾自測(心跳 · 逐動詞回報 · 逾時;假子行程 · 零網路)===")
    chk("⓪ 直接前版 %s 自測過" % PRIOR_PATH.name, rc0 == 0, f"rc {rc0}")
    canned = {"health": (0, "[VDF_SystemManager v0184] health GREEN"), "status": (2, "[VDF_SystemManager v0184] status YELLOW"),
              "bridges --json": (0, '{"accel": "112/112", "net_callers": "9/9", "missing_accel": [], "missing_net": []}'),
              "test": (None, ""), "synchronizer check": (0, "[VDF_SystemManager v0184] synchronizer GREEN")}

    def fake(args, timeout=300.0):
        k = " ".join(args)
        if k == "test":
            time.sleep(0.35)                       # 模擬慢:超過心跳間隔
            return None, "逾時", 0.35               # 模擬 _run 逾時回 None
        time.sleep(0.02)
        rc, t = canned[k]
        return rc, t, 0.02
    buf = io.StringIO()
    with tempfile.TemporaryDirectory() as td:
        r = beat_runner(timeout=0.3, beat=0.1, out=buf, run=fake)
        try:
            res = BODY.monitor(lanes=3, runner=r, out_dir=td, rcpt_dir=Path(td) / "none")
        finally:
            r.stop.set()
    log = buf.getvalue()
    by = {x["cell"]: x for x in res["rows"]}
    chk("① 慢的動詞跑的時候有 [心跳] 行(點名還在跑的動詞)", "[心跳]" in log and "test" in log.split("[心跳]", 1)[1].split("\n", 1)[0], log[:300])
    chk("② 每個動詞都有 [起] / [完] 各一行", all(log.count(f"[起] {k}") == 1 and log.count(f"[完] {k}") == 1 for k in canned), log)
    chk("③ 逾時那支 → 那一格黃(標逾時),其餘格照常", by["UNIT"]["lamp"] == "YELLOW" and "逾時" in by["UNIT"]["line"]
        and by["SYSTEM"]["lamp"] == "GREEN" and by["ACCEL_NET"]["lamp"] == "GREEN", by["UNIT"])
    chk("④ 九格都在 · 總燈取最差", [x["cell"] for x in res["rows"]] == BODY.ORDER and res["lamp"] in ("YELLOW", "RED"))
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
