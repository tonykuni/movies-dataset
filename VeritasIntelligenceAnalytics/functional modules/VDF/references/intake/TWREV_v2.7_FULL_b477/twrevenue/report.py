"""report.py -- 單頁 HTML 儀表板 (視覺鎖定: VIA 族群分類 v1.1 風格).

視覺規範 (鎖定, 不隨 OS 深色模式改變):
    紙感底色 #f5f4f0 / 白卡片 / 細線 #dbd9d3
    Syne (標題) + DM Mono (數字/標籤) + DM Sans/Noto Sans TC (內文)
    台股慣例紅漲綠跌: 成長 = 紅 ▲ (#c96b5a), 衰退 = 綠 ▼ (#5a9e6f)
矩陣對齊: 表頭與資料列共用同一 grid 欄位定義, 數字右對齊。
無橫向捲軸: 窄螢幕依欄位優先級自動收合次要欄。
"""
from __future__ import annotations

import datetime as dt
import html as _html

import numpy as np
import pandas as pd


# ── 格式 helpers: 紅▲成長 / 綠▼衰退 ─────────────────────────
def _pct(v, digits=1):
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
    if v is None or pd.isna(v):
        return "—"
    yi = v / 100000.0
    return f"{yi:,.2f} 億" if yi >= 1 else f"{v/10000:,.1f} 千萬"


