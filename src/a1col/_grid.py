"""Shared geometry for rectangular references: bounds, sizes and cell iteration."""

from __future__ import annotations

from collections.abc import Iterator

from ._cell import CellRef


class GridMixin:
    """Bounds and iteration for any reference with ``start`` and ``end`` corner cells."""

    start: CellRef
    end: CellRef

    @property
    def sheet(self) -> str | None:
        """The unquoted sheet name shared by both corners, or ``None``."""
        return self.start.sheet

    @property
    def min_column(self) -> int:
        """Leftmost one-based column."""
        return min(self.start.column, self.end.column)

    @property
    def max_column(self) -> int:
        """Rightmost one-based column."""
        return max(self.start.column, self.end.column)

    @property
    def min_row(self) -> int:
        """Top one-based row."""
        return min(self.start.row, self.end.row)

    @property
    def max_row(self) -> int:
        """Bottom one-based row."""
        return max(self.start.row, self.end.row)

    @property
    def width(self) -> int:
        """Number of columns covered."""
        return self.max_column - self.min_column + 1

    @property
    def height(self) -> int:
        """Number of rows covered."""
        return self.max_row - self.min_row + 1

    @property
    def size(self) -> int:
        """Number of cells covered (``width * height``)."""
        return self.width * self.height

    def __len__(self) -> int:
        """The number of cells, the same as ``size``."""
        return self.size

    def is_single_cell(self) -> bool:
        """Return whether the range covers exactly one cell."""
        return self.size == 1

    def cells(self) -> Iterator[CellRef]:
        """Yield every cell, row by row, left to right, as relative ``CellRef`` values."""
        for row in range(self.min_row, self.max_row + 1):
            for column in range(self.min_column, self.max_column + 1):
                yield CellRef(column, row, sheet=self.sheet)

    def __iter__(self) -> Iterator[CellRef]:
        """Iterate the cells row by row, the same as ``cells()``."""
        return self.cells()

    def rows(self) -> Iterator[tuple[CellRef, ...]]:
        """Yield one tuple of cells per row, top to bottom."""
        cols = range(self.min_column, self.max_column + 1)
        for row in range(self.min_row, self.max_row + 1):
            yield tuple(CellRef(c, row, sheet=self.sheet) for c in cols)

    def columns(self) -> Iterator[tuple[CellRef, ...]]:
        """Yield one tuple of cells per column, left to right."""
        rows = range(self.min_row, self.max_row + 1)
        for column in range(self.min_column, self.max_column + 1):
            yield tuple(CellRef(column, r, sheet=self.sheet) for r in rows)
