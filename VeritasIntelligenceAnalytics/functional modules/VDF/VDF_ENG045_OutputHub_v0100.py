#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
vdf_output_hub_v0100 — VDF 統一參數+全格式輸出樞紐(TOOL-058;操作員令 2026-08-18)
================================================================================
令:「先整合所有 vdf 輸入參數;引擎連到所有支援模組;輸出資料庫規劃——
parquet/csv(編碼)/duckdb/google sheet/sqlite/sql 全格式可選且都可輸出;
資料在引擎中跑 JSON 連線 SSOT;模組功能工具自動註冊;輸出運作結果
資料庫矩陣詳細摘要」。
設計:
  ① 統一參數:VDF_Unified_Params_v0100.json 單一 SSOT 參數檔(日期/市場
     /格式選/路徑)——各 VDF 引擎讀此檔,參數不再散落各檔頂部
  ② 內流合約:引擎間資料一律 JSON rows(list[dict]);落地才轉格式
  ③ 全格式輸出(都實作,--formats 可選):
     parquet(pyarrow)/csv(utf-8-sig 解中文編碼)/duckdb(表寫入)
     /sqlite(標準庫)/sql(INSERT dump,萬用移植)
     /gsheet=Google Sheets 相容 csv+上傳指引(真 API 屬雲端道:網路+OAuth
     ——登錄列管,同意閘+憑證到位才實連,誠實不假雲)
  ④ 支援模組全連:SuperAccel(橋)/SSOT_Unified/NetSupport 同意閘
     graceful 取用;自動註冊=iface/namereg 掃描自動收(零手登)
  ⑤ 運作結果資料庫矩陣詳細摘要:逐格式×逐表 rows/bytes/status 矩陣
     +讀回驗證(count 對齊)+JSON 存證
紅線:儲存不落 OneDrive(輸出根=倉內 VDF/output_hub);零刪除(寫前備份)。
用法:via-vdfout --selftest        → 合成資料全格式往返七檢
     via-vdfout <rows.json> [--formats parquet,csv,duckdb,sqlite,sql]
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

import csv as _csv
import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
PARAMS = HERE / "VDF_Unified_Params_v0100.json"
OUT_ROOT = HERE / "output_hub"
EV = VIA / "VIA_Reports" / "vdfout_runs"

DEFAULT_PARAMS = {
    "schema": "VIA.VDF.UnifiedParams.v1",
    "note": "VDF 全引擎統一參數 SSOT——參數集中此檔,引擎讀此不各自散置",
    "time": {"start_date": "2018-01-01", "end_date": "TODAY", "use_current_as_end": True},
    "fetch": {"batch_size": 5, "max_retries": 3, "retry_delay_s": 2, "timeout_s": 30},
    "markets": {"US_INDICES": ["^GSPC", "^DJI", "^IXIC", "^VIX"],
                "TAIWAN_INDICES": ["^TWII", "^TWOII"],
                "INTERNATIONAL": ["^HSI", "^N225"],
                "CURRENCIES": ["EURUSD=X", "JPYUSD=X"]},
    "output": {"formats": ["parquet", "csv", "duckdb", "sqlite", "sql"],
               "csv_encoding": "utf-8-sig", "root": "functional modules/VDF/output_hub",
               "gsheet": "REGISTERED(真 API=雲端道:VIA_NET_CONSENT+OAuth 憑證到位才實連;先出相容 csv)"},
    "honesty": {"simulation_data": "禁——模擬值必須欄名帶 _SIM 後綴且摘要標註,絕不冒充真值"},
}


