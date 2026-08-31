# -*- coding: utf-8 -*-
"""ENG-052 SSOT persistence. Preferred DuckDB + Parquet; SQLite is a degraded local fallback."""
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
import argparse,csv,json,sqlite3
from datetime import datetime
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;OUT=ROOT/"out";CFG=HERE/"ssot_store_params.json"
def jload(p,d):
    try:return json.loads(Path(p).read_text(encoding="utf-8-sig"))
    except Exception:return d
def jl(p):
    rows=[]
    if not Path(p).exists():return rows
    for ln in Path(p).read_text(encoding="utf-8",errors="replace").splitlines():
        try:rows.append(json.loads(ln))
        except Exception:pass
    return rows
def csvrows(p):
    if not Path(p).exists():return []
    with Path(p).open("r",encoding="utf-8-sig",errors="replace",newline="") as f:return list(csv.DictReader(f))
def latest_projects():
    cur={}
    for r in jl(OUT/"project_registry.jsonl"):
        pid=r.get("project_id")
        if pid:
            x=cur.get(pid,{})
            x.update({k:v for k,v in r.items() if v is not None});cur[pid]=x
    return list(cur.values())
def datasets():
    return {
      "projects":latest_projects(),
      "emails":jl(OUT/"email_raw_graph.jsonl"),
      "commitments":jload(OUT/"commitment_status.json",{"items":[]}).get("items",[]),
      "work_items":jload(OUT/"unified_work_register.json",{"items":[]}).get("items",[]),
      "events":csvrows(OUT/"process_event_log.csv"),
      "project_cards":jload(OUT/"project_cards.json",{"cards":[]}).get("cards",[]),
      "stakeholders":jl(OUT/"stakeholder_registry.jsonl"),
      "stakeholder_roles":jl(OUT/"stakeholder_role_registry.jsonl"),
      "milestones":jload(OUT/"milestone_summary.json",{"projects":[]}).get("projects",[]),
      "attachments":jl(OUT/"attachment_intelligence.jsonl"),
      "topics":jload(OUT/"topic_episodes.json",{"threads":[]}).get("threads",[]),
      "lessons":jl(OUT/"lesson_registry.jsonl"),
      "meetings":jload(OUT/"meeting_t2_guard.json",{"items":[]}).get("items",[]),
      "escalations":jload(OUT/"escalation_candidates.json",{"items":[]}).get("items",[])
    }
def normalize(rows):
    return [{k:(json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list)) else v) for k,v in r.items()} for r in rows]
def duckdb_snapshot(cfg,data):
    try:
        import duckdb, pyarrow as pa, pyarrow.parquet as pq
    except Exception as e:return None,str(e)
    db=ROOT/cfg["duckdb_path"];db.parent.mkdir(parents=True,exist_ok=True)
    pqroot=ROOT/cfg["parquet_root"];pqroot.mkdir(parents=True,exist_ok=True)
    con=duckdb.connect(str(db))
    table_stats={}
    try:
        for name,rows in data.items():
            rows=normalize(rows)
            if rows:
                tbl=pa.Table.from_pylist(rows)
                con.register("_incoming",tbl)
                con.execute(f'CREATE OR REPLACE TABLE "{name}" AS SELECT * FROM _incoming')
                con.unregister("_incoming")
                pq.write_table(tbl,pqroot/f"{name}.parquet",compression="zstd")
                table_stats[name]=len(rows)
            else:
                table_stats[name]=0
        con.execute("CREATE TABLE IF NOT EXISTS ssot_meta(key VARCHAR PRIMARY KEY,value VARCHAR)")
        con.execute("INSERT OR REPLACE INTO ssot_meta VALUES ('last_snapshot',?)",[datetime.now().astimezone().isoformat(timespec="seconds")])
    finally:con.close()
    return table_stats,None
def sqlite_snapshot(cfg,data):
    db=ROOT/cfg["fallback_sqlite"];db.parent.mkdir(parents=True,exist_ok=True);con=sqlite3.connect(db)
    stats={}
    try:
        for name,rows in data.items():
            rows=normalize(rows);con.execute(f'DROP TABLE IF EXISTS "{name}"')
            cols=sorted({k for r in rows for k in r.keys()}) if rows else ["_empty"]
            con.execute(f'CREATE TABLE "{name}" ({",".join(chr(34)+c+chr(34)+" TEXT" for c in cols)})')
            if rows:
                q=f'INSERT INTO "{name}" ({",".join(chr(34)+c+chr(34) for c in cols)}) VALUES ({",".join("?" for _ in cols)})'
                con.executemany(q,[[None if r.get(c) is None else str(r.get(c)) for c in cols] for r in rows])
            stats[name]=len(rows)
        con.execute("CREATE TABLE IF NOT EXISTS ssot_meta(key TEXT PRIMARY KEY,value TEXT)")
        con.execute("INSERT OR REPLACE INTO ssot_meta VALUES (?,?)",("last_snapshot",datetime.now().astimezone().isoformat(timespec="seconds")))
        con.commit()
    finally:con.close()
    return stats
def snapshot():
    cfg=jload(CFG,{});data=datasets();stats,err=duckdb_snapshot(cfg,data)
    if stats is not None:mode="DUCKDB_PARQUET";gate="PASS"
    else:stats=sqlite_snapshot(cfg,data);mode="SQLITE_DEGRADED";gate="READY_WITH_WARNINGS"
    rep={"engine_id":"ENG-052","gate":gate,"mode":mode,"tables":stats,"duckdb_error":err,
         "generated_at":datetime.now().astimezone().isoformat(timespec="seconds")}
    (OUT/"ssot_status.json").write_text(json.dumps(rep,ensure_ascii=False,indent=2),encoding="utf-8");return rep
def main():
    ap=argparse.ArgumentParser();ap.add_argument("command",nargs="?",default="snapshot",choices=["snapshot","status"]);a=ap.parse_args()
    print(json.dumps(snapshot() if a.command=="snapshot" else jload(OUT/"ssot_status.json",{}),ensure_ascii=False,indent=2));return 0
if __name__=="__main__":raise SystemExit(main())
