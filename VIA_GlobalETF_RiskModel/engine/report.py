# -*- coding: utf-8 -*-
"""
report.py — M40_Report：JSON 輸出 + Visual Lock HTML 儀表板
=============================================================================
MODULE M40_Report
  [MCFL-M40-C41-F401] write_outputs   — append-only run 目錄 + run_ledger.jsonl
  [MCFL-M40-C41-F402] render_dashboard — 單檔自足 HTML（無外部資源/CDN）

Visual Lock（沿用 MDL008 / RotationEngine 房規，刻意單一淺色主題）：
  bg #f5f4f0 · paper #fff · ink #1e1d1a · 紅漲 #c96b5a · 綠跌 #5a9e6f
  相關性用 藍(+)#4c78a8 ↔ 琥珀(−)#c4943a（與漲跌色系分離）
  色彩永不單獨承載意義：所有色格同列印出數值；狀態 chip 一律帶文字。
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import html as _H
import json
from pathlib import Path

VL = {"bg": "#f5f4f0", "paper": "#ffffff", "ink": "#1e1d1a", "sub": "#6b6a66",
      "bd": "#dbd9d3", "up": "#c96b5a", "down": "#5a9e6f", "blue": "#4c78a8",
      "teal": "#439a9a", "am": "#c4943a", "seal": "#b5291a"}
STATUS = {"good": "#5a9e6f", "warning": "#c4943a", "serious": "#c96b5a",
          "critical": "#b5291a", "pending": "#6b6a66"}
QUAD = {"Q1": VL["up"], "Q2": VL["blue"], "Q3": VL["down"], "Q4": VL["am"]}

HEAT_CAP = {"1d": 0.02, "5d": 0.04, "20d": 0.08, "60d": 0.15, "120d": 0.25}


def esc(s):
    return _H.escape(str(s))


def fmt_pct(v, digits=2):
    if v is None:
        return "—"
    return "%+.*f%%" % (digits, v * 100.0)


def fmt_num(v, digits=2):
    return "—" if v is None else "%.*f" % (digits, v)


def _heat(v, cap, pos=VL["up"], neg=VL["down"]):
    if v is None:
        return "transparent"
    alpha = min(0.80, abs(v) / cap * 0.80)
    hexc = pos if v > 0 else neg
    r, g, b = int(hexc[1:3], 16), int(hexc[3:5], 16), int(hexc[5:7], 16)
    return "rgba(%d,%d,%d,%.3f)" % (r, g, b, alpha)


def _chip(label, status):
    return ('<span class="chip" style="background:%s">%s</span>'
            % (STATUS.get(status, VL["sub"]), esc(label)))


def _spark(values, width=128, height=34, color=VL["blue"]):
    vals = [v for v in values if v is not None]
    if len(vals) < 2:
        return ""
    lo, hi = min(vals), max(vals)
    span = (hi - lo) or 1.0
    pts, n = [], len(values)
    for i, v in enumerate(values):
        if v is None:
            continue
        x = 2 + i * (width - 4) / max(1, n - 1)
        y = height - 3 - (v - lo) / span * (height - 6)
        pts.append("%.1f,%.1f" % (x, y))
    last = pts[-1].split(",")
    return ('<svg viewBox="0 0 %d %d" width="%d" height="%d" aria-hidden="true">'
            '<polyline points="%s" fill="none" stroke="%s" stroke-width="1.6"/>'
            '<circle cx="%s" cy="%s" r="2.4" fill="%s"/></svg>'
            % (width, height, width, height, " ".join(pts), color,
               last[0], last[1], color))


def _meter(value, status):
    if value is None:
        return '<div class="meter"><div class="fill" style="width:0%"></div></div>'
    return ('<div class="meter"><div class="fill" style="width:%.1f%%;background:%s">'
            '</div></div>' % (min(100.0, value), STATUS.get(status, VL["blue"])))


# --------------------------------------------------------------------------- #
# 版面區塊
# --------------------------------------------------------------------------- #

def _sec_header(ds):
    prov = ds["provenance"]
    synthetic = prov.get("data_source") == "synthetic_demo"
    warn = ""
    if synthetic:
        warn = ('<div class="synth">⚠ SYNTHETIC（T4）示範資料 — seed=%s · '
                '僅供管線與儀表板驗證，禁止作為任何投資判讀。正式使用請以 '
                '--prices/--macro 接真實 CSV，或接 MDL008 真流輸出。</div>'
                % prov.get("seed"))
    chip = _chip("T4 SYNTHETIC DEMO" if synthetic else "T3 價量估算",
                 "warning" if synthetic else "good")
    return """
