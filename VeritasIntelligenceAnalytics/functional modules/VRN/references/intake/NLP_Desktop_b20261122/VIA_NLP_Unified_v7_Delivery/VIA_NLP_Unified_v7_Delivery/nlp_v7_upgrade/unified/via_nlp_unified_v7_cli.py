from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[1]
VENDOR_SRC = WORKSPACE / 'vendor' / 'VIA_NLP_Application_System_v1.8.0' / 'src'
if str(VENDOR_SRC) not in sys.path:
    sys.path.insert(0, str(VENDOR_SRC))

from via_nlp_engine.bundle_ops import read_document_bundle  # type: ignore
from via_nlp_unified_v7 import artifact_payloads, process_text


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='VIA Unified NLP v7 standalone offline reconstruction tool')
    parser.add_argument('--input', type=Path, nargs='+', required=True, help='One or more files or directories')
    parser.add_argument('--output-dir', type=Path, default=Path('VIA_NLP_Unified_v7_Output'))
    parser.add_argument('--quality', choices=['fast', 'balanced', 'deep'], default='balanced')
    parser.add_argument('--max-files', type=int, default=1000)
    parser.add_argument('--max-total-bytes', type=int, default=512 * 1024 * 1024)
    parser.add_argument('--max-file-bytes', type=int, default=50 * 1024 * 1024)
    args = parser.parse_args(argv)

    bundle = read_document_bundle(
        args.input,
        recursive=True,
        max_files=args.max_files,
        max_total_bytes=args.max_total_bytes,
        max_file_bytes=args.max_file_bytes,
        use_markitdown=False,
    )
    source_name = ', '.join(item['source_name'] for item in bundle['source_record_ledger'])
    result = process_text(source_name, bundle['text'], quality=args.quality)
    output_dir = args.output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    payloads = artifact_payloads(result)
    written: list[str] = []
    for filename, payload in payloads.items():
        path = output_dir / filename
        if filename.endswith('.mmd') and isinstance(payload, str):
            path.write_text(payload, encoding='utf-8')
        else:
            path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8')
        written.append(str(path))
    manifest = {
        'schema': 'VIA_UNIFIED_NLP_STANDALONE_MANIFEST/7.0',
        'engine_id': 'VIA-ENG-021',
        'engine_version': '7.0.0',
        'source_record_ledger': bundle['source_record_ledger'],
        'completeness': bundle['completeness'],
        'projection': result['projection'],
        'artifacts': written,
        'execution_policy': {
            'source_write': False,
            'source_delete': False,
            'code_execution': False,
            'network': False,
            'package_install': False,
        },
    }
    manifest_path = output_dir / 'VIA_NLP_Unified_v7_Manifest.json'
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print(json.dumps({
        'status': 'PASS_WITH_REVIEW',
        'engine_id': 'VIA-ENG-021',
        'output_dir': str(output_dir),
        'source_files': bundle['completeness']['file_count'],
        'source_characters': bundle['completeness']['combined_text_chars'],
        'artifacts': written + [str(manifest_path)],
        'quality': result['projection']['quality'],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
