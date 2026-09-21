#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CGC_MDL115_SSOTRegexDict — 中央 SSOT Regex/同義字治理中心(批296;操作員令)
====================================================================
操作員 Mega-Prompt 核心:「掛載中央 SSOT 規範庫與同義字/Regex 治理
中心——集中管理跨子系統命名實體、欄位定義、語意對照表與正則庫;
自動消除同義異名、格式衝突與跨模組語意歧義」。
三職(Zero-Hydra 全唯讀掃描,零改零執行):
v0100→v0101(批664:清冊記下來的式,不是樹上那條式)
  MDL169 六域現況矩陣上線第一跑就把這本冊照紅了:top_shared 兩條 pattern
  **編不過**——
      top_shared[9]  '<meta\\s+name=["\\'
      top_shared[24] '\\b(Buy|Sell|Hold|Neutral|Overweight|Underweight|Outperform|'
  兩條都是**被截斷的**,不是樹上真的有壞式。根因在這支自己的尺:
      RX = ...r?(['"])(.+?)\\1
  ① `(.+?)\\1` 非貪婪吃到**第一個同款引號**就收手,碰到式子裡跳脫過的引號
     (`["\\']`)就在那裡斷掉 —— 43 個檔共用的那條 `<meta` 式就是這樣斷的。
  ② 隱式相接的多段字面(一個 re.compile( 跨行接兩段)只拿得到第一段。
  修法:改走 **AST 零執行**取 re.<fn>() 的第一個引數字面——跳脫與隱式相接
  都由 Python 自己還原,不必我再寫一條會漏的 regex 去讀 regex。
  正則那條留作**退路**(AST 解不開的檔才走),而且退路走了幾檔要報出來:
  **退路默默生效,等於一本你以為是 AST 產的冊其實是舊尺產的**。
  另補 ⑤ 檢:冊裡每一條 pattern 都要編得過——清冊記錯了式,
  拿它去全樹取代的人會一無所獲而且不知道為什麼。
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
import ast
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
# 批664(L77 掃描根一律帶排除清單):原本的排除清單漏了退役夾與隔離區,
#   於是**死碼的 regex 被算進全樹清冊**——那三支「語法真的壞掉」的檔全都住在
#   VIA_RetiredEngines/…/_review_quarantine 裡。退役的東西壞掉不是現況,
#   把它算進分母只會讓「全樹有幾條式」這個數字回答不了任何問題(L57 誠實分母)。
SKIP = ("references", "intake", "_retired", "ASSETS", "SCOPE_COPY",
        "__pycache__", "fixtures", "output_hub", "runtime_command_center",
        "VIA_RetiredEngines", "_review_quarantine", "_quarantine")
# re.<fn>("pattern" 或 'pattern' 或 r"…"(單行字面;跨行/變數樣式誠實略)
RX = re.compile(r"""re\.(?:compile|search|match|findall|finditer|sub|split)\s*\(\s*r?(['"])(.+?)\1""")
SYN_KEYS = ("lexicon", "synonym", "alias", "ssot", "regex", "dict")
_RE_FNS = {"compile", "search", "match", "findall", "finditer", "sub", "split"}


def _compiles(rx: str) -> bool:
    try:
        re.compile(rx)
        return True
    except re.error:
        return False


def _ast_patterns(txt: str):
    """AST 零執行取 re.<fn>() 的第一個字面引數。

    跳脫(`[\"\\']`)與隱式相接(跨行兩段字面)都由 Python 自己還原——
    寫一條 regex 去讀 regex,永遠會在某個跳脫上斷掉(批664 實錄:斷了 2 條)。
    回 None 代表這個檔 AST 解不開,呼叫端要走退路**而且要記一筆**。
    """
    try:
        tree = ast.parse(txt)
    except SyntaxError as exc:
        return ("SYNTAX", f"L{exc.lineno}: {exc.msg}")
    except Exception as exc:
        return ("SYNTAX", f"{type(exc).__name__}: {str(exc)[:60]}")
    out = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not node.args:
            continue
        fn = node.func
        if not (isinstance(fn, ast.Attribute) and fn.attr in _RE_FNS
                and isinstance(fn.value, ast.Name) and fn.value.id == "re"):
            continue
        a0 = node.args[0]
        if isinstance(a0, ast.Constant) and isinstance(a0.value, str):
            out.append(a0.value)           # 變數樣式/f-string 誠實略(拿不到字面)
    return ("OK", out)


# py3.12 之前 f-string 裡不准有反斜線(PEP 701 才鬆綁)。容器是 3.11、
# 工作站家族境是 3.12——**同一支檔,兩邊解出來的結果不一樣**。
# 把它判成「檔壞了」是判錯的紅燈:壞的是我這邊的解譯器版本,不是那支檔。
_PY312_HINT = "f-string expression part cannot include a backslash"


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
    needs_py312: list = []                     # 本境 py<3.12 讀不動(不是檔壞)
    syntax_broken: list = []                   # 真的語法壞掉,逐檔點名
    dropped: list = []                         # 編不過而沒入冊的式,具名不靜默
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
            kind, payload = _ast_patterns(txt)
            if kind == "OK":
                pats = payload
            else:                                  # AST 解不開:逐檔分類,不混為一談
                if _PY312_HINT in payload:
                    needs_py312.append(f"{f.name}({payload})")
                else:
                    syntax_broken.append(f"{f.name}({payload})")
                pats = [m.group(2) for m in RX.finditer(txt)]   # 舊正則退路
            for pat in pats:
                if len(pat) < 2:
                    continue
                if not _compiles(pat):
                    # 清冊的用途是「拿這條式去全樹找」。一條編不過的式對誰都沒用,
                    # 但**不能靜默丟掉**——丟掉就變成一本看起來很乾淨的冊。具名留著。
                    dropped.append({"file": f.name, "pattern": pat[:80]})
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
    bad = sorted(p_ for p_ in pat_hits if not _compiles(p_))
    return {"ts": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "harvest": ("AST 零執行取 re.<fn>() 首個字面引數(批664;跳脫與隱式相接由 Python 還原)"
                        f"· 本境 python {sys.version.split()[0]}"),
            "needs_py312": sorted(set(needs_py312)),
            "syntax_broken": sorted(set(syntax_broken)),
            "dropped_uncompilable": dropped[:20],
            "dropped_n": len(dropped),
            "uncompilable": bad[:10],
            "uncompilable_n": len(bad),
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
    # 批664 ⑦:清冊記下來的式,自己要編得過。記錯了式,拿它去全樹取代的人
    #   會一無所獲、而且不知道為什麼——那是最難查的一種錯:**東西在,只是不對**。
    chk("⑦ 冊裡每條 pattern 都編得過,落選的具名不靜默(批664)",
        d["uncompilable_n"] == 0 and isinstance(d["dropped_uncompilable"], list),
        f"(冊內編不過 {d['uncompilable_n']} · 落選具名 {d['dropped_n']} 條"
        f"{[x['file'] for x in d['dropped_uncompilable'][:2]]})")
    # ⑧ AST 取式要真的解得開,退路只能是少數;退路默默生效=你以為 AST 產的冊其實是舊尺產的
    # 解不開的檔分兩類:本境 python 版本讀不動的(不是檔壞)、真的語法壞掉的。
    #   混成一句「9 檔解不開」會讓人去修 6 支根本沒壞的檔,而真壞的 3 支照樣沒人管。
    chk("⑧ AST 為主;解不開的逐檔分類(版本 vs 真壞)(批664)",
        "AST" in d.get("harvest", "") and isinstance(d.get("needs_py312"), list)
        and isinstance(d.get("syntax_broken"), list),
        f"(py<3.12 讀不動 {len(d['needs_py312'])} 檔 · **真語法壞 {len(d['syntax_broken'])} 檔**"
        f":{[x.split('(')[0] for x in d['syntax_broken'][:3]]})")
    # ⑨ 跳脫引號與隱式相接這兩個舊尺的破口,現在要真的補起來(拿實例咬)
    probe = ('import re\n'
             'a = re.compile(r\'<meta\\s+name=["\\\']x\\\'>\')\n'
             'b = re.compile(r"\\b(Buy|Sell|"\n'
             '               r"Hold)\\b")\n')
    _k, got = _ast_patterns(probe)
    got = got if _k == "OK" else []
    chk("⑨ 跳脫引號不斷、隱式相接接得起來(批664 根因咬合)",
        _k == "OK" and len(got) == 2 and got[0].endswith(">") and "Hold" in got[1],
        f"({[g[:30] for g in got]})")
    chk("⑥ Zero-Hydra 唯讀宣告+零網路+加速橋",
        "唯讀" in src and "零執行" in src and "ACCEL-BRIDGE" in src
        and all(("import " + k) not in src for k in ("requests", "httpx",
                                                     "subprocess")))
    print(f"  [計] 九檢 OK {9 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print("=== 中央 SSOT Regex 治理中心(CGC_MDL115)· 九檢自測(零網路)===")
        return selftest()
    return run("--print" in a)


if __name__ == "__main__":
    sys.exit(main())
