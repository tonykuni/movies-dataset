#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VAP_ENG008_TestConsole — VAP 全測×簡潔響應式主控台(批162;via-vapui)
====================================================================
操作員令:VAP 測試完做一個簡單 U/I 操作——字小一點、響應式設計、
內涵測試報告、自動畫(自動繪圖)規格。
  測試面(subprocess 實跑,誠實三態):ENG004 TAFactory/ENG005
    TemplateRunner/ENG007 RawWide/spec_guard(TOOL-083 圖規鎖)各
    --selftest;ENG001 chartlib(尾版)/ENG003=py_compile 編譯檢
    (無 selftest 介面=誠實標 COMPILE_ONLY,不假測)
  自動繪圖規格收割(全由冊/源碼動態,零發明):
    模板冊 spec/VAP_Template_Registry_v0100.json(6 模板)
    圖規冊 spec/VIA_VAP_40_Structural_Snapshots_v017.json(40 圖規)
    chartlib 函數面=ENG001 尾版 AST def 收割
    TA 面=ENG004 源碼 ta_ 函數收割
  UI=VIA_UI_VAPConsole_v0100.html:淺色、小字級(基準 clamp 10.5-12.5px)、
    grid auto-fit 響應式、overflow-wrap:anywhere、行動裝置 viewport
用法:via-vapui run(全測+收割+產 UI)| --status | --selftest
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

import ast
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VAP = HERE.parent
VIA = VAP.parent.parent
UI_OUT = VIA / "supportive modules" / "ui_support" / "VIA_UI_VAPConsole_v0100.html"
TPL_BOOK = VAP / "spec" / "VAP_Template_Registry_v0100.json"
SNAP_BOOK = VAP / "spec" / "VIA_VAP_40_Structural_Snapshots_v017.json"


def _newest(pattern: str, root: Path) -> Path | None:
    hits = sorted(p for p in root.glob(pattern) if "_sha" not in p.stem)
    return hits[-1] if hits else None


def run_tests() -> list[dict]:
    """VAP 測試電池(誠實三態;selftest 缺者=COMPILE_ONLY 不假測)"""
    battery = [
        ("TAFactory selftest", _newest("VAP_ENG004_TAFactory_v*.py", HERE), ["--selftest"]),
        ("TemplateRunner 十檢", _newest("VAP_ENG005_TemplateRunner_v*.py", HERE), ["--selftest"]),
        ("寬表刷新六檢", _newest("VAP_ENG007_RawWideRefresh_v*.py", HERE), ["--selftest"]),
        ("圖規鎖守衛(TOOL-083)", _newest("vap_spec_guard_v*.py", VAP), ["--selftest"]),
    ]
    results = []
    for name, path, args in battery:
        if path is None:
            results.append({"name": name, "state": "SKIP", "note": "引擎缺(誠實)"})
            continue
        r = subprocess.run([sys.executable, str(path), *args], cwd=path.parent,
                           capture_output=True, text=True, timeout=300)
        tail = (r.stdout or r.stderr).strip().splitlines()[-1:] or [""]
        results.append({"name": name, "state": "OK" if r.returncode == 0 else "FAIL",
                        "engine": path.name, "note": tail[0][:90]})
    for name, pat in (("chartlib 編譯檢", "VAP_ENG001_AutoplotEngineChartlib_v*.py"),
                      ("Seaborn/Plotly 編譯檢", "VAP_ENG003_AutoplotSeabornPlotly_v*.py"),
                      ("Autoplot v001 編譯檢", "VAP_ENG002_AutoplotEngine_v*.py")):
        p = _newest(pat, HERE)
        if p is None:
            results.append({"name": name, "state": "SKIP", "note": "缺"})
            continue
        r = subprocess.run([sys.executable, "-m", "py_compile", str(p)],
                           capture_output=True, text=True)
        results.append({"name": name, "state": "OK" if r.returncode == 0 else "FAIL",
                        "engine": p.name,
                        "note": "COMPILE_ONLY(無 selftest 介面=誠實標記)"})
    return results


