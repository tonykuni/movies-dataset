
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

import importlib.util
import sys
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import json
import duckdb

ROOT = Path(__file__).resolve().parents[2]


def def_load(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


HIST = def_load('panorama_hist_test', 'functional modules/VDF/engine/VDF_ENG064_HistoryBackfill_v0111.py')
ETF = def_load('panorama_etf_test', 'functional modules/VDF/engine/VDF_ENG078_ActiveETFHoldingsHistory_v0108.py')


def def_row(day, ticker, close=100):
    return dict(date=day, ticker=ticker, open=100., high=max(101., close), low=min(99., close), close=float(close), adj_close=float(close), volume=10.)


def def_db(path, rows):
    c = duckdb.connect(str(path))
    c.execute('CREATE TABLE tw_daily_prices(date VARCHAR,ticker VARCHAR,open DOUBLE,high DOUBLE,low DOUBLE,close DOUBLE,adj_close DOUBLE,volume DOUBLE)')
    c.executemany('INSERT INTO tw_daily_prices VALUES (?,?,?,?,?,?,?,?)', [list(r.values()) for r in rows])
    c.close()


class GapFetch(unittest.TestCase):
    def test_plan_missing_db_never_creates_it(self):
        with tempfile.TemporaryDirectory() as d:
            db = Path(d) / 'not_here.duckdb'
            self.assertEqual(HIST.def_gap_plan('2026-09-14','2026-09-15',db)['state'], 'BLOCKED_DB')
            self.assertFalse(db.exists())

    def test_only_missing_day_is_fetched_and_rerun_zero_network(self):
        with tempfile.TemporaryDirectory() as d, patch.dict(os.environ, VIA_NET_CONSENT='YES', VIA_SCRAPE_CONSENT='YES'):
            db = Path(d)/'price.duckdb'
            def_db(db,[def_row('2026-09-14','2330.TW'), def_row('2026-09-15','2330.TW'), def_row('2026-09-14','3324.TWO')])
            seen = []
            def fetch(net, tickers, start, end):
                seen.append(tickers)
                return {'rows':[def_row('2026-09-15','3324.TWO')], 'failed':[]}
            with patch.object(HIST, '_fetch_batch', side_effect=fetch):
                a=HIST.def_gap_run('2026-09-14','2026-09-15',db,True,net=object())
                b=HIST.def_gap_run('2026-09-14','2026-09-15',db,True,net=object())
            self.assertEqual(seen, [['3324.TWO']])
            self.assertEqual(a['state'],'COMPLETE')
            self.assertEqual((a['inserted'],b['requests_sent']), (1,0))
            self.assertEqual(len(list((Path(d)/'history_gap_batches').glob('batch_*.csv'))),1)
            self.assertEqual(len(list((Path(d)/'history_gap_batches').glob('batch_*.parquet'))),1)

    def test_staged_batch_replays_without_second_fetch_after_write_failure(self):
        with tempfile.TemporaryDirectory() as d, patch.dict(os.environ, VIA_NET_CONSENT='YES', VIA_SCRAPE_CONSENT='YES'):
            db=Path(d)/'price.duckdb'
            def_db(db,[def_row('2026-09-14','2330.TW')])
            with patch.object(HIST,'_fetch_batch',return_value={'rows':[def_row('2026-09-15','2330.TW')]}), patch.object(HIST,'def_gap_commit',side_effect=RuntimeError('write interrupted')):
                a=HIST.def_gap_run('2026-09-14','2026-09-15',db,True,net=object())
            self.assertEqual(a['state'],'PARTIAL')
            with patch.object(HIST,'_fetch_batch',side_effect=AssertionError('must not fetch')):
                b=HIST.def_gap_run('2026-09-14','2026-09-15',db,True,net=object())
            self.assertEqual(b['replayed'],1)
            self.assertEqual(b['state'],'COMPLETE')

    def test_failure_never_becomes_complete(self):
        with tempfile.TemporaryDirectory() as d, patch.dict(os.environ, VIA_NET_CONSENT='YES', VIA_SCRAPE_CONSENT='YES'):
            db=Path(d)/'price.duckdb'
            def_db(db,[def_row('2026-09-14','2330.TW')])
            with patch.object(HIST,'_fetch_batch',return_value={'rows':[], 'failed':[{'ticker':'2330.TW','note':'timeout'}]}) as f:
                a=HIST.def_gap_run('2026-09-14','2026-09-15',db,True,net=object())
                b=HIST.def_gap_run('2026-09-14','2026-09-15',db,True,net=object())
            self.assertEqual((a['state'], b['state'], f.call_count),('PARTIAL','PARTIAL',2))

    def test_conflicting_duplicate_rejected_and_volume_not_forward_filled(self):
        a=def_row('2026-09-15','2330.TW')
        b=def_row('2026-09-15','2330.TW',101)
        good,bad=HIST.def_gap_validate([a,b],['2330.TW'],['2026-09-15'])
        self.assertEqual(good,[])
        self.assertTrue(bad)
        a['volume']=None
        good,bad=HIST.def_gap_validate([a],['2330.TW'],['2026-09-15'])
        self.assertEqual(good,[])

    def test_existing_quality_gap_not_hidden(self):
        with tempfile.TemporaryDirectory() as d:
            db=Path(d)/'price.duckdb'
            r=def_row('2026-09-14','2330.TW');r['adj_close']=None
            def_db(db,[r])
            p=HIST.def_gap_plan('2026-09-14','2026-09-14',db)
            self.assertEqual(p['missing_keys'],0)
            self.assertEqual(p['quality_gaps'][0]['fields'],['adj_close'])

    def test_legacy_failure_not_checkpointed_as_done(self):
        with tempfile.TemporaryDirectory() as d:
            db=Path(d)/'price.duckdb'
            def_db(db,[def_row('2026-09-14','2330.TW')])
            with patch.object(HIST,'CKPT',Path(d)/'ck.json'),patch.object(HIST,'SEGMENTS',[('test','2026-09-14','2026-09-15')]),patch.object(HIST,'_BREAK',{'tripped':False}),patch.object(HIST,'_fetch_batch',return_value={'rows':[],'failed':[{'ticker':'2330.TW'}]}):
                HIST._run_db(object(),db,'tw_daily_prices',HIST._tickers_tw,'台股',None)
                ck=json.loads((Path(d)/'ck.json').read_text())
            self.assertEqual(ck['segments']['台股:test'],[])

    def test_etf_bounds_stale_checkpoint_and_snapshot_presence_scope(self):
        with tempfile.TemporaryDirectory() as d, patch.object(ETF,'CKPT',Path(d)/'ck.json'),patch.object(ETF,'DB_TW',Path(d)/'none.duckdb'),patch.object(ETF,'universe',return_value=[{'ticker':'00981A','name':'Test','issuer':'test','first_seen':'2025-01-01'}]),patch.object(ETF,'snapshot_dates',return_value={'00981A':['2026-09-14']}):
            ck={'days':{'00981A':{'2026-09-15':{'state':'FILLED'}}}}
            r=ETF.coverage(None,ck,'2026-09-14','2026-09-15',save=False)
            self.assertEqual(r['etfs'][0]['expected_days'],2)
            self.assertEqual(r['etfs'][0]['missing_days'],1)
            self.assertEqual(ck['days']['00981A']['2026-09-15']['state'],'MISSING')
            self.assertFalse((Path(d)/'ck.json').exists())

    def test_etf_exchange_comes_from_ssot_not_tw_assumption(self):
        with tempfile.TemporaryDirectory() as d, patch.object(ETF,'DB_TW',Path(d)/'prices.duckdb'):
            def_db(ETF.DB_TW,[def_row('2026-09-14','2330.TW'),def_row('2026-09-14','3324.TWO')])
            self.assertEqual(ETF.def_holding_yf('3324'),'3324.TWO')
            self.assertEqual(ETF.def_holding_yf('2330'),'2330.TW')
            self.assertIsNone(ETF.def_holding_yf('9999'))

    def test_etf_single_batch_duplicate_and_atomic_rollback(self):
        with tempfile.TemporaryDirectory() as d, patch.object(ETF,'DB_ETF',Path(d)/'ActiveTWETF.duckdb'):
            c=duckdb.connect(str(ETF.DB_ETF))
            c.execute('CREATE TABLE holdings_daily(portfolio_date VARCHAR,etf_ticker VARCHAR,holding_ticker VARCHAR,shares DOUBLE CHECK(shares>=0))')
            c.close()
            self.assertEqual(ETF.upsert_holdings('00981A','2026-09-14',[{'holding_ticker':'2330','shares':1},{'holding_ticker':'2330','shares':1}]),1)
            with self.assertRaises(Exception):
                ETF.upsert_holdings('00981A','2026-09-15',[{'holding_ticker':'2330','shares':1},{'holding_ticker':'2317','shares':-1}])
            c=duckdb.connect(str(ETF.DB_ETF),read_only=True)
            self.assertEqual(c.execute('SELECT count(*) FROM holdings_daily').fetchone()[0],1)
            c.close()


if __name__=='__main__':
    unittest.main()
