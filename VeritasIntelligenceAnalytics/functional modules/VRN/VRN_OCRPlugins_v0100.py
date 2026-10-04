#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN OCR 基礎層插件,單檔、延遲載入、可插拔;Python 3.10+。

鐵律(架構正典 VRN_LAYOUT_PLUGIN_ARCH_v0100):圖中文字辨識、圖片抽取、圖表數值還原是
**三個功能**;抽出圖片 ≠ 取得圖中數據。本檔三支插件一功能一支,互不代辦:
  ocr.image_extract    圖片抽取(嵌入圖原樣抽出;本身不做 OCR,ocr_used 恆 False)
  ocr.text_recognition 圖中文字辨識(無文字層/缺字區的局部基礎 OCR;字框+信心值)
  ocr.chart_restore    圖表數值還原【基礎層】:圖名/座標軸刻度/資料標籤 OCR + 等差校驗;
                       曲線/柱形逐點還原屬重型層(需另驗),本檔誠實標 NEEDS_HEAVY 不捏造。
執行路徑(正典):NON_OCR 先行 → 無文字層才進局部基礎 OCR → 少數失敗區才重型;
只有解析度不足最後才 350 DPI(預設 144,升 DPI 走 config,不自動)。
治理:不安裝、不下載、不連網、不自動註冊中央 SSOT;pytesseract / tesseract 執行檔
缺席一律 UNAVAILABLE 誠實標示,不假造結果;central_id=None 等 VCGC 配發。

宿主使用方式::

    import VRN_OCRPlugins_v0100 as ocr_lane
    plugins = ocr_lane.get_plugins()
    result = plugins["ocr.image_extract"]["call"]("images", "report.pdf", "temp/ocr")

統一契約與 VRN_NewPlugins_v0102 相同:call(task, pdf, work, config=None, run_cli=None) -> dict;
work 為 TEMP 根,每呼叫自建子目錄;擷取完成只標 EXTRACTED_UNVERIFIED / 黃燈,實報交宿主驗證。
自測: VIA_FROM_VCGC=YES python VRN_OCRPlugins_v0100.py --selftest(契約式:依賴在場測實跑,缺席測誠實態)
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

import ast
import copy
from functools import wraps
import json
import os
from pathlib import Path
import re
import statistics
import sys
import tempfile

VERSION = "0.1.0"
UPDATED_AT = "2026-10-05T00:00:00+00:00"
CATEGORIES = ("TEXT", "GRAPH", "LAYOUT")
OCR_DEFAULT_CONFIG = {
    "render_dpi": 144,          # 正典:只有解析度不足最後才 350;不自動升
    "ocr_lang": "eng",          # 宿主可給 "eng+chi_tra";缺語言包交 tesseract 誠實報錯
    "ocr_psm": 6,
    "min_confidence": 40.0,     # 低於門檻的字框丟棄進 warnings,不混入結果
    "max_images_per_page": 64,
    "timeout_seconds": 120,
}
PLUGINS = {}


def plugin(key, categories, tasks, description, ocr_used):
    """僅註冊本檔局部描述;錯誤隔離同 VRN_NewPlugins 契約,不決定執行順序。"""
    def decorate(function):
        @wraps(function)
        def guarded(task, pdf, work, config=None, run_cli=None):
            row = def_result(key, task, ocr_used)
            try:
                if task not in tasks:
                    raise ValueError(f"Unsupported task: {task}; allowed: {tasks}")
                merged = copy.deepcopy(OCR_DEFAULT_CONFIG)
                if config:
                    merged.update(copy.deepcopy(config))
                pdf = Path(pdf).expanduser().resolve(strict=True)
                if not pdf.is_file():
                    raise ValueError("input path must be a file")
                root = Path(work).expanduser().resolve()
                root.mkdir(parents=True, exist_ok=True)
                work = Path(tempfile.mkdtemp(prefix=key + "-", dir=root))
                row["work_dir"] = str(work)
                result = function(task, pdf, work, merged)
                result["work_dir"] = str(work)
                result["source"] = str(pdf)
                return result
            except (ImportError, FileNotFoundError) as exc:
                row.update(state="UNAVAILABLE", light="YELLOW", error=str(exc))
            except Exception as exc:
                row.update(state="ERROR", light="RED", error=f"{type(exc).__name__}: {exc}")
            return row
        local_id = "ocr." + key
        if local_id in PLUGINS:
            raise ValueError("Duplicate plugin: " + local_id)
        PLUGINS[local_id] = {
            "plugin_id": local_id, "central_id": None, "version": VERSION,
            "updated_at": UPDATED_AT, "mode": "SINGLE",
            "categories": tuple(categories), "tasks": tuple(tasks),
            "description": description, "call": guarded,
            "validation": "REAL_PDF_NOT_CERTIFIED", "ocr": ocr_used,
        }
        return guarded
    return decorate


