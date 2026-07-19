from __future__ import annotations

import argparse
import json

from .pipeline import run_pipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Forecast Singapore monthly tourist pressure")
    subparsers = parser.add_subparsers(dest="command", required=True)
    run = subparsers.add_parser("run", help="Refresh data, evaluate the model and forecast")
    run.add_argument("--no-refresh", action="store_true", help="Use cached official data")
    run.add_argument("--forecast-months", type=int, default=12)
    run.add_argument("--holdout-months", type=int, default=12)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "run":
        result = run_pipeline(
            refresh=not args.no_refresh,
            forecast_months=args.forecast_months,
            holdout_months=args.holdout_months,
        )
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
