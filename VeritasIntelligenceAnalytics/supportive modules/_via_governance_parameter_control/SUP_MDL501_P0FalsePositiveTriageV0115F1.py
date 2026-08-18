from __future__ import annotations

import argparse
import csv
import html
import json
import re
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


def table(rows: List[Dict[str, Any]], cols: List[str], max_rows: int = 500) -> str:
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
            if "TRUE_SECRET" in joined or "TRUE_DANGER" in joined or "MANUAL_REVIEW_REQUIRED" in joined:
                cls = " class='risk-high'"
            elif "NEEDS_CONTEXT" in joined:
                cls = " class='risk-med'"
            elif "LIKELY_FALSE_POSITIVE" in joined:
                cls = " class='risk-low'"
            out.append(f"<tr{cls}>")
            for c in cols:
                v = prop(r, c)
                if len(v) > 520:
                    v = v[:520] + "..."
                out.append(f"<td>{h(v)}</td>")
            out.append("</tr>")

    out.append("</tbody></table>")
    return "".join(out)


def resolve_runs(v0115f_run: Path) -> Dict[str, str]:
    manifest = v0115f_run / "output" / "VIA_v0115F_P0OrderedReviewEvidence_Manifest.json"
    if not manifest.exists():
        raise FileNotFoundError(f"Missing v0115F manifest: {manifest}")
    obj = read_json(manifest)
    return {
        "v0115e_run": obj.get("v0115e_run", ""),
        "v0115d_run": obj.get("v0115d_run", ""),
        "v0115c_run": obj.get("v0115c_run", "")
    }


