# PROMOTED by UNIT03 v0113 20260804_175530 from Chart Library Builder candidate (SHA 2AE164B5082B2113E12C4D1BCD8D73E97C66010F602E01F4A81D8E4B53689EEC)
# Eight-site visual-lock repair 0.4 -> 0.75 per v0111R2 adjudication + v0112 guarded trial (all gates PASS).
# Canonical via_autoplot_engine_v001.py is unaffected. Do not edit in place - version forward instead.
#!/usr/bin/env python3
"""VIA · VeritasAutoPlot (VAP) engine v001 · 雙軸互比繪圖引擎.

Reads the VDF-produced analytical database (<Base>/functional modules/VDF/db or
<Base>/VDF/db · CSV / TSV / JSON / SQLite) and renders dual-axis comparison
charts as fully self-contained HTML+SVG, following Chart & Layout Spec ONE:

  Chart Library Builder unified spec: 線粗 1 · 折線 0.9 · 填色 0.75 · 軸距 2/2.5/5/10 × 5 刻度 · via combo 色序

Pairing contract 配對規約 (per operator requirement):
  一個資料一個軸 — exactly one series per axis;
  相互比較這兩個軸 — left axis vs right axis over a shared X;
  用不同的圖形來表示 — the two series always use two different mark forms
  (default: left bars, right line), and clarity is enforced: grey/ink axis
  tick labels (builder ax rule), legend + direct end labels + hover readout.

Zero third-party dependencies. Outputs are products, written under --out
(default <Base>/VAP/output); canonical trees are never touched.

Usage:
  python via_autoplot_engine_v001.py --base <Base> --list
  python via_autoplot_engine_v001.py --base <Base> --table prices \
      --x date --left close --right volume [--left-form bar|line|area]
  python via_autoplot_engine_v001.py --base <Base> --auto [--max-charts 12]
"""
from __future__ import annotations

import argparse
import csv
import datetime as _dt
import html as _html
import io
import json
import math
import re
import sqlite3
import sys
from pathlib import Path

VERSION = "v001"

# Chart & Layout Spec ONE design tokens (from the canonical spec shell).
TOKENS = {
    "bg": "#f5f4f0", "surface": "#ffffff", "paper2": "#fafaf8",
    "border": "#dbd9d3", "soft": "#ecebe6",
    "ink": "#1e1d1a", "ink2": "#33403f", "muted": "#6b6860", "muted2": "#9c9890",
    # Chart Library Builder 統一色序(VIA combo,固定順序,只增不減):
    # ["#c96b5a","#c4943a","#5a9e6f","#439a9a","#4c78a8","#7a6daa"]
    "left": "#c96b5a",   # 系列 1 · via combo C[0]
    "right": "#c4943a",  # 系列 2 · via combo C[1]
}
# Chart Library Builder 統一預設(unified spec store · vap_chartlib_v1):
LINE_WIDTH = 1        # lineWidth default 1
LINE_OPACITY = 0.9    # lineOpacity default 0.9(折線)
FILL_OPACITY = 0.75    # fillOpacity default 0.75(底部填色 / 雙軸柱)
NICE_STEPS = (1.0, 2.0, 2.5, 5.0, 10.0)  # 間隔值為 2/2.5/5/10 之倍數
AXIS_INTERVALS = 4    # 左右軸各 5 刻度 · 4 間隔(builder ax() 規則)

DB_SUFFIXES = {".csv", ".tsv", ".json", ".sqlite", ".sqlite3", ".db"}
EXCLUDED_DIRS = {".git", "__pycache__", "node_modules", "venv", "staging",
                 "received_duplicates"}
EXCLUDED_PREFIXES = ("cache", "archive", "backup")


def log(message: str) -> None:
    print(f"[VAP] {message}")


# ---------------------------------------------------------------- data intake
def _excluded(path: Path) -> bool:
    for part in path.parts:
        low = part.lower()
        if low in EXCLUDED_DIRS or low.startswith(EXCLUDED_PREFIXES):
            return True
    return False


def _scan_roots(roots: list[Path]) -> list[Path]:
    found: list[Path] = []
    for root in roots:
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*")):
            if path.is_file() and path.suffix.lower() in DB_SUFFIXES and not _excluded(path):
                found.append(path)
    return found


def discover_db_files(base: Path, extra: list[str] | None = None) -> list[Path]:
    # 1) explicit --db paths win (files or directories, anywhere on disk)
    if extra:
        found: list[Path] = []
        for raw in extra:
            path = Path(raw).expanduser().resolve()
            if path.is_file() and path.suffix.lower() in DB_SUFFIXES:
                found.append(path)
            elif path.is_dir():
                found.extend(_scan_roots([path]))
            else:
                log(f"WARN --db path not found or unsupported: {raw}")
        return found
    # 2) canonical db roots
    db_roots = [base / "functional modules" / "VDF" / "db", base / "VDF" / "db",
                base / "functional modules" / "VeritasDataForge" / "db"]
    found = _scan_roots(db_roots)
    if found:
        return found
    # 3) fallback: whole VDF trees (data may not live in a db/ subfolder yet)
    fallback = _scan_roots([base / "functional modules" / "VDF", base / "VDF",
                            base / "functional modules" / "VeritasDataForge"])
    if fallback:
        log("NOTE data found outside VDF/db — using whole-VDF fallback scan")
    return fallback


def write_demo_db(base: Path) -> Path:
    """--demo: create a small sample VDF dataset so charts work immediately."""
    import random
    random.seed(42)
    db_dir = base / "functional modules" / "VDF" / "db"
    db_dir.mkdir(parents=True, exist_ok=True)
    demo_csv = db_dir / "demo_tw_stock_monthly.csv"
    price = 580.0
    with demo_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["date", "close", "volume", "foreign_net"])
        writer.writeheader()
        for month in range(1, 25):
            year, mon = 2024 + (month - 1) // 12, (month - 1) % 12 + 1
            price *= 1 + random.uniform(-0.06, 0.08)
            writer.writerow({"date": f"{year}-{mon:02d}", "close": round(price, 1),
                             "volume": int(random.uniform(18, 55) * 1e6),
                             "foreign_net": round(random.uniform(-8, 12), 2)})
    log(f"DEMO dataset written: {demo_csv}")
    return demo_csv


def _rows_from_csv(path: Path) -> list[dict]:
    delimiter = "\t" if path.suffix.lower() == ".tsv" else ","
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle, delimiter=delimiter))


