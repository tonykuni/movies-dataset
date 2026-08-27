#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
via_oldroot_scan_v0104 — 舊根對帳掃描器(TOOL-086)
v0103→v0104(批84):docstring 改 raw 字串——工作站 Py3.13 對「\\?\ 」
  尾隨空白判 invalid escape SyntaxWarning(噪音蓋進度條);行為零變更。
v0102→v0103(批82,2026-08-20):Windows 長路徑免疫+apply 不斷鏈:
  ⑩ 工作站實證 git stash 撞 260 字元上限(Filename too long,
     rollback/rb-… 深巢路徑)。本器自身改 \\?\ 長路徑前綴(_lp:
     nt 且 ≥248 字元自動加前綴,雜湊/複製/建夾全走),不依賴
     registry LongPathsEnabled 也能處理超長路徑。
  ⑪ apply 逐檔 try/except:單檔 OSError(長路徑/鎖檔/權限)記
     FAIL 列誠實入 manifest,不再炸斷整場 apply。
v0101→v0102(批81):工作站真跑卡斷證據定讞的三修:
  ⑦ 舊根側也并行+進度條 — v0101 只有倉索引并行,scan() 對舊根
     145k 件仍「串行雜湊零輸出」=卡斷主因。改:舊根盤點 sweep+
     ThreadPool 并行雜湊+單行進度條(常備令Ⅱ全程不卡斷)。
  ⑧ 免重複雜湊 — SAME 判定原對 target 再整檔雜湊一次(倉已索引
     過);改用索引附帶 rel→sha 映射直查,倉側零第二次雜湊。
  ⑨ 加速器數可調 — 環境變數 VIA_OLDSCAN_WORKERS(操作員令 25 個
     加速器);未設=CPU-1。存證 JSON 錨定 --repo(唯一正典)之
     VIA_Reports/oldroot_runs/,不再落舊克隆;apply 亦有進度條。
v0100→v0101(批77):--with-artifacts 唯一夾整併+倉索引并行+橋。
====================================================================
四態判決(hash 定生死,檔名不能定生死):
  SAME    同路徑同 hash          → 讓位零動作
  MOVED   路徑不同但倉內有同 hash → 讓位(記現址)
  DIFF    同路徑異 hash          → 候 _sha8 鏡像收容(--apply)
  MISSING 倉內查無此 hash        → 遺漏候收容(--apply 原路徑補入)
原則:
  ① 預設唯讀報告;--apply 才落檔(MISSING 補入+DIFF 鏡像),
     manifest 存證+--undo 可逆(只刪本器 apply 且 hash 未變者)。
  ② 排除快取區(.git/__pycache__/.venv/node_modules);VIA_Reports
     與 data/output 標 ARTIFACT(產物,資訊列不催收);
     --with-artifacts 才升入待辦與 apply(唯一夾整併模式)。
  ③ 誠實三態;RICH 矩陣+JSON 存證(錨定 repo)。
用法:
  via-oldscan --old <舊根路徑>              → 對帳報告(唯讀)
  via-oldscan --old <舊根路徑> --apply      → 補遺+鏡像收容
  via-oldscan --old <舊根> --apply --with-artifacts → 連產物區抓回(唯一夾整併)
  via-oldscan --undo <manifest>             → 反轉一次 apply
  via-oldscan --selftest                    → 十四檢(沙盒零網路)
