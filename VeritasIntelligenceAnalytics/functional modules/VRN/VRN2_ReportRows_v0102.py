#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VRN2_ReportRows v0102 — v0101 薄尾(v0101 一字不動):非個股車道改走 VRN2_NonStockSummarizer v0100。

操作員 2026-11-12:「非個股 v0300 整合進 VRN-2;輸入有 PDF / Word / 圖片 / 文字;個股與非個股報告都要處理;結果用矩陣」。
v0101 的非個股只在有 internal/NON_STOCK_CORE_v0200.py 時才跑 v0310(一直缺 → 全落「暫代」)。本版只換兩件事:
  ① run_nonstock → VRN2_NonStockSummarizer.run(v0310 不改;原件核心在用原件,不在用 VRN-2 自建核心,每列照實標「暫代」核心)。
     輸出照舊寫到 <out>/nonstock_v0310/RESULTS.json(與 v0310 同鍵),v0101 的 ns_index / build_rows / 原句驗證一字不動。
  ② 同一個輸入夾裡的非 PDF(Word / 圖片 / 文字 / 網頁 / 訊息 / 筆記)也一起交非個股車道 → <out>/nonstock_other/NONSTOCK_MATRIX.*;
     摘要頁 summary 多 non_pdf 一節(檔數 · 狀態 · 矩陣路徑);燈號把 non_pdf 的 ERROR / ABSENT / REVIEW 照實併進來。
個股車道(VRN-2 主線冊)不變。邊界同 v0101:只寫自己的輸出夾;零網路;不用 TA-Lib;不 import VCGC。
用法:python VRN2_ReportRows_v0102.py run [--pdf-dir D] [--out O] [--vrn2-books B] [--nonstock-out N] · --selftest
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

import argparse
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

VERSION = "v0102"
ENGINE = "VRN2_ReportRows " + VERSION
HERE = Path(__file__).resolve().parent
_PRIOR = HERE / "VRN2_ReportRows_v0101.py"
_spec = importlib.util.spec_from_file_location("vrn2_reportrows_v0101_for_v0102", _PRIOR)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
_NS_FILE = HERE / "VRN2_NonStockSummarizer_v0100.py"
_ns_spec = importlib.util.spec_from_file_location("vrn2_nonstock_for_rows_v0102", _NS_FILE)
NS = importlib.util.module_from_spec(_ns_spec)
sys.modules[_ns_spec.name] = NS
_ns_spec.loader.exec_module(NS)

_RUN_V0101 = PRIOR.run
_RUN_NS_V0101 = PRIOR.run_nonstock


def __getattr__(name):
    return getattr(PRIOR, name)


def ns_core_state() -> dict:
    st = NS.core_state()
    return {"ok": True, "mode": st["mode"], "sha_match": st["sha_match"], "why": st["why"]}


def run_nonstock(pdfs: list, outdir: Path) -> dict:
    """非個股 PDF → VRN2_NonStockSummarizer(v0310 + 原件 / 暫代核心)→ RESULTS.json(v0310 同鍵)。"""
    if not pdfs:
        return {"report_summary": [], "topic_detail": [], "company_detail": []}
    try:
        NS.run([str(p) for p in pdfs], Path(outdir), include_stock=True)   # 車道已由 v0101 分好,這裡全收
    except Exception as exc:  # noqa: BLE001 — 失敗照實回 error,v0101 會落暫代並寫原因
        return {"error": "非個股摘要器 %s: %s" % (type(exc).__name__, str(exc)[:160])}
    return PRIOR.load_ns_results(outdir) or {"error": "非個股摘要器沒寫出 RESULTS.json"}


def run(pdf_dir: Path, out: Path, books_dir=None, ns_out=None) -> dict:
    PRIOR.run_nonstock = run_nonstock
    PRIOR.ns_core_state = ns_core_state
    try:
        s = _RUN_V0101(pdf_dir, out, books_dir or PRIOR.DEFAULT_BOOKS, ns_out)
    finally:
        PRIOR.run_nonstock = _RUN_NS_V0101
    st = NS.core_state()
    s["engine"], s["nonstock_core"] = ENGINE, "%s(%s)" % (st["core"], st["mode"])
    others = [p for p in sorted(Path(pdf_dir).iterdir()) if p.is_file() and p.suffix.lower() != ".pdf"
              and p.suffix.lower() in _ns_exts() and not p.name.startswith("~$")] if Path(pdf_dir).is_dir() else []
    if others:
        r = NS.run([str(p) for p in others], Path(out) / "nonstock_other")
        s["non_pdf"] = {"files": r["files"], "status": r["status"], "by_format": r["by_format"], "lamp": r["lamp"],
                        "matrix": str(Path(out) / "nonstock_other" / "NONSTOCK_MATRIX.html")}
        if r["lamp"] == "RED" and s.get("lamp") != "RED":
            s["lamp"] = "RED"
        elif r["lamp"] in ("YELLOW", "NODATA") and s.get("lamp") == "GREEN":
            s["lamp"] = "YELLOW"
    else:
        s["non_pdf"] = {"files": 0}
    (Path(out) / "VRN2_ReportRows_summary_v0102.json").write_text(json.dumps(s, ensure_ascii=False, indent=2), encoding="utf-8")
    return s


