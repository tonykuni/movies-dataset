#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""SUP_MDL746 · PDFPlumberPlusHub v0102 —— 薄尾:重型 OCR 不裝作跑得動 · 同一行程只建一次 · 自測抽樣有上限

v0101→v0102(側線 2026-10-02 c;VCGC-REQ126 · VRN-REQ006):操作員令「專注 VCGC VRN VDF 成功啟動、結果驗證成功」
「只有輸出準確度提高、擷取更快:從 NON-OCR → OCR,從 pdfplumber 單引擎 → 雙引擎 → paddle 重型工具,無法才使用重型工具」。
工作站 VRN 鏈實錄(2026-10-02):本支 --selftest 逾時 180s · VRN_ENG072 逾時 600s,停掉前最後一行
`OCR 引擎載入失敗,掃描頁將標記為 NO_OCR:RuntimeError: Engine 'paddle_static' is unavailable because dependency 'paddlepaddle' is not installed`。
根因三條(全景 + 讀碼,收容件 VIA_PDFPlumberPlusEngine v1.0.0 與 v0101 一字不動):
  ① v0101 ocr_ready() 只看 paddleocr / numpy / pymupdf import 得到,不看推論核心 paddle(paddlepaddle)——paddleocr 在、paddle 不在的機器
     被報「可跑」,每一件掃描頁都去建 PaddleOCR(paddle 3.x 建構時要找核心、還可能找模型)再失敗。
  ② v0101 ocr_page() 每呼叫一次就 new 一個 _ScannedExtractor;收容件的 `_failed` 旗標只活一次呼叫 → 失敗不記,下一件重來。
  ③ v0101 自測 ⑥ 把整棵 VIA 樹的 PDF 全部 triage 一遍(工作站 incoming 幾十上百件)→ 180s 逾時;
     而且全庫沒有掃描檔時 ⑥ 必紅(容器 14 件全 DIGITAL/THIN 就紅)——拿「隨資料變的數」當斷言(同 LL332)。
本版:
  ① ocr_ready():前版說可跑之後再查 importlib.util.find_spec("paddle")(只看在不在,不 import);不在 → 不可跑並點名缺 paddlepaddle。
  ② 收容件的 _ScannedExtractor 在本行程按 OCR 參數只建一次(之後沿用同一個);建失敗過一次 → 之後 ocr_ready() 回 UNAVAILABLE、
     ocr_page() 標記帶 UNAVAILABLE(ENG072 看到會把 ppp:paddleocr 標壞,下一件直接跳過重型車道,不再每件重建)。
  ③ 自測:前版九檢照跑,只把 ⑥ 的全庫掃描封頂(VIA_PPP_SELFTEST_MAX,預設 40 件,依檔名排序取前段);
     樣本裡沒有掃描檔 → ⑥ 照實記 NODATA(rc 2,缺料不是壞掉),其餘任一檢紅照紅。
  判準(triage 規則表 · 密度門檻 · SPARSE_CHARS)一個字沒動;收容件原地不動;零網路;零彈窗;尾版律;Zero-Hydra;誠實降級留因由。
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

import contextlib
import importlib.util
import io
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "SUP_MDL746_PDFPlumberPlusHub"
PRIOR_PATH = max(p for p in HERE.glob(_STEM + "_v*.py") if p.name < Path(__file__).name)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_v0102", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)

SELFTEST_MAX = int(os.environ.get("VIA_PPP_SELFTEST_MAX") or 40)
_EXTRACTORS_V0102: dict = {}
_FAILED_V0102: dict = {}
_ORIG_READY_V0102 = PRIOR.ocr_ready
_ORIG_PAGE_V0102 = PRIOR.ocr_page


def __getattr__(name):
    return getattr(PRIOR, name)


def paddle_runtime() -> bool:
    """推論核心 paddle(套件名 paddlepaddle)在不在——只看 spec,不 import(import 很重)。"""
    try:
        return importlib.util.find_spec("paddle") is not None
    except (ImportError, ValueError):
        return False


def ocr_ready() -> tuple[bool, str]:
    """前版判準照舊;前版說可跑之後,再要推論核心在、且本行程沒建失敗過。"""
    ok, why = _ORIG_READY_V0102()
    if not ok:
        return ok, why
    if not paddle_runtime():
        return False, "缺 paddlepaddle(paddleocr 在但推論核心 paddle 不在;重型車道不開,免得每件掃描頁重建再失敗)"
    if _FAILED_V0102:
        return False, "UNAVAILABLE(本行程建 OCR 已失敗一次:" + next(iter(_FAILED_V0102.values()))[:80] + ")"
    return True, ""


