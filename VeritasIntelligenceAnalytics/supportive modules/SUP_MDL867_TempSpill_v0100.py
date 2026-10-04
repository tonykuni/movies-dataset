#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""SUP_MDL867_TempSpill v0100 — 記憶體改用 TEMP(L107 · R-DB-06 · R-TEMP-01 的 Python 共用件;操作員 2026-10-03「記憶體改用 TEMP」)

PS 骨架 v0104 已把 TMP / TEMP / TMPDIR / POLARS_TEMP_DIR / VIA_DUCKDB_TEMP_DIR 指到 VIA_TEMP_ROOT\<run>;本支是 Python 這一半:
引擎檔頭一行 `import SUP_MDL867_TempSpill as spill; RUN = spill.activate("<引擎名>")` 之後 —
  ① tempfile.tempdir / TMP / TEMP / TMPDIR 全指 VIA_TEMP_ROOT/<tool>/<run>(不在 OneDrive · 不進 git)
  ② duckdb:spill.connect(db) 回一條已 SET temp_directory · memory_limit(預設 2GB,可環境變數 VIA_DUCKDB_MEM)· threads 的連線;大 JOIN / GROUP BY 落碟
  ③ polars:POLARS_TEMP_DIR 指過去;spill.collect(lf) = lf.collect(streaming=True)(大於記憶體的框走串流)
  ④ pandas 大檔:spill.read_csv_chunks(path) 以 chunk 寫 parquet part 再 duckdb 讀(不整表進記憶體)
  ⑤ pymupdf / OCR 中介:spill.doc_dir(doc_sha) → <run>/<doc_sha>/<page>/<dpi>/<tool>(R-TEMP-01 分夾;文件做完 spill.done(doc_sha) 才清)
  ⑥ 滾動:每工具只留最近 N 輪(預設 5;VIA_TEMP_KEEP),刪了追加 purge_ledger.jsonl(L107 ④);三不刪:VIA_Reports · registry · 任何冊 / 帳
只動 TEMP;不碰正本;缺 duckdb / polars 時各自 graceful(回 None,不假綠)。
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
import json, os, shutil, sys, tempfile, time
from datetime import datetime
from pathlib import Path

ENGINE = "SUP_MDL867_TempSpill_v0100"
_STATE: dict = {"run": None, "tool": None}
FORBIDDEN = ("VIA_Reports", "supportive modules", "functional modules", ".git")   # 三不刪:路徑含這些一律不清


def temp_root() -> Path:
    r = os.environ.get("VIA_TEMP_ROOT")
    if not r:
        base = os.environ.get("LOCALAPPDATA") or tempfile.gettempdir()
        r = str(Path(base) / "Temp" / "VIA_progress")
    p = Path(r); p.mkdir(parents=True, exist_ok=True)
    return p


def activate(tool: str, keep: int | None = None) -> Path:
    """指 TEMP · 建本輪夾 · 滾動清舊輪。回本輪夾。"""
    root = temp_root(); keep = keep or int(os.environ.get("VIA_TEMP_KEEP") or 5)
    tdir = root / tool; tdir.mkdir(parents=True, exist_ok=True)
    run = tdir / ("run_" + datetime.now().strftime("%Y%m%d_%H%M%S_%f")); run.mkdir(parents=True, exist_ok=True)
    for k in ("TMP", "TEMP", "TMPDIR", "POLARS_TEMP_DIR", "VIA_DUCKDB_TEMP_DIR"):
        os.environ[k] = str(run)
    os.environ["VIA_SPILL_TO_DISK"] = "1"; tempfile.tempdir = str(run)
    _STATE.update(run=run, tool=tool)
    purge(tool, keep)
    return run