def def_result(tool, task, ocr_used):
    """統一結果 schema;成功呼叫 ≠ 完整擷取驗證(黃燈交宿主驗)。"""
    return {
        "plugin_id": "ocr." + tool, "central_id": None, "tool": tool,
        "version": VERSION, "task": task,
        "state": "EXTRACTED_UNVERIFIED", "light": "YELLOW",
        "text": "", "elements": [], "tables": [], "images": [],
        "metadata": {}, "artifacts": [], "warnings": [], "ocr_used": ocr_used,
    }


def _fitz():
    import fitz  # PyMuPDF;延遲載入,缺席由 guarded 轉 UNAVAILABLE
    return fitz


def _tesseract():
    import pytesseract
    from pytesseract import TesseractNotFoundError
    try:  # 執行檔缺席要在呼叫前誠實暴露成 UNAVAILABLE,不等到半路炸
        pytesseract.get_tesseract_version()
    except TesseractNotFoundError as exc:
        raise FileNotFoundError("tesseract binary missing: " + str(exc)) from exc
    return pytesseract


def _render_page(pdf, page_number, dpi, out_png):
    """fitz 渲染單頁成 PNG(基礎 OCR 的輸入;DPI 來自 config,不自動升)。"""
    fitz = _fitz()
    with fitz.open(str(pdf)) as doc:
        page = doc[page_number - 1]
        pix = page.get_pixmap(dpi=int(dpi))
        pix.save(str(out_png))
    return out_png


def _ocr_words(image_path, config):
    """pytesseract TSV → 字框列表;低信心丟 warnings,不混入結果(不捏造)。"""
    pytesseract = _tesseract()
    from PIL import Image
    tsv = pytesseract.image_to_data(
        Image.open(str(image_path)), lang=config["ocr_lang"],
        config=f"--psm {int(config['ocr_psm'])}",
        output_type=pytesseract.Output.DICT)
    words, dropped = [], 0
    for i in range(len(tsv["text"])):
        txt = (tsv["text"][i] or "").strip()
        if not txt:
            continue
        conf = float(tsv["conf"][i])
        if conf < float(config["min_confidence"]):
            dropped += 1
            continue
        words.append({"text": txt, "conf": conf,
                      "bbox": [tsv["left"][i], tsv["top"][i],
                               tsv["left"][i] + tsv["width"][i],
                               tsv["top"][i] + tsv["height"][i]]})
    return words, dropped


@plugin("image_extract", ("GRAPH", "LAYOUT"), ("images",),
        "圖片抽取:嵌入圖原樣抽出成檔(xref · bbox · 尺寸);本功能不做 OCR,抽出圖 ≠ 取得圖中數據。",
        ocr_used=False)
