#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
SUP_MDL754_VIAIntakeBaseline v0100 — 收容夾基線冊(批595)

批594 的 `via-govaudit intake` 閘量出:58 個收容夾裡有 **25 夾是 NODATA**
——不是綠,是**沒有可比的 sha**。本支把那 25 夾補上基線冊,讓閘真的守得住。

## 一句話要先講清楚:**基線不是「沒被動過」的證明**

這支寫進去的 sha 是**現在**的 sha。在此之前那些檔案有沒有被誰動過,
**這份基線答不出來**。它能保證的只有一件事:**從這一刻起再被動,閘會抓到。**

把基線講成「驗證通過」就是假綠。所以冊裡有一個 `baseline_note` 欄位寫著這句話,
而且 `via-govaudit intake` 對基線冊蓋出來的綠燈,語意是「**自基線以來沒變**」,
不是「跟上傳當下一致」。

## 為什麼另立一支,不做進 MDL164

`CGC_MDL164` 是**唯讀稽核**——它的檢① 就是「零網路 · 零寫入倉 · 沒有 `--apply`」。
把寫檔塞進去會把那一檢變成謊話。**尺不寫字,寫字的另外一支。**

## 零觸碰怎麼保證

只新增 `_INTAKE_BASELINE_b<批>.json`(**檔名跟既有的 `_INTAKE_MANIFEST.json` 不同**,
不會覆蓋任何人的冊),而且 `apply` 前後各算一次全夾 sha 快照逐檔比對;
**有任何既有檔案變了就是本支的錯,當場報紅並停手**。

律:零網路;零安裝;預設只列不寫(`--apply` 才寫);`--selftest` 只在 tempfile 沙盒寫。
用法:python3 SUP_MDL754_VIAIntakeBaseline_v0100.py [plan|apply] [--selftest]
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

import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent
VERSION = Path(__file__).stem.rsplit("_v", 1)[-1]
BATCH = 595
BASELINE_NAME = f"_INTAKE_BASELINE_b{BATCH}.json"
SKIP_PARTS = ("__pycache__", "/.git/", ".DS_Store")

BASELINE_NOTE = (
    "**這是現況基線,不是「沒被動過」的證明。**這份冊裡的 sha 是批595 當下算的;"
    "在此之前這些檔案有沒有被誰動過,本冊答不出來。它能保證的只有一件事:"
    "**從這一刻起再被動,`via-govaudit intake` 會抓到。**"
    "把基線講成「驗證通過」就是假綠。"
)


def _sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def _files(d: Path) -> list:
    out = []
    for p in sorted(d.rglob("*")):
        s = str(p).replace("\\", "/")
        if not p.is_file() or any(k in s for k in SKIP_PARTS):
            continue
        if p.name.startswith("_INTAKE_BASELINE_b"):
            continue                      # 基線冊自己不入冊(否則寫完就對不上自己)
        out.append(p)
    return out


def _has_sha(d: Path) -> bool:
    """這一夾已經有**逐檔 sha** 可比了嗎?有就不用補基線。"""
    for g in ("_INTAKE_MANIFEST*.json", "*manifest*.json", "*MANIFEST*.json", BASELINE_NAME):
        for mf in sorted(d.glob(g)):
            try:
                j = json.loads(mf.read_text(encoding="utf-8"))
            except Exception:
                continue
            # 本支自己寫的基線冊:**認 schema 不認內容**。
            # 空夾的 `files` 是 `{}`,用 `any()` 判會變成「還是沒有 sha」——
            # 那等於說「這夾沒查過」,而它明明查過了,查出來就是 0 檔。
            # **空不等於沒查過**,自測⑩ 當場抓到。
            if j.get("schema") == "VIA.Intake.Baseline.v1" and isinstance(j.get("files"), dict):
                return True
            f = j.get("files")
            if isinstance(f, dict) and any(
                    isinstance(v, str) and len(v) >= 32 or
                    (isinstance(v, dict) and isinstance(v.get("sha256"), str)) for v in f.values()):
                return True
            if isinstance(f, list) and any(
                    isinstance(it, dict) and isinstance(it.get("sha256"), str) for it in f):
                return True
            s1 = j.get("sha256")
            if isinstance(s1, str) and len(s1) >= 32 and (
                    j.get("source_path") or j.get("source") or j.get("file") or j.get("name")):
                return True
    return False


