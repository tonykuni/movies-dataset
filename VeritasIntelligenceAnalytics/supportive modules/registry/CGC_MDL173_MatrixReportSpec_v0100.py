#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
CGC_MDL173_MatrixReportSpec v0100 — 矩陣式報告排版規格(批672)
====================================================================
操作員令(批672):「以後跑完都要生成矩陣式報告 BY RICH,字小,優化矩陣排版規格」。

為什麼這支要存在,而不是各自把 CSS 再抄一遍:
  批669–671 之間我一口氣做了四支會落頁的引擎——
    MDL169 六域現況 · MDL170 VDF 鏈 · MDL171 全景計畫 · MDL172 VRN 鏈
  四支各自帶一份 `css = ("body{background:#0f1116;...")`。四份幾乎一樣,但**不是同一份**:
  字級 13px / 12.5px / 13px 各有各的,深淺配色只有一支有,手機寬度只有一支顧到。
  「排版規格」如果活在四個地方,它就不是規格,是四個人各自的習慣(L30 一個出處)。
  操作員說「字小」的那一刻,要改的地方有四個——這就是規格散掉的代價。

所以這支**只做一件事**:把「矩陣式報告長什麼樣」收成一份,讓那四支去呼叫。
它不產生任何新資料、不判任何燈、不碰任何庫——**它是排版,不是引擎**。

BY RICH 的意思(操作員原話)是:**表由 rich 畫**。
  這支不自己拼 <table>,它給 rich 一個 `code_format`,
  讓 `Console.export_html(inline_styles=True)` 直接吐出**整頁**。
  rich 畫矩陣,這支管頁殼(字級·密度·深淺·手機寬·三顆鍵)。
  inline_styles=True → 零 class 依賴 → 零 CDN 零外連,file:// 直開(L100)。

排版規格(SPEC,可用 `--spec` 印出來對):
  字小      矩陣 10.5px / 行高 1.22(原本 12.5–13px;同一張頁多塞約三成的列)
  密度      rich padding (0,1) · box=SIMPLE_HEAD(只有表頭一條線,不畫格子)
  寬        Console width 200:矩陣**寧可橫向捲,也不要讓欄位換行**——
            換行的矩陣對不齊,對不齊的矩陣就不是矩陣了
  對齊      數字欄 right + tabular-nums;態欄固定寬置中
  深淺      prefers-color-scheme 兩套;**不給切換鈕**(零彈窗律,頁上不長 UI)
  手機      橫向捲條只包矩陣,頁身不橫捲
  鍵        MD / JSON / 複製 三顆;MD 由呼叫端傳進來,**JS 永不自己拼第二份**(L30)

用法:
  from CGC_MDL173_MatrixReportSpec_v0100 import console, table, page   # 給四支引擎呼叫
  via-matrixspec            → 印排版規格(可貼給操作員對)
  via-matrixspec demo       → 落一張示範頁(看得到字級與密度)
  via-matrixspec --selftest → 二十檢(沙盒零網路)
誠實 rc:0 GREEN · 1 RED · 2 NODATA(rich 缺席=缺料不是壞掉)· 3 ABSENT
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
import os
import sys
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
BATCH = "批672"

# ── 一份規格(L30)────────────────────────────────────────────────────
SPEC: dict = {
    "version": "v0100",
    "batch": BATCH,
    "why": "四支落頁引擎各帶一份 CSS,字級 13/12.5/13 各有各的;規格散在四處就不是規格",
    "font": {
        "matrix_px": 10.5,      # 操作員令「字小」——原本 12.5–13px
        "matrix_line": 1.22,
        "body_px": 12,
        "h1_px": 16,
        "h2_px": 12.5,
        "kpi_px": 15,
        "note_px": 10.5,
        "stack": "ui-monospace,SFMono-Regular,Consolas,'Noto Sans Mono CJK TC',monospace",
    },
    "matrix": {
        "console_width": 200,   # 寧可橫捲,也不要讓欄位換行
        "box": "SIMPLE_HEAD",   # 只有表頭一條線,不畫格子
        "padding": [0, 1],
        "cell_pad": "2px 7px",   # HTML 矩陣的格內留白;跟 rich 的 (0,1) 對齊視覺密度
        "show_lines": False,
        "num_justify": "right",
        "num_variant": "tabular-nums",
        "state_width": 7,
    },
    "page": {
        "one_file": True,       # 一頁一檔:零外連零 CDN,file:// 直開(L100)
        "color_scheme": ["dark", "light"],
        "scheme_toggle": False,  # 零彈窗律:頁上不長 UI
        "mobile_scroll": "matrix_only",
        "max_width_px": 1680,
        "buttons": ["MD", "JSON", "複製"],
        "md_source": "caller",  # MD 由呼叫端傳進來,JS 永不自己拼(L30)
    },
    "states": {   # 誠實六態 + 資料層兩態;顏色在這裡定一次
        "GREEN": "#9ece6a", "RED": "#f7768e", "NODATA": "#e0af68",
        "GATED": "#7dcfff", "ABSENT": "#9aa5ce", "SKIP": "#6b7280",
        "YELLOW": "#e0af68", "NA": "#9aa5ce",
    },
}


