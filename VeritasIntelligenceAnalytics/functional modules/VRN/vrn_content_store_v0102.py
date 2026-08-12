#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
vrn_content_store_v0102 — 對帳綠燈內容落庫 via.duckdb(--init 建新庫版)
=======================================================================
v0101→v0102:操作員全碟掃描(C:\\ D:\\ Get-ChildItem -Recurse)證實
via.duckdb 於本機「零存在」——MDL025 正典路徑(2026-05-24 證據,含 22 表)
之實體檔已不在。新增 --init:候選全空時於正典路徑建全新庫落庫,
誠實記錄 FRESH_INIT(非歷史 22 表庫之延續;歷史庫若他日尋回,本引擎
upsert 冪等可直接對其重跑,新表併入零衝突)。無 --init 行為與 v0101 全同。
治理鐵則(承 v0100):
  ① dry-run 預設 — 不帶 --commit 只出落庫計畫,零寫入
  ② 只增不減 — 只建/寫「新表」(vrn_report_*),22 現表零觸碰
  ③ 寫前整檔備份 via.duckdb → via.duckdb.pre_<ts>.bak
  ④ upsert 冪等 — 同 pdf_name/source_document 舊列剔除後插入,重跑不疊加
  ⑤ 稽核 append-only — 每次 commit 寫 vrn_store_log 一列
