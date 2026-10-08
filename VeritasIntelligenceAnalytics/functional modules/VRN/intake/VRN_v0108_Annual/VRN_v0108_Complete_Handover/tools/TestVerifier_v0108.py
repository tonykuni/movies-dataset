PARAMS = {'verifier': 'VerifyPack_v0108.py', 'default_pack': '../pack'}
import argparse
import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path


def def_main():
    parser = argparse.ArgumentParser(description='Reject deliberate errors without modifying the reference pack')
    parser.add_argument('--receipt', type=Path, required=True)
    args = parser.parse_args()
    here = Path(__file__).resolve().parent
    pack = (here / PARAMS['default_pack']).resolve()
    if args.receipt.resolve().is_relative_to(pack):
        raise ValueError('RECEIPT_MUST_BE_OUTSIDE_PACK')
    spec = importlib.util.spec_from_file_location('vrn_verifier', here / PARAMS['verifier'])
    verifier = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(verifier)
    base = verifier.def_json(pack / 'data/AnnualFinancialData.json')
    checks = []
    for name in ['changed_number', 'quarterly_frequency', 'duplicate_key', 'missing_filled_zero']:
        rows = copy.deepcopy(base)
        if name == 'changed_number':
            rows[0]['VALUE_NUMERIC'] = 123456789
        elif name == 'quarterly_frequency':
            rows[0]['FREQUENCY'] = 'QUARTERLY'
        elif name == 'duplicate_key':
            rows[1] = copy.deepcopy(rows[0])
        else:
            row = next(x for x in rows if x['TABLE_ID'] == 'N01-P2-T3' and x['METRIC'] == 'Otheroperatingcashflow' and x['PERIOD'] == '2028')
            row['VALUE_NUMERIC'] = 0
        try:
            verifier.def_fact_contract(rows, base)
        except ValueError as exc:
            checks.append({'test': name, 'status': 'PASS_REJECTED', 'reason': str(exc)})
        else:
            raise AssertionError('FAILED_TO_REJECT: ' + name)
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        source = root / 'engine.py'
        source.write_text('before', encoding='utf-8')
        (root / 'SHA256_MANIFEST.json').write_text(json.dumps({'engine.py': verifier.def_hash(source)}), encoding='utf-8')
        source.write_text('after', encoding='utf-8')
        try:
            verifier.def_verify_manifest(root)
        except ValueError as exc:
            checks.append({'test': 'changed_file', 'status': 'PASS_REJECTED', 'reason': str(exc)})
        else:
            raise AssertionError('FAILED_TO_REJECT: changed_file')
        receipt = root / 'failure.json'
        result = subprocess.run([sys.executable, str(here / PARAMS['verifier']), '--pack', str(pack), '--results', str(root / 'missing'), '--receipt', str(receipt)], capture_output=True, text=True, encoding='utf-8')
        if result.returncode != 1 or verifier.def_json(receipt)['status'] != 'FAIL':
            raise AssertionError('CLI_FAILURE_NOT_PROPAGATED')
        checks.append({'test': 'missing_results_cli_exit', 'status': 'PASS_REJECTED', 'exit_code': result.returncode})
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps({'status': 'PASS', 'checks': checks}, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'status': 'PASS', 'rejected_cases': len(checks)}))


if __name__ == '__main__':
    def_main()
