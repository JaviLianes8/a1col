"""Plain data views of references, used by the command line ``parse`` command."""

from __future__ import annotations

from typing import Any

from ._cell import CellRef
from ._parse import AnyRef
from ._range import RangeRef
from ._spans import ColumnSpan


def _cell(cell: CellRef) -> dict[str, Any]:
    return {
        "a1": cell.to_a1(include_sheet=False),
        "column": cell.column,
        "column_letters": cell.column_letters,
        "row": cell.row,
        "column_absolute": cell.column_absolute,
        "row_absolute": cell.row_absolute,
    }


def describe(ref: AnyRef) -> dict[str, Any]:
    """Return a JSON-ready mapping describing ``ref``: kind, sheet, canonical text, bounds."""
    data: dict[str, Any] = {"a1": str(ref), "sheet": ref.sheet}
    if isinstance(ref, CellRef):
        data["kind"] = "cell"
        data.update(_cell(ref))
    elif isinstance(ref, RangeRef):
        data["kind"] = "range"
        data["start"], data["end"] = _cell(ref.start), _cell(ref.end)
        data.update(
            min_column=ref.min_column,
            max_column=ref.max_column,
            min_row=ref.min_row,
            max_row=ref.max_row,
            width=ref.width,
            height=ref.height,
            size=ref.size,
        )
    else:
        data["kind"] = "columns" if isinstance(ref, ColumnSpan) else "rows"
        data.update(first=ref.first, last=ref.last, count=ref.count)
    data["a1"] = str(ref)  # the full text, sheet included, even for a single cell
    return data


def describe_text(ref: AnyRef) -> str:
    """Return a short human-readable, line-per-fact description of ``ref``."""
    data = describe(ref)
    lines = [f"kind: {data['kind']}", f"a1: {data['a1']}", f"sheet: {data['sheet'] or '-'}"]
    if isinstance(ref, CellRef):
        lines.append(f"column: {ref.column_letters} ({ref.column})")
        lines.append(f"row: {ref.row}")
    elif isinstance(ref, RangeRef):
        lines.append(f"columns: {ref.min_column}..{ref.max_column}")
        lines.append(f"rows: {ref.min_row}..{ref.max_row}")
        lines.append(f"size: {ref.height} rows x {ref.width} columns = {ref.size} cells")
    else:
        lines.append(f"{data['kind']}: {ref.low}..{ref.high} ({ref.count})")
    return "\n".join(lines)
