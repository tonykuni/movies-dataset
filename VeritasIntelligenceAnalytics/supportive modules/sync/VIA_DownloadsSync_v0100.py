#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VIA_DownloadsSync v0100 — 自適應 Downloads 同步器(規則每次由倉本身推出 · 不寫死名冊 · U/I 由清單生成)

操作員令(2026-11-11):「自建管理平台 U/I 需要容易更新 · synchronizer 自適應式 · C:\\Users\\tonyk\\Downloads · 之前好像做過 請查」。
查到的前作:
  · Collect-VIA-Intake-v0100 / v0101.ps1(批245 / 247):寫死 10 個檔名樣式(2026-09 的件)→ 新檔型抓不到;收完自動 commit 並推 main
    (現行規則只推作業分支、提交由閘鏈負責)。
  · VIA_HTML_UI/ui/VIA-SYNCHRONIZER-Standalone.html:狀態存瀏覽器 localStorage、要手動維護 → 不易更新。
本工具取兩者之長、補兩者之短(兩支前作原件一字不動):
  plan  [--src D] [--out D]   只讀掃描 → 清單 JSON + 自含 HTML 頁(重跑即更新;頁面嵌清單,不靠 localStorage)
  apply [--src D] [--out D]   只把「該收」的件複製進 supportive modules/references/intake/VIA_Downloads_<日期>/(只增 · 不覆寫);
                              原件零觸碰;不做 git(提交 / 編號走 VCGC 閘鏈)
  --selftest
判定(每次由倉推出,不寫死):
  IN_REPO      內容(git blob)已在倉 → 不收
  CONFLICT     同檔名已在倉、內容不同、檔名帶版號 → 不收,要人判(版號律:已發布版號檔不就地改)
  CHANGED      同檔名已在倉、內容不同、檔名無版號 → 收(另存,不覆寫倉內檔)
  NEW_VERSION  族已在倉、版號比倉內最大還大 → 收
  OLD_VERSION  族已在倉、版號較小且倉內沒有 → 收(補環候選,標明)
  NEW_FAMILY   像 VIA 的檔名(系統前綴)但倉內無此族 → 收
  ZIP          zip:逐成員比對(不解壓);有倉外成員才收整包
  DUP          同一份內容在來源夾出現多次((1)(2) 副本)→ 只收第一份
  IGNORE       與 VIA 無關的個人檔 → 只計數,不列檔名(隱私)
大檔(預設 > 50 MB)只記錄不複製。不碰 TA-Lib;不讀寫同意閘;零網路。
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

VERSION = "v0100"
TAG = "VIA_DownloadsSync " + VERSION
HERE = Path(__file__).resolve().parent
VIA = HERE.parents[1]                                      # VeritasIntelligenceAnalytics/
INTAKE_ROOT = VIA / "supportive modules" / "references" / "intake"
VIA_PREFIX = re.compile(r"(?i)^(VIA[_-]|VRN|VDF|VQG|VAP|VCGC|CGC_|Veritas|Activate|Invoke-VIA|Collect-VIA|SUP_|ENG\d|MDL\d)")
VER_RX = re.compile(r"^(?P<fam>.+?)_v(?P<ver>\d{4})(?P<ext>\.[A-Za-z0-9]+)$")
BIG = 50 * 1024 * 1024
TAKE = ("CHANGED", "NEW_VERSION", "OLD_VERSION", "NEW_FAMILY", "ZIP")


def utc_min() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M +00:00")


def blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def repo_index(via: Path | None = None) -> dict:
    """倉的現況(git ls-files -s):blob 集 · 檔名 → 路徑 · 族 → 最大版號。"""
    via = via or VIA
    out = subprocess.run(["git", "ls-files", "-s", "-z"], cwd=str(via), capture_output=True, timeout=300)
    blobs, names, fams = {}, {}, {}
    for rec in out.stdout.decode("utf-8", "replace").split("\0"):
        if not rec or "\t" not in rec:
            continue
        meta, path = rec.split("\t", 1)
        parts = meta.split()
        if len(parts) < 2:
            continue
        blobs.setdefault(parts[1], path)
        name = Path(path).name
        names.setdefault(name, []).append(path)
        m = VER_RX.match(name)
        if m:
            k = (m.group("fam"), m.group("ext").lower())
            fams[k] = max(fams.get(k, 0), int(m.group("ver")))
    return {"blobs": blobs, "names": names, "fams": fams}