<div class="eyebrow">VIA GLOBAL MARKET RADAR · MDL009 ETFRISK · %s</div>
<h1><span class="seal">理</span>全球 ETF 風險同步觀測 · Risk × Regime × Rotation</h1>
<div class="eyebrow">asof %s · run %s · %s · 紅漲綠跌 · 數值恆列印（色彩不單獨承載意義）</div>
<div class="strip"></div>%s""" % (
        esc(ds["config_version"]), esc(ds["asof"]), esc(ds["run_id"]), chip, warn)


def _sec_regime(reg):
    top = reg["top"]
    bars = []
    for r in reg["ranked"]:
        is_top = r["id"] == top["id"]
        color = VL["blue"] if is_top else VL["bd"]
        bars.append(
            '<div class="rrow"><div class="rname%s">%s</div>'
            '<div class="rtrack"><div class="rfill" style="width:%.0f%%;'
            'background:%s"></div></div><div class="rval">%.0f%%</div></div>'
            % (" strong" if is_top else "", esc(r["name_zh"]),
               r["score"] * 100, color, r["score"] * 100))
    runner = reg.get("runner_up")
    runner_txt = ("次高：%s %.0f%%" % (runner["name_zh"], runner["score"] * 100)
                  if runner else "")
    return """
<div class="card regime">
  <div class="klabel">REGIME BANNER · %s</div>
  <div class="regime-top">%s <span class="conf">信心 %.0f%%</span>
    <span class="sub">%s</span></div>
  %s
</div>""" % (esc(reg["mcfl"]), esc(top["name_zh"]), reg["confidence"] * 100,
             esc(runner_txt), "".join(bars))


def _sec_kpis(scores, pulse, sync):
    tiles = []
    for sid in ("usd_stress", "rate_shock", "credit_stress", "commodity_inflation"):
        s = scores[sid]
        band = s["band"]
        tiles.append("""
<div class="kpi">
  <div class="klabel">%s <span class="mcfl">%s</span></div>
  <div class="kval">%s <span class="unit">/100</span> %s</div>
  %s
  <div class="kspark">%s</div>
</div>""" % (esc(s["name_zh"]), esc(s["mcfl"]),
             fmt_num(s["risk"], 1), _chip(band["label_zh"], band["status"]),
             _meter(s["risk"], band["status"]),
             _spark(s["history"])))
    pd_map = {"risk_on": ("偏風險端", "serious"), "risk_off": ("退守防禦", "warning"),
              "neutral": ("中性", "good")}
    plabel, pstat = pd_map.get(pulse["direction"], ("中性", "good"))
    tiles.append("""
<div class="kpi">
  <div class="klabel">%s <span class="mcfl">%s</span></div>
  <div class="kval">%s <span class="unit">z</span> %s</div>
  <div class="knote">風險腿 %s − 防禦腿 %s</div>
  <div class="kspark">%s</div>
</div>""" % (esc(pulse["name_zh"]), esc(pulse["mcfl"]), fmt_num(pulse["z"], 2),
             _chip(plabel, pstat),
             esc("+".join(t for t, _ in pulse["legs"]["risk"])),
             esc("+".join(t for t, _ in pulse["legs"]["defense"])),
             _spark([h for h in pulse["history"]], color=VL["teal"])))
    pc1 = sync.get("pc1_share")
    disp = sync.get("dispersion_20d")
    ddc = sync["drawdown_sync"]
    tiles.append("""
