# a1col guide

Everything `a1col` understands, with the exact rules it applies. All examples run as
written.

## Columns

Column letters count in bijective base 26: `A` is 1, `Z` is 26, `AA` is 27, `XFD`
is 16,384. Letters are ASCII and case-insensitive, and one leading `$` is allowed.

| Function | Base | Example |
| --- | --- | --- |
| `column_to_index` | one-based | `column_to_index("AA") == 27` |
| `index_to_column` | one-based | `index_to_column(27) == "AA"` |
| `column_to_index0` | zero-based | `column_to_index0("AA") == 26` |
| `index0_to_column` | zero-based | `index0_to_column(26) == "AA"` |
| `is_column` | n/a | `is_column("$xfd") is True`, never raises |

Each conversion takes an optional `limits=`. Without it any length is accepted.
Indexes may be any integer type, NumPy integers included (anything with
`__index__`).

## Cells: `CellRef`

```python
from a1col import CellRef

cell = CellRef.parse("$B3")
cell.column, cell.row  # (2, 3), one-based
cell.column_absolute, cell.row_absolute  # (True, False)
cell.column0, cell.row0  # (1, 2), zero-based views
CellRef.from_zero_based(column=1, row=2)  # B3
```

Rules: letters then digits, an optional `$` before each. Rows are ASCII digits with
no sign and no leading zero (`A0` and `A01` are rejected). Printing gives canonical
text, so `str(CellRef.parse(text)) == text` whenever `text` is already canonical
(upper-case letters, sheet quoted only when needed).

`absolute()` and `relative()` set or clear both markers. `with_sheet(name)` adds or
removes a sheet. Every `CellRef` is a frozen, hashable dataclass that compares by
value, markers and sheet included.

## Moving references

* `offset(rows=, columns=)` moves the whole reference: `$B$3` by (1, 1) is `$C$4`.
* `translate(rows=, columns=)` moves only relative parts, which is what a
  spreadsheet does to a formula copied to another cell: `$B3` by (1, 1) is `$B4`.

Both raise `OutOfBoundsError` instead of producing row 0, column 0 or a cell past
`limits`. `RangeRef` offers the same two moves with the same keywords. `ColumnSpan`
and `RowSpan` move along their own axis only: `ColumnSpan.offset(columns)`,
`ColumnSpan.translate(columns)`, `RowSpan.offset(rows)` and `RowSpan.translate(rows)`.

## Ranges: `RangeRef`

```python
from a1col import CellRef, RangeRef

rng = RangeRef.parse("C3:A1")
str(rng)  # "C3:A1", corners kept as written
str(rng.normalized())  # "A1:C3"
rng.min_column, rng.max_column, rng.min_row, rng.max_row  # (1, 3, 1, 3)
rng.width, rng.height, rng.size  # (3, 3, 9)
```

* A single cell parses as a 1x1 range, so `RangeRef.parse("B2")` always works.
* Iteration is row by row: `list(rng)`, `rng.cells()`, `rng.rows()` (one tuple
  per row) and `rng.columns()` (one tuple per column). Cells come back relative.
* `cell in rng`, `rng.contains(other_range)`, `rng.overlaps(other)`,
  `rng.intersection(other)` (or `None`) and `rng.bounding_box(other)`.
* Sheets: a reference with no sheet matches any sheet; two different sheets never
  overlap and cannot be bounded together.

## Whole columns and rows: `ColumnSpan`, `RowSpan`

`A:C` and `$1:$3` describe whole columns and rows. They need no limits to answer
`count`, containment (`cell in span`) or `letters()`. To get concrete cells call
`to_range(limits)`, which defaults to the Excel grid:

```python
from a1col import EXCEL_97, ColumnSpan

str(ColumnSpan.parse("A:C").to_range())  # "A1:C1048576"
str(ColumnSpan.parse("A:C").to_range(EXCEL_97))  # "A1:C65536"
```

The corners of `to_range` come back relative, whatever markers the span had.

## One front door: `parse_ref`

`parse_ref(text)` returns a `CellRef`, `RangeRef`, `ColumnSpan` or `RowSpan`
depending on the text. Mixed forms such as `A1:C` or `A:3` are rejected.

## Sheet names and quoting

A sheet name stays bare only when it is letters, digits, underscores and dots, does
not start with a digit or dot, and does not read as a reference itself. Anything
else is wrapped in single quotes and every quote inside is doubled.

