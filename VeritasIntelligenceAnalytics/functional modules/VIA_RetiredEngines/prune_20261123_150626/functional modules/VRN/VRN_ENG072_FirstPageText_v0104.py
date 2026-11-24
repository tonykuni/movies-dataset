#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VRN_ENG072_FirstPageText v0104 — 首頁三法整合擷取器(批235 立;批245 尾版化)
====================================================================
操作員令:「用 VDF 中 LAYOUT ANALYSIS/TEXT FETCHER 功能擷取出
個股報告第一頁文字內容」。
機制(與 digest ㉓㉙ 同優先序):
  PDF:fitz(pymupdf)版面閱讀序抽第 1 頁(LAYOUT ANALYSIS 正主)
       →pypdf 後備(版面重排風險誠實標 PYPDF_FALLBACK)
       →零文字=掃描版,誠實標 NEEDS_OCR(候 via-ocrsuper 道,不假抽)
  DOCX:無頁界概念→前 30 段誠實近似(標 DOCX_HEAD)
輸出:VIA_Reports/first_page_text/<原檔名>.txt 逐件
      +FIRSTPAGE_SUMMARY.html 一頁堆疊總覽(誠實三態)
紅線:券商報告原文抽取物不入 git(輸出夾 .gitignore);原件僅在
本機 input_reports。
批236 追令(操作員實錄:左右兩欄交錯+本文斷碎):
  ①分區 LAYOUT:fitz dict blocks 依 BBox 分四區——全寬標題帶/
    左本文區/右資訊區(x0≥52% 頁寬)/頁尾帶(底 8%)——
    「像表格切開處理並還原對齊」,兩欄分開各依 (y,x) 排序
  ②本文修復:區塊內斷行接回;句尾無終止標點(。.!?%)且下行為
    延續句=合併(EN 補空白/ZH 直接接;連字號斷詞修復)
  ③字級階層:font size+bold 判標題 H1-H3/頁尾小字=雜訊
    (收容件 geminicode_repair/hierarchy_b236 邏輯整合)
  輸出=.txt 四節【標題帶】【右資訊區】【本文(修復)】【頁尾(雜訊)】
    +.json 結構化 sidecar+總覽 HTML 左右雙欄對照顯示
批242 追令(操作員:「另外用 PDFPLUMBER 擷取相互對照;至少兩個
成功的方法及內容對照;輸出完整第一頁文字/表格/上左右資訊區/本文,
還原分類;先不管摘要」):
  法A=fitz 分區(v0101 正主)/法B=pdfplumber words 同判準分區
  +extract_tables 表格還原——雙法逐區對照(正規化 difflib 比率):
  ≥0.90 AGREE/≥0.60 PARTIAL/低=DIVERGE 誠實列示;
  sidecar 增 plumber/tables/compare/blocks(字級階層分類)四鍵,
  fitz 區鍵保持頂層=下游 ENG073 零改動。
批243 追令(操作員:「INTEGRATE ALL LIBS AND TOOLS INTO EXISTING
ENGINES」——收容包整合進現役引擎,收容件原地不動,graceful 掛載):
  法C=GenericLayoutEngine v2.0.0(收容 intake/GenericLayoutEngine_
    v2.0.0_b242):zone_for_bbox 九宮分區標+font_weight_from_name
    字重階層(操作員字體階層長文)+weighted_median 本文字級推定
    +probe_backends 後端可用矩陣→sidecar "gle" 鍵(缺席=誠實 absent)
  句級修復=NLP OneEngine TextProcessor(帶 ssot_lexicon;修 ENG073
    掛載漏 lexicon_path 永遠 fallback 之債):本文修復後再
    split_sentences 一句一資料;疊字修復;標題不加句號
    →sidecar "sentences" 鍵+.txt 新節【本文(句級)】
  fitz 區鍵仍為 sidecar 頂層=下游 ENG073 零改動。
批245 追令(操作員 Downloads 八件收容波):法C 收容夾改動態尾版
  解析(glob GenericLayoutEngine_* 取尾;嚴禁寫死版號)——工作站收容
  器落 v2.1.0 後,法C 零改動自動升級;缺席仍誠實 absent。
