# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import csv
import hashlib
import html
import importlib.util
import json
import os
import py_compile
import re
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any


VERSION = "VIS_VRN_MASTER_REGISTRY_BRIDGE_V0611_MANIFEST_RESTORE"


# ==================================================================================================
# def 01_COMMON
# ==================================================================================================
def def_status_lights(sev: str) -> str:
    s = str(sev or "").upper()
    if s in ["OK", "GREEN", "PASS", "TRUE"]:
        return "🟢 INPUT 🟢 DB 🟢 TRUST"
    if s in ["WARN", "YELLOW", "ORANGE", "REVIEW", "PARTIAL"]:
        return "🟢 INPUT 🟡 DB 🟡 TRUST"
    return "🔴 INPUT 🔴 DB 🔴 TRUST"


def def_sha256(path: str | Path) -> str:
    p = Path(path)
    if not p.exists():
        return ""
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def def_write_csv(path: str | Path, rows: list[dict]) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        rows = [{"empty_marker": ""}]
    fields = []
    for r in rows:
        for k in r.keys():
            if k not in fields:
                fields.append(k)
    with Path(path).open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


def def_write_json(path: str | Path, obj: Any) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def def_load_module_paths(path: str | Path) -> list[str]:
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(obj, list):
        return []
    return [str(x) for x in obj]


# ==================================================================================================
# def 02_SCAN
# ==================================================================================================
def def_scan_module(path: str) -> dict:
    p = Path(path)
    row = {
        "Status Lights": def_status_lights("ERR"),
        "File": str(p),
        "Name": p.name,
        "Exists": p.exists(),
        "Size": "",
        "SHA256": "",
        "AST": False,
        "Compile": False,
        "Import Safe": False,
        "Functions": 0,
        "Classes": 0,
        "Constants": 0,
        "Financial SSOT Like": False,
        "TW Official YFinance Like": False,
        "Risk": "RED",
        "Error": "",
        "Severity": "ERR",
    }

    if not p.exists():
        row["Error"] = "file not found"
        return row

    try:
        text = p.read_text(encoding="utf-8", errors="ignore")
        row["Size"] = len(text)
        row["SHA256"] = def_sha256(p)

        tree = ast.parse(text)
        row["AST"] = True

        funcs = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
        classes = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
        constants = []
        for n in ast.walk(tree):
            if isinstance(n, ast.Assign):
                for t in n.targets:
                    if isinstance(t, ast.Name) and t.id.isupper():
                        constants.append(t.id)

        row["Functions"] = len(funcs)
        row["Classes"] = len(classes)
        row["Constants"] = len(set(constants))

        low = text.lower()
        row["Financial SSOT Like"] = bool("financial" in low and ("ssot" in low or "alias" in low or "account" in low))
        row["TW Official YFinance Like"] = bool("yfinance" in low or ".tw" in low or ".two" in low or "twse" in low or "tpex" in low)

        compile(text, str(p), "exec")
        row["Compile"] = True

        try:
            spec = importlib.util.spec_from_file_location(p.stem, str(p))
            mod = importlib.util.module_from_spec(spec)
            if spec and spec.loader:
                spec.loader.exec_module(mod)
                row["Import Safe"] = True
        except Exception as e:
            row["Error"] = "import non-blocking: " + str(e)

        row["Risk"] = "GREEN" if row["Import Safe"] else "YELLOW"
        row["Severity"] = "OK" if row["Import Safe"] else "WARN"
        row["Status Lights"] = def_status_lights(row["Severity"])
        return row

    except Exception as e:
        row["Error"] = str(e)
        row["Risk"] = "RED"
        row["Severity"] = "ERR"
        row["Status Lights"] = def_status_lights("ERR")
        return row


def def_build_manifest(scan_rows: list[dict]) -> list[dict]:
    out = []
    for r in scan_rows:
        out.append({
            "file": r.get("File", ""),
            "name": r.get("Name", ""),
            "exists": bool(r.get("Exists")),
            "ast": bool(r.get("AST")),
            "compile": bool(r.get("Compile")),
            "import_safe": bool(r.get("Import Safe")),
            "sha256": r.get("SHA256", ""),
            "financial_ssot_like": bool(r.get("Financial SSOT Like")),
            "tw_official_yfinance_like": bool(r.get("TW Official YFinance Like")),
            "risk": r.get("Risk", ""),
        })
    return out


