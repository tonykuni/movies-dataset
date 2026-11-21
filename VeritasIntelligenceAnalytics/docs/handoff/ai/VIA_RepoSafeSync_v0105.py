#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VIA_RepoSafeSync v0105 — 薄尾:修 PR 709 Codex 對 v0104 一項(git 輸出的檔名位元組被改);並封住同源的 fail-open 洞

  P2 檔名位元組:v0100 的 _git 用 text=True + errors="replace" → 檔名裡的 \\r 被換行轉換成 \\n、非 UTF-8 位元組變 �,
     規劃與備份拿到的是「另一個路徑」→ 被忽略的本機檔沒備份就被覆蓋(容器重現 v0104:secret\\r.txt 與 \\xffbad.txt 都沒備到)。
     本版 _git 一律讀位元組,用 UTF-8 + surrogateescape 解碼(不轉換換行、不替換;交回 git / 檔案系統時原位元組還原),
     並換進整條前版鏈(v0100 ~ v0104 每一版的模組全域 _git)。
  同源洞:v0103 對「git 列了、磁碟上找不到」的未追蹤擋路檔直接略過(當成本機已刪)→ 路徑對不上時會靜靜放行。
     本版改成 fail-closed:未追蹤擋路檔在磁碟上找不到 = BACKUP_FAIL,工作樹零改動;備份階段任何意外例外也一律 BACKUP_FAIL。
  連帶:manifest.json / 收據遇到非 UTF-8 檔名時改用 ASCII 跳脫寫出(可原樣還原);畫面輸出不因檔名炸掉。
其餘全照 v0104(pathspec 照字面 · 先備份逐項驗過才動工作樹 · 只在 main 快轉 · main 為準)。用法同 v0100。
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
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VIA_RepoSafeSync"
TAG = "VIA_RepoSafeSync v0105"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem + "_for_v0105", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
BASE = PRIOR.BASE                                       # v0100 本體(main / _say / 收據;叫模組全域的 plan / apply)
plan, apply = PRIOR.plan, PRIOR.apply                   # 行為入口照 v0104(pathspec 照字面);本版換的是底下的 _git 與 _backup_all


def __getattr__(name):
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def _chain() -> list:
    """前版鏈上每一個模組(v0104 → v0103 → … → v0100)。"""
    out, mod = [], PRIOR
    while mod is not None and mod not in out:
        out.append(mod)
        mod = vars(mod).get("PRIOR")
    return out


_GIT_V0100 = vars(BASE)["_git"]


def _git(repo, *a, check=False):
    """位元組讀 git 輸出 → UTF-8 + surrogateescape 解碼:不轉換 \\r、不替換壞位元組;os.fsencode 可原樣還原。"""
    r = subprocess.run(["git", "-C", str(repo), *a], capture_output=True)
    res = subprocess.CompletedProcess(r.args, r.returncode, r.stdout.decode("utf-8", "surrogateescape"),
                                      r.stderr.decode("utf-8", "replace"))
    if check and res.returncode != 0:
        raise RuntimeError(f"git {' '.join(map(str, a))} rc {res.returncode}: {(res.stderr or res.stdout).strip()[:200]}")
    return res


V0103 = next(m for m in _chain() if hasattr(m, "BackupError") and "_backup_all" in vars(m) and "BackupError" in vars(m))
_BACKUP_ALL_V0103 = vars(V0103)["_backup_all"]


def _backup_all(root: Path, p: dict, bk: Path) -> dict:
    """fail-closed:git 列為未追蹤擋路、磁碟上卻找不到 → 路徑對不上,停(v0103 會當成本機已刪而略過);
    備份階段任何意外例外一律轉成 BackupError(apply 回 BACKUP_FAIL,工作樹零改動),不讓整支程式中途炸掉。"""
    missing = [r for r in p["blocking_untracked"] if not os.path.lexists(Path(root) / r)]
    if missing:
        raise V0103.BackupError("git 列了、磁碟上找不到(路徑對不上):" + " · ".join(repr(x) for x in missing[:5]))
    try:
        return _BACKUP_ALL_V0103(root, p, bk)
    except V0103.BackupError:
        raise
    except Exception as exc:  # noqa: BLE001 — fail-closed:備份階段任何意外都停
        raise V0103.BackupError(f"{type(exc).__name__}: {exc}") from exc


class _JsonSafe:
    """json 轉接:能用 UTF-8 寫就照原樣(中文可讀);含 surrogate(非 UTF-8 檔名)寫不出去時才改成 ASCII 跳脫(可原樣還原)。"""

    def __getattr__(self, name):
        return getattr(json, name)

    @staticmethod
    def dumps(obj, **kw):
        s = json.dumps(obj, **kw)
        try:
            s.encode("utf-8")
            return s
        except UnicodeEncodeError:
            return json.dumps(obj, **dict(kw, ensure_ascii=True))


for _m in _chain():                                     # 整條鏈換成位元組安全的 _git
    if "_git" in vars(_m):
        _m._git = _git
V0103._backup_all = _backup_all
V0103.json = BASE.json = _JsonSafe()                    # manifest.json 與收據 REPO_SYNC_latest.json
BASE.plan, BASE.apply = plan, apply


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    for stream in (sys.stdout, sys.stderr):                # 畫面輸出遇到非 UTF-8 檔名不炸(印成 \\xff)
        try:
            stream.reconfigure(errors="backslashreplace")
        except (AttributeError, ValueError):
            pass
    if a[:1] == ["--selftest"]:
        return selftest()
    BASE.TAG = TAG                                      # 畫面與收據的 tool 欄寫實際跑的尾版(前版一直印 v0100;自測時各版保留原名)
    return BASE.main(a)