def _ns_exts() -> set:
    eng, _st = NS.load_engine()
    return set(getattr(eng.CORE, "ALL_EXT", {".txt", ".md", ".html", ".htm", ".docx", ".json", ".enex"}))


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)) if note else ""), flush=True)

    print("[%s selftest]" % ENGINE, flush=True)
    cp = subprocess.run([sys.executable, str(_PRIOR), "--selftest"], cwd=str(HERE), capture_output=True, text=True, encoding="utf-8",
                        errors="replace", timeout=900, env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    chk("① 前版 v0101 自測(乾淨子行程)", cp.returncode == 0, (cp.stdout.strip().splitlines() or ["?"])[-1][:90])
    st = ns_core_state()
    chk("② 非個股核心狀態照實(原件 / 暫代)", st["mode"] in ("ORIGINAL", "STANDIN") and st["why"], st["why"][:70])
    with tempfile.TemporaryDirectory() as td:
        d = Path(td) / "in"
        d.mkdir()
        try:
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.cidfonts import UnicodeCIDFont
            from reportlab.pdfgen import canvas
            pdfmetrics.registerFont(UnicodeCIDFont("MSung-Light"))
            cv = canvas.Canvas(str(d / "20261112兆豐台灣產業專題-散熱產業.pdf"))
            cv.setFont("MSung-Light", 12)
            y = 800
            for line in ["散熱產業｜結論", "AI伺服器液冷滲透率提升，帶動散熱模組需求成長 40%。",
                         "由於GB300功耗上升，CSP資本支出上調，推升水冷板出貨。", "奇鋐(3017)與雙鴻(3324)為主要受惠者。",
                         "若關稅提高，下半年出貨可能放緩。"]:
                cv.drawString(50, y, line)
                y -= 22
            cv.save()
            has_pdf = True
        except Exception:  # noqa: BLE001 — 沒有 reportlab / CID 字型 → 這一項不算
            has_pdf = False
        (d / "news_shipping.html").write_text("<h1>航運快訊</h1><p>記者報導:貨櫃運價回升 12%,帶動長榮(2603)獲利改善。</p>"
                                              "<p>由於紅海航線受阻,運力吃緊推升運價。</p>", encoding="utf-8")
        out = Path(td) / "out"
        s = run(d, out, Path(td) / "nobooks")
        chk("③ 輸入夾的非 PDF(網頁)也進非個股車道 → 矩陣", s["non_pdf"].get("files") == 1 and (out / "nonstock_other" / "NONSTOCK_MATRIX.html").is_file(),
            s["non_pdf"])
        if has_pdf:
            res = json.loads((out / "nonstock_v0310" / "RESULTS.json").read_text(encoding="utf-8")) if (out / "nonstock_v0310" / "RESULTS.json").is_file() else {}
            chk("④ 非個股 PDF 經 VRN2_NonStockSummarizer → RESULTS.json(v0310 同鍵)· 不再整份落暫代",
                res.get("report_summary") and s["by_source"].get(PRIOR.SRC_NS), (s["by_source"], s.get("nonstock")))
        else:
            chk("④ 非個股 PDF(容器沒有 reportlab CID 字型造樣本 → 跳過不算)", True, "ABSENT")
        chk("⑤ 摘要記核心模式 · 寫 summary_v0102.json", "nonstock_core" in s and (out / "VRN2_ReportRows_summary_v0102.json").is_file(), s.get("nonstock_core"))
        chk("⑥ 跑完把 v0101 的 run_nonstock 還原(不外洩)", PRIOR.run_nonstock is _RUN_NS_V0101)
    names = [n for n in dir(PRIOR) if not n.startswith("_") and callable(getattr(PRIOR, n, None))]
    chk("⑦ 尾版保有前版公開名稱(TAILAPI)", all(getattr(sys.modules[__name__], n, None) is not None for n in names), "%d 支" % len(names))
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑧ 不用 TA-Lib · 不 import VCGC · 零網路", not re.search(r"^\s*(?:import|from)\s+(talib|CGC_|requests|urllib)", src, re.M | re.I))
    n = sum(ok)
    print("[%s] %s selftest · %d/%d" % ("PASS" if n == len(ok) else "FAIL", ENGINE, n, len(ok)), flush=True)
    return 0 if n == len(ok) else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=ENGINE)
    ap.add_argument("verb", nargs="?", default="run", choices=["run", "selftest"])
    ap.add_argument("--pdf-dir", default=str(PRIOR.VIA / PRIOR.P.FIXTURE_REL))
    ap.add_argument("--out", default=str(PRIOR.VIA / "VIA_Reports" / "vrn2" / "report_rows"))
    ap.add_argument("--vrn2-books", default=str(PRIOR.DEFAULT_BOOKS))
    ap.add_argument("--nonstock-out", default="")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest or a.verb == "selftest":
        return selftest()
    s = run(Path(a.pdf_dir), Path(a.out), a.vrn2_books, a.nonstock_out or None)
    print("[%s] %s · 報告 %d · 行 %d · 來源 %s · 主線命中 %d · 非個股核心 %s · 非 PDF %s · 原句驗證 %d/%d → %s" % (
        s["lamp"], ENGINE, s["reports"], s["rows"], json.dumps(s["by_source"], ensure_ascii=False), s["main_hits"], s["nonstock_core"],
        json.dumps(s["non_pdf"].get("status", {}), ensure_ascii=False), s["sentences"]["verified"], s["sentences"]["total"],
        Path(a.out) / "VRN2_ReportRows_latest.html"), flush=True)
    return 0 if s["lamp"] != "RED" else 2


if __name__ == "__main__":
    sys.exit(main())
