from datetime import date, datetime
from zoneinfo import ZoneInfo

import pytest

import scripts.daily_sales_report_runner as report_runner
from scripts.daily_sales_report_runner import (
    filters_for_report_day,
    parse_report_date,
    previous_day_period,
)

SAO_PAULO = ZoneInfo("America/Sao_Paulo")


@pytest.mark.parametrize(
    ("run_at", "expected"),
    [
        (datetime(2026, 9, 30, 7, 0, tzinfo=SAO_PAULO), date(2026, 9, 29)),
        (datetime(2026, 10, 1, 7, 0, tzinfo=SAO_PAULO), date(2026, 9, 30)),
        (datetime(2026, 10, 2, 7, 0, tzinfo=SAO_PAULO), date(2026, 10, 1)),
        (datetime(2027, 1, 1, 7, 0, tzinfo=SAO_PAULO), date(2026, 12, 31)),
    ],
)
def test_previous_day_period_uses_prior_local_calendar_day(run_at, expected):
    assert previous_day_period(run_at) == (expected, expected)


def test_previous_day_period_converts_aware_instants_to_sao_paulo():
    run_at_utc = datetime(2026, 9, 30, 10, 0, tzinfo=ZoneInfo("UTC"))

    assert previous_day_period(run_at_utc) == (date(2026, 9, 29), date(2026, 9, 29))


def test_previous_day_period_rejects_naive_datetimes():
    with pytest.raises(ValueError, match="timezone-aware"):
        previous_day_period(datetime(2026, 9, 30, 7, 0))


def test_parse_report_date_accepts_iso_calendar_date():
    assert parse_report_date("2026-09-29") == date(2026, 9, 29)


def test_parse_report_date_rejects_invalid_date():
    with pytest.raises(ValueError):
        parse_report_date("2026-02-30")


def test_filters_use_only_equal_start_and_end_dates():
    report_day = date(2026, 9, 29)

    assert filters_for_report_day(report_day) == {
        "data_inicio": report_day,
        "data_fim": report_day,
    }


def test_preview_token_validation_accepts_matching_token():
    assert (
        report_runner.is_preview_token_valid("capture-token", "capture-token") is True
    )


def test_preview_token_validation_rejects_mismatched_tokens():
    assert report_runner.is_preview_token_valid("capture-token", "other-token") is False


def test_preview_token_validation_rejects_missing_or_empty_tokens():
    assert report_runner.is_preview_token_valid(None, "capture-token") is False
    assert report_runner.is_preview_token_valid("capture-token", None) is False
    assert report_runner.is_preview_token_valid("", "capture-token") is False
    assert report_runner.is_preview_token_valid("capture-token", "") is False


def test_preview_token_validation_rejects_non_ascii_tokens():
    assert report_runner.is_preview_token_valid("capture-token", "café") is False
    assert report_runner.is_preview_token_valid("café", "café") is False


def test_cli_date_only_prints_the_computed_previous_day(monkeypatch, capsys):
    expected_day = date(2026, 9, 29)
    monkeypatch.setattr(
        report_runner,
        "previous_day_period",
        lambda: (expected_day, expected_day),
    )

    assert report_runner.main(["--date-only"]) == 0
    assert capsys.readouterr().out == "2026-09-29\n"
