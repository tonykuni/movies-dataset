from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

ROOT = Path('/home/ubuntu/work/reconstruction')
SOURCE = ROOT / 'VIA_SSOT_Engine_Registry_v4.json'
TARGET = ROOT / 'VIA_SSOT_Engine_Registry_v5.json'
ACCELERATORS = [f'VIA-ACC-{i:03d}' for i in range(1, 9)]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def profile(pid: str, eid: str, mode: str, specialization: str) -> dict:
    return {'profile_id': pid, 'engine_id': eid, 'mode': mode, 'accelerators': ACCELERATORS, 'specialization': specialization}


def make_engine(eid: str, name: str, name_zh: str, short: str, version: str, kind: str, responsibility: str, inputs: list[str], outputs: list[str], deps: list[str], profile_id: str, adapters: list[str], aliases: list[str], sha: str) -> dict:
    return {
        'engine_id': eid,
        'canonical_name': name,
        'canonical_name_zh': name_zh,
        'short_name': short,
        'version': version,
        'kind': kind,
        'status': 'canonical_proposal',
        'responsibility': responsibility,
        'input_contracts': inputs,
        'output_contracts': outputs,
        'depends_on': deps,
        'acceleration_profile_id': profile_id,
        'adapter_ids': adapters,
        'legacy_aliases': aliases,
        'source_attachment_sha256': sha,
        'execution_policy': {
            'source_write': False,
            'code_execution': False,
            'network': False,
            'subprocess': False,
            'package_install': 'explicit_only',
        },
    }


