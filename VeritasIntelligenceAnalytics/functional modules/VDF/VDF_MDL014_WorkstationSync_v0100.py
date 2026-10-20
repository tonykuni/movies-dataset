#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_MDL014_WorkstationSync v0100 — VDF 工作站一鍵:備份分岔 → VDF 自己的 MAIN → 交接真的重跑 → 只交 VDF 收據(不 force · 不動他系統)

操作員令(2026-10-20):「INTEGRATED INTO ONE CODE TO HANDLE ALL ABOVE」。上文的實錄:
  cd → git pull → via-vcgc handoff test qg_onebridge → git add / commit → git push 被拒(non-fast-forward)。
  工作站 main 與 origin/main 分岔(本機獨有 133 · 落後 181),本機獨有提交含 VRN-2 / VCGC / VRN 的工作;
  handoff test 回「沿用成功」(沒真的重跑);「git add docs\\handoff\\evidence」連 VRN 的收據一起收。
  四系統對等獨立(L123):不可為了 VDF 去 reset / 合併他系統的本機工作。
一個指令(預設預演,--apply 才動手):
  ① fetch;量落後 / 本機獨有提交;本機獨有提交若沒有任何遠端分支收著 → 推到新分支 workstation-backup-<時間>
     (不動 main、不 force)。
  ② VDF 自己的 MAIN:一個固定在 origin/main 的 git 工作樹(預設 %LOCALAPPDATA%\\VIA\\<倉名>-vdf-main,不進 OneDrive);
     不在就建、乾淨就移到最新 main、有未提交改動就停。本機原 checkout(他系統的工作)一個位元組都不碰。
  ③ 在 VDF MAIN 裡經 VCGC 跑交接案:每案先把舊收據移開 → 真的重跑(不沿用);沒產出就把舊收據放回;
     VCGC 的冊(Lessons Ledger · SubsystemSeat)還原、不提交。
  ④ 只收這次跑過、而且屬於 VDF 的案的收據(指令 VDF_ 開頭或相依在 functional modules/VDF/),
     提交到新分支 vdf-workstation-receipts-<時間> 並推上去;印 PR 連結。從不推 main、從不 force。
用法(工作站 cmd,在倉內 VeritasIntelligenceAnalytics 夾):
  python "functional modules\\VDF\\VDF_MDL014_WorkstationSync_v0100.py"            預演
  python "functional modules\\VDF\\VDF_MDL014_WorkstationSync_v0100.py" --apply    執行(預設案 qg_onebridge;--case 可多次)
VDF 自己的模組:不匯入他系統程式;同意閘不讀不寫;不碰 TA-Lib;不裝套件、不寫環境;git 走本機憑證。
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
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: F401
except ImportError:
    VIA_ACCEL = None
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
        spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        module = _nb_ilu.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

# ===== [VIA:LIB-BRIDGE:v0100] 三庫正典橋(批597;缺席大聲拋,不 graceful) =====
import sys as _lb_sys
from pathlib import Path as _lb_Path
_lb_p = _lb_Path(__file__).resolve()
while _lb_p.parent != _lb_p:
    if (_lb_p / "supportive modules").is_dir():
        _lb_sys.path.insert(0, str(_lb_p / "supportive modules"))
        break
    _lb_p = _lb_p.parent
import VIA_LibCanon as _LIB          # 正典缺席=大聲拋,不假裝有(LL151)
# ===== [VIA:LIB-BRIDGE:END] =====



import argparse
import datetime
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent                     # …/functional modules/VDF
TAG = "VDF_MDL014_WorkstationSync v0100"
VIA_DIR = "VeritasIntelligenceAnalytics"
EVID = "docs/handoff/evidence"
SSOT = "supportive modules/registry/VIA_Handoff_Continuity_SSOT_v0100.json"
VCGC_GLOB = "CGC_MDL149_VeritasCentralGovernanceConsole_v*.py"
VCGC_BOOKS = ("supportive modules/registry/VIA_Lessons_Ledger_v0100.json",
              "supportive modules/registry/VIA_VCGC_SubsystemSeat_v0100.json")   # VCGC 自己的冊:跑測會動到,一律還原、不提交
