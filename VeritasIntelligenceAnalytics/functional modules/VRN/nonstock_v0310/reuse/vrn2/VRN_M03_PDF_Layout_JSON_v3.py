#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""reuse/vrn2/VRN_M03_PDF_Layout_JSON_v3 — VIA 版面轉接(給非個股摘要器 v0310 用的同名介面)。

v0310 引擎要兩個函數:
  analyze_pdf_layout(path, use_ocr_for_image_only=False) -> [ {page: 0-based, spans: [ {text, role, bbox(x0,y0,x1,y1), size} ]} ]
  extract_blocks_pymupdf(path, page_index) -> [物件(.text)]
實作:PyMuPDF(fitz)取 span / block 座標與字級;角色(TITLE / SUBTITLE / SECTION_HEADING / BODY)用「本頁字級階層」推定;
VIA 鎖版版面席位 SUP_MDL743_GenericLayoutHub 在、且收容件 GLE 掛得上時,拿它的 zone_annotate(九宮分區 + 字重階層)補 zone / weight 欄
(單一實作 · Zero-Hydra);掛不上就誠實記 layout_seat = ABSENT,角色照字級。只讀 PDF · 不寫檔 · 零網路([VIA:NET-BRIDGE] 留名)。
"""
from __future__ import annotations
import importlib.util
import sys
from pathlib import Path

LAYOUT_SEAT = None
_SEAT_MOD = None


def _via_root() -> Path | None:
    p = Path(__file__).resolve()
    while p.parent != p:
        if (p / "supportive modules").is_dir() and (p / "functional modules").is_dir():
            return p
        p = p.parent
    return None


def _seat():
    """鎖版版面席位(VIA_ToolVersion_Lock 的 layout 那一支);載不到回 None(誠實 absent)。"""
    global LAYOUT_SEAT, _SEAT_MOD
    if _SEAT_MOD is not None or LAYOUT_SEAT == "ABSENT":
        return _SEAT_MOD
    via = _via_root()
    try:
        import json
        lock = json.loads((via / "supportive modules" / "registry" / "VIA_ToolVersion_Lock_v0100.json").read_text(encoding="utf-8"))
        path = via.parent / lock["layout"]["path"] if not Path(lock["layout"]["path"]).is_absolute() else Path(lock["layout"]["path"])
        if not path.is_file():
            path = via / lock["layout"]["path"].split("VeritasIntelligenceAnalytics/", 1)[-1]
        spec = importlib.util.spec_from_file_location("via_layout_seat", path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules["via_layout_seat"] = mod
        spec.loader.exec_module(mod)
        _SEAT_MOD, LAYOUT_SEAT = mod, path.name
    except Exception:                                       # noqa: BLE001 — 席位掛不上就 absent,角色照字級
        LAYOUT_SEAT = "ABSENT"
    return _SEAT_MOD


class _Block:
    __slots__ = ("text", "bbox", "page")

    def __init__(self, text, bbox, page):
        self.text, self.bbox, self.page = text, bbox, page


def _fitz():
    import fitz  # PyMuPDF(桌機 via_core 有 · 容器系統 Python 沒有 → ImportError 照實)
    return fitz


def _roles(spans: list) -> None:
    sizes = sorted({round(s["size"], 1) for s in spans if s["text"].strip()}, reverse=True)
    if not sizes:
        return
    body = max(set(round(s["size"], 1) for s in spans), key=lambda z: sum(len(s["text"]) for s in spans if round(s["size"], 1) == z))
    for s in spans:
        z = round(s["size"], 1)
        if z >= sizes[0] and z > body * 1.25:
            s["role"] = "TITLE"
        elif len(sizes) > 1 and z >= sizes[1] and z > body * 1.12:
            s["role"] = "SUBTITLE"
        elif z > body * 1.04 or (s.get("bold") and len(s["text"]) <= 40):
            s["role"] = "SECTION_HEADING"
        else:
            s["role"] = "BODY"


def analyze_pdf_layout(path, use_ocr_for_image_only: bool = False) -> list:
    fitz = _fitz()
    out = []
    with fitz.open(str(path)) as doc:
        for pi, page in enumerate(doc):
            W, H = page.rect.width, page.rect.height
            spans, blocks = [], []
            d = page.get_text("dict")
            for b in d.get("blocks", []):
                if b.get("type") != 0:
                    continue
                x0, y0, x1, y1 = b["bbox"]
                btxt, bsize, bfont, bbold = [], 0.0, "", False
                for ln in b.get("lines", []):
                    for sp in ln.get("spans", []):
                        t = sp.get("text", "")
                        if not t.strip():
                            continue
                        bold = bool(sp.get("flags", 0) & 16) or "Bold" in sp.get("font", "")
                        spans.append({"text": t, "bbox": tuple(sp["bbox"]), "size": float(sp.get("size", 0)), "font": sp.get("font", ""), "bold": bold, "role": "BODY"})
                        btxt.append(t); bsize = max(bsize, float(sp.get("size", 0))); bfont = bfont or sp.get("font", ""); bbold = bbold or bold
                if btxt:
                    blocks.append({"x0": x0, "y0": y0, "x1": x1, "y1": y1, "size": bsize, "lines": len(b.get("lines", [])), "font": bfont, "bold": bbold})
            _roles(spans)
            zone = None
            seat = _seat()
            if seat is not None and hasattr(seat, "zone_annotate") and blocks:
                try:
                    zone = seat.zone_annotate(blocks, W, H)
                except Exception:                           # noqa: BLE001 — 席位算不出就不補
                    zone = None
            out.append({"page": pi, "width": W, "height": H, "spans": spans, "layout_seat": LAYOUT_SEAT or "ABSENT",
                        "zone": zone if isinstance(zone, dict) and zone.get("available", True) else None})
    return out


def extract_blocks_pymupdf(path, page_index: int) -> list:
    fitz = _fitz()
    with fitz.open(str(path)) as doc:
        page = doc[page_index]
        items = []
        for b in page.get_text("blocks"):
            if len(b) >= 7 and b[6] != 0:
                continue
            text = (b[4] or "").strip()
            if text:
                items.append(_Block(text, tuple(b[:4]), page_index + 1))
        return items


def selftest(pdf: str | None = None) -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond)); print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)) if note else ""))
    try:
        _fitz()
    except ImportError:
        print("[ABSENT] PyMuPDF(fitz)不在本直譯器 → 版面轉接測不了(桌機 via_core 有;容器用 venv)")
        return 3
    sample = Path(pdf) if pdf else None
    if sample is None:
        via = _via_root()
        for cand in (via / "functional modules" / "WorkOps" / "VeritasPulse" / "output" / "VRN_Meeting_Minutes.pdf", via / "supportive modules" / "specs" / "EarningsInsight_062626.pdf"):
            if cand.is_file():
                sample = cand; break
    if sample is None or not sample.is_file():
        print("[ABSENT] 沒有樣本 PDF"); return 3
    lay = analyze_pdf_layout(sample)
    chk("① analyze_pdf_layout:每頁 page(0-based)· spans 有 text / role / bbox / size", lay and all({"page", "spans"} <= set(p) for p in lay) and all({"text", "role", "bbox", "size"} <= set(s) for p in lay for s in p["spans"]), "%d 頁 · %d spans" % (len(lay), sum(len(p["spans"]) for p in lay)))
    roles = {s["role"] for p in lay for s in p["spans"]}
    chk("② 角色只在 TITLE / SUBTITLE / SECTION_HEADING / BODY · 本文有 BODY", roles <= {"TITLE", "SUBTITLE", "SECTION_HEADING", "BODY"} and "BODY" in roles, sorted(roles))
    blocks = extract_blocks_pymupdf(sample, 0)
    chk("③ extract_blocks_pymupdf:物件有 .text · 第一頁 > 0 塊", blocks and all(hasattr(b, "text") for b in blocks), len(blocks))
    chk("④ 版面席位誠實:%s" % (lay[0].get("layout_seat")), lay[0].get("layout_seat") in ("ABSENT",) or lay[0].get("layout_seat", "").startswith("SUP_MDL743"))
    bad = len(ok) - sum(ok)
    print("[%s] reuse/vrn2 Layout 轉接 · %d 項 · 不過 %d · 樣本 %s" % ("PASS" if not bad else "FAIL", len(ok), bad, sample.name))
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(selftest(sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else None))
