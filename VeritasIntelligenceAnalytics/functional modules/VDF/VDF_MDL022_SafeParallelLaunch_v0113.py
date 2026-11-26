#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VDF_MDL022_SafeParallelLaunch v0113 — 薄尾(v0100–v0112 一字不動):中斷時說實話 · 預估剩餘用上一輪實測 · 紅黃直接列錯誤行

桌機 2026-11-27 00:18 實跑(start · 3 道):fetch 跑到 10 分鐘按 Ctrl+C,接著印出的「詳細摘要矩陣」是**上一輪**
(2026-11-26T14:12Z · 548.5s)的 —— v0112 中斷後照樣印 VDF_Launch_latest.json,沒說那是舊的;
進度條 ETA 一直停在 03:54(v0111 用「已耗 ÷ 已完成數」估,fetch 一支就佔大半,估不準);
紅燈的「原因」只給最後一行(例「[加速] 載工具時生的輔助子行程 0 支」),看不出真正錯在哪。
本版(start / summary 兩個動詞換成本檔的;其餘照 v0112):
  ① start 記開跑時間;跑完看 VDF_Launch_latest.json 是不是這一輪寫的(檔時間 ≥ 開跑):
     不是(中斷 / 子行程沒寫完)→ 先印黃框「本輪沒有跑完」+ 本輪各流程停在哪(完成 / 跑中 / 未開始 · 秒),
     再印上一輪矩陣並標明時間;中斷回 rc 130。
  ② 預估剩餘:用上一輪每支流程的實測秒數(VDF_Launch_latest.json)。輪詢時記每支流程第一次「跑中」的時間,
     跑中的剩 = 上一輪秒數 − 本輪已跑;剩餘 ≈ max(跑中最久還剩的那支, 全部剩餘工作 ÷ 同時在跑的道數)(並行不重算)。
     沒有上一輪就照 v0111 的估法。
  ③ summary:紅 / 黃流程,從它自己的日誌抓前 3 條錯誤行(Traceback · Error · RED · FAIL · rc≠0 · 失敗 · 錯)直接列出,
     不用再自己開日誌找。只在本機印,不寫檔、不送出。