def selftest() -> int:
    import tempfile
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note and not cond else ''}")

    rc0 = PRIOR.selftest()                              # 前版自測在本版的 _git 下跑(更嚴格的底層,前版行為不能退)
    print(f"=== {TAG} · 薄尾自測(檔名位元組原樣:\\r · 非 UTF-8 · 找不到就停;暫存倉 · 零網路)===")
    chk("⓪ 前版 v0104 自測過(含 v0103 ~ v0100;底層已換成位元組安全 _git)", rc0 == 0, f"rc {rc0}")

    def sh(cwd, *a):
        return subprocess.run(["git", "-C", str(cwd), *a], capture_output=True, check=True)
    posix = os.name != "nt"
    with tempfile.TemporaryDirectory(prefix="repo_sync105_") as td:
        t = Path(td)
        up, desk, dev = t / "up.git", t / "desk", t / "dev"
        subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(up)], check=True)
        subprocess.run(["git", "clone", "-q", str(up), str(dev)], check=True, capture_output=True)
        sh(dev, "config", "user.email", "t@t"); sh(dev, "config", "user.name", "t")
        (dev / ".gitignore").write_text("*.txt\n"); (dev / "k").write_text("k\n")
        sh(dev, "add", "-A"); sh(dev, "commit", "-qm", "c1"); sh(dev, "push", "-q", "origin", "main")
        subprocess.run(["git", "clone", "-q", str(up), str(desk)], check=True, capture_output=True)
        sh(desk, "config", "user.email", "d@d"); sh(desk, "config", "user.name", "d")
        names = ["中文 被忽略.txt"] + (["secret\r.txt", os.fsdecode(b"\xffbad.txt")] if posix else [])
        for n in names:
            (dev / n).write_text("main\n"); sh(dev, "add", "-f", "--", n)
        sh(dev, "commit", "-qm", "c2"); sh(dev, "push", "-q", "origin", "main")
        for i, n in enumerate(names):
            (desk / n).write_text(f"LOCAL-{i}\n")
        p = plan(desk)
        chk("① 擋路清單是磁碟上真的路徑(\\r 沒變 \\n · 壞位元組沒變 �)", sorted(p["blocking_untracked"]) == sorted(names)
            and all(os.path.lexists(desk / n) for n in p["blocking_untracked"]), [repr(x) for x in p.get("blocking_untracked", [])])
        r = apply(desk, backup_dir=t / "bk")
        chk("② SYNCED · 每個本機版本都在備份(worktree/<原名>)· 工作樹是 main",
            r["state"] == "SYNCED" and all((t / "bk" / "worktree" / n).read_text() == f"LOCAL-{i}\n" and (desk / n).read_text() == "main\n"
                                           for i, n in enumerate(names)), r)
        man = json.loads((t / "bk" / "manifest.json").read_text(encoding="utf-8"))
        chk("③ manifest.json 寫得出來、讀回來的路徑和原名一致", sorted(e["path"] for e in man["worktree"]) == sorted(names))
        chk("③b 再跑 = UP_TO_DATE(冪等)", plan(desk)["state"] == "UP_TO_DATE")
        fake = dict(p, blocking_untracked=["no-such-file"], blocking_modified=[], blocking_staged=[])
        try:
            _backup_all(desk, fake, t / "bk_missing")
            stopped = False
        except V0103.BackupError:
            stopped = True
        chk("④ git 列了、磁碟上找不到 → BackupError(fail-closed,不再略過)", stopped and not (t / "bk_missing").exists())
    import io
    buf = io.StringIO()
    rec_ok = True
    try:
        with tempfile.TemporaryDirectory() as td2:
            keep_tag, BASE.TAG = BASE.TAG, TAG
            try:
                BASE._receipt({"repo": td2, "state": "SYNCED", "blocking_untracked": [os.fsdecode(b"\xffx")] if posix else ["x"]})
            finally:
                BASE.TAG = keep_tag
            rec = Path(td2) / "VIA_Reports" / "vcgc" / "sync" / "REPO_SYNC_latest.json"
            got = json.loads(rec.read_text(encoding="utf-8")) if rec.is_file() else {}
            rec_ok = got.get("state") == "SYNCED" and got.get("tool") == TAG
    except Exception:  # noqa: BLE001
        rec_ok = False
    chk("④b 收據 REPO_SYNC_latest.json 遇到非 UTF-8 檔名照樣寫得出來 · tool 欄 = 本版", rec_ok)
    del buf
    chk("⑤ 整條鏈的 _git 都是本版(v0100 ~ v0104)", all(vars(m).get("_git", _git) is _git for m in _chain()) and BASE._git is _git)
    chk("⑥ 換裝:v0100 main 叫到的 plan / apply = 尾版入口 · v0103 的 _backup_all = 本版", BASE.plan is plan and BASE.apply is apply
        and V0103._backup_all is _backup_all)
    src = Path(__file__).read_text(encoding="utf-8")
    body = src.split("def selftest", 1)[0]
    chk("⑦ 加速器橋 · 網路橋在;不碰 TA-Lib;沒有 reset --hard / push --force / clean -f",
        "[VIA:ACCEL-BRIDGE:v0100]" in src and "[VIA:NET-BRIDGE:v0100]" in src and "talib" not in body.lower()
        and not any(x in body for x in ('"reset", "--hard"', '"--force"', '"clean", "-f')))
    pub = [n for n in dir(PRIOR) if not n.startswith("_") and callable(getattr(PRIOR, n, None))]
    chk("⑧ 尾版保有前版公開名稱(TAILAPI)", all(getattr(sys.modules[__name__], n, None) is not None for n in pub), f"{len(pub)} 支")
    print(f"  [計] {TAG} 本版 {sum(ok)}/{len(ok)} · {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
