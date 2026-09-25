"""全名冊月營收：期別、先查庫、來源優先及同日避免重抓；零網路。"""
import importlib.util
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
import duckdb

VIA = Path(__file__).resolve().parents[3]


class MonthlyScope(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        p = sorted((VIA / 'functional modules/VDF/engine').glob('VDF_ENG063_MonthlyRevenue_v*.py'))[-1]
        spec = importlib.util.spec_from_file_location('monthly_scope', p)
        self.m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.m)
        self.m.DB_TW = self.root / 'market.duckdb'
        self.m.VIA = self.root
        self.m.os = SimpleNamespace(environ={'VIA_NET_CONSENT': 'YES'})
        self.universe = {'2330': {}, '6488': {}}
        self.m._universe_owner = lambda: SimpleNamespace(fetch_universe=lambda db, codes: self.universe,
                                                         snapshot_day=lambda: '2026-09-25')
        with duckdb.connect(str(self.m.DB_TW)) as con:
            self.m._ensure_schema(con)

    def test_source_priority_does_not_double_count(self):
        with duckdb.connect(str(self.m.DB_TW)) as con:
            con.execute("INSERT INTO tw_monthly_revenue VALUES ('2330','202608',100,'MOPS_OFFICIAL','2026-09-25'),"
                        "('2330','202608',500,'CNYES:fixture','2026-09-25')")
            self.assertEqual(con.execute('SELECT code,ym,revenue FROM monthly_revenue_analysis').fetchall(),
                             [('2330', '202608', 100.0)])

    def test_coverage_uses_canonical_period_clock(self):
        with duckdb.connect(str(self.m.DB_TW)) as con:
            con.execute("INSERT INTO tw_monthly_revenue VALUES ('2330','202608',100,'MOPS_OFFICIAL','2026-09-25'),"
                        "('6488','202606',50,'MOPS_OFFICIAL','2026-09-25')")
            cov = self.m.revenue_coverage(con, ['2330', '6488', '1101'], '2026-09-25')
            self.assertEqual(cov['missing'], ['1101'])
            self.assertEqual(cov['overdue'], ['6488'])
            self.assertEqual(cov['covered'], 2)

    def test_same_day_full_roster_skips_network(self):
        with duckdb.connect(str(self.m.DB_TW)) as con:
            con.executemany('INSERT INTO tw_monthly_revenue VALUES (?, ?, ?, ?, ?)',
                            [(c, '202608', 100, 'MOPS_OFFICIAL', '2026-09-25') for c in self.universe])
        self.m._net = lambda: self.fail('already fetched today')
        self.assertEqual(self.m.run(), 0)

    def test_no_roster_no_network_or_new_db(self):
        self.universe.clear()
        self.m._net = lambda: self.fail('missing roster')
        self.assertEqual(self.m.run(), 3)

    def test_official_failure_or_missing_codes_not_green(self):
        self.m._net = lambda: object()
        self.m.run_mops = lambda net, con, ts: (0, ['TWSE'])
        self.assertEqual(self.m.run(), 2)
        self.assertTrue((self.root / 'VIA_Reports/monthly_revenue/COVERAGE_latest.json').exists())

    def test_default_does_not_probe_commercial_for_whole_universe(self):
        self.m._net = lambda: SimpleNamespace(http_json=lambda u: self.fail('unapproved candidate bulk'))
        def official(net, con, ts):
            # 未覆蓋的另一碼仍回報缺口，不對全市場盲探測。
            con.execute("INSERT INTO tw_monthly_revenue VALUES ('2330','202608',100,'MOPS_OFFICIAL',?)", [ts])
            return 1, []
        self.m.run_mops = official
        self.assertEqual(self.m.run(), 2)


if __name__ == '__main__':
    unittest.main()
