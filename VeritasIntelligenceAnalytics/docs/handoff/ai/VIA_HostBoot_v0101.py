#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VIA_HostBoot v0101 — 薄尾(v0100 一字不動):桌機一支 PS 銜接全部 · 動詞 fnc · bak · vdf · --push 收據回推(遠端判讀)

操作員 2026-11-25:「網路工具也要強制加入 · C:\\Users\\tonyk\\OneDrive\\Desktop\\測試\\VCGC · 銜接 ps · 遠端操作」。
雲端工作階段連不到桌機(Remote Control 資料夾清單是空的)→ 遠端操作改成:桌機跑 → 收據(燈 · 數字 · 雜湊;家目錄換 ~)
經 VIA_FastRun 尾版的 push 推到 intake/fastrun-<時間> → AI 端 git fetch 讀。不推任何資料內容(資料邊界)。

用法:python VIA_HostBoot_v0101.py --repo <倉> <動詞> [動詞參數…] [--push] [--sync] [--fnc-dir <夾>]
  fnc [FNC 動詞…]   VCGC FNC 封包尾版(預設 ~/OneDrive/Desktop/測試/VCGC/VIA_VCGC_FNC_v*.zip):py -3 -X utf8 <zip> <動詞>
                    (沒給 = host:Windows 在地驗收)。封包自己驗 SHA、建專用環境、寫 receipts/<執行碼>/;本檔只叫它、收收據。
  bak [參數…]       VIA_DailyBackup 尾版 full --via <倉>/VeritasIntelligenceAnalytics(三閘並行 → 補裝 → Fail-Closed → 備份)
  vdf [參數…]       VDF_LocalIntegrateLaunch 尾版 --repo <倉>(VCGC 健康 → via_vdf 境 → 三步盤點 → 本機 claude)
  vdfp [--branch B] VDF 參數正本 / 衍生冊 / 引擎合併計畫的桌機實測:TEMP 另開 git worktree 指 origin/<B>(你的工作夾不動),
                    在裡面依序跑 VDF_ENG053 尾版 --selftest · unify · derive · consolidate,再跑 VCGC via_params_central 尾版
                    --selftest · vdf-master(只讀匯總 VDF 正本;全唯讀),收 SUMMARY,拆 worktree
  沒動詞            前版 v0100(同步 → 快跑器)
  vdf3 [--branch B] [--live]
                    三期蒸餾 + 排程的桌機實測(在你的真倉跑,因為資料庫與湖在倉的 VIA_Reports 底下):照前版規則暫時切到 origin/<B>
                    (已追蹤檔有改動 = 停不碰 · 擋路的未追蹤檔一樣就移除、不一樣搬倉外備份)→ 經 VDF_SystemManager three
                    --selftest · ready · inventory · plan · names · [run --live] · distill · reconcile · bench → 兩邊 schedule list →
                    VCGC schedule run vcgc_vdf_master → 一定切回原分支。沒 --live = 不出網(run 只列指令)。
  fin5y [--branch B] [--live] [--only 代碼,..] [--max N]
                    全部台股近 5 年度財報 → 8 指標(VDF_ENG243):同 vdf3 暫切分支在真倉跑 → --selftest · plan → [--live:probe · fetch] → compute。
                    第一次建議 --live --only 2330,3017,3324 --max 30 先驗;全市場約 1,800 家 × 9 請求 × fin5y.rate_s 秒(預設 3 秒 ≈ 13.5 小時,可斷點續跑)
  --sync            先跑前版的同步(--dry:fetch · 擋路檔 · main 快轉)
  --push            收尾把收據推 intake/fastrun-<時間>(經 VIA_FastRun 尾版 push;工作夾不動)
