# -*- coding: utf-8 -*-
"""Parse shorthand datetime strings inspired by Grafana. Main module"""


from __future__ import annotations

import datetime
import re
from typing import Optional, Union


def _roundtimestamp(dt: datetime.datetime, target: str) -> datetime.datetime:
    """
    Rounds a timestamp to the day

    Parameters
    ----------
    dt : datetime.datetime
        The timestamp to round
    target : str
        The target to round to. Can be 'd', 'M' or 'Y'

    Returns
    -------
    datetime.datetime
        The rounded timestamp

    Raises
    ------
    ValueError
        If the target is not 'd', 'M' or 'Y'

    Examples
    --------
    >>> _roundtimestamp(datetime.datetime(2024, 7, 21, 12, 30), 'd')
    datetime.datetime(2024, 7, 21, 0, 0)
    >>> _roundtimestamp(datetime.datetime(2024, 7, 21, 12, 30), 'M')
    datetime.datetime(2024, 7, 1, 0, 0)
    >>> _roundtimestamp(datetime.datetime(2024, 7, 21, 12, 30), 'Y')
    datetime.datetime(2024, 1, 1, 0, 0)
    """
    if target == "d":
        return dt.replace(hour=0, minute=0, second=0, microsecond=0)
    elif target == "M":
        return dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    elif target == "Y":
        return dt.replace(day=1, month=1, hour=0, minute=0, second=0, microsecond=0)
    raise ValueError(f"Invalid target '{target}'. Must be 'd', 'M' or 'Y'")


def _timedelta(value: Union[int, float, str], unit: str) -> datetime.timedelta:
    """
    Returns the timedelta object for the given value and unit

    Parameters
    ----------
    value : Union[int, float, str]
        The value to convert to a timedelta
    unit : str
        The unit of the value. Can be 'd', 'W', 'M' or 'Y'

    Returns
    -------
    datetime.timedelta
        The timedelta object

    Raises
    ------
    ValueError
        If the unit is not 'd', 'W', 'M' or 'Y' or if the value is out of range
        for 'M'

    Examples
    --------
    >>> _timedelta(5, 'd')
    datetime.timedelta(days=5)
    >>> _timedelta(3, 'W')
    datetime.timedelta(days=21)
    >>> _timedelta(2, 'M')
    datetime.timedelta(days=60, seconds=72002, microseconds=304000)
    >>> _timedelta(1, 'Y')
    datetime.timedelta(days=365, seconds=20952)
    """
    if unit == "d":
        return datetime.timedelta(days=int(value))
    elif unit == "W":
        return datetime.timedelta(weeks=int(value))
    elif unit == "M":
        if int(value) >= 601 or int(value) <= -601:
            raise ValueError(f"Value out of range. Please enter a value between -600 and 600. Value entered: {value}")
        return datetime.timedelta(weeks=int(value) * 4.34524)
    elif unit == "Y":
        return datetime.timedelta(weeks=int(value) * 52.1775)
    else:
        raise ValueError(f"Invalid unit '{unit}'. Must be 'd', 'W', 'M' or 'Y'")


def parse_shorthand_datetime(datestr: str) -> Optional[datetime.datetime]:
    """Parse a shorthand datetime string and return a datetime object. By
    shorthand datetime string we mean a string that can be used to represent
    a datetime in a more human readable way. This function is inspired by
    Grafana's datetime input. Typical examples are:

    - 'now-6d/d' : 6 days ago rounded to the day
    - 'now-1W' : 1 week ago
    - 'now-2M' : 2 months ago
    - 'now-1M/M' : 1 month ago rounded to the month
    - 'now-3Y' : 3 years ago
    - 'now' : current datetime
    - 'now/d' : current datetime rounded to the day
    - 'now/M' : current datetime rounded to the month

    .. note:: The function discards any spaces in the input string, therefore
              'now - 6d / d' is equivalent to 'now-6d/d'

    Parameters
    ----------
    datestr : str
        The shorthand datetime string

    Returns
    -------
    Union[datetime.datetime, None]
        The datetime object if the string can be parsed, None otherwise

    Examples
    --------
    >>> # Suppose today is 2024-07-21 12:30
    >>> parse_shorthand_datetime('now-6d/d')
    datetime.datetime(2024, 7, 15, 0, 0)
    >>> parse_shorthand_datetime('now-1W')
    datetime.datetime(2024, 7, 14, 12, 30)
    >>> parse_shorthand_datetime('now-2M')
    datetime.datetime(2024, 5, 21, 12, 30)
    >>> parse_shorthand_datetime('now-1M/M')
    datetime.datetime(2024, 6, 1, 0, 0)
    """

    datestr = datestr.replace(" ", "")  # Remove linebreaks

    if not datestr.startswith("now"):
        return None

    if datestr == "now":
        return datetime.datetime.now()

    # Relative datetime string in relation to current day
    value = re.findall(r"[-+]?[.]?[\d]+(?:,\d\d\d)*[\.]?\d*(?:[eE][-+]?\d+)?", datestr)
    if not value:
        value = [0]

    unit = re.findall("[dWMY]", datestr)

    dt = datetime.datetime.now() + _timedelta(value[0], unit[0])

    if "/" in datestr:
        return _roundtimestamp(dt, unit[-1])
    else:
        return dt
