#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VCGC_CommandHub v0117 — 薄尾(v0100–v0116 一字不動):via-graph build 動態進度條 + 動態百分比(依檔數估)

操作員 2026-11-25:「卡段沒反應,請加動態進度條及動態百分比」。v0116 只有每 30 秒一行心跳。
Graphify 本身不報進度 → 本版照實「估」:
  ① 開跑前數該系統要建圖的程式檔(同 CGC_MDL280 的系統夾與排除規則)。
  ② 每檔秒數:這台機器上次建同一系統量到的(VIA_Graphify_timing.json)> 容器實測 0.12 秒/檔(VRN 共用夾 1,086 支 · 121 秒)。
  ③ 終端機同一行原地更新:[████░░░░] 約 45%(依檔數估 · 1,234 支)· 已 63 秒 · 預估剩 77 秒;子行程沒結束前最多顯示 99%,
     超過預估時改寫「比預估慢,仍在跑」,不假裝完成;結束才寫 100%(或照實寫失敗)。
  ④ 建完把這次的檔數與秒數寫進 VIA_Graphify_timing.json(同 MDL280 輸出夾),下次估得更準。
  ⑤ 不是終端機(轉向檔案 / 日誌):退回 v0116 的心跳(每 ≤30 秒一行)。Ctrl+C / 逾時同 v0116:收整棵子行程樹。
換的是 v0116 模組全域 hb_run(v0116 的 cmd_graph 叫的就是本版);非建圖的子行程(git · 查詢 · via-bak)照 v0116。
不 import 他系統;零 TA-Lib;不設同意閘。
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

import fnmatch
import importlib.util
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VCGC_CommandHub"
TAG = "VCGC_CommandHub v0117"
DEFAULT_SEC_PER_FILE = 0.12                               # 容器實測:VRN 共用夾 1,086 支 · 121 秒
CODE_EXT = {".py", ".ps1", ".psm1", ".js", ".ts", ".sh"}
SYSTEMS_FALLBACK = {"VRN": "functional modules/VRN2", "VRN_Shared": "functional modules/VRN", "VDF": "functional modules/VDF",
                    "VCGC": "supportive modules/registry", "VQG": "functional modules/VQG", "AOS": "supportive modules/agent_os"}
EXCLUDES_FALLBACK = ["references/", "intake/", "_quarantine*/", "*quarantine*/", "VIA_RetiredEngines/", "backup*/", "archive*/"]


def _vnum(p) -> int:
    m = re.search(r"_v(\d+)$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
if PRIOR_PATH.stem in sys.modules:
    PRIOR = sys.modules[PRIOR_PATH.stem]
else:
    _spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem, PRIOR_PATH)
    PRIOR = importlib.util.module_from_spec(_spec)
    sys.modules[PRIOR_PATH.stem] = PRIOR
    _spec.loader.exec_module(PRIOR)
_PREV_HB = PRIOR.hb_run


def __getattr__(name):
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def _graph_rules():
    """系統夾與排除規則:取 CGC_MDL280 尾版的(同一套),讀不到才用本檔的備份值。"""
    try:
        reg = HERE / "supportive modules" / "registry"
        tail = max((p for p in reg.glob("CGC_MDL280_VCGCAgentOSHub_v*.py") if _vnum(p) >= 0), key=_vnum)
        spec = importlib.util.spec_from_file_location("cgc_mdl280_rules_hub117", tail)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        return dict(m.GRAPHIFY_SYSTEMS), list(m.GRAPHIFY_EXCLUDES)
    except Exception:                                    # noqa: BLE001
        return dict(SYSTEMS_FALLBACK), list(EXCLUDES_FALLBACK)


def count_code_files(folder: Path, excludes: list) -> int:
    pats = [e.rstrip("/") for e in excludes]
    n = 0
    for dirpath, dirnames, filenames in os.walk(folder):
        dirnames[:] = [d for d in dirnames if not any(fnmatch.fnmatch(d, p) for p in pats) and not d.startswith(".")]
        n += sum(1 for f in filenames if Path(f).suffix.lower() in CODE_EXT)
    return n


def timing_path(out: Path = None) -> Path:
    return (out or PRIOR.GRAPH_OUT) / "VIA_Graphify_timing.json"


def sec_per_file(system: str, out: Path = None) -> tuple:
    try:
        rec = json.loads(timing_path(out).read_text(encoding="utf-8")).get(system) or {}
        if rec.get("files") and rec.get("secs"):
            return max(0.005, rec["secs"] / rec["files"]), "這台上次實測"
    except (OSError, ValueError, TypeError):
        pass
    return DEFAULT_SEC_PER_FILE, "容器實測預設"


