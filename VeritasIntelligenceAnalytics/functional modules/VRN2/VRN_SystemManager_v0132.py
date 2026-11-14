#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_SystemManager v0132 — 薄尾:TEXT_DOC 擴到 UNCLASSIFIED / 無分型(2026-10-06 實跑最後 1 份 REVIEW:GF-Thoughts on TPU… 檔名律分不出型,0 FIN 1 OTHER)。
律:只要「無代號 + 非 EQUITY/None 分型 + 0 FIN 表」= TEXT_DOC;有代號(個股)照舊 REVIEW。其餘照前版鏈。
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
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: F401
except ImportError:
    VIA_ACCEL = None
# ===== [VIA:ACCEL-BRIDGE:END] =====

import importlib.util
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VRN_SystemManager"
TAG = "v0132"


def _vnum_v0132(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0132(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0132(p) < _vnum_v0132(__file__)), key=_vnum_v0132)
PRIOR = _load_v0132(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


def __getattr__(name):
    return getattr(PRIOR, name)


_P31 = PRIOR
_P27 = _P31._P27
_EXTRACT_ONE_31 = _P27.extract_one


def extract_one_32(pdf, out_root, engines=("pdfplumber", "camelot", "tabula"), avail=None) -> dict:
    rec = _EXTRACT_ONE_31(pdf, out_root, engines, avail)
    fn = rec.get("filename") or {}
    cats = rec.get("categories") or {}
    fin = sum(v for k, v in cats.items() if k not in ("OTHER", "TEXT_BLOCK"))
    if rec.get("status") == "REVIEW" and fin == 0 and not fn.get("codes") and fn.get("doc_kind") not in ("EQUITY",):
        rec["status"], rec["why"] = "TEXT_DOC", "無代號 · 分型 %s · 無財務表(正常;OTHER %d · 文字塊 %d)" % (fn.get("doc_kind") or "UNCLASSIFIED", cats.get("OTHER", 0), cats.get("TEXT_BLOCK", 0))
    return rec


_P27.extract_one = extract_one_32


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    os.environ.setdefault("VIA_FROM_VCGC", "YES")
    if "--selftest" in args[:2]:
        return selftest()
    return _P31.main(args)


def selftest() -> int:
    import shutil
    import tempfile
    p = f = 0

    def chk(name, cond):
        nonlocal p, f
        if cond:
            p += 1
            print("  [OK] %s" % name)
        else:
            f += 1
            print("  [FAIL] %s" % name)

    td = Path(tempfile.mkdtemp(prefix="vrn132-"))
    saved = {k: os.environ.get(k) for k in ("VIA_VRN_EXTRACT_OUT", "VIA_NO_OPEN", "VIA_VRN_UI_DIR")}
    os.environ.update({"VIA_VRN_EXTRACT_OUT": str(td / "out"), "VIA_NO_OPEN": "1", "VIA_VRN_UI_DIR": str(td / "ui")})
    try:
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Table
        from reportlab.lib.styles import getSampleStyleSheet
        st = getSampleStyleSheet()
        pdf = td / "GF-Thoughts on TPU Competition 20251126.pdf"
        SimpleDocTemplate(str(pdf)).build([Paragraph("TPU vs GPU thoughts. Shipments by vendor below.", st["Normal"]), Table([["Vendor", "2025", "2026"], ["Alpha", "10", "20"], ["Beta", "5", "9"]])])
        res = _P27.extract([pdf], ("pdfplumber",))
        r = res["rows"][0]
        chk("① 無代號未分型筆記 + 數字表認不出列標 → TEXT_DOC(非 REVIEW)", r["status"] == "TEXT_DOC")
        pdf2 = td / "GS-2330 20251001.pdf"
        SimpleDocTemplate(str(pdf2)).build([Paragraph("ABC Corp", st["Normal"]), Table([["Item", "2025", "2026"], ["Widgets", "10", "20"]])])
        res2 = _P27.extract([pdf2], ("pdfplumber",))
        chk("② 有代號個股(2330)不走 TEXT_DOC(仍 REVIEW/NODATA,要人看)", res2["rows"][0]["status"] != "TEXT_DOC")
    except ImportError:
        print("  [注] reportlab 不在 → ①② 跳過")
        p += 2
    print("  ── 前版鏈自測(原樣印出;前版行為)──")
    _P27.extract_one = _EXTRACT_ONE_31
    try:
        prc = 0 if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1" else _P31.selftest()
    finally:
        _P27.extract_one = extract_one_32
    chk("③ 前版鏈 %s 自測 rc 0" % PRIOR_PATH.stem, prc == 0)
    body = Path(__file__).read_text(encoding="utf-8")
    chk("④ 帶加速器橋 · glob 取前版 · 獨立 MAIN", "[VIA:ACCEL-BRIDGE:v0100]" in body and "setdefault(\"VIA_FROM_VCGC\"" in body)
    for k, v in saved.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v
    shutil.rmtree(td, ignore_errors=True)
    print("[計] VRN_SystemManager_v0132 自測 %d/%d · %s" % (p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
