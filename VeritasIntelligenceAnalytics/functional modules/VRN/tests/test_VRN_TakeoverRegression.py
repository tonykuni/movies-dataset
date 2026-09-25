#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""接手回歸：缺行情不假綠；修訂百分比不冒充金額；錯誤金額仍判錯。"""
from __future__ import annotations

import importlib.util
import copy
import sys
import unittest
from pathlib import Path

TESTS = Path(__file__).resolve().parent
VIA = TESTS.parents[2]

# [VIA:ACCEL-BRIDGE] Existing mother accelerator, optional in isolated tests.
def def_accelerator():
    support = VIA / 'supportive modules'
    if support.is_dir() and str(support) not in sys.path:
        sys.path.insert(0, str(support))
    try:
        import VIA_SuperAccel_Module
        return VIA_SuperAccel_Module
    except ImportError:
        return None


def def_load_oracle():
    spec = importlib.util.spec_from_file_location('takeover_price_oracle', TESTS / 'test_VRN_AdjOracle.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class LatestQuoteRegression(unittest.TestCase):
    def test_missing_same_day_quote_is_nodata(self):
        case = def_load_oracle().AdjOracleInvariantTest('test_the_latest_adj_close_is_the_traded_price')
        case.latest = {'2330.TW': (100.0, '2026-09-23', None)}
        with self.assertRaisesRegex(unittest.SkipTest, 'NODATA.*0/1'):
            case.test_the_latest_adj_close_is_the_traded_price()

    def test_wrong_same_day_price_still_fails(self):
        case = def_load_oracle().AdjOracleInvariantTest('test_the_latest_adj_close_is_the_traded_price')
        case.latest = {'2330.TW': (100.0, '2026-09-23', 80.0)}
        with self.assertRaises(AssertionError):
            case.test_the_latest_adj_close_is_the_traded_price()

    def test_partial_coverage_keeps_numeric_check_and_reports_gap(self):
        case = def_load_oracle().AdjOracleInvariantTest('test_the_latest_adj_close_is_the_traded_price')
        case.latest = {'2330.TW': (100.0, '2026-09-23', 100.0), '1101.TW': (50.0, '2026-09-23', None)}
        case.test_the_latest_adj_close_is_the_traded_price()
        with self.assertRaisesRegex(unittest.SkipTest, 'coverage 1/2'):
            case.test_latest_exchange_quote_coverage()

    def test_complete_coverage_passes(self):
        case = def_load_oracle().AdjOracleInvariantTest('test_the_latest_adj_close_is_the_traded_price')
        case.latest = {'2330.TW': (100.0, '2026-09-23', 100.0)}
        case.test_the_latest_adj_close_is_the_traded_price()
        case.test_latest_exchange_quote_coverage()


def def_load_financial_engine():
    path = TESTS.parent / 'engine/VRN_Integrated_ReportDatabase_Engine.py'
    spec = importlib.util.spec_from_file_location('takeover_financial_engine', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def def_revision_fixture():
    """Synthetic values in the merged revision-header layout observed in a real industry report."""
    return {'TableID': 'SYNTHETIC_REVISION', 'PageNumber': 3, 'Rows': [
        ['(NT$mn)', '2026E 2027E 2028E New Old Chg. New Old Chg. New Old Chg.', '', '', '', '', '', '', '', '', ''],
        ['Sales', '400', '320', '25%', '500', '400', '25%', '600', '480', '25%', ''],
        ['Sequential growth', '25%', '20%', '', '25%', '25%', '', '20%', '20%', '', ''],
        ['Gross Profit', '120', '100', '20%', '150', '120', '25%', '180', '140', '28.6%', ''],
        ['Operating Expenses', '20', '10', '100%', '30', '20', '50%', '40', '30', '33.3%', ''],
        ['Operating Profit', '100', '90', '11.1%', '120', '100', '20%', '140', '110', '27.3%', ''],
    ]}


class FinancialRevisionRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = def_load_financial_engine()

    def records(self, table=None):
        return self.engine.parse_financial_tables_to_records([table or def_revision_fixture()],
                                                            {'ReportID': 'SYNTHETIC_INDUSTRY', 'TW_TICKER': ''}, 'test')

    def test_year_and_revision_roles_are_recovered(self):
        rows = self.records()
        sales = [r for r in rows if r['MetricName'] == 'Revenue']
        self.assertEqual([r['FiscalYear'] for r in sales], [2026]*3 + [2027]*3 + [2028]*3)
        self.assertEqual([r['PeriodLabelRaw'] for r in sales[:3]], ['2026E New', '2026E Old', '2026E Chg.'])
        self.assertTrue(all(r['TW_TICKER'] == '' for r in rows))

    def test_percentage_body_cannot_set_amount_units(self):
        rows = self.records()
        self.assertEqual((rows[0]['Unit'], rows[0]['Scale']), ('NT$m', 1_000_000))
        self.assertEqual(rows[2]['Unit'], '%')

    def test_percent_changes_keep_evidence_but_not_wide_amount(self):
        rows = self.records()
        r = next(r for r in rows if r['MetricName'] == 'Revenue' and r['ColumnIndex'] == 3)
        self.assertEqual((r['Value'], r['ValueRaw']), (25.0, '25%'))
        self.assertIn('PERCENT_CHANGE', r['ValidationIssues'])
        self.assertEqual(r['ValidationStatus'], 'REVIEW')
        self.assertIn(r['Revenue'], (None, ''))

    def test_valid_amount_identities_exclude_percentage_changes(self):
        check = self.engine.financial_identity_checks(self.records())
        self.assertEqual((check['checked'], check['passed'], check['failed']), (6, 6, []))
        self.assertGreater(check['excluded_non_amount_rows'], 0)

    def test_wrong_amount_still_fails(self):
        table = def_revision_fixture()
        table['Rows'][-1][1] = '130'
        check = self.engine.financial_identity_checks(self.records(table))
        self.assertEqual(len(check['failed']), 1)
        self.assertEqual(check['failed'][0]['got'], 130)

    def test_ambiguous_merged_header_is_not_guessed(self):
        table = def_revision_fixture()
        table['Rows'][0][1] = '2026E 2027E 2028E Forecasts'
        rows = self.records(table)
        self.assertTrue(rows)
        self.assertTrue(all(r['FiscalYear'] is None for r in rows))
        self.assertTrue(all('PERIOD_UNCLEAR' in r['ValidationIssues'] for r in rows))

    def test_extra_value_column_prevents_header_expansion(self):
        table = def_revision_fixture()
        table['Rows'][1][-1] = '999'
        self.assertEqual(self.engine.expand_revision_header(table['Rows'][0], table['Rows'][1:]), table['Rows'][0])

    def test_mixed_units_do_not_receive_a_pass(self):
        rows = copy.deepcopy(self.records())
        next(r for r in rows if r['MetricName'] == 'OperatingProfit' and r['ColumnIndex'] == 1)['Scale'] = 1000
        check = self.engine.financial_identity_checks(rows)
        self.assertEqual(check['checked'], 5)
        self.assertEqual(check['skipped_unit_checks'], 1)

    def test_per_share_and_margin_units_override_table_amounts(self):
        self.assertEqual(self.engine.infer_unit_and_scale('EPS (NT$)', '(NT$mn)', '5.3'), ('NT$', 'TWD', 1.0))
        self.assertEqual(self.engine.infer_unit_and_scale('Gross Margin', '(NT$mn)', '30'), ('%', 'TWD', 1.0))


def def_emit_finstat_fixture(directory):
    """Synthetic contract fixture, explicitly separate from real market data."""
    import duckdb
    root = Path(directory).resolve()
    root.mkdir(parents=True, exist_ok=True)
    path = sorted((VIA / 'functional modules/VRN').glob('VRN_ENG090_FinStatementsTemplate_v*.py'))[-1]
    spec = importlib.util.spec_from_file_location('takeover_finstat', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    e82, details = module.upstream()
    if e82 is None:
        raise RuntimeError(details)
    db = root / 'synthetic_finstat.duckdb'
    if db.exists():
        raise FileExistsError(db)
    with duckdb.connect(str(db)) as con:
        con.execute(f'CREATE TABLE {e82.MOPS_TABLE} ({e82.MOPS_SCHEMA})')
        con.execute(f'CREATE TABLE {e82.MOPS_LOG} ({e82.MOPS_LOG_SCHEMA})')
        con.execute('CREATE TABLE tw_listings (code VARCHAR, name VARCHAR, market VARCHAR)')
        for market, code in [('TWSE', '1101'), ('TPEX', '6147')]:
            con.execute('INSERT INTO tw_listings VALUES (?, ?, ?)', [code, 'SYNTHETIC FIXTURE', market])
            for statement, name in e82.MOPS_ST.items():
                for industry in e82.MOPS_IND:
                    source = e82._mops_source(market, statement, industry)
                    count = 1 if industry == 'ci' else 0
                    if count:
                        con.execute(f'INSERT INTO {e82.MOPS_TABLE} (date,code,name,market,industry,statement,basis,item,value,unit,period,report_date,source,fetched_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                                    ['2026-06-30', code, 'SYNTHETIC FIXTURE', market, industry, name, 'YTD' if name == 'IS' else 'POINT', '營業收入', 100.0, '仟元', '2026Q2', '115/08/10', source, '2026-09-24 10:00:00'])
                    con.execute(f'INSERT INTO {e82.MOPS_LOG} VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',
                                [market, name, industry, source, 'OK', 1, count, count, '2026Q2' if count else None, '2026-06-30' if count else None, 'SYNTHETIC FIXTURE', '2026-09-24 10:00:00'])
    return db


def main():
    def_accelerator()
    if '--emit-fixture' in sys.argv:
        print(def_emit_finstat_fixture(sys.argv[sys.argv.index('--emit-fixture') + 1]))
        return 0
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]))
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    raise SystemExit(main())
