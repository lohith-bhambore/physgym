# Task 01: projectile problem generator

**Goal:** a function that generates unlimited, reproducible physics problems about projectiles, each with a correct answer in SI units. No model, no grader, no training yet: just a solid, tested problem generator.

**Time:** about 45–60 minutes with Claude Code.
**How to use:** open WSL, `cd ~/physgym`, run `claude`, and paste: *"Read CLAUDE.md and notes/SPEC_01_projectiles.md, then implement it. Write the tests first."*

---

## Files to create

```
envs/__init__.py
envs/base.py          # Problem dataclass + Family interface
envs/projectiles.py   # the projectile family
tests/test_projectiles.py
pyproject.toml        # minimal; deps: pint, numpy, pytest
```

## `envs/base.py`

```python
@dataclass(frozen=True)
class Problem:
    id: str                 # e.g. "projectiles/range/d2/seed=123"
    family: str             # "projectiles"
    template: str           # "max_height" | "range" | "time_of_flight" | "from_cliff"
    difficulty: int         # 1..4
    question: str           # text shown to the model
    answer_value: float     # gold answer in SI units
    answer_unit: str        # pint-parsable SI unit, e.g. "m", "s", "m/s"
    params: dict            # the raw sampled inputs (in SI), for debugging and audits
    solution_steps: list[str]  # short worked solution (used later for analysis, not training)

class Family(Protocol):
    name: str
    def sample(self, rng: np.random.Generator, difficulty: int) -> Problem: ...
```

Also add `generate(family, n, difficulty, seed) -> list[Problem]`, which is deterministic for a given seed.

## `envs/projectiles.py`: 4 templates

Use g = 9.81 m/s², no air resistance, launch from ground level unless the template says otherwise.

| Template | Asks for | Formula |
|---|---|---|
| `max_height` | maximum height | h = (v sinθ)² / (2g) |
| `time_of_flight` | time in the air | t = 2 v sinθ / g |
| `range` | horizontal distance | R = v² sin(2θ) / g |
| `from_cliff` | horizontal distance when launched horizontally from height H | R = v · √(2H/g) |

**Parameter ranges:** v in 5–50 m/s, θ in 15°–75°, H in 5–100 m. Round sampled inputs to sensible precision (v to 0.1, θ to 1°, H to 1 m) so questions read naturally.

**Difficulty knobs** (each level adds one thing):
1. Inputs in SI units, a single step.
2. Inputs in mixed units: speed in **km/h**, or height in **cm** or **ft**. The answer stays SI.
3. Level 2, plus **ask for the answer in a non-SI unit** (e.g. "in cm", "in ms"). Store `answer_value`/`answer_unit` in *that* unit.
4. Level 3, plus **one irrelevant number** in the text (e.g. the ball's mass, or air temperature).

Use `pint` for every unit conversion. Never hand-write conversion factors.

**Question text:** 2–3 natural phrasings per template, chosen by the rng, so the model can't memorize one wording. End every question with: *"Give your final answer as \boxed{value unit}."*

## Tests (`tests/test_projectiles.py`), written first

1. **Deterministic:** the same seed gives identical problems, and different seeds give different ones.
2. **Physics sanity:**
   - range at θ and 90°−θ is equal (same v)
   - max height is maximal at θ=90° and grows with v²
   - `time_of_flight` × v cosθ equals `range` (consistency between templates)
   - `from_cliff` time equals √(2H/g)
3. **Units:** for difficulty 2–4, converting `params` back reproduces `answer_value` within 1e-9 relative error, using pint.
4. **Difficulty 4:** the distractor number appears in the question and does **not** change the answer.
5. **Smoke test:** generate 1,000 problems across all templates and difficulties with no errors, NaNs or negative answers, and print 3 examples.

## Done when
- `pytest` passes
- `python -m envs.projectiles --n 5 --difficulty 3 --seed 0` prints 5 readable problems with answers
- Committed and pushed: `git commit -m "Projectile problem family + tests"`

## Out of scope (later tasks)
Grader, other families, Python tool, model calls, training.