不代設同意閘;不碰 TA-Lib;不改前版任何名稱。
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
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        _nb_spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        _nb_mod = _nb_ilu.module_from_spec(_nb_spec)
        _nb_spec.loader.exec_module(_nb_mod)
        return _nb_mod
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import importlib.util
import json
import os
import re
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parents[1]
STEM = "VDF_MDL022_SafeParallelLaunch"
VERSION = "v0113"
TAG = f"{STEM} {VERSION}"
RUNNER = None                                           # 自測換掉主流程用(本檔自己的鉤子,不改前版模組)
CHILD_CMD = None
ERR_RX = re.compile(r"Traceback|Error\b|Exception|\bRED\b|\bFAIL|失敗|錯誤|\brc[ =:]*[1-9]", re.I)


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(str(p)).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(f"{STEM}_prior_for_{VERSION}", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
LATEST = PRIOR.LATEST                                   # v0111 的 VDF_Launch_latest.json


def __getattr__(name):  # 尾版律 TAILAPI:前版公開名稱經本檔轉接
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


# ───────── ② 預估剩餘用上一輪實測 ─────────
def last_durations(rep: dict | None) -> dict:
    out = {}
    for j in ((rep or {}).get("run") or {}).get("jobs") or []:
        try:
            if j.get("id") and j.get("sec") is not None:
                out[str(j["id"])] = float(j["sec"])
        except (TypeError, ValueError):
            pass
    return out


def mark_started(j: dict | None, started: dict, now: float) -> dict:
    """輪詢時第一次看到某流程變「跑中」就記下時間(進度檔本身沒有每支的開跑時間)。"""
    for k, v in ((j or {}).get("jobs") or {}).items():
        if v.get("state") == "RUN" and k not in started:
            started[k] = now
    return started


def eta_from_history(j: dict | None, hist: dict, started: dict | None = None, now: float | None = None) -> float | None:
    """並行下的剩餘時間(PR #767 Codex P2):
    跑中的每一支 剩 = max(0, 上一輪秒數 − 本輪已跑);還沒開始的照上一輪秒數;
    剩餘 ≈ max(跑中最久還剩的那支, 全部剩餘工作 ÷ 同時在跑的道數)。缺歷史 → None(照 v0111)。"""
    jobs = (j or {}).get("jobs") or {}
    if not jobs or not hist:
        return None
    now = time.time() if now is None else now
    started = started or {}
    run_k = [k for k, v in jobs.items() if v.get("state") == "RUN"]
    wait_k = [k for k, v in jobs.items() if v.get("state") not in ("DONE", "FAILED", "SKIP", "RUN")]
    if any(k not in hist for k in run_k + wait_k):
        return None
    rem_run = [max(0.0, hist[k] - (now - started.get(k, now))) for k in run_k]
    work = sum(rem_run) + sum(hist[k] for k in wait_k)
    lanes = max(1, len(run_k))
    return max(max(rem_run, default=0.0), work / lanes)


def view(j: dict | None, hist: dict, started: dict | None = None) -> dict | None:
    if not j:
        return j
    now = time.time()
    if started is not None:
        mark_started(j, started, now)
    e = eta_from_history(j, hist, started, now)
    return dict(j, eta_s=round(e, 1)) if e is not None else j


def _render_ansi(proc, path: Path, poll: float, out, hist: dict) -> None:
    f, started = 0, {}
    out.write("\x1b[?25l")
    try:
        while proc.poll() is None:
            out.write(PRIOR.bar_line(view(PRIOR._read(path), hist, started), f))
            out.flush()
            f += 1
            time.sleep(poll)
        out.write(PRIOR.bar_line(view(PRIOR._read(path), hist), f, done=True) + "\n")
    finally:
        out.write("\x1b[?25h")
        out.flush()


def _render_rich(proc, path: Path, poll: float, hist: dict) -> bool:
    try:
        from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
    except ImportError:
        return False
    with Progress(SpinnerColumn(), TextColumn("[bold]{task.description}"), BarColumn(), TextColumn("{task.percentage:>5.1f}%"),
                  TimeElapsedColumn(), TextColumn("ETA {task.fields[eta]}")) as bar:
        t = bar.add_task("VDF 啟動", total=100, eta="--:--")
        started = {}
        while proc.poll() is None:
            j = view(PRIOR._read(path), hist, started)
            if j:
                bar.update(t, completed=float(j.get("pct") or 0), eta=PRIOR._mmss(j.get("eta_s")),
                           description=f"VDF {j.get('done', 0)}/{j.get('total', 0)} · {j.get('current') or ''}"[:80])
            time.sleep(poll)
        bar.update(t, completed=100, eta="00:00")
    return True


# ───────── ① 中斷時說實話 ─────────
def is_fresh(latest: Path, t0: float) -> bool:
    try:
        return latest.stat().st_mtime >= t0 - 1
    except OSError:
        return False


def progress_table(j: dict | None) -> list:
    rows = []
    for k, v in ((j or {}).get("jobs") or {}).items():
        st = v.get("state") or "WAIT"
        rows.append(f"    {k:<12} {({'DONE': '完成', 'FAILED': '失敗', 'SKIP': '略過', 'RUN': '跑中'}).get(st, '未開始'):<4} "
                    f"{('%.1fs' % float(v['sec'])) if v.get('sec') is not None else '—':>8}  {v.get('lamp') or ''}")
    return rows


def start_cmd(rest: list, out=None, tty=None, progress_path: Path = None, poll: float = 0.12, log_dir=None, latest: Path = None) -> int:
    import subprocess
    import tempfile
    out = out or sys.stdout
    rest = list(rest)
    ui = "auto"
    if "--ui" in rest:
        i = rest.index("--ui")
        ui = (rest[i + 1:i + 2] or ["auto"])[0]
        del rest[i:i + 2]
    is_tty = out.isatty() if tty is None else tty
    run = RUNNER or main
    if "--plain" in rest or "--check" in rest or ui == "plain" or not is_tty:
        return run(["launch", *[a for a in rest if a != "--plain"]])
    rc = run(["launch", "--check", *rest])
    if rc == 1:
        return 1
    latest = Path(latest or LATEST)
    hist = last_durations(PRIOR._read(latest))
    path = Path(progress_path or PRIOR.PROGRESS_FILE)
    try:
        path.unlink()
    except OSError:
        pass
    t0 = time.time()
    log = Path(log_dir or tempfile.gettempdir()) / f"VIA_VDF_launch_{time.strftime('%Y%m%d_%H%M%S')}.log"
    cmd = list(CHILD_CMD) if CHILD_CMD else [sys.executable, "-X", "utf8", str(Path(__file__).resolve()), "launch", "--skip-preflight", *rest]
    interrupted = False
    with open(log, "w", encoding="utf-8", errors="replace") as fh:
        proc = PRIOR.spawn(cmd, stdout=fh, stderr=subprocess.STDOUT)
        print(f"  背景執行中 · 完整輸出 → {log}" + ("(預估剩餘用上一輪實測秒數)" if hist else ""), file=out, flush=True)
        try:
            if ui == "ansi" or not (ui in ("auto", "rich") and _render_rich(proc, path, poll, hist)):
                _render_ansi(proc, path, poll, out, hist)
        except KeyboardInterrupt:
            interrupted = True
            print("\n  中斷:收掉背景 Python 行程樹", file=out, flush=True)
        finally:
            if proc.poll() is None:
                PRIOR.kill_tree(proc)
        rc = proc.wait()
    if interrupted or not is_fresh(latest, t0):
        mins = (time.time() - t0) / 60
        print(f"\n  ╭─ 黃 · 本輪沒有跑完({'你按了中斷' if interrupted else '子行程 rc %s,沒寫出本輪摘要' % rc} · 已跑 {mins:.1f} 分)", file=out)
        print("  │ 本輪各流程停在:", file=out)
        for ln in progress_table(PRIOR._read(path)) or ["    (進度檔還沒有流程)"]:
            print("  │" + ln, file=out)
        old = PRIOR._read(latest) or {}
        print(f"  ╰─ 下面的矩陣是**上一輪**({old.get('at') or old.get('stamp') or '時間不明'})的,不是這一輪", file=out, flush=True)
    run(["summary"])
    print(f"  完整輸出 → {log}", file=out, flush=True)
    return 130 if interrupted else rc


# ───────── ③ 紅黃直接列錯誤行 ─────────
def error_lines(log_path, n: int = 3) -> list:
    try:
        lines = Path(log_path).read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []
    hits = [ln.strip() for ln in lines if ERR_RX.search(ln) and ln.strip()]
    seen, out = set(), []
    for ln in hits:
        if ln not in seen:
            seen.add(ln)
            out.append(ln[:180])
        if len(out) >= n:
            break
    return out


def summary_cmd(args: list, out=None, latest: Path = None) -> int:
    out = out or sys.stdout
    rc = (RUNNER or PRIOR.main)(["summary", *args])
    rep = PRIOR._read(Path(latest or LATEST)) or {}
    bad = [j for j in (rep.get("run") or {}).get("jobs") or [] if j.get("lamp") in ("RED", "YELLOW")]
    if bad:
        print("  紅 / 黃流程的日誌錯誤行(前 3 條;只在本機印):", file=out)
        for j in bad:
            ls = error_lines(j.get("log")) if j.get("log") else []
            print(f"    {j.get('id')} [{j.get('lamp')}]" + ("" if ls else " · 日誌裡沒有錯誤字樣(看最後一行)"), file=out)
            for ln in ls:
                print(f"      · {ln}", file=out)
        out.flush()
    return rc


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    if args[:1] == ["start"]:
        return start_cmd(args[1:])
    if args[:1] == ["summary"]:
        return summary_cmd(args[1:])
    return (RUNNER or PRIOR.main)(args)


def selftest() -> int:
    import io
    import subprocess
    import tempfile
    ok, bad = [], []

    def chk(name, cond, note=""):
        (ok if cond else bad).append(name)
        print(f"  [{'OK' if cond else 'NG'}] {name}" + (f" · {str(note)[:300]}" if note and not cond else ""), flush=True)

    chk("加速器載入(VIA_ACCEL is not None)", VIA_ACCEL is not None)
    chk("網路工具載入(_via_net() is not None · 載入不出網)", _via_net() is not None, VIA_NET_TOOL_PATH)
    hist = last_durations({"run": {"jobs": [{"id": "gate", "sec": 12}, {"id": "fetch", "sec": 300}, {"id": "sync", "sec": 200},
                                            {"id": "a", "sec": 100}, {"id": "b", "sec": 100}, {"id": "c", "sec": 150}]}})
    j = {"jobs": {"gate": {"state": "DONE", "sec": 12}, "fetch": {"state": "RUN"}, "sync": {"state": "WAIT"}}}
    e = eta_from_history(j, hist, {"fetch": 1000.0}, 1100.0)
    jc = {"jobs": {"a": {"state": "DONE", "sec": 100}, "b": {"state": "DONE", "sec": 100}, "c": {"state": "RUN"}}}
    ec = eta_from_history(jc, hist, {"c": 0.0}, 100.0)
    st = mark_started({"jobs": {"x": {"state": "RUN"}, "y": {"state": "WAIT"}}}, {}, 5.0)
    chk("① 剩餘時間(並行):fetch 已跑 100 秒 → max(200, (200+200)/1) = 400;Codex 例 a b c 同時開跑、a b 100 秒完、c 上輪 150 → 剩 50;"
        "第一次看到跑中才記開跑時間;缺歷史 → None",
        e == 400 and ec == 50 and st == {"x": 5.0} and eta_from_history({"jobs": {"new": {"state": "RUN"}}}, hist) is None, (e, ec, st))
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        prog, latest = td / "P.json", td / "L.json"
        latest.write_text(json.dumps({"at": "2026-11-26T14:12:34Z", "run": {"jobs": [{"id": "fetch", "sec": 301}]}}), encoding="utf-8")
        os.utime(latest, (time.time() - 3600,) * 2)
        writer = ("import json,sys,time\n"
                  "open(sys.argv[1],'w').write(json.dumps({'pct':50,'done':1,'total':2,'elapsed_s':1,'eta_s':1,'current':'fetch',"
                  "'jobs':{'gate':{'state':'DONE','sec':1.0,'lamp':'GREEN'},'fetch':{'state':'RUN'}}}))\n"
                  "time.sleep(0.3)\nsys.exit(int(sys.argv[2]))\n")
        calls = []
        globals()["RUNNER"] = lambda a: calls.append(list(a)) or 0
        try:
            globals()["CHILD_CMD"] = [sys.executable, "-c", writer, str(prog), "1"]
            buf = io.StringIO()
            rc = start_cmd(["--ui", "ansi"], out=buf, tty=True, progress_path=prog, poll=0.05, log_dir=td, latest=latest)
            txt = buf.getvalue()
            chk("② 子行程沒寫出本輪摘要 → 黃框「本輪沒有跑完」· 列本輪各流程(gate 完成 · fetch 跑中)· 標明下面是上一輪 14:12Z",
                rc == 1 and "本輪沒有跑完" in txt and "gate" in txt and "跑中" in txt and "上一輪" in txt and "14:12:34Z" in txt
                and calls[-1] == ["summary"], txt[-400:])
            fresh_writer = writer.replace("time.sleep(0.3)", "time.sleep(0.3);open(%r,'a').write(' ')" % str(latest))
            globals()["CHILD_CMD"] = [sys.executable, "-c", fresh_writer, str(prog), "0"]
            buf2 = io.StringIO()
            rc2 = start_cmd(["--ui", "ansi"], out=buf2, tty=True, progress_path=prog, poll=0.05, log_dir=td, latest=latest)
            chk("③ 本輪有寫出摘要(檔時間 ≥ 開跑)→ 不出黃框 · rc 照子行程 0", rc2 == 0 and "本輪沒有跑完" not in buf2.getvalue(),
                buf2.getvalue()[-300:])
        finally:
            globals()["RUNNER"] = None
            globals()["CHILD_CMD"] = None
        lg = td / "fetch.log"
        lg.write_text("start\n[加速] ok\nTraceback (most recent call last):\nValueError: bad\nValueError: bad\nrc=0\n[e054] RED rc 4\nend\n",
                      encoding="utf-8")
        el = error_lines(lg)
        chk("④ 日誌錯誤行:前 3 條、去重(Traceback · ValueError · RED rc 4);rc=0 不算", el == ["Traceback (most recent call last):",
            "ValueError: bad", "[e054] RED rc 4"], el)
        latest.write_text(json.dumps({"run": {"jobs": [{"id": "fetch", "lamp": "RED", "log": str(lg)}, {"id": "gate", "lamp": "GREEN"}]}}),
                          encoding="utf-8")
        globals()["RUNNER"] = lambda a: 0
        try:
            sb = io.StringIO()
            summary_cmd([], out=sb, latest=latest)
        finally:
            globals()["RUNNER"] = None
        chk("⑤ summary:紅 / 黃流程直接列日誌錯誤行;綠的不列", "fetch [RED]" in sb.getvalue() and "ValueError: bad" in sb.getvalue()
            and "gate [" not in sb.getvalue(), sb.getvalue())
    alone = subprocess.run([sys.executable, str(PRIOR_PATH), "--selftest"], capture_output=True, text=True, timeout=1800)
    tail = (alone.stdout.strip().splitlines() or [""])[-1]
    chk("⑥ 前版 v0112 自測單獨跑:綠,或它自己照實回黃(rc 2)· 本版不換裝前版任何名稱", alone.returncode in (0, 2), (alone.returncode, tail))
    src = Path(__file__).read_text(encoding="utf-8")
    chk("檔面:第 3 行加速器標記 · 雙橋在 · 不設同意閘 · 不含本機路徑",
        src.splitlines()[2].startswith("# [VIA:ACCEL-BRIDGE") and "[VIA:ACCEL-BRIDGE:v0100]" in src and "[VIA:NET-BRIDGE:v0100]" in src
        and not re.search(r"^\s*os\.environ\[[\"']VIA_(NET|SCRAPE)_CONSENT[\"']\]\s*=", src, re.M)
        and "C:\\Users\\" + "tonyk" not in src)
    yellow = alone.returncode == 2
    print(f"[selftest] {TAG} {len(ok)}/{len(ok) + len(bad)} " + ("PASS" if not bad else "FAIL · " + " · ".join(bad))
          + (" · 前版自測本來就黃(照實回 rc 2)" if yellow and not bad else ""), flush=True)
    return 1 if bad else (2 if yellow else 0)


if __name__ == "__main__":
    sys.exit(main())
