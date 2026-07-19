from __future__ import annotations

import unittest

from sg_tourist_model.config import MARKETS
from sg_tourist_model.international_school_calendars import (
    INTERNATIONAL_SCHOOL_RULES,
    international_school_break_dates,
)


class InternationalSchoolCalendarsTest(unittest.TestCase):
    def test_three_curricula_are_sourced_and_cover_all_markets(self) -> None:
        self.assertEqual({rule.curriculum for rule in INTERNATIONAL_SCHOOL_RULES},
                         {"US curriculum", "UK curriculum", "AU curriculum"})
        self.assertTrue(all(rule.source_url.startswith("https://") for rule in INTERNATIONAL_SCHOOL_RULES))
        days = international_school_break_dates(2026, 2026)
        self.assertEqual(set(days["market"]), set(MARKETS))

    def test_curriculum_breaks_have_lower_segment_weights(self) -> None:
        days = international_school_break_dates(2026, 2026)
        self.assertGreater(len(days), 0)
        self.assertTrue(days["weight"].between(0, .25).all())


if __name__ == "__main__":
    unittest.main()
