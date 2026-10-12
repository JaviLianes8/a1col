"""``RangeRef``: a rectangular block of cells such as ``A1:C3``."""

from __future__ import annotations

from dataclasses import dataclass, replace

from ._cell import CellRef, cell_from_body
from ._errors import InvalidReferenceError
from ._grid import GridMixin
from ._limits import SheetLimits
from ._sheet import split_sheet, with_sheet_prefix


@dataclass(frozen=True)
class RangeRef(GridMixin):
    """Two corner cells on the same sheet, for example ``A1:C3`` or ``'Q1'!$A$1:B2``.

    Corners are kept as written (``C3:A1`` stays ``C3:A1``); every geometric property
    uses the normalized bounds. ``len(rng)`` is the number of cells and iterating
    yields every cell row by row. The sheet lives on both corners and prints once.
    """

    start: CellRef
    end: CellRef

    def __post_init__(self) -> None:
        if self.start.sheet != self.end.sheet:
            raise InvalidReferenceError(
                f"range corners are on different sheets: {self.start.sheet!r}, {self.end.sheet!r}"
            )

    @classmethod
    def parse(cls, text: str, *, limits: SheetLimits | None = None) -> RangeRef:
        """Parse ``"A1:C3"``, ``"Sheet1!$A$1:B2"`` or a single cell ``"B2"`` (a 1x1 range).

        Raises:
            InvalidReferenceError: not a cell range (whole columns and rows such as
                ``A:C`` are ``ColumnSpan`` and ``RowSpan``), or more than one ``:``.
            OutOfBoundsError: a corner lies outside ``limits``.
        """
        sheet, body = split_sheet(text)
        parts = body.split(":")
        if len(parts) > 2:
            raise InvalidReferenceError(f"a range has at most one ':': {text!r}")
        start = cell_from_body(parts[0], sheet, limits, text)
        return cls(start, cell_from_body(parts[-1], sheet, limits, text))

    @classmethod
    def from_r1c1(
        cls, text: str, anchor: CellRef | None = None, *, limits: SheetLimits | None = None
    ) -> RangeRef:
        """Parse ``R1C1:R[2]C[2]``; relative parts are resolved against ``anchor``."""
        from ._r1c1 import range_from_r1c1

        return range_from_r1c1(text, anchor, limits)

    def normalized(self) -> RangeRef:
        """Return the same block with ``start`` top-left and ``end`` bottom-right.

        Each bound keeps the ``$`` marker of the corner it came from.
        """
        s, e = self.start, self.end
        left, right = (s, e) if s.column <= e.column else (e, s)
        top, bottom = (s, e) if s.row <= e.row else (e, s)
        start = CellRef(left.column, top.row, left.column_absolute, top.row_absolute, s.sheet)
        end = CellRef(right.column, bottom.row, right.column_absolute, bottom.row_absolute, s.sheet)
        return RangeRef(start, end)

    def _same_sheet(self, other: CellRef | RangeRef) -> bool:
        return self.sheet is None or other.sheet is None or self.sheet == other.sheet

    def __contains__(self, item: object) -> bool:
        if not isinstance(item, CellRef) or not self._same_sheet(item):
            return False
        return (
            self.min_column <= item.column <= self.max_column
            and self.min_row <= item.row <= self.max_row
        )

    def contains(self, other: CellRef | RangeRef) -> bool:
        """Return whether ``other`` lies entirely inside this range.

        Sheets are compared only when both sides name one; a missing sheet matches any.
        """
        if isinstance(other, CellRef):
            return other in self
        return (
            self._same_sheet(other)
            and self.min_column <= other.min_column
            and other.max_column <= self.max_column
            and self.min_row <= other.min_row
            and other.max_row <= self.max_row
        )

    def intersection(self, other: RangeRef) -> RangeRef | None:
        """Return the overlapping block (relative corners), or ``None`` when disjoint."""
        if not self._same_sheet(other):
            return None
        left, right = max(self.min_column, other.min_column), min(self.max_column, other.max_column)
        top, bottom = max(self.min_row, other.min_row), min(self.max_row, other.max_row)
        if left > right or top > bottom:
            return None
        sheet = self.sheet if self.sheet is not None else other.sheet
        return RangeRef(CellRef(left, top, sheet=sheet), CellRef(right, bottom, sheet=sheet))

    def overlaps(self, other: RangeRef) -> bool:
        """Return whether the two ranges share at least one cell."""
        return self.intersection(other) is not None

    def bounding_box(self, other: CellRef | RangeRef) -> RangeRef:
        """Return the smallest range (relative corners) covering both ``self`` and ``other``."""
        if not self._same_sheet(other):
            raise InvalidReferenceError("cannot bound references on different sheets")
        box = other if isinstance(other, RangeRef) else RangeRef(other, other)
        sheet = self.sheet if self.sheet is not None else box.sheet
        start = CellRef(min(self.min_column, box.min_column), min(self.min_row, box.min_row))
        end = CellRef(max(self.max_column, box.max_column), max(self.max_row, box.max_row))
        return RangeRef(start.with_sheet(sheet), end.with_sheet(sheet))

    def check(self, limits: SheetLimits | None) -> RangeRef:
        """Return ``self`` if both corners fit ``limits``, else raise ``OutOfBoundsError``."""
        self.start.check(limits)
        self.end.check(limits)
        return self

    def to_a1(self, *, include_sheet: bool = True) -> str:
        """Return ``start:end`` in A1 text with the sheet prefix written once."""
        body = f"{self.start.to_a1(include_sheet=False)}:{self.end.to_a1(include_sheet=False)}"
        return with_sheet_prefix(self.sheet if include_sheet else None, body)

    def __str__(self) -> str:
        return self.to_a1()

    def to_r1c1(self, anchor: CellRef | None = None) -> str:
        """Return ``start:end`` in R1C1; relative parts become offsets from ``anchor``."""
        from ._r1c1 import range_to_r1c1

        return range_to_r1c1(self, anchor)

    def with_sheet(self, sheet: str | None) -> RangeRef:
        """Return a copy with both corners qualified by ``sheet`` (``None`` removes it)."""
        return RangeRef(self.start.with_sheet(sheet), self.end.with_sheet(sheet))

    def offset(
        self, *, rows: int = 0, columns: int = 0, limits: SheetLimits | None = None
    ) -> RangeRef:
        """Move both corners by ``rows`` and ``columns``; raises if it leaves the grid."""
        start = self.start.offset(rows=rows, columns=columns, limits=limits)
        return replace(
            self, start=start, end=self.end.offset(rows=rows, columns=columns, limits=limits)
        )

    def translate(
        self, *, rows: int = 0, columns: int = 0, limits: SheetLimits | None = None
    ) -> RangeRef:
        """Shift only the relative parts of each corner, as copying a formula does."""
        start = self.start.translate(rows=rows, columns=columns, limits=limits)
        end = self.end.translate(rows=rows, columns=columns, limits=limits)
        return replace(self, start=start, end=end)