def classify(name: str, data: bytes, idx: dict) -> dict:
    b = blob_sha(data)
    if b in idx["blobs"]:
        return {"state": "IN_REPO", "repo_path": idx["blobs"][b]}
    m = VER_RX.match(name)
    if name in idx["names"]:
        return {"state": "CONFLICT" if m else "CHANGED", "repo_path": idx["names"][name][0]}
    if m:
        k = (m.group("fam"), m.group("ext").lower())
        if k in idx["fams"]:
            top = idx["fams"][k]
            ver = int(m.group("ver"))
            return {"state": "NEW_VERSION" if ver > top else "OLD_VERSION", "repo_max": f"v{top:04d}"}
    if VIA_PREFIX.match(name) or (m and VIA_PREFIX.match(m.group("fam"))):
        return {"state": "NEW_FAMILY"}
    return {"state": "IGNORE"}


def zip_scan(path: Path, idx: dict) -> dict:
    """zip 逐成員比對(只讀 · 不解壓到磁碟)。"""
    c = {"members": 0, "in_repo": 0, "outside": 0, "via_like": 0}
    try:
        with zipfile.ZipFile(path) as z:
            for info in z.infolist():
                if info.is_dir() or info.file_size > BIG:
                    continue
                c["members"] += 1
                name = Path(info.filename).name
                data = z.read(info)
                st = classify(name, data, idx)["state"]
                if st == "IN_REPO":
                    c["in_repo"] += 1
                else:
                    c["outside"] += 1
                    c["via_like"] += st != "IGNORE"
    except (zipfile.BadZipFile, OSError) as e:
        c["error"] = type(e).__name__
    return c


def scan(src: Path, idx: dict, depth: int = 2) -> dict:
    rows, ignored, seen = [], 0, {}
    base_depth = len(src.resolve().parts)
    copy_rx = re.compile(r" \(\d+\)(?=\.[^.]+$)|\(\d+\)$")       # 「名 (1).ext」副本排在乾淨檔名之後:正本優先
    for p in sorted(src.rglob("*"), key=lambda q: (bool(copy_rx.search(q.name)), str(q))):
        if not p.is_file() or any(part.startswith(".") for part in p.relative_to(src).parts):
            continue
        if len(p.resolve().parts) - base_depth > depth:
            continue
        size = p.stat().st_size
        if size > BIG:
            st = classify(p.name, b"", idx)
            if st["state"] == "IGNORE":
                ignored += 1
                continue
            rows.append({"name": p.name, "rel": str(p.relative_to(src)), "bytes": size, "state": "BIG",
                         "why": "大檔只記錄不複製", "mtime": datetime.fromtimestamp(p.stat().st_mtime, timezone.utc).strftime("%Y-%m-%d %H:%M")})
            continue
        data = p.read_bytes()
        sha = hashlib.sha256(data).hexdigest()
        st = classify(p.name, data, idx)
        if p.suffix.lower() == ".zip" and st["state"] not in ("IN_REPO",):
            z = zip_scan(p, idx)
            if z.get("via_like") or VIA_PREFIX.match(p.name):
                st = {"state": "ZIP" if z.get("outside") else "IN_REPO", "zip": z}
        if st["state"] == "IGNORE":
            ignored += 1
            continue
        if sha in seen and st["state"] in TAKE:
            st = {"state": "DUP", "dup_of": seen[sha]}
        seen.setdefault(sha, p.name)
        rows.append({"name": p.name, "rel": str(p.relative_to(src)), "bytes": size, "sha256": sha,
                     "mtime": datetime.fromtimestamp(p.stat().st_mtime, timezone.utc).strftime("%Y-%m-%d %H:%M"), **st})
    counts = {}
    for r in rows:
        counts[r["state"]] = counts.get(r["state"], 0) + 1
    counts["IGNORE"] = ignored
    lamp = "YELLOW" if counts.get("CONFLICT") else "GREEN"
    return {"schema": "via.downloads.sync/1", "engine": TAG, "at": utc_min(), "src": str(src), "counts": counts, "lamp": lamp,
            "take": sum(1 for r in rows if r["state"] in TAKE), "rows": rows}


