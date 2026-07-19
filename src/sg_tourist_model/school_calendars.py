from __future__ import annotations

from dataclasses import dataclass
import pandas as pd

from .config import MARKETS


@dataclass(frozen=True)
class SchoolBreakRule:
    start_month: int
    start_day: int
    end_month: int
    end_day: int
    name: str
    scope: str
    weight: float
    source_url: str


SCHOOL_BREAK_RULES: dict[str, tuple[SchoolBreakRule, ...]] = {
    "China": (
        SchoolBreakRule(1, 24, 3, 1, "Winter school break", "Beijing proxy", .75, "https://jw.beijing.gov.cn/xxgk/2024zcwj/2024qtwj/202507/t20250704_4141331.html"),
        SchoolBreakRule(7, 8, 8, 31, "Summer school break", "Beijing proxy", .75, "https://jw.beijing.gov.cn/xxgk/2024zcwj/2024qtwj/202507/t20250704_4141331.html"),
    ),
    "Indonesia": (
        SchoolBreakRule(6, 27, 7, 11, "Semester 2 break", "Jakarta proxy", .75, "https://edu.jakarta.go.id/cdn/files/photos/cms/kalender20252026.pdf"),
        SchoolBreakRule(12, 20, 1, 3, "Semester 1 break", "Jakarta proxy", .75, "https://edu.jakarta.go.id/cdn/files/photos/cms/kalender20252026.pdf"),
    ),
    "Malaysia": (
        SchoolBreakRule(5, 29, 6, 9, "Term 1 break", "Johor / KPM Group B", 1.0, "https://www.moe.gov.my/storage/files/shares/Takwim/Takwim%20Persekolahan/Kalendar%20Akademik%202025_2026%20%28Pindaan%29.pdf"),
        SchoolBreakRule(9, 13, 9, 21, "Term 2 break", "Johor / KPM Group B", 1.0, "https://www.moe.gov.my/storage/files/shares/Takwim/Takwim%20Persekolahan/Kalendar%20Akademik%202025_2026%20%28Pindaan%29.pdf"),
        SchoolBreakRule(12, 20, 1, 11, "Year-end school break", "Johor / KPM Group B", 1.0, "https://www.moe.gov.my/storage/files/shares/Takwim/Takwim%20Persekolahan/Kalendar%20Akademik%202025_2026%20%28Pindaan%29.pdf"),
    ),
    "Australia": (
        SchoolBreakRule(12, 22, 1, 26, "Summer school break", "NSW Eastern Division proxy", .75, "https://education.nsw.gov.au/schooling/calendars/2026"),
        SchoolBreakRule(4, 7, 4, 17, "Autumn school break", "NSW Eastern Division proxy", .75, "https://education.nsw.gov.au/schooling/calendars/2026"),
        SchoolBreakRule(7, 6, 7, 17, "Winter school break", "NSW Eastern Division proxy", .75, "https://education.nsw.gov.au/schooling/calendars/2026"),
        SchoolBreakRule(9, 28, 10, 9, "Spring school break", "NSW Eastern Division proxy", .75, "https://education.nsw.gov.au/schooling/calendars/2026"),
    ),
    "India": (
        SchoolBreakRule(1, 1, 1, 15, "Winter school break", "Delhi proxy", .65, "https://www.edudel.nic.in/upload/upload_2023_24/1010_dt_04122024.pdf"),
        SchoolBreakRule(5, 11, 6, 30, "Summer school break", "Delhi proxy", .65, "https://www.edudel.nic.in/upload/upload_2023_24/1010_dt_04122024.pdf"),
        SchoolBreakRule(9, 29, 10, 1, "Autumn school break", "Delhi proxy", .65, "https://www.edudel.nic.in/upload/upload_2023_24/1010_dt_04122024.pdf"),
    ),
    "Japan": (
        SchoolBreakRule(12, 26, 1, 7, "Winter school break", "Tokyo metropolitan proxy", .65, "https://www.kyoiku.metro.tokyo.lg.jp/"),
        SchoolBreakRule(3, 26, 4, 5, "Spring school break", "Tokyo metropolitan proxy", .65, "https://www.kyoiku.metro.tokyo.lg.jp/"),
        SchoolBreakRule(7, 21, 8, 31, "Summer school break", "Tokyo metropolitan proxy", .65, "https://www.kyoiku.metro.tokyo.lg.jp/"),
    ),
    "South Korea": (
        SchoolBreakRule(1, 1, 2, 28, "Winter school break", "Seoul proxy", .60, "https://www.sen.go.kr/"),
        SchoolBreakRule(7, 20, 8, 16, "Summer school break", "Seoul proxy", .60, "https://www.sen.go.kr/"),
    ),
    "Philippines": (
        SchoolBreakRule(4, 1, 6, 1, "Year-end school break", "DepEd public-school proxy", .85, "https://www.deped.gov.ph/2026/05/04/deped-binigyang-diin-ang-istruktura-at-layunin-ng-three-term-school-calendar-bago-ang-implementasyon/"),
        SchoolBreakRule(12, 20, 1, 4, "Christmas school break", "DepEd public-school proxy", .85, "https://www.deped.gov.ph/"),
    ),
    "United Kingdom": (
        SchoolBreakRule(12, 20, 1, 4, "Christmas school break", "Somerset / England proxy", .60, "https://www.somerset.gov.uk/children-families-and-education/school-life/school-term-dates-and-holidays/"),
        SchoolBreakRule(2, 14, 2, 22, "Spring half-term", "Somerset / England proxy", .60, "https://www.somerset.gov.uk/children-families-and-education/school-life/school-term-dates-and-holidays/"),
        SchoolBreakRule(4, 3, 4, 19, "Easter school break", "Somerset / England proxy", .60, "https://www.somerset.gov.uk/children-families-and-education/school-life/school-term-dates-and-holidays/"),
        SchoolBreakRule(5, 23, 5, 31, "Summer half-term", "Somerset / England proxy", .60, "https://www.somerset.gov.uk/children-families-and-education/school-life/school-term-dates-and-holidays/"),
        SchoolBreakRule(7, 23, 9, 2, "Summer school break", "Somerset / England proxy", .60, "https://www.somerset.gov.uk/children-families-and-education/school-life/school-term-dates-and-holidays/"),
        SchoolBreakRule(10, 25, 11, 2, "Autumn half-term", "Somerset / England proxy", .60, "https://www.somerset.gov.uk/children-families-and-education/school-life/school-term-dates-and-holidays/"),
    ),
    "USA": (
        SchoolBreakRule(12, 24, 1, 2, "Winter recess", "New York City proxy", .60, "https://www.schools.nyc.gov/calendar/2025-2026-school-year-calendar"),
        SchoolBreakRule(2, 16, 2, 20, "Midwinter recess", "New York City proxy", .60, "https://www.schools.nyc.gov/calendar/2025-2026-school-year-calendar"),
        SchoolBreakRule(4, 2, 4, 10, "Spring recess", "New York City proxy", .60, "https://www.schools.nyc.gov/calendar/2025-2026-school-year-calendar"),
        SchoolBreakRule(6, 27, 9, 7, "Summer recess", "New York City proxy", .60, "https://www.schools.nyc.gov/calendar/2025-2026-school-year-calendar"),
    ),
}