def _rows_from_json(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if isinstance(data, dict):
        for value in data.values():
            if isinstance(value, list) and value and isinstance(value[0], dict):
                return value
        return []
    if isinstance(data, list) and (not data or isinstance(data[0], dict)):
        return data
    return []


def load_tables(path: Path) -> list[tuple[str, list[dict]]]:
    """Return [(table_name, rows-as-dicts)] for one database file."""
    suffix = path.suffix.lower()
    stem = path.stem
    if suffix in {".csv", ".tsv"}:
        return [(stem, _rows_from_csv(path))]
    if suffix == ".json":
        return [(stem, _rows_from_json(path))]
    tables: list[tuple[str, list[dict]]] = []
    connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        connection.row_factory = sqlite3.Row
        names = [row[0] for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
        for name in names:
            rows = [dict(row) for row in connection.execute(
                f'SELECT * FROM "{name}"')]
            tables.append((f"{stem}.{name}", rows))
    finally:
        connection.close()
    return tables


_DATE_PATTERNS = ("%Y-%m-%d", "%Y/%m/%d", "%Y-%m", "%Y/%m", "%Y%m%d", "%Y-%m-%dT%H:%M:%S")


def parse_x(value) -> tuple[float, str] | None:
    """Coerce an X value to (sortable float, display label)."""
    if value is None:
        return None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value), f"{value:g}"
    text = str(value).strip()
    if not text:
        return None
    for pattern in _DATE_PATTERNS:
        try:
            stamp = _dt.datetime.strptime(text, pattern)
            return stamp.timestamp(), stamp.strftime("%Y-%m-%d" if "%d" in pattern else "%Y-%m")
        except ValueError:
            continue
    try:
        return float(text.replace(",", "")), text
    except ValueError:
        return None


def parse_number(value) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().replace(",", "")
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def numeric_columns(rows: list[dict]) -> list[str]:
    if not rows:
        return []
    columns = []
    for column in rows[0].keys():
        values = [parse_number(row.get(column)) for row in rows[:50]]
        good = [v for v in values if v is not None]
        if len(good) >= max(3, len(values) // 2):
            columns.append(column)
    return columns


def x_column(rows: list[dict], preferred: str | None = None) -> str | None:
    if not rows:
        return None
    if preferred:
        return preferred if preferred in rows[0] else None
    names = list(rows[0].keys())
    for name in names:
        if re.search(r"date|time|day|month|year|期間|日期", name, re.I):
            return name
    return names[0] if names else None


# ------------------------------------------------------------------ axis math
def nice_ticks(low: float, high: float, target: int = 5) -> list[float]:
    """Builder ax() rule: exactly AXIS_INTERVALS+1 ticks, step on the
    2/2.5/5/10 ladder (decade multiples), domain covering the data extremes."""
    if high <= low:
        high = low + 1.0

    def ladder(raw: float) -> float:
        magnitude = 10.0 ** math.floor(math.log10(raw))
        for candidate in NICE_STEPS:
            if candidate * magnitude >= raw:
                return candidate * magnitude
        return magnitude * 10.0

    step = ladder((high - low) / AXIS_INTERVALS)
    while True:  # 首刻度貼齊 step 網格後仍須涵蓋極值,否則升一級
        first = math.floor(low / step) * step
        if first + step * AXIS_INTERVALS >= high:
            break
        step = ladder(step * 1.0001)
    return [round(first + step * k, 10) for k in range(AXIS_INTERVALS + 1)]


def format_tick(value: float) -> str:
    if value == 0:
        return "0"
    if abs(value) >= 1_000_000_000:
        return f"{value / 1_000_000_000:.4g}B"
    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:.4g}M"
    if abs(value) >= 10_000:
        return f"{value / 1_000:.4g}K"
    if abs(value) >= 100:
        return f"{value:,.0f}"
    return f"{value:g}"


# ------------------------------------------------------------------ rendering
def _esc(text: str) -> str:
    return _html.escape(str(text), quote=True)


def _scale(value: float, low: float, high: float, px_low: float, px_high: float) -> float:
    if high <= low:
        return (px_low + px_high) / 2
    return px_low + (value - low) / (high - low) * (px_high - px_low)


def chart_code(left_form: str, right_form: str) -> str:
    """Chart Library Builder registry code for the pairing."""
    if "area" in (left_form, right_form):
        return "VAP-CH-11"  # 雙軸 底色面積×對比折線 Dual Area×Line
    if "bar" in (left_form, right_form):
        return "VAP-CH-12"  # 條+線 雙軸 Bar × Line
    return "VAP-CH-11"      # 雙折線視為 CH-11 家族(第二線虛線)


def render_chart_svg(labels: list[str], left_values: list[float], right_values: list[float],
                     left_name: str, right_name: str,
                     left_form: str, right_form: str) -> str:
    """Dual-axis chart per Chart Library Builder ax()/dbarline()/dline() rules:
    shared 5-tick / 4-interval grid on both axes, frame rect, grid #ecebe6,
    left tick labels #9c9890 / right #33403f, series colors via-combo C0/C1,
    bar fill 0.75 · area fill 0.75×0.55 · line width 1 opacity 0.9, second
    line dashed when both series are lines, colored end labels with
    collision push (≥11px)."""
    width, height = 960, 420
    pad_left, pad_right, pad_top, pad_bottom = 64, 64, 20, 46
    plot_w = width - pad_left - pad_right
    plot_h = height - pad_top - pad_bottom
    count = len(labels)

    def axis_domain(values: list[float], include_zero: bool) -> tuple[float, float, list[float]]:
        low, high = min(values), max(values)
        if include_zero:
            low, high = min(low, 0.0), max(high, 0.0)
        if low == high:
            low, high = low - 1, high + 1
        ticks = nice_ticks(low, high)
        return ticks[0], ticks[-1], ticks

    left_lo, left_hi, left_ticks = axis_domain(left_values, left_form in ("bar", "area"))
    right_lo, right_hi, right_ticks = axis_domain(right_values, right_form in ("bar", "area"))

    def y_left(value: float) -> float:
        return _scale(value, left_lo, left_hi, pad_top + plot_h, pad_top)

    def y_right(value: float) -> float:
        return _scale(value, right_lo, right_hi, pad_top + plot_h, pad_top)

    def x_center(index: int) -> float:
        slot = plot_w / max(1, count)
        return pad_left + slot * index + slot / 2

    parts: list[str] = []
    parts.append(f'<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" '
                 f'font-family="Microsoft JhengHei,Segoe UI,system-ui,sans-serif" font-size="11">')
    # shared grid: both axes have the same 5 tick positions (builder ax rule)
    for k in range(AXIS_INTERVALS + 1):
        y = pad_top + plot_h - plot_h * k / AXIS_INTERVALS
        parts.append(f'<line x1="{pad_left}" y1="{y:.1f}" x2="{width - pad_right}" y2="{y:.1f}" '
                     f'stroke="{TOKENS["soft"]}" stroke-width="1"/>')
    # frame(builder default frame=true)
    parts.append(f'<rect x="{pad_left}" y="{pad_top}" width="{plot_w}" height="{plot_h}" '
                 f'fill="none" stroke="{TOKENS["border"]}" stroke-width="1"/>')

    # marks -------------------------------------------------------------
    both_lines = left_form == "line" and right_form == "line"

    def series_marks(values, form, color, y_of, dashed):
        out = []
        slot = plot_w / max(1, count)
        if form == "bar":
            bar_w = max(2.0, slot * 0.8 / 2)  # builder: slot*0.8, halved for dual density
            base_y = y_of(0.0)
            for i, value in enumerate(values):
                top = min(y_of(value), base_y)
                bar_h = max(1.0, abs(y_of(value) - base_y))
                out.append(f'<rect x="{x_center(i) - bar_w / 2:.1f}" y="{top:.1f}" '
                           f'width="{bar_w:.1f}" height="{bar_h:.1f}" fill="{color}" '
                           f'fill-opacity="{FILL_OPACITY}"/>')
            return out
        points = " ".join(f"{x_center(i):.1f},{y_of(v):.1f}" for i, v in enumerate(values))
        if form == "area":
            floor = y_of(max(min(values), 0.0) if min(values) >= 0 else 0.0)
            out.append(f'<polygon points="{x_center(0):.1f},{floor:.1f} {points} '
                       f'{x_center(count - 1):.1f},{floor:.1f}" fill="{color}" '
                       f'fill-opacity="{FILL_OPACITY * 0.55:.2f}"/>')
        dash = ' stroke-dasharray="5 3"' if dashed else ""
        out.append(f'<polyline points="{points}" fill="none" stroke="{color}" '
                   f'stroke-width="{LINE_WIDTH}" stroke-opacity="{LINE_OPACITY}"{dash} '
                   f'stroke-linejoin="round" stroke-linecap="round"/>')
        for i, value in enumerate(values):
            out.append(f'<circle cx="{x_center(i):.1f}" cy="{y_of(value):.1f}" r="1.6" '
                       f'fill="{color}"/>')
        return out

    parts.extend(series_marks(left_values, left_form, TOKENS["left"], y_left, False))
    parts.extend(series_marks(right_values, right_form, TOKENS["right"], y_right, both_lines))

    # tick labels: left #9c9890 · right #33403f, unified decimals (builder ax)
    for k in range(AXIS_INTERVALS + 1):
        y = pad_top + plot_h - plot_h * k / AXIS_INTERVALS
        parts.append(f'<text x="{pad_left - 5}" y="{y + 2.8:.1f}" text-anchor="end" '
                     f'fill="{TOKENS["muted2"]}" font-family="Consolas,monospace" font-size="10">'
                     f'{_esc(format_tick(left_ticks[k]))}</text>')
        parts.append(f'<text x="{width - pad_right + 5}" y="{y + 2.8:.1f}" text-anchor="start" '
                     f'fill="{TOKENS["ink2"]}" font-family="Consolas,monospace" font-size="10">'
                     f'{_esc(format_tick(right_ticks[k]))}</text>')
    # x labels (thinned)
    label_every = max(1, math.ceil(count / 10))
    for i in range(0, count, label_every):
        parts.append(f'<line x1="{x_center(i):.1f}" y1="{pad_top + plot_h}" x2="{x_center(i):.1f}" '
                     f'y2="{pad_top + plot_h + 3}" stroke="#c4c0b8" stroke-width="1"/>')
        parts.append(f'<text x="{x_center(i):.1f}" y="{pad_top + plot_h + 16}" text-anchor="middle" '
                     f'fill="{TOKENS["muted"]}">{_esc(labels[i])}</text>')
    # colored end labels with collision push ≥11px (builder rule)
    y_a = y_left(left_values[-1]) - 6
    y_b = y_right(right_values[-1]) - 6
    if abs(y_a - y_b) < 11:
        push = (11 - abs(y_a - y_b)) / 2
        if y_a < y_b:
            y_a, y_b = y_a - push, y_b + push
        else:
            y_a, y_b = y_a + push, y_b - push
    parts.append(f'<text x="{x_center(count - 1) - 4:.1f}" y="{y_a:.1f}" text-anchor="end" '
                 f'font-weight="700" fill="{TOKENS["left"]}">'
                 f'{_esc(format_tick(left_values[-1]))}</text>')
    parts.append(f'<text x="{x_center(count - 1) + 4:.1f}" y="{y_b:.1f}" text-anchor="start" '
                 f'font-weight="700" fill="{TOKENS["right"]}">'
                 f'{_esc(format_tick(right_values[-1]))}</text>')
    # hover layer -------------------------------------------------------
    slot = plot_w / max(1, count)
    for i in range(count):
        tip = (f"{labels[i]} · {left_name} {format_tick(left_values[i])}"
               f" · {right_name} {format_tick(right_values[i])}")
        parts.append(
            f'<g class="hv"><rect x="{pad_left + slot * i:.1f}" y="{pad_top}" width="{slot:.1f}" '
            f'height="{plot_h}" fill="transparent"><title>{_esc(tip)}</title></rect>'
            f'<line class="ch" x1="{x_center(i):.1f}" y1="{pad_top}" x2="{x_center(i):.1f}" '
            f'y2="{pad_top + plot_h}" stroke="{TOKENS["muted2"]}" stroke-width="1" '
            f'stroke-dasharray="3 3" opacity="0"/></g>')
    parts.append("</svg>")
    return "".join(parts)


def render_page(title: str, subtitle: str, svg: str, left_name: str, right_name: str,
                left_form: str, right_form: str, source: str) -> str:
    form_zh = {"bar": "柱狀 BAR", "line": "折線 LINE", "area": "面積 AREA"}
    code = chart_code(left_form, right_form)
    return f"""<!DOCTYPE html>
<html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{_esc(title)}</title>
<style>
:root{{--bg:{TOKENS['bg']};--sf:{TOKENS['surface']};--bd:{TOKENS['border']};--ink:{TOKENS['ink']};
--ink2:{TOKENS['ink2']};--mut:{TOKENS['muted']};--left:{TOKENS['left']};--right:{TOKENS['right']}}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:var(--bg);color:var(--ink2);font-family:"Microsoft JhengHei","Segoe UI",system-ui,sans-serif;padding:22px}}
.card{{max-width:1040px;margin:0 auto;background:var(--sf);border:1px solid var(--bd);border-radius:8px;
box-shadow:0 1px 2px rgba(27,26,23,.04),0 8px 24px -12px rgba(27,26,23,.14);padding:18px 22px}}
h1{{font-size:17px;color:var(--ink)}} .sub{{font-size:11.5px;color:var(--mut);margin:2px 0 10px}}
.legend{{display:flex;gap:18px;font-size:12px;margin:6px 0 4px}}
.legend b{{font-weight:700}}
.sw{{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:6px;vertical-align:-1px}}
svg{{width:100%;height:auto;display:block}}
.hv:hover .ch{{opacity:1}}
.foot{{font-size:10px;color:var(--mut);border-top:1px solid var(--bd);margin-top:10px;padding-top:8px;
display:flex;justify-content:space-between;flex-wrap:wrap;gap:6px}}
</style></head><body><div class="card">
<h1>{_esc(title)}</h1><div class="sub">{_esc(subtitle)}</div>
<div class="legend">
<span><span class="sw" style="background:var(--left)"></span><b>{_esc(left_name)}</b> · 左軸 LEFT · {form_zh[left_form]}</span>
<span><span class="sw" style="background:var(--right)"></span><b>{_esc(right_name)}</b> · 右軸 RIGHT · {form_zh[right_form]}</span>
</div>
{svg}
<div class="foot"><span>SOURCE · VDF DB · {_esc(source)} · {code}</span>
<span>VIA · VeritasAutoPlot {VERSION} · 🔒 UNIFIED SPEC 線粗 {LINE_WIDTH} · 折線 {LINE_OPACITY} · 填色 {FILL_OPACITY} · 軸距 2/2.5/5/10 × 5 刻度 · via combo</span></div>
</div></body></html>
"""


# ------------------------------------------------------------- workbench UI
WORKBENCH_TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>VIA · VeritasAutoPlot 工作台 · AutoPlot Workbench v001</title>
<style>
:root{
 --bg:#f2f1ec; --paper:#fff; --paper2:#fbfaf7;
 --ink:#1b1a17; --ink2:#3a3f3e; --mut:#6b6860; --mut2:#9c9890;
 --line:#dcdad3; --line2:#ebe9e3;
 --teal:#3d8f8f; --blue:#4c78a8; --violet:#7a6daa; --amber:#bf8f33; --green:#4f9465; --red:#c4634f;
 --r:8px; --r-sm:5px;
 --fs-h2:clamp(17px,1.45vw,21px); --fs-h3:clamp(14px,1.08vw,15.5px);
 --fs-metric:clamp(20px,1.85vw,27px); --fs-body:clamp(12.5px,.86vw,13.5px);
 --fs-sm:clamp(11.5px,.78vw,12.5px); --fs-xs:clamp(10px,.68vw,11px); --fs-lbl:clamp(9.5px,.62vw,10.5px);
 --sb:clamp(232px,18vw,268px);
 --shadow:0 1px 2px rgba(27,26,23,.04),0 8px 24px -12px rgba(27,26,23,.14);
 --mono:"SFMono-Regular",Consolas,"Liberation Mono",monospace;
 --sans:"Microsoft JhengHei","Segoe UI",system-ui,Arial,sans-serif;
}
*{box-sizing:border-box;margin:0;padding:0}
html,body{height:100%}
body{background:var(--bg);color:var(--ink2);font-family:var(--sans);font-size:var(--fs-body);line-height:1.62;display:flex;overflow:hidden}
.sidebar{flex:none;width:var(--sb);height:100vh;background:var(--paper);border-right:1px solid var(--line);display:flex;flex-direction:column}
.brand{padding:18px 16px 12px;border-bottom:1px solid var(--line2)}
.brand .k{font:700 var(--fs-lbl) var(--mono);letter-spacing:.14em;text-transform:uppercase;color:var(--mut2)}
.brand h2{font-size:var(--fs-h2);color:var(--ink);line-height:1.25;margin-top:4px}
.brand h2 span{display:block;font-size:var(--fs-xs);font-weight:400;color:var(--mut)}
.brand p{font:600 var(--fs-lbl) var(--mono);color:var(--teal);margin-top:6px;letter-spacing:.06em}
.navScroll{flex:1;overflow-y:auto;padding:10px 10px 14px}
.groupTitle{font:700 var(--fs-lbl) var(--mono);letter-spacing:.12em;text-transform:uppercase;color:var(--mut2);padding:12px 8px 5px}
.nav button{display:flex;align-items:center;gap:9px;width:100%;text-align:left;border:1px solid transparent;background:none;
 border-radius:var(--r-sm);padding:7px 9px;font-family:var(--sans);font-size:var(--fs-sm);color:var(--ink2);cursor:pointer}
.nav button:hover{background:var(--paper2);border-color:var(--line2)}
.nav button.on{background:var(--ink);color:#fff}
.nav button.on .n{color:#fff;opacity:.7}
.nav .n{font:700 var(--fs-lbl) var(--mono);color:var(--mut2);width:18px;flex:none}
.nav .en{display:block;font-size:var(--fs-xs);opacity:.65}
.sideStats{border-top:1px solid var(--line2);padding:10px 16px;display:grid;grid-template-columns:1fr 1fr;gap:6px 10px}
.sideStats .mk{font:700 var(--fs-lbl) var(--mono);letter-spacing:.08em;color:var(--mut2);text-transform:uppercase;display:block}
.sideStats .mv{font:700 var(--fs-sm) var(--mono);color:var(--ink)}
.main{flex:1;height:100vh;overflow-y:auto;display:flex;flex-direction:column}
header{padding:18px 26px 12px;border-bottom:1px solid var(--line);background:var(--paper2);display:flex;justify-content:space-between;gap:18px;flex-wrap:wrap}
.kicker{font:700 var(--fs-lbl) var(--mono);letter-spacing:.12em;text-transform:uppercase;color:var(--teal)}
header h1{font-size:var(--fs-h2);color:var(--ink);margin-top:2px}
header h1 span{font-size:var(--fs-xs);font-weight:400;color:var(--mut);margin-left:8px}
.sub{font-size:var(--fs-sm);color:var(--mut)}
.headMeta{display:flex;gap:20px;align-items:center;flex-wrap:wrap}
.headMeta .mk{font:700 var(--fs-lbl) var(--mono);letter-spacing:.08em;color:var(--mut2);text-transform:uppercase;display:block}
.headMeta .mv{font:700 var(--fs-sm) var(--mono);color:var(--ink)}
.pages{flex:1;padding:18px 26px 30px}
.page{display:none}
.page.on{display:block}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin-bottom:16px}
.card{display:flex;flex-direction:column;justify-content:space-between;min-height:78px;background:var(--paper);border:1px solid var(--line);border-radius:var(--r-sm);padding:10px 13px;min-width:0}
.card .v{font:700 var(--fs-metric) var(--mono);color:var(--ink)}
.card .l{font:700 var(--fs-lbl) var(--mono);letter-spacing:.08em;text-transform:uppercase;color:var(--mut2)}
.panel{background:var(--paper);border:1px solid var(--line);border-radius:var(--r);box-shadow:var(--shadow);padding:15px 18px;margin-bottom:16px}
.panel h3{font-size:var(--fs-h3);color:var(--ink)}
.panel h3 span{font-size:var(--fs-xs);font-weight:400;color:var(--mut);margin-left:7px}
.panel .hint{font-size:var(--fs-xs);color:var(--mut);margin:2px 0 10px}
table{width:100%;border-collapse:collapse;font-size:var(--fs-sm)}
th{font:700 var(--fs-lbl) var(--mono);letter-spacing:.07em;text-transform:uppercase;color:var(--mut2);text-align:left;
 border-bottom:1px solid var(--line);padding:5px 8px}
td{border-bottom:1px solid var(--line2);padding:6px 8px;vertical-align:top;word-break:break-word}
.mono{font-family:var(--mono)}
.ctrl{display:flex;gap:14px;flex-wrap:wrap;align-items:flex-end;margin-bottom:12px}
.ctrl label{display:block;font:700 var(--fs-lbl) var(--mono);letter-spacing:.08em;text-transform:uppercase;color:var(--mut2);margin-bottom:3px}
.ctrl select,.ctrl button{font-family:var(--sans);font-size:var(--fs-sm);color:var(--ink2);background:var(--paper2);
 border:1px solid var(--line);border-radius:var(--r-sm);padding:6px 9px;cursor:pointer}
.ctrl .go{background:var(--ink);color:#fff;font-weight:700;border-color:var(--ink);padding:6px 16px}
.ctrl .swap{font-family:var(--mono)}
.legend{display:flex;gap:18px;font-size:var(--fs-sm);margin:4px 0 2px}
.sw{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:6px;vertical-align:-1px}
svg{width:100%;height:auto;display:block}
.hv:hover .ch{opacity:1}
.readout{font:600 var(--fs-xs) var(--mono);color:var(--mut);min-height:18px;margin-top:4px}
.gallery{display:grid;grid-template-columns:repeat(auto-fill,minmax(330px,1fr));gap:12px}
.gcell{background:var(--paper);border:1px solid var(--line);border-radius:var(--r-sm);padding:10px 12px;cursor:pointer}
.gcell:hover{border-color:var(--teal)}
.gcell .t{font-size:var(--fs-sm);font-weight:700;color:var(--ink)}
.gcell .s{font-size:var(--fs-xs);color:var(--mut);margin-bottom:4px}
.lockrow{display:flex;gap:10px;flex-wrap:wrap;margin:8px 0}
.badge{font:700 var(--fs-lbl) var(--mono);letter-spacing:.06em;border:1px solid var(--line);border-radius:var(--r-sm);
 background:var(--paper2);color:var(--ink2);padding:3px 9px}
footer{border-top:1px solid var(--line);padding:8px 26px;font-size:var(--fs-xs);color:var(--mut);background:var(--paper2);
 display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px}
kbd{font:700 var(--fs-lbl) var(--mono);border:1px solid var(--line);border-bottom-width:2px;border-radius:4px;padding:0 5px;background:var(--paper)}
</style></head><body>
<aside class="sidebar">
 <div class="brand">
  <div class="k"><span>Veritas Intelligence Analytics</span></div>
  <h2>自動繪圖工作台<br><span>AutoPlot Workbench</span></h2>
  <p>VAP · VeritasAutoPlot · v001</p>
 </div>
 <div class="navScroll">
  <div class="groupTitle">繪圖 Plotting</div>
  <div class="nav">
   <button id="nav-home" onclick="switchPage('home')"><span class="n">01</span><span>平台總覽<span class="en">OVERVIEW</span></span></button>
   <button id="nav-pair" onclick="switchPage('pair')"><span class="n">02</span><span>配對繪圖<span class="en">PAIR PLOT</span></span></button>
   <button id="nav-gallery" onclick="switchPage('gallery')"><span class="n">03</span><span>圖庫 <span class="en">GALLERY</span></span></button>
  </div>
  <div class="groupTitle">治理 Governance</div>
  <div class="nav">
   <button id="nav-spec" onclick="switchPage('spec')"><span class="n">04</span><span>繪圖規範<span class="en">SPEC · VISUAL LOCK</span></span></button>
  </div>
 </div>
 <div class="sideStats">
  <div><span class="mk">Tables</span><span class="mv" id="ssTables">0</span></div>
  <div><span class="mk">Pairs</span><span class="mv" id="ssPairs">0</span></div>
  <div><span class="mk">State</span><span class="mv" style="color:var(--green)">READY</span></div>
  <div><span class="mk">Lock</span><span class="mv">🔒 1 · .9/.75</span></div>
 </div>
</aside>
<div class="main">
 <header>
  <div>
   <div class="kicker">VDF 資料庫 → 雙軸互比 → 規範圖表 · VISUAL LOCK</div>
   <h1 id="pageTitle">平台總覽 <span>Overview</span></h1>
   <p id="pageSubtitle" class="sub">資料目錄與繪圖入口 · Data catalog and plotting entry</p>
  </div>
  <div class="headMeta">
   <div><span class="mk">建置 Build</span><span class="mv">VAP v001</span></div>
   <div><span class="mk">資料表 Tables</span><span class="mv" id="hmTables">0</span></div>
   <div><span class="mk">規範 Spec</span><span class="mv">ONE 🔒</span></div>
  </div>
 </header>
 <div class="pages">
  <section class="page" id="page-home">
   <div class="cards">
    <div class="card"><div class="v" id="cTables">0</div><div class="l">資料表 Tables</div></div>
    <div class="card"><div class="v" id="cRows">0</div><div class="l">資料列 Rows</div></div>
    <div class="card"><div class="v" id="cCols">0</div><div class="l">數值欄 Numeric</div></div>
    <div class="card"><div class="v" id="cPairs">0</div><div class="l">可配對 Pairs</div></div>
   </div>
   <div class="panel">
    <h3>VDF 資料目錄 <span>Data Catalog</span></h3>
    <div class="hint">來源 Source:VDF 分析資料庫(CSV / TSV / JSON / SQLite)· 唯讀 READ-ONLY</div>
    <table><thead><tr><th>資料表 Table</th><th>列數 Rows</th><th>X 軸</th><th>數值欄 Numeric Columns</th><th>來源 Origin</th></tr></thead>
    <tbody id="catalogBody"></tbody></table>
   </div>
  </section>
  <section class="page" id="page-pair">
   <div class="panel">
    <h3>雙軸互比設定 <span>Dual-Axis Pairing</span></h3>
    <div class="hint">配對規約:一個資料一個軸 · 兩軸互比 · 兩系列必用不同圖形 · 顯示清楚</div>
    <div class="ctrl">
     <div><label>資料表 Table</label><select id="selTable"></select></div>
     <div><label>X 軸</label><select id="selX"></select></div>
     <div><label>左軸 Left</label><select id="selLeft"></select></div>
     <div><label>左圖形 Form</label><select id="selLeftForm"><option value="bar">柱狀 BAR</option><option value="line">折線 LINE</option><option value="area">面積 AREA</option></select></div>
     <div><label>右軸 Right</label><select id="selRight"></select></div>
     <div><label>右圖形 Form</label><select id="selRightForm"><option value="line">折線 LINE</option><option value="bar">柱狀 BAR</option><option value="area">面積 AREA</option></select></div>
     <button class="swap" onclick="swapAxes()" title="左右互換">⇄ 互換</button>
     <button class="go" onclick="renderPair()">繪製 RENDER</button>
    </div>
    <div class="legend" id="pairLegend"></div>
    <div id="pairChart"></div>
    <div class="readout" id="pairReadout">滑鼠移入圖面可讀值 · hover for readout</div>
   </div>
  </section>
  <section class="page" id="page-gallery">
   <div class="panel">
    <h3>全配對圖庫 <span>Auto-Pair Gallery</span></h3>
    <div class="hint">每一組數值欄配對一張縮圖;點擊載入「02 配對繪圖」細看 · click to open in PAIR PLOT</div>
    <div class="gallery" id="galleryGrid"></div>
   </div>
  </section>
  <section class="page" id="page-spec">
   <div class="panel">
    <h3>視覺鎖 <span>VISUAL LOCK</span></h3>
    <div class="lockrow">
     <span class="badge">線粗 LINE WIDTH · 1</span>
     <span class="badge">折線透明 LINE OPACITY · 0.9</span>
     <span class="badge">填色透明 FILL OPACITY · 0.75</span>
     <span class="badge">軸距 STEPS · 2 / 2.5 / 5 / 10 倍數</span>
     <span class="badge">左右軸 5 刻度 · 4 間隔</span>
     <span class="badge">外框 FRAME · ON</span>
    </div>
    <div class="hint">權威來源 Authority:VAP 最佳圖庫建構器 Chart Library Builder(統一位置 unified spec store · 28 圖型註冊 VAP-CH-01…28)+ Chart &amp; Layout Spec ONE;皆 SHA-256 登錄於 VAP anchor</div>
   </div>
   <div class="panel">
    <h3>配對規約 <span>Pairing Contract</span></h3>
    <table><thead><tr><th>項目 Item</th><th>規定 Rule</th></tr></thead><tbody>
     <tr><td>軸 Axes</td><td>一個資料一個軸;左軸 × 右軸,共用 X,相互比較</td></tr>
     <tr><td>圖形 Forms</td><td>兩系列必用不同圖形(柱 / 線 / 面積);相同選擇會被強制錯開</td></tr>
     <tr><td>色票 Colors</td><td><span class="sw" style="background:#c96b5a"></span>系列1 #c96b5a · <span class="sw" style="background:#c4943a"></span>系列2 #c4943a(VIA combo 固定色序,Chart Library Builder 統一預設)</td></tr>
     <tr><td>圖型編號 Codes</td><td>柱×線 = VAP-CH-12 · 面積×線 = VAP-CH-11(雙折線時第二線虛線)</td></tr>
     <tr><td>清晰 Clarity</td><td>軸刻度染系列色 · 圖例 · 末值直標 · 懸停讀值 · 淡灰格線</td></tr>
     <tr><td>治理 Governance</td><td>VDF 資料庫唯讀;產出僅寫入 &lt;Base&gt;/VAP/output</td></tr>
    </tbody></table>
   </div>
  </section>
 </div>
 <footer>
  <span>VIA · VeritasAutoPlot v001 · 🔒 VISUAL LOCK 線粗 1 · 折線 0.9 · 填色 0.75 · 軸距 2/2.5/5/10</span>
  <span>鍵盤:<kbd>[</kbd> / <kbd>]</kbd> 切換頁面</span>
 </footer>
</div>
<script>
const CATALOG = __CATALOG__;
const LOCK = {lw:1, lineOp:0.9, fillOp:0.75, steps:[1,2,2.5,5,10], intervals:4};
const COLORS = {left:'#c96b5a', right:'#c4943a', soft:'#ebe9e3', frame:'#dbd9d3', ink2:'#33403f', mut:'#6b6860', mut2:'#9c9890'};
const PAGES = ['home','pair','gallery','spec'];
const TITLES = {home:['平台總覽','Overview','資料目錄與繪圖入口 · Data catalog and plotting entry'],
 pair:['配對繪圖','Pair Plot','雙軸互比 · 一個資料一個軸 · Dual-axis comparison'],
 gallery:['圖庫','Gallery','全配對縮圖 · All numeric pairs at a glance'],
 spec:['繪圖規範','Spec · Visual Lock','權威定義與配對規約 · Authority and pairing contract']};
function switchPage(p){
 PAGES.forEach(q=>{document.getElementById('page-'+q).classList.toggle('on',q===p);
  document.getElementById('nav-'+q).classList.toggle('on',q===p);});
 const t=TITLES[p];
 document.getElementById('pageTitle').innerHTML=t[0]+' <span>'+t[1]+'</span>';
 document.getElementById('pageSubtitle').textContent=t[2];
 try{localStorage.setItem('vap_wb_page',p);}catch(e){}
}
document.addEventListener('keydown',e=>{
 if(e.key!=='['&&e.key!==']')return;
 const cur=PAGES.findIndex(p=>document.getElementById('page-'+p).classList.contains('on'));
 switchPage(PAGES[(cur+(e.key===']'?1:PAGES.length-1))%PAGES.length]);
});
function ladder(raw){const mag=Math.pow(10,Math.floor(Math.log10(raw)));
 for(const c of LOCK.steps){if(c*mag>=raw)return c*mag;}return mag*10;}
function niceTicks(lo,hi){
 if(hi<=lo)hi=lo+1;
 let step=ladder((hi-lo)/LOCK.intervals);
 let first=Math.floor(lo/step)*step;
 while(first+step*LOCK.intervals<hi){step=ladder(step*1.0001);first=Math.floor(lo/step)*step;}
 const t=[];for(let k=0;k<=LOCK.intervals;k++)t.push(+(first+step*k).toPrecision(12));
 return t;
}
function fmt(v){
 if(v===0)return'0';
 const a=Math.abs(v);
 if(a>=1e9)return(v/1e9).toPrecision(4).replace(/\.?0+$/,'')+'B';
 if(a>=1e6)return(v/1e6).toPrecision(4).replace(/\.?0+$/,'')+'M';
 if(a>=1e4)return(v/1e3).toPrecision(4).replace(/\.?0+$/,'')+'K';
 if(a>=100)return v.toLocaleString(undefined,{maximumFractionDigits:0});
 return String(+v.toPrecision(6));
}
function esc(s){return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');}
function drawChart(labels,lv,rv,lname,rname,lform,rform,compact){
 if(lform===rform)rform=lform!=='line'?'line':'bar';
 const bothLines=lform==='line'&&rform==='line';
 const W=960,H=compact?300:420,PL=64,PR=64,PT=18,PB=44,pw=W-PL-PR,ph=H-PT-PB,n=labels.length;
 function dom(vals,zero){let lo=Math.min(...vals),hi=Math.max(...vals);
  if(zero){lo=Math.min(lo,0);hi=Math.max(hi,0);}if(lo===hi){lo-=1;hi+=1;}
  const t=niceTicks(lo,hi);return{lo:t[0],hi:t[t.length-1],t:t};}
 const L=dom(lv,lform!=='line'),R=dom(rv,rform!=='line');
 const yl=v=>PT+ph-(v-L.lo)/(L.hi-L.lo)*ph, yr=v=>PT+ph-(v-R.lo)/(R.hi-R.lo)*ph;
 const slot=pw/Math.max(1,n), xc=i=>PL+slot*i+slot/2;
 let s='<svg viewBox="0 0 '+W+' '+H+'" xmlns="http://www.w3.org/2000/svg" font-family="Microsoft JhengHei,Segoe UI,sans-serif" font-size="11">';
 for(let k=0;k<=LOCK.intervals;k++){const yy=PT+ph-ph*k/LOCK.intervals;
  s+='<line x1="'+PL+'" y1="'+yy+'" x2="'+(W-PR)+'" y2="'+yy+'" stroke="'+COLORS.soft+'"/>';}
 s+='<rect x="'+PL+'" y="'+PT+'" width="'+pw+'" height="'+ph+'" fill="none" stroke="'+COLORS.frame+'"/>';
 function marks(vals,form,color,yof,dashed){
  let o='';
  if(form==='bar'){const bw=Math.max(2,slot*0.8/2),base=yof(0);
   for(let i=0;i<n;i++){const top=Math.min(yof(vals[i]),base),h=Math.max(1,Math.abs(yof(vals[i])-base));
    o+='<rect x="'+(xc(i)-bw/2)+'" y="'+top+'" width="'+bw+'" height="'+h+'" fill="'+color+'" fill-opacity="'+LOCK.fillOp+'"/>';}
   return o;}
  const pts=vals.map((v,i)=>xc(i)+','+yof(v)).join(' ');
  if(form==='area'){o+='<polygon points="'+xc(0)+','+yof(Math.max(Math.min(...vals),0))+' '+pts+' '+xc(n-1)+','+yof(Math.max(Math.min(...vals),0))+'" fill="'+color+'" fill-opacity="'+(LOCK.fillOp*0.55).toFixed(2)+'"/>';}
  o+='<polyline points="'+pts+'" fill="none" stroke="'+color+'" stroke-width="'+LOCK.lw+'" stroke-opacity="'+LOCK.lineOp+'"'+(dashed?' stroke-dasharray="5 3"':'')+' stroke-linejoin="round" stroke-linecap="round"/>';
  for(let i=0;i<n;i++)o+='<circle cx="'+xc(i)+'" cy="'+yof(vals[i])+'" r="1.6" fill="'+color+'"/>';
  return o;}
 s+=marks(lv,lform,COLORS.left,yl,false)+marks(rv,rform,COLORS.right,yr,bothLines);
 for(let k=0;k<=LOCK.intervals;k++){const yy=PT+ph-ph*k/LOCK.intervals;
  s+='<text x="'+(PL-5)+'" y="'+(yy+2.8)+'" text-anchor="end" fill="'+COLORS.mut2+'" font-family="Consolas,monospace" font-size="10">'+fmt(L.t[k])+'</text>';
  s+='<text x="'+(W-PR+5)+'" y="'+(yy+2.8)+'" text-anchor="start" fill="'+COLORS.ink2+'" font-family="Consolas,monospace" font-size="10">'+fmt(R.t[k])+'</text>';}
 const ev=Math.max(1,Math.ceil(n/(compact?6:10)));
 for(let i=0;i<n;i+=ev){s+='<line x1="'+xc(i)+'" y1="'+(PT+ph)+'" x2="'+xc(i)+'" y2="'+(PT+ph+3)+'" stroke="#c4c0b8"/>';
  s+='<text x="'+xc(i)+'" y="'+(PT+ph+16)+'" text-anchor="middle" fill="'+COLORS.mut+'">'+esc(labels[i])+'</text>';}
 let yA=yl(lv[n-1])-6,yB=yr(rv[n-1])-6;
 if(Math.abs(yA-yB)<11){const push=(11-Math.abs(yA-yB))/2;if(yA<yB){yA-=push;yB+=push;}else{yA+=push;yB-=push;}}
 s+='<text x="'+(xc(n-1)-4)+'" y="'+yA+'" text-anchor="end" font-weight="700" fill="'+COLORS.left+'">'+fmt(lv[n-1])+'</text>';
 s+='<text x="'+(xc(n-1)+4)+'" y="'+yB+'" text-anchor="start" font-weight="700" fill="'+COLORS.right+'">'+fmt(rv[n-1])+'</text>';
 for(let i=0;i<n;i++){
  s+='<g class="hv" data-i="'+i+'"><rect x="'+(PL+slot*i)+'" y="'+PT+'" width="'+slot+'" height="'+ph+'" fill="transparent"/>'
   +'<line class="ch" x1="'+xc(i)+'" y1="'+PT+'" x2="'+xc(i)+'" y2="'+(PT+ph)+'" stroke="'+COLORS.mut2+'" stroke-dasharray="3 3" opacity="0"/></g>';}
 s+='</svg>';
 return s;
}
function tableByName(name){return CATALOG.find(t=>t.name===name);}
function fillSelect(sel,opts,val){sel.innerHTML=opts.map(o=>'<option'+(o===val?' selected':'')+'>'+esc(o)+'</option>').join('');}
function onTableChange(){
 const t=tableByName(document.getElementById('selTable').value);if(!t)return;
 fillSelect(document.getElementById('selX'),t.all_columns,t.x);
 fillSelect(document.getElementById('selLeft'),t.numeric,t.numeric[0]);
 fillSelect(document.getElementById('selRight'),t.numeric,t.numeric[1]||t.numeric[0]);
}
function swapAxes(){
 const l=document.getElementById('selLeft'),r=document.getElementById('selRight');
 const tmp=l.value;l.value=r.value;r.value=tmp;renderPair();
}
function seriesOf(t,xcol,col){
 const pts=[];
 for(let i=0;i<t.rows.length;i++){
  const x=t.rows[i][xcol],v=parseFloat(String(t.rows[i][col]).replace(/,/g,''));
  if(x!==undefined&&x!==null&&String(x).length&&isFinite(v))pts.push([String(x),v]);}
 return pts;
}
function renderPair(){
 const t=tableByName(document.getElementById('selTable').value);if(!t)return;
 const xcol=document.getElementById('selX').value,
  ln=document.getElementById('selLeft').value, rn=document.getElementById('selRight').value,
  lf=document.getElementById('selLeftForm').value, rf=document.getElementById('selRightForm').value;
 const lp=seriesOf(t,xcol,ln), rp=seriesOf(t,xcol,rn);
 const keys=lp.map(p=>p[0]).filter(k=>rp.some(q=>q[0]===k));
 const labels=keys, lv=keys.map(k=>lp.find(p=>p[0]===k)[1]), rv=keys.map(k=>rp.find(p=>p[0]===k)[1]);
 if(labels.length<3){document.getElementById('pairChart').innerHTML='<div class="hint">資料點不足(&lt;3)· not enough complete points</div>';return;}
 const fz={bar:'柱狀 BAR',line:'折線 LINE',area:'面積 AREA'};
 document.getElementById('pairLegend').innerHTML=
  '<span><span class="sw" style="background:'+COLORS.left+'"></span><b>'+esc(ln)+'</b> · 左軸 LEFT · '+fz[lf]+'</span>'
 +'<span><span class="sw" style="background:'+COLORS.right+'"></span><b>'+esc(rn)+'</b> · 右軸 RIGHT · '+fz[rf===lf?(lf!=='line'?'line':'bar'):rf]+'</span>';
 document.getElementById('pairChart').innerHTML=drawChart(labels,lv,rv,ln,rn,lf,rf,false);
 document.querySelectorAll('#pairChart .hv').forEach(g=>{
  g.addEventListener('mousemove',()=>{const i=+g.dataset.i;
   document.getElementById('pairReadout').textContent=labels[i]+' · '+ln+' '+fmt(lv[i])+' · '+rn+' '+fmt(rv[i]);});});
}
function openInPair(tname,l,r){
 fillSelect(document.getElementById('selTable'),CATALOG.map(t=>t.name),tname);
 onTableChange();
 document.getElementById('selLeft').value=l;document.getElementById('selRight').value=r;
 switchPage('pair');renderPair();
}
function boot(){
 let rows=0,cols=0,pairs=0;
 const cbody=document.getElementById('catalogBody'),grid=document.getElementById('galleryGrid');
 for(const t of CATALOG){
  rows+=t.rows.length;cols+=t.numeric.length;
  pairs+=t.numeric.length*(t.numeric.length-1)/2;
  cbody.innerHTML+='<tr><td class="mono"><b>'+esc(t.name)+'</b></td><td class="mono">'+t.rows.length+'</td><td class="mono">'+esc(t.x)+'</td><td>'+t.numeric.map(esc).join(' · ')+'</td><td class="mono">'+esc(t.origin)+'</td></tr>';
  for(let i=0;i<t.numeric.length;i++)for(let j=i+1;j<t.numeric.length;j++){
   const l=t.numeric[i],r=t.numeric[j];
   const lp=seriesOf(t,t.x,l),rp=seriesOf(t,t.x,r);
   const keys=lp.map(p=>p[0]).filter(k=>rp.some(q=>q[0]===k));
   if(keys.length<3)continue;
   const cell=document.createElement('div');cell.className='gcell';
   cell.innerHTML='<div class="t">'+esc(l)+' × '+esc(r)+'</div><div class="s">'+esc(t.name)+' · '+keys.length+' pts</div>'
    +drawChart(keys,keys.map(k=>lp.find(p=>p[0]===k)[1]),keys.map(k=>rp.find(p=>p[0]===k)[1]),l,r,'bar','line',true);
   cell.onclick=()=>openInPair(t.name,l,r);
   grid.appendChild(cell);}}
 document.getElementById('cTables').textContent=CATALOG.length;
 document.getElementById('cRows').textContent=rows;
 document.getElementById('cCols').textContent=cols;
 document.getElementById('cPairs').textContent=pairs;
 document.getElementById('ssTables').textContent=CATALOG.length;
 document.getElementById('ssPairs').textContent=pairs;
 document.getElementById('hmTables').textContent=CATALOG.length;
 if(CATALOG.length){fillSelect(document.getElementById('selTable'),CATALOG.map(t=>t.name),CATALOG[0].name);
  document.getElementById('selTable').addEventListener('change',onTableChange);
  onTableChange();renderPair();}
 let p='home';try{p=localStorage.getItem('vap_wb_page')||'home';}catch(e){}
 switchPage(PAGES.includes(p)?p:'home');
}
boot();
</script></body></html>
"""

MAX_UI_ROWS = 800


def write_workbench(catalog: list[tuple[str, list[dict], str]], out_dir: Path) -> Path:
    """--ui: emit the interactive AutoPlot Workbench (v0162C platform format)."""
    payload = []
    for name, rows, origin in catalog:
        numerics = numeric_columns(rows)
        x_name = x_column(rows)
        trimmed = rows[:MAX_UI_ROWS]
        if len(rows) > MAX_UI_ROWS:
            log(f"UI  {name}: embedding first {MAX_UI_ROWS} of {len(rows)} rows")
        payload.append({
            "name": name, "origin": origin, "x": x_name,
            "all_columns": list(rows[0].keys()) if rows else [],
            "numeric": numerics,
            "rows": [{k: row.get(k) for k in ([x_name] if x_name else []) + numerics}
                     for row in trimmed],
        })
    page = WORKBENCH_TEMPLATE.replace("__CATALOG__", json.dumps(payload, ensure_ascii=False))
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "VAP_Workbench.html"
    out_path.write_text(page, encoding="utf-8")
    log(f"WORKBENCH {out_path}")
    return out_path


# ----------------------------------------------------------------- pipelines
def build_pair_chart(rows: list[dict], table: str, x_name: str, left_name: str,
                     right_name: str, left_form: str, right_form: str,
                     out_dir: Path, source: str) -> Path | None:
    points = []
    for row in rows:
        x_parsed = parse_x(row.get(x_name))
        left_value = parse_number(row.get(left_name))
        right_value = parse_number(row.get(right_name))
        if x_parsed is None or left_value is None or right_value is None:
            continue
        points.append((x_parsed[0], x_parsed[1], left_value, right_value))
    if len(points) < 3:
        log(f"SKIP {table}: fewer than 3 complete points for {left_name} vs {right_name}")
        return None
    points.sort(key=lambda item: item[0])
    labels = [p[1] for p in points]
    left_values = [p[2] for p in points]
    right_values = [p[3] for p in points]
    if left_form == right_form:
        right_form = "line" if left_form != "line" else "bar"  # 強制不同圖形
    svg = render_chart_svg(labels, left_values, right_values, left_name, right_name,
                           left_form, right_form)
    title = f"{left_name} × {right_name} · 雙軸互比 Dual-Axis Comparison"
    subtitle = f"table {table} · X = {x_name} · {len(points)} points"
    page = render_page(title, subtitle, svg, left_name, right_name, left_form, right_form, source)
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", f"{table}__{left_name}__vs__{right_name}")
    out_path = out_dir / f"VAP_{safe}.html"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path.write_text(page, encoding="utf-8")
    log(f"CHART {out_path.name} ({len(points)} pts, {left_form}+{right_form})")
    return out_path


def write_index(out_dir: Path, charts: list[Path]) -> Path:
    items = "\n".join(
        f'<li><a href="{_esc(p.name)}">{_esc(p.name)}</a></li>' for p in charts)
    page = f"""<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">
<title>VIA · VeritasAutoPlot 圖庫索引</title>
<style>body{{background:{TOKENS['bg']};font-family:"Microsoft JhengHei","Segoe UI",sans-serif;
color:{TOKENS['ink2']};padding:24px}}h1{{font-size:16px;color:{TOKENS['ink']}}}
li{{margin:4px 0;font-size:13px}}</style></head><body>
<h1>VIA · VeritasAutoPlot {VERSION} · 產出索引 ({len(charts)})</h1><ul>{items}</ul></body></html>"""
    index_path = out_dir / "index.html"
    index_path.write_text(page, encoding="utf-8")
    return index_path


def main() -> int:
    parser = argparse.ArgumentParser(description="VIA VeritasAutoPlot engine")
    parser.add_argument("--base", required=True)
    parser.add_argument("--list", action="store_true", help="list tables/columns and exit")
    parser.add_argument("--table", help="table name (file stem, or sqlitefile.table)")
    parser.add_argument("--x", dest="x_name", help="X column (default: auto date-like)")
    parser.add_argument("--left", help="left-axis column")
    parser.add_argument("--right", help="right-axis column")
    parser.add_argument("--left-form", choices=["bar", "line", "area"], default="bar")
    parser.add_argument("--right-form", choices=["bar", "line", "area"], default="line")
    parser.add_argument("--auto", action="store_true",
                        help="auto-generate charts for numeric column pairs")
    parser.add_argument("--max-charts", type=int, default=12)
    parser.add_argument("--out", help="output dir (default <Base>/VAP/output)")
    parser.add_argument("--db", action="append",
                        help="explicit data file or folder (repeatable); overrides auto-discovery")
    parser.add_argument("--demo", action="store_true",
                        help="write a sample dataset into VDF/db first (demo_tw_stock_monthly.csv)")
    parser.add_argument("--ui", action="store_true",
                        help="emit the interactive AutoPlot Workbench (v0162C platform format)")
    args = parser.parse_args()

    base = Path(args.base).resolve()
    out_dir = Path(args.out).resolve() if args.out else base / "VAP" / "output"
    if args.demo:
        write_demo_db(base)
    files = discover_db_files(base, args.db)
    if not files:
        log("no VDF database files found. Options: put CSV/TSV/JSON/SQLite under "
            "<Base>/functional modules/VDF/db, point at data with --db <file-or-folder>, "
            "or run with --demo for a sample dataset")
        return 2
    catalog: list[tuple[str, list[dict], str]] = []
    for path in files:
        try:
            try:
                origin = str(path.relative_to(base))
            except ValueError:  # --db source outside Base
                origin = str(path)
            for name, rows in load_tables(path):
                if rows:
                    catalog.append((name, rows, origin))
        except Exception as exc:  # noqa: BLE001 — corrupt source must not kill the run
            log(f"WARN cannot read {path.name}: {exc}")

    if args.ui:
        workbench = write_workbench(catalog, out_dir)
        log(f"DONE workbench → {workbench}")
        if not (args.auto or (args.table and args.left and args.right)):
            return 0

    if args.list or (not args.auto and not args.ui
                     and not (args.table and args.left and args.right)):
        log(f"{len(catalog)} table(s) discovered:")
        for name, rows, rel in catalog:
            numerics = numeric_columns(rows)
            log(f"  {name} ({len(rows)} rows, {rel}) · X≈{x_column(rows)} · numeric: {', '.join(numerics)}")
        if not args.list:
            log("give --table/--left/--right for one pair, or --auto for all pairs")
        return 0

    charts: list[Path] = []
    if args.auto:
        for name, rows, rel in catalog:
            x_name = x_column(rows, args.x_name)
            numerics = [c for c in numeric_columns(rows) if c != x_name]
            for i in range(len(numerics)):
                for j in range(i + 1, len(numerics)):
                    if len(charts) >= args.max_charts:
                        log(f"CAP reached ({args.max_charts}) — remaining pairs skipped; "
                            f"raise --max-charts to cover them")
                        break
                    chart = build_pair_chart(rows, name, x_name, numerics[i], numerics[j],
                                             args.left_form, args.right_form, out_dir, rel)
                    if chart:
                        charts.append(chart)
    else:
        matches = [(n, r, rel) for n, r, rel in catalog if n == args.table]
        if not matches:
            log(f"table not found: {args.table} (use --list)")
            return 2
        name, rows, rel = matches[0]
        x_name = x_column(rows, args.x_name)
        chart = build_pair_chart(rows, name, x_name, args.left, args.right,
                                 args.left_form, args.right_form, out_dir, rel)
        if chart:
            charts.append(chart)

    if not charts:
        log("no charts produced")
        return 2
    index_path = write_index(out_dir, charts)
    log(f"INDEX {index_path}")
    log(f"DONE {len(charts)} chart(s) → {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
