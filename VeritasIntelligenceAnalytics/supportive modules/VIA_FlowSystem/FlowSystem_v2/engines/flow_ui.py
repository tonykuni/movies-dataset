# -*- coding: utf-8 -*-
"""UI-14 flow_ui.py — 由 JSON 產 Visual Lock index.html(v0100R)。

U/I 對齊:Veritas WorkOps v2 設計鎖 token(Panorama 色階/DM Mono kicker/固定圓角/
via combo 色序)— 與指揮板同語彙;RWD(README v0110);零 CDN 全自含。
"""
import html as _html
import json
from pathlib import Path

from flow_core import snapshot, load_universe, load_params

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OUTP = ROOT / "index.html"

# WorkOps v2 視覺鎖 token(單一事實源,worldmap/sim/perf/monitor 共用)
TOKENS = {"bg": "#f2f1ec", "paper": "#ffffff", "paper2": "#fbfaf7", "ink": "#1b1a17",
          "ink2": "#3a3f3e", "mut": "#6b6860", "mut2": "#9c9890", "line": "#dcdad3",
          "line2": "#ebe9e3", "teal": "#3d8f8f", "up": "#c96b5a", "down": "#5a9e6f",
          "amber": "#bf8f33", "blue": "#4c78a8", "violet": "#7a6daa"}
COMBO = ["#c96b5a", "#c4943a", "#5a9e6f", "#439a9a", "#4c78a8", "#7a6daa"]


def esc(s):
    return _html.escape(str(s), quote=True)


def css_base():
    t = TOKENS
    return """
*{box-sizing:border-box;margin:0;padding:0}
body{background:%(bg)s;color:%(ink2)s;font-family:"Microsoft JhengHei","Segoe UI",system-ui,sans-serif;font-size:13px;line-height:1.6;padding:18px}
.wrap{max-width:1180px;margin:0 auto}
.kick{font:700 10px "DM Mono",Consolas,monospace;letter-spacing:.14em;text-transform:uppercase;color:%(teal)s}
h1{font-size:clamp(16px,2vw,19px);color:%(ink)s}
.sub{font-size:11px;color:%(mut)s;margin:2px 0 12px}
.card{background:%(paper)s;border:1px solid %(line)s;border-radius:8px;padding:14px 16px;margin-bottom:14px;
box-shadow:0 1px 2px rgba(27,26,23,.04),0 8px 24px -12px rgba(27,26,23,.14)}
.card h3{font-size:13.5px;color:%(ink)s;margin-bottom:8px}
.row{display:flex;gap:14px;flex-wrap:wrap}
.row>.card{flex:1;min-width:300px}
table{width:100%%;border-collapse:collapse;font-size:12px}
th{font:700 9.5px "DM Mono",Consolas,monospace;letter-spacing:.07em;text-transform:uppercase;color:%(mut2)s;text-align:left;border-bottom:1px solid %(line)s;padding:5px 8px}
td{border-bottom:1px solid %(line2)s;padding:5px 8px}
.mono{font-family:Consolas,monospace}
.badge{display:inline-block;font:700 10px "DM Mono",Consolas,monospace;border:1px solid %(line)s;border-radius:5px;padding:2px 9px;background:%(paper2)s}
.badge.g{color:#2e7d32;border-color:#a5c9a7}.badge.r{color:#b3402a;border-color:#dcb0a5}.badge.a{color:%(amber)s}
.bar{height:8px;border-radius:4px;background:%(line2)s;overflow:hidden}
.bar i{display:block;height:100%%}
.tabs{display:flex;gap:6px;margin-bottom:12px;overflow-x:auto}
.tabs button{font-family:inherit;font-size:12px;border:1px solid %(line)s;background:%(paper)s;border-radius:6px;padding:6px 14px;cursor:pointer;color:%(ink2)s;white-space:nowrap}
.tabs button.on{background:%(ink)s;color:#fff;border-color:%(ink)s}
.page{display:none}.page.on{display:block}
.hint{font-size:10.5px;color:%(mut)s}
.scroll{overflow-x:auto}
@media (max-width:760px){.row{flex-direction:column}body{padding:10px}}
""" % t


