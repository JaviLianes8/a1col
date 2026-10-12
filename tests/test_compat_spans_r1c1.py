"""Integer compatibility, sheet-name rules, span moves and whole row/column R1C1."""

import pytest

from a1col import (
    EXCEL,
    EXCEL_97,
    A1Error,
    CellRef,
    ColumnSpan,
    InvalidReferenceError,
    OutOfBoundsError,
    RowSpan,
    SheetLimits,
    a1_to_r1c1,
    index0_to_column,
    index_to_column,
    parse_ref,
    quote_sheet_name,
    r1c1_to_a1,
)


class Idx:
    """A non-int integer type, the way NumPy integers behave."""

    def __init__(self, value: int) -> None:
        self.value = value

    def __index__(self) -> int:
        return self.value


def test_index_types_keep_working() -> None:
    assert index_to_column(Idx(28)) == "AB"  # type: ignore[arg-type]
    assert index0_to_column(Idx(27)) == "AB"  # type: ignore[arg-type]
    assert index_to_column(True) == "A"  # unchanged from the original release


def test_reference_types_store_plain_ints() -> None:
    cell = CellRef(Idx(2), Idx(3))  # type: ignore[arg-type]
    assert cell == CellRef(2, 3)
    assert type(cell.column) is int
    assert type(cell.row) is int
    assert CellRef.from_zero_based(column=Idx(1), row=Idx(2)) == cell  # type: ignore[arg-type]
    span = ColumnSpan(Idx(1), Idx(3))  # type: ignore[arg-type]
    assert type(span.first) is int
    assert str(span) == "A:C"
    limits = SheetLimits("x", Idx(5), Idx(5))  # type: ignore[arg-type]
    assert type(limits.max_columns) is int


def test_bad_sheet_limits_raise_a1_error() -> None:
    for bad in (0, True, 1.5, "3"):
        with pytest.raises(A1Error):
            SheetLimits("x", bad, 1)  # type: ignore[arg-type]


@pytest.mark.parametrize("text", ["'Sheet1:Sheet3'!A1", "'Sheet 1:Sheet 3'!A1:B2", "S1:S2!A:A"])
def test_three_d_references_are_rejected_quoted_or_not(text: str) -> None:
    with pytest.raises(InvalidReferenceError):
        parse_ref(text)


def test_no_sheet_name_may_contain_a_colon() -> None:
    with pytest.raises(InvalidReferenceError):
        quote_sheet_name("a:b")
    with pytest.raises(InvalidReferenceError):
        CellRef(1, 1, sheet="a:b")


def test_span_translate_moves_only_relative_bounds() -> None:
    assert str(ColumnSpan.parse("$A:C").translate(2)) == "$A:E"
    assert str(RowSpan.parse("1:$3").translate(1)) == "2:$3"
    assert str(RowSpan.parse("$1:$3").translate(100)) == "$1:$3"
    with pytest.raises(OutOfBoundsError):
        ColumnSpan.parse("A:$C").translate(-1)
    with pytest.raises(OutOfBoundsError):
        RowSpan.parse("1048576:1048576").translate(1, limits=EXCEL)


@pytest.mark.parametrize(
    ("a1", "r1c1"),
    [
        ("$2:$2", "R2"),
        ("$1:$3", "R1:R3"),
        ("$A:$C", "C1:C3"),
        ("$B:$B", "C2"),
        ("B:B", "C"),
        ("2:2", "R"),
        ("1:$3", "R[-1]:R3"),
        ("C:$C", "C[1]:C3"),
        ("'Q 1'!A:B", "'Q 1'!C[-1]:C"),
    ],
)
def test_whole_rows_and_columns_in_r1c1(a1: str, r1c1: str) -> None:
    assert a1_to_r1c1(a1, "B2") == r1c1
    assert r1c1_to_a1(r1c1, "B2") == a1
    assert parse_ref(a1).to_r1c1(CellRef(2, 2)) == r1c1


def test_absolute_spans_need_no_anchor() -> None:
    assert a1_to_r1c1("A:C") == "C1:C3"
    assert r1c1_to_a1("R5") == "$5:$5"
    with pytest.raises(InvalidReferenceError):
        r1c1_to_a1("R[1]")
    with pytest.raises(OutOfBoundsError):
        r1c1_to_a1("C[-2]", "B2")


@pytest.mark.parametrize("text", ["R1:C1", "R1:R2:R3", "R0", "C01", "R1C1:R2", "R[+1]"])
def test_bad_r1c1_spans(text: str) -> None:
    with pytest.raises(InvalidReferenceError):
        r1c1_to_a1(text, "B2")


def test_string_converters_honour_limits() -> None:
    with pytest.raises(OutOfBoundsError):
        a1_to_r1c1("IW1", limits=EXCEL_97)
    with pytest.raises(OutOfBoundsError):
        r1c1_to_a1("R1C300", limits=EXCEL_97)
    with pytest.raises(OutOfBoundsError):
        r1c1_to_a1("R70000", limits=EXCEL_97)
    with pytest.raises(OutOfBoundsError):
        r1c1_to_a1("RC[1]", "IV1", limits=EXCEL_97)
    assert r1c1_to_a1("R1C256", limits=EXCEL_97) == "$IV$1"


def test_span_r1c1_round_trip_over_a_block() -> None:
    anchor = CellRef(5, 5)
    for first in range(1, 10):
        for last in range(1, 10):
            for flags in ((False, False), (True, False), (False, True), (True, True)):
                for span in (ColumnSpan(first, last, *flags), RowSpan(first, last, *flags)):
                    assert parse_ref(r1c1_to_a1(span.to_r1c1(anchor), anchor)) == span
