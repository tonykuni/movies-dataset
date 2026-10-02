#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""First-page restore: text on the left, tables on the right.

Input is a parameter dict. Each table's header row becomes the DataFrame
columns. Rows are written to a temp parquet before any frame is built, so
the raw rows and the frame are not both held. Past ``mem_rows`` the frame
is only a preview; the full table stays on disk and is queried from there.
A summary is one title and four quoted points, and only after the restored
first page still covers the source.
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

import html
import importlib.util
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

import duckdb
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location(
    "vrn_eng107", HERE / "VRN_ENG107_TextRestore_v0100.py")
ENG107 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ENG107)

PARAMS = ("temp_dir", "header", "chunk", "mem_rows", "preview")
COVER_MIN = 0.999
_DROP = re.compile(r"[\s\u200b\ufeff]+")


def _bag(text: str) -> Counter:
    flat = _DROP.sub("", unicodedata.normalize("NFKC", str(text or "")))
    return Counter(flat)


def cover(source: str, restored: str) -> float:
    src = _bag(source)
    if not src:
        return 1.0
    got = _bag(restored)
    hit = sum(min(got[ch], n) for ch, n in src.items())
    return hit / sum(src.values())


def choose_text(source: str, candidate: str) -> tuple[str, str]:
    """A repair that drops a character is rolled back. The source is kept."""
    if cover(source, candidate) + 1e-12 < cover(source, source):
        return source, "ROLLBACK"
    return candidate, "REPAIRED" if candidate != source else "INTACT"


def _names(header: list) -> tuple[list[str], list[str]]:
    flags, names, seen = [], [], {}
    for i, cell in enumerate(header):
        name = str(cell).strip() if cell is not None else ""
        if not name:
            name = f"col_{i}"
            flags.append("HEADER_FILLED")
        n = seen.get(name, 0) + 1
        seen[name] = n
        if n > 1:
            name = f"{name}_{n}"
            flags.append("HEADER_DEDUPED")
        names.append(name)
    return names, flags


def _align(row: list, width: int) -> tuple[list, bool]:
    cells = [None if c is None else str(c) for c in row]
    extra = len(cells) > width
    if extra:
        cells = cells[:width - 1] + [" | ".join(cells[width - 1:])]
    elif len(cells) < width:
        cells = cells + [None] * (width - len(cells))
    return cells, extra


def header_frame(rows, params: dict) -> dict:
    """Stream ``rows`` to temp, then build the DataFrame from that file."""
    temp = Path(params["temp_dir"])
    temp.mkdir(parents=True, exist_ok=True)
    chunk = max(1, int(params.get("chunk") or 500))
    mem_rows = int(params.get("mem_rows") or 2000)
    preview = int(params.get("preview") or 20)
    header = params.get("header", 0)
    stem = str(params.get("stem") or "table")
    path = temp / f"{stem}.parquet"

    it = iter(rows)
    flags: list[str] = []
    if isinstance(header, (list, tuple)):
        columns, flags = _names(list(header))
    else:
        skip = int(header)
        head = None
        for i, row in enumerate(it):
            if i == skip:
                head = list(row)
                break
        if head is None:
            return {"state": "NODATA", "why": "沒有 HEADER 列", "frame": None, "n": 0}
        columns, flags = _names(head)

    width = len(columns)
    writer = None
    batch: list[list] = []
    n = 0
    peak = 0
    extra = False

    def flush() -> None:
        nonlocal writer, batch, n, peak
        if not batch:
            return
        peak = max(peak, len(batch))
        data = {
            columns[i]: pa.array([row[i] for row in batch], type=pa.string())
            for i in range(width)
        }
        table = pa.table(data)
        if writer is None:
            writer = pq.ParquetWriter(str(path), table.schema)
        writer.write_table(table)
        n += len(batch)
        batch = []

    for row in it:
        cells, has_extra = _align(list(row), width)
        extra = extra or has_extra
        batch.append(cells)
        if len(batch) >= chunk:
            flush()
    flush()
    if writer is not None:
        writer.close()
    elif n == 0:
        pq.write_table(pa.table({c: pa.array([], type=pa.string()) for c in columns}), path)
    if extra:
        flags.append("EXTRA_CELLS")

    spilled = n > mem_rows
    if spilled:
        frame = duckdb.sql(
            "SELECT * FROM read_parquet(?) LIMIT ?",
            params=[str(path), preview],
        ).df()
    else:
        frame = pd.read_parquet(path)
        frame = frame.astype("object").where(frame.notna(), None)
    return {
        "state": "OK",
        "columns": columns,
        "flags": flags,
        "frame": frame,
        "n": n,
        "spilled": spilled,
        "peak_batch": peak,
        "path": str(path),
        "preview": preview if spilled else n,
    }


