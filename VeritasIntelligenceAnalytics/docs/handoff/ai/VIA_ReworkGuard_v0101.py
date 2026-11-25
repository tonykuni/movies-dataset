#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VIA_ReworkGuard v0101 — 薄尾(v0100 一字不動;v0100 已鎖成功,修改開新版):真分支上三個誤判

  v0100 在本批自己的分支上跑出三個誤判(容器 2026-11-24):
    R2 撞號  新冊版是整本複製前版 → 舊代碼全被當成「這次新發的號」,跟開著的 PR(同樣整本複製)全撞
             → 本版:兩邊都先扣掉 base 上已有的代碼,只比「這次新出現的」。
    R3 工作樹 已提交的收據改動(base...head)被當成「工具重寫了已追蹤檔」→ 本版只看工作樹未提交的改動。
    R6 本機路徑 新冊版複製了前版就有的舊列(含本機路徑)→ 本版扣掉 base 同家族尾版已有的。
  其餘(13 類 · 解法 · report · causes · CI 用法)全照 v0100;經 PRIOR 的模組全域換上本版函式,v0100 的 main / render 照用。
用法同 v0100:python VIA_ReworkGuard_v0101.py check [--fetch-prs] | report | causes | --selftest
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
import json
import re
import subprocess
import sys
from pathlib import Path

VERSION = "v0101"
HERE = Path(__file__).resolve()
FAMILY = "VIA_ReworkGuard"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.parent.glob(FAMILY + "_v*.py") if 0 <= _vnum(p) < _vnum(HERE)), key=_vnum)
_spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem + "_for_v0101", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
P = PRIOR
VIA, VER, NUM_ID, LOCAL_PATH, git, read = P.VIA, P.VER, P.NUM_ID, P.LOCAL_PATH, P.git, P.read
_V0100 = {n: getattr(P, n) for n in ("changed", "d_dirty", "d_openpr", "d_localpath", "run_check", "TAG")}


def __getattr__(name):
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def changed(repo, base, head) -> dict:
    """同 v0100,另多一格 W = 工作樹未提交的已追蹤改動(R3 只看它)。"""
    out = _V0100["changed"](repo, base, head)
    out["W"] = sorted({ln[3:].strip().strip('"') for ln in git(repo, "status", "--porcelain").splitlines()
                       if ln[:2] != "??" and "D" not in ln[:2]})
    return out


def d_dirty(repo, ch) -> list:
    return _V0100["d_dirty"](repo, dict(ch, M=ch["W"]))


ERE = r"VIA-[A-Z]+-?[A-Z]*-?[0-9]+|(VCGC|VDF|VRN|VQG|VAP)-(REQ|WKF)[0-9]+"   # git grep 只吃 POSIX ERE(沒有 (?: 與 \b)→ 粗撈再用 NUM_ID 精篩


def base_ids(repo, base) -> set:
    raw = git(repo, "grep", "-ohE", ERE, base, "--", VIA + "supportive modules/registry", check=False)
    return set(NUM_ID.findall(raw.replace("\n", " ")))


CODE_KEY = re.compile(r'"(?:code|id|declared|req_id|case)"\s*:\s*"([^"]{3,80})"')
IDENT_KEY = re.compile(r'"(?:key|identity|full|declared|source|name)"\s*:\s*"([^"]{2,200})"')


def added_ids(repo, rng) -> dict:
    """diff 新增行裡「代碼欄位」的號(說明文字裡提到不算)→ 號 → 附近 ±6 行的身分值(key · identity · full · source …)。"""
    lines = [ln[1:] for ln in git(repo, "diff", "-U0", rng, check=False).splitlines() if ln.startswith("+") and not ln.startswith("+++")]
    out = {}
    for i, ln in enumerate(lines):
        for c in CODE_KEY.findall(ln):
            if not NUM_ID.fullmatch(c):
                continue
            near = " ".join(lines[max(0, i - 6): i + 7]) if ln.count('"') <= 4 else ln     # jsonl 一列一筆;多行 json 看附近
            out.setdefault(c, set()).update(IDENT_KEY.findall(near))
    return out


