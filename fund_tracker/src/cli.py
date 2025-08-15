"""Command-line entry point.

Usage
-----
• First run: ``python -m fund_tracker.cli`` → pulls *all-time* Peter Thiel
  deals (because there’s no record of a previous run) and records today’s
  date.
• Subsequent runs (e.g. weekly cron): the same command automatically fetches
  only the deals announced since the last successful run (effectively the
  past 7 days if you run once a week).

You can override the window with ``--days-back N`` where *N* is a positive
integer (days). Passing ``0`` or a negative value forces an all-time backfill
regardless of the last-run file.
"""

import json
import argparse
from pathlib import Path

import pendulum
import sys

from .pipeline import run_pipeline

def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Fetch Peter Thiel-related deals from Crunchbase and send to Zapier. "
            "If --days-back is omitted, the script will automatically determine "
            "the correct window based on the date of the last successful run."
        )
    )
    parser.add_argument(
        "--days-back",
        type=int,
        default=None,
        help=(
            "Number of days to look back. 0 or negative ⇒ all-time. "
            "If omitted, window is computed from last run."
        ),
    )

    args = parser.parse_args()


    LAST_RUN_FILE = Path(__file__).resolve().parents[1] / "last_run.txt"

    if args.days_back is not None:
        # User explicitly set a value → respect it verbatim.
        days_back = args.days_back if args.days_back > 0 else None
    else:
        # Auto-determine window.
        if LAST_RUN_FILE.exists():
            try:
                last_run_date = pendulum.parse(LAST_RUN_FILE.read_text().strip()).date()
                days_back = (pendulum.today().date() - last_run_date).days or 1
            except Exception:
                # Malformed file – fall back to weekly window.
                days_back = 7
        else:
            # No previous run – perform full historical fetch.
            days_back = None

    deals = run_pipeline(days_back=days_back)
    print(json.dumps([d.__dict__ for d in deals], indent=2))

    # Record today as the last successful run (only if everything above worked)
    try:
        LAST_RUN_FILE.write_text(pendulum.today().to_date_string())
    except Exception as exc:
        # Non-fatal – log to stderr but don’t crash the main flow.
        print(f"Warning: could not write last-run file: {exc}", file=sys.stderr)

if __name__ == "__main__":
    main()
