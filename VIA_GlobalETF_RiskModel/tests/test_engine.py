# -*- coding: utf-8 -*-
"""引擎層測試：指標解析、EPS 結轉狀態機、regime 規則、資料層治理。"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from engine import data_layer as dl                      # noqa: E402
from engine.earnings import build_earnings_ledger        # noqa: E402
from engine.factors import FactorPanel, resolve_indicator  # noqa: E402
from engine.regime import classify_regime                # noqa: E402


def mini_market(days=320, up="AAA", down="BBB", bench="ACWI"):
    """人工小世界：AAA 相對基準走強、BBB 走弱、殖利率緩升。"""
    dates, prices, macro = [], {up: [], down: [], bench: []}, \
        {"DGS2": [], "DGS10": [], "DFII10": [], "T10YIE": []}
    import datetime as dt
    d = dt.date(2026, 8, 14)
    ds = dl.business_days_back(d, days)
    for i, day in enumerate(ds):
        dates.append(day.isoformat())
        prices[up].append(100.0 * (1.002 ** i))
        prices[down].append(100.0 * (0.999 ** i))
        prices[bench].append(100.0 * (1.0005 ** i))
        macro["DGS10"].append(4.0 + 0.001 * i)
        macro["DGS2"].append(4.2 + 0.001 * i)
        macro["T10YIE"].append(2.3)
        macro["DFII10"].append(4.0 + 0.001 * i - 2.3)
    return dl.MarketData(dates, prices, macro,
                         {"data_source": "unit_test", "truth_tier": "T4"})


class TestIndicatorResolver(unittest.TestCase):
    def setUp(self):
        self.panel = FactorPanel(mini_market(), benchmark="ACWI")

    def test_ret_rs_rel_chg(self):
        self.assertGreater(resolve_indicator(self.panel, "ret_20_AAA"), 0)
        self.assertGreater(resolve_indicator(self.panel, "rs_20_AAA"), 0)
        self.assertLess(resolve_indicator(self.panel, "rs_20_BBB"), 0)
        self.assertGreater(resolve_indicator(self.panel, "rel_20_AAA_BBB"), 0)
        self.assertAlmostEqual(resolve_indicator(self.panel, "chg_20_DGS10"),
                               0.02, places=6)
        self.assertAlmostEqual(resolve_indicator(self.panel, "curvechg_20"),
                               0.0, places=6)

    def test_neg_and_dd(self):
        self.assertLess(resolve_indicator(self.panel, "neg_ret_20_AAA"), 0)
        self.assertEqual(resolve_indicator(self.panel, "dd_60_AAA"), 0.0)
        self.assertGreater(resolve_indicator(self.panel, "dd_60_BBB"), 0)

    def test_unknown_grammar_raises(self):
        with self.assertRaises(ValueError):
            resolve_indicator(self.panel, "banana_20_AAA")

    def test_score_injection(self):
        self.assertEqual(
            resolve_indicator(self.panel, "score_usd_stress",
                              scores={"usd_stress": 63.0}), 63.0)
        self.assertIsNone(resolve_indicator(self.panel, "score_missing",
                                            scores={}))


class TestRegimeRules(unittest.TestCase):
    def test_single_rule_world(self):
        cfg = {"def_regimes": [
            {"id": "up_world", "name_zh": "上行", "signals": [
                {"id": "rs_20_AAA", "op": ">", "value": 0.0, "weight": 2.0},
                {"id": "rs_20_BBB", "op": "<", "value": 0.0, "weight": 1.0}]},
            {"id": "down_world", "name_zh": "下行", "signals": [
                {"id": "rs_20_AAA", "op": "<", "value": 0.0, "weight": 1.0}]},
        ]}
        panel = FactorPanel(mini_market(), benchmark="ACWI")
        out = classify_regime(panel, cfg, {})
        self.assertEqual(out["top"]["id"], "up_world")
        self.assertEqual(out["top"]["score"], 1.0)
        self.assertEqual(out["ranked"][-1]["score"], 0.0)
        self.assertEqual(out["confidence"], 1.0)


class TestEarningsCarryForward(unittest.TestCase):
    CFG = {"def_earnings": {
        "mcfl": "MCFL-M35-C35-F350",
        "carry_forward_days": {"fresh": 7, "usable": 21,
                               "stale_warning": 45, "needs_refresh": 90},
        "index_proxy_map": {"IDX": "AAA"},
        "index_country_map": {"IDX": "Xland"},
        "usd_funding_stress_pp_at_100": 1.0,
        "rounding_mismatch_tolerance": 0.0005,
        "sources_file": "unused"}}
    FUND = {"Xland": {"local_10y": 2.0, "fx_dep_risk_pp": 0.5}}

    def make(self, publish, level=2000.0, pe=20.0, **extra):
        snap = {"source_name": "T", "index_name": "IDX", "region": "X",
                "source_publish_date": publish, "index_level_used": level,
                "published_forward_pe": pe, "forward_horizon": "NTM",
                "index_type": "price"}
        snap.update(extra)
        market = mini_market()
        return build_earnings_ledger(market, self.CFG, self.FUND, [snap], 50.0)

    def test_implied_eps_and_freeze(self):
        led = self.make("2026-07-31")
        row = led["active"][0]
        self.assertAlmostEqual(row["implied_forward_eps"], 100.0, places=6)
        self.assertEqual(row["eps_status"], "Calculated_NotOriginal")
        # 每日重算的是 P/E：repriced = pe × proxy 價格比（輸出四捨五入至 2 位）
        self.assertAlmostEqual(row["daily_repriced_pe"],
                               20.0 * row["proxy_ratio_since_publish"], delta=0.01)
        # ERP = EY − local10Y；USD-adj 再扣 0.5 fx + 0.5 funding(50/100×1.0)
        self.assertAlmostEqual(row["usd_adj_erp_pp"],
                               row["erp_pp"] - 0.5 - 0.5, places=6)

    def test_staleness_ladder(self):
        cases = [("2026-08-08", "FRESH"), ("2026-07-31", "USABLE"),
                 ("2026-07-01", "STALE_WARNING"), ("2026-06-01", "NEEDS_REFRESH"),
                 ("2026-01-02", "REJECT_FOR_CURRENT_VALUATION")]
        for publish, expect in cases:
            led = self.make(publish)
            self.assertEqual(led["active"][0]["staleness"]["state"], expect,
                             "publish=%s" % publish)

    def test_rounding_devil(self):
        led = self.make("2026-07-31", level=6890.59, pe=23.1,
                        published_forward_eps=298.56)
        flags = [d["flag"] for d in led["active"][0]["devil_warnings"]]
        self.assertIn("forward_pe_rounding", flags)

    def test_source_divergence(self):
        market = mini_market()
        snaps = []
        for src, pe in (("A", 20.0), ("B", 21.5)):
            snaps.append({"source_name": src, "index_name": "IDX", "region": "X",
                          "source_publish_date": "2026-07-31",
                          "index_level_used": 2000.0, "published_forward_pe": pe,
                          "forward_horizon": "NTM", "index_type": "price"})
        led = build_earnings_ledger(market, self.CFG, self.FUND, snaps, 50.0)
        flags = [d["flag"] for r in led["rows"] for d in r["devil_warnings"]]
        self.assertIn("source_divergence", flags)


class TestDataLayer(unittest.TestCase):
    def test_demo_deterministic_and_labeled(self):
        cfg = dl.load_config()
        a = dl.generate_demo(cfg, asof="2026-08-14", days=120, seed=1)
        b = dl.generate_demo(cfg, asof="2026-08-14", days=120, seed=1)
        c = dl.generate_demo(cfg, asof="2026-08-14", days=120, seed=2)
        self.assertEqual(a.prices["SPY"], b.prices["SPY"])
        self.assertNotEqual(a.prices["SPY"], c.prices["SPY"])
        self.assertEqual(a.provenance["truth_tier"], "T4")
        self.assertEqual(a.provenance["data_source"], "synthetic_demo")

    def test_business_days_end_on_weekday(self):
        import datetime as dt
        days = dl.business_days_back(dt.date(2026, 8, 14), 10)
        self.assertEqual(len(days), 10)
        self.assertTrue(all(d.weekday() < 5 for d in days))
        self.assertEqual(days[-1], dt.date(2026, 8, 14))


class TestCsvHardening(unittest.TestCase):
    def _write(self, name, text):
        import tempfile, os
        fd, path = tempfile.mkstemp(suffix=name)
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as fh:
            fh.write(text)
        self.addCleanup(os.unlink, path)
        return path

    def test_nonfinite_cells_become_none_then_ffill(self):
        p = self._write("p.csv", "date,SPY\n2026-08-10,100\n2026-08-11,NaN\n"
                                 "2026-08-12,\n2026-08-13,inf\n2026-08-14,102\n")
        m = dl.load_csv_wide(p)
        # NaN/空值/inf 皆視為缺值 → 向前補 100，最後回到 102
        self.assertEqual(m.prices["SPY"], [100.0, 100.0, 100.0, 100.0, 102.0])

    def test_unsorted_dates_raise(self):
        p = self._write("u.csv", "date,SPY\n2026-08-14,100\n2026-08-12,99\n")
        with self.assertRaises(ValueError):
            dl.load_csv_wide(p)

    def test_duplicate_dates_raise(self):
        p = self._write("d.csv", "date,SPY\n2026-08-14,100\n2026-08-14,101\n")
        with self.assertRaises(ValueError):
            dl.load_csv_wide(p)

    def test_weekly_macro_asof_alignment(self):
        prices = ["date,SPY"]
        macro = ["date,DGS10"]
        import datetime as dt
        days = dl.business_days_back(dt.date(2026, 8, 14), 20)
        for i, d in enumerate(days):
            prices.append("%s,%d" % (d.isoformat(), 100 + i))
            if i % 5 == 0:
                macro.append("%s,%.2f" % (d.isoformat(), 4.0 + i * 0.01))
        p = self._write("p.csv", "\n".join(prices) + "\n")
        q = self._write("m.csv", "\n".join(macro) + "\n")
        m = dl.load_csv_wide(p, q)
        self.assertEqual(len(m.macro["DGS10"]), len(m.dates))
        # 第 0 天有錨；第 3 天沿用第 0 天錨值；第 5 天換新錨
        self.assertAlmostEqual(m.macro["DGS10"][3], 4.00)
        self.assertAlmostEqual(m.macro["DGS10"][5], 4.05)
        self.assertAlmostEqual(m.macro["DGS10"][-1], m.macro["DGS10"][15])


class TestRoundThreeHardening(unittest.TestCase):
    def test_run_id_unique_within_second(self):
        from engine import report as rp
        ids = {rp.make_run_id() for _ in range(50)}
        self.assertEqual(len(ids), 50)

    def test_future_publish_date_flagged_not_fresh(self):
        cfg = TestEarningsCarryForward.CFG
        fnd = TestEarningsCarryForward.FUND
        from engine.earnings import build_earnings_ledger
        snap = [{"source_name": "T", "index_name": "IDX", "region": "X",
                 "source_publish_date": "2026-12-31", "index_level_used": 2000.0,
                 "published_forward_pe": 20.0, "forward_horizon": "NTM",
                 "index_type": "price"}]
        led = build_earnings_ledger(mini_market(), cfg, fnd, snap, 50.0)
        r = led["active"][0]
        self.assertEqual(r["staleness"]["state"], "FUTURE_DATED")
        self.assertEqual(r["carry_forward_state"], "NEEDS_SOURCE_REVIEW")
        self.assertIn("publish_date_in_future",
                      [d["flag"] for d in r["devil_warnings"]])

    def test_fragility_dirty_values_skipped_not_crash(self):
        from engine.factors import FactorPanel
        from engine.scores import compute_fragility
        cfg = dl.load_config()
        panel = FactorPanel(mini_market(up="SPY", down="EWT"), benchmark="ACWI")
        fnd = {"US": {"name_zh": "美國", "etf": "SPY",
                      "debt_gdp": "<script>alert(1)</script>",
                      "fiscal_balance_gdp": -6.5},
               "TW": {"name_zh": "台灣", "etf": "EWT",
                      "debt_gdp": 27.0, "fiscal_balance_gdp": True}}
        rows = compute_fragility(panel, cfg, fnd)
        by = {r["country"]: r for r in rows}
        # 字串/bool 欄位被跳過而非崩潰；乾淨欄位照算
        self.assertNotIn("debt_gdp", by["US"]["detail"])
        self.assertNotIn("fiscal_balance_gdp", by["TW"]["detail"])
        self.assertIn("fiscal_balance_gdp", by["US"]["detail"])
        self.assertIn("debt_gdp", by["TW"]["detail"])

    def test_config_only_ticker_extension(self):
        import copy
        import run_monitor as rm
        cfg = copy.deepcopy(dl.load_config())
        cfg["def_etf_universe"]["emerging_markets"].append(
            {"ticker": "KWEB", "name": "中國互聯網", "region": "China",
             "haven_level": 4})
        cfg_path = Path(__file__).resolve().parents[1] / "config" / \
            "global_etf_risk_config.json"
        m = dl.generate_demo(cfg, asof="2026-08-14", days=300, seed=7)
        ds = rm.build_dataset(cfg, cfg_path, m)
        tickers = [r["ticker"] for rows in ds["heatmap"].values() for r in rows]
        self.assertIn("KWEB", tickers)


class TestShortDataGracefulDegrade(unittest.TestCase):
    def test_40d_end_to_end_renders(self):
        import run_monitor as rm
        from engine import report as rp
        cfg = dl.load_config()
        cfg_path = Path(__file__).resolve().parents[1] / "config" / \
            "global_etf_risk_config.json"
        m = dl.generate_demo(cfg, asof="2026-08-14", days=40, seed=1)
        ds = rm.build_dataset(cfg, cfg_path, m)
        # 暖機不足的分數應為 None + pending 帶，而非假數字
        self.assertIsNone(ds["scores"]["commodity_inflation"]["risk"])
        self.assertEqual(ds["scores"]["commodity_inflation"]["band"]["id"],
                         "pending")
        html = rp.render_dashboard(ds)
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn("—", html)


if __name__ == "__main__":
    unittest.main()
