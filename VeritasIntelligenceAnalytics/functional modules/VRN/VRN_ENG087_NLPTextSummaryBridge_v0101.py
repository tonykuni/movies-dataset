#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VRN_ENG087_NLPTextSummaryBridge v0100

VIA 中央唯一入口：
  1. 以 ENG072 擷取指定 PDF/DOCX 檔案夾首頁文字；
  2. 以 SUP_MDL744 NLPApplicationHub 對文字做 TextProcessor 正規化、切段、版面、表格、角色與證據型摘要；
  3. 以 ENG073 將同一批 sidecar 寫入指定 vrn_reports.duckdb；
  4. 建立 vrn_nlp_text_summary / vrn_pipeline_runs，保留可回溯文字、摘要、source hash 與狀態；
  5. 透過 VDF_ENG087 唯讀檢查 VDF 三清單狀態；
  6. 產生可供 VIA/VDF/VRN 接手的 JSON 證據。

本橋是離線檔案處理路徑；不自行開網路、不安裝套件、不使用已退役技術指標工具。
網路工具掛載只做存在性與雜湊盤點，VDF status 仍遵守 VIA 網路同意閘。
"""
from __future__ import annotations

import argparse
import hashlib
import html as html_lib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import duckdb
except Exception as exc:  # pragma: no cover - runtime gate prints the reason
    duckdb = None
    _DUCKDB_IMPORT_ERROR = f"{type(exc).__name__}: {exc}"
else:
    _DUCKDB_IMPORT_ERROR = ""

ENGINE_ID = "VRN_ENG087_NLPTextSummaryBridge"
VERSION = "v0100"
HERE = Path(__file__).resolve()
VIA = HERE.parents[2]
VRN_ROOT = VIA / "functional modules" / "VRN"
VDF_ROOT = VIA / "functional modules" / "VDF" / "engine"
NLP_ROOT = VIA / "supportive modules" / "70_VRN_Rules"
DEFAULT_DB = VRN_ROOT / "db" / "vrn_reports.duckdb"
DEFAULT_SIDECAR_DIR = VIA / "VIA_Reports" / "first_page_text"
DEFAULT_OUT = VIA / "VIA_Reports" / "vrn" / "nlp_pipeline"

# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋 =====
try:
    _sa_p = HERE
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
except Exception:
    VIA_ACCEL = None
# ===== [VIA:ACCEL-BRIDGE:END] =====

# ===== [VIA:NETWORK-MOUNT:v0100] Celeritas/Aegis 掛載盤點；本橋預設離線 =====
QUANTGUARD_ROOT = VIA / "functional modules" / "VDF" / "references" / "intake" / "VIA_QuantGuard_v20260916"
CELERITAS_MOUNT = QUANTGUARD_ROOT / "mounts" / "VeritasCeleritas.py"
AEGIS_MOUNT = QUANTGUARD_ROOT / "mounts" / "VeritasAegisNexus.py"
# ===== [VIA:NETWORK-MOUNT:END] =====


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def accelerator_status() -> str:
    return "VIA_SuperAccel_AVAILABLE" if VIA_ACCEL is not None else "VIA_SuperAccel_ABSENT_GRACEFUL"


def mount_status() -> dict[str, Any]:
    def digest(p: Path) -> str | None:
        return sha256_file(p) if p.is_file() else None
    return {
        "celeritas": {"path": str(CELERITAS_MOUNT), "sha256": digest(CELERITAS_MOUNT)},
        "aegis_nexus": {"path": str(AEGIS_MOUNT), "sha256": digest(AEGIS_MOUNT)},
        "network_gate": "OFF_BY_DEFAULT",
        "execution_mode": "OFFLINE_FILE_INPUT",
    }


def newest(pattern_root: Path, pattern: str) -> Path | None:
    files = sorted(pattern_root.glob(pattern))
    return files[-1] if files else None


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot create import spec: {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def load_nlp_hub() -> tuple[Any | None, dict[str, Any]]:
    path = newest(NLP_ROOT, "SUP_MDL744_NLPApplicationHub_v*.py")
    if path is None:
        return None, {"state": "ABSENT", "path": None, "why": "SUP_MDL744 NLP Hub not found"}
    try:
        mod = load_module(path, "via_sup_mdl744_nlp_hub")
        status = mod.status() if hasattr(mod, "status") else {}
        status.update({"state": "VERIFIED", "path": str(path), "sha256": sha256_file(path)})
        return mod, status
    except Exception as exc:
        return None, {"state": "FAILED", "path": str(path), "why": f"{type(exc).__name__}: {exc}"}


def supported_inputs(path: Path) -> list[Path]:
    allowed = {".pdf", ".docx", ".doc", ".png", ".jpg", ".jpeg", ".tif", ".tiff"}
    if path.is_file():
        return [path] if path.suffix.lower() in allowed else []
    if path.is_dir():
        return sorted(p for p in path.rglob("*") if p.is_file() and p.suffix.lower() in allowed)
    return []


def compose_text(payload: dict[str, Any]) -> str:
    """只取 sidecar 的可回溯文字，不把 OCR/表格缺席誤當成文字。"""
    parts: list[str] = []
    for key, label in (("header", "【標題帶】"), ("right", "【右資訊區】"), ("body", "【本文】")):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            parts.append(f"{label}\n{value.strip()}")
    if not parts:
        text_only = payload.get("text_only")
        if isinstance(text_only, str) and text_only.strip():
            parts.append(text_only.strip())
    if not parts:
        sentences = payload.get("sentences")
        if isinstance(sentences, list):
            parts.append("\n".join(str(x).strip() for x in sentences if str(x).strip()))
    return "\n\n".join(parts).strip()


def sidecar_for_input(source: Path) -> Path:
    return DEFAULT_SIDECAR_DIR / f"{source.stem}.json"


def prepare_sidecars(inputs: list[Path], stage: Path) -> tuple[list[Path], list[dict[str, Any]]]:
    stage.mkdir(parents=True, exist_ok=True)
    copied: list[Path] = []
    missing: list[dict[str, Any]] = []
    seen: set[str] = set()
    for source in inputs:
        expected = sidecar_for_input(source)
        if not expected.is_file():
            missing.append({"input": str(source), "sidecar": str(expected), "state": "ABSENT"})
            continue
        target_name = expected.name
        if target_name in seen:
            target_name = f"{source.parent.name}__{target_name}"
        target = stage / target_name
        shutil.copy2(expected, target)
        copied.append(target)
        seen.add(target_name)
    return copied, missing


def run_command(command: list[str], cwd: Path) -> dict[str, Any]:
    completed = subprocess.run(command, cwd=str(cwd), text=True, capture_output=True, check=False)
    return {
        "argv": [str(x) for x in command],
        "returncode": int(completed.returncode),
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def nlp_one(hub: Any, sidecar: Path, points: int) -> dict[str, Any]:
    payload = json.loads(sidecar.read_text(encoding="utf-8", errors="replace"))
    raw = compose_text(payload)
    normalized = hub.nfkc(raw) if raw else ""
    segments = hub.segments(normalized) if normalized else []
    tables = hub.tables(normalized) if normalized else []
    layout = hub.layout(normalized) if normalized else {}
    roles = hub.roles(normalized) if normalized else {}
    summary = hub.summarize(normalized, points) if normalized else {"state": "EMPTY", "points": []}
    processor = hub.text_processor()
    return {
        "report_file": sidecar.stem,
        "sidecar": str(sidecar),
        "source_sha256": sha256_file(sidecar),
        "raw_char_count": len(raw),
        "normalized_text": normalized,
        "normalized_sha256": hashlib.sha256(normalized.encode("utf-8")).hexdigest(),
        "normalized_char_count": len(normalized),
        "text_processor_state": "VERIFIED" if processor is not None else "ABSENT",
        "summary": summary,
        "segment_count": len(segments),
        "table_count": len(tables),
        "layout_block_count": len(layout.get("blocks", [])) if isinstance(layout, dict) else 0,
        "role_count": len(roles.get("records", [])) if isinstance(roles, dict) else 0,
        "roles_why": hub.roles_why() if hasattr(hub, "roles_why") else "",
        "logic": payload.get("logic", {}),
        "tag": payload.get("tag", ""),
    }


def ensure_tables(con: Any) -> None:
    con.execute("""
        CREATE TABLE IF NOT EXISTS vrn_nlp_text_summary (
            report_file VARCHAR PRIMARY KEY,
            source_sha256 VARCHAR,
            normalized_text VARCHAR,
            normalized_sha256 VARCHAR,
            raw_char_count BIGINT,
            normalized_char_count BIGINT,
            text_processor_state VARCHAR,
            summary_state VARCHAR,
            summary_points_json VARCHAR,
            evidence_spans_valid BOOLEAN,
            segment_count BIGINT,
            table_count BIGINT,
            layout_block_count BIGINT,
            role_count BIGINT,
            roles_why VARCHAR,
            extraction_tag VARCHAR,
            logic_json VARCHAR,
            generated_at TIMESTAMP
        )
    """)
    con.execute("""
        CREATE TABLE IF NOT EXISTS vrn_pipeline_runs (
            run_id VARCHAR PRIMARY KEY,
            input_path VARCHAR,
            input_count BIGINT,
            sidecar_count BIGINT,
            summary_ok_count BIGINT,
            eng072_rc INTEGER,
            eng073_rc INTEGER,
            vdf_rc INTEGER,
            verdict VARCHAR,
            db_path VARCHAR,
            output_dir VARCHAR,
            started_at TIMESTAMP,
            finished_at TIMESTAMP,
            accelerator VARCHAR,
            network_mode VARCHAR
        )
    """)


def write_nlp_rows(db_path: Path, rows: list[dict[str, Any]]) -> None:
    if duckdb is None:
        raise RuntimeError(f"duckdb unavailable: {_DUCKDB_IMPORT_ERROR}")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(db_path))
    try:
        ensure_tables(con)
        for row in rows:
            sm = row.get("summary") or {}
            con.execute("DELETE FROM vrn_nlp_text_summary WHERE report_file = ?", [row["report_file"]])
            con.execute("""
                INSERT INTO vrn_nlp_text_summary VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                row["report_file"], row["source_sha256"], row["normalized_text"], row["normalized_sha256"],
                row["raw_char_count"], row["normalized_char_count"], row["text_processor_state"],
                sm.get("state", "UNKNOWN"), json.dumps(sm.get("points", []), ensure_ascii=False),
                sm.get("evidence_spans_valid"), row["segment_count"], row["table_count"],
                row["layout_block_count"], row["role_count"], row["roles_why"], row["tag"],
                json.dumps(row["logic"], ensure_ascii=False), datetime.now(timezone.utc),
            ])
    finally:
        con.close()


