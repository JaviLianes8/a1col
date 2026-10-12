"""Real end to end test: build the wheel, install it, drive the installed console script.

No mocks. The project is built into a wheel, the wheel is pip-installed into a throwaway
virtual environment, and the real ``a1col`` executable is run over ``subprocess``. The
assertions cover the actual stdout, stderr and exit codes.
"""

from __future__ import annotations

import json
import subprocess
import sys
import venv
from pathlib import Path

import pytest

import a1col

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _exe(env_dir: Path, name: str) -> Path:
    scripts = env_dir / ("Scripts" if sys.platform == "win32" else "bin")
    return scripts / (f"{name}.exe" if sys.platform == "win32" else name)


@pytest.fixture(scope="module")
def a1col_cli(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Build a wheel, install it into a fresh venv and return the console script path."""
    wheel_dir = tmp_path_factory.mktemp("a1col-wheel")
    subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "wheel",
            "--no-deps",
            "-w",
            str(wheel_dir),
            str(PROJECT_ROOT),
        ],
        check=True,
        capture_output=True,
        timeout=600,
    )
    wheels = sorted(wheel_dir.glob("a1col-*.whl"))
    assert len(wheels) == 1, wheels
    env_dir = tmp_path_factory.mktemp("a1col-e2e-venv")
    venv.create(env_dir, with_pip=True)
    subprocess.run(
        [
            str(_exe(env_dir, "python")),
            "-m",
            "pip",
            "install",
            "--quiet",
            "--no-deps",
            str(wheels[0]),
        ],
        check=True,
        capture_output=True,
        timeout=600,
    )
    cli = _exe(env_dir, "a1col")
    assert cli.is_file(), f"console script was not installed at {cli}"
    return cli


def _run(cli: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([str(cli), *args], capture_output=True, text=True, timeout=60)


def test_column_both_ways(a1col_cli: Path) -> None:
    assert _run(a1col_cli, "column", "XFD").stdout.strip() == "16384"
    result = _run(a1col_cli, "column", "16384")
    assert (result.returncode, result.stdout.strip(), result.stderr) == (0, "XFD", "")


def test_parse_json_of_a_quoted_sheet_range(a1col_cli: Path) -> None:
    result = _run(a1col_cli, "parse", "--json", "'It''s Q1'!$A$1:C3")
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert (data["sheet"], data["size"], data["a1"]) == ("It's Q1", 9, "'It''s Q1'!$A$1:C3")


def test_cells_iterates_a_range(a1col_cli: Path) -> None:
    result = _run(a1col_cli, "cells", "--by-row", "A1:B2")
    assert result.stdout.splitlines() == ["A1\tB1", "A2\tB2"]


def test_r1c1_round_trip(a1col_cli: Path) -> None:
    r1c1 = _run(a1col_cli, "r1c1", "B3", "--anchor", "A1").stdout.strip()
    assert r1c1 == "R[2]C[1]"
    assert _run(a1col_cli, "a1", r1c1, "--anchor", "A1").stdout.strip() == "B3"


def test_offset(a1col_cli: Path) -> None:
    assert _run(a1col_cli, "offset", "B2", "--rows", "3", "--columns", "-1").stdout.strip() == "A5"


def test_errors_go_to_stderr_with_exit_1(a1col_cli: Path) -> None:
    result = _run(a1col_cli, "--limits", "excel97", "parse", "IW1")
    assert result.returncode == 1
    assert result.stdout == ""
    assert "257" in result.stderr


def test_help_lists_examples(a1col_cli: Path) -> None:
    result = _run(a1col_cli, "--help")
    assert result.returncode == 0
    assert "examples:" in result.stdout


def test_installed_library_imports_in_the_venv(a1col_cli: Path) -> None:
    python = _exe(a1col_cli.parent.parent, "python")
    code = "import a1col; print(a1col.__version__, a1col.parse_ref('A1:B2').size)"
    result = subprocess.run([str(python), "-c", code], capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stderr
    version, size = result.stdout.split()
    assert size == "4"
    assert version == a1col.__version__
