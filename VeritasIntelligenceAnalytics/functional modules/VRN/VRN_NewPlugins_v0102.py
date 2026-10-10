#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN 新增插件，單檔、延遲載入、可插拔；Python 3.10+。

SYSTEM MANAGER:
  只包含基準清點中缺少的 9 個原生非 OCR adapter，不複製既有引擎。
  LAYOUT / TABLE / TEXT / GRAPH / OTHERS 分類由 PLUGINS 提供。
  全部為 SINGLE；DUAL 組合、pdfplumber 優先、升級策略由宿主處理。
  TABLE 無新增 adapter：既有 pdfplumber / Camelot / Tabula 等由宿主重用。
  borb / lopdf / iText 的具體 bridge 未實作，不註冊空殼。
  本檔不安裝、不下載、不連雲端、不自動註冊中央 SSOT、不改成功舊引擎。
  plugin_id 是本地穩定鍵；central_id=None，等待 VCGC 配發，不能冒充中央編號。

宿主使用方式::

    import VRN_NewPlugins_v0102 as additions
    plugins = additions.get_plugins()       # 新字典，僅匯入不執行
    plugins.pop("new.xpdf", None)           # 本地拔除，不影響其他插件
    result = plugins["new.pdfium"]["call"](
        "layout", "report.pdf", "temp/results", config={})

統一契約：call(task, pdf, work, config=None, run_cli=None) -> dict。
  work 為呼叫者提供的 TEMP 根目錄；每次建立獨立子目錄避免舊結果混入。
  CLI 插件必須注入既有 runner，介面如下：
    run_cli(argv: list[str], work: Path, config: dict, accepted=(0,)) -> str
  runner 必須：shell=False、設 timeout、將 stderr 寫入 work/stderr.log、
  保存退出碼與警告、終止逾時程序樹、限制輸出與 TEMP 用量、不下載依賴。
  原生 Python 插件亦應由宿主隔離程序執行；本地 try/except 無法中止卡住的 C 擴充。
  加速器由宿主包覆 call，無全域 monkey patch；工作資料夾不自動刪除，便於驗證。
  擷取完成只標記 EXTRACTED_UNVERIFIED / 黃燈，實報完整性由宿主驗證。
  型別/語法/契約測試不等於 Windows、依賴版本或實際 PDF 擷取認證。
