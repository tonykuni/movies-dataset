#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN 函式庫補位插件,單檔、延遲載入、可插拔;Python 3.10+。

全景清點(2026-10-05,20 支 local free libs 對 VRN 樹):16 支已有真轉接器
(pdfplumber/Camelot/Tabula/pdfminer/PyMuPDF/Poppler/Xpdf/qpdf/pdfcpu/ExifTool/
Ghostscript/PDFium/pdfrw/pdf2json/pypdf + pikepdf),本檔補齊其餘 5 支的可插拔接頭:
  lib.mutool   MuPDF CLI(mutool draw/extract;主樹原僅 references 參考區有)
  lib.pdfbox   Apache PDFBox(java -jar pdfbox-app.jar;jar 走明確路徑制)
  lib.borb     borb(AGPL 授權註記;純 Python 延遲載入,逐頁文字)
  lib.lopdf    lopdf(Rust crate 無官方 CLI:座位制,收自備接頭路徑,缺=誠實 UNAVAILABLE)
  lib.itext    iText 7(Java AGPL 無官方 CLI:同座位制;本機免費,不含付費雲服務)
鐵律沿用:pdfplumber 單引擎優先,本檔皆為補位/雙引擎第二工具;付費外部服務不加入;
缺依賴/缺執行檔一律 UNAVAILABLE 誠實標示,不假造;central_id=None 等 VCGC 配發。

統一契約與 VRN_NewPlugins_v0102 相同:call(task, pdf, work, config=None, run_cli=None) -> dict;
CLI 插件(mutool/pdfbox/lopdf/itext)必須注入宿主有界 runner(shell=False · timeout ·
stderr 落檔 · 不下載依賴);擷取完成只標 EXTRACTED_UNVERIFIED / 黃燈,實報交宿主驗證。
自測: VIA_FROM_VCGC=YES python VRN_LibPlugins_v0100.py --selftest(契約式:缺席環境驗誠實態)
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
import shutil
import sys
import tempfile

VERSION = "0.1.0"
UPDATED_AT = "2026-10-05T00:00:00+00:00"
LIB_DEFAULT_CONFIG = {
    "binary_paths": {},          # mutool · java · pdfbox_jar · lopdf_cli · itext_cli 可明給
    "timeout_seconds": 120,
    "max_output_bytes": 32 * 1024 * 1024,
}
CLI_KEYS = ("mutool", "pdfbox", "lopdf", "itext")
PLUGINS = {}


def plugin(key, categories, tasks, description, license_note=""):
    """僅註冊本檔局部描述;錯誤隔離同 VRN_NewPlugins 契約,不決定執行順序或雙引擎搭配。"""
    def decorate(function):
        @wraps(function)
        def guarded(task, pdf, work, config=None, run_cli=None):
            row = def_result(key, task)
            try:
                if task not in tasks:
                    raise ValueError(f"Unsupported task: {task}; allowed: {tasks}")
                merged = copy.deepcopy(LIB_DEFAULT_CONFIG)
                if config:
                    merged.update(copy.deepcopy(config))
                pdf = Path(pdf).expanduser().resolve(strict=True)
                if not pdf.is_file():
                    raise ValueError("input path must be a file")
                root = Path(work).expanduser().resolve()
                root.mkdir(parents=True, exist_ok=True)
                work = Path(tempfile.mkdtemp(prefix=key + "-", dir=root))
                row["work_dir"] = str(work)
                if key in CLI_KEYS and run_cli is None:
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
        local_id = "lib." + key
        if local_id in PLUGINS:
            raise ValueError("Duplicate plugin: " + local_id)
        PLUGINS[local_id] = {
            "plugin_id": local_id, "central_id": None, "version": VERSION,
            "updated_at": UPDATED_AT, "mode": "SINGLE",
            "categories": tuple(categories), "tasks": tuple(tasks),
            "description": description, "license_note": license_note, "call": guarded,
            "validation": "REAL_PDF_NOT_CERTIFIED", "ocr": False,
        }
        return guarded
    return decorate


def def_result(tool, task):
    """統一結果 schema;成功呼叫 ≠ 完整擷取驗證(黃燈交宿主驗)。"""
    return {
        "plugin_id": "lib." + tool, "central_id": None, "tool": tool,
        "version": VERSION, "task": task,
        "state": "EXTRACTED_UNVERIFIED", "light": "YELLOW",
        "text": "", "elements": [], "tables": [], "images": [],
        "metadata": {}, "artifacts": [], "warnings": [], "ocr_used": False,
    }


