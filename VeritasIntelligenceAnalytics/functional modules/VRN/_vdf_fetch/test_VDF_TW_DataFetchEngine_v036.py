"""Offline regressions. *_SIM data are synthetic; fixtures/ contains captured official samples."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("fetch_v036", HERE/"VDF_TW_DataFetchEngine_v036.py")
v = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(v)
FIX = HERE/"fixtures"


def def_fixture(name):
    return json.loads((FIX/(name+".json")).read_text(encoding="utf-8"))


def def_quote_sim():
    return pd.DataFrame([{
        **v.def_identity("2330","TWSE","台積電_SIM"),"date":pd.Timestamp("2026-10-22"),
        "open":100.0,"high":110.0,"low":90.0,"close":100.0,
        "volume":1000,"turnover":10000.0,"shares_outstanding":1000000,
    }])


class TestFetch(unittest.TestCase):
    def test_dates(self):
        for text in ("1151022","20261022","115/10/22","2026-10-22"):
            self.assertEqual(v.def_date(text),pd.Timestamp("2026-10-22"))

    def test_identities(self):
        self.assertEqual(v.def_identity("2330","TWSE","x")["yfinance_ticker"],"2330.TW")
        self.assertEqual(v.def_identity("6488","TPEX","x")["yfinance_ticker"],"6488.TWO")
        self.assertEqual(v.def_identity("6488","TPEX","x")["bloomberg_ticker"],"6488 TT")

    def test_unknown_market_rejected(self):
        with self.assertRaises(ValueError):
            v.def_identity("2330","UNKNOWN","x")

    def test_close_crosscheck_adjusts_all_ohlc(self):
        raw=def_quote_sim();yf=pd.DataFrame([{"date":raw.date[0],"ticker":"2330","yf_close":100.0,"yf_adj_close":80.0,"yf_volume":1000}])
        out=v.def_adjust_prices(raw,yf)
        self.assertEqual(out.close[0],100)
        self.assertEqual(out.adj_open[0],80)
        self.assertEqual(out.adj_low[0],72)
        self.assertEqual(out.adj_high[0],88)
        self.assertEqual(out.adj_close[0],80)
        self.assertEqual(out.volume[0],1000)

    def test_mismatch_not_adjusted(self):
        raw=def_quote_sim();yf=pd.DataFrame([{"date":raw.date[0],"ticker":"2330","yf_close":50.0,"yf_adj_close":40.0}])
        out=v.def_adjust_prices(raw,yf)
        self.assertEqual(out.close_check[0],"MISMATCH")
        self.assertTrue(pd.isna(out.adj_close[0]))

    def test_missing_adjustment_not_raw_close(self):
        out=v.def_adjust_prices(def_quote_sim(),pd.DataFrame())
        self.assertTrue(pd.isna(out.adj_close[0]))

    def test_daytrade_amount_convention(self):
        raw=def_quote_sim();raw['day_trade_volume']=300;raw['day_trade_buy_value']=2000;raw['day_trade_sell_value']=2200
        out=v.def_deduct_daytrade(raw)
        self.assertEqual(out.volume_ex_daytrade[0],700)
        self.assertEqual(out.turnover_ex_daytrade[0],7900)
        self.assertEqual(v.def_deduct_daytrade(raw,"sum").turnover_ex_daytrade[0],5800)

    def test_missing_daytrade_is_null(self):
        out=v.def_deduct_daytrade(def_quote_sim())
        self.assertEqual(out.daytrade_status[0],"MISSING")
        self.assertTrue(pd.isna(out.volume_ex_daytrade[0]))

    def test_negative_net_rejected(self):
        raw=def_quote_sim();raw['day_trade_volume']=2000;raw['day_trade_buy_value']=100;raw['day_trade_sell_value']=100
        out=v.def_deduct_daytrade(raw)
        self.assertEqual(out.daytrade_status[0],"INVALID")
        self.assertTrue(pd.isna(out.volume_ex_daytrade[0]))

    def test_official_quotes(self):
        for name,market,ticker in [('twse_daily','TWSE','2330'),('tpex_daily','TPEX','6488')]:
            frame=v.def_normalize_quotes(def_fixture(name),market,name,"2026-10-22")
            self.assertIn(ticker,frame.ticker.values)
            self.assertTrue((frame.low<=frame.high).all())

    def test_source_date_mismatch_rejected(self):
        with self.assertRaises(ValueError):
            v.def_normalize_quotes(def_fixture('twse_daily'),'TWSE','x','2026-10-21')

    def test_duplicate_raw_key_rejected(self):
        data=def_fixture('twse_daily');table=next(t for t in data['tables'] if '證券代號' in t.get('fields',[]))
        table['data'].append(table['data'][0])
        with self.assertRaises(ValueError):
            v.def_normalize_quotes(data,'TWSE','x','2026-10-22')

    def test_tpex_institutional(self):
        out=v.def_normalize_chips(def_fixture('tpex_inst'),'TPEX','institutional','2026-10-22','official')
        self.assertTrue(((out.inst_foreign_net+out.inst_trust_net+out.inst_dealer_net)==out.inst_total_net).all())

    def test_margin_lots_to_shares(self):
        out=v.def_normalize_chips(def_fixture('tpex_margin'),'TPEX','margin','2026-10-22','official')
        self.assertEqual(out.loc[out.ticker.eq('6488'),'margin_balance'].iloc[0],12958000)

    def test_real_per_stock_daytrade(self):
        out=v.def_normalize_chips(def_fixture('tpex_daytrade'),'TPEX','daytrade','2026-10-22','official')
        self.assertIn('6488',out.ticker.values)
        self.assertTrue(out.day_trade_volume.notna().all())

    def test_financial_three_statements(self):
        ident=v.def_identity('2330','TWSE','台積電')
        for name,stmt in [('mops_bs','BALANCE_SHEET'),('mops_income','INCOME_STATEMENT'),('mops_cf','CASH_FLOW')]:
            out=v.def_parse_statement((FIX/(name+'.html')).read_text(),ident,stmt,name,'2025Q4')
            self.assertFalse(out.empty)
            self.assertEqual(set(out.basis),{'POINT'} if stmt=='BALANCE_SHEET' else {'YTD'})

    def test_quarter_ytd_distinguished(self):
        out=v.def_parse_statement((FIX/'mops_income_q2.html').read_text(),v.def_identity('2330','TWSE','台積電'),'INCOME_STATEMENT','official','2026Q2')
        revenue=out.loc[out.account.eq('營業收入合計')&out.fiscal_year.eq(2026)]
        self.assertEqual(revenue.loc[revenue.basis.eq('QUARTER'),'value'].iloc[0],1270380250)
        self.assertEqual(revenue.loc[revenue.basis.eq('YTD'),'value'].iloc[0],2404483690)

    def test_financial_wrong_period_rejected(self):
        with self.assertRaises(ValueError):
            v.def_parse_statement((FIX/'mops_cf.html').read_text(),v.def_identity('2330','TWSE','x'),'CASH_FLOW','official','2026Q2')

    def test_annual_not_quarter4(self):
        raw=v.def_parse_statement((FIX/'mops_cf.html').read_text(),v.def_identity('2330','TWSE','x'),'CASH_FLOW','official','2025Q4')
        out=v.def_derive_financial_periods(raw)
        self.assertIn('ANNUAL',out.basis.values)
        self.assertNotIn('QUARTER',out.basis.values)  # no Q3 cumulative input

    def test_ytd_difference_sim(self):
        base={**v.def_identity('2330','TWSE','x_SIM'),'financial_statement':'CASH_FLOW','account':'營業現金流_SIM','unit':'TWD_THOUSAND','report_scope':'UNSPECIFIED','fiscal_year':2025,'basis':'YTD','is_derived':False,'source':'MOPS_SIM'}
        raw=pd.DataFrame([{**base,'quarter':3,'date':pd.Timestamp('2025-09-30'),'value':300}, {**base,'quarter':4,'date':pd.Timestamp('2025-12-31'),'value':450}])
        out=v.def_derive_financial_periods(raw)
        self.assertEqual(out.loc[out.basis.eq('QUARTER')&out.quarter.eq(4),'value'].iloc[0],150)

    def test_monthly_revenue(self):
        out=v.def_normalize_revenue(def_fixture('monthly_revenue'),'TWSE','official')
        self.assertEqual(set(out.account),{'MONTHLY_REVENUE','YTD_REVENUE'})
        self.assertEqual(set(out.unit),{'TWD_THOUSAND'})

    def test_atomic_idempotent_storage_and_catalog(self):
        import duckdb
        with tempfile.TemporaryDirectory() as temp:
            frame=v.def_daily_quality(v.def_deduct_daytrade(v.def_adjust_prices(def_quote_sim(),pd.DataFrame())))
            v.def_store(temp,'tw_equity_daily',frame);v.def_store(temp,'tw_equity_daily',frame)
            out=v.def_load_dataset(temp,'tw_equity_daily');self.assertEqual(len(out),1)
            v.def_catalog(temp)
            with duckdb.connect(str(Path(temp)/'VDF_TWEquity_Daily.duckdb')) as db:
                self.assertEqual(db.execute('select count(*) from tw_equity_daily').fetchone()[0],1)
            csv=next(Path(temp).glob('parquet/**/data.csv'))
            self.assertTrue(csv.read_bytes().startswith(b'\xef\xbb\xbf'))
            self.assertIn('2026/10/22',csv.read_text(encoding='utf-8-sig'))

    def test_revision_and_explicit_adjustment_invalidation(self):
        with tempfile.TemporaryDirectory() as temp:
            raw=def_quote_sim();yahoo=pd.DataFrame([{'date':raw.date[0],'ticker':'2330','yf_close':100,'yf_adj_close':80}])
            v.def_store(temp,'tw_equity_daily',v.def_daily_quality(v.def_deduct_daytrade(v.def_adjust_prices(raw,yahoo))))
            yahoo['yf_close']=50
            v.def_store(temp,'tw_equity_daily',v.def_daily_quality(v.def_deduct_daytrade(v.def_adjust_prices(raw,yahoo))))
            out=v.def_load_dataset(temp,'tw_equity_daily')
            self.assertTrue(pd.isna(out.adj_close[0]))
            self.assertTrue(list(Path(temp).glob('revisions/**/*.parquet')))

    def test_lock_blocks_second_writer(self):
        with tempfile.TemporaryDirectory() as temp:
            with v.def_run_lock(temp):
                with self.assertRaises(RuntimeError):
                    with v.def_run_lock(temp):
                        pass

    def test_official_index_and_market_activity(self):
        class CapturedClient:
            def __init__(self,root):
                self.root=Path(root)
            def json(self,url,params=None,fresh=False):
                name = ('twse_index' if 'MI_5MINS_HIST' in url else
                        'twse_market_total' if 'FMTQIK' in url else
                        'tpex_index' if 'indexInfo/inx' in url else 'tpex_daily')
                return def_fixture(name),url
        with tempfile.TemporaryDirectory() as temp:
            issues=[]
            result=v.def_collect_indices(CapturedClient(temp),pd.Timestamp('2026-10-22'),pd.Timestamp('2026-10-22'),issues)
            out=v.def_load_dataset(temp,'tw_index_daily')
            self.assertEqual(result['rows'],2)
            self.assertEqual(issues,[])
            self.assertTrue((out.volume>0).all())
            self.assertTrue((out.turnover>0).all())
            self.assertEqual(set(out.index_code),{'TAIEX','TPEX'})

    def test_source_scope_is_consolidated(self):
        out=v.def_parse_statement((FIX/'mops_cf.html').read_text(),v.def_identity('2330','TWSE','x'),'CASH_FLOW','official','2025Q4')
        self.assertEqual(set(out.report_scope),{'CONSOLIDATED'})

    def test_network_deny_does_not_fallback(self):
        class DenyBridge:
            def curl_bytes(self,*args,**kwargs):
                return {'state':'DENY'}
        with tempfile.TemporaryDirectory() as temp:
            client=v.FetchClient(temp,bridge=DenyBridge())
            with self.assertRaises(PermissionError):
                client.get('https://example.invalid/never-connect')

    def test_cash_balances_are_not_differenced(self):
        base={**v.def_identity('2330','TWSE','x_SIM'),'financial_statement':'CASH_FLOW','account':'期末現金及約當現金餘額','unit':'TWD_THOUSAND','report_scope':'CONSOLIDATED','fiscal_year':2025,'basis':'YTD','is_derived':False,'source':'MOPS_SIM'}
        raw=pd.DataFrame([{**base,'quarter':3,'date':pd.Timestamp('2025-09-30'),'value':300}, {**base,'quarter':4,'date':pd.Timestamp('2025-12-31'),'value':450}])
        out=v.def_derive_financial_periods(raw)
        self.assertNotIn('QUARTER',out.basis.values)


if __name__=='__main__':
    unittest.main(verbosity=2)
