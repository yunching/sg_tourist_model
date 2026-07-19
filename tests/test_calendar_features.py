from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from sg_tourist_model.calendar_features import _is_weekend, aggregate_holiday_features, load_manual_windows


class CalendarFeaturesTest(unittest.TestCase):
    def test_expands_manual_window(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "windows.csv"
            path.write_text(
                "market,start_date,end_date,name,kind,weight,source_url\n"
                "Japan,2025-08-13,2025-08-16,Obon,customary_break,1.0,https://example.test\n",
                encoding="utf-8",
            )
            result = load_manual_windows(path)
        self.assertEqual(len(result), 4)
        self.assertEqual(result["weight"].sum(), 4.0)

    def test_aggregates_public_and_manual_days(self) -> None:
        public = pd.DataFrame({
            "market": ["Japan", "Japan"],
            "date": pd.to_datetime(["2025-05-03", "2025-05-04"]),
            "name": ["A", "B"], "weight": [1.0, 1.0],
            "kind": ["public_holiday", "public_holiday"],
        })
        manual = pd.DataFrame({
            "market": ["Japan"], "date": pd.to_datetime(["2025-05-05"]),
            "name": ["C"], "weight": [0.5], "kind": ["school_break"],
        })
        result = aggregate_holiday_features(public, manual, pd.Timestamp("2025-05-01"), pd.Timestamp("2025-05-01"))
        japan = result[result["market"] == "Japan"].iloc[0]
        self.assertEqual(japan["holiday_days"], 2)
        self.assertEqual(japan["max_consecutive_holidays"], 2)
        self.assertEqual(japan["school_break_days"], 1)
        self.assertEqual(japan["school_break_weight"], 0.5)

    def test_johor_state_holidays_are_separate_features(self) -> None:
        public = pd.DataFrame({
            "market": ["Malaysia", "Malaysia"],
            "date": pd.to_datetime(["2026-03-23", "2026-03-24"]),
            "name": ["Sultan of Johor's Birthday", "Federal holiday"],
            "weight": [1.0, 1.0],
            "kind": ["state_holiday", "public_holiday"],
            "region": ["Johor", None],
        })
        manual = pd.DataFrame(columns=["market", "date", "name", "weight", "kind", "region"])
        result = aggregate_holiday_features(public, manual, pd.Timestamp("2026-03-01"), pd.Timestamp("2026-03-01"))
        malaysia = result[result["market"] == "Malaysia"].iloc[0]
        self.assertEqual(malaysia["holiday_days"], 2)
        self.assertEqual(malaysia["state_holiday_days"], 1)
        self.assertEqual(malaysia["state_max_consecutive_holidays"], 1)
        other = result[result["market"] == "Japan"].iloc[0]
        self.assertEqual(other["state_holiday_days"], 0)


    def test_holiday_block_includes_adjacent_weekend_and_spills_month(self) -> None:
        public = pd.DataFrame({
            "market": ["Japan"], "date": pd.to_datetime(["2025-01-31"]),
            "name": ["Holiday"], "weight": [1.0],
            "kind": ["public_holiday"], "region": [None],
        })
        manual = pd.DataFrame(columns=["market", "date", "name", "weight", "kind", "region"])
        result = aggregate_holiday_features(
            public, manual, pd.Timestamp("2025-01-01"), pd.Timestamp("2025-02-01")
        )
        japan = result[result["market"].eq("Japan")].set_index("month")
        self.assertEqual(japan.loc[pd.Timestamp("2025-01-01"), "effective_holiday_days"], 1)
        self.assertEqual(japan.loc[pd.Timestamp("2025-02-01"), "effective_holiday_days"], 2)
        self.assertEqual(japan.loc[pd.Timestamp("2025-01-01"), "long_weekend_count"], 1)
        self.assertEqual(japan.loc[pd.Timestamp("2025-02-01"), "holiday_return_lag"], 0.25)

    def test_school_overlap_is_weighted(self) -> None:
        public = pd.DataFrame({
            "market": ["Japan"], "date": pd.to_datetime(["2025-05-05"]),
            "name": ["Holiday"], "weight": [1.0],
            "kind": ["public_holiday"], "region": [None],
        })
        manual = pd.DataFrame({
            "market": ["Japan"], "date": pd.to_datetime(["2025-05-05"]),
            "name": ["School break"], "weight": [0.6],
            "kind": ["school_break"], "region": ["Tokyo"],
        })
        result = aggregate_holiday_features(
            public, manual, pd.Timestamp("2025-05-01"), pd.Timestamp("2025-05-01")
        )
        japan = result[result["market"].eq("Japan")].iloc[0]
        self.assertAlmostEqual(japan["school_holiday_overlap_weight"], 0.6)

    def test_johor_weekend_change_is_respected(self) -> None:
        self.assertTrue(_is_weekend("Malaysia", pd.Timestamp("2024-12-27")))
        self.assertFalse(_is_weekend("Malaysia", pd.Timestamp("2024-12-29")))
        self.assertFalse(_is_weekend("Malaysia", pd.Timestamp("2025-01-03")))
        self.assertTrue(_is_weekend("Malaysia", pd.Timestamp("2025-01-05")))


if __name__ == "__main__":
    unittest.main()