def apply(man: dict, src: Path, intake_root: Path | None = None, max_bytes: int = 1024 * 1024) -> dict:
    """只增複製:該收的件 → intake/VIA_Downloads_<日期>/;同名不同內容另開 _r 檔名,永不覆寫;原件不動。
    超過 max_bytes(預設 1 MB · 七日上傳整理同一取捨)只記錄不複製(跑測輸出包多半很大,倉不跟著膨脹)。"""
    dest = (intake_root or INTAKE_ROOT) / ("VIA_Downloads_" + man["at"][:10].replace("-", ""))
    copied, kept, record_only = [], 0, []
    for r in man["rows"]:
        if r["state"] not in TAKE:
            continue
        if r["bytes"] > max_bytes:
            record_only.append({"name": r["name"], "bytes": r["bytes"], "state": r["state"], "sha256": r["sha256"]})
            continue
        dest.mkdir(parents=True, exist_ok=True)
        target = dest / r["name"]
        if target.exists():
            if hashlib.sha256(target.read_bytes()).hexdigest() == r["sha256"]:
                kept += 1
                continue
            target = dest / f"{Path(r['name']).stem}_r{r['sha256'][:8]}{Path(r['name']).suffix}"
            if target.exists():
                kept += 1
                continue
        shutil.copy2(src / r["rel"], target)
        copied.append({"name": r["name"], "to": target.name, "state": r["state"], "sha256": r["sha256"]})
    if copied:
        mf = dest / "MANIFEST_downloads_sync.jsonl"
        with mf.open("a", encoding="utf-8", newline="\n") as fh:
            for c in copied:
                fh.write(json.dumps({"at": man["at"], "engine": TAG, **c}, ensure_ascii=False) + "\n")
    if record_only:
        dest.mkdir(parents=True, exist_ok=True)
        with (dest / "RECORD_ONLY_downloads_sync.jsonl").open("a", encoding="utf-8", newline="\n") as fh:
            for c in record_only:
                fh.write(json.dumps({"at": man["at"], "engine": TAG, "max_bytes": max_bytes, **c}, ensure_ascii=False) + "\n")
    return {"dest": str(dest), "copied": len(copied), "already": kept, "record_only": len(record_only)}


STATE_LABEL = {"IN_REPO": "已在倉", "CONFLICT": "同名異內容 · 要人判", "CHANGED": "同名改過(無版號)", "NEW_VERSION": "新版號",
               "OLD_VERSION": "舊版號 · 補環候選", "NEW_FAMILY": "新族", "ZIP": "zip 有倉外成員", "DUP": "重複副本",
               "BIG": "大檔只記錄"}
STATE_TONE = {"IN_REPO": "ok", "CONFLICT": "bad", "CHANGED": "warn", "NEW_VERSION": "take", "OLD_VERSION": "warn",
              "NEW_FAMILY": "take", "ZIP": "take", "DUP": "mute", "BIG": "mute"}


def _zip_note(z: dict) -> str:
    return (f"成員 {z.get('members', 0)} · 已在倉 {z.get('in_repo', 0)} · 倉外 {z.get('outside', 0)}(像 VIA 的 {z.get('via_like', 0)})"
            + (f" · 讀取錯 {z['error']}" if z.get("error") else ""))


