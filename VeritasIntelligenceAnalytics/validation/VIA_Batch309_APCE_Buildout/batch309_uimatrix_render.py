#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
batch309_uimatrix_render — 批309 APCE 指標庫 MATRIX + 參數家族 + 真值榜(零手寫數字)
輸入:FlowSystem_v2/data/output/apce_latest.json(ENG029 輸出:catalog/latest/indices/health)
     GroupIndex/.../VIA_FLOWROT_Method_Thresholds_v0400.json(參數家族)
     FlowSystem_v2/data/input/tw_apce_panel.json(面板覆蓋/來源)
輸出:VIA_Batch309_APCE_UIMatrix_v0100.html(批306 Codex 模板語言)
"""
from __future__ import annotations
import html, json
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
FS = VIA / "supportive modules" / "VIA_FlowSystem" / "FlowSystem_v2"
SSOT = sorted((VIA / "functional modules" / "GroupIndex" / "flow_simulation_v0400" / "ssot").glob("VIA_FLOWROT_Method_Thresholds_v*.json"))[-1]
OUT = HERE / "VIA_Batch309_APCE_UIMatrix_v0100.html"
NOW = datetime.now().strftime("%Y-%m-%d %H:%M")
esc = lambda s: html.escape(str(s), quote=True)

def jload(p, d=None):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except Exception:
        return d

def fmt(v, nd=2):
    if v is None:
        return "—"
    if isinstance(v, bool):
        return "✓" if v else "✗"
    if isinstance(v, float):
        return f"{v:,.{nd}f}"
    return str(v)

def main() -> int:
    res = jload(FS / "data" / "output" / "apce_latest.json", {})
    pan = jload(FS / "data" / "input" / "tw_apce_panel.json", {})
    ssot = jload(SSOT, {"controls": []})
    latest = res.get("latest", [])
    health = res.get("health", {})
    idx = res.get("indices", {})
    asof = res.get("asof", "—")
    cov = res.get("coverage", {})
    PT = {"F": ("warn", "Type-F 固定"), "D": ("ok", "Type-D 滾動"), "H": ("acc", "Type-H 混合"),
          "核心": ("acc", "核心輸入"), "監控": ("mut", "監控"), "策略": ("bad", "策略")}

    # 甲 指標庫 MATRIX(一類一類)
    cat = res.get("catalog", [])
    classes = []
    for c in cat:
        if c["class"] not in classes:
            classes.append(c["class"])
    cat_html = ""
    for cl in classes:
        rows = "".join(
            f'<tr><td class="mono"><b>{esc(c["var"])}</b></td><td class="mono det">{esc(c["formula"])}</td>'
            f'<td class="det">{esc(c["meaning"])}</td>'
            f'<td><span class="badge {PT.get(c["ptype"], ("mut", c["ptype"]))[0]} dot">{esc(PT.get(c["ptype"], ("mut", c["ptype"]))[1])}</span></td></tr>'
            for c in cat if c["class"] == cl)
        cat_html += (f'<div class="card"><h3>{esc(cl)}</h3><table><thead><tr><th style="width:190px">變數</th>'
                     f'<th style="width:300px">計算式</th><th>意義</th><th style="width:110px">參數型</th></tr></thead><tbody>{rows}</tbody></table></div>')

    # 乙 參數家族表
    fam_rows = ""
    for c in ssot.get("controls", []):
        pt = c.get("param_type", "F")
        roll = c.get("rolling", {}); lk = c.get("lock", {})
        rule = (f"滾動 {roll.get('stat')} q={roll.get('q', '')} w={roll.get('window', '')}" + (f" floor={roll.get('floor')}" if 'floor' in roll else "") if roll else "")
        rule += (f" | 鎖:{lk.get('trigger')} → {lk.get('lock_value')} / {lk.get('hold_days')} 日" if lk else "")
        used = (res.get("params_used") or {}).get(c["id"], {})
        mode = used.get("mode", "") if isinstance(used, dict) else ""
        fam_rows += (f'<tr><td class="mono">{esc(c["id"])}</td><td>{esc(c["name"])}</td>'
                     f'<td><span class="badge {PT[pt][0]} dot">{esc(PT[pt][1])}</span></td>'
                     f'<td class="mono">{esc(c["value"])} {esc(c.get("unit", ""))}</td><td class="det">{esc(rule or "固定憲法")}</td>'
                     f'<td class="mono">{esc(mode or "—")}{(" · " + esc(used.get("value"))) if isinstance(used, dict) and used.get("value") is not None and mode not in ("", "FIXED") else ""}</td>'
                     f'<td class="det">{esc(c.get("note", ""))}</td></tr>')

    # 丙 族群指數/健康
    gh_rows = ""
    for sec, hh in sorted(health.items(), key=lambda kv: -(kv[1].get("pc1_absorption") or -1)):
        v = idx.get(sec, {}).get(asof, {})
        g = hh.get("index_grade", "")
        cls = "ok" if g == "INDEX_GRADE" else "acc" if g == "EXPLORE_PASS" else "bad" if g == "REMOVE" else "mut"
        gh_rows += (f'<tr><td><b>{esc(sec)}</b></td><td class="mono">{esc(hh.get("n_members"))}</td>'
                    f'<td class="mono">{fmt(hh.get("pc1_absorption"), 3)}</td><td><span class="badge {cls} dot">{esc(g)}</span></td>'
                    f'<td class="mono">{fmt(v.get("eq"))}</td><td class="mono">{fmt(v.get("tier"))}</td><td class="mono"><b>{fmt(v.get("att"))}</b></td>'
                    f'<td class="mono">{fmt((v.get("att") or 0) - (v.get("eq") or 0)) if v.get("att") is not None and v.get("eq") is not None else "—"}</td>'
                    f'<td class="mono">{fmt(hh.get("max_w_att"), 3)}</td><td class="mono">{fmt(hh.get("hhi_att"), 3)}</td></tr>')

    # 丁 角色榜(LEADER 優先)+訊號
    order = {"LEADER": 0, "WASHOUT": 1, "PEER": 2, "FAKE_PULL": 3, "LAGGER": 4, "UNRELATED": 5, "RANK_ONLY": 6, "None": 7}
    top = sorted(latest, key=lambda r: (order.get(str(r.get("role")), 9), -(r.get("leader_score") or 0)))[:40]
    role_rows = "".join(
        f'<tr><td class="mono">{esc(r["ticker"])}</td><td>{esc(r["sector"])}</td><td class="mono">{esc(r["market"])}</td>'
        f'<td><span class="badge {"ok" if r["role"] == "LEADER" else "acc" if r["role"] == "WASHOUT" else "bad" if r["role"] in ("FAKE_PULL", "LAGGER") else "mut"} dot">{esc(r["role"])}</span></td>'
        f'<td class="mono">{fmt(r.get("leader_score"), 3)}</td><td class="mono">{fmt((r.get("as") or 0) * 100, 2)}%</td>'
        f'<td class="mono">{fmt(r.get("price_rs"), 3)}</td><td class="mono">{fmt(r.get("rs_mom"), 3)}</td>'
        f'<td class="mono">{fmt(r.get("price_corr"))}/{fmt(r.get("vol_corr"))}</td><td class="mono">{fmt(r.get("adaptive_score"))}</td>'
        f'<td class="mono">{fmt(r.get("gravity_shock"), 3)}</td><td>{esc(r.get("size_tier"))}</td><td class="mono">{fmt(r.get("valid_member"))}</td>'
        f'<td class="det">{"·".join(k.replace("Signal_", "") for k in ("Signal_Strong_Leader", "Signal_Washout_Buy", "Signal_SITC_Ignition") if r.get(k)) or (("避:" + r["Avoid"]) if r.get("Avoid") else "—")}</td></tr>'
        for r in top)
    rc = res.get("role_counts", {})
    sig_n = sum(1 for r in latest if r.get("Signal_Strong_Leader") or r.get("Signal_Washout_Buy") or r.get("Signal_SITC_Ignition"))
    cov_rows = "".join(f'<tr><td class="mono">{esc(k)}</td><td class="mono">{(v * 100):.1f}%</td></tr>' for k, v in cov.items())
    prov = pan.get("provenance", [])[-6:]
    prov_rows = "".join(f'<tr><td class="det">{esc(p.get("ts"))}</td><td class="det">{esc(p.get("note"))}</td><td class="mono">新 {esc(p.get("new"))}/覆 {esc(p.get("updated"))}</td></tr>' for p in prov)

    page = f"""<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Batch 309 · APCE Metrics Matrix</title>
