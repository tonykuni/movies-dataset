from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from engine.via_time_utils import def_available_at_utc, def_local_calendar_date


class TimeUtilityMissingScalarTests(unittest.TestCase):
    def test_scalar_missing_values_return_nat(self) -> None:
        values = (None, pd.NaT, pd.NA, float("nan"), np.datetime64("NaT"))
        for value in values:
            with self.subTest(value=repr(value), function="available"):
                self.assertTrue(pd.isna(def_available_at_utc(value)))
            with self.subTest(value=repr(value), function="local_date"):
                self.assertTrue(pd.isna(def_local_calendar_date(value)))

    def test_non_scalar_does_not_enter_ambiguous_missing_truth_path(self) -> None:
        with self.assertRaises((TypeError, ValueError)) as error:
            def_local_calendar_date(np.array(["2026-01-02", "2026-01-05"]))
        self.assertNotIn("truth value of an array", str(error.exception))


if __name__ == "__main__":
    unittest.main()
