"""Private packaging utility for the one VCGC Layout engine.

The capability SSOT owns the runtime file list. Copy exact source bytes, verify
all declared hashes, and exclude historical files not used by this composition.
This module does not execute extraction, install dependencies or deploy a host.
"""
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
import hashlib
import json
import zipfile
from pathlib import Path, PurePosixPath
from . import VIA_ACCEL

# def 01_PARAMETERS — package contract is centralized in the capability SSOT.
VIA=Path(__file__).resolve().parents[3]
CAPABILITIES=VIA/'supportive modules/registry/VIA_Layout_Capabilities_SSOT_v0100.json'
MANIFEST_NAME='BUNDLE_MANIFEST.json'
RUNTIME_PREFIX='VeritasIntelligenceAnalytics'
SOURCE_SUFFIXES=('.py','.json','.csv','.md')
IGNORED_PARTS={'__pycache__','VIA_Reports'}
# [VIA:ACCEL-BRIDGE] Reuse the owning package's canonical compatibility bridge.


def def_relative(value):
    """Accept portable relative member paths only, including on Windows."""
    raw=str(value);path=PurePosixPath(raw)
    if not raw or path.is_absolute() or '..' in path.parts or '\\' in raw or ':' in raw or str(path)!=raw:
        raise ValueError('unsafe package path: '+raw)
    return raw


def def_copy_runtime(source, destination, relatives):
    """Build a fresh runtime tree from explicit files; never overwrite a host tree."""
    source=Path(source).resolve();destination=Path(destination).resolve()
    if destination==source or destination.is_relative_to(source):raise ValueError('package destination inside source tree')
    if destination.exists() and any(destination.iterdir()):raise ValueError('package destination is not empty')
    names=[def_relative(p) for p in relatives]
    if len({p.casefold() for p in names})!=len(names):raise ValueError('duplicate or case-colliding package paths')
    records=[]
    for relative in sorted(names):
        original=source/relative
        if original.is_symlink() or not original.resolve().is_relative_to(source) or not original.is_file():raise ValueError('missing or escaped source: '+relative)
        data=original.read_bytes();target=destination/relative;target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(data)
        records.append({'path':relative,'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)})
    return {'schema':'VIA.LayoutRuntimeBundle.v1','public_entry':'via-vcgc layout','runtime_prefix':RUNTIME_PREFIX,'files':records}


def def_verify(root, manifest):
    """Missing, altered, escaping or unexpected source files fail verification."""
    root=Path(root).resolve();errors=[];expected=set()
    for record in manifest['files']:
        relative=def_relative(record['path']);folded=relative.casefold()
        if folded in expected:errors.append('duplicate: '+relative)
        expected.add(folded);path=root/relative
        if path.is_symlink() or not path.resolve().is_relative_to(root):errors.append('escaped: '+relative)
        elif not path.is_file():errors.append('missing: '+relative)
        elif hashlib.sha256(path.read_bytes()).hexdigest()!=record['sha256']:errors.append('hash mismatch: '+relative)
    for path in root.rglob('*'):
        relative=path.relative_to(root)
        if not (set(relative.parts)&IGNORED_PARTS) and path.is_file() and path.suffix in SOURCE_SUFFIXES and relative.as_posix().casefold() not in expected:
            errors.append('unexpected source: '+relative.as_posix())
    return {'state':'ERROR' if errors else 'VERIFIED','files':len(manifest['files']),'errors':errors}


def def_create_zip(runtime, destination, manifest, extras=None):
    """Package the verified tree and ordered supplemental artifacts atomically."""
    runtime=Path(runtime);destination=Path(destination)
    verification=def_verify(runtime,manifest)
    if verification['errors']:raise RuntimeError(str(verification['errors']))
    extras=extras or {};names={MANIFEST_NAME.casefold()}
    for name in extras:
        name=def_relative(name)
        folded=name.casefold()
        if folded in names or folded==RUNTIME_PREFIX.casefold() or folded.startswith(RUNTIME_PREFIX.casefold()+'/'):raise ValueError('reserved archive path: '+name)
        names.add(folded)
    destination.parent.mkdir(parents=True,exist_ok=True);temporary=destination.with_suffix(destination.suffix+'.tmp')
    try:
        with zipfile.ZipFile(temporary,'w',zipfile.ZIP_DEFLATED) as archive:
            archive.writestr(MANIFEST_NAME,json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
            for record in manifest['files']:archive.write(runtime/record['path'],RUNTIME_PREFIX+'/'+record['path'])
            for name,path in extras.items():archive.write(Path(path),name)
        with zipfile.ZipFile(temporary) as archive:
            failed=archive.testzip()
            if failed:raise RuntimeError('archive integrity: '+failed)
        temporary.replace(destination)
    finally:
        if temporary.exists():temporary.unlink()
    return {'state':'VERIFIED','path':str(destination.resolve()),'bytes':destination.stat().st_size,'sha256':hashlib.sha256(destination.read_bytes()).hexdigest()}
