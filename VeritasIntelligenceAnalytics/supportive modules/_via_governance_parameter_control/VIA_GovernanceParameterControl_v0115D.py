# -*- coding: utf-8 -*-
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


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


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
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def flatten(prefix: str, obj: Any, out: List[Dict[str, Any]]) -> None:
    if isinstance(obj, dict):
        for k, v in obj.items():
            flatten(f"{prefix}.{k}" if prefix else str(k), v, out)
    elif isinstance(obj, list):
        out.append({
            "def_parameter_key": prefix,
            "def_parameter_type": "list",
            "def_default_value": "; ".join([str(x) for x in obj]),
            "def_control_layer": prefix.split(".")[0] if prefix else "root",
            "def_apply_enabled": "false"
        })
    else:
        out.append({
            "def_parameter_key": prefix,
            "def_parameter_type": type(obj).__name__,
            "def_default_value": str(obj),
            "def_control_layer": prefix.split(".")[0] if prefix else "root",
            "def_apply_enabled": "false"
        })


def prop(row: Dict[str, Any], key: str, default: str = "") -> str:
    return str(row.get(key, default) if row.get(key, default) is not None else default)


def table(rows: List[Dict[str, Any]], cols: List[str], max_rows: int = 300) -> str:
    buf = ["<table><thead><tr>"]
    for c in cols:
        buf.append(f"<th>{html.escape(c)}</th>")
    buf.append("</tr></thead><tbody>")

    if not rows:
        buf.append(f"<tr><td colspan='{len(cols)}'>No rows</td></tr>")
    else:
        for r in rows[:max_rows]:
            buf.append("<tr>")
            for c in cols:
                v = str(r.get(c, ""))
                if len(v) > 420:
                    v = v[:420] + "..."
                buf.append(f"<td>{html.escape(v)}</td>")
            buf.append("</tr>")
    buf.append("</tbody></table>")
    return "".join(buf)


