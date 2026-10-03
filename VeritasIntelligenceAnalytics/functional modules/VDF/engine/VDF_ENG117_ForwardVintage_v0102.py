#!/usr/bin/env python3
"""ForwardVintage v0102: compatible --selftest alias, preserve canonical calculation."""
from __future__ import annotations
import importlib.util, sys, os, json, tempfile
from datetime import datetime, timezone
from pathlib import Path
HERE=Path(__file__).resolve()
PRIOR_PATH=HERE.with_name('VDF_ENG117_ForwardVintage_v0101.py')
_PRIOR=None
# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(VDF 全導入令;惰性載入=import 時零網路、零行為變更) =====
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
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT;網路只認 AegisNexus);缺席回 None(誠實)"""
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
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(全樹導入令;graceful 零行為變更) =====
try:
    _sa_p = HERE
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

def prior():
    global _PRIOR
    if _PRIOR is None:
        spec=importlib.util.spec_from_file_location('forward_vintage_prior',PRIOR_PATH)
        _PRIOR=importlib.util.module_from_spec(spec);sys.modules[spec.name]=_PRIOR;spec.loader.exec_module(_PRIOR)
        _PRIOR.append_immutable_parquet_part=append_immutable_parquet_part
    return _PRIOR


def __getattr__(name):
    return getattr(prior(),name)


def append_immutable_parquet_part(
    frame: pd.DataFrame,
    dataset_dir: str | Path,
    dataset_name: str,
) -> dict[str, Any]:
    """Write one new immutable Parquet part plus an append-only JSONL manifest."""
    mod=prior()
    import duckdb
    if frame.empty:
        return {"status": "skipped_empty", "rows": 0}

    target_dir = Path(dataset_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    before_hashes = mod._snapshot_part_hashes(target_dir)
    payload_hash = mod._canonical_dataframe_hash(frame)
    schema_hash = mod._dataframe_schema_hash(frame)
    minimum_date, maximum_date = mod._dataframe_date_bounds(frame)
    part_name = f"part-{payload_hash[:20]}.parquet"
    target_path = target_dir / part_name

    if target_path.exists():
        return {
            "status": "skipped_idempotent",
            "rows": len(frame),
            "part": str(target_path),
            "payload_hash": payload_hash,
        }

    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            prefix="pending-",
            suffix=".parquet",
            dir=target_dir,
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)
        with duckdb.connect(':memory:') as connection:
            connection.from_df(frame).write_parquet(str(temporary_path))
        os.replace(temporary_path, target_path)
        temporary_path = None
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()

    after_hashes = mod._snapshot_part_hashes(target_dir)
    for name, old_hash in before_hashes.items():
        if after_hashes.get(name) != old_hash:
            raise RuntimeError(f"Existing Parquet part changed: {name}")
    if part_name not in after_hashes:
        raise RuntimeError("New Parquet part was not committed")
    if len(after_hashes) != len(before_hashes) + 1:
        raise RuntimeError("Expected exactly one new Parquet part")

    manifest_path = target_dir / "manifest.jsonl"
    manifest_record = {
        "dataset": dataset_name,
        "part": part_name,
        "rows": len(frame),
        "payload_hash": payload_hash,
        "file_sha256": after_hashes[part_name],
        "schema_hash": schema_hash,
        "minimum_date": minimum_date,
        "maximum_date": maximum_date,
        "committed_ts_utc": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "methodology_version": mod.METHODOLOGY_VERSION,
        "status": "committed",
    }
    with manifest_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(manifest_record, ensure_ascii=False) + "\n")

    return {"status": "committed", **manifest_record, "path": str(target_path)}

def selftest():
    result=prior().run_self_test()
    print(json.dumps(result,ensure_ascii=False,default=str))
    ok=result.get('status')=='pass'
    print('[計] OK 1 · FAIL 0' if ok else '[計] OK 0 · FAIL 1')
    return 0 if ok else 1


def main():
    if os.environ.get('VIA_FROM_VCGC')!='YES':
        print('[GATED] ONLY_VIA_ENTRY');return 2
    if sys.argv[1:] in (['--selftest'],['--self-test']):
        try:
            return selftest()
        except (ImportError,ModuleNotFoundError) as exc:
            print('[ABSENT] '+str(exc));return 3
    return prior().main()


if __name__=='__main__':
    raise SystemExit(main())