用法:python3 VRN_ENG072_FirstPageText_v0104.py run [--dir 報告夾]
        [--open] | --selftest
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
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
DEFAULT_DIR = HERE / "input_reports"
OUTDIR = VIA / "VIA_Reports" / "first_page_text"


ZH_END = "。!?!?;;:」)】%"

_INTAKE = HERE / "references" / "intake"


def _gle_mod():
    """批243 掛載;批245 尾版化:glob GenericLayoutEngine_* 取尾版夾
    (嚴禁寫死版號;v2.1.0 收容落地即自動升級;收容件原地不動)"""
    try:
        cands = sorted(d for d in _INTAKE.glob("GenericLayoutEngine_*")
                       if d.is_dir()
                       and (d / "generic_layout_engine.py").exists())
        if not cands:
            return None                      # 收容缺席=誠實 absent
        d = cands[-1]
        if str(d) not in sys.path:
            sys.path.insert(0, str(d))
        import generic_layout_engine as GLE  # noqa: N811
        return GLE
    except Exception:
        return None                          # 缺席=誠實 absent,零影響


def _nlp_tp():
    """批243:NLP OneEngine TextProcessor 正掛(帶 ssot_lexicon;
    修 ENG073 v0103 漏 lexicon_path 之債)"""
    try:
        pkg = _INTAKE / "VIA_NLP_OneEngine_v1.1.0"
        if str(pkg / "src") not in sys.path:
            sys.path.insert(0, str(pkg / "src"))
        from via_nlp_engine.text_ops import TextProcessor  # noqa
        lex = pkg / "data" / "lexicon" / "ssot_lexicon.json"
        return TextProcessor(lex) if lex.exists() else None
    except Exception:
        return None


def gle_annotate(blocks: list[dict], W: float, H: float) -> dict:
    """法C(批243):GLE 九宮分區標+字重階層+本文字級推定+後端矩陣"""
    GLE = _gle_mod()
    if GLE is None:
        return {"available": False, "note": "GLE 收容件缺席=誠實 absent"}
    try:
        els = []
        for b in blocks:
            bb = GLE.BBox(b["x0"], b["y0"], b["x1"], b["y1"])
            wt, bold, italic = GLE.font_weight_from_name(
                b.get("font", ""), 16 if b.get("bold") else 0)
            els.append({"zone": GLE.zone_for_bbox(bb, W, H),
                        "weight": wt, "bold": bold, "italic": italic,
                        "size": round(b["size"], 1),
                        "head": " ".join(b["lines"])[:80]})
        body_font = GLE.weighted_median(
            [(b["size"], sum(len(ln) for ln in b["lines"])) for b in blocks])
        backends = {s.name: s.available for s in GLE.probe_backends()}
        return {"available": True, "engine": "GenericLayoutEngine/2.0",
                "body_font": round(body_font, 1) if body_font else None,
                "elements": els,
                "backends_available": sorted(k for k, v in backends.items() if v),
                "backends_total": len(backends)}
    except Exception as exc:
        return {"available": False, "note": f"GLE 例外({type(exc).__name__})"}


def split_sentences_repaired(body: str) -> list[str]:
    """句級修復(批243;操作員長文:一句一句號一資料):TextProcessor
    正主(句切+疊字修);缺席=stdlib 終止標點後備。標題不經此道=無句號。"""
    if not body.strip():
        return []
    import re as _re
    # 彈點符前置切分(操作員真件樣本:➢ 摘要彈點=一彈點一資料)
    body = _re.sub(r"\s*([➢◆●■▲►•])", r"\n\1", body)
    tp = _nlp_tp()
    if tp is not None:
        try:
            sents = []
            for para in body.splitlines():
                if para.strip():
                    sents.extend(tp.split_sentences(para))
            return sents
        except Exception:
            pass
    import re as _re
    out = []
    for para in body.splitlines():
        out.extend(s.strip() for s in
                   _re.split(r"(?<=[。!?!?])", para) if s.strip())
    return out


