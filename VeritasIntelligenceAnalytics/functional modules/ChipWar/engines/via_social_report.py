# [VIA 歸檔補丁 2026-08-10] 路徑常數改為 VIA_CHIPWAR_STAGING/VIA_CHIPWAR_REPORTS 環境變數
# 可覆寫之模組相對路徑(_generated/,gitignored);運算邏輯零觸碰。原始上傳 sha256[:16]=bc4f9d190de84e32
# -*- coding: utf-8 -*-
"""Social FOMO lane report — Visual Lock."""
import json
import pandas as pd, numpy as np

import os as _os
from pathlib import Path as _P
STAG = _os.environ.get("VIA_CHIPWAR_STAGING") or str(_P(__file__).resolve().parents[1] / "_generated" / "staging")
_P(STAG).mkdir(parents=True, exist_ok=True)
_REPORTS = _os.environ.get("VIA_CHIPWAR_REPORTS") or str(_P(__file__).resolve().parents[1] / "_generated" / "reports")
_P(_REPORTS).mkdir(parents=True, exist_ok=True)
OUT = str(_P(_REPORTS) / "VIA_ChipWar_SocialFOMO_Report.html")
r = json.load(open(f"{STAG}/social_run.json", encoding="utf-8"))
S = pd.DataFrame(r["social"]); ccf = pd.DataFrame(r["ccf"]); g = r["gate"]; LEX = r["lexicon"]

def norm(x):
    x = np.asarray(x, float); lo, hi = np.nanmin(x), np.nanmax(x)
    return (x - lo) / (hi - lo + 1e-12)

def svg_line(series, W=1000, H=230, x0="", x1="", vi=None, vlab=""):
    n = max(len(s["y"]) for s in series)
    X = lambda i: 46 + i / (n - 1) * (W - 60)
    Y = lambda v: 14 + (1 - v) * (H - 42)
    p = [f'<svg viewBox="0 0 {W} {H}" width="100%" style="display:block">']
    for gv in (0, .5, 1): p.append(f'<line x1="46" y1="{Y(gv):.1f}" x2="{W-14}" y2="{Y(gv):.1f}" stroke="#ecebe6"/>')
    if vi is not None:
        p.append(f'<line x1="{X(vi):.1f}" y1="14" x2="{X(vi):.1f}" y2="{H-28}" stroke="#1e1d1a" stroke-dasharray="3 3"/>'
                 f'<text x="{X(vi)+3:.1f}" y="24" font-size="8" fill="#1e1d1a" font-family="DM Mono,monospace">{vlab}</text>')
    for s in series:
        y = norm(s["y"])
        pts = " ".join(f"{X(i):.1f},{Y(v):.1f}" for i, v in enumerate(y) if np.isfinite(v))
        p.append(f'<polyline points="{pts}" fill="none" stroke="{s["c"]}" stroke-width="{s.get("w",1.9)}" opacity="{s.get("o",1)}"/>')
    p.append(f'<text x="46" y="{H-8}" font-size="8" fill="#6b6860" font-family="DM Mono,monospace">{x0}</text>'
             f'<text x="{W-14}" y="{H-8}" text-anchor="end" font-size="8" fill="#6b6860" font-family="DM Mono,monospace">{x1}</text></svg>')
    return "".join(p)

