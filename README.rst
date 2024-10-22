Shorthand datetime
-----------------------

Simple package to parse shorthand datetime strings in the `Elasticsearch date
math format <https://www.elastic.co/guide/en/elasticsearch/reference/current/common-options.html#date-math>`_.

Using the package
------------------

.. code-block:: python

    # Simplest usage example
    from shorthand_datetime.shorthand import parse_shorthand_datetime

    string = 'now-7d'
    dt = parse_shorthand_datetime(string)

.. code-block:: python

    # Example with freeze_time for testings
    from freezegun import freeze_time
    from shorthand_datetime import parse_shorthand_datetime

    @freeze_time("2023-10-25 12:21:45")
    def test_now():
        strings = ['now-7d', 'now/d', 'now-7d/d', 'now/M', 'now-1M/M',
                   'now-3W+6h', 'now-1M+1W/d']
        for string in strings:
            print(f'{string} -> {parse_shorthand_datetime(string)}')

    # Call the test and print the results
    test_now()

Output:

.. code-block:: shell

    now-7d -> 2023-10-18 12:21:45
    now/d -> 2023-10-25 00:00:00
    now-7d/d -> 2023-10-18 00:00:00
    now/M -> 2023-10-01 00:00:00
    now-1M/M -> 2023-09-01 00:00:00
    now-3W+6h -> 2023-10-04 18:21:45
    now-1M+1W/d -> 2023-10-02 00:00:00


Typical examples
----------------
- ``now-7d``: current timestamp minus 7 days
- ``now/d``: today, rounded to the start of the day
- ``now-7d/d``: 7 days ago, rounded to the start of the day
- ``now/M``: first day of this month
- ``now-1M/M``: first day of previous month
- ``now-3W+6h``: 3 weeks ago plus 6 hours
- ``now-1M+1W/d``: 1 month ago plus 1 week, rounded to the start of the day

Acknowledgements
----------------
© 2024 24SEA - Monitoring Offshore Structures. All rights reserved.