def triage_rule(row: Dict[str, str]) -> Dict[str, str]:
    rel = prop(row, "def_source_rel_path")
    rel_l = rel.replace("\\", "/").lower()
    ext = prop(row, "def_source_ext").lower()
    subsystem = prop(row, "def_subsystem")
    secret = prop(row, "def_secret_marker") == "true"
    danger = prop(row, "def_danger_marker") == "true"
    err = prop(row, "def_error_marker") == "true"
    reason = prop(row, "def_review_reason").lower()
    action = prop(row, "def_recommended_action").lower()

    # 1. Vendor / venv / site-packages: almost always false positives in dependency source.
    if (
        "/site-packages/" in rel_l or
        rel_l.startswith(".venv/") or
        "/.venv/" in rel_l or
        "/lib/site-packages/" in rel_l or
        "/pip/_vendor/" in rel_l or
        "/setuptools/_vendor/" in rel_l
    ):
        return {
            "def_triage_class": "LIKELY_FALSE_POSITIVE_VENDOR_ENV",
            "def_confidence": "HIGH",
            "def_reason": "Path is Python virtual environment or third-party dependency; marker likely from vendor code or syntax sample.",
            "def_next_action": "EXCLUDE_FROM_P0_ACTIVE_REVIEW_CANDIDATE",
            "def_active_p0_candidate": "false"
        }

    # 2. Historical reports / logs / matrices.
    if (
        "/report/" in rel_l or
        "/reports/" in rel_l or
        "/runtime/" in rel_l or
        "/logs/" in rel_l or
        rel_l.endswith(".log") or
        "transcript" in rel_l or
        "matrix" in rel_l or
        "report" in rel_l or
        "_report" in rel_l
    ):
        return {
            "def_triage_class": "LIKELY_FALSE_POSITIVE_REPORT_LOG_HISTORY",
            "def_confidence": "HIGH",
            "def_reason": "Marker appears in report/log/matrix/runtime evidence, not active source path.",
            "def_next_action": "EXCLUDE_FROM_P0_ACTIVE_REVIEW_CANDIDATE_KEEP_AUDIT",
            "def_active_p0_candidate": "false"
        }

    # 3. Sandbox / staged / generated historical copies.
    if (
        "/sandbox/" in rel_l or
        "/staged/" in rel_l or
        "/_sandbox_repair_copies/" in rel_l or
        "/scope_copy/" in rel_l or
        "/_used_tools/" in rel_l or
        "/_toolbox_used/" in rel_l or
        "/runs/run_" in rel_l or
        "_not_run" in rel_l or
        "not-run" in rel_l or
        "generated-not-run" in rel_l or
        "repaired-not-run" in rel_l or
        "original_" in rel_l
    ):
        return {
            "def_triage_class": "LIKELY_FALSE_POSITIVE_SANDBOX_OR_STAGED_COPY",
            "def_confidence": "HIGH",
            "def_reason": "Path is run artifact, sandbox/staged copy, generated-not-run, or historical repair copy.",
            "def_next_action": "EXCLUDE_FROM_P0_ACTIVE_REVIEW_CANDIDATE_KEEP_AUDIT",
            "def_active_p0_candidate": "false"
        }

    # 4. Disabled boundary or preview-only script names.
    if (
        "disabled" in rel_l or
        "previewonly" in rel_l or
        "preview-only" in rel_l or
        "review_only" in rel_l or
        "review-only" in rel_l or
        "dryrun" in rel_l or
        "dry-run" in rel_l or
        "validation" in rel_l or
        "sealonly" in rel_l or
        "seal-only" in rel_l
    ):
        return {
            "def_triage_class": "LIKELY_FALSE_POSITIVE_DISABLED_OR_REVIEW_BOUNDARY",
            "def_confidence": "MEDIUM_HIGH",
            "def_reason": "Path name indicates disabled, preview, validation, seal-only, dryrun, or review-only boundary.",
            "def_next_action": "KEEP_BOUNDARY_REVIEW_BUT_REMOVE_FROM_ACTIVE_P0_FIX_QUEUE",
            "def_active_p0_candidate": "false"
        }

    # 5. JSON/CSV/HTML usually not executable source unless it contains real secrets.
    if ext in {".csv", ".json", ".html", ".md", ".txt"}:
        if secret and not danger:
            return {
                "def_triage_class": "NEEDS_CONTEXT_SECRET_STRING_IN_DATA_OR_DOC",
                "def_confidence": "MEDIUM",
                "def_reason": "Data/doc file contains secret-like marker; could be field name, report text, or true secret. Needs context review.",
                "def_next_action": "CONTEXT_REVIEW_NO_AUTO_FIX",
                "def_active_p0_candidate": "true"
            }
        if danger:
            return {
                "def_triage_class": "LIKELY_FALSE_POSITIVE_DOC_OR_MATRIX_DANGER_MARKER",
                "def_confidence": "MEDIUM_HIGH",
                "def_reason": "Dangerous command marker inside data/doc/report-like file is likely a recorded policy or evidence string.",
                "def_next_action": "EXCLUDE_FROM_AUTO_FIX_KEEP_AUDIT",
                "def_active_p0_candidate": "false"
            }

    # 6. Active PowerShell / Python source with danger marker remains active P0.
    if ext in {".ps1", ".psm1", ".py", ".cmd", ".bat", ".sh"} and danger:
        return {
            "def_triage_class": "TRUE_DANGER_REVIEW_REQUIRED",
            "def_confidence": "HIGH",
            "def_reason": "Executable source-like file has dangerous marker; ordered manual review still required.",
            "def_next_action": "KEEP_IN_ACTIVE_P0_ORDERED_REVIEW",
            "def_active_p0_candidate": "true"
        }

    # 7. Source with secret marker remains context review; do not auto-clear.
    if ext in {".ps1", ".psm1", ".py", ".js", ".ts", ".json"} and secret:
        return {
            "def_triage_class": "TRUE_SECRET_OR_RUNTIME_PARAMETER_REVIEW_REQUIRED",
            "def_confidence": "MEDIUM_HIGH",
            "def_reason": "Source/config-like file has secret-like marker; may be field name but must be reviewed before clearance.",
            "def_next_action": "KEEP_IN_ACTIVE_P0_ORDERED_REVIEW",
            "def_active_p0_candidate": "true"
        }

    # 8. Error-only markers in source become P1 candidate, not P0.
    if err and not secret and not danger:
        return {
            "def_triage_class": "DOWNGRADE_CANDIDATE_TO_P1_ERROR_CONTEXT_REVIEW",
            "def_confidence": "MEDIUM",
            "def_reason": "Error marker without secret/danger marker should move to P1 sequential context review.",
            "def_next_action": "P1_SEQUENTIAL_REVIEW_CANDIDATE",
            "def_active_p0_candidate": "false"
        }

    return {
        "def_triage_class": "MANUAL_REVIEW_REQUIRED",
        "def_confidence": "LOW",
        "def_reason": "No safe false-positive rule matched.",
        "def_next_action": "KEEP_IN_ACTIVE_P0_ORDERED_REVIEW",
        "def_active_p0_candidate": "true"
    }


