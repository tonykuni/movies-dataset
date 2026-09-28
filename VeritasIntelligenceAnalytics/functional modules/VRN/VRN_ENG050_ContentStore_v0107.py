#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_ENG050_ContentStore v0107 — 薄尾:補 --selftest 門(VRN 鏈跑器量得到;正常執行一字不變)
前版不認 --selftest,旗標被吃掉後照跑預設落庫計畫並回 rc=0(假綠);本尾在任何本體程式碼跑之前先攔下。
自測查:本體(同夾前一版,newest-glob 找)可載入、main/find_db 與 CANON/ONEDRIVE_LEGACY 在位;
find_db 純函式(--db 指定檔在/不在);再把 HERE/CANON/ONEDRIVE_LEGACY 全改指暫存夾,
以暫存 duckdb 實跑 main():缺庫誠實停、--migrate 缺源誠實停、--init 乾跑零建檔、
--init --commit 建 4 新表列數對、再 --commit 冪等不疊加+備份、dry-run 零寫入。前版原檔留作歷史不動(L04)。
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

STEM = "VRN_ENG050_ContentStore"
TAIL_VER = "v0107"
HERE = Path(__file__).resolve().parent
# 尾版律:前一版用 newest-glob 找(比本檔名小的最後一支),不釘版號
PRIOR_PATH = [p for p in sorted(HERE.glob(STEM + "_v*.py")) if p.name < Path(__file__).name][-1]

_BODY = None


def _load_body(fresh: bool = False):
    """載入前版本體為模組(本體頂層只有 find_db/main 定義、路徑常數與加速器橋;duckdb 在 main 內才載)。"""
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
    """PEP 562:匯入端照舊看得到前版整面(main/find_db/CANON/…)。"""
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(_load_body(), name)