# ==================================================================================================
# def 03_PATCH_MANIFEST
# ==================================================================================================
def def_replace_source_manifest(text: str, manifest: list[dict]) -> str:
    manifest_py = repr(manifest)

    pattern = r"SOURCE_MODULE_MANIFEST\s*=\s*(\[[\s\S]*?\])\n\n# =================================================================================================="
    repl = "SOURCE_MODULE_MANIFEST = " + manifest_py + "\n\n# =================================================================================================="

    if re.search(pattern, text):
        return re.sub(pattern, repl, text, count=1)

    marker = 'YEAR_FALSE_POSITIVE = set(str(y) for y in range(2021, 2031))'
    if marker in text:
        return text.replace(marker, marker + "\nSOURCE_MODULE_MANIFEST = " + manifest_py)

    return "SOURCE_MODULE_MANIFEST = " + manifest_py + "\n" + text


def def_test_import(path: str | Path) -> dict:
    p = Path(path)
    out = {
        "AST": False,
        "Compile": False,
        "Import": False,
        "Health": False,
        "Source Modules": 0,
        "Financial SSOT Accounts": 0,
        "Error": "",
    }

    try:
        ast.parse(p.read_text(encoding="utf-8", errors="ignore"))
        out["AST"] = True
    except Exception:
        out["Error"] = traceback.format_exc()
        return out

    try:
        py_compile.compile(str(p), doraise=True)
        out["Compile"] = True
    except Exception:
        out["Error"] = traceback.format_exc()
        return out

    try:
        spec = importlib.util.spec_from_file_location(p.stem, str(p))
        mod = importlib.util.module_from_spec(spec)
        if spec and spec.loader:
            spec.loader.exec_module(mod)
        out["Import"] = True
        if hasattr(mod, "def_master_health"):
            h = mod.def_master_health()
            out["Health"] = isinstance(h, dict)
            out["Source Modules"] = h.get("source_modules", 0)
            out["Financial SSOT Accounts"] = h.get("financial_ssot_accounts", 0)
    except Exception:
        out["Error"] = traceback.format_exc()
        return out

    return out


# ==================================================================================================
# def 04_HTML
# ==================================================================================================
def def_normalize_header(c: str) -> str:
    c = str(c or "").replace("_", " ").strip()
    acr = {"ID", "DB", "API", "URL", "PDF", "CSV", "JSON", "HTML", "SSOT", "TWSE", "TPEX", "MOPS", "YFINANCE"}
    out = []
    for p in c.split():
        up = p.upper()
        if up in acr:
            out.append(up)
        elif re.search(r"[\u4e00-\u9fff]", p):
            out.append(p)
        else:
            out.append(p[:1].upper() + p[1:].lower())
    return " ".join(out)


def def_table_html(title: str, rows: list[dict]) -> str:
    if not rows:
        return f"<section class='card'><h2>{html.escape(title)}</h2><div class='empty'>No rows.</div></section>"
    fields = []
    for r in rows:
        for k in r.keys():
            if k not in fields:
                fields.append(k)
    th = "".join(f"<th>{html.escape(def_normalize_header(c))}</th>" for c in fields)
    trs = []
    for r in rows:
        tds = []
        for c in fields:
            v = "" if r.get(c) is None else str(r.get(c, ""))
            lc = c.lower()
            cls = "left" if any(k in lc for k in ["file", "path", "error", "reason"]) else "center"
            cls = "right" if any(k in lc for k in ["size", "count", "modules", "accounts"]) else cls
            tds.append(f"<td class='{cls}'>{html.escape(v)}</td>")
        trs.append("<tr>" + "".join(tds) + "</tr>")
    return f"<section class='card'><h2>{html.escape(title)}</h2><div class='table-wrap'><table><thead><tr>{th}</tr></thead><tbody>{''.join(trs)}</tbody></table></div></section>"


