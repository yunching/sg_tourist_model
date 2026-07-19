from __future__ import annotations

import unittest

from sg_tourist_model.data import normalize_wide_series


class NormalizeWideSeriesTest(unittest.TestCase):
    def test_normalizes_selected_market_and_ignores_metadata(self) -> None:
        records = [
            {"_id": 1, "DataSeries": "    Japan", "2025Jan": "100", "2025Feb": "110"},
            {"_id": 2, "DataSeries": "    Canada", "2025Jan": "50", "2025Feb": "55"},
        ]
        result = normalize_wide_series(records, {"Japan"}, "arrivals")
        self.assertEqual(result["market"].unique().tolist(), ["Japan"])
        self.assertEqual(result["arrivals"].tolist(), [100.0, 110.0])
        self.assertEqual(result["month"].dt.strftime("%Y-%m").tolist(), ["2025-01", "2025-02"])


if __name__ == "__main__":
    unittest.main()
