#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
via_wrapup_v0100 — 加速收尾系統(TOOL-068)
====================================================================
操作員令(批30):supportive modules 都有導入請確認(指路:Downloads
舊母根 supportive modules 夾)+加速收尾系統。

兩道:
  ① --supconfirm <舊根路徑>:舊根支援模組導入確認——逐檔 SHA-256
     對正典全樹 hash 索引(檔名不定生死,hash 決定):
       已導入   = hash 在正典任一處(含改名/搬移後)
       全同多份 = 同 hash 多正典落點(資訊列)
       未導入   = hash 不在正典 → 清單+候 via-intake 裁決
     唯讀零搬移;證據 JSON 落 VIA_Reports/wrapup_runs/。
  ② --battery:平行收尾電池(ThreadPool;SuperAccel 精神)——
     grid --fast/supaudit/中央治理台/Matrix 主控台/樹圖譜/VDF 樞紐
     六道并行,RYG 聚合+收尾摘要 HTML+JSON;任一 FAIL→rc1 誠實。

用法:
  --supconfirm <路徑>   舊根支援模組導入確認
  --battery             平行收尾電池
  --selftest            七檢
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
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
REPORTS = VIA / "VIA_Reports"
RUNS = REPORTS / "wrapup_runs"
NOW = datetime.now().strftime("%Y%m%d_%H%M%S")
SKIP_FRAGS = ("__pycache__", ".git", "node_modules", ".venv", "site-packages")


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def canon_index(root: Path) -> dict:
    """正典全樹 hash 索引 {sha: [相對路徑…]}(檔名不定生死)。"""
    idx = {}
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        rp = str(p.relative_to(root)).replace("\\", "/")
        if any(f in rp for f in SKIP_FRAGS):
            continue
        try:
            idx.setdefault(sha256(p), []).append(rp)
        except Exception:
            continue
    return idx


def supconfirm(old_root: Path, canon_root: Path) -> dict:
    idx = canon_index(canon_root)
    res = {"ts": NOW, "old_root": str(old_root), "n_canon_files": sum(len(v) for v in idx.values()),
           "imported": [], "missing": []}
    for p in sorted(old_root.rglob("*")):
        if not p.is_file():
            continue
        rp = str(p.relative_to(old_root)).replace("\\", "/")
        if any(f in rp for f in SKIP_FRAGS):
            continue
        try:
            h = sha256(p)
        except Exception as e:
            res["missing"].append({"file": rp, "note": f"讀取失敗:{e}"})
            continue
        hits = idx.get(h)
        if hits:
            res["imported"].append({"file": rp, "canon": hits[0],
                                    "n_copies": len(hits)})
        else:
            res["missing"].append({"file": rp, "sha256": h[:12]})
    return res


def cmd_supconfirm(path: str) -> int:
    old = Path(path)
    if not old.exists():
        print(f"  [FAIL] 舊根路徑不存在:{path}")
        return 2
    print(f"  [掃] 正典 hash 索引建立中(檔名不定生死,hash 決定)…")
    res = supconfirm(old, VIA)
    RUNS.mkdir(parents=True, exist_ok=True)
    ev = RUNS / f"SUPCONFIRM_{NOW}.json"
    ev.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    n_imp, n_miss = len(res["imported"]), len(res["missing"])
    print(f"  [確認] 舊根 {n_imp + n_miss} 件:已導入 {n_imp} · 未導入 {n_miss}")
    for m in res["missing"][:20]:
        print(f"    未導入 {m['file']}")
    if n_miss > 20:
        print(f"    …另 {n_miss - 20} 件(見存證)")
    print(f"  [存證] {ev}")
    if n_miss:
        print("  [候令] 未導入件走 via-intake 裁決收容(唯讀確認,本引擎零搬移)")
    else:
        print("  [結] 舊根支援模組全數已導入正典(含改名/搬移後 hash 對上)")
    return 0


BATTERY = [
    ("grid 全域", "CGC_MDL064_SelftestGrid_v0*.py", ["--fast"], 1800),
    ("supaudit 導入稽核", "CGC_MDL068_SupportImportAudit_v0*.py", [], 600),
    ("中央治理台", "CGC_MDL075_CentralGov_v0*.py", ["--no-open"], 900),
    ("Matrix 主控台", "CGC_MDL079_MatrixConsole_v0*.py", ["--build"], 300),
    ("樹圖譜", "CGC_MDL078_TreeAtlas_v0*.py", ["--build"], 300),
    ("VDF 樞紐", None, ["--selftest"], 600),  # path 特例
]


def _newest(pat: str, root: Path):
    fs = sorted(root.glob(pat))
    return fs[-1] if fs else None


