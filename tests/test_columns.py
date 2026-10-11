import pytest

from a1col import column_to_index, index_to_column


def test_column_a_is_one() -> None:
    assert column_to_index("A") == 1


def test_column_z_is_twenty_six() -> None:
    assert column_to_index("Z") == 26


def test_column_aa_is_twenty_seven() -> None:
    assert column_to_index("AA") == 27


def test_column_ab_is_twenty_eight() -> None:
    assert column_to_index("AB") == 28


def test_index_one_is_a() -> None:
    assert index_to_column(1) == "A"


def test_index_twenty_seven_is_aa() -> None:
    assert index_to_column(27) == "AA"


def test_round_trip_over_a_range() -> None:
    for column in ("A", "Z", "AA", "AZ", "BA", "ZZ", "AAA", "XFD"):
        assert index_to_column(column_to_index(column)) == column


def test_lowercase_is_accepted() -> None:
    assert column_to_index("aa") == 27


def test_leading_absolute_marker_is_accepted() -> None:
    assert column_to_index("$C") == 3


def test_empty_input_raises() -> None:
    with pytest.raises(ValueError):
        column_to_index("")


def test_lone_marker_raises() -> None:
    with pytest.raises(ValueError):
        column_to_index("$")


def test_non_letters_raise() -> None:
    with pytest.raises(ValueError):
        column_to_index("A1")


def test_index_below_one_raises() -> None:
    with pytest.raises(ValueError):
        index_to_column(0)
