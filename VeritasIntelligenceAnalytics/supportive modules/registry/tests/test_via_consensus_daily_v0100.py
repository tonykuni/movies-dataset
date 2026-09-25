"""全名冊、增量、來源時間與完整回包：零網路，僅暫存 DuckDB。"""
import importlib.util
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import duckdb

VIA = Path(__file__).resolve().parents[3]
VRN = VIA / 'functional modules/VRN'


def load(pattern, name):
    p = sorted(VRN.glob(pattern))[-1]
    spec = importlib.util.spec_from_file_location(name, p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


class DailyConsensus(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db = Path(self.tmp.name) / 'market.duckdb'
        with duckdb.connect(str(self.db)) as con:
            con.execute('CREATE TABLE tw_listings(code VARCHAR, market VARCHAR)')
            con.executemany('INSERT INTO tw_listings VALUES (?,?)',
                            [('2330', 'TWSE'), ('6488', 'TPEX'), ('9999', 'UNKNOWN')])
            con.execute('CREATE TABLE tw_listings_industry(code VARCHAR, market VARCHAR)')
            con.execute("INSERT INTO tw_listings_industry VALUES ('1101','TWSE')")
        self.store = load('VRN_ENG069_ConsensusDB_v*.py', 'store_test')
        self.store.snapshot_day = lambda: '2026-09-25'
        self.yahoo = load('VRN_ENG070_YahooConsensus_v*.py', 'yahoo_test')
        self.cnyes = load('VRN_ENG071_CnyesFusion_v*.py', 'cnyes_test')
        for m in (self.yahoo, self.cnyes):
            m.DB_TW = self.db
            m._store = lambda: self.store
            # 僅模組自己的假環境與假網路；不設行程 CONSENT、不載任何真網路。
            m.os = SimpleNamespace(environ={'VIA_NET_CONSENT': 'YES'})

    def rows(self, sql):
        with duckdb.connect(str(self.db), read_only=True) as con:
            return con.execute(sql).fetchall()

    def test_universe_and_missing_file_no_creation(self):
        got = self.store.fetch_universe(self.db)
        self.assertEqual(set(got), {'1101', '2330', '6488'})
        self.assertEqual(got['6488']['symbol'], '6488.TWO')
        self.assertEqual(self.store.fetch_universe(self.db, ['6488']), {'6488': got['6488']})
        missing = self.db.parent / 'absent.duckdb'
        self.assertEqual(self.store.fetch_universe(missing), {})
        self.assertFalse(missing.exists())

    def test_day_uses_taipei(self):
        m = load('VRN_ENG069_ConsensusDB_v*.py', 'day_test')
        import datetime
        seen = []
        class Clock(datetime.datetime):
            @classmethod
            def now(cls, tz=None):
                seen.append(tz.utcoffset(None))
                return datetime.datetime(2026, 9, 24, 17, tzinfo=datetime.timezone.utc).astimezone(tz)
        with patch.object(m._dt, 'datetime', Clock):
            self.assertEqual(m.snapshot_day(), '2026-09-25')
        self.assertEqual(seen, [datetime.timedelta(hours=8)])

    def test_yahoo_all_symbols_raw_fields_and_same_day_zero_fetch(self):
        calls = []
        def fetch(symbols, modules):
            calls.append(symbols)
            self.assertTrue({'earningsHistory', 'recommendationTrend', 'upgradeDowngradeHistory'} <= set(modules.split(',')))
            return {'state': 'OK', 'data': {
                s: {'financialData': {'targetMeanPrice': {'raw': 120}, 'extra': '完整欄位'},
                    'earningsTrend': {'trend': [{'period': '0y', 'endDate': '2026-12-31',
                                               'earningsEstimate': {'avg': {'raw': 8}}}]}}
                for s in symbols}}
        self.yahoo._net = lambda: SimpleNamespace(yahoo_quote_summary_raw=fetch)
        self.assertEqual(self.yahoo.run(), 0)
        self.assertEqual(set(calls[0]), {'1101.TW', '2330.TW', '6488.TWO'})
        self.assertEqual(self.yahoo.run(), 0)
        self.assertEqual(len(calls), 1)
        self.assertEqual(self.rows('SELECT count(*) FROM consensus_daily'), [(3,)])
        rows = self.rows('SELECT provider_asof_raw, fetched_at_utc, payload_json FROM consensus_observations')
        self.assertTrue(all(r[0] is None and r[1].endswith('+00:00') for r in rows))
        self.assertEqual(json.loads(rows[0][2])['financialData']['extra'], '完整欄位')
        self.assertIn('2026-12-31', rows[0][2])

    def test_yahoo_partial_retry_only_missing(self):
        calls = []
        def fetch(symbols, modules):
            calls.append(symbols)
            return {'state': 'OK', 'data': {s: {'financialData': {}} for s in symbols if s != '6488.TWO'}}
        self.yahoo._net = lambda: SimpleNamespace(yahoo_quote_summary_raw=fetch)
        self.assertEqual(self.yahoo.run(), 2)
        self.assertEqual(self.yahoo.run(), 2)
        self.assertEqual(calls[1], ['6488.TWO'])
        self.assertEqual(self.rows("SELECT count(*) FROM consensus_observations WHERE state='ERROR'"), [(1,)])

    def test_eps_without_target_is_not_dropped(self):
        row = self.yahoo.parse_symbol({'earningsTrend': {'trend': [
            {'period': '+1y', 'earningsEstimate': {'avg': {'raw': 0}}}]}})
        self.assertIsNotNone(row)
        self.assertEqual(row['eps_fy1'], 0)
        self.assertIsNone(row['target_mean'])

    def test_tpex_close_no_future_price(self):
        with duckdb.connect(str(self.db)) as con:
            con.execute('CREATE TABLE prices_canonical(ticker VARCHAR, date VARCHAR, close DOUBLE)')
            con.execute("INSERT INTO prices_canonical VALUES ('6488.TWO','2026-09-24',100),"
                        "('6488.TWO','2026-09-26',500),('6488.TW','2026-09-24',999)")
            row = self.yahoo.parse_symbol({'financialData': {'targetMeanPrice': {'raw': 120}}})
            self.yahoo.upsert(con, '2026-09-25', '6488', row, '6488.TWO')
        self.assertEqual(self.rows('SELECT close FROM consensus_daily'), [(100.0,)])

    def test_cnyes_asof_full_payload_market_and_years(self):
        calls = []
        def get(net, url):
            calls.append(url)
            if 'targetPrice' in url:
                return {'feMedian': 100, 'rateDate': '2026-09-21', 'currency': 'TWD', 'last': 90}
            return [{'financialYear': 2025, 'feMean': 3}, {'financialYear': 2026, 'feMean': 5},
                    {'financialYear': 2027, 'feMean': 7}, {'financialYear': 2028, 'feMean': 9}]
        self.cnyes._net = lambda: object()
        self.cnyes._get = get
        self.assertEqual(self.cnyes.run(['6488']), 0)
        self.assertTrue(all('TWO:6488:STOCK' in u for u in calls))
        self.assertEqual(self.rows('SELECT eps_fy0, eps_fy1 FROM consensus_daily'), [(5.0, 7.0)])
        row = self.rows('SELECT snapshot_date, provider_asof_raw, payload_json FROM consensus_observations')[0]
        self.assertEqual(row[:2], ('2026-09-25', '2026-09-21'))
        self.assertEqual(len(json.loads(row[2])['estimateProfit']), 4)
        self.assertEqual(self.cnyes.run(['6488']), 0)
        self.assertEqual(len(calls), 2)

    def test_missing_next_year_not_relabelled(self):
        row = self.cnyes.parse_eps([{'financialYear': 2026, 'feMean': 5},
                                   {'financialYear': 2029, 'feMean': 99}], 2026)
        self.assertEqual(row, {'eps_fy0': 5, 'eps_fy1': None})

    def test_cnyes_partial_payload_keeps_retry_right(self):
        self.cnyes._net = lambda: object()
        self.cnyes._get = lambda net, url: {'feMedian': 100} if 'targetPrice' in url else None
        self.assertEqual(self.cnyes.run(['2330']), 2)
        self.assertEqual(self.store.pending_codes(self.db, ['2330'], 'CNYES_FACTSET', '2026-09-25'), ['2330'])
        self.assertEqual(self.rows('SELECT target_median FROM consensus_daily'), [(100.0,)])

    def test_observation_dedup_revisions_and_sources(self):
        with duckdb.connect(str(self.db)) as con:
            kw = dict(day='2026-09-25', code='2330', source='YAHOO_QS', symbol='2330.TW', urls=['https://example.test'])
            self.store.record_observation(con, payload={'x': 1}, **kw)
            self.store.record_observation(con, payload={'x': 1}, **kw)
            self.store.record_observation(con, payload={'x': 2}, **kw)
            self.store.record_observation(con, payload={'x': 1}, **{**kw, 'source': 'CNYES_FACTSET'})
        self.assertEqual(self.rows('SELECT count(*) FROM consensus_observations'), [(3,)])

    def test_no_roster_never_calls_network(self):
        self.yahoo._net = lambda: self.fail('network called before valid universe')
        self.assertEqual(self.yahoo.run(['9999']), 3)
        self.assertEqual(self.yahoo.run(['2330', '9999']), 3)

    def test_atomic_record_failure_rolls_back_daily(self):
        self.yahoo._net = lambda: SimpleNamespace(yahoo_quote_summary_raw=lambda syms, mods: {
            'data': {s: {'financialData': {'targetMeanPrice': {'raw': 120}}} for s in syms}})
        self.store.record_observation = lambda *a, **kw: (_ for _ in ()).throw(RuntimeError('disk'))
        with self.assertRaisesRegex(RuntimeError, 'disk'):
            self.yahoo.run(['2330'])
        self.assertNotIn(('consensus_daily',), self.rows('SHOW TABLES'))


if __name__ == '__main__':
    unittest.main()
