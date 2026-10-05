#!/usr/bin/env python3
"""Read-only inspection report generator for VIA AzureFlow v8.

The script never starts, stops, restarts, imports, or executes user source.
It reads the local workspace and performs GET requests to the configured API.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_BASE_URL = "http://127.0.0.1:8766"
DEFAULT_ROOT = Path("/home/ubuntu/work/reconstruction")
DEFAULT_RUNS_DIR = DEFAULT_ROOT / "app" / "runs"

MODULE_SURFACES = {
    "VIA-MOD-001": "source_ledger",
    "VIA-MOD-002": "text_nlp",
    "VIA-MOD-003": "discussion_commands",
    "VIA-MOD-004": "knowledge_mindmap",
    "VIA-MOD-005": "ast_modules",
    "VIA-MOD-006": "governance",
    "VIA-MOD-007": "runtime",
}

OUTPUT_FILES = {
    "source_preserved": "source_preserved.txt",
    "corrected_content": "corrected_content.md",
    "summary_markdown": "SUMMARY.md",
    "summary_v5": "summary_v5.json",
    "record": "record.json",
    "v8_unified": "v8_unified.json",
    "v8_source_ledger": "v8_source_ledger.json",
    "v8_text_nlp": "v8_text_nlp.json",
    "v8_discussion_commands": "v8_discussion_commands.json",
    "v8_knowledge_mindmap": "v8_knowledge_mindmap.json",
    "v8_ast_modules": "v8_ast_modules.json",
    "v8_governance": "v8_governance.json",
    "program_spec": "program_spec.md",
    "program_structure": "program_structure.json",
    "dashboard_snapshot": "dashboard_snapshot.json",
}


def compact(value: Any, limit: int = 500) -> str:
    text = json.dumps(value, ensure_ascii=False, sort_keys=True) if not isinstance(value, str) else value
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


def md_cell(value: Any) -> str:
    return compact(value).replace("|", "\\|").replace("\n", " ")


def get_json(base_url: str, endpoint: str, timeout: float = 8.0) -> tuple[Any | None, str | None]:
    url = base_url.rstrip("/") + endpoint
    request = urllib.request.Request(url, headers={"Accept": "application/json"}, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8", errors="replace")
            return json.loads(body), None
    except urllib.error.HTTPError as exc:
        return None, f"HTTP {exc.code} for {endpoint}"
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        return None, f"{type(exc).__name__} for {endpoint}: {exc}"


def load_json(path: Path) -> Any | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None


def num(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def fmt_duration(job: dict[str, Any]) -> str:
    started = job.get("started_at")
    completed = job.get("completed_at")
    if started is None or completed is None:
        return "n/a"
    return f"{max(0.0, num(completed) - num(started)):.3f} s"


def fmt_time(value: Any) -> str:
    if value is None:
        return "n/a"
    try:
        return datetime.fromtimestamp(float(value), tz=timezone.utc).isoformat()
    except (TypeError, ValueError, OSError, OverflowError):
        return str(value)


def read_run(run_dir: Path) -> dict[str, Any]:
    data: dict[str, Any] = {"path": str(run_dir), "exists": run_dir.is_dir(), "files": []}
    if not run_dir.is_dir():
        return data
    data["files"] = sorted(p.name for p in run_dir.iterdir() if p.is_file())
    for key in ("record", "summary_v5", "v8_unified", "v8_ast_modules", "v8_governance"):
        filename = {"record": "record.json", "summary_v5": "summary_v5.json", "v8_unified": "v8_unified.json", "v8_ast_modules": "v8_ast_modules.json", "v8_governance": "v8_governance.json"}[key]
        data[key] = load_json(run_dir / filename)
    data["file_sizes"] = {name: (run_dir / name).stat().st_size for name in data["files"] if (run_dir / name).is_file()}
    return data


def registry_engines(root: Path) -> tuple[dict[str, dict[str, Any]], dict[str, Any] | None]:
    registry = load_json(root / "VIA_SSOT_Engine_Registry_v8.json")
    if not isinstance(registry, dict):
        return {}, None
    engines = {item.get("engine_id"): item for item in registry.get("engines", []) if isinstance(item, dict) and item.get("engine_id")}
    return engines, registry


def merge_engines(catalog: dict[str, Any] | None, registry_map: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    catalog_map = {}
    if isinstance(catalog, dict):
        for item in catalog.get("engines", []):
            if isinstance(item, dict) and item.get("engine_id"):
                catalog_map[item["engine_id"]] = item
    merged: list[dict[str, Any]] = []
    for engine_id in ["VIA-ENG-022", *MODULE_SURFACES]:
        value = dict(registry_map.get(engine_id, {}))
        value.update(catalog_map.get(engine_id, {}))
        value.setdefault("engine_id", engine_id)
        if engine_id.startswith("VIA-MOD-"):
            value.setdefault("editable_surface", MODULE_SURFACES[engine_id])
        value.setdefault("status", "unknown")
        merged.append(value)
    return merged


def quality_summary(run: dict[str, Any]) -> dict[str, Any]:
    record = run.get("record") if isinstance(run.get("record"), dict) else {}
    gates = record.get("quality_gates") if isinstance(record.get("quality_gates"), dict) else {}
    v8 = run.get("v8_unified") if isinstance(run.get("v8_unified"), dict) else {}
    projection = v8.get("projection") if isinstance(v8.get("projection"), dict) else {}
    quality = projection.get("quality") if isinstance(projection.get("quality"), dict) else {}
    return {
        "source_preserved": gates.get("source_preserved", quality.get("v8_source_preserved")),
        "source_mutated": gates.get("source_mutated", quality.get("source_text_mutated", quality.get("v8_source_mutated"))),
        "source_deleted": gates.get("source_deleted"),
        "source_sha256": (record.get("source") or {}).get("source_sha256") if isinstance(record.get("source"), dict) else None,
        "source_coverage": gates.get("source_coverage"),
        "code_execution": gates.get("code_execution", quality.get("policy", {}).get("code_execution") if isinstance(quality.get("policy"), dict) else None),
        "network": gates.get("network_access", quality.get("policy", {}).get("network") if isinstance(quality.get("policy"), dict) else None),
        "subprocess": gates.get("subprocess_access"),
        "review_required": gates.get("review_required", quality.get("review_required")),
    }


def job_detail(job: dict[str, Any], runs_dir: Path) -> dict[str, Any]:
    job_id = str(job.get("job_id", ""))
    run = read_run(runs_dir / job_id)
    record = run.get("record") if isinstance(run.get("record"), dict) else {}
    source = record.get("source") if isinstance(record.get("source"), dict) else {}
    summary = run.get("summary_v5") if isinstance(run.get("summary_v5"), dict) else {}
    v8 = run.get("v8_unified") if isinstance(run.get("v8_unified"), dict) else {}
    projection = v8.get("projection") if isinstance(v8.get("projection"), dict) else {}
    quality = projection.get("quality") if isinstance(projection.get("quality"), dict) else {}
    ast = run.get("v8_ast_modules") if isinstance(run.get("v8_ast_modules"), dict) else {}
    metrics = job.get("metrics") if isinstance(job.get("metrics"), dict) else {}
    return {
        "job": job,
        "run": run,
        "source": source,
        "summary": summary,
        "v8": v8,
        "quality": quality,
        "ast": ast,
        "metrics": metrics,
        "gates": quality_summary(run),
        "topics": len(summary.get("topics", [])) if isinstance(summary.get("topics"), list) else metrics.get("topics", 0),
        "units": len(record.get("units", [])) if isinstance(record.get("units"), list) else metrics.get("units", 0),
    }


def api_probe(base_url: str, job_id: str, logical_key: str) -> str:
    url = base_url.rstrip("/") + f"/api/artifact/{job_id}/{logical_key}"
    request = urllib.request.Request(url, headers={"Accept": "*/*"}, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=8.0) as response:
            return str(response.status)
    except urllib.error.HTTPError as exc:
        return str(exc.code)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return f"unreachable ({type(exc).__name__})"


def render_report(base_url: str, root: Path, runs_dir: Path, payload: dict[str, Any], probe_artifacts: bool) -> str:
    now = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    health = payload.get("health") if isinstance(payload.get("health"), dict) else {}
    catalog = payload.get("catalog") if isinstance(payload.get("catalog"), dict) else {}
    status = payload.get("status") if isinstance(payload.get("status"), dict) else {}
    dashboard = payload.get("dashboard") if isinstance(payload.get("dashboard"), dict) else {}
    registry = payload.get("registry") if isinstance(payload.get("registry"), dict) else {}
    engines = payload.get("engines", [])
    details = payload.get("details", [])
    jobs = payload.get("jobs", [])
    errors = payload.get("api_errors", [])
    lines: list[str] = []
    lines += [
        "# VIA 天青智流 AzureFlow v8 檢查報告",
        "",
        f"**檢查時間：** {now}  ",
        f"**API：** `{base_url}`  ",
        f"**工作區：** `{root}`  ",
        "",
        "## 1. 執行摘要",
        "",
        f"- API health：`{health.get('status', 'unavailable')}`；API status：`{status.get('status', 'unavailable')}`。",
        f"- 八個核心引擎：`{len(engines)}`；可用輸出格式：`{len(catalog.get('output_formats', [])) if isinstance(catalog.get('output_formats'), list) else 'n/a'}`。",
        f"- Jobs：`{len(jobs)}` 個可見，completed={sum(1 for j in jobs if j.get('status') == 'completed')}，running={sum(1 for j in jobs if j.get('status') == 'running')}，failed={sum(1 for j in jobs if j.get('status') == 'failed')}。",
        f"- SSOT registry status：`{registry.get('status', 'unavailable')}`；請勿將 API PASS 解讀為解除人工審核。",
        "",
        "## 2. 八個核心引擎狀態",
        "",
        "| ID | 名稱 | 中文名稱 | kind | status | editable surface | legacy aliases |",
        "|---|---|---|---|---|---|---|",
    ]
    for engine in engines:
        aliases = engine.get("legacy_aliases", [])
        if not aliases and isinstance(registry.get("legacy_aliases"), dict):
            aliases = [alias for alias, target in registry["legacy_aliases"].items() if target == engine.get("engine_id")]
        surface = engine.get("editable_surface") or MODULE_SURFACES.get(engine.get("engine_id"), "facade")
        lines.append("| " + " | ".join(md_cell(engine.get(key, "n/a")) for key in ("engine_id", "canonical_name", "canonical_name_zh", "kind", "status")) + f" | `{md_cell(surface)}` | `{md_cell(', '.join(aliases) if aliases else '—')}` |")
    lines += ["", "### 2.1 串接拓撲", "", "```text", "輸入／Windows I/O／拖曳", "        ↓", "VIA-ENG-022 統一 NLP 編排器", "        ↓", "MOD-001 source ledger → MOD-002 text/NLP → MOD-003 discussion/commands", "        ↓", "MOD-004 knowledge/mind map ──┐", "                              └→ MOD-005 AST/static fallback", "        ↓", "MOD-006 governance/export → MOD-007 runtime/serialization/dashboard", "        ↓", "AzureFlow UI／artifact endpoint／Downloads", "```", "", "### 2.2 引擎責任與安全", "", "- `VIA-MOD-001` 讀取格式、建立 source hash 與 immutable ledger。", "- `VIA-MOD-002` 修正空格／斷句／標點並建立 token、Regex、同義字、factor、parameter projection。", "- `VIA-MOD-003` 建立 topics、回題、指令與 proposal-only similarity merge。", "- `VIA-MOD-004` 產生 SUMMARY、knowledge body、typed graph、Mind Map 與演化紀錄。", "- `VIA-MOD-005` 只做 Python AST 靜態分析；非 Python 或不完整片段必須標示 fallback/review。", "- `VIA-MOD-006` 套用 source/evidence/conflict/execution gates 並輸出 JSON／MD／HTML／ZIP。", "- `VIA-MOD-007` 提供離線 bounded runtime、canonical serialization、cache 與 dashboard snapshot。", "- 安全政策：`source_write=false`、`source_delete=false`、`code_execution=false`、`network=false`、`human_review_required=true`。", "", "## 3. Job 總表", "", "| Job ID | status | source | duration | units | topics | commands → merged | AST | source preserved |", "|---|---|---|---:|---:|---:|---:|---|---|"]
    for detail in details:
        job = detail["job"]
        metrics = detail["metrics"]
        gates = detail["gates"]
        ast_status = metrics.get("v8_ast_parse_status", detail["ast"].get("parse_status", "n/a"))
        lines.append("| " + " | ".join([
            f"`{job.get('job_id', 'n/a')}`",
            md_cell(job.get("status", "n/a")),
            md_cell(job.get("source_name", "n/a")),
            fmt_duration(job),
            str(metrics.get("units", detail.get("units", 0))),
            str(metrics.get("topics", detail.get("topics", 0))),
            f"{metrics.get('original_commands', 0)} → {metrics.get('merged_command_groups', 0)}",
            md_cell(ast_status),
            str(gates.get("source_preserved", "n/a")),
        ]) + " |")
    lines += ["", "## 4. 各 Job 詳細執行紀錄與輸出", ""]
    for index, detail in enumerate(details, 1):
        job = detail["job"]
        source = detail["source"]
        metrics = detail["metrics"]
        summary = detail["summary"]
        ast = detail["ast"]
        gates = detail["gates"]
        run = detail["run"]
        lines += [
            f"### 4.{index} `{job.get('job_id', 'n/a')}`",
            "",
            f"- Input：`{job.get('source_name', 'n/a')}`；mode=`{job.get('source_mode', 'n/a')}`；run directory=`{run.get('path')}`。",
            f"- Created／started／completed：`{fmt_time(job.get('created_at'))}`／`{fmt_time(job.get('started_at'))}`／`{fmt_time(job.get('completed_at'))}`。",
            f"- Source SHA-256：`{source.get('source_sha256', 'n/a')}`；bytes={source.get('byte_size', 'n/a')}；characters={source.get('extracted_characters', 'n/a')}。",
            f"- Engine IDs：`{', '.join(job.get('engine_ids', [])) or 'n/a'}`。",
            f"- Selected outputs：`{', '.join(job.get('output_formats', [])) or 'n/a'}`。",
            f"- Metrics：units={metrics.get('units', detail.get('units', 0))}、topics={metrics.get('topics', detail.get('topics', 0))}、original_commands={metrics.get('original_commands', 0)}、merged_groups={metrics.get('merged_command_groups', 0)}、deduplicated={metrics.get('deduplicated_command_candidates', 0)}、parameter_conflicts={metrics.get('parameter_conflicts', 0)}。",
            f"- Result：status=`{job.get('status', 'n/a')}`、error=`{job.get('error')}`、warnings=`{job.get('warnings')}`、source_preserved=`{gates.get('source_preserved')}`、review_required=`{gates.get('review_required')}`。",
            f"- Summary：title=`{summary.get('title', 'n/a')}`；key_points={len(summary.get('key_points', [])) if isinstance(summary.get('key_points'), list) else 'n/a'}。",
        ]
        if ast:
            lines.append(f"- AST：mode=`{ast.get('analysis_mode', 'n/a')}`、parse_status=`{ast.get('parse_status', 'n/a')}`、imports={len(ast.get('imports', [])) if isinstance(ast.get('imports'), list) else 'n/a'}、functions={len(ast.get('functions', [])) if isinstance(ast.get('functions'), list) else 'n/a'}、risk_flags=`{compact(ast.get('risk_flags', []))}`、execution_authorized=`{ast.get('execution_authorized', 'n/a')}`。")
        lines += ["- Local artifacts:", ""]
        for filename in run.get("files", []):
            size = run.get("file_sizes", {}).get(filename, "?")
            lines.append(f"  - `{filename}` ({size} bytes)")
        lines.append("")
    lines += ["## 5. Artifact 與 API 暴露狀態", "", "每個 job 的 `artifacts` mapping 只代表本次 output selector 選取的 API logical keys；run directory 可以保存更多診斷與相容投影。未選取的 logical key 可能在本地存在，但 API endpoint 回傳 404，不能直接判定為檔案遺失。", "", "| Job ID | downloads enabled | bundle | selected API artifacts | local run exists |", "|---|---|---|---|---|"]
    for detail in details:
        job = detail["job"]
        downloads = job.get("downloads") if isinstance(job.get("downloads"), dict) else {}
        lines.append(f"| `{job.get('job_id', 'n/a')}` | {downloads.get('enabled', 'n/a')} | `{downloads.get('bundle')}` | `{', '.join((job.get('artifacts') or {}).keys())}` | {detail['run'].get('exists')} |")
        if probe_artifacts and job.get("job_id"):
            selected = job.get("artifacts") if isinstance(job.get("artifacts"), dict) else {}
            if selected:
                probe_rows = [f"`{key}`={api_probe(base_url, job['job_id'], key)}" for key in selected]
                lines.append(f"  - API probe: {'; '.join(probe_rows)}")
    lines += ["", "## 6. 品質閘門、注意事項與限制", ""]
    for detail in details:
        job = detail["job"]
        gates = detail["gates"]
        lines.append(f"- `{job.get('job_id', 'n/a')}`：source_preserved={gates.get('source_preserved')}、source_mutated={gates.get('source_mutated')}、source_deleted={gates.get('source_deleted')}、coverage={gates.get('source_coverage')}、code_execution={gates.get('code_execution')}、network={gates.get('network')}、subprocess={gates.get('subprocess')}、review_required={gates.get('review_required')}。")
    for detail in details:
        ast = detail["ast"]
        if ast.get("risk_flags"):
            lines.append(f"- AST 注意：job `{detail['job'].get('job_id')}` 有 risk flags `{compact(ast.get('risk_flags'))}`；請視為 static fallback／人工複核，不要宣稱為成功 AST。")
    if errors:
        lines.append("- API 注意：" + "; ".join(errors))
    if not errors and not jobs:
        lines.append("- 目前沒有 API job；若本地也無 run directory，只能產出 catalog/status 層級報告。")
    lines += ["", "## 7. 來源與檢查時間", "", f"- SSOT：`{root / 'VIA_SSOT_Engine_Registry_v8.json'}`。", f"- Integration map：`{root / 'VIA_Consolidated_NLP_v8_Integration_Map.md'}`。", f"- Run roots：`{runs_dir}`。", f"- Report generated at：`{now}`。", ""]
    return "\n".join(lines)


def local_job_stubs(runs_dir: Path) -> list[dict[str, Any]]:
    """Create metadata-only job records when the API is unavailable."""
    stubs: list[dict[str, Any]] = []
    if not runs_dir.is_dir():
        return stubs
    for run_dir in sorted(p for p in runs_dir.iterdir() if p.is_dir()):
        record = load_json(run_dir / "record.json")
        if not isinstance(record, dict):
            continue
        source = record.get("source") if isinstance(record.get("source"), dict) else {}
        control = record.get("control_center") if isinstance(record.get("control_center"), dict) else {}
        via = record.get("_via_control") if isinstance(record.get("_via_control"), dict) else {}
        gates = record.get("quality_gates") if isinstance(record.get("quality_gates"), dict) else {}
        projections = record.get("projections") if isinstance(record.get("projections"), dict) else {}
        command = projections.get("command_reconstruction") if isinstance(projections.get("command_reconstruction"), dict) else {}
        merge = command.get("similarity_merge") if isinstance(command.get("similarity_merge"), dict) else {}
        output_formats = control.get("output_formats") or via.get("output_formats") or []
        artifacts = {key: filename for key, filename in OUTPUT_FILES.items() if (run_dir / filename).is_file()}
        stubs.append({
            "job_id": run_dir.name,
            "status": "local_only",
            "source_name": source.get("source_name", run_dir.name),
            "source_path": source.get("source_path", str(run_dir / "input")),
            "source_mode": "local_run_only",
            "engine_ids": control.get("engine_ids") or via.get("engine_ids") or ["VIA-ENG-022"],
            "output_formats": output_formats,
            "artifacts": artifacts,
            "downloads": {"enabled": False, "files": [], "bundle": None},
            "metrics": {
                "units": len(record.get("units", [])) if isinstance(record.get("units"), list) else 0,
                "original_commands": merge.get("original_command_count", 0),
                "merged_command_groups": merge.get("merged_command_count", 0),
                "deduplicated_command_candidates": merge.get("deduplicated_candidate_count", 0),
                "topics": len(projections.get("topic_reconstruction", {}).get("topics", [])) if isinstance(projections.get("topic_reconstruction"), dict) and isinstance(projections.get("topic_reconstruction", {}).get("topics"), list) else 0,
                "parameter_conflicts": len(projections.get("parameter_reconstruction", {}).get("conflicts", [])) if isinstance(projections.get("parameter_reconstruction"), dict) and isinstance(projections.get("parameter_reconstruction", {}).get("conflicts"), list) else 0,
                "v8_modules": 7,
                "v8_ast_parse_status": "local_only",
                "v8_source_preserved": gates.get("source_preserved"),
            },
            "error": None,
            "warnings": "API unavailable; local run metadata only",
        })
    return stubs


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only VIA AzureFlow v8 engine/job inspection")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--runs-dir", type=Path, default=None)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--no-artifact-probe", action="store_true")
    args = parser.parse_args()
    root = args.root.expanduser().resolve()
    runs_dir = (args.runs_dir or (root / "app" / "runs")).expanduser().resolve()
    payload: dict[str, Any] = {"api_errors": []}
    for name, endpoint in (("health", "/api/health"), ("catalog", "/api/catalog"), ("status", "/api/status"), ("jobs_payload", "/api/jobs"), ("dashboard", "/api/dashboard")):
        value, error = get_json(args.base_url, endpoint)
        payload["health" if name == "health" else "catalog" if name == "catalog" else "status" if name == "status" else "dashboard" if name == "dashboard" else name] = value
        if error:
            payload["api_errors"].append(error)
    jobs_payload = payload.get("jobs_payload") if isinstance(payload.get("jobs_payload"), dict) else {}
    jobs = jobs_payload.get("jobs", []) if isinstance(jobs_payload.get("jobs"), list) else []
    registry_map, registry = registry_engines(root)
    payload["registry"] = registry or {}
    payload["engines"] = merge_engines(payload.get("catalog"), registry_map)
    if not jobs:
        jobs = local_job_stubs(runs_dir)
    payload["jobs"] = jobs
    payload["details"] = [job_detail(job, runs_dir) for job in jobs if isinstance(job, dict)]
    report = render_report(args.base_url, root, runs_dir, payload, not args.no_artifact_probe)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(report, encoding="utf-8")
    else:
        sys.stdout.write(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
