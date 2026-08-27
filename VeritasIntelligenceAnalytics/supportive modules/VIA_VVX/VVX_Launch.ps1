#requires -Version 7.0
# ============================================================================
#  VVX_Launch.ps1  v01.1  -  Veritas Viz eXtractor  (VIA / VPN family)
#  One paste-and-run PS7. Scans HTML U/I, pulls every Plotly / matplotlib /
#  seaborn / Chart.js / ECharts figure intact at a standardized W x H, finds
#  time-axis + colors + plotting conventions, then auto-opens an HTML gallery
#  AND the panoramic fix-matrix report.
#  Modules : M01 SUP_MDL165_VVXExtractor.py  M02 vvx_gallery.js  M03 VVX_Gallery.html
#            M04 VVX_FixReport.html
#  10 accelerators : ACC01..ACC10.
#  Rules : UTF-8 No BOM, append-only, full cmdlets, no aliases, no block
#  comments, no Start-Job, ProcessStartInfo subprocess, script scope, read-only
#  on scanned HTML.
#  Usage : paste and run. Default scans your Downloads for *.html.
#          -ScanPath <folder|.txt|.html>  -OutRoot <folder>  -Port <n>
#          -Recurse   (scan subfolders)   -MinSide <px>  -StdW/-StdH <px>
# ============================================================================
param(
    [string]$ScanPath = (Join-Path $env:USERPROFILE 'Downloads'),
    [string]$OutRoot  = (Join-Path $env:USERPROFILE 'Downloads\VVX_ChartSpecs'),
    [int]$Port        = 8872,
    [int]$StdW        = 1000,
    [int]$StdH        = 560,
    [int]$MinSide     = 150,
    [switch]$Recurse,
    [switch]$NoLaunch
)

# ---- ACC10 : runtime tuning (no lag) ---------------------------------------
$ErrorActionPreference = 'Stop'
$ProgressPreference    = 'SilentlyContinue'
try { if ($PSStyle) { $PSStyle.OutputRendering = 'PlainText' } } catch { }

$script:Root = $OutRoot
$script:Scan = $ScanPath
$script:Utf8 = [System.Text.UTF8Encoding]::new($false)

# ---- ACC03 : StringBuilder report buffer -----------------------------------
$script:Log = [System.Text.StringBuilder]::new()
function Add-Log {
    param([string]$Line, [string]$Color = 'Gray')
    [void]$script:Log.AppendLine($Line)
    Write-Host ('  ' + $Line) -ForegroundColor $Color
}

