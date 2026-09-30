"""VDF System Manager：日價執行契約、有效參數與 HEADER 分層呈現。"""
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


import html
import importlib.util
import json
import os
from pathlib import Path
import sys
from unittest.mock import patch

# def 01_PARAMETERS
HERE = Path(__file__).resolve().parent
VIA = HERE.parents[1]
VERSION = "v0120"
PRIOR_PATH = max(p for p in HERE.glob("VDF_SystemManager_v*.py") if p.name < Path(__file__).name)
ENGINE_GLOB = "VDF_ENG054_TWDailyBackfill_v*.py"
PAGE = VIA / "VIA_Reports" / "vdf_system" / "VDF_Manager_Matrix_v0120.html"


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


PRIOR = _load(PRIOR_PATH, "vdf_manager_prior_120")


def __getattr__(name):
    return getattr(PRIOR, name)


def read_contract():
    engine = _load(max((HERE / "engine").glob(ENGINE_GLOB)), "vdf_manager_contract_120")
    return engine.contract()


def read(domain, key=None, full=False):
    if domain == "contract":
        return read_contract()
    if domain == "headers":
        return read_contract()["headers"]
    result = PRIOR.read(domain, key, full)
    if domain == "param":
        result = dict(result, execution_contract=read_contract()["parameters"])
    return result


def read_param(key=None, full=False):
    return read("param", key, full)


def collect():
    result = PRIOR.collect()
    result["execution_contract"] = read_contract()
    return result


def measure():
    owner = PRIOR._measure_owner()
    with patch.object(owner, "PAGE", PAGE):
        card = PRIOR.measure()
    contract = read_contract()
    card.update(door=Path(__file__).stem, execution_contract=contract,
                production_database_verified=False)
    paragraphs = ["<section><h2>日價執行契約</h2><p>狀態檢查不代表資料更新；HEADER 為規格，主機資料尚未驗證。</p>",
                  "<table><tr><th>參數</th><th>宣告／有效值</th></tr>"]
    for key, value in contract["parameters"].items():
        paragraphs.append("<tr><td>" + html.escape(key) + "</td><td>" + html.escape(json.dumps(value, ensure_ascii=False)) + "</td></tr>")
    paragraphs.append("</table><h3>原始表與整合規格</h3><pre>" + html.escape(json.dumps(contract["headers"], ensure_ascii=False, indent=2)) + "</pre></section>")
    content = PAGE.read_text(encoding="utf-8")
    PAGE.write_text(content.replace("</main>", "".join(paragraphs) + "</main>"), encoding="utf-8")
    return card


def measure_rc(card):
    if card.get("rc_name") == "RED":
        return 1
    if card.get("open") or card.get("cmds_missing") or card.get("rc_name") != "GREEN":
        return 2
    return 0


def main(argv=None):
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print("[DENY] 只能經 VCGC")
        return 2
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] == "store":
        store = _load(max(HERE.glob("VDF_ParquetStore_v*.py")), "vdf_manager_store_120")
        return store.main(args[1:])
    if args == ["--selftest"]:
        return selftest()
    if args == ["measure"]:
        card = measure()
        print(json.dumps(card, ensure_ascii=False, indent=1))
        return measure_rc(card)
    if len(args) >= 2 and args[:2] in (["read", "contract"], ["read", "headers"], ["read", "param"]):
        rest = args[2:]
        keys = [x for x in rest if not x.startswith("--")]
        if any(x.startswith("--") and x not in ("--full", "--json") for x in rest) or len(keys) > 1 or (args[1] != "param" and keys):
            print("[BAD_PARAM] read contract / headers 不接受額外鍵；param [id] [--full] [--json]")
            return 2
        result = read(args[1], keys[0] if keys else None, "--full" in rest)
        print(json.dumps(result, ensure_ascii=False, indent=1))
        return 0 if result.get("state") not in ("ABSENT", "NODATA", "RED") else 2
    with patch.object(sys, "argv", [str(__file__), *args]):
        return PRIOR.main()


def selftest():
    prior_rc = PRIOR.selftest()
    tests = _load(HERE / "tests" / "test_backfill_dispatch_v0100.py", "vdf120_tests")
    return max(prior_rc, tests.run_manager_tests(sys.modules[__name__]))


if __name__ == "__main__":
    raise SystemExit(main())
