#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_ENG397_P1Segment v0100 — 第一頁切割擷取檢視(操作員 2026-10-11:先切割再擷取 · 本文 / 上左右下資訊區分開 · 資訊區依類別再細切 · 頁區序號 + 大類小類 ·
   文表圖不混 · 不亂碼 · 斷句銜接不接標題 · 句號一句一筆 · 標題一行一筆 · 表格儲存格 TRIM · HTML U/I 看效果 · 先第一頁 · NON-OCR pdfplumber 為主 · 不能用馬上換)。
  PDF → pdfplumber(字詞 / 表格 / 圖)切區:頁首 T · 頁尾 B · 左 L / 右 R 資訊欄(依 x 方向最大空隙)· 本文 M(再分段落 / 表格 / 圖)· 資訊區依關鍵字細分小類
  擷取:每區用 pdfplumber 裁切擷取 · 亂碼(私用區 / 替代字元)超過門檻 → 換 pymupdf · NFKC 只套全形英數 / 相容漢字 · 中文字間去空格
  Word / TXT / 圖片 → 首頁 + 財報頁轉 OCR 好讀的 PNG 到 TEMP 排隊(Word / TXT 同時直接擷取文字)
  [VIA:AST-CLASS] 類別 = 引擎(第一頁切割擷取)· 入口 = VRN_SystemManager p1view 動詞
