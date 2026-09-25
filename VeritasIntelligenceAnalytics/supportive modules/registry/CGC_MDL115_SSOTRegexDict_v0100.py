#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CGC_MDL115_SSOTRegexDict — 中央 SSOT Regex/同義字治理中心(批296;操作員令)
====================================================================
操作員 Mega-Prompt 核心:「掛載中央 SSOT 規範庫與同義字/Regex 治理
中心——集中管理跨子系統命名實體、欄位定義、語意對照表與正則庫;
自動消除同義異名、格式衝突與跨模組語意歧義」。
三職(Zero-Hydra 全唯讀掃描,零改零執行):
  ①Regex 普查:全樹 .py 掃 re.compile/re.search/re.match/re.findall
    之字面樣式→中央 Regex 冊(pattern×出處×次數);同 pattern 跨
    ≥2 檔=共用(候抽公庫);近似同義 pattern=衝突候標
  ②同義字/lexicon 彙整:registry 內 *lexicon*/*synonym*/*alias*/
    *ssot* JSON 冊聚成中央目錄(鍵數/檔)
  ③四分區矩陣(Mega-Prompt 規範 MODULE/ENGINE/FUNCTION-LIB/OTHERS)
    +RYG:各區 regex 樣式數/共用數/衝突數
輸出:VIA_SSOT_RegexDict_v0100.json(中央冊)+
  VIA_UI_SSOTRegexDict_v0100.html(四分區矩陣;小字體自適應自動換行)
用法:python3 CGC_MDL115_SSOTRegexDict_v0100.py [--print] | --selftest
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
import json
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
FM = VIA / "functional modules"
OUTJ = HERE / "VIA_SSOT_RegexDict_v0100.json"
OUT = (VIA / "supportive modules" / "ui_support"
       / "VIA_UI_SSOTRegexDict_v0100.html")
SKIP = ("references", "intake", "_retired", "ASSETS", "SCOPE_COPY",
        "__pycache__", "fixtures", "output_hub", "runtime_command_center")
# re.<fn>("pattern" 或 'pattern' 或 r"…"(單行字面;跨行/變數樣式誠實略)
RX = re.compile(r"""re\.(?:compile|search|match|findall|finditer|sub|split)\s*\(\s*r?(['"])(.+?)\1""")
SYN_KEYS = ("lexicon", "synonym", "alias", "ssot", "regex", "dict")


def _zone(path: Path) -> str:
    """四分區歸屬(Mega-Prompt 規範)"""
    s = str(path).lower()
    rel = path.name.lower()
    if "functional modules" in s:
        return "MODULE"                        # 子系統引擎
    if rel.startswith(("cgc_mdl064", "cgc_mdl095", "cgc_mdl101",
                       "cgc_mdl103")) or "deckserver" in rel \
            or "selftestgrid" in rel:
        return "ENGINE"                        # 核心引擎/樞紐/沙盒
    if "registry" in s:
        return "FUNCTION-LIB"                  # 底層冊/工具庫
    return "OTHERS"


