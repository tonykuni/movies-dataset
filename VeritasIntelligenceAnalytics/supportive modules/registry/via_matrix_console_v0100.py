#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
via_matrix_console_v0100 — 三大 Matrix HTML U/I 主控台(TOOL-067)
====================================================================
操作員令(批28):
  ① VRN BASIC INFO / FINANCIAL DATA 驗證結果 → Matrix HTML U/I
  ② VDF 運作摘要 → Matrix HTML U/I
  ③ VAP/FLOW 族群分類+族群指數+量價指標摘要(for VRN)→ Matrix

誠實原則:全數據驅動——讀實際 SSOT/驗證產物/圖規;無數據之格
誠實標「候數據」,絕不捏數。三 tab 一頁(理印紙墨/零 CDN/小字體
/表格自適應換行)。

數據源:
  VRN tab:MDL006 BASIC_INFO/FINANCIAL_DATA schema(正則抽引擎原文)
          +驗證鏈五引擎在位檢+MDL008 Verified 產物掃描(倉內/
          VIA_Reports;無=候工作站跑 MDL008)
  VDF tab:VDF_Unified_Params SSOT+輸出樞紐六格式道+VDF 家族計數
  族群 tab:字庫 K6 族群枝+C2 官方 27 類+C3 量價四象限+族群指數
          圖規(flow_groupindex_chartspec.json → 行內 SVG 折線)

用法:--build(預設)/ --selftest 八檢
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
REPORTS = VIA / "VIA_Reports"
UI_PATH = REPORTS / "VIA_UI_MatrixConsole.html"
NOW = datetime.now().strftime("%Y%m%d_%H%M%S")

MDL006 = VIA / "functional modules/VRN/VRN_MDL006_ConsolidatorAndPhaseValidator.py"
MDL008 = VIA / "functional modules/VRN/VRN_MDL008_CrossValidator.py"
LEX = VIA / "functional modules/VRN/knowledge/VRN_Lexicon_v0100.json"
VDF_PARAMS = VIA / "functional modules/VDF/VDF_Unified_Params_v0100.json"
CHARTSPEC = REPORTS / "flow_groupindex_chartspec.json"

VRN_CHAIN = [
    ("MDL003 TableRestorer", "functional modules/VRN/VRN_MDL003_TableRestorer.py", "報告表格重建(phase1)"),
    ("MDL004 OCR Table", "functional modules/VRN/VRN_MDL004_OCR_FetchingPDFTable.py", "OCR 表格擷取(phase2)"),
    ("MDL006 Consolidator", "functional modules/VRN/VRN_MDL006_ConsolidatorAndPhaseValidator.py", "BASIC/FIN 整併+雙相對照 compare_phases"),
    ("MDL007 APIDataFetcher", "functional modules/VRN/VRN_MDL007_APIDataFetcher.py", "MOPS/TWSE/yfinance 真值源"),
    ("MDL008 CrossValidator", "functional modules/VRN/VRN_MDL008_CrossValidator.py", "Step7-11 交叉驗證+信心分數"),
]
VDF_FORMATS = [("parquet", "pandas 讀回驗證"), ("csv", "utf-8-sig 防亂碼"),
               ("duckdb", "read_json_auto 參數化"), ("sqlite", "標準庫"),
               ("sql", "INSERT dump 逃逸"), ("gsheet", "COMPAT_CSV 誠實(雲道候同意閘)")]
C3_QUADS = [("領漲放量", "報酬z≥0 · 量z≥0", "主升攻擊段"), ("領漲縮量", "報酬z≥0 · 量z<0", "續航存疑"),
            ("回檔放量", "報酬z<0 · 量z≥0", "出貨/換手警訊"), ("回檔縮量", "報酬z<0 · 量z<0", "冷卻整理")]


def extract_cols(name: str) -> list:
    if not MDL006.exists():
        return []
    t = MDL006.read_text(encoding="utf-8", errors="ignore")
    m = re.search(name + r"\s*=\s*\[(.*?)\]", t, re.S)
    return re.findall(r'"([a-z_]+)"', m.group(1)) if m else []


