#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL233_ToolActivate v0106 — 薄尾:PRADDLE 擷取編排(VRN_ENG398)與 LAYOUT · NLP 同一把尺,經 VCGC 啟用、鎖版號

操作員 2026-10-02(VCGC-REQ128;原側線編 REQ127,與 main 每日交接同號 → 改編):「將 LAYOUT NPL 都有導入工具」—— PRADDLE(RapidOCR + PaddleOCR 雙引擎,隔離境)
要像 LAYOUT · NLP 一樣進工具鎖冊;LAYOUT(SUP_MDL743 v0110)· NLP(SUP_MDL866 v0106)再從鎖冊取它,不靠 glob 猜版本。
本版只把一家加進 FAMILIES:praddle = VRN_ENG398_PraddleExtractor(functional modules/VRN;必備 API main · selftest ·
run_pdf · ladder_page)。檢查照前版原樣(檔在該在的夾 · 四位版號 · AST · 零 TA-Lib · 加速器橋 · 匯入層不開子行程 ·
必備 API · 公開名稱不少於現役 · 參數只增不減 · 冊上已登錄 · 席位恰一列);`tools activate praddle <file> --apply` 才寫鎖冊。
引擎版本冊的席位列 VIA-TOOL-0224(role=engine)與本版同批登錄。
同批:LAYOUT v0110 · NLP v0106 先登 role=candidate(VIA-TOOL-0225 / 0226)、前版 v0109 / v0105 留 role=prior(0227 / 0228),
再經同一把尺啟用;前版鏈自測時 pinned() 對這兩家回鎖冊 previous(它們出貨時的現役),現役由 ㉟ 量。
OCR 套件本身(paddle · rapidocr · onnxruntime)不進鎖冊、不進主境:它們在 via_ocr_super 的隔離境裡,由車道探測報 READY / NO_ENV。
其餘照 v0105。只有 VCGC 能啟用。零網路。
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


def _vnum(path: Path) -> int:
    m = re.search(r"_v(\d+)$", Path(path).stem)
    return int(m.group(1)) if m else -1


PRIOR = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR)
_PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _PRIOR
_spec.loader.exec_module(_PRIOR)
BASE = _PRIOR.BASE
VRN_DIR = BASE.VIA / "functional modules" / "VRN"
NEW_FAMILIES = {
    "praddle": ("VRN_ENG398_PraddleExtractor", VRN_DIR, ("main", "selftest", "run_pdf", "ladder_page"), ()),
}
BASE.FAMILIES.update(NEW_FAMILIES)            # 前版的 checks / plan / apply / status 都讀這一本字典
FAMILIES = BASE.FAMILIES
REGISTERED = "冊上已登錄(VCGC 工具號)"
# v0101 ⑫ 寫死「layout v0109 · nlp v0105 對現役過全部檢查」—— 那是它出貨時的鎖冊。本版同批把兩家推到 v0110 / v0106,
# 前版鏈自測時 pinned() 對這兩家回鎖冊 previous(= 前版出貨時的現役),量前版當時的承諾;現役另由 ㉟ 量。
SHIPPED_V0106 = {"layout": "SUP_MDL743_GenericLayoutHub_v0109.py", "nlp": "SUP_MDL866_VIAUnifiedNLPOrchestrator_v0105.py"}
_PINNED_V0106 = BASE.pinned


def _pinned_as_shipped_v0106(family: str, root: Path | None = None) -> Path | None:
    if root is None and family in SHIPPED_V0106:
        prev = (BASE._json(BASE.lock_path()).get(family) or {}).get("previous") or {}
        p = BASE.REPO / str(prev.get("path") or "")
        if Path(str(prev.get("path") or "")).name == SHIPPED_V0106[family] and p.is_file():
            return p
    return _PINNED_V0106(family, root)


def __getattr__(name: str):
    return getattr(_PRIOR, name)


def main(argv=None) -> int:
    return _PRIOR.main(argv)


def selftest() -> int:
    for k in NEW_FAMILIES:                     # 前版自測量前版那六家
        FAMILIES.pop(k, None)
    BASE.pinned = _pinned_as_shipped_v0106     # 前版鏈量它出貨時的鎖冊(見 SHIPPED_V0106)
    try:
        rc = _PRIOR.selftest()
    finally:
        BASE.pinned = _PINNED_V0106
        FAMILIES.update(NEW_FAMILIES)
    results = []

    def chk(name, ok, note=""):
        results.append(bool(ok))
        print(f"  [{'OK' if ok else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    chk("㉛ 七家同一把尺:accelerator · network · layout · nlp · token · frame · praddle",
        set(FAMILIES) >= {"accelerator", "network", "layout", "nlp", "token", "frame", "praddle"}, ", ".join(sorted(FAMILIES)))
    tails = sorted(VRN_DIR.glob("VRN_ENG398_PraddleExtractor_v*.py"), key=_vnum)
    if tails:
        res = BASE.checks("praddle", tails[-1].name)
        bad = [c["check"] + ":" + c["detail"] for c in res if not c["ok"]]
        chk(f"㉜ praddle 尾版過全部啟用檢查({tails[-1].name} · {len(res)} 檢;含冊上已登錄 · 席位恰一列)",
            not bad and any(c["check"] == REGISTERED for c in res), "; ".join(bad)[:200])
    else:
        chk("㉜ praddle 尾版不在 → 照實失敗(不冒充)", False, "VRN_ENG398_PraddleExtractor_v*.py 不在")
    wrong = BASE.checks("praddle", "SUP_MDL866_VIAUnifiedNLPOrchestrator_v0105.py")
    chk("㉝ 家別不對的檔擋下(NLP 檔不能當 PRADDLE 啟用)", not all(c["ok"] for c in wrong))
    cur = {f: BASE.pinned(f) for f in ("layout", "nlp")}
    bad2 = {f: [c["check"] for c in BASE.checks(f, p.name) if not c["ok"]] for f, p in cur.items() if p}
    chk("㉟ 現役 LAYOUT · NLP(從鎖冊取 PRADDLE 的那兩支)過全部啟用檢查;前版出貨的 v0109 / v0105 留在冊上(role=prior)",
        all(cur.values()) and not any(bad2.values()) and BASE.pinned is _PINNED_V0106,
        {f: (p.name if p else None) for f, p in cur.items()} if not any(bad2.values()) else bad2)
    text = Path(__file__).read_text(encoding="utf-8")
    chk("㉞ 加速器橋在 · 不碰 TA-Lib · 本行程沒載任何 OCR 套件",
        "VIA:ACCEL-BRIDGE" in text and not re.search(r"^\s*(import|from)\s+talib", text, re.M)
        and not {"paddle", "paddleocr", "rapidocr_onnxruntime"} & {m.split(".")[0] for m in sys.modules})
    ok = rc == 0 and all(results)
    print(f"  {ENGINE} selftest +{sum(results)}/{len(results)} {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
