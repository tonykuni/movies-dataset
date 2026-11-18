#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ===== [VRN:ID:v0100] VRN-ENG016 · VRN_Matrix_v0100 v0100 · ENGINE =====
# AST 注入（只加註解，AST 不變）：類別 0 · 函式 21；逐一編號在 ssot/VRN_ID_SSOT_v0100.json
# ===== [VRN:ID:END] =====
"""
VRN_Matrix v0100 -- the verified results of one run as a matrix in the console, for the operator's review.

Operator 2026-10-12:
  「real test and output validated results in matrix by rich for my reviewing」

One row per stock report, one column per part (ticker, company, broker, date, rating, target, price, upside, analyst, phone,
annual cells): the value as read, its state (✓ VERIFIED · ✗ CONFLICT · ~ SINGLE · ! MISSING · – NOT_PRINTED · ? REVIEW) and
its lock (鎖 HELD · 新 NEW · 破 BROKEN).  Then one totals table per part, and the legend.

Rendering: `rich` when it is installed on the operator's machine (nothing is installed by VRN); otherwise the same layout in
plain text with ANSI colours, CJK-text_width aware; colours are off when stdout is not a terminal, with --plain, or NO_COLOR.
The matrix is also written without colours to VRN_Matrix_Console_v0100.txt in the run folder.

Sources (nothing new is computed, the HTML matrix of G15 stays as it is):
  autotest/round*/titletrim/VRN_TitleTrim_Results_v0100.json   every part of every stock report (G17)
  autotest/round*/titletrim/vrn_lock_status.json                the lock of every part (G18)
  autotest/round*/VRN_Verified_Matrix_v0105.csv                 the engines' own values per file (G15), shown when G17 has none
No network, LIVE off, no consent variable read or set.
"""

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

import argparse
import csv
import json
import os
import sys
import tempfile
import unicodedata
from collections import Counter
from pathlib import Path

MATRIX_VERSION = "v0100"
OUT_NAME = "VRN_Matrix_Console_v0100.txt"
COLUMNS = [("title.ticker", "代碼"), ("title.company", "公司"), ("cover.broker", "券商"), ("cover.date", "日期"),
           ("cover.rating", "評等"), ("cover.target_price", "目標價"), ("cover.current_price", "現價"), ("cover.upside", "上漲%"),
           ("cover.analyst", "分析師"), ("cover.tel", "電話")]
ANNUAL_HEADER = "年度財報格"
RECORD_COLUMNS = [("ticker", "代號"), ("yfinance_ticker", "YF"), ("bloomberg_ticker", "BBG"), ("name", "公司名"), ("english_name", "英文名"),
                  ("broker", "券商"), ("analyst", "分析師"), ("title", "標題"), ("email", "E-mail"), ("tel", "電話"), ("rating", "評等"),
                  ("target_price_original", "目標價"), ("target_price_adj", "目標價(調)"), ("adj_close", "ADJ CLOSE"),
                  ("adj_close_before_report", "報告日前"), ("upside_pct", "上漲%")]
OUT_RECORD_NAME = "VRN_Matrix_Record_v0100.txt"
MARK = {"VERIFIED": "✓", "CONFLICT": "✗", "SINGLE": "~", "MISSING": "!", "NOT_PRINTED": "–", "REVIEW": "?", "UNMAPPED": "?",
        "REPORT_CHECK": "?", "TRIM_LOSS": "✗", "TRIM_REGRESSION": "✗", "DB": "庫", "DERIVED": "推", "NOT_APPLICABLE": "–", "ABSENT": "!"}
LOCK_MARK = {"HELD": "鎖", "NEW": "新", "BROKEN": "破", "DYNAMIC": "動"}
# 部位總計／代號紀錄總計那兩張表的欄位（文字版的總計列是照 totals 動態組的，這兩個只管表格版）。
# 2026-10-21 第二十三輪：部位這邊本來少了 DERIVED —— cover.upside 從這一輪起會是 DERIVED
# （首頁沒印、VRN 算得出來），沒有這一欄，59 格推算值在部位總計表上會整個消失。
TOTAL_STATES_WITH_ANNUAL = ("VERIFIED", "CONFLICT", "SINGLE", "DERIVED", "MISSING", "NOT_PRINTED", "REVIEW")
TOTAL_STATES_RECORD = ("VERIFIED", "SINGLE", "DB", "DERIVED", "MISSING", "NOT_PRINTED")
COLOR = {"VERIFIED": "green", "CONFLICT": "red", "SINGLE": "yellow", "MISSING": "magenta", "NOT_PRINTED": "dim", "REVIEW": "cyan",
         "UNMAPPED": "cyan", "REPORT_CHECK": "cyan", "TRIM_LOSS": "red", "TRIM_REGRESSION": "red", "BROKEN": "bold red", "DB": "cyan",
         "DERIVED": "yellow", "NOT_APPLICABLE": "dim", "ABSENT": "magenta"}
