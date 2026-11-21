#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VIA_RepoSafeSync v0102 — 薄尾:修 PR 709 Codex 對 v0101 的三項;其餘照 v0101 / v0100

  ① P1 目錄 / 檔案祖孫衝突:上游新增檔 cache,本機有被忽略的目錄 cache/(內有 cache/secret)→ v0101 只比完全相同的路徑,
     漏掉,merge 覆蓋被忽略的檔時整個目錄沒備份就沒了。反過來(本機檔 d · 上游新增 d/x)也一樣。
     本版擋路 = 本機路徑和上游路徑「相同 · 是它的上層 · 是它的下層」三種都算;搬走後留下的空目錄一併收掉(只收空的)。
  ② P2 備份命名空間:v0101 工作樹層存 <備份>/<路徑>、暫存層存 <備份>/_index/<路徑>,倉裡真的有 _index/f 時兩層互蓋。
     本版分兩個夾:<備份>/worktree/<路徑> · <備份>/index/<路徑>,倉內任何路徑都撞不到。
  ③ P2 符號連結:v0101 用 is_file() 判斷,指向不存在目標的連結不備份;copy2 也會順著連結抄目標內容。
     本版用 lexists 判斷,連結原樣備份成連結(建不了連結的系統改存 <路徑>.symlink.txt 記目標),不順著連結。
其餘(只在 main 快轉 · 分歧停 · main 為準 · 不刪本機獨有的檔 · 不重寫歷史 · -z 路徑 · 收據)全照前版。用法同 v0100。
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
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VIA_RepoSafeSync"
TAG = "VIA_RepoSafeSync v0102"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem + "_for_v0102", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
BASE = PRIOR.PRIOR                                      # v0100 本體(main / _say / 收據都在這裡,叫模組全域的 plan / apply)
_git, _z = PRIOR._git, PRIOR._z
_PLAN_V0100 = PRIOR._PLAN_V0100
_PLAN_V0101, _APPLY_V0101 = PRIOR.plan, PRIOR.apply


def __getattr__(name):
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def _ancestors(rel: str) -> list:
    parts = rel.split("/")
    return ["/".join(parts[:k]) for k in range(1, len(parts))]


def _collides(rel: str, incoming: set, incoming_dirs: set) -> bool:
    """相同 · 本機路徑是上游路徑的上層目錄 · 上游路徑是本機路徑的上層。"""
    return rel in incoming or rel in incoming_dirs or any(a in incoming for a in _ancestors(rel))


def plan(repo, branch: str = "main", remote: str = "origin", fetch: bool = True) -> dict:
    p = _PLAN_V0100(repo, branch, remote, fetch)
    if p.get("state") != "BEHIND":
        return p
    root, up = Path(p["repo"]), f"{remote}/{branch}"
    incoming = set(_z(_git(root, "-c", "core.quotepath=off", "diff", "--name-only", "-z", "HEAD", up)))
    incoming_dirs = {a for r in incoming for a in _ancestors(r)}
    untracked_all = set(_z(_git(root, "ls-files", "--others", "-z")))                 # 含被忽略的,逐檔列(目錄內的檔也列)
    ignored = set(_z(_git(root, "ls-files", "--others", "--ignored", "--exclude-standard", "-z")))
    work = set(_z(_git(root, "diff", "--name-only", "-z", "HEAD")))
    staged = set(_z(_git(root, "diff", "--cached", "--name-only", "-z", "HEAD")))
    modified = work | staged

    def hit(s):
        return sorted(r for r in s if _collides(r, incoming, incoming_dirs))
    bu, bm = hit(untracked_all), hit(modified)
    p.update(incoming=len(incoming), blocking_untracked=bu, blocking_modified=bm, blocking_ignored=hit(ignored),
             blocking_staged=hit(staged), blocking_nested=sorted(r for r in bu + bm if r not in incoming),
             kept_local=len((untracked_all - ignored | modified) - set(bu) - set(bm)))
    return p


def _backup_path(src: Path, dst: Path) -> bool:
    """不順著連結:連結存成連結(建不了就存 .symlink.txt 記目標);一般檔 copy2。回傳有沒有存到。"""
    if not os.path.lexists(src):
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.is_symlink():
        target = os.readlink(src)
        try:
            os.symlink(target, dst)
        except OSError:
            Path(str(dst) + ".symlink.txt").write_text(str(target), encoding="utf-8")
        return True
    if src.is_file():
        shutil.copy2(src, dst, follow_symlinks=False)
        return True
    return False


