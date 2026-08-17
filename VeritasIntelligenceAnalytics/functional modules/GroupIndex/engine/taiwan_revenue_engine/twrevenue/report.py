"""report.py -- 單頁 HTML 儀表板 (視覺鎖定: VIA 族群分類 v1.1 風格).

視覺規範 (鎖定, 不隨 OS 深色模式改變):
    紙感底色 #f5f4f0 / 白卡片 / 細線 #dbd9d3
    字體: Syne (標題) + DM Mono (數字/標籤) + DM Sans/Noto Sans TC (內文)
    台股慣例 紅漲綠跌: 成長 = 紅色 ▲ (#c96b5a), 衰退 = 綠色 ▼ (#5a9e6f)
    角色標籤 LEADER(紅) / PEER(藍) / LAGGARD(灰), 同 VIA 附件
矩陣對齊: 表頭與資料列共用同一 grid 欄位定義, 數字右對齊。
族群零遺漏: VIA 全部 31 群都列於矩陣 (週期群標示「週期」置底, 不參與動能排名)。
"""
from __future__ import annotations

import datetime as dt
import html as _html

import numpy as np
import pandas as pd


# ----------------------------------------------------------------------------
#  格式 helpers -- 紅▲成長 / 綠▼衰退 (台股慣例)
# ----------------------------------------------------------------------------
def _pct(v, digits=1):
    """方向性百分比: ▲ +x% 紅 / ▼ -x% 綠 / — 無資料."""
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return '<span class="flat">—</span>'
    try:
        v = float(v)
    except (TypeError, ValueError):
        return '<span class="flat">—</span>'
    if pd.isna(v):
        return '<span class="flat">—</span>'
    if v > 0:
        return f'<span class="up">▲ +{v:,.{digits}f}%</span>'
    if v < 0:
        return f'<span class="down">▼ {v:,.{digits}f}%</span>'
    return '<span class="flat">0.0%</span>'


def _fmt(v, pct=False, digits=1):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return "—"
    try:
        s = f"{float(v):,.{digits}f}"
    except (ValueError, TypeError):
        return _html.escape(str(v))
    return s + ("%" if pct else "")


def _rev_str(v):
    if pd.isna(v):
        return "—"
    yi = v / 100000.0
    if yi >= 1:
        return f"{yi:,.2f} 億"
    return f"{v/10000:,.1f} 千萬"


def _score_bar(score):
    if score is None or pd.isna(score):
        return '<span class="flat">—</span>'
    pctv = max(0, min(100, float(score)))
    return (f'<div class="bar2"><div class="bar2-fill" style="width:{pctv:.0f}%"></div>'
            f'<span class="bar2-val">{score:.0f}</span></div>')


def _season_html(v):
    s = str(v)
    if "淡季不淡" in s:
        return f'<span class="up small">{_html.escape(s)}</span>'
    if "旺季不旺" in s:
        return f'<span class="down small">{_html.escape(s)}</span>'
    return f'<span class="flat small">{_html.escape(s)}</span>'


def _tier_html(v):
    s = str(v)
    if s == "優選":
        return '<span class="up">優選</span>'
    if s == "警戒":
        return '<span class="down">警戒</span>'
    if "排除" in s:
        return f'<span class="am small">{_html.escape(s)}</span>'
    return f'<span class="flat">{_html.escape(s)}</span>'


def _verdict_badge(v):
    s = str(v)
    if "加速" in s:
        return f'<span class="vb bup">{_html.escape(s)}</span>'
    if "轉弱" in s:
        return f'<span class="vb bdn">{_html.escape(s)}</span>'
    if "週期" in s:
        return f'<span class="vb bam">{_html.escape(s)}</span>'
    return f'<span class="vb bmut">{_html.escape(s)}</span>'


def _confirm_html(confirm):
    if confirm is True or str(confirm) == "True":
        return '<span class="teal">✔ 確認</span>'
    if confirm is False or str(confirm) == "False":
        return '<span class="am">✘ 背離</span>'
    return '<span class="flat">—</span>'


_ROLE = {"L": ("LEADER", "var(--up)"), "P": ("PEER", "var(--blue)"),
         "G": ("LAGGARD", "var(--mut2)")}


def _role_chip(role):
    lab, col = _ROLE.get(str(role), ("—", "var(--mut2)"))
    return f'<span class="cls" style="background:{col}">{lab}</span>'


# ----------------------------------------------------------------------------
#  個股表格
# ----------------------------------------------------------------------------
def _rows(df, cols):
    out = []
    for _, r in df.iterrows():
        tds = []
        for key, kind in cols:
            v = r.get(key)
            if kind == "id":
                tds.append(f'<td class="mono">{_html.escape(str(v))}</td>')
            elif kind == "name":
                tds.append(f'<td class="name">{_html.escape(str(v))}</td>')
            elif kind == "rev":
                tds.append(f'<td class="num">{_rev_str(v)}</td>')
            elif kind == "pct":
                tds.append(f'<td class="num">{_pct(v)}</td>')
            elif kind == "num":
                tds.append(f'<td class="num">{_fmt(v)}</td>')
            elif kind == "int":
                tds.append(f'<td class="num">{"" if pd.isna(v) else int(v)}</td>')
            elif kind == "score":
                tds.append(f'<td class="score">{_score_bar(v)}</td>')
            elif kind == "season":
                tds.append(f'<td>{_season_html(v)}</td>')
            elif kind == "tier":
                tds.append(f'<td>{_tier_html(v)}</td>')
            else:
                tds.append(f'<td>{_html.escape(str(v))}</td>')
        out.append("<tr>" + "".join(tds) + "</tr>")
    return "\n".join(out)


