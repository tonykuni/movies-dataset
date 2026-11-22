from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
REGISTRY = ROOT / 'VIA_SSOT_Engine_Registry_v5.json'
LEXICON = ROOT / 'VIA_NLP_SSOT_Lexicon_v5.json'
INVENTORY = ROOT / 'VIA_V5_New_Attachments_Static_Inventory.json'
BENCHMARK = ROOT / 'v5' / 'VIA_NLP_v5_Threshold_Benchmark.json'
BUNDLE = ROOT / 'v5' / 'test_output_v5' / 'VIA_NLP_Reconstruction_Bundle_v5.json'
REPORT = ROOT / 'VIA_NLP_v5_Regression_Report.json'


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding='utf-8'))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Validate VIA v5 NLP integration')
    parser.add_argument('--registry', type=Path, default=REGISTRY)
    parser.add_argument('--lexicon', type=Path, default=LEXICON)
    parser.add_argument('--inventory', type=Path, default=INVENTORY)
    parser.add_argument('--benchmark', type=Path, default=BENCHMARK)
    parser.add_argument('--bundle', type=Path, default=BUNDLE)
    parser.add_argument('--report', type=Path, default=REPORT)
    args = parser.parse_args(argv)

    errors: list[str] = []
    registry = load(args.registry)
    lexicon = load(args.lexicon)
    inventory = load(args.inventory)
    benchmark = load(args.benchmark)
    bundle = load(args.bundle)

    engines = {item['engine_id']: item for item in registry['engines']}
    profiles = {item['profile_id']: item for item in registry['acceleration_profiles']}
    adapters = {item['adapter_id']: item for item in registry['adapters']}
    contracts = {item['contract_id']: item for item in registry['contracts']}
    gates = {item['gate_id']: item for item in registry['gates']}
    inv = {item['filename']: item for item in inventory['items']}

    expected_engines = {'VIA-ENG-018', 'VIA-ENG-019', 'VIA-ENG-020'}
    expected_adapters = {'VIA-ADP-013', 'VIA-ADP-014', 'VIA-ADP-015', 'VIA-ADP-016', 'VIA-ADP-017', 'VIA-ADP-018'}
    expected_contracts = {f'VIA-CTR-{i:03d}' for i in range(30, 37)}
    expected_gates = {f'VIA-GATE-{i:03d}' for i in range(23, 30)}
    if registry['registry_id'] != 'VIA-SSOT-REG-000004':
        errors.append('registry identity mismatch')
    if registry['registry_version'] != '5.0.0':
        errors.append('registry version mismatch')
    if not expected_engines.issubset(engines):
        errors.append('missing v5 engines')
    if not expected_adapters.issubset(adapters):
        errors.append('missing v5 adapters')
    if not expected_contracts.issubset(contracts):
        errors.append('missing v5 contracts')
    if not expected_gates.issubset(gates):
        errors.append('missing v5 gates')

    for engine_id in sorted(expected_engines):
        engine = engines[engine_id]
        profile = profiles.get(engine['acceleration_profile_id'])
        if not profile:
            errors.append(f'{engine_id} missing accelerator profile')
        elif set(profile['accelerators']) != {f'VIA-ACC-{i:03d}' for i in range(1, 9)}:
            errors.append(f'{engine_id} missing shared accelerator')
        if engine['execution_policy']['source_write'] is not False:
            errors.append(f'{engine_id} source_write is not false')
        if engine['execution_policy']['code_execution'] is not False:
            errors.append(f'{engine_id} code_execution is not false')

    for filename, row in inv.items():
        if not row['exists']:
            errors.append(f'missing v5 attachment: {filename}')
        if row['attachment_executed'] is not False:
            errors.append(f'attachment execution flag is not false: {filename}')
        if row['sha256'] != registry['v5_integration']['attachments'].get(filename):
            errors.append(f'attachment hash lineage mismatch: {filename}')
    if any(value is not False for value in inventory['execution_policy'].values()):
        errors.append('inventory execution policy is not fully false')

    if lexicon['version'] != '5.0.0':
        errors.append('lexicon version mismatch')
    for key in ('regex', 'synonyms', 'factors', 'parameters'):
        if not lexicon.get(key):
            errors.append(f'lexicon section empty: {key}')
    if sha256(args.lexicon) != engines['VIA-ENG-018']['source_attachment_sha256']:
        errors.append('lexicon hash mismatch in engine lineage')

    selected = benchmark.get('selected_row', {})
    if benchmark.get('status') != 'PASS':
        errors.append('threshold benchmark status is not PASS')
    if benchmark.get('selected_threshold') != registry['v5_integration']['selected_command_threshold']:
        errors.append('selected threshold mismatch between benchmark and registry')
    if selected.get('safety_pass') is not True:
        errors.append('selected threshold safety gate failed')
    if selected.get('deduplicated_command_candidates', 0) <= 0:
        errors.append('threshold benchmark produced no deduplication')

    gates_result = bundle.get('quality_gates', {})
    required_bundle_gates = {
        'source_preserved': True,
        'source_deleted': False,
        'source_mutated': False,
        'original_commands_preserved': True,
        'semantic_rewrite_executable': False,
    }
    for key, expected in required_bundle_gates.items():
        if gates_result.get(key) != expected:
            errors.append(f'bundle gate mismatch: {key}={gates_result.get(key)!r}')
    if bundle.get('summary', {}).get('deduplicated_command_candidates', 0) <= 0:
        errors.append('full test bundle produced no command deduplication')
    if bundle.get('summary', {}).get('topics', 0) <= 0:
        errors.append('full test bundle produced no topics')
    if bundle.get('summary', {}).get('parameter_conflicts', 0) < 0:
        errors.append('invalid parameter conflict count')

    result = {
        'schema': 'VIA_NLP_REGRESSION_REPORT/5.0',
        'status': 'PASS' if not errors else 'FAIL',
        'registry_id': registry['registry_id'],
        'engine_version': '5.0.0',
        'tests': {
            'lexicon_integrity': not any('lexicon' in error for error in errors),
            'attachment_lineage': not any('attachment' in error for error in errors),
            'threshold_benchmark': benchmark.get('status') == 'PASS' and selected.get('safety_pass') is True,
            'source_preservation': gates_result.get('source_preserved') is True and gates_result.get('source_mutated') is False,
            'command_conservation': gates_result.get('original_commands_preserved') is True,
            'non_executable_semantic_projection': gates_result.get('semantic_rewrite_executable') is False,
            'topic_reconstruction': bundle.get('summary', {}).get('topics', 0) > 0,
            'summary_traceability': all(record['projections']['summary']['source_unit_traceable'] for record in bundle.get('records', [])),
        },
        'metrics': {
            'original_commands': bundle.get('summary', {}).get('original_commands'),
            'merged_command_groups': bundle.get('summary', {}).get('merged_command_groups'),
            'deduplicated_command_candidates': bundle.get('summary', {}).get('deduplicated_command_candidates'),
            'topics': bundle.get('summary', {}).get('topics'),
            'parameter_conflicts': bundle.get('summary', {}).get('parameter_conflicts'),
            'selected_command_threshold': benchmark.get('selected_threshold'),
        },
        'execution_policy': {
            'attachments_executed': False,
            'dependencies_installed': False,
            'network_access': False,
            'source_modified': False,
            'semantic_rewrite_executable': False,
        },
        'errors': errors,
    }
    args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == '__main__':
    raise SystemExit(main())
