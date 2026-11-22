#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VIA_FastRun v0100 — 一支 Python 快跑器:VCGC 只過一次閘,各系統的唯讀檢查並行跑,每項只印一行,全文存 .txt(可推 intake 分支)

操作員 2026-11-22:「GENERATE A FAST CODE IN PY AND LAUNCH IT TO RUN THE SYSTEM TO GET THE OUTPUT IN TOKEN SAVING WAYS」。
量過(PR 723 主機實跑 · 容器對照):
  · 主機上每個 `via-vcgc run <引擎> <動詞>` 要 110~311 秒,容器約 6 秒,其中引擎本身只佔 0.1 秒;
    時間花在 VCGC 每次的開場(省 Token 第一步 · 政策冊 · 流程閘 · 背景監控)——五個動詞就付五次。
  · 上一版 PS 一行把日誌存成 .log,被 .gitignore 的 *.log 擋掉,推上去只剩摘要。
本支:
  · 自己不是經 VCGC 起的 → 經 VCGC `run` 重新進來一次(VCGC 的開場與流程閘只付一次;VCGC 擋 = 照擋、印最後幾行就停)。
  · 在 VCGC 裡:各組工作開子行程直跑各系統自己的入口,依機器核數同時 3~6 道;
      nlp → SUP_MDL866 尾版(VCGC 收的引擎,子行程沿用這一輪 VCGC 的入口旗標)
      vrn → VRN_SystemManager 尾版、vdf → VDF_SystemManager 尾版(各系統自己的入口:子行程拿掉 VCGC 的旗標,互不干涉)
    每 20 秒一行心跳;每支逾時另計(預設 900 秒)。
  · 省 Token 輸出:每項一行「名 · rc · 秒 · 燈 · 要點」,stdout 的 JSON 取燈與要點(stderr 的警告不混進來);
    摘要帶三數(應跑 · 已跑 · 略過);全文每項一個 <名>.log.txt + summary.txt + summary.json,
    放在 VIA_Reports/fastrun/<時間>(不進版控)。
  · --push:用 TEMP 的 git worktree(從 origin/main)把本輪的 .txt / .json 推到 intake/fastrun-<時間>(家目錄路徑換成 ~),
    不動工作夾、不併 main。只收程式結構 / 收據,不碰市場資料。
用法:python VIA_FastRun_v0100.py [--set all|nlp,vrn,vdf] [--lanes N] [--timeout 秒] [--push] [--selftest]
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
except Exception:  # noqa: BLE001
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

TAG = "VIA_FastRun v0100"
MARK = "[快跑]"
HERE = Path(__file__).resolve()
VIA = next((p for p in HERE.parents if (p / "supportive modules").is_dir() and (p / "functional modules").is_dir()), HERE.parents[3])
REPO = VIA.parent
VCGC_FLAGS = ("VIA_FROM_VCGC", "VIA_GATE_PASSED_HEAD", "VIA_GATE_PASSED_AT", "VIA_GATE_PASSED_LINE")
KEYS = ("lamp", "gate", "truncated", "scanned_files", "records", "missing", "help_missing")
ORDER = {"GREEN": 0, "GRAY": 1, "YELLOW": 2, "RED": 3}


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


def tail(folder: Path, family: str):
    c = [p for p in Path(folder).glob(family + "_v*.py") if _vnum(p) >= 0]
    return max(c, key=_vnum) if c else None


def say(text: str) -> None:
    print(f"{MARK} {text}", flush=True)


