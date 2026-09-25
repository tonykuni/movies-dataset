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


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def prop(row: Dict[str, Any], key: str, default: str = "") -> str:
    v = row.get(key, default)
    return "" if v is None else str(v)


def h(x: Any) -> str:
    return html.escape("" if x is None else str(x))


def decision_for_class(cls: str, subsystem: str, path: str) -> Dict[str, str]:
    p = path.replace("\\", "/").lower()

    # Strong false-positive / historical boundaries.
    historical_markers = [
        "/backup/", "/runs/", "/run_", "/output/", "/outputs/",
        "/_integration_", "/_via_", "/dict/vdf/_active/",
        "before_", "template", "preview", "dryrun", "dry-run",
        "review", "seal", "gate", "sandbox", "candidate",
        ".csv", ".json", ".html", ".md", ".txt"
    ]

    is_historical_or_artifact = any(x in p for x in historical_markers)

    if cls == "TRUE_DANGER_CONTEXT_REVIEW_REQUIRED":
        if is_historical_or_artifact:
            return {
                "def_decision_bucket": "GATED_OR_ARTIFACT_DANGER_BOUNDARY_CONFIRMATION",
                "def_decision_risk": "MEDIUM_HIGH",
                "def_decision": "確認是否僅為 gate/report/backup/output 中的危險指令字串；不進自動修。",
                "def_next_gate": "v0115F4_BOUNDARY_FALSE_POSITIVE_CONFIRMATION_ONLY",
                "def_active_repair_candidate": "false"
            }
        return {
            "def_decision_bucket": "TRUE_DANGER_BOUNDARY_REVIEW",
            "def_decision_risk": "HIGH",
            "def_decision": "疑似 active source 內含危險命令或可執行流程；只能人工 ordered review。",
            "def_next_gate": "v0115F4_TRUE_DANGER_MANUAL_REVIEW_QUEUE_ONLY",
            "def_active_repair_candidate": "false"
        }

    if cls == "TRUE_SECRET_VALUE_SUSPECT_REVIEW_REQUIRED":
        return {
            "def_decision_bucket": "TRUE_SECRET_RUNTIME_PARAMETER_REVIEW",
            "def_decision_risk": "HIGH",
            "def_decision": "疑似 secret value；只允許轉 runtime parameter / env presence check，不可寫入 HTML/CSV/JSON 明文。",
            "def_next_gate": "v0115F4_SECRET_RUNTIME_PARAMETER_REVIEW_ONLY",
            "def_active_repair_candidate": "false"
        }

    if cls == "DANGER_IN_GATED_OR_REVIEW_BOUNDARY":
        return {
            "def_decision_bucket": "GATED_DANGER_BOUNDARY_CONFIRMATION",
            "def_decision_risk": "MEDIUM_HIGH",
            "def_decision": "看起來位於 gate/review/dryrun/disabled 邊界；下一步只做邊界確認。",
            "def_next_gate": "v0115F4_BOUNDARY_CONFIRMATION_ONLY",
            "def_active_repair_candidate": "false"
        }

    if cls == "SECRET_FIELD_NAME_OR_RUNTIME_PARAMETER_LIKELY":
        return {
            "def_decision_bucket": "SECRET_FIELDNAME_CLEARANCE_CANDIDATE",
            "def_decision_risk": "MEDIUM",
            "def_decision": "較像欄位名、參數名、runtime secret contract；可進 clearance candidate，但不修改 source。",
            "def_next_gate": "v0115F4_SECRET_FIELDNAME_CLEARANCE_ONLY",
            "def_active_repair_candidate": "false"
        }

    if cls == "COMMENT_OR_DOCSTRING_FALSE_POSITIVE_CANDIDATE":
        return {
            "def_decision_bucket": "COMMENT_DOC_FALSE_POSITIVE_CLEARANCE",
            "def_decision_risk": "LOW",
            "def_decision": "危險/secret marker 位於 comment/docstring/CSS/text；可進 false-positive clearance。",
            "def_next_gate": "v0115F4_FALSE_POSITIVE_CLEARANCE_ONLY",
            "def_active_repair_candidate": "false"
        }

    if cls in {"LARGE_FILE_SKIPPED", "FILE_MISSING_OR_UNREADABLE", "BINARY_FILE_SKIPPED"}:
        return {
            "def_decision_bucket": "PATH_SIZE_REVIEW",
            "def_decision_risk": "MEDIUM",
            "def_decision": "大型/缺檔/不可讀；不自動讀取，不修補，只做路徑與大小 review。",
            "def_next_gate": "v0115F4_PATH_SIZE_REVIEW_ONLY",
            "def_active_repair_candidate": "false"
        }

    return {
        "def_decision_bucket": "MANUAL_DECISION_REVIEW",
        "def_decision_risk": "MEDIUM",
        "def_decision": "無法自動清楚判定；維持人工 review。",
        "def_next_gate": "v0115F4_MANUAL_DECISION_REVIEW_ONLY",
        "def_active_repair_candidate": "false"
    }


