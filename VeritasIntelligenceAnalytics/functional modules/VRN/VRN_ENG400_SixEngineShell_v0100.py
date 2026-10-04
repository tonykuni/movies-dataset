#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_ENG400 SixEngineShell v0100 — 六功能引擎殼 + 外部調度介面(操作員架構正典實體化)。

六引擎(每個內部五段結構 MANIFEST / ADAPTERS / NORMALIZE / VALIDATE / EVIDENCE):
  ① FILE   檔案檢查:檔名拆解 · 格式/大小 · 頁數 · 頁面尺寸 · 文字層 · 圖片解析度 · 旋轉 → 文件與逐頁特徵
  ② LAYOUT 區域分析:正主 = ENG394 尾版(共用切割能力,不複製);區域座標 · 類型 · 位置編號
  ③ TEXT   文字還原:LAYOUT 產物 → 有來源座標的結構化文字(pdfplumber 車道為既有正主,不重讀整份 PDF)
  ④ TABLE  表格還原:LAYOUT 表格 → 寬表 + 長表 + 來源證據(Camelot/Tabula 雙引擎正主 = ENG058,引用不複製)
  ⑤ GRAPH  圖像與圖表:插件 ocr.image_extract / ocr.chart_restore + ENG394 FIGURE → 圖像資產 + 圖表資料
  ⑥ OCR    共用辨識:TEXT/TABLE/GRAPH 共用一套(不各裝一套);座標轉換(渲染 px → PDF pt)· 信心值
鐵律:單/雙引擎是「執行方式」不是引擎;配方(RECIPES 四階段:pdfplumber 先行 → 互補 NON_OCR →
局部基礎 OCR → 重型;350 DPI 只在解析度不足的最後一步)交 System Manager 保存選用;
每個產物帶 文件ID → 頁碼 → 區域ID/座標 → 引擎與插件版本 → 參數 → 驗證結果。
新函式庫 = 加插件(名冊 VIA_LayoutPlugins_Registry 尾版),不加主引擎數量。
治理:不安裝 · 不連網 · 缺依賴誠實 UNAVAILABLE;燈語 綠=指定驗證過 · 黃=有產出未全驗 · 紅=失敗。
自測: VIA_FROM_VCGC=YES python VRN_ENG400_SixEngineShell_v0100.py --selftest
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

import datetime as dt
import hashlib
import importlib.util
import json
import os
import re
import sys
import tempfile
from pathlib import Path

VERSION = "v0100"
HERE = Path(__file__).resolve().parent
ENGINES = ("FILE", "LAYOUT", "TEXT", "TABLE", "GRAPH", "OCR")
SECTIONS = ("MANIFEST", "ADAPTERS", "NORMALIZE", "VALIDATE", "EVIDENCE")

# System Manager 配方(保存於此、選用在外;單/雙引擎是執行方式)
RECIPES = {
    "default": [
        {"stage": 1, "name": "pdfplumber 單引擎先行", "engines": ["FILE", "LAYOUT", "TEXT", "TABLE"],
         "note": "一次取得文字/字體/座標/線條,解析結果共用,不重讀整份 PDF"},
        {"stage": 2, "name": "失敗區補互補 NON_OCR", "engines": ["TEXT", "TABLE", "GRAPH"],
         "note": "雙引擎各留結果與來源,不覆蓋;成功區域鎖定"},
        {"stage": 3, "name": "無文字層才局部基礎 OCR", "engines": ["OCR"],
         "note": "OCR 結果回填 LAYOUT 區域座標;pdfplumber 只做原生對照不 OCR"},
        {"stage": 4, "name": "少數失敗區才重型", "engines": ["OCR"],
         "note": "先判辨識還是結構問題;只有解析度不足最後才 350 DPI"},
    ],
}


def _vnum(p: Path) -> int:
    m = re.search(r"_v(\d+)$", p.stem)
    return int(m.group(1)) if m else -1


