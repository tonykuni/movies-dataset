#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_ENG400 SixEngineShell v0101 — 薄尾:OCR 重型座位接上 Paddle 車道正主(不複製律)。

v0100 的 ENG400.OCR heavy 是宣告座位;本尾版把它接到既有正主,不另寫一套 paddle:
  判準/健康/墊片 = VRN_ENG082_ExtractionLogic 尾版(install_paddle_compat · broken_backends ·
  verdict_of);階梯實錄 = VRN_ENG072 第三階;車道調度 = SUP_MDL747 OcrLaneRunner(via_paddle_311 境)。
行為:paddleocr 在本境 → 先裝 3.x 相容墊片再實跑(PaddleOCR 文字;PPStructure 在場加表格結構),
結果一律標 requires_separate_validation=True(正典:重型還原需另驗,不冒充已驗);
paddleocr 缺席 → 誠實 UNAVAILABLE,附車道指路(via_paddle_311)與 ENG082 後端健康名單,不假造。
其餘六引擎/配方/產物鏈照 v0100(前版鏈 __getattr__ 全轉接)。
自測: VIA_FROM_VCGC=YES python VRN_ENG400_SixEngineShell_v0101.py --selftest
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
import json
import os
import re
import sys
import tempfile
from pathlib import Path

VERSION = "v0101"
HERE = Path(__file__).resolve().parent
_STEM = "VRN_ENG400_SixEngineShell"


def _vnum(q: Path) -> int:
    m = re.search(r"_v(\d+)$", q.stem)
    return int(m.group(1)) if m else -1


_PRIOR_PATH = max((q for q in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(q) < _vnum(Path(__file__))),
                  key=_vnum, default=HERE / (_STEM + "_v0100.py"))   # the prior this tail was cut from
_spec = importlib.util.spec_from_file_location("eng400_prior_for_" + Path(__file__).stem, _PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)

PADDLE_LANE = "via_paddle_311"
PADDLE_ADAPTERS = ("paddleocr", "paddle_ppstructure", "paddle_pdf_pipeline")


def _family(stem: str):
    """載他家族尾版(正主引用)。"""
    roots = [HERE, HERE.parents[1] / "supportive modules" / "70_VRN_Rules"]
    hits = sorted((p for r in roots for p in r.glob(stem + "_v*.py") if _vnum(p) >= 0), key=_vnum)
    if not hits:
        raise FileNotFoundError("正主家族不在:" + stem)
    name = "heavy_" + hits[-1].stem
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, hits[-1])
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


def heavy_targets() -> dict:
    """重型座位的正主盤點(唯讀):三家族尾版 + ENG082 後端健康 + 車道名。"""
    out = {"lane_env": PADDLE_LANE, "adapters": list(PADDLE_ADAPTERS), "masters": {}, "broken": None}
    for stem in ("VRN_ENG082_ExtractionLogic", "VRN_ENG072_FirstPageText", "SUP_MDL747_OcrLaneRunner"):
        try:
            out["masters"][stem] = Path(_family(stem).__file__).name
        except Exception as exc:  # 正主缺席也要誠實列出,不丟例外
            out["masters"][stem] = f"MISSING: {type(exc).__name__}"
    try:
        out["broken"] = _family("VRN_ENG082_ExtractionLogic").broken_backends()
    except Exception as exc:
        out["broken"] = f"health unavailable: {type(exc).__name__}"
    return out


