#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_ENG057_ScanOcrRescue v0105 — 薄尾:補 --selftest 門(VRN 鏈跑器量得到;正常執行一字不變)
自測項:前版本體語法樹可讀、可載入;main 在且可呼叫;無參數印說明回 2;收件夾無匹配誠實回 1(HERE 暫指暫存夾);
main 內巢狀 run_ocr 以語法樹單獨取出,餵假 OCR 物件實測 3.x predict / .json / 2.x ocr 三路解析;
build_ocr 以假 PaddleOCR 實測參數梯次降階;paddleocr 缺件時主流程須誠實停、不寫主表。
缺 paddleocr / fitz / pandas 即印原 ModuleNotFoundError 並記 NODATA(缺件≠壞掉 L16),rc=2;不假綠。
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

import importlib
import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STEM = "VRN_ENG057_ScanOcrRescue"
PRIOR_PATH = [p for p in sorted(HERE.glob(STEM + "_v*.py")) if p.name < Path(__file__).name][-1]

_BODY = None


def _body():
    """惰性載入前版本體(本體頂層只有 import/HERE/main 定義;重庫全在 main 內,載入零副作用)。"""
    global _BODY
    if _BODY is None:
        spec = importlib.util.spec_from_file_location("_" + STEM + "_body", PRIOR_PATH)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = mod
        spec.loader.exec_module(mod)
        _BODY = mod
    return _BODY


def __getattr__(name):
    """PEP 562:舊公開面(main / HERE …)一律轉接前版本體。"""
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(_body(), name)


def main() -> int:
    """正常執行=前版 main 原樣(同一個 sys.argv);--selftest 先攔。"""
    if "--selftest" in sys.argv[1:]:
        return selftest()
    return _body().main()


def _nested_fn(tree, outer: str, inner: str, env: dict):
    """從語法樹取出 outer 函式內的巢狀 inner 函式,單獨編譯到 env(自由變數由 env 供給)。"""
    import ast
    for nd in tree.body:
        if isinstance(nd, ast.FunctionDef) and nd.name == outer:
            for sub in ast.walk(nd):
                if isinstance(sub, ast.FunctionDef) and sub.name == inner:
                    mod = ast.Module(body=[sub], type_ignores=[])
                    exec(compile(mod, str(PRIOR_PATH), "exec"), env)
                    return env[inner]
    return None


