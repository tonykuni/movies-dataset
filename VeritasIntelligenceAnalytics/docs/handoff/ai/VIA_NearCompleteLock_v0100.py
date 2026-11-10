#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VIA_NearCompleteLock v0100 — 歷次「近完工」狀態的紀錄與鎖定(操作員 2026-11-10)。

操作員令:「CLAUDE / MANUS / GITHUB 應該都有 VCGC / VRN / VDF 這三個獨立系統很多次幾乎完工的狀態 · 用那些工具列管 · 透過 VCGC 全景式
分析找出來 · 現在進度維持 · 檢視其他為何沒完成 · 以目前狀態將先前的跟先前快完成的版本狀態都建立紀錄鎖定 · 都是臨門一腳 AI 搞不了 抓出來檢查」
「不可使用 TALIB · 各自獨立 · VRN VDF 完善化即使 VCGC 改動大對他們影響有限」。

做的事(只讀 · 不改任何系統的檔 · 只寫本工具的鎖檔):
  build  讀近完工清單(milestones.json:每系統一串里程碑,含 repo · commit · 入口名)→ 每個里程碑鎖住:
           commit 存在 · commit 時間 · 整倉快照 tree 雜湊(commit^{tree})· 入口檔在該 commit 的 blob 雜湊與路徑;
         另鎖「目前狀態」:每系統入口尾版的檔案 SHA-256 與 HEAD。→ VIA_NearCompleteLock_v0100.json / .md
  check  重驗鎖檔:每個里程碑的 commit 仍在、tree 與入口 blob 雜湊一字不差(git 歷史被改寫 = RED);
         目前狀態與鎖時比較(入口換版 = 只報漂移,不算錯:進度本來就會往前)。
獨立性:只用 Python 標準庫 + git;不 import VCGC / VDF / VRN-2 任何模組,不執行被鎖的程式;VRN-1 倉只讀(L123)。
   VCGC 之後怎麼改,本工具與鎖檔都不受影響;VDF / VRN-2 的鎖只依它們自己的入口與 git 歷史。不用 TA-Lib。
