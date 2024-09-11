#   ---------------------------------------------------------------------------------
#   Copyright (c) Microsoft Corporation. All rights reserved.
#   Licensed under the MIT License. See LICENSE in project root for information.
#   ---------------------------------------------------------------------------------
"""This is a Sample Python file."""


from __future__ import annotations
import re
import datetime
from typing import Union

def _roundtimestamp(dt:datetime.datetime, target) -> datetime.datetime:
    """
    Rounds a timestamp to the day
    """
    if target == 'd':
        return dt.replace(hour=0, minute=0, second=0, microsecond=0)
    elif target == 'M':
        return dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    elif target == 'Y':
        return dt.replace(day=1, month=1, hour=0, minute=0, second=0, microsecond=0)


def _timedelta(value, unit) -> datetime.timedelta:
    """
    Returns the timedelta object for the given value and unit
    """

    if unit == "d":
        return datetime.timedelta(days=int(value))
    elif unit == "W":
        return datetime.timedelta(weeks=int(value))
    elif unit == "M":
        return datetime.timedelta(weeks=int(value) * 4.34524)
    elif unit == "Y":
        return datetime.timedelta(weeks=int(value) * 52.1775)
    else:
        raise ValueError(f"Invalid unit '{unit}'")


def parse_shorthand_datetime(datestr:str) -> Union[datetime.datetime, None]:

    if 'now' in datestr:
        # Relative datetime string in relation to current day
        datestr = datestr.replace(' ','') # Remove linebreaks
        value = re.findall("[-+]?[.]?[\d]+(?:,\d\d\d)*[\.]?\d*(?:[eE][-+]?\d+)?", datestr)
        if not value:
            value = [0]

        unit = re.findall("[dWMY]", datestr)

        dt = datetime.datetime.now() + _timedelta(value[0], unit[0])

        if '/' in datestr:
            return _roundtimestamp(dt, unit[-1])
        else:
            return dt

    else:
        return None



