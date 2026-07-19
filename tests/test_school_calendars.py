from __future__ import annotations

import unittest

import pandas as pd

from sg_tourist_model.config import MARKETS
from sg_tourist_model.school_calendars import SCHOOL_BREAK_RULES, school_break_dates


class SchoolCalendarsTest(unittest.TestCase):
    def test_every_market_has_a_sourced_profile(self) -> None:
        self.assertEqual(set(SCHOOL_BREAK_RULES), set(MARKETS))
        for rules in SCHOOL_BREAK_RULES.values():
            self.assertTrue(rules)
            self.assertTrue(all(rule.source_url.startswith("https://") for rule in rules))

    def test_china_summer_and_cross_year_breaks_expand(self) -> None:
        days = school_break_dates(2026, 2026)
        china = days[days["market"] == "China"]
        self.assertTrue(((china["date"].dt.month == 7) & (china["name"] == "Summer school break")).any())
        indonesia = days[(days["market"] == "Indonesia") & (days["name"] == "Semester 1 break")]
        self.assertTrue((indonesia["date"].dt.month == 1).any())
        self.assertTrue((indonesia["date"].dt.month == 12).any())


    def test_johor_uses_exact_2026_group_b_calendar(self) -> None:
        days = school_break_dates(2026, 2026)
        malaysia = days[days["market"].eq("Malaysia")]
        term_two = malaysia[malaysia["name"].eq("Term 2 break")]
        self.assertEqual(term_two["date"].min(), pd.Timestamp("2026-08-29"))
        self.assertEqual(term_two["date"].max(), pd.Timestamp("2026-09-06"))
        self.assertTrue(
            ((malaysia["name"].eq("Deepavali school extension"))
             & (malaysia["date"].eq(pd.Timestamp("2026-11-10")))).any()
        )



if __name__ == "__main__":
    unittest.main()
