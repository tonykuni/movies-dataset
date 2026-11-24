#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VIA_FastRun v0103 — 薄尾(v0100–v0102 一字不動):主機實跑兩個修正 · env 提速

主機實跑 v0102(操作員 2026-11-24 18:14):
  ① 並行段一進去心跳執行緒就崩:run_all(..., beat=10**9) → Windows 的 Event.wait 上限約 49.7 天,OverflowError。
     (工作本身在別的執行緒,沒有停;只是心跳那一條掛了、印一大段例外。)
  ② 太慢:env:doctor_before 889 秒、doctor_after 650 秒(容器約 100 秒),幾乎都花在環境總管(CGC_MDL240 envmgr)。
     裝套件只影響 LIB 那幾項,裝後整套重驗是白做;envmgr 也不必擋在安裝前面。
本版:
  · 心跳間隔上限 3600 秒(進度條已經每 0.5 秒重畫,心跳只是保險)。
  · env 依序段:doctor(裝前)只跑跟安裝計畫有關的 6 項(不含 envmgr)→ 安裝閘 → doctor(裝後)只重驗 3 項
    (envtools 缺冊列 · gate_conflict 衝突 · gate_doctor 多層互撞);
    envmgr 改成並行段裡的一個工作(跟 vrn / vdf / fidelity 一起跑,不擋安裝)。
  · 工作跑完、VCGC 還在寫帳時,進度條寫「VCGC 收尾中」(v0102 這段會誤寫成「開場中」)。
其餘照 v0102(動態進度條 · 每步即時寫檔與上限 · 稀疏推送 · 只推雜湊與數字)。
用法:python VIA_FastRun_v0103.py --set env,vrn,vdf[,fidelity] [--dirs A;B] [--lanes N] [--timeout 秒] [--push] [--selftest]
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

import argparse
import importlib.util
import json
import os
import re
import shutil
import sys
import tempfile
import threading
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve()
FAMILY = "VIA_FastRun"
TAG = "VIA_FastRun v0103"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.parent.glob(FAMILY + "_v*.py") if 0 <= _vnum(p) < _vnum(HERE)), key=_vnum)
_spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem + "_for_v0103", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
BASE = PRIOR.BASE                                         # v0100
VIA = BASE.VIA
BEAT_MAX = 3600
DOCTOR_BEFORE = ["gate_doctor", "gate_conflict", "envtools", "accel", "envgov", "connect"]   # 不含 envmgr
DOCTOR_AFTER = ["envtools", "gate_conflict", "gate_doctor"]                                  # 裝套件只動到這三項
_RUN_ALL0 = BASE.run_all


def __getattr__(name):
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def run_all(jobs, out, lanes, timeout, beat: float = 20.0):
    """① 心跳間隔夾到 BEAT_MAX:Windows 的 wait 不收超大秒數。"""
    return _RUN_ALL0(jobs, out, lanes, timeout, beat=min(float(beat), BEAT_MAX))


def run_env(out: Path, timeout: int) -> tuple:
    """② env 依序段:裝前 doctor 只跑跟安裝有關的 6 項 · 裝後只重驗 3 項;envmgr 不在這裡(並行段另跑)。"""
    hub = PRIOR.hub_path()
    if hub is None:
        return [], ["env:*(VCGC_CommandHub 尾版不在)"]
    py, res = sys.executable, []
    root = Path(os.environ.get("VIA_ROOT") or VIA) / "VIA_Reports" / "vcgc_hub" / "doctor"

    def step(name, args, cap):
        PRIOR._DONE["stage"] = name
        r = PRIOR.run_job({"name": name, "argv": [py, str(hub), *args], "env": "vcgc", "timeout": cap}, out, timeout)
        BASE.say(BASE.line_of(r))
        res.append(r)
        return r
    step("env:doctor_before", ["doctor", "--only", *DOCTOR_BEFORE], 900)
    if (root / "DOCTOR_latest.txt").exists():
        shutil.copy2(root / "DOCTOR_latest.txt", out / "DOCTOR_before.txt")
    plan = PRIOR.doctor_plan()
    BASE.say("env 計畫:經安裝閘要裝 %d 個 · %s" % (len(plan), " ".join(plan) or "—"))
    if plan:
        r = step("env:install", ["install", "--yes", *plan], 3600)
        bad = PRIOR.failed_wheels((out / "env_install.log.txt").read_text(encoding="utf-8", errors="replace"))
        if r["rc"] != 0 and bad:
            rest = [x for x in plan if x not in bad]
            BASE.say("env 建不出 wheel 先拆出來:%s · 其餘 %d 個再裝" % (" ".join(bad), len(rest)))
            with PRIOR._LOCK:
                PRIOR._DONE["total"] += 1
            if rest:
                step("env:install_rest", ["install", "--yes", *rest], 3600)
        step("env:doctor_after", ["doctor", "--only", *DOCTOR_AFTER], 600)
        if (root / "DOCTOR_latest.txt").exists():
            shutil.copy2(root / "DOCTOR_latest.txt", out / "DOCTOR_after.txt")
    else:
        with PRIOR._LOCK:
            PRIOR._DONE["n"] += 2                          # 沒有要裝的:install 與裝後重驗都不用跑
        BASE.say("env 沒有要裝的 → 不跑裝後重驗")
    return res, []


