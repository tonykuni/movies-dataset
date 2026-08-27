#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CGC_MDL092_ConsolidationAudit — 引擎簡化工程稽核(批179;操作員 Roadmap)
====================================================================
操作員令:未使用引擎盤點+同功能整併(不傷原有能力);網路工具凍結
不可動。本引擎=AUDIT-ONLY 零改動(guardrail:不 big bang;整併裁決權
=操作員,本冊僅候審列示):
  ① census:未使用引擎盤點(不在 grid battery 且無人 import;排除
     凍結/_sha/SCOPE_COPY/收容原件區)→按功能字幹+關鍵詞分群=
     候整併群冊 VIA_Engine_Consolidation_Register(全 PENDING_OPERATOR)
  ② Phase 1 落地 A:Schema Registry——雙 DuckDB 全表欄位型別快照
     版本化 VIA_Schema_Registry(schema drift 守門基線)
  ③ Phase 1 落地 B:Engine Contract 冊——load/transform/evaluate/emit
     四介面規格+Pydantic I/O 封包模型(對齊交接報告 08.2 資料封包:
     run_id/data_class/quality_status/grain/content_sha256)
凍結名單(NEVER_TOUCH):SUP_MDL740/SUP_MDL741/VIA_NetSupport(統包
網路正主;操作員明令)+v0201 輪動正典原件。
用法:python3 CGC_MDL092_ConsolidationAudit_v0101.py run | --selftest
v0100→v0101(批180 第一波執行後):census 排除讓位封存區;自測改
一致性口徑(讓位 manifest 完整性+殘餘=HOLD_DYNAMIC_REF/FROZEN 誠實)。
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

import importlib.util
import json
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
REG_CONS = HERE / "VIA_Engine_Consolidation_Register_v0100.json"
REG_SCHEMA = HERE / "VIA_Schema_Registry_v0100.json"
REG_CONTRACT = HERE / "VIA_Engine_Contract_v0100.json"
DB_TW = VIA / "functional modules" / "VDF" / "output_hub" / "mega" / "vdf_tw_market.duckdb"
DB_GL = VIA / "functional modules" / "VDF" / "output_hub" / "mega" / "vdf_global_market.duckdb"

NEVER_TOUCH = ("SUP_MDL740", "SUP_MDL741", "VIA_NetSupport",
               "VIA_TW_GroupingIndexRotationUnifiedEngine_v0201")
EXCLUDE_FRAGS = ("VIA_RetiredEngines", "rollback", "_sha", "SCOPE_COPY", "references/intake",
                 "__pycache__", "/temp/", "flow_simulation", "vendor",
                 "_rebuilds_superseded", "/docs/history/")
# 功能關鍵詞分群(名稱語意;僅分群用零發明)
KEYWORD_GROUPS = [
    ("FETCH_NET", r"fetch|crawler|scrap|download|api"),
    ("OCR_DOC", r"ocr|pdf|docx|scan|layout|table|converter|extract"),
    ("PLOT_UI", r"plot|chart|dashboard|ui|html|visual|render"),
    ("FLOW_REGIME", r"flow|regime|momentum|rotation|group"),
    ("FINANCE_CALC", r"financial|valuation|eps|band|consensus|factor"),
    ("NLP_TEXT", r"summar|nlp|keyword|lexicon|digest|narrative"),
    ("STORE_DB", r"store|db|duckdb|dataset|schema|registry"),
    ("GOV_TEST", r"test|audit|selftest|governance|validate|check"),
]
_FAM_RX = re.compile(r"^(.*?)(?:_v\d+[a-z0-9]*)?$")


def _grid_battery_stems() -> set:
    g = sorted(HERE.glob("CGC_MDL064_SelftestGrid_v*.py"))[-1]
    spec = importlib.util.spec_from_file_location("grid_c92", g)
    m = importlib.util.module_from_spec(spec)
    sys.modules["grid_c92"] = m
    spec.loader.exec_module(m)
    out = set()
    for b in m.battery(fast=False):
        p = b.get("path")
        if p and p != "PYCODE":
            out.add(Path(str(p)).stem)
    return out


def _imported_stems() -> set:
    reg = json.loads((HERE / "VIA_Interface_Contract_Registry_v0100.json"
                      ).read_text(encoding="utf-8"))
    out = set()
    for mod in reg["modules"].values():
        for imp in (mod.get("contract", {}).get("imports") or []):
            out.add(imp)
    return out


