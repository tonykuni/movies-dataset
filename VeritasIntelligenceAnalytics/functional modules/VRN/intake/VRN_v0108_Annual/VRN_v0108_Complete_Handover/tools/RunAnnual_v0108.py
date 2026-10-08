#!/usr/bin/env python3
PARAMS = {
    'version': 'v0108-handover-v0100',
    'pack': '../pack',
    'main': 'VRN_AnnualFinancial_v0108.py',
    'audit': 'VRN_AnnualAudit_v0108.py',
}
import hashlib
import importlib.util
import json
import sys
import zipfile
from pathlib import Path


def def_package_portable(out, version):
    paths = sorted(p for p in out.rglob('*') if p.is_file() and p.suffix != '.zip' and p.name != 'SHA256_MANIFEST.json' and '__pycache__' not in p.parts)
    manifest = {p.relative_to(out).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    manifest_path = out / 'SHA256_MANIFEST.json'
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    archive = out / ('VRN_AnnualFinancial_' + version + '.zip')
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as zipped:
        for path in paths + [manifest_path]:
            zipped.write(path, path.relative_to(out).as_posix())
    with zipfile.ZipFile(archive) as zipped:
        if zipped.testzip() is not None:
            raise ValueError('ZIP_CRC_FAILED')
        if not all(hashlib.sha256(zipped.read(name)).hexdigest() == digest for name, digest in manifest.items()):
            raise ValueError('ZIP_MANIFEST_MISMATCH')
    return {'檢查': 'ZIP／SHA256 全檔讀回', '結果': 'PASS', '證據': str(len(manifest)) + ' files; portable POSIX member names'}


def def_main():
    pack = (Path(__file__).resolve().parent / PARAMS['pack']).resolve()
    spec = importlib.util.spec_from_file_location('vrn_handover_main', pack / PARAMS['main'])
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    original_import = module.def_import

    def def_import_adapter(path, name):
        loaded = original_import(path, name)
        if Path(path).name == PARAMS['audit']:
            loaded.def_package = def_package_portable
        return loaded

    module.def_import = def_import_adapter
    try:
        module.def_cli()
    finally:
        module.def_import = original_import


if __name__ == '__main__':
    def_main()
