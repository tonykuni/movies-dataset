# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(全引擎導入令 2026-08-18;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # accel_map/fetch/pip_install/run_fast
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====
# =============================================================================
# VIA SuperBOM Content Parser / Loader v0100
# def 目的：把一個 GREEN 提案的 BOM 檔(CSV 或 relational JSON)parse 進 content-level
#          Super BOM SSOT 的 M01_ITEM / M02_BOM_EDGE / M03_ATTR。
# def Round-1 gate：先在 10 列樣本上 dry-run 驗證;不過關 -> 整檔不載入(BLOCKED)。
# def 隔離：無法辨識/型別錯誤的列 -> Q01_QUARANTINE(不阻斷主線)。
# def 安全政策：source read-only、DB append-only(CREATE IF NOT EXISTS、只 INSERT、
#             永不 UPDATE/DELETE/DROP)、no subprocess、no network、no canonical mutation。
# def 冪等：uid = sha12(來源|鍵);重跑同檔不會爆量(存在即跳過)。
# def 相容：Python 3.11+ ;需要 duckdb(pip install duckdb)。CSV/JSON 解析用標準庫。
# def VersionDate 20260703
# =============================================================================

import argparse
import csv
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# -----------------------------------------------------------------------------
# PARAMS
# -----------------------------------------------------------------------------
PARAM_ENGINE = "VIA_SuperBOM_ContentParser"
PARAM_VERSION = "v0100"
PARAM_SAMPLE_N = 10           # Round-1 dry-run sample size
PARAM_DRYRUN_MIN_PASS = 0.70  # required valid fraction in the sample to proceed

PARAM_VL = {
    "bg": "#f5f4f0", "ink": "#1e1d1a", "red": "#c96b5a",
    "green": "#5a9e6f", "blue": "#4c78a8", "teal": "#439a9a", "muted": "#8a857c",
}

# Header synonym map -> canonical field. This is the Round-1 Ontology layer.
# Extend by adding synonyms; never rename a canonical key (append-only spirit).
PARAM_SYNONYMS: Dict[str, List[str]] = {
    "item_number": ["item_number", "itemno", "item_no", "item", "pn", "partnumber", "part_number",
                    "partno", "part", "material", "material_number", "materialno", "child", "child_pn",
                    "childpn", "component", "component_pn", "料號", "子件", "零件", "品號"],
    "parent_number": ["parent", "parent_pn", "parentpn", "parent_item", "parent_number", "assembly",
                      "assy", "top", "top_level", "母件", "上階", "組件"],
    "qty_per": ["qty", "quantity", "qty_per", "qtyper", "usage", "qpa", "qty_pa", "用量", "數量", "使用量"],
    "qty_uom": ["uom", "unit", "units", "qty_uom", "單位"],
    "ref_des": ["refdes", "ref_des", "reference", "references", "designator", "designators",
                "location", "位號", "參考位號"],
    "description": ["description", "desc", "descr", "name", "item_name", "品名", "說明", "描述"],
    "item_rev": ["rev", "revision", "ecn", "eco_rev", "版本", "版次"],
    "item_class": ["class", "category", "type", "commodity", "component_type", "類別", "類型"],
    "mpn": ["mpn", "manufacturer_part", "mfr_pn", "mfrpn", "mpn_no", "廠商料號"],
    "manufacturer": ["manufacturer", "mfr", "mfg", "maker", "vendor", "supplier", "廠商", "供應商", "製造商"],
    "value": ["value", "val", "component_value", "電氣值", "值", "規格值"],
    "package": ["package", "footprint", "pkg", "case", "封裝", "包裝"],
    "level": ["level", "lvl", "bom_level", "indent", "階", "階層"],
    "find_no": ["find_no", "findno", "position", "pos", "line", "line_no", "seq", "項次", "序號"],
    "populate_flag": ["populate", "populate_flag", "dnp", "fitted", "nofit", "no_populate", "貼裝"],
}

