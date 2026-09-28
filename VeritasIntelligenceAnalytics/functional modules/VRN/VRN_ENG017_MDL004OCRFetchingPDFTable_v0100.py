#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_ENG017_MDL004OCRFetchingPDFTable v0100 — 薄尾:補 --selftest 門(VRN 鏈跑器量得到;正常執行一字不變)
自測查:本體檔在、語法樹可解析;`__all__` 宣告的名字在本體頂層都有定義,入口類別
VRN_MDL004_OCRFetcher.run 與 __main__ 區塊都在;本體可安全載入(重庫 fitz/pdfplumber/paddle… 皆為探針式,
缺了只是 None;在暫存夾內進行,零網路零寫檔);再用合成輸入實跑修復庫純函式
`_clean_number` / F10 / F11 / F12 / F13 / F14 / `find_real_header_row`(有 pandas 時加 F06)。
無版號原檔 VRN_ENG017_MDL004OCRFetchingPDFTable.py 原封不動留作歷史(L04);本檔只是薄尾轉接。
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

import __future__ as _fut
import ast
import importlib.util
import os
import re
import runpy
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
STEM = Path(__file__).stem.rsplit("_v", 1)[0]
BODY = HERE / (STEM + ".py")          # 本體 = 同夾無版號原檔(不釘版號)
_BODY_MOD = None
_NO_FORWARD = {"__path__", "__wrapped__"}


def _load_body():
    """惰性載入本體(本體頂層會探 fitz/pdfplumber/camelot/paddleocr/docling 等重庫,故不在 import 本尾時就載)。"""
    global _BODY_MOD
    if _BODY_MOD is None:
        name = "_via_body_" + STEM
        spec = importlib.util.spec_from_file_location(name, str(BODY))
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        try:
            spec.loader.exec_module(mod)
        except BaseException:
            sys.modules.pop(name, None)
            raise
        _BODY_MOD = mod
    return _BODY_MOD


def __getattr__(name: str):
    """PEP 562:本尾沒有的名字一律轉給本體(惰性載入)。"""
    if name in _NO_FORWARD:
        raise AttributeError(name)
    return getattr(_load_body(), name)


def _run_normal() -> None:
    """正常執行:原檔 __main__ 區塊是就地寫的(argparse → VRN_MDL004_OCRFetcher(cfg).run()),
    所以原樣以 __main__ 身分跑本體,sys.argv 不動。"""
    runpy.run_path(str(BODY), run_name="__main__")


def _isolated(tree: ast.Module, names: set, ns: dict) -> dict:
    """從本體語法樹只抽出指定的頂層定義,在隔離命名空間 exec(不跑本體其餘任何一行)。"""
    picked = []
    for nd in tree.body:
        if isinstance(nd, (ast.FunctionDef, ast.ClassDef)) and nd.name in names:
            picked.append(nd)
        elif isinstance(nd, ast.Assign) and any(isinstance(t, ast.Name) and t.id in names for t in nd.targets):
            picked.append(nd)
        elif isinstance(nd, ast.AnnAssign) and isinstance(nd.target, ast.Name) and nd.target.id in names:
            picked.append(nd)
    code = compile(ast.Module(body=picked, type_ignores=[]), str(BODY) + "#isolated", "exec",
                   flags=_fut.annotations.compiler_flag, dont_inherit=True)
    exec(code, ns)
    return ns


_PURE = {"_PARAMS", "_P", "_BRACKET_RE", "_ZH_SP_RE", "_OCR_NUM_RE", "_PERIOD_RE",
         "_clean_number", "fix_F10_empty_row_drop", "fix_F11_zh_space", "fix_F12_ocr_alphanum",
         "fix_F13_trim_nbsp", "fix_F14_currency_bracket", "find_real_header_row"}


