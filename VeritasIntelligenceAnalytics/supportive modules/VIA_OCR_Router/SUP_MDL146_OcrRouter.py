# -*- coding: utf-8 -*-
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
# VIA OCR 統一路由器 v0100(ENG-026)— 全平台 OCR/擷取引擎的探測·裁決·薄執行層
#
# 背景(操作員 2026/08/08:review vrn system…apply all necessary engines, local free
#   tools/libs, register):平台三處各有 OCR 家底 —
#   VRN MDL005(fitz→pdfplumber→pdfminer→PaddleOCR 四段)/MDL004(表格+PaddleOCR)、
#   Forge(PIL+pytesseract+tesseract 二進位)、PMIS(surya 選配+no-OCR 檔名錨,純 stdlib)。
#   缺的是「統一探測與路由」:任一台機器上,消費者無從得知哪幾段活著。
# 本檔(全部本機免費工具,零雲端):
#   probe            誠實列出每一段的可用性(模組 import + 二進位偵測)
#   route <檔>       依副檔名×可用性裁決最佳引擎(正本仍在 VRN/Forge/PMIS,本檔不複製)
#   extract <檔>     薄執行:PDF 文字層(fitz→pdfplumber→pdfminer 首個可用)/
#                    影像(pytesseract 若在)/末梯永遠可用=PMIS 檔名錨(不空手)
# 治理:唯讀輸入;重 OCR(PaddleOCR/surya)只路由不代跑(各自隔離 env 依 EnvManager);
#   誠實回報 engine_used 與降級原因;exit 0 成 / 1 無可用 / 3 前置缺。
import argparse
import importlib.util
import json
import shutil
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent            # VIA_OCR_Router/
VIA = HERE.parent.parent                          # VeritasIntelligenceAnalytics/
PMIS_OCR = VIA / "supportive modules" / "PMIS-Lite" / "pmis_lite" / "pmis_lite" / "ocr_intake.py"
VRN_005 = VIA / "functional modules" / "VRN" / "VRN_ENG018_MDL005OCRFetchingPDFText.py"
VRN_004 = VIA / "functional modules" / "VRN" / "VRN_ENG017_MDL004OCRFetchingPDFTable.py"

RUNGS = [
    # (鍵, 種類, 檢測法, 正本歸屬)
    ("fitz",       "pdf-text",  "mod:fitz",        "VRN MDL005 Engine A(PyMuPDF)"),
    ("pdfplumber", "pdf-text",  "mod:pdfplumber",  "VRN MDL005 Engine B"),
    ("pdfminer",   "pdf-text",  "mod:pdfminer",    "VRN MDL005 Engine C"),
    ("camelot",    "pdf-table", "mod:camelot",     "表格擷取(camelot_311 env 域)"),
    ("paddleocr",  "ocr-heavy", "mod:paddleocr",   "VRN MDL004/005 主力(paddle_311 env 域)"),
    ("pytesseract","ocr-image", "mod:pytesseract", "Forge 影像文字(需 tesseract 二進位)"),
    ("tesseract",  "bin",       "bin:tesseract",   "本機二進位(免費)"),
    ("easyocr",    "ocr-heavy", "mod:easyocr",     "選配"),
    ("surya",      "ocr-heavy", "mod:surya",       "PMIS ocr_intake 選配"),
    ("filename_anchor", "anchor", "file:PMIS",     "PMIS ocr_intake(純 stdlib,永遠可用)"),
]


def _has_mod(name):
    try:
        return importlib.util.find_spec(name) is not None
    except Exception:
        return False


def probe():
    out = {}
    for key, kind, how, owner in RUNGS:
        if how.startswith("mod:"):
            ok = _has_mod(how[4:])
        elif how.startswith("bin:"):
            ok = shutil.which(how[4:]) is not None
        else:
            ok = PMIS_OCR.exists()
        out[key] = {"kind": kind, "available": ok, "owner": owner}
    out["_originals"] = {"VRN_MDL005": VRN_005.exists(), "VRN_MDL004": VRN_004.exists(),
                        "PMIS_ocr_intake": PMIS_OCR.exists()}
    return out


