#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VIA_GitHistorySSOT v0100 — GitHub 紀錄 SSOT 化 + 與 VCGC 冊一致性對照(只讀倉 · 只寫報告)。

操作員令(2026-11-13):「讀取一切 GITHUB 紀錄將這些 SSOT 化 與 VCGC 進行一回一致性對照 完成及功能補充 一切自 VCGC 取過來 完善化」。
動詞:
  build  [--out 夾]   git log(本倉 VIA 樹)→ 每系統(VCGC · VDF · VRN · VQG · VAP · 其他)× 每家族 × 每版本:新增日 · 提交 · 刪除日;
                      每系統提交數 · 首末日 · PR 號(合併訊息 #NNN)→ GIT_SSOT_<UTC>.json + GIT_SSOT_latest.json
  check  [--out 夾]   一致性對照(凍結 / 收件 / 參考 / 副本 / 發布包路徑不算,VCGC 本就不登):每系統尾版(倉內現存最大版號)× VCGC 元件冊(VIA_Component_Inventory_SSOT)× 編號冊(VIA_NumberBooks)
                      → 未註冊 · 未編號 · 冊上 ACTIVE 但檔已不在(過期)· 系統能力缺口(L132 對等矩陣尾版)→ CONSISTENCY_<UTC>.json/.md
  --selftest          臨時 git 倉 + 假冊驗 build / check 判定
不改任何冊與程式;不連網;不用 TA-Lib;編號仍由 VCGC 核發(L125),本工具只點名。
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
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====
import collections
import datetime as _dt
import glob
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

VERSION = "v0100"
HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent.parent
OUT_DEFAULT = VIA / "VIA_Reports" / "githistory"
FROZEN = re.compile(r"(/intake/|/references/|SCOPE_COPY|/_quarantine|QUARANTINE|/BACKUP/|_release_v\d|/vcgc_panorama_v|/_superseded/|/20260804/|_sha[0-9a-f]{6,}|/input/|/_output/)")
VR = re.compile(r"^(?P<stem>.+)_v(?P<v>\d{4})\.(?P<ext>py|json|ps1|jsonl|md)$")


def system_of(rel: str) -> str:
    if rel.startswith("functional modules/VDF/"):
        return "VDF"
    if rel.startswith("functional modules/VRN"):
        return "VRN"
    if rel.startswith("functional modules/VQG/"):
        return "VQG"
    if rel.startswith("functional modules/VAP/"):
        return "VAP"
    if rel.startswith(("supportive modules/", "docs/handoff/")):
        return "VCGC"
    return "OTHER"


def now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def git_log(repo: Path, sub: str) -> list:
    """[(hash, date, subject, [(status, relpath_under_sub)])]"""
    fmt = "@@%h\x1f%ad\x1f%s"
    out = subprocess.run(["git", "-C", str(repo), "log", "--date=short", f"--format={fmt}", "--name-status", "--no-renames", "--", sub or "."],
                         capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
    rows, cur = [], None
    pre = (sub.rstrip("/") + "/") if sub else ""
    for ln in out.splitlines():
        if ln.startswith("@@"):
            h, d, s = (ln[2:].split("\x1f") + ["", ""])[:3]
            cur = (h, d, s, [])
            rows.append(cur)
        elif ln.strip() and cur is not None and "\t" in ln:
            st, path = ln.split("\t", 1)
            path = path.strip('"')
            if pre and path.startswith(pre):
                path = path[len(pre):]
            cur[3].append((st[:1], path))
    return rows


def build(repo: Path, sub: str) -> dict:
    log = git_log(repo, sub)
    sysinfo = collections.defaultdict(lambda: {"commits": set(), "first": None, "last": None, "prs": set()})
    fam = collections.defaultdict(lambda: collections.defaultdict(dict))
    for h, d, s, files in reversed(log):                 # 由舊到新
        prs = set(re.findall(r"#(\d{2,5})\b", s))
        for st, p in files:
            S = system_of(p)
            si = sysinfo[S]
            si["commits"].add(h)
            si["first"] = si["first"] or d
            si["last"] = d
            si["prs"] |= prs
            m = VR.match(Path(p).name)
            if not m:
                continue
            key = str(Path(p).parent / m.group("stem")) + "." + m.group("ext")
            v = fam[S][key].setdefault(m.group("v"), {"added": None, "commit": None, "deleted": None})
            if st == "A" and not v["added"]:
                v["added"], v["commit"] = d, h
            elif st == "D":
                v["deleted"] = d
            elif st == "A" and v["deleted"]:
                v["deleted"] = None                       # 刪後又加回(還原)
    out = {"schema": "via.git.ssot/1", "version": VERSION, "at": now(), "commits_total": len(log),
           "span": [log[-1][1], log[0][1]] if log else None, "systems": {}}
    for S, si in sorted(sysinfo.items()):
        fams = fam.get(S, {})
        out["systems"][S] = {
            "commits": len(si["commits"]), "first": si["first"], "last": si["last"], "prs": sorted(si["prs"], key=int),
            "families": len(fams),
            "versions": sum(len(v) for v in fams.values()),
            "deleted_versions": sum(1 for v in fams.values() for x in v.values() if x["deleted"]),
            "family_index": {k: {"versions": sorted(v), "tail": max(v), "added": {n: x["added"] for n, x in sorted(v.items())},
                                 "deleted": sorted(n for n, x in v.items() if x["deleted"])} for k, v in sorted(fams.items())}}
    return out


def _registers(via: Path):
    inv = via / "supportive modules" / "registry" / "VIA_Component_Inventory_SSOT_v0100.json"
    reg = collections.defaultdict(set)
    if inv.is_file():
        for r in json.load(open(inv, encoding="utf-8")).get("records", []):
            if r.get("source"):
                reg[r["source"]].add(r.get("state") or "?")
    num = set()
    for p in glob.glob(str(via / "supportive modules" / "registry" / "VIA_NumberBooks" / "*.jsonl")):
        for ln in open(p, encoding="utf-8", errors="ignore"):
            if '"source"' in ln:
                try:
                    r = json.loads(ln)
                except ValueError:
                    continue
                if r.get("source") and not r.get("gone_since"):
                    num.add(r["source"])
    return reg, num


def check(via: Path, ssot: dict) -> dict:
    reg, num = _registers(via)
    res = {"schema": "via.git.consistency/1", "version": VERSION, "at": now(), "systems": {}}
    for S, info in ssot["systems"].items():
        if S == "OTHER":
            continue
        unreg, unnum, tails = [], [], 0
        for key, f in info["family_index"].items():
            stem, ext = key.rsplit(".", 1)
            p = f"{stem}_v{f['tail']}.{ext}"
            if not (via / p).is_file():                 # 尾版已刪 → 找現存最大版
                live = [v for v in f["versions"] if (via / f"{stem}_v{v}.{ext}").is_file()]
                if not live:
                    continue
                p = f"{stem}_v{max(live)}.{ext}"
            if ext != "py" or FROZEN.search("/" + p):
                continue
            tails += 1
            if p not in reg:
                unreg.append(p)
            if p not in num:
                unnum.append(p)
        stale = sorted(s for s, st in reg.items() if system_of(s) == S and "ACTIVE" in st and s.endswith(".py") and not (via / s).is_file())
        res["systems"][S] = {"py_tails": tails, "unregistered": len(unreg), "unnumbered": len(unnum), "stale_registry": len(stale),
                             "lists": {"unregistered": unreg[:200], "unnumbered": unnum[:200], "stale_registry": stale[:200]}}
    par = sorted(glob.glob(str(via / "docs" / "handoff" / "ai" / "VIA_SystemParity_*.json")))
    if par:
        pj = json.load(open(par[-1], encoding="utf-8"))
        for S in res["systems"]:
            res["systems"][S]["capability_gaps"] = [r["capability"] for r in pj.get("rows", []) if S in r and not r[S]["has"]]
    return res


def write(out: Path, name: str, obj: dict, md: str | None = None) -> Path:
    out.mkdir(parents=True, exist_ok=True)
    p = out / f"{name}_{obj['at']}.json"
    for q in (p, out / f"{name}_latest.json"):
        q.write_text(json.dumps(obj, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    if md:
        (out / f"{name}_latest.md").write_text(md, encoding="utf-8")
    return p


def md_of(ssot: dict, cons: dict) -> str:
    L = [f"# GitHub 紀錄 SSOT × VCGC 一致性對照({cons['at']})", "",
         f"提交 {ssot['commits_total']} · 期間 {ssot['span']}", "",
         "| 系統 | 提交 | 首 | 末 | PR | 家族 | 版本 | 曾刪 | py 尾版 | 未註冊 | 未編號 | 冊上過期 | 能力缺口 |", "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for S, s in ssot["systems"].items():
        c = cons["systems"].get(S, {})
        L.append(f"| {S} | {s['commits']} | {s['first']} | {s['last']} | {len(s['prs'])} | {s['families']} | {s['versions']} | {s['deleted_versions']} | "
                 f"{c.get('py_tails', '—')} | {c.get('unregistered', '—')} | {c.get('unnumbered', '—')} | {c.get('stale_registry', '—')} | "
                 f"{', '.join(c.get('capability_gaps', [])) or '—'} |")
    L += ["", "未註冊 / 未編號 → `registry-sync --apply` · `run CGC_MDL237_NumberingSystem --apply --scope <檔>`(VCGC 核發,L125);"
          "冊上過期 → registry-sync 退役;能力缺口 → L132 由 VCGC 取一份進該系統(L131 自存鎖版)。"]
    return "\n".join(L) + "\n"


def selftest() -> int:
    ok = []

    def chk(n, c, note=""):
        ok.append(bool(c))
        print(f"  [{'OK' if c else 'FAIL'}] {n}{(' · ' + str(note)) if note and not c else ''}")
    with tempfile.TemporaryDirectory() as td:
        r = Path(td)
        sh = lambda *a: subprocess.run(["git", "-C", str(r), *a], capture_output=True, text=True)
        sh("init", "-q")
        sh("config", "user.email", "t@t")
        sh("config", "user.name", "t")
        v = r / "VIA"
        (v / "functional modules" / "VDF").mkdir(parents=True)
        (v / "supportive modules" / "registry" / "VIA_NumberBooks").mkdir(parents=True)
        for n in ("A_ENG001_X_v0100.py", "A_ENG001_X_v0101.py"):
            (v / "functional modules" / "VDF" / n).write_text("x=1\n")
        sh("add", "-A")
        sh("commit", "-qm", "add (#12)")
        (v / "functional modules" / "VDF" / "A_ENG001_X_v0100.py").unlink()
        (v / "functional modules" / "VDF" / "B_ENG002_Y_v0100.py").write_text("y=1\n")
        sh("add", "-A")
        sh("commit", "-qm", "del + new")
        ss = build(r, "VIA")
        vd = ss["systems"].get("VDF", {})
        fi = vd.get("family_index", {})
        chk("① build:VDF 2 提交 · PR #12 · 2 家族 · 3 版本 · 曾刪 1", vd.get("commits") == 2 and vd.get("prs") == ["12"] and vd.get("families") == 2
            and vd.get("versions") == 3 and vd.get("deleted_versions") == 1, vd and {k: vd[k] for k in ("commits", "prs", "families", "versions", "deleted_versions")})
        chk("② 家族索引:A 尾版 0101 · 刪除 0100", fi.get("functional modules/VDF/A_ENG001_X.py", {}).get("deleted") == ["0100"])
        inv = {"records": [{"source": "functional modules/VDF/A_ENG001_X_v0101.py", "state": "ACTIVE"},
                           {"source": "functional modules/VDF/A_ENG001_X_v0100.py", "state": "ACTIVE"}]}
        (v / "supportive modules" / "registry" / "VIA_Component_Inventory_SSOT_v0100.json").write_text(json.dumps(inv))
        (v / "supportive modules" / "registry" / "VIA_NumberBooks" / "VIA_NumberBook_ENG_v0100.jsonl").write_text(
            json.dumps({"source": "functional modules/VDF/A_ENG001_X_v0101.py"}) + "\n")
        c = check(v, ss)["systems"]["VDF"]
        chk("③ check:B 未註冊 · B 未編號 · A v0100 冊上 ACTIVE 但已刪 = 過期", c["lists"]["unregistered"] == ["functional modules/VDF/B_ENG002_Y_v0100.py"]
            and c["lists"]["unnumbered"] == ["functional modules/VDF/B_ENG002_Y_v0100.py"]
            and c["lists"]["stale_registry"] == ["functional modules/VDF/A_ENG001_X_v0100.py"], c["lists"])
    src = Path(__file__).read_text(encoding="utf-8")
    chk("④ 只讀:不寫冊 · 不連網 · 零 TA-Lib", "import " + "talib" not in src and ("url" + "open") not in src and ("requests" + ".") not in src)
    print(f"[selftest] VIA_GitHistorySSOT {VERSION} {sum(ok)}/{len(ok)}")
    return 0 if all(ok) else 1


def main() -> int:
    a = sys.argv[1:]
    if not a or a[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    if a[0] == "--selftest":
        return selftest()
    out = Path(a[a.index("--out") + 1]) if "--out" in a else OUT_DEFAULT
    repo = VIA.parent
    ssot = build(repo, VIA.name)
    if a[0] == "build":
        p = write(out, "GIT_SSOT", ssot)
        print(f"[GitSSOT] 提交 {ssot['commits_total']} · 期間 {ssot['span']} · " + " · ".join(
            f"{S} {s['commits']} 提交 / {s['families']} 家族 / {s['versions']} 版" for S, s in ssot["systems"].items()) + f" → {p}")
        return 0
    if a[0] == "check":
        cons = check(VIA, ssot)
        write(out, "GIT_SSOT", ssot)
        p = write(out, "CONSISTENCY", cons, md_of(ssot, cons))
        print(md_of(ssot, cons))
        bad = sum(s["unregistered"] + s["unnumbered"] for s in cons["systems"].values())
        print(f"[一致性] 未註冊 + 未編號 合計 {bad} · 報告 {p}")
        return 0 if bad == 0 else 2
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