def rel(p: Path | str) -> str:
    try:
        return str(Path(p).resolve().relative_to(VIA)).replace("\\", "/")
    except Exception:
        return str(p)


# ── rich 掛載:缺席是缺料不是壞掉 ───────────────────────────────────
def rich_ok() -> tuple[bool, str]:
    try:
        import rich  # noqa: F401
        from importlib.metadata import version
        return True, f"rich {version('rich')}"
    except Exception as exc:
        return False, f"rich 缺席({type(exc).__name__})——缺料不是壞掉"


def console(width: int | None = None, record: bool = True):
    """規格內的 Console。矩陣寧可橫捲也不換行,所以 width 走 SPEC。"""
    from rich.console import Console
    return Console(record=record, width=width or SPEC["matrix"]["console_width"],
                   soft_wrap=False, highlight=False)


def table(title: str = "", columns: list | None = None, caption: str = ""):
    """規格內的 Table。columns 每項:字串,或 {name, justify, width, no_wrap, style}。"""
    from rich import box as _box
    from rich.table import Table
    t = Table(title=title or None, caption=caption or None,
              box=getattr(_box, SPEC["matrix"]["box"]),
              padding=tuple(SPEC["matrix"]["padding"]),
              show_lines=SPEC["matrix"]["show_lines"],
              title_style="bold", header_style="bold",
              caption_style="dim", expand=False)
    for c in (columns or []):
        if isinstance(c, str):
            t.add_column(c, overflow="fold")
        else:
            t.add_column(c.get("name", ""), justify=c.get("justify", "left"),
                         width=c.get("width"), no_wrap=c.get("no_wrap", False),
                         style=c.get("style"), overflow=c.get("overflow", "fold"))
    return t


# ── 頁殼 ──────────────────────────────────────────────────────────────
#   rich 的 export_html 會把 code_format.format(code=..., stylesheet=..., ...) 跑一次,
#   所以**頁殼裡的大括號會被 .format 吃掉**。作法:頁殼只放哨兵,export 完再換進去。
#   (批664 實錄同一類坑:拿 regex 去讀 regex,永遠在跳脫上斷——改走「先出再換」。)
_SENTINEL = {"title": "@@VIA_TITLE@@", "css": "@@VIA_CSS@@",
             "head": "@@VIA_HEAD@@", "foot": "@@VIA_FOOT@@"}

_CODE_FORMAT = (
    "<!DOCTYPE html><html lang='zh-Hant'><head><meta charset='utf-8'>"
    "<meta name='viewport' content='width=device-width,initial-scale=1'>"
    f"<title>{_SENTINEL['title']}</title>"
    "<style>{stylesheet}\nbody{{color:{foreground};background-color:{background}}}\n"
    f"{_SENTINEL['css']}</style></head><body>"
    f"{_SENTINEL['head']}"
    "<div class='mwrap'><pre class='m'><code>{code}</code></pre></div>"
    f"{_SENTINEL['foot']}"
    "</body></html>"
)


