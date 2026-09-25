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


def add_validation(rows: List[Dict[str, Any]], layer: str, name: str, ok: bool, msg: str, risk: str = "LOW") -> None:
    rows.append({
        "def_layer": layer,
        "def_validation": name,
        "def_status": "PASS" if ok else "FAIL",
        "def_risk": risk if not ok else "LOW",
        "def_message": msg
    })


def validate_green(green: List[Dict[str, str]], out: List[Dict[str, Any]]) -> None:
    add_validation(out, "GREEN", "GREEN_COUNT_294", len(green) == 294, f"green={len(green)} expected=294")
    add_validation(out, "GREEN", "GREEN_STATUS_CANDIDATE_ONLY", all(prop(r, "def_candidate_status") == "CLEARANCE_LEDGER_CANDIDATE_ONLY" for r in green), "all green rows candidate only")
    add_validation(out, "GREEN", "GREEN_NEXT_GATE", all(prop(r, "def_next_gate") == "v0115F7_CLEARANCE_LEDGER_VALIDATION_ONLY" for r in green), "all green next_gate validation only")
    add_validation(out, "GREEN", "GREEN_NO_AUTO_CLEAR", all(prop(r, "def_auto_clear_allowed") == "false" for r in green), "all auto_clear_allowed=false")
    add_validation(out, "GREEN", "GREEN_NO_SOURCE_READ", all(prop(r, "def_requires_source_read") == "false" for r in green), "all requires_source_read=false")
    add_validation(out, "GREEN", "GREEN_NO_APPLY", all(prop(r, "def_apply_enabled") == "false" for r in green), "all apply=false")
    add_validation(out, "GREEN", "GREEN_NO_MUTATION", all(prop(r, "def_source_mutation") == "false" for r in green), "all source_mutation=false")
    add_validation(out, "GREEN", "GREEN_NO_DB_WRITE", all(prop(r, "def_db_write") == "false" for r in green), "all db_write=false")


def validate_red(red: List[Dict[str, str]], out: List[Dict[str, Any]]) -> None:
    add_validation(out, "RED", "RED_COUNT_63", len(red) == 63, f"red={len(red)} expected=63")
    add_validation(out, "RED", "RED_STATUS_CANDIDATE_ONLY", all(prop(r, "def_candidate_status") == "EVIDENCE_PACK_CANDIDATE_ONLY" for r in red), "all red rows evidence pack candidate only")
    add_validation(out, "RED", "RED_NEXT_GATE", all(prop(r, "def_next_gate") == "v0115F7_RED_EVIDENCE_PACK_VALIDATION_ONLY" for r in red), "all red next_gate validation only")
    add_validation(out, "RED", "RED_MANUAL_REVIEW_REQUIRED", all(prop(r, "def_requires_manual_review") == "true" for r in red), "all red rows require manual review")
    add_validation(out, "RED", "RED_REPAIR_BLOCKED", all(prop(r, "def_repair_allowed") == "false" for r in red), "all repair_allowed=false")
    add_validation(out, "RED", "RED_NO_SOURCE_READ", all(prop(r, "def_requires_source_read") == "false" for r in red), "all requires_source_read=false")
    add_validation(out, "RED", "RED_NO_APPLY", all(prop(r, "def_apply_enabled") == "false" for r in red), "all apply=false")
    add_validation(out, "RED", "RED_NO_MUTATION", all(prop(r, "def_source_mutation") == "false" for r in red), "all source_mutation=false")
    add_validation(out, "RED", "RED_NO_DB_WRITE", all(prop(r, "def_db_write") == "false" for r in red), "all db_write=false")