DEFAULT_CASES = ("qg_onebridge",)
BACKUP_PREFIX = "workstation-backup-"
RECEIPT_PREFIX = "vdf-workstation-receipts-"
GIT_LOG: list = []                                         # 本行程下過的 git 指令(自測驗「從不 force」)


def git(args: list, cwd: Path, check: bool = True) -> str:
    GIT_LOG.append(list(args))
    p = subprocess.run(["git", "-c", "core.quotepath=false", *args], cwd=str(cwd), capture_output=True, text=True, encoding="utf-8", errors="replace")
    if check and p.returncode != 0:
        raise RuntimeError("git %s 失敗(rc %s):%s" % (" ".join(args), p.returncode, (p.stderr or p.stdout).strip()[:400]))
    return p.stdout.rstrip()          # 只去尾:porcelain 首行開頭的空白是狀態欄,不能去


def default_worktree(root: Path) -> Path:
    """VDF 自己的 MAIN 放倉外(不進 OneDrive 同步夾):%LOCALAPPDATA%\\VIA\\<倉名>-vdf-main;沒有 LOCALAPPDATA 就放倉旁邊。"""
    base = os.environ.get("LOCALAPPDATA")
    return (Path(base) / "VIA" / (root.name + "-vdf-main")) if base else root.parent / (root.name + "-vdf-main")


def vdf_owned(case: dict) -> bool:
    """交接案是不是 VDF 的:指令跑 VDF_ 開頭的東西,或相依落在 functional modules/VDF/(四系統各管各的收據)。"""
    argv = case.get("argv") or []
    deps = case.get("dependencies") or []
    return bool(argv) and str(argv[0]).startswith("VDF_") or any(str(d).startswith("functional modules/VDF/") for d in deps)


def survey(root: Path, remote: str, wt: Path, fetch: bool = True) -> dict:
    """只量不動手:落後 / 獨有提交 · 獨有提交有沒有遠端分支收著 · VDF 工作樹在不在、乾不乾淨。"""
    if fetch:
        git(["fetch", remote], root)
    up = "%s/main" % remote
    behind, ahead = (int(x) for x in git(["rev-list", "--left-right", "--count", "%s...HEAD" % up], root).split())
    head = git(["rev-parse", "HEAD"], root)
    holders = [b.strip() for b in git(["branch", "-r", "--contains", "HEAD"], root).splitlines() if b.strip() and "->" not in b]
    wt_ok = (wt / ".git").exists()
    wt_dirty = []
    if wt_ok:
        wt_dirty = [ln for ln in git(["status", "--porcelain"], wt).splitlines()
                    if ln.strip() and not any(ln[3:].strip().strip('"').endswith(b) for b in VCGC_BOOKS)]
    return {"up": up, "behind": behind, "ahead": ahead, "head": head, "holders": holders,
            "backup_needed": ahead > 0 and not holders, "wt": str(wt), "wt_exists": wt_ok, "wt_dirty": wt_dirty,
            "main_dirty": [ln for ln in git(["status", "--porcelain"], root).splitlines() if ln.strip()]}


def backup(root: Path, remote: str, s: dict, stamp: str) -> str:
    """本機獨有提交推到新分支(從不 force,從不動 main)。已有遠端分支收著就不重推。"""
    if not s["backup_needed"]:
        return s["holders"][0] if s["holders"] else ""
    name = BACKUP_PREFIX + stamp
    git(["push", remote, "HEAD:refs/heads/%s" % name], root)
    return "%s/%s" % (remote, name)


def ensure_worktree(root: Path, s: dict) -> str:
    """VDF 自己的 MAIN:一個固定在 origin/main 的 git 工作樹。不在就建;在且乾淨就移到最新 main;有未提交的改動就停。"""
    wt = Path(s["wt"])
    if not s["wt_exists"]:
        wt.parent.mkdir(parents=True, exist_ok=True)
        git(["worktree", "add", "--detach", str(wt), s["up"]], root)
        return "建立"
    if s["wt_dirty"]:
        raise RuntimeError("VDF 工作樹有未提交的改動,先處理再跑(不覆蓋):%s" % s["wt_dirty"][:5])
    git(["checkout", "--detach", s["up"]], wt)
    return "更新"


