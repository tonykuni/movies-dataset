from __future__ import annotations

import hashlib
import json
from pathlib import Path

UPLOAD = Path('/home/ubuntu/upload')
NAMES = [
    'via_engine_standardizer(3).py',
    'Invoke-VIA-EngineStandardizer(3).ps1',
    'VES_AI_COLLAB(1).md',
    'VIA_CGC_ABC_AutoFixEngine_v0200.py',
]
OUT = Path('/home/ubuntu/work/reconstruction/VIA_V5_New_Attachments_Static_Inventory.json')


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def main() -> int:
    rows = []
    for name in NAMES:
        path = UPLOAD / name
        rows.append({
            'filename': name,
            'path': str(path),
            'exists': path.exists(),
            'size_bytes': path.stat().st_size if path.exists() else None,
            'sha256': digest(path) if path.exists() else None,
            'source_is_immutable': True,
            'attachment_executed': False,
        })
    result = {
        'schema': 'VIA_V5_NEW_ATTACHMENTS_STATIC_INVENTORY/5.0',
        'execution_policy': {
            'attachments_executed': False,
            'dependencies_installed': False,
            'network_access': False,
            'source_modified': False,
        },
        'items': rows,
    }
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': 'PASS', 'output': str(OUT), 'item_count': len(rows)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