def main() -> int:
    data = copy.deepcopy(json.loads(SOURCE.read_text(encoding='utf-8')))
    data['schema'] = 'VIA_SSOT_ENGINE_REGISTRY/5.0'
    data['registry_id'] = 'VIA-SSOT-REG-000004'
    data['registry_version'] = '5.0.0'
    data['status'] = 'PROPOSAL_REVIEW_REQUIRED'
    data['system']['version'] = '5.0.0'
    data['system']['registry_id'] = 'VIA-SSOT-REG-000004'
    data['system']['registry_version'] = '5.0.0'

    # Update the existing E3 standardization proposal to the newer v1000 source lineage.
    for engine in data['engines']:
        if engine['engine_id'] == 'VIA-ENG-015':
            engine['version'] = '10.0.0'
            engine['source_attachment_sha256'] = '88aff36e3be04d2265b2e256667714e2c2c334de914ea37ca3c9d91060895eb7'
            engine['legacy_aliases'] += ['via_engine_standardizer(3).py', 'Invoke-VIA-EngineStandardizer(3).ps1', 'VES v1000']
            engine['output_contracts'] += ['VIA-CTR-036']
            engine['responsibility'] += ' v5 source adds E3 sandbox, Hydra, decision-token and verify-dir orchestration; apply remains human-gated.'

    data['engines'].extend([
        make_engine('VIA-ENG-018', 'Enhanced NLP and SSOT Lexicon Engine', '強化 NLP 與 SSOT 詞庫引擎', 'VIA-ENLP', '5.0.0', 'semantic_engine', 'Apply versioned Regex, synonym, factor and parameter libraries to protected normalization, multilingual classification, entity/factor extraction and evidence-linked NLP projections.', ['VIA-CTR-006', 'VIA-CTR-007', 'VIA-CTR-008'], ['VIA-CTR-030'], ['VIA-ENG-001', 'VIA-ENG-004', 'VIA-ENG-008', 'VIA-ENG-011'], 'VIA-PRF-018', ['VIA-ADP-013'], ['VIA_NLP_SSOT_Lexicon_v5.json', 'Enhanced NLP v5', 'SSOT Regex/同義字/因子/參數庫'], sha256(ROOT / 'VIA_NLP_SSOT_Lexicon_v5.json')),
        make_engine('VIA-ENG-019', 'Command Convergence and Instruction Simplification Engine', '指令收斂與指令簡化引擎', 'VIA-CCIS', '5.0.0', 'governance_engine', 'Normalize instruction synonyms, build command signatures, merge similar command candidates, preserve member commands and emit proposal-only canonical command groups.', ['VIA-CTR-010', 'VIA-CTR-018', 'VIA-CTR-030'], ['VIA-CTR-032'], ['VIA-ENG-005', 'VIA-ENG-008', 'VIA-ENG-011'], 'VIA-PRF-019', ['VIA-ADP-014', 'VIA-ADP-015'], ['similar command merge', 'VES_AI_COLLAB/1.0 decision handoff'], 'a4b8f8f6a4a798d2d92a2a0f18da2cbf6df3ad236dc4a1e9d0f58f4f71b3a6a0'),
        make_engine('VIA-ENG-020', 'Dialogue Topic and Evidence Summary Engine', '對話主題與證據摘要引擎', 'VIA-DTES', '5.0.0', 'semantic_engine', 'Reconstruct topic episodes, speakers, timestamps, topic return links and multi-layer evidence-linked summaries without deleting source units.', ['VIA-CTR-009', 'VIA-CTR-012', 'VIA-CTR-030'], ['VIA-CTR-031', 'VIA-CTR-033'], ['VIA-ENG-005', 'VIA-ENG-007', 'VIA-ENG-008', 'VIA-ENG-011'], 'VIA-PRF-020', ['VIA-ADP-013', 'VIA-ADP-015'], ['enhanced dialogue reconstruction', 'VIA summary v5', 'topic episode builder'], 'a4b8f8f6a4a798d2d92a2a0f18da2cbf6df3ad236dc4a1e9d0f58f4f71b3a6a0'),
    ])

    data['adapters'].extend([
        {'adapter_id':'VIA-ADP-013','canonical_name':'SSOT Regex Synonym Factor Parameter Library Adapter','version':'5.0.0','from_engine':'VIA-ENG-018','to_engines':['VIA-ENG-004','VIA-ENG-005','VIA-ENG-018','VIA-ENG-019','VIA-ENG-020'],'input':'versioned lexicon, source text and protected spans','output':'normalized terms, regex evidence, factors, parameter candidates and confidence','source_writeback':False,'code_execution':False,'network':False,'legacy_aliases':['VIA_NLP_SSOT_Lexicon_v5.json']},
        {'adapter_id':'VIA-ADP-014','canonical_name':'Similar Command Merge Adapter','version':'5.0.0','from_engine':'VIA-ENG-019','to_engines':['VIA-ENG-005','VIA-ENG-009'],'input':'proposal-only command candidates and normalized signatures','output':'merge groups, representative goal, union actions, member IDs and similarity evidence','source_writeback':False,'executable':False,'legacy_aliases':['similar command convergence']},
        {'adapter_id':'VIA-ADP-015','canonical_name':'VES AI Decision Handoff Adapter','version':'1.0.0','from_engine':'VIA-ENG-019','to_engines':['VIA-ENG-008','VIA-ENG-015'],'input':'restricted decision tokens, task cards, slices and verify reports','output':'append-only decision candidates and human approval status','source_writeback':'approval_only','canonical_write':False,'legacy_aliases':['VES_AI_COLLAB/1.0']},
        {'adapter_id':'VIA-ADP-016','canonical_name':'CGC ABC Safe Fix Candidate Adapter','version':'2.0.0','from_engine':'VIA-ENG-008','to_engines':['VIA-ENG-015','VIA-ENG-009'],'input':'static findings, fixability, CGC token and sandbox report','output':'fixed-copy candidate, backup ledger, compile gate and review queue','source_writeback':'approval_only','code_execution':'sandbox_only','legacy_aliases':['VIA_CGC_ABC_AutoFixEngine_v0200.py']},
        {'adapter_id':'VIA-ADP-017','canonical_name':'VIA E3 Standardizer v1000 Control Adapter','version':'10.0.0','from_engine':'VIA-ENG-015','to_engines':['VIA-ENG-006','VIA-ENG-008','VIA-ENG-009'],'input':'source root, scan policy, Hydra profile, decision token and verify-dir','output':'inventory, merge plan, candidate adapters, sandbox report and verification report','source_writeback':'approval_only','network':'explicit_localhost_only','legacy_aliases':['via_engine_standardizer(3).py','Invoke-VIA-EngineStandardizer(3).ps1']},
        {'adapter_id':'VIA-ADP-018','canonical_name':'Enhanced NLP Test Fixture Adapter','version':'5.0.0','from_engine':'VIA-ENG-018','to_engines':['VIA-ENG-019','VIA-ENG-020','VIA-ENG-008'],'input':'gold fixtures, thresholds and expected conservation gates','output':'benchmark rows, selected threshold and regression report','source_writeback':False,'code_execution':False,'legacy_aliases':['VIA_NLP_v5_Threshold_Benchmark']},
    ])

    data['contracts'].extend([
        {'contract_id':'VIA-CTR-030','name':'NLP SSOT Lexicon Projection','schema':'VIA_NLP_SSOT_LEXICON_PROJECTION/1.0','owner':'VIA-ENG-018'},
        {'contract_id':'VIA-CTR-031','name':'Dialogue Topic Episode Reconstruction','schema':'VIA_DIALOGUE_TOPIC_EPISODE/1.0','owner':'VIA-ENG-020'},
        {'contract_id':'VIA-CTR-032','name':'Similar Command Merge Candidate','schema':'VIA_SIMILAR_COMMAND_MERGE/1.0','owner':'VIA-ENG-019'},
        {'contract_id':'VIA-CTR-033','name':'Evidence Linked Enhanced Summary','schema':'VIA_EVIDENCE_LINKED_SUMMARY/1.0','owner':'VIA-ENG-020'},
        {'contract_id':'VIA-CTR-034','name':'VES AI Decision Handoff','schema':'VIA_VES_AI_DECISION_HANDOFF/1.0','owner':'VIA-ENG-019'},
        {'contract_id':'VIA-CTR-035','name':'CGC ABC Safe Fix Candidate','schema':'VIA_CGC_ABC_SAFE_FIX_CANDIDATE/1.0','owner':'VIA-ENG-008'},
        {'contract_id':'VIA-CTR-036','name':'VIA E3 Standardizer Control Plane','schema':'VIA_E3_STANDARDIZER_CONTROL/1.0','owner':'VIA-ENG-015'},
    ])

    data['gates'].extend([
        {'gate_id':'VIA-GATE-023','name':'Lexicon Integrity Gate','condition':'Regex, synonym, factor and parameter libraries are versioned, parseable, deterministic and protected tokens remain unchanged.','failure':'FAIL_CLOSED'},
        {'gate_id':'VIA-GATE-024','name':'Command Conservation Gate','condition':'Similar-command merge preserves every original command ID and sets executable=false for every merged projection.','failure':'FAIL_CLOSED'},
        {'gate_id':'VIA-GATE-025','name':'Topic Boundary Gate','condition':'Topic episodes retain source unit IDs, speaker/timestamp evidence and unresolved return links.','failure':'HOLD_REVIEW'},
        {'gate_id':'VIA-GATE-026','name':'Summary Evidence Gate','condition':'Every key point, question, constraint and summary claim links to source units; summary never replaces source.','failure':'HOLD_REVIEW'},
        {'gate_id':'VIA-GATE-027','name':'AutoFix Source Gate','condition':'AutoFix remains fixed-copy or approval-only; source write-back requires token, sandbox, backup and verification.','failure':'BLOCK'},
        {'gate_id':'VIA-GATE-028','name':'Decision Freshness Gate','condition':'VES decision tokens and slices match the current source hash, plan hash and expected token hint.','failure':'BLOCK'},
        {'gate_id':'VIA-GATE-029','name':'NLP Regression Fixture Gate','condition':'Threshold benchmark and representative fixtures pass source preservation, command conservation and non-executable semantic rewrite checks.','failure':'FAIL_CLOSED'},
    ])

    data['artifacts'].extend([
        {'artifact_id':'VIA-ART-019','name':'NLP SSOT Lexicon v5','filename':'VIA_NLP_SSOT_Lexicon_v5.json','schema':'VIA_NLP_SSOT_LEXICON/5.0','owner':'VIA-ENG-018'},
        {'artifact_id':'VIA-ART-020','name':'Enhanced NLP Reconstruction Bundle v5','filename':'VIA_NLP_Reconstruction_Bundle_v5.json','schema':'VIA_NLP_RECONSTRUCTION_BUNDLE/5.0','owner':'VIA-ENG-018'},
        {'artifact_id':'VIA-ART-021','name':'Command Similarity Benchmark','filename':'VIA_NLP_v5_Threshold_Benchmark.json','schema':'VIA_NLP_THRESHOLD_BENCHMARK/5.0','owner':'VIA-ENG-019'},
        {'artifact_id':'VIA-ART-022','name':'Topic Reconstruction Report','filename':'topic_reconstruction.json','schema':'VIA_DIALOGUE_TOPIC_EPISODE/1.0','owner':'VIA-ENG-020'},
        {'artifact_id':'VIA-ART-023','name':'Command Merge Projection','filename':'command_similarity_merge.json','schema':'VIA_SIMILAR_COMMAND_MERGE/1.0','owner':'VIA-ENG-019'},
        {'artifact_id':'VIA-ART-024','name':'V5 Regression Report','filename':'VIA_NLP_v5_Regression_Report.json','schema':'VIA_NLP_REGRESSION_REPORT/5.0','owner':'VIA-ENG-008'},
        {'artifact_id':'VIA-ART-025','name':'V5 Integration Matrix','filename':'VIA_NLP_Integration_Matrix_v5.html','schema':'VIA_NLP_INTEGRATION_MATRIX/5.0','owner':'VIA-ENG-008'},
    ])

    data['acceleration_profiles'].extend([
        profile('VIA-PRF-018','VIA-ENG-018','balanced','lexicon cache, protected span index, multilingual token batch and factor/parameter lookup'),
        profile('VIA-PRF-019','VIA-ENG-019','safe','signature cache, bounded greedy merge, command conservation and proposal-only output'),
        profile('VIA-PRF-020','VIA-ENG-020','balanced','topic anchor index, incremental episodes, return links and evidence-ranked summary'),
    ])
    data['activation_gates'].extend([f'VIA-GATE-{i:03d}' for i in range(23, 30)])
    data['v5_integration'] = {
        'version': '5.0.0',
        'lexicon': str(ROOT / 'VIA_NLP_SSOT_Lexicon_v5.json'),
        'core': str(ROOT / 'v5/via_nlp_reconstruction_v5.py'),
        'threshold_benchmark': str(ROOT / 'v5/VIA_NLP_v5_Threshold_Benchmark.json'),
        'attachments': {
            'via_engine_standardizer(3).py': sha256(Path('/home/ubuntu/upload/via_engine_standardizer(3).py')),
            'Invoke-VIA-EngineStandardizer(3).ps1': sha256(Path('/home/ubuntu/upload/Invoke-VIA-EngineStandardizer(3).ps1')),
            'VES_AI_COLLAB(1).md': sha256(Path('/home/ubuntu/upload/VES_AI_COLLAB(1).md')),
            'VIA_CGC_ABC_AutoFixEngine_v0200.py': sha256(Path('/home/ubuntu/upload/VIA_CGC_ABC_AutoFixEngine_v0200.py')),
        },
        'new_engine_ids': ['VIA-ENG-018', 'VIA-ENG-019', 'VIA-ENG-020'],
        'new_adapter_ids': ['VIA-ADP-013', 'VIA-ADP-014', 'VIA-ADP-015', 'VIA-ADP-016', 'VIA-ADP-017', 'VIA-ADP-018'],
        'new_contract_ids': ['VIA-CTR-030', 'VIA-CTR-031', 'VIA-CTR-032', 'VIA-CTR-033', 'VIA-CTR-034', 'VIA-CTR-035', 'VIA-CTR-036'],
        'new_gate_ids': ['VIA-GATE-023', 'VIA-GATE-024', 'VIA-GATE-025', 'VIA-GATE-026', 'VIA-GATE-027', 'VIA-GATE-028', 'VIA-GATE-029'],
        'source_policy': 'source_original preserved; lexical, topic, command and summary outputs are derivative projections; AutoFix is approval-only.',
        'selected_command_threshold': 0.45,
    }
    TARGET.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(TARGET)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