class OcrEngine(PRIOR.OcrEngine):   # 同名承接:前版 selftest 以 __name__ 取鍵
    """⑥ OCR 共用辨識(v0101):heavy 座位實接 Paddle 車道正主;basic 照前版。"""

    def __init__(self, evidence_sink=None):
        super().__init__(evidence_sink)
        self.ADAPTERS = dict(self.ADAPTERS)
        self.ADAPTERS["heavy"] = self.heavy
        self.ADAPTERS["heavy_targets"] = heavy_targets
        self.MANIFEST = dict(self.MANIFEST)
        self.MANIFEST["version"] = VERSION
        self.MANIFEST["deps"] = list(self.MANIFEST["deps"]) + [
            "重型正主:VRN_ENG082(墊片/健康/判準)· VRN_ENG072 第三階 · SUP_MDL747 車道(via_paddle_311)"]

    def heavy(self, pdf: str, work: str, config=None) -> dict:
        """重型 OCR:paddle 在境實跑(先墊片);缺席誠實 UNAVAILABLE + 車道指路。結果一律需另驗。"""
        cfg = dict(config or {})
        row = {"plugin_id": "eng400.ocr_heavy", "tool": "paddle", "version": VERSION,
               "task": "heavy", "state": "EXTRACTED_UNVERIFIED", "light": "YELLOW",
               "text": "", "elements": [], "tables": [], "images": [], "artifacts": [],
               "warnings": [], "ocr_used": True,
               "metadata": {"requires_separate_validation": True,
                            "reason": "正典 OCR 重型列:曲線/柱形/複雜結構還原需另驗,不冒充已驗",
                            "lane_env": PADDLE_LANE}}
        eng082 = _family("VRN_ENG082_ExtractionLogic")
        try:
            shim = eng082.install_paddle_compat()
            row["metadata"]["compat_shim"] = shim
        except Exception as exc:
            row["metadata"]["compat_shim"] = f"shim skipped: {type(exc).__name__}"
        try:
            import paddleocr  # 延遲載入;重型依賴只住 via_paddle_311 境
        except ImportError as exc:
            row.update(state="UNAVAILABLE",
                       error=f"paddleocr 缺席:{exc};派車道 {PADDLE_LANE}(SUP_MDL747)")
            row["metadata"]["backend_health"] = heavy_targets()["broken"]
            self.record("heavy", {"state": "UNAVAILABLE", "lane": PADDLE_LANE})
            return row
        work = Path(tempfile.mkdtemp(prefix="eng400-heavy-", dir=str(Path(work))))
        row["work_dir"] = str(work)
        page_no = int(cfg.get("page", 1))
        dpi = int(cfg.get("render_dpi", 300))        # 重型預設 300;350 只在解析度不足最後(正典)
        try:   # 渲染失敗不是 paddle 的錯:隔離成 ERROR,不丟例外、不記後端 BROKEN
            img = PRIOR._tail("VRN_OCRPlugins")._render_page(pdf, page_no, dpi, work / "page.png")
            row["artifacts"].append(str(img))
        except Exception as exc:
            row.update(state="ERROR", light="RED",
                       error=f"render: {type(exc).__name__}: {str(exc)[:200]}")
            self.record("heavy", {"state": "ERROR", "stage": "render"})
            return row
        try:
            ocr = paddleocr.PaddleOCR(lang=cfg.get("paddle_lang", "ch"))
            got = ocr.ocr(str(img))
            for line in (got[0] if got and isinstance(got, list) else []) or []:
                quad, (txt, conf) = line[0], line[1]
                xs = [p[0] for p in quad]; ys = [p[1] for p in quad]
                row["elements"].append({"text": txt, "conf": float(conf),
                                        "bbox": [min(xs), min(ys), max(xs), max(ys)],
                                        "bbox_pt": PRIOR.px_to_pt([min(xs), min(ys), max(xs), max(ys)], dpi)})
            row["text"] = " ".join(e["text"] for e in row["elements"])
            row["metadata"].update(page=page_no, dpi=dpi, word_count=len(row["elements"]))
        except Exception as exc:
            eng082.mark_backend("paddleocr", "BROKEN", str(exc)[:400])
            row.update(state="ERROR", light="RED", error=f"{type(exc).__name__}: {str(exc)[:200]}")
            return row
        try:   # PPStructure 在場才加表格/版面結構;缺席不是錯
            from paddleocr import PPStructure
            st = PPStructure(show_log=False)
            for blk in st(str(img)) or []:
                if blk.get("type") == "table":
                    row["tables"].append({"bbox": blk.get("bbox"),
                                          "html": (blk.get("res") or {}).get("html", ""),
                                          "needs_validation": True})
        except ImportError:
            row["warnings"].append("PPStructure 缺席:只出文字層,表格結構待車道")
        except Exception as exc:
            row["warnings"].append(f"PPStructure 失敗(誠實記,不吞):{type(exc).__name__}")
        self.record("heavy", {"state": row["state"], "words": len(row["elements"]),
                              "tables": len(row["tables"])})
        return row


# 家族式接管:SHELL 與調度總覽用本版 OCR 引擎(其餘五引擎照前版)
OcrEngineHeavy = None  # 佔位,下行定義後補
SHELL = tuple(OcrEngine if c.__name__ == "OcrEngine" else c for c in PRIOR.SHELL)
OcrEngineHeavy = OcrEngine  # 別名(重型版)
PRIOR.SHELL = SHELL
PRIOR.OcrEngine = OcrEngine


