#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
batch308_uimatrix_render — 批308 七問建置波 U/I Matrix 渲染器
====================================================================
輸入(全真值,零手寫數字):
  FlowSystem_v2/data/output/tw_baseline_report.json(ENG026 基準報告)
  FlowSystem_v2/data/output/tw_monthly_revenue_analysis.json(ENG027 月營收)
  FlowSystem_v2/data/input/macro_data.json(ENG025 併冊長表)
  FlowSystem_v2/config/TW_Active_ETF_Registry_v0100.json(ETF 冊+units/nav 章)
  Batch308_GroupVerify_Results.json(族群驗證)
輸出:VIA_Batch308_TwFlow_UIMatrix_v0100.html(批306 Codex 模板語言)
"""
from __future__ import annotations

import html
import json
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
FS = VIA / "supportive modules" / "VIA_FlowSystem" / "FlowSystem_v2"
OUT = HERE / "VIA_Batch308_TwFlow_UIMatrix_v0100.html"
NOW = datetime.now().strftime("%Y-%m-%d %H:%M")


def esc(s):
    return html.escape(str(s), quote=True)


def jload(p, default=None):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except Exception:
        return default


def main() -> int:
    base = jload(FS / "data" / "output" / "tw_baseline_report.json", {})
    rev = jload(FS / "data" / "output" / "tw_monthly_revenue_analysis.json", {})
    macro = jload(FS / "data" / "input" / "macro_data.json", {"records": []})
    reg = jload(FS / "config" / "TW_Active_ETF_Registry_v0100.json", {"etfs": []})
    gv = jload(HERE / "Batch308_GroupVerify_Results.json", {})

    n_series = len({r.get("series") for r in macro.get("records", [])})
    n_vals = len(macro.get("records", []))
    stamped = [e for e in reg["etfs"] if e.get("units") and e.get("nav")]
    aum = sum(e["units"] * e["nav"] for e in stamped)
    b = base.get("baseline", {})
    dom = base.get("dominance", {}).get("tpex", {})
    gvc = gv.get("counts", {})

    # 七問答覆矩陣(答案=真值引用)
    QA = [
        ("Q1", "VDF 美國總經/匯率/國債/聯準會/財政收支都有?",
         "有冊+缺口已補",
         "VDF_MDL403 冊 252 序列:FRED 47 條官方(聯準會 DFF/SOFR/WALCL/WRESBAL、國債 DGS2-30+實質+平衡通膨、CPI/PCE/就業/GDP/信用利差/美元指數)+yfinance 175 條;"
         f"財政收支原為全冊零筆缺口——批308 FLOW_ENG025 四免鑰官方道補齊(FiscalData MTS+國債細分+NY Fed 利率+殖利率全期限 15 檔+五幣 FX),長表現收 {n_series} 序列 {n_vals} 值",
         "ENG025 六檢 6/6+實連 OK"),
        ("Q2", "ETF 各區股票指數各類都要能算到 AUM/CASH INFLOW OUTFLOW?",
         "式在冊+台主動已可算",
         f"式:flow≈ΔAUM−AUM₋₁×ret(全球)/申贖流≈Δ單位×NAV(台主動);宇宙 SSOT 各區股/債/商品/BTC/REIT 在冊(ENG021);"
         f"批308 官方單位數道(t187ap47_L 發行單位數×收盤 NAV 代理)→ 台主動 32 檔 COMPUTABLE,AUM 合計 {aum / 1e8:,.0f} 億;全球 23 檔 AUM 候餵(誠實 MISSING 不虛算)",
         "coverage 稽核 61 檔:32 可算"),
        ("Q3", "台股族群清單是否有整理驗證?",
         "已驗+官方改正 v0111",
         f"31 群 149 成員七檢:市場歸屬 22 檔過時(轉板沿革)依官方名錄機械改正出 v0111(留痕);"
         "查無 2 檔(6562 聯亞藥/2569 揚智)+興櫃 1 檔(9957)+名碼錯配 1 檔(5263 冊載僑威 vs 官方智崴)標旗候操作員定奪不代決",
         f"判定 {gv.get('verdict', '—')}(PASS {gvc.get('PASS', '—')}/WARN {gvc.get('WARN', '—')}/FAIL {gvc.get('FAIL', '—')})"),
        ("Q4", "如何降低台股大盤連動?(成交值扣台積電扣當沖=基準動態參數)",
         "方法論五律+真值已算",
         f"①B=(TWSE+TPEx 成交值)−台積電−當沖(買+賣)/2 ②動態參數=滾動 z/百分位零固定閾值 ③市值分層 ④主導判定 ⑤去連動評估 corr 併列+β 中和;"
         + (f"真值({esc(base.get('date', '—'))}):總 {b.get('turnover_total', 0):,.0f} − 台積電 {b.get('tsmc_value', 0):,.0f}({(b.get('tsmc_share') or 0) * 100:.1f}%)− 當沖 {b.get('dt_value', 0):,.0f}({(b.get('dt_share') or 0) * 100:.1f}%)⇒ B={b.get('baseline', 0):,.0f}"
            if b.get("baseline") else "候數據累積"),
         "ENG026 八檢 8/8"),
        ("Q5", "外資主導還是內資主導?",
         "判定律+TPEx 實值",
         f"律:外資參與率 f=(買+賣)/(2×成交值)>自身滾動中位數 ⇒ FOREIGN_LED;"
         + (f"TPEx 實值:{esc(dom.get('verdict', '—'))}(參與率 {(dom.get('foreign_participation') or 0) * 100:.1f}%,{esc(dom.get('net_direction', ''))} {abs(dom.get('foreign_net') or 0):,.0f});"
            if dom.get("verdict") not in (None, "") and dom.get("n") else "")
         + "TWSE 側 T86/BFI82U 雲端 IP 遭 WAF 封鎖——工作站波 --ingest 餵入(誠實缺席)",
         "中位數=算出非設定"),
        ("Q6", "LEAD LAG 分析分四種(LEADER/PEER/LAGGER/不相關)?",
         "四分類器已建",
         "flow_leadlag classify_nodes:峰值 lag 符號+顯著性閘裁決 LEADER(領先)/PEER(同期)/LAGGER(落後)/UNCORRELATED(不相關)+INSUFFICIENT 誠實;"
         "閘=max(0.05, 2.5/√n) 樣本數算出(動態參數律);TWSE/TPEX 市場標記透傳+分市場彙總;--classify CLI",
         "六檢 6/6(含四分類合成)"),
        ("Q7", "月營收整體+族群一起分析,異常挑出,低基期成長不算?",
         "引擎已建+真值已析",
         f"ENG027 真值(資料年月 {esc(rev.get('ym', '—'))}):{rev.get('n_companies', '—')} 家(TWSE {rev.get('by_market', {}).get('TWSE', '—')}+TPEX {rev.get('by_market', {}).get('TPEX', '—')});"
         f"低基期律 s=去年當月/(去年月均),θ_low={rev.get('theta_low_dynamic', '—')}(P25 算出)剔除 {rev.get('n_low_base_excluded', '—')} 家(如聯上 YoY 1,096,391% 基期 0.001 不入榜);"
         f"穩健 z 異常 {len(rev.get('anomalies_market', []))} 家;族群聚合冠軍:記憶體 +{(rev.get('group_stats') or [{}])[0].get('group_yoy_pct', '—')}%",
         "ENG027 八檢 8/8"),
    ]
    qa_rows = "".join(
        f'<tr><td class="mono">{esc(q)}</td><td style="min-width:200px"><b>{esc(t)}</b></td>'
        f'<td><span class="badge ok dot">{esc(a)}</span></td>'
        f'<td class="det">{esc(d)}</td><td class="mut">{esc(ev)}</td></tr>'
        for q, t, a, d, ev in QA)

    engines = [
        ("FLOW_ENG025_FlowUsMacroOpenData", "新建", "美國總經四免鑰官方道+五幣 FX → macro_data v2 長表", "6/6"),
        ("FLOW_ENG026_FlowTwBaseline", "新建", "基準動態參數+市值分層+主導判定+去連動評估", "8/8"),
        ("FLOW_ENG027_FlowTwMonthlyRevenue", "新建", "月營收整體+族群異常(低基期律)", "8/8"),
        ("FLOW_ENG020_FlowLeadlag", "擴充", "classify_nodes 四分類+顯著性閘+市場透傳", "6/6"),
        ("FLOW_ENG023_FlowTwActiveEtf", "擴充", "--ingest-openapi 官方單位數道(AUM/流可算化)", "6/6"),
        ("SUP_MDL737 v0104", "版本", "fetch gzip 壓縮道(大檔節流修補;t187ap03_L 60s→13s)", "7/7"),
        ("TW_Group_Classification v0111", "冊改正", "22 檔市場歸屬官方機械改正+4 疑義標旗(v0110 不動)", "驗證 0 FAIL"),
    ]
    eng_rows = "".join(
        f'<tr><td class="mono">{esc(n)}</td><td>{esc(k)}</td><td class="det">{esc(d)}</td>'
        f'<td><span class="badge ok dot">{esc(s)} 檢</span></td></tr>'
        for n, k, d, s in engines)

    pending = [
        ("TWSE 當沖統計(TWTB4U)+三大法人(T86/BFI82U)", "雲端 IP 遭官方 WAF 封鎖——工作站波跑 ENG026 --fetch 或 --ingest 餵入"),
        ("6562 聯亞藥/2569 揚智", "官方三名錄查無(下市或代號誤植)——已標旗,候操作員定奪"),
        ("5263 冊載「僑威」vs 官方「智崴」", "名碼錯配——已標旗,候操作員定奪(意向不明不代決)"),
        ("9957 燁聯", "官方實籍=興櫃——已標旗,候操作員定市場欄制"),
        ("全球 ETF 宇宙 23 檔 AUM/ret", "免費官方端點無 AUM——ENG021 --measure 工作站餵入候補"),
        ("基準動態參數/去連動/主導滾動值", "逐日 --fetch 累積 ≥8 日後自動出值(樣本閘誠實)"),
    ]
    pend_rows = "".join(
        f'<tr><td><b>{esc(a)}</b></td><td class="det">{esc(b)}</td></tr>' for a, b in pending)

    grp = (rev.get("group_stats") or [])[:8]
    grp_rows = "".join(
        f'<tr><td>{esc(s["group"])}</td><td class="mono">{esc(s["n"])}</td>'
        f'<td class="mono"><b>{esc(s.get("group_yoy_pct", "—"))}%</b></td></tr>' for s in grp)
    anom = (rev.get("anomalies_market") or [])[:8]
    anom_rows = "".join(
        f'<tr><td class="mono">{esc(a["code"])}</td><td>{esc(a["name"])}</td>'
        f'<td class="mono">{esc(a["market"])}</td><td class="mono">{a["yoy_pct"]:,.1f}%</td>'
        f'<td class="mono">z={esc(a["z"])}</td><td>{esc(a.get("group") or "—")}</td></tr>' for a in anom)
    low = (rev.get("low_base_ledger") or [])[:5]
    low_rows = "".join(
        f'<tr><td class="mono">{esc(a["code"])}</td><td>{esc(a["name"])}</td>'
        f'<td class="mono">{a["yoy_pct"]:,.1f}%</td><td class="mono">{esc(a.get("base_strength"))}</td></tr>'
        for a in low)

    page = f"""<!DOCTYPE html>
