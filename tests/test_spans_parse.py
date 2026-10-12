import pytest

from a1col import (
    EXCEL,
    EXCEL_97,
    CellRef,
    ColumnSpan,
    InvalidReferenceError,
    OutOfBoundsError,
    RangeRef,
    RowSpan,
    parse_ref,
)


def test_column_span() -> None:
    span = ColumnSpan.parse("$a:C")
    assert (span.first, span.last, span.first_absolute, span.last_absolute) == (1, 3, True, False)
    assert str(span) == "$A:C"
    assert span.count == 3
    assert list(ColumnSpan.parse("Y:AB").letters()) == ["Y", "Z", "AA", "AB"]
    assert CellRef.parse("B999999") in span
    assert CellRef.parse("D1") not in span
    assert "B1" not in span


def test_row_span() -> None:
    span = RowSpan.parse("'My Sheet'!5:$3")
    assert (span.low, span.high, span.count) == (3, 5, 3)
    assert str(span) == "'My Sheet'!5:$3"
    assert CellRef.parse("XFD4") in span
    assert CellRef.parse("'My Sheet'!A4") in span
    assert CellRef.parse("Other!A4") not in span


def test_spans_to_ranges() -> None:
    assert str(ColumnSpan.parse("A:C").to_range()) == "A1:C1048576"
    assert str(RowSpan.parse("S!2:3").to_range(EXCEL_97)) == "S!A2:IV3"
    with pytest.raises(OutOfBoundsError):
        ColumnSpan.parse("A:IW").to_range(EXCEL_97)
    with pytest.raises(OutOfBoundsError):
        RowSpan.parse("1:65537").to_range(EXCEL_97)


def test_span_offsets() -> None:
    assert str(ColumnSpan.parse("A:B").offset(2)) == "C:D"
    assert str(RowSpan.parse("$1:2").offset(3)) == "$4:5"
    with pytest.raises(OutOfBoundsError):
        ColumnSpan.parse("A:B").offset(-1)
    with pytest.raises(OutOfBoundsError):
        RowSpan.parse("1048576:1048576").offset(1, limits=EXCEL)


@pytest.mark.parametrize("text", ["A", "A:", ":A", "A:B:C", "A:1", "A1:B", "A :B", "S!A:1"])
def test_invalid_column_spans(text: str) -> None:
    with pytest.raises(InvalidReferenceError):
        ColumnSpan.parse(text)


@pytest.mark.parametrize("text", ["1", "1:", ":1", "1:2:3", "1:A", "0:3", "01:3", "1 :2"])
def test_invalid_row_spans(text: str) -> None:
    with pytest.raises(InvalidReferenceError):
        RowSpan.parse(text)


def test_span_constructors_validate() -> None:
    with pytest.raises(OutOfBoundsError):
        ColumnSpan(0, 1)
    with pytest.raises(OutOfBoundsError):
        RowSpan(1, 0)
    with pytest.raises(InvalidReferenceError):
        RowSpan(1, 1, sheet="")


def test_span_limits_on_parse() -> None:
    with pytest.raises(OutOfBoundsError):
        ColumnSpan.parse("A:XFE", limits=EXCEL)
    with pytest.raises(OutOfBoundsError):
        RowSpan.parse("1:1048577", limits=EXCEL)


@pytest.mark.parametrize(
    ("text", "kind"),
    [
        ("B3", CellRef),
        ("'S 1'!$B$3", CellRef),
        ("A1:C3", RangeRef),
        ("S!A1:C3", RangeRef),
        ("A:C", ColumnSpan),
        ("$A:$A", ColumnSpan),
        ("1:3", RowSpan),
        ("S!$1:$1", RowSpan),
    ],
)
def test_parse_ref_dispatch(text: str, kind: type) -> None:
    ref = parse_ref(text)
    assert isinstance(ref, kind)
    assert str(ref) == text


@pytest.mark.parametrize("text", ["", "A", "1", "A1:C", "A:3", "A1:B2:C3", "A:B:C", "x y"])
def test_parse_ref_errors(text: str) -> None:
    with pytest.raises(InvalidReferenceError):
        parse_ref(text)


def test_parse_ref_limits() -> None:
    with pytest.raises(OutOfBoundsError):
        parse_ref("IW1", limits=EXCEL_97)
