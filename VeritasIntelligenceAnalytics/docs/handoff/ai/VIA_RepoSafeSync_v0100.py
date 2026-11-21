#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VIA_RepoSafeSync v0100 — 一個功能:桌機倉安全快轉到 origin/main(同名檔以 main 為準 · 擋路的先搬到倉外備份 · 不刪任何檔)

操作員 2026-11-21 桌機實錄:`git pull --ff-only origin main` 被一個未追蹤檔擋下
(functional modules/VDF/registry/VDF_SSOT_Register_v0113.json:桌機自己生的,main 上同名已追蹤)→ 整個 pull 放棄,
桌機停在 b579e16f3(少 52 個提交)→ 後面跑的全是舊程式(ApplyRun v0104 / v0105、沒有官方對帳層),紅燈全是舊程式的燈。
既有 VIA_SYSTEM_MANAGER do_sync(stash 含未追蹤 → 快轉 → 套回)遇到這種同名檔會在套回時整包衝突,本機改動全卡在 stash;
本檔補這個缺口,做一件事:
  ① 只在目標分支(預設 main)上動;不在 → 印 `git switch main` 那一行、零寫入(rc 2)。
  ② fetch;本機有自己的提交(分歧)→ 不能快轉,停(rc 2,不重寫歷史)。
  ③ 擋路清單 = 上游這段會新增 / 改動的路徑 ∩(本機未追蹤 · 或本機改過未提交)。
  ④ --apply:擋路的檔先複製到倉外 <倉上一層>/VIA_SyncBackup/<UTC 時間>/<原路徑>,未追蹤的搬走、改過的還原成 HEAD(main 為準);
     其餘本機改動(上游沒碰的)原樣留著;然後 git merge --ff-only。沒加 --apply = 只列計畫、零寫入。
  ⑤ 收據 VIA_Reports/vcgc/sync/REPO_SYNC_latest.json(做了什麼 · 備份在哪 · 前後 HEAD)。
用法:python VIA_RepoSafeSync_v0100.py [--apply] [--repo <倉內任一路徑>] [--branch main] [--remote origin] [--backup-dir <夾>] · --selftest
不設同意閘;不碰 TA-Lib;本檔不出網(git 自己連 GitHub)。
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

# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 全導入令;graceful 零行為變更) =====
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
    """統包唯一網路工具惰性載入;本檔不出網(git 自己連),橋只為全樹覆蓋。"""
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

import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

TAG = "VIA_RepoSafeSync v0100"


def _git(repo, *a, check=False):
    r = subprocess.run(["git", "-C", str(repo), *a], capture_output=True, text=True, encoding="utf-8", errors="replace")
    if check and r.returncode != 0:
        raise RuntimeError(f"git {' '.join(a)} rc {r.returncode}: {(r.stderr or r.stdout).strip()[:200]}")
    return r


def _lines(r) -> list:
    return [x for x in (r.stdout or "").splitlines() if x.strip()]


