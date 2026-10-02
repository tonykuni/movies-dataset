#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Layout tail v0110: LAYOUT 導入 PRADDLE 工具(從工具鎖冊取,經 VCGC 才跑)。

操作員 2026-10-02(VCGC-REQ127):「將 LAYOUT NPL 都有導入工具」。
PRADDLE(VRN_ENG398;RapidOCR → PaddleOCR 雙引擎,各在隔離境子行程)由 CGC_MDL233 v0106 啟用進鎖冊 `praddle`。
本版只加三件,其餘(修復鏈 STAGES · def_repair_document · def_run_batch · 換行鎖 · pdfminer 降噪)照 v0109:
  · praddle_pinned():只認鎖冊那一支(檔在 · sha256 對得上,CRLF 正規化也算);沒啟用 / 檔不在 / 被改過 照實回因由,
    不 glob 猜尾版、不退舊版。
  · def_praddle_lanes():兩車道在各自隔離境的狀態(READY / NO_ENV …);本行程不 import 任何 OCR 套件。
  · def_run_praddle(pdf, output_root, ocr, pages):掃描頁 / 編碼壞頁走 PRADDLE 階梯(原生 → RapidOCR → 不足才 PaddleOCR),
    OCR 行回到本 LAYOUT 修復鏈(ENG398 呼叫 STAGES / def_repair_document)。只收 VCGC 呼叫。
def_run_batch 不改道(避免 LAYOUT → PRADDLE → LAYOUT 迴圈);要 OCR 的件由呼叫端明講 def_run_praddle。零網路。
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
import hashlib
import importlib.util
import json
import os
import re
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
PRIOR = HERE / "SUP_MDL743_GenericLayoutHub_v0109.py"
VIA = HERE.parents[1]
REPO = VIA.parent
REGISTRY = VIA / "supportive modules" / "registry"
OCR_PKGS = ("paddle", "paddleocr", "rapidocr_onnxruntime", "onnxruntime", "cv2")
_TOOLS_V0110: dict = {}


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def __getattr__(name: str):
    return getattr(_load(PRIOR, "layout_v0109_for_v0110"), name)