_RIGHT_KINDS = {"pct", "num", "int", "rev", "score"}


def _table(df, cols, headers):
    """表頭對齊方向與該欄資料一致: 數值欄右對齊, 文字欄左對齊."""
    if df.empty:
        return '<p class="empty">此類別目前無符合的公司。</p>'
    head = "".join(
        f'<th class="ta-r">{h}</th>' if kind in _RIGHT_KINDS else f"<th>{h}</th>"
        for h, (_k, kind) in zip(headers, cols))
    return (f'<table><thead><tr>{head}</tr></thead>'
            f'<tbody>{_rows(df, cols)}</tbody></table>')


def _member_table(analysis, groups, grp):
    from .groups import group_members_detail
    m = group_members_detail(analysis, groups, grp)
    rows = ""
    for _, d in m.iterrows():
        role = str(d.get("role", "")) if pd.notna(d.get("role")) else ""
        chip = _role_chip(role)
        if pd.isna(d.get("cum_yoy")):
            rows += (f'<tr><td class="mono">{_html.escape(str(d["stock_id"]))}</td>'
                     f'<td class="name">{_html.escape(str(d.get("name","")))}</td>'
                     f'<td>{chip}</td>'
                     f'<td colspan="6" class="flat small">無營收資料 (未涵蓋)</td></tr>')
            continue
        rows += (
            "<tr>"
            f'<td class="mono">{_html.escape(str(d["stock_id"]))}</td>'
            f'<td class="name">{_html.escape(str(d.get("name","")))}</td>'
            f'<td>{chip}</td>'
            f'<td class="score">{_score_bar(d.get("score"))}</td>'
            f'<td class="num">{_pct(d.get("cum_yoy"))}</td>'
            f'<td class="num">{_pct(d.get("yoy"))}</td>'
            f'<td class="num">{_pct(d.get("mom"))}</td>'
            f'<td>{_season_html(d.get("seasonality",""))}</td>'
            f'<td>{_tier_html(d.get("tier",""))}</td>'
            "</tr>")
    return (
        '<table class="mtab"><thead><tr><th>代號</th><th>名稱</th><th>角色</th>'
        '<th class="ta-r">動能分數</th><th class="ta-r">累計YoY</th>'
        '<th class="ta-r">單月YoY</th><th class="ta-r">MoM</th>'
        '<th>季節訊號</th><th>分級</th></tr></thead><tbody>'
        f'{rows}</tbody></table>')


# ----------------------------------------------------------------------------
#  族群矩陣 (grid 對齊, 表頭與資料同欄同向)
# ----------------------------------------------------------------------------
def _group_details(r, analysis, groups, cyclical=False):
    grp = str(r["group"])
    lead = str(r["leader_names"]) if pd.notna(r["leader_names"]) and str(r["leader_names"]) else "—"
    if cyclical:
        cells = (
            f'<span class="grk">{int(r["rank"])}</span>'
            f'<span class="gnm">{_html.escape(grp)}</span>'
            f'<span>{_verdict_badge(r["verdict"])}</span>'
            f'<span class="gm ga-r">{_pct(r["agg_cum_yoy"])}</span>'
            f'<span class="gm ga-r">{_pct(r["agg_yoy"])}</span>'
            f'<span class="gm ga-r cFam">{int(r["covered"])}/{int(r["members"])}</span>')
    else:
        cells = (
            f'<span class="grk">{int(r["rank"])}</span>'
            f'<span class="gnm">{_html.escape(grp)}</span>'
            f'<span class="glead cLead">{_html.escape(lead)}</span>'
            f'<span>{_verdict_badge(r["verdict"])}</span>'
            f'<span class="cScore">{_score_bar(r["group_score"])}</span>'
            f'<span class="gm ga-r">{_pct(r["agg_cum_yoy"])}</span>'
            f'<span class="gm ga-r">{_pct(r["agg_yoy"])}</span>'
            f'<span class="gm ga-r cBreadth">{_fmt(r["breadth_pos"], pct=True, digits=0)}</span>'
            f'<span class="gm ga-r cPref">{int(r["n_pref"])}/{int(r["covered"])}</span>'
            f'<span class="gm cConfirm">{_confirm_html(r["leader_confirm"])}</span>')
    return (
        f'<details class="grp"><summary>{cells}</summary>'
        f'<div class="gbody">{_member_table(analysis, groups, grp)}</div>'
        '</details>')


