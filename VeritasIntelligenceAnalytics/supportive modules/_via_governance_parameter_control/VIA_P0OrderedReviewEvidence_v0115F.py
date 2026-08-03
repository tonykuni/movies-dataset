from __future__ import annotations

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
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        rows = [{"def_empty": "true"}]
    cols = []
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


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def prop(row: Dict[str, Any], key: str, default: str = "") -> str:
    v = row.get(key, default)
    return "" if v is None else str(v)


def h(value: Any) -> str:
    return html.escape("" if value is None else str(value))


def table(rows: List[Dict[str, Any]], cols: List[str], max_rows: int = 400) -> str:
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
            if "HYDRA_HIGH" in joined or "P0" in joined or "HIGH" in joined:
                cls = " class='risk-high'"
            elif "MEDIUM" in joined:
                cls = " class='risk-med'"
            out.append(f"<tr{cls}>")
            for c in cols:
                v = prop(r, c)
                if len(v) > 480:
                    v = v[:480] + "..."
                out.append(f"<td>{h(v)}</td>")
            out.append("</tr>")

    out.append("</tbody></table>")
    return "".join(out)


def resolve_runs(v0115e_run: Path) -> Dict[str, Path]:
    manifest_e = v0115e_run / "output" / "VIA_v0115E_ProblemLedgerGovernanceUI_Manifest.json"
    if not manifest_e.exists():
        raise FileNotFoundError(f"Missing v0115E manifest: {manifest_e}")

    obj = read_json(manifest_e)
    v0115d = Path(obj.get("v0115d_run", ""))
    v0115c = Path(obj.get("v0115c_run", ""))

    if not v0115d.exists():
        raise FileNotFoundError(f"v0115D run not found: {v0115d}")
    if not v0115c.exists():
        raise FileNotFoundError(f"v0115C run not found: {v0115c}")

    return {"v0115d": v0115d, "v0115c": v0115c}


def build_inventory_index(inventory_rows: List[Dict[str, str]]) -> Dict[str, Dict[str, str]]:
    idx = {}
    for r in inventory_rows:
        rel = prop(r, "def_rel_path")
        if rel and rel not in idx:
            idx[rel] = r
    return idx


def classify_hydra(row: Dict[str, Any]) -> str:
    subsystem = prop(row, "def_subsystem")
    reason = (prop(row, "def_review_reason") + " " + prop(row, "def_recommended_action") + " " + prop(row, "def_source_rel_path")).lower()

    if any(x in reason for x in ["secret", "dangerous", "remove-item", "stop-process", "invoke-expression", "db write", "source mutation"]):
        return "HYDRA_HIGH"
    if subsystem in {"VDF_VeritasDataForge", "Registry_SSOT", "Supportive_NexusCore_Env", "VAP_VisualizationAnalytics"}:
        return "HYDRA_HIGH"
    if subsystem in {"VRN_VeritasReportNova", "VETF_ActiveETF", "VIS_InvestmentSystem"}:
        return "HYDRA_MEDIUM"
    return "HYDRA_MEDIUM"


