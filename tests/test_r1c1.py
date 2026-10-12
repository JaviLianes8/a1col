import pytest

from a1col import (
    CellRef,
    InvalidReferenceError,
    OutOfBoundsError,
    RangeRef,
    a1_to_r1c1,
    r1c1_to_a1,
)

C3 = CellRef.parse("C3")


@pytest.mark.parametrize(
    ("a1", "r1c1"),
    [
        ("C3", "RC"),
        ("B2", "R[-1]C[-1]"),
        ("E1", "R[-2]C[2]"),
        ("$C$3", "R3C3"),
        ("$A5", "R[2]C1"),
        ("D$1", "R1C[1]"),
        ("'My Sheet'!$B$2", "'My Sheet'!R2C2"),
    ],
)
def test_cell_to_r1c1_with_anchor(a1: str, r1c1: str) -> None:
    cell = CellRef.parse(a1)
    assert cell.to_r1c1(C3) == r1c1
    assert CellRef.from_r1c1(r1c1, C3) == cell


def test_without_anchor_every_part_is_absolute() -> None:
    assert CellRef.parse("B3").to_r1c1() == "R3C2"
    assert str(CellRef.from_r1c1("R3C2")) == "$B$3"


def test_relative_parse_needs_anchor() -> None:
    with pytest.raises(InvalidReferenceError):
        CellRef.from_r1c1("R[1]C1")
    with pytest.raises(InvalidReferenceError):
        CellRef.from_r1c1("RC")


def test_lowercase_and_zero_offsets() -> None:
    assert CellRef.from_r1c1("r[0]c[0]", C3) == C3
    assert CellRef.from_r1c1("r3c3") == C3.absolute()
    assert str(CellRef.from_r1c1("R1C", C3)) == "C$1"
    assert str(CellRef.from_r1c1("RC1", C3)) == "$A3"


@pytest.mark.parametrize(
    "text",
    ["R0C1", "R1C0", "R01C1", "R1", "R1C1C1", "C1", "R[1.5]C1", "R[+1]C1", "R[01]C", "R[-0]C",
     "R[]C", "R1C1:R2C2:R3C3", "A1", "R1 C1", ""],
)  # fmt: skip
def test_invalid_r1c1(text: str) -> None:
    with pytest.raises(InvalidReferenceError):
        RangeRef.from_r1c1(text, C3)


def test_relative_parts_cannot_leave_the_grid() -> None:
    with pytest.raises(OutOfBoundsError):
        CellRef.from_r1c1("R[-3]C", C3)
    with pytest.raises(OutOfBoundsError):
        CellRef.from_r1c1("RC[-3]", C3)


def test_ranges() -> None:
    rng = RangeRef.parse("A1:$D$4")
    assert rng.to_r1c1(C3) == "R[-2]C[-2]:R4C4"
    assert RangeRef.from_r1c1("R[-2]C[-2]:R4C4", C3) == rng
    assert RangeRef.from_r1c1("S!R1C1:R2C2").sheet == "S"
    assert RangeRef.from_r1c1("R1C1").is_single_cell()


def test_string_helpers() -> None:
    assert a1_to_r1c1("B3") == "R3C2"
    assert a1_to_r1c1("B3", "A1") == "R[2]C[1]"
    assert a1_to_r1c1("A1:$C$3", "B2") == "R[-1]C[-1]:R3C3"
    assert a1_to_r1c1("'Q 1'!B3", C3) == "'Q 1'!RC[-1]"
    assert r1c1_to_a1("R[2]C[1]", "A1") == "B3"
    assert r1c1_to_a1("R3C2") == "$B$3"
    assert r1c1_to_a1("R[-1]C:R1C[2]", "B2") == "B1:D$1"
    assert r1c1_to_a1("'Q 1'!RC", "B2") == "'Q 1'!B2"


def test_exact_round_trip_over_a_block() -> None:
    anchor = CellRef.parse("E5")
    for column in range(1, 12):
        for row in range(1, 12):
            for col_abs in (False, True):
                for row_abs in (False, True):
                    cell = CellRef(column, row, col_abs, row_abs)
                    assert CellRef.from_r1c1(cell.to_r1c1(anchor), anchor) == cell
                    assert r1c1_to_a1(a1_to_r1c1(str(cell), anchor), anchor) == str(cell)
