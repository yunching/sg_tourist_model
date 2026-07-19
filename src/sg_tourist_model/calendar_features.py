from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
import re

import pandas as pd

from .config import HOLIDAY_COUNTRY_CODES, HOLIDAY_SUBDIVISIONS, MARKETS


OPPORTUNITY_FEATURES = (
    "effective_holiday_days",
    "state_effective_holiday_days",
    "long_weekend_count",
    "max_time_off_block",
    "holiday_departure_lead",
    "holiday_return_lag",
    "school_holiday_overlap_weight",
)

_ISO_DATE = re.compile(r"(20\d{2})-(\d{2})-(\d{2})")


def public_holiday_dates(start_year: int, end_year: int) -> pd.DataFrame:
    try:
        import holidays
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("Install project dependencies to generate holiday features") from exc

    rows: list[dict] = []
    years = range(start_year, end_year + 1)
    for market in MARKETS:
        code = HOLIDAY_COUNTRY_CODES[market]
        national = holidays.country_holidays(code, years=years, observed=True)
        for day, name in sorted(national.items()):
            rows.append({"market": market, "date": pd.Timestamp(day), "name": str(name),
                         "weight": 1.0, "kind": "public_holiday", "region": None})

        for region, subdivision in HOLIDAY_SUBDIVISIONS.get(market, {}).items():
            regional = holidays.country_holidays(code, subdiv=subdivision, years=years, observed=True)
            for day, name in sorted(regional.items()):
                if day in national:
                    continue
                rows.append({"market": market, "date": pd.Timestamp(day), "name": str(name),
                             "weight": 1.0, "kind": "state_holiday", "region": region})
    return pd.DataFrame(rows)


def load_manual_windows(path: Path) -> pd.DataFrame:
    columns = ["market", "date", "name", "weight", "kind", "region"]
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame(columns=columns)
    windows = pd.read_csv(path)
    if windows.empty:
        return pd.DataFrame(columns=columns)
    required = {"market", "start_date", "end_date", "name", "kind", "weight"}
    missing = required - set(windows.columns)
    if missing:
        raise ValueError(f"Manual travel windows are missing columns: {sorted(missing)}")
    unknown = set(windows["market"].dropna()) - set(MARKETS)
    if unknown:
        raise ValueError(f"Unknown markets in manual travel windows: {sorted(unknown)}")

    rows: list[dict] = []
    for row in windows.itertuples(index=False):
        start = pd.Timestamp(row.start_date)
        end = pd.Timestamp(row.end_date)
        if end < start:
            raise ValueError(f"Travel window ends before it starts: {row.name}")
        for day in pd.date_range(start, end, freq="D"):
            rows.append({"market": row.market, "date": day, "name": row.name,
                         "weight": float(row.weight), "kind": row.kind, "region": None})
    return pd.DataFrame(rows, columns=columns)


def _max_consecutive_days(days: Iterable[pd.Timestamp]) -> int:
    unique_days = sorted(set(pd.Timestamp(day).normalize() for day in days))
    if not unique_days:
        return 0
    longest = current = 1
    for previous, current_day in zip(unique_days, unique_days[1:]):
        if (current_day - previous).days == 1:
            current += 1
            longest = max(longest, current)
        else:
            current = 1
    return longest



def _is_weekend(market: str, day: pd.Timestamp) -> bool:
    """Return the locally relevant weekend for travel-opportunity blocks.

    Johor observed Friday-Saturday weekends from 2014 through 2024 and
    returned to Saturday-Sunday from 1 January 2025.
    """
    normalized = pd.Timestamp(day).normalize()
    if market == "Malaysia" and pd.Timestamp("2014-01-01") <= normalized < pd.Timestamp("2025-01-01"):
        return normalized.dayofweek in {4, 5}
    return normalized.dayofweek in {5, 6}


def _working_day_overrides(public: pd.DataFrame, manual: pd.DataFrame) -> dict[str, set[pd.Timestamp]]:
    """Collect weekend dates that are explicitly designated as working days."""
    overrides = {market: set() for market in MARKETS}
    if not manual.empty and "kind" in manual:
        for row in manual[manual["kind"].eq("working_day")].itertuples(index=False):
            overrides[row.market].add(pd.Timestamp(row.date).normalize())

    # China swaps selected weekend days into the working week. python-holidays
    # records the corresponding rest day and embeds the worked date in its name.
    if not public.empty:
        china = public[public["market"].eq("China")]
        for row in china.itertuples(index=False):
            name = str(row.name)
            if "\u8c03\u4f11" not in name:
                continue
            for year, month, day in _ISO_DATE.findall(name):
                candidate = pd.Timestamp(year=int(year), month=int(month), day=int(day))
                if candidate != pd.Timestamp(row.date).normalize():
                    overrides["China"].add(candidate)
    return overrides


