Shorthand datetime
-----------------------

Simple package to parse shorthand datetime strings

Using the package
------------------

    .. code-block:: python

        from shorthand_datetime.shorthand import parse_shorthand_datetime

        s = 'now-7d'
        dt = parse_shorthand_datetime(s)

Typical examples
----------------
- now-7d : current timestamp minus 7d
- now/d : today, rounded to the start of the day
- now-7d/d: 7 days ago, rounded to the start of the day
- now/M : first day of this month
- now-1M/M : first day of previous month

Acknowledgements
----------------
