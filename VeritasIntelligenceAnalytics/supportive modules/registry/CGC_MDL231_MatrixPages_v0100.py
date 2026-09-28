#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL231_MatrixPages v0100 — VCGC · VDF · VRN 多頁式矩陣報告(rich 畫表 · 小字 · 版面自動縮放 · 鎖檢)

操作員 2026-09-28:「成功的部份鎖住 後面的部分就邊測邊修 … VCGC VDF VRN 自動跳出多頁式矩陣式報告 BY RICH 字體小版面自動優化」。
不另立第二套報告(L05):矩陣內容全取自全景報告正主 CGC_MDL229 尾版的 build(側車 SWEEP_SIDE_latest.json + 各鏈 JSON),
本支只做三件事:
  ① 分頁:總覽 · 鎖 · VCGC · VDF · VRN · DB · 橋與全景 · 工具 · 一鍵(每頁一組 rich 表,匯出 HTML、行內樣式);
  ② 鎖檢:讀鎖冊尾版 VIA_LampLock_v*.json(v2 起含 VDF / VRN 鏈節點)對這一次的燈與鏈 ——
     已鎖 GREEN = 守住;RED / ABSENT / NODATA / CRASH = **回歸**(進總覽待辦最前);GATED / SKIP / 沒量到 = 未量;
     開著的項目這次綠了 = 可加鎖(照實列,AI 依貼回開下一版冊,工作站不自己寫冊);
  ③ 一鍵頁 / 診斷:讀 VIA_Reports/runall/RUNALL_STEPS_latest.json(一鍵 v0102 寫)。
輸出 VIA_Reports/matrix/VIA_MATRIX_PAGES_latest.html:零 CDN、零外連、file:// 直開;字級 11px 起,本機 JS 依視窗寬度自動縮到 7px 讓整表塞得下。
開頁由呼叫端(一鍵)決定;本支不自開(VCGC 零彈窗律照舊)。rich 缺席 = 退純文字同內容(照實標)。

用法(經 VCGC;VIA_FROM_VCGC=YES):
  python CGC_MDL231_MatrixPages_v0100.py pages [--width N]     # 產頁,印一行 [MatrixPages] … HTML <路徑>
  python CGC_MDL231_MatrixPages_v0100.py lock                  # 只印鎖檢(守住 / 回歸 / 未量 / 可加鎖)
  python CGC_MDL231_MatrixPages_v0100.py --selftest
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

import html as _html
import importlib.util
import io
import json
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
REPORTS = VIA / "VIA_Reports"
OUT = REPORTS / "matrix"
PAGE_NAME = "VIA_MATRIX_PAGES_latest.html"
SIDE = REPORTS / "sweep" / "SWEEP_SIDE_latest.json"
RUNALL = REPORTS / "runall" / "RUNALL_STEPS_latest.json"
VDF_CHAIN = REPORTS / "vdf_chain" / "VDFCHAIN_latest.json"
VRN_CHAIN = REPORTS / "vrn_chain" / "VRNCHAIN_latest.json"
DBM_HTML = REPORTS / "dbmanager" / "DBM_REPORT_latest.html"
ENGINE_TAG = "CGC_MDL231_MatrixPages v" + Path(__file__).stem.rsplit("_v", 1)[-1]
REGRESS = {"RED", "ABSENT", "NODATA", "CRASH"}
UNMEASURED = {"GATED", "SKIP", "", "—", None}
TAB_OF = {"①": "總覽", "⑩": "總覽", "②": "VCGC", "③": "VCGC", "④": "VCGC", "⑤": "DB", "⑥": "VDF", "⑦": "VRN",
          "⑧": "橋與全景", "⑨": "橋與全景", "⑪": "工具", "⑫": "工具", "⑬": "工具", "⑭": "工具"}
TABS = ("總覽", "鎖", "VCGC", "VDF", "VRN", "DB", "橋與全景", "工具", "一鍵")


def _load_json(p: Path):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def sweep_tail():
    hits = sorted(HERE.glob("CGC_MDL229_SweepReport_v*.py"))
    if not hits:
        return None
    spec = importlib.util.spec_from_file_location("mdl229_for_mdl231", hits[-1])
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def lock_book(folder: Path = HERE):
    hits = sorted(folder.glob("VIA_LampLock_v*.json"))
    return (_load_json(hits[-1]), hits[-1].name) if hits else (None, None)


def lamp_states(sections: list) -> dict:
    """③ VCGC 子系統燈 → {'vdf_logic': 'GREEN', …}。"""
    out = {}
    for t, cols, rows, _st in sections:
        if not str(t).startswith("③"):
            continue
        for r in rows or []:
            side = str(r[0]).strip().lower()
            for c, v in zip(cols[2:], r[2:]):
                out[f"{side}_{str(c).strip()}"] = str(v).strip()
    return out


