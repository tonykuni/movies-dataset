#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VIA_HostBoot v0100 — 桌機啟動器(獨立一支,不載前版):同步倉 → 呼叫快跑器;PS 只負責把它取出來執行

操作員 2026-11-24:「以後這種指令都用 py 寫導入加速器 · ps 只是簡單啟動 · 好慢」。PS 一行實跑兩個問題:
  ① 貼上時第一個字掉了($R= → R=),後面幾步沿用前一行留下的舊變數 → 路徑多一層;
  ② 倉裡有未追蹤的 VIA_ProfileLoader_v0102.ps1,main 上同名檔已被追蹤 → git 拒絕快轉。
本支(不靠倉裡任何別的檔,PS 從分支取出到 TEMP 直接跑):
  1 git fetch(git 自己的進度直接顯示)
  2 已追蹤檔有改動 → 停,列出來,不碰;未追蹤卻擋住快轉 / 切版的檔:跟目標那份一模一樣 → 移除(合併後放回同一份);
    不一樣 → 搬到 <倉的上一層>/VIA_untracked_backup/<時間>/ 保留(不刪)
  3 main 快轉到 origin/main
  4 分支還沒併進 main → 暫時切到 origin/<分支>(只換差的幾個檔)
  5 呼叫快跑器尾版(它自己畫進度條)→ 切回原分支
用法:python VIA_HostBoot_v0100.py --repo <倉> [--branch <分支>] [--dry] -- <快跑器參數…>
rc:0 綠 · 2 黃 · 1 紅 · 4 倉有已追蹤的改動(沒動) · 5 git 失敗
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
    VIA_ACCEL = None  # graceful:從 TEMP 跑時倉外找不到加速器 = 零影響;快跑器在倉內自己帶橋
# ===== [VIA:ACCEL-BRIDGE:END] =====

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

TAG = "VIA_HostBoot v0100"
MARK = "[啟動]"
FASTRUN_DIR = "VeritasIntelligenceAnalytics/docs/handoff/ai"
_T0 = time.time()
_STEP = {"k": 0, "n": 5}


def say(msg: str) -> None:
    print("%s %s" % (MARK, msg), flush=True)


def step(title: str) -> None:
    _STEP["k"] += 1
    k, n = _STEP["k"], _STEP["n"]
    bar = "█" * (4 * (k - 1)) + "░" * (4 * (n - k + 1))
    print("%s ▕%s▏ %d/%d · %s · 已 %ds" % (MARK, bar, k, n, title, time.time() - _T0), flush=True)


def git(repo: Path, *a, live: bool = False):
    """live=True:git 自己的輸出(含進度)直接到主控台;否則收起來回傳。"""
    if live:
        return subprocess.run(["git", "-C", str(repo), *a]).returncode, "", ""
    p = subprocess.run(["git", "-C", str(repo), *a], capture_output=True, text=True, encoding="utf-8", errors="replace")
    return p.returncode, p.stdout, p.stderr


def tracked_changes(repo: Path) -> list:
    return [ln for ln in git(repo, "status", "--porcelain", "--untracked-files=no")[1].splitlines() if ln.strip()]


def blockers(repo: Path, targets: list) -> list:
    """未追蹤、但目標 commit 裡有同名追蹤檔 → 快轉 / 切版會被擋。回 [(相對路徑, 目標)]。"""
    rc, out, _ = git(repo, "ls-files", "--others", "--exclude-standard", "-z")
    untracked = set(x for x in out.split("\0") if x)
    hits, seen = [], set()
    for t in targets:
        if not untracked:
            break
        rc, out, _ = git(repo, "ls-tree", "-r", "--name-only", "-z", t)
        for x in out.split("\0"):
            if x and x in untracked and x not in seen:
                hits.append((x, t))
                seen.add(x)
    return hits


def clear_blockers(repo: Path, hits: list, stamp: str) -> list:
    """一模一樣 → 移除;不一樣 → 搬到備份夾。回每一個的處理結果。"""
    done = []
    for rel, t in hits:
        p = repo / rel
        local = git(repo, "hash-object", rel)[1].strip()
        want = git(repo, "rev-parse", "%s:%s" % (t, rel))[1].strip()
        if local and local == want:
            p.unlink()
            done.append(("移除(跟 %s 那份一模一樣)" % t, rel, ""))
        else:
            bk = repo.parent / "VIA_untracked_backup" / stamp / rel
            bk.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(p), str(bk))
            done.append(("搬到備份(跟 %s 那份不一樣)" % t, rel, str(bk)))
    return done


