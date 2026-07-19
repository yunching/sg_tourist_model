from __future__ import annotations

from dataclasses import dataclass
import pandas as pd

from .config import MARKETS


@dataclass(frozen=True)
class InternationalSchoolRule:
    curriculum: str
    start_month: int
    start_day: int
    end_month: int
    end_day: int
    name: str
    weight: float
    source_url: str


INTERNATIONAL_SCHOOL_RULES: tuple[InternationalSchoolRule, ...] = (
    InternationalSchoolRule("US curriculum", 6, 5, 8, 11, "Summer break", .20, "https://www.sas.edu.sg/calendars"),
    InternationalSchoolRule("US curriculum", 10, 19, 10, 23, "Fall break", .20, "https://www.sas.edu.sg/calendars"),
    InternationalSchoolRule("US curriculum", 12, 21, 1, 8, "Winter break", .20, "https://www.sas.edu.sg/calendars"),
    InternationalSchoolRule("US curriculum", 3, 22, 3, 26, "Spring break", .20, "https://www.sas.edu.sg/calendars"),
    InternationalSchoolRule("UK curriculum", 7, 1, 8, 17, "Summer break", .20, "https://www.tts.edu.sg/school-life/term-dates"),
    InternationalSchoolRule("UK curriculum", 10, 12, 10, 23, "October half-term", .20, "https://www.tts.edu.sg/school-life/term-dates"),
    InternationalSchoolRule("UK curriculum", 12, 19, 1, 10, "Year-end break", .20, "https://www.tts.edu.sg/school-life/term-dates"),
    InternationalSchoolRule("UK curriculum", 2, 13, 2, 21, "Spring half-term", .20, "https://www.tts.edu.sg/school-life/term-dates"),
    InternationalSchoolRule("AU curriculum", 12, 11, 1, 18, "Summer break", .20, "https://www.ais.com.sg/school-life/calendar-dates/"),
    InternationalSchoolRule("AU curriculum", 3, 30, 4, 10, "Term 1 break", .20, "https://www.ais.com.sg/school-life/calendar-dates/"),
    InternationalSchoolRule("AU curriculum", 6, 22, 7, 17, "Mid-year break", .20, "https://www.ais.com.sg/school-life/calendar-dates/"),
    InternationalSchoolRule("AU curriculum", 9, 21, 10, 2, "Term 3 break", .20, "https://www.ais.com.sg/school-life/calendar-dates/"),
)


def international_school_break_dates(start_year: int, end_year: int) -> pd.DataFrame:
    rows: list[dict] = []
    for year in range(start_year - 1, end_year + 1):
        for rule in INTERNATIONAL_SCHOOL_RULES:
            start = pd.Timestamp(year=year, month=rule.start_month, day=rule.start_day)
            end = pd.Timestamp(year=year + (rule.end_month < rule.start_month), month=rule.end_month, day=rule.end_day)
            for day in pd.date_range(start, end, freq="D"):
                if not start_year <= day.year <= end_year:
                    continue
                for market in MARKETS:
                    rows.append({
                        "market": market, "date": day, "name": rule.name,
                        "weight": rule.weight, "kind": "international_school_break",
                        "region": rule.curriculum, "source_url": rule.source_url,
                    })
    return pd.DataFrame(rows).drop_duplicates(["market", "date", "name", "region"])
