#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VIA_RepoSafeSync v0103 — 薄尾:修 PR 709 Codex 對 v0102 的兩項,並把同一類問題一次封住(先備份 · 逐項驗過 · 才動工作樹)

  ① P1 目錄型擋路:被忽略的目錄本身是巢狀 git 倉時,git 只列 cache/(不展開),v0102 只備一般檔 → 整個巢狀倉沒備份就被刪。
     本版目錄型擋路整棵複製(含 .git、連結照原樣);刪除只在備份逐項比對過之後。
  ② P2 連結退路撞名:建不了連結時 v0102 寫 <路徑>.symlink.txt,和倉內真的叫 link.symlink.txt 的檔同一個夾 → 互蓋。
     本版連結目標一律記在 <備份>/manifest.json(倉內路徑撞不到);建得了連結時另外放一個連結,方便直接看。
  一次封住的其他格(LL-20261121-17:不再只修被點名的那一種):
   · 失敗就停:任何一項備不起來(特殊檔 FIFO / socket — git 不列,另查上游路徑在磁碟上的型別 · 權限 · 磁碟滿)或備份比對不合 → BACKUP_FAIL,工作樹零改動。
   · 大小寫:core.ignorecase=true(Windows / macOS 預設)時 README.md 與 Readme.md 算同一路徑。
   · 備份夾不得在倉內(不然被 git 當未追蹤檔);同名備份夾已存在且非空 → 加 -N,不覆蓋舊備份。
   · 備份夾三區:worktree/<路徑> · index/<路徑> · manifest.json(每一項的型別 · 大小 · 連結目標 · 驗證結果)。
其餘(只在 main 快轉 · 分歧停 · main 為準 · 本機獨有的檔不動 · 不重寫歷史 · -z 路徑 · 收據)全照前版。用法同 v0100。
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
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VIA_RepoSafeSync"
TAG = "VIA_RepoSafeSync v0103"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem + "_for_v0103", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
BASE = PRIOR.BASE                                       # v0100 本體(main / _say / 收據;叫模組全域的 plan / apply)
_git, _z, _ancestors = PRIOR._git, PRIOR._z, PRIOR._ancestors
_PLAN_V0100 = PRIOR._PLAN_V0100
_PLAN_V0102, _APPLY_V0102 = PRIOR.plan, PRIOR.apply


def __getattr__(name):
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


class BackupError(RuntimeError):
    pass


def _ignorecase(root: Path) -> bool:
    return (_git(root, "config", "--bool", "core.ignorecase").stdout or "").strip() == "true"


def plan(repo, branch: str = "main", remote: str = "origin", fetch: bool = True) -> dict:
    p = _PLAN_V0100(repo, branch, remote, fetch)
    if p.get("state") != "BEHIND":
        return p
    root, up = Path(p["repo"]), f"{remote}/{branch}"
    fold = _ignorecase(root)

    def key(r):
        return r.casefold() if fold else r
    incoming = {key(r) for r in _z(_git(root, "-c", "core.quotepath=off", "diff", "--name-only", "-z", "HEAD", up))}
    incoming_dirs = {key(a) for r in incoming for a in _ancestors(r)}

    def collides(r):
        return key(r) in incoming or key(r) in incoming_dirs or any(key(a) in incoming for a in _ancestors(r))

    def norm(xs):
        return {x.rstrip("/") for x in xs if x.rstrip("/")}       # 巢狀倉 / 未展開目錄 git 寫成 cache/
    untracked_all = norm(_z(_git(root, "ls-files", "--others", "-z")))
    ignored = norm(_z(_git(root, "ls-files", "--others", "--ignored", "--exclude-standard", "-z")))
    work = norm(_z(_git(root, "diff", "--name-only", "-z", "HEAD")))
    staged = norm(_z(_git(root, "diff", "--cached", "--name-only", "-z", "HEAD")))
    modified = work | staged

    def hit(s):
        return sorted(r for r in s if collides(r))
    bu, bm = hit(untracked_all), hit(modified)
    raw_in = _z(_git(root, "-c", "core.quotepath=off", "diff", "--name-only", "-z", "HEAD", up))
    special = sorted({r for x in raw_in for r in [x, *_ancestors(x)] if _kind(root / r) == "special"})   # git 不列 FIFO / socket
    p.update(incoming=len(incoming), ignorecase=fold, blocking_special=special, blocking_untracked=bu, blocking_modified=bm, blocking_ignored=hit(ignored),
             blocking_staged=hit(staged), blocking_nested=sorted(r for r in bu + bm if key(r) not in incoming),
             kept_local=len((untracked_all - ignored | modified) - set(bu) - set(bm)))
    return p


