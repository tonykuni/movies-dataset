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
import ast
import csv
import hashlib
import html
import json
import os
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple


DANGER_PATTERNS = [
    "Remove-Item", "Stop-Process", "Invoke-Expression", "iex", "Start-Process",
    "Set-ExecutionPolicy", "New-Item", "Set-Content", "Add-Content", "Out-File",
    "Move-Item", "Copy-Item", "Invoke-WebRequest", "Invoke-RestMethod",
    "Start-Job", "Start-ThreadJob", "schtasks", "reg add", "rm -rf", "del /f"
]

SECRET_PATTERNS = [
    "api_key", "apikey", "secret", "token", "password", "passwd",
    "credential", "bearer", "authorization", "client_secret", "access_key"
]


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


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def prop(row: Dict[str, Any], key: str, default: str = "") -> str:
    v = row.get(key, default)
    return "" if v is None else str(v)


def h(value: Any) -> str:
    return html.escape("" if value is None else str(value))


def sha256_file(path: Path, max_bytes: int = 8 * 1024 * 1024) -> str:
    try:
        size = path.stat().st_size
        if size > max_bytes:
            return "SKIPPED_LARGE_FILE"
        m = hashlib.sha256()
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(1024 * 512), b""):
                m.update(chunk)
        return m.hexdigest()
    except Exception as e:
        return f"HASH_ERROR:{type(e).__name__}"


def looks_binary(path: Path) -> bool:
    try:
        with path.open("rb") as f:
            chunk = f.read(4096)
        return b"\x00" in chunk
    except Exception:
        return False


def mask_secret_line(line: str) -> str:
    s = line.rstrip("\n\r")

    # Python 3.13 safe regex:
    # Do NOT embed (?i) inside a nested group.
    # Use re.IGNORECASE flags instead.
    secret_key = r"(api[_-]?key|apikey|secret|token|password|passwd|credential|client[_-]?secret|access[_-]?key|authorization)"

    assign_pat = re.compile(
        r"(" + secret_key + r"\s*[:=]\s*)(['\"]?)[^,'\"\s\]]+(['\"]?)",
        flags=re.IGNORECASE
    )
    s = assign_pat.sub(r"\1\2***MASKED***\3", s)

    # Mask Bearer tokens safely without inline global flag in the middle.
    s = re.sub(
        r"(bearer\s+)[A-Za-z0-9_\-\.=]{12,}",
        r"\1***MASKED***",
        s,
        flags=re.IGNORECASE
    )

    # Mask long suspicious token-like strings.
    # Keep this conservative enough for reports; exact source is not changed.
    s = re.sub(r"([A-Za-z0-9_\-]{32,})", "***LONG_TOKEN_MASKED***", s)

    return s
def is_comment_or_doc_line(line: str, ext: str) -> bool:
    x = line.strip()
    if not x:
        return False
    if ext in {".ps1", ".psm1"}:
        return x.startswith("#") or x.startswith("<#") or x.startswith("#>")
    if ext in {".py"}:
        return x.startswith("#") or x.startswith('"""') or x.startswith("'''") or x.endswith('"""') or x.endswith("'''")
    if ext in {".js", ".ts", ".html", ".css"}:
        return x.startswith("//") or x.startswith("/*") or x.startswith("*") or x.startswith("<!--")
    return False


def marker_hits(line: str) -> Tuple[List[str], List[str]]:
    low = line.lower()
    secret_hits = [p for p in SECRET_PATTERNS if p.lower() in low]
    danger_hits = [p for p in DANGER_PATTERNS if p.lower() in low]
    return secret_hits, danger_hits


def read_text_lines(path: Path, max_file_bytes: int) -> Tuple[str, List[str]]:
    try:
        if not path.exists():
            return "FILE_MISSING", []
        size = path.stat().st_size
        if size > max_file_bytes:
            return "LARGE_FILE_SKIPPED", []
        if looks_binary(path):
            return "BINARY_FILE_SKIPPED", []
        raw = path.read_text(encoding="utf-8", errors="replace")
        return "READ_OK", raw.splitlines()
    except Exception as e:
        return f"READ_ERROR:{type(e).__name__}", []