def css() -> str:
    f, m, pg = SPEC["font"], SPEC["matrix"], SPEC["page"]
    st = SPEC["states"]
    lamps = "".join(f".s-{k}{{color:{v};font-weight:700}}" for k, v in st.items())
    return (
        ":root{--bg:#0f1116;--fg:#d8dee9;--dim:#8b949e;--line:#2b313c;--acc:#7dcfff}"
        "@media(prefers-color-scheme:light){:root{--bg:#fbfbfd;--fg:#1f2430;"
        "--dim:#5b6472;--line:#d6dae2;--acc:#1f6feb}}"
        f"html,body{{background:var(--bg);color:var(--fg);margin:0;"
        f"font-family:{f['stack']};font-size:{f['body_px']}px}}"
        f".wrap{{max-width:{pg['max_width_px']}px;margin:0 auto;padding:16px 18px 40px}}"
        f"h1{{font-size:{f['h1_px']}px;margin:0 0 3px;letter-spacing:.2px}}"
        f"h2{{font-size:{f['h2_px']}px;margin:18px 0 5px;color:var(--acc)}}"
        f".sub{{color:var(--dim);font-size:{f['note_px']}px;margin:0 0 12px;line-height:1.5}}"
        # 矩陣本體:字小 + 密 + 只有矩陣自己橫捲
        ".mwrap{overflow-x:auto;overflow-y:hidden;-webkit-overflow-scrolling:touch;"
        "border:1px solid var(--line);border-radius:6px;padding:8px 10px;margin:0 0 14px}"
        f"pre.m{{margin:0;font-size:{f['matrix_px']}px;line-height:{f['matrix_line']};"
        f"font-variant-numeric:{m['num_variant']};white-space:pre;"
        f"font-family:{f['stack']}}}"
        "pre.m code{font-family:inherit;font-size:inherit}"
        # KPI 條
        ".kpi{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 12px}"
        ".kpi div{border:1px solid var(--line);border-radius:6px;padding:5px 10px;"
        f"font-size:{f['note_px']}px;color:var(--dim)}}"
        f".kpi b{{display:block;font-size:{f['kpi_px']}px;color:var(--fg)}}"
        # 三顆鍵
        ".bar{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin:0 0 12px}"
        ".bar button{background:transparent;color:var(--fg);border:1px solid var(--line);"
        f"border-radius:6px;padding:5px 11px;font:inherit;font-size:{f['note_px']}px;"
        "cursor:pointer}"
        ".bar button:hover{border-color:var(--acc);color:var(--acc)}"
        f"#vmsg{{color:#9ece6a;font-size:{f['note_px']}px}}"
        f".law{{color:var(--dim);font-size:{f['note_px']}px;border-left:3px solid var(--line);"
        "padding-left:9px;margin:10px 0;line-height:1.55}"
        # HTML 矩陣:有些矩陣是逐列舉證(81 列 × 7 欄),排成 <table> 比排成
        #   預格式化文字好讀。兩種矩陣走**同一份字級與密度**,規格才是一份。
        f"table.m{{border-collapse:collapse;width:100%;font-size:{f['matrix_px']}px;"
        f"line-height:{f['matrix_line']};font-variant-numeric:{m['num_variant']}}}"
        "table.m th,table.m td{border-bottom:1px solid var(--line);"
        f"padding:{m['cell_pad']};text-align:left;vertical-align:top}}"
        "table.m th{position:sticky;top:0;background:var(--bg);color:var(--dim);"
        "font-weight:700;white-space:nowrap}"
        "table.m td.n{text-align:right;white-space:nowrap}"
        "table.m td.c{text-align:center;white-space:nowrap}"
        "table.m tbody tr:hover{background:rgba(125,207,255,.07)}"
        + lamps +
        f"@media(max-width:640px){{.wrap{{padding:12px 10px 32px}}"
        f"pre.m{{font-size:{f['matrix_px'] - 1}px}}"
        f"table.m{{font-size:{f['matrix_px'] - 1}px}}}}"
    )


