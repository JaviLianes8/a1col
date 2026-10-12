"""``parse_ref``: one front door for every kind of A1 reference."""

from __future__ import annotations

from ._cell import CellRef
from ._errors import InvalidReferenceError
from ._limits import SheetLimits
from ._range import RangeRef
from ._sheet import split_sheet
from ._spans import ColumnSpan, RowSpan
from ._tokens import is_column_token, is_row_token

AnyRef = CellRef | RangeRef | ColumnSpan | RowSpan
"""Any reference ``parse_ref`` can return."""


def parse_ref(text: str, *, limits: SheetLimits | None = None) -> AnyRef:
    """Parse any A1 reference and return the matching type.

    * ``"B3"``, ``"$B$3"``, ``"Sheet1!B3"`` give a :class:`CellRef`.
    * ``"A1:C3"`` gives a :class:`RangeRef` (corners kept as written).
    * ``"A:C"`` gives a :class:`ColumnSpan` and ``"1:3"`` a :class:`RowSpan`.

    Raises:
        InvalidReferenceError: the text matches none of these forms, mixes forms
            (``A1:C``), or has a malformed sheet prefix.
        OutOfBoundsError: a column or row lies outside ``limits``.
    """
    _, body = split_sheet(text)
    if ":" not in body:
        return CellRef.parse(text, limits=limits)
    first, _, last = body.partition(":")
    if is_column_token(first) and is_column_token(last):
        return ColumnSpan.parse(text, limits=limits)
    if is_row_token(first) and is_row_token(last):
        return RowSpan.parse(text, limits=limits)
    if ":" in last:
        raise InvalidReferenceError(f"a range has at most one ':': {text!r}")
    return RangeRef.parse(text, limits=limits)
