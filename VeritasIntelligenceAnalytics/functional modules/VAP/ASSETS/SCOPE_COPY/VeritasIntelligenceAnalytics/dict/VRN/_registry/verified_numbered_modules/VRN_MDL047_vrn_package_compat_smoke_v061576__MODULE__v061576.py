# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import csv
import hashlib
import html
import json
import os
import re
import shutil
import sys
import traceback
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any


VERSION = "VRN_PACKAGE_COMPAT_SMOKE_V061576"


# ==================================================================================================
# def 00_UTILITIES
# ==================================================================================================
def def_clean(x: Any) -> str:
    s = "" if x is None else str(x)
    s = html.unescape(s)
    s = s.replace("\u3000", " ").replace("\r", "\n")
    s = re.sub(r"[ \t]+", " ", s)
    return s.strip()


def def_light(sev: str) -> str:
    s = str(sev or "").upper()
    if s in ["OK", "PASS", "YES", "INCLUDED", "READY", "FOUND"]:
        return "🟢 INPUT 🟢 DB 🟢 TRUST"
    if s in ["WARN", "OPTIONAL", "REVIEW", "SMOKE_ONLY"]:
        return "🟢 INPUT 🟡 DB 🟡 TRUST"
    return "🔴 INPUT 🔴 DB 🔴 TRUST"


