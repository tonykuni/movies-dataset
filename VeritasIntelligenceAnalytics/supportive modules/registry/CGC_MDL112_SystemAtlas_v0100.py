#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CGC_MDL112_SystemAtlas — VIA 系統現況總圖(批280;操作員令)
====================================================================
操作員令:「刪除所有 HTML U/I 重新規劃——VIA 應該充分顯示現況
SUBSYSTEM / MODULE / ENGINE / SSOT AND OTHER FUNCTIONS」。
重新規劃律:
  ①本頁=新總 U/I 主畫面:六區現況全譜,全檔案樹+冊真掃零發明
    (SUBSYSTEM 子系統/ENGINE 引擎尾版/MODULE 治理模組/SSOT 冊/
     FUNCTIONS 短令+任務/OTHER 頁面+測試現況)
  ②「刪除」=讓位道(平台鐵律只增不減):物理刪檔會被日更引擎
    重生=假刪除;正解=本頁上位為主畫面+舊頁降役為區內連結,
    陳舊非再生頁另批讓位 _retired 夾存證
  ③視覺=b258 鎖定 tokens;零 CDN;手機單欄自適應
用法:python3 CGC_MDL112_SystemAtlas_v0100.py [--print] | --selftest
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

import html
import importlib.util
import json
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
FM = VIA / "functional modules"
UIDIR = VIA / "supportive modules" / "ui_support"
OUT = UIDIR / "VIA_UI_SystemAtlas_v0100.html"
VER_RX = re.compile(r"_v\d+(?:\.py)?$")


def _fam(files) -> dict:
    """檔→族(去 _vNNNN)取尾版"""
    fam: dict = {}
    for f in sorted(files):
        fam[VER_RX.sub("", f.stem)] = f.name
    return fam


