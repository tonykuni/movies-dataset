"""VPL-I02/I03 chart engine with an 'auto-optimize' pass.

optimize(fig, ax) applies VIA Visual Lock styling + decluttering to ANY
matplotlib axes: brand palette, despined frame, light grid, mono tick
labels, tight layout. Each builder returns a saved PNG path.
"""
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
import os
from datetime import datetime
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import matplotlib.dates as mdates
import numpy as np
from .. import theme as T

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": [T.FONT_BODY, T.FONT_BODY_FB, "DejaVu Sans"],
    "figure.facecolor": T.mpl(T.PANEL),
    "axes.facecolor":   T.mpl(T.PANEL),
    "savefig.facecolor": T.mpl(T.PANEL),
    "text.color":  T.mpl(T.INK),
    "axes.labelcolor": T.mpl(T.INK_SOFT),
    "xtick.color": T.mpl(T.INK_SOFT),
    "ytick.color": T.mpl(T.INK_SOFT),
})


def optimize(ax, *, grid="y"):
    """The 'auto optimize any chart' pass — declutter + brand any axes."""
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(T.mpl(T.LINE))
    ax.tick_params(length=0, labelsize=9)
    if grid in ("y", "both"):
        ax.grid(axis="y", color=T.mpl(T.LINE), linewidth=0.8, zorder=0)
    if grid in ("x", "both"):
        ax.grid(axis="x", color=T.mpl(T.LINE), linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    if ax.get_title():
        ax.title.set_fontsize(13)
        ax.title.set_fontweight("bold")
        ax.title.set_color(T.mpl(T.INK))


def _save(fig, out_dir, name, w=8.2, h=4.4):
    fig.set_size_inches(w, h)
    fig.tight_layout(pad=1.1)
    path = os.path.join(out_dir, name)
    fig.savefig(path, dpi=200)
    plt.close(fig)
    return path


def _d(s):
    return datetime.strptime(s, "%Y-%m-%d")


def gantt(tasks, out_dir):
    fig, ax = plt.subplots()
    tasks = list(reversed(tasks))  # top-down reading order
    for i, t in enumerate(tasks):
        start, fin = _d(t["start"]), _d(t["finish"])
        dur = (fin - start).days
        col = T.mpl(T.STATUS.get(t["status"], T.INK_FAINT))
        ax.barh(i, dur, left=start, height=0.55, color=col, zorder=3,
                edgecolor="none")
        # progress overlay
        if t["progress"] > 0:
            ax.barh(i, dur * t["progress"], left=start, height=0.55,
                    color="white", alpha=0.30, zorder=4, edgecolor="none")
        ax.text(start, i + 0.42, t["name"], fontsize=8.5,
                color=T.mpl(T.INK), va="bottom")
    ax.set_yticks([])
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
    ax.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=mdates.MO))
    ax.set_ylim(-0.6, len(tasks) - 0.1)
    optimize(ax, grid="x")
    legend = [Patch(facecolor=T.mpl(T.STATUS[k]), label=k.title())
              for k in ("done", "active", "blocked", "waiting")]
    ax.legend(handles=legend, loc="lower left", bbox_to_anchor=(0, 1.0),
              frameon=False, fontsize=8, ncol=4, handlelength=1.0)
    return _save(fig, out_dir, "chart_gantt.png", h=4.6)


def budget(rows, out_dir):
    fig, ax = plt.subplots()
    cats = [r["category"] for r in rows]
    planned = [r["planned"] for r in rows]
    actual = [r["actual"] for r in rows]
    x = np.arange(len(cats))
    w = 0.38
    ax.bar(x - w/2, planned, w, label="Planned", color=T.mpl(T.INK_FAINT), zorder=3)
    ax.bar(x + w/2, actual, w, label="Actual", color=T.mpl(T.ACCENT), zorder=3)
    ax.set_xticks(x)
    ax.set_xticklabels(cats, fontsize=8.5)
    ax.yaxis.set_major_formatter(lambda v, _: f"${v/1000:.0f}k")
    optimize(ax)
    ax.legend(frameon=False, fontsize=9, loc="upper right")
    return _save(fig, out_dir, "chart_budget.png", h=4.2)


def risk_heatmap(risks, out_dir):
    fig, ax = plt.subplots()
    grid = np.zeros((5, 5))
    for r in risks:
        grid[5 - r["impact"], r["probability"] - 1] += 1
    # green -> amber -> rust gradient via custom colormap
    from matplotlib.colors import LinearSegmentedColormap
    cmap = LinearSegmentedColormap.from_list(
        "via", [T.mpl(T.PANEL_ALT), T.mpl(T.AMBER), T.mpl(T.RUST)])
    ax.imshow(grid, cmap=cmap, aspect="auto", zorder=2)
    for r in risks:
        c = r["probability"] - 1
        rr = 5 - r["impact"]
        ax.text(c, rr, "●", ha="center", va="center",
                color=T.mpl(T.INK), fontsize=11)
    ax.set_xticks(range(5)); ax.set_xticklabels(range(1, 6))
    ax.set_yticks(range(5)); ax.set_yticklabels(range(5, 0, -1))
    ax.set_xlabel("Probability →", fontsize=9)
    ax.set_ylabel("Impact →", fontsize=9)
    for s in ("top", "right", "left", "bottom"):
        ax.spines[s].set_visible(False)
    ax.tick_params(length=0)
    return _save(fig, out_dir, "chart_risk.png", w=5.0, h=4.2)


def stakeholders(rows, out_dir):
    fig, ax = plt.subplots()
    for s in rows:
        ax.scatter(s["interest"], s["power"], s=420, color=T.mpl(T.BLUE),
                   alpha=0.85, zorder=3, edgecolor="white", linewidth=1.5)
        ax.text(s["interest"], s["power"] - 0.42, s["name"], ha="center",
                va="top", fontsize=7.5, color=T.mpl(T.INK_SOFT))
    ax.axvline(3, color=T.mpl(T.LINE), zorder=1)
    ax.axhline(3, color=T.mpl(T.LINE), zorder=1)
    ax.set_xlim(0.5, 5.7); ax.set_ylim(0.5, 5.7)
    ax.set_xlabel("Interest →", fontsize=9)
    ax.set_ylabel("Power →", fontsize=9)
    quad = {(4.6, 5.4): "Manage closely", (1.0, 5.4): "Keep satisfied",
            (4.6, 0.9): "Keep informed", (1.0, 0.9): "Monitor"}
    for (xx, yy), lab in quad.items():
        ax.text(xx, yy, lab, fontsize=7.5, color=T.mpl(T.INK_FAINT),
                style="italic")
    optimize(ax, grid="none")
    return _save(fig, out_dir, "chart_stake.png", w=5.6, h=4.2)
