import importlib.util
import unittest
from pathlib import Path


ENGINE_PATH = (
    Path(__file__).resolve().parents[1] / "VIA_TW_Branch_Capital_Circle_Engine.py"
)
SPEC = importlib.util.spec_from_file_location("capital_circle_engine", ENGINE_PATH)
ENGINE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(ENGINE)


class CapitalCirclePureFunctionTests(unittest.TestCase):
    def build_observations(self):
        rows = []
        for day in range(1, 11):
            date_value = f"2026-08-{day:02d}"
            rows.extend([
                {
                    "date": date_value, "stock_id": "3017", "branch_id": "A001",
                    "branch_name": "甲券商", "buy_volume": 1000 + day * 20,
                    "sell_volume": 100, "buy_price": 120 + day * 0.1,
                    "sell_price": 119.8 + day * 0.1, "groups": ("AI_SERVER",),
                    "stock_total_abs_net": 5000,
                },
                {
                    "date": date_value, "stock_id": "3017", "branch_id": "B002",
                    "branch_name": "乙券商", "buy_volume": 750 + day * 15,
                    "sell_volume": 80, "buy_price": 120.05 + day * 0.1,
                    "sell_price": 119.9 + day * 0.1, "groups": ("AI_SERVER",),
                    "stock_total_abs_net": 5000,
                },
                {
                    "date": date_value, "stock_id": "3017", "branch_id": "C003",
                    "branch_name": "丙券商", "buy_volume": 50,
                    "sell_volume": 900 + day * 11, "buy_price": 120.1 + day * 0.1,
                    "sell_price": 119.95 + day * 0.1, "groups": ("AI_SERVER",),
                    "stock_total_abs_net": 5000,
                },
            ])
        return rows

    def test_same_strategy_branches_form_circle(self):
        profiles, edges, circles = ENGINE.build_capital_circles(self.build_observations())
        self.assertEqual(set(profiles), {"A001", "B002", "C003"})
        self.assertTrue(any(set(members) == {"A001", "B002"} for members in circles.values()))
        self.assertFalse(any("C003" in members for members in circles.values()))
        matched_edge = next(
            edge for edge in edges if {edge["branch_a"], edge["branch_b"]} == {"A001", "B002"}
        )
        self.assertGreaterEqual(matched_edge["direction_match"], 0.99)
        self.assertGreaterEqual(matched_edge["score"], ENGINE.CIRCLE_EDGE_THRESHOLD)

    def test_institutional_alignment_is_probabilistic(self):
        circle_flow = {}
        institution_flow = {}
        for day in range(1, 16):
            key = (f"2026-08-{day:02d}", "3017")
            circle_flow[key] = 1000 + day * 10
            institution_flow[key] = {
                "investment_trust": 800 + day * 8,
                "dealer_self": -100,
                "dealer_hedging": 0,
                "foreign_investor": -200,
            }
        result = ENGINE.institutional_alignment(circle_flow, institution_flow)
        self.assertTrue(result["qualified"])
        self.assertEqual(result["best_category"], "investment_trust")
        self.assertIn("投信", result["style"])

    def test_sideways_accumulation_and_split_order_signals(self):
        signals = ENGINE.classify_daily_behavior({
            "net_1": 1000, "net_5": 5000, "net_20": 12000,
            "gross_1": 1400, "ret_1": 0.002, "ret_5": 0.01, "ret_20": 0.02,
            "price_position": 0.30, "volume_ratio": 0.90,
            "flow_concentration": 0.42, "buy_days_5": 5, "sell_days_5": 0,
            "active_members": 2, "circle_members": 2, "previous_net": 900,
            "amount_cv_5": 0.10, "close": 100, "previous_high_20": 105,
        })
        codes = {signal["behavior_code"] for signal in signals}
        self.assertIn("WH-002", codes)
        self.assertIn("WH-005", codes)
        self.assertIn("WH-006", codes)

    def test_daily_data_limitations_are_explicit(self):
        catalog = {code: status for code, _name, _state, status in ENGINE.BEHAVIOR_CATALOG}
        self.assertEqual(catalog["WH-018"], "not_identifiable_from_daily")
        self.assertEqual(catalog["WH-031"], "requires_futures_positions")
        self.assertEqual(catalog["WH-035"], "requires_event_calendar")

    def test_cross_circle_turnover_candidate(self):
        old_circle = {}
        new_circle = {}
        for day in range(1, 7):
            key = (f"2026-08-{day:02d}", "3017")
            old_circle[key] = {
                "net_volume": 800.0, "net_amount": 96000.0,
                "groups": ("AI_SERVER",),
            }
        final_key = ("2026-08-07", "3017")
        old_circle[final_key] = {
            "net_volume": -1200.0, "net_amount": -144000.0,
            "groups": ("AI_SERVER",),
        }
        new_circle[final_key] = {
            "net_volume": 1150.0, "net_amount": 138000.0,
            "groups": ("AI_SERVER",),
        }
        rows = ENGINE.build_cross_circle_behavior_rows(
            "2026-08-07",
            {"CC-OLD": old_circle, "CC-NEW": new_circle},
            {final_key: {"ret_1": 0.005, "volume_ratio": 1.8}},
        )
        codes = {row["behavior_code"] for row in rows}
        self.assertIn("WH-021", codes)
        self.assertIn("WH-022", codes)
        self.assertIn("WH-023", codes)


if __name__ == "__main__":
    unittest.main(verbosity=2)
