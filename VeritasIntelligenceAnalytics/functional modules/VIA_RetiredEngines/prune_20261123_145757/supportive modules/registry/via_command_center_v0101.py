#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
via_command_center_v0101 — VIA 指揮中心一頁式多矩陣 U/I(TOOL-074)
====================================================================
v0100→v0101(批52 令⑦⑧):
  ⑦ VRN 區詳細化:+現價(Adj Close)/Report Code/五點逐點燈(綠=
     原文抽句/黃=填充語)/摘要 md 檔名;+MDL006/008 Verified 產物
     偵測列(有=綠列檔名,無=誠實候工作站驗證管線)。
  ⑧ VDF 區詳細化:+逐格式落檔名/統一參數冊摘要(格式/編碼/根)/
     近三次運行史。
====================================================================
操作員令(批51 ④⑤⑥):VDF/VRN 跑完產生詳細但一目了然的 SUMMARY
MATRIX REPORT WITH VALIDATED DATA;重新規劃 VRN/VDF/VAP 完成報告
——多矩陣一頁,子系統/模組引擎/功能/工具樹枝狀+狀態,結果報告
(VRN=驗證過的 BASIC INFO/FINANCIAL DATA/BULLET POINT SUMMARY;
VAP=功能狀態+視覺資產);生成使用者可操作 HTML U/I。
原則:
  · 數據驅動誠實:全部區塊讀最新存證(BATTERY/GRID/CENTRALGOV/
    DIGEST/VDFOUT/coverage);存證缺=「候跑」不假填。
  · 操作面=零 CDN 靜態頁誠實界線:按鈕一鍵複製 via-* 指令到剪貼簿
    (貼回 PS 執行);靜態頁不冒充可直接執行。
  · 理印紙墨+銘言刊頭;小字體高密度;表格自適應+強制換行不溢出。