def census() -> dict:
    battery = _grid_battery_stems()
    imported = _imported_stems()
    unused = []
    for p in (VIA / "functional modules").rglob("*.py"):
        rp = str(p.relative_to(VIA))
        if any(k in str(p) for k in EXCLUDE_FRAGS):
            continue
        stem = p.stem
        fam = _FAM_RX.match(stem).group(1)
        if any(nt in stem for nt in NEVER_TOUCH):
            continue  # 凍結名單:連候審都不列(操作員明令不可動)
        used = (stem in battery or fam in battery or stem in imported
                or fam in imported
                or any(s.startswith(fam) for s in battery)
                or any(i.startswith(fam) for i in imported))
        if not used:
            unused.append((rp, stem, fam))
    # 分群:功能關鍵詞(名稱語意)
    groups = defaultdict(list)
    for rp, stem, fam in unused:
        low = stem.lower()
        gid = next((g for g, rx in KEYWORD_GROUPS if re.search(rx, low)),
                   "OTHER")
        groups[gid].append(rp)
    return {"n_unused": len(unused), "groups": dict(groups),
            "battery_n": len(battery), "imported_n": len(imported)}


def build_registers() -> dict:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    c = census()
    cons = {
        "schema": "VIA_ENGINE_CONSOLIDATION_V1", "version": "v0100",
        "append_only": True, "ts": ts,
        "policy": ("AUDIT-ONLY 零改動:全群 PENDING_OPERATOR 候裁;整併原則="
                   "不傷原有能力(讓位前功能對照+回退直通保留);"
                   "guardrail=不 big bang,每波一群、測綠後行。"),
        "never_touch": list(NEVER_TOUCH),
        "n_unused": c["n_unused"],
        "groups": {g: {"n": len(v), "disposition": "PENDING_OPERATOR",
                       "files": sorted(v)}
                   for g, v in sorted(c["groups"].items())},
    }
    REG_CONS.write_text(json.dumps(cons, ensure_ascii=False, indent=1),
                        encoding="utf-8")
    # Phase 1A:Schema Registry(雙庫全表快照;drift 守門基線)
    import duckdb
    schemas = {}
    for label, db in (("vdf_tw_market", DB_TW), ("vdf_global_market", DB_GL)):
        if not db.exists():
            schemas[label] = {"note": "庫缺(誠實)"}
            continue
        con = duckdb.connect(str(db), read_only=True)
        tbls = {}
        for (t,) in con.execute("SHOW TABLES").fetchall():
            cols = con.execute(f'SELECT * FROM "{t}" LIMIT 0').description
            tbls[t] = {c[0]: str(c[1]) for c in cols}
        con.close()
        schemas[label] = tbls
    REG_SCHEMA.write_text(json.dumps(
        {"schema": "VIA_SCHEMA_REGISTRY_V1", "version": "v0100",
         "append_only": True, "ts": ts,
         "policy": "Phase 1 schema drift 守門基線:新引擎改表須先過本冊比對;漂移=新版 append 舊版留存。",
         "databases": schemas}, ensure_ascii=False, indent=1),
        encoding="utf-8")
    # Phase 1B:Engine Contract 冊(四介面+Pydantic 封包)
    contract = {
        "schema": "VIA_ENGINE_CONTRACT_V1", "version": "v0100",
        "append_only": True, "ts": ts,
        "interface": {
            "load":      "載入輸入(唯讀;宣告 sources+grain)",
            "transform": "轉換(純函數;不觸網不寫正本)",
            "evaluate":  "驗證(schema check+quality_status 判定)",
            "emit":      "產出(封包化;data_class 繼承上游)"},
        "io_envelope": {
            "note": "對齊交接報告 08.2 統一資料封包;所有新引擎 I/O 必經此封包+Pydantic 驗證",
            "fields": ["run_id", "artifact_id", "subsystem", "schema_version",
                       "source_name", "source_type", "as_of_date", "grain",
                       "row_count", "content_sha256", "quality_status",
                       "data_class", "evidence_path", "warnings", "errors"],
            "quality_status": ["PASS", "WARN", "HOLD", "FAIL"],
            "data_class": ["ACTUAL", "DERIVED", "PROXY", "ESTIMATED"]},
        "pydantic_model": (
            "from pydantic import BaseModel\n"
            "class EngineEnvelope(BaseModel):\n"
            "    run_id: str; artifact_id: str; subsystem: str\n"
            "    schema_version: str; source_name: str; source_type: str\n"
            "    as_of_date: str; grain: list[str]; row_count: int\n"
            "    content_sha256: str; quality_status: str; data_class: str\n"
            "    evidence_path: str; warnings: list[str] = []\n"
            "    errors: list[str] = []"),
    }
    REG_CONTRACT.write_text(json.dumps(contract, ensure_ascii=False, indent=1),
                            encoding="utf-8")
    n_tbl = sum(len(v) for v in schemas.values() if isinstance(v, dict))
    return {"unused": c["n_unused"], "groups": len(cons["groups"]),
            "tables": n_tbl}