def _lock_v0110(registry: Path | None = None) -> dict:
    hits = sorted((registry or REGISTRY).glob("VIA_ToolVersion_Lock_v*.json"))
    if not hits:
        return {}
    try:
        return json.loads(hits[-1].read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def praddle_pinned(lock: dict | None = None, repo: Path | None = None) -> dict:
    """鎖冊 `praddle` 那一支:{state: PINNED | NOT_ACTIVATED | PINNED_FILE_MISSING | SHA_DRIFT, path, version, why}。"""
    ent = (lock if lock is not None else _lock_v0110()).get("praddle") or {}
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


def praddle_tool():
    """載入鎖冊那一支 PRADDLE(同一行程只載一次);不是 PINNED 就回 None。"""
    pin = praddle_pinned()
    if pin["state"] != "PINNED":
        return None
    key = pin["path"]
    if key not in _TOOLS_V0110:
        _TOOLS_V0110[key] = _load(Path(key), "praddle_pinned_for_layout_v0110")
    return _TOOLS_V0110[key]


def def_praddle_lanes() -> dict:
    pin = praddle_pinned()
    mod = praddle_tool()
    if mod is None:
        return {"pin": pin, "lanes": {}}
    got = mod.lanes()
    return {"pin": pin, "lanes": {k: v.get("state") for k, v in got.items() if not k.startswith("_")},
            "why": got.get("_why", "")}


def def_run_praddle(pdf, output_root=None, ocr: str = "auto", pages: str | None = None) -> dict:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        raise RuntimeError("DENY")
    mod = praddle_tool()
    if mod is None:
        pin = praddle_pinned()
        return {"state": pin["state"], "why": pin["why"]}
    kw = {"ocr": ocr, "pages": pages}
    if output_root is not None:
        kw["out_root"] = Path(output_root)
    return mod.run_pdf(Path(pdf), **kw)


def def_run_batch(source, output_root, evidence=None):
    return _load(PRIOR, "layout_run_v0109_for_v0110").def_run_batch(source, output_root, evidence)


def main() -> int:
    return _load(PRIOR, "layout_main_v0109_for_v0110").main()


def selftest() -> int:
    print("=== SUP_MDL743 GenericLayoutHub v0110 · LAYOUT 導入 PRADDLE(鎖冊)===")
    rc = _load(PRIOR, "layout_selftest_v0109_for_v0110").selftest()   # v0109 先跑(它會把閘設回 YES)
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    chk("① 前版 v0109 自測過(DENY 閘 · pdfminer 降噪)", rc == 0)
    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp)
        f = t / "VRN_ENG398_PraddleExtractor_v0100.py"
        f.write_text("x = 1\n", encoding="utf-8")
        good = hashlib.sha256(f.read_bytes()).hexdigest()
        rel = f.name
        states = (praddle_pinned({}, t)["state"],
                  praddle_pinned({"praddle": {"path": "nope_v0100.py", "sha256": good}}, t)["state"],
                  praddle_pinned({"praddle": {"path": rel, "sha256": "0" * 64}}, t)["state"],
                  praddle_pinned({"praddle": {"path": rel, "sha256": good, "version": "v0100"}}, t)["state"])
    chk("② 只認鎖冊:沒啟用 / 檔不在 / sha 不對 照實回因由,對得上才 PINNED(不 glob 猜尾版)",
        states == ("NOT_ACTIVATED", "PINNED_FILE_MISSING", "SHA_DRIFT", "PINNED"), states)
    os.environ.pop("VIA_FROM_VCGC", None)
    try:
        def_run_praddle("x.pdf")
        denied = False
    except RuntimeError as exc:
        denied = str(exc) == "DENY"
    os.environ["VIA_FROM_VCGC"] = "YES"
    chk("③ def_run_praddle 只收 VCGC 呼叫(沒有 VIA_FROM_VCGC=YES → DENY)", denied)
    pin = praddle_pinned()
    chk("④ 實鎖冊 praddle 已經 VCGC 啟用且 sha 對得上", pin["state"] == "PINNED", pin.get("version") or pin["why"])
    lanes = def_praddle_lanes()
    chk("⑤ 車道狀態取得到(RapidOCR · PaddleOCR 各在隔離境;容器無境 = NO_ENV 照實)",
        pin["state"] != "PINNED" or {"rapidocr", "paddleocr"} <= set(lanes["lanes"]), lanes["lanes"])
    sample = (VIA / "functional modules" / "VRN" / "references" / "intake" / "PDFRegressionEvidence_v1.0.0_b245"
              / "PDFRegressionEvidence_v1.0.0" / "synthetic_financial_report.pdf")
    if pin["state"] == "PINNED" and sample.is_file():
        with tempfile.TemporaryDirectory() as tmp:
            rep = def_run_praddle(sample, Path(tmp), ocr="auto")
            saved = (Path(rep.get("out", tmp)) / "PRADDLE.json").is_file()
        routes = [p.get("route") for p in rep.get("pages", [])]
        chk("⑥ 經 LAYOUT 跑鎖冊那支 PRADDLE:合成報表數位頁全走 native(不叫 OCR)· 原生行 > 0 · GREEN/YELLOW · 報告落地",
            bool(routes) and all(r == "native" for r in routes) and rep.get("native_lines", 0) > 0
            and rep.get("verdict") in ("GREEN", "YELLOW") and saved,
            f"{rep.get('verdict')} · 頁 {routes} · 原生行 {rep.get('native_lines')} · 表 {len(rep.get('tables') or [])} · {rep.get('sec')}s")
    else:
        chk("⑥ 合成樣本或鎖冊缺 → 照實跳過(不冒充)", True, "SKIP")
    src = Path(__file__).read_text(encoding="utf-8")
    loaded = {m.split(".")[0] for m in sys.modules}
    chk("⑦ 本行程沒載任何 OCR 套件 · 加速器橋在 · 不碰 TA-Lib · def_run_batch 不改道",
        not (set(OCR_PKGS) & loaded) and "[VIA:ACCEL-BRIDGE" in src
        and not re.search(r"^\s*(import|from)\s+talib", src, re.M) and "praddle" not in _batch_src_v0110(src))
    print(f"  [計] SUP_MDL743 v0110 {sum(ok)}/{len(ok)} · {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


def _batch_src_v0110(src: str) -> str:
    m = re.search(r"^def def_run_batch\(.*?(?=^def )", src, re.S | re.M)
    return m.group(0) if m else "praddle"


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
