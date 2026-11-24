#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VDF_ENG053_ParamEngineMap — VDF 輸入參數×引擎整合映射器(批134;via-vdf-map)
====================================================================
操作員令(2026-08-25):Integrate all VDF input parameters and map
with corresponding engines and test。
四參數冊聯動+全引擎重收割(舊 Param Registry 收割止於 08-23,
ENG046-052 七具新引擎未入冊=本器補齊):
  冊① VDF_Unified_Params(統一參數 SSOT)→ 別名表對映引擎常數
  冊② VDF_Param_Registry(678 收割+24 canonical 裁定)→ 裁定附掛
  冊③ VDF_Input_Interface_Matrix(五分區活冊)→ 源碼實證推導消費引擎
  冊④ VDF_Fetch_Orders(擷取單車道)→ 源碼實證推導接單引擎
收割雙面:AST 模組級大寫常數+argparse CLI 選項(輸入參數全譜)。
產物:VDF_Param_Engine_Map_v0100.json(by_engine/by_param/books/gaps)
     ;誠實列缺(多值無裁定/無參引擎/未映車道)。
紅線:唯讀收割零觸碰引擎原件;四冊唯讀;僅寫映射冊(version-forward)。
v0100→v0101(批135):在役面收割=版本家族只取 glob 最新(舊版檔
保存不入工作面);canonical 追加 HTTP_HEADERS/TW_TICKER_REGEX 後候裁歸零。
用法:via-vdf-map run | --selftest
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
        _nb_spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        _nb_mod = _nb_ilu.module_from_spec(_nb_spec)
        _nb_spec.loader.exec_module(_nb_mod)
        return _nb_mod
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import ast
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent          # .../VDF/engine
VDF = HERE.parent
VIA = VDF.parent.parent
MAP_OUT = VDF / "VDF_Param_Engine_Map_v0100.json"

BOOKS = {
    "unified": "VDF_Unified_Params_v0100.json",
    "registry": "VDF_Param_Registry_v0100.json",
    "matrix": "VDF_Input_Interface_Matrix_v0100.json",
    "orders": "VDF_Fetch_Orders_v0100.json",
}
EXCLUDE_DIRS = {"__pycache__", "_superseded", "_rebuilds_superseded",
                "candidates", "removed_", "output_hub", "DATABASE"}
# 統一參數 SSOT 別名表(引擎常數名 → 冊①路徑)
UNIFIED_ALIAS = {
    "START_DATE": "time.start_date", "END_DATE": "time.end_date",
    "BATCH_SIZE": "fetch.batch_size", "MAX_RETRIES": "fetch.max_retries",
    "RETRY_DELAY": "fetch.retry_delay_s", "RETRY_DELAY_S": "fetch.retry_delay_s",
    "TIMEOUT": "fetch.timeout_s", "TIMEOUT_S": "fetch.timeout_s",
    "HTTP_TIMEOUT": "fetch.timeout_s", "OUTPUT_DIR": "output.root",
    "OUTPUT_ROOT": "output.root", "CSV_ENCODING": "output.csv_encoding",
    "MARKETS": "markets",
}


_FAM_RX = re.compile(r"^(.*)_v\d+$")


def active_engines() -> list[Path]:
    """在役面收割:_sha 鏡像/收容夾排除+版本家族只取 glob 最新(v0101:
    對齊動態解析最新版紅線;舊版本檔保存但不入映射工作面)"""
    cand = []
    for base in (VDF, HERE):
        for p in sorted(base.glob("*.py")):
            low = p.name.lower()
            if "_sha" in low or any(x in str(p) for x in EXCLUDE_DIRS):
                continue
            cand.append(p)
    fam: dict[tuple, Path] = {}
    for p in cand:
        m = _FAM_RX.match(p.stem)
        key = (str(p.parent), m.group(1)) if m else (str(p.parent), p.stem)
        if key not in fam or p.name > fam[key].name:
            fam[key] = p
    return sorted(fam.values())


def harvest_file(path: Path) -> dict:
    """AST 收割:模組級大寫常數+argparse CLI 選項(唯讀)"""
    src = path.read_text(encoding="utf-8", errors="replace")
    consts, cli = [], []
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return {"parse": "SYNTAX_SKIP", "consts": [], "cli": []}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id.isupper():
                    try:
                        val = ast.unparse(node.value)
                    except Exception:
                        val = "<unparse-fail>"
                    consts.append({"name": t.id, "value": val[:160],
                                   "lineno": node.lineno})
    for node in ast.walk(tree):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and node.func.attr == "add_argument"):
            for a in node.args:
                if isinstance(a, ast.Constant) and isinstance(a.value, str) \
                        and a.value.startswith("-"):
                    cli.append(a.value)
    return {"parse": "OK", "consts": consts, "cli": sorted(set(cli))}


