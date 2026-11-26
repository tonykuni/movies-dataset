#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VIA_ReworkGuard v0104 — 薄尾(v0103 以前一字不動;已鎖成功,修改開新版):R2 開著的 PR 比對提速

操作員 2026-11-25:「出 ReworkGuard 新版 更快」。先量(容器 cProfile,v0103 `check`):總 72.7s,其中
  d_openpr(R2 開著的 PR 同號 / 同檔名)66.6s —— refs/remotes/pr/ 下約一千個 PR 頭,逐一 `git rev-parse` +
  最多兩次 `git merge-base --is-ancestor` + `git log -1`,共約 2,900 個 git 子行程。
本版只換 d_openpr 的「取 PR 頭與篩掉已併」那一段,判法逐字照 v0101:
  ① 一次 `git for-each-ref --format=%(refname) %(objectname) %(committerdate:unix)` 拿全部 PR 頭的 sha 與時間(取代逐一 rev-parse / log)
  ② 兩次 `git for-each-ref --merged=<base>` / `--merged=HEAD` 拿「已是 base 或 HEAD 祖先」的 PR 頭(= merge-base --is-ancestor,取代逐一比)
  ③ 剩下的(開著 · 未併 · 10 天內)才逐一 diff / added_ids,跟 v0101 一樣。
git 子行程 ≈ 2,900 → 個位數 + 剩下要比的 PR 數。結果與 v0103 相同(自測 ⓪ 用同一個暫存倉比兩版輸出)。
其餘全照 v0103 / v0102 / v0101 / v0100(經 v0100 模組全域換上 d_openpr)。
用法同 v0100:python VIA_ReworkGuard_v0104.py check [--fetch-prs] | report | causes | --selftest
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
import importlib.util
import re
import sys
from pathlib import Path

VERSION = "v0104"
HERE = Path(__file__).resolve()
FAMILY = "VIA_ReworkGuard"
TAG = "VIA_ReworkGuard " + VERSION


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.parent.glob(FAMILY + "_v*.py") if 0 <= _vnum(p) < _vnum(HERE)), key=_vnum)
_spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem + "_for_v0104", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
BASE = PRIOR.BASE                                         # v0100:run_check 叫它模組全域的 d_openpr
V1 = PRIOR.PRIOR.PRIOR                                    # v0101:d_openpr 的判法本體(base_ids · added_ids · VER · SKIPPED)
_SLOW_OPENPR, _V0103_TAG = BASE.d_openpr, PRIOR.TAG


def __getattr__(name):
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def _refs_merged_into(repo, commit: str) -> set:
    try:
        return {r for r in BASE.git(repo, "for-each-ref", "--format=%(refname)", f"--merged={commit}", "refs/remotes/pr/").split() if r}
    except RuntimeError:
        return set()                                      # 同 v0101:merge-base 失敗 = 不是祖先


def d_openpr(repo, base, ch, fetch: bool, open_prs: set | None = None) -> list:
    """同 v0101 的判法;只把「每個 PR 頭逐一 rev-parse / merge-base / log」換成三次批次 for-each-ref。"""
    open_prs = BASE.open_pr_list() if open_prs is None else open_prs
    if fetch:
        BASE.git(repo, "fetch", "-q", "origin", "+refs/pull/*/head:refs/remotes/pr/*", check=False)
    rows = []
    for ln in BASE.git(repo, "for-each-ref", "--format=%(refname) %(objectname) %(committerdate:unix)", "refs/remotes/pr/").splitlines():
        parts = ln.split()
        if len(parts) == 3:
            rows.append((parts[0], parts[1], int(parts[2] or 0)))
    if not rows:
        return [("GRAY", "R2", "沒有開著的 PR 頭可比(加 --fetch-prs 抓;取號 / 出新版號前一定要比)")]
    known = V1.base_ids(repo, base)
    mine_files = {Path(p).name for p in ch["A"] + ch["U"] if V1.VER.match(Path(p).name)}
    mine = {k: v for k, v in V1.added_ids(repo, f"{base}...HEAD").items() if k not in known}
    head = BASE.git(repo, "rev-parse", "HEAD").strip()
    cutoff = BASE.time.time() - 10 * 86400
    cand = [(r, sha, ct) for r, sha, ct in rows if open_prs is None or r.split("/")[-1] in open_prs]
    merged = (_refs_merged_into(repo, base) | _refs_merged_into(repo, "HEAD")) if cand else set()
    out, compared = [], 0
    for r, sha, ct in cand:
        num = r.split("/")[-1]
        if sha == head or r in merged:
            continue
        if open_prs is None and ct < cutoff:
            continue
        try:
            names = {Path(p).name for p in BASE.git(repo, "diff", "--name-only", "--diff-filter=A", f"{base}...{r}").splitlines()}
        except RuntimeError as exc:
            V1.SKIPPED.append(f"#{num}:{str(exc)[:40]}")
            continue
        compared += 1
        theirs = {k: v for k, v in V1.added_ids(repo, f"{base}...{r}").items() if k not in known} if mine else {}
        lamp, who = ("RED", f"開著的 PR #{num}") if open_prs is not None else ("YELLOW", f"PR #{num}(10 天內 · 未併 · 沒確認是否還開著)")
        both = sorted(mine_files & names)
        if both:
            out.append((lamp, "R2", f"{who} 也新增了同檔名 {both[:3]} → 改發兩邊最大號之上"))
        dup = sorted(k for k in set(mine) & set(theirs) if not (mine[k] & theirs[k]))   # 同號 · 不同實體
        if dup:
            out.append((lamp, "R2", f"{who} 也發了 {dup[:4]}(指向不同的東西)→ 重新取號"))
    if not compared and not out:
        out.append(("GRAY", "R2", "沒有可比的 PR 頭(開著的清單空 · 或都已併)"))
    return out