def _split(blocks: list) -> tuple[list, list]:
    """Vertical cut first. Text stays left. Tables stay right, top to bottom."""
    xs = [float(b.get("x") or 0) for b in blocks]
    cut = (min(xs) + max(xs)) / 2 if xs else 0
    left, right = [], []
    for block in blocks:
        side = block.get("side")
        if side == "right" or (side != "left" and float(block.get("x") or 0) >= cut and block.get("kind") == "table"):
            right.append(block)
        else:
            left.append(block)
    left.sort(key=lambda b: float(b.get("y") or 0))
    right.sort(key=lambda b: float(b.get("y") or 0))
    return left, right


def _restore_left(blocks: list) -> dict:
    parts, how = [], []
    for block in blocks:
        src = str(block.get("text") or "")
        candidate = ENG107.restore(src)["text"]
        kept, state = choose_text(src, candidate)
        parts.append(kept)
        how.append(state)
    text = "\n".join(p for p in parts if p)
    return {"text": text, "how": how}


def summary_of(text: str, ratio: float) -> dict | None:
    """No summary until the restored page still covers the source."""
    if ratio + 1e-12 < COVER_MIN or not text:
        return None
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    title = lines[0] if lines else "未提及"
    body = lines[1:]
    points = [(body[i] if i < len(body) else "未提及") for i in range(4)]
    grounded = all((p == "未提及") or (p in text) for p in points) and (title in text)
    quoted = sum(p != "未提及" for p in points)
    state = "GREEN" if grounded and quoted == 4 and title != "未提及" else "YELLOW"
    return {"title": title, "points": points, "state": state, "n": 4}


def run(params: dict | None) -> dict:
    if not isinstance(params, dict) or not params.get("temp_dir"):
        return {"state": "NODATA", "why": "缺輸入參數 temp_dir", "params": list(PARAMS)}
    blocks = list(params.get("blocks") or [])
    tables = list(params.get("tables") or [])
    if not blocks and not tables and params.get("rows") is None:
        return {"state": "NODATA", "why": "缺 rows、tables 或 blocks", "params": list(PARAMS)}

    temp = Path(params["temp_dir"])
    temp.mkdir(parents=True, exist_ok=True)
    left_blocks, right_blocks = _split(blocks) if blocks else ([], [])
    left = _restore_left(left_blocks) if left_blocks else {"text": "", "how": []}
    if params.get("rows") is not None:
        tables = [{"rows": params["rows"], "y": 0}] + tables
    for block in right_blocks:
        if block.get("kind") == "table":
            tables.append(block)

    frames = []
    db_path = Path(params["temp_dir"]) / "tables.duckdb"
    con = duckdb.connect(str(db_path))
    try:
        for i, table in enumerate(tables):
            item = dict(params)
            item["stem"] = f"t{i}"
            item["temp_dir"] = params["temp_dir"]
            got = header_frame(table.get("rows") if isinstance(table, dict) else table, item)
            frames.append(got)
            if got.get("path"):
                con.execute(f"CREATE OR REPLACE TABLE t{i} AS SELECT * FROM read_parquet(?)", [got["path"]])
    finally:
        con.close()

    source = "\n".join(str(b.get("text") or "") for b in left_blocks)
    for table in tables:
        rows = table.get("rows") if isinstance(table, dict) else table
        if isinstance(rows, list):
            source += "\n" + "\n".join("\t".join(str(c or "") for c in row) for row in rows)
    restored_cells = left["text"]
    for got in frames:
        if got.get("frame") is not None and not got.get("spilled"):
            restored_cells += "\n" + "\n".join(
                "\t".join("" if v is None else str(v) for v in row)
                for row in got["frame"].itertuples(index=False))
            restored_cells += "\n" + "\t".join(got.get("columns") or [])
    ratio = cover(source, restored_cells) if source.strip() else 1.0
    complete = ratio + 1e-12 >= COVER_MIN
    summary = summary_of(left["text"], ratio)

    page = Path(params["temp_dir"]) / "page.html"
    right_html = []
    for i, got in enumerate(frames):
        view = got.get("frame")
        body = "" if view is None else view.to_html(index=False)
        right_html.append(f"<h3>t{i} · {got.get('n', 0)} 列</h3>{body}")
    page.write_text(
        "<div style='display:flex;gap:24px'>"
        f"<pre id='left'>{html.escape(left['text'])}</pre>"
        f"<div id='right'>{''.join(right_html)}</div></div>",
        encoding="utf-8")
    return {
        "state": "REPAIRED" if complete else "PARTIAL",
        "left": left,
        "frames": [{k: v for k, v in g.items() if k != "frame"} | {"columns": g.get("columns"), "n": g.get("n"), "spilled": g.get("spilled")} for g in frames],
        "frame_objects": frames,
        "cover": ratio,
        "summary": summary,
        "db": str(db_path),
        "html": str(page),
        "params": {k: params.get(k) for k in PARAMS},
    }


