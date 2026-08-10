# -*- coding: utf-8 -*-
"""VDF-FLOW-MONITOR flow_monitor.py — 族群整合監控 + 採用項目專頁(v0100R)。

README v0120:兩分頁 — ①族群整合監控(方向▲▼ + 強度 bar 0-100 + 走勢%% + sparkline
+ 成分檔數)②實際採用項目(FIS 宇宙 70 檔依 T1-T4 / 走勢標的 / 模擬三維節點 / 資料來源)。
"""
import json
from pathlib import Path

from flow_core import bucket_fis, load_json, load_universe
from flow_sim import load_sim
from flow_ui import TOKENS, esc

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OUTP = ROOT / "flow_monitor.html"


def _spark(vals, color, w=110, h=26):
    if not vals:
        return ""
    lo, hi = min(vals), max(vals)
    rng = (hi - lo) or 1.0
    pts = " ".join("%.1f,%.1f" % (i * w / max(1, len(vals) - 1),
                                  h - 2 - (v - lo) / rng * (h - 4))
                   for i, v in enumerate(vals))
    return ('<svg viewBox="0 0 %d %d" style="width:%dpx;height:%dpx">'
            '<polyline points="%s" fill="none" stroke="%s" stroke-width="1"/></svg>'
            % (w, h, w, h, pts, color))


