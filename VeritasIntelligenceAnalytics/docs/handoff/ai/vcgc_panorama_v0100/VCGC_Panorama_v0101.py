#!/usr/bin/env python3
"""VCGC local orchestration and three-pass source audit. No source rewriting.

v0101 (2026-11-07 · Codex PR #603 P1 / P2 · v0100 一字不改留存, SHA256SUMS 仍指 v0100):
  P1 預設沿用相依未變的站收據 (`test`, 由主控台 CGC_MDL224 依相依判沿用); 要全站重跑改用 --force-full (`test --full`).
     --reuse-receipts 保留為相容旗標 (= 預設行為).
  P2 逾時終止升級到整個 owned process group: SIGTERM 群 → 等 10 s → SIGKILL 群 (不論父行程是否已離開) → 再 kill 父; Windows 照舊 taskkill /T /F.
"""
from __future__ import annotations

import argparse
import ast
import collections
import concurrent.futures
import csv
import hashlib
import html
import importlib
import io
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
import tokenize
from datetime import datetime, timezone
from pathlib import Path

# ---------------- 1. Parameters and source provenance ----------------
VERSION = 'v0101'
REFERENCE_COMMIT = '4647c8c12e931b6d69730cd0077ecfb41caba1b5'
DEFAULT_ROOTS = [r'C:\Users\tonyk\OneDrive\Documents\VeritasIntelligenceAnalytics', r'C:\Users\tonyk\OneDrive\Documents\movies-dataset']
SOURCE_EXTENSIONS = {'.py', '.ps1', '.psm1', '.psd1'}
DEPENDENCY_DIRS = {'node_modules', '.venv', 'venv', 'env', 'site-packages', '__pycache__'}
ALWAYS_EXCLUDE = {'.git'}
HEARTBEAT_SECONDS = 15
MAX_SOURCE_BYTES = 32 * 1024 * 1024
MAX_WARNINGS_PER_FILE = 100
PIN_FAMILIES = ['token', 'accelerator', 'network', 'nlp', 'layout', 'frame', 'praddle', 'pdfplumber', 'ocr']
NET_PREFIXES = ('requests.', 'httpx.', 'urllib.request.', 'aiohttp.', 'socket.')
ACCEL_METHODS = {'accel_map', 'run_fast', 'activate', 'parallel_map', 'run_parallel', 'apply_limits'}
PS_NET_NAMES = {'invoke-webrequest', 'invoke-restmethod', 'curl', 'curl.exe', 'wget'}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.tmp')
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str) + '\n', encoding='utf-8')
    tmp.replace(path)


def read_json(path: Path, default=None):
    try:
        return json.loads(path.read_text(encoding='utf-8-sig'))
    except (OSError, ValueError):
        return default


def sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def version_number(path: Path) -> int:
    match = re.search(r'[_-]v(\d+)\.[^.]+$', path.name)
    return int(match[1]) if match else -1


def latest(folder: Path, pattern: str) -> Path | None:
    return max(folder.glob(pattern), key=version_number, default=None)


def pinned_path(via: Path, value: str) -> Path:
    parts = value.replace('\\', '/').split('/')
    if 'VeritasIntelligenceAnalytics' in parts:
        parts = parts[parts.index('VeritasIntelligenceAnalytics') + 1:]
    candidate = (via / Path(*parts)).resolve()
    if not candidate.is_relative_to(via.resolve()):
        raise ValueError('Lock path escapes the selected VIA root')
    return candidate


def inspect_pins(via: Path, lock: dict) -> list[dict]:
    rows = []
    for family in PIN_FAMILIES:
        item = lock.get(family) or {}
        row = {'family': family, 'version': item.get('version', ''), 'expected_sha256': item.get('sha256', ''), 'state': 'ABSENT'}
        try:
            if not item.get('path'):
                raise ValueError('No path in local lock')
            path = pinned_path(via, item['path'])
            row['path'] = str(path)
            raw = path.read_bytes()
            row['sha256'] = hashlib.sha256(raw).hexdigest()
            row['lf_sha256'] = hashlib.sha256(raw.replace(b'\r\n', b'\n')).hexdigest()
            if not row['expected_sha256']:
                row['state'] = 'NO_HASH'
            elif row['sha256'] == row['expected_sha256']:
                row['state'] = 'MATCH'
            elif row['lf_sha256'] == row['expected_sha256']:
                row['state'] = 'LINE_ENDINGS_ONLY'
            else:
                row['state'] = 'MISMATCH'
        except (OSError, ValueError) as exc:
            row['error'] = str(exc)
        rows.append(row)
    return rows