<div class="kpi">
  <div class="klabel">全球共振 PC1 / 離散度</div>
  <div class="kval">%s <span class="unit">PC1占比</span></div>
  <div class="knote">20d 橫斷面離散度 %s · 60d回撤≥5%%：%d / %d 檔</div>
</div>""" % ("—" if pc1 is None else "%.0f%%" % (pc1 * 100),
             "—" if disp is None else "%.2f%%" % (disp * 100),
             ddc["count"], ddc["total"]))
    return '<div class="kgrid">%s</div>' % "".join(tiles)


def _sec_heatmap(ds):
    tf = ["1d", "5d", "20d", "60d", "120d"]
    head = "".join("<th>%s</th>" % t for t in tf)
    body = []
    for group, rows in ds["heatmap"].items():
        body.append('<tr class="grp"><td colspan="%d">%s</td></tr>'
                    % (len(tf) + 1, esc(group)))
        for r in rows:
            cells = []
            for t in tf:
                v = r["ret"].get(t)
                cells.append('<td class="num" style="background:%s" '
                             'data-tip="%s %s %s">%s</td>'
                             % (_heat(v, HEAT_CAP[t]), esc(r["ticker"]), t,
                                fmt_pct(v), fmt_pct(v, 1)))
            body.append('<tr><td><b>%s</b> <span class="sub">%s</span></td>%s</tr>'
                        % (esc(r["ticker"]), esc(r["name"]), "".join(cells)))
    return """
<div class="card">
  <h2>全球熱力圖 · ETF 報酬（對數）</h2>
  <div class="twrap"><table class="heat"><thead>
  <tr><th>ETF</th>%s</tr></thead><tbody>%s</tbody></table></div>
</div>""" % (head, "".join(body))


def _rrg_svg(rot):
    W, H, pad = 480, 430, 34
    cx, cy = W / 2, (H - 20) / 2 + 10
    sc_x = (W / 2 - pad) / 3.0
    sc_y = ((H - 20) / 2 - pad + 10) / 3.0

    def X(v):
        return cx + max(-2.75, min(2.75, v)) * sc_x

    def Y(v):
        return cy - max(-2.75, min(2.75, v)) * sc_y

    s = ['<svg viewBox="0 0 %d %d" style="width:100%%;max-width:480px" '
         'role="img" aria-label="RRG rotation quadrant">' % (W, H)]
    tint = {"Q1": (cx, 10), "Q2": (pad, 10), "Q3": (pad, cy), "Q4": (cx, cy)}
    for q, (x, y) in tint.items():
        s.append('<rect x="%.0f" y="%.0f" width="%.0f" height="%.0f" fill="%s" '
                 'opacity="0.05"/>' % (x, y, W / 2 - pad, cy - 10 if y == 10 else cy - pad,
                                       QUAD[q]))
    s.append('<line x1="%.0f" y1="10" x2="%.0f" y2="%.0f" stroke="%s"/>'
             % (cx, cx, H - 24, VL["bd"]))
    s.append('<line x1="%d" y1="%.0f" x2="%.0f" y2="%.0f" stroke="%s"/>'
             % (pad, cy, W - pad, cy, VL["bd"]))
    labs = {"Q1": (W - pad - 4, 22, "end", "領先 LEADING"),
            "Q2": (pad + 4, 22, "start", "改善 IMPROVING ★"),
            "Q3": (pad + 4, H - 30, "start", "落後 LAGGING"),
            "Q4": (W - pad - 4, H - 30, "end", "轉弱 WEAKENING ⚠")}
    for q, (x, y, anc, name) in labs.items():
        s.append('<text x="%.0f" y="%.0f" text-anchor="%s" class="mono" '
                 'font-size="10" font-weight="700" fill="%s">%s</text>'
                 % (x, y, anc, QUAD[q], esc(name)))
    s.append('<text x="%.0f" y="%d" text-anchor="middle" font-size="9" fill="%s" '
             'class="mono">RS 水位 z →</text>' % (cx, H - 8, VL["sub"]))
    s.append('<text x="12" y="%.0f" text-anchor="middle" font-size="9" fill="%s" '
             'class="mono" transform="rotate(-90 12 %.0f)">RS 動能 →</text>'
             % (cy, VL["sub"], cy))
    for r in rot["rows"]:
        if r["rs_z"] is None or r["velocity"] is None:
            continue
        col = QUAD.get(r["quadrant"], VL["sub"])
        if len(r["trail"]) >= 2:
            path = "M " + " L ".join("%.1f,%.1f" % (X(a), Y(b)) for a, b in r["trail"])
            s.append('<path d="%s" fill="none" stroke="%s" stroke-width="1" '
                     'opacity="0.22"/>' % (path, col))
        x, y = X(r["rs_z"]), Y(r["velocity"])
        s.append('<circle cx="%.1f" cy="%.1f" r="4.5" fill="%s" data-tip="%s %s · '
                 'rs %.2f / vel %.2f"/>' % (x, y, col, esc(r["ticker"]),
                                            esc(r["name"]), r["rs_z"], r["velocity"]))
        s.append('<text x="%.1f" y="%.1f" font-size="9" font-weight="600" '
                 'fill="%s">%s</text>' % (x + 6.5, y + 3, VL["ink"], esc(r["ticker"])))
    s.append("</svg>")
    return "".join(s)


def _sec_rotation(rot):
    rows = []
    for r in rot["rows"]:
        q = r["quadrant"] or "—"
        chip = ('<span class="chip" style="background:%s">%s</span>'
                % (QUAD.get(q, VL["sub"]), esc(r["quadrant_label"] or "P")))
        rows.append("<tr><td><b>%s</b> <span class='sub'>%s</span></td><td>%s</td>"
                    "<td class='num'>%s</td><td class='num'>%s</td>"
                    "<td class='num'>%s</td><td class='sub'>%s</td></tr>"
                    % (esc(r["ticker"]), esc(r["name"]), chip,
                       fmt_num(r["rs_z"]), fmt_num(r["velocity"]),
                       fmt_num(r["accel"]), esc(r["action"] or "—")))
    counts = rot["quadrant_counts"]
    cnt = " · ".join("%s %d" % (q, counts.get(q, 0)) for q in ("Q1", "Q2", "Q3", "Q4"))
    return """
