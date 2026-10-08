#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""VRN_ENG394_LayoutRestore v0101 — 薄尾:右側資訊區 / 表格雙欄還原 · 一句一標題一資料(兩種編號 · 兩層分類)· 截取完整度 · 去重修復(前版 v0100 本體照讀)

操作員 R37(2026-10-01):「一句一標題一資料並且有編號分類兩種 確認全部都有被截取 周邊資訊區及表格放右邊還原」「植入去重修復引擎」。
① 編號兩種:全文流水號 S0001…(跨頁連號)· 章節號 節.句(遇到 H1/H2/H3 開新節,標題本身是 節.0);每列都帶「所屬標題」——一句一標題一資料。
   分類兩層:類別(文 / 表 / 圖)× 次類別(H1/H2/H3/BODY/SMALL · 表的 KV/TOC/格線表/扁平表 · 圖的影像 / 座標軸)。表與圖另編 T01 / F01。
② 截取完整度(確認全部都有被截取):真值 = 該頁文字層每一個字(fitz rawdict;沿用 ENG392 的 coverage / missing_segments 同一把尺);
   截取 = 本文句 + 資訊區表格 + 圖說 + **排除區原文**(排除區是「有截到、不擷取」,不是漏)。截取覆蓋率 ≥ 99.9% = GREEN,否則 RED 並列缺字片段;
   另報「擷取覆蓋率」(不含排除區)給人看排除了多少。
③ 去重修復:跨頁 —— 同一句(去空白後相同)出現在 ≥ 2 頁且 ≥ 半數選取頁 = 頁眉 / 頁尾 / 浮水印,只留第一次,其餘移到排除區(理由 跨頁重複);
   同頁 —— 同一句重複只留第一次。去掉的不消失,排除區照列(原文 · 據點 · 理由)。
④ 雙欄頁:LAYOUT_latest.html 每頁左欄本文(編號 · 標題階層)、右欄資訊區表格 + 圖;排除區收在下方。窄螢幕自動上下疊。
其餘(XY 切 · 合併格 · 扁平表 · 驗算 · 圖≠表)照 v0100 一字不動。VIA_FROM_VCGC:經 VCGC 跑;零網路;不用 TA-Lib;正本唯讀。
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
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VRN_ENG394_LayoutRestore"


def _vnum(p: Path) -> int:
    m = re.search(r"_v(\d+)$", Path(p).stem)
    return int(m.group(1)) if m else -1


_PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum,
                  default=HERE / "VRN_ENG394_LayoutRestore_v0100.py")   # the prior this tail was cut from
_spec = importlib.util.spec_from_file_location("layout_prior_for_" + Path(__file__).stem, _PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name: str):
    return getattr(PRIOR, name)


ENGINE = Path(__file__).stem
tidy, md_table = PRIOR.tidy, PRIOR.md_table
COVER_MIN = 0.999
DEDUP = True                                         # 去重修復開關(前版自測在關閉下重跑 = 證明其餘行為不變)
SUB_ZH = {"KV": "鍵值", "TOC": "目錄"}
SAME_PAGE_MIN = 12          # 同頁去重只對 ≥12 字的句子;卡片 / 表格裡重複的短標籤(PEER / LEADER)是資料,不是雜訊(實測族群分類頁)