# ---------------- 2. Process execution, receipts and acceleration ----------------
def _killpg(pid: int, sig) -> bool:
    """Signal the whole owned process group; False when the group is already gone."""
    try:
        os.killpg(pid, sig)
        return True
    except ProcessLookupError:
        return False


def terminate_owned(proc: subprocess.Popen, grace: float = 10.0) -> None:
    """v0101: escalate to the entire owned process group so descendants that ignore SIGTERM cannot outlive the runner."""
    if os.name == 'nt':
        subprocess.run(['taskkill', '/PID', str(proc.pid), '/T', '/F'], capture_output=True, timeout=30, check=False)
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=10)
        return
    _killpg(proc.pid, signal.SIGTERM)
    try:
        proc.wait(timeout=grace)
    except subprocess.TimeoutExpired:
        pass
    # Grace period over (or parent already gone): SIGKILL the group regardless of the parent's state,
    # then make sure the parent itself is reaped.
    _killpg(proc.pid, signal.SIGKILL)
    if proc.poll() is None:
        proc.kill()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        pass


def run_command(label: str, command: list[str], cwd: Path, out: Path, timeout: int, receipts: list, env: dict) -> dict:
    """No shell interpolation; logs remain complete; only our process tree is terminated."""
    log = out / 'logs' / (re.sub(r'[^A-Za-z0-9_.-]', '_', label) + '.log')
    log.parent.mkdir(parents=True, exist_ok=True)
    start = time.monotonic()
    row = {'id': label, 'command': command, 'cwd': str(cwd), 'at': utc_now(), 'log': str(log), 'state': 'RUNNING'}
    receipts.append(row)
    write_json(out / 'COMMANDS.json', receipts)
    print(f'[START] {label} | log={log}', flush=True)
    try:
        with log.open('wb') as stream:
            opts = {'start_new_session': True} if os.name != 'nt' else {}
            proc = subprocess.Popen(command, cwd=cwd, env=env, stdin=subprocess.DEVNULL, stdout=stream, stderr=subprocess.STDOUT, **opts)
            next_beat = start + HEARTBEAT_SECONDS
            while proc.poll() is None:
                elapsed = time.monotonic() - start
                if elapsed >= timeout:
                    terminate_owned(proc)
                    row.update(rc=124, state='TIMEOUT')
                    break
                if time.monotonic() >= next_beat:
                    print(f'[HEARTBEAT] {label} {elapsed:.0f}s | log {log.stat().st_size:,} bytes', flush=True)
                    next_beat += HEARTBEAT_SECONDS
                time.sleep(0.25)
            if 'rc' not in row:
                row.update(rc=proc.returncode, state='RETURNED_ZERO' if proc.returncode == 0 else 'NONZERO')
    except (OSError, subprocess.SubprocessError) as exc:
        row.update(rc=125, state='ERROR', error=str(exc))
    row['seconds'] = round(time.monotonic() - start, 2)
    write_json(out / 'COMMANDS.json', receipts)
    print(f"[DONE] {label} rc={row['rc']} {row['seconds']}s", flush=True)
    return row


def activate_bridge(via: Path) -> dict:
    """[VIA:ACCEL-BRIDGE:v0100] Use the existing bridge and actual activate API."""
    folder = via / 'supportive modules'
    path = folder / 'VIA_SuperAccel_Module.py'
    if not path.is_file():
        return {'state': 'ABSENT', 'path': str(path)}
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(folder))
    try:
        module = importlib.import_module('VIA_SuperAccel_Module')
        result = module.activate(apply_limits=True)
        if not isinstance(result, dict):
            return {'state': 'UNVERIFIED', 'why': 'activate returned no dictionary'}
        applied = result.get('applied') or {}
        ok = bool(result.get('celeritas')) and isinstance(applied, dict) and bool(applied) and 'err' not in applied
        return {'state': 'API_APPLIED' if ok else 'UNVERIFIED', 'result': result, 'path': str(path)}
    except Exception as exc:
        return {'state': 'ERROR', 'error': f'{type(exc).__name__}: {exc}', 'path': str(path)}