def selftest() -> int:
    import ast
    import contextlib
    import io
    import tempfile

    ver = Path(__file__).stem.rsplit("_", 1)[-1]
    res: list[bool] = []
    missing: list[str] = []

    def chk(label: str, cond, detail: str = "") -> None:
        res.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {label}{(' · ' + detail) if detail else ''}", flush=True)

    print(f"=== {STEM} {ver} 自測(前版本體 {PRIOR_PATH.name})===")
    try:
        tree = ast.parse(PRIOR_PATH.read_text(encoding="utf-8"))
        chk("前版本體語法樹可讀", True, PRIOR_PATH.name)
    except SyntaxError as exc:
        chk("前版本體語法樹可讀", False, f"{type(exc).__name__}: {exc}")
        return _tally(ver, res, missing)
    try:
        b = _body()
        chk("前版本體可載入", True)
    except Exception as exc:
        chk("前版本體可載入", False, f"{type(exc).__name__}: {exc}")
        return _tally(ver, res, missing)
    chk("入口 main 在且可呼叫 · HERE 為路徑", callable(getattr(b, "main", None)) and isinstance(getattr(b, "HERE", None), Path))

    # 重庫探針(本體 main 真跑時才 import;缺=ABSENT 不是壞)
    for m in ("fitz", "pandas", "paddleocr"):
        try:
            importlib.import_module(m)
        except ModuleNotFoundError as exc:
            print(f"  {type(exc).__name__}: {exc}")
            print(f"  NODATA 缺件 {exc.name or m}(缺件≠壞掉 L16)")
            missing.append(exc.name or m)
        except Exception as exc:  # 裝了但載不起來(例:paddlex 附屬件被拔)=環境,不是本引擎壞
            print(f"  NODATA {m} 載入失敗 {type(exc).__name__}: {str(exc)[:80]}(環境缺料≠壞掉 L16)")
            missing.append(m)

    saved_argv, saved_here = sys.argv[:], b.HERE
    try:
        # ① 無參數 → 印說明、rc 2
        buf = io.StringIO()
        sys.argv = [str(PRIOR_PATH)]
        with contextlib.redirect_stdout(buf):
            rc = b.main()
        chk("無參數:印說明並回 2", rc == 2 and "OCR" in buf.getvalue(), f"rc={rc}")

        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            (tdp / "input" / "incoming").mkdir(parents=True)
            b.HERE = tdp
            # ② 收件夾無匹配 → rc 1(不碰真收件夾)
            buf = io.StringIO()
            sys.argv = [str(PRIOR_PATH), "NOPE_*.pdf", "--dry-run"]
            with contextlib.redirect_stdout(buf):
                rc = b.main()
            chk("收件夾無匹配:誠實回 1", rc == 1 and "收件夾無匹配" in buf.getvalue(), f"rc={rc}")
            # ③ paddleocr 缺件時主流程須誠實停、不寫主表(有 paddleocr 會真建模型/下載,不跑)
            if "paddleocr" in missing and "fitz" not in missing:
                (tdp / "input" / "incoming" / "scan_x.pdf").write_bytes(b"%PDF-1.4\n%%EOF\n")
                buf = io.StringIO()
                sys.argv = [str(PRIOR_PATH), "scan_*.pdf"]
                with contextlib.redirect_stdout(buf):
                    rc = b.main()
                chk("paddleocr 缺件:主流程誠實停(rc 1)且不寫主表",
                    rc == 1 and "paddleocr 不可用" in buf.getvalue() and not (tdp / "staging").exists(),
                    f"rc={rc}")
    finally:
        sys.argv, b.HERE = saved_argv, saved_here

    # ④ run_ocr 三路解析(巢狀函式單獨取出;假 OCR 物件,零模型)
    run_ocr = _nested_fn(tree, "main", "run_ocr", {"__name__": "_selftest_run_ocr"})
    chk("巢狀 run_ocr 可自語法樹取出", callable(run_ocr))
    if callable(run_ocr):
        class Ocr3:
            def predict(self, image):
                return [{"rec_texts": [" 台積電 ", "", "2330"], "rec_scores": [0.91, 0.5, 0.8]}]

        class JsonRes:
            json = {"res": {"rec_texts": ["法說會"], "rec_scores": [0.7]}}

        class Ocr3Json:
            def predict(self, image):
                return [JsonRes()]

        class Ocr2:
            def ocr(self, image, cls=True):
                box = [[0, 0], [1, 0], [1, 1], [0, 1]]
                return [[[box, ("甲", 0.7)], [box, ("   ", 0.3)], "壞"]]

        got = (run_ocr(Ocr3(), "x.png"), run_ocr(Ocr3Json(), "x.png"), run_ocr(Ocr2(), "x.png"))
        want = ([("台積電", 0.91), ("2330", 0.8)], [("法說會", 0.7)], [("甲", 0.7)])
        chk("run_ocr:3.x rec_texts · .json 退路 · 2.x item[1] 三路解析(空白/壞項剔除)", got == want, repr(got))

    # ⑤ build_ocr 參數梯次(假 PaddleOCR:mobile 參數不吃 → 降到第二梯)
    class FakePaddle:
        def __init__(self, **kw):
            if "use_doc_unwarping" in kw:
                raise TypeError("unexpected keyword")
            self.kw = kw

    build_ocr = _nested_fn(tree, "main", "build_ocr",
                           {"__name__": "_selftest_build_ocr", "server": False, "PaddleOCR": FakePaddle})
    if callable(build_ocr):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            o = build_ocr()
        chk("build_ocr:參數不合即降階(第二梯 textline+ch)",
            getattr(o, "kw", None) == {"use_textline_orientation": True, "lang": "ch"}, repr(getattr(o, "kw", None)))
    else:
        chk("巢狀 build_ocr 可自語法樹取出", False)
    return _tally(ver, res, missing)


def _tally(ver: str, res: list, missing: list) -> int:
    k, n = sum(res), len(res)
    if not (res and all(res)):
        print(f"  [計] {STEM} {ver} 自測 {k}/{n} · FAIL")
        return 1
    if missing:
        print(f"  [計] {STEM} {ver} 自測 {k}/{n} · NODATA(缺件 {','.join(missing)};可跑的檢查全過,缺件部分未量)")
        return 2
    print(f"  [計] {STEM} {ver} 自測 {k}/{n} · PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
