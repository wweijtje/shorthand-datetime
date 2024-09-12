# -*- coding: utf-8 -*-
"""
This module exposes the current version of the package
so the version can be retreived directly within other code
files. The version assumes the semver notation (major.minor.patch-release.num).

Example:
    Import the version as constant, dict or tuple:

    >>> from shorthand_datetime.version import __version__

    >>> from shorthand_datetime.version import parse_version
    >>> parse_version(__version__)

Attributes:
    __version__ (str): Current shorthand_datetime version.

"""
import re
from typing import NamedTuple, Optional

__version__: str = "0.1.1"

_REGEX = "".join(
    [
        r"(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)",
        r"(?:\-(?P<release>.*)\.(?P<num>\d+))?",
    ]
)


class Version(NamedTuple):
    """Convenience structure for interpreting the version information"""

    major: int
    minor: int
    patch: int
    release: Optional[str] = None
    num: Optional[int] = None


def parse_version(version: str) -> Version:
    """Converts the given version string to a named tuple per the semantic
    version guidelines"""
    match = re.search(_REGEX, version)
    if not match:
        raise ValueError(f"Version '{version}' does not comply with the semantic" "versioning naming scheme")

    major = int(match.group("major"))
    minor = int(match.group("minor"))
    patch = int(match.group("patch"))
    release = match.group("release")

    num = None  # type: Optional[int]
    try:
        num = int(match.group("num"))
    except TypeError:
        pass

    return Version(
        major=major,
        minor=minor,
        patch=patch,
        release=release,
        num=num,
    )