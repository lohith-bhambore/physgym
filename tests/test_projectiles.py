import math

import numpy as np
import pint
import pytest

from envs.base import Problem, generate
from envs.projectiles import (
    G,
    TEMPLATES,
    Projectiles,
    cliff_range,
    cliff_time,
    max_height,
    projectile_range,
    solve,
    time_of_flight,
)

ureg = pint.UnitRegistry()
FAMILY = Projectiles()


# ---------- 1. determinism ----------

def test_same_seed_gives_identical_problems():
    a = generate(FAMILY, 20, 3, seed=7)
    b = generate(FAMILY, 20, 3, seed=7)
    assert a == b


def test_different_seeds_give_different_problems():
    a = generate(FAMILY, 20, 3, seed=1)
    b = generate(FAMILY, 20, 3, seed=2)
    assert a != b


def test_generate_returns_problem_objects_with_requested_difficulty():
    probs = generate(FAMILY, 5, 2, seed=0)
    assert len(probs) == 5
    assert all(isinstance(p, Problem) and p.difficulty == 2 for p in probs)
    assert all(p.family == "projectiles" for p in probs)


def test_ids_are_unique_within_a_batch():
    probs = generate(FAMILY, 200, 1, seed=0)
    assert len({p.id for p in probs}) == 200


# ---------- 2. physics sanity ----------

@pytest.mark.parametrize("theta", [15, 30, 40, 60])
def test_range_equal_for_complementary_angles(theta):
    assert projectile_range(25.0, theta) == pytest.approx(projectile_range(25.0, 90 - theta))


def test_max_height_is_maximal_at_90_degrees():
    heights = [max_height(30.0, th) for th in range(15, 91)]
    assert max(heights) == pytest.approx(max_height(30.0, 90))
    assert heights.index(max(heights)) == len(heights) - 1


def test_max_height_grows_with_v_squared():
    assert max_height(20.0, 45) / max_height(10.0, 45) == pytest.approx(4.0)


@pytest.mark.parametrize("v,theta", [(10.0, 30), (37.5, 62), (5.0, 15)])
def test_time_of_flight_times_horizontal_speed_equals_range(v, theta):
    horizontal = v * math.cos(math.radians(theta))
    assert time_of_flight(v, theta) * horizontal == pytest.approx(projectile_range(v, theta))


@pytest.mark.parametrize("H", [5.0, 20.0, 100.0])
def test_cliff_time_equals_sqrt_2H_over_g(H):
    assert cliff_time(H) == pytest.approx(math.sqrt(2 * H / G))


def test_cliff_range_is_speed_times_fall_time():
    assert cliff_range(12.0, 45.0) == pytest.approx(12.0 * cliff_time(45.0))


def test_g_is_9_81():
    assert G == 9.81


# ---------- known values (independent hand calculation) ----------

def test_known_values():
    # v=20, theta=30: v sin = 10 -> h = 100/(2*9.81)
    assert max_height(20.0, 30) == pytest.approx(100 / (2 * 9.81))
    assert time_of_flight(20.0, 30) == pytest.approx(20 / 9.81)
    # v=20, theta=45 -> R = 400/9.81
    assert projectile_range(20.0, 45) == pytest.approx(400 / 9.81)


# ---------- 3. units ----------

def _answer_in_si(p: Problem) -> float:
    """Recompute the gold answer from params (SI) via the formulas."""
    return solve(p.template, p.params)


@pytest.mark.parametrize("difficulty", [2, 3, 4])
def test_params_reproduce_answer_value_via_pint(difficulty):
    for p in generate(FAMILY, 300, difficulty, seed=11):
        si_unit = {"max_height": "m", "range": "m", "from_cliff": "m", "time_of_flight": "s"}[p.template]
        expected = (_answer_in_si(p) * ureg(si_unit)).to(p.answer_unit).magnitude
        assert p.answer_value == pytest.approx(expected, rel=1e-9)


def test_answer_unit_is_pint_parsable_at_all_levels():
    for d in range(1, 5):
        for p in generate(FAMILY, 100, d, seed=3):
            ureg(p.answer_unit)  # must not raise


