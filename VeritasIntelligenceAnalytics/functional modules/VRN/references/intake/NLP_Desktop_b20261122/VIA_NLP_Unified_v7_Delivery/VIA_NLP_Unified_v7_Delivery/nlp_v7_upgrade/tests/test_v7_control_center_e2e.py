from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from pathlib import Path

BASE = 'http://127.0.0.1:8765'
ROOT = Path('/home/ubuntu/work/reconstruction')


def request(method: str, path: str, payload: bytes | None = None, headers: dict[str, str] | None = None):
    req = urllib.request.Request(BASE + path, data=payload, headers=headers or {}, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read()


def get_json(path: str) -> dict:
    status, body = request('GET', path)
    assert status == 200, (status, body[:500])
    return json.loads(body.decode('utf-8'))


def poll(job_id: str) -> dict:
    for _ in range(150):
        data = get_json('/api/job/' + job_id)
        if data['status'] in {'completed', 'failed'}:
            return data
        time.sleep(0.2)
    raise AssertionError('job timeout: ' + job_id)


def main() -> int:
    health = get_json('/api/health')
    assert health['status'] == 'ok'
    assert health['source_write'] is False and health['code_execution'] is False and health['network'] is False
    assert health['version'].startswith('7.')

    catalog = get_json('/api/catalog')
    engine_ids = {item['engine_id'] for item in catalog['engines']}
    assert 'VIA-ENG-021' in engine_ids
    assert 'VIA-ENG-021' in set(catalog['defaults']['engine_ids'])
    output_ids = {item['id'] for item in catalog['output_formats']}
    required_outputs = {
        'v7_unified', 'v7_summary', 'v7_knowledge_body', 'v7_context_reconstruction',
        'v7_instruction_reconstruction', 'v7_module_composition', 'v7_content_roles',
        'v7_function_classification', 'v7_source_ledger', 'v7_mind_map',
        'v7_mind_map_evolution', 'v7_mind_map_mermaid', 'v7_quality_gates',
    }
    assert required_outputs.issubset(output_ids)

    status, ui = request('GET', '/')
    assert status == 200 and b'VIA NLP Control Center v7' in ui and b'REG-000005 / v7' in ui

    source = (
        '# Unified NLP v7 E2E\n'
        '09:00 Alice：請修正空格、重組跳動討論並產生摘要。\n'
        '09:05 Bob：請合併相似指令 python tool.py --mode balanced。\n'
        '規格：不得刪除原文；驗證來源 hash；禁止執行貼上的程式。\n'
    )
    output_formats = [
        'markdown', 'html', 'record', 'v7_unified', 'v7_summary', 'v7_knowledge_body',
        'v7_context_reconstruction', 'v7_instruction_reconstruction', 'v7_module_composition',
        'v7_content_roles', 'v7_function_classification', 'v7_source_ledger', 'v7_mind_map',
        'v7_mind_map_evolution', 'v7_mind_map_mermaid', 'v7_quality_gates',
    ]
    payload = json.dumps({
        'source_text': source,
        'filename': 'v7_e2e_input.md',
        'command_threshold': 0.45,
        'engine_ids': ['VIA-ENG-018', 'VIA-ENG-019', 'VIA-ENG-020', 'VIA-ENG-021'],
        'output_formats': output_formats,
        'output_to_downloads': True,
    }, ensure_ascii=False).encode('utf-8')
    status, body = request('POST', '/api/reconstruct', payload, {'Content-Type': 'application/json'})
    assert status == 202, (status, body[:500])
    queued = json.loads(body.decode('utf-8'))
    job = poll(queued['job_id'])
    assert job['status'] == 'completed', job
    assert job['engine_ids'][-1] == 'VIA-ENG-021'
    assert job['metrics']['v7_knowledge_units'] > 0
    assert job['metrics']['v7_context_threads'] > 0
    assert job['execution_policy']['source_write'] is False
    assert job['execution_policy']['code_execution'] is False
    assert job['execution_policy']['network'] is False

    for logical in ['markdown', 'html', 'record', 'v7_unified', 'v7_summary', 'v7_knowledge_body', 'v7_context_reconstruction', 'v7_instruction_reconstruction', 'v7_module_composition', 'v7_content_roles', 'v7_function_classification', 'v7_source_ledger', 'v7_mind_map', 'v7_mind_map_evolution', 'v7_mind_map_mermaid', 'v7_quality_gates', 'download_bundle']:
        status, body = request('GET', f'/api/artifact/{job["job_id"]}/{logical}')
        assert status == 200 and body, (logical, status)

    status, v7_body = request('GET', f'/api/artifact/{job["job_id"]}/v7_unified')
    assert status == 200
    v7 = json.loads(v7_body.decode('utf-8'))
    assert v7['schema'] == 'VIA_UNIFIED_NLP_RESULT/7.0'
    assert v7['projection']['engine']['engine_id'] == 'VIA-ENG-021'
    assert v7['projection']['quality']['body_summary_evidence_integrity'] is True
    assert v7['projection']['quality']['command_execution_authorized'] is False

    status, mmd = request('GET', f'/api/artifact/{job["job_id"]}/v7_mind_map_mermaid')
    assert status == 200 and mmd.startswith(b'flowchart LR')
    status, md = request('GET', f'/api/artifact/{job["job_id"]}/markdown')
    assert status == 200 and b'Unified NLP v7 Evidence Projection' in md
    status, html = request('GET', f'/api/artifact/{job["job_id"]}/html')
    assert status == 200 and b'Unified NLP v7 Evidence Projection' in html

    status, traversal = request('GET', f'/api/artifact/{job["job_id"]}/../../via_nlp_control_api.py')
    assert status == 404
    print(json.dumps({
        'status': 'PASS', 'job_id': job['job_id'], 'engine_ids': job['engine_ids'],
        'artifact_count': len(job['artifacts']), 'metrics': job['metrics'],
        'downloads': job['downloads'], 'catalog_engines': len(catalog['engines']),
        'catalog_outputs': len(catalog['output_formats']), 'path_traversal_status': status,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