def _restore_vcgc_books(via: Path) -> None:
    for b in VCGC_BOOKS:
        if (via / b).exists():
            git(["checkout", "--", b], via, check=False)


def run_cases(wt: Path, cases: list, timeout: int = 2700) -> list:
    """在 VDF 工作樹裡經 VCGC 跑交接案;每案先把舊收據移開 → 真的重跑(不沿用)。沒產出新收據就把舊的放回。"""
    via = wt / VIA_DIR
    hits = sorted((via / "supportive modules" / "registry").glob(VCGC_GLOB))
    if not hits:
        raise RuntimeError("工作樹裡找不到 VCGC 主控台 %s" % VCGC_GLOB)
    out = []
    env = dict(os.environ, VIA_FROM_VCGC="YES", VIA_VCGC_PUSH="NO", VIA_NO_OPEN="1")
    for c in cases:
        rec = via / EVID / (c + ".json")
        bak = rec.with_suffix(".json.pre_sync")
        if rec.exists():
            rec.replace(bak)
        try:
            p = subprocess.run([sys.executable, str(hits[-1]), "handoff", "test", c], cwd=str(via), env=env,
                               capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
            rc, tail = p.returncode, (p.stdout + p.stderr)[-1500:]
        except subprocess.TimeoutExpired:
            rc, tail = 124, "逾時 %s 秒" % timeout
        verdict = {}
        for ln in (tail.splitlines()[::-1]):
            if ln.startswith("{") and '"case"' in ln:
                try:
                    verdict = json.loads(ln)
                except ValueError:
                    pass
                break
        if rec.exists():
            if bak.exists():
                bak.unlink()
        elif bak.exists():
            bak.replace(rec)
        out.append({"case": c, "rc": rc, "marker": verdict.get("marker"), "reused": bool(verdict.get("reused")), "tail": tail[-400:]})
    _restore_vcgc_books(via)
    return out


def stage_vdf_receipts(wt: Path, ran: list) -> list:
    """只挑這次跑過、而且是 VDF 的案的收據(含 history/<案>-*);他系統的收據與 VCGC 的冊一個都不收。"""
    via = wt / VIA_DIR
    book = json.loads((via / SSOT).read_text(encoding="utf-8")).get("test_cases") or {}
    mine = {r["case"] for r in ran if r["case"] in book and vdf_owned(book[r["case"]])}
    picked = []
    for ln in git(["status", "--porcelain", "--untracked-files=all", "--", EVID], via).splitlines():
        rel = ln[3:].strip().strip('"')
        name = rel.split(EVID + "/", 1)[-1]
        first = name.split("/")[1] if name.startswith("history/") else name
        case = re.sub(r"(-[0-9a-f]{16,})?(\.(json|txt))?$", "", first)
        if case in mine:
            picked.append(rel)
    for rel in picked:
        git(["add", "--", rel.split(VIA_DIR + "/", 1)[-1] if rel.startswith(VIA_DIR + "/") else rel], via)
    return picked


def publish(wt: Path, remote: str, picked: list, ran: list, stamp: str) -> str:
    """收據提交到新分支並推上去(從不 force · 從不推 main);沒東西就不提交。"""
    if not picked:
        return ""
    name = RECEIPT_PREFIX + stamp
    git(["switch", "-c", name], wt)
    msg = "交接收據(工作站 · %s):%s\n\n由 %s 在 VDF 工作樹(固定在 main)真的重跑;只收 VDF 的案。" % (
        stamp, " · ".join("%s rc %s" % (r["case"], r["rc"]) for r in ran), TAG)
    git(["commit", "-m", msg], wt)
    git(["push", "-u", remote, name], wt)
    return name


def remote_web(root: Path, remote: str) -> str:
    u = git(["remote", "get-url", remote], root, check=False)
    m = re.search(r"github\.com[:/](.+?)(?:\.git)?$", u)
    return "https://github.com/%s" % m.group(1) if m else ""


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog=Path(__file__).name, description=TAG)
    ap.add_argument("--apply", action="store_true", help="真的執行(預設只預演)")
    ap.add_argument("--case", action="append", help="要重跑的交接案(可多次;預設 qg_onebridge)")
    ap.add_argument("--worktree", help="VDF 工作樹位置(預設 %%LOCALAPPDATA%%\\VIA\\<倉名>-vdf-main)")
    ap.add_argument("--remote", default="origin")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    root = Path(git(["rev-parse", "--show-toplevel"], HERE))
    wt = Path(a.worktree).resolve() if a.worktree else default_worktree(root)
    cases = a.case or list(DEFAULT_CASES)
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M")
    print("=== %s · %s ===" % (TAG, "執行" if a.apply else "預演(加 --apply 才動手)"))
    s = survey(root, a.remote, wt)
    print("  [倉] %s · 本機 HEAD %s · 落後 %s %d 提交 · 本機獨有 %d 提交" % (root, s["head"][:9], s["up"], s["behind"], s["ahead"]))
    if s["main_dirty"]:
        print("  [倉] 本機有 %d 個未提交改動 —— 本工具不碰它們(他系統的工作照留)" % len(s["main_dirty"]))
    print("  [備份] %s" % ("需要:推到新分支 %s%s(不動 main、不 force)" % (BACKUP_PREFIX, stamp) if s["backup_needed"]
                          else ("不需要:已在 %s" % ", ".join(s["holders"][:3]) if s["ahead"] else "不需要:沒有本機獨有提交")))
    print("  [VDF MAIN] %s · %s" % (wt, ("已在" + (" · 有未提交改動 %d" % len(s["wt_dirty"]) if s["wt_dirty"] else " · 乾淨")) if s["wt_exists"] else "還沒建"))
    print("  [交接案] %s(先移開舊收據 → 真的重跑;只收 VDF 的收據)" % ", ".join(cases))
    if not a.apply:
        print("NEXT: python \"%s\" --apply" % Path(__file__).name)
        return 0
    held = backup(root, a.remote, s, stamp)
    if held:
        print("  [備份] 本機獨有提交在 %s" % held)
    print("  [VDF MAIN] %s → %s" % (ensure_worktree(root, s), git(["rev-parse", "--short", "HEAD"], wt)))
    ran = run_cases(wt, cases)
    for r in ran:
        print("  [交接] %s rc %s · 標記 %s%s" % (r["case"], r["rc"], r["marker"], " · 沿用(不該發生)" if r["reused"] else ""))
    picked = stage_vdf_receipts(wt, ran)
    br = publish(wt, a.remote, picked, ran, stamp)
    ok = all(r["rc"] == 0 and r["marker"] and not r["reused"] for r in ran)
    web = remote_web(root, a.remote)
    if br:
        print("  [收據] %d 檔 → 分支 %s" % (len(picked), br))
        print("NEXT: 開 PR %s/pull/new/%s(或把這行貼給 AI)" % (web, br))
    else:
        print("  [收據] 沒有新的 VDF 收據要交")
    print("[計] %s · 交接 %s · %s" % (TAG, "全綠" if ok else "有紅", "PASS" if ok else "FAIL"))
    return 0 if ok else 1


