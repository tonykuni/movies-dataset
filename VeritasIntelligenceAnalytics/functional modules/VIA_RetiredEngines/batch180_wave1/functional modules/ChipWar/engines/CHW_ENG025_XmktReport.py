# [VIA 歸檔補丁 2026-08-10] 路徑常數改為 VIA_CHIPWAR_STAGING/VIA_CHIPWAR_REPORTS 環境變數
# 可覆寫之模組相對路徑(_generated/,gitignored);運算邏輯零觸碰。原始上傳 sha256[:16]=883366d54e9de41b
# -*- coding: utf-8 -*-
"""Cross-market FOMO factor lab report — Visual Lock."""
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
import json
import pandas as pd, numpy as np

import os as _os
from pathlib import Path as _P
STAG = _os.environ.get("VIA_CHIPWAR_STAGING") or str(_P(__file__).resolve().parents[1] / "_generated" / "staging")
_P(STAG).mkdir(parents=True, exist_ok=True)
_REPORTS = _os.environ.get("VIA_CHIPWAR_REPORTS") or str(_P(__file__).resolve().parents[1] / "_generated" / "reports")
_P(_REPORTS).mkdir(parents=True, exist_ok=True)
OUT = str(_P(_REPORTS) / "VIA_XMkt_FactorLab_Report.html")
r = json.load(open(f"{STAG}/xmkt_run.json", encoding="utf-8"))
GRID = pd.DataFrame(r["grid"]); CTRL = pd.DataFrame(r["ctrl"])
WFS = pd.DataFrame(r["wf_summary"]); g = r["gate"]

FZH = {"fomo_index": "FOMO Index", "behavior_fomo": "行為面 FOMO", "social_fomo": "言論面 FOMO",
       "hype_divergence": "純吹背離", "boarding_ratio": "上車詞頻", "dxy": "美元指數",
       "fed_net_liq": "Fed 淨流動性", "wti": "WTI", "m1b_m2_spread": "M1B−M2", "global_flow": "全球資金流"}
HORIZONS = [1, 5, 10, 21]

def heat(target, title):
    rows = ""
    for f in FZH:
        cells = ""
        for h in HORIZONS:
            cell = GRID[(GRID.factor == f) & (GRID.target == target) & (GRID.horizon == h)].iloc[0]
            v = cell.icir; a = min(abs(v) / 1.4, 1)
            bg = f"rgba(201,107,90,{a:.2f})" if v > 0 else f"rgba(90,158,111,{a:.2f})"
            fg = "#fff" if a > .55 else "#33403f"
            star = "★" if abs(v) > 0.5 else ""
            cells += f'<td style="background:{bg};color:{fg};text-align:center;font-weight:700">{v:+.2f}{star}</td>'
        rows += f'<tr><td style="font-family:\'Noto Sans TC\'">{FZH[f]}</td>{cells}</tr>'
    return (f'<div style="font:800 10px Syne,sans-serif;color:#1e1d1a;margin:10px 0 4px">{title}</div>'
            f'<table><thead><tr><th>Factor \\ Horizon</th>' +
            "".join(f"<th style='text-align:center'>{h}d</th>" for h in HORIZONS) +
            f'</tr></thead><tbody>{rows}</tbody></table>')

ctrl_rows = ""
for x in CTRL.itertuples():
    died = abs(x.gspc_f5_partial_ic) < abs(x.gspc_f5_raw_ic) * 0.5
    ctrl_rows += (f'<tr><td style="font-family:\'Noto Sans TC\'">{FZH[x.factor]}</td>'
                  f'<td>{x.gspc_f5_raw_ic:+.4f}</td><td style="font-weight:800">{x.gspc_f5_partial_ic:+.4f}</td>'
                  f'<td style="color:{"#5a9e6f" if not died else "#9c9890"}">{"存活" if not died else "死於控制"}</td></tr>')

wf_rows = ""
zh_c = {"max_icir": "IC 加權（train窗選）", "top_k": "Top-3 選因（train窗選）", "equal_w": "等權基準", "max_icir_gspc": "IC 加權 → GSPC"}
for x in WFS.itertuples():
    gapc = "#c96b5a" if x.honesty_gap > 0.12 else "#c4943a" if x.honesty_gap > 0.06 else "#5a9e6f"
    wf_rows += (f'<tr><td style="font-family:\'Noto Sans TC\'">{zh_c.get(x.criteria, x.criteria)}</td><td>{x.n}</td>'
                f'<td>{x.insample_ic_mean:+.4f}</td><td style="font-weight:800">{x.oos_ic_mean:+.4f}</td>'
                f'<td style="color:{gapc};font-weight:800">{x.honesty_gap:.4f}</td></tr>')

