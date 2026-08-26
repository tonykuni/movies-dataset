"""VPL-C05 · Storage policy + archive (Parquet / JSON / DuckDB).

"所有資料存檔使用 PARQUET / JSON / DUCKDB,看適當類型."

Policy (chosen per data shape):
  - PARQUET : large / append-only / columnar analytics
              (transcript segments, ledger, weeklog, news)
  - JSON    : small structured config / registry
              (plans, news_sources, team, project meta)
  - DUCKDB  : the unified query engine + operational warehouse
              (tasks, risks, etc. + views over the Parquet/JSON above)

SQLite stays the live transactional store; archive() mirrors it into the
analytics formats and a DuckDB warehouse that views the Parquet/JSON files.
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
import os
from pathlib import Path
from .store import load_project, connect

PARQUET = ("segment", "ledger", "weeklog", "news")
JSON = ("plan", "news_source", "team", "stakeholder")
DUCK = ("task", "risk", "milestone", "budget", "meeting", "checklist", "event")

POLICY = {**{t: "parquet" for t in PARQUET},
          **{t: "json" for t in JSON},
          **{t: "duckdb" for t in DUCK}}


def _rows(db_path, table):
    con = connect(db_path)
    rows = [dict(r) for r in con.execute(f"SELECT * FROM {table}")]
    con.close()
    return rows


def archive(db_path: str, out_dir: str = "output/warehouse") -> dict:
    import pyarrow as pa
    import pyarrow.parquet as pq
    import duckdb
    os.makedirs(out_dir, exist_ok=True)
    manifest = {"parquet": {}, "json": {}, "duckdb": None, "policy": POLICY}

    # PARQUET — columnar analytics
    for t in PARQUET:
        rows = _rows(db_path, t)
        if not rows:
            continue
        table = pa.Table.from_pylist(rows)
        path = os.path.join(out_dir, f"{t}.parquet")
        pq.write_table(table, path)
        manifest["parquet"][t] = {"path": path, "rows": len(rows)}

    # JSON — config / small structured
    for t in JSON:
        rows = _rows(db_path, t)
        path = os.path.join(out_dir, f"{t}.json")
        Path(path).write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
        manifest["json"][t] = {"path": path, "rows": len(rows)}

    # DUCKDB — warehouse: operational tables + views over parquet/json
    duck_path = os.path.join(out_dir, "veritaspulse.duckdb")
    if os.path.exists(duck_path):
        os.remove(duck_path)
    con = duckdb.connect(duck_path)
    for t in DUCK:
        rows = _rows(db_path, t)
        if rows:
            con.register("tmp", pa.Table.from_pylist(rows))
            con.execute(f"CREATE TABLE {t} AS SELECT * FROM tmp")
            con.unregister("tmp")
    for t, meta in manifest["parquet"].items():
        con.execute(f"CREATE VIEW v_{t} AS SELECT * FROM read_parquet('{meta['path']}')")
    for t, meta in manifest["json"].items():
        con.execute(f"CREATE VIEW v_{t} AS SELECT * FROM read_json_auto('{meta['path']}')")
    con.close()
    manifest["duckdb"] = duck_path
    return manifest


def generate_minutes(db_path: str, out_dir: str, meeting_id: int = 1) -> dict:
    """DuckDB-powered Meeting Minutes from confirmed transcript segments."""
    import duckdb
    man = archive(db_path, out_dir)
    con = duckdb.connect(man["duckdb"])
    seg = f"SELECT * FROM v_segment WHERE meeting_id={meeting_id}"
    decisions  = [r[0] for r in con.execute(f"SELECT text FROM ({seg}) WHERE category='Decision' AND confirmed=1 ORDER BY ord").fetchall()]
    actions    = [{"text": r[0], "owner": r[1]} for r in con.execute(f"SELECT text, speaker FROM ({seg}) WHERE action=1 ORDER BY ord").fetchall()]
    discussion = [r[0] for r in con.execute(f"SELECT text FROM ({seg}) WHERE category='Discussion' ORDER BY ord").fetchall()]
    risks      = [r[0] for r in con.execute(f"SELECT text FROM ({seg}) WHERE category='Risk' ORDER BY ord").fetchall()]
    cats       = dict(con.execute(f"SELECT category, COUNT(*) FROM ({seg}) GROUP BY category").fetchall())
    con.close()

    summary = (f"本次會議共 {sum(cats.values())} 段,含 {len(decisions)} 項決議、"
               f"{len(actions)} 項行動、{len(risks)} 項風險。")
    minutes = {"meeting_id": meeting_id, "summary": summary, "categories": cats,
               "decisions": decisions, "actions": actions,
               "discussion": discussion, "risks": risks}

    # persist minutes: JSON (config-like) + back into SQLite minutes table
    Path(os.path.join(out_dir, "warehouse")).mkdir(parents=True, exist_ok=True)
    Path(os.path.join(out_dir, "minutes.json")).write_text(
        json.dumps(minutes, ensure_ascii=False, indent=2), encoding="utf-8")
    sc = connect(db_path)
    sc.execute("DELETE FROM minutes WHERE meeting_id=?", (meeting_id,))
    sc.execute("INSERT INTO minutes(meeting_id,summary,actions,decisions,discussion) VALUES(?,?,?,?,?)",
               (meeting_id, summary, json.dumps(actions, ensure_ascii=False),
                json.dumps(decisions, ensure_ascii=False),
                json.dumps(discussion, ensure_ascii=False)))
    sc.commit(); sc.close()
    return minutes


def export_csv(db_path: str, out_dir: str = "output/warehouse") -> list:
    """Export key entities to CSV via DuckDB, UTF-8 **with BOM** so Excel opens
    Traditional Chinese without 亂碼 (mojibake)."""
    import csv
    import duckdb
    man = archive(db_path, out_dir)
    con = duckdb.connect(man["duckdb"])
    targets = {"segment": "v_segment", "ledger": "v_ledger", "weeklog": "v_weeklog",
               "news": "v_news", "task": "task", "risk": "risk",
               "milestone": "milestone", "stakeholder": "v_stakeholder", "plan": "v_plan"}
    out = []
    for name, view in targets.items():
        try:
            cur = con.execute(f"SELECT * FROM {view}")
            cols = [d[0] for d in cur.description]
            rows = cur.fetchall()
        except Exception:
            continue
        path = os.path.join(out_dir, f"{name}.csv")
        with open(path, "w", encoding="utf-8-sig", newline="") as f:  # BOM → no mojibake
            w = csv.writer(f)
            w.writerow(cols)
            w.writerows(rows)
        out.append(path)
    con.close()
    return out


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="output/veritaspulse.db")
    ap.add_argument("--out", default="output")
    a = ap.parse_args()
    m = archive(a.db, os.path.join(a.out, "warehouse"))
    mins = generate_minutes(a.db, a.out)
    print(json.dumps({"parquet": list(m["parquet"]), "json": list(m["json"]),
                      "duckdb": m["duckdb"], "minutes_actions": len(mins["actions"]),
                      "minutes_decisions": len(mins["decisions"])}, ensure_ascii=False, indent=2))