def render_html(man: dict) -> str:
    """自含頁:清單嵌在頁內(重跑 plan 就更新,不靠 localStorage);篩選只是顯示,不改資料。"""
    chips = "".join(f'<button class="chip {STATE_TONE.get(k, "mute")}" data-s="{k}">{html.escape(STATE_LABEL.get(k, k))} '
                    f'<b>{v}</b></button>' for k, v in man["counts"].items() if k != "IGNORE")
    trs = "".join(
        f'<tr data-s="{r["state"]}"><td><span class="tag {STATE_TONE.get(r["state"], "mute")}">{html.escape(STATE_LABEL.get(r["state"], r["state"]))}</span></td>'
        f'<td class="mono">{html.escape(r["rel"])}</td><td class="num">{r["bytes"]:,}</td><td class="mono">{r["mtime"]}</td>'
        f'<td class="mono">{html.escape(r.get("repo_path") or r.get("repo_max") or r.get("dup_of") or (_zip_note(r["zip"]) if r.get("zip") else r.get("why", "")))}</td></tr>'
        for r in man["rows"])
    return f"""<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>VIA Downloads 同步器</title><style>
:root{{--bg:#eef2f7;--panel:#fff;--ink:#1f2a37;--mute:#6b7685;--line:#d9e0ea;--gold:#b8892b;--ok:#2e7d4f;--warn:#a36b00;--bad:#b3261e;--take:#1f5fa8}}
@media (prefers-color-scheme:dark){{:root{{--bg:#12161c;--panel:#1b2129;--ink:#e6ebf1;--mute:#97a3b3;--line:#2c3540}}}}
body{{margin:0;background:var(--bg);color:var(--ink);font:14px/1.5 system-ui,"Noto Sans TC",sans-serif;padding:16px max(16px,env(safe-area-inset-left))}}
h1{{font-size:18px;margin:0 0 4px;border-left:4px solid var(--gold);padding-left:8px}} .sub{{color:var(--mute);font-size:12px;margin-bottom:12px}}
.panel{{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:12px;margin-bottom:12px}}
.chips{{display:flex;flex-wrap:wrap;gap:6px}} .chip{{border:1px solid var(--line);background:var(--panel);color:var(--ink);border-radius:999px;padding:4px 10px;cursor:pointer;font:inherit}}
.chip.on{{outline:2px solid var(--gold)}} .tag{{font-size:12px;padding:1px 6px;border-radius:4px;white-space:nowrap}}
.ok{{color:var(--ok)}} .warn{{color:var(--warn)}} .bad{{color:var(--bad)}} .take{{color:var(--take)}} .mute{{color:var(--mute)}}
.wrap{{overflow-x:auto}} table{{border-collapse:collapse;width:100%;min-width:720px}} th,td{{border-bottom:1px solid var(--line);padding:6px 8px;text-align:left;vertical-align:top}}
th{{font-size:12px;color:var(--mute);font-weight:600}} .mono{{font-family:ui-monospace,Consolas,monospace;font-size:12px;word-break:break-all}} .num{{text-align:right;font-variant-numeric:tabular-nums}}
</style></head><body>
<h1>VIA Downloads 同步器</h1>
<div class="sub">{html.escape(TAG)} · 掃描 {html.escape(man['at'])} · 來源 {html.escape(man['src'])} · 燈 {man['lamp']} · 該收 {man['take']} · 與 VIA 無關 {man['counts'].get('IGNORE', 0)} 件(只計數不列名)</div>
<div class="panel chips">{chips}<button class="chip" data-s="">全部</button></div>
<div class="panel wrap"><table><thead><tr><th>狀態</th><th>檔案</th><th>位元組</th><th>修改時間(UTC)</th><th>倉內對照 / 說明</th></tr></thead><tbody>{trs}</tbody></table></div>
<div class="sub">更新方法:重跑 <span class="mono">python VIA_DownloadsSync_v0100.py plan</span> 即重生本頁;收件:<span class="mono">apply</span>(只增 · 不覆寫 · 原件不動)。</div>
<script id="manifest" type="application/json">{html.escape(json.dumps(man, ensure_ascii=False))}</script>
<script>document.querySelectorAll('.chip').forEach(function(b){{b.addEventListener('click',function(){{var s=b.dataset.s;
document.querySelectorAll('.chip').forEach(function(x){{x.classList.toggle('on',x===b&&s!=='')}});
document.querySelectorAll('tbody tr').forEach(function(tr){{tr.hidden=!!s&&tr.dataset.s!==s}});}})}});</script>
</body></html>"""


def default_src() -> Path:
    return Path(os.environ.get("VIA_DOWNLOADS") or (Path.home() / "Downloads"))


