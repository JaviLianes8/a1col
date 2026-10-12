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
    from ._spans import ColumnSpan, RowSpan, _Span

_PART = r"(?:([0-9]+)|\[(-?[0-9]+)\])?"
_R1C1 = re.compile(rf"[Rr]{_PART}[Cc]{_PART}", re.ASCII)
_ROWS = re.compile(rf"[Rr]{_PART}", re.ASCII)
_COLS = re.compile(rf"[Cc]{_PART}", re.ASCII)


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


def span_to_r1c1(span: _Span, anchor: CellRef | None) -> str:
    """Render whole columns as ``C1:C3`` or whole rows as ``R[-1]:R2``."""
    from ._spans import ColumnSpan

    is_col = isinstance(span, ColumnSpan)
    letter = "C" if is_col else "R"
    base = None if anchor is None else (anchor.column if is_col else anchor.row)
    first = _axis(letter, span.first, span.first_absolute, base)
    last = _axis(letter, span.last, span.last_absolute, base)
    return with_sheet_prefix(span.sheet, first if first == last else f"{first}:{last}")


def span_from_r1c1(
    text: str, anchor: CellRef | None, limits: SheetLimits | None
) -> ColumnSpan | RowSpan | None:
    """Parse ``R2``, ``R1:R3``, ``C[1]`` or ``C1:C3``; ``None`` if it is not a span."""
    from ._cell import check_axis
    from ._spans import ColumnSpan, RowSpan

    sheet, body = split_sheet(text)
    parts = body.split(":")
    for pattern, name in ((_ROWS, "row"), (_COLS, "column")):
        matches = [pattern.fullmatch(part) for part in parts]
        if len(parts) > 2 or not all(matches):
            continue
        base = None if anchor is None else (anchor.row if name == "row" else anchor.column)
        bounds = [_resolve(name, m[1], m[2], base, text) for m in matches if m is not None]
        values = [check_axis(name, value, limits) for value, _ in bounds]
        span_type = RowSpan if name == "row" else ColumnSpan
        return span_type(values[0], values[-1], bounds[0][1], bounds[-1][1], sheet)
    return None


def a1_to_r1c1(
    text: str, anchor: CellRef | str | None = None, *, limits: SheetLimits | None = None
) -> str:
    """Convert any A1 reference (``"B3"``, ``"A1:$C$3"``, ``"A:C"``, ``"2:2"``) to R1C1.

    Relative parts become offsets from ``anchor`` (a ``CellRef`` or A1 text); with no
    anchor every part is written as an absolute number. Whole columns and rows become
    ``C1:C3`` and ``R2``. With ``limits`` the reference must fit that grid.

    Raises:
        InvalidReferenceError: ``text`` is not an A1 reference.
        OutOfBoundsError: ``text`` lies outside ``limits``.
    """
    from ._parse import parse_ref

    return parse_ref(text, limits=limits).to_r1c1(_anchor(anchor))


def r1c1_to_a1(
    text: str, anchor: CellRef | str | None = None, *, limits: SheetLimits | None = None
) -> str:
    """Convert R1C1 text (``"R3C2"``, ``"R[-1]C:R1C[2]"``, ``"R2"``, ``"C1:C3"``) to A1.

    Absolute parts come back with ``$`` markers; relative parts are resolved against
    ``anchor`` and come back without them. ``R2`` alone is the whole row 2 and ``C3``
    alone the whole column C, as in a spreadsheet.

    Raises:
        InvalidReferenceError: bad syntax, or a relative part with no anchor.
        OutOfBoundsError: a part resolves above row 1, left of column A, or past ``limits``.
    """
    resolved = _anchor(anchor)
    span = span_from_r1c1(text, resolved, limits)
    if span is not None:
        return str(span)
    rng = range_from_r1c1(text, resolved, limits)
    return str(rng.start) if ":" not in split_sheet(text)[1] else str(rng)


def _anchor(anchor: CellRef | str | None) -> CellRef | None:
    from ._cell import CellRef

    return CellRef.parse(anchor) if isinstance(anchor, str) else anchor
