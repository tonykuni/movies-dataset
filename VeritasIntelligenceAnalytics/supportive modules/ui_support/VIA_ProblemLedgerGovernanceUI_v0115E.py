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


def table(rows: List[Dict[str, Any]], cols: List[str], max_rows: int = 300, css_class: str = "") -> str:
    out = [f"<table class='{css_class}'><thead><tr>"]
    for c in cols:
        out.append(f"<th>{h(c)}</th>")
    out.append("</tr></thead><tbody>")

    if not rows:
        out.append(f"<tr><td colspan='{len(cols)}'>No rows</td></tr>")
    else:
        for r in rows[:max_rows]:
            risk_class = ""
            joined = " ".join(str(v) for v in r.values()).upper()
            if "P0" in joined or "HIGH" in joined:
                risk_class = " class='risk-high'"
            elif "P1" in joined or "MEDIUM" in joined:
                risk_class = " class='risk-med'"
            elif "P2" in joined:
                risk_class = " class='risk-low'"
            out.append(f"<tr{risk_class}>")
            for c in cols:
                v = prop(r, c)
                if len(v) > 420:
                    v = v[:420] + "..."
                out.append(f"<td>{h(v)}</td>")
            out.append("</tr>")

    out.append("</tbody></table>")
    return "".join(out)


def find_source_v0115c_from_v0115d(v0115d_run: Path) -> Path:
    manifest = v0115d_run / "output" / "VIA_v0115D_GovernanceParameterControl_Manifest.json"
    if manifest.exists():
        obj = read_json(manifest)
        src = obj.get("source_run", "")
        if src and Path(src).exists():
            return Path(src)
    raise FileNotFoundError("Cannot resolve source v0115C run from v0115D manifest.")