def chain_states(rep: dict | None, key: str) -> dict:
    return {str(s.get(key)): str(s.get("state") or "") for s in ((rep or {}).get("stages") or []) if s.get(key) is not None}


def _judge(state) -> str:
    if state == "GREEN":
        return "守住"
    if state in REGRESS:
        return "回歸"
    return "未量"


def lock_check(book: dict | None, lamps: dict, vdf: dict, vrn: dict) -> dict:
    """回 {rows: [[類, 項目, 這次, 判定]], regress: [...], unmeasured: n, add: [...]}。"""
    rows, regress, add = [], [], []
    if not book:
        return {"rows": [], "regress": [], "held": 0, "unmeasured": 0, "add": [], "absent": True}
    for lid in book.get("locked") or []:
        st = lamps.get(lid)
        j = _judge(st)
        rows.append(["燈", lid, st or "沒量到", j])
        if j == "回歸":
            regress.append(f"燈 {lid}:{st}")
    for side, states in (("vdf", vdf), ("vrn", vrn)):
        for nid in (book.get("nodes") or {}).get(side) or []:
            st = states.get(str(nid))
            j = _judge(st)
            rows.append([f"{side.upper()} 節點", str(nid), st or "沒量到", j])
            if j == "回歸":
                regress.append(f"{side.upper()} {nid}:{st}")
    for lid in book.get("open") or []:
        if lamps.get(lid) == "GREEN":
            add.append(f"燈 {lid}")
    for side, states in (("vdf", vdf), ("vrn", vrn)):
        for nid in (book.get("nodes_open") or {}).get(side) or []:
            if states.get(str(nid)) == "GREEN":
                add.append(f"{side.upper()} {nid}")
    order = {"回歸": 0, "未量": 1, "守住": 2}
    rows.sort(key=lambda r: (order.get(r[3], 3), r[0], r[1]))
    return {"rows": rows, "regress": regress, "held": sum(1 for r in rows if r[3] == "守住"),
            "unmeasured": sum(1 for r in rows if r[3] == "未量"), "add": add, "absent": False}


def build_pages(rep: dict, lock: dict, book_name: str | None, runall: dict | None) -> dict:
    pages = {t: [] for t in TABS}
    for sec in rep.get("sections") or []:
        tab = TAB_OF.get(str(sec[0])[:1], "總覽")
        pages[tab].append(tuple(sec))
    # 鎖頁
    if lock.get("absent"):
        pages["鎖"].append(("鎖檢 · 鎖冊不在(VIA_LampLock_v*.json)", ["狀態"], [["ABSENT · 沒有鎖冊就沒有回歸可比"]], 0))
    else:
        head = [["回歸", str(len(lock["regress"])), "已鎖卻退回 RED / ABSENT / NODATA —— 最優先"],
                ["守住", str(lock["held"]), "這次仍是 GREEN"],
                ["未量", str(lock["unmeasured"]), "GATED / SKIP / 沒量到:本次沒量,不算回歸"],
                ["可加鎖", str(len(lock["add"])), "開著的項目這次綠了:" + (" · ".join(lock["add"][:8]) or "無")]]
        pages["鎖"].append((f"鎖檢摘要({book_name})", ["判定", "數", "說明"], head, 0))
        pages["鎖"].append(("鎖檢逐項(回歸在最上)", ["類", "項目", "這次", "判定"], lock["rows"], 3))
    if lock.get("regress"):
        pages["總覽"].insert(1, ("🔒 回歸(已鎖卻退回非綠)", ["項目"], [[x] for x in lock["regress"]], None))
    # 一鍵頁 + 診斷
    if runall:
        steps = [[s.get("title", ""), s.get("state", ""), "" if s.get("rc") is None else str(s.get("rc")),
                  "" if s.get("sec") is None else f"{s.get('sec')}s", " / ".join(s.get("tail") or [])[:160]] for s in runall.get("steps") or []]
        pages["一鍵"].append((f"一鍵總表 · {runall.get('ts', '')} · HEAD {runall.get('head', '')}", ["步驟", "狀態", "rc", "秒", "尾行"], steps, 1))
        for d in runall.get("diag") or []:
            lines = [[ln] for ln in (d.get("fail") or []) + ["──"] + (d.get("tail") or [])]
            pages["VRN"].append((f"診斷 · {d.get('name')} · {d.get('state')} · 全文 {d.get('log', '')}", ["輸出(VIA_OCR_TRACE=1)"], lines, None))
    else:
        pages["一鍵"].append(("一鍵總表", ["狀態"], [["本次不是經一鍵跑的(RUNALL_STEPS_latest.json 不在)"]], None))
    if DBM_HTML.is_file():
        pages["DB"].append(("DB 面板全文(十二張矩陣)", ["檔"], [[str(DBM_HTML)]], None))
    return pages


