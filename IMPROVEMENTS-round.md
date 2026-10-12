# a1col improvement round

A ranked list of substantial, coherent improvements for this round. Every item is
additive: `column_to_index` and `index_to_column` keep their signatures and results,
and every error they raise is still a `ValueError`, so nothing downstream breaks.

## Starting point

Before this round `a1col` converted column letters to one-based indices and back.
There was no notion of a cell, a range, a sheet or an application limit, no
zero-based variant, no R1C1 support, no typed error and no command line entry point.

## Ranked improvements

1. **`CellRef`: a typed, frozen cell reference.** Parse `B3`, `$B$3`, `B$3` or
   `'My Sheet'!B3` into a dataclass holding one-based `column` and `row`, the two
   absolute markers and an optional sheet. It prints back to canonical A1 text, so
   `str(CellRef.parse(text)) == text` for every canonical input. Zero-based views
   (`column0`, `row0`) and `CellRef.from_zero_based` make NumPy and list indexing
   explicit instead of guessed.

2. **`RangeRef`: ranges with real geometry.** `A1:C3` parses into two corners with
   `width`, `height`, `size`, row-major iteration (`cells`, `rows`, `columns`),
   containment (`cell in rng`, `rng.contains(other)`), `overlaps`, `intersection`
   and `bounding_box`. A bare cell parses as a 1x1 range so callers never branch.

3. **Whole columns and whole rows.** `A:C` and `1:3` parse into `ColumnSpan` and
   `RowSpan`, which know their width or height, test containment without any
   limit, and turn into a concrete `RangeRef` with `to_range(limits)`.

4. **Sheet-qualified references with exact quoting rules.** `quote_sheet_name`
   quotes only when needed (spaces, punctuation, a leading digit, a name that looks
   like an A1 or R1C1 reference) and doubles embedded quotes; `split_sheet` reverses
   it. Every reference type carries its sheet and prints it once.

5. **R1C1 <-> A1 relative to an anchor cell.** `to_r1c1(anchor)` writes absolute
   parts as `R5C3` and relative parts as `R[-1]C[2]` offsets from the anchor;
   `from_r1c1(text, anchor)` resolves them back. Works for cells, ranges, whole rows
   (`R2`) and whole columns (`C1:C3`), with
   string helpers `a1_to_r1c1` and `r1c1_to_a1`. Round-trips are exact.

6. **Configurable application limits.** `SheetLimits` with ready presets `EXCEL`
   (16,384 columns to `XFD`, 1,048,576 rows), `EXCEL_97` (256 columns to `IV`,
   65,536 rows), `LIBREOFFICE` (Calc 7.4 and later, same grid as Excel) and
   `GOOGLE_SHEETS` (18,278 columns to `ZZZ`). Every parser takes `limits=` and
   rejects out-of-grid references with a typed error. Default stays unbounded.

7. **Offsetting and moving references.** `offset` shifts a reference as a whole;
   `translate` shifts only its relative parts, which is exactly what a spreadsheet
   does when a formula is copied. Both refuse to leave the grid.

8. **Explicit zero-based column helpers.** `column_to_index0`, `index0_to_column`
   and the `is_column` predicate, so the base is in the name and never implied.

9. **Honest typed errors.** `A1Error` (a `ValueError`) with
   `InvalidReferenceError`, `InvalidColumnError`, `InvalidRowError` and
   `OutOfBoundsError`, each naming the offending text or number.

10. **`parse_ref`: one front door.** Returns a `CellRef`, `RangeRef`, `ColumnSpan`
    or `RowSpan` depending on the text, all sharing `sheet`, `to_a1` and `limits`.

11. **A command line tool.** `a1col column`, `parse` (text or `--json`), `cells`
    (iterate a range, optionally row by row), `r1c1`, `a1` and `offset`, with a
    global `--limits` choice, runnable examples in `--help`, results on stdout and
    errors on stderr with exit code 1.

12. **Documentation and contracts.** Docstrings on every public name, a `GUIDE.md`
    covering each concept and edge case, an exhaustive contract test (every column
    from 1 to 16,384 round-trips, every boundary of every preset, quoting rules),
    an optional cross-check against a well known workbook library when it is
    installed (test only, never a runtime dependency), and a real end to end test
    that builds the wheel, installs it into a throwaway virtual environment and
    drives the installed `a1col` script.

## Out of scope

3D references across several sheets (`Sheet1:Sheet3!A1`), structured table
references and named ranges are rejected with a clear error rather than half
supported.