def exercise_token_tools(token: str, via: Path, out: Path, timeout: int, receipts: list, env: dict) -> dict:
    """Exercise real slice/chain/ETag interfaces without modifying their targets."""
    base = [sys.executable, token]
    lock_path = via / 'supportive modules' / 'registry' / 'VIA_ToolVersion_Lock_v0100.json'
    tasks = [('token_slice', ['slice', token, 'main']), ('token_chain', ['chain', token, '--all']), ('token_json_slice', ['slice', str(lock_path), 'token.path'])]
    for label, words in tasks:
        run_command(label, base + words, via.parent, out, timeout, receipts, env)
    first = run_command('token_etag_read', base + ['read', str(lock_path)], via.parent, out, timeout, receipts, env)
    content = Path(first['log']).read_text(encoding='utf-8', errors='replace') if Path(first['log']).is_file() else ''
    matches = re.findall(r'etag\s*[=:]\s*[\"\']?([0-9a-fA-F]{8,64})', content)
    if first['rc'] == 0 and matches:
        second = run_command('token_etag_reuse', base + ['read', str(lock_path), '--if-etag', matches[-1]], via.parent, out, timeout, receipts, env)
        text = Path(second['log']).read_text(encoding='utf-8', errors='replace')
        return {'state': 'VERIFIED_304' if second['rc'] == 0 and '304_NOT_MODIFIED' in text else 'UNVERIFIED', 'etag': matches[-1]}
    return {'state': 'UNVERIFIED', 'why': 'No successful ETag receipt'}


# ---------------- 3. Full recursive inventory: all retained versions ----------------
def enumerate_sources(roots: list[Path], include_dependencies: bool = False) -> tuple[list[Path], list[dict]]:
    found, excluded = {}, []
    for root in roots:
        if not root.is_dir():
            excluded.append({'path': str(root), 'reason': 'ROOT_MISSING', 'blocking': True})
            continue
        def onerror(error):
            excluded.append({'path': error.filename, 'reason': 'DIRECTORY_READ_ERROR', 'error': str(error), 'blocking': True})
        for directory, dirs, files in os.walk(root, followlinks=False, onerror=onerror):
            keep = []
            for name in dirs:
                child = Path(directory) / name
                dependency = name.lower() in DEPENDENCY_DIRS or (child / 'pyvenv.cfg').is_file()
                junction = getattr(child, 'is_junction', lambda: False)()
                if os.name == 'nt' and not junction:
                    try:
                        junction = getattr(child.lstat(), 'st_reparse_tag', 0) == 0xA0000003
                    except OSError as exc:
                        excluded.append({'path': str(child), 'reason': 'DIRECTORY_READ_ERROR', 'error': str(exc), 'blocking': True})
                        continue
                if child.is_symlink() or junction:
                    excluded.append({'path': str(child), 'reason': 'LINK_DIRECTORY_NOT_FOLLOWED', 'blocking': False})
                elif name.lower() in ALWAYS_EXCLUDE or (dependency and not include_dependencies):
                    excluded.append({'path': str(child), 'reason': 'DEPENDENCY_OR_GIT', 'blocking': False})
                else:
                    keep.append(name)
            dirs[:] = keep
            for name in files:
                path = Path(directory) / name
                if path.suffix.lower() not in SOURCE_EXTENSIONS:
                    continue
                if path.is_symlink():
                    excluded.append({'path': str(path), 'reason': 'LINK_FILE_NOT_FOLLOWED', 'blocking': False})
                    continue
                found[os.path.normcase(str(path.resolve()))] = path.resolve()
    return sorted(found.values(), key=lambda p: str(p).casefold()), excluded


def function_name(node) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return function_name(node.value) + '.' + node.attr
    return ''


