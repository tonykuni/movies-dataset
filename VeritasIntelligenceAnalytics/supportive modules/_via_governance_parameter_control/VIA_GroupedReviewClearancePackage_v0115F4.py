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


def package_name(bucket: str) -> str:
    mapping = {
        "TRUE_DANGER_BOUNDARY_REVIEW": "TRUE_DANGER_MANUAL_REVIEW_QUEUE",
        "TRUE_SECRET_RUNTIME_PARAMETER_REVIEW": "TRUE_SECRET_RUNTIME_PARAMETER_REVIEW_QUEUE",
        "GATED_DANGER_BOUNDARY_CONFIRMATION": "BOUNDARY_CONFIRMATION_QUEUE",
        "GATED_OR_ARTIFACT_DANGER_BOUNDARY_CONFIRMATION": "ARTIFACT_FALSE_POSITIVE_CONFIRMATION_QUEUE",
        "SECRET_FIELDNAME_CLEARANCE_CANDIDATE": "SECRET_FIELDNAME_CLEARANCE_QUEUE",
        "COMMENT_DOC_FALSE_POSITIVE_CLEARANCE": "COMMENT_DOC_FALSE_POSITIVE_CLEARANCE_QUEUE",
        "PATH_SIZE_REVIEW": "PATH_SIZE_REVIEW_QUEUE",
    }
    return mapping.get(bucket, "MANUAL_REVIEW_QUEUE")


def ry_status(package: str, risk: str) -> str:
    if package in {"TRUE_DANGER_MANUAL_REVIEW_QUEUE", "TRUE_SECRET_RUNTIME_PARAMETER_REVIEW_QUEUE"}:
        return "RED_REVIEW"
    if package in {"BOUNDARY_CONFIRMATION_QUEUE", "ARTIFACT_FALSE_POSITIVE_CONFIRMATION_QUEUE", "PATH_SIZE_REVIEW_QUEUE"}:
        return "YELLOW_CONFIRM"
    return "GREEN_CLEARANCE_CANDIDATE"