<div class="card">
  <h2>區域/風格輪動 RRG <span class="mcfl">%s</span></h2>
  <div class="sub" style="margin-bottom:8px">%s ｜ %s ｜ 順時針 Q3→Q2→Q1→Q4</div>
  <div class="rrgwrap">%s
  <div class="twrap" style="flex:1;min-width:300px"><table>
  <thead><tr><th>ETF</th><th>象限</th><th>RS z</th><th>動能</th><th>加速</th>
  <th>對策</th></tr></thead><tbody>%s</tbody></table></div></div>
</div>""" % (esc(rot["mcfl"]), esc(rot["axes"]["x"] + " × " + rot["axes"]["y"]),
             esc(cnt), _rrg_svg(rot), "".join(rows))


def _sec_rates(ds):
    rows = []
    for r in ds["rates_panel"]:
        val = (fmt_num(r["level"], 3) + "%" if r.get("kind") == "yield"
               else fmt_pct(r["level"], 2) if r.get("kind") == "ret"
               else fmt_num(r["level"], 3))
        chg = r.get("chg20")
        chg_txt = (("%+.0f bp" % (chg * 100)) if r.get("kind") == "yield" and chg is not None
                   else fmt_pct(chg) if chg is not None else "—")
        bar_v = (chg or 0) * (1 if r.get("kind") == "yield" else 1)
        cap = 0.5 if r.get("kind") == "yield" else 0.08
        rows.append('<tr><td>%s <span class="sub">%s</span></td>'
                    '<td class="num">%s</td>'
                    '<td class="num" style="background:%s">%s</td></tr>'
                    % (esc(r["id"]), esc(r["name"]), val,
                       _heat(bar_v, cap), chg_txt))
    return """
<div class="card">
  <h2>美元 / 利率 / Fed 接入面板</h2>
  <div class="twrap"><table><thead><tr><th>指標</th><th>水位</th>
  <th>20日變化</th></tr></thead><tbody>%s</tbody></table></div>