def python_findings(tree: ast.AST) -> tuple[list[dict], list[str], list[str], list[str]]:
    findings, defs, accel, network = [], [], [], []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            defs.append(node.name)
            defaults = list(node.args.defaults) + [x for x in node.args.kw_defaults if x]
            if any(isinstance(x, (ast.List, ast.Dict, ast.Set)) for x in defaults):
                findings.append({'rule': 'MUTABLE_DEFAULT', 'line': node.lineno})
        if isinstance(node, ast.ExceptHandler):
            if node.type is None:
                findings.append({'rule': 'BARE_EXCEPT', 'line': node.lineno})
            if node.body and all(isinstance(x, ast.Pass) for x in node.body):
                findings.append({'rule': 'SWALLOWED_EXCEPTION_REVIEW', 'line': node.lineno})
        if isinstance(node, ast.Call):
            name = function_name(node.func)
            if ('accel' in name.lower() or 'celeritas' in name.lower()) and name.rsplit('.', 1)[-1] in ACCEL_METHODS:
                accel.append(name)
            if name.startswith(NET_PREFIXES):
                network.append(name)
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            names = collections.Counter(x.name for x in node.body if isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)))
            for name, count in names.items():
                if count > 1:
                    findings.append({'rule': 'SAME_SCOPE_REDEFINITION_REVIEW', 'name': name, 'count': count, 'line': getattr(node, 'lineno', 1)})
            ended = False
            for child in node.body:
                if ended:
                    findings.append({'rule': 'AFTER_UNCONDITIONAL_EXIT', 'line': getattr(child, 'lineno', 0)})
                    break
                ended = isinstance(child, (ast.Return, ast.Raise))
    return findings, defs, sorted(set(accel)), sorted(set(network))


def inspect_source(path: Path) -> dict:
    row = {'path': str(path), 'name': path.name, 'extension': path.suffix.lower(), 'state': 'UNPARSED', 'findings': []}
    try:
        stat = path.stat()
        row.update(bytes=stat.st_size, sha256=sha_file(path), version=version_number(path))
        if stat.st_size > MAX_SOURCE_BYTES:
            row.update(state='TOO_LARGE', why=f'Above {MAX_SOURCE_BYTES} bytes; not counted as parsed')
            return row
        data = path.read_bytes()
        if row['extension'] == '.py':
            encoding, _ = tokenize.detect_encoding(io.BytesIO(data).readline)
            text = data.decode(encoding)
            tree = ast.parse(text, filename=str(path))
            compile(tree, str(path), 'exec')
            issues, defs, calls, network = python_findings(tree)
            row.update(state='PARSED', definitions=defs, accel_calls=calls, network_calls=network, findings=issues[:MAX_WARNINGS_PER_FILE], finding_count=len(issues), encoding=encoding)
        else:
            text = data.decode('utf-8-sig', errors='replace')
            row.update(state='PENDING_POWERSHELL_AST', accel_calls=[], network_calls=[], definitions=[])
        row['bridge_marker'] = '[VIA:ACCEL-BRIDGE' in text if row['extension'] == '.py' else '[VIA:PS-ACCEL' in text
        row['network_adapter_marker'] = bool(re.search(r'Aegis|_via_net|VIA_NET|NetUnified', text, re.I))
        row['lines'] = len(text.splitlines())
    except (OSError, UnicodeError, SyntaxError, ValueError, MemoryError, RecursionError) as exc:
        row.update(state='ERROR', error=f'{type(exc).__name__}: {exc}', line=getattr(exc, 'lineno', None))
    return row


def scan_sources(files: list[Path], workers: int) -> list[dict]:
    rows = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        pending = {pool.submit(inspect_source, path): path for path in files}
        done_count = 0
        last = time.monotonic()
        while pending:
            done, _ = concurrent.futures.wait(pending, timeout=1, return_when=concurrent.futures.FIRST_COMPLETED)
            for future in done:
                path = pending.pop(future)
                try:
                    rows.append(future.result())
                except Exception as exc:
                    rows.append({'path': str(path), 'state': 'ERROR', 'error': str(exc), 'findings': []})
                done_count += 1
            if time.monotonic() - last >= HEARTBEAT_SECONDS:
                print(f'[PASS 1] {done_count}/{len(files)} files', flush=True)
                last = time.monotonic()
    return sorted(rows, key=lambda row: row['path'].casefold())


def resource_budget(requested: int, acceleration: dict) -> dict:
    workers = max(1, min(requested, os.cpu_count() or 1, 16))
    budget = (acceleration.get('result') or {}).get('thread_budget')
    if isinstance(budget, int) and budget > 0:
        workers = min(workers, budget)
    row = {'requested': requested, 'cpu_count': os.cpu_count(), 'accelerator_thread_budget': budget}
    try:
        import psutil
        available = psutil.virtual_memory().available
        row['available_memory_bytes'] = available
        if available < 2 * 1024**3:
            workers = 1
        elif available < 4 * 1024**3:
            workers = min(workers, 2)
    except ImportError:
        row['memory_probe'] = 'psutil unavailable; conservative maximum two scan workers'
        workers = min(workers, 2)
    row['workers'] = workers
    return row


