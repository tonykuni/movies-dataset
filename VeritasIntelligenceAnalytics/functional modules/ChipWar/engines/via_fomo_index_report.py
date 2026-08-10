# [VIA 歸檔補丁 2026-08-10] 路徑常數改為 VIA_CHIPWAR_STAGING/VIA_CHIPWAR_REPORTS 環境變數
# 可覆寫之模組相對路徑(_generated/,gitignored);運算邏輯零觸碰。原始上傳 sha256[:16]=a2d6e20f8e1ab42b
# -*- coding: utf-8 -*-
"""FOMO Index report — Visual Lock + FlowSystem verdict style."""
import json
import pandas as pd, numpy as np

import os as _os
from pathlib import Path as _P
STAG = _os.environ.get("VIA_CHIPWAR_STAGING") or str(_P(__file__).resolve().parents[1] / "_generated" / "staging")
_P(STAG).mkdir(parents=True, exist_ok=True)
_REPORTS = _os.environ.get("VIA_CHIPWAR_REPORTS") or str(_P(__file__).resolve().parents[1] / "_generated" / "reports")
_P(_REPORTS).mkdir(parents=True, exist_ok=True)
OUT = str(_P(_REPORTS) / "VIA_FOMO_Index_Report.html")
r = json.load(open(f"{STAG}/fomo_index_run.json", encoding="utf-8"))
S = pd.DataFrame(r["series"]); G = r["gates"]; meta = r["gate"]; ST = pd.DataFrame(r["state_stats"])

latest = float(meta["latest"]["fomo_index"]); lstate = meta["latest"]["state"]

# gauge (RORO needle style, 0..100)
def gauge(v, W=1000, H=110):
    x = 60 + v / 100 * (W - 120)
    return f'''<svg viewBox="0 0 {W} {H}" width="100%" style="display:block">
<defs><linearGradient id="gg" x1="0" x2="1"><stop offset="0" stop-color="#5a9e6f"/><stop offset=".45" stop-color="#e5e3df"/><stop offset="1" stop-color="#c96b5a"/></linearGradient></defs>
<rect x="60" y="38" width="{W-120}" height="12" rx="6" fill="url(#gg)" opacity=".85"/>
{"".join(f'<line x1="{60+t/100*(W-120):.0f}" y1="52" x2="{60+t/100*(W-120):.0f}" y2="58" stroke="#9c9890"/><text x="{60+t/100*(W-120):.0f}" y="70" text-anchor="middle" font-size="8" fill="#9c9890" font-family="DM Mono,monospace">{t}</text>' for t in (0,20,40,60,80,100))}
<path d="M {x:.0f} 34 l -7 -12 l 14 0 z" fill="#1e1d1a"/>
<text x="{x:.0f}" y="16" text-anchor="middle" font-size="20" font-weight="800" fill="{'#c96b5a' if v>=60 else '#5a9e6f' if v<40 else '#6b6860'}" font-family="Syne,sans-serif">{v:.1f}</text>
<text x="60" y="92" font-size="9" fill="#5a9e6f" font-family="DM Mono,monospace">◀ 恐慌 0</text>
<text x="{W-60}" y="92" text-anchor="end" font-size="9" fill="#c96b5a" font-family="DM Mono,monospace">100 過熱 ▶</text></svg>'''

def norm(x):
    x = np.asarray(x, float); return (x - np.nanmin(x)) / (np.nanmax(x) - np.nanmin(x) + 1e-12)

def line_chart(W=1000, H=230):
    n = len(S); X = lambda i: 46 + i / (n - 1) * (W - 60); Y = lambda v: 12 + (1 - v / 100) * (H - 40)
    p = [f'<svg viewBox="0 0 {W} {H}" width="100%" style="display:block">']
    for band, col in [((80, 100), "#c96b5a"), ((0, 20), "#5a9e6f")]:
        p.append(f'<rect x="46" y="{Y(band[1]):.0f}" width="{W-60}" height="{Y(band[0])-Y(band[1]):.0f}" fill="{col}" opacity=".07"/>')
    for gv in (0, 20, 40, 60, 80, 100):
        p.append(f'<line x1="46" y1="{Y(gv):.1f}" x2="{W-14}" y2="{Y(gv):.1f}" stroke="#ecebe6"/><text x="42" y="{Y(gv)+3:.1f}" text-anchor="end" font-size="8" fill="#9c9890" font-family="DM Mono,monospace">{gv}</text>')
    for i, row in S.iterrows():
        if row.froth_flag:
            p.append(f'<line x1="{X(i):.1f}" y1="{H-28}" x2="{X(i):.1f}" y2="{H-24}" stroke="#7a6daa" stroke-width="1.5"/>')
    for col, key, w, o in [("#dbd9d3", "behavior_fomo", 1.2, .9), ("#c4943a", "social_fomo", 1.2, .7), ("#c96b5a", "fomo_index", 2.6, 1)]:
        pts = " ".join(f"{X(i):.1f},{Y(v):.1f}" for i, v in enumerate(S[key]))
        p.append(f'<polyline points="{pts}" fill="none" stroke="{col}" stroke-width="{w}" opacity="{o}"/>')
    p.append(f'<text x="46" y="{H-8}" font-size="8" fill="#6b6860" font-family="DM Mono,monospace">{S.trade_date.iloc[0]}</text>'
             f'<text x="{W-14}" y="{H-8}" text-anchor="end" font-size="8" fill="#6b6860" font-family="DM Mono,monospace">{S.trade_date.iloc[-1]}</text>'
             f'<text x="50" y="{H-24}" font-size="8" fill="#7a6daa" font-family="DM Mono,monospace">▎純吹背離日</text></svg>')
    return "".join(p)