def _kind(p: Path):
    if not os.path.lexists(p):
        return None
    if p.is_symlink():
        return "link"
    st = p.lstat().st_mode
    if stat.S_ISDIR(st):
        return "dir"
    if stat.S_ISREG(st):
        return "file"
    return "special"


def _tree_sig(d: Path) -> list:
    """目錄指紋:每一項的相對路徑 · 型別 · 大小或連結目標(不順著連結)。"""
    out = []
    for cur, dirs, files in os.walk(d, followlinks=False):
        for n in sorted(dirs + files):
            q = Path(cur) / n
            k = _kind(q)
            rel = q.relative_to(d).as_posix()
            out.append((rel, k, os.readlink(q) if k == "link" else (q.lstat().st_size if k == "file" else 0)))
    return sorted(out)


def _backup_dir(root: Path, backup_dir) -> Path:
    bk = Path(backup_dir) if backup_dir else root.parent / "VIA_SyncBackup" / time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    bk = bk.resolve()
    try:
        bk.relative_to(root.resolve())
        raise BackupError(f"備份夾在倉內:{bk}(會被 git 當成未追蹤檔)")
    except ValueError:
        pass
    base, n = bk, 1
    while bk.exists() and any(bk.iterdir()):
        bk, n = base.with_name(f"{base.name}-{n}"), n + 1
    return bk


def _backup_all(root: Path, p: dict, bk: Path) -> dict:
    """全部備份 + 逐項比對;任何一項不合就丟 BackupError(此時工作樹還沒動)。"""
    man = {"tool": TAG, "repo": str(root), "worktree": [], "index": [], "links": {}}
    for rel in sorted(set(p["blocking_untracked"] + p["blocking_modified"])):
        src, dst = root / rel, bk / "worktree" / rel
        k = _kind(src)
        if k is None:
            continue                                              # 本機已刪:內容就是 HEAD,沒有要留的
        dst.parent.mkdir(parents=True, exist_ok=True)
        if k == "file":
            shutil.copy2(src, dst, follow_symlinks=False)
            okv = dst.read_bytes() == src.read_bytes()
        elif k == "link":
            target = os.readlink(src)
            man["links"][rel] = target                            # 正本記在 manifest;倉內檔名撞不到
            try:
                os.symlink(target, dst)
            except OSError:
                pass
            okv = man["links"][rel] == os.readlink(src)
        elif k == "dir":
            shutil.copytree(src, dst, symlinks=True)
            okv = _tree_sig(src) == _tree_sig(dst)
        else:
            raise BackupError(f"{rel}:不能備份的檔案型別(FIFO / socket / 裝置)")
        if not okv:
            raise BackupError(f"{rel}:備份比對不合")
        man["worktree"].append({"path": rel, "kind": k})
    for rel in p["blocking_staged"]:
        blob = subprocess.run(["git", "-C", str(root), "show", f":{rel}"], capture_output=True)
        if blob.returncode != 0:
            continue                                              # 暫存區是刪除:沒有內容要留
        dst = bk / "index" / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(blob.stdout)
        if dst.read_bytes() != blob.stdout:
            raise BackupError(f"index/{rel}:備份比對不合")
        man["index"].append({"path": rel, "kind": "blob", "size": len(blob.stdout)})
    bk.mkdir(parents=True, exist_ok=True)
    (bk / "manifest.json").write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
    return man


def _drop(root: Path, rel: str) -> None:
    f = root / rel
    k = _kind(f)
    if k in ("file", "link"):
        f.unlink()
    elif k == "dir":
        shutil.rmtree(f)                                          # 只在 _backup_all 比對過之後才會走到
    d = f.parent
    while d != root and d.is_dir() and not d.is_symlink() and not any(d.iterdir()):
        d.rmdir()
        d = d.parent