def merge_ps_results(rows: list[dict], ps_file: Path) -> None:
    parsed = {}
    if ps_file.is_file():
        for line in ps_file.read_text(encoding='utf-8-sig').splitlines():
            try:
                item = json.loads(line)
                parsed[os.path.normcase(item['path'])] = item
            except (ValueError, KeyError):
                continue
    for row in rows:
        if row.get('extension') not in {'.ps1', '.psm1', '.psd1'}:
            continue
        item = parsed.get(os.path.normcase(row['path']))
        if not item:
            row['state'] = 'POWERSHELL_AST_UNVERIFIED'
            continue
        row['ps_ast'] = item
        row['state'] = 'ERROR' if item.get('errors') else 'PARSED'
        row['definitions'] = [d['name'] for d in item.get('functions', [])]
        row['network_calls'] = [c for c in item.get('commands', []) if c.lower() in PS_NET_NAMES]
        row['accel_calls'] = [c for c in item.get('commands', []) if re.search('celeritas|accel', c, re.I)]


def serial_review(rows: list[dict]) -> list[dict]:
    review = []
    buckets = collections.defaultdict(list)
    for row in rows:
        if row.get('state') == 'ERROR' and row.get('extension') == '.py':
            again = inspect_source(Path(row['path']))
            review.append({'path': row['path'], 'kind': 'SEQUENTIAL_RECHECK', 'first': row['state'], 'second': again['state'], 'hash_same': row.get('sha256') == again.get('sha256')})
        buckets[row.get('name', Path(row['path']).name)].append(row)
        if not row.get('bridge_marker'):
            review.append({'path': row['path'], 'kind': 'NO_BRIDGE_MARKER_REVIEW'})
        if row.get('network_calls') and not row.get('network_adapter_marker'):
            review.append({'path': row['path'], 'kind': 'DIRECT_NETWORK_CALL_REVIEW', 'calls': row['network_calls']})
    for name, group in buckets.items():
        if len(group) > 1 and len({r.get('sha256') for r in group}) > 1:
            review.append({'kind': 'SAME_NAME_DIFFERENT_CONTENT_REVIEW', 'name': name, 'paths': [r['path'] for r in group]})
    return review


def compare_snapshot(rows: list[dict], roots: list[Path], include_dependencies: bool) -> tuple[list[dict], list[dict]]:
    files, exclusions = enumerate_sources(roots, include_dependencies)
    before = {r['path']: r.get('sha256') for r in rows}
    after = {str(p): p for p in files}
    changes = [{'path': p, 'kind': 'REMOVED'} for p in before.keys() - after.keys()]
    changes += [{'path': p, 'kind': 'ADDED'} for p in after.keys() - before.keys()]
    for name in before.keys() & after.keys():
        try:
            if sha_file(after[name]) != before[name]:
                changes.append({'path': name, 'kind': 'CHANGED'})
        except OSError as exc:
            changes.append({'path': name, 'kind': 'READ_ERROR', 'error': str(exc)})
    return changes, exclusions


# ---------------- 4. Reports: runtime evidence stays distinct from static evidence ----------------
def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fields, extrasaction='ignore')
        writer.writeheader()
        for row in rows:
            writer.writerow({key: json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else value for key, value in row.items() if key in fields})


def render_table(rows: list[dict], fields: list[str]) -> str:
    head = ''.join('<th>' + html.escape(key) + '</th>' for key in fields)
    body = ''.join('<tr>' + ''.join('<td>' + html.escape(str(row.get(key, ''))) + '</td>' for key in fields) + '</tr>' for row in rows)
    return '<table><thead><tr>' + head + '</tr></thead><tbody>' + body + '</tbody></table>'


