"""R1C1 notation: ``R5C3`` (absolute) and ``R[-1]C[2]`` (relative to an anchor cell)."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from ._errors import InvalidReferenceError
from ._limits import SheetLimits
from ._sheet import split_sheet, with_sheet_prefix

if TYPE_CHECKING:
    from ._cell import CellRef
    from ._range import RangeRef

_PART = r"(?:([0-9]+)|\[(-?[0-9]+)\])?"
_R1C1 = re.compile(rf"[Rr]{_PART}[Cc]{_PART}", re.ASCII)


def _axis(letter: str, value: int, absolute: bool, anchor_value: int | None) -> str:
    if absolute or anchor_value is None:
        return f"{letter}{value}"
    delta = value - anchor_value
    return letter if delta == 0 else f"{letter}[{delta}]"


def _body(cell: CellRef, anchor: CellRef | None) -> str:
    row = _axis("R", cell.row, cell.row_absolute, None if anchor is None else anchor.row)
    col = _axis("C", cell.column, cell.column_absolute, None if anchor is None else anchor.column)
    return row + col


def cell_to_r1c1(cell: CellRef, anchor: CellRef | None) -> str:
    """Render ``cell`` in R1C1, relative parts as offsets from ``anchor``."""
    return with_sheet_prefix(cell.sheet, _body(cell, anchor))


def range_to_r1c1(rng: RangeRef, anchor: CellRef | None) -> str:
    """Render ``rng`` in R1C1 as ``start:end`` with a single sheet prefix."""
    body = f"{_body(rng.start, anchor)}:{_body(rng.end, anchor)}"
    return with_sheet_prefix(rng.sheet, body)


def _resolve(
    name: str, plain: str | None, offset: str | None, anchor_value: int | None, text: str
) -> tuple[int, bool]:
    if plain is not None:
        if plain[0] == "0":
            raise InvalidReferenceError(f"R1C1 {name} must be >= 1 without leading zeros: {text!r}")
        return int(plain), True
    if anchor_value is None:
        raise InvalidReferenceError(f"relative R1C1 reference needs an anchor cell: {text!r}")
    delta = int(offset) if offset is not None else 0
    digits = "" if offset is None else offset.lstrip("-")
    if digits.startswith("0") and (len(digits) > 1 or offset != digits):
        raise InvalidReferenceError(f"R1C1 offset has a leading zero: {text!r}")
    return anchor_value + delta, False


def _body_cell(
    body: str, sheet: str | None, anchor: CellRef | None, limits: SheetLimits | None, text: str
) -> CellRef:
    from ._cell import CellRef, check_axis

    match = _R1C1.fullmatch(body)
    if match is None:
        raise InvalidReferenceError(f"not an R1C1 cell reference: {text!r}")
    r_plain, r_off, c_plain, c_off = match.groups()
    row, row_abs = _resolve("row", r_plain, r_off, None if anchor is None else anchor.row, text)
    col, col_abs = _resolve(
        "column", c_plain, c_off, None if anchor is None else anchor.column, text
    )
    check_axis("row", row, limits)
    check_axis("column", col, limits)
    return CellRef(col, row, col_abs, row_abs, sheet)


def cell_from_r1c1(text: str, anchor: CellRef | None, limits: SheetLimits | None) -> CellRef:
    """Parse one R1C1 cell, resolving relative parts against ``anchor``."""
    sheet, body = split_sheet(text)
    return _body_cell(body, sheet, anchor, limits, text)


def range_from_r1c1(text: str, anchor: CellRef | None, limits: SheetLimits | None) -> RangeRef:
    """Parse ``R1C1:R2C2`` (or a single R1C1 cell, as a 1x1 range)."""
    from ._range import RangeRef

    sheet, body = split_sheet(text)
    parts = body.split(":")
    if len(parts) > 2:
        raise InvalidReferenceError(f"a range has at most one ':': {text!r}")
    start = _body_cell(parts[0], sheet, anchor, limits, text)
    end = _body_cell(parts[-1], sheet, anchor, limits, text)
    return RangeRef(start, end)


def a1_to_r1c1(text: str, anchor: CellRef | str | None = None) -> str:
    """Convert an A1 cell or range (``"B3"``, ``"A1:$C$3"``) to R1C1 text.

    Relative parts become offsets from ``anchor`` (a ``CellRef`` or A1 text); with no
    anchor every part is written as an absolute number.

    Raises:
        InvalidReferenceError: ``text`` is not an A1 cell or cell range.
    """
    from ._cell import CellRef
    from ._range import RangeRef

    if ":" in split_sheet(text)[1]:
        return RangeRef.parse(text).to_r1c1(_anchor(anchor))
    return CellRef.parse(text).to_r1c1(_anchor(anchor))


def r1c1_to_a1(text: str, anchor: CellRef | str | None = None) -> str:
    """Convert an R1C1 cell or range (``"R3C2"``, ``"R[-1]C:R1C[2]"``) to A1 text.

    Absolute parts come back with ``$`` markers; relative parts are resolved against
    ``anchor`` and come back without them.

    Raises:
        InvalidReferenceError: bad syntax, or a relative part with no anchor.
        OutOfBoundsError: a relative part resolves above row 1 or left of column A.
    """
    rng = range_from_r1c1(text, _anchor(anchor), None)
    return str(rng.start) if ":" not in split_sheet(text)[1] else str(rng)


def _anchor(anchor: CellRef | str | None) -> CellRef | None:
    from ._cell import CellRef

    return CellRef.parse(anchor) if isinstance(anchor, str) else anchor
