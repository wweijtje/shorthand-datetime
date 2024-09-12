import datetime
from typing import Optional
from unittest import mock

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

FAKE_TIME: datetime.datetime = datetime.datetime(2024, 11, 15, 17, 5, 55)


# Helper class for datetime patching
class mydatetime(datetime.datetime):
    @classmethod
    def now(cls, tz: Optional[datetime.tzinfo] = None):
        """Providing a timezone is essential for mypy to not complain, as
        otherwise it will infer the return type as datetime.datetime or None,
        meaning that the return type will be Optional[datetime.datetime].
        Optional[datetime.datetime] is not granted to have the ``year``,
        ``month``, ``day``, ``hour``, ``minute``, and ``second`` attributes.
        """
        if isinstance(tz, datetime.tzinfo):
            return FAKE_TIME.astimezone(tz) if tz else FAKE_TIME
        return FAKE_TIME


def test_shorthand_no_strategies():
    """Test the shorthand parsing with fixed inputs"""
    from shorthand_datetime.shorthand import parse_shorthand_datetime

    with mock.patch("datetime.datetime", mydatetime):
        s = "now+1d"
        dt_1d = parse_shorthand_datetime(s)
        assert dt_1d.strftime("%Y%m%d") == "20241116"

        s = "now+7d"
        dt_7d = parse_shorthand_datetime(s)
        assert dt_7d.strftime("%Y%m%d") == "20241122"

        s = "now+1M"
        dt_M = parse_shorthand_datetime(s)
        assert dt_M.strftime("%Y%m%d") == "20241216"

        s = "now+1Y"
        dt_y = parse_shorthand_datetime(s)
        assert dt_y.strftime("%Y%m%d") == "20251115"

        s = "now-1d"
        dt_1d = parse_shorthand_datetime(s)
        assert dt_1d.strftime("%Y%m%d") == "20241114"

        s = "now-7d"
        dt_7d = parse_shorthand_datetime(s)
        assert dt_7d.strftime("%Y%m%d") == "20241108"

        s = "now-1M"
        dt_M = parse_shorthand_datetime(s)
        assert dt_M.strftime("%Y%m%d") == "20241016"

        s = "now-1Y"
        dt_y = parse_shorthand_datetime(s)
        assert dt_y.strftime("%Y%m%d") == "20231116"


def test_rounded_shorthand_no_strategies():
    """Test the shorthand with rounding (e.g., "now/d", "now/M", "now/Y")"""
    from shorthand_datetime.shorthand import parse_shorthand_datetime

    with mock.patch("datetime.datetime", mydatetime):
        s = "now/d"
        dt_d = parse_shorthand_datetime(s)
        assert dt_d.second == 0
        assert dt_d.strftime("%Y%m%d_%H%M%S") == "20241115_000000"

        s = "now/M"
        dt_7d = parse_shorthand_datetime(s)
        assert dt_7d.strftime("%Y%m%d") == "20241101"

        s = "now/Y"
        dt_7d = parse_shorthand_datetime(s)
        assert dt_7d.strftime("%Y%m%d") == "20240101"

        s = "now-2Y/Y"
        dt_7d = parse_shorthand_datetime(s)
        assert dt_7d.strftime("%Y%m%d") == "20220101"

        s = "now-1M/M"
        dt_7d = parse_shorthand_datetime(s)
        assert dt_7d.strftime("%Y%m%d") == "20241001"


def test_patch_datetime():
    """Test the datetime patching"""
    with mock.patch("datetime.datetime", mydatetime):
        assert datetime.datetime.now() == FAKE_TIME
        assert datetime.datetime.now().year == FAKE_TIME.year
        assert datetime.datetime.now().month == FAKE_TIME.month
        assert datetime.datetime.now().day == FAKE_TIME.day
        assert datetime.datetime.now().hour == FAKE_TIME.hour
        assert datetime.datetime.now().minute == FAKE_TIME.minute
        assert datetime.datetime.now().second == FAKE_TIME.second


def generate_shorthand(min_value: int = -600, max_value: int = 600) -> st.SearchStrategy:
    """Generate shorthand expressions dynamically"""
    time_unit = st.sampled_from(["d", "M", "Y"])  # days, months, years
    # -- Works until ~600 months (50 years) in the future because of the
    #    approximation in the calculation of months from weeks
    amount = st.integers(min_value=min_value, max_value=max_value)  # random integer
    return st.builds(lambda u, a: f"now{a:+d}{u}", time_unit, amount)