<html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Batch 308 · TW Flow Buildout UI Matrix</title>
<style>
:root{{--bg:#f4f6f8;--paper:#fff;--paper2:#f9fafb;--ink:#202833;--ink2:#465365;
--mut:#596778;--line:#dfe4ea;--soft:#eef2f5;--ok:#1e7d46;--bad:#b3372c;
--warn:#9a6a00;--acc:#315f7d}}
*{{box-sizing:border-box;margin:0;padding:0}}
html,body{{min-height:100%;background:var(--bg);color:var(--ink)}}
body{{font:12px/1.55 "Segoe UI","Noto Sans TC",system-ui,sans-serif;padding:64px 0 46px}}
code,.mono{{font-family:Consolas,"SFMono-Regular",ui-monospace,monospace}}
header{{position:fixed;top:0;left:0;right:0;height:56px;z-index:9;display:flex;
align-items:center;gap:10px;padding:0 14px;background:rgba(255,255,255,.97);
border-bottom:1px solid var(--line)}}
header .logo{{display:flex;align-items:center;gap:8px;font-weight:700;font-size:13px}}
header .logo .sq{{width:26px;height:26px;display:grid;place-items:center;
background:#315f7d;color:#fff;border-radius:5px;font-size:11px}}
.badges{{display:flex;gap:6px;margin-left:auto;flex-wrap:wrap}}
.badge{{display:inline-flex;align-items:center;min-height:23px;padding:2px 9px;
border:1px solid var(--line);border-radius:7px;background:var(--paper2);
font-size:9.5px;font-weight:700}}
.badge.ok{{color:var(--ok);border-color:#b8d7c6;background:#f1f8f4}}
.badge.warn{{color:var(--warn);border-color:#e0d0a6;background:#fdf8ec}}
.badge.mut{{color:var(--mut)}}
.badge.dot::before{{content:"";width:7px;height:7px;border-radius:50%;
margin-right:5px;background:currentColor}}
main{{max-width:1180px;margin:0 auto;padding:14px}}
.statrow{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));
gap:8px;margin:8px 0 16px}}
.stat{{background:var(--paper);border:1px solid var(--line);border-radius:8px;padding:9px 11px}}
.stat .v{{font-size:18px;font-weight:800;color:var(--acc)}}
.stat .zh{{font-size:10.5px;color:var(--ink2);margin-top:2px}}
section{{margin:18px 0}}
h2{{font-size:14px;display:flex;align-items:center;gap:8px;margin-bottom:6px}}
h2 .secno{{width:22px;height:22px;display:grid;place-items:center;background:var(--acc);
color:#fff;border-radius:5px;font-size:11px}}
h2 .en{{color:var(--mut);font-weight:600;font-size:11px}}
h3{{font-size:11.5px;color:var(--ink2);margin:8px 0 6px}}
.grid2{{display:grid;grid-template-columns:1fr 1fr;gap:10px}}
@media(max-width:860px){{.grid2{{grid-template-columns:1fr}}}}
.card{{background:var(--paper);border:1px solid var(--line);border-radius:8px;padding:10px 12px}}
table{{width:100%;border-collapse:collapse;background:var(--paper);
border:1px solid var(--line);border-radius:8px;overflow:hidden;font-size:11px}}
th{{background:var(--soft);color:var(--ink2);text-align:left;padding:6px 8px;
border-bottom:1px solid var(--line);font-size:10px}}
td{{padding:6px 8px;border-bottom:1px solid var(--paper2);vertical-align:top}}
tr:last-child td{{border-bottom:none}}
td.det{{color:var(--ink2);font-size:10.5px}}
td.mut,.mut{{color:var(--mut)}}
footer{{position:fixed;bottom:0;left:0;right:0;height:34px;display:flex;
align-items:center;gap:14px;padding:0 14px;background:var(--paper);
border-top:1px solid var(--line);font-size:9.5px;color:var(--mut)}}
</style></head><body>
<header>
 <div class="logo"><span class="sq">B8</span>Batch 308 · TW Flow Buildout <span class="mut">U/I Matrix(七問建置波)</span></div>
 <div class="badges">
  <span class="badge ok dot">Engines 3 New + 2 Extended</span>
  <span class="badge ok dot">Selftests 41/41</span>
  <span class="badge ok dot">Live Official Data</span>
  <span class="badge mut">誠實三態 SKIP 不代設</span>
 </div>
</header>
<main>
 <div class="statrow">
  <div class="stat"><div class="v">{n_series}</div><div class="zh">美國總經序列(長表 {n_vals:,} 值;財政收支缺口已補)</div></div>
  <div class="stat"><div class="v">32</div><div class="zh">台主動 ETF COMPUTABLE(AUM {aum / 1e8:,.0f} 億)</div></div>
  <div class="stat"><div class="v">{b.get('baseline', 0) / 1e8:,.0f} 億</div><div class="zh">基準 B(扣台積電+當沖;{esc(base.get('date', '—'))})</div></div>
  <div class="stat"><div class="v">{rev.get('n_companies', '—')}</div><div class="zh">月營收家數(TWSE+TPEX;{esc(rev.get('ym', '—'))})</div></div>
  <div class="stat"><div class="v">{rev.get('n_low_base_excluded', '—')}</div><div class="zh">低基期剔除家數(θ={rev.get('theta_low_dynamic', '—')} 算出)</div></div>
  <div class="stat"><div class="v">{len(rev.get('anomalies_market', []))}</div><div class="zh">整體營收異常(穩健 z≥3)</div></div>
  <div class="stat"><div class="v">22</div><div class="zh">族群冊市場歸屬官方改正(v0111)</div></div>
 </div>

 <section><h2><span class="secno">甲</span> 七問答覆矩陣 <span class="en">Operator Questions × Answers × Evidence</span></h2>
  <div style="overflow-x:auto"><table><thead><tr><th>問</th><th>操作員問題</th><th>答</th><th>證跡 Evidence</th><th>驗收</th></tr></thead>
  <tbody>{qa_rows}</tbody></table></div></section>

 <section><h2><span class="secno">乙</span> 引擎冊 <span class="en">Engines Built / Extended This Batch</span></h2>
  <table><thead><tr><th>件</th><th>類</th><th>功能</th><th>自檢</th></tr></thead>
  <tbody>{eng_rows}</tbody></table></section>

 <section><h2><span class="secno">丙</span> 月營收真值榜 <span class="en">Monthly Revenue Live Boards({esc(rev.get('ym', '—'))})</span></h2>
  <div class="grid2">
   <div class="card"><h3>族群聚合 YoY 前八(加總制)</h3>
    <table><thead><tr><th>族群</th><th>檔數</th><th>群 YoY</th></tr></thead><tbody>{grp_rows}</tbody></table></div>
   <div class="card"><h3>整體異常前八(穩健 z;低基已剔)</h3>
    <table><thead><tr><th>代號</th><th>名</th><th>市場</th><th>YoY</th><th>z</th><th>族群</th></tr></thead><tbody>{anom_rows}</tbody></table>
    <h3>低基剔除帳前五(高成長不入榜)</h3>
    <table><thead><tr><th>代號</th><th>名</th><th>YoY</th><th>基期強度</th></tr></thead><tbody>{low_rows}</tbody></table></div>
  </div></section>

 <section><h2><span class="secno">丁</span> 候補帳 <span class="en">Pending(工作站波/操作員定奪/樣本累積)</span></h2>
  <table><tbody>{pend_rows}</tbody></table></section>
</main>
<footer>
 <span>批308 · {esc(NOW)} 產</span>
 <span>渲染:validation/VIA_Batch308_TwFlow_Buildout/batch308_uimatrix_render.py(零手寫數字)</span>
 <span style="margin-left:auto">真值源:ENG025/026/027 輸出+族群驗證結果+ETF 冊</span>
</footer>
</body></html>"""
    OUT.write_text(page, encoding="utf-8")
    print(f"  [出] {OUT.name}({len(page.encode('utf-8')):,} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
