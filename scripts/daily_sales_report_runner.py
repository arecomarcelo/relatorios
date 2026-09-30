"""Helpers for daily sales-report scheduling and rendering."""

from __future__ import annotations

import argparse
import hmac
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

SAO_PAULO = ZoneInfo("America/Sao_Paulo")


def previous_day_period(now: datetime | None = None) -> tuple[date, date]:
    """Return the prior São Paulo calendar day as an inclusive one-day period."""
    if now is None:
        now = datetime.now(SAO_PAULO)
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("now must be timezone-aware")

    report_day = now.astimezone(SAO_PAULO).date() - timedelta(days=1)
    return report_day, report_day


def parse_report_date(value: str) -> date:
    """Parse the strict YYYY-MM-DD date used to render a single-day report."""
    if not isinstance(value, str) or len(value) != 10:
        raise ValueError("report date must use YYYY-MM-DD")
    parsed = date.fromisoformat(value)
    if parsed.isoformat() != value:
        raise ValueError("report date must use YYYY-MM-DD")
    return parsed


def filters_for_report_day(report_day: date) -> dict[str, date]:
    """Return only the equal start/end date filters; leave every other filter unset."""
    if not isinstance(report_day, date):
        raise TypeError("report_day must be a date")
    return {"data_inicio": report_day, "data_fim": report_day}


def is_preview_token_valid(expected_token: str | None, provided_token: str | None) -> bool:
    """Require a non-empty, exact, constant-time match for the temporary preview token."""
    if not isinstance(expected_token, str) or not expected_token:
        return False
    if not isinstance(provided_token, str) or not provided_token:
        return False
    try:
        expected_bytes = expected_token.encode("ascii")
        provided_bytes = provided_token.encode("ascii")
    except UnicodeEncodeError:
        return False
    return hmac.compare_digest(expected_bytes, provided_bytes)


def main(argv: list[str] | None = None) -> int:
    """Print the prior local calendar day for use by scheduled wrappers."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--date-only",
        action="store_true",
        help="imprime a data anterior em YYYY-MM-DD, no fuso America/Sao_Paulo",
    )
    args = parser.parse_args(argv)
    if not args.date_only:
        parser.error("informe --date-only")

    start_date, end_date = previous_day_period()
    if start_date != end_date:
        raise RuntimeError("o relatório diário deve usar datas inicial e final iguais")
    print(start_date.isoformat())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
