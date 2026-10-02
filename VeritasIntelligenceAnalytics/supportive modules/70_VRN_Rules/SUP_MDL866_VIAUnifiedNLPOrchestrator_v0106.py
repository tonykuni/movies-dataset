#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SUP_MDL866 NLP tail v0106: NLP 導入 PRADDLE 工具(從工具鎖冊取,經 VCGC 才跑)。

操作員 2026-10-02(VCGC-REQ127):「將 LAYOUT NPL 都有導入工具」。
PRADDLE(VRN_ENG398)由 CGC_MDL233 v0106 啟用進鎖冊 `praddle`。本版只加一個動詞,其餘(status · text · pipeline · --brief)照 v0105:
  · `pdf --file <x.pdf> [--ocr auto|off|force] [--points N] [--compact] [--brief]`:
    PDF → 鎖冊那一支 PRADDLE(數位頁原生 + LAYOUT 修復鏈;掃描 / 編碼壞頁才走隔離境 RapidOCR → 不足才 PaddleOCR)
    → 修復後的閱讀順序段落(頁眉頁腳等雜訊已剔除)→ v0103 的 run_text(摘要 · 分類 · 標記)。
  · 只認鎖冊(檔在 · sha256 對得上);沒啟用 / 被改過 照實回 BLOCKED 與因由,不 glob 猜尾版。
  · 本行程不 import 任何 OCR 套件(它們在隔離境子行程裡)。只收 VCGC 呼叫。零網路。
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
import contextlib
import hashlib
import importlib.util
import json
import os
import re
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
PRIOR = HERE / "SUP_MDL866_VIAUnifiedNLPOrchestrator_v0105.py"
BODY = HERE / "SUP_MDL866_VIAUnifiedNLPOrchestrator_v0103.py"
VIA = HERE.parents[1]
REPO = VIA.parent
REGISTRY = VIA / "supportive modules" / "registry"
OCR_PKGS = ("paddle", "paddleocr", "rapidocr_onnxruntime", "onnxruntime", "cv2")
_MODS_V0106: dict = {}


def _load_v0106(path: Path, name: str):
    if name not in _MODS_V0106:
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        _MODS_V0106[name] = module
    return _MODS_V0106[name]