</div>""" % "".join(rows)


def _sec_sync(sync):
    fnames = sync["factor_names"]
    flabels = sync["factor_labels"]
    head = "".join("<th>%s</th>" % esc(flabels[f]) for f in fnames)
    body = []
    m60 = sync["matrix"].get("60", {})
    for tkr, row in m60.items():
        cells = []
        for f in fnames:
            c = row.get(f)
            cells.append('<td class="num" style="background:%s" data-tip="%s×%s 60d corr %s">%s</td>'
                         % (_heat(c, 1.0, pos=VL["blue"], neg=VL["am"]),
                            esc(tkr), esc(flabels[f]), fmt_num(c),
                            "—" if c is None else "%.2f" % c))
        body.append("<tr><td><b>%s</b></td>%s</tr>" % (esc(tkr), "".join(cells)))
    ll = []
    for r in sync["lead_lag"]:
        ll.append("<tr><td>%s → %s</td><td class='num'>%s</td>"
                  "<td class='num'>%s</td><td class='sub'>%s</td></tr>"
                  % (esc(r["leader"]), esc(r["follower"]),
                     "—" if r["best_lag"] is None else r["best_lag"],
                     fmt_num(r["best_corr"]), esc(r["reading_zh"])))
    dd = sync["drawdown_sync"]
    dd_txt = ("、".join("%s(−%.1f%%)" % (h["ticker"], h["drawdown"] * 100)
                        for h in dd["hits"][:8]) or "無")
    return """
<div class="card">
  <h2>同步矩陣 · ETF × 因子（60d 相關）<span class="mcfl">%s</span></h2>
  <div class="sub" style="margin-bottom:6px">藍=正相關 · 琥珀=負相關（與漲跌色系分離）</div>
  <div class="twrap"><table class="heat"><thead><tr><th>ETF</th>%s</tr></thead>
  <tbody>%s</tbody></table></div>
  <h2 style="margin-top:14px">領先滯後（120d 窗）</h2>
  <div class="twrap"><table><thead><tr><th>配對</th><th>最佳lag</th><th>corr</th>
  <th>判讀</th></tr></thead><tbody>%s</tbody></table></div>
  <div class="knote" style="margin-top:8px">回撤同步：60d 高點回落≥%.0f%% → %d / %d 檔（%s）</div>
</div>""" % (esc(sync["mcfl"]), head, "".join(body), "".join(ll),
             dd["trigger"] * 100, dd["count"], dd["total"], esc(dd_txt))


def _sec_fragility(frag, regional):
    rows = []
    for r in frag:
        b = r["band"]
        flag = ' <span class="chip" style="background:%s">⚠ 雙弱</span>' % STATUS["critical"] \
            if r["double_weak"] else ""
        d = r["detail"]

        def dv(f):
            return d.get(f, {}).get("value", "—")
        rows.append("<tr><td><b>%s</b> <span class='sub'>%s</span>%s</td>"
                    "<td class='num'>%s</td><td>%s</td>"
                    "<td class='num'>%s</td><td class='num'>%s</td>"
                    "<td class='num'>%s</td><td class='num'>%s</td>"
                    "<td class='num' style='background:%s'>%s</td></tr>"
                    % (esc(r["name_zh"]), esc(r["etf"] or ""), flag,
                       fmt_num(r["composite"], 0), _chip(b["label_zh"], b["status"]),
                       dv("debt_gdp"), dv("fiscal_balance_gdp"),
                       dv("current_account_gdp"), dv("external_debt_gni"),
                       _heat(r["etf_ret20"], 0.08), fmt_pct(r["etf_ret20"], 1)))
    reg_rows = []
    for r in regional:
        if r.get("status") == "PENDING":
            continue
        reg_rows.append("<tr><td>%s <span class='sub'>%s</span></td>"
                        "<td class='num'>%+.2fpp</td><td class='num'>%s</td>"
                        "<td class='num'>%+.3f</td><td class='sub'>%s</td></tr>"
                        % (esc(r["region"]), esc(r["fx_etf"]), r["spread_pp"],
                           fmt_pct(r["fx_ret20"], 2), r["potential"],
                           esc(r["reading_zh"])))
    return """