def selftest() -> int:
    import contextlib
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

    print(f"=== {STEM} {TAIL_VER} 自測(沙盒零網路;暫存 duckdb;本體={PRIOR_PATH.name})===")
    holder: dict = {}

    def _c_load():
        holder["m"] = _load_body(fresh=True)
        return True, PRIOR_PATH.name

    check("本體載入(前版 newest-glob 定位、import 無副作用)", _c_load)
    body = holder.get("m")
    if body is not None:
        def _c_surface():
            miss = [n for n in ("main", "find_db") if not callable(getattr(body, n, None))]
            miss += [n for n in ("CANON", "ONEDRIVE_LEGACY") if not isinstance(getattr(body, n, None), Path)]
            return not miss, ("缺 " + ",".join(miss)) if miss else "main/find_db 可呼叫 · 路徑常數齊"
        check("公開面:main()、find_db() 與 CANON/ONEDRIVE_LEGACY 在位", _c_surface)

        def _c_find_db():
            with tempfile.TemporaryDirectory() as td:
                gone = Path(td) / "nope.duckdb"
                a = body.find_db(str(gone))
                real = Path(td) / "here.duckdb"
                real.write_bytes(b"")
                b = body.find_db(str(real))
            ok = a == (None, [str(gone)]) and b == (real, [str(real)])
            return ok, f"不在→{a[0]} · 在→{b[0].name if b[0] else None}"
        check("find_db():--db 指定檔不在回 None、在則原樣回傳", _c_find_db)

        def _c_store():
            import duckdb
            saved = (body.HERE, body.CANON, body.ONEDRIVE_LEGACY, list(sys.argv))
            notes: list[str] = []
            oks: list[bool] = []

            def run(*flags: str) -> tuple[int, str]:
                sys.argv = [str(PRIOR_PATH), *flags]
                buf = io.StringIO()
                with contextlib.redirect_stdout(buf):
                    rc = body.main()
                return rc, buf.getvalue()

            def counts(db: Path) -> dict:
                con = duckdb.connect(str(db), read_only=True)
                try:
                    got = {t: con.execute(f"select count(*) from {t}").fetchone()[0]
                           for t in ("vrn_report_content_canon", "vrn_report_text_blocks",
                                     "vrn_report_table_cells", "vrn_store_log")}
                    got["broker_A"] = con.execute("select broker from vrn_report_content_canon "
                                                  "where source_document='A.pdf'").fetchone()[0]
                    got["tick_A"] = con.execute("select primary_tickers from vrn_report_content_canon "
                                                "where source_document='A.pdf'").fetchone()[0]
                    got["actions"] = [r[0] for r in con.execute("select action from vrn_store_log").fetchall()]
                    return got
                finally:
                    con.close()

            try:
                with tempfile.TemporaryDirectory() as td:
                    tdp = Path(td)
                    here = tdp / "VRN"
                    body.HERE = here
                    body.CANON = tdp / "canon" / "via.duckdb"
                    body.ONEDRIVE_LEGACY = tdp / "onedrive" / "via.duckdb"
                    recs = [{"source_document": "A.pdf", "record_id": "R1", "broker_guess": "元大",
                             "final_primary_ticker_proposals": ["2330"], "filtered_target_price_proposals": [1200],
                             "review_required": 1},
                            {"source_document": "B.pdf", "record_id": "R2", "final_broker_proposal": "凱基"}]
                    v2 = here / "SSOT/v2/VRN_ResearchReport_SSOT.v2.jsonl"
                    v2.parent.mkdir(parents=True)
                    v2.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in recs), encoding="utf-8")
                    t005 = here / "staging/ocr_out/mdl005_temp/VRN_MDL005_Text.parquet"
                    t004 = here / "staging/ocr_out/mdl004_temp/VRN_MDL004_Tables.parquet"
                    t005.parent.mkdir(parents=True)
                    t004.parent.mkdir(parents=True)
                    mk = duckdb.connect()
                    try:
                        mk.execute(f"copy (select * from (values ('A.pdf','甲'),('A.pdf','乙'),('B.pdf','丙')) "
                                   f"t(pdf_name, text)) to '{t005.as_posix()}' (format parquet)")
                        mk.execute(f"copy (select * from (values ('A.pdf','1'),('B.pdf','2')) "
                                   f"t(pdf_name, value)) to '{t004.as_posix()}' (format parquet)")
                    finally:
                        mk.close()
                    db = tdp / "db" / "via.duckdb"

                    rc, out = run("--db", str(db))
                    oks.append(rc == 1 and not db.exists() and "[FAIL]" in out)
                    notes.append(f"缺庫無 --init rc={rc}")
                    rc, out = run("--migrate")
                    oks.append(rc == 1 and "遷移來源不在" in out)
                    notes.append(f"--migrate 缺源 rc={rc}")
                    rc, out = run("--db", str(db), "--init")
                    oks.append(rc == 0 and not db.exists())
                    notes.append(f"--init 乾跑 rc={rc} 建檔={db.exists()}")
                    rc, out = run("--db", str(db), "--init", "--commit")
                    c1 = counts(db) if db.exists() else {}
                    oks.append(rc == 0 and c1.get("vrn_report_content_canon") == 2
                               and c1.get("vrn_report_text_blocks") == 3 and c1.get("vrn_report_table_cells") == 2
                               and c1.get("actions") == ["FRESH_INIT+STORE_64_CORPUS"]
                               and c1.get("broker_A") == "元大" and c1.get("tick_A") == '["2330"]')
                    notes.append(f"--init --commit rc={rc} canon/text/cells/log="
                                 f"{c1.get('vrn_report_content_canon')}/{c1.get('vrn_report_text_blocks')}/"
                                 f"{c1.get('vrn_report_table_cells')}/{c1.get('vrn_store_log')}")
                    rc, out = run("--db", str(db), "--commit")
                    c2 = counts(db)
                    baks = list(db.parent.glob("via.duckdb.pre_*.bak"))
                    oks.append(rc == 0 and c2["vrn_report_content_canon"] == 2 and c2["vrn_report_text_blocks"] == 3
                               and c2["vrn_report_table_cells"] == 2 and c2["vrn_store_log"] == 2 and len(baks) == 1)
                    notes.append(f"再 --commit rc={rc} 冪等 canon={c2['vrn_report_content_canon']} "
                                 f"text={c2['vrn_report_text_blocks']} log={c2['vrn_store_log']} 備份 {len(baks)}")
                    rc, out = run("--db", str(db))
                    c3 = counts(db)
                    oks.append(rc == 0 and c3["vrn_store_log"] == 2 and "[dry-run]" in out)
                    notes.append(f"dry-run rc={rc} log 仍 {c3['vrn_store_log']}")
            finally:
                body.HERE, body.CANON, body.ONEDRIVE_LEGACY = saved[0], saved[1], saved[2]
                sys.argv = saved[3]
            return all(oks) and len(oks) == 6, " · ".join(notes)
        check("實跑 main()(暫存 duckdb):缺庫停/缺源停/乾跑零建檔/init+commit 落 4 表/再 commit 冪等+備份/dry-run 零寫",
              _c_store)

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
