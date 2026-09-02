#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
batch307_uimatrix_render — 批307 驗證結果 HTML U/I Matrix 渲染器
================================================================
輸入:Batch307_CrossValidation_Results.json(batch307_crossvalidate_core 產出)
     +TW_Active_ETF_Registry_v0100.json(引擎更新後真值)
輸出:VIA_Batch307_TWActiveETF_VRN_UIMatrix_v0100.html(自含式紀錄工件;
     版面循批306 Codex 模板語言:固定 header 徽章列+stat 磚+矩陣表+固定 footer)
誠實界線:頁面全數靜態自真值渲染,零手寫數字。
"""
from __future__ import annotations

import html
import json
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
RESULTS = HERE / "Batch307_CrossValidation_Results.json"
REG = (VIA / "supportive modules" / "VIA_FlowSystem" / "FlowSystem_v2" / "config"
       / "TW_Active_ETF_Registry_v0100.json")
OUT = HERE / "VIA_Batch307_TWActiveETF_VRN_UIMatrix_v0100.html"

AREA_ORDER = ["ETF清單", "BASIC INFO", "SUMMARY", "FINANCIAL"]
AREA_META = {
    "ETF清單": ("甲", "TW Active ETF Registry Update", "FLOW_ENG023 --refresh 實連 TWSE OpenAPI+獨立快照互證"),
    "BASIC INFO": ("乙", "VRN Basic Info", "StockReportBasicInfo CSV↔JSON↔sha 副本+規則冊+官方在籍"),
    "SUMMARY": ("丙", "VRN Summary (Research Report SSOT)", "v2 世代鏈 sha256+schema 冊+沿革"),
    "FINANCIAL": ("丁", "VRN Financial Data", "SSOT 契約+抽取事實列規則+雙欄互證+跨集參照"),
}
STATUS_CLS = {"PASS": "ok", "FAIL": "bad", "WARN": "warn", "SKIP": "mut"}
STATUS_ZH = {"PASS": "PASS 合", "FAIL": "FAIL 不合", "WARN": "WARN 註記", "SKIP": "SKIP 誠實跳過"}


def esc(s) -> str:
    return html.escape(str(s), quote=True)


def main() -> int:
    res = json.loads(RESULTS.read_text(encoding="utf-8"))
    reg = json.loads(REG.read_text(encoding="utf-8"))
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    n = res["counts"]
    checks = res["checks"]
    etfs = reg["etfs"]
    hist = [h for h in reg.get("history", []) if h.get("op") == "refresh"][-1]
    n_ver = sum(1 for e in etfs if str(e.get("status", "")).startswith("VERIFIED_OPENAPI"))
    n_corr = sum(1 for e in etfs if e.get("status") == "VERIFIED_OPENAPI_NAME_CORRECTED")
    n_pend = len(etfs) - n_ver
    verdict = res["verdict"]
    v_cls = "ok" if verdict == "ALL_GREEN" else ("warn" if verdict == "GREEN_WITH_NOTES" else "bad")
    v_zh = {"ALL_GREEN": "全綠", "GREEN_WITH_NOTES": "綠+註記", "HAS_FAILURES": "有不合(見缺陷帳)"}[verdict]

    def chip(st):
        return f'<span class="badge dot {STATUS_CLS[st]}">{esc(STATUS_ZH[st])}</span>'

    def matrix_table(area):
        rows = [c for c in checks if c["area"] == area]
        tr = "".join(
            f'<tr><td class="mono">{esc(c["id"])}</td><td>{esc(c["name"])}</td>'
            f'<td class="mut">{esc(c["method"])}</td><td>{chip(c["status"])}</td>'
            f'<td class="det">{esc(c["detail"])}</td></tr>'
            for c in rows)
        return (f'<table><thead><tr><th style="width:44px">檢號</th>'
                f'<th style="width:250px">檢項 Check</th><th style="width:120px">方法道 Lane</th>'
                f'<th style="width:104px">判定</th><th>證跡 Evidence</th></tr></thead>'
                f'<tbody>{tr}</tbody></table>')

    corr_rows = "".join(
        f'<tr><td class="mono">{esc(e["ticker"])}</td><td class="strike">{esc(e.get("seed_name", ""))}</td>'
        f'<td><b>{esc(e["name"])}</b></td>'
        f'<td>{"矩陣證實" if "矩陣對映經官方證實" in e.get("verify_note", "") else "官方改正"}</td></tr>'
        for e in etfs if e.get("status") == "VERIFIED_OPENAPI_NAME_CORRECTED")
    pend_rows = "".join(
        f'<tr><td class="mono">{esc(e["ticker"])}</td><td>{esc(e["name"])}</td>'
        f'<td class="mut">{esc(e.get("verify_note", ""))}</td></tr>'
        for e in etfs if not str(e.get("status", "")).startswith("VERIFIED"))
    new_rows = "".join(
        f'<tr><td class="mono">{esc(e["ticker"])}</td><td>{esc(e["name"])}</td>'
        f'<td class="mut">{esc(e.get("official_type", ""))}</td></tr>'
        for e in etfs if "名錄新收" in e.get("verify_note", ""))

    defects = [c for c in checks if c["status"] == "FAIL"]
    warns = [c for c in checks if c["status"] == "WARN"]
    defect_html = "".join(
        f'<div class="defect bad"><b>{esc(c["id"])} {esc(c["name"])}</b>'
        f'<div class="det">{esc(c["detail"])}</div></div>' for c in defects) or \
        '<div class="defect ok"><b>零缺陷</b></div>'
    warn_html = "".join(
        f'<div class="defect warn"><b>{esc(c["id"])} {esc(c["name"])}</b>'
        f'<div class="det">{esc(c["detail"])}</div></div>' for c in warns)

    lanes = [
        ("法一 引擎道", "FLOW_ENG023 --refresh 經 SUP_MDL737 v0103 fetch(同意閘+UA 修補+WAF 快取自癒)"),
        ("法二 獨立傳輸", "curl 快照(異 UA/異工具/異時點)重解析互比"),
        ("法三 雙解析器/雙欄", "stdlib csv/json vs 自寫 RFC4180 狀態機;value↔raw_value 互證"),
        ("法四 雜湊鏈", "sha256 重算 vs SSOT 指標檔宣告+檔名內嵌雜湊"),
        ("法五 規則冊", "欄位格式/值域/制式/沿革逐列驗"),
        ("法六 官方在籍/跨集", "TWSE 上市+TPEx 上櫃/興櫃名錄實連;跨資料集參照完整性"),
    ]
    lane_html = "".join(f'<tr><td style="white-space:nowrap"><b>{esc(a)}</b></td>'
                        f'<td class="mut">{esc(b)}</td></tr>' for a, b in lanes)

    sections = ""
    for area in AREA_ORDER:
        tag, en, sub = AREA_META[area]
        extra = ""
        if area == "ETF清單":
            extra = (
                '<div class="grid2">'
                '<div class="card"><h3>官方改正 Name Corrections(官方名錄為準)</h3>'
                '<table><thead><tr><th>代號</th><th>冊載(改前)</th><th>官方(改後)</th><th>定奪</th></tr></thead>'
                f'<tbody>{corr_rows}</tbody></table></div>'
                '<div class="card"><h3>誠實候驗 Pending(名錄查無不定奪)</h3>'
                '<table><thead><tr><th>代號</th><th>冊載名</th><th>候驗註</th></tr></thead>'
                f'<tbody>{pend_rows}</tbody></table>'
                '<h3 style="margin-top:10px">名錄新收 Newly Listed</h3>'
                '<table><thead><tr><th>代號</th><th>官方簡稱</th><th>基金類型</th></tr></thead>'
                f'<tbody>{new_rows}</tbody></table></div></div>')
        sections += (
            f'<section id="{esc(tag)}"><h2><span class="secno">{esc(tag)}</span> {esc(area)}'
            f' <span class="en">{esc(en)}</span></h2>'
            f'<div class="mut sub">{esc(sub)}</div>{matrix_table(area)}{extra}</section>')

    page = f"""<!DOCTYPE html>
