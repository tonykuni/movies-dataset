#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PR 守門(版號尾版 · 成功鎖)— 合併前就攔下過去一週最常見的兩種重工。

  ① 版號插到尾版底下:PR 新增 <家族>_vNNNN 的程式檔(.py / .ps1 / .psm1),而 base 上同家族已經有更大的版號。
     薄尾版用 glob 取「比自己小的最大版」當前版 → 舊號一插進來,上面那版的前版鏈就悄悄換掉(例:#690 的 VDF_SystemManager_v0187
     插在 main v0191 底下、v0188 的前版會從 v0186 變成 v0187)。程式檔 = 紅(擋);冊 / 文件(.json · .jsonl · .md …)= 黃(只提醒,
     冊的前版寫在 prior 欄,不靠 glob)。修法:改發 base 尾版之上的新版號。
  ② 已鎖成功被改或刪:docs/handoff/daily/VIA_SuccessLock_Ledger_v0100.jsonl(只增帳)每個路徑最新那一列的 sha256(LF 正規化)
     就是鎖定位元;PR 修改後位元不同、或刪掉 = 紅。規則「修改開新版」:要改就出新版號。

用法:python3 .github/scripts/pr_guard.py --base origin/main --head HEAD [--summary 檔]   · 自測:--selftest
唯讀:只讀 git 物件,不改檔、不出網、不執行被檢查的程式。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

VIA = "VeritasIntelligenceAnalytics/"
LEDGER = VIA + "docs/handoff/daily/VIA_SuccessLock_Ledger_v0100.jsonl"
CODE_EXT = {".py", ".ps1", ".psm1"}
VER = re.compile(r"^(?P<fam>.+)_v(?P<n>\d{4})(?P<ext>\.[A-Za-z0-9]+)$")


def git(repo, *a, binary=False):
    r = subprocess.run(["git", "-C", str(repo), *a], capture_output=True)
    if r.returncode != 0:
        raise RuntimeError(f"git {' '.join(a)}: {r.stderr.decode('utf-8', 'replace').strip()[:200]}")
    return r.stdout if binary else r.stdout.decode("utf-8", "surrogateescape")


def changes(repo, base, head) -> dict:
    out = {"A": [], "M": [], "D": []}
    raw = git(repo, "diff", "--name-status", "-z", "--no-renames", f"{base}...{head}")
    parts = raw.split("\0")
    for st, path in zip(parts[0::2], parts[1::2]):
        if st[:1] in out:
            out[st[:1]].append(path)
    return out


def family_tails(repo, ref) -> dict:
    tails = {}
    for p in git(repo, "ls-tree", "-r", "-z", "--name-only", ref).split("\0"):
        m = VER.match(p)
        if m:
            k = (m["fam"], m["ext"].lower())
            tails[k] = max(tails.get(k, 0), int(m["n"]))
    return tails


def lf_sha(data: bytes) -> str:
    return hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest()


def locked(repo, ref) -> dict:
    """每個路徑最新那一列(只增帳 → 後列蓋前列)。"""
    try:
        text = git(repo, "show", f"{ref}:{LEDGER}")
    except RuntimeError:
        return {}
    rows = {}
    for ln in text.splitlines():
        try:
            r = json.loads(ln)
        except ValueError:
            continue
        if r.get("path") and r.get("sha256_lf"):
            rows[r["path"]] = r
    return rows


def check(repo, base, head) -> dict:
    ch = changes(repo, base, head)
    tails = family_tails(repo, base)
    red, yellow = [], []
    for p in ch["A"]:
        m = VER.match(p)
        if not m:
            continue
        top = tails.get((m["fam"], m["ext"].lower()), 0)
        if top > int(m["n"]):
            msg = f"`{p}` 是 v{m['n']},base 上同家族已到 v{top:04d}(插到尾版底下)"
            (red if m["ext"].lower() in CODE_EXT else yellow).append("① " + msg)
    locks = locked(repo, base)
    for kind in ("M", "D"):
        for p in ch[kind]:
            if not p.startswith(VIA):
                continue
            row = locks.get(p[len(VIA):])
            if not row:
                continue
            if kind == "D":
                red.append(f"② `{p}` 已鎖成功(鎖於 {row.get('locked_at')}),PR 把它刪了")
                continue
            now = lf_sha(git(repo, "show", f"{head}:{p}", binary=True))
            if now != row["sha256_lf"]:
                red.append(f"② `{p}` 已鎖成功(鎖於 {row.get('locked_at')} · sha {row['sha256_lf'][:12]}),PR 改了位元(現在 {now[:12]})→ 請出新版號")
    return {"red": red, "yellow": yellow, "added": len(ch["A"]), "modified": len(ch["M"]), "deleted": len(ch["D"]), "locks": len(locks)}