_CSS = """
:root{--bg:#f6f8fa;--fg:#1f2328;--card:#ffffff;--line:#d0d7de;--acc:#0969da}
@media (prefers-color-scheme: dark){:root{--bg:#0d1117;--fg:#c9d1d9;--card:#161b22;--line:#30363d;--acc:#58a6ff}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:13px/1.4 system-ui,-apple-system,"Segoe UI","Noto Sans TC",sans-serif}
header{position:sticky;top:0;z-index:2;background:var(--card);border-bottom:1px solid var(--line);padding:6px 10px}
h1{font-size:14px;margin:0 0 6px}nav{display:flex;flex-wrap:wrap;gap:4px}
nav button{font:inherit;font-size:12px;padding:3px 10px;border:1px solid var(--line);border-radius:999px;background:transparent;color:var(--fg);cursor:pointer}
nav button[aria-selected=true]{background:var(--acc);border-color:var(--acc);color:#fff}
nav button .n{opacity:.8;margin-left:4px}
main{padding:8px 10px}section[role=tabpanel]{display:none}section[role=tabpanel].on{display:block}
pre.mx{margin:0 0 10px;padding:8px;border-radius:6px;background:#272822;color:#f8f8f2;overflow-x:auto;white-space:pre;
font-family:"Cascadia Mono","Sarasa Mono TC","Noto Sans Mono CJK TC",Consolas,monospace;font-size:11px;line-height:1.22}
footer{padding:6px 10px;font-size:11px;opacity:.7}
"""

_JS = """
(function(){
 var tabs=[].slice.call(document.querySelectorAll('nav button')),pans=[].slice.call(document.querySelectorAll('section[role=tabpanel]'));
 function fit(p){[].slice.call(p.querySelectorAll('pre.mx')).forEach(function(x){var s=11;x.style.fontSize=s+'px';
  while(s>7&&x.scrollWidth>x.clientWidth+1){s-=0.5;x.style.fontSize=s+'px';}});}
 function show(i){tabs.forEach(function(b,k){b.setAttribute('aria-selected',k===i?'true':'false');});
  pans.forEach(function(p,k){p.classList.toggle('on',k===i);});fit(pans[i]);try{location.hash='t'+i;}catch(e){}}
 tabs.forEach(function(b,i){b.addEventListener('click',function(){show(i);});});
 var m=/#t(\\d+)/.exec(location.hash||'');show(m?Math.min(+m[1],tabs.length-1):0);
 var t;window.addEventListener('resize',function(){clearTimeout(t);t=setTimeout(function(){pans.forEach(function(p){if(p.classList.contains('on'))fit(p);});},120);});
})();
"""


def _render_tab(secs: list, width: int, style: dict, cell) -> tuple:
    """一頁 → (HTML 片段, 引擎)。rich 缺席 = 純文字(同內容)。"""
    try:
        from rich import box
        from rich.console import Console
        from rich.table import Table
        from rich.text import Text
    except ImportError:
        chunks = []
        for t, cols, rows, _st in secs:
            lines = [f"== {t} ==", " | ".join(cols)] + [" | ".join(str(c) for c in r) for r in rows or []]
            chunks.append("<pre class='mx'>" + _html.escape("\n".join(lines)) + "</pre>")
        return "".join(chunks), "plain"
    try:
        from rich.terminal_theme import MONOKAI as theme          # 深底高對比:預設主題的 red 在深底幾乎看不見
    except ImportError:
        theme = None
    out = []
    for t, cols, rows, st in secs:
        con = Console(record=True, width=width, file=io.StringIO(), force_terminal=True, color_system="truecolor", legacy_windows=False, soft_wrap=False)
        tb = Table(title=str(t), title_justify="left", title_style="bold cyan", box=box.SIMPLE_HEAVY, header_style="bold", pad_edge=False)
        for c in cols:
            tb.add_column(str(c), overflow="fold")
        for r in rows or [["(無)"] + [""] * (len(cols) - 1)]:
            cells = [cell(x) for x in list(r) + [""] * (len(cols) - len(r))]
            if st is not None and st < len(cells) and style.get(cells[st]):
                cells[st] = Text(cells[st], style=style[cells[st]])
            tb.add_row(*cells)
        con.print(tb)
        out.append("<pre class='mx'>" + con.export_html(theme=theme, inline_styles=True, code_format="{code}") + "</pre>")
    return "".join(out), "rich"


