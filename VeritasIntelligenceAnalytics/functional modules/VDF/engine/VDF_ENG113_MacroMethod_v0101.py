#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Same Fed-method refresh. The live us_macro table has three columns; add fetched_at, do not rebuild it."""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(批102 全樹導入令;graceful 零行為變更) =====
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
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====
# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 VDF 全導入令;graceful 零行為變更) =====
VIA_NET_TOOL_PATH = None
try:
    from pathlib import Path as _nb_Path
    _nb_p = _nb_Path(__file__).resolve()
    while _nb_p.parent != _nb_p:
        _nb_dir = _nb_p / "supportive modules" / "network"
        if _nb_dir.exists():
            _nb_hits = sorted(_nb_dir.glob("via_net_unified_v*.py"))
            if _nb_hits:
                VIA_NET_TOOL_PATH = str(_nb_hits[-1])
            break
        _nb_p = _nb_p.parent
except Exception:
    VIA_NET_TOOL_PATH = None


def _via_net():
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        _nb_spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        _nb_mod = _nb_ilu.module_from_spec(_nb_spec)
        _nb_spec.loader.exec_module(_nb_mod)
        return _nb_mod
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import importlib.util
import json
import os
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _prior():
    spec = importlib.util.spec_from_file_location("method_v0100", HERE / "VDF_ENG113_MacroMethod_v0100.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _ensure(con) -> list[str]:
    con.execute("CREATE TABLE IF NOT EXISTS us_macro (date DATE, series VARCHAR, value DOUBLE, fetched_at TIMESTAMP)")
    names = [row[0] for row in con.execute("DESCRIBE us_macro").fetchall()]
    if "fetched_at" not in names:
        con.execute("ALTER TABLE us_macro ADD COLUMN fetched_at TIMESTAMP")
        names.append("fetched_at")
    return names


def _write(con, series: str, rows: list[tuple[str, float]], since: str, now: datetime) -> None:
    con.execute("BEGIN")
    try:
        con.execute("DELETE FROM us_macro WHERE series = ? AND date >= ?", [series, since])
        con.executemany(
            "INSERT INTO us_macro (date, series, value, fetched_at) VALUES (?, ?, ?, ?)",
            [(d, series, v, now) for d, v in rows],
        )
        con.execute("COMMIT")
    except Exception:
        con.execute("ROLLBACK")
        raise


def refresh() -> dict:
    prior = _prior()
    import duckdb
    book = prior.load()
    key = os.environ.get("FRED_API_KEY", "")
    if not key:
        return {"via": "vcgc", "state": "DENY", "why": "FRED_API_KEY is not set"}
    prior.OUT.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(prior.DB))
    _ensure(con)
    now = datetime.now()
    wrote = []
    for sid in prior.fred_ids(book):
        rows = prior._fred(key, sid, book["since"])
        _write(con, sid, rows, book["since"], now)
        wrote.append({"series": sid, "n": len(rows), "last": rows[-1][0] if rows else None})
    dts = prior._dts(book["since"])
    _write(con, "DTS_TGA_CLOSE", dts, book["since"], now)
    n = con.execute("SELECT COUNT(*) FROM us_macro").fetchone()[0]
    con.close()
    return {
        "via": "vcgc",
        "door": "VDF_ENG113_MacroMethod_v0101",
        "state": "OK",
        "db": str(prior.DB),
        "rows": n,
        "series": wrote,
        "dts": len(dts),
        "columns": ["date", "series", "value", "fetched_at"],
        "intake_edited": False,
        "do_not": book["do_not"],
        "next": "none",
    }


def main() -> int:
    prior = _prior()
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY"}, ensure_ascii=False))
        return 2
    if "--refresh" in sys.argv:
        card = refresh()
    else:
        card = prior.check()
        card["door"] = "VDF_ENG113_MacroMethod_v0101"
        card["next"] = "refresh"
    print(json.dumps(card, ensure_ascii=False, indent=1))
    return 0 if card.get("state", "OK") != "DENY" else 2


def selftest() -> int:
    import duckdb
    path = Path("/tmp/us_macro_v0101.duckdb")
    if path.exists():
        path.unlink()
    con = duckdb.connect(str(path))
    con.execute("CREATE TABLE us_macro (date DATE, series VARCHAR, value DOUBLE)")
    con.execute("INSERT INTO us_macro VALUES ('2019-01-01', 'WALCL', 1.0)")
    names = _ensure(con)
    _write(con, "WALCL", [("2020-01-02", 2.0)], "2020-01-01", datetime(2026, 9, 27))
    kept = con.execute("SELECT COUNT(*) FROM us_macro WHERE date < '2020-01-01'").fetchone()[0]
    added = con.execute("SELECT value, fetched_at IS NOT NULL FROM us_macro WHERE series = 'WALCL' AND date >= '2020-01-01'").fetchone()
    con.close()
    path.unlink()
    ok = "fetched_at" in names and kept == 1 and added[0] == 2.0 and added[1] is True
    print("  [OK]" if ok else "  [FAIL]")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