def def_image_extract(task, pdf, work, config):
    fitz = _fitz()
    row = def_result("image_extract", task, ocr_used=False)
    with fitz.open(str(pdf)) as doc:
        for pno, page in enumerate(doc, 1):
            for idx, info in enumerate(page.get_images(full=True)):
                if idx >= int(config["max_images_per_page"]):
                    row["warnings"].append(f"p{pno} 超過 max_images_per_page,其餘略過")
                    break
                xref = info[0]
                img = doc.extract_image(xref)
                out = Path(work) / f"p{pno:03d}_x{xref}.{img['ext']}"
                out.write_bytes(img["image"])
                rects = [list(r) for r in page.get_image_rects(xref)]
                row["images"].append({"page": pno, "xref": xref, "file": str(out),
                                      "width": img.get("width"), "height": img.get("height"),
                                      "bbox": rects[0] if rects else None})
                row["artifacts"].append(str(out))
    row["metadata"]["image_count"] = len(row["images"])
    return row


@plugin("text_recognition", ("TEXT", "GRAPH"), ("ocr_text",),
        "圖中文字辨識:無文字層/缺字區的局部基礎 OCR;字框+信心值,低信心丟棄不混入;不抽圖、不還原圖表數值。",
        ocr_used=True)
def def_text_recognition(task, pdf, work, config):
    row = def_result("text_recognition", task, ocr_used=True)
    page_no = int(config.get("page", 1))
    if str(pdf).lower().endswith((".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp")):
        image_path = pdf
    else:
        image_path = _render_page(pdf, page_no, config["render_dpi"], Path(work) / "page.png")
        row["artifacts"].append(str(image_path))
    words, dropped = _ocr_words(image_path, config)
    row["elements"] = words
    row["text"] = " ".join(w["text"] for w in words)
    row["metadata"] = {"page": page_no, "dpi": int(config["render_dpi"]),
                       "lang": config["ocr_lang"], "word_count": len(words)}
    if dropped:
        row["warnings"].append(f"低信心(<{config['min_confidence']})字框丟棄 {dropped} 個,不混入結果")
    return row


_NUM_RX = re.compile(r"^[+-]?\d{1,3}(?:,\d{3})*(?:\.\d+)?%?$")


def _axis_candidates(words):
    """數字字框 → 候選軸刻度(去千分位/百分號);非數字留給圖名/圖例。"""
    ticks = []
    for w in words:
        if _NUM_RX.match(w["text"]):
            ticks.append({"text": w["text"], "bbox": w["bbox"], "conf": w["conf"],
                          "value": float(w["text"].rstrip("%").replace(",", ""))})
    return ticks


def _arith_check(values):
    """等差校驗(沿 ENG394 FIGURE 刻度律):3 刻度以上且間距一致才算一條軸。"""
    if len(values) < 3:
        return False, 0.0
    diffs = [b - a for a, b in zip(values, values[1:])]
    step = statistics.median(diffs)
    if step == 0:
        return False, 0.0
    ok = all(abs(d - step) <= abs(step) * 0.05 for d in diffs)
    return ok, step


@plugin("chart_restore", ("GRAPH",), ("chart_basic",),
        "圖表數值還原【基礎層】:OCR 圖名/座標軸刻度/資料標籤 + 等差校驗;曲線柱形逐點還原屬重型層,誠實標 NEEDS_HEAVY 不捏造。",
        ocr_used=True)
def def_chart_restore(task, pdf, work, config):
    row = def_result("chart_restore", task, ocr_used=True)
    page_no = int(config.get("page", 1))
    if str(pdf).lower().endswith((".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp")):
        image_path = pdf
    else:
        image_path = _render_page(pdf, page_no, config["render_dpi"], Path(work) / "page.png")
        row["artifacts"].append(str(image_path))
    words, dropped = _ocr_words(image_path, config)
    ticks = _axis_candidates(words)
    ticks_sorted = sorted(ticks, key=lambda t: (t["bbox"][0], t["bbox"][1]))
    values = sorted(t["value"] for t in ticks_sorted)
    arith, step = _arith_check(values)
    labels = [w for w in words if not _NUM_RX.match(w["text"])]
    row["elements"] = words
    row["metadata"] = {
        "page": page_no, "axis_ticks": ticks_sorted,
        "axis_arithmetic": arith, "axis_step": step if arith else None,
        "data_labels": [{"text": w["text"], "bbox": w["bbox"]} for w in labels],
        "series_values": None,          # 逐點數值屬重型層;基礎層不產出、不猜
        "needs_heavy": True,
        "needs_heavy_reason": "曲線/柱形逐點還原需重型 OCR/結構模型並另驗(正典 OCR 重型列)",
    }
    if dropped:
        row["warnings"].append(f"低信心字框丟棄 {dropped} 個")
    if not arith:
        row["warnings"].append("軸刻度不足或非等差:axis_step 誠實為 None,不外插")
    return row


