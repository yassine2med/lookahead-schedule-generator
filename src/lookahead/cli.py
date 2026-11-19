"""Command line interface."""
from __future__ import annotations

import argparse
import sys
from datetime import date

from . import core


def main(argv: list[str] | None = None) -> int:
    """Run the tool and return an exit code."""
    parser = argparse.ArgumentParser(prog="lookahead", description="Lookahead report from a schedule CSV.")
    parser.add_argument("csv", help="CSV with columns activity,trade,location,start,finish")
    parser.add_argument("--from", dest="from_date", default=date.today().isoformat(),
                        help="any date in the first week, YYYY-MM-DD (default today)")
    parser.add_argument("--weeks", type=int, default=3, help="number of weeks (default 3)")
    parser.add_argument("--trades", action="store_true", help="add a count of activity-weeks per trade")
    args = parser.parse_args(argv)
    try:
        start = date.fromisoformat(args.from_date)
        weeks = core.build(core.load(args.csv), start, args.weeks)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(core.render(weeks))
    if args.trades:
        print("\nActivity-weeks per trade:")
        for trade, n in core.by_trade(weeks).items():
            print(f"  {trade:<16} {n}")
    return 0