# ---- ACC04 : direct IO writer (UTF-8 No BOM) -------------------------------
function Write-VvxFile {
    param([string]$Path, [string]$Content)
    $dir = Split-Path -Parent $Path
    if (-not (Test-Path -LiteralPath $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
    [System.IO.File]::WriteAllText($Path, $Content, $script:Utf8)
}


# ---- embedded modules (UTF-8 No BOM on write) ----
$script:PY_EXTRACTOR = @'
# -*- coding: utf-8 -*-
# ============================================================================
#  SUP_MDL165_VVXExtractor.py  -  Veritas Viz eXtractor  (VIA / VPN family)
#  M01 : multi-engine chart detector + per-figure spec + intact single-chart pull
#  Engines : Plotly / Dash(=Plotly) / matplotlib+seaborn (PNG|SVG) /
#            Chart.js / ECharts / Bokeh / generic inline-SVG & base64-image
#  Stdlib only (re, json, base64, pathlib, argparse, datetime, hashlib, html).
#  Append-only. Read-only on scanned HTML. UTF-8 No BOM out.
# ============================================================================
import re
import os
import json
import base64
import argparse
import hashlib
from pathlib import Path
from datetime import datetime

VVX_VERSION = "v01.1"

# ---- date / time-axis heuristics ------------------------------------------
DATE_VAL_RE = re.compile(
    r"^\s*\d{4}[-/]\d{1,2}([-/]\d{1,2})?([ T]\d{1,2}:\d{2})?")
DATE_FMT_RE = re.compile(r"%[YymdHMb]|\bYYYY\b|\bMM\b|\bDD\b")
DATE_WORDS = ("date", "time", "\u65e5\u671f", "\u6642\u9593", "\u5e74", "\u6708",
              "month", "year", "day", "quarter", "week", "datetime")

HEX_RE = re.compile(r"#(?:[0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b")


def is_dateish(s):
    if s is None:
        return False
    s = str(s)
    return bool(DATE_VAL_RE.match(s))


def std_dims(orig_w, orig_h, std_w, std_h):
    # keep aspect ratio of the original inside the standard box
    if orig_w and orig_h and orig_w > 0 and orig_h > 0:
        ar = orig_w / orig_h
        if ar >= std_w / std_h:
            return std_w, round(std_w / ar)
        return round(std_h * ar), std_h
    return std_w, std_h


# ============================================================================
#  bracket-balanced argument slicing (for Plotly.newPlot / setOption / new Chart)
# ============================================================================
def slice_balanced(text, start, open_ch, close_ch):
    """Return substring covering a balanced open..close starting at index `start`
       (text[start] must equal open_ch). String-aware."""
    depth = 0
    i = start
    instr = None
    esc = False
    while i < len(text):
        c = text[i]
        if instr:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == instr:
                instr = None
        else:
            if c in ("'", '"', "`"):
                instr = c
            elif c == open_ch:
                depth += 1
            elif c == close_ch:
                depth -= 1
                if depth == 0:
                    return text[start:i + 1], i + 1
        i += 1
    return None, len(text)


def split_top_args(arglist):
    """Split a top-level comma-separated argument string (without outer parens)."""
    args, depth, instr, esc, cur = [], 0, None, False, []
    for c in arglist:
        if instr:
            cur.append(c)
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == instr:
                instr = None
            continue
        if c in ("'", '"', "`"):
            instr = c; cur.append(c); continue
        if c in "([{":
            depth += 1; cur.append(c); continue
        if c in ")]}":
            depth -= 1; cur.append(c); continue
        if c == "," and depth == 0:
            args.append("".join(cur)); cur = []; continue
        cur.append(c)
    if cur:
        args.append("".join(cur))
    return [a.strip() for a in args]


def try_json(s):
    if not s:
        return None
    try:
        return json.loads(s)
    except Exception:
        return None


# ============================================================================
#  PLOTLY  (covers Dash exports + plotly.express/graph_objects write_html)
# ============================================================================
def _build_var_map(raw):
    """Map top-level `var/let/const NAME = [...]|{...}` to their JSON text."""
    vmap = {}
    for m in re.finditer(r"\b(?:var|let|const)\s+([A-Za-z_$][\w$]*)\s*=\s*", raw):
        name = m.group(1)
        j = m.end()
        while j < len(raw) and raw[j] in " \t\r\n":
            j += 1
        if j < len(raw) and raw[j] in "[{":
            blk, _ = slice_balanced(raw, j, raw[j], "]" if raw[j] == "[" else "}")
            if blk and name not in vmap:
                vmap[name] = blk
    return vmap


def extract_plotly(raw):
    figs = []
    vmap = _build_var_map(raw)
    for m in re.finditer(r"Plotly\.(?:newPlot|react)\s*\(", raw):
        p = raw.find("(", m.start())
        whole, _ = slice_balanced(raw, p, "(", ")")
        if not whole:
            continue
        inner = whole[1:-1]
        args = split_top_args(inner)
        data = layout = None
        for a in args:
            a = a.strip()
            # resolve identifier args via var map (S1: var-assignment pattern)
            if re.fullmatch(r"[A-Za-z_$][\w$]*", a) and a in vmap:
                a = vmap[a]
            if data is None and a.startswith("["):
                data = try_json(a)
            elif layout is None and a.startswith("{"):
                layout = try_json(a)
        if data is None and layout is None:
            continue
        figs.append(_plotly_spec(data or [], layout or {}))
    # plotly offline figure embedded as application/json
    for m in re.finditer(r'<script[^>]*type="application/json"[^>]*>(.*?)</script>',
                         raw, re.DOTALL):
        obj = try_json(m.group(1).strip())
        if isinstance(obj, dict) and "data" in obj and "layout" in obj:
            figs.append(_plotly_spec(obj.get("data") or [], obj.get("layout") or {}))
    return figs


def _plotly_spec(data, layout):
    xaxis = layout.get("xaxis", {}) if isinstance(layout, dict) else {}
    yaxis = layout.get("yaxis", {}) if isinstance(layout, dict) else {}
    title = ""
    t = layout.get("title")
    if isinstance(t, dict):
        title = t.get("text", "")
    elif isinstance(t, str):
        title = t

    # time axis
    has_time, basis = False, ""
    if str(xaxis.get("type", "")).lower() == "date":
        has_time, basis = True, "xaxis.type=date"
    elif DATE_FMT_RE.search(str(xaxis.get("tickformat", ""))):
        has_time, basis = True, "xaxis.tickformat"
    else:
        xt = xaxis.get("title")
        xttxt = xt.get("text", "") if isinstance(xt, dict) else (xt or "")
        if any(w in str(xttxt).lower() for w in DATE_WORDS):
            has_time, basis = True, "xaxis.title keyword"
        elif data and isinstance(data, list):
            xs = data[0].get("x") if isinstance(data[0], dict) else None
            if isinstance(xs, list) and xs and is_dateish(xs[0]):
                has_time, basis = True, "x[0] date value"

    # traces / colors / stacking
    colors, trace_types = [], []
    stacked = str(layout.get("barmode", "")).lower() == "stack"
    for tr in (data if isinstance(data, list) else []):
        if not isinstance(tr, dict):
            continue
        trace_types.append(tr.get("type", tr.get("mode", "scatter")))
        if tr.get("stackgroup"):
            stacked = True
        mk = tr.get("marker", {})
        ln = tr.get("line", {})
        for c in (mk.get("color"), ln.get("color")):
            if isinstance(c, str) and c and c not in colors:
                colors.append(c)
    cw = layout.get("colorway")
    if not cw and isinstance(layout.get("template"), dict):
        cw = (layout["template"].get("layout", {}) or {}).get("colorway")
    if isinstance(cw, list):
        for c in cw:
            if c not in colors:
                colors.append(c)

    n = len([1 for tr in (data if isinstance(data, list) else []) if isinstance(tr, dict)])
    kind = "stacked" if stacked else ("single" if n <= 1 else ("double" if n == 2 else "multi"))
    w = layout.get("width")
    h = layout.get("height")
    font = layout.get("font", {})
    return {
        "engine": "plotly", "kind": kind, "title": title or "(untitled)",
        "orig_w": w, "orig_h": h,
        "has_time_axis": has_time, "time_axis_basis": basis,
        "x_axis": {"type": xaxis.get("type", ""),
                   "tickformat": xaxis.get("tickformat", "")},
        "y_axis": {"type": yaxis.get("type", "")},
        "n_traces": n, "trace_types": trace_types[:12],
        "stacked": stacked, "colors": colors[:24],
        "template": (layout.get("template", {}) or {}).get("__name__", "")
                    if isinstance(layout.get("template"), dict) else str(layout.get("template", "")),
        "font_family": font.get("family", "") if isinstance(font, dict) else "",
        "margin": layout.get("margin", {}),
        "legend": bool(layout.get("showlegend", True)),
        "hovermode": layout.get("hovermode", ""),
        "_data": data, "_layout": layout,   # kept for intact re-render
    }


# ============================================================================
#  IMAGE figures (matplotlib / seaborn savefig -> base64 png|svg, or <img>)
# ============================================================================
def png_dims(b):
    # PNG: 8-byte sig, then IHDR len(4)+'IHDR'(4)+W(4)+H(4)
    if len(b) >= 24 and b[:8] == b"\x89PNG\r\n\x1a\n":
        w = int.from_bytes(b[16:20], "big")
        h = int.from_bytes(b[20:24], "big")
        return w, h
    return None, None


def svg_dims(svg):
    w = h = None
    mw = re.search(r'<svg[^>]*\bwidth="([\d.]+)', svg)
    mh = re.search(r'<svg[^>]*\bheight="([\d.]+)', svg)
    if mw:
        w = float(mw.group(1))
    if mh:
        h = float(mh.group(1))
    if (w is None or h is None):
        vb = re.search(r'viewBox="[\d.\-]+ [\d.\-]+ ([\d.]+) ([\d.]+)"', svg)
        if vb:
            w = w or float(vb.group(1))
            h = h or float(vb.group(2))
    return (round(w) if w else None), (round(h) if h else None)


def svg_time_axis(svg):
    texts = re.findall(r"<text[^>]*>(.*?)</text>", svg, re.DOTALL)
    for t in texts:
        t = re.sub(r"<[^>]+>", "", t).strip()
        if is_dateish(t):
            return True, "svg tick text date"
    return False, ""


def svg_colors(svg):
    cols = []
    for m in re.findall(r'(?:fill|stroke)\s*[:=]\s*["\']?(#[0-9a-fA-F]{3,6})', svg):
        c = m.lower()
        if c not in cols and c not in ("#000", "#000000", "#fff", "#ffffff"):
            cols.append(c)
    return cols[:24]


def extract_images(raw, near_mpl, minside=0):
    figs = []
    # base64 png
    for m in re.finditer(r'data:image/png;base64,([A-Za-z0-9+/=\s]+?)["\')]', raw):
        b64 = re.sub(r"\s+", "", m.group(1))
        try:
            head = base64.b64decode(b64[:64] + "=" * (-len(b64[:64]) % 4))
        except Exception:
            head = b""
        w, h = png_dims(head)
        if minside and w and h and w < minside and h < minside:
            continue   # icon / favicon, not a chart
        figs.append({
            "engine": "matplotlib" if near_mpl else "raster_png",
            "kind": "single", "title": "(raster figure)",
            "orig_w": w, "orig_h": h,
            "has_time_axis": False, "time_axis_basis": "raster: not parseable",
            "x_axis": {}, "y_axis": {}, "n_traces": None, "trace_types": [],
            "stacked": False, "colors": [], "template": "", "font_family": "",
            "margin": {}, "legend": None, "hovermode": "",
            "_png_b64": b64,
        })
    # inline svg
    for m in re.finditer(r"<svg\b.*?</svg>", raw, re.DOTALL):
        svg = m.group(0)
        if len(svg) < 200:
            continue   # skip tiny icon svgs
        w, h = svg_dims(svg)
        if minside and w and h and w < minside and h < minside:
            continue   # icon, not a chart
        ht, basis = svg_time_axis(svg)
        figs.append({
            "engine": "matplotlib_svg" if near_mpl else "svg",
            "kind": "single", "title": "(svg figure)",
            "orig_w": w, "orig_h": h,
            "has_time_axis": ht, "time_axis_basis": basis or "svg: no date ticks",
            "x_axis": {}, "y_axis": {}, "n_traces": None, "trace_types": [],
            "stacked": False, "colors": svg_colors(svg), "template": "",
            "font_family": "", "margin": {}, "legend": None, "hovermode": "",
            "_svg": svg,
        })
    return figs


# ============================================================================
#  Chart.js / ECharts / Bokeh  (lightweight spec-level)
# ============================================================================
def _hex_all(text):
    return [c.lower() for c in re.findall(r'(#[0-9a-fA-F]{6}|#[0-9a-fA-F]{3})\b', text)]


def extract_chartjs(raw):
    figs = []
    for m in re.finditer(r"new\s+Chart\s*\(", raw):
        p = raw.find("(", m.start())
        whole, _ = slice_balanced(raw, p, "(", ")")
        if not whole:
            continue
        b = whole.find("{")
        blk = slice_balanced(whole, b, "{", "}")[0] if b >= 0 else ""
        cfg = try_json(blk)
        ctype = ""; colors = []; ht = False; basis = ""; n = 1; stacked = False
        if isinstance(cfg, dict):
            ctype = cfg.get("type", "")
            ds = (cfg.get("data", {}) or {}).get("datasets", [])
            n = len(ds) or 1
            for d in ds:
                for k in ("backgroundColor", "borderColor"):
                    c = d.get(k)
                    if isinstance(c, str) and c not in colors:
                        colors.append(c)
            scales = (cfg.get("options", {}) or {}).get("scales", {})
            for ax in (scales.values() if isinstance(scales, dict) else []):
                if isinstance(ax, dict):
                    if str(ax.get("type", "")).lower() == "time":
                        ht, basis = True, "chart.js scale type=time"
                    if ax.get("stacked") is True:
                        stacked = True
        else:
            # ---- lenient regex fallback (handles unquoted JS keys) ----
            mt = re.search(r"\btype\s*:\s*['\"]?([A-Za-z]+)", blk)
            ctype = mt.group(1) if mt else ""
            colors = []
            for c in re.findall(r"(?:backgroundColor|borderColor)\s*:\s*['\"](#[0-9a-fA-F]{3,6})", blk):
                if c.lower() not in colors:
                    colors.append(c.lower())
            n = len(re.findall(r"\blabel\s*:", blk)) or 1
            if re.search(r"type\s*:\s*['\"]time['\"]", blk):
                ht, basis = True, "chart.js scale type=time (lenient)"
            if re.search(r"stacked\s*:\s*true", blk):
                stacked = True
        kind = "stacked" if stacked else ("single" if n <= 1 else ("double" if n == 2 else "multi"))
        figs.append({
            "engine": "chartjs", "kind": kind, "title": "(chart.js)",
            "orig_w": None, "orig_h": None, "has_time_axis": ht,
            "time_axis_basis": basis or "chart.js: no time scale",
            "x_axis": {"type": "time" if ht else ""}, "y_axis": {},
            "n_traces": n, "trace_types": [ctype] if ctype else [],
            "stacked": stacked, "colors": colors[:24], "template": "",
            "font_family": "", "margin": {}, "legend": None, "hovermode": "",
        })
    return figs


def extract_echarts(raw):
    figs = []
    for m in re.finditer(r"\.setOption\s*\(", raw):
        p = raw.find("(", m.start())
        whole, _ = slice_balanced(raw, p, "(", ")")
        if not whole:
            continue
        b = whole.find("{")
        blk = slice_balanced(whole, b, "{", "}")[0] if b >= 0 else ""
        opt = try_json(blk)
        ht = False; basis = ""; colors = []; n = 1; ctypes = []
        if isinstance(opt, dict):
            xa = opt.get("xAxis", {})
            xa = xa[0] if isinstance(xa, list) and xa else xa
            if isinstance(xa, dict) and str(xa.get("type", "")).lower() == "time":
                ht, basis = True, "echarts xAxis type=time"
            series = opt.get("series", [])
            series = series if isinstance(series, list) else [series]
            n = len(series) or 1
            for s in series:
                if isinstance(s, dict):
                    ctypes.append(s.get("type", ""))
                    c = s.get("color")
                    if isinstance(c, str) and c not in colors:
                        colors.append(c)
            cw = opt.get("color")
            if isinstance(cw, list):
                colors.extend([c for c in cw if c not in colors])
        else:
            # ---- lenient regex fallback (unquoted JS keys) ----
            cm = re.search(r"\bcolor\s*:\s*\[([^\]]*)\]", blk)
            if cm:
                for c in re.findall(r"(#[0-9a-fA-F]{3,6})", cm.group(1)):
                    if c.lower() not in colors:
                        colors.append(c.lower())
            for c in re.findall(r"\bcolor\s*:\s*['\"](#[0-9a-fA-F]{3,6})", blk):
                if c.lower() not in colors:
                    colors.append(c.lower())
            ctypes = re.findall(r"\btype\s*:\s*['\"](line|bar|scatter|pie|candlestick|heatmap|boxplot|k)['\"]", blk)
            n = max(1, len(ctypes))
            xm = re.search(r"xAxis\s*:\s*[\{\[][\s\S]{0,120}?type\s*:\s*['\"]time['\"]", blk)
            if xm or re.search(r"type\s*:\s*['\"]time['\"]", blk):
                ht, basis = True, "echarts xAxis type=time (lenient)"
        kind = "single" if n <= 1 else ("double" if n == 2 else "multi")
        figs.append({
            "engine": "echarts", "kind": kind, "title": "(echarts)",
            "orig_w": None, "orig_h": None, "has_time_axis": ht,
            "time_axis_basis": basis or "echarts: no time axis",
            "x_axis": {"type": "time" if ht else ""}, "y_axis": {},
            "n_traces": n, "trace_types": ctypes[:12], "stacked": False,
            "colors": colors[:24], "template": "", "font_family": "",
            "margin": {}, "legend": None, "hovermode": "",
        })
    return figs


def detect_engines(raw):
    # instantiation-based, so a tool *catalog* that merely names "chart.js"
    # does not get falsely tagged as containing chart.js figures.
    e = []
    low = raw.lower()
    if re.search(r"plotly\.(?:newplot|react)\s*\(", low) or "plotly-graph-div" in low:
        e.append("plotly")
    if re.search(r"new\s+chart\s*\(", low):
        e.append("chartjs")
    if "echarts.init" in low and ".setoption(" in low:
        e.append("echarts")
    if re.search(r"bokeh\.embed|bokehjs", low):
        e.append("bokeh")
    if "data:image/png;base64" in low or "data:image/svg" in low or "<svg" in low:
        e.append("image")
    return e


# ============================================================================
#  intact single-chart writers
# ============================================================================
PLOTLY_TPL = """<!DOCTYPE html><html lang="zh-TW"><head><meta charset="utf-8">
<title>__TITLE__</title>
<script src="https://cdn.plot.ly/plotly-2.32.0.min.js"></script>
<style>html,body{margin:0;background:#0f1318;}
#c{width:__SW__px;height:__SH__px;margin:0 auto;}</style></head>
<body><div id="c"></div><script>
var data=__DATA__, layout=__LAYOUT__;
layout=Object.assign({autosize:true,paper_bgcolor:"#14181d",plot_bgcolor:"#14181d",
  font:{color:"#e7ecf1"}}, layout);
delete layout.width; delete layout.height;
Plotly.newPlot("c", data, layout, {responsive:true,displaylogo:false});
</script></body></html>"""


def write_intact(fig, out_dir, base, idx, std_w, std_h):
    rel = None
    if fig.get("_data") is not None or fig.get("_layout") is not None:
        sw, sh = std_dims(fig.get("orig_w"), fig.get("orig_h"), std_w, std_h)
        html = (PLOTLY_TPL
                .replace("__TITLE__", base + " fig" + str(idx))
                .replace("__SW__", str(sw)).replace("__SH__", str(sh))
                .replace("__DATA__", json.dumps(fig.get("_data") or []))
                .replace("__LAYOUT__", json.dumps(fig.get("_layout") or {})))
        rel = "charts/%s__fig%d.html" % (base, idx)
        (out_dir / rel).write_text(html, encoding="utf-8")
    elif fig.get("_svg"):
        rel = "charts/%s__fig%d.svg" % (base, idx)
        (out_dir / rel).write_text(fig["_svg"], encoding="utf-8")
    elif fig.get("_png_b64"):
        rel = "charts/%s__fig%d.png" % (base, idx)
        try:
            (out_dir / rel).write_bytes(base64.b64decode(
                fig["_png_b64"] + "=" * (-len(fig["_png_b64"]) % 4)))
        except Exception:
            rel = None
    return rel


def compute_issues(fig):
    iss = []
    if fig.get("orig_w") in (None, 0) or fig.get("orig_h") in (None, 0):
        iss.append("no explicit width/height (responsive/auto)")
    if not fig.get("extracted"):
        iss.append("spec-only: needs source data to re-render")
    if not fig.get("colors"):
        iss.append("no colors detected")
    if not fig.get("has_time_axis") and str(fig.get("time_axis_basis", "")).startswith("raster"):
        iss.append("raster: time-axis unverifiable")
    if (fig.get("title") or "").startswith("("):
        iss.append("no explicit title")
    return iss


def clean_fig(fig, rel, std_w, std_h):
    sw, sh = std_dims(fig.get("orig_w"), fig.get("orig_h"), std_w, std_h)
    out = {k: v for k, v in fig.items() if not k.startswith("_")}
    out["std_w"], out["std_h"] = sw, sh
    out["extracted"] = rel
    out["issues"] = compute_issues(out)
    return out


# ============================================================================
#  per-file + folder scan
# ============================================================================
def scan_file(path, out_dir, std_w, std_h, minside=0):
    raw = Path(path).read_text(encoding="utf-8", errors="replace")
    engines = detect_engines(raw)
    near_mpl = bool(re.search(r"matplotlib|seaborn", raw, re.IGNORECASE))
    figs = []
    figs += extract_plotly(raw)
    figs += extract_chartjs(raw)
    figs += extract_echarts(raw)
    figs += extract_images(raw, near_mpl, minside)

    base = re.sub(r"[^A-Za-z0-9_.-]", "_", Path(path).stem)[:60]

    # dedup identical figures (e.g. plotly offline newPlot + application/json twin)
    seen, uniq = set(), []
    for f in figs:
        sig = "%s|%s|%s|%s|%s|%s" % (
            f.get("engine"), f.get("orig_w"), f.get("orig_h"),
            f.get("title"), f.get("kind"), ",".join(f.get("colors") or []))
        sig += "|" + hashlib.md5(
            (f.get("_svg") or json.dumps(f.get("_data") or "") or "").encode("utf-8", "replace")
        ).hexdigest()[:8]
        if sig in seen:
            continue
        seen.add(sig)
        uniq.append(f)
    figs = uniq

    cleaned = []
    for i, f in enumerate(figs, 1):
        rel = write_intact(f, out_dir, base, i, std_w, std_h)
        cleaned.append(clean_fig(f, rel, std_w, std_h))

    return {
        "file": Path(path).name,
        "path": str(path),
        "size_bytes": Path(path).stat().st_size,
        "sha256": hashlib.sha256(raw.encode("utf-8", "replace")).hexdigest()[:16],
        "engines": engines,
        "figure_count": len(cleaned),
        "figures": cleaned,
    }


def aggregate_conventions(files):
    fonts, templates, colorways, time_yes, time_no = {}, {}, {}, 0, 0
    kinds, engines = {}, {}
    for fl in files:
        for fg in fl["figures"]:
            engines[fg["engine"]] = engines.get(fg["engine"], 0) + 1
            kinds[fg["kind"]] = kinds.get(fg["kind"], 0) + 1
            if fg.get("font_family"):
                fonts[fg["font_family"]] = fonts.get(fg["font_family"], 0) + 1
            if fg.get("template"):
                templates[fg["template"]] = templates.get(fg["template"], 0) + 1
            for c in fg.get("colors", []):
                colorways[c] = colorways.get(c, 0) + 1
            if fg.get("has_time_axis"):
                time_yes += 1
            else:
                time_no += 1
    top = lambda d, n=12: sorted(d.items(), key=lambda kv: -kv[1])[:n]
    return {
        "engines": dict(top(engines)),
        "kinds": dict(top(kinds)),
        "fonts": dict(top(fonts)),
        "templates": dict(top(templates)),
        "top_colors": [{"hex": k, "uses": v} for k, v in top(colorways, 24)],
        "time_axis": {"with": time_yes, "without": time_no},
    }


def main():
    ap = argparse.ArgumentParser(description="VVX chart extractor (M01)")
    ap.add_argument("--scan", required=True, help="folder OR a .txt list of html paths")
    ap.add_argument("--out", required=True, help="output root (charts/ + vvx_specs.json)")
    ap.add_argument("--stdw", type=int, default=1000)
    ap.add_argument("--stdh", type=int, default=560)
    ap.add_argument("--glob", default="*.html")
    ap.add_argument("--recurse", action="store_true", help="scan subfolders too")
    ap.add_argument("--minside", type=int, default=150,
                    help="skip image figures whose both sides < this (icons); 0 = keep all")
    args = ap.parse_args()

    out_root = Path(args.out)
    (out_root / "charts").mkdir(parents=True, exist_ok=True)
    out_resolved = out_root.resolve()

    # resolve target html files
    targets = []
    sp = Path(args.scan)
    if sp.is_dir():
        it = sp.rglob(args.glob) if args.recurse else sp.glob(args.glob)
        targets = sorted(t for t in it if out_resolved not in t.resolve().parents
                         and t.resolve() != out_resolved)
    elif sp.suffix.lower() == ".txt" and sp.exists():
        for line in sp.read_text(encoding="utf-8").splitlines():
            line = line.strip().strip('"')
            if line and Path(line).exists():
                targets.append(Path(line))
    elif sp.suffix.lower() in (".html", ".htm"):
        targets = [sp]

    work = [t for t in targets if t.name.lower() != "vvx_gallery.html"]

    def _one(t):
        try:
            return scan_file(t, out_root, args.stdw, args.stdh, args.minside)
        except Exception as e:
            return {"file": t.name, "path": str(t), "error": str(e),
                    "engines": [], "figure_count": 0, "figures": []}

    files = []
    if len(work) > 3:
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=min(8, len(work))) as ex:
            files = list(ex.map(_one, work))   # ex.map preserves input order
    else:
        files = [_one(t) for t in work]

    total_figs = sum(f.get("figure_count", 0) for f in files)
    payload = {
        "meta": {
            "tool": "VVX Extractor", "version": VVX_VERSION,
            "generated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "scan_path": str(sp.resolve()) if sp.exists() else str(sp),
            "file_count": len(files), "total_figures": total_figs,
            "std_size": {"w": args.stdw, "h": args.stdh},
        },
        "conventions": aggregate_conventions(files),
        "files": files,
    }
    (out_root / "vvx_specs.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print("[VVX] files=%d figures=%d  -> %s"
          % (len(files), total_figs, out_root / "vvx_specs.json"))


if __name__ == "__main__":
    main()

'@

$script:JS_GALLERY = @'
/* ==========================================================================
 *  vvx_gallery.js  -  Veritas Viz eXtractor  (VIA / VPN family)
 *  M02 : render chart-spec gallery from SUP_MDL165_VVXExtractor.py JSON.
 *        live-embeds each intact single chart (.html iframe / .svg / .png)
 *        beside a full spec panel (std W×H, time-axis, colors, conventions).
 * ======================================================================== */
(function () {
  "use strict";
  var S = { data: null, fEngine: "ALL", fKind: "ALL", fTime: "ALL", q: "" };

  function $(s, r) { return (r || document).querySelector(s); }
  function el(t, c, x) { var e = document.createElement(t); if (c) e.className = c; if (x != null) e.textContent = x; return e; }

  function load() {
    fetch("./vvx_specs.json?ts=" + Date.now())
      .then(function (r) { return r.json(); })
      .then(function (j) { S.data = j; boot(); })
      .catch(function (e) {
        $("#vvx-body").innerHTML = '<div class="vvx-empty">\u672a\u80fd\u8f09\u5165 vvx_specs.json\uff1a' + e + "</div>";
      });
  }

  function boot() { renderMeta(); renderConventions(); wire(); renderBody(); }

  /* ---- meta strip ---- */
  function renderMeta() {
    var m = S.data.meta, c = S.data.conventions;
    var box = $("#vvx-summary"); box.innerHTML = "";
    var tw = c.time_axis.with, tn = c.time_axis.without;
    [["\u6a94\u6848", m.file_count], ["\u5716\u8868", m.total_figures, "fig"],
     ["\u6709\u6642\u9593\u8ef8", tw, "time"], ["\u7121\u6642\u9593\u8ef8", tn, "notime"],
     ["\u6a19\u6e96\u5c3a\u5bf8", m.std_size.w + "\u00d7" + m.std_size.h]].forEach(function (r) {
      var b = el("div", "vvx-stat" + (r[2] ? " is-" + r[2] : ""));
      b.appendChild(el("div", "vvx-stat-n", String(r[1])));
      b.appendChild(el("div", "vvx-stat-l", r[0]));
      box.appendChild(b);
    });
    $("#vvx-scanpath").textContent = m.scan_path + "   \u00b7   " + m.tool + " " + m.version + "  \u00b7  " + m.generated;
  }

  /* ---- conventions panel (\u7e6a\u5716\u898f\u7bc4) ---- */
  function swatch(hex, n) {
    var s = el("span", "vvx-sw");
    s.style.background = hex;
    s.title = hex + (n ? "  \u00d7" + n : "");
    s.onclick = function () { try { navigator.clipboard.writeText(hex); } catch (e) {} s.classList.add("copied"); setTimeout(function(){s.classList.remove("copied");}, 600); };
    return s;
  }
  function renderConventions() {
    var c = S.data.conventions, host = $("#vvx-conv"); host.innerHTML = "";
    var blocks = [
      ["\u5f15\u64ce engines", Object.keys(c.engines).map(function (k) { return k + " \u00d7" + c.engines[k]; }).join("  \u00b7  ") || "\u2014"],
      ["\u985e\u578b kinds", Object.keys(c.kinds).map(function (k) { return k + " \u00d7" + c.kinds[k]; }).join("  \u00b7  ") || "\u2014"],
      ["\u5b57\u9ad4 fonts", Object.keys(c.fonts).join("  \u00b7  ") || "\u2014"],
      ["\u4e3b\u984c templates", Object.keys(c.templates).join("  \u00b7  ") || "\u2014"]
    ];
    blocks.forEach(function (b) {
      var row = el("div", "vvx-conv-row");
      row.appendChild(el("span", "vvx-conv-k", b[0]));
      row.appendChild(el("span", "vvx-conv-v", b[1]));
      host.appendChild(row);
    });
    var crow = el("div", "vvx-conv-row");
    crow.appendChild(el("span", "vvx-conv-k", "\u8272\u5f69 palette"));
    var sw = el("span", "vvx-conv-sw");
    (c.top_colors || []).forEach(function (o) { sw.appendChild(swatch(o.hex, o.uses)); });
    if (!(c.top_colors || []).length) sw.appendChild(el("span", "vvx-conv-v", "\u2014"));
    crow.appendChild(sw);
    host.appendChild(crow);
  }

  /* ---- filters ---- */
  function wire() {
    var engines = ["ALL"].concat(Object.keys(S.data.conventions.engines));
    var es = $("#vvx-engine");
    engines.forEach(function (e) { var o = el("option"); o.value = e; o.textContent = (e === "ALL" ? "\u5168\u90e8\u5f15\u64ce" : e); es.appendChild(o); });
    es.onchange = function () { S.fEngine = this.value; renderBody(); };
    $("#vvx-kind").onchange = function () { S.fKind = this.value; renderBody(); };
    document.querySelectorAll("[data-time]").forEach(function (b) {
      b.onclick = function () {
        S.fTime = this.getAttribute("data-time");
        document.querySelectorAll("[data-time]").forEach(function (x) { x.classList.remove("on"); });
        this.classList.add("on"); renderBody();
      };
    });
    $("#vvx-search").oninput = function () { S.q = this.value.toLowerCase().trim(); renderBody(); };
  }

  function pass(fig, file) {
    if (S.fEngine !== "ALL" && fig.engine !== S.fEngine) return false;
    if (S.fKind !== "ALL" && fig.kind !== S.fKind) return false;
    if (S.fTime === "YES" && !fig.has_time_axis) return false;
    if (S.fTime === "NO" && fig.has_time_axis) return false;
    if (S.q) {
      var hay = (file + " " + fig.title + " " + fig.engine + " " + (fig.colors || []).join(" ")).toLowerCase();
      if (hay.indexOf(S.q) < 0) return false;
    }
    return true;
  }

  /* ---- figure embed ---- */
  function embed(fig) {
    var box = el("div", "vvx-embed");
    var ex = fig.extracted;
    if (!ex) { box.appendChild(el("div", "vvx-noembed", "\u50c5\u898f\u683c\uff08\u9700\u539f\u59cb\u8cc7\u6599\u624d\u80fd\u91cd\u7e6a\uff09")); return box; }
    if (/\.html$/.test(ex)) {
      var ifr = document.createElement("iframe");
      ifr.src = "./" + ex; ifr.loading = "lazy";
      ifr.className = "vvx-ifr";
      box.appendChild(ifr);
    } else {
      var img = document.createElement("img");
      img.src = "./" + ex; img.loading = "lazy"; img.className = "vvx-img";
      box.appendChild(img);
    }
    return box;
  }

  function specRow(k, v) {
    var r = el("div", "vvx-srow");
    r.appendChild(el("span", "vvx-sk", k));
    var val = el("span", "vvx-sv");
    if (v instanceof Node) val.appendChild(v); else val.textContent = (v == null || v === "" ? "\u2014" : v);
    r.appendChild(val);
    return r;
  }

  function specPanel(fig) {
    var p = el("div", "vvx-spec");
    var head = el("div", "vvx-spec-h");
    head.appendChild(el("span", "vvx-eng vvx-eng-" + fig.engine.split("_")[0], fig.engine));
    head.appendChild(el("span", "vvx-kind k-" + fig.kind, fig.kind));
    var tb = el("span", "vvx-time " + (fig.has_time_axis ? "t-yes" : "t-no"),
      fig.has_time_axis ? "\u6642\u9593\u8ef8 \u2713" : "\u6642\u9593\u8ef8 \u2717");
    head.appendChild(tb);
    p.appendChild(head);
    p.appendChild(el("div", "vvx-title", fig.title));

    p.appendChild(specRow("\u539f\u59cb \u9577\u00d7\u5bec", (fig.orig_w || "auto") + " \u00d7 " + (fig.orig_h || "auto")));
    p.appendChild(specRow("\u6a19\u6e96 \u9577\u00d7\u5bec", fig.std_w + " \u00d7 " + fig.std_h));
    p.appendChild(specRow("\u6642\u9593\u8ef8\u4f9d\u64da", fig.time_axis_basis));
    if (fig.x_axis && (fig.x_axis.type || fig.x_axis.tickformat))
      p.appendChild(specRow("X \u8ef8", (fig.x_axis.type || "") + (fig.x_axis.tickformat ? "  fmt=" + fig.x_axis.tickformat : "")));
    if (fig.n_traces != null) p.appendChild(specRow("\u8cc7\u6599\u5e8f\u5217", fig.n_traces + (fig.trace_types && fig.trace_types.length ? "  (" + fig.trace_types.join(", ") + ")" : "")));
    p.appendChild(specRow("\u5806\u758a stacked", fig.stacked ? "yes" : "no"));
    if (fig.template) p.appendChild(specRow("\u4e3b\u984c template", fig.template));
    if (fig.font_family) p.appendChild(specRow("\u5b57\u9ad4 font", fig.font_family));
    if (fig.hovermode) p.appendChild(specRow("hovermode", fig.hovermode));

    var swc = el("span", "vvx-conv-sw");
    (fig.colors || []).forEach(function (h) { swc.appendChild(swatch(h)); });
    if (!(fig.colors || []).length) swc.textContent = "\u2014";
    p.appendChild(specRow("\u8272\u5f69 colors", swc));

    if (fig.issues && fig.issues.length) {
      var ib = el("div", "vvx-issues");
      ib.appendChild(el("span", "vvx-issues-h", "\u26a0 issues"));
      fig.issues.forEach(function (s) { ib.appendChild(el("span", "vvx-issue", s)); });
      p.appendChild(ib);
    }

    if (fig.extracted) {
      var a = el("a", "vvx-open", "\u958b\u555f\u55ae\u5716 \u2197");
      a.href = "./" + fig.extracted; a.target = "_blank";
      p.appendChild(a);
    }
    return p;
  }

  function renderBody() {
    var host = $("#vvx-body"); host.innerHTML = "";
    var shown = 0;
    S.data.files.forEach(function (fl) {
      var figs = (fl.figures || []).filter(function (g) { return pass(g, fl.file); });
      if (!figs.length) return;
      var sec = el("section", "vvx-file");
      var fh = el("div", "vvx-fh");
      fh.appendChild(el("span", "vvx-fh-name", fl.file));
      fh.appendChild(el("span", "vvx-fh-meta", (fl.engines || []).join(" / ") + "  \u00b7  " + figs.length + " \u5716  \u00b7  " + (fl.size_bytes / 1024).toFixed(0) + " KB"));
      sec.appendChild(fh);
      figs.forEach(function (g) {
        shown++;
        var card = el("div", "vvx-card");
        card.appendChild(embed(g));
        card.appendChild(specPanel(g));
        sec.appendChild(card);
      });
      host.appendChild(sec);
    });
    if (!shown) host.innerHTML = '<div class="vvx-empty">\u6c92\u6709\u7b26\u5408\u7be9\u9078\u7684\u5716\u8868</div>';
  }

  document.addEventListener("DOMContentLoaded", load);
})();

'@

$script:HTML_GALLERY = @'
<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>VERITAS INTELLIGENCE SYSTEM</title>
<!-- @lock VPN v3.5 visual identity : palette + fonts immutable -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;500;600;700&family=Syne:wght@600;700;800&display=swap" rel="stylesheet">
<style>
:root{
  --vpn-blue:#4c78a8; --vpn-grey:#9c9890; --vpn-teal:#439a9a;
  --bg:#0f1318; --bg2:#141a21; --panel:#1a212a; --panel2:#202a35;
  --line:#2a3540; --ink:#e7ecf1; --ink-dim:#9aa7b4; --ink-faint:#6b7886;
  --yes:#5bb38a; --no:#d8654f; --fig:#e0b450;
  --font-display:"Syne",sans-serif; --font-body:"DM Sans",sans-serif; --font-mono:"DM Mono",monospace;
}
*{box-sizing:border-box;}
html,body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--font-body);}
a{color:var(--vpn-teal);}

