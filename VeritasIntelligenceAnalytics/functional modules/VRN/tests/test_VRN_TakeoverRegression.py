#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""接手回歸：日期缺料不可假綠；有同日行情而數值不符仍必須失敗。"""
from __future__ import annotations

import importlib.util
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
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(LatestQuoteRegression))
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    raise SystemExit(main())