def choose_context(lines: List[str], ext: str, context_lines: int) -> List[Dict[str, Any]]:
    hits = []
    for i, line in enumerate(lines):
        secret_hits, danger_hits = marker_hits(line)
        if secret_hits or danger_hits:
            start = max(0, i - context_lines)
            end = min(len(lines), i + context_lines + 1)
            snippet_lines = []
            for j in range(start, end):
                raw_line = lines[j]
                snippet_lines.append(f"{j+1}: {mask_secret_line(raw_line)}")
            hits.append({
                "def_hit_line": str(i + 1),
                "def_secret_hits": ";".join(secret_hits),
                "def_danger_hits": ";".join(danger_hits),
                "def_hit_is_comment_or_doc": str(is_comment_or_doc_line(line, ext)).lower(),
                "def_masked_context": "\n".join(snippet_lines)
            })
    return hits[:12]


def ast_status(path: Path, ext: str, lines: List[str]) -> str:
    if ext != ".py":
        return "NOT_PYTHON"
    try:
        ast.parse("\n".join(lines), filename=str(path))
        return "AST_OK"
    except SyntaxError as e:
        return f"AST_SYNTAX_ERROR_LINE_{getattr(e, 'lineno', '')}"
    except Exception as e:
        return f"AST_ERROR:{type(e).__name__}"


def classify_context(row: Dict[str, Any], read_status: str, contexts: List[Dict[str, Any]], ext: str) -> Tuple[str, str, str]:
    triage_class = prop(row, "def_triage_class")
    source_rel = prop(row, "def_source_rel_path").lower()

    if read_status == "FILE_MISSING":
        return "FILE_MISSING_OR_UNREADABLE", "HIGH", "Path from evidence no longer exists or cannot be found."
    if read_status.startswith("READ_ERROR"):
        return "FILE_MISSING_OR_UNREADABLE", "HIGH", read_status
    if read_status == "LARGE_FILE_SKIPPED":
        return "LARGE_FILE_SKIPPED", "MEDIUM", "Skipped to avoid heavy memory use; needs targeted review only if still active."
    if read_status == "BINARY_FILE_SKIPPED":
        return "BINARY_FILE_SKIPPED", "LOW", "Binary-like file skipped from text context sampling."

    danger_count = sum(1 for c in contexts if prop(c, "def_danger_hits"))
    secret_count = sum(1 for c in contexts if prop(c, "def_secret_hits"))
    comment_count = sum(1 for c in contexts if prop(c, "def_hit_is_comment_or_doc") == "true")

    if contexts and comment_count == len(contexts):
        return "COMMENT_OR_DOCSTRING_FALSE_POSITIVE_CANDIDATE", "MEDIUM_HIGH", "All sampled marker hits appear in comments/docstrings."

    if danger_count > 0:
        if any(x in source_rel for x in ["preview", "dryrun", "review", "seal", "gate", "disabled", "not-run", "not_run"]):
            return "DANGER_IN_GATED_OR_REVIEW_BOUNDARY", "MEDIUM_HIGH", "Danger marker appears in gated/review/dryrun/disabled-looking script; verify boundary."
        return "TRUE_DANGER_CONTEXT_REVIEW_REQUIRED", "HIGH", "Danger marker appears in active source context."

    if secret_count > 0:
        joined = "\n".join(prop(c, "def_masked_context") for c in contexts).lower()
        if any(x in joined for x in ["***masked***", "bearer", "authorization"]):
            return "TRUE_SECRET_VALUE_SUSPECT_REVIEW_REQUIRED", "HIGH", "Secret-like assignment/value pattern detected and masked."
        return "SECRET_FIELD_NAME_OR_RUNTIME_PARAMETER_LIKELY", "MEDIUM", "Secret-like marker appears more like key/field/runtime parameter name."

    if triage_class.startswith("NEEDS_CONTEXT"):
        return "CONTEXT_NOT_CONFIRMED_ACTIVE_SECRET", "MEDIUM", "No direct marker hit found in limited sampling despite active queue label."

    return "MANUAL_CONTEXT_REVIEW_REQUIRED", "MEDIUM", "No decisive context rule matched."