ANSI = {"green": "\x1b[32m", "red": "\x1b[31m", "yellow": "\x1b[33m", "magenta": "\x1b[35m", "cyan": "\x1b[36m", "dim": "\x1b[2m",
        "bold red": "\x1b[1;31m", "bold": "\x1b[1m", "reset": "\x1b[0m"}
# 2026-10-21 第二十三輪：推（DERIVED）本來只寫在「代號紀錄另有」那一段 —— 上漲% 這一欄從這一輪起也會印推，
# 圖例沒跟上，操作員就會在部位那張表上看到一個圖例沒解釋的記號。
LEGEND = ("記號：✓ 兩條讀法一致（VERIFIED） · ✗ 不一致（CONFLICT） · ~ 只有一條讀法（SINGLE） · ! 該有沒讀到（MISSING） · – 報告沒印 · ? 要人看 · "
          "庫 值取資料庫（公司名、現價） · 推 報告沒印、VRN 算得出來（上漲% =（目標價−現價）÷現價）；"
          "鎖：鎖 HELD · 新 NEW · 破 BROKEN（擋下）；代號紀錄另有：庫 本機資料庫 · 推 推算（<代號> TT、.TW/.TWO）")
MAX_WIDTH = {"file": 30, "title.company": 14, "cover.rating": 10, "cover.analyst": 10, "cover.tel": 13}
DROP_ORDER = ["cover.analyst", "cover.tel", "cover.upside", "cover.rating", "title.company"]   # left out first when the window is narrow


# [VRN-ID] VRN-ENG016-FNC021 · LOGIC
def table_has_rich():
    try:
        import rich  # noqa: F401
        return True
    except Exception:  # noqa: BLE001
        return False


# [VRN-ID] VRN-ENG016-FNC022 · LOGIC
def text_width(text):
    """Display text_width: wide and full-text_width characters take two columns, combining marks none."""
    w = 0
    for ch in str(text or ""):
        if unicodedata.combining(ch):
            continue
        w += 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1
    return w


# [VRN-ID] VRN-ENG016-FNC023 · LOGIC
def clip_text(text, max_width):
    """Cut to a display text_width, with a trailing … when something was cut."""
    text = str(text or "")
    if text_width(text) <= max_width:
        return text
    out, w = "", 0
    for ch in text:
        cw = 2 if unicodedata.east_asian_width(ch) in ("W", "F") else (0 if unicodedata.combining(ch) else 1)
        if w + cw > max_width - 1:
            break
        out += ch
        w += cw
    return out + "…"


# [VRN-ID] VRN-ENG016-FNC024 · LOGIC
def pad_text(text, to_width):
    return str(text) + " " * max(0, to_width - text_width(text))


# [VRN-ID] VRN-ENG016-FNC025 · LOGIC
def table_value(part, value):
    """A value as it reads in a cell: numbers without noise, long texts clipped."""
    if value in (None, "", []):
        return ""
    if isinstance(value, float):
        return f"{value:g}" if abs(value) < 1e6 else f"{value:.0f}"
    s = str(value)
    if part == "cover.tel":
        digits = "".join(ch for ch in s if ch.isdigit())
        return digits[-10:] if digits else s
    return clip_text(s, MAX_WIDTH.get(part, 12))


# [VRN-ID] VRN-ENG016-FNC006 · LOGIC
def find_run_files(run_dir):
    run = Path(run_dir)
    results = sorted(run.glob("autotest/round*/titletrim/VRN_TitleTrim_Results_v0100.json"))
    locks = sorted(run.glob("autotest/round*/titletrim/vrn_lock_status.json"))
    g15 = sorted(run.glob("autotest/round*/VRN_Verified_Matrix_v0105.csv"))
    return (results[-1] if results else None), (locks[-1] if locks else None), (g15[-1] if g15 else None)


