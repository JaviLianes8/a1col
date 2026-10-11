# a1col

Convert spreadsheet A1 column letters to one-based indices and back.

## Install

```
pip install a1col
```

## Usage

```python
from a1col import column_to_index, index_to_column

column_to_index("A")    # 1
column_to_index("AA")   # 27
column_to_index("aa")   # 27, letters are case-insensitive
column_to_index("$C")   # 3, a leading absolute marker is allowed

index_to_column(28)     # "AB"
index_to_column(27)     # "AA"
```

Invalid input raises `ValueError`: an empty string, a lone marker, anything that
is not letters, or an index below one.

## Why

Spreadsheet column letters count in base 26 with no zero, so `Z` is followed by
`AA`, not `BA`. The standard library has no primitive for it, and reaching for a
full workbook library such as `openpyxl` just to turn `AA` into `27` pulls in a
large dependency for one line. This package does only that, with no dependencies.

## License

MIT. See [LICENSE](LICENSE).

## Links

- Website: https://lianes8studio.com
- GitHub: https://github.com/JaviLianes8
- LinkedIn: https://www.linkedin.com/in/jlianes/