def gather() -> dict:
    subs = []
    engines: dict = {}
    for d in sorted(FM.iterdir()):
        if not d.is_dir():
            continue
        pys = list(d.rglob("*.py"))
        eng = _fam(p for p in pys
                   if re.search(r"_ENG\d+|^flow_", p.stem))
        if pys:
            subs.append({"name": d.name, "py": len(pys),
                         "engines": len(eng)})
            if eng:
                engines[d.name] = eng
    mods = _fam(HERE.glob("CGC_MDL*.py"))
    ssot = [{"name": f.name, "kb": f.stat().st_size // 1024}
            for f in sorted(HERE.glob("*.json"))
            if f.stat().st_size > 200]
    verbs = []
    reg = sorted(VIA.glob("Register-VIA-Commands-v*.ps1"))
    if reg:
        verbs = re.findall(r"function global:([a-z-]+)",
                           reg[-1].read_text(encoding="utf-8"))
    tasks = {}
    try:
        deck = sorted(HERE.glob("CGC_MDL095_DeckServer_v*.py"))[-1]
        spec = importlib.util.spec_from_file_location("m95a", deck)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        tasks = {k: v["zh"] for k, v in m.task_registry().items()}
    except Exception:
        pass                                   # 誠實:任務冊載入敗=空列
    pages = _fam(UIDIR.glob("VIA_UI_*.html"))
    grid = None
    hits = sorted((VIA / "VIA_Reports").rglob("GRID_*.json"))
    if hits:
        rows = json.loads(hits[-1].read_text(encoding="utf-8"))
        rows = rows if isinstance(rows, list) else \
            rows.get("results") or rows.get("rows") or list(rows.values())[0]
        grid = {"n": len(rows), "src": hits[-1].name,
                "fail": sum(1 for r in rows if str(r.get("state", ""))
                            .upper().startswith("FAIL"))}
    led = 0
    regj = HERE / "VIA_AutoCode_Registry_v0100.json"
    if regj.exists():
        led = len(json.loads(regj.read_text(encoding="utf-8"))
                  .get("ledger", []))
    return {"ts": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "subs": subs, "engines": engines, "mods": mods,
            "ssot": ssot, "verbs": verbs, "tasks": tasks,
            "pages": pages, "grid": grid, "ledger": led}


def render(d: dict) -> str:
    def sec(sid, title, body):
        return (f'<section id="{sid}"><h2>{title}</h2>{body}</section>')

    subs_rows = "".join(
        f"<tr><td>{html.escape(s['name'])}</td><td>{s['engines']}</td>"
        f"<td>{s['py']}</td></tr>" for s in d["subs"])
    eng_blocks = "".join(
        f"<details><summary><b>{html.escape(sub)}</b>"
        f"<span class='tag'>{len(fam)} 引擎族</span></summary><p>"
        + " ".join(f"<code>{html.escape(b)}</code>"
                   for b in sorted(fam)) + "</p></details>"
        for sub, fam in d["engines"].items())
    mods_list = " ".join(f"<code>{html.escape(b)}</code>"
                         for b in sorted(d["mods"]))
    ssot_rows = "".join(
        f"<tr><td>{html.escape(s['name'])}</td><td>{s['kb']} KB</td></tr>"
        for s in d["ssot"])
    verbs = " ".join(f"<code>{html.escape(v)}</code>" for v in d["verbs"])
    tasks = "".join(f"<tr><td><code>{html.escape(k)}</code></td>"
                    f"<td>{html.escape(z)}</td></tr>"
                    for k, z in d["tasks"].items())
    pages = " · ".join(
        f'<a href="{f}" style="color:var(--blue)">{html.escape(b[7:])}</a>'
        for b, f in sorted(d["pages"].items()))
    g = d["grid"]
    return f"""<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>VIA 系統現況總圖</title><style>
:root{{--bg:#f3f5f7;--panel:#fff;--line:#dce2e8;--text:#1f2933;
--muted:#6b7785;--blue:#4c78a8;--green:#5a9e6f;--navw:250px}}
@media (prefers-color-scheme: dark){{:root{{--bg:#10151b;--panel:#171e26;
--line:#2a333d;--text:#dbe3ea;--muted:#8a97a5;--blue:#7ba3cc;
--green:#79b58c}}}}
*{{box-sizing:border-box;margin:0}}
body{{background:var(--bg);color:var(--text);
font:12.5px/1.55 "Segoe UI","Noto Sans TC",sans-serif}}
.app{{display:grid;grid-template-columns:var(--navw) 1fr;
min-height:100vh}}
aside{{background:var(--panel);border-right:1px solid var(--line);
padding:14px 10px;position:sticky;top:0;height:100vh}}
h1{{font-size:14px;padding:0 7px 2px}}
.sub{{color:var(--muted);font-size:10px;padding:0 7px 10px}}
.nav-btn{{display:block;width:100%;text-align:left;border:1px solid
transparent;background:none;border-radius:8px;padding:7px 9px;
margin-bottom:2px;color:var(--text);font-size:12.5px;
text-decoration:none}}
.nav-btn:hover{{background:#edf3f8;color:var(--blue)}}
main{{padding:14px;display:grid;gap:14px}}
section{{background:var(--panel);border:1px solid var(--line);
border-radius:10px;padding:12px}}
h2{{font-size:11px;color:var(--muted);font-weight:800;
letter-spacing:.08em;text-transform:uppercase;padding-bottom:8px}}
table{{width:100%;border-collapse:collapse}}
td,th{{padding:5px 8px;border-bottom:1px solid var(--line);
text-align:left;font-variant-numeric:tabular-nums;
overflow-wrap:anywhere}}
th{{font-size:10px;color:var(--muted)}}
code{{color:var(--blue);font-size:10.5px}}
details{{padding:4px 0}}summary{{cursor:pointer}}
.tag{{float:right;font-size:9px;border-radius:999px;padding:1px 7px;
background:var(--line);color:var(--muted)}}
.kpis{{display:grid;grid-template-columns:repeat(4,1fr);gap:8px}}
.kpi{{border:1px solid var(--line);border-radius:8px;padding:8px;
border-left:3px solid var(--green)}}
.kpi b{{font-size:18px}}
.kpi small{{display:block;color:var(--muted)}}
@media(max-width:900px){{.app{{grid-template-columns:1fr}}
aside{{position:static;height:auto;border-right:0;
border-bottom:1px solid var(--line)}}
.kpis{{grid-template-columns:1fr 1fr}}}}</style></head><body>
<div class="app"><aside>
<h1>VIA 系統現況總圖</h1>
<div class="sub">{d['ts']} · 批280 重新規劃主畫面 · 全樹真掃零發明</div>
<a class="nav-btn" href="#sub">▤ SUBSYSTEM 子系統</a>
<a class="nav-btn" href="#eng">⚙ ENGINE 引擎</a>
<a class="nav-btn" href="#mod">▦ MODULE 治理模組</a>
<a class="nav-btn" href="#ssot">◇ SSOT 冊</a>
<a class="nav-btn" href="#fn">⌘ FUNCTIONS 功能</a>
<a class="nav-btn" href="#other">▧ OTHER 頁面·測試</a>
</aside><main>
{sec("kpi", "現況總榜", f'''<div class="kpis">
<div class="kpi"><b>{len(d["subs"])}</b><small>子系統</small></div>
<div class="kpi"><b>{sum(len(v) for v in d["engines"].values())}</b>
<small>引擎族(尾版)</small></div>
<div class="kpi"><b>{len(d["mods"])}</b><small>治理模組族</small></div>
<div class="kpi"><b>{d["ledger"]}</b><small>台帳筆(append-only)</small>
</div></div>''')}
{sec("sub", "SUBSYSTEM · 子系統", '<table><tr><th>子系統</th>'
     '<th>引擎族</th><th>py 檔</th></tr>' + subs_rows + '</table>')}
{sec("eng", "ENGINE · 引擎尾版族(點開展列)", eng_blocks)}
{sec("mod", f"MODULE · 治理模組(CGC_MDL {len(d['mods'])} 族)",
     "<p>" + mods_list + "</p>")}
{sec("ssot", f"SSOT · 冊({len(d['ssot'])} 件)",
     '<table><tr><th>冊</th><th>大小</th></tr>' + ssot_rows + '</table>')}
{sec("fn", f"FUNCTIONS · 短令 {len(d['verbs'])}+任務 {len(d['tasks'])}",
     "<p>" + verbs + "</p><table><tr><th>任務</th><th>說明</th></tr>"
     + tasks + "</table>")}
{sec("other", "OTHER · 頁面與測試現況",
     f"<p>現役頁 {len(d['pages'])} 族:{pages}</p><p>全矩陣:"
     + (f"{g['n']} 站 · FAIL {g['fail']}({html.escape(g['src'])})"
        if g else "存證缺(誠實)") + "</p>")}
<p class="sub" style="padding:0 4px">「刪除」=讓位道(只增不減):
本頁上位主畫面,舊頁降役為連結;陳舊非再生頁讓位 _retired 夾存證。
零 CDN · b258 視覺鎖定 tokens</p></main></div></body></html>"""


def run(do_print: bool = False) -> int:
    d = gather()
    OUT.write_text(render(d), encoding="utf-8")
    print(f"[現況總圖] 子系統 {len(d['subs'])} · 引擎族 "
          f"{sum(len(v) for v in d['engines'].values())} · 模組族 "
          f"{len(d['mods'])} · SSOT {len(d['ssot'])} · 短令 "
          f"{len(d['verbs'])}+任務 {len(d['tasks'])} · {OUT.name}")
    if do_print:
        for s in d["subs"]:
            print(f"  [子系統] {s['name']}: 引擎族 {s['engines']}")
    return 0


def selftest() -> int:
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    src = Path(__file__).read_text(encoding="utf-8")
    d = gather()
    rc = run()
    page = OUT.read_text(encoding="utf-8")
    chk("① 六區現況齊(SUB/ENG/MOD/SSOT/FN/OTHER)", rc == 0
        and all(f'id="{k}"' in page
                for k in ("sub", "eng", "mod", "ssot", "fn", "other")))
    chk("② 子系統真掃(≥4 子系統含 VDF/VRN/VAP)",
        len(d["subs"]) >= 4
        and {"VDF", "VRN", "VAP"} <= {s["name"] for s in d["subs"]})
    chk("③ 引擎/模組尾版族真計(引擎>80 族+模組>30 族)",
        sum(len(v) for v in d["engines"].values()) > 80
        and len(d["mods"]) > 30)
    chk("④ FUNCTIONS 真值(短令≥12+任務≥26)",
        len(d["verbs"]) >= 12 and len(d["tasks"]) >= 26)
    chk("⑤ SSOT 冊+台帳+grid 現況在頁",
        len(d["ssot"]) > 5 and d["ledger"] > 600 and "全矩陣" in page)
    chk("⑥ 讓位紀律宣告+零 CDN+零網路+加速橋",
        "讓位" in page and '<script src="http' not in page
        and '<link href="http' not in page and "ACCEL-BRIDGE" in src
        and all(("import " + k) not in src for k in ("requests", "httpx")))
    print(f"  [計] 六檢 OK {6 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print("=== 系統現況總圖(CGC_MDL112)· 六檢自測(零網路)===")
        return selftest()
    return run("--print" in a)


if __name__ == "__main__":
    sys.exit(main())