def build_decisions(sample_rows: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    rows = []
    for i, r in enumerate(sample_rows, 1):
        cls = prop(r, "def_context_evidence_class")
        subsystem = prop(r, "def_subsystem")
        path = prop(r, "def_source_rel_path")
        d = decision_for_class(cls, subsystem, path)

        rows.append({
            "def_decision_id": f"P0-DEC-{i:06d}",
            "def_p0_evidence_id": prop(r, "def_p0_evidence_id"),
            "def_subsystem": subsystem,
            "def_context_evidence_class": cls,
            "def_context_confidence": prop(r, "def_context_confidence"),
            "def_source_rel_path": path,
            "def_read_status": prop(r, "def_read_status"),
            "def_context_hit_count": prop(r, "def_context_hit_count"),
            "def_ast_status": prop(r, "def_ast_status"),
            "def_decision_bucket": d["def_decision_bucket"],
            "def_decision_risk": d["def_decision_risk"],
            "def_decision": d["def_decision"],
            "def_next_gate": d["def_next_gate"],
            "def_active_repair_candidate": d["def_active_repair_candidate"],
            "def_apply_enabled": "false",
            "def_source_mutation": "false",
            "def_db_write": "false"
        })

    return rows


def build_decision_summary(decisions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    g = defaultdict(lambda: {"count": 0, "examples": []})
    for r in decisions:
        key = (
            prop(r, "def_decision_bucket"),
            prop(r, "def_decision_risk"),
            prop(r, "def_subsystem"),
            prop(r, "def_next_gate")
        )
        g[key]["count"] += 1
        if len(g[key]["examples"]) < 5:
            g[key]["examples"].append(prop(r, "def_source_rel_path"))

    out = []
    n = 0
    for (bucket, risk, subsystem, next_gate), payload in g.items():
        n += 1
        out.append({
            "def_summary_id": f"P0-DEC-SUM-{n:04d}",
            "def_decision_bucket": bucket,
            "def_decision_risk": risk,
            "def_subsystem": subsystem,
            "def_count": payload["count"],
            "def_next_gate": next_gate,
            "def_examples": " | ".join(payload["examples"]),
            "def_apply_enabled": "false"
        })

    risk_rank = {"HIGH": 0, "MEDIUM_HIGH": 1, "MEDIUM": 2, "LOW": 3}
    return sorted(out, key=lambda x: (risk_rank.get(x["def_decision_risk"], 9), -int(x["def_count"]), x["def_subsystem"]))


def build_master_matrix(decisions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    c = Counter()
    for r in decisions:
        c[prop(r, "def_decision_bucket")] += 1

    return [
        {
            "PROCESS": "01 Active P0 Decision Split",
            "SUPPORTIVE MODULES": f"TRUE_DANGER={c['TRUE_DANGER_BOUNDARY_REVIEW']} / SECRET_RUNTIME={c['TRUE_SECRET_RUNTIME_PARAMETER_REVIEW']}",
            "VDF": "VDF 先拆 danger boundary / secret runtime / fieldname clearance，不修 source",
            "VAP": "VAP HTML/CSS/JS/template 多數應進 UI false-positive or fieldname clearance",
            "OTHERS": "Registry / VRN / VIS / VETF 保持 review-only",
            "STATUS": "DECISION_READY_REVIEW_ONLY",
            "NEXT": "v0115F4 grouped review package only"
        },
        {
            "PROCESS": "02 Boundary Confirmation",
            "SUPPORTIVE MODULES": f"GATED_BOUNDARY={c['GATED_DANGER_BOUNDARY_CONFIRMATION']} / ARTIFACT_BOUNDARY={c['GATED_OR_ARTIFACT_DANGER_BOUNDARY_CONFIRMATION']}",
            "VDF": "v0113/v0114 gate/seal/dryrun/preview scripts 先確認邊界",
            "VAP": "HTML template 內 danger string 若是文字或 demo，不進 active repair",
            "OTHERS": "任何 backup/output/report 均不得直接視為 source bug",
            "STATUS": "BOUNDARY_REVIEW_ONLY",
            "NEXT": "v0115F4 boundary confirmation only"
        },
        {
            "PROCESS": "03 Secret Governance",
            "SUPPORTIVE MODULES": f"FIELDNAME={c['SECRET_FIELDNAME_CLEARANCE_CANDIDATE']} / TRUE_SECRET={c['TRUE_SECRET_RUNTIME_PARAMETER_REVIEW']}",
            "VDF": "FRED/API key 類維持 runtime parameter policy",
            "VAP": "UI 不可 localStorage/sessionStorage/URL 暴露 secret",
            "OTHERS": "JSON/CSV 中若是欄位名，進 clearance candidate",
            "STATUS": "SECRET_POLICY_READY",
            "NEXT": "v0115F4 secret runtime / fieldname clearance"
        },
        {
            "PROCESS": "04 False Positive Clearance",
            "SUPPORTIVE MODULES": f"COMMENT_DOC={c['COMMENT_DOC_FALSE_POSITIVE_CLEARANCE']} / PATH_SIZE={c['PATH_SIZE_REVIEW']}",
            "VDF": "輸出、矩陣、報告、歷史 gate 的文字命中應清到 audit ledger",
            "VAP": "CSS comment / docstring / templates 以 UI false-positive ledger 處理",
            "OTHERS": "大型檔案只留待抽樣，不全檔讀",
            "STATUS": "CLEARANCE_CANDIDATE",
            "NEXT": "v0115F4 clearance package only"
        }
    ]


def build_readiness(decisions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    c = Counter(prop(r, "def_decision_bucket") for r in decisions)
    true_high = c["TRUE_DANGER_BOUNDARY_REVIEW"] + c["TRUE_SECRET_RUNTIME_PARAMETER_REVIEW"]

    return [{
        "def_gate_status": "ACTIVE_P0_DECISION_MATRIX_READY_REVIEW_ONLY",
        "def_allow_next": "true",
        "def_reason": "Active P0 context evidence converted to decision matrix. No source read, no mutation, no apply.",
        "def_input_rows": str(len(decisions)),
        "def_true_high_review_rows": str(true_high),
        "def_boundary_confirmation_rows": str(c["GATED_DANGER_BOUNDARY_CONFIRMATION"] + c["GATED_OR_ARTIFACT_DANGER_BOUNDARY_CONFIRMATION"]),
        "def_secret_fieldname_clearance_rows": str(c["SECRET_FIELDNAME_CLEARANCE_CANDIDATE"]),
        "def_false_positive_clearance_rows": str(c["COMMENT_DOC_FALSE_POSITIVE_CLEARANCE"]),
        "def_path_size_review_rows": str(c["PATH_SIZE_REVIEW"]),
        "def_execution_enabled": "false",
        "def_apply_enabled": "false",
        "def_source_read": "false",
        "def_source_mutation": "false",
        "def_db_write": "false",
        "def_next_allowed_phase": "v0115F4 grouped review and clearance package only"
    }]


def render_table(rows: List[Dict[str, Any]], cols: List[str], max_rows: int = 500) -> str:
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
            if "TRUE_DANGER_BOUNDARY_REVIEW" in joined or "TRUE_SECRET_RUNTIME" in joined:
                cls = " class='risk-high'"
            elif "BOUNDARY" in joined or "PATH_SIZE" in joined:
                cls = " class='risk-med'"
            elif "CLEARANCE" in joined:
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


def write_html(path: Path, payload: Dict[str, Any]) -> None:
    readiness = payload["readiness"][0]

    cards = ""
    for k, v in [
        ("Gate", readiness["def_gate_status"]),
        ("Input", readiness["def_input_rows"]),
        ("True High", readiness["def_true_high_review_rows"]),
        ("Boundary", readiness["def_boundary_confirmation_rows"]),
        ("Fieldname", readiness["def_secret_fieldname_clearance_rows"]),
        ("False Positive", readiness["def_false_positive_clearance_rows"]),
        ("Apply", "false"),
        ("Next", "v0115F4")
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
.risk-high td{background:rgba(201,107,90,.08)}.risk-med td{background:rgba(196,148,58,.08)}.risk-low td{background:rgba(90,158,111,.065)}
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
<head><meta charset="utf-8"/><title>VIA v0115F3 Active P0 Decision Matrix</title><style>{style}</style><script>{js}</script></head>
<body><div class="wrap">
  <div class="header">
    <div>
      <h1>def VIA v0115F3 · Active P0 Decision Matrix Only</h1>
      <div class="sub">Decision Buckets · Boundary Confirmation · Secret Runtime Governance · False Positive Clearance · No Source Read · No Apply</div>
    </div>
    <div class="seal">理</div>
  </div>

  <div class="cards">{cards}</div>

  <div class="sec">
    <h2>def Executive Judgment</h2>
    <span class="tag">DECISION MATRIX ONLY</span><span class="tag">NO SOURCE READ</span><span class="tag">NO MUTATION</span><span class="tag">NO APPLY</span><span class="tag">NO DB WRITE</span>
    <div class="note">v0115F3 將 v0115F2/F2A 的 Active P0 context evidence 轉成決策矩陣。這一步不再讀 source，只讀已遮蔽的 sampling CSV/JSON。下一步 v0115F4 才依 bucket 產生 grouped review / clearance package，仍然不改 source。</div>
    <input id="q" class="search" oninput="filterTables(this.value)" placeholder="搜尋 TRUE_DANGER / TRUE_SECRET / BOUNDARY / FIELDNAME / CLEARANCE / VDF / VAP ..."/>
    <button class="btn" onclick="quick('TRUE_DANGER')">TRUE_DANGER</button>
    <button class="btn" onclick="quick('TRUE_SECRET')">TRUE_SECRET</button>
    <button class="btn" onclick="quick('BOUNDARY')">BOUNDARY</button>
    <button class="btn" onclick="quick('FIELDNAME')">FIELDNAME</button>
    <button class="btn" onclick="quick('CLEARANCE')">CLEARANCE</button>
    <button class="btn" onclick="quick('VDF')">VDF</button>
    <button class="btn" onclick="quick('VAP')">VAP</button>
    <button class="btn" onclick="quick('')">RESET</button>
  </div>

  <div class="sec"><h2>def Readiness Gate</h2>{render_table(payload["readiness"], ["def_gate_status","def_allow_next","def_reason","def_input_rows","def_true_high_review_rows","def_boundary_confirmation_rows","def_secret_fieldname_clearance_rows","def_false_positive_clearance_rows","def_path_size_review_rows","def_apply_enabled","def_source_read","def_source_mutation","def_db_write","def_next_allowed_phase"], 20)}</div>
  <div class="sec"><h2>def PROCESS / SUPPORTIVE MODULES / VDF / VAP / OTHERS</h2>{render_table(payload["master_matrix"], ["PROCESS","SUPPORTIVE MODULES","VDF","VAP","OTHERS","STATUS","NEXT"], 40)}</div>
  <div class="sec"><h2>def Decision Summary</h2>{render_table(payload["decision_summary"], ["def_summary_id","def_decision_bucket","def_decision_risk","def_subsystem","def_count","def_next_gate","def_apply_enabled"], 200)}</div>
  <div class="sec"><h2>def Full Decision Matrix</h2>{render_table(payload["decisions"], ["def_decision_id","def_p0_evidence_id","def_subsystem","def_context_evidence_class","def_context_confidence","def_decision_bucket","def_decision_risk","def_source_rel_path","def_next_gate","def_active_repair_candidate","def_apply_enabled"], 700)}</div>

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
    decision_dir = run_dir / "_active_p0_decision_matrix"
    output.mkdir(parents=True, exist_ok=True)
    report.mkdir(parents=True, exist_ok=True)
    decision_dir.mkdir(parents=True, exist_ok=True)

    sample_path = source_run / "_active_p0_context_sampling" / "VIA_v0115F2_ActiveP0_ContextSampleRows.csv"
    sample_rows = read_csv(sample_path)

    decisions = build_decisions(sample_rows)
    decision_summary = build_decision_summary(decisions)
    master_matrix = build_master_matrix(decisions)
    readiness = build_readiness(decisions)

    write_csv(decision_dir / "VIA_v0115F3_ActiveP0_DecisionMatrix.csv", decisions)
    write_csv(decision_dir / "VIA_v0115F3_ActiveP0_DecisionSummary.csv", decision_summary)
    write_csv(decision_dir / "VIA_v0115F3_MasterDecisionProgressMatrix.csv", master_matrix)
    write_csv(output / "VIA_v0115F3_ReadinessGate.csv", readiness)

    write_json(decision_dir / "VIA_v0115F3_ActiveP0_DecisionMatrix.json", decisions)
    write_json(decision_dir / "VIA_v0115F3_ActiveP0_DecisionSummary.json", decision_summary)
    write_json(decision_dir / "VIA_v0115F3_MasterDecisionProgressMatrix.json", master_matrix)
    write_json(output / "VIA_v0115F3_ReadinessGate.json", readiness)

    html_path = report / "VIA_v0115F3_ActiveP0_DecisionMatrix_OnePage.html"
    payload = {
        "source_run": str(source_run),
        "run_dir": str(run_dir),
        "decisions": decisions,
        "decision_summary": decision_summary,
        "master_matrix": master_matrix,
        "readiness": readiness
    }
    write_html(html_path, payload)

    manifest = {
        "schema_version": "VIA_v0115F3_ActiveP0DecisionMatrixOnly",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "gate": readiness[0]["def_gate_status"],
        "source_run": str(source_run),
        "run_dir": str(run_dir),
        "report": str(html_path),
        "outputs": {
            "decision_matrix": str(decision_dir / "VIA_v0115F3_ActiveP0_DecisionMatrix.csv"),
            "decision_summary": str(decision_dir / "VIA_v0115F3_ActiveP0_DecisionSummary.csv"),
            "master_matrix": str(decision_dir / "VIA_v0115F3_MasterDecisionProgressMatrix.csv"),
            "readiness": str(output / "VIA_v0115F3_ReadinessGate.csv")
        },
        "policy": {
            "decision_matrix_only": True,
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
    write_json(output / "VIA_v0115F3_ActiveP0DecisionMatrix_Manifest.json", manifest)

    print("")
    print("=" * 80)
    print("def VIA v0115F3 Active P0 Decision Matrix COMPLETE")
    print("=" * 80)
    print("Gate       : ACTIVE_P0_DECISION_MATRIX_READY_REVIEW_ONLY")
    print(f"Input Rows : {len(decisions)}")
    print(f"Report     : {html_path}")
    print(f"Decision   : {decision_dir}")
    print(f"Output     : {output}")
    print("[SAFE] No source read. No rescan. No apply. No source mutation. No DB write.")


if __name__ == "__main__":
    main()