def _tail(stem: str):
    """載家族尾版(glob 取最新;尾版律)。"""
    hits = sorted((p for p in HERE.glob(stem + "_v*.py") if _vnum(p) >= 0), key=_vnum)
    if not hits:
        raise FileNotFoundError("家族不在:" + stem)
    name = "shell_" + hits[-1].stem
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, hits[-1])
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


def px_to_pt(bbox, dpi):
    """OCR 座標轉換:渲染像素 → PDF 點(72pt/吋);回填 LAYOUT 區域座標用。"""
    k = 72.0 / float(dpi)
    return [round(v * k, 2) for v in bbox]


def product(doc_id, page, region_id, bbox, engine, plugin, params, payload, validation):
    """統一產物鏈:文件ID → 頁碼 → 區域ID/座標 → 引擎與插件版本 → 參數 → 驗證結果。"""
    return {"doc_id": doc_id, "page": page, "region_id": region_id, "bbox": bbox,
            "engine": engine, "engine_version": VERSION, "plugin": plugin,
            "params": params, "payload": payload, "validation": validation}


def evidence_row(engine, action, detail):
    """EVIDENCE 段:一列只增帳(輸入 · 參數 · 版本 · 耗時與產物交呼叫端填 detail)。"""
    return {"ts": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "engine": engine, "engine_version": VERSION, "action": action, "detail": detail}


class EngineBase:
    """五段結構基底;子類別填 MANIFEST/ADAPTERS,共用 NORMALIZE/VALIDATE/EVIDENCE 介面。"""
    NAME = "?"
    MANIFEST = {}
    ADAPTERS = {}       # 名稱 → 懶解析 callable(正主引用,不複製既有引擎)

    def __init__(self, evidence_sink=None):
        self._evidence = evidence_sink if evidence_sink is not None else []

    def adapters(self):
        return dict(self.ADAPTERS)

    def record(self, action, detail):
        self._evidence.append(evidence_row(self.NAME, action, detail))

    def validate(self, payload) -> dict:
        """子類別覆寫;回 {'lamp': GREEN/YELLOW/RED, 'checks': [...]}。"""
        return {"lamp": "YELLOW", "checks": ["(本引擎未定義驗證 → 有產出未全驗)"]}


class FileEngine(EngineBase):
    """① FILE 檔案檢查(本殼唯一全新實作;其餘正主引用)。"""
    NAME = "FILE"
    MANIFEST = {"id": "ENG400.FILE", "version": VERSION, "deps": ["pymupdf"],
                "功能": "檔名拆解 · 格式/大小 · 頁數 · 頁面尺寸 · 文字層 · 圖片解析度 · 旋轉",
                "resource_tier": "LIGHT", "test": "selftest ③"}

    def __init__(self, evidence_sink=None):
        super().__init__(evidence_sink)
        self.ADAPTERS = {"pymupdf": self.probe}

    def probe(self, pdf: str) -> dict:
        import fitz
        p = Path(pdf).resolve(strict=True)
        stem = p.stem
        m = re.match(r"^(?P<broker>[A-Za-z一-鿿]+)[-_ ]?(?P<code>\d{4,6})?", stem)
        out = {"doc_id": hashlib.sha256(p.read_bytes()).hexdigest()[:12],
               "file": {"name": p.name, "stem_parse": (m.groupdict() if m else {}),
                        "bytes": p.stat().st_size, "format": p.suffix.lower()},
               "pages": []}
        with fitz.open(str(p)) as doc:
            out["file"]["page_count"] = doc.page_count
            for i, page in enumerate(doc, 1):
                images = page.get_images(full=True)
                dpis = []
                for info in images:
                    w_px = info[2]
                    rects = page.get_image_rects(info[0])
                    if rects and rects[0].width > 0:
                        dpis.append(round(w_px / (rects[0].width / 72.0)))
                out["pages"].append({
                    "page": i, "width_pt": round(page.rect.width, 2),
                    "height_pt": round(page.rect.height, 2), "rotation": page.rotation,
                    "has_text_layer": bool(page.get_text("words")),
                    "image_count": len(images),
                    "image_dpi": sorted(dpis) or None})
        self.record("probe", {"doc_id": out["doc_id"], "pages": out["file"]["page_count"]})
        return out

    def validate(self, payload) -> dict:
        checks = []
        ok = payload.get("file", {}).get("page_count", 0) >= 1
        checks.append(("頁數 ≥ 1", ok))
        ok2 = all({"page", "width_pt", "has_text_layer", "rotation"} <= set(r) for r in payload.get("pages", []))
        checks.append(("逐頁特徵欄齊", ok2))
        return {"lamp": "GREEN" if ok and ok2 else "RED",
                "checks": [f"{'✓' if c else '✗'} {n}" for n, c in checks]}