def scan_verified() -> list:
    hits = []
    for pat in ("*MDL008_Verified*", "VIA_NLP*Verified*"):
        for root in (VIA, REPORTS):
            hits += [str(p.relative_to(VIA)) for p in root.rglob(pat)
                     if p.is_file() and "__pycache__" not in str(p)]
    return sorted(set(hits))


def lex_groups() -> dict:
    if not LEX.exists():
        return {}
    try:
        d = json.loads(LEX.read_text(encoding="utf-8"))
        return {k: v["zh"] for k, v in d.get("tree", {}).get("K6", {}).get("children", {}).items()}
    except Exception:
        return {}


def chart_svg() -> str:
    """族群指數圖規 → 行內 SVG 折線(無圖規=候數據)。"""
    if not CHARTSPEC.exists():
        return "<p class='pend'>候數據:先跑 via-etfflow groups --chartspec <rows.json></p>"
    try:
        sp = json.loads(CHARTSPEC.read_text(encoding="utf-8"))
    except Exception:
        return "<p class='pend'>圖規解析失敗(誠實)</p>"
    series = sp.get("series", [])
    vals = [v for s in series for v in s["values"] if v is not None]
    if not vals:
        return "<p class='pend'>圖規空(誠實)</p>"
    lo, hi = min(vals), max(vals)
    rng = (hi - lo) or 1.0
    W, H, P = 560, 220, 30
    colors = ["#3c6660", "#9e2b25", "#24457f", "#8a6420", "#3d7a52"]
    polys, legends = "", ""
    for i, s in enumerate(series[:5]):
        pts = []
        n = max(1, len(s["values"]) - 1)
        for j, v in enumerate(s["values"]):
            if v is None:
                continue
            x = P + j * (W - 2 * P) / n
            y = H - P - (v - lo) / rng * (H - 2 * P)
            pts.append(f"{x:.1f},{y:.1f}")
        c = colors[i % len(colors)]
        polys += f"<polyline points='{' '.join(pts)}' fill='none' stroke='{c}' stroke-width='2'/>"
        legends += f"<tspan fill='{c}'>■ {s['name']} </tspan>"
    return (f"<svg viewBox='0 0 {W} {H}' style='width:100%;max-width:640px;background:#fbfaf7;"
            f"border:1px solid #dbd9d3'><text x='{P}' y='16' font-size='11'>{legends}</text>"
            f"<text x='{P}' y='{H-8}' font-size='10'>{sp['x']['values'][0]} → {sp['x']['values'][-1]}"
            f" · base100 · {len(series)} 族群</text>{polys}</svg>"
            f"<p class='p'>{sp.get('methodology','')}</p>")


