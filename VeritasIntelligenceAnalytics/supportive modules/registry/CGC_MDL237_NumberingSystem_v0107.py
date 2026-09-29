"""中央編號 v0107：四來源 SRC 與各來源的 BI/FD 欄位分開登錄；
觀測值由中央規格給穩定 OBS ID，同源多引擎重試不冒充另一來源。
不改歷史號碼；更新 2026-09-29T15:38:10+00:00"""
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
        spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        module = _nb_ilu.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL237_NumberingSystem"
PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if p.name < Path(__file__).name), key=lambda p: p.name)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_v0107", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
BASE = PRIOR.BASE
SOURCE = "supportive modules/registry/VRN_SourceProvenance_SSOT_v0100.json"
HANDOFF = "supportive modules/registry/VIA_Handoff_Continuity_SSOT_v0100.json"
_PRIOR_COLLECT = BASE.collect
if "SRC" not in BASE.KIND_NO:
    BASE.KINDS.append(("SRC", "資料來源通道"))
    BASE.KIND_NO["SRC"] = "K" + str(len(BASE.KINDS)).zfill(2)


def provenance_items():
    book = json.loads((BASE.VIA / SOURCE).read_text(encoding="utf-8"))
    rows = []
    for source in book["sources"]:
        key = source["key"]
        rows.append(BASE.item("SRC", SOURCE + "#" + key, source["name"], "VRN source lane", SOURCE,
                              "VRN_SystemManager provenance", book["updated_at"], "VRN", book["version"],
                              "GREEN", source["scope"], source_lane=key))
        for field in BASE.field_items():
            if field["sub"] == "VRN":
                rows.append(dict(field, key=field["key"] + "|source=" + key,
                                 name=field["name"] + " / " + source["name"],
                                 cat="來源分立/" + field["cat"], source_lane=key,
                                 canonical_field_key=field["key"], source_contract=SOURCE))
    for path in (SOURCE, HANDOFF):
        definition = json.loads((BASE.VIA / path).read_text(encoding="utf-8"))
        for group, kind in (("policies", "PLCY"), ("parameters", "PRMT"),
                            ("test_cases", "LGC"), ("work_items", "LGC"), ("escalation", "LGC")):
            values = definition.get(group, {})
            pairs = (values.items() if isinstance(values, dict) else
                     ((str(v.get("id", v.get("engine", i))), v) for i, v in enumerate(values)))
            for key, value in pairs:
                rows.append(BASE.item(kind, path + "#" + group + "/" + key, key,
                    "交接與來源驗證/" + group, path, group + "/" + key,
                    definition["updated_at"], "VRN" if path == SOURCE else "VCGC",
                    definition["version"], "GREEN", str(value), definition_sha256=hashlib.sha256(
                        json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()))
    unique = {}
    for row in rows:
        unique.setdefault((row["kind"], row["key"], row["version"]), row)
    return list(unique.values())


def collect():
    rows, notes = _PRIOR_COLLECT()
    rows.extend(provenance_items())
    return rows, notes


BASE.collect = collect


def source_catalog():
    """Read the central SRC book; never invent a local sequence or mutate the central allocator."""
    path = BASE._newest(BASE.BOOK_DIR, "VIA_NumberBook_SRC_v*.jsonl")
    if not path:
        raise ValueError("VCGC central source registration required")
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return {row["source_lane"]: row["code"] for row in rows if row.get("source_lane") and row.get("source") == SOURCE}


def observation_id(source_code, document_sha256, locator, field):
    """Stable centrally defined identity; value/engine excluded so retries are not independent sources."""
    if not re.fullmatch(r"VIA-VRN-SRC\d+", source_code) or not re.fullmatch(r"[0-9a-f]{64}", document_sha256):
        raise ValueError("registered source code and document SHA-256 required")
    identity = {"document": document_sha256, "source": source_code, "locator": locator, "field": field}
    digest = hashlib.sha256(json.dumps(identity, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return source_code + "-OBS-" + digest


def __getattr__(name):
    return getattr(PRIOR, name)


def main(argv=None):
    return PRIOR.main(argv)


def selftest():
    # The previous FAC selftest assumed FAC was the final kind. The established kind numbers stay fixed.
    kinds = list(BASE.KINDS)
    BASE.KINDS[:] = [x for x in kinds if x[0] != "SRC"]
    collector = BASE.collect
    BASE.collect = _PRIOR_COLLECT
    try:
        failure = PRIOR.selftest()
    finally:
        BASE.KINDS[:] = kinds
        BASE.collect = collector
    rows = provenance_items()
    sources = [r for r in rows if r["kind"] == "SRC"]
    checks = [len(sources) == 4, len({r["key"] for r in sources}) == 4,
              len({(r["kind"], r["key"]) for r in rows}) == len(rows),
              BASE.KIND_NO["REQ"] == "K24", BASE.KIND_NO["FAC"] == "K25", BASE.KIND_NO["SRC"] == "K26"]
    doc = "a" * 64
    a = observation_id("VIA-VRN-SRC001", doc, {"page": 1}, "ticker")
    checks += [a == observation_id("VIA-VRN-SRC001", doc, {"page": 1}, "ticker"),
               a != observation_id("VIA-VRN-SRC002", doc, {"page": 1}, "ticker"),
               a != observation_id("VIA-VRN-SRC001", doc, {"page": 2}, "ticker")]
    if not all(checks):
        print("[來源編號失敗項] " + str([i + 1 for i, ok in enumerate(checks) if not ok]))
    print("[來源編號] checks=" + str(len(checks)) + "; fail=" + str(sum(not x for x in checks)))
    return int(bool(failure) or not all(checks))


if __name__ == "__main__":
    raise SystemExit(selftest() if sys.argv[1:] == ["--selftest"] else main())
