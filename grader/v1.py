"""Grader v1 (hardened). See notes/SPEC_02_grader.md.

reply -> exactly one \\boxed{...} -> whole box is "[symbol =|≈] [≈] NUMBER UNIT [.,;]"
      -> unit (own alias table) == asked unit -> |x - gold| <= rtol * |gold|
Anything that doesn't fit scores 0. Imports only Problem from the env package.
"""
from __future__ import annotations

import math
import re

from envs.base import Problem
from grader.units import canonical_unit

# ---------- 1. box extraction ----------

_BOXED = re.compile(r"\\boxed(?![A-Za-z])")


def extract_single_box(reply: str) -> str | None:
    """Contents of the only \\boxed{...} in reply, or None if there are 0 or 2+ or it is malformed."""
    hits = list(_BOXED.finditer(reply))
    if len(hits) != 1:
        return None
    i = hits[0].end()
    while i < len(reply) and reply[i].isspace():
        i += 1
    if i >= len(reply) or reply[i] != "{":
        return None
    depth = 0
    for j in range(i, len(reply)):
        if reply[j] == "{":
            depth += 1
        elif reply[j] == "}":
            depth -= 1
            if depth == 0:
                return reply[i + 1 : j]
    return None  # unbalanced


# ---------- 2. normalization ----------

_TEXT_WRAPPERS = re.compile(r"\\(?:text|mathrm|textrm|mathit|operatorname)\s*\{((?:[^{}]|\{[^{}]*\})*)\}")
_SPACES = re.compile(r"\\[,;:!]|\\ |\\quad|\\qquad|~")
_SUPERSCRIPT = re.compile(r"[⁰¹²³⁴⁵⁶⁷⁸⁹⁻⁺]+")
_SUP_TO_ASCII = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹⁻⁺", "0123456789-+")


def normalize(s: str) -> str:
    s = s.replace("$", "")
    prev = None
    while prev != s:  # unwrap nested \text{...}
        prev, s = s, _TEXT_WRAPPERS.sub(r"\1", s)
    s = _SPACES.sub(" ", s)
    s = s.replace("\\approx", "≈").replace("\\times", "×").replace("\\cdot", "×").replace("·", "×")
    s = s.replace("−", "-")  # unicode minus
    s = _SUPERSCRIPT.sub(lambda m: "^" + m.group().translate(_SUP_TO_ASCII), s)
    return s.strip()


# ---------- 3. box grammar ----------

_SYMBOL = r"(?:\\[A-Za-z]+(?:\s*[A-Za-z])?|[A-Za-z])(?:_(?:\{[^{}]*\}|[A-Za-z0-9]))?"
_NUMBER = (
    r"(?P<sign>[-+])?"
    r"(?P<mant>(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?|\.\d+)"
    r"(?:[eE](?P<e1>[-+]?\d+)|\s*×\s*10\s*\^\s*\{?\s*(?P<e2>[-+]?\d+)\s*\}?)?"
)
_BOX = re.compile(
    rf"^(?:{_SYMBOL}\s*[=≈]\s*|≈\s*)?{_NUMBER}\s*(?P<unit>[^\d\s.,;].*?)\s*[.,;]?$"
)


def parse_box(content: str) -> tuple[float, str] | None:
    """(value, unit spelling) if the box is exactly one number + one unit, else None."""
    m = _BOX.match(normalize(content))
    if m is None:
        return None
    exp = m.group("e1") or m.group("e2") or "0"
    value = float(f"{m.group('sign') or ''}{m.group('mant').replace(',', '')}e{exp}")
    return value, m.group("unit")


# ---------- 4. grade ----------


def grade(reply: str, problem: Problem, rtol: float = 0.01) -> float:
    asked = canonical_unit(problem.answer_unit)
    if asked is None:
        raise ValueError(f"grader v1 has no table entry for answer unit {problem.answer_unit!r}")
    content = extract_single_box(reply)
    if content is None:
        return 0.0
    parsed = parse_box(content)
    if parsed is None:
        return 0.0
    value, unit = parsed
    if canonical_unit(unit) != asked or not math.isfinite(value):
        return 0.0
    gold = problem.answer_value
    return 1.0 if abs(value - gold) <= rtol * abs(gold) else 0.0
