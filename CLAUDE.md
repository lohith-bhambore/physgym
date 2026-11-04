# PhysGym: context for Claude Code

## What this repo is
A public research project: **RL with verifiable rewards on generated physics problems.** A small open model (~1.5B, e.g. Qwen2.5-Math-1.5B) is trained with GRPO to solve multi-step physics problems, optionally using a sandboxed Python tool. A central part is a **reward-hacking audit**: start with a deliberately naive grader, document how the model games it, harden the grader, and retrain.

The owner is building this as public proof of skill for Research Engineer roles (post-training / evals). Quality bar: careful, reproducible, honest. Every number in the README must come from a script in `scripts/`.

## Layout
- `envs/`: problem families (generators). Each returns `Problem` objects (see `envs/base.py`).
- `grader/`: v0 (naive, on purpose) and v1 (hardened: one boxed answer, units via pint, ~1% tolerance)
- `tools/`: sandboxed Python tool (subprocess, timeout, no network)
- `train/`: GRPO configs and scripts (Unsloth / TRL)
- `eval/`: fixed eval sets (fixed seeds) and the eval runner
- `scripts/`: one script per README chart
- `data/labels/`: hand-labeled model replies for testing the grader
- `notes/`: specs (`SPEC_XX_*.md`) and a lab notebook
- `tests/`: pytest

## Conventions
- Python 3.11, type hints, small pure functions, `numpy.random.Generator` passed in explicitly (no global random state).
- All unit handling through `pint`; never hand-write conversion factors.
- Write tests first for anything with physics or units in it.
- Deterministic by seed everywhere.
- Keep dependencies minimal; add one only when a task needs it.

## Environment
- Develop in WSL2 on a personal Windows PC (RTX 4060, 8GB). Final training runs on a rented GPU.
- Never copy code, prompts or data from the owner's employer into this repo.

## Workflow
- Each task has a spec in `notes/SPEC_XX_*.md`. Implement it, run `pytest`, then commit with a clear message.
- At the end of a session, append 2–3 lines to `notes/LOG.md`: what was done, what's next, any open question.

## Tooling
- Use **uv**, not pip: `uv add <pkg>` (or `uv add --dev <pkg>`), and run everything with `uv run` (e.g. `uv run pytest`, `uv run python -m envs.projectiles`).
- Commit `pyproject.toml`, `uv.lock` and `.python-version`.