def plan(repo, branch: str = "main", remote: str = "origin", fetch: bool = True) -> dict:
    """回同步計畫(零寫入工作樹;fetch 只更新遠端追蹤分支)。"""
    top = _git(repo, "rev-parse", "--show-toplevel")
    if top.returncode != 0:
        return {"state": "NOT_REPO", "rc": 2, "why": f"{repo} 不是 git 倉"}
    root = Path(top.stdout.strip())
    cur = _git(root, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
    out = {"repo": str(root), "branch": cur, "target": f"{remote}/{branch}"}
    if cur != branch:
        return dict(out, state="WRONG_BRANCH", rc=2, why=f"目前在 {cur},不是 {branch}", fix=f"git -C \"{root}\" switch {branch}")
    if fetch:
        f = _git(root, "fetch", remote, branch)
        if f.returncode != 0:
            return dict(out, state="FETCH_FAIL", rc=2, why=(f.stderr or f.stdout).strip()[:200])
    up = f"{remote}/{branch}"
    ahead, behind = (int(x) for x in _git(root, "rev-list", "--left-right", "--count", f"HEAD...{up}", check=True).stdout.split())
    out.update(head=_git(root, "rev-parse", "--short=9", "HEAD").stdout.strip(), upstream=_git(root, "rev-parse", "--short=9", up).stdout.strip(),
               ahead=ahead, behind=behind)
    if behind == 0:
        return dict(out, state="UP_TO_DATE", rc=0, blocking_untracked=[], blocking_modified=[])
    if ahead > 0:
        return dict(out, state="DIVERGED", rc=2, why=f"本機多 {ahead} 個自己的提交,不能快轉(不重寫歷史)")
    incoming = set(_lines(_git(root, "diff", "--name-only", "HEAD", up)))
    untracked = set(_lines(_git(root, "ls-files", "--others", "--exclude-standard")))
    modified = set(_lines(_git(root, "diff", "--name-only", "HEAD")))
    return dict(out, state="BEHIND", rc=0, incoming=len(incoming),
                blocking_untracked=sorted(untracked & incoming), blocking_modified=sorted(modified & incoming),
                kept_local=len((untracked | modified) - incoming))


def apply(repo, branch: str = "main", remote: str = "origin", backup_dir=None) -> dict:
    p = plan(repo, branch, remote)
    if p.get("state") != "BEHIND":
        return p
    root = Path(p["repo"])
    ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    bk = Path(backup_dir) if backup_dir else root.parent / "VIA_SyncBackup" / ts
    moved = []
    for rel in p["blocking_untracked"] + p["blocking_modified"]:
        src = root / rel
        if src.exists():
            dst = bk / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            moved.append(rel)
    for rel in p["blocking_untracked"]:
        (root / rel).unlink()
    if p["blocking_modified"]:
        _git(root, "restore", "--source=HEAD", "--staged", "--worktree", "--", *p["blocking_modified"], check=True)
    m = _git(root, "merge", "--ff-only", f"{remote}/{branch}")
    p.update(backup=str(bk) if moved else None, backed_up=moved)
    if m.returncode != 0:
        return dict(p, state="FF_FAIL", rc=2, why=(m.stderr or m.stdout).strip()[:300])
    return dict(p, state="SYNCED", rc=0, head_after=_git(root, "rev-parse", "--short=9", "HEAD").stdout.strip())


def _receipt(res: dict) -> None:
    try:
        d = Path(res["repo"]) / "VeritasIntelligenceAnalytics" / "VIA_Reports" / "vcgc" / "sync"
        if not d.parent.parent.is_dir():
            d = Path(res["repo"]) / "VIA_Reports" / "vcgc" / "sync"
        d.mkdir(parents=True, exist_ok=True)
        (d / "REPO_SYNC_latest.json").write_text(json.dumps(dict(res, tool=TAG, ts=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())),
                                                            ensure_ascii=False, indent=1), encoding="utf-8")
    except (OSError, KeyError):
        pass


def _say(res: dict, applied: bool) -> None:
    st = res.get("state")
    head = f"[{TAG}] {st} · {res.get('branch', '?')} {res.get('head', '')} → {res.get('target', '')} {res.get('upstream', '')}"
    if "behind" in res:
        head += f" · 少 {res['behind']} 個提交 · 多 {res.get('ahead', 0)} 個"
    print(head, flush=True)
    if res.get("why"):
        print(f"  原因:{res['why']}")
    if res.get("fix"):
        print(f"  先跑:{res['fix']}")
    for k, zh in (("blocking_untracked", "擋路的未追蹤檔(main 上同名)"), ("blocking_modified", "擋路的本機改動(main 也改了)")):
        for x in res.get(k) or []:
            print(f"  {zh}:{x}")
    if res.get("backup"):
        print(f"  已備份 {len(res['backed_up'])} 檔 → {res['backup']}(main 為準;要找回原樣從這裡拿)")
    if st == "BEHIND" and not applied:
        print(f"  [乾跑] 零寫入;加 --apply 才搬擋路檔並快轉 · 本機其餘改動 {res.get('kept_local', 0)} 檔原樣保留")
    if st == "SYNCED":
        print(f"  快轉完成 → {res.get('head_after')} · 本機其餘改動 {res.get('kept_local', 0)} 檔原樣保留")


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] == ["--selftest"]:
        return selftest()

    def opt(k, d=None):
        return a[a.index(k) + 1] if k in a and a.index(k) + 1 < len(a) else d
    repo = opt("--repo", str(Path(__file__).resolve().parent))
    kw = dict(branch=opt("--branch", "main"), remote=opt("--remote", "origin"))
    res = apply(repo, backup_dir=opt("--backup-dir"), **kw) if "--apply" in a else plan(repo, **kw)
    _say(res, "--apply" in a)
    if "--apply" in a and "repo" in res:
        _receipt(res)
    return int(res.get("rc", 2))