def envmgr_job():
    t = BASE.tail(VIA / "supportive modules" / "registry", "CGC_MDL240_EnvManager")
    return {"name": "env:envmgr", "argv": [sys.executable, str(t), "check"], "env": "vcgc", "timeout": 1800} if t else None


_RENDER0 = PRIOR.render


def _closing() -> None:
    """③ 工作都跑完了:進度檔換成「收尾」(外層不再顯示「VCGC 開場中」);下次開跑時外層先刪掉它。"""
    try:
        tmp = PRIOR.PROGRESS.with_suffix(".tmp")
        tmp.write_text(json.dumps({"closing": True, "done": PRIOR._DONE["n"], "total": PRIOR._DONE["total"]}), encoding="utf-8")
        os.replace(tmp, PRIOR.PROGRESS)
    except OSError:
        PRIOR.PROGRESS.unlink(missing_ok=True)


def render(snap, waited: float, width: int = 118) -> str:
    if snap and snap.get("closing"):
        spin = "|/-\\"[int(waited * 2) % 4]
        return ("%s %s 工作 %d/%d 跑完 · VCGC 收尾中(寫帳 · 收據)· %ds" % (PRIOR.MARK, spin, snap.get("done", 0), snap.get("total", 0), waited))[:width]
    return _RENDER0(snap, waited, width)


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        return PRIOR.via_vcgc(argv)
    ap = argparse.ArgumentParser(prog=TAG)
    ap.add_argument("--set", default="all")
    ap.add_argument("--dirs", default="")
    ap.add_argument("--lanes", type=int)
    ap.add_argument("--timeout", type=int, default=900)
    ap.add_argument("--push", action="store_true")
    a = ap.parse_args(argv)
    sets = ["nlp", "vrn", "vdf"] if a.set == "all" else [s.strip() for s in a.set.split(",") if s.strip()]
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = VIA / "VIA_Reports" / "fastrun" / stamp
    out.mkdir(parents=True, exist_ok=True)
    jobs, skipped = BASE.jobs_for([s for s in sets if s in ("nlp", "vrn", "vdf")], out)
    if "env" in sets:
        ej = envmgr_job()
        (jobs.append(ej) if ej else skipped.append("env:envmgr(CGC_MDL240 尾版不在)"))
    fj, fs = PRIOR.fid_jobs(PRIOR.fid_dirs(a.dirs), out) if "fidelity" in sets else ([], [])
    skipped += fs
    PRIOR._DONE["total"] = len(jobs) + len(fj) + (3 if "env" in sets else 0)
    stop = threading.Event()
    wt = threading.Thread(target=PRIOR._writer, args=(stop,), daemon=True)
    wt.start()
    lanes = BASE.lanes_for(a.lanes)
    t0 = time.time()
    BASE.say("%s · 組 %s · %d 項 · %d 道 · 全文 %s" % (TAG, ",".join(sets), PRIOR._DONE["total"], lanes, out))
    results = []
    try:
        if "env" in sets:
            r, s = run_env(out, a.timeout)
            results += r
            skipped += s
        PRIOR._DONE["stage"] = "並行"
        if jobs or fj:
            results += run_all(jobs + fj, out, max(1, min(lanes, len(jobs) + len(fj))), a.timeout, beat=BEAT_MAX)
        PRIOR.fid_collect(fj, out)
    finally:
        stop.set()
        wt.join(timeout=3)
        _closing()
    worst, lines = BASE.summarize(results, skipped, out, t0, lanes)
    BASE.say(lines[0])
    for s in skipped:
        BASE.say("略過 · " + s)
    if a.push:
        BASE.say(PRIOR.push(out, stamp))
    return {"GREEN": 0, "GRAY": 2, "YELLOW": 2}.get(worst, 1)


def _install():
    BASE.HERE, BASE.TAG = HERE, TAG                      # 經 VCGC 重新進來時跑本檔
    PRIOR.HERE = HERE                                    # v0102 via_vcgc 用它自己模組的 HERE 算相對路徑
    PRIOR.render = render                                # v0102 via_vcgc 叫模組全域 render → 認得「收尾」


