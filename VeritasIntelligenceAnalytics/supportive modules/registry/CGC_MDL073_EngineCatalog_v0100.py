#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
via_engine_catalog_v0100 — 引擎總目錄產生器(TOOL-054;操作員令 2026-08-18)
==========================================================================
令:「引擎整合強化測試 矩陣畫清單及對每一個引擎的功能寫詳細」。
原則:零發明——每一筆說明取自 AST 實抽之 docstring(介面合約冊 TOOL-041)
+函式簽名+CLI 旗標+類冊;正典號取自命名冊 TOOL-047;自測能力=CLI 含
--selftest 實測值;整合邊=import 實值。
產出:
  ① VIA_Engine_Catalog_v0100.json(tracked;全 ENG 逐支詳目)
  ② VIA_Engine_Catalog_v0100.md(tracked;按 SYS 分章,逐引擎:正典號/
     版本族/功能說明/函式簽名/CLI/自測/整合邊)
  ③ VIA_Reports/VIA_UI_EngineCatalog.html(U/I 檢索板,理印鎖定,runtime)
用法:via-catalog            → 產出三件
     via-catalog --selftest → 完整性四檢
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

import html as H
import json
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
NAMEREG = HERE / "VIA_Naming_Registry_v0100.json"
IFACE = HERE / "VIA_Interface_Contract_Registry_v0100.json"
JSON_OUT = HERE / "VIA_Engine_Catalog_v0100.json"
MD_OUT = HERE / "VIA_Engine_Catalog_v0100.md"
UI_OUT = VIA / "VIA_Reports" / "VIA_UI_EngineCatalog.html"

SYS_ZH = {"VRN": "報告情報", "VDF": "數據鍛造", "VAP": "視覺分析", "CHW": "籌碼戰",
          "FLOW": "資金流", "GRP": "族群指數", "VIA": "泛功能", "PLG": "插件", "CGC": "中央治理", "SUP": "支援"}


def build() -> dict:
    reg = json.loads(NAMEREG.read_text(encoding="utf-8"))
    iface = json.loads(IFACE.read_text(encoding="utf-8"))["modules"]
    by_rel = {m["rel"]: m for m in iface.values()}
    engines = []
    for fam, it in reg["items"].items():
        if it["kind"] != "ENG":
            continue
        newest_rel = sorted(it["members"])[-1]
        c = by_rel.get(newest_rel, {}).get("contract", {})
        desc = (by_rel.get(newest_rel, {}).get("desc") or "").strip()
        fns = [{"name": f.get("name"), "args": f.get("args", [])}
               for f in c.get("functions", []) if isinstance(f, dict) and not str(f.get("name", "")).startswith("_")]
        cls = [cl.get("name") if isinstance(cl, dict) else str(cl) for cl in c.get("classes", [])]
        cli = sorted(c.get("cli_flags", []))
        sup_edges = sorted({str(i).split(".")[0] for i in c.get("imports", [])
                            if str(i).startswith(("VIA_", "Veritas", "superextract"))})
        engines.append({
            "canonical": it["canonical"], "sys": it["sys"], "family": fam,
            "versions": len(it["members"]), "newest": newest_rel,
            "desc": desc or "(原碼無 docstring——候補說明,誠實不代寫)",
            "functions": fns, "classes": cls, "cli": cli,
            "selftest": "--selftest" in cli, "has_main": bool(c.get("has_main")),
            "support_edges": sup_edges,
        })
    engines.sort(key=lambda e: e["canonical"])
    return {"schema": "VIA.EngineCatalog.v1", "ts": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "principle": "零發明:說明=AST 實抽 docstring;函式/CLI/邊=合約冊實值",
            "n": len(engines), "engines": engines}


def write_md(cat: dict) -> None:
    L = ["# VIA 引擎總目錄 v0100(逐引擎詳細功能)", "",
         f"引擎 {cat['n']} 支 · {cat['ts']} · 原則:{cat['principle']}", "",
         "| SYS | 支數 | 自測具備 |", "|---|---|---|"]
    by_sys: dict[str, list] = {}
    for e in cat["engines"]:
        by_sys.setdefault(e["sys"], []).append(e)
    for s in sorted(by_sys):
        es = by_sys[s]
        L.append(f"| {s} · {SYS_ZH.get(s, '')} | {len(es)} | {sum(1 for e in es if e['selftest'])} |")
    for s in sorted(by_sys):
        L += ["", f"## {s} · {SYS_ZH.get(s, '')}({len(by_sys[s])} 支)", ""]
        for e in by_sys[s]:
            L.append(f"### {e['canonical']}")
            L.append(f"- **族**:`{e['family']}`(版本 {e['versions']};現役 `{Path(e['newest']).name}`)")
            d = e["desc"].replace("\n", " ").strip()
            L.append(f"- **功能**:{d[:600]}")
            if e["classes"]:
                L.append(f"- **類**:{', '.join(e['classes'][:12])}")
            if e["functions"]:
                sig = " · ".join(f"`{f['name']}({', '.join(f['args'][:5])})`" for f in e["functions"][:10])
                L.append(f"- **函式**({len(e['functions'])}):{sig}")
            if e["cli"]:
                L.append(f"- **CLI**:{' '.join('`' + c + '`' for c in e['cli'][:12])}")
            L.append(f"- **自測**:{'✅ --selftest' if e['selftest'] else ('主程式可跑' if e['has_main'] else '匯入型')}"
                     + (f" · **整合邊**:{', '.join(e['support_edges'][:6])}" if e["support_edges"] else ""))
            L.append("")
    MD_OUT.write_text("\n".join(L), encoding="utf-8")