def selftest() -> int:
    import tempfile
    fails = []

    def chk(name, ok):
        print(("  [OK] " if ok else "  [FAIL] ") + name)
        if not ok:
            fails.append(name)

    chk("缺參數", run({})["state"] == "NODATA")
    chk("修復退回", choose_text("營收100", "營收")[1] == "ROLLBACK")

    with tempfile.TemporaryDirectory() as td:
        small = header_frame(
            [["科目", "2025", "2025", ""], ["營收", "100", "80", "1"], ["毛利", "40", "30"]],
            {"temp_dir": td, "header": 0, "chunk": 1, "mem_rows": 50, "stem": "small"},
        )
        frame = small["frame"]
        chk("HEADER 轉欄", list(frame.columns) == ["科目", "2025", "2025_2", "col_3"])
        chk("值來自 TEMP", frame.iloc[0, 1] == "100" and Path(small["path"]).is_file())
        chk("短列不丟", frame.iloc[1, 3] is None and "HEADER_DEDUPED" in small["flags"])

        live = {"held": 0, "peak": 0}

        def gen():
            yield ["科目", "值"]
            for i in range(5000):
                live["held"] += 1
                live["peak"] = max(live["peak"], live["held"])
                yield ["營收", str(i)]
                live["held"] -= 1

        big = header_frame(gen(), {"temp_dir": td, "chunk": 200, "mem_rows": 1000, "preview": 20, "stem": "big"})
        n_db = duckdb.sql("SELECT count(*) FROM read_parquet(?)", params=[big["path"]]).fetchone()[0]
        chk("溢寫不進記憶體", big["spilled"] and big["n"] == 5000 and n_db == 5000 and len(big["frame"]) == 20)
        chk("批次不高過 chunk", big["peak_batch"] <= 200 and live["peak"] == 1)

        page = run({
            "temp_dir": str(Path(td) / "page"),
            "header": 0,
            "chunk": 10,
            "mem_rows": 100,
            "preview": 5,
            "blocks": [
                {"kind": "text", "x": 40, "y": 10, "text": "台積電 2330"},
                {"kind": "text", "x": 40, "y": 40, "text": "我們維持\n買進。"},
                {"kind": "text", "x": 40, "y": 70, "text": "目標價\n１２７５。"},
                {"kind": "text", "x": 40, "y": 100, "text": "營收成長來自先進製程。"},
                {"kind": "text", "x": 40, "y": 130, "text": "毛利率持穩。"},
                {"kind": "text", "x": 40, "y": 160, "text": "資本支出高於去年。"},
                {"kind": "table", "x": 320, "y": 40, "rows": [["科目", "2025"], ["營收", "100"], ["毛利", "40"]]},
                {"kind": "table", "x": 320, "y": 180, "rows": [["科目", "2026"], ["營收", "120"], ["毛利", "50"]]},
            ],
        })
        left = page["left"]["text"]
        html_txt = Path(page["html"]).read_text(encoding="utf-8")
        db = duckdb.connect(page["db"])
        counts = [db.execute(f"SELECT count(*) FROM t{i}").fetchone()[0] for i in range(2)]
        db.close()
        summary = page["summary"] or {}
        chk("文左表右", "我們維持買進。" in left and "1275" in left and "id='left'" in html_txt and "id='right'" in html_txt)
        chk("右表入庫", counts == [2, 2] and page["frame_objects"][0]["columns"] == ["科目", "2025"])
        chk("全文還在", "資本支出高於去年。" in left and page["cover"] >= COVER_MIN)
        chk("一標題四點", summary.get("title") == "台積電 2330" and summary.get("n") == 4
            and summary["points"][0] == "我們維持買進。" and summary["points"][3] == "毛利率持穩。"
            and all(p in left for p in summary["points"]))
        chk("不完整不摘要", summary_of("台積電 2330\n我們維持買進。", 0.5) is None)

    print(f"  [計] {12 - len(fails)} 檢 OK · FAIL {len(fails)}")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(selftest())