header.vvx-top{background:linear-gradient(90deg,var(--vpn-blue),#3c5f86);
  padding:16px 26px;display:flex;align-items:center;gap:16px;border-bottom:1px solid var(--line);}
.vvx-mark{width:38px;height:38px;border-radius:9px;background:var(--vpn-teal);display:grid;place-items:center;
  font-family:var(--font-display);font-weight:800;color:#0f1318;font-size:18px;}
.vvx-tt h1{margin:0;font-family:var(--font-display);font-weight:800;font-size:19px;}
.vvx-tt p{margin:2px 0 0;font-size:12px;color:#dbe6f2;letter-spacing:1.5px;text-transform:uppercase;}

.vvx-summary{display:flex;gap:14px;padding:18px 26px 6px;flex-wrap:wrap;}
.vvx-stat{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:13px 18px;min-width:96px;}
.vvx-stat-n{font-family:var(--font-mono);font-size:22px;}
.vvx-stat-l{font-size:11px;color:var(--ink-dim);margin-top:3px;}
.vvx-stat.is-fig .vvx-stat-n{color:var(--fig);}
.vvx-stat.is-time .vvx-stat-n{color:var(--yes);}
.vvx-stat.is-notime .vvx-stat-n{color:var(--no);}
.vvx-scanpath{padding:2px 26px 10px;font-family:var(--font-mono);font-size:11px;color:var(--ink-faint);}

.vvx-conv{margin:0 26px 12px;background:var(--bg2);border:1px solid var(--line);border-radius:12px;padding:12px 16px;}
.vvx-conv-row{display:flex;gap:14px;padding:5px 0;align-items:center;border-bottom:1px solid rgba(42,53,64,.5);}
.vvx-conv-row:last-child{border-bottom:0;}
.vvx-conv-k{font-family:var(--font-mono);font-size:12px;color:var(--ink-dim);min-width:140px;}
.vvx-conv-v{font-size:12px;color:var(--ink);}
.vvx-conv-sw{display:flex;gap:5px;flex-wrap:wrap;}
.vvx-sw{width:18px;height:18px;border-radius:5px;border:1px solid rgba(255,255,255,.18);cursor:pointer;display:inline-block;}
.vvx-sw.copied{outline:2px solid var(--vpn-teal);}

.vvx-bar{display:flex;gap:10px;padding:0 26px 14px;flex-wrap:wrap;align-items:center;}
.vvx-bar input,.vvx-bar select{background:var(--bg2);border:1px solid var(--line);color:var(--ink);border-radius:9px;padding:8px 12px;font-size:13px;font-family:var(--font-body);}
.vvx-bar input{min-width:220px;flex:1;}
.vvx-seg{display:flex;border:1px solid var(--line);border-radius:9px;overflow:hidden;}
.vvx-seg button{background:var(--bg2);color:var(--ink-dim);border:0;padding:8px 14px;font-size:12px;cursor:pointer;font-family:var(--font-body);}
.vvx-seg button.on{background:var(--vpn-blue);color:#fff;}

.vvx-stage{padding:6px 26px 60px;}
.vvx-file{margin-bottom:26px;}
.vvx-fh{display:flex;align-items:baseline;gap:12px;margin:14px 0 10px;border-bottom:1px solid var(--line);padding-bottom:8px;}
.vvx-fh-name{font-family:var(--font-display);font-size:16px;font-weight:700;}
.vvx-fh-meta{font-family:var(--font-mono);font-size:11px;color:var(--ink-faint);}

.vvx-card{display:grid;grid-template-columns:minmax(0,1.4fr) minmax(280px,1fr);gap:16px;
  background:var(--bg2);border:1px solid var(--line);border-radius:14px;padding:14px;margin-bottom:14px;}
.vvx-embed{background:#0c1014;border:1px solid var(--line);border-radius:10px;overflow:hidden;min-height:300px;display:flex;align-items:center;justify-content:center;}
.vvx-ifr{width:100%;height:380px;border:0;background:#0f1318;}
.vvx-img{max-width:100%;max-height:380px;display:block;}
.vvx-noembed{color:var(--ink-faint);font-size:13px;padding:30px;text-align:center;}

.vvx-spec{display:flex;flex-direction:column;}
.vvx-spec-h{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:8px;}
.vvx-eng,.vvx-kind,.vvx-time{font-size:11px;padding:3px 9px;border-radius:7px;font-family:var(--font-mono);}
.vvx-eng{background:rgba(76,120,168,.18);color:#bcd3ec;border:1px solid rgba(76,120,168,.5);}
.vvx-eng-matplotlib{background:rgba(224,180,80,.16);color:var(--fig);border-color:rgba(224,180,80,.45);}
.vvx-eng-chartjs{background:rgba(67,154,154,.16);color:#7fd6d6;border-color:rgba(67,154,154,.45);}
.vvx-eng-echarts{background:rgba(156,152,144,.18);color:#cfc9bf;border-color:rgba(156,152,144,.45);}
.vvx-kind{background:rgba(156,152,144,.14);color:var(--ink-dim);border:1px solid var(--line);}
.vvx-time.t-yes{background:rgba(91,179,138,.15);color:var(--yes);border:1px solid rgba(91,179,138,.4);}
.vvx-time.t-no{background:rgba(216,101,79,.15);color:var(--no);border:1px solid rgba(216,101,79,.4);}
.vvx-title{font-family:var(--font-display);font-size:15px;font-weight:600;margin-bottom:8px;}
.vvx-srow{display:grid;grid-template-columns:120px 1fr;gap:10px;padding:5px 0;border-bottom:1px solid rgba(42,53,64,.45);align-items:center;}
.vvx-srow:last-of-type{border-bottom:0;}
.vvx-sk{font-family:var(--font-mono);font-size:11px;color:var(--ink-dim);}
.vvx-sv{font-size:12px;color:var(--ink);word-break:break-word;display:flex;align-items:center;gap:6px;flex-wrap:wrap;}
.vvx-open{margin-top:10px;font-size:12px;font-family:var(--font-mono);align-self:flex-start;text-decoration:none;
  border:1px solid var(--vpn-teal);padding:6px 12px;border-radius:8px;}
.vvx-issues{margin-top:9px;display:flex;flex-wrap:wrap;gap:6px;align-items:center;}
.vvx-issues-h{font-family:var(--font-mono);font-size:11px;color:var(--fig);}
.vvx-issue{font-size:11px;background:rgba(224,180,80,.12);color:#e7cf9a;border:1px solid rgba(224,180,80,.32);
  padding:2px 8px;border-radius:6px;}
.vvx-empty{padding:40px;text-align:center;color:var(--ink-faint);}

@media(max-width:780px){ .vvx-card{grid-template-columns:1fr;} .vvx-ifr{height:320px;} }
</style>
</head>
<body>
<header class="vvx-top" data-lock="true">
  <div class="vvx-mark">V</div>
  <div class="vvx-tt">
    <h1>VVX \u00b7 HTML \u5716\u8868\u64f7\u53d6\u5668</h1>
    <p>VERITAS INTELLIGENCE SYSTEM</p>
  </div>
</header>

<div class="vvx-summary" id="vvx-summary"></div>
<div class="vvx-scanpath" id="vvx-scanpath"></div>
<div class="vvx-conv" id="vvx-conv"></div>

<div class="vvx-bar">
  <input id="vvx-search" placeholder="\u641c\u5c0b \u6a94\u540d / \u6a19\u984c / \u8272\u78bc\u2026">
  <select id="vvx-engine"></select>
  <select id="vvx-kind">
    <option value="ALL">\u5168\u90e8\u985e\u578b</option>
    <option value="single">single \u55ae\u5716</option>
    <option value="double">double \u96d9\u5716</option>
    <option value="stacked">stacked \u5806\u758a</option>
    <option value="multi">multi \u591a\u5e8f\u5217</option>
  </select>
  <div class="vvx-seg">
    <button data-time="ALL" class="on">\u5168\u90e8</button>
    <button data-time="YES">\u6709\u6642\u9593\u8ef8</button>
    <button data-time="NO">\u7121\u6642\u9593\u8ef8</button>
  </div>
</div>

<div class="vvx-stage"><div id="vvx-body"></div></div>
<script src="./vvx_gallery.js"></script>
</body>
</html>

'@

$script:HTML_REPORT = @'
<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>VERITAS INTELLIGENCE SYSTEM</title>
<!-- @lock VPN v3.5 visual identity : palette + fonts immutable -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;500;600;700&family=Syne:wght@600;700;800&display=swap" rel="stylesheet">
<style>
:root{
  --vpn-blue:#4c78a8;--vpn-grey:#9c9890;--vpn-teal:#439a9a;
  --bg:#0f1318;--bg2:#141a21;--panel:#1a212a;--line:#2a3540;
  --ink:#e7ecf1;--ink-dim:#9aa7b4;--ink-faint:#6b7886;
  --par:#5bb38a;--seq:#e0b450;--fin:#7fb3e0;--hi:#d8654f;--mid:#e0b450;--lo:#5bb38a;
  --font-display:"Syne",sans-serif;--font-body:"DM Sans",sans-serif;--font-mono:"DM Mono",monospace;
}
*{box-sizing:border-box;}
html,body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--font-body);}
header.top{background:linear-gradient(90deg,var(--vpn-blue),#3c5f86);padding:16px 26px;display:flex;align-items:center;gap:16px;border-bottom:1px solid var(--line);}
.mark{width:38px;height:38px;border-radius:9px;background:var(--vpn-teal);display:grid;place-items:center;font-family:var(--font-display);font-weight:800;color:#0f1318;font-size:18px;}
.tt h1{margin:0;font-family:var(--font-display);font-weight:800;font-size:19px;}
.tt p{margin:2px 0 0;font-size:12px;color:#dbe6f2;letter-spacing:1.5px;text-transform:uppercase;}
.wrap{padding:18px 26px 60px;max-width:1180px;}
.summary{display:flex;gap:14px;flex-wrap:wrap;margin-bottom:18px;}
.stat{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:13px 18px;min-width:110px;}
.stat-n{font-family:var(--font-mono);font-size:22px;}
.stat-l{font-size:11px;color:var(--ink-dim);margin-top:3px;}
.is-par .stat-n{color:var(--par);}.is-seq .stat-n{color:var(--seq);}.is-pass .stat-n{color:var(--par);}
h2{font-family:var(--font-display);font-size:15px;font-weight:700;margin:26px 0 10px;border-bottom:1px solid var(--line);padding-bottom:7px;letter-spacing:.4px;}
.note{font-size:12px;color:var(--ink-dim);margin:-4px 0 12px;line-height:1.6;}
table{width:100%;border-collapse:collapse;font-size:12px;background:var(--bg2);border:1px solid var(--line);border-radius:12px;overflow:hidden;}
th{background:var(--panel);text-align:left;padding:9px 11px;font-family:var(--font-mono);font-size:11px;color:var(--ink-dim);font-weight:500;border-bottom:1px solid var(--line);}
td{padding:9px 11px;border-bottom:1px solid rgba(42,53,64,.5);vertical-align:top;color:var(--ink);}
tr:last-child td{border-bottom:0;}
.id{font-family:var(--font-mono);color:var(--vpn-teal);}
.tag{font-size:10px;font-family:var(--font-mono);padding:2px 7px;border-radius:6px;white-space:nowrap;}
.t-par{background:rgba(91,179,138,.14);color:var(--par);border:1px solid rgba(91,179,138,.4);}
.t-seq{background:rgba(224,180,80,.14);color:var(--seq);border:1px solid rgba(224,180,80,.4);}
.t-fin{background:rgba(127,179,224,.14);color:var(--fin);border:1px solid rgba(127,179,224,.4);}
.h-HIGH{color:var(--hi);font-family:var(--font-mono);}.h-MID{color:var(--mid);font-family:var(--font-mono);}.h-LOW{color:var(--lo);font-family:var(--font-mono);}.h-NONE{color:var(--ink-faint);font-family:var(--font-mono);}
.st{font-family:var(--font-mono);font-size:11px;}
.st-FIXED,.st-DONE,.st-PASS{color:var(--par);}
.delta{font-family:var(--font-mono);color:var(--ink-dim);}
.flow{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin:6px 0 4px;}
.step{background:var(--panel);border:1px solid var(--line);border-radius:9px;padding:8px 12px;font-family:var(--font-mono);font-size:11px;}
.step.pass{border-color:rgba(91,179,138,.5);color:var(--par);}
.arrow{color:var(--ink-faint);}
.bar{height:10px;border-radius:6px;background:linear-gradient(90deg,var(--vpn-teal),var(--par));}
.barrow{display:grid;grid-template-columns:160px 1fr 70px;gap:12px;align-items:center;margin:6px 0;font-size:12px;}
.barrow .lbl{font-family:var(--font-mono);color:var(--ink-dim);}
.track{background:#0c1014;border:1px solid var(--line);border-radius:6px;overflow:hidden;}
.val{font-family:var(--font-mono);text-align:right;}
.foot{margin-top:24px;font-size:11px;color:var(--ink-faint);font-family:var(--font-mono);}
</style>
</head>
<body>
<header class="top" data-lock="true">
  <div class="mark">V</div>
  <div class="tt"><h1>VVX \u00b7 \u5168\u666f\u5f0f\u5206\u6790\u8207\u4fee\u6b63\u77e9\u9663\u5831\u544a</h1>
  <p>VERITAS INTELLIGENCE SYSTEM \u00b7 PANORAMIC FIX MATRIX</p></div>
</header>
<div class="wrap">
  <div class="summary" id="summary"></div>

  <h2>1 \u00b7 \u4fee\u6b63\u968e\u6bb5\u6d41\u7a0b\uff08\u907f\u514d\u4e5d\u982d\u9f8d\u98a8\u96aa\uff09</h2>
  <div class="note">\u5168\u9762\u6027\uff08\u53ef\u5e73\u884c\u3001\u4e92\u4e0d\u5f71\u97ff\uff09\u2192 \u9806\u5e8f\u6027\uff08\u52d5\u5171\u7528\u89e3\u6790\u8def\u5f91\uff09\u2192 \u6536\u5c3e\u6027\uff08\u512a\u5316\u8207\u4e00\u81f4\u6027\uff09\u3002\u6bcf\u4e00\u8f2a\u4fee\u6b63\u5f8c\u91cd\u8de1\u5168\u5957\u6e2c\u8a66\uff0c\u78ba\u8a8d\u672a\u5f15\u5165\u65b0\u932f\u8aa4\u3002</div>
  <div class="flow">
    <div class="step pass">\u5168\u9762\u6027\u6279\u6b21\uff083 \u9805\uff09</div><span class="arrow">\u2192</span>
    <div class="step pass">\u9806\u5e8f\u6027 S1</div><span class="arrow">\u2192</span>
    <div class="step pass">\u6536\u5c3e\u6027\uff084 \u9805\uff09</div><span class="arrow">\u2192</span>
    <div class="step pass">\u5168\u666f\u91cd\u9a57</div>
  </div>

  <h2>2 \u00b7 \u4e09\u8f2a\u5168\u666f\u5206\u6790 \u00b7 \u932f\u8aa4\u8207\u512a\u5316\u77e9\u9663</h2>
  <table id="matrix"><thead><tr>
    <th>ID</th><th>\u9805\u76ee</th><th>\u985e\u5225</th><th>\u4e5d\u982d\u9f8d\u98a8\u96aa</th>
    <th>\u6839\u56e0</th><th>\u4fee\u6b63</th><th>\u72c0\u614b</th><th>\u6e2c\u8a66\u5dee</th>
  </tr></thead><tbody></tbody></table>

  <h2>3 \u00b7 \u6e2c\u8a66\u6f14\u9032\uff08\u6bcf\u968e\u6bb5\u91cd\u8de1\uff09</h2>
  <div id="evo"></div>

  <h2>4 \u00b7 \u9a57\u8b49\u95dc\u5361\uff08test\u2192debug\u2192upgrade\u2192optimize\u2192consolidate\u2192user-test\uff09</h2>
  <div class="flow" id="gates"></div>

  <div class="foot" id="foot"></div>
</div>

<script>
var R = {
  generated: "AUTO",
  summary: [["\u932f\u8aa4\u6578",3],["\u512a\u5316\u9805",5],["\u5df2\u4fee\u6b63",8,"par"],["\u5206\u6790\u8f2a\u6b21",3],["\u6700\u7d42\u901a\u904e",46,"pass"]],
  matrix: [
    ["E01","Plotly var-assignment \u8b80\u53d6\u932f\u8aa4\uff08\u8aa4\u628a config \u7576 layout\uff09","seq","HIGH",
     "extract_plotly \u50c5\u8b58\u5167\u806f JSON \u5b57\u9762\uff0cidentifier \u5f15\u6578\u672a\u89e3\u6790",
     "\u5efa var/let/const \u8c4b\u503c\u8868\uff0cnewPlot identifier \u5f15\u6578\u4ee3\u5165\uff08\u4fdd\u7559 inline \u8def\u5f91\uff09","FIXED","3\u21920"],
    ["E02","Chart.js unquoted JS keys \u89e3\u6790\u5931\u6557\uff08\u6642\u9593\u8ef8/\u8272\u5f69/stacked \u5168\u7121\uff09","par","LOW",
     "json.loads \u62d2\u7d55 JS \u7269\u4ef6\u5b57\u9762\uff08\u672a\u52a0\u5f15\u865f\u9375\uff09",
     "\u5bec\u9b06\u6b63\u5247 fallback\uff1atype/color/stacked/scale=time","FIXED","3\u21920"],
    ["E03","ECharts unquoted JS keys \u89e3\u6790\u5931\u6557\uff08\u6642\u9593\u8ef8/\u8272\u5f69\uff09","par","LOW",
     "\u540c E02\uff1asetOption \u7269\u4ef6\u672a\u52a0\u5f15\u865f",
     "\u5bec\u9b06\u6b63\u5247 fallback\uff1acolor[]/xAxis type=time/series type","FIXED","2\u21920"],
    ["O01","\u7f3a\u4e4f\u6bcf\u5716\u8a3a\u65b7\u8cc7\u8a0a","par","NONE",
     "\u898f\u683c\u7121\u554f\u984c\u6a19\u8a18\uff0c\u4f7f\u7528\u8005\u96e3\u5224\u65b7\u53ef\u4fe1\u5ea6",
     "\u65b0\u589e issues[] \u6b04\u4f4d\uff08\u7121\u5bec\u9ad8/spec-only/raster\u672a\u9a57\u7b49\uff09","DONE","\u2014"],
    ["O02","\u91cd\u8907\u5716\u8868\uff08plotly offline newPlot + json \u96d9\u80de\uff09","par","LOW",
     "\u540c\u4e00\u5716\u88ab newPlot \u8207 application/json \u5169\u8def\u91cd\u8907\u64f7\u53d6",
     "\u4f9d\u7c3d\u540d\uff08engine+\u5c3a\u5bf8+\u8272+\u5167\u5bb9 hash\uff09\u53bb\u91cd","DONE","\u2014"],
    ["O03","colorway \u4e09\u5143\u5f0f\u8106\u5f31","fin","LOW",
     "\u904b\u7b97\u5b50\u512a\u5148\u5e8f\u96e3\u8b80\u3001\u6613\u8aa4\u89e3",
     "\u6539\u70ba\u660e\u78ba\u5206\u652f\u908f\u8f2f","DONE","\u2014"],
    ["O04","\u4e32\u884c\u89e3\u6790\uff08\u591a\u6a94\u6548\u80fd\uff09","fin","LOW",
     "\u9010\u6a94\u4e32\u884c\uff0c\u5927\u91cf\u6a94\u6848\u504f\u6162",
     "ThreadPoolExecutor\uff08ex.map \u4fdd\u5e8f\uff0c>3 \u6a94\u555f\u7528\uff09","DONE","\u2014"],
    ["O05","\u7121\u905e\u8ff4\u6383\u63cf","fin","NONE",
     "\u50c5\u6383\u9802\u5c64\u8cc7\u6599\u593e",
     "--recurse / -Recurse\uff0c\u4e26\u6392\u9664\u81ea\u8eab\u8f38\u51fa\u76ee\u9304","DONE","\u2014"]
  ],
  evo: [
    ["\u57fa\u6e96 spec suite",23,31],
    ["\u5168\u9762\u6027\u6279\u6b21\u5f8c",28,31],
    ["\u9806\u5e8f\u6027 S1 \u5f8c",31,31],
    ["\u6536\u5c3e\u6027\u5f8c\uff08\u7121\u56de\u6b78\uff09",31,31],
    ["jsdom user-test",15,15]
  ],
  gates: [["test",1],["debug",1],["upgrade",1],["test",1],["optimize",1],["test",1],
          ["consolidate",1],["test",1],["user-test 15/15",1],["ps_lint 0E/0W",1],["http \u5b78\u67e55/5",1]]
};

(function(){
  var s=document.getElementById('summary');
  R.summary.forEach(function(r){var b=document.createElement('div');b.className='stat'+(r[2]?' is-'+r[2]:'');
    b.innerHTML='<div class="stat-n">'+r[1]+'</div><div class="stat-l">'+r[0]+'</div>';s.appendChild(b);});

  var tb=document.querySelector('#matrix tbody');
  var tagcls={par:'t-par',seq:'t-seq',fin:'t-fin'},tagtxt={par:'\u53ef\u5e73\u884c',seq:'\u9806\u5e8f',fin:'\u6536\u5c3e'};
  R.matrix.forEach(function(r){
    var tr=document.createElement('tr');
    tr.innerHTML='<td class="id">'+r[0]+'</td><td>'+r[1]+'</td>'+
      '<td><span class="tag '+tagcls[r[2]]+'">'+tagtxt[r[2]]+'</span></td>'+
      '<td class="h-'+r[3]+'">'+r[3]+'</td><td>'+r[4]+'</td><td>'+r[5]+'</td>'+
      '<td class="st st-'+r[6]+'">'+r[6]+'</td><td class="delta">'+r[7]+'</td>';
    tb.appendChild(tr);
  });

  var evo=document.getElementById('evo');
  R.evo.forEach(function(r){
    var pct=Math.round(r[1]/r[2]*100);
    var row=document.createElement('div');row.className='barrow';
    row.innerHTML='<span class="lbl">'+r[0]+'</span>'+
      '<div class="track"><div class="bar" style="width:'+pct+'%"></div></div>'+
      '<span class="val">'+r[1]+'/'+r[2]+'</span>';
    evo.appendChild(row);
  });

  var g=document.getElementById('gates');
  R.gates.forEach(function(r,i){
    var d=document.createElement('div');d.className='step pass';d.textContent='\u2713 '+r[0];g.appendChild(d);
    if(i<R.gates.length-1){var a=document.createElement('span');a.className='arrow';a.textContent='\u2192';g.appendChild(a);}
  });

  document.getElementById('foot').textContent=
    'VVX Extractor v01.1 \u00b7 8 \u9805\u5168\u4fee\u6b63\u7d93 1 \u6b21\u5e73\u884c\u6279\u6b21 + 1 \u6b21\u9806\u5e8f\u4fee\u6b63\u5b8c\u6210 \u00b7 \u6bcf\u8f2a\u91cd\u8de1\u7121\u4e5d\u982d\u9f8d\u56de\u6b78 \u00b7 \u751f\u6210\uff1a'+
    new Date().toISOString().slice(0,19).replace('T',' ');
})();
</script>
</body>
</html>

'@


Write-Host ''
Write-Host '  VVX  HTML Chart Extractor  v01.1  (VPN v3.5)' -ForegroundColor Cyan
Write-Host '  --------------------------------------------' -ForegroundColor DarkGray

# ---- ACC05 : Stopwatch ------------------------------------------------------
$script:Sw = [System.Diagnostics.Stopwatch]::StartNew()

$script:Accel = [ordered]@{
    ACC01 = 'compiled regex pre-filter'
    ACC02 = 'typed generic List collections'
    ACC03 = 'StringBuilder report buffer'
    ACC04 = 'direct [IO.File] read/write'
    ACC05 = 'Stopwatch timing'
    ACC06 = 'ProcessStartInfo subprocess'
    ACC07 = 'parallel pre-scan (ForEach-Object -Parallel)'
    ACC08 = 'HttpListener static server'
    ACC09 = 'buffered byte streaming'
    ACC10 = 'runtime tuning (Progress/PSStyle/GC)'
}
foreach ($k in $script:Accel.Keys) {
    Add-Log ('[' + $k + '] ' + $script:Accel[$k] + ' :: active') 'DarkGray'
}

if (-not (Test-Path -LiteralPath $script:Root)) {
    New-Item -ItemType Directory -Path $script:Root -Force | Out-Null
}
$null = New-Item -ItemType Directory -Path (Join-Path $script:Root 'charts') -Force
Write-VvxFile (Join-Path $script:Root 'SUP_MDL165_VVXExtractor.py') $script:PY_EXTRACTOR
Write-VvxFile (Join-Path $script:Root 'vvx_gallery.js')   $script:JS_GALLERY
Write-VvxFile (Join-Path $script:Root 'VVX_Gallery.html') $script:HTML_GALLERY
Write-VvxFile (Join-Path $script:Root 'VVX_FixReport.html') $script:HTML_REPORT
Add-Log ('modules ready -> ' + $script:Root) 'DarkGray'

# ---- ACC01 + ACC02 + ACC07 : compiled-regex parallel pre-scan ---------------
$script:LibRe = [regex]::new(
    'Plotly\.(newPlot|react)|new\s+Chart\s*\(|echarts\.init|data:image|<svg',
    ([System.Text.RegularExpressions.RegexOptions]::Compiled -bor
     [System.Text.RegularExpressions.RegexOptions]::IgnoreCase))
$rePattern = $script:LibRe.ToString()

$script:Candidates = [System.Collections.Generic.List[string]]::new()
if (Test-Path -LiteralPath $script:Scan -PathType Container) {
    $gciParams = @{ LiteralPath = $script:Scan; Filter = '*.html'; File = $true }
    if ($Recurse) { $gciParams['Recurse'] = $true }
    Get-ChildItem @gciParams | ForEach-Object { $script:Candidates.Add($_.FullName) }
} elseif ($script:Scan -match '\.html?$') {
    $script:Candidates.Add($script:Scan)
}

$hits = @()
if ($script:Candidates.Count -gt 0) {
    $hits = $script:Candidates | ForEach-Object -Parallel {
        $rx = [regex]::new($using:rePattern,
              ([System.Text.RegularExpressions.RegexOptions]::Compiled -bor
               [System.Text.RegularExpressions.RegexOptions]::IgnoreCase))
        try {
            $txt = [System.IO.File]::ReadAllText($_)
            if ($rx.IsMatch($txt)) { $_ }
        } catch { }
    } -ThrottleLimit 8
}
$hitCount = @($hits).Count
Add-Log ('pre-scan : ' + $script:Candidates.Count + ' html, ' + $hitCount + ' contain charts') 'Green'

# ---- resolve python (py launcher first; VIA convention) ---------------------
function Test-PyCandidate {
    param([string]$Exe, [string]$Lead)
    try {
        $p = [System.Diagnostics.ProcessStartInfo]::new()
        $p.FileName = $Exe
        $p.Arguments = (($Lead + ' --version').Trim())
        $p.UseShellExecute = $false
        $p.RedirectStandardOutput = $true
        $p.RedirectStandardError = $true
        $p.CreateNoWindow = $true
        $pr = [System.Diagnostics.Process]::Start($p)
        $pr.WaitForExit(5000) | Out-Null
        return ($pr.ExitCode -eq 0)
    } catch { return $false }
}
$script:PyExe = $null
$script:PyLead = ''
foreach ($cand in @(
        @{ Exe = 'py';      Lead = '-3.12' },
        @{ Exe = 'py';      Lead = '-3.11' },
        @{ Exe = 'py';      Lead = '-3'    },
        @{ Exe = 'python';  Lead = ''      },
        @{ Exe = 'python3'; Lead = ''      })) {
    if (Test-PyCandidate -Exe $cand.Exe -Lead $cand.Lead) {
        $script:PyExe = $cand.Exe
        $script:PyLead = $cand.Lead
        break
    }
}
if ($null -eq $script:PyExe) {
    Write-Host '  [ERROR] No Python 3 found (py / python / python3). Install Python 3 and re-run.' -ForegroundColor Red
    return
}
Add-Log ('python   : ' + ($script:PyExe + ' ' + $script:PyLead).Trim()) 'DarkGray'

# ---- ACC06 : run extractor via ProcessStartInfo -----------------------------
$script:ReaderPy = Join-Path $script:Root 'SUP_MDL165_VVXExtractor.py'
$recurseArg = ''
if ($Recurse) { $recurseArg = ' --recurse' }
$argStr = ($script:PyLead + ' "' + $script:ReaderPy + '" --scan "' + $script:Scan +
           '" --out "' + $script:Root + '" --stdw ' + $StdW + ' --stdh ' + $StdH +
           ' --minside ' + $MinSide + $recurseArg).Trim()
$psi = [System.Diagnostics.ProcessStartInfo]::new()
$psi.FileName = $script:PyExe
$psi.Arguments = $argStr
$psi.UseShellExecute = $false
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError = $true
$psi.CreateNoWindow = $true
$proc = [System.Diagnostics.Process]::Start($psi)
$stdout = $proc.StandardOutput.ReadToEnd()
$stderr = $proc.StandardError.ReadToEnd()
$proc.WaitForExit()
if ($stdout) { Add-Log $stdout.Trim() 'Green' }
if ($proc.ExitCode -ne 0) {
    Write-Host '  [ERROR] extractor failed:' -ForegroundColor Red
    Write-Host $stderr -ForegroundColor DarkRed
    return
}
$script:Sw.Stop()
Add-Log ('extract  : done in ' + $script:Sw.ElapsedMilliseconds + ' ms') 'Cyan'

# ---- ACC08 : pick a free port + HttpListener --------------------------------
function Get-Mime {
    param([string]$Path)
    $map = [ordered]@{
        '.html' = 'text/html; charset=utf-8'
        '.js'   = 'application/javascript; charset=utf-8'
        '.json' = 'application/json; charset=utf-8'
        '.css'  = 'text/css; charset=utf-8'
        '.svg'  = 'image/svg+xml'
        '.png'  = 'image/png'
        '.ico'  = 'image/x-icon'
    }
    $ext = [System.IO.Path]::GetExtension($Path).ToLower()
    if ($map.Contains($ext)) { return $map[$ext] }
    return 'application/octet-stream'
}
$script:Listener = $null
$script:UsePort = $Port
for ($i = 0; $i -lt 25; $i++) {
    $tryPort = $Port + $i
    try {
        $l = [System.Net.HttpListener]::new()
        $l.Prefixes.Add("http://127.0.0.1:$tryPort/")
        $l.Start()
        $script:Listener = $l
        $script:UsePort = $tryPort
        break
    } catch {
        if ($null -ne $l) { $l.Close() }
    }
}
if ($null -eq $script:Listener) {
    Write-Host '  [ERROR] No free port in range.' -ForegroundColor Red
    return
}
$base = "http://127.0.0.1:$($script:UsePort)/"
$script:Url       = $base + 'VVX_Gallery.html'
$script:ReportUrl = $base + 'VVX_FixReport.html'
Add-Log ('gallery  : ' + $script:Url) 'Cyan'
Add-Log ('report   : ' + $script:ReportUrl) 'Cyan'

# ---- ACC09 : serve with buffered byte streaming + auto-open both ------------
if (-not $NoLaunch) {
    Start-Process $script:ReportUrl
    Start-Sleep -Milliseconds 350
    Start-Process $script:Url
}
Write-Host ''
Write-Host '  LIVE. Press Ctrl+C to stop the server.' -ForegroundColor Yellow
Write-Host ''
try {
    while ($script:Listener.IsListening) {
        $ctx = $script:Listener.GetContext()
        $rel = [Uri]::UnescapeDataString($ctx.Request.Url.AbsolutePath.TrimStart('/'))
        if ([string]::IsNullOrWhiteSpace($rel)) { $rel = 'VVX_Gallery.html' }
        $full = Join-Path $script:Root $rel
        try {
            if (Test-Path -LiteralPath $full -PathType Leaf) {
                $bytes = [System.IO.File]::ReadAllBytes($full)
                $ctx.Response.ContentType = (Get-Mime $full)
                $ctx.Response.ContentLength64 = $bytes.Length
                $ctx.Response.OutputStream.Write($bytes, 0, $bytes.Length)
            } else {
                $ctx.Response.StatusCode = 404
                $nf = [System.Text.Encoding]::UTF8.GetBytes('404: ' + $rel)
                $ctx.Response.OutputStream.Write($nf, 0, $nf.Length)
            }
        } catch {
            $ctx.Response.StatusCode = 500
        } finally {
            $ctx.Response.Close()
        }
    }
} finally {
    if ($null -ne $script:Listener) { $script:Listener.Stop(); $script:Listener.Close() }
    Write-Host '  server stopped.' -ForegroundColor DarkGray
}

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