# -----------------------------------------------------------------------------
# EMBEDDED DDL  (self-contained; consistent with super_bom_ssot_template.sql)
# -----------------------------------------------------------------------------
PARAM_DDL = r"""
CREATE SCHEMA IF NOT EXISTS sbom;
CREATE TABLE IF NOT EXISTS sbom.M01_ITEM (
  item_uid VARCHAR PRIMARY KEY, item_number VARCHAR NOT NULL, item_rev VARCHAR NOT NULL DEFAULT '-',
  item_tier VARCHAR NOT NULL, item_class VARCHAR, description VARCHAR,
  base_uom VARCHAR NOT NULL DEFAULT 'EA',
  lifecycle VARCHAR NOT NULL DEFAULT 'ACTIVE'
    CHECK (lifecycle IN ('ACTIVE','NRND','EOL','OBSOLETE','DEPRECATED')),
  make_buy VARCHAR NOT NULL DEFAULT 'BUY'
    CHECK (make_buy IN ('MAKE','BUY','PHANTOM','SUBCON','CONSIGNED')),
  ext JSON, src_system VARCHAR, src_ref VARCHAR, ingest_batch VARCHAR,
  ingest_ts TIMESTAMP DEFAULT current_timestamp, confidence DOUBLE DEFAULT 1.0,
  ssot_status VARCHAR DEFAULT 'ACTIVE' CHECK (ssot_status IN ('ACTIVE','QUARANTINE','DEPRECATED')),
  valid_from TIMESTAMP DEFAULT current_timestamp, valid_to TIMESTAMP, superseded_by VARCHAR
);
CREATE TABLE IF NOT EXISTS sbom.M02_BOM_EDGE (
  edge_uid VARCHAR PRIMARY KEY, parent_uid VARCHAR NOT NULL, child_uid VARCHAR NOT NULL,
  find_no INTEGER, qty_per DOUBLE NOT NULL DEFAULT 1.0, qty_uom VARCHAR NOT NULL DEFAULT 'EA',
  ref_des VARCHAR[], ref_des_count INTEGER GENERATED ALWAYS AS (COALESCE(len(ref_des),0)) VIRTUAL,
  populate_flag VARCHAR NOT NULL DEFAULT 'FITTED' CHECK (populate_flag IN ('FITTED','DNP')),
  alt_group VARCHAR, alt_rank INTEGER DEFAULT 1,
  bom_view VARCHAR NOT NULL DEFAULT 'ENGINEERING'
    CHECK (bom_view IN ('ENGINEERING','MANUFACTURING','PLANNING','COSTED')),
  eco_in VARCHAR, eco_out VARCHAR, eff_from DATE, eff_to DATE, ext JSON,
  src_system VARCHAR, src_ref VARCHAR, ingest_batch VARCHAR,
  ingest_ts TIMESTAMP DEFAULT current_timestamp, confidence DOUBLE DEFAULT 1.0,
  ssot_status VARCHAR DEFAULT 'ACTIVE' CHECK (ssot_status IN ('ACTIVE','QUARANTINE','DEPRECATED')),
  valid_from TIMESTAMP DEFAULT current_timestamp, valid_to TIMESTAMP, superseded_by VARCHAR
);
CREATE TABLE IF NOT EXISTS sbom.M03_ATTR (
  attr_uid VARCHAR PRIMARY KEY, owner_kind VARCHAR NOT NULL CHECK (owner_kind IN ('ITEM','EDGE')),
  owner_uid VARCHAR NOT NULL, ns VARCHAR NOT NULL, attr_key VARCHAR NOT NULL,
  val_text VARCHAR, val_num DOUBLE, val_json JSON, unit VARCHAR,
  src_system VARCHAR, ingest_batch VARCHAR, ingest_ts TIMESTAMP DEFAULT current_timestamp,
  confidence DOUBLE DEFAULT 1.0,
  ssot_status VARCHAR DEFAULT 'ACTIVE' CHECK (ssot_status IN ('ACTIVE','QUARANTINE','DEPRECATED')),
  valid_from TIMESTAMP DEFAULT current_timestamp, valid_to TIMESTAMP, superseded_by VARCHAR
);
CREATE TABLE IF NOT EXISTS sbom.R01_ATTR_DEF (
  ns VARCHAR NOT NULL, attr_key VARCHAR NOT NULL,
  data_type VARCHAR NOT NULL DEFAULT 'text' CHECK (data_type IN ('text','num','json')),
  unit_hint VARCHAR, applies_to VARCHAR NOT NULL DEFAULT 'ITEM',
  promoted BOOLEAN DEFAULT FALSE, description VARCHAR,
  added_by VARCHAR DEFAULT 'CONTENT_PARSER', added_ts TIMESTAMP DEFAULT current_timestamp,
  PRIMARY KEY (ns, attr_key)
);
CREATE TABLE IF NOT EXISTS sbom.Q01_QUARANTINE (
  q_uid VARCHAR PRIMARY KEY, intake_ts TIMESTAMP DEFAULT current_timestamp,
  src_system VARCHAR, ingest_batch VARCHAR, reason_code VARCHAR, raw_json JSON,
  confidence DOUBLE, resolved BOOLEAN DEFAULT FALSE
);
CREATE OR REPLACE VIEW sbom.V_ITEM_CURRENT AS
  SELECT * FROM sbom.M01_ITEM WHERE valid_to IS NULL AND ssot_status = 'ACTIVE';
CREATE OR REPLACE VIEW sbom.V_EDGE_CURRENT AS
  SELECT * FROM sbom.M02_BOM_EDGE WHERE valid_to IS NULL AND ssot_status = 'ACTIVE';
CREATE OR REPLACE VIEW sbom.V_REFDES_GUARD AS
  SELECT edge_uid, parent_uid, child_uid, qty_per, ref_des_count, ref_des
  FROM sbom.V_EDGE_CURRENT
  WHERE populate_flag = 'FITTED' AND ref_des_count > 0 AND ref_des_count <> qty_per;
"""

# -----------------------------------------------------------------------------
# COMMON
# -----------------------------------------------------------------------------
def def_now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def def_run_id() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + PARAM_VERSION


