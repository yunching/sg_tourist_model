from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


MARKETS: tuple[str, ...] = (
    "China",
    "Indonesia",
    "Malaysia",
    "Australia",
    "India",
    "Japan",
    "South Korea",
    "Philippines",
    "United Kingdom",
    "USA",
)

HOLIDAY_COUNTRY_CODES: dict[str, str] = {
    "China": "CN",
    "Indonesia": "ID",
    "Malaysia": "MY",
    "Australia": "AU",
    "India": "IN",
    "Japan": "JP",
    "South Korea": "KR",
    "Philippines": "PH",
    "United Kingdom": "GB",
    "USA": "US",
}

# Johor is directly connected to Singapore; Python Holidays uses ISO code 01.
HOLIDAY_SUBDIVISIONS: dict[str, dict[str, str]] = {
    "Malaysia": {"Johor": "01"},
}

ARRIVALS_DATASET_ID = "d_7e7b2ee60c6ffc962f80fef129cf306e"
VISITOR_DAYS_DATASET_ID = "d_f1fa8e1ffdda0912360f820af84c2b9e"
DATASTORE_URL = "https://data.gov.sg/api/action/datastore_search"


@dataclass(frozen=True)
class Paths:
    root: Path

    @property
    def raw(self) -> Path:
        return self.root / "data" / "raw"

    @property
    def processed(self) -> Path:
        return self.root / "data" / "processed"

    @property
    def manual(self) -> Path:
        return self.root / "data" / "manual"

    @property
    def outputs(self) -> Path:
        return self.root / "outputs"

    def create(self) -> None:
        for path in (self.raw, self.processed, self.manual, self.outputs):
            path.mkdir(parents=True, exist_ok=True)


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]
