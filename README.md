# PhysGym: teaching a small model physics with RL, and catching it cheat


## What this is

A small, fully open experiment in **reinforcement learning with verifiable rewards (RLVR)**:

1. **An environment** that generates unlimited fresh physics problems from templates (projectiles, inclines with friction, springs and energy, circuits, ideal gases). Difficulty is controlled by the number of steps, unit conversions and distractor information.
2. **A grader** that checks the final answer's number *and* units. No LLM judge.
3. **A Python tool** the model may call to compute or simulate before answering.
4. **RL training** (GRPO) of a ~1.5B open model on this environment, with before-vs-after evals.
5. **A reward-hacking audit:** start with a deliberately naive grader, document every way the model games it, fix each one, and retrain.

**Question:** can RL teach a small model to solve multi-step physics problems, and to *check its own work with code*, without learning to game the grader?

## Why physics

- Answers are numbers with units, so correctness is checkable without a judge.
- Generated problems mean no benchmark contamination and exact control over difficulty.
- Units and tolerances are a natural, realistic place for reward hacking.

## Environment

| Piece | Details |
|---|---|
| Problem families (v1) | Kinematics, Newton's laws (inclines, friction), work/energy/springs, DC circuits, ideal gas |
| Held-out families (OOD) | Two families never seen in training, to test generalization (e.g. RC circuits, momentum) |
| Difficulty knobs | 1-4 reasoning steps, unit conversions (cm, km/h, kPa...), irrelevant numbers in the text |
| Answer format | `\boxed{9.81 m/s^2}`: one number, one unit |
| Tool | Sandboxed Python (subprocess, timeout, no network, numpy/scipy), up to N calls per problem |

## Grader

**v0 (deliberately naive, for the audit):** takes the first number in the reply, 5% tolerance, ignores units.

**v1 (hardened):**
- Parses exactly one boxed answer; multiple answers score 0
- Converts units with `pint`; wrong dimension scores 0
- Relative tolerance about 1%, tuned so correct solutions pass and sloppy ones don't
- Checked against a hand-labeled set of model replies; grader accuracy is reported

## Experiments

| ID | What | Metrics |
|---|---|---|
| E0 | Baselines: 2-3 small open models, with and without the tool | Accuracy (in-distribution and OOD), tool-call rate |
| E1 | GRPO without the tool | Accuracy vs. training steps, reply length |
| E2 | GRPO with the tool | Same, plus "did the tool call actually compute the answer?" |
| E3 | Reward-hacking audit: train on grader v0, inspect, fix, retrain on v1 | Catalogue of exploits, their frequency, accuracy under v1 |

Rigor rules: fixed eval sets, at least 3 seeds where compute allows, confidence intervals, and every chart reproducible from a script in `scripts/`.

## Results

_Coming soon. Filled only with measured numbers._

## Reward-hacking log

_Each exploit gets: what the model did, an example reply, how often, and the grader fix._

## Repo layout

```
physgym/
  envs/            problem templates + generator
  grader/          v0 and v1 graders, unit handling, tests
  tools/           sandboxed Python tool
  train/           GRPO training configs and scripts
  eval/            eval sets (fixed seeds) and eval runner
  scripts/         one script per chart in the README
  data/labels/     hand-labeled replies for testing the grader
  notes/           lab notebook: what was tried, what happened
  tests/
  README.md
```

## Stack

Python, PyTorch, Unsloth / TRL (GRPO), vLLM for generation, `pint` and `sympy` for units and math. Develop on an 8GB GPU (WSL2), run final training on a rented 24-80GB GPU.

## Timeline (matches the job plan)

| Week of | Milestone |
|---|---|
| Nov 2 | Repo public, README, first problem family generating problems |
| Nov 9 | All 5 families + held-out families; Python tool sandboxed |
| Nov 16 | Grader v0 and v1 working; v1 tested against hand labels |
| Nov 23 | E0 baselines done; first results in the README |
| Nov 30 | E1 GRPO run started (local small run, then rented GPU) |
| Dec | E2 with tool, E3 reward-hacking audit |
| Jan | Write-up, blog post, 4-page workshop paper draft |

## License

MIT
