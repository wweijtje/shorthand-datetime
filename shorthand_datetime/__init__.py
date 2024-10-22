# -*- coding: utf-8 -*-
"""Parse shorthand datetime strings in the Elasticsearch date math format. Inspired by Grafana."""

from .shorthand import parse_shorthand_datetime as parse_shorthand_datetime
from .version import __version__ as __version__  # noqa: F401
