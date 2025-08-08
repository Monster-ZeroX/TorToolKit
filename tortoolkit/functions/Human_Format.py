"""Utility helpers for presenting human readable values.

This module previously contained several incomplete implementations which
resulted in syntax errors and missing features.  The helpers below now support
full conversion of bytes, time deltas and speeds to a compact textual format.
"""

from datetime import timedelta


def human_readable_bytes(value, digits=2, delim="", postfix=""):
    """Return a human-readable file size.

    Parameters
    ----------
    value: int
        Size in bytes.
    digits: int, optional
        Number of fractional digits to display.
    delim: str, optional
        Delimiter between the number and the unit.
    postfix: str, optional
        String to append after the unit.
    """
    if value is None:
        return None

    chosen_unit = "B"
    for unit in ("KiB", "MiB", "GiB", "TiB"):
        if value > 1000:
            value /= 1024
            chosen_unit = unit
        else:
            break
    return f"{value:.{digits}f}" + delim + chosen_unit + postfix


def human_readable_speed(value, digits=2, delim=""):
    """Return a human-readable speed string.

    This is a thin wrapper over :func:`human_readable_bytes` which simply adds
    a ``"/s"`` postfix to the converted value.
    """

    return human_readable_bytes(value, digits=digits, delim=delim, postfix="/s")


def human_readable_timedelta(seconds, precision=0):
    """Return a human-readable time delta as a string.

    Parameters
    ----------
    seconds: int
        Number of seconds for the time delta.
    precision: int, optional
        Limits the number of components in the returned string. ``0`` means no
        limit and therefore all components are shown.
    """

    pieces = []
    value = timedelta(seconds=int(seconds))

    if value.days:
        pieces.append(f"{value.days}d")

    seconds = value.seconds

    if seconds >= 3600:
        hours = seconds // 3600
        pieces.append(f"{hours}h")
        seconds -= hours * 3600

    if seconds >= 60:
        minutes = seconds // 60
        pieces.append(f"{minutes}m")
        seconds -= minutes * 60

    if seconds > 0 or not pieces:
        pieces.append(f"{seconds}s")

    if precision:
        return "".join(pieces[:precision])
    return "".join(pieces)