| Name | Written as |
| --- | --- |
| `Sheet1` | `Sheet1!A1` |
| `My Sheet` | `'My Sheet'!A1` |
| `It's` | `'It''s'!A1` |
| `2024` | `'2024'!A1` |
| `A1`, `R1C1`, `C3` | `'A1'!A1`, `'R1C1'!A1`, `'C3'!A1` |

`quote_sheet_name`, `needs_quotes` and `split_sheet` expose these rules. Parsing
accepts quoted names containing anything except `:`, including `!`. Parsing is
lenient about one thing: a bare name that would need quotes only because it reads
as a reference (`A1!B2`) is accepted, and printed back quoted (`'A1'!B2`).
Three-dimensional references (`Sheet1:Sheet3!A1`, `'Sheet 1:Sheet 3'!A1`) are
rejected, and no sheet name may contain `:`. Other application-specific rules, such
as the 31 character limit in Excel, are not enforced.

## R1C1 notation

R1C1 writes absolute parts as numbers and relative parts as offsets in brackets from
the cell that holds the formula (the anchor):

| A1 (anchor `C3`) | R1C1 |
| --- | --- |
| `C3` | `RC` |
| `B2` | `R[-1]C[-1]` |
| `$C$3` | `R3C3` |
| `$A5` | `R[2]C1` |

```python
from a1col import CellRef, a1_to_r1c1, r1c1_to_a1

a1_to_r1c1("A1:$C$3", "B2")  # "R[-1]C[-1]:R3C3"
r1c1_to_a1("R[-1]C:R1C[2]", "B2")  # "B1:D$1"
CellRef.from_r1c1("R[-1]C[2]", CellRef.parse("C3"))  # E2
```

Whole rows and columns work too: `R2` is row 2, `R[-1]:R1` a block of rows, `C3`
column C, and a lone `R` or `C` the anchor's own row or column.

```python
from a1col import a1_to_r1c1, r1c1_to_a1

a1_to_r1c1("A:C")  # "C1:C3"
a1_to_r1c1("$2:$2")  # "R2"
r1c1_to_a1("C[1]:C3", "B2")  # "C:$C"
```

Rules: letters `R` and `C` are case-insensitive; inside a reference a bare `R` or
`C` means offset 0 (`RC`, `R1C`, `RC1`); offsets are signed integers without a `+`
and without leading zeros. `a1_to_r1c1` and `r1c1_to_a1` take `limits=` like the
parsers. Absolute parts
come back with `$` markers. Parsing a relative part without an anchor raises
`InvalidReferenceError`; converting to R1C1 without an anchor writes every part as
an absolute number. With an anchor, conversions round-trip exactly.

## Application limits

| Preset | Columns | Rows |
| --- | --- | --- |
| `EXCEL` | 16,384 (`XFD`) | 1,048,576 |
| `EXCEL_97` | 256 (`IV`) | 65,536 |
| `LIBREOFFICE` | 16,384 (`XFD`), Calc 7.4 and later | 1,048,576 |
| `GOOGLE_SHEETS` | 18,278 (`ZZZ`) | 10,000,000 (no fixed row limit; derived from the 10 million cell cap) |

Define your own with `SheetLimits("Mine", max_columns, max_rows)`. Pass any of them
as `limits=` to parsers and movers, or use `check_column`, `check_row`, `contains`
and `last_column` directly.

## Errors

```
ValueError
  A1Error
    InvalidReferenceError     bad text or sheet, mixed forms
      InvalidColumnError      bad column letters
      InvalidRowError         bad row number
    OutOfBoundsError          below one, or past the limits
```

Passing a non-string where text is expected, or a non-integer where a number is
expected, raises `TypeError`. An invalid `SheetLimits` raises `A1Error`.

## Command line

```
a1col [--limits {none,excel,excel97,libreoffice,google-sheets}] COMMAND
```

| Command | Does |
| --- | --- |
| `column VALUE [--zero-based]` | letters to a number, or a number to letters |
| `parse REF [--json]` | kind, sheet, canonical text, bounds and size |
| `cells REF [--by-row]` | every cell of a range; whole spans need `--limits` |
| `r1c1 REF [--anchor CELL]` | A1 to R1C1, whole columns and rows included |
| `a1 REF [--anchor CELL]` | R1C1 to A1, whole columns and rows included |
| `offset REF --rows N --columns N [--translate]` | move a cell or range |

`--limits` applies to every command. Results print to stdout with exit code 0. Every error prints `a1col: error: ...` to
stderr with exit code 1, usage errors included.