def _top_names(tree: ast.Module) -> set:
    out = set()
    for nd in tree.body:
        if isinstance(nd, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            out.add(nd.name)
        elif isinstance(nd, ast.Assign):
            out.update(t.id for t in nd.targets if isinstance(t, ast.Name))
        elif isinstance(nd, ast.AnnAssign) and isinstance(nd.target, ast.Name):
            out.add(nd.target.id)
    return out


def _selftest() -> int:
    sys.dont_write_bytecode = True
    marks: list = []

    def chk(name: str, ok: bool, note: str = "") -> None:
        marks.append(bool(ok))
        print(f"  [{'OK' if ok else 'FAIL'}] {name}" + (f" — {note}" if note else ""), flush=True)

    print(f"=== {STEM} v0100 自測(本體 {BODY.name})===", flush=True)
    # ① 本體在、語法樹可解析
    tree = None
    try:
        tree = ast.parse(BODY.read_text(encoding="utf-8"), filename=str(BODY))
        chk("本體檔在且語法樹可解析", True, BODY.name)
    except (OSError, SyntaxError) as exc:
        chk("本體檔在且語法樹可解析", False, f"{type(exc).__name__}: {exc}")
    if tree is None:
        print(f"  [計] {STEM} v0100 自測 {sum(marks)}/{len(marks)} · FAIL", flush=True)
        return 1

    # ② 入口與公開 API(語法樹層,不必載入)
    tops = _top_names(tree)
    declared: list = []
    for nd in tree.body:
        if isinstance(nd, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "__all__" for t in nd.targets):
            declared = [e.value for e in getattr(nd.value, "elts", []) if isinstance(e, ast.Constant)]
    undefined = [x for x in declared if x not in tops]
    chk("語法樹:__all__ 宣告的名字在本體頂層都有定義", bool(declared) and not undefined,
        f"宣告 {len(declared)} 個" + (f",缺 {undefined}" if undefined else ""))
    cls = next((n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "VRN_MDL004_OCRFetcher"), None)
    meths = {n.name for n in cls.body if isinstance(n, ast.FunctionDef)} if cls else set()
    main_calls = set()
    for nd in tree.body:
        if isinstance(nd, ast.If) and "__main__" in ast.dump(nd.test):
            main_calls = {c.func.id for c in ast.walk(nd) if isinstance(c, ast.Call) and isinstance(c.func, ast.Name)}
    chk("語法樹:入口 VRN_MDL004_OCRFetcher.run 在,且原檔 __main__ 建它",
        {"__init__", "run"} <= meths and "VRN_MDL004_OCRFetcher" in main_calls,
        f"方法 {sorted(meths)} · __main__ 呼叫含 VRN_MDL004_OCRFetcher={'VRN_MDL004_OCRFetcher' in main_calls}")

    # ③ 安全載入本體(暫存夾當工作目錄;本體頂層重庫全走探針,零網路零寫檔)
    mod = None
    old_cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as td:
        os.chdir(td)
        try:
            mod = _load_body()
            caps = getattr(mod, "_CAP", {}) or {}
            have = sorted(k for k, v in caps.items() if v)
            lack = sorted(k for k, v in caps.items() if not v)
            chk("本體可載入且入口類別在", hasattr(mod, "VRN_MDL004_OCRFetcher"),
                f"__version__={getattr(mod, '__version__', '?')}")
            print(f"  [記] 本機可用引擎/庫 {have};缺 {lack}(本體探針式載入,缺件≠壞掉 L16)", flush=True)
        except ModuleNotFoundError as exc:
            missing = exc.name or str(exc)
            print(f"  ModuleNotFoundError: No module named '{missing}'", flush=True)
            print(f"  [略] 載入本體需要 {missing}(缺件≠壞掉 L16);下列功能檢改走隔離命名空間", flush=True)
        except Exception as exc:
            chk("本體可載入且入口類別在", False, f"{type(exc).__name__}: {str(exc)[:160]}")
        finally:
            os.chdir(old_cwd)

    # ④ 功能檢:合成輸入 → 讀碼推得的期望值(引擎本身要真 PDF + 重庫,不在此跑)
    if mod is not None:
        ns = vars(mod)
        how = "已載入本體"
    else:
        ns = _isolated(tree, _PURE, {"re": re})
        how = "隔離命名空間 exec 抽出原始碼(本體未載入)"
    cn = ns["_clean_number"]
    got = (cn("(1,234)"), cn("12.5%"), cn("N/A"), cn("O5"), cn("abc"))
    chk(f"_clean_number 括號負數/百分比/缺值/OCR O→0/非數({how})",
        got == (-1234.0, 12.5, None, 5.0, None), repr(got))
    got = ns["fix_F14_currency_bracket"]("$(1,234)")
    chk(f"F14 $(1,234) → -1,234({how})", got == "-1,234", repr(got))
    got = ns["fix_F10_empty_row_drop"]([["a", "b"], ["", None], [" ", ""]])
    chk(f"F10 丟全空列({how})", got == ([["a", "b"]], True), repr(got))
    got = ns["fix_F11_zh_space"](" 台 積 電 營收 ")
    chk(f"F11 去中文字間空白({how})", got == "台積電營收", repr(got))
    got = (ns["fix_F12_ocr_alphanum"]("l23"), ns["fix_F12_ocr_alphanum"]("12O"))
    chk(f"F12 OCR l→1 / O→0({how})", got == ("123", "120"), repr(got))
    got = ns["fix_F13_trim_nbsp"]("  12　\n")
    chk(f"F13 NBSP/全形空白修剪({how})", got == "12", repr(got))
    rows = [["說明", "備註"], ["科目", "2023A", "2024E", "2025F"], ["營收", "100", "120", "130"]]
    got = ns["find_real_header_row"](rows)
    chk(f"find_real_header_row 找到期別列({how})", got == 1, f"idx={got}")
    if mod is not None and (getattr(mod, "_CAP", {}) or {}).get("pandas"):
        got = mod.fix_F06_rowspan_ffill([["A", "1"], ["", "2"]])
        chk("F06 垂直合併格往下補(pandas)", got == ([["A", "1"], ["A", "2"]], True), repr(got))
    else:
        print("  [略] F06 垂直合併格往下補需要 pandas 與已載入本體(缺件≠壞掉 L16)", flush=True)

    k, n = sum(marks), len(marks)
    ok = k == n
    print(f"  [計] {STEM} v0100 自測 {k}/{n} · {'PASS' if ok else 'FAIL'}", flush=True)
    return 0 if ok else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv[1:]:
        sys.exit(_selftest())
    _run_normal()
