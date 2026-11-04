"""Projectile problem family: 4 templates, 4 difficulty levels. g = 9.81, no drag."""
from __future__ import annotations

import argparse
import math

import numpy as np
import pint

from envs.base import Problem, generate

G = 9.81  # m/s^2
TEMPLATES = ("max_height", "time_of_flight", "range", "from_cliff")
BOXED = "Give your final answer as \\boxed{value unit}."

ureg = pint.UnitRegistry()

# ---------- physics (SI floats) ----------


def max_height(v: float, theta_deg: float) -> float:
    return (v * math.sin(math.radians(theta_deg))) ** 2 / (2 * G)


def time_of_flight(v: float, theta_deg: float) -> float:
    return 2 * v * math.sin(math.radians(theta_deg)) / G


def projectile_range(v: float, theta_deg: float) -> float:
    return v**2 * math.sin(2 * math.radians(theta_deg)) / G


def cliff_time(H: float) -> float:
    return math.sqrt(2 * H / G)


def cliff_range(v: float, H: float) -> float:
    return v * cliff_time(H)


def solve(template: str, params: dict) -> float:
    """Gold answer in SI (m or s) from SI params; extra keys are ignored."""
    if template == "max_height":
        return max_height(params["v"], params["theta_deg"])
    if template == "time_of_flight":
        return time_of_flight(params["v"], params["theta_deg"])
    if template == "range":
        return projectile_range(params["v"], params["theta_deg"])
    if template == "from_cliff":
        return cliff_range(params["v"], params["H"])
    raise ValueError(template)


_SI_ANSWER_UNIT = {"max_height": "m", "range": "m", "from_cliff": "m", "time_of_flight": "s"}
_ALT_UNITS = {"m": ("cm", "km", "ft"), "s": ("ms", "min")}

# ---------- question text ----------
# {v} {theta} {H} are pre-formatted "value unit" strings.
_PHRASINGS = {
    "max_height": [
        "A ball is launched from level ground with a speed of {v} at an angle of {theta} above the horizontal. Ignoring air resistance, what maximum height does it reach?",
        "A projectile leaves the ground at {v}, {theta} above the horizontal. Neglecting drag, find the greatest height it attains.",
        "Neglect air resistance. A stone is thrown from the ground at {theta} above the horizontal with initial speed {v}. How high does it rise at its peak?",
    ],
    "time_of_flight": [
        "A ball is launched from level ground with a speed of {v} at an angle of {theta} above the horizontal. Ignoring air resistance, how long is it in the air?",
        "A projectile is fired from the ground at {v}, {theta} above the horizontal. Neglecting drag, find its total time of flight.",
        "Neglect air resistance. A stone is thrown from the ground at {theta} above the horizontal with initial speed {v}. How much time passes before it lands?",
    ],
    "range": [
        "A ball is launched from level ground with a speed of {v} at an angle of {theta} above the horizontal. Ignoring air resistance, how far from the launch point does it land?",
        "A projectile is fired from the ground at {v}, {theta} above the horizontal. Neglecting drag, find its horizontal range.",
        "Neglect air resistance. A stone is thrown from the ground at {theta} above the horizontal with initial speed {v}. What horizontal distance does it cover before landing?",
    ],
    "from_cliff": [
        "A ball is thrown horizontally at {v} from the top of a cliff {H} high. Ignoring air resistance, how far from the base of the cliff does it land?",
        "From a cliff {H} above level ground, a stone is launched horizontally with speed {v}. Neglecting drag, what horizontal distance does it travel before hitting the ground?",
        "Neglect air resistance. A projectile leaves the edge of a {H} high cliff moving horizontally at {v}. Find the horizontal distance from the cliff base to its landing point.",
    ],
}


def _fmt(x: float) -> str:
    return f"{x:.1f}".rstrip("0").rstrip(".")


def _distractor(rng: np.random.Generator) -> dict:
    if rng.integers(2) == 0:
        m = round(float(rng.uniform(0.1, 5.0)), 2)
        return {"kind": "mass", "value": m, "unit": "kg", "text": f"The object has a mass of {m:g} kg."}
    t = int(rng.integers(-5, 36))
    return {"kind": "temperature", "value": t, "unit": "degC", "text": f"The air temperature is {t} °C."}