def _install():
    BASE.d_openpr = d_openpr
    V1.d_openpr = d_openpr
    BASE.TAG = TAG
    for c in BASE.CAUSES:
        c["cmd"] = c["cmd"].replace(PRIOR_PATH.name, HERE.name)


_install()


def run_check(*a, **kw) -> dict:
    r = PRIOR.run_check(*a, **kw)
    r["tool"] = TAG
    return r


def selftest() -> int:
    import contextlib
    import io
    import os
    import shutil
    import subprocess
    import tempfile
    import time
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)[:300]) if note and not cond else ''}", flush=True)

    buf = io.StringIO()
    BASE.d_openpr, V1.d_openpr, BASE.TAG = _SLOW_OPENPR, _SLOW_OPENPR, _V0103_TAG
    for c in BASE.CAUSES:
        c["cmd"] = c["cmd"].replace(HERE.name, PRIOR_PATH.name)
    try:
        with contextlib.redirect_stdout(buf):
            rc0 = PRIOR.selftest()                        # v0103 自測照 v0103 的判法跑(它再照前版鏈跑)
    finally:
        _install()
    print(f"=== {TAG} · 薄尾自測(R2 批次取 PR 頭 · 結果與前版相同;暫存倉 · 零網路)===", flush=True)
    chk("⓪ 前版 %s 自測照過(含整條前版鏈)" % PRIOR_PATH.name, rc0 == 0, buf.getvalue()[-300:])
    td = Path(tempfile.mkdtemp(prefix="via_rework104_"))
    env = dict(os.environ, GIT_AUTHOR_NAME="fx", GIT_AUTHOR_EMAIL="fx@fx", GIT_COMMITTER_NAME="fx", GIT_COMMITTER_EMAIL="fx@fx")

    def g(*a):
        return subprocess.run(["git", "-C", str(td), *a], capture_output=True, text=True, env=env, check=True).stdout.strip()
    try:
        g("init", "-q", "-b", "main")
        (td / "a.txt").write_text("a\n", encoding="utf-8")
        g("add", "-A")
        g("commit", "-q", "-m", "base")
        g("update-ref", "refs/remotes/origin/main", "HEAD")
        base_sha = g("rev-parse", "HEAD")
        g("update-ref", "refs/remotes/pr/1", base_sha)                      # 已併(= base 祖先)
        g("checkout", "-q", "-b", "pr2")
        (td / "Tool_v0100.py").write_text("X = 1\n", encoding="utf-8")
        g("add", "-A")
        g("commit", "-q", "-m", "pr2")
        g("update-ref", "refs/remotes/pr/2", "HEAD")                         # 開著 · 新增同檔名
        g("checkout", "-q", "-b", "pr3", base_sha)
        (td / "Other_v0100.py").write_text("Y = 1\n", encoding="utf-8")
        g("add", "-A")
        g("commit", "-q", "-m", "pr3")
        g("update-ref", "refs/remotes/pr/3", "HEAD")                         # 開著 · 不撞
        g("checkout", "-q", "-b", "mine", base_sha)
        (td / "Tool_v0100.py").write_text("Z = 2\n", encoding="utf-8")
        g("add", "-A")
        g("commit", "-q", "-m", "mine")
        ch = {"A": ["Tool_v0100.py"], "U": [], "M": [], "D": []}
        res = {}
        for label, fn in (("slow", _SLOW_OPENPR), ("fast", d_openpr)):
            for prs in ({"1", "2", "3"}, None):
                t0 = time.time()
                res[(label, str(prs))] = (sorted(fn(str(td), "origin/main", ch, False, prs)), time.time() - t0)
    finally:
        shutil.rmtree(td, ignore_errors=True)
    same = all(res[("slow", k)][0] == res[("fast", k)][0] for k in ("{'1', '2', '3'}", "None") if ("slow", k) in res)
    fast_out = res.get(("fast", str({"1", "2", "3"})), ([], 0))[0]
    chk("① 結果與前版逐字相同(開著清單給定 / 沒給 兩種)", same and len(res) == 4,
        {k: v[0] for k, v in res.items()})
    chk("② 已併的 PR(base 祖先)略過;開著且新增同檔名 → 紅 R2;不撞的 PR 不報",
        any(lamp == "RED" and "#2" in msg and "Tool_v0100.py" in msg for lamp, _c, msg in fast_out)
        and not any("#1" in msg or "#3" in msg for _l, _c, msg in fast_out), fast_out)
    chk("③ run_check 走本版 d_openpr(v0100 / v0101 模組全域已換上)", BASE.d_openpr is d_openpr and V1.d_openpr is d_openpr and BASE.TAG == TAG)
    pub = [n for n in vars(PRIOR) if not n.startswith("_") and callable(getattr(PRIOR, n)) and getattr(getattr(PRIOR, n), "__module__", "") == PRIOR.__name__]
    chk("④ 尾版保有前版公開名稱(TAILAPI)", all(getattr(sys.modules[__name__], n, None) is not None for n in pub), f"{len(pub)} 支")
    print(f"  [計] {TAG} 本版 {sum(ok)}/{len(ok)} · {'PASS' if all(ok) else 'FAIL'}", flush=True)
    return 0 if all(ok) else 1


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    BASE.run_check = run_check
    return BASE.main(a)


if __name__ == "__main__":
    sys.exit(main())
