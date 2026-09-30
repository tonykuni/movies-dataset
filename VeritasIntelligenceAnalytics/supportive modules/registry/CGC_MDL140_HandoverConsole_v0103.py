"""交接 v0103：活入口仍由元件冊管理，保留依賴另核對中央歷史編號與冊指紋。"""
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


import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
STEM = "CGC_MDL140_HandoverConsole"
PRIOR_PATH = max(p for p in HERE.glob(STEM + "_v*.py") if p.name < Path(__file__).name)
_spec = importlib.util.spec_from_file_location("handoff_prior_103", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
_OWNER = PRIOR.audit.__globals__
_AUDIT = PRIOR.audit
_READ = PRIOR.read


def __getattr__(name):
    return getattr(PRIOR, name)


def historical_registration(via, policy, inventory):
    """只認已宣告的同族舊依賴；活入口在元件冊，歷史列在指紋吻合的中央 MDL/ENG 冊。"""
    via = Path(via)
    active = {row.get("source") for row in inventory.get("records", []) if row.get("state") == "ACTIVE"}
    books = sorted((via / "supportive modules/registry").glob("VIA_Numbering_SSOT_v*.json"))
    if not books:
        return []
    ssot = _READ(books[-1])
    numbered = []
    for kind in ("MDL", "ENG"):
        meta = ssot.get("books", {}).get(kind, {})
        if not meta.get("file"):
            continue
        path = (via / meta["file"]).resolve()
        if not path.is_relative_to(via.resolve()) or not path.is_file():
            continue
        raw = path.read_text(encoding="utf-8")
        if hashlib.sha256(raw.encode()).hexdigest()[:16] != meta.get("sha"):
            continue
        rows = [json.loads(line) for line in raw.splitlines() if line.strip()]
        if len(rows) != meta.get("n"):
            continue
        numbered.extend(row for row in rows if row.get("kind") == kind)
    accepted = []
    for link in policy.get("retained_dependencies", []):
        old, new = link.get("path", ""), link.get("active_entry", "")
        older = re.fullmatch(r"(.+)_v([0-9]{4})\.py", old)
        newer = re.fullmatch(r"(.+)_v([0-9]{4})\.py", new)
        if not older or not newer or older[1] != newer[1] or int(older[2]) >= int(newer[2]) or new not in active:
            continue
        old_path = (via / old).resolve()
        if not old_path.is_relative_to(via.resolve()) or not old_path.is_file():
            continue
        rows = [row for row in numbered if row.get("source") == old and row.get("version") == "v" + older[2]
                and row.get("name") == Path(old).stem and row.get("code")]
        if len(rows) == 1:
            accepted.append({"source": old, "code": rows[0]["code"], "active_entry": new,
                             "registration": "verified_numbering_history", "numbering_book": str(books[-1].relative_to(via))})
    return accepted


def audit(via=PRIOR.VIA, policy=None, baseline=None, require_baseline=True):
    via = Path(via)
    policy = policy or _READ(via / PRIOR.POLICY.relative_to(PRIOR.VIA))
    invpath = (via / policy["component_inventory"]).resolve()
    inventory = _READ(invpath) if invpath.exists() else {"records": []}
    history = historical_registration(via, policy, inventory)
    def read(path):
        if Path(path).resolve() == invpath:
            result = copy.deepcopy(inventory)
            result["records"].extend(history)
            return result
        return _READ(path)
    with patch.dict(_OWNER, {"read": read}):
        result = _AUDIT(via, policy, baseline, require_baseline)
    result["historical_registration"] = history
    return result


_OWNER["audit"] = audit


def selftest():
    import tempfile
    rc = PRIOR.selftest()
    checks = []
    with tempfile.TemporaryDirectory() as temp:
        via = Path(temp);reg = via / "supportive modules/registry";reg.mkdir(parents=True)
        old = "functional modules/VRN/VRN_SystemManager_v0110.py"
        new = "functional modules/VRN/VRN_SystemManager_v0111.py"
        (via / old).parent.mkdir(parents=True);(via / old).write_text("# retained\n")
        inventory = {"records": [{"source": new, "state": "ACTIVE"}]}
        policy = {"retained_dependencies": [{"path": old, "active_entry": new}]}
        book = reg / "history.jsonl"
        raw = json.dumps({"source": old, "version": "v0110", "kind": "MDL", "name": Path(old).stem, "code": "VIA-VRN-MDL001"}) + "\n"
        book.write_text(raw)
        ssot = {"books": {"MDL": {"file": str(book.relative_to(via)), "n": 1, "sha": hashlib.sha256(raw.encode()).hexdigest()[:16]}}}
        (reg / "VIA_Numbering_SSOT_v0100.json").write_text(json.dumps(ssot))
        checks.append(len(historical_registration(via,policy,inventory)) == 1)
        checks.append(historical_registration(via,{},inventory) == [])
        checks.append(historical_registration(via,policy,{"records": []}) == [])
        book.write_text(raw + " ")
        checks.append(historical_registration(via,policy,inventory) == [])
        book.write_text(raw)
        policy["retained_dependencies"][0]["active_entry"] = "functional modules/VDF/VDF_SystemManager_v0111.py"
        checks.append(historical_registration(via,policy,inventory) == [])
    failed = checks.count(False) + bool(rc)
    print("[交接歷史席位] fail=" + str(failed))
    return int(bool(failed))


def main(argv=None):
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print("[DENY] VCGC entry required")
        return 2
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["--selftest"]:
        return selftest()
    return PRIOR.main(args)


if __name__ == "__main__":
    raise SystemExit(main())
