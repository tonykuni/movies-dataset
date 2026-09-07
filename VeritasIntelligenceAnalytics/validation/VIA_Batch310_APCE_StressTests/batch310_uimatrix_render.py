#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch310_uimatrix_render — 批310 壓力測試結果 U/I Matrix(零手寫數字)"""
from __future__ import annotations
import html, json
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
RES = HERE / "Batch310_StressTest_Results.json"
OUT = HERE / "VIA_Batch310_APCE_StressTest_UIMatrix_v0100.html"
NOW = datetime.now().strftime("%Y-%m-%d %H:%M")
esc = lambda s: html.escape(str(s), quote=True)
CLS = {"PASS": "ok", "FAIL": "bad", "WARN": "warn", "INFO": "acc", "SKIP": "mut"}

def f(v, nd=3):
    if v is None: return "—"
    if isinstance(v, bool): return "✓" if v else "✗"
    if isinstance(v, float): return f"{v:,.{nd}f}"
    return str(v)

def table(head, rows):
    th = "".join(f"<th>{esc(h)}</th>" for h in head)
    tb = "".join("<tr>" + "".join(f'<td class="mono">{c}</td>' for c in r) + "</tr>" for r in rows)
    return f'<div style="overflow-x:auto"><table><thead><tr>{th}</tr></thead><tbody>{tb}</tbody></table></div>'

