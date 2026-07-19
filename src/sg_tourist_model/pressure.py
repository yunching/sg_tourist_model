from __future__ import annotations

import numpy as np
import pandas as pd


def pressure_forecast(
    market_forecast: pd.DataFrame,
    arrivals: pd.DataFrame,
    visitor_days: pd.DataFrame,
) -> pd.DataFrame:
    modeled_actual = arrivals.groupby("month", as_index=False)["arrivals"].sum().rename(columns={"arrivals": "modeled_arrivals"})
    joined = modeled_actual.merge(visitor_days, on="month", how="inner")
    joined = joined[joined["month"].dt.year >= 2023].copy()
    if joined.empty:
        raise ValueError("No recent overlap between arrivals and visitor-day data")

    # Visitor days per modeled-market arrival implicitly adjusts for unmodeled markets.
    ratio = float(np.median(joined["visitor_days"] / joined["modeled_arrivals"]))
    forecast = market_forecast.groupby("month", as_index=False)["prediction"].sum()
    forecast = forecast.rename(columns={"prediction": "modeled_market_arrivals"})
    forecast["estimated_total_visitor_days"] = forecast["modeled_market_arrivals"] * ratio
    forecast["days_in_month"] = forecast["month"].dt.days_in_month
    forecast["estimated_average_tourists_present"] = forecast["estimated_total_visitor_days"] / forecast["days_in_month"]

    baseline = visitor_days[visitor_days["month"].dt.year == 2019].copy()
    baseline["average_present"] = baseline["visitor_days"] / baseline["month"].dt.days_in_month
    baseline_mean = float(baseline["average_present"].mean())
    if not np.isfinite(baseline_mean) or baseline_mean <= 0:
        raise ValueError("Cannot calculate the 2019 pressure baseline")
    forecast["tourism_pressure_index"] = 100 * forecast["estimated_average_tourists_present"] / baseline_mean
    forecast["visitor_days_per_modeled_arrival"] = ratio
    return forecast
