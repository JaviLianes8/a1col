import pytest

from a1col import (
    EXCEL,
    EXCEL_97,
    InvalidColumnError,
    OutOfBoundsError,
    column_to_index,
    column_to_index0,
    index0_to_column,
    index_to_column,
    is_column,
)


def test_zero_based_conversions() -> None:
    assert column_to_index0("A") == 0
    assert column_to_index0("AA") == 26
    assert index0_to_column(0) == "A"
    assert index0_to_column(26) == "AA"
    assert index0_to_column(16_383) == "XFD"


def test_zero_based_round_trip() -> None:
    for index in range(0, 2_000):
        assert column_to_index0(index0_to_column(index)) == index


def test_negative_zero_based_index_is_out_of_bounds() -> None:
    with pytest.raises(OutOfBoundsError):
        index0_to_column(-1)


def test_is_column_never_raises() -> None:
    assert is_column("A")
    assert is_column("$xfd")
    for bad in ("", "$", "A1", "Ä", " A", "A$", "$$A", 3, None):
        assert not is_column(bad)  # type: ignore[arg-type]


def test_limits_reject_columns_past_the_grid() -> None:
    assert column_to_index("XFD", limits=EXCEL) == 16_384
    with pytest.raises(OutOfBoundsError):
        column_to_index("XFE", limits=EXCEL)
    with pytest.raises(OutOfBoundsError):
        index_to_column(257, limits=EXCEL_97)
    with pytest.raises(OutOfBoundsError):
        index0_to_column(256, limits=EXCEL_97)
    assert index0_to_column(255, limits=EXCEL_97) == "IV"


def test_errors_are_typed_and_still_value_errors() -> None:
    with pytest.raises(InvalidColumnError):
        column_to_index("A1")
    with pytest.raises(ValueError):
        column_to_index("")
    with pytest.raises(OutOfBoundsError):
        index_to_column(0)


def test_non_string_and_non_int_inputs_raise_type_error() -> None:
    with pytest.raises(TypeError):
        column_to_index(5)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        index_to_column("5")  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        index_to_column(1.0)  # type: ignore[arg-type]


def test_long_columns_are_unbounded_without_limits() -> None:
    assert column_to_index("AAAA") == 18_279
    assert index_to_column(18_279) == "AAAA"