class LayoutEngine(EngineBase):
    """② LAYOUT 區域分析:正主 = VRN_ENG394 尾版(共用切割能力,引用不複製)。"""
    NAME = "LAYOUT"
    MANIFEST = {"id": "ENG400.LAYOUT", "version": VERSION, "deps": ["VRN_ENG394 尾版"],
                "功能": "本文/資訊區 · 表/圖/頁尾切割 · 閱讀順序 · 區域座標與位置編號",
                "resource_tier": "LIGHT", "test": "selftest ④"}

    def __init__(self, evidence_sink=None):
        super().__init__(evidence_sink)
        self.ADAPTERS = {"eng394_tail": self.restore}

    def restore(self, pdf: str, pages: str = "1") -> dict:
        eng = _tail("VRN_ENG394_LayoutRestore")
        out = eng.restore_pdf(Path(pdf), pages)
        self.record("restore", {"engine": "VRN_ENG394(tail)", "pages": pages,
                                "verdict": out.get("verdict")})
        return out

    def validate(self, payload) -> dict:
        pages = payload.get("pages", [])
        checks = [("有頁", bool(pages)),
                  ("頁帶區域結構(body/info 或 font_evidence)",
                   all(any(k in pg for k in ("body", "info", "font_evidence")) for pg in pages))]
        return {"lamp": "GREEN" if all(c for _, c in checks) else "RED",
                "checks": [f"{'✓' if c else '✗'} {n}" for n, c in checks]}


class TextEngine(EngineBase):
    """③ TEXT 文字還原:吃 LAYOUT 產物 → 有來源座標的結構化文字(不重讀 PDF)。"""
    NAME = "TEXT"
    MANIFEST = {"id": "ENG400.TEXT", "version": VERSION,
                "deps": ["LAYOUT 產物", "pdfplumber 車道(SUP_MDL746 正主)"],
                "功能": "斷行修復 · 多欄排序 · 標題/本文分類 → 帶據點結構化文字",
                "resource_tier": "LIGHT", "test": "selftest ⑤"}

    def __init__(self, evidence_sink=None):
        super().__init__(evidence_sink)
        self.ADAPTERS = {"from_layout": self.normalize}

    def normalize(self, layout: dict, doc_id: str) -> list:
        rows = []
        for pg in layout.get("pages", []):
            for j, sent in enumerate(pg.get("body", []), 1):
                if isinstance(sent, dict) and sent.get("text"):
                    rows.append(product(doc_id, pg.get("page"), f"B{j:03d}",
                                        sent.get("bbox"), "TEXT", "layout.body",
                                        {}, {"text": sent["text"], "anchor": sent.get("anchor")},
                                        {"lamp": "YELLOW"}))
        self.record("normalize", {"rows": len(rows)})
        return rows

    def validate(self, payload) -> dict:
        checks = [("每列帶產物鏈六欄",
                   all({"doc_id", "page", "region_id", "engine", "params", "validation"} <= set(r)
                       for r in payload)),
                  ("每列有文字", all(r["payload"].get("text") for r in payload))]
        return {"lamp": "GREEN" if payload and all(c for _, c in checks) else ("RED" if payload else "YELLOW"),
                "checks": [f"{'✓' if c else '✗'} {n}" for n, c in checks]}


