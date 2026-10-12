# a1col

Spreadsheet A1 references for Python: column letters, cells, ranges, whole rows and
columns, sheet names with correct quoting, and R1C1 conversion. Typed, frozen,
dependency free.

## Install

```
pip install a1col
```

## Usage

```python
from a1col import column_to_index, index_to_column

column_to_index("A")  # 1
column_to_index("AA")  # 27
column_to_index("aa")  # 27, letters are case-insensitive
column_to_index("$C")  # 3, a leading absolute marker is allowed

index_to_column(28)  # "AB"
index_to_column(27)  # "AA"
```

Zero-based variants carry the base in their name:

```python
from a1col import column_to_index0, index0_to_column

column_to_index0("A")  # 0
index0_to_column(26)  # "AA"
```

### Cells, ranges and sheets

```python
from a1col import CellRef, RangeRef, parse_ref

cell = CellRef.parse("'Q1 Sales'!$B3")
cell.column, cell.row  # (2, 3)
cell.sheet  # "Q1 Sales"
str(cell.offset(rows=1, columns=1))  # "'Q1 Sales'!$C4"
str(cell.translate(rows=1, columns=1))  # "'Q1 Sales'!$B4", like copying a formula

rng = RangeRef.parse("A1:C3")
rng.width, rng.height, rng.size  # (3, 3, 9)
CellRef.parse("B2") in rng  # True
str(rng.intersection(RangeRef.parse("B2:D4")))  # "B2:C3"
[str(c) for c in RangeRef.parse("A1:B2")]  # ["A1", "B1", "A2", "B2"]

parse_ref("A:C")  # ColumnSpan(first=1, last=3, ...)
parse_ref("1:3")  # RowSpan(first=1, last=3, ...)
```

### R1C1 and application limits

```python
from a1col import EXCEL, EXCEL_97, CellRef, a1_to_r1c1, r1c1_to_a1

a1_to_r1c1("B3", "A1")  # "R[2]C[1]"
r1c1_to_a1("R[-1]C[2]", "C3")  # "E2"
r1c1_to_a1("R5C3")  # "$C$5"

CellRef.parse("XFD1048576", limits=EXCEL)  # fine, the last Excel cell
CellRef.parse("IW1", limits=EXCEL_97)  # raises OutOfBoundsError
```

Presets: `EXCEL` (16,384 columns to `XFD`, 1,048,576 rows), `EXCEL_97` (256 by
65,536), `LIBREOFFICE` (Calc 7.4 and later, same grid as Excel) and `GOOGLE_SHEETS`
(18,278 columns to `ZZZ`). Without `limits` any positive size is accepted.

### Errors

Every error is a `ValueError` subclass of `A1Error`: `InvalidReferenceError` (with
`InvalidColumnError` and `InvalidRowError` below it) for bad text, and
`OutOfBoundsError` for numbers below one or past the chosen limits.

## Command line

```
$ a1col column AA
27
$ a1col parse "'My Sheet'!A1:C3"
kind: range
a1: 'My Sheet'!A1:C3
sheet: My Sheet
columns: 1..3
rows: 1..3
size: 3 rows x 3 columns = 9 cells
$ a1col cells --by-row A1:B2
A1	B1
A2	B2
$ a1col r1c1 B3 --anchor A1
R[2]C[1]
$ a1col offset B2 --rows 3 --columns -1
A5
```

`a1col --help` lists every command with examples. Results go to stdout; errors go
to stderr with exit code 1.

See [GUIDE.md](GUIDE.md) for every concept and edge case.

## Why

Spreadsheet column letters count in base 26 with no zero, so `Z` is followed by
`AA`, not `BA`. References add absolute markers, sheet names with their own quoting
rules, and a second notation (R1C1) that is relative to the cell holding the
formula. The standard library has no primitive for any of it, and reaching for a
full workbook library just to read `'Q1'!$A$1:C3` pulls in a large dependency. This
package does only that, with no dependencies.

## License

MIT. See [LICENSE](LICENSE).

## Links

- Website: https://lianes8studio.com
- GitHub: https://github.com/JaviLianes8
- LinkedIn: https://www.linkedin.com/in/jlianes/
