#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VIA_RepoSafeSync v0101 — 薄尾:修 PR 709 Codex 三項(被忽略的檔 · 暫存區內容 · 中文路徑);其餘照 v0100

  ① P1 被 git 忽略的本機檔:上游開始追蹤某個本機被忽略的路徑時,v0100 用 --exclude-standard 看不到它,
     merge 預設會覆蓋被忽略的檔 → 沒備份就沒了。本版擋路清單改用「全部未追蹤(含被忽略)」∩ 上游要寫的路徑,一樣先備份再搬走。
  ② P1 暫存區內容:同一路徑有已暫存 + 未暫存兩層改動時,v0100 只備份工作樹那層,restore --staged 後暫存那層就消失。
     本版「改過」= 工作樹對 HEAD ∪ 暫存區對 HEAD;暫存區那層和 HEAD 不同時,另存到 <備份>/_index/<原路徑>(工作樹那層照存原路徑)。
  ③ P2 中文 / 特殊字元路徑:git 預設把非 ASCII 路徑轉成帶引號的八進位跳脫字串 → Path / restore 找不到。
     本版所有路徑清單一律 -z(NUL 分隔)讀,原樣處理(本倉滿是中文路徑)。
其餘(只在 main 快轉 · 分歧停 · main 為準 · 不刪檔 · 不重寫歷史 · 收據)全照 v0100。用法同 v0100。
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

import importlib.util
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VIA_RepoSafeSync"
TAG = "VIA_RepoSafeSync v0101"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem + "_for_v0101", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
_git = PRIOR._git
_PLAN_V0100, _APPLY_V0100 = PRIOR.plan, PRIOR.apply


def __getattr__(name):
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def _z(r) -> list:
    """NUL 分隔輸出 → 路徑清單(原樣,不經 git 的引號跳脫)。"""
    return [x for x in (r.stdout or "").split("\0") if x]


def plan(repo, branch: str = "main", remote: str = "origin", fetch: bool = True) -> dict:
    p = _PLAN_V0100(repo, branch, remote, fetch)
    if p.get("state") != "BEHIND":
        return p
    root, up = Path(p["repo"]), f"{remote}/{branch}"
    incoming = set(_z(_git(root, "-c", "core.quotepath=off", "diff", "--name-only", "-z", "HEAD", up)))
    untracked_all = set(_z(_git(root, "ls-files", "--others", "-z")))                 # 含被忽略的(不加 --exclude-standard)
    ignored = set(_z(_git(root, "ls-files", "--others", "--ignored", "--exclude-standard", "-z")))
    work = set(_z(_git(root, "diff", "--name-only", "-z", "HEAD")))
    staged = set(_z(_git(root, "diff", "--cached", "--name-only", "-z", "HEAD")))
    modified = work | staged
    p.update(incoming=len(incoming), blocking_untracked=sorted(untracked_all & incoming), blocking_modified=sorted(modified & incoming),
             blocking_ignored=sorted(ignored & incoming), blocking_staged=sorted(staged & incoming),
             kept_local=len((untracked_all - ignored | modified) - incoming))
    return p


def apply(repo, branch: str = "main", remote: str = "origin", backup_dir=None) -> dict:
    p = plan(repo, branch, remote)
    if p.get("state") != "BEHIND":
        return p
    root = Path(p["repo"])
    ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    bk = Path(backup_dir) if backup_dir else root.parent / "VIA_SyncBackup" / ts
    saved = []
    for rel in p["blocking_untracked"] + p["blocking_modified"]:
        src = root / rel
        if src.is_file():
            dst = bk / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            saved.append(rel)
    for rel in p["blocking_staged"]:                                                    # 暫存區那層另存(和 HEAD 不同才會在這清單)
        blob = subprocess.run(["git", "-C", str(root), "show", f":{rel}"], capture_output=True)
        if blob.returncode == 0:
            dst = bk / "_index" / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(blob.stdout)
            saved.append("_index/" + rel)
    for rel in p["blocking_untracked"]:
        f = root / rel
        if f.is_file() or f.is_symlink():
            f.unlink()
    tracked_mod = [r for r in p["blocking_modified"] if _git(root, "cat-file", "-e", f"HEAD:{r}").returncode == 0]
    new_staged = [r for r in p["blocking_modified"] if r not in tracked_mod]          # HEAD 沒有、只在暫存區新增的路徑
    if tracked_mod:
        _git(root, "restore", "--source=HEAD", "--staged", "--worktree", "--", *tracked_mod, check=True)
    if new_staged:
        _git(root, "rm", "-q", "--cached", "-f", "--", *new_staged, check=True)
        for r in new_staged:
            f = root / r
            if f.is_file():
                f.unlink()
    m = _git(root, "merge", "--ff-only", f"{remote}/{branch}")
    p.update(backup=str(bk) if saved else None, backed_up=saved)
    if m.returncode != 0:
        return dict(p, state="FF_FAIL", rc=2, why=(m.stderr or m.stdout).strip()[:300])
    return dict(p, state="SYNCED", rc=0, head_after=_git(root, "rev-parse", "--short=9", "HEAD").stdout.strip())