_VIA_HEADER = (
    '<div class="ghd"><span></span><span class="ga-r">#</span>'
    '<span>族群</span><span class="cLead">龍頭</span><span>動能判定</span>'
    '<span class="cScore">族群分數</span><span class="ga-r">加總累計YoY</span>'
    '<span class="ga-r">加總YoY</span><span class="ga-r cBreadth">廣度YoY&gt;0</span>'
    '<span class="ga-r cPref">優選</span><span class="cConfirm">龍頭確認</span></div>')

_SECTOR_HEADER = (
    '<div class="ghd"><span></span><span class="ga-r">#</span>'
    '<span>週期類</span><span>判定</span>'
    '<span class="ga-r">加總累計YoY</span><span class="ga-r">加總YoY</span>'
    '<span class="ga-r cFam">家數</span></div>')


def _group_section(gt: pd.DataFrame, analysis: pd.DataFrame,
                   groups: pd.DataFrame,
                   sector_table: pd.DataFrame | None = None,
                   sector_groups: pd.DataFrame | None = None) -> str:
    if gt is None or gt.empty:
        return ""
    noncyc = gt[~gt["is_cyclical"]]
    n_accel = int((noncyc["verdict"] == "族群加速").sum())
    n_weak = int((noncyc["verdict"] == "族群轉弱").sum())

    # 全部 31 群零遺漏: 非週期依分數排名, 週期群 (鋼鐵/條鋼/貨櫃/散裝) 置底標示週期
    via_html = "".join(_group_details(r, analysis, groups)
                       for _, r in gt.iterrows())

    if sector_table is not None and not sector_table.empty:
        n_cyc_cos = int(sector_table["covered"].sum())
        cyc_html = "".join(
            _group_details(r, analysis, sector_groups, cyclical=True)
            for _, r in sector_table.iterrows())
        cyc_title = (f'週期分流 · 全市場六大類 <span class="en">TWSE+TPEX 依 MOPS 產業別'
                     f'自動歸類 · {n_cyc_cos} tickers · 不看月營收</span>')
        cyc_block = (f'<h2>{cyc_title}</h2>'
                     f'<div class="gwrap"><div class="gmx sector">'
                     f'{_SECTOR_HEADER}{cyc_html}</div></div>')
    else:
        cyc_block = ""

    n_g = groups["group"].nunique() if not groups.empty else 0
    n_t = groups["stock_id"].nunique() if not groups.empty else 0

    return (
        '<div class="panel0">'
        '<h2>熱門族群動能矩陣 <span class="en">grouping momentum · '
        'leader confirm · via curated × mops actual</span></h2>'
        '<p class="desc">VIA 策展族群 (LEADER/PEER/LAGGARD) × 引擎實證月營收動能。'
        '加總表現 = 族群營收加權 YoY (Σ本期營收 / Σ去年同期 − 1)。'
        '點任一列展開個別成員。龍頭確認 = 龍頭營收動能 ≥ 族群中位, ✘ 背離值得警覺。'
        f'全部 <b>{n_g} 群零遺漏</b> (週期群置底標示, 不參與動能排名) · '
        f'加速 <b class="up">▲ {n_accel}</b> · 轉弱 <b class="down">▼ {n_weak}</b>。</p>'
        f'<div class="gwrap"><div class="gmx">{_VIA_HEADER}{via_html}</div></div>'
        f'{cyc_block}'
        f'<p class="gsrc">族群分類 SSOT: <code>twrevenue/groups.csv</code> '
        f'({n_g} 群 / {n_t} 檔) · 驗證 <code>python -m twrevenue.cli groups</code> · '
        f'測試 <code>python -m twrevenue.cli selftest</code></p>'
        '</div>')