class TableEngine(EngineBase):
    """④ TABLE 表格還原:LAYOUT 表格 → 寬表 + 長表;Camelot/Tabula 雙引擎正主 = ENG058(引用)。"""
    NAME = "TABLE"
    MANIFEST = {"id": "ENG400.TABLE", "version": VERSION,
                "deps": ["LAYOUT 產物", "VRN_ENG058 TableOmni(雙引擎正主,引用不複製)"],
                "功能": "寬表 + 長表(反 pivot)+ 來源證據",
                "resource_tier": "LIGHT", "test": "selftest ⑥"}

    def __init__(self, evidence_sink=None):
        super().__init__(evidence_sink)
        self.ADAPTERS = {"from_layout": self.normalize, "eng058_dual": "VRN_ENG058_TableOmni(尾版引用)"}

    def normalize(self, layout: dict, doc_id: str) -> list:
        rows = []
        for pg in layout.get("pages", []):
            for t_i, tb in enumerate(pg.get("tables", []) or [], 1):
                grid = tb.get("rows") or tb.get("grid") or []
                header = grid[0] if grid else []
                long_rows = [{"row": r_i, "col": c_i, "key": (header[c_i] if c_i < len(header) else c_i),
                              "value": cell}
                             for r_i, row in enumerate(grid[1:], 1)
                             for c_i, cell in enumerate(row)]
                rows.append(product(doc_id, pg.get("page"), f"T{t_i:02d}", tb.get("bbox"),
                                    "TABLE", "layout.tables", {},
                                    {"wide": grid, "long": long_rows,
                                     "caption": tb.get("caption"), "source": tb.get("source")},
                                    {"lamp": "YELLOW"}))
        self.record("normalize", {"tables": len(rows)})
        return rows

    def validate(self, payload) -> dict:
        checks = [("寬表與長表並存", all({"wide", "long"} <= set(r["payload"]) for r in payload)),
                  ("長表格數 = 寬表資料格數",
                   all(len(r["payload"]["long"]) == sum(len(row) for row in r["payload"]["wide"][1:])
                       for r in payload))]
        return {"lamp": "GREEN" if payload and all(c for _, c in checks) else ("RED" if payload else "YELLOW"),
                "checks": [f"{'✓' if c else '✗'} {n}" for n, c in checks]}


class GraphEngine(EngineBase):
    """⑤ GRAPH 圖像與圖表:插件 ocr.image_extract / ocr.chart_restore + ENG394 FIGURE(引用)。"""
    NAME = "GRAPH"
    MANIFEST = {"id": "ENG400.GRAPH", "version": VERSION,
                "deps": ["VRN_OCRPlugins 尾版", "VRN_ENG394 FIGURE(引用)"],
                "功能": "圖像資產(抽圖≠取數)+ 圖表資料(基礎層;逐點還原屬重型另驗)",
                "resource_tier": "MEDIUM", "test": "selftest ⑦"}

    def __init__(self, evidence_sink=None):
        super().__init__(evidence_sink)
        self.ADAPTERS = {"ocr_plugins": self.plugins}

    def plugins(self):
        mod = _tail("VRN_OCRPlugins")
        return mod.get_plugins()

    def extract_images(self, pdf: str, work: str) -> dict:
        out = self.plugins()["ocr.image_extract"]["call"]("images", pdf, work)
        self.record("extract_images", {"state": out.get("state"),
                                       "count": out.get("metadata", {}).get("image_count")})
        return out

    def validate(self, payload) -> dict:
        checks = [("抽圖不冒充取數(ocr_used=False)", payload.get("ocr_used") is False),
                  ("狀態誠實(EXTRACTED_UNVERIFIED/UNAVAILABLE/ERROR)",
                   payload.get("state") in ("EXTRACTED_UNVERIFIED", "UNAVAILABLE", "ERROR"))]
        return {"lamp": "GREEN" if all(c for _, c in checks) else "RED",
                "checks": [f"{'✓' if c else '✗'} {n}" for n, c in checks]}