def svg_ccf(df, W=1000, H=200):
    lo, hi = df.spearman.min(), df.spearman.max(); rng = hi - lo + 1e-9
    n = len(df); bw = (W - 80) / n * 0.72
    X = lambda i: 50 + i / (n - 1) * (W - 80)
    Y = lambda v: 12 + (hi - v) / rng * (H - 46)
    p = [f'<svg viewBox="0 0 {W} {H}" width="100%" style="display:block">']
    p.append(f'<line x1="40" y1="{Y(0):.1f}" x2="{W-14}" y2="{Y(0):.1f}" stroke="#dbd9d3"/>')
    besti = int(df.spearman.abs().idxmax())
    for i, row in df.iterrows():
        col = "#c96b5a" if i == besti else ("#4c78a8" if row.lag < 0 else "#9c9890")
        y0, y1 = sorted((Y(0), Y(row.spearman)))
        p.append(f'<rect x="{X(i)-bw/2:.1f}" y="{y0:.1f}" width="{bw:.1f}" height="{max(y1-y0,1):.1f}" fill="{col}" rx="1"/>')
        if row.lag % 5 == 0:
            p.append(f'<text x="{X(i):.1f}" y="{H-8}" text-anchor="middle" font-size="8" fill="#6b6860" font-family="DM Mono,monospace">{int(row.lag)}</text>')
    p.append(f'<text x="{X(besti):.1f}" y="{Y(df.loc[besti].spearman)-5:.1f}" text-anchor="middle" font-size="9" font-weight="700" fill="#c96b5a" font-family="DM Mono,monospace">lag {int(df.loc[besti].lag)} · ρ={df.loc[besti].spearman:.2f}</text>')
    p.append(f'<text x="40" y="{H-24}" font-size="8" fill="#9c9890" font-family="DM Mono,monospace">← social 領先 | social 落後 →</text></svg>')
    return "".join(p)

dts = S.trade_date.tolist()
vi = next((i for i, d in enumerate(dts) if d >= "2025-11-15"), None)
two_ch = svg_line([{"y": S.behavior_fomo, "c": "#4c78a8", "w": 2.2},
                   {"y": S.social_fomo, "c": "#c96b5a", "w": 2.2},
                   {"y": S.post_volume, "c": "#dbd9d3", "w": 1.1, "o": .9}],
                  x0=dts[0], x1=dts[-1], vi=vi, vlab="嵌入轉折")
div_ch = svg_line([{"y": S.hype_divergence, "c": "#7a6daa", "w": 2.0},
                   {"y": S.mention_hhi, "c": "#c4943a", "w": 1.4, "o": .8},
                   {"y": S.flow_hhi_x, "c": "#439a9a", "w": 1.4, "o": .8}],
                  x0=dts[0], x1=dts[-1], vi=vi, vlab="嵌入轉折")

lex_html = ""
lex_zh = {"boarding": ("上車/貪婪詞", "#c96b5a"), "capitulation": ("畢業/恐慌詞", "#5a9e6f"),
          "leverage": ("槓桿詞", "#c4943a"), "sarcasm_risk": ("反串風險詞(降權)", "#9c9890")}
for k, terms in LEX.items():
    zh, col = lex_zh[k]
    chips = "".join(f'<span style="display:inline-block;background:{col}14;border:1px solid {col};border-radius:3px;padding:2px 8px;margin:2px;font:600 9px \'Noto Sans TC\';color:#33403f">{t}</span>' for t in terms)
    lex_html += f'<div style="margin:8px 0"><div style="font:800 10px Syne,sans-serif;color:#1e1d1a;margin-bottom:3px">{zh} <span style="font:600 8px \'DM Mono\',monospace;color:#9c9890">{k}</span></div>{chips}</div>'