用法:py vrn_content_store_v0102.py [--db PATH] [--commit] [--init]
"""
from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
# 正典:MDL025 vrn_production_home primary_duckdb
CANON = Path.home() / "OneDrive/VeritasIntelligenceAnalytics/module/VeritasDataForge/data/via.duckdb"


def find_db(override: str | None):
    if override:
        p = Path(override)
        return (p, [str(p)]) if p.exists() else (None, [str(p)])
    cands = [
        # 正典:MDL025 vrn_production_home primary_duckdb(多份證據一致)
        CANON,
        # 次候選:Data Source Matrix 儀表配置
        Path("D:/VIA/via.duckdb"),
        # v0100 舊候選(保留,只增不減)
        HERE / "db" / "via.duckdb",
        VIA / "functional modules/VDF/db/via.duckdb",
        Path.home() / "OneDrive/VeritasIntelligenceAnalytics/module/VDF/dict/via.duckdb",
        Path.home() / "OneDrive/VeritasIntelligenceAnalytics/module/via.duckdb",
    ]
    for c in cands:
        if c.exists():
            return c, [str(x) for x in cands]
    return None, [str(x) for x in cands]


def main() -> int:
    args = sys.argv[1:]
    commit = "--commit" in args
    override = args[args.index("--db") + 1] if "--db" in args else None
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    try:
        import duckdb
    except ImportError:
        print("[FAIL] duckdb 未安裝 — 誠實停止")
        return 1

    db, tried = find_db(override)
    fresh = False
    if db is None:
        if "--init" in args:
            db = Path(override) if override else CANON
            fresh = True
            print("  [init] 候選全空 — 於正典路徑建全新庫(誠實:FRESH_INIT,非 2026-05-24 之 22 表歷史庫)")
        else:
            print("[FAIL] via.duckdb 不在下列候選(--db 指定實際路徑;本機確無則 --init 建新庫):")
            for t in tried:
                print(f"   · {t}")
            return 1

    v2p = HERE / "SSOT/v2/VRN_ResearchReport_SSOT.v2.jsonl"
    records = [json.loads(l) for l in v2p.read_text(encoding="utf-8-sig").splitlines() if l.strip()]
    t005 = HERE / "staging/ocr_out/mdl005_temp/VRN_MDL005_Text.parquet"
    t004 = HERE / "staging/ocr_out/mdl004_temp/VRN_MDL004_Tables.parquet"

    mode = "COMMIT" if commit else "DRY-RUN(計畫;--commit 才寫)"
    print(f"=== 內容落庫 v0102 · {mode} ===")
    print(f"  [庫] {db}({'新建' if fresh else f'{db.stat().st_size:,}B'})")
    print(f"  [源] SSOT v2 {len(records)} 筆 · 文字表 {'在' if t005.exists() else '缺'} · 表格表 {'在' if t004.exists() else '缺'}")

    if fresh and not commit:
        print("  [計畫] 建新庫 + 4 新表(canon 64/text/cells/log)")
        print("  [dry-run] 新庫尚未建立。確認後:via-store --init --commit")
        return 0

    if fresh:
        db.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(db), read_only=not commit)
    try:
        existing = {r[0] for r in con.execute(
            "select table_name from information_schema.tables where table_schema='main'").fetchall()}
        ours = {"vrn_report_content_canon", "vrn_report_text_blocks", "vrn_report_table_cells", "vrn_store_log"}
        print(f"  [表] 庫內 {len(existing)} 表 · 本引擎目標 4 新表({len(ours & existing)} 已在)· 其餘現表零觸碰")

        canon_rows = []
        for rec in records:
            tps = rec.get("filtered_target_price_proposals") or rec.get("target_price_content_guesses") or []
            canon_rows.append({
                "source_document": rec.get("source_document"),
                "record_id": rec.get("record_id"),
                "record_hash": rec.get("record_hash"),
                "canonical_record_state": rec.get("canonical_record_state"),
                "broker": rec.get("final_broker_proposal") or rec.get("broker_guess"),
                "report_date": rec.get("report_date_guess"),
                "report_type": rec.get("final_report_type_proposal") or rec.get("report_type_guess"),
                "primary_tickers": json.dumps(rec.get("final_primary_ticker_proposals") or [], ensure_ascii=False),
                "target_prices": json.dumps(tps, ensure_ascii=False),
                "evidence_state": rec.get("evidence_state"),
                "review_required": bool(rec.get("review_required")),
                "source_sha256": rec.get("source_sha256"),
                "stored_at": ts,
                "provenance": "SSOT_v2.records64 + ocr_out reconcile COVERED 20260812_034305",
            })
        n_text = con.execute(f"select count(*) from read_parquet('{t005.as_posix()}')").fetchone()[0] if t005.exists() else 0
        n_cell = con.execute(f"select count(*) from read_parquet('{t004.as_posix()}')").fetchone()[0] if t004.exists() else 0
        print(f"  [計畫] content_canon upsert {len(canon_rows)} · text_blocks {n_text:,} · table_cells {n_cell:,}")

        if not commit:
            print("  [dry-run] 零寫入。確認計畫無誤後:via-store --commit")
            return 0

        # ③ 寫前整檔備份(新建庫無前檔——誠實跳過)
        if fresh:
            bak = db.with_name(db.name + f".pre_{ts}.none")
            print("  [備份] 新建庫無前檔 — 跳過")
        else:
            bak = db.with_name(db.name + f".pre_{ts}.bak")
            shutil.copy2(db, bak)
            print(f"  [備份] {bak.name}")

        con.execute("begin")
        con.execute("""create table if not exists vrn_report_content_canon(
            source_document varchar, record_id varchar, record_hash varchar,
            canonical_record_state varchar, broker varchar, report_date varchar,
            report_type varchar, primary_tickers varchar, target_prices varchar,
            evidence_state varchar, review_required boolean, source_sha256 varchar,
            stored_at varchar, provenance varchar)""")
        docs = [r["source_document"] for r in canon_rows]
        con.execute("delete from vrn_report_content_canon where source_document in "
                    f"({','.join('?' * len(docs))})", docs)
        cols = list(canon_rows[0].keys())
        con.executemany(
            f"insert into vrn_report_content_canon({','.join(cols)}) values ({','.join('?' * len(cols))})",
            [[r[c] for c in cols] for r in canon_rows])

        for stem, table, path in (("mdl005", "vrn_report_text_blocks", t005),
                                  ("mdl004", "vrn_report_table_cells", t004)):
            if not path.exists():
                print(f"  [WARN] {stem} parquet 缺 — {table} 跳過(誠實)")
                continue
            con.execute(f"create table if not exists {table} as select * from read_parquet('{path.as_posix()}') limit 0")
            key = "pdf_name"
            has_key = any(r[0] == key for r in con.execute(f"describe {table}").fetchall())
            if has_key:
                con.execute(f"delete from {table} where {key} in (select distinct {key} from read_parquet('{path.as_posix()}'))")
            con.execute(f"insert into {table} by name (select * from read_parquet('{path.as_posix()}'))")

        con.execute("""create table if not exists vrn_store_log(
            ts varchar, action varchar, canon_rows int, text_rows bigint, cell_rows bigint,
            backup varchar, provenance varchar)""")
        con.execute("insert into vrn_store_log values (?,?,?,?,?,?,?)",
                    [ts, "FRESH_INIT+STORE_64_CORPUS" if fresh else "STORE_64_CORPUS",
                     len(canon_rows), n_text, n_cell, bak.name,
                     "vrn_content_store_v0102"])
        con.execute("commit")

        now = {r[0] for r in con.execute(
            "select table_name from information_schema.tables where table_schema='main'").fetchall()}
        for t in ("vrn_report_content_canon", "vrn_report_text_blocks", "vrn_report_table_cells", "vrn_store_log"):
            if t not in now:
                print(f"  [驗] {t}:未建(來源缺,已誠實跳過)")
                continue
            n = con.execute(f"select count(*) from {t}").fetchone()[0]
            print(f"  [驗] {t}:{n:,} 列")
        print("  [完] 落庫完成(現表零觸碰;稽核已記;備份留存)")
        return 0
    except Exception as exc:
        try:
            con.execute("rollback")
        except Exception:
            pass
        print(f"  [FAIL] {type(exc).__name__}: {exc}(已回滾;備份未動)")
        return 1
    finally:
        con.close()


if __name__ == "__main__":
    sys.exit(main())