def test_level_1_is_si_in_and_out():
    for p in generate(FAMILY, 200, 1, seed=5):
        assert p.answer_unit in ("m", "s")
        assert p.answer_value == pytest.approx(_answer_in_si(p), rel=1e-12)
        assert "km/h" not in p.question and " cm" not in p.question and " ft" not in p.question


def test_level_2_uses_mixed_input_units_but_si_answer():
    probs = generate(FAMILY, 300, 2, seed=5)
    assert all(p.answer_unit in ("m", "s") for p in probs)
    text = " ".join(p.question for p in probs)
    assert "km/h" in text and "ft" in text


def test_level_3_asks_for_non_si_answer_unit():
    probs = generate(FAMILY, 300, 3, seed=5)
    units = {p.answer_unit for p in probs}
    assert units - {"m", "s"}, "expected some non-SI answer units"
    for p in probs:
        if p.answer_unit not in ("m", "s"):
            assert f"in {p.answer_unit}" in p.question


def test_params_are_si_and_within_ranges():
    for d in range(1, 5):
        for p in generate(FAMILY, 200, d, seed=9):
            if "v" in p.params:
                assert 5 - 1e-9 <= p.params["v"] <= 50 + 1e-9
            if "theta_deg" in p.params:
                assert 15 <= p.params["theta_deg"] <= 75
            if "H" in p.params:
                assert 5 - 1e-9 <= p.params["H"] <= 100 + 1e-9


def test_level_1_inputs_are_rounded():
    for p in generate(FAMILY, 200, 1, seed=2):
        if "v" in p.params:
            assert round(p.params["v"], 1) == pytest.approx(p.params["v"])
        if "theta_deg" in p.params:
            assert p.params["theta_deg"] == round(p.params["theta_deg"])
        if "H" in p.params:
            assert p.params["H"] == round(p.params["H"])


# ---------- display units fit the magnitude ----------

def test_cm_is_only_used_for_values_under_2_m():
    import re

    for d in range(1, 5):
        for p in generate(FAMILY, 400, d, seed=21):
            for num in re.findall(r"(\d+(?:\.\d+)?) cm\b", p.question):
                assert float(num) <= 200, p.question  # inputs shown in cm
            if p.answer_unit == "cm":
                assert p.answer_value <= 200, (p.question, p.answer_value)


def test_heights_in_questions_use_m_or_ft_and_speeds_use_ms_or_kmh():
    import re

    for d in range(1, 5):
        for p in generate(FAMILY, 300, d, seed=22):
            body = p.question.split(" Express your answer")[0]
            units = set(re.findall(r"\d(?:\.\d+)? (m/s|km/h|m|ft|cm|km)\b", body))
            assert units <= {"m/s", "km/h", "m", "ft"}, (units, p.question)


def test_length_answers_are_not_shown_in_absurd_magnitudes():
    for d in (3, 4):
        for p in generate(FAMILY, 400, d, seed=23):
            if p.answer_unit == "km":
                assert p.answer_value >= 1, p.question
            if p.answer_unit in ("cm", "km"):
                assert p.answer_value < 1000, p.question


# ---------- 4. difficulty 4 distractor ----------

def test_level_4_has_distractor_in_text_not_affecting_answer():
    probs = generate(FAMILY, 200, 4, seed=13)
    for p in probs:
        d = p.params["distractor"]
        assert d["text"] in p.question
        # answer is fully determined by the physical inputs, ignoring the distractor
        physical = {k: v for k, v in p.params.items() if k != "distractor"}
        si_unit = "s" if p.template == "time_of_flight" else "m"
        expected = (solve(p.template, physical) * ureg(si_unit)).to(p.answer_unit).magnitude
        assert p.answer_value == pytest.approx(expected, rel=1e-9)


def test_levels_below_4_have_no_distractor():
    for d in (1, 2, 3):
        assert all("distractor" not in p.params for p in generate(FAMILY, 100, d, seed=1))


# ---------- question text ----------

def test_every_question_ends_with_boxed_instruction():
    for d in range(1, 5):
        for p in generate(FAMILY, 100, d, seed=4):
            assert p.question.rstrip().endswith("Give your final answer as \\boxed{value unit}.")