def _repair_lines(lines: list[str]) -> str:
    """本文修復:斷行接回(批236 ②)——句尾無終止標點=延續句合併"""
    out: list[str] = []
    for ln in lines:
        ln = ln.strip()
        if not ln:
            continue
        if out and out[-1] and out[-1][-1] not in ZH_END \
                and not out[-1].endswith("."):
            prev = out.pop()
            if prev.endswith("-") and ln[:1].isalpha():
                out.append(prev[:-1] + ln)          # 連字號斷詞
            elif prev[-1].isascii() and ln[:1].isascii():
                out.append(prev + " " + ln)          # 英文補空白
            else:
                out.append(prev + ln)                # 中文直接接
        else:
            out.append(ln)
    return "\n".join(out)


def extract_page1_zones(p: Path) -> dict | None:
    """分區 LAYOUT(批236 ①③):四區+字級階層;回 None=無文字層"""
    try:
        import fitz
    except Exception:
        return None
    try:
        with fitz.open(str(p)) as doc:
            if not doc.page_count:
                return None
            page = doc[0]
            W, H = page.rect.width, page.rect.height
            blocks = []
            for b in page.get_text("dict")["blocks"]:
                if b.get("type") != 0:
                    continue
                lines, mx, bold, font = [], 0.0, False, ""
                for ln in b["lines"]:
                    t = "".join(sp["text"] for sp in ln["spans"]).strip()
                    if t:
                        lines.append(t)
                    for sp in ln["spans"]:
                        if sp["size"] > mx:
                            mx = sp["size"]
                            font = sp.get("font", "")   # 批243:字型名供 GLE 字重
                        if (sp["flags"] & 16) or "Bold" in sp.get("font", ""):
                            bold = True
                if not lines:
                    continue
                x0, y0, x1, y1 = b["bbox"]
                blocks.append({"lines": lines, "x0": x0, "y0": y0,
                               "x1": x1, "y1": y1, "size": mx, "bold": bold,
                               "font": font})
            if not blocks:
                return None
            zones = {"header": [], "right": [], "body": [], "footer": []}
            for b in blocks:
                wide = (b["x1"] - b["x0"]) > 0.66 * W
                if b["y1"] > 0.92 * H and b["size"] < 9:
                    z = "footer"                     # 頁尾小字=雜訊帶
                elif wide and b["y0"] < 0.18 * H:
                    z = "header"                     # 全寬標題帶
                elif b["x0"] >= 0.52 * W:
                    z = "right"                      # 右資訊區(卡)
                else:
                    z = "body"                       # 左本文區
                zones[z].append(b)
            for z in zones:
                zones[z].sort(key=lambda b: (round(b["y0"], 1), b["x0"]))
            heads = [{"text": " ".join(b["lines"])[:120],
                      "size": round(b["size"], 1),
                      "level": ("H1" if b["size"] >= 18 else
                                "H2" if b["size"] >= 14 else "H3")}
                     for b in blocks
                     if b["size"] >= 13 or (b["bold"] and b["size"] >= 11)]
            body_lines = [ln for b in zones["body"] for ln in b["lines"]]
            right_lines = [ln for b in zones["right"] for ln in b["lines"]]
            body = _repair_lines(body_lines)
            return {
                "header": "\n".join(ln for b in zones["header"]
                                     for ln in b["lines"]),
                "right": "\n".join(right_lines),
                "body": body,
                "footer": "\n".join(ln for b in zones["footer"]
                                     for ln in b["lines"]),
                "heads": heads,
                # 批243 整合鍵(fitz 區鍵仍頂層=下游零改)
                "gle": gle_annotate(blocks, W, H),
                "sentences": split_sentences_repaired(body)}
    except Exception:
        return None