def build_monitor(rows, write=True):
    uni = load_universe()
    sim = load_sim()
    perf = load_json(ROOT / "config" / "perf.json", {}) or {}
    by_d = {}
    for r in rows or []:
        by_d.setdefault(r["date"], []).append(r)
    dates = sorted(by_d)
    groups = {}
    for d in dates[-22:]:
        cf = bucket_fis(by_d[d], lambda r, u: u.get("asset_class"), universe=uni)
        for k, v in cf.items():
            groups.setdefault(k, []).append(v)
    t = TOKENS
    h = ['<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">'
         '<meta name="viewport" content="width=device-width,initial-scale=1">'
         '<title>VIA FlowSystem · 資金流動監控</title><style>'
         '*{box-sizing:border-box;margin:0;padding:0}'
         'body{background:%(bg)s;color:%(ink2)s;font-family:"Microsoft JhengHei","Segoe UI",sans-serif;font-size:13px;padding:16px}'
         '.wrap{max-width:1100px;margin:0 auto}'
         '.kick{font:700 10px "DM Mono",Consolas,monospace;letter-spacing:.14em;text-transform:uppercase;color:%(teal)s}'
         'h1{font-size:clamp(15px,2vw,18px);color:%(ink)s;margin-bottom:8px}'
         '.card{background:%(paper)s;border:1px solid %(line)s;border-radius:8px;padding:12px 14px;margin-bottom:12px}'
         '.tabs{display:flex;gap:6px;margin-bottom:10px}'
         '.tabs button{font-family:inherit;font-size:12px;border:1px solid %(line)s;background:%(paper)s;border-radius:6px;padding:6px 14px;cursor:pointer}'
         '.tabs button.on{background:%(ink)s;color:#fff;border-color:%(ink)s}'
         '.page{display:none}.page.on{display:block}'
         'table{width:100%%;border-collapse:collapse;font-size:12px}'
         'th{font:700 9.5px "DM Mono",Consolas,monospace;text-transform:uppercase;color:%(mut2)s;text-align:left;border-bottom:1px solid %(line)s;padding:5px 8px}'
         'td{border-bottom:1px solid %(line2)s;padding:5px 8px;vertical-align:middle}'
         '.bar{height:8px;border-radius:4px;background:%(line2)s;overflow:hidden;min-width:90px}'
         '.bar i{display:block;height:100%%}'
         '.hint{font-size:10.5px;color:%(mut)s}.mono{font-family:Consolas,monospace}'
         '.scroll{overflow-x:auto}'
         '</style></head><body><div class="wrap">' % t]
    h.append('<div class="kick">VIA FlowSystem v2(v0100R)</div>')
    h.append('<h1>資金流動監控 — 族群整合 × 採用項目</h1>')
    h.append('<div class="tabs"><button class="on" data-p="m1">族群整合監控</button>'
             '<button data-p="m2">實際採用項目</button></div>')
    # 分頁 1
    h.append('<div class="page on" id="m1"><div class="card scroll">'
             '<h3 style="font-size:13px;margin-bottom:8px">方向 · 強度 · 走勢 整合為一</h3>'
             '<table><thead><tr><th>族群</th><th>方向</th><th>強度</th><th></th><th>近月走勢</th><th>成分</th></tr></thead><tbody>')
    zh = {"cash": "現金", "gold": "黃金", "bond": "債券", "equity": "股票",
          "crypto": "加密", "commodity": "大宗商品", "fx": "外匯", "vol": "波動率"}
    members = {}
    for tk, u in uni.items():
        members[u.get("asset_class", "?")] = members.get(u.get("asset_class", "?"), 0) + 1
    for g, vals in sorted(groups.items(), key=lambda kv: -abs(kv[1][-1] if kv[1] else 0)):
        last = vals[-1] if vals else 0
        mom = (vals[-1] - vals[0]) if len(vals) > 1 else 0
        color = t["up"] if last > 0 else t["down"]
        h.append('<tr><td><b>%s</b> <span class="hint">%s</span></td>'
                 '<td style="color:%s">%s</td>'
                 '<td class="mono">%s</td>'
                 '<td><div class="bar"><i style="width:%.0f%%;background:%s"></i></div></td>'
                 '<td>%s</td><td class="mono">%d</td></tr>' %
                 (esc(zh.get(g, g)), esc(g), color, "流入▲" if last > 0 else "流出▼",
                  round(50 + last / 2, 0), min(100, 50 + last / 2), color,
                  _spark(vals, color), members.get(g, 0)))
    h.append('</tbody></table><div class="hint">強度 = 50+FIS/2(0-100)· 走勢=近月 FIS 軌跡 · 資料=系統當前 panel</div></div></div>')
    # 分頁 2
    h.append('<div class="page" id="m2">')
    h.append('<div class="card scroll"><h3 style="font-size:13px">① FIS 資金流 ETF 宇宙(70 檔依 T1–T4)</h3>'
             '<table><thead><tr><th>層</th><th>檔數</th><th>成員</th></tr></thead><tbody>')
    tiers = {}
    for tk, u in uni.items():
        tiers.setdefault("T%d" % u.get("risk_tier", 3), []).append(tk)
    for tname in ("T1", "T2", "T3", "T4"):
        m = sorted(tiers.get(tname, []))
        h.append('<tr><td><b>%s</b></td><td class="mono">%d</td><td class="mono hint">%s</td></tr>'
                 % (tname, len(m), " ".join(m)))
    h.append('</tbody></table></div>')
    h.append('<div class="card scroll"><h3 style="font-size:13px">② 正規化走勢採用標的</h3>'
             '<table><thead><tr><th>分類</th><th>標的</th></tr></thead><tbody>')
    gz = {"index": "指數", "theme_us": "美股主題ETF", "gics": "GICS產業", "theme_tw": "台股主題個股"}
    for g, items in (perf.get("groups") or {}).items():
        h.append('<tr><td><b>%s</b></td><td class="hint">%s</td></tr>' %
                 (esc(gz.get(g, g)), esc("、".join("%s(%s)" % (i["n"], i["t"]) for i in items))))
    h.append('</tbody></table><div class="hint">美股主題=ETF · 台股主題=個股(明確區分)</div></div>')
    h.append('<div class="card"><h3 style="font-size:13px">③ 情境模擬三維節點</h3><div class="hint">'
             '區域 %d · 風險層 %d · 類型 %d(config/sim.json)</div></div>' %
             (len(sim.get("regions", [])), len(sim.get("tiers", [])), len(sim.get("types", []))))
    h.append('<div class="card"><h3 style="font-size:13px">④ 資料來源</h3><div class="hint">'
             'TWSE T86/MI_MARGN · FRED · Yahoo/yfinance bridge(data/input/*.json 側車;'
             '本引擎零爬站只讀本地)· 時效:daily_data 每日 · reference_flows 週/月(真值)</div></div>')
    h.append('</div>')
    h.append("""<script>
document.querySelectorAll('.tabs button').forEach(function(b){
 b.addEventListener('click',function(){
  document.querySelectorAll('.tabs button').forEach(function(x){x.classList.remove('on');});
  document.querySelectorAll('.page').forEach(function(x){x.classList.remove('on');});
  b.classList.add('on');document.getElementById(b.dataset.p).classList.add('on');});});
</script></div></body></html>""")
    page = "".join(h)
    if write:
        OUTP.write_text(page, encoding="utf-8")
    return page
