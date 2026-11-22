from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from v5.via_nlp_reconstruction_v5 import load_lexicon, reconstruct_v5_paths  # noqa: E402

INPUTS = [
    ROOT / 'testmessage.txt',
    ROOT / 'dialogue20260708.txt',
]
THRESHOLDS = [0.45, 0.52, 0.58, 0.62, 0.68, 0.74, 0.80]
OUT = ROOT / 'v5' / 'VIA_NLP_v5_Threshold_Benchmark.json'


def main() -> int:
    lexicon = load_lexicon()
    rows = []
    for threshold in THRESHOLDS:
        bundle = reconstruct_v5_paths(INPUTS, lexicon, command_threshold=threshold)
        summary = bundle['summary']
        rows.append({
            'threshold': threshold,
            'original_commands': summary['original_commands'],
            'merged_command_groups': summary['merged_command_groups'],
            'deduplicated_command_candidates': summary['deduplicated_command_candidates'],
            'topics': summary['topics'],
            'parameter_conflicts': summary['parameter_conflicts'],
            'source_preserved': bundle['quality_gates']['source_preserved'],
            'original_commands_preserved': bundle['quality_gates']['original_commands_preserved'],
            'semantic_rewrite_executable': bundle['quality_gates']['semantic_rewrite_executable'],
            'safety_pass': bundle['quality_gates']['source_preserved'] and bundle['quality_gates']['original_commands_preserved'] and not bundle['quality_gates']['semantic_rewrite_executable'],
        })
    safe_rows = [row for row in rows if row['safety_pass'] and row['merged_command_groups'] >= row['original_commands'] / 2]
    # Prefer the highest deduplication that still keeps at least half of command groups.
    selected = max(safe_rows, key=lambda row: (row['deduplicated_command_candidates'], -row['merged_command_groups']))
    result = {
        'schema': 'VIA_NLP_THRESHOLD_BENCHMARK/5.0',
        'inputs': [str(path) for path in INPUTS],
        'rows': rows,
        'selection_policy': 'maximize safe deduplicated command candidates; preserve original commands and keep semantic rewrite non-executable',
        'selected_threshold': selected['threshold'],
        'selected_row': selected,
        'status': 'PASS' if selected['safety_pass'] else 'FAIL',
    }
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
