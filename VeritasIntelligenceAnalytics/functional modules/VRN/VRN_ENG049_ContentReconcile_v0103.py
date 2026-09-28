#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_ENG049_ContentReconcile v0103 — 薄尾:補 --selftest 門(VRN 鏈跑器量得到;正常執行一字不變)
前版每條路都會寫 VIA_Reports 存證,故本尾在任何本體程式碼跑之前先攔 --selftest。
自測查:本體(同夾前一版,newest-glob 找)可載入、main/load_flat/norm 在位且可呼叫;
norm 與 load_flat(缺檔回 None、CSV 退路)的純函式結果;再於暫存夾造合成 SSOT v2 五筆
+ staging(文字/表格/docx_txt)+ 首頁道,改指 HERE/VIA 後實跑 main():五態分佈、GAPS rc=1、
補齊後 COVERED rc=0、存證 json/html 落在暫存夾。前版原檔留作歷史不動(L04)。
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

STEM = "VRN_ENG049_ContentReconcile"
TAIL_VER = "v0103"
HERE = Path(__file__).resolve().parent
# 尾版律:前一版用 newest-glob 找(比本檔名小的最後一支),不釘版號
PRIOR_PATH = [p for p in sorted(HERE.glob(STEM + "_v*.py")) if p.name < Path(__file__).name][-1]

_BODY = None


def _load_body(fresh: bool = False):
    """載入前版本體為模組(本體頂層只有函式定義、路徑常數與加速器橋,無印字/寫檔/網路)。"""
    global _BODY
    if _BODY is not None and not fresh:
        return _BODY
    name = "_" + STEM + "_body" + ("_selftest" if fresh else "")
    spec = importlib.util.spec_from_file_location(name, PRIOR_PATH)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    try:
        spec.loader.exec_module(mod)
    except BaseException:
        sys.modules.pop(name, None)
        raise
    if not fresh:
        _BODY = mod
    return mod


def __getattr__(name: str):
    """PEP 562:匯入端照舊看得到前版整面(main/load_flat/norm/…)。"""
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(_load_body(), name)