def build_samples(base: Path, active_rows: List[Dict[str, str]], max_files: int, context_lines: int, max_file_bytes: int) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    samples = []
    hit_rows = []

    for idx, row in enumerate(active_rows[:max_files], 1):
        rel = prop(row, "def_source_rel_path")
        path = base / rel
        ext = path.suffix.lower()

        read_status, lines = read_text_lines(path, max_file_bytes=max_file_bytes)
        contexts = choose_context(lines, ext, context_lines=context_lines) if lines else []
        ast_result = ast_status(path, ext, lines) if read_status == "READ_OK" else "NOT_CHECKED"

        evidence_class, confidence, reason = classify_context(row, read_status, contexts, ext)
        file_hash = sha256_file(path) if path.exists() and read_status == "READ_OK" else ""

        base_row = {
            "def_sample_order": f"{idx:06d}",
            "def_p0_evidence_id": prop(row, "def_p0_evidence_id"),
            "def_subsystem": prop(row, "def_subsystem"),
            "def_triage_class": prop(row, "def_triage_class"),
            "def_context_evidence_class": evidence_class,
            "def_context_confidence": confidence,
            "def_context_reason": reason,
            "def_source_rel_path": rel,
            "def_source_exists": str(path.exists()).lower(),
            "def_read_status": read_status,
            "def_file_ext": ext,
            "def_file_size_bytes": str(path.stat().st_size) if path.exists() else "",
            "def_sha256": file_hash,
            "def_ast_status": ast_result,
            "def_context_hit_count": str(len(contexts)),
            "def_apply_enabled": "false",
            "def_source_mutation": "false",
            "def_db_write": "false",
        }
        samples.append(base_row)

        if contexts:
            for j, c in enumerate(contexts, 1):
                hit = dict(base_row)
                hit.update({
                    "def_context_hit_index": str(j),
                    "def_hit_line": prop(c, "def_hit_line"),
                    "def_secret_hits": prop(c, "def_secret_hits"),
                    "def_danger_hits": prop(c, "def_danger_hits"),
                    "def_hit_is_comment_or_doc": prop(c, "def_hit_is_comment_or_doc"),
                    "def_masked_context": prop(c, "def_masked_context"),
                })
                hit_rows.append(hit)
        else:
            hit = dict(base_row)
            hit.update({
                "def_context_hit_index": "0",
                "def_hit_line": "",
                "def_secret_hits": "",
                "def_danger_hits": "",
                "def_hit_is_comment_or_doc": "",
                "def_masked_context": ""
            })
            hit_rows.append(hit)

    return samples, hit_rows


