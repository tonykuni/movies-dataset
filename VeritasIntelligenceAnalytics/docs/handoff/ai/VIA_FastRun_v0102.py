#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VIA_FastRun v0102 — 薄尾(v0100 · v0101 一字不動):env · fidelity 兩組 + 動態進度條 + 每步即時紀錄與上限

操作員 2026-11-24:「以後這種指令都用 py 寫導入加速器 · ps 只是簡單啟動 · 好慢」「如果沒卡斷都要加入動態進度條」。
  今天兩條 PS 一行(環境檢查 · VRN 量測)都把邏輯寫在 PS:git 靜音卡住看不出來、變數名不分大小寫撞名、輪詢慢。
  CLAUDE.md 2026-11-18 早就要「短指令背後改成呼叫 Python 入口 · PS 只留進環境與轉呼叫」→ 掛在既有的快跑器上,不另做一支。
本版:
  --set env       VCGC 中樞 doctor →(讀 DOCTOR_latest 的計畫)install --yes(經 CGC_MDL056 安裝閘;同意閘只在安裝子行程)
                  → 建不出 wheel 的拆出來、其餘再裝一次 → doctor 再驗。依序跑(後一步要前一步的結果)。
  --set fidelity  VRN ENG397 尾版 fidelity 量兩個測試夾(預設 <家>/OneDrive/Documents/VeritasIntelligenceAnalytics/private/
                  測試樣本報告 與 知識文件_非報告;--dirs a;b 可換),並行;只推雜湊與數字(檔名對照留本機)。
  其他組(nlp · vrn · vdf)照前版。
  動態進度條:子行程每秒寫進度檔;外層(連著主控台的那一支)每 0.5 秒原地重畫一行:
    總進度 · 各跑著的步驟秒數 / 上限 · 量測第幾份 / 共幾份;VCGC 開場時也轉圈顯示秒數(不會看起來卡住)。
  每一步:子行程輸出即時寫檔(不再整段收在記憶體)· 上限到了連子行程樹一起停,記 rc 124,接下一步。
用法:python VIA_FastRun_v0102.py --set env,fidelity [--dirs A;B] [--lanes N] [--timeout 秒] [--push] [--selftest]
rc:0 全綠 · 2 有黃 / 有略過 · 1 有紅 / 有失敗 · 3 VCGC 擋下
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
import subprocess
import sys
import tempfile
import threading
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve()
FAMILY = "VIA_FastRun"
TAG = "VIA_FastRun v0102"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.parent.glob(FAMILY + "_v*.py") if 0 <= _vnum(p) < _vnum(HERE)), key=_vnum)
_spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem + "_for_v0102", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
BASE = PRIOR.PRIOR                                       # v0100:run_all · run_job · push · via_vcgc 都在這
VIA, REPO, MARK = BASE.VIA, BASE.REPO, BASE.MARK
PROGRESS = VIA / "VIA_Reports" / "fastrun" / "_progress_live.json"
FID_DIRS = [("reports", "測試樣本報告"), ("knowledge", "知識文件_非報告")]
_RUN = {}                                                # 跑著的步驟:名 → {t0, timeout, log, tot}
_DONE = {"n": 0, "total": 0, "stage": ""}
_LOCK = threading.Lock()


def __getattr__(name):
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


# ─────────────────────────── 每步:即時寫檔 · 上限 · 停整棵 ───────────────────────────
def _kill_tree(p) -> None:
    try:
        if os.name == "nt":
            subprocess.run(["taskkill", "/T", "/F", "/PID", str(p.pid)], capture_output=True)
        else:
            os.killpg(p.pid, 9)
    except Exception:  # noqa: BLE001  已經結束的行程停不了 = 目的已達
        p.kill()