def selftest() -> int:
    import contextlib
    import csv
    import io
    import json
    import os
    import tempfile

    os.environ["VIA_SELFTEST"] = "1"
    results: list[bool] = []
    missing: list[str] = []

    def check(label: str, fn) -> None:
        try:
            good, detail = fn()
        except ModuleNotFoundError as exc:
            print(f"  {type(exc).__name__}: {exc}")
            print(f"  NODATA 缺件 {exc.name}(缺件≠壞掉 L16)· 此檢略過:{label}")
            missing.append(str(exc.name))
            return
        except Exception as exc:
            good, detail = False, f"{type(exc).__name__}: {str(exc)[:120]}"
        results.append(bool(good))
        print(f"  [{'OK' if good else 'FAIL'}] {label}" + (f" — {detail}" if detail else ""))

    def write_csv(path: Path, rows: list) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)

    print(f"=== {STEM} {TAIL_VER} 自測(沙盒零網路;本體={PRIOR_PATH.name})===")
    holder: dict = {}

    def _c_load():
        holder["m"] = _load_body(fresh=True)
        return True, PRIOR_PATH.name

    check("本體載入(前版 newest-glob 定位、import 無副作用)", _c_load)
    body = holder.get("m")
    if body is not None:
        def _c_surface():
            need = ("main", "load_flat", "norm")
            miss = [n for n in need if not callable(getattr(body, n, None))]
            return not miss, ("缺 " + ",".join(miss)) if miss else "main/load_flat/norm 皆可呼叫"
        check("公開面:main()、load_flat()、norm() 在位", _c_surface)
        check("norm():去空白轉小寫、None→空字串",
              lambda: (body.norm("  ABC.PDF ") == "abc.pdf" and body.norm(None) == "", "' ABC.PDF '→'abc.pdf'"))

        def _c_load_flat():
            with tempfile.TemporaryDirectory() as td:
                tdp = Path(td)
                none_ok = body.load_flat(tdp, "nothing") is None
                write_csv(tdp / "T.csv", [{"pdf_name": "甲.pdf", "text": "你好"}])
                got = body.load_flat(tdp, "T")
            ok = none_ok and got == [{"pdf_name": "甲.pdf", "text": "你好"}]
            return ok, f"缺檔→None={none_ok} · CSV 退路→{got}"
        check("load_flat():缺檔回 None、無 parquet 走 CSV 退路", _c_load_flat)

        def _c_reconcile():
            saved = (body.HERE, body.VIA, list(sys.argv))
            notes = []
            try:
                with tempfile.TemporaryDirectory() as td:
                    via = Path(td)
                    here = via / "functional modules" / "VRN"
                    body.HERE, body.VIA = here, via
                    recs = [
                        {"source_document": "A.pdf", "target_price_content_guesses": [{"value": 1200.0}]},
                        {"source_document": "B.pdf"},
                        {"source_document": "C.docx"},
                        {"source_document": "D.pdf"},
                        {"source_document": "E.pdf"},
                    ]
                    v2 = here / "SSOT/v2/VRN_ResearchReport_SSOT.v2.jsonl"
                    v2.parent.mkdir(parents=True)
                    v2.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in recs), encoding="utf-8")
                    stg = via / "stg"
                    text_rows = [{"pdf_name": "A.pdf", "text": "目標價 1200 元,維持買進"},
                                 {"pdf_name": "B.pdf", "text": "營收成長"}]
                    write_csv(stg / "mdl005_temp/VRN_MDL005_Text.csv", text_rows)
                    write_csv(stg / "mdl004_temp/VRN_MDL004_Tables.csv", [{"pdf_name": "a.pdf", "value": "1"}])
                    (stg / "docx_txt").mkdir()
                    (stg / "docx_txt/c.txt").write_text("docx", encoding="utf-8")
                    (via / "VIA_Reports/first_page_text").mkdir(parents=True)
                    (via / "VIA_Reports/first_page_text/E.txt").write_text("首頁", encoding="utf-8")
                    sys.argv = [str(PRIOR_PATH), "--staging", str(stg), "--json", "--no-open"]
                    buf = io.StringIO()
                    with contextlib.redirect_stdout(buf):
                        rc1 = body.main()
                    out1 = json.loads(buf.getvalue().strip().splitlines()[-1])
                    want = {"FULL": 1, "TEXT_ONLY": 1, "DOCX_TXT": 1, "NO_EXTRACTION": 1, "FIRSTPAGE": 1}
                    gaps = [g["source_document"] for g in out1.get("gap_diagnostics", [])]
                    runs = sorted((via / "VIA_Reports/vrn_reconcile_runs").glob("reconcile_*.json"))
                    probe = ""
                    if runs:
                        saved_rows = json.loads(runs[-1].read_text(encoding="utf-8"))["rows"]
                        probe = next(r["content_probe"] for r in saved_rows if r["source_document"] == "A.pdf")
                    c1 = (rc1 == 1 and out1["distribution"] == want and out1["verdict"] == "GAPS"
                          and out1["covered"] == 4 and gaps == ["D.pdf"] and probe == "目標價 1/1 在文中尋獲"
                          and len(list((via / "VIA_Reports/vrn_reconcile_runs").glob("reconcile_*.html"))) == 1)
                    notes.append(f"首跑 rc={rc1} {out1['verdict']} 分佈={out1['distribution']} 缺口={gaps} A 探測「{probe}」")
                    text_rows.append({"pdf_name": "D.pdf", "text": "補件"})
                    write_csv(stg / "mdl005_temp/VRN_MDL005_Text.csv", text_rows)
                    buf2 = io.StringIO()
                    with contextlib.redirect_stdout(buf2):
                        rc2 = body.main()
                    out2 = json.loads(buf2.getvalue().strip().splitlines()[-1])
                    c2 = rc2 == 0 and out2["verdict"] == "COVERED" and out2["distribution"].get("TEXT_ONLY") == 2
                    notes.append(f"補 D 後 rc={rc2} {out2['verdict']}")
            finally:
                body.HERE, body.VIA, sys.argv = saved[0], saved[1], saved[2]
            return c1 and c2, " · ".join(notes)
        check("實跑 main():合成 SSOT 五筆 × staging → 五態分佈/GAPS rc=1 → 補件 COVERED rc=0(存證落暫存夾)",
              _c_reconcile)

    n, k = len(results), sum(results)
    if n and k == n and missing:
        print(f"  [計] {STEM} {TAIL_VER} 自測 {k}/{n} · NODATA(缺件 {','.join(missing)};已跑之檢全過,不假綠)")
        return 2
    verdict = "PASS" if n and k == n else "FAIL"
    print(f"  [計] {STEM} {TAIL_VER} 自測 {k}/{n} · {verdict}")
    return 0 if verdict == "PASS" else 1


def main() -> int:
    if "--selftest" in sys.argv[1:]:
        return selftest()
    return _load_body().main()


if __name__ == "__main__":
    sys.exit(main())
