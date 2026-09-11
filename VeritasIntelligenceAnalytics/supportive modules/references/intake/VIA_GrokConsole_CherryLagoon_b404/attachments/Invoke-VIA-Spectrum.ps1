#requires -Version 7
# ============================================================================
#  VIA Spectrum Launcher  v1.0  (2026-09-06)
#  Dual / Triple / N-source consensus spectrum -> single interactive HTML
#  Paste-and-run (wrapped in &{ } per LL#25) or:  pwsh -ExecutionPolicy Bypass -File .\Invoke-VIA-Spectrum.ps1
#  Bars: green (downside) -> red (upside) gradient, one shared axis gradient aligned on price; transparent bg
#  Edit  $Root\spectrum_input.json  to add sources (Bloomberg / Reuters / Street) -> Triple Spectrum auto-renders
# ============================================================================
&{
param(
    [string]$Root      = (Join-Path $env:USERPROFILE 'VIA\Spectrum'),
    [string]$PythonExe = 'python',
    [switch]$SkipOpen
)
$ErrorActionPreference = 'Stop'
$script:Clock = [System.Diagnostics.Stopwatch]::StartNew()
$Utf8NoBom = [System.Text.UTF8Encoding]::new($false)
$Total = 6

function Write-Step {
    param([int]$N, [string]$Msg)
    Write-Host ("[{0}/{1}] {2,-48} +{3:0.0}s" -f $N, $script:TotalSteps, $Msg, $script:Clock.Elapsed.TotalSeconds) -ForegroundColor Cyan
}
function Invoke-Native {
    # LL#26: no redirect -> child output streams live, never looks frozen
    param([string]$Exe, [string[]]$ArgList, [string]$Cwd)
    $psi = [System.Diagnostics.ProcessStartInfo]::new()
    $psi.FileName = $Exe
    $psi.UseShellExecute = $false
    $psi.RedirectStandardOutput = $false
    $psi.RedirectStandardError = $false
    $psi.WorkingDirectory = $Cwd
    foreach ($a in $ArgList) { [void]$psi.ArgumentList.Add($a) }
    $p = [System.Diagnostics.Process]::Start($psi)
    $p.WaitForExit()
    return $p.ExitCode
}
$script:TotalSteps = $Total

# --- 1. folders ---------------------------------------------------------------
Write-Step 1 'Prepare folders'
$OutDir = Join-Path $Root 'out'
$BakDir = Join-Path $Root '_bak'
foreach ($d in @($Root, $OutDir, $BakDir)) { if (-not (Test-Path -LiteralPath $d)) { [void](New-Item -ItemType Directory -Path $d) } }

# --- 2. write python module (append-only: previous version archived) ----------
Write-Step 2 'Write via_dual_spectrum.py'
$PyPath = Join-Path $Root 'via_dual_spectrum.py'
if (Test-Path -LiteralPath $PyPath) {
    Copy-Item -LiteralPath $PyPath -Destination (Join-Path $BakDir ('via_dual_spectrum_{0}.py' -f (Get-Date -Format 'yyyyMMdd_HHmmss'))) -Force
}
$PyCode = @'
# -*- coding: utf-8 -*-
# VIA Dual/Triple Spectrum  --  N-source consensus spectrum dashboard (Plotly, single HTML)
# Usage:  python via_dual_spectrum.py <input.json> <output.html>
#   input.json : {"title", "unit", "price" (current price), "asof" YYYY-MM-DD, "sources": {"FactSet": {...}, "YFinance": [...]}}
#   per-source "asof" overrides the global one; "n" = sample count (analyst count)
#   each source is EITHER precomputed stats {"mean","median","low","high","std"(opt),"n"(opt)}
#                 OR a raw list of samples [150.0, 152.5, ...]  -> stats are computed here
import sys, json, statistics, datetime
from urllib.parse import quote
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ---- Visual Lock palette (background transparent; bars = green->red gradient aligned on price) ----
BG, PAPER, INK, HAIR = "#f5f4f0", "#ffffff", "#1e1d1a", "#dbd9d3"
FONT_BODY = "DM Sans, Segoe UI, Microsoft JhengHei, sans-serif"
FONT_MONO = "DM Mono, Consolas, monospace"


def _stats(v):
    """Normalize one source into a stats dict (accepts raw samples or precomputed)."""
    if isinstance(v, dict):
        s = dict(v)
        s.setdefault("std", None)
        s.setdefault("n", None)
        s.setdefault("asof", None)
        return s
    xs = sorted(float(x) for x in v)
    return {
        "mean": statistics.fmean(xs),
        "median": statistics.median(xs),
        "low": xs[0],
        "high": xs[-1],
        "std": statistics.pstdev(xs) if len(xs) > 1 else 0.0,
        "n": len(xs),
        "asof": None,
    }


GREEN, RED = "#5a9e6f", "#c96b5a"


def _hex2rgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def _mix(c1, c2, t):
    a, b = _hex2rgb(c1), _hex2rgb(c2)
    return "#%02x%02x%02x" % tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def _axis_color(x, x0, x1, pivot):
    """Global gradient: GREEN at x0 -> PAPER at pivot -> RED at x1. Every bar samples THIS function,
    so all bars share one aligned gradient (same x = same color)."""
    if x <= pivot:
        return _mix(GREEN, PAPER, (x - x0) / (pivot - x0)) if pivot > x0 else PAPER
    return _mix(PAPER, RED, (x - pivot) / (x1 - pivot)) if x1 > pivot else PAPER


def _bar_svg(low, high, x0, x1, pivot):
    """SVG for one bar: stops = global gradient sampled at low / pivot / high."""
    stops = [(0.0, _axis_color(low, x0, x1, pivot))]
    if low < pivot < high:
        stops.append(((pivot - low) / (high - low), PAPER))
    stops.append((1.0, _axis_color(high, x0, x1, pivot)))
    st = "".join(f"<stop offset='{o:.4f}' stop-color='{c}'/>" for o, c in stops)
    svg = (f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1 1' preserveAspectRatio='none'>"
           f"<linearGradient id='g' x1='0' x2='1' y1='0' y2='0'>{st}</linearGradient>"
           f"<rect width='1' height='1' fill='url(#g)'/></svg>")
    return "data:image/svg+xml;utf8," + quote(svg, safe="")


def dual_spectrum_plot(sources, title="Consensus Spectrum", unit="", out_html=None, price=None, asof=None, eps=None):
    """
    sources : dict {source_name: samples | stats}   (2 = Dual, 3 = Triple, N supported)
    Returns the Plotly Figure; writes a standalone HTML when out_html is given.
    Single Range Spectrum (Low-High) per source, Median label above / Mean label below, current-price line.
    price   : reference (current) price -> upside % on Median/Mean labels, sign first, red up / green down.
    asof    : data update date YYYY-MM-DD (global default; each source may carry its own "asof").
    eps     : optional {"title": "FactSet Consensus EPS", "rows": [{"period":"FY0","label":"今年 N","eps":9.8}, ...]}
              -> 3-column table on the right, FY0..FY3: Fiscal Period | Estimated EPS | Forward PER (= price / eps)
              missing FY3 (or later rows) are auto-extrapolated with the latest YoY EPS growth and marked *
    """
    asof = asof or datetime.date.today().isoformat()
    names = list(sources.keys())
    st = {k: _stats(v) for k, v in sources.items()}
    ypos = list(range(len(names)))[::-1]  # first source on top

    if eps:
        fig = make_subplots(rows=1, cols=2, column_widths=[0.58, 0.42], horizontal_spacing=0.06,
                            specs=[[{"type": "xy"}, {"type": "table"}]])
    else:
        fig = go.Figure()
    BAR_H = 0.34

    # ---- value axis + gradient pivot (aligned on price) ----------------------
    vmin = min([s["low"] for s in st.values()] + ([price] if price else []))
    vmax = max([s["high"] for s in st.values()] + ([price] if price else []))
    pad = (vmax - vmin) * 0.18 or 1
    x0, x1 = vmin - pad, vmax + pad
    pivot = price if price else (x0 + x1) / 2

    for k, y in zip(names, ypos):
        s = st[k]
        n_txt = f" (n={s['n']})" if s.get("n") else ""
        # gradient bar (green downside -> red upside), sampled from the shared axis gradient
        fig.add_layout_image(source=_bar_svg(s["low"], s["high"], x0, x1, pivot), xref="x", yref="y",
                             x=s["low"], y=y + BAR_H / 2, sizex=s["high"] - s["low"], sizey=BAR_H,
                             xanchor="left", yanchor="top", sizing="stretch", layer="below")
        # invisible hover carrier (Bar, no line) + endpoint labels (text only)
        fig.add_trace(go.Bar(
            base=[s["low"]], x=[s["high"] - s["low"]], y=[y], orientation="h", width=BAR_H, name=k, showlegend=False,
            marker=dict(color="rgba(0,0,0,0)", line=dict(width=0)),
            hovertemplate=f"<b>{k}</b>{n_txt}<br>Low {s['low']:,.2f} - High {s['high']:,.2f} {unit}<extra></extra>",
        ))
        fig.add_trace(go.Scatter(
            x=[s["low"], s["high"]], y=[y, y], mode="text", showlegend=False, hoverinfo="skip",
            text=[f"{s['low']:,.0f}", f"{s['high']:,.0f}"], textposition=["middle left", "middle right"],
            textfont=dict(family=FONT_MONO, size=11, color=INK),
        ))
        # mean tick + median diamond on the bar
        fig.add_trace(go.Scatter(
            x=[s["mean"]], y=[y], mode="markers", showlegend=False,
            marker=dict(symbol="line-ns", size=24, color=INK, line=dict(width=3, color=INK)),
            hovertemplate=f"<b>{k}</b> mean {s['mean']:,.2f}<extra></extra>",
        ))
        fig.add_trace(go.Scatter(
            x=[s["median"]], y=[y], mode="markers", showlegend=False,
            marker=dict(symbol="diamond", size=10, color=PAPER, line=dict(width=1.5, color=INK)),
            hovertemplate=f"<b>{k}</b> median {s['median']:,.2f}<extra></extra>",
        ))
        # Median above / Mean below; upside vs price, sign first, TW colors (red up / green down)
        def _up(v):
            if not price:
                return ""
            d = (v / price - 1) * 100
            col = RED if d > 0 else (GREEN if d < 0 else INK)
            return f"  <span style='color:{col}'><b>{d:+.1f}%</b></span>"
        n_lbl = (f"  n={s['n']}" if s.get("n") else "") + f"  {s.get('asof') or asof}"
        xmid = (s["low"] + s["high"]) / 2
        fig.add_annotation(x=xmid, y=y, yshift=24, showarrow=False,
                           text=f"Median {s['median']:,.0f}{_up(s['median'])}{n_lbl}",
                           font=dict(family=FONT_MONO, size=11, color=INK))
        fig.add_annotation(x=xmid, y=y, yshift=-24, showarrow=False,
                           text=f"Mean {s['mean']:,.0f}{_up(s['mean'])}",
                           font=dict(family=FONT_MONO, size=11, color=INK))

    # current-price reference line
    if price:
        fig.add_shape(type="line", xref="x", yref="paper", x0=price, x1=price, y0=0, y1=1,
                      line=dict(color=INK, width=1, dash="dot"))
        fig.add_annotation(xref="x", yref="paper", x=price, y=1, yshift=12, showarrow=False,
                           text=f"Price {price:,.0f}", font=dict(family=FONT_MONO, size=10, color=INK))

    # ---- consensus-gap annotation (first source vs each other source) -------
    base = st[names[0]]
    gaps = []
    for k in names[1:]:
        d = st[k]["mean"] - base["mean"]
        pct = d / base["mean"] * 100 if base["mean"] else 0
        gaps.append(f"{k} vs {names[0]}: mean {d:+,.2f} ({pct:+.2f}%) | median {st[k]['median'] - base['median']:+,.2f}")
    gap_txt = "<br>".join(gaps)

    fig.layout.xaxis.update(range=[x0, x1], title_text=unit or "Value",
                     gridcolor=HAIR, zerolinecolor=HAIR, tickfont=dict(family=FONT_MONO, size=10))
    fig.layout.yaxis.update(tickvals=ypos, ticktext=names, tickfont=dict(family=FONT_BODY, size=13), showgrid=False,
                     range=[-0.75, len(names) - 1 + 0.75])

    # ---- right-side consensus EPS / forward PER table ---------------------------
    if eps:
        rows = [dict(r) for r in eps.get("rows", [])]
        # FY0..FY3 required: if N+3 is missing, extrapolate it with the latest YoY growth (eps[-1] / eps[-2])
        DEFAULT_LABEL = {0: "今年 N", 1: "明年 N+1", 2: "後年 N+2", 3: "N+3"}
        extrapolated = False
        while len(rows) < 4:
            i = len(rows)
            prev = [r["eps"] for r in rows if r.get("eps")]
            g = (prev[-1] / prev[-2]) if len(prev) >= 2 and prev[-2] else 1.0
            rows.append({"period": f"FY{i}", "label": DEFAULT_LABEL.get(i, f"N+{i}"),
                         "eps": round(prev[-1] * g, 2) if prev else None, "est": True})
            extrapolated = True
        rows = rows[:4]
        c1 = [f"{r.get('period', '')}" + (f" ({r['label']})" if r.get("label") else "") for r in rows]
        c2 = [(f"$ {r['eps']:,.2f}" + (" *" if r.get("est") else "")) if r.get("eps") is not None else "-" for r in rows]
        per_txt = [f"{price / r['eps']:,.1f} x" if (price and r.get("eps")) else "-" for r in rows]
        fig.add_trace(go.Table(
            columnwidth=[1.1, 1.0, 1.0],
            header=dict(values=["<b>Fiscal Period</b>", "<b>Estimated EPS (共識)</b>", "<b>Forward PER (隨時價聯動)</b>"],
                        fill_color=PAPER, line_color=HAIR, align="left", height=30,
                        font=dict(family=FONT_BODY, size=12, color=INK)),
            cells=dict(values=[c1, c2, per_txt], fill_color="rgba(0,0,0,0)", line_color=HAIR, align="left", height=28,
                       font=dict(family=FONT_MONO, size=11, color=INK)),
        ), row=1, col=2)
        if extrapolated:
            fig.add_annotation(xref="paper", yref="paper", x=1.0, y=-0.16, xanchor="right", showarrow=False,
                               text="* 自動調漲：以最近一年 EPS 成長率外推", font=dict(family=FONT_BODY, size=10, color="#6f6f6f"))
        fig.add_annotation(xref="paper", yref="paper", x=1.0, y=1.06, xanchor="right", showarrow=False,
                           text=f"<b>{eps.get('title', 'Consensus EPS')}</b>"
                                + (f"  <span style='color:#6f6f6f'>@ price {price:,.0f}</span>" if price else ""),
                           font=dict(family=FONT_BODY, size=13, color=INK))

    fig.update_layout(
        title=dict(text=f"<b>{title}</b><br><span style='font-size:12px;color:#6f6f6f'>{gap_txt}</span>",
                   x=0.01, xanchor="left", font=dict(family=FONT_BODY, size=20, color=INK)),
        barmode="overlay", height=140 + 125 * len(names),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(family=FONT_BODY, color=INK),
        showlegend=False,
        margin=dict(l=90, r=30, t=120, b=90),
    )

    if out_html:
        fig.write_html(out_html, include_plotlyjs=True, full_html=True,
                       config=dict(displaylogo=False, responsive=True))
    return fig


if __name__ == "__main__":
    inp, out = sys.argv[1], sys.argv[2]
    with open(inp, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    dual_spectrum_plot(cfg["sources"], title=cfg.get("title", "Consensus Spectrum"),
                       unit=cfg.get("unit", ""), out_html=out, price=cfg.get("price"), asof=cfg.get("asof"),
                       eps=cfg.get("eps"))
    print(f"@@PROGRESS|100|written {out}")
'@
[System.IO.File]::WriteAllText($PyPath, $PyCode, $Utf8NoBom)

# --- 3. sample input (created once, never overwritten -> edit freely) ---------
Write-Step 3 'Ensure spectrum_input.json'
$InPath = Join-Path $Root 'spectrum_input.json'
if (-not (Test-Path -LiteralPath $InPath)) {
    $Sample = @'
{
  "title": "2330 TSMC Target Price Consensus - Dual Spectrum",
  "unit": "TWD",
  "price": 140,
  "asof": "2026-09-07",
  "sources": {
    "FactSet": {
      "mean": 155,
      "median": 152,
      "low": 120,
      "high": 185,
      "n": 24,
      "asof": "2026-09-05"
    },
    "YFinance": [
      110,
      135,
      140,
      148,
      150,
      155,
      160,
      168,
      190
    ]
  },
  "eps": {
    "title": "FactSet Consensus EPS",
    "rows": [
      {
        "period": "FY0",
        "label": "今年 N",
        "eps": 9.8
      },
      {
        "period": "FY1",
        "label": "明年 N+1",
        "eps": 11.5
      },
      {
        "period": "FY2",
        "label": "後年 N+2",
        "eps": 14.0
      }
    ]
  }
}
'@
    [System.IO.File]::WriteAllText($InPath, $Sample, $Utf8NoBom)
    Write-Host ('      created sample -> {0}' -f $InPath) -ForegroundColor DarkGray
} else {
    Write-Host ('      using existing -> {0}' -f $InPath) -ForegroundColor DarkGray
}

# --- 4. dependency check ------------------------------------------------------
Write-Step 4 'Check plotly'
$rc = Invoke-Native -Exe $PythonExe -ArgList @('-c', 'import plotly') -Cwd $Root
if ($rc -ne 0) {
    Write-Host '      plotly missing -> pip install' -ForegroundColor Yellow
    $rc = Invoke-Native -Exe $PythonExe -ArgList @('-m', 'pip', 'install', 'plotly', '--quiet') -Cwd $Root
    if ($rc -ne 0) { throw ('pip install plotly failed (exit {0})' -f $rc) }
}

# --- 5. render ----------------------------------------------------------------
Write-Step 5 'Render spectrum HTML'
$HtmlPath = Join-Path $OutDir ('Spectrum_{0}.html' -f (Get-Date -Format 'yyyyMMdd_HHmmss'))
$rc = Invoke-Native -Exe $PythonExe -ArgList @($PyPath, $InPath, $HtmlPath) -Cwd $Root
if ($rc -ne 0) { throw ('render failed (exit {0})' -f $rc) }

# --- 6. open ------------------------------------------------------------------
Write-Step 6 'Open report'
if (-not $SkipOpen) { Start-Process -FilePath $HtmlPath }   # LL#12
Write-Host ''
Write-Host ('  HTML  : {0}' -f $HtmlPath) -ForegroundColor Green
Write-Host ('  Input : {0}   (add a 3rd source here -> Triple Spectrum)' -f $InPath) -ForegroundColor Green
Write-Host ('  Done in {0:0.0}s' -f $script:Clock.Elapsed.TotalSeconds) -ForegroundColor Green
}