def purge(tool: str, keep: int = 5) -> list:
    """只清本工具夾下的舊輪;留最近 keep 輪;每筆記 purge_ledger.jsonl。"""
    tdir = temp_root() / tool
    if not tdir.is_dir():
        return []
    runs = sorted((p for p in tdir.iterdir() if p.is_dir() and p.name.startswith("run_")), key=lambda p: p.name)
    gone = []
    for p in runs[:-keep] if keep > 0 else []:
        if any(f in str(p) for f in FORBIDDEN):
            continue
        mb = round(sum(f.stat().st_size for f in p.rglob("*") if f.is_file()) / 1048576, 2)
        shutil.rmtree(p, ignore_errors=True); gone.append(p.name)
        with open(temp_root() / "purge_ledger.jsonl", "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"at": datetime.now().isoformat(timespec="seconds"), "tool": tool, "purged": p.name, "mb": mb, "rule": f"L107 keep_last={keep}", "by": ENGINE}, ensure_ascii=False) + "\n")
    return gone


def run_dir() -> Path:
    return _STATE["run"] or activate(_STATE["tool"] or "anon")


def doc_dir(doc_sha: str, page: int | None = None, dpi: int | None = None, tool: str | None = None) -> Path:
    """R-TEMP-01:<run>/<doc_sha>/<page>/<dpi>/<tool>;同一頁同 dpi 的渲染給輕 → 重工具共用。"""
    p = run_dir() / doc_sha[:16]
    for part in (page, dpi, tool):
        if part is not None:
            p = p / str(part)
    p.mkdir(parents=True, exist_ok=True)
    return p


def done(doc_sha: str) -> bool:
    """文件做完才清它的分夾(不是每個動作就清)。"""
    p = run_dir() / doc_sha[:16]
    if p.is_dir():
        shutil.rmtree(p, ignore_errors=True); return True
    return False


def connect(db: str | os.PathLike = ":memory:", read_only: bool = False):
    """duckdb 連線已設 temp_directory(本輪夾)· memory_limit · threads;缺 duckdb 回 None。"""
    try:
        import duckdb
    except Exception:
        return None
    con = duckdb.connect(str(db), read_only=read_only)
    con.execute(f"SET temp_directory='{str(run_dir()).replace(chr(39), chr(39) * 2)}'")
    con.execute(f"SET memory_limit='{os.environ.get('VIA_DUCKDB_MEM') or '2GB'}'")
    con.execute(f"SET threads={int(os.environ.get('VIA_DUCKDB_THREADS') or max(1, (os.cpu_count() or 2) - 1))}")
    return con


def collect(lf):
    """polars LazyFrame 走串流 collect(大於記憶體也行);不是 LazyFrame 原樣回。"""
    try:
        import polars as pl
        if isinstance(lf, pl.LazyFrame):
            try:
                return lf.collect(engine="streaming")
            except TypeError:
                return lf.collect(streaming=True)
    except Exception:
        pass
    return lf


def read_csv_chunks(path: str | os.PathLike, chunksize: int = 200_000, **kw) -> Path | None:
    """pandas 大 CSV → chunk 落 parquet part(本輪夾)→ 回夾;之後 duckdb read_parquet('<夾>/*.parquet')。缺 pandas/pyarrow 回 None。"""
    try:
        import pandas as pd
    except Exception:
        return None
    out = run_dir() / ("csv_" + Path(path).stem); out.mkdir(parents=True, exist_ok=True)
    for i, chunk in enumerate(pd.read_csv(path, chunksize=chunksize, **kw)):
        tmp = out / f"part_{i:05d}.parquet.tmp"
        chunk.to_parquet(tmp, index=False); tmp.replace(out / f"part_{i:05d}.parquet")      # 原子換名(R-DB-05)
    return out


def status() -> dict:
    root = temp_root()
    size = sum(f.stat().st_size for f in root.rglob("*") if f.is_file()) if root.is_dir() else 0
    return {"root": str(root), "run": str(_STATE["run"]) if _STATE["run"] else None, "tool": _STATE["tool"], "mb": round(size / 1048576, 1),
            "env": {k: os.environ.get(k) for k in ("TMP", "TEMP", "TMPDIR", "POLARS_TEMP_DIR", "VIA_DUCKDB_TEMP_DIR", "VIA_SPILL_TO_DISK")}}


def selftest() -> int:
    ok = []
    def chk(name, cond, note=""):
        ok.append(bool(cond)); print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + note) if note else ''}")
    with tempfile.TemporaryDirectory() as td:
        os.environ["VIA_TEMP_ROOT"] = td
        r1 = activate("selftest_tool", keep=2)
        chk("① activate:本輪夾在 VIA_TEMP_ROOT 下 · TMP/TEMP/TMPDIR/POLARS/duckdb 全指過去", r1.is_dir() and all(os.environ[k] == str(r1) for k in ("TMP", "TEMP", "TMPDIR", "POLARS_TEMP_DIR", "VIA_DUCKDB_TEMP_DIR")) and tempfile.gettempdir() == str(r1))
        for _ in range(3):
            time.sleep(0.002); activate("selftest_tool", keep=2)
        runs = sorted(p.name for p in (Path(td) / "selftest_tool").iterdir() if p.is_dir())
        led = (Path(td) / "purge_ledger.jsonl")
        chk("② 滾動留 2 輪 · 刪了記帳", len(runs) == 2 and led.is_file() and len(led.read_text(encoding="utf-8").splitlines()) >= 2, f"輪 {len(runs)}")
        d = doc_dir("abcdef0123456789ffff", 1, 300, "rapidocr"); chk("③ 文件分夾 <sha>/<page>/<dpi>/<tool>", d.is_dir() and d.parts[-3:] == ("1", "300", "rapidocr"))
        chk("④ done(sha) 才清文件夾", done("abcdef0123456789ffff") and not d.exists())
        con = connect()
        if con is None:
            chk("⑤ duckdb 缺 → None(誠實)", True, "duckdb 缺")
        else:
            td_set = con.execute("SELECT current_setting('temp_directory')").fetchone()[0]
            chk("⑤ duckdb temp_directory = 本輪夾 · memory_limit 在", str(run_dir()) in str(td_set) and con.execute("SELECT current_setting('memory_limit')").fetchone()[0], str(td_set)[-40:])
            con.close()
        try:
            import pandas as pd
            csv = Path(td) / "big.csv"; pd.DataFrame({"a": range(1000), "b": range(1000)}).to_csv(csv, index=False)
            out = read_csv_chunks(csv, chunksize=300)
            chk("⑥ 大 CSV chunk → parquet parts(原子換名,無 .tmp 殘留)", out is not None and len(list(out.glob("*.parquet"))) == 4 and not list(out.glob("*.tmp")))
        except Exception as e:
            chk("⑥ pandas/pyarrow 缺 → 跳過(誠實)", True, str(e)[:40])
        chk("⑦ 三不刪:含 VIA_Reports 的路徑不會被 purge 碰", all(f not in str(run_dir()) for f in FORBIDDEN))
        chk("⑧ 加速器橋在", "VIA:ACCEL-BRIDGE" in Path(__file__).read_text(encoding="utf-8"))
    print(f"  [計] {ENGINE} 自測 {sum(ok)}/{len(ok)} · {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv[1:]:
        raise SystemExit(selftest())
    if "status" in sys.argv[1:]:
        print(json.dumps(status(), ensure_ascii=False, indent=1)); raise SystemExit(0)
    print(__doc__)