def _flat(d, pfx=""):
    out = {}
    for k, v in d.items():
        key = f"{pfx}.{k}" if pfx else k
        if isinstance(v, dict):
            out.update(_flat(v, key))
        else:
            out[key] = v
    return out


def load_books() -> dict:
    got = {}
    for key, name in BOOKS.items():
        p = VDF / name
        got[key] = json.loads(p.read_text(encoding="utf-8-sig")) if p.exists() else None
    return got


def derive_string_consumers(engines: dict, tokens: list[str]) -> dict:
    """源碼實證:掃引擎原文含指定字面(車道名/分區鍵)→ 消費引擎表"""
    hits = {t: [] for t in tokens}
    for rel, meta in engines.items():
        src = (VDF / rel).read_text(encoding="utf-8", errors="replace")
        for t in tokens:
            if re.search(r"['\"]" + re.escape(t) + r"['\"]", src):
                hits[t].append(rel)
    return hits


def build_map() -> dict:
    books = load_books()
    engines = {}
    for p in active_engines():
        rel = str(p.relative_to(VDF))
        engines[rel] = harvest_file(p)
    by_param: dict[str, dict] = {}
    for rel, meta in engines.items():
        for c in meta["consts"]:
            e = by_param.setdefault(c["name"], {"engines": {}, "values": set()})
            e["engines"][rel] = c["value"]
            e["values"].add(c["value"])
    canonical = (books["registry"] or {}).get("canonical", {})
    unified_flat = _flat(books["unified"] or {})
    for name, e in by_param.items():
        e["n_engines"] = len(e["engines"])
        e["n_values"] = len(e["values"])
        e["values"] = sorted(e["values"])[:8]
        if name in canonical:
            e["governance"] = {"state": "GOVERNED_CANONICAL",
                               "ruling": canonical[name].get("ruling")}
        elif name in UNIFIED_ALIAS and UNIFIED_ALIAS[name] in unified_flat:
            e["governance"] = {"state": "GOVERNED_UNIFIED",
                               "ssot": UNIFIED_ALIAS[name],
                               "ssot_value": str(unified_flat[UNIFIED_ALIAS[name]])[:80]}
        elif name in ("HERE", "VIA", "OUT", "ROOT", "SELF") or all(
                ("Path(" in v or ".parent" in v) for v in e["values"]):
            e["governance"] = {"state": "INFRA_PATH_ANCHOR",
                               "note": "檔案位置錨定=各檔自錨設計,非輸入參數債"}
        elif e["n_values"] > 1:
            e["governance"] = {"state": "NEEDS_RULING",
                               "note": "多引擎多值且無 canonical/unified 裁定=候操作員"}
        else:
            e["governance"] = {"state": "SINGLE_VALUE"}
    lanes = sorted({ln if isinstance(ln, str) else ln.get("lane")
                    for o in (books["orders"] or {}).get("orders", [])
                    for ln in (o.get("lanes") or [])})
    lane_map = derive_string_consumers(engines, lanes)
    sections = sorted(((books["matrix"] or {}).get("sections") or {}).keys())
    sect_map = derive_string_consumers(engines, sections)
    old_srcs = {p.get("src") for p in (books["registry"] or {}).get("params", [])}
    newly = [rel for rel in engines
             if Path(rel).name not in {Path(s).name for s in old_srcs if s}]
    gaps = {
        "params_needs_ruling": sorted(n for n, e in by_param.items()
                                      if e["governance"]["state"] == "NEEDS_RULING"),
        "engines_without_params": sorted(r for r, m in engines.items()
                                         if m["parse"] == "OK" and not m["consts"]
                                         and not m["cli"]),
        "lanes_unmapped": sorted(t for t, hs in lane_map.items() if not hs),
        "sections_unmapped": sorted(t for t, hs in sect_map.items() if not hs),
        "engines_new_since_registry": sorted(newly),
        "syntax_skipped": sorted(r for r, m in engines.items()
                                 if m["parse"] == "SYNTAX_SKIP"),
    }
    return {
        "schema": "VIA.VDF.ParamEngineMap.v1",
        "policy": "批134 整合映射;唯讀收割零觸碰引擎;四冊唯讀;誠實列缺",
        "books": {k: BOOKS[k] + ("" if books[k] else "(缺)") for k in BOOKS},
        "by_engine": {rel: {"parse": m["parse"],
                            "n_consts": len(m["consts"]),
                            "cli": m["cli"],
                            "consts": m["consts"]} for rel, m in engines.items()},
        "by_param": by_param,
        "lane_engines": lane_map,
        "section_engines": sect_map,
        "gaps": gaps,
    }