def apply(repo, branch: str = "main", remote: str = "origin", backup_dir=None) -> dict:
    p = plan(repo, branch, remote)
    if p.get("state") != "BEHIND":
        return p
    root = Path(p["repo"])
    blockers = p["blocking_untracked"] + p["blocking_modified"] + p["blocking_staged"]
    bk, man = None, None
    try:
        if p.get("blocking_special"):
            raise BackupError("擋路的是特殊檔(FIFO / socket / 裝置),git 不列也備不起來:" + " · ".join(p["blocking_special"][:5]))
        if blockers:
            bk = _backup_dir(root, backup_dir)
            man = _backup_all(root, p, bk)
    except (BackupError, OSError, shutil.Error) as exc:
        return dict(p, state="BACKUP_FAIL", rc=2, why=f"{type(exc).__name__}: {exc}"[:300], backup=str(bk) if bk else None,
                    backed_up=[], worktree_changed=False, fix="處理上面那一項(搬走 / 改權限 / 騰空間)後再跑;工作樹沒有被改")
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
    saved = ([("worktree/" + e["path"]) for e in man["worktree"]] + [("index/" + e["path"]) for e in man["index"]]) if man else []
    p.update(backup=str(bk) if saved else None, backed_up=saved, manifest=str(bk / "manifest.json") if saved else None)
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
    BASE.plan, BASE.apply = _PLAN_V0102, _APPLY_V0102
    PRIOR.plan, PRIOR.apply = _PLAN_V0102, _APPLY_V0102
    try:
        rc0 = PRIOR.selftest()
    finally:
        BASE.plan, BASE.apply, PRIOR.plan, PRIOR.apply = keep
    print(f"=== {TAG} · 薄尾自測(巢狀倉 · 連結退路 · 失敗就停 · 大小寫 · 備份夾;暫存倉 · 零網路)===")
    chk("⓪ 前版 v0102 自測過(含 v0101 · v0100)", rc0 == 0, f"rc {rc0}")

    def sh(cwd, *a):
        return subprocess.run(["git", "-C", str(cwd), *a], capture_output=True, text=True, check=True)

    def mk(t: Path, name: str, base_files: dict, main_change):
        up, desk, dev = t / f"{name}.git", t / f"{name}_desk", t / f"{name}_dev"
        subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(up)], check=True)
        subprocess.run(["git", "clone", "-q", str(up), str(dev)], check=True, capture_output=True)
        sh(dev, "config", "user.email", "t@t"); sh(dev, "config", "user.name", "t")
        for k, v in base_files.items():
            (dev / k).write_text(v)
        sh(dev, "add", "-A"); sh(dev, "commit", "-qm", "c1"); sh(dev, "push", "-q", "origin", "main")
        subprocess.run(["git", "clone", "-q", str(up), str(desk)], check=True, capture_output=True)
        sh(desk, "config", "user.email", "d@d"); sh(desk, "config", "user.name", "d")
        main_change(dev)
        sh(dev, "commit", "-qm", "c2"); sh(dev, "push", "-q", "origin", "main")
        return desk

    with tempfile.TemporaryDirectory(prefix="repo_sync103_") as td:
        t = Path(td)

        # ① 巢狀 git 倉被忽略 · 上游新增同名檔
        def ch1(dev):
            (dev / "cache").write_text("main-cache\n"); sh(dev, "add", "-f", "cache")
        desk = mk(t, "n", {".gitignore": "cache\ncache/\n", "a.txt": "a\n"}, ch1)
        (desk / "cache").mkdir(); subprocess.run(["git", "init", "-q", str(desk / "cache")], check=True)
        (desk / "cache" / "secret").write_text("desk-secret\n")
        p = plan(desk)
        r = apply(desk, backup_dir=t / "bk1")
        b = t / "bk1" / "worktree" / "cache"
        chk("① 巢狀倉 cache/ 整棵備份(含 .git 與 secret)後才快轉 · main 為準",
            "cache" in p["blocking_untracked"] and r["state"] == "SYNCED" and (b / "secret").read_text() == "desk-secret\n"
            and (b / ".git" / "HEAD").is_file() and (desk / "cache").read_text() == "main-cache\n", r)

        # ② 連結建不了時,目標記在 manifest,不會跟倉內 link.symlink.txt 互蓋
        can_link = True
        try:
            os.symlink("x", t / "probe")
        except (OSError, NotImplementedError):
            can_link = False

        def ch2(dev):
            (dev / "link").write_text("main-link\n"); (dev / "link.symlink.txt").write_text("main-txt\n")
            sh(dev, "add", "link", "link.symlink.txt")
        desk = mk(t, "l", {"x.txt": "x\n"}, ch2)
        if can_link:
            os.symlink("desk-target", desk / "link")
        (desk / "link.symlink.txt").write_text("desk-txt\n")
        real = os.symlink

        def boom(*a, **k):
            raise PermissionError("no symlink privilege (simulated)")
        os.symlink = boom
        try:
            r = apply(desk, backup_dir=t / "bk2")
        finally:
            os.symlink = real
        man = json.loads((t / "bk2" / "manifest.json").read_text(encoding="utf-8")) if (t / "bk2" / "manifest.json").is_file() else {}
        chk("② 建不了連結:目標記在 manifest.json · 倉內 link.symlink.txt 的本機內容另存不互蓋",
            r["state"] == "SYNCED" and (not can_link or man.get("links", {}).get("link") == "desk-target")
            and (t / "bk2" / "worktree" / "link.symlink.txt").read_text() == "desk-txt\n", (r, man))

        # ③ 失敗就停:擋路的是 FIFO(備不起來)→ BACKUP_FAIL,工作樹與 HEAD 都沒動
        if hasattr(os, "mkfifo"):
            def ch3(dev):
                (dev / "pipe").write_text("main\n"); (dev / "m.txt").write_text("m2\n"); sh(dev, "add", "pipe", "m.txt")
            desk = mk(t, "f", {"m.txt": "m1\n"}, ch3)
            os.mkfifo(desk / "pipe"); (desk / "m.txt").write_text("m-local\n")
            head0 = sh(desk, "rev-parse", "HEAD").stdout
            r = apply(desk, backup_dir=t / "bk3")
            chk("③ 備不起來(git 不列的 FIFO)→ blocking_special · BACKUP_FAIL · rc 2 · 工作樹零改動(m.txt 本機內容還在 · HEAD 沒動)",
                r.get("blocking_special") == ["pipe"] and r["state"] == "BACKUP_FAIL" and r["rc"] == 2 and (desk / "m.txt").read_text() == "m-local\n"
                and sh(desk, "rev-parse", "HEAD").stdout == head0, r)
        else:
            chk("③ 這台沒有 FIFO:略過(其餘照驗)", True)

        # ④ 大小寫不分的檔案系統設定:README.md 與 Readme.md 算同一路徑
        def ch4(dev):
            (dev / "Readme.md").write_text("main\n"); sh(dev, "add", "Readme.md")
        desk = mk(t, "c", {"z.txt": "z\n"}, ch4)
        sh(desk, "config", "core.ignorecase", "true")
        (desk / "README.md").write_text("desk-readme\n")
        r = apply(desk, backup_dir=t / "bk4")
        chk("④ core.ignorecase=true:README.md 擋 Readme.md · 先備份", "README.md" in r.get("blocking_untracked", [])
            and r["state"] == "SYNCED" and (t / "bk4" / "worktree" / "README.md").read_text() == "desk-readme\n", r)

        # ⑤ 備份夾在倉內 → 拒絕、零改動;⑥ 已存在且非空的備份夾不覆蓋
        def ch5(dev):
            (dev / "q.txt").write_text("q2\n"); sh(dev, "add", "q.txt")
        desk = mk(t, "b", {"q.txt": "q1\n"}, ch5)
        (desk / "q.txt").write_text("q-local\n")
        r = apply(desk, backup_dir=desk / "inside")
        chk("⑤ 備份夾在倉內 → BACKUP_FAIL · 工作樹零改動", r["state"] == "BACKUP_FAIL" and (desk / "q.txt").read_text() == "q-local\n", r)
        old = t / "bk6"; old.mkdir(); (old / "keep").write_text("old\n")
        r = apply(desk, backup_dir=old)
        chk("⑥ 備份夾已有東西 → 改用 bk6-1,舊備份不動 · SYNCED", r["state"] == "SYNCED" and (old / "keep").read_text() == "old\n"
            and (t / "bk6-1" / "worktree" / "q.txt").read_text() == "q-local\n", r)
        chk("⑦ 再跑 = UP_TO_DATE(冪等)", plan(desk)["state"] == "UP_TO_DATE")
    chk("⑧ 換裝:v0100 main 叫到的 plan / apply = 本版", BASE.plan is plan and BASE.apply is apply)
    src = Path(__file__).read_text(encoding="utf-8")
    body = src.split("def selftest", 1)[0]
    chk("⑨ 加速器橋 · 網路橋在;不碰 TA-Lib;沒有 reset --hard / push --force / clean -f",
        "[VIA:ACCEL-BRIDGE:v0100]" in src and "[VIA:NET-BRIDGE:v0100]" in src and "talib" not in body.lower()
        and not any(x in body for x in ('"reset", "--hard"', '"--force"', '"clean", "-f')))
    names = [n for n in dir(PRIOR) if not n.startswith("_") and callable(getattr(PRIOR, n, None))]
    chk("⑩ 尾版保有前版公開名稱(TAILAPI)", all(getattr(sys.modules[__name__], n, None) is not None for n in names), f"{len(names)} 支")
    print(f"  [計] {TAG} 本版 {sum(ok)}/{len(ok)} · {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
