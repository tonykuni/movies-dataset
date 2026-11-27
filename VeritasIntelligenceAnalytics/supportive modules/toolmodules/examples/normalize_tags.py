#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""Example of a complete, independently testable intake module. [VIA:ACCEL-BRIDGE]"""
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
except Exception:  # noqa: BLE001
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

MODULE_ID = 'VTM-CUSTOM-001'
MAX_TAGS = 1000
MAX_TAG_LENGTH = 100

import argparse
import json
from pathlib import Path


def describe():
    return {'module_id': MODULE_ID, 'verb': 'normalize-tags', 'description': '清理標籤空白並去除完全相同的標籤；不合併來源 ID。'}


def execute(request):
    if not isinstance(request, dict) or set(request) != {'tags'}:
        raise ValueError('Expected exactly one tags field')
    tags = request['tags']
    if not isinstance(tags, list) or len(tags) > MAX_TAGS:
        raise ValueError('tags must be a bounded list')
    if any(not isinstance(tag, str) or len(tag) > MAX_TAG_LENGTH for tag in tags):
        raise ValueError('Each tag must be a bounded string')
    return {'module_id': MODULE_ID, 'status': 'OK', 'tags': sorted({tag.strip() for tag in tags if tag.strip()})}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--request', required=True)
    args = parser.parse_args()
    path = Path(args.request)
    if path.stat().st_size > 1024 * 1024:
        raise ValueError('Request exceeds one MiB')
    result = execute(json.loads(path.read_text(encoding='utf-8-sig')))
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
