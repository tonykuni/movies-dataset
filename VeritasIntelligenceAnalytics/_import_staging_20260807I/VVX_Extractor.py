# -*- coding: utf-8 -*-
# ============================================================================
#  VVX_Extractor.py  -  Veritas Viz eXtractor  (VIA / VPN family)
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