def validate_yellow(yellow: List[Dict[str, str]], out: List[Dict[str, Any]]) -> None:
    add_validation(out, "YELLOW", "YELLOW_COUNT_91", len(yellow) == 91, f"yellow={len(yellow)} expected=91")
    add_validation(out, "YELLOW", "YELLOW_STATUS_CANDIDATE_ONLY", all(prop(r, "def_candidate_status") == "CONFIRMATION_CANDIDATE_ONLY" for r in yellow), "all yellow rows confirmation candidate only")
    add_validation(out, "YELLOW", "YELLOW_REPAIR_BLOCKED", all(prop(r, "def_repair_allowed") == "false" for r in yellow), "all repair_allowed=false")
    add_validation(out, "YELLOW", "YELLOW_NO_SOURCE_READ", all(prop(r, "def_requires_source_read") == "false" for r in yellow), "all requires_source_read=false")
    add_validation(out, "YELLOW", "YELLOW_NO_APPLY", all(prop(r, "def_apply_enabled") == "false" for r in yellow), "all apply=false")
    add_validation(out, "YELLOW", "YELLOW_NO_MUTATION", all(prop(r, "def_source_mutation") == "false" for r in yellow), "all source_mutation=false")
    add_validation(out, "YELLOW", "YELLOW_NO_DB_WRITE", all(prop(r, "def_db_write") == "false" for r in yellow), "all db_write=false")


def validate_governance(gov: List[Dict[str, str]], out: List[Dict[str, Any]]) -> None:
    add_validation(out, "GOVERNANCE", "GOVERNANCE_BRIDGE_PRESENT", len(gov) >= 30, f"governance_params={len(gov)} expected>=30")
    add_validation(out, "GOVERNANCE", "GOVERNANCE_NO_MUTABLE_IN_F7", all(prop(r, "def_mutable_in_f6") == "false" for r in gov), "all mutable_in_f6=false")
    add_validation(out, "GOVERNANCE", "GOVERNANCE_NO_APPLY", all(prop(r, "def_apply_enabled") == "false" for r in gov), "all apply=false")
    add_validation(out, "GOVERNANCE", "GOVERNANCE_NO_MUTATION", all(prop(r, "def_source_mutation") == "false" for r in gov), "all source_mutation=false")