def build_triage_rows(evidence_rows: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    rows = []
    for r in evidence_rows:
        decision = triage_rule(r)
        out = dict(r)
        out.update(decision)
        out["def_auto_fix_allowed"] = "false"
        out["def_apply_enabled"] = "false"
        out["def_source_mutation"] = "false"
        out["def_db_write"] = "false"
        rows.append(out)
    return rows


def build_summary(triage_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    groups = defaultdict(lambda: {"count": 0, "active": 0, "examples": []})
    for r in triage_rows:
        key = (
            prop(r, "def_triage_class"),
            prop(r, "def_confidence"),
            prop(r, "def_next_action"),
            prop(r, "def_active_p0_candidate")
        )
        groups[key]["count"] += 1
        if prop(r, "def_active_p0_candidate") == "true":
            groups[key]["active"] += 1
        if len(groups[key]["examples"]) < 5:
            groups[key]["examples"].append(prop(r, "def_source_rel_path"))

    rows = []
    n = 0
    for (klass, confidence, action, active), g in groups.items():
        n += 1
        rows.append({
            "def_triage_summary_id": f"P0-FP-SUM-{n:04d}",
            "def_triage_class": klass,
            "def_confidence": confidence,
            "def_count": g["count"],
            "def_active_p0_count": g["active"],
            "def_next_action": action,
            "def_active_p0_candidate": active,
            "def_examples": " | ".join(g["examples"]),
            "def_apply_enabled": "false"
        })
    return sorted(rows, key=lambda x: (x["def_active_p0_candidate"] != "true", -int(x["def_count"]), x["def_triage_class"]))


def build_subsystem_summary(triage_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    groups = defaultdict(Counter)
    for r in triage_rows:
        s = prop(r, "def_subsystem")
        groups[s]["total"] += 1
        groups[s][prop(r, "def_triage_class")] += 1
        if prop(r, "def_active_p0_candidate") == "true":
            groups[s]["active"] += 1
        else:
            groups[s]["cleared_candidate"] += 1

    rows = []
    for subsystem, c in groups.items():
        total = c["total"]
        active = c["active"]
        cleared = c["cleared_candidate"]
        rows.append({
            "def_subsystem": subsystem,
            "def_total_p0": total,
            "def_active_p0_after_triage": active,
            "def_false_positive_or_downgrade_candidate": cleared,
            "def_candidate_reduction_ratio": f"{(cleared / total if total else 0):.2%}",
            "def_vendor_env": c["LIKELY_FALSE_POSITIVE_VENDOR_ENV"],
            "def_report_log_history": c["LIKELY_FALSE_POSITIVE_REPORT_LOG_HISTORY"],
            "def_sandbox_or_staged": c["LIKELY_FALSE_POSITIVE_SANDBOX_OR_STAGED_COPY"],
            "def_disabled_boundary": c["LIKELY_FALSE_POSITIVE_DISABLED_OR_REVIEW_BOUNDARY"],
            "def_true_danger": c["TRUE_DANGER_REVIEW_REQUIRED"],
            "def_true_secret": c["TRUE_SECRET_OR_RUNTIME_PARAMETER_REVIEW_REQUIRED"],
            "def_manual_review": c["MANUAL_REVIEW_REQUIRED"],
            "def_apply_enabled": "false"
        })
    return sorted(rows, key=lambda x: (-int(x["def_active_p0_after_triage"]), -int(x["def_total_p0"]), x["def_subsystem"]))


def build_active_queue(triage_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    active = [r for r in triage_rows if prop(r, "def_active_p0_candidate") == "true"]

    rank = {
        "TRUE_DANGER_REVIEW_REQUIRED": 1,
        "TRUE_SECRET_OR_RUNTIME_PARAMETER_REVIEW_REQUIRED": 2,
        "NEEDS_CONTEXT_SECRET_STRING_IN_DATA_OR_DOC": 3,
        "MANUAL_REVIEW_REQUIRED": 4,
    }

    active.sort(key=lambda r: (
        rank.get(prop(r, "def_triage_class"), 99),
        prop(r, "def_subsystem"),
        prop(r, "def_source_rel_path")
    ))

    out = []
    for i, r in enumerate(active, 1):
        out.append({
            "def_order": f"{i:06d}",
            "def_p0_evidence_id": prop(r, "def_p0_evidence_id"),
            "def_subsystem": prop(r, "def_subsystem"),
            "def_triage_class": prop(r, "def_triage_class"),
            "def_confidence": prop(r, "def_confidence"),
            "def_source_rel_path": prop(r, "def_source_rel_path"),
            "def_secret_marker": prop(r, "def_secret_marker"),
            "def_danger_marker": prop(r, "def_danger_marker"),
            "def_error_marker": prop(r, "def_error_marker"),
            "def_next_action": prop(r, "def_next_action"),
            "def_auto_fix_allowed": "false",
            "def_apply_enabled": "false",
            "def_source_mutation": "false",
            "def_db_write": "false"
        })
    return out


def build_cleared_queue(triage_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    cleared = [r for r in triage_rows if prop(r, "def_active_p0_candidate") == "false"]
    out = []
    for i, r in enumerate(cleared, 1):
        out.append({
            "def_order": f"{i:06d}",
            "def_p0_evidence_id": prop(r, "def_p0_evidence_id"),
            "def_subsystem": prop(r, "def_subsystem"),
            "def_triage_class": prop(r, "def_triage_class"),
            "def_confidence": prop(r, "def_confidence"),
            "def_source_rel_path": prop(r, "def_source_rel_path"),
            "def_next_action": prop(r, "def_next_action"),
            "def_keep_audit": "true",
            "def_apply_enabled": "false",
            "def_source_mutation": "false",
            "def_db_write": "false"
        })
    return out


def build_readiness(total: int, active: int, cleared: int) -> List[Dict[str, Any]]:
    return [{
        "def_gate_status": "P0_FALSE_POSITIVE_TRIAGE_READY_REVIEW_ONLY",
        "def_allow_next": "true",
        "def_reason": "P0 false-positive triage generated from v0115F evidence. No source read, no rescan, no apply.",
        "def_p0_input_rows": str(total),
        "def_active_p0_after_triage": str(active),
        "def_false_positive_or_downgrade_candidates": str(cleared),
        "def_candidate_reduction_ratio": f"{(cleared / total if total else 0):.2%}",
        "def_execution_enabled": "false",
        "def_apply_enabled": "false",
        "def_source_read": "false",
        "def_source_mutation": "false",
        "def_canonical_merge": "false",
        "def_db_write": "false",
        "def_next_allowed_phase": "v0115F2 active P0 context sampling package only"
    }]


def write_html(path: Path, payload: Dict[str, Any]) -> None:
    readiness = payload["readiness"][0]
    cards = ""
    for k, v in [
        ("Gate", readiness["def_gate_status"]),
        ("Input P0", readiness["def_p0_input_rows"]),
        ("Active P0", readiness["def_active_p0_after_triage"]),
        ("FP/Downgrade", readiness["def_false_positive_or_downgrade_candidates"]),
        ("Reduction", readiness["def_candidate_reduction_ratio"]),
        ("Source Read", "false"),
        ("Apply", "false"),
        ("Next", "v0115F2")
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
.risk-high td{background:rgba(201,107,90,.075)}.risk-med td{background:rgba(196,148,58,.075)}.risk-low td{background:rgba(90,158,111,.06)}
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
<head><meta charset="utf-8"/><title>VIA v0115F1 P0 False-Positive Triage</title><style>{style}</style><script>{js}</script></head>
<body><div class="wrap">
  <div class="header">
    <div>
      <h1>def VIA v0115F1 · P0 False-Positive Triage Only</h1>
      <div class="sub">Vendor Env · Report/Log History · Sandbox/Staged Copy · Disabled Boundary · Active P0 Queue · No Source Read · No Apply</div>
    </div>
    <div class="seal">理</div>
  </div>

  <div class="cards">{cards}</div>

  <div class="sec">
    <h2>def Executive Judgment</h2>
    <span class="tag">FALSE-POSITIVE TRIAGE</span><span class="tag">NO SOURCE READ</span><span class="tag">NO RESCAN</span><span class="tag">NO AUTO FIX</span><span class="tag">NO APPLY</span>
    <div class="note">v0115F1 只用 v0115F evidence rows 做分類，不讀 source、不重掃、不改檔。這一步的價值是把 vendor env、歷史 report/log/matrix、sandbox/staged copy、generated-not-run、disabled/review/dryrun boundary 先從 active P0 queue 分流出去。分流結果仍是候選，下一步 v0115F2 才對仍 active 的 P0 做小樣本 context sampling package。</div>
    <input id="q" class="search" oninput="filterTables(this.value)" placeholder="搜尋 TRUE_DANGER / TRUE_SECRET / VDF / VAP / VENDOR_ENV / SANDBOX / ACTIVE ..."/>
    <button class="btn" onclick="quick('TRUE_DANGER')">TRUE_DANGER</button>
    <button class="btn" onclick="quick('TRUE_SECRET')">TRUE_SECRET</button>
    <button class="btn" onclick="quick('LIKELY_FALSE_POSITIVE')">FALSE_POSITIVE</button>
    <button class="btn" onclick="quick('VENDOR_ENV')">VENDOR_ENV</button>
    <button class="btn" onclick="quick('SANDBOX')">SANDBOX</button>
    <button class="btn" onclick="quick('VDF')">VDF</button>
    <button class="btn" onclick="quick('VAP')">VAP</button>
    <button class="btn" onclick="quick('')">RESET</button>
  </div>

  <div class="sec"><h2>def Readiness Gate</h2>{table(payload["readiness"], ["def_gate_status","def_allow_next","def_reason","def_p0_input_rows","def_active_p0_after_triage","def_false_positive_or_downgrade_candidates","def_candidate_reduction_ratio","def_source_read","def_apply_enabled","def_source_mutation","def_db_write","def_next_allowed_phase"], 20)}</div>
  <div class="sec"><h2>def Triage Summary</h2>{table(payload["summary_rows"], ["def_triage_summary_id","def_triage_class","def_confidence","def_count","def_active_p0_count","def_next_action","def_active_p0_candidate","def_apply_enabled"], 80)}</div>

  <div class="grid2">
    <div class="sec"><h2>def Subsystem Triage Summary</h2>{table(payload["subsystem_summary"], ["def_subsystem","def_total_p0","def_active_p0_after_triage","def_false_positive_or_downgrade_candidate","def_candidate_reduction_ratio","def_vendor_env","def_report_log_history","def_sandbox_or_staged","def_disabled_boundary","def_true_danger","def_true_secret","def_manual_review","def_apply_enabled"], 80)}</div>
    <div class="sec"><h2>def Active P0 Queue After Triage</h2>{table(payload["active_queue"], ["def_order","def_p0_evidence_id","def_subsystem","def_triage_class","def_confidence","def_source_rel_path","def_next_action","def_auto_fix_allowed","def_apply_enabled"], 260)}</div>
  </div>

  <div class="sec"><h2>def Cleared / Downgrade Candidate Queue Preview</h2>{table(payload["cleared_queue"], ["def_order","def_p0_evidence_id","def_subsystem","def_triage_class","def_confidence","def_source_rel_path","def_next_action","def_keep_audit","def_apply_enabled"], 500)}</div>
  <div class="sec"><h2>def Full Triage Rows Preview</h2>{table(payload["triage_rows"], ["def_p0_evidence_id","def_subsystem","def_risk","def_triage_class","def_confidence","def_active_p0_candidate","def_source_rel_path","def_secret_marker","def_danger_marker","def_error_marker","def_next_action","def_apply_enabled"], 500)}</div>

  <div class="footer">
    v0115F: <span class="path">{h(payload["v0115f_run"])}</span><br/>
    RunDir: <span class="path">{h(payload["run_dir"])}</span><br/>
    SAFE: No external call · No rescan · No source read · No source mutation · No canonical merge · No DB write · No apply
  </div>
</div></body></html>"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(doc, encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--v0115f-run", required=True)
    ap.add_argument("--run-dir", required=True)
    args = ap.parse_args()

    v0115f_run = Path(args.v0115f_run)
    run_dir = Path(args.run_dir)
    output = run_dir / "output"
    report = run_dir / "report"
    triage_dir = run_dir / "_p0_false_positive_triage"
    output.mkdir(parents=True, exist_ok=True)
    report.mkdir(parents=True, exist_ok=True)
    triage_dir.mkdir(parents=True, exist_ok=True)

    runs = resolve_runs(v0115f_run)
    evidence_rows = read_csv(v0115f_run / "_p0_ordered_review_evidence" / "VIA_v0115F_P0_EvidenceRows.csv")

    triage_rows = build_triage_rows(evidence_rows)
    summary_rows = build_summary(triage_rows)
    subsystem_summary = build_subsystem_summary(triage_rows)
    active_queue = build_active_queue(triage_rows)
    cleared_queue = build_cleared_queue(triage_rows)
    readiness = build_readiness(len(triage_rows), len(active_queue), len(cleared_queue))

    write_csv(triage_dir / "VIA_v0115F1_P0_TriageRows.csv", triage_rows)
    write_csv(triage_dir / "VIA_v0115F1_P0_TriageSummary.csv", summary_rows)
    write_csv(triage_dir / "VIA_v0115F1_P0_SubsystemTriageSummary.csv", subsystem_summary)
    write_csv(triage_dir / "VIA_v0115F1_P0_ActiveQueueAfterTriage.csv", active_queue)
    write_csv(triage_dir / "VIA_v0115F1_P0_ClearedOrDowngradeCandidates.csv", cleared_queue)
    write_csv(output / "VIA_v0115F1_ReadinessGate.csv", readiness)

    write_json(triage_dir / "VIA_v0115F1_P0_TriageRows.json", triage_rows)
    write_json(triage_dir / "VIA_v0115F1_P0_TriageSummary.json", summary_rows)
    write_json(triage_dir / "VIA_v0115F1_P0_SubsystemTriageSummary.json", subsystem_summary)
    write_json(triage_dir / "VIA_v0115F1_P0_ActiveQueueAfterTriage.json", active_queue)
    write_json(triage_dir / "VIA_v0115F1_P0_ClearedOrDowngradeCandidates.json", cleared_queue)
    write_json(output / "VIA_v0115F1_ReadinessGate.json", readiness)

    html_path = report / "VIA_v0115F1_P0_FalsePositiveTriage_OnePage.html"
    payload = {
        "v0115f_run": str(v0115f_run),
        "v0115e_run": runs["v0115e_run"],
        "v0115d_run": runs["v0115d_run"],
        "v0115c_run": runs["v0115c_run"],
        "run_dir": str(run_dir),
        "triage_rows": triage_rows,
        "summary_rows": summary_rows,
        "subsystem_summary": subsystem_summary,
        "active_queue": active_queue,
        "cleared_queue": cleared_queue,
        "readiness": readiness
    }
    write_html(html_path, payload)

    manifest = {
        "schema_version": "VIA_v0115F1_P0FalsePositiveTriageOnly",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "gate": readiness[0]["def_gate_status"],
        "v0115f_run": str(v0115f_run),
        "run_dir": str(run_dir),
        "report": str(html_path),
        "outputs": {
            "triage_rows": str(triage_dir / "VIA_v0115F1_P0_TriageRows.csv"),
            "triage_summary": str(triage_dir / "VIA_v0115F1_P0_TriageSummary.csv"),
            "subsystem_summary": str(triage_dir / "VIA_v0115F1_P0_SubsystemTriageSummary.csv"),
            "active_queue": str(triage_dir / "VIA_v0115F1_P0_ActiveQueueAfterTriage.csv"),
            "cleared_candidates": str(triage_dir / "VIA_v0115F1_P0_ClearedOrDowngradeCandidates.csv"),
            "readiness": str(output / "VIA_v0115F1_ReadinessGate.csv")
        },
        "policy": {
            "false_positive_triage_only": True,
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
    write_json(output / "VIA_v0115F1_P0FalsePositiveTriage_Manifest.json", manifest)

    print("")
    print("=" * 80)
    print("def VIA v0115F1 P0 False-Positive Triage COMPLETE")
    print("=" * 80)
    print("Gate       : P0_FALSE_POSITIVE_TRIAGE_READY_REVIEW_ONLY")
    print(f"Input P0   : {len(triage_rows)}")
    print(f"Active P0  : {len(active_queue)}")
    print(f"Cleared    : {len(cleared_queue)}")
    print(f"Report     : {html_path}")
    print(f"Triage     : {triage_dir}")
    print(f"Output     : {output}")
    print("[SAFE] No source read. No rescan. No apply. No source mutation. No DB write.")


if __name__ == "__main__":
    main()