"""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0100] 加速器橋(2026-10-08 accel sweep 注入;L103 最高政策 PY 導入加速器;缺席不擋,記黃) =====
import sys as _ab_sys
from pathlib import Path as _ab_Path
_ab_p = _ab_Path(__file__).resolve()
while _ab_p.parent != _ab_p:
    if (_ab_p / "supportive modules").is_dir():
        _ab_sys.path.insert(0, str(_ab_p / "supportive modules"))
        break
    _ab_p = _ab_p.parent
try:
    import VeritasCeleritas_v1141 as _ACCEL  # noqa: F401
except Exception:  # noqa: BLE001
    _ACCEL = None
# ===== [VIA:ACCEL-BRIDGE:END] =====

import ast
import copy
from functools import wraps
import json
from pathlib import Path
import shutil
import tempfile

VERSION = "0.1.2"
UPDATED_AT = "2026-10-04T22:11:29+08:00"
BASELINE = "local inventory v0100; GitHub latest not asserted"
CATEGORIES = ("LAYOUT", "TABLE", "TEXT", "GRAPH", "OTHERS")
DEFAULT_CONFIG = {
    "binary_paths": {}, "render_dpi": 144,
    "timeout_seconds": 120, "max_output_bytes": 32 * 1024 * 1024,
    "max_temp_bytes": 512 * 1024 * 1024,
}
PENDING_IMPLEMENTATION = ("borb", "lopdf", "itext")
PLUGINS = {}


def plugin(key, categories, tasks, description):
    """僅註冊本檔局部描述；提供錯誤隔離，不決定執行順序或雙引擎搭配。"""
    def decorate(function):
        @wraps(function)
        def guarded(task, pdf, work, config=None, run_cli=None):
            row = def_result(key, task)
            try:
                if task not in tasks:
                    raise ValueError(f"Unsupported task: {task}; allowed: {tasks}")
                merged = copy.deepcopy(DEFAULT_CONFIG)
                if config:
                    merged.update(copy.deepcopy(config))
                pdf = Path(pdf).expanduser().resolve(strict=True)
                if not pdf.is_file():
                    raise ValueError("PDF path must be a file")
                root = Path(work).expanduser().resolve()
                root.mkdir(parents=True, exist_ok=True)
                work = Path(tempfile.mkdtemp(prefix=key + "-", dir=root))
                row["work_dir"] = str(work)
                if key in ("xpdf", "qpdf", "pdfcpu", "exiftool", "ghostscript", "pdf2json") and run_cli is None:
                    raise ValueError("Inject the host bounded CLI runner; no implicit subprocess")
                result = function(task, pdf, work, merged, run_cli)
                result["work_dir"] = str(work)
                result["source"] = str(pdf)
                if (work / "stderr.log").is_file():
                    result["artifacts"].append(str(work / "stderr.log"))
                return result
            except (ImportError, FileNotFoundError) as exc:
                row.update(state="UNAVAILABLE", light="YELLOW", error=str(exc))
            except Exception as exc:
                row.update(state="ERROR", light="RED", error=f"{type(exc).__name__}: {exc}")
            return row
        local_id = "new." + key
        if local_id in PLUGINS:
            raise ValueError("Duplicate plugin: " + local_id)
        PLUGINS[local_id] = {
            "plugin_id": local_id, "central_id": None, "version": VERSION,
            "updated_at": UPDATED_AT, "mode": "SINGLE",
            "categories": tuple(categories), "tasks": tuple(tasks),
            "description": description, "call": guarded,
            "validation": "REAL_PDF_NOT_CERTIFIED", "ocr": False,
        }
        return guarded
    return decorate


def def_result(tool, task):
    """統一結果 schema；不把成功呼叫錯當成完整擷取驗證。"""
    return {
        "plugin_id": "new." + tool, "central_id": None, "tool": tool,
        "version": VERSION, "task": task,
        "state": "EXTRACTED_UNVERIFIED", "light": "YELLOW",
        "text": "", "elements": [], "tables": [], "images": [],
        "metadata": {}, "artifacts": [], "warnings": [], "ocr_used": False,
    }


def def_binary(name, config):
    """解析本機執行檔；Xpdf 僅接受明確路徑，避免誤用 Poppler pdftotext。"""
    value = config["binary_paths"].get(name)
    if not value and name != "xpdf_pdftotext":
        value = shutil.which(name)
    if not value:
        raise FileNotFoundError("Missing local binary: " + name)
    return str(value)


@plugin('pdfium', ['TEXT', 'LAYOUT', 'OTHERS'], ['text', 'layout', 'metadata'], 'PDFium 原生文字、字元座標與頁面尺寸；不執行 OCR。')
def def_pdfium_native(task, pdf, work, config, run_cli=None):
    """PDFium 原生文字、字元座標與頁面尺寸；不執行 OCR。"""
    pdf, work = Path(pdf), Path(work)
    work.mkdir(parents=True, exist_ok=True)
    row=def_result('pdfium',task)
    def binary(name):
        return def_binary(name,config)
    import pypdfium2 as pdfium
    document = pdfium.PdfDocument(pdf)
    try:
        row['metadata'] = {'pages': len(document), 'page_sizes': []}
        for i in range(len(document)):
            page = document[i]
            textpage = page.get_textpage()
            try:
                row['metadata']['page_sizes'].append(list(page.get_size()))
                text = textpage.get_text_bounded()
                row['text'] += text + '\n'
                if task == 'layout':
                    for j in range(textpage.count_chars()):
                        left, bottom, right, top = textpage.get_charbox(j)
                        row['elements'].append({'page': i + 1, 'text': textpage.get_text_range(j, 1), 'bbox': [left, page.get_height() - top, right, page.get_height() - bottom]})
            finally:
                textpage.close()
                page.close()
    finally:
        document.close()
    return row

@plugin('pdfrw', ['OTHERS'], ['metadata'], '讀取 PDF 文件資訊與 MediaBox 尺寸；不是影像 DPI。')
def def_pdfrw_native(task, pdf, work, config, run_cli=None):
    """讀取 PDF 文件資訊與 MediaBox 尺寸；不是影像 DPI。"""
    pdf, work = Path(pdf), Path(work)
    work.mkdir(parents=True, exist_ok=True)
    row=def_result('pdfrw',task)
    def binary(name):
        return def_binary(name,config)
    import pdfrw
    document = pdfrw.PdfReader(str(pdf))
    row['metadata'] = {'pages': len(document.pages), 'info': str(document.Info), 'page_sizes': [[float(p.inheritable.MediaBox[2]) - float(p.inheritable.MediaBox[0]), float(p.inheritable.MediaBox[3]) - float(p.inheritable.MediaBox[1])] for p in document.pages]}
    return row

@plugin('pikepdf', ['GRAPH', 'OTHERS'], ['image', 'metadata'], '抽出頁面嵌入影像及文件資訊；不解析圖中數值。')
def def_pikepdf_native(task, pdf, work, config, run_cli=None):
    """抽出頁面嵌入影像及文件資訊；不解析圖中數值。"""
    pdf, work = Path(pdf), Path(work)
    work.mkdir(parents=True, exist_ok=True)
    row=def_result('pikepdf',task)
    def binary(name):
        return def_binary(name,config)
    import pikepdf
    with pikepdf.open(pdf) as document:
        row['metadata'] = {'pages': len(document.pages), 'info': {str(k): str(v) for k, v in document.docinfo.items()}}
        if task == 'image':
            for n, page in enumerate(document.pages, 1):
                for i, (_, image) in enumerate(page.images.items()):
                    output = pikepdf.PdfImage(image).extract_to(fileprefix=str(work / ('p%d_i%d' % (n, i))))
                    row['images'].append({'page': n, 'artifact': str(output), 'pixels': [int(image.Width), int(image.Height)]})
    return row

@plugin('xpdf', ['TEXT'], ['text'], 'Xpdf 保留排版文字；須明確指定 Xpdf 執行檔。')
def def_xpdf_native(task, pdf, work, config, run_cli=None):
    """Xpdf 保留排版文字；須明確指定 Xpdf 執行檔。"""
    pdf, work = Path(pdf), Path(work)
    work.mkdir(parents=True, exist_ok=True)
    row=def_result('xpdf',task)
    def binary(name):
        return def_binary(name,config)
    row['text'] = run_cli([binary('xpdf_pdftotext'), '-layout', str(pdf), '-'], work, config)
    return row

@plugin('qpdf', ['OTHERS'], ['metadata'], '輸出 PDF 結構物件 JSON；保留警告退出碼。')
def def_qpdf_native(task, pdf, work, config, run_cli=None):
    """輸出 PDF 結構物件 JSON；保留警告退出碼。"""
    pdf, work = Path(pdf), Path(work)
    work.mkdir(parents=True, exist_ok=True)
    row=def_result('qpdf',task)
    def binary(name):
        return def_binary(name,config)
    row['metadata']['objects'] = json.loads(run_cli([binary('qpdf'), '--json', str(pdf)], work, config, accepted=(0, 3)))
    return row

@plugin('pdfcpu', ['OTHERS'], ['metadata'], '輸出 pdfcpu info 原始資訊；尚未正規化欄位。')
def def_pdfcpu_native(task, pdf, work, config, run_cli=None):
    """輸出 pdfcpu info 原始資訊；尚未正規化欄位。"""
    pdf, work = Path(pdf), Path(work)
    work.mkdir(parents=True, exist_ok=True)
    row=def_result('pdfcpu',task)
    def binary(name):
        return def_binary(name,config)
    row['metadata']['raw_info'] = run_cli([binary('pdfcpu'), 'info', str(pdf)], work, config)
    return row

@plugin('exiftool', ['OTHERS'], ['metadata'], '讀取帶群組名稱的文件 metadata；不推定全文件 DPI。')
def def_exiftool_native(task, pdf, work, config, run_cli=None):
    """讀取帶群組名稱的文件 metadata；不推定全文件 DPI。"""
    pdf, work = Path(pdf), Path(work)
    work.mkdir(parents=True, exist_ok=True)
    row=def_result('exiftool',task)
    def binary(name):
        return def_binary(name,config)
    row['metadata']['tags'] = json.loads(run_cli([binary('exiftool'), '-j', '-G', str(pdf)], work, config))
    return row

@plugin('ghostscript', ['GRAPH', 'OTHERS'], ['image', 'metadata'], '頁面渲染或內容 bounding box；不是嵌入圖片抽取。')
def def_ghostscript_native(task, pdf, work, config, run_cli=None):
    """頁面渲染或內容 bounding box；不是嵌入圖片抽取。"""
    pdf, work = Path(pdf), Path(work)
    work.mkdir(parents=True, exist_ok=True)
    row=def_result('ghostscript',task)
    def binary(name):
        return def_binary(name,config)
    if task == 'image':
        target = work / 'render-%03d.png'
        run_cli([binary('gs'), '-dSAFER', '-dBATCH', '-dNOPAUSE', '-sDEVICE=png16m', '-r' + str(config['render_dpi']), '-sOutputFile=' + str(target), str(pdf)], work, config)
        row['artifacts'] = [str(p) for p in work.glob('render-*.png')]
        row['warnings'].append('Page render; not embedded-image extraction or source DPI')
    else:
        run_cli([binary('gs'), '-dSAFER', '-dBATCH', '-dNOPAUSE', '-sDEVICE=bbox', str(pdf)], work, config)
        row['metadata']['bounding_boxes'] = (work / 'stderr.log').read_text()
    return row

@plugin('pdf2json', ['TEXT', 'LAYOUT'], ['text', 'layout'], '保存 pdf2json 原始 JSON 與文字；座標單位保留原格式。')
def def_pdf2json_native(task, pdf, work, config, run_cli=None):
    """保存 pdf2json 原始 JSON 與文字；座標單位保留原格式。"""
    pdf, work = Path(pdf), Path(work)
    work.mkdir(parents=True, exist_ok=True)
    row=def_result('pdf2json',task)
    def binary(name):
        return def_binary(name,config)
    run_cli([binary('pdf2json'), '-f', str(pdf), '-o', str(work), '-c'], work, config)
    row['artifacts'] = [str(p) for p in work.glob('*.json')]
    row['text'] = '\n'.join((p.read_text(errors='replace') for p in work.glob('*.content.txt')))
    return row

def get_plugins():
    """回傳可自行新增/移除的描述字典；不啟動引擎、不改中央註冊。"""
    return {key: dict(value) for key, value in PLUGINS.items()}


def ast_catalog():
    """用 AST 分類所有函式（含巢狀輔助函式），不執行第三方套件。"""
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    mapped = {item["call"].__name__: item for item in PLUGINS.values()}
    rows = []
    def visit(node, prefix=""):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                qualified = prefix + child.name
                descriptor = mapped.get(child.name, {}) if not prefix else {}
                rows.append({
                    "function": qualified, "line": child.lineno,
                    "signature": ast.unparse(child.args),
                    "description": ast.get_docstring(child) or "Internal helper",
                    "categories": descriptor.get("categories", ("OTHERS",)),
                    "mode": descriptor.get("mode", "HELPER"),
                    "plugin_id": descriptor.get("plugin_id"),
                })
                visit(child, qualified + ".")
            else:
                visit(child, prefix)
    visit(tree)
    return rows


if __name__ == "__main__":
    # 預設僅列出 AST 索引；不擷取任何檔案、不安裝任何依賴。
    print(json.dumps(ast_catalog(), ensure_ascii=False, indent=2))
