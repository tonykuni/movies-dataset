from __future__ import annotations

import argparse
import ast
import json
import py_compile
import traceback
from pathlib import Path
from datetime import datetime

# def HELPERS
def def_now() -> str:
    return datetime.now().isoformat()

def def_read_text(path_value: Path) -> str:
    try:
        return path_value.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path_value.read_text(encoding="utf-8", errors="replace")

def def_write_json(path_value: Path, payload):
    path_value.parent.mkdir(parents=True, exist_ok=True)
    path_value.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

def def_write_html(path_value: Path, rows):
    html_rows = []
    for row in rows:
        html_rows.append(
            "<tr>"
            f"<td>{row.get('file','')}</td>"
            f"<td>{row.get('kind','')}</td>"
            f"<td>{row.get('status','')}</td>"
            f"<td>{row.get('detail','')}</td>"
            "</tr>"
        )
    html = f"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8" />
<title>VIA Panorama Patch Plan</title>
<style>
body {{ font-family: Arial, sans-serif; margin: 24px; background: #f7f8fb; color: #1f2937; }}
.card {{ background: #fff; border-radius: 12px; padding: 16px; margin-bottom: 16px; box-shadow: 0 2px 8px rgba(0,0,0,.08); }}
table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
th, td {{ border: 1px solid #d1d5db; padding: 8px; text-align: left; vertical-align: top; }}
th {{ background: #eef2ff; }}
</style>
</head>
<body>
<div class="card">
<h1>VIA Panorama Patch Plan</h1>
<p>Generated: {def_now()}</p>
</div>
<div class="card">
<table>
<thead>
<tr><th>File</th><th>Kind</th><th>Status</th><th>Detail</th></tr>
</thead>
<tbody>
{''.join(html_rows)}
</tbody>
</table>
</div>
</body>
</html>"""
    path_value.write_text(html, encoding="utf-8")

# def AST ANALYSIS
def def_analyze_python_file(file_path: Path):
    result = {
        "file": str(file_path),
        "kind": "python",
        "status": "OK",
        "detail": "",
        "import_insert_after_line": None,
        "main_guard_line": None,
        "functions": [],
        "errors": [],
    }
    try:
        source = def_read_text(file_path)
        tree = ast.parse(source, filename=str(file_path))
        compile(tree, str(file_path), "exec")

        import_lines = []
        for node in tree.body:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                import_lines.append(getattr(node, "end_lineno", getattr(node, "lineno", None)))

        if import_lines:
            result["import_insert_after_line"] = max(line for line in import_lines if line is not None)

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                result["functions"].append({
                    "name": node.name,
                    "line": node.lineno,
                    "has_ctx": any(arg.arg == "ctx" for arg in node.args.args),
                })
            if isinstance(node, ast.If):
                test_src = ast.unparse(node.test) if hasattr(ast, "unparse") else ""
                if "__name__" in test_src and "__main__" in test_src:
                    result["main_guard_line"] = node.lineno

        try:
            py_compile.compile(str(file_path), doraise=True)
        except Exception as exc:
            result["status"] = "WARN"
            result["errors"].append("py_compile: " + str(exc))

        result["detail"] = f"imports={result['import_insert_after_line']} main_guard={result['main_guard_line']} funcs={len(result['functions'])}"
        return result

    except Exception as exc:
        result["status"] = "ERROR"
        result["detail"] = str(exc)
        result["errors"].append(traceback.format_exc())
        return result

# def INVENTORY
def def_scan_project(base_root: Path):
    rows = []
    for path_value in sorted(base_root.rglob("*")):
        if not path_value.is_file():
            continue
        suffix = path_value.suffix.lower()
        if suffix == ".py":
            rows.append(def_analyze_python_file(path_value))
        elif suffix in [".ps1", ".psm1", ".json", ".md", ".html", ".log"]:
            rows.append({
                "file": str(path_value),
                "kind": suffix.lstrip("."),
                "status": "INDEXED",
                "detail": "non-python indexed only",
            })
    return rows

# def MAIN
def def_main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-root", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--compat-shim", action="store_true")
    args = parser.parse_args()

    base_root = Path(args.base_root)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not base_root.exists():
        raise FileNotFoundError(f"Base root not found: {base_root}")

    rows = def_scan_project(base_root)

    json_path = output_dir / "VIA_Panorama_PatchPlan.json"
    html_path = output_dir / "VIA_Panorama_PatchPlan.html"
    summary_path = output_dir / "VIA_Panorama_Summary.json"

    def_write_json(json_path, rows)
    def_write_html(html_path, rows)

    summary = {
        "ok": True,
        "generated_at": def_now(),
        "base_root": str(base_root),
        "output_dir": str(output_dir),
        "dry_run": args.dry_run,
        "execute": args.execute,
        "compat_shim": args.compat_shim,
        "total_rows": len(rows),
        "python_rows": len([r for r in rows if r.get("kind") == "python"]),
        "error_rows": len([r for r in rows if r.get("status") == "ERROR"]),
        "json_path": str(json_path),
        "html_path": str(html_path),
    }
    def_write_json(summary_path, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(def_main())
