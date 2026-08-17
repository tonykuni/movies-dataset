# -*- coding: utf-8 -*-
"""mathkit 單元測試（stdlib unittest；補 --selftest 未覆蓋的邊界）。"""
import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from engine import mathkit as mk  # noqa: E402


class TestRobustZ(unittest.TestCase):
    def test_symmetric_and_clip(self):
        sample = [0.01 * i for i in range(-40, 41)]
        self.assertEqual(mk.robust_z(99.0, sample), 3.0)
        self.assertEqual(mk.robust_z(-99.0, sample), -3.0)
        z = mk.robust_z(0.0, sample)
        self.assertAlmostEqual(z, 0.0, places=6)

    def test_short_sample_returns_none(self):
        self.assertIsNone(mk.robust_z(1.0, [1.0, 2.0, 3.0]))

    def test_zero_mad_falls_back_to_std(self):
        # 多數值相同 → MAD=0，需退回 std 而非除以零
        sample = [1.0] * 30 + [2.0, 0.0]
        self.assertIsNotNone(mk.robust_z(1.5, sample))

    def test_all_constant_returns_none(self):
        self.assertIsNone(mk.robust_z(5.0, [1.0] * 40))


class TestScales(unittest.TestCase):
    def test_fis_bounds(self):
        self.assertEqual(mk.fis_scale(0.0), 0.0)
        self.assertLess(abs(mk.fis_scale(3.0)), 100.0)
        self.assertGreater(mk.fis_scale(3.0), 90.0)
        self.assertIsNone(mk.fis_scale(None))


class TestSeries(unittest.TestCase):
    def test_window_return(self):
        prices = [100.0, 110.0, 121.0]
        self.assertAlmostEqual(mk.window_return(prices, 2), math.log(1.21))
        self.assertIsNone(mk.window_return(prices, 5))

    def test_drawdown(self):
        vals = [100, 120, 90, 96]
        self.assertAlmostEqual(mk.drawdown_from_high(vals, 4), 1 - 96 / 120)
        self.assertEqual(mk.drawdown_from_high([100, 100, 110], 3), 0.0)

    def test_series_change(self):
        self.assertAlmostEqual(mk.series_change([4.0, 4.2, 4.5], 2), 0.5)


class TestCorr(unittest.TestCase):
    def test_pearson_perfect(self):
        a = [float(i) for i in range(30)]
        b = [2 * x + 1 for x in a]
        self.assertAlmostEqual(mk.pearson(a, b), 1.0, places=9)

    def test_lead_lag_detects_shift(self):
        import random
        rng = random.Random(7)
        leader = [rng.gauss(0, 1) for _ in range(300)]
        follower = [0.0] * 5 + leader[:-5]  # leader 領先 5 日
        best = None
        for lag in (0, 1, 5, 10):
            c = mk.lead_lag_corr(leader, follower, lag, 200)
            if c is not None and (best is None or abs(c) > abs(best[1])):
                best = (lag, c)
        self.assertEqual(best[0], 5)
        self.assertGreater(best[1], 0.95)

    def test_pc1_identical_series_is_full_share(self):
        import random
        rng = random.Random(3)
        base = [rng.gauss(0, 1) for _ in range(80)]
        share = mk.pc1_variance_share([base[:], base[:], base[:]])
        self.assertGreater(share, 0.999)


if __name__ == "__main__":
    unittest.main()