def build_work_packages(problem_rows: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    grouped = defaultdict(lambda: {"count": 0, "examples": []})

    for r in problem_rows:
        key = (
            prop(r, "def_priority", "PX"),
            prop(r, "def_fix_class", "UNKNOWN"),
            prop(r, "def_risk", "UNKNOWN"),
            prop(r, "def_subsystem", "UNKNOWN"),
            prop(r, "def_recommended_control", "REVIEW")
        )
        count = int(prop(r, "def_count", "0") or "0")
        grouped[key]["count"] += count
        ex = prop(r, "def_examples", "")
        if ex and len(grouped[key]["examples"]) < 3:
            grouped[key]["examples"].append(ex)

    rows = []
    n = 0
    for (priority, fix_class, risk, subsystem, control), payload in grouped.items():
        n += 1

        if priority == "P0":
            gate = "v0115F_P0_ORDERED_REVIEW_ONLY"
            action = "只建立證據包與人工審核清單，不自動修。"
            hydra = "HIGH"
            parallel = "false"
        elif priority == "P1":
            gate = "v0115G_P1_SEQUENTIAL_REPAIR_CANDIDATE_ONLY"
            action = "依 dependency order 建立順序修正候選，不直接修改 source。"
            hydra = "MEDIUM"
            parallel = "false"
        elif priority == "P2":
            gate = "v0115H_P2_PARALLEL_CLASSIFICATION_PACKAGE_ONLY"
            action = "可平行分類、補 registry、補 SSOT candidate，但仍不動 source。"
            hydra = "LOW"
            parallel = "true"
        else:
            gate = "v0115I_P3_CONSOLIDATION_AND_UI_PACKAGE_ONLY"
            action = "文件、UI、命名、報表整理候選；適合最後收尾。"
            hydra = "LOW"
            parallel = "true"

        rows.append({
            "def_work_package_id": f"VIA-WP-{n:04d}",
            "def_priority": priority,
            "def_fix_class": fix_class,
            "def_risk": risk,
            "def_subsystem": subsystem,
            "def_count": payload["count"],
            "def_recommended_control": control,
            "def_hydra_risk": hydra,
            "def_parallel_safe_candidate": parallel,
            "def_next_gate": gate,
            "def_action": action,
            "def_examples": " || ".join(payload["examples"]),
            "def_apply_enabled": "false",
            "def_source_mutation": "false",
            "def_db_write": "false"
        })

    return sorted(rows, key=lambda x: (x["def_priority"], -int(x["def_count"]), x["def_subsystem"]))


def build_master_progress(
    summary: Dict[str, Any],
    problem_rows: List[Dict[str, str]],
    work_packages: List[Dict[str, Any]],
    subsystem_rows: List[Dict[str, str]]
) -> List[Dict[str, Any]]:
    priority_counts = Counter()
    for r in problem_rows:
        priority_counts[prop(r, "def_priority", "PX")] += int(prop(r, "def_count", "0") or "0")

    subsystem_counter = {}
    for r in subsystem_rows:
        subsystem_counter[prop(r, "def_subsystem", "UNKNOWN")] = prop(r, "def_files", "0")

    return [
        {
            "PROCESS": "01 Governance Command Center",
            "SUPPORTIVE MODULES": "EnvManager / RegistryCore / SSOT / Celeritas / Aegis 進入中央治理；PowerShell 只當 launcher",
            "VDF": "v0114 release chain 已完成多階 validation / seal；下一步只接 governance review，不 apply",
            "VAP": "VAP 承接高整合 HTML U/I、VisualLock、matrix dashboard、chart/layout governance",
            "OTHERS": "VRN / VETF / VIS / PromptOps / IAM 全部進 registry + SSOT candidate",
            "STATUS": "READY_REVIEW_ONLY",
            "NEXT": "v0115F P0 ordered review evidence package only"
        },
        {
            "PROCESS": "02 Problem Accounting Ledger",
            "SUPPORTIVE MODULES": f"P0={priority_counts.get('P0',0)} / P1={priority_counts.get('P1',0)} / P2={priority_counts.get('P2',0)} / P3={priority_counts.get('P3',0)}",
            "VDF": "P0 高風險 marker 先進 ordered review，不進自動修",
            "VAP": "UI 問題先用 preview matrix / no-writeback policy",
            "OTHERS": f"WorkPackages={len(work_packages)}; HighRisk={summary.get('HighRisk','')}; MediumRisk={summary.get('MediumRisk','')}",
            "STATUS": "ACCOUNTING_READY",
            "NEXT": "問題先修帳、分桶、排程，再談修補"
        },
        {
            "PROCESS": "03 Governance Parameter Control",
            "SUPPORTIVE MODULES": "Default parameter JSON 已建立；後續轉成正式 SSOT candidate",
            "VDF": "policy / registry / alias / schema 由 JSON 控制",
            "VAP": "ThemeRegistry / ChartSpec / LayoutSpec 由 JSON 控制",
            "OTHERS": f"RegistryRows={summary.get('RegistryRows','')}; SSOTRows={summary.get('SSOTRows','')}",
            "STATUS": "PARAMETER_READY",
            "NEXT": "v0115F 不改參數，只封存 review"
        },
        {
            "PROCESS": "04 Computer Optimization",
            "SUPPORTIVE MODULES": "不重掃、bounded hash、reuse CSV/JSON、no REPL、strict exit-code",
            "VDF": "不啟動 fetch / DB write / apply",
            "VAP": "HTML max preview rows + lazy table + filter",
            "OTHERS": "No network / no full-read large file / no parallel apply",
            "STATUS": "NO_STALL_OPTIMIZED",
            "NEXT": "大型掃描只在 explicit rescan gate 後再跑"
        },
        {
            "PROCESS": "05 HTML U/I Integration",
            "SUPPORTIVE MODULES": "一頁式 dashboard + matrix + buttons + filter，仍 read-only",
            "VDF": "VDF status 接入中央 dashboard",
            "VAP": "VAP 成為 UI layer，不碰資料核心",
            "OTHERS": "所有子系統統一欄位、統一 RYG、統一 next gate",
            "STATUS": "UI_BRIDGE_READY",
            "NEXT": "v0115F 產出 P0 review package"
        }
    ]


def build_parameter_map(param_rows: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    rows = []
    for r in param_rows:
        key = prop(r, "def_parameter_key")
        layer = prop(r, "def_control_layer")
        value = prop(r, "def_default_value")
        typ = prop(r, "def_parameter_type")

        if key.startswith("policy."):
            target = "GLOBAL_POLICY_GATE"
        elif key.startswith("python_runner."):
            target = "PYTHON_RUNNER_GATE"
        elif key.startswith("scan_defaults."):
            target = "SCAN_GOVERNANCE_GATE"
        elif key.startswith("risk_policy."):
            target = "RISK_CLASSIFICATION_GATE"
        elif key.startswith("fix_flow."):
            target = "THREE_ROUND_FIX_GATE"
        elif key.startswith("ui_defaults."):
            target = "HTML_UI_GATE"
        elif key.startswith("computer_optimization."):
            target = "PERFORMANCE_GATE"
        else:
            target = "GENERAL_SSOT_CANDIDATE"

        rows.append({
            "def_parameter_key": key,
            "def_control_layer": layer,
            "def_parameter_type": typ,
            "def_default_value": value,
            "def_target_gate": target,
            "def_governance_status": "DEFAULT_LOCKED_REVIEW_ONLY",
            "def_apply_enabled": "false"
        })
    return rows


def build_ui_bridge(master_rows, work_packages, parameter_map) -> List[Dict[str, Any]]:
    return [
        {
            "def_ui_component": "HeaderCards",
            "def_source": "v0115D summary/readiness",
            "def_function": "顯示 Files / HighRisk / MediumRisk / Registry / SSOT / FixRows / Apply",
            "def_writeback": "false",
            "def_status": "READY"
        },
        {
            "def_ui_component": "MasterProgressMatrix",
            "def_source": "v0115E master progress",
            "def_function": "PROCESS / SUPPORTIVE MODULES / VDF / VAP / OTHERS 總控",
            "def_writeback": "false",
            "def_status": "READY"
        },
        {
            "def_ui_component": "ProblemWorkPackages",
            "def_source": f"{len(work_packages)} work packages",
            "def_function": "P0/P1/P2/P3 分桶、Hydra 風險、下一個 gate",
            "def_writeback": "false",
            "def_status": "READY"
        },
        {
            "def_ui_component": "ParameterControlMap",
            "def_source": f"{len(parameter_map)} default parameter rows",
            "def_function": "將 default parameters 對接 policy / python runner / scan / risk / UI / performance gates",
            "def_writeback": "false",
            "def_status": "READY"
        },
        {
            "def_ui_component": "SmartFilters",
            "def_source": "client-side JavaScript only",
            "def_function": "依 P0/P1/P2/P3、High/Medium/Low、Subsystem 搜尋",
            "def_writeback": "false",
            "def_status": "READY"
        }
    ]


def write_html(path: Path, payload: Dict[str, Any]) -> None:
    summary = payload["summary"]
    cards = ""
    for k, v in [
        ("Gate", "PROBLEM_LEDGER_GOVERNANCE_UI_READY"),
        ("Files", summary.get("Files", "")),
        ("HighRisk", summary.get("HighRisk", "")),
        ("MediumRisk", summary.get("MediumRisk", "")),
        ("Registry", summary.get("RegistryRows", "")),
        ("SSOT", summary.get("SSOTRows", "")),
        ("FixRows", summary.get("FixRows", "")),
        ("Apply", "false"),
    ]:
        cards += f"<div class='card'><div class='k'>{h(k)}</div><div class='v'>{h(v)}</div></div>"

    style = """
:root{--bg:#f7f6f2;--paper:#fffefa;--line:#dedbd2;--ink:#24231f;--muted:#706d64;--seal:#8f2f24;--green:#5a9e6f;--yellow:#c4943a;--red:#c96b5a;--sky:#9fbcc2}
body{margin:0;background:radial-gradient(circle at 12% 10%,rgba(159,188,194,.24),transparent 28%),radial-gradient(circle at 88% 0%,rgba(180,200,190,.22),transparent 31%),linear-gradient(135deg,rgba(255,255,255,.68),rgba(247,246,242,1));color:var(--ink);font-family:'Microsoft JhengHei','Noto Sans TC',Arial,sans-serif;font-size:8.6px;line-height:1.35}
.wrap{max-width:1880px;margin:0 auto;padding:16px}.header{display:grid;grid-template-columns:1fr auto;gap:16px;align-items:start;margin-bottom:10px}
h1{font-size:15px;margin:0 0 4px;font-weight:650}.sub{font-size:8.2px;color:var(--muted)}
.seal{border:2px solid var(--seal);color:var(--seal);width:42px;height:42px;display:flex;align-items:center;justify-content:center;font-size:22px;font-weight:700;border-radius:6px;background:rgba(255,255,255,.48)}
.cards{display:grid;grid-template-columns:repeat(8,1fr);gap:7px;margin:10px 0}.card{background:var(--paper);border:1px solid var(--line);border-radius:10px;padding:7px;min-height:43px;box-shadow:0 8px 22px rgba(60,50,30,.045)}
.k{font-size:7.5px;color:var(--muted)}.v{font:650 10.4px Consolas,monospace;margin-top:4px;word-break:break-word}
.sec{background:rgba(255,254,250,.93);border:1px solid var(--line);border-radius:13px;padding:9px;margin-bottom:10px;overflow:hidden;box-shadow:0 10px 26px rgba(60,50,30,.045)}
h2{font-size:10px;margin:0 0 7px;font-weight:650}.note{white-space:pre-wrap;background:#fbfaf6;border:1px solid #e8e4da;border-radius:10px;padding:8px;color:#514d45;font-size:8.2px}
table{width:100%;border-collapse:collapse;table-layout:fixed;font-size:7.55px}th,td{border-bottom:1px solid #ebe8df;padding:3px 4px;vertical-align:top;word-break:break-word;overflow-wrap:anywhere}
th{background:#f0eee8;text-align:left;font-weight:650;color:#555149;position:sticky;top:0}tr:hover td{background:#f8f7f1}
.risk-high td{background:rgba(201,107,90,.075)}.risk-med td{background:rgba(196,148,58,.075)}.risk-low td{background:rgba(90,158,111,.06)}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:10px}.tag{display:inline-block;border:1px solid var(--line);border-radius:999px;padding:2px 7px;background:white;margin-right:4px;color:var(--muted)}
.bar{display:flex;gap:5px;flex-wrap:wrap;margin:8px 0}.btn{border:1px solid var(--line);background:white;border-radius:999px;padding:4px 9px;cursor:pointer;font-size:8px}.btn:hover{border-color:var(--sky)}
.search{width:100%;padding:7px 9px;border:1px solid var(--line);border-radius:9px;background:white;margin:6px 0 8px;font-size:9px}
.footer{margin:12px 0 4px;color:var(--muted);font-size:8px}.path{font-family:Consolas,monospace;color:#355b63}
"""
    html_doc = f"""<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8"/>
<title>VIA v0115E Problem Ledger Governance UI</title>
<style>{style}</style>
<script>
function filterTables(q){{
  q = (q || '').toLowerCase();
  document.querySelectorAll('tbody tr').forEach(function(tr){{
    var text = tr.innerText.toLowerCase();
    tr.style.display = text.indexOf(q) >= 0 ? '' : 'none';
  }});
}}
function quick(q){{ document.getElementById('q').value=q; filterTables(q); }}
</script>
</head>
<body>
<div class="wrap">
  <div class="header">
    <div>
      <h1>def VIA v0115E · 問題修帳子系統 × Governance Parameter Control × HTML U/I Bridge</h1>
      <div class="sub">PROCESS / SUPPORTIVE MODULES / VDF / VAP / OTHERS · Work Packages · Default Parameters · Hydra Control · No Apply</div>
    </div>
    <div class="seal">理</div>
  </div>

  <div class="cards">{cards}</div>

  <div class="sec">
    <h2>def Executive Judgment</h2>
    <span class="tag">NO RESCAN</span><span class="tag">PROBLEM LEDGER</span><span class="tag">WORK PACKAGES</span><span class="tag">JSON PARAMETER CONTROL</span><span class="tag">HTML READ ONLY</span><span class="tag">NO APPLY</span>
    <div class="note">v0115E 不重掃母系統，只讀 v0115D/v0115C 成果。現在的核心任務是把 6900 個 HIGH 與 5615 個 MEDIUM 先修成「問題帳本」與「工作包」，再透過 Governance Parameter Control 決定哪些只能人工 ordered review、哪些可 sequential、哪些可 parallel-safe。此階段不修 source，不 apply，不 DB write。</div>
    <input id="q" class="search" oninput="filterTables(this.value)" placeholder="搜尋 P0 / P1 / VDF / VAP / HIGH / sequential / parameter / db_write ..."/>
    <div class="bar">
      <button class="btn" onclick="quick('P0')">P0</button>
      <button class="btn" onclick="quick('P1')">P1</button>
      <button class="btn" onclick="quick('P2')">P2</button>
      <button class="btn" onclick="quick('P3')">P3</button>
      <button class="btn" onclick="quick('VDF')">VDF</button>
      <button class="btn" onclick="quick('VAP')">VAP</button>
      <button class="btn" onclick="quick('HIGH')">HIGH</button>
      <button class="btn" onclick="quick('')">RESET</button>
    </div>
  </div>

  <div class="sec"><h2>def Master Progress Matrix</h2>{table(payload["master_progress"], ["PROCESS","SUPPORTIVE MODULES","VDF","VAP","OTHERS","STATUS","NEXT"], 50)}</div>
  <div class="sec"><h2>def Problem Accounting Work Packages</h2>{table(payload["work_packages"], ["def_work_package_id","def_priority","def_fix_class","def_risk","def_subsystem","def_count","def_hydra_risk","def_parallel_safe_candidate","def_next_gate","def_action","def_apply_enabled","def_source_mutation","def_db_write"], 260)}</div>

  <div class="grid2">
    <div class="sec"><h2>def Governance → U/I Bridge</h2>{table(payload["ui_bridge"], ["def_ui_component","def_source","def_function","def_writeback","def_status"], 80)}</div>
    <div class="sec"><h2>def Readiness Gate</h2>{table(payload["readiness"], ["def_gate_status","def_allow_next","def_reason","def_execution_enabled","def_apply_enabled","def_source_mutation","def_db_write","def_next_allowed_phase"], 20)}</div>
  </div>

  <div class="sec"><h2>def Parameter Control Map</h2>{table(payload["parameter_map"], ["def_parameter_key","def_control_layer","def_parameter_type","def_default_value","def_target_gate","def_governance_status","def_apply_enabled"], 260)}</div>
  <div class="sec"><h2>def Subsystem Matrix</h2>{table(payload["subsystem_rows"], ["def_system_class","def_subsystem","def_files","def_total_bytes","def_high","def_medium","def_low","def_top_extensions"], 160)}</div>

  <div class="footer">
    Source v0115D: <span class="path">{h(payload["v0115d_run"])}</span><br/>
    Source v0115C: <span class="path">{h(payload["v0115c_run"])}</span><br/>
    RunDir: <span class="path">{h(payload["run_dir"])}</span><br/>
    SAFE: No external call · No rescan · No source mutation · No canonical merge · No DB write · No apply
  </div>
</div>
</body>
</html>"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html_doc, encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--v0115d-run", required=True)
    ap.add_argument("--run-dir", required=True)
    args = ap.parse_args()

    v0115d_run = Path(args.v0115d_run)
    run_dir = Path(args.run_dir)
    output = run_dir / "output"
    report = run_dir / "report"
    bridge = run_dir / "_governance_ui_bridge"
    output.mkdir(parents=True, exist_ok=True)
    report.mkdir(parents=True, exist_ok=True)
    bridge.mkdir(parents=True, exist_ok=True)

    v0115d_output = v0115d_run / "output"
    v0115c_run = find_source_v0115c_from_v0115d(v0115d_run)
    v0115c_output = v0115c_run / "output"

    manifest_d = read_json(v0115d_output / "VIA_v0115D_GovernanceParameterControl_Manifest.json")
    summary_obj = read_json(v0115c_output / "VIA_v0115_MotherSystemPanorama_Summary.json")
    summary = summary_obj.get("summary", summary_obj)

    problem_rows = read_csv(v0115d_output / "VIA_v0115D_ProblemLedger_FixAccounting.csv")
    parameter_rows = read_csv(v0115d_output / "VIA_v0115D_GovernanceParameterRows.csv")
    subsystem_rows = read_csv(v0115c_output / "VIA_v0115_SubsystemMatrix.csv")

    work_packages = build_work_packages(problem_rows)
    parameter_map = build_parameter_map(parameter_rows)
    master_progress = build_master_progress(summary, problem_rows, work_packages, subsystem_rows)
    ui_bridge = build_ui_bridge(master_progress, work_packages, parameter_map)

    readiness = [{
        "def_gate_status": "PROBLEM_LEDGER_GOVERNANCE_UI_READY_REVIEW_ONLY",
        "def_allow_next": "true",
        "def_reason": "Problem ledger governance UI and work packages generated. No rescan, no apply.",
        "def_execution_enabled": "false",
        "def_apply_enabled": "false",
        "def_source_mutation": "false",
        "def_canonical_merge": "false",
        "def_db_write": "false",
        "def_next_allowed_phase": "v0115F P0 ordered review evidence package only"
    }]

    write_csv(output / "VIA_v0115E_MasterProgressGovernanceMatrix.csv", master_progress)
    write_csv(output / "VIA_v0115E_ProblemAccountingWorkPackages.csv", work_packages)
    write_csv(output / "VIA_v0115E_DefaultParameterControlMap.csv", parameter_map)
    write_csv(output / "VIA_v0115E_GovernanceToUIBridge.csv", ui_bridge)
    write_csv(output / "VIA_v0115E_ReadinessGate.csv", readiness)

    write_json(output / "VIA_v0115E_MasterProgressGovernanceMatrix.json", master_progress)
    write_json(output / "VIA_v0115E_ProblemAccountingWorkPackages.json", work_packages)
    write_json(output / "VIA_v0115E_DefaultParameterControlMap.json", parameter_map)
    write_json(output / "VIA_v0115E_GovernanceToUIBridge.json", ui_bridge)
    write_json(output / "VIA_v0115E_ReadinessGate.json", readiness)

    payload = {
        "summary": summary,
        "manifest_d": manifest_d,
        "v0115d_run": str(v0115d_run),
        "v0115c_run": str(v0115c_run),
        "run_dir": str(run_dir),
        "master_progress": master_progress,
        "problem_rows": problem_rows,
        "work_packages": work_packages,
        "parameter_map": parameter_map,
        "ui_bridge": ui_bridge,
        "readiness": readiness,
        "subsystem_rows": subsystem_rows
    }

    html_path = report / "VIA_v0115E_ProblemLedger_GovernanceUI_OnePage.html"
    write_html(html_path, payload)

    manifest = {
        "schema_version": "VIA_v0115E_ProblemLedgerGovernanceUIBridge",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "gate": readiness[0]["def_gate_status"],
        "v0115d_run": str(v0115d_run),
        "v0115c_run": str(v0115c_run),
        "run_dir": str(run_dir),
        "report": str(html_path),
        "outputs": {
            "master_progress": str(output / "VIA_v0115E_MasterProgressGovernanceMatrix.csv"),
            "work_packages": str(output / "VIA_v0115E_ProblemAccountingWorkPackages.csv"),
            "parameter_map": str(output / "VIA_v0115E_DefaultParameterControlMap.csv"),
            "ui_bridge": str(output / "VIA_v0115E_GovernanceToUIBridge.csv"),
            "readiness": str(output / "VIA_v0115E_ReadinessGate.csv")
        },
        "policy": {
            "no_rescan": True,
            "external_call": False,
            "execution_enabled": False,
            "apply_enabled": False,
            "source_mutation": False,
            "canonical_merge": False,
            "db_write": False
        }
    }
    write_json(output / "VIA_v0115E_ProblemLedgerGovernanceUI_Manifest.json", manifest)

    print("")
    print("=" * 80)
    print("def VIA v0115E Problem Ledger Governance UI COMPLETE")
    print("=" * 80)
    print("Gate       : PROBLEM_LEDGER_GOVERNANCE_UI_READY_REVIEW_ONLY")
    print(f"v0115D     : {v0115d_run}")
    print(f"v0115C     : {v0115c_run}")
    print(f"RunDir     : {run_dir}")
    print(f"Report     : {html_path}")
    print(f"Output     : {output}")
    print("[SAFE] No rescan. No external call. No apply. No source mutation. No DB write.")


if __name__ == "__main__":
    main()
