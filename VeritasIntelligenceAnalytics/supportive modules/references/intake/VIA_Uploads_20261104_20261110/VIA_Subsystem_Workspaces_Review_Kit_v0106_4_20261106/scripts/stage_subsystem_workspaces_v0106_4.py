#!/usr/bin/env python3
"""Verify first, then stage a new v0106.4 review add-on. Never run an engine."""
from datetime import datetime, timezone
import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import stat
import zipfile

MAX_FILES = 240
MAX_FILE = 64 * 1024 * 1024
MAX_TOTAL = 128 * 1024 * 1024


def sha(data):
    return hashlib.sha256(data).hexdigest()


def strict(raw):
    def pairs(items):
        out = {}
        for k, v in items:
            if k in out:
                raise ValueError('duplicate JSON key')
            out[k] = v
        return out
    def reject(value):
        raise ValueError('nonfinite JSON')
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=reject)


def chain(path):
    p = Path(path).absolute()
    for q in [p, *p.parents]:
        if q.exists() or q.is_symlink():
            s = q.lstat()
            if q.is_symlink() or getattr(s, 'st_file_attributes', 0) & 0x400:
                raise ValueError('STOP symlink/reparse path')
    return p


def safe_name(name):
    if not name or name.startswith('/') or '\\' in name or ':' in name or len(name) > 240:
        raise ValueError('STOP unsafe member')
    for part in name.split('/'):
        if not part or part in ('.', '..') or part[-1] in '. ' or re.search(r'[<>:"|?*\x00-\x1f\x7f]', part):
            raise ValueError('STOP unsafe Windows path')
        if re.fullmatch(r'(CON|PRN|AUX|NUL|COM[0-9]|LPT[0-9])', part.split('.')[0], re.I):
            raise ValueError('STOP reserved device name')
    return name


def verify(archive, expected_sha):
    p = chain(archive)
    if not re.fullmatch('[a-f0-9]{64}', expected_sha) or not p.is_file() or p.stat().st_size > MAX_TOTAL:
        raise ValueError('STOP invalid archive/hash')
    return verify_blob(p.read_bytes(), expected_sha)


def verify_blob(raw, expected_sha):
    if len(raw) > MAX_TOTAL or sha(raw) != expected_sha:
        raise ValueError('STOP external archive SHA mismatch')
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        info = z.infolist()
        if len(info) > MAX_FILES or sum(i.file_size for i in info) > MAX_TOTAL:
            raise ValueError('STOP package capacity exceeded')
        seen = set()
        for i in info:
            safe_name(i.filename)
            if i.filename.casefold() in seen or i.is_dir() or i.flag_bits & 1 or stat.S_ISLNK(i.external_attr >> 16):
                raise ValueError('STOP duplicate/directory/encrypted/symlink member')
            seen.add(i.filename.casefold())
            if i.file_size > MAX_FILE or i.file_size / max(i.compress_size, 1) > 100:
                raise ValueError('STOP file/compression ratio limit')
        if z.testzip():
            raise ValueError('STOP ZIP CRC mismatch')
        m = strict(z.read('manifest.json'))
        if m.get('version') != 'v0106.4' or m.get('policy') != 'EXISTING_PLUS_NEW_ATLAS_AND_LOCAL_TOOLS':
            raise ValueError('STOP version/policy mismatch')
        for k in ('release_ready', 'production_deployment', 'formal_registration', 'existing_engine_modified', 'contracts_activated'):
            if m.get(k) is not False:
                raise ValueError('STOP missing/unsafe approval flag')
        records = m.get('files')
        if not isinstance(records, dict) or len(records) != m.get('file_count'):
            raise ValueError('STOP manifest shape/count')
        if set(z.namelist()) != set(records) | {'manifest.json', 'SHA256SUMS'}:
            raise ValueError('STOP precise member allowlist mismatch')
        sums = {}
        for line in z.read('SHA256SUMS').decode('utf-8').splitlines():
            h, name = line.split('  ', 1)
            if name in sums:
                raise ValueError('STOP duplicate SUMS')
            sums[name] = h
        if set(sums) != set(records):
            raise ValueError('STOP SHA256SUMS coverage mismatch')
        for name, r in records.items():
            safe_name(name)
            body = z.read(name)
            if not isinstance(r, dict) or len(body) != r.get('bytes') or sha(body) != r.get('sha256') or sums[name] != r['sha256']:
                raise ValueError('STOP member hash/length mismatch')
        return m


def stage(archive, expected_sha, root):
    root = chain(root)
    if not root.is_dir():
        raise FileNotFoundError('STOP existing owner root required; root is not created')
    archive = chain(archive)
    if not re.fullmatch('[a-f0-9]{64}', expected_sha) or not archive.is_file() or archive.stat().st_size > MAX_TOTAL:
        raise ValueError('STOP invalid source archive/hash')
    raw = archive.read_bytes()
    manifest = verify_blob(raw, expected_sha)
    parent = chain(root / 'VIA_Review_Candidates')
    parent.mkdir(exist_ok=True)
    target = chain(parent / ('v0106.4_' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')))
    target.mkdir(exist_ok=False)
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        for name in z.namelist():
            p = target / safe_name(name)
            p.parent.mkdir(parents=True, exist_ok=True)
            with p.open('xb') as f:
                f.write(z.read(name))
    return {'status': 'PASS_STAGED_CANDIDATE_ONLY', 'target': str(target), 'version': 'v0106.4', 'zip_sha256': expected_sha,
            'verified_files': manifest['file_count'], 'commands_executed': 0, 'existing_engine_modified': False,
            'formal_registration': False, 'production_deployment': False}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--zip', type=Path, required=True)
    ap.add_argument('--sha256', required=True)
    ap.add_argument('--root', type=Path, required=True)
    a = ap.parse_args()
    print(json.dumps(stage(a.zip, a.sha256, a.root), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