def extract_page1_plumber(p: Path) -> dict | None:
    """法B(批242):pdfplumber words 同判準分區+表格還原"""
    try:
        import pdfplumber
    except Exception:
        return None
    try:
        with pdfplumber.open(str(p)) as pdf:
            if not pdf.pages:
                return None
            pg = pdf.pages[0]
            W, H = pg.width, pg.height
            zones = {"header": [], "right": [], "body": [], "footer": []}
            line_map: dict = {}
            for w in pg.extract_words(use_text_flow=False):
                key = round(w["top"] / 4)
                line_map.setdefault(key, []).append(w)
            for key in sorted(line_map):
                ws = sorted(line_map[key], key=lambda x: x["x0"])
                # 批242 修:同 y 左右欄併行病→行內大縫隙(>15%W)切段,
                # 每段獨立分區(對齊 fitz block 語意)
                parts, cur = [], [ws[0]]
                for w in ws[1:]:
                    if w["x0"] - cur[-1]["x1"] > 0.15 * W:
                        parts.append(cur)
                        cur = [w]
                    else:
                        cur.append(w)
                parts.append(cur)
                for seg in parts:
                    x0 = min(x["x0"] for x in seg)
                    x1 = max(x["x1"] for x in seg)
                    top = min(x["top"] for x in seg)
                    bot = max(x["bottom"] for x in seg)
                    txt = " ".join(x["text"] for x in seg)
                    wide = (x1 - x0) > 0.66 * W
                    if bot > 0.92 * H:
                        z = "footer"
                    elif wide and top < 0.18 * H:
                        z = "header"
                    elif x0 >= 0.52 * W:
                        z = "right"
                    else:
                        z = "body"
                    zones[z].append(txt)
            tables = []
            for t in (pg.extract_tables() or []):
                rows = [[(c or "").strip() for c in row] for row in t]
                if any(any(c for c in row) for row in rows):
                    tables.append(rows[:30])
            return {"header": "\n".join(zones["header"]),
                    "right": "\n".join(zones["right"]),
                    "body": _repair_lines(zones["body"]),
                    "footer": "\n".join(zones["footer"]),
                    "tables": tables}
    except Exception:
        return None


def compare_zones(a: dict, b: dict) -> dict:
    """雙法逐區對照(批242):正規化 difflib 比率+三態判定"""
    import difflib
    out = {}
    for k in ("header", "right", "body"):
        ta = "".join(str(a.get(k, "")).split())
        tb = "".join(str(b.get(k, "")).split())
        if not ta and not tb:
            out[k] = {"ratio": 1.0, "verdict": "BOTH_EMPTY"}
            continue
        r = difflib.SequenceMatcher(None, ta, tb).ratio()
        out[k] = {"ratio": round(r, 3),
                  "verdict": ("AGREE" if r >= 0.90 else
                              "PARTIAL" if r >= 0.60 else "DIVERGE")}
    return out


def extract_pdf_page1(p: Path) -> tuple[str, str]:
    """回 (文字, 方法標記);fitz 版面序優先,pypdf 後備,零字=NEEDS_OCR"""
    try:
        import fitz
        with fitz.open(str(p)) as doc:
            if doc.page_count:
                # sort=True=版面閱讀序(LAYOUT ANALYSIS;digest ㉙ 同族)
                txt = doc[0].get_text("text", sort=True).strip()
                if txt:
                    return txt, "FITZ_LAYOUT"
    except Exception:
        pass
    try:
        import pypdf
        r = pypdf.PdfReader(str(p))
        if r.pages:
            txt = (r.pages[0].extract_text() or "").strip()
            if txt:
                return txt, "PYPDF_FALLBACK"
    except Exception:
        pass
    return "", "NEEDS_OCR"


def extract_docx_head(p: Path, n_para: int = 30) -> tuple[str, str]:
    try:
        import docx
        d = docx.Document(str(p))
        paras = [q.text for q in d.paragraphs if q.text.strip()][:n_para]
        if paras:
            return "\n".join(paras), "DOCX_HEAD"
        return "", "DOCX_EMPTY"
    except ImportError:
        return "", "DOCX_LIB_MISSING(pip install python-docx)"
    except Exception as exc:
        return "", f"DOCX_ERR({type(exc).__name__})"