def write_ui(cat: dict) -> None:
    rows = json.dumps([{**e, "functions": [f["name"] for f in e["functions"]]} for e in cat["engines"]],
                      ensure_ascii=False)
    htm = """<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>VIA 引擎總目錄</title><style>
:root{--paper:#f2f1ec;--card:#fbfaf7;--ink:#1b1a17;--muted:#6b6860;--hair:#dbd9d3;--seal:#9e2b25;--teal:#3c6660;--mastH:64px}
*{box-sizing:border-box}body{font-family:'Microsoft JhengHei',system-ui,sans-serif;margin:0;background:var(--paper);color:var(--ink)}
.mast{position:fixed;top:0;left:0;right:0;z-index:9;display:flex;gap:.7rem;align-items:center;padding:.6rem 1.2rem;
background:var(--card);border-bottom:1px solid var(--hair);transition:transform .28s}.mast.hide{transform:translateY(-110%)}
.seal{width:36px;height:36px;border-radius:5px;background:var(--seal);color:#f2f1ec;display:flex;align-items:center;justify-content:center;font-family:serif;font-size:21px}
h1{font-family:'Cormorant Garamond',Georgia,serif;font-size:17px;margin:0}
.wrap{padding:calc(var(--mastH) + .8rem) 1.2rem 1rem}
input,select{padding:.4rem .6rem;border:1px solid var(--hair);border-radius:4px}
details{background:var(--card);border:1px solid var(--hair);border-radius:5px;margin:.35rem 0;padding:.3rem .7rem}
summary{cursor:pointer;font-family:'SFMono-Regular',Consolas,monospace;font-size:.82rem;color:#24457f}
.d{font-size:.82rem;padding:.3rem 0 .4rem;color:var(--ink)}.mut{color:var(--muted)}
.tag{border:1px solid var(--hair);border-radius:3px;padding:0 .35rem;font-size:.7rem;color:var(--muted);margin-right:.2rem}
</style></head><body>
<div class="mast" id="m"><div class="seal">理</div><div><h1>VIA 引擎總目錄</h1>
<div class="mut" style="font-size:.75rem">逐引擎詳細功能 · AST 實值零發明</div></div></div>
<div class="wrap"><p><input id="q" placeholder="搜尋…" size="30"> <select id="s"><option value="">全 SYS</option></select>
<span class="mut" id="st"></span></p><div id="list"></div></div>
<script>const D=__ROWS__;
const l=document.getElementById('list'),q=document.getElementById('q'),s=document.getElementById('s'),st=document.getElementById('st');
[...new Set(D.map(r=>r.sys))].sort().forEach(x=>{const o=document.createElement('option');o.textContent=x;s.appendChild(o)});
function render(){const t=q.value.toLowerCase(),sy=s.value;
 const rs=D.filter(r=>(!sy||r.sys===sy)&&(!t||r.canonical.toLowerCase().includes(t)||r.desc.toLowerCase().includes(t)));
 l.innerHTML=rs.slice(0,400).map(r=>`<details><summary>${r.canonical} <span class="tag">${r.sys}</span>`+
  `<span class="tag">v×${r.versions}</span>${r.selftest?'<span class="tag" style="color:#3d7a52">selftest</span>':''}</summary>`+
  `<div class="d">${r.desc.slice(0,500)}<br><span class="mut">函式:${r.functions.slice(0,14).join(', ')||'—'}</span>`+
  `<br><span class="mut">CLI:${r.cli.join(' ')||'—'} · 邊:${r.support_edges.join(', ')||'—'}</span></div></details>`).join('');
 st.textContent=rs.length+'/'+D.length+' 支'}
q.oninput=render;s.onchange=render;render();
let y=0;addEventListener('scroll',()=>{const n=scrollY;document.getElementById('m').classList.toggle('hide',n>y&&n>80);y=n},{passive:true});
</script></body></html>"""
    UI_OUT.parent.mkdir(parents=True, exist_ok=True)
    UI_OUT.write_text(htm.replace("__ROWS__", rows), encoding="utf-8")


def selftest() -> int:
    print("=== 引擎總目錄 v0100 · 完整性四檢 ===")
    cat = build()
    reg = json.loads(NAMEREG.read_text(encoding="utf-8"))
    n_eng = sum(1 for it in reg["items"].values() if it["kind"] == "ENG")
    with_desc = sum(1 for e in cat["engines"] if not e["desc"].startswith("("))
    checks = [("全 ENG 覆蓋(冊=目)", cat["n"] == n_eng),
              ("逐支詳目非空", all(e["canonical"] and e["family"] for e in cat["engines"])),
              ("說明實值比 ≥60%", with_desc / max(cat["n"], 1) >= 0.6),
              ("零發明原則標記", "零發明" in cat["principle"])]
    n = 0
    for name, ok in checks:
        n += ok
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
    print(f"  [計] {n}/4 檢通過 · ENG {cat['n']} · 有實說明 {with_desc}({with_desc * 100 // max(cat['n'], 1)}%)")
    return 0 if n == 4 else 1


def main() -> int:
    if "--selftest" in sys.argv[1:]:
        return selftest()
    cat = build()
    JSON_OUT.write_text(json.dumps(cat, ensure_ascii=False, indent=1), encoding="utf-8")
    write_md(cat)
    write_ui(cat)
    by = {}
    for e in cat["engines"]:
        by[e["sys"]] = by.get(e["sys"], 0) + 1
    print(f"=== 引擎總目錄 v0100 · ENG {cat['n']} 支 ===")
    print("  [屬] " + " · ".join(f"{k}×{v}" for k, v in sorted(by.items())))
    print(f"  [出] {JSON_OUT.name} + {MD_OUT.name} + {UI_OUT.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