"""
from __future__ import annotations

# ===== [VIA:ACCEL-BRIDGE:v0111] 最新有版號的正本加速器(動態取最高 VeritasCeleritas_v####;退回鎖版 v1141)· 正本網路工具 VeritasAegisNexus_v1652(找不到 = 不改任何行為) =====
import importlib as _cb_il
import re as _cb_re
import sys as _cb_sys
from pathlib import Path as _cb_Path
_ACCEL, _ACCEL_VER = None, ""
_cb_p = _cb_Path(__file__).resolve()
while _cb_p.parent != _cb_p:
    if (_cb_p / "supportive modules").is_dir():
        _cb_sup = _cb_p / "supportive modules"
        _cb_c = sorted(list(_cb_sup.glob("VeritasCeleritas_v[0-9][0-9][0-9][0-9].py")) + list(_cb_sup.glob("*/VeritasCeleritas_v[0-9][0-9][0-9][0-9].py")),
                       key=lambda x: int(_cb_re.search(r"_v(\d{4})", x.name).group(1)))
        for _cb_d in [str(_cb_sup)] + ([str(_cb_c[-1].parent)] if _cb_c else []) + [str(x.parent) for x in list(_cb_sup.glob("*/VeritasAegisNexus_v1652.py"))[:1]]:
            if _cb_d not in _cb_sys.path:
                _cb_sys.path.insert(0, _cb_d)
        if _cb_c:
            try:
                _ACCEL, _ACCEL_VER = _cb_il.import_module(_cb_c[-1].stem), _cb_c[-1].stem
            except Exception:  # noqa: BLE001
                _ACCEL = None
        break
    _cb_p = _cb_p.parent
if _ACCEL is None:
    try:
        import VeritasCeleritas_v1141 as _ACCEL  # noqa: F401  退回鎖版
        _ACCEL_VER = "VeritasCeleritas_v1141"
    except Exception:  # noqa: BLE001
        _ACCEL = None


def _net():
    """正本網路工具(只在需要出網時載入;本引擎不出網)。"""
    try:
        import VeritasAegisNexus_v1652 as _NET  # noqa: WPS433
        return _NET
    except Exception:  # noqa: BLE001
        return None
# ===== [VIA:ACCEL-BRIDGE:END] =====

import html
import json
import os
import re
import sys
import tempfile
import unicodedata
import zipfile
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENGINE_ID, ENGINE_NAME = "VRN_ENG397", "P1Segment(第一頁切割擷取檢視)"
EXT = {".pdf": "PDF", ".docx": "WORD", ".doc": "WORD(舊)", ".txt": "TXT", ".png": "IMG", ".jpg": "IMG", ".jpeg": "IMG", ".tif": "IMG", ".tiff": "IMG", ".bmp": "IMG"}
MAJOR = {"T": "頁首", "B": "頁尾", "L": "左資訊區", "R": "右資訊區", "M": "本文"}
MINOR = [("RT", "評等 / 目標價", r"(?i)評等|rating|目標價|target|買進|buy|overweight|中立|neutral|持有|hold|outperform|增加持股"),
         ("AN", "分析師", r"(?i)@|tel\b|電話|analyst|分析師|研究員"),
         ("SD", "股價資料", r"(?i)股價|price|市值|market cap|52|成交|volume|股本|shares|流通|free float|外資|beta|收盤|close"),
         ("DS", "免責 / 揭露", r"(?i)免責|disclaimer|請參閱|important|僅供參考|版權|disclosure|certification"),
         ("DT", "日期 / 報告資訊", r"(?:19|20)\d{2}[/.\-年]\s?\d{1,2}|\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)")]
COLOR = {"T": (37, 99, 235), "B": (107, 114, 128), "L": (217, 119, 6), "R": (217, 119, 6), "M": (22, 163, 74), "TB": (220, 38, 38), "IMG": (124, 58, 237)}
_END = re.compile(r"[。！？!?]$|(?<![A-Z])\.$")
_BULLET = re.compile(r"^\s*(?:[•●■◆▪‧\-–—]|\(?\d{1,2}[).、]|[一二三四五六七八九十]+、)")
_FIN = re.compile(r"(?i)損益表|資產負債表|現金流量表|財務預測|財務摘要|income statement|balance sheet|cash flow|financial summary|eps|營收|revenue")


COMMON = set("請參閱聲明頁之免責揭露其及與等並於的一是不了人我在有他這中大來上國個到說們為子和你地出道也時年得就那要下以生會自著去之過家學對可她裡後小麼心多天而能好都然沒日於起還發成事只作當想看文無開手十用主行方又如前所本見經頭面公同三已老從動兩長知民樣現分將外但身些與高意進把法此實回二理美點月明其種聲全工己話兒者向情部正名定女問力機給等幾很業最間新什打便位因重被走電四第門相次東政海口使教西再平真聽世氣信北少關並內加化由卻代軍產入先山五太水萬市眼體別處總才場師書比住員九笑性通目華報立馬命張活難神數件安表原車白應路期叫死常提感金何更反合放做系計或司利受光王果親界及今京務制解各任至清物臺特程品認持營收毛淨稅益資負債權股價標評買賣出持增減季度預估元億百仟千息配率盈虧損費用銷售額利潤現金流量投融籌備率週轉存貨帳款應付收入支出成本營業外非控制母子合併財報表重點展望需求擴大提升優於年增率市值分析研究員電話證券投顧評等目標中立買進賣出持有增加減少逢低強勁液冷健策晶片半導體電子科技伺服器光通訊散熱零組件材料設備廠客戶訂單產能出貨毛利率營益率淨利率每股盈餘殖利率本益比淨值比報酬權益資產負債總計流動非流動長期短期借款折舊攤銷資本支出自由現金流第一二三四季上下半年度預估實際月週日元角萬億兆台灣美國中國日本韓國歐洲亞洲全球集團公司股份有限")


def garbled(s: str) -> float:
    if not s:
        return 0.0
    cid = sum(len(m) for m in re.findall(r"\(cid:\d+\)", s))
    bad = cid + sum(1 for c in s if c == "\ufffd" or 0xE000 <= ord(c) <= 0xF8FF or unicodedata.category(c) == "Co")
    return bad / len(s)


def quality(s: str, min_cjk: int = 2) -> tuple:
    """(分數, 常用字比例, 亂碼比例):合法但錯的字(字型編碼錯)用常用字比例判斷 · 中文 ≥min_cjk 字才判。"""
    cjk = [c for c in s if "\u3400" <= c <= "\u9fff"]
    ratio = (sum(1 for c in cjk if c in COMMON) / len(cjk)) if len(cjk) >= min_cjk else 1.0
    g = garbled(s)
    return ratio - 5 * g, ratio, g


def clean(s: str) -> str:
    """不亂碼:去私用區 / 替代字元 · 全形英數 / 相容漢字 / 部首 → NFKC · 中文字間去空格 · TRIM。"""
    out = []
    for c in re.sub(r"\(cid:\d+\)", "", s or ""):
        o = ord(c)
        if c == "\ufffd" or 0xE000 <= o <= 0xF8FF:
            continue
        if 0xFF01 <= o <= 0xFF5E or 0xF900 <= o <= 0xFAFF or 0x2E80 <= o <= 0x2FDF:
            c = unicodedata.normalize("NFKC", c)
        out.append(c)
    t = re.sub(r"[ \t\u3000]+", " ", "".join(out))
    t = re.sub(r"(?<=[\u3400-\u9fff\u3000-\u303f\uff00-\uffef]) (?=[\u3400-\u9fff\u3000-\u303f\uff00-\uffef])", "", t)
    return t.strip()


def records(lines: list, body_size: float = 0.0, mode: str = "body") -> list:
    """本文:標題(字大 / 短且不含逗號頓號冒號 %)一行一筆 · 句子到句號一句一筆 · 不接到標題 · 項目符號開新筆。資訊區(mode=info):一行一筆(標籤:值 不串句)。"""
    if mode == "info":
        return [{"kind": "資訊", "text": t} for t in (clean(x) for x, _ in lines) if t]
    out, buf = [], ""
    sizes = [z for _, z in lines if z]
    body_size = body_size or (sorted(sizes)[len(sizes) // 2] if sizes else 0)

    def flush(final=False):
        nonlocal buf
        parts = re.split(r"(?<=[。！？!?])|(?<=[^A-Z]\.)\s+(?=[A-Z])", buf)
        keep = []
        for p in parts:
            p = clean(p)
            if p and (_END.search(p) or final):
                out.append({"kind": "句", "text": p})
            elif p:
                keep.append(p)
        buf = " ".join(keep) if not final else ""
    for i, (raw, size) in enumerate(lines):
        t = clean(raw)
        if not t:
            continue
        is_head = not _END.search(t) and (bool(size and body_size and size >= body_size * 1.15)
                                          or (len(t) <= 18 and i + 1 < len(lines) and not buf and not re.search(r"[，,、；;：:%]", t)))
        if is_head and not _BULLET.match(t):
            flush(final=True)
            out.append({"kind": "標題", "text": t})
            continue
        if _BULLET.match(t) and buf:
            flush(final=True)
        sep = "" if (buf and re.search(r"[\u3400-\u9fff，、]$", buf) and re.match(r"[\u3400-\u9fff]", t)) else " "
        buf = (buf + sep + t).strip() if buf else t
        flush()
    flush(final=True)
    return out


def _lines(words: list) -> list:
    rows = []
    for w in sorted(words, key=lambda w: (round(w["top"] / 3), w["x0"])):
        if rows and abs(rows[-1]["top"] - w["top"]) <= 3:
            rows[-1]["ws"].append(w)
            rows[-1]["bottom"] = max(rows[-1]["bottom"], w["bottom"])
        else:
            rows.append({"top": w["top"], "bottom": w["bottom"], "ws": [w]})
    out = []
    for r in rows:
        ws = sorted(r["ws"], key=lambda w: w["x0"])
        txt = ""
        for a, b in zip([None] + ws[:-1], ws):
            txt += ("" if a is None else ("" if b["x0"] - a["x1"] < 1.5 else " ")) + b["text"]
        out.append({"text": txt, "size": max(float(w.get("size") or 0) for w in ws), "top": r["top"], "bottom": r["bottom"], "x0": ws[0]["x0"], "x1": max(w["x1"] for w in ws)})
    return out


def _blocks(lines: list, gap_k: float = 1.6) -> list:
    if not lines:
        return []
    hs = sorted(l["bottom"] - l["top"] for l in lines)
    lh = hs[len(hs) // 2] or 8
    blocks, cur = [], [lines[0]]
    for a, b in zip(lines, lines[1:]):
        if b["top"] - a["bottom"] > gap_k * lh:
            blocks.append(cur)
            cur = []
        cur.append(b)
    blocks.append(cur)
    return blocks


def _minor(text: str) -> tuple:
    for code, zh, rx in MINOR:
        if re.search(rx, text or ""):
            return code, zh
    return "TX", "文字"


def _inside(b, box, pad=1.0):
    return b[0] >= box[0] - pad and b[1] >= box[1] - pad and b[2] <= box[2] + pad and b[3] <= box[3] + pad


def segment(page) -> dict:
    """pdfplumber 頁物件 → 區塊清單(頁首 / 頁尾 / 左右資訊欄 / 本文 · 表格 / 圖 · 小類)。"""
    W, H = float(page.width), float(page.height)
    words = page.extract_words(x_tolerance=1.5, y_tolerance=3, keep_blank_chars=False, extra_attrs=["size"])
    tables = [t.bbox for t in page.find_tables()]
    images = [(float(i["x0"]), float(i["top"]), float(i["x1"]), float(i["bottom"])) for i in page.images if (i["x1"] - i["x0"]) * (i["bottom"] - i["top"]) > 0.01 * W * H]
    sizes = sorted(float(w.get("size") or 0) for w in words) or [0]
    body_size = sizes[len(sizes) // 2]
    big = max(sizes)
    top_cut, bot_cut = 0.11 * H, 0.90 * H
    title_ws = [w for w in words if float(w.get("size") or 0) >= max(body_size * 1.5, big * 0.9) and w["top"] < 0.35 * H]
    if title_ws:
        top_cut = max(top_cut, max(w["bottom"] for w in title_ws) + 2)
    mid = [w for w in words if w["top"] >= top_cut and w["bottom"] <= bot_cut]
    segs = []
    for x0, x1 in sorted((w["x0"], w["x1"]) for w in mid):
        if segs and x0 <= segs[-1][1] + 2:
            segs[-1][1] = max(segs[-1][1], x1)
        else:
            segs.append([x0, x1])
    split, side = None, None
    best = 0
    for a, b in zip(segs, segs[1:]):
        g = b[0] - a[1]
        left_w, right_w = a[1] - segs[0][0], segs[-1][1] - b[0]
        nl = sum(1 for w in mid if w["x1"] <= a[1] + 1)
        nr = sum(1 for w in mid if w["x0"] >= b[0] - 1)
        if g >= 6 and g > best and min(left_w, right_w) >= 0.06 * W and min(nl, nr) >= 3:
            best, split = g, (a[1] + b[0]) / 2
            side = "L" if left_w < right_w else "R"
    zones = []

    def add(major, bbox, kind, minor_code, minor_zh, ws=None, table=None):
        zones.append({"major": major, "bbox": [round(v, 1) for v in bbox], "kind": kind, "minor": minor_code, "minor_zh": minor_zh, "words": ws or [], "table": table})
    for major, ws in (("T", [w for w in words if w["bottom"] <= top_cut]), ("B", [w for w in words if w["top"] >= bot_cut])):
        for blk in _blocks(_lines(ws)):
            txt = " ".join(l["text"] for l in blk)
            code, zh = ("TT", "標題") if major == "T" and any(l["size"] >= big * 0.9 for l in blk) else _minor(txt)
            add(major, (min(l["x0"] for l in blk), blk[0]["top"], max(l["x1"] for l in blk), blk[-1]["bottom"]), "文", code, zh,
                [w for w in ws if blk[0]["top"] - 1 <= w["top"] <= blk[-1]["bottom"] + 1])
    body_box = (split if side == "L" else 0, top_cut, split if side == "R" else W, bot_cut) if split else (0, top_cut, W, bot_cut)
    side_box = ((0, top_cut, split, bot_cut) if side == "L" else (split, top_cut, W, bot_cut)) if split else None
    for tb in tables:
        major = "M" if _inside(tb, body_box, 6) or not side_box else side
        add(major, tb, "表", "TB", "表格", table=tb)
    for im in images:
        add("M" if _inside(im, body_box, 6) or not side_box else side, im, "圖", "IMG", "圖")
    blocked = tables + images
    free = [w for w in mid if not any(_inside((w["x0"], w["top"], w["x1"], w["bottom"]), b, 1) for b in blocked)]
    if side_box:
        sw = [w for w in free if _inside((w["x0"], w["top"], w["x1"], w["bottom"]), side_box, 2)]
        for blk in _blocks(_lines(sw), 1.3):
            txt = " ".join(l["text"] for l in blk)
            code, zh = _minor(txt)
            add(side, (min(l["x0"] for l in blk), blk[0]["top"], max(l["x1"] for l in blk), blk[-1]["bottom"]), "文", code, zh,
                [w for w in sw if blk[0]["top"] - 1 <= w["top"] <= blk[-1]["bottom"] + 1])
    bw = [w for w in free if _inside((w["x0"], w["top"], w["x1"], w["bottom"]), body_box, 2)]
    for blk in _blocks(_lines(bw), 2.2):
        add("M", (min(l["x0"] for l in blk), blk[0]["top"], max(l["x1"] for l in blk), blk[-1]["bottom"]), "文", "TX", "本文段落",
            [w for w in bw if blk[0]["top"] - 1 <= w["top"] <= blk[-1]["bottom"] + 1])
    order = {"T": 0, "L": 1, "R": 2, "M": 3, "B": 4}
    zones.sort(key=lambda z: (order[z["major"]], z["bbox"][1], z["bbox"][0]))
    seq = Counter()
    for z in zones:
        seq[z["major"]] += 1
        z["id"] = "P1·%s·%02d·%s" % (z["major"], seq[z["major"]], z["minor"])
    return {"W": W, "H": H, "zones": zones, "split": split, "side": side, "body_size": body_size}


def _pdfium(tp, bbox, H) -> str:
    x0, top, x1, bottom = bbox
    return tp.get_text_bounded(left=x0, bottom=H - bottom, right=x1, top=H - top) if tp is not None else ""


def extract_zone(page, z: dict, fz=None, tp=None) -> dict:
    """每區分開擷取:pdfplumber → 錯碼 / 常用字比例低 → pypdfium2(同框重抽)→ pymupdf → 都不行 → OCR 排隊。"""
    if z["kind"] == "圖":
        return {"engine": "—", "records": [], "rows": [], "garbled": 0.0, "needs_ocr": False}
    H = float(page.height)
    bad = lambda q: q[2] > 0.01 or q[1] < 0.6  # noqa: E731     觸發換引擎(中文 ≥2 字就判)
    ocr = lambda txt: garbled(txt) > 0.01 or quality(txt, 6)[1] < 0.4  # noqa: E731     送 OCR 要更嚴(中文 ≥6 字 · 常用字 <0.4 才送 · 常用字表有限不誤送)
    if z["kind"] == "表":
        crop = page.crop(z["bbox"], strict=False)
        try:
            ts = crop.find_tables()
            t = ts[0] if ts else None
            rows = t.extract() if t else (crop.extract_table() or [])
        except Exception:  # noqa: BLE001
            t, rows = None, []
        q = quality("".join("".join(c or "" for c in r) for r in rows))
        eng = "pdfplumber"
        if bad(q) and t is not None and tp is not None:
            rows = [[(_pdfium(tp, c, H) if c else "") for c in r.cells] for r in t.rows]
            q, eng = quality("".join("".join(r) for r in rows)), "pypdfium2(逐格換)"
        rows = [[clean(c or "") for c in r] for r in rows]
        return {"engine": eng, "rows": rows, "records": [], "garbled": round(q[2], 4), "common": round(q[1], 3), "needs_ocr": ocr("".join("".join(r) for r in rows))}
    lines = _lines(z["words"])
    cands = [("pdfplumber", [(l["text"], l["size"]) for l in lines])]
    q0 = quality("".join(l["text"] for l in lines))
    if bad(q0):
        if tp is not None:
            cands.append(("pypdfium2(換)", [(t, 0) for t in re.split(r"\r?\n", _pdfium(tp, z["bbox"], H))]))
        if fz is not None:
            try:
                import fitz  # noqa: WPS433
                cands.append(("pymupdf(換)", [(t, 0) for t in fz.get_text("text", clip=fitz.Rect(*z["bbox"])).splitlines()]))
            except Exception:  # noqa: BLE001
                pass
    scored = [(quality("".join(t for t, _ in ls)), e, ls) for e, ls in cands]
    q, eng, ls = max(scored, key=lambda x: x[0][0])
    need = ocr("".join(t for t, _ in ls))
    return {"engine": eng if not need else eng + " · 仍錯碼 → OCR 排隊", "records": records(ls, mode="body" if z["major"] == "M" else "info"), "rows": [], "garbled": round(q[2], 4),
            "common": round(q[1], 3), "needs_ocr": need}


def recategorize(z: dict):
    if z["kind"] == "文" and z["major"] in ("L", "R", "T", "B") and z["minor"] != "TT":
        z["minor"], z["minor_zh"] = _minor(" ".join(x["text"] for x in z.get("records") or []))
        z["id"] = re.sub(r"·[A-Z]+$", "·" + z["minor"], z["id"])


_FONTS = [r"C:\Windows\Fonts\msjh.ttc", r"C:\Windows\Fonts\mingliu.ttc", r"C:\Windows\Fonts\msyh.ttc", "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
          "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc", "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"]


def _font(size=22):
    from PIL import ImageFont
    for f in _FONTS:
        if Path(f).exists():
            try:
                return ImageFont.truetype(f, size)
            except OSError:
                continue
    return ImageFont.load_default()


def text_png(lines: list, dst: Path, width=1700, size=26) -> Path:
    """文字 → OCR 好讀的 PNG(白底黑字 · 大字級 · 中文字型)。"""
    from PIL import Image, ImageDraw
    f = _font(size)
    h = max(400, 60 + len(lines) * int(size * 1.6))
    im = Image.new("RGB", (width, h), "white")
    d = ImageDraw.Draw(im)
    for i, l in enumerate(lines):
        d.text((40, 30 + i * int(size * 1.6)), l[:90], fill="black", font=f)
    dst.parent.mkdir(parents=True, exist_ok=True)
    im.save(dst)
    return dst


def read_txt(p: Path) -> tuple:
    raw = p.read_bytes()
    for enc in ("utf-8-sig", "utf-8", "cp950", "big5", "gb18030", "utf-16"):
        try:
            t = raw.decode(enc)
            if garbled(t) < 0.001:
                return t, enc
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace"), "utf-8(替代)"


def read_docx(p: Path) -> tuple:
    try:
        import docx  # noqa: WPS433
        d = docx.Document(str(p))
        paras = [x.text for x in d.paragraphs]
        for t in d.tables:
            for r in t.rows:
                paras.append(" | ".join(clean(c.text) for c in r.cells))
        return "\n".join(paras), "python-docx"
    except Exception:  # noqa: BLE001
        with zipfile.ZipFile(p) as z:
            xml = z.read("word/document.xml").decode("utf-8", errors="replace")
        paras = [re.sub(r"<[^>]+>", "", m) for m in re.findall(r"<w:p[ >].*?</w:p>", xml, flags=re.S)]
        return "\n".join(html.unescape(x) for x in paras), "zip XML(換)"


def queue_dir() -> Path:
    return Path(os.environ.get("VIA_SPILL_DIR") or tempfile.gettempdir()) / "vrn_ocr_queue"


def non_pdf(p: Path, kind: str) -> dict:
    """Word / TXT / 圖片 → 首頁 + 財報頁 PNG 到 TEMP 排隊(Word / TXT 同時直接擷取 · 記錄)。"""
    q = queue_dir() / re.sub(r"[^\w\u4e00-\u9fff.-]+", "_", p.stem)[:60]
    out = {"kind": kind, "queue": str(q), "pngs": [], "records": [], "engine": "", "garbled": 0.0}
    if kind == "IMG":
        from PIL import Image
        im = Image.open(p).convert("RGB")
        if im.width < 1800:
            k = 1800 / im.width
            im = im.resize((1800, int(im.height * k)))
        q.mkdir(parents=True, exist_ok=True)
        im.save(q / "p1.png")
        out.update(pngs=[str(q / "p1.png")], engine="PIL")
        return out
    if kind == "WORD(舊)":
        out["engine"] = "需要 Word 轉 .docx(舊 .doc 無法直讀)"
        return out
    text, eng = read_txt(p) if kind == "TXT" else read_docx(p)
    lines = [clean(l) for l in text.splitlines() if clean(l)]
    out.update(engine=eng, garbled=round(garbled(text), 4), records=records([(l, 0) for l in lines[:60]]))
    out["pngs"].append(str(text_png(lines[:48], q / "p1.png")))
    starts, last = [], -10 ** 6
    for i, l in enumerate(lines):
        if _FIN.search(l) and i >= last + 40:                 # 財報段落起點 · 每 40 行一張(不重複輸出同一段)
            starts.append(i)
            last = i
    for n, i in enumerate(starts[:3]):
        out["pngs"].append(str(text_png(lines[i:i + 40], q / ("fin%d.png" % (n + 1)))))
    return out


def render(page, seg: dict, dst: Path, res=110) -> Path:
    from PIL import ImageDraw
    im = page.to_image(resolution=res).original.convert("RGB")
    k = res / 72.0
    d = ImageDraw.Draw(im)
    f = _font(14)
    for z in seg["zones"]:
        c = COLOR.get(z["minor"]) or COLOR[z["major"]]
        b = [v * k for v in z["bbox"]]
        d.rectangle(b, outline=c, width=2)
        d.text((b[0] + 2, max(b[1] - 15, 0)), z["id"], fill=c, font=f)
    dst.parent.mkdir(parents=True, exist_ok=True)
    im.save(dst)
    return dst


def run(indir: Path, rep: Path, one: str = "") -> dict:
    import pdfplumber  # noqa: WPS433
    indir, rep = Path(indir), Path(rep)
    od = rep / "p1view"
    (od / "img").mkdir(parents=True, exist_ok=True)
    items = sorted(p for p in indir.rglob("*") if p.is_file() and p.suffix.lower() in EXT and (not one or one in p.name))
    res = []
    for n, p in enumerate(items, 1):
        kind = EXT[p.suffix.lower()]
        rec = {"n": n, "file": p.name, "kind": kind, "stock": bool(re.search(r"(?<!\d)\d{4}(?!\d)", p.name))}
        try:
            if kind != "PDF":
                rec.update(non_pdf(p, kind))
                rec["lamp"] = "YELLOW" if rec.get("pngs") else "GRAY"
            else:
                fz = tp = None
                try:
                    import fitz  # noqa: WPS433
                    fz = fitz.open(str(p))[0]
                except Exception:  # noqa: BLE001
                    fz = None
                try:
                    import pypdfium2 as pdfium  # noqa: WPS433
                    tp = pdfium.PdfDocument(str(p))[0].get_textpage()
                except Exception:  # noqa: BLE001
                    tp = None
                with pdfplumber.open(str(p)) as pdf:
                    page = pdf.pages[0]
                    seg = segment(page)
                    q = queue_dir() / re.sub(r"[^\w\u4e00-\u9fff.-]+", "_", p.stem)[:60]
                    for z in seg["zones"]:
                        z.update(extract_zone(page, z, fz, tp))
                        recategorize(z)
                        z.pop("words", None)
                        if z.get("needs_ocr"):
                            q.mkdir(parents=True, exist_ok=True)
                            page.crop(z["bbox"], strict=False).to_image(resolution=300).original.save(q / (z["id"].replace("·", "_") + ".png"))
                    img = render(page, seg, od / "img" / ("%03d.png" % n))
                g = max([z["garbled"] for z in seg["zones"]] or [0])
                rec.update(zones=seg["zones"], side=seg["side"], img="img/%03d.png" % n, garbled=g,
                           lamp="RED" if g > 0.01 else ("GREEN" if seg["side"] and any(z["major"] == "M" for z in seg["zones"]) else "YELLOW"))
        except Exception as exc:  # noqa: BLE001
            rec.update(lamp="RED", err="%s: %s" % (type(exc).__name__, str(exc)[:120]))
        res.append(rec)
        print("  [切] %d/%d · %s · %s · %s" % (n, len(items), p.name[:40], kind, rec.get("err") or ("%d 區" % len(rec.get("zones") or []) if kind == "PDF" else "%d PNG 排隊" % len(rec.get("pngs") or []))), flush=True)
    (od / "P1VIEW_latest.json").write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    lampc = {"GREEN": "#16a34a", "YELLOW": "#eab308", "RED": "#dc2626", "GRAY": "#9ca3af"}
    nav = "".join("<a href='#f%d'><i style='background:%s'></i>%s</a>" % (r["n"], lampc[r["lamp"]], html.escape(r["file"][:34])) for r in res)
    secs = []
    for r in res:
        zrows = ""
        for z in r.get("zones") or []:
            body = ""
            if z.get("rows"):
                body = "<table class=t>" + "".join("<tr>" + "".join("<td>%s</td>" % html.escape(c) for c in row) + "</tr>" for row in z["rows"]) + "</table>"
            elif z.get("records"):
                body = "".join("<div class='%s'>%s</div>" % ("h" if x["kind"] == "標題" else "s", html.escape(x["text"])) for x in z["records"])
            zrows += "<tr><td><b>%s</b></td><td>%s · %s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (z["id"], MAJOR[z["major"]], z["minor_zh"], z.get("engine", ""),
                                                                                                    ("%.1f%%" % (100 * z.get("garbled", 0))) if z.get("garbled") else "0", body)
        if r["kind"] != "PDF":
            zrows = "<tr><td colspan=5>%s · 引擎 %s · 排隊 %s<br>%s</td></tr>" % (r["kind"], html.escape(str(r.get("engine", ""))), html.escape(str(r.get("queue", ""))),
                                                                            "".join("<div class='%s'>%s</div>" % ("h" if x["kind"] == "標題" else "s", html.escape(x["text"])) for x in r.get("records") or []))
        img = "<img src='%s'>" % r["img"] if r.get("img") else ""
        secs.append("<section id='f%d'><h3><i style='background:%s'></i>%s · %s%s</h3><div class=g><div class=pi>%s</div><div><table class=z><tr><th>編號</th><th>大類 · 小類</th><th>引擎</th><th>亂碼</th><th>擷取還原</th></tr>%s</table></div></div></section>" % (
            r["n"], lampc[r["lamp"]], html.escape(r["file"]), r["kind"], (" · " + html.escape(r["err"])) if r.get("err") else "", img, zrows))
    css = ("body{margin:0;font:13px system-ui,-apple-system,'Microsoft JhengHei',sans-serif;display:flex}nav{width:240px;height:100vh;overflow:auto;position:sticky;top:0;border-right:1px solid #e5e7eb;padding:6px}"
           "nav a{display:block;padding:3px 4px;color:#111;text-decoration:none;font-size:12px}i{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:5px}"
           "main{flex:1;padding:8px;overflow:auto}.g{display:grid;grid-template-columns:minmax(300px,46%) 1fr;gap:8px}.pi img{width:100%;border:1px solid #e5e7eb}"
           "table.z{border-collapse:collapse;width:100%}table.z td,table.z th{border:1px solid #e5e7eb;padding:3px;vertical-align:top;font-size:12px}.t td{border:1px solid #d1d5db;padding:1px 3px}"
           ".h{font-weight:700;color:#1d4ed8;margin:2px 0}.s{margin:1px 0}@media(max-width:900px){.g{grid-template-columns:1fr}nav{display:none}}")
    (od / "P1VIEW_latest.html").write_text("<!doctype html><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>第一頁切割擷取</title><style>%s</style><nav>%s</nav><main>"
                                           "<h2>第一頁切割擷取檢視 · %s · 框色:藍 頁首 · 橘 資訊欄 · 綠 本文 · 紅 表格 · 紫 圖 · 灰 頁尾</h2>%s</main>" % (css, nav, ENGINE_ID, "".join(secs)), encoding="utf-8")
    return {"n": len(res), "kinds": dict(Counter(r["kind"] for r in res)), "lamps": dict(Counter(r["lamp"] for r in res)), "zones": sum(len(r.get("zones") or []) for r in res),
            "queued": sum(len(r.get("pngs") or []) for r in res), "html": str(od / "P1VIEW_latest.html"), "errs": [r for r in res if r.get("err")][:4], "queue": str(queue_dir())}



def _fixture_pdf(path: Path):
    from reportlab.pdfgen import canvas
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.cidfonts import UnicodeCIDFont
    pdfmetrics.registerFont(UnicodeCIDFont("MSung-Light"))
    c = canvas.Canvas(str(path), pagesize=(595, 842))
    c.setFont("MSung-Light", 20)
    c.drawString(40, 800, "健策 3653 TT 液冷成長動能強勁")
    c.setFont("MSung-Light", 9)
    for i, t in enumerate(["評等:買進", "目標價:NT$650", "", "股價(10/1):520", "市值:NT$65bn", "", "分析師 王小明", "wang@kgi.com"]):
        if t:
            c.drawString(40, 700 - i * 14, t)
    c.setFont("MSung-Light", 10)
    y = 700
    for t in ["投資重點", "公司第三季營收年增 25%,優於", "預期。毛利率提升至 38%。", "", "", "展望", "明年液冷需求持續擴大。"]:
        if t:
            c.drawString(220, y, t)
        y -= 15
    xs, ys = [220, 320, 420, 520], [520, 500, 480, 460]
    for x in xs:
        c.line(x, ys[0], x, ys[-1])
    for yy in ys:
        c.line(xs[0], yy, xs[-1], yy)
    for r, row in enumerate([["年度", "2024A", "2025F"], ["營收", " 1,200 ", "1,500"], ["EPS", "10.5", "12.3"]]):
        for k, v in enumerate(row):
            c.drawString(xs[k] + 4, ys[r] - 14, v)
    c.setFont("MSung-Light", 7)
    c.drawString(40, 40, "請參閱最後一頁之免責聲明")
    c.save()


def selftest() -> int:
    import shutil
    p = f = 0

    def chk(name, cond):
        nonlocal p, f
        if cond:
            p += 1
            print("  [OK] %s" % name)
        else:
            f += 1
            print("  [FAIL] %s" % name)
    td = Path(tempfile.mkdtemp(prefix="eng397-"))
    saved = os.environ.get("VIA_SPILL_DIR")
    try:
        os.environ["VIA_SPILL_DIR"] = str(td / "spill")
        indir = td / "測試樣本報告"
        indir.mkdir()
        _fixture_pdf(indir / "KGI_3653 健策_20260915.pdf")
        import pdfplumber
        with pdfplumber.open(str(indir / "KGI_3653 健策_20260915.pdf")) as pdf:
            page = pdf.pages[0]
            seg = segment(page)
            import pypdfium2 as pdfium
            tp = pdfium.PdfDocument(str(indir / "KGI_3653 健策_20260915.pdf"))[0].get_textpage()
            for z in seg["zones"]:
                z.update(extract_zone(page, z, None, tp))
                recategorize(z)
        maj = Counter(z["major"] for z in seg["zones"])
        minors = {z["minor"] for z in seg["zones"] if z["major"] == "L"}
        chk("① 切割:頁首 T · 左資訊欄 L(依 x 最大空隙)· 本文 M · 頁尾 B · 共 %d 區 · %s" % (len(seg["zones"]), dict(maj)), seg["side"] == "L" and all(maj[k] for k in "TLMB"))
        info = [x["text"] for z in seg["zones"] if z["major"] == "L" for x in z["records"]]
        chk("② 資訊區依類別細切:評等 / 目標價 RT · 股價資料 SD · 分析師 AN → %s · 一行一筆(不串句)%s" % (sorted(minors), info[:3]),
            {"RT", "SD", "AN"} <= minors and "評等:買進" in info and "目標價:NT$650" in info)
        body = [x for z in seg["zones"] if z["major"] == "M" and z["kind"] == "文" for x in z["records"]]
        txt = [(x["kind"], x["text"]) for x in body]
        chk("③ 斷句銜接:標題「投資重點」「展望」各一筆 · 跨行句子接起來到句號 · 一句一筆 · 不接到標題 → %s" % txt[:4],
            ("標題", "投資重點") in txt and ("標題", "展望") in txt and any(k == "句" and t.startswith("公司第三季營收年增") and t.endswith("優於預期。") for k, t in txt)
            and ("句", "毛利率提升至 38%。") in txt and not any(k == "標題" and "。" in t for k, t in txt))
        tb = next((z for z in seg["zones"] if z["kind"] == "表"), None)
        chk("④ 表格獨立一區 · 儲存格 TRIM → %s" % (tb["rows"][:2] if tb else None), tb is not None and tb["rows"][0] == ["年度", "2024A", "2025F"] and tb["rows"][1] == ["營收", "1,200", "1,500"])
        engs = {z.get("engine", "") for z in seg["zones"]}
        chk("⑤ 不亂碼:私用區 / (cid:N) 剔除 · 全形轉半形 · 中文字間去空格 · 字型編碼錯(合法但錯的字)用常用字比例抓到 → 換 pypdfium2 · 本頁引擎 %s" % sorted(engs),
            clean("營\ue000收 １２３ 億 元(cid:98)") == "營收 123 億元" and garbled("營(cid:98)") > 0.5 and quality("兟岱貥砦煙菪緯崌")[1] < 0.6 and quality("公司第三季營收年增")[1] >= 0.9
            and any("pypdfium2" in e for e in engs))
        (indir / "6488_note.txt").write_bytes("環球晶 6488 法說會紀要\n營收年增 12%。\n損益表摘要\nEPS 30.5\n".encode("cp950"))
        (indir / "6488_note.docx").write_bytes(b"")
        with zipfile.ZipFile(indir / "6488_note.docx", "w") as z:
            z.writestr("word/document.xml", '<w:document><w:body><w:p><w:r><w:t>德微 3675 Memo</w:t></w:r></w:p><w:p><w:r><w:t>營收創新高。</w:t></w:r></w:p></w:body></w:document>')
        from PIL import Image
        Image.new("RGB", (800, 600), "white").save(indir / "3653_scan.jpg")
        o = run(indir, td / "rep")
        js = {r["file"]: r for r in json.loads((td / "rep" / "p1view" / "P1VIEW_latest.json").read_text(encoding="utf-8"))}
        tx, dx, ix = js["6488_note.txt"], js["6488_note.docx"], js["3653_scan.jpg"]
        chk("⑥ TXT(cp950 編碼不亂碼)→ 首頁 + 財報頁 PNG 排隊 %d 張 · 引擎 %s · Word → %s · 圖片 → PNG 放大到 1800 寬" % (len(tx["pngs"]), tx["engine"], dx["engine"]),
            tx["engine"] == "cp950" and len(tx["pngs"]) == 2 and any(x["text"] == "營收年增 12%。" for x in tx["records"]) and dx["engine"] in ("python-docx", "zip XML(換)")
            and any("營收創新高。" == x["text"] for x in dx["records"]) and Image.open(ix["pngs"][0]).width == 1800)
        htm = (td / "rep" / "p1view" / "P1VIEW_latest.html").read_text(encoding="utf-8")
        chk("⑦ HTML U/I:左檔案清單 · 右頁面圖(切割框)+ 各區擷取還原 · %d 檔 · %d 區" % (o["n"], o["zones"]), "<img src='img/" in htm and "P1·L·" in htm and "P1·M·" in htm and o["n"] == 4)
    finally:
        if saved is None:
            os.environ.pop("VIA_SPILL_DIR", None)
        else:
            os.environ["VIA_SPILL_DIR"] = saved
        shutil.rmtree(td, ignore_errors=True)
    me = Path(__file__).read_text(encoding="utf-8")
    chk("⑧ 最新有版號加速器橋 [VIA:ACCEL-BRIDGE:v0111]", "[VIA:ACCEL-BRIDGE:v0111]" in me)
    print("[計] %s v0100 自測 %d/%d · %s" % (ENGINE_ID, p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv[1:2]:
        raise SystemExit(selftest())
    print(json.dumps(run(Path(sys.argv[1]) if len(sys.argv) > 1 else Path(r"C:\測試樣本報告"), HERE / "_p1view_out"), ensure_ascii=False, default=str)[:1500])