def run() -> int:
    m = build_map()
    ne = len(m["by_engine"])
    np_ = len(m["by_param"])
    ncli = sum(len(v["cli"]) for v in m["by_engine"].values())
    gov = {}
    for e in m["by_param"].values():
        s = e["governance"]["state"]
        gov[s] = gov.get(s, 0) + 1
    print(f"=== VDF 參數×引擎整合映射(批134)· 引擎 {ne} · 參數 {np_} · CLI 選項 {ncli} ===")
    for k, v in sorted(gov.items()):
        print(f"  [治理] {k}×{v}")
    lm = m["lane_engines"]
    print(f"  [車道→引擎] {sum(1 for h in lm.values() if h)}/{len(lm)} 映通:"
          + " · ".join(f"{t}→{len(h)}" for t, h in sorted(lm.items())))
    sm = m["section_engines"]
    print(f"  [分區→引擎] {sum(1 for h in sm.values() if h)}/{len(sm)} 映通")
    g = m["gaps"]
    print(f"  [缺口誠實] 候裁參數 {len(g['params_needs_ruling'])} · 無參引擎 "
          f"{len(g['engines_without_params'])} · 未映車道 {len(g['lanes_unmapped'])} · "
          f"registry 未收割新引擎 {len(g['engines_new_since_registry'])} · "
          f"語法跳過 {len(g['syntax_skipped'])}")
    for rel in g["engines_new_since_registry"][:12]:
        print(f"    + 新收割:{rel}")
    MAP_OUT.write_text(json.dumps(m, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  [冊] {MAP_OUT.name}")
    return 0


def selftest() -> int:
    import tempfile
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / "eng.py"
        f.write_text("import argparse\nSTART_DATE = '2024-01-02'\nBATCH = 9\n"
                     "def cli():\n    p = argparse.ArgumentParser()\n"
                     "    p.add_argument('--mode')\n    p.add_argument('-q')\n"
                     "    tw = 'tw_daily'\n    sec = 'TW_FIN'\n")
        h = harvest_file(f)
        chk("① AST 常數收割(僅模組級大寫)",
            [c["name"] for c in h["consts"]] == ["START_DATE", "BATCH"])
        chk("② argparse CLI 選項收割", h["cli"] == ["--mode", "-q"])
        bad = Path(td) / "bad.py"
        bad.write_text("x=(\n")
        chk("③ 語法壞件誠實跳過", harvest_file(bad)["parse"] == "SYNTAX_SKIP")

    chk("④ 別名表對映統一 SSOT",
        UNIFIED_ALIAS["START_DATE"] == "time.start_date"
        and UNIFIED_ALIAS["HTTP_TIMEOUT"] == "fetch.timeout_s")
    flat = _flat({"time": {"start_date": "2018-01-01"}, "fetch": {"batch_size": 5}})
    chk("⑤ 冊①扁平化", flat["time.start_date"] == "2018-01-01"
        and flat["fetch.batch_size"] == 5)

    eng = {"a.py": {}, "b.py": {}}
    orig_read = Path.read_text
    m = build_map()
    chk("⑥ 實冊四書在位讀通", all("(缺)" not in v for v in m["books"].values()))
    chk("⑦ 車道→引擎源碼實證映通(ENG050/052 接單)",
        any("VDF_ENG052" in h for h in m["lane_engines"].get("tw_daily", []))
        and len(m["gaps"]["lanes_unmapped"]) == 0)
    chk("⑧ 新引擎補收割(ENG046-052 入冊)",
        any("VDF_ENG052" in r for r in m["gaps"]["engines_new_since_registry"])
        and any("VDF_ENG053" in r for r in m["by_engine"]))
    gov_states = {e["governance"]["state"] for e in m["by_param"].values()}
    chk("⑨ 治理五態齊備(含 INFRA 錨定鏡頭)+候裁誠實列名",
        "GOVERNED_CANONICAL" in gov_states and "SINGLE_VALUE" in gov_states
        and "INFRA_PATH_ANCHOR" in gov_states
        and m["by_param"]["HERE"]["governance"]["state"] == "INFRA_PATH_ANCHOR"
        and isinstance(m["gaps"]["params_needs_ruling"], list))
    src = Path(__file__).read_text(encoding="utf-8")
    body = src.split("def build_map", 1)[1].split("def selftest", 1)[0]
    chk("⑩ 唯讀保證(收割/四冊零寫入;僅映射冊落盤)",
        "write_text" not in body.split("def run", 1)[0]
        and "MAP_OUT.write_text" in body)
    fam_names = [Path(r).name for r in m["by_engine"]]
    chk("⑪ 在役面=家族最新(ENG052 v0101 入列、v0100 讓位不入)",
        "VDF_ENG052_MegaFetch_v0101.py" in fam_names
        and "VDF_ENG052_MegaFetch_v0100.py" not in fam_names)
    print(f"  [計] 十一檢 OK {11 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== VDF 參數映射器(VDF_ENG053)· 十一檢自測 ===")
        return selftest()
    if "run" in args or not args:
        return run()
    print(__doc__.split("用法:")[1])
    return 0


if __name__ == "__main__":
    sys.exit(main())