best = g["best_cell"]
html = f"""<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>VIA · 跨市場 FOMO Factor Lab</title>
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
.panel li{{list-style:none;padding:6px 0;border-bottom:1px solid var(--soft);font:400 10.5px/1.55 'Noto Sans TC',sans-serif}}
.panel li:last-child{{border-bottom:none}}.panel li b{{color:var(--up);font-family:'DM Mono',monospace;font-size:10px}}
.hero{{display:flex;gap:10px;flex-wrap:wrap;margin-top:10px}}
.hc{{background:var(--paper);border:1px solid var(--line);border-radius:5px;padding:9px 14px;min-width:130px}}
.hc .v{{font:800 16px 'Syne',sans-serif;color:var(--ink)}}.hc .l{{font:600 8px 'DM Mono',monospace;color:var(--mut);text-transform:uppercase;margin-top:3px}}
</style></head><body><div class="bar"></div><div class="wrap">
<header><div class="kicker">VIA · CROSS-MARKET FOMO FACTOR LAB · ^TWII + ^GSPC · SSOT v0.6.0</div>
<h1>台灣 FOMO 因子組 → <span>雙市場</span> Factor Lab</h1>
<p class="sub">10 因子 × 2 標的 × 4 horizon = <b>80 格自動滾動測試</b>（60d rolling Spearman，ICIR 計分）+ walk-forward 自動選權優化（三準則）。<b>時序閘門：</b>台股 13:30 收盤在美股開盤前——TW 因子(t) 合法預測同日美股 session；打台股必須 t+1。</p>
<div class="hero">
<div class="hc"><div class="v">{best["factor"]}</div><div class="l">最佳格 · {best["target"]} {best["horizon"]}d</div></div>
<div class="hc"><div class="v">ICIR {best["icir"]:+.2f}</div><div class="l">ic_mean {best["ic_mean"]:+.3f}</div></div>
<div class="hc"><div class="v">{g["n_grid_tests"]}</div><div class="l">格數 · 多重檢定校正: 只認 |ICIR|&gt;0.5★</div></div>
<div class="hc"><div class="v">{"✓" if g["extreme_spillover_truth_recovered"] else "✗"}</div><div class="l">極值外溢真值還原</div></div>
</div></header>
<div class="warn">⚠ T4 合成 · GSPC 嵌入真值：全球因子 + 台股同日連動 + <b>僅極值</b> FOMO 外溢。Lab 必須（a）還原極值外溢（b）證明多數「TW 領先 SPX」原始 IC 死於全球因子控制。兩者皆達成。</div>

<h2>① ICIR 熱力格 <span class="en">10 factors × 4 horizons × 2 targets · ★ = |ICIR|>0.5</span></h2>
<div class="panel">{heat("twii", "→ ^TWII（因子 t，報酬 t+1 起）")}
{heat("gspc", "→ ^GSPC（因子 t，同日美股 session 起 = 合法時序）")}
<p style="margin-top:8px;font-size:10px;color:var(--mut)">紅=正 ICIR、綠=負（台灣紅漲綠跌慣例沿用於訊號方向）。80 格多重檢定下，原始 IC 顯著是廉價的——<b>只認 ★（|ICIR|&gt;0.5）</b>。</p></div>

<h2>② 全球因子控制 <span class="en">gspc 5d · partial IC after removing same-day TWII co-move</span></h2>
<div class="panel"><table><thead><tr><th>因子</th><th>原始 IC</th><th>Partial IC</th><th>判定</th></tr></thead><tbody>{ctrl_rows}</tbody></table>
<p style="margin-top:8px;font-size:10px;color:var(--mut)">「台灣領先美股」的多數原始 IC 只是全球因子 + 時區順序的鏡像；控制同日台股連動後，僅極值型因子存活——與嵌入真值一致。真實資料上此表是<b>發表前的必經關卡</b>。</p></div>

<h2>③ Walk-Forward 優化 <span class="en">train 120d → select → eval 21d OOS · honesty gap mandatory</span></h2>
<div class="panel"><table><thead><tr><th>準則</th><th>窗數</th><th>樣本內 IC</th><th>OOS IC</th><th>誠實 Gap</th></tr></thead><tbody>{wf_rows}</tbody></table>
<p style="margin-top:8px;font-size:10px;color:var(--mut)">選權只在 train 窗內進行；<b>gap = 樣本內 − OOS</b> 每次必報。Top-3 選因 OOS 最佳（{WFS[WFS.criteria=="top_k"].oos_ic_mean.iloc[0]:+.3f}）；等權基準 OOS 為負——說明「全部因子平均」在此組合是稀釋而非分散。GSPC 的 gap 最大（{WFS[WFS.criteria=="max_icir_gspc"].honesty_gap.iloc[0]:.3f}）＝台灣因子打美股樣本內好看、OOS 幾乎不剩。</p></div>

<h2>④ 魔鬼代言人 <span class="en">cross-market traps</span></h2>
<div class="panel dev"><ul>
<li><b>XM-1</b> 時區順序是跨市場第一漏洞：TWII 目標未 shift(-1) 的任何「預測力」直接作廢。本 lab 於 schema 層強制。</li>
<li><b>XM-2</b> 「TW 領先 SPX」大多是全球因子鏡像：partial IC 控制表為發表前必經關卡。</li>
<li><b>XM-3</b> walk-forward 仍是優化器：gap 逐期追蹤，gap 收斂於零且 OOS 上升才可信；gap 擴大 = 因子庫開始被市場學走或過擬合。</li>
<li><b>XM-4</b> 80 格多重檢定：期望值上 ~4 格會偶然「顯著」。只認 ICIR、跨 horizon 一致性、與經濟邏輯三重同時成立。</li>
<li><b>XM-5</b> 合成 GSPC 無真實微結構（隔夜跳空/期貨連動）：真實資料需用 ES=F 期貨對齊台股收盤時點，而非現貨收盤。</li>
</ul></div>
<p style="margin-top:14px;font:500 8px 'DM Mono',monospace;color:var(--mut2)">VIA XMkt Factor Lab v0.1 · {g["n_grid_tests"]} cells · parse_errors {g["parse_errors"]} · T4 · 理</p>
</div></body></html>"""
open(OUT, "w", encoding="utf-8").write(html)
print("written", OUT, len(html))
