import json

import pytest

from a1col._cli import main


def run(capsys: pytest.CaptureFixture[str], *args: str) -> tuple[int, str, str]:
    code = main(list(args))
    out, err = capsys.readouterr()
    return code, out, err


@pytest.mark.parametrize(
    ("args", "expected"),
    [
        (["column", "AA"], "27"),
        (["column", "aa"], "27"),
        (["column", "$C"], "3"),
        (["column", "27"], "AA"),
        (["column", "--zero-based", "AA"], "26"),
        (["column", "--zero-based", "0"], "A"),
        (["--limits", "excel", "column", "16384"], "XFD"),
        (["r1c1", "B3", "--anchor", "A1"], "R[2]C[1]"),
        (["r1c1", "A1:$C$3"], "R1C1:R3C3"),
        (["a1", "R[-1]C[2]", "--anchor", "C3"], "E2"),
        (["a1", "R3C2"], "$B$3"),
        (["r1c1", "A:C"], "C1:C3"),
        (["r1c1", "2:2", "--anchor", "B2"], "R"),
        (["a1", "R2"], "$2:$2"),
        (["a1", "C[1]:C3", "--anchor", "B2"], "C:$C"),
        (["--limits", "excel97", "a1", "R1C256"], "$IV$1"),
        (["offset", "B2", "--rows", "3", "--columns", "-1"], "A5"),
        (["offset", "$B2:C3", "--rows", "1", "--columns", "1", "--translate"], "$B3:D4"),
        (["offset", "'My Sheet'!A1", "--columns", "2"], "'My Sheet'!C1"),
    ],
)
def test_single_line_commands(
    capsys: pytest.CaptureFixture[str], args: list[str], expected: str
) -> None:
    code, out, err = run(capsys, *args)
    assert (code, out, err) == (0, expected + "\n", "")


def test_parse_text(capsys: pytest.CaptureFixture[str]) -> None:
    code, out, _ = run(capsys, "parse", "'My Sheet'!$A$1:C3")
    assert code == 0
    assert "kind: range" in out
    assert "sheet: My Sheet" in out
    assert "size: 3 rows x 3 columns = 9 cells" in out
    for ref, kind in (("B3", "kind: cell"), ("A:C", "kind: columns"), ("2:4", "kind: rows")):
        assert kind in run(capsys, "parse", ref)[1]


def test_parse_json(capsys: pytest.CaptureFixture[str]) -> None:
    code, out, _ = run(capsys, "parse", "--json", "S!$B$2:D4")
    data = json.loads(out)
    assert code == 0
    assert data["kind"] == "range"
    assert data["sheet"] == "S"
    assert data["start"]["column_absolute"] is True
    assert (data["width"], data["height"], data["size"]) == (3, 3, 9)
    cell = json.loads(run(capsys, "parse", "--json", "c7")[1])
    assert (cell["column"], cell["column_letters"], cell["row"], cell["a1"]) == (3, "C", 7, "C7")
    span = json.loads(run(capsys, "parse", "--json", "1:3")[1])
    assert (span["kind"], span["count"], span["sheet"]) == ("rows", 3, None)


def test_cells(capsys: pytest.CaptureFixture[str]) -> None:
    assert run(capsys, "cells", "A1:B2")[1] == "A1\nB1\nA2\nB2\n"
    assert run(capsys, "cells", "C3")[1] == "C3\n"
    assert run(capsys, "cells", "--by-row", "A1:C2")[1] == "A1\tB1\tC1\nA2\tB2\tC2\n"
    assert run(capsys, "--limits", "excel97", "cells", "1:1")[1].count("\n") == 256


@pytest.mark.parametrize(
    "args",
    [
        ["column", "A1"],
        ["column", "0"],
        ["--limits", "excel", "column", "XFE"],
        ["parse", "A1:B"],
        ["--limits", "excel97", "parse", "IW1"],
        ["cells", "A:A"],
        ["a1", "R[1]C"],
        ["r1c1", "A1:B"],
        ["offset", "A1", "--rows", "-1"],
        ["offset", "A:B", "--rows", "1"],
        ["parse", "My Sheet!A1"],
        ["--limits", "excel97", "r1c1", "IW1"],
        ["--limits", "excel97", "a1", "R1C300"],
        ["parse", "'Sheet1:Sheet3'!A1"],
    ],
)
def test_errors_go_to_stderr_with_exit_1(
    capsys: pytest.CaptureFixture[str], args: list[str]
) -> None:
    code, out, err = run(capsys, *args)
    assert code == 1
    assert out == ""
    assert err.startswith("a1col: error: ")


@pytest.mark.parametrize("args", [[], ["bogus"], ["parse"], ["--limits", "mars", "parse", "A1"]])
def test_usage_errors_exit_1(capsys: pytest.CaptureFixture[str], args: list[str]) -> None:
    with pytest.raises(SystemExit) as info:
        main(args)
    assert info.value.code == 1
    assert "usage:" in capsys.readouterr().err


def test_help_has_runnable_examples(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as info:
        main(["--help"])
    assert info.value.code == 0
    out = capsys.readouterr().out
    assert "examples:" in out
    assert "a1col column AA" in out
    assert "--limits" in out


def test_non_ascii_sheet_names(capsys: pytest.CaptureFixture[str]) -> None:
    code, out, err = run(capsys, "parse", "--json", "'日本 Q1'!A1")
    assert (code, err) == (0, "")
    data = json.loads(out)
    assert (data["sheet"], data["a1"]) == ("日本 Q1", "'日本 Q1'!A1")
