#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
via_oldroot_scan_v0100 — 舊根對帳掃描器(TOOL-086)
====================================================================
操作員令(批76,2026-08-20):「C:\\Users\\tonyk\\Downloads\\
VeritasIntelligenceAnalytics 這是舊的檔案夾 檢查有無遺漏 整合這幾個
系統」。本器在工作站側對帳舊 VIA 樹 vs 現役倉,整合去重鐵律裁決。
四態判決(hash 定生死,檔名不能定生死):
  SAME    同路徑同 hash          → 讓位零動作
  MOVED   路徑不同但倉內有同 hash → 讓位(記現址)
  DIFF    同路徑異 hash          → 候 _sha8 鏡像收容(--apply)
  MISSING 倉內查無此 hash        → 遺漏候收容(--apply 原路徑補入)
原則:
  ① 預設唯讀報告;--apply 才落檔(MISSING 補入+DIFF 鏡像),
     manifest 存證+--undo 可逆(只刪本器 apply 且 hash 未變者)。
  ② 排除快取區(.git/__pycache__/.venv/node_modules);VIA_Reports
     與 data/output 標 ARTIFACT(產物,資訊列不催收)。
  ③ 誠實三態;RICH 矩陣+JSON 存證 VIA_Reports/oldroot_runs/。
用法:
  via-oldscan --old <舊根路徑>              → 對帳報告(唯讀)
  via-oldscan --old <舊根路徑> --apply      → 補遺+鏡像收容
  via-oldscan --undo <manifest>             → 反轉一次 apply
  via-oldscan --selftest                    → 八檢(沙盒零網路)
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
OUT_ROOT = VIA / "VIA_Reports" / "oldroot_runs"
EXCLUDE_DIRS = {".git", "__pycache__", ".venv", "node_modules", "site-packages"}
ARTIFACT_FRAGS = ("VIA_Reports", "data/output", "data\\output", "output_hub")