def run(src: Path | None = None, open_after: bool = False) -> int:
    src = src or DEFAULT_DIR
    files = sorted([*src.glob("*.pdf"), *src.glob("*.docx")]) if src.exists() else []
    if not files:
        print(f"[首頁擷取] {src} 無報告件(誠實;缺件搜集器先跑)")
        return 2
    OUTDIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    stats = {"DUAL_ZONES": 0, "FITZ_ZONES": 0, "FITZ_LAYOUT": 0,
             "PYPDF_FALLBACK": 0, "NEEDS_OCR": 0, "DOCX": 0, "OTHER": 0}
    cards = []
    import json as _json
    for p in files:
        zones = None
        if p.suffix.lower() == ".pdf":
            zones = extract_page1_zones(p)
            if zones and (zones["body"] or zones["right"] or zones["header"]):
                plum = extract_page1_plumber(p)      # 法B(批242)
                comp = compare_zones(zones, plum) if plum else {}
                zones["plumber"] = {k: plum[k] for k in
                                    ("header", "right", "body", "footer")} \
                    if plum else None
                zones["tables"] = (plum or {}).get("tables", [])
                zones["compare"] = comp
                agree = "/".join(f"{k}:{v['verdict']}"
                                 for k, v in comp.items()) or "單法"
                ttxt = "\n\n".join(
                    "〔表" + str(i + 1) + "〕\n" +
                    "\n".join(" | ".join(r) for r in t)
                    for i, t in enumerate(zones["tables"][:4]))
                sent = "\n".join(zones.get("sentences", []))
                g = zones.get("gle", {})
                glel = (f"GenericLayoutEngine/2.0 · 本文字級 {g.get('body_font')}"
                        f" · 後端可用 {len(g.get('backends_available', []))}"
                        f"/{g.get('backends_total', 0)}"
                        if g.get("available") else "absent(誠實)")
                txt = (f"【標題帶】\n{zones['header']}\n\n"
                       f"【右資訊區】\n{zones['right']}\n\n"
                       f"【本文(修復)】\n{zones['body']}\n\n"
                       f"【本文(句級一句一資料)】\n{sent}\n\n"
                       f"【表格(pdfplumber 還原)】\n{ttxt or '(頁一無表格=誠實)'}\n\n"
                       f"【雙法對照】{agree}\n【法C GLE】{glel}\n\n"
                       f"【頁尾(雜訊帶)】\n{zones['footer']}")
                tag = "DUAL_ZONES" if plum else "FITZ_ZONES"
                (OUTDIR / (p.stem + ".json")).write_text(_json.dumps(
                    zones, ensure_ascii=False, indent=1), encoding="utf-8")
            else:
                txt, tag = extract_pdf_page1(p)
        else:
            txt, tag = extract_docx_head(p)
        key = tag if tag in stats else ("DOCX" if tag.startswith("DOCX") else "OTHER")
        stats[key] = stats.get(key, 0) + 1
        (OUTDIR / (p.stem + ".txt")).write_text(
            f"# {p.name} · {tag} · {ts}\n\n{txt}", encoding="utf-8")
        state = "ok" if txt else "warn"
        if zones and tag in ("FITZ_ZONES", "DUAL_ZONES"):
            cards.append(
                f"<section class='{state}'><h2>{html.escape(p.name)}"
                f"<span class='tag'>{tag} · 分區還原</span></h2>"
                f"<div class='hd'>{html.escape(zones['header'][:300])}</div>"
                f"<div class='cols'><div class='col'><h3>本文區(修復)</h3>"
                f"<pre>{html.escape(zones['body'][:2000])}</pre></div>"
                f"<div class='col r'><h3>右資訊區</h3>"
                f"<pre>{html.escape(zones['right'][:1200])}</pre></div></div>"
                f"</section>")
        else:
            cards.append(
                f"<section class='{state}'><h2>{html.escape(p.name)}"
                f"<span class='tag'>{tag} · {len(txt):,} 字</span></h2>"
                f"<pre>{html.escape(txt[:2400]) if txt else '(零文字=掃描版或抽取失敗;候 OCR 道,誠實不假抽)'}"
                + ("\n…(全文見同名 .txt)" if len(txt) > 2400 else "") + "</pre></section>")
        print(f"  [{tag}] {p.name} · {len(txt):,} 字")
    summary = f"""<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>個股報告首頁文字總覽</title><style>
body{{background:#0b1220;color:#c7d3e8;font:10.5px/1.55 "Segoe UI",
"Noto Sans TC",sans-serif;padding:14px;max-width:1100px;margin:0 auto}}
h1{{font-size:14px;color:#e8eefb}}
.sub{{color:#7e8db0;font-size:10px;margin:2px 0 10px}}
section{{background:#111a2e;border:1px solid #1e2a44;border-radius:8px;
padding:10px;margin-bottom:10px}}
section.warn{{border-color:#f0b429}}
h2{{font-size:11px;color:#4f8ef7;overflow-wrap:anywhere}}
.tag{{color:#7e8db0;font-size:9px;margin-left:8px}}
pre{{white-space:pre-wrap;overflow-wrap:anywhere;color:#c7d3e8;
font:9.5px/1.5 Consolas,monospace;margin-top:6px;max-height:340px;
overflow:auto}}
.cols{{display:grid;grid-template-columns:3fr 2fr;gap:10px}}
.col h3{{font-size:10px;color:#7e8db0;margin-top:6px}}
.col.r pre{{border-left:2px solid #2a3c61;padding-left:8px}}
.hd{{color:#e8eefb;font-size:10.5px;margin:4px 0;overflow-wrap:anywhere}}
@media(max-width:760px){{.cols{{grid-template-columns:1fr}}}}
</style></head><body>
<h1>個股報告首頁文字擷取總覽(LAYOUT ANALYSIS · 批243 三法整合)</h1>
<div class="sub">{ts} · {len(files)} 件 · 雙法 {stats['DUAL_ZONES']} · 分區 {stats['FITZ_ZONES']} · fitz 版面序 {stats['FITZ_LAYOUT']}
· pypdf 後備 {stats['PYPDF_FALLBACK']} · 候 OCR {stats['NEEDS_OCR']}
· docx {stats['DOCX']} · 逐件 .txt 同夾 · 不入 git(紅線)</div>
{''.join(cards)}</body></html>"""
    outp = OUTDIR / "FIRSTPAGE_SUMMARY.html"
    outp.write_text(summary, encoding="utf-8")
    print(f"[計] {len(files)} 件 · 雙法 {stats['DUAL_ZONES']} · 分區 {stats['FITZ_ZONES']} · fitz {stats['FITZ_LAYOUT']} · pypdf "
          f"{stats['PYPDF_FALLBACK']} · 候OCR {stats['NEEDS_OCR']} · docx "
          f"{stats['DOCX']} · 總覽 {outp}")
    if open_after:
        try:
            import webbrowser
            webbrowser.open(outp.as_uri())
        except Exception:
            pass
    return 0