_install()


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + name + ((" · " + str(note)[:300]) if note and not cond else ""), flush=True)

    print("[計] %s 自測開始(本版 8 項 · 前版 %s)" % (TAG, PRIOR_PATH.name), flush=True)
    chk("T1 鏈:前版 v0102 · 本體 v0100 · 重新進來跑本檔", PRIOR_PATH.name == "VIA_FastRun_v0102.py" and Path(BASE.__file__).name == "VIA_FastRun_v0100.py"
        and BASE.HERE == HERE and PRIOR.HERE == HERE)
    seen = {}
    keep = BASE.run_all
    try:
        globals()["_RUN_ALL0"] = lambda jobs, out, lanes, timeout, beat=20.0: seen.setdefault("beat", beat) and []
        run_all([], Path("."), 1, 1, beat=10 ** 9)
    finally:
        globals()["_RUN_ALL0"] = keep
    chk("T2 心跳間隔夾到 %d 秒(Windows 的 wait 不再 OverflowError)" % BEAT_MAX, seen.get("beat") == BEAT_MAX, seen)
    ev = threading.Event()
    try:
        ev.wait(min(float(10 ** 9), BEAT_MAX) * 0 + 0.01)
        wait_ok = True
    except OverflowError:
        wait_ok = False
    chk("T2b 夾過的間隔 Event.wait 收得下(Windows 上限約 4294967 秒)", BEAT_MAX < 4294967 and wait_ok)
    chk("T3 doctor 裝前不含 envmgr · 裝後只重驗 3 項 · envmgr 變成並行工作",
        "envmgr" not in DOCTOR_BEFORE and DOCTOR_AFTER == ["envtools", "gate_conflict", "gate_doctor"]
        and (envmgr_job() is None or envmgr_job()["name"] == "env:envmgr"))
    calls = []
    keep_rj, keep_plan, keep_hub = PRIOR.run_job, PRIOR.doctor_plan, PRIOR.hub_path
    with tempfile.TemporaryDirectory(prefix="fastrun103_") as td:
        out = Path(td)
        try:
            PRIOR.hub_path = lambda: Path("hub.py")
            PRIOR.run_job = lambda job, out_, timeout: (calls.append(job["argv"][2:]) or {"name": job["name"], "rc": 0, "secs": 0.0, "lamp": "GREEN", "bits": []})
            PRIOR.doctor_plan = lambda via=VIA: []
            PRIOR._DONE.update(n=0, total=3)
            r1, _ = run_env(out, 60)
            n_empty = PRIOR._DONE["n"]
            PRIOR.doctor_plan = lambda via=VIA: ["rich"]
            (out / "env_install.log.txt").write_text("ok\n", encoding="utf-8")
            calls.clear()
            r2, _ = run_env(out, 60)
        finally:
            PRIOR.run_job, PRIOR.doctor_plan, PRIOR.hub_path = keep_rj, keep_plan, keep_hub
    chk("T4 沒有要裝的:只跑裝前 doctor(6 項)· 不裝 · 不重驗(省兩步)",
        len(r1) == 1 and n_empty == 2, (len(r1), n_empty))
    chk("T5 有要裝的:裝前 6 項 → 安裝閘 → 裝後只 3 項", calls == [["doctor", "--only", *DOCTOR_BEFORE], ["install", "--yes", "rich"], ["doctor", "--only", *DOCTOR_AFTER]], calls)
    line = render({"closing": True, "done": 9, "total": 9}, 12.0)
    chk("T7 跑完後進度條寫「VCGC 收尾中」不再寫「開場中」· 一行不超寬 · 其他狀態照前版",
        "收尾中" in line and "開場中" not in line and len(line) <= 118 and "開場中" in render(None, 1.0) and PRIOR.render is render, line)
    src = HERE.read_text(encoding="utf-8")
    chk("T6 檔面:加速器橋 · 零 TA-Lib · 不寫同意閘 · 沒有寫死的使用者路徑 · 本檔不再出現 10**9 心跳",
        "[VIA:ACCEL-BRIDGE:v0100]" in src and not re.search(r"^\s*(import|from)\s+talib", src, re.M)
        and not re.search(r"os\.environ\[[\"']VIA_(NET|SCRAPE)_CONSENT", src) and not re.search(r"[A-Z]:\\\\Users\\\\[a-z]", src)
        and "beat=10 ** 9)" not in src.split("def selftest")[0])
    n = sum(ok)
    print("[計] %s 自測 %d/%d · %s" % (TAG, n, len(ok), "PASS" if n == len(ok) else "FAIL"), flush=True)
    print("[前版] %s 自測(前版自己的 HERE / TAG)" % PRIOR_PATH.name, flush=True)
    keep_here = (BASE.HERE, BASE.TAG, PRIOR.HERE, PRIOR.render)
    BASE.HERE, BASE.TAG, PRIOR.HERE, PRIOR.render = PRIOR_PATH.resolve(), PRIOR.TAG, PRIOR_PATH.resolve(), _RENDER0
    try:
        rc_prior = PRIOR.selftest()
    finally:
        BASE.HERE, BASE.TAG, PRIOR.HERE, PRIOR.render = keep_here
    print("[計] %s 自測 OK %d · FAIL %d · 前版 rc=%s" % (TAG, n, len(ok) - n, rc_prior), flush=True)
    return 0 if n == len(ok) and rc_prior == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
