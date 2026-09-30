"""VDF_ENG054 台股日價回補：明確派送、參數證據與只增不減。

狀態檢查不冒充更新；抓取仍使用既有本體、網路閘與中央 upsert。
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


import argparse
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
import uuid

# def 01_PARAMETERS
HERE = Path(__file__).resolve().parent
VIA = HERE.parents[2]
REG = VIA / "supportive modules" / "registry"
VERSION = "v0112"
STEM = "VDF_ENG054_TWDailyBackfill"
DB_NAME = "vdf_tw_market.duckdb"
DB_ENV = "VIA_DB_VDF_TW_MARKET"
SPEC_PATH = REG / "VIA_InputConsole_Spec_v0100.json"
UNIFIED_PATH = HERE.parent / "VDF_Unified_Params_v0100.json"
HEADER_PATTERN = "VIA_VDF_SSOT_b*/vdf_fetch_matrix.json"
PRIOR_PATH = max(p for p in HERE.glob(STEM + "_v*.py") if p.name < Path(__file__).name)


def _module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


PRIOR = _module(PRIOR_PATH, "vdf_backfill_prior_112")


def __getattr__(name):
    return getattr(PRIOR, name)


def _json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def _database(explicit=None):
    """沿用資料家與唯一庫掃描器；不在倉內另造正式庫。"""
    datahome = _module(max(REG.glob("CGC_MDL123_DataHome_v*.py")), "vdf112_datahome")
    chosen = explicit or os.environ.get(DB_ENV)
    if chosen:
        db = Path(chosen).expanduser()
        ok, why = datahome.home_usable(db)
        if not ok or db.suffix.lower() != ".duckdb" or not db.parent.is_dir():
            raise ValueError("資料庫路徑不可用: " + why)
        return db, "--db" if explicit else "env " + DB_ENV
    bus = _module(max(REG.glob("CGC_MDL148_EngineBus_v*.py")), "vdf112_bus")
    home, source = bus.data_home()
    if home is None:
        raise ValueError("資料家尚未就緒: " + source)
    ok, why = datahome.home_usable(home)
    if not ok:
        raise ValueError(why)
    if home.is_file():
        if home.name != DB_NAME:
            raise ValueError("資料家單檔不是 " + DB_NAME)
        return home, source
    candidates = [p for p in bus.db_files() if p.name == DB_NAME and p.resolve().is_relative_to(home.resolve())]
    if len(candidates) > 1:
        raise ValueError("資料家有多本同名正庫；請明確指定 --db")
    return (candidates[0] if candidates else home / DB_NAME), source


def _preserve_etfs(keep):
    """舊資料完整保留；本輪清單選擇只影響新增抓取。"""
    return {"listings": 0, "prices": 0, "policy": "append_only", "selected": len(keep)}


def _prepared(explicit=None):
    body = PRIOR._load()
    body.DB_TW, source = _database(explicit)
    body.OUT = body.DB_TW.parent / "tw_backfill_snapshots"
    body.CKPT = body.DB_TW.parent / "tw_backfill_checkpoint.json"
    connect = body.connect_retry
    writer = body.write_parquet

    def connect_retry(path=None, read_only=False):
        return connect(body.DB_TW if path is None else path, read_only=read_only)

    def write_parquet(rows, stem):
        # CSV fallback must retain fields present only in later nullable rows.
        fields = list(dict.fromkeys(key for row in rows for key in row))
        normalized = [{key: row.get(key) for key in fields} for row in rows]
        return writer(normalized, stem + "_" + uuid.uuid4().hex)

    body.connect_retry = connect_retry
    body.write_parquet = write_parquet
    body.purge_other_etfs = _preserve_etfs
    return body, source


def contract():
    """只讀正主宣告；不把規格欄位或不同日期當作主機實測。"""
    body = PRIOR._load()
    spec = _json(SPEC_PATH)
    unified = _json(UNIFIED_PATH)
    group = next(g for g in spec["families"]["vdf"]["groups"] if g["id"] == "tw_equity")
    item = next(i for i in group["items"] if i["id"] == "tw_prices_inc")
    header_path = max((HERE.parent / "references" / "intake").glob(HEADER_PATTERN))
    header = _json(header_path)
    ddl = body.PRICE_DDL.split("(", 1)[1].rsplit(")", 1)[0]
    raw = [{"name": c.strip().split()[0], "dtype": c.strip().split()[1]} for c in ddl.split(",")]
    return {
        "schema": "VIA.VDF.BackfillContract.v1", "engine": Path(__file__).stem,
        "owner": Path(body.__file__).name, "item": item["id"],
        "dispatch": {"default": "status", "status": "read_only", "run": "existing_fetch_with_append_only_adapter"},
        "parameters": {"central_default_start": spec["defaults"].get("start"),
                       "group_start": spec.get("user", {}).get("group_starts", {}).get("tw_equity"),
                       "item_start": spec.get("user", {}).get("starts", {}).get(item["id"]),
                       "declared_item_params": item.get("params", []),
                       "unified_start": unified["time"]["start_date"],
                       "empty_ticker_start": body.START_DATE, "overlap_days": body.OVERLAP_DAYS,
                       "start_rule": "MAX(date) minus overlap; empty ticker uses engine start; item exposes no start/end",
                       "accepted_run_flags": ["--db", "--limit", "--full"]},
        "headers": {"raw_table": "tw_daily_prices", "raw_ddl": raw,
                    "target_prices_core": header["unified_headers"]["prices_core"],
                    "target_source": header_path.relative_to(VIA).as_posix(),
                    "actual_database_verified": False, "actual_parquet_verified": False,
                    "mapping_verified": False, "state": "DECLARED_ONLY"},
        "append_only": {"etf_purge": False, "replace_existing_rows": False, "unique_snapshot_names": True},
        "sources": [SPEC_PATH.relative_to(VIA).as_posix(), UNIFIED_PATH.relative_to(VIA).as_posix()],
        "production_database_verified": False,
    }


def run(limit=None, full=False, db=None):
    body, source = _prepared(db)
    if not body.gate_open():
        print("[GATED] 原網路同意閘未開；未抓取、未寫入")
        return 2
    stats = {"groups": 0, "rows": 0, "failed": 0}
    fetch = body._fetch_group

    def tracked_fetch(*args, **kwargs):
        result = fetch(*args, **kwargs)
        stats["groups"] += 1
        stats["rows"] += len(result.get("rows") or [])
        stats["failed"] += len(result.get("failed") or [])
        return result

    body._fetch_group = tracked_fetch
    print(json.dumps({"operation": "run", "database": str(body.DB_TW), "source": source,
                      "empty_ticker_start": body.START_DATE, "append_only": True}, ensure_ascii=False))
    try:
        rc = body.run(limit=limit, full=full)
    except body.DbBusy as exc:
        print("[DB_BUSY] " + str(exc))
        return 3
    if rc == 0 and (stats["failed"] or (stats["groups"] and not stats["rows"])):
        rc = 2
    print(json.dumps({"operation": "run", "rc": rc, "fetch_results": stats,
                      "production_acceptance": "NOT_EVALUATED"}, ensure_ascii=False))
    return rc


def status(db=None):
    """沿用既有狀態尺，只改資料庫定位；零抓取零建庫。"""
    body, source = _prepared(db)
    owner = PRIOR.PRIOR
    original = owner._load
    try:
        owner._load = lambda: body
        card = owner.db_status()
    finally:
        owner._load = original
    card.update(door=Path(__file__).stem, operation="status", database_source=source,
                data_updated=False, production_acceptance="NOT_EVALUATED")
    print(json.dumps(card, ensure_ascii=False, indent=1))
    return 0 if card["lock_success"] else 2


def _positive(value):
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be positive")
    return parsed


def main(argv=None):
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print("[DENY] 只能經 VCGC")
        return 2
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("verb", nargs="?", choices=("status", "run", "contract"), default="status")
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--db")
    parser.add_argument("--limit", type=_positive)
    parser.add_argument("--full", action="store_true")
    args = parser.parse_args(argv)
    if args.__dict__["selftest"]:
        if args.verb != "status" or args.status or args.db or args.limit or args.full:
            parser.error("--selftest cannot be combined with execution arguments")
        return selftest()
    if args.status and args.verb != "status":
        parser.error("--status conflicts with verb")
    if args.verb != "run" and (args.limit is not None or args.full):
        parser.error("--limit / --full require run")
    if args.verb == "contract" and args.db:
        parser.error("contract reads declarations; --db belongs to status/run")
    if args.verb == "contract":
        print(json.dumps(contract(), ensure_ascii=False, indent=1))
        return 0
    try:
        return run(args.limit, args.full, args.db) if args.verb == "run" else status(args.db)
    except (ValueError, OSError) as exc:
        print("[ABSENT] " + str(exc))
        return 2


def selftest():
    prior_rc = PRIOR.selftest()
    tests = _module(HERE.parent / "tests" / "test_backfill_dispatch_v0100.py", "vdf112_tests")
    return max(prior_rc, tests.run_tests(sys.modules[__name__]))


if __name__ == "__main__":
    raise SystemExit(main())