def write_run_row(db_path: Path, record: dict[str, Any]) -> None:
    if duckdb is None:
        raise RuntimeError(f"duckdb unavailable: {_DUCKDB_IMPORT_ERROR}")
    con = duckdb.connect(str(db_path))
    try:
        ensure_tables(con)
        con.execute("DELETE FROM vrn_pipeline_runs WHERE run_id = ?", [record["run_id"]])
        con.execute("""
            INSERT INTO vrn_pipeline_runs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            record["run_id"], record["input_path"], record["input_count"], record["sidecar_count"],
            record["summary_ok_count"], record["eng072_rc"], record["eng073_rc"], record["vdf_rc"],
            record["verdict"], record["db_path"], record["output_dir"], record["started_at"],
            record["finished_at"], record["accelerator"], record["network_mode"],
        ])
    finally:
        con.close()


def verify_db(db_path: Path) -> dict[str, Any]:
    if duckdb is None or not db_path.is_file():
        return {"state": "ABSENT", "path": str(db_path), "why": _DUCKDB_IMPORT_ERROR or "database absent"}
    con = duckdb.connect(str(db_path), read_only=True)
    try:
        tables = [r[0] for r in con.execute("SHOW TABLES").fetchall()]
        counts = {}
        for table in ("vrn_report_basic", "vrn_report_metrics", "vrn_report_analyst", "vrn_nlp_text_summary", "vrn_pipeline_runs"):
            counts[table] = con.execute(f"SELECT count(*) FROM {table}").fetchone()[0] if table in tables else None
        return {"state": "GREEN" if "vrn_nlp_text_summary" in tables else "YELLOW", "path": str(db_path), "tables": tables, "counts": counts}
    finally:
        con.close()


def _gate_rows(result: dict[str, Any]) -> list[dict[str, Any]]:
    engines = result.get("engines", {})
    nlp = result.get("nlp", {})
    db = result.get("database", {})
    vdf_gate = result.get("vdf_gate", {})
    return [
        {"order": 1, "stage": "輸入樣本", "component": "PDF/DOCX/Image intake", "expected": ">=1 個可支援檔案", "actual": f"{result.get('input_count', 0)} 個", "state": "PASS" if result.get("input_count", 0) else "BLOCKED", "evidence": "; ".join(result.get("input_paths", []))},
        {"order": 2, "stage": "首頁擷取", "component": "VRN ENG072", "expected": "returncode=0；sidecar 齊全", "actual": f"rc={engines.get('eng072', {}).get('returncode')}; sidecar={result.get('sidecar_count', 0)}", "state": "PASS" if engines.get("eng072", {}).get("returncode") == 0 and not result.get("missing_sidecars") else "BLOCKED", "evidence": result.get("output_dir", "") + "/eng072.stdout.txt"},
        {"order": 3, "stage": "NLP 文字與摘要", "component": "SUP_MDL744 NLPApplicationHub", "expected": "Hub VERIFIED；摘要可回溯", "actual": f"processed={nlp.get('processed', 0)}; summary_ok={nlp.get('summary_ok', 0)}", "state": "PASS" if nlp.get("processed", 0) and not nlp.get("errors") else "BLOCKED", "evidence": "vrn_nlp_text_summary.summary_points_json + normalized_text"},
        {"order": 4, "stage": "VRN 結構化入庫", "component": "VRN ENG073", "expected": "returncode=0；DB 可讀", "actual": f"rc={engines.get('eng073', {}).get('returncode')}; DB={db.get('state')}", "state": "PASS" if engines.get("eng073", {}).get("returncode") == 0 and db.get("state") == "GREEN" else "BLOCKED", "evidence": engines.get("eng073", {}).get("argv", [])},
        {"order": 5, "stage": "資料庫驗證", "component": "vrn_reports.duckdb", "expected": "NLP 表與 pipeline runs 在位", "actual": json.dumps(db.get("counts", {}), ensure_ascii=False), "state": "PASS" if db.get("state") == "GREEN" and db.get("counts", {}).get("vrn_nlp_text_summary", 0) is not None else "BLOCKED", "evidence": result.get("database_path", "")},
        {"order": 6, "stage": "VDF 中央狀態", "component": "VDF ENG087 / MARKET_LISTS", "expected": "三清單 GREEN", "actual": vdf_gate.get("verdict", "UNKNOWN"), "state": "PASS" if vdf_gate.get("verdict") == "GREEN" and engines.get("vdf087", {}).get("returncode") == 0 else "BLOCKED", "evidence": vdf_gate.get("report", "")},
    ]


def _render_matrix_html(result: dict[str, Any]) -> str:
    esc = lambda value: html_lib.escape(str(value if value is not None else ""))
    gates = _gate_rows(result)
    engines = result.get("engines", {})
    verdict = esc(result.get("verdict"))
    rows = "\n".join(
        f"<tr><td>{g['order']}</td><td>{esc(g['stage'])}</td><td>{esc(g['component'])}</td>"
        f"<td>{esc(g['expected'])}</td><td>{esc(g['actual'])}</td>"
        f"<td class='{g['state'].lower()}'><strong>{g['state']}</strong></td><td><code>{esc(g['evidence'])}</code></td></tr>"
        for g in gates
    )
    detail_rows = []
    for index, item in enumerate(result.get("rows", []), 1):
        summary = item.get("summary") or {}
        points = "<br>".join(esc(p.get("text", "")) for p in summary.get("points", [])) or "(無摘要點)"
        detail_rows.append(
            f"<tr><td>{index}</td><td>{esc(item.get('report_file'))}</td><td>{item.get('normalized_char_count', 0)}</td>"
            f"<td>{esc(item.get('text_processor_state'))}</td><td>{esc(summary.get('state'))}</td>"
            f"<td>{summary.get('evidence_spans_valid')}</td><td>{points}</td></tr>"
        )
    details = "\n".join(detail_rows) or "<tr><td colspan='7'>沒有可顯示的逐件結果</td></tr>"
    blockers = result.get("vdf_gate", {}).get("blockers", [])
    blocker_html = "<ul>" + "".join(f"<li>{esc(b)}</li>" if isinstance(b, str) else f"<li><b>{esc(b.get('list'))}</b>：{esc(b.get('why'))}</li>" for b in blockers) + "</ul>" if blockers else "<p>無 VDF 阻擋。</p>"
    return f"""<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8"><title>VIA NLP→VRN→VDF 矩陣報告</title>
<style>
body{{font-family:Arial,'Noto Sans TC',sans-serif;background:#f4f1eb;color:#202322;margin:0}}
.page{{width:1120px;min-height:720px;margin:24px auto;padding:38px 46px;background:#fffdf9;box-sizing:border-box;page-break-after:always;box-shadow:0 2px 10px #0001}}
h1{{font-size:30px;margin:0 0 12px;color:#163b42}} h2{{color:#24636c;margin-top:24px}}
.hero{{border-left:8px solid #2f8f83;padding:18px 22px;background:#e9f4ef;margin:18px 0}}
.verdict{{font-size:34px;font-weight:800;color:{'#1f7a57' if result.get('verdict') == 'GREEN' else '#a45a16'}}}
.meta{{color:#65706c;font-size:13px;line-height:1.7}} table{{border-collapse:collapse;width:100%;font-size:13px}}
th{{background:#244e58;color:white;text-align:left;padding:9px}} td{{border-bottom:1px solid #ddd4c7;padding:8px;vertical-align:top}}
tr:nth-child(even){{background:#fbf8f2}} .pass{{color:#13734e;background:#e8f5ed}} .blocked{{color:#9b4b1d;background:#fff0df}}
code{{white-space:pre-wrap;word-break:break-word}} .small{{font-size:12px;color:#5d6864}}
.nav{{position:fixed;right:24px;top:12px;font-size:12px}} a{{color:#176c76;margin-left:10px}}
</style></head><body>
<div class="nav"><a href="#p1">第1頁</a><a href="#p2">第2頁</a><a href="#p3">第3頁</a></div>
<section class="page" id="p1"><h1>第 1 頁｜VIA NLP → VRN → VDF 實測矩陣報告</h1>
<div class="hero"><div class="verdict">{verdict}</div><div>VRN_ENG087_NLPTextSummaryBridge {esc(result.get('version'))}</div></div>
<p class="meta">Run ID：{esc(result.get('run_id'))}<br>開始：{esc(result.get('started_at'))}<br>完成：{esc(result.get('finished_at'))}<br>輸入：{result.get('input_count',0)} 件；sidecar：{result.get('sidecar_count',0)} 件；NLP：{result.get('nlp',{}).get('processed',0)} 件；摘要通過：{result.get('nlp',{}).get('summary_ok',0)} 件<br>資料庫：<code>{esc(result.get('database_path'))}</code></p>
<h2>總覽裁決</h2><table><tr><th>站點</th><th>實測值</th><th>狀態</th></tr>
<tr><td>ENG072 首頁擷取</td><td>rc={engines.get('eng072',{}).get('returncode')}; sidecar={result.get('sidecar_count',0)}</td><td>{'PASS' if gates[1]['state']=='PASS' else 'BLOCKED'}</td></tr>
<tr><td>NLP 文字修復／證據摘要</td><td>{result.get('nlp',{}).get('processed',0)}/{result.get('input_count',0)}；evidence span</td><td>{'PASS' if gates[2]['state']=='PASS' else 'BLOCKED'}</td></tr>
<tr><td>ENG073／DuckDB</td><td>{esc(result.get('database',{}).get('counts'))}</td><td>{'PASS' if gates[3]['state']=='PASS' and gates[4]['state']=='PASS' else 'BLOCKED'}</td></tr>
<tr><td>VDF 三清單</td><td>{esc(result.get('vdf_gate',{}).get('verdict'))}</td><td>{'PASS' if gates[5]['state']=='PASS' else 'BLOCKED'}</td></tr></table>
<p class="small">此頁是給操作員與下一位 AI 的裁決摘要；詳細逐站證據見第 2、3 頁及同批 JSON/Markdown。</p></section>
<section class="page" id="p2"><h1>第 2 頁｜完整測試矩陣</h1><p class="small">每一列都有 expected、actual、state 與 evidence；BLOCKED 不轉成 PASS。</p>
<table><tr><th>序</th><th>階段</th><th>元件</th><th>預期</th><th>實際</th><th>結果</th><th>證據</th></tr>{rows}</table>
<h2>VDF 阻擋原因</h2>{blocker_html}<p class="small">VDF 結果檔：<code>{esc(result.get('vdf_gate',{}).get('report'))}</code></p></section>
<section class="page" id="p3"><h1>第 3 頁｜逐件依序結果</h1><p class="small">順序：輸入 → ENG072 → NLP 正規化／摘要 → ENG073 → DuckDB → VDF。</p>
<table><tr><th>序</th><th>報告 sidecar</th><th>正規化字數</th><th>TextProcessor</th><th>摘要</th><th>span 可回溯</th><th>證據型摘要點</th></tr>{details}</table>
<h2>可重跑與 AI 轉換檔</h2><ul><li>JSON：<code>NLP_VRN_VDF_RESULT.json</code>，機器裁決正本。</li><li>Markdown：<code>NLP_VRN_VDF_RESULT.md</code>，方便 AI 低額度接手。</li><li>DuckDB：<code>vrn_nlp_text_summary</code> 保存 normalized_text、source hash、summary_points_json。</li></ul>
<p class="small">加速器：{esc(result.get('accelerator'))}；執行模式：{esc(result.get('network_mode'))}；網路閘：{esc(result.get('tool_mounts',{}).get('network_gate'))}</p></section>
</body></html>"""


def _render_report_markdown(result: dict[str, Any]) -> str:
    gates = _gate_rows(result)
    lines = [
        f"# VIA NLP → VRN → VDF 實測矩陣報告（{result.get('verdict')}）",
        "", f"- **Run ID：** `{result.get('run_id')}`", f"- **輸入：** {result.get('input_count', 0)} 件；sidecar {result.get('sidecar_count', 0)} 件",
        f"- **NLP：** {result.get('nlp', {}).get('processed', 0)} 件；摘要通過 {result.get('nlp', {}).get('summary_ok', 0)} 件",
        f"- **DuckDB：** `{result.get('database_path')}`", "", "## 第 2 頁｜完整測試矩陣", "", "|序|階段|元件|預期|實際|結果|", "|---:|---|---|---|---|---|",
    ]
    lines += [f"|{g['order']}|{g['stage']}|{g['component']}|{g['expected']}|{g['actual']}|**{g['state']}**|" for g in gates]
    lines += ["", "## VDF 阻擋原因", ""]
    blockers = result.get("vdf_gate", {}).get("blockers", [])
    blocker_lines = []
    for blocker in blockers:
        if isinstance(blocker, str):
            blocker_lines.append(f"- {blocker}")
        else:
            blocker_lines.append(f"- {blocker.get('list')}：{blocker.get('why')}")
    lines += blocker_lines or ["- 無 VDF 阻擋。"]
    lines += ["", "## 第 3 頁｜逐件依序結果", "", "|序|報告|正規化字數|TextProcessor|摘要|span|摘要點|", "|---:|---|---:|---|---|---|---|"]
    for i, item in enumerate(result.get("rows", []), 1):
        sm = item.get("summary") or {}
        points = " / ".join(str(p.get("text", "")).replace("|", "\\|") for p in sm.get("points", []))
        lines.append(f"|{i}|{item.get('report_file')}|{item.get('normalized_char_count', 0)}|{item.get('text_processor_state')}|{sm.get('state')}|{sm.get('evidence_spans_valid')}|{points}|")
    lines += ["", "## AI 接手提示", "", "JSON 是機器裁決正本；HTML 是三頁矩陣；DuckDB `vrn_nlp_text_summary` 是文字與證據摘要資料表。VDF 若非 GREEN，必須讀 `vdf_gate.blockers`，不得把整批標成 GREEN。", ""]
    return "\n".join(lines)


def write_report_artifacts(result: dict[str, Any], run_dir: Path, out_dir: Path) -> None:
    html_path = run_dir / "NLP_VRN_VDF_MATRIX.html"
    md_path = run_dir / "NLP_VRN_VDF_RESULT.md"
    json_path = run_dir / "NLP_VRN_VDF_RESULT.json"
    result["report_artifacts"] = {
        "html": str(html_path), "markdown": str(md_path), "json": str(json_path),
        "pages": ["overview", "test_matrix", "sequential_results"],
    }
    html_path.write_text(_render_matrix_html(result), encoding="utf-8")
    md_path.write_text(_render_report_markdown(result), encoding="utf-8")
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
    (out_dir / "NLP_VRN_VDF_latest.html").write_text(_render_matrix_html(result), encoding="utf-8")
    (out_dir / "NLP_VRN_VDF_latest.md").write_text(_render_report_markdown(result), encoding="utf-8")
    (out_dir / "NLP_VRN_VDF_latest.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")


def run_pipeline(input_paths: list[Path], db_path: Path, out_dir: Path, points: int = 5, force: bool = False) -> tuple[int, dict[str, Any]]:
    started = now_iso()
    run_id = "B529-" + datetime.now().strftime("%Y%m%dT%H%M%S") + "-" + uuid.uuid4().hex[:8]
    out_dir.mkdir(parents=True, exist_ok=True)
    run_dir = out_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    inputs: list[Path] = []
    for path in input_paths:
        inputs.extend(supported_inputs(path))
    # deterministic de-duplication by resolved path
    uniq: list[Path] = []
    seen: set[str] = set()
    for p in inputs:
        key = str(p.resolve())
        if key not in seen:
            seen.add(key)
            uniq.append(p)
    inputs = uniq
    if not inputs:
        payload = {"schema": "VIA.VRN.NLP.VDF.Pipeline.v1", "run_id": run_id, "verdict": "BLOCKED", "why": "no supported PDF/DOCX/image input", "inputs": [str(p) for p in input_paths]}
        (out_dir / "NLP_VRN_VDF_latest.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return 2, payload

    eng072 = newest(VRN_ROOT, "VRN_ENG072_FirstPageText_v*.py")
    eng073 = newest(VRN_ROOT, "VRN_ENG073_ReportStructuredDB_v*.py")
    vdf087 = newest(VDF_ROOT, "VDF_ENG087_MarketListGovernance_v*.py")
    if eng072 is None or eng073 is None:
        raise FileNotFoundError("ENG072/ENG073 tail engines are required")

    cmd072 = [sys.executable, str(eng072), "run"]
    for p in input_paths:
        cmd072 += ["--in", str(p)]
    if force:
        cmd072.append("--force")
    eng072_result = run_command(cmd072, VIA)
    (run_dir / "eng072.stdout.txt").write_text(eng072_result["stdout"], encoding="utf-8", errors="replace")
    (run_dir / "eng072.stderr.txt").write_text(eng072_result["stderr"], encoding="utf-8", errors="replace")

    stage = run_dir / "sidecars"
    staged, missing = prepare_sidecars(inputs, stage)
    cmd073 = [sys.executable, str(eng073), "run", "--dir", str(stage), "--db", str(db_path)]
    eng073_result = run_command(cmd073, VIA)
    (run_dir / "eng073.stdout.txt").write_text(eng073_result["stdout"], encoding="utf-8", errors="replace")
    (run_dir / "eng073.stderr.txt").write_text(eng073_result["stderr"], encoding="utf-8", errors="replace")

    hub, hub_status = load_nlp_hub()
    rows: list[dict[str, Any]] = []
    nlp_errors: list[dict[str, Any]] = []
    if hub is not None:
        for sidecar in staged:
            try:
                rows.append(nlp_one(hub, sidecar, points))
            except Exception as exc:
                nlp_errors.append({"sidecar": str(sidecar), "state": "FAILED", "why": f"{type(exc).__name__}: {exc}"})
    else:
        nlp_errors.append({"state": hub_status.get("state"), "why": hub_status.get("why", "NLP Hub unavailable")})

    if rows:
        write_nlp_rows(db_path, rows)
    db_status = verify_db(db_path)

    vdf_result = {"returncode": 2, "stdout": "", "stderr": "VDF engine absent"}
    if vdf087 is not None:
        vdf_result = run_command([sys.executable, str(vdf087)], VIA)
        (run_dir / "vdf087.stdout.txt").write_text(vdf_result["stdout"], encoding="utf-8", errors="replace")
        (run_dir / "vdf087.stderr.txt").write_text(vdf_result["stderr"], encoding="utf-8", errors="replace")
    vdf_report = VIA / "VIA_Reports" / "vdf" / "central_lists" / "MARKET_LISTS_latest.json"
    vdf_gate: dict[str, Any] = {"verdict": "ABSENT", "report": str(vdf_report), "blockers": []}
    if vdf_report.is_file():
        try:
            vdf_payload = json.loads(vdf_report.read_text(encoding="utf-8"))
            blockers = []
            for key, item in (vdf_payload.get("lists") or {}).items():
                if item.get("state") != "GREEN":
                    blockers.append({"list": key, "state": item.get("state"), "why": item.get("why", "")})
            vdf_gate = {"verdict": vdf_payload.get("verdict", "UNKNOWN"), "report": str(vdf_report), "blockers": blockers}
        except Exception as exc:
            vdf_gate = {"verdict": "FAILED", "report": str(vdf_report), "blockers": [f"{type(exc).__name__}: {exc}"]}
    vdf_green = vdf_result["returncode"] == 0 and vdf_gate.get("verdict") == "GREEN"
    summary_ok = sum(1 for x in rows if (x.get("summary") or {}).get("state") in ("OK", "EMPTY"))
    finished = now_iso()
    # Write the run row before reading final counts, so the machine result proves the run was recorded.
    write_run_row(db_path, {
        "run_id": run_id, "input_path": ";".join(str(p) for p in input_paths), "input_count": len(inputs),
        "sidecar_count": len(staged), "summary_ok_count": summary_ok,
        "eng072_rc": eng072_result["returncode"], "eng073_rc": eng073_result["returncode"],
        "vdf_rc": vdf_result["returncode"], "verdict": "GREEN" if (
            eng072_result["returncode"] == 0 and eng073_result["returncode"] == 0 and
            bool(staged) and not missing and not nlp_errors and db_status.get("state") == "GREEN" and vdf_green
        ) else "YELLOW", "db_path": str(db_path),
        "output_dir": str(run_dir), "started_at": started, "finished_at": finished,
        "accelerator": accelerator_status(), "network_mode": "OFFLINE_FILE_INPUT",
    })
    db_status = verify_db(db_path)
    verdict = "GREEN" if (
        eng072_result["returncode"] == 0 and eng073_result["returncode"] == 0 and
        bool(staged) and not missing and not nlp_errors and db_status.get("state") == "GREEN" and
        vdf_green
    ) else "YELLOW"
    result = {
        "schema": "VIA.VRN.NLP.VDF.Pipeline.v1",
        "engine": ENGINE_ID,
        "version": VERSION,
        "run_id": run_id,
        "verdict": verdict,
        "input_paths": [str(p) for p in input_paths],
        "input_count": len(inputs),
        "inputs": [str(p) for p in inputs],
        "sidecar_count": len(staged),
        "missing_sidecars": missing,
        "engines": {"eng072": eng072_result, "eng073": eng073_result, "vdf087": vdf_result},
        "nlp": {"hub": hub_status, "processed": len(rows), "summary_ok": summary_ok, "errors": nlp_errors},
        "vdf_gate": vdf_gate,
        "database": db_status,
        "accelerator": accelerator_status(),
        "tool_mounts": mount_status(),
        "network_mode": "OFFLINE_FILE_INPUT",
        "started_at": started,
        "finished_at": finished,
        "output_dir": str(run_dir),
        "database_path": str(db_path),
        "rows": [{k: v for k, v in r.items() if k != "normalized_text"} for r in rows],
        "policy": "文字與摘要均保留 source hash/evidence span；缺席或失敗不假綠；ENG073 canonical 欄位不被 NLP 覆寫",
    }
    write_report_artifacts(result, run_dir, out_dir)
    print(json.dumps({"engine": ENGINE_ID, "run_id": run_id, "verdict": verdict, "input_count": len(inputs), "sidecars": len(staged), "nlp_processed": len(rows), "summary_ok": summary_ok, "db": db_status, "vdf_green": vdf_green, "output": str(run_dir)}, ensure_ascii=False, indent=2, default=str))
    return 0 if verdict == "GREEN" else 2, result


def status() -> int:
    path = DEFAULT_OUT / "NLP_VRN_VDF_latest.json"
    if not path.is_file():
        print(f"[VRN_ENG087] ABSENT · {path}")
        return 2
    payload = json.loads(path.read_text(encoding="utf-8"))
    print(f"[VRN_ENG087] {payload.get('verdict')} · run={payload.get('run_id')} · inputs={payload.get('input_count')} · sidecars={payload.get('sidecar_count')} · NLP={payload.get('nlp', {}).get('processed')} · DB={payload.get('database', {}).get('state')}")
    print(f"  output={payload.get('output_dir')}\n  db={payload.get('database_path')}")
    return 0 if payload.get("verdict") == "GREEN" else 2


def selftest() -> int:
    failures: list[str] = []
    checks: list[tuple[str, bool, str]] = []
    hub, hs = load_nlp_hub()
    checks.append(("NLP Hub mount", hub is not None and hs.get("state") == "VERIFIED", hs.get("why", hs.get("mount", {}).get("state", ""))))
    services = set(hs.get("report_services", []))
    checks.append(("六項研報 NLP 服務在位", {"table_ops", "layout_analysis", "content_roles", "context_reconstruction", "summarization", "function_classifier"}.issubset(services), f"{len(services)}/6"))
    text = "台積電 2330 買進，需求強勁。風險為匯率波動。"
    if hub is not None:
        normalized = hub.nfkc(text)
        summary = hub.summarize(normalized, 3)
        checks.append(("TextProcessor 正規化", normalized == "台積電 2330 買進, 需求強勁。風險為匯率波動。", normalized[:30]))
        checks.append(("證據型摘要", summary.get("state") in ("OK", "EMPTY", "ABSENT"), summary.get("state", "")))
        checks.append(("摘要 span 可回溯", summary.get("state") != "OK" or all(isinstance(p.get("source_span"), dict) for p in summary.get("points", [])), "source_span"))
    else:
        checks.extend([("TextProcessor 正規化", False, "NLP Hub absent"), ("證據型摘要", False, "NLP Hub absent"), ("摘要 span 可回溯", False, "NLP Hub absent")])
    checks.append(("DuckDB 套件在位", duckdb is not None, _DUCKDB_IMPORT_ERROR))
    checks.append(("ENG072 正主在位", newest(VRN_ROOT, "VRN_ENG072_FirstPageText_v*.py") is not None, ""))
    checks.append(("ENG073 v0127 正主在位", newest(VRN_ROOT, "VRN_ENG073_ReportStructuredDB_v0127.py") is not None, ""))
    checks.append(("VDF ENG087 正主在位", newest(VDF_ROOT, "VDF_ENG087_MarketListGovernance_v*.py") is not None, ""))
    checks.append(("網路預設關閉", mount_status().get("network_gate") == "OFF_BY_DEFAULT", ""))
    checks.append(("加速器橋已宣告", "VIA_SuperAccel" in accelerator_status(), accelerator_status()))
    for name, ok, note in checks:
        print(f"  [{'OK' if ok else 'FAIL'}] {name} {note}")
        if not ok:
            failures.append(name)
    print(f"  [計] 十一檢 OK {len(checks) - len(failures)} · FAIL {len(failures)}")
    return 1 if failures else 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="VIA NLP→VRN→VDF offline bridge")
    sub = parser.add_subparsers(dest="verb")
    run = sub.add_parser("run")
    run.add_argument("--in", dest="inputs", action="append", required=True)
    run.add_argument("--db", default=str(DEFAULT_DB))
    run.add_argument("--out", default=str(DEFAULT_OUT))
    run.add_argument("--points", type=int, default=5)
    run.add_argument("--force", action="store_true")
    sub.add_parser("status")
    sub.add_parser("selftest")
    return parser.parse_args(_normalise_argv_b534(sys.argv[1:]))   # 批534:旗標=位置動詞(L39)



# ===== 批534:VIA 全樹以 `--selftest` 呼叫自測(格子站/匯流排/Deck/總控頁);本引擎原只認位置動詞。=====
# 等價轉換,只增不減:旗標 → 位置動詞(L39 U/I 對接契約律;一個功能一種呼叫法)。
_FLAG_VERBS_B534 = {"--selftest": "selftest", "--status": "status", "--manifest": "manifest", "--routes": "routes"}


def _normalise_argv_b534(argv):
    out, verb = [], None
    for a in argv:
        if a in _FLAG_VERBS_B534 and verb is None:
            verb = _FLAG_VERBS_B534[a]
        else:
            out.append(a)
    return ([verb] + out) if verb else out

def main() -> int:
    args = parse_args()
    if args.verb in (None, "status"):
        return status()
    if args.verb == "selftest":
        return selftest()
    paths = [Path(x) for x in args.inputs]
    rc, _ = run_pipeline(paths, Path(args.db), Path(args.out), max(1, args.points), args.force)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