def scan() -> list:
    """所有收容夾,標出哪些還沒有逐檔 sha。"""
    rows = []
    for d in sorted(VIA.rglob("references/intake/*")):
        if not d.is_dir() or "__pycache__" in str(d):
            continue
        fs = _files(d)
        rows.append({"dir": str(d.relative_to(VIA)).replace("\\", "/"), "path": d,
                     "n": len(fs), "has_sha": _has_sha(d)})
    return rows


def plan() -> dict:
    rows = scan()
    need = [r for r in rows if not r["has_sha"]]
    empty = [r for r in need if r["n"] == 0]
    return {"state": "OK", "dirs": len(rows), "have": len(rows) - len(need),
            "need": len(need), "need_dirs": [r["dir"] for r in need],
            "empty_dirs": [r["dir"] for r in empty],
            "files_to_record": sum(r["n"] for r in need),
            "why": ("空夾也照寫一份(`files` 為空)——**空不等於沒查過**,"
                    "有冊才分得出「這夾本來就空」與「還沒人量過」。")}


def apply_() -> dict:
    """寫基線冊。前後各算一次全夾快照,**既有檔案有任何一個變了就報紅**。"""
    rows = [r for r in scan() if not r["has_sha"]]
    before = {r["dir"]: {str(p.relative_to(r["path"])): _sha256(p) for p in _files(r["path"])}
              for r in rows}
    wrote, ts = [], datetime.now().strftime("%Y-%m-%d %H:%M")
    for r in rows:
        d = r["path"]
        body = {
            "schema": "VIA.Intake.Baseline.v1", "batch": BATCH, "ts": ts,
            "dir": r["dir"], "n_files": r["n"],
            "baseline_note": BASELINE_NOTE,
            "written_by": f"SUP_MDL754_VIAIntakeBaseline v{VERSION}",
            "files": before[r["dir"]],
        }
        (d / BASELINE_NAME).write_text(json.dumps(body, ensure_ascii=False, indent=1),
                                       encoding="utf-8")
        wrote.append(r["dir"])
    after = {r["dir"]: {str(p.relative_to(r["path"])): _sha256(p) for p in _files(r["path"])}
             for r in rows}
    touched = [d for d in before if before[d] != after[d]]
    return {"state": "FAIL" if touched else "OK", "wrote": len(wrote), "dirs": wrote,
            "touched": touched,
            "why": ("零觸碰保證:只新增 `" + BASELINE_NAME + "`(檔名跟既有 `_INTAKE_MANIFEST.json` 不同,"
                    "不覆蓋任何人的冊),寫入前後各算一次全夾 sha 逐檔比對;"
                    "`touched` 非空就是**本支的錯**,不是樹的錯。")}