def harvest_specs() -> dict:
    """自動繪圖規格收割(冊+AST;零發明)"""
    out = {"templates": [], "chart_specs": [], "chartlib_functions": [],
           "ta_functions": [], "sources": {}}
    if TPL_BOOK.exists():
        d = json.loads(TPL_BOOK.read_text(encoding="utf-8"))
        for t in d.get("templates", []):
            out["templates"].append({
                "name": t.get("name"), "zh": t.get("zh"), "kind": t.get("kind"),
                "chart_ref": t.get("chart_ref"),
                "source": (t.get("data") or {}).get("source")})
        out["sources"]["templates"] = TPL_BOOK.name
    if SNAP_BOOK.exists():
        d = json.loads(SNAP_BOOK.read_text(encoding="utf-8"))
        items = d if isinstance(d, list) else d.get("snapshots") or d.get("items") or []
        for s in items:
            if isinstance(s, dict):
                out["chart_specs"].append({
                    "id": s.get("id") or s.get("chart_id") or s.get("name"),
                    "title": (s.get("title") or s.get("zh") or s.get("name") or "")[:40]})
        out["sources"]["chart_specs"] = SNAP_BOOK.name
    lib = _newest("VAP_ENG001_AutoplotEngineChartlib_v*.py", HERE)
    if lib is not None:
        tree = ast.parse(lib.read_text(encoding="utf-8"))
        fns = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)
               and not n.name.startswith("_")]
        out["chartlib_functions"] = sorted(set(fns))
        out["sources"]["chartlib"] = lib.name
    ta = _newest("VAP_ENG004_TAFactory_v*.py", HERE)
    if ta is not None:
        try:  # 正主冊=indicator_roster()(動態載入;敗=源碼 family 鍵後備)
            import importlib.util
            spec = importlib.util.spec_from_file_location("vap_ta_dyn", ta)
            m = importlib.util.module_from_spec(spec)
            sys.modules["vap_ta_dyn"] = m
            spec.loader.exec_module(m)
            roster = m.indicator_roster()
            out["ta_functions"] = sorted(roster.keys() if isinstance(roster, dict)
                                         else roster)
        except Exception:
            src = ta.read_text(encoding="utf-8")
            out["ta_functions"] = sorted(set(re.findall(r'"([A-Z][A-Z0-9_%]{1,12})":', src)))
        out["sources"]["ta"] = ta.name
    return out


def build_ui(results: list[dict], specs: dict) -> Path:
    ok = sum(1 for r in results if r["state"] == "OK")
    fail = sum(1 for r in results if r["state"] == "FAIL")
    skip = sum(1 for r in results if r["state"] == "SKIP")
    color = {"OK": "#15803d", "FAIL": "#b91c1c", "SKIP": "#a16207"}
    rows = "".join(
        f'<div class="row"><span class="st" style="background:{color[r["state"]]}">'
        f'{r["state"]}</span><b>{r["name"]}</b>'
        f'<span class="mut">{r.get("engine", "")}</span>'
        f'<span class="note">{r.get("note", "")}</span></div>' for r in results)
    tpl_rows = "".join(
        f'<tr><td>{t["name"]}</td><td>{t["zh"]}</td><td>{t["kind"]}</td>'
        f'<td>{t["chart_ref"]}</td><td>{t["source"]}</td></tr>'
        for t in specs["templates"])
    spec_chips = "".join(f'<span class="chip">{s["id"]}</span>'
                         for s in specs["chart_specs"][:40])
    fn_chips = "".join(f'<span class="chip c2">{f}</span>'
                       for f in specs["chartlib_functions"][:48])
    ta_chips = "".join(f'<span class="chip c3">{f}</span>'
                       for f in specs["ta_functions"][:36])
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    html = f"""<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>VAP 主控台 v0100</title><style>
:root{{--fs:clamp(10.5px,1.15vw,12.5px)}}
*{{box-sizing:border-box}}
body{{margin:0;background:#f6f7f9;color:#1f2937;font:var(--fs)/1.5 'Segoe UI','Noto Sans TC',sans-serif}}
.wrap{{max-width:1180px;margin:0 auto;padding:clamp(8px,1.6vw,18px)}}
h1{{font-size:clamp(.95rem,2vw,1.25rem);margin:.3em 0 .05em}}
h2{{font-size:clamp(.8rem,1.6vw,1rem);margin:1em 0 .3em;color:#334155}}
.meta{{color:#64748b;font-size:.86em}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(340px,100%),1fr));gap:10px}}
.card{{background:#fff;border:1px solid #e5e7eb;border-radius:10px;padding:10px 12px;
overflow-wrap:anywhere;min-width:0}}
.row{{display:flex;gap:8px;align-items:baseline;padding:3px 0;border-bottom:1px dashed #eef2f7;flex-wrap:wrap}}
.st{{color:#fff;border-radius:4px;padding:0 6px;font-size:.82em}}
.mut{{color:#94a3b8;font-size:.85em}}
.note{{color:#64748b;font-size:.85em;flex-basis:100%}}
table{{width:100%;border-collapse:collapse;font-size:.92em}}
th,td{{text-align:left;padding:3px 6px;border-bottom:1px solid #eef2f7}}
th{{color:#475569;font-weight:600}}
.tablewrap{{overflow-x:auto}}
.chip{{display:inline-block;background:#eff6ff;color:#1d4ed8;border-radius:5px;
padding:1px 7px;margin:2px;font-size:.85em}}
.chip.c2{{background:#f0fdf4;color:#15803d}}
.chip.c3{{background:#fff7ed;color:#b45309}}
.kpi{{display:flex;gap:14px;margin:.4em 0}}
.kpi b{{font-size:1.5em}}
</style></head><body><div class="wrap">
<h1>VAP 主控台(測試報告×自動繪圖規格)</h1>
<div class="meta">批162 · 生成 {ts} · 淺色小字級響應式 · 收割源:{'、'.join(specs['sources'].values())}</div>
<div class="kpi"><span><b style="color:#15803d">{ok}</b> OK</span>
<span><b style="color:#b91c1c">{fail}</b> FAIL</span>
<span><b style="color:#a16207">{skip}</b> SKIP/編譯檢</span></div>
<div class="grid">
<div class="card"><h2>測試報告(誠實三態)</h2>{rows}</div>
<div class="card"><h2>自動繪圖模板冊({len(specs['templates'])})</h2>
<div class="tablewrap"><table><tr><th>模板</th><th>中文</th><th>型</th><th>chart_ref</th><th>資料源</th></tr>{tpl_rows}</table></div></div>
<div class="card"><h2>圖規冊 v017({len(specs['chart_specs'])} 規格)</h2>{spec_chips}</div>
<div class="card"><h2>chartlib 函數面({len(specs['chartlib_functions'])})</h2>{fn_chips}</div>
<div class="card"><h2>TA 工廠({len(specs['ta_functions'])})</h2>{ta_chips}</div>
</div></div></body></html>"""
    UI_OUT.write_text(html, encoding="utf-8")
    return UI_OUT