def _drop(root: Path, rel: str) -> None:
    f = root / rel
    if f.is_symlink() or f.is_file():
        f.unlink()
    d = f.parent                                         # 收掉因此變空的上層目錄(只收空的,不出倉根)
    while d != root and d.is_dir() and not d.is_symlink() and not any(d.iterdir()):
        d.rmdir()
        d = d.parent


def apply(repo, branch: str = "main", remote: str = "origin", backup_dir=None) -> dict:
    p = plan(repo, branch, remote)
    if p.get("state") != "BEHIND":
        return p
    root = Path(p["repo"])
    ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    bk = Path(backup_dir) if backup_dir else root.parent / "VIA_SyncBackup" / ts
    saved = []
    for rel in sorted(set(p["blocking_untracked"] + p["blocking_modified"])):
        if _backup_path(root / rel, bk / "worktree" / rel):
            saved.append("worktree/" + rel)
    for rel in p["blocking_staged"]:                                                    # 暫存區那層另一個夾
        blob = subprocess.run(["git", "-C", str(root), "show", f":{rel}"], capture_output=True)
        if blob.returncode == 0:
            dst = bk / "index" / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(blob.stdout)
            saved.append("index/" + rel)
    for rel in p["blocking_untracked"]:
        _drop(root, rel)
    tracked_mod = [r for r in p["blocking_modified"] if _git(root, "cat-file", "-e", f"HEAD:{r}").returncode == 0]
    new_staged = [r for r in p["blocking_modified"] if r not in tracked_mod]
    if tracked_mod:
        _git(root, "restore", "--source=HEAD", "--staged", "--worktree", "--", *tracked_mod, check=True)
    if new_staged:
        _git(root, "rm", "-q", "--cached", "-f", "--", *new_staged, check=True)
        for r in new_staged:
            _drop(root, r)
    m = _git(root, "merge", "--ff-only", f"{remote}/{branch}")
    p.update(backup=str(bk) if saved else None, backed_up=saved)
    if m.returncode != 0:
        return dict(p, state="FF_FAIL", rc=2, why=(m.stderr or m.stdout).strip()[:300])
    return dict(p, state="SYNCED", rc=0, head_after=_git(root, "rev-parse", "--short=9", "HEAD").stdout.strip())


BASE.plan, BASE.apply = plan, apply                    # v0100 main / _say 用模組全域叫 plan / apply
PRIOR.plan, PRIOR.apply = plan, apply


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] == ["--selftest"]:
        return selftest()
    return BASE.main(a)