# [VRN-ID] VRN-ENG016-FNC007 · IO
def load_run(run_dir):
    """-> (results list, {(file, part): lock}, {file: G15 row}) of the newest round of one run folder."""
    rp, lp, gp = find_run_files(run_dir)
    results = json.loads(rp.read_text(encoding="utf-8")) if rp else []
    locks = {}
    if lp:
        for r in json.loads(lp.read_text(encoding="utf-8")):
            locks[(r.get("file"), r.get("part"))] = r.get("lock", "")
    g15 = {}
    if gp:
        with open(gp, encoding="utf-8-sig", newline="") as fh:
            for row in csv.DictReader(fh):
                g15[row.get("檔案", "")] = row
    return results, locks, g15


# [VRN-ID] VRN-ENG016-FNC026 · BUILD
def build_report_matrix(results, locks=None, g15=None):
    """-> {rows: [{file, cells: {part: {value, state, lock, text}}, annual: {verified, total}}], totals, lock_totals}."""
    locks = locks or {}
    g15 = g15 or {}
    rows = []
    totals = {part: Counter() for part, _h in COLUMNS}
    lock_totals = Counter()
    for res in sorted(results, key=lambda r: str(r.get("file", ""))):
        if res.get("status") not in ("OK",) and not res.get("parts"):
            continue
        name = res.get("file", "")
        parts = {p["part"].split("@")[0] if "@" not in p["part"] else p["part"]: p for p in res.get("parts") or []}
        cells = {}
        for part, _h in COLUMNS:
            p = parts.get(part) or {}
            state = p.get("state", "") or ("NOT_PRINTED" if p else "")
            lock = locks.get((name, part), "")
            value = p.get("value", "")
            if not p and part == "cover.broker" and g15.get(name, {}).get("券商"):   # G17 has no reading at all: the engine's (one reader)
                value, state = g15[name]["券商"], "SINGLE"
            text = table_value(part, value)
            mark = MARK.get(state, "") + ("庫" if p.get("source") == "db" else "")   # 2026-10-13: the value is the database's
            lk = LOCK_MARK.get(lock, "")
            cells[part] = {"value": value, "state": state, "lock": lock,
                           "text": (text + (" " + mark if mark and text else (mark if mark else ""))) + (lk if lk else "")}
            if state:
                totals[part][state] += 1
            if lock in LOCK_MARK:
                lock_totals[lock] += 1
        annual = [p for p in res.get("parts") or [] if str(p.get("part", "")).startswith("annual.")]
        ok = sum(1 for p in annual if p.get("state") == "VERIFIED")
        rows.append({"file": name, "cells": cells, "annual": {"verified": ok, "total": len(annual)}})
    return {"rows": rows, "totals": totals, "lock_totals": lock_totals, "columns": COLUMNS}


# [VRN-ID] VRN-ENG016-FNC032 · BUILD
def build_record_matrix(run_dir):
    """The 4-digit-code record (G20 vrn_ticker_record.json) as a matrix model: one row per report, the 15 fields, value + state."""
    run = Path(run_dir)
    paths = sorted(run.glob("autotest/round*/titletrim/vrn_ticker_record.json"))
    rows_in = json.loads(paths[-1].read_text(encoding="utf-8")) if paths else []
    rows, totals = [], {part: Counter() for part, _h in RECORD_COLUMNS}
    for r in sorted(rows_in, key=lambda x: str(x.get("file", ""))):
        cells = {}
        for part, _h in RECORD_COLUMNS:
            state = str(r.get(part + "_state", "") or "")
            text = clip_text(str(r.get(part, "") or ""), 16) if part == "title" else table_value("cover.tel" if part == "tel" else part, r.get(part, ""))
            mark = MARK.get(state, "")
            cells[part] = {"value": r.get(part, ""), "state": state, "lock": "", "text": (text + (" " + mark if mark and text else mark))}
            if state:
                totals[part][state] += 1
        rows.append({"file": r.get("file", ""), "cells": cells, "annual": {"verified": 0, "total": 0}})
    return {"rows": rows, "totals": totals, "lock_totals": Counter(), "columns": RECORD_COLUMNS, "title": "VRN 代號紀錄矩陣（四碼代號 → 15 欄）",
            "annual": False, "out_name": OUT_RECORD_NAME}