def save_timing(system: str, files: int, secs: float, out: Path = None) -> None:
    p = timing_path(out)
    try:
        data = json.loads(p.read_text(encoding="utf-8")) if p.is_file() else {}
    except (OSError, ValueError):
        data = {}
    data[system] = {"files": files, "secs": round(secs, 1), "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(p.name + ".%d.tmp" % os.getpid())
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    os.replace(tmp, p)


def bar(pct: float, width: int = 24) -> str:
    pct = max(0.0, min(100.0, pct))
    full = int(round(width * pct / 100))
    return "█" * full + "░" * (width - full)


def progress_text(system: str, files: int, elapsed: float, est: float, done: bool = False, rc: int = None) -> str:
    if done:
        pct = 100.0 if rc == 0 else min(99.0, 100.0 * elapsed / est if est else 0.0)
        tail = "完成" if rc == 0 else "沒完成(rc %s)" % rc
        return "[via-graph] 建圖 %s [%s] %3.0f%%(依檔數估 · %s 支)· 已 %d 秒 · %s" % (system, bar(pct), pct, f"{files:,}", elapsed, tail)
    pct = min(99.0, 100.0 * elapsed / est) if est else 0.0
    left = "預估剩 %d 秒" % max(0, est - elapsed) if elapsed < est else "比預估慢,仍在跑(不用按 Ctrl+C)"
    return "[via-graph] 建圖 %s [%s] 約 %2.0f%%(依檔數估 · %s 支)· 已 %d 秒 · %s" % (system, bar(pct), pct, f"{files:,}", elapsed, left)


def _graph_target(argv) -> str | None:
    a = [str(x) for x in argv]
    if "graphify" in a and "run" in a and "--system" in a:
        return a[a.index("--system") + 1]
    return None


def pb_run(argv, env=None, cwd=None, capture_output=False, text=False, timeout=None, every=None, log=print, out_stream=None, tty=None,
           timing_out=None):
    """建圖子行程:終端機上畫動態進度條(依檔數估);其餘子行程與非終端機照 v0116 的 hb_run(心跳)。"""
    system = _graph_target(argv)
    stream = out_stream or sys.stdout
    is_tty = stream.isatty() if tty is None else tty
    if system is None or capture_output or not is_tty:
        return _PREV_HB(argv, env=env, cwd=cwd, capture_output=capture_output, text=text, timeout=timeout, every=every, log=log)
    systems, excludes = _graph_rules()
    folder = HERE / systems.get(system, "")
    files = count_code_files(folder, excludes) if folder.is_dir() else 0
    rate, src = sec_per_file(system, out=timing_out)
    est = max(5.0, files * rate)
    stream.write("[via-graph] %s:%s 支程式檔 · 每檔 %.2f 秒(%s)→ 預估 %d 秒\n" % (system, f"{files:,}", rate, src, est))
    kw = {"env": env, "cwd": cwd}
    if os.name == "nt":
        kw["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        kw["start_new_session"] = True
    start = time.monotonic()
    proc = subprocess.Popen(list(argv), **kw)
    try:
        while proc.poll() is None:
            el = time.monotonic() - start
            if timeout is not None and el >= timeout:
                PRIOR._kill_tree(proc)
                stream.write("\n")
                raise subprocess.TimeoutExpired(argv, timeout)
            stream.write("\r" + progress_text(system, files, el, est).ljust(110))
            stream.flush()
            time.sleep(0.5)
    except KeyboardInterrupt:
        PRIOR._kill_tree(proc)
        stream.write("\n[via-graph] 收到 Ctrl+C · 建圖 %s 的子行程(pid %d)已整棵收掉 · 這一步沒完成,不寫快照\n" % (system, proc.pid))
        stream.flush()
        raise
    el = time.monotonic() - start
    stream.write("\r" + progress_text(system, files, el, est, done=True, rc=proc.returncode).ljust(110) + "\n")
    stream.flush()
    if proc.returncode == 0 and files:
        save_timing(system, files, el, out=timing_out)
    return subprocess.CompletedProcess(argv, proc.returncode, None, None)


def install() -> None:
    PRIOR.hb_run = pb_run                                # v0116 的 cmd_graph / cmd_bak_sub 查模組全域 → 用本版


def _restore() -> None:
    PRIOR.hb_run = _PREV_HB


install()


def main(argv: list | None = None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    return PRIOR.main(a)


def selftest() -> int:
    import contextlib
    import io
    import tempfile
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + name + ((" · " + str(note)[:300]) if note and not cond else ""), flush=True)

    print("[計] %s 自測開始(本版 6 項 · 前版 %s)" % (TAG, PRIOR_PATH.name), flush=True)
    with tempfile.TemporaryDirectory(prefix="hub117_") as td:
        t = Path(td)
        (t / "src" / "references").mkdir(parents=True)
        (t / "src" / "backup_old").mkdir()
        for i in range(5):
            (t / "src" / f"a{i}.py").write_text("x=1\n", encoding="utf-8")
        (t / "src" / "b.ps1").write_text("$x=1\n", encoding="utf-8")
        (t / "src" / "c.json").write_text("{}", encoding="utf-8")
        (t / "src" / "references" / "skip.py").write_text("", encoding="utf-8")
        (t / "src" / "backup_old" / "skip.py").write_text("", encoding="utf-8")
        n = count_code_files(t / "src", EXCLUDES_FALLBACK)
        chk("① 數檔照 MDL280 的排除規則(references/ · backup*/ 不算;只算程式檔)", n == 6, n)
        r0 = sec_per_file("VCGC", out=t)
        save_timing("VCGC", 100, 50.0, out=t)
        r1 = sec_per_file("VCGC", out=t)
        chk("② 每檔秒數:沒紀錄 → 容器預設 0.12;建完寫 timing → 下次用這台實測(50 秒 / 100 支 = 0.5)",
            r0 == (DEFAULT_SEC_PER_FILE, "容器實測預設") and r1 == (0.5, "這台上次實測"), (r0, r1))
    mid = progress_text("VCGC", 1234, 63, 140)
    slow = progress_text("VCGC", 1234, 200, 140)
    fin = progress_text("VCGC", 1234, 150, 140, done=True, rc=0)
    bad = progress_text("VCGC", 1234, 40, 140, done=True, rc=3)
    chk("③ 進度字:約 45% · 預估剩 77 秒;超過預估最多 99% 並寫「比預估慢,仍在跑」;成功才 100%;失敗照實寫",
        "約 45%" in mid and "預估剩 77 秒" in mid and "約 99%" in slow and "比預估慢" in slow and "100%" in fin and "完成" in fin
        and "沒完成(rc 3)" in bad and "100%" not in bad, (mid, slow, fin, bad))
    screen = io.StringIO()
    keep = _graph_rules
    globals()["_graph_rules"] = lambda: ({"VCGC": "supportive modules/registry"}, EXCLUDES_FALLBACK)
    try:
        with tempfile.TemporaryDirectory(prefix="hub117t_") as tt:
            r = pb_run([sys.executable, "-c", "import time; time.sleep(1.6)", "graphify", "run", "--system", "VCGC"],
                       out_stream=screen, tty=True, timing_out=Path(tt))
            wrote = (Path(tt) / "VIA_Graphify_timing.json").is_file()
    finally:
        globals()["_graph_rules"] = keep
    s = screen.getvalue()
    chk("④ 終端機:同一行原地更新(\\r)· 進度條 · 百分比 · 結束寫 100% 與「完成」· 回傳碼照收",
        r.returncode == 0 and s.count("\r") >= 2 and "█" in s and "完成" in s and "100%" in s and wrote
        and not timing_path().is_file(), s[-240:])
    lines = []
    r2 = pb_run([sys.executable, "-c", "import time; time.sleep(2.6)", "graphify", "run", "--system", "VCGC"],
                every=1, log=lambda *a, **k: lines.append(" ".join(map(str, a))), out_stream=io.StringIO(), tty=False)
    chk("⑤ 不是終端機:退回 v0116 心跳(每 ≤1 秒測試間隔一行);非建圖子行程一律照 v0116",
        r2.returncode == 0 and sum("心跳" in x for x in lines) >= 2 and PRIOR.hb_run is pb_run, lines)
    src = Path(__file__).read_text(encoding="utf-8")
    body = src.split("def selftest", 1)[0]
    chk("⑥ 檔面:加速器橋 · 零 TA-Lib · 不設同意閘 · 不 import 他系統",
        "[VIA:ACCEL-BRIDGE:v0100]" in src and not re.search(r"^\s*(import|from)\s+talib", body, re.M)
        and not re.search(r"os\.environ\[[\"']VIA_(NET|SCRAPE)_CONSENT", body) and not re.search(r"^\s*(import|from)\s+(VDF_|VRN_|VQG_|VAP_|CGC_)", body, re.M))
    n_ok = sum(ok)
    print("[計] %s 自測 %d/%d · %s" % (TAG, n_ok, len(ok), "PASS" if n_ok == len(ok) else "FAIL"), flush=True)
    print("[前版] %s 自測(換回前版的 hb_run)" % PRIOR_PATH.name, flush=True)
    _restore()
    try:
        with contextlib.redirect_stdout(io.StringIO()) as buf:
            rc_prior = PRIOR.selftest()
    finally:
        install()
    print(buf.getvalue()[-400:], end="", flush=True)
    print("[計] %s 自測 OK %d · FAIL %d · 前版 rc=%s" % (TAG, n_ok, len(ok) - n_ok, rc_prior), flush=True)
    return 0 if n_ok == len(ok) and rc_prior == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
