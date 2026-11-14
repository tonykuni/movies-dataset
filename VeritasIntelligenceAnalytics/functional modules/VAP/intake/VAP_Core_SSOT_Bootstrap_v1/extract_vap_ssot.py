"""Extract supplied authoritative JSON verbatim; never execute uploaded text."""
from pathlib import Path
import argparse
import hashlib
import json
import re


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def extract(source, output):
    text = source.read_text(encoding='utf-8-sig')
    decoder = json.JSONDecoder()
    found = {}
    for name in ('vap_spec.json', 'vap_chartlib.json'):
        marker = re.search(r'(?m)^ssot/' + re.escape(name) + r'\s*$', text)
        if not marker:
            raise ValueError('Missing section: ' + name)
        start = text.index('{', marker.end())
        obj, end = decoder.raw_decode(text[start:])
        raw = text[start:start + end] + '\n'
        found[name] = (obj, raw)
    spec = found['vap_spec.json'][0]
    library = found['vap_chartlib.json'][0]
    if spec.get('$schema') != 'VIA-VAP-SPEC/1.0':
        raise ValueError('Unexpected spec schema')
    if library.get('$schema') != 'VIA-VAP-CHARTLIB/1.0':
        raise ValueError('Unexpected chart library schema')
    codes = [c['code'] for g in library['groups'] for c in g['charts']]
    expected = {'VAP-CH-' + str(n).zfill(2) for n in range(1, 29)}
    if len(codes) != 28 or set(codes) != expected:
        raise ValueError('Expected exactly 28 unique chart codes')
    if library['meta'].get('specRef') != 'ssot/vap_spec.json':
        raise ValueError('Unexpected specRef')
    # Preflight EVERY target before writing any file; never silently replace SSOT.
    for name, (_, raw) in found.items():
        target = output / name
        if target.exists() and target.read_text(encoding='utf-8') != raw:
            raise FileExistsError('Refusing to overwrite differing SSOT: ' + str(target))
    output.mkdir(parents=True, exist_ok=True)
    for name, (_, raw) in found.items():
        target = output / name
        if not target.exists():
            target.write_text(raw, encoding='utf-8')
    manifest = {
        'schema_version': 'VAP-SOURCE-EXTRACTION/1.0',
        'source_filename': source.name,
        'source_sha256': digest(source.read_bytes()),
        'policy': 'Formal JSON preserved verbatim; extraction does not change version or rules.',
        'spec_version': spec['meta']['version'],
        'library_version': library['meta']['version'],
        'chart_count': len(codes),
        'group_counts': {g['id']: len(g['charts']) for g in library['groups']},
        'files': {n: digest(raw.encode('utf-8')) for n, (_, raw) in found.items()},
    }
    (output / 'source_manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, default=Path('/home/ubuntu/upload/pasted_content_3.txt'))
    parser.add_argument('--output', type=Path, default=Path(__file__).resolve().parent / 'ssot')
    args = parser.parse_args()
    print(json.dumps(extract(args.source, args.output), ensure_ascii=False, indent=2))