def build_package_rows(decisions: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    rows = []
    for i, r in enumerate(decisions, 1):
        bucket = prop(r, "def_decision_bucket")
        risk = prop(r, "def_decision_risk")
        pkg = package_name(bucket)

        rows.append({
            "def_package_row_id": f"F4-PKG-{i:06d}",
            "def_package_name": pkg,
            "def_ryg_status": ry_status(pkg, risk),
            "def_decision_id": prop(r, "def_decision_id"),
            "def_p0_evidence_id": prop(r, "def_p0_evidence_id"),
            "def_subsystem": prop(r, "def_subsystem"),
            "def_decision_bucket": bucket,
            "def_decision_risk": risk,
            "def_context_evidence_class": prop(r, "def_context_evidence_class"),
            "def_source_rel_path": prop(r, "def_source_rel_path"),
            "def_next_gate": next_gate_for_package(pkg),
            "def_required_human_action": required_action(pkg),
            "def_auto_fix_allowed": "false",
            "def_apply_enabled": "false",
            "def_source_read": "false",
            "def_source_mutation": "false",
            "def_db_write": "false"
        })
    return rows


def next_gate_for_package(pkg: str) -> str:
    if pkg == "TRUE_DANGER_MANUAL_REVIEW_QUEUE":
        return "v0115F5_TRUE_DANGER_MANUAL_REVIEW_PRECHECK_ONLY"
    if pkg == "TRUE_SECRET_RUNTIME_PARAMETER_REVIEW_QUEUE":
        return "v0115F5_SECRET_RUNTIME_PARAMETER_PRECHECK_ONLY"
    if pkg == "BOUNDARY_CONFIRMATION_QUEUE":
        return "v0115F5_BOUNDARY_CONFIRMATION_PRECHECK_ONLY"
    if pkg == "ARTIFACT_FALSE_POSITIVE_CONFIRMATION_QUEUE":
        return "v0115F5_ARTIFACT_FALSE_POSITIVE_CONFIRMATION_ONLY"
    if pkg == "SECRET_FIELDNAME_CLEARANCE_QUEUE":
        return "v0115F5_SECRET_FIELDNAME_CLEARANCE_LEDGER_ONLY"
    if pkg == "COMMENT_DOC_FALSE_POSITIVE_CLEARANCE_QUEUE":
        return "v0115F5_COMMENT_DOC_FALSE_POSITIVE_LEDGER_ONLY"
    if pkg == "PATH_SIZE_REVIEW_QUEUE":
        return "v0115F5_PATH_SIZE_SAMPLE_PLAN_ONLY"
    return "v0115F5_MANUAL_REVIEW_PRECHECK_ONLY"


def required_action(pkg: str) -> str:
    if pkg == "TRUE_DANGER_MANUAL_REVIEW_QUEUE":
        return "人工確認是否為 active source 中可執行危險流程；不得自動修補。"
    if pkg == "TRUE_SECRET_RUNTIME_PARAMETER_REVIEW_QUEUE":
        return "確認是否有 secret value；只允許轉 runtime parameter / env presence policy。"
    if pkg == "BOUNDARY_CONFIRMATION_QUEUE":
        return "確認是否已有 NoApply/NoMutation/Gate/Review/Disabled 邊界。"
    if pkg == "ARTIFACT_FALSE_POSITIVE_CONFIRMATION_QUEUE":
        return "確認是否屬於 backup/output/report/template/history artifact；若是，納入 clearance ledger。"
    if pkg == "SECRET_FIELDNAME_CLEARANCE_QUEUE":
        return "確認是否只是欄位名、參數名、contract name；若是，納入 clearance ledger。"
    if pkg == "COMMENT_DOC_FALSE_POSITIVE_CLEARANCE_QUEUE":
        return "確認是否只在註解、docstring、CSS、展示文字中；若是，納入 false-positive ledger。"
    if pkg == "PATH_SIZE_REVIEW_QUEUE":
        return "大型或未抽樣檔案；下一步只建立抽樣計畫，不全檔讀取。"
    return "人工確認。"


def build_summary(package_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    g = defaultdict(lambda: {"count": 0, "examples": []})
    for r in package_rows:
        key = (
            prop(r, "def_package_name"),
            prop(r, "def_ryg_status"),
            prop(r, "def_subsystem"),
            prop(r, "def_next_gate")
        )
        g[key]["count"] += 1
        if len(g[key]["examples"]) < 5:
            g[key]["examples"].append(prop(r, "def_source_rel_path"))

    rows = []
    n = 0
    for (pkg, ryg, subsystem, next_gate), payload in g.items():
        n += 1
        rows.append({
            "def_package_summary_id": f"F4-SUM-{n:04d}",
            "def_package_name": pkg,
            "def_ryg_status": ryg,
            "def_subsystem": subsystem,
            "def_count": payload["count"],
            "def_next_gate": next_gate,
            "def_examples": " | ".join(payload["examples"]),
            "def_auto_fix_allowed": "false",
            "def_apply_enabled": "false"
        })

    order = {"RED_REVIEW": 0, "YELLOW_CONFIRM": 1, "GREEN_CLEARANCE_CANDIDATE": 2}
    return sorted(rows, key=lambda x: (order.get(x["def_ryg_status"], 9), -int(x["def_count"]), x["def_subsystem"]))


def build_master_progress(package_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    c = Counter(prop(r, "def_package_name") for r in package_rows)

    return [
        {
            "PROCESS": "01 TRUE HIGH REVIEW",
            "SUPPORTIVE MODULES": "嚴禁自動修補；先人工核對 active source / command boundary",
            "VDF": f"Danger/Secret 高風險需 review：{c['TRUE_DANGER_MANUAL_REVIEW_QUEUE'] + c['TRUE_SECRET_RUNTIME_PARAMETER_REVIEW_QUEUE']} total across all subsystems",
            "VAP": "VAP active template/script 若命中 danger，先進 manual review，不直接修改 UI source",
            "OTHERS": "Registry / VRN / VETF / Unclassified 同樣 review-only",
            "RYG": "RED_REVIEW",
            "NEXT": "v0115F5 true high precheck only"
        },
        {
            "PROCESS": "02 BOUNDARY CONFIRMATION",
            "SUPPORTIVE MODULES": "確認 Gate / Dryrun / Review / Disabled 是否足以降級",
            "VDF": f"Boundary queues：{c['BOUNDARY_CONFIRMATION_QUEUE'] + c['ARTIFACT_FALSE_POSITIVE_CONFIRMATION_QUEUE']}",
            "VAP": "HTML/template/report 類 danger string 多半需 artifact confirmation",
            "OTHERS": "backup/output/report 不應視為 live source bug",
            "RYG": "YELLOW_CONFIRM",
            "NEXT": "v0115F5 boundary confirmation only"
        },
        {
            "PROCESS": "03 SECRET FIELDNAME CLEARANCE",
            "SUPPORTIVE MODULES": "欄位名/參數名/contract 名稱可入 clearance ledger",
            "VDF": f"Secret fieldname clearance rows：{c['SECRET_FIELDNAME_CLEARANCE_QUEUE']}",
            "VAP": "UI 不可存 secret value；但 field name / parameter label 可 clearance",
            "OTHERS": "JSON/CSV/registry 需分辨 field name vs value",
            "RYG": "GREEN_CLEARANCE_CANDIDATE",
            "NEXT": "v0115F5 fieldname clearance ledger only"
        },
        {
            "PROCESS": "04 FALSE POSITIVE / PATH SIZE",
            "SUPPORTIVE MODULES": "comment/docstring/CSS 與大型檔案分流處理",
            "VDF": "歷史矩陣/輸出檔納入 false-positive ledger",
            "VAP": f"Comment false positive：{c['COMMENT_DOC_FALSE_POSITIVE_CLEARANCE_QUEUE']}；PathSize：{c['PATH_SIZE_REVIEW_QUEUE']}",
            "OTHERS": "大型 registry 只建立抽樣計畫，不全檔讀取",
            "RYG": "YELLOW_CONFIRM",
            "NEXT": "v0115F5 false positive / path size only"
        }
    ]


def build_readiness(package_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    c = Counter(prop(r, "def_package_name") for r in package_rows)
    red = c["TRUE_DANGER_MANUAL_REVIEW_QUEUE"] + c["TRUE_SECRET_RUNTIME_PARAMETER_REVIEW_QUEUE"]
    yellow = c["BOUNDARY_CONFIRMATION_QUEUE"] + c["ARTIFACT_FALSE_POSITIVE_CONFIRMATION_QUEUE"] + c["PATH_SIZE_REVIEW_QUEUE"]
    green = c["SECRET_FIELDNAME_CLEARANCE_QUEUE"] + c["COMMENT_DOC_FALSE_POSITIVE_CLEARANCE_QUEUE"]

    return [{
        "def_gate_status": "GROUPED_REVIEW_CLEARANCE_PACKAGE_READY_REVIEW_ONLY",
        "def_allow_next": "true",
        "def_reason": "v0115F3 decision rows grouped into review and clearance packages. No source read, no mutation, no apply.",
        "def_input_rows": str(len(package_rows)),
        "def_red_review_rows": str(red),
        "def_yellow_confirmation_rows": str(yellow),
        "def_green_clearance_candidate_rows": str(green),
        "def_true_danger_manual_review_rows": str(c["TRUE_DANGER_MANUAL_REVIEW_QUEUE"]),
        "def_true_secret_runtime_review_rows": str(c["TRUE_SECRET_RUNTIME_PARAMETER_REVIEW_QUEUE"]),
        "def_boundary_confirmation_rows": str(c["BOUNDARY_CONFIRMATION_QUEUE"] + c["ARTIFACT_FALSE_POSITIVE_CONFIRMATION_QUEUE"]),
        "def_secret_fieldname_clearance_rows": str(c["SECRET_FIELDNAME_CLEARANCE_QUEUE"]),
        "def_false_positive_clearance_rows": str(c["COMMENT_DOC_FALSE_POSITIVE_CLEARANCE_QUEUE"]),
        "def_path_size_review_rows": str(c["PATH_SIZE_REVIEW_QUEUE"]),
        "def_source_read": "false",
        "def_execution_enabled": "false",
        "def_apply_enabled": "false",
        "def_source_mutation": "false",
        "def_canonical_merge": "false",
        "def_db_write": "false",
        "def_next_allowed_phase": "v0115F5 package-specific precheck only"
    }]


def render_table(rows: List[Dict[str, Any]], cols: List[str], max_rows: int = 600) -> str:
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
            if "RED_REVIEW" in joined or "TRUE_DANGER" in joined or "TRUE_SECRET" in joined:
                cls = " class='risk-red'"
            elif "YELLOW_CONFIRM" in joined or "BOUNDARY" in joined or "PATH_SIZE" in joined:
                cls = " class='risk-yellow'"
            elif "GREEN_CLEARANCE" in joined or "CLEARANCE" in joined:
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
        ("Red Review", readiness["def_red_review_rows"]),
        ("Yellow", readiness["def_yellow_confirmation_rows"]),
        ("Green", readiness["def_green_clearance_candidate_rows"]),
        ("Danger", readiness["def_true_danger_manual_review_rows"]),
        ("Secret", readiness["def_true_secret_runtime_review_rows"]),
        ("Next", "v0115F5")
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
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:10px}.footer{margin:12px 0 4px;color:var(--muted);font-size:8px}.path{font-family:Consolas,monospace;color:#355b63}
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
<head><meta charset="utf-8"/><title>VIA v0115F4 Grouped Review Clearance Package</title><style>{style}</style><script>{js}</script></head>
<body><div class="wrap">
  <div class="header">
    <div>
      <h1>def VIA v0115F4 · Grouped Review / Clearance Package Only</h1>
      <div class="sub">RYG Matrix · Manual Review · Boundary Confirmation · Secret Runtime · Clearance Ledger · No Source Read · No Apply</div>
    </div>
    <div class="seal">理</div>
  </div>

  <div class="cards">{cards}</div>

  <div class="sec">
    <h2>def Executive Judgment</h2>
    <span class="tag">PACKAGE ONLY</span><span class="tag">RYG GOVERNANCE</span><span class="tag">NO SOURCE READ</span><span class="tag">NO MUTATION</span><span class="tag">NO APPLY</span><span class="tag">NO DB WRITE</span>
    <div class="note">v0115F4 只把 v0115F3 的 decision matrix 拆成 review package 與 clearance package。不讀 source、不修檔、不 apply。下一步 v0115F5 才按 package 類別做 precheck。</div>
    <input id="q" class="search" oninput="filterTables(this.value)" placeholder="搜尋 RED_REVIEW / YELLOW_CONFIRM / GREEN_CLEARANCE / VDF / VAP / TRUE_SECRET / FIELDNAME ..."/>
    <button class="btn" onclick="quick('RED_REVIEW')">RED</button>
    <button class="btn" onclick="quick('YELLOW_CONFIRM')">YELLOW</button>
    <button class="btn" onclick="quick('GREEN_CLEARANCE')">GREEN</button>
    <button class="btn" onclick="quick('TRUE_DANGER')">TRUE_DANGER</button>
    <button class="btn" onclick="quick('TRUE_SECRET')">TRUE_SECRET</button>
    <button class="btn" onclick="quick('FIELDNAME')">FIELDNAME</button>
    <button class="btn" onclick="quick('VDF')">VDF</button>
    <button class="btn" onclick="quick('VAP')">VAP</button>
    <button class="btn" onclick="quick('')">RESET</button>
  </div>

  <div class="sec"><h2>def Readiness Gate</h2>{render_table(payload["readiness"], ["def_gate_status","def_allow_next","def_reason","def_input_rows","def_red_review_rows","def_yellow_confirmation_rows","def_green_clearance_candidate_rows","def_true_danger_manual_review_rows","def_true_secret_runtime_review_rows","def_boundary_confirmation_rows","def_secret_fieldname_clearance_rows","def_false_positive_clearance_rows","def_path_size_review_rows","def_apply_enabled","def_source_read","def_source_mutation","def_db_write","def_next_allowed_phase"], 20)}</div>
  <div class="sec"><h2>def PROCESS / SUPPORTIVE MODULES / VDF / VAP / OTHERS</h2>{render_table(payload["master_progress"], ["PROCESS","SUPPORTIVE MODULES","VDF","VAP","OTHERS","RYG","NEXT"], 40)}</div>
  <div class="sec"><h2>def Package Summary Matrix</h2>{render_table(payload["package_summary"], ["def_package_summary_id","def_package_name","def_ryg_status","def_subsystem","def_count","def_next_gate","def_auto_fix_allowed","def_apply_enabled"], 200)}</div>
  <div class="sec"><h2>def Full Grouped Package Matrix</h2>{render_table(payload["package_rows"], ["def_package_row_id","def_package_name","def_ryg_status","def_decision_id","def_p0_evidence_id","def_subsystem","def_decision_bucket","def_decision_risk","def_source_rel_path","def_next_gate","def_required_human_action","def_auto_fix_allowed","def_apply_enabled"], 700)}</div>

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
    package_dir = run_dir / "_grouped_review_clearance_package"
    output.mkdir(parents=True, exist_ok=True)
    report.mkdir(parents=True, exist_ok=True)
    package_dir.mkdir(parents=True, exist_ok=True)

    decision_path = source_run / "_active_p0_decision_matrix" / "VIA_v0115F3_ActiveP0_DecisionMatrix.csv"
    decisions = read_csv(decision_path)

    package_rows = build_package_rows(decisions)
    package_summary = build_summary(package_rows)
    master_progress = build_master_progress(package_rows)
    readiness = build_readiness(package_rows)

    write_csv(package_dir / "VIA_v0115F4_GroupedReviewClearancePackage.csv", package_rows)
    write_csv(package_dir / "VIA_v0115F4_GroupedReviewClearanceSummary.csv", package_summary)
    write_csv(package_dir / "VIA_v0115F4_ProcessSupportiveVdfVapOthersMatrix.csv", master_progress)
    write_csv(output / "VIA_v0115F4_ReadinessGate.csv", readiness)

    write_json(package_dir / "VIA_v0115F4_GroupedReviewClearancePackage.json", package_rows)
    write_json(package_dir / "VIA_v0115F4_GroupedReviewClearanceSummary.json", package_summary)
    write_json(package_dir / "VIA_v0115F4_ProcessSupportiveVdfVapOthersMatrix.json", master_progress)
    write_json(output / "VIA_v0115F4_ReadinessGate.json", readiness)

    html_path = report / "VIA_v0115F4_GroupedReviewClearancePackage_OnePage.html"
    payload = {
        "source_run": str(source_run),
        "run_dir": str(run_dir),
        "package_rows": package_rows,
        "package_summary": package_summary,
        "master_progress": master_progress,
        "readiness": readiness
    }
    write_html(html_path, payload)

    manifest = {
        "schema_version": "VIA_v0115F4_GroupedReviewClearancePackageOnly",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "gate": readiness[0]["def_gate_status"],
        "source_run": str(source_run),
        "run_dir": str(run_dir),
        "report": str(html_path),
        "outputs": {
            "package_rows": str(package_dir / "VIA_v0115F4_GroupedReviewClearancePackage.csv"),
            "package_summary": str(package_dir / "VIA_v0115F4_GroupedReviewClearanceSummary.csv"),
            "process_matrix": str(package_dir / "VIA_v0115F4_ProcessSupportiveVdfVapOthersMatrix.csv"),
            "readiness": str(output / "VIA_v0115F4_ReadinessGate.csv")
        },
        "policy": {
            "package_only": True,
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
    write_json(output / "VIA_v0115F4_GroupedReviewClearancePackage_Manifest.json", manifest)

    print("")
    print("=" * 80)
    print("def VIA v0115F4 Grouped Review Clearance Package COMPLETE")
    print("=" * 80)
    print("Gate       : GROUPED_REVIEW_CLEARANCE_PACKAGE_READY_REVIEW_ONLY")
    print(f"Input Rows : {len(package_rows)}")
    print(f"Report     : {html_path}")
    print(f"Package    : {package_dir}")
    print(f"Output     : {output}")
    print("[SAFE] No source read. No rescan. No apply. No source mutation. No DB write.")


if __name__ == "__main__":
    main()