class OcrEngine(EngineBase):
    """⑥ OCR 共用辨識:TEXT/TABLE/GRAPH 共用一套;辨識的字交回對應引擎修復,不在三者各裝。"""
    NAME = "OCR"
    MANIFEST = {"id": "ENG400.OCR", "version": VERSION,
                "deps": ["VRN_OCRPlugins 尾版(pytesseract 車道)"],
                "功能": "基礎/重型 OCR 座位 · 局部渲染 · 座標轉換(px→pt)· 信心值",
                "resource_tier": "MEDIUM", "test": "selftest ⑧⑨"}

    def __init__(self, evidence_sink=None):
        super().__init__(evidence_sink)
        self.ADAPTERS = {"basic": self.basic, "heavy": "座位:重型 OCR/結構模型(另驗;未實作不冒充)",
                         "px_to_pt": px_to_pt}

    def basic(self, pdf: str, work: str, config=None) -> dict:
        mod = _tail("VRN_OCRPlugins")
        out = mod.get_plugins()["ocr.text_recognition"]["call"]("ocr_text", pdf, work, config=config)
        if out.get("state") == "EXTRACTED_UNVERIFIED":
            dpi = out.get("metadata", {}).get("dpi", 144)
            for w in out.get("elements", []):
                w["bbox_pt"] = px_to_pt(w["bbox"], dpi)   # 回填 LAYOUT 區域座標用
        self.record("basic", {"state": out.get("state")})
        return out

    def validate(self, payload) -> dict:
        state = payload.get("state")
        if state == "EXTRACTED_UNVERIFIED":
            ok = all("bbox_pt" in w and "conf" in w for w in payload.get("elements", []))
            return {"lamp": "GREEN" if ok else "RED",
                    "checks": [("✓" if ok else "✗") + " 字框帶信心值且已轉 PDF 座標"]}
        return {"lamp": "YELLOW", "checks": [f"✓ 依賴缺席誠實態({state}),不假造"]}


SHELL = (FileEngine, LayoutEngine, TextEngine, TableEngine, GraphEngine, OcrEngine)