def _travel_opportunity_features(
    public: pd.DataFrame,
    manual: pd.DataFrame,
    start_month: pd.Timestamp,
    end_month: pd.Timestamp,
) -> pd.DataFrame:
    """Convert holiday dates into monthly opportunities for outbound travel.

    Public holidays are joined to adjacent local weekend days. Lead and return
    weights sit on neighboring dates so month-end breaks can affect both months.
    School overlap remains a separate family-travel signal.
    """
    first_day = pd.Timestamp(start_month).normalize()
    last_day = pd.Timestamp(end_month).normalize() + pd.offsets.MonthEnd(1)
    padded_days = pd.date_range(
        first_day - pd.Timedelta(days=14),
        last_day + pd.Timedelta(days=14),
        freq="D",
    )
    working_overrides = _working_day_overrides(public, manual)
    rows: list[dict] = []

    for market in MARKETS:
        market_public = public[public["market"].eq(market)] if not public.empty else public
        public_dates = market_public.get("date", pd.Series(dtype="datetime64[ns]"))
        holiday_dates = set(pd.to_datetime(public_dates.dropna()).dt.normalize())
        state_mask = market_public.get(
            "kind", pd.Series(index=market_public.index, dtype=str)
        ).eq("state_holiday")
        state_dates = (
            set(pd.to_datetime(market_public.loc[state_mask, "date"]).dt.normalize())
            if not market_public.empty else set()
        )

        market_manual = manual[manual["market"].eq(market)] if not manual.empty else manual
        school_mask = market_manual.get(
            "kind", pd.Series(index=market_manual.index, dtype=str)
        ).eq("school_break")
        school = market_manual[school_mask]
        school_weight = school.groupby("date")["weight"].max().to_dict() if not school.empty else {}

        off_days = {
            day for day in padded_days
            if day in holiday_dates
            or (_is_weekend(market, day) and day not in working_overrides[market])
        }
        blocks: list[list[pd.Timestamp]] = []
        current: list[pd.Timestamp] = []
        for day in padded_days:
            if day in off_days:
                if current and (day - current[-1]).days > 1:
                    blocks.append(current)
                    current = []
                current.append(day)
            elif current:
                blocks.append(current)
                current = []
        if current:
            blocks.append(current)

        daily = pd.DataFrame({"date": padded_days})
        for feature in OPPORTUNITY_FEATURES:
            daily[feature] = 0.0

        for block in blocks:
            block_holidays = sorted(set(block).intersection(holiday_dates))
            if not block_holidays:
                continue
            duration = len(block)
            block_mask = daily["date"].isin(block)
            daily.loc[block_mask, "effective_holiday_days"] = 1.0
            if set(block).intersection(state_dates):
                daily.loc[block_mask, "state_effective_holiday_days"] = 1.0
            for period in daily.loc[block_mask, "date"].dt.to_period("M").unique():
                month_mask = daily["date"].dt.to_period("M").eq(period)
                daily.loc[month_mask, "max_time_off_block"] = daily.loc[
                    month_mask, "max_time_off_block"
                ].clip(lower=duration)
            if duration >= 3:
                daily.loc[
                    daily["date"].eq(block_holidays[0]), "long_weekend_count"
                ] += 1.0
            daily.loc[
                daily["date"].eq(block[0] - pd.Timedelta(days=1)),
                "holiday_departure_lead",
            ] += 0.5
            daily.loc[
                daily["date"].eq(block[-1] + pd.Timedelta(days=1)),
                "holiday_return_lag",
            ] += 0.25

        daily["school_holiday_overlap_weight"] = daily.apply(
            lambda row: float(school_weight.get(row["date"], 0.0))
            * row["effective_holiday_days"],
            axis=1,
        )
        daily = daily[daily["date"].between(first_day, last_day)].copy()
        daily["market"] = market
        daily["month"] = daily["date"].dt.to_period("M").dt.to_timestamp()
        monthly = daily.groupby(["market", "month"], as_index=False).agg(
            effective_holiday_days=("effective_holiday_days", "sum"),
            state_effective_holiday_days=("state_effective_holiday_days", "sum"),
            long_weekend_count=("long_weekend_count", "sum"),
            max_time_off_block=("max_time_off_block", "max"),
            holiday_departure_lead=("holiday_departure_lead", "sum"),
            holiday_return_lag=("holiday_return_lag", "sum"),
            school_holiday_overlap_weight=("school_holiday_overlap_weight", "sum"),
        )
        rows.extend(monthly.to_dict("records"))
    return pd.DataFrame(rows)


