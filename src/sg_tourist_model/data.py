from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import pandas as pd

from .config import (
    ARRIVALS_DATASET_ID,
    DATASTORE_URL,
    MARKETS,
    VISITOR_DAYS_DATASET_ID,
)

MONTH_COLUMN = re.compile(r"^(\d{4})([A-Z][a-z]{2})$")


def fetch_datastore_records(dataset_id: str, timeout: int = 30) -> list[dict]:
    query = urlencode({"resource_id": dataset_id, "limit": 1000})
    request = Request(
        f"{DATASTORE_URL}?{query}",
        headers={"User-Agent": "sg-tourist-model/0.1"},
    )
    with urlopen(request, timeout=timeout) as response:
        payload = json.load(response)
    if not payload.get("success"):
        raise RuntimeError(f"data.gov.sg returned an unsuccessful response for {dataset_id}")
    return payload["result"]["records"]


def _month_from_column(value: str) -> pd.Timestamp | None:
    if not MONTH_COLUMN.match(value):
        return None
    return pd.to_datetime(value, format="%Y%b")


def normalize_wide_series(
    records: list[dict],
    series_names: set[str] | None = None,
    value_name: str = "value",
) -> pd.DataFrame:
    rows: list[dict] = []
    for record in records:
        series = str(record.get("DataSeries", "")).strip()
        if series_names is not None and series not in series_names:
            continue
        for key, raw_value in record.items():
            month = _month_from_column(key)
            if month is None:
                continue
            value = pd.to_numeric(raw_value, errors="coerce")
            if pd.isna(value):
                continue
            rows.append({"market": series, "month": month, value_name: float(value)})
    frame = pd.DataFrame(rows)
    if frame.empty:
        requested = sorted(series_names) if series_names else "all series"
        raise ValueError(f"No usable observations found for {requested}")
    return frame.sort_values(["market", "month"]).reset_index(drop=True)


def load_arrivals(cache_path: Path, refresh: bool = True) -> pd.DataFrame:
    if cache_path.exists() and not refresh:
        return pd.read_csv(cache_path, parse_dates=["month"])
    records = fetch_datastore_records(ARRIVALS_DATASET_ID)
    frame = normalize_wide_series(records, set(MARKETS), "arrivals")
    missing = set(MARKETS) - set(frame["market"].unique())
    if missing:
        raise ValueError(f"Official dataset is missing configured markets: {sorted(missing)}")
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(cache_path, index=False)
    return frame


def load_visitor_days(cache_path: Path, refresh: bool = True) -> pd.DataFrame:
    if cache_path.exists() and not refresh:
        return pd.read_csv(cache_path, parse_dates=["month"])
    records = fetch_datastore_records(VISITOR_DAYS_DATASET_ID)
    frame = normalize_wide_series(records, {"Visitor Days"}, "visitor_days")
    frame = frame.drop(columns="market")
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(cache_path, index=False)
    return frame