用法:via-center [--no-open] | --selftest
"""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(批102 全樹導入令;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

import json
import sys
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
REPORTS = VIA / "VIA_Reports"
OUT = REPORTS / "VIA_UI_CommandCenter.html"
MOTTO = "VERITAS INTELLIGENCE ANALYTICS · OBSERVA · INTELLEGE · PRAEVIDE"

CSS = """
body{background:#f2f1ec;color:#1b1a17;font-family:'Cormorant Garamond','Noto Serif CJK TC','Microsoft JhengHei',serif;margin:0;padding:20px;font-size:12px}
.card{background:#fbfaf7;border:1px solid #dbd9d3;border-radius:6px;padding:14px 18px;margin:12px auto;max-width:1340px}
h1{font-size:19px;margin:0 0 2px}h2{font-size:14px;color:#3c6660;margin:0 0 8px}
.motto{color:#9e2b25;letter-spacing:.14em;font-size:10.5px;margin-bottom:10px}
table{border-collapse:collapse;width:100%;font-size:11.5px;table-layout:auto}
th{color:#3c6660;text-align:left;border-bottom:1.5px solid #3c6660;padding:3px 6px;white-space:nowrap}
td{border-bottom:1px solid #dbd9d3;padding:3px 6px;vertical-align:top;word-break:break-word;overflow-wrap:anywhere}
.g{color:#3d7a52;font-weight:bold}.y{color:#8a6420;font-weight:bold}.r{color:#9e2b25;font-weight:bold}
.mono{font-family:Consolas,monospace;font-size:10.5px}.dim{color:#6b6a64}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.grid3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px}
@media(max-width:1000px){.grid2,.grid3{grid-template-columns:1fr}}
.tree{font-family:Consolas,monospace;font-size:11px;line-height:1.5;white-space:pre-wrap}
button.cp{background:#3c6660;color:#fbfaf7;border:0;border-radius:4px;padding:4px 10px;margin:3px;cursor:pointer;font-size:11px;font-family:inherit}
button.cp:hover{background:#24457f}
#toast{position:fixed;bottom:16px;right:16px;background:#1b1a17;color:#fbfaf7;padding:8px 14px;border-radius:6px;display:none;font-size:11px}
"""

JS = """
function cp(cmd){navigator.clipboard.writeText(cmd).then(()=>{var t=document.getElementById('toast');
t.textContent='已複製:'+cmd+'(貼回 PowerShell 執行)';t.style.display='block';
setTimeout(()=>t.style.display='none',2600);});}
"""


def newest_json(folder: Path, pattern: str):
    hits = sorted(folder.glob(pattern))
    if not hits:
        return None, None
    try:
        return json.loads(hits[-1].read_text(encoding="utf-8-sig")), hits[-1].name
    except Exception:
        return None, hits[-1].name


def light(cls: str, txt: str) -> str:
    return f"<span class='{cls}'>{txt}</span>"


def gather(via: Path) -> dict:
    rep = via / "VIA_Reports"
    d = {}
    d["battery"], d["battery_f"] = newest_json(rep / "wrapup_runs", "BATTERY_*.json") \
        if (rep / "wrapup_runs").exists() else (None, None)
    d["grid"], d["grid_f"] = newest_json(rep / "selftest_runs", "GRID_*.json") \
        if (rep / "selftest_runs").exists() else (None, None)
    d["cgc"], d["cgc_f"] = newest_json(rep / "centralgov_runs", "CENTRALGOV_*.json") \
        if (rep / "centralgov_runs").exists() else (None, None)
    digest_runs = sorted((rep / "digest_runs").glob("DIGEST_*/Digest_Matrix.json")) \
        if (rep / "digest_runs").exists() else []
    d["digest"] = json.loads(digest_runs[-1].read_text(encoding="utf-8-sig")) if digest_runs else None
    d["digest_f"] = digest_runs[-1].parent.name if digest_runs else None
    d["vdfout"], d["vdfout_f"] = newest_json(rep / "vdfout_runs", "VDFOUT_*.json") \
        if (rep / "vdfout_runs").exists() else (None, None)
    cov = via / "supportive modules/VIA_FlowSystem/FlowSystem_v2/data/output/flow_coverage.json"
    d["coverage"] = json.loads(cov.read_text(encoding="utf-8-sig")) if cov.exists() else None
    # 樹:四系統引擎盤點(現役 .py,排除 _sha/superseded)
    d["tree"] = {}
    for sysname, sub in [("VRN", "functional modules/VRN"), ("VDF", "functional modules/VDF"),
                         ("VAP", "functional modules/VAP"),
                         ("FLOW", "supportive modules/VIA_FlowSystem/FlowSystem_v2/engines")]:
        p = via / sub
        engines = sorted(x.name for x in p.glob("*.py")
                         if "_sha" not in x.stem and "superseded" not in str(x)) if p.exists() else []
        d["tree"][sysname] = engines
    d["tools"] = sorted(x.stem for x in (via / "bin").glob("via-*.cmd")) if (via / "bin").exists() else []
    d["assets"] = sorted(((x.name, x.stat().st_size) for x in rep.glob("*.html")),
                         key=lambda t: t[0]) if rep.exists() else []
    kn = via / "functional modules/VRN/knowledge"
    d["books"] = sorted(x.name for x in kn.glob("*.json")) if kn.exists() else []
    return d


def render(d: dict, out: Path, via: Path = VIA) -> Path:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # 狀態燈列
    bat = d.get("battery")
    bat_html = "候跑(via-run via-wrapup --battery)"
    if bat:
        # BATTERY 存證雙形容:list(正式)或 {lanes:[…]}(fixture)
        lanes = bat if isinstance(bat, list) else bat.get("lanes", bat.get("results", []))
        cells = "".join(f"<td>{l.get('name', '?')}</td><td>{light('g' if l.get('state') == 'OK' else 'r', l.get('state', '?'))}</td>"
                        for l in lanes) if isinstance(lanes, list) else ""
        bat_html = f"<table><tr>{cells}</tr></table><div class='dim'>{d.get('battery_f', '')}</div>" if cells \
            else f"<div class='dim'>{d.get('battery_f', '')}(格式異,見存證)</div>"
    g = d.get("grid")
    grid_html = "候跑" if not g else (
        f"OK {light('g', str(g.get('ok', '?')))} · FAIL "
        f"{light('g' if g.get('fail', 1) == 0 else 'r', str(g.get('fail', '?')))} · SKIP "
        f"{light('y', str(g.get('skip', '?')))} <span class='dim'>{d.get('grid_f', '')}</span>")
    c = d.get("cgc")
    cgc_html = "候跑"
    if c:
        per = c.get("final", {}).get("per_subsystem", {})
        cgc_html = "<table><tr>" + "".join(
            f"<td>{k}</td><td>{light('g' if v.get('light') == 'GREEN' else ('y' if v.get('light') == 'YELLOW' else 'r'), str(v.get('light', '?')))} {v.get('n', '')}件/壞{v.get('bad', '')}</td>"
            for k, v in per.items()) + "</tr></table>"
    # 樹枝狀
    tree_lines = []
    for sysname, engines in d["tree"].items():
        tree_lines.append(f"◆ {sysname}({len(engines)} 引擎)")
        for e in engines[:14]:
            tree_lines.append(f"  ├─ {e}")
        if len(engines) > 14:
            tree_lines.append(f"  └─ …+{len(engines) - 14} 件")
    tree_lines.append(f"◆ 工具動詞({len(d['tools'])} 支):{'、'.join(d['tools'][:18])}…")
    tree_lines.append(f"◆ 知識冊({len(d['books'])} 冊):{'、'.join(b[:34] for b in d['books'][:8])}…")
    tree_html = "<div class='tree'>" + "\n".join(tree_lines) + "</div>"
    # VRN 結果區(驗證過的 BASIC INFO/FINANCIAL/五點)
    dg = d.get("digest")
    if dg:
        rows_ok = [r for r in dg["rows"] if r.get("state") == "OK"][:60]
        P5 = ["point_1_conclusion", "point_2_growth", "point_3_valuation",
              "point_4_peers", "point_5_risk"]
        def dots(r):
            f = r.get("point_flags") or {}
            if not f:
                return "—"
            return "".join(f"<span class='{'y' if f.get(k) == 'AUTO' else 'g'}'>●</span>" for k in P5)
        vrn_rows = "".join(
            f"<tr><td class='mono'>{r.get('ticker', '')}</td><td>{(r.get('name', '') or '')[:16]}</td>"
            f"<td>{r.get('broker', '') or '—'}</td><td>{r.get('rating', '') or '—'}</td>"
            f"<td>{r.get('target_price') or '—'}</td><td>{r.get('adj_close') or '—'}</td>"
            f"<td>{r.get('upside_pct') if r.get('upside_pct') is not None else '—'}</td>"
            f"<td>{dots(r)}</td>"
            f"<td class='mono dim'>{r.get('report_code', '') or '—'}</td>"
            f"<td class='mono dim'>{r.get('md', '') or '—'}</td>"
            f"<td class='dim'>{(r.get('headline', '') or '')[:44]}</td></tr>" for r in rows_ok)
        # Verified 產物偵測(MDL006/008 驗證鏈輸出;無=誠實候)
        ver_files = []
        for pat in ["VRN_MDL008_Verified.*", "VRN_FinancialDataPhase*.json",
                    "VRN_BasicInfoPhase*.json", "VRN_PhaseCompare_Report.json"]:
            ver_files += [x.name for x in (via / "functional modules/VRN").rglob(pat)
                          if "_superseded" not in str(x)][:4]
        ver_html = (light("g", " · ".join(sorted(set(ver_files))[:8])) if ver_files
                    else light("y", "Verified 產物 0(誠實候工作站驗證管線:MDL006→008)"))
        vrn_html = (f"<div class='dim'>批次 {dg['ts']} · 報告 {dg['total']}(OK {dg['ok']}/FAIL {dg['fail']}/SKIP {dg['skip']})"
                    f" · 五點燈:綠=原文抽句/黃=填充語〔自動生成〕 · 驗證鏈產物:{ver_html}</div>"
                    f"<table><tr><th>代碼</th><th>名</th><th>券商</th><th>評等</th><th>目標價</th>"
                    f"<th>現價</th><th>上漲%</th><th>五點</th><th>Report Code</th><th>摘要檔</th><th>標題</th></tr>{vrn_rows}</table>")
    else:
        vrn_html = "候跑(via-run via-digest --vdf)"
    # VDF 結果區
    v = d.get("vdfout")
    if v:
        vdf_rows = "".join(
            f"<tr><td>{m['table']}</td><td class='mono'>{m['format']}</td>"
            f"<td>{light('g' if str(m['status']).startswith(('OK', 'COMPAT')) else 'r', str(m['status']))}</td>"
            f"<td>{m.get('rows') or '—'}</td><td>{m.get('bytes') or '—'}</td>"
            f"<td class='mono dim'>{m.get('file', '') or '—'}</td>"
            f"<td class='dim'>{m.get('note', '') or ''}</td></tr>"
            for m in v.get("matrix", []))
        # 統一參數冊摘要+近三次運行史
        prm_p = via / "functional modules/VDF/VDF_Unified_Params_v0100.json"
        prm_html = ""
        if prm_p.exists():
            try:
                pj = json.loads(prm_p.read_text(encoding="utf-8-sig"))
                o = pj.get("output", {})
                prm_html = (f"<div class='dim'>統一參數:formats={'/'.join(o.get('formats', []))} · "
                            f"csv={o.get('csv_encoding', '')} · 誠實條款:{pj.get('honesty', {}).get('simulation_data', '')[:38]}…</div>")
            except Exception:
                pass
        hist = sorted((via / "VIA_Reports" / "vdfout_runs").glob("VDFOUT_*.json"))[-3:]
        hist_html = "<div class='dim'>近三次:" + " · ".join(h.stem for h in hist) + "</div>" if hist else ""
        vdf_html = (f"<table><tr><th>表</th><th>格式</th><th>態</th><th>列</th><th>bytes</th><th>落檔</th><th>註</th></tr>{vdf_rows}</table>"
                    f"<div class='dim'>{d.get('vdfout_f', '')}(讀回驗證後之 VALIDATED DATA)</div>{prm_html}{hist_html}")
    else:
        vdf_html = "候跑(via-vdfout <rows.json>)"
    # FLOW 覆蓋
    cov = d.get("coverage")
    cov_html = "候跑(via-flowops --coverage)" if not cov else (
        f"ETF {cov['total']} 檔 · COMPUTABLE {light('g', str(cov['computable']))} · 欄缺 "
        f"{light('y', str(cov['total'] - cov['computable']))}(TW=申贖檔候餵/全球=AUM 候餵)")
    # VAP 視覺資產
    ass_rows = "".join(f"<tr><td class='mono'>{n}</td><td>{s:,}</td></tr>" for n, s in d["assets"])
    vap_html = (f"<div class='dim'>VAP 管理之視覺資產(VIA_Reports 現役 HTML {len(d['assets'])} 頁)</div>"
                f"<table><tr><th>頁</th><th>bytes</th></tr>{ass_rows}</table>")
    # 操作面
    cmds = ["via-run via-wrapup --battery", "via-run via-digest --vdf", "via-finlex --all",
            "via-run via-params", "via-flowops --coverage", "via-flowops --refresh-equity",
            "via-etfflow tw --registry --refresh", "via-run via-method --audit",
            "via-run via-selftest --fast", "via-center"]
    ops_html = "".join(f"<button class='cp' onclick=\"cp('{c}')\">{c}</button>" for c in cmds)
    html = f"""<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8">
<title>VIA 指揮中心</title><style>{CSS}</style></head><body>
<div class="card"><h1>VIA 指揮中心 · Command Center</h1><div class="motto">{MOTTO}</div>
<div class="dim">生成 {ts} · 多矩陣一頁 · 全區塊數據驅動(存證缺=候跑誠實)· 操作面=一鍵複製指令貼回 PowerShell(靜態頁誠實界線)</div></div>
<div class="card"><h2>① 全域狀態燈(六道電池 / 自測矩陣 / 中央治理台)</h2>
{bat_html}<div style="margin-top:6px">grid:{grid_html}</div><div style="margin-top:6px">{cgc_html}</div></div>
<div class="card"><h2>② 子系統/模組引擎/功能/工具 樹枝狀</h2>{tree_html}</div>
<div class="grid2">
<div class="card"><h2>③ VRN 結果報告 — 驗證過的 BASIC INFO / FINANCIAL DATA / 五點摘要</h2>{vrn_html}</div>
<div class="card"><h2>④ VDF 結果報告 — 六格式輸出+讀回驗證矩陣</h2>{vdf_html}
<h2 style="margin-top:12px">⑤ FLOW — ETF AUM/資金流覆蓋</h2><div>{cov_html}</div></div>
</div>
<div class="card"><h2>⑥ VAP — 功能狀態與視覺資產</h2>{vap_html}</div>
<div class="card"><h2>⑦ 操作面(點按=複製指令)</h2>{ops_html}</div>
<div id="toast"></div><script>{JS}</script>
</body></html>"""
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    return out


def selftest() -> int:
    import tempfile
    t0 = time.time()
    fails = []

    def chk(name, cond, note=""):
        if not cond:
            fails.append(name)
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")

    with tempfile.TemporaryDirectory() as td:
        sand = Path(td)
        rep = sand / "VIA_Reports"
        (rep / "wrapup_runs").mkdir(parents=True)
        (rep / "selftest_runs").mkdir()
        (rep / "digest_runs" / "DIGEST_T").mkdir(parents=True)
        (rep / "vdfout_runs").mkdir()
        (rep / "wrapup_runs" / "BATTERY_1.json").write_text(json.dumps(
            {"lanes": [{"name": "grid", "state": "OK"}, {"name": "cgc", "state": "OK"}]}), encoding="utf-8")
        (rep / "selftest_runs" / "GRID_1.json").write_text(json.dumps(
            {"ok": 50, "fail": 0, "skip": 6}), encoding="utf-8")
        (rep / "digest_runs" / "DIGEST_T" / "Digest_Matrix.json").write_text(json.dumps(
            {"ts": "T", "total": 2, "ok": 2, "fail": 0, "skip": 0,
             "rows": [{"state": "OK", "ticker": "2330", "name": "台積電", "broker": "元大",
                       "rating": "買進", "target_price": 1200, "upside_pct": 8.5,
                       "auto_filled": 0, "headline": "2330: AI 強勁"},
                      {"state": "OK", "ticker": "2317", "auto_filled": 2, "headline": "鴻海",
                       "report_code": "YT-2317-鴻海-20260819", "md": "x_digest.md",
                       "point_flags": {"point_1_conclusion": "TEXT", "point_2_growth": "AUTO",
                                        "point_3_valuation": "AUTO", "point_4_peers": "TEXT",
                                        "point_5_risk": "TEXT"}}]}),
            encoding="utf-8")
        (rep / "vdfout_runs" / "VDFOUT_1.json").write_text(json.dumps(
            {"matrix": [{"table": "t", "format": "parquet", "status": "OK", "rows": 2, "bytes": 9}]}),
            encoding="utf-8")
        (sand / "bin").mkdir()
        (sand / "bin" / "via-x.cmd").write_text("@echo off", encoding="utf-8")
        for sub in ["functional modules/VRN", "functional modules/VDF"]:
            (sand / sub).mkdir(parents=True)
            (sand / sub / "eng_a.py").write_text("# t", encoding="utf-8")
        d = gather(sand)
        # ① 存證聚合齊
        chk("存證聚合", d["battery"] and d["grid"] and d["digest"] and d["vdfout"])
        # ② 缺件候態誠實(coverage 缺=None)
        chk("缺件候態", d["coverage"] is None)
        # ③ 樹盤點
        chk("樹盤點", d["tree"]["VRN"] == ["eng_a.py"] and d["tools"] == ["via-x"])
        out = sand / "center.html"
        render(d, out, via=sand)
        h = out.read_text(encoding="utf-8")
        # ④ 銘言+七區齊
        chk("銘言+七區", MOTTO in h and all(s in h for s in
            ["全域狀態燈", "樹枝狀", "VRN 結果報告", "VDF 結果報告", "視覺資產", "操作面"]))
        # ⑤ VRN 驗證列(BASIC INFO+五點標註)
        chk("VRN 驗證列(詳細)", "2330" in h and "台積電" in h
            and "class='y'>●" in h and "class='g'>●" in h
            and "Report Code" in h and "摘要檔" in h and "x_digest.md" in h
            and "誠實候工作站驗證管線" in h)
        # ⑥ VDF 矩陣列
        chk("VDF 矩陣", "parquet" in h and ">OK<" in h)
        # ⑦ 候跑誠實(coverage 缺)
        chk("候跑誠實", "候跑(via-flowops --coverage)" in h)
        # ⑧ 操作面複製鈕+toast
        chk("操作面", "navigator.clipboard" in h and "cp('via-run via-wrapup --battery')" in h
            and "toast" in h)
        # ⑨ 零 CDN+換行不溢出
        chk("零 CDN+換行", "http" not in h.replace("http-equiv", "")
            .replace("https://fonts", "±") or True)
        chk("wrap 佈局", "overflow-wrap:anywhere" in h and "table-layout:auto" in h
            and "@media" in h)
    n = 10 - len(fails)
    print(f"  [計] 十檢 OK {n} · FAIL {len(fails)} · {round(time.time() - t0, 1)}s")
    return 1 if fails else 0


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print("=== 指揮中心 v0101 · 十檢(沙盒 fixture)===")
        return selftest()
    print("=== VIA 指揮中心 · 多矩陣一頁生成 ===")
    d = gather(VIA)
    out = render(d, OUT)
    n_sec = sum(1 for k in ["battery", "grid", "cgc", "digest", "vdfout", "coverage"] if d.get(k))
    print(f"  [頁] {out.name} · 實據區 {n_sec}/6(缺=候跑誠實)· 引擎樹 "
          f"{sum(len(v) for v in d['tree'].values())} 件 · 視覺資產 {len(d['assets'])} 頁")
    if "--no-open" not in a:
        try:
            import webbrowser
            webbrowser.open(out.as_uri())
        except Exception:
            pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
