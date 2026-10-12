"""Cross-check against an independent workbook library when it happens to be installed.

This is a test-only oracle; a1col never imports it at runtime. Without it these tests skip.
"""

import pytest

from a1col import EXCEL, CellRef, ColumnSpan, RangeRef, column_to_index, index_to_column, parse_ref

cell_utils = pytest.importorskip("openpyxl.utils.cell")


def test_every_excel_column_matches() -> None:
    for index in range(1, EXCEL.max_columns + 1):
        letters = index_to_column(index)
        assert cell_utils.get_column_letter(index) == letters
        assert cell_utils.column_index_from_string(letters) == column_to_index(letters)


@pytest.mark.parametrize(
    "text", ["A1", "$B$3", "A1:C3", "$A$1:XFD1048576", "B2:B2", "A:C", "$D:$D", "1:3", "$5:$9"]
)
def test_range_boundaries_match(text: str) -> None:
    ref = parse_ref(text)
    expected = cell_utils.range_boundaries(text)
    got: tuple[int | None, ...]
    if isinstance(ref, RangeRef):
        got = (ref.min_column, ref.min_row, ref.max_column, ref.max_row)
    elif isinstance(ref, CellRef):
        got = (ref.column, ref.row, ref.column, ref.row)
    elif isinstance(ref, ColumnSpan):
        got = (ref.low, None, ref.high, None)
    else:
        got = (None, ref.low, None, ref.high)
    assert got == expected


@pytest.mark.parametrize("text", ["A1", "B$3", "XFD1048576", "$AA$27"])
def test_coordinate_split_matches(text: str) -> None:
    ref = parse_ref(text)
    letters, row = cell_utils.coordinate_from_string(text.replace("$", ""))
    assert (letters, row) == (ref.column_letters, ref.row)  # type: ignore[union-attr]
