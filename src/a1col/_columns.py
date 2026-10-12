"""Column-letter and index conversions for A1 notation, one-based and zero-based."""

from __future__ import annotations

import operator

from ._errors import InvalidColumnError, OutOfBoundsError
from ._limits import SheetLimits

_A = ord("A")
_ALPHABET = 26


def _letters(column: str) -> str:
    if not isinstance(column, str):
        raise TypeError(f"column must be a str, got {type(column).__name__}")
    letters = column[1:] if column.startswith("$") else column
    if not letters or not letters.isascii() or not letters.isalpha():
        raise InvalidColumnError(f"not a column reference: {column!r}")
    return letters


def _as_index(index: int, base: int) -> int:
    # operator.index keeps NumPy integers and other ``__index__`` types working.
    try:
        value = operator.index(index)
    except TypeError:
        raise TypeError(f"column index must be an int, got {type(index).__name__}") from None
    if value < base:
        raise OutOfBoundsError(f"column index must be >= {base}, got {value}")
    return value


def is_column(text: str) -> bool:
    """Return whether ``text`` is valid column letters, with an optional leading ``$``.

    Never raises: anything that is not a string, or not ASCII letters, is ``False``.
    """
    try:
        _letters(text)
    except (InvalidColumnError, TypeError):
        return False
    return True


def column_to_index(column: str, *, limits: SheetLimits | None = None) -> int:
    """Return the one-based index of a column (``"A"`` is ``1``, ``"AA"`` is ``27``).

    Letters are case-insensitive and a single leading absolute marker (``$``) is allowed.
    With ``limits`` the result must also fit that application's grid.

    Raises:
        InvalidColumnError: the text is empty, a lone ``$``, or not ASCII letters.
        OutOfBoundsError: the column lies beyond ``limits.max_columns``.
    """
    index = 0
    for char in _letters(column).upper():
        index = index * _ALPHABET + (ord(char) - _A + 1)
    if limits is not None:
        limits.check_column(index)
    return index


def index_to_column(index: int, *, limits: SheetLimits | None = None) -> str:
    """Return the column letters for a one-based index (``1`` is ``"A"``, ``27`` is ``"AA"``).

    Any integer type works, NumPy integers included (anything with ``__index__``).

    Raises:
        OutOfBoundsError: the index is below one, or beyond ``limits.max_columns``.
    """
    index = _as_index(index, 1)
    if limits is not None:
        limits.check_column(index)
    letters = ""
    while index > 0:
        index, remainder = divmod(index - 1, _ALPHABET)
        letters = chr(_A + remainder) + letters
    return letters


def column_to_index0(column: str, *, limits: SheetLimits | None = None) -> int:
    """Return the zero-based index of a column (``"A"`` is ``0``, ``"AA"`` is ``26``).

    Same rules and errors as :func:`column_to_index`, shifted down by one.
    """
    return column_to_index(column, limits=limits) - 1


def index0_to_column(index: int, *, limits: SheetLimits | None = None) -> str:
    """Return the column letters for a zero-based index (``0`` is ``"A"``, ``26`` is ``"AA"``).

    Raises:
        OutOfBoundsError: the index is negative, or beyond the grid of ``limits``.
    """
    return index_to_column(_as_index(index, 0) + 1, limits=limits)
