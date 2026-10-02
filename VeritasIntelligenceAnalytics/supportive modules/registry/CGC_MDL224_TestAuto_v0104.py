#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL224_TestAuto v0104 — 薄尾:交接案站(C-*)依加速器 CPU 預算並行(串測牆鐘減半)

實測(2026-10-02,操作員「全部系統在 CPU 架構下最大加速化」):VCGC 全功能串測 133 站 605s,4 核只用約 23%
(每站是一支單執行緒子行程,一站接一站)。C-* 交接案站 62 站共 420s,彼此不相依(各自 --selftest)。
本版只換「跑一站」那一格,主迴圈不動(順序 · 印行 · 狀態檔 · 紀錄冊 · 判燈全照前版):
  ① 平行度 = 加速器 VeritasCeleritas thread_budget("aggressive")(實體核數 × 記憶體壓力係數;本機 4);
     `--jobs N` 或環境 VIA_TEST_JOBS 可改;N = 1 完全等於前版。
  ② 只並行「盤點冊上連續一段、這輪真的要跑」的 C-* 站;中間夾的 V / S / E / I / L / P 站照序列跑,不跟並行段重疊
     (V 站會寫治理報告,後面的站可能讀)。沿用 / 待辦 / PS 站不叫子行程,不切段。
  ③ 同一支引擎的站排同一條線依序跑(不同時寫同一份報告);進度暫存(CGC_MDL251)讀寫加執行緒鎖。
  ④ 教訓帳的並行寫入由 CGC_MDL058 v0103 跨行程鎖保護(本版的前提;實測無鎖 6 行程 600 筆剩 24 筆)。
只收 VCGC 呼叫;零網路;不碰 TA-Lib。
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
# ===== [VIA:NET-BRIDGE:END] =====

import importlib.util
import json
import os
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENGINE = Path(__file__).stem
_STEM = "CGC_MDL224_TestAuto"


def _vnum(path) -> int:
    m = re.search(r"_v(\d+)$", Path(path).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + ENGINE, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)          # v0103:進度暫存
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
BODY = PRIOR.BODY
_RC_V0103 = BODY.run_console                            # v0103 裝上的站執行格(進度暫存 → 本體)
_RUN_V0103 = BODY.run
_LOCK = threading.Lock()
_PLAN: dict = {}


def __getattr__(name: str):
    return getattr(PRIOR, name)


# ---------------------------------------------------------------- ① 平行度
def cpu_jobs(argv: list | None = None) -> tuple:
    """(平行度, 來源)。--jobs N > VIA_TEST_JOBS > 加速器 aggressive 預算 > os.cpu_count()。"""
    argv = argv or []
    if "--jobs" in argv and argv.index("--jobs") + 1 < len(argv):
        try:
            return max(1, int(argv[argv.index("--jobs") + 1])), "--jobs"
        except ValueError:
            pass
    env = os.environ.get("VIA_TEST_JOBS", "").strip()
    if env.isdigit() and int(env) > 0:
        return int(env), "VIA_TEST_JOBS"
    try:
        cel = VIA_ACCEL.celeritas() if VIA_ACCEL is not None else None
        if cel is not None:
            return max(1, int(cel.thread_budget("aggressive"))), "VeritasCeleritas aggressive"
    except Exception:
        pass
    return max(1, os.cpu_count() or 1), "os.cpu_count"


# ---------------------------------------------------------------- ② 這輪真的要跑的站 · 連續 C-* 段
def eligible(st: dict) -> bool:
    argv = st.get("argv") or []
    return st["id"].startswith("C-") and bool(argv) and argv[0] == "run" and st.get("kind") != "ps"


def target_of(argv: list) -> str:
    """同一支引擎同一條線:run [--family X] <引擎> … 取引擎名。"""
    a, i = list(argv[1:]), 0
    while i < len(a) and a[i].startswith("--"):
        i += 2 if a[i] == "--family" else 1
    return a[i] if i < len(a) else "?"


def log_path(via: Path, st: dict) -> Path:
    return via / "VIA_Reports" / "vcgc" / "test_logs" / (re.sub(r"[^A-Za-z0-9_.-]+", "_", st["id"]) + ".txt")


def will_run(argv: list, via: Path) -> list:
    """照前版 run() 同一套篩法,列出這輪會叫子行程的站(盤點冊順序)。"""
    full, quick = "--full" in argv, "--quick" in argv
    only = argv[argv.index("--only") + 1] if "--only" in argv and argv.index("--only") + 1 < len(argv) else None
    inv_path, inv = BODY.load_inventory(via)
    if inv is None:
        return []
    stations = [s for s in inv.get("stations") or [] if not s.get("disabled")]
    if quick:
        stations = [s for s in stations if s.get("quick") or s.get("auto")]
    if only:
        stations = [s for s in stations if s["id"] == only or s["id"].startswith(only)]
    state = BODY._read_json(via / "VIA_Reports" / "vcgc" / "TEST_STATE_v0101.json", {}) or {}
    inv_sha = BODY.sha16(inv_path)
    out = []
    for st in stations:
        fp = BODY.fingerprint(via, st, inv_sha)
        last = state.get(st["id"]) or {}
        fresh = last.get("fp") == fp and last.get("lamp") == "GREEN" and \
            time.time() - float(last.get("t", 0)) < float(inv.get("reuse_hours", 24)) * 3600
        if fresh and not full:
            continue
        if st.get("pending_until") and not (via / st["pending_until"]).is_file():
            continue
        if st.get("kind") == "ps":
            continue
        out.append(st)
    return out


