# -*- coding: utf-8 -*-
"""VDF-FLOW-HUB flow_hub.py — 單一視窗整合 Hub + 理論總覽(v0100R;操作員「介面整合」令)。

「所有跳出來的介面整合 · 用流程圖說明邏輯 · 圖示/邏輯/關聯清楚 · 重整介面」:
  一窗到底:固定左側欄(VRN 側欄規約同族)+ 右側內嵌六視圖(iframe 同資料夾離線);
  啟動器自此只開本頁,不再彈六窗。
  00 理論總覽:①全鏈流程圖(資料→FIS→校準→三層驗證→宏觀→六視圖)②判讀四象限圖
  (FIS × 宏觀分)③三層 SOLID 關係圖 ④引擎五層關聯圖 — 全 SVG 自含零 CDN。
"""
from pathlib import Path

from flow_ui import TOKENS, esc

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OUTP = ROOT / "flow_hub.html"

PAGES = [("theory", "00", "理論總覽", "THEORY", ""),
         ("dash", "01", "儀表板", "DASHBOARD", "index.html"),
         ("world", "02", "世界地圖", "WORLD MAP", "world_flow.html"),
         ("tier", "03", "風險階梯", "RISK LADDER", "tier_flow.html"),
         ("sim", "04", "情境模擬", "SCENARIO SIM", "global_map_sim.html"),
         ("perf", "05", "走勢圖", "PERF TREND", "perf_trend.html"),
         ("mon", "06", "監控台", "MONITOR", "flow_monitor.html")]


