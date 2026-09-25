#!/usr/bin/env python3
"""VIA · VeritasAutoPlot (VAP) engine v001 · 雙軸互比繪圖引擎.

Reads the VDF-produced analytical database (<Base>/functional modules/VDF/db or
<Base>/VDF/db · CSV / TSV / JSON / SQLite) and renders dual-axis comparison
charts as fully self-contained HTML+SVG, following Chart & Layout Spec ONE:

  VISUAL LOCK · 線粗 1 · 透明度 0.75 · 軸距 1/2/2.5/5/10 nice steps

Pairing contract 配對規約 (per operator requirement):
  一個資料一個軸 — exactly one series per axis;
  相互比較這兩個軸 — left axis vs right axis over a shared X;
  用不同的圖形來表示 — the two series always use two different mark forms
  (default: left bars, right line), and clarity is enforced: each axis is
  tinted to its series colour, legend + direct end labels + hover readout.

Zero third-party dependencies. Outputs are products, written under --out
(default <Base>/VAP/output); canonical trees are never touched.

Usage:
  python via_autoplot_engine_v001.py --base <Base> --list
  python via_autoplot_engine_v001.py --base <Base> --table prices \
      --x date --left close --right volume [--left-form bar|line|area]
  python via_autoplot_engine_v001.py --base <Base> --auto [--max-charts 12]
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
    "left": "#4c78a8",   # 左軸系列 · spec token --blue(依規範原配色)
    "right": "#439a9a",  # 右軸系列 · spec token --teal(依規範原配色;藍青分離度
                         # 偏低 ΔE 10.9,以「不同圖形 + 軸染色 + 直接標值」補償)
}
LINE_WIDTH = 1        # VISUAL LOCK 線粗 1
FILL_OPACITY = 0.75   # VISUAL LOCK 透明度 0.75
NICE_STEPS = (1.0, 2.0, 2.5, 5.0, 10.0)  # VISUAL LOCK 軸距

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
    """Ticks on the VISUAL LOCK step ladder 1/2/2.5/5/10 × 10^k."""
    if high <= low:
        high = low + 1.0
    span = high - low
    raw = span / max(1, target)
    magnitude = 10.0 ** math.floor(math.log10(raw))
    step = magnitude * 10.0
    for candidate in NICE_STEPS:
        if candidate * magnitude >= raw:
            step = candidate * magnitude
            break
    first = math.floor(low / step) * step
    ticks = [round(first, 10)]
    while ticks[-1] < high:  # 軸域必須完整涵蓋資料極值,不得截斷
        ticks.append(round(ticks[-1] + step, 10))
    return ticks


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


def render_chart_svg(labels: list[str], left_values: list[float], right_values: list[float],
                     left_name: str, right_name: str,
                     left_form: str, right_form: str) -> str:
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
    # recessive grid from the left axis only
    for tick in left_ticks:
        y = y_left(tick)
        parts.append(f'<line x1="{pad_left}" y1="{y:.1f}" x2="{width - pad_right}" y2="{y:.1f}" '
                     f'stroke="{TOKENS["soft"]}" stroke-width="1"/>')
    # marks -------------------------------------------------------------
    def series_marks(values, form, color, y_of, baseline_value, side_shift):
        out = []
        slot = plot_w / max(1, count)
        bar_w = max(2.0, slot * 0.42)
        if form == "bar":
            base_y = y_of(max(min(baseline_value, max(values)), min(min(values), baseline_value)))
            base_y = y_of(0.0) if min(values) <= 0 <= max(values) or min(values) >= 0 else y_of(baseline_value)
            for i, value in enumerate(values):
                x = x_center(i) + side_shift
                top = min(y_of(value), base_y)
                bar_h = max(1.0, abs(y_of(value) - base_y))
                out.append(f'<rect x="{x - bar_w / 2:.1f}" y="{top:.1f}" width="{bar_w:.1f}" '
                           f'height="{bar_h:.1f}" rx="1.5" fill="{color}" fill-opacity="{FILL_OPACITY}"/>')
            return out
        points = " ".join(f"{x_center(i) + side_shift:.1f},{y_of(v):.1f}" for i, v in enumerate(values))
        if form == "area":
            floor = y_of(max(min(values), 0.0) if min(values) >= 0 else 0.0)
            first_x = x_center(0) + side_shift
            last_x = x_center(count - 1) + side_shift
            out.append(f'<polygon points="{first_x:.1f},{floor:.1f} {points} {last_x:.1f},{floor:.1f}" '
                       f'fill="{color}" fill-opacity="{FILL_OPACITY * 0.4:.2f}"/>')
        out.append(f'<polyline points="{points}" fill="none" stroke="{color}" '
                   f'stroke-width="{LINE_WIDTH}" stroke-opacity="{FILL_OPACITY}" '
                   f'stroke-linejoin="round" stroke-linecap="round"/>')
        for i, value in enumerate(values):
            out.append(f'<circle cx="{x_center(i) + side_shift:.1f}" cy="{y_of(value):.1f}" r="1.6" '
                       f'fill="{color}"/>')
        return out

    parts.extend(series_marks(left_values, left_form, TOKENS["left"], y_left, 0.0, 0.0))
    parts.extend(series_marks(right_values, right_form, TOKENS["right"], y_right, 0.0, 0.0))

    # axes --------------------------------------------------------------
    parts.append(f'<line x1="{pad_left}" y1="{pad_top}" x2="{pad_left}" y2="{pad_top + plot_h}" '
                 f'stroke="{TOKENS["left"]}" stroke-width="{LINE_WIDTH}"/>')
    parts.append(f'<line x1="{width - pad_right}" y1="{pad_top}" x2="{width - pad_right}" '
                 f'y2="{pad_top + plot_h}" stroke="{TOKENS["right"]}" stroke-width="{LINE_WIDTH}"/>')
    for tick in left_ticks:
        parts.append(f'<text x="{pad_left - 6}" y="{y_left(tick) + 3.5:.1f}" text-anchor="end" '
                     f'fill="{TOKENS["left"]}">{_esc(format_tick(tick))}</text>')
    for tick in right_ticks:
        parts.append(f'<text x="{width - pad_right + 6}" y="{y_right(tick) + 3.5:.1f}" '
                     f'text-anchor="start" fill="{TOKENS["right"]}">{_esc(format_tick(tick))}</text>')
    # x labels (thinned)
    label_every = max(1, math.ceil(count / 10))
    for i in range(0, count, label_every):
        parts.append(f'<text x="{x_center(i):.1f}" y="{pad_top + plot_h + 16}" text-anchor="middle" '
                     f'fill="{TOKENS["muted"]}">{_esc(labels[i])}</text>')
    # direct end labels 直接標示末值
    parts.append(f'<text x="{x_center(count - 1) - 4:.1f}" y="{y_left(left_values[-1]) - 6:.1f}" '
                 f'text-anchor="end" font-weight="700" fill="{TOKENS["left"]}">'
                 f'{_esc(format_tick(left_values[-1]))}</text>')
    parts.append(f'<text x="{x_center(count - 1) + 4:.1f}" y="{y_right(right_values[-1]) - 6:.1f}" '
                 f'text-anchor="start" font-weight="700" fill="{TOKENS["right"]}">'
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
<div class="foot"><span>SOURCE · VDF DB · {_esc(source)}</span>
<span>VIA · VeritasAutoPlot {VERSION} · 🔒 VISUAL LOCK 線粗 {LINE_WIDTH} · 透明度 {FILL_OPACITY} · 軸距 1/2/2.5/5/10</span></div>
</div></body></html>
"""


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

    if args.list or (not args.auto and not (args.table and args.left and args.right)):
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