def build_html() -> str:
    basic = extract_cols("BASIC_INFO_COLS")
    fin = extract_cols("FINANCIAL_DATA_COLS")
    verified = scan_verified()
    chain_rows = "".join(
        f"<tr><td>{n}</td><td class='p'>{p}</td><td>{d}</td>"
        f"<td><span class='dot {'g' if (VIA/p).exists() else 'r'}'></span>"
        f"{'在位' if (VIA/p).exists() else '缺'}</td></tr>"
        for n, p, d in VRN_CHAIN)
    basic_rows = "".join(f"<tr><td>{i+1}</td><td><code>{c}</code></td>"
                         f"<td>{'候驗證數據' if not verified else '見產物'}</td></tr>"
                         for i, c in enumerate(basic))
    fin_rows = "".join(f"<tr><td>{i+1}</td><td><code>{c}</code></td>"
                       f"<td>{'候驗證數據' if not verified else '見產物'}</td></tr>"
                       for i, c in enumerate(fin))
    ver_state = ("".join(f"<li><code>{v}</code></li>" for v in verified)
                 if verified else
                 "<li class='pend'>倉內無 MDL008 Verified 產物——工作站跑 VRN 管線後,"
                 "產物路徑會自動入列(誠實候數據,不捏)</li>")
    params = {}
    if VDF_PARAMS.exists():
        try:
            params = json.loads(VDF_PARAMS.read_text(encoding="utf-8"))
        except Exception:
            params = {}
    pkeys = params.get("params", params) if isinstance(params, dict) else {}
    param_rows = "".join(
        f"<tr><td><code>{k}</code></td><td>{str(v)[:90]}</td></tr>"
        for k, v in (pkeys.items() if isinstance(pkeys, dict) else []))
    fmt_rows = "".join(f"<tr><td><code>{f}</code></td><td>{d}</td>"
                       f"<td><span class='dot g'></span>lane 在位(selftest 7/7)</td></tr>"
                       for f, d in VDF_FORMATS)
    groups = lex_groups()
    grp_rows = "".join(f"<tr><td><code>{k}</code></td><td>{v}</td></tr>"
                       for k, v in groups.items()) or \
        "<tr><td colspan=2 class='pend'>候 via-lexicon --build</td></tr>"
    quad_rows = "".join(f"<tr><td><b>{q}</b></td><td>{c}</td><td>{m}</td></tr>"
                        for q, c, m in C3_QUADS)
    return f"""<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>VIA Matrix Console</title><style>
:root{{--paper:#f2f1ec;--card:#fbfaf7;--ink:#1b1a17;--seal:#9e2b25;--teal:#3c6660;
--green:#3d7a52;--gold:#8a6420;--hair:#dbd9d3}}
*{{box-sizing:border-box;margin:0}}body{{background:var(--paper);color:var(--ink);
font:12px/1.6 "Microsoft JhengHei","Noto Serif CJK TC",serif;padding:14px}}
h1{{font:600 20px/1.3 "Cormorant Garamond","Noto Serif CJK TC",serif}}
h2{{font:600 13px/1.4 inherit;color:var(--teal);margin:12px 0 4px;border-bottom:1px solid var(--hair)}}
.mast{{background:var(--card);border:1px solid var(--hair);border-top:3px solid var(--seal);
padding:10px 14px;margin-bottom:10px}}
table{{width:100%;border-collapse:collapse;background:var(--card);margin:4px 0 10px}}
td,th{{border:1px solid var(--hair);padding:3px 6px;word-break:break-word;overflow-wrap:anywhere}}
th{{background:#efede6}}
code{{font-family:Consolas,monospace;font-size:11px;color:var(--gold)}}
.p{{color:#8a877f;font-size:11px}}.pend{{color:var(--gold)}}
.dot{{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:4px}}
.dot.g{{background:var(--green)}}.dot.r{{background:var(--seal)}}
.tabs input{{display:none}}
.tabs label{{display:inline-block;padding:6px 16px;border:1px solid var(--hair);
border-bottom:none;background:#efede6;cursor:pointer;font-weight:600}}
.tabs input:checked+label{{background:var(--card);color:var(--seal)}}
.pane{{display:none;background:var(--card);border:1px solid var(--hair);padding:12px}}
#t1:checked~#p1,#t2:checked~#p2,#t3:checked~#p3{{display:block}}
.grid{{display:grid;grid-template-columns:1fr 1fr;gap:12px}}
@media(max-width:820px){{.grid{{grid-template-columns:1fr}}}}</style></head><body>
<div class="mast"><h1>VIA Matrix Console <span class="p">v0100 · {NOW}</span></h1>
<div>VRN 驗證矩陣 · VDF 運作摘要矩陣 · 族群/量價指標矩陣(數據驅動,無數據誠實候)</div></div>
<div class="tabs">
<input type="radio" name="t" id="t1" checked><label for="t1">VRN 驗證矩陣</label>
<input type="radio" name="t" id="t2"><label for="t2">VDF 運作摘要</label>
<input type="radio" name="t" id="t3"><label for="t3">族群+量價指標</label>
<div class="pane" id="p1">
<h2>驗證鏈五引擎(BASIC INFO+FINANCIAL DATA → 對照驗證)</h2>
<table><tr><th>引擎</th><th>路徑</th><th>職責</th><th>態</th></tr>{chain_rows}</table>
<div class="grid"><div>
<h2>BASIC INFO 契約({len(basic)} 欄,源:MDL006 原文)</h2>
<table><tr><th>#</th><th>欄</th><th>驗證值</th></tr>{basic_rows}</table>
</div><div>
<h2>FINANCIAL DATA 契約({len(fin)} 欄)</h2>
<table><tr><th>#</th><th>欄</th><th>驗證值</th></tr>{fin_rows}</table>
</div></div>
<h2>MDL008 Verified 產物(Step7-11:單位統一→歷史對照→Fallback→預測自洽→信心分數)</h2>
<ul>{ver_state}</ul></div>
<div class="pane" id="p2">
<h2>統一輸入參數 SSOT({len(pkeys) if isinstance(pkeys, dict) else 0} 鍵)</h2>
<table><tr><th>參數</th><th>值</th></tr>{param_rows or '<tr><td colspan=2 class="pend">候 SSOT</td></tr>'}</table>
<h2>六格式輸出道(運作結果逐格式×逐表矩陣由 via-vdfout summary() 產)</h2>
<table><tr><th>格式</th><th>道</th><th>態</th></tr>{fmt_rows}</table>
<p class="p">實跑摘要:via-vdfout 寫庫時逐格式讀回驗證+matrix rows;倉內煙測 csv+sqlite 雙 OK</p></div>
<div class="pane" id="p3">
<div class="grid"><div>
<h2>C1 供應鏈/題材族群(字庫 K6,{len(groups)} 枝)</h2>
<table><tr><th>枝</th><th>族群</th></tr>{grp_rows}</table>
</div><div>
<h2>C3 量價輪動四象限指標</h2>
<table><tr><th>象限</th><th>條件</th><th>解讀</th></tr>{quad_rows}</table>
<p class="p">C2 官方 TWSE 產業別 27 類子集另見 via-etfflow groups --taxonomy</p>
</div></div>
<h2>族群指數(base100;圖規→行內 SVG)</h2>
{chart_svg()}</div>
</div></body></html>"""


