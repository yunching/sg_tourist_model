from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

NUMERIC_FEATURES = (
    "lag_1",
    "lag_12",
    "rolling_mean_3",
    "rolling_mean_12",
    "holiday_days",
    "holiday_weekend_days",
    "max_consecutive_holidays",
    "state_holiday_days",
    "state_holiday_weekend_days",
    "state_max_consecutive_holidays",
    "school_break_days",
    "school_break_weight",
    "international_school_break_days",
    "international_school_break_weight",
    "travel_window_days",
    "travel_window_weight",
    "effective_holiday_days",
    "state_effective_holiday_days",
    "long_weekend_count",
    "max_time_off_block",
    "holiday_departure_lead",
    "holiday_return_lag",
    "school_holiday_overlap_weight",
    "month_sin",
    "month_cos",
    "trend",
)



HOLIDAY_RESPONSE_FEATURES = (
    "effective_holiday_days",
    "state_effective_holiday_days",
    "long_weekend_count",
    "max_time_off_block",
    "holiday_departure_lead",
    "holiday_return_lag",
    "school_holiday_overlap_weight",
    "school_break_weight",
    "travel_window_weight",
)

@dataclass
class RidgeArrivalModel:
    alpha: float = 10.0
    coefficients_: np.ndarray | None = None
    means_: np.ndarray | None = None
    scales_: np.ndarray | None = None
    columns_: list[str] | None = None

    def _design(self, frame: pd.DataFrame, fit: bool) -> np.ndarray:
        numeric = frame.reindex(columns=NUMERIC_FEATURES, fill_value=0.0).astype(float).to_numpy()
        if fit:
            self.means_ = np.nanmean(numeric, axis=0)
            self.scales_ = np.nanstd(numeric, axis=0)
            self.scales_[self.scales_ == 0] = 1.0
        if self.means_ is None or self.scales_ is None:
            raise RuntimeError("Model has not been fit")
        numeric = np.where(np.isnan(numeric), self.means_, numeric)
        scaled = (numeric - self.means_) / self.scales_

        categories = pd.get_dummies(frame["market"], prefix="market", dtype=float)
        if fit:
            self.columns_ = list(categories.columns)
        if self.columns_ is None:
            raise RuntimeError("Model has not been fit")
        categories = categories.reindex(columns=self.columns_, fill_value=0.0)
        category_values = categories.to_numpy()
        holiday_indices = [NUMERIC_FEATURES.index(name) for name in HOLIDAY_RESPONSE_FEATURES]
        # Shared coefficients capture the general effect; regularized
        # interactions let each origin respond differently without fitting
        # ten completely separate small models.
        holiday_values = numeric[:, holiday_indices] / self.scales_[holiday_indices]
        interactions = (
            holiday_values[:, :, None] * category_values[:, None, :]
        ).reshape(len(frame), -1)
        return np.column_stack([np.ones(len(frame)), scaled, category_values, interactions])

    def fit(self, frame: pd.DataFrame) -> "RidgeArrivalModel":
        clean = frame.dropna(subset=["arrivals", "lag_12"]).copy()
        if clean.empty:
            raise ValueError("No complete training observations")
        x = self._design(clean, fit=True)
        # Learn a correction to the strong same-month-last-year anchor instead
        # of asking a small pooled model to relearn the full seasonal level.
        y = np.log1p(clean["arrivals"].to_numpy(dtype=float)) - np.log1p(
            clean["lag_12"].to_numpy(dtype=float)
        )
        penalty = np.eye(x.shape[1]) * self.alpha
        penalty[0, 0] = 0.0
        self.coefficients_ = np.linalg.solve(x.T @ x + penalty, x.T @ y)
        return self

    def predict(self, frame: pd.DataFrame) -> np.ndarray:
        if self.coefficients_ is None:
            raise RuntimeError("Model has not been fit")
        correction = self._design(frame, fit=False) @ self.coefficients_
        correction = np.clip(correction, -0.5, 0.5)
        anchor = np.log1p(frame["lag_12"].to_numpy(dtype=float))
        values = np.expm1(anchor + correction)
        return np.maximum(values, 0.0)


RIDGE_ALPHAS = (10.0, 30.0, 100.0, 300.0)


