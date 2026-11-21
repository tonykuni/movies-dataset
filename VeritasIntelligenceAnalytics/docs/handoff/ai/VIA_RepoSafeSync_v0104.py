#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VIA_RepoSafeSync v0104 — 薄尾:修 PR 709 Codex 對 v0103 一項(檔名被 git 當萬用字元);其餘照 v0103

  P2 pathspec 照字面:git restore / git rm 收到的路徑預設會套 pathspec 規則,檔名 a[1].txt(Windows 也合法)會同時配到 a1.txt,
     :(glob)*.txt 會配到所有 .txt → 沒在備份清單上的本機改動被一起還原、沒備份就沒了(容器重現 v0103:a1.txt 本機改動消失)。
     本版 plan / apply 整段在 GIT_LITERAL_PATHSPECS=1 下跑(git 官方開關:關掉 glob 與 pathspec magic,路徑一律照字面),
     跑完還原呼叫者原本的環境變數。
其餘(fail-closed 先備份 · 逐項驗過 · 才動工作樹 · 只在 main 快轉 · main 為準)全照 v0103。用法同 v0100。
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
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VIA_RepoSafeSync"
TAG = "VIA_RepoSafeSync v0104"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem + "_for_v0104", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
BASE = PRIOR.BASE                                       # v0100 本體(main / _say / 收據;叫模組全域的 plan / apply)
_PLAN_V0103, _APPLY_V0103 = PRIOR.plan, PRIOR.apply


def __getattr__(name):
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


@contextmanager
def literal_pathspecs():
    """這段裡所有 git 子行程的路徑都照字面(不 glob、不吃 :(magic));出來還原原值。"""
    old = os.environ.get("GIT_LITERAL_PATHSPECS")
    os.environ["GIT_LITERAL_PATHSPECS"] = "1"
    try:
        yield
    finally:
        if old is None:
            os.environ.pop("GIT_LITERAL_PATHSPECS", None)
        else:
            os.environ["GIT_LITERAL_PATHSPECS"] = old


def plan(repo, branch: str = "main", remote: str = "origin", fetch: bool = True) -> dict:
    with literal_pathspecs():
        return _PLAN_V0103(repo, branch, remote, fetch)


def apply(repo, branch: str = "main", remote: str = "origin", backup_dir=None) -> dict:
    with literal_pathspecs():
        return _APPLY_V0103(repo, branch, remote, backup_dir)


BASE.plan, BASE.apply = plan, apply                    # v0100 main / _say 用模組全域叫 plan / apply


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

    keep = (BASE.plan, BASE.apply)
    BASE.plan, BASE.apply = _PLAN_V0103, _APPLY_V0103
    try:
        rc0 = PRIOR.selftest()
    finally:
        BASE.plan, BASE.apply = keep
    print(f"=== {TAG} · 薄尾自測(檔名照字面:[ ] * ? :(glob);暫存倉 · 零網路)===")
    chk("⓪ 前版 v0103 自測過(含 v0102 · v0101 · v0100)", rc0 == 0, f"rc {rc0}")

    def sh(cwd, *a):
        return subprocess.run(["git", "-C", str(cwd), *a], capture_output=True, text=True, check=True)
    names = ["a[1].txt", "a1.txt", "b.txt"] + ([":(glob)*.txt", "c.txt"] if os.name != "nt" else [])
    with tempfile.TemporaryDirectory(prefix="repo_sync104_") as td:
        t = Path(td)
        up, desk, dev = t / "up.git", t / "desk", t / "dev"
        subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(up)], check=True)
        subprocess.run(["git", "clone", "-q", str(up), str(dev)], check=True, capture_output=True)
        sh(dev, "config", "user.email", "t@t"); sh(dev, "config", "user.name", "t")
        for n in names:
            (dev / n).write_text("1\n")
        sh(dev, "add", "-A"); sh(dev, "commit", "-qm", "c1"); sh(dev, "push", "-q", "origin", "main")
        subprocess.run(["git", "clone", "-q", str(up), str(desk)], check=True, capture_output=True)
        sh(desk, "config", "user.email", "d@d"); sh(desk, "config", "user.name", "d")
        changed = [n for n in names if n in ("a[1].txt", ":(glob)*.txt")]
        for n in changed:
            (dev / n).write_text("main\n")
        sh(dev, "commit", "-qam", "c2"); sh(dev, "push", "-q", "origin", "main")
        for n in changed:
            (desk / n).write_text("local-" + n + "\n")
        others = [n for n in names if n not in changed]
        for n in others:
            (desk / n).write_text("LOCAL-ONLY " + n + "\n")                 # 上游沒碰:不在擋路清單,必須原樣留著
        env0 = os.environ.get("GIT_LITERAL_PATHSPECS")
        r = apply(desk, backup_dir=t / "bk")
        chk("① SYNCED · 擋路只有上游改到的那幾個(照字面)", r["state"] == "SYNCED" and sorted(r["blocking_modified"]) == sorted(changed), r)
        chk("② 上游沒碰的 a1.txt / b.txt(/ c.txt)本機改動原樣留著", all((desk / n).read_text() == "LOCAL-ONLY " + n + "\n" for n in others))
        chk("③ 上游改到的那幾個:備份是本機內容 · 工作樹是 main", all((t / "bk" / "worktree" / n).read_text() == "local-" + n + "\n"
                                                              and (desk / n).read_text() == "main\n" for n in changed))
        chk("④ 呼叫完環境變數還原(GIT_LITERAL_PATHSPECS 原值)", os.environ.get("GIT_LITERAL_PATHSPECS") == env0)
        chk("⑤ 再跑 = UP_TO_DATE(冪等)", plan(desk)["state"] == "UP_TO_DATE")
    chk("⑥ 換裝:v0100 main 叫到的 plan / apply = 本版", BASE.plan is plan and BASE.apply is apply)
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