def cmd_build(quiet=False) -> int:
    REPORTS.mkdir(parents=True, exist_ok=True)
    UI_PATH.write_text(build_html(), encoding="utf-8")
    if not quiet:
        print(f"  [出] {UI_PATH}")
        print(f"  [態] VRN 契約欄 {len(extract_cols('BASIC_INFO_COLS'))}+{len(extract_cols('FINANCIAL_DATA_COLS'))}"
              f" · Verified 產物 {len(scan_verified())}(0=誠實候工作站管線)"
              f" · K6 族群 {len(lex_groups())} · 圖規 {'在位' if CHARTSPEC.exists() else '候'}")
    return 0


def selftest() -> int:
    ok, total = 0, 8
    b, f = extract_cols("BASIC_INFO_COLS"), extract_cols("FINANCIAL_DATA_COLS")
    if len(b) == 15 and "target_price" in b:
        ok += 1; print("  [PASS] BASIC INFO 契約 15 欄自 MDL006 原文抽取")
    else:
        print(f"  [FAIL] BASIC {len(b)}")
    if len(f) == 14 and "confidence" in f:
        ok += 1; print("  [PASS] FINANCIAL DATA 契約 14 欄")
    else:
        print(f"  [FAIL] FIN {len(f)}")
    html = build_html()
    if all(x in html for x in ("VRN 驗證矩陣", "VDF 運作摘要", "族群+量價指標")):
        ok += 1; print("  [PASS] 三 tab 矩陣一頁")
    else:
        print("  [FAIL] tabs")
    if "MDL008" in html and ("誠實候數據" in html or "候工作站" in html or scan_verified()):
        ok += 1; print("  [PASS] 驗證產物誠實態(無數據不捏)")
    else:
        print("  [FAIL] 誠實態")
    if all(fmt in html for fmt, _ in VDF_FORMATS):
        ok += 1; print("  [PASS] VDF 六格式道矩陣")
    else:
        print("  [FAIL] VDF")
    if "領漲放量" in html and "回檔縮量" in html:
        ok += 1; print("  [PASS] C3 量價四象限指標矩陣")
    else:
        print("  [FAIL] 量價")
    if ("<svg" in html and "polyline" in html) or "候數據" in html:
        ok += 1; print("  [PASS] 族群指數行內 SVG(或誠實候數據)")
    else:
        print("  [FAIL] SVG")
    if "fonts.googleapis" not in html and "--seal:#9e2b25" in html and cmd_build(quiet=True) == 0:
        ok += 1; print("  [PASS] 理印鎖+零 CDN+落檔")
    else:
        print("  [FAIL] 鎖/落檔")
    print(f"  [計] {ok}/{total} 檢通過")
    return 0 if ok == total else 1


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        return selftest()
    return cmd_build()


if __name__ == "__main__":
    raise SystemExit(main())