<div class="card">
  <h2>國家財政/外部脆弱度（跨國百分位合成）</h2>
  <div class="sub" style="margin-bottom:6px">欄位：債務/GDP · 財政餘額 · 經常帳 · 外債/GNI（demo 值，NeedsVerify）</div>
  <div class="twrap"><table><thead><tr><th>國家</th><th>脆弱度</th><th>分級</th>
  <th>債務</th><th>財政</th><th>經常帳</th><th>外債</th><th>ETF 20d</th></tr></thead>
  <tbody>%s</tbody></table></div>
  <h2 style="margin-top:14px">區域利差×匯率勢能 <span class="mcfl">MCFL-M20-C26-F230</span></h2>
  <div class="twrap"><table><thead><tr><th>區域</th><th>利差</th><th>FX 20d</th>
  <th>勢能</th><th>判讀</th></tr></thead><tbody>%s</tbody></table></div>
</div>""" % ("".join(rows), "".join(reg_rows))


def _sec_earnings(led):
    rows = []
    for r in led["active"]:
        st = r["staleness"]
        devils = "".join('<span class="devil">%s</span>' % esc(d["flag"])
                         for d in r["devil_warnings"])
        rows.append("<tr><td><b>%s</b> <span class='sub'>%s</span></td>"
                    "<td class='sub'>%s<br>%s</td><td>%s</td>"
                    "<td class='num'>%s</td><td class='num'>%s → %s</td>"
                    "<td class='num'>%s</td><td class='num'>%s</td>"
                    "<td class='num'>%s</td><td>%s</td></tr>"
                    % (esc(r["index_name"]), esc(r["source_name"]),
                       esc(r["source_publish_date"]),
                       "%d 天前" % r["stale_days"],
                       _chip(st["state"], st["status"]),
                       fmt_num(r["implied_forward_eps"]),
                       fmt_num(r["published_forward_pe"]),
                       fmt_num(r["daily_repriced_pe"]),
                       fmt_num(r["earnings_yield_pct"]),
                       fmt_num(r["erp_pp"]), fmt_num(r["usd_adj_erp_pp"]),
                       devils))
    return """
<div class="card">
  <h2>Forward Earnings / 估值（隱含共識 EPS 結轉）<span class="mcfl">%s</span></h2>
  <div class="sub" style="margin-bottom:6px">EPS=發布日倒算後凍結（Calculated_NotOriginal）；每日只重算 P/E / EY / ERP。USD-adj ERP = ERP − FX貶值風險 − 美元資金壓力。</div>
  <div class="twrap"><table><thead><tr><th>指數</th><th>發布</th><th>新鮮度</th>
  <th>隱含EPS</th><th>P/E 發布→重算</th><th>EY%%</th><th>ERP</th>
  <th>USD-adj</th><th>惡魔旗標</th></tr></thead><tbody>%s</tbody></table></div>
</div>""" % (esc(led["mcfl"]), "".join(rows))


def _sec_devil(devil_rows):
    rows = "".join("<tr><td>%s</td><td><b>%s</b></td><td class='sub'>%s</td></tr>"
                   % (_chip(d["severity_zh"], d["severity"]), esc(d["flag"]),
                      esc(d["detail"])) for d in devil_rows)
    return """
<div class="card">
  <h2>惡魔驗證面板 · Devil Validation</h2>
  <div class="twrap"><table><thead><tr><th>等級</th><th>旗標</th><th>內容</th></tr>
  </thead><tbody>%s</tbody></table></div>
</div>""" % rows


def render_dashboard(ds):
    """[MCFL-M40-C41-F402] 單檔自足 HTML。"""
    body = "".join([
        _sec_header(ds),
        _sec_regime(ds["regime"]),
        _sec_kpis(ds["scores"], ds["pulse"], ds["sync"]),
        _sec_heatmap(ds),
        _sec_rotation(ds["rotation"]),
        _sec_rates(ds),
        _sec_sync(ds["sync"]),
        _sec_fragility(ds["fragility"], ds["regional_potential"]),
        _sec_earnings(ds["earnings"]),
        _sec_devil(ds["devil_panel"]),
    ])
    return """<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>VIA Global Market Radar</title>