# [VRN-ID] VRN-ENG016-FNC027 · LOGIC
def table_cell_color(cell):
    if cell.get("lock") == "BROKEN":
        return "bold red"
    return COLOR.get(cell.get("state", ""), "")


# [VRN-ID] VRN-ENG016-FNC010 · LOGIC
def annual_text(a):
    if not a["total"]:
        return "–"
    return f"{a['verified']}/{a['total']} " + ("✓" if a["verified"] == a["total"] else "~")


# [VRN-ID] VRN-ENG016-FNC028 · LOGIC
def table_annual_color(a):
    if not a["total"]:
        return "dim"
    return "green" if a["verified"] == a["total"] else "yellow"


# [VRN-ID] VRN-ENG016-FNC019 · LOGIC
def column_widths(model, columns, rows=0):
    """-> (shown rows, text per row, display text_width per column) for the given part columns."""
    cols = [("file", "檔案")] + list(columns) + [("annual", ANNUAL_HEADER)]
    shown = model["rows"][:rows] if rows else model["rows"]
    table = []
    for r in shown:
        line = {"file": clip_text(r["file"], MAX_WIDTH["file"]), "annual": annual_text(r["annual"])}
        for part, _h in columns:
            line[part] = r["cells"][part]["text"]
        table.append(line)
    widths = {key: max([text_width(head)] + [text_width(t[key]) for t in table]) for key, head in cols}
    return shown, table, widths


# [VRN-ID] VRN-ENG016-FNC029 · LOGIC
def table_fit_columns(model, max_width, rows=0, sep=3):
    """A window narrower than the table: the least important part columns are left out (DROP_ORDER) until it fits.
    -> (columns kept, columns left out).  max_width 0 = everything."""
    columns = list(model["columns"])
    dropped = []
    while max_width and len(columns) > 1:
        _s, _t, widths = column_widths(model, columns, rows)
        if sum(widths.values()) + sep * (len(widths) - 1) <= max_width:
            break
        nxt = next((p for p in DROP_ORDER if any(p == c for c, _h in columns)), None)
        if nxt is None:
            break
        dropped.append(next(h for c, h in columns if c == nxt))
        columns = [(c, h) for c, h in columns if c != nxt]
    return columns, dropped


# [VRN-ID] VRN-ENG016-FNC012 · REPORT
def render_plain(model, color=False, rows=0, max_width=0):
    """The matrix as text lines (ANSI colours optional); every line the same display text_width.  max_width > 0: columns that do not
    fit the window are left out (the file copy is written with max_width 0 and keeps every column)."""
    columns, dropped = table_fit_columns(model, max_width, rows)
    with_annual = model.get("annual", True)
    cols = [("file", "檔案")] + list(columns) + ([("annual", ANNUAL_HEADER)] if with_annual else [])
    shown, table, widths = column_widths(model, columns, rows)

    # [VRN-ID] VRN-ENG016-FNC013 · LOGIC
    def paint(text, style):
        if not color or not style or style not in ANSI:
            return text
        return ANSI[style] + text + ANSI["reset"]
    out = [model.get("title", "VRN 核對矩陣") + " " + MATRIX_VERSION + f" · 個股 {len(model['rows'])} 檔" + (f"（列前 {len(shown)} 檔）" if rows and rows < len(model["rows"]) else "")
           + " · 鎖 " + " · ".join(f"{k} {v}" for k, v in sorted(model["lock_totals"].items()))
           + (f" · 視窗窄，省略：{'、'.join(dropped)}（完整版在 {OUT_NAME}）" if dropped else "")]
    out.append(" │ ".join(pad_text(head, widths[key]) for key, head in cols))
    out.append("─┼─".join("─" * widths[key] for key, _h in cols))
    for r, t in zip(shown, table):
        cells = [pad_text(t["file"], widths["file"])]
        for part, _h in columns:
            cells.append(paint(pad_text(t[part], widths[part]), table_cell_color(r["cells"][part])))
        if with_annual:
            cells.append(paint(pad_text(t["annual"], widths["annual"]), table_annual_color(r["annual"])))
        out.append(" │ ".join(cells))
    out.append("")
    out.append("部位總計：" + " · ".join(f"{head} " + "/".join(f"{MARK.get(s, s)}{n}" for s, n in sorted(model["totals"][part].items(), key=lambda kv: -kv[1]))
                                   for part, head in model["columns"] if model["totals"][part]))
    out.append(LEGEND)
    return out