class Projectiles:
    name = "projectiles"

    def sample(self, rng: np.random.Generator, difficulty: int, template: str | None = None) -> Problem:
        if difficulty not in (1, 2, 3, 4):
            raise ValueError(f"difficulty must be 1..4, got {difficulty}")
        if template is None:
            template = TEMPLATES[int(rng.integers(len(TEMPLATES)))]

        # --- sample inputs, as *displayed* values, then convert to SI with pint ---
        # v: 5-50 m/s (0.1); theta: 15-75 deg (1); H: 5-100 m (1)
        v_unit, H_unit = "m/s", "m"
        if difficulty >= 2:
            if template == "from_cliff":
                # convert speed, or height (cm / ft); one of them stays SI
                choice = ("speed", "cm", "ft")[int(rng.integers(3))]
                v_unit = "km/h" if choice == "speed" else "m/s"
                H_unit = choice if choice in ("cm", "ft") else "m"
            else:
                v_unit = "km/h"

        v_disp = {
            "m/s": round(float(rng.uniform(5, 50)), 1),
            "km/h": round(float(rng.uniform(18, 180)), 1),
        }[v_unit]
        theta = int(rng.integers(15, 76))
        H_disp = {
            "m": int(rng.integers(5, 101)),
            "cm": int(rng.integers(5, 101)) * 100,
            "ft": int(rng.integers(math.ceil(5 / 0.3048), math.floor(100 / 0.3048) + 1)),
        }[H_unit]

        v = (v_disp * ureg(v_unit)).to("m/s").magnitude
        H = (H_disp * ureg(H_unit)).to("m").magnitude

        params: dict = {"v": v}
        if template == "from_cliff":
            params["H"] = H
        else:
            params["theta_deg"] = float(theta)

        # --- answer ---
        si_unit = _SI_ANSWER_UNIT[template]
        answer_unit = si_unit
        if difficulty >= 3:
            alts = _ALT_UNITS[si_unit]
            answer_unit = alts[int(rng.integers(len(alts)))]
        si_answer = solve(template, params)
        answer_value = (si_answer * ureg(si_unit)).to(answer_unit).magnitude

        # --- text ---
        options = _PHRASINGS[template]
        body = options[int(rng.integers(len(options)))].format(
            v=f"{_fmt(v_disp)} {v_unit}",
            theta=f"{theta}°",
            H=f"{H_disp} {H_unit}",
        )
        parts = [body]
        if difficulty >= 4:
            d = _distractor(rng)
            params["distractor"] = d
            parts.append(d["text"])
        if difficulty >= 3:
            parts.append(f"Express your answer in {answer_unit}.")
        parts.append(BOXED)
        question = " ".join(parts)

        return Problem(
            id=f"projectiles/{template}/d{difficulty}",
            family=self.name,
            template=template,
            difficulty=difficulty,
            question=question,
            answer_value=float(answer_value),
            answer_unit=answer_unit,
            params=params,
            solution_steps=_steps(template, params, si_answer, si_unit, answer_value, answer_unit),
        )


def _steps(template, params, si_answer, si_unit, answer_value, answer_unit) -> list[str]:
    v = params["v"]
    steps = [f"Convert inputs to SI: v = {v:.4g} m/s" + (f", H = {params['H']:.4g} m" if "H" in params else "")
             + (f", θ = {params['theta_deg']:.0f}°" if "theta_deg" in params else "") + f", g = {G} m/s²."]
    formula = {
        "max_height": "h = (v sinθ)² / (2g)",
        "time_of_flight": "t = 2 v sinθ / g",
        "range": "R = v² sin(2θ) / g",
        "from_cliff": "R = v · √(2H/g)",
    }[template]
    steps.append(f"Use {formula}.")
    steps.append(f"Result: {si_answer:.4g} {si_unit}.")
    if answer_unit != si_unit:
        steps.append(f"Convert to {answer_unit}: {answer_value:.4g} {answer_unit}.")
    return steps


def main() -> None:
    ap = argparse.ArgumentParser(description="Print sample projectile problems.")
    ap.add_argument("--n", type=int, default=5)
    ap.add_argument("--difficulty", type=int, default=1)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    for p in generate(Projectiles(), args.n, args.difficulty, args.seed):
        print(f"[{p.id}]\n{p.question}\n-> answer: {p.answer_value:.4g} {p.answer_unit}\n")


if __name__ == "__main__":
    main()
