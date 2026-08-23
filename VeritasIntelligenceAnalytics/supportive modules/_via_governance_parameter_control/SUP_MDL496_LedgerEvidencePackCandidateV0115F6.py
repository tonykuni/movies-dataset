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

import argparse
import csv
import html
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def read_json(path: Path) -> Any:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        rows = [{"def_empty": "true"}]
    cols: List[str] = []
    seen = set()
    for r in rows:
        for k in r.keys():
            if k not in seen:
                seen.add(k)
                cols.append(k)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def prop(row: Dict[str, Any], key: str, default: str = "") -> str:
    v = row.get(key, default)
    return "" if v is None else str(v)


def h(x: Any) -> str:
    return html.escape("" if x is None else str(x))


def build_green_ledger(rows: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    out = []
    n = 0
    for r in rows:
        if prop(r, "def_ryg") != "GREEN":
            continue
        n += 1
        track = prop(r, "def_precheck_track")
        clearance_type = "SECRET_FIELDNAME" if "FIELDNAME" in track else "COMMENT_DOC_FALSE_POSITIVE"

        out.append({
            "def_ledger_candidate_id": f"F6-GREEN-LEDGER-{n:06d}",
            "def_precheck_id": prop(r, "def_precheck_id"),
            "def_package_row_id": prop(r, "def_package_row_id"),
            "def_clearance_type": clearance_type,
            "def_subsystem": prop(r, "def_subsystem"),
            "def_source_rel_path": prop(r, "def_source_rel_path"),
            "def_basis": prop(r, "def_required_checks"),
            "def_candidate_status": "CLEARANCE_LEDGER_CANDIDATE_ONLY",
            "def_ledger_action": "record_as_candidate_not_apply",
            "def_auto_clear_allowed": "false",
            "def_requires_source_read": "false",
            "def_apply_enabled": "false",
            "def_source_mutation": "false",
            "def_db_write": "false",
            "def_next_gate": "v0115F7_CLEARANCE_LEDGER_VALIDATION_ONLY"
        })
    return out


def build_red_evidence(rows: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    out = []
    n = 0
    for r in rows:
        if prop(r, "def_ryg") != "RED":
            continue
        n += 1
        track = prop(r, "def_precheck_track")
        if "SECRET" in track:
            pack_type = "TRUE_SECRET_RUNTIME_EVIDENCE_PACK"
            required = "env_presence_policy; plaintext_secret_block; ui_no_localstorage; masking_contract; operator_review"
        else:
            pack_type = "TRUE_DANGER_CONTEXT_EVIDENCE_PACK"
            required = "active_source_boundary; command_context; no_apply_guard; no_mutation_guard; operator_review"

        out.append({
            "def_red_evidence_pack_id": f"F6-RED-EVIDENCE-{n:06d}",
            "def_precheck_id": prop(r, "def_precheck_id"),
            "def_package_row_id": prop(r, "def_package_row_id"),
            "def_evidence_pack_type": pack_type,
            "def_subsystem": prop(r, "def_subsystem"),
            "def_source_rel_path": prop(r, "def_source_rel_path"),
            "def_hydra_risk": prop(r, "def_hydra_risk"),
            "def_fix_class": prop(r, "def_fix_class"),
            "def_required_evidence": required,
            "def_candidate_status": "EVIDENCE_PACK_CANDIDATE_ONLY",
            "def_repair_allowed": "false",
            "def_requires_manual_review": "true",
            "def_requires_source_read": "false",
            "def_apply_enabled": "false",
            "def_source_mutation": "false",
            "def_db_write": "false",
            "def_next_gate": "v0115F7_RED_EVIDENCE_PACK_VALIDATION_ONLY"
        })
    return out


def build_yellow_confirmation(rows: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    out = []
    n = 0
    for r in rows:
        if prop(r, "def_ryg") != "YELLOW":
            continue
        n += 1
        track = prop(r, "def_precheck_track")
        if "PATH_SIZE" in track:
            confirm_type = "PATH_SIZE_SAMPLE_PLAN"
            required = "bounded_bytes_only; no_full_read; file_type; sample_strategy"
            next_gate = "v0115F7_PATH_SIZE_SAMPLE_PLAN_VALIDATION_ONLY"
        elif "ARTIFACT" in track:
            confirm_type = "ARTIFACT_FALSE_POSITIVE_CONFIRMATION"
            required = "backup_path; output_path; report_path; template_path; historical_run_path"
            next_gate = "v0115F7_ARTIFACT_CONFIRMATION_LEDGER_VALIDATION_ONLY"
        else:
            confirm_type = "BOUNDARY_CONFIRMATION"
            required = "gate_status; dryrun_status; no_apply_label; no_mutation_label; disabled_boundary_marker"
            next_gate = "v0115F7_BOUNDARY_CONFIRMATION_VALIDATION_ONLY"

        out.append({
            "def_yellow_confirmation_id": f"F6-YELLOW-CONFIRM-{n:06d}",
            "def_precheck_id": prop(r, "def_precheck_id"),
            "def_package_row_id": prop(r, "def_package_row_id"),
            "def_confirmation_type": confirm_type,
            "def_subsystem": prop(r, "def_subsystem"),
            "def_source_rel_path": prop(r, "def_source_rel_path"),
            "def_required_confirmation": required,
            "def_candidate_status": "CONFIRMATION_CANDIDATE_ONLY",
            "def_repair_allowed": "false",
            "def_requires_source_read": "false",
            "def_apply_enabled": "false",
            "def_source_mutation": "false",
            "def_db_write": "false",
            "def_next_gate": next_gate
        })
    return out


def build_governance_bridge(default_params: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows = []
    n = 0

    def add(section: str, name: str, value: Any, meaning: str) -> None:
        nonlocal n
        n += 1
        rows.append({
            "def_param_id": f"F6-GOV-PARAM-{n:04d}",
            "def_section": section,
            "def_parameter": name,
            "def_value": json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list, bool, int, float)) else str(value),
            "def_meaning": meaning,
            "def_mutable_in_f6": "false",
            "def_source_mutation": "false",
            "def_apply_enabled": "false"
        })

    policy = default_params.get("governance_policy", {})
    params = default_params.get("default_parameters", {})
    counts = default_params.get("counts", {})
    next_phase = default_params.get("next_phase", {})

    for k, v in policy.items():
        add("governance_policy", k, v, "F5 policy carried into F6 as read-only control.")
    for k, v in params.items():
        add("default_parameters", k, v, "Default runtime/control parameter, not applied to source.")
    for k, v in counts.items():
        add("counts", k, v, "Expected continuity count from F5.")
    add("next_phase", "recommended", next_phase.get("recommended", ""), "Recommended next phase from F5.")
    add("next_phase", "blocked", next_phase.get("blocked", []), "Blocked actions must remain blocked in F6.")

    return rows


def build_process_matrix(red: List[Dict[str, Any]], yellow: List[Dict[str, Any]], green: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    all_rows = red + yellow + green
    sub = Counter(prop(r, "def_subsystem") for r in all_rows)

    return [
        {
            "PROCESS": "01 GREEN Clearance Ledger Candidate",
            "SUPPORTIVE MODULES": f"Supportive green candidates tracked; no source read. Supportive total={sub['Supportive_NexusCore_Env']}",
            "VDF": "VDF fieldname/schema/parameter labels enter candidate ledger only.",
            "VAP": "VAP UI/comment/doc false positives enter candidate ledger only.",
            "OTHERS": "VRN/VIS/Registry/Unclassified only candidate ledger, no canonical merge.",
            "RYG": "GREEN",
            "COUNT": str(len(green)),
            "NEXT": "v0115F7 clearance ledger validation only"
        },
        {
            "PROCESS": "02 RED Evidence Pack Candidate",
            "SUPPORTIVE MODULES": "Danger/secret nodes locked; evidence pack only.",
            "VDF": "VDF danger/secret requires context evidence before any repair discussion.",
            "VAP": "VAP active script danger remains manual review only.",
            "OTHERS": "Unclassified must be classified before any action.",
            "RYG": "RED",
            "COUNT": str(len(red)),
            "NEXT": "v0115F7 red evidence pack validation only"
        },
        {
            "PROCESS": "03 YELLOW Confirmation / Sample Plan",
            "SUPPORTIVE MODULES": "Boundary/artifact/path-size confirmation only.",
            "VDF": "VDF boundary and artifact rows need confirmation before clearance.",
            "VAP": "VAP path-size rows get bounded sample plan only; no full read.",
            "OTHERS": "Registry large files get sample plan only.",
            "RYG": "YELLOW",
            "COUNT": str(len(yellow)),
            "NEXT": "v0115F7 yellow confirmation validation only"
        },
        {
            "PROCESS": "04 Total Governance Matrix",
            "SUPPORTIVE MODULES": f"Supportive rows={sub['Supportive_NexusCore_Env']}",
            "VDF": f"VDF rows={sub['VDF_VeritasDataForge']}",
            "VAP": f"VAP rows={sub['VAP_VisualizationAnalytics']}",
            "OTHERS": f"Others rows={len(all_rows) - sub['Supportive_NexusCore_Env'] - sub['VDF_VeritasDataForge'] - sub['VAP_VisualizationAnalytics']}",
            "RYG": "GREEN",
            "COUNT": str(len(all_rows)),
            "NEXT": "v0115F7 validation only"
        }
    ]


def build_summary(red: List[Dict[str, Any]], yellow: List[Dict[str, Any]], green: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows = []
    buckets = [
        ("RED", "RED_EVIDENCE_PACK_CANDIDATE", red),
        ("YELLOW", "YELLOW_CONFIRMATION_CANDIDATE", yellow),
        ("GREEN", "GREEN_CLEARANCE_LEDGER_CANDIDATE", green),
    ]

    n = 0
    for ryg, group, items in buckets:
        counter = defaultdict(int)
        for r in items:
            counter[prop(r, "def_subsystem")] += 1
        for subsystem, count in sorted(counter.items(), key=lambda x: (-x[1], x[0])):
            n += 1
            rows.append({
                "def_summary_id": f"F6-SUM-{n:04d}",
                "def_ryg": ryg,
                "def_group": group,
                "def_subsystem": subsystem,
                "def_count": count,
                "def_apply_enabled": "false",
                "def_source_read": "false",
                "def_source_mutation": "false",
                "def_db_write": "false"
            })
    return rows


def build_validation(precheck_rows: List[Dict[str, Any]], red: List[Dict[str, Any]], yellow: List[Dict[str, Any]], green: List[Dict[str, Any]], gov: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows = []

    def add(name: str, ok: bool, msg: str) -> None:
        rows.append({
            "def_validation": name,
            "def_status": "PASS" if ok else "FAIL",
            "def_message": msg
        })

    c = Counter(prop(r, "def_ryg") for r in precheck_rows)
    total = len(precheck_rows)

    add("INPUT_NOT_EMPTY", total > 0, f"input={total}")
    add("CONTINUITY_448_ROWS", total == 448, f"input={total}")
    add("RED_COUNT_MATCH", len(red) == c["RED"], f"red_pack={len(red)} red_input={c['RED']}")
    add("YELLOW_COUNT_MATCH", len(yellow) == c["YELLOW"], f"yellow_pack={len(yellow)} yellow_input={c['YELLOW']}")
    add("GREEN_COUNT_MATCH", len(green) == c["GREEN"], f"green_pack={len(green)} green_input={c['GREEN']}")
    add("RYG_SUM_MATCH", len(red) + len(yellow) + len(green) == total, f"sum={len(red)+len(yellow)+len(green)} total={total}")
    add("NO_APPLY", all(prop(r, "def_apply_enabled") == "false" for r in red + yellow + green), "all apply=false")
    add("NO_SOURCE_READ", all(prop(r, "def_requires_source_read") == "false" for r in red + yellow + green), "all requires_source_read=false")
    add("NO_SOURCE_MUTATION", all(prop(r, "def_source_mutation") == "false" for r in red + yellow + green), "all source_mutation=false")
    add("NO_DB_WRITE", all(prop(r, "def_db_write") == "false" for r in red + yellow + green), "all db_write=false")
    add("GOVERNANCE_BRIDGE_PRESENT", len(gov) > 0, f"governance_params={len(gov)}")

    return rows


def build_readiness(red: List[Dict[str, Any]], yellow: List[Dict[str, Any]], green: List[Dict[str, Any]], validation: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    fail = sum(1 for r in validation if prop(r, "def_status") != "PASS")
    return [{
        "def_gate_status": "LEDGER_EVIDENCE_PACK_CANDIDATE_READY_REVIEW_ONLY" if fail == 0 else "BLOCKED_BY_F6_VALIDATION_FAIL",
        "def_allow_next": "true" if fail == 0 else "false",
        "def_reason": "F6 generated green ledger candidates, red evidence pack candidates, and yellow confirmation candidates. No source read, no mutation, no apply.",
        "def_input_rows": str(len(red) + len(yellow) + len(green)),
        "def_red_evidence_pack_rows": str(len(red)),
        "def_yellow_confirmation_rows": str(len(yellow)),
        "def_green_clearance_ledger_rows": str(len(green)),
        "def_validation_fail": str(fail),
        "def_source_read": "false",
        "def_execution_enabled": "false",
        "def_apply_enabled": "false",
        "def_source_mutation": "false",
        "def_canonical_merge": "false",
        "def_db_write": "false",
        "def_next_allowed_phase": "v0115F7 validation only"
    }]


def render_table(rows: List[Dict[str, Any]], cols: List[str], max_rows: int = 900) -> str:
    out = ["<table><thead><tr>"]
    for c in cols:
        out.append(f"<th>{h(c)}</th>")
    out.append("</tr></thead><tbody>")

    if not rows:
        out.append(f"<tr><td colspan='{len(cols)}'>No rows</td></tr>")
    else:
        for r in rows[:max_rows]:
            joined = " ".join(str(v) for v in r.values()).upper()
            cls = ""
            if "RED" in joined:
                cls = " class='risk-red'"
            elif "YELLOW" in joined:
                cls = " class='risk-yellow'"
            elif "GREEN" in joined:
                cls = " class='risk-green'"
            out.append(f"<tr{cls}>")
            for c in cols:
                v = prop(r, c)
                if len(v) > 520:
                    v = v[:520] + "..."
                out.append(f"<td>{h(v)}</td>")
            out.append("</tr>")

    out.append("</tbody></table>")
    return "".join(out)


def write_html(path: Path, payload: Dict[str, Any]) -> None:
    readiness = payload["readiness"][0]
    cards = ""
    for k, v in [
        ("Gate", readiness["def_gate_status"]),
        ("Input", readiness["def_input_rows"]),
        ("Red Evidence", readiness["def_red_evidence_pack_rows"]),
        ("Yellow", readiness["def_yellow_confirmation_rows"]),
        ("Green Ledger", readiness["def_green_clearance_ledger_rows"]),
        ("ValidationFail", readiness["def_validation_fail"]),
        ("SourceRead", readiness["def_source_read"]),
        ("Next", "v0115F7")
    ]:
        cards += f"<div class='card'><div class='k'>{h(k)}</div><div class='v'>{h(v)}</div></div>"

    style = """
:root{--bg:#f7f6f2;--paper:#fffefa;--line:#dedbd2;--ink:#24231f;--muted:#706d64;--seal:#8f2f24;--red:#c96b5a;--yellow:#c4943a;--green:#5a9e6f;--sky:#9fbcc2}
body{margin:0;background:radial-gradient(circle at 12% 10%,rgba(159,188,194,.24),transparent 28%),radial-gradient(circle at 88% 0%,rgba(180,200,190,.22),transparent 31%),linear-gradient(135deg,rgba(255,255,255,.70),rgba(247,246,242,1));color:var(--ink);font-family:'Microsoft JhengHei','Noto Sans TC',Arial,sans-serif;font-size:8.5px;line-height:1.35}
.wrap{max-width:1880px;margin:0 auto;padding:16px}.header{display:grid;grid-template-columns:1fr auto;gap:16px;align-items:start;margin-bottom:10px}
h1{font-size:15px;margin:0 0 4px;font-weight:650}.sub{font-size:8.2px;color:var(--muted)}
.seal{border:2px solid var(--seal);color:var(--seal);width:42px;height:42px;display:flex;align-items:center;justify-content:center;font-size:22px;font-weight:700;border-radius:6px;background:rgba(255,255,255,.48)}
.cards{display:grid;grid-template-columns:repeat(8,1fr);gap:7px;margin:10px 0}.card{background:var(--paper);border:1px solid var(--line);border-radius:10px;padding:7px;min-height:43px;box-shadow:0 8px 22px rgba(60,50,30,.045)}
.k{font-size:7.5px;color:var(--muted)}.v{font:650 9.8px Consolas,monospace;margin-top:4px;word-break:break-word}
.sec{background:rgba(255,254,250,.93);border:1px solid var(--line);border-radius:13px;padding:9px;margin-bottom:10px;overflow:hidden;box-shadow:0 10px 26px rgba(60,50,30,.045)}
h2{font-size:10px;margin:0 0 7px;font-weight:650}.note{white-space:pre-wrap;background:#fbfaf6;border:1px solid #e8e4da;border-radius:10px;padding:8px;color:#514d45;font-size:8.2px}
table{width:100%;border-collapse:collapse;table-layout:fixed;font-size:7.45px}th,td{border-bottom:1px solid #ebe8df;padding:3px 4px;vertical-align:top;word-break:break-word;overflow-wrap:anywhere}
th{background:#f0eee8;text-align:left;font-weight:650;color:#555149;position:sticky;top:0}tr:hover td{background:#f8f7f1}
.risk-red td{background:rgba(201,107,90,.09)}.risk-yellow td{background:rgba(196,148,58,.09)}.risk-green td{background:rgba(90,158,111,.075)}
.tag{display:inline-block;border:1px solid var(--line);border-radius:999px;padding:2px 7px;background:white;margin-right:4px;color:var(--muted)}
.search{width:100%;padding:7px 9px;border:1px solid var(--line);border-radius:9px;background:white;margin:6px 0 8px;font-size:9px}
.btn{border:1px solid var(--line);background:white;border-radius:999px;padding:4px 9px;cursor:pointer;font-size:8px;margin-right:4px}.btn:hover{border-color:var(--sky)}
.footer{margin:12px 0 4px;color:var(--muted);font-size:8px}.path{font-family:Consolas,monospace;color:#355b63}
"""
    js = """
function filterTables(q){
  q=(q||'').toLowerCase();
  document.querySelectorAll('tbody tr').forEach(function(tr){
    var t=tr.innerText.toLowerCase();
    tr.style.display=t.indexOf(q)>=0?'':'none';
  });
}
function quick(q){document.getElementById('q').value=q;filterTables(q);}
"""

    doc = f"""<!doctype html>
<html lang="zh-Hant">
<head><meta charset="utf-8"/><title>VIA v0115F6 Ledger Evidence Pack Candidate</title><style>{style}</style><script>{js}</script></head>
<body><div class="wrap">
  <div class="header">
    <div>
      <h1>def VIA v0115F6 · Ledger / Evidence Pack Candidate Only</h1>
      <div class="sub">GREEN Clearance Ledger · RED Evidence Pack · YELLOW Confirmation · Governance Parameter Bridge · No Source Read · No Apply</div>
    </div>
    <div class="seal">理</div>
  </div>

  <div class="cards">{cards}</div>

  <div class="sec">
    <h2>def Executive Judgment</h2>
    <span class="tag">CANDIDATE ONLY</span><span class="tag">NO SOURCE READ</span><span class="tag">NO MUTATION</span><span class="tag">NO APPLY</span><span class="tag">NO DB WRITE</span>
    <div class="note">F6 只建立候選治理資產：Green ledger candidates、Red evidence pack candidates、Yellow confirmation candidates。這一步不讀 source、不修 source、不合併 SSOT、不寫 DB。下一步 F7 只做 validation。</div>
    <input id="q" class="search" oninput="filterTables(this.value)" placeholder="搜尋 GREEN / RED / YELLOW / VDF / VAP / SECRET / DANGER / FIELDNAME / PATH_SIZE ..."/>
    <button class="btn" onclick="quick('GREEN')">GREEN</button>
    <button class="btn" onclick="quick('RED')">RED</button>
    <button class="btn" onclick="quick('YELLOW')">YELLOW</button>
    <button class="btn" onclick="quick('VDF')">VDF</button>
    <button class="btn" onclick="quick('VAP')">VAP</button>
    <button class="btn" onclick="quick('SECRET')">SECRET</button>
    <button class="btn" onclick="quick('PATH_SIZE')">PATH_SIZE</button>
    <button class="btn" onclick="quick('')">RESET</button>
  </div>

  <div class="sec"><h2>def Readiness Gate</h2>{render_table(payload["readiness"], ["def_gate_status","def_allow_next","def_reason","def_input_rows","def_red_evidence_pack_rows","def_yellow_confirmation_rows","def_green_clearance_ledger_rows","def_validation_fail","def_source_read","def_apply_enabled","def_source_mutation","def_db_write","def_next_allowed_phase"], 20)}</div>
  <div class="sec"><h2>def PROCESS / SUPPORTIVE MODULES / VDF / VAP / OTHERS</h2>{render_table(payload["process_matrix"], ["PROCESS","SUPPORTIVE MODULES","VDF","VAP","OTHERS","RYG","COUNT","NEXT"], 20)}</div>
  <div class="sec"><h2>def Summary Matrix</h2>{render_table(payload["summary"], ["def_summary_id","def_ryg","def_group","def_subsystem","def_count","def_apply_enabled","def_source_read","def_source_mutation","def_db_write"], 80)}</div>
  <div class="sec"><h2>def Validation Matrix</h2>{render_table(payload["validation"], ["def_validation","def_status","def_message"], 40)}</div>
  <div class="sec"><h2>def GREEN Clearance Ledger Candidates</h2>{render_table(payload["green"], ["def_ledger_candidate_id","def_precheck_id","def_clearance_type","def_subsystem","def_source_rel_path","def_basis","def_candidate_status","def_next_gate"], 500)}</div>
  <div class="sec"><h2>def RED Evidence Pack Candidates</h2>{render_table(payload["red"], ["def_red_evidence_pack_id","def_precheck_id","def_evidence_pack_type","def_subsystem","def_source_rel_path","def_hydra_risk","def_required_evidence","def_candidate_status","def_next_gate"], 200)}</div>
  <div class="sec"><h2>def YELLOW Confirmation Candidates</h2>{render_table(payload["yellow"], ["def_yellow_confirmation_id","def_precheck_id","def_confirmation_type","def_subsystem","def_source_rel_path","def_required_confirmation","def_candidate_status","def_next_gate"], 200)}</div>
  <div class="sec"><h2>def Governance Parameter Bridge</h2>{render_table(payload["gov_bridge"], ["def_param_id","def_section","def_parameter","def_value","def_meaning","def_mutable_in_f6","def_apply_enabled"], 120)}</div>

  <div class="footer">
    SourceRun: <span class="path">{h(payload["source_run"])}</span><br/>
    RunDir: <span class="path">{h(payload["run_dir"])}</span><br/>
    SAFE: No external call · No rescan · No source read · No source mutation · No canonical merge · No DB write · No apply
  </div>
</div></body></html>"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(doc, encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-run", required=True)
    ap.add_argument("--run-dir", required=True)
    args = ap.parse_args()

    source_run = Path(args.source_run)
    run_dir = Path(args.run_dir)
    output = run_dir / "output"
    report = run_dir / "report"
    pack = run_dir / "_ledger_evidence_pack_candidate"
    param = run_dir / "_governance_parameter_bridge"

    output.mkdir(parents=True, exist_ok=True)
    report.mkdir(parents=True, exist_ok=True)
    pack.mkdir(parents=True, exist_ok=True)
    param.mkdir(parents=True, exist_ok=True)

    precheck_path = source_run / "_package_specific_precheck" / "VIA_v0115F5_PackageSpecificPrecheckMatrix.csv"
    default_param_path = source_run / "_governance_default_parameters" / "VIA_v0115F5_GovernanceDefaultParameters.json"

    precheck_rows = read_csv(precheck_path)
    default_params = read_json(default_param_path)

    green = build_green_ledger(precheck_rows)
    red = build_red_evidence(precheck_rows)
    yellow = build_yellow_confirmation(precheck_rows)
    gov_bridge = build_governance_bridge(default_params)
    process_matrix = build_process_matrix(red, yellow, green)
    summary = build_summary(red, yellow, green)
    validation = build_validation(precheck_rows, red, yellow, green, gov_bridge)
    readiness = build_readiness(red, yellow, green, validation)

    write_csv(pack / "VIA_v0115F6_GREEN_ClearanceLedgerCandidates.csv", green)
    write_csv(pack / "VIA_v0115F6_RED_EvidencePackCandidates.csv", red)
    write_csv(pack / "VIA_v0115F6_YELLOW_ConfirmationCandidates.csv", yellow)
    write_csv(pack / "VIA_v0115F6_SummaryMatrix.csv", summary)
    write_csv(pack / "VIA_v0115F6_ProcessSupportiveVdfVapOthersMatrix.csv", process_matrix)
    write_csv(pack / "VIA_v0115F6_ValidationMatrix.csv", validation)
    write_csv(param / "VIA_v0115F6_GovernanceParameterBridge.csv", gov_bridge)
    write_csv(output / "VIA_v0115F6_ReadinessGate.csv", readiness)

    write_json(pack / "VIA_v0115F6_GREEN_ClearanceLedgerCandidates.json", green)
    write_json(pack / "VIA_v0115F6_RED_EvidencePackCandidates.json", red)
    write_json(pack / "VIA_v0115F6_YELLOW_ConfirmationCandidates.json", yellow)
    write_json(pack / "VIA_v0115F6_SummaryMatrix.json", summary)
    write_json(pack / "VIA_v0115F6_ProcessSupportiveVdfVapOthersMatrix.json", process_matrix)
    write_json(pack / "VIA_v0115F6_ValidationMatrix.json", validation)
    write_json(param / "VIA_v0115F6_GovernanceParameterBridge.json", gov_bridge)
    write_json(output / "VIA_v0115F6_ReadinessGate.json", readiness)

    html_path = report / "VIA_v0115F6_LedgerEvidencePackCandidate_OnePage.html"
    payload = {
        "source_run": str(source_run),
        "run_dir": str(run_dir),
        "green": green,
        "red": red,
        "yellow": yellow,
        "gov_bridge": gov_bridge,
        "process_matrix": process_matrix,
        "summary": summary,
        "validation": validation,
        "readiness": readiness
    }
    write_html(html_path, payload)

    manifest = {
        "schema_version": "VIA_v0115F6_LedgerEvidencePackCandidateOnly",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "gate": readiness[0]["def_gate_status"],
        "source_run": str(source_run),
        "run_dir": str(run_dir),
        "report": str(html_path),
        "outputs": {
            "green_clearance_ledger": str(pack / "VIA_v0115F6_GREEN_ClearanceLedgerCandidates.csv"),
            "red_evidence_pack": str(pack / "VIA_v0115F6_RED_EvidencePackCandidates.csv"),
            "yellow_confirmation": str(pack / "VIA_v0115F6_YELLOW_ConfirmationCandidates.csv"),
            "governance_bridge": str(param / "VIA_v0115F6_GovernanceParameterBridge.csv"),
            "readiness": str(output / "VIA_v0115F6_ReadinessGate.csv")
        },
        "policy": {
            "candidate_only": True,
            "no_source_read": True,
            "no_rescan": True,
            "external_call": False,
            "execution_enabled": False,
            "apply_enabled": False,
            "source_mutation": False,
            "canonical_merge": False,
            "db_write": False
        }
    }
    write_json(output / "VIA_v0115F6_LedgerEvidencePackCandidate_Manifest.json", manifest)

    print("")
    print("=" * 80)
    print("def VIA v0115F6 Ledger Evidence Pack Candidate COMPLETE")
    print("=" * 80)
    print(f"Gate       : {readiness[0]['def_gate_status']}")
    print(f"Input Rows : {readiness[0]['def_input_rows']}")
    print(f"Red        : {readiness[0]['def_red_evidence_pack_rows']}")
    print(f"Yellow     : {readiness[0]['def_yellow_confirmation_rows']}")
    print(f"Green      : {readiness[0]['def_green_clearance_ledger_rows']}")
    print(f"Fail       : {readiness[0]['def_validation_fail']}")
    print(f"Report     : {html_path}")
    print(f"Pack       : {pack}")
    print(f"Params     : {param}")
    print(f"Output     : {output}")
    print("[SAFE] No source read. No rescan. No apply. No source mutation. No DB write.")


if __name__ == "__main__":
    main()