# ----------------------------------------------------------------------------
#  主組版
# ----------------------------------------------------------------------------
def build_dashboard(analysis: pd.DataFrame, cfg: dict,
                    data_month: str | None = None,
                    group_table: pd.DataFrame | None = None,
                    groups: pd.DataFrame | None = None,
                    sector_table: pd.DataFrame | None = None,
                    sector_groups: pd.DataFrame | None = None) -> str:
    rc = cfg["report"]
    if groups is None:
        groups = pd.DataFrame()
    top_n = rc["top_n"]
    total = len(analysis)
    noncyc = analysis[~analysis["is_cyclical"]]
    cyc = analysis[analysis["is_cyclical"]]

    n_pref = int((noncyc["tier"] == "優選").sum())
    n_watch = int((noncyc["tier"] == "觀察").sum())
    n_warn = int((noncyc["tier"] == "警戒").sum())
    n_cyc = len(cyc)

    accel = noncyc[(noncyc["tier"] == "優選")].head(top_n)
    decline = noncyc[noncyc["tier"] == "警戒"].sort_values("cum_yoy").head(top_n)
    star = noncyc[noncyc["seasonality"].astype(str).str.contains("淡季不淡")].head(top_n)

    pat_counts = noncyc["pattern"].value_counts()
    cyc_by_ind = (cyc.groupby("industry")["stock_id"].count()
                  .sort_values(ascending=False)) if not cyc.empty else pd.Series(dtype=int)

    cols_main = [
        ("rank", "int"), ("stock_id", "id"), ("name", "name"),
        ("industry", "name"), ("score", "score"),
        ("cum_yoy", "pct"), ("yoy", "pct"), ("mom", "pct"),
        ("consec_pos_yoy", "int"), ("cagr_2y", "pct"),
        ("seasonality", "season"), ("pattern", "name"),
    ]
    head_main = ["#", "代號", "名稱", "產業", "動能分數",
                 "累計YoY", "單月YoY", "MoM", "連正月", "2年CAGR",
                 "季節訊號", "型態"]
    cols_decl = [
        ("stock_id", "id"), ("name", "name"), ("industry", "name"),
        ("cum_yoy", "pct"), ("yoy", "pct"), ("mom", "pct"),
        ("seasonality", "season"), ("pattern", "name"),
    ]
    head_decl = ["代號", "名稱", "產業", "累計YoY", "單月YoY",
                 "MoM", "季節訊號", "型態"]

    cyc_rows = ""
    for ind, n in cyc_by_ind.items():
        cyc_rows += (f'<tr><td class="name">{_html.escape(str(ind))}</td>'
                     f'<td class="num">{n}</td></tr>')
    if not cyc_rows:
        cyc_rows = '<tr><td colspan="2" class="flat">無</td></tr>'

    pat_rows = ""
    max_pat = int(pat_counts.max()) if len(pat_counts) else 1
    for pat, n in pat_counts.items():
        w = 100 * n / max_pat
        pat_rows += (
            f'<div class="patrow"><span class="patlabel">{_html.escape(str(pat))}</span>'
            f'<span class="patbar"><span class="patfill" style="width:{w:.0f}%"></span></span>'
            f'<span class="patn">{n}</span></div>')

    gen = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    dm = data_month or "—"

    n_groups = groups["group"].nunique() if not groups.empty else 0
    return _TEMPLATE.format(
        title=_html.escape(rc["title"]),
        gen=gen, data_month=dm,
        total=total, n_pref=n_pref, n_watch=n_watch,
        n_warn=n_warn, n_cyc=n_cyc, n_groups=n_groups,
        group_section=_group_section(group_table, analysis, groups,
                                     sector_table, sector_groups),
        pat_rows=pat_rows,
        accel_table=_table(accel, cols_main, head_main),
        decline_table=_table(decline, cols_decl, head_decl),
        star_table=_table(star, cols_decl, head_decl),
        cyc_rows=cyc_rows,
        cum_strong=cfg["analyze"]["cum_yoy_strong"],
        mean_strong=cfg["analyze"]["mean_yoy_strong"],
    )