<style>
:root{--bg:%(bg)s;--sf:%(paper)s;--bd:%(bd)s;--ink:%(ink)s;--sub:%(sub)s}
*{box-sizing:border-box}
body{margin:0;padding:22px;background:var(--bg);color:var(--ink);
font-family:"Noto Sans TC","Microsoft JhengHei","PingFang TC",system-ui,sans-serif;
font-size:13px;line-height:1.5}
.wrap{max-width:1180px;margin:0 auto}
.mono,.num{font-family:"DM Mono",ui-monospace,Consolas,monospace;
font-variant-numeric:tabular-nums}
.eyebrow{font-family:"DM Mono",ui-monospace,Consolas,monospace;font-size:11px;
letter-spacing:2px;text-transform:uppercase;color:var(--sub)}
h1{font-size:22px;font-weight:800;margin:6px 0 4px;letter-spacing:.01em;
text-wrap:balance}
h2{font-size:13.5px;font-weight:700;margin:0 0 8px}
.seal{display:inline-flex;width:30px;height:30px;align-items:center;
justify-content:center;border-radius:7px;background:%(seal)s;color:#fff;
font-weight:900;margin-right:8px;vertical-align:middle}
.strip{height:6px;border-radius:2px;margin:12px 0;
background:linear-gradient(90deg,%(blue)s,%(teal)s,%(am)s,%(up)s)}
.synth{background:#f8ead8;border:1px solid %(am)s;border-radius:6px;
padding:9px 12px;margin:10px 0;font-weight:600}
.card{background:var(--sf);border:1px solid var(--bd);border-radius:8px;
padding:14px;margin:10px 0}
.grid2{display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));
gap:10px}.grid2 .card{margin:0}
.kgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));
gap:10px;margin:10px 0}
.kpi{background:var(--sf);border:1px solid var(--bd);border-radius:8px;
padding:10px 12px}
.klabel{font-size:10px;color:var(--sub);text-transform:uppercase;
letter-spacing:1px;margin-bottom:4px}
.kval{font-size:22px;font-weight:700;font-family:"DM Mono",ui-monospace,monospace}
.kval .unit{font-size:10px;color:var(--sub);font-weight:400}
.knote{font-size:10px;color:var(--sub);margin-top:3px}
.kspark{margin-top:6px}
.mcfl{font-family:"DM Mono",monospace;font-size:9px;color:var(--sub);
font-weight:400;letter-spacing:.5px}
.chip{display:inline-block;color:#fff;padding:1px 8px;border-radius:3px;
font-family:"DM Mono",monospace;font-size:10px;font-weight:700;
vertical-align:middle}
.meter{height:6px;background:#e9e7e1;border-radius:3px;overflow:hidden;
margin-top:8px}.meter .fill{height:100%%;border-radius:3px}
.regime .regime-top{font-size:19px;font-weight:800;margin:2px 0 10px}
.regime .conf{font-family:"DM Mono",monospace;font-size:12px;color:%(blue)s;
margin-left:8px}
.rrow{display:flex;align-items:center;gap:8px;margin:3px 0}
.rname{width:170px;font-size:11px;color:var(--sub)}
.rname.strong{color:var(--ink);font-weight:700}
.rtrack{flex:1;height:8px;background:#efede8;border-radius:3px;overflow:hidden}
.rfill{height:100%%}
.rval{width:44px;text-align:right;font-family:"DM Mono",monospace;font-size:11px}
table{width:100%%;border-collapse:collapse;font-size:12px}
th,td{padding:4px 7px;border-bottom:1px solid #eeece7;text-align:left;
vertical-align:top}
th{font-size:9.5px;color:var(--sub);text-transform:uppercase;letter-spacing:.5px}
td.num{text-align:right}
tr.grp td{background:#efede8;font-weight:700;font-size:10.5px;
letter-spacing:1px;color:var(--sub)}
.twrap{overflow-x:auto}
.sub{color:var(--sub);font-size:11px}
.rrgwrap{display:flex;gap:14px;flex-wrap:wrap;align-items:flex-start}
.devil{display:inline-block;background:#f3e9e7;color:%(seal)s;border:1px solid
%(up)s;border-radius:3px;padding:0 5px;font-family:"DM Mono",monospace;
font-size:9px;margin:1px 2px}
.foot{color:var(--sub);font-size:10px;margin-top:16px;line-height:1.7}
#tip{position:fixed;pointer-events:none;background:%(ink)s;color:#fff;
padding:4px 8px;border-radius:4px;font-size:11px;font-family:"DM Mono",monospace;
opacity:0;transition:opacity .08s;z-index:9;max-width:280px}
@media (prefers-reduced-motion:reduce){#tip{transition:none}}
a{color:%(blue)s}
</style></head><body><div class="wrap">
%(body)s
<div class="foot">
Engine %(engine)s %(ver)s · config %(cfg_hash)s · %(policy)s<br>
真值階梯：本引擎輸出為 T3 價量估算層（demo 模式=T4 SYNTHETIC）；T1 真流請接
MDL008 VIA_GlobalETFFlow。所有分數 z 基準為各 component 自身 T-1 歷史（反循環）。<br>
Visual Lock：紅漲綠跌；相關性藍(+)/琥珀(−)；狀態 chip 恆帶文字，色彩不單獨承載意義。
</div>
</div><div id="tip" role="status"></div>
<script>
(function(){var tip=document.getElementById('tip');
document.addEventListener('mouseover',function(e){
var t=e.target.closest('[data-tip]');
if(t){tip.textContent=t.getAttribute('data-tip');tip.style.opacity=1;}
else{tip.style.opacity=0;}});
document.addEventListener('mousemove',function(e){
tip.style.left=Math.min(window.innerWidth-290,e.clientX+12)+'px';
tip.style.top=(e.clientY+14)+'px';});})();
</script></body></html>""" % {
        "bg": VL["bg"], "paper": VL["paper"], "bd": VL["bd"], "ink": VL["ink"],
        "sub": VL["sub"], "blue": VL["blue"], "teal": VL["teal"], "am": VL["am"],
        "up": VL["up"], "seal": VL["seal"], "body": body,
        "engine": esc(ds["engine_id"]), "ver": esc(ds["engine_version"]),
        "cfg_hash": esc(ds["config_hash"][:12]),
        "policy": "read-only source · append-only runs · UTF-8 no BOM",
    }


# --------------------------------------------------------------------------- #
# 輸出
# --------------------------------------------------------------------------- #

def write_json(path, obj):
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(obj, fh, ensure_ascii=False, indent=2)
        fh.write("\n")


def write_outputs(ds, out_root):
    """[MCFL-M40-C41-F401] append-only run 目錄 + run_ledger.jsonl。"""
    out_root = Path(out_root)
    run_dir = out_root / ds["run_id"]
    run_dir.mkdir(parents=True, exist_ok=True)

    write_json(run_dir / "scores.json",
               {"scores": ds["scores"], "pulse": ds["pulse"],
                "regional_potential": ds["regional_potential"],
                "provenance": ds["provenance"]})
    write_json(run_dir / "regime.json", ds["regime"])
    write_json(run_dir / "rotation.json", ds["rotation"])
    write_json(run_dir / "sync.json", ds["sync"])
    write_json(run_dir / "fragility.json", ds["fragility"])
    write_json(run_dir / "forward_earnings_ledger.json", ds["earnings"])
    write_json(run_dir / "run_summary.json", ds["summary"])

    html = render_dashboard(ds)
    html_path = run_dir / "dashboard.html"
    with open(html_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(html)

    ledger_path = out_root / "run_ledger.jsonl"
    with open(ledger_path, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(ds["summary"], ensure_ascii=False) + "\n")
    return run_dir, html_path


def config_hash(config_path):
    with open(config_path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def make_run_id(prefix="RUN", suffix="VIA_GLOBAL_ETF_RISK"):
    stamp = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    return "%s_%s_%s" % (prefix, stamp, suffix)
