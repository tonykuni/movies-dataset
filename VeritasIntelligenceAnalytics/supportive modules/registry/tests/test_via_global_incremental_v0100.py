"""全球日更負控：永久 checkpoint 不阻更新；查實庫水位、補尾段、保留缺載態。"""
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(graceful 缺席零影響) =====
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
    VIA_ACCEL = None
# ===== [VIA:ACCEL-BRIDGE:END] =====

import calendar
import importlib.util
import json
from pathlib import Path
import tempfile
import time
from types import SimpleNamespace
import unittest
import duckdb

VIA = Path(__file__).resolve().parents[3]


class GlobalIncremental(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        path = sorted((VIA / 'functional modules/VDF/engine').glob('VDF_ENG055_OmniFetch_v*.py'))[-1]
        spec = importlib.util.spec_from_file_location('omni_incremental', path)
        self.m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.m)
        self.m.VIA = root
        self.m.DB_GL = root / 'global.duckdb'
        self.m.CKPT = root / 'checkpoint.json'
        self.m.CKPT.write_text(json.dumps({'done': ['^GSPC']}))
        self.m.write_parquet = lambda rows, stem: None
        for k in ('IDX_ASIA', 'IDX_EU', 'IDX_SOUTH_ASIA', 'FX', 'ETF_REGION'):
            setattr(self.m, k, [])
        self.m.IDX_US = ['^GSPC']
        reg = root / 'supportive modules/registry'
        reg.mkdir(parents=True)
        (reg / 'VIA_Global_Universe_v0100.json').write_text(json.dumps({'categories': [
            {'cat': 'commodity_future', 'symbols': ['GC=F']},
            {'cat': 'spot_pending', 'symbols': [], 'pending_note': 'no verified source'}]}))
        with duckdb.connect(str(self.m.DB_GL)) as con:
            con.execute('CREATE TABLE global_daily(date VARCHAR,ticker VARCHAR,adj_close DOUBLE)')
            con.execute("INSERT INTO global_daily VALUES ('2026-09-20','^GSPC',100)")

    def test_checkpoint_does_not_disable_daily_and_roster_is_used(self):
        calls = []
        def fetch(symbols, start, end):
            calls.append((symbols, start))
            return {'rows': [{'date': '2026-09-24', 'ticker': s, 'adj_close': 110} for s in symbols]}
        r = self.m.lane_global(SimpleNamespace(yahoo_chart=fetch))
        mapping = {s: start for symbols, start in calls for s in symbols}
        self.assertEqual(set(mapping), {'^GSPC', 'GC=F'})
        self.assertEqual(mapping['^GSPC'], calendar.timegm(time.strptime('2026-09-13', '%Y-%m-%d')))
        self.assertEqual(mapping['GC=F'], calendar.timegm(time.strptime(self.m.START_DATE, '%Y-%m-%d')))
        self.assertEqual(r['state'], 'PARTIAL')
        self.assertEqual(r['pending_categories'], ['spot_pending'])
        with duckdb.connect(str(self.m.DB_GL), read_only=True) as con:
            self.assertEqual(con.execute("SELECT max(date) FROM global_daily WHERE ticker='^GSPC'").fetchone()[0], '2026-09-24')
            self.assertEqual(con.execute('SELECT DISTINCT provider FROM global_daily WHERE provider IS NOT NULL').fetchall(), [('YAHOO',)])

    def test_missing_response_keeps_symbol_named(self):
        r = self.m.lane_global(SimpleNamespace(yahoo_chart=lambda *a: {'rows': []}))
        self.assertEqual(r['state'], 'PARTIAL')
        self.assertEqual(r['failed'], ['GC=F', '^GSPC'])

    def test_read_error_does_not_trigger_full_download(self):
        self.m.DB_GL.write_bytes(b'not a duckdb')
        net = SimpleNamespace(yahoo_chart=lambda *a: self.fail('must not fetch after failed database read'))
        with self.assertRaises(duckdb.Error):
            self.m.lane_global(net)

    def test_partial_lane_cannot_return_success(self):
        self.m.gate_open = lambda: True
        self.m._net_or_none = lambda: object()
        self.m.LANES = {'L6': ('global', lambda net: {'state': 'PARTIAL', 'rows': 0})}
        self.assertEqual(self.m.run(['L6']), 2)


if __name__ == '__main__':
    unittest.main()