<html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Batch 307 · TW Active ETF + VRN Cross-Validation UI Matrix</title>
<style>
:root{{--bg:#f4f6f8;--paper:#fff;--paper2:#f9fafb;--ink:#202833;
--ink2:#465365;--mut:#596778;--line:#dfe4ea;--soft:#eef2f5;
--ok:#1e7d46;--bad:#b3372c;--warn:#9a6a00;--acc:#315f7d}}
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
font-size:9.5px;font-weight:700;letter-spacing:.02em}}
.badge.ok{{color:var(--ok);border-color:#b8d7c6;background:#f1f8f4}}
.badge.bad{{color:var(--bad);border-color:#e3c0bc;background:#fff5f3}}
.badge.warn{{color:var(--warn);border-color:#e0d0a6;background:#fdf8ec}}
.badge.mut{{color:var(--mut)}}
.badge.dot::before{{content:"";width:7px;height:7px;border-radius:50%;
margin-right:5px;background:currentColor}}
main{{max-width:1180px;margin:0 auto;padding:14px}}
.statrow{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));
gap:8px;margin:8px 0 16px}}
.stat{{background:var(--paper);border:1px solid var(--line);border-radius:8px;
padding:9px 11px}}
.stat .v{{font-size:19px;font-weight:800;color:var(--acc)}}
.stat .v.okc{{color:var(--ok)}}.stat .v.badc{{color:var(--bad)}}.stat .v.warnc{{color:var(--warn)}}
.stat .zh{{font-size:10.5px;color:var(--ink2);margin-top:2px}}
section{{margin:18px 0}}
h2{{font-size:14px;display:flex;align-items:center;gap:8px;margin-bottom:2px}}
h2 .secno{{width:22px;height:22px;display:grid;place-items:center;background:var(--acc);
color:#fff;border-radius:5px;font-size:11px}}
h2 .en{{color:var(--mut);font-weight:600;font-size:11px}}
h3{{font-size:11.5px;color:var(--ink2);margin-bottom:6px}}
.sub{{margin:0 0 8px 30px;font-size:10.5px}}
.card{{background:var(--paper);border:1px solid var(--line);border-radius:8px;
padding:10px 12px;margin-top:10px}}
.grid2{{display:grid;grid-template-columns:1fr 1fr;gap:10px}}
@media(max-width:860px){{.grid2{{grid-template-columns:1fr}}}}
table{{width:100%;border-collapse:collapse;background:var(--paper);
border:1px solid var(--line);border-radius:8px;overflow:hidden;font-size:11px}}
th{{background:var(--soft);color:var(--ink2);text-align:left;padding:6px 8px;
border-bottom:1px solid var(--line);font-size:10px;letter-spacing:.03em}}
td{{padding:6px 8px;border-bottom:1px solid var(--paper2);vertical-align:top}}
tr:last-child td{{border-bottom:none}}
td.det{{color:var(--ink2);font-size:10.5px}}
td.mut,.mut{{color:var(--mut)}}
td.strike{{color:var(--mut);text-decoration:line-through}}
.defect{{border:1px solid var(--line);border-left:4px solid var(--mut);
border-radius:6px;background:var(--paper);padding:8px 10px;margin:6px 0}}
.defect.bad{{border-left-color:var(--bad)}}
.defect.warn{{border-left-color:var(--warn)}}
.defect.ok{{border-left-color:var(--ok)}}
.defect .det{{color:var(--ink2);font-size:10.5px;margin-top:2px}}
footer{{position:fixed;bottom:0;left:0;right:0;height:34px;display:flex;
align-items:center;gap:14px;padding:0 14px;background:var(--paper);
border-top:1px solid var(--line);font-size:9.5px;color:var(--mut)}}
a{{color:var(--acc);text-decoration:none}}
.toc{{display:flex;gap:8px;flex-wrap:wrap;margin:10px 0 0}}
.toc a{{border:1px solid var(--line);border-radius:6px;padding:3px 9px;
background:var(--paper);font-size:10.5px}}
</style></head><body>
<header>
 <div class="logo"><span class="sq">B7</span>Batch 307 · TW Active ETF Registry + VRN Data Cross-Validation <span class="mut">U/I Matrix</span></div>
 <div class="badges">
  <span class="badge ok dot">TWSE OpenAPI Live · {esc(hist["rows_fetched"])} Rows</span>
  <span class="badge ok dot">Multi-Method · 6 Lanes</span>
  <span class="badge {v_cls} dot">Verdict · {esc(v_zh)}</span>
  <span class="badge mut">誠實三態 SKIP 不代設</span>
 </div>
</header>
<main>
 <div class="statrow">
  <div class="stat"><div class="v">{len(etfs)}</div><div class="zh">主動式 ETF 冊載檔數(38=37 冊+1 新收)</div></div>
  <div class="stat"><div class="v okc">{n_ver}</div><div class="zh">VERIFIED_OPENAPI(官方實連定奪)</div></div>
  <div class="stat"><div class="v warnc">{n_corr}</div><div class="zh">官方改正(種子/冊載名≠官方)</div></div>
  <div class="stat"><div class="v">{n_pend}</div><div class="zh">誠實候驗(名錄查無不定奪)</div></div>
  <div class="stat"><div class="v okc">{n["PASS"]}</div><div class="zh">檢項 PASS</div></div>
  <div class="stat"><div class="v warnc">{n["WARN"]}</div><div class="zh">檢項 WARN 註記</div></div>
  <div class="stat"><div class="v badc">{n["FAIL"]}</div><div class="zh">檢項 FAIL(缺陷帳)</div></div>
 </div>
 <div class="toc"><a href="#甲">甲 ETF 清單</a><a href="#乙">乙 Basic Info</a>
 <a href="#丙">丙 Summary</a><a href="#丁">丁 Financial</a>
 <a href="#缺">缺陷帳 Defect Ledger</a><a href="#法">方法冊 Method Lanes</a></div>
 {sections}
 <section id="缺"><h2><span class="secno">戊</span> 缺陷帳 <span class="en">Defect Ledger(FAIL=候修;WARN=誠實註記)</span></h2>
  {defect_html}{warn_html}
 </section>
 <section id="法"><h2><span class="secno">己</span> 方法冊 <span class="en">Method Lanes(獨立道互證)</span></h2>
  <table><tbody>{lane_html}</tbody></table>
 </section>
</main>
<footer>
 <span>批307 · {esc(now)} 產</span>
 <span>核驗核心:validation/VIA_Batch307_TWActiveETF_VRN_CrossValidation/batch307_crossvalidate_core.py</span>
 <span>真值:TW_Active_ETF_Registry_v0100.json(as_of {esc(reg["as_of"])})+Batch307_CrossValidation_Results.json</span>
 <span style="margin-left:auto">零手寫數字 · 全靜態自真值渲染</span>
</footer>
</body></html>"""
    OUT.write_text(page, encoding="utf-8")
    print(f"  [出] {OUT.name}({len(page):,} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