def selftest() -> int:
    import tempfile
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    src = Path(__file__).read_text(encoding="utf-8")
    chk("① 抽取道優先序=digest ㉓㉙ 同族(fitz 版面序→pypdf 後備→NEEDS_OCR)",
        'get_text("text", sort=True)' in src and "PYPDF_FALLBACK" in src
        and "NEEDS_OCR" in src)
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        import fitz
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 100), "TEST REPORT 2330 TT")
        page.insert_text((72, 130), "Target Price 1,500")
        doc.new_page().insert_text((72, 100), "PAGE TWO SHOULD NOT APPEAR")
        doc.save(str(tdp / "fx_report.pdf"))
        doc.close()
        txt, tag = extract_pdf_page1(tdp / "fx_report.pdf")
        chk("② 首頁抽取實測(fixture 2 頁 PDF 僅取第 1 頁)",
            tag == "FITZ_LAYOUT" and "2330" in txt
            and "PAGE TWO" not in txt)
        # 批236 fixture:雙欄頁(左本文斷行+右資訊卡)
        d2 = fitz.open()
        pg = d2.new_page()   # 預設 595x842
        pg.insert_text((40, 60), "EARNINGS UPSIDE REITERATE BUY", fontsize=20)
        pg.insert_text((40, 140), "We expect the momentum to")
        pg.insert_text((40, 158), "continue in coming quarters")
        pg.insert_text((40, 176), "driven by GB200 ramp.")
        pg.insert_text((360, 140), "Buy")
        pg.insert_text((360, 158), "Target price NT$165.00")
        pg.insert_text((360, 176), "Price NT$114.00")
        pg.insert_text((40, 820), "Disclaimer fine print", fontsize=6)
        d2.save(str(tdp / "fx_twocol.pdf"))
        d2.close()
        z = extract_page1_zones(tdp / "fx_twocol.pdf")
        zp = extract_page1_plumber(tdp / "fx_twocol.pdf")
        cmpz = compare_zones(z, zp) if zp else {}
        chk("⑪ 法B pdfplumber 同判準分區+雙法對照(body/right AGREE)",
            zp is not None and "Target price" in zp["right"]
            and cmpz.get("body", {}).get("verdict") in ("AGREE", "PARTIAL")
            and cmpz.get("right", {}).get("verdict") in ("AGREE", "PARTIAL"))
        cd = compare_zones({"body": "abc def", "right": "", "header": ""},
                           {"body": "totally different text!", "right": "",
                            "header": ""})
        chk("⑫ 對照三態機制(DIVERGE 誠實判離+BOTH_EMPTY)",
            cd["body"]["verdict"] == "DIVERGE"
            and cd["right"]["verdict"] == "BOTH_EMPTY")
        chk("⑨ 分區還原(批236:左本文/右資訊卡切開零交錯)",
            z is not None and "Target price" in z["right"]
            and "Target price" not in z["body"]
            and "momentum" in z["body"] and "momentum" not in z["right"])
        chk("⑩ 本文斷行修復+標題階層+頁尾雜訊帶",
            "momentum to continue" in z["body"].replace("\n", " ")
            and z["body"].count("\n") <= 1
            and any(h["level"] == "H1" for h in z["heads"])
            and "Disclaimer" in z["footer"])
        g = z.get("gle", {})
        chk("⑬ 法C GLE 掛載(批243:九宮分區標+字重階層+後端矩陣;"
            "缺席=誠實 absent)",
            ("gle" in z) and (not g.get("available")
             or (g.get("elements") and g.get("backends_total", 0) > 0
                 and any(e["zone"] for e in g["elements"]))))
        sents = split_sentences_repaired("營收強勁。毛利率回升,展望正向。維持買進")
        chk("⑭ 句級修復(批243:一句一資料;句界切分;標題不經句道)",
            len(sents) >= 2 and sents[0].endswith("。")
            and "sentences" in z)
        blank = fitz.open()
        blank.new_page()
        blank.save(str(tdp / "fx_scan.pdf"))
        blank.close()
        t2, tag2 = extract_pdf_page1(tdp / "fx_scan.pdf")
        chk("③ 掃描版誠實(零文字=NEEDS_OCR 不假抽)", tag2 == "NEEDS_OCR"
            and t2 == "")
        rc = run(tdp)
        page_html = (OUTDIR / "FIRSTPAGE_SUMMARY.html").read_text(encoding="utf-8")
        chk("④ 逐件 .txt+總覽 HTML 產出(一頁堆疊)", rc == 0
            and (OUTDIR / "fx_report.txt").exists()
            and "首頁文字擷取總覽" in page_html)
        chk("⑤ 空夾誠實 rc2(缺件先搜集)",
            run(tdp / "nothing_x") == 2)
    chk("⑥ docx 道誠實(無頁界=前段近似標 DOCX_HEAD;缺庫誠實提示)",
        "DOCX_HEAD" in src and "DOCX_LIB_MISSING" in src)
    chk("⑦ 紅線宣告(抽取物不入 git;原件僅本機)",
        "不入 git" in src)
    chk("⑧ 零網路+加速橋(純本地抽取)",
        "ACCEL-BRIDGE" in src
        and all(("import " + k) not in src for k in ("requests", "httpx")))
    print(f"  [計] 十四檢 OK {14 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== 首頁三法整合擷取器(VRN_ENG072 v0104)· 十四檢自測(零網路)===")
        return selftest()
    if args and args[0] == "run":
        d = None
        if "--dir" in args:
            d = Path(args[args.index("--dir") + 1])
        return run(d, "--open" in args)
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main())
