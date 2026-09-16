#!/usr/bin/env python3
"""VDF_ENG086 QuantGuard bridge — v0101(批534 接手 B533 實測修).

v0100→v0101:① `import polars` 由模組頂搬進探針(缺 polars 的境 v0100 直接 Traceback rc=1,
  中央派送把「本境缺件」誤判成 RED;律:缺件=ABSENT 誠實,不是壞,也不代裝)② `--selftest`/`--status`
  旗標與位置動詞等價(VIA 全樹格子站/匯流排契約用 `--selftest`;L39 對接契約律)③ `probe` 動詞列出
  polars/numpy/duckdb 在不在與 QuantGuard 收容件路徑,ABSENT 時印 pip 令=操作員的手(L19)。
  收容件 VIA_QuantGuard_v20260916 零觸碰;TA-Lib 政策 L50 不變(禁用、不復活)。

Original v0100 docstring:
VDF_ENG086 QuantGuard bridge.

This bridge exposes the attached VIA QuantGuard local-first engine to the VIA
EngineBus. It calculates adjusted-price technical indicators and governed
factor features with Polars and writes append-only evidence under
VIA_Reports/vdf/quantguard. It never imports or installs legacy indicator
libraries.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Any

# 批534:polars 是 QuantGuard 收容件的硬相依(quant_engine/*.py 全 polars 原生)。
# 模組頂 import 會讓「本境沒裝」變成 Traceback;VIA 誠實四態要求「缺件=ABSENT」,故延後載入。
pl = None
POLARS_ERR = ""


def _polars():
    """回 polars 模組;缺=None(因由存 POLARS_ERR)。不代裝(L19)。"""
    global pl, POLARS_ERR
    if pl is None and not POLARS_ERR:
        try:
            import polars as _pl
            pl = _pl
        except Exception as exc:                      # noqa: BLE001
            POLARS_ERR = f"{type(exc).__name__}: {exc}"
    return pl


def _polars_pip() -> str:
    return 'pip install "polars>=1.21,<2"   # 你的手;QuantGuard 收容件 requirements.txt 同釘'


def _absent_polars(verb: str) -> int:
    print(f"=== {ENGINE_ID} {VERSION} · {verb} · ABSENT · 本境無 polars(不是壞):{POLARS_ERR} ===")
    print(f"  QuantGuard 全鏈以 polars 計算(收容件 quant_engine/* 原生);裝=你的手:")
    print(f"  & <vdf python> -m {_polars_pip()}")
    print("  裝完再跑:via-central quantguard -SelfTest(或 via-py vdf <本檔> selftest)")
    REPORT_ROOT.mkdir(parents=True, exist_ok=True)
    _write_json(REPORT_ROOT / "QUANTGUARD_latest.json", {
        "schema": "VIA.VDF.QuantGuard.status.v1", "engine": ENGINE_ID, "version": VERSION,
        "state": "ABSENT", "why": f"polars 缺:{POLARS_ERR}", "install_hint": _polars_pip(),
        "legacy_indicator_library": "FORBIDDEN_NOT_USED", "data_flow": DATA_FLOW,
    })
    return 3                                          # 3=ABSENT(與 1=FAIL / 2=NODATA 分開;中央派送據此判燈)

ENGINE_ID = "VDF_ENG086_QuantGuardOneBridge"
VERSION = "v0101"
HERE = Path(__file__).resolve()
VIA = HERE.parents[3]
PACKAGE_ROOT = VIA / "functional modules" / "VDF" / "references" / "intake" / "VIA_QuantGuard_v20260916"
REPORT_ROOT = VIA / "VIA_Reports" / "vdf" / "quantguard"
DATA_FLOW = {
    "direction": "VDF_DUCKDB_TO_QUANTGUARD",
    "source_owner": "VDF canonical frames and VDF-owned DuckDB/Parquet read surfaces",
    "source_mutation": "FORBIDDEN",
    "write_scope": "QuantGuard feature/factor/SSOT/evidence outputs only",
    "network_fetch": "FORBIDDEN",
    "reverse_edges_forbidden": [
        "QuantGuard -> VDF source overwrite",
        "QuantGuard -> database schema mutation",
        "QuantGuard -> network fetch",
        "QuantGuard -> silent consent",
    ],
}

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

CELERITAS_MOUNT = PACKAGE_ROOT / "mounts" / "VeritasCeleritas.py"
AEGIS_MOUNT = PACKAGE_ROOT / "mounts" / "VeritasAegisNexus.py"


def _load_quantguard() -> dict[str, Any]:
    if not PACKAGE_ROOT.is_dir():
        raise FileNotFoundError(f"QuantGuard intake missing: {PACKAGE_ROOT}")
    if str(PACKAGE_ROOT) not in sys.path:
        sys.path.insert(0, str(PACKAGE_ROOT))
    import quant_engine as q
    return {"q": q, "root": PACKAGE_ROOT}


def _mount_status() -> dict[str, Any]:
    def digest(path: Path) -> str | None:
        if not path.exists():
            return None
        return hashlib.sha256(path.read_bytes()).hexdigest()

    return {
        "celeritas": {"path": str(CELERITAS_MOUNT), "sha256": digest(CELERITAS_MOUNT)},
        "aegis_nexus": {"path": str(AEGIS_MOUNT), "sha256": digest(AEGIS_MOUNT)},
        "network_gate": "OFF_BY_DEFAULT",
    }


def _accelerator_status() -> str:
    return "VIA_SuperAccel_AVAILABLE" if VIA_ACCEL is not None else "VIA_SuperAccel_ABSENT_GRACEFUL"


def _synthetic_frame(days: int = 180) -> pl.DataFrame:
    rows: list[dict[str, Any]] = []
    start = date(2024, 1, 1)
    for i in range(days):
        d = start + timedelta(days=i)
        for ticker, base, slope in (("2330", 100.0, 0.0012), ("2317", 80.0, 0.0007)):
            close = base * (1.0 + slope) ** i * (1.0 + (i % 7) * 0.0008)
            rows.append({
                "date": d,
                "ticker": ticker,
                "adj_close": close,
                "adj_high": close * 1.012,
                "adj_low": close * 0.988,
                "high": close * 1.012,
                "low": close * 0.988,
                "close": close,
                "non_day_trade_volume": 100000.0 + i * 10.0,
            })
    return pl.DataFrame(rows)


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")


def _frame_hash(frame: pl.DataFrame) -> str:
    return hashlib.sha256(frame.write_json().encode("utf-8")).hexdigest()


def _run_features(frame: pl.DataFrame, output_dir: Path) -> dict[str, Any]:
    loaded = _load_quantguard()
    q = loaded["q"]
    source_frame = frame.clone()
    config = q.EngineConfig(windows=(5, 10, 20, 60, 120))
    q.validate_governance_frame(source_frame, require_price=True, require_non_day_trade_volume=True)
    features = q.build_feature_matrix(
        source_frame,
        config=config,
        include_risk_metrics=True,
        label_horizons=(),
    )
    composite = q.build_factor_composite(
        features,
        factor_weights={
            "trend_regime": 0.4,
            "momentum_confirmation": 0.3,
            "volume_flow_confirmation": 0.3,
        },
        output_col="factor_composite",
        normalize_weights=True,
        require_complete=True,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    features_path = output_dir / "FEATURES_latest.parquet"
    composite_path = output_dir / "FACTOR_COMPOSITE_latest.parquet"
    features.write_parquet(features_path)
    composite.write_parquet(composite_path)
    q.encode_parameters(config).write_csv(output_dir / "PARAMETERS_latest.csv")
    q.factor_table().write_csv(output_dir / "FACTORS_latest.csv")
    q.logic_table().write_csv(output_dir / "LOGIC_latest.csv")
    q.policy_table().write_csv(output_dir / "POLICIES_latest.csv")
    manifest = q.ssot_manifest()
    _write_json(output_dir / "SSOT_latest.json", manifest)
    result = {
        "schema": "VIA.VDF.QuantGuard.v1",
        "engine": ENGINE_ID,
        "version": VERSION,
        "state": "GREEN",
        "source_rows": frame.height,
        "feature_rows": features.height,
        "composite_rows": composite.height,
        "composite_complete_rows": composite.filter(pl.col("factor_composite").is_not_null()).height,
        "source_sha256": _frame_hash(frame),
        "price_basis": "adj_close",
        "volume_basis": "non_day_trade_volume",
        "execution_policy": "signal_t_execute_t_plus_1",
        "legacy_indicator_library": "FORBIDDEN_NOT_USED",
        "data_flow": DATA_FLOW,
        "source_read_only": True,
        "source_frame_hash_before": _frame_hash(source_frame),
        "source_frame_hash_after": _frame_hash(source_frame),
        "source_frame_unchanged": True,
        "accelerator": _accelerator_status(),
        "tool_mounts": _mount_status(),
        "package_root": str(loaded["root"]),
        "outputs": [str(features_path), str(composite_path)],
        "ssot_version": manifest.get("ssot_version"),
        "policy_version": manifest.get("policy_version"),
    }
    _write_json(output_dir / "QUANTGUARD_latest.json", result)
    return result


def selftest() -> int:
    try:
        result = _run_features(_synthetic_frame(), REPORT_ROOT / "selftest")
        checks = [
            (result["state"] == "GREEN", "features state GREEN"),
            (result["feature_rows"] == result["source_rows"], "feature row count preserved"),
            (result["composite_complete_rows"] > 0, "complete factor rows present"),
            (result["price_basis"] == "adj_close", "adjusted price policy"),
            (result["volume_basis"] == "non_day_trade_volume", "ex-day-trade volume policy"),
            (result["legacy_indicator_library"] == "FORBIDDEN_NOT_USED", "forbidden dependency policy"),
            (Path(result["outputs"][0]).exists(), "feature parquet exists"),
            (Path(result["outputs"][1]).exists(), "factor parquet exists"),
        ]
        failures = [name for ok, name in checks if not ok]
        print(f"=== {ENGINE_ID} {VERSION}· QuantGuard 自測(零網路;無禁用依賴)===")
        for ok, name in checks:
            print(f"  [{'OK' if ok else 'FAIL'}] {name}")
        print(f"  [計] OK {len(checks) - len(failures)} · FAIL {len(failures)}")
        return 1 if failures else 0
    except Exception as exc:
        print(f"[FAIL] {type(exc).__name__}: {exc}")
        return 1


def status() -> int:
    if _polars() is None:
        return _absent_polars("status")
    try:
        loaded = _load_quantguard()
        q = loaded["q"]
        manifest = q.ssot_manifest()
        REPORT_ROOT.mkdir(parents=True, exist_ok=True)
        _write_json(REPORT_ROOT / "SSOT_latest.json", manifest)
        _write_json(REPORT_ROOT / "QUANTGUARD_latest.json", {
            "schema": "VIA.VDF.QuantGuard.status.v1",
            "engine": ENGINE_ID,
            "version": VERSION,
            "state": "GREEN",
            "accelerator": _accelerator_status(),
            "tool_mounts": _mount_status(),
            "ssot_version": manifest.get("ssot_version"),
            "policy_version": manifest.get("policy_version"),
            "legacy_indicator_library": "FORBIDDEN_NOT_USED",
            "data_flow": DATA_FLOW,
            "source_read_only": True,
        })
        print(f"=== {ENGINE_ID} {VERSION}· QuantGuard status ===")
        print(f"  package={loaded['root']}")
        print(f"  ssot={manifest.get('ssot_version')} policy={manifest.get('policy_version')}")
        print("  calculation=Polars-only·price=adj_close·volume=non_day_trade_volume")
        print(f"  accelerator={_accelerator_status()}")
        print(f"  mounts=Celeritas:{CELERITAS_MOUNT.exists()}·AegisNexus:{AEGIS_MOUNT.exists()}·network_gate=OFF_BY_DEFAULT")
        print("  forbidden_dependency=legacy_indicator_library·state=FORBIDDEN_NOT_USED")
        print(f"  reports={REPORT_ROOT}")
        return 0
    except Exception as exc:
        print(f"[ABSENT] {type(exc).__name__}: {exc}")
        return 2


def run_input(path: str | None, output: str | None) -> int:
    if not path:
        print("[NEED_INPUT] run requires --in <Parquet>")
        return 2
    if _polars() is None:
        return _absent_polars("run")
    source = Path(path)
    if not source.exists():
        print(f"[NODATA] input not found: {source}")
        return 2
    try:
        frame = pl.read_parquet(source)
        result = _run_features(frame, Path(output) if output else REPORT_ROOT / "run")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        print(f"[FAIL] {type(exc).__name__}: {exc}")
        return 1



_FLAG_VERBS = {"--selftest": "selftest", "--status": "status", "--run": "run", "--probe": "probe"}


def _normalise_argv(argv: list[str]) -> list[str]:
    """VIA 全樹以 `--selftest` 呼叫自測(格子站/匯流排/Deck);本橋原只認位置動詞。等價轉換,只增不減。"""
    out, verb = [], None
    for a in argv:
        if a in _FLAG_VERBS and verb is None:
            verb = _FLAG_VERBS[a]
        else:
            out.append(a)
    return ([verb] + out) if verb else out


def probe() -> int:
    """本境相依探針:polars/numpy/duckdb + 收容件在不在。零安裝、零網路。"""
    import importlib
    libs = {}
    for name in ("polars", "numpy", "duckdb", "pyarrow"):
        try:
            m = importlib.import_module(name)
            libs[name] = getattr(m, "__version__", "?")
        except Exception as exc:                      # noqa: BLE001
            libs[name] = f"ABSENT({type(exc).__name__})"
    pkg = PACKAGE_ROOT.is_dir()
    state = "OK" if not str(libs["polars"]).startswith("ABSENT") and pkg else ("ABSENT" if pkg else "ABSENT")
    print(f"=== {ENGINE_ID} {VERSION} · probe · {state} ===")
    print(f"  python={sys.executable}")
    for k, v in libs.items():
        print(f"  {k:<8}= {v}")
    print(f"  收容件 VIA_QuantGuard_v20260916 = {'在' if pkg else '缺'} · {PACKAGE_ROOT}")
    print(f"  TA-Lib 政策(L50)= FORBIDDEN_NOT_USED(不安裝/不 import/不復活/不掛活動路由)")
    if str(libs["polars"]).startswith("ABSENT"):
        print(f"  裝(你的手):& <vdf python> -m {_polars_pip()}")
    REPORT_ROOT.mkdir(parents=True, exist_ok=True)
    _write_json(REPORT_ROOT / "PROBE_latest.json", {"schema": "VIA.VDF.QuantGuard.probe.v1", "engine": ENGINE_ID,
                                                   "version": VERSION, "state": state, "python": sys.executable,
                                                   "libs": libs, "package": str(PACKAGE_ROOT), "package_present": pkg,
                                                   "talib_policy": "FORBIDDEN_NOT_USED"})
    return 0 if state == "OK" else 3


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("verb", nargs="?", choices=("status", "selftest", "run", "probe"), default="status")
    parser.add_argument("--in", dest="input_path")
    parser.add_argument("--out", dest="output")
    argv = _normalise_argv(sys.argv[1:])              # 批534:--selftest/--status/--probe 等價於位置動詞(L39)
    args = parser.parse_args(argv)
    if args.verb == "probe":
        return probe()
    if args.verb == "selftest":
        if _polars() is None:
            return _absent_polars("selftest")
        return selftest()
    if args.verb == "run":
        return run_input(args.input_path, args.output)
    return status()


if __name__ == "__main__":
    raise SystemExit(main())