def _score_bar(score):
    if score is None or pd.isna(score):
        return '<span class="flat">—</span>'
    p = max(0, min(100, float(score)))
    return (f'<div class="bar2"><div class="bar2-fill" style="width:{p:.0f}%"></div>'
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


def _bo_badge(v):
    """突破判定徽章: 真突破=紅, 假突破=綠(警示), 其他=灰."""
    s = str(v)
    if s == "真突破":
        return '<span class="vb bup">真突破</span>'
    if "低基期" in s:
        return f'<span class="vb bdn">{_html.escape(s)}</span>'
    if "兩年無成長" in s or "TTM未創高" in s:
        return f'<span class="vb bam">{_html.escape(s)}</span>'
    return f'<span class="vb bmut">{_html.escape(s)}</span>'


def _gate(ok):
    return '<span class="up">✔</span>' if ok else '<span class="down">✘</span>'


def _confirm_html(c):
    if c is True or str(c) == "True":
        return '<span class="teal">✔ 確認</span>'
    if c is False or str(c) == "False":
        return '<span class="am">✘ 背離</span>'
    return '<span class="flat">—</span>'


_ROLE = {"L": ("LEADER", "var(--up)"), "P": ("PEER", "var(--blue)"),
         "G": ("LAGGARD", "var(--mut2)")}


def _role_chip(role):
    lab, col = _ROLE.get(str(role), ("—", "var(--mut2)"))
    return f'<span class="cls" style="background:{col}">{lab}</span>'


# ── 一般個股表格 ────────────────────────────────────────────
_RIGHT = {"pct", "num", "int", "rev", "score"}


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
            elif kind == "gate":
                tds.append(f'<td class="num">{_gate(bool(v))}</td>')
            elif kind == "bov":
                tds.append(f'<td>{_bo_badge(v)}</td>')
            elif kind == "ratio":
                tds.append(f'<td class="num">{"—" if pd.isna(v) else f"{float(v):.2f}"}</td>')
            else:
                tds.append(f'<td>{_html.escape(str(v))}</td>')
        out.append("<tr>" + "".join(tds) + "</tr>")
    return "\n".join(out)


def _table(df, cols, headers, cls=""):
    """表頭對齊方向與該欄資料一致."""
    if df is None or df.empty:
        return '<p class="empty">此類別目前無符合的公司。</p>'
    head = "".join(
        f'<th class="ta-r">{h}</th>' if kind in _RIGHT else f"<th>{h}</th>"
        for h, (_k, kind) in zip(headers, cols))
    c = f' class="{cls}"' if cls else ""
    return f'<table{c}><thead><tr>{head}</tr></thead><tbody>{_rows(df, cols)}</tbody></table>'


def _member_table(analysis, groups, grp, level="group"):
    from .groups import group_members_detail
    m = group_members_detail(analysis, groups, grp, level=level)
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
        rows += ("<tr>"
                 f'<td class="mono">{_html.escape(str(d["stock_id"]))}</td>'
                 f'<td class="name">{_html.escape(str(d.get("name","")))}</td>'
                 f'<td>{chip}</td>'
                 f'<td class="score">{_score_bar(d.get("score"))}</td>'
                 f'<td class="num">{_pct(d.get("cum_yoy"))}</td>'
                 f'<td class="num">{_pct(d.get("yoy"))}</td>'
                 f'<td class="num">{_pct(d.get("mom"))}</td>'
                 f'<td>{_season_html(d.get("seasonality",""))}</td>'
                 f'<td>{_tier_html(d.get("tier",""))}</td></tr>')
    return ('<table class="mtab"><thead><tr><th>代號</th><th>名稱</th><th>角色</th>'
            '<th class="ta-r">動能分數</th><th class="ta-r">累計YoY</th>'
            '<th class="ta-r">單月YoY</th><th class="ta-r">MoM</th>'
            f'<th>季節訊號</th><th>分級</th></tr></thead><tbody>{rows}</tbody></table>')


# ── 族群矩陣 (兩階層: L1 大類 -> L2 子族群 -> 個股) ──────────
def _group_cells(r, lead_html):
    """L1/L2 共用的一列 grid 儲存格 — 欄數與 _VIA_HEADER 完全一致."""
    return (f'<span class="grk">{int(r["rank"])}</span>'
            f'<span class="gnm">{_html.escape(str(r["group"]))}</span>'
            f'{lead_html}'
            f'<span>{_verdict_badge(r["verdict"])}</span>'
            f'<span class="cScore">{_score_bar(r["group_score"])}</span>'
            f'<span class="gm ga-r">{_pct(r["agg_cum_yoy"])}</span>'
            f'<span class="gm ga-r">{_pct(r["agg_yoy"])}</span>'
            f'<span class="gm ga-r cBreadth">'
            f'{_fmt(r["breadth_pos"], pct=True, digits=0)}</span>'
            f'<span class="gm ga-r cPref">{int(r["n_pref"])}/{int(r["covered"])}</span>'
            f'<span class="gm cConfirm">{_confirm_html(r["leader_confirm"])}</span>')


def _two_level_rows(parent_table, group_table, analysis, groups):
    """L1 大類 (可展開) -> L2 子族群 (可展開) -> 個股明細."""
    from .groups import subgroups_of
    out = ""
    for _, p in parent_table.iterrows():
        pname = str(p["group"])
        subs = subgroups_of(group_table, groups, pname)
        n_sub = int(p.get("n_subgroups", len(subs)) or len(subs))
        phead = _group_cells(
            p, f'<span class="glead cLead gsub">{n_sub} 子族群</span>')
        inner = "".join(
            f'<details class="grp l2"><summary>'
            f'{_group_cells(s, _lead_span(s))}</summary>'
            f'<div class="gbody">{_member_table(analysis, groups, str(s["group"]))}'
            f'</div></details>' for _, s in subs.iterrows())
        if not inner:      # 無子群明細 -> 直接列個股
            inner = (f'<div class="gbody">'
                     f'{_member_table(analysis, groups, pname, level="parent")}</div>')
        out += (f'<details class="grp l1"><summary>{phead}</summary>'
                f'<div class="gnest">{inner}</div></details>')
    return out


def _lead_span(r):
    lead = (str(r["leader_names"])
            if pd.notna(r["leader_names"]) and str(r["leader_names"]) else "—")
    return f'<span class="glead cLead">{_html.escape(lead)}</span>'


def _group_details(r, analysis, groups, cyclical=False):
    grp = str(r["group"])
    lead = str(r["leader_names"]) if pd.notna(r["leader_names"]) and str(r["leader_names"]) else "—"
    if cyclical:
        cells = (f'<span class="grk">{int(r["rank"])}</span>'
                 f'<span class="gnm">{_html.escape(grp)}</span>'
                 f'<span>{_verdict_badge(r["verdict"])}</span>'
                 f'<span class="gm ga-r">{_pct(r["agg_cum_yoy"])}</span>'
                 f'<span class="gm ga-r">{_pct(r["agg_yoy"])}</span>'
                 f'<span class="gm ga-r cFam">{int(r["covered"])}/{int(r["members"])}</span>')
    else:
        cells = (f'<span class="grk">{int(r["rank"])}</span>'
                 f'<span class="gnm">{_html.escape(grp)}</span>'
                 f'<span class="glead cLead">{_html.escape(lead)}</span>'
                 f'<span>{_verdict_badge(r["verdict"])}</span>'
                 f'<span class="cScore">{_score_bar(r["group_score"])}</span>'
                 f'<span class="gm ga-r">{_pct(r["agg_cum_yoy"])}</span>'
                 f'<span class="gm ga-r">{_pct(r["agg_yoy"])}</span>'
                 f'<span class="gm ga-r cBreadth">{_fmt(r["breadth_pos"], pct=True, digits=0)}</span>'
                 f'<span class="gm ga-r cPref">{int(r["n_pref"])}/{int(r["covered"])}</span>'
                 f'<span class="gm cConfirm">{_confirm_html(r["leader_confirm"])}</span>')
    return (f'<details class="grp"><summary>{cells}</summary>'
            f'<div class="gbody">{_member_table(analysis, groups, grp)}</div></details>')


_VIA_HEADER = ('<div class="ghd"><span></span><span class="ga-r">#</span>'
               '<span>族群</span><span class="cLead">龍頭／子群</span><span>動能判定</span>'
               '<span class="cScore">族群分數</span><span class="ga-r">加總累計YoY</span>'
               '<span class="ga-r">加總YoY</span><span class="ga-r cBreadth">廣度YoY&gt;0</span>'
               '<span class="ga-r cPref">優選</span><span class="cConfirm">龍頭確認</span></div>')

_SECTOR_HEADER = ('<div class="ghd"><span></span><span class="ga-r">#</span>'
                  '<span>週期類</span><span>判定</span>'
                  '<span class="ga-r">加總累計YoY</span><span class="ga-r">加總YoY</span>'
                  '<span class="ga-r cFam">家數</span></div>')


def _group_section(gt, analysis, groups, sector_table=None, sector_groups=None,
                   parent_table=None):
    if gt is None or gt.empty:
        return ""
    noncyc = gt[~gt["is_cyclical"]]
    n_accel = int((noncyc["verdict"] == "族群加速").sum())
    n_weak = int((noncyc["verdict"] == "族群轉弱").sum())
    two_level = parent_table is not None and not parent_table.empty
    if two_level:
        via_html = _two_level_rows(parent_table, gt, analysis, groups)
    else:
        via_html = "".join(_group_details(r, analysis, groups)
                           for _, r in gt.iterrows())

    cyc_block = ""
    if sector_table is not None and not sector_table.empty:
        n_cyc_cos = int(sector_table["covered"].sum())
        cyc_html = "".join(_group_details(r, analysis, sector_groups, cyclical=True)
                           for _, r in sector_table.iterrows())
        cyc_block = (
            f'<h2>週期分流 · 全市場六大類 <span class="en">TWSE+TPEX 依 MOPS 產業別'
            f'自動歸類 · {n_cyc_cos} tickers · 不看月營收</span></h2>'
            f'<div class="gwrap"><div class="gmx sector">{_SECTOR_HEADER}{cyc_html}</div></div>')

    n_g = groups["group"].nunique() if not groups.empty else 0
    n_t = groups["stock_id"].nunique() if not groups.empty else 0
    n_p = groups["parent"].nunique() if ("parent" in groups and not groups.empty) else 0
    head = (f'熱門族群動能矩陣 <span class="en">two-level · {n_p} 大類 / {n_g} 子族群'
            '</span>' if two_level else
            '熱門族群動能矩陣 <span class="en">grouping momentum · leader confirm</span>')
    lvl = ('兩階層展開: <b>L1 大類 → L2 子族群 → 個股</b>。L1 加總已<b>依個股去重</b>'
           '(同一檔跨子群不重複計入)。' if two_level else '點任一列展開個別成員。')
    return (
        '<div class="panel0">'
        f'<h2>{head}</h2>'
        '<p class="desc">VIA 策展族群 (LEADER/PEER/LAGGARD) × 引擎實證月營收動能。'
        f'加總表現 = 族群營收加權 YoY (Σ本期營收 / Σ去年同期 − 1)。{lvl}'
        '龍頭確認 = 龍頭營收動能 ≥ 族群中位, ✘ 背離值得警覺。'
        f'全部 <b>{n_g} 子族群零遺漏</b> (週期群置底標示) · '
        f'加速 <b class="up">▲ {n_accel}</b> · 轉弱 <b class="down">▼ {n_weak}</b>。</p>'
        f'<div class="gwrap"><div class="gmx">{_VIA_HEADER}{via_html}</div></div>'
        f'{cyc_block}'
        f'<p class="gsrc">族群分類 SSOT: <code>twrevenue/groups.csv</code> '
        f'({n_p} 大類 / {n_g} 子族群 / {n_t} 檔, 兩階層) · '
        f'驗證 <code>python -m twrevenue.cli groups</code> · '
        f'測試 <code>python -m twrevenue.cli selftest</code></p></div>')


# ── 產業階層區塊 (電子 / 非電子 / 金融 -> 中類 -> 小類) ──────
def _hier_row(r, indent=0, marker=False):
    """階層一列 (grid 對齊).

    marker=True 供 L3 使用: L1/L2 由 summary::before 的 ▸ 佔掉第一格,
    L3 是普通 div 沒有該偽元素, 必須補一個空格位, 否則兩層會整列錯開一欄。
    """
    pad = f' style="padding-left:{indent}px"' if indent else ""
    lead = "<span></span>" if marker else ""
    return (lead +
            f'<span class="grk">{int(r["covered"])}</span>'
            f'<span class="gnm"{pad}>{_html.escape(str(r["key"]))}</span>'
            f'<span>{_verdict_badge(r["verdict"])}</span>'
            f'<span class="cScore">{_score_bar(r["score"])}</span>'
            f'<span class="gm ga-r">{_pct(r["agg_cum_yoy"])}</span>'
            f'<span class="gm ga-r">{_pct(r["agg_yoy"])}</span>'
            f'<span class="gm ga-r cBreadth">{_fmt(r["breadth_pos"], pct=True, digits=0)}</span>'
            f'<span class="gm ga-r cPref">{int(r["n_pref"])}/{int(r["covered"])}</span>'
            f'<span class="gm ga-r cFam">{int(r["n_cyclical"])}</span>')


_HIER_HEADER = ('<div class="ghd"><span></span><span class="ga-r">家數</span>'
                '<span>產業</span><span>動能判定</span><span class="cScore">動能分數</span>'
                '<span class="ga-r">加總累計YoY</span><span class="ga-r">加總YoY</span>'
                '<span class="ga-r cBreadth">廣度YoY&gt;0</span>'
                '<span class="ga-r cPref">優選</span>'
                '<span class="ga-r cFam">週期股</span></div>')


def _hierarchy_section(analysis, cfg):
    from . import taxonomy as T
    if "sector_l1" not in analysis.columns:
        return ""
    l1 = T.rollup(analysis, "sector_l1", cfg)
    if l1.empty:
        return ""
    order = {k: i for i, k in enumerate(T.L1_ORDER)}
    l1 = l1.sort_values("key", key=lambda s: s.map(lambda v: order.get(v, 9)))

    blocks = ""
    for _, r1 in l1.iterrows():
        l2 = T.rollup(analysis, "sector_l2", cfg, parent=r1["key"])
        inner = ""
        for _, r2 in l2.iterrows():
            l3 = T.rollup(analysis, "industry_canon", cfg, parent=r2["key"])
            l3rows = "".join(
                f'<div class="hrow l3">{_hier_row(r3, indent=14, marker=True)}</div>'
                for _, r3 in l3.iterrows())
            inner += (f'<details class="grp l2"><summary>{_hier_row(r2, indent=7)}</summary>'
                      f'<div class="l3wrap">{l3rows}</div></details>')
        blocks += (f'<details class="grp l1" open><summary>{_hier_row(r1)}</summary>'
                   f'<div class="l2wrap">{inner}</div></details>')

    amb = int(analysis.get("industry_ambiguous", pd.Series(dtype=bool)).sum())
    unk = int(analysis.get("industry_unknown", pd.Series(dtype=bool)).sum()) \
        if "industry_unknown" in analysis else 0
    a = T.audit()
    return (
        '<div class="panel0">'
        '<h2>產業分類階層 <span class="en">taiwan sector hierarchy · '
        'electronics / non-electronics / financials</span></h2>'
        '<p class="desc">台股慣用三分法 <b>電子 / 非電子 / 金融</b> → 中類 → '
        'TWSE·TPEX 官方產業別 (小類)。加總 = 營收加權 YoY,反映各層真實體量。'
        '<b>點中類可展開小類</b>。'
        f'　SSOT 正規化: {a["n_canon"]} 個正式產業別 · {a["n_alias"]} 組同義字 '
        f'(TWSE/TPEX 後綴差異、歷史更名、上櫃專有類別已整合)'
        f'{f" · 歷史混類 {amb} 檔不強制拆解" if amb else ""}'
        f'{f" · 未知產業 {unk} 檔" if unk else ""}。</p>'
        f'<div class="gwrap"><div class="gmx hier">{_HIER_HEADER}{blocks}</div></div></div>')


# ── 國際產業對照區塊 (GICS / yfinance / ICB) ─────────────────
def _intl_row(r, zh_map=None, sub=""):
    name = str(r["key"])
    zh = f' <span class="flat">{_html.escape(zh_map[name])}</span>' if zh_map and name in zh_map else ""
    return (f'<span class="grk">{int(r["covered"])}</span>'
            f'<span class="gnm">{_html.escape(name)}{zh}</span>'
            f'<span class="glead cLead">{_html.escape(sub)}</span>'
            f'<span>{_verdict_badge(r["verdict"])}</span>'
            f'<span class="cScore">{_score_bar(r["score"])}</span>'
            f'<span class="gm ga-r">{_pct(r["agg_cum_yoy"])}</span>'
            f'<span class="gm ga-r">{_pct(r["agg_yoy"])}</span>'
            f'<span class="gm ga-r cBreadth">{_fmt(r["breadth_pos"], pct=True, digits=0)}</span>'
            f'<span class="gm ga-r cPref">{int(r["n_pref"])}/{int(r["covered"])}</span>'
            f'<span class="gm ga-r cFam">{int(r["n_cyclical"])}</span>')


_INTL_HEADER = ('<div class="ghd"><span></span><span class="ga-r">家數</span>'
                '<span>GICS Sector (S&amp;P 500 / Dow Jones)</span>'
                '<span class="cLead">yfinance · ICB</span><span>動能判定</span>'
                '<span class="cScore">動能分數</span>'
                '<span class="ga-r">加總累計YoY</span><span class="ga-r">加總YoY</span>'
                '<span class="ga-r cBreadth">廣度YoY&gt;0</span>'
                '<span class="ga-r cPref">優選</span>'
                '<span class="ga-r cFam">週期股</span></div>')


def _intl_section(analysis, cfg):
    from . import intl as I
    if "gics_sector" not in analysis.columns:
        return ""
    g = I.rollup(analysis, "gics_sector", cfg)
    if g.empty:
        return ""
    rows = ""
    for _, r in g.iterrows():
        gs = str(r["key"])
        sub = f'{I.GICS_TO_YF.get(gs,"—")} · {I.GICS_TO_ICB.get(gs,"—")}'
        rows += f'<div class="hrow intl"><span></span>{_intl_row(r, I.GICS_ZH, sub)}</div>'

    # Morningstar 3 super sector (yfinance 最上層) 摘要
    sup = I.rollup(analysis, "yf_super", cfg)
    sup_cards = ""
    for _, r in sup.iterrows():
        k = str(r["key"])
        sup_cards += (
            f'<div class="pb"><b>{_html.escape(k)} · {_html.escape(I.YF_SUPER_ZH.get(k,""))}</b><br>'
            f'{int(r["covered"])} 檔 · 加總累計YoY {_pct(r["agg_cum_yoy"])} · '
            f'加總YoY {_pct(r["agg_yoy"])}</div>')

    a = I.audit()
    n_mixed = int(analysis.get("gics_mixed", pd.Series(dtype=bool)).sum())
    n_unmapped = len(I.unmapped(analysis))
    covered = int(g["covered"].sum())
    return (
        '<div class="panel0">'
        '<h2>國際產業分類對照 <span class="en">gics (s&amp;p 500 / dow jones) · '
        'yfinance (morningstar) · icb (ftse russell)</span></h2>'
        '<p class="desc">台股產業別對映到國際標準,方便和 S&amp;P 500 做跨市場比較、'
        '或直接接 yfinance 拉價量資料。'
        '<b>三套標準的關係常被混淆</b>:<b>S&amp;P 500 與道瓊用的是同一套 GICS</b> '
        '(S&amp;P Dow Jones Indices 與 MSCI 共同維護,11 sectors);'
        '<b>ICB</b> 曾是 Dow Jones 與 FTSE 各半合資,但 Dow Jones 已於 <b>2011 年賣掉持股</b>,'
        '現由 FTSE Russell 維護;'
        '<b>yfinance 回傳的 sector 不是 GICS</b>,而是 Yahoo 採用的 Morningstar 分類 '
        '(11 sectors 可與 GICS 一對一,但名稱不同 — 直接拿字串比對會全部對不上)。'
        f'　已對映 {covered} 檔 / {a["n_industry"]} 個台股產業別 · '
        f'{a["n_override"]} 組個股覆寫 (以產業別設防)'
        f'{f" · 跨 sector 混類 {n_mixed} 檔" if n_mixed else ""}'
        f'{f" · <b>未對映 {n_unmapped} 檔</b> (產業別為「其他」或未知, 不計入彙總)" if n_unmapped else ""}。</p>'
        f'<div class="gwrap"><div class="gmx intl">{_INTL_HEADER}{rows}</div></div>'
        '<h3 class="sub2">Morningstar Super Sector <span class="en">yfinance 最上層 · '
        '與台股電子/非電子/金融同屬粗分層級</span></h3>'
        f'<div class="playbook">{sup_cards}</div></div>')


# ── 真突破區塊 ─────────────────────────────────────────────
def _breakout_section(bo, cfg):
    from . import breakout as B
    if bo is None or bo.empty:
        return ""
    bc = cfg["breakout"]
    n = bc.get("top_n", 30)
    s = B.summary(bo)
    real = bo[bo["verdict"] == B.V_REAL].head(n)
    fake = bo[bo["verdict"].isin([B.V_LOWBASE, B.V_NO_CAGR])] \
        .sort_values("yoy", ascending=False).head(n)

    cols_real = [
        ("rank", "int"), ("stock_id", "id"), ("name", "name"), ("industry", "name"),
        ("score", "score"), ("revenue", "rev"), ("ath_margin", "pct"),
        ("ath_streak", "int"), ("yoy", "pct"), ("ttm_yoy", "pct"),
        ("base_pct", "num"), ("base_ratio", "ratio"), ("cagr_2y", "pct"),
    ]
    head_real = ["#", "代號", "名稱", "產業", "突破強度", "當月營收", "超越前高",
                 "連創高", "單月YoY", "TTM YoY", "基期百分位", "基期比", "2年CAGR"]

    cols_fake = [
        ("stock_id", "id"), ("name", "name"), ("verdict", "bov"),
        ("yoy", "pct"), ("g1_ath", "gate"), ("g4_base", "gate"), ("g5_cagr", "gate"),
        ("base_pct", "num"), ("base_ratio", "ratio"), ("cagr_2y", "pct"),
    ]
    head_fake = ["代號", "名稱", "判定", "單月YoY", "創高", "基期", "2年",
                 "基期百分位", "基期比", "2年CAGR"]

    return (
        '<div class="panel0">'
        '<h2>真突破偵測 <span class="en">genuine breakout · ath + strong yoy − low-base illusion</span></h2>'
        '<p class="desc">抓出<b>表現特別優異</b>的公司: 創歷史新高、年增率強,'
        '<b>且排除「YoY 高只是因為去年基期低」的假象</b>。五道關卡全過才算真突破 — '
        f'① 當月創歷史新高 ② 近12月滾動營收(TTM)也創高(排除單月一次性訂單) '
        f'③ 單月YoY ≥ {bc["min_yoy"]:.0f}% ④ 基期不低(去年同月百分位 ≥ {bc["min_base_pct"]:.0f}% '
        f'且 / 其前12月中位數 ≥ {bc["min_base_ratio"]:.2f}) ⑤ 兩年CAGR ≥ {bc["min_cagr_2y"]:.0f}% '
        f'(完全跳過去年基期)。'
        f'　候選 <b>{s["candidates"]}</b> 檔 → 真突破 <b class="up">▲ {s["real"]}</b> · '
        f'低基期假象 <b class="down">▼ {s["lowbase"]}</b> · '
        f'兩年無成長 {s["no_cagr"]} · 未創高 {s["no_ath"]} · 單月暴衝 {s["oneoff"]}。</p>'
        f'<div class="over tbo">{_table(real, cols_real, head_real)}</div>'
        '<h3 class="sub2">被濾掉的假突破 <span class="en">rejected · why the filter matters</span></h3>'
        '<p class="desc">這些公司 YoY 看起來很漂亮 (有些甚至比上面的真突破還高),'
        '但基期塌陷或兩年沒成長 — <b>只看 YoY 就會買在這裡</b>。'
        '✔/✘ 標示各關卡通過與否。</p>'
        f'<div class="over tfake">{_table(fake, cols_fake, head_fake)}</div></div>')


# ── 主組版 ─────────────────────────────────────────────────
def build_dashboard(analysis, cfg, data_month=None, group_table=None, groups=None,
                    sector_table=None, sector_groups=None, breakout_table=None,
                    parent_table=None):
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

    from . import breakout as B
    n_real = int((breakout_table["verdict"] == B.V_REAL).sum()) \
        if breakout_table is not None and not breakout_table.empty else 0

    accel = noncyc[noncyc["tier"] == "優選"].head(top_n)
    decline = noncyc[noncyc["tier"] == "警戒"].sort_values("cum_yoy").head(top_n)
    star = noncyc[noncyc["seasonality"].astype(str).str.contains("淡季不淡")].head(top_n)
    pat_counts = noncyc["pattern"].value_counts()
    cyc_by_ind = (cyc.groupby("industry")["stock_id"].count().sort_values(ascending=False)
                  if not cyc.empty else pd.Series(dtype=int))

    cols_main = [("rank", "int"), ("stock_id", "id"), ("name", "name"),
                 ("industry", "name"), ("score", "score"), ("cum_yoy", "pct"),
                 ("yoy", "pct"), ("mom", "pct"), ("consec_pos_yoy", "int"),
                 ("cagr_2y", "pct"), ("seasonality", "season"), ("pattern", "name")]
    head_main = ["#", "代號", "名稱", "產業", "動能分數", "累計YoY", "單月YoY",
                 "MoM", "連正月", "2年CAGR", "季節訊號", "型態"]
    cols_side = [("stock_id", "id"), ("name", "name"), ("industry", "name"),
                 ("cum_yoy", "pct"), ("yoy", "pct"), ("mom", "pct"),
                 ("seasonality", "season"), ("pattern", "name")]
    head_side = ["代號", "名稱", "產業", "累計YoY", "單月YoY", "MoM", "季節訊號", "型態"]

    cyc_rows = "".join(
        f'<tr><td class="name">{_html.escape(str(i))}</td><td class="num">{n}</td></tr>'
        for i, n in cyc_by_ind.items()) or '<tr><td colspan="2" class="flat">無</td></tr>'

    pat_rows, max_pat = "", int(pat_counts.max()) if len(pat_counts) else 1
    for pat, n in pat_counts.items():
        pat_rows += (f'<div class="patrow"><span class="patlabel">{_html.escape(str(pat))}</span>'
                     f'<span class="patbar"><span class="patfill" style="width:{100*n/max_pat:.0f}%"></span></span>'
                     f'<span class="patn">{n}</span></div>')

    return _TEMPLATE.format(
        title=_html.escape(rc["title"]),
        gen=dt.datetime.now().strftime("%Y-%m-%d %H:%M"),
        data_month=data_month or "—",
        total=total, n_pref=n_pref, n_watch=n_watch, n_warn=n_warn, n_cyc=n_cyc,
        n_real=n_real,
        n_groups=groups["group"].nunique() if not groups.empty else 0,
        breakout_section=_breakout_section(breakout_table, cfg),
        hierarchy_section=_hierarchy_section(analysis, cfg),
        intl_section=_intl_section(analysis, cfg),
        group_section=_group_section(group_table, analysis, groups,
                                     sector_table, sector_groups, parent_table),
        pat_rows=pat_rows,
        accel_table=_table(accel, cols_main, head_main),
        decline_table=_table(decline, cols_side, head_side),
        star_table=_table(star, cols_side, head_side),
        cyc_rows=cyc_rows,
        cum_strong=cfg["analyze"]["cum_yoy_strong"],
        mean_strong=cfg["analyze"]["mean_yoy_strong"],
    )


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
  .wrap{{max-width:1680px;margin:0 auto;padding:0 clamp(10px,2vw,24px) 60px;}}
  .bar{{position:fixed;top:0;left:0;right:0;height:4px;background:var(--reson);opacity:.92;z-index:50;}}
  header{{position:relative;padding:20px 0 9px;margin-bottom:10px;border-bottom:2px solid var(--ink);}}
  .kicker{{font:700 10px 'DM Mono',monospace;letter-spacing:2.2px;color:var(--mut);text-transform:uppercase;margin-bottom:7px;}}
  h1{{font:800 19px/1.2 'Syne',sans-serif;color:var(--ink);}}
  h1 span{{color:var(--up);}}
  .sub{{margin-top:6px;font:400 10.5px/1.55 'DM Sans','Noto Sans TC',sans-serif;color:var(--mut);max-width:1000px;}}
  .sub b{{color:var(--ink2);}}
  .gov{{display:flex;align-items:center;gap:10px;flex-wrap:wrap;background:#1e1d1a;border-radius:3px;padding:7px 14px;margin:12px 0;}}
  .gov .lk{{font:700 8.5px 'DM Mono',monospace;letter-spacing:.8px;color:#7fd0a0;text-transform:uppercase;}}
  .gov .pill{{font:600 7.5px 'DM Mono',monospace;color:#cfcabf;}}
  .gov .ver{{margin-left:auto;font:700 8px 'DM Mono',monospace;color:#fff;background:#5a9e6f;border-radius:3px;padding:2px 8px;}}
  .legend{{display:flex;gap:14px;flex-wrap:wrap;margin:10px 0 4px;font:600 9px 'DM Mono',monospace;color:var(--mut);}}
  .legend span{{display:inline-flex;align-items:center;gap:5px;}}
  .dot{{width:11px;height:11px;border-radius:2px;}}
  .scards{{display:grid;grid-template-columns:repeat(6,1fr);gap:9px;margin:12px 0 4px;}}
  .sc{{background:var(--paper);border:1px solid var(--line);border-radius:5px;padding:9px 14px;}}
  .sc .v{{font:800 21px 'Syne',sans-serif;line-height:1;color:var(--ink);}}
  .sc .l{{font:600 8px 'DM Mono',monospace;color:var(--mut);text-transform:uppercase;letter-spacing:.6px;margin-top:4px;}}
  h2{{font:800 13px 'Syne',sans-serif;color:var(--ink);margin:24px 0 4px;padding-bottom:5px;
    border-bottom:1px solid var(--line);display:flex;align-items:baseline;gap:8px;flex-wrap:wrap;}}
  h2 .en{{font:600 8px 'DM Mono',monospace;color:var(--mut2);letter-spacing:1px;text-transform:uppercase;}}
  h3.sub2{{font:800 11px 'Syne',sans-serif;color:var(--ink);margin:18px 0 2px;display:flex;gap:8px;align-items:baseline;flex-wrap:wrap;}}
  h3.sub2 .en{{font:600 7.5px 'DM Mono',monospace;color:var(--mut2);letter-spacing:1px;text-transform:uppercase;}}
  .panel0{{margin-top:6px;}}
  .desc{{color:var(--mut);font:400 10.5px/1.6 'DM Sans','Noto Sans TC',sans-serif;margin:4px 0 10px;max-width:1180px;}}
  .desc b{{color:var(--ink2);}}
  .panel{{background:var(--paper);border:1px solid var(--line);border-radius:6px;padding:13px 15px;margin-top:12px;}}
  .panel.warn{{border-left:3px solid var(--am);}}
  .panel h3{{font:800 11px 'Syne',sans-serif;color:var(--ink);margin-bottom:8px;}}
  .up{{color:var(--up);font-weight:600;}}
  .down{{color:var(--down);font-weight:600;}}
  .flat{{color:var(--mut2);}}
  .teal{{color:var(--teal);font-weight:700;}}
  .am{{color:var(--am);font-weight:700;}}
  .small{{font-size:9.5px;}}
  .cls{{font:700 7px 'DM Mono',monospace;color:#fff;border-radius:3px;padding:2px 5px;
    min-width:48px;text-align:center;letter-spacing:.4px;display:inline-block;}}
  .vb{{font:700 7.5px 'DM Mono',monospace;color:#fff;border-radius:3px;padding:2px 6px;
    letter-spacing:.4px;white-space:nowrap;}}
  .vb.bup{{background:var(--up);}} .vb.bdn{{background:var(--down);}}
  .vb.bam{{background:var(--am);}} .vb.bmut{{background:var(--mut2);}}
  table{{width:100%;border-collapse:collapse;margin-top:10px;font:500 10px 'DM Mono',monospace;background:var(--paper);}}
  th{{font:700 8px 'DM Mono',monospace;text-transform:uppercase;letter-spacing:.6px;color:var(--mut);
    text-align:left;padding:7px 9px;border-bottom:2px solid var(--ink);background:var(--paper2);white-space:nowrap;}}
  th.ta-r{{text-align:right;}}
  td{{padding:5px 9px;border-bottom:1px solid var(--soft);white-space:nowrap;}}
  tr:hover td{{background:var(--paper2);}}
  td.num,td.score{{text-align:right;font-variant-numeric:tabular-nums;}}
  td.mono{{color:var(--mut);}}
  td.name{{font-family:'Noto Sans TC',sans-serif;font-weight:600;font-size:10.5px;color:var(--ink2);
    max-width:150px;overflow:hidden;text-overflow:ellipsis;}}
  .mtab th:nth-child(-n+3){{text-align:left;}}
  .bar2{{position:relative;height:13px;background:var(--soft);border-radius:3px;min-width:60px;display:inline-block;width:100%;}}
  .bar2-fill{{position:absolute;left:0;top:0;bottom:0;background:var(--blue);border-radius:3px;}}
  .bar2-val{{position:relative;padding-right:5px;font:700 9px 'DM Mono',monospace;color:var(--ink);}}
  .patrow{{display:flex;align-items:center;gap:10px;margin:4px 0;}}
  .patlabel{{width:170px;font:600 10.5px 'Noto Sans TC',sans-serif;}}
  .patbar{{flex:1;height:12px;background:var(--soft);border-radius:3px;overflow:hidden;}}
  .patfill{{display:block;height:100%;background:var(--blue);border-radius:3px;}}
  .patn{{width:36px;text-align:right;font:600 10px 'DM Mono',monospace;}}
  .gwrap{{background:var(--paper);border:1px solid var(--line);border-radius:6px;margin-top:10px;}}
  .gmx{{--pad:12px;--ind:20px;--gap:8px;--gc:14px 24px minmax(110px,1.2fr) minmax(88px,1fr) 104px 92px 110px 98px 82px 54px 76px;}}
  .gmx.sector{{--gc:14px 24px minmax(96px,1fr) 168px 114px 100px 64px;}}
  /* 產業階層: 家數 · 產業 · 判定 · 分數 · 加總累計YoY · 加總YoY · 廣度 · 優選 · 週期股 */
  .gmx.hier{{--gc:14px 44px minmax(126px,1.6fr) 102px 94px 114px 100px 82px 56px 60px;}}
  .gmx.intl{{--gc:14px 44px minmax(180px,1.5fr) minmax(140px,1fr) 102px 94px 114px 100px 82px 56px 60px;}}
  .gmx.hier .ghd{{grid-template-columns:var(--gc);}}
  .grp.l1 > summary{{background:var(--paper2);border-top:1px solid var(--line);}}
  .grp.l1 > summary .gnm{{font-size:13px;}}
  .grp.l2 > summary{{padding-top:5px;padding-bottom:5px;}}
  .grp.l2 > summary .gnm{{font:700 11px 'Noto Sans TC',sans-serif;color:var(--ink2);}}
  /* 兩階層巢狀: 巢狀容器左右 padding 必須為 0, 否則 L2 各欄會與表頭錯位。
     縮排只加在名稱格 (gnm), 數值欄因此與 L1/表頭逐欄精準對齊。 */
  .gnest{{display:block;padding:0;background:rgba(0,0,0,.012);}}
  .gnest .grp.l2{{border-bottom:1px solid var(--soft);}}
  .gnest .grp.l2:last-child{{border-bottom:none;}}
  .grp.l2 > summary .gnm{{padding-left:13px;position:relative;}}
  .grp.l2 > summary .gnm::before{{content:"└";position:absolute;left:1px;
    color:var(--mut2);font-size:9px;font-weight:400;}}
  .gsub{{font:600 10px 'DM Mono',monospace;color:var(--mut2);}}
  .hrow{{display:grid;grid-template-columns:var(--gc);gap:0 var(--gap);align-items:center;
    white-space:nowrap;border-bottom:1px solid var(--soft);}}
  /* 縮排只能加在名稱格, 不可加在列的 padding — 否則彈性名稱欄被擠壓的量
     與縮排量在窄螢幕不再相等, 後面每個數值欄都會橫移 (實測 4~6px)。 */
  .hrow.l3{{padding:4px var(--pad);}}
  .hrow.l3 .gnm{{padding-left:var(--ind);}}
  .hrow.intl{{padding:6px var(--pad);}}   /* 國際對照是平的一層, 不縮排 */
  .hrow.l3 .gnm{{font:500 10px 'Noto Sans TC',sans-serif;color:var(--mut);}}
  .hrow.l3:last-child{{border-bottom:none;}}
  .l2wrap,.l3wrap{{display:block;}}
  .ghd{{display:grid;grid-template-columns:var(--gc);gap:0 var(--gap);align-items:center;
    padding:7px var(--pad) 6px;color:var(--mut);font:700 8px 'DM Mono',monospace;
    text-transform:uppercase;letter-spacing:.6px;border-bottom:2px solid var(--ink);
    background:var(--paper2);white-space:nowrap;}}
  .grp{{border-bottom:1px solid var(--soft);}}
  .grp:last-child{{border-bottom:none;}}
  .grp > summary{{display:grid;grid-template-columns:var(--gc);gap:0 var(--gap);align-items:center;
    padding:7px var(--pad);cursor:pointer;list-style:none;white-space:nowrap;}}
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
  .two{{display:grid;grid-template-columns:1fr 1fr;gap:14px;}}
  .two > *{{min-width:0;}}
  .over{{overflow:hidden;}}
  .playbook{{display:grid;grid-template-columns:1fr 1fr;gap:9px;margin-top:8px;}}
  .pb{{background:var(--paper2);border:1px solid var(--line);border-radius:5px;padding:10px 12px;
    font:400 10.5px/1.5 'Noto Sans TC',sans-serif;}}
  .pb b{{color:var(--blue);font-family:'DM Mono',monospace;font-size:9px;text-transform:uppercase;letter-spacing:.5px;}}
  ol.flow{{margin:6px 0 0;padding-left:18px;font:400 10.5px/1.6 'Noto Sans TC',sans-serif;}}
  ol.flow li{{margin:4px 0;}} ol.flow b{{font-family:'DM Mono',monospace;color:var(--ink);font-size:9.5px;}}
  .review{{list-style:none;border-left:3px solid var(--am);padding-left:12px;}}
  .review li{{padding:4px 0;border-bottom:1px solid var(--soft);font:400 10.5px/1.5 'Noto Sans TC',sans-serif;}}
  .review li:last-child{{border-bottom:none;}}
  .empty{{color:var(--mut2);font-size:10.5px;padding:8px 0;}}
  footer{{margin-top:28px;padding-top:10px;border-top:1px solid var(--line);
    font:500 8.5px 'DM Mono',monospace;color:var(--mut2);text-align:center;letter-spacing:.5px;}}
  /* ===== 響應式: 欄位優先級收合 => 全程無橫向捲軸 ===== */
  @media (max-width:1300px){{
    .tside th:nth-child(3),.tside td:nth-child(3),
    .tside th:nth-child(8),.tside td:nth-child(8){{display:none;}}
    .tbo th:nth-child(4),.tbo td:nth-child(4),
    .tbo th:nth-child(11),.tbo td:nth-child(11){{display:none;}}
  }}
  @media (max-width:1180px){{
    .tmain th:nth-child(4),.tmain td:nth-child(4),
    .tmain th:nth-child(9),.tmain td:nth-child(9),
    .tmain th:nth-child(10),.tmain td:nth-child(10){{display:none;}}
    .tbo th:nth-child(6),.tbo td:nth-child(6){{display:none;}}
  }}
  @media (max-width:1120px){{
    .gmx{{--gc:12px 20px minmax(86px,1.1fr) minmax(66px,.9fr) 92px 76px 96px 86px 68px 46px 64px;}}
    .gmx.sector{{--gc:12px 20px minmax(84px,1fr) 150px 102px 90px 56px;}}
    .gmx.hier{{--gc:12px 38px minmax(100px,1.4fr) 92px 84px 100px 90px 72px 48px 52px;}}
    .gmx.intl{{--gc:12px 38px minmax(140px,1.3fr) minmax(110px,.9fr) 92px 84px 100px 90px 72px 48px 52px;}}
    .gmx{{--pad:9px;--ind:17px;}}
    table,.gm,.glead{{font-size:9.5px;}} .gnm{{font-size:11px;}}
    td{{padding-left:9px;padding-right:9px;}}
    .scards{{grid-template-columns:repeat(4,1fr);}}
  }}
  @media (max-width:920px){{
    .cLead,.cBreadth{{display:none!important;}}
    .gmx{{--gc:12px 20px minmax(92px,1.1fr) 92px 78px 98px 88px 46px 64px;}}
    .gmx.hier{{--gc:12px 36px minmax(92px,1.3fr) 88px 80px 96px 86px 46px 50px;}}
    .gmx.intl{{--gc:12px 36px minmax(120px,1.2fr) 88px 80px 96px 86px 46px 50px;}}
    .two{{grid-template-columns:1fr;}}
    .tbo th:nth-child(12),.tbo td:nth-child(12),
    .tbo th:nth-child(8),.tbo td:nth-child(8){{display:none;}}
    .tfake th:nth-child(9),.tfake td:nth-child(9){{display:none;}}
  }}
  @media (max-width:640px){{
    .cScore,.cPref,.cConfirm{{display:none!important;}}
    .gmx{{--gc:11px 18px minmax(76px,1fr) 86px 92px 82px;}}
    .gmx.sector{{--gc:11px 18px minmax(60px,1fr) 108px 86px 78px 42px;}}
    .gmx.hier{{--gc:11px 30px minmax(68px,1fr) 76px 84px 76px 42px;}}
    .gmx.intl{{--gc:11px 30px minmax(84px,1fr) 76px 84px 76px 42px;}}
    .gmx{{--ind:9px;--gap:6px;}}
    table,.gm{{font-size:9px;}} td,th{{padding:4px 6px;}}
    .tmain th:nth-child(12),.tmain td:nth-child(12),
    .tmain th:nth-child(5),.tmain td:nth-child(5){{display:none;}}
    .tside th:nth-child(3),.tside td:nth-child(3),
    .tside th:nth-child(8),.tside td:nth-child(8){{display:none;}}
    .mtab th:nth-child(3),.mtab td:nth-child(3),
    .mtab th:nth-child(8),.mtab td:nth-child(8){{display:none;}}
    .tbo th:nth-child(5),.tbo td:nth-child(5),
    .tbo th:nth-child(13),.tbo td:nth-child(13),
    .tbo th:nth-child(7),.tbo td:nth-child(7){{display:none;}}
    .tfake th:nth-child(5),.tfake td:nth-child(5),
    .tfake th:nth-child(6),.tfake td:nth-child(6),
    .tfake th:nth-child(7),.tfake td:nth-child(7){{display:none;}}
    .gbody{{padding-left:14px;padding-right:8px;}}
    .scards{{grid-template-columns:repeat(2,1fr);}}
    .sc .v{{font-size:17px;}} .patlabel{{width:112px;}}
  }}
  @media (max-width:460px){{
    .cFam{{display:none!important;}}
    .gmx{{--gc:10px 15px minmax(62px,1fr) 76px 84px 74px;}}
    .gmx.sector{{--gc:10px 14px minmax(50px,1fr) 90px 80px 72px;}}
    .gmx.hier{{--gc:10px 26px minmax(52px,1fr) 66px 76px 68px;}}
    .gmx.intl{{--gc:10px 26px minmax(64px,1fr) 66px 76px 68px;}}
    .gmx{{--pad:8px;--ind:6px;--gap:5px;}}
    table,.gm{{font-size:8.5px;}} .gnm{{font-size:10px;}}
    td,th{{padding:3px 5px;}} .vb{{font-size:6.5px;padding:2px 4px;}}
    .mtab th:nth-child(4),.mtab td:nth-child(4),
    .mtab th:nth-child(9),.mtab td:nth-child(9){{display:none;}}
    .mtab{{font-size:8px;}} .mtab td,.mtab th{{padding:2px 4px;}}
    .mtab td.name{{font-size:9px;max-width:64px;}}
    .tbo th:nth-child(10),.tbo td:nth-child(10){{display:none;}}
    .gbody{{padding-left:10px;padding-right:6px;}}
  }}
  @media (max-width:400px){{
    .gmx{{--gc:10px 13px minmax(44px,1fr) 66px 74px 64px;}}
    .gmx.sector{{--gc:10px 12px minmax(40px,1fr) 78px 70px 64px;}}
    .gmx.hier{{--gc:10px 22px minmax(40px,1fr) 58px 66px 60px;}}
    .gmx.intl{{--gc:10px 22px minmax(48px,1fr) 58px 66px 60px;}}
    .gmx{{--pad:6px;--ind:5px;--gap:4px;}}
    .ghd{{font-size:7px;letter-spacing:.3px;}}
    .gnm{{font-size:9.5px;}} .gm{{font-size:8px;}}
    .wrap{{padding-left:8px;padding-right:8px;}}
  }}
  @media print{{@page{{size:A4 landscape;margin:10mm}}html,body{{background:#fff!important}}}}
</style>
</head>
<body>
<div class="bar"></div>
<div class="wrap">

<header>
  <div class="kicker">Taiwan Revenue Momentum Engine · MOPS 實證月營收 × VIA 族群 · 三層動能 + 真突破偵測</div>
  <h1>台股月營收 <span>動能總表</span> · Revenue Momentum Matrix</h1>
  <p class="sub">資料月份 <b>{data_month}</b> · 產生 {gen} · 來源 <b>MOPS 公開資訊觀測站</b> (TWSE+TPEX 全市場) ·
  三層引擎: <b>累計YoY</b> (主判準) → <b>多月YoY趨勢</b> → <b>MoM vs 季節性</b> ·
  <b>真突破偵測</b>: 創歷史新高 + 年增強 − 低基期假象 · <b>紅▲成長 綠▼衰退</b>。</p>
</header>

<div class="gov">
  <span class="lk">🔒 Visual Locked · VIA Style</span>
  <span class="pill">三層權重 45/35/20</span>
  <span class="pill">真突破 5 道關卡</span>
  <span class="pill">週期六大類分流</span>
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
  <div class="sc"><div class="v" style="color:var(--up)">{n_real}</div><div class="l">真突破 ▲ · genuine</div></div>
  <div class="sc"><div class="v" style="color:var(--teal)">{n_groups}</div><div class="l">族群 · 零遺漏</div></div>
  <div class="sc"><div class="v" style="color:var(--up)">{n_pref}</div><div class="l">優選 ▲ · preferred</div></div>
  <div class="sc"><div class="v" style="color:var(--down)">{n_warn}</div><div class="l">警戒 ▼ · alert</div></div>
  <div class="sc"><div class="v" style="color:var(--am)">{n_cyc}</div><div class="l">週期股 · excluded</div></div>
</div>

{breakout_section}

{hierarchy_section}

{intl_section}

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
月營收 YoY·MoM 嚴重失真 — 已排除於動能排名與真突破偵測, 改用以下判準。</p>
<div class="two">
  <div class="panel over">
    <h3>週期產業分布 (MOPS 產業別)</h3>
    <table><thead><tr><th>產業</th><th class="ta-r">家數</th></tr></thead><tbody>{cyc_rows}</tbody></table>
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
      <li><b>DAY 1–3</b> 抓取 MOPS 最新月營收 → parquet/duckdb 增量合併</li>
      <li><b>DAY 4–6</b> Layer1 濾網: 累計YoY ≥ {cum_strong}% 且未連續下滑</li>
      <li><b>DAY 7–8</b> Layer2: 連續 ≥3 月 YoY 正, 平均YoY ≥ {mean_strong}%, 低波動</li>
      <li><b>DAY 9</b> Layer3 季節性 + 族群/週期分流 + <b>真突破偵測</b></li>
      <li><b>DAY 10</b> 產出當月結論 + 規則檢討 (見右)</li>
    </ol>
  </div>
  <div class="panel warn">
    <h3>每月 10 號 · 檢討提醒 · review</h3>
    <ul class="review">
      <li>是否過度依賴單月 YoY / MoM?</li>
      <li>是否忽略基期效應? (看真突破的基期百分位與基期比)</li>
      <li>是否有營收成長但獲利惡化的公司被誤選? (加毛利率/ROE)</li>
      <li>是否有高波動公司被誤判為成長?</li>
      <li>週期股是否誤用月營收判斷?</li>
    </ul>
  </div>
</div>

<footer>TAIWAN REVENUE MOMENTUM ENGINE v2.0 · 三層動能 + 真突破偵測(5關卡) + VIA 31 族群零遺漏 +
全市場週期六大類 · 紅▲成長 綠▼衰退 · PARQUET/DUCKDB 累計增量 · 量化篩選結果, 非投資建議</footer>
</div>
</body>
</html>"""