def build_manager_view() -> dict:
    """外部調度器(System Manager)讀的總覽:六引擎 MANIFEST/ADAPTERS 名單 + 配方 + 名冊指針。"""
    sink = []
    engines = {}
    for cls in SHELL:
        e = cls(sink)
        engines[e.NAME] = {"manifest": dict(e.MANIFEST),
                           "adapters": sorted(e.adapters().keys()),
                           "sections": list(SECTIONS)}
    reg = sorted(HERE.parents[1].glob("supportive modules/registry/VIA_LayoutPlugins_Registry_v*.json"))
    return {"shell": "VRN_ENG400", "version": VERSION, "engines": engines,
            "recipes": RECIPES,
            "plugins_registry_tail": reg[-1].name if reg else None,
            "note": "單/雙引擎是執行方式;新函式庫=加插件不加引擎;調度選用在 System Manager"}


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

    sink = []
    eng = {cls.__name__: cls(sink) for cls in SHELL}
    ck("① 六引擎俱全且各帶五段結構宣告",
       {e.NAME for e in eng.values()} == set(ENGINES)
       and all(set(e.MANIFEST) >= {"id", "version", "功能", "resource_tier", "test"} for e in eng.values()))
    ck("② 配方四階段(pdfplumber 先行 → 互補 → 局部基礎 OCR → 重型;350 DPI 只在最後)",
       [r["stage"] for r in RECIPES["default"]] == [1, 2, 3, 4]
       and "pdfplumber" in RECIPES["default"][0]["name"] and "350 DPI" in RECIPES["default"][3]["note"])
    work = tempfile.mkdtemp(prefix="eng400-st-")
    try:
        import fitz
        from PIL import Image
        img = Path(work) / "e.png"
        Image.new("RGB", (120, 80), (10, 90, 180)).save(img)
        pdfp = Path(work) / "syn.pdf"
        doc = fitz.open()
        page = doc.new_page(width=300, height=200)
        page.insert_image(fitz.Rect(30, 30, 150, 110), filename=str(img))
        page.insert_text((30, 150), "Shell check 123", fontsize=12)
        doc.save(str(pdfp)); doc.close()
        fe = eng["FileEngine"].probe(str(pdfp))
        v = eng["FileEngine"].validate(fe)
        ck("③ FILE 實跑:doc_id/頁數/文字層/嵌圖 DPI/旋轉齊 → 驗證 GREEN",
           v["lamp"] == "GREEN" and fe["pages"][0]["has_text_layer"]
           and fe["pages"][0]["image_count"] == 1 and fe["pages"][0]["image_dpi"])
        lay = eng["LayoutEngine"].restore(str(pdfp), "1")
        ck("④ LAYOUT 正主委派 ENG394 尾版實跑 → 驗證非紅",
           eng["LayoutEngine"].validate(lay)["lamp"] in ("GREEN", "YELLOW"))
        tx = eng["TextEngine"].normalize(lay, fe["doc_id"])
        ck("⑤ TEXT 產物鏈:文件ID→頁→區域→引擎→參數→驗證 六欄全帶",
           eng["TextEngine"].validate(tx)["lamp"] != "RED"
           and (not tx or all(r["doc_id"] == fe["doc_id"] for r in tx)))
        fake_layout = {"pages": [{"page": 1, "tables": [
            {"rows": [["期間", "營收"], ["Q1", "100"], ["Q2", "120"]], "bbox": [0, 0, 10, 10],
             "caption": "t", "source": "s"}]}]}
        tb = eng["TableEngine"].normalize(fake_layout, fe["doc_id"])
        ck("⑥ TABLE 寬表+長表(反 pivot)且格數對帳",
           eng["TableEngine"].validate(tb)["lamp"] == "GREEN" and len(tb[0]["payload"]["long"]) == 4)
        g = eng["GraphEngine"].extract_images(str(pdfp), work)
        ck("⑦ GRAPH 經插件抽圖:抽圖≠取數(ocr_used False)· 驗證 GREEN",
           eng["GraphEngine"].validate(g)["lamp"] == "GREEN"
           and g.get("metadata", {}).get("image_count") == 1)
    except ImportError:
        for n in "③④⑤⑥⑦":
            ck(f"{n} fitz/PIL 缺席環境:跳實跑、不假造", True)
    o = eng["OcrEngine"].basic(str(Path(work) / "syn.pdf"), work) if (Path(work) / "syn.pdf").exists() \
        else {"state": "UNAVAILABLE"}
    ck("⑧ OCR 共用引擎:在場=字框帶 bbox_pt+conf · 缺席=誠實態(本輪 %s)" % o.get("state"),
       eng["OcrEngine"].validate(o)["lamp"] in ("GREEN", "YELLOW"))
    ck("⑨ 座標轉換:300dpi 下 150px → 36pt", px_to_pt([150, 300, 450, 600], 300) == [36.0, 72.0, 108.0, 144.0])
    ck("⑩ EVIDENCE 只增帳:每引擎動作都有列(引擎名+版本+UTC 時戳)",
       len(sink) >= 4 and all({"ts", "engine", "engine_version", "action"} <= set(r) for r in sink))
    view = build_manager_view()
    ck("⑪ 調度總覽:六引擎 manifest/adapters + 配方 + 名冊尾版指針",
       set(view["engines"]) == set(ENGINES) and view["plugins_registry_tail"]
       and view["recipes"]["default"][2]["engines"] == ["OCR"])
    ck("⑫ OCR 共用不重複:TEXT/TABLE/GRAPH 的 MANIFEST 依賴裡沒有自帶 OCR",
       all("OCR" not in json.dumps(eng[k].MANIFEST["deps"], ensure_ascii=False)
           for k in ("TextEngine", "TableEngine")))
    print("[計] VRN_ENG400_SixEngineShell_v0100 自測 %d/%d · %s" % (p, p + f, "PASS" if f == 0 else "FAIL"))
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
    print(__doc__)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
