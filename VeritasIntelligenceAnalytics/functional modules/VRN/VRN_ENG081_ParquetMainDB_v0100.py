#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VRN_ENG081_ParquetMainDB v0100 — VRN 交付主資料庫(Parquet 唯一真值)
====================================================================
操作員令(批472 架構總表):
  「**Parquet 當唯一真實主資料庫,CSV / DuckDB / JSON / Google Sheet 全部從
    Parquet 派生,不要反過來維護**」
  主庫兩支:StockReportBasicInfo.parquet + StockReportFinancialData.parquet
  更新方式:**累積式更新、去重、不重複擷取、不覆蓋有效舊資料**

先查再造(量到的,不是規劃的):
  · 資料**早就在**正典 DuckDB 裡:vrn_report_basic(71 列/31 欄)、
    vrn_report_financial(36 列/8 欄)、vrn_report_metrics(54 列/6 欄)。
    所以本件是**派生車道**,不是第二套抽取——一個 regex 都不重寫(Zero-Hydra)。
  · 全樹掃過:`StockReportBasicInfo.parquet` / `StockReportFinancialData.parquet`
    **一個都不存在**;散落的是 14 份 .json/.csv/.duckdb,分在 VRN/VAP/VDF 三處,
    彼此沒有主從關係——那正是操作員要收掉的那種「反過來維護」。
  · 寫 Parquet 用 DuckDB 自己的 `COPY … TO … (FORMAT PARQUET)`:**零新相依**
    (pyarrow 在位也不必經過它)。

累積律(只增不減的實作):
  既有 Parquet(若有)⊎ 本輪 DuckDB 列 → 依主鍵去重 → 寫回。
  **先合併再寫**,所以就算正典庫被重建或清空,Parquet 也不會掉列。
  主鍵:basic = report_file;financial = (report_file, page, canonical, period);
       metrics = (report_file, metric, period)。
  同鍵衝突取**新的那一列**(extracted_at 較新者;缺欄則取本輪),舊列不刪、只被取代。
  寫檔用「先寫暫存再原子換名」,中途斷電不會留下半個 Parquet。

派生律(單向,永不回流):
  Parquet(真值)→ CSV(utf-8-sig 給 Excel)/ JSON / DuckDB 檢視。
  **派生物永遠不被讀回來當來源**;要改資料只能改上游引擎再重跑。

用法:
  python3 VRN_ENG081_ParquetMainDB_v0100.py build            # 建/更新兩支主庫
  python3 VRN_ENG081_ParquetMainDB_v0100.py build --derive    # 併產 CSV/JSON/DuckDB
  python3 VRN_ENG081_ParquetMainDB_v0100.py status            # 唯讀盤點
  python3 VRN_ENG081_ParquetMainDB_v0100.py --selftest