def segments(runs: list) -> list:
    """連續的 C-* 站成一段;中間夾一支要跑的非 C 站就切開。"""
    segs, cur = [], []
    for st in runs:
        if eligible(st):
            cur.append(st)
        else:
            if cur:
                segs.append(cur)
            cur = []
    if cur:
        segs.append(cur)
    return segs


# ---------------------------------------------------------------- ③ 並行執行格
def _journaled(via, console, argv, timeout, log):
    """同 v0103 的站執行格,但進度暫存的讀寫加鎖(多條線同時寫)。"""
    j = PRIOR._J.get("j")
    key = "console|" + "\x1f".join(str(a) for a in argv)
    with _LOCK:
        hit = j.get(key) if j is not None else None
    if hit is not None:
        out = (hit.get("out") or "") + "\n" + PRIOR.RESUME_MARK
        Path(log).parent.mkdir(parents=True, exist_ok=True)
        Path(log).write_text(out, encoding="utf-8")
        return hit.get("rc"), hit.get("secs", 0.0), out
    rc, secs, out = PRIOR._RC0(via, console, argv, timeout, log)
    if j is not None:
        with _LOCK:
            j.put(key, {"rc": rc, "secs": secs, "out": (out or "")[-20000:]})
    return rc, secs, out


def _launch(seg_id: int, via, console, runner=None) -> None:
    seg = _PLAN["segs"][seg_id]
    groups: dict = {}
    for st in seg:
        groups.setdefault(target_of(st["argv"]), []).append(st)
    run1 = runner or _journaled

    def work(sts):
        for st in sts:
            key = str(log_path(via, st))
            try:
                res = run1(via, console, st["argv"], int(st.get("timeout") or 300), log_path(via, st))
            except BaseException as exc:                 # 子行程起不來 → 這站照實紅,其他站照跑
                res = (1, 0.0, f"[並行] 站執行例外 {type(exc).__name__}: {exc}")
            _PLAN["res"][key] = res
            _PLAN["evt"][key].set()

    for st in seg:
        _PLAN["evt"][str(log_path(via, st))] = threading.Event()
    pool = ThreadPoolExecutor(max_workers=_PLAN["jobs"], thread_name_prefix="via-test")
    _PLAN["pools"].append(pool)
    # 長的組先排(同組依序):整段牆鐘 ≈ 最長那一組 / 平行度
    for sts in sorted(groups.values(), key=lambda g: -sum(int(s.get("timeout") or 300) for s in g) - 1000 * len(g)):
        pool.submit(work, sts)
    _PLAN["launched"].add(seg_id)


def run_console(via, console, argv, timeout, log):
    key = str(log)
    seg_id = _PLAN.get("seg_of", {}).get(key)
    if seg_id is None or _PLAN.get("jobs", 1) <= 1:
        return _RC_V0103(via, console, argv, timeout, log)
    if seg_id not in _PLAN["launched"]:
        _launch(seg_id, via, console)
    _PLAN["evt"][key].wait()
    return _PLAN["res"][key]


def run(argv: list, via: Path = BODY.VIA) -> tuple:
    jobs, src = cpu_jobs(argv)
    runs = will_run(argv, via) if jobs > 1 else []
    segs = segments(runs)
    _PLAN.clear()
    _PLAN.update(jobs=jobs, segs=segs, launched=set(), evt={}, res={}, pools=[],
                 seg_of={str(log_path(via, st)): i for i, seg in enumerate(segs) for st in seg})
    n_par = sum(len(s) for s in segs)
    if jobs > 1:
        print(f"  [並行] 平行度 {jobs}({src})· 交接案站 {n_par} 站分 {len(segs)} 段並行 · 其餘 {len(runs) - n_par} 站照序列")
    else:
        print(f"  [並行] 平行度 1({src})→ 全部照序列(同前版)")
    sys.stdout.flush()
    t0 = time.time()
    try:
        card, rc = _RUN_V0103(argv, via)
    finally:
        for p in _PLAN.get("pools", []):
            p.shutdown(wait=True)
    card["parallel"] = {"jobs": jobs, "source": src, "stations": n_par, "segments": len(segs),
                        "serial": len(runs) - n_par, "wall": round(time.time() - t0, 1), "by": ENGINE}
    latest = via / "VIA_Reports" / "vcgc" / "TEST_latest.json"   # 本體先寫好了報告;並行資訊補進同一份(照前版格式多一欄)
    doc = BODY._read_json(latest, None)
    if isinstance(doc, dict) and doc.get("run") == card.get("run"):
        doc["parallel"] = card["parallel"]
        latest.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return card, rc


