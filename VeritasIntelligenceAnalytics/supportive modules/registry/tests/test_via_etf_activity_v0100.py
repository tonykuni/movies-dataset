"""Source/timing/estimation regressions; all inputs and databases are synthetic."""
from __future__ import annotations
import copy
import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

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

VIA = Path(__file__).resolve().parents[3]
path = sorted((VIA / "functional modules/VDF/engine").glob("VDF_ENG094_ActiveETFActivity_v*.py"))[-1]
spec = importlib.util.spec_from_file_location("activity_under_test", path)
M = importlib.util.module_from_spec(spec)
spec.loader.exec_module(M)


def fixture(start="2026-09-01", end="2026-09-02", before=100, after=120, price=20):
    source = "https://example.invalid/synthetic-fixture"
    fetched = end + "T13:00:00+00:00"
    action = {"state": "VERIFIED", "factor": 1, "start": start, "end": end, "as_of": end, "source_url": source, "fetched_at_utc": fetched}
    def fund(day, units):
        return {"as_of": day, "units": units, "nav": 10, "aum": units * 10, "currency": "TWD", "source_url": source, "fetched_at_utc": fetched}
    def holdings(day, shares):
        return {"as_of": day, "complete": True, "currency": "TWD", "source_url": source, "fetched_at_utc": fetched,
                "positions": [{"code": "2330", "shares": shares}]}
    return {"schema": M.SCHEMA, "etf_ticker": "00999A", "start": start, "end": end, "currency": "TWD",
            "fund_previous": fund(start, 1000), "fund_current": fund(end, 1100),
            "fund_adjustment": copy.deepcopy(action), "holdings_previous": holdings(start, before),
            "holdings_current": holdings(end, after), "holding_adjustments": {"2330": copy.deepcopy(action)},
            "prices": {"2330": {"as_of": end, "start": start, "end": end, "price": price,
                                 "currency": "TWD", "method": "INTERVAL_VWAP", "coverage_complete": True, "source_url": source, "fetched_at_utc": fetched}}}