def fastrun_tail(repo: Path):
    c = sorted((repo / FASTRUN_DIR).glob("VIA_FastRun_v[0-9][0-9][0-9][0-9].py"))
    return c[-1] if c else None


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    rest = argv[argv.index("--") + 1:] if "--" in argv else []
    head = argv[:argv.index("--")] if "--" in argv else argv
    ap = argparse.ArgumentParser(prog=TAG)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--branch", default="")
    ap.add_argument("--dry", action="store_true", help="只同步,不呼叫快跑器")
    a = ap.parse_args(head)
    repo = Path(a.repo).expanduser().resolve()
    if not (repo / ".git").exists():
        say("[停] 找不到倉 %s(.git 不在)" % repo)
        return 5
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    step("抓最新(git fetch · git 自己的進度)")
    refs = ["main"] + ([a.branch] if a.branch else [])
    if git(repo, "fetch", "--progress", "origin", *refs, live=True)[0] != 0:
        say("[停] git fetch 失敗(網路 / 登入視窗?)")
        return 5
    step("檢查倉(已追蹤的改動 · 擋路的未追蹤檔)")
    ch = tracked_changes(repo)
    if ch:
        say("[停] 倉裡有已追蹤檔的改動,沒有動它們;先提交或還原再跑:")
        for ln in ch[:20]:
            say("   " + ln)
        return 4
    targets = ["origin/main"] + (["origin/" + a.branch] if a.branch else [])
    for verb, rel, bk in clear_blockers(repo, blockers(repo, targets), stamp):
        say("[YELLOW] %s · %s%s" % (verb, rel, (" → " + bk) if bk else ""))
    step("main 快轉到 origin/main")
    rc, cur, _ = git(repo, "rev-parse", "--abbrev-ref", "HEAD")
    cur = cur.strip()
    if cur != "main" and git(repo, "switch", "-q", "main", live=True)[0] != 0:
        say("[停] 切不回 main")
        return 5
    if git(repo, "merge", "--ff-only", "origin/main", live=True)[0] != 0:
        say("[停] main 沒辦法快轉(本機 main 有 origin 沒有的提交?)")
        return 5
    switched = False
    step("切到要跑的版本")
    if a.branch and git(repo, "merge-base", "--is-ancestor", "origin/" + a.branch, "origin/main")[0] != 0:
        if git(repo, "switch", "-q", "--detach", "origin/" + a.branch, live=True)[0] != 0:
            say("[停] 切不到 origin/%s" % a.branch)
            return 5
        switched = True
        say("暫時切到 origin/%s(還沒併進 main)" % a.branch)
    else:
        say("用 main(%s)" % ("分支已併進 main" if a.branch else "沒指定分支"))
    rc = 0
    try:
        step("快跑器")
        t = fastrun_tail(repo)
        if a.dry:
            say("--dry:只同步,不呼叫快跑器(尾版 %s)" % (t.name if t else "不在"))
        elif t is None:
            say("[停] 找不到 VIA_FastRun 尾版")
            rc = 5
        else:
            say("%s %s" % (t.name, " ".join(rest)))
            rc = subprocess.run([sys.executable, str(t), *rest], cwd=str(repo), env=dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")).returncode
    finally:
        if switched:
            git(repo, "switch", "-q", "main" if cur in ("HEAD", "main") else cur, live=True)
    say("完成 · rc %s · 總計 %ds" % (rc, time.time() - _T0))
    return rc


# ─────────────────────────── 自測(全在暫存夾造倉 · 不跑快跑器)───────────────────────────
def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + name + ((" · " + str(note)[:300]) if note and not cond else ""), flush=True)

    print("[計] %s 自測開始(本版 6 項)" % TAG, flush=True)
    env0 = {k: os.environ.get(k) for k in ("GIT_AUTHOR_NAME", "GIT_AUTHOR_EMAIL", "GIT_COMMITTER_NAME", "GIT_COMMITTER_EMAIL")}
    os.environ.update(GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")
    try:
        with tempfile.TemporaryDirectory(prefix="hostboot_") as td:
            td = Path(td)
            g = lambda *x, cwd: subprocess.run(["git", *x], cwd=str(cwd), capture_output=True, text=True)
            g("init", "-q", "--bare", "-b", "main", str(td / "origin.git"), cwd=td)
            g("clone", "-q", str(td / "origin.git"), str(td / "up"), cwd=td)
            up = td / "up"
            (up / "a.txt").write_text("base\n", encoding="utf-8")
            g("add", "-A", cwd=up)
            g("commit", "-qm", "base", cwd=up)
            g("push", "-q", "origin", "HEAD:main", cwd=up)
            g("clone", "-q", str(td / "origin.git"), str(td / "host"), cwd=td)
            host = td / "host"
            (up / "same.ps1").write_text("同一份\n", encoding="utf-8")
            (up / "diff.ps1").write_text("main 的版本\n", encoding="utf-8")
            fr = up / FASTRUN_DIR
            fr.mkdir(parents=True)
            (fr / "VIA_FastRun_v0102.py").write_text("print('fastrun')\n", encoding="utf-8")
            g("add", "-A", cwd=up)
            g("commit", "-qm", "main 加三檔", cwd=up)
            g("push", "-q", "origin", "HEAD:main", cwd=up)
            g("switch", "-q", "-c", "feat", cwd=up)
            (up / "feat.txt").write_text("分支才有\n", encoding="utf-8")
            g("add", "-A", cwd=up)
            g("commit", "-qm", "feat", cwd=up)
            g("push", "-q", "origin", "feat", cwd=up)
            (host / "same.ps1").write_text("同一份\n", encoding="utf-8")            # 未追蹤 · 跟 main 一樣
            (host / "diff.ps1").write_text("本機改過的\n", encoding="utf-8")        # 未追蹤 · 跟 main 不一樣
            (host / "mine.txt").write_text("不擋路的未追蹤檔\n", encoding="utf-8")
            g("fetch", "-q", "origin", "main", "feat", cwd=host)
            hits = blockers(host, ["origin/main", "origin/feat"])
            chk("T1 找出擋快轉的未追蹤檔(只找目標裡有同名追蹤檔的)", sorted(h[0] for h in hits) == ["diff.ps1", "same.ps1"], hits)
            rc = main(["--repo", str(host), "--branch", "feat", "--dry"])
            bk = list((td / "VIA_untracked_backup").rglob("diff.ps1"))
            chk("T2 一樣的移除 · 不一樣的搬到倉外備份(內容保留)· 不擋路的不動",
                rc == 0 and bk and bk[0].read_text(encoding="utf-8") == "本機改過的\n" and (host / "mine.txt").exists(), (rc, bk))
            chk("T3 main 快轉到 origin/main · 合併後 same.ps1 是 main 那份",
                g("rev-parse", "main", cwd=host).stdout == g("rev-parse", "origin/main", cwd=host).stdout
                and (host / "same.ps1").read_text(encoding="utf-8") == "同一份\n")
            chk("T4 分支還沒併進 main → 跑的時候切到分支,跑完切回 main", g("rev-parse", "--abbrev-ref", "HEAD", cwd=host).stdout.strip() == "main"
                and not (host / "feat.txt").exists())
            (host / "a.txt").write_text("改了已追蹤檔\n", encoding="utf-8")
            rc2 = main(["--repo", str(host), "--dry"])
            chk("T5 已追蹤檔有改動 → rc 4 停下 · 改動原樣保留", rc2 == 4 and (host / "a.txt").read_text(encoding="utf-8") == "改了已追蹤檔\n", rc2)
            g("checkout", "--", "a.txt", cwd=host)
            chk("T6 快跑器尾版找得到(glob 取最高版號)", fastrun_tail(host) is not None and fastrun_tail(host).name == "VIA_FastRun_v0102.py")
    finally:
        for k, v in env0.items():
            os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)
    n = sum(ok)
    print("[計] %s 自測 %d/%d · %s" % (TAG, n, len(ok), "PASS" if n == len(ok) else "FAIL"), flush=True)
    return 0 if n == len(ok) else 1


if __name__ == "__main__":
    raise SystemExit(main())