def route(path):
    p = Path(path)
    ext = p.suffix.lower()
    av = probe()
    def ok(k):
        return av.get(k, {}).get("available")
    if ext == ".pdf":
        for k in ("fitz", "pdfplumber", "pdfminer"):
            if ok(k):
                return {"engine": k, "via": "VRN MDL005 文字層", "heavy_fallback":
                        "paddleocr" if ok("paddleocr") else None}
        if ok("paddleocr"):
            return {"engine": "paddleocr", "via": "VRN MDL005 OCR 段(paddle_311)"}
        return {"engine": "filename_anchor", "via": "PMIS no-OCR 錨點(文字層引擎全缺)"}
    if ext in (".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"):
        if ok("pytesseract") and ok("tesseract"):
            return {"engine": "pytesseract", "via": "Forge 影像文字"}
        if ok("paddleocr"):
            return {"engine": "paddleocr", "via": "VRN OCR"}
        if ok("surya"):
            return {"engine": "surya", "via": "PMIS 選配"}
        return {"engine": "filename_anchor", "via": "PMIS no-OCR 錨點"}
    return {"engine": "filename_anchor", "via": "非 PDF/影像 → 檔名錨點(或交 Forge 庫鍛)"}


def _anchor(path):
    spec = importlib.util.spec_from_file_location("via_pmis_ocr_intake", str(PMIS_OCR))
    m = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = m
    spec.loader.exec_module(m)
    return m.decompose_filename(str(path))


def extract(path):
    p = Path(path)
    if not p.exists():
        return {"ok": False, "error": "檔案不存在:%s" % p}
    r = route(path)
    eng = r["engine"]
    try:
        if eng == "fitz":
            import fitz
            doc = fitz.open(str(p))
            txt = "\n".join(pg.get_text() for pg in doc)
            doc.close()
            return {"ok": True, "engine_used": "fitz", "chars": len(txt), "text_head": txt[:400]}
        if eng == "pdfplumber":
            import pdfplumber
            with pdfplumber.open(str(p)) as doc:
                txt = "\n".join((pg.extract_text() or "") for pg in doc.pages)
            return {"ok": True, "engine_used": "pdfplumber", "chars": len(txt), "text_head": txt[:400]}
        if eng == "pdfminer":
            from pdfminer.high_level import extract_text
            txt = extract_text(str(p))
            return {"ok": True, "engine_used": "pdfminer", "chars": len(txt), "text_head": txt[:400]}
        if eng == "pytesseract":
            from PIL import Image
            import pytesseract
            txt = pytesseract.image_to_string(Image.open(str(p)), lang="chi_tra+eng")
            return {"ok": True, "engine_used": "pytesseract", "chars": len(txt), "text_head": txt[:400]}
        if eng in ("paddleocr", "surya"):
            return {"ok": False, "engine_used": None, "route": r,
                    "note": "重 OCR 段只路由不代跑 — 依 EnvManager 於隔離 env 內以 VRN 引擎執行"}
    except Exception as e:
        r["degrade_reason"] = str(e)[:200]
    anchor = _anchor(p)
    return {"ok": True, "engine_used": "filename_anchor", "route": r, "anchor": anchor,
            "note": "no-OCR 備援:不空手,回檔名錨點"}


def main():
    ap = argparse.ArgumentParser(description="VIA OCR 統一路由器:探測·裁決·薄執行(全本機免費)")
    ap.add_argument("command", nargs="?", default="probe", choices=["probe", "route", "extract"])
    ap.add_argument("path", nargs="?", default="")
    a = ap.parse_args()
    if a.command == "probe":
        out = probe()
        n = sum(1 for k, v in out.items() if not k.startswith("_") and v["available"])
        print(json.dumps(out, ensure_ascii=False, indent=1))
        print("[總結] 可用 %d / %d 段(檔名錨永遠在;重 OCR 依隔離 env)" % (n, len(RUNGS)))
        return 0
    if not a.path:
        print(json.dumps({"ok": False, "error": "%s 需要檔案路徑" % a.command}, ensure_ascii=False))
        return 3
    out = route(a.path) if a.command == "route" else extract(a.path)
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0 if out.get("ok", True) else 1


if __name__ == "__main__":
    sys.exit(main())
