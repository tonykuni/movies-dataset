#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
via_ui_kit_v0100 — 母子系統統一 U/X U/I 套件(TOOL-084)
====================================================================
操作員令(批73,2026-08-20):「母系統跟仔細同 U/X U/I 完善所有
系統與重新規劃 U/X U/I」。
原則:
  ① 單一真相 — 全部樣式出自 VIA_Style_Locks_v0100.json(批71 雙
     風格鎖:理印紙墨+Industry 48 tokens+操作員核定響應式套路);
     本套件只讀冊生成 CSS/JS,零寫死色值(退階常數=冊值鏡像)。
  ② 母子同貌 — 任何 VIA 生成頁(digest/finaudit/finx/center/…)
     匯入 kit_css()+kit_js() 即得:雙主題切換(localStorage 全站
     共享 via_theme 鍵=母子頁同步)+auto-fit 等高卡格+orientation
     橫直式+微互動+理印銘言刊頭樣式。
  ③ graceful — 冊缺=退階內建鏡像值,誠實記 source;零 CDN。
用法(引擎側):
  from via_ui_kit… import kit_css, kit_js   (動態載入套路亦可)
  html = f"<style>{kit_css()}</style> … <script>{kit_js()}</script>"
自測:python via_ui_kit_v0100.py --selftest(六檢)
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
LOCKS = VIA / "functional modules" / "VAP" / "VIA_Style_Locks_v0100.json"
MOTTO = "VERITAS INTELLIGENCE ANALYTICS · OBSERVA · INTELLEGE · PRAEVIDE"

# 冊值鏡像(退階用;正源=VIA_Style_Locks_v0100.json)
_LIYIN = {"paper": "#f2f1ec", "card": "#fbfaf7", "ink": "#1b1a17", "seal": "#9e2b25",
          "teal": "#3c6660", "green": "#3d7a52", "gold": "#8a6420", "blue": "#24457f",
          "line": "#dbd9d3",
          "font": "'Cormorant Garamond','Noto Serif CJK TC','Microsoft JhengHei',serif"}
_IND = {"paper": "#f2f2f3", "card": "#f5f5f8", "ink": "#1d1f20", "seal": "#416180",
        "teal": "#5980a6", "green": "#597ea3", "gold": "#7a7a7d", "blue": "#2c455d",
        "line": "#d4d4d7", "font": "'Barlow','Microsoft JhengHei',system-ui,sans-serif"}


def load_locks() -> tuple[dict, dict, str]:
    """讀雙風格鎖冊;缺=鏡像退階(誠實記 source)"""
    if LOCKS.exists():
        try:
            d = json.loads(LOCKS.read_text(encoding="utf-8-sig"))
            li = d["locks"]["liyin"]
            tk = d["locks"]["industry"]["tokens"]
            ind = {"paper": tk.get("--color-bg", _IND["paper"]),
                   "card": tk.get("--color-neutral-100", _IND["card"]),
                   "ink": tk.get("--color-text", _IND["ink"]),
                   "seal": tk.get("--color-accent-700", _IND["seal"]),
                   "teal": tk.get("--color-accent", _IND["teal"]),
                   "green": tk.get("--color-accent-600", _IND["green"]),
                   "gold": tk.get("--color-neutral-600", _IND["gold"]),
                   "blue": tk.get("--color-accent-800", _IND["blue"]),
                   "line": tk.get("--color-neutral-300", _IND["line"]),
                   "font": _IND["font"]}
            liy = {k: li.get(k, v) for k, v in _LIYIN.items()}
            return liy, ind, LOCKS.name
        except Exception:
            pass
    return dict(_LIYIN), dict(_IND), "鏡像退階(冊缺)"