# ────────────────────────── 自測 ──────────────────────────
def selftest() -> int:
    import ast as _ast
    import tempfile
    n, fails = [0], []

    def chk(label, ok, extra=""):
        n[0] += 1
        print(f"  [{'OK' if ok else 'FAIL'}] {label}" + (f" ({extra})" if extra else ""))
        if not ok:
            fails.append(label)

    tree = _ast.parse(Path(__file__).read_text(encoding="utf-8"))
    mods = set()
    for nd in _ast.walk(tree):
        if isinstance(nd, _ast.Import):
            mods |= {a.name.split(".")[0] for a in nd.names}
        elif isinstance(nd, _ast.ImportFrom) and nd.module:
            mods.add(nd.module.split(".")[0])
    chk("① 零網路零安裝:語法樹裡沒有 requests/httpx/urllib/subprocess 的 import",
        not (mods & {"requests", "httpx", "urllib", "subprocess", "socket", "http"}),
        f"(import:{sorted(mods)})")
    chk("② 冊裡一定帶 `baseline_note`,而且明說**不是「沒被動過」的證明**"
        "(講成驗證通過就是假綠)",
        "不是「沒被動過」的證明" in BASELINE_NOTE and "假綠" in BASELINE_NOTE)
    chk("③ 基線冊檔名跟既有 `_INTAKE_MANIFEST.json` **不同**,不覆蓋任何人的冊",
        BASELINE_NAME.startswith("_INTAKE_BASELINE_b") and "MANIFEST" not in BASELINE_NAME,
        BASELINE_NAME)

    with tempfile.TemporaryDirectory() as td:
        t = Path(td) / "references" / "intake"
        (t / "d1").mkdir(parents=True)
        (t / "d1" / "a.py").write_text("print(1)\n", encoding="utf-8")
        (t / "d1" / "sub").mkdir()
        (t / "d1" / "sub" / "b.txt").write_text("値\n", encoding="utf-8")
        (t / "d2_empty").mkdir()
        (t / "d3_has").mkdir()
        (t / "d3_has" / "x.py").write_text("x=1\n", encoding="utf-8")
        (t / "d3_has" / "_INTAKE_MANIFEST.json").write_text(
            json.dumps({"files": {"x.py": _sha256(t / "d3_has" / "x.py")}}), encoding="utf-8")

        g = globals()
        old = g["VIA"]
        g["VIA"] = Path(td)
        try:
            pl = plan()
            chk("④ 已經有逐檔 sha 的夾**不重複補**(d3_has 有冊就跳過)",
                pl["need"] == 2 and "references/intake/d3_has" not in pl["need_dirs"],
                f"(需補 {pl['need_dirs']})")
            chk("⑤ 空夾也照寫(**空不等於沒查過**——有冊才分得出「本來就空」與「還沒人量過」)",
                "references/intake/d2_empty" in pl["empty_dirs"])

            snap = {str(p): _sha256(p) for p in (t.rglob("*")) if p.is_file()}
            ap = apply_()
            chk("⑥ apply 寫了冊,而且**既有檔案一個都沒變**(前後全夾 sha 逐檔比)",
                ap["state"] == "OK" and ap["wrote"] == 2 and not ap["touched"],
                f"(寫 {ap['wrote']} 夾 · 動到 {ap['touched'] or '無'})")
            after = {str(p): _sha256(p) for p in (t.rglob("*"))
                     if p.is_file() and not p.name.startswith("_INTAKE_BASELINE_b")}
            chk("⑦ 逐檔再驗一次:除了新增的基線冊,沒有任何檔案的 sha 變動",
                all(snap.get(k) == v for k, v in after.items()),
                f"({len(after)} 檔比對")
            b = json.loads((t / "d1" / BASELINE_NAME).read_text(encoding="utf-8"))
            chk("⑧ 冊內容:相對路徑為鍵、含子夾、sha 對得上真檔",
                set(b["files"]) == {"a.py", "sub/b.txt"}
                and b["files"]["a.py"] == _sha256(t / "d1" / "a.py")
                and b["n_files"] == 2 and b["batch"] == BATCH)
            chk("⑨ 基線冊**自己不入冊**(入了就寫完當場對不上自己)",
                not any(k.startswith("_INTAKE_BASELINE_b") for k in b["files"]))
            chk("⑩ 冪等:再跑一次 plan,這兩夾已經有 sha 了,不會再被列為要補",
                plan()["need"] == 0, f"(需補 {plan()['need']})")
        finally:
            g["VIA"] = old

    print(f"  [計] {n[0]} 檢 OK {n[0] - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print(f"=== 收容夾基線冊(SUP_MDL754 v{VERSION})· 十檢自測(零網路;只在沙盒寫)===")
        return selftest()
    verb = a[0] if a and not a[0].startswith("-") else "plan"
    if verb == "apply":
        r = apply_()
        print(f"[SUP_MDL754 v{VERSION}] apply · {r['state']} · 寫 {r['wrote']} 夾")
        print(f"  {r['why']}")
        for d in r["dirs"]:
            print(f"  [寫] {d}/{BASELINE_NAME}")
        if r["touched"]:
            print(f"  [絕] **動到既有檔案**(本支的錯):{r['touched']}")
        return 0 if r["state"] == "OK" else 1
    r = plan()
    print(f"[SUP_MDL754 v{VERSION}] plan · 收容夾 {r['dirs']} · 已有逐檔 sha {r['have']} · "
          f"**要補 {r['need']}** · 要記錄 {r['files_to_record']} 檔")
    print(f"  {r['why']}")
    for d in r["need_dirs"]:
        print(f"  [待補] {d}" + ("  (空夾)" if d in r["empty_dirs"] else ""))
    print("  預設只列不寫;確認後 apply")
    return 0


if __name__ == "__main__":
    sys.exit(main())
