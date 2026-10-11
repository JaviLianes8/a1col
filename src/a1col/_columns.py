"""Column-letter and one-based index conversions for A1 notation."""

from __future__ import annotations

_A = ord("A")
_ALPHABET = 26


def column_to_index(column: str) -> int:
    """Return the one-based index of a column (``"A"`` is ``1``, ``"AA"`` is ``27``).

    Letters are case-insensitive and a single leading absolute marker (``$``) is allowed.
    """
    letters = column[1:] if column.startswith("$") else column
    if not letters or not letters.isascii() or not letters.isalpha():
        raise ValueError(f"not a column reference: {column!r}")
    index = 0
    for char in letters.upper():
        index = index * _ALPHABET + (ord(char) - _A + 1)
    return index


def index_to_column(index: int) -> str:
    """Return the column letters for a one-based index (``1`` is ``"A"``, ``27`` is ``"AA"``)."""
    if index < 1:
        raise ValueError(f"column index must be >= 1, got {index}")
    letters = ""
    while index > 0:
        index, remainder = divmod(index - 1, _ALPHABET)
        letters = chr(_A + remainder) + letters
    return letters