def def_sha256_file(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def def_read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    for enc in ["utf-8", "utf-8-sig", "cp950", "big5"]:
        try:
            return json.loads(path.read_text(encoding=enc))
        except Exception:
            pass
    return {}


def def_write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def def_write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        rows = [{"empty_marker": ""}]

    fields: list[str] = []
    for r in rows:
        for k in r:
            if k not in fields:
                fields.append(k)

    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


def def_find_latest_dir(root: Path, prefixes: list[str]) -> Path | None:
    if not root.exists():
        return None
    hits: list[Path] = []
    for prefix in prefixes:
        hits.extend([p for p in root.glob(prefix + "_*") if p.is_dir()])
    if not hits:
        return None
    return sorted(hits, key=lambda p: p.stat().st_mtime, reverse=True)[0]


def def_ast_compile_check(path: Path) -> tuple[str, str]:
    if not path.exists():
        return "NO", "missing"
    if path.suffix.lower() != ".py":
        return "N/A", ""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
        ast.parse(text)
        compile(text, str(path), "exec")
        return "YES", ""
    except Exception as e:
        return "NO", f"{type(e).__name__}: {e}"


def def_file_size(path: Path) -> int:
    try:
        return path.stat().st_size
    except Exception:
        return 0


def def_copy_asset(src: Path, package_dir: Path, category: str) -> Path:
    safe_category = re.sub(r"[^A-Za-z0-9_\-]+", "_", category).strip("_") or "misc"
    dst_dir = package_dir / safe_category
    dst_dir.mkdir(parents=True, exist_ok=True)

    name = src.name
    dst = dst_dir / name
    if dst.exists():
        stem = src.stem
        suffix = src.suffix
        dst = dst_dir / f"{stem}_{def_sha256_file(src)[:10]}{suffix}"

    shutil.copy2(src, dst)
    return dst


# ==================================================================================================
# def 01_HTML
# ==================================================================================================
def def_html_table(title: str, rows: list[dict], limit: int | None = None) -> str:
    if limit is not None:
        rows = rows[:limit]

    if not rows:
        return f"<section class='card'><h2>{html.escape(title)}</h2><p>No rows.</p></section>"

    fields: list[str] = []
    for r in rows:
        for k in r:
            if k not in fields:
                fields.append(k)

    th = "".join(f"<th>{html.escape(str(k))}</th>" for k in fields)
    trs: list[str] = []

    for r in rows:
        sev = str(r.get("Severity", "OK")).upper()
        tr_cls = "warnrow" if sev == "WARN" else ("errrow" if sev == "ERR" else "")
        tds: list[str] = []

        for k in fields:
            v = "" if r.get(k) is None else str(r.get(k, ""))
            cls = "left" if any(x in k.lower() for x in ["path", "asset", "role", "reason", "file", "rule", "next", "package"]) else "center"
            safe_v = html.escape(str(v)).replace(chr(10), "<br>")
            tds.append(f"<td class='{cls}'>{safe_v}</td>")

        trs.append(f"<tr class='{tr_cls}'>" + "".join(tds) + "</tr>")

    return (
        f"<section class='card'>"
        f"<h2>{html.escape(title)}</h2>"
        f"<div class='table-wrap'>"
        f"<table><thead><tr>{th}</tr></thead><tbody>{''.join(trs)}</tbody></table>"
        f"</div></section>"
    )


def def_write_html(path: Path, counts: dict, sections: list[tuple[str, list[dict], int | None]]) -> None:
    css = """
body{margin:0;background:#07111f;color:#eef6ff;font-family:Segoe UI,'Microsoft JhengHei',Arial,sans-serif;font-size:12px}
header{padding:30px 38px;background:linear-gradient(135deg,#0d1b2f,#102a43);border-bottom:1px solid #1f3557}
h1{margin:0;font-size:28px}.sub{color:#9fb3c8;margin-top:10px;font-size:13px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:14px;padding:22px 34px}
.kpi{background:#0d1b2f;border:1px solid #1f3557;border-radius:18px;padding:16px;box-shadow:0 10px 28px rgba(0,0,0,.18)}
.v{font-size:25px;font-weight:800}.k{color:#9fb3c8}
main{padding:0 34px 34px}
.card{background:#0d1b2f;border:1px solid #1f3557;border-radius:18px;padding:18px;margin:18px 0;box-shadow:0 10px 28px rgba(0,0,0,.14)}
.table-wrap{overflow:auto;max-height:78vh;border:1px solid #1f3557;border-radius:14px}
table{border-collapse:collapse;min-width:100%;width:max-content}
th{position:sticky;top:0;background:#132541;padding:10px;text-align:center;z-index:2}
td{padding:8px 10px;border-bottom:1px solid rgba(255,255,255,.08);vertical-align:top;max-width:1500px;white-space:normal;word-break:break-word}
td.left{text-align:left}td.center{text-align:center}
.warnrow{background:rgba(255,209,102,.08)}
.errrow{background:rgba(255,80,80,.10)}
.footer{padding:20px 34px;color:#9fb3c8}
"""
    cards = "".join(
        f"<div class='kpi'><div class='v'>{html.escape(str(v))}</div><div class='k'>{html.escape(str(k))}</div></div>"
        for k, v in counts.items()
    )
    body = "".join(def_html_table(t, rows, lim) for t, rows, lim in sections)

    doc = f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>VRN Package Matrix + Compatibility Smoke v061576</title>
<style>{css}</style>
</head>
<body>
<header>
<h1>VRN · Package Matrix + Future Input Compatibility Smoke v0.6.15.7.6</h1>
<div class="sub">package command documents · matrix display · smoke test BASE/input · no DB write · no canonical / SSOT mutation</div>
</header>
<div class="grid">{cards}</div>
<main>{body}</main>
<div class="footer">Veritas Intelligence Analytics │ AI-Augmented Investment Intelligence for Smarter Decisions and Deeper Insight</div>
</body>
</html>
"""
    path.write_text(doc, encoding="utf-8")


# ==================================================================================================
# def 02_PACKAGE_SELECTION
# ==================================================================================================
def def_collect_assets(base: Path, run_root: Path, supportive_dir: Path, config_dir: Path) -> tuple[list[dict], list[Path]]:
    rows: list[dict] = []
    paths: list[Path] = []

    latest_specs = [
        ("VRN Production Home", ["VRN_FINAL_CONTROL_CENTER_V061575"], "VRN_PRODUCTION_HOME_v061575.html", "HTML final home", True),
        ("VRN Business Validation", ["VRN_BUSINESS_VALIDATION_REPORT_V061574"], "VRN_FinancialData_Business_Validation_Report_v061574.html", "HTML business validation", True),
        ("VRN Production Lock", ["VRN_FINAL_PRODUCTION_LOCK_REGISTRY_V061573"], "VRN_Final_Production_Lock_Registry_v061573.html", "HTML production lock", True),
        ("VRN Post Commit Seal", ["VRN_POST_COMMIT_PRODUCTION_SEAL_V0615721"], "VRN_PostCommit_Production_Seal_v0615721.html", "HTML post-commit audit", True),
        ("VRN Real Commit Proof", ["VRN_REAL_COMMIT_ARGFIX_BACKUP_POSTCHECK_V0615711"], "VRN_Real_Commit_ArgFix_Backup_Postcheck_Rollback_v0615711.html", "HTML real commit proof", True),
        ("VRN Final Governance", ["VRN_FINAL_INTEGRATION_GOVERNANCE_SEAL_V0615703"], "VRN_Final_Integration_Governance_Seal_v0615703.html", "HTML governance", False),
        ("VRN Final Handover", ["VRN_FINAL_HANDOVER_COMMIT_BLOCKER_SEAL_V0615702"], "VRN_Final_Handover_Commit_Blocker_Seal_v0615702.html", "HTML handover", False),
    ]

    for label, prefixes, filename, role, required in latest_specs:
        d = def_find_latest_dir(run_root, prefixes)
        p = d / filename if d else Path("")
        exists = p.exists()
        sev = "OK" if exists else ("ERR" if required else "WARN")
        rows.append({
            "Status Lights": def_light(sev),
            "Package Item": label,
            "Category": "latest_report",
            "Role": role,
            "Path": str(p) if str(p) != "." else "",
            "Exists": "YES" if exists else "NO",
            "Size": def_file_size(p),
            "SHA256": def_sha256_file(p),
            "Required": "YES" if required else "NO",
            "Severity": sev,
        })
        if exists:
            paths.append(p)

        if d:
            for ext in ["*.json", "*.csv", "*.md", "*.ps1"]:
                for extra in d.glob(ext):
                    if extra.is_file():
                        rows.append({
                            "Status Lights": def_light("OK"),
                            "Package Item": extra.name,
                            "Category": "latest_run_support_file",
                            "Role": f"{label} support output",
                            "Path": str(extra),
                            "Exists": "YES",
                            "Size": def_file_size(extra),
                            "SHA256": def_sha256_file(extra),
                            "Required": "NO",
                            "Severity": "OK",
                        })
                        paths.append(extra)

    direct_assets = [
        ("Compatibility Gate Module", supportive_dir / "VIS_VRN_NewReportCompatibilityGate_v01.py", "future_gate", "Python gate for new report compatibility", True),
        ("Adapter Registry", config_dir / "VIS_VRN_AdapterRegistry_v01.json", "future_gate", "Broker/layout adapter registry", True),
        ("New Report Format Playbook", config_dir / "VIS_VRN_NewReport_Format_Playbook_v01.md", "future_gate", "New format handling playbook", True),
        ("Supportive Module Index HTML", supportive_dir / "VIS_Supportive_Module_Index.html", "supportive_index", "Supportive module final index", False),
        ("Supportive Module Index JSON", supportive_dir / "VIS_Supportive_Module_Index.json", "supportive_index", "Supportive module final index data", False),
    ]

    for label, p, cat, role, required in direct_assets:
        exists = p.exists()
        ast_ok, ast_err = def_ast_compile_check(p)
        sev = "OK" if exists and ast_ok != "NO" else ("ERR" if required else "WARN")
        rows.append({
            "Status Lights": def_light(sev),
            "Package Item": label,
            "Category": cat,
            "Role": role,
            "Path": str(p),
            "Exists": "YES" if exists else "NO",
            "AST/Compile": ast_ok,
            "AST Error": ast_err,
            "Size": def_file_size(p),
            "SHA256": def_sha256_file(p),
            "Required": "YES" if required else "NO",
            "Severity": sev,
        })
        if exists:
            paths.append(p)

    # Include current package/control scripts in BASE if present.
    for pattern in ["*.ps1", "*.md"]:
        for p in base.glob(pattern):
            if p.is_file():
                rows.append({
                    "Status Lights": def_light("OK"),
                    "Package Item": p.name,
                    "Category": "base_command_doc",
                    "Role": "VRN base command/doc file",
                    "Path": str(p),
                    "Exists": "YES",
                    "Size": def_file_size(p),
                    "SHA256": def_sha256_file(p),
                    "Required": "NO",
                    "Severity": "OK",
                })
                paths.append(p)

    # Deduplicate paths.
    seen = set()
    unique_paths: list[Path] = []
    for p in paths:
        rp = str(p.resolve()).lower()
        if rp not in seen:
            seen.add(rp)
            unique_paths.append(p)

    return rows, unique_paths


# ==================================================================================================
# def 03_SMOKE_TEST
# ==================================================================================================
def def_smoke_test_input(input_dir: Path) -> list[dict]:
    rows: list[dict] = []

    if not input_dir.exists():
        return [{
            "Status Lights": def_light("ERR"),
            "File": "",
            "Suffix": "",
            "Size": 0,
            "Ticker Found": "",
            "Broker Guess": "",
            "Route": "INPUT_DIR_MISSING",
            "Reason": str(input_dir),
            "Severity": "ERR",
        }]

    files = []
    for ext in ["*.pdf", "*.PDF", "*.html", "*.htm", "*.txt", "*.csv", "*.xlsx", "*.xls"]:
        files.extend(input_dir.glob(ext))

    files = sorted(set([p for p in files if p.is_file()]), key=lambda p: p.name.lower())

    if not files:
        return [{
            "Status Lights": def_light("WARN"),
            "File": "",
            "Suffix": "",
            "Size": 0,
            "Ticker Found": "",
            "Broker Guess": "",
            "Route": "NO_INPUT_FILES",
            "Reason": "Put future reports into BASE\\input and rerun.",
            "Severity": "WARN",
        }]

    broker_patterns = [
        ("國泰", ["國泰", "Cathay"]),
        ("兆豐", ["兆豐", "Mega"]),
        ("華南", ["華南", "HuaNan", "Hua Nan"]),
        ("CLST", ["CLST"]),
        ("未知", []),
    ]

    for p in files:
        name = p.name
        ticker_hits = re.findall(r"(?<!\d)([1-9]\d{3})(?!\d)", name)
        ticker = ticker_hits[0] if ticker_hits else ""

        broker = "未知"
        for b, pats in broker_patterns:
            if any(x.lower() in name.lower() for x in pats):
                broker = b
                break

        if not ticker:
            route = "STAGING_REVIEW"
            reason = "No 4-digit Taiwan ticker found in filename; Compatibility Gate required."
            sev = "WARN"
        elif broker == "未知":
            route = "COMPATIBILITY_GATE"
            reason = "Ticker found but broker/layout unknown; staging only."
            sev = "WARN"
        else:
            route = "COMPATIBILITY_GATE_READY"
            reason = "Ticker and broker hint found; still must pass Compatibility Gate before canonical."
            sev = "OK"

        rows.append({
            "Status Lights": def_light(sev),
            "File": name,
            "Path": str(p),
            "Suffix": p.suffix.lower(),
            "Size": def_file_size(p),
            "Ticker Found": ticker,
            "Broker Guess": broker,
            "Route": route,
            "Reason": reason,
            "Severity": sev,
        })

    return rows


# ==================================================================================================
# def 04_ZIP
# ==================================================================================================
def def_build_package_zip(package_dir: Path, files: list[Path]) -> tuple[Path, list[dict]]:
    package_dir.mkdir(parents=True, exist_ok=True)
    copied_rows: list[dict] = []

    for src in files:
        if not src.exists() or not src.is_file():
            continue

        if src.suffix.lower() in [".duckdb", ".db", ".sqlite", ".parquet"]:
            # Do not copy DB/heavy data into command/doc package by default.
            continue

        category = "docs"
        lower = src.name.lower()
        if src.suffix.lower() == ".ps1":
            category = "commands"
        elif src.suffix.lower() == ".py":
            category = "modules"
        elif src.suffix.lower() == ".html":
            category = "html_reports"
        elif src.suffix.lower() == ".json":
            category = "json_registry"
        elif src.suffix.lower() == ".csv":
            category = "csv_matrix"
        elif src.suffix.lower() == ".md":
            category = "playbooks"

        dst = def_copy_asset(src, package_dir, category)
        copied_rows.append({
            "Status Lights": def_light("OK"),
            "Source": str(src),
            "Package Path": str(dst),
            "Category": category,
            "Size": def_file_size(dst),
            "SHA256": def_sha256_file(dst),
            "Severity": "OK",
        })

    zip_path = package_dir.parent / (package_dir.name + ".zip")
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for p in package_dir.rglob("*"):
            if p.is_file():
                z.write(p, p.relative_to(package_dir.parent))

    copied_rows.append({
        "Status Lights": def_light("OK"),
        "Source": "PACKAGE_ZIP",
        "Package Path": str(zip_path),
        "Category": "zip",
        "Size": def_file_size(zip_path),
        "SHA256": def_sha256_file(zip_path),
        "Severity": "OK",
    })

    return zip_path, copied_rows


# ==================================================================================================
# def 05_MAIN
# ==================================================================================================
def def_main() -> None:
    if len(sys.argv) < 8:
        raise SystemExit("usage: py <base> <run_root> <run_dir> <input_dir> <supportive_dir> <config_dir> <via_root>")

    base = Path(sys.argv[1])
    run_root = Path(sys.argv[2])
    run_dir = Path(sys.argv[3])
    input_dir = Path(sys.argv[4])
    supportive_dir = Path(sys.argv[5])
    config_dir = Path(sys.argv[6])
    via_root = Path(sys.argv[7])

    run_dir.mkdir(parents=True, exist_ok=True)

    package_dir = run_dir / "VRN_PRODUCTION_PACKAGE_v061576"

    package_matrix, package_files = def_collect_assets(base, run_root, supportive_dir, config_dir)
    smoke_rows = def_smoke_test_input(input_dir)
    zip_path, copied_rows = def_build_package_zip(package_dir, package_files)

    required_errors = [r for r in package_matrix if r.get("Required") == "YES" and r.get("Severity") == "ERR"]
    smoke_err = [r for r in smoke_rows if r.get("Severity") == "ERR"]

    package_ok = len(required_errors) == 0 and zip_path.exists()
    smoke_ok = len(smoke_err) == 0

    hard_rules = [
        {"Status Lights": def_light("OK"), "Rule": "Future report formats never bypass Compatibility Gate", "Value": "ON", "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Rule": "Unknown broker/layout goes staging only", "Value": "ON", "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Rule": "No DB write in packaging/smoke", "Value": "YES", "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Rule": "No canonical mutation", "Value": "YES", "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Rule": "No SSOT mutation", "Value": "YES", "Severity": "OK"},
        {"Status Lights": def_light("WARN"), "Rule": "Rollback is manual insurance only", "Value": "NO AUTO ROLLBACK", "Severity": "WARN"},
    ]

    next_steps = [
        {"Status Lights": def_light("OK"), "Next Step": "Use ZIP as VRN command/docs package.", "Reason": "Package includes production reports, playbooks, launcher, compatibility assets.", "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Next Step": "Put different future reports into BASE\\input and rerun this script.", "Reason": "Smoke matrix will route each file to Compatibility Gate / staging review.", "Severity": "OK"},
        {"Status Lights": def_light("WARN"), "Next Step": "Do not bypass Compatibility Gate even if filename looks familiar.", "Reason": "Broker layouts can change.", "Severity": "WARN"},
    ]

    outputs = {
        "html": str(run_dir / "VRN_Package_Compatibility_Smoke_Report_v061576.html"),
        "json": str(run_dir / "vrn_package_compatibility_smoke_report_v061576.json"),
        "package_matrix_csv": str(run_dir / "vrn_package_matrix_v061576.csv"),
        "copied_files_csv": str(run_dir / "vrn_package_copied_files_v061576.csv"),
        "input_smoke_csv": str(run_dir / "vrn_future_input_smoke_matrix_v061576.csv"),
        "hard_rules_csv": str(run_dir / "vrn_future_gate_hard_rules_v061576.csv"),
        "next_steps_csv": str(run_dir / "vrn_package_next_steps_v061576.csv"),
        "package_dir": str(package_dir),
        "package_zip": str(zip_path),
    }

    def_write_csv(Path(outputs["package_matrix_csv"]), package_matrix)
    def_write_csv(Path(outputs["copied_files_csv"]), copied_rows)
    def_write_csv(Path(outputs["input_smoke_csv"]), smoke_rows)
    def_write_csv(Path(outputs["hard_rules_csv"]), hard_rules)
    def_write_csv(Path(outputs["next_steps_csv"]), next_steps)

    final_pass = package_ok and smoke_ok

    counts = {
        "Final": "PASS" if final_pass else "REVIEW",
        "Package OK": "YES" if package_ok else "NO",
        "Package Items": len(package_matrix),
        "Copied Files": len([r for r in copied_rows if r.get("Category") != "zip"]),
        "Input Files": len([r for r in smoke_rows if r.get("File")]),
        "Smoke OK": "YES" if smoke_ok else "NO",
        "Required Missing": len(required_errors),
        "Future Gate": "ON",
        "DB Write": "NO",
        "SSOT": "NO",
    }

    overview = [
        {"Status Lights": def_light("OK" if final_pass else "WARN"), "Gate": "PACKAGE_AND_SMOKE_PASS", "Value": "YES" if final_pass else "REVIEW", "Severity": "OK" if final_pass else "WARN"},
        {"Status Lights": def_light("OK" if package_ok else "ERR"), "Gate": "PACKAGE_OK", "Value": "YES" if package_ok else "NO", "Severity": "OK" if package_ok else "ERR"},
        {"Status Lights": def_light("OK" if smoke_ok else "ERR"), "Gate": "INPUT_SMOKE_OK", "Value": "YES" if smoke_ok else "NO", "Severity": "OK" if smoke_ok else "ERR"},
        {"Status Lights": def_light("OK"), "Gate": "FUTURE_GATE_POLICY", "Value": "ON", "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Gate": "DB_WRITE_THIS_RUN", "Value": "NO", "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Gate": "SSOT_MUTATION", "Value": "NO", "Severity": "OK"},
    ]

    result = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "system_pass": final_pass,
        "base": str(base),
        "input_dir": str(input_dir),
        "counts": counts,
        "outputs": outputs,
    }

    def_write_json(Path(outputs["json"]), result)
    def_write_html(
        Path(outputs["html"]),
        counts,
        [
            ("01 Overview", overview, None),
            ("02 打包包含哪些指令文件 / Package Matrix", package_matrix, None),
            ("03 Package Copied Files + ZIP", copied_rows, None),
            ("04 Future INPUT Compatibility Smoke Matrix", smoke_rows, None),
            ("05 Future Gate Hard Rules", hard_rules, None),
            ("06 Next Steps", next_steps, None),
        ],
    )

    print(json.dumps(result, ensure_ascii=False, indent=2))


# ==================================================================================================
# def ENTRYPOINT
# ==================================================================================================
if __name__ == "__main__":
    try:
        def_main()
    except Exception:
        print(traceback.format_exc())
        raise