def kit_css() -> str:
    liy, ind, _src = load_locks()

    def block(t):
        return (f"--bg:{t['paper']};--card:{t['card']};--ink:{t['ink']};--seal:{t['seal']};"
                f"--teal:{t['teal']};--green:{t['green']};--gold:{t['gold']};"
                f"--blue:{t['blue']};--line:{t['line']};--font:{t['font']}")
    return f"""
:root{{{block(liy)}}}
body.theme-industry{{{block(ind)}}}
body{{background:var(--bg);color:var(--ink);font-family:var(--font);margin:0;padding:20px;transition:background .3s ease}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:16px 20px;margin:12px auto;max-width:1280px;
transition:transform .3s cubic-bezier(.25,1,.5,1),box-shadow .3s cubic-bezier(.25,1,.5,1),border-color .3s}}
.card:hover{{transform:translateY(-3px);border-color:var(--teal);box-shadow:0 10px 25px -8px rgba(60,102,96,.22)}}
h1{{font-size:clamp(16px,2.2vw,20px);margin:0 0 2px}}h2{{font-size:15px;color:var(--teal);margin:16px 0 6px}}
.motto{{color:var(--seal);letter-spacing:.14em;font-size:11px;margin-bottom:14px}}
table{{border-collapse:collapse;width:100%;font-size:12.5px;table-layout:auto}}
th{{color:var(--teal);text-align:left;border-bottom:1.5px solid var(--teal);padding:4px 8px}}
td{{border-bottom:1px solid var(--line);padding:4px 8px;vertical-align:top;word-break:break-word;overflow-wrap:anywhere}}
.ok{{color:var(--green);font-weight:bold}}.warn{{color:var(--gold);font-weight:bold}}.bad{{color:var(--seal);font-weight:bold}}
.g{{color:var(--green);font-weight:bold}}.y{{color:var(--gold);font-weight:bold}}.r{{color:var(--seal);font-weight:bold}}
.mono{{font-family:Consolas,monospace;font-size:11.5px}}.dim{{color:#6b6a64}}
.kitgrid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));grid-auto-rows:1fr;gap:12px}}
@media(orientation:portrait){{body{{padding:10px}}.card{{padding:10px 12px}}.kitgrid{{grid-template-columns:1fr}}}}
#themebtn{{position:fixed;top:12px;right:14px;z-index:9;background:var(--ink);color:var(--card);border:0;border-radius:16px;padding:6px 14px;cursor:pointer;font-size:11px;font-family:inherit}}
"""


def kit_js() -> str:
    return """
function themeToggle(){var b=document.body;b.classList.toggle('theme-industry');
localStorage.setItem('via_theme',b.classList.contains('theme-industry')?'industry':'liyin');
document.getElementById('themebtn').textContent=b.classList.contains('theme-industry')?'風格:Industry':'風格:理印';}
(function(){if(localStorage.getItem('via_theme')==='industry'){document.body.classList.add('theme-industry');}
var b=document.createElement('button');b.id='themebtn';b.onclick=themeToggle;
b.textContent=document.body.classList.contains('theme-industry')?'風格:Industry':'風格:理印';
document.body.appendChild(b);})();
"""


def selftest() -> int:
    t0 = time.time()
    fails = []

    def chk(name, cond, note=""):
        if not cond:
            fails.append(name)
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")

    liy, ind, src = load_locks()
    chk("風格鎖冊讀取", src == LOCKS.name, f"({src})")
    chk("理印鎖值", liy["paper"] == "#f2f1ec" and liy["seal"] == "#9e2b25")
    chk("Industry 鎖值(冊 48 tokens 映射)", ind["paper"] == "#f2f2f3"
        and ind["teal"] == "#5980a6" and ind["ink"] == "#1d1f20")
    css = kit_css()
    chk("kit_css(雙主題+auto-fit+橫直式+微互動)",
        "theme-industry" in css and "repeat(auto-fit,minmax(" in css
        and "grid-auto-rows:1fr" in css and "orientation:portrait" in css
        and "cubic-bezier(.25,1,.5,1)" in css and "http" not in css)
    js = kit_js()
    chk("kit_js(全站 via_theme 共享鍵)", "localStorage" in js and "via_theme" in js
        and "themebtn" in js)
    # 冊缺退階
    import unittest.mock as _m
    with _m.patch.object(Path, "exists", return_value=False):
        _l, _i, s2 = load_locks()
    chk("冊缺 graceful 退階", s2.startswith("鏡像退階") and _l["paper"] == "#f2f1ec")
    n = 6 - len(fails)
    print(f"  [計] 六檢 OK {n} · FAIL {len(fails)} · {round(time.time() - t0, 1)}s")
    return 1 if fails else 0


if __name__ == "__main__":
    if "--selftest" in sys.argv[1:]:
        print("=== 母子統一 U/I 套件 v0100 · 六檢 ===")
        sys.exit(selftest())
    print(kit_css())
    sys.exit(0)
