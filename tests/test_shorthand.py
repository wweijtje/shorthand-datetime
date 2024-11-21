import datetime
from typing import Optional
from unittest import mock

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

FAKE_TIME: datetime.datetime = datetime.datetime(2024, 11, 15, 17, 5, 55, tzinfo=datetime.timezone.utc)


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

        s = "now+1W"
        dt_1W = parse_shorthand_datetime(s)
        assert dt_1W.strftime("%Y%m%d") == "20241122"

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

        s = "now-1W"
        dt_1W = parse_shorthand_datetime(s)
        assert dt_1W.strftime("%Y%m%d") == "20241108"

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


def test_parse_shorthand_datetime_now():
    """Test parsing 'now'"""
    from shorthand_datetime.shorthand import parse_shorthand_datetime

    with mock.patch("datetime.datetime", mydatetime):
        dt = parse_shorthand_datetime("now")
        assert dt == datetime.datetime.now()


@given(shorthand=st.text(min_size=1).filter(lambda s: not s.startswith(("now", "-", "+", "/"))))
def test_parse_shorthand_not_starting_with_now_returns_None(shorthand: str):
    """Test parsing a shorthand that does not start with 'now' returns None"""
    from shorthand_datetime.shorthand import parse_shorthand_datetime

    with mock.patch("datetime.datetime", mydatetime):
        dt = parse_shorthand_datetime(shorthand)
        assert dt is None


@given(shorthand=st.sampled_from(["-", "+"]))
def test_parse_shorthand_starting_with_unit_returns_now(shorthand: str):
    """Test parsing a shorthand that starts with a unit returns the current datetime"""
    from shorthand_datetime.shorthand import parse_shorthand_datetime

    with mock.patch("datetime.datetime", mydatetime):
        dt = parse_shorthand_datetime(shorthand)
        assert dt == datetime.datetime.now()


@given(shorthand=st.sampled_from(["/"]))
def test_parse_shorthand_starting_with_unit_returns_none(shorthand: str):
    """Test parsing a shorthand that starts with a unit returns the current datetime"""
    from shorthand_datetime.shorthand import parse_shorthand_datetime

    with mock.patch("datetime.datetime", mydatetime):
        dt = parse_shorthand_datetime(shorthand)
        assert dt is None


@given(
    shorthand=st.sampled_from(
        [
            "now + 1d",
            "now - 1d",
            "now - 1M",
            "now - 1Y",
            "now + 1M",
            "now + 1Y",
            "now / d",
            "now / M",
            "now / Y",
            "now - 2Y / Y",
            "now - 1M / M",
        ]
    )
)
def test_parse_shorthand_with_spaces(shorthand: str):
    """Test parsing a shorthand with spaces"""
    from shorthand_datetime.shorthand import parse_shorthand_datetime

    expected_results = {
        "now + 1d": "20241116",
        "now - 1d": "20241114",
        "now - 1M": "20241016",
        "now - 1Y": "20231116",
        "now + 1M": "20241216",
        "now + 1Y": "20251115",
        "now / d": "20241115_000000",
        "now / M": "20241101_000000",
        "now / Y": "20240101_000000",
        "now - 2Y / Y": "20220101_000000",
        "now - 1M / M": "20241001_000000",
    }

    with mock.patch("datetime.datetime", mydatetime):
        dt = parse_shorthand_datetime(shorthand)
        if " / " in shorthand:
            assert dt.second == 0  # type: ignore
            assert dt.strftime("%Y%m%d_%H%M%S") == expected_results[shorthand]  # type: ignore
        else:
            assert dt.strftime("%Y%m%d") == expected_results[shorthand]  # type: ignore


@given(target=st.sampled_from(["s", "m", "h", "H", "d", "W", "M", "Y"]))
def test__roundtimestamp_valid(target):
    """Test the _roundtimestamp function with valid targets"""
    from shorthand_datetime.shorthand import _roundtimestamp

    with mock.patch("datetime.datetime", mydatetime):
        result = _roundtimestamp(datetime.datetime.now(), target)
        assert result.__class__.__name__ == "datetime"


@given(target=st.text().filter(lambda x: x not in ["s", "m", "h", "H", "d", "W", "M", "Y"]))
def test__roundtimestamp_invalid(target):
    """Test the _roundtimestamp function with invalid targets"""
    from shorthand_datetime.shorthand import _roundtimestamp

    with mock.patch("datetime.datetime", mydatetime):
        with pytest.raises(ValueError):
            _roundtimestamp(datetime.datetime.now(), target)


@given(unit=st.sampled_from(["s", "m", "h", "H", "d", "W", "M", "Y"]))
def test__timedelta_valid(unit):
    """Test the _timedelta function with valid units"""
    from shorthand_datetime.shorthand import _timedelta

    result = _timedelta(1, unit)
    assert result.__class__.__name__ == "timedelta"