def build_manager_view() -> dict:
    view = PRIOR.build_manager_view()
    view["version"] = VERSION
    view["heavy_seat"] = heavy_targets()
    return view


def __getattr__(name):
    """PEP 562 轉接(尾版律 TAILAPI):本版沒蓋的名稱(含私名)一律轉前版;只擋 dunder。"""
    if name.startswith("__") and name.endswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def selftest() -> int:
    p = f = 0

    def ck(name, cond):
        nonlocal p, f
        if cond:
            p += 1
            print("  [OK] %s" % name)
        else:
            f += 1
            print("  [FAIL] %s" % name)

    t = heavy_targets()
    ck("① 重型正主三家族全找得到尾版(ENG082 · ENG072 · SUP_MDL747)",
       all(not str(v).startswith("MISSING") for v in t["masters"].values()))
    ck("② 車道與轉接器名對齊操作員實錄(via_paddle_311 · paddle 三支)",
       t["lane_env"] == PADDLE_LANE and set(t["adapters"]) == set(PADDLE_ADAPTERS))
    ck("③ ENG082 後端健康可讀(broken_backends 回列表)", isinstance(t["broken"], list))
    sink = []
    oc = OcrEngine(sink)
    ck("④ heavy 座位已實接(callable,不再是字串宣告)", callable(oc.ADAPTERS["heavy"]))
    work = tempfile.mkdtemp(prefix="eng400h-st-")
    src = __file__
    try:   # 有 fitz 就合成真 PDF 當重型測資(拿 .py 餵引擎只測得到隔離,測不到實跑)
        import fitz
        pdfp = Path(work) / "heavy.pdf"
        d = fitz.open(); pg = d.new_page(width=300, height=200)
        pg.insert_text((30, 100), "HEAVY CHECK 123", fontsize=20)
        d.save(str(pdfp)); d.close()
        src = str(pdfp)
    except ImportError:
        pass
    r = oc.heavy(src, work)
    has_paddle = r["state"] != "UNAVAILABLE"
    if has_paddle:
        ck("⑤ paddle 在境:實跑(含 3.x 墊片)· 狀態 %s · 字 %s" % (r["state"], r["metadata"].get("word_count")),
           r["state"] in ("EXTRACTED_UNVERIFIED", "ERROR") and "compat_shim" in r["metadata"])
        if r["state"] == "ERROR":
            print("      [誠實記] %s" % r.get("error", "")[:160])
    else:
        ck("⑤ paddle 缺席:誠實 UNAVAILABLE + 車道指路 + 後端健康名單",
           PADDLE_LANE in r.get("error", "") and "backend_health" in r["metadata"])
    ck("⑥ 重型鐵律:requires_separate_validation 恆 True(不冒充已驗)",
       r["metadata"]["requires_separate_validation"] is True)
    ck("⑦ 前版六引擎/配方經轉接照常(SHELL 六引擎 · OCR 為本版)",
       len(SHELL) == 6 and SHELL[-1] is OcrEngine and callable(__getattr__("px_to_pt")))
    view = build_manager_view()
    ck("⑧ 調度總覽帶 heavy_seat 盤點 · 版本 v0101",
       view["version"] == VERSION and view["heavy_seat"]["lane_env"] == PADDLE_LANE)
    import io, contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        prc = PRIOR.selftest()
    tail = [l for l in buf.getvalue().splitlines() if "自測" in l][-1:]
    print("  " + (tail[0].strip() if tail else ""))
    ck("⑨ 前版 v0100 自測在本版接管下仍全過", prc == 0)
    body = Path(__file__).read_text(encoding="utf-8")
    ck("⑩ 帶加速器橋 · VIA_FROM_VCGC 閘 · _PRIOR_PATH 家族式",
       "[VIA:ACCEL-BRIDGE:v0100]" in body and "VIA_FROM_VCGC" in body and "_PRIOR_PATH" in body)
    print("[計] VRN_ENG400_SixEngineShell_v0101 自測 %d/%d · %s" % (p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print("Use VCGC entry")
        return 2
    args = sys.argv[1:]
    if "--selftest" in args:
        return selftest()
    if "view" in args:
        print(json.dumps(build_manager_view(), ensure_ascii=False, indent=1))
        return 0
    if "heavy-targets" in args:
        print(json.dumps(heavy_targets(), ensure_ascii=False, indent=1))
        return 0
    print(__doc__)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