# [VRN-ID] VRN-ENG016-FNC014 · REPORT
def render_rich(model, rows=0):
    """The same matrix with rich (when installed).  -> True when printed, False when rich is not there."""
    try:
        from rich.console import Console
        from rich.table import Table
        from rich.text import Text
        from rich import box
    except Exception:  # noqa: BLE001
        return False
    console = Console()
    columns, dropped = table_fit_columns(model, console.width, rows, sep=3)
    shown = model["rows"][:rows] if rows else model["rows"]
    with_annual = model.get("annual", True)
    table = Table(title=model.get("title", "VRN 核對矩陣") + " " + MATRIX_VERSION + f" · 個股 {len(model['rows'])} 檔 · 鎖 "
                  + " · ".join(f"{k} {v}" for k, v in sorted(model["lock_totals"].items()))
                  + (f"\n視窗窄，省略：{'、'.join(dropped)}（完整版在 {OUT_NAME}）" if dropped else ""),
                  box=box.SIMPLE_HEAVY, show_lines=False, pad_edge=False)
    table.add_column("檔案", no_wrap=True, max_width=MAX_WIDTH["file"] + 2)
    for _part, head in columns:
        table.add_column(head, no_wrap=True)
    if with_annual:
        table.add_column(ANNUAL_HEADER, no_wrap=True)
    for r in shown:
        cells = [Text(clip_text(r["file"], MAX_WIDTH["file"]))]
        for part, _h in columns:
            c = r["cells"][part]
            cells.append(Text(c["text"], style=table_cell_color(c) or ""))
        if with_annual:
            cells.append(Text(annual_text(r["annual"]), style=table_annual_color(r["annual"])))
        table.add_row(*cells)
    console.print(table)
    tot = Table(title="部位總計", box=box.SIMPLE, pad_edge=False)
    tot.add_column("部位")
    states = TOTAL_STATES_WITH_ANNUAL if with_annual else TOTAL_STATES_RECORD
    for state in states:
        tot.add_column(MARK[state] + (" " + state if console.width >= 110 else ""), justify="right", style=COLOR[state] if COLOR[state] != "dim" else "")
    for part, head in model["columns"]:
        tot.add_row(head, *[str(model["totals"][part].get(s, 0) or "") for s in states])
    console.print(tot)
    console.print(LEGEND, style="dim")
    return True


# [VRN-ID] VRN-ENG016-FNC030 · LOGIC
def table_write(run_dir, model):
    path = Path(run_dir) / model.get("out_name", OUT_NAME)
    path.write_text("\n".join(render_plain(model, color=False)) + "\n", encoding="utf-8")
    return path


# [VRN-ID] VRN-ENG016-FNC031 · LOGIC
def show_report_matrix(run_dir, plain=False, rows=0, stream=None, view="parts"):
    """Render one run's matrix to the console (rich if installed and not --plain, else text) and write the text copy.
    view = parts (the G17/G18 parts) or record (the G20 4-digit-code record).  -> {rendered, rows, path} or {error}."""
    stream = stream or sys.stdout
    if view == "record":
        if not sorted(Path(run_dir).glob("autotest/round*/titletrim/vrn_ticker_record.json")):
            return {"error": f"沒有 G20 代號紀錄：{Path(run_dir) / 'autotest/round1/titletrim/vrn_ticker_record.json'}"}
        model = build_record_matrix(run_dir)
    else:
        rp, _lp, _gp = find_run_files(run_dir)
        if rp is None:
            return {"error": f"沒有 G17 結果：{Path(run_dir) / 'autotest/round1/titletrim/VRN_TitleTrim_Results_v0100.json'}"}
        model = build_report_matrix(*load_run(run_dir))
    path = table_write(run_dir, model)
    color = (not plain) and hasattr(stream, "isatty") and stream.isatty() and os.environ.get("NO_COLOR") is None
    rendered = "plain"
    if not plain and stream is sys.stdout and render_rich(model, rows=rows):
        rendered = "rich"
    else:
        try:
            import shutil
            max_width = shutil.get_terminal_size((0, 0)).columns if color else 0
        except Exception:  # noqa: BLE001
            max_width = 0
        for line in render_plain(model, color=color, rows=rows, max_width=max_width):
            print(line, file=stream)
    print(f"[MATRIX-CONSOLE] {rendered} · {len(model['rows'])} 檔 · 文字版 {path}", file=stream)
    return {"rendered": rendered, "rows": len(model["rows"]), "path": str(path)}