def selftest() -> int:
    import tempfile
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note and not cond else ''}")

    keep = (BASE.plan, BASE.apply, PRIOR.plan, PRIOR.apply)
    BASE.plan, BASE.apply = _PLAN_V0101, _APPLY_V0101
    PRIOR.plan, PRIOR.apply = _PLAN_V0101, _APPLY_V0101
    try:
        rc0 = PRIOR.selftest()
    finally:
        BASE.plan, BASE.apply, PRIOR.plan, PRIOR.apply = keep
    print(f"=== {TAG} · 薄尾自測(目錄祖孫衝突 · 備份兩夾 · 符號連結;暫存倉 · 零網路)===")
    chk("⓪ 前版 v0101 自測過(含 v0100)", rc0 == 0, f"rc {rc0}")
    can_link = True
    with tempfile.TemporaryDirectory() as td0:
        try:
            os.symlink("x", Path(td0) / "l")
        except (OSError, NotImplementedError):
            can_link = False

    def sh(cwd, *a):
        return subprocess.run(["git", "-C", str(cwd), *a], capture_output=True, text=True, check=True)
    with tempfile.TemporaryDirectory(prefix="repo_sync102_") as td:
        t = Path(td)
        up, desk, dev = t / "up.git", t / "desk", t / "dev"
        subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(up)], check=True)
        subprocess.run(["git", "clone", "-q", str(up), str(dev)], check=True, capture_output=True)
        sh(dev, "config", "user.email", "t@t"); sh(dev, "config", "user.name", "t")
        (dev / ".gitignore").write_text("cache\ncache/\n")
        (dev / "f").write_text("f1\n"); (dev / "_index").mkdir(); (dev / "_index" / "f").write_text("if1\n")
        (dev / "ln.txt").write_text("ln1\n"); (dev / "keep.txt").write_text("k1\n"); (dev / "中文.txt").write_text("c1\n")
        sh(dev, "add", "-A"); sh(dev, "commit", "-qm", "c1"); sh(dev, "push", "-q", "origin", "main")
        subprocess.run(["git", "clone", "-q", str(up), str(desk)], check=True, capture_output=True)
        sh(desk, "config", "user.email", "d@d"); sh(desk, "config", "user.name", "d")
        (dev / "cache").write_text("main-cache\n"); sh(dev, "add", "-f", "cache")          # 上游新增檔 cache(本機是被忽略的目錄)
        (dev / "d").mkdir(); (dev / "d" / "x").write_text("main-dx\n"); sh(dev, "add", "d/x")  # 上游新增 d/x(本機有檔 d)
        (dev / "f").write_text("f2\n"); (dev / "_index" / "f").write_text("if2\n"); (dev / "ln.txt").write_text("ln2\n")
        (dev / "中文.txt").write_text("c2\n")
        sh(dev, "commit", "-qam", "c2"); sh(dev, "push", "-q", "origin", "main")
        (desk / "cache").mkdir(); (desk / "cache" / "secret").write_text("desk-secret\n")       # ① 祖孫:被忽略的目錄
        (desk / "d").write_text("desk-d\n")                                                     # ① 反向:本機檔 d
        (desk / "f").write_text("f-staged\n"); sh(desk, "add", "f"); (desk / "f").write_text("f-work\n")   # ② 兩層 + 撞名夾
        (desk / "_index" / "f").write_text("desk-index-f\n")
        if can_link:
            (desk / "ln.txt").unlink(); os.symlink("no-such-target", desk / "ln.txt")            # ③ 懸空連結取代追蹤檔
        (desk / "中文.txt").write_text("c-local\n"); (desk / "keep.txt").write_text("k-local\n")  # keep.txt 上游沒碰 → 照留
        p = plan(desk)
        chk("① 擋路含 cache/secret(上游新增 cache)· d(上游新增 d/x)· 標在 blocking_nested · keep.txt 不擋",
            {"cache/secret", "d"} <= set(p["blocking_untracked"]) and {"cache/secret", "d"} <= set(p["blocking_nested"])
            and "keep.txt" not in p["blocking_modified"], p)
        bk = t / "bk"
        r = apply(desk, backup_dir=bk)
        chk("② SYNCED · 祖孫衝突兩向都先備份(worktree/cache/secret · worktree/d)", r["state"] == "SYNCED"
            and (bk / "worktree" / "cache" / "secret").read_text() == "desk-secret\n" and (bk / "worktree" / "d").read_text() == "desk-d\n", r)
        chk("③ 備份兩夾不互蓋:worktree/f · worktree/_index/f · index/f 各是自己的內容",
            (bk / "worktree" / "f").read_text() == "f-work\n" and (bk / "worktree" / "_index" / "f").read_text() == "desk-index-f\n"
            and (bk / "index" / "f").read_text() == "f-staged\n")
        if can_link:
            b = bk / "worktree" / "ln.txt"
            chk("④ 懸空連結原樣備份成連結(不順著連結)", b.is_symlink() and os.readlink(b) == "no-such-target")
        else:
            chk("④ 這台建不了連結:略過連結檢(其餘照驗)", True)
        chk("⑤ main 為準:cache · d/x · f · _index/f · ln.txt · 中文.txt 都是 main 的內容;keep.txt 本機改動照留",
            (desk / "cache").read_text() == "main-cache\n" and (desk / "d" / "x").read_text() == "main-dx\n"
            and (desk / "f").read_text() == "f2\n" and (desk / "_index" / "f").read_text() == "if2\n"
            and not (desk / "ln.txt").is_symlink() and (desk / "ln.txt").read_text() == "ln2\n"
            and (desk / "中文.txt").read_text() == "c2\n" and (desk / "keep.txt").read_text() == "k-local\n")
        chk("⑥ 再跑 = UP_TO_DATE(冪等)", plan(desk)["state"] == "UP_TO_DATE")
    chk("⑦ 換裝:v0100 main 叫到的 plan / apply = 本版", BASE.plan is plan and BASE.apply is apply)
    src = Path(__file__).read_text(encoding="utf-8")
    body = src.split("def selftest", 1)[0]
    chk("⑧ 加速器橋 · 網路橋在;不碰 TA-Lib;沒有 reset --hard / push --force / clean -f",
        "[VIA:ACCEL-BRIDGE:v0100]" in src and "[VIA:NET-BRIDGE:v0100]" in src and "talib" not in body.lower()
        and not any(x in body for x in ('"reset", "--hard"', '"--force"', '"clean", "-f')))
    names = [n for n in dir(PRIOR) if not n.startswith("_") and callable(getattr(PRIOR, n, None))]
    chk("⑨ 尾版保有前版公開名稱(TAILAPI)", all(getattr(sys.modules[__name__], n, None) is not None for n in names), f"{len(names)} 支")
    print(f"  [計] {TAG} 本版 {sum(ok)}/{len(ok)} · {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
