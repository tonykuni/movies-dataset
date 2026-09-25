#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
vrn_content_store_v0106 — 對帳綠燈內容落庫 via.duckdb(Windows 自鎖根因修)
=======================================================================
v0105→v0106(工作站 WinError 32 實錄):v0105 先開「寫入連線」後做整檔
備份——DuckDB 寫入連線於 Windows 持排他鎖,自己鎖死自己的 shutil.copy2
(Linux 不鎖故容器未現形;首次非新建 commit 才走到此路)。
修:備份移至 duckdb.connect 之前(commit 模式先備份再開連線)。
(承 v0105)
=======================================================================
v0103→v0104(操作員令:OneDrive 裡面的備份檔全數刪除):
  新增 --purge-onedrive:刪前強制完整性閘——本機正典與 OneDrive 舊庫
  「表列+逐表行數」全同才放行;dry-run 先列刪除清單(via.duckdb 本體+
  同夾 *.bak/*.pre_*);--commit 才刪。範圍嚴限 VeritasDataForge\data 夾
  之 via.duckdb 家族(更大範圍清理需另令明示)。此為操作員明令之刪除,
  完整性閘+雙段確認為紅線護欄。
v0102→v0103(操作員令 2026-08-12:儲存不落 OneDrive):
  正典遷本機:functional modules/VDF/db/via.duckdb(repo 樹內,gitignore
  護欄已在);--init 改建於本機正典;OneDrive 路徑退位為「舊制偵測」末位
  (命中時誠實告示建議遷移);新增 --migrate:OneDrive 舊庫→本機正典
  「複製」搬遷(零刪除——OneDrive 原件原地凍結為備份,不動不刪)。
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
用法:py vrn_content_store_v0106.py(v0104→v0105:docstring raw 化除 SyntaxWarning 噪音,行為零變更) [--db PATH] [--commit] [--init] [--migrate] [--purge-onedrive]
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

import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
# 正典(2026-08-12 去 OneDrive 令):本機 repo 樹內(gitignore 護欄已在)
CANON = HERE.parent / "VDF/db/via.duckdb"
# 舊制:MDL025 OneDrive primary_duckdb——退位為偵測末位+遷移來源(唯讀凍結)
ONEDRIVE_LEGACY = Path.home() / "OneDrive/VeritasIntelligenceAnalytics/module/VeritasDataForge/data/via.duckdb"


def find_db(override: str | None):
    if override:
        p = Path(override)
        return (p, [str(p)]) if p.exists() else (None, [str(p)])
    cands = [
        # 正典:本機(去 OneDrive 令)
        CANON,
        HERE / "db" / "via.duckdb",
        Path("C:/VIA/via.duckdb"),
        Path("D:/VIA/via.duckdb"),
        # 舊制末位(命中=候遷移;只增不減保留偵測)
        ONEDRIVE_LEGACY,
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

    if "--purge-onedrive" in args:
        print("=== OneDrive 備份清除 · " + ("COMMIT" if commit else "DRY-RUN(--commit 才刪)") + " ===")
        if not ONEDRIVE_LEGACY.exists():
            print(f"  [OK  ] OneDrive 已無 via.duckdb({ONEDRIVE_LEGACY.parent})——無事可刪")
            return 0
        if not CANON.exists():
            print("  [FAIL] 本機正典不在——先 via-store --migrate --commit(刪前必有本機庫,紅線)")
            return 1
        # 完整性閘:本機 vs OneDrive 表列+逐表行數全同才放行
        try:
            a = duckdb.connect(str(CANON), read_only=True)
            b = duckdb.connect(str(ONEDRIVE_LEGACY), read_only=True)
            ta = {r[0] for r in a.execute("select table_name from information_schema.tables where table_schema='main'").fetchall()}
            tb = {r[0] for r in b.execute("select table_name from information_schema.tables where table_schema='main'").fetchall()}
            if ta != tb:
                print(f"  [FAIL] 表列不同(本機 {len(ta)} vs OneDrive {len(tb)})——不刪(誠實停止)")
                return 1
            for t in sorted(ta):
                na = a.execute(f'select count(*) from "{t}"').fetchone()[0]
                nb = b.execute(f'select count(*) from "{t}"').fetchone()[0]
                if na != nb:
                    print(f"  [FAIL] {t} 行數不同({na} vs {nb})——不刪(誠實停止)")
                    return 1
                print(f"  [驗] {t}:{na:,} 列 全同")
            a.close(); b.close()
        except Exception as exc:
            print(f"  [FAIL] 完整性閘異常 {type(exc).__name__}: {exc} — 不刪")
            return 1
        targets = sorted(p for p in ONEDRIVE_LEGACY.parent.glob("via.duckdb*") if p.is_file())
        print(f"  [單] 刪除清單({len(targets)} 件,嚴限 {ONEDRIVE_LEGACY.parent}):")
        for p in targets:
            print(f"     · {p.name}({p.stat().st_size:,}B)")
        if not commit:
            print("  [dry-run] 零刪除。完整性閘全同已證;確認後:via-store --purge-onedrive --commit")
            return 0
        for p in targets:
            p.unlink()
            print(f"  [刪] {p.name}")
        print("  [完] OneDrive via.duckdb 家族清除完成(本機正典完整性已先證)")
        return 0

    if "--migrate" in args:
        if not ONEDRIVE_LEGACY.exists():
            print(f"[FAIL] 遷移來源不在:{ONEDRIVE_LEGACY}")
            return 1
        print("=== 去 OneDrive 遷移 · " + ("COMMIT" if commit else "DRY-RUN(--commit 才複製)") + " ===")
        print(f"  [源] {ONEDRIVE_LEGACY}({ONEDRIVE_LEGACY.stat().st_size:,}B)")
        print(f"  [靶] {CANON}{'(已在——誠實不覆蓋,如需重遷先移走本機檔)' if CANON.exists() else '(本機正典)'}")
        if not commit:
            print("  [dry-run] 零動作。確認後:via-store --migrate --commit")
            return 0
        if CANON.exists():
            print("  [FAIL] 本機正典已在——不覆蓋(誠實停止)")
            return 1
        CANON.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ONEDRIVE_LEGACY, CANON)
        print(f"  [遷] 複製完成 {CANON.stat().st_size:,}B · OneDrive 原件原地凍結為備份(零刪除)")
        print("  [次步] via-store 驗新正典;日後落庫皆走本機")
        return 0

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
    print(f"=== 內容落庫 v0106 · {mode} ===")
    if db == ONEDRIVE_LEGACY:
        print("  [告示] 命中 OneDrive 舊制庫——依令儲存不落 OneDrive:建議 via-store --migrate --commit 遷本機")
    print(f"  [庫] {db}({'新建' if fresh else f'{db.stat().st_size:,}B'})")
    print(f"  [源] SSOT v2 {len(records)} 筆 · 文字表 {'在' if t005.exists() else '缺'} · 表格表 {'在' if t004.exists() else '缺'}")

    if fresh and not commit:
        print("  [計畫] 建新庫 + 4 新表(canon 64/text/cells/log)")
        print("  [dry-run] 新庫尚未建立。確認後:via-store --init --commit")
        return 0

    if fresh:
        db.parent.mkdir(parents=True, exist_ok=True)
    # ③ 寫前整檔備份 —— 必在開寫入連線「之前」(Windows 排他鎖自鎖根因修)
    bak = db.with_name(db.name + f".pre_{ts}." + ("none" if fresh else "bak"))
    if commit:
        if fresh:
            print("  [備份] 新建庫無前檔 — 跳過")
        else:
            shutil.copy2(db, bak)
            print(f"  [備份] {bak.name}(先備份後開連線)")
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
                     "vrn_content_store_v0106"])
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
