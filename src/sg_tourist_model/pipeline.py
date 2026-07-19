from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from .calendar_features import aggregate_holiday_features, load_manual_windows, public_holiday_dates
from .config import Paths, project_root
from .data import load_arrivals, load_visitor_days
from .features import build_panel
from .model import evaluate_holdout, recursive_forecast
from .pressure import pressure_forecast
from .school_calendars import school_break_dates
from .international_school_calendars import international_school_break_dates


def run_pipeline(
    root: Path | None = None,
    refresh: bool = True,
    forecast_months: int = 12,
    holdout_months: int = 12,
) -> dict:
    paths = Paths(root or project_root())
    paths.create()
    arrivals = load_arrivals(paths.raw / "arrivals.csv", refresh=refresh)
    visitor_days = load_visitor_days(paths.raw / "visitor_days.csv", refresh=refresh)

    latest = max(arrivals["month"].max(), visitor_days["month"].max())
    start_month = arrivals["month"].min()
    end_month = latest + pd.offsets.MonthBegin(forecast_months)
    public_days = public_holiday_dates(start_month.year, end_month.year)
    manual_days = load_manual_windows(paths.manual / "travel_windows.csv")
    school_days = school_break_dates(start_month.year, end_month.year)
    international_school_days = international_school_break_dates(start_month.year, end_month.year)
    manual_days = pd.concat([manual_days, school_days, international_school_days], ignore_index=True)
    holiday_features = aggregate_holiday_features(public_days, manual_days, start_month, end_month)
    holiday_features.to_csv(paths.processed / "holiday_features.csv", index=False)

    panel = build_panel(arrivals, holiday_features)
    panel.to_csv(paths.processed / "model_panel.csv", index=False)
    evaluation, holdout = evaluate_holdout(panel, holdout_months=holdout_months)
    holdout.to_csv(paths.outputs / "holdout_predictions.csv", index=False)
    with (paths.outputs / "evaluation.json").open("w", encoding="utf-8") as handle:
        json.dump(evaluation, handle, indent=2)

    forecast = recursive_forecast(
        panel,
        holiday_features,
        months=forecast_months,
        method=evaluation["selected_model"],
    )
    forecast.to_csv(paths.outputs / "market_forecast.csv", index=False)
    pressure = pressure_forecast(forecast, arrivals, visitor_days)
    pressure.to_csv(paths.outputs / "tourism_pressure_forecast.csv", index=False)
    return {
        "evaluation": evaluation,
        "latest_observation": pd.Timestamp(arrivals["month"].max()).strftime("%Y-%m-%d"),
        "forecast_start": pd.Timestamp(forecast["month"].min()).strftime("%Y-%m-%d"),
        "forecast_end": pd.Timestamp(forecast["month"].max()).strftime("%Y-%m-%d"),
        "output_directory": str(paths.outputs),
    }
