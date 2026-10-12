"""Grid size limits of common spreadsheet applications."""

from __future__ import annotations

import operator
from dataclasses import dataclass

from ._errors import A1Error, OutOfBoundsError


@dataclass(frozen=True)
class SheetLimits:
    """The largest one-based column and row an application accepts.

    ``max_columns`` and ``max_rows`` are inclusive. Pass an instance as ``limits=`` to
    any parser or mover to reject references that fall outside that grid.
    """

    name: str
    max_columns: int
    max_rows: int

    def __post_init__(self) -> None:
        for field in ("max_columns", "max_rows"):
            value = getattr(self, field)
            try:
                number = None if isinstance(value, bool) else operator.index(value)
            except TypeError:
                number = None
            if number is None or number < 1:
                raise A1Error(f"{field} must be a positive int, got {value!r}")
            object.__setattr__(self, field, number)

    @property
    def last_column(self) -> str:
        """The letters of the last column, for example ``"XFD"`` for Excel."""
        from ._columns import index_to_column

        return index_to_column(self.max_columns)

    def check_column(self, column: int) -> int:
        """Return ``column`` unchanged, or raise ``OutOfBoundsError`` if it is off the grid."""
        if not 1 <= column <= self.max_columns:
            raise OutOfBoundsError(
                f"column {column} is outside 1..{self.max_columns} ({self.name})"
            )
        return column

    def check_row(self, row: int) -> int:
        """Return ``row`` unchanged, or raise ``OutOfBoundsError`` if it is off the grid."""
        if not 1 <= row <= self.max_rows:
            raise OutOfBoundsError(f"row {row} is outside 1..{self.max_rows} ({self.name})")
        return row

    def contains(self, column: int, row: int) -> bool:
        """Return whether the one-based ``column`` and ``row`` both lie on this grid."""
        return 1 <= column <= self.max_columns and 1 <= row <= self.max_rows


EXCEL = SheetLimits("Excel", 16_384, 1_048_576)
"""Excel 2007 and later: 16,384 columns (``A`` to ``XFD``) by 1,048,576 rows."""

EXCEL_97 = SheetLimits("Excel 97-2003", 256, 65_536)
"""The legacy ``.xls`` grid: 256 columns (``A`` to ``IV``) by 65,536 rows."""

LIBREOFFICE = SheetLimits("LibreOffice Calc", 16_384, 1_048_576)
"""LibreOffice Calc 7.4 and later: the same 16,384 by 1,048,576 grid as Excel."""

GOOGLE_SHEETS = SheetLimits("Google Sheets", 18_278, 10_000_000)
"""Google Sheets: 18,278 columns (``A`` to ``ZZZ``).

Sheets has no fixed row count; a spreadsheet holds at most 10 million cells, so
10,000,000 rows is the ceiling reachable with a single column.
"""
