#!/usr/bin/env python3
"""VeritasPulse — build everything (interactive app + project deck)."""
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
import argparse, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vpl.core import store
from vpl.core import archive
from vpl.app import build_app
from vpl.ppt import generate
from vpl.meeting import minutes_doc, excel_template
from vpl import config as vplconfig


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="output/veritaspulse.db")
    ap.add_argument("--out", default="output")
    ap.add_argument("--pid", type=int, default=1)
    a = ap.parse_args()

    t0 = time.time()
    os.makedirs(a.out, exist_ok=True)
    vplconfig.write_default(a.out)        # flexible config surface
    store.init_db(a.db, seed=True)
    # storage layer: mirror to Parquet/JSON/DuckDB warehouse + generate minutes
    man = archive.archive(a.db, os.path.join(a.out, "warehouse"))
    archive.generate_minutes(a.db, a.out)
    csvs = archive.export_csv(a.db, os.path.join(a.out, "warehouse"))
    # professional meeting deliverables
    mins = minutes_doc.build(a.db, a.out, mode="comprehensive")
    xls = excel_template.build(a.db, a.out)
    app = build_app.build(a.db, a.out, project_id=a.pid)
    deck = generate.build(store.load_project(a.db, a.pid), a.out)
    print(f"[VPL] warehouse: parquet={list(man['parquet'])} json={list(man['json'])} duckdb=ok")
    print(f"[VPL] csv     : {len(csvs)} files (UTF-8 BOM)")
    print(f"[VPL] minutes: {mins['html']} + {mins['pdf']}")
    print(f"[VPL] excel  : {xls}")
    print(f"[VPL] app : {app}")
    print(f"[VPL] deck: {deck}")
    print(f"[VPL] built in {time.time()-t0:.2f}s")


if __name__ == "__main__":
    main()
