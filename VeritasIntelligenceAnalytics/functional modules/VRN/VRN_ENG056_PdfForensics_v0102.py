#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_ENG056_PdfForensics v0101 — 薄尾:補 --selftest 門(VRN 鏈跑器量得到;正常執行一字不變)
自測項:前版本體語法樹可讀、可載入;forensics / main 在且可呼叫,REMEDY 六判決齊備;
暫存夾合成檔實測判決:不存在→MISSING、偽副檔名→NOT_PDF;有 fitz 時再以 fitz 現做
文字頁→OK_TEXT、純影像頁→IMAGE_ONLY_SCAN、空白頁→CORRUPT_STRUCTURE,並跑 main --file 全流程。
缺 fitz 即印原 ModuleNotFoundError 並記 NODATA(缺件≠壞掉 L16),rc=2;不假綠。
前版原封不動留作版史(L04);本檔以 glob 取前版(不釘版號),以 PEP 562 __getattr__ 轉接舊公開面。
"""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0111] 最新有版號的正本加速器(動態取最高 VeritasCeleritas_v####;退回鎖版 v1141)· 正本網路工具 VeritasAegisNexus_v1652(找不到 = 不改任何行為) =====
import importlib as _cb_il
import re as _cb_re
import sys as _cb_sys
from pathlib import Path as _cb_Path
_ACCEL, _ACCEL_VER = None, ""
_cb_p = _cb_Path(__file__).resolve()
while _cb_p.parent != _cb_p:
    if (_cb_p / "supportive modules").is_dir():
        _cb_sup = _cb_p / "supportive modules"
        _cb_c = sorted(list(_cb_sup.glob("VeritasCeleritas_v[0-9][0-9][0-9][0-9].py")) + list(_cb_sup.glob("*/VeritasCeleritas_v[0-9][0-9][0-9][0-9].py")),
                       key=lambda x: int(_cb_re.search(r"_v(\d{4})", x.name).group(1)))
        for _cb_d in [str(_cb_sup)] + ([str(_cb_c[-1].parent)] if _cb_c else []) + [str(x.parent) for x in list(_cb_sup.glob("*/VeritasAegisNexus_v1652.py"))[:1]]:
            if _cb_d not in _cb_sys.path:
                _cb_sys.path.insert(0, _cb_d)
        if _cb_c:
            try:
                _ACCEL, _ACCEL_VER = _cb_il.import_module(_cb_c[-1].stem), _cb_c[-1].stem
            except Exception:  # noqa: BLE001
                _ACCEL = None
        break
    _cb_p = _cb_p.parent
if _ACCEL is None:
    try:
        import VeritasCeleritas_v1141 as _ACCEL  # noqa: F401  退回鎖版
        _ACCEL_VER = "VeritasCeleritas_v1141"
    except Exception:  # noqa: BLE001
        _ACCEL = None


def _net():
    """正本網路工具(只在需要出網時載入;本引擎不出網)。"""
    try:
        import VeritasAegisNexus_v1652 as _NET  # noqa: WPS433
        return _NET
    except Exception:  # noqa: BLE001
        return None
# ===== [VIA:ACCEL-BRIDGE:END] =====
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
STEM = "VRN_ENG056_PdfForensics"
PRIOR_PATH = [p for p in sorted(HERE.glob(STEM + "_v*.py")) if p.name < Path(__file__).name][-1]

_BODY = None


def _body():
    """惰性載入前版本體(本體頂層只有 import/HERE/函式/REMEDY;fitz 在函式內才載,載入零副作用)。"""
    global _BODY
    if _BODY is None:
        spec = importlib.util.spec_from_file_location("_" + STEM + "_body", PRIOR_PATH)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = mod
        spec.loader.exec_module(mod)
        _BODY = mod
    return _BODY


def __getattr__(name):
    """PEP 562:舊公開面(forensics / REMEDY / main / HERE)一律轉接前版本體。"""
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(_body(), name)


def main() -> int:
    """正常執行=前版 main 原樣(同一個 sys.argv);--selftest 先攔。"""
    if "--selftest" in sys.argv[1:]:
        return selftest()
    return _body().main()


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
        ast.parse(PRIOR_PATH.read_text(encoding="utf-8"))
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
    verdicts = {"OK_TEXT", "IMAGE_ONLY_SCAN", "ENCRYPTED", "CORRUPT_STRUCTURE", "NOT_PDF", "MISSING"}
    chk("forensics / main 可呼叫 · REMEDY 六判決齊備",
        callable(getattr(b, "forensics", None)) and callable(getattr(b, "main", None))
        and set(getattr(b, "REMEDY", {})) == verdicts)

    fitz = None
    try:
        fitz = importlib.import_module("fitz")
    except ImportError as exc:                     # 沒裝 = ModuleNotFoundError;裝了但載不起來(DLL 壞)= ImportError,都照實缺件
        name = getattr(exc, "name", None) or "fitz"
        print(f"  ModuleNotFoundError: No module named '{name}'" if isinstance(exc, ModuleNotFoundError) else f"  {type(exc).__name__}: {exc}")
        print(f"  NODATA 缺件 {name}(缺件≠壞掉 L16)")
        missing.append(name)
    if importlib.util.find_spec("pdfplumber") is None:
        print("  [註] pdfplumber 未裝——只在 fitz 缺席時當後備路;fitz 在時不影響判決")

    saved_argv = sys.argv[:]
    try:
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            r = b.forensics(tdp / "nope.pdf")
            chk("不存在的檔 → MISSING", r["verdict"] == "MISSING" and r["layers"][0]["ok"] is False, r["verdict"])
            fake = tdp / "fake.pdf"
            fake.write_bytes(b"PK\x03\x04 not a pdf at all")
            r = b.forensics(fake)
            chk("偽副檔名(zip 簽章)→ NOT_PDF", r["verdict"] == "NOT_PDF" and len(r["layers"]) == 1, r["verdict"])

            if fitz is not None:
                txt, img, blank = tdp / "text.pdf", tdp / "scan.pdf", tdp / "blank.pdf"
                d = fitz.open()
                d.new_page().insert_text((72, 72), "VRN selftest 2330")
                d.save(str(txt))
                d.close()
                d = fitz.open()
                pg = d.new_page()
                pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 16, 16), False)
                pix.clear_with(200)
                pg.insert_image(fitz.Rect(72, 72, 172, 172), pixmap=pix)
                d.save(str(img))
                d.close()
                d = fitz.open()
                d.new_page()
                d.save(str(blank))
                d.close()
                got = tuple(b.forensics(p)["verdict"] for p in (txt, img, blank))
                chk("fitz 現做三檔:文字頁 OK_TEXT · 純影像頁 IMAGE_ONLY_SCAN · 空白頁 CORRUPT_STRUCTURE",
                    got == ("OK_TEXT", "IMAGE_ONLY_SCAN", "CORRUPT_STRUCTURE"), repr(got))
                r = b.forensics(txt)
                f1 = r["layers"][0]
                chk("F1 檔案層:%PDF- 簽章與 %%EOF 都認得", f1["ok"] and "EOF標記=有" in f1["note"], f1["note"])

                buf = io.StringIO()
                sys.argv = [str(PRIOR_PATH), "--file", str(txt)]
                with contextlib.redirect_stdout(buf):
                    rc = b.main()
                chk("main --file 文字檔:印判決 OK_TEXT 並回 0", rc == 0 and "[判決] OK_TEXT" in buf.getvalue(), f"rc={rc}")
                buf = io.StringIO()
                sys.argv = [str(PRIOR_PATH), "--file", str(img)]
                with contextlib.redirect_stdout(buf):
                    rc = b.main()
                chk("main --file 掃描件:非 OK_TEXT 回 1", rc == 1 and "IMAGE_ONLY_SCAN" in buf.getvalue(), f"rc={rc}")

            buf = io.StringIO()
            sys.argv = [str(PRIOR_PATH)]
            with contextlib.redirect_stdout(buf):
                rc = b.main()
            chk("無參數:印說明並回 2", rc == 2 and "法醫" in buf.getvalue(), f"rc={rc}")
    finally:
        sys.argv = saved_argv
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
