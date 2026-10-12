import pytest

from a1col import CellRef, InvalidReferenceError, needs_quotes, quote_sheet_name, split_sheet


@pytest.mark.parametrize(
    "name", ["Sheet1", "Data", "data_2024", "Q1.final", "_x", "Données", "ABCD1"]
)
def test_bare_safe_names_stay_bare(name: str) -> None:
    assert not needs_quotes(name)
    assert quote_sheet_name(name) == name


@pytest.mark.parametrize(
    ("name", "quoted"),
    [
        ("My Sheet", "'My Sheet'"),
        ("It's", "'It''s'"),
        ("''", "''''''"),
        ("2024", "'2024'"),
        ("1st", "'1st'"),
        (".hidden", "'.hidden'"),
        ("A1", "'A1'"),
        ("xfd1048576", "'xfd1048576'"),
        ("R1C1", "'R1C1'"),
        ("R", "'R'"),
        ("c", "'c'"),
        ("RC", "'RC'"),
        ("R12", "'R12'"),
        ("C3", "'C3'"),
        ("Q1-Q2", "'Q1-Q2'"),
        ("a!b", "'a!b'"),
        ("Sales (EU)", "'Sales (EU)'"),
    ],
)
def test_names_that_need_quotes(name: str, quoted: str) -> None:
    assert needs_quotes(name)
    assert quote_sheet_name(name) == quoted
    assert split_sheet(f"{quoted}!A1") == (name, "A1")


def test_split_without_sheet() -> None:
    assert split_sheet("A1:B2") == (None, "A1:B2")


def test_split_bare_sheet() -> None:
    assert split_sheet("Sheet1!A1") == ("Sheet1", "A1")


def test_split_keeps_bang_inside_quotes() -> None:
    assert split_sheet("'a!b'!C3") == ("a!b", "C3")


@pytest.mark.parametrize(
    "text", ["'abc", "'abc'A1", "''!A1", "!A1", "My Sheet!A1", "Sheet1:Sheet3!A1", "'a''!A1"]
)
def test_split_errors(text: str) -> None:
    with pytest.raises(InvalidReferenceError):
        split_sheet(text)


def test_empty_name_is_rejected() -> None:
    with pytest.raises(InvalidReferenceError):
        quote_sheet_name("")


def test_non_string_is_type_error() -> None:
    with pytest.raises(TypeError):
        split_sheet(None)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        quote_sheet_name(1)  # type: ignore[arg-type]


def test_cell_looking_bare_sheet_parses_and_reprints_quoted() -> None:
    assert str(CellRef.parse("A1!B2")) == "'A1'!B2"
