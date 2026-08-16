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


if __name__ == "__main__":
    unittest.main()
