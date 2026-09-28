#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_ENG230_ForwardValuation v0101 — 薄尾:FactSet 候選表一律建表(沒候選 = 0 列,不是「冊上有、庫裡沒有」)

R17-b 工作站實跑(2026-09-28 17:10):⑥ Forward PER OK,但 DB 面板 HIGH「vdf_global_market.duckdb ·
fwd_valuation_factset_candidates 冊上宣告,庫裡沒有這張表」。原因:v0100 只在 B 真的產出候選時才寫這張表
(upsert_rows 空批次不建表);這一趟 FactSet 沒有候選 → 表從沒建過。冊下限是 0 —— 「這趟沒有候選」是合法結論,不是壞。

本尾版:run 真的跑過(不是 dry、不是 DENY、收容件 sha 相符)之後,候選表不在就照 B 的
FactSetValuationCandidate 欄位建空表(float→DOUBLE · bool→BOOLEAN · 其餘 VARCHAR;與 v0100 _cand_row 寫入的型一致)。
  · 同意閘沒開 = DENY:照舊零寫入、庫不建(v0100 ⑩ 原樣)。
  · 有候選時照 v0100 寫(鍵 raw_document_hash);先建的空表與後來寫入的列型相容(自測 ⑯)。
其餘全照 v0100(L04 舊版一字不動;兩支收容件原位元不動)。