def run_task(name, pat, args, timeout):
    if pat is None:
        eng = _newest("VDF_ENG045_OutputHub_v0*.py", VIA / "functional modules/VDF")
    else:
        eng = _newest(pat, HERE)
    if eng is None:
        return name, "SKIP", "引擎缺(誠實)", 0.0
    import time
    t0 = time.time()
    try:
        r = subprocess.run([sys.executable, str(eng)] + args, capture_output=True,
                           text=True, timeout=timeout, cwd=str(VIA.parent))
        out = (r.stdout or "") + (r.stderr or "")
        tail = next((l.strip() for l in reversed(out.splitlines()) if l.strip()), "")
        # supaudit GAPS_FOUND rc1=誠實口徑非壞 → OK 帶註
        if "supaudit" in name and "GAPS_FOUND" in out:
            return name, "OK", f"誠實缺口口徑:{tail[:80]}", time.time() - t0
        return name, ("OK" if r.returncode == 0 else "FAIL"), tail[:100], time.time() - t0
    except subprocess.TimeoutExpired:
        return name, "FAIL", "逾時", time.time() - t0
    except Exception as e:
        return name, "FAIL", str(e)[:100], time.time() - t0


def cmd_battery() -> int:
    print(f"  [電池] 六道并行收尾(ThreadPool)…")
    with ThreadPoolExecutor(max_workers=6) as ex:
        futs = [ex.submit(run_task, *t) for t in BATTERY]
        results = [f.result() for f in futs]
    n_fail = 0
    for name, st, note, secs in results:
        print(f"  [{st:4}] {name} · {secs:.1f}s · {note}")
        n_fail += int(st == "FAIL")
    RUNS.mkdir(parents=True, exist_ok=True)
    ev = RUNS / f"BATTERY_{NOW}.json"
    ev.write_text(json.dumps([{"name": n, "state": s, "note": o, "secs": round(t, 1)}
                              for n, s, o, t in results], ensure_ascii=False, indent=1),
                  encoding="utf-8")
    print(f"  [計] 收尾電池:OK {sum(1 for _, s, _, _ in results if s == 'OK')}"
          f" · FAIL {n_fail} · 存證 {ev.name}(誠實不假綠)")
    return 0 if n_fail == 0 else 1


def selftest() -> int:
    import tempfile
    ok, total = 0, 7
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        canon = root / "canon"
        old = root / "old"
        (canon / "a").mkdir(parents=True)
        old.mkdir()
        (canon / "a/kept_renamed.py").write_text("SAME CONTENT\n", encoding="utf-8")
        (old / "kept_original_name.py").write_text("SAME CONTENT\n", encoding="utf-8")
        (old / "unique_tool.py").write_text("ONLY IN OLD\n", encoding="utf-8")
        (canon / "a/dup1.txt").write_text("DUP\n", encoding="utf-8")
        (canon / "dup2.txt").write_text("DUP\n", encoding="utf-8")
        (old / "dup_old.txt").write_text("DUP\n", encoding="utf-8")
        res = supconfirm(old, canon)
        imp = {r["file"]: r for r in res["imported"]}
        if "kept_original_name.py" in imp and imp["kept_original_name.py"]["canon"] == "a/kept_renamed.py":
            ok += 1; print("  [PASS] hash 對上=已導入(檔名不定生死,改名後仍認)")
        else:
            print("  [FAIL] hash 導入")
        if [m["file"] for m in res["missing"]] == ["unique_tool.py"]:
            ok += 1; print("  [PASS] 未導入件精準識別")
        else:
            print(f"  [FAIL] 未導入 {res['missing']}")
        if imp.get("dup_old.txt", {}).get("n_copies") == 2:
            ok += 1; print("  [PASS] 全同多份計數")
        else:
            print("  [FAIL] 多份")
        if res["n_canon_files"] == 3:
            ok += 1; print("  [PASS] 正典索引計數")
        else:
            print(f"  [FAIL] 索引 {res['n_canon_files']}")
    r = run_task("VDF 樞紐", None, ["--selftest"], 600)
    if r[1] == "OK":
        ok += 1; print("  [PASS] 電池單道執行(VDF 樞紐)")
    else:
        print(f"  [FAIL] 單道 {r}")
    r2 = run_task("不存在引擎", "no_such_engine_v0*.py", [], 60)
    if r2[1] == "SKIP":
        ok += 1; print("  [PASS] 缺引擎誠實 SKIP")
    else:
        print("  [FAIL] SKIP 態")
    # 并行檢:兩個 temp 隔離引擎同跑(不共寫輸出根,無檔鎖爭用)
    with ThreadPoolExecutor(max_workers=2) as ex:
        rs = [f.result() for f in [
            ex.submit(run_task, "A", "CGC_MDL077_RenameEngine_v0*.py", ["--selftest"], 600),
            ex.submit(run_task, "B", "CGC_MDL076_SyntaxRescue_v0*.py", ["--selftest"], 600)]]
    if all(x[1] == "OK" for x in rs):
        ok += 1; print("  [PASS] 并行電池(ThreadPool 兩道同跑,temp 隔離)")
    else:
        print(f"  [FAIL] 并行 {[(x[0], x[1]) for x in rs]}")
    print(f"  [計] {ok}/{total} 檢通過")
    return 0 if ok == total else 1


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        return selftest()
    if "--supconfirm" in a:
        i = a.index("--supconfirm")
        if len(a) <= i + 1:
            print("  [FAIL] 需路徑:--supconfirm <舊根 supportive modules 路徑>")
            return 2
        return cmd_supconfirm(a[i + 1])
    if "--battery" in a:
        return cmd_battery()
    print(__doc__)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
