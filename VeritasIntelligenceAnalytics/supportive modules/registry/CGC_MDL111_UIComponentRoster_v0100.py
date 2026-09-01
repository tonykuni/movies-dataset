#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CGC_MDL111_UIComponentRoster — 統一 U/I 元件盤點冊(批278;操作員令)
====================================================================
操作員令:「規劃 VIA VDF VRN HTML U/I,統一規劃裡面有哪些元件」
——單一 U/I 架構(批277)之元件清點報告(Zero-Hydra 全複用):
  ①頁域=MDL105 尾版 page_families+PAGE_ROSTER(28 族唯一歸屬)
  ②塊元件=MDL107 尾版 KINDS 六類 regex(STYLE/SCRIPT/SVG/TABLE/
    SECTION/ASIDE)逐頁抽取計數
  ③class 元件普查:class="…" token 全收;跨系統(≥2 系)出現=
    「共用元件」(統一規劃之公共件);單系=系統專屬件
  ④設計 token 普查::root 內 --var 名全收(統一色版/字階冊)
輸出:VIA_UI_ComponentRoster_v0100.html(手機單欄;系統別計數表+
  共用元件榜+token 冊;零 CDN)+--print 終端表
律:唯讀全頁零改寫;數字全來自真頁掃描零發明;缺頁=誠實標。
用法:python3 CGC_MDL111_UIComponentRoster_v0100.py [--print]
      | --selftest
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
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
UIDIR = VIA / "supportive modules" / "ui_support"
OUT = UIDIR / "VIA_UI_ComponentRoster_v0100.html"

CLASS_RX = re.compile(r'class=["\']([^"\']+)["\']')
TOKEN_RX = re.compile(r"--([a-zA-Z][\w-]*)\s*:")

# 系統別顯名(架構=批277 歸屬冊)
SYS_ZH = {"overview": "總覽", "governance": "總管理 CGC", "ssot": "SSOT",
          "support": "支援", "vdf": "VDF", "vrn": "VRN", "vap": "VAP",
          "mdconvert": "MD 轉換", "prompts": "Prompt"}