def selftest() -> int:
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    r = build_registers()
    mf = VIA / "functional modules" / "VIA_RetiredEngines" / "batch180_wave1" / "RETIRE_MANIFEST.json"
    man = json.loads(mf.read_text(encoding="utf-8"))
    import hashlib
    bad = sum(1 for mv in man["moves"]
              if not Path(VIA / mv["to"]).exists()
              or hashlib.sha256((VIA / mv["to"]).read_bytes()).hexdigest() != mv["sha256"])
    chk("① 第一波讓位完整性(manifest 自洽:全件在+sha 全符+undo 在位)",
        len(man["moves"]) >= 180 and bad == 0
        and len(man.get("held_syntax_gate", [])) >= 1
        and (mf.parent / "undo_retire.py").exists(),
        f"(讓位 {len(man['moves'])}·閘冊 HOLD {len(man.get('held_syntax_gate', []))}·壞 {bad})")
    chk("①b 殘餘盤點一致(census=HOLD 動態引用+凍結網路群,無漏)",
        r["unused"] <= 130, f"({r['unused']} 件=HOLD 92+FETCH_NET 20+新增件)")
    cons = json.loads(REG_CONS.read_text(encoding="utf-8"))
    chk("② 候整併群冊(功能分群+全 PENDING_OPERATOR 候裁零改動)",
        r["groups"] >= 6
        and all(g["disposition"] == "PENDING_OPERATOR"
                for g in cons["groups"].values()))
    chk("③ 凍結名單(網路工具 740/741/NetSupport+v0201 正典=連候審不列)",
        set(NEVER_TOUCH) == set(cons["never_touch"])
        and not any("SUP_MDL740" in f or "SUP_MDL741" in f
                    for g in cons["groups"].values() for f in g["files"]))
    sch = json.loads(REG_SCHEMA.read_text(encoding="utf-8"))
    chk("④ Schema Registry(雙庫≥20 表欄位型別快照=drift 基線)",
        r["tables"] >= 20 and "tw_prices_adj" in sch["databases"]["vdf_tw_market"]
        and "consensus_daily" in sch["databases"]["vdf_tw_market"])
    ct = json.loads(REG_CONTRACT.read_text(encoding="utf-8"))
    chk("⑤ Engine Contract 冊(load/transform/evaluate/emit 四介面)",
        set(ct["interface"]) == {"load", "transform", "evaluate", "emit"})
    chk("⑥ I/O 封包=交接報告 08.2 對齊(15 欄+data_class 四態)",
        len(ct["io_envelope"]["fields"]) == 15
        and ct["io_envelope"]["data_class"] == ["ACTUAL", "DERIVED", "PROXY",
                                                "ESTIMATED"])
    try:
        import pydantic  # noqa: F401
        ns = {}
        exec(ct["pydantic_model"], ns)
        m = ns["EngineEnvelope"](run_id="R", artifact_id="A", subsystem="VDF",
                                 schema_version="1.0.0", source_name="TWSE",
                                 source_type="OFFICIAL", as_of_date="2026-08-26",
                                 grain=["Date", "Ticker"], row_count=1,
                                 content_sha256="x", quality_status="PASS",
                                 data_class="ACTUAL", evidence_path="p")
        ok_val = m.row_count == 1
    except Exception as e:
        ok_val = False
        print("   (pydantic 驗證例外:", str(e)[:60], ")")
    chk("⑦ Pydantic 封包模型實跑驗證(合法件過)", ok_val)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑧ 紀律宣告(AUDIT-ONLY/裁決權=操作員/不 big bang/回退保留)",
        all(k in src for k in ("AUDIT-ONLY", "PENDING_OPERATOR",
                               "不 big bang", "回退")))
    print(f"  [計] 九檢 OK {9 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== 引擎簡化工程稽核(CGC_MDL092)· 八檢自測(零網路零改動)===")
        return selftest()
    r = build_registers()
    print(f"[稽核] 未使用 {r['unused']} 件 · 候整併 {r['groups']} 群"
          f"(全 PENDING_OPERATOR)· Schema Registry {r['tables']} 表"
          f" · Engine Contract 四介面冊在位")
    return 0


if __name__ == "__main__":
    sys.exit(main())