找檔順序:本檔旁(PS 從分支取到 TEMP 的那一份)→ 倉裡。子行程輸出逐塊直通(安裝閘的 YES 提示照樣看得到、打得進)。
rc:子行程的 rc(推送失敗只印,不改 rc)。
"""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0111] SuperAccel 加速器橋(從 TEMP 跑時改由工作目錄 / VIA_REPO 找倉;graceful) =====
try:
    import os as _sa_os
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_hit = None
    _sa_roots = [_sa_Path(__file__).resolve(), _sa_Path.cwd().resolve()]
    if _sa_os.environ.get("VIA_REPO"):
        _sa_roots.append(_sa_Path(_sa_os.environ["VIA_REPO"]).resolve())
    for _sa_r in _sa_roots:
        for _sa_q in (_sa_r, *_sa_r.parents):
            for _sa_c in (_sa_q / "supportive modules", _sa_q / "VeritasIntelligenceAnalytics" / "supportive modules"):
                if (_sa_c / "VIA_SuperAccel_Module.py").exists():
                    _sa_hit = _sa_c
                    break
            if _sa_hit:
                break
        if _sa_hit:
            break
    if _sa_hit and str(_sa_hit) not in _sa_sys.path:
        _sa_sys.path.insert(0, str(_sa_hit))
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
except Exception:  # noqa: BLE001
    VIA_ACCEL = None  # graceful:加速器缺席零影響(自測會把它記成黃)
# ===== [VIA:ACCEL-BRIDGE:END] =====
# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(操作員 2026-11-25「網路工具也要強制加入」;從 TEMP 跑時改由工作目錄 / VIA_REPO 找倉;graceful) =====
VIA_NET_TOOL_PATH = None
try:
    import os as _nb_os
    from pathlib import Path as _nb_Path
    _nb_roots = [_nb_Path(__file__).resolve(), _nb_Path.cwd().resolve()]
    if _nb_os.environ.get("VIA_REPO"):
        _nb_roots.append(_nb_Path(_nb_os.environ["VIA_REPO"]).resolve())
    for _nb_r in _nb_roots:
        for _nb_q in (_nb_r, *_nb_r.parents):
            for _nb_dir in (_nb_q / "supportive modules" / "network", _nb_q / "VeritasIntelligenceAnalytics" / "supportive modules" / "network"):
                _nb_hits = sorted(_nb_dir.glob("via_net_unified_v*.py")) if _nb_dir.is_dir() else []
                if _nb_hits:
                    VIA_NET_TOOL_PATH = str(_nb_hits[-1])
                    break
            if VIA_NET_TOOL_PATH:
                break
        if VIA_NET_TOOL_PATH:
            break
except Exception:  # noqa: BLE001
    VIA_NET_TOOL_PATH = None


def _via_net():
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT:載入不出網,真的連線才看閘);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        _nb_spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        _nb_mod = _nb_ilu.module_from_spec(_nb_spec)
        _nb_spec.loader.exec_module(_nb_mod)
        return _nb_mod
    except Exception:  # noqa: BLE001
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

FAMILY = "VIA_HostBoot"
VERSION = "v0101"
TAG = f"{FAMILY} {VERSION}"
HERE = Path(__file__).resolve()
_T0 = time.time()
VIA_REL = "VeritasIntelligenceAnalytics"
AI_REL = Path(VIA_REL) / "docs" / "handoff" / "ai"
VDF_REL = Path(VIA_REL) / "functional modules" / "VDF"
VERBS = ("fnc", "bak", "vdf", "vdfp", "vdf3", "fin5y")
MAX_RECEIPT = 2 * 1024 * 1024


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(str(p)).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.parent.glob(FAMILY + "_v*.py") if 0 <= _vnum(p) < _vnum(HERE)), key=_vnum)
_spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem + "_for_" + VERSION, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name):  # 尾版律 TAILAPI:前版公開名稱經本檔轉接
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def say(msg: str) -> None:
    print(f"[{time.time() - _T0:6.1f}s] {msg}", flush=True)


def newest(d: Path, pat: str):
    c = [p for p in d.glob(pat) if _vnum(p) >= 0] if d.is_dir() else []
    return max(c, key=_vnum) if c else None


def staged_root():
    """PS 把分支檔取到 TEMP 時的根(本檔在 <根>/VeritasIntelligenceAnalytics/docs/handoff/ai/)。"""
    try:
        return HERE.parents[3] if HERE.parent.name == "ai" else None
    except IndexError:
        return None


def find_tail(repo: Path, rel: Path, pat: str):
    """本檔旁(TEMP 取出的分支檔)與倉裡兩處比版號,取最大的(同號以本檔旁為先)。"""
    c = [t for t in (newest(r / rel, pat) for r in (staged_root(), repo) if r is not None) if t is not None]
    return max(c, key=_vnum) if c else None


def fnc_zip(fnc_dir=None):
    d = Path(fnc_dir) if fnc_dir else Path.home() / "OneDrive" / "Desktop" / "測試" / "VCGC"
    return newest(d, "VIA_VCGC_FNC_v*.zip"), d


def fnc_python() -> list:
    """FNC 封包要 Python 3.11+:Windows 優先 py -3(封包 CMD 也這樣叫),否則本解譯器。"""
    py = shutil.which("py")
    if py:
        return [py, "-3", "-X", "utf8"]
    return [sys.executable, "-X", "utf8"]


def stream(argv: list, cwd: Path, env: dict, log: Path) -> int:
    """子行程輸出逐塊直通主控台(沒換行的 YES 提示也看得到),同時留尾巴 400 KB 做收據;stdin 繼承(你照樣能打字)。"""
    env = dict(env, PYTHONUNBUFFERED="1", PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
    keep = bytearray()
    p = subprocess.Popen(argv, cwd=str(cwd), env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = getattr(sys.stdout, "buffer", None)
    while True:
        b = p.stdout.read1(4096) if hasattr(p.stdout, "read1") else p.stdout.read(1)
        if not b:
            break
        if out is not None:
            out.write(b)
            out.flush()
        keep += b
        if len(keep) > 400_000:
            del keep[:len(keep) - 400_000]
    rc = p.wait()
    log.write_text(keep.decode("utf-8", errors="replace"), encoding="utf-8")
    return rc


def collect(verb: str, repo: Path, out: Path, fnc_dir=None) -> list:
    """把本輪收據(小檔:燈 · 數字 · 雜湊)抄到 out;FastRun 的 push 只收 .txt / .json,家目錄換 ~。"""
    picks = []
    if verb == "fnc":
        z, d = fnc_zip(fnc_dir)
        runs = sorted((d / "receipts").glob("*"), key=lambda p: p.stat().st_mtime) if (d / "receipts").is_dir() else []
        if runs:
            picks += [p for p in runs[-1].rglob("*.json")]
    elif verb == "bak":
        la = os.environ.get("LOCALAPPDATA")
        bk = (Path(la) / "VIA" / "_via_backups") if la else (Path.home() / "_via_backups")
        picks += [bk / "BACKUP_latest.json"]
        snaps = sorted(p for p in bk.glob("2*") if p.is_dir()) if bk.is_dir() else []
        if snaps:
            picks += [snaps[-1] / "extras" / "GATES.json", snaps[-1] / "extras" / "SHA256SUMS.txt", snaps[-1] / "extras" / "EXTRAS_MANIFEST.json"]
        bs = sorted((repo / VIA_REL / "VIA_Reports" / "books_sync").glob("2*"))
        if bs:
            picks += [bs[-1] / "SUMMARY.json"]
    elif verb == "vdf":
        runs = sorted((repo / VIA_REL / "VIA_Reports" / "vdf_local_integrate").glob("2*"))
        if runs:
            picks += [runs[-1] / "summary.json", runs[-1] / "report.md"]
    done = []
    for i, p in enumerate(picks):
        if p.is_file() and p.stat().st_size <= MAX_RECEIPT:
            name = f"{verb}_{i:02d}_{p.stem}" + (".json" if p.suffix == ".json" else ".txt")
            shutil.copyfile(p, out / name)
            done.append(name)
    return done


def push_receipts(repo: Path, out: Path, stamp: str) -> str:
    fr = newest(repo / AI_REL, "VIA_FastRun_v*.py")
    if fr is None:
        return "[推送略過] 倉裡沒有 VIA_FastRun(先 --sync)"
    try:
        sp = importlib.util.spec_from_file_location("via_fastrun_for_hostboot", fr)
        mod = importlib.util.module_from_spec(sp)
        sys.modules[sp.name] = mod
        sp.loader.exec_module(mod)
        return mod.push(out, stamp, repo)
    except Exception as e:  # noqa: BLE001 - 推送失敗只印,不改 rc
        return f"[推送失敗] {type(e).__name__}: {e}"


def run_vdfp(rest: list, repo: Path, out: Path, env: dict) -> int:
    br = "claude/eloquent-rubin-q01657"
    if "--branch" in rest:
        j = rest.index("--branch")
        br = rest[j + 1]
        del rest[j:j + 2]
    wt = Path(tempfile.gettempdir()) / f"via_vdfp_{out.name}"
    git = lambda *a: subprocess.run(["git", "-C", str(repo), *a], capture_output=True, text=True, encoding="utf-8", errors="replace")  # noqa: E731
    if git("fetch", "-q", "origin", br).returncode != 0:
        say(f"[RED] git fetch origin {br} 失敗")
        return 5
    r = git("worktree", "add", "--detach", str(wt), "FETCH_HEAD")
    if r.returncode != 0:
        say("[RED] worktree:" + r.stderr.strip()[:200])
        return 5
    rc = 0
    try:
        eng = newest(wt / VDF_REL / "engine", "VDF_ENG053_ParamEngineMap_v*.py")
        if eng is None:
            say("[RED] 分支上沒有 VDF_ENG053 尾版")
            return 1
        for i, v in enumerate(rest or ["--selftest", "unify", "derive", "consolidate"]):
            say(f"vdfp · {eng.name} {v}")
            r1 = stream([sys.executable, str(eng), v], wt, dict(env, VIA_REPO=str(wt)), out / f"vdfp_{i}_{v.strip('-')}_console.txt")
            rc = max(rc, r1 if r1 in (0, 1, 2) else 1)
        hub = newest(wt / VIA_REL / "supportive modules" / "registry", "via_params_central_v*.py")
        if hub is not None and not rest:                                  # VDF 自報之後,VCGC 只讀匯總(讀得到 VDF 的 unify 收據)
            for i, v in enumerate(["--selftest", "vdf-master"]):
                say(f"vdfp · {hub.name} {v}")
                r1 = stream([sys.executable, str(hub), v], wt, dict(env, VIA_REPO=str(wt)), out / f"vdfp_vcgc_{i}_{v.strip('-')}_console.txt")
                rc = max(rc, r1 if r1 in (0, 1, 2) else 1)
        for p in sorted((wt / VIA_REL / "VIA_Reports" / "vdf_params").glob("2*/SUMMARY.json")):
            shutil.copyfile(p, out / f"vdfp_{p.parent.name}_SUMMARY.json")
        for p in sorted((wt / VIA_REL / "VIA_Reports" / "vcgc" / "central_params").glob("2*/SUMMARY.json")):
            shutil.copyfile(p, out / f"vdfp_vcgc_{p.parent.name}_SUMMARY.json")
    finally:
        git("worktree", "remove", "--force", str(wt))
    return rc


def run_vdf3(rest: list, repo: Path, out: Path, env: dict) -> int:
    def steps(via: Path, live: bool, extra: list) -> list:
        vm = newest(via / "functional modules" / "VDF", "VDF_SystemManager_v*.py")
        cm = newest(via / "supportive modules" / "registry", "CGC_SystemManager_v*.py")
        st = [[str(vm), "three", v] for v in ("--selftest", "ready", "inventory", "plan", "names")]
        if live:
            st.append([str(vm), "three", "run", "--live"])
        st += [[str(vm), "three", v] for v in ("distill", "reconcile", "bench")]
        return st + [[str(vm), "schedule", "list"], [str(cm), "schedule", "list"], [str(cm), "schedule", "run", "vcgc_vdf_master"]]
    return on_branch(rest, repo, out, env, "vdf3", steps, ("vdf_three", "vcgc/central_params"))


def run_fin5y(rest: list, repo: Path, out: Path, env: dict) -> int:
    def steps(via: Path, live: bool, extra: list) -> list:
        f = newest(via / "functional modules" / "VDF" / "engine", "VDF_ENG243_TWFin5Y_v*.py")
        st = [[str(f), "--selftest"], [str(f), "plan", *extra]]
        if live:
            st += [[str(f), "probe", "--live"], [str(f), "fetch", "--live", *extra]]
        return st + [[str(f), "compute"]]
    return on_branch(rest, repo, out, env, "fin5y", steps, ("vdf_fin5y",))


def on_branch(rest: list, repo: Path, out: Path, env: dict, tag: str, steps_fn, report_dirs: tuple) -> int:
    """暫切 origin/<分支> 在真倉跑(資料在 VIA_Reports / output_hub,不受 git 追蹤),一定切回;已追蹤檔有改動 = 停不碰。"""
    rest = list(rest)
    br = "claude/eloquent-rubin-q01657"
    if "--branch" in rest:
        j = rest.index("--branch")
        br = rest[j + 1]
        del rest[j:j + 2]
    live = "--live" in rest
    extra = [x for x in rest if x != "--live"]
    G = PRIOR.git
    if G(repo, "fetch", "-q", "origin", br)[0] != 0:
        say(f"[RED] git fetch origin {br} 失敗")
        return 5
    ch = PRIOR.tracked_changes(repo)
    if ch:
        say("[停] 倉裡有已追蹤檔的改動,沒有動它們;先提交或還原再跑:")
        for ln in ch[:20]:
            say("   " + ln)
        return 4
    stamp = out.name
    for verb_, rel, bk in PRIOR.clear_blockers(repo, PRIOR.blockers(repo, ["origin/" + br]), stamp):
        say(f"[YELLOW] {verb_} · {rel}" + (f" → {bk}" if bk else ""))
    cur = G(repo, "rev-parse", "--abbrev-ref", "HEAD")[1].strip()
    if G(repo, "switch", "-q", "--detach", "origin/" + br, live=True)[0] != 0:
        say(f"[RED] 切不到 origin/{br}")
        return 5
    say(f"暫時切到 origin/{br}(跑完切回 {cur})")
    t0 = time.time()
    rc = 0
    try:
        via = repo / VIA_REL
        for i, st in enumerate(steps_fn(via, live, extra)):
            name = re.sub(r"[^\w]+", "_", "_".join(x.strip("-") for x in st[1:3]))
            say(f"{tag} · {Path(st[0]).name} {' '.join(st[1:])}")
            r1 = stream([sys.executable, *st], repo, dict(env, VIA_REPO=str(repo)), out / f"{tag}_{i:02d}_{name}_console.txt")
            rc = max(rc, r1 if r1 in (0, 1, 2) else 1)
        for d in report_dirs:
            for p in sorted((via / "VIA_Reports" / d).glob("2*/SUMMARY.json")):
                if p.stat().st_mtime >= t0 - 2:
                    shutil.copyfile(p, out / f"{tag}_{d.replace('/', '_')}_{p.parent.name}_SUMMARY.json")
        for lg in (via / "VIA_Reports" / "vdf_schedule" / "RUN_LEDGER.jsonl", via / "VIA_Reports" / "vcgc_schedule" / "RUN_LEDGER.jsonl",
                   via / "VIA_Reports" / "vdf_three" / "run" / "RUN_LEDGER.jsonl"):
            if lg.is_file():
                (out / f"{tag}_{lg.parent.name}_ledger_tail.txt").write_text("\n".join(lg.read_text(encoding="utf-8").splitlines()[-30:]), encoding="utf-8")
    finally:
        back = "main" if cur in ("HEAD", "") else cur
        G(repo, "switch", "-q", back, live=True)
        say(f"切回 {back}")
    return rc


def run_verb(verb: str, rest: list, repo: Path, fnc_dir=None) -> int:
    env = dict(os.environ, VIA_REPO=str(repo))
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = Path(tempfile.gettempdir()) / f"via_hostboot_{verb}_{stamp}"
    out.mkdir(parents=True, exist_ok=True)
    if verb == "fnc":
        z, d = fnc_zip(fnc_dir)
        if z is None:
            say(f"[RED] {d} 沒有 VIA_VCGC_FNC_v*.zip(--fnc-dir 指定)")
            return 1, None, None
        argv, cwd = fnc_python() + [str(z), *(rest or ["host"])], z.parent
    elif verb in ("vdfp", "vdf3", "fin5y"):
        rc = {"vdfp": run_vdfp, "vdf3": run_vdf3, "fin5y": run_fin5y}[verb](list(rest), repo, out, env)
        (out / f"{verb}_RUN.json").write_text(json.dumps({"tool": TAG, "verb": verb, "rc": rc, "secs": round(time.time() - _T0, 1), "args": rest,
                                                        "accel": VIA_ACCEL is not None, "net": VIA_NET_TOOL_PATH is not None}, ensure_ascii=False, indent=1), encoding="utf-8")
        say(f"{verb} · rc {rc} · 收據 → {out}")
        return rc, out, stamp
    elif verb == "bak":
        t = find_tail(repo, AI_REL, "VIA_DailyBackup_v*.py")
        if t is None:
            say("[RED] 找不到 VIA_DailyBackup 尾版")
            return 1, None, None
        argv, cwd = [sys.executable, str(t), "full", "--via", str(repo / VIA_REL), *rest], repo
    else:
        t = find_tail(repo, VDF_REL, "VDF_LocalIntegrateLaunch_v*.py")
        if t is None:
            say("[RED] 找不到 VDF_LocalIntegrateLaunch 尾版")
            return 1, None, None
        argv, cwd = [sys.executable, str(t), "--repo", str(repo), *rest], repo
    say(f"{TAG} · {verb} → {Path(argv[len(fnc_python())] if verb == 'fnc' else argv[1]).name} {' '.join(rest)}".rstrip())
    rc = stream(argv, cwd, env, out / f"{verb}_console_tail.txt")
    (out / f"{verb}_RUN.json").write_text(json.dumps({"tool": TAG, "verb": verb, "rc": rc, "secs": round(time.time() - _T0, 1),
                                                       "argv_tail": rest, "accel": VIA_ACCEL is not None, "net": VIA_NET_TOOL_PATH is not None},
                                                      ensure_ascii=False, indent=1), encoding="utf-8")
    got = collect(verb, repo, out, fnc_dir)
    say(f"{verb} · rc {rc} · 收據 {len(got) + 2} 檔 → {out}")
    return rc, out, stamp


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    verb = next((a for a in argv if a in VERBS), None)
    if verb is None:
        return PRIOR.main(argv)                                           # 沒動詞 = 前版(同步 → 快跑器)
    i = argv.index(verb)
    head, rest = argv[:i], argv[i + 1:]
    flags = {"--push": False, "--sync": False}
    for f in list(flags):
        for lst in (head, rest):
            if f in lst:
                flags[f] = True
                lst.remove(f)
    fnc_dir = None
    if "--fnc-dir" in head:
        j = head.index("--fnc-dir")
        fnc_dir = head[j + 1]
        del head[j:j + 2]
    if "--repo" not in head:
        say("[RED] 要 --repo <倉>")
        return 1
    repo = Path(head[head.index("--repo") + 1]).expanduser().resolve()
    if not (repo / VIA_REL).is_dir():
        say(f"[RED] 不是 VIA 倉:{repo}")
        return 1
    say(f"{TAG} · 倉 {repo} · 加速器 {'載入' if VIA_ACCEL is not None else '沒載到(黃)'} · 網路工具 {'在' if VIA_NET_TOOL_PATH else '不在(黃)'}")
    if flags["--sync"]:
        say("同步(前版 --dry)")
        PRIOR.main(["--repo", str(repo), "--dry"])
    rc, out, stamp = run_verb(verb, rest, repo, fnc_dir)
    if flags["--push"] and out is not None:
        say(push_receipts(repo, out, stamp))
    say(f"完成 · rc {rc} · 總計 {time.time() - _T0:.0f}s")
    return rc


# ---------------------------------------------------------------- 自測(全在暫存夾造資料)
def selftest() -> int:
    ok, bad = [], []

    def chk(name, cond, note=""):
        (ok if cond else bad).append(name)
        print(("  [OK] " if cond else "  [NG] ") + name + (f" · {note}" if note else ""), flush=True)

    chk("加速器載入(VIA_ACCEL is not None)", VIA_ACCEL is not None)
    chk("網路工具載入(_via_net() is not None · 載入不出網)", _via_net() is not None, str(VIA_NET_TOOL_PATH))
    chk("前版經 glob 載入(v0100)", PRIOR_PATH.name == FAMILY + "_v0100.py")
    keep = {k: os.environ.get(k) for k in ("LOCALAPPDATA",)}
    try:
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            repo = td / "repo"
            ai = repo / AI_REL
            ai.mkdir(parents=True)
            (repo / VDF_REL).mkdir(parents=True)
            (ai / "VIA_DailyBackup_v0199.py").write_text(
                "import sys, os\nprint('BAK', ' '.join(sys.argv[1:]), os.environ.get('VIA_REPO') is not None)\nsys.exit(2)\n", encoding="utf-8")
            (repo / VDF_REL / "VDF_LocalIntegrateLaunch_v0199.py").write_text(
                "import sys\nsys.stdout.write('請輸入 YES:')\nsys.stdout.flush()\nsys.exit(0)\n", encoding="utf-8")
            fdir = td / "VCGC"
            fdir.mkdir()
            import zipfile
            with zipfile.ZipFile(fdir / "VIA_VCGC_FNC_v0101.zip", "w") as z:
                z.writestr("__main__.py", "import sys, pathlib, json\nr = pathlib.Path('receipts/RUN1'); r.mkdir(parents=True, exist_ok=True)\n"
                                          "(r / 'VCGC_FNC_HOST.json').write_text(json.dumps({'native_gate': 'PASS', 'args': sys.argv[1:]}))\nprint('FNC', sys.argv[1:])\n")
            os.environ["LOCALAPPDATA"] = str(td / "la")
            bk = td / "la" / "VIA" / "_via_backups" / "20260101_000000Z" / "extras"
            bk.mkdir(parents=True)
            (bk / "GATES.json").write_text('{"G1": "GREEN"}', encoding="utf-8")
            (bk.parents[1] / "BACKUP_latest.json").write_text('{"lamp": "GREEN"}', encoding="utf-8")
            t = find_tail(repo, AI_REL, "VIA_DailyBackup_v*.py")
            chk("找檔:本檔旁與倉裡比版號取最大", t is not None and _vnum(t) == 199, str(t))
            rc, out, _ = run_verb("bak", ["--books-check-only"], repo)
            log = (out / "bak_console_tail.txt").read_text(encoding="utf-8")
            chk("bak:叫備份尾版 full --via · 參數直通 · rc 照傳 · 有 VIA_REPO",
                rc == 2 and "full --via" in log and "--books-check-only" in log and "True" in log, log[-200:])
            got = sorted(p.name for p in out.iterdir())
            chk("bak:收據(BACKUP_latest · GATES · RUN · console)", any("BACKUP_latest" in g for g in got) and any("GATES" in g for g in got)
                and "bak_RUN.json" in got, str(got))
            rc, out, _ = run_verb("vdf", [], repo)
            chk("vdf:沒換行的提示也直通(YES 提示看得到)", rc == 0 and "請輸入 YES:" in (out / "vdf_console_tail.txt").read_text(encoding="utf-8"))
            rc, out, _ = run_verb("fnc", [], repo, fnc_dir=fdir)
            got = sorted(p.name for p in out.iterdir())
            chk("fnc:預設 host · 收封包 receipts/<執行碼>/*.json", rc == 0 and "host" in (out / "fnc_console_tail.txt").read_text(encoding="utf-8")
                and any("VCGC_FNC_HOST" in g for g in got), str(got))
            chk("fnc:沒有封包 = 紅", run_verb("fnc", [], repo, fnc_dir=td / "none")[0] == 1)
            chk("不是 VIA 倉 = 紅", main(["--repo", str(td), "bak"]) == 1)
            chk("沒有 FastRun = 推送略過(只印)", push_receipts(repo, out, "x").startswith("[推送略過]"))
            src = td / "origin"
            eng = src / VDF_REL / "engine"
            eng.mkdir(parents=True)
            (eng / "VDF_ENG053_ParamEngineMap_v0106.py").write_text(
                "import sys, os, pathlib\nprint('ENG053', sys.argv[1:], pathlib.Path.cwd().name.startswith('via_vdfp_'))\nsys.exit(0)\n", encoding="utf-8")
            g = lambda *a: subprocess.run(["git", *a], capture_output=True, text=True)  # noqa: E731
            g("init", "-q", "-b", "main", str(src))
            g("-C", str(src), "-c", "user.email=t@t", "-c", "user.name=t", "add", "-A")
            g("-C", str(src), "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "t")
            g("-C", str(src), "branch", "feat")
            g("clone", "-q", str(src), str(td / "clone"))
            (td / "clone" / VIA_REL).mkdir(parents=True, exist_ok=True)
            rc, out, _ = run_verb("vdfp", ["--branch", "feat", "unify"], td / "clone")
            log = (out / "vdfp_0_unify_console.txt").read_text(encoding="utf-8") if out else ""
            wts = g("-C", str(td / "clone"), "worktree", "list").stdout.strip().splitlines()
            vm = src / VIA_REL / "functional modules" / "VDF"
            vm.mkdir(parents=True, exist_ok=True)
            (vm / "VDF_SystemManager_v0192.py").write_text("import sys, subprocess\nprint('VDFM', sys.argv[1:], subprocess.run(['git','rev-parse','--abbrev-ref','HEAD'],capture_output=True,text=True).stdout.strip())\n", encoding="utf-8")
            reg = src / VIA_REL / "supportive modules" / "registry"
            reg.mkdir(parents=True, exist_ok=True)
            (reg / "CGC_SystemManager_v0121.py").write_text("import sys\nprint('CGCM', sys.argv[1:])\n", encoding="utf-8")
            g("-C", str(src), "-c", "user.email=t@t", "-c", "user.name=t", "add", "-A")
            g("-C", str(src), "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "m")
            g("-C", str(src), "branch", "-f", "feat2")
            g("-C", str(td / "clone"), "fetch", "-q", "origin")
            rc3, out3, _ = run_verb("vdf3", ["--branch", "feat2"], td / "clone")
            logs = " ".join(p.read_text(encoding="utf-8") for p in sorted(out3.glob("vdf3_*_console.txt"))) if out3 else ""
            head = g("-C", str(td / "clone"), "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
            chk("vdf3:暫切分支在真倉跑(detached)· 經兩個管理器 · 沒 --live 不跑 run · 跑完切回", rc3 == 0 and "VDFM ['three', 'ready'] HEAD" in logs
                and "'run', '--live'" not in logs and "CGCM ['schedule', 'run', 'vcgc_vdf_master']" in logs and head == "main", logs[-200:] + " head=" + head)
            chk("vdfp:分支另開 worktree 跑 ENG053 尾版 · 跑完拆掉 · 工作夾不動", rc == 0 and "ENG053 ['unify'] True" in log and len(wts) == 1, log[-160:] + str(wts))
    finally:
        for k, v in keep.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
    print(f"{TAG} selftest {len(ok)}/{len(ok) + len(bad)}" + (" · 不過:" + " · ".join(bad) if bad else ""), flush=True)
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
