#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL233_ToolActivate v0107 — 薄尾:PDFPLUMBER 樞紐(SUP_MDL746)與 OCR 隔離車道(via_ocr_super)掛進工具鎖冊

操作員 2026-10-03(VCGC-REQ134):「VRN 有 NLP / LAYOUT 支援確保版本都要註冊 · PRADDLE PDFPLUMBER 相關 OCR 工具都有掛入並編號」。
鎖冊原有七家(accelerator · network · layout · nlp · token · frame · praddle);PRADDLE 已掛,但它底下兩支 OCR 相關工具沒在鎖冊:
  pdfplumber = SUP_MDL746_PDFPlumberPlusHub(supportive modules/70_VRN_Rules;非 OCR 引擎 B 樞紐 + 重型 OCR 是否跑得動;
               必備 API ocr_ready · ocr_page · selftest · main)
  ocr        = via_ocr_super(supportive modules/registry;隔離境 OCR 車道 RapidOCR / PaddleOCR 探測與逐行座標;
               必備 API parse_box_output · run_lane_boxes · main)
檢查照前版原樣(夾 · 四位版號 · AST · 零 TA-Lib · 加速器橋 · 匯入層不開子行程 · 必備 API · 公開名稱不少於現役 · 參數只增不減 ·
冊上已登錄 · 席位恰一列);引擎版本冊席位列 VIA-TOOL-0229(pdfplumber)· VIA-TOOL-0230(ocr)與本版同批登錄(role=engine)。
`via-vcgc tools activate pdfplumber|ocr <檔> --apply` 才寫鎖冊。OCR 套件本身(paddle · rapidocr · onnxruntime)照舊不進主境、
不進鎖冊(在 via_ocr_super 的隔離境裡)。其餘照 v0106。只有 VCGC 能啟用。零網路。
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

import importlib.util
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL233_ToolActivate"
ENGINE = Path(__file__).stem



def _vnum_v0107(path: Path) -> int:
    m = re.search(r"_v(\d+)$", Path(path).stem)
    return int(m.group(1)) if m else -1


PRIOR = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0107(p) < _vnum_v0107(Path(__file__))), key=_vnum_v0107)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR)
_PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _PRIOR
_spec.loader.exec_module(_PRIOR)
BASE = _PRIOR.BASE
RULES_DIR = BASE.VIA / "supportive modules" / "70_VRN_Rules"
NEW_FAMILIES_V0107 = {
    "pdfplumber": ("SUP_MDL746_PDFPlumberPlusHub", RULES_DIR, ("ocr_ready", "ocr_page", "selftest", "main"), ()),
    "ocr": ("via_ocr_super", BASE.HERE, ("parse_box_output", "run_lane_boxes", "main"), ()),
}
BASE.FAMILIES.update(NEW_FAMILIES_V0107)
FAMILIES = BASE.FAMILIES
REGISTERED_V0107 = "冊上已登錄(VCGC 工具號)"


def __getattr__(name: str):
    return getattr(_PRIOR, name)


def main(argv=None) -> int:
    return _PRIOR.main(argv)


def selftest() -> int:
    for k in NEW_FAMILIES_V0107:               # 前版自測量前版那七家
        FAMILIES.pop(k, None)
    try:
        rc = _PRIOR.selftest()
    finally:
        FAMILIES.update(NEW_FAMILIES_V0107)
    results = []

    def chk(name, ok, note=""):
        results.append(bool(ok))
        print(f"  [{'OK' if ok else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    print(f"=== {ENGINE} · 薄尾自測(PDFPLUMBER · OCR 車道掛進工具鎖冊)===")
    chk("㊱ 前版鏈自測過(七家)", rc == 0, f"rc {rc}")
    chk("㊲ 九家同一把尺:accelerator · network · layout · nlp · token · frame · praddle · pdfplumber · ocr",
        set(FAMILIES) >= {"accelerator", "network", "layout", "nlp", "token", "frame", "praddle", "pdfplumber", "ocr"}, ", ".join(sorted(FAMILIES)))
    for fam, (stem, folder, _api, _) in NEW_FAMILIES_V0107.items():
        tails = sorted(folder.glob(stem + "_v*.py"), key=_vnum_v0107)
        if not tails:
            chk(f"㊳ {fam} 尾版不在 → 照實失敗(不冒充)", False, f"{stem}_v*.py 不在")
            continue
        res = BASE.checks(fam, tails[-1].name)
        bad = [c["check"] + ":" + c["detail"] for c in res if not c["ok"]]
        chk(f"㊳ {fam} 尾版過全部啟用檢查({tails[-1].name} · {len(res)} 檢;含冊上已登錄 · 席位恰一列)",
            not bad and any(c["check"] == REGISTERED_V0107 for c in res), "; ".join(bad)[:200])
    wrong = BASE.checks("ocr", "SUP_MDL746_PDFPlumberPlusHub_v0102.py")
    chk("㊴ 家別不對的檔擋下(PDFPLUMBER 檔不能當 OCR 車道啟用)", not all(c["ok"] for c in wrong))
    text = Path(__file__).read_text(encoding="utf-8")
    chk("㊵ 加速器橋在 · 不碰 TA-Lib · 本行程沒載任何 OCR 套件",
        "VIA:ACCEL-BRIDGE" in text and not re.search(r"^\s*(import|from)\s+talib", text, re.M)
        and not {"paddle", "paddleocr", "rapidocr_onnxruntime"} & {m.split(".")[0] for m in sys.modules})
    ok = rc == 0 and all(results)
    print(f"  {ENGINE} selftest +{sum(results)}/{len(results)} {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
