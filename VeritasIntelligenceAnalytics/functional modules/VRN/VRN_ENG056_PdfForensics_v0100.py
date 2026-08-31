#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
vrn_pdf_forensics_v0100 — PDF 法醫探針(唯讀;零輸出檔死因判定)
================================================================
動機:MQ-1560 solo 補擷引擎 exit 0 但 0 列(對 MDL004/005 隱形)。
本探針逐層檢死因,誠實輸出每層實測:
  F1 檔案層:存在/大小/%PDF- 簽章/EOF 標記(%%EOF)
  F2 開檔層:fitz 能否開/加密旗標/頁數;退 pdfplumber 交叉
  F3 文字層:逐頁 get_text 字元數 → 全零=純影像掃描件
  F4 影像層:逐頁影像物件數(掃描件特徵)
  F5 判決:OK_TEXT / IMAGE_ONLY_SCAN(候重 OCR)/ ENCRYPTED /
         CORRUPT_STRUCTURE / NOT_PDF / MISSING
用法:py vrn_pdf_forensics_v0100.py <pattern>(對 input/incoming 匹配)
     py vrn_pdf_forensics_v0100.py --file <path>(指定檔)
"""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(全引擎導入令 2026-08-18;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # accel_map/fetch/pip_install/run_fast
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def forensics(p: Path) -> dict:
    r = {"file": p.name, "layers": [], "verdict": "?"}

    def layer(name, ok, note):
        r["layers"].append({"layer": name, "ok": bool(ok), "note": str(note)})

    if not p.exists():
        layer("F1 檔案層", False, "檔案不存在")
        r["verdict"] = "MISSING"
        return r
    raw = p.read_bytes()
    size = len(raw)
    sig = raw[:8]
    has_sig = sig.startswith(b"%PDF-")
    has_eof = b"%%EOF" in raw[-2048:]
    layer("F1 檔案層", has_sig and has_eof,
          f"{size:,}B · 簽章={sig[:5].decode('latin1') if has_sig else repr(sig[:8])} · EOF標記={'有' if has_eof else '缺'}")
    if not has_sig:
        r["verdict"] = "NOT_PDF"
        return r

    doc = None
    try:
        import fitz
        try:
            doc = fitz.open(p)
            enc = doc.is_encrypted
            layer("F2 開檔層(fitz)", not enc, f"頁數 {doc.page_count} · 加密={'是' if enc else '否'}")
            if enc:
                r["verdict"] = "ENCRYPTED"
                return r
        except Exception as exc:
            layer("F2 開檔層(fitz)", False, f"{type(exc).__name__}: {str(exc)[:70]}")
    except ImportError:
        layer("F2 開檔層(fitz)", False, "fitz 未安裝(誠實 WARN)")

    if doc is None:
        try:
            import pdfplumber
            with pdfplumber.open(p) as pl:
                layer("F2 開檔層(pdfplumber 交叉)", True, f"頁數 {len(pl.pages)}")
                chars = sum(len(pg.extract_text() or "") for pg in pl.pages[:10])
                layer("F3 文字層(前10頁)", chars > 0, f"{chars:,} 字元")
                r["verdict"] = "OK_TEXT" if chars else "IMAGE_ONLY_SCAN"
                return r
        except Exception as exc:
            layer("F2 開檔層(pdfplumber 交叉)", False, f"{type(exc).__name__}: {str(exc)[:70]}")
            r["verdict"] = "CORRUPT_STRUCTURE"
            return r

    total_chars = 0
    total_imgs = 0
    per_page = []
    try:
        for i in range(min(doc.page_count, 50)):
            pg = doc[i]
            c = len(pg.get_text() or "")
            im = len(pg.get_images(full=True))
            total_chars += c
            total_imgs += im
            per_page.append(f"p{i + 1}:{c}字/{im}圖")
        layer("F3 文字層", total_chars > 0, f"共 {total_chars:,} 字元 · " + " ".join(per_page[:6]))
        layer("F4 影像層", True, f"共 {total_imgs} 影像物件")
        if total_chars > 0:
            r["verdict"] = "OK_TEXT"
        elif total_imgs > 0:
            r["verdict"] = "IMAGE_ONLY_SCAN"
        else:
            r["verdict"] = "CORRUPT_STRUCTURE"
    except Exception as exc:
        layer("F3 文字層", False, f"{type(exc).__name__}: {str(exc)[:70]}")
        r["verdict"] = "CORRUPT_STRUCTURE"
    finally:
        doc.close()
    return r


REMEDY = {
    "OK_TEXT": "文字層在——引擎零輸出屬引擎側過濾/例外,候引擎 log 深查",
    "IMAGE_ONLY_SCAN": "純影像掃描件——候重 OCR(paddleocr 渲染路徑;via-ocr route 末梯)",
    "ENCRYPTED": "加密 PDF——候解密或供應方重出",
    "CORRUPT_STRUCTURE": "結構損檔——候重新下載/重出;SSOT 記 spec-only 誠實除外",
    "NOT_PDF": "非 PDF(偽副檔名)——依實際格式改走對應解析鏈",
    "MISSING": "檔不在收件夾",
}


def main() -> int:
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 2
    if "--file" in args:
        files = [Path(args[args.index("--file") + 1])]
    else:
        files = sorted((HERE / "input/incoming").glob(args[0]))
    if not files:
        print(f"[FAIL] 無匹配:{args[0]}")
        return 1
    print(f"=== PDF 法醫探針 v0100(唯讀)· {len(files)} 檔 ===")
    worst = 0
    for f in files:
        r = forensics(f)
        print(f"  ── {r['file']} ──")
        for lyr in r["layers"]:
            print(f"     {'✓' if lyr['ok'] else '✗'} {lyr['layer']}:{lyr['note']}")
        print(f"  [判決] {r['verdict']} — {REMEDY.get(r['verdict'], '?')}")
        if r["verdict"] not in ("OK_TEXT",):
            worst = 1
    return worst


if __name__ == "__main__":
    sys.exit(main())
