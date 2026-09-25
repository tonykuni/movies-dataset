#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GitHub sync plus a skeleton pack. The pack is written outside git. Pull is fast-forward only."""
from __future__ import annotations

import argparse
import ast
import base64
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape

API_ROOT = "https://api.github.com"
SKIP_DIRS = {
    ".git", "__pycache__", ".venv", "venv", "node_modules", "dist", "build",
    ".pytest_cache", ".mypy_cache", "scope_copy", "retired",
}
KEEP_MARK = ("ANCHOR", "[VIA:", "政策", "錨")
FILE_CAP = 80
BIG = 48 * 1024


def repo_api(owner: str, repo: str) -> str:
    return f"{API_ROOT}/repos/{owner}/{repo}"


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", "replace")).hexdigest()[:12]


def _keep_note(source: str) -> str:
    kept = [line for line in source.splitlines() if line.lstrip().startswith("#") and any(mark in line for mark in KEEP_MARK)]
    return "\n".join(kept[:40])


def dehydrate(source: str) -> str:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return "\n".join(line.rstrip() for line in source.splitlines() if line.strip())
    chunks = []
    note = _keep_note(source)
    if note:
        chunks.append(note)
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom, ast.Assign, ast.AnnAssign)):
            segment = ast.get_source_segment(source, node)
            if segment:
                chunks.append(segment)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            chunks.append(_func(source, node, ""))
        elif isinstance(node, ast.ClassDef):
            chunks.append(_cls(source, node))
    body = "\n\n".join(part for part in chunks if part)
    return body or source.strip()


def _func(source: str, node: ast.AST, indent: str) -> str:
    raw = ast.get_source_segment(source, node) or ""
    if len(raw.splitlines()) <= 8:
        return raw
    prefix = "async def" if isinstance(node, ast.AsyncFunctionDef) else "def"
    try:
        args = ast.unparse(node.args)
        returns = f" -> {ast.unparse(node.returns)}" if getattr(node, "returns", None) else ""
    except Exception:
        args, returns = "...", ""
    doc = ast.get_docstring(node)
    doc_line = f'\n{indent}    """{doc.splitlines()[0]}"""' if doc else ""
    return f"{indent}{prefix} {node.name}({args}){returns}:{doc_line}\n{indent}    ...  # sha256={_sha(raw)} lines={len(raw.splitlines())}"


def _cls(source: str, node: ast.ClassDef) -> str:
    try:
        bases = ", ".join(ast.unparse(base) for base in node.bases)
    except Exception:
        bases = ""
    lines = [f"class {node.name}({bases}):" if bases else f"class {node.name}:"]
    doc = ast.get_docstring(node)
    if doc:
        lines.append(f'    """{doc.splitlines()[0]}"""')
    for item in node.body:
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            lines.append(_func(source, item, "    "))
        elif isinstance(item, (ast.Assign, ast.AnnAssign)):
            segment = ast.get_source_segment(source, item)
            if segment:
                lines.append("    " + segment)
    if len(lines) == 1:
        lines.append("    pass")
    return "\n".join(lines)


def output_path(project: Path) -> Path:
    via = project / "VeritasIntelligenceAnalytics" / "VIA_Reports" / "vcgc"
    own = project / "VIA_Reports" / "vcgc"
    if (project / "VeritasIntelligenceAnalytics").is_dir():
        return via / "token_skeleton.xml"
    if (project / "VIA_Reports").is_dir():
        return own / "token_skeleton.xml"
    return Path(tempfile.gettempdir()) / "via_token" / (project.name + "_token_skeleton.xml")