def _ocr_key_v0102(P: dict) -> str:
    return json.dumps(sorted((k, repr(v)) for k, v in dict(P).items() if str(k).startswith("OCR")), ensure_ascii=False)


def _install_extractor_cache_v0102(m=None) -> bool:
    """收容件的 _ScannedExtractor 換成「同一組 OCR 參數本行程只建一次」的工廠(只改記憶體裡的模組屬性,不改檔)。"""
    m = m if m is not None else PRIOR._mod()
    if m is None or getattr(m, "_v0102_extractor_cache", False):
        return False
    real = m._ScannedExtractor

    def factory(P, *a, **k):
        key = _ocr_key_v0102(P)
        inst = _EXTRACTORS_V0102.get(key)
        if inst is None:
            inst = real(P, *a, **k)
            _EXTRACTORS_V0102[key] = inst
        return inst
    factory.__wrapped__ = real
    m._ScannedExtractor = factory
    m._v0102_extractor_cache = True
    return True


def ocr_page(pdf, page_no: int = 1) -> tuple[str, str]:
    """同前版;抽取器沿用同一個,建失敗過就把 UNAVAILABLE 帶在標記上(ENG072 據此把重型車道標壞)。"""
    _install_extractor_cache_v0102()
    text, tag = _ORIG_PAGE_V0102(pdf, page_no)
    for key, inst in list(_EXTRACTORS_V0102.items()):
        if getattr(inst, "_failed", False) and key not in _FAILED_V0102:
            _FAILED_V0102[key] = tag or "建 OCR 失敗"
    if not text and _FAILED_V0102 and "UNAVAILABLE" not in tag:
        tag = f"PPP_OCR_UNAVAILABLE(建 OCR 失敗,本行程不再重建)·{tag}"
    return text, tag


PRIOR.ocr_ready = ocr_ready          # 前版 ocr_page / status 以模組全域找 ocr_ready → 一起換上
PRIOR.ocr_page = ocr_page


class _CappedVIAV0102(type(Path())):
    """只給自測 ⑥ 用:rglob 依檔名排序取前 SELFTEST_MAX 件(其他路徑運算照 Path)。"""

    def rglob(self, pattern, *a, **k):
        hits = sorted(super().rglob(pattern, *a, **k))
        _CappedVIAV0102.seen = len(hits)
        return iter(hits[:SELFTEST_MAX])


_CappedVIAV0102.seen = 0