def _lines_toc(lns: list) -> list | None:
    """同 v0100;唯一改動:目錄標題行(Table of Contents)下一行是頁碼時,它是一筆目錄項目(FactSet 目錄把自己也列進去),
    不再當標題跳過 —— 跳過會讓「Table of Contents 2」16 字在截取完整度裡變成缺字(實測 p2 RED)。"""
    heads = [h.lower() for h in PRIOR.ssot().get("toc_heads", [])]
    rows, used, i = [], 0, 0
    while i < len(lns):
        t = tidy(lns[i]["text"])
        m = re.match(r"^(.*?[A-Za-z\u4e00-\u9fff].*?)\s*(?:\.{3,}|…+)?\s+(\d{1,3})$", t)
        nxt_pg = i + 1 < len(lns) and re.fullmatch(r"\d{1,3}", tidy(lns[i + 1]["text"]))
        if t.lower() in heads and not nxt_pg:
            used += 1
        elif m:
            rows.append([tidy(m.group(1)), m.group(2)])
            used += 1
        elif nxt_pg and re.search(r"[A-Za-z\u4e00-\u9fff]", t):
            rows.append([t, tidy(lns[i + 1]["text"])])
            used += 2
            i += 1
        i += 1
    pg = [int(r[1]) for r in rows]
    if len(rows) >= 3 and used >= 0.6 * len(lns) and sum(1 for a, b in zip(pg, pg[1:]) if b >= a) >= 0.8 * (len(pg) - 1):
        return rows
    return None


PRIOR._lines_toc = _lines_toc


def _key(s: str) -> str:
    return re.sub(r"\s+", "", str(s or "")).lower()


# ---------------------------------------------------------------- ③ 去重修復

def dedup(res: dict) -> dict:
    if not DEDUP:
        res["dedup"] = {"removed": 0, "cross_page_keys": 0, "off": True}
        return res
    pages = res.get("pages") or [res]
    n = len(pages)
    seen_on = {}
    for p in pages:
        for k in {_key(b["text"]) for b in p.get("body", []) if len(_key(b["text"])) >= 2}:
            seen_on[k] = seen_on.get(k, 0) + 1
    cross = {k for k, c in seen_on.items() if c >= 2 and c * 2 >= n}
    first_kept, removed = set(), 0
    for p in pages:
        keep, here = [], set()
        for b in p.get("body", []):
            k = _key(b["text"])
            why = ""
            if k in cross and k in first_kept:
                why = f"跨頁重複(出現在 {seen_on[k]}/{n} 頁:頁眉 / 頁尾 / 浮水印)"
            elif k in here and len(k) >= SAME_PAGE_MIN:
                why = "同頁重複句"
            if why:
                p.setdefault("excluded", []).append({"anchor": b["anchor"], "bbox": b.get("bbox"), "reason": why, "size": b.get("size"),
                                                     "head": b["text"][:40], "lines": 1, "text": b["text"], "dedup": True})
                removed += 1
                continue
            here.add(k)
            if k in cross:
                first_kept.add(k)
            keep.append(b)
        p["body"] = keep
    res["dedup"] = {"removed": removed, "cross_page_keys": len(cross)}
    return res


# ---------------------------------------------------------------- ① 兩種編號 · 兩層分類 · 所屬標題

def number(res: dict) -> dict:
    pages = res.get("pages") or [res]
    sid, sec, idx, title = 0, 0, 0, ""
    tn = fn = 0
    for p in pages:
        for b in p.get("body", []):
            sid += 1
            b["no"] = f"S{sid:04d}"
            if b.get("subcategory") in ("H1", "H2", "H3"):
                sec, idx, title = sec + 1, 0, b["text"]
                b["sec_no"] = f"{sec}.0"
                b["title"] = b["text"]
            else:
                idx += 1
                b["sec_no"] = f"{max(sec, 0)}.{idx}"
                b["title"] = title or "(首段 · 無標題)"
            b["cat"] = PRIOR.CAT_ZH.get(b.get("category", "text"), "文")
        for t in p.get("info", []):
            tn += 1
            t["no"] = f"T{tn:02d}"
            t["sub2"] = SUB_ZH.get(t.get("subcategory"), t.get("subcategory")) or {"pdf_grid": "格線表", "pdf_text": "扁平表", "text": "扁平表", "pdf_info": "鍵值",
                                                  "pdf_toc": "目錄"}.get(t.get("origin", ""), "表")
        for f in p.get("figures", []):
            fn += 1
            f["no"] = f"F{fn:02d}"
            f["sub2"] = "影像" if f.get("origin") == "pdf_image" else "座標軸圖"
    return res