def selftest() -> int:
    """離線:假遠端(bare)+ 兩個 clone 做出「本機分岔」,假 VCGC 主控台,整條流程跑一次。"""
    import tempfile
    p = f = 0

    def chk(name, cond, note=""):
        nonlocal p, f
        if cond:
            p += 1
            print("  [OK] %s" % name)
        else:
            f += 1
            print("  [FAIL] %s%s" % (name, (" · " + str(note)[:300]) if note else ""))

    print("=== %s · 自測(離線假倉;不連網 · 不碰真倉)===" % TAG)
    td = Path(tempfile.mkdtemp(prefix="vdf_mdl014_"))
    keep = {k: os.environ.get(k) for k in ("GIT_AUTHOR_NAME", "GIT_AUTHOR_EMAIL", "GIT_COMMITTER_NAME", "GIT_COMMITTER_EMAIL", "LOCALAPPDATA")}
    os.environ.update(GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@x", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@x")
    os.environ.pop("LOCALAPPDATA", None)
    try:
        remote = td / "remote.git"
        git(["init", "--bare", "-b", "main", str(remote)], td)
        seed = td / "seed"
        git(["clone", str(remote), str(seed)], td)
        via = seed / VIA_DIR
        (via / EVID).mkdir(parents=True)
        reg = via / "supportive modules" / "registry"
        reg.mkdir(parents=True)
        (reg / "VIA_VCGC_SubsystemSeat_v0100.json").write_text("{}\n", encoding="utf-8")
        (via / SSOT).write_text(json.dumps({"test_cases": {
            "vdf_case": {"argv": ["VDF_X", "--selftest"], "dependencies": ["functional modules/VDF/VDF_X_v*.py"]},
            "vrn_case": {"argv": ["VRN_Y", "--selftest"], "dependencies": ["functional modules/VRN/VRN_Y_v*.py"]}}}), encoding="utf-8")
        (via / EVID / "vdf_case.json").write_text('{"rc": 0, "old": true}\n', encoding="utf-8")
        (reg / "CGC_MDL149_VeritasCentralGovernanceConsole_v0001.py").write_text(
            "import json, sys, pathlib\n"
            "case = sys.argv[3]\n"
            "ev = pathlib.Path('docs/handoff/evidence')\n"
            "fresh = not (ev / (case + '.json')).exists()\n"
            "(ev / (case + '.json')).write_text(json.dumps({'case': case, 'rc': 0, 'fresh': fresh}))\n"
            "(ev / (case + '.txt')).write_text('log')\n"
            "h = ev / 'history' / (case + '-0123456789abcdef0123'); h.mkdir(parents=True, exist_ok=True); (h / 'receipt.json').write_text('{}')\n"
            "pathlib.Path('supportive modules/registry/VIA_VCGC_SubsystemSeat_v0100.json').write_text('{\"dirty\": 1}')\n"
            "with open('calls.log', 'a') as fh: fh.write(case + chr(10))\n"
            "print(json.dumps({'case': case, 'rc': 0, 'marker': fresh, 'reused': not fresh}))\n", encoding="utf-8")
        (seed / ".gitignore").write_text("calls.log\n", encoding="utf-8")
        git(["add", "-A"], seed)
        git(["commit", "-m", "seed"], seed)
        git(["push", "origin", "main"], seed)
        work = td / "work"
        git(["clone", str(remote), str(work)], td)
        (work / "other_system_local.txt").write_text("VRN-2 本機獨有\n", encoding="utf-8")
        git(["add", "-A"], work)
        git(["commit", "-m", "ws local"], work)
        (work / "uncommitted.txt").write_text("他系統未提交的工作\n", encoding="utf-8")
        (seed / "upstream.txt").write_text("main 前進\n", encoding="utf-8")
        git(["add", "-A"], seed)
        git(["commit", "-m", "upstream"], seed)
        git(["push", "origin", "main"], seed)
        wt = td / "vdf-main"
        head0 = git(["rev-parse", "HEAD"], work)
        s = survey(work, "origin", wt)
        chk("① 預演:量得出分岔(落後 1 · 本機獨有 1)· 要備份 · 工作樹還沒建 · 看得到本機未提交改動",
            s["behind"] == 1 and s["ahead"] == 1 and s["backup_needed"] and not s["wt_exists"] and s["main_dirty"], s)
        GIT_LOG.clear()
        held = backup(work, "origin", s, "T1")
        chk("② 備份:本機獨有提交推到新分支,遠端分支收著本機 HEAD", held == "origin/" + BACKUP_PREFIX + "T1"
            and git(["rev-parse", "refs/heads/" + BACKUP_PREFIX + "T1"], remote) == head0, held)
        how = ensure_worktree(work, s)
        chk("③ VDF MAIN:工作樹建在 origin/main(含 upstream 的提交)", how == "建立" and (wt / "upstream.txt").exists()
            and git(["rev-parse", "HEAD"], wt) == git(["rev-parse", "refs/heads/main"], remote))
        ran = run_cases(wt, ["vdf_case", "vrn_case"])
        r0 = json.loads((wt / VIA_DIR / EVID / "vdf_case.json").read_text(encoding="utf-8"))
        chk("④ 真的重跑:舊收據先移開 → 主控台判不沿用(fresh)· 兩案都跑到 · 沒留 .pre_sync",
            r0.get("fresh") is True and [r["marker"] for r in ran] == [True, True] and not any(r["reused"] for r in ran)
            and not list((wt / VIA_DIR / EVID).glob("*.pre_sync")), ran)
        chk("⑤ VCGC 的冊跑測被動到 → 已還原(不提交他系統的冊)",
            not git(["status", "--porcelain", "--", "supportive modules/registry"], wt / VIA_DIR))
        picked = stage_vdf_receipts(wt, ran)
        chk("⑥ 只收 VDF 的案:vdf_case 的收據 / log / history 都收 · vrn_case 一檔不收",
            picked and all("vdf_case" in x for x in picked) and len(picked) == 3, picked)
        br = publish(wt, "origin", picked, ran, "T1")
        chk("⑦ 收據提交到新分支並推上去;遠端 main 沒被動到",
            br == RECEIPT_PREFIX + "T1" and git(["rev-parse", "refs/heads/" + br], remote)
            and git(["log", "-1", "--format=%s", "refs/heads/main"], remote) == "upstream", br)
        chk("⑧ 本機 checkout 一點沒動:HEAD 照舊 · 未提交的他系統檔還在 · 本機獨有檔還在",
            git(["rev-parse", "HEAD"], work) == head0 and (work / "uncommitted.txt").exists() and (work / "other_system_local.txt").exists())
        pushes = [c for c in GIT_LOG if c and c[0] == "push"]
        chk("⑨ 從不 force · 從不推 main", pushes and not any(("--force" in c or "-f" in c or "--force-with-lease" in c
                                                          or any(str(x).endswith(":refs/heads/main") or x == "main" for x in c[1:])) for c in pushes), pushes)
        s2 = survey(work, "origin", wt)
        chk("⑩ 再跑一次:已有遠端分支收著 → 不重複備份", not s2["backup_needed"] and s2["holders"], s2["holders"])
        (wt / "scratch.txt").write_text("x", encoding="utf-8")
        s3 = survey(work, "origin", wt)
        try:
            ensure_worktree(work, s3)
            stopped = False
        except RuntimeError as exc:
            stopped = "未提交" in str(exc)
        chk("⑪ VDF 工作樹有未提交改動 → 停下不覆蓋", stopped and (wt / "scratch.txt").exists())
        chk("⑫ 認 VDF 的案:VDF_ 開頭的指令或相依在 functional modules/VDF/ 才算",
            vdf_owned({"argv": ["VDF_ENG086_QuantGuardOneBridge"]}) and vdf_owned({"argv": ["VDF_SystemManager", "x"]})
            and vdf_owned({"argv": ["CGC_X"], "dependencies": ["functional modules/VDF/a.py"]})
            and not vdf_owned({"argv": ["VRN_Y"], "dependencies": ["functional modules/VRN/b.py"]}))
        chk("⑬ VDF MAIN 預設放倉外(%LOCALAPPDATA%\\VIA\\<倉名>-vdf-main;沒有就放倉旁)",
            default_worktree(Path("/x/movies-dataset")) == Path("/x/movies-dataset-vdf-main"))
        src = Path(__file__).read_text(encoding="utf-8")
        imports = re.findall(r"^\s*(?:import|from)\s+([A-Za-z_][\w.]*)", src, re.M)
        chk("⑭ 三橋在 · 不匯入他系統程式 · 不碰 TA-Lib · 同意閘不寫",
            all(t in src for t in ("[VIA:ACCEL-BRIDGE:v0100]", "[VIA:NET-BRIDGE:v0100]", "[VIA:LIB-BRIDGE:v0100]"))
            and not [x for x in imports if x.startswith(("CGC_", "VRN_", "VRN2_", "VCGC"))]
            and not re.search(r"^\s*(import|from)\s+" + "talib", src, re.M)
            and not re.search(r"\[[\"']VIA_(NET|SCRAPE)_" + r"CONSENT[\"']\]\s*=(?!=)", src))
    finally:
        for k, v in keep.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        shutil.rmtree(td, ignore_errors=True)
    print("  [計] %s 自測 %d/%d · %s" % (TAG, p, p + f, "PASS" if not f else "FAIL"))
    return 0 if not f else 1


if __name__ == "__main__":
    raise SystemExit(main())