def _lock_v0106(registry: Path | None = None) -> dict:
    hits = sorted((registry or REGISTRY).glob("VIA_ToolVersion_Lock_v*.json"))
    if not hits:
        return {}
    try:
        return json.loads(hits[-1].read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def praddle_pinned(lock: dict | None = None, repo: Path | None = None) -> dict:
    """鎖冊 `praddle` 那一支:{state: PINNED | NOT_ACTIVATED | PINNED_FILE_MISSING | SHA_DRIFT, path, version, why}。"""
    ent = (lock if lock is not None else _lock_v0106()).get("praddle") or {}
    if not ent.get("path"):
        return {"state": "NOT_ACTIVATED", "why": "鎖冊沒有 praddle;經 VCGC:via-vcgc tools activate praddle <VRN_ENG398_…_vNNNN.py> --apply"}
    p = (repo or REPO) / ent["path"]
    if not p.is_file():
        return {"state": "PINNED_FILE_MISSING", "path": str(p), "why": f"鎖冊指的 {p.name} 不在"}
    raw = p.read_bytes()
    shas = {hashlib.sha256(raw).hexdigest(), hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest()}
    if ent.get("sha256") not in shas:
        return {"state": "SHA_DRIFT", "path": str(p), "why": f"{p.name} 跟鎖冊的 sha256 不同(被改過;要重新經 VCGC 啟用)"}
    return {"state": "PINNED", "path": str(p), "version": ent.get("version"), "why": ""}


def paragraphs_of(out_dir: Path) -> list:
    """PRADDLE 輸出夾裡 LAYOUT 修復後的段落(原生在前、OCR 在後;同頁照修復鏈的閱讀順序)。"""
    paras = []
    for i, f in enumerate(sorted(Path(out_dir).rglob("REPAIRED.json"), key=lambda p: ("ocr" in p.parts, str(p)))):
        try:
            doc = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        lane = "ocr" if "ocr" in f.parts else "native"
        for n, p in enumerate((doc.get("text") or {}).get("paragraphs") or []):
            t = str(p.get("text") or "").strip()
            if t:
                paras.append({"text": t, "role": p.get("role"), "pages": p.get("pages") or [], "lane": lane, "order": (i, n)})
    return paras


def pdf_text(pdf, ocr: str = "auto") -> dict:
    """PDF → 鎖冊 PRADDLE → 段落文字。回 {state, text, paragraphs, verdict, routes, pin}。"""
    pin = praddle_pinned()
    if pin["state"] != "PINNED":
        return {"state": "BLOCKED", "why": pin["why"], "pin": pin}
    tool = _load_v0106(Path(pin["path"]), "praddle_pinned_for_nlp_v0106")
    with tempfile.TemporaryDirectory(prefix="nlp_praddle_") as tmp:
        rep = tool.run_pdf(Path(pdf), ocr=ocr, out_root=Path(tmp))
        paras = paragraphs_of(Path(rep.get("out") or tmp))
    routes = [r.get("route") for r in rep.get("pages") or []]
    state = "PASS" if paras else "NODATA"
    return {"state": state, "text": "\n\n".join(p["text"] for p in paras), "paragraphs": len(paras),
            "lanes": sorted({p["lane"] for p in paras}), "verdict": rep.get("verdict"), "routes": routes,
            "no_ocr_pages": rep.get("no_ocr_pages") or [], "pin": pin, "sec": rep.get("sec")}


def run_pdf_text(pdf, points: int = 5, compact: bool = False, ocr: str = "auto") -> dict:
    got = pdf_text(pdf, ocr)
    if got["state"] != "PASS":
        return {k: v for k, v in got.items() if k != "text"}
    result = _load_v0106(BODY, "nlp_v0103_for_v0106").run_text(got["text"], points, compact)
    result["praddle"] = {k: v for k, v in got.items() if k != "text"}
    return result


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY", "why": "only via-vcgc"}, ensure_ascii=False))
        return 2
    args = sys.argv[1:]
    if not args or args[0] != "pdf":
        return _load_v0106(PRIOR, "nlp_v0105_for_v0106").main()
    ap = argparse.ArgumentParser(prog="SUP_MDL866 pdf")
    ap.add_argument("--file", required=True)
    ap.add_argument("--ocr", choices=("auto", "off", "force"), default="auto")
    ap.add_argument("--points", type=int, default=5)
    ap.add_argument("--compact", action="store_true")
    ap.add_argument("--brief", "-Brief", action="store_true")
    a = ap.parse_args(args[1:])
    with contextlib.redirect_stdout(sys.stderr):          # LAYOUT 進度行走 stderr;stdout 只留一份 JSON
        result = run_pdf_text(a.file, a.points, a.compact, a.ocr)
    if a.brief and result.get("state") == "PASS":
        shown = _load_v0106(BODY, "nlp_v0103_for_v0106").brief_of(result)
        shown["praddle"] = result["praddle"]
    else:
        shown = result
    print(json.dumps(shown, ensure_ascii=False, indent=2, default=str))
    return 0 if result.get("state") == "PASS" else 2


def selftest() -> int:
    print("=== SUP_MDL866 NLP v0106 · NLP 導入 PRADDLE(鎖冊)===")
    rc = _load_v0106(PRIOR, "nlp_v0105_selftest_for_v0106").selftest()   # 前版先跑(它會拿掉 VCGC 閘量 DENY)
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    chk("① 前版 v0105 自測過(只收 VCGC · --brief)", rc == 0)
    os.environ.pop("VIA_FROM_VCGC", None)
    argv, sys.argv = sys.argv, [sys.argv[0], "pdf", "--file", "x.pdf"]
    try:
        denied = main() == 2
    finally:
        sys.argv = argv
    os.environ["VIA_FROM_VCGC"] = "YES"
    chk("② pdf 動詞只收 VCGC 呼叫(沒有 VIA_FROM_VCGC=YES → DENY)", denied)
    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp)
        f = t / "VRN_ENG398_PraddleExtractor_v0100.py"
        f.write_text("x = 1\n", encoding="utf-8")
        good = hashlib.sha256(f.read_bytes()).hexdigest()
        states = (praddle_pinned({}, t)["state"],
                  praddle_pinned({"praddle": {"path": f.name, "sha256": "0" * 64}}, t)["state"],
                  praddle_pinned({"praddle": {"path": f.name, "sha256": good}}, t)["state"])
    chk("③ 只認鎖冊:沒啟用 / sha 不對 照實回因由,對得上才 PINNED(不 glob 猜尾版)",
        states == ("NOT_ACTIVATED", "SHA_DRIFT", "PINNED"), states)
    pin = praddle_pinned()
    chk("④ 實鎖冊 praddle 已經 VCGC 啟用且 sha 對得上", pin["state"] == "PINNED", pin.get("version") or pin["why"])
    sample = (VIA / "functional modules" / "VRN" / "references" / "intake" / "PDFRegressionEvidence_v1.0.0_b245"
              / "PDFRegressionEvidence_v1.0.0" / "synthetic_financial_report.pdf")
    if pin["state"] == "PINNED" and sample.is_file():
        got = pdf_text(sample)
        txt = got.get("text") or ""
        chk("⑤ PDF → PRADDLE → LAYOUT 修復段落:數位頁走 native · 有標題與正文 · 頁眉雜訊已剔除",
            got["state"] == "PASS" and all(r == "native" for r in got["routes"]) and "Annual Research Report" in txt
            and "body paragraph" in txt and "Generic Layout Engine Test" not in txt,
            f"{got['state']} · 段 {got.get('paragraphs')} · 頁 {got.get('routes')} · {got.get('sec')}s")
        res = run_pdf_text(sample, 3, True)
        chk("⑥ 段落交給 v0103 run_text:判決 PASS · 帶 PRADDLE 來源欄", res.get("state") == "PASS" and "praddle" in res,
            f"{res.get('state')} · {sorted(res)[:6]}")
    else:
        chk("⑤ 合成樣本或鎖冊缺 → 照實跳過(不冒充)", True, "SKIP")
        chk("⑥ 同上 → 跳過", True, "SKIP")
    src = Path(__file__).read_text(encoding="utf-8")
    loaded = {m.split(".")[0] for m in sys.modules}
    chk("⑦ 本行程沒載任何 OCR 套件 · 加速器橋在 · 不碰 TA-Lib",
        not (set(OCR_PKGS) & loaded) and "[VIA:ACCEL-BRIDGE" in src and not re.search(r"^\s*(import|from)\s+talib", src, re.M))
    print(f"  [計] SUP_MDL866 v0106 {sum(ok)}/{len(ok)} · {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