def _node(x, y, w, h, icon, zh, en, color, sub=""):
    t = TOKENS
    return ('<g><rect x="%d" y="%d" width="%d" height="%d" rx="7" fill="%s" stroke="%s" stroke-width="1.2"/>'
            '<text x="%d" y="%d" text-anchor="middle" font-size="15">%s</text>'
            '<text x="%d" y="%d" text-anchor="middle" font-size="11.5" font-weight="700" fill="%s">%s</text>'
            '<text x="%d" y="%d" text-anchor="middle" font-size="8" font-family="Consolas" fill="%s">%s</text>'
            '%s</g>'
            % (x, y, w, h, t["paper"], color,
               x + w // 2, y + 20, icon,
               x + w // 2, y + 36, t["ink"], esc(zh),
               x + w // 2, y + 48, t["mut2"], esc(en),
               ('<text x="%d" y="%d" text-anchor="middle" font-size="8.5" fill="%s">%s</text>'
                % (x + w // 2, y + 60, t["mut"], esc(sub))) if sub else ""))


def _arrow(x1, y1, x2, y2, label="", color=None):
    t = TOKENS
    c = color or t["mut2"]
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    lab = ('<text x="%.0f" y="%.0f" text-anchor="middle" font-size="8.5" fill="%s">%s</text>'
           % (mx, my - 5, t["mut"], esc(label))) if label else ""
    return ('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-width="1.4" marker-end="url(#ar)"/>%s'
            % (x1, y1, x2, y2, c, lab))


def svg_main_flow():
    """①全鏈流程圖:資料側車 → FIS 核心 → 校準 → 三層驗證 → 宏觀對照 → 六視圖。"""
    t = TOKENS
    s = ['<svg viewBox="0 0 1080 240" xmlns="http://www.w3.org/2000/svg" '
         'font-family="Microsoft JhengHei,Segoe UI,sans-serif">'
         '<defs><marker id="ar" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto">'
         '<path d="M0 0 L7 3.5 L0 7 Z" fill="%s"/></marker></defs>' % t["mut2"]]
    s.append(_node(10, 60, 140, 70, "📥", "資料側車", "daily/macro/ref", t["blue"], "零爬站只讀本地"))
    s.append(_node(190, 60, 140, 70, "🧮", "FIS 核心", "flow_core", t["teal"], "雙估計器+守衛"))
    s.append(_node(370, 60, 140, 70, "🎯", "校準迴圈", "calibrate", t["amber"], "grid+OOS 反證"))
    s.append(_node(550, 60, 140, 70, "🛡️", "三層驗證", "SOLID gate", t["violet"], "A 測量·B 效力·自測"))
    s.append(_node(730, 60, 140, 70, "🌐", "宏觀對照", "flow_macro", t["up"], "匯率/利率/DXY/經濟"))
    s.append(_node(910, 60, 160, 70, "🖥️", "六視圖 Hub", "one window", t["ink"], "本頁側欄切換"))
    s.append(_arrow(150, 95, 188, 95, "panel"))
    s.append(_arrow(330, 95, 368, 95, "FIS rows"))
    s.append(_arrow(510, 95, 548, 95, "gates"))
    s.append(_arrow(690, 95, 728, 95, "verdict"))
    s.append(_arrow(870, 95, 908, 95, "判讀"))
    s.append('<text x="540" y="170" text-anchor="middle" font-size="10" fill="%s">'
             '每站誠實 OK/FAIL:沒訊號報沒訊號(alpha=0 必 NOT_VALID 已實證)· 真值未接=UNCALIBRATED 明標 · 判讀=規則非預測</text>' % t["mut"])
    s.append('<text x="540" y="190" text-anchor="middle" font-size="10" fill="%s">'
             '資料流向:側車 JSON → 引擎計算 → data/output/*.json 側產物 → 六視圖只讀呈現(可隨時重生)</text>' % t["mut2"])
    s.append('</svg>')
    return "".join(s)


def svg_quadrant():
    """②判讀四象限:X=宏觀分 Y=FIS — 各象限圖示+行動。"""
    t = TOKENS
    s = ['<svg viewBox="0 0 560 330" xmlns="http://www.w3.org/2000/svg" '
         'font-family="Microsoft JhengHei,Segoe UI,sans-serif">']
    x0, y0, w, h = 70, 30, 430, 240
    for (qx, qy, bg, icon, zh, act) in [
        (x0 + w // 2, y0, "#eef4ee", "✅", "順風流入", "宏觀支撐 · 可留意"),
        (x0, y0, "#fdf3ef", "⚠️", "背離:流入無支撐", "慎追 · 等宏觀跟上"),
        (x0, y0 + h // 2, "#f0f6f0", "🌱", "背離:流出但宏觀轉佳", "關注轉折 · 逆向名單"),
        (x0 + w // 2, y0 + h // 2, "#f2f2f4", "🍂", "順風流出", "宏觀同向 · 迴避"),
    ]:
        s.append('<rect x="%d" y="%d" width="%d" height="%d" fill="%s" stroke="%s"/>'
                 % (qx, qy, w // 2, h // 2, bg, t["line"]))
        s.append('<text x="%d" y="%d" text-anchor="middle" font-size="17">%s</text>'
                 % (qx + w // 4, qy + 42, icon))
        s.append('<text x="%d" y="%d" text-anchor="middle" font-size="11.5" font-weight="700" fill="%s">%s</text>'
                 % (qx + w // 4, qy + 64, t["ink"], esc(zh)))
        s.append('<text x="%d" y="%d" text-anchor="middle" font-size="9.5" fill="%s">%s</text>'
                 % (qx + w // 4, qy + 80, t["mut"], esc(act)))
    s.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-width="1.5"/>' % (x0, y0 + h // 2, x0 + w, y0 + h // 2, t["ink2"]))
    s.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-width="1.5"/>' % (x0 + w // 2, y0, x0 + w // 2, y0 + h, t["ink2"]))
    s.append('<text x="%d" y="%d" text-anchor="middle" font-size="10" font-weight="700" fill="%s">FIS 流入 ↑</text>' % (x0 - 34, y0 + 40, t["up"]))
    s.append('<text x="%d" y="%d" text-anchor="middle" font-size="10" font-weight="700" fill="%s">FIS 流出 ↓</text>' % (x0 - 34, y0 + h - 30, t["down"]))
    s.append('<text x="%d" y="%d" text-anchor="middle" font-size="10" font-weight="700" fill="%s">宏觀分 −  ←</text>' % (x0 + 70, y0 + h + 22, t["down"]))
    s.append('<text x="%d" y="%d" text-anchor="middle" font-size="10" font-weight="700" fill="%s">→  宏觀分 +(本幣強/利差正/經濟佳/美元順風)</text>' % (x0 + w - 130, y0 + h + 22, t["up"]))
    s.append('</svg>')
    return "".join(s)


def svg_solid():
    """③三層驗證 AND 關係圖。"""
    t = TOKENS
    s = ['<svg viewBox="0 0 560 200" xmlns="http://www.w3.org/2000/svg" '
         'font-family="Microsoft JhengHei,Segoe UI,sans-serif">'
         '<defs><marker id="ar2" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto">'
         '<path d="M0 0 L7 3.5 L0 7 Z" fill="%s"/></marker></defs>' % t["mut2"]]
    s.append(_node(10, 10, 150, 54, "📏", "Pillar A 測量", "流量是真的嗎", t["blue"], "真值缺=UNCALIBRATED"))
    s.append(_node(10, 74, 150, 54, "🔮", "Pillar B 效力", "能預測未來嗎", t["amber"], "G002-G011+OOS"))
    s.append(_node(10, 138, 150, 54, "🧪", "self-test", "邊界穩嗎", t["teal"], "14 項"))
    s.append('<rect x="240" y="70" width="90" height="60" rx="7" fill="%s" stroke="%s"/>'
             '<text x="285" y="96" text-anchor="middle" font-size="13" font-weight="700" fill="%s">AND</text>'
             '<text x="285" y="112" text-anchor="middle" font-size="8.5" fill="%s">任一紅=紅</text>'
             % (t["paper2"], t["ink2"], t["ink"], t["mut"]))
    for y in (37, 101, 165):
        s.append('<line x1="162" y1="%d" x2="238" y2="100" stroke="%s" stroke-width="1.4" marker-end="url(#ar2)"/>' % (y, t["mut2"]))
    s.append(_node(400, 70, 150, 60, "🏛️", "SYSTEM SOLID", "全綠才立", t["down"], "紅=NOT_SOLID 明標"))
    s.append('<line x1="332" y1="100" x2="398" y2="100" stroke="%s" stroke-width="1.4" marker-end="url(#ar2)"/>' % t["mut2"])
    s.append('</svg>')
    return "".join(s)


def svg_engine_layers():
    """④引擎五層關聯圖(18 支)。"""
    t = TOKENS
    layers = [
        ("資料層", t["blue"], ["bridge 側車入口", "roles 閘門/分類"]),
        ("核心層", t["teal"], ["core FIS", "validate 閘", "calibrate 校準", "factors 因子", "macro 宏觀"]),
        ("驗證層", t["amber"], ["selftest 14", "autotest 17", "pillar_a 真值"]),
        ("呈現層", t["violet"], ["ui 儀表板", "grid 網格", "worldmap 地圖", "sim 模擬", "perf 走勢", "monitor 監控", "hub 一窗"]),
        ("編排", t["ink"], ["manager 18 動詞"]),
    ]
    s = ['<svg viewBox="0 0 1080 300" xmlns="http://www.w3.org/2000/svg" '
         'font-family="Microsoft JhengHei,Segoe UI,sans-serif">'
         '<defs><marker id="ar3" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto">'
         '<path d="M0 0 L7 3.5 L0 7 Z" fill="%s"/></marker></defs>' % t["mut2"]]
    y = 10
    for name, color, mods in layers:
        s.append('<rect x="10" y="%d" width="92" height="40" rx="6" fill="%s" opacity="0.9"/>'
                 '<text x="56" y="%d" text-anchor="middle" font-size="11" font-weight="700" fill="#fff">%s</text>'
                 % (y, color, y + 25, esc(name)))
        x = 120
        for m in mods:
            wd = 24 + len(m) * 10
            s.append('<rect x="%d" y="%d" width="%d" height="40" rx="6" fill="%s" stroke="%s"/>'
                     '<text x="%d" y="%d" text-anchor="middle" font-size="10" font-family="Consolas" fill="%s">%s</text>'
                     % (x, y, wd, t["paper"], color, x + wd // 2, y + 25, t["ink2"], esc(m)))
            x += wd + 10
        if y > 10:
            s.append('<line x1="56" y1="%d" x2="56" y2="%d" stroke="%s" stroke-width="1.2" marker-end="url(#ar3)"/>' % (y - 16, y - 2, t["mut2"]))
        y += 58
    s.append('<text x="540" y="296" text-anchor="middle" font-size="9.5" fill="%s">'
             '關聯:資料層供料 → 核心層計算 → 驗證層把關 → 呈現層只讀呈現;manager 統一編排(all/live 一鍵全鏈);flow_ui.TOKENS=六視圖共用視覺鎖單一事實源</text>' % t["mut"])
    s.append('</svg>')
    return "".join(s)


def build_hub(write=True):
    t = TOKENS
    nav = []
    for pid, num, zh, en, _f in PAGES:
        nav.append('<button class="nv%s" data-p="%s"><span class="n">%s</span>'
                   '<span>%s<span class="en">%s</span></span></button>'
                   % (" on" if pid == "theory" else "", pid, num, esc(zh), esc(en)))
    frames = []
    for pid, _num, zh, _en, f in PAGES:
        if pid == "theory":
            continue
        frames.append('<div class="pg" id="pg-%s"><iframe data-src="%s" title="%s"></iframe></div>'
                      % (pid, esc(f), esc(zh)))
    theory = """
<div class="pg on" id="pg-theory"><div class="tin">
<div class="card"><h3>① 全鏈流程 — 資料怎麼變成判讀</h3>%s</div>
<div class="row">
<div class="card"><h3>② 判讀四象限 — FIS × 宏觀分(圖示=行動)</h3>%s</div>
<div class="card"><h3>③ 三層驗證 — SOLID 怎麼立</h3>%s
<h3 style="margin-top:14px">核心公式(理論整合)</h3>
<ul>
<li><b>FIS</b> = 100·tanh(流量 z / κ):流量=Δ股數×價(申贖代理),雙估計器(AUM 路徑)互驗抓假象;分割守衛/新生排除/權重上限三硬化</li>
<li><b>GRAM</b> = 100·tanh(((T3+T4)−(T1+T2))/2/κ):風險偏好動能,雙形並陳(標準化+原始 net$/pool)</li>
<li><b>宏觀分</b> = 0.30·本幣動能 + 0.25·利差(區−美) + 0.30·經濟(PMI−50) − 0.15·美元逆風</li>
<li><b>評價 V</b> =(預期報酬 − λ·風險)/ 估值成本:成本隨累積流入上升(反身性 — 錢湧入變貴)</li>
</ul></div>
</div>
<div class="card"><h3>④ 引擎關聯 — 誰餵誰 · 誰把關誰</h3>%s</div>
</div></div>""" % (svg_main_flow(), svg_quadrant(), svg_solid(), svg_engine_layers())
    page = """<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>VIA FlowSystem · 整合 Hub(一窗到底)</title><style>
*{box-sizing:border-box;margin:0;padding:0}
html,body{height:100%%}
body{background:%(bg)s;color:%(ink2)s;font-family:"Microsoft JhengHei","Segoe UI",system-ui,sans-serif;font-size:13px;display:flex;overflow:hidden}
.sb{flex:none;width:210px;height:100vh;background:%(paper)s;border-right:1px solid %(line)s;display:flex;flex-direction:column}
.brand{padding:16px 14px 10px;border-bottom:1px solid %(line2)s}
.brand .k{font:700 9.5px "DM Mono",Consolas,monospace;letter-spacing:.13em;text-transform:uppercase;color:%(mut2)s}
.brand h2{font-size:15px;color:%(ink)s;margin-top:3px}
.brand p{font:600 9.5px "DM Mono",Consolas,monospace;color:%(teal)s;margin-top:4px}
.nav{flex:1;overflow-y:auto;padding:8px}
.nav button{display:flex;align-items:center;gap:9px;width:100%%;text-align:left;border:1px solid transparent;background:none;
border-radius:6px;padding:8px 9px;font-family:inherit;font-size:12px;color:%(ink2)s;cursor:pointer;margin-bottom:2px}
.nav button:hover{background:%(paper2)s;border-color:%(line2)s}
.nav button.on{background:%(ink)s;color:#fff}
.nav .n{font:700 9.5px "DM Mono",Consolas,monospace;color:%(mut2)s;width:18px;flex:none}
.nav button.on .n{color:#fff;opacity:.7}
.nav .en{display:block;font-size:9px;opacity:.6}
.foot{border-top:1px solid %(line2)s;padding:9px 14px;font-size:9.5px;color:%(mut)s}
.main{flex:1;height:100vh;overflow:hidden;position:relative}
.pg{display:none;height:100%%}
.pg.on{display:block}
.pg iframe{width:100%%;height:100%%;border:0;background:%(bg)s}
.tin{height:100%%;overflow-y:auto;padding:16px 20px}
.card{background:%(paper)s;border:1px solid %(line)s;border-radius:8px;padding:13px 16px;margin-bottom:13px;
box-shadow:0 1px 2px rgba(27,26,23,.04)}
.card h3{font-size:13px;color:%(ink)s;margin-bottom:8px}
.row{display:flex;gap:13px;flex-wrap:wrap}
.row>.card{flex:1;min-width:330px}
svg{width:100%%;height:auto;display:block}
ul{padding-left:18px;font-size:11.5px;line-height:1.75}
@media (max-width:760px){.sb{width:150px}}
</style></head><body>
<aside class="sb">
<div class="brand"><div class="k">Veritas Intelligence Analytics</div>
<h2>FlowSystem 整合 Hub</h2><p>ONE WINDOW · v0100R</p></div>
<div class="nav">%(nav)s</div>
<div class="foot">一窗到底 · 零 CDN 離線 · 理論=規則非預測 · 誠實紅</div>
</aside>
<div class="main">
%(theory)s
%(frames)s
</div>
<script>
document.querySelectorAll('.nav button').forEach(function(b){
 b.addEventListener('click',function(){
  document.querySelectorAll('.nav button').forEach(function(x){x.classList.remove('on');});
  document.querySelectorAll('.pg').forEach(function(x){x.classList.remove('on');});
  b.classList.add('on');
  var pg=document.getElementById('pg-'+b.dataset.p);pg.classList.add('on');
  var f=pg.querySelector('iframe');
  if(f&&!f.src)f.src=f.dataset.src; /* 懶載:點到才載,啟動秒開 */
 });});
</script></body></html>""" % dict(t, nav="".join(nav), theory=theory, frames="".join(frames))
    if write:
        OUTP.write_text(page, encoding="utf-8")
    return page
