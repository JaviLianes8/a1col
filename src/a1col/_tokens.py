"""Lexing of the pieces of an A1 reference: column token, row token, cell token."""

from __future__ import annotations

import re
from typing import NamedTuple

from ._columns import column_to_index
from ._errors import A1Error, InvalidReferenceError, InvalidRowError
from ._limits import SheetLimits

_CELL = re.compile(r"(\$?)([A-Za-z]+)(\$?)([0-9]+)", re.ASCII)
_COLUMN = re.compile(r"\$?[A-Za-z]+", re.ASCII)
_ROW = re.compile(r"\$?[0-9]+", re.ASCII)


class Coord(NamedTuple):
    """One axis value of a reference with its absolute marker."""

    value: int
    absolute: bool


def row_number(text: str, *, limits: SheetLimits | None = None) -> int:
    """Return the row number written as ``text`` (``"12"`` is ``12``).

    Rows are ASCII digits without a sign, without leading zeros and at least ``1``.

    Raises:
        InvalidRowError: empty, non-digit, ``0``, or with a leading zero.
        OutOfBoundsError: beyond ``limits.max_rows``.
    """
    if not text or not text.isascii() or not text.isdigit():
        raise InvalidRowError(f"not a row number: {text!r}")
    if text[0] == "0":
        raise InvalidRowError(f"row numbers start at 1 and have no leading zeros: {text!r}")
    row = int(text)
    if limits is not None:
        limits.check_row(row)
    return row


def is_column_token(text: str) -> bool:
    return _COLUMN.fullmatch(text) is not None


def is_row_token(text: str) -> bool:
    return _ROW.fullmatch(text) is not None


def column_coord(text: str, limits: SheetLimits | None) -> Coord:
    """Lex ``$C`` or ``C`` into a column ``Coord``."""
    return Coord(column_to_index(text, limits=limits), text.startswith("$"))


def row_coord(text: str, limits: SheetLimits | None) -> Coord:
    """Lex ``$3`` or ``3`` into a row ``Coord``."""
    absolute = text.startswith("$")
    return Coord(row_number(text[1:] if absolute else text, limits=limits), absolute)


def cell_coords(
    text: str, limits: SheetLimits | None, context: str | None = None
) -> tuple[Coord, Coord]:
    """Lex ``$B$3`` into ``(column, row)`` coordinates.

    ``context`` is the full reference ``text`` came from, quoted in error messages.

    Raises:
        InvalidReferenceError: the text is not a single A1 cell.
    """
    where = "" if context is None or context == text else f" in {context!r}"
    match = _CELL.fullmatch(text)
    if match is None:
        raise InvalidReferenceError(f"not an A1 cell reference: {text!r}{where}")
    col_mark, letters, row_mark, digits = match.groups()
    try:
        column = Coord(column_to_index(letters, limits=limits), col_mark == "$")
        row = Coord(row_number(digits, limits=limits), row_mark == "$")
    except A1Error as exc:
        raise type(exc)(f"{exc}{where}") from None
    return column, row


def axis_text(value: int, absolute: bool) -> str:
    """Render one row coordinate, for example ``$3``."""
    return f"{'$' if absolute else ''}{value}"