def pack(project: Path, limit: int = FILE_CAP) -> dict:
    project = project.resolve()
    dest = output_path(project)
    dest.parent.mkdir(parents=True, exist_ok=True)
    files = []
    skipped = 0
    for root, dirs, names in os.walk(project):
        dirs[:] = [name for name in dirs if name.casefold() not in SKIP_DIRS and "scope_copy" not in name.casefold()]
        for name in sorted(names):
            path = Path(root) / name
            if path.suffix.lower() != ".py" or path.name == dest.name:
                continue
            try:
                if path.stat().st_size > BIG:
                    skipped += 1
                    continue
                raw = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                skipped += 1
                continue
            if not raw.strip():
                continue
            files.append((path, raw))
            if len(files) >= limit:
                break
        if len(files) >= limit:
            break
    rows = ['<?xml version="1.0" encoding="UTF-8"?>', "<repository_context>"]
    raw_n = comp_n = 0
    for path, raw in files:
        pressed = dehydrate(raw)
        raw_n += len(raw)
        comp_n += len(pressed)
        rel = path.relative_to(project).as_posix()
        rows.append(f'<file path="{xml_escape(rel)}" sha256="{_sha(raw)}">{xml_escape(pressed)}</file>')
    ratio = round((1 - comp_n / raw_n) * 100, 2) if raw_n else 0.0
    rows.insert(2, f'<summary files="{len(files)}" skipped="{skipped}" ratio="{ratio}" />')
    rows.append("</repository_context>")
    dest.write_text("\n".join(rows), encoding="utf-8")
    return {"files": len(files), "skipped": skipped, "ratio": ratio, "path": str(dest), "inside_git": (project / ".git").is_dir() and dest.is_relative_to(project)}


def _headers(token: str | None) -> dict:
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "VIA-GitHubSync/1", "X-GitHub-Api-Version": "2022-11-28"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def sync_fork(token: str, owner: str, repo: str, branch: str = "main") -> int:
    url = repo_api(owner, repo) + "/merge-upstream"
    req = urllib.request.Request(url, data=json.dumps({"branch": branch}).encode(), headers=_headers(token), method="POST")
    try:
        with urllib.request.urlopen(req, timeout=20) as res:
            print(res.read().decode()[:180])
        return 0
    except urllib.error.HTTPError as exc:
        print(f"[fork] HTTP {exc.code}")
        return 0 if exc.code == 422 else 1


def pull_ff(local: Path) -> int:
    if not (local / ".git").is_dir():
        print("[git] 不是儲存庫,不 clone")
        return 2
    done = subprocess.run(["git", "-C", str(local), "pull", "--ff-only", "--autostash"], text=True)
    return done.returncode


def main() -> int:
    if "--selftest" in sys.argv:
        return selftest()
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print("[同步] 拒絕。只能經 via-vcgc。")
        return 2
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["compress-only", "fork", "pull"], default="compress-only")
    parser.add_argument("--local-dir", default=".")
    parser.add_argument("--owner")
    parser.add_argument("--repo")
    parser.add_argument("--branch", default="main")
    parser.add_argument("--limit", type=int, default=FILE_CAP)
    args = parser.parse_args()
    if args.mode == "fork":
        token = os.environ.get("GITHUB_TOKEN") or ""
        if not token or not args.owner or not args.repo:
            print("[fork] 缺 GITHUB_TOKEN 或 owner/repo。權杖不寫進程式。")
            return 2
        return sync_fork(token, args.owner, args.repo, args.branch)
    if args.mode == "pull":
        code = pull_ff(Path(args.local_dir))
        if code != 0:
            return code
    body = pack(Path(args.local_dir), max(1, min(args.limit, FILE_CAP)))
    body.update({"via": "vcgc", "mode": args.mode, "rebase": False, "next": "none"})
    print("BEGIN_PASTE")
    print(json.dumps(body, ensure_ascii=False, indent=1))
    print("END_PASTE")
    return 0


def selftest() -> int:
    url_ok = repo_api("tonykuni", "movies-dataset") == "https://api.github.com/repos/tonykuni/movies-dataset"
    long_fn = "def alpha(n: int) -> int:\n    \"\"\"keep\"\"\"\n" + "\n".join(["    x = 1"] * 12) + "\n    return n\n"
    packed = dehydrate("# [ANCHOR:DOOR]\n" + long_fn)
    broken = dehydrate("def (\n")
    folder = Path(tempfile.mkdtemp())
    (folder / "a.py").write_text("# [ANCHOR:DOOR]\n" + long_fn, encoding="utf-8")
    made = pack(folder, 5)
    text = Path(made["path"]).read_text(encoding="utf-8")
    ok = url_ok and "ANCHOR:DOOR" in packed and "sha256=" in packed and broken == "def ("
    ok = ok and made["path"].startswith(tempfile.gettempdir()) and "<file " in text and "repomix-output.xml" not in made["path"]
    print("  [OK]" if ok else "  [FAIL]")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