# ----------------------------------------------------------------------------
#  模板 -- 視覺鎖定 VIA v1.1 風格 (紙感/DM Mono/Syne/紅漲綠跌)
# ----------------------------------------------------------------------------
_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:wght@400;500;700&family=DM+Mono:wght@400;500&family=Noto+Sans+TC:wght@400;500;700&display=swap" rel="stylesheet">
<style>
  :root{{
    --bg:#f5f4f0; --paper:#ffffff; --paper2:#fafaf8;
    --ink:#1e1d1a; --ink2:#33403f; --mut:#6b6860; --mut2:#9c9890;
    --line:#dbd9d3; --soft:#ecebe6;
    --blue:#4c78a8; --teal:#439a9a; --am:#c4943a; --vi:#7a6daa;
    --up:#c96b5a; --down:#5a9e6f;
    --reson:linear-gradient(90deg,#c96b5a 0 14.2%,#c4943a 0 28.5%,#5a9e6f 0 42.8%,#439a9a 0 57.1%,#4c78a8 0 71.4%,#7a6daa 0 85.7%,#1e1d1a 0 100%);
  }}
  *{{box-sizing:border-box;margin:0;padding:0}}
  html,body{{background:var(--bg);}}
  body{{color:var(--ink2);font-family:'DM Sans','Noto Sans TC',system-ui,sans-serif;
    font-size:11px;line-height:1.5;-webkit-font-smoothing:antialiased;}}
  ::selection{{background:rgba(67,154,154,.22);}}
  .wrap{{max-width:1600px;margin:0 auto;padding:0 clamp(10px,2vw,24px) 60px;}}
  .bar{{position:fixed;top:0;left:0;right:0;height:4px;background:var(--reson);opacity:.92;z-index:50;}}
  header{{position:relative;padding:20px 0 9px;margin-bottom:10px;border-bottom:2px solid var(--ink);}}
  .kicker{{font:700 10px 'DM Mono',monospace;letter-spacing:2.2px;color:var(--mut);text-transform:uppercase;margin-bottom:7px;}}
  h1{{font:800 19px/1.2 'Syne',sans-serif;color:var(--ink);}}
  h1 span{{color:var(--up);}}
  .sub{{margin-top:6px;font:400 10.5px/1.55 'DM Sans','Noto Sans TC',sans-serif;color:var(--mut);max-width:980px;}}
  .sub b{{color:var(--ink2);}}
  .gov{{display:flex;align-items:center;gap:10px;flex-wrap:wrap;background:#1e1d1a;border-radius:3px;padding:7px 14px;margin:12px 0;}}
  .gov .lk{{font:700 8.5px 'DM Mono',monospace;letter-spacing:.8px;color:#7fd0a0;text-transform:uppercase;}}
  .gov .pill{{font:600 7.5px 'DM Mono',monospace;color:#cfcabf;}}
  .gov .ver{{margin-left:auto;font:700 8px 'DM Mono',monospace;color:#fff;background:#5a9e6f;border-radius:3px;padding:2px 8px;}}
  .legend{{display:flex;gap:14px;flex-wrap:wrap;margin:10px 0 4px;font:600 9px 'DM Mono',monospace;color:var(--mut);}}
  .legend span{{display:inline-flex;align-items:center;gap:5px;}}
  .dot{{width:11px;height:11px;border-radius:2px;}}
  /* 計分卡: 偶數一列 (6 → 4 → 2) */
  .scards{{display:grid;grid-template-columns:repeat(6,1fr);gap:9px;margin:12px 0 4px;}}
  .sc{{background:var(--paper);border:1px solid var(--line);border-radius:5px;padding:9px 14px;}}
  .sc .v{{font:800 21px 'Syne',sans-serif;line-height:1;color:var(--ink);}}
  .sc .l{{font:600 8px 'DM Mono',monospace;color:var(--mut);text-transform:uppercase;letter-spacing:.6px;margin-top:4px;}}
  h2{{font:800 13px 'Syne',sans-serif;color:var(--ink);margin:24px 0 4px;padding-bottom:5px;
    border-bottom:1px solid var(--line);display:flex;align-items:baseline;gap:8px;flex-wrap:wrap;}}
  h2 .en{{font:600 8px 'DM Mono',monospace;color:var(--mut2);letter-spacing:1px;text-transform:uppercase;}}
  .panel0{{margin-top:6px;}}
  .desc{{color:var(--mut);font:400 10.5px/1.55 'DM Sans','Noto Sans TC',sans-serif;margin:4px 0 10px;max-width:1100px;}}
  .desc b{{color:var(--ink2);}}
  .panel{{background:var(--paper);border:1px solid var(--line);border-radius:6px;padding:13px 15px;margin-top:12px;}}
  .panel.warn{{border-left:3px solid var(--am);}}
  .panel h3{{font:800 11px 'Syne',sans-serif;color:var(--ink);margin-bottom:8px;}}
  /* 上下漲跌 */
  .up{{color:var(--up);font-weight:600;}}
  .down{{color:var(--down);font-weight:600;}}
  .flat{{color:var(--mut2);}}
  .teal{{color:var(--teal);font-weight:700;}}
  .am{{color:var(--am);font-weight:700;}}
  .small{{font-size:9.5px;}}
  /* 角色/判定標籤 (同 VIA .cls/.tag) */
  .cls{{font:700 7px 'DM Mono',monospace;color:#fff;border-radius:3px;padding:2px 5px;
    min-width:48px;text-align:center;letter-spacing:.4px;display:inline-block;}}
  .vb{{font:700 7.5px 'DM Mono',monospace;color:#fff;border-radius:3px;padding:2px 6px;
    letter-spacing:.4px;white-space:nowrap;}}
  .vb.bup{{background:var(--up);}} .vb.bdn{{background:var(--down);}}
  .vb.bam{{background:var(--am);}} .vb.bmut{{background:var(--mut2);}}
  /* 表格 (mono, 同 VIA) */
  table{{width:100%;border-collapse:collapse;margin-top:10px;font:500 10px 'DM Mono',monospace;background:var(--paper);}}
  th{{font:700 8px 'DM Mono',monospace;text-transform:uppercase;letter-spacing:.6px;color:var(--mut);
    text-align:left;padding:7px 9px;border-bottom:2px solid var(--ink);background:var(--paper2);white-space:nowrap;}}
  th.ta-r{{text-align:right;}}  /* 表頭對齊方向 = 該欄資料對齊方向 */
  td{{padding:5px 9px;border-bottom:1px solid var(--soft);white-space:nowrap;}}
  tr:hover td{{background:var(--paper2);}}
  td.num,td.score{{text-align:right;font-variant-numeric:tabular-nums;}}
  td.mono{{color:var(--mut);}}
  td.name{{font-family:'Noto Sans TC',sans-serif;font-weight:600;font-size:10.5px;color:var(--ink2);
    max-width:150px;overflow:hidden;text-overflow:ellipsis;}}
  .mtab th:nth-child(-n+3){{text-align:left;}}
  /* 分數條 */
  .bar2{{position:relative;height:13px;background:var(--soft);border-radius:3px;min-width:64px;display:inline-block;width:100%;}}
  .bar2-fill{{position:absolute;left:0;top:0;bottom:0;background:var(--blue);border-radius:3px;}}
  .bar2-val{{position:relative;padding-right:5px;font:700 9px 'DM Mono',monospace;color:var(--ink);}}
  /* 型態分布 */
  .patrow{{display:flex;align-items:center;gap:10px;margin:4px 0;}}
  .patlabel{{width:170px;font:600 10.5px 'Noto Sans TC',sans-serif;}}
  .patbar{{flex:1;height:12px;background:var(--soft);border-radius:3px;overflow:hidden;}}
  .patfill{{display:block;height:100%;background:var(--blue);border-radius:3px;}}
  .patn{{width:36px;text-align:right;font:600 10px 'DM Mono',monospace;}}
  /* 族群矩陣 grid (表頭資料同欄同向; 無橫向捲軸 — 窄幅自動收合次要欄) */
  .gwrap{{background:var(--paper);border:1px solid var(--line);border-radius:6px;margin-top:10px;}}
  .gmx{{--gc:14px 24px minmax(110px,1.2fr) minmax(88px,1fr) 104px 92px 110px 98px 82px 54px 76px;}}
  .gmx.sector{{--gc:14px 24px minmax(96px,1fr) 168px 114px 100px 64px;}}
  .ghd{{display:grid;grid-template-columns:var(--gc);gap:0 8px;align-items:center;
    padding:7px 12px 6px;color:var(--mut);font:700 8px 'DM Mono',monospace;
    text-transform:uppercase;letter-spacing:.6px;border-bottom:2px solid var(--ink);
    background:var(--paper2);white-space:nowrap;}}
  .grp{{border-bottom:1px solid var(--soft);}}
  .grp:last-child{{border-bottom:none;}}
  .grp > summary{{display:grid;grid-template-columns:var(--gc);gap:0 8px;align-items:center;
    padding:7px 12px;cursor:pointer;list-style:none;white-space:nowrap;}}
  .grp > summary::-webkit-details-marker{{display:none;}}
  .grp > summary::before{{content:"▸";color:var(--mut2);font-size:10px;transition:transform .15s;}}
  .grp[open] > summary::before{{transform:rotate(90deg);}}
  .grp[open] > summary, .grp:hover > summary{{background:var(--paper2);}}
  .grk{{text-align:right;font:600 10px 'DM Mono',monospace;color:var(--mut2);}}
  .gnm{{font:800 12px 'Syne','Noto Sans TC',sans-serif;color:var(--ink);overflow:hidden;text-overflow:ellipsis;}}
  .glead{{font:600 10px 'Noto Sans TC',sans-serif;color:var(--mut);overflow:hidden;text-overflow:ellipsis;}}
  .gm{{font:600 10px 'DM Mono',monospace;}}
  .ga-r{{text-align:right;}}
  .gbody{{padding:2px 12px 10px 26px;}}
  .gsrc{{font:500 9px 'DM Mono',monospace;color:var(--mut);margin-top:8px;}}
  .gsrc code{{background:var(--paper);border:1px solid var(--line);border-radius:3px;padding:1px 5px;}}
  /* 左右各一格 (偶數欄) */
  .two{{display:grid;grid-template-columns:1fr 1fr;gap:14px;}}
  .two > *{{min-width:0;}}   /* 防內容撐開欄位 */
  .over{{overflow:hidden;}}
  .playbook{{display:grid;grid-template-columns:1fr 1fr;gap:9px;margin-top:8px;}}
  .pb{{background:var(--paper2);border:1px solid var(--line);border-radius:5px;padding:10px 12px;
    font:400 10.5px/1.5 'Noto Sans TC',sans-serif;}}
  .pb b{{color:var(--blue);font-family:'DM Mono',monospace;font-size:9px;text-transform:uppercase;letter-spacing:.5px;}}
  ol.flow{{margin:6px 0 0;padding-left:18px;font:400 10.5px/1.6 'Noto Sans TC',sans-serif;}}
  ol.flow li{{margin:4px 0;}}
  ol.flow b{{font-family:'DM Mono',monospace;color:var(--ink);font-size:9.5px;}}
  .review{{list-style:none;border-left:3px solid var(--am);padding-left:12px;}}
  .review li{{padding:4px 0;border-bottom:1px solid var(--soft);font:400 10.5px/1.5 'Noto Sans TC',sans-serif;}}
  .review li:last-child{{border-bottom:none;}}
  .empty{{color:var(--mut2);font-size:10.5px;padding:8px 0;}}
  footer{{margin-top:28px;padding-top:10px;border-top:1px solid var(--line);
    font:500 8.5px 'DM Mono',monospace;color:var(--mut2);text-align:center;letter-spacing:.5px;}}
  /* ===== 響應式: 字級/欄寬遞減 + 次要欄收合 => 全程無橫向捲軸 ===== */
  @media (max-width:1120px){{
    .gmx{{--gc:12px 20px minmax(86px,1.1fr) minmax(66px,.9fr) 92px 76px 96px 86px 68px 46px 64px;}}
    .gmx.sector{{--gc:12px 20px minmax(84px,1fr) 150px 102px 90px 56px;}}
    table,.gm,.glead{{font-size:9.5px;}} .gnm{{font-size:11px;}}
    td,.grp>summary{{padding-left:9px;padding-right:9px;}}
    .scards{{grid-template-columns:repeat(4,1fr);}}
  }}
  @media (max-width:1300px){{
    .tside th:nth-child(3),.tside td:nth-child(3),
    .tside th:nth-child(8),.tside td:nth-child(8){{display:none;}}    /* 產業·型態 */
  }}
  @media (max-width:1180px){{
    .tmain th:nth-child(4),.tmain td:nth-child(4),
    .tmain th:nth-child(9),.tmain td:nth-child(9),
    .tmain th:nth-child(10),.tmain td:nth-child(10){{display:none;}} /* 產業·連正月·CAGR */
  }}
  @media (max-width:920px){{
    .cLead,.cBreadth{{display:none!important;}}   /* 收合: 龍頭·廣度 */
    .gmx{{--gc:12px 20px minmax(92px,1.1fr) 92px 78px 98px 88px 46px 64px;}}
    .two{{grid-template-columns:1fr;}}
  }}
  @media (max-width:640px){{
    .cScore,.cPref,.cConfirm{{display:none!important;}} /* 收合: 分數·優選·確認 */
    .gmx{{--gc:11px 18px minmax(76px,1fr) 86px 92px 82px;}}
    .gmx.sector{{--gc:11px 18px minmax(60px,1fr) 108px 86px 78px 42px;}}
    .ghd,.grp > summary{{gap:0 6px;}}
    table,.gm{{font-size:9px;}}
    td,th{{padding:4px 6px;}}
    .tmain th:nth-child(12),.tmain td:nth-child(12),
    .tmain th:nth-child(5),.tmain td:nth-child(5){{display:none;}}    /* 型態·分數 */
    .tside th:nth-child(3),.tside td:nth-child(3),
    .tside th:nth-child(8),.tside td:nth-child(8){{display:none;}}    /* 產業·型態 */
    .mtab th:nth-child(3),.mtab td:nth-child(3),
    .mtab th:nth-child(8),.mtab td:nth-child(8){{display:none;}}      /* 角色·季節 */
    .gbody{{padding-left:14px;padding-right:8px;}}
    .scards{{grid-template-columns:repeat(2,1fr);}}
    .sc .v{{font-size:17px;}} .patlabel{{width:112px;}}
  }}
  @media (max-width:460px){{
    .cFam{{display:none!important;}}
    .gmx{{--gc:10px 15px minmax(62px,1fr) 76px 84px 74px;}}
    .gmx.sector{{--gc:10px 14px minmax(50px,1fr) 90px 80px 72px;}}
    .ghd,.grp > summary{{gap:0 5px;padding-left:8px;padding-right:8px;}}
    table,.gm{{font-size:8.5px;}} .gnm{{font-size:10px;}}
    td,th{{padding:3px 5px;}}
    .vb{{font-size:6.5px;padding:2px 4px;}}
    .mtab th:nth-child(4),.mtab td:nth-child(4),
    .mtab th:nth-child(9),.mtab td:nth-child(9){{display:none;}}      /* 分數·分級 */
    .mtab{{font-size:8px;}}
    .mtab td,.mtab th{{padding:2px 4px;}}
    .mtab td.name{{font-size:9px;max-width:64px;}}
    .gbody{{padding-left:10px;padding-right:6px;}}
  }}
  @media print{{@page{{size:A4 landscape;margin:10mm}}html,body{{background:#fff!important}}}}
</style>
</head>
<body>
<div class="bar"></div>
<div class="wrap">

<header>
  <div class="kicker">Taiwan Revenue Momentum Engine · MOPS 實證月營收 × VIA 族群 · 三層動能</div>
  <h1>台股月營收 <span>動能總表</span> · Revenue Momentum Matrix</h1>
  <p class="sub">資料月份 <b>{data_month}</b> · 產生 {gen} · 來源 <b>MOPS 公開資訊觀測站</b> (TWSE+TPEX 全市場) ·
  三層引擎: <b>累計YoY</b> (主判準) → <b>多月YoY趨勢</b> → <b>MoM vs 季節性</b> · 2年CAGR 修正基期 · <b>紅▲成長 綠▼衰退</b>。</p>
</header>

<div class="gov">
  <span class="lk">🔒 Visual Locked · VIA Style</span>
  <span class="pill">三層權重 45/35/20</span>
  <span class="pill">週期六大類分流 · 不看月營收</span>
  <span class="pill">parquet+duckdb 累計增量</span>
  <span class="ver">{total} TICKERS · {data_month}</span>
</div>

<div class="legend">
  <span><span class="dot" style="background:var(--up)"></span>▲ 紅 = 成長 (YoY/MoM 為正)</span>
  <span><span class="dot" style="background:var(--down)"></span>▼ 綠 = 衰退 (YoY/MoM 為負)</span>
  <span><span class="dot" style="background:var(--up)"></span>LEADER 龍頭</span>
  <span><span class="dot" style="background:var(--blue)"></span>PEER 第二梯隊</span>
  <span><span class="dot" style="background:var(--mut2)"></span>LAGGARD 落後</span>
</div>

<div class="scards">
  <div class="sc"><div class="v">{total}</div><div class="l">分析公司 · 台股全部</div></div>
  <div class="sc"><div class="v" style="color:var(--teal)">{n_groups}</div><div class="l">族群 · 零遺漏</div></div>
  <div class="sc"><div class="v" style="color:var(--up)">{n_pref}</div><div class="l">優選 ▲ · preferred</div></div>
  <div class="sc"><div class="v">{n_watch}</div><div class="l">觀察 · watch</div></div>
  <div class="sc"><div class="v" style="color:var(--down)">{n_warn}</div><div class="l">警戒 ▼ · alert</div></div>
  <div class="sc"><div class="v" style="color:var(--am)">{n_cyc}</div><div class="l">週期股 · excluded</div></div>
</div>

{group_section}

<h2>動能型態分布 <span class="en">pattern distribution · non-cyclical</span></h2>
<div class="panel">{pat_rows}</div>

<h2>動能加速名單 · 優選 <span class="en">accelerating · buy watchlist</span></h2>
<p class="desc">累計YoY ≥ {cum_strong}% 且未連續下滑 · 連續 ≥3 月 YoY 為正。依綜合動能分數排序
(Layer1 累計YoY 45% + Layer2 多月趨勢 35% + Layer3 季節/加速 20%)。</p>
<div class="over tmain">{accel_table}</div>

<div class="two">
  <div>
    <h2>動能衰退 · 警戒 <span class="en">decelerating · avoid</span></h2>
    <p class="desc">累計YoY 轉負或由高轉低跌破門檻, 或旺季不旺且 YoY 為負。</p>
    <div class="over tside">{decline_table}</div>
  </div>
  <div>
    <h2>淡季不淡 · 強訊號 <span class="en">off-season strength · layer 3</span></h2>
    <p class="desc">歷史淡季月份 MoM 明顯優於季節常態, 需求動能超季節。</p>
    <div class="over tside">{star_table}</div>
  </div>
</div>

<h2>原物料 / 週期股 · 替代判準 <span class="en">cyclical playbook · not monthly revenue</span></h2>
<p class="desc">原物料營收 = 價格 × 量, 價格波動遠大於量, 加上庫存循環/合約制/批次出貨,
月營收 YoY·MoM 嚴重失真 — 已排除於動能排名, 改用以下判準。</p>
<div class="two">
  <div class="panel over">
    <h3>週期產業分布 (MOPS 產業別)</h3>
    <table><thead><tr><th>產業</th><th>家數</th></tr></thead><tbody>{cyc_rows}</tbody></table>
  </div>
  <div class="playbook">
    <div class="pb"><b>Cycle Position</b><br>價格 YoY (現貨/期貨/ASP) &gt; 10% → 週期回升</div>
    <div class="pb"><b>Demand</b><br>庫存 YoY &lt; 0 → 需求回溫</div>
    <div class="pb"><b>Strength</b><br>產能利用率 &gt; 85% → 景氣強</div>
    <div class="pb"><b>Profit Cycle</b><br>毛利率 YoY &gt; 0 → 週期回升</div>
  </div>
</div>

<div class="two">
  <div class="panel">
    <h3>每月 1–10 號工作流 · monthly cadence</h3>
    <ol class="flow">
      <li><b>DAY 1–3</b> 抓取 MOPS 最新月營收 → parquet/duckdb 增量合併 (36 個月視窗)</li>
      <li><b>DAY 4–6</b> Layer1 濾網: 累計YoY ≥ {cum_strong}% 且未連續下滑, 標記加速/減速</li>
      <li><b>DAY 7–8</b> Layer2: 連續 ≥3 月 YoY 正, 平均YoY ≥ {mean_strong}%, 低波動</li>
      <li><b>DAY 9</b> Layer3 季節性 + 族群/週期分流</li>
      <li><b>DAY 10</b> 產出當月結論 + 規則檢討 (見右)</li>
    </ol>
  </div>
  <div class="panel warn">
    <h3>每月 10 號 · 檢討提醒 · review</h3>
    <ul class="review">
      <li>是否過度依賴單月 YoY / MoM?</li>
      <li>是否忽略基期效應? (用 2年CAGR 交叉檢查)</li>
      <li>是否有營收成長但獲利惡化的公司被誤選? (加毛利率/ROE)</li>
      <li>是否有高波動公司被誤判為成長?</li>
      <li>週期股是否誤用月營收判斷?</li>
    </ul>
  </div>
</div>

<footer>TAIWAN REVENUE MOMENTUM ENGINE v1.5 · 三層動能 + VIA 31 族群零遺漏 + 全市場週期六大類 ·
紅▲成長 綠▼衰退 · PARQUET/DUCKDB 累計增量 · 量化篩選結果, 非投資建議</footer>
</div>
</body>
</html>"""