def def_write_html(path: str, result: dict, sections: list[tuple[str, list[dict]]]) -> None:
    css = """
:root{--bg:#07111f;--panel:#0d1b2f;--line:#1f3557;--text:#eef6ff;--muted:#9fb3c8;--cyan:#42d9ff}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at top,#142a45,#07111f 52%,#050914);font-family:Segoe UI,'Microsoft JhengHei',Arial,sans-serif;color:var(--text);font-size:12px}
header{padding:24px 32px;border-bottom:1px solid var(--line);position:sticky;top:0;background:rgba(7,17,31,.94);backdrop-filter:blur(12px);z-index:10}
h1{margin:0;font-size:24px}.sub{margin-top:8px;color:var(--muted)}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:14px;padding:20px 32px}
.kpi{background:linear-gradient(180deg,rgba(66,217,255,.12),rgba(13,27,47,.92));border:1px solid var(--line);border-radius:18px;padding:16px;box-shadow:0 12px 28px rgba(0,0,0,.25);transition:.15s}
.kpi:hover{transform:translateY(-2px) scale(1.01);border-color:var(--cyan)}.kpi .v{font-size:26px;font-weight:850}.kpi .k{color:var(--muted);margin-top:6px}
main{padding:0 32px 32px}.card{background:rgba(13,27,47,.92);border:1px solid var(--line);border-radius:18px;margin:18px 0;padding:18px}
h2{margin:0 0 12px}.table-wrap{overflow:auto;max-height:76vh;border:1px solid var(--line);border-radius:14px}
table{border-collapse:collapse;min-width:100%;width:max-content}th{position:sticky;top:0;background:#132541;color:#fff;text-align:center;vertical-align:top;padding:10px;border-bottom:1px solid var(--line);white-space:normal}
td{padding:8px 10px;border-bottom:1px solid rgba(255,255,255,.08);border-right:1px solid rgba(255,255,255,.05);vertical-align:top;text-align:center;max-width:620px;white-space:normal;word-break:break-word}
td.left{text-align:left}td.right{text-align:right;font-variant-numeric:tabular-nums}tr:hover td{background:rgba(66,217,255,.07)}
footer{padding:18px 32px;color:var(--muted);border-top:1px solid var(--line)}
"""
    card_html = "<div class='grid'>" + "".join(
        f"<div class='kpi'><div class='v'>{html.escape(str(v))}</div><div class='k'>{html.escape(str(k))}</div></div>"
        for k, v in result.get("counts", {}).items()
    ) + "</div>"
    sec_html = "\n".join(def_table_html(t, r) for t, r in sections)
    doc = f"""<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><title>VIS VRN Master Bridge Manifest Restore</title><style>{css}</style></head>
<body><header><h1>VIS · VRN Master Registry Bridge Manifest Restore</h1>
<div class="sub">source_modules=0 repair · Python repr manifest · import seal · health seal</div></header>
{card_html}<main>{sec_html}</main><footer>Veritas Intelligence Analytics</footer></body></html>"""
    Path(path).write_text(doc, encoding="utf-8")


