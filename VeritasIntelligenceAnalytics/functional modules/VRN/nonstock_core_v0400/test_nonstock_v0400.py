"""Isolated contract and regression tests; no original source is mutated."""

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
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

import ast
import csv
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ENGINE = Path(__file__).with_name('NON_STOCK_CORE_v0400.py')
SPEC = importlib.util.spec_from_file_location('nonstock_under_test', ENGINE)
M = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = M
SPEC.loader.exec_module(M)
TEXT = ('管理層表示AI Server需求成長30%，帶動供應鏈訂單擴張。'
        '由於CSP資本支出增加，液冷設備與散熱訂單需求改善。'
        'NVIDIA受惠AI伺服器擴張，先進晶片出貨成長。'
        '分析師預估2027年市場仍須觀察成本上升與需求延遲風險。')


class NonStockRegression(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source = self.root / '20261108_industry.txt'
        self.source.write_text(TEXT, encoding='utf-8')

    def tearDown(self):
        self.temp.cleanup()

    def run_batch(self, **kwargs):
        return M.def_run([str(self.source)], self.root / 'out', **kwargs)

    def test_01_original_core_selftest(self):
        self.assertEqual(M.def_selftest(), 0)

    def test_02_embedded_hashes_and_ast(self):
        result = M.def_doctor()
        self.assertEqual(len(result['embedded_components']), 4)
        self.assertTrue(all(item['hash_match'] and item['ast_parse'] for item in result['embedded_components'].values()))

    def test_03_single_file_relocation(self):
        target = self.root / ENGINE.name
        target.write_bytes(ENGINE.read_bytes())
        child = subprocess.run([sys.executable, str(target), '--selftest'], capture_output=True, text=True, timeout=30)
        self.assertEqual(child.returncode, 0, child.stderr)
        child = subprocess.run([sys.executable, str(target), str(self.source), '--outdir', str(self.root / 'relocated_output'), '--csv-only'], capture_output=True, text=True, timeout=30)
        self.assertIn(child.returncode, (0, 2), child.stderr)
        pointer = json.loads((self.root / 'relocated_output/LATEST.json').read_text())
        result = json.loads((self.root / 'relocated_output' / pointer['directory'] / 'RESULTS.json').read_text())
        self.assertTrue(all(run['status'] != 'ERROR' for run in result['runs']))

    def test_04_empty_core_is_review(self):
        self.source.write_text('', encoding='utf-8')
        result = M.def_analyze(self.source)
        self.assertEqual(result['quality']['gate'], 'REVIEW')
        self.assertEqual(result['quality']['investment_guard_pass_pct'], 0)

    def test_05_multicompany_sentence_isolation(self):
        text = '甲公司(2330)目標價1200元，預估營收成長。乙公司(2317)目標價300元，預估需求增加。'
        claims = M.def_extract_claims([M.SourceBlock('s', 'f', 1, 0, 'TEXT', text)])
        self.assertEqual([c.tickers for c in claims], [['2330'], ['2317']])
        rows = M.def_integrated_module().def_company_rows('r', [], claims)
        self.assertEqual({r['TICKER']: r['TARGET_PRICE'] for r in rows}, {'2317': '300', '2330': '1200'})

    def test_06_ambiguous_financial_field_not_assigned(self):
        text = '甲公司(2330)及乙公司(2317)目標價1200元，預期訂單成長。'
        claims = M.def_extract_claims([M.SourceBlock('s', 'f', 1, 0, 'TEXT', text)])
        rows = M.def_integrated_module().def_company_rows('r', [], claims)
        self.assertTrue(all(not r['TARGET_PRICE'] and r['STATUS'] == 'REVIEW' for r in rows))

    def test_07_single_company_context(self):
        text = '台積電(2330)法說會摘要。管理層預估AI需求成長，營收提升。'
        claims = M.def_extract_claims([M.SourceBlock('s', 'f', 1, 0, 'TEXT', text)])
        self.assertTrue(all(c.tickers == ['2330'] for c in claims))

    def test_08_no_english_substring_false_positive(self):
        self.assertNotIn('EV_AUTOMOTIVE', M.def_detect_stories('revenue development'))
        self.assertNotIn('AMD', M.def_detect_anchors('exampleamdesign'))
        self.assertNotIn('RATES_BONDS', M.def_detect_stories('毛利率提升'))

    def test_09_airline_is_not_line_chat(self):
        result = M.def_profile_router(Path('airline.txt'), [])
        self.assertNotEqual(result[0], M.PROFILE_MESSENGER)
        self.assertNotEqual(M.def_integrated_module().def_route_profile(Path('pipeline.txt'), [])[0], M.PROFILE_MESSENGER)

    def test_10_numbers_are_not_stock_codes(self):
        self.assertEqual(M.def_detect_tickers('2027年營收1200億元，旅客4500人。'), [])

    def test_11_growth_decrease_and_negative_eps(self):
        metrics = M.def_metrics('營收年減12.5%，EPS -2.3。')
        values = {m['metric']: M.def_metric_value(m) for m in metrics}
        self.assertEqual(values['REVENUE_YOY'], -12.5)
        self.assertEqual(values['EPS'], -2.3)

    def test_12_period_variants(self):
        self.assertEqual([m.group() for m in M.PERIOD_RE.finditer('2026Q1 2026.Q2 FY2027')], ['2026Q1', '2026.Q2', 'FY2027'])

    def test_13_json_metadata_not_claims(self):
        path = self.root / 'meta.json'
        path.write_text(json.dumps({'metadata': 'AI營收成長30%'}))
        with self.assertRaisesRegex(ValueError, 'JSON_SCHEMA_UNSUPPORTED'):
            M.def_extract_input(path)

    def test_14_structured_json_and_duplicate_id(self):
        path = self.root / 'blocks.json'
        path.write_text(json.dumps({'blocks': [{'sid': 'same', 'text': TEXT}, {'sid': 'same', 'text': TEXT}]}))
        with self.assertRaisesRegex(ValueError, 'DUPLICATE'):
            M.def_extract_input(path)

    def test_15_claim_limit_is_explicit(self):
        with mock.patch.object(M, 'MAX_CLAIMS_PER_SOURCE', 1):
            with self.assertRaisesRegex(ValueError, 'CLAIM_LIMIT'):
                M.def_extract_claims([M.SourceBlock('s', 'f', 1, 0, 'TEXT', TEXT)])

    def test_16_input_size_limits(self):
        with mock.patch.object(M, 'MAX_INPUT_BYTES', 1):
            with self.assertRaisesRegex(ValueError, 'INPUT_BYTES_LIMIT'):
                M.def_extract_input(self.source)
        with mock.patch.object(M, 'MAX_INPUT_CHARS', 1):
            with self.assertRaisesRegex(ValueError, 'INPUT_CHARACTER_LIMIT'):
                M.def_extract_input(self.source)

    def test_17_date_calendar_validation(self):
        module = M.def_integrated_module()
        self.assertEqual(module.def_report_date(Path('20260230.txt'), []), '')
        self.assertEqual(module.def_report_date(Path('20240229.txt'), []), '2024-02-29')

    def test_18_long_point_retains_source_tail(self):
        text = '管理層表示AI伺服器需求' + '持續成長並增加供應能力，' * 30 + '但仍有成本上升風險。'
        claim = M.def_extract_claims([M.SourceBlock('s', 'f', 1, 0, 'TEXT', text)])[0]
        four = M.def_integrated_module().def_four_points([claim])
        self.assertEqual(four['POINT_1'], claim.text)
        self.assertIn('成本上升風險', four['POINT_1'])

    def test_19_main_points_have_exact_evidence(self):
        result = M.def_analyze_one(self.source)
        self.assertTrue(all(check['source_exact_match'] for check in result['point_validation']['report']))
        self.assertEqual(result['report']['EVIDENCE_COUNT'], len(result['evidence']))

    def test_20_same_filename_different_directory_has_unique_id(self):
        directory = self.root / 'other'
        directory.mkdir()
        other = directory / self.source.name
        other.write_text(TEXT)
        self.assertNotEqual(M.def_analyze_one(self.source)['report']['REPORT_ID'], M.def_analyze_one(other)['report']['REPORT_ID'])

    def test_21_csv_parquet_and_manifest(self):
        try:
            import pyarrow.parquet as pq
        except ImportError:
            self.skipTest('pyarrow is unavailable; explicit missing-dependency behavior is separately tested')
        result = self.run_batch()
        directory = Path(result['output_directory'])
        for name, receipt in result['tables'].items():
            self.assertEqual(pq.read_table(directory / (name + '.parquet')).num_rows, receipt['rows'])
            with (directory / (name + '.csv')).open(encoding='utf-8-sig') as stream:
                self.assertEqual(len(list(csv.DictReader(stream))), receipt['rows'])
        manifest = json.loads((directory / 'MANIFEST.json').read_text())
        self.assertTrue(all(M.def_file_sha256(directory / name) == sha for name, sha in manifest['sha256'].items()))

    def test_22_cache_idempotence(self):
        first = self.run_batch(parquet=False)
        second = self.run_batch(parquet=False)
        self.assertFalse(first['runs'][0]['cache_hit'])
        self.assertTrue(second['runs'][0]['cache_hit'])
        self.assertEqual(first['report_summary'], second['report_summary'])

    def test_23_cache_invalidation(self):
        self.run_batch(parquet=False)
        self.source.write_text(TEXT + '\n新增風險為原油成本上升。')
        self.assertFalse(self.run_batch(parquet=False)['runs'][0]['cache_hit'])

    def test_24_cache_corruption_recovers(self):
        self.run_batch(parquet=False)
        cache = next((self.root / 'out/cache').glob('*.json'))
        cache.write_text('{broken')
        self.assertFalse(self.run_batch(parquet=False)['runs'][0]['cache_hit'])

    def test_25_empty_or_missing_input_fails(self):
        empty = self.root / 'empty'
        empty.mkdir()
        with self.assertRaisesRegex(ValueError, 'NO_SUPPORTED_INPUT'):
            M.def_run([str(empty)], self.root / 'out', parquet=False)
        with self.assertRaises(FileNotFoundError):
            M.def_run([str(self.root / 'missing.txt')], self.root / 'out', parquet=False)

    def test_26_partial_failure_is_not_pass(self):
        broken = self.root / 'broken.json'
        broken.write_text('{broken')
        result = M.def_run([str(self.source), str(broken)], self.root / 'out', parquet=False)
        self.assertEqual(result['status'], 'REVIEW')
        self.assertIn('ERROR', [r['status'] for r in result['runs']])

    def test_27_missing_parquet_explicit(self):
        original = importlib.util.find_spec
        with mock.patch('importlib.util.find_spec', side_effect=lambda name: None if name == 'pyarrow' else original(name)):
            with self.assertRaisesRegex(RuntimeError, 'PARQUET_DEPENDENCY_MISSING'):
                self.run_batch()

    def test_28_failed_publication_retains_previous(self):
        self.run_batch(parquet=False)
        pointer = self.root / 'out/LATEST.json'
        previous = pointer.read_bytes()
        with mock.patch.object(M, 'def_write_table', side_effect=OSError('disk full')):
            with self.assertRaises(OSError):
                self.run_batch(parquet=False)
        self.assertEqual(pointer.read_bytes(), previous)
        self.assertFalse((self.root / 'out/.nonstock-writer.lock').exists())

    def test_29_existing_writer_is_not_deleted(self):
        out = self.root / 'out'
        out.mkdir()
        lock = out / '.nonstock-writer.lock'
        lock.write_text('other owner')
        with self.assertRaises(FileExistsError):
            self.run_batch(parquet=False)
        self.assertEqual(lock.read_text(), 'other owner')

    def test_30_no_network_on_text_lane(self):
        with mock.patch('socket.socket.connect', side_effect=AssertionError('network forbidden')):
            result = M.def_analyze_one(self.source)
        self.assertGreater(len(result['evidence']), 0)

    def test_31_synthetic_pdf_extraction(self):
        import fitz
        path = self.root / 'sample.pdf'
        document = fitz.open()
        page = document.new_page()
        page.insert_text((70, 70), 'AI server demand grows. NVIDIA capex expands in 2027.\nIndustry outlook and supply chain risk.')
        document.save(path)
        document.close()
        result = M.def_analyze_one(path)
        self.assertGreater(len(result['evidence']), 0)
        self.assertEqual(result['meta']['backend'], 'VRN2_M03_LAYOUT+MDL003_REPAIR')

    def test_32_synthetic_docx(self):
        from docx import Document
        path = self.root / 'sample.docx'
        document = Document()
        document.add_paragraph(TEXT)
        document.save(path)
        result = M.def_analyze_one(path)
        self.assertGreater(len(result['evidence']), 0)

    def test_33_enex_preserves_note_attribution(self):
        path = self.root / 'sample.enex'
        path.write_text('<en-export><note><title>AI Note</title><content><![CDATA[<en-note><div>我認為AI Server需求仍需觀察，2027年有成本風險。</div></en-note>]]></content></note></en-export>')
        result = M.def_analyze_one(path)
        self.assertEqual(result['report']['REPORT_TYPE'], M.PROFILE_EVERNOTE)
        self.assertTrue(any('USER' in c['attribution'] for c in result['core']['claims']))

    def test_34_unsupported_json_cli_returns_nonzero(self):
        path = self.root / 'bad.json'
        path.write_text('{}')
        result = subprocess.run([sys.executable, str(ENGINE), str(path), '--outdir', str(self.root / 'out'), '--csv-only'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)

    def test_35_input_is_not_mutated(self):
        before = self.source.read_bytes()
        self.run_batch(parquet=False)
        self.assertEqual(self.source.read_bytes(), before)

    def test_36_multiple_values_in_one_claim_are_not_confirmed_conflict(self):
        text = '台積電(2330)2027年一月營收年增10%，二月營收年增20%，需求成長。'
        claims = M.def_extract_claims([M.SourceBlock('s', 'f', 1, 0, 'TEXT', text)])
        issues = M.def_detect_contradictions(claims)
        self.assertTrue(issues)
        self.assertTrue(all(item['status'] == 'METRIC_CONTEXT_REVIEW' for item in issues))

    def test_37_headings_and_recommendation_list_not_thesis(self):
        block = M.SourceBlock('s', 'f', 1, 0, 'TEXT', '推薦相關個股:甲公司(2330)、乙公司(2317)。CSP開發自家AI晶片帶動ASIC需求和長期成長。')
        four = M.def_integrated_module().def_four_points(M.def_extract_claims([block]))
        self.assertTrue(four['POINT_1'].startswith('CSP'))

    def test_38_short_informative_blocks_are_not_dropped(self):
        self.source.write_text('管理層預期AI伺服器需求成長。\n\n由於成本上升，散熱訂單可能延遲。')
        result = M.def_analyze_one(self.source)
        self.assertEqual(len(result['topics']), 2)

    def test_39_legacy_report_id_mapping(self):
        result = M.def_analyze_one(self.source)
        digest = hashlib.sha256((self.source.name + M.def_file_sha256(self.source)[:16]).encode()).hexdigest()[:8].upper()
        self.assertEqual(result['report']['LEGACY_REPORT_ID'], 'RPT-' + digest)

    def test_40_pdf_cache_json_page_keys(self):
        import fitz
        path = self.root / 'multipage.pdf'
        document = fitz.open()
        for index in range(12):
            page = document.new_page()
            page.insert_text((70, 70), f'AI server demand grows. NVIDIA capex expands in 2027. Page {index + 1}.')
        document.save(path)
        document.close()
        first = M.def_run([str(path)], self.root / 'out', parquet=False)
        second = M.def_run([str(path)], self.root / 'out', parquet=False)
        self.assertTrue(second['runs'][0]['cache_hit'])
        self.assertEqual(first['report_summary'], second['report_summary'])

    def test_41_diagnostic_contract_is_additive(self):
        health = M.def_health()
        doctor = M.def_doctor()
        self.assertIsInstance(health['existing_via_engines'], dict)
        self.assertIsInstance(doctor['guards'], list)
        self.assertIsInstance(doctor['profiles'], list)
        self.assertIsInstance(M.def_analyze(self.source)['meta']['existing_via_engines'], dict)


if __name__ == '__main__':
    unittest.main(verbosity=2)