def build_summary(samples: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    groups = defaultdict(lambda: {"count": 0, "examples": []})
    for r in samples:
        key = (
            prop(r, "def_context_evidence_class"),
            prop(r, "def_context_confidence"),
            prop(r, "def_subsystem"),
        )
        groups[key]["count"] += 1
        if len(groups[key]["examples"]) < 5:
            groups[key]["examples"].append(prop(r, "def_source_rel_path"))

    rows = []
    n = 0
    for (klass, confidence, subsystem), g in groups.items():
        n += 1
        rows.append({
            "def_context_summary_id": f"P0-CTX-SUM-{n:04d}",
            "def_context_evidence_class": klass,
            "def_context_confidence": confidence,
            "def_subsystem": subsystem,
            "def_count": g["count"],
            "def_examples": " | ".join(g["examples"]),
            "def_next_action": next_action_for_class(klass),
            "def_auto_fix_allowed": "false",
            "def_apply_enabled": "false"
        })

    return sorted(rows, key=lambda x: (-int(x["def_count"]), x["def_context_evidence_class"], x["def_subsystem"]))


def next_action_for_class(klass: str) -> str:
    if klass == "TRUE_DANGER_CONTEXT_REVIEW_REQUIRED":
        return "v0115F3_DANGER_BOUNDARY_DECISION_MATRIX_ONLY"
    if klass == "TRUE_SECRET_VALUE_SUSPECT_REVIEW_REQUIRED":
        return "v0115F3_SECRET_RUNTIME_PARAMETER_DECISION_MATRIX_ONLY"
    if klass == "DANGER_IN_GATED_OR_REVIEW_BOUNDARY":
        return "v0115F3_BOUNDARY_CONFIRMATION_MATRIX_ONLY"
    if klass == "SECRET_FIELD_NAME_OR_RUNTIME_PARAMETER_LIKELY":
        return "v0115F3_SECRET_FIELDNAME_CLEARANCE_CANDIDATE_ONLY"
    if klass == "COMMENT_OR_DOCSTRING_FALSE_POSITIVE_CANDIDATE":
        return "v0115F3_FALSE_POSITIVE_CLEARANCE_CANDIDATE_ONLY"
    if klass in {"FILE_MISSING_OR_UNREADABLE", "LARGE_FILE_SKIPPED"}:
        return "v0115F3_PATH_AND_SIZE_REVIEW_ONLY"
    return "v0115F3_MANUAL_DECISION_MATRIX_ONLY"


def build_subsystem_matrix(samples: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    groups = defaultdict(Counter)
    for r in samples:
        s = prop(r, "def_subsystem")
        groups[s]["total"] += 1
        groups[s][prop(r, "def_context_evidence_class")] += 1

    rows = []
    for subsystem, c in groups.items():
        total = c["total"]
        high = c["TRUE_DANGER_CONTEXT_REVIEW_REQUIRED"] + c["TRUE_SECRET_VALUE_SUSPECT_REVIEW_REQUIRED"]
        rows.append({
            "def_subsystem": subsystem,
            "def_sampled_active_p0": total,
            "def_true_danger": c["TRUE_DANGER_CONTEXT_REVIEW_REQUIRED"],
            "def_secret_value_suspect": c["TRUE_SECRET_VALUE_SUSPECT_REVIEW_REQUIRED"],
            "def_gated_danger_boundary": c["DANGER_IN_GATED_OR_REVIEW_BOUNDARY"],
            "def_secret_field_or_runtime_likely": c["SECRET_FIELD_NAME_OR_RUNTIME_PARAMETER_LIKELY"],
            "def_comment_doc_false_positive_candidate": c["COMMENT_OR_DOCSTRING_FALSE_POSITIVE_CANDIDATE"],
            "def_missing_or_unreadable": c["FILE_MISSING_OR_UNREADABLE"],
            "def_large_skipped": c["LARGE_FILE_SKIPPED"],
            "def_high_attention_ratio": f"{(high / total if total else 0):.2%}",
            "def_apply_enabled": "false"
        })
    return sorted(rows, key=lambda x: (-int(x["def_true_danger"]) - int(x["def_secret_value_suspect"]), -int(x["def_sampled_active_p0"]), x["def_subsystem"]))


def build_readiness(input_rows: int, sampled: int, summary_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    counter = Counter()
    for r in summary_rows:
        counter[prop(r, "def_context_evidence_class")] += int(prop(r, "def_count", "0"))

    high_attention = (
        counter["TRUE_DANGER_CONTEXT_REVIEW_REQUIRED"] +
        counter["TRUE_SECRET_VALUE_SUSPECT_REVIEW_REQUIRED"] +
        counter["DANGER_IN_GATED_OR_REVIEW_BOUNDARY"]
    )

    return [{
        "def_gate_status": "ACTIVE_P0_CONTEXT_SAMPLING_READY_REVIEW_ONLY",
        "def_allow_next": "true",
        "def_reason": "Limited masked context sampling completed for active P0 queue. No mutation, no apply.",
        "def_active_p0_input_rows": str(input_rows),
        "def_sampled_rows": str(sampled),
        "def_high_attention_rows": str(high_attention),
        "def_source_read": "limited_masked_context_only",
        "def_execution_enabled": "false",
        "def_apply_enabled": "false",
        "def_source_mutation": "false",
        "def_canonical_merge": "false",
        "def_db_write": "false",
        "def_next_allowed_phase": "v0115F3 active P0 decision matrix only"
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
            if "TRUE_DANGER" in joined or "TRUE_SECRET_VALUE" in joined:
                cls = " class='risk-high'"
            elif "BOUNDARY" in joined or "MISSING" in joined or "LARGE" in joined:
                cls = " class='risk-med'"
            elif "FIELD_NAME" in joined or "FALSE_POSITIVE" in joined:
                cls = " class='risk-low'"
            out.append(f"<tr{cls}>")
            for c in cols:
                v = prop(r, c)
                if len(v) > 1200:
                    v = v[:1200] + "..."
                out.append(f"<td><pre>{h(v)}</pre></td>" if c == "def_masked_context" else f"<td>{h(v)}</td>")
            out.append("</tr>")

    out.append("</tbody></table>")
    return "".join(out)


def write_html(path: Path, payload: Dict[str, Any]) -> None:
    readiness = payload["readiness"][0]

    cards = ""
    for k, v in [
        ("Gate", readiness["def_gate_status"]),
        ("Active P0 Input", readiness["def_active_p0_input_rows"]),
        ("Sampled", readiness["def_sampled_rows"]),
        ("High Attention", readiness["def_high_attention_rows"]),
        ("Source Read", "limited"),
        ("Mutation", "false"),
        ("Apply", "false"),
        ("Next", "v0115F3")
    ]:
        cards += f"<div class='card'><div class='k'>{h(k)}</div><div class='v'>{h(v)}</div></div>"

    style = """
:root{--bg:#f7f6f2;--paper:#fffefa;--line:#dedbd2;--ink:#24231f;--muted:#706d64;--seal:#8f2f24;--red:#c96b5a;--yellow:#c4943a;--green:#5a9e6f;--sky:#9fbcc2}
body{margin:0;background:radial-gradient(circle at 12% 10%,rgba(159,188,194,.24),transparent 28%),radial-gradient(circle at 88% 0%,rgba(180,200,190,.22),transparent 31%),linear-gradient(135deg,rgba(255,255,255,.70),rgba(247,246,242,1));color:var(--ink);font-family:'Microsoft JhengHei','Noto Sans TC',Arial,sans-serif;font-size:8.4px;line-height:1.34}
.wrap{max-width:1880px;margin:0 auto;padding:16px}.header{display:grid;grid-template-columns:1fr auto;gap:16px;align-items:start;margin-bottom:10px}
h1{font-size:15px;margin:0 0 4px;font-weight:650}.sub{font-size:8.2px;color:var(--muted)}
.seal{border:2px solid var(--seal);color:var(--seal);width:42px;height:42px;display:flex;align-items:center;justify-content:center;font-size:22px;font-weight:700;border-radius:6px;background:rgba(255,255,255,.48)}
.cards{display:grid;grid-template-columns:repeat(8,1fr);gap:7px;margin:10px 0}.card{background:var(--paper);border:1px solid var(--line);border-radius:10px;padding:7px;min-height:43px;box-shadow:0 8px 22px rgba(60,50,30,.045)}
.k{font-size:7.5px;color:var(--muted)}.v{font:650 9.8px Consolas,monospace;margin-top:4px;word-break:break-word}
.sec{background:rgba(255,254,250,.93);border:1px solid var(--line);border-radius:13px;padding:9px;margin-bottom:10px;overflow:hidden;box-shadow:0 10px 26px rgba(60,50,30,.045)}
h2{font-size:10px;margin:0 0 7px;font-weight:650}.note{white-space:pre-wrap;background:#fbfaf6;border:1px solid #e8e4da;border-radius:10px;padding:8px;color:#514d45;font-size:8.2px}
table{width:100%;border-collapse:collapse;table-layout:fixed;font-size:7.25px}th,td{border-bottom:1px solid #ebe8df;padding:3px 4px;vertical-align:top;word-break:break-word;overflow-wrap:anywhere}
th{background:#f0eee8;text-align:left;font-weight:650;color:#555149;position:sticky;top:0}tr:hover td{background:#f8f7f1}
pre{white-space:pre-wrap;margin:0;font-family:Consolas,'DM Mono',monospace;font-size:7px;line-height:1.28}
.risk-high td{background:rgba(201,107,90,.08)}.risk-med td{background:rgba(196,148,58,.08)}.risk-low td{background:rgba(90,158,111,.065)}
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
<head><meta charset="utf-8"/><title>VIA v0115F2 Active P0 Context Sampling</title><style>{style}</style><script>{js}</script></head>
<body><div class="wrap">
  <div class="header">
    <div>
      <h1>def VIA v0115F2 · Active P0 Context Sampling Package Only</h1>
      <div class="sub">Limited Source Read · Masked Context · Danger Boundary · Runtime Secret · No Mutation · No Apply</div>
    </div>
    <div class="seal">理</div>
  </div>

  <div class="cards">{cards}</div>

  <div class="sec">
    <h2>def Executive Judgment</h2>
    <span class="tag">LIMITED CONTEXT</span><span class="tag">MASKED SECRET</span><span class="tag">NO MUTATION</span><span class="tag">NO APPLY</span><span class="tag">NO DB WRITE</span>
    <div class="note">v0115F2 只對 v0115F1 剩餘 Active P0 做有限上下文讀取。所有疑似 secret value 會先遮蔽後才寫入 CSV/JSON/HTML。這一步仍不是修補；下一步 v0115F3 才根據 context evidence 建立 decision matrix。</div>
    <input id="q" class="search" oninput="filterTables(this.value)" placeholder="搜尋 TRUE_DANGER / TRUE_SECRET_VALUE / FIELD_NAME / BOUNDARY / VDF / VAP / Supportive ..."/>
    <button class="btn" onclick="quick('TRUE_DANGER')">TRUE_DANGER</button>
    <button class="btn" onclick="quick('TRUE_SECRET_VALUE')">SECRET_VALUE</button>
    <button class="btn" onclick="quick('FIELD_NAME')">FIELD_NAME</button>
    <button class="btn" onclick="quick('BOUNDARY')">BOUNDARY</button>
    <button class="btn" onclick="quick('VDF')">VDF</button>
    <button class="btn" onclick="quick('VAP')">VAP</button>
    <button class="btn" onclick="quick('')">RESET</button>
  </div>

  <div class="sec"><h2>def Readiness Gate</h2>{render_table(payload["readiness"], ["def_gate_status","def_allow_next","def_reason","def_active_p0_input_rows","def_sampled_rows","def_high_attention_rows","def_source_read","def_apply_enabled","def_source_mutation","def_db_write","def_next_allowed_phase"], 20)}</div>
  <div class="sec"><h2>def Context Evidence Summary</h2>{render_table(payload["summary_rows"], ["def_context_summary_id","def_context_evidence_class","def_context_confidence","def_subsystem","def_count","def_next_action","def_auto_fix_allowed","def_apply_enabled"], 200)}</div>

  <div class="grid2">
    <div class="sec"><h2>def Subsystem Context Matrix</h2>{render_table(payload["subsystem_matrix"], ["def_subsystem","def_sampled_active_p0","def_true_danger","def_secret_value_suspect","def_gated_danger_boundary","def_secret_field_or_runtime_likely","def_comment_doc_false_positive_candidate","def_missing_or_unreadable","def_large_skipped","def_high_attention_ratio","def_apply_enabled"], 80)}</div>
    <div class="sec"><h2>def Sample Row Matrix</h2>{render_table(payload["sample_rows"], ["def_sample_order","def_p0_evidence_id","def_subsystem","def_triage_class","def_context_evidence_class","def_context_confidence","def_source_rel_path","def_read_status","def_context_hit_count","def_ast_status","def_apply_enabled"], 500)}</div>
  </div>

  <div class="sec"><h2>def Masked Context Hit Matrix</h2>{render_table(payload["context_hits"], ["def_sample_order","def_p0_evidence_id","def_subsystem","def_context_evidence_class","def_source_rel_path","def_hit_line","def_secret_hits","def_danger_hits","def_hit_is_comment_or_doc","def_masked_context","def_apply_enabled"], 700)}</div>

  <div class="footer">
    v0115F1: <span class="path">{h(payload["v0115f1_run"])}</span><br/>
    RunDir: <span class="path">{h(payload["run_dir"])}</span><br/>
    SAFE: Local-only · Limited source read · Masked output · No source mutation · No canonical merge · No DB write · No apply
  </div>
</div></body></html>"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(doc, encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--v0115f1-run", required=True)
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--max-files", type=int, default=512)
    ap.add_argument("--context-lines", type=int, default=3)
    ap.add_argument("--max-file-bytes", type=int, default=2 * 1024 * 1024)
    args = ap.parse_args()

    base = Path(args.base)
    v0115f1_run = Path(args.v0115f1_run)
    run_dir = Path(args.run_dir)
    output = run_dir / "output"
    report = run_dir / "report"
    sample_dir = run_dir / "_active_p0_context_sampling"
    output.mkdir(parents=True, exist_ok=True)
    report.mkdir(parents=True, exist_ok=True)
    sample_dir.mkdir(parents=True, exist_ok=True)

    active_path = v0115f1_run / "_p0_false_positive_triage" / "VIA_v0115F1_P0_ActiveQueueAfterTriage.csv"
    active_rows = read_csv(active_path)

    samples, context_hits = build_samples(
        base=base,
        active_rows=active_rows,
        max_files=args.max_files,
        context_lines=args.context_lines,
        max_file_bytes=args.max_file_bytes
    )

    summary_rows = build_summary(samples)
    subsystem_matrix = build_subsystem_matrix(samples)
    readiness = build_readiness(len(active_rows), len(samples), summary_rows)

    write_csv(sample_dir / "VIA_v0115F2_ActiveP0_ContextSampleRows.csv", samples)
    write_csv(sample_dir / "VIA_v0115F2_ActiveP0_MaskedContextHits.csv", context_hits)
    write_csv(sample_dir / "VIA_v0115F2_ActiveP0_ContextEvidenceSummary.csv", summary_rows)
    write_csv(sample_dir / "VIA_v0115F2_ActiveP0_SubsystemContextMatrix.csv", subsystem_matrix)
    write_csv(output / "VIA_v0115F2_ReadinessGate.csv", readiness)

    write_json(sample_dir / "VIA_v0115F2_ActiveP0_ContextSampleRows.json", samples)
    write_json(sample_dir / "VIA_v0115F2_ActiveP0_MaskedContextHits.json", context_hits)
    write_json(sample_dir / "VIA_v0115F2_ActiveP0_ContextEvidenceSummary.json", summary_rows)
    write_json(sample_dir / "VIA_v0115F2_ActiveP0_SubsystemContextMatrix.json", subsystem_matrix)
    write_json(output / "VIA_v0115F2_ReadinessGate.json", readiness)

    html_path = report / "VIA_v0115F2_ActiveP0_ContextSampling_OnePage.html"
    payload = {
        "v0115f1_run": str(v0115f1_run),
        "run_dir": str(run_dir),
        "readiness": readiness,
        "sample_rows": samples,
        "context_hits": context_hits,
        "summary_rows": summary_rows,
        "subsystem_matrix": subsystem_matrix
    }
    write_html(html_path, payload)

    manifest = {
        "schema_version": "VIA_v0115F2A_ActiveP0ContextSamplingRegexHotfix",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "gate": readiness[0]["def_gate_status"],
        "base": str(base),
        "v0115f1_run": str(v0115f1_run),
        "run_dir": str(run_dir),
        "report": str(html_path),
        "active_p0_input_rows": len(active_rows),
        "sampled_rows": len(samples),
        "outputs": {
            "sample_rows": str(sample_dir / "VIA_v0115F2_ActiveP0_ContextSampleRows.csv"),
            "masked_context_hits": str(sample_dir / "VIA_v0115F2_ActiveP0_MaskedContextHits.csv"),
            "context_summary": str(sample_dir / "VIA_v0115F2_ActiveP0_ContextEvidenceSummary.csv"),
            "subsystem_matrix": str(sample_dir / "VIA_v0115F2_ActiveP0_SubsystemContextMatrix.csv"),
            "readiness": str(output / "VIA_v0115F2_ReadinessGate.csv")
        },
        "policy": {
            "local_only": True,
            "no_external_call": True,
            "no_rescan": True,
            "source_read": "limited_masked_context_only",
            "mask_secret_output": True,
            "execution_enabled": False,
            "apply_enabled": False,
            "source_mutation": False,
            "canonical_merge": False,
            "db_write": False,
            "delete": False,
            "stop_process": False
        }
    }
    write_json(output / "VIA_v0115F2_ActiveP0ContextSampling_Manifest.json", manifest)

    print("")
    print("=" * 80)
    print("def VIA v0115F2A Active P0 Context Sampling Regex Hotfix COMPLETE")
    print("=" * 80)
    print("Gate       : ACTIVE_P0_CONTEXT_SAMPLING_READY_REVIEW_ONLY")
    print(f"Active P0  : {len(active_rows)}")
    print(f"Sampled    : {len(samples)}")
    print(f"Report     : {html_path}")
    print(f"Samples    : {sample_dir}")
    print(f"Output     : {output}")
    print("[SAFE] Limited masked source read only. No apply. No source mutation. No DB write.")


if __name__ == "__main__":
    main()

