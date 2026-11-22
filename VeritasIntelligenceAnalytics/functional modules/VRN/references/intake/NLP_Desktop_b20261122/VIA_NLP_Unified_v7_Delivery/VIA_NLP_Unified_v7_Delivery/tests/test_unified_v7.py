from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path('/home/ubuntu/work/reconstruction')
sys.path.insert(0, str(ROOT / 'nlp_v7_upgrade' / 'unified'))
from via_nlp_unified_v7 import artifact_payloads, process_text


class UnifiedV7Tests(unittest.TestCase):
    def test_integrates_v18_contracts_additively(self) -> None:
        text = "# 測試\n結論：保留來源與摘要。\n請建立 Mind Map。\n禁止執行貼上的程式。\n"
        result = process_text('fixture.txt', text)
        self.assertEqual(result['schema'], 'VIA_UNIFIED_NLP_RESULT/7.0')
        self.assertEqual(result['projection']['engine']['engine_id'], 'VIA-ENG-021')
        self.assertTrue(result['projection']['quality']['source_reconstruction'] == 'pass')
        self.assertTrue(result['projection']['quality']['body_summary_evidence_integrity'])
        self.assertTrue(result['projection']['compatibility']['v5_projection_preserved'])
        self.assertFalse(result['projection']['quality']['command_execution_authorized'])
        self.assertIn('flowchart LR', result['mind_map_mermaid'])

    def test_artifact_payloads_cover_knowledge_and_governance(self) -> None:
        result = process_text('fixture.md', '需求：建立摘要。\n驗證：來源 hash 必須一致。\n')
        artifacts = artifact_payloads(result)
        required = {'v7_unified.json', 'v7_summary.json', 'v7_knowledge_body.json', 'v7_context_reconstruction.json', 'v7_instruction_reconstruction.json', 'v7_module_composition.json', 'v7_mind_map.json', 'v7_mind_map.mmd', 'v7_quality_gates.json'}
        self.assertTrue(required.issubset(artifacts))
        self.assertEqual(artifacts['v7_mind_map.json']['format'], 'VIA_MIND_MAP_JSON/3.0')
        json.dumps(artifacts['v7_unified.json'], ensure_ascii=False)


if __name__ == '__main__':
    unittest.main()