PRIOR.plan, PRIOR.apply = plan, apply                  # v0100 main / _say 用模組全域叫 plan / apply


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] == ["--selftest"]:
        return selftest()
    return PRIOR.main(a)


def selftest() -> int:
    import tempfile
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note and not cond else ''}")

    keep = (PRIOR.plan, PRIOR.apply)
    PRIOR.plan, PRIOR.apply = _PLAN_V0100, _APPLY_V0100
    try:
        rc0 = PRIOR.selftest()
    finally:
        PRIOR.plan, PRIOR.apply = keep
    print(f"=== {TAG} · 薄尾自測(被忽略的檔 · 暫存區 · 中文路徑;暫存倉 · 零網路)===")
    chk("⓪ 前版 v0100 自測過(v0100 原判法)", rc0 == 0, f"rc {rc0}")

    def sh(cwd, *a):
        return subprocess.run(["git", "-C", str(cwd), *a], capture_output=True, text=True, check=True)
    with tempfile.TemporaryDirectory(prefix="repo_sync101_") as td:
        t = Path(td)
        up, desk, dev = t / "up.git", t / "desk", t / "dev"
        subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(up)], check=True)
        subprocess.run(["git", "clone", "-q", str(up), str(dev)], check=True, capture_output=True)
        sh(dev, "config", "user.email", "t@t"); sh(dev, "config", "user.name", "t")
        (dev / ".gitignore").write_text("*.cache\n"); (dev / "s.txt").write_text("s1\n"); (dev / "中文.txt").write_text("c1\n")
        sh(dev, "add", "-A"); sh(dev, "commit", "-qm", "c1"); sh(dev, "push", "-q", "origin", "main")
        subprocess.run(["git", "clone", "-q", str(up), str(desk)], check=True, capture_output=True)
        sh(desk, "config", "user.email", "d@d"); sh(desk, "config", "user.name", "d")
        (dev / "keep.cache").write_text("main\n"); sh(dev, "add", "-f", "keep.cache")             # 上游開始追蹤被忽略的路徑
        (dev / "s.txt").write_text("s2\n"); (dev / "中文.txt").write_text("c2\n")
        sh(dev, "commit", "-qam", "c2"); sh(dev, "push", "-q", "origin", "main")
        (desk / "keep.cache").write_text("desk-ignored\n")                                          # 本機被忽略的同名檔
        (desk / "s.txt").write_text("staged\n"); sh(desk, "add", "s.txt"); (desk / "s.txt").write_text("worktree\n")  # 兩層改動
        (desk / "中文.txt").write_text("c-local\n")                                                 # 中文路徑的本機改動
        p = plan(desk)
        chk("① 擋路清單含被忽略的 keep.cache · 兩層改動 s.txt(且在暫存清單)· 中文路徑原樣(不是跳脫字串)",
            "keep.cache" in p["blocking_untracked"] and "keep.cache" in p["blocking_ignored"] and "s.txt" in p["blocking_staged"]
            and "中文.txt" in p["blocking_modified"], p)
        bk = t / "bk"
        r = apply(desk, backup_dir=bk)
        chk("② SYNCED · 被忽略的檔先備份(desk-ignored)· 中文檔備份原樣", r["state"] == "SYNCED"
            and (bk / "keep.cache").read_text() == "desk-ignored\n" and (bk / "中文.txt").read_text() == "c-local\n", r)
        chk("③ 兩層改動都留:工作樹層 → 原路徑 · 暫存層 → _index/", (bk / "s.txt").read_text() == "worktree\n"
            and (bk / "_index" / "s.txt").read_text() == "staged\n")
        chk("④ main 為準:三個檔都是 main 的內容", (desk / "keep.cache").read_text() == "main\n" and (desk / "s.txt").read_text() == "s2\n"
            and (desk / "中文.txt").read_text() == "c2\n")
        chk("⑤ 再跑 = UP_TO_DATE(冪等)", plan(desk)["state"] == "UP_TO_DATE")
    chk("⑥ 換裝:v0100 main 叫到的 plan / apply = 本版", PRIOR.plan is plan and PRIOR.apply is apply)
    src = Path(__file__).read_text(encoding="utf-8")
    body = src.split("def selftest", 1)[0]
    chk("⑦ 加速器橋 · 網路橋在;不碰 TA-Lib;沒有 reset --hard / push --force / clean -f",
        "[VIA:ACCEL-BRIDGE:v0100]" in src and "[VIA:NET-BRIDGE:v0100]" in src and "talib" not in body.lower()
        and not any(x in body for x in ('"reset", "--hard"', '"--force"', '"clean", "-f')))
    names = [n for n in dir(PRIOR) if not n.startswith("_") and callable(getattr(PRIOR, n, None))]
    chk("⑧ 尾版保有前版公開名稱(TAILAPI)", all(getattr(sys.modules[__name__], n, None) is not None for n in names), f"{len(names)} 支")
    print(f"  [計] {TAG} 本版 {sum(ok)}/{len(ok)} · {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
