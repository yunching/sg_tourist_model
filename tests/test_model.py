from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from sg_tourist_model.features import build_panel
from sg_tourist_model.model import RidgeArrivalModel


class RidgeModelTest(unittest.TestCase):
    def test_fit_predict_returns_nonnegative_values(self) -> None:
        months = pd.date_range("2010-01-01", periods=48, freq="MS")
        arrivals = pd.DataFrame(
            {
                "market": ["Japan"] * len(months),
                "month": months,
                "arrivals": 100_000 + 20_000 * np.sin(2 * np.pi * months.month / 12),
            }
        )
        holidays = pd.DataFrame(
            {
                "market": ["Japan"] * len(months),
                "month": months,
                "holiday_days": 1,
                "holiday_weekend_days": 0,
                "max_consecutive_holidays": 1,
                "travel_window_days": 0,
                "travel_window_weight": 0.0,
            }
        )
        panel = build_panel(arrivals, holidays)
        model = RidgeArrivalModel().fit(panel)
        predictions = model.predict(panel.dropna(subset=["lag_12"]))
        self.assertTrue(np.all(np.isfinite(predictions)))
        self.assertTrue(np.all(predictions >= 0))


if __name__ == "__main__":
    unittest.main()
