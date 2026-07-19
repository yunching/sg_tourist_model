from __future__ import annotations

import numpy as np
import pandas as pd


def build_panel(arrivals: pd.DataFrame, holiday_features: pd.DataFrame) -> pd.DataFrame:
    panel = arrivals.merge(holiday_features, on=["market", "month"], how="left")
    panel = panel.sort_values(["market", "month"]).reset_index(drop=True)
    group = panel.groupby("market", group_keys=False)["arrivals"]
    panel["lag_1"] = group.shift(1)
    panel["lag_12"] = group.shift(12)
    panel["rolling_mean_3"] = group.transform(lambda series: series.shift(1).rolling(3).mean())
    panel["rolling_mean_12"] = group.transform(lambda series: series.shift(1).rolling(12).mean())
    panel["month_number"] = panel["month"].dt.month
    panel["month_sin"] = np.sin(2 * np.pi * panel["month_number"] / 12)
    panel["month_cos"] = np.cos(2 * np.pi * panel["month_number"] / 12)
    panel["trend"] = (panel["month"].dt.year - panel["month"].dt.year.min()) * 12 + panel["month_number"]
    # Border restrictions and the 2023 reopening ramp are not normal
    # calendar demand, so they are excluded from holiday-effect fitting.
    panel["pandemic"] = panel["month"].dt.year.between(2020, 2023).astype(int)
    return panel