def build_governance_matrix(summary: Dict[str, Any], fix_plan: List[Dict[str, str]], subsystem: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    risk = Counter([prop(r, "def_risk", "UNKNOWN") for r in fix_plan])
    prio = Counter([prop(r, "def_priority", "PX") for r in fix_plan])
    classes = Counter([prop(r, "def_system_class", "UNKNOWN") for r in subsystem])

    files = summary.get("Files", 0)
    registry = summary.get("RegistryRows", 0)
    ssot = summary.get("SSOTRows", 0)
    high = summary.get("HighRisk", 0)
    medium = summary.get("MediumRisk", 0)

    return [
        {
            "PROCESS": "01 母系統總盤點",
            "SUPPORTIVE MODULES": f"支援模組由 Python Manager 控制；Files={files}",
            "VDF": "VDF v0114 release chain 已到 validation/seal；仍 no apply",
            "VAP": "VAP 進入 UI/Chart/Layout/VisualLock governance",
            "OTHERS": "VRN / VETF / VIS / PromptOps / IAM 進入統一 registry",
            "STATUS": "READY_REVIEW_ONLY",
            "DETAIL": "v0115C 已成功掃描，v0115D 不重掃，只讀既有 CSV/JSON"
        },
        {
            "PROCESS": "02 問題修帳 Problem Ledger",
            "SUPPORTIVE MODULES": f"P0={prio.get('P0',0)} P1={prio.get('P1',0)} P2={prio.get('P2',0)} P3={prio.get('P3',0)}",
            "VDF": "高風險 marker 先進 ordered review，不直接修",
            "VAP": "UI 問題先以 preview/layout matrix 處理",
            "OTHERS": f"HIGH={high}; MEDIUM={medium}; RiskCounter={dict(risk)}",
            "STATUS": "ACCOUNTING_READY",
            "DETAIL": "修帳 = 把問題轉成可管理 ledger，而不是立刻改 source"
        },
        {
            "PROCESS": "03 Governance Parameter Control",
            "SUPPORTIVE MODULES": "Default parameters 已 JSON 化",
            "VDF": "VDF policy / registry / alias / schema 後續接 JSON SSOT",
            "VAP": "VAP ThemeRegistry / ChartSpec / LayoutSpec 後續接 JSON SSOT",
            "OTHERS": f"SSOTRows={ssot}; RegistryRows={registry}",
            "STATUS": "JSON_SSOT_READY",
            "DETAIL": "PowerShell 只當 launcher；Python 管核心；JSON 管參數；HTML 管審核"
        },
        {
            "PROCESS": "04 電腦效能最佳化",
            "SUPPORTIVE MODULES": "避免重掃、避免 full read、bounded hash、reuse latest output",
            "VDF": "不啟動 DB write / fetch / apply",
            "VAP": "HTML 預覽列數限制、one-page matrix、lazy review",
            "OTHERS": "no network / no parallel apply / no Stop-Process",
            "STATUS": "NO_STALL_OPTIMIZED",
            "DETAIL": "80872 檔掃描結果已存在；後續優先用 output CSV/JSON 做治理"
        },
        {
            "PROCESS": "05 複雜 HTML U/I 對接",
            "SUPPORTIVE MODULES": "Governance JSON → Python manager → HTML one-page U/I",
            "VDF": "VDF release status 可掛入 dashboard",
            "VAP": "VAP 作為高整合 UI 層，讀 JSON/CSV，不直接寫核心",
            "OTHERS": "所有子系統以統一欄位納入",
            "STATUS": "HTML_UI_BRIDGE_READY",
            "DETAIL": "高度整合但低耦合：UI 只讀，不直接 apply"
        }
    ]


def build_problem_ledger(fix_plan: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    groups = defaultdict(lambda: {
        "def_count": 0,
        "def_examples": [],
    })

    for r in fix_plan:
        key = (
            prop(r, "def_priority", "PX"),
            prop(r, "def_fix_class", "UNKNOWN"),
            prop(r, "def_risk", "UNKNOWN"),
            prop(r, "def_subsystem", "UNKNOWN"),
        )
        groups[key]["def_count"] += 1
        if len(groups[key]["def_examples"]) < 5:
            groups[key]["def_examples"].append(prop(r, "def_source_rel_path", ""))

    rows = []
    for (priority, fix_class, risk, subsystem), g in groups.items():
        if priority == "P0":
            action = "ORDERED_REVIEW_ONLY_NO_AUTO_FIX"
        elif priority == "P1":
            action = "SEQUENTIAL_SAFE_REVIEW"
        elif priority == "P2":
            action = "PARALLEL_SAFE_CLASSIFICATION"
        else:
            action = "CONSOLIDATION_CANDIDATE"

        rows.append({
            "def_priority": priority,
            "def_fix_class": fix_class,
            "def_risk": risk,
            "def_subsystem": subsystem,
            "def_count": g["def_count"],
            "def_recommended_control": action,
            "def_examples": " | ".join(g["def_examples"]),
            "def_apply_enabled": "false",
            "def_source_mutation": "false",
            "def_db_write": "false"
        })

    return sorted(rows, key=lambda x: (x["def_priority"], -int(x["def_count"]), x["def_subsystem"]))


def build_computer_optimization_matrix(params: Dict[str, Any], summary: Dict[str, Any]) -> List[Dict[str, Any]]:
    files = summary.get("Files", 0)
    return [
        {
            "def_layer": "SCAN",
            "def_issue": f"Large mother-system scan already completed: files={files}",
            "def_optimization": "Do not rescan by default; reuse latest CSV/JSON output.",
            "def_default_parameter": "scan_defaults.reuse_latest_output=true",
            "def_risk_control": "Rescan requires explicit future gate.",
            "def_status": "OPTIMIZED"
        },
        {
            "def_layer": "PYTHON",
            "def_issue": "Python entered REPL after run because inspect/startup environment was not fully removed.",
            "def_optimization": "Remove PYTHONINSPECT/PYTHONSTARTUP; run python with -I -X utf8 -B.",
            "def_default_parameter": "python_runner.prevent_repl=true",
            "def_risk_control": "Strict non-empty arg list and exit-code gate.",
            "def_status": "HOTFIXED"
        },
        {
            "def_layer": "HASH",
            "def_issue": "Full hashing large files can stall.",
            "def_optimization": "Use bounded hash and skip very large files unless explicitly requested.",
            "def_default_parameter": "scan_defaults.max_hash_mb_default=25",
            "def_risk_control": "Large file full read=false.",
            "def_status": "OPTIMIZED"
        },
        {
            "def_layer": "HTML_UI",
            "def_issue": "Too many rows can make browser sluggish.",
            "def_optimization": "Use one-page summary + capped preview rows + CSV links.",
            "def_default_parameter": "computer_optimization.html_max_preview_rows=260",
            "def_risk_control": "HTML is read-only.",
            "def_status": "OPTIMIZED"
        },
        {
            "def_layer": "APPLY",
            "def_issue": "High coupling changes may create Hydra risk.",
            "def_optimization": "Separate P0/P1/P2/P3 and block apply by default.",
            "def_default_parameter": "policy.apply_enabled=false",
            "def_risk_control": "Explicit future approval gate required.",
            "def_status": "LOCKED"
        }
    ]


def write_html(path: Path, data: Dict[str, Any]) -> None:
    summary = data["summary"]
    cards = ""
    for k, v in [
        ("Gate", "GOVERNANCE_PARAMETER_CONTROL_READY_REVIEW_ONLY"),
        ("Files", summary.get("Files", 0)),
        ("HighRisk", summary.get("HighRisk", 0)),
        ("MediumRisk", summary.get("MediumRisk", 0)),
        ("Registry", summary.get("RegistryRows", 0)),
        ("SSOT", summary.get("SSOTRows", 0)),
        ("FixRows", summary.get("FixRows", 0)),
        ("Apply", "false"),
    ]:
        cards += f"<div class='card'><div class='k'>{html.escape(str(k))}</div><div class='v'>{html.escape(str(v))}</div></div>"

    style = """
    :root{--bg:#f7f6f2;--paper:#fffefa;--line:#dedbd2;--ink:#24231f;--muted:#706d64;--seal:#8f2f24;--sky:#9fbcc2}
    body{margin:0;background:radial-gradient(circle at 12% 10%,rgba(159,188,194,.25),transparent 28%),radial-gradient(circle at 88% 0%,rgba(180,200,190,.22),transparent 31%),linear-gradient(135deg,rgba(255,255,255,.68),rgba(247,246,242,1));color:var(--ink);font-family:'Microsoft JhengHei','Noto Sans TC',Arial,sans-serif;font-size:8.6px;line-height:1.35}
    .wrap{max-width:1880px;margin:0 auto;padding:16px}.header{display:grid;grid-template-columns:1fr auto;gap:16px;align-items:start;margin-bottom:10px}
    h1{font-size:15px;margin:0 0 4px;font-weight:650;letter-spacing:.02em}.sub{font-size:8.2px;color:var(--muted)}
    .seal{border:2px solid var(--seal);color:var(--seal);width:42px;height:42px;display:flex;align-items:center;justify-content:center;font-size:22px;font-weight:700;border-radius:6px;background:rgba(255,255,255,.48)}
    .cards{display:grid;grid-template-columns:repeat(8,1fr);gap:7px;margin:10px 0}.card{background:var(--paper);border:1px solid var(--line);border-radius:10px;padding:7px;min-height:43px;box-shadow:0 8px 22px rgba(60,50,30,.045)}
    .k{font-size:7.5px;color:var(--muted)}.v{font:650 10.4px Consolas,monospace;margin-top:4px;word-break:break-word}
    .sec{background:rgba(255,254,250,.92);border:1px solid var(--line);border-radius:13px;padding:9px;margin-bottom:10px;overflow:hidden;box-shadow:0 10px 26px rgba(60,50,30,.045)}
    h2{font-size:10px;margin:0 0 7px;font-weight:650}.note{white-space:pre-wrap;background:#fbfaf6;border:1px solid #e8e4da;border-radius:10px;padding:8px;color:#514d45;font-size:8.2px}
    table{width:100%;border-collapse:collapse;table-layout:fixed;font-size:7.6px}th,td{border-bottom:1px solid #ebe8df;padding:3px 4px;vertical-align:top;word-break:break-word;overflow-wrap:anywhere}
    th{background:#f0eee8;text-align:left;font-weight:650;color:#555149}tr:hover td{background:#f8f7f1}
    .grid2{display:grid;grid-template-columns:1fr 1fr;gap:10px}.tag{display:inline-block;border:1px solid var(--line);border-radius:999px;padding:2px 7px;background:white;margin-right:4px;color:var(--muted)}
    .footer{margin:12px 0 4px;color:var(--muted);font-size:8px}.path{font-family:Consolas,monospace;color:#355b63}
    """

    doc = f"""<!doctype html>
<html lang="zh-Hant">
<head><meta charset="utf-8"/><title>VIA v0115D Governance Parameter Control</title><style>{style}</style></head>
<body><div class="wrap">
<div class="header">
  <div>
    <h1>def VIA v0115D · Mother System Governance Parameter Control</h1>
    <div class="sub">PROCESS / SUPPORTIVE MODULES / VDF / VAP / OTHERS · Default Parameters · Problem Ledger · Computer Optimization · HTML U/I · No Apply</div>
  </div>
  <div class="seal">理</div>
</div>
<div class="cards">{cards}</div>

<div class="sec">
  <h2>def Executive Judgment</h2>
  <span class="tag">NO RESCAN</span><span class="tag">NO REPL</span><span class="tag">STRICT EXITCODE</span><span class="tag">JSON DEFAULTS</span><span class="tag">HTML UI</span><span class="tag">NO APPLY</span>
  <div class="note">v0115D 只讀取已完成的 v0115C 掃描成果，不重掃 80872 檔。Python Runner 已改為 no-inspect / no-startup / isolated mode，避免再次進入 >>>。此階段建立中央 Governance Parameter Control，將母系統、子系統、預設參數、問題修帳、電腦效能優化與 HTML U/I 對接。</div>
</div>

<div class="sec"><h2>def MATRIX 總進度 · PROCESS / SUPPORTIVE MODULES / VDF / VAP / OTHERS</h2>{table(data["governance_matrix"], ["PROCESS","SUPPORTIVE MODULES","VDF","VAP","OTHERS","STATUS","DETAIL"], 50)}</div>
<div class="sec"><h2>def Governance Parameter Defaults</h2>{table(data["parameter_rows"], ["def_parameter_key","def_parameter_type","def_default_value","def_control_layer","def_apply_enabled"], 260)}</div>

<div class="grid2">
  <div class="sec"><h2>def Problem Ledger / 問題修帳</h2>{table(data["problem_ledger"], ["def_priority","def_fix_class","def_risk","def_subsystem","def_count","def_recommended_control","def_apply_enabled","def_source_mutation","def_db_write"], 180)}</div>
  <div class="sec"><h2>def Computer Optimization Matrix</h2>{table(data["computer_optimization"], ["def_layer","def_issue","def_optimization","def_default_parameter","def_risk_control","def_status"], 80)}</div>
</div>

<div class="sec"><h2>def Readiness Gate</h2>{table(data["readiness"], ["def_gate_status","def_allow_next","def_reason","def_files","def_high_risk","def_medium_risk","def_registry_rows","def_ssot_rows","def_fix_rows","def_execution_enabled","def_apply_enabled","def_db_write"], 20)}</div>
<div class="sec"><h2>def Subsystem Matrix</h2>{table(data["subsystem"], ["def_system_class","def_subsystem","def_files","def_total_bytes","def_high","def_medium","def_low","def_top_extensions"], 160)}</div>

<div class="footer">
SourceRun: <span class="path">{html.escape(str(data["source_run"]))}</span><br/>
RunDir: <span class="path">{html.escape(str(data["run_dir"]))}</span><br/>
SAFE: No external call · No rescan · No apply · No source mutation · No canonical merge · No DB write
</div>
</div></body></html>"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(doc, encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-run", required=True)
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--params", required=True)
    args = ap.parse_args()

    source_run = Path(args.source_run)
    run_dir = Path(args.run_dir)
    output = run_dir / "output"
    report = run_dir / "report"
    output.mkdir(parents=True, exist_ok=True)
    report.mkdir(parents=True, exist_ok=True)

    params = read_json(Path(args.params))

    source_output = source_run / "output"
    source_candidate = source_run / "_iam_registry_ssot_candidates"

    summary_obj = read_json(source_output / "VIA_v0115_MotherSystemPanorama_Summary.json")
    summary = summary_obj.get("summary", summary_obj)

    readiness = read_csv(source_output / "VIA_v0115_ReadinessGate.csv")
    subsystem = read_csv(source_output / "VIA_v0115_SubsystemMatrix.csv")
    fix_plan = read_csv(source_output / "VIA_v0115_FixOptimizationPlan.csv")

    parameter_rows: List[Dict[str, Any]] = []
    flatten("", params, parameter_rows)

    governance_matrix = build_governance_matrix(summary, fix_plan, subsystem)
    problem_ledger = build_problem_ledger(fix_plan)
    computer_optimization = build_computer_optimization_matrix(params, summary)

    write_csv(output / "VIA_v0115D_GovernanceParameterRows.csv", parameter_rows)
    write_csv(output / "VIA_v0115D_GovernanceProgressMatrix.csv", governance_matrix)
    write_csv(output / "VIA_v0115D_ProblemLedger_FixAccounting.csv", problem_ledger)
    write_csv(output / "VIA_v0115D_ComputerOptimizationMatrix.csv", computer_optimization)

    readiness_d = [{
        "def_gate_status": "GOVERNANCE_PARAMETER_CONTROL_READY_REVIEW_ONLY",
        "def_allow_next": "true",
        "def_reason": "Governance parameter control generated from existing v0115 output. No rescan, no apply.",
        "def_files": str(summary.get("Files", "")),
        "def_high_risk": str(summary.get("HighRisk", "")),
        "def_medium_risk": str(summary.get("MediumRisk", "")),
        "def_registry_rows": str(summary.get("RegistryRows", "")),
        "def_ssot_rows": str(summary.get("SSOTRows", "")),
        "def_fix_rows": str(summary.get("FixRows", "")),
        "def_execution_enabled": "false",
        "def_apply_enabled": "false",
        "def_source_mutation": "false",
        "def_db_write": "false"
    }]
    write_csv(output / "VIA_v0115D_ReadinessGate.csv", readiness_d)

    manifest = {
        "schema_version": "VIA_v0115D_GovernanceParameterControl",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source_run": str(source_run),
        "run_dir": str(run_dir),
        "params": str(args.params),
        "report": str(report / "VIA_v0115D_GovernanceParameterControl_OnePage_UI.html"),
        "policy": {
            "no_rescan": True,
            "external_call": False,
            "apply_enabled": False,
            "source_mutation": False,
            "canonical_merge": False,
            "db_write": False
        }
    }
    write_json(output / "VIA_v0115D_GovernanceParameterControl_Manifest.json", manifest)

    html_path = report / "VIA_v0115D_GovernanceParameterControl_OnePage_UI.html"
    write_html(html_path, {
        "summary": summary,
        "source_run": source_run,
        "run_dir": run_dir,
        "governance_matrix": governance_matrix,
        "parameter_rows": parameter_rows,
        "problem_ledger": problem_ledger,
        "computer_optimization": computer_optimization,
        "readiness": readiness_d,
        "subsystem": subsystem
    })

    print("")
    print("=" * 80)
    print("def VIA v0115D Governance Parameter Control COMPLETE")
    print("=" * 80)
    print("Gate       : GOVERNANCE_PARAMETER_CONTROL_READY_REVIEW_ONLY")
    print(f"SourceRun  : {source_run}")
    print(f"RunDir     : {run_dir}")
    print(f"Report     : {html_path}")
    print(f"Output     : {output}")
    print("[SAFE] No rescan. No apply. No source mutation. No DB write. No external call.")


if __name__ == "__main__":
    main()
