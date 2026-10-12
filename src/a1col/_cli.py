"""The ``a1col`` command line tool."""

from __future__ import annotations

import argparse
import errno
import io
import json
import os
import sys
from collections.abc import Iterable, Sequence
from typing import NoReturn

from ._cell import CellRef
from ._columns import column_to_index, index_to_column
from ._describe import describe, describe_text
from ._errors import A1Error
from ._limits import EXCEL, EXCEL_97, GOOGLE_SHEETS, LIBREOFFICE, SheetLimits
from ._parse import parse_ref
from ._r1c1 import a1_to_r1c1, r1c1_to_a1
from ._range import RangeRef

LIMITS: dict[str, SheetLimits | None] = {
    "none": None,
    "excel": EXCEL,
    "excel97": EXCEL_97,
    "libreoffice": LIBREOFFICE,
    "google-sheets": GOOGLE_SHEETS,
}

EXAMPLES = """\
examples:
  a1col column AA                    # 27
  a1col column 27                    # AA
  a1col column --zero-based AA       # 26
  a1col parse "'My Sheet'!\\$A\\$1:C3"   # kind, sheet, bounds and size
  a1col parse --json A1:C3
  a1col cells A1:B2                  # A1, B1, A2, B2, one per line
  a1col cells --by-row A1:C2         # one tab-separated line per row
  a1col --limits excel cells A:A     # whole columns need a grid size
  a1col r1c1 B3 --anchor A1          # R[2]C[1]
  a1col r1c1 A:C                     # C1:C3
  a1col a1 "R[-1]C[2]" --anchor C3   # E2
  a1col offset B2 --rows 3 --columns -1   # A5
  a1col --limits excel97 parse IW1   # error: past column IV, exit 1
"""


class _Parser(argparse.ArgumentParser):
    """Argument parser whose usage errors exit with status 1 like every other error."""

    def error(self, message: str) -> NoReturn:
        self.print_usage(sys.stderr)
        self.exit(1, f"{self.prog}: error: {message}\n")


def build_parser() -> argparse.ArgumentParser:
    """Return the argument parser for the ``a1col`` command."""
    parser = _Parser(
        prog="a1col",
        description="Convert and inspect spreadsheet A1 references.",
        epilog=EXAMPLES,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--limits",
        choices=sorted(LIMITS),
        default="none",
        help="grid to enforce (default: none, any size)",
    )
    sub = parser.add_subparsers(dest="command", required=True, parser_class=_Parser)
    col = sub.add_parser("column", help="column letters to a number, or a number to letters")
    col.add_argument("value", help="letters such as AA, or a number such as 27")
    col.add_argument("--zero-based", action="store_true", help="numbers count from 0")
    parse = sub.add_parser("parse", help="describe any reference")
    parse.add_argument("ref", help="cell, range, whole columns or whole rows")
    parse.add_argument("--json", action="store_true", help="print a JSON object")
    cells = sub.add_parser("cells", help="list every cell of a range, row by row")
    cells.add_argument("ref", help="range such as A1:C3, or whole columns or rows with --limits")
    cells.add_argument("--by-row", action="store_true", help="one tab-separated line per row")
    for name, helptext in (("r1c1", "A1 to R1C1"), ("a1", "R1C1 to A1")):
        conv = sub.add_parser(name, help=helptext)
        conv.add_argument("ref", help="cell, cell range, whole columns or whole rows")
        conv.add_argument("--anchor", help="cell that relative parts are measured from")
    move = sub.add_parser("offset", help="move a cell or range")
    move.add_argument("ref", help="cell or cell range")
    move.add_argument("--rows", type=int, default=0, help="rows to move (negative is up)")
    move.add_argument("--columns", type=int, default=0, help="columns to move (negative is left)")
    move.add_argument(
        "--translate", action="store_true", help="move only relative parts, like copying a formula"
    )
    return parser


def _column(value: str, zero_based: bool, limits: SheetLimits | None) -> str:
    base = 0 if zero_based else 1
    if value.isascii() and value.isdigit():
        return index_to_column(int(value) + 1 - base, limits=limits)
    return str(column_to_index(value, limits=limits) - 1 + base)


def _range_for_cells(ref: str, limits: SheetLimits | None) -> RangeRef:
    parsed = parse_ref(ref, limits=limits)
    if isinstance(parsed, CellRef):
        return RangeRef(parsed, parsed)
    if isinstance(parsed, RangeRef):
        return parsed
    if limits is None:
        raise A1Error(f"whole columns or rows need --limits to know where they end: {ref!r}")
    return parsed.to_range(limits)


def _run(args: argparse.Namespace) -> Iterable[str]:
    limits = LIMITS[args.limits]
    if args.command == "cells":
        rng = _range_for_cells(args.ref, limits)
        if args.by_row:
            return ("\t".join(map(str, row)) for row in rng.rows())
        return map(str, rng.cells())
    return [_run_one(args, limits)]


def _run_one(args: argparse.Namespace, limits: SheetLimits | None) -> str:
    if args.command == "column":
        return _column(args.value, args.zero_based, limits)
    if args.command == "parse":
        ref = parse_ref(args.ref, limits=limits)
        return (
            json.dumps(describe(ref), indent=2, ensure_ascii=False)
            if args.json
            else describe_text(ref)
        )
    if args.command == "r1c1":
        return a1_to_r1c1(args.ref, args.anchor, limits=limits)
    if args.command == "a1":
        return r1c1_to_a1(args.ref, args.anchor, limits=limits)
    target = parse_ref(args.ref, limits=limits)
    if not isinstance(target, (CellRef, RangeRef)):
        raise A1Error(f"offset needs a cell or a cell range: {args.ref!r}")
    mover = target.translate if args.translate else target.offset
    return str(mover(rows=args.rows, columns=args.columns, limits=limits))


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line tool and return its exit status (0 ok, 1 on any error)."""
    args = build_parser().parse_args(argv)
    for stream in (sys.stdout, sys.stderr):
        # Sheet names may hold any character; never crash on a narrow console encoding.
        if isinstance(stream, io.TextIOWrapper):
            stream.reconfigure(errors="backslashreplace")
    try:
        for line in _run(args):
            print(line)
        sys.stdout.flush()
    except (A1Error, TypeError) as exc:
        print(f"a1col: error: {exc}", file=sys.stderr)
        return 1
    except OSError as exc:
        # A reader such as ``head`` closed the pipe early (EINVAL on Windows): not an error.
        if not isinstance(exc, BrokenPipeError) and exc.errno != errno.EINVAL:
            raise
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())
        return 0
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