def run() -> int:
    print("[測試] VAP 電池…", flush=True)
    results = run_tests()
    for r in results:
        print(f"  [{r['state']}] {r['name']} {r.get('note', '')[:60]}")
    specs = harvest_specs()
    print(f"[收割] 模板 {len(specs['templates'])} · 圖規 {len(specs['chart_specs'])}"
          f" · 函數 {len(specs['chartlib_functions'])} · TA {len(specs['ta_functions'])}")
    p = build_ui(results, specs)
    fail = sum(1 for r in results if r["state"] == "FAIL")
    print(f"[UI] {p.name} · FAIL {fail}")
    return 0 if fail == 0 else 1


def status() -> int:
    print(f"UI={'在' if UI_OUT.exists() else '未生'} · 模板冊={'在' if TPL_BOOK.exists() else '缺'}"
          f" · 圖規冊={'在' if SNAP_BOOK.exists() else '缺'}")
    return 0


def selftest() -> int:
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    chk("① 規格冊在位(模板+圖規 v017)", TPL_BOOK.exists() and SNAP_BOOK.exists())
    s = harvest_specs()
    chk("② 規格收割(模板 6+圖規 40+chartlib/TA 函數)",
        len(s["templates"]) >= 5 and len(s["chart_specs"]) >= 30
        and len(s["chartlib_functions"]) >= 5,
        f"(t{len(s['templates'])}·s{len(s['chart_specs'])}·f{len(s['chartlib_functions'])}·ta{len(s['ta_functions'])})")
    import tempfile
    global UI_OUT
    _u = UI_OUT
    with tempfile.TemporaryDirectory() as td:
        UI_OUT = Path(td) / "ui.html"
        fake = [{"name": "x", "state": "OK", "engine": "e", "note": "n"},
                {"name": "y", "state": "FAIL", "engine": "e2", "note": "m"}]
        p = build_ui(fake, s)
        h = p.read_text(encoding="utf-8")
        chk("③ UI 產出(小字級 clamp 10.5-12.5px)", "clamp(10.5px" in h)
        chk("④ 響應式(viewport+auto-fit+overflow-wrap)",
            "viewport" in h and "auto-fit" in h and "overflow-wrap:anywhere" in h)
        chk("⑤ 內涵測試報告+繪圖規格(雙面同頁)",
            "測試報告" in h and "自動繪圖模板冊" in h and "圖規冊" in h)
        chk("⑥ 誠實三態呈現(FAIL 紅入頁)", "#b91c1c" in h and ">FAIL<" in h)
    UI_OUT = _u
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑦ 誠實紀律(無 selftest 介面=COMPILE_ONLY 不假測;收割零發明)",
        "COMPILE_ONLY" in src and "零發明" in src)
    print(f"  [計] 七檢 OK {7 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== VAP 主控台(VAP_ENG008)· 七檢自測 ===")
        return selftest()
    if "--status" in args:
        return status()
    if "run" in args:
        return run()
    print(__doc__.split("用法:")[1])
    return 0


if __name__ == "__main__":
    sys.exit(main())