def test_phrasings_vary_within_a_template():
    for t in TEMPLATES:
        qs = set()
        for s in range(60):
            p = FAMILY.sample(np.random.default_rng(s), 1, template=t)
            # strip digits so only wording differs
            qs.add("".join(c for c in p.question if not c.isdigit()))
        assert len(qs) >= 2, t


def test_all_templates_are_generated():
    probs = generate(FAMILY, 200, 1, seed=0)
    assert {p.template for p in probs} == set(TEMPLATES)


def test_solution_steps_nonempty():
    for p in generate(FAMILY, 50, 3, seed=0):
        assert p.solution_steps and all(isinstance(s, str) and s for s in p.solution_steps)


# ---------- 5. smoke ----------

def test_smoke_1000_problems_all_templates_and_difficulties(capsys):
    problems: list[Problem] = []
    for d in range(1, 5):
        problems += generate(FAMILY, 250, d, seed=100 + d)
    assert len(problems) == 1000
    for p in problems:
        assert math.isfinite(p.answer_value)
        assert p.answer_value > 0
    assert {p.template for p in problems} == set(TEMPLATES)
    assert {p.difficulty for p in problems} == {1, 2, 3, 4}
    for p in (problems[0], problems[400], problems[999]):
        print(f"\n[{p.id}]\n{p.question}\n-> {p.answer_value:.4g} {p.answer_unit}")
    assert capsys.readouterr().out  # the examples were printed


def test_problem_i_does_not_depend_on_batch_size():
    small = generate(FAMILY, 10, 3, seed=7)
    large = generate(FAMILY, 1000, 3, seed=7)
    assert small == large[:10]


# ---------- g is stated in every question ----------

G_SENTENCE = "Use g = 9.81 m/s²."


def test_every_question_states_g_before_the_answer_instructions():
    for d in range(1, 5):
        for p in generate(FAMILY, 100, d, seed=31):
            q = p.question
            assert q.count(G_SENTENCE) == 1, q
            assert q.index(G_SENTENCE) < q.index("Give your final answer as"), q
            if "Express your answer" in q:
                assert q.index(G_SENTENCE) < q.index("Express your answer"), q


# ---------- end-to-end oracle ----------
# Independent of solve(), pint and params: parse the question text, convert with
# hand-written factors, recompute with formulas written out here.

import re

_FT = 0.3048  # m
_KMH = 1 / 3.6  # m/s per km/h
_G = 9.81
_TO_ASKED = {"m": 1.0, "cm": 100.0, "ft": 1 / 0.3048, "km": 1 / 1000.0, "s": 1.0, "ms": 1000.0}


def _oracle_answer(template: str, question: str) -> tuple[float, str]:
    body = question.split(" Use g = ")[0]  # inputs live before the g sentence

    sp = re.search(r"(\d+(?:\.\d+)?) (m/s|km/h)(?!²)", body)
    assert sp, question
    v = float(sp.group(1)) * (1.0 if sp.group(2) == "m/s" else _KMH)

    th = re.search(r"(\d+)°(?!C)", body)
    ht = re.search(r"(\d+(?:\.\d+)?) (m|ft)\b(?!/)", body)

    if template == "from_cliff":
        assert ht, question
        H = float(ht.group(1)) * (1.0 if ht.group(2) == "m" else _FT)
        ans = v * math.sqrt(2 * H / _G)
        base = "m"
    else:
        assert th, question
        a = math.radians(float(th.group(1)))
        if template == "max_height":
            ans, base = (v * math.sin(a)) ** 2 / (2 * _G), "m"
        elif template == "time_of_flight":
            ans, base = 2 * v * math.sin(a) / _G, "s"
        else:  # range
            ans, base = v * v * math.sin(2 * a) / _G, "m"

    asked = re.search(r"Express your answer in (\w+)\.", question)
    unit = asked.group(1) if asked else base
    return ans * _TO_ASKED[unit], unit


@pytest.mark.parametrize("difficulty", [1, 2, 3, 4])
def test_oracle_recomputes_answer_from_question_text_alone(difficulty):
    for p in generate(FAMILY, 500, difficulty, seed=77):
        expected, unit = _oracle_answer(p.template, p.question)
        assert p.answer_unit == unit, p.question
        assert p.answer_value == pytest.approx(expected, rel=1e-6), p.question