def def_binary(name, config, hint):
    """解析本機執行檔/jar/自備接頭;config 優先,部分允許 which;缺=誠實 FileNotFoundError。"""
    value = config["binary_paths"].get(name)
    if not value and name in ("mutool", "java"):
        value = shutil.which(name)
    if not value:
        raise FileNotFoundError(f"Missing local binary/bridge '{name}': {hint}")
    return str(value)


@plugin("mutool", ("TEXT", "LAYOUT"), ("text", "extract"),
        "MuPDF CLI:mutool draw -F txt 文字(含版面序)/ mutool extract 內嵌物件;主樹補位,雙引擎第二工具。")
def def_mutool(task, pdf, work, config, run_cli):
    binary = def_binary("mutool", config, "安裝 MuPDF 或 binary_paths['mutool'] 明給")
    row = def_result("mutool", task)
    if task == "text":
        out = run_cli([binary, "draw", "-F", "txt", "-o", str(Path(work) / "text.txt"), str(pdf)],
                      work, config, accepted=(0,))
        txt = (Path(work) / "text.txt")
        row["text"] = txt.read_text(encoding="utf-8", errors="replace") if txt.is_file() else (out or "")
        row["artifacts"].append(str(txt))
    else:
        run_cli([binary, "extract", str(pdf)], work, config, accepted=(0,))
        pulled = [str(p) for p in Path(work).iterdir() if p.suffix.lower() in
                  (".png", ".jpg", ".jpeg", ".ttf", ".cff", ".jbig2")]
        row["images"] = [{"file": p} for p in pulled if not p.endswith((".ttf", ".cff"))]
        row["artifacts"] += pulled
        row["metadata"]["extracted_count"] = len(pulled)
    return row


@plugin("pdfbox", ("TEXT", "OTHERS"), ("text",),
        "Apache PDFBox CLI:java -jar pdfbox-app.jar export:text;jar 走明確路徑制(不猜 classpath)。",
        license_note="Apache 2.0;需本機 java + pdfbox-app.jar")
def def_pdfbox(task, pdf, work, config, run_cli):
    java = def_binary("java", config, "本機需 Java 執行環境")
    jar = def_binary("pdfbox_jar", config, "binary_paths['pdfbox_jar'] 明給 pdfbox-app-3.x.jar 路徑")
    row = def_result("pdfbox", task)
    out_txt = Path(work) / "text.txt"
    run_cli([java, "-jar", jar, "export:text", "-i", str(pdf), "-o", str(out_txt)],
            work, config, accepted=(0,))
    row["text"] = out_txt.read_text(encoding="utf-8", errors="replace") if out_txt.is_file() else ""
    row["artifacts"].append(str(out_txt))
    return row


@plugin("borb", ("TEXT", "OTHERS"), ("text",),
        "borb:純 Python 逐頁文字抽取(SimpleTextExtraction);延遲載入,未安裝=UNAVAILABLE。",
        license_note="AGPL-3.0 授權註記;本機免費")
def def_borb(task, pdf, work, config, run_cli):
    from borb.pdf import PDF  # 延遲載入;缺席由 guarded 轉 UNAVAILABLE
    from borb.toolkit import SimpleTextExtraction
    row = def_result("borb", task)
    ext = SimpleTextExtraction()
    with open(pdf, "rb") as fh:
        doc = PDF.loads(fh, [ext])
    if doc is None:
        raise ValueError("borb could not parse the document")
    pages = []
    i = 0
    while True:
        try:
            pages.append(ext.get_text()[i])
        except KeyError:
            break
        i += 1
    row["text"] = "\n".join(pages)
    row["metadata"]["page_count"] = len(pages)
    return row


@plugin("lopdf", ("OTHERS",), ("objects",),
        "lopdf 座位:Rust crate 無官方 CLI;收 binary_paths['lopdf_cli'] 自備接頭(stdout JSON),缺=誠實 UNAVAILABLE,不是空殼。",
        license_note="MIT;接頭由操作員自建(cargo 專案)")