def render(r: dict) -> str:
    lamp = "紅" if r["red"] else ("黃" if r["yellow"] else "綠")
    lines = [f"### PR 守門 · {lamp}", "",
             f"新增 {r['added']} · 修改 {r['modified']} · 刪除 {r['deleted']} · 成功鎖 {r['locks']} 個路徑", ""]
    for x in r["red"]:
        lines.append(f"- 🔴 {x}")
    for x in r["yellow"]:
        lines.append(f"- 🟡 {x}")
    if not (r["red"] or r["yellow"]):
        lines.append("- 沒有插到尾版底下的程式版號 · 沒有改到已鎖成功的檔")
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="origin/main")
    ap.add_argument("--head", default="HEAD")
    ap.add_argument("--repo", default=".")
    ap.add_argument("--summary", default=os.environ.get("GITHUB_STEP_SUMMARY"))
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    r = check(a.repo, a.base, a.head)
    text = render(r)
    print(text)
    if a.summary:
        with open(a.summary, "a", encoding="utf-8") as fh:
            fh.write(text)
    return 1 if r["red"] else 0


def selftest() -> int:
    import tempfile
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note and not cond else ''}")

    def sh(d, *a):
        subprocess.run(["git", "-C", str(d), *a], check=True, capture_output=True)

    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        sh(d, "init", "-q", "-b", "main")
        sh(d, "config", "user.email", "t@t")
        sh(d, "config", "user.name", "t")
        fm = d / VIA / "functional modules" / "VDF"
        fm.mkdir(parents=True)
        for v in ("0186", "0188", "0191"):
            (fm / f"VDF_SystemManager_v{v}.py").write_text(f"V = '{v}'\n")
        reg = d / VIA / "supportive modules" / "registry"
        reg.mkdir(parents=True)
        (reg / "VIA_Requirements_SSOT_v0297.json").write_text("{}\n")
        (fm / "VDF_Locked_v0100.py").write_text("x = 1\r\n")
        led = d / LEDGER
        led.parent.mkdir(parents=True)
        led.write_text(json.dumps({"path": "functional modules/VDF/VDF_Locked_v0100.py", "sha256_lf": lf_sha(b"x = 1\r\n"),
                                   "locked_at": "2026-11-21T00:00:00Z"}) + "\n")
        sh(d, "add", "-A")
        sh(d, "commit", "-qm", "base")
        sh(d, "checkout", "-qb", "pr")
        (fm / "VDF_SystemManager_v0187.py").write_text("V = '0187'\n")      # 程式插到尾版底下
        (fm / "VDF_SystemManager_v0192.py").write_text("V = '0192'\n")      # 正常新版
        (reg / "VIA_Requirements_SSOT_v0293.json").write_text("{}\n")      # 冊插到尾版底下
        (fm / "VDF_New_v0100.py").write_text("n = 1\n")                     # 新家族
        sh(d, "add", "-A")
        sh(d, "commit", "-qm", "pr")
        r = check(d, "main", "pr")
        chk("① #690 情境:程式 v0187 插到 v0191 底下 → 紅", any("VDF_SystemManager_v0187.py" in x for x in r["red"]), r)
        chk("② 正常新版 v0192 · 新家族 → 不報", not any("v0192" in x or "VDF_New" in x for x in r["red"] + r["yellow"]))
        chk("③ 冊 v0293 插到 v0297 底下 → 黃(只提醒)", any("Requirements_SSOT_v0293" in x for x in r["yellow"])
            and not any("Requirements" in x for x in r["red"]))
        chk("④ 沒動到鎖檔 → 沒有 ② 紅", not any(x.startswith("②") for x in r["red"]))
        (fm / "VDF_Locked_v0100.py").write_text("x = 1\n")                 # 只把 CRLF 換成 LF:位元正規化後相同
        sh(d, "commit", "-qam", "lf")
        chk("⑤ 鎖檔只換行尾(LF 正規化後同)→ 不算改", not any(x.startswith("②") for x in check(d, "main", "pr")["red"]))
        (fm / "VDF_Locked_v0100.py").write_text("x = 2\n")
        sh(d, "commit", "-qam", "edit")
        chk("⑥ LL-21-04 情境:改了已鎖成功的檔 → 紅", any("VDF_Locked_v0100.py" in x and x.startswith("②") for x in check(d, "main", "pr")["red"]))
        sh(d, "rm", "-q", str(fm / "VDF_Locked_v0100.py"))
        sh(d, "commit", "-qm", "del")
        chk("⑦ 刪掉已鎖成功的檔 → 紅", any("刪了" in x for x in check(d, "main", "pr")["red"]))
        chk("⑧ 回碼:有紅 = 1", main(["--repo", str(d), "--base", "main", "--head", "pr", "--summary", str(d / "s.md")]) == 1
            and "PR 守門 · 紅" in (d / "s.md").read_text(encoding="utf-8"))
    print(f"  [計] pr_guard 自測 {sum(ok)}/{len(ok)} · {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
