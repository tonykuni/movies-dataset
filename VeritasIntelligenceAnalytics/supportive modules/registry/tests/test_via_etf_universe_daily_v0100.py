"""ETF 官方觀測與後備分開，不用既有聯集自證仍上市；零網路。"""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import duckdb

VIA = Path(__file__).resolve().parents[3]


class ETFUniverseDaily(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        p = sorted((VIA / 'functional modules/VDF/engine').glob('VDF_ENG077_ActiveETFUniverse_v*.py'))[-1]
        spec = importlib.util.spec_from_file_location('etf_universe_daily', p)
        self.m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.m)
        self.m.DB_ETF = self.root / 'etf.duckdb'
        self.m.SSOT_CSV = self.root / 'universe.csv'
        self.m.REP = self.root / 'reports'
        self.rows = self.m.unify([
            {'ticker': '00981A', 'name': '主動台股', 'fund_type': '國內成分證券', 'source': 'TWSE', 'as_of': '1150924'},
            {'ticker': '00982A', 'name': '主動台股二', 'fund_type': '國內成分證券', 'source': 'TWSE', 'as_of': '1150924'}], [], [])
        self.m.persist(self.rows, '2026-09-24 10:00:00')
        self.actual_existing = self.m.from_existing
        self.m.from_existing = lambda: self.rows
        self.m.from_etf_book = lambda: (self.rows, 'cached')

    def test_fallback_does_not_advance_last_seen(self):
        self.assertEqual(self.m.run(['--offline']), 2)
        with duckdb.connect(str(self.m.DB_ETF), read_only=True) as con:
            self.assertEqual(con.execute(f'SELECT DISTINCT last_seen FROM {self.m.REG_TABLE}').fetchall(),
                             [('2026-09-24 10:00:00',)])
        report = json.loads(next(self.m.REP.glob('UNIVERSE_*.json')).read_text())
        self.assertEqual(report['state'], 'FALLBACK_UNVERIFIED')

    def test_missing_official_retains_history_but_not_current_csv(self):
        self.m.gate_open = lambda: True
        self.m._net_or_none = lambda: object()
        self.m.from_twse = lambda net: ([self.rows[0]], 'verified fixture')
        self.assertEqual(self.m.run([]), 2)
        with duckdb.connect(str(self.m.DB_ETF), read_only=True) as con:
            rows = con.execute(f'SELECT ticker, status, last_seen FROM {self.m.REG_TABLE} ORDER BY ticker').fetchall()
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[1], ('00982A', 'MISSING_FROM_SOURCE', '2026-09-24 10:00:00'))
        self.assertNotIn('00982A', self.m.SSOT_CSV.read_text(encoding='utf-8-sig'))
        # 隔天官方道讀不到，也不能拿舊 etf_book 後備把缺席者復活。
        self.m.from_existing = self.actual_existing
        self.assertEqual(self.m.run(['--offline']), 2)
        self.assertNotIn('00982A', self.m.SSOT_CSV.read_text(encoding='utf-8-sig'))

    def test_complete_official_preserves_source_dates(self):
        self.m.gate_open = lambda: True
        self.m._net_or_none = lambda: object()
        self.m.from_twse = lambda net: (self.rows, 'verified fixture')
        self.assertEqual(self.m.run([]), 0)
        report = json.loads(next(self.m.REP.glob('UNIVERSE_*.json')).read_text())
        self.assertEqual(report['source_dates'], ['1150924'])


if __name__ == '__main__':
    unittest.main()