def generate_rounded_shorthand() -> st.SearchStrategy:
    """Generate rounded shorthand expressions (e.g., now/d, now/M, now/Y)"""
    time_unit = st.sampled_from(["d", "M", "Y"])
    return st.builds(lambda u: f"now/{u}", time_unit)


@given(shorthand=generate_shorthand())
@settings(max_examples=2000)
def test_shorthand(shorthand: str):
    """Test the shorthand parsing with dynamically generated inputs"""
    from shorthand_datetime.shorthand import parse_shorthand_datetime

    def get_delta(shorthand: str) -> float:
        """Extract the delta from the shorthand string"""
        return float(shorthand.split("-")[1][:-1]) if "-" in shorthand else float(shorthand.split("+")[1][:-1])

    # Apply the patch inside the test so it resets for every hypothesis example
    with mock.patch("datetime.datetime", mydatetime):
        dt: Optional[datetime.datetime] = parse_shorthand_datetime(shorthand)
        if dt is None:
            pytest.fail(f"parse_shorthand_datetime returned None for shorthand: {shorthand}")

        delta = get_delta(shorthand)
        # We won't know the exact output since we're generating floats, but we can check the delta
        if "d" in shorthand:
            # Extract the number of days from the shorthand string
            actual_delta = abs(datetime.datetime.now() - dt).total_seconds() / (24 * 60 * 60)  # type: ignore
        elif "M" in shorthand:
            # For months, we approximate by comparing the difference in months
            actual_delta = abs((datetime.datetime.now().year - dt.year) * 12 + datetime.datetime.now().month - dt.month)  # type: ignore
        elif "Y" in shorthand:
            # For years, we compare the difference in years
            actual_delta = abs(datetime.datetime.now().year - dt.year)  # type: ignore

        assert abs(actual_delta - delta) < 1e-1
        if "+" in shorthand:
            assert dt >= datetime.datetime.now()  # type: ignore
        elif "-" in shorthand:
            assert dt <= datetime.datetime.now()  # type: ignore


@given(shorthand=generate_shorthand(min_value=-1000, max_value=-601))
@settings(max_examples=500)
def test_shorthand_failure_1(shorthand: str):
    """Test the shorthand parsing with dynamically generated inputs.
    Expect a ValueError when the value is out of range for large negative values
    of months."""
    from shorthand_datetime.shorthand import parse_shorthand_datetime

    if "M" in shorthand:
        with pytest.raises(ValueError):
            parse_shorthand_datetime(shorthand)


@given(shorthand=generate_shorthand(min_value=601, max_value=1000))
@settings(max_examples=500)
def test_shorthand_failure_2(shorthand: str):
    """Test the shorthand parsing with dynamically generated inputs.
    Expect a ValueError when the value is out of range for large positive values
    of months."""
    from shorthand_datetime.shorthand import parse_shorthand_datetime

    if "M" in shorthand:
        with pytest.raises(ValueError):
            parse_shorthand_datetime(shorthand)


@given(shorthand=generate_rounded_shorthand())
def test_rounded_shorthand(shorthand: str):
    """Test the shorthand with rounding (e.g., "now/d", "now/M", "now/Y")"""
    from shorthand_datetime.shorthand import parse_shorthand_datetime

    # Apply the patch inside the test so it resets for every hypothesis example
    with mock.patch("datetime.datetime", mydatetime):
        dt: Optional[datetime.datetime] = parse_shorthand_datetime(shorthand)
        if dt is None:
            pytest.fail(f"parse_shorthand_datetime returned None for shorthand: {shorthand}")

        if "/d" in shorthand:
            # Check if the time is rounded to the start of the day (no hour, minute, second)
            assert dt.hour == 0 and dt.minute == 0 and dt.second == 0  # type: ignore
        elif "/M" in shorthand:
            # Check if the date is rounded to the start of the month (day=1, no hour, minute, second)
            assert dt.day == 1 and dt.hour == 0 and dt.minute == 0 and dt.second == 0  # type: ignore
        elif "/Y" in shorthand:
            # Check if the date is rounded to the start of the year (month=1, day=1, no hour, minute, second)
            assert dt.month == 1 and dt.day == 1 and dt.hour == 0 and dt.minute == 0 and dt.second == 0  # type: ignore