def run_job(job: dict, out: Path, timeout: int) -> dict:
    """前版 run_job 的即時版:stdout / stderr 直接寫檔(進度條讀得到)· 上限到了停整棵子行程樹 · 回傳格式照前版。"""
    t0 = time.time()
    safe = re.sub(r"[^\w.-]+", "_", job["name"])
    so_p, se_p = out / f"{safe}.stdout.live", out / f"{safe}.stderr.live"
    cap = int(job.get("timeout") or timeout)
    with _LOCK:
        _RUN[job["name"]] = {"t0": t0, "timeout": cap, "log": str(so_p), "tot": job.get("tot", 0)}
    rc = None
    try:
        with open(so_p, "w", encoding="utf-8") as fo, open(se_p, "w", encoding="utf-8") as fe:
            kw = {"start_new_session": True} if os.name != "nt" else {}
            p = subprocess.Popen(job["argv"], stdout=fo, stderr=fe, env=BASE.child_env(job["env"]), cwd=str(REPO), **kw)
            while p.poll() is None:
                if time.time() - t0 > cap:
                    _kill_tree(p)
                    p.wait(timeout=30)
                    rc = 124
                    break
                time.sleep(0.25)
            rc = p.returncode if rc is None else rc
    except OSError as exc:
        se_p.write_text("%s: %s" % (type(exc).__name__, exc), encoding="utf-8")
        rc = 127
    finally:
        with _LOCK:
            _RUN.pop(job["name"], None)
            _DONE["n"] += 1
    so = so_p.read_text(encoding="utf-8", errors="replace")
    se = se_p.read_text(encoding="utf-8", errors="replace") + ("\n逾時 %d 秒,已停整棵子行程" % cap if rc == 124 else "")
    secs = time.time() - t0
    (out / f"{safe}.log.txt").write_text("# %s\n# argv: %s\n# rc %s · %.1fs\n\n## stdout\n%s\n\n## stderr\n%s\n"
                                        % (job["name"], " ".join(map(str, job["argv"])), rc, secs, so, se), encoding="utf-8")
    for f in (so_p, se_p):
        f.unlink(missing_ok=True)
    return PRIOR.brief(job, rc, secs, so, se)          # 一行結果由呼叫端印(run_all 的 one() 照前版印)


# ─────────────────────────── 進度:子行程寫檔 · 外層重畫一行 ───────────────────────────
def _docs_done(log: str) -> int:
    try:
        return len(set(re.findall(r"^\s+(D\d{3})·", Path(log).read_text(encoding="utf-8", errors="replace"), re.M)))
    except OSError:
        return 0


def snapshot() -> dict:
    now = time.time()
    with _LOCK:
        run = [{"name": k, "secs": int(now - v["t0"]), "timeout": v["timeout"], "docs": _docs_done(v["log"]) if v["tot"] else 0, "tot": v["tot"]}
               for k, v in _RUN.items()]
        return {"done": _DONE["n"], "total": _DONE["total"], "stage": _DONE["stage"], "running": run, "ts": now}


def _writer(stop: threading.Event) -> None:
    PROGRESS.parent.mkdir(parents=True, exist_ok=True)
    while not stop.wait(1.0):
        try:
            tmp = PROGRESS.with_suffix(".tmp")
            tmp.write_text(json.dumps(snapshot(), ensure_ascii=False), encoding="utf-8")
            os.replace(tmp, PROGRESS)
        except OSError:
            continue                                     # 進度檔寫不進去只影響進度條,不影響工作


def render(snap: dict | None, waited: float, width: int = 118) -> str:
    """一行進度條(不換行)。snap 為 None = 子行程還沒開始寫(VCGC 開場中)。"""
    if not snap:
        spin = "|/-\\"[int(waited * 2) % 4]
        return ("%s %s VCGC 開場中(省 Token 第一步 · 政策 · 閘)%ds" % (MARK, spin, waited))[:width]
    tot, done = max(1, snap["total"]), snap["done"]
    k = int(20 * done / tot)
    bar = "█" * k + "░" * (20 - k)
    parts = []
    for r in snap["running"][:3]:
        s = "%s %ds/%ds" % (r["name"], r["secs"], r["timeout"])
        if r["tot"]:
            s += " 第 %d/%d 份" % (r["docs"], r["tot"])
        parts.append(s)
    line = "%s ▕%s▏ %d/%d · %ds · %s%s" % (MARK, bar, done, snap["total"], waited, (snap["stage"] + " · ") if snap["stage"] else "",
                                         " | ".join(parts) or "收尾中")
    return line[:width]