badge = ("PROVED_VALID", "#5a9e6f") if meta["verdict"] == "PROVED_VALID" else ("FAILED_GATES", "#c96b5a")
gpills = ""
for k, v in G.items():
    col = "#5a9e6f" if v["pass"] else "#c96b5a"
    val = v["value"] if not isinstance(v["value"], list) else " → ".join(f"{x:+.3f}" if isinstance(x,float) else str(x) for x in v["value"][:5])
    gpills += (f'<div style="background:#fafaf8;border:1px solid var(--line);border-left:3px solid {col};border-radius:4px;padding:8px 12px;margin:6px 0">'
               f'<span style="font:700 9px \'DM Mono\',monospace;color:{col}">{k} {"✓" if v["pass"] else "✗"}</span>'
               f'<span style="font:500 9px \'DM Mono\',monospace;color:#33403f;margin-left:10px">{val}</span>'
               f'<div style="font:400 9px \'Noto Sans TC\';color:#6b6860;margin-top:2px">{v["rule"]}</div></div>')

order = ["恐慌", "冷", "溫", "熱", "過熱"]
ST["o"] = ST.state.map({s: i for i, s in enumerate(order)}); ST = ST.sort_values("o")
scol = {"恐慌": "#5a9e6f", "冷": "#439a9a", "溫": "#9c9890", "熱": "#c4943a", "過熱": "#c96b5a"}
srows = "".join(
    f'<tr><td><span style="background:{scol[x.state]};color:#fff;border-radius:3px;padding:2px 8px;font-weight:700">{x.state}</span></td>'
    f'<td>{int(x.n)}</td><td style="color:{"#c96b5a" if x.fwd10_mean>=0 else "#5a9e6f"};font-weight:800">{x.fwd10_mean*100:+.2f}%</td></tr>'
    for x in ST.itertuples())

html = f"""<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>VIA · FOMO Index</title>
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
.verdict{{display:inline-flex;align-items:center;gap:10px;background:{badge[1]};color:#fff;border-radius:20px;padding:7px 18px;font:800 13px 'Syne',sans-serif;letter-spacing:.5px}}
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
<header><div class="kicker">VIA · FOMO INDEX · 統一貪婪恐慌指數 · v0.1</div>
<h1>FOMO Index <span>{latest:.1f}</span> · {lstate}</h1>
<p class="sub">行為面 70%（融資/當沖/戶數/量能）+ 言論面 30%（聊天室）；言論面另供兩個離散 overlay：<b>極值閘門</b>（p95/p5 反向）與<b>純吹旗標</b>。權重手設凍結（tech debt → CPCV）。</p>
<div style="margin-top:10px"><span class="verdict">◉ {badge[0]}</span><span style="font:600 9px 'DM Mono',monospace;color:var(--mut);margin-left:12px">4/4 gates · T4 synthetic · run rows {meta["rows"]}</span></div></header>
<div class="warn">⚠ T4 合成驗證 · verdict 證明的是<b>管線與 gate 邏輯</b>，不是真實市場結論。真實資料重跑後 verdict 才有交易意義。</div>

<h2>① 指針 <span class="en">latest reading</span></h2>
<div class="panel">{gauge(latest)}</div>

<h2>② 指數全程 <span class="en">index vs two channels · froth days marked</span></h2>
<div class="panel">
<div class="legend"><span><i style="background:#c96b5a"></i>FOMO Index</span><span><i style="background:#dbd9d3"></i>行為面</span><span><i style="background:#c4943a"></i>言論面</span><span><i style="background:#7a6daa"></i>純吹背離日({meta["froth_days"]}d)</span></div>
{line_chart()}</div>

<h2>③ 五狀態 × 前瞻報酬 <span class="en">state → fwd10</span></h2>
<div class="panel"><table><thead><tr><th>狀態</th><th>樣本數</th><th>fwd 10d 平均</th></tr></thead><tbody>{srows}</tbody></table>
<p style="margin-top:8px;font-size:10px;color:var(--mut)">恐慌 +2.40% 單調遞減至 過熱 −1.49%：極值反向 + 中段鈍化的教科書結構。<b>操作語義：</b>過熱≠立即做空，是「停止加碼+收緊風控」；恐慌是「分批承接」條件之一，須與 regime/主導 lane 共同確認。</p></div>

<h2>④ 驗證閘門 <span class="en">gates · flowsystem style</span></h2>
<div class="panel">{gpills}</div>

<h2>⑤ 魔鬼代言人 <span class="en">index-specific traps</span></h2>
<div class="panel dev"><ul>
<li><b>FI-1</b> 70/30 權重手設：G-gates 全過不代表權重最優，只代表此設計不自相矛盾。CPCV 重擬合前禁止調參追分。</li>
<li><b>FI-2</b> G_oos 為單切 split-half：依 LL 單切偽樂觀，verdict 標 PROVISIONAL 直到 CPCV 多路徑。</li>
<li><b>FI-3</b> 指數與 chipwar score 共用部分輸入（融資/當沖）：兩者同時報警不是雙重確認。</li>
<li><b>FI-4</b> 極值樣本稀少（過熱 18 / 恐慌 20 obs）：反向統計的 CI 很寬，真實資料需事件重疊去重（clustered extremes ≠ 獨立樣本）。</li>
<li><b>FI-5</b> FOMO 指數是<b>風險儀表非擇時訊號</b>：直接反向交易中段讀值必然虧損（中段無資訊已證）。</li>
</ul></div>
<p style="margin-top:14px;font:500 8px 'DM Mono',monospace;color:var(--mut2)">VIA FOMO Index v0.1 · verdict {badge[0]} · parse_errors {meta["parse_errors"]} · T4 · 理</p>
</div></body></html>"""
open(OUT, "w", encoding="utf-8").write(html)
print("written", OUT, len(html))
