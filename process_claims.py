"""Command-line entry point for the insurance claim processor.

Usage:
    python process_claims.py [path/to/claims.csv]

Prints the total approved claim amount per policy and reports any rows that
were skipped because of invalid policy numbers or malformed data.
"""

from __future__ import annotations

import argparse
import sys

from claims_processor import process_claims

DEFAULT_CSV = "data/sample_claims.csv"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Process insurance claim CSV data.")
    parser.add_argument(
        "csv_path",
        nargs="?",
        default=DEFAULT_CSV,
        help=f"Path to the claims CSV file (default: {DEFAULT_CSV})",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with a non-zero status if any row fails validation.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    try:
        result = process_claims(args.csv_path)
    except FileNotFoundError:
        print(f"error: file not found: {args.csv_path}", file=sys.stderr)
        return 2

    for policy in sorted(result.summaries):
        summary = result.summaries[policy]
        print(
            f"{policy}: {summary.approved_total} "
            f"({summary.approved_count}/{summary.claim_count} approved)"
        )

    print(f"\nTotal approved across all policies: {result.total_approved}")

    if result.errors:
        print(f"\nSkipped {len(result.errors)} invalid row(s):", file=sys.stderr)
        for error in result.errors:
            print(f"  - {error}", file=sys.stderr)
        if args.strict:
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
