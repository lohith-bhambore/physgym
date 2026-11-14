"""Tests for grader v0 (naive, on purpose) and v1 (hardened). See notes/SPEC_02_grader.md."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from envs.base import Problem, generate
from envs.projectiles import Projectiles
from grader import GRADERS, grade_v0, grade_v1

LABELS = Path(__file__).resolve().parent.parent / "data" / "labels" / "hand_labeled_replies.jsonl"


def P(value: float, unit: str) -> Problem:
    """A minimal problem whose gold answer is value [unit]. Gold values are hand-written."""
    return Problem(
        id="test",
        family="test",
        template="test",
        difficulty=1,
        question="q",
        answer_value=value,
        answer_unit=unit,
        params={},
        solution_steps=[],
    )


R12 = P(12.0, "m")  # gold: 12 m


def boxed(s: str) -> str:
    return f"Some working here. So the answer is \\boxed{{{s}}}"


# ======================= v1: box extraction =======================


class TestV1Boxes:
    def test_one_box_correct(self):
        assert grade_v1(boxed("12 m"), R12) == 1.0

    def test_no_box(self):
        assert grade_v1("The answer is 12 m.", R12) == 0.0

    def test_two_boxes_both_correct(self):
        assert grade_v1("\\boxed{12 m} and again \\boxed{12 m}", R12) == 0.0

    def test_two_boxes_hedging(self):
        assert grade_v1("\\boxed{12 m} or maybe \\boxed{50 m}", R12) == 0.0

    def test_echoed_instruction_plus_answer(self):
        reply = "I must give \\boxed{value unit}. Final: \\boxed{12 m}"
        assert grade_v1(reply, R12) == 0.0

    @pytest.mark.parametrize("reply", ["\\boxed{}", "\\boxed{ }", "\\boxed{\\,}"])
    def test_empty_box(self, reply):
        assert grade_v1(reply, R12) == 0.0

    def test_unbalanced_braces(self):
        assert grade_v1("\\boxed{12 m", R12) == 0.0

    def test_box_without_braces(self):
        assert grade_v1("\\boxed 12 m", R12) == 0.0

    def test_nested_braces(self):
        assert grade_v1("\\boxed{1.2 \\times 10^{1}\\,\\text{m}}", R12) == 1.0

    def test_box_inside_math_mode(self):
        assert grade_v1("$$\\boxed{12\\ \\mathrm{m}}$$", R12) == 1.0

    def test_dollars_inside_box(self):
        assert grade_v1("\\boxed{$12$ m}", R12) == 1.0


# ======================= v1: box contents =======================


class TestV1Contents:
    @pytest.mark.parametrize(
        "content",
        [
            "12",  # bare number, no unit
            "m",  # unit, no number
            "12-13 m",  # range
            "12 m or 13 m",  # hedge inside one box
            "12 or 13 m",
            "12 m = 1200 cm",
            "\\frac{24}{2} m",
            "12 m (approx)",
            "about 12 m",
            "12 13 m",
            "12 m 13",
        ],
    )
    def test_rejected(self, content):
        assert grade_v1(boxed(content), R12) == 0.0


# ======================= v1: symbol prefix =======================


class TestV1SymbolPrefix:
    @pytest.mark.parametrize(
        "content",
        [
            "R = 12 m",
            "R=12m",
            "R ≈ 12 m",
            "R \\approx 12 m",
            "R \\approx 12\\,\\text{m}",
            "h_{max} = 12 m",
            "h_{\\text{max}} = 12 m",
            "x_1 = 12 m",  # subscript digit is part of the symbol, not a second number
            "\\Delta x = 12 m",
        ],
    )
    def test_accepted(self, content):
        assert grade_v1(boxed(content), R12) == 1.0

    @pytest.mark.parametrize(
        "content",
        [
            "R = 12 m = 1200 cm",  # two numbers
            "R = 12 m ≈ 12.0 m",
            "12 m = R",  # symbol on the wrong side
            "2R = 24 m",  # coefficient is a second number
            "R = 2 \\cdot 6 m",  # an expression, not a number
            "R_{12} 12 m",  # no relation sign
            "R = = 12 m",
            "d = ≈ 12 m",
            "the range R = 12 m",  # words before the symbol
        ],
    )
    def test_rejected(self, content):
        assert grade_v1(boxed(content), R12) == 0.0


# ======================= v1: number formats =======================


class TestV1Numbers:
    @pytest.mark.parametrize(
        "content,gold",
        [
            ("12 m", 12.0),
            ("12.0 m", 12.0),
            (".5 m", 0.5),
            ("-3.5 m", -3.5),
            ("−3.5 m", -3.5),  # unicode minus
            ("+12 m", 12.0),
            ("1.2e3 m", 1200.0),
            ("1.2E+03 m", 1200.0),
            ("1.2e-3 m", 0.0012),
            ("1.2×10^3 m", 1200.0),
            ("1.2 × 10^3 m", 1200.0),
            ("1.2×10³ m", 1200.0),
            ("1.2×10⁻³ m", 0.0012),
            ("1.2 \\times 10^{3} m", 1200.0),
            ("1.2 \\times 10^{-3} m", 0.0012),
            ("1.2 \\cdot 10^3 m", 1200.0),
            ("1.2·10^3 m", 1200.0),
            ("1,234.5 m", 1234.5),
            ("1,234,567 m", 1234567.0),
            ("1 234 m", None),  # space-separated groups are not supported -> 0
        ],
    )
    def test_formats(self, content, gold):
        if gold is None:
            assert grade_v1(boxed(content), P(1234.0, "m")) == 0.0
        else:
            assert grade_v1(boxed(content), P(gold, "m")) == 1.0

    @pytest.mark.parametrize("content", ["1,5 m", "12,34 m", "1,2345 m", ",123 m", "1.2.3 m", "1e m", "10^3 m"])
    def test_bad_numbers(self, content):
        # gold chosen so any lenient reading would be "right"
        for gold in (1.5, 1234.0, 12.345, 123.0, 1.2, 1.0, 1000.0, 15.0):
            assert grade_v1(boxed(content), P(gold, "m")) == 0.0

    def test_infinite_number(self):
        assert grade_v1(boxed("1e999 m"), R12) == 0.0


# ======================= v1: prefix / suffix / LaTeX =======================


class TestV1Wrapping:
    @pytest.mark.parametrize(
        "content",
        [
            "≈ 12 m",
            "≈12 m",
            "\\approx 12 m",
            "12 m.",
            "12 m,",
            "12 m;",
            "12\\,\\text{m}",
            "12\\;\\mathrm{m}",
            "12~m",
            "12\\ m",
            "12\\text{ m}",
            "12 \\text{m}.",
            "\\mathrm{12\\ m}",
            "  12 m  ",
        ],
    )
    def test_accepted(self, content):
        assert grade_v1(boxed(content), R12) == 1.0

    @pytest.mark.parametrize("content", ["12 m!", "12 m.)", "~~12 m??", "12 m :)", "<12 m", "> 12 m"])
    def test_rejected(self, content):
        assert grade_v1(boxed(content), R12) == 0.0


# ======================= v1: units =======================


class TestV1Units:
    @pytest.mark.parametrize(
        "content,gold,unit",
        [
            ("12 meters", 12.0, "m"),
            ("12 metres", 12.0, "m"),
            ("12 meter", 12.0, "m"),
            ("12 Meters", 12.0, "m"),  # words are case-insensitive
            ("3 s", 3.0, "s"),
            ("3 seconds", 3.0, "s"),
            ("3 sec", 3.0, "s"),
            ("300 ms", 300.0, "ms"),
            ("300 milliseconds", 300.0, "ms"),
            ("40 ft", 40.0, "ft"),
            ("40 feet", 40.0, "ft"),
            ("50 cm", 50.0, "cm"),
            ("2 km", 2.0, "km"),
            ("12 m/s", 12.0, "m/s"),
            ("12 \\text{m/s}", 12.0, "m/s"),
            ("12 m s^{-1}", 12.0, "m/s"),
            ("9.81 m/s^2", 9.81, "m/s^2"),
            ("9.81 m/s²", 9.81, "m/s^2"),
            ("9.81 \\mathrm{m/s^{2}}", 9.81, "m/s^2"),
            ("36 km/h", 36.0, "km/h"),
        ],
    )
    def test_aliases(self, content, gold, unit):
        assert grade_v1(boxed(content), P(gold, unit)) == 1.0

    @pytest.mark.parametrize(
        "content,gold,unit",
        [
            ("12 km", 12.0, "m"),  # right number, wrong unit
            ("12 cm", 12.0, "m"),
            ("0.012 km", 12.0, "m"),  # right quantity, wrong unit
            ("1200 cm", 12.0, "m"),
            ("12 ft", 12.0, "m"),
            ("0.3 s", 300.0, "ms"),
            ("300 s", 300.0, "ms"),
            ("12 M", 12.0, "m"),  # symbols are case-sensitive
            ("300 Ms", 300.0, "ms"),
            ("300 MS", 300.0, "ms"),
            ("12 m/s", 12.0, "m"),
            ("12 furlongs", 12.0, "m"),  # unknown unit
            ("12 m m", 12.0, "m"),
        ],
    )
    def test_wrong_unit(self, content, gold, unit):
        assert grade_v1(boxed(content), P(gold, unit)) == 0.0

    def test_unknown_answer_unit_raises(self):
        with pytest.raises(ValueError):
            grade_v1(boxed("12 furlongs"), P(12.0, "furlong"))


# ======================= v1: tolerance =======================


class TestV1Tolerance:
    def test_exact(self):
        assert grade_v1(boxed("100 m"), P(100.0, "m")) == 1.0

    def test_09_percent_high(self):
        assert grade_v1(boxed("100.9 m"), P(100.0, "m")) == 1.0

    def test_09_percent_low(self):
        assert grade_v1(boxed("99.1 m"), P(100.0, "m")) == 1.0

    def test_15_percent_high(self):
        assert grade_v1(boxed("101.5 m"), P(100.0, "m")) == 0.0

    def test_15_percent_low(self):
        assert grade_v1(boxed("98.5 m"), P(100.0, "m")) == 0.0

    def test_wrong_sign(self):
        assert grade_v1(boxed("-100 m"), P(100.0, "m")) == 0.0

    def test_rtol_is_a_parameter(self):
        assert grade_v1(boxed("101.5 m"), P(100.0, "m"), rtol=0.02) == 1.0
        assert grade_v1(boxed("100.5 m"), P(100.0, "m"), rtol=0.001) == 0.0

    def test_default_rtol_is_one_percent(self):
        import inspect

        assert inspect.signature(grade_v1).parameters["rtol"].default == 0.01

    def test_returns_float(self):
        assert type(grade_v1(boxed("12 m"), R12)) is float
        assert type(grade_v1("nothing", R12)) is float


# ======================= v1: independence from the generator =======================


def test_v1_does_not_import_generator_or_pint():
    code = (
        "import sys, grader.v1; "
        "bad = [m for m in ('envs.projectiles', 'pint') if m in sys.modules]; "
        "assert not bad, bad"
    )
    root = Path(__file__).resolve().parent.parent
    r = subprocess.run([sys.executable, "-c", code], cwd=root, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr


# ======================= v1: real generated problems =======================


def _fmt_variants(v: float, u: str) -> list[str]:
    mant, exp = f"{v:.4e}".split("e")
    exp_i = int(exp)
    return [
        f"\\boxed{{{v:.4g} {u}}}",
        f"\\boxed{{{v:.5f}\\,\\text{{{u}}}}}",
        f"\\boxed{{{v:.3e} \\mathrm{{{u}}}}}",
        f"\\boxed{{{mant} \\times 10^{{{exp_i}}}\\ {u}}}",
        f"\\boxed{{x \\approx {v:.4g} {u}}}.",
        f"Working... $$\\boxed{{{v:,.3f} {u}}}$$",
    ]


@pytest.mark.parametrize("difficulty", [1, 2, 3, 4])
def test_v1_accepts_real_generated_answers(difficulty):
    problems = generate(Projectiles(), n=50, difficulty=difficulty, seed=7)
    for p in problems:
        for reply in _fmt_variants(p.answer_value, p.answer_unit):
            assert grade_v1(reply, p) == 1.0, (p.id, reply)
        # same digits, another unit -> 0
        other = "km" if p.answer_unit != "km" else "m"
        assert grade_v1(f"\\boxed{{{p.answer_value:.4g} {other}}}", p) == 0.0
        # 1.5% off -> 0
        assert grade_v1(f"\\boxed{{{p.answer_value * 1.015:.6g} {p.answer_unit}}}", p) == 0.0


# ======================= v0: naive grader, holes documented =======================


class TestV0Naive:
    """v0 is naive ON PURPOSE. These tests pin down its holes so the audit can measure them."""

    def test_correct_answer(self):
        assert grade_v0(boxed("12 m"), R12) == 1.0

    def test_default_rtol_is_five_percent(self):
        import inspect

        assert inspect.signature(grade_v0).parameters["rtol"].default == 0.05

    def test_takes_first_number(self):
        assert grade_v0("Using v = 20 m/s ... \\boxed{12 m}", R12) == 0.0

    def test_no_number(self):
        assert grade_v0("I don't know.", R12) == 0.0

    # ---- holes: v0 says 1, v1 says 0 ----
    HACKS = [
        ("two boxes", "\\boxed{12 m} or \\boxed{50 m}"),
        ("right number wrong unit", "\\boxed{12 km}"),
        ("no unit", "\\boxed{12}"),
        ("no box at all", "12"),
        ("hedge in one box", "\\boxed{12 m or 13 m}"),
        ("4% off", "\\boxed{12.48 m}"),
        ("echoed instruction", "\\boxed{12 m} as required by \\boxed{value unit}"),
    ]

    @pytest.mark.parametrize("name,reply", HACKS, ids=[h[0] for h in HACKS])
    def test_hole_v0_fooled_v1_not(self, name, reply):
        assert grade_v0(reply, R12) == 1.0, f"v0 should be fooled by: {name}"
        assert grade_v1(reply, R12) == 0.0, f"v1 should reject: {name}"


def test_graders_registry():
    assert GRADERS == {"v0": grade_v0, "v1": grade_v1}


# ======================= hand-labeled replies =======================


def _load_labels() -> list[dict]:
    if not LABELS.exists():
        return []
    return [json.loads(line) for line in LABELS.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_hand_labels_file_exists():
    assert LABELS.exists()


def test_v1_agrees_with_hand_labels():
    rows = _load_labels()
    if not rows:
        pytest.skip("no hand-labeled replies yet")
    wrong = []
    for i, row in enumerate(rows):
        assert set(row) >= {"reply", "answer_value", "answer_unit", "label"}, f"row {i} missing keys"
        assert row["label"] in (0, 1), f"row {i} label must be 0 or 1"
        got = grade_v1(row["reply"], P(float(row["answer_value"]), row["answer_unit"]))
        if got != row["label"]:
            wrong.append((i, row.get("note", ""), row["label"], got))
    assert not wrong, f"v1 disagrees with {len(wrong)}/{len(rows)} hand labels: {wrong}"
