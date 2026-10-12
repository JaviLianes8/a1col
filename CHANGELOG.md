# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0]

### Added

- `CellRef`: frozen cell reference with absolute markers, sheet, zero-based views,
  `offset`, `translate` and R1C1 conversion.
- `RangeRef`: cell ranges with bounds, size, row-major iteration, containment,
  `overlaps`, `intersection`, `bounding_box`, `offset` and `translate`.
- `ColumnSpan` and `RowSpan` for whole columns (`A:C`) and rows (`1:3`).
- `parse_ref`, returning the right reference type for any A1 text.
- Sheet quoting helpers: `quote_sheet_name`, `needs_quotes`, `split_sheet`.
- R1C1 conversion relative to an anchor: `a1_to_r1c1`, `r1c1_to_a1`,
  `CellRef.from_r1c1`, `RangeRef.from_r1c1`.
- `SheetLimits` with `EXCEL`, `EXCEL_97`, `LIBREOFFICE` and `GOOGLE_SHEETS`, accepted
  as `limits=` everywhere.
- Zero-based helpers `column_to_index0`, `index0_to_column` and the `is_column`
  predicate.
- Typed errors: `A1Error`, `InvalidReferenceError`, `InvalidColumnError`,
  `InvalidRowError`, `OutOfBoundsError`, all `ValueError` subclasses.
- The `a1col` command line tool: `column`, `parse`, `cells`, `r1c1`, `a1`, `offset`.
- `GUIDE.md`.

### Changed

- `column_to_index` and `index_to_column` accept an optional `limits=` and raise the
  typed errors above (still `ValueError`), or `TypeError` for a wrong argument type.

## [0.1.0]

- Add `column_to_index` and `index_to_column` for A1 column letters and one-based indices.
