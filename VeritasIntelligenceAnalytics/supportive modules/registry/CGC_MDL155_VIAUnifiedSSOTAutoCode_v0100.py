#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL155 — VIA Unified SSOT / AutoCode Gateway.

This is the VIA-controlled adapter for the user-provided VCG AutoCode generator.
The existing VIA Naming Registry and Component Inventory remain the canonical
system numbering authorities.  CodeChain/KNO/IDX/PRD are an append-only,
coexisting namespace and are exercised in an isolated SSOT root during tests.

The bridge consolidates, without rewriting source registries:
  REGEX/synonyms, logic, parameters, factors, databases, module inventory,
  system/engine/subsystem/module states, and quarantine intake metadata.

It is local-only, deterministic, read-mostly, and never downloads or executes
quarantined source modules.  It writes only its own report directory.
"""
from __future__ import annotations

# ===== [VIA:ACCEL-BRIDGE:v0100] graceful SuperAccel mount =====
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
    VIA_ACCEL = None
# ===== [VIA:ACCEL-BRIDGE:END] =====

import argparse
import ast
import hashlib
import html
import importlib.util
import json
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
REPORT_DIR = VIA / "VIA_Reports" / "ssot_autocode"
LATEST_JSON = REPORT_DIR / "VIA_SSOT_AUTOCODE_latest.json"
LATEST_HTML = REPORT_DIR / "VIA_SSOT_AUTOCODE_latest.html"
AUTOCODE = HERE / "VIA_AutoCodeGenerator_v0100.py"
NAMING = HERE / "VIA_Naming_Registry_v0100.json"
COMPONENTS = HERE / "VIA_Component_Inventory_SSOT_v0100.json"
INTERFACES = HERE / "VIA_Interface_Contract_Registry_v0100.json"

# Source registries are deliberately referenced, not copied or rewritten.
SOURCE_SPECS: dict[str, list[tuple[str, str]]] = {
    "regex_synonym": [
        ("central_regex_synonym", "supportive modules/registry/VIA_Central_Synonym_Regex_v0100.json"),
        ("regex_dict", "supportive modules/registry/VIA_SSOT_RegexDict_v0100.json"),
        ("regex_census", "supportive modules/ssot/VIA_RegexSynonym_Census_v0100.json"),
        ("synonym_seed", "supportive modules/ssot/VIA_Synonym_Seed_v0100.json"),
        ("vrn_financial_synonym", "supportive modules/ssot/VRN_FinancialSynonym_BidirectionalIndex.json"),
    ],
    "logic": [
        ("vrn_extraction_logic", "supportive modules/registry/VRN_ExtractionLogic_SSOT_v0100.json"),
        ("vrn_financial_regex", "supportive modules/ssot/VRN_FinancialRegex_SSOT.json"),
    ],
    "parameters": [
        ("parameter_pointer", "supportive modules/ssot/VIA_FinalParameters_OneInterface_ActivePointer.json"),
        ("parameter_summary", "supportive modules/ssot/VIA_FinalParameters_OneInterface_Summary.json"),
        ("parameter_canonical", "supportive modules/registry/VIA_FinalParameters_CanonicalRegistry.json"),
        ("parameter_ssot", "supportive modules/ssot/VIA_Parameters_SSOT.json"),
    ],
    "factors": [
        ("factor_spec", "supportive modules/specs/VIA_TW_StockFlow_Indicators_v001.md"),
        ("factor_matrix", "supportive modules/ui_support/VIA_Factor_Dict_Matrix.html"),
        ("quantguard_ssot", "functional modules/VDF/references/intake/VIA_QuantGuard_v20260916/ssot/quant_engine_ssot.json"),
    ],
    "databases": [
        ("stock_duckdb", "functional modules/VDF/output_hub/mega/vdf_tw_market.duckdb"),
        ("active_etf_duckdb", "functional modules/VDF/output_hub/active_tw_etf/active_tw_etf_holdings/ActiveTWETF.duckdb"),
        ("vrn_report_db", "functional modules/VRN/db/vrn_reports.duckdb"),
    ],
    "modules": [
        ("vcg_autocode_gateway", "supportive modules/registry/VIA_AutoCodeGenerator_v0100.py"),
        ("vcg_ssot_root", "supportive modules/registry/vcg/ssot"),
        ("naming_registry", "supportive modules/registry/VIA_Naming_Registry_v0100.json"),
        ("component_inventory", "supportive modules/registry/VIA_Component_Inventory_SSOT_v0100.json"),
        ("interface_registry", "supportive modules/registry/VIA_Interface_Contract_Registry_v0100.json"),
        ("supportive_registry", "supportive modules/registry/supportive_modules_registry.json"),
        ("vrn_registry", "supportive modules/registry/VRN_Verified_Module_Registry.json"),
        ("vdf_registry", "supportive modules/registry/VDF_NexusCore_ModuleRegistry.json"),
    ],
    "states": [
        ("nexuscore_runtime", "supportive modules/ssot/VIA_SSOT_NexusCoreStatus_Runtime_v029SSOT1A.json"),
        ("bridge_status", "supportive modules/runtime_bridge/BRIDGE_STATUS_NORMALIZED.json"),
        ("functional_acceptance", "VIA_Reports/acceptance/VIA_FUNCTIONAL_ACCEPTANCE_latest.json"),
    ],
    "quarantine": [
        ("quality_rules_quarantine", "supportive modules/ssot/SUP_MDL676_MDL269VRNQualityRulesQuarantineDryRunMODULEV00.py"),
        ("quarantine_vendor_root", "functional modules/VRN/_quarantine_pip_vendor"),
    ],
}


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return None


def resolve(rel: str) -> Path:
    return VIA / rel


def source_inventory() -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = {}
    for category, specs in SOURCE_SPECS.items():
        rows = []
        for key, rel in specs:
            path = resolve(rel)
            rows.append({
                "key": key,
                "path": rel,
                "exists": path.exists(),
                "kind": "directory" if path.is_dir() else (path.suffix.lower().lstrip(".") or "file"),
                "sha256": sha256(path) if path.is_file() else None,
                "bytes": path.stat().st_size if path.is_file() else None,
            })
        out[category] = rows
    return out


def _norm(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip().casefold())


def _walk_synonyms(value: Any, key_hint: str = "") -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    if isinstance(value, dict):
        for key, item in value.items():
            low = str(key).lower()
            if low in {"synonyms", "aliases", "lexicon", "terms", "aliases_by_canonical"} and isinstance(item, dict):
                pairs.extend(_walk_synonyms(item, low))
            elif isinstance(item, list):
                canonical = str(key)
                for alias in item:
                    if isinstance(alias, (str, int, float)):
                        pairs.append((str(alias), canonical))
            elif isinstance(item, str) and key_hint in {"synonyms", "aliases", "lexicon"}:
                pairs.append((item, str(key)))
            elif isinstance(item, dict):
                pairs.extend(_walk_synonyms(item, str(key)))
    elif isinstance(value, list):
        for item in value:
            if isinstance(item, dict):
                canonical = item.get("canonical") or item.get("key") or item.get("name") or key_hint
                aliases = item.get("aliases") or item.get("synonyms") or item.get("terms") or []
                if isinstance(aliases, str):
                    aliases = [aliases]
                for alias in aliases:
                    pairs.append((str(alias), str(canonical)))
                pairs.extend(_walk_synonyms(item, key_hint))
    return pairs


def merged_regex_synonyms() -> dict[str, Any]:
    # These are semantic aliases already present in separate VIA financial
    # vocabularies.  The central SSOT names remain the canonical display keys.
    canonical_equivalents = {
        "PRICE_TARGET": "TARGET_PRICE",
        "BASIC_EPS": "EPS",
        "DILUTED_EPS": "EPS",
    }
    aliases: dict[str, dict[str, Any]] = {}
    regexes: dict[str, dict[str, Any]] = {}
    semantic_merges: list[dict[str, str]] = []
    conflicts: list[dict[str, str]] = []
    for key, rel in SOURCE_SPECS["regex_synonym"]:
        path = resolve(rel)
        data = load_json(path)
        if isinstance(data, dict):
            for name, rec in (data.get("regex", {}) or {}).items():
                if isinstance(rec, dict) and rec.get("pattern"):
                    regexes.setdefault(str(name), {"pattern": rec["pattern"], "sources": []})
                    regexes[str(name)]["sources"].append(key)
            pairs = _walk_synonyms(data)
            if isinstance(data.get("synonyms"), dict):
                pairs.extend(_walk_synonyms(data["synonyms"], "synonyms"))
        else:
            pairs = []
        for alias, canonical in pairs:
            na = _norm(alias)
            if not na:
                continue
            original_canonical = canonical
            canonical = canonical_equivalents.get(canonical, canonical)
            if original_canonical != canonical:
                semantic_merges.append({"alias": alias, "from": original_canonical, "to": canonical, "source": key})
            row = aliases.setdefault(na, {"canonical": canonical, "sources": []})
            row["sources"].append(key)
            if row["canonical"] != canonical:
                conflicts.append({"alias": alias, "left": row["canonical"], "right": canonical, "source": key})
    return {"aliases": aliases, "regex": regexes, "conflicts": conflicts, "semantic_merges": semantic_merges}


def _count_json_rows(path: Path) -> int | None:
    data = load_json(path)
    if isinstance(data, list):
        return len(data)
    if isinstance(data, dict):
        for key in ("rows", "items", "entries", "factors", "parameters", "modules", "links"):
            value = data.get(key)
            if isinstance(value, list):
                return len(value)
            if isinstance(value, dict):
                return len(value)
        return len(data)
    return None


def state_snapshot(inventory: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    def existing(category: str) -> int:
        return sum(1 for row in inventory[category] if row["exists"])
    core_ok = all(resolve(rel).exists() for rel in (
        "supportive modules/registry/VIA_Naming_Registry_v0100.json",
        "supportive modules/registry/VIA_Component_Inventory_SSOT_v0100.json",
        "supportive modules/registry/VIA_Interface_Contract_Registry_v0100.json",
        "supportive modules/registry/VIA_Central_Synonym_Regex_v0100.json",
        "supportive modules/registry/VRN_ExtractionLogic_SSOT_v0100.json",
    ))
    return {
        "system_state": "GREEN" if core_ok else "YELLOW",
        "engine_state": "GREEN" if AUTOCODE.is_file() else "RED",
        "data_state": "GREEN" if all(row["exists"] for row in inventory["databases"]) else "YELLOW",
        "missing_data_sources": [row["key"] for row in inventory["databases"] if not row["exists"]],
        "subsystem_state": {
            "VRN": "GREEN" if existing("logic") and existing("modules") else "YELLOW",
            "VDF": "GREEN" if existing("databases") >= 2 else "YELLOW",
            "VAP": "GREEN" if existing("factors") >= 1 else "YELLOW",
            "CGC": "GREEN" if existing("states") >= 1 else "YELLOW",
        },
        "module_state": {
            "collected": existing("modules"),
            "quarantine_collected": existing("quarantine"),
            "quarantine_execution": "FORBIDDEN",
        },
    }


def naming_resolution() -> list[dict[str, Any]]:
    data = load_json(NAMING)
    if not isinstance(data, dict):
        return []
    out = []
    for family, item in data.get("items", {}).items():
        if "UnifiedSSOTAutoCode" in family or "VIA_AutoCodeGenerator" in family:
            out.append({
                "family": family,
                "canonical": item.get("canonical"),
                "num": item.get("num"),
                "iface_urn": item.get("iface_urn"),
                "members": item.get("members", []),
            })
    return out


def _import_autocode():
    if not AUTOCODE.is_file():
        raise RuntimeError("VIA_AutoCodeGenerator_v0100.py 不存在")
    spec = importlib.util.spec_from_file_location("via_autocode_generator_v0100", AUTOCODE)
    if spec is None or spec.loader is None:
        raise RuntimeError("自動編碼器 import spec 建立失敗")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _seed_isolated_ssot(root: Path) -> None:
    reg = root / "registry"
    reg.mkdir(parents=True, exist_ok=True)
    def put(name: str, data: dict[str, Any]) -> None:
        (reg / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    put("lib.registry.json", {"libraries": {"VIA_CENTRAL": {"version": "1.0", "status": "active"}}})
    put("module.registry.json", {"modules": {"VRN": {"latest_index": 0, "items": []}}})
    put("function.registry.json", {"functions": {"VRN": {"latest_index": 0, "items": []}}})
    put("worldline.registry.json", {"worldlines": {}})
    put("engine.registry.json", {"engines": {}})
    put("factor.registry.json", {"factors": {}})
    put("kno.taxonomy.json", {
        "domains": ["OTHER", "TA", "STAT", "ML", "RISK"],
        "stateless_domains": ["TA", "STAT", "ML"],
        "categories": {}, "types": {}, "sources": {"central": ["VIA", "TWSE"]},
        "freqs": ["M", "Q", "W", "D", "T", "A"],
        "versions": {"V1": "raw", "V2": "clean", "V3": "seasonal", "V4": "forecast", "V5": "enhanced"},
        "countries": ["TW", "US"], "index_markets": ["TW"], "index_families": ["EQUITY"],
        "product_assets": ["EQUITY"], "product_families": ["STOCK"], "link_roles": ["MEASURES"],
    })


def isolated_protocol_test() -> dict[str, Any]:
    mod = _import_autocode()
    with tempfile.TemporaryDirectory(prefix="via_cgc155_") as tmp:
        root = Path(tmp) / "ssot"
        _seed_isolated_ssot(root)
        engine = mod.AutoCodeEngine(mod.SSOT(root))
        chain = engine.generate("VIA", "VRN", "VIA_CENTRAL", new_module=True)
        kno = engine.kno_generate(text="台灣 RSI 技術分析", domain="TA", source="VIA", freq="D", version="V1")
        idx = engine.idx_generate("TW", "TW", "EQUITY", "2330", "TWSE", "D", "V1")
        prd = engine.prd_generate("EQUITY", "TW", "STOCK", "2330", "TWSE", "D", "V1")
        link = engine.gov_link(kno=kno["kno"], codechain=chain["codechain"], index=idx["index"], product=prd["product"])
        health = engine.health()
        return {
            "codechain": chain["codechain"], "kno": kno["kno"], "index": idx["index"],
            "product": prd["product"], "link_id": link["link_id"], "health": health,
            "pass": health["status"] == "GREEN",
        }


def build_manifest() -> dict[str, Any]:
    inventory = source_inventory()
    merged = merged_regex_synonyms()
    counts = {
        category: {
            "declared": len(rows),
            "present": sum(1 for row in rows if row["exists"]),
            "missing": [row["key"] for row in rows if not row["exists"]],
        }
        for category, rows in inventory.items()
    }
    return {
        "schema": "VIA.UnifiedSSOT.AutoCode.v0100",
        "ts": now_iso(),
        "policy": {
            "source_of_truth": "existing VIA registries remain canonical",
            "append_only": True,
            "physical_rename": False,
            "quarantine_execution": "FORBIDDEN",
            "network": "OFF_BY_DEFAULT",
            "conflict": "RED until canonical owner resolves",
        },
        "protocols": ["CodeChain", "KNO", "IDX", "PRD"],
        "namespaces": {
            "central_via": "VIA_Naming_Registry_v0100 + VIA_Component_Inventory_SSOT_v0100",
            "vcg_auxiliary": "VIA-AutoCodeGenerator_v0100 isolated/coexisting CodeChain-KNO-IDX-PRD",
            "collision_rule": "never renumber existing VIA IDs; reject conflicting aliases or codes",
        },
        "sources": inventory,
        "counts": counts,
        "regex_synonym": {
            "regex_count": len(merged["regex"]),
            "synonym_count": len(merged["aliases"]),
            "conflict_count": len(merged["conflicts"]),
            "conflicts": merged["conflicts"][:50],
            "semantic_merges": merged["semantic_merges"][:50],
            "sample_aliases": [{"alias": k, **v} for k, v in sorted(merged["aliases"].items())[:25]],
        },
        "states": state_snapshot(inventory),
        "central_registry": {
            "naming_registry": str(NAMING.relative_to(VIA)),
            "component_inventory": str(COMPONENTS.relative_to(VIA)),
            "interface_registry": str(INTERFACES.relative_to(VIA)),
            "auto_code_generator": str(AUTOCODE.relative_to(VIA)),
            "naming_resolution": naming_resolution(),
        },
        "result_rule": "GREEN only when source inventory has no missing database, conflict scan is clean, protocol test passes, and central registry links are verified; otherwise YELLOW",
    }


def render_html(payload: dict[str, Any]) -> str:
    states = payload["states"]
    rows = []
    for category, detail in payload["counts"].items():
        state = "GREEN" if not detail["missing"] else "YELLOW"
        rows.append(f"<tr><td>{html.escape(category)}</td><td>{detail['present']}/{detail['declared']}</td><td class='{state.lower()}'>{state}</td><td>{html.escape(', '.join(detail['missing']) or '—')}</td></tr>")
    sub = "".join(f"<li><b>{html.escape(k)}</b> {html.escape(str(v))}</li>" for k, v in states["subsystem_state"].items())
    aliases = "".join(f"<tr><td>{html.escape(row['alias'])}</td><td>{html.escape(str(row['canonical']))}</td><td>{html.escape(', '.join(row['sources']))}</td></tr>" for row in payload["regex_synonym"]["sample_aliases"])
    return f"""<!doctype html><html lang='zh-Hant'><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