# Exact, year-specific calendars take precedence over recurring proxy rules.
# Johor is in Malaysia KPM Group B from 2025 onward.
SCHOOL_BREAK_OVERRIDES: dict[str, dict[int, tuple[SchoolBreakRule, ...]]] = {
    "Malaysia": {
        2026: (
            SchoolBreakRule(2, 16, 2, 20, "Chinese New Year school break", "Johor / KPM Group B", 1.0, "https://www.moe.gov.my/storage/files/shares/Takwim/Takwim%20Persekolahan/Kalendar%20Akademik%202026.pdf"),
            SchoolBreakRule(3, 19, 3, 29, "Term 1 and Aidilfitri break", "Johor / KPM Group B", 1.0, "https://www.moe.gov.my/storage/files/shares/Takwim/Takwim%20Persekolahan/Kalendar%20Akademik%202026.pdf"),
            SchoolBreakRule(5, 23, 6, 7, "Mid-year school break", "Johor / KPM Group B", 1.0, "https://www.moe.gov.my/storage/files/shares/Takwim/Takwim%20Persekolahan/Kalendar%20Akademik%202026.pdf"),
            SchoolBreakRule(8, 29, 9, 6, "Term 2 break", "Johor / KPM Group B", 1.0, "https://www.moe.gov.my/storage/files/shares/Takwim/Takwim%20Persekolahan/Kalendar%20Akademik%202026.pdf"),
            SchoolBreakRule(11, 8, 11, 10, "Deepavali school extension", "Johor / KPM Group B", 1.0, "https://www.moe.gov.my/storage/files/shares/Takwim/Takwim%20Persekolahan/Kalendar%20Akademik%202026.pdf"),
            SchoolBreakRule(12, 5, 12, 31, "Year-end school break", "Johor / KPM Group B", 1.0, "https://www.moe.gov.my/storage/files/shares/Takwim/Takwim%20Persekolahan/Kalendar%20Akademik%202026.pdf"),
        ),
    },
}


def school_break_dates(start_year: int, end_year: int) -> pd.DataFrame:
    rows: list[dict] = []
    for market in MARKETS:
        for year in range(start_year - 1, end_year + 1):
            rules = SCHOOL_BREAK_OVERRIDES.get(market, {}).get(year, SCHOOL_BREAK_RULES[market])
            for rule in rules:
                start = pd.Timestamp(year=year, month=rule.start_month, day=rule.start_day)
                end_year_for_rule = year + (rule.end_month < rule.start_month)
                end = pd.Timestamp(year=end_year_for_rule, month=rule.end_month, day=rule.end_day)
                for day in pd.date_range(start, end, freq="D"):
                    if start_year <= day.year <= end_year:
                        rows.append({
                            "market": market, "date": day, "name": rule.name,
                            "weight": rule.weight, "kind": "school_break",
                            "region": rule.scope, "source_url": rule.source_url,
                        })
    return pd.DataFrame(rows).drop_duplicates(["market", "date", "name"])