# ---------------------------------------------------------------- ② 截取完整度

def _captured_text(p: dict) -> tuple:
    body = [b["text"] for b in p.get("body", [])]
    info = []
    for t in p.get("info", []):
        info += [str(c) for c in t.get("columns", [])]
        if t.get("subcategory") == "KV":                     # 鍵值列原文是「項目:內容」,冒號也是原文的一部分
            info += [f"{r[0]}：{r[1]}" if r[0] else str(r[1]) for r in t.get("rows", [])]
        else:
            info += [str(x) for r in t.get("rows", []) for x in r]
        info += [t.get("source") or "", t.get("caption") or "", t.get("title") or ""] + list(t.get("notes") or [])
    figs = []
    for f in p.get("figures", []):
        figs += [f.get("table_no") or "", f.get("title") or "", " ".join(f.get("x_labels") or []), " ".join(f.get("data_labels") or []),
                 f.get("legend") or "", f.get("source") or "", " ".join(str(v) for v in (f.get("axis") or {}).get("ticks", []))]
    excl = [e.get("text") or e.get("head") or "" for e in p.get("excluded", [])]
    return " ".join(body + info + figs), " ".join(excl)


def completeness(res: dict, src_pages: list) -> dict:
    e392 = PRIOR._eng392()
    rows, worst = [], "GREEN"
    for p, src in zip(res.get("pages") or [res], src_pages):
        kept, excl = _captured_text(p)
        if e392 is None:
            rows.append({"page": p.get("page", 1), "state": "NODATA", "why": "ENG392 不在"})
            worst = "NODATA" if worst == "GREEN" else worst
            continue
        cap, miss, _x = e392.coverage(src, kept + " " + excl)
        ext, _m2, _x2 = e392.coverage(src, kept)
        segs = [s for s in e392.missing_segments(src, kept + " " + excl) if not s.get("moved")][:8] if miss else []
        lamp = "GREEN" if cap >= COVER_MIN else "RED"
        if lamp == "RED":
            worst = "RED"
        rows.append({"page": p.get("page", 1), "src_chars": len(re.sub(r"\s", "", src)), "captured": round(cap * 100, 2),
                     "extracted": round(ext * 100, 2), "missing_chars": sum(miss.values()), "segments": segs, "state": lamp})
    return {"verdict": worst, "pages": rows, "rule": "截取 = 本文 + 資訊區 + 圖 + 排除區原文;≥ 99.9% GREEN(ENG392 同一把尺)"}


def _src_pages(path: Path, sel: list) -> list:
    import fitz
    out = []
    with fitz.open(str(path)) as doc:
        for pno in sel:
            chars = []
            for b in doc[pno - 1].get_text("rawdict").get("blocks", []):
                if b.get("type") != 0:
                    continue
                for ln in b.get("lines", []):
                    chars.append("".join(ch.get("c", "") for sp in ln.get("spans", []) for ch in sp.get("chars", [])))
            out.append("\n".join(chars))
    return out


def _fill_excluded_text(path: Path, res: dict) -> None:
    """排除區只記了開頭 40 字 → 用 bbox 回頁面取全文(完整度要算進去:排除 = 有截到、不擷取)。"""
    import fitz
    with fitz.open(str(path)) as doc:
        for p in res.get("pages", []):
            page = doc[p["page"] - 1]
            for e in p.get("excluded", []):
                if not e.get("text") and e.get("bbox"):
                    try:
                        e["text"] = tidy(page.get_text("text", clip=fitz.Rect(*e["bbox"])))
                    except (ValueError, TypeError, RuntimeError) as exc:
                        e["text_error"] = f"{type(exc).__name__}"


_PRIOR_RESTORE = PRIOR.restore_pdf