用法:python VIA_NearCompleteLock_v0100.py build --milestones <json> [--out <夾>] · check [--lock <json>] · --selftest
"""
from __future__ import annotations

import argparse
import datetime
import glob
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

VERSION = "v0100"
TAG = "VIA_NearCompleteLock " + VERSION
HERE = Path(__file__).resolve().parent
LOCK_NAME = "VIA_NearCompleteLock_v0100.json"
# 目前狀態:各系統入口(glob 取最高版號);VRN-1 是外部倉,只記 HEAD
ENTRIES = {
    "VCGC": "supportive modules/registry/CGC_MDL149_VeritasCentralGovernanceConsole_v*.py",
    "VDF": "functional modules/VDF/VDF_SystemManager_v*.py",
    "VRN-2": "functional modules/VRN/VRN_SystemManager_v*.py",
}
_VER = re.compile(r"_v(\d{4})\.py$")


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def git(repo: Path, *args, check=True) -> str:
    cp = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, encoding="utf-8", errors="replace")
    if check and cp.returncode != 0:
        raise RuntimeError("git %s: %s" % (" ".join(args), (cp.stderr or "").strip()[:200]))
    return (cp.stdout or "").strip()


def git_ok(repo: Path, *args) -> bool:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True).returncode == 0


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def tail(root: Path, pattern: str):
    hits = [Path(x) for x in glob.glob(str(root / pattern))]
    hits = [h for h in hits if _VER.search(h.name)]
    return max(hits, key=lambda h: int(_VER.search(h.name).group(1))) if hits else None


def find_entry_path(repo: Path, commit: str, entry: str | None) -> str | None:
    """入口名(例 VRN_SystemManager_v0256 或含路徑)→ 該 commit 樹裡的路徑;找不到回 None。"""
    if not entry:
        return None
    name = entry.replace("\\", "/").split("/")[-1]
    if not name.endswith(".py"):
        name += ".py"
    files = git(repo, "ls-tree", "-r", "--name-only", commit).splitlines()
    hits = [f for f in files if f.split("/")[-1] == name]
    return sorted(hits, key=len)[0] if hits else None


def lock_milestone(m: dict, repos: dict) -> dict:
    repo = repos.get(m.get("repo") or ("VRN-1" if m.get("system") == "VRN-1" else "VIA"))
    out = {k: m.get(k) for k in ("system", "date", "commit", "pr", "title", "entry", "lamp", "verified", "left", "source")}
    out["repo"] = m.get("repo") or ("VRN-1" if m.get("system") == "VRN-1" else "VIA")
    if repo is None or not m.get("commit"):
        out.update(locked=False, why="沒有 repo 或 commit")
        return out
    c = m["commit"]
    if not git_ok(repo, "cat-file", "-e", c + "^{commit}"):
        out.update(locked=False, why="commit 不在本機 git 歷史")
        return out
    out["commit"] = git(repo, "rev-parse", c + "^{commit}")
    out["commit_time"] = git(repo, "show", "-s", "--format=%cI", out["commit"])
    out["tree"] = git(repo, "rev-parse", out["commit"] + "^{tree}")
    path = find_entry_path(repo, out["commit"], m.get("entry"))
    if path:
        out["entry_path"] = path
        out["entry_blob"] = git(repo, "rev-parse", "%s:%s" % (out["commit"], path))
    out["locked"] = True
    return out


def current_state(via_root: Path, vrn1: Path | None) -> dict:
    st = {}
    repo = via_root.parent if (via_root.parent / ".git").exists() else via_root
    head = git(repo, "rev-parse", "HEAD") if git_ok(repo, "rev-parse", "HEAD") else None
    for sysname, pat in ENTRIES.items():
        t = tail(via_root, pat)
        st[sysname] = {"entry": str(t.relative_to(via_root)).replace("\\", "/") if t else None,
                       "entry_version": ("v" + _VER.search(t.name).group(1)) if t else None,
                       "entry_sha256": sha256_file(t) if t else None, "repo_head": head}
    if vrn1 and (vrn1 / ".git").exists():
        st["VRN-1"] = {"entry": None, "repo_head": git(vrn1, "rev-parse", "HEAD"), "note": "外部倉只讀 · 只記 HEAD(L123)"}
    return st


def build(milestones_path: Path, via_root: Path, vrn1: Path | None, out_dir: Path, extra: dict | None = None) -> dict:
    src = json.loads(Path(milestones_path).read_text(encoding="utf-8"))
    repo = via_root.parent if (via_root.parent / ".git").exists() else via_root
    repos = {"VIA": repo, "VRN-1": vrn1}
    locked = {}
    for sysname, block in (src.get("systems") or {}).items():
        ms = block.get("milestones") or []
        locked[sysname] = [lock_milestone(dict(m, system=m.get("system") or sysname), repos) for m in ms]
    lock = {"tool": TAG, "built_at": _now(), "source": str(milestones_path), "independent": "stdlib + git only · 不 import 任何系統模組 · 不用 TA-Lib",
            "milestones": locked, "current": current_state(via_root, vrn1), "extra": extra or {}}
    lock["counts"] = {s: {"total": len(v), "locked": sum(1 for x in v if x.get("locked"))} for s, v in locked.items()}
    lock["fingerprint"] = hashlib.sha256(json.dumps(lock["milestones"], ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / LOCK_NAME).write_text(json.dumps(lock, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    (out_dir / LOCK_NAME.replace(".json", ".md")).write_text(render_md(lock), encoding="utf-8")
    return lock


def check(lock_path: Path, via_root: Path, vrn1: Path | None) -> dict:
    lock = json.loads(Path(lock_path).read_text(encoding="utf-8"))
    repo = via_root.parent if (via_root.parent / ".git").exists() else via_root
    repos = {"VIA": repo, "VRN-1": vrn1}
    bad, ok, skipped = [], 0, 0
    for sysname, ms in lock.get("milestones", {}).items():
        for m in ms:
            if not m.get("locked"):
                skipped += 1
                continue
            r = repos.get(m.get("repo"))
            c = m["commit"]
            if r is None or not git_ok(r, "cat-file", "-e", c + "^{commit}"):
                bad.append("%s %s commit 不見了" % (sysname, c[:12]))
                continue
            if git(r, "rev-parse", c + "^{tree}") != m["tree"]:
                bad.append("%s %s tree 雜湊變了" % (sysname, c[:12]))
                continue
            if m.get("entry_path") and git(r, "rev-parse", "%s:%s" % (c, m["entry_path"])) != m.get("entry_blob"):
                bad.append("%s %s 入口 blob 變了" % (sysname, c[:12]))
                continue
            ok += 1
    fp = hashlib.sha256(json.dumps(lock["milestones"], ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
    if fp != lock.get("fingerprint"):
        bad.append("鎖檔內容被改過(指紋不符)")
    now = current_state(via_root, vrn1)
    drift = []
    for s, v in (lock.get("current") or {}).items():
        n = now.get(s) or {}
        if v.get("entry_sha256") and n.get("entry_sha256") != v.get("entry_sha256"):
            drift.append("%s 入口 %s → %s" % (s, v.get("entry_version"), n.get("entry_version")))
        if s == "VRN-1" and n.get("repo_head") != v.get("repo_head"):
            drift.append("VRN-1 HEAD %s → %s" % ((v.get("repo_head") or "")[:12], (n.get("repo_head") or "")[:12]))
    lamp = "RED" if bad else ("YELLOW" if drift else "GREEN")
    return {"lamp": lamp, "verified": ok, "bad": bad, "skipped": skipped, "drift": drift, "at": _now()}


def render_md(lock: dict) -> str:
    L = ["# 近完工狀態鎖定紀錄 · %s · %s" % (TAG, lock["built_at"]), "",
         "鎖的是 git 歷史裡的整倉快照(tree 雜湊)與當時入口檔(blob 雜湊);`check` 會逐一重驗。只讀 · 不執行 · 不 import 任何系統模組。", ""]
    L.append("| 系統 | 里程碑 | 已鎖 |")
    L.append("|---|---|---|")
    for s, c in lock["counts"].items():
        L.append("| %s | %d | %d |" % (s, c["total"], c["locked"]))
    L += ["", "## 目前狀態(鎖時)", "", "| 系統 | 入口 | 版 | SHA-256 前 16 | HEAD |", "|---|---|---|---|---|"]
    for s, v in lock["current"].items():
        L.append("| %s | %s | %s | %s | %s |" % (s, v.get("entry") or "—", v.get("entry_version") or "—", (v.get("entry_sha256") or "—")[:16], (v.get("repo_head") or "—")[:12]))
    for s, ms in lock["milestones"].items():
        L += ["", "## %s" % s, "", "| 日期 | commit | PR | 入口 | 燈 | 當時差什麼 | 鎖 |", "|---|---|---|---|---|---|---|"]
        for m in ms:
            left = str(m.get("left") or "").replace("|", "/").replace("\n", " ")[:160]
            L.append("| %s | `%s` | %s | %s | %s | %s | %s |" % (str(m.get("date") or "")[:10], (m.get("commit") or "")[:12], m.get("pr") or "—",
                                                            (m.get("entry_path") or m.get("entry") or "—").split("/")[-1], m.get("lamp") or "—", left,
                                                            "✔" if m.get("locked") else "✘ " + str(m.get("why") or "")))
    return "\n".join(L) + "\n"


def selftest() -> int:
    ok = total = 0

    def chk(name, cond, note=""):
        nonlocal ok, total
        total += 1
        ok += bool(cond)
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)) if note else ""), flush=True)
    print("[%s selftest]" % TAG, flush=True)
    with tempfile.TemporaryDirectory() as td:
        t = Path(td)
        repo = t / "movies-dataset"
        via = repo / "VeritasIntelligenceAnalytics"
        (via / "functional modules/VDF").mkdir(parents=True)
        (via / "functional modules/VRN").mkdir(parents=True)
        (via / "supportive modules/registry").mkdir(parents=True)
        env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}

        def g(*a):
            subprocess.run(["git", "-C", str(repo), *a], check=True, capture_output=True, env=env)
        g("init", "-q")
        (via / "functional modules/VDF/VDF_SystemManager_v0100.py").write_text("print('v0100')\n", encoding="utf-8")
        (via / "functional modules/VRN/VRN_SystemManager_v0200.py").write_text("print('v0200')\n", encoding="utf-8")
        (via / "supportive modules/registry/CGC_MDL149_VeritasCentralGovernanceConsole_v0100.py").write_text("x=1\n", encoding="utf-8")
        g("add", "-A")
        g("commit", "-q", "-m", "near-complete 1")
        c1 = git(repo, "rev-parse", "HEAD")
        (via / "functional modules/VDF/VDF_SystemManager_v0101.py").write_text("print('v0101')\n", encoding="utf-8")
        g("add", "-A")
        g("commit", "-q", "-m", "near-complete 2")
        c2 = git(repo, "rev-parse", "HEAD")
        ms = {"systems": {"VDF": {"milestones": [{"commit": c1, "entry": "VDF_SystemManager_v0100", "lamp": "YELLOW", "left": "同意閘"},
                                                 {"commit": c2, "entry": "VDF_SystemManager_v0101", "lamp": "GREEN", "left": ""},
                                                 {"commit": "0" * 40, "entry": "x", "left": "不存在的 commit"}]},
                          "VRN-2": {"milestones": [{"commit": c1[:12], "entry": "VRN_SystemManager_v0200", "lamp": "GREEN"}]}}}
        mp = t / "ms.json"
        mp.write_text(json.dumps(ms), encoding="utf-8")
        out = t / "out"
        lock = build(mp, via, None, out)
        vdf = lock["milestones"]["VDF"]
        chk("① build:真 commit 鎖住(tree + 入口 blob + 路徑)· 不存在的 commit 照實標未鎖", vdf[0]["locked"] and vdf[0]["tree"] and vdf[0]["entry_path"].endswith("VDF_SystemManager_v0100.py")
            and vdf[1]["locked"] and not vdf[2]["locked"] and "不在" in vdf[2]["why"])
        chk("② 短 commit 展開成 40 碼 · 目前狀態取入口尾版(VDF v0101)", len(lock["milestones"]["VRN-2"][0]["commit"]) == 40 and lock["current"]["VDF"]["entry_version"] == "v0101")
        chk("③ 鎖檔 json + md 都寫出 · 計數正確", (out / LOCK_NAME).is_file() and (out / LOCK_NAME.replace(".json", ".md")).is_file() and lock["counts"]["VDF"] == {"total": 3, "locked": 2})
        r = check(out / LOCK_NAME, via, None)
        chk("④ check:沒變 = GREEN · 重驗 3 個里程碑", r["lamp"] == "GREEN" and r["verified"] == 3 and not r["bad"], r)
        (via / "functional modules/VDF/VDF_SystemManager_v0102.py").write_text("print('v0102')\n", encoding="utf-8")
        r2 = check(out / LOCK_NAME, via, None)
        chk("⑤ 入口往前換版 = YELLOW 漂移(不是錯)", r2["lamp"] == "YELLOW" and any("VDF" in d for d in r2["drift"]) and not r2["bad"], r2["drift"])
        g("commit", "-q", "--amend", "-m", "rewritten")
        g("reflog", "expire", "--expire=now", "--all")
        g("gc", "-q", "--prune=now")
        r3 = check(out / LOCK_NAME, via, None)
        chk("⑥ git 歷史被改寫(鎖住的 commit 消失)= RED", r3["lamp"] == "RED" and any(c2[:12] in b for b in r3["bad"]), r3["bad"])
        lk = json.loads((out / LOCK_NAME).read_text(encoding="utf-8"))
        lk["milestones"]["VDF"][0]["lamp"] = "GREEN"
        (out / LOCK_NAME).write_text(json.dumps(lk, ensure_ascii=False), encoding="utf-8")
        r4 = check(out / LOCK_NAME, via, None)
        chk("⑦ 鎖檔被手改 = 指紋不符 RED", any("指紋" in b for b in r4["bad"]))
    src = Path(__file__).read_text(encoding="utf-8")
    imports = re.findall(r"^\s*(?:import|from)\s+([\w.]+)", src, re.M)
    chk("⑧ 獨立:只用標準庫(不 import VCGC / VDF / VRN 任何模組 · 不用 TA-Lib)",
        not any(x.lower().startswith(("cgc", "vdf", "vrn", "via_", "talib")) for x in imports), sorted(set(imports)))
    print("[%s] %s selftest · %d/%d" % ("PASS" if ok == total else "FAIL", TAG, ok, total), flush=True)
    return 0 if ok == total else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=TAG)
    ap.add_argument("verb", nargs="?", default="check", choices=["build", "check", "selftest"])
    ap.add_argument("--milestones")
    ap.add_argument("--lock", default=str(HERE / LOCK_NAME))
    ap.add_argument("--out", default=str(HERE))
    ap.add_argument("--via", default=str(HERE.parents[2]))
    ap.add_argument("--vrn1", default=None, help="VRN-1 倉(只讀;沒給就不鎖 VRN-1 里程碑)")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest or a.verb == "selftest":
        return selftest()
    vrn1 = Path(a.vrn1) if a.vrn1 else None
    if a.verb == "build":
        if not a.milestones:
            print("[RED] build 要 --milestones <json>")
            return 2
        lock = build(Path(a.milestones), Path(a.via), vrn1, Path(a.out))
        print("[GREEN] %s build · %s · 指紋 %s → %s" % (TAG, " · ".join("%s %d/%d" % (s, c["locked"], c["total"]) for s, c in lock["counts"].items()),
                                                   lock["fingerprint"][:16], Path(a.out) / LOCK_NAME))
        return 0
    r = check(Path(a.lock), Path(a.via), vrn1)
    print("[%s] %s check · 重驗 %d · 壞 %d · 未鎖 %d · 漂移 %d%s" % (r["lamp"], TAG, r["verified"], len(r["bad"]), r["skipped"], len(r["drift"]),
                                                          ("\n  " + "\n  ".join(r["bad"] + r["drift"])) if (r["bad"] or r["drift"]) else ""))
    return 0 if r["lamp"] != "RED" else 2


if __name__ == "__main__":
    sys.exit(main())