def selftest(tail_only: bool = False) -> int:
    print(f"=== {_STEM} v0102 · 薄尾自測(重型 OCR 不裝作跑得動 · 只建一次 · 自測抽樣封頂){' · 只驗薄尾' if tail_only else ''}===")
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    g = globals()
    keep_ready, keep_find = g["_ORIG_READY_V0102"], importlib.util.find_spec
    try:
        g["_ORIG_READY_V0102"] = lambda: (True, "")
        importlib.util.find_spec = lambda name, *a, **k: None if name == "paddle" else keep_find(name, *a, **k)
        r1 = ocr_ready()
        importlib.util.find_spec = lambda name, *a, **k: object() if name == "paddle" else keep_find(name, *a, **k)
        r2 = ocr_ready()
    finally:
        importlib.util.find_spec = keep_find
        g["_ORIG_READY_V0102"] = keep_ready
    chk("① paddleocr 在、推論核心 paddle 不在 → 不可跑並點名 paddlepaddle;核心在 → 照前版可跑",
        r1[0] is False and "paddlepaddle" in r1[1] and r2 == (True, ""), (r1, r2))

    class _FakeExtractor:
        built = 0

        def __init__(self, P):
            _FakeExtractor.built += 1
            self._failed = False

    class _FakeMod:
        _ScannedExtractor = _FakeExtractor

    keep_ex, keep_failed = dict(_EXTRACTORS_V0102), dict(_FAILED_V0102)
    _EXTRACTORS_V0102.clear()
    _FAILED_V0102.clear()
    try:
        fm = _FakeMod()
        _install_extractor_cache_v0102(fm)
        a = fm._ScannedExtractor({"OCR_LANG": "ch", "EMIT_JSON": False})
        b = fm._ScannedExtractor({"OCR_LANG": "ch", "EMIT_JSON": True})
        c = fm._ScannedExtractor({"OCR_LANG": "en"})
        chk("② 抽取器同一組 OCR 參數本行程只建一次(非 OCR 參數不影響);OCR 參數不同才另建",
            a is b and c is not a and _FakeExtractor.built == 2, f"建 {_FakeExtractor.built} 次")
        a._failed = True
        keep_page = g["_ORIG_PAGE_V0102"]
        g["_ORIG_PAGE_V0102"] = lambda pdf, page_no=1: ("", "PPP_OCR_NO_OCR(PaddleOCR)")
        try:
            t, tag = ocr_page("x.pdf", 1)
        finally:
            g["_ORIG_PAGE_V0102"] = keep_page
        g["_ORIG_READY_V0102"] = lambda: (True, "")
        keep_find2 = importlib.util.find_spec
        importlib.util.find_spec = lambda name, *a, **k: object() if name == "paddle" else keep_find2(name, *a, **k)
        try:
            r3 = ocr_ready()
        finally:
            importlib.util.find_spec = keep_find2
            g["_ORIG_READY_V0102"] = keep_ready
        chk("③ 建失敗過一次 → 標記帶 UNAVAILABLE(ENG072 據此標壞跳過)· 之後 ocr_ready 回不可跑,不再重建",
            t == "" and "UNAVAILABLE" in tag and r3[0] is False and "UNAVAILABLE" in r3[1], (tag, r3[1][:40]))
    finally:
        _EXTRACTORS_V0102.clear()
        _EXTRACTORS_V0102.update(keep_ex)
        _FAILED_V0102.clear()
        _FAILED_V0102.update(keep_failed)
    chk("④ 前版的 ocr_ready / ocr_page 已換成本版(前版內部呼叫也走同一把尺)",
        PRIOR.ocr_ready is ocr_ready and PRIOR.ocr_page is ocr_page)

    src = Path(__file__).read_text(encoding="utf-8")
    if tail_only:                       # 交接案用:只驗本版四件事 + 紀律(前版九檢隨資料變,完整自測留給 VRN 鏈)
        chk("⑥ 加速器橋在;收容件與前版一字不動(只改記憶體裡的屬性);零網路;不碰 TA-Lib",
            "[VIA:ACCEL-BRIDGE" in src and "import talib" not in src.replace('"import talib"', ""))
        state = "PASS" if all(ok) else "FAIL"
        print(f"  [計] {_STEM} v0102 本版 {sum(ok)}/{len(ok)} · 只驗薄尾 · {state}")
        return 0 if state == "PASS" else 1
    # ⑤ 前版九檢照跑(⑥ 的全庫掃描封頂);輸出照印,判讀 ⑥ 的缺料
    keep_via = PRIOR.VIA
    buf = io.StringIO()
    real_out = sys.stdout
    try:
        PRIOR.VIA = _CappedVIAV0102(keep_via)
        with contextlib.redirect_stdout(buf):
            prior_rc = PRIOR.selftest()
    finally:
        PRIOR.VIA = keep_via
    out = buf.getvalue()
    real_out.write(out)
    fails = [ln for ln in out.splitlines() if ln.strip().startswith("[FAIL]")]
    only6_nodata = bool(fails) and all(ln.strip().startswith("[FAIL] ⑥") and re.search(r"SCANNED 0\b", ln) for ln in fails)
    seen = _CappedVIAV0102.seen
    chk(f"⑤ 前版九檢照跑 · ⑥ 全庫掃描封頂 {SELFTEST_MAX} 件(樹上共 {seen} 件 PDF)",
        prior_rc == 0 or only6_nodata, f"前版 rc {prior_rc}" + (" · ⑥ 樣本無掃描檔 = NODATA(缺料不是壞掉)" if only6_nodata else ""))
    chk("⑥ 加速器橋在;收容件與前版一字不動(只改記憶體裡的屬性);零網路;不碰 TA-Lib",
        "[VIA:ACCEL-BRIDGE" in src and "import talib" not in src.replace('"import talib"', ""))
    own = all(ok)
    state = "PASS" if own and prior_rc == 0 else ("NODATA" if own and only6_nodata else "FAIL")
    print(f"  [計] {_STEM} v0102 本版 {sum(ok)}/{len(ok)} · 前版 rc {prior_rc} · {state}")
    return 0 if state == "PASS" else (2 if state == "NODATA" else 1)


def main() -> int:
    if "--selftest-tail" in sys.argv[1:]:
        return selftest(tail_only=True)
    if "--selftest" in sys.argv[1:]:
        return selftest()
    return PRIOR.main()


if __name__ == "__main__":
    sys.exit(main())