def _monthly_holidays(frame: pd.DataFrame, prefix: str = "") -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=["market", "month", f"{prefix}holiday_days",
                                     f"{prefix}holiday_weekend_days", f"{prefix}max_consecutive_holidays"])
    copy = frame.copy()
    copy["month"] = copy["date"].dt.to_period("M").dt.to_timestamp()
    copy["is_weekend"] = copy["date"].dt.dayofweek >= 5
    return copy.groupby(["market", "month"], as_index=False).agg(**{
        f"{prefix}holiday_days": ("date", "nunique"),
        f"{prefix}holiday_weekend_days": ("is_weekend", "sum"),
        f"{prefix}max_consecutive_holidays": ("date", _max_consecutive_days),
    })


def aggregate_holiday_features(public_days: pd.DataFrame, manual_days: pd.DataFrame,
                               start_month: pd.Timestamp, end_month: pd.Timestamp) -> pd.DataFrame:
    public, manual = public_days.copy(), manual_days.copy()
    for frame in (public, manual):
        if not frame.empty:
            frame["date"] = pd.to_datetime(frame["date"]).dt.normalize()

    months = pd.date_range(start_month, end_month, freq="MS")
    grid = pd.MultiIndex.from_product([MARKETS, months], names=["market", "month"]).to_frame(index=False)
    public_monthly = _monthly_holidays(public)
    state = public[public.get("kind", pd.Series(index=public.index, dtype=str)).eq("state_holiday")]
    state_monthly = _monthly_holidays(state, prefix="state_")

    manual["month"] = manual["date"].dt.to_period("M").dt.to_timestamp() if not manual.empty else pd.Series(dtype="datetime64[ns]")
    kinds = manual.get("kind", pd.Series(index=manual.index, dtype=str))
    school = manual[kinds.eq("school_break")]
    international_school = manual[kinds.eq("international_school_break")]
    working_days = manual[kinds.eq("working_day")]
    excluded = school.index.union(international_school.index).union(working_days.index)
    other_windows = manual[~manual.index.isin(excluded)]
    school_monthly = (
        school.groupby(["market", "month"], as_index=False)
        .agg(school_break_days=("date", "nunique"), school_break_weight=("weight", "sum"))
        if not school.empty else pd.DataFrame(columns=["market", "month", "school_break_days", "school_break_weight"])
    )
    international_school_monthly = (
        international_school.groupby(["market", "month"], as_index=False)
        .agg(international_school_break_days=("date", "nunique"), international_school_break_weight=("weight", "sum"))
        if not international_school.empty else pd.DataFrame(columns=["market", "month", "international_school_break_days", "international_school_break_weight"])
    )
    manual_monthly = (
        other_windows.groupby(["market", "month"], as_index=False)
        .agg(travel_window_days=("date", "nunique"), travel_window_weight=("weight", "sum"))
        if not other_windows.empty else pd.DataFrame(columns=["market", "month", "travel_window_days", "travel_window_weight"])
    )

    features = grid.merge(public_monthly, on=["market", "month"], how="left")
    features = features.merge(state_monthly, on=["market", "month"], how="left")
    features = features.merge(school_monthly, on=["market", "month"], how="left")
    features = features.merge(international_school_monthly, on=["market", "month"], how="left")
    features = features.merge(manual_monthly, on=["market", "month"], how="left")
    opportunity = _travel_opportunity_features(public, manual, start_month, end_month)
    features = features.merge(opportunity, on=["market", "month"], how="left")
    numeric = [column for column in features.columns if column not in {"market", "month"}]
    features[numeric] = features[numeric].fillna(0.0)
    return features
