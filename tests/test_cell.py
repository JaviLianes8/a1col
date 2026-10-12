import dataclasses

import pytest

from a1col import (
    EXCEL,
    CellRef,
    InvalidReferenceError,
    InvalidRowError,
    OutOfBoundsError,
)


def test_parse_relative_cell() -> None:
    assert CellRef.parse("B3") == CellRef(2, 3)


@pytest.mark.parametrize(
    ("text", "col_abs", "row_abs"),
    [("B3", False, False), ("$B3", True, False), ("B$3", False, True), ("$B$3", True, True)],
)
def test_parse_markers(text: str, col_abs: bool, row_abs: bool) -> None:
    cell = CellRef.parse(text)
    assert (cell.column, cell.row) == (2, 3)
    assert (cell.column_absolute, cell.row_absolute) == (col_abs, row_abs)
    assert str(cell) == text


def test_lowercase_is_canonicalized() -> None:
    assert str(CellRef.parse("xfd1048576")) == "XFD1048576"


def test_sheet_qualified_cells() -> None:
    cell = CellRef.parse("'It''s Q1'!$A$1")
    assert cell.sheet == "It's Q1"
    assert str(cell) == "'It''s Q1'!$A$1"
    assert cell.to_a1(include_sheet=False) == "$A$1"
    assert str(CellRef.parse("Sheet1!C2")) == "Sheet1!C2"
    assert str(CellRef.parse("'Sheet1'!C2")) == "Sheet1!C2"


@pytest.mark.parametrize(
    "text",
    ["", "B", "3", "3B", "B3C", "B 3", " B3", "B3 ", "B-3", "B+3", "$$B3", "B$$3", "B3$", "Ä3",
     "B٣", "B³", "A1:B2"],
)  # fmt: skip
def test_invalid_cells(text: str) -> None:
    with pytest.raises(InvalidReferenceError):
        CellRef.parse(text)


@pytest.mark.parametrize("text", ["A0", "A01", "A001"])
def test_invalid_rows(text: str) -> None:
    with pytest.raises(InvalidRowError):
        CellRef.parse(text)


def test_limits_on_parse() -> None:
    assert CellRef.parse("XFD1048576", limits=EXCEL) == CellRef(16_384, 1_048_576)
    for text in ("XFE1", "A1048577"):
        with pytest.raises(OutOfBoundsError):
            CellRef.parse(text, limits=EXCEL)


def test_constructor_validates() -> None:
    with pytest.raises(OutOfBoundsError):
        CellRef(0, 1)
    with pytest.raises(OutOfBoundsError):
        CellRef(1, 0)
    with pytest.raises(TypeError):
        CellRef(True, 1)
    with pytest.raises(InvalidReferenceError):
        CellRef(1, 1, sheet="")


def test_frozen() -> None:
    cell = CellRef(1, 1)
    with pytest.raises(dataclasses.FrozenInstanceError):
        cell.row = 2  # type: ignore[misc]


def test_zero_based_views() -> None:
    cell = CellRef.from_zero_based(column=0, row=0)
    assert cell == CellRef(1, 1)
    assert (CellRef(3, 7).column0, CellRef(3, 7).row0) == (2, 6)
    assert CellRef.from_zero_based(column=2, row=6, sheet="S").sheet == "S"
    with pytest.raises(OutOfBoundsError):
        CellRef.from_zero_based(column=-1, row=0)
    with pytest.raises(OutOfBoundsError):
        CellRef.from_zero_based(column=16_384, row=0, limits=EXCEL)
    with pytest.raises(TypeError):
        CellRef.from_zero_based(column=0.0, row=0)  # type: ignore[arg-type]


def test_marker_helpers_and_sheet() -> None:
    cell = CellRef.parse("B3")
    assert str(cell.absolute()) == "$B$3"
    assert str(cell.absolute().relative()) == "B3"
    assert str(cell.with_sheet("My Sheet")) == "'My Sheet'!B3"
    assert cell.with_sheet("X").with_sheet(None) == cell
    assert cell.column_letters == "B"


def test_offset_moves_everything() -> None:
    assert str(CellRef.parse("$B$3").offset(rows=2, columns=1)) == "$C$5"
    assert str(CellRef.parse("B3").offset(rows=-2, columns=-1)) == "A1"
    with pytest.raises(OutOfBoundsError):
        CellRef.parse("A1").offset(rows=-1)
    with pytest.raises(OutOfBoundsError):
        CellRef.parse("XFD1").offset(columns=1, limits=EXCEL)


def test_translate_moves_only_relative_parts() -> None:
    assert str(CellRef.parse("$B3").translate(rows=1, columns=1)) == "$B4"
    assert str(CellRef.parse("B$3").translate(rows=1, columns=1)) == "C$3"
    assert str(CellRef.parse("$B$3").translate(rows=9, columns=9)) == "$B$3"
    assert str(CellRef.parse("$A$1").translate(rows=-5)) == "$A$1"
    with pytest.raises(OutOfBoundsError):
        CellRef.parse("A$1").translate(columns=-1)


def test_check() -> None:
    cell = CellRef(16_384, 1)
    assert cell.check(None) is cell
    assert cell.check(EXCEL) is cell
    with pytest.raises(OutOfBoundsError):
        CellRef(16_385, 1).check(EXCEL)


def test_hashable_and_comparable_by_value() -> None:
    assert len({CellRef.parse("b3"), CellRef.parse("B3"), CellRef(2, 3)}) == 1
    assert CellRef.parse("B3") != CellRef.parse("$B3")