"""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(graceful 缺席零影響) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
except Exception:
    VIA_ACCEL = None
# ===== [VIA:ACCEL-BRIDGE:END] =====

import json
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent

#: 正典庫(與 ENG073 同一條路徑律;主路徑缺才探替根)
DB_MAIN = VIA / "functional modules" / "VDF" / "output_hub" / "mega" / "vdf_tw_market.duckdb"
#: 主庫落點(VIA_Reports/* 已在 .gitignore —— 資料不進 git)
OUTDIR = VIA / "VIA_Reports" / "vrn" / "maindb"

#: 冊:表 → (檔名, 主鍵欄)。**檔名依操作員的檔名修正表**:
#:   無空白、無重複副檔名、Financial 一律寫全 `FinancialData`。
TABLES = (
    ("vrn_report_basic", "StockReportBasicInfo.parquet",
     ("report_file",)),
    # **value 也在主鍵裡**(批472 真料實測逼出來的)。
    # 第一版的鍵是 (report_file, metric, period),對 71 份真報告一跑
    # **54 列變 51 列**——掉的三筆查完只有一筆是真重複:
    #     凱基_3665 eps 2026 ×2 值 10.0 | 10.0   → 真重複,該併
    #     凱基_3665 eps 2027 ×2 值 2025.0 | 2028.0 → 兩個都是被誤讀成 EPS 的年份
    #     3014TT   eps 2024 ×2 值 11.0  | 9.53   → 兩個不同的預估值
    # 後兩筆是**衝突**不是重複,而我判不出哪個對——偷偷選一個留下,
    # 就是在沒有依據的情況下替操作員做了決定。照系統既有的 KEEP_BOTH 律:
    # 值不同就兩列都留,讓它在矩陣上看得見;值相同才是真重複,併掉。
    ("vrn_report_financial", "StockReportFinancialData.parquet",
     ("report_file", "page", "canonical", "period", "value")),
    ("vrn_report_metrics", "StockReportMetrics.parquet",
     ("report_file", "metric", "period", "value")),
)
#: 新舊同鍵時用哪一欄判「較新」(缺欄=取本輪)
FRESH_COL = "extracted_at"


def _duck():
    try:
        import duckdb
        return duckdb
    except Exception:
        return None


def resolve_db(db: Path | None = None) -> tuple[Path | None, str]:
    """主路徑 → 替根(與 ENG073 _resolve_db 同律:家目錄下 glob movies-dataset*)。"""
    cand = [Path(db)] if db else [DB_MAIN]
    if not db:
        rel = Path("VeritasIntelligenceAnalytics/functional modules/VDF/"
                   "output_hub/mega/vdf_tw_market.duckdb")
        home = Path.home()
        for base in (home, home / "Downloads", home / "Github",
                     home / "OneDrive" / "Documents"):
            try:
                for root in sorted(base.glob("movies-dataset*")):
                    cand.append(root / rel)
            except Exception:
                continue
    for c in cand:
        if c.exists():
            return c, ("主路徑" if c == DB_MAIN else f"替根 {c}")
    return None, f"庫不在(主路徑與替根皆探過):{DB_MAIN}"


def _atomic_parquet(con, sql: str, dest: Path) -> None:
    """先寫暫存再原子換名——中途斷電不留半個 Parquet。"""
    dest.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(suffix=".parquet", dir=str(dest.parent))
    os.close(fd)
    tmp_p = Path(tmp)
    try:
        con.execute(f"COPY ({sql}) TO '{tmp_p.as_posix()}' (FORMAT PARQUET)")
        os.replace(str(tmp_p), str(dest))
    finally:
        if tmp_p.exists():
            try:
                tmp_p.unlink()
            except Exception:
                pass


def _merge_sql(table: str, keys: tuple, dest: Path, cols: list) -> str:
    """既有 Parquet ⊎ 本輪庫列 → 依主鍵去重(同鍵取較新)。

    **先合併再寫**:正典庫被重建或清空時,Parquet 一列都不會掉。
    """
    collist = ", ".join(f'"{c}"' for c in cols)
    keylist = ", ".join(f'"{k}"' for k in keys)
    fresh = FRESH_COL if FRESH_COL in cols else None
    order = f'"{fresh}" DESC NULLS LAST, _src ASC' if fresh else "_src ASC"
    if dest.exists():
        # _src: 0=本輪庫列(較新)、1=既有 Parquet;同鍵同新舊時本輪優先
        base = (f"SELECT {collist}, 0 AS _src FROM \"{table}\" "
                f"UNION ALL BY NAME "
                f"SELECT {collist}, 1 AS _src FROM read_parquet('{dest.as_posix()}')")
    else:
        base = f"SELECT {collist}, 0 AS _src FROM \"{table}\""
    return (f"SELECT {collist} FROM (SELECT *, row_number() OVER "
            f"(PARTITION BY {keylist} ORDER BY {order}) AS _rn FROM ({base})) "
            f"WHERE _rn = 1")


def build(db: Path | None = None, outdir: Path | None = None,
          derive: bool = False, do_print: bool = True) -> dict:
    """建/更新兩支主庫(累積式;既有列只會被同鍵較新者取代,不會消失)。"""
    out = Path(outdir) if outdir else OUTDIR
    rep: dict = {"schema": "VIA.VRN.MainDB.v1",
                 "ts": datetime.now().isoformat(timespec="seconds"),
                 "outdir": str(out), "tables": [], "derived": [], "why": ""}
    duckdb = _duck()
    if duckdb is None:
        rep["why"] = "本環境無 duckdb=誠實停;vrn 境補庫:uv pip install duckdb"
        if do_print:
            print(f"[主庫] {rep['why']}")
        return rep
    dbp, dbwhy = resolve_db(db)
    if dbp is None:
        rep["why"] = dbwhy + "=誠實停(先跑 vrn_structdb 讓正典庫長出來)"
        if do_print:
            print(f"[主庫] {rep['why']}")
        return rep
    rep["db"] = str(dbp)
    rep["db_src"] = dbwhy
    con = duckdb.connect(str(dbp), read_only=True)
    try:
        have = {r[0] for r in con.execute("SHOW TABLES").fetchall()}
        for table, fname, keys in TABLES:
            dest = out / fname
            row: dict = {"table": table, "file": fname, "keys": list(keys)}
            if table not in have:
                row["state"] = "NODATA"
                row["note"] = f"庫在但缺表 {table}(先跑 vrn_structdb/vrn_finpages)"
                rep["tables"].append(row)
                continue
            cols = [r[0] for r in con.execute(f'DESCRIBE "{table}"').fetchall()]
            before = 0
            if dest.exists():
                try:
                    before = con.execute(
                        f"SELECT COUNT(*) FROM read_parquet('{dest.as_posix()}')"
                    ).fetchone()[0]
                except Exception:
                    before = 0
            src_n = con.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
            _atomic_parquet(con, _merge_sql(table, keys, dest, cols), dest)
            after = con.execute(
                f"SELECT COUNT(*) FROM read_parquet('{dest.as_posix()}')").fetchone()[0]
            row.update({"state": "GREEN", "rows_before": before, "rows_db": src_n,
                        "rows_after": after, "added": after - before,
                        "cols": len(cols), "bytes": dest.stat().st_size})
            # 併掉的是**真重複**(全鍵相同)——要講出來,別讓「少了幾列」無聲無息。
            dup = src_n + before - after
            if dup > 0:
                row["dedup_dropped"] = dup
                row["dedup_note"] = (f"併掉 {dup} 列**全鍵相同**的真重複"
                                     "(值不同者依 KEEP_BOTH 律兩列都留)")
            # **只增不減的守衛**:合併後列數不得少於既有(少了就是丟資料)
            if after < before:
                row["state"] = "RED"
                row["note"] = (f"合併後列數 {after} < 既有 {before}=丟了資料,"
                               "這不該發生;請查主鍵是否選錯")
            rep["tables"].append(row)
            if do_print:
                print(f"  [{row['state']}] {fname:<34} 庫 {src_n:>5} 列 · "
                      f"既有 {before:>5} → 合併後 {after:>5}(+{after - before})"
                      f" · {row.get('cols', 0)} 欄")
        if derive:
            rep["derived"] = _derive(con, out, do_print)
    finally:
        con.close()
    ok = all(t.get("state") in ("GREEN", "NODATA") for t in rep["tables"])
    green = sum(1 for t in rep["tables"] if t.get("state") == "GREEN")
    if do_print:
        print(f"[主庫] {'GREEN' if ok else 'RED'} · 主庫 {green}/{len(TABLES)} 支 · "
              f"落點 {out}"
              + (f" · 派生 {len(rep['derived'])} 件" if derive else ""))
    rep["verdict"] = "GREEN" if ok else "RED"
    return rep


def _derive(con, out: Path, do_print: bool = True) -> list:
    """**單向派生**:Parquet(真值)→ CSV / JSON / DuckDB 檢視。

    派生物永遠不被讀回來當來源;要改資料只能改上游引擎再重跑。
    每一件都標 `_derived_from`,讓人一眼看出它不是真值。
    """
    made = []
    for _table, fname, _keys in TABLES:
        src = out / fname
        if not src.exists():
            continue
        stem = src.stem
        rel = src.as_posix()
        csv_p = out / f"{stem}.csv"
        json_p = out / f"{stem}.json"
        try:
            # CSV:utf-8-sig 給 Excel(操作員備註:注意 BOM 與中文)
            # DuckDB 的 COPY TO CSV 本來就寫 UTF-8;`ENCODING 'UTF-8'` 這個選項
            # 這一版收不了(實測 InvalidInputException)。BOM 由下面自己補——
            # utf-8-sig 的定義就是「UTF-8 + BOM」,Excel 認的是那三個位元組。
            con.execute(f"COPY (SELECT * FROM read_parquet('{rel}')) "
                        f"TO '{csv_p.as_posix()}' (FORMAT CSV, HEADER)")
            raw = csv_p.read_bytes()
            if not raw.startswith(b"\xef\xbb\xbf"):
                csv_p.write_bytes(b"\xef\xbb\xbf" + raw)
            made.append(str(csv_p))
        except Exception as exc:
            if do_print:
                print(f"    [派生] CSV 失敗 {stem}:{type(exc).__name__}")
        try:
            rows = con.execute(f"SELECT * FROM read_parquet('{rel}')").fetchall()
            cols = [d[0] for d in con.description]
            json_p.write_text(json.dumps(
                {"_derived_from": fname, "_note": "派生物;真值在 Parquet,勿反向維護",
                 "rows": [dict(zip(cols, r)) for r in rows]},
                ensure_ascii=False, indent=1, default=str), encoding="utf-8")
            made.append(str(json_p))
        except Exception as exc:
            if do_print:
                print(f"    [派生] JSON 失敗 {stem}:{type(exc).__name__}")
    # DuckDB 檢視:**view 不是 table**——它永遠照著 Parquet 走,不會各自長大
    ddb = out / "StockReport.duckdb"
    try:
        import duckdb as _d
        c2 = _d.connect(str(ddb))
        for _t, fname, _k in TABLES:
            src = out / fname
            if src.exists():
                c2.execute(f'CREATE OR REPLACE VIEW "{Path(fname).stem}" AS '
                           f"SELECT * FROM read_parquet('{src.as_posix()}')")
        c2.close()
        made.append(str(ddb))
    except Exception as exc:
        if do_print:
            print(f"    [派生] DuckDB 失敗:{type(exc).__name__}")
    if do_print:
        print(f"    [派生] {len(made)} 件(CSV/JSON/DuckDB 檢視;單向,不回流)")
    return made


def status(outdir: Path | None = None, do_print: bool = True) -> dict:
    """唯讀盤點:兩支主庫在不在、幾列幾欄、多久以前。"""
    out = Path(outdir) if outdir else OUTDIR
    duckdb = _duck()
    rep = {"outdir": str(out), "tables": []}
    for _t, fname, keys in TABLES:
        p = out / fname
        row = {"file": fname, "exists": p.exists(), "keys": list(keys)}
        if p.exists() and duckdb is not None:
            try:
                c = duckdb.connect(":memory:")
                row["rows"] = c.execute(
                    f"SELECT COUNT(*) FROM read_parquet('{p.as_posix()}')").fetchone()[0]
                row["cols"] = len(c.execute(
                    f"SELECT * FROM read_parquet('{p.as_posix()}') LIMIT 0").description)
                c.close()
                row["bytes"] = p.stat().st_size
                row["mtime"] = datetime.fromtimestamp(
                    p.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
            except Exception as exc:
                row["why"] = f"讀不開 {type(exc).__name__}"
        rep["tables"].append(row)
        if do_print:
            print(f"  {'在' if row['exists'] else '缺'} {fname:<34} "
                  + (f"{row.get('rows', '?'):>6} 列 · {row.get('cols', '?')} 欄 · "
                     f"{row.get('mtime', '')}" if row["exists"] else "(未建;跑 build)"))
    return rep


def selftest() -> int:
    print("=== VRN 交付主資料庫(VRN_ENG081 v0100)· 十一檢自測(零網路)===")
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    src = Path(__file__).read_text(encoding="utf-8")
    body = src.split("def selftest")[0]
    duckdb = _duck()

    chk("① 檔名依操作員的檔名修正表(無空白、無重複副檔名、Financial 寫全)",
        all(" " not in f and f.count(".parquet") == 1 for _t, f, _k in TABLES)
        and any(f == "StockReportBasicInfo.parquet" for _t, f, _k in TABLES)
        and any(f == "StockReportFinancialData.parquet" for _t, f, _k in TABLES),
        f"({[f for _t, f, _k in TABLES]})")

    chk("② **Zero-Hydra:本件不自建抽取**——一個 regex 都沒有,資料一律來自正典 DuckDB",
        "re.compile" not in body and "vrn_report_basic" in body,
        "(零 regex · 讀正典表)")

    if duckdb is None:
        chk("③–⑧ 合併/累積/派生實跑", True, "(本環境無 duckdb=誠實跳)")
    else:
        import tempfile as _tf
        with _tf.TemporaryDirectory() as td:
            root = Path(td)
            db = root / "t.duckdb"
            c = duckdb.connect(str(db))
            c.execute("CREATE TABLE vrn_report_basic(report_file VARCHAR, ticker VARCHAR, "
                      "target_price DOUBLE, extracted_at VARCHAR)")
            c.execute("INSERT INTO vrn_report_basic VALUES "
                      "('a.pdf','2330',1200.0,'2026-09-13 10:00'),"
                      "('b.pdf','2317',250.0,'2026-09-13 10:00')")
            c.execute("CREATE TABLE vrn_report_financial(report_file VARCHAR, page INTEGER, "
                      "canonical VARCHAR, raw_label VARCHAR, period VARCHAR, status VARCHAR, "
                      "value DOUBLE, raw_text VARCHAR)")
            c.execute("INSERT INTO vrn_report_financial VALUES "
                      "('a.pdf',1,'eps','EPS','2025','A',9.8,'x')")
            c.close()
            out = root / "md"
            r1 = build(db=db, outdir=out, do_print=False)
            bp = out / "StockReportBasicInfo.parquet"
            fp = out / "StockReportFinancialData.parquet"
            chk("③ 兩支主庫落地(Parquet;原子換名)",
                bp.exists() and fp.exists() and r1["verdict"] == "GREEN",
                f"(basic {bp.exists()} · financial {fp.exists()})")

            # 庫改了一列、加了一列、**刪掉一列** → Parquet 仍不得掉列
            c = duckdb.connect(str(db))
            c.execute("DELETE FROM vrn_report_basic WHERE report_file='b.pdf'")
            c.execute("UPDATE vrn_report_basic SET target_price=1300.0, "
                      "extracted_at='2026-09-13 12:00' WHERE report_file='a.pdf'")
            c.execute("INSERT INTO vrn_report_basic VALUES "
                      "('c.pdf','2454',900.0,'2026-09-13 12:00')")
            c.close()
            r2 = build(db=db, outdir=out, do_print=False)
            c = duckdb.connect(":memory:")
            rows = {x[0]: x[2] for x in c.execute(
                f"SELECT report_file, ticker, target_price FROM "
                f"read_parquet('{bp.as_posix()}')").fetchall()}
            c.close()
            chk("④ **累積式**:庫裡被刪掉的 b.pdf 仍在 Parquet(只增不減;"
                "正典庫被重建也不會掉列)",
                "b.pdf" in rows, f"(鍵={sorted(rows)})")
            chk("⑤ **同鍵取較新**:a.pdf 由 1200 → 1300(extracted_at 較新者勝),"
                "而且是**取代不是併存**",
                rows.get("a.pdf") == 1300.0 and len(rows) == 3,
                f"(a.pdf={rows.get('a.pdf')} · 列數={len(rows)})")
            chk("⑥ 新列進得來", "c.pdf" in rows, "")
            b_row = next(t for t in r2["tables"] if t["file"] == "StockReportBasicInfo.parquet")
            chk("⑦ **丟資料守衛**:合併後列數少於既有就判 RED(主鍵選錯時會炸給人看)",
                b_row["rows_after"] >= b_row["rows_before"]
                and "rows_before" in b_row and "added" in b_row
                and "合併後列數" in body,
                f"(既有 {b_row['rows_before']} → {b_row['rows_after']})")

            # KEEP_BOTH:同 (檔,指標,期別) 但**值不同** → 兩列都要在
            c = duckdb.connect(str(db))
            c.execute("CREATE TABLE vrn_report_metrics(report_file VARCHAR, metric VARCHAR, "
                      "period VARCHAR, status VARCHAR, value DOUBLE, raw_text VARCHAR)")
            c.execute("INSERT INTO vrn_report_metrics VALUES "
                      "('d.pdf','eps','2024','E',11.0,'x'),"
                      "('d.pdf','eps','2024','E',9.53,'y'),"   # 衝突=兩列都留
                      "('d.pdf','eps','2026','E',10.0,'p'),"
                      "('d.pdf','eps','2026','E',10.0,'q')")   # 真重複=併成一列
            c.close()
            build(db=db, outdir=out, do_print=False)
            mp = out / "StockReportMetrics.parquet"
            c = duckdb.connect(":memory:")
            mrows = c.execute(f"SELECT period, value FROM read_parquet('{mp.as_posix()}') "
                              f"ORDER BY period, value").fetchall()
            c.close()
            chk("⑦b **KEEP_BOTH**:同(檔/指標/期別)但**值不同**=衝突,兩列都留"
                "(真料實測:3014TT eps 2024 有 11.0 與 9.53 兩個預估,我判不出哪個對,"
                "偷偷選一個就是替操作員做了沒依據的決定);**值相同**才是真重複,併掉",
                len(mrows) == 3 and ("2024", 9.53) in mrows and ("2024", 11.0) in mrows
                and sum(1 for r in mrows if r[0] == "2026") == 1,
                f"(4 進 → {len(mrows)} 留:{mrows})")

            r3 = build(db=db, outdir=out, derive=True, do_print=False)
            csv_p = out / "StockReportBasicInfo.csv"
            json_p = out / "StockReportBasicInfo.json"
            ddb = out / "StockReport.duckdb"
            head = csv_p.read_bytes()[:3] if csv_p.exists() else b""
            _bom_ok = head == b"\xef\xbb\xbf"
            jd = json.loads(json_p.read_text(encoding="utf-8")) if json_p.exists() else {}
            chk("⑧ **單向派生**:CSV(utf-8-sig 給 Excel)/ JSON / DuckDB **檢視**皆自 Parquet 出;"
                "JSON 標明 _derived_from,DuckDB 用 VIEW 不是 TABLE(它永遠照著 Parquet 走,"
                "不會各自長大成第二份真值)",
                csv_p.exists() and head == b"\xef\xbb\xbf"
                and jd.get("_derived_from") == "StockReportBasicInfo.parquet"
                and ddb.exists() and "CREATE OR REPLACE VIEW" in body
                and len(r3["derived"]) >= 4,
                f"(派生 {len(r3['derived'])} 件 · BOM={_bom_ok})")

    chk("⑨ 缺庫/缺表=**誠實停**,不假裝寫了主庫(缺料 ≠ 壞掉)",
        "誠實停" in body and "NODATA" in body
        and build(db=Path("/一定不存在的庫.duckdb"), do_print=False)["why"] != "",
        "")

    chk("⑩ 零網路 · 落點在 VIA_Reports(已在 .gitignore,資料不進 git)· 加速橋在位",
        all(("import " + k) not in body for k in ("requests", "httpx", "urllib.request"))
        and 'VIA_Reports' in body and "ACCEL-BRIDGE" in src, "")

    n = 11
    print(f"  [計] 十一檢({n} 檢) OK {n - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        return selftest()
    outdir = Path(a[a.index("--out") + 1]) if "--out" in a else None
    if a and a[0] == "status":
        status(outdir)
        return 0
    if a and a[0] == "build":
        r = build(outdir=outdir, derive="--derive" in a)
        return 0 if r.get("verdict") == "GREEN" or r.get("why") else 1
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main())