def _fit_tuned_model(frame: pd.DataFrame, validation_months: int = 12) -> RidgeArrivalModel:
    """Select shrinkage on a trailing slice of training data, then refit."""
    months = sorted(frame["month"].dropna().unique())
    if len(months) <= validation_months:
        return RidgeArrivalModel().fit(frame)
    cutoff = pd.Timestamp(months[-validation_months])
    inner_train = frame[frame["month"] < cutoff]
    validation = frame[frame["month"] >= cutoff]
    if inner_train.empty or validation.empty:
        return RidgeArrivalModel().fit(frame)

    actual = validation["arrivals"].to_numpy(dtype=float)
    scored: list[tuple[float, float]] = []
    for alpha in RIDGE_ALPHAS:
        candidate = RidgeArrivalModel(alpha=alpha).fit(inner_train)
        prediction = candidate.predict(validation)
        wape = float(np.sum(np.abs(prediction - actual)) / np.sum(np.abs(actual)))
        scored.append((wape, alpha))
    selected_alpha = min(scored)[1]
    return RidgeArrivalModel(alpha=selected_alpha).fit(frame)


def evaluate_holdout(panel: pd.DataFrame, holdout_months: int = 12) -> tuple[dict, pd.DataFrame]:
    eligible = panel[(panel["pandemic"] == 0) & panel["lag_12"].notna()].copy()
    months = sorted(eligible["month"].unique())
    if len(months) <= holdout_months:
        raise ValueError("Not enough eligible months for the requested holdout")
    cutoff = pd.Timestamp(months[-holdout_months])
    train = eligible[eligible["month"] < cutoff]
    test = eligible[eligible["month"] >= cutoff].copy()
    model = _fit_tuned_model(train)
    test["prediction"] = model.predict(test)
    test["seasonal_naive"] = test["lag_12"]

    def metrics(prediction: pd.Series) -> dict[str, float]:
        actual = test["arrivals"].to_numpy(dtype=float)
        predicted = prediction.to_numpy(dtype=float)
        error = predicted - actual
        return {
            "mae": float(np.mean(np.abs(error))),
            "rmse": float(np.sqrt(np.mean(error**2))),
            "wape": float(np.sum(np.abs(error)) / np.sum(np.abs(actual))),
        }

    model_metrics = metrics(test["prediction"])
    naive_metrics = metrics(test["seasonal_naive"])
    result = {
        "holdout_start": cutoff.strftime("%Y-%m-%d"),
        "holdout_end": pd.Timestamp(test["month"].max()).strftime("%Y-%m-%d"),
        "observations": int(len(test)),
        "model": model_metrics,
        "model_alpha": model.alpha,
        "seasonal_naive": naive_metrics,
        "selected_model": "holiday_ridge" if model_metrics["wape"] <= naive_metrics["wape"] else "seasonal_naive",
    }
    return result, test


def recursive_forecast(
    panel: pd.DataFrame,
    holiday_features: pd.DataFrame,
    months: int = 12,
    method: str = "holiday_ridge",
) -> pd.DataFrame:
    fit_frame = panel[(panel["pandemic"] == 0) & panel["lag_12"].notna()].copy()
    model = _fit_tuned_model(fit_frame) if method == "holiday_ridge" else None
    history = panel[["market", "month", "arrivals"]].copy()
    latest = pd.Timestamp(history["month"].max())
    future_months = pd.date_range(latest + pd.offsets.MonthBegin(1), periods=months, freq="MS")
    output: list[pd.DataFrame] = []

    for month in future_months:
        skeleton = pd.DataFrame({"market": sorted(history["market"].unique()), "month": month})
        combined = pd.concat([history, skeleton.assign(arrivals=np.nan)], ignore_index=True)
        future_panel = build_future_rows(combined, holiday_features)
        current = future_panel[future_panel["month"] == month].copy()
        if method == "holiday_ridge":
            current["prediction"] = model.predict(current)
        else:
            current["prediction"] = current["lag_12"]
        output.append(current[["market", "month", "prediction"]])
        additions = current[["market", "month", "prediction"]].rename(columns={"prediction": "arrivals"})
        history = pd.concat([history, additions], ignore_index=True)
    return pd.concat(output, ignore_index=True)


def build_future_rows(history: pd.DataFrame, holiday_features: pd.DataFrame) -> pd.DataFrame:
    from .features import build_panel

    return build_panel(history, holiday_features)