# ─────────────────────────── 工作清單 ───────────────────────────
def jobs_for(sets: list, out: Path, via: Path = VIA) -> tuple:
    """回 (jobs, skipped)。每個 job:name · argv · env 模式('vcgc' 沿用 VCGC 旗標 / 'own' 拿掉 VCGC 旗標)。"""
    jobs, skipped = [], []
    py = sys.executable
    if "nlp" in sets:
        t = tail(via / "supportive modules" / "70_VRN_Rules", "SUP_MDL866_VIAUnifiedNLPOrchestrator")
        doc = next((p for p in (via / "docs/handoff/ai/VIA_WeeklyRework_Review_20261122.md", via.parent / "AGENTS.md", via.parent / "CLAUDE.md") if p.is_file()), None)
        intake = via / "functional modules/VRN/references/intake/NLP_Desktop_b20261122"
        if t is None:
            skipped.append("nlp:*(SUP_MDL866 尾版不在)")
        else:
            jobs.append({"name": "nlp:intake-status", "argv": [py, str(t), "intake-status"], "env": "vcgc"})
            if doc:
                jobs.append({"name": "nlp:reconstruct", "argv": [py, str(t), "reconstruct", str(doc), "--out", str(out / "nlp_reconstruct")], "env": "vcgc"})
                jobs.append({"name": "nlp:unified", "argv": [py, str(t), "unified", str(doc), "--out", str(out / "nlp_unified")], "env": "vcgc"})
            else:
                skipped += ["nlp:reconstruct(沒有輸入文件)", "nlp:unified(沒有輸入文件)"]
            if intake.is_dir():
                jobs.append({"name": "nlp:scan-folder", "argv": [py, str(t), "scan-folder", str(intake), "--out", str(out / "nlp_scan")], "env": "vcgc"})
            else:
                skipped.append("nlp:scan-folder(收容夾不在)")
            jobs.append({"name": "nlp:semantic", "argv": [py, str(t), "semantic", "--text", "VIA 快跑器 主機實測 · VIA FastRun host check", "--runtime", str(out / "nlp_vusipe")], "env": "vcgc"})
    for key, fam, verbs in (("vrn", "VRN_SystemManager", ("version", "health", "verbs")), ("vdf", "VDF_SystemManager", ("version", "health"))):
        if key not in sets:
            continue
        sysdir = via / "functional modules" / key.upper()
        t = tail(sysdir, fam)
        if t is None:
            skipped.append(f"{key}:*({fam} 尾版不在)")
            continue
        for v in verbs:
            jobs.append({"name": f"{key}:{v}", "argv": [py, str(t), v, "--json"], "env": "own"})
    return jobs, skipped


def child_env(mode: str) -> dict:
    env = dict(os.environ)
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    env["VIA_NO_OPEN"] = "1"
    if mode == "own":                                   # 別的系統的入口:不帶 VCGC 的旗標(系統獨立)
        for k in VCGC_FLAGS:
            env.pop(k, None)
    return env


# ─────────────────────────── 取燈與要點 ───────────────────────────
def find_json(text: str):
    text = (text or "").strip()
    try:
        return json.loads(text)
    except ValueError:
        pass
    for m in re.finditer(r"^\{\s*$", text, re.M):                     # 前面混了別的行:從獨立一行的 { 開始試
        try:
            return json.loads(text[m.start():])
        except ValueError:
            continue
    return None


def brief(job: dict, rc: int, secs: float, stdout: str, stderr: str) -> dict:
    body = find_json(stdout)
    lamp, bits = None, []
    if isinstance(body, dict):
        lamp = body.get("lamp")
        if not lamp and "gate" in body:
            lamp = {"PASS": "GREEN", "HOLD": "YELLOW"}.get(str(body["gate"]).upper(), "RED")
        for k in KEYS:
            if k in body and k != "lamp" and body[k] not in (None, "", [], {}):
                bits.append(f"{k}={json.dumps(body[k], ensure_ascii=False)[:60]}")
        why = body.get("why")
        if why:
            bits.append("why=" + (why if isinstance(why, str) else "; ".join(map(str, why)))[:90])
        for k in ("red", "yellow"):
            if body.get(k):
                bits.append(f"{k}={len(body[k])}:" + "; ".join(map(str, body[k]))[:80])
    if lamp is None:
        lamp = "GREEN" if rc == 0 else ("YELLOW" if rc == 2 else "RED")
        err = [ln for ln in (stderr or "").splitlines() if ln.strip() and "Warning" not in ln]
        if rc not in (0, 2) and err:
            bits.append("err=" + err[-1].strip()[:140])           # 紅且沒有 JSON:只帶最後一行錯誤(全文在 .txt)
    return {"name": job["name"], "rc": rc, "secs": round(secs, 1), "lamp": lamp, "bits": bits}