def sha256_of(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def walk_files(root: Path):
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if any(part in EXCLUDE_DIRS for part in p.parts):
            continue
        yield p


def build_repo_index(repo: Path) -> dict[str, list[str]]:
    """倉內容雜湊索引 {sha: [relpath,…]}"""
    idx: dict[str, list[str]] = {}
    for p in walk_files(repo):
        try:
            idx.setdefault(sha256_of(p), []).append(str(p.relative_to(repo)))
        except OSError:
            continue
    return idx


def scan(old: Path, repo: Path) -> dict:
    idx = build_repo_index(repo)
    rows = []
    counts = {"SAME": 0, "MOVED": 0, "DIFF": 0, "MISSING": 0, "ARTIFACT": 0}
    for p in walk_files(old):
        rel = str(p.relative_to(old))
        rel_posix = rel.replace("\\", "/")
        try:
            h = sha256_of(p)
        except OSError as exc:
            rows.append({"rel": rel, "state": "FAIL", "note": str(exc)[:60]})
            continue
        artifact = any(frag.replace("\\", "/") in rel_posix for frag in ARTIFACT_FRAGS)
        target = repo / rel
        if target.exists() and sha256_of(target) == h:
            state, note = "SAME", "讓位零動作"
        elif h in idx:
            state, note = "MOVED", f"讓位(現址 {idx[h][0][:70]})"
        elif target.exists():
            state, note = "DIFF", "候 _sha8 鏡像(--apply)"
        else:
            state, note = "MISSING", "遺漏候收容(--apply)"
        if artifact and state in ("MISSING", "DIFF"):
            counts["ARTIFACT"] += 1
            rows.append({"rel": rel, "state": f"ARTIFACT:{state}", "sha": h[:16],
                         "note": "產物區(資訊列,不催收)"})
            continue
        counts[state] += 1
        rows.append({"rel": rel, "state": state, "sha": h[:16], "note": note})
    return {"schema": "VIA.OldRootScan.v1", "old": str(old), "repo": str(repo),
            "counts": counts, "rows": rows}


def apply_actions(result: dict, old: Path, repo: Path) -> dict:
    """MISSING 原路徑補入+DIFF _sha8 鏡像;回 manifest(零刪除+undo 可逆)"""
    applied = []
    for r in result["rows"]:
        if r["state"] == "MISSING":
            src = old / r["rel"]
            dst = repo / r["rel"]
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            applied.append({"action": "ADD", "rel": r["rel"], "sha": sha256_of(dst)[:16]})
        elif r["state"] == "DIFF":
            src = old / r["rel"]
            h8 = sha256_of(src)[:8]
            base = repo / r["rel"]
            dst = base.with_name(f"{base.stem}_sha{h8}{base.suffix}")
            if not dst.exists():
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
                applied.append({"action": "MIRROR",
                                "rel": str(dst.relative_to(repo)), "sha": sha256_of(dst)[:16]})
    return {"applied": applied, "n": len(applied)}


def undo(manifest_path: Path, repo: Path = VIA) -> int:
    m = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    n_undone = n_skip = 0
    for a in m.get("apply", {}).get("applied", []):
        p = repo / a["rel"]
        if p.exists() and sha256_of(p)[:16] == a["sha"]:
            p.unlink()
            n_undone += 1
        else:
            n_skip += 1  # 已變動/已缺=誠實不動
    print(f"  [undo] 還原 {n_undone} · 略過 {n_skip}(hash 已變/缺,誠實)")
    return 0


def rich_report(result: dict) -> None:
    c = result["counts"]
    print(f"  [計] SAME {c['SAME']}(讓位)· MOVED {c['MOVED']}(讓位)· "
          f"DIFF {c['DIFF']}(候鏡像)· MISSING {c['MISSING']}(遺漏候收容)· "
          f"ARTIFACT {c['ARTIFACT']}(產物資訊列)")
    actionable = [r for r in result["rows"] if r["state"] in ("MISSING", "DIFF")]
    try:
        from rich import box
        from rich.console import Console
        from rich.table import Table
        t = Table(title="舊根對帳 — 待辦明細(MISSING/DIFF;全量見 JSON 存證)",
                  box=box.SIMPLE_HEAVY, title_style="bold", header_style="bold cyan",
                  pad_edge=False)
        for col in ["態", "相對路徑", "sha16", "判決"]:
            t.add_column(col, overflow="fold", no_wrap=False)
        for r in actionable[:80]:
            color = "red" if r["state"] == "MISSING" else "yellow"
            t.add_row(f"[{color}]{r['state']}[/]", r["rel"], r.get("sha", ""), r["note"])
        Console().print(t)
        if len(actionable) > 80:
            print(f"  [註] 明細顯示前 80,全量 {len(actionable)} 在 JSON(誠實)")
    except Exception:
        for r in actionable[:80]:
            print(f"  [{r['state']}] {r['rel']} {r['note']}")


def run(old: Path, repo: Path, do_apply: bool) -> int:
    if not old.exists():
        print(f"  [FAIL] 舊根不存在:{old}")
        return 1
    print(f"  [掃] 舊根 {old} ↔ 倉 {repo}(hash 定生死;快取區除外)")
    result = scan(old, repo)
    rich_report(result)
    if do_apply:
        result["apply"] = apply_actions(result, old, repo)
        print(f"  [apply] 落檔 {result['apply']['n']} 件(ADD 補遺+MIRROR 鏡像;undo 可逆)")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    mf = OUT_ROOT / f"OLDROOT_{ts}.json"
    mf.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  [存] {mf}")
    if do_apply:
        print(f"  [undo] via-oldscan --undo \"{mf}\"")
    return 0


def selftest() -> int:
    import tempfile
    t0 = time.time()
    fails = []

    def chk(name, cond, note=""):
        if not cond:
            fails.append(name)
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")

    with tempfile.TemporaryDirectory() as td:
        sand = Path(td)
        old = sand / "old"
        repo = sand / "repo"
        (old / "a").mkdir(parents=True)
        (repo / "a").mkdir(parents=True)
        (repo / "b").mkdir()
        (old / "a" / "same.py").write_text("SAME", encoding="utf-8")
        (repo / "a" / "same.py").write_text("SAME", encoding="utf-8")
        (old / "a" / "moved.py").write_text("MOVEDCONTENT", encoding="utf-8")
        (repo / "b" / "renamed.py").write_text("MOVEDCONTENT", encoding="utf-8")
        (old / "a" / "diff.py").write_text("OLDBODY", encoding="utf-8")
        (repo / "a" / "diff.py").write_text("NEWBODY", encoding="utf-8")
        (old / "a" / "missing.py").write_text("LOSTFILE", encoding="utf-8")
        (old / "VIA_Reports").mkdir()
        (old / "VIA_Reports" / "run.json").write_text("{}", encoding="utf-8")
        (old / "__pycache__").mkdir()
        (old / "__pycache__" / "x.pyc").write_text("c", encoding="utf-8")
        r = scan(old, repo)
        c = r["counts"]
        # ① 四態判決各一
        chk("四態判決", c["SAME"] == 1 and c["MOVED"] == 1 and c["DIFF"] == 1
            and c["MISSING"] == 1)
        # ② 產物區資訊列
        chk("產物區 ARTIFACT", c["ARTIFACT"] == 1)
        # ③ 快取區排除
        chk("快取區排除", not any("__pycache__" in x["rel"] for x in r["rows"]))
        # ④ MOVED 記現址
        mv = next(x for x in r["rows"] if x["state"] == "MOVED")
        chk("MOVED 記現址", "renamed.py" in mv["note"])
        # ⑤ apply:補遺+鏡像
        r["apply"] = apply_actions(r, old, repo)
        chk("apply 補遺+鏡像", r["apply"]["n"] == 2
            and (repo / "a" / "missing.py").exists()
            and len(list((repo / "a").glob("diff_sha*.py"))) == 1
            and (repo / "a" / "diff.py").read_text(encoding="utf-8") == "NEWBODY")
        # ⑥ 再掃=零待辦(冪等)
        r2 = scan(old, repo)
        chk("冪等(再掃零 MISSING/DIFF)", r2["counts"]["MISSING"] == 0
            and r2["counts"]["DIFF"] == 0)
        # ⑦ undo 可逆
        mfp = sand / "mf.json"
        mfp.write_text(json.dumps(r, ensure_ascii=False), encoding="utf-8")
        undo(mfp, repo)
        chk("undo 可逆", not (repo / "a" / "missing.py").exists()
            and not list((repo / "a").glob("diff_sha*.py")))
        # ⑧ 正本零觸碰(repo 原件內容不變)
        chk("正本零觸碰", (repo / "a" / "diff.py").read_text(encoding="utf-8") == "NEWBODY"
            and (repo / "a" / "same.py").read_text(encoding="utf-8") == "SAME")
    n = 8 - len(fails)
    print(f"  [計] 八檢 OK {n} · FAIL {len(fails)} · {round(time.time() - t0, 1)}s")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== 舊根對帳掃描器 v0100 · 八檢(沙盒零網路)===")
        return selftest()
    if "--undo" in args:
        i = args.index("--undo")
        if i + 1 >= len(args):
            print("[用法] via-oldscan --undo <manifest>")
            return 2
        print("=== 舊根對帳 undo(零刪除鐵律:只刪本器 apply 且 hash 未變者)===")
        return undo(Path(args[i + 1]))
    if "--old" not in args:
        print(__doc__.split("用法:")[1])
        return 2
    i = args.index("--old")
    old = Path(args[i + 1]) if i + 1 < len(args) else None
    repo = VIA
    if "--repo" in args:
        j = args.index("--repo")
        repo = Path(args[j + 1])
    print("=== 舊根對帳掃描器 v0100 · 檢查遺漏+整合(TOOL-086)===")
    return run(old, repo, "--apply" in args)


if __name__ == "__main__":
    sys.exit(main())