def _js(md: str, payload: dict, stem: str) -> str:
    """三顆鍵。MD 是呼叫端給的那一份——**JS 不自己拼第二份**(L30)。"""
    return (
        "<script>\n"
        "const VIA_MD=" + json.dumps(md, ensure_ascii=False) + ";\n"
        "const VIA_JSON=" + json.dumps(payload, ensure_ascii=False) + ";\n"
        "const VIA_STEM=" + json.dumps(stem, ensure_ascii=False) + ";\n"
        "function vsay(t){const m=document.getElementById('vmsg');"
        "if(m){m.textContent=t;setTimeout(()=>{m.textContent='';},2600);}}\n"
        "function vdl(txt,ext,mime){try{const b=new Blob([txt],{type:mime});"
        "const u=URL.createObjectURL(b);const a=document.createElement('a');"
        "a.href=u;a.download=VIA_STEM+ext;document.body.appendChild(a);a.click();"
        "a.remove();setTimeout(()=>URL.revokeObjectURL(u),1500);vsay('已存 '+VIA_STEM+ext);}"
        "catch(e){vsay('存檔失敗:'+e.message);}}\n"
        "function vmd(){vdl(VIA_MD,'.md','text/markdown;charset=utf-8');}\n"
        "function vjson(){vdl(JSON.stringify(VIA_JSON,null,2),'.json',"
        "'application/json;charset=utf-8');}\n"
        "function vcopy(){const t=VIA_MD;"
        "if(navigator.clipboard&&window.isSecureContext){"
        "navigator.clipboard.writeText(t).then(()=>vsay('MD 已複製'),()=>vfall(t));}"
        "else{vfall(t);}}\n"
        "function vfall(t){const a=document.createElement('textarea');a.value=t;"
        "a.style.position='fixed';a.style.opacity='0';document.body.appendChild(a);"
        "a.select();try{document.execCommand('copy');vsay('MD 已複製');}"
        "catch(e){vsay('複製失敗,請用 MD 鍵下載');}a.remove();}\n"
        "</script>"
    )


def _head_foot(title, subtitle, kpis, law, md, payload, stem) -> tuple[str, str]:
    """頁殼的頭與尾。**rich 矩陣與 HTML 矩陣共用這一個殼**——
    兩個殼就是兩份規格,操作員說「字小」的時候又要改兩個地方。"""
    head = ["<div class='wrap'>", f"<h1>{html.escape(title)}</h1>"]
    if subtitle:
        head.append(f"<div class='sub'>{html.escape(subtitle)}</div>")
    if kpis:
        head.append("<div class='kpi'>" + "".join(
            f"<div><b class='s-{html.escape(str(k.get('state','')))}'>"
            f"{html.escape(str(k.get('value','')))}</b>{html.escape(str(k.get('label','')))}</div>"
            for k in kpis) + "</div>")
    head.append("<div class='bar'>"
                "<button onclick='vmd()'>⬇ MD</button>"
                "<button onclick='vjson()'>⬇ JSON</button>"
                "<button onclick='vcopy()'>⧉ 複製 MD</button>"
                "<span id='vmsg'></span></div>")
    foot = []
    if law:
        foot.append(f"<div class='law'>{law}</div>")
    foot.append(f"<div class='sub'>排版規格 CGC_MDL173 {SPEC['version']}({SPEC['batch']})"
                f" · 矩陣 {SPEC['font']['matrix_px']}px · 零 CDN 零外連 · file:// 直開</div>")
    foot.append("</div>" + _js(md, payload or {}, stem))
    return "".join(head), "".join(foot)


def page(con, *, title: str, subtitle: str = "", md: str = "",
         payload: dict | None = None, kpis: list | None = None,
         law: str = "", out: Path | None = None) -> Path:
    """rich 車道:把 rich 畫好的矩陣包進規格頁殼,落一個檔。回落點。

    con     已經 print 過矩陣的 Console(record=True)
    md      呼叫端產的 Markdown —— 頁上那顆 MD 鍵吐的就是**這一份**
    payload 呼叫端的 JSON 報告本體
    """
    out = out or (VIA / "VIA_Reports" / "matrix" / "VIA_MATRIX_demo.html")
    head, foot = _head_foot(title, subtitle, kpis, law, md, payload or {}, out.stem)
    raw = con.export_html(inline_styles=True, code_format=_CODE_FORMAT)
    raw = (raw.replace(_SENTINEL["title"], html.escape(title))
              .replace(_SENTINEL["css"], css())
              .replace(_SENTINEL["head"], head)
              .replace(_SENTINEL["foot"], foot))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(raw, encoding="utf-8")
    return out


def html_table(headers: list, rows: list, *, caption: str = "",
               num_cols: set | None = None, center_cols: set | None = None) -> str:
    """HTML 車道的一張矩陣。字級/密度/對齊全部出自 SPEC(與 rich 那條同一份)。

    rows 的每一格可以是字串,或 {"t": 文字, "s": 態}(態會套 SPEC 的燈色)。
    """
    num_cols, center_cols = (num_cols or set()), (center_cols or set())
    out = ["<div class='mwrap'>"]
    if caption:
        out.append(f"<h2>{html.escape(caption)}</h2>")
    out.append("<table class='m'><thead><tr>"
               + "".join(f"<th>{html.escape(str(h))}</th>" for h in headers)
               + "</tr></thead><tbody>")
    for r in rows:
        tds = []
        for i, cell in enumerate(r):
            cls = "n" if i in num_cols else ("c" if i in center_cols else "")
            if isinstance(cell, dict):
                txt, st = str(cell.get("t", "")), str(cell.get("s", ""))
                inner = (f"<span class='s-{html.escape(st)}'>{html.escape(txt)}</span>"
                         if st in SPEC["states"] else html.escape(txt))
            else:
                inner = html.escape(str(cell))
            tds.append(f"<td class='{cls}'>{inner}</td>" if cls else f"<td>{inner}</td>")
        out.append("<tr>" + "".join(tds) + "</tr>")
    out.append("</tbody></table></div>")
    return "".join(out)