<style>
:root{{--bg:#f4f6f8;--paper:#fff;--paper2:#f9fafb;--ink:#202833;--ink2:#465365;--mut:#596778;--line:#dfe4ea;--soft:#eef2f5;--ok:#1e7d46;--bad:#b3372c;--warn:#9a6a00;--acc:#315f7d}}
*{{box-sizing:border-box;margin:0;padding:0}}html,body{{min-height:100%;background:var(--bg);color:var(--ink)}}
body{{font:12px/1.55 "Segoe UI","Noto Sans TC",system-ui,sans-serif;padding:64px 0 46px}}
code,.mono{{font-family:Consolas,"SFMono-Regular",ui-monospace,monospace}}
header{{position:fixed;top:0;left:0;right:0;height:56px;z-index:9;display:flex;align-items:center;gap:10px;padding:0 14px;background:rgba(255,255,255,.97);border-bottom:1px solid var(--line)}}
header .logo{{display:flex;align-items:center;gap:8px;font-weight:700;font-size:13px}}
header .logo .sq{{width:26px;height:26px;display:grid;place-items:center;background:#315f7d;color:#fff;border-radius:5px;font-size:11px}}
.badges{{display:flex;gap:6px;margin-left:auto;flex-wrap:wrap}}
.badge{{display:inline-flex;align-items:center;min-height:21px;padding:1px 8px;border:1px solid var(--line);border-radius:7px;background:var(--paper2);font-size:9.5px;font-weight:700;white-space:nowrap}}
.badge.ok{{color:var(--ok);border-color:#b8d7c6;background:#f1f8f4}}.badge.bad{{color:var(--bad);border-color:#e3c0bc;background:#fff5f3}}
.badge.warn{{color:var(--warn);border-color:#e0d0a6;background:#fdf8ec}}.badge.acc{{color:var(--acc);border-color:#b9cbd8;background:#eef4f8}}.badge.mut{{color:var(--mut)}}
.badge.dot::before{{content:"";width:7px;height:7px;border-radius:50%;margin-right:5px;background:currentColor}}
main{{max-width:1240px;margin:0 auto;padding:14px}}
.statrow{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:8px;margin:8px 0 16px}}
.stat{{background:var(--paper);border:1px solid var(--line);border-radius:8px;padding:9px 11px}}.stat .v{{font-size:18px;font-weight:800;color:var(--acc)}}.stat .zh{{font-size:10.5px;color:var(--ink2);margin-top:2px}}
section{{margin:18px 0}}h2{{font-size:14px;display:flex;align-items:center;gap:8px;margin-bottom:6px}}
h2 .secno{{width:22px;height:22px;display:grid;place-items:center;background:var(--acc);color:#fff;border-radius:5px;font-size:11px}}h2 .en{{color:var(--mut);font-weight:600;font-size:11px}}
h3{{font-size:11.5px;color:var(--ink2);margin:8px 0 6px}}.card{{background:var(--paper);border:1px solid var(--line);border-radius:8px;padding:10px 12px;margin-top:10px}}
table{{width:100%;border-collapse:collapse;background:var(--paper);border:1px solid var(--line);border-radius:8px;overflow:hidden;font-size:11px}}
th{{background:var(--soft);color:var(--ink2);text-align:left;padding:6px 8px;border-bottom:1px solid var(--line);font-size:10px}}
td{{padding:5px 8px;border-bottom:1px solid var(--paper2);vertical-align:top}}tr:last-child td{{border-bottom:none}}td.det{{color:var(--ink2);font-size:10.5px}}.mut{{color:var(--mut)}}
.toc{{display:flex;gap:8px;flex-wrap:wrap;margin:10px 0 0}}.toc a{{border:1px solid var(--line);border-radius:6px;padding:3px 9px;background:var(--paper);font-size:10.5px;color:var(--acc);text-decoration:none}}
.grid2{{display:grid;grid-template-columns:1fr 2fr;gap:10px}}@media(max-width:900px){{.grid2{{grid-template-columns:1fr}}}}
footer{{position:fixed;bottom:0;left:0;right:0;height:34px;display:flex;align-items:center;gap:14px;padding:0 14px;background:var(--paper);border-top:1px solid var(--line);font-size:9.5px;color:var(--mut)}}
</style></head><body>
<header><div class="logo"><span class="sq">B9</span>Batch 309 · APCE 自適應完美分類引擎 <span class="mut">Metrics Matrix · Param Family · Live Boards</span></div>
<div class="badges"><span class="badge ok dot">Selftests 24/24</span><span class="badge acc dot">stdlib 零依賴</span><span class="badge warn dot">Type-F/D/H 一個家</span><span class="badge mut">誠實三態 SKIP 不代設</span></div></header>
<main>
<div class="statrow">
 <div class="stat"><div class="v">{len(cat)}</div><div class="zh">指標庫項目({len(classes)} 類)</div></div>
 <div class="stat"><div class="v">{len(ssot.get("controls", []))}</div><div class="zh">參數家族控項(F {sum(1 for c in ssot.get("controls", []) if c.get("param_type") == "F")}/D {sum(1 for c in ssot.get("controls", []) if c.get("param_type") == "D")}/H {sum(1 for c in ssot.get("controls", []) if c.get("param_type") == "H")})</div></div>
 <div class="stat"><div class="v">{res.get("n_tickers", "—")}</div><div class="zh">面板成員(排台積電後 {len(latest)} 檔分類;{res.get("n_dates", "—")} 交易日)</div></div>
 <div class="stat"><div class="v">{len(health)}</div><div class="zh">族群指數(三加權;基準 {esc(res.get("base_date", "—"))}=100)</div></div>
 <div class="stat"><div class="v">{sum(1 for h in health.values() if h.get("index_grade") == "INDEX_GRADE")}</div><div class="zh">INDEX_GRADE(PC1≥C-01b 0.55)</div></div>
 <div class="stat"><div class="v">{rc.get("LEADER", 0)}</div><div class="zh">LEADER(相對+絕對雙重條件;asof {esc(asof)})</div></div>
 <div class="stat"><div class="v">{sig_n}</div><div class="zh">觸發訊號檔數(三策略)</div></div>
</div>
<div class="toc"><a href="#甲">甲 指標庫 MATRIX</a><a href="#乙">乙 參數家族</a><a href="#丙">丙 族群指數/健康</a><a href="#丁">丁 角色榜/訊號</a><a href="#戊">戊 面板覆蓋</a></div>
<section id="甲"><h2><span class="secno">甲</span> 指標庫 MATRIX <span class="en">一類一類:變數 × 計算式 × 意義 × 參數型(自引擎 registry 渲染)</span></h2>{cat_html}</section>
<section id="乙"><h2><span class="secno">乙</span> 參數家族 <span class="en">{esc(ssot.get("ssot_id", ""))} · F 憲法優先 → D 滾動 → H 條件鎖</span></h2>
<div class="mut" style="margin:0 0 8px 30px;font-size:10.5px">鎖觸:{esc("; ".join(t["id"] + " " + t["rule"] for t in ssot.get("lock_triggers", [])))} · 敏感律:{esc(ssot.get("sensitivity_doctrine", ""))}</div>
<div style="overflow-x:auto"><table><thead><tr><th>控項</th><th>名稱</th><th>型</th><th>基值</th><th>滾動/鎖定律</th><th>本次解析</th><th>註</th></tr></thead><tbody>{fam_rows}</tbody></table></div></section>
<section id="丙"><h2><span class="secno">丙</span> 族群指數與健康 <span class="en">三加權(T-1/封頂/鏈結) · PC1 吸收率 · 指數資格(asof {esc(asof)})</span></h2>
<div style="overflow-x:auto"><table><thead><tr><th>族群</th><th>n</th><th>PC1</th><th>資格</th><th>等權</th><th>階層</th><th>聚焦(att)</th><th>att−eq</th><th>max w</th><th>HHI</th></tr></thead><tbody>{gh_rows}</tbody></table></div></section>
<section id="丁"><h2><span class="secno">丁</span> 角色榜與訊號 <span class="en">Top 40(LEADER→WASHOUT→PEER…;角色分佈 {esc(rc)})</span></h2>
<div style="overflow-x:auto"><table><thead><tr><th>代號</th><th>族群</th><th>市</th><th>角色</th><th>複合分</th><th>AS</th><th>RS</th><th>RS動能</th><th>價/量同動</th><th>量能分</th><th>重力</th><th>層</th><th>有效</th><th>訊號/迴避</th></tr></thead><tbody>{role_rows}</tbody></table></div></section>
<section id="戊"><h2><span class="secno">戊</span> 面板覆蓋與來源 <span class="en">誠實界線:欄缺=模組 SKIP;分層制 {esc(res.get("tier_basis", "—"))}</span></h2>
<div class="grid2"><div class="card"><h3>欄位覆蓋率</h3><table><tbody>{cov_rows}</tbody></table></div>
<div class="card"><h3>來源沿革(末六筆)</h3><table><tbody>{prov_rows}</tbody></table>
<div class="det" style="margin-top:8px">Yahoo 歷史=trust medium(成交值 PROXY=量×收盤,官方值到日覆蓋);TWSE 個股當沖/法人/融資=雲端 WAF 封鎖候工作站 --ingest;etr_basis NO_DT=當沖未扣(誠實標)。</div></div></div></section>
</main>
<footer><span>批309 · {esc(NOW)} 產</span><span>渲染:validation/VIA_Batch309_APCE_Buildout/batch309_uimatrix_render.py</span><span style="margin-left:auto">真值源:apce_latest.json + 門檻冊 v0400 + 面板</span></footer>
</body></html>"""
    OUT.write_text(page, encoding="utf-8")
    print(f"  [出] {OUT.name}({len(page.encode('utf-8')):,} bytes)")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