def def_safe_str(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def def_sha12(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()[:12]


def def_to_float(value: Any) -> Optional[float]:
    # Strict numeric parse. A component VALUE like '10K' must NOT parse as a qty.
    raw = def_safe_str(value).replace(",", "")
    if raw == "":
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def def_split_refdes(value: Any) -> List[str]:
    raw = def_safe_str(value)
    if raw == "":
        return []
    for sep in [";", ",", " "]:
        raw = raw.replace(sep, "|")
    return [tok for tok in (part.strip() for part in raw.split("|")) if tok]


# -----------------------------------------------------------------------------
# READ
# -----------------------------------------------------------------------------
def def_read_csv(path: Path) -> Tuple[List[str], List[Dict[str, Any]]]:
    with path.open("r", encoding="utf-8-sig", errors="ignore", newline="") as handle:
        reader = csv.DictReader(handle)
        headers = reader.fieldnames or []
        rows = [dict(row) for row in reader]
    return headers, rows


def def_read_json_records(path: Path) -> Tuple[str, List[Dict[str, Any]], Dict[str, Any]]:
    # Returns (shape, records, relational). shape in {flat, relational, unknown}.
    data = json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    if isinstance(data, list) and data and isinstance(data[0], dict):
        return "flat", data, {}
    if isinstance(data, dict):
        items = data.get("items") or data.get("nodes") or data.get("M01_ITEM")
        edges = data.get("edges") or data.get("links") or data.get("bom") or data.get("M02_BOM_EDGE")
        if isinstance(items, list) or isinstance(edges, list):
            return "relational", [], {"items": items or [], "edges": edges or [],
                                       "attributes": data.get("attributes") or data.get("M03_ATTR") or []}
        records = data.get("records") or data.get("rows")
        if isinstance(records, list):
            return "flat", records, {}
    return "unknown", [], {}


# -----------------------------------------------------------------------------
# HEADER MAPPING  (Round-1 ontology)
# -----------------------------------------------------------------------------
def def_norm_header(name: str) -> str:
    return def_safe_str(name).lower().replace(" ", "").replace("_", "").replace("-", "")


def def_map_headers(headers: List[str]) -> Dict[str, str]:
    lookup = {def_norm_header(h): h for h in headers}
    mapping: Dict[str, str] = {}
    for canonical, syns in PARAM_SYNONYMS.items():
        for syn in syns:
            key = def_norm_header(syn)
            if key in lookup:
                mapping[canonical] = lookup[key]
                break
    return mapping


def def_unmapped_headers(headers: List[str], mapping: Dict[str, str]) -> List[str]:
    used = set(mapping.values())
    return [h for h in headers if h not in used]


# -----------------------------------------------------------------------------
# NORMALIZE A ROW  -> item(s) + optional edge + attrs, or a quarantine reason
# -----------------------------------------------------------------------------
def def_normalize_row(row: Dict[str, Any], mapping: Dict[str, str],
                      unmapped: List[str]) -> Dict[str, Any]:
    result: Dict[str, Any] = {"ok": False, "reason": "", "child": None, "parent": None,
                              "qty": 1.0, "ref_des": [], "attrs": [], "raw": row}
    if not any(def_safe_str(v) for v in row.values()):
        result["reason"] = "EMPTY_ROW"
        return result

    child_pn = def_safe_str(row.get(mapping.get("item_number", "__none__")))
    if child_pn == "":
        result["reason"] = "NO_ITEM_NUMBER"
        return result

    qty_raw = row.get(mapping.get("qty_per", "__none__"))
    if "qty_per" in mapping and def_safe_str(qty_raw) != "":
        qty = def_to_float(qty_raw)
        if qty is None:
            result["reason"] = "NON_NUMERIC_QTY"
            return result
    else:
        qty = 1.0  # qty is NEVER inferred from a component value token

    result["child"] = {
        "item_number": child_pn,
        "item_rev": def_safe_str(row.get(mapping.get("item_rev", "__none__"))) or "-",
        "item_class": def_safe_str(row.get(mapping.get("item_class", "__none__"))) or None,
        "description": def_safe_str(row.get(mapping.get("description", "__none__"))) or None,
        "base_uom": def_safe_str(row.get(mapping.get("qty_uom", "__none__"))) or "EA",
    }
    if "parent_number" in mapping:
        parent_pn = def_safe_str(row.get(mapping["parent_number"]))
        result["parent"] = parent_pn or None
    result["qty"] = qty
    result["qty_uom"] = result["child"]["base_uom"]
    result["find_no"] = def_to_float(row.get(mapping.get("find_no", "__none__")))
    if "ref_des" in mapping:
        result["ref_des"] = def_split_refdes(row.get(mapping["ref_des"]))

    pf = def_safe_str(row.get(mapping.get("populate_flag", "__none__"))).lower()
    result["populate_flag"] = "DNP" if pf in {"dnp", "nofit", "no", "0", "false"} else "FITTED"

    # attrs: mapped electronics fields (value goes to component_value, NEVER qty)
    attrs: List[Tuple[str, str, str]] = []  # (ns, key, value)
    for canon, key in (("value", "component_value"), ("package", "package"),
                       ("mpn", "mpn"), ("manufacturer", "manufacturer")):
        if canon in mapping:
            val = def_safe_str(row.get(mapping[canon]))
            if val:
                attrs.append(("SSOT", key, val))
    # unmapped columns -> namespace-isolated SRC attrs (lossless, add-only)
    for header in unmapped:
        val = def_safe_str(row.get(header))
        if val:
            attrs.append(("SRC", def_norm_header(header), val))
    result["attrs"] = attrs
    result["ok"] = True
    return result


# -----------------------------------------------------------------------------
# DRY-RUN GATE  (Round-1: validate a 10-row sample before any write)
# -----------------------------------------------------------------------------
def def_dryrun(records: List[Dict[str, Any]], mapping: Dict[str, str],
               unmapped: List[str]) -> Dict[str, Any]:
    sample = records[:PARAM_SAMPLE_N]
    n = len(sample)
    verdict = {"sampled": n, "valid": 0, "issues": [], "mapping_ok": "item_number" in mapping,
               "pass": False, "reason": ""}
    if n == 0:
        verdict["reason"] = "NO_DATA_ROWS"
        return verdict
    if not verdict["mapping_ok"]:
        verdict["reason"] = "ITEM_NUMBER_COLUMN_NOT_RESOLVED"
        return verdict
    counted = 0
    for idx, row in enumerate(sample):
        norm = def_normalize_row(row, mapping, unmapped)
        if norm["reason"] == "EMPTY_ROW":
            continue  # blank separator line: skipped, not a failure
        counted += 1
        if norm["ok"]:
            verdict["valid"] += 1
        else:
            verdict["issues"].append({"row": idx, "reason": norm["reason"]})
    if counted == 0:
        verdict["reason"] = "NO_NONEMPTY_ROWS"
        return verdict
    frac = verdict["valid"] / counted
    verdict["counted"] = counted
    verdict["valid_fraction"] = round(frac, 3)
    verdict["pass"] = frac >= PARAM_DRYRUN_MIN_PASS
    if not verdict["pass"]:
        verdict["reason"] = f"SAMPLE_PASS_{frac:.2f}_BELOW_{PARAM_DRYRUN_MIN_PASS}"
    return verdict


# -----------------------------------------------------------------------------
# LOAD  (add-only, idempotent; DuckDB)
# -----------------------------------------------------------------------------
def def_ensure_db(con) -> None:
    con.execute(PARAM_DDL)


def def_item_uid(src: str, item_number: str, item_rev: str) -> str:
    return "I-" + def_sha12(f"{src}|{item_number}|{item_rev}")


def def_exists(con, table: str, uid_col: str, uid: str) -> bool:
    row = con.execute(f"SELECT 1 FROM sbom.{table} WHERE {uid_col} = ? LIMIT 1", [uid]).fetchone()
    return row is not None


def def_infer_tier(is_parent: bool, is_top: bool, given: Optional[str]) -> str:
    if given:
        return given
    if is_top:
        return "T6"
    if is_parent:
        return "T4"
    return "T2"


def def_load(con, records: List[Dict[str, Any]], mapping: Dict[str, str], unmapped: List[str],
             src: str, run_id: str, top_hint: str) -> Dict[str, Any]:
    stats = {"items": 0, "edges": 0, "attrs": 0, "quarantined": 0,
             "quarantine_reasons": {}, "skipped_existing": 0}
    src_name = Path(src).name

    normalized: List[Dict[str, Any]] = []
    parents_seen: set = set()
    for row in records:
        norm = def_normalize_row(row, mapping, unmapped)
        if norm["reason"] == "EMPTY_ROW":
            continue  # blank separator line: skip silently, keep quarantine clean
        if not norm["ok"]:
            q_uid = "Q-" + def_sha12(f"{src}|{run_id}|{json.dumps(norm['raw'], ensure_ascii=False, sort_keys=True)}")
            if not def_exists(con, "Q01_QUARANTINE", "q_uid", q_uid):
                con.execute(
                    "INSERT INTO sbom.Q01_QUARANTINE (q_uid,src_system,ingest_batch,reason_code,raw_json,confidence,resolved) "
                    "VALUES (?,?,?,?,CAST(? AS JSON),?,FALSE)",
                    [q_uid, src_name, run_id, norm["reason"],
                     json.dumps(norm["raw"], ensure_ascii=False), 0.0])
            stats["quarantined"] += 1
            stats["quarantine_reasons"][norm["reason"]] = stats["quarantine_reasons"].get(norm["reason"], 0) + 1
            continue
        normalized.append(norm)
        if norm.get("parent"):
            parents_seen.add(norm["parent"])

    has_explicit_parent = "parent_number" in mapping
    has_level = "level" in mapping

    # Mode B: infer parent from a level stack when no explicit parent column.
    level_stack: Dict[int, str] = {}
    top_pn = def_safe_str(top_hint) or (Path(src).stem + "__TOP")
    synthetic_top_used = False

    def _upsert_item(item_number: str, rev: str, is_parent: bool, is_top: bool,
                     item_class=None, description=None, base_uom="EA") -> str:
        uid = def_item_uid(src, item_number, rev)
        if not def_exists(con, "M01_ITEM", "item_uid", uid):
            tier = def_infer_tier(is_parent, is_top, None)
            make_buy = "MAKE" if (is_parent or is_top) else "BUY"
            con.execute(
                "INSERT INTO sbom.M01_ITEM (item_uid,item_number,item_rev,item_tier,item_class,"
                "description,base_uom,lifecycle,make_buy,ext,src_system,src_ref,ingest_batch,confidence,ssot_status) "
                "VALUES (?,?,?,?,?,?,?,'ACTIVE',?,NULL,?,?,?,?, 'ACTIVE')",
                [uid, item_number, rev, tier, item_class, description, base_uom, make_buy,
                 src_name, src, run_id, 1.0])
            stats["items"] += 1
        else:
            stats["skipped_existing"] += 1
        return uid

    for seq, norm in enumerate(normalized, start=1):
        child = norm["child"]
        is_parent_child = child["item_number"] in parents_seen
        child_uid = _upsert_item(child["item_number"], child["item_rev"], is_parent_child, False,
                                 child["item_class"], child["description"], child["base_uom"])

        # resolve parent
        parent_pn = None
        if has_explicit_parent and norm.get("parent"):
            parent_pn = norm["parent"]
        elif has_level:
            lvl_raw = def_to_float(norm["raw"].get(mapping["level"]))
            lvl = int(lvl_raw) if lvl_raw is not None else 1
            level_stack[lvl] = child["item_number"]
            parent_at = level_stack.get(lvl - 1)
            parent_pn = parent_at  # None at top level
        if parent_pn is None:
            parent_pn = top_pn
            synthetic_top_used = True

        parent_uid = _upsert_item(parent_pn, "-", True, parent_pn == top_pn)

        # edge (skip self-loop)
        if parent_uid != child_uid:
            find_no = int(norm["find_no"]) if norm["find_no"] is not None else seq * 10
            edge_uid = "E-" + def_sha12(f"{src}|{parent_pn}|{child['item_number']}|{find_no}")
            if not def_exists(con, "M02_BOM_EDGE", "edge_uid", edge_uid):
                ref = norm["ref_des"] if norm["ref_des"] else None
                con.execute(
                    "INSERT INTO sbom.M02_BOM_EDGE (edge_uid,parent_uid,child_uid,find_no,qty_per,qty_uom,"
                    "ref_des,populate_flag,alt_rank,bom_view,src_system,src_ref,ingest_batch,confidence,ssot_status) "
                    "VALUES (?,?,?,?,?,?,?,?,1,'ENGINEERING',?,?,?,?, 'ACTIVE')",
                    [edge_uid, parent_uid, child_uid, find_no, norm["qty"], norm["qty_uom"],
                     ref, norm["populate_flag"], src_name, src, run_id, 1.0])
                stats["edges"] += 1
            else:
                stats["skipped_existing"] += 1

        # attrs
        for ns, key, val in norm["attrs"]:
            attr_uid = "A-" + def_sha12(f"{child_uid}|{ns}|{key}")
            if def_exists(con, "M03_ATTR", "attr_uid", attr_uid):
                continue
            num = def_to_float(val) if ns == "SSOT" and key in {"tolerance_pct"} else None
            con.execute(
                "INSERT INTO sbom.M03_ATTR (attr_uid,owner_kind,owner_uid,ns,attr_key,val_text,val_num,"
                "val_json,unit,src_system,ingest_batch,confidence,ssot_status) "
                "VALUES (?, 'ITEM', ?,?,?,?,?,NULL,NULL,?,?,?, 'ACTIVE')",
                [attr_uid, child_uid, ns, key, val, num, src_name, run_id, 1.0])
            stats["attrs"] += 1
            # register the attr def (add-only)
            con.execute(
                "INSERT INTO sbom.R01_ATTR_DEF (ns,attr_key,data_type,applies_to,promoted,description,added_by) "
                "SELECT ?,?,?, 'ITEM', FALSE, ?, 'CONTENT_PARSER' "
                "WHERE NOT EXISTS (SELECT 1 FROM sbom.R01_ATTR_DEF WHERE ns=? AND attr_key=?)",
                [ns, key, "num" if num is not None else "text", f"auto from {src_name}", ns, key])

    stats["synthetic_top_used"] = synthetic_top_used
    return stats


# -----------------------------------------------------------------------------
# HTML REPORT  (Visual Lock RYG)
# -----------------------------------------------------------------------------
def def_render_html(src_name: str, run_id: str, verdict: Dict[str, Any],
                    stats: Optional[Dict[str, Any]], refdes_flags: int) -> str:
    vl = PARAM_VL
    loaded = stats is not None
    gate_color = vl["green"] if (loaded and verdict.get("pass")) else vl["red"]
    gate_text = "PROCEED · LOADED" if loaded else "BLOCKED · NOT LOADED"
    s = stats or {"items": 0, "edges": 0, "attrs": 0, "quarantined": 0, "quarantine_reasons": {}}

    qrows = "".join(
        f'<tr><td class="mono">{r}</td><td class="mono">{c}</td></tr>'
        for r, c in (s.get("quarantine_reasons") or {}).items()
    ) or '<tr><td colspan="2" class="muted">none</td></tr>'

    tpl = '''<!DOCTYPE html>
<html lang="zh-Hant"><head><meta charset="utf-8"><title>SuperBOM Load Report</title>
<style>
 body{background:__BG__;color:__INK__;font-family:"DM Sans","Noto Sans TC",sans-serif;margin:0;padding:32px}
 h1{font-family:"Syne","DM Sans",sans-serif;font-size:22px;margin:0 0 4px}
 .sub{color:__MUTED__;font-size:13px;margin-bottom:18px}
 .gate{display:inline-block;padding:6px 14px;border-radius:3px;color:#fff;font-weight:600;font-size:13px;background:__GATE__}
 .cards{display:flex;gap:12px;margin:18px 0}
 .card{border:1px solid rgba(30,29,26,.12);border-radius:3px;padding:12px 16px;min-width:96px}
 .card .n{font-size:24px;font-family:"DM Mono",monospace}
 .g{color:__GREEN__}.r{color:__RED__}.y{color:__BLUE__}
 table{border-collapse:collapse;font-size:13px;margin-top:8px}
 th,td{text-align:left;padding:6px 12px;border-bottom:1px solid rgba(30,29,26,.10)}
 th{font-size:11px;text-transform:uppercase;letter-spacing:.04em;color:__MUTED__}
 .mono{font-family:"DM Mono",monospace;font-size:12px}.muted{color:__MUTED__}
 .policy{margin-top:22px;font-size:12px;color:__MUTED__;border-top:1px solid rgba(30,29,26,.10);padding-top:12px}
</style></head><body>
<h1>VIA SuperBOM · Content Load Report</h1>
<div class="sub">__SRC__ · run __RUN__ · Round-1 dry-run sample __SAMP__ · valid __VF__</div>
<div class="gate">__GATETXT__</div>
<div class="cards">
 <div class="card"><div class="muted">ITEMS (M01)</div><div class="n g">__ITEMS__</div></div>
 <div class="card"><div class="muted">EDGES (M02)</div><div class="n g">__EDGES__</div></div>
 <div class="card"><div class="muted">ATTRS (M03)</div><div class="n g">__ATTRS__</div></div>
 <div class="card"><div class="muted">QUARANTINED</div><div class="n r">__QN__</div></div>
 <div class="card"><div class="muted">REFDES≠QTY</div><div class="n y">__RD__</div></div>
</div>
<table><thead><tr><th>Quarantine Reason</th><th>Count</th></tr></thead><tbody>__QROWS__</tbody></table>
<div class="policy">Policy: SOURCE READ_ONLY · DB APPEND_ONLY (INSERT only, no UPDATE/DELETE/DROP) · idempotent re-run · Q01 non-blocking. REFDES≠QTY rows are loaded and flagged by V_REFDES_GUARD, not dropped.</div>
</body></html>'''
    return (tpl.replace("__BG__", vl["bg"]).replace("__INK__", vl["ink"]).replace("__MUTED__", vl["muted"])
            .replace("__GREEN__", vl["green"]).replace("__RED__", vl["red"]).replace("__BLUE__", vl["blue"])
            .replace("__GATE__", gate_color).replace("__GATETXT__", gate_text)
            .replace("__SRC__", src_name).replace("__RUN__", run_id)
            .replace("__SAMP__", str(verdict.get("sampled", 0)))
            .replace("__VF__", str(verdict.get("valid_fraction", 0.0)))
            .replace("__ITEMS__", str(s["items"])).replace("__EDGES__", str(s["edges"]))
            .replace("__ATTRS__", str(s["attrs"])).replace("__QN__", str(s["quarantined"]))
            .replace("__RD__", str(refdes_flags)).replace("__QROWS__", qrows))


# -----------------------------------------------------------------------------
# ORCHESTRATE ONE FILE
# -----------------------------------------------------------------------------
def def_run_bom(bom_path: Path, db_path: Path, out_root: Path, top_hint: str = "") -> Dict[str, Any]:
    import duckdb
    run_id = def_run_id()
    out_root.mkdir(parents=True, exist_ok=True)
    ext = bom_path.suffix.lower()

    if ext in {".csv"}:
        headers, records = def_read_csv(bom_path)
        shape = "flat"
        relational: Dict[str, Any] = {}
    elif ext in {".json"}:
        shape, records, relational = def_read_json_records(bom_path)
        if shape == "relational":
            records = list(relational.get("edges") or [])
            headers = sorted({k for r in records for k in r.keys()}) if records else []
        else:
            headers = sorted({k for r in records for k in r.keys()}) if records else []
    else:
        raise ValueError(f"unsupported BOM extension: {ext} (use .csv or .json)")

    if shape == "unknown":
        headers, records = [], []

    mapping = def_map_headers(headers)
    unmapped = def_unmapped_headers(headers, mapping)
    verdict = def_dryrun(records, mapping, unmapped)

    con = duckdb.connect(str(db_path))
    def_ensure_db(con)

    stats = None
    if verdict["pass"]:
        stats = def_load(con, records, mapping, unmapped, str(bom_path), run_id, top_hint)
    else:
        # whole file blocked -> quarantine one summary record, load nothing
        q_uid = "Q-" + def_sha12(f"{bom_path}|{run_id}|DRYRUN_BLOCKED")
        con.execute(
            "INSERT INTO sbom.Q01_QUARANTINE (q_uid,src_system,ingest_batch,reason_code,raw_json,confidence,resolved) "
            "VALUES (?,?,?, 'DRYRUN_BLOCKED', CAST(? AS JSON), ?, FALSE)",
            [q_uid, bom_path.name, run_id, json.dumps(verdict, ensure_ascii=False), 0.0])

    refdes_flags = con.execute("SELECT COUNT(*) FROM sbom.V_REFDES_GUARD").fetchone()[0]
    con.close()

    html = def_render_html(bom_path.name, run_id, verdict, stats, refdes_flags)
    html_path = out_root / f"VIA_SuperBOM_Load_Report_{run_id}.html"
    html_path.write_text(html, encoding="utf-8")

    manifest = {
        "engine": PARAM_ENGINE, "version": PARAM_VERSION, "run_id": run_id,
        "generated_at": def_now_iso(), "source": str(bom_path), "shape": shape,
        "db": str(db_path), "header_mapping": mapping, "unmapped_headers": unmapped,
        "dryrun": verdict, "loaded": bool(verdict["pass"]), "load_stats": stats,
        "refdes_qty_flags": refdes_flags,
        "policy": "SOURCE_READ_ONLY_DB_APPEND_ONLY_IDEMPOTENT_Q01_NONBLOCKING",
        "report_html": str(html_path),
    }
    manifest_path = out_root / f"VIA_SuperBOM_Load_Manifest_{run_id}.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


# -----------------------------------------------------------------------------
# ORCHESTRATE FROM BRIDGE PROPOSALS  (only GREEN + PROPOSE_LOAD)
# -----------------------------------------------------------------------------
def def_run_from_proposals(proposals_path: Path, db_path: Path, out_root: Path) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    if proposals_path.suffix.lower() == ".json":
        data = json.loads(proposals_path.read_text(encoding="utf-8", errors="ignore"))
        if isinstance(data, list):
            for batch in data:
                rows.extend(batch.get("records", []) if isinstance(batch, dict) else [])
    else:
        with proposals_path.open("r", encoding="utf-8-sig", errors="ignore", newline="") as handle:
            rows = list(csv.DictReader(handle))
    targets = [r for r in rows if def_safe_str(r.get("def_ryg")) == "GREEN"
               and def_safe_str(r.get("def_bridge_gate")).startswith("PROPOSE_LOAD")]
    results = []
    for r in targets:
        src = Path(def_safe_str(r.get("def_source_path")))
        if src.exists() and src.suffix.lower() in {".csv", ".json"}:
            results.append(def_run_bom(src, db_path, out_root))
    return {"engine": PARAM_ENGINE, "from_proposals": str(proposals_path),
            "green_propose_load": len(targets), "loaded_files": len(results),
            "runs": results}


# -----------------------------------------------------------------------------
# SELFTEST
# -----------------------------------------------------------------------------
def def_selftest() -> int:
    import tempfile, duckdb
    tmp = Path(tempfile.mkdtemp())
    db = tmp / "superbom.duckdb"
    out = tmp / "out"

    # (1) explicit parent/child CSV with the 10K value + a ref_des/qty mismatch + dirty rows
    csv1 = tmp / "bom_explicit.csv"
    csv1.write_text(
        "Parent,PartNumber,Qty,RefDes,Value,Manufacturer,Description\n"
        "PCBA-77,IC-STM32,1,U1,,STMicro,MCU 32-bit\n"
        "PCBA-77,R-10K-0402,3,\"R1;R2;R3\",10K,Yageo,RES 10K\n"          # value 10K must be attr, qty=3
        "PCBA-77,R-10K-0402,5,\"R4;R5;R6\",10K,Yageo,RES 10K\n"          # qty5 vs 3 refdes -> flagged
        ",,,,,,\n"                                                        # EMPTY_ROW -> quarantine
        "PCBA-77,C-100N,two,C1,100nF,Murata,CAP\n"                        # NON_NUMERIC_QTY -> quarantine
        "FG-1000,PCBA-77,1,,,,Main Board\n",
        encoding="utf-8")
    m1 = def_run_bom(csv1, db, out)
    assert m1["loaded"], "csv1 should pass dry-run"
    st = m1["load_stats"]
    assert st["quarantined"] == 1, f"expected 1 quarantined (non-numeric qty), got {st['quarantined']}"
    assert "NON_NUMERIC_QTY" in st["quarantine_reasons"] and "EMPTY_ROW" not in st["quarantine_reasons"]
    assert m1["refdes_qty_flags"] == 1, f"expected 1 refdes flag, got {m1['refdes_qty_flags']}"

    con = duckdb.connect(str(db))
    # 10K guard: value stored as attr, never as qty
    val = con.execute("SELECT val_text FROM sbom.M03_ATTR WHERE attr_key='component_value' LIMIT 1").fetchone()
    assert val and val[0] == "10K", "component_value not stored as attr"
    maxq = con.execute("SELECT MAX(qty_per) FROM sbom.M02_BOM_EDGE").fetchone()[0]
    assert maxq == 5.0, "qty polluted by value token"
    n_items_1 = con.execute("SELECT COUNT(*) FROM sbom.M01_ITEM").fetchone()[0]
    n_edges_1 = con.execute("SELECT COUNT(*) FROM sbom.M02_BOM_EDGE").fetchone()[0]
    con.close()

    # (2) idempotency: rerun same file -> counts must NOT grow (add-only + dedup)
    def_run_bom(csv1, db, out)
    con = duckdb.connect(str(db))
    n_items_2 = con.execute("SELECT COUNT(*) FROM sbom.M01_ITEM").fetchone()[0]
    n_edges_2 = con.execute("SELECT COUNT(*) FROM sbom.M02_BOM_EDGE").fetchone()[0]
    con.close()
    assert (n_items_1, n_edges_1) == (n_items_2, n_edges_2), "re-run grew tables (not idempotent)"

    # (3) level-based CSV (parent inferred from indent level)
    csv2 = tmp / "bom_level.csv"
    csv2.write_text(
        "Level,Item,Qty,Desc\n"
        "1,ASSY-TOP,1,Top\n2,SUB-A,2,Sub A\n3,LEAF-1,4,Leaf\n2,SUB-B,1,Sub B\n",
        encoding="utf-8")
    m2 = def_run_bom(csv2, db, out, top_hint="ASSY-TOP")
    assert m2["loaded"]
    con = duckdb.connect(str(db))
    # LEAF-1 (level3) should hang under SUB-A (level2)
    row = con.execute("""
        SELECT p.item_number FROM sbom.V_EDGE_CURRENT e
        JOIN sbom.V_ITEM_CURRENT c ON c.item_uid=e.child_uid
        JOIN sbom.V_ITEM_CURRENT p ON p.item_uid=e.parent_uid
        WHERE c.item_number='LEAF-1'""").fetchone()
    assert row and row[0] == "SUB-A", f"level inference wrong: {row}"
    con.close()

    # (4) relational JSON
    js = tmp / "rel.json"
    js.write_text(json.dumps({
        "items": [{"item_number": "M-1", "description": "Module"}],
        "edges": [{"parent": "M-1", "item_number": "SCREW", "qty": 4, "refdes": ""}]
    }, ensure_ascii=False), encoding="utf-8")
    m3 = def_run_bom(js, db, out, top_hint="M-1")
    assert m3["loaded"], "relational json should load"

    # (5) dry-run BLOCK: a file with no resolvable item_number column
    bad = tmp / "bad.csv"
    bad.write_text("colA,colB\nfoo,bar\nbaz,qux\n", encoding="utf-8")
    m4 = def_run_bom(bad, db, out)
    assert not m4["loaded"], "file with no item_number must be BLOCKED"
    assert m4["dryrun"]["reason"].startswith("ITEM_NUMBER"), m4["dryrun"]["reason"]

    print("SELFTEST PASS")
    print(json.dumps({"csv_explicit": m1["load_stats"], "level_loaded": m2["loaded"],
                      "relational_loaded": m3["loaded"], "bad_blocked": (not m4["loaded"])},
                     ensure_ascii=False))
    return 0


def def_parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="VIA SuperBOM Content Parser: BOM CSV/JSON -> M01/M02/M03 with dry-run gate + Q01.")
    parser.add_argument("--bom", default=None, help="BOM file (.csv or .json)")
    parser.add_argument("--from-proposals", default=None, help="bridge proposals (.csv/.json); loads GREEN PROPOSE_LOAD only")
    parser.add_argument("--db", default="superbom.duckdb", help="DuckDB SSOT file (append-only)")
    parser.add_argument("--output-root", default="VIA_SuperBOM_Load_Output", help="append-only report root")
    parser.add_argument("--top", default="", help="synthetic top assembly PN when BOM has no parent/level column")
    parser.add_argument("--selftest", action="store_true")
    return parser.parse_args()


def def_main() -> int:
    args = def_parse_args()
    if args.selftest:
        return def_selftest()
    if args.from_proposals:
        result = def_run_from_proposals(Path(args.from_proposals), Path(args.db), Path(args.output_root))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    if not args.bom:
        print("provide --bom <file.csv|.json>, or --from-proposals <bridge.csv|.json>, or --selftest")
        return 2
    manifest = def_run_bom(Path(args.bom), Path(args.db), Path(args.output_root), args.top)
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(def_main())