def page_html(body: str, *, title: str, subtitle: str = "", md: str = "",
              payload: dict | None = None, kpis: list | None = None,
              law: str = "", out: Path | None = None) -> Path:
    """HTML 車道:呼叫端自己拼好矩陣片段(建議用 html_table),這裡只給殼。
    與 rich 車道**共用同一個 _head_foot 與同一份 css()**——規格是一份。"""
    out = out or (VIA / "VIA_Reports" / "matrix" / "VIA_MATRIX_demo.html")
    head, foot = _head_foot(title, subtitle, kpis, law, md, payload or {}, out.stem)
    raw = ("<!DOCTYPE html><html lang='zh-Hant'><head><meta charset='utf-8'>"
           "<meta name='viewport' content='width=device-width,initial-scale=1'>"
           f"<title>{html.escape(title)}</title><style>{css()}</style></head><body>"
           f"{head}{body}{foot}</body></html>")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(raw, encoding="utf-8")
    return out


# ── 印規格 ────────────────────────────────────────────────────────────
def print_spec() -> int:
    ok, why = rich_ok()
    if not ok:
        print(f"  [NODATA] {why}")
        return 2
    con = console(record=False, width=110)
    t = table("矩陣式報告排版規格(CGC_MDL173 " + SPEC["version"] + ")",
              [{"name": "面", "width": 6}, {"name": "鍵", "width": 18},
               {"name": "值", "justify": "right", "width": 22},
               {"name": "為什麼是這個值"}])
    rows = [
        ("字", "matrix_px", SPEC["font"]["matrix_px"], "操作員令「字小」;原本四支各自 12.5–13px"),
        ("字", "matrix_line", SPEC["font"]["matrix_line"], "同一張頁多塞約三成的列"),
        ("矩陣", "console_width", SPEC["matrix"]["console_width"], "寧可橫捲也不讓欄位換行——換行就對不齊"),
        ("矩陣", "box", SPEC["matrix"]["box"], "只有表頭一條線;畫滿格子會把字擠小又更難讀"),
        ("矩陣", "padding", str(tuple(SPEC["matrix"]["padding"])), "上下 0 左右 1:密度來自這裡"),
        ("矩陣", "num_variant", SPEC["matrix"]["num_variant"], "數字等寬才對得起來"),
        ("頁", "one_file", SPEC["page"]["one_file"], "零 CDN 零外連;file:// 直開(L100)"),
        ("頁", "scheme_toggle", SPEC["page"]["scheme_toggle"], "零彈窗律:頁上不長 UI,跟系統走"),
        ("頁", "mobile_scroll", SPEC["page"]["mobile_scroll"], "只有矩陣橫捲,頁身不捲"),
        ("鍵", "md_source", SPEC["page"]["md_source"], "MD 由引擎產一份給頁;JS 永不自己拼第二份(L30)"),
    ]
    for r in rows:
        t.add_row(*[str(x) for x in r])
    con.print(t)
    t2 = table("誠實態配色(一次定在這裡)",
               [{"name": "態", "width": 8}, {"name": "色", "width": 10}, {"name": "意思"}])
    mean = {"GREEN": "量到而且過了", "RED": "真的壞", "NODATA": "量不到/缺料/逾時",
            "GATED": "等閘——同意閘 AI 永不代設", "ABSENT": "冊上有、樹上沒有",
            "SKIP": "這一輪不跑(具名列出,不偷偷消失)",
            "YELLOW": "資料層:有值但沒把握", "NA": "資料層:天生算不出"}
    for k, v in SPEC["states"].items():
        t2.add_row(f"[{v}]{k}[/]", v, mean.get(k, ""))
    con.print(t2)
    print(f"  [計] 規格 {SPEC['version']} · {why} · 呼叫端:MDL169/170/171/172")
    return 0