用法同 v0100(經 VCGC;VIA_FROM_VCGC=YES):status · run [--days N] [--dry] · --selftest
"""
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
# ===== [VIA:LIB-BRIDGE:v0100] 三庫正典橋(批597;缺席大聲拋,不 graceful) =====
import sys as _lb_sys
from pathlib import Path as _lb_Path
_lb_p = _lb_Path(__file__).resolve()
while _lb_p.parent != _lb_p:
    if (_lb_p / "supportive modules").is_dir():
        _lb_sys.path.insert(0, str(_lb_p / "supportive modules"))
        break
    _lb_p = _lb_p.parent
import VIA_LibCanon as _LIB          # 正典缺席=大聲拋,不假裝有(LL151)
# ===== [VIA:LIB-BRIDGE:END] =====
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
        spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        module = _nb_ilu.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import dataclasses
import importlib.util
import json
import os
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_ENG230_ForwardValuation"
PRIOR_PATH = [p for p in sorted(HERE.glob(_STEM + "_v*.py")) if p.name < Path(__file__).name][-1]
_spec = importlib.util.spec_from_file_location("vdf_eng230_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)

ENGINE_TAG = _STEM + "_v" + Path(__file__).stem.rsplit("_v", 1)[-1]
PRIOR.ENGINE_TAG = ENGINE_TAG
T_CAND = PRIOR.T_CAND


def cand_schema() -> str:
    """B 的 FactSetValuationCandidate 欄位 → DuckDB 欄宣告(註記是字串:B 開了 __future__ annotations)。"""
    cols = []
    for f in dataclasses.fields(PRIOR.B.FactSetValuationCandidate):
        t = str(f.type)
        typ = "BOOLEAN" if t.strip() == "bool" else ("DOUBLE" if t.split("|")[0].strip() == "float" else "VARCHAR")
        cols.append(f'"{f.name}" {typ}')
    return ", ".join(cols)


def ensure_cand_table(db: Path) -> str:
    """候選表不在就建空表。回 created / present。"""
    import duckdb
    db = Path(db)
    db.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(db))
    try:
        if T_CAND in {r[0] for r in con.execute("SHOW TABLES").fetchall()}:
            return "present"
        con.execute(f'CREATE TABLE IF NOT EXISTS "{T_CAND}" ({cand_schema()})')
        return "created"
    finally:
        con.close()


_PRIOR_RUN = PRIOR.run


def run(days: int = 400, net=None, db: Path = None, out_dir: Path = None, dry: bool = False, tp=None) -> dict:
    db = Path(db) if db is not None else PRIOR.OUT_DB
    out_dir = Path(out_dir) if out_dir is not None else PRIOR.OUT_DIR
    r = _PRIOR_RUN(days=days, net=net, db=db, out_dir=out_dir, dry=dry, tp=tp)
    if not dry and r.get("state") != "DENY" and "why" not in r:
        r.setdefault("stored", {})["cand_table"] = ensure_cand_table(db)
        rep = out_dir / "FWDVAL_latest.json"
        if rep.is_file():
            rep.write_text(json.dumps(r, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    return r


PRIOR.run = run                  # v0100 的 main / 自測呼叫的 run 一律走本尾版


def __getattr__(name):
    return getattr(PRIOR, name)


def selftest() -> int:
    rc = PRIOR.selftest()
    results = []

    def chk(name, ok, note=""):
        results.append(bool(ok))
        print(f"  [{'OK' if ok else 'FAIL'}] {name}{(' · ' + note) if note else ''}")

    print(f"=== {ENGINE_TAG} 薄尾加檢(候選表一律建表)===")
    import duckdb
    no_factset = {k: v for k, v in PRIOR._fixtures("<html></html>").items() if "factset" not in k}
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        r = run(days=30, net=PRIOR._FakeNet(no_factset), db=td / "gl.duckdb", out_dir=td / "out")
        con = duckdb.connect(str(td / "gl.duckdb"), read_only=True)
        try:
            tabs = {x[0] for x in con.execute("SHOW TABLES").fetchall()}
            n = con.execute(f'SELECT count(*) FROM "{T_CAND}"').fetchone()[0] if T_CAND in tabs else None
            types = {x[0]: x[1] for x in con.execute(f'DESCRIBE "{T_CAND}"').fetchall()} if T_CAND in tabs else {}
        finally:
            con.close()
        chk("⑭ FactSet 沒候選 → 候選表照樣建(0 列),面板不再報「冊上有、庫裡沒有」", r["factset_gate"]["action"] == "NONE" and n == 0
            and r["stored"].get("cand_table") == "created", f"{r['factset_gate']['action']} · 列 {n} · {r['stored'].get('cand_table')}")
        chk("⑮ 欄型照 B 的候選欄位(float→DOUBLE · bool→BOOLEAN · 其餘 VARCHAR)", types.get("published_forward_pe") == "DOUBLE"
            and types.get("is_approximate") == "BOOLEAN" and types.get("raw_document_hash") == "VARCHAR"
            and len(types) == len(dataclasses.fields(PRIOR.B.FactSetValuationCandidate)), f"{len(types)} 欄")
        from datetime import date, datetime, timezone
        vals = {"publication_ts_utc": datetime(2026, 9, 26, 12, tzinfo=timezone.utc), "retrieved_ts_utc": datetime(2026, 9, 27, tzinfo=timezone.utc),
                "source_as_of_date": date(2026, 9, 25), "available_from_date": date(2026, 9, 26), "date_precision_only": False,
                "published_forward_pe": 22.4, "forward_eps_points_reported": 306.25, "index_level_anchor": 6860.0,
                "published_forward_pe_increment": 0.1, "is_approximate": False, "extraction_confidence": 0.95,
                "extraction_warnings": ("w1",), "extraction_pattern_id": None, "extraction_excerpt": None}
        cand = PRIOR.B.FactSetValuationCandidate(**{f.name: vals.get(f.name, "x" if f.name != "raw_document_hash" else "h1")
                                                    for f in dataclasses.fields(PRIOR.B.FactSetValuationCandidate)})
        st = PRIOR.persist([], {"candidate": cand}, td / "gl.duckdb")
        con = duckdb.connect(str(td / "gl.duckdb"), read_only=True)
        try:
            got = con.execute(f'SELECT published_forward_pe, is_approximate, extraction_warnings FROM "{T_CAND}"').fetchall()
        finally:
            con.close()
        chk("⑯ 先建的空表收得下 v0100 寫法的真候選列(型相容)", st["cand_new"] == 1 and got and got[0][0] == 22.4 and got[0][1] is False, str(got))
        r2 = run(days=30, net=PRIOR._FakeNet({}, deny=True), db=td / "g2.duckdb", out_dir=td / "o2")
        chk("⑰ 同意閘沒開 = DENY:照舊零寫入、庫不建(不為了建空表破例)", r2["state"] == "DENY" and not (td / "g2.duckdb").exists()
            and "cand_table" not in r2.get("stored", {}))
        r3 = run(days=30, net=PRIOR._FakeNet(no_factset), db=td / "g3.duckdb", out_dir=td / "o3", dry=True)
        chk("⑱ --dry 不建表", not (td / "g3.duckdb").exists())
    ok = rc == 0 and all(results)
    print(f"  [計] {ENGINE_TAG} 薄尾 {sum(results)}/{len(results)} · v0100 本體 {'PASS' if rc == 0 else 'FAIL'} · 合計 {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in a:
        return selftest()
    return PRIOR.main(a)


if __name__ == "__main__":
    raise SystemExit(main())
