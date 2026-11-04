"""Shared problem types and the deterministic batch generator."""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Protocol

import numpy as np


@dataclass(frozen=True)
class Problem:
    id: str  # e.g. "projectiles/range/d2/seed=123/n=0"
    family: str  # "projectiles"
    template: str  # "max_height" | "range" | "time_of_flight" | "from_cliff"
    difficulty: int  # 1..4
    question: str  # text shown to the model
    answer_value: float  # gold answer, in answer_unit
    answer_unit: str  # pint-parsable unit, e.g. "m", "s", "cm"
    params: dict  # raw sampled inputs (SI), for debugging and audits
    solution_steps: list[str]  # short worked solution (analysis only)


class Family(Protocol):
    name: str

    def sample(self, rng: np.random.Generator, difficulty: int) -> Problem: ...


def generate(family: Family, n: int, difficulty: int, seed: int) -> list[Problem]:
    """Deterministic for a given seed. Problem i does not depend on n."""
    children = np.random.SeedSequence(seed).spawn(n)
    problems = []
    for i, child in enumerate(children):
        p = family.sample(np.random.default_rng(child), difficulty)
        problems.append(replace(p, id=f"{p.id}/seed={seed}/n={i}"))
    return problems
