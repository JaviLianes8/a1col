"""Contract: the complete promise of every public name, checked exhaustively where possible."""

import dataclasses
import importlib.resources
import string

import pytest

import a1col
from a1col import (
    EXCEL,
    EXCEL_97,
    GOOGLE_SHEETS,
    LIBREOFFICE,
    CellRef,
    ColumnSpan,
    RangeRef,
    RowSpan,
    SheetLimits,
)

# The public API. This list is the contract: the test below fails if it and the module disagree.
PUBLIC_API: list[str] = [
    "EXCEL", "EXCEL_97", "GOOGLE_SHEETS", "LIBREOFFICE",
    "A1Error", "InvalidColumnError", "InvalidReferenceError", "InvalidRowError",
    "OutOfBoundsError", "AnyRef", "CellRef", "ColumnSpan", "RangeRef", "RowSpan",
    "SheetLimits", "a1_to_r1c1", "column_to_index", "column_to_index0", "index0_to_column",
    "index_to_column", "is_column", "needs_quotes", "parse_ref", "quote_sheet_name",
    "r1c1_to_a1", "split_sheet",
]  # fmt: skip
PRESETS = [EXCEL, EXCEL_97, LIBREOFFICE, GOOGLE_SHEETS]


def test_all_lists_exactly_the_public_api() -> None:
    assert sorted(a1col.__all__) == sorted(PUBLIC_API)


def test_every_exported_name_resolves_and_is_documented() -> None:
    for name in a1col.__all__:
        obj = getattr(a1col, name)
        if callable(obj) and name != "AnyRef":
            assert obj.__doc__, f"{name} has no docstring"


def test_version_is_a_three_part_string() -> None:
    parts = a1col.__version__.split(".")
    assert len(parts) == 3
    assert all(part.isdigit() for part in parts)


def test_the_package_ships_type_information() -> None:
    assert importlib.resources.files("a1col").joinpath("py.typed").is_file()


def test_every_error_is_a_value_error() -> None:
    for name in ("InvalidColumnError", "InvalidReferenceError", "InvalidRowError"):
        assert issubclass(getattr(a1col, name), a1col.InvalidReferenceError)
    for name in ("InvalidReferenceError", "OutOfBoundsError"):
        assert issubclass(getattr(a1col, name), a1col.A1Error)
    assert issubclass(a1col.A1Error, ValueError)


def test_exhaustive_column_round_trip_over_the_excel_grid() -> None:
    previous = ""
    for index in range(1, EXCEL.max_columns + 1):
        letters = a1col.index_to_column(index, limits=EXCEL)
        assert a1col.column_to_index(letters, limits=EXCEL) == index
        assert a1col.column_to_index(letters.lower()) == index
        assert a1col.column_to_index("$" + letters) == index
        assert a1col.column_to_index0(letters) == index - 1
        assert a1col.index0_to_column(index - 1) == letters
        assert a1col.is_column(letters)
        assert set(letters) <= set(string.ascii_uppercase)
        # Spreadsheet order: shorter names first, then alphabetical.
        assert (len(previous), previous) < (len(letters), letters)
        previous = letters
    assert previous == "XFD"


def test_exhaustive_cell_round_trip_on_the_first_row_and_column() -> None:
    for index in range(1, EXCEL.max_columns + 1):
        for col_abs in (False, True):
            cell = CellRef(index, index, col_abs, not col_abs)
            assert CellRef.parse(str(cell), limits=EXCEL) == cell
            assert CellRef.from_r1c1(cell.to_r1c1(CellRef(9, 9)), CellRef(9, 9)) == cell


@pytest.mark.parametrize("limits", PRESETS, ids=lambda lim: lim.name)
def test_every_preset_boundary(limits: SheetLimits) -> None:
    last = f"{limits.last_column}{limits.max_rows}"
    assert CellRef.parse(last, limits=limits) == CellRef(limits.max_columns, limits.max_rows)
    assert limits.contains(limits.max_columns, limits.max_rows)
    assert not limits.contains(limits.max_columns + 1, 1)
    assert not limits.contains(1, limits.max_rows + 1)
    assert not limits.contains(0, 1)
    past_column = a1col.index_to_column(limits.max_columns + 1)
    for text in (f"{past_column}1", f"A{limits.max_rows + 1}"):
        with pytest.raises(a1col.OutOfBoundsError):
            a1col.parse_ref(text, limits=limits)
    full = ColumnSpan(1, limits.max_columns).to_range(limits)
    assert full.size == limits.max_columns * limits.max_rows
    assert RowSpan(1, 1).to_range(limits).width == limits.max_columns


def test_documented_preset_values() -> None:
    assert (EXCEL.max_columns, EXCEL.max_rows, EXCEL.last_column) == (16_384, 1_048_576, "XFD")
    assert (EXCEL_97.max_columns, EXCEL_97.max_rows, EXCEL_97.last_column) == (256, 65_536, "IV")
    assert (LIBREOFFICE.max_columns, LIBREOFFICE.max_rows) == (16_384, 1_048_576)
    assert (GOOGLE_SHEETS.max_columns, GOOGLE_SHEETS.last_column) == (18_278, "ZZZ")


def test_sheet_limits_validate_and_are_frozen() -> None:
    for bad in (0, -1, True, 1.5):
        with pytest.raises(ValueError):
            SheetLimits("x", bad, 1)  # type: ignore[arg-type]
        with pytest.raises(ValueError):
            SheetLimits("x", 1, bad)  # type: ignore[arg-type]
    with pytest.raises(dataclasses.FrozenInstanceError):
        EXCEL.max_rows = 1  # type: ignore[misc]
    assert SheetLimits("tiny", 2, 2).check_column(2) == 2
    with pytest.raises(a1col.OutOfBoundsError):
        SheetLimits("tiny", 2, 2).check_row(3)


@pytest.mark.parametrize(
    "name", ["Sheet1", "My Sheet", "It's", "a''b", "A1", "R1C1", "1", "x!y", "Ünïcødé", " "]
)
def test_quoting_round_trips_through_every_reference_type(name: str) -> None:
    for ref in (
        CellRef(2, 3, sheet=name),
        RangeRef(CellRef(1, 1, sheet=name), CellRef(2, 2, True, True, sheet=name)),
        ColumnSpan(1, 3, sheet=name),
        RowSpan(1, 3, sheet=name),
    ):
        text = str(ref)
        assert text.startswith(a1col.quote_sheet_name(name) + "!")
        assert a1col.parse_ref(text) == ref
        assert a1col.split_sheet(text)[0] == name


def test_all_reference_types_are_frozen_and_hashable() -> None:
    refs: list[a1col.AnyRef] = [
        CellRef(1, 1),
        RangeRef.parse("A1:B2"),
        ColumnSpan(1, 2),
        RowSpan(1, 2),
    ]
    for ref in refs:
        assert hash(ref) == hash(dataclasses.replace(ref))
        with pytest.raises(dataclasses.FrozenInstanceError):
            ref.sheet = "x"  # type: ignore[misc]