def line_of(r: dict) -> str:
    s = f"{r['name']} · rc {r['rc']} · {r['secs']}s · {r['lamp']}"
    return (s + " · " + " · ".join(r["bits"]))[:240] if r["bits"] else s


# ─────────────────────────── 跑 ───────────────────────────
def run_job(job: dict, out: Path, timeout: int) -> dict:
    t0 = time.time()
    try:
        p = subprocess.run(job["argv"], capture_output=True, text=True, encoding="utf-8", errors="replace",
                           env=child_env(job["env"]), cwd=str(REPO), timeout=timeout)
        rc, so, se = p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired as exc:
        rc = 124
        so = exc.stdout.decode("utf-8", "replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        se = f"逾時 {timeout} 秒,已停"
    except OSError as exc:
        rc, so, se = 127, "", f"{type(exc).__name__}: {exc}"
    secs = time.time() - t0
    safe = re.sub(r"[^\w.-]+", "_", job["name"])
    (out / f"{safe}.log.txt").write_text(f"# {job['name']}\n# argv: {' '.join(job['argv'])}\n# rc {rc} · {secs:.1f}s\n\n## stdout\n{so}\n\n## stderr\n{se}\n",
                                        encoding="utf-8")
    return brief(job, rc, secs, so, se)


def lanes_for(n: int | None) -> int:
    if n:
        return max(1, min(6, n))
    return max(3, min(6, (os.cpu_count() or 4) // 2))                # CLAUDE.md:依機器能力同時 3~6 道


def run_all(jobs: list, out: Path, lanes: int, timeout: int, beat: float = 20.0) -> list:
    running, lock, done = {}, threading.Lock(), threading.Event()

    def one(job):
        with lock:
            running[job["name"]] = time.time()
        try:
            r = run_job(job, out, timeout)
        finally:
            with lock:
                running.pop(job["name"], None)
        say(line_of(r))
        return r

    def heartbeat():
        while not done.wait(beat):
            with lock:
                now = time.time()
                busy = ", ".join(f"{k} {now - v:.0f}s" for k, v in running.items())
            if busy:
                say("心跳 · 跑著:" + busy)

    hb = threading.Thread(target=heartbeat, daemon=True)
    hb.start()
    try:
        with ThreadPoolExecutor(max_workers=lanes) as ex:
            results = list(ex.map(one, jobs))
    finally:
        done.set()
    return results


def summarize(results: list, skipped: list, out: Path, t0: float, lanes: int) -> tuple:
    worst = max((r["lamp"] for r in results), key=lambda x: ORDER.get(x, 3), default="GRAY")
    if skipped and ORDER.get(worst, 0) < ORDER["YELLOW"]:
        worst = "YELLOW"                                               # 略過 = 黃(SKIP 不是綠)
    head = (f"{TAG} · {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} · {worst} · 應跑 {len(results) + len(skipped)} · 已跑 {len(results)} · "
            f"略過 {len(skipped)} · {lanes} 道 · {time.time() - t0:.0f}s")
    lines = [head] + [line_of(r) for r in results] + [f"略過 · {s}" for s in skipped] + [f"全文 · {out}"]
    (out / "summary.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (out / "summary.json").write_text(json.dumps({"tool": TAG, "lamp": worst, "results": results, "skipped": skipped, "out": str(out)},
                                                 ensure_ascii=False, indent=1), encoding="utf-8")
    return worst, lines


def scrub(text: str) -> str:
    home = str(Path.home())
    return text.replace(home.replace("\\", "\\\\"), "~").replace(home, "~") if home and home != "/" else text


def push(out: Path, stamp: str) -> str:
    """TEMP 的 worktree(origin/main)→ docs/handoff/evidence/fastrun/<stamp>/ → 推 intake/fastrun-<stamp>;工作夾不動。"""
    br, wt = f"intake/fastrun-{stamp}", Path(tempfile.gettempdir()) / f"via_fastrun_{stamp}"

    def git(*a, cwd=REPO):
        return subprocess.run(["git", "-C", str(cwd), *a], capture_output=True, text=True)
    if git("fetch", "-q", "origin", "main").returncode != 0:
        return "[推送失敗] git fetch 不過"
    r = git("worktree", "add", "-q", "-b", br, str(wt), "origin/main")
    if r.returncode != 0:
        return "[推送失敗] worktree:" + r.stderr.strip()[:120]
    try:
        dst = wt / "VeritasIntelligenceAnalytics" / "docs" / "handoff" / "evidence" / "fastrun" / stamp
        dst.mkdir(parents=True, exist_ok=True)
        for f in sorted(out.iterdir()):
            if f.is_file() and f.suffix in (".txt", ".json"):
                (dst / f.name).write_text(scrub(f.read_text(encoding="utf-8", errors="replace")), encoding="utf-8")
        git("add", "-A", cwd=wt)
        git("commit", "-qm", f"FastRun evidence {stamp} (receipts only)", cwd=wt)
        p = git("push", "-q", "-u", "origin", br, cwd=wt)
        return f"[已推] 分支 {br}" if p.returncode == 0 else "[推送失敗] " + p.stderr.strip()[:160]
    finally:
        git("worktree", "remove", "--force", str(wt))
        git("branch", "-D", br)


# ─────────────────────────── 入口 ───────────────────────────
def via_vcgc(argv: list) -> int:
    """不是經 VCGC 起的 → 經 VCGC run 進來一次;只把帶 [快跑] 的行印出來,VCGC 開場全文存檔。"""
    v = tail(VIA / "supportive modules" / "registry", "CGC_MDL149_VeritasCentralGovernanceConsole")
    if v is None:
        print(f"{MARK} VCGC 主控台不在 → 停(rc 3)")
        return 3
    env = dict(os.environ, VIA_FROM_VCGC="YES", PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
    rel = HERE.relative_to(VIA).as_posix()
    p = subprocess.Popen([sys.executable, str(v), "run", rel, *argv], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         text=True, encoding="utf-8", errors="replace", env=env, cwd=str(REPO))
    keep = []
    for ln in p.stdout:
        keep.append(ln)
        if ln.startswith(MARK):
            print(ln, end="", flush=True)
    rc = p.wait()
    wrap = VIA / "VIA_Reports" / "fastrun" / "_vcgc_wrapper_last.txt"
    wrap.parent.mkdir(parents=True, exist_ok=True)
    wrap.write_text("".join(keep), encoding="utf-8")
    if not any(ln.startswith(MARK) for ln in keep):                   # VCGC 擋在前面:印最後幾行讓人看得到原因
        print(f"{MARK} VCGC 沒有放行(rc {rc})· 最後幾行:")
        for ln in keep[-5:]:
            print("   " + ln.rstrip()[:200])
        return 3 if rc in (0, 2) else rc
    return rc


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        return via_vcgc(argv)
    ap = argparse.ArgumentParser(prog=TAG)
    ap.add_argument("--set", default="all")
    ap.add_argument("--lanes", type=int)
    ap.add_argument("--timeout", type=int, default=900)
    ap.add_argument("--push", action="store_true")
    a = ap.parse_args(argv)
    sets = ["nlp", "vrn", "vdf"] if a.set == "all" else [s.strip() for s in a.set.split(",") if s.strip()]
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = VIA / "VIA_Reports" / "fastrun" / stamp
    out.mkdir(parents=True, exist_ok=True)
    jobs, skipped = jobs_for(sets, out)
    lanes = lanes_for(a.lanes)
    t0 = time.time()
    say(f"{TAG} · 組 {','.join(sets)} · {len(jobs)} 項 · {lanes} 道 · 全文 {out}")
    results = run_all(jobs, out, lanes, a.timeout)
    worst, lines = summarize(results, skipped, out, t0, lanes)
    say(lines[0])
    for s in skipped:
        say("略過 · " + s)
    if a.push:
        say(push(out, stamp))
    return {"GREEN": 0, "GRAY": 2, "YELLOW": 2}.get(worst, 1)


# ─────────────────────────── 自測 ───────────────────────────
def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)[:300]) if note and not cond else ''}", flush=True)

    print(f"=== {TAG} 自測(暫存夾 · 假子行程 · 零網路)===")
    with tempfile.TemporaryDirectory(prefix="via_fastrun_") as td:
        t = Path(td)
        good = t / "good.py"
        good.write_text("import json,sys\nprint('雜訊一行')\nprint(json.dumps({'lamp':'YELLOW','why':['詞庫 ABSENT'],'records':1},ensure_ascii=False,indent=1))\n"
                        "sys.stderr.write('SyntaxWarning: x\\n')\nsys.exit(2)\n", encoding="utf-8")
        bad = t / "bad.py"
        bad.write_text("import sys\nprint('開場')\nraise ModuleNotFoundError(\"No module named 'jieba'\")\n", encoding="utf-8")
        slow = t / "slow.py"
        slow.write_text("import time\ntime.sleep(5)\n", encoding="utf-8")
        envp = t / "env.py"
        envp.write_text("import json,os\nprint(json.dumps({'lamp':'GREEN','flags':[k for k in os.environ if k.startswith('VIA_FROM_VCGC') or k.startswith('VIA_GATE')]}))\n",
                        encoding="utf-8")
        out = t / "out"
        out.mkdir()
        keep = {k: os.environ.get(k) for k in VCGC_FLAGS}
        os.environ["VIA_FROM_VCGC"], os.environ["VIA_GATE_PASSED_HEAD"] = "YES", "abc"
        try:
            jobs = [{"name": "a:good", "argv": [sys.executable, str(good)], "env": "vcgc"},
                    {"name": "b:bad", "argv": [sys.executable, str(bad)], "env": "vcgc"},
                    {"name": "c:own", "argv": [sys.executable, str(envp)], "env": "own"},
                    {"name": "d:vcgc", "argv": [sys.executable, str(envp)], "env": "vcgc"}]
            buf_lines = []
            real_say = globals()["say"]
            globals()["say"] = lambda s: buf_lines.append(s)
            try:
                res = run_all(jobs, out, 3, 60, beat=0.2)
                slow_r = run_job({"name": "e:slow", "argv": [sys.executable, str(slow)], "env": "vcgc"}, out, 1)
            finally:
                globals()["say"] = real_say
        finally:
            for k, v in keep.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
        r = {x["name"]: x for x in res}
        chk("① stdout 混雜訊也取得到 JSON 的燈與要點;stderr 的警告不混進要點", r["a:good"]["lamp"] == "YELLOW" and r["a:good"]["rc"] == 2
            and any("ABSENT" in b for b in r["a:good"]["bits"]) and any("records=1" in b for b in r["a:good"]["bits"])
            and not any("Warning" in b for b in r["a:good"]["bits"]), r["a:good"])
        chk("② 紅且沒有 JSON:只帶最後一行錯誤(jieba)", r["b:bad"]["lamp"] == "RED" and any("jieba" in b for b in r["b:bad"]["bits"]), r["b:bad"])
        own = json.loads((out / "c_own.log.txt").read_text(encoding="utf-8").split("## stdout\n", 1)[1].split("\n\n## stderr", 1)[0])
        vc = json.loads((out / "d_vcgc.log.txt").read_text(encoding="utf-8").split("## stdout\n", 1)[1].split("\n\n## stderr", 1)[0])
        chk("③ 系統獨立:VRN / VDF 的子行程拿掉 VCGC 旗標;NLP(VCGC 收的引擎)沿用", own["flags"] == [] and set(vc["flags"]) >= {"VIA_FROM_VCGC", "VIA_GATE_PASSED_HEAD"},
            (own, vc))
        chk("④ 每項全文存成 .log.txt(不是 .log:*.log 會被 .gitignore 擋)", all((out / f"{n}.log.txt").is_file() for n in ("a_good", "b_bad", "c_own", "d_vcgc"))
            and not list(out.glob("*.log")))
        chk("⑤ 每項只印一行(≤ 240 字)", all(len(line_of(x)) <= 240 and "\n" not in line_of(x) for x in res))
        chk("⑥ 逾時會停、記 rc 124、燈紅", slow_r["rc"] == 124 and slow_r["lamp"] == "RED", slow_r)
        worst, lines = summarize(res, ["x:y(測試)"], out, time.time(), 3)
        chk("⑦ 摘要三數:應跑 = 已跑 + 略過;有紅 → 紅", worst == "RED" and "應跑 5 · 已跑 4 · 略過 1" in lines[0] and (out / "summary.json").is_file(), lines[0])
        w2, l2 = summarize([dict(r["c:own"])], ["x:y"], out, time.time(), 3)
        chk("⑧ 全綠但有略過 → 黃(SKIP 不是綠)", w2 == "YELLOW", l2[0])
        chk("⑨ 道數:指定就夾在 1~6;沒指定依核數 3~6", lanes_for(9) == 6 and lanes_for(1) == 1 and 3 <= lanes_for(None) <= 6)
        nap = t / "nap.py"
        nap.write_text("import time\ntime.sleep(1.2)\n", encoding="utf-8")
        beats = []
        globals()["say"] = lambda s: beats.append(s)
        try:
            run_all([{"name": "f:nap", "argv": [sys.executable, str(nap)], "env": "vcgc"}], out, 1, 60, beat=0.2)
        finally:
            globals()["say"] = real_say
        chk("⑩ 心跳:跑超過一個心跳間隔就印「心跳 · 跑著:<名>」", any(s.startswith("心跳") and "f:nap" in s for s in beats), beats)
        home = str(Path.home())
        chk("⑪ 推送前把家目錄換成 ~(含 JSON 裡的雙反斜線寫法)", home in ("", "/") or (scrub(f"a {home}/x") == "a ~/x"))
    jobs, skipped = jobs_for(["nlp", "vrn", "vdf"], Path(tempfile.gettempdir()) / "via_fastrun_plan")
    names = [j["name"] for j in jobs]
    chk("⑫ 真樹:三組都找得到尾版(nlp 五動詞 · vrn 三 · vdf 二)、沒有略過", len([n for n in names if n.startswith("nlp:")]) == 5
        and {"vrn:version", "vrn:health", "vrn:verbs", "vdf:version", "vdf:health"} <= set(names) and not skipped, (names, skipped))
    fams = [(Path(j["argv"][1]), re.sub(r"_v\d{4}$", "", Path(j["argv"][1]).stem)) for j in jobs]
    chk("⑬ 尾版一律用 glob 取磁碟上最大版號(不寫死版號)", all(f == tail(f.parent, fam) for f, fam in fams), [f.name for f, _ in fams][:3])
    src = HERE.read_text(encoding="utf-8")
    body = src.split("def selftest", 1)[0]
    chk("⑭ 加速器橋在 · 不碰 TA-Lib · 不 import 網路套件(推送只用 git)", "[VIA:ACCEL-BRIDGE:v0100]" in src and "talib" not in body.lower()
        and not re.search(r"^\s*(import|from)\s+(requests|urllib|socket|http)\b", src, re.M))
    chk("⑮ 不在檔案裡設 VCGC 旗標(只在經 VCGC run 進來的那一個子行程環境裡設)", body.count('VIA_FROM_VCGC="YES"') == 1 and "os.environ[\"VIA_FROM_VCGC\"]" not in body)
    print(f"  [計] {TAG} 自測 {sum(ok)}/{len(ok)} · {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