# ==================================================================================================
# def 05_MAIN
# ==================================================================================================
def def_main():
    if len(sys.argv) < 6:
        raise SystemExit("usage: py <target_module> <module_json> <run_dir> <config_dir> <support_root>")

    target_module = Path(sys.argv[1])
    module_json = Path(sys.argv[2])
    run_dir = Path(sys.argv[3])
    config_dir = Path(sys.argv[4])
    support_root = Path(sys.argv[5])

    run_dir.mkdir(parents=True, exist_ok=True)
    config_dir.mkdir(parents=True, exist_ok=True)

    module_paths = def_load_module_paths(module_json)
    scan_rows = [def_scan_module(p) for p in module_paths]
    manifest = def_build_manifest(scan_rows)

    before = def_test_import(target_module)

    backup = str(target_module) + ".bak_manifest_restore_" + datetime.now().strftime("%Y%m%d_%H%M%S")
    target_text = target_module.read_text(encoding="utf-8", errors="ignore")
    Path(backup).write_text(target_text, encoding="utf-8")

    patched = def_replace_source_manifest(target_text, manifest)
    target_module.write_text(patched, encoding="utf-8")

    after = def_test_import(target_module)

    source_compile_ok = sum(1 for r in scan_rows if r.get("AST") and r.get("Compile"))
    source_import_safe = sum(1 for r in scan_rows if r.get("Import Safe"))
    financial_like = sum(1 for r in scan_rows if r.get("Financial SSOT Like"))
    tw_like = sum(1 for r in scan_rows if r.get("TW Official YFinance Like"))

    final_pass = bool(
        after.get("AST")
        and after.get("Compile")
        and after.get("Import")
        and after.get("Health")
        and after.get("Source Modules") == len(module_paths)
    )

    overview = [
        {"Status Lights": def_status_lights("OK"), "Gate": "MODULE_JSON", "Value": str(module_json), "Severity": "OK"},
        {"Status Lights": def_status_lights("OK"), "Gate": "SOURCE_MODULES_LISTED", "Value": len(module_paths), "Severity": "OK"},
        {"Status Lights": def_status_lights("OK"), "Gate": "MANIFEST_RESTORED", "Value": len(manifest), "Severity": "OK"},
        {"Status Lights": def_status_lights("OK"), "Gate": "SOURCE_AST_COMPILE_OK", "Value": f"{source_compile_ok}/{len(module_paths)}", "Severity": "OK"},
        {"Status Lights": def_status_lights("OK"), "Gate": "SOURCE_IMPORT_SAFE", "Value": source_import_safe, "Severity": "OK"},
        {"Status Lights": def_status_lights("OK"), "Gate": "FINANCIAL_SSOT_LIKE_MODULES", "Value": financial_like, "Severity": "OK"},
        {"Status Lights": def_status_lights("OK"), "Gate": "TW_OFFICIAL_YFINANCE_LIKE_MODULES", "Value": tw_like, "Severity": "OK"},
        {"Status Lights": def_status_lights("OK" if before.get("Import") else "WARN"), "Gate": "BEFORE_IMPORT", "Value": before.get("Import"), "Severity": "OK" if before.get("Import") else "WARN"},
        {"Status Lights": def_status_lights("OK" if after.get("Import") else "ERR"), "Gate": "AFTER_IMPORT", "Value": after.get("Import"), "Severity": "OK" if after.get("Import") else "ERR"},
        {"Status Lights": def_status_lights("OK" if after.get("Health") else "ERR"), "Gate": "AFTER_HEALTH", "Value": after.get("Health"), "Severity": "OK" if after.get("Health") else "ERR"},
        {"Status Lights": def_status_lights("OK" if after.get("Source Modules") == len(module_paths) else "ERR"), "Gate": "AFTER_SOURCE_MODULES", "Value": after.get("Source Modules"), "Severity": "OK" if after.get("Source Modules") == len(module_paths) else "ERR"},
        {"Status Lights": def_status_lights("OK"), "Gate": "BACKUP", "Value": backup, "Severity": "OK"},
    ]

    error_rows = [
        {
            "Status Lights": def_status_lights("WARN" if before.get("Error") else "OK"),
            "Stage": "Before",
            "Error": str(before.get("Error", ""))[-4000:],
            "Severity": "WARN" if before.get("Error") else "OK",
        },
        {
            "Status Lights": def_status_lights("ERR" if after.get("Error") else "OK"),
            "Stage": "After",
            "Error": str(after.get("Error", ""))[-4000:],
            "Severity": "ERR" if after.get("Error") else "OK",
        },
    ]

    html_path = str(run_dir / "VIS_VRN_MasterRegistryBridge_v0611_Manifest_Restore_Report.html")
    json_path = str(run_dir / "vis_vrn_master_registry_bridge_v0611_manifest_restore.json")
    overview_csv = str(run_dir / "vis_vrn_master_registry_bridge_v0611_manifest_restore_overview.csv")
    scan_csv = str(run_dir / "vis_vrn_master_registry_bridge_v0611_manifest_restore_scan.csv")
    error_csv = str(run_dir / "vis_vrn_master_registry_bridge_v0611_manifest_restore_errors.csv")
    rule_lock = str(config_dir / "VIS_VRN_MasterRegistryBridge_v0611_ManifestRestore_RuleLock.json")

    result = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "system_pass": final_pass,
        "counts": {
            "System Pass": final_pass,
            "Source Modules": len(module_paths),
            "Manifest Restored": len(manifest),
            "After Import": after.get("Import"),
            "After Health": after.get("Health"),
            "After Source Modules": after.get("Source Modules"),
            "Financial SSOT Like": financial_like,
            "TW YFinance Like": tw_like,
        },
        "outputs": {
            "html": html_path,
            "json": json_path,
            "target_module": str(target_module),
            "backup": backup,
            "overview_csv": overview_csv,
            "scan_csv": scan_csv,
            "error_csv": error_csv,
            "rule_lock_json": rule_lock,
        },
        "before": before,
        "after": after,
        "policy": {
            "restore_manifest_only": True,
            "python_repr_manifest": True,
            "old_source_modules_untouched": True,
            "canonical_mutation": False,
            "stable_mutation": False,
            "no_fake_fill": True,
        },
    }

    def_write_csv(overview_csv, overview)
    def_write_csv(scan_csv, scan_rows)
    def_write_csv(error_csv, error_rows)
    def_write_json(json_path, result)
    def_write_json(rule_lock, {
        "version": VERSION,
        "rules": [
            "Restore SOURCE_MODULE_MANIFEST into VIS_VRN_MasterRegistryBridge_v0611.py.",
            "Use Python repr manifest, not JSON literal, to avoid true/false NameError.",
            "Preserve 9 source modules.",
            "Require after import true.",
            "Require after health true.",
            "Require after source_modules equals listed module count.",
            "No canonical mutation.",
            "No stable mutation."
        ],
    })

    def_write_html(html_path, result, [
        ("01 Overview", overview),
        ("02 Source Module Scan", scan_rows),
        ("03 Error Diagnosis", error_rows),
    ])

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        def_main()
    except Exception:
        print(traceback.format_exc())
        raise