def main() -> int:
    d = json.loads(RES.read_text(encoding="utf-8"))
    st, n = d.get("stats", {}), d.get("counts", {})
    chk_rows = "".join(
        f'<tr><td class="mono">{esc(c["id"])}</td><td><b>{esc(c["name"])}</b></td>'
        f'<td><span class="badge {CLS.get(c["status"], "mut")} dot">{esc(c["status"])}</span></td><td class="det">{esc(c["detail"])}</td></tr>'
        for c in d["checks"])
    ic = table(["因子", "期", "日數", "均 IC", "t", "勝率"],
               [[esc(r["feature"]), r["horizon"], r["n_days"], f"{r['mean_ic']:+.4f}", f"{r['t']:+.2f}", f"{r['hit']:.0%}"]
                for r in sorted(st.get("ic", []), key=lambda r: -abs(r["t"]))])
    rf = table(["角色", "n", "fwd5 %", "fwd20 %", "t5", "t20"],
               [[esc(r["role"]), r["n"], f"{r['fwd5_mean']:+.2f}", f"{r['fwd20_mean']:+.2f}", r["t5"], r["t20"]] for r in st.get("role_fwd", [])])
    pl = table(["參數", "值", "角色一致率", "LEADER Jaccard", "LEADER 數"],
               [[esc(r["param"]), r["value"], f(r["role_agreement"]), f(r["leader_jaccard"]), r["n_leader"]] for r in st.get("plateau", [])])
    ab = table(["拔除", "角色變動率", "LEADER 數", "FAKE/WASH 數"],
               [[esc(r["ablate"]), f"{r['role_change']:.1%}", r["n_leader"], r["n_fake_wash"]] for r in st.get("ablation", [])])
    pm = table(["族群", "峰值 lag", "IC", "p", "BH 臨界", "FDR 顯著", "方向"],
               [[esc(r["sector"]), f"{r['peak_lag']:+d}", f"{r['ic']:+.3f}", r["p"], r.get("bh_crit"), f(r.get("fdr_sig")), esc(r["direction"])]
                for r in st.get("permutation", [])])
    la = table(["族群", "T-1 終值", "T0 終值", "偏誤"], [[esc(r["sector"]), r["t1"], r["t0"], f"{r['bias']:+.2%}"] for r in st.get("lookahead", [])])
    sv = table(["族群", "退出成員", "鏈結", "回填", "高估"], [[esc(r["sector"]), esc(r["removed"]), r["chain"], r["backfill"], f"{r['bias']:+.2%}"] for r in st.get("survivorship", [])])
    pc = st.get("pc1", {})
    pcr = table(["族群", "40 窗", "60 窗", "90 窗"], [[esc(s), f(v.get("40")), f(v.get("60")), f(v.get("90"))]
                for s, v in sorted(pc.items(), key=lambda kv: -((kv[1].get("60") or 0)))])
    reg = table(["引擎", "rc", "自檢"], [[esc(r["engine"]), r["rc"], esc(r["tally"])] for r in st.get("regression", [])])
    fam = st.get("family", {})
    to = st.get("turnover", {})
    cap = st.get("cap", {})
    sc = st.get("smallcap", {})
    pr = st.get("proxy_ratio", {})
    page = f"""<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Batch 310 · APCE Stress Tests</title>
<style>
:root{{--bg:#f4f6f8;--paper:#fff;--paper2:#f9fafb;--ink:#202833;--ink2:#465365;--mut:#596778;--line:#dfe4ea;--soft:#eef2f5;--ok:#1e7d46;--bad:#b3372c;--warn:#9a6a00;--acc:#315f7d}}
*{{box-sizing:border-box;margin:0;padding:0}}html,body{{min-height:100%;background:var(--bg);color:var(--ink)}}
body{{font:12px/1.55 "Segoe UI","Noto Sans TC",system-ui,sans-serif;padding:64px 0 46px}}code,.mono{{font-family:Consolas,"SFMono-Regular",ui-monospace,monospace}}
header{{position:fixed;top:0;left:0;right:0;height:56px;z-index:9;display:flex;align-items:center;gap:10px;padding:0 14px;background:rgba(255,255,255,.97);border-bottom:1px solid var(--line)}}
header .logo{{display:flex;align-items:center;gap:8px;font-weight:700;font-size:13px}}header .logo .sq{{width:26px;height:26px;display:grid;place-items:center;background:#315f7d;color:#fff;border-radius:5px;font-size:11px}}
.badges{{display:flex;gap:6px;margin-left:auto;flex-wrap:wrap}}.badge{{display:inline-flex;align-items:center;min-height:21px;padding:1px 8px;border:1px solid var(--line);border-radius:7px;background:var(--paper2);font-size:9.5px;font-weight:700;white-space:nowrap}}
.badge.ok{{color:var(--ok);border-color:#b8d7c6;background:#f1f8f4}}.badge.bad{{color:var(--bad);border-color:#e3c0bc;background:#fff5f3}}.badge.warn{{color:var(--warn);border-color:#e0d0a6;background:#fdf8ec}}.badge.acc{{color:var(--acc);border-color:#b9cbd8;background:#eef4f8}}.badge.mut{{color:var(--mut)}}
.badge.dot::before{{content:"";width:7px;height:7px;border-radius:50%;margin-right:5px;background:currentColor}}
main{{max-width:1240px;margin:0 auto;padding:14px}}.statrow{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:8px;margin:8px 0 16px}}
.stat{{background:var(--paper);border:1px solid var(--line);border-radius:8px;padding:9px 11px}}.stat .v{{font-size:18px;font-weight:800;color:var(--acc)}}.stat .zh{{font-size:10.5px;color:var(--ink2);margin-top:2px}}
section{{margin:18px 0}}h2{{font-size:14px;display:flex;align-items:center;gap:8px;margin-bottom:6px}}h2 .secno{{width:22px;height:22px;display:grid;place-items:center;background:var(--acc);color:#fff;border-radius:5px;font-size:11px}}h2 .en{{color:var(--mut);font-weight:600;font-size:11px}}
h3{{font-size:11.5px;color:var(--ink2);margin:8px 0 6px}}.card{{background:var(--paper);border:1px solid var(--line);border-radius:8px;padding:10px 12px;margin-top:10px}}
table{{width:100%;border-collapse:collapse;background:var(--paper);border:1px solid var(--line);border-radius:8px;overflow:hidden;font-size:11px}}th{{background:var(--soft);color:var(--ink2);text-align:left;padding:6px 8px;border-bottom:1px solid var(--line);font-size:10px}}
td{{padding:5px 8px;border-bottom:1px solid var(--paper2);vertical-align:top}}tr:last-child td{{border-bottom:none}}td.det{{color:var(--ink2);font-size:10.5px}}.mut{{color:var(--mut)}}
.grid2{{display:grid;grid-template-columns:1fr 1fr;gap:10px}}@media(max-width:900px){{.grid2{{grid-template-columns:1fr}}}}
footer{{position:fixed;bottom:0;left:0;right:0;height:34px;display:flex;align-items:center;gap:14px;padding:0 14px;background:var(--paper);border-top:1px solid var(--line);font-size:9.5px;color:var(--mut)}}
</style></head><body>
<header><div class="logo"><span class="sq">B10</span>Batch 310 · APCE 壓力測試 <span class="mut">Stress Tests · Devil's Advocate Wave</span></div>
<div class="badges"><span class="badge {CLS.get('PASS')} dot">PASS {n.get('PASS', 0)}</span><span class="badge warn dot">WARN {n.get('WARN', 0)}</span><span class="badge acc dot">INFO {n.get('INFO', 0)}</span><span class="badge bad dot">FAIL {n.get('FAIL', 0)}</span><span class="badge mut">判定 {esc(d.get('verdict'))}</span></div></header>
<main>
<div class="statrow">
 <div class="stat"><div class="v">{len(d['checks'])}</div><div class="zh">測試項(真實面板 {esc(st.get('baseline', {}).get('n', '—'))} 檔;asof {esc(st.get('baseline', {}).get('asof', '—'))})</div></div>
 <div class="stat"><div class="v">{f(to.get('role_change_rate'), 3) if to.get('role_change_rate') is None else f"{to['role_change_rate']:.1%}"}</div><div class="zh">角色日變動率</div></div>
 <div class="stat"><div class="v">{(f"{(1 - to['valid_member_flip'] / to['valid_raw_flip']):.0%}" if to.get('valid_raw_flip') else '—')}</div><div class="zh">遲滯翻轉降幅</div></div>
 <div class="stat"><div class="v">{f(pr.get('median'), 4)}</div><div class="zh">PROXY/官方成交值中位比(n={pr.get('n', '—')})</div></div>
 <div class="stat"><div class="v">{sum(1 for r in st.get('permutation', []) if r.get('fdr_sig'))}</div><div class="zh">CCF 置換 FDR 顯著族群 / {len(st.get('permutation', []))}</div></div>
 <div class="stat"><div class="v">{len(cap.get('infeasible', []))}</div><div class="zh">封頂不可行族群(n×0.18&lt;1)</div></div>
 <div class="stat"><div class="v">{sc.get('vol_shock_top10_small', '—')}→{sc.get('gravity_top10_small', '—')}</div><div class="zh">Top10 Small 數:時序 Z → 重力乘數</div></div>
</div>
<section><h2><span class="secno">甲</span> 測試總表 <span class="en">14 類 × 判定 × 證跡</span></h2>
<div style="overflow-x:auto"><table><thead><tr><th>檢</th><th>測試</th><th>判定</th><th>證跡</th></tr></thead><tbody>{chk_rows}</tbody></table></div></section>
<section><h2><span class="secno">乙</span> 統計效度 <span class="en">IC 檢定 · 角色前瞻報酬(誠實列數,不美化)</span></h2>
<div class="grid2"><div class="card"><h3>因子 IC(逐日橫截面 Spearman)</h3>{ic}</div><div class="card"><h3>角色前瞻報酬(均,%;重疊樣本)</h3>{rf}</div></div></section>
<section><h2><span class="secno">丙</span> 穩健性 <span class="en">高原 · 閹割 · 置換+FDR</span></h2>
<div class="grid2"><div class="card"><h3>T10 高原測試</h3>{pl}<h3>T11 閹割測試</h3>{ab}</div><div class="card"><h3>T12 CCF ±5 置換(B=200)+BH FDR q=0.10</h3>{pm}</div></div></section>
<section><h2><span class="secno">丁</span> 偏誤量化 <span class="en">前視(T0 vs T-1) · 倖存者(回填 vs 鏈結) · PC1 跨窗</span></h2>
<div class="grid2"><div class="card"><h3>T6 前視偏誤</h3>{la}<h3>T7 倖存者偏差</h3>{sv}</div><div class="card"><h3>T9 PC1 吸收率跨窗</h3>{pcr}</div></div></section>
<section><h2><span class="secno">戊</span> 迴歸與家族 <span class="en">全引擎自檢 · 參數家族實值校準</span></h2>
<div class="grid2"><div class="card"><h3>T1 迴歸</h3>{reg}</div><div class="card"><h3>T14 家族校準</h3><div class="det mono">state={esc(fam.get('state'))}<br>modes={esc(fam.get('modes'))} fired={esc(fam.get('fired'))}<br>C-05={esc(fam.get('C-05'))}<br>C-06={esc(fam.get('C-06'))}<br>C-13={esc(fam.get('C-13'))}</div></div></div></section>
</main>
<footer><span>批310 · {esc(NOW)} 產</span><span>渲染:validation/VIA_Batch310_APCE_StressTests/batch310_uimatrix_render.py</span><span style="margin-left:auto">真值源:Batch310_StressTest_Results.json</span></footer>
</body></html>"""
    OUT.write_text(page, encoding="utf-8")
    print(f"  [出] {OUT.name}({len(page.encode('utf-8')):,} bytes)")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