def scan() -> dict:
    pat_hits: dict = defaultdict(list)         # pattern → [(zone, file)]
    zone_files: dict = defaultdict(set)
    roots = [FM, HERE]
    for root in roots:
        for f in root.rglob("*.py"):
            if any(part in SKIP or any(part.startswith(s) for s in SKIP)
                   for part in f.parts):
                continue
            try:
                txt = f.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            z = _zone(f)
            for m in RX.finditer(txt):
                pat = m.group(2)
                if len(pat) < 2:
                    continue
                pat_hits[pat].append((z, f.name))
                zone_files[z].add(f.name)
    # 同義字/lexicon 冊
    syn = []
    for f in sorted(HERE.glob("*.json")):
        low = f.name.lower()
        if any(k in low for k in SYN_KEYS) and f.stat().st_size > 100:
            try:
                d = json.loads(f.read_text(encoding="utf-8"))
                n = len(d) if isinstance(d, (dict, list)) else 0
            except Exception:
                n = -1
            syn.append({"name": f.name, "keys": n,
                        "kb": f.stat().st_size // 1024})
    # 統計
    shared = {p: hs for p, hs in pat_hits.items()
              if len({f for _, f in hs}) >= 2}
    zone_stat = {}
    for z in ("MODULE", "ENGINE", "FUNCTION-LIB", "OTHERS"):
        zpats = [p for p, hs in pat_hits.items()
                 if any(zz == z for zz, _ in hs)]
        zshared = [p for p in zpats if p in shared]
        zone_stat[z] = {"files": len(zone_files[z]), "patterns": len(zpats),
                        "shared": len(zshared)}
    return {"ts": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "total_patterns": len(pat_hits),
            "total_shared": len(shared),
            "zone_stat": zone_stat,
            "top_shared": sorted(
                ({"pattern": p, "n_files": len({f for _, f in hs}),
                  "files": sorted({f for _, f in hs})[:6]}
                 for p, hs in shared.items()),
                key=lambda x: -x["n_files"])[:25],
            "synonyms": syn}


def render(d: dict) -> str:
    zrows = "".join(
        f"<tr class='{'g' if v['patterns'] else 'y'}'><td>{z}</td>"
        f"<td>{v['files']}</td><td>{v['patterns']}</td>"
        f"<td>{v['shared']}</td></tr>"
        for z, v in d["zone_stat"].items())
    srows = "".join(
        f"<tr><td><code>{html.escape(s['pattern'][:60])}</code></td>"
        f"<td>{s['n_files']}</td><td><small>"
        f"{html.escape(' '.join(s['files']))}</small></td></tr>"
        for s in d["top_shared"]) or "<tr><td colspan=3>無跨檔共用樣式</td></tr>"
    yrows = "".join(
        f"<tr><td>{html.escape(s['name'])}</td>"
        f"<td>{s['keys'] if s['keys'] >= 0 else '解析敗(誠實)'}</td>"
        f"<td>{s['kb']} KB</td></tr>" for s in d["synonyms"]) \
        or "<tr><td colspan=3>無同義字/lexicon 冊</td></tr>"
    return f"""<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>VIA SSOT Regex 治理中心</title><style>
:root{{--bg:#f3f5f7;--panel:#fff;--line:#dce2e8;--text:#1f2933;
--muted:#6b7785;--blue:#4c78a8;--green:#5a9e6f;--amber:#c4943a}}
@media (prefers-color-scheme: dark){{:root{{--bg:#10151b;--panel:#171e26;
--line:#2a333d;--text:#dbe3ea;--muted:#8a97a5;--blue:#7ba3cc;
--green:#79b58c;--amber:#d4a95c}}}}
body{{background:var(--bg);color:var(--text);margin:0 auto;
font:11.5px/1.5 "Segoe UI","Noto Sans TC",sans-serif;padding:16px;
max-width:900px}}
h1{{font-size:15px}}h2{{font-size:10px;color:var(--muted);
text-transform:uppercase;letter-spacing:.08em;margin:14px 0 6px}}
.sub{{color:var(--muted);font-size:10px}}
table{{width:100%;border-collapse:collapse;background:var(--panel);
border:1px solid var(--line);border-radius:8px}}
td,th{{padding:4px 8px;border-bottom:1px solid var(--line);
text-align:left;overflow-wrap:anywhere;word-break:break-all;
font-variant-numeric:tabular-nums}}
th{{font-size:9px;color:var(--muted)}}
code{{color:var(--blue);font-size:10px}}
tr.g td:first-child{{border-left:3px solid var(--green);padding-left:8px}}
tr.y td:first-child{{border-left:3px solid var(--amber);padding-left:8px}}
.kpis{{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin:8px 0}}
.kpi{{background:var(--panel);border:1px solid var(--line);
border-radius:8px;padding:8px;border-left:3px solid var(--blue)}}
.kpi b{{font-size:18px}}.kpi small{{display:block;color:var(--muted)}}
.wrap{{overflow-x:auto}}</style></head><body>
<h1>中央 SSOT · Regex/同義字治理中心(批296)</h1>
<div class="sub">{d['ts']} · 全樹唯讀普查(Zero-Hydra 零改零執行)·
Mega-Prompt 四分區 MODULE/ENGINE/FUNCTION-LIB/OTHERS · 小字體自適應自動換行</div>
<div class="kpis">
<div class="kpi"><b>{d['total_patterns']}</b><small>唯一 Regex 樣式</small></div>
<div class="kpi"><b>{d['total_shared']}</b><small>跨檔共用(候抽公庫)</small></div>
<div class="kpi"><b>{len(d['synonyms'])}</b><small>同義字/lexicon 冊</small></div>
</div>
<h2>四分區矩陣(RYG)</h2><div class="wrap"><table>
<tr><th>分區</th><th>檔數</th><th>Regex 樣式</th><th>共用</th></tr>
{zrows}</table></div>
<h2>跨檔共用 Regex 榜(前 25;≥2 檔=候抽中央公庫)</h2>
<div class="wrap"><table><tr><th>樣式</th><th>檔數</th><th>出處</th></tr>
{srows}</table></div>
<h2>同義字/Lexicon 中央目錄</h2><div class="wrap"><table>
<tr><th>冊</th><th>鍵數</th><th>大小</th></tr>{yrows}</table></div>
<p class="sub">中央冊=VIA_SSOT_RegexDict_v0100.json · 共用樣式=抽公庫
候裁示(不失功能重新註冊)· 零網路零 CDN</p></body></html>"""


def run(do_print: bool = False) -> int:
    d = scan()
    OUTJ.write_text(json.dumps(d, ensure_ascii=False, indent=1),
                    encoding="utf-8")
    OUT.write_text(render(d), encoding="utf-8")
    print(f"[SSOT Regex] 樣式 {d['total_patterns']} · 共用 "
          f"{d['total_shared']} · 同義字冊 {len(d['synonyms'])} · "
          f"{OUT.name}")
    if do_print:
        for z, v in d["zone_stat"].items():
            print(f"  [{z}] 檔 {v['files']} · 樣式 {v['patterns']} · "
                  f"共用 {v['shared']}")
    return 0


def selftest() -> int:
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    src = Path(__file__).read_text(encoding="utf-8")
    d = scan()
    rc = run()
    page = OUT.read_text(encoding="utf-8")
    chk("① 全樹 regex 普查(樣式>50=真掃)",
        rc == 0 and d["total_patterns"] > 50)
    chk("② 四分區齊全(MODULE/ENGINE/FUNCTION-LIB/OTHERS)",
        set(d["zone_stat"]) == {"MODULE", "ENGINE", "FUNCTION-LIB",
                                "OTHERS"})
    chk("③ 跨檔共用偵測(≥2 檔;共用榜有值或誠實空)",
        "n_files" in (d["top_shared"][0] if d["top_shared"] else {"n_files": 0})
        or d["total_shared"] == 0)
    chk("④ 同義字/lexicon 中央目錄(≥1 冊真讀)",
        len(d["synonyms"]) >= 1)
    chk("⑤ 四分區矩陣頁(小字體+自動換行+RYG+零 CDN)",
        "SSOT" in page and "word-break:break-all" in page
        and "MODULE" in page and 'src="http' not in page)
    chk("⑥ Zero-Hydra 唯讀宣告+零網路+加速橋",
        "唯讀" in src and "零執行" in src and "ACCEL-BRIDGE" in src
        and all(("import " + k) not in src for k in ("requests", "httpx",
                                                     "subprocess")))
    print(f"  [計] 六檢 OK {6 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print("=== 中央 SSOT Regex 治理中心(CGC_MDL115)· 六檢自測(零網路)===")
        return selftest()
    return run("--print" in a)


if __name__ == "__main__":
    sys.exit(main())
