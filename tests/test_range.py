import pytest

from a1col import EXCEL, CellRef, InvalidReferenceError, OutOfBoundsError, RangeRef


def r(text: str) -> RangeRef:
    return RangeRef.parse(text)


def test_parse_and_print() -> None:
    rng = r("A1:C3")
    assert (rng.start, rng.end) == (CellRef(1, 1), CellRef(3, 3))
    assert str(rng) == "A1:C3"
    assert str(r("'My Sheet'!$A$1:b2")) == "'My Sheet'!$A$1:B2"
    assert r("Sheet1!A1:B2").to_a1(include_sheet=False) == "A1:B2"


def test_single_cell_parses_as_one_by_one() -> None:
    rng = r("B2")
    assert rng.is_single_cell()
    assert rng.start == rng.end == CellRef(2, 2)
    assert str(rng) == "B2:B2"


def test_geometry() -> None:
    rng = r("B2:D5")
    assert (rng.min_column, rng.max_column, rng.min_row, rng.max_row) == (2, 4, 2, 5)
    assert (rng.width, rng.height, rng.size, len(rng)) == (3, 4, 12, 12)


def test_reversed_corners_are_kept_but_measured_normalized() -> None:
    rng = r("C3:A1")
    assert str(rng) == "C3:A1"
    assert rng.size == 9
    assert str(rng.normalized()) == "A1:C3"
    assert str(r("$C1:A$3").normalized()) == "A1:$C$3"


def test_iteration_is_row_major() -> None:
    assert [str(c) for c in r("A1:B2")] == ["A1", "B1", "A2", "B2"]
    assert [[str(c) for c in row] for row in r("A1:B2").rows()] == [["A1", "B1"], ["A2", "B2"]]
    assert [[str(c) for c in col] for col in r("A1:B2").columns()] == [["A1", "A2"], ["B1", "B2"]]
    assert [str(c) for c in r("S!B2:A1").cells()] == ["S!A1", "S!B1", "S!A2", "S!B2"]


def test_containment() -> None:
    rng = r("B2:D4")
    assert CellRef.parse("C3") in rng
    assert CellRef.parse("$B$2") in rng
    assert CellRef.parse("A1") not in rng
    assert "C3" not in rng
    assert rng.contains(r("C3:D4"))
    assert rng.contains(CellRef.parse("D4"))
    assert not rng.contains(r("C3:E4"))


def test_sheets_in_containment() -> None:
    rng = r("S!A1:C3")
    assert CellRef.parse("S!B2") in rng
    assert CellRef.parse("B2") in rng
    assert CellRef.parse("T!B2") not in rng
    assert not rng.contains(r("T!A1:B2"))


def test_intersection_and_overlap() -> None:
    a, b = r("A1:C3"), r("B2:D4")
    assert str(a.intersection(b)) == "B2:C3"
    assert a.overlaps(b)
    assert a.intersection(r("D4:E5")) is None
    assert not a.overlaps(r("D1:D9"))
    assert str(r("$A$1:$C$3").intersection(r("C3:Z9"))) == "C3:C3"
    assert r("S!A1:B2").intersection(r("T!A1:B2")) is None
    assert str(r("A1:B2").intersection(r("S!B2:C3"))) == "S!B2:B2"


def test_bounding_box() -> None:
    assert str(r("B2:C3").bounding_box(r("E1:F2"))) == "B1:F3"
    assert str(r("B2:C3").bounding_box(CellRef.parse("A9"))) == "A2:C9"
    with pytest.raises(InvalidReferenceError):
        r("S!A1").bounding_box(r("T!A1"))


def test_offset_and_translate() -> None:
    assert str(r("A1:$B$2").offset(rows=1, columns=1)) == "B2:$C$3"
    assert str(r("A1:$B$2").translate(rows=1, columns=1)) == "B2:$B$2"
    with pytest.raises(OutOfBoundsError):
        r("A1:B2").offset(columns=-1)
    with pytest.raises(OutOfBoundsError):
        r("A1:XFD1").offset(columns=1, limits=EXCEL)


def test_with_sheet_and_check() -> None:
    rng = r("A1:B2").with_sheet("Data 1")
    assert str(rng) == "'Data 1'!A1:B2"
    assert rng.with_sheet(None) == r("A1:B2")
    assert rng.check(EXCEL) is rng
    with pytest.raises(OutOfBoundsError):
        RangeRef(CellRef(1, 1), CellRef(1, 1_048_577)).check(EXCEL)


@pytest.mark.parametrize(
    "text", ["A1:", ":B2", "A1:B2:C3", "A1:B", "A:B2", "A1:S!B2", "A1:B2 ", "1:B2"]
)
def test_invalid_ranges(text: str) -> None:
    with pytest.raises(InvalidReferenceError):
        r(text)


def test_corners_must_share_a_sheet() -> None:
    with pytest.raises(InvalidReferenceError):
        RangeRef(CellRef(1, 1, sheet="S"), CellRef(2, 2))


def test_limits_on_parse() -> None:
    with pytest.raises(OutOfBoundsError):
        RangeRef.parse("A1:XFE1", limits=EXCEL)
