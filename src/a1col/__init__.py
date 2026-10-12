"""Spreadsheet A1 references: columns, cells, ranges, sheets and R1C1, with typed results.

Zero dependencies. Every parser takes an optional ``limits`` (``EXCEL``, ``EXCEL_97``,
``LIBREOFFICE``, ``GOOGLE_SHEETS`` or your own ``SheetLimits``) and every error is a
``ValueError`` subclass of :class:`A1Error`.
"""

from __future__ import annotations

from ._cell import CellRef
from ._columns import (
    column_to_index,
    column_to_index0,
    index0_to_column,
    index_to_column,
    is_column,
)
from ._errors import (
    A1Error,
    InvalidColumnError,
    InvalidReferenceError,
    InvalidRowError,
    OutOfBoundsError,
)
from ._limits import EXCEL, EXCEL_97, GOOGLE_SHEETS, LIBREOFFICE, SheetLimits
from ._parse import AnyRef, parse_ref
from ._r1c1 import a1_to_r1c1, r1c1_to_a1
from ._range import RangeRef
from ._sheet import needs_quotes, quote_sheet_name, split_sheet
from ._spans import ColumnSpan, RowSpan

__version__ = "0.2.0"

__all__ = [
    "EXCEL",
    "EXCEL_97",
    "GOOGLE_SHEETS",
    "LIBREOFFICE",
    "A1Error",
    "AnyRef",
    "CellRef",
    "ColumnSpan",
    "InvalidColumnError",
    "InvalidReferenceError",
    "InvalidRowError",
    "OutOfBoundsError",
    "RangeRef",
    "RowSpan",
    "SheetLimits",
    "a1_to_r1c1",
    "column_to_index",
    "column_to_index0",
    "index0_to_column",
    "index_to_column",
    "is_column",
    "needs_quotes",
    "parse_ref",
    "quote_sheet_name",
    "r1c1_to_a1",
    "split_sheet",
]