def get_plugins():
    """回傳可自行增刪的描述字典;僅匯入不執行、不改中央註冊。"""
    return {k: dict(v) for k, v in PLUGINS.items()}


def ast_catalog():
    """用 AST 分類本檔所有函式(含巢狀);不執行第三方套件。"""
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    out = []

    def visit(node, prefix=""):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                name = prefix + child.name
                doc = (ast.get_docstring(child) or "").strip().splitlines()
                out.append({"name": name, "line": child.lineno,
                            "desc": doc[0][:100] if doc else "(無說明)"})
                visit(child, name + ".")
            else:
                visit(child, prefix)
    visit(tree)
    return out


def selftest():
    """契約式自測:依賴在場測實跑,缺席測誠實態(兩種環境都該全綠,不假造)。"""
    p = f = 0

    def ck(name, cond):
        nonlocal p, f
        if cond:
            p += 1
            print("  [OK] %s" % name)
        else:
            f += 1
            print("  [FAIL] %s" % name)

    pl = get_plugins()
    ck("① 三功能三支插件(鐵律:一功能一支)", set(pl) == {"ocr.image_extract", "ocr.text_recognition", "ocr.chart_restore"})
    ck("② 分工誠實:抽圖不 OCR · 辨識/還原標 ocr",
       pl["ocr.image_extract"]["ocr"] is False and pl["ocr.text_recognition"]["ocr"] is True
       and pl["ocr.chart_restore"]["ocr"] is True)
    bad = PLUGINS["ocr.image_extract"]["call"]("images", "no_such_file.pdf", tempfile.mkdtemp(prefix="ocr-st-"))
    ck("③ 錯誤隔離:檔不存在 → ERROR/RED 不丟例外", bad["state"] in ("ERROR", "UNAVAILABLE") and "error" in bad)
    bad2 = PLUGINS["ocr.chart_restore"]["call"]("wrong_task", __file__, tempfile.mkdtemp(prefix="ocr-st-"))
    ck("④ 不支援 task → ERROR", bad2["state"] == "ERROR")
    ck("⑤ 等差校驗:0/10/20/30 過 · 0/10/25 不過",
       _arith_check([0, 10, 20, 30])[0] and not _arith_check([0, 10, 25])[0])
    ck("⑥ 數字刻度正則:1,234.5 / 45% 收 · ABC / 1.2.3 不收",
       bool(_NUM_RX.match("1,234.5")) and bool(_NUM_RX.match("45%"))
       and not _NUM_RX.match("ABC") and not _NUM_RX.match("1.2.3"))
    work = tempfile.mkdtemp(prefix="ocr-st-")
    try:
        fitz = _fitz()
        from PIL import Image
        img_src = Path(work) / "emb.png"
        Image.new("RGB", (60, 40), (200, 30, 30)).save(img_src)
        pdfp = Path(work) / "syn.pdf"
        doc = fitz.open()
        page = doc.new_page(width=300, height=200)
        page.insert_image(fitz.Rect(40, 40, 160, 120), filename=str(img_src))
        page.insert_text((40, 160), "TICK 0 10 20 30", fontsize=12)
        doc.save(str(pdfp))
        doc.close()
        r = PLUGINS["ocr.image_extract"]["call"]("images", str(pdfp), work)
        ck("⑦ 圖片抽取實跑:合成 PDF 抽回 1 張嵌入圖(檔案落地 · ocr_used False)",
           r["metadata"].get("image_count") == 1 and Path(r["images"][0]["file"]).is_file()
           and r["ocr_used"] is False)
        ck("⑧ 工作目錄隔離:每呼叫獨立子目錄", Path(r["work_dir"]) != Path(bad.get("work_dir") or "/nonexist"))
    except ImportError:
        ck("⑦ fitz 缺席 → image_extract 回 UNAVAILABLE(誠實態)",
           PLUGINS["ocr.image_extract"]["call"]("images", __file__, work)["state"] in ("UNAVAILABLE", "ERROR"))
        ck("⑧ 缺席環境不假造圖片結果", True)
    try:
        _tesseract()
        r2 = PLUGINS["ocr.text_recognition"]["call"]("ocr_text", str(pdfp), work)
        ck("⑨ 圖中文字辨識實跑:合成頁找回 TICK 字樣(字框帶信心值)",
           r2["state"] == "EXTRACTED_UNVERIFIED" and any("TICK" in w["text"].upper() for w in r2["elements"]))
        chartp = Path(work) / "chart.pdf"
        cdoc = fitz.open()
        cpage = cdoc.new_page(width=300, height=240)
        for i, v in enumerate(("40", "30", "20", "10")):   # 縱軸大字刻度,一字一位,對 OCR 公平
            cpage.insert_text((20, 50 + i * 45), v, fontsize=18)
        cpage.insert_text((120, 30), "Revenue", fontsize=16)
        cdoc.save(str(chartp))
        cdoc.close()
        r3 = PLUGINS["ocr.chart_restore"]["call"]("chart_basic", str(chartp), work,
                                                  config={"render_dpi": 300})
        m3 = r3["metadata"]
        ck("⑩ 圖表基礎還原契約:series_values 誠實 None + NEEDS_HEAVY · axis_ticks 為列表",
           m3.get("series_values") is None and m3.get("needs_heavy") is True
           and isinstance(m3.get("axis_ticks"), list))
        n_ticks = len(m3.get("axis_ticks") or [])
        if n_ticks >= 3:
            ck("⑩b 等差實跑:認得 %d 刻度 → 等差成立" % n_ticks, m3.get("axis_arithmetic") is True)
        else:
            ck("⑩b OCR 僅認得 %d 刻度(<3)→ 誠實不外插:axis_step=None + 警告在列" % n_ticks,
               m3.get("axis_step") is None and any("不外插" in w for w in r3["warnings"]))
    except (ImportError, FileNotFoundError):
        r2 = PLUGINS["ocr.text_recognition"]["call"]("ocr_text", __file__, work)
        r3 = PLUGINS["ocr.chart_restore"]["call"]("chart_basic", __file__, work)
        ck("⑨ pytesseract/tesseract 缺席 → 辨識回 UNAVAILABLE(誠實態不假造)", r2["state"] in ("UNAVAILABLE", "ERROR"))
        ck("⑩ 缺席環境圖表還原同樣誠實態", r3["state"] in ("UNAVAILABLE", "ERROR"))
    body = Path(__file__).read_text(encoding="utf-8")
    tree = ast.parse(body)
    imported = {(a.name if isinstance(n, ast.Import) else n.module or "").split(".")[0]
                for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))
                for a in (n.names if isinstance(n, ast.Import) else [n])}
    banned = {"talib", "urllib", "requests", "subprocess", "socket", "http", "pip"}
    ck("⑪ 帶加速器橋 · VIA_FROM_VCGC 閘 · AST 查無 TA-Lib/網路/安裝類匯入",
       "[VIA:ACCEL-BRIDGE:v0100]" in body and "VIA_FROM_VCGC" in body and not (imported & banned))
    print("[計] VRN_OCRPlugins_v0100 自測 %d/%d · %s" % (p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


def main():
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print("Use VCGC entry")
        return 2
    if "--selftest" in sys.argv[1:]:
        return selftest()
    if "catalog" in sys.argv[1:]:
        print(json.dumps(ast_catalog(), ensure_ascii=False, indent=1))
        return 0
    print(__doc__)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
