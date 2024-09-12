import pytest
import shorthand_datetime
from hypothesis import given, settings, strategies as st
import datetime
from unittest import mock
from typing import Optional

FAKE_TIME: datetime.datetime = datetime.datetime(2021, 11, 15, 17, 5, 55)

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
        return FAKE_TIME.astimezone(tz) if tz else FAKE_TIME

def generate_shorthand(min_value: int=-699, max_value: int=662) -> st.SearchStrategy:
    """Generate shorthand expressions dynamically"""
    time_unit = st.sampled_from(['d', 'M', 'Y'])  # days, months, years
    # -- Works until 698 months (58 years) in the future because of the
    #    approximation in the calculation of months from weeks
    amount = st.integers(min_value=min_value, max_value=max_value)  # random integer
    return st.builds(lambda u, a: f"now{a:+d}{u}", time_unit, amount)

def generate_rounded_shorthand() -> st.SearchStrategy:
    """Generate rounded shorthand expressions (e.g., now/d, now/M, now/Y)"""
    time_unit = st.sampled_from(['d', 'M', 'Y'])
    return st.builds(lambda u: f"now/{u}", time_unit)

@given(shorthand=generate_shorthand())
@settings(max_examples=2000)
def test_shorthand(shorthand: str):
    """Test the shorthand parsing with dynamically generated inputs"""
    from shorthand_datetime.shorthand import parse_shorthand_datetime
    def get_delta(shorthand: str) -> float:
        """Extract the delta from the shorthand string"""
        return float(shorthand.split('-')[1][:-1]) if '-' in shorthand else float(shorthand.split('+')[1][:-1])
    # Apply the patch inside the test so it resets for every hypothesis example
    with mock.patch('datetime.datetime', mydatetime):
        dt: Optional[datetime.datetime] = parse_shorthand_datetime(shorthand)
        if dt is None:
            pytest.fail(f"parse_shorthand_datetime returned None for shorthand: {shorthand}")
        
        delta = get_delta(shorthand)
        # We won't know the exact output since we're generating floats, but we can check the delta
        if 'd' in shorthand:
            # Extract the number of days from the shorthand string
            actual_delta = abs(mydatetime.now() - dt).total_seconds() / (24 * 60 * 60)
        elif 'M' in shorthand:
            # For months, we approximate by comparing the difference in months
            actual_delta = abs((mydatetime.now().year - dt.year) * 12 + mydatetime.now().month - dt.month)
        elif 'Y' in shorthand:
            # For years, we compare the difference in years
            actual_delta = abs(mydatetime.now().year - dt.year)
        
        assert abs(actual_delta - delta) < 1e-1
        if '+' in shorthand:
            assert dt >= mydatetime.now()
        elif '-' in shorthand:
            assert dt <= mydatetime.now()


@given(shorthand=generate_shorthand(min_value=-1000, max_value=-700))
@settings(max_examples=400)
def test_shorthand_failure_1(shorthand: str):
    """Test the shorthand parsing with dynamically generated inputs.
    Expect a ValueError when the value is out of range for large negative values
    of months."""
    from shorthand_datetime.shorthand import parse_shorthand_datetime
    if 'M' in shorthand:
        with pytest.raises(ValueError):
            parse_shorthand_datetime(shorthand)


@settings(max_examples=500)
@given(shorthand=generate_shorthand(min_value=663, max_value=1000))
def test_shorthand_failure_2(shorthand: str):
    """Test the shorthand parsing with dynamically generated inputs.
    Expect a ValueError when the value is out of range for large positive values
    of months."""
    from shorthand_datetime.shorthand import parse_shorthand_datetime
    if 'M' in shorthand:
        with pytest.raises(ValueError):
            parse_shorthand_datetime(shorthand)

@given(shorthand=generate_rounded_shorthand())
def test_rounded_shorthand(shorthand: str):
    """Test the shorthand with rounding (e.g., "now/d", "now/M", "now/Y")"""
    from shorthand_datetime.shorthand import parse_shorthand_datetime
    
    # Apply the patch inside the test so it resets for every hypothesis example
    with mock.patch('datetime.datetime', mydatetime):
        dt: Optional[datetime.datetime] = parse_shorthand_datetime(shorthand)
        if dt is None:
            pytest.fail(f"parse_shorthand_datetime returned None for shorthand: {shorthand}")
        
        if '/d' in shorthand:
            # Check if the time is rounded to the start of the day (no hour, minute, second)
            assert dt.hour == 0 and dt.minute == 0 and dt.second == 0
        elif '/M' in shorthand:
            # Check if the date is rounded to the start of the month (day=1, no hour, minute, second)
            assert dt.day == 1 and dt.hour == 0 and dt.minute == 0 and dt.second == 0
        elif '/Y' in shorthand:
            # Check if the date is rounded to the start of the year (month=1, day=1, no hour, minute, second)
            assert dt.month == 1 and dt.day == 1 and dt.hour == 0 and dt.minute == 0 and dt.second == 0