def render(width: int = 150, out: Path = OUT, side_path: Path = SIDE, runall_path: Path = RUNALL, rep: dict | None = None) -> dict:
    tail = sweep_tail()
    style = dict(getattr(tail, "STYLE", {}) or {})
    style.update({"守住": "green", "回歸": "bold red", "未量": "dim", "可加鎖": "cyan"})
    cell = getattr(tail, "_cell", lambda v: "" if v is None else str(v))
    if rep is None:
        side = _load_json(side_path)
        if tail is None or side is None:
            rep = {"sections": [("總覽", ["狀態"], [["ABSENT · " + ("CGC_MDL229 尾版不在" if tail is None else f"側車不在:{side_path}(先跑一次全景)")]], None)],
                   "verdict": "ABSENT", "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "head": ""}
        else:
            rep = tail.build(side)
    vdf, vrn = _load_json(VDF_CHAIN), _load_json(VRN_CHAIN)
    book, book_name = lock_book()
    lock = lock_check(book, lamp_states(rep.get("sections") or []), chain_states(vdf, "id"), chain_states(vrn, "name"))
    runall = _load_json(runall_path)
    pages = build_pages(rep, lock, book_name, runall)
    verdict = "RED" if lock["regress"] else rep.get("verdict", "")
    title = f"VIA 多頁矩陣 · {verdict} · {rep.get('ts', '')} · HEAD {rep.get('head', '')}"
    nav, panels, engine = [], [], "rich"
    for i, name in enumerate(TABS):
        frag, engine = _render_tab(pages[name], width, style, cell) if pages[name] else ("<p>(本頁本次沒有內容)</p>", engine)
        n = len(lock["regress"]) if name == "鎖" else sum(len(s[2] or []) for s in pages[name])
        nav.append(f"<button role='tab' aria-selected='false'>{_html.escape(name)}<span class='n'>{n}</span></button>")
        panels.append(f"<section role='tabpanel' aria-label='{_html.escape(name)}'>{frag}</section>")
    doc = ("<!doctype html><html lang='zh-Hant'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
           f"<title>VIA 多頁矩陣</title><style>{_CSS}</style></head><body><header><h1>{_html.escape(title)}</h1><nav role='tablist'>"
           + "".join(nav) + "</nav></header><main>" + "".join(panels) + "</main>"
           + f"<footer>{ENGINE_TAG} · {engine} · 零 CDN 零外連 · 鎖冊 {_html.escape(book_name or '不在')}</footer><script>{_JS}</script></body></html>")
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    path = out / PAGE_NAME
    path.write_text(doc, encoding="utf-8")
    return {"path": str(path), "engine": engine, "verdict": verdict, "regress": lock["regress"], "add": lock["add"],
            "held": lock["held"], "unmeasured": lock["unmeasured"], "tabs": {t: len(pages[t]) for t in TABS}}


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in a:
        return selftest()
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY", "why": "只經 VCGC(VIA_FROM_VCGC=YES)"}, ensure_ascii=False))
        return 2
    verb = next((x for x in a if not x.startswith("-")), "pages")
    width = int(a[a.index("--width") + 1]) if "--width" in a and a.index("--width") + 1 < len(a) else 150
    r = render(width=width)
    if verb == "lock":
        print(f"  [鎖] 回歸 {len(r['regress'])} · 守住 {r['held']} · 未量 {r['unmeasured']} · 可加鎖 {len(r['add'])}")
        for x in r["regress"]:
            print(f"    回歸 {x}")
        return 1 if r["regress"] else 0
    print(f"  [鎖] 回歸 {len(r['regress'])} · 守住 {r['held']} · 未量 {r['unmeasured']} · 可加鎖 {len(r['add'])}"
          + (" · " + " · ".join(r["regress"][:4]) if r["regress"] else ""))
    print(f"[MatrixPages] {r['engine']} · {r['verdict']} · HTML {r['path']}")
    return 0


def selftest() -> int:
    results = []

    def chk(name, ok, note=""):
        results.append(bool(ok))
        print(f"  [{'OK' if ok else 'FAIL'}] {name}{(' · ' + note) if note else ''}")

    print(f"=== {ENGINE_TAG} 自測(夾具;零網路)===")
    lamps_sec = ("③ VCGC 子系統燈", ["系統", "總燈", "policy", "logic", "engine"],
                 [["VDF", "GREEN", "GREEN", "RED", "GATED"], ["VRN", "GREEN", "GREEN", "GREEN", "NODATA"]], 1)
    lamps = lamp_states([lamps_sec])
    chk("① ③ 燈表 → vdf_logic / vrn_engine …", lamps.get("vdf_logic") == "RED" and lamps.get("vrn_engine") == "NODATA" and lamps.get("vdf_engine") == "GATED")
    book = {"locked": ["vdf_policy", "vdf_logic", "vdf_engine"], "open": ["vrn_logic"],
            "nodes": {"vdf": ["0a", "0b"], "vrn": ["X", "Y"]}, "nodes_open": {"vdf": [], "vrn": ["Z"]}}
    lk = lock_check(book, lamps, {"0a": "GREEN", "0b": "GATED"}, {"X": "GREEN", "Y": "RED", "Z": "GREEN"})
    chk("② 已鎖退回 RED = 回歸(燈與節點都抓)", sorted(lk["regress"]) == ["VRN Y:RED", "燈 vdf_logic:RED"], "; ".join(lk["regress"]))
    chk("③ GATED / 沒量到 = 未量,不算回歸", lk["unmeasured"] == 2 and lk["held"] == 3, f"未量 {lk['unmeasured']} · 守住 {lk['held']}")
    chk("④ 開著的項目這次綠了 = 可加鎖", sorted(lk["add"]) == ["VRN Z", "燈 vrn_logic"], "; ".join(lk["add"]))
    chk("⑤ 回歸排在逐項表最上", lk["rows"][0][3] == "回歸")
    real, name = lock_book()
    chk("⑥ 真鎖冊尾版讀得到、同一項不能又鎖又開", real is not None and not (set(real.get("locked") or []) & set(real.get("open") or [])), str(name))
    rep = {"verdict": "AMBER", "ts": "2026-09-28 20:00:00", "head": "abc1234",
           "sections": [("① 總判 KPI", ["步驟", "狀態"], [["① VCGC", "GREEN"]], 1), lamps_sec,
                        ("⑥ VDF 鏈跑器", ["狀態", "站"], [], 0), ("⑦ VRN 鏈跑器", ["狀態", "節點"], [["RED", "Y"]], 0),
                        ("⑪ Ⓐ 工具註冊", ["燈", "檔"], [["GREEN", "a.py"]], 0)]}
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        ra = td / "runall.json"
        ra.write_text(json.dumps({"ts": "t", "head": "h", "steps": [{"title": "① VCGC", "state": "OK", "rc": 0, "sec": 1.0, "tail": ["x"]}],
                                  "diag": [{"name": "Y", "state": "RED", "fail": ["[FAIL] ㉜ 詳"], "tail": ["最後一行"], "log": "d.log"}]}), encoding="utf-8")
        global VDF_CHAIN, VRN_CHAIN
        keep = (VDF_CHAIN, VRN_CHAIN)
        vc, rc_ = td / "vdf.json", td / "vrn.json"
        vc.write_text(json.dumps({"stages": [{"id": "0a", "state": "GREEN"}]}), encoding="utf-8")
        rc_.write_text(json.dumps({"stages": [{"name": "Y", "state": "RED"}]}), encoding="utf-8")
        VDF_CHAIN, VRN_CHAIN = vc, rc_
        try:
            r = render(width=120, out=td / "out", runall_path=ra, rep=rep)
        finally:
            VDF_CHAIN, VRN_CHAIN = keep
        doc = Path(r["path"]).read_text(encoding="utf-8")
        chk("⑦ 九頁都在(總覽 · 鎖 · VCGC · VDF · VRN · DB · 橋與全景 · 工具 · 一鍵)", doc.count("role='tabpanel'") == 9 and all(f">{t}<" in doc for t in TABS))
        chk("⑧ 零 CDN 零外連(沒有 http(s):// 與外部 src)", "http://" not in doc and "https://" not in doc and " src=" not in doc)
        chk("⑨ 字級小 + 自動縮放腳本在(11px 起,縮到 7px)", "font-size:11px" in doc and "scrollWidth" in doc and "s>7" in doc)
        chk("⑩ 診斷與一鍵總表上頁;矩陣是 rich 匯出(或 rich 缺席時照實 plain)", "㉜ 詳" in doc and "① VCGC" in doc and r["engine"] in ("rich", "plain"), r["engine"])
    keep = os.environ.pop("VIA_FROM_VCGC", None)
    denied = main(["pages"]) == 2
    if keep is not None:
        os.environ["VIA_FROM_VCGC"] = keep
    chk("⑪ 不經 VCGC 就拒跑", denied)
    ok = all(results)
    print(f"  [計] {ENGINE_TAG} 自測 {sum(results)}/{len(results)} · {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