@given(unit=st.text().filter(lambda x: x not in ["s", "m", "h", "H", "d", "W", "M", "Y"]))
def test__timedelta_invalid(unit):
    """Test the _timedelta function with invalid units"""
    from shorthand_datetime.shorthand import _timedelta

    with pytest.raises(ValueError):
        _timedelta(1, unit)


def test__backslash_not_second_to_last():
    """Test the _backslash_not_second_to_last function"""
    from shorthand_datetime.shorthand import parse_shorthand_datetime

    dt = parse_shorthand_datetime("now / ")
    assert dt is None
    dt = parse_shorthand_datetime("now /d")
    assert isinstance(dt, datetime.datetime)
    dt = parse_shorthand_datetime("now /d/")
    assert dt is None


@pytest.mark.parametrize(
    "datestr, tz, expected",
    [
        ("now", "UTC", "20241115_170555"),
        ("now", "America/New_York", "20241115_120555"),
        ("now-6d/d", "UTC", "20241109_000000"),
        ("now-1W", "America/New_York", "20241108_120555"),
        ("now-2M", "UTC", "20240915_210552"),
        ("now-1M/M", "America/New_York", "20241001_000000"),
        ("now-3Y", "UTC", "20211115_234907"),
        ("now/d", "America/New_York", "20241115_000000"),
        ("now/M", "UTC", "20241101_000000"),
        ("now/Y", "America/New_York", "20240101_000000"),
    ],
)
def test_parse_shorthand_datetime_with_timezone(datestr, tz, expected):
    """Test parse_shorthand_datetime with various inputs and timezones"""
    from shorthand_datetime.shorthand import parse_shorthand_datetime
    with mock.patch("datetime.datetime", mydatetime):
        dt = parse_shorthand_datetime(datestr, tz)
        assert dt.strftime("%Y%m%d_%H%M%S") == expected


    @pytest.mark.parametrize(
        "datestr",
        [
            "now-6d/d/d",
            "now-1W/W",
            "now-2M/M/M",
            "now-1M/M/M",
            "now-3Y/Y/Y",
            "now/d/d",
            "now/M/M",
            "now/Y/Y",
        ],
    )
    def test_parse_shorthand_datetime_invalid(datestr):
        """Test parse_shorthand_datetime with invalid inputs"""
        from shorthand_datetime.shorthand import parse_shorthand_datetime

        with mock.patch("datetime.datetime", mydatetime):
            dt = parse_shorthand_datetime(datestr)
            assert dt is None


    @pytest.mark.parametrize(
        "datestr, expected",
        [
            ("now+1d", "20241116_170555"),
            ("now+7d", "20241122_170555"),
            ("now+1W", "20241122_170555"),
            ("now+1M", "20241215_170555"),
            ("now+1Y", "20251115_170555"),
            ("now-1d", "20241114_170555"),
            ("now-7d", "20241108_170555"),
            ("now-1W", "20241108_170555"),
            ("now-1M", "20241015_170555"),
            ("now-1Y", "20231115_170555"),
        ],
    )
    def test_parse_shorthand_datetime_relative(datestr, expected):
        """Test parse_shorthand_datetime with relative inputs"""
        from shorthand_datetime.shorthand import parse_shorthand_datetime

        with mock.patch("datetime.datetime", mydatetime):
            dt = parse_shorthand_datetime(datestr)
            assert dt.strftime("%Y%m%d_%H%M%S") == expected


@pytest.mark.parametrize(
    "datestr, expected_tz",
    [
        ('now "UTC"', "UTC"),
        ("now 'America/New_York'", "America/New_York"),
        ('now-6d/d "Europe/London"', "Europe/London"),
        ("now-1W 'Asia/Tokyo'", "Asia/Tokyo"),
        ('now-2M "Australia/Sydney"', "Australia/Sydney"),
        ("now-1M/M 'Europe/Berlin'", "Europe/Berlin"),
        ('now-3Y "America/Los_Angeles"', "America/Los_Angeles"),
        ("now 'UTC' - 1d", "UTC"),
        ("now 'America/New_York' - 1d", "America/New_York"),
    ],
)
def test_parse_shorthand_datetime_with_quoted_timezone(datestr, expected_tz):
    """Test parse_shorthand_datetime with quoted timezone"""
    from shorthand_datetime.shorthand import parse_shorthand_datetime, _get_timezone

    with mock.patch("datetime.datetime", mydatetime):
        dt = parse_shorthand_datetime(datestr)
        assert str(dt.tzinfo) == expected_tz


def test_warning_timezone_passed_twice():
    """Test the warning when the timezone is passed as an argument and in the date string"""
    from shorthand_datetime.shorthand import parse_shorthand_datetime

    with mock.patch("datetime.datetime", mydatetime):
        with pytest.warns(UserWarning):
            dt = parse_shorthand_datetime('now-6d/d "UTC"', "America/New_York")
            assert dt.strftime("%Y%m%d_%H%M%S") == "20241109_000000"