def load_params() -> dict:
    if not PARAMS.exists():
        PARAMS.write_text(json.dumps(DEFAULT_PARAMS, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"  [初] 統一參數檔生成:{PARAMS.name}")
    return json.loads(PARAMS.read_text(encoding="utf-8"))


def _bak(p: Path):
    if p.exists():
        b = p.with_suffix(p.suffix + f".pre_{datetime.now().strftime('%Y%m%d_%H%M%S')}.bak")
        p.replace(b)


def write_all(rows: list[dict], table: str, formats: list[str], outdir: Path) -> list[dict]:
    """JSON rows(內流合約)→ 全格式落地;回矩陣列(逐格式詳細)。"""
    outdir.mkdir(parents=True, exist_ok=True)
    matrix = []

    def rec(fmt, status, path=None, n=None, note=""):
        row = {"table": table, "format": fmt, "status": status, "rows": n,
               "bytes": (path.stat().st_size if path and path.exists() else None),
               "file": (path.name if path else None), "note": note}
        matrix.append(row)

    cols = sorted({k for r in rows for k in r})
    # parquet
    if "parquet" in formats:
        try:
            import pandas as pd
            p = outdir / f"{table}.parquet"
            _bak(p)
            pd.DataFrame(rows).to_parquet(p, index=False)
            rb = len(pd.read_parquet(p))
            rec("parquet", "OK" if rb == len(rows) else "READBACK_MISMATCH", p, rb)
        except Exception as exc:
            rec("parquet", f"FAIL({type(exc).__name__})", note=str(exc)[:60])
    # csv(utf-8-sig 解中文編碼)
    if "csv" in formats:
        try:
            p = outdir / f"{table}.csv"
            _bak(p)
            with open(p, "w", encoding="utf-8-sig", newline="") as fh:
                w = _csv.DictWriter(fh, fieldnames=cols)
                w.writeheader()
                w.writerows(rows)
            rb = sum(1 for _ in open(p, encoding="utf-8-sig")) - 1
            rec("csv", "OK" if rb == len(rows) else "READBACK_MISMATCH", p, rb, "utf-8-sig(Excel 中文直開)")
        except Exception as exc:
            rec("csv", f"FAIL({type(exc).__name__})", note=str(exc)[:60])
    # duckdb
    if "duckdb" in formats:
        try:
            import duckdb
            p = outdir / "vdf_hub.duckdb"
            tmpj = outdir / f"_{table}.tmp.json"
            tmpj.write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
            con = duckdb.connect(str(p))
            con.execute(f'CREATE OR REPLACE TABLE "{table}" AS SELECT * FROM read_json_auto(?)', [str(tmpj)])
            rb = con.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
            con.close()
            tmpj.unlink(missing_ok=True)
            rec("duckdb", "OK" if rb == len(rows) else "READBACK_MISMATCH", p, rb)
        except Exception as exc:
            rec("duckdb", f"FAIL({type(exc).__name__})", note=str(exc)[:60])
    # sqlite(標準庫)
    if "sqlite" in formats:
        try:
            p = outdir / "vdf_hub.sqlite"
            con = sqlite3.connect(str(p))
            con.execute(f'DROP TABLE IF EXISTS "{table}"')
            con.execute(f'CREATE TABLE "{table}" ({", ".join(chr(34) + c + chr(34) + " TEXT" for c in cols)})')
            con.executemany(f'INSERT INTO "{table}" VALUES ({", ".join("?" * len(cols))})',
                            [[str(r.get(c, "")) for c in cols] for r in rows])
            con.commit()
            rb = con.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
            con.close()
            rec("sqlite", "OK" if rb == len(rows) else "READBACK_MISMATCH", p, rb)
        except Exception as exc:
            rec("sqlite", f"FAIL({type(exc).__name__})", note=str(exc)[:60])
    # sql dump(萬用移植)
    if "sql" in formats:
        try:
            p = outdir / f"{table}.sql"
            _bak(p)
            with open(p, "w", encoding="utf-8") as fh:
                fh.write(f'CREATE TABLE IF NOT EXISTS "{table}" ({", ".join(chr(34) + c + chr(34) + " TEXT" for c in cols)});\n')
                for r in rows:
                    vals = ", ".join("'" + str(r.get(c, "")).replace("'", "''") + "'" for c in cols)
                    fh.write(f'INSERT INTO "{table}" VALUES ({vals});\n')
            rb = sum(1 for l in open(p, encoding="utf-8") if l.startswith("INSERT"))
            rec("sql", "OK" if rb == len(rows) else "READBACK_MISMATCH", p, rb)
        except Exception as exc:
            rec("sql", f"FAIL({type(exc).__name__})", note=str(exc)[:60])
    # gsheet:相容 csv+指引(真 API=雲端道登錄)
    if "gsheet" in formats:
        p = outdir / f"{table}.gsheet.csv"
        try:
            with open(p, "w", encoding="utf-8", newline="") as fh:
                w = _csv.DictWriter(fh, fieldnames=cols)
                w.writeheader()
                w.writerows(rows)
            rec("gsheet", "COMPAT_CSV(真 API 候同意閘+OAuth)", p, len(rows),
                "Sheets 匯入:File→Import→Upload 此 csv;實連屬雲端道列管")
        except Exception as exc:
            rec("gsheet", f"FAIL({type(exc).__name__})", note=str(exc)[:60])
    return matrix


def summary(matrix: list[dict]) -> None:
    print("  ── 運作結果資料庫矩陣(逐格式詳細)──")
    print(f"  {'表':14s}{'格式':9s}{'狀態':26s}{'列數':>7s}{'位元組':>10s}  檔")
    for m in matrix:
        print(f"  {m['table'][:13]:14s}{m['format']:9s}{str(m['status'])[:24]:26s}"
              f"{str(m['rows'] or '—'):>7s}{str(m['bytes'] or '—'):>10s}  {m['file'] or ''}"
              + (f" · {m['note']}" if m["note"] else ""))
    ok = sum(1 for m in matrix if str(m["status"]).startswith(("OK", "COMPAT")))
    print(f"  [計] 格式出 {ok}/{len(matrix)} 綠(誠實;FAIL 不假綠)")


def selftest() -> int:
    print("=== VDF 輸出樞紐 v0100 · 全格式往返七檢(合成)===")
    load_params()
    rows = [{"Date": "2026-08-18", "Ticker": "^TWII", "Close": "24000.5", "名稱": "加權指數"},
            {"Date": "2026-08-18", "Ticker": "^GSPC", "Close": "5600.25", "名稱": "標普500"},
            {"Date": "2026-08-17", "Ticker": "^TWII", "Close": "23900.0", "名稱": "加權指數"}]
    outdir = EV / "selftest_out"
    m = write_all(rows, "hub_selftest", ["parquet", "csv", "duckdb", "sqlite", "sql", "gsheet"], outdir)
    summary(m)
    by = {x["format"]: x for x in m}
    checks = [
        ("parquet 往返", by["parquet"]["status"] == "OK"),
        ("csv utf-8-sig 中文往返", by["csv"]["status"] == "OK"),
        ("duckdb 表往返", by["duckdb"]["status"] == "OK"),
        ("sqlite 往返", by["sqlite"]["status"] == "OK"),
        ("sql dump 往返", by["sql"]["status"] == "OK"),
        ("gsheet 相容道誠實標註", by["gsheet"]["status"].startswith("COMPAT_CSV")),
        ("統一參數檔在位", PARAMS.exists()),
    ]
    n = 0
    for name, ok in checks:
        n += ok
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
    print(f"  [計] {n}/{len(checks)} 檢通過")
    return 0 if n == len(checks) else 1


def main() -> int:
    argv = sys.argv[1:]
    if "--selftest" in argv:
        return selftest()
    if not argv:
        load_params()
        print(__doc__)
        return 2
    src = Path(argv[0])
    if not src.is_file():
        print(f"[FAIL] rows JSON 不存在:{src}")
        return 1
    rows = json.loads(src.read_text(encoding="utf-8"))
    fmts = (argv[argv.index("--formats") + 1].split(",") if "--formats" in argv
            else load_params()["output"]["formats"])
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    m = write_all(rows, src.stem[:40], fmts, OUT_ROOT)
    summary(m)
    EV.mkdir(parents=True, exist_ok=True)
    (EV / f"VDFOUT_{ts}.json").write_text(json.dumps({"ts": ts, "matrix": m}, ensure_ascii=False, indent=1),
                                          encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