def demo(out: Path | None = None) -> int:
    ok, why = rich_ok()
    if not ok:
        print(f"  [NODATA] {why}")
        return 2
    con = console()
    t = table("示範矩陣(看字級與密度)",
              [{"name": "站", "width": 26}, {"name": "態", "width": SPEC["matrix"]["state_width"],
                                             "justify": "center"},
               {"name": "秒", "justify": "right", "width": 6},
               {"name": "量到什麼"}])
    demo_rows = [("六域現況矩陣", "GREEN", "2.1", "ENV/LIBS/SSOT/TOOLS/VDF/VRN 六域逐格"),
                 ("VDF 獨立鏈", "GATED", "0.3", "要觸網的站在等同意閘——AI 永不代設"),
                 ("全景批次修復計畫", "NODATA", "1.8", "只有缺料;真缺 0,沒有波要排"),
                 ("VRN 六層鏈", "GREEN", "29.2", "層間依序層內並行;44 節點量到 32"),
                 ("沒有自測門的支", "SKIP", "0.0", "沒敲——回音不是綠也不是紅")]
    for n, s, sec, note in demo_rows:
        t.add_row(n, f"[{SPEC['states'][s]}]{s}[/]", sec, note)
    con.print(t)
    md = ("# 示範矩陣\n\n| 站 | 態 | 秒 | 量到什麼 |\n|---|---|---|---|\n"
          + "".join(f"| {n} | {s} | {sec} | {note} |\n" for n, s, sec, note in demo_rows))
    out = out or (VIA / "VIA_Reports" / "matrix" / "VIA_MATRIX_SPEC_demo.html")
    p = page(con, title="矩陣式報告排版規格 · 示範頁",
             subtitle=f"{datetime.now():%Y-%m-%d %H:%M} · CGC_MDL173 {SPEC['version']}"
                      f" · 矩陣 {SPEC['font']['matrix_px']}px · 表 BY RICH",
             md=md, payload={"spec": SPEC, "rows": demo_rows},
             kpis=[{"label": "示範列", "value": len(demo_rows), "state": "GREEN"},
                   {"label": "字級", "value": SPEC["font"]["matrix_px"], "state": "GREEN"}],
             law="**這一頁不判任何燈。** 它只證明排版規格長什麼樣——"
                 "四支落頁引擎共用這一份,操作員說「字小」的時候只要改這裡一個數字。",
             out=out)
    print(f"  [頁] {rel(p)}")
    return 0


