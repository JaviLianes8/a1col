"""Typed errors raised by a1col. Every one of them is a ``ValueError``."""

from __future__ import annotations


class A1Error(ValueError):
    """Base class for every error raised by a1col.

    It subclasses ``ValueError`` so code written against the original API, which raised
    plain ``ValueError``, keeps catching everything.
    """


class InvalidReferenceError(A1Error):
    """Text that is not a valid reference: bad syntax, a bad sheet name, mixed kinds."""


class InvalidColumnError(InvalidReferenceError):
    """Text that is not valid column letters (``""``, ``"$"``, ``"A1"``, ``"Ä"``)."""


class InvalidRowError(InvalidReferenceError):
    """Text that is not a valid row number (``""``, ``"0"``, ``"01"``, ``"1.5"``)."""


class OutOfBoundsError(A1Error):
    """A column or row number below one, or beyond the configured ``SheetLimits``."""
