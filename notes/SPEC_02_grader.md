# SPEC_02: answer graders (v0 naive, v1 hardened)

**Goal:** two graders with the same signature, `grade(reply: str, problem: Problem, rtol=...) -> float` (1.0 or 0.0). No LLM judge. Doesn't touch `envs/projectiles.py`.

```
grader/v0.py     naive, on purpose (for the reward-hacking audit)
grader/v1.py     hardened
grader/units.py  v1's own unit alias table
grader/__init__.py  exposes grade_v0, grade_v1, GRADERS = {"v0": ..., "v1": ...}
tests/test_grader.py
data/labels/hand_labeled_replies.jsonl   (empty for now)
```

## v0 (naive, as planned in the README)

First number anywhere in the reply, `rtol=0.05`, units ignored, boxes ignored.
Tests document that it **is fooled** by: two boxes, right number in the wrong unit, no unit, 4% off, hedged answers.

## v1 pipeline

```
reply ──► find \boxed{…} (brace matching) ──► exactly one? ──no──► 0
                                                │yes
                     normalize LaTeX spacing/wrappers inside box
                                                │
     whole box matches: [symbol =|≈  or  ≈] NUMBER UNIT [.,;] ──no──► 0
                                                │
             UNIT (via grader's own alias table) == problem.answer_unit? ──no──► 0
                                                │
                  |x − gold| ≤ rtol·|gold|  (rtol=0.01) ? ──► 1 / 0
```

## v1 rules

| Rule | Accepted | Scores 0 |
|---|---|---|
| Box count | exactly one `\boxed{}` | none; 2+ (even if the instruction "\boxed{value unit}" is echoed); empty box |
| Box contents | one number + one unit, nothing else | `12-13 m`, `12 m or 13 m`, `R = 12 m = 1200 cm`, `\frac{1}{2} m`, bare number |
| Symbol prefix | `R = 12 m`, `R ≈ 12 m`, `R \approx 12 m`, `h_{max} = 1.2 m`, `v_0 = 12 m/s` (subscript belongs to the symbol) | two numbers anywhere, e.g. `R = 12 m = 1200 cm` |
| Numbers | `12`, `-3.5`, `−3.5` (unicode minus), `1.2e3`, `1.2E+03`, `1.2×10^3`, `1.2×10³`, `1.2 \times 10^{3}`, `1.2 \cdot 10^3`, `1,234.5` | `1,5` (comma only valid in groups of 3) |
| Prefix/suffix | leading `≈` / `\approx`; trailing `.` `,` `;` | anything else around the number/unit |
| LaTeX | `\text{m}`, `\mathrm{m}`, `\,` `\;` `\ ` `~` spacing, `$…$` | |
| Units | must equal the asked unit after alias mapping (`m`/`meter`/`metres` → `m`). Symbols are **case-sensitive** (`ms` ≠ `Ms`, `m` ≠ `M`). | right value in another unit, e.g. `0.5 km` when key is `m` |
| Tolerance | relative, `rtol=0.01` parameter | 1.5% off |

## Independence

v1 has its **own** alias table: spelling → canonical unit symbol. It holds **no conversion factors** and never converts, because a wrong unit scores 0 anyway (so pint isn't needed). A conversion bug in the generator can't be cancelled by the grader. v1 imports only `Problem` from `envs.base`; a test checks it doesn't import `envs.projectiles`. If `problem.answer_unit` isn't in the table, v1 raises (a missing table entry must fail loudly, not score 0 silently).

## Tests (written first)

One test (or parametrized group) per rule row, with near-misses: 0.9% off → 1, 1.5% off → 0, right number wrong unit → 0, two boxes → 0, empty box → 0, echoed instruction plus answer → 0. One integration test formats real generated answers several valid ways and expects 1.0 from v1.

**Hand labels:** `data/labels/hand_labeled_replies.jsonl`, one row per reply:
`{"reply": str, "answer_value": float, "answer_unit": str, "label": 0|1, "note": str}`.
The test asserts v1's grade == label for every row and **skips** if the file is empty.

## Decisions (agreed 2026-11-11)

1. Follow repo layout (`grader/`, `notes/`, `data/labels/`).
2. Build both v0 and v1; v0's holes are documented by tests.
3. Strict units at levels 1–2 too (m / s implied, since those questions don't name the unit).
4. Leading `symbol =` / `symbol ≈` allowed if there's exactly one number.

## TODO (separate task)

- [ ] Generator: make **every** level state the answer unit in the question (today levels 1–2 never do: 0/400 checked), so the strict unit rule is fair.