def build_p0_evidence(fix_rows: List[Dict[str, str]], inventory_rows: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    inv = build_inventory_index(inventory_rows)
    out = []
    n = 0

    for r in fix_rows:
        if prop(r, "def_priority") != "P0":
            continue

        rel = prop(r, "def_source_rel_path")
        iv = inv.get(rel, {})
        n += 1

        merged = {
            "def_p0_evidence_id": f"P0-EVD-{n:06d}",
            "def_priority": prop(r, "def_priority"),
            "def_fix_class": prop(r, "def_fix_class"),
            "def_risk": prop(r, "def_risk"),
            "def_subsystem": prop(r, "def_subsystem"),
            "def_source_rel_path": rel,
            "def_source_file_type": prop(iv, "def_file_type"),
            "def_source_ext": prop(iv, "def_ext"),
            "def_size_bytes": prop(iv, "def_size_bytes"),
            "def_sha256": prop(iv, "def_sha256"),
            "def_secret_marker": prop(iv, "def_secret_marker"),
            "def_danger_marker": prop(iv, "def_danger_marker"),
            "def_error_marker": prop(iv, "def_error_marker"),
            "def_python_ast": prop(iv, "def_python_ast"),
            "def_review_reason": prop(iv, "def_review_reason"),
            "def_recommended_action": prop(r, "def_recommended_action"),
            "def_hydra_risk": "",
            "def_ordered_review_required": "true",
            "def_parallel_safe_candidate": "false",
            "def_apply_enabled": "false",
            "def_source_mutation": "false",
            "def_db_write": "false"
        }
        merged["def_hydra_risk"] = classify_hydra(merged)
        out.append(merged)

    return out


def build_p0_package_summary(evidence_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    groups = defaultdict(lambda: {
        "count": 0,
        "secret": 0,
        "danger": 0,
        "error": 0,
        "hydra_high": 0,
        "examples": []
    })

    for r in evidence_rows:
        key = (prop(r, "def_subsystem"), prop(r, "def_risk"), prop(r, "def_hydra_risk"))
        g = groups[key]
        g["count"] += 1
        if prop(r, "def_secret_marker") == "true":
            g["secret"] += 1
        if prop(r, "def_danger_marker") == "true":
            g["danger"] += 1
        if prop(r, "def_error_marker") == "true":
            g["error"] += 1
        if prop(r, "def_hydra_risk") == "HYDRA_HIGH":
            g["hydra_high"] += 1
        if len(g["examples"]) < 5:
            g["examples"].append(prop(r, "def_source_rel_path"))

    rows = []
    n = 0
    for (subsystem, risk, hydra), g in groups.items():
        n += 1
        rows.append({
            "def_p0_package_id": f"P0-PKG-{n:04d}",
            "def_subsystem": subsystem,
            "def_risk": risk,
            "def_hydra_risk": hydra,
            "def_count": g["count"],
            "def_secret_marker_count": g["secret"],
            "def_danger_marker_count": g["danger"],
            "def_error_marker_count": g["error"],
            "def_hydra_high_count": g["hydra_high"],
            "def_review_mode": "ORDERED_REVIEW_ONLY",
            "def_next_gate": "v0115F1_P0_FALSE_POSITIVE_TRIAGE_ONLY",
            "def_examples": " | ".join(g["examples"]),
            "def_apply_enabled": "false",
            "def_source_mutation": "false",
            "def_db_write": "false"
        })

    return sorted(rows, key=lambda x: (-int(x["def_count"]), x["def_subsystem"]))


def build_ordered_queue(evidence_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    subsystem_rank = {
        "Registry_SSOT": 1,
        "Supportive_NexusCore_Env": 2,
        "VDF_VeritasDataForge": 3,
        "VAP_VisualizationAnalytics": 4,
        "VRN_VeritasReportNova": 5,
        "VETF_ActiveETF": 6,
        "VIS_InvestmentSystem": 7,
        "HTML_UI_Assets": 8,
        "Reports_Matrices": 9,
        "Prompt_Assets": 10,
        "Unclassified": 11,
    }

    def score(r: Dict[str, Any]) -> int:
        s = 0
        if prop(r, "def_hydra_risk") == "HYDRA_HIGH":
            s += 100000
        if prop(r, "def_secret_marker") == "true":
            s += 50000
        if prop(r, "def_danger_marker") == "true":
            s += 30000
        if prop(r, "def_error_marker") == "true":
            s += 10000
        s += 1000 - subsystem_rank.get(prop(r, "def_subsystem"), 99)
        return s

    rows = sorted(evidence_rows, key=lambda r: (-score(r), prop(r, "def_subsystem"), prop(r, "def_source_rel_path")))

    out = []
    for i, r in enumerate(rows, 1):
        if prop(r, "def_secret_marker") == "true":
            review_action = "SECRET_POLICY_REVIEW_RUNTIME_PARAMETER_ONLY"
        elif prop(r, "def_danger_marker") == "true":
            review_action = "DANGEROUS_COMMAND_BOUNDARY_REVIEW"
        elif prop(r, "def_error_marker") == "true":
            review_action = "ERROR_CONTEXT_REVIEW_FALSE_POSITIVE_OR_PATCH_CANDIDATE"
        else:
            review_action = "ORDERED_MANUAL_REVIEW"

        out.append({
            "def_order": f"{i:06d}",
            "def_p0_evidence_id": prop(r, "def_p0_evidence_id"),
            "def_subsystem": prop(r, "def_subsystem"),
            "def_hydra_risk": prop(r, "def_hydra_risk"),
            "def_source_rel_path": prop(r, "def_source_rel_path"),
            "def_secret_marker": prop(r, "def_secret_marker"),
            "def_danger_marker": prop(r, "def_danger_marker"),
            "def_error_marker": prop(r, "def_error_marker"),
            "def_review_action": review_action,
            "def_auto_fix_allowed": "false",
            "def_apply_enabled": "false",
            "def_source_mutation": "false",
            "def_db_write": "false"
        })

    return out


def build_hydra_matrix(evidence_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    groups = defaultdict(lambda: Counter())

    for r in evidence_rows:
        subsystem = prop(r, "def_subsystem")
        groups[subsystem]["total"] += 1
        groups[subsystem][prop(r, "def_hydra_risk")] += 1
        if prop(r, "def_secret_marker") == "true":
            groups[subsystem]["secret"] += 1
        if prop(r, "def_danger_marker") == "true":
            groups[subsystem]["danger"] += 1
        if prop(r, "def_error_marker") == "true":
            groups[subsystem]["error"] += 1

    rows = []
    for subsystem, c in groups.items():
        total = c["total"]
        high = c["HYDRA_HIGH"]
        ratio = high / total if total else 0
        if ratio >= 0.6 or high >= 100:
            control = "LOCKED_ORDERED_REVIEW"
        elif high > 0:
            control = "ORDERED_REVIEW_FIRST"
        else:
            control = "MANUAL_REVIEW"

        rows.append({
            "def_subsystem": subsystem,
            "def_total_p0": total,
            "def_hydra_high": high,
            "def_hydra_medium": c["HYDRA_MEDIUM"],
            "def_secret_marker": c["secret"],
            "def_danger_marker": c["danger"],
            "def_error_marker": c["error"],
            "def_hydra_high_ratio": f"{ratio:.2%}",
            "def_control": control,
            "def_apply_enabled": "false"
        })

    return sorted(rows, key=lambda x: (-int(x["def_hydra_high"]), -int(x["def_total_p0"]), x["def_subsystem"]))


def build_false_positive_rules() -> List[Dict[str, Any]]:
    return [
        {
            "def_rule_id": "P0-FP-001",
            "def_marker": "secret-like marker",
            "def_triage": "若只是字串中的 'api_key' 欄位名稱或測試樣板，不等於真實 secret；仍需確認沒有實值。",
            "def_action": "MASK_OR_RUNTIME_PARAMETER_POLICY_IF_TRUE_SECRET",
            "def_auto_fix_allowed": "false"
        },
        {
            "def_rule_id": "P0-FP-002",
            "def_marker": "dangerous command marker",
            "def_triage": "若 Remove-Item/Stop-Process 只在註解、文件、掃描規則或禁用邊界文字中出現，列為 false-positive candidate。",
            "def_action": "BOUNDARY_REVIEW_NO_AUTO_EXECUTION",
            "def_auto_fix_allowed": "false"
        },
        {
            "def_rule_id": "P0-FP-003",
            "def_marker": "error/fatal marker",
            "def_triage": "若 FATAL/FAIL/Traceback 是歷史 log 或報告內容，不等於目前程式錯誤。",
            "def_action": "EVIDENCE_CONTEXT_REVIEW",
            "def_auto_fix_allowed": "false"
        },
        {
            "def_rule_id": "P0-FP-004",
            "def_marker": "high-coupled subsystem",
            "def_triage": "Registry_SSOT、Supportive、VDF、VAP 屬高耦合節點，即使 marker 可能是假陽性，也不得與其他修正併行。",
            "def_action": "ORDERED_REVIEW_ONLY",
            "def_auto_fix_allowed": "false"
        }
    ]


def build_readiness(evidence_rows: List[Dict[str, Any]], queue: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [{
        "def_gate_status": "P0_ORDERED_REVIEW_EVIDENCE_PACKAGE_READY_REVIEW_ONLY",
        "def_allow_next": "true",
        "def_reason": "P0 evidence package generated. No rescan, no apply, no source mutation.",
        "def_p0_evidence_rows": str(len(evidence_rows)),
        "def_ordered_queue_rows": str(len(queue)),
        "def_execution_enabled": "false",
        "def_apply_enabled": "false",
        "def_source_mutation": "false",
        "def_canonical_merge": "false",
        "def_db_write": "false",
        "def_next_allowed_phase": "v0115F1 P0 false-positive triage only"
    }]


def write_html(path: Path, payload: Dict[str, Any]) -> None:
    summary = payload["summary"]
    readiness = payload["readiness"][0]

    cards = ""
    for k, v in [
        ("Gate", readiness["def_gate_status"]),
        ("Files", summary.get("Files", "")),
        ("P0 Evidence", readiness["def_p0_evidence_rows"]),
        ("Queue", readiness["def_ordered_queue_rows"]),
        ("HighRisk", summary.get("HighRisk", "")),
        ("MediumRisk", summary.get("MediumRisk", "")),
        ("Apply", "false"),
        ("Next", "v0115F1")
    ]:
        cards += f"<div class='card'><div class='k'>{h(k)}</div><div class='v'>{h(v)}</div></div>"

    style = """
:root{--bg:#f7f6f2;--paper:#fffefa;--line:#dedbd2;--ink:#24231f;--muted:#706d64;--seal:#8f2f24;--red:#c96b5a;--yellow:#c4943a;--green:#5a9e6f;--sky:#9fbcc2}
body{margin:0;background:radial-gradient(circle at 12% 10%,rgba(159,188,194,.24),transparent 28%),radial-gradient(circle at 88% 0%,rgba(180,200,190,.22),transparent 31%),linear-gradient(135deg,rgba(255,255,255,.70),rgba(247,246,242,1));color:var(--ink);font-family:'Microsoft JhengHei','Noto Sans TC',Arial,sans-serif;font-size:8.6px;line-height:1.35}
.wrap{max-width:1880px;margin:0 auto;padding:16px}.header{display:grid;grid-template-columns:1fr auto;gap:16px;align-items:start;margin-bottom:10px}
h1{font-size:15px;margin:0 0 4px;font-weight:650}.sub{font-size:8.2px;color:var(--muted)}
.seal{border:2px solid var(--seal);color:var(--seal);width:42px;height:42px;display:flex;align-items:center;justify-content:center;font-size:22px;font-weight:700;border-radius:6px;background:rgba(255,255,255,.48)}
.cards{display:grid;grid-template-columns:repeat(8,1fr);gap:7px;margin:10px 0}.card{background:var(--paper);border:1px solid var(--line);border-radius:10px;padding:7px;min-height:43px;box-shadow:0 8px 22px rgba(60,50,30,.045)}
.k{font-size:7.5px;color:var(--muted)}.v{font:650 9.8px Consolas,monospace;margin-top:4px;word-break:break-word}
.sec{background:rgba(255,254,250,.93);border:1px solid var(--line);border-radius:13px;padding:9px;margin-bottom:10px;overflow:hidden;box-shadow:0 10px 26px rgba(60,50,30,.045)}
h2{font-size:10px;margin:0 0 7px;font-weight:650}.note{white-space:pre-wrap;background:#fbfaf6;border:1px solid #e8e4da;border-radius:10px;padding:8px;color:#514d45;font-size:8.2px}
table{width:100%;border-collapse:collapse;table-layout:fixed;font-size:7.45px}th,td{border-bottom:1px solid #ebe8df;padding:3px 4px;vertical-align:top;word-break:break-word;overflow-wrap:anywhere}
th{background:#f0eee8;text-align:left;font-weight:650;color:#555149;position:sticky;top:0}tr:hover td{background:#f8f7f1}
.risk-high td{background:rgba(201,107,90,.075)}.risk-med td{background:rgba(196,148,58,.075)}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:10px}.tag{display:inline-block;border:1px solid var(--line);border-radius:999px;padding:2px 7px;background:white;margin-right:4px;color:var(--muted)}
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
<head><meta charset="utf-8"/><title>VIA v0115F P0 Ordered Review Evidence</title><style>{style}</style><script>{js}</script></head>
<body><div class="wrap">
  <div class="header">
    <div>
      <h1>def VIA v0115F · P0 Ordered Review Evidence Package</h1>
      <div class="sub">P0 Evidence · Hydra Matrix · Manual Queue · False-Positive Rules · No Apply</div>
    </div>
    <div class="seal">理</div>
  </div>
  <div class="cards">{cards}</div>

  <div class="sec">
    <h2>def Executive Judgment</h2>
    <span class="tag">P0 ONLY</span><span class="tag">ORDERED REVIEW</span><span class="tag">HYDRA CONTROL</span><span class="tag">NO RESCAN</span><span class="tag">NO AUTO FIX</span><span class="tag">NO APPLY</span>
    <div class="note">v0115F 只把 P0 問題轉成 evidence package 與 ordered review queue。這一步不是修補，不移動、不改寫、不 canonical merge、不 DB write。下一步 v0115F1 才做 false-positive triage，仍然 review-only。</div>
    <input id="q" class="search" oninput="filterTables(this.value)" placeholder="搜尋 VDF / VAP / secret / dangerous / HYDRA_HIGH / Registry_SSOT / Remove-Item ..."/>
    <button class="btn" onclick="quick('HYDRA_HIGH')">HYDRA_HIGH</button>
    <button class="btn" onclick="quick('secret')">secret</button>
    <button class="btn" onclick="quick('danger')">danger</button>
    <button class="btn" onclick="quick('VDF')">VDF</button>
    <button class="btn" onclick="quick('VAP')">VAP</button>
    <button class="btn" onclick="quick('Registry_SSOT')">Registry</button>
    <button class="btn" onclick="quick('')">RESET</button>
  </div>

  <div class="sec"><h2>def Readiness Gate</h2>{table(payload["readiness"], ["def_gate_status","def_allow_next","def_reason","def_p0_evidence_rows","def_ordered_queue_rows","def_execution_enabled","def_apply_enabled","def_source_mutation","def_db_write","def_next_allowed_phase"], 20)}</div>
  <div class="sec"><h2>def P0 Package Summary</h2>{table(payload["package_summary"], ["def_p0_package_id","def_subsystem","def_risk","def_hydra_risk","def_count","def_secret_marker_count","def_danger_marker_count","def_error_marker_count","def_review_mode","def_next_gate","def_apply_enabled"], 100)}</div>

  <div class="grid2">
    <div class="sec"><h2>def Hydra Risk Matrix</h2>{table(payload["hydra_matrix"], ["def_subsystem","def_total_p0","def_hydra_high","def_hydra_medium","def_secret_marker","def_danger_marker","def_error_marker","def_hydra_high_ratio","def_control","def_apply_enabled"], 100)}</div>
    <div class="sec"><h2>def False-Positive Triage Rules</h2>{table(payload["false_positive_rules"], ["def_rule_id","def_marker","def_triage","def_action","def_auto_fix_allowed"], 20)}</div>
  </div>

  <div class="sec"><h2>def Ordered Review Queue Preview</h2>{table(payload["ordered_queue"], ["def_order","def_p0_evidence_id","def_subsystem","def_hydra_risk","def_source_rel_path","def_secret_marker","def_danger_marker","def_error_marker","def_review_action","def_auto_fix_allowed","def_apply_enabled"], 500)}</div>
  <div class="sec"><h2>def P0 Evidence Rows Preview</h2>{table(payload["evidence_rows"], ["def_p0_evidence_id","def_subsystem","def_risk","def_hydra_risk","def_source_rel_path","def_secret_marker","def_danger_marker","def_error_marker","def_python_ast","def_review_reason","def_recommended_action","def_apply_enabled"], 500)}</div>

  <div class="footer">
    v0115E: <span class="path">{h(payload["v0115e_run"])}</span><br/>
    v0115D: <span class="path">{h(payload["v0115d_run"])}</span><br/>
    v0115C: <span class="path">{h(payload["v0115c_run"])}</span><br/>
    RunDir: <span class="path">{h(payload["run_dir"])}</span><br/>
    SAFE: No external call · No rescan · No source mutation · No canonical merge · No DB write · No apply
  </div>
</div></body></html>"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(doc, encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--v0115e-run", required=True)
    ap.add_argument("--run-dir", required=True)
    args = ap.parse_args()

    v0115e_run = Path(args.v0115e_run)
    run_dir = Path(args.run_dir)
    output = run_dir / "output"
    report = run_dir / "report"
    evidence_dir = run_dir / "_p0_ordered_review_evidence"
    output.mkdir(parents=True, exist_ok=True)
    report.mkdir(parents=True, exist_ok=True)
    evidence_dir.mkdir(parents=True, exist_ok=True)

    runs = resolve_runs(v0115e_run)
    v0115d_run = runs["v0115d"]
    v0115c_run = runs["v0115c"]

    summary_obj = read_json(v0115c_run / "output" / "VIA_v0115_MotherSystemPanorama_Summary.json")
    summary = summary_obj.get("summary", summary_obj)

    fix_rows = read_csv(v0115c_run / "output" / "VIA_v0115_FixOptimizationPlan.csv")
    inventory_rows = read_csv(v0115c_run / "output" / "VIA_v0115_FileInventory.csv")

    evidence_rows = build_p0_evidence(fix_rows, inventory_rows)
    package_summary = build_p0_package_summary(evidence_rows)
    ordered_queue = build_ordered_queue(evidence_rows)
    hydra_matrix = build_hydra_matrix(evidence_rows)
    false_positive_rules = build_false_positive_rules()
    readiness = build_readiness(evidence_rows, ordered_queue)

    write_csv(evidence_dir / "VIA_v0115F_P0_EvidenceRows.csv", evidence_rows)
    write_csv(evidence_dir / "VIA_v0115F_P0_PackageSummary.csv", package_summary)
    write_csv(evidence_dir / "VIA_v0115F_P0_OrderedReviewQueue.csv", ordered_queue)
    write_csv(evidence_dir / "VIA_v0115F_P0_HydraRiskMatrix.csv", hydra_matrix)
    write_csv(evidence_dir / "VIA_v0115F_P0_FalsePositiveTriageRules.csv", false_positive_rules)
    write_csv(output / "VIA_v0115F_ReadinessGate.csv", readiness)

    write_json(evidence_dir / "VIA_v0115F_P0_EvidenceRows.json", evidence_rows)
    write_json(evidence_dir / "VIA_v0115F_P0_PackageSummary.json", package_summary)
    write_json(evidence_dir / "VIA_v0115F_P0_OrderedReviewQueue.json", ordered_queue)
    write_json(evidence_dir / "VIA_v0115F_P0_HydraRiskMatrix.json", hydra_matrix)
    write_json(evidence_dir / "VIA_v0115F_P0_FalsePositiveTriageRules.json", false_positive_rules)
    write_json(output / "VIA_v0115F_ReadinessGate.json", readiness)

    html_path = report / "VIA_v0115F_P0_OrderedReviewEvidence_OnePage.html"
    payload = {
        "summary": summary,
        "v0115e_run": str(v0115e_run),
        "v0115d_run": str(v0115d_run),
        "v0115c_run": str(v0115c_run),
        "run_dir": str(run_dir),
        "evidence_rows": evidence_rows,
        "package_summary": package_summary,
        "ordered_queue": ordered_queue,
        "hydra_matrix": hydra_matrix,
        "false_positive_rules": false_positive_rules,
        "readiness": readiness
    }
    write_html(html_path, payload)

    manifest = {
        "schema_version": "VIA_v0115F_P0OrderedReviewEvidencePackage",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "gate": readiness[0]["def_gate_status"],
        "v0115e_run": str(v0115e_run),
        "v0115d_run": str(v0115d_run),
        "v0115c_run": str(v0115c_run),
        "run_dir": str(run_dir),
        "report": str(html_path),
        "outputs": {
            "evidence_rows": str(evidence_dir / "VIA_v0115F_P0_EvidenceRows.csv"),
            "package_summary": str(evidence_dir / "VIA_v0115F_P0_PackageSummary.csv"),
            "ordered_queue": str(evidence_dir / "VIA_v0115F_P0_OrderedReviewQueue.csv"),
            "hydra_matrix": str(evidence_dir / "VIA_v0115F_P0_HydraRiskMatrix.csv"),
            "false_positive_rules": str(evidence_dir / "VIA_v0115F_P0_FalsePositiveTriageRules.csv"),
            "readiness": str(output / "VIA_v0115F_ReadinessGate.csv")
        },
        "policy": {
            "p0_only": True,
            "ordered_review_only": True,
            "no_rescan": True,
            "external_call": False,
            "execution_enabled": False,
            "apply_enabled": False,
            "source_mutation": False,
            "canonical_merge": False,
            "db_write": False,
            "delete": False,
            "stop_process": False
        }
    }
    write_json(output / "VIA_v0115F_P0OrderedReviewEvidence_Manifest.json", manifest)

    print("")
    print("=" * 80)
    print("def VIA v0115F P0 Ordered Review Evidence COMPLETE")
    print("=" * 80)
    print("Gate       : P0_ORDERED_REVIEW_EVIDENCE_PACKAGE_READY_REVIEW_ONLY")
    print(f"P0 Rows    : {len(evidence_rows)}")
    print(f"Queue Rows : {len(ordered_queue)}")
    print(f"Report     : {html_path}")
    print(f"Evidence   : {evidence_dir}")
    print(f"Output     : {output}")
    print("[SAFE] No rescan. No external call. No apply. No source mutation. No DB write.")


if __name__ == "__main__":
    main()
