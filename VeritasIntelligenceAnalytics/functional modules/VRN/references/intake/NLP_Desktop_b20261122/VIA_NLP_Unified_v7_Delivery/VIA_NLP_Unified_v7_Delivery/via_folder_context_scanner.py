from __future__ import annotations

import csv
import hashlib
import html
import json
import os
import re
import textwrap
import uuid
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

EXCLUDED_DIRS = {".git", ".hg", ".svn", "node_modules", "__pycache__", ".venv", "venv", "env", "runs", "folder_scans", "VIA_TEST_RESULTS", "test_output_v5", ".idea", ".vs", "dist", "build"}
MAX_CONTENT_BYTES = 2 * 1024 * 1024
CODE_EXTENSIONS = {".py", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx", ".java", ".go", ".rs", ".c", ".cpp", ".h", ".hpp", ".cs", ".php", ".rb", ".swift", ".kt", ".ps1", ".psm1", ".sh", ".bat", ".cmd", ".sql"}
TEXT_EXTENSIONS = {".txt", ".md", ".markdown", ".rst", ".html", ".htm", ".css", ".scss", ".json", ".jsonl", ".csv", ".tsv", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf", ".xml", ".env", ".log"} | CODE_EXTENSIONS
ARCHIVE_EXTENSIONS = {".zip", ".whl", ".jar", ".tar", ".gz", ".7z", ".rar"}
DOCUMENT_EXTENSIONS = {".pdf", ".docx", ".pptx", ".xlsx", ".odt", ".ods", ".odp"}
DATA_EXTENSIONS = {".csv", ".tsv", ".json", ".jsonl", ".parquet", ".sqlite", ".db", ".xlsx"}
MANIFEST_NAMES = {"requirements.txt", "requirements-envcheck.txt", "pyproject.toml", "package.json", "package-lock.json", "pnpm-lock.yaml", "uv.toml", "dockerfile", "docker-compose.yml", "docker-compose.yaml", "makefile", "readme.md", "license"}
READER_PROFILES = {
    "source": {"engine_ids": ["VIA-ENG-006", "VIA-ENG-012", "VIA-ENG-015", "VIA-ENG-016"], "tools": ["static AST/import inventory", "VIA_MultiLanguageToolConvergence", "via_engine_standardizer", "Veritas semantic evidence"]},
    "html": {"engine_ids": ["VIA-ENG-002", "VIA-ENG-006"], "tools": ["Invoke-VIA-SuperHtmlParser", "static DOM/JS/CSS parser"]},
    "document": {"engine_ids": ["VIA-ENG-003", "VIA-ENG-013"], "tools": ["GenericLayoutEngine", "VIA_PDFPlumberPlusEngine/poppler safe adapter"]},
    "text": {"engine_ids": ["VIA-ENG-004", "VIA-ENG-005", "VIA-ENG-017", "VIA-ENG-018", "VIA-ENG-020"], "tools": ["VIA v5 NLP", "discussion reconstruction", "MarkdownEditingEngine", "SSOT lexicon", "evidence summary"]},
    "structured": {"engine_ids": ["VIA-ENG-003", "VIA-ENG-004", "VIA-ENG-014", "VIA-ENG-016"], "tools": ["GenericLayout schema adapter", "NLP field projection", "VAKE data knowledge ingestion", "Veritas semantic evidence"]},
    "archive": {"engine_ids": ["VIA-ENG-012", "VIA-ENG-015", "VIA-ENG-016"], "tools": ["safe archive manifest reader", "canonical contract standardizer", "Veritas package evidence"]},
    "asset": {"engine_ids": ["VIA-ENG-003"], "tools": ["layout/asset metadata adapter"]},
    "other": {"engine_ids": ["VIA-ENG-008"], "tools": ["governance review gate"]},
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_text(path: Path, limit: int = MAX_CONTENT_BYTES) -> str:
    raw = path.read_bytes()[:limit]
    for encoding in ("utf-8", "utf-8-sig", "utf-16", "big5", "cp950", "latin-1"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def safe_label(value: str, limit: int = 150) -> str:
    value = re.sub(r"\s+", " ", value).strip()
    return value[:limit] + ("…" if len(value) > limit else "")


def format_for(path: Path) -> str:
    ext = path.suffix.casefold()
    name = path.name.casefold()
    if name in {"dockerfile", "makefile"}:
        return name
    if ext in CODE_EXTENSIONS:
        return f"{ext[1:].upper()} source"
    if ext in {".md", ".markdown", ".rst"}:
        return "Markdown/documentation"
    if ext in {".html", ".htm"}:
        return "HTML/UI"
    if ext in {".json", ".jsonl", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf", ".env", ".xml"}:
        return "configuration/structured data"
    if ext in DATA_EXTENSIONS:
        return "dataset/table"
    if ext in {".txt", ".log"}:
        return "plain text/log"
    if ext in DOCUMENT_EXTENSIONS:
        return f"{ext[1:].upper()} document"
    if ext in ARCHIVE_EXTENSIONS:
        return "archive/package"
    if ext in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".ico"}:
        return "image/asset"
    return ext[1:].upper() + " file" if ext else "extensionless file"


def role_for(path: Path, fmt: str) -> str:
    name = path.name.casefold()
    parts = {part.casefold() for part in path.parts}
    if name in MANIFEST_NAMES or any(token in name for token in ("requirements", "pyproject", "package.json", "uv.toml", "dockerfile")):
        return "environment/manifest"
    if any(token in name for token in ("test", "spec", "fixture")) or any(token in parts for token in ("tests", "test", "spec", "fixtures")):
        return "test/verification"
    if any(token in name for token in ("readme", "license", "changelog", "handover", "guide", "docs")) or "docs" in parts:
        return "documentation"
    if path.suffix.casefold() in CODE_EXTENSIONS:
        if any(token in name for token in ("adapter", "plugin", "engine", "module", "service")):
            return "engine/adapter"
        if any(token in name for token in ("run", "invoke", "launch", "start", "main", "app")):
            return "entrypoint/script"
        return "source/module"
    if path.suffix.casefold() in DATA_EXTENSIONS:
        return "data/dataset"
    if path.suffix.casefold() in ARCHIVE_EXTENSIONS:
        return "archive/package"
    if path.suffix.casefold() in DOCUMENT_EXTENSIONS:
        return "document"
    if fmt == "HTML/UI":
        return "ui/asset"
    return "asset/other"


def reader_profile(path: Path, fmt: str, role: str) -> dict[str, list[str]]:
    extension = path.suffix.casefold()
    if extension in CODE_EXTENSIONS:
        profile = READER_PROFILES["source"]
    elif extension in {".html", ".htm"}:
        profile = READER_PROFILES["html"]
    elif extension in DOCUMENT_EXTENSIONS:
        profile = READER_PROFILES["document"]
    elif extension in ARCHIVE_EXTENSIONS:
        profile = READER_PROFILES["archive"]
    elif extension in {".json", ".jsonl", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf", ".xml", ".csv", ".tsv"}:
        profile = READER_PROFILES["structured"]
    elif extension in TEXT_EXTENSIONS:
        profile = READER_PROFILES["text"]
    elif extension in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".ico"}:
        profile = READER_PROFILES["asset"]
    else:
        profile = READER_PROFILES["other"]
    return {"engine_ids": list(profile["engine_ids"]), "tools": list(profile["tools"])}


def extract_imports(text: str, path: Path) -> list[str]:
    values: list[str] = []
    patterns = [
        r"^\s*import\s+([A-Za-z0-9_./-]+)",
        r"^\s*from\s+([A-Za-z0-9_./-]+)\s+import",
        r"require\([\"']([^\"']+)",
        r"from\s+[\"']([^\"']+)[\"']",
        r"Import-Module\s+([A-Za-z0-9_.\\/-]+)",
        r"^\s*#include\s*[<\"]([^>\"]+)",
    ]
    for pattern in patterns:
        values.extend(re.findall(pattern, text, re.I | re.M))
    result = []
    for value in values:
        clean = value.replace("\\", "/").strip()
        if clean and clean not in result:
            result.append(clean)
    return result[:40]


def parse_docx(path: Path) -> dict[str, Any]:
    try:
        with zipfile.ZipFile(path) as archive:
            names = archive.namelist()
            xml = archive.read("word/document.xml") if "word/document.xml" in names else b""
        root = ElementTree.fromstring(xml) if xml else None
        texts = []
        if root is not None:
            for node in root.iter():
                if node.tag.endswith("}t") and node.text:
                    texts.append(node.text)
        return {"status": "parsed", "summary": safe_label(" ".join(texts[:80])), "detail": f"OOXML members={len(names)}", "imports": [], "headings": []}
    except Exception as exc:
        return {"status": "error", "summary": "DOCX parse failed", "detail": f"{type(exc).__name__}: {exc}", "imports": [], "headings": []}


def parse_archive(path: Path) -> dict[str, Any]:
    try:
        if path.suffix.casefold() == ".zip" or zipfile.is_zipfile(path):
            with zipfile.ZipFile(path) as archive:
                members = archive.namelist()
            return {"status": "detected_only", "summary": safe_label("archive/package: " + ", ".join(members[:8])), "detail": f"members={len(members)}; source not extracted or executed", "imports": [], "headings": members[:20]}
    except Exception as exc:
        return {"status": "error", "summary": "Archive listing failed", "detail": f"{type(exc).__name__}: {exc}", "imports": [], "headings": []}
    return {"status": "detected_only", "summary": "binary archive/package; static listing unavailable", "detail": "source not extracted or executed", "imports": [], "headings": []}


def parse_content(path: Path, fmt: str, size: int) -> dict[str, Any]:
    if path.suffix.casefold() in ARCHIVE_EXTENSIONS:
        return parse_archive(path)
    if path.suffix.casefold() == ".docx":
        return parse_docx(path)
    if path.suffix.casefold() in {".pdf", ".pptx", ".xlsx", ".odt", ".ods", ".odp", ".sqlite", ".db", ".parquet"}:
        return {"status": "detected_only", "summary": f"{fmt}; binary structure detected", "detail": "format detected; parser adapter can be attached; source not executed", "imports": [], "headings": []}
    if size > MAX_CONTENT_BYTES:
        return {"status": "detected_only", "summary": f"{fmt}; content exceeds safe preview limit", "detail": f"preview_limit={MAX_CONTENT_BYTES} bytes; hash retained", "imports": [], "headings": []}
    try:
        text = read_text(path)
    except Exception as exc:
        return {"status": "error", "summary": "read failed", "detail": f"{type(exc).__name__}: {exc}", "imports": [], "headings": []}
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    headings = []
    if path.suffix.casefold() in {".md", ".markdown", ".rst"}:
        headings = [safe_label(line.lstrip("# ")) for line in lines if line.startswith("#")][:12]
    elif path.suffix.casefold() in {".html", ".htm"}:
        headings = [safe_label(item) for item in re.findall(r"<(?:title|h[1-6])[^>]*>(.*?)</(?:title|h[1-6])>", text, re.I | re.S)][:12]
        headings = [re.sub(r"<[^>]+>", "", item) for item in headings]
    elif path.suffix.casefold() in CODE_EXTENSIONS:
        headings = [safe_label(item) for item in re.findall(r"^\s*(?:class|def|function|export\s+(?:default\s+)?function|interface|struct|enum)\s+[^\n{(:]+", text, re.I | re.M)][:12]
    elif path.suffix.casefold() in {".json", ".yaml", ".yml", ".toml"}:
        headings = [safe_label(item) for item in re.findall(r"^\s*[\"']?([A-Za-z_][A-Za-z0-9_.-]*)[\"']?\s*[:=]", text, re.M)][:12]
    if path.suffix.casefold() in {".json", ".yaml", ".yml", ".toml"}:
        summary = f"{fmt}; keys/sections: {', '.join(headings[:8])}" if headings else f"{fmt}; structured content"
    elif path.suffix.casefold() in {".csv", ".tsv"}:
        first = lines[0] if lines else ""
        summary = f"{fmt}; columns: {safe_label(first, 180)}"
    else:
        summary = safe_label(" ".join(lines[:3])) or f"{fmt}; empty text"
    return {
        "status": "parsed",
        "summary": summary,
        "detail": f"lines={len(text.splitlines())}; chars={len(text)}",
        "imports": extract_imports(text, path) if path.suffix.casefold() in CODE_EXTENSIONS else [],
        "headings": headings,
        "language": "zh-Hant" if len(re.findall(r"[\u3400-\u9fff]", text)) > len(re.findall(r"[A-Za-z]", text)) else "en/mixed",
    }


def dependency_ids(rows: list[dict[str, Any]]) -> None:
    by_stem: dict[str, list[str]] = defaultdict(list)
    for row in rows:
        stem = Path(row["relative_path"]).stem.casefold()
        by_stem[stem].append(row["module_id"])
        by_stem[Path(row["relative_path"]).name.casefold()].append(row["module_id"])
    for row in rows:
        dependencies = []
        for imported in row.get("imports", []):
            key = Path(imported.split(".")[-1]).stem.casefold()
            for module_id in by_stem.get(key, []):
                if module_id != row["module_id"] and module_id not in dependencies:
                    dependencies.append(module_id)
        row["dependency_module_ids"] = dependencies[:30]


def scan_folder(root: str | Path, output_dir: str | Path, max_files: int = 5000) -> dict[str, Any]:
    root_path = Path(root).expanduser().resolve()
    output = Path(output_dir).expanduser().resolve()
    if not root_path.is_dir():
        raise ValueError(f"root is not a directory: {root_path}")
    output.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    scanned = 0
    for current, dirnames, filenames in os.walk(root_path):
        dirnames[:] = sorted(name for name in dirnames if name not in EXCLUDED_DIRS and not name.startswith("."))
        for filename in sorted(filenames):
            if scanned >= max_files:
                break
            path = Path(current) / filename
            try:
                stat = path.stat()
                relative = path.relative_to(root_path).as_posix()
                fmt = format_for(path)
                role = role_for(path, fmt)
                readers = reader_profile(path, fmt, role)
                parsed = parse_content(path, fmt, stat.st_size)
                rows.append({
                    "module_id": f"VIA-MOD-{len(rows) + 1:04d}",
                    "relative_path": relative,
                    "absolute_path": str(path),
                    "name": filename,
                    "parent_context": str(Path(relative).parent).replace(".", "root"),
                    "format": fmt,
                    "role": role,
                    "reader_engine_ids": readers["engine_ids"],
                    "reader_tools": readers["tools"],
                    "bytes": stat.st_size,
                    "sha256": sha256_file(path),
                    "status": parsed.get("status", "detected_only"),
                    "function_summary": parsed.get("summary", ""),
                    "detail": parsed.get("detail", ""),
                    "headings": parsed.get("headings", [])[:12],
                    "imports": parsed.get("imports", [])[:40],
                    "language": parsed.get("language", "binary/unknown"),
                    "risk_policy": "static_review_only" if path.suffix.casefold() in CODE_EXTENSIONS or path.suffix.casefold() in ARCHIVE_EXTENSIONS else "read_only",
                })
                scanned += 1
            except Exception as exc:
                errors.append({"path": str(path), "error": f"{type(exc).__name__}: {exc}"})
        if scanned >= max_files:
            break
    dependency_ids(rows)
    formats = Counter(row["format"] for row in rows)
    roles = Counter(row["role"] for row in rows)
    statuses = Counter(row["status"] for row in rows)
    reader_engines = Counter(engine_id for row in rows for engine_id in row.get("reader_engine_ids", []))
    reader_tools = Counter(tool for row in rows for tool in row.get("reader_tools", []))
    folder_counts = Counter(str(Path(row["relative_path"]).parent).replace(".", "root") for row in rows)
    result = {
        "schema": "VIA_FOLDER_CONTEXT_SCAN/1.0",
        "scan_id": output.name,
        "root": str(root_path),
        "output_dir": str(output),
        "source_policy": {"read_only": True, "source_write": False, "source_delete": False, "code_execution": False, "network": False, "package_install": False},
        "limits": {"max_files": max_files, "scanned_files": scanned, "max_content_preview_bytes": MAX_CONTENT_BYTES},
        "summary": {"file_count": len(rows), "folder_count": len(folder_counts), "formats": dict(formats), "roles": dict(roles), "statuses": dict(statuses), "reader_engines": dict(reader_engines), "reader_tools": dict(reader_tools), "errors": len(errors)},
        "folders": [{"folder": folder, "file_count": count} for folder, count in folder_counts.most_common()],
        "modules": rows,
        "errors": errors,
    }
    write_outputs(result, output)
    return result


def write_workflow_mermaid(result: dict[str, Any], path: Path) -> None:
    summary = result["summary"]
    lines = ["flowchart LR", "    A[\"System Folder\nRead-only input\"] --> B[\"VIA-FLD-001\nInventory & hash\"]", "    B --> C[\"VIA-FLD-002\nFormat & role detection\"]", "    C --> D[\"VIA-FLD-003\nSafe structure parsing\"]", "    D --> E[\"VIA-FLD-004\nDependency/context graph\"]", "    E --> F[\"VIA-FLD-005\nNumbered module matrix\"]", "    F --> G[\"VIA-FLD-006\nWorkflow + status outputs\"]"]
    for index, (fmt, count) in enumerate(sorted(summary["formats"].items()), 1):
        node = f"FMT{index}"
        label = fmt.replace('"', "'")[:42]
        lines.append(f"    C --> {node}[\"{label}\n{count} files\"]")
    for index, (role, count) in enumerate(sorted(summary["roles"].items()), 1):
        node = f"ROLE{index}"
        label = role.replace('"', "'")[:42]
        lines.append(f"    D --> {node}[\"{label}\\n{count} files\"]")
    for index, (engine_id, count) in enumerate(sorted(summary.get("reader_engines", {}).items()), 1):
        node = f"ENG{index}"
        lines.append(f"    D --> {node}[\"{engine_id}\\nreader coverage={count}\"]")
    for row in result["modules"][:80]:
        node = "M" + row["module_id"].replace("-", "")
        label = f"{row['module_id']}\\n{row['name'][:28]}\\n{row['status']}".replace('"', "'")
        lines.append(f"    F --> {node}[\"{label}\"]")
    lines.extend(["    classDef safe fill:#eaf7ee,stroke:#57956a,color:#173b24", "    classDef review fill:#fff6db,stroke:#c99a29,color:#5b4300", "    classDef binary fill:#eef3f8,stroke:#91a3b5,color:#283a4d"])
    for row in result["modules"][:80]:
        node = "M" + row["module_id"].replace("-", "")
        class_name = "safe" if row["status"] == "parsed" else "binary" if row["status"] == "detected_only" else "review"
        lines.append(f"    class {node} {class_name}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_matrix_csv(result: dict[str, Any], path: Path) -> None:
    fields = ["module_id", "relative_path", "parent_context", "format", "role", "reader_engine_ids", "reader_tools", "status", "bytes", "sha256", "function_summary", "detail", "language", "risk_policy", "dependency_module_ids", "imports"]
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in result["modules"]:
            item = dict(row)
            item["dependency_module_ids"] = ",".join(row.get("dependency_module_ids", []))
            item["imports"] = ",".join(row.get("imports", []))
            item["reader_engine_ids"] = ",".join(row.get("reader_engine_ids", []))
            item["reader_tools"] = ",".join(row.get("reader_tools", []))
            writer.writerow({field: item.get(field, "") for field in fields})


def write_matrix_markdown(result: dict[str, Any], path: Path) -> None:
    lines = [f"# VIA Folder Context Matrix — `{result['root']}`", "", f"- Scan ID: `{result['scan_id']}`", f"- Files: `{result['summary']['file_count']}`", f"- Folders: `{result['summary']['folder_count']}`", "- Policy: read-only; source is not modified or executed.", "", "## Numbered Module Matrix", "", "| Module ID | Relative Path | Format | Role | Reader Engines | Tools | Status | Function Summary | Dependencies |", "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for row in result["modules"]:
        values = [row["module_id"], row["relative_path"], row["format"], row["role"], ", ".join(row.get("reader_engine_ids", [])), ", ".join(row.get("reader_tools", [])), row["status"], row["function_summary"], ", ".join(row.get("dependency_module_ids", []))]
        lines.append("| " + " | ".join(str(value).replace("|", "\\|").replace("\n", " ") for value in values) + " |")
    lines += ["", "## Summary", "", f"- Formats: `{json.dumps(result['summary']['formats'], ensure_ascii=False)}`", f"- Roles: `{json.dumps(result['summary']['roles'], ensure_ascii=False)}`", f"- Statuses: `{json.dumps(result['summary']['statuses'], ensure_ascii=False)}`", f"- Errors: `{result['summary']['errors']}`", "", "## Interpretation", "", "The matrix is a static evidence map. `parsed` means a safe text/structure preview was extracted; `detected_only` means the format was identified without executing or fully unpacking source; `error` requires review."]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_matrix_html(result: dict[str, Any], path: Path) -> None:
    esc = html.escape
    rows = "".join("<tr>" + "".join(f"<td>{esc(str(row.get(field, '')))}</td>" for field in ("module_id", "relative_path", "format", "role", "reader_engine_ids", "reader_tools", "status", "function_summary", "dependency_module_ids")) + "</tr>" for row in result["modules"])
    path.write_text(f'''<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>VIA Folder Context Matrix</title><style>body{{font-family:system-ui,"Noto Sans CJK TC",sans-serif;background:#f4f7fb;color:#142033;margin:0;padding:24px}}main{{max-width:1800px;margin:auto;background:#fff;padding:24px;border-radius:16px}}table{{border-collapse:collapse;width:100%;font-size:13px}}th,td{{border:1px solid #d6e0ea;padding:8px;text-align:left;vertical-align:top}}th{{background:#edf2f7}}code{{font-family:ui-monospace,monospace}}</style></head><body><main><h1>VIA Folder Context Matrix</h1><p><b>Root:</b> <code>{esc(result['root'])}</code><br><b>Scan:</b> {esc(result['scan_id'])} · <b>Files:</b> {result['summary']['file_count']} · <b>Folders:</b> {result['summary']['folder_count']}</p><p>Read-only static evidence map; source code is not executed.</p><table><thead><tr><th>Module ID</th><th>Relative Path</th><th>Format</th><th>Role</th><th>Reader Engines</th><th>Tools</th><th>Status</th><th>Function Summary</th><th>Dependencies</th></tr></thead><tbody>{rows}</tbody></table></main></body></html>''', encoding="utf-8")


def write_outputs(result: dict[str, Any], output: Path) -> None:
    (output / "folder_scan.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_workflow_mermaid(result, output / "VIA_Folder_Workflow_Chart.mmd")
    write_matrix_csv(result, output / "VIA_Module_Matrix.csv")
    write_matrix_markdown(result, output / "VIA_Module_Matrix.md")
    write_matrix_html(result, output / "VIA_Module_Matrix.html")
    summary = [f"# VIA Folder Context Report — {result['root']}", "", "## Status", "", f"- Scan ID: `{result['scan_id']}`", f"- Files: `{result['summary']['file_count']}`", f"- Folders: `{result['summary']['folder_count']}`", f"- Errors: `{result['summary']['errors']}`", "- Source write/delete/execution: `false`", "", "## Workflow", "", "See `VIA_Folder_Workflow_Chart.mmd`.", "", "## Matrix", "", "See `VIA_Module_Matrix.csv`, `.md`, and `.html`.", "", "## Format counts", "", json.dumps(result["summary"]["formats"], ensure_ascii=False, indent=2), "", "## Role counts", "", json.dumps(result["summary"]["roles"], ensure_ascii=False, indent=2), "", "## Reader engine coverage", "", json.dumps(result["summary"].get("reader_engines", {}), ensure_ascii=False, indent=2), "", "## Reader tools", "", json.dumps(result["summary"].get("reader_tools", {}), ensure_ascii=False, indent=2)]
    (output / "VIA_Folder_Context_Report.md").write_text("\n".join(summary) + "\n", encoding="utf-8")


def scan_id() -> str:
    return uuid.uuid4().hex[:16]


def main(argv: list[str] | None = None) -> int:
    import argparse
    parser = argparse.ArgumentParser(description="VIA read-only folder context scanner")
    parser.add_argument("root", type=Path, help="system folder to scan")
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--max-files", type=int, default=5000)
    args = parser.parse_args(argv)
    output = args.output_dir or (Path.cwd() / f"VIA_Folder_Context_{scan_id()}")
    result = scan_folder(args.root, output, max_files=max(1, min(args.max_files, 50000)))
    print(json.dumps({"status": "PASS" if not result["errors"] else "PASS_WITH_REVIEW", "scan_id": result["scan_id"], "root": result["root"], "output_dir": str(output), "summary": result["summary"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
