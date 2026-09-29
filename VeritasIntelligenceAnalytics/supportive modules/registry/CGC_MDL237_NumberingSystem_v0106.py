"""NumberingSystem v0106 — register the active QuantGuard SSOT by reference.

Adds FAC after existing kinds, without changing any existing kind or number.
The active VDF QuantGuard bridge already consumes this frozen source book.
Central rows point to its declared factors, logic, parameters and policies;
formulas and rules remain in the original SSOT and are never copied or executed.
No TA-Lib, Polars, OCR, network, database or installation is needed for discovery.
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


def _vnum(path):
    m = re.search(r"_v(\d+)$", Path(path).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py")
                  if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
BASE = PRIOR.BASE
SOURCE = "functional modules/VDF/references/intake/VIA_QuantGuard_v20260916/ssot/quant_engine_ssot.json"
OWNER = "VDF_ENG086_QuantGuardOneBridge"
_GROUPS = (("factor_library", "FAC"), ("indicator_logic_library", "LGC"),
           ("parameter_policies", "PRMT"), ("market_policies", "PLCY"),
           ("global_invariants", "PLCY"))
if "FAC" not in BASE.KIND_NO:
    BASE.KINDS.append(("FAC", "計算因子"))
    BASE.KIND_NO["FAC"] = "K" + str(len(BASE.KINDS)).zfill(2)
_PRIOR_COLLECT = BASE.collect


def quantguard_items(book=None):
    data = json.loads((BASE.VIA / SOURCE).read_text(encoding="utf-8")) if book is None else book
    if not data.get("ssot_version") or not data.get("policy_version"):
        raise ValueError("QuantGuard SSOT must declare its versions")
    rows = []
    for group, kind in _GROUPS:
        definitions = data[group]
        if isinstance(definitions, list):
            pairs = [(r["code"], r) for r in definitions]
        elif isinstance(definitions, dict):
            pairs = list(definitions.items())
        else:
            raise ValueError("Invalid declared library: " + group)
        if len({str(k) for k, _ in pairs}) != len(pairs):
            raise ValueError("Duplicate declared keys: " + group)
        for key, definition in pairs:
            escaped = str(key).replace("~", "~0").replace("/", "~1")
            # Lists use stable declared-code selectors rather than unstable array indices.
            pointer = group + ("[code=" + str(key) + "]" if isinstance(definitions, list) else "/" + escaped)
            version = data["policy_version"] if kind == "PLCY" else data["ssot_version"]
            name = definition.get("name_zh", str(key)) if isinstance(definition, dict) else str(key)
            rows.append(BASE.item(kind, SOURCE + "#" + pointer, name, "QuantGuard/" + group,
                                  SOURCE, OWNER + " → ssot_manifest()#" + pointer,
                                  BASE.updated(SOURCE), "VDF", version, "GREEN",
                                  "宣告已登記；不代表因子計算或資料庫實測通過",
                                  declared_code=str(key), source_pointer=pointer, owner_engine=OWNER,
                                  definition_sha256=hashlib.sha256(json.dumps(definition, ensure_ascii=False,
                                      sort_keys=True, separators=(",", ":")).encode()).hexdigest()))
    return rows


def collect():
    rows, notes = _PRIOR_COLLECT()
    rows.extend(quantguard_items())
    return rows, notes


BASE.collect = collect


def __getattr__(name):
    return getattr(PRIOR, name)


def main(argv=None):
    return PRIOR.main(argv)


def selftest():
    failure = PRIOR.selftest()
    checks = []
    rows = quantguard_items()
    checks.append(("原冊 7 因子／30 邏輯／14 參數／12 政策", {k:sum(r["kind"] == k for r in rows) for k in ("FAC","LGC","PRMT","PLCY")} == {"FAC":7,"LGC":30,"PRMT":14,"PLCY":12}))
    checks.append(("有唯一來源鍵與宣告版號", len({(r["kind"], r["key"]) for r in rows}) == len(rows) and all(r["version"] and r["source_pointer"] for r in rows)))
    checks.append(("只存來源與指紋，未複製公式", all("formula" not in r and r["owner_engine"] == OWNER and len(r["definition_sha256"]) == 64 for r in rows)))
    checks.append(("FAC 追加於既有類別之後", BASE.KINDS[-1][0] == "FAC" and BASE.KIND_NO["REQ"] == "K24"))
    checks.append(("仍使用中央收集器和編號器", BASE.collect is collect and callable(BASE.assign)))
    fixture = {"ssot_version":"v1", "policy_version":"p1", "factor_library":{}, "indicator_logic_library":{},
               "parameter_policies":[{"code":"A"},{"code":"A"}], "market_policies":{}, "global_invariants":{}}
    try:
        quantguard_items(fixture)
        duplicate_rejected = False
    except ValueError:
        duplicate_rejected = True
    checks.append(("來源重號拒絕假綠", duplicate_rejected))
    for name, ok in checks:
        print(("[OK] " if ok else "[FAIL] ") + name)
    print("[因子 SSOT] " + str(sum(ok for _,ok in checks)) + "/6; inherited rc=" + str(failure))
    return 1 if failure or not all(ok for _,ok in checks) else 0


if __name__ == "__main__":
    raise SystemExit(selftest() if sys.argv[1:] == ["--selftest"] else main())
