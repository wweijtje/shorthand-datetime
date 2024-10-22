# -*- coding: utf-8 -*-
"""Parse shorthand datetime strings inspired by Grafana. Main module"""


from __future__ import annotations

import datetime
import logging
import re
from typing import Optional, Union

# Configure logging
logging.basicConfig(format="%(message)s", level=logging.DEBUG)


def _roundtimestamp(dt: datetime.datetime, target: str) -> datetime.datetime:
    """
    Rounds a timestamp to the day

    Parameters
    ----------
    dt : datetime.datetime
        The timestamp to round
    target : str
        The target to round to. Can be 's', 'm', 'h', 'H', 'd', 'W', 'M' or 'Y'

    Returns
    -------
    datetime.datetime
        The rounded timestamp

    Raises
    ------
    ValueError
        If the target is not 's', 'm', 'h', 'H', 'd', 'W', 'M' or 'Y'

    Examples
    --------
    >>> _roundtimestamp(datetime.datetime(2024, 7, 21, 12, 30), 'd')
    datetime.datetime(2024, 7, 21, 0, 0)
    >>> _roundtimestamp(datetime.datetime(2024, 7, 21, 12, 30), 'M')
    datetime.datetime(2024, 7, 1, 0, 0)
    >>> _roundtimestamp(datetime.datetime(2024, 7, 21, 12, 30), 'Y')
    datetime.datetime(2024, 1, 1, 0, 0)
    """

    if target == "s":
        return dt.replace(microsecond=0)
    elif target == "m":
        return dt.replace(second=0, microsecond=0)
    elif target in ["h", "H"]:
        return dt.replace(minute=0, second=0, microsecond=0)
    elif target == "d":
        return dt.replace(hour=0, minute=0, second=0, microsecond=0)
    elif target == "W":
        return dt.replace(hour=0, minute=0, second=0, microsecond=0) - datetime.timedelta(days=dt.weekday())
    elif target == "M":
        return dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    elif target == "Y":
        return dt.replace(day=1, month=1, hour=0, minute=0, second=0, microsecond=0)

    raise ValueError(f"Invalid target '{target}'. " "Must be 's', 'm', 'h', 'H', 'd', 'W', 'M' or 'Y'")


def _timedelta(value: Union[int, float, str], unit: str) -> datetime.timedelta:
    """
    Returns the timedelta object for the given value and unit

    Parameters
    ----------
    value : Union[int, float, str]
        The value to convert to a timedelta
    unit : str
        The unit of the value. Can be 's', 'm', 'h', 'H', 'd', 'W', 'M' or 'Y'

    Returns
    -------
    datetime.timedelta
        The timedelta object

    Raises
    ------
    ValueError
        If the unit is not 's', 'm', 'h', 'H', 'd', 'W', 'M' or 'Y' or if the
        value is out of range for 'M' or 'Y'

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
    if unit == "s":
        return datetime.timedelta(seconds=int(value))
    elif unit == "m":
        return datetime.timedelta(minutes=int(value))
    elif unit in ["h", "H"]:
        return datetime.timedelta(hours=int(value))
    elif unit == "d":
        return datetime.timedelta(days=int(value))
    elif unit == "W":
        return datetime.timedelta(weeks=int(value))
    elif unit == "M":
        if int(value) >= 601 or int(value) <= -601:
            raise ValueError(f"Value out of range. Please enter a value between -600 and 600. Value entered: {value}")
        return datetime.timedelta(weeks=int(value) * 4.34524)
    elif unit == "Y":
        return datetime.timedelta(weeks=int(value) * 52.177142857142854)
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

    valid_targets = ["s", "m", "h", "H", "d", "W", "M", "Y"]

    dt = datetime.datetime.now()

    if datestr == "now":
        return dt

    datestr = datestr.replace(" ", "")  # Remove linebreaks
    # Check if there are more than 1 "/" in the string
    if datestr.count("/") > 1:
        logging.warning("Invalid date string. Only one '/' is allowed")
        return None

    # Check that "/", if there, is always the second to last character,
    # and it is followed by a valid target
    if "/" in datestr:
        if datestr[-1] == "/":
            logging.warning("Invalid date string. '/' must be followed by a " "valid target")
            return None
        if datestr[-2] != "/":
            logging.warning("Invalid date string. '/' must be second to last " "character")
            return None
        if datestr[-1] not in valid_targets:
            logging.warning("Invalid date string. '/' must be followed by a " "valid target")
            return None

    target = None
    if "/" in datestr:
        target = [datestr.split("/")[1][0]]

        # Strip the target and the "/" from the datestr
        datestr = datestr.split("/")[0]

    if not datestr.startswith("now"):
        if datestr.startswith(("-", "+")):
            datestr = "now" + datestr
        else:
            return None

    # Relative datetime string in relation to current day
    value = re.findall(r"[-+]?[.]?[\d]+(?:,\d\d\d)*[\.]?\d*(?:[eE][-+]?\d+)?|[-+](?=[smhHdWMY])", datestr)

    if not value:
        value = [1]
    if any(v in ("-", "+") for v in value):
        value = [1] if value[0] == "+" else [-1]
    if not isinstance(value, list):
        value = [value]

    unit = re.findall("[smhHdWMY]", datestr)
    if not isinstance(unit, list):
        unit = [unit]

    timedelta_list = [_timedelta(int(v), u) for v, u in zip(value, unit)]
    total_timedelta = sum(timedelta_list, datetime.timedelta())
    dt = dt + total_timedelta

    if target is not None:
        dt = _roundtimestamp(dt, target[0])

    return dt
