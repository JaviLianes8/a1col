"""Whole columns (``A:C``) and whole rows (``1:3``)."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, replace
from typing import ClassVar, TypeVar

from ._cell import CellRef, check_axis
from ._columns import index_to_column
from ._errors import InvalidReferenceError
from ._limits import EXCEL, SheetLimits
from ._range import RangeRef
from ._sheet import split_sheet, with_sheet_prefix
from ._tokens import Coord, axis_text, column_coord, is_column_token, is_row_token, row_coord


def _split_pair(text: str, kind: str) -> tuple[str | None, str, str]:
    sheet, body = split_sheet(text)
    parts = body.split(":")
    if len(parts) != 2:
        raise InvalidReferenceError(f"whole {kind} need the form first:last: {text!r}")
    return sheet, parts[0], parts[1]


_S = TypeVar("_S", bound="_Span")


@dataclass(frozen=True)
class _Span:
    first: int
    last: int
    first_absolute: bool = False
    last_absolute: bool = False
    sheet: str | None = None
    _axis: ClassVar[str] = "column"

    def __post_init__(self) -> None:
        object.__setattr__(self, "first", check_axis(self._axis, self.first, None))
        object.__setattr__(self, "last", check_axis(self._axis, self.last, None))
        if self.sheet is not None:
            with_sheet_prefix(self.sheet, "")

    @property
    def low(self) -> int:
        """The smaller of ``first`` and ``last``."""
        return min(self.first, self.last)

    @property
    def high(self) -> int:
        """The larger of ``first`` and ``last``."""
        return max(self.first, self.last)

    @property
    def count(self) -> int:
        """How many whole columns or rows the span covers."""
        return self.high - self.low + 1

    def _label(self, value: int, absolute: bool) -> str:
        return axis_text(value, absolute)

    def to_a1(self, *, include_sheet: bool = True) -> str:
        """Return ``first:last`` in A1 text, for example ``"$A:C"`` or ``"'Q1'!1:3"``."""
        body = f"{self._label(self.first, self.first_absolute)}:"
        body += self._label(self.last, self.last_absolute)
        return with_sheet_prefix(self.sheet if include_sheet else None, body)

    def __str__(self) -> str:
        return self.to_a1()

    def _same_sheet(self, cell: CellRef) -> bool:
        return self.sheet is None or cell.sheet is None or self.sheet == cell.sheet

    def _shift(self: _S, delta: int, only_relative: bool, limits: SheetLimits | None) -> _S:
        first = self.first + (0 if only_relative and self.first_absolute else delta)
        last = self.last + (0 if only_relative and self.last_absolute else delta)
        first, last = check_axis(self._axis, first, limits), check_axis(self._axis, last, limits)
        return replace(self, first=first, last=last)

    def to_r1c1(self, anchor: CellRef | None = None) -> str:
        """Return R1C1 text such as ``C1:C3`` or ``R[-1]``; relative bounds use ``anchor``.

        A span whose two bounds render the same is written once (``R2``, ``C[1]``).
        """
        from ._r1c1 import span_to_r1c1

        return span_to_r1c1(self, anchor)


@dataclass(frozen=True)
class ColumnSpan(_Span):
    """Whole columns, for example ``A:C`` or ``Sheet1!$B:$B``. Columns are one-based."""

    @classmethod
    def parse(cls, text: str, *, limits: SheetLimits | None = None) -> ColumnSpan:
        """Parse ``"A:C"``, ``"$B:$B"`` or ``"'My Sheet'!A:C"``.

        Raises:
            InvalidReferenceError: not two column tokens joined by ``:``.
            OutOfBoundsError: a column lies beyond ``limits``.
        """
        sheet, a, b = _split_pair(text, "columns")
        if not (is_column_token(a) and is_column_token(b)):
            raise InvalidReferenceError(f"not a whole-column reference: {text!r}")
        first: Coord = column_coord(a, limits)
        last: Coord = column_coord(b, limits)
        return cls(first.value, last.value, first.absolute, last.absolute, sheet)

    def _label(self, value: int, absolute: bool) -> str:
        return ("$" if absolute else "") + index_to_column(value)

    def __contains__(self, item: object) -> bool:
        return (
            isinstance(item, CellRef)
            and self._same_sheet(item)
            and (self.low <= item.column <= self.high)
        )

    def letters(self) -> Iterator[str]:
        """Yield the column letters from left to right."""
        for column in range(self.low, self.high + 1):
            yield index_to_column(column)

    def to_range(self, limits: SheetLimits = EXCEL) -> RangeRef:
        """Return the concrete block from row 1 to ``limits.max_rows`` (Excel by default).

        The corners come back relative: ``$A:$C`` gives ``A1:C1048576``.
        """
        limits.check_column(self.high)
        start = CellRef(self.low, 1, sheet=self.sheet)
        return RangeRef(start, CellRef(self.high, limits.max_rows, sheet=self.sheet))

    def offset(self, columns: int, *, limits: SheetLimits | None = None) -> ColumnSpan:
        """Move both bounds by ``columns``; raises ``OutOfBoundsError`` off the grid."""
        return self._shift(columns, False, limits)

    def translate(self, columns: int, *, limits: SheetLimits | None = None) -> ColumnSpan:
        """Move only the relative bounds by ``columns``, as copying a formula does."""
        return self._shift(columns, True, limits)


@dataclass(frozen=True)
class RowSpan(_Span):
    """Whole rows, for example ``1:3`` or ``Sheet1!$5:$5``. Rows are one-based."""

    _axis: ClassVar[str] = "row"

    @classmethod
    def parse(cls, text: str, *, limits: SheetLimits | None = None) -> RowSpan:
        """Parse ``"1:3"``, ``"$5:$5"`` or ``"'My Sheet'!1:3"``.

        Raises:
            InvalidReferenceError: not two row tokens joined by ``:``.
            OutOfBoundsError: a row lies beyond ``limits``.
        """
        sheet, a, b = _split_pair(text, "rows")
        if not (is_row_token(a) and is_row_token(b)):
            raise InvalidReferenceError(f"not a whole-row reference: {text!r}")
        first, last = row_coord(a, limits), row_coord(b, limits)
        return cls(first.value, last.value, first.absolute, last.absolute, sheet)

    def __contains__(self, item: object) -> bool:
        return (
            isinstance(item, CellRef)
            and self._same_sheet(item)
            and (self.low <= item.row <= self.high)
        )

    def to_range(self, limits: SheetLimits = EXCEL) -> RangeRef:
        """Return the concrete block from column A to ``limits.max_columns`` (Excel default).

        The corners come back relative: ``$1:$3`` gives ``A1:XFD3``.
        """
        limits.check_row(self.high)
        start = CellRef(1, self.low, sheet=self.sheet)
        return RangeRef(start, CellRef(limits.max_columns, self.high, sheet=self.sheet))

    def offset(self, rows: int, *, limits: SheetLimits | None = None) -> RowSpan:
        """Move both bounds by ``rows``; raises ``OutOfBoundsError`` off the grid."""
        return self._shift(rows, False, limits)

    def translate(self, rows: int, *, limits: SheetLimits | None = None) -> RowSpan:
        """Move only the relative bounds by ``rows``, as copying a formula does."""
        return self._shift(rows, True, limits)
