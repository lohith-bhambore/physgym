"""v1's own unit table: spelling -> canonical unit symbol.

Deliberately independent of the generator: no pint, no conversion factors.
v1 never converts (a wrong unit scores 0), so it only needs to recognise spellings.
Canonical names match the strings the generator stores in Problem.answer_unit.
"""
from __future__ import annotations

# Symbols: matched case-sensitively (ms != Ms, m != M). Keys are normalized
# (see normalize_unit): single spaces, no braces, exponents as ^n.
# v1 has already turned \cdot and · into ×, and unicode superscripts into ^n.
_SYMBOLS: dict[str, tuple[str, ...]] = {
    "m": ("m",),
    "cm": ("cm",),
    "km": ("km",),
    "ft": ("ft",),
    "s": ("s",),
    "ms": ("ms",),
    "m/s": ("m/s", "m s^-1", "m*s^-1", "m×s^-1", "m × s^-1"),
    "km/h": ("km/h", "km h^-1", "km/hr", "kph"),
    "m/s^2": ("m/s^2", "m s^-2", "m*s^-2", "m×s^-2", "m × s^-2"),
}

# Words: matched case-insensitively.
_WORDS: dict[str, tuple[str, ...]] = {
    "m": ("meter", "meters", "metre", "metres"),
    "cm": ("centimeter", "centimeters", "centimetre", "centimetres"),
    "km": ("kilometer", "kilometers", "kilometre", "kilometres"),
    "ft": ("foot", "feet"),
    "s": ("sec", "secs", "second", "seconds"),
    "ms": ("millisecond", "milliseconds", "msec", "msecs"),
    "m/s": ("meters per second", "metres per second"),
    "km/h": ("kilometers per hour", "kilometres per hour"),
    "m/s^2": ("meters per second squared", "metres per second squared"),
}

SYMBOL_TABLE: dict[str, str] = {a: canon for canon, aliases in _SYMBOLS.items() for a in aliases}
WORD_TABLE: dict[str, str] = {a: canon for canon, aliases in _WORDS.items() for a in aliases}

CANONICAL: frozenset[str] = frozenset(_SYMBOLS)


def normalize_unit(text: str) -> str:
    """Collapse whitespace, drop braces: 'm s^{-1}' -> 'm s^-1', ' m/s^{2} ' -> 'm/s^2'."""
    return " ".join(text.replace("{", "").replace("}", "").split())


def canonical_unit(text: str) -> str | None:
    """Canonical unit for a spelling, or None if unknown."""
    u = normalize_unit(text)
    if u in SYMBOL_TABLE:
        return SYMBOL_TABLE[u]
    return WORD_TABLE.get(u.lower())