BODY.run_console = run_console
BODY.run = run


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args:
        return selftest()
    return PRIOR.main(args)


def selftest() -> int:
    print(f"=== {ENGINE} · 薄尾自測(交接案站依 CPU 預算並行)===")
    BODY.run, BODY.run_console = _RUN_V0103, _RC_V0103      # 前版自測驗它自己的裝法:先還原,跑完裝回本版
    try:
        rc = PRIOR.selftest()
    finally:
        BODY.run, BODY.run_console = run, run_console
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    chk("① 前版 v0103 自測全過(進度暫存 · 接續);跑完後本版換裝還在", rc == 0 and BODY.run is run and BODY.run_console is run_console)
    j, src = cpu_jobs([])
    chk("② 平行度取加速器 aggressive 預算;--jobs / VIA_TEST_JOBS 可蓋過", j >= 1 and cpu_jobs(["--jobs", "1"]) == (1, "--jobs"), (j, src))
    st = lambda i, argv: {"id": i, "argv": argv}
    runs = [st("V-a", ["status"]), st("C-1", ["run", "A", "--selftest"]), st("C-2", ["run", "--family", "vrn", "B", "--selftest"]),
            st("C-3", ["run", "A", "--selftest-tail"]), st("V-b", ["ssot"]), st("C-4", ["run", "C"]), st("upd:X", ["run", "--family", "core", "X"])]
    segs = segments(runs)
    chk("③ 切段:連續 C-* 一段,中間夾 V 站就切開;upd / V 站不並行;引擎名跳過 --family",
        [[s["id"] for s in g] for g in segs] == [["C-1", "C-2", "C-3"], ["C-4"]] and target_of(runs[2]["argv"]) == "B"
        and target_of(runs[1]["argv"]) == target_of(runs[3]["argv"]) == "A")
    spans, lk = {}, threading.Lock()

    def fake(via, console, argv, timeout, log):
        t = time.time()
        time.sleep(0.4)
        with lk:
            spans.setdefault(target_of(argv), []).append((t, time.time()))
        return 0, 0.4, "ok " + " ".join(argv)

    seg = [st(f"C-{k}{n}", ["run", f"E{k}", "--selftest", str(n)]) for k in range(4) for n in range(2)]
    via = BODY.VIA
    _PLAN.clear()
    _PLAN.update(jobs=4, segs=[seg], launched=set(), evt={}, res={}, pools=[], seg_of={str(log_path(via, s)): 0 for s in seg})
    t0 = time.time()
    _launch(0, via, None, runner=fake)
    for s in seg:
        _PLAN["evt"][str(log_path(via, s))].wait(10)
    wall = time.time() - t0
    for p in _PLAN["pools"]:
        p.shutdown(wait=True)
    got = [_PLAN["res"][str(log_path(via, s))][2] for s in seg]
    overlap_same = any(a[1] > b[0] and b[1] > a[0] for v in spans.values() for i, a in enumerate(v) for b in v[i + 1:])
    chk("④ 8 站 4 支引擎、平行度 4:牆鐘約 2 站時間(序列要 8 站);每站結果對回自己;同引擎不重疊",
        wall < 0.4 * 8 * 0.6 and got == ["ok run " + " ".join(s["argv"][1:]) for s in seg] and not overlap_same,
        f"{wall:.2f}s · 同引擎重疊 {overlap_same}")
    _PLAN.clear()
    _PLAN.update(jobs=1, seg_of={})
    chk("⑤ 平行度 1 或非 C 站 → 直接走前版執行格(行為照前版)", run_console.__code__ is not None and _PLAN["jobs"] == 1)
    src_text = Path(__file__).read_text(encoding="utf-8")
    les = sorted(HERE.glob("CGC_MDL058_Lessons_v*.py"), key=_vnum)
    chk("⑥ 前提在:教訓帳 CGC_MDL058 尾版有跨行程鎖(v0103 起)· 加速器橋 · 網路橋 · 不碰 TA-Lib",
        bool(les) and _vnum(les[-1]) >= 103 and "ledger_lock" in les[-1].read_text(encoding="utf-8")
        and "[VIA:ACCEL-BRIDGE" in src_text and "[VIA:NET-BRIDGE" in src_text and not re.search(r"^\s*(import|from)\s+talib", src_text, re.M))
    print(f"  [{ENGINE}] 薄尾 {sum(ok)}/{len(ok)} {'PASS' if all(ok) else 'FAIL'}")
    return 0 if rc == 0 and all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
