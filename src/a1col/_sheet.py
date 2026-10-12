"""Sheet-name quoting and the ``Sheet!Ref`` prefix."""

from __future__ import annotations

import re

from ._errors import InvalidReferenceError

# A name that may stand unquoted: word characters and dots, not starting with a digit.
_BARE = re.compile(r"[^\W\d][\w.]*")
# Names that would read as a reference if left bare, so they must be quoted.
_LOOKS_A1 = re.compile(r"[A-Za-z]{1,3}[0-9]+", re.ASCII)
_LOOKS_R1C1 = re.compile(r"[Rr][0-9]*([Cc][0-9]*)?|[Cc][0-9]*", re.ASCII)


def _check_name(name: str) -> None:
    if not isinstance(name, str):
        raise TypeError(f"sheet name must be a str, got {type(name).__name__}")
    if not name:
        raise InvalidReferenceError("sheet name must not be empty")


def needs_quotes(name: str) -> bool:
    """Return whether ``name`` has to be wrapped in single quotes before a ``!``.

    A name may stay bare only when it is made of letters, digits, underscores and dots,
    does not start with a digit or a dot, and does not itself read as an A1 reference
    (``AB12``) or an R1C1 reference (``R1C1``, ``R``, ``C3``).
    """
    _check_name(name)
    if _BARE.fullmatch(name) is None:
        return True
    return bool(_LOOKS_A1.fullmatch(name) or _LOOKS_R1C1.fullmatch(name))


def quote_sheet_name(name: str) -> str:
    """Return ``name`` ready to sit before ``!``: quoted with ``'`` only when required.

    Embedded single quotes are doubled inside the quotes, so ``It's`` becomes
    ``'It''s'``. A bare-safe name such as ``Sheet1`` is returned unchanged.

    Raises:
        InvalidReferenceError: the name is empty.
    """
    if not needs_quotes(name):
        return name
    return "'" + name.replace("'", "''") + "'"


def split_sheet(text: str) -> tuple[str | None, str]:
    """Split ``"'My Sheet'!A1"`` into ``("My Sheet", "A1")``; no prefix gives ``None``.

    Quoted names have their doubled quotes collapsed. A bare name must be made of
    letters, digits, underscores and dots. Only the part before the first ``!`` outside
    quotes is treated as the sheet; the remainder is returned untouched.

    Raises:
        InvalidReferenceError: an unterminated quote, a quoted name not followed by
            ``!``, an empty name, or a bare name with characters that need quoting.
    """
    if not isinstance(text, str):
        raise TypeError(f"reference must be a str, got {type(text).__name__}")
    if text.startswith("'"):
        return _split_quoted(text)
    bang = text.find("!")
    if bang < 0:
        return None, text
    name, rest = text[:bang], text[bang + 1 :]
    _check_name(name)
    if ":" in name:
        raise InvalidReferenceError(f"3D references are not supported: {text!r}")
    if _BARE.fullmatch(name) is None:
        raise InvalidReferenceError(f"sheet name {name!r} must be quoted: {text!r}")
    return name, rest


def _split_quoted(text: str) -> tuple[str, str]:
    chars: list[str] = []
    i = 1
    while i < len(text):
        char = text[i]
        if char == "'":
            if text.startswith("''", i):
                chars.append("'")
                i += 2
                continue
            if not text.startswith("!", i + 1):
                raise InvalidReferenceError(f"quoted sheet name must be followed by '!': {text!r}")
            name = "".join(chars)
            _check_name(name)
            return name, text[i + 2 :]
        chars.append(char)
        i += 1
    raise InvalidReferenceError(f"unterminated quoted sheet name: {text!r}")


def with_sheet_prefix(sheet: str | None, body: str) -> str:
    """Return ``body`` prefixed by the quoted ``sheet`` and ``!``, or alone if no sheet."""
    return body if sheet is None else f"{quote_sheet_name(sheet)}!{body}"