def save_reports(out: Path, report: dict, rows: list[dict], reviews: list[dict]) -> None:
    write_json(out / 'SUMMARY.json', report)
    write_json(out / 'SOURCE_INVENTORY.json', rows)
    write_json(out / 'REVIEW.json', reviews)
    write_csv(out / 'SOURCE_INVENTORY.csv', rows, ['path', 'state', 'bytes', 'lines', 'sha256', 'version', 'bridge_marker', 'accel_calls', 'network_calls', 'finding_count', 'error'])
    write_csv(out / 'TOOLS.csv', report.get('tools', []), ['family', 'version', 'state', 'path', 'sha256', 'expected_sha256'])
    issue_rows = [r for r in rows if r['state'] != 'PARSED' or r.get('findings')]
    parts = [f"<h1>理 · VIA VCGC · {VERSION}</h1>", '<p>全景來源稽核 / 工具與全功能串測 / 三輪證據矩陣</p>', f"<p>{html.escape(report['at'])} · {html.escape(report['state'])} · {len(rows):,} 檔</p>", '<p>PARSED 僅表示語法解析成功；API_APPLIED 僅代表本行程呼叫已套用。靜態呼叫候選不等於實際執行、效能提升或業務驗收。</p>', '<input id="search" placeholder="搜尋表格，例如 token、NLP、ERROR、路徑">']
    parts += ['<h2>摘要</h2><pre>' + html.escape(json.dumps(report['counts'], ensure_ascii=False, indent=2)) + '</pre>', '<h2>工具鎖定</h2>', render_table(report.get('tools', []), ['family', 'version', 'state', 'path']), '<h2>實際指令收據</h2>', render_table(report.get('commands', []), ['id', 'state', 'rc', 'seconds', 'log']), '<h2>檔案問題</h2>', render_table(issue_rows, ['path', 'state', 'error', 'findings']), '<h2>待複核（不是自動判定錯誤）</h2>', render_table(reviews, ['kind', 'path', 'name', 'paths']), '<h2>完整檔案矩陣</h2>', render_table(rows, ['path', 'state', 'bridge_marker', 'accel_calls', 'network_calls'])]
    css = 'body{font:12px/1.35 system-ui;background:#101720;color:#e3e9ed;margin:22px}h1{font-size:22px;color:#caa66c}h2{font-size:16px;margin-top:26px}table{border-collapse:collapse;width:100%;margin:10px 0;table-layout:auto}td,th{border:1px solid #34414e;padding:5px;text-align:left;vertical-align:top;overflow-wrap:anywhere}th{background:#21303e;position:sticky;top:0}input{padding:9px;width:70%;background:#21303e;color:white;border:1px solid #caa66c}pre{white-space:pre-wrap}tr:nth-child(even){background:#15212d}'
    script = "document.getElementById('search').addEventListener('input',e=>{const q=e.target.value.toLowerCase();document.querySelectorAll('tbody tr').forEach(r=>r.hidden=!r.textContent.toLowerCase().includes(q));});"
    (out / 'VCGC_PANORAMA.html').write_text('<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>VCGC Panorama</title><style>' + css + '</style><body>' + ''.join(parts) + '<script>' + script + '</script></body></html>', encoding='utf-8')


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', action='append', default=[])
    parser.add_argument('--via-root', required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--workers', type=int, default=4)
    parser.add_argument('--step-timeout', type=int, default=1800)
    parser.add_argument('--full-timeout', type=int, default=43200)
    parser.add_argument('--pwsh', default=shutil.which('pwsh') or '')
    parser.add_argument('--include-dependencies', action='store_true')
    parser.add_argument('--reuse-receipts', action='store_true', help='v0101: compatibility flag; dependency-aware receipt reuse is already the default')
    parser.add_argument('--force-full', action='store_true', help='v0101: rerun every registered station (test --full) instead of reusing receipts whose dependencies are unchanged')
    return parser


def main(argv=None) -> int:
    args = make_parser().parse_args(argv)
    via, out = Path(args.via_root).resolve(), Path(args.out).resolve()
    roots = [Path(r).resolve() for r in (args.root or DEFAULT_ROOTS)]
    out.mkdir(parents=True, exist_ok=True)
    reg = via / 'supportive modules' / 'registry'
    console = latest(reg, 'CGC_MDL149_VeritasCentralGovernanceConsole_v*.py')
    env = os.environ.copy()
    env.update(VIA_FROM_VCGC='YES', VIA_VCGC_PUSH='NO', PYTHONIOENCODING='utf-8', PYTHONUNBUFFERED='1', PYTHONDONTWRITEBYTECODE='1')
    os.environ.update({k: env[k] for k in ['VIA_FROM_VCGC', 'VIA_VCGC_PUSH', 'PYTHONDONTWRITEBYTECODE']})
    report = {'version': VERSION, 'at': utc_now(), 'reference_commit': REFERENCE_COMMIT, 'via_root': str(via), 'roots': [str(r) for r in roots], 'python': sys.version, 'commands': [], 'tools': [], 'state': 'RUNNING', 'activation_scope': 'VCGC support APIs and registered tests; no business pipeline startup'}
    receipts = report['commands']
    def console_call(label, words, timeout=None):
        return run_command(label, [sys.executable, str(console), *words], via.parent, out, timeout or args.step_timeout, receipts, env)
    token_ok = False
    if console:
        report['console_sha256'] = sha_file(console)
        token_ok = console_call('01_token', ['token'])['rc'] == 0
    else:
        report['blocker'] = 'VCGC console missing'
    lock = read_json(reg / 'VIA_ToolVersion_Lock_v0100.json', {})
    report['tools'] = inspect_pins(via, lock)
    token_row = next(r for r in report['tools'] if r['family'] == 'token')
    # Transport-only CRLF differences are reported; the console remains the authority.
    core_pin_ok = all(r['state'] in {'MATCH', 'LINE_ENDINGS_ONLY'} for r in report['tools'] if r['family'] in {'token', 'accelerator', 'network', 'nlp'})
    ready = token_ok and core_pin_ok
    if token_ok:
        console_call('02_handoff', ['handoff', 'check'])
        console_call('03_functions', ['functions'])
    if ready:
        report['python_acceleration'] = activate_bridge(via)
        env.update(os.environ)
        env.update(VIA_FROM_VCGC='YES', VIA_VCGC_PUSH='NO', PYTHONIOENCODING='utf-8', PYTHONUNBUFFERED='1', PYTHONDONTWRITEBYTECODE='1')
        console_call('04_quick', ['test', '--quick'])
        enter = console_call('05_entry_card', ['enter', '--no-pull', '--card'])
        report['entry_gate_rc'] = enter['rc']
        console_call('06_inventory', ['test', 'inventory'])
    else:
        report['blocker'] = 'Token preflight or locked support tool validation failed; activation and registered tests skipped'
    # Pass 1: all project source files, including old versions, independently of gate outcome.
    files, excluded = enumerate_sources(roots, args.include_dependencies)
    report['resource_budget'] = resource_budget(args.workers, report.get('python_acceleration', {}))
    workers = report['resource_budget']['workers']
    print(f'[PASS 1] {len(files):,} PS/PY files; workers={workers}', flush=True)
    rows = scan_sources(files, workers)
    write_json(out / 'EXCLUSIONS.json', excluded)
    ps_files = [str(p) for p in files if p.suffix.lower() != '.py']
    write_json(out / 'PS_FILES.json', ps_files)
    ps_result = out / 'PS_AST.jsonl'
    if ps_files and args.pwsh and Path(args.pwsh).is_file():
        run_command('07_ps_ast', [args.pwsh, '-NoProfile', '-NonInteractive', '-File', str(Path(__file__).with_name('Parse-VCGC-Sources-v0100.ps1')), '-Manifest', str(out / 'PS_FILES.json'), '-OutputFile', str(ps_result)], out, out, args.full_timeout, receipts, env)
    merge_ps_results(rows, ps_result)
    # Pass 2: sequential issue confirmation plus existing VCGC governance tools.
    print('[PASS 2] Sequential review + VCGC governance', flush=True)
    reviews = serial_review(rows)
    if ready:
        token = token_row['path']
        for i, root in enumerate(roots, 1):
            if root.is_dir():
                for verb in ['pack', 'read']:
                    run_command(f'08_token_{verb}_{i}', [sys.executable, token, verb, str(root)], via.parent, out, args.full_timeout, receipts, env)
        report['etag_check'] = exercise_token_tools(token, via, out, args.step_timeout, receipts, env)
        sample = out / 'NLP_SMOKE_INPUT.txt'
        sample.write_text('VCGC coordinates VIA governance and retains source evidence.\nToken tools provide source outlines, definition slices, log summaries, and cache checks.\nThis is a synthetic smoke test, not an investment research report.\n', encoding='utf-8')
        nlp_path = next(r.get('path') for r in report['tools'] if r['family'] == 'nlp')
        console_call('nlp_brief_smoke', ['run', nlp_path, 'text', '--file', str(sample), '--brief'])
        run_command('09_token_scan', [sys.executable, token, 'scan', '--json'], via.parent, out, args.full_timeout, receipts, env)
        console_call('10_ssot_panorama', ['ssot', 'panorama', '--no-write'], args.full_timeout)
        # This uses the existing inventory-driven test manager, including acceleration,
        # network adapter, NLP, OCR/layout/frame and MCP selftests. It does not call go.
        test_start = time.time()
        full = console_call('11_registered_tests', ['test', '--full'] if args.force_full else ['test'], args.full_timeout)   # v0101: reuse by default
        official = via / 'VIA_Reports' / 'vcgc' / 'TEST_latest.json'
        if official.is_file() and official.stat().st_mtime >= test_start - 2:
            card = read_json(official, {})
            write_json(out / 'VCGC_TEST_RESULT.json', card)
            report['registered_tests'] = {'lamp': card.get('lamp'), 'counts': card.get('counts'), 'stations_returned': len(card.get('rows', [])), 'families': card.get('families'), 'source': str(official), 'rc': full['rc']}
        else:
            report['registered_tests'] = {'lamp': 'UNVERIFIED', 'why': 'No fresh TEST_latest.json from this invocation', 'rc': full['rc']}
        console_call('12_mcp_doctor', ['mcp', 'doctor'])
        console_call('13_status_final', ['status'])
        console_call('14_handoff_final', ['handoff', 'check'])
        # digest never replaces the complete original command logs.
        run_command('15_token_digest', [sys.executable, token, 'digest', str(out / 'logs' / '11_registered_tests.log')], via.parent, out, args.step_timeout, receipts, env)
    # Pass 3: membership and hash stability after tests; receipts vs inventory.
    print('[PASS 3] Source hashes + completeness + final verdict', flush=True)
    changes, final_excluded = compare_snapshot(rows, roots, args.include_dependencies)
    write_json(out / 'SOURCE_CHANGES.json', changes)
    write_json(out / 'FINAL_EXCLUSIONS.json', final_excluded)
    inv_path = latest(reg, 'VIA_VCGC_FunctionInventory_SSOT_v*.json')
    inventory = read_json(inv_path, {}) if inv_path else {}
    report['inventory'] = {'path': str(inv_path or ''), 'version': inventory.get('version'), 'stations': len(inventory.get('stations', []))}
    write_json(out / 'LOCAL_FUNCTION_INVENTORY.json', inventory)
    bootstrap = read_json(out / 'PS_BOOTSTRAP.json', {})
    report['ps_acceleration'] = bootstrap
    counts = dict(collections.Counter(r['state'] for r in rows))
    report['counts'] = {'source_files': len(rows), 'parse_states': counts, 'bridge_marked': sum(bool(r.get('bridge_marker')) for r in rows), 'static_accel_call_candidates': sum(bool(r.get('accel_calls')) for r in rows), 'review_items': len(reviews), 'source_changes': len(changes), 'excluded_directories_or_links': len(excluded), 'commands_nonzero': sum(r.get('rc') != 0 for r in receipts)}
    fatal = not ready or not rows or bool(changes) or any(r['state'] != 'PARSED' for r in rows) or any(r.get('blocking') for r in excluded + final_excluded) or any(r.get('rc') not in (0, 2, 5) for r in receipts) or report.get('registered_tests', {}).get('lamp') == 'RED'
    caution = bool(reviews) or any(r.get('findings') for r in rows) or any(r.get('rc') for r in receipts) or any(r['state'] != 'MATCH' for r in report['tools']) or report.get('python_acceleration', {}).get('state') != 'API_APPLIED' or bootstrap.get('celeritas') != 'START_RETURNED' or report.get('registered_tests', {}).get('lamp') != 'GREEN' or report.get('etag_check', {}).get('state') != 'VERIFIED_304' or any('LINK' in x['reason'] for x in excluded)
    report['state'] = 'RED' if fatal else ('YELLOW' if caution else 'GREEN')
    report['finished_at'] = utc_now()
    report['limits'] = ['Static call detection is heuristic, not runtime coverage or speed proof.', 'All retained project versions scanned; .git and dependency environments excluded unless requested.', 'No source injection, code rewrite, git pull/push, package installation, remote service configuration, or production fetch requested by this runner.', 'Existing VCGC tests may write their normal local reports and ledgers.', 'Missing Windows/OCR/data evidence stays unverified.']
    save_reports(out, report, rows, reviews)
    print(f"[FINAL] {report['state']} | {out / 'VCGC_PANORAMA.html'}", flush=True)
    return {'GREEN': 0, 'YELLOW': 2, 'RED': 1}[report['state']]


if __name__ == '__main__':
    raise SystemExit(main())