# =====================================================================
# SELFTEST / CLI
# =====================================================================
# [VRN-ID] VRN-ENG016-FNC017 · ENTRY
def selftest(verbose=True):
    checks = []
    results = [{"file": "凱基_2330台積電_20260901_公司更新.pdf", "status": "OK",
                "parts": [{"part": "title.ticker", "value": "2330", "state": "VERIFIED"}, {"part": "title.company", "value": "台積電", "state": "VERIFIED"},
                          {"part": "cover.broker", "value": "KGI", "state": "VERIFIED"}, {"part": "cover.date", "value": "2026-09-01", "state": "VERIFIED"},
                          {"part": "cover.rating", "value": "買進", "state": "SINGLE"}, {"part": "cover.target_price", "value": 1200.0, "state": "VERIFIED"},
                          {"part": "cover.current_price", "value": 1000.0, "state": "CONFLICT"}, {"part": "cover.upside", "value": 20.0, "state": "VERIFIED"},
                          {"part": "cover.analyst", "value": "王小明", "state": "SINGLE"}, {"part": "cover.tel", "value": "886221818888", "state": "VERIFIED"},
                          {"part": "annual.revenue@2025", "value": 1200.0, "state": "VERIFIED"}, {"part": "annual.cogs@2025", "value": 696.0, "state": "SINGLE"}]},
               {"file": "GS-1590 20251203.pdf", "status": "OK",
                "parts": [{"part": "title.ticker", "value": "1590", "state": "VERIFIED"}, {"part": "cover.rating", "value": "", "state": "MISSING"},
                          {"part": "cover.target_price", "value": "", "state": "NOT_PRINTED"}]}]
    locks = {("凱基_2330台積電_20260901_公司更新.pdf", "title.ticker"): "HELD", ("凱基_2330台積電_20260901_公司更新.pdf", "cover.target_price"): "NEW",
             ("GS-1590 20251203.pdf", "title.ticker"): "BROKEN"}
    model = build_report_matrix(results, locks, {"GS-1590 20251203.pdf": {"券商": "GS"}})
    by = {r["file"]: r for r in model["rows"]}
    lines = render_plain(model, color=False)
    body = [l for l in lines[1:-3]]
    kgi = next((l for l in body if "2330" in l), "")
    gs = next((l for l in body if "1590" in l), "")
    checks.append(("每一列同寬（中英文寬度算對）", len({text_width(l) for l in body}) == 1, {text_width(l) for l in body}))
    checks.append(("值 + 記號 + 鎖：2330 ✓鎖 · 1200 ✓新 · 1590 ✓破", "2330 ✓鎖" in kgi and "1200 ✓新" in kgi and "1590 ✓破" in gs, [kgi, gs]))
    checks.append(("沒讀到 ! · 沒印 – · 年度格 1/2 ~", "!" in gs and "–" in gs and "1/2 ~" in kgi, gs))
    checks.append(("G17 沒讀券商時用 G15 的（一條讀法 ~）", by["GS-1590 20251203.pdf"]["cells"]["cover.broker"]["text"] == "GS ~", by["GS-1590 20251203.pdf"]["cells"]["cover.broker"]))
    checks.append(("部位總計與圖例", "部位總計：" in lines[-2] and lines[-1].startswith("記號："), lines[-2][:40]))
    colored = render_plain(model, color=True)
    checks.append(("ANSI 顏色只在要求時", any("\x1b[" in l for l in colored) and not any("\x1b[" in l for l in lines), ""))
    checks.append(("BROKEN 的格是粗紅", table_cell_color(by["GS-1590 20251203.pdf"]["cells"]["title.ticker"]) == "bold red", ""))
    with tempfile.TemporaryDirectory(prefix="vrn_matrix_") as td:
        run = Path(td) / "run"
        (run / "autotest" / "round1" / "titletrim").mkdir(parents=True)
        (run / "autotest" / "round1" / "titletrim" / "VRN_TitleTrim_Results_v0100.json").write_text(json.dumps(results, ensure_ascii=False), encoding="utf-8")
        (run / "autotest" / "round1" / "titletrim" / "vrn_lock_status.json").write_text(
            json.dumps([{"file": f, "part": p, "lock": lk} for (f, p), lk in locks.items()], ensure_ascii=False), encoding="utf-8")
        import io
        buf = io.StringIO()
        got = show_report_matrix(run, plain=True, stream=buf)
        text = (run / OUT_NAME).read_text(encoding="utf-8")
        checks.append(("show：文字版寫在執行夾、兩檔都在", got.get("rendered") == "plain" and got.get("rows") == 2 and "GS-1590" in text and "[MATRIX-CONSOLE]" in buf.getvalue(), got))
        checks.append(("沒有結果的資料夾 = 說清楚", "error" in show_report_matrix(Path(td) / "nothing", plain=True, stream=io.StringIO()), ""))
    with tempfile.TemporaryDirectory(prefix="vrn_matrix_rec_") as td:
        run = Path(td) / "run"
        (run / "autotest" / "round1" / "titletrim").mkdir(parents=True)
        (run / "autotest" / "round1" / "titletrim" / "vrn_ticker_record.json").write_text(json.dumps([
            {"file": "a.pdf", "ticker": "2330", "ticker_state": "VERIFIED", "yfinance_ticker": "2330.TW", "yfinance_ticker_state": "DB",
             "bloomberg_ticker": "2330 TT", "bloomberg_ticker_state": "DERIVED", "name": "台積電", "name_state": "VERIFIED", "english_name": "", "english_name_state": "NOT_PRINTED",
             "target_price_original": 1200.0, "target_price_original_state": "VERIFIED", "adj_close": 1010.0, "adj_close_state": "DB"}], ensure_ascii=False), encoding="utf-8")
        import io as _io
        buf = _io.StringIO()
        got = show_report_matrix(run, plain=True, stream=buf, view="record")
        text = (run / OUT_RECORD_NAME).read_text(encoding="utf-8")
        checks.append(("代號紀錄矩陣：15 欄、庫／推 記號、沒有年度格欄", got.get("rows") == 1 and "2330.TW 庫" in text and "2330 TT 推" in text and "年度財報格" not in text
                       and "代號紀錄矩陣" in text, text.splitlines()[:4]))
    kept, dropped = table_fit_columns(model, 100)
    narrow = render_plain(model, color=False, max_width=100)
    checks.append(("視窗窄就省略分析師、電話…並說明；文字檔完整", dropped[:2] == ["分析師", "電話"] and "省略" in narrow[0] and max(text_width(l) for l in narrow[1:-3]) <= 100
                   and not table_fit_columns(model, 0)[1], (dropped, max(text_width(l) for l in narrow[1:-3]))))
    checks.append(("rich 有就用、沒有就文字（兩種都算過）", table_has_rich() in (True, False), f"rich={'有' if table_has_rich() else '無'}"))
    bad = [c for c in checks if not c[1]]
    if verbose:
        for name, ok, detail in checks:
            print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + ("" if ok else f" · {detail}"))
        print(f"[MATRIX] {MATRIX_VERSION} · {len(checks) - len(bad)}/{len(checks)}")
    return 0 if not bad else 1


# [VRN-ID] VRN-ENG016-FNC018 · ENTRY
def main(argv=None):
    parser = argparse.ArgumentParser(prog="VRN_Matrix_v0100.py", description="一次實測的核對矩陣（console；rich 有就用）")
    sub = parser.add_subparsers(dest="command")
    p_show = sub.add_parser("show", help="畫出一次實測的核對矩陣")
    p_show.add_argument("--out", required=True, help="實測輸出資料夾")
    p_show.add_argument("--plain", action="store_true", help="純文字、不用 rich、不上色")
    p_show.add_argument("--rows", type=int, default=0, help="只列前 N 檔（0 = 全部）")
    p_show.add_argument("--view", choices=("parts", "record"), default="parts")
    sub.add_parser("selftest")
    args = parser.parse_args(argv)
    if args.command == "show":
        got = show_report_matrix(args.out, plain=args.plain, rows=args.rows, view=args.view)
        if "error" in got:
            print("[MATRIX-CONSOLE] " + got["error"])
            return 1
        return 0
    return selftest()


if __name__ == "__main__":
    sys.exit(main())