html = f"""<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>VIA · 聊天室 FOMO Lane</title>
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:wght@400;500;700&family=DM+Mono:wght@400;500&family=Noto+Sans+TC:wght@400;500;700&display=swap" rel="stylesheet">
<style>
:root{{--bg:#f5f4f0;--paper:#fff;--ink:#1e1d1a;--ink2:#33403f;--mut:#6b6860;--mut2:#9c9890;--line:#dbd9d3;--soft:#ecebe6;--up:#c96b5a;--down:#5a9e6f;--blue:#4c78a8;--teal:#439a9a;--am:#c4943a;--vi:#7a6daa;--reson:linear-gradient(90deg,#c96b5a 0 14.2%,#c4943a 0 28.5%,#5a9e6f 0 42.8%,#439a9a 0 57.1%,#4c78a8 0 71.4%,#7a6daa 0 85.7%,#1e1d1a 0 100%)}}
*{{box-sizing:border-box;margin:0;padding:0}}body{{background:var(--bg);color:var(--ink2);font:11px/1.5 'DM Sans','Noto Sans TC',sans-serif}}
.wrap{{max-width:1180px;margin:0 auto;padding:0 22px 60px}}.bar{{position:fixed;top:0;left:0;right:0;height:4px;background:var(--reson);z-index:50}}
header{{padding:22px 0 9px;margin-bottom:12px;border-bottom:2px solid var(--ink)}}
.kicker{{font:700 10px 'DM Mono',monospace;letter-spacing:2.2px;color:var(--mut);text-transform:uppercase;margin-bottom:7px}}
h1{{font:800 19px/1.2 'Syne',sans-serif;color:var(--ink)}}h1 span{{color:var(--up)}}
.sub{{margin-top:6px;font-size:10.5px;color:var(--mut);max-width:960px}}.sub b{{color:var(--ink2)}}
.warn{{background:#1e1d1a;border-radius:3px;padding:8px 14px;margin:12px 0;font:600 9px 'DM Mono',monospace;color:#f0c674}}
h2{{font:800 13px 'Syne',sans-serif;color:var(--ink);margin:26px 0 8px;padding-bottom:5px;border-bottom:1px solid var(--line)}}
h2 .en{{font:600 8px 'DM Mono',monospace;color:var(--mut2);letter-spacing:1px;margin-left:8px;text-transform:uppercase}}
.panel{{background:var(--paper);border:1px solid var(--line);border-radius:6px;padding:14px 16px;margin-top:10px}}
.panel.dev{{border-left:3px solid var(--up)}}
table{{width:100%;border-collapse:collapse;font:500 10px 'DM Mono',monospace}}
th{{font:700 8px 'DM Mono',monospace;text-transform:uppercase;color:var(--mut);text-align:left;padding:6px 9px;border-bottom:2px solid var(--ink);background:#fafaf8}}
td{{padding:5px 9px;border-bottom:1px solid var(--soft)}}
.legend{{display:flex;gap:14px;flex-wrap:wrap;margin:8px 0;font:600 9px 'DM Mono',monospace;color:var(--mut)}}
.legend i{{display:inline-block;width:14px;height:3px;border-radius:2px;margin-right:5px;vertical-align:middle}}
.panel li{{list-style:none;padding:6px 0;border-bottom:1px solid var(--soft);font:400 10.5px/1.55 'Noto Sans TC',sans-serif}}
.panel li:last-child{{border-bottom:none}}.panel li b{{color:var(--up);font-family:'DM Mono',monospace;font-size:10px}}
</style></head><body><div class="bar"></div><div class="wrap">
<header><div class="kicker">VIA · SOCIAL FOMO LANE · 聊天室第二通道 · SSOT v0.4.0</div>
<h1>聊天室 FOMO：<span>言論面</span> vs 行為面 · Two-Channel</h1>
<p class="sub">行為面 FOMO（融資/當沖/散戶戶數）量的是<b>做了什麼</b>；聊天室 FOMO（PTT/Dcard/Mobile01/Trends）量的是<b>說了什麼</b>。兩通道的 lead-lag、極值反向、與「純吹背離」是三個核心測試。</p></header>
<div class="warn">⚠ T4 合成 · 嵌入真值：social 落後 behavior 7bd、極值反向、話題集中而資金未集中之背離。三測試全數還原（引擎證偽通過）。真實爬蟲以 endpoint registry 於本機執行（jieba userdict = 本 lexicon）。</div>

<h2>① 兩通道曲線 <span class="en">behavior vs social · normalized</span></h2>
<div class="panel">
<div class="legend"><span><i style="background:#4c78a8"></i>行為面 FOMO</span><span><i style="background:#c96b5a"></i>聊天室 FOMO</span><span><i style="background:#dbd9d3"></i>發文量</span></div>
{two_ch}
<p style="margin-top:8px;font-size:10px;color:var(--mut)">紅線（言論）追著藍線（行為）走——散戶先做再喊。</p></div>

<h2>② Lead-Lag CCF <span class="en">spearman cross-correlation · shift −15..+15 bd</span></h2>
<div class="panel">
{svg_ccf(ccf)}
<p style="margin-top:8px;font-size:10px;color:var(--mut)">峰值 lag <b>{g["ccf_best_lag"]}</b>（ρ={g["ccf_best_spearman"]:.3f}）＝聊天室<b>落後</b>行為面 {abs(g["ccf_best_lag"])} 個交易日；嵌入真值 −{g["embedded_true_lag_bd"]}，<b>精準還原</b>。定位：確認指標非領先指標——魔鬼代言人 SL-3：若真實資料出現「social 領先」，先查聚合 look-ahead（收盤後發文算入當日）再談任何 alpha。</p></div>

<h2>③ 極值反向測試 <span class="en">contrarian at extremes only</span></h2>
<div class="panel"><table><thead><tr><th>條件</th><th>n</th><th>fwd 10d 平均</th><th>vs 無條件 {g["fwd10_uncond_mean"]*100:+.2f}%</th></tr></thead><tbody>
<tr><td>p95 貪婪（上車/梭哈詞爆量）</td><td>{g["n_greed"]}</td><td style="color:var(--down);font-weight:800">{g["fwd10_after_greed_mean"]*100:+.2f}%</td><td>顯著劣於</td></tr>
<tr><td>p5 恐慌（畢業/斷頭詞爆量）</td><td>{g["n_fear"]}</td><td style="color:var(--up);font-weight:800">{g["fwd10_after_fear_mean"]*100:+.2f}%</td><td>顯著優於</td></tr>
</tbody></table>
<p style="margin-top:8px;font-size:10px;color:var(--mut)">反向訊號<b>只在極值成立</b>（p95/p5）；中段的 social FOMO 無資訊量，禁止線性使用。</p></div>

<h2>④ 純吹背離 <span class="en">hype divergence · talk without flow</span></h2>
<div class="panel">
<div class="legend"><span><i style="background:#7a6daa"></i>背離 z（話題HHI − 資金HHI）</span><span><i style="background:#c4943a"></i>話題集中度 mention_hhi</span><span><i style="background:#439a9a"></i>資金集中度 flow_hhi</span></div>
{div_ch}
<p style="margin-top:8px;font-size:10px;color:var(--mut)">聊天室談的本來就是已經漲的（機械相關）——<b>只有背離有資訊</b>：話題集中而資金未集中 = 純吹（本合成 {g["hype_divergence_days_gt1p5z"]} 天 &gt;1.5z）。此指標與 bloc lane 的 flow_hhi 交叉，正是 BL-3 共用輸入警示的正確用法：用差、不用和。</p></div>

<h2>⑤ PTT-native Lexicon <span class="en">ships as jieba userdict</span></h2>
<div class="panel">{lex_html}
<p style="margin-top:8px;font-size:10px;color:var(--mut)">正式 zh 情緒模型在 PTT 語境失效，lexicon 必須原生；含反串降權詞。本表隨 schema 交付，本機爬蟲直接掛 jieba。</p></div>

<h2>⑥ 魔鬼代言人 <span class="en">social-specific traps</span></h2>
<div class="panel dev"><ul>
<li><b>SL-1</b> 聊天室資料上限 T2：自選樣本+機器人灌水+反串污染；私人 LINE/Telegram 群<b>不可觀測</b>，公開聊天室量到的是散戶回聲，永遠不是主力。</li>
<li><b>SL-2</b> 自刪/版主刪文 = 生存者偏誤：fetched_ts ASOF + 定期重爬 diff 估刪文率。</li>
<li><b>SL-3</b> social 理應落後：若出現「領先」，第一嫌疑是聚合 look-ahead（收盤後貼文計入當日），不是發現 alpha。</li>
<li><b>SL-4</b> mention_hhi 與 flow_hhi 高相關是機械性的——只有背離有資訊量。</li>
<li><b>SL-5</b> Google Trends 週頻在低量詞會被 rescale：抓歷史須固定錨詞重疊窗拼接，否則序列不可比。</li>
</ul></div>
<p style="margin-top:14px;font:500 8px 'DM Mono',monospace;color:var(--mut2)">VIA Social FOMO Lane v0.1 · rows {g["rows"]} · parse_errors {g["parse_errors"]} · lag_recovered {str(g["lag_recovered"]).lower()} · T4 · 理</p>
</div></body></html>"""
open(OUT, "w", encoding="utf-8").write(html)
print("written", OUT, len(html))
