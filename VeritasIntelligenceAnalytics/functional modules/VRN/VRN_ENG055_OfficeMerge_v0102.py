#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_ENG055_OfficeMerge v0102 — 薄尾:補 --selftest 門(VRN 鏈跑器量得到;正常執行一字不變)
前版只認 --commit,其餘旗標一律落入預設動作;本尾在任何本體程式碼跑之前先攔 --selftest。
自測查:本體(同夾前一版,newest-glob 找)可載入、main/INBOX/T004/T005/EXTS 在位且可呼叫;
並在暫存夾放一份合成 CSV,把收件夾與兩張 parquet 路徑改指暫存夾,實跑 main():
dry-run 零寫入 → --commit 落 6 格(他檔舊列保留)→ 再 --commit 冪等不疊加且留備份。
不帶 --selftest 時原封轉交前版 main()(同一 sys.argv);前版原檔留作歷史不動(L04)。
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

STEM = "VRN_ENG055_OfficeMerge"
TAIL_VER = "v0102"
HERE = Path(__file__).resolve().parent
# 尾版律:前一版用 newest-glob 找(比本檔名小的最後一支),不釘版號
PRIOR_PATH = [p for p in sorted(HERE.glob(STEM + "_v*.py")) if p.name < Path(__file__).name][-1]

_BODY = None


def _load_body(fresh: bool = False):
    """載入前版本體為模組(本體頂層只有路徑常數與加速器橋,無印字/寫檔/網路)。"""
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
    """PEP 562:匯入端照舊看得到前版整面(main/INBOX/T004/…)。"""
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(_load_body(), name)


def selftest() -> int:
    import contextlib
    import io
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

    print(f"=== {STEM} {TAIL_VER} 自測(沙盒零網路;本體={PRIOR_PATH.name})===")
    holder: dict = {}

    def _c_load():
        holder["m"] = _load_body(fresh=True)
        return True, PRIOR_PATH.name

    check("本體載入(前版 newest-glob 定位、import 無副作用)", _c_load)
    body = holder.get("m")
    if body is not None:
        def _c_surface():
            need = ("main", "INBOX", "T004", "T005", "SDX", "EXTS")
            miss = [n for n in need if not hasattr(body, n)]
            ok = not miss and callable(body.main)
            return ok, ("缺 " + ",".join(miss)) if miss else "main 可呼叫 · 常數齊"
        check("公開面:main() 與收件夾/主表路徑常數在位", _c_surface)
        check("副檔名白名單 EXTS = {.xlsx,.xls,.csv,.docx}",
              lambda: (body.EXTS == {".xlsx", ".xls", ".csv", ".docx"}, str(sorted(body.EXTS))))

        def _c_merge():
            import pandas as pd
            sys.path.insert(0, str(body.SDX))  # 與本體 main() 同一條載入路
            import superextract.pipeline  # noqa: F401  缺=NODATA,不假綠
            saved = (body.INBOX, body.T004, body.T005, list(sys.argv))
            notes = []
            try:
                with tempfile.TemporaryDirectory() as td:
                    tdp = Path(td)
                    body.INBOX = tdp / "office_in"
                    body.T004 = tdp / "mdl004" / "VRN_MDL004_Tables.parquet"
                    body.T005 = tdp / "mdl005" / "VRN_MDL005_Text.parquet"
                    body.INBOX.mkdir()
                    (body.INBOX / "合成表.csv").write_text("name,qty\n蘋果,3\n香蕉,5\n", encoding="utf-8")
                    body.T004.parent.mkdir()
                    pd.DataFrame([{"pdf_name": "other.pdf", "page_no": 1, "table_no": 1, "row": 0,
                                   "col": 0, "value": "舊", "engine": "x"}]).to_parquet(body.T004, index=False)
                    buf = io.StringIO()
                    sys.argv = [str(PRIOR_PATH)]
                    with contextlib.redirect_stdout(buf):
                        rc_dry = body.main()
                    dry_ok = rc_dry == 0 and len(pd.read_parquet(body.T004)) == 1 and not body.T005.exists()
                    notes.append(f"dry-run rc={rc_dry} 零寫入={'是' if dry_ok else '否'}")
                    sys.argv = [str(PRIOR_PATH), "--commit"]
                    with contextlib.redirect_stdout(buf):
                        rc1 = body.main()
                    df1 = pd.read_parquet(body.T004)
                    mine = df1[df1["pdf_name"] == "合成表.csv"]
                    cell = mine[(mine["row"] == 1) & (mine["col"] == 0)]["value"].tolist()
                    c1 = (rc1 == 0 and len(df1) == 7 and len(mine) == 6 and cell == ["蘋果"]
                          and (df1["pdf_name"] == "other.pdf").sum() == 1
                          and set(mine["engine"]) == {"office_merge"} and not body.T005.exists())
                    notes.append(f"commit#1 rc={rc1} 共 {len(df1)} 列(本件 {len(mine)} 格,r1c0={cell})")
                    with contextlib.redirect_stdout(buf):
                        rc2 = body.main()
                    df2 = pd.read_parquet(body.T004)
                    baks = list(body.T004.parent.glob("*.pre_*.bak.parquet"))
                    c2 = rc2 == 0 and len(df2) == 7 and len(baks) >= 1
                    notes.append(f"commit#2 rc={rc2} 共 {len(df2)} 列 · 備份 {len(baks)} 件")
            finally:
                body.INBOX, body.T004, body.T005 = saved[0], saved[1], saved[2]
                sys.argv = saved[3]
            return dry_ok and c1 and c2, " · ".join(notes)
        check("實跑 main():合成 CSV → dry-run 零寫 / commit 落 6 格保留他檔 / 再 commit 冪等+備份(全在暫存夾)",
              _c_merge)

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