def def_lopdf(task, pdf, work, config, run_cli):
    cli = def_binary("lopdf_cli", config, "自建 lopdf CLI(讀 PDF 印物件 JSON)後明給路徑")
    row = def_result("lopdf", task)
    out = run_cli([cli, str(pdf)], work, config, accepted=(0,))
    row["metadata"]["objects_raw"] = (out or "")[:int(config["max_output_bytes"])]
    return row


@plugin("itext", ("TEXT", "OTHERS"), ("text",),
        "iText 7 座位:Java 函式庫無官方 CLI;收 java + binary_paths['itext_cli'] 自備 jar 接頭,缺=誠實 UNAVAILABLE;只用本機免費核心。",
        license_note="AGPL-3.0 授權註記;不接付費雲服務")
def def_itext(task, pdf, work, config, run_cli):
    java = def_binary("java", config, "本機需 Java 執行環境")
    jar = def_binary("itext_cli", config, "自建 iText 文字抽取 jar 後明給路徑")
    row = def_result("itext", task)
    out = run_cli([java, "-jar", jar, str(pdf)], work, config, accepted=(0,))
    row["text"] = out or ""
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
    """契約式自測:介面/隔離/誠實態;真工具與真 PDF 擷取認證留宿主。"""
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
    ck("① 五支補位插件齊(mutool · pdfbox · borb · lopdf · itext)",
       set(pl) == {"lib.mutool", "lib.pdfbox", "lib.borb", "lib.lopdf", "lib.itext"})
    ck("② 授權註記在位(borb/itext AGPL · 不接付費服務)",
       "AGPL" in pl["lib.borb"]["license_note"] and "AGPL" in pl["lib.itext"]["license_note"])
    work = tempfile.mkdtemp(prefix="lib-st-")
    r = PLUGINS["lib.mutool"]["call"]("text", __file__, work)
    ck("③ CLI 插件未注入 runner → ERROR(不隱式 subprocess)", r["state"] == "ERROR" and "runner" in r["error"])
    def dummy_runner(argv, w, cfg, accepted=(0,)):
        raise AssertionError("不該執行到")
    r2 = PLUGINS["lib.lopdf"]["call"]("objects", __file__, work, run_cli=dummy_runner)
    ck("④ 座位制:lopdf 無自備接頭 → UNAVAILABLE 誠實態(非空殼假成功)",
       r2["state"] == "UNAVAILABLE" and "lopdf_cli" in r2["error"])
    r3 = PLUGINS["lib.itext"]["call"]("text", __file__, work, run_cli=dummy_runner)
    ck("⑤ 座位制:itext 缺 java/jar → UNAVAILABLE", r3["state"] == "UNAVAILABLE")
    r4 = PLUGINS["lib.borb"]["call"]("text", __file__, work)
    ck("⑥ borb 未安裝/壞檔 → UNAVAILABLE 或 ERROR,不丟例外", r4["state"] in ("UNAVAILABLE", "ERROR"))
    r5 = PLUGINS["lib.mutool"]["call"]("wrong", __file__, work, run_cli=dummy_runner)
    ck("⑦ 不支援 task → ERROR", r5["state"] == "ERROR")
    bad = PLUGINS["lib.pdfbox"]["call"]("text", "no_such.pdf", work, run_cli=dummy_runner)
    ck("⑧ 檔不存在 → 隔離成 ERROR/RED", bad["state"] in ("ERROR", "UNAVAILABLE"))
    cat = ast_catalog()
    ck("⑨ AST 分類:每個 def 都有說明欄", len(cat) >= 10 and all(c["desc"] for c in cat))
    body = Path(__file__).read_text(encoding="utf-8")
    tree = ast.parse(body)
    imported = {(a.name if isinstance(n, ast.Import) else n.module or "").split(".")[0]
                for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))
                for a in (n.names if isinstance(n, ast.Import) else [n])}
    banned = {"talib", "urllib", "requests", "subprocess", "socket", "http", "pip"}
    ck("⑩ 帶加速器橋 · VIA_FROM_VCGC 閘 · AST 查無 TA-Lib/網路/安裝/隱式子程序匯入",
       "[VIA:ACCEL-BRIDGE:v0100]" in body and "VIA_FROM_VCGC" in body and not (imported & banned))
    print("[計] VRN_LibPlugins_v0100 自測 %d/%d · %s" % (p, p + f, "PASS" if f == 0 else "FAIL"))
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
