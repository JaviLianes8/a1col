"""``CellRef``: one cell in A1 notation."""

from __future__ import annotations

import operator
from dataclasses import dataclass, replace

from ._columns import index_to_column
from ._errors import OutOfBoundsError
from ._limits import SheetLimits
from ._sheet import split_sheet, with_sheet_prefix
from ._tokens import axis_text, cell_coords


def as_int(name: str, value: int) -> int:
    """Return ``value`` as a plain int (NumPy integers welcome); ``bool`` is refused."""
    if isinstance(value, bool):
        raise TypeError(f"{name} must be an int, got bool")
    try:
        return operator.index(value)
    except TypeError:
        raise TypeError(f"{name} must be an int, got {type(value).__name__}") from None


def check_axis(name: str, value: int, limits: SheetLimits | None) -> int:
    """Validate a one-based axis value and return it as a plain int."""
    value = as_int(name, value)
    if value < 1:
        raise OutOfBoundsError(f"{name} must be >= 1, got {value}")
    if limits is not None:
        (limits.check_column if name == "column" else limits.check_row)(value)
    return value


def cell_from_body(
    body: str, sheet: str | None, limits: SheetLimits | None, context: str
) -> CellRef:
    """Build a ``CellRef`` from A1 text without a sheet prefix; errors quote ``context``."""
    column, row = cell_coords(body, limits, context)
    return CellRef(column.value, row.value, column.absolute, row.absolute, sheet)


@dataclass(frozen=True)
class CellRef:
    """A single cell such as ``B3``, ``$B$3`` or ``'My Sheet'!B3``.

    ``column`` and ``row`` are one-based (``A1`` is column 1, row 1). The two flags
    record the ``$`` markers, and ``sheet`` holds the unquoted sheet name or ``None``.
    ``str(cell)`` gives canonical A1 text: upper-case letters, quoting only as needed.
    """

    column: int
    row: int
    column_absolute: bool = False
    row_absolute: bool = False
    sheet: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "column", check_axis("column", self.column, None))
        object.__setattr__(self, "row", check_axis("row", self.row, None))
        if self.sheet is not None:
            with_sheet_prefix(self.sheet, "")

    @classmethod
    def parse(cls, text: str, *, limits: SheetLimits | None = None) -> CellRef:
        """Parse ``"B3"``, ``"$B$3"``, ``"b$3"`` or ``"'Q1 ''24'!B3"`` into a ``CellRef``.

        Letters are case-insensitive. Rows have no sign and no leading zeros.

        Raises:
            InvalidReferenceError: not a single A1 cell, or a malformed sheet prefix.
            OutOfBoundsError: the cell lies outside ``limits``.
        """
        sheet, body = split_sheet(text)
        return cell_from_body(body, sheet, limits, text)

    @classmethod
    def from_zero_based(
        cls, *, column: int, row: int, sheet: str | None = None, limits: SheetLimits | None = None
    ) -> CellRef:
        """Build a relative cell from zero-based indexes (``column=0, row=0`` is ``A1``)."""
        column, row = as_int("column", column), as_int("row", row)
        for name, value in (("column", column), ("row", row)):
            if value < 0:
                raise OutOfBoundsError(f"zero-based {name} must be >= 0, got {value}")
        return cls(column + 1, row + 1, sheet=sheet).check(limits)

    @property
    def column_letters(self) -> str:
        """The column as letters without a marker, for example ``"B"``."""
        return index_to_column(self.column)

    @property
    def column0(self) -> int:
        """The zero-based column index (``A`` is ``0``)."""
        return self.column - 1

    @property
    def row0(self) -> int:
        """The zero-based row index (row ``1`` is ``0``)."""
        return self.row - 1

    def check(self, limits: SheetLimits | None) -> CellRef:
        """Return ``self`` if it fits ``limits`` (``None`` accepts any), else raise."""
        if limits is not None:
            limits.check_column(self.column)
            limits.check_row(self.row)
        return self

    def to_a1(self, *, include_sheet: bool = True) -> str:
        """Return the A1 text, for example ``"$B3"`` or ``"'My Sheet'!B3"``."""
        col = ("$" if self.column_absolute else "") + self.column_letters
        body = col + axis_text(self.row, self.row_absolute)
        return with_sheet_prefix(self.sheet if include_sheet else None, body)

    def __str__(self) -> str:
        return self.to_a1()

    def with_sheet(self, sheet: str | None) -> CellRef:
        """Return a copy qualified by ``sheet`` (``None`` removes the qualifier)."""
        return replace(self, sheet=sheet)

    def absolute(self) -> CellRef:
        """Return a copy with both markers set, ``B3`` becoming ``$B$3``."""
        return replace(self, column_absolute=True, row_absolute=True)

    def relative(self) -> CellRef:
        """Return a copy with both markers cleared, ``$B$3`` becoming ``B3``."""
        return replace(self, column_absolute=False, row_absolute=False)

    def offset(
        self, *, rows: int = 0, columns: int = 0, limits: SheetLimits | None = None
    ) -> CellRef:
        """Move the whole reference by ``rows`` and ``columns``, markers included.

        Raises:
            OutOfBoundsError: the result would leave the grid (below one or past ``limits``).
        """
        column, row = self.column + columns, self.row + rows
        check_axis("column", column, limits)
        check_axis("row", row, limits)
        return replace(self, column=column, row=row)

    def translate(
        self, *, rows: int = 0, columns: int = 0, limits: SheetLimits | None = None
    ) -> CellRef:
        """Shift only the relative parts, as a spreadsheet does when a formula is copied.

        ``$B3`` translated by one row and one column becomes ``$B4``: the absolute
        column stays put. Raises ``OutOfBoundsError`` when a part would leave the grid.
        """
        return self.offset(
            rows=0 if self.row_absolute else rows,
            columns=0 if self.column_absolute else columns,
            limits=limits,
        )

    def to_r1c1(self, anchor: CellRef | None = None) -> str:
        """Return R1C1 text; relative parts become offsets from ``anchor``.

        With ``anchor=None`` every part is written as an absolute number (``R3C2``).
        """
        from ._r1c1 import cell_to_r1c1

        return cell_to_r1c1(self, anchor)

    @classmethod
    def from_r1c1(
        cls, text: str, anchor: CellRef | None = None, *, limits: SheetLimits | None = None
    ) -> CellRef:
        """Parse R1C1 text such as ``R5C3`` or ``R[-1]C[2]`` (offsets need ``anchor``)."""
        from ._r1c1 import cell_from_r1c1

        return cell_from_r1c1(text, anchor, limits)