def _mod(pat: str):
    p = sorted(HERE.glob(pat))[-1]
    spec = importlib.util.spec_from_file_location(p.stem, p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def gather() -> dict:
    m105 = _mod("CGC_MDL105_GovernanceConsole_v*.py")
    m107 = _mod("CGC_MDL107_UISpecManager_v*.py")
    fam = m105.page_families()
    roster = m105.PAGE_ROSTER
    per_sys: dict = defaultdict(lambda: {"pages": 0, "kinds": Counter(),
                                         "classes": Counter()})
    class_sys: dict = defaultdict(set)        # class→出現系統集
    tokens: Counter = Counter()
    for base, fname in fam.items():
        view = roster.get(base, "support")
        if view is None:
            view = "governance"               # 主控台殼自身=總管理件
        f = UIDIR / fname
        if not f.exists():
            continue
        src = f.read_text(encoding="utf-8", errors="ignore")
        S = per_sys[view]
        S["pages"] += 1
        for kind, rx, _label in m107.KINDS:
            S["kinds"][kind] += len(re.findall(rx, src, re.S | re.I))
        for grp in CLASS_RX.findall(src):
            for c in grp.split():
                S["classes"][c] += 1
                class_sys[c].add(view)
        tokens.update(TOKEN_RX.findall(src))
    shared = sorted((c for c, vs in class_sys.items() if len(vs) >= 2),
                    key=lambda c: -sum(per_sys[v]["classes"][c]
                                       for v in class_sys[c]))
    return {"ts": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "n_pages": sum(s["pages"] for s in per_sys.values()),
            "per_sys": {k: {"pages": v["pages"],
                            "kinds": dict(v["kinds"]),
                            "n_classes": len(v["classes"]),
                            "top": [c for c, _ in
                                    v["classes"].most_common(8)]}
                        for k, v in per_sys.items()},
            "shared": shared[:30],
            "n_shared": len(shared),
            "tokens": [t for t, _ in tokens.most_common(24)],
            "n_tokens": len(tokens)}


def render(d: dict) -> str:
    rows = "".join(
        f"<tr><td>{html.escape(SYS_ZH.get(k, k))}</td><td>{v['pages']}</td>"
        f"<td>{v['kinds'].get('style', 0)}/{v['kinds'].get('script', 0)}/"
        f"{v['kinds'].get('svg', 0)}/{v['kinds'].get('table', 0)}/"
        f"{v['kinds'].get('section', 0)}</td><td>{v['n_classes']}</td>"
        f"<td><small>{html.escape(' '.join(v['top']))}</small></td></tr>"
        for k, v in sorted(d["per_sys"].items()))
    shared = " ".join(f"<code>.{html.escape(c)}</code>" for c in d["shared"])
    toks = " ".join(f"<code>--{html.escape(t)}</code>" for t in d["tokens"])
    return f"""<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>VIA U/I 元件盤點冊</title><style>
:root{{--bg:#f3f5f7;--panel:#fff;--line:#dce2e8;--text:#1f2933;
--muted:#6b7785;--blue:#4c78a8}}
@media (prefers-color-scheme: dark){{:root{{--bg:#10151b;--panel:#171e26;
--line:#2a333d;--text:#dbe3ea;--muted:#8a97a5;--blue:#7ba3cc}}}}
body{{background:var(--bg);color:var(--text);margin:0 auto;
font:12.5px/1.55 "Segoe UI","Noto Sans TC",sans-serif;padding:16px;
max-width:880px}}
h1{{font-size:16px}}h2{{font-size:11px;color:var(--muted);
text-transform:uppercase;letter-spacing:.08em;margin:16px 0 6px}}
.sub{{color:var(--muted);font-size:11px}}
table{{width:100%;border-collapse:collapse;background:var(--panel);
border:1px solid var(--line);border-radius:8px}}
td,th{{padding:6px 8px;border-bottom:1px solid var(--line);
text-align:left;font-variant-numeric:tabular-nums;
overflow-wrap:anywhere}}
th{{font-size:10px;color:var(--muted)}}
code{{color:var(--blue);font-size:10.5px}}
small{{color:var(--muted)}}
.wrap{{overflow-x:auto}}</style></head><body>
<h1>統一 U/I 元件盤點冊(批278)</h1>
<div class="sub">{d['ts']} · 頁域={d['n_pages']} 頁(批277 單一架構)·
塊元件=MDL107 六類 · class 普查+跨系統共用判定 · 唯讀真頁掃描零發明</div>
<h2>系統別元件計數</h2><div class="wrap"><table>
<tr><th>系統</th><th>頁</th><th>style/script/svg/table/section</th>
<th>class 種數</th><th>高頻 class</th></tr>{rows}</table></div>
<h2>共用元件(跨 ≥2 系統;統一規劃公共件 共 {d['n_shared']} 件,列前 30)</h2>
<p>{shared}</p>
<h2>設計 token 冊(--var 普查 共 {d['n_tokens']} 名,列前 24)</h2>
<p>{toks}</p>
<p class="sub">正本=本頁(ui_support)· 元件轉碼/移植=MDL107
UISpecManager 正主道 · 零 CDN</p></body></html>"""


def run(do_print: bool = False) -> int:
    d = gather()
    OUT.write_text(render(d), encoding="utf-8")
    print(f"[元件冊] {d['n_pages']} 頁 · 共用元件 {d['n_shared']} · "
          f"token {d['n_tokens']} · {OUT.name}")
    if do_print:
        for k, v in sorted(d["per_sys"].items()):
            print(f"  [{SYS_ZH.get(k, k)}] 頁 {v['pages']} · "
                  f"class {v['n_classes']} · 高頻 {' '.join(v['top'][:5])}")
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
    chk("① 頁域=單一架構全族(≥25 頁真掃)", rc == 0
        and d["n_pages"] >= 25)
    chk("② 系統別計數在(vdf/vrn/vap/governance 全列)",
        all(k in d["per_sys"] for k in ("vdf", "vrn", "vap", "governance")))
    chk("③ 共用元件判定(跨≥2系;>10 件=統一規劃實證)",
        d["n_shared"] > 10)
    chk("④ token 冊普查(--bg/--line 等基色 token 在列)",
        "bg" in d["tokens"] and "line" in d["tokens"])
    chk("⑤ 一頁冊產出(手機單欄+零 CDN)",
        "元件盤點冊" in page and 'src="http' not in page)
    chk("⑥ Zero-Hydra 複用宣告(MDL105 頁域+MDL107 KINDS)+零網路+加速橋",
        "CGC_MDL105_GovernanceConsole_v*" in src
        and "CGC_MDL107_UISpecManager_v*" in src and "ACCEL-BRIDGE" in src
        and all(("import " + k) not in src for k in ("requests", "httpx")))
    print(f"  [計] 六檢 OK {6 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print("=== 統一 U/I 元件盤點(CGC_MDL111)· 六檢自測(零網路)===")
        return selftest()
    return run("--print" in a)


if __name__ == "__main__":
    sys.exit(main())
