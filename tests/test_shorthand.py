import pytest
import shorthand_datetime

import numpy as np

import datetime

FAKE_TIME = datetime.datetime(2024, 11, 15, 17, 5, 55)

@pytest.fixture
def patch_datetime_now(monkeypatch):

    class mydatetime(datetime.datetime):
        @classmethod
        def now(cls):
            return FAKE_TIME

    monkeypatch.setattr(datetime, 'datetime', mydatetime)

# Pytest will discover and run all test functions named `test_*` or `*_test`.

def test_version():
    """ check sdypy_template_project exposes a version attribute """
    assert hasattr(shorthand_datetime, "__version__")
    assert isinstance(shorthand_datetime.__version__, str)

def test_patch_datetime(patch_datetime_now):
    assert datetime.datetime.now() == FAKE_TIME

def test_shorthand(patch_datetime_now):
    from shorthand_datetime.shorthand import parse_shorthand_datetime

    s = 'now-7d'
    dt_7d = parse_shorthand_datetime(s)
    assert dt_7d.strftime('%Y%m%d') == '20241108'

    s = 'now-1M'
    dt_M = parse_shorthand_datetime(s)
    assert dt_M.strftime('%Y%m%d') == '20241016'

    s = 'now-1Y'
    dt_y = parse_shorthand_datetime(s)
    assert dt_y.strftime('%Y%m%d') == '20231116'

def test_rounded_shorthand(patch_datetime_now):
    from shorthand_datetime.shorthand import parse_shorthand_datetime

    s = 'now/d'
    dt_d = parse_shorthand_datetime(s)
    assert dt_d.second == 0
    assert dt_d.strftime('%Y%m%d_%H%M%S') == '20241115_000000'

    s = 'now/M'
    dt_7d = parse_shorthand_datetime(s)
    assert dt_7d.strftime('%Y%m%d') == '20241101'

    s = 'now/Y'
    dt_7d = parse_shorthand_datetime(s)
    assert dt_7d.strftime('%Y%m%d') == '20240101'

    s = 'now-2Y/Y'
    dt_7d = parse_shorthand_datetime(s)
    assert dt_7d.strftime('%Y%m%d') == '20220101'

    s = 'now-1M/M'
    dt_7d = parse_shorthand_datetime(s)
    assert dt_7d.strftime('%Y%m%d') == '20241001'