def selftest() -> int:
    import tempfile
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note and not cond else ''}")

    def sh(cwd, *a):
        return subprocess.run(["git", "-C", str(cwd), *a], capture_output=True, text=True, check=True)
    print(f"=== {TAG} · 自測(暫存倉 · 重現桌機實錄 · 零網路)===")
    with tempfile.TemporaryDirectory(prefix="repo_sync_") as td:
        t = Path(td)
        up, desk, dev = t / "up.git", t / "desk", t / "dev"
        subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(up)], check=True)
        subprocess.run(["git", "clone", "-q", str(up), str(dev)], check=True)
        for c in (dev,):
            sh(c, "config", "user.email", "t@t"); sh(c, "config", "user.name", "t")
        (dev / "a.txt").write_text("a1\n"); (dev / "led.jsonl").write_text("l1\n"); (dev / "keep.txt").write_text("k1\n")
        sh(dev, "add", "-A"); sh(dev, "commit", "-qm", "c1"); sh(dev, "push", "-q", "origin", "main")
        subprocess.run(["git", "clone", "-q", str(up), str(desk)], check=True)
        sh(desk, "config", "user.email", "d@d"); sh(desk, "config", "user.name", "d")
        (dev / "reg").mkdir(); (dev / "reg" / "v0113.json").write_text('{"main":1}\n'); (dev / "a.txt").write_text("a2\n")
        sh(dev, "add", "-A"); sh(dev, "commit", "-qm", "c2"); sh(dev, "push", "-q", "origin", "main")
        (desk / "reg").mkdir(); (desk / "reg" / "v0113.json").write_text('{"desktop":1}\n')        # 桌機自己生的同名檔
        (desk / "a.txt").write_text("a-local\n")                                                    # main 也改了的本機改動
        (desk / "keep.txt").write_text("k-local\n")                                                 # main 沒碰的本機改動
        (desk / "new_local.py").write_text("x = 1\n"); sh(desk, "add", "new_local.py")              # 暫存區新增(main 沒有)
        raw = subprocess.run(["git", "-C", str(desk), "pull", "--ff-only", "origin", "main"], capture_output=True, text=True)
        chk("① 重現:直接 pull 被擋(untracked would be overwritten)", raw.returncode != 0 and "overwritten" in (raw.stderr + raw.stdout), raw.stderr[-120:])
        before = {p: p.read_bytes() for p in desk.rglob("*") if p.is_file() and ".git" not in p.parts}
        p = plan(desk)
        after = {p_: p_.read_bytes() for p_ in desk.rglob("*") if p_.is_file() and ".git" not in p_.parts}
        chk("② 乾跑:BEHIND 1 · 擋路未追蹤 reg/v0113.json · 擋路改動 a.txt · 工作樹零寫入",
            p["state"] == "BEHIND" and p["behind"] == 1 and p["blocking_untracked"] == ["reg/v0113.json"] and p["blocking_modified"] == ["a.txt"]
            and before == after, p)
        bk = t / "bk"
        r = apply(desk, backup_dir=bk)
        chk("③ --apply:快轉到 main(SYNCED)· 擋路兩檔先備份(內容是桌機原樣)",
            r["state"] == "SYNCED" and (bk / "reg" / "v0113.json").read_text() == '{"desktop":1}\n' and (bk / "a.txt").read_text() == "a-local\n", r)
        chk("④ main 為準:reg/v0113.json · a.txt 是 main 的內容",
            (desk / "reg" / "v0113.json").read_text() == '{"main":1}\n' and (desk / "a.txt").read_text() == "a2\n")
        st = subprocess.run(["git", "-C", str(desk), "status", "--porcelain"], capture_output=True, text=True).stdout
        chk("⑤ main 沒碰的本機改動照留(keep.txt 改動 · 暫存新增 new_local.py)",
            (desk / "keep.txt").read_text() == "k-local\n" and "A  new_local.py" in st, st)
        chk("⑥ 再跑一次 = UP_TO_DATE(冪等)", plan(desk)["state"] == "UP_TO_DATE")
        sh(desk, "switch", "-q", "-c", "other")
        w = plan(desk)
        chk("⑦ 不在 main → WRONG_BRANCH · 給 switch 那一行 · 零寫入", w["state"] == "WRONG_BRANCH" and "switch main" in w.get("fix", ""), w)
        sh(desk, "switch", "-q", "main")
        sh(desk, "add", "-A"); sh(desk, "commit", "-qm", "local")
        (dev / "a.txt").write_text("a3\n"); sh(dev, "commit", "-qam", "c3"); sh(dev, "push", "-q", "origin", "main")
        dv = apply(desk)
        chk("⑧ 本機有自己的提交(分歧)→ DIVERGED 停 · 不重寫歷史", dv["state"] == "DIVERGED" and dv["rc"] == 2, dv)
        chk("⑨ 不是 git 倉 → NOT_REPO(rc 2)", plan(t)["state"] == "NOT_REPO")
    src = Path(__file__).read_text(encoding="utf-8")
    body = src.split("def selftest", 1)[0]
    chk("⑩ 加速器橋 · 網路橋在;不碰 TA-Lib;不寫同意閘;沒有 reset --hard / push --force / clean -f",
        "[VIA:ACCEL-BRIDGE:v0100]" in src and "[VIA:NET-BRIDGE:v0100]" in src and "def _via_net" in src
        and "talib" not in body.lower() and "VIA_NET_CONSENT\"]" not in body
        and not any(x in body for x in ('"reset", "--hard"', '"--force"', '"clean", "-f')))
    print(f"  [計] {TAG} 自測 {sum(ok)}/{len(ok)} · {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