def via_vcgc(argv: list) -> int:
    """經 VCGC run 進來一次(照前版);外層邊收子行程的 [快跑] 行、邊每 0.5 秒原地重畫進度條。"""
    v = BASE.tail(VIA / "supportive modules" / "registry", "CGC_MDL149_VeritasCentralGovernanceConsole")
    if v is None:
        print("%s VCGC 主控台不在 → 停(rc 3)" % MARK)
        return 3
    PROGRESS.unlink(missing_ok=True)
    env = dict(os.environ, VIA_FROM_VCGC="YES", PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
    p = subprocess.Popen([sys.executable, str(v), "run", HERE.relative_to(VIA).as_posix(), *argv], stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace", env=env, cwd=str(REPO))
    keep, lines = [], []
    rd = threading.Thread(target=lambda: [keep.append(ln) or (ln.startswith(MARK) and lines.append(ln)) for ln in p.stdout], daemon=True)
    rd.start()
    tty, t0, shown, bucket = sys.stdout.isatty(), time.time(), "", -1
    while p.poll() is None or rd.is_alive():
        while lines:
            if tty and shown:
                sys.stdout.write("\r" + " " * len(shown) + "\r")
                shown = ""
            sys.stdout.write(lines.pop(0))
        try:
            snap = json.loads(PROGRESS.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            snap = None
        cur = render(snap, time.time() - t0)
        if tty:
            sys.stdout.write("\r" + cur.ljust(len(shown)))
            shown = cur
        elif int((time.time() - t0) // 20) != bucket:            # 不是主控台(被轉存)就 20 秒一行
            bucket = int((time.time() - t0) // 20)
            print(cur)
        sys.stdout.flush()
        time.sleep(0.5)
    if tty and shown:
        sys.stdout.write("\r" + " " * len(shown) + "\r")
    for ln in lines:
        sys.stdout.write(ln)
    rc = p.wait()
    wrap = VIA / "VIA_Reports" / "fastrun" / "_vcgc_wrapper_last.txt"
    wrap.parent.mkdir(parents=True, exist_ok=True)
    wrap.write_text("".join(keep), encoding="utf-8")
    if not any(ln.startswith(MARK) for ln in keep):
        print("%s VCGC 沒有放行(rc %s)· 最後幾行:" % (MARK, rc))
        for ln in keep[-5:]:
            print("   " + ln.rstrip()[:200])
        return 3 if rc in (0, 2) else rc
    return rc


# ─────────────────────────── env:doctor → install → doctor ───────────────────────────
def hub_path():
    return BASE.tail(VIA, "VCGC_CommandHub")


def failed_wheels(text: str) -> list:
    return sorted(set(re.findall(r"Failed building wheel for (\S+)", text or "")))


def doctor_plan(via: Path = VIA) -> list:
    root = Path(os.environ.get("VIA_ROOT") or via)
    try:
        rep = json.loads((root / "VIA_Reports" / "vcgc_hub" / "doctor" / "DOCTOR_latest.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    return [x for x in (rep.get("plan") or {}).get("pip") or [] if x]


def run_env(out: Path, timeout: int) -> tuple:
    hub = hub_path()
    if hub is None:
        return [], ["env:*(VCGC_CommandHub 尾版不在)"]
    py, res, skipped = sys.executable, [], []
    root = Path(os.environ.get("VIA_ROOT") or VIA) / "VIA_Reports" / "vcgc_hub" / "doctor"

    def step(name, args, cap):
        _DONE["stage"] = name
        r = run_job({"name": name, "argv": [py, str(hub), *args], "env": "vcgc", "timeout": cap}, out, timeout)
        BASE.say(BASE.line_of(r))
        res.append(r)
        return r
    step("env:doctor_before", ["doctor"], 1200)
    shutil.copy2(root / "DOCTOR_latest.txt", out / "DOCTOR_before.txt") if (root / "DOCTOR_latest.txt").exists() else None
    plan = doctor_plan()
    BASE.say("env 計畫:經安裝閘要裝 %d 個 · %s" % (len(plan), " ".join(plan) or "—"))
    if plan:
        r = step("env:install", ["install", "--yes", *plan], 3600)
        bad = failed_wheels((out / "env_install.log.txt").read_text(encoding="utf-8", errors="replace"))
        if r["rc"] != 0 and bad:
            rest = [x for x in plan if x not in bad]
            BASE.say("env 建不出 wheel 先拆出來:%s · 其餘 %d 個再裝" % (" ".join(bad), len(rest)))
            with _LOCK:
                _DONE["total"] += 1
            if rest:
                step("env:install_rest", ["install", "--yes", *rest], 3600)
    else:
        with _LOCK:
            _DONE["n"] += 1                               # 沒有要裝的:install 這一步算完成
    step("env:doctor_after", ["doctor"], 1200)
    shutil.copy2(root / "DOCTOR_latest.txt", out / "DOCTOR_after.txt") if (root / "DOCTOR_latest.txt").exists() else None
    return res, skipped


# ─────────────────────────── fidelity:兩個測試夾並行 ───────────────────────────
def fid_dirs(arg: str = "") -> list:
    if arg:
        return [("dir%d" % i, Path(x.strip())) for i, x in enumerate(arg.split(";"), 1) if x.strip()]
    base = Path.home() / "OneDrive" / "Documents" / "VeritasIntelligenceAnalytics" / "private"
    return [(k, base / name) for k, name in FID_DIRS]


def fid_jobs(dirs: list, out: Path) -> tuple:
    eng = BASE.tail(VIA / "functional modules" / "VRN", "VRN_ENG397_P1Segment")
    if eng is None or "def fidelity" not in eng.read_text(encoding="utf-8", errors="replace"):
        return [], ["fidelity:*(VRN ENG397 尾版沒有 fidelity)"]
    jobs, skipped = [], []
    for k, d in dirs:
        if not d.is_dir():
            skipped.append("fidelity:%s(找不到資料夾)" % k)
            continue
        top = len(list(d.glob("*.pdf")))
        deep = len(list(d.rglob("*.pdf")))
        kinds = {}
        for f in d.rglob("*"):
            if f.is_file():
                kinds[f.suffix.lower() or "(無)"] = kinds.get(f.suffix.lower() or "(無)", 0) + 1
        (out / ("fidelity_%s_counts.txt" % k)).write_text("頂層 PDF %d · 含子夾 PDF %d · 全部檔案:%s\n" % (
            top, deep, " · ".join("%s %d" % kv for kv in sorted(kinds.items(), key=lambda x: -x[1]))), encoding="utf-8")
        if deep > top:
            BASE.say("fidelity:%s 子夾裡的 %d 份 PDF 略過(引擎只讀頂層,和 VRN 正常流程一樣)" % (k, deep - top))
        if top == 0:
            skipped.append("fidelity:%s(頂層沒有 PDF)" % k)
            continue
        jobs.append({"name": "fidelity:%s" % k, "argv": [sys.executable, str(eng), "fidelity", str(d), "--rep", str(out / ("fid_" + k)), "--calib", "1"],
                     "env": "own", "timeout": max(1800, top * 180), "tot": top, "dir": str(d), "key": k})
    return jobs, skipped


def fid_collect(jobs: list, out: Path) -> None:
    """只把雜湊與數字搬到頂層(會被 --push 收):FIDELITY_latest.json / .txt;資料夾路徑換成 <key>;檔名對照不搬。"""
    for j in jobs:
        src = out / ("fid_" + j["key"]) / "p1view"
        for nm, ext in (("FIDELITY_latest.json", "json"), ("FIDELITY_latest.txt", "txt")):
            f = src / nm
            if f.exists():
                (out / ("fidelity_%s.%s" % (j["key"], ext))).write_text(f.read_text(encoding="utf-8").replace(j["dir"], "<%s>" % j["key"]), encoding="utf-8")


# ─────────────────────────── 推收據:稀疏工作樹(只取收據夾,不再整倉 checkout)───────────────────────────
EVID = "VeritasIntelligenceAnalytics/docs/handoff/evidence/fastrun"


def push(out: Path, stamp: str, repo: Path = None) -> str:
    """origin/main 的稀疏工作樹(--no-checkout + sparse-checkout 只取 evidence/fastrun)→ 推 intake/fastrun-<stamp>;工作夾不動。
    前版整倉 checkout(現在 1,500+ 檔)是桌機上最慢的一步。"""
    repo = Path(repo or REPO)
    br, wt = "intake/fastrun-%s" % stamp, Path(tempfile.gettempdir()) / ("via_fastrun_%s" % stamp)

    def git(*a, cwd=None):
        return subprocess.run(["git", "-C", str(cwd or repo), *a], capture_output=True, text=True, encoding="utf-8", errors="replace")
    BASE.say("推收據 · git fetch origin main")
    if git("fetch", "origin", "main").returncode != 0:
        return "[推送失敗] git fetch 不過"
    r = git("worktree", "add", "--no-checkout", "-b", br, str(wt), "origin/main")
    if r.returncode != 0:
        return "[推送失敗] worktree:" + r.stderr.strip()[:160]
    try:
        for a in (("sparse-checkout", "set", "--no-cone", "/%s/" % EVID), ("checkout",)):
            r = git(*a, cwd=wt)
            if r.returncode != 0:
                return "[推送失敗] %s:%s" % (a[0], r.stderr.strip()[:160])
        dst = wt / EVID / stamp
        dst.mkdir(parents=True, exist_ok=True)
        n = 0
        for f in sorted(out.iterdir()):
            if f.is_file() and f.suffix in (".txt", ".json") and "names_local" not in f.name:
                (dst / f.name).write_text(BASE.scrub(f.read_text(encoding="utf-8", errors="replace")), encoding="utf-8", newline="\n")
                n += 1
        git("add", "--sparse", "-A", EVID, cwd=wt)
        c = git("commit", "-qm", "FastRun evidence %s (receipts only)" % stamp, cwd=wt)
        if c.returncode != 0:
            return "[推送失敗] commit:" + (c.stderr or c.stdout).strip()[:160]
        BASE.say("推收據 · %d 檔 · git push %s" % (n, br))
        p = git("push", "-u", "origin", br, cwd=wt)
        return ("[已推] 分支 %s(%d 檔)" % (br, n)) if p.returncode == 0 else "[推送失敗] " + p.stderr.strip()[:160]
    finally:
        git("worktree", "remove", "--force", str(wt))
        git("branch", "-D", br)


# ─────────────────────────── 入口 ───────────────────────────
def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        return via_vcgc(argv)
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
    fj, fs = fid_jobs(fid_dirs(a.dirs), out) if "fidelity" in sets else ([], [])
    skipped += fs
    _DONE["total"] = len(jobs) + len(fj) + (3 if "env" in sets else 0)
    stop = threading.Event()
    wt = threading.Thread(target=_writer, args=(stop,), daemon=True)
    wt.start()
    lanes = BASE.lanes_for(a.lanes)
    t0 = time.time()
    BASE.say("%s · 組 %s · %d 項 · %d 道 · 全文 %s" % (TAG, ",".join(sets), _DONE["total"], lanes, out))
    results = []
    try:
        if "env" in sets:                                # 依序(後一步要前一步的結果),先跑:裝好的套件給後面的組用
            r, s = run_env(out, a.timeout)
            results += r
            skipped += s
        _DONE["stage"] = "並行"
        if jobs or fj:
            results += BASE.run_all(jobs + fj, out, max(1, min(lanes, len(jobs) + len(fj))), a.timeout, beat=10 ** 9)
        fid_collect(fj, out)
    finally:
        stop.set()
        PROGRESS.unlink(missing_ok=True)
    worst, lines = BASE.summarize(results, skipped, out, t0, lanes)
    BASE.say(lines[0])
    for s in skipped:
        BASE.say("略過 · " + s)
    if a.push:
        BASE.say(push(out, stamp))
    return {"GREEN": 0, "GRAY": 2, "YELLOW": 2}.get(worst, 1)


_BASE_RUN_JOB0 = BASE.run_job                            # 前版原函式(前版自測照它原本的跑)


def _install():
    BASE.run_job = run_job                               # v0100 run_all 叫模組全域 run_job → 換成即時版
    BASE.HERE, BASE.TAG = HERE, TAG                      # 經 VCGC 重新進來時跑本檔


_install()


# ─────────────────────────── 自測(全在暫存夾 · 不跑真工具)───────────────────────────
def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + name + ((" · " + str(note)[:300]) if note and not cond else ""), flush=True)

    print("[計] %s 自測開始(本版 8 項 · 前版 %s)" % (TAG, PRIOR_PATH.name), flush=True)
    chk("T1 鏈:前版 v0101 · 本體 v0100;run_all 用的 run_job 換成即時版 · 重新進來跑本檔",
        PRIOR_PATH.name == "VIA_FastRun_v0101.py" and BASE.run_job is run_job and BASE.HERE == HERE and Path(BASE.__file__).name == "VIA_FastRun_v0100.py")
    with tempfile.TemporaryDirectory(prefix="fastrun102_") as td:
        out = Path(td)
        kid = out / "kid.py"
        kid.write_text("import sys,time\nfor i in range(3):\n    print('  D%03d·abc p1 VERIFIED T0' % (i+1), flush=True)\n    time.sleep(0.3)\n"
                       "time.sleep(float(sys.argv[1]))\nprint('{\"lamp\": \"GREEN\"}')\n", encoding="utf-8")
        _DONE.update(n=0, total=2, stage="自測")
        seen = []
        th = threading.Thread(target=lambda: [seen.append(snapshot()) or time.sleep(0.4) for _ in range(6)], daemon=True)
        th.start()
        r1 = run_job({"name": "kid:ok", "argv": [sys.executable, str(kid), "0.5"], "env": "own", "tot": 3}, out, 30)
        th.join()
        docs = max((x["docs"] for s in seen for x in s["running"] if x["name"] == "kid:ok"), default=0)
        chk("T2 即時版:輸出邊跑邊寫檔 · 進度看得到第幾份 · 跑完 rc 0 · 全文 .log.txt 照前版格式",
            r1["rc"] == 0 and docs >= 1 and (out / "kid_ok.log.txt").read_text(encoding="utf-8").startswith("# kid:ok") and not list(out.glob("*.live")), (r1, docs))
        t = time.time()
        r2 = run_job({"name": "kid:slow", "argv": [sys.executable, str(kid), "30"], "env": "own", "timeout": 2}, out, 30)
        chk("T3 上限到了停整棵子行程 · rc 124 · 不等滿 30 秒 · 燈不是綠", r2["rc"] == 124 and time.time() - t < 15 and r2["lamp"] != "GREEN", (r2["rc"], round(time.time() - t, 1)))
        chk("T4 建不出 wheel 的套件拆得出來", failed_wheels("x\n  ERROR: Failed building wheel for jieba\nFailed building wheel for foo-bar\n") == ["foo-bar", "jieba"])
        a = out / "A"
        a.mkdir()
        (a / "x.pdf").write_bytes(b"%PDF-1.4")
        (a / "sub").mkdir()
        (a / "sub" / "y.pdf").write_bytes(b"%PDF-1.4")
        (a / "n.docx").write_bytes(b"x")
        js, sk = fid_jobs([("reports", a), ("knowledge", out / "沒有這個夾")], out)
        chk("T5 量測工作:頂層 PDF 數當總份數 · 找不到的夾略過(不是綠)· 檔案種類數寫進 counts",
            len(js) == 1 and js[0]["tot"] == 1 and js[0]["env"] == "own" and sk == ["fidelity:knowledge(找不到資料夾)"]
            and "含子夾 PDF 2" in (out / "fidelity_reports_counts.txt").read_text(encoding="utf-8"), (js, sk))
        snap = {"done": 1, "total": 4, "stage": "並行", "running": [{"name": "fidelity:reports", "secs": 12, "timeout": 1800, "docs": 3, "tot": 40}]}
        l1, l2 = render(snap, 75.2), render(None, 9.0)
        chk("T6 進度條一行(不換行 · 不超寬)· 有第幾份 · VCGC 開場也有轉圈秒數",
            "\n" not in l1 and len(l1) <= 118 and "第 3/40 份" in l1 and "1/4" in l1 and "VCGC 開場中" in l2 and "9s" in l2, (l1, l2))
    with tempfile.TemporaryDirectory(prefix="fastrun102g_") as td:
        g = lambda *x, cwd: subprocess.run(["git", *x], cwd=str(cwd), capture_output=True, text=True)
        td = Path(td)
        g("init", "-q", "--bare", "-b", "main", str(td / "origin.git"), cwd=td)
        g("clone", "-q", str(td / "origin.git"), str(td / "work"), cwd=td)
        w = td / "work"
        for k in range(30):
            (w / "big").mkdir(exist_ok=True)
            (w / "big" / ("f%02d.txt" % k)).write_text("x" * 100, encoding="utf-8")
        g("-c", "user.email=t@t", "-c", "user.name=t", "add", "-A", cwd=w)
        g("-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "base", cwd=w)
        g("push", "-q", "origin", "HEAD:main", cwd=w)
        o = td / "out"
        o.mkdir()
        (o / "summary.txt").write_text("綠 · ~ 測", encoding="utf-8")
        (o / "FIDELITY_names_local.json").write_text("{}", encoding="utf-8")
        env0 = {k: os.environ.get(k) for k in ("GIT_AUTHOR_NAME", "GIT_AUTHOR_EMAIL", "GIT_COMMITTER_NAME", "GIT_COMMITTER_EMAIL")}
        os.environ.update(GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")
        try:
            msg = push(o, "ST", repo=w)
        finally:
            for k, v in env0.items():
                os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)
        ls = g("ls-tree", "-r", "--name-only", "intake/fastrun-ST", cwd=td / "origin.git").stdout.split()
        chk("T8 稀疏推送:遠端分支有收據 · 不含檔名對照 · 原有檔照留 · 暫存工作樹與本地分支都清掉",
            msg.startswith("[已推]") and (EVID + "/ST/summary.txt") in ls and not any("names_local" in x for x in ls) and "big/f00.txt" in ls
            and not (Path(tempfile.gettempdir()) / "via_fastrun_ST").exists() and "intake/fastrun-ST" not in g("branch", cwd=w).stdout, (msg, ls[:5]))
    src = HERE.read_text(encoding="utf-8")
    chk("T7 檔面:加速器橋 · 零 TA-Lib · 本行程不寫同意閘 · 沒有寫死的使用者名稱路徑",
        "[VIA:ACCEL-BRIDGE:v0100]" in src and not re.search(r"^\s*(import|from)\s+talib", src, re.M)
        and not re.search(r"os\.environ\[[\"']VIA_(NET|SCRAPE)_CONSENT", src) and not re.search(r"[A-Z]:\\\\Users\\\\[a-z]", src))
    n = sum(ok)
    print("[計] %s 自測 %d/%d · %s" % (TAG, n, len(ok), "PASS" if n == len(ok) else "FAIL"), flush=True)
    print("[前版] %s 自測(原函式)" % PRIOR_PATH.name, flush=True)
    keep = BASE.run_job
    BASE.run_job = _BASE_RUN_JOB0
    try:
        rc_prior = PRIOR.selftest()
    finally:
        BASE.run_job = keep
    print("[計] %s 自測 OK %d · FAIL %d · 前版 rc=%s" % (TAG, n, len(ok) - n, rc_prior), flush=True)
    return 0 if n == len(ok) and rc_prior == 0 else 1



if __name__ == "__main__":
    raise SystemExit(main())