def d_openpr(repo, base, ch, fetch: bool, open_prs: set | None = None) -> list:
    """同 v0100 的流程;撞號改成「兩邊都在代碼欄新發 · 扣掉 base 已有 · 指向不同實體」才算(同一個元件兩邊登同號不算)。"""
    open_prs = P.open_pr_list() if open_prs is None else open_prs
    if fetch:
        git(repo, "fetch", "-q", "origin", "+refs/pull/*/head:refs/remotes/pr/*", check=False)
    refs = [r for r in git(repo, "for-each-ref", "--format=%(refname)", "refs/remotes/pr/").split() if r]
    if not refs:
        return [("GRAY", "R2", "沒有開著的 PR 頭可比(加 --fetch-prs 抓;取號 / 出新版號前一定要比)")]
    known = base_ids(repo, base)
    mine_files = {Path(p).name for p in ch["A"] + ch["U"] if VER.match(Path(p).name)}
    mine = {k: v for k, v in added_ids(repo, f"{base}...HEAD").items() if k not in known}
    head = git(repo, "rev-parse", "HEAD").strip()
    cutoff = P.time.time() - 10 * 86400
    out, compared = [], 0
    for r in refs:
        num = r.split("/")[-1]
        if open_prs is not None and num not in open_prs:
            continue
        sha = git(repo, "rev-parse", r).strip()
        if sha == head or any(subprocess.run(["git", "-C", str(repo), "merge-base", "--is-ancestor", sha, x], capture_output=True).returncode == 0
                              for x in (base, "HEAD")):
            continue
        if open_prs is None and int(git(repo, "log", "-1", "--format=%ct", sha).strip() or 0) < cutoff:
            continue
        try:
            names = {Path(p).name for p in git(repo, "diff", "--name-only", "--diff-filter=A", f"{base}...{r}").splitlines()}
        except RuntimeError as exc:
            SKIPPED.append(f"#{num}:{str(exc)[:40]}")
            continue
        compared += 1
        theirs = {k: v for k, v in added_ids(repo, f"{base}...{r}").items() if k not in known} if mine else {}
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


SKIPPED: list = []


def base_tail_text(repo, base, p) -> str:
    m = VER.match(Path(p).name)
    if not m:
        return ""
    folder = str(Path(p).parent).replace("\\", "/") + "/"
    same = [x for x in git(repo, "ls-tree", "--name-only", base, folder, check=False).splitlines()
            if VER.match(Path(x).name) and VER.match(Path(x).name)["fam"] == m["fam"] and VER.match(Path(x).name)["ext"] == m["ext"]]
    if not same:
        return ""
    return git(repo, "show", "%s:%s" % (base, max(same, key=lambda x: int(VER.match(Path(x).name)["n"]))), check=False)


CTX = {"base": "origin/main"}


def d_localpath(repo, files) -> list:
    """同 v0100,但扣掉 base 同家族尾版已有的本機路徑(新冊版複製前版的舊列不算這次新加)。"""
    out = []
    for p in files:
        if not p.endswith((".py", ".ps1", ".psm1", ".json", ".md")) or "/evidence/" in p:
            continue
        old = set(LOCAL_PATH.findall(base_tail_text(repo, CTX["base"], p)))
        if any(x not in old for x in LOCAL_PATH.findall(read(repo, p))):
            out.append(("YELLOW", "R6", f"`{p}` 含本機路徑(新檔不含本機路徑;用 $HOME / 倉根相對)"))
    return out


def run_check(repo, base="origin/main", head="HEAD", fetch=False, open_prs=None) -> dict:
    CTX["base"] = base
    r = _V0100["run_check"](repo, base, head, fetch, open_prs)
    r["tool"] = TAG
    return r


TAG = "VIA_ReworkGuard " + VERSION


def _install():
    P.changed, P.d_dirty, P.d_openpr, P.d_localpath = changed, d_dirty, d_openpr, d_localpath
    P.TAG = TAG
    for c in P.CAUSES:                                                       # 內建指令指向現役尾版(本檔),不寫死 v0100
        c["cmd"] = c["cmd"].replace(PRIOR_PATH.name, HERE.name)


_install()