class ActivityTests(unittest.TestCase):
    def test_fund_and_constituent_flows_are_different(self):
        r = M.analyze(fixture())
        self.assertEqual(r["state"], "ESTIMATE")
        self.assertEqual(r["fund"]["net_subscription_value_estimate"], 1000)
        self.assertEqual(r["holdings"][0]["net_position_value_estimate"], 400)
        self.assertIsNone(r["fund"]["gross_redemptions"])
        self.assertIsNone(r["holdings"][0]["actual_trade_cost"])

    def test_fund_split_is_not_subscription(self):
        f = fixture();f["fund_current"].update(units=2000, nav=5, aum=10000);f["fund_adjustment"]["factor"] = 2
        self.assertEqual(M.analyze(f)["fund"]["net_subscription_value_estimate"], 0)

    def test_share_split_is_not_buy(self):
        f = fixture(before=100, after=200);f["holding_adjustments"]["2330"]["factor"] = 2
        self.assertEqual(M.analyze(f)["holdings"][0]["net_position_value_estimate"], 0)

    def test_unverified_actions_withhold_values(self):
        f=fixture();f.pop("fund_adjustment");f["holding_adjustments"]={}
        r=M.analyze(f)
        self.assertEqual(r["state"],"REVIEW")
        self.assertIsNone(r["fund"]["net_subscription_value_estimate"])
        self.assertIsNone(r["holdings"][0]["net_position_value_estimate"])

    def test_aum_nav_conflict_and_fetch_date_do_not_pass(self):
        f=fixture();f["fund_current"]["aum"] *= 1000;f["fund_previous"].pop("as_of");f["fund_previous"]["fetched_at_utc"]="2026-09-01T00:00:00Z"
        r=M.analyze(f)["fund"]
        self.assertIsNone(r["net_subscription_value_estimate"])
        self.assertTrue(any("CONFLICT" in i for i in r["issues"]))
        self.assertTrue(any("ASOF" in i for i in r["issues"]))

    def test_price_interval_currency_and_method_guard(self):
        for field,value in (("end","2026-09-03"),("currency","USD"),("method","UNKNOWN"),("coverage_complete",False),("price",None)):
            with self.subTest(field=field):
                f=fixture();f["prices"]["2330"][field]=value
                self.assertIsNone(M.analyze(f)["holdings"][0]["net_position_value_estimate"])

    def test_incomplete_snapshot_is_not_liquidation(self):
        f=fixture();f["holdings_current"].update(complete=False, positions=[])
        r=M.analyze(f)
        self.assertIsNone(r["holdings"][0]["net_shares"])
        self.assertIsNone(M.summarize([r])[0]["estimated_average_sell_price"])

    def test_confirmed_entry_and_exit(self):
        f=fixture();f["holdings_previous"]["positions"]=[]
        self.assertEqual(M.analyze(f)["holdings"][0]["net_shares"],120)
        f=fixture();f["holdings_current"]["positions"]=[]
        self.assertEqual(M.analyze(f)["holdings"][0]["net_shares"],-100)
        self.assertEqual(M.summarize([M.analyze(f)])[0]["estimated_average_sell_price"],20)

    def test_invalid_and_duplicate_shares(self):
        for val in (None,-1,True):
            f=fixture();f["holdings_current"]["positions"][0]["shares"]=val
            self.assertIsNone(M.analyze(f)["holdings"][0]["net_shares"])
        f=fixture();f["holdings_current"]["positions"] *= 2
        self.assertIsNone(M.analyze(f)["holdings"][0]["net_shares"])

    def test_quantity_weighted_buy_sell_separately(self):
        a=M.analyze(fixture(before=100,after=110,price=10))
        b=M.analyze(fixture("2026-09-02","2026-09-03",110,140,20))
        c=M.analyze(fixture("2026-09-03","2026-09-04",140,120,30))
        r=M.summarize([a,b,c])[0]
        self.assertEqual(r["estimated_average_buy_price"],17.5)
        self.assertEqual(r["estimated_average_sell_price"],30)
        self.assertEqual((r["buy_qty"],r["sell_qty"]),(40,20))

    def test_missing_price_gap_and_overlap(self):
        a=M.analyze(fixture());f=fixture("2026-09-02","2026-09-03");f["prices"]={};b=M.analyze(f)
        self.assertIsNone(M.summarize([a,b])[0]["estimated_average_buy_price"])
        c=M.analyze(fixture("2026-09-04","2026-09-05"))
        self.assertIsNone(M.summarize([a,c])[0]["estimated_average_buy_price"])
        with self.assertRaisesRegex(ValueError,"Overlapping"):
            M.summarize([a,a])

    def test_discontinuous_snapshots_withhold_period_average(self):
        a=M.analyze(fixture(before=100,after=110))
        b=M.analyze(fixture("2026-09-02","2026-09-03",100,120))
        r=M.summarize([a,b])[0]
        self.assertTrue(r["snapshot_discontinuity"])
        self.assertIsNone(r["estimated_average_buy_price"])

    def test_period_never_averages_pre_and_post_split_units(self):
        a=M.analyze(fixture(before=100,after=110,price=100))
        b=fixture("2026-09-02","2026-09-03",110,240,50)
        b["holding_adjustments"]["2330"]["factor"]=2
        r=M.summarize([a,M.analyze(b)])[0]
        self.assertTrue(r["period_share_basis_requires_normalization"])
        self.assertIsNone(r["estimated_average_buy_price"])

    def test_unknown_snapshot_blocks_other_stock_period(self):
        a=M.analyze(fixture());f=fixture("2026-09-02","2026-09-03")
        for k in ("holdings_previous","holdings_current"):
            f[k]["complete"]=False;f[k]["positions"]=[{"code":"2454","shares":3}]
        rows=M.summarize([a,M.analyze(f)])
        self.assertIsNone(next(r for r in rows if r["code"]=="2330")["estimated_average_buy_price"])

    def test_exact_iso_and_json_nonfinite(self):
        for k,v in (("start","20260901"),("end","2026-02-30"),("currency","USD")):
            f=fixture();f[k]=v
            with self.assertRaises(ValueError):M.analyze(f)
        f=fixture();f["prices"]["2330"]["price"]=float("nan")
        with self.assertRaises(ValueError):M.analyze(f)

    def test_absent_database_plan_does_not_create(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"missing.duckdb"
            self.assertEqual(M.inspect_database(p)["state"],"NODATA")
            with self.assertRaisesRegex(ValueError,"refusing"):
                M.build(p,[fixture()],apply=True)
            self.assertFalse(p.exists())

    def test_persistence_dedup_cache_and_revisions(self):
        import duckdb
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"test.duckdb";duckdb.connect(str(p)).close()
            a=fixture();a["source_revision_at"]="2026-09-02T12:00:00Z"
            with patch.object(M,"analyze",wraps=M.analyze) as compute:
                first=M.build(p,[a,a],apply=True)
                self.assertEqual(compute.call_count,1)
            self.assertEqual(first["computed"],1)
            with patch.object(M,"analyze",side_effect=AssertionError("cached input recalculated")):
                second=M.build(p,apply=True)
            self.assertEqual(second["cached"],1)
            b=copy.deepcopy(a);b["prices"]["2330"]["price"]=25;b["source_revision_at"]="2026-09-02T13:00:00Z"
            M.build(p,[b],apply=True)
            latest=M.build(p)
            self.assertEqual(latest["summary"][0]["estimated_average_buy_price"],25)
            with duckdb.connect(str(p),read_only=True) as con:
                self.assertEqual(con.execute("SELECT count(*) FROM etf_activity_inputs").fetchone()[0],2)
                self.assertEqual(con.execute("SELECT count(*) FROM etf_activity_results").fetchone()[0],2)

    def test_conflicting_revisions_are_not_hash_ordered(self):
        a=fixture();b=copy.deepcopy(a);b["prices"]["2330"]["price"]=30
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(ValueError,"Conflicting source revisions"):
                M.build(Path(td)/"absent.duckdb",[a,b])

    def test_retrieval_time_is_not_a_data_revision(self):
        import duckdb
        a=fixture();b=copy.deepcopy(a)
        def refreshed(item):
            if isinstance(item,dict):
                for key,value in item.items():
                    if key=="fetched_at_utc":item[key]="2026-09-03T13:00:00+00:00"
                    else:refreshed(value)
            elif isinstance(item,list):
                for value in item:refreshed(value)
        refreshed(b)
        self.assertNotEqual(M.digest(a),M.digest(b))
        self.assertEqual(M.data_digest(a),M.data_digest(b))
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"test.duckdb";duckdb.connect(str(p)).close()
            M.build(p,[a],apply=True)
            with patch.object(M,"analyze",side_effect=AssertionError("unchanged data recalculated")):
                r=M.build(p,[b],apply=True)
            self.assertEqual((r["computed"],r["cached"]),(0,1))
            self.assertEqual(M.build(p)["state"],"ESTIMATE")
            with duckdb.connect(str(p),read_only=True) as con:
                self.assertEqual(con.execute("SELECT count(*) FROM etf_activity_inputs").fetchone()[0],2)
                self.assertEqual(con.execute("SELECT count(*) FROM etf_activity_results").fetchone()[0],1)
            for invalid in ("INVALID", "VALID_FETCH_TIMESTAMP", [True,None], None):
                b["fund_current"]["fetched_at_utc"]=invalid
                self.assertNotEqual(M.data_digest(a),M.data_digest(b))
                self.assertEqual(M.analyze(b)["state"],"REVIEW")
                with self.assertRaisesRegex(ValueError,"Conflicting source revisions"):
                    M.build(p,[b],apply=True)

    def test_incremental_conflict_is_rejected_before_persistence(self):
        import duckdb
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"test.duckdb";duckdb.connect(str(p)).close()
            a=fixture();b=copy.deepcopy(a);b["prices"]["2330"]["price"]=30
            M.build(p,[a],apply=True)
            with self.assertRaisesRegex(ValueError,"Conflicting source revisions"):
                M.build(p,[b],apply=True)
            with duckdb.connect(str(p),read_only=True) as con:
                self.assertEqual(con.execute("SELECT count(*) FROM etf_activity_inputs").fetchone()[0],1)
                self.assertEqual(con.execute("SELECT count(*) FROM etf_activity_results").fetchone()[0],1)
            self.assertEqual(M.build(p)["state"],"ESTIMATE")

    def test_position_order_and_numeric_json_format_are_not_revisions(self):
        import duckdb
        a=fixture()
        for key,shares in (("holdings_previous",10),("holdings_current",20)):
            a[key]["positions"].append({"code":"2454","shares":shares})
        for key in ("holding_adjustments","prices"):
            a[key]["2454"]=copy.deepcopy(a[key]["2330"])
        b=copy.deepcopy(a)
        for key in ("holdings_previous","holdings_current"):
            b[key]["positions"].reverse()
            for row in b[key]["positions"]:row["shares"]=float(row["shares"])
        for key in ("fund_previous","fund_current"):
            for field in ("nav","units","aum"):b[key][field]=float(b[key][field])
        self.assertNotEqual(M.digest(a),M.digest(b))
        self.assertEqual(M.data_digest(a),M.data_digest(b))
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"test.duckdb";duckdb.connect(str(p)).close();M.build(p,[a],apply=True)
            with patch.object(M,"analyze",side_effect=AssertionError("equivalent data recalculated")):
                r=M.build(p,[b],apply=True)
            self.assertEqual((r["computed"],r["cached"],r["state"]),(0,1,"ESTIMATE"))

    def test_result_failure_rolls_back_inputs(self):
        import duckdb
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"test.duckdb";duckdb.connect(str(p)).close()
            original=M._LIB.UTILS.upsert_select
            def fail(con,table,*args,**kwargs):
                if table=="etf_activity_results":raise RuntimeError("injected result failure")
                return original(con,table,*args,**kwargs)
            with patch.object(M._LIB.UTILS,"upsert_select",side_effect=fail):
                with self.assertRaisesRegex(RuntimeError,"injected"):
                    M.build(p,[fixture()],apply=True)
            with duckdb.connect(str(p),read_only=True) as con:
                self.assertEqual(con.execute("SHOW TABLES").fetchall(),[])

    def test_canonical_template_and_untrusted_text(self):
        f=fixture();evil="</script><script>window.badETF=true</script>"
        f["fund_current"]["source_url"]="https://example.invalid/"+evil
        with tempfile.TemporaryDirectory() as td:
            root=Path(os.environ.get("VIA_ETF_UAT_OUT") or td)
            report=M.build(Path(td)/"absent.duckdb",[f])
            entry=M.template_report(report,root)
            self.assertTrue(entry.exists())
            page=(root/"ui/VIA-UI-Standalone-NoServer.html").read_text()
            self.assertIn("VIA_REGISTER_ADDON",page)
            self.assertNotIn(evil,page)
            self.assertIn("\\u003c/script>",page)
            source=(M.VIA/"VIA_HTML_UI/ui/VIA-UI-Standalone-NoServer.html").read_text()
            begin=page.index('<script id="via-etf-activity-data"')
            end=page.index('</body>',begin)
            self.assertEqual(page[:begin]+page[end:],source)


if __name__=="__main__":
    unittest.main()