def _fis_color(v):
    return TOKENS["up"] if v > 0 else (TOKENS["down"] if v < 0 else TOKENS["mut2"])


def build_index(rows, calib, status=None, grid=None, factors=None, write=True):
    sn = snapshot(rows) if rows else {"per_ticker": [], "bucket": {}, "asset_class": {},
                                      "roro": 50, "gram_score": 0, "gram_raw": 0,
                                      "regime": "NEUTRAL", "tier_fis": {}, "regime_market": "CALM"}
    uni = load_universe()
    st = status or {}
    layers = st.get("layers", {})
    solid = st.get("solid", "NOT_SOLID")
    h = ['<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">'
         '<meta name="viewport" content="width=device-width,initial-scale=1">'
         '<title>VIA FlowSystem · 全球 ETF 資金流向</title><style>', css_base(), '</style></head><body><div class="wrap">']
    h.append('<div class="kick">Veritas Intelligence Analytics · FlowSystem v2(v0100R)</div>')
    h.append('<h1>全球 ETF 資金流向與強度 — 自我驗證系統</h1>')
    h.append('<div class="sub">region=曝險非來源 · 驗證未過=誠實紅 · 零雲端自含</div>')
    # 三層狀態橫幅
    b = lambda okv: "g" if okv == "OK" else ("a" if okv == "SKIP" else "r")
    h.append('<div class="card"><h3>三層驗證 · SOLID 狀態</h3>')
    h.append('<span class="badge %s">SYSTEM %s</span> ' % ("g" if solid == "SOLID" else "r", esc(solid)))
    for k in ("pillar_a", "pillar_b", "selftest"):
        v = layers.get(k, "SKIP")
        h.append('<span class="badge %s">%s %s</span> ' % (b(v), k.upper(), esc(v)))
    h.append('<div class="hint">%s</div></div>' % esc(st.get("note", "")))
    h.append('<div class="tabs"><button class="on" data-p="f1">Flow &amp; Validation</button>'
             '<button data-p="f2">Region × Sector</button><button data-p="f3">Fidelity</button></div>')
    # --- 分頁 1
    h.append('<div class="page on" id="f1">')
    ver = (calib or {}).get("status", "—")
    h.append('<div class="row"><div class="card"><h3>驗證 Verdict</h3>'
             '<span class="badge %s">%s</span><div class="hint">%s</div></div>' %
             ("g" if ver == "PROVED_VALID" else "r", esc(ver), esc((calib or {}).get("reason", ""))))
    h.append('<div class="card"><h3>RORO 單針</h3><div class="mono" style="font-size:26px;color:%s">%s</div>'
             '<div class="bar"><i style="width:%s%%;background:%s"></i></div>'
             '<div class="hint">GRAM %s · raw %s · %s</div></div></div>' %
             (_fis_color(sn.get("gram_score", 0)), sn.get("roro", 50), sn.get("roro", 50),
              TOKENS["teal"], sn.get("gram_score", 0), sn.get("gram_raw", 0), esc(sn.get("regime", ""))))
    h.append('<div class="card"><h3>Risk-Tier Ladder + GRAM</h3><table><thead><tr><th>層</th><th>FIS</th><th></th></tr></thead><tbody>')
    for tname in ("T4", "T3", "T2", "T1"):
        v = sn.get("tier_fis", {}).get(tname, 0)
        h.append('<tr><td>%s</td><td class="mono" style="color:%s">%s</td>'
                 '<td style="width:55%%"><div class="bar"><i style="width:%.0f%%;background:%s"></i></div></td></tr>'
                 % (tname, _fis_color(v), v, min(100, abs(v)), _fis_color(v)))
    h.append('</tbody></table></div>')
    if factors:
        h.append('<div class="card"><h3>因子庫</h3><table><thead><tr><th>因子</th><th>IC</th><th>狀態</th></tr></thead><tbody>')
        for f in factors.get("kept", []):
            h.append('<tr><td>%s</td><td class="mono">%s</td><td><span class="badge g">KEPT</span></td></tr>' % (esc(f["name"]), f["ic"]))
        for f in factors.get("rejected", []):
            h.append('<tr><td>%s</td><td class="mono">%s</td><td><span class="badge r">REJECTED</span></td></tr>' % (esc(f["name"]), f["ic"]))
        h.append('</tbody></table></div>')
    met = (calib or {}).get("oos") or {}
    if met:
        h.append('<div class="card"><h3>硬化指標</h3><span class="badge">tHAC %s</span> '
                 '<span class="badge">lead %s</span> <span class="badge">IC %s</span> '
                 '<span class="badge">ICIR %s</span></div>' %
                 (met.get("t_hac", "—"), met.get("lead_ratio", "—"), met.get("ic", "—"), met.get("icir", "—")))
    h.append('<div class="card scroll"><h3>Per-ETF(依 |FIS| 排序;confidence D/CONFLICT 不進聚合)</h3>'
             '<table><thead><tr><th>Ticker</th><th>FIS</th><th>z</th><th>Flow $</th><th>Conf</th><th>Tier</th><th>類別</th></tr></thead><tbody>')
    for r in sn["per_ticker"][:40]:
        u = uni.get(r["ticker"], {})
        h.append('<tr><td class="mono"><b>%s</b></td><td class="mono" style="color:%s">%s</td>'
                 '<td class="mono">%s</td><td class="mono">%s</td><td>%s</td><td>T%s</td><td>%s</td></tr>' %
                 (esc(r["ticker"]), _fis_color(r["fis"]), r["fis"], r["flow_z"],
                  ("%.0f" % r["flow_usd"]), esc(r["confidence"]), u.get("risk_tier", "—"),
                  esc(u.get("asset_class", ""))))
    h.append('</tbody></table></div></div>')
    # --- 分頁 2 Region×Sector
    h.append('<div class="page" id="f2"><div class="card scroll"><h3>全球輪動熱圖(US=direct·其餘=proxy)</h3>')
    rs = (grid or {}).get("region_sector") or {}
    if rs:
        secs = rs.get("sectors", [])
        h.append('<table><thead><tr><th>區域</th>%s</tr></thead><tbody>' %
                 "".join('<th>%s</th>' % esc(s) for s in secs))
        for reg in rs.get("rows", []):
            h.append('<tr><td><b>%s</b>%s</td>' % (esc(reg["region"]),
                     "" if reg.get("direct") else ' <span class="hint">proxy</span>'))
            for v in reg["cells"]:
                h.append('<td class="mono" style="background:%s22;color:%s">%s</td>' %
                         (_fis_color(v), _fis_color(v), round(v, 1)))
            h.append('</tr>')
        h.append('</tbody></table><div class="hint">紅=流入 · 綠=流出(台股慣例)· proxy = 區域錨點 × US-sector tilt</div>')
    else:
        h.append('<div class="hint">grid.json 未產 — 先跑 manager grid</div>')
    h.append('</div></div>')
    # --- 分頁 3 Fidelity
    h.append('<div class="page" id="f3"><div class="card scroll"><h3>ETF 流量監控可信度評分卡</h3>')
    fid = (grid or {}).get("fidelity") or []
    if fid:
        h.append('<table><thead><tr><th>類</th><th>中位 fidelity</th><th>backing/role</th><th>live FIS</th><th>建議用法</th></tr></thead><tbody>')
        for f in fid:
            weak = f["median_fidelity"] < 60
            h.append('<tr><td>%s</td><td class="mono">%s%s</td><td>%s</td><td class="mono" style="color:%s">%s</td><td class="hint">%s</td></tr>' %
                     (esc(f["cls"]), f["median_fidelity"],
                      ' <span class="badge r">weak</span>' if weak else "",
                      esc(f["backing_role"]), _fis_color(f.get("live_fis", 0)), f.get("live_fis", "—"),
                      esc(f["advice"])))
        h.append('</tbody></table>')
    else:
        h.append('<div class="hint">grid.json 未產 — 先跑 manager grid</div>')
    h.append('</div></div>')
    h.append('<div class="hint">VIA FlowSystem v2 · 視覺鎖對齊 WorkOps v2 · 誠實驗證(Gate 紅=紅)</div>')
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
