#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_ENG052_DocxEngine v0102 — 薄尾:補 --selftest 門(VRN 鏈跑器量得到;正常執行一字不變)
自測項:前版本體語法樹可讀、可載入;十個公開函式(E1 預檢/E4 攤平/E7 去幽靈/擷取梯/修復/驗證/對照/main)都在且可呼叫;
以純函式合成輸入實測 E1 四種簽章判、E4 巢狀攤平、E7 NFKC+零寬拔除、修復三式 clean_text;
暫存夾現做最小 .docx(含 vMerge 垂直合併格)實測內建 XML 末梯、擷取梯、repair_table ffill+升表頭、
validate_table 空值率,並跑 --compare 新舊對照全流程。所有檔案 IO 只在 TemporaryDirectory。
docx2python / python-docx 為選配梯(缺則本體走內建 XML 末梯,設計即如此),缺件只註記不扣分。
前版原封不動留作版史(L04);本檔以 glob 取前版(不釘版號),以 PEP 562 __getattr__ 轉接舊公開面。
"""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(全引擎導入令 2026-08-18;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # accel_map/fetch/pip_install/run_fast
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STEM = "VRN_ENG052_DocxEngine"
PRIOR_PATH = [p for p in sorted(HERE.glob(STEM + "_v*.py")) if p.name < Path(__file__).name][-1]

_BODY = None


def _body():
    """惰性載入前版本體(本體頂層只有標準庫 import/常數/函式;重庫全在函式內,載入零副作用)。"""
    global _BODY
    if _BODY is None:
        spec = importlib.util.spec_from_file_location("_" + STEM + "_body", PRIOR_PATH)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = mod
        spec.loader.exec_module(mod)
        _BODY = mod
    return _BODY


def __getattr__(name):
    """PEP 562:舊公開面(extract_docx / repair_table / compare_docs / W_NS / HERE …)一律轉接前版本體。"""
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(_body(), name)


def main() -> int:
    """正常執行=前版 main 原樣(同一個 sys.argv);--selftest 先攔。"""
    if "--selftest" in sys.argv[1:]:
        return selftest()
    return _body().main()


_W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def _selftest_make_docx(path: Path, para: str, rows: list) -> None:
    """夾具:純標準庫寫最小合法 .docx;rows 內 None=vMerge 續格、("v", 文字)=vMerge 起格。"""
    import zipfile
    from xml.sax.saxutils import escape

    def cell(v):
        if v is None:
            return "<w:tc><w:tcPr><w:vMerge/></w:tcPr><w:p/></w:tc>"
        if isinstance(v, tuple):
            return (f'<w:tc><w:tcPr><w:vMerge w:val="restart"/></w:tcPr>'
                    f"<w:p><w:r><w:t>{escape(v[1])}</w:t></w:r></w:p></w:tc>")
        return f"<w:tc><w:p><w:r><w:t>{escape(v)}</w:t></w:r></w:p></w:tc>"
    tbl = "<w:tbl>" + "".join("<w:tr>" + "".join(cell(c) for c in r) + "</w:tr>" for r in rows) + "</w:tbl>"
    doc = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document xmlns:w="{_W}"><w:body>'
           f"<w:p><w:r><w:t>{escape(para)}</w:t></w:r></w:p><w:p/>{tbl}<w:sectPr/></w:body></w:document>")
    ctypes = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
              '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
              '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
              '<Default Extension="xml" ContentType="application/xml"/>'
              '<Override PartName="/word/document.xml" '
              'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>')
    rels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/'
            'officeDocument" Target="word/document.xml"/></Relationships>')
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", ctypes)
        z.writestr("_rels/.rels", rels)
        z.writestr("word/document.xml", doc)


def selftest() -> int:
    import ast
    import contextlib
    import io
    import tempfile

    ver = Path(__file__).stem.rsplit("_", 1)[-1]
    res: list[bool] = []

    def chk(label: str, cond, detail: str = "") -> None:
        res.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {label}{(' · ' + detail) if detail else ''}", flush=True)

    print(f"=== {STEM} {ver} 自測(前版本體 {PRIOR_PATH.name})===")
    try:
        ast.parse(PRIOR_PATH.read_text(encoding="utf-8"))
        chk("前版本體語法樹可讀", True, PRIOR_PATH.name)
    except SyntaxError as exc:
        chk("前版本體語法樹可讀", False, f"{type(exc).__name__}: {exc}")
        return _tally(ver, res)
    try:
        b = _body()
        chk("前版本體可載入", True)
    except Exception as exc:
        chk("前版本體可載入", False, f"{type(exc).__name__}: {exc}")
        return _tally(ver, res)
    funcs = ("precheck_zip", "flatten_cell", "strip_ghost", "extract_builtin_xml", "extract_docx",
             "clean_text", "repair_table", "validate_table", "compare_docs", "main")
    lost = [n for n in funcs if not callable(getattr(b, n, None))]
    chk("十個公開函式俱在且可呼叫", not lost, ("缺:" + ",".join(lost)) if lost else f"{len(funcs)} 函式")
    for m in ("docx2python", "docx"):
        if importlib.util.find_spec(m) is None:
            print(f"  [註] 選配梯 {m} 未裝——本體設計即退內建 XML 末梯(永不空手),不算缺件")
    has_pd = importlib.util.find_spec("pandas") is not None

    # 純函式
    chk("E4 巢狀攤平:['a',['b',['c','']]] → a/b/c 三行",
        b.flatten_cell(["a", ["b", ["c", ""]]]) == "a\nb\nc" and b.flatten_cell(7) == "7")
    chk("E7 去幽靈:全形 ＡＢ + 零寬 → AB", b.strip_ghost("Ａ​Ｂ﻿") == "AB")
    ct = b.clean_text("  x\t y\n\n\nz ----media/image1.png---- ")
    chk("修復三式 clean_text:空白收斂 · 空行壓縮 · 圖片佔位清除", ct == "x y\nz", repr(ct))

    saved_argv = sys.argv[:]
    try:
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            sigs = {"ok.docx": b"PK\x03\x04rest", "old.docx": b"\xd0\xcf\x11\xe0rest",
                    "pdf.docx": b"%PDF-1.7", "junk.docx": b"JUNK"}
            for n, raw in sigs.items():
                (tdp / n).write_bytes(raw)
            pre = {n: b.precheck_zip(tdp / n) for n in sigs}
            chk("E1 簽章預檢:PK 放行 · OLE2/PDF/未知 三種偽裝各自誠實判",
                pre["ok.docx"] is None and "OLE2" in (pre["old.docx"] or "")
                and "PDF" in (pre["pdf.docx"] or "") and (pre["junk.docx"] or "").startswith("NOT_DOCX_ZIP:未知簽章"),
                " / ".join(str(v)[:18] for v in pre.values()))

            old, new = tdp / "old_real.docx", tdp / "new_real.docx"
            rows = [["項次", "名稱"], [("v", "1"), "A"], [None, "B"]]
            _selftest_make_docx(old, "甲乙丙", rows)
            _selftest_make_docx(new, "甲乙丁", rows)
            paras, tables, eng = b.extract_builtin_xml(old)
            chk("內建 XML 末梯:段落 + 表格 + vMerge 續格留空",
                (paras, tables, eng) == (["甲乙丙"], [[["項次", "名稱"], ["1", "A"], ["", "B"]]], "builtin_xml"),
                repr((paras, tables, eng)))
            p2, t2, e2 = b.extract_docx(old)
            flat = "\n".join(p2) + "\n" + "\n".join(str(c) for t in t2 for r in t for c in r)
            chk("擷取梯 extract_docx:引擎屬三梯之一且內容讀得到",
                e2 in ("docx2python", "python-docx", "builtin_xml") and "甲乙丙" in flat and "名稱" in flat
                and (e2 != "builtin_xml" or (p2, t2) == (paras, tables)), f"引擎={e2}")

            tb, notes = b.repair_table(tables[0])
            if has_pd:
                got = (list(tb.columns), tb.values.tolist())
                chk("repair_table:ffill 補回合併格 · 首列升表頭",
                    got == (["項次", "名稱"], [["1", "A"], ["1", "B"]])
                    and any("ffill 填補 1 格" in x for x in notes) and "首列升表頭" in notes, f"{got} {notes}")
            else:
                chk("repair_table(pandas 缺退路):純 python ffill",
                    tb == [["項次", "名稱"], ["1", "A"], ["1", "B"]] and any("填補 1 格" in x for x in notes), repr(tb))
            v = b.validate_table(tb)
            want_v = {"rows": 2, "cols": 2, "empty_rate": 0.0} if has_pd else {"rows": 3, "cols": 2, "empty_rate": 0.0}
            chk("validate_table:列/欄/空值率", v == want_v, repr(v))
            v2 = b.validate_table([["a", ""], ["", ""]])
            chk("validate_table(list):空值率 3/4 = 0.75", v2 == {"rows": 2, "cols": 2, "empty_rate": 0.75}, repr(v2))

            buf = io.StringIO()
            sys.argv = [str(PRIOR_PATH), "--compare", str(old), str(new)]
            with contextlib.redirect_stdout(buf):
                rc = b.main()
            out = buf.getvalue()
            chk("main --compare:文字差 2 行 · 表格配對 1 組且一致",
                rc == 0 and "文字層 diff(2 行差異)" in out and "配對 1 組" in out and "表1:一致" in out,
                f"rc={rc}")

            buf = io.StringIO()
            sys.argv = [str(PRIOR_PATH)]
            with contextlib.redirect_stdout(buf):
                rc = b.main()
            chk("無參數:印說明並回 2", rc == 2 and "DOCX" in buf.getvalue(), f"rc={rc}")
    finally:
        sys.argv = saved_argv
    return _tally(ver, res)


def _tally(ver: str, res: list) -> int:
    k, n = sum(res), len(res)
    passed = bool(res) and all(res)
    print(f"  [計] {STEM} {ver} 自測 {k}/{n} · {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