def restore_pdf(path: Path, pages: str = "1") -> dict:
    res = _PRIOR_RESTORE(path, pages)
    _fill_excluded_text(Path(path), res)
    dedup(res)
    number(res)
    res["completeness"] = completeness(res, _src_pages(Path(path), [p["page"] for p in res["pages"]]))
    if res["completeness"]["verdict"] == "RED" and res["verdict"] != "RED":
        res["verdict"] = "RED"
    return res


_PRIOR_TEXT = PRIOR.text_restore


def text_restore(text: str) -> dict:
    res = _PRIOR_TEXT(text)
    res.setdefault("page", 1)
    dedup(res)
    number(res)
    res["completeness"] = completeness(res, [text])
    return res


PRIOR.restore_pdf = restore_pdf
PRIOR.text_restore = text_restore


# ---------------------------------------------------------------- 輸出:本文表(兩種編號 · 兩層分類 · 所屬標題)· 完整度 · 去重 · 雙欄頁

def _body_md(body: list) -> str:
    rows = [[b.get("no", ""), b.get("anchor", ""), b.get("cat", "文"), b.get("subcategory", ""), "" if b.get("size") is None else b["size"],
             "" if b.get("bold") is None else ("粗" if b["bold"] else ""), b["text"], b.get("sec_no", ""), b.get("title", "")] for b in body]
    # 前 7 欄與 v0100 同(# = 全文編號 S0001)· 後 2 欄新增:節.句(第二種編號)· 所屬標題(一句一標題一資料)
    return md_table(["#", "據點", "類別", "次類別", "字級", "粗", "內容", "節.句", "所屬標題"], rows)


PRIOR._body_md = _body_md
_PRIOR_MD = PRIOR.to_markdown


def to_markdown(res: dict) -> str:
    md = _PRIOR_MD(res)
    c = res.get("completeness") or {}
    extra = ["", "## 截取完整度(確認全部都有被截取)", "", f"總判 {c.get('verdict', '—')} · {c.get('rule', '')}", ""]
    extra.append(md_table(["頁", "來源字", "截取覆蓋%", "擷取覆蓋%(不含排除區)", "缺字", "燈", "缺字片段"],
                          [[r.get("page"), r.get("src_chars", ""), r.get("captured", ""), r.get("extracted", ""), r.get("missing_chars", ""), r.get("state"),
                            " · ".join(f"「{s['before']}【{s['text']}】{s['after']}」" for s in r.get("segments", [])[:3])] for r in c.get("pages", [])]))
    d = res.get("dedup") or {}
    extra += ["", f"去重修復:移到排除區 {d.get('removed', 0)} 句 · 跨頁重複鍵 {d.get('cross_page_keys', 0)}(原文照列在排除區)"]
    return md.rstrip() + "\n" + "\n".join(extra) + "\n"


PRIOR.to_markdown = to_markdown

CSS = """<style>
.lr-grid{display:grid;grid-template-columns:minmax(0,3fr) minmax(0,2fr);gap:16px;align-items:start}
@media (max-width:900px){.lr-grid{grid-template-columns:1fr}}
.lr-col h4{margin:.4em 0}.lr-body td.no{white-space:nowrap;font-variant-numeric:tabular-nums}
.lr-h1 td{font-weight:700;font-size:1.15em}.lr-h2 td{font-weight:700}.lr-h3 td{font-weight:600}
.lr-small td{opacity:.75;font-size:.9em}.lr-right table{font-size:.92em}
details.lr-ex{margin-top:8px}
</style>"""