def selftest() -> int:
    import contextlib
    import io
    import shutil
    import tempfile
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)[:300]) if note and not cond else ''}", flush=True)

    buf = io.StringIO()
    P.changed, P.d_dirty, P.d_openpr, P.d_localpath, P.TAG = (_V0100[k] for k in ("changed", "d_dirty", "d_openpr", "d_localpath", "TAG"))
    try:
        with contextlib.redirect_stdout(buf):
            rc0 = P.selftest()                                               # 前版自測照前版的函式跑(它的情境把號寫在註解裡)
    finally:
        _install()
    print(f"=== {TAG} · 薄尾自測(三個誤判 · 前版原封不動;暫存 git 倉 · 零網路)===", flush=True)
    chk("⓪ 前版 %s 自測照過(16 項)" % PRIOR_PATH.name, rc0 == 0, buf.getvalue()[-300:])
    td = Path(tempfile.mkdtemp(prefix="via_rework101_"))
    try:
        r = td / "repo"
        r.mkdir()

        def sh(*a):
            return git(r, *a)
        sh("init", "-q", "-b", "main")
        sh("config", "user.email", "t@example.invalid")
        sh("config", "user.name", "t")
        sh("config", "commit.gpgsign", "false")
        reg = r / VIA / "supportive modules" / "registry"
        reg.mkdir(parents=True)
        local = "C:" + "\\Users\\someone\\x"
        (reg / "VIA_Req_SSOT_v0001.json").write_text(json.dumps({"r": [{"id": "VCGC-REQ001", "note": local}]}), encoding="utf-8")
        rcp = r / VIA / "docs/handoff/daily"
        rcp.mkdir(parents=True)
        (rcp / "X_latest.md").write_text("a\n", encoding="utf-8")
        sh("add", "-A")
        sh("commit", "-qm", "base")
        sh("update-ref", "refs/remotes/origin/main", "HEAD")
        sh("checkout", "-qb", "pr5")
        (reg / "VIA_Req_SSOT_v0002.json").write_text(json.dumps({"r": [{"id": "VCGC-REQ001", "note": local}, {"id": "VCGC-REQ002"}]}), encoding="utf-8")
        sh("add", "-A")
        sh("commit", "-qm", "pr5")
        sh("update-ref", "refs/remotes/pr/5", "HEAD")
        sh("checkout", "-q", "main")
        sh("checkout", "-qb", "work")
        (reg / "VIA_Req_SSOT_v0003.json").write_text(json.dumps({"r": [{"id": "VCGC-REQ001", "note": local}, {"id": "VCGC-REQ003"}]}), encoding="utf-8")
        (rcp / "X_latest.md").write_text("b\n", encoding="utf-8")
        sh("add", "-A")
        sh("commit", "-qm", "work")
        res = run_check(r, "origin/main", "HEAD", open_prs={"5"})
        txt = json.dumps(res, ensure_ascii=False)
        chk("① 兩邊整本複製的舊代碼 VCGC-REQ001 不算撞號(只比新出現的)", "VCGC-REQ001" not in txt, res["findings"])
        (reg / "VIA_Req_SSOT_v0003.json").write_text(json.dumps({"r": [{"id": "VCGC-REQ001", "note": local}, {"id": "VCGC-REQ002"}]}), encoding="utf-8")
        sh("commit", "-qam", "same new id")
        res2 = run_check(r, "origin/main", "HEAD", open_prs={"5"})
        chk("② 兩邊都新發 VCGC-REQ002 → 照樣紅 R2", any(f["lamp"] == "RED" and "VCGC-REQ002" in f["what"] for f in res2["findings"]), res2["findings"])
        inv = reg / "VIA_Inv_v0100.json"
        sh("checkout", "-q", "pr5")
        inv.write_text(json.dumps({"rows": [{"key": "class|Hub:A", "code": "VIA-CLS-0900", "first_seen": "t1"}]}, indent=1), encoding="utf-8")
        sh("add", "-A")
        sh("commit", "-qm", "pr5 inv")
        sh("update-ref", "refs/remotes/pr/5", "HEAD")
        sh("checkout", "-q", "work")
        inv.write_text(json.dumps({"rows": [{"key": "class|Hub:A", "code": "VIA-CLS-0900", "first_seen": "t2"}]}, indent=1), encoding="utf-8")
        sh("add", "-A")
        sh("commit", "-qm", "work inv")
        res4 = run_check(r, "origin/main", "HEAD", open_prs={"5"})
        chk("②b 兩邊替同一個元件(同 key)登了同號 → 不算撞號", not any("VIA-CLS-0900" in f["what"] for f in res4["findings"]), res4["findings"])
        chk("③ 已提交的收據改動不算「工作樹被工具重寫」(R3 只看未提交)", not any(f["cause"] == "R3" for f in res4["findings"]), res4["findings"])
        chk("④ 新冊版裡前版就有的本機路徑不算新加(R6)", not any(f["cause"] == "R6" for f in res4["findings"]), res4["findings"])
        (rcp / "X_latest.md").write_text("c\n", encoding="utf-8")
        (reg / "VIA_New_v0001.json").write_text(json.dumps({"p": local}), encoding="utf-8")
        res3 = run_check(r, "origin/main", "HEAD", open_prs={"5"})
        chk("⑤ 工作樹未提交的收據重寫 → 黃 R3;全新檔含本機路徑 → 黃 R6", any(f["cause"] == "R3" for f in res3["findings"])
            and any(f["cause"] == "R6" and "VIA_New_v0001" in f["what"] for f in res3["findings"]), res3["findings"])
    finally:
        shutil.rmtree(td, ignore_errors=True)
    chk("⑥ 本版真的換上:前版模組的 changed / d_dirty / d_openpr / d_localpath 是本版 · 工具名本版",
        P.changed is changed and P.d_dirty is d_dirty and P.d_openpr is d_openpr and P.d_localpath is d_localpath and P.TAG == TAG)
    src = HERE.read_text(encoding="utf-8")
    body = src.split("def selftest", 1)[0]
    chk("⑦ 加速器橋 · 不出網 · 不碰 TA-Lib · 不設他系統入口旗標", "import VIA_SuperAccel_Module" in src and "talib" not in body.lower()
        and not re.search(r"^\s*(import|from)\s+(requests|urllib|socket|http)\b", src, re.M)
        and not re.search(r"environ(?:\[[\"']VIA_FROM_\w+[\"']\]\s*=|\.setdefault\([\"']VIA_FROM_)", body))
    pub = [n for n in vars(P) if not n.startswith("_") and callable(getattr(P, n)) and getattr(getattr(P, n), "__module__", "") == P.__name__]
    chk("⑧ 尾版保有前版公開名稱(TAILAPI)", all(getattr(sys.modules[__name__], n, None) is not None for n in pub), f"{len(pub)} 支")
    print(f"  [計] {TAG} 本版 {sum(ok)}/{len(ok)} · {'PASS' if all(ok) else 'FAIL'}", flush=True)
    return 0 if all(ok) else 1


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    P.run_check = run_check
    return P.main(a)


if __name__ == "__main__":
    sys.exit(main())
