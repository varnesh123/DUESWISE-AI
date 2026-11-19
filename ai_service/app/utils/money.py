"""Money formatting helpers.

Amounts are integer paise everywhere. Formatting never performs financial
calculation and never introduces floating point arithmetic.
"""

from __future__ import annotations


def format_inr(paise: int) -> str:
    """Format integer paise using Indian digit grouping, e.g. 1200000 -> ₹12,000."""

    if paise < 0:
        raise ValueError("paise must be non-negative")
    rupees, remainder = divmod(int(paise), 100)
    whole = str(rupees)
    if len(whole) > 3:
        head, tail = whole[:-3], whole[-3:]
        groups: list[str] = []
        while len(head) > 2:
            groups.insert(0, head[-2:])
            head = head[:-2]
        if head:
            groups.insert(0, head)
        whole = ",".join([*groups, tail])
    if remainder:
        return f"₹{whole}.{remainder:02d}"
    return f"₹{whole}"