<title>VIA Unified SSOT AutoCode</title><style>
body{{font:13px/1.55 system-ui,'Noto Sans TC',sans-serif;background:#f4f5f7;color:#202733;max-width:1100px;margin:0 auto;padding:22px}}h1{{font-size:22px}}h2{{font-size:15px;margin-top:24px}}.grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}}.card,table{{background:#fff;border:1px solid #dfe3e8;border-radius:8px}}.card{{padding:12px}}.big{{font-size:24px;font-weight:700}}table{{width:100%;border-collapse:collapse;overflow:hidden}}th,td{{padding:7px 9px;border-bottom:1px solid #e6e9ed;text-align:left;vertical-align:top}}th{{color:#596575;font-size:11px}}.green{{color:#18794e}}.yellow{{color:#9a6700}}.red{{color:#b42318}}code{{color:#245b9a;overflow-wrap:anywhere}}ul{{padding-left:22px}}@media(max-width:720px){{.grid{{grid-template-columns:repeat(2,1fr)}}}}
</style><body><h1>VIA 統一 SSOT／自動編碼中央橋</h1><p>CGC_MDL155 · {html.escape(payload['ts'])} · append-only · 不改既有正典、不執行收容模組</p>
<div class='grid'><div class='card'><div class='big'>{payload['regex_synonym']['regex_count']}</div>Regex</div><div class='card'><div class='big'>{payload['regex_synonym']['synonym_count']}</div>同義字</div><div class='card'><div class='big'>{payload['counts']['modules']['present']}/{payload['counts']['modules']['declared']}</div>模組來源</div><div class='card'><div class='big'>{html.escape(states['system_state'])}</div>系統狀態</div></div>
<h2>系統／引擎／子系統／收容模組狀態</h2><ul><li><b>System</b> {html.escape(states['system_state'])}</li><li><b>Engine</b> {html.escape(states['engine_state'])}</li>{sub}<li><b>Quarantine</b> {states['module_state']['quarantine_collected']} source(s) collected; execution={html.escape(states['module_state']['quarantine_execution'])}</li></ul>
<h2>SSOT 來源矩陣</h2><table><tr><th>類別</th><th>存在</th><th>燈號</th><th>缺少</th></tr>{''.join(rows)}</table>
<h2>Regex／同義字樣本</h2><table><tr><th>Alias</th><th>Canonical</th><th>Sources</th></tr>{aliases or '<tr><td colspan=3>無樣本</td></tr>'}</table>
<h2>自動編碼命名空間</h2><p><code>VIA_Naming_Registry_v0100</code> 是中央正典；附件提供的 CodeChain／KNO／IDX／PRD 以共存、隔離 SSOT 方式運作。既有 VIA 編號不重發。</p></body></html>"""


def run(write: bool = True) -> dict[str, Any]:
    payload = build_manifest()
    protocol = isolated_protocol_test()
    payload["protocol_test"] = protocol
    payload["verdict"] = "GREEN" if protocol["pass"] and payload["regex_synonym"]["conflict_count"] == 0 and payload["states"]["system_state"] == "GREEN" and payload["states"]["data_state"] == "GREEN" else "YELLOW"
    if write:
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        LATEST_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        LATEST_HTML.write_text(render_html(payload), encoding="utf-8")
    return payload


def classify(text: str) -> dict[str, Any]:
    payload = run(write=True)
    merged = merged_regex_synonyms()
    norm = _norm(text)
    direct = merged["aliases"].get(norm)
    return {"text": text, "normalized": norm, "canonical": direct["canonical"] if direct else None, "source_count": len(direct["sources"]) if direct else 0, "manifest": str(LATEST_JSON)}


def selftest() -> int:
    failures: list[str] = []
    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'OK' if ok else 'FAIL'}] {name}{(' · ' + detail) if detail else ''}")
        if not ok:
            failures.append(name)
    payload = run(write=True)
    check("① 附件自動編碼器可 import", AUTOCODE.is_file())
    check("② 中央正典與收容來源盤點", sum(x["present"] for x in payload["counts"].values()) > 0)
    check("③ Regex/同義字合併且無衝突", payload["regex_synonym"]["regex_count"] > 0 and payload["regex_synonym"]["synonym_count"] > 0 and payload["regex_synonym"]["conflict_count"] == 0)
    check("④ CodeChain/KNO/IDX/PRD 隔離協定實測", payload["protocol_test"]["pass"], json.dumps(payload["protocol_test"], ensure_ascii=False))
    check("⑤ 既有 VIA 中央命名/元件/介面冊已連結", all(Path(resolve(rel)).exists() for rel in ("supportive modules/registry/VIA_Naming_Registry_v0100.json", "supportive modules/registry/VIA_Component_Inventory_SSOT_v0100.json", "supportive modules/registry/VIA_Interface_Contract_Registry_v0100.json")))
    check("⑥ 系統/引擎/子系統/收容狀態有明確燈號", payload["states"]["system_state"] in {"GREEN", "YELLOW"} and payload["states"]["engine_state"] == "GREEN" and payload["states"]["module_state"]["quarantine_execution"] == "FORBIDDEN")
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    imported = {alias.name.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names}
    imported.update({node.module.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module})
    check("⑦ 零網路、零禁用技術指標、零收容執行接線", not imported.intersection({"requests", "httpx", "subprocess", "talib"}))
    check("⑧ JSON/HTML 報告已落檔", LATEST_JSON.is_file() and LATEST_HTML.is_file())
    check("⑨ 缺少資料庫不假綠", payload["verdict"] == ("GREEN" if not payload["states"]["missing_data_sources"] else "YELLOW"))
    print(f"  [計] OK {9 - len(failures)} · FAIL {len(failures)}")
    print(f"  JSON: {LATEST_JSON}")
    print(f"  HTML: {LATEST_HTML}")
    return 1 if failures else 0


def main() -> int:
    parser = argparse.ArgumentParser(description="CGC_MDL155 VIA Unified SSOT / AutoCode Gateway")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("selftest")
    sub.add_parser("status")
    sub.add_parser("manifest")
    c = sub.add_parser("classify")
    c.add_argument("text")
    sub.add_parser("routes")
    args = parser.parse_args()
    if args.cmd == "selftest":
        return selftest()
    if args.cmd == "classify":
        print(json.dumps(classify(args.text), ensure_ascii=False, indent=2))
        return 0
    if args.cmd == "routes":
        print(json.dumps({"SSOT": "source registries → CGC_MDL155 manifest → VCG isolated protocol test", "REGEX": "central regex/synonym SSOT → normalized alias/canonical", "AUTOCODE": "VIA central naming remains canonical; CodeChain/KNO/IDX/PRD coexisting", "STATE": "system → engine → subsystem → module/quarantine", "QUARANTINE": "collect/hash/report only; execution forbidden"}, ensure_ascii=False, indent=2))
        return 0
    payload = run(write=True)
    print(json.dumps(payload if args.cmd == "manifest" else {"verdict": payload["verdict"], "states": payload["states"], "counts": payload["counts"], "protocol_test": payload["protocol_test"], "json": str(LATEST_JSON), "html": str(LATEST_HTML)}, ensure_ascii=False, indent=2))
    return 0 if payload["verdict"] == "GREEN" else 2


if __name__ == "__main__":
    raise SystemExit(main())