# ── 自測 ──────────────────────────────────────────────────────────────
def selftest() -> int:
    import re
    import tempfile
    t0 = time.time()
    fails: list[str] = []

    def chk(name, ok, note=""):
        print(f"  [{'OK' if ok else 'FAIL'}] {name} {note}")
        if not ok:
            fails.append(name)

    ok, why = rich_ok()
    if not ok:
        print(f"  [NODATA] {why} —— 缺料不是壞掉")
        return 2
    chk("rich 在位", True, f"({why})")

    con = console()
    t = table("咬用矩陣", [{"name": "甲", "width": 10},
                           {"name": "乙", "justify": "right", "width": 8}, {"name": "丙"}])
    t.add_row("一", "1", "[#9ece6a]GREEN[/]")
    t.add_row("二", "22", "[#f7768e]RED[/]")
    con.print(t)
    md = "# 咬用\n\n| 甲 | 乙 |\n|---|---|\n| 一 | 1 |\n"
    payload = {"k": "v", "brace": "{not a format placeholder}", "n": 2}
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "BITE_v0100.html"
        p = page(con, title="咬用頁", subtitle="沙盒",
                 md=md, payload=payload,
                 kpis=[{"label": "列", "value": 2, "state": "GREEN"}],
                 law="律句", out=out)
        h = p.read_text(encoding="utf-8")

    # ① 一頁一檔:零外連零 CDN
    #   第一版我寫「'cdn' not in h」——結果它咬到的是頁尾自己那句「零 CDN 零外連」。
    #   **宣告零 CDN 的那句話本身被當成 CDN**(批664 同一類自我指涉坑)。
    #   量得準的是「有沒有真的往外指」:外連屬性、@import、以及已知 CDN 主機名。
    ext = re.findall(r"(?:src|href)\s*=\s*['\"](?:https?:)?//[^'\"]+", h)
    imp = re.findall(r"@import\s+(?:url\()?['\"]?(?:https?:)?//", h)
    hosts = [x for x in ("cdn.jsdelivr", "cdnjs.cloudflare", "unpkg.com",
                         "ajax.googleapis", "fonts.googleapis", "fonts.gstatic")
             if x in h.lower()]
    chk("零外連零 CDN(一頁一檔)", not ext and not imp and not hosts,
        f"(外連 {len(ext)} · @import {len(imp)} · CDN 主機 {hosts})")
    # ② 字小:規格裡的字級真的印進頁裡,而且 ≤ 11px
    chk("字小(矩陣字級出自 SPEC 且 ≤11px)",
        f"font-size:{SPEC['font']['matrix_px']}px" in h and SPEC["font"]["matrix_px"] <= 11,
        f"({SPEC['font']['matrix_px']}px)")
    # ③ 表 BY RICH:頁上的矩陣是 rich 吐的(inline style 的 span),不是我自己拼 <table>
    chk("表 BY RICH(rich 的 pre/code,不是手拼 table)",
        "<pre class='m'><code>" in h and "<span style=" in h and "<table" not in h,
        f"(span {h.count('<span style=')})")
    # ④ 三顆鍵在位
    chk("三顆鍵在位(MD/JSON/複製)",
        all(s in h for s in ("vmd()", "vjson()", "vcopy()")) and h.count("<button") == 3,
        f"(button {h.count('<button')})")
    # ⑤ MD 是呼叫端那一份,JS 不自己拼
    chk("頁上 MD = 呼叫端傳進來的同一份(JS 不自己拼)",
        json.dumps(md, ensure_ascii=False) in h and "const VIA_MD=" in h)
    # ⑥ JSON 原樣帶得走(L96),而且大括號沒被 .format 吃掉
    m = re.search(r"const VIA_JSON=(.*?);\nconst VIA_STEM=", h, re.S)
    got = json.loads(m.group(1)) if m else None
    chk("JSON 原樣帶得走(大括號沒被 format 吃掉)", got == payload, f"({got})")
    # ⑦ 深淺兩套 + 不給切換鈕(零彈窗)
    chk("深淺兩套且不長切換 UI",
        "prefers-color-scheme:light" in h and SPEC["page"]["scheme_toggle"] is False)
    # ⑧ 手機:只有矩陣橫捲
    chk("只有矩陣橫捲,頁身不捲",
        ".mwrap{overflow-x:auto" in h and "@media(max-width:640px)" in h)
    # ⑨ 數字等寬
    chk("數字等寬(tabular-nums)", f"font-variant-numeric:{SPEC['matrix']['num_variant']}" in h)
    # ⑩ 規格是一份:頁上印的字級 = SPEC 的字級(改 SPEC 才會變)
    chk("頁尾具名規格版本(改 SPEC 才會變)",
        f"CGC_MDL173 {SPEC['version']}" in h and f"{SPEC['font']['matrix_px']}px" in h)
    # ⑪ 標題有跳脫(不是把 < 直接吐出去)
    con2 = console()
    con2.print("x")
    with tempfile.TemporaryDirectory() as td:
        p2 = page(con2, title="<b>注入</b>", md="m", payload={}, out=Path(td) / "X.html")
        h2 = p2.read_text(encoding="utf-8")
    chk("標題跳脫(HTML 不被注入)", "&lt;b&gt;注入&lt;/b&gt;" in h2 and "<b>注入</b>" not in h2)
    # ⑫ 矩陣密度:box 與 padding 出自 SPEC,不是各自寫死
    from rich import box as _box
    tt = table("x", ["a"])
    chk("矩陣密度出自 SPEC(box/padding)",
        tt.box is getattr(_box, SPEC["matrix"]["box"])
        and tuple(tt.padding) == (SPEC["matrix"]["padding"][0], SPEC["matrix"]["padding"][1],
                                  SPEC["matrix"]["padding"][0], SPEC["matrix"]["padding"][1]),
        f"({SPEC['matrix']['box']} · {tuple(tt.padding)})")
    # ⑬ 寬度出自 SPEC:矩陣不換行
    chk("Console 寬度出自 SPEC(矩陣不換行)",
        console().width == SPEC["matrix"]["console_width"], f"({console().width})")
    # ⑭ 負向:把字級改大,第②檢必須敗——不敗就是那一檢沒咬住
    _keep = SPEC["font"]["matrix_px"]
    try:
        SPEC["font"]["matrix_px"] = 99
        con3 = console()
        con3.print("y")
        with tempfile.TemporaryDirectory() as td:
            h3 = page(con3, title="t", md="m", payload={},
                      out=Path(td) / "Y.html").read_text(encoding="utf-8")
        bites = ("font-size:99px" in h3)
    finally:
        SPEC["font"]["matrix_px"] = _keep
    chk("負向:改 SPEC 字級,頁上跟著變(規格真的是一份)", bites, f"(99px→{bites})")
    # ⑮ 這支不碰庫不判燈:源碼裡不准出現 duckdb / 判燈動詞
    src = Path(__file__).read_text(encoding="utf-8").split("def selftest(")[0]
    needle = "duck" + "db"
    chk("排版不是引擎(不碰庫)", needle not in src.lower(), "")
    # ⑯ 零網路
    chk("零網路(不 import requests/urllib.request)",
        "import requests" not in src and "urllib.request" not in src)
    # ⑰ 落點在 VIA_Reports(資料不進 git)
    chk("預設落點在 VIA_Reports(.gitignore 內)",
        "VIA_Reports" in src and str(VIA / "VIA_Reports") not in h)

    # ⑱ 負向:塞一條真外連進去,第①檢要咬得住。
    #   ——不然它只是在替我數 0,不是在替我把關(批671 LL320)。
    _bad = h.replace("</body>",
                     "<script src='//cdn.jsdelivr.net/npm/x.js'></script></body>")
    _e = re.findall(r"(?:src|href)\s*=\s*['\"](?:https?:)?//[^'\"]+", _bad)
    _hosts = [x for x in ("cdn.jsdelivr",) if x in _bad.lower()]
    chk("負向:塞一條真外連,零外連檢要敗", bool(_e) and bool(_hosts),
        f"(外連 {len(_e)} · 主機 {_hosts})")
    # ⑲ HTML 車道:與 rich 車道**共用同一個殼與同一份 css()**。
    #   兩個殼 = 兩份規格,操作員說「字小」時又要改兩個地方(這支存在的全部理由)。
    body = html_table(["站", "態", "秒"],
                      [["甲", {"t": "GREEN", "s": "GREEN"}, "1.0"],
                       ["乙", {"t": "RED", "s": "RED"}, "2.0"]],
                      caption="HTML 車道矩陣", num_cols={2}, center_cols={1})
    with tempfile.TemporaryDirectory() as td:
        h4 = page_html(body, title="HTML 車道", subtitle="沙盒", md=md, payload=payload,
                       kpis=[{"label": "列", "value": 2, "state": "GREEN"}],
                       out=Path(td) / "H_v0100.html").read_text(encoding="utf-8")
    same_shell = (css() in h4 and css() in h
                  and "<div class='bar'>" in h4 and "const VIA_MD=" in h4
                  and f"CGC_MDL173 {SPEC['version']}" in h4)
    chk("HTML 車道與 rich 車道共用同一個殼與同一份 css()", same_shell)
    # ⑳ html_table:態套到 SPEC 的燈色,數字欄靠右
    chk("html_table 的態套燈色 · 數字欄靠右",
        "class='s-GREEN'" in h4 and "class='s-RED'" in h4 and "<td class='n'>" in h4
        and f"table.m{{border-collapse:collapse;width:100%;font-size:{SPEC['font']['matrix_px']}px" in h4)
    n = 20 - len(fails)
    print(f"  [計] 二十檢 OK {n} · FAIL {len(fails)} · {round(time.time() - t0, 1)}s")
    return 1 if fails else 0


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in a:
        print("=== 矩陣式報告排版規格 v0100 · 二十檢(沙盒零網路)===")
        return selftest()
    verb = next((x for x in a if not x.startswith("-")), "spec")
    if verb == "demo":
        rc = demo()
        if rc == 0 and not os.environ.get("VIA_NO_OPEN"):
            try:
                import webbrowser
                webbrowser.open((VIA / "VIA_Reports" / "matrix"
                                 / "VIA_MATRIX_SPEC_demo.html").as_uri())
            except Exception:
                pass
        return rc
    if verb not in ("spec", "demo"):
        print(f"  [用法] spec | demo | --selftest(收到 {verb!r})")
        return 2
    return print_spec()


if __name__ == "__main__":
    sys.exit(main())