"""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(全引擎導入令 2026-08-18;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # accel_map/fetch/pip_install/run_fast
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

import hashlib
import json
import os
import shutil
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
EXCLUDE_DIRS = {".git", "__pycache__", ".venv", "node_modules", "site-packages"}
ARTIFACT_FRAGS = ("VIA_Reports", "data/output", "data\\output", "output_hub")


def _workers() -> int:
    """加速器數:VIA_OLDSCAN_WORKERS 環境變數(批81 令 25)>CPU-1"""
    try:
        w = int(os.environ.get("VIA_OLDSCAN_WORKERS", "0"))
    except ValueError:
        w = 0
    return w if w > 0 else max(2, (os.cpu_count() or 4) - 1)


def _lp(p: Path) -> str:
    r"""Windows 長路徑免疫(批82 ⑩):nt 且 ≥248 字元自動加 \\?\ 前綴"""
    s = str(p)
    if os.name == "nt" and len(s) >= 248 and not s.startswith("\\\\?\\"):
        return "\\\\?\\" + s
    return s


def sha256_of(p: Path) -> str:
    h = hashlib.sha256()
    with open(_lp(p), "rb") as f:
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


def _sweep(msg: str, i: int, n: int) -> None:
    """常備令Ⅱ:單行動態進度條不卡斷"""
    w = 24
    k = int(w * i / max(n, 1))
    sys.stdout.write(f"\r  [{'█' * k}{'░' * (w - k)}] {i}/{n} {msg[:40]:<40}")
    sys.stdout.flush()
    if i >= n:
        sys.stdout.write("\n")


def _hash_parallel(files: list[Path], label: str) -> dict[Path, tuple[str | None, str]]:
    """并行雜湊(VIA_OLDSCAN_WORKERS 工)+進度條;回 {path:(sha|None,err)}"""
    out: dict[Path, tuple[str | None, str]] = {}
    if not files:
        return out

    def job(p: Path):
        try:
            return p, sha256_of(p), ""
        except OSError as exc:
            return p, None, str(exc)[:60]
    with ThreadPoolExecutor(max_workers=_workers()) as ex:
        for i, (p, h, err) in enumerate(ex.map(job, files), 1):
            out[p] = (h, err)
            if i % 200 == 0 or i == len(files):
                _sweep(label, i, len(files))
    return out


def build_repo_index(repo: Path) -> tuple[dict[str, list[str]], dict[str, str]]:
    """倉雜湊索引 {sha:[rel,…]} + {rel:sha}(免二次雜湊,批81 ⑧)"""
    files = []
    for i, p in enumerate(walk_files(repo), 1):
        files.append(p)
        if i % 1000 == 0:
            sys.stdout.write(f"\r  [走] 倉盤點 {i} 件…")
            sys.stdout.flush()
    if len(files) >= 1000:
        sys.stdout.write("\n")
    hashes = _hash_parallel(files, "倉索引")
    idx: dict[str, list[str]] = {}
    rel_sha: dict[str, str] = {}
    for p, (h, _err) in hashes.items():
        if h:
            rel = str(p.relative_to(repo))
            idx.setdefault(h, []).append(rel)
            rel_sha[rel] = h
    return idx, rel_sha


def scan(old: Path, repo: Path, with_artifacts: bool = False) -> dict:
    idx, rel_sha = build_repo_index(repo)
    old_files = []
    for i, p in enumerate(walk_files(old), 1):
        old_files.append(p)
        if i % 1000 == 0:
            sys.stdout.write(f"\r  [走] 舊根盤點 {i} 件…")
            sys.stdout.flush()
    if len(old_files) >= 1000:
        sys.stdout.write("\n")
    hashes = _hash_parallel(old_files, "舊根雜湊")
    rows = []
    counts = {"SAME": 0, "MOVED": 0, "DIFF": 0, "MISSING": 0, "ARTIFACT": 0}
    for p in old_files:
        rel = str(p.relative_to(old))
        rel_posix = rel.replace("\\", "/")
        h, err = hashes.get(p, (None, "no-hash"))
        if not h:
            rows.append({"rel": rel, "state": "FAIL", "note": err})
            continue
        artifact = any(frag.replace("\\", "/") in rel_posix for frag in ARTIFACT_FRAGS)
        repo_h = rel_sha.get(rel)
        if repo_h == h:
            state, note = "SAME", "讓位零動作"
        elif h in idx:
            state, note = "MOVED", f"讓位(現址 {idx[h][0][:70]})"
        elif repo_h is not None or (repo / rel).exists():
            state, note = "DIFF", "候 _sha8 鏡像(--apply)"
        else:
            state, note = "MISSING", "遺漏候收容(--apply)"
        if artifact and state in ("MISSING", "DIFF") and not with_artifacts:
            counts["ARTIFACT"] += 1
            rows.append({"rel": rel, "state": f"ARTIFACT:{state}", "sha": h[:16],
                         "note": "產物區(資訊列,不催收)"})
            continue
        counts[state] += 1
        rows.append({"rel": rel, "state": state, "sha": h[:16], "note": note})
    return {"schema": "VIA.OldRootScan.v1", "old": str(old), "repo": str(repo),
            "with_artifacts": with_artifacts, "workers": _workers(),
            "counts": counts, "rows": rows}


def apply_actions(result: dict, old: Path, repo: Path) -> dict:
    """MISSING 補入+DIFF _sha8 鏡像;逐檔 try/except 不斷鏈(批82 ⑪);
    進度條;manifest(零刪除+undo 可逆)"""
    actionable = [r for r in result["rows"] if r["state"] in ("MISSING", "DIFF")]
    applied = []
    failed = []
    for i, r in enumerate(actionable, 1):
        try:
            if r["state"] == "MISSING":
                src = old / r["rel"]
                dst = repo / r["rel"]
                Path(_lp(dst.parent)).mkdir(parents=True, exist_ok=True)
                shutil.copy2(_lp(src), _lp(dst))
                applied.append({"action": "ADD", "rel": r["rel"],
                                "sha": sha256_of(dst)[:16]})
            else:
                src = old / r["rel"]
                h8 = sha256_of(src)[:8]
                base = repo / r["rel"]
                dst = base.with_name(f"{base.stem}_sha{h8}{base.suffix}")
                if not dst.exists():
                    Path(_lp(dst.parent)).mkdir(parents=True, exist_ok=True)
                    shutil.copy2(_lp(src), _lp(dst))
                    applied.append({"action": "MIRROR",
                                    "rel": str(dst.relative_to(repo)),
                                    "sha": sha256_of(dst)[:16]})
        except OSError as exc:
            failed.append({"rel": r["rel"], "err": str(exc)[:80]})
        if i % 100 == 0 or i == len(actionable):
            _sweep("apply 落檔", i, len(actionable))
    if failed:
        print(f"  [WARN] apply 單檔失敗 {len(failed)} 件(誠實入 manifest,不斷鏈)")
    return {"applied": applied, "n": len(applied), "failed": failed}


def undo(manifest_path: Path, repo: Path | None = None) -> int:
    m = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    repo = repo or Path(m.get("repo", str(VIA)))
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
          f"ARTIFACT {c['ARTIFACT']}(產物資訊列)· 工 {result['workers']}")
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


def run(old: Path, repo: Path, do_apply: bool, with_artifacts: bool = False) -> int:
    if not old.exists():
        print(f"  [FAIL] 舊根不存在:{old}")
        return 1
    print(f"  [掃] 舊根 {old} ↔ 倉 {repo}(hash 定生死;快取區除外;工 {_workers()})")
    result = scan(old, repo, with_artifacts)
    rich_report(result)
    if do_apply:
        result["apply"] = apply_actions(result, old, repo)
        print(f"  [apply] 落檔 {result['apply']['n']} 件(ADD 補遺+MIRROR 鏡像;undo 可逆)")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_root = repo / "VIA_Reports" / "oldroot_runs"  # 批81 ⑨:存證錨定唯一正典
    out_root.mkdir(parents=True, exist_ok=True)
    mf = out_root / f"OLDROOT_{ts}.json"
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
        # ⑨ 唯一夾整併模式:--with-artifacts 連產物抓回(批77)
        r3 = scan(old, repo, with_artifacts=True)
        chk("with-artifacts 產物入待辦", r3["counts"]["ARTIFACT"] == 0
            and any(x["rel"].startswith("VIA_Reports") and x["state"] == "MISSING"
                    for x in r3["rows"]))
        r3["apply"] = apply_actions(r3, old, repo)
        chk("產物抓回落檔", (repo / "VIA_Reports" / "run.json").exists())
        # ⑪ 加速器數環境變數可調(批81 令 25)
        _saved = os.environ.get("VIA_OLDSCAN_WORKERS")
        os.environ["VIA_OLDSCAN_WORKERS"] = "25"
        w25 = _workers()
        os.environ["VIA_OLDSCAN_WORKERS"] = "bogus"
        wfb = _workers()
        if _saved is None:
            os.environ.pop("VIA_OLDSCAN_WORKERS", None)
        else:
            os.environ["VIA_OLDSCAN_WORKERS"] = _saved
        chk("加速器數可調", w25 == 25 and wfb >= 2)
        # ⑫ 存證錨定 --repo(不落舊克隆)
        rc = run(old, repo, do_apply=False)
        chk("存證錨定 repo", rc == 0
            and len(list((repo / "VIA_Reports" / "oldroot_runs").glob("OLDROOT_*.json"))) == 1)
        # ⑬ apply 例外不斷鏈(批82:單檔失效記 failed,其餘照落)
        old2 = sand / "old2"
        repo2 = sand / "repo2"
        old2.mkdir()
        repo2.mkdir()
        (old2 / "keep.py").write_text("KEEP", encoding="utf-8")
        (old2 / "gone.py").write_text("GONE", encoding="utf-8")
        r4 = scan(old2, repo2)
        (old2 / "gone.py").unlink()  # 模擬 apply 時來源鎖檔/長路徑失效
        r4["apply"] = apply_actions(r4, old2, repo2)
        chk("apply 例外不斷鏈", (repo2 / "keep.py").exists()
            and len(r4["apply"]["failed"]) == 1
            and r4["apply"]["failed"][0]["rel"] == "gone.py")
        # ⑭ 長路徑前綴器(nt 才加前綴;posix 原樣)
        import unittest.mock as _mock
        longp = Path("C:\\" + "a" * 300 + "\\x.py")
        with _mock.patch("os.name", "nt"):
            pref = _lp(longp)
        chk("長路徑前綴器", pref.startswith("\\\\?\\") and _lp(Path("short.py")) == "short.py")
    n = 14 - len(fails)
    print(f"  [計] 十四檢 OK {n} · FAIL {len(fails)} · {round(time.time() - t0, 1)}s")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== 舊根對帳掃描器 v0104 · 十四檢(沙盒零網路)===")
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
    print("=== 舊根對帳掃描器 v0104 · 唯一夾整併(TOOL-086)===")
    return run(old, repo, "--apply" in args, "--with-artifacts" in args)


if __name__ == "__main__":
    sys.exit(main())