def page_html(docs: list) -> str:
    e = _html.escape
    kit = PRIOR._kit()
    lamp = (kit.lamp if kit else (lambda s, t: f"<b>{e(t)}</b>"))

    def tbl(cols, rows, cls=""):
        return (f"<table class='via {cls}'><tr>" + "".join(f"<th>{e(tidy(c))}</th>" for c in cols) + "</tr>"
                + "".join("<tr>" + "".join(f"<td>{e(tidy(x))}</td>" for x in r) + "</tr>" for r in rows) + "</table>")
    summ, parts = [], []
    for d in docs:
        pages = d["pages"] if d.get("mode") == "pdf" else [d]
        c = d.get("completeness") or {}
        cov = min((r.get("captured", 100) for r in c.get("pages", []) if "captured" in r), default=None)
        summ.append([d["verdict"], d["name"], sum(len(p["info"]) for p in pages), sum(len(p["body"]) for p in pages),
                     sum(len(p["excluded"]) for p in pages), f"{cov}%" if cov is not None else "—", c.get("verdict", "—"),
                     (d.get("dedup") or {}).get("removed", 0)])
        sec = [f"<h3>{e(d['name'])} · {lamp(d['verdict'], d['verdict'])} · 截取 {lamp(c.get('verdict', 'NODATA'), c.get('verdict', '—'))}</h3>"]
        for p in pages:
            body_rows = "".join(
                f"<tr class='lr-{(b.get('subcategory') or 'body').lower()}'><td class='no'>{e(b.get('no', ''))}</td><td class='no'>{e(b.get('sec_no', ''))}</td>"
                f"<td>{e(b.get('cat', ''))}·{e(b.get('subcategory', ''))}</td><td>{e(b['text'])}</td><td class='no'>{e(b.get('anchor', ''))}</td></tr>"
                for b in p["body"])
            left = (f"<div class='lr-col lr-body'><h4>本文區(左)· 第 {p.get('page', 1)} 頁</h4><table class='via'><tr><th>編號</th><th>節.句</th>"
                    f"<th>類別</th><th>資料(一句)</th><th>據點</th></tr>{body_rows}</table></div>")
            right = ["<div class='lr-col lr-right'><h4>資訊區 · 表格 · 圖(右)</h4>"]
            for t in p["info"]:
                right.append(f"<div class='via-note'>{e(t.get('no', ''))} · {e(t.get('sub2', ''))} · {lamp(t.get('verdict', ''), t.get('verdict', ''))} "
                             f"{e(tidy(t.get('table_no') or ''))} {e(tidy(t.get('title') or ''))}</div>" + tbl(t["columns"], t["rows"])
                             + (f"<div class='via-note'>資料來源:{e(t['source'])}</div>" if t.get("source") else ""))
            for f in p["figures"]:
                right.append(f"<div class='via-note'>{e(f.get('no', ''))} · 圖 · {e(f.get('sub2', ''))} {e(tidy(f.get('title') or ''))} — "
                             f"{e(f.get('note', ''))}</div>")
            right.append("</div>")
            ex = "".join(f"<tr><td>{e(x.get('anchor', ''))}</td><td>{e(x.get('reason', ''))}</td><td>{e((x.get('text') or x.get('head') or '')[:120])}</td></tr>"
                         for x in p["excluded"])
            sec.append(f"<div class='lr-grid'>{left}{''.join(right)}</div>"
                       + (f"<details class='lr-ex'><summary>排除區 {len(p['excluded'])} 項(小字頁尾 · 附錄 · 跨頁重複)</summary>"
                          f"<table class='via'><tr><th>據點</th><th>理由</th><th>原文</th></tr>{ex}</table></details>" if p["excluded"] else ""))
        parts.append("".join(sec))
    body = (CSS + "<h3>紅黃綠矩陣 · 版面還原(左本文 · 右資訊區與表格)</h3>"
            + tbl(["燈", "文件", "表", "本文句", "排除", "截取覆蓋", "截取燈", "去重"], summ) + "".join(parts)
            + "<div class='via-note'>一句一標題一資料:每列有全文編號 S0001 與章節號 節.句、類別 × 次類別;"
              "截取覆蓋 = 本文 + 資訊區 + 圖 + 排除區原文對文字層逐字核(ENG392 同一把尺)。</div>")
    v = PRIOR._worst([d["verdict"] for d in docs])
    side = f"<div class='via-card'>{lamp(v, '總判 ' + v)}</div><div class='via-note'>{len(docs)} 件</div>"
    if kit:
        return kit.page("VRN 版面還原", body, side, module={"id": "vrn-layout-restore", "name": "版面還原"})
    return f"<!doctype html><meta charset='utf-8'><title>VRN 版面還原</title>{side}{body}"