def write_outputs(man: dict, out: Path) -> tuple[Path, Path]:
    out.mkdir(parents=True, exist_ok=True)
    j = out / "VIA_DownloadsSync_latest.json"
    h = out / "VIA_DownloadsSync_latest.html"
    j.write_text(json.dumps(man, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    h.write_text(render_html(man), encoding="utf-8")
    return j, h


def selftest() -> int:
    import tempfile
    checks = []

    def ck(name, cond, note=""):
        checks.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}" + (f" · {note}" if note else ""))

    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        repo = td / "repo"
        repo.mkdir()
        run = lambda *a: subprocess.run(["git", *a], cwd=str(repo), capture_output=True)
        run("init", "-q")
        (repo / "VDF_ENG001_Demo_v0101.py").write_bytes(b"print(1)\n")
        (repo / "VRN_Notes.md").write_bytes(b"# notes\n")
        run("add", "-A")
        run("-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "x")
        idx = repo_index(repo)
        ck("倉索引:blob · 檔名 · 族最大版號", len(idx["blobs"]) == 2 and idx["fams"].get(("VDF_ENG001_Demo", ".py")) == 101)
        src = td / "Downloads"
        src.mkdir()
        (src / "VDF_ENG001_Demo_v0101.py").write_bytes(b"print(1)\n")                 # 已在倉
        (src / "VDF_ENG001_Demo_v0102.py").write_bytes(b"print(2)\n")                 # 新版號
        (src / "VDF_ENG001_Demo_v0100.py").write_bytes(b"print(0)\n")                 # 舊版號
        (src / "VRN_Notes.md").write_bytes(b"# notes changed\n")                      # 同名改過(無版號)
        (src / "VQG_NewTool_v0100.py").write_bytes(b"print('q')\n")                   # 新族
        (src / "VQG_NewTool_v0100 (1).py").write_bytes(b"print('q')\n")               # 重複副本(名不同 · 內容同)
        (src / "holiday_photo.jpg").write_bytes(b"\xff\xd8personal")                  # 個人檔
        with zipfile.ZipFile(src / "VIA_Bundle_v0100.zip", "w") as z:
            z.writestr("a/VDF_ENG001_Demo_v0101.py", b"print(1)\n")
            z.writestr("a/VAP_New_v0100.py", b"x=1\n")
        conflict = td / "c"
        conflict.mkdir()
        man = scan(src, idx)
        st = {r["name"]: r["state"] for r in man["rows"]}
        ck("已在倉 → IN_REPO", st.get("VDF_ENG001_Demo_v0101.py") == "IN_REPO")
        ck("新版號 → NEW_VERSION · 舊版號 → OLD_VERSION", st.get("VDF_ENG001_Demo_v0102.py") == "NEW_VERSION"
           and st.get("VDF_ENG001_Demo_v0100.py") == "OLD_VERSION")
        ck("同名無版號改過 → CHANGED", st.get("VRN_Notes.md") == "CHANGED")
        ck("新族 → NEW_FAMILY · 同內容副本 → DUP", st.get("VQG_NewTool_v0100.py") == "NEW_FAMILY"
           and "DUP" in (st.get("VQG_NewTool_v0100 (1).py"), st.get("VQG_NewTool_v0100.py")))
        ck("zip 逐成員比對:有倉外成員 → ZIP", st.get("VIA_Bundle_v0100.zip") == "ZIP", [r.get("zip") for r in man["rows"] if r["name"].endswith(".zip")])
        ck("個人檔不列名 · 只計數(隱私)", "holiday_photo.jpg" not in st and man["counts"].get("IGNORE") == 1)
        (src / "VDF_ENG001_Demo_v0101.py").write_bytes(b"print('edited')\n")
        man2 = scan(src, idx)
        ck("同名帶版號但內容不同 → CONFLICT(要人判)· 燈 YELLOW", {r["name"]: r["state"] for r in man2["rows"]}["VDF_ENG001_Demo_v0101.py"] == "CONFLICT"
           and man2["lamp"] == "YELLOW")
        before = {p.name: p.read_bytes() for p in src.iterdir()}
        res = apply(man, src, td / "intake")
        dest = Path(res["dest"])
        got = sorted(p.name for p in dest.iterdir())
        ck("apply 只收該收的(新版 · 舊版 · 改過 · 新族 · zip;不收已在倉 / 衝突 / 副本)",
           res["copied"] == 5 and "VDF_ENG001_Demo_v0101.py" not in got and "MANIFEST_downloads_sync.jsonl" in got, got)
        ck("原件零觸碰", before == {p.name: p.read_bytes() for p in src.iterdir()})
        res2 = apply(man, src, td / "intake")
        ck("重跑 apply:同內容不再複製(只增 · 不重複)", res2["copied"] == 0 and res2["already"] == 5, res2)
        (src / "VQG_NewTool_v0100.py").write_bytes(b"print('q2')\n")
        res3 = apply(scan(src, idx), src, td / "intake")
        ck("同名不同內容 → 另存 _r<sha8>,不覆寫已收件", res3["copied"] >= 1 and any("_r" in p.name for p in dest.iterdir()))
        page = render_html(man)
        big = src / "VDF_Big_v0100.py"
        big.write_bytes(b"#" * 2048)
        rb = apply(scan(src, idx), src, td / "intake", max_bytes=1024)
        ck("超過上限只記錄不複製(RECORD_ONLY 帳)", rb["record_only"] >= 1 and not (dest / "VDF_Big_v0100.py").exists()
           and (dest / "RECORD_ONLY_downloads_sync.jsonl").is_file(), rb)
        ck("U/I 由清單生成:嵌清單 · 有篩選 · 不用 localStorage · 不列個人檔", 'id="manifest"' in page and "data-s=" in page
           and "localStorage" not in page and "holiday_photo" not in page)
        j, h = write_outputs(man, td / "out")
        ck("plan 寫清單 JSON + HTML(重跑即更新)", j.is_file() and h.is_file() and json.loads(j.read_text(encoding="utf-8"))["take"] == man["take"])
    src_txt = Path(__file__).read_text(encoding="utf-8")
    ck("不碰 TA-Lib · 不寫同意閘 · 不做 git 寫入(只 ls-files)", not re.search(r"^\s*(import|from)\s+talib", src_txt, re.M)
       and not re.search(r"environ\[[\"']VIA_(NET|SCRAPE)_CONSENT", src_txt)
       and not re.search(r"\"git\", \"(add|commit|push)\"", src_txt))
    print(f"[計] {TAG} 自測 {sum(checks)}/{len(checks)} " + ("PASS" if all(checks) else "FAIL"))
    return 0 if all(checks) else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog=TAG, description="自適應 Downloads 同步器(只讀掃描 · 只增收件 · U/I 由清單生成)")
    ap.add_argument("verb", nargs="?", choices=("plan", "apply"), default="plan")
    ap.add_argument("--src")
    ap.add_argument("--out")
    ap.add_argument("--max-mb", type=float, default=1.0, help="apply 複製上限(MB;超過只記錄)")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    src = Path(a.src) if a.src else default_src()
    if not src.is_dir():
        print(f"[{TAG}] RED · 來源夾不在:{src}(用 --src 指定,或設 VIA_DOWNLOADS)")
        return 2
    man = scan(src, repo_index())
    out = Path(a.out) if a.out else VIA / "VIA_Reports" / "sync"
    j, h = write_outputs(man, out)
    c = man["counts"]
    print(f"[{TAG}] {man['lamp']} · " + " · ".join(f"{STATE_LABEL.get(k, k) if k != 'IGNORE' else '無關'} {v}" for k, v in c.items())
          + f" · 該收 {man['take']}")
    print(f"  清單 {j}\n  頁面 {h}")
    for r in man["rows"]:
        if r["state"] == "CONFLICT":
            print(f"  [要人判] {r['rel']} 與倉內 {r['repo_path']} 同名不同內容(版號律:另出新版號,不覆寫)")
    if a.verb == "apply":
        res = apply(man, src, max_bytes=int(a.max_mb * 1024 * 1024))
        print(f"[{TAG}] 收件 · 複製 {res['copied']} · 已收過 {res['already']} · 大於 {a.max_mb} MB 只記錄 {res['record_only']} · 到 {res['dest']}(只增 · 原件不動 · 提交 / 編號走 VCGC 閘鏈)")
    return 0 if man["lamp"] == "GREEN" else 1


if __name__ == "__main__":
    sys.exit(main())