def build_summary(green: List[Dict[str, str]], red: List[Dict[str, str]], yellow: List[Dict[str, str]], gov: List[Dict[str, str]], validation: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    fail = sum(1 for r in validation if prop(r, "def_status") != "PASS")
    rows = []

    def add(group: str, count: int, status: str, next_gate: str) -> None:
        rows.append({
            "def_group": group,
            "def_count": count,
            "def_status": status,
            "def_next_gate": next_gate,
            "def_source_read": "false",
            "def_apply_enabled": "false",
            "def_source_mutation": "false",
            "def_db_write": "false"
        })

    add("GREEN_CLEARANCE_LEDGER_CANDIDATES", len(green), "VALIDATED" if fail == 0 else "REVIEW", "v0115F8_GOVERNANCE_UI_CONTRACT_SEAL_ONLY")
    add("RED_EVIDENCE_PACK_CANDIDATES", len(red), "VALIDATED" if fail == 0 else "REVIEW", "v0115F8_GOVERNANCE_UI_CONTRACT_SEAL_ONLY")
    add("YELLOW_CONFIRMATION_CANDIDATES", len(yellow), "VALIDATED" if fail == 0 else "REVIEW", "v0115F8_GOVERNANCE_UI_CONTRACT_SEAL_ONLY")
    add("GOVERNANCE_PARAMETER_BRIDGE", len(gov), "VALIDATED" if fail == 0 else "REVIEW", "v0115F8_GOVERNANCE_UI_CONTRACT_SEAL_ONLY")

    return rows


def build_subsystem_matrix(green: List[Dict[str, str]], red: List[Dict[str, str]], yellow: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    subs = sorted(set([prop(r, "def_subsystem") for r in green + red + yellow]))
    rows = []
    for s in subs:
        rows.append({
            "def_subsystem": s,
            "def_green_ledger": sum(1 for r in green if prop(r, "def_subsystem") == s),
            "def_red_evidence": sum(1 for r in red if prop(r, "def_subsystem") == s),
            "def_yellow_confirmation": sum(1 for r in yellow if prop(r, "def_subsystem") == s),
            "def_total": sum(1 for r in green + red + yellow if prop(r, "def_subsystem") == s),
            "def_hydra_control": "RED locked; YELLOW confirmation; GREEN candidate only",
            "def_apply_enabled": "false"
        })
    return rows


def build_readiness(green: List[Dict[str, str]], red: List[Dict[str, str]], yellow: List[Dict[str, str]], gov: List[Dict[str, str]], validation: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    fail = sum(1 for r in validation if prop(r, "def_status") != "PASS")
    return [{
        "def_gate_status": "LEDGER_EVIDENCE_VALIDATION_READY_REVIEW_ONLY" if fail == 0 else "BLOCKED_BY_F7_VALIDATION_FAIL",
        "def_allow_next": "true" if fail == 0 else "false",
        "def_reason": "F7 validated F6 candidate packages. No source read, no mutation, no apply.",
        "def_input_rows": str(len(green) + len(red) + len(yellow)),
        "def_green_ledger_rows": str(len(green)),
        "def_red_evidence_rows": str(len(red)),
        "def_yellow_confirmation_rows": str(len(yellow)),
        "def_governance_params": str(len(gov)),
        "def_validation_rows": str(len(validation)),
        "def_validation_fail": str(fail),
        "def_source_read": "false",
        "def_rescan": "false",
        "def_execution_enabled": "false",
        "def_apply_enabled": "false",
        "def_source_mutation": "false",
        "def_canonical_merge": "false",
        "def_db_write": "false",
        "def_next_allowed_phase": "v0115F8 governance UI contract seal only"
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
            if "FAIL" in joined or "RED" in joined:
                cls = " class='risk-red'"
            elif "YELLOW" in joined or "REVIEW" in joined:
                cls = " class='risk-yellow'"
            elif "PASS" in joined or "GREEN" in joined or "VALIDATED" in joined:
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
        ("Green", readiness["def_green_ledger_rows"]),
        ("Red", readiness["def_red_evidence_rows"]),
        ("Yellow", readiness["def_yellow_confirmation_rows"]),
        ("Gov", readiness["def_governance_params"]),
        ("Fail", readiness["def_validation_fail"]),
        ("Next", "v0115F8")
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
<head><meta charset="utf-8"/><title>VIA v0115F7 Validation Only</title><style>{style}</style><script>{js}</script></head>
<body><div class="wrap">
  <div class="header">
    <div>
      <h1>def VIA v0115F7 · Ledger / Evidence Pack Validation Only</h1>
      <div class="sub">GREEN Ledger · RED Evidence · YELLOW Confirmation · Governance Bridge · Validation Only · No Apply</div>
    </div>
    <div class="seal">理</div>
  </div>

  <div class="cards">{cards}</div>

  <div class="sec">
    <h2>def Executive Judgment</h2>
    <span class="tag">VALIDATION ONLY</span><span class="tag">NO SOURCE READ</span><span class="tag">NO MUTATION</span><span class="tag">NO APPLY</span><span class="tag">NO DB WRITE</span>
    <div class="note">F7 只驗證 F6 候選治理資產。通過後，下一步 F8 仍只做 Governance UI Contract Seal，不進 source 修復。</div>
    <input id="q" class="search" oninput="filterTables(this.value)" placeholder="搜尋 PASS / FAIL / GREEN / RED / YELLOW / VDF / VAP / GOVERNANCE ..."/>
    <button class="btn" onclick="quick('PASS')">PASS</button>
    <button class="btn" onclick="quick('FAIL')">FAIL</button>
    <button class="btn" onclick="quick('GREEN')">GREEN</button>
    <button class="btn" onclick="quick('RED')">RED</button>
    <button class="btn" onclick="quick('YELLOW')">YELLOW</button>
    <button class="btn" onclick="quick('VDF')">VDF</button>
    <button class="btn" onclick="quick('VAP')">VAP</button>
    <button class="btn" onclick="quick('')">RESET</button>
  </div>

  <div class="sec"><h2>def Readiness Gate</h2>{render_table(payload["readiness"], ["def_gate_status","def_allow_next","def_reason","def_input_rows","def_green_ledger_rows","def_red_evidence_rows","def_yellow_confirmation_rows","def_governance_params","def_validation_rows","def_validation_fail","def_source_read","def_rescan","def_apply_enabled","def_source_mutation","def_db_write","def_next_allowed_phase"], 20)}</div>
  <div class="sec"><h2>def Validation Matrix</h2>{render_table(payload["validation"], ["def_layer","def_validation","def_status","def_risk","def_message"], 80)}</div>
  <div class="sec"><h2>def Summary Matrix</h2>{render_table(payload["summary"], ["def_group","def_count","def_status","def_next_gate","def_source_read","def_apply_enabled","def_source_mutation","def_db_write"], 40)}</div>
  <div class="sec"><h2>def Subsystem Matrix</h2>{render_table(payload["subsystem"], ["def_subsystem","def_green_ledger","def_red_evidence","def_yellow_confirmation","def_total","def_hydra_control","def_apply_enabled"], 80)}</div>

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
    validation_dir = run_dir / "_ledger_evidence_validation_only"

    output.mkdir(parents=True, exist_ok=True)
    report.mkdir(parents=True, exist_ok=True)
    validation_dir.mkdir(parents=True, exist_ok=True)

    f6_pack = source_run / "_ledger_evidence_pack_candidate"
    f6_gov = source_run / "_governance_parameter_bridge"

    green = read_csv(f6_pack / "VIA_v0115F6_GREEN_ClearanceLedgerCandidates.csv")
    red = read_csv(f6_pack / "VIA_v0115F6_RED_EvidencePackCandidates.csv")
    yellow = read_csv(f6_pack / "VIA_v0115F6_YELLOW_ConfirmationCandidates.csv")
    gov = read_csv(f6_gov / "VIA_v0115F6_GovernanceParameterBridge.csv")

    validation: List[Dict[str, Any]] = []
    validate_green(green, validation)
    validate_red(red, validation)
    validate_yellow(yellow, validation)
    validate_governance(gov, validation)

    summary = build_summary(green, red, yellow, gov, validation)
    subsystem = build_subsystem_matrix(green, red, yellow)
    readiness = build_readiness(green, red, yellow, gov, validation)

    write_csv(validation_dir / "VIA_v0115F7_FinalValidationMatrix.csv", validation)
    write_csv(validation_dir / "VIA_v0115F7_SummaryMatrix.csv", summary)
    write_csv(validation_dir / "VIA_v0115F7_SubsystemMatrix.csv", subsystem)
    write_csv(output / "VIA_v0115F7_ReadinessGate.csv", readiness)

    write_json(validation_dir / "VIA_v0115F7_FinalValidationMatrix.json", validation)
    write_json(validation_dir / "VIA_v0115F7_SummaryMatrix.json", summary)
    write_json(validation_dir / "VIA_v0115F7_SubsystemMatrix.json", subsystem)
    write_json(output / "VIA_v0115F7_ReadinessGate.json", readiness)

    html_path = report / "VIA_v0115F7_LedgerEvidenceValidation_OnePage.html"
    payload = {
        "source_run": str(source_run),
        "run_dir": str(run_dir),
        "validation": validation,
        "summary": summary,
        "subsystem": subsystem,
        "readiness": readiness
    }
    write_html(html_path, payload)

    manifest = {
        "schema_version": "VIA_v0115F7_LedgerEvidenceValidationOnly",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "gate": readiness[0]["def_gate_status"],
        "source_run": str(source_run),
        "run_dir": str(run_dir),
        "report": str(html_path),
        "outputs": {
            "final_validation": str(validation_dir / "VIA_v0115F7_FinalValidationMatrix.csv"),
            "summary": str(validation_dir / "VIA_v0115F7_SummaryMatrix.csv"),
            "subsystem": str(validation_dir / "VIA_v0115F7_SubsystemMatrix.csv"),
            "readiness": str(output / "VIA_v0115F7_ReadinessGate.csv")
        },
        "policy": {
            "validation_only": True,
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
    write_json(output / "VIA_v0115F7_LedgerEvidenceValidation_Manifest.json", manifest)

    print("")
    print("=" * 80)
    print("def VIA v0115F7 Ledger Evidence Validation COMPLETE")
    print("=" * 80)
    print(f"Gate       : {readiness[0]['def_gate_status']}")
    print(f"Input Rows : {readiness[0]['def_input_rows']}")
    print(f"Green      : {readiness[0]['def_green_ledger_rows']}")
    print(f"Red        : {readiness[0]['def_red_evidence_rows']}")
    print(f"Yellow     : {readiness[0]['def_yellow_confirmation_rows']}")
    print(f"Gov Params : {readiness[0]['def_governance_params']}")
    print(f"Fail       : {readiness[0]['def_validation_fail']}")
    print(f"Report     : {html_path}")
    print(f"Validation : {validation_dir}")
    print(f"Output     : {output}")
    print("[SAFE] Validation only. No source read. No rescan. No apply. No source mutation. No DB write.")


if __name__ == "__main__":
    main()