PRIOR.page_html = page_html


def selftest() -> int:
    import tempfile
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note and not cond else ''}")

    with tempfile.TemporaryDirectory() as td:
        pdf = PRIOR.make_pdf(Path(td) / "synthetic_firstpage.pdf")
        res = restore_pdf(pdf, "1")
        p = res["pages"][0]
        b = p["body"]
        chk("兩種編號:全文 S0001… 連號 · 章節 節.句(標題 = 節.0)", [x["no"] for x in b] == [f"S{i:04d}" for i in range(1, len(b) + 1)]
            and b[0]["sec_no"] == "1.0" and any(x["sec_no"] == "2.1" for x in b), [(x["no"], x["sec_no"]) for x in b][:6])
        chk("一句一標題一資料:每列都有所屬標題(本文句的標題 = 上一個 H 列)", all(x.get("title") for x in b)
            and next(x for x in b if x["sec_no"] == "2.1")["title"] == "Key Points", [(x["sec_no"], x["title"]) for x in b][:5])
        chk("兩層分類:類別(文)× 次類別(H1/H2/BODY…)· 表 T01… 帶次類別(格線表 / 鍵值 / 扁平表)",
            all(x["cat"] == "文" for x in b) and {t["sub2"] for t in p["info"]} >= {"格線表", "鍵值", "扁平表"}, {t["sub2"] for t in p["info"]})
        c = res["completeness"]
        chk("截取完整度:合成首頁每個字都在(本文 + 資訊區 + 表 + 排除區)→ GREEN ≥ 99.9%", c["verdict"] == "GREEN"
            and c["pages"][0]["captured"] >= 99.9, c["pages"])
        chk("擷取覆蓋(不含排除區)< 截取覆蓋:排除區有截到、不擷取(數得出差多少)", c["pages"][0]["extracted"] < c["pages"][0]["captured"], c["pages"])
        md = PRIOR.to_markdown(res)
        chk("輸出 md:本文表 # (S0001)| 據點 | 類別 | 次類別 | 字級 | 粗 | 內容 | 節.句 | 所屬標題 · 截取完整度表 · 去重行",
            "| # | 據點 | 類別 | 次類別 | 字級 | 粗 | 內容 | 節.句 | 所屬標題 |" in md and "## 截取完整度" in md and "去重修復" in md)
        h = page_html([res])
        chk("雙欄頁:左本文區 · 右資訊區 / 表格 / 圖(CSS grid,窄螢幕上下疊)", "lr-grid" in h and "本文區(左)" in h and "資訊區 · 表格 · 圖(右)" in h
            and "@media (max-width:900px)" in h)
        # 截取完整度抓漏:把一句從本文刪掉 → RED 並列缺字片段
        res2 = restore_pdf(pdf, "1")
        gone = res2["pages"][0]["body"].pop(3)
        c2 = completeness(res2, _src_pages(pdf, [1]))
        chk("抓漏:刪掉一句 → 截取完整度 RED · 缺字片段指出那一句", c2["verdict"] == "RED" and c2["pages"][0]["segments"]
            and any(re.sub(r"\W", "", seg["text"])[:4] in re.sub(r"\W", "", gone["text"]) for seg in c2["pages"][0]["segments"]),
            c2["pages"][0].get("segments"))
        # 去重:三頁同樣的頁眉 + 同頁重複句
        import fitz
        q = Path(td) / "three.pdf"
        doc = fitz.open()
        for i in range(3):
            pg = doc.new_page(width=595, height=842)
            pg.insert_text((40, 40), "EARNINGS INSIGHT WEEKLY", fontname="hebo", fontsize=16)
            for j in range(6):
                pg.insert_text((40, 90 + j * 14), f"Page {i + 1} line {j + 1} has distinct content about demand trends.", fontname="helv", fontsize=10)
            pg.insert_text((40, 190), f"Note {i + 1} repeats on this page.", fontname="helv", fontsize=10)
            pg.insert_text((40, 204), f"Note {i + 1} repeats on this page.", fontname="helv", fontsize=10)
        doc.save(str(q))
        doc.close()
        r3 = restore_pdf(q, "all")
        heads = [x["text"] for pp in r3["pages"] for x in pp["body"] if "EARNINGS INSIGHT" in x["text"]]
        ex = [x for pp in r3["pages"] for x in pp["excluded"] if x.get("dedup")]
        chk("去重:跨頁頁眉只留第一頁 · 其餘兩頁移到排除區(理由 跨頁重複)", len(heads) == 1 and sum("跨頁重複" in x["reason"] for x in ex) == 2,
            (heads, [x["reason"] for x in ex]))
        chk("去重:同頁重複句只留一次(每頁各去一句 · 原文留在排除區)", sum(x["reason"] == "同頁重複句" for x in ex) == 3
            and all(x.get("text") for x in ex), [x["reason"] for x in ex])
        chk("去重後截取完整度仍 GREEN(去掉的在排除區,不算漏)", r3["completeness"]["verdict"] == "GREEN", r3["completeness"]["pages"])
    real = PRIOR.VIA / "supportive modules" / "specs" / "EarningsInsight_062626.pdf"
    if real.exists():
        r = restore_pdf(real, "all")
        c = r["completeness"]
        chk("真實 31 頁:每頁截取完整度 GREEN(含 p2 目錄自列項)· 跨頁頁眉去重", c["verdict"] == "GREEN" and r["dedup"]["cross_page_keys"] >= 1,
            [(x["page"], x["captured"]) for x in c["pages"] if x["state"] != "GREEN"])
        chk("目錄自列項:「Table of Contents | 2」是目錄表的一列", any(["Table of Contents", "2"] in t["rows"] for t in r["pages"][1]["info"]
                                                               if t.get("subcategory") == "TOC"))
    else:
        print("  [—] 倉內真實樣本不在 → 真實回歸略過(誠實記缺件)")
    t = text_restore(PRIOR.FX_CITI)
    chk("文字模式也編號 · 也算完整度", t["completeness"]["pages"][0]["captured"] >= 99.0 and all(x.get("no") for x in t["body"]),
        t["completeness"]["pages"][0])
    body = Path(__file__).read_text(encoding="utf-8")
    chk("帶加速器橋 · VIA_FROM_VCGC 標記 · 不匯入 TA-Lib", "[VIA:ACCEL-BRIDGE" in body and "VIA_FROM_VCGC" in body
        and not re.search(r"^\s*(import|from)\s+" + "ta" + r"lib\b", body, re.M))
    print("--- 前版 v0100 全套自測(本版編號 / 完整度 / 雙欄照開;去重關閉 —— 跨頁頁眉只留一次是本版新行為,由上方去重檢驗)---")
    global DEDUP
    DEDUP = False
    try:
        prc = PRIOR.selftest()
    finally:
        DEDUP = True
    chk("前版自測在本版下仍全過(去重關)", prc == 0)
    print(f"[VRN_ENG394 v0101 雙欄 · 編號 · 完整度 · 去重] 自測 {sum(ok)}/{len(ok)} {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


def main() -> int:
    if "--selftest" in sys.argv[1:]:
        return selftest()
    return PRIOR.main()


if __name__ == "__main__":
    sys.exit(